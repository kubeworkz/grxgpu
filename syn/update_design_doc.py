#!/usr/bin/env python3
"""Update the G100 tapeout plan doc with TGM double-buffer battery results."""
import sys

doc_path = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu/docs/grxgpu_g100_tapeout_plan.md"

with open(doc_path, 'r') as f:
    content = f.read()

# 1. Add battery results after fp32 tolerance bullet
scope_marker = '> **Scope notes:**'
idx = content.find(scope_marker)
if idx < 0:
    print("ERROR: Could not find scope notes marker")
    sys.exit(1)

battery_text = """- **TGM double-buffer correctness battery — full sweep (Sept 2026)** — rebuilt simx with the 128-core flagship config (8 clusters × 16 cores, 4 warps, 4 threads, 4 issue width, `NUM_DXA_CORES=2`) and ran the `sgemm_tcu_wg_dxa` GEMM across K=16→512. **All 5 sizes PASSED.** Critical finding: `WGMMA_DXA_DOUBLE_BUFFER` requires `NUM_DXA_CORES ≥ 2` — the fused A+B pair needs 2 DXA workers; with `NUM_DXA_CORES=1` the TGM FSM deadlocks (stuck at "wait for completion"). With `NUM_DXA_CORES=2` the design is fully functional:

| K | Instrs | Cycles | IPC | Wall Time | Status |
|---|--------|--------|-----|-----------|--------|
| 16 | 24,704 | 8,253 | 2.993 | 6.9s | PASSED |
| 64 | 69,056 | 12,553 | 5.501 | 11.1s | PASSED |
| 128 | 128,192 | 18,969 | 6.758 | 15.7s | PASSED |
| 256 | 246,464 | 30,017 | 8.211 | 30.7s | PASSED |
| 512 | 483,008 | 54,609 | 8.845 | 50.0s | PASSED |

IPC scales from 3.0 at K=16 to 8.8 at K=512, confirming the double-buffer FSM effectively hides DXA latency at scale. Cycles grow 6.6× from K=16→512 while instructions grow 19.6×, indicating DXA bandwidth (2 cores serving 128 compute cores) is the saturation point. The 2-core config shows the same correctness with lower IPC (0.758 at K=512), confirming the DXA bandwidth bottleneck.

"""

content = content[:idx] + battery_text + content[idx:]

# 2. Update the validation plan: Full SGEMM now has battery results
old_val = '| **Full SGEMM** | 512×512×512 | PASSED (SimX baseline) |'
new_val = '| **Full SGEMM** | K=16→512 battery | All 5 sizes PASSED on 128-core SimX (see §2) |'
content = content.replace(old_val, new_val)

with open(doc_path, 'w') as f:
    f.write(content)

print("Doc updated successfully")
print("  - Battery bullet added after fp32 tolerance")
print("  - Validation plan updated")
