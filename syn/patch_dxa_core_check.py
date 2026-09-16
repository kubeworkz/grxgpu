#!/usr/bin/env python3
"""Add runtime NUM_DXA_CORES >= 2 check for WGMMA_DXA_DOUBLE_BUFFER."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/grxgpu/tests/regression/sgemm_tcu_wg_dxa/main.cpp"

with open(path, 'r') as f:
    content = f.read()

# Insert after the DXA extension check closing brace
marker = """  if ((isa_flags & VX_ISA_EXT_DXA) == 0) {
    std::cerr << "Error: DXA ISA extension is disabled." << std::endl;
    cleanup();
    return -1;
  }

  uint64_t NT;"""

replacement = """  if ((isa_flags & VX_ISA_EXT_DXA) == 0) {
    std::cerr << "Error: DXA ISA extension is disabled." << std::endl;
    cleanup();
    return -1;
  }

  // WGMMA_DXA_DOUBLE_BUFFER requires >= 2 DXA cores (fused A+B pair needs 2 workers).
#ifdef WGMMA_DXA_DOUBLE_BUFFER
  {
    uint64_t num_dxa_cores;
    RT_CHECK(vx_device_query(device, VX_CAPS_NUM_DXA_CORES, &num_dxa_cores));
    if (num_dxa_cores < 2) {
      std::cerr << "Error: WGMMA_DXA_DOUBLE_BUFFER requires NUM_DXA_CORES >= 2, got "
                << num_dxa_cores << std::endl;
      cleanup();
      return -1;
    }
  }
#endif

  uint64_t NT;"""

if marker not in content:
    print("ERROR: marker not found")
    sys.exit(1)

content = content.replace(marker, replacement, 1)

with open(path, 'w') as f:
    f.write(content)

print("Patched main.cpp with NUM_DXA_CORES >= 2 runtime check")
