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
  // The CTA warp count is fixed at VX_CFG_ISSUE_WIDTH (the WGMMA lockstep
  // group size), so the A/B tile footprint and the bank-shifted stage stride
  // are compile-time constants. Keeping them constant lets the compiler emit
  // immediate smem offsets instead of carrying a live pointer set, which
  // previously spilled to local memory and dominated the load latency. Stage
  // 1 is bank-shifted by half a LMEM sweep (wgmma_dbuf_stride_elems) so its
  // DXA writes use banks disjoint from the compute stage's reads.
  // ---------------------------------------------------------------------
  constexpr uint32_t a_size      = VX_CFG_ISSUE_WIDTH * ctx::xtileM * ctx::tileK;
  constexpr uint32_t b_size      = ctx::tileK * ctx::xtileN;
  constexpr uint32_t stage_stride = wgmma_dbuf_stride_elems(a_size + b_size, sizeof(ctx::input_t));

  auto smem = reinterpret_cast<ctx::input_t *>(__local_mem());
  const uint32_t a_warp_off = warp_rank * ctx::xtileM * ctx::tileK;

  // One shared barrier base: bar n = bar_base + (n << 8). Keeping this as a
  // single derived value (instead of a bar[2] array of runtime ids) avoids
  // spilling the barrier state to local memory each iteration.
  const uint32_t bar_base = get_local_group_id();
  const uint32_t nwarps   = get_num_sub_groups();

  // Prologue: issue the first K-tile into stage 0 (barrier 0).
  if (is_dxa_warp) {
    vx_barrier_expect_tx(bar_base, 2);
    vx_dxa_issue_2d_wg(kDescA, bar_base, smem, 0, tile_row);
    vx_dxa_issue_2d_wg(kDescB, bar_base, smem + a_size, tile_col, 0);
  }

  uint32_t cur = 0;
  for (uint32_t k = 0; k < K; k += ctx::tileK) {
    uint32_t nxt = cur ^ 1u;
    uint32_t next_k = k + ctx::tileK;

    // Prefetch the next K-tile into the other stage while the WGMMA below
    // consumes the current stage.
    if (next_k < K && is_dxa_warp) {
      uint32_t bar_nxt = bar_base + (nxt << 8);
      vx_barrier_expect_tx(bar_nxt, 2);
      vx_dxa_issue_2d_wg(kDescA, bar_nxt, smem + nxt * stage_stride, next_k, tile_row);
      vx_dxa_issue_2d_wg(kDescB, bar_nxt, smem + nxt * stage_stride + a_size, tile_col, next_k);
    }

    // Wait for the current stage's DXA (all warps participate).
    vx_barrier(bar_base + (cur << 8), nwarps);

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
    vx_barrier(bar_base + (cur << 8), nwarps);

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
