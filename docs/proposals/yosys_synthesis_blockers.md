# Yosys Synthesis Blockers — GRXGPU TFR Compute Engine

**Date:** 2026-09-03
**Target:** Yosys 0.68 (conda) / Yosys 0.48 (OSS CAD Suite)
**Block:** `hw/rtl/tcu/tfr/` (17 modules, ~5,000 lines)
**Goal:** Synthesize TFR with `hierarchy -top VX_tcu_fedp_tfr` → `synth` → `stat`

---

## 1. Blockers found (ordered by severity)

### BLOCKER 1: Generate-scoped variable declarations

**Severity:** Fatal — cannot synthesize without fixing
**Modules affected:** 14 of 17 TFR modules

Yosys does not support `wire`/`reg`/`logic` declarations inside `for (genvar)` generate blocks. The TFR design uses this pattern extensively:

```systemverilog
for (genvar i = 0; i < TCK; ++i) begin : g_lane
    wire lane_valid = vld_mask[i*4];          // ← Yosys error
    wire [7:0] raw_a = a_row[i/2][OFF +: 8]; // ← Yosys error
    // ...
end
```

**Root cause:** In SystemVerilog, generate-block-local declarations create scoped variables. Yosys's Verilog-2005 frontend (even with `-sv` flag) doesn't support this.

**Count:** ~95 generate-scoped declarations across all TFR modules. The worst offenders:

| Module | Gen-scoped wires | Complexity |
|--------|-----------------|------------|
| `VX_tcu_tfr_mul_f4.sv` | 40+ | MXFP4/NVFP4 dual-path, 6 genvar loops |
| `VX_tcu_tfr_align.sv` | 12 | Signed subtractor matrix, alignment |
| `VX_tcu_tfr_mul_f8.sv` | 20+ | FP8/BF8 dual-path, classifier |
| `VX_tcu_tfr_mul_i4.sv` | 12 | Signed/unsigned integer multiply |
| `VX_tcu_tfr_max_exp.sv` | 2 | Maximum exponent finder |
| `VX_tcu_tfr_acc.sv` | 2 | Sign-extension accumulator |

**Fix:** Hoist all generate-scoped declarations to module scope, prefix with `g_<loop>_` to avoid name collisions. Example:

```systemverilog
// Before (Yosys-incompatible):
for (genvar i = 0; i < TCK; ++i) begin : g_lane
    wire lane_valid = vld_mask[i*4];
    wire [7:0] raw_a = a_row[i/2][OFF +: 8];
    assign products[i] = raw_a * raw_b;
end

// After (Yosys-compatible):
wire [TCK-1:0] g_lane_lane_valid;
wire [TCK-1:0][7:0] g_lane_raw_a;
wire [TCK-1:0][7:0] g_lane_raw_b;

for (genvar i = 0; i < TCK; ++i) begin : g_lane
    assign g_lane_lane_valid[i] = vld_mask[i*4];
    assign g_lane_raw_a[i] = a_row[i/2][OFF +: 8];
    assign g_lane_raw_b[i] = b_col[i/2][OFF +: 8];
    assign products[i] = g_lane_raw_a[i] * g_lane_raw_b[i];
end
```

**Alternative (less invasive):** For the ~50 combinational-only generate-scoped wires (used only in `assign` statements within the same block), replace with inline expressions:

```systemverilog
// Before:
wire lane_valid = vld_mask[i*4];
wire [7:0] raw_a = a_row[i/2][OFF +: 8];

// After (inline):
assign products[i] = a_row[i/2][OFF +: 8] * b_col[i/2][OFF +: 8];
```

This reduces the refactor scope to ~45 declarations that are actually used in `always @*` blocks.

---

### BLOCKER 2: `$bits()` system function

**Severity:** High — 326 occurrences in `VX_gpu_pkg.sv`, 2 in TFR
**Modules affected:** All (via package dependency)

Yosys doesn't support `$bits()`. In `VX_gpu_pkg.sv` there are 326 occurrences, mostly in:
- `PACKAGE_ASSERT` macros (assertion-only, stripable)
- `localparam` definitions for type widths (`AMO_REQ_BITS`, `MEM_ATTR_WIDTH`)
- Padding calculations in struct definitions

**Fix for TFR-only synthesis:** The flatten_tfr.py preprocessing already handles this — replaces `$bits(fedp_excep_t)` → `3`, `$bits(fedp_class_t)` → `4`, `$bits(tcu_header_t)` → `32`.

**Fix for full-TCU synthesis:** Requires the VX_gpu_pkg preprocessor to compute concrete widths for all 326 `$bits()` calls from struct definitions.

---

### BLOCKER 3: `import` statements (package imports)

**Severity:** High — all TFR modules use `import VX_tcu_pkg::*`
**Modules affected:** All 17 TFR modules

Yosys cannot parse `import <package>::*` — it has no package awareness.

**Fix:** Already handled by flatten_tfr.py — all package references are replaced with `define` macros and literal constants. The package hierarchy is completely bypassed.

---

### BLOCKER 4: `always_ff` / `always_comb` / `always_latch`

**Severity:** Medium — 12 occurrences across TFR
**Modules affected:** `VX_tcu_tfr_mul_f16.sv`, `VX_tcu_tfr_norm_round.sv`, `VX_tcu_tfr_shared_mul.sv`, `VX_tcu_fedp_tfr.sv`

Yosys doesn't parse `always_ff` or `always_comb` in the Verilog-2005 frontend. Even with `-sv`, these are not in the "small subset" Yosys supports.

**Fix:** Replace all `always_ff @(posedge clk)` → `always @(posedge clk)`, `always_comb` → `always @*`, `always_latch` → `always @*`.

---

### BLOCKER 5: `logic` type in module/generate scope

**Severity:** Medium — ~100 occurrences
**Modules affected:** `VX_tcu_tfr_mul_f8.sv`, `VX_tcu_tfr_mul_f4.sv`, `VX_tcu_fedp_tfr.sv`

Yosys's Verilog-2005 frontend doesn't understand `logic` as a port type or generate-scope declaration.

**Fix:** Replace all `logic` with `wire` (continuous assignment) or `reg` (procedural assignment).

---

### BLOCKER 6: `typedef struct packed`

**Severity:** Medium — `fedp_excep_t`, `fedp_class_t` used in 12 modules
**Modules affected:** All modules that use exception/classification types

Yosys can't parse `typedef struct packed { ... } name;` in its SV subset.

**Fix:** Replace with explicit wire widths:
- `fedp_excep_t` → `logic [2:0]` (is_inf=bit2, is_nan=bit1, sign=bit0)
- `fedp_class_t` → `logic [3:0]` (is_zero=bit3, is_sub=bit2, is_inf=bit1, is_nan=bit0)
- All `.is_inf` → `[2]`, `.is_nan` → `[1]`, `.sign` → `[0]`, `.is_zero` → `[3]`, `.is_sub` → `[2]`

---

### BLOCKER 7: `function automatic` in packages

**Severity:** Medium — 35 functions in `VX_gpu_pkg.sv`, 6 in `VX_tcu_pkg.sv`
**Modules affected:** Via package dependency

Yosys can't parse `function automatic int exp_bits(input int fmt);` with `return` statements.

**Fix:** Already handled by flatten_tfr.py — all functions are replaced with literal values at preprocessing time. Functions that are referenced at elaboration time (e.g., `tcu_fmt_width()`) are replaced with hardcoded constants.

---

### BLOCKER 8: `STRING` type parameter

**Severity:** Low — `parameter STRING INSTANCE_ID = ""` in 10+ modules
**Modules affected:** Most TFR modules

`STRING` is a simulation-only type for debug labels. Yosys doesn't support string parameters.

**Fix:** Strip all `parameter STRING INSTANCE_ID = ""` lines and all references to `INSTANCE_ID`.

---

### BLOCKER 9: Missing Vortex utility macros

**Severity:** Low — ~15 macro definitions
**Modules affected:** All

Macros like `STATIC_ASSERT`, `FORCE_BUILTIN_ADDER`, `MAP_AOS_SOA`, `UNUSED_PARAM`, `UNUSED_VAR`, `TRACE`, `CLOG2`, `DBG_TRACE_TCU` are defined in `VX_platform.vh` and `VX_define.vh` but are simulation-only.

**Fix:** Define all as no-ops at the top of the flat file.

---

### BLOCKER 10: `for (genvar i = 0; i < N; i++)` inline declaration

**Severity:** Low — Yosys accepts `for (genvar i = 0; ...)` when `-sv` flag is set, but the `genvar` declaration must be outside the `for` loop header.

**Fix:** Already handled — the flatten script preserves the `for (genvar ...)` syntax which Yosys 0.68 accepts with `-sv`.

---

## 2. Refactoring plan

### Phase A: Quick wins (1-2 days, covers ~70% of blockers)

These can be done with search-and-replace across the TFR files:

1. **Strip simulation macros** — `STATIC_ASSERT`, `UNUSED_*`, `FORCE_BUILTIN_ADDER`, `MAP_AOS_SOA`, `TRACE_ARRAY`, `DBG_TRACE_TCU` blocks → no-ops
2. **Replace `always_ff` → `always @(posedge clk)`** — 12 occurrences
3. **Replace `always_comb` → `always @*`** — 0 occurrences (already stripped)
4. **Replace `logic` → `wire`/`reg`** — ~100 occurrences, context-dependent
5. **Strip `parameter STRING INSTANCE_ID`** — ~15 occurrences
6. **Replace `$bits()`** — 2 occurrences in TFR (fedp_excep_t, fedp_class_t)
7. **Replace `typedef struct packed`** — 2 typedefs → explicit wire widths

**Estimated effort:** ~200 line edits across 14 files. Can be automated with a Python script.

### Phase B: Generate-block refactor (3-5 days, covers BLOCKER 1)

This is the hard part. The ~95 generate-scoped declarations need to be hoisted to module scope.

**Approach per module:**

1. For each `for (genvar i = 0; i < N; ++i) begin : g_xxx` block:
   - Identify all `wire`/`reg`/`logic` declarations inside the block
   - For **combinational-only wires** used only in `assign` statements within the same block:
     - Replace with inline expressions (preferred) or hoist to module scope with array indexing
   - For **sequential registers** (used in `always_ff` blocks):
     - Hoist to module scope as `reg [N-1:0][WIDTH-1:0] g_xxx_<name>`
     - Add explicit `assign` or `always @*` at module scope

2. **Name collision avoidance:** Prefix all hoisted wires with the generate block label:
   - `wire lane_valid` in `g_lane` → `wire [TCK-1:0] g_lane_lane_valid`

3. **Parameterized widths:** Some generate-scoped wires have parameterized widths that depend on the loop index (e.g., `wire [i-1:0] left_signals`). These require:
   - Computing the maximum width across all iterations
   - Using the maximum width for the hoisted declaration
   - Indexing into the correct bits

**Per-module estimates:**

| Module | Gen-scoped wires | Difficulty | Notes |
|--------|-----------------|------------|-------|
| `VX_tcu_tfr_wmul.sv` | 0 | Easy | Uses `USE_DSP` if/else, no gen-scoped decls |
| `VX_tcu_tfr_classifier.sv` | 0 | Easy | Pure combinational, no generate |
| `VX_tcu_tfr_norm_round.sv` | 0 | Easy | No generate |
| `VX_tcu_tfr_pipe_register.sv` | 0 | Easy | Uses `LANE_MASK` if/else |
| `VX_tcu_tfr_exc_reduce.sv` | 0 | Easy | Simple unpack loop |
| `VX_tcu_tfr_mul_join.sv` | 0 | Easy | Simple exc packing |
| `VX_tcu_tfr_mul_f16.sv` | 1 | Easy | Single `lane_valid` wire |
| `VX_tcu_tfr_acc.sv` | 2 | Easy | `int_sig`, `fp_mag` |
| `VX_tcu_tfr_max_exp.sv` | 2 | Medium | `and_left`, `left_signals` (variable-width) |
| `VX_tcu_tfr_lane_mask.sv` | 0 | Easy | No gen-scoped decls |
| `VX_tcu_tfr_mul_i8.sv` | 6 | Medium | Signed multiply, DSP branching |
| `VX_tcu_tfr_mul_i4.sv` | 12 | Medium | 4-element multiply, DSP branching |
| `VX_tcu_tfr_align.sv` | 12 | Hard | Signed subtractor matrix, variable-width wires |
| `VX_tcu_tfr_mul_f8.sv` | 20 | Hard | FP8/BF8 dual-path, classifier, logic decls |
| `VX_tcu_tfr_shared_mul.sv` | 8 | Medium | SF loop, lane loop |
| `VX_tcu_tfr_mul_f4.sv` | 40 | Very Hard | MXFP4/NVFP4 dual-path, 6 genvar loops, 20+ wires |
| `VX_tcu_fedp_tfr.sv` | 0 | Easy | Top-level, no generate |

### Phase C: Build automation (1 day)

1. **Merge all preprocessing steps** into a single `flatten_tfr.py` that:
   - Reads all 17 TFR modules
   - Applies all Phase A fixes (macros, types, always_ff, etc.)
   - Applies Phase B hoisting (generate-scoped → module-scope)
   - Emits a single flat `.sv` file
2. **Yosys synthesis script** — `read_verilog -sv` the flat file, `hierarchy`, `synth`, `stat`
3. **CI integration** — run synthesis on every commit to catch regressions

---

## 3. What Yosys CAN'T handle (known limitations, no workaround)

| Feature | Yosys status | Impact |
|---------|-------------|--------|
| `$clog2()` in parameters | Works with `-sv` | ✅ |
| `for (genvar i = 0; ...)` | Works with `-sv` | ✅ |
| `parameter` arrays | Works | ✅ |
| `generate`/`endgenerate` | Works | ✅ |
| `wire [a:b]` port arrays | Works | ✅ |
| `$signed()` / `$unsigned()` | Works | ✅ |
| `function automatic` (at file scope) | Works | ✅ |
| `case`/`if`/`for` in combinational | Works | ✅ |

---

## 4. Synthesis results after fix (predicted)

After all blockers are resolved, the TFR synthesis should produce:

- **Top module:** `VX_tcu_fedp_tfr` (the tensor floating-point reduction pipeline)
- **Estimated area:** ~50K-100K gate equivalents (based on multiplier count: 17 TFR sub-modules × ~3K gates each)
- **Estimated Fmax:** 200-400 MHz (depends on critical path through multiplier tree)
- **Estimated power:** ~5-10 mW at 200 MHz (pure combinational pipeline, no state)

The `stat` output will show:
- Number of cells (AND, OR, XOR, MUX, DFF, etc.)
- Wire count and average fanout
- Estimated area in gate equivalents

---

## 5. Next steps

1. **Commit the synthesis infrastructure** (`syn/` directory, flattener scripts) to `dev`
2. **Execute Phase A** — automated macro/type fixes across all TFR modules
3. **Execute Phase B** — generate-block hoisting, starting with easy modules
4. **Run Yosys synthesis** on the fixed flat file
5. **Analyze results** and update the design doc with area/timing/power estimates
6. **Evaluate FPGA prototyping** — if Yosys timing is marginal, try Vivado synthesis on the same TFR block
