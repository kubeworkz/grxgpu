#!/usr/bin/env python3
"""Check that the GF180 flow and RTL agree on the selected chip configuration.

Exit 0 when slot geometry, clock, SRAM/cache sizing, and configured RTL sources
are consistent. Any drift is reported as a FAIL and returns exit 1.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "design_name": "grx930_test_chip",
    "die_area": (0, 0, 3930, 5120),
    "core_area": (441, 441, 3489, 4679),
    "clock_port": "i_clk",
    "clock_period_ns": 40.0,
    "clock_hz": 25_000_000,
    "sram_bytes": 2048,
    "cache_bytes": 512,
    "cache_line_bytes": 32,
}
CORE_FILES = (
    "riscv_core_top.sv",
    "riscv_core_icache_controller.sv",
    "riscv_core_icache_memory.sv",
    "riscv_core_icache_top.sv",
    "riscv_core_dcache_controller.sv",
    "riscv_core_dcache_memory.sv",
    "riscv_core_dcache_top.sv",
)


def area(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a four-coordinate string")
    try:
        result = tuple(int(v) for v in value.replace(",", " ").split())
    except ValueError as exc:
        raise ValueError(f"{name} contains a non-integer coordinate") from exc
    if len(result) != 4:
        raise ValueError(f"{name} must have four coordinates")
    return result


def check(root=ROOT):
    failures = []

    def require(condition, message):
        if not condition:
            failures.append(message)

    configs = {
        "OpenLane RTL": root / "openlane2_rtl/config.json",
        "OpenLane design": root / "openlane2_design/config.json",
    }
    parsed = {}
    for label, path in configs.items():
        try:
            parsed[label] = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"{label} config unreadable/invalid ({path}): {exc}")

    for label, cfg in parsed.items():
        require(cfg.get("DESIGN_NAME") == EXPECTED["design_name"],
                f"{label}: DESIGN_NAME must be {EXPECTED['design_name']!r}")
        require(cfg.get("CLOCK_PORT") == EXPECTED["clock_port"],
                f"{label}: CLOCK_PORT must be {EXPECTED['clock_port']!r}")
        require(cfg.get("FP_SIZING") == "absolute",
                f"{label}: FP_SIZING must be 'absolute' for the configured slot geometry")
        require(cfg.get("PDK") == "gf180mcuD",
                f"{label}: PDK must be gf180mcuD")
        require(cfg.get("STD_CELL_LIBRARY") == "gf180mcu_fd_sc_mcu7t5v0",
                f"{label}: STD_CELL_LIBRARY must be gf180mcu_fd_sc_mcu7t5v0")
        require(cfg.get("CLOCK_PERIOD") == EXPECTED["clock_period_ns"],
                f"{label}: CLOCK_PERIOD must be {EXPECTED['clock_period_ns']} ns (25 MHz)")
        try:
            require(area(cfg.get("DIE_AREA"), "DIE_AREA") == EXPECTED["die_area"],
                    f"{label}: DIE_AREA must be {EXPECTED['die_area']} µm")
        except ValueError as exc:
            failures.append(f"{label}: {exc}")
        try:
            require(area(cfg.get("CORE_AREA"), "CORE_AREA") == EXPECTED["core_area"],
                    f"{label}: CORE_AREA must be {EXPECTED['core_area']} µm")
        except ValueError as exc:
            failures.append(f"{label}: {exc}")

    rtl_cfg = parsed.get("OpenLane RTL")
    design_cfg = parsed.get("OpenLane design")
    if rtl_cfg is not None:
        require(rtl_cfg.get("VERILOG_FILES") == "dir::src/*.sv",
                "OpenLane RTL: VERILOG_FILES must select src/*.sv")
    if design_cfg is not None:
        require(design_cfg.get("VERILOG_FILES") == "dir::../openlane2_rtl/src/*.sv",
                "OpenLane design: VERILOG_FILES must select the maintained OpenLane RTL, not archived netlists")

    top_path = root / "grx930_test_chip.sv"
    ol_top_path = root / "openlane2_rtl/src/grx930_test_chip.sv"
    try:
        top = top_path.read_text()
        ol_top = ol_top_path.read_text()
        require(top == ol_top,
                "root and OpenLane grx930_test_chip.sv sources have drifted")
        require(bool(re.search(r"\bmodule\s+grx930_test_chip\b", top)),
                "top RTL must declare module grx930_test_chip")
        freq = re.search(r"\bparameter\s+int\s+CLK_FREQ\s*=\s*([\d_]+)", top)
        require(freq is not None and int(freq.group(1).replace("_", "")) == EXPECTED["clock_hz"],
                "top RTL CLK_FREQ must be 25_000_000 Hz (consistent with 40 ns)")

        icache = re.search(r"\.ICACHE_INDEX_WIDTH\s*\(\s*(\d+)\s*\)", top)
        dcache = re.search(r"\.DCACHE_INDEX_WIDTH\s*\(\s*(\d+)\s*\)", top)
        require(icache is not None and dcache is not None,
                "top RTL must set both I-cache and D-cache index widths")
        if icache and dcache:
            line_bytes = EXPECTED["cache_line_bytes"]
            cache_sizes = tuple((1 << int(m.group(1))) * line_bytes for m in (icache, dcache))
            require(cache_sizes == (EXPECTED["cache_bytes"], EXPECTED["cache_bytes"]),
                    f"I/D cache data arrays must each be {EXPECTED['cache_bytes']} B (found {cache_sizes[0]} B and {cache_sizes[1]} B)")
            for instance, width in (("icache", int(icache.group(1))), ("dcache", int(dcache.group(1)))):
                core_top = root / "openlane2_rtl/src/riscv_core_top.sv"
                core_source = core_top.read_text()
                parameter = "ICACHE_INDEX_WIDTH" if instance == "icache" else "DCACHE_INDEX_WIDTH"
                require(bool(re.search(rf"\.INDEX_WIDTH\s*\(\s*{parameter}\s*\)", core_source)),
                        f"riscv_core_top.sv: {parameter} must propagate to {instance}")
                top_file = root / f"openlane2_rtl/src/riscv_core_{instance}_top.sv"
                memory_file = root / f"openlane2_rtl/src/riscv_core_{instance}_memory.sv"
                for path in (top_file, memory_file):
                    try:
                        source = path.read_text()
                        require(bool(re.search(r"\bparameter\s+INDEX_WIDTH\s*=\s*7\b", source)),
                                f"{path.name}: generic INDEX_WIDTH default must remain 7")
                        if path == memory_file:
                            require(bool(re.search(r"2\s*\*\*\s*INDEX_WIDTH", source)),
                                    f"{path.name}: cache capacity must scale as 2**INDEX_WIDTH")
                            require(bool(re.search(r"\bparameter\s+AXI_DATA_WIDTH\s*=\s*256\b", source)),
                                    f"{path.name}: cache line width must remain 256 bits (32 B)")
                    except OSError as exc:
                        failures.append(f"cache RTL unreadable ({path.name}): {exc}")
                try:
                    cache_top = top_file.read_text()
                    cache_memory = memory_file.read_text()
                    if instance == "icache":
                        require("riscv_core_icache_memory #(.INDEX_WIDTH(INDEX_WIDTH)" in cache_top,
                                f"{top_file.name}: index width must reach cache memory")
                        require(bool(re.search(r"INSTR_MEM\s*\[0\s*:\s*CACHE_DEPTH\s*-\s*1\]", cache_memory)),
                                f"{memory_file.name}: I-cache array must use CACHE_DEPTH")
                    else:
                        require("riscv_core_dcache_memory #(.INDEX_WIDTH(INDEX_WIDTH)" in cache_top,
                                f"{top_file.name}: index width must reach cache memory")
                        require(bool(re.search(r"DATA_MEM\s*\[0\s*:\s*CACHE_DEPTH\s*-\s*1\]", cache_memory)),
                                f"{memory_file.name}: D-cache array must use CACHE_DEPTH")
                except OSError as exc:
                    failures.append(f"cache RTL unreadable ({instance}): {exc}")

        depth = re.search(r"\blocalparam\s+int\s+DEPTH\s*=\s*(\d+)", top)
        sram = re.search(r"\bmodule\s+grx930_sram_2kb\b", top)
        word_array = re.search(r"\blogic\s*\[63:0\]\s+mem\s*\[DEPTH\s*-\s*1\s*:\s*0\]", top)
        sram_instance = re.search(r"\bgrx930_sram_2kb\s+u_sram\s*\(", top)
        require(sram is not None and sram_instance is not None and
                depth is not None and word_array is not None,
                "top RTL must instantiate a 64-bit-word grx930_sram_2kb storage array")
        if depth:
            sram_bytes = int(depth.group(1)) * 8  # 64-bit storage words
            require(sram_bytes == EXPECTED["sram_bytes"],
                    f"main SRAM must be {EXPECTED['sram_bytes']} B (found {sram_bytes} B)")
    except OSError as exc:
        failures.append(f"top RTL unreadable: {exc}")

    canonical = root.parent.parent / "rv64imac/RTL"
    ol_source = root / "openlane2_rtl/src"
    for name in CORE_FILES:
        canonical_file = canonical / name
        ol_file = ol_source / name
        try:
            require(ol_file.read_bytes() == canonical_file.read_bytes(),
                    f"OpenLane RTL {name} differs from canonical rv64imac/RTL source")
        except OSError as exc:
            failures.append(f"core source missing/unreadable ({name}): {exc}")

    for name in ("flow_openroad_gf180mcu.tcl", "flow_openroad_gf180mcu_cts.tcl"):
        try:
            text = (root / name).read_text()
            require(bool(re.search(r"create_clock\s+-name\s+i_clk\s+-period\s+40(?:\.0)?\b", text)),
                    f"{name}: clock must be 40 ns on i_clk")
            require(bool(re.search(r"-die_area\s+\{0\s+0\s+3930\s+5120\}", text)),
                    f"{name}: die area must be 3930×5120 µm")
            require(bool(re.search(r"-core_area\s+\{441\s+441\s+3489\s+4679\}", text)),
                    f"{name}: core area must be {EXPECTED['core_area']} µm")
        except OSError as exc:
            failures.append(f"{name} unreadable: {exc}")

    try:
        runner = (root / "run_ol2.sh").read_text()
        require(bool(re.search(r"\$\{PYTHON:-python3\}\s+check_configuration\.py", runner)) and
                bool(re.search(r"openlane\s+openlane2_rtl/config\.json\b", runner)),
                "run_ol2.sh must validate configuration and run openlane2_rtl/config.json")
        require("openlane2_design/config.json" not in runner,
                "run_ol2.sh must not run the stale synthesized-netlist config")
    except OSError as exc:
        failures.append(f"run_ol2.sh unreadable: {exc}")
    try:
        runner = (root / "run_ol2_cts.sh").read_text()
        require(bool(re.search(r"cd\s+c930/asic_gf180mcu(?:/openlane2_rtl)?", runner)) and
                bool(re.search(r"\$\{PYTHON:-python3\}\s+check_configuration\.py", runner)) and
                bool(re.search(r"openlane\s+--pdk\s+gf180mcuD\s+config\.json\b", runner)),
                "run_ol2_cts.sh must validate and run config.json from openlane2_rtl")
        require("openlane2_design/config.json" not in runner,
                "run_ol2_cts.sh must not run the stale synthesized-netlist config")
    except OSError as exc:
        failures.append(f"run_ol2_cts.sh unreadable: {exc}")

    if failures:
        for message in failures:
            print(f"FAIL: {message}")
        print(f"\nConfiguration check failed ({len(failures)} issue(s)).")
        return 1

    print("PASS: 1×1 slot (3930×5120 µm die; 3048×4238 µm core budget), "
          "25 MHz / 40 ns, 2 KiB SRAM, 512 B I/D cache arrays, "
          "and canonical active RTL sources agree.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
