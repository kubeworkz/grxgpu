// TGM test kernel: replaces the software K-loop with a single TGM instruction.
// All 4 warps issue TGM with per-warp A-slice descriptors; the FSM computes
// each warp's fragment, writes it to that warp's fregs (f0..f7), the warp
// resumes and stores its own slice of C.
//
// For K=512 testing: k_tiles = 512/8 = 64 (passed at runtime via a2).

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
  uint32_t tile_row = blockIdx.y * cta_M;
  uint32_t tile_col = blockIdx.x * ctx::xtileN;
  uint32_t N = arg->N;

  // smem layout (FP16 elements): A tile (cta_M x tileK) then B tile (tileK x xtileN).
  const uint32_t a_size = cta_M * ctx::tileK;
  const uint32_t b_offset = a_size * sizeof(ctx::input_t);  // byte offset

  // Per-warp A slice (byte offset into smem).
  const uint32_t a_warp_off = warp_rank * ctx::xtileM * ctx::tileK * sizeof(ctx::input_t);
  // A row-major (ldm = tileK bytes), B block-major (ldm = 0).
  uint32_t desc_a = (ctx::tileK * sizeof(ctx::input_t) << 16) | a_warp_off;
  uint32_t desc_b = (0u << 16) | b_offset;

  // One TGM covers the full K range; the FSM runs FETCH/COMPUTE per K-tile.
  uint32_t k_tiles = arg->K / ctx::tileK;
  ctx::fragment_acc fragC;
  vx_tgm(desc_a, desc_b, k_tiles, fragC.data.data());

  // Warp resumed after TGM: store its slice of C.
  auto pC = reinterpret_cast<ctx::output_t *>(arg->C_addr);
  auto pTileC = pC + (tile_row + warp_rank * ctx::xtileM) * N + tile_col;
  ctx::store_matrix_sync(pTileC, fragC, N);
}