#include "common.h"
#include <vx_spawn2.h>
#include <vx_tensor.h>
#include <vx_intrinsics.h>
#include <vx_dxa.h>
#include <vx_barrier.h>

namespace vt = vortex::tensor;
using ctx = vt::wgmma_context<VX_CFG_NUM_THREADS, vt::ITYPE, vt::OTYPE, false, WGMMA_NRC>;

// DXA descriptor slots (programmed by host in main.cpp).
[[maybe_unused]] constexpr uint32_t kDescA = 0;
[[maybe_unused]] constexpr uint32_t kDescB = 1;

__kernel void kernel_main(kernel_arg_t* __UNIFORM__ arg) {
  auto pC = reinterpret_cast<ctx::output_t *>(arg->C_addr);
#ifdef SW_LOAD_B
  auto pB = reinterpret_cast<const ctx::input_t *>(arg->B_addr);
#endif
#ifdef SW_LOAD_A
  auto pA = reinterpret_cast<const ctx::input_t *>(arg->A_addr);
#endif

  uint32_t N = arg->N;
  uint32_t K = arg->K;

  uint32_t tid = threadIdx.x;
  uint32_t num_threads = blockDim.x;
  uint32_t warp_rank = tid / VX_CFG_NUM_THREADS;
  uint32_t num_warps = num_threads / VX_CFG_NUM_THREADS;

  // CTA tile dimensions
  uint32_t cta_M = num_warps * ctx::xtileM;
  uint32_t tile_row = blockIdx.y * cta_M;
  uint32_t tile_col = blockIdx.x * ctx::xtileN;

  // Initialize accumulator tile to zero.
  ctx::fragment_acc fragC;
  ctx::fill_fragment(fragC, 0);

  // Only the first warp in the CTA issues DXA commands.
  const bool is_dxa_warp = (get_sub_group_id() == 0);

  // A is fetched row-major (ldm = tileK); B is fetched block-major (bbuf-native).

#ifdef WGMMA_DXA_DOUBLE_BUFFER
  // ---------------------------------------------------------------------
  // Double-buffered: two pipeline stages, two barriers. The next K-tile's
  // DXA copy is issued (async, on bar[nxt]) before the current tile computes,
  // so the DMA overlaps the WGMMA.
  //
  // IMPORTANT: Use the barrier class which embeds get_local_group_id() into
  // the barrier ID via (id << 8) + cta_id.  Raw arithmetic like
  //   bar_base = get_local_group_id();  bar_base + (n << 8)
  // causes cross-CTA collisions at high CTA counts (CTA 0's bar1 = CTA 256's
  // bar0 = 256).  The barrier class isolates each CTA's barriers.
  // ---------------------------------------------------------------------
  // a_size must match the HOST's cta_M * tileK, not the compile-time
  // VX_CFG_ISSUE_WIDTH, because the host may launch fewer warps than
  // ISSUE_WIDTH (e.g. when VX_CAPS_ISSUE_WIDTH < VX_CFG_ISSUE_WIDTH).
  // Using the wrong value overflows smem and corrupts stack data.
  const uint32_t a_size      = cta_M * ctx::tileK;
  const uint32_t b_size      = ctx::tileK * ctx::xtileN;
  const uint32_t stage_stride = wgmma_dbuf_stride_elems(a_size + b_size, sizeof(ctx::input_t));

  auto smem = reinterpret_cast<ctx::input_t *>(__local_mem());
  const uint32_t a_warp_off = warp_rank * ctx::xtileM * ctx::tileK;

  // Two barriers, one per pipeline stage.  The barrier class computes
  //   bar_id = (logical_id << 8) + get_local_group_id()
  // ensuring every CTA gets unique hardware barrier slots.
  vortex::barrier bar0(0);
  vortex::barrier bar1(1);

  // Prologue: issue the first K-tile into stage 0 (bar0).
  if (is_dxa_warp) {
    bar0.expect_tx(2);
    vx_dxa_issue_2d_wg(kDescA, bar0.id(), smem, 0, tile_row);
    vx_dxa_issue_2d_wg(kDescB, bar0.id(), smem + a_size, tile_col, 0);
  }

  uint32_t cur = 0;
  for (uint32_t k = 0; k < K; k += ctx::tileK) {
    uint32_t nxt = cur ^ 1u;
    uint32_t next_k = k + ctx::tileK;

    // Prefetch the next K-tile into the other stage while the WGMMA below
    // consumes the current stage.
    if (next_k < K && is_dxa_warp) {
      vortex::barrier& bar_nxt = (nxt == 0) ? bar0 : bar1;
      bar_nxt.expect_tx(2);
      vx_dxa_issue_2d_wg(kDescA, bar_nxt.id(), smem + nxt * stage_stride, next_k, tile_row);
      vx_dxa_issue_2d_wg(kDescB, bar_nxt.id(), smem + nxt * stage_stride + a_size, tile_col, next_k);
    }

    // Wait for the current stage's DXA (all warps participate).
    vortex::barrier& bar_cur = (cur == 0) ? bar0 : bar1;
    bar_cur.arrive_and_wait();

    // Compute on the current stage.
    auto A_warp = smem + cur * stage_stride + a_warp_off;
    auto desc_b = vt::vx_make_smem_desc(smem + cur * stage_stride + a_size, 0);

#if defined(WGMMA_RS) && (WGMMA_NRC <= 16)
    ctx::fragment_a fragA;
    ctx::load_matrix_sync(fragA, A_warp, ctx::tileK);
    ctx::wgmma_sync(fragC, fragA, desc_b, fragC);
#else
    auto desc_a = vt::vx_make_smem_desc(A_warp, ctx::tileK * sizeof(ctx::input_t));
    ctx::wgmma_sync(fragC, desc_a, desc_b, fragC);
#endif

    // Sync after WGMMA before this stage is reused by a later prefetch.
    bar_cur.arrive_and_wait();

    cur = nxt;
  }
#else
  // ---------------------------------------------------------------------
  // Single-buffered (default): DXA load, sync, compute, sync.
  // ---------------------------------------------------------------------
  auto smem   = reinterpret_cast<ctx::input_t *>(__local_mem());
  auto A_smem = smem;
  auto B_smem = smem + cta_M * ctx::tileK;

  vortex::barrier bar(0);

  for (uint32_t k = 0; k < K; k += ctx::tileK) {
    {
    #if defined(SW_LOAD_A) && defined(SW_LOAD_B)
      // both via SW — no DXA needed
    #elif defined(SW_LOAD_A)
      if (is_dxa_warp) { bar.expect_tx(1); vx_dxa_issue_2d_wg(kDescB, bar.id(), B_smem, tile_col, k); }
    #elif defined(SW_LOAD_B)
      if (is_dxa_warp) { bar.expect_tx(1); vx_dxa_issue_2d_wg(kDescA, bar.id(), A_smem, k, tile_row); }
    #else
      if (is_dxa_warp) {
        bar.expect_tx(2);
        vx_dxa_issue_2d_wg(kDescA, bar.id(), A_smem, k, tile_row);
        vx_dxa_issue_2d_wg(kDescB, bar.id(), B_smem, tile_col, k);
      }
    #endif
    #ifdef SW_LOAD_A
      uint32_t a_size = cta_M * ctx::tileK;
      for (uint32_t i = 0; i < a_size; i += num_threads) {
        uint32_t idx = i + tid;
        uint32_t r = idx / ctx::tileK;
        uint32_t c = idx % ctx::tileK;
        A_smem[r * ctx::tileK + c] = pA[(tile_row + r) * K + (k + c)];
      }
    #endif
    #ifdef SW_LOAD_B
      uint32_t b_size = ctx::tileK * ctx::xtileN;
      for (uint32_t i = 0; i < b_size; i += num_threads) {
        uint32_t idx = i + tid;
        uint32_t r = idx / ctx::xtileN;
        uint32_t c = idx % ctx::xtileN;
        B_smem[ctx::b_blockmajor_idx(r, c)] = pB[(k + r) * N + (tile_col + c)];
      }
    #endif
    }

    bar.arrive_and_wait();

    auto A_warp = A_smem + warp_rank * ctx::xtileM * ctx::tileK;
    auto desc_b = vt::vx_make_smem_desc(B_smem, 0);

  #if defined(WGMMA_RS) && (WGMMA_NRC <= 16)
    ctx::fragment_a fragA;
    ctx::load_matrix_sync(fragA, A_warp, ctx::tileK);
    ctx::wgmma_sync(fragC, fragA, desc_b, fragC);
  #else
    auto desc_a = vt::vx_make_smem_desc(A_warp, ctx::tileK * sizeof(ctx::input_t));
    ctx::wgmma_sync(fragC, desc_a, desc_b, fragC);
  #endif

    bar.arrive_and_wait();
  }
#endif

  // Store the computed C tile to global memory.
  auto pTileC = pC + (tile_row + warp_rank * ctx::xtileM) * N + tile_col;
  ctx::store_matrix_sync(pTileC, fragC, N);
}
