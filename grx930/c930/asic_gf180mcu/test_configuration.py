#!/usr/bin/env python3
"""Regression tests for the GF180 configuration drift checker."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import check_configuration

SOURCE_ROOT = Path(__file__).resolve().parent
CORE_FILES = check_configuration.CORE_FILES
COPIED_FILES = (
    "grx930_test_chip.sv",
    "openlane2_rtl/config.json",
    "openlane2_rtl/src/grx930_test_chip.sv",
    "openlane2_design/config.json",
    "flow_openroad_gf180mcu.tcl",
    "flow_openroad_gf180mcu_cts.tcl",
    "run_ol2.sh",
    "run_ol2_cts.sh",
)


class ConfigurationDriftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.root = self.repo / "grx930/c930/asic_gf180mcu"
        for relative in COPIED_FILES:
            source = SOURCE_ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        canonical = self.repo / "grx930/rv64imac/RTL"
        canonical.mkdir(parents=True)
        for name in CORE_FILES:
            shutil.copy2(SOURCE_ROOT.parent.parent / "rv64imac/RTL" / name,
                         canonical / name)
        for name in CORE_FILES:
            shutil.copy2(canonical / name, self.root / "openlane2_rtl/src" / name)

    def tearDown(self):
        self.temp.cleanup()

    def check_result(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = check_configuration.check(self.root)
        return result, output.getvalue()

    def update_config(self, directory, key, value):
        path = self.root / directory / "config.json"
        config = json.loads(path.read_text())
        config[key] = value
        path.write_text(json.dumps(config))

    def assert_drift_rejected(self, expected_message):
        result, output = self.check_result()
        self.assertEqual(result, 1, output)
        self.assertIn(expected_message, output)

    def test_current_configuration_passes(self):
        result, output = self.check_result()
        self.assertEqual(result, 0, output)
        self.assertIn("25 MHz / 40 ns", output)

    def test_die_geometry_drift_is_rejected(self):
        self.update_config("openlane2_rtl", "DIE_AREA", "0 0 4000 5120")
        self.assert_drift_rejected("DIE_AREA")

    def test_clock_period_drift_is_rejected(self):
        self.update_config("openlane2_design", "CLOCK_PERIOD", 20.0)
        self.assert_drift_rejected("CLOCK_PERIOD")

    def test_sram_depth_drift_is_rejected(self):
        path = self.root / "grx930_test_chip.sv"
        path.write_text(path.read_text().replace("localparam int DEPTH = 256",
                                                 "localparam int DEPTH = 512", 1))
        (self.root / "openlane2_rtl/src/grx930_test_chip.sv").write_text(path.read_text())
        self.assert_drift_rejected("main SRAM must be 2048 B")

    def test_cache_size_drift_is_rejected(self):
        path = self.root / "grx930_test_chip.sv"
        path.write_text(path.read_text().replace(".ICACHE_INDEX_WIDTH (4)",
                                                 ".ICACHE_INDEX_WIDTH (5)", 1))
        (self.root / "openlane2_rtl/src/grx930_test_chip.sv").write_text(path.read_text())
        self.assert_drift_rejected("I/D cache data arrays must each be 512 B")

    def test_archived_netlist_source_selection_is_rejected(self):
        self.update_config("openlane2_design", "VERILOG_FILES", "dir::src/*.v")
        self.assert_drift_rejected("OpenLane design: VERILOG_FILES")

    def test_canonical_core_source_drift_is_rejected(self):
        path = self.root / "openlane2_rtl/src/riscv_core_top.sv"
        path.write_text(path.read_text() + "\n// drift\n")
        self.assert_drift_rejected("differs from canonical rv64imac/RTL source")


if __name__ == "__main__":
    unittest.main(verbosity=2)
