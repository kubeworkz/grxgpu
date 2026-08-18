#ifndef _SGEMM_TCU_WG_DXA_COMMON_H_
#define _SGEMM_TCU_WG_DXA_COMMON_H_

#include <stdint.h>

#ifndef WGMMA_NRC
  #define WGMMA_NRC 8
#endif

#ifndef ITYPE
#define ITYPE fp16
#endif

#ifndef OTYPE
#define OTYPE fp32
#endif

typedef struct {
  uint32_t M, N, K;
  uint64_t A_addr;
  uint64_t B_addr;
  uint64_t C_addr;
} kernel_arg_t;

// Double-buffered smem stage stride, in elements.
//
// SimX LMEM banks interleave at word granularity (sim/simx/mem/local_mem.cpp):
//   bank = (byte_addr >> log2(VX_CFG_XLEN/8)) & (VX_CFG_LMEM_NUM_BANKS-1)
// so a full sweep of all banks spans VX_CFG_LMEM_NUM_BANKS * (VX_CFG_XLEN/8)
// bytes. Laying the two pipeline stages back-to-back makes stage 1's accesses
// alias stage 0's banks exactly, so the DXA prefetch's smem writes collide with
// the compute stage's TCU/LSU smem reads. Shift stage 1 by half a sweep (only
// when that stays MEM_BLOCK_SIZE-aligned) so its accesses land on the opposite
// bank half, decoupling the two stages' smem traffic.
static constexpr uint32_t wgmma_dbuf_stride_elems(uint32_t stage_elems, uint32_t elem_bytes) {
  const uint32_t word_bytes  = VX_CFG_XLEN / 8;
  const uint32_t sweep_bytes = VX_CFG_LMEM_NUM_BANKS * word_bytes;
  const uint32_t half_bytes  = sweep_bytes / 2;
  uint32_t stage_bytes = stage_elems * elem_bytes;
  uint32_t shift = ((half_bytes % VX_CFG_MEM_BLOCK_SIZE) == 0) ? half_bytes : 0;
  uint32_t stride_bytes = ((stage_bytes + sweep_bytes - 1) / sweep_bytes) * sweep_bytes + shift;
  return stride_bytes / elem_bytes;
}

#endif
