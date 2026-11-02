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
#
# `--staged` limits the scan to the paths the index would commit, which is
# what the pre-commit hook needs: unchanged files were already checked when
# their commit was made, and a full scan costs seconds on a large checkout.

set -euo pipefail

# Byte semantics: the magic-byte match below compares raw bytes.
export LC_ALL=C

STAGED=0
case "${1:-}" in
  --staged) STAGED=1; shift ;;
  "") ;;
  *) echo "usage: $0 [--staged]" >&2; exit 2 ;;
esac
if [ "$#" -ne 0 ]; then
  echo "usage: $0 [--staged]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! git -C "$ROOT" rev-parse --git-dir > /dev/null 2>&1; then
  echo "check_tracked_artifacts: $ROOT is not a git checkout" >&2
  exit 1
fi

cd "$ROOT"

# A pathspec list for the staged case, empty for the full scan. Deletions are
# excluded: a path with no staged content cannot carry build output.
scope=()
if [ "$STAGED" -eq 1 ]; then
  mapfile -t changed < <(git diff --cached --name-only --diff-filter=ACMR)
  if [ "${#changed[@]}" -eq 0 ]; then
    echo "check_tracked_artifacts: OK — nothing staged"
    exit 0
  fi
  scope=(-- "${changed[@]}")
fi

fail=0
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

git ls-files "${scope[@]}" | sort > "$tmpdir/tracked"

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
# match magic bytes rather than "is binary" — and every tracked file is
# examined, because git's text heuristic calls a short binary text and a
# text/binary split would let it through.
: > "$tmpdir/binaries"

if [ "$STAGED" -eq 1 ]; then
  # Staged content, not the checkout: a partially staged file is judged by
  # the bytes the commit would receive. One batch read answers for the whole
  # commit; a process per path costs ~40ms and a commit can touch hundreds.
  # The record bodies are skipped by ci/binary_magic.py because a shell
  # cannot skip binary content safely (`read -N` drops NUL bytes).
  if [ -s "$tmpdir/tracked" ]; then
    # The interpreter is probed, not assumed: `python3` may be an install
    # stub that exists on PATH but exits without running anything.
    python=""
    for candidate in python3 python; do
      if "$candidate" -c 'import sys' > /dev/null 2>&1; then
        python=$candidate
        break
      fi
    done
    if [ -z "$python" ]; then
      echo "check_tracked_artifacts: no working python3/python on PATH" >&2
      exit 1
    fi

    mapfile -t requests < "$tmpdir/tracked"
    printf ':%s\n' "${requests[@]}" \
      | git cat-file --batch 2>/dev/null \
      | "$python" "$ROOT/ci/binary_magic.py" "$tmpdir/tracked" > "$tmpdir/binaries" || true
  fi
else
  # The first four bytes of the checkout copy, read with the shell builtin:
  # a process per file cost ~6s on a large tree.
  while IFS= read -r file; do
    [ -f "$file" ] || continue   # submodule gitlinks and absent entries
    magic=""
    IFS= read -r -N 4 magic < "$file" 2>/dev/null || true
    case "$magic" in
      $'\x7f'ELF|MZ*|$'\xcf\xfa\xed\xfe'|$'\xce\xfa\xed\xfe'|$'\xfe\xed\xfa\xce'|$'\xfe\xed\xfa\xcf'|$'\xca\xfe\xba\xbe')
        echo "$file" >> "$tmpdir/binaries"
        ;;
    esac
  done < "$tmpdir/tracked"
fi

while IFS= read -r file; do
  [ -n "$file" ] || continue
  echo "ERROR: machine binary is tracked: $file"
  fail=1
done < "$tmpdir/binaries"

# Tracked and ignored at the same time is contradictory: the file is either
# generated output that slipped in, or the ignore rule is wrong. Root dotfiles
# are intentionally tracked even though .gitignore ignores `/.*` wholesale.
allow='^(\.gitignore|\.gitmodules|\.clang-format|\.freebuff/project-id)$'
git ls-files -i -c --exclude-standard "${scope[@]}" | grep -Ev "$allow" | sort > "$tmpdir/ignored" || true
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
