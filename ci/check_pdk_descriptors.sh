#!/bin/bash
# CI guard: PDK descriptors are complete, well formed and stored LF.
#
# syn/pdk/*.pdk is the only place a process value is allowed to live in the
# syn/ flows, so a descriptor that is CRLF, malformed, or missing a field
# either fails somewhere inside OpenROAD or — worse — lets a flow run without
# the library it thinks it has. The loader and renderer check at run time; this
# gate checks the stored blob, so the problem is reported on the commit that
# introduces it.
#
# A descriptor marked PDK_READY=0 is a skeleton for a process whose libraries
# have not been delivered: it may leave the library and cell values empty, but
# it must still parse and still carry every field name, so filling it is an
# edit rather than a rediscovery of the contract in syn/pdk/README.md.

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

# Byte semantics: the line-ending scan below compares byte counts.
export LC_ALL=C

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! git -C "$ROOT" rev-parse --git-dir > /dev/null 2>&1; then
  echo "check_pdk_descriptors: $ROOT is not a git checkout" >&2
  exit 1
fi

cd "$ROOT"

IDENTITY_FIELDS="PDK_NAME PDK_DESCRIPTION PDK_NODE_NM PDK_READY"
LIBRARY_FIELDS="PDK_LIBERTY PDK_TECH_LEF PDK_CELL_LEF"
MACRO_FIELDS="PDK_POWER_NET PDK_GROUND_NET PDK_STORAGE_CELL PDK_TRISTATE_CELL PDK_INV_CELL PDK_TAP_CELL"
MACRO_FIELDS="$MACRO_FIELDS PDK_FILLER_CELLS PDK_MAX_TAP_DIST PDK_HAS_ORRAM"
MACRO_FIELDS="$MACRO_FIELDS PDK_ROUTING_LAYER PDK_VER_LAYER PDK_HOR_LAYER"
KNOWN_FIELDS="$IDENTITY_FIELDS $LIBRARY_FIELDS $MACRO_FIELDS"

if [ "$STAGED" -eq 1 ]; then
  mapfile -t paths < <(git diff --cached --name-only --diff-filter=ACMR -- 'syn/pdk/*.pdk')
else
  mapfile -t paths < <(git ls-files -- 'syn/pdk/*.pdk')
fi

where="tracked tree"
[ "$STAGED" -eq 1 ] && where="staged files"

if [ "${#paths[@]}" -eq 0 ]; then
  echo "check_pdk_descriptors: OK — $where: no descriptors"
  exit 0
fi

status=0
ready=0
skeleton=0
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

for path in "${paths[@]}"; do
  declare -A present=() value=()
  problems=()

  git cat-file blob ":$path" > "$tmp"

  if [ "$(tr -d '\r' < "$tmp" | wc -c)" -ne "$(wc -c < "$tmp")" ]; then
    problems+=("stored with CRLF line endings")
  fi

  lineno=0
  while IFS= read -r line || [ -n "$line" ]; do
    lineno=$((lineno + 1))
    line="${line%$'\r'}"
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac

    if [[ "$line" != *=* ]]; then
      problems+=("line $lineno: expected KEY=VALUE, got '$line'")
      continue
    fi
    key="${line%%=*}"
    val="${line#*=}"

    if ! [[ "$key" =~ ^PDK_[A-Z0-9_]+$ ]]; then
      problems+=("line $lineno: '$key' is not a PDK_ field name")
      continue
    fi
    if [[ " $KNOWN_FIELDS " != *" $key "* ]]; then
      problems+=("line $lineno: unknown field $key")
      continue
    fi
    if [ -n "${present[$key]:-}" ]; then
      problems+=("line $lineno: duplicate field $key")
      continue
    fi
    present[$key]=1

    val="${val#"${val%%[![:space:]]*}"}"
    val="${val%"${val##*[![:space:]]}"}"
    if [ "${#val}" -ge 2 ] && [ "${val:0:1}" = '"' ] && [ "${val: -1}" = '"' ]; then
      val="${val:1:${#val}-2}"
    fi
    value[$key]=$val
  done < "$tmp"

  for key in $KNOWN_FIELDS; do
    [ -n "${present[$key]:-}" ] || problems+=("missing field $key")
  done

  # Identity is filled even in a skeleton: it is what names the process the
  # file describes, and what an error message quotes back.
  for key in PDK_NAME PDK_NODE_NM; do
    [ -n "${value[$key]:-}" ] || problems+=("$key is empty")
  done

  ready_flag="${value[PDK_READY]:-}"
  case "$ready_flag" in
    0|1|"") ;;
    *) problems+=("PDK_READY must be 0 or 1, got '$ready_flag'") ;;
  esac
  orram_flag="${value[PDK_HAS_ORRAM]:-}"
  case "$orram_flag" in
    0|1|"") ;;
    *) problems+=("PDK_HAS_ORRAM must be 0 or 1, got '$orram_flag'") ;;
  esac

  if [ "$ready_flag" = "1" ]; then
    for key in $LIBRARY_FIELDS; do
      [ -n "${value[$key]:-}" ] || problems+=("PDK_READY=1 but $key is empty")
    done
    if [ "$orram_flag" = "1" ]; then
      for key in $MACRO_FIELDS; do
        [ -n "${value[$key]:-}" ] || problems+=("PDK_HAS_ORRAM=1 but $key is empty")
      done
    fi
  fi

  if [ "${#problems[@]}" -eq 0 ]; then
    if [ "$ready_flag" = "1" ]; then
      ready=$((ready + 1))
    else
      skeleton=$((skeleton + 1))
    fi
    continue
  fi

  status=1
  echo "ERROR: $path"
  printf '  %s\n' "${problems[@]}"
  echo
done

if [ "$status" -ne 0 ]; then
  echo "A descriptor is what a flow maps against, so it must be complete and"
  echo "stored LF before it lands. The field set is documented in"
  echo "  syn/pdk/README.md"
  exit 1
fi

echo "check_pdk_descriptors: OK — $where: ${#paths[@]} descriptors, $ready ready, $skeleton skeleton"
