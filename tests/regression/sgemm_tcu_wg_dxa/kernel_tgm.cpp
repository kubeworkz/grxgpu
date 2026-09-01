// TGM test kernel: replaces the software K-loop with a single TGM instruction.
// For K=64 testing: k_tiles = 64/8 = 8 (compile-time constant).

#include "common.h"
#include <vx_spawn2.h>
#include <vx_tensor.h>
#include <vx_intrinsics.h>
#include <vx_dxa.h>
#include <vx_barrier.h>
#include "vx_tgm_test.h"

namespace vt = vortex::tensor;
using ctx = vt::wgmma_context<VX_CFG_NUM_THREADS, vt::ITYPE, vt::OTYPE, false, WGMMA_NRC>;

__kernel void kernel_main(kernel_arg_t* __UNIFORM__ arg) {
  auto pC = reinterpret_cast<ctx::output_t *>(arg->C_addr);

  uint32_t tid = threadIdx.x;
  uint32_t num_threads = blockDim.x;
  uint32_t warp_rank = tid / VX_CFG_NUM_THREADS;
  uint32_t num_warps = num_threads / VX_CFG_NUM_THREADS;

  uint32_t cta_M = num_warps * ctx::xtileM;
  uint32_t tile_row = blockIdx.y * cta_M;
  uint32_t tile_col = blockIdx.x * ctx::xtileN;

  ctx::fragment_acc fragC;
  ctx::fill_fragment(fragC, 0);

  const bool is_dxa_warp = (get_sub_group_id() == 0);

  if (is_dxa_warp) {
    auto smem = reinterpret_cast<ctx::input_t *>(__local_mem());
    const uint32_t a_size = cta_M * ctx::tileK;

    uint32_t a_offset = 0;
    uint32_t a_leading = ctx::tileK * sizeof(ctx::input_t);

    [[maybe_unused]] auto b_ptr = smem + a_size;
    uint32_t b_offset = a_size;

    uint32_t desc_a = (a_leading << 16) | (a_offset / sizeof(ctx::input_t));
    uint32_t desc_b = (0u << 16) | (b_offset / sizeof(ctx::input_t));

    // Issue TGM with compile-time k_tiles=8 (K=64, tileK=8).
    // K_END=8, FMT_S=9(fp16), FMT_D=1(fp32), CD_NREGS=0(8 regs), IS_A_SMEM=1
    constexpr uint32_t K_TILES = 8;

    vx_tgm_imm<K_TILES>(desc_a, desc_b);
  } else {
    vortex::barrier sync_bar(3);
    sync_bar.arrive_and_wait();
  }

  uint32_t N = arg->N;
  auto pTileC = pC + (tile_row + warp_rank * ctx::xtileM) * N + tile_col;
  ctx::store_matrix_sync(pTileC, fragC, N);
}
