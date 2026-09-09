#!/usr/bin/env python3
"""Update design doc sections 10.2 and 10.3 with DXA core synthesis results."""
import re

with open('/home/ubuntu/grxgpu/docs/grxgpu_g100_tapeout_plan.md') as f:
    text = f.read()

# Find and replace section 10.2
start_102 = text.find('### 10.2 DXA Synthesis')
end_102 = text.find('### 10.3 Full TCU Extrapolation')
if start_102 >= 0 and end_102 >= 0:
    old_102 = text[start_102:end_102]
    new_102 = """### 10.2 DXA Synthesis (Synlig + Yosys ECP5)

The full DXA unit (`VX_dxa_core`) was synthesized end-to-end using Synlig (Surelog frontend) for SV parsing and Yosys 0.67 for ECP5 mapping. All 15 DXA modules parse with 0 FATAL, 0 SYNTAX, 0 ERROR.

| Resource | DXA core (full) | TFR | DXA / TFR |
|----------|----------------|-----|----------| 
| **LUT4** | **132** | 138 | 0.96x |
| **PFUMX** | 16 | 12 | 1.33x |
| **L6MUX21** | 2 | 5 | 0.40x |
| **CCU2C** | 86 | 32 | 2.69x |
| **TRELLIS_FF** | **180** | 272 | 0.66x |
| **Total cells** | 463 | 2,310 | 0.20x |

**Key insight:** The full DXA core is similar in LUT4 count to the TFR (132 vs 138) but uses more carry chains (86 vs 32 CCU2C) because the address generation is carry-chain-friendly arithmetic. The DXA has fewer FFs (180 vs 272) because its control logic is simpler than the TFR 16-lane pipeline.

**Synlig pipeline:** `read_systemverilog -defer` -> `read_systemverilog -link` -> `synth_ecp5 -flatten`
**Synthesis time:** ~35s (Synlig parse + elaborate + ECP5 map, 1 GB peak memory)

**Interface flattening:** All 3 internal interface arrays (worker_req_if, worker_gmem_bus_if, worker_smem_bus_if) were flattened to single instances for the single-core configuration (VX_CFG_NUM_DXA_CORES=1).

"""
    text = text[:start_102] + new_102 + text[end_102:]

# Find and replace section 10.3
start_103 = text.find('### 10.3 Full TCU Extrapolation')
end_103 = text.find('### 10.4 Synthesis Pipeline')
if start_103 >= 0 and end_103 >= 0:
    old_103 = text[start_103:end_103]
    new_103 = """### 10.3 Full TCU Resource Estimate (Measured + Extrapolated)

Combined TFR + DXA synthesis results with TCU module estimates:

| Component | LUT4 | FF | Confidence |
|-----------|------|----|-----------| 
| TFR (17 sub-modules) | **138** | **272** | Measured (Synlig+ECP5) |
| DXA core (15 sub-modules) | **132** | **180** | Measured (Synlig+ECP5) |
| TCU control logic (est.) | ~200 | ~300 | Estimated |
| WGMMA scheduler (est.) | ~150 | ~200 | Estimated |
| ABUF/BBUF/TBUF (est.) | ~100 | ~150 | Estimated |
| DSM + lockstep (est.) | ~50 | ~80 | Estimated |
| **TCU total (synth est)** | **~770** | **~1,182** | Extrapolated |
| **TCU total (P&R est)** | **~6,000** | **~800** | P&R expansion factor ~8x |

**TFR P&R result (ECP5-85F):** 4,012 LUT4 (4.8%), 513 DFF (0.6%), 89.54 MHz

**128-core GRX G100 scaling:**
- 128 TCUs x 6,000 LUT4 = **768,000 LUT4** (~9% of ECP5-85K)
- 28nm ASIC: ~1.2 mm2 TCU logic area (no SRAM)
- Total with SRAM: ~25 mm2 (hybrid ORRAM + embedded SRAM)

"""
    text = text[:start_103] + new_103 + text[end_103:]

with open('/home/ubuntu/grxgpu/docs/grxgpu_g100_tapeout_plan.md', 'w') as f:
    f.write(text)

print('Updated design doc sections 10.2 and 10.3')
