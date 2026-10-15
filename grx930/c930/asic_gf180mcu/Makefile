# Makefile — GRX930 test chip for wafer.space GF180MCU shuttle
#
# Targets wafer.space 1×1 slot (3.93mm × 5.12mm, 12.92 mm² core)
#
# Usage:
#   cd c930/asic_gf180mcu
#   make gates        # Validate and print the configuration summary
#   make check-config # Check slot, clock, SRAM, cache and RTL-source consistency
#   make test-config  # Test that configuration drift is caught
#   make synth       # Yosys synthesis → GF180MCU
#   make pnr         # OpenROAD place & route
#   make signoff     # DRC + LVS check
#   make submit      # Prepare wafer.space submission package
#   make clean       # Remove build artifacts

TOP       = grx930_test_chip
BUILD     = build
RTL_DIR   = ../rtl
RV_DIR    = ../rv64imac/RTL

# GF180MCU PDK (set in environment)
PDK_ROOT ?= /usr/local/share/pdk/gf180mcu
PYTHON   ?= python3

.PHONY: all gates check-config test-config synth pnr signoff submit clean

all: gates

check-config:
	$(PYTHON) check_configuration.py


test-config:
	$(PYTHON) -m unittest -v test_configuration.py


# ============================================================
# Configuration summary (not a synthesized area estimate)
# ============================================================
gates: check-config
	@echo "=== GRX930 GF180MCU Configuration ==="
	@echo "Slot:       wafer.space 1×1"
	@echo "Die:        3930 × 5120 µm"
	@echo "Core:       3048 × 4238 µm (12.92 mm² configured budget; fit pending)"
	@echo "Clock:      25 MHz target (40 ns period)"
	@echo "I-cache:    512 B data array (16 × 32 B lines)"
	@echo "D-cache:    512 B data array (16 × 32 B lines)"
	@echo "Main SRAM:  2 KiB inferred flip-flop array; no SRAM macro"
	@echo "Area/timing closure: not established; run synthesis and physical design"
	@echo "OpenLane2 source: openlane2_rtl/src/*.sv (canonical RTL, not archived netlists)"

# ============================================================
# Yosys synthesis
# ============================================================
$(BUILD):
	mkdir -p $(BUILD)

synth: check-config $(BUILD)
	yosys -s synth_gf180mcu.ys 2>&1 | tee $(BUILD)/synth.log
	@echo "=== Synthesis complete ==="
	@echo "Output: $(BUILD)/grx930_test_chip_synth.v"

# ============================================================
# OpenROAD physical design
# ============================================================
pnr: synth
	PDK_ROOT=$(PDK_ROOT) openroad -exit flow_openroad_gf180mcu.tcl 2>&1 | tee $(BUILD)/pnr.log
	@echo "=== Physical design complete ==="
	@echo "Output: $(BUILD)/grx930_test_chip_routed.gds"

# ============================================================
# Signoff (DRC + LVS)
# ============================================================
signoff: pnr
	@echo "=== Running DRC ==="
	magic -noconsole -dnull \
		-c "tech read $(PDK_ROOT)/gf180mcu_fd_sc_mcu7t5v0/gf180mcu_fd_sc_mcu7t5v0.tech" \
		-c "gds read $(BUILD)/grx930_test_chip_routed.gds" \
		-c "drc list" \
		-c "quit" 2>&1 | tee $(BUILD)/drc.log
	@echo "=== Running LVS ==="
	netgen -script lvs_gf180mcu.tcl 2>&1 | tee $(BUILD)/lvs.log
	@echo "=== Signoff complete ==="

# ============================================================
# wafer.space submission package
# ============================================================
submit: signoff
	@echo "=== Preparing wafer.space submission ==="
	mkdir -p $(BUILD)/submission
	cp $(BUILD)/grx930_test_chip_routed.gds $(BUILD)/submission/
	cp $(BUILD)/grx930_test_chip_routed.v   $(BUILD)/submission/
	cp $(BUILD)/grx930_test_chip_routed.spef $(BUILD)/submission/
	cp pad_ring.cfg                          $(BUILD)/submission/
	cp $(BUILD)/drc.log                      $(BUILD)/submission/
	cp $(BUILD)/lvs.log                      $(BUILD)/submission/
	@echo ""
	@echo "=== Submission package ready ==="
	@echo "Directory: $(BUILD)/submission/"
	@echo ""
	@echo "Files to submit to wafer.space:"
	@echo "  1. grx930_test_chip_routed.gds  — Final GDS"
	@echo "  2. grx930_test_chip_routed.v    — Gate-level netlist"
	@echo "  3. grx930_test_chip_routed.spef — Parasitics"
	@echo "  4. pad_ring.cfg                  — Pad configuration"
	@echo "  5. drc.log                       — DRC report (must be clean)"
	@echo "  6. lvs.log                       — LVS report (must be clean)"
	@echo ""
	@echo "Submit at: https://wafer.space"
	@echo "Slot: 1×1 (full) — $8,000 standard / $7,000 early bird"
	@echo "Deadline: 16 December 2026 (GDS submission)"

# ============================================================
# Gate-level simulation
# ============================================================
sim: synth
	iverilog -o $(BUILD)/$(TOP)_synth.vvp \
		$(BUILD)/grx930_test_chip_synth.v \
		../tb/tb_grx930_test_chip.sv
	vvp $(BUILD)/$(TOP)_synth.vvp | tee $(BUILD)/sim.log

# ============================================================
# Clean
# ============================================================
clean:
	rm -rf $(BUILD)
