#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROBE="${TFR_WMUL_PROBE_DIR:-$ROOT/build32/g100-slang-exact-128c/run-20261022/wmul-cost-probe-20261024}"
RUN_ROOT="$ROOT/build32/g100-slang-exact-128c/run-20261022"
YOSYS="$RUN_ROOT/worktest/bin/yosys"
PLUGIN="$RUN_ROOT/worktest/share/yosys/plugins/synlig-sv.so"
OUT="${1:-$PROBE/ooc-matrix-$(date -u +%Y%m%d-%H%M%S)}"

for required in "$YOSYS" "$PLUGIN" \
    "$PROBE/isolated-baseline/VX_tcu_tfr_wmul.sv" \
    "$PROBE/isolated-candidate/VX_tcu_tfr_wmul.sv" \
    "$PROBE/native-src/VX_define.vh" \
    "$ROOT/hw/rtl/libs/VX_wallace_mul.sv" \
    "$ROOT/hw/rtl/libs/VX_csa_tree.sv" \
    "$ROOT/hw/rtl/libs/VX_csa_42.sv" \
    "$ROOT/hw/rtl/libs/VX_csa_32.sv" \
    "$ROOT/hw/rtl/libs/VX_ks_adder.sv"; do
    [[ -f "$required" ]] || { echo "Missing required file: $required" >&2; exit 1; }
done
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

# Distinct USE_DSP=0 configurations instantiated by the TCU's TFR arithmetic.
# P defaults to N+M in the RTL for all of these instances.
cases=(
    'fp16_mantissa|11|11|1|0'
    'fp8_pair|4|4|2|0'
    'mx_nv_fp4_pair|2|2|2|0'
    'nvfp4_scale|4|4|1|0'
    'nvfp4_shared_scale_terms|4|8|2|1'
)

for entry in "${cases[@]}"; do
    IFS='|' read -r name n m lanes shared <<< "$entry"
    p=$((n + m))
    case_root="$OUT/$name"
    mkdir -p "$case_root"

    for variant in baseline candidate; do
        work="$case_root/$variant"
        mkdir -p "$work/src"
        cp "$PROBE/isolated-$variant/VX_tcu_tfr_wmul.sv" "$work/src/"
        cp "$PROBE/native-src/VX_define.vh" "$PROBE/native-src/VX_platform.vh" \
           "$PROBE/native-src/VX_config.vh" "$PROBE/native-src/VX_types.vh" \
           "$PROBE/native-src/VX_scope.vh" "$work/src/"
        cp "$ROOT/hw/rtl/libs/VX_wallace_mul.sv" \
           "$ROOT/hw/rtl/libs/VX_csa_tree.sv" \
           "$ROOT/hw/rtl/libs/VX_csa_42.sv" \
           "$ROOT/hw/rtl/libs/VX_csa_32.sv" \
           "$ROOT/hw/rtl/libs/VX_ks_adder.sv" "$work/src/"

        cat > "$work/src/VX_tfr_wmul_ooc.sv" <<EOF
module VX_tfr_wmul_ooc (
    input  wire [$((lanes - 1)):0][$((n - 1)):0] a,
    input  wire [$((lanes - 1)):0][$((m - 1)):0] b,
    output wire [$((lanes - 1)):0][$((p - 1)):0] p
);
    wire [$((lanes - 1)):0][$((p - 1)):0] p_lane;
    VX_tcu_tfr_wmul #(
        .N        ($n),
        .M        ($m),
        .LANES    ($lanes),
        .SHARED_B ($shared),
        .P        ($p),
        .USE_DSP  (0)
    ) dut (
        .a (a),
        .b (b),
        .p (p_lane)
    );
    assign p = p_lane;
endmodule
EOF

        cat > "$work/run.ys" <<EOF
read_systemverilog -lowmem -mt 1 -mp 1 -noinfo -DASIC -DSYNTHESIS -DYOSYS -top VX_tfr_wmul_ooc -I$work/src \\
  $work/src/VX_wallace_mul.sv \\
  $work/src/VX_csa_tree.sv \\
  $work/src/VX_csa_42.sv \\
  $work/src/VX_csa_32.sv \\
  $work/src/VX_ks_adder.sv \\
  $work/src/VX_tcu_tfr_wmul.sv \\
  $work/src/VX_tfr_wmul_ooc.sv
hierarchy -check -top VX_tfr_wmul_ooc
stat
write_rtlil $work/Vortex_wmul_ooc.rtlil
EOF
        printf 'case=%s\nN=%s\nM=%s\nLANES=%s\nSHARED_B=%s\nP=%s\nUSE_DSP=0\nvariant=%s\nstart_utc=%s\n' \
            "$name" "$n" "$m" "$lanes" "$shared" "$p" "$variant" \
            "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$work/run.status"
        start_ns=$(date +%s%N)
        set +e
        /usr/bin/time -v timeout --signal=TERM --kill-after=10s 300s \
            "$YOSYS" -m "$PLUGIN" -Q -s "$work/run.ys" -l "$work/yosys.log" \
            > "$work/yosys.stdout.log" 2>&1
        rc=$?
        set -e
        end_ns=$(date +%s%N)
        printf 'exit=%s\nelapsed_seconds=%.3f\nend_utc=%s\n' \
            "$rc" "$(awk -v s="$start_ns" -v e="$end_ns" 'BEGIN {print (e-s)/1e9}')" \
            "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$work/run.status"
        if [[ $rc -ne 0 ]]; then
            echo "$name/$variant failed (exit $rc); inspect $work/yosys.stdout.log" >&2
            exit "$rc"
        fi
        grep -q 'Executing HIERARCHY pass' "$work/yosys.log"
        grep -q '^=== design hierarchy ===' "$work/yosys.log"
        grep -q 'VX_tfr_wmul_ooc' "$work/yosys.stdout.log"
        grep -q '\[  FATAL\] : 0' "$work/yosys.stdout.log"
        grep -q '\[ SYNTAX\] : 0' "$work/yosys.stdout.log"
        grep -q '\[  ERROR\] : 0' "$work/yosys.stdout.log"
        grep -q 'End of script\.' "$work/yosys.log"
        [[ -s "$work/Vortex_wmul_ooc.rtlil" ]]
        awk '/^=== design hierarchy ===/{capture=1} capture{print} /^4\. Executing RTLIL backend/{exit}' \
            "$work/yosys.log" > "$work/structure.txt"
        grep -E '^   VX_tfr_wmul_ooc|^   Number of cells:|^     \$' \
            "$work/structure.txt" > "$work/summary.txt"
        grep -E 'End of script\.|Time spent:' "$work/yosys.log" >> "$work/summary.txt"
    done

    base_files=$(find "$case_root/baseline/src" -maxdepth 1 -type f -printf '%f\n' | sort)
    candidate_files=$(find "$case_root/candidate/src" -maxdepth 1 -type f -printf '%f\n' | sort)
    [[ "$base_files" == "$candidate_files" ]]
    differences=$(for file in $base_files; do
        cmp -s "$case_root/baseline/src/$file" "$case_root/candidate/src/$file" || printf '%s\n' "$file"
    done)
    [[ "$differences" == "VX_tcu_tfr_wmul.sv" ]]
    for header in VX_define.vh VX_platform.vh VX_config.vh VX_types.vh VX_scope.vh; do
        cmp -s "$case_root/baseline/src/$header" "$case_root/candidate/src/$header"
    done
    source_count=$(grep -c '\.sv' "$case_root/baseline/run.ys")
    {
        printf 'case=%s\nN=%s\nM=%s\nLANES=%s\nSHARED_B=%s\nP=%s\nUSE_DSP=0\n' \
            "$name" "$n" "$m" "$lanes" "$shared" "$p"
        printf 'source_file_count=%s\nsource_reference_count=%s\n' \
            "$(wc -l <<< "$base_files" | tr -d ' ')" "$source_count"
        printf 'only_rtl_difference=%s\nheaders_identical=true\n' "$differences"
        printf 'include_option=-I<single-token-stage-path>\nscratch=independent per run\n'
    } > "$case_root/staging.validation.txt"
done

python3 - "$OUT" <<'PY'
import pathlib, re, sys
out = pathlib.Path(sys.argv[1])
print("case N M lanes shared P | baseline s / KB / cells | candidate s / KB / cells")
for validation in sorted(out.glob("*/staging.validation.txt")):
    values = dict(line.split("=", 1) for line in validation.read_text().splitlines() if "=" in line)
    fields = [values[k] for k in ("case", "N", "M", "LANES", "SHARED_B", "P")]
    metrics = []
    for variant in ("baseline", "candidate"):
        work = validation.parent / variant
        status = dict(line.split("=", 1) for line in (work / "run.status").read_text().splitlines() if "=" in line)
        text = (work / "yosys.stdout.log").read_text(errors="replace")
        rss = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", text)
        summary = (work / "structure.txt").read_text(errors="replace")
        cells = re.search(r"Number of cells:\s*(\d+)", summary)
        metrics.extend((status.get("elapsed_seconds", "?"), rss.group(1) if rss else "?", cells.group(1) if cells else "?"))
    print(f"{' '.join(fields[:1])} {fields[1]} {fields[2]} {fields[3]} {fields[4]} {fields[5]} | "
          f"{metrics[0]} / {metrics[1]} / {metrics[2]} | {metrics[3]} / {metrics[4]} / {metrics[5]}")
print(f"out={out}")
PY
