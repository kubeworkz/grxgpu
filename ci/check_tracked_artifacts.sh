#!/bin/bash
# CI guard: reject committed build output.
#
# Vortex builds out-of-tree (AGENTS.md §2), so generated files, toolchain
# byproducts and machine binaries belong in the build directory, never in git.
# .gitignore only stops them from being staged by accident; this gate catches
# what is actually tracked, including files swept in with `git add -f`.
#
# Deliberately committed data is not matched: documentation images, evidence
# logs, synthesis .lib databases and vendored packages stay legitimate.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! git -C "$ROOT" rev-parse --git-dir > /dev/null 2>&1; then
  echo "check_tracked_artifacts: $ROOT is not a git checkout" >&2
  exit 1
fi

cd "$ROOT"

fail=0
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

git ls-files | sort > "$tmpdir/tracked"

# Names that are always produced by the build or by a test run: compiler
# output, config/dependency caches, compiled shaders, run logs and traces.
grep -E \
  '(^|/)\.depend$|(^|/)__pycache__/|(^|/)\.DS_Store$|\.(stamp|o|a|so|elf|vxbin|pyc|dump)$|\.stats\.log$|\.spv$|\.log\.ch[0-9]+$' \
  "$tmpdir/tracked" > "$tmpdir/names" || true

if [ -s "$tmpdir/names" ]; then
  echo "ERROR: generated build/test output is tracked:"
  sed 's/^/  /' "$tmpdir/names"
  echo
  echo "These files are produced by the build or by a test run. Delete them and"
  echo "let the .gitignore rules cover them; do not commit generated output."
  echo
  fail=1
fi

# Machine binaries under any name (ELF, PE/COFF, Mach-O): a renamed test
# executable is still build output. Other binary assets are legitimate, so
# match magic bytes rather than "is binary".
git grep --cached -I -l -e '' | sort > "$tmpdir/text" || true
comm -23 "$tmpdir/tracked" "$tmpdir/text" > "$tmpdir/candidates"
: > "$tmpdir/binaries"

while IFS= read -r file; do
  [ -f "$file" ] || continue   # submodule gitlinks and absent entries
  magic=$(od -An -tx1 -N4 -- "$file" 2>/dev/null | tr -d ' \n' || true)
  case "$magic" in
    7f454c46|4d5a*|cffaedfe|cefaedfe|feedface|feedfacf|cafebabe)
      echo "ERROR: machine binary is tracked: $file"
      echo "$file" >> "$tmpdir/binaries"
      fail=1
      ;;
  esac
done < "$tmpdir/candidates"

# Tracked and ignored at the same time is contradictory: the file is either
# generated output that slipped in, or the ignore rule is wrong. Root dotfiles
# are intentionally tracked even though .gitignore ignores `/. *` wholesale.
allow='^(\.gitignore|\.gitmodules|\.clang-format|\.freebuff/project-id)$'
git ls-files -i -c --exclude-standard | grep -Ev "$allow" | sort > "$tmpdir/ignored" || true
cat "$tmpdir/names" "$tmpdir/binaries" | sort > "$tmpdir/reported"
comm -23 "$tmpdir/ignored" "$tmpdir/reported" > "$tmpdir/ignored_new" || true

if [ -s "$tmpdir/ignored_new" ]; then
  echo "ERROR: tracked files match .gitignore rules:"
  sed 's/^/  /' "$tmpdir/ignored_new"
  echo
  echo "Either the file is generated (delete it) or the ignore rule is wrong."
  echo
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "Build output belongs in the build tree, not in git (AGENTS.md §2)."
  exit 1
fi

echo "check_tracked_artifacts: OK — no build output or machine binaries tracked"
