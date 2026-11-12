#!/usr/bin/env bash
# Renders @PDK_*@ placeholders in a Yosys script from a PDK descriptor. Yosys
# scripts cannot read Tcl variables, so the .ys flows are templates rendered
# from the same descriptor the Tcl flows load.
#
#   syn/pdk/render.sh [--pdk NAME] TEMPLATE [OUTPUT]
#
# Without OUTPUT the rendered script goes to stdout. Unresolved placeholders
# are an error: a missing descriptor field must not silently drop a library.
set -euo pipefail

pdk="${PDK:-sky130hd}"
if [ "${1:-}" = "--pdk" ]; then
    [ $# -ge 2 ] || { echo "usage: $0 [--pdk NAME] TEMPLATE [OUTPUT]" >&2; exit 2; }
    pdk="$2"
    shift 2
fi
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "usage: $0 [--pdk NAME] TEMPLATE [OUTPUT]" >&2
    exit 2
fi

dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
desc="$dir/$pdk.pdk"
[ -r "$desc" ] || { echo "$0: no PDK descriptor '$pdk' ($desc)" >&2; exit 1; }

subs=()
while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|'#'*) continue ;; esac
    case "$line" in *=*) ;; *)
        echo "$0: $desc: expected KEY=VALUE, got '$line'" >&2
        exit 1
    esac
    key="${line%%=*}"
    val="${line#*=}"
    key="${key//[[:space:]]/}"
    val="${val#"${val%%[![:space:]]*}"}"
    val="${val%"${val##*[![:space:]]}"}"
    if [ "${#val}" -ge 2 ] && [ "${val:0:1}" = '"' ] && [ "${val: -1}" = '"' ]; then
        val="${val:1:${#val}-2}"
    fi
    val="${val//\\/\\\\}"
    val="${val//&/\\&}"
    val="${val//|/\\|}"
    subs+=(-e "s|@${key}@|${val}|g")
done < "$desc"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
sed "${subs[@]}" "$1" > "$tmp"

leftover="$(grep -oE '@PDK_[A-Z0-9_]+@' "$tmp" | sort -u | tr '\n' ' ' || true)"
if [ -n "$leftover" ]; then
    echo "$0: $desc does not define: $leftover" >&2
    exit 1
fi

if [ $# -eq 2 ]; then
    cat "$tmp" > "$2"
else
    cat "$tmp"
fi
