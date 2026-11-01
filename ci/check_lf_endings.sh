#!/bin/bash
# CI guard: files pinned to eol=lf must be stored with LF endings.
#
# .gitattributes acts at checkout time only. It cannot repair a blob that was
# committed with CRLF: git writes the stored bytes, so a CRLF `configure` or
# Makefile survives every clone and fails on Linux with a bad-interpreter
# error or `$'\r': command not found` — exactly what the pin exists to prevent.
# This gate inspects the stored bytes instead of trusting the attribute.
#
# The pinned set is read back from the attributes (`git ls-files --eol`), so
# .gitattributes stays the single source of truth and new rules are covered
# without editing this script. On a clean CI checkout the index equals HEAD,
# so the result describes the committed tree; locally it also catches a CRLF
# blob that is staged but not yet committed.

set -euo pipefail

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

tab=$(printf '\t')
pinned=0
bad=()

while IFS= read -r -d '' record; do
  meta="${record%%"$tab"*}"
  path="${record#*"$tab"}"

  case "$meta" in
    *"attr/"*"eol=lf"*) ;;
    *) continue ;;
  esac

  pinned=$((pinned + 1))
  case "$meta" in
    i/crlf*|i/mixed*) bad+=("$path") ;;
  esac
done < <(git ls-files --eol -z)

if [ "$pinned" -eq 0 ]; then
  echo "ERROR: no tracked file is pinned to LF — .gitattributes is missing or broken." >&2
  exit 1
fi

if [ "${#bad[@]}" -gt 0 ]; then
  echo "ERROR: pinned file(s) are stored with CRLF line endings:"
  printf '  %s\n' "${bad[@]}"
  echo
  echo "An attribute cannot repair a committed blob; the stored bytes must"
  echo "change. Renormalize and commit:"
  echo "  git add --renormalize ${bad[*]}"
  echo
  exit 1
fi

echo "check_lf_endings: OK — $pinned pinned files stored as LF"
