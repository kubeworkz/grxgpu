#include "common.h"
#include <vx_spawn2.h>
#include <vx_tensor.h>
#include <vx_intrinsics.h>

namespace vt = vortex::tensor;

using ctx = vt::wgmma_context<VX_CFG_NUM_THREADS, vt::ITYPE, vt::OTYPE, false, WGMMA_NRC>;

__kernel void kernel_main(kernel_arg_t* __UNIFORM__ arg) {
  auto pA = reinterpret_cast<ctx::input_t *>(arg->A_addr);
  auto pB = reinterpret_cast<ctx::input_t *>(arg->B_addr);
  auto pC = reinterpret_cast<ctx::output_t *>(arg->C_addr);

  uint32_t N = arg->N;
  uint32_t K = arg->K;

  uint32_t tid = threadIdx.x;
  uint32_t num_threads = blockDim.x;  // warps * VX_CFG_NUM_THREADS
  uint32_t warp_rank = tid / VX_CFG_NUM_THREADS;
  uint32_t num_warps = num_threads / VX_CFG_NUM_THREADS;

  // CTA tile dimensions
  uint32_t cta_M = num_warps * ctx::xtileM;
  uint32_t tile_row = blockIdx.y * cta_M;
  uint32_t tile_col = blockIdx.x * ctx::xtileN;

  ctx::fragment_acc fragC;
  ctx::fill_fragment(fragC, 0);

#ifdef WGMMA_DOUBLE_BUFFER
  // ---------------------------------------------------------------------
  // Double-buffered smem staging: two stages, each holding A then B.
  //
  // NOTE: measured as a REGRESSION in SimX. Prefetching the next K-tile with
  // the plain ld.global + st.shared cooperative load breaks the burst locality
  // of the single-buffered load phase (load_lat 34 -> ~677 cycles, scheduler
  // 15% -> ~91% idle, ~6-30x more cycles), so the TCU is utilized *less*.
  // A real overlap requires an async-copy path (e.g. the DXA engine used by
  // sgemm2_dxa), not software ping-pong with in-order loads.
  // ---------------------------------------------------------------------
  auto smem = reinterpret_cast<ctx::input_t *>(__local_mem());
  uint32_t a_size      = cta_M * ctx::tileK;
  uint32_t b_size      = ctx::tileK * ctx::xtileN;
  uint32_t stage_elems = a_size + b_size;

#ifdef WGMMA_RMAJOR_A
  const uint32_t a_warp_off = warp_rank * ctx::xtileM * ctx::tileK;
  constexpr uint32_t a_ldm = ctx::tileK;
#else
  const uint32_t a_warp_off = warp_rank * ctx::a_warp_elems;
  constexpr uint32_t a_ldm = 0;
#endif

  // Prologue: stage 0 receives the first K-tile.
  {
    auto A_smem = smem;
    auto B_smem = smem + a_size;
    for (uint32_t i = 0; i < a_size; i += num_threads) {
      uint32_t idx = i + tid;
      uint32_t r = idx / ctx::tileK;
      uint32_t c = idx % ctx::tileK;
#ifdef WGMMA_RMAJOR_A
      A_smem[r * ctx::tileK + c] = pA[(tile_row + r) * K + c];
#else
      A_smem[ctx::a_blockmajor_idx(r, c)] = pA[(tile_row + r) * K + c];
#endif
    }
    for (uint32_t i = 0; i < b_size; i += num_threads) {
      uint32_t idx = i + tid;
      uint32_t r = idx / ctx::xtileN;
      uint32_t c = idx % ctx::xtileN;
      B_smem[ctx::b_blockmajor_idx(r, c)] = pB[r * N + (tile_col + c)];
    }
  }
  __syncthreads();

  uint32_t cur = 0;
  for (uint32_t k = 0; k < K; k += ctx::tileK) {
    uint32_t nxt = cur ^ 1u;

    // Prefetch the next K-tile into the other stage.
    uint32_t next_k = k + ctx::tileK;
    if (next_k < K) {
      auto A_smem = smem + nxt * stage_elems;
      auto B_smem = smem + nxt * stage_elems + a_size;
      for (uint32_t i = 0; i < a_size; i += num_threads) {
        uint32_t idx = i + tid;
        uint32_t r = idx / ctx::tileK;
        uint32_t c = idx % ctx::tileK;
#ifdef WGMMA_RMAJOR_A
        A_smem[r * ctx::tileK + c] = pA[(tile_row + r) * K + (next_k + c)];
#else
        A_smem[ctx::a_blockmajor_idx(r, c)] = pA[(tile_row + r) * K + (next_k + c)];
#endif
      }
      for (uint32_t i = 0; i < b_size; i += num_threads) {
        uint32_t idx = i + tid;
        uint32_t r = idx / ctx::xtileN;
        uint32_t c = idx % ctx::xtileN;
        B_smem[ctx::b_blockmajor_idx(r, c)] = pB[(next_k + r) * N + (tile_col + c)];
      }
    }

    // Compute on the current stage.
    {
      auto A_warp = smem + cur * stage_elems + a_warp_off;
      auto desc_b = vt::vx_make_smem_desc(smem + cur * stage_elems + a_size, 0);
#if defined(WGMMA_RS) && (WGMMA_NRC <= 16)
      ctx::fragment_a fragA;
      ctx::load_matrix_sync(fragA, A_warp, a_ldm);
      ctx::wgmma_sync(fragC, fragA, desc_b, fragC);
#else
      auto desc_a = vt::vx_make_smem_desc(A_warp, a_ldm * sizeof(ctx::input_t));
      ctx::wgmma_sync(fragC, desc_a, desc_b, fragC);
#endif
    }

    __syncthreads();
    cur = nxt;
  }
#else
  // ---------------------------------------------------------------------
  // Single-buffered (default): load the whole K-tile, sync, then compute.
  // ---------------------------------------------------------------------
  auto smem   = reinterpret_cast<ctx::input_t *>(__local_mem());
  auto A_smem = smem;
  auto B_smem = smem + cta_M * ctx::tileK;

  for (uint32_t k = 0; k < K; k += ctx::tileK) {
    // Cooperatively load A [cta_M × tileK] into smem.
    uint32_t a_size = cta_M * ctx::tileK;
    for (uint32_t i = 0; i < a_size; i += num_threads) {
      uint32_t idx = i + tid;
      uint32_t r = idx / ctx::tileK;
      uint32_t c = idx % ctx::tileK;
#ifdef WGMMA_RMAJOR_A
      A_smem[r * ctx::tileK + c] = pA[(tile_row + r) * K + (k + c)];
#else
      A_smem[ctx::a_blockmajor_idx(r, c)] = pA[(tile_row + r) * K + (k + c)];
#endif
    }

    // Cooperatively load B into smem (block-major).
    uint32_t b_size = ctx::tileK * ctx::xtileN;
    for (uint32_t i = 0; i < b_size; i += num_threads) {
      uint32_t idx = i + tid;
      uint32_t r = idx / ctx::xtileN;
      uint32_t c = idx % ctx::xtileN;
      B_smem[ctx::b_blockmajor_idx(r, c)] = pB[(k + r) * N + (tile_col + c)];
    }

    __syncthreads();

#ifdef WGMMA_RMAJOR_A
    auto A_warp = A_smem + warp_rank * ctx::xtileM * ctx::tileK;
#else
    auto A_warp = A_smem + warp_rank * ctx::a_warp_elems;
#endif
    auto desc_b = vt::vx_make_smem_desc(B_smem, 0);

#ifdef WGMMA_RMAJOR_A
    constexpr uint32_t a_ldm = ctx::tileK;
#else
    constexpr uint32_t a_ldm = 0;
#endif
#if defined(WGMMA_RS) && (WGMMA_NRC <= 16)
    ctx::fragment_a fragA;
    ctx::load_matrix_sync(fragA, A_warp, a_ldm);
    ctx::wgmma_sync(fragC, fragA, desc_b, fragC);
#else
    auto desc_a = vt::vx_make_smem_desc(A_warp, a_ldm * sizeof(ctx::input_t));
    ctx::wgmma_sync(fragC, desc_a, desc_b, fragC);
#endif

    __syncthreads();
  }
#endif

  // Store C tile using wgmma_context's n-major store
  auto out = pC + (tile_row + warp_rank * ctx::xtileM) * N + tile_col;
  ctx::store_matrix_sync(out, fragC, N);
}
