#!/bin/bash
# CI guard: files that execute as text must be stored with LF endings.
#
# .gitattributes acts at checkout time only. It cannot repair a blob that was
# committed with CRLF: git writes the stored bytes, so a CRLF `configure` or
# Makefile survives every clone and fails on Linux with a bad-interpreter
# error or `$'\r': command not found` — exactly what the pin exists to prevent.
# This gate inspects the stored bytes instead of trusting the attribute.
#
# Two classes are enforced:
#   1. every file pinned to eol=lf in .gitattributes;
#   2. every file that starts with `#!`, whatever its name. A pattern list
#      cannot name extensions that do not exist yet, so content decides for
#      scripts. Such a file must also be pinned: an LF blob still checks out
#      CRLF on a Windows clone unless a rule covers it, so an unpinned script
#      is reported rather than silently left at the platform default.
#
# On a clean CI checkout the index equals HEAD, so this describes the committed
# tree; locally it also catches a CRLF blob that is staged but not committed.

set -euo pipefail

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

# Byte semantics: the blob scan below counts characters while walking content.
export LC_ALL=C

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! git -C "$ROOT" rev-parse --git-dir > /dev/null 2>&1; then
  echo "check_lf_endings: $ROOT is not a git checkout" >&2
  exit 1
fi

cd "$ROOT"

# A deleted or renamed .gitattributes would leave nothing pinned and let this
# gate pass vacuously, so require the rules to still resolve first.
for probe in configure Makefile; do
  resolved=$(git check-attr eol -- "$probe" | sed 's/.*: //')
  if [ "$resolved" != "lf" ]; then
    echo "ERROR: .gitattributes no longer pins $probe to LF (eol: $resolved)." >&2
    echo "Restore the pin before relying on this check." >&2
    exit 1
  fi
done

# A pathspec list for the staged case, empty for the full scan: unchanged
# files were checked when their own commit was made.
scope=()
if [ "$STAGED" -eq 1 ]; then
  mapfile -t changed < <(git diff --cached --name-only --diff-filter=ACMR)
  if [ "${#changed[@]}" -eq 0 ]; then
    echo "check_lf_endings: OK — nothing staged"
    exit 0
  fi
  scope=(-- "${changed[@]}")
fi

tab=$(printf '\t')
declare -A index_eol=() pinned_lf=() crlf=() unpinned=()
pinned=0

while IFS= read -r -d '' record; do
  meta="${record%%"$tab"*}"
  path="${record#*"$tab"}"
  index_eol["$path"]="${meta%% *}"

  case "$meta" in
    *"attr/"*"eol=lf"*) pinned_lf["$path"]=1 ;;
  esac
done < <(git ls-files --eol -z "${scope[@]}")

# With no pathspec at all, an empty pinned set can only mean the attributes
# went missing; a staged commit of unpinned files is normal.
if [ "$STAGED" -eq 0 ] && [ "${#pinned_lf[@]}" -eq 0 ]; then
  echo "ERROR: no tracked file is pinned to LF — .gitattributes is missing or broken." >&2
  exit 1
fi

pinned=${#pinned_lf[@]}

# A pinned blob must be stored LF. `i/none` means the blob holds no line
# ending at all, which cannot carry a CR. The guard is not redundant: printf
# reuses its format with no arguments, so an empty array would emit a blank
# line and the loop would read an empty path.
for path in "${!pinned_lf[@]}"; do
  case "${index_eol[$path]:-}" in
    i/crlf|i/mixed) crlf["$path"]=1 ;;
  esac
done

# Content decides for scripts. grep narrows the tree to files with a `#!` in
# column 0 anywhere, then the blob's first two bytes confirm it starts the
# file. One `git cat-file --batch` serves every candidate: a process per file
# costs ~20 s on a Windows checkout, and this runs on every push.
mapfile -t candidates < <(git grep --cached -I -l -e '^#!' "${scope[@]}" || true)
scripts=0

if [ "${#candidates[@]}" -gt 0 ]; then
  i=0
  while IFS= read -r header; do
    path="${candidates[$i]}"
    i=$((i + 1))
    case "$header" in *" missing") continue ;; esac

    size="${header##* }"
    magic=""
    # `read -n` stops at a newline, so a blob shorter than two bytes would
    # lose its record terminator and desync the stream; those cannot match a
    # shebang and are consumed by count instead.
    if [ "$size" -ge 2 ]; then
      IFS= read -r -n 2 magic || true
      if [ "$size" -gt 2 ]; then
        IFS= read -r -N $((size - 2)) _rest || true
      fi
    elif [ "$size" -eq 1 ]; then
      IFS= read -r -N 1 _rest || true
    fi
    IFS= read -r _terminator || true

    [ "$magic" = "#!" ] || continue

    scripts=$((scripts + 1))
    case "${index_eol[$path]:-}" in
      i/crlf|i/mixed) crlf["$path"]=1 ;;
    esac
    if [ -z "${pinned_lf[$path]:-}" ]; then
      unpinned["$path"]=1
    fi
  done < <(printf ':%s\n' "${candidates[@]}" | git cat-file --batch 2>/dev/null)
fi

status=0

if [ "${#crlf[@]}" -gt 0 ]; then
  echo "ERROR: file(s) stored with CRLF line endings:"
  printf '%s\n' "${!crlf[@]}" | sort | sed 's/^/  /'
  echo
  echo "An attribute cannot repair a committed blob; the stored bytes must"
  echo "change. Renormalize and commit:"
  echo "  git add --renormalize <paths>"
  echo
  status=1
fi

if [ "${#unpinned[@]}" -gt 0 ]; then
  echo "ERROR: script(s) start with a shebang but no rule pins them to LF:"
  printf '%s\n' "${!unpinned[@]}" | sort | sed 's/^/  /'
  echo
  echo "A shebang file is executed directly, so it must not check out CRLF on"
  echo "a Windows clone. Add its extension (or an explicit path) to"
  echo "  .gitattributes   <pattern>  text eol=lf"
  echo
  status=1
fi

if [ "$status" -ne 0 ]; then
  exit 1
fi

where="tracked tree"
[ "$STAGED" -eq 1 ] && where="staged files"
echo "check_lf_endings: OK — $where: $pinned pinned, $scripts shebang scripts stored as LF"
