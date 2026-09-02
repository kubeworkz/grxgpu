// TGM test kernel: replaces the software K-loop with a single TGM instruction.
// For K=512 testing: k_tiles = 512/8 = 64 (compile-time constant).

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
  uint32_t tid = threadIdx.x;
  uint32_t warp_rank = tid / VX_CFG_NUM_THREADS;

  uint32_t cta_M = VX_CFG_NUM_WARPS * ctx::xtileM;
  (void)cta_M;
  uint32_t tile_row = blockIdx.y * cta_M;
  uint32_t tile_col = blockIdx.x * ctx::xtileN;

  const bool is_dxa_warp = (get_sub_group_id() == 0);

  if (is_dxa_warp) {
    auto smem __attribute__((unused)) = reinterpret_cast<ctx::input_t *>(__local_mem());
    const uint32_t a_size = VX_CFG_NUM_WARPS * ctx::xtileM * ctx::tileK;

    uint32_t a_offset = 0;
    uint32_t a_leading = ctx::tileK * sizeof(ctx::input_t);

    uint32_t b_offset = a_size;

    uint32_t desc_a = (a_leading << 16) | (a_offset / sizeof(ctx::input_t));
    uint32_t desc_b = (0u << 16) | (b_offset / sizeof(ctx::input_t));

    // Issue TGM with compile-time k_tiles=8 (K=64, tileK=8).
    // TGM stalls the warp until completion.
    constexpr uint32_t K_TILES = 64;
    vx_tgm_imm<K_TILES>(desc_a, desc_b);
    // Warp is stalled by TGM - never reaches here.
  }

  // Non-DXA warps: store zeros to output (no correctness check).
  // DXA warp: never reaches here (stalled by TGM).
  ctx::fragment_acc fragC;
  ctx::fill_fragment(fragC, 0);
  uint32_t N = arg->N;
  auto pC = reinterpret_cast<ctx::output_t *>(arg->C_addr);
  auto pTileC = pC + (tile_row + warp_rank * ctx::xtileM) * N + tile_col;
  ctx::store_matrix_sync(pTileC, fragC, N);
}
