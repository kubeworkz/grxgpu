#ifndef _SGEMM_TCU_BF16_COMMON_H_
#define _SGEMM_TCU_BF16_COMMON_H_

#include <stdint.h>

#ifndef WGMMA_NRC
  #define WGMMA_NRC 8
#endif

#ifndef ITYPE
#define ITYPE bf16
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
