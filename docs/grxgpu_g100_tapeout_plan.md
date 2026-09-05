# GRX G100 ASIC Tapeout Plan

## Executive Summary

This document outlines the plan to take the GRX G100 — a 128-core GPU with tensor compute (TCU), data transfer engine (DXA), and graphics pipeline — from RTL to working silicon on TSMC 28nm HPC+.

**Key decisions:**
- **SRAM strategy**: Hybrid — ORRAM (open-source, DFF-based) for small SRAMs, foundry embedded SRAM IP for large SRAMs
- **Target**: TSMC 28nm HPC+ MPW shuttle
- **Budget**: $50K–$100K (shuttle + packaging + test)
- **Timeline**: 6–9 months from RTL freeze to working silicon

---

## 1. Design Overview

### 1.1 GRX G100 Architecture

| Component | Count | Description |
|-----------|-------|-------------|
| **Cores** | 128 (8 clusters × 16) | RISC-V scalar + SIMD vector pipeline |
| **TCU** | 4 blocks/core | WGMMA tensor engine (fp32/bf16/fp16) |
| **DXA** | 2 cores/cluster | GMEM→LMEM tile fetch engine |
| **Graphics** | Per-cluster | Rasterizer, texture cache, RTU, output merger |
| **Barriers** | 128/core | Hardware barrier unit for CTA sync |

### 1.2 Memory Hierarchy

| Memory | Size/Core | Count | Total | Technology |
|--------|-----------|-------|-------|------------|
| **LMEM** (shared mem) | 16 KB | 128 | 2,048 KB | Embedded SRAM |
| **ICache** | 16 KB | 128 | 2,048 KB | Embedded SRAM |
| **DCache** | 16 KB | 128 | 2,048 KB | Embedded SRAM |
| **TCACHE** | 8 KB | 2 | 16 KB | ORRAM |
| **RCACHE** | 4 KB | 1 | 4 KB | ORRAM |
| **OCACHE** | 16 KB | 2 | 32 KB | ORRAM |
| **Total SRAM** | — | — | **~6.1 MB** | Hybrid |

---

## 2. SRAM Strategy

### 2.1 Why Hybrid?

| Approach | Area (28nm) | Cost | Risk |
|----------|------------|------|------|
| **All ORRAM (DFF-based)** | ~50 mm² | $0 license | High area, slow DRT routing |
| **All custom 6T SRAM** | ~13 mm² | $150K–$200K license | SRAM compiler dependency |
| **Hybrid (recommended)** | ~25 mm² | $0 license | Balanced |

### 2.2 SRAM Assignment

#### Large SRAMs — Foundry Embedded SRAM IP (Free with PDK)

These are the performance-critical, area-dominant SRAMs. The foundry provides pre-characterized, silicon-proven SRAM macros at no additional cost when you sign a PDK agreement.

| SRAM | Size | Ports | Count | Why Embedded |
|------|------|-------|-------|-------------|
| LMEM | 16 KB | 1RW | 128 | TCU reads tiles here — 1-cycle access critical |
| ICache | 16 KB | 1RW | 128 | Instruction fetch bandwidth |
| DCache | 16 KB | 1RW | 128 | Data load/store bandwidth |

**Total embedded SRAM**: 6,144 KB = **6 MB**

#### Small SRAMs — ORRAM (Open-Source, Free)

These are shared caches with lower access frequency. ORRAM's DFF-based approach is acceptable here because:
- Area overhead is small (32 KB total = ~0.5 mm²)
- Access latency is 1–2 cycles (acceptable for texture/raster)
- No license cost, no NDA

| SRAM | Size | Ports | Count | Why ORRAM |
|------|------|-------|-------|----------|
| TCACHE | 8 KB | 1RW | 2 | Shared, lower bandwidth need |
| RCACHE | 4 KB | 1RW | 1 | Shared, minimal |
| OCACHE | 16 KB | 1RW | 2 | Shared, write-heavy |

**Total ORRAM**: 84 KB = **~0.5 mm² at 28nm**

### 2.3 Area Estimate

**Logic area is now measured** via Yosys blackbox synthesis on the Nangate45 (45 nm) open-cell library (Sept 2026). The full 16-core cluster cannot be synthesized in one flat Yosys pass (sv2v inlines the interface hierarchy, so Yosys must re-derive 16 inlined cores single-threaded — it never finishes). The blackbox flow stubs `VX_core` in the source tree and synthesizes only the fabric, then recovers the core area by difference:

| Measurement (Nangate45, RAM blackboxed) | Area | Cells |
|------------------------------------------|------|-------|
| 1-socket full design (core + fabric) | 613,610 µm² | 340K |
| BB1 — 1-socket fabric, `VX_core` stubbed | 179,465 µm² | 84K |
| **VX_core logic alone** (= full − BB1) | **434,146 µm²** | ~256K |
| BB16 — 16-socket cluster fabric, cores stubbed | 11,698,076 µm² | 5.76M |
| **16-core cluster total** (= BB16 + 16×core) | **18,644,409 µm²** | ~9.9M |

Key finding: the shared 16-socket fabric (L2 control, cluster crossbars/arbiters) is **11.7 mm²** — 4× the sum of per-socket fabrics (16 × 0.18 = 2.9 mm²) — so the L2/interconnect does not scale linearly with core count. It dominates a 16-core cluster.

**Where the 11.7 mm² goes** — recursive per-type decomposition of the BB16 stat (`syn/decompose_fabric.py`; totals reconcile exactly to the reported top-module area):

| Fabric component | Cluster (BB16) | Per-socket (BB1) | Shared (BB16 − 16×BB1) |
|------------------|----------------|------------------|------------------------|
| **Arbiters** (`VX_stream_arb`, rr/priority) | **5.66 mm² (48%)** | 0.009 mm² | **5.51 mm²** |
| **Crossbar/switch** (`VX_stream_buffer`, xbar, omega) | **3.11 mm² (27%)** | 0.082 mm² | **1.80 mm²** |
| **Buffers/queues** (`VX_pipe_register`, fifo_queue) | **1.79 mm² (15%)** | 0.036 mm² | **1.21 mm²** |
| **Cache control** (bank/mshr/data/tags) | **0.89 mm² (8%)** | 0.040 mm² | **0.25 mm²** |
| RAM macros (blackbox) | 0.17 mm² (1%) | 0.004 mm² | 0.11 mm² |
| Misc + top glue | ~0.08 mm² | ~0.008 mm² | ~0 |
| **Total** | **11.70 mm²** | **0.179 mm²** | **8.88 mm²** |

Decomposition takeaways: **L2 control is tiny** (~0.25 mm² shared; the data arrays will add on top but the control logic is negligible). The cost center is the **arbitration network** — `VX_stream_arb` alone is ~5.6 mm², essentially all cluster-level. 76% of the fabric is shared cluster-level logic; only 24% scales linearly with socket count. For die area, the NoC topology and arbiter port counts matter far more than cache tuning.

**Arbiter area scaling** — `VX_stream_arb` synthesized standalone (Nangate45, `syn/arb_area_sweep.sh`):

| Ports (N:1, DW=64, RR) | Area | per-bit-per-input |
|------------------------|------|-------------------|
| 2:1 | 140 µm² | 1.09 µm² |
| 4:1 | 419 µm² | 1.64 µm² |
| 8:1 | 958 µm² | 1.87 µm² |
| 16:1 | 4,055 µm² | 3.96 µm² |
| 32:1 | 8,127 µm² | 3.97 µm² |
| 64:1 | 19,538 µm² | 4.77 µm² |

| Width (16:1, RR) | Area | per-bit |
|------------------|------|---------|
| 32 b | 2,225 µm² | 69.5 µm² |
| 64 b | 4,055 µm² | 63.4 µm² |
| 128 b | 7,715 µm² | 60.3 µm² |
| 256 b | 15,036 µm² | 58.7 µm² |
| 512 b | 29,676 µm² | 58.0 µm² |

| Variant (16:1, DW=64) | Area | Δ vs baseline |
|----------------------|------|---------------|
| Round-robin | 4,055 µm² | — |
| Priority (`"P"`) | 3,927 µm² | −3% |
| Sticky | 4,233 µm² | +4% |
| OUT_BUF=1 | 4,497 µm² | +11% |

| Realistic L2 shape (32→16, DW=512) | Area |
|-------------------------------------|------|
| RR | 15,356 µm² |
| Priority | 15,340 µm² |
| 16→8 (half-width crossbar) | 7,688 µm² |
| 8→4 | 3,853 µm² |
| 4→2 | 1,936 µm² |

Key scaling findings:
- **Area grows superlinearly with ports** — the 8:1→16:1 step is 4.2× (not 2×). Per-bit-per-input jumps from 1.9 to 4.0 µm² at the 16-port threshold, then saturates ~4.8 µm² at 64 ports. The grant/onehot logic dominates at low port counts; the data MUX dominates beyond ~16 inputs.
- **Width scales linearly** — ~58–70 µm² per data bit at fixed ports; total arb area ≈ 60 µm²/bit × DW at 16:1.
- **Arbiter flavor is nearly free**: priority vs round-robin is −3%, sticky +4%, output buffering +11%. Pick priority (used at the L2) with no area penalty.
- **Tree arbitration is the big lever**: a flat 64:1 arb costs 19,538 µm²; a 3-level 8:1 tree (8 × 8:1) costs 7,661 µm² — **−61%**. Even 2×32:1 is −17%. Since `VX_stream_arb` already self-slices at `MAX_FANOUT=8`, the cluster fabric's 5.6 mm² is partly tree-structured, but the L2 32→16 crossbar is still flat per output. Replacing the flat 32→16 L2 arb with a 2-level (4→2 then 16×) tree would cut the 15.4K µm² instance to ~8K, and a 3-level design roughly halves it again at the cost of one extra pipeline stage of latency.

> **Scope notes:** (1) `VX_core` instantiates `VX_execute` → `VX_tcu_unit`/`VX_dxa_unit`, so the measured 434K µm²/core **includes** the TCU + DXA tensor logic (verified present in the 613K reference, absent from the stubbed BB runs — the orphan TCU module definitions Yosys drops contribute 0 cells). (2) The 8-cluster G100 row assumes no extra inter-cluster fabric (L3/NoC); add interconnect margin when sizing the full die.

> **Process-node note:** Nangate45 is a **45 nm** library. Scaling to the 28 nm target **shrinks** area by (28/45)² ≈ **0.39×** (it does *not* grow 2.5× as previously stated).

| Component | Area @45 nm | Area @28 nm (×0.39) |
|-----------|------------|---------------------|
| 16-core cluster logic | 18.64 mm² | ~7.2 mm² |
| G100 logic (8 clusters) | 149.2 mm² | ~57.8 mm² |
| Embedded SRAM (6 MB) | — | ~13 mm² (0.25 µm²/bit 6T) |
| ORRAM (84 KB) | — | ~0.5 mm² |
| **Total die estimate** | — | **~71 mm²** |

**This is a die-area problem for MPW.** A ~71 mm² G100 does not fit a typical 4 mm² MPW shuttle tile. Options: (a) shrink the tapeout to a single **16-core cluster (~20 mm² @28nm incl. SRAM)** as a first-silicon proof point, or (b) move to a full reticle/wafer share. Revisit with the foundry's shuttle tile size before committing.

---

## 3. Fabrication Path

### 3.1 Foundry Selection

| Foundry | Node | MPW Cost | SRAM IP | Recommendation |
|---------|------|----------|---------|----------------|
| **TSMC** | 28nm HPC+ | $30K–$80K | Included with PDK | **Primary choice** |
| GlobalFoundries | 28nm SLPe | €50K | Included with PDK | Backup |
| SkyWater | 130nm | $0 (Tiny Tapeout) | Manual porting | Proof-of-concept only |

### 3.2 MPW Shuttle Schedule (2026–2027)

| Deadline | Fab Start | Delivery | Status |
|----------|-----------|----------|--------|
| **Sep 15, 2026** | Oct 2026 | Jan 2027 | ⚠️ 11 days away — unlikely |
| **Oct 15, 2026** | Nov 2026 | Feb 2027 | Feasible if RTL freezes soon |
| **Nov 15, 2026** | Dec 2026 | Mar 2027 | **Recommended target** |
| Jan 15, 2027 | Feb 2027 | May 2027 | Backup |

**Recommendation**: Target the **November 15, 2026** deadline. This gives ~11 weeks for:
- RTL freeze and lint
- Synthesis (Yosys/OpenROAD)
- Place & route (OpenROAD)
- DRC/LVS signoff
- GDSII export

### 3.3 Cost Breakdown

| Item | Cost | Notes |
|------|------|-------|
| **TSMC 28nm HPC+ MPW** | $40K–$60K | 4 mm² die, shuttle fee |
| **Foundry PDK** | $0 | Included with MPW agreement |
| **Embedded SRAM IP** | $0 | Included with PDK |
| **ORRAM license** | $0 | BSD 3-Clause |
| **EDA tools** | $0–$100K | OpenLane (free) or commercial |
| **Packaging (QFN/BGA)** | $5K–$10K | 20–100 units |
| **Test board + probe** | $5K–$15K | Custom PCB or eval board |
| **DRC/LVS signoff** | $10K–$20K | Foundry PDK checks |
| **Second shuttle (if bugs)** | $40K–$60K | Typical 2-pass to production |
| **Total NRE** | **$100K–$265K** | First silicon to production-ready |

---

## 4. Design Flow

### 4.1 RTL-to-GDSII Pipeline

```
RTL (SystemVerilog)
    │
    ▼
┌─────────────┐
│  Lint (Verilator)  │  ← Catch syntax/width errors
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Synthesis (Yosys/OpenROAD)  │  ← Gate-level netlist
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Floorplan (OpenROAD)  │  ← Die size, SRAM placement
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Place & Route (OpenROAD)  │  ← Cell placement, routing
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  STA (OpenSTA)  │  ← Timing closure
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  DRC/LVS (KLayout + Magic)  │  ← Physical verification
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  GDSII Export  │  ← Tapeout!
└─────────────┘
```

### 4.2 Open-Source Tool Chain

| Tool | Purpose | Status |
|------|---------|--------|
| **Yosys** | RTL synthesis | ✅ Installed on server |
| **OpenROAD** | P&R + STA | ✅ Docker image (26Q3) |
| **OpenRAM/ORRAM** | SRAM generation | ✅ Validated (512B SRAM) |
| **KLayout** | DRC/LVS + GDSII | ⏳ Need to install |
| **Magic** | DRC/LVS | ⏳ Need to install |
| **OpenSTA** | Static timing | ✅ Included with OpenROAD |

### 4.3 SRAM Integration

#### Embedded SRAM (LMEM, ICache, DCache)

1. Sign TSMC 28nm HPC+ MPW agreement → receive PDK
2. PDK includes embedded SRAM compiler (or pre-built macros)
3. Generate 16 KB SRAM macros for each configuration
4. Import as black boxes in RTL (Verilog behavioral model for sim, LEF/GDS for P&R)
5. Place SRAMs in floorplan near their consumer cores

#### ORRAM (TCACHE, RCACHE, OCACHE)

1. Use OpenROAD Docker container (already validated)
2. Generate 4–16 KB macros for each configuration
3. Import LEF abstract + Verilog behavioral + liberty timing
4. Place in floorplan near graphics pipeline

---

## 5. Risk Mitigation

### 5.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **SRAM yield** | High | Use foundry-proven embedded SRAM; ORRAM for non-critical |
| **Timing closure** | High | Start synthesis early; 28nm has good timing margins |
| **DRC violations** | Medium | Run DRC weekly during P&R; use foundry DRC deck |
| **Power density** | Medium | 28nm handles ~1W/mm² easily; 22 mm² = 22W budget |
| **Multi-core rtlsim bug** | Low | Fixed (drain placement); GRXCP team confirmed |

### 5.2 Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **RTL not frozen** | High | Freeze by Oct 15 for Nov shuttle |
| **SRAM integration delays** | Medium | Use black-box SRAMs in RTL; integrate post-synthesis |
| **EDA tool issues** | Medium | Docker image validated; have commercial fallback |
| **Foundry delays** | Low | MPW is quarterly; can slip to Jan 2027 |

### 5.3 First-Silicon Validation Plan

| Test | Method | Pass Criteria |
|------|--------|--------------|
| **Basic core boot** | JTAG debug | PC advances, CSR reads |
| **LMEM read/write** | Memory test | All 16 KB per core |
| **TCU WGMMA** | SGEMM K=16 | Correct matrix multiply |
| **DXA fetch** | GMEM→LMEM DMA | Correct tile transfer |
| **Multi-core** | Barrier test | All 128 cores sync |
| **Graphics pipeline** | Rasterizer test | Fragment output |
| **Full SGEMM** | 512×512×512 | PASSED (SimX baseline) |

---

## 6. Timeline

```
Aug 2026          Sep 2026          Oct 2026          Nov 2026          Jan 2027
    │                 │                 │                 │                 │
    ├─ RTL freeze     ├─ Synthesis      ├─ P&R            ├─ DRC/LVS       ├─ Silicon
    │  (Aug 15)       │  (Sep 15)       │  (Oct 15)       │  (Nov 1)       │  delivery
    │                 │                 │                 │                 │
    ├─ Lint           ├─ Floorplan      ├─ STA closure    ├─ GDSII export  ├─ Test
    │  (Verilator)    │  (SRAM place)   │  (timing met)   │  (Nov 10)      │  board
    │                 │                 │                 │                 │
    └─ SimX verify    └─ SRAM gen       └─ Route          └─ Shuttle       └─ Silicon
       (K=512 PASSED)    (ORRAM + embedded) (OpenROAD)      submit (Nov 15)   validation
```

### Key Milestones

| Date | Milestone | Status |
|------|-----------|--------|
| **Now** | RTL complete, all tests passing | ✅ Done |
| **Aug 15, 2026** | RTL freeze (no more feature additions) | ⏳ 11 days |
| **Sep 1, 2026** | Synthesis complete, gate count known | ⏳ Next |
| **Oct 1, 2026** | Floorplan + SRAM placement done | ⏳ Planned |
| **Nov 1, 2026** | Timing closure, DRC/LVS clean | ⏳ Planned |
| **Nov 15, 2026** | GDSII submitted to TSMC | ⏳ Target |
| **Feb 2027** | Silicon delivered | ⏳ Expected |
| **Mar 2027** | First silicon validated | ⏳ Goal |

---

## 7. Open Questions

1. **SRAM compiler**: Does TSMC 28nm HPC+ PDK include an embedded SRAM compiler, or do we need to license one separately?
2. **Multi-project wafer**: Can we share the shuttle with another project to reduce cost?
3. **Package**: QFN vs BGA — which is easier for first-silicon test?
4. **Clock target**: What frequency should we target? (28nm HPC+ can do 500–800 MHz)
5. **Power budget**: What's the TDP target? (22 mm² at 28nm can handle 15–20W)

---

## 8. Appendix: Validated ORRAM Results

### 8.1 512-Byte SRAM (sky130nm)

| Metric | Value |
|--------|-------|
| Macro | RAM16x32 |
| Size | 462.3 × 46.24 µm |
| Area | 0.021 mm² |
| Density | 192 Kbit/mm² |
| Word size | 32 bits |
| Words | 16 |
| Routing time | ~100s (Docker, 8-core) |
| Technology | sky130hd (130nm) |

### 8.2 Scaling to 28nm

| Metric | sky130nm | 28nm (estimated) |
|--------|----------|-----------------|
| DFF density | 192 Kbit/mm² | ~960 Kbit/mm² |
| 16 KB SRAM area | 1.3 mm² | 0.26 mm² |
| 6 MB total | 502 mm² | 100 mm² |

### 8.3 ORRAM Configuration Used

```tcl
generate_ram \
  -word_size 32 \
  -num_words 16 \
  -rw_ports 1 \
  -storage_cell sky130_fd_sc_hd__dfxtp_1 \
  -tristate_cell sky130_fd_sc_hd__ebufn_4 \
  -inv_cell sky130_fd_sc_hd__inv_1 \
  -routing_layer {met1 0.48} \
  -ver_layer {met2 0.48 40} \
  -hor_layer {met3 0.48 20} \
  -filler_cells {sky130_fd_sc_hd__fill_1 ...} \
  -tapcell sky130_fd_sc_hd__tap_1 \
  -max_tap_dist 15
```

---

*Document version: 1.0 — September 4, 2026*
*Author: Buffy (Codebuff agent) + GRX GPU team*
