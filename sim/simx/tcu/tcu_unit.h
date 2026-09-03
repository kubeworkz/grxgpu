// Copyright © 2019-2023
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include <simobject.h>
#include <mempool.h>
#include <array>
#include "instr_trace.h"
#include "instr.h"
#include "func_unit.h"
#include "tcu_tbuf.h"

// The TCU metadata SRAM is present when any metadata-consuming mode (MX or
// sparse) is enabled. Internal derived macro — not a VX_CFG_* knob; mirrors the
// RTL derivation in hw/rtl/VX_define.vh.
#if defined(VX_CFG_TCU_MX_ENABLE) || defined(VX_CFG_TCU_SPARSE_ENABLE)
#define TCU_META_ENABLE
#endif

namespace vortex {

class Core;

///////////////////////////////////////////////////////////////////////////////

// Micro-op generator for TCU instructions (WMMA/WGMMA).
// Owned by each per-warp Sequencer.
class TcuUopGen {
public:
  TcuUopGen(PoolAllocator<Instr, 64>& pool) : pool_(pool) {}

  // Returns total micro-op count for a macro instruction (>1 means macro-op).
  static uint32_t uop_count(const Instr& instr);

  // Generate micro-op Instr at uop_index for the given macro instruction.
  Instr::Ptr get(const Instr& macro_instr, uint32_t uop_index);

private:
  PoolAllocator<Instr, 64>& pool_;
};

///////////////////////////////////////////////////////////////////////////////



/// TGM FSM state: hardware-managed DXA prefetch + WGMMA loop.
struct TgmFsmState {
  enum Phase : uint8_t { IDLE, FETCH, WAIT_DXA, COMPUTE, ADVANCE, DONE };
  Phase      phase = IDLE;
  uint32_t   k_current = 0;       // current K-tile index
  uint32_t   k_end = 0;           // K_end (exclusive)
  uint32_t   tile_row = 0;        // M-tile offset for DXA A fetch
  uint32_t   tile_col = 0;        // N-tile offset for DXA B fetch
  uint32_t   fmt_s = 9;           // input format id (fp16 default; TGM fixed context)
  uint32_t   a_desc = 0;          // A tile descriptor (smem addr)
  uint32_t   b_desc = 0;          // B tile descriptor (smem addr)
  uint32_t   stage = 0;           // double-buffer stage (0 or 1)
  uint32_t   wid = 0;             // warp ID
  uint32_t   cta_id = 0;          // CTA ID
  uint32_t   compute_step = 0;    // current WGMMA compute step
  uint32_t   compute_total = 0;   // total WGMMA steps per K-tile
  uint32_t   bar_wait_phase = 0;  // barrier phase captured at FETCH (DXA done)
  uint32_t   stage_stride_bytes = 0;  // double-buffer stride in bytes
  bool       has_prefetch = false;  // true if prefetch for next K-tile was issued
  uint32_t   prefetch_bar_wait_phase = 0;  // barrier phase for prefetch
  // Persistent accumulator across K-tiles: [fragment reg][lane].
  std::vector<std::vector<reg_data_t>> fragC;
};

class TcuUnit : public FuncUnit<VX_CFG_NUM_TCU_BLOCKS> {
public:
  using Ptr = std::shared_ptr<TcuUnit>;

  static op_string_t op_string(TcuType tcu_type, IntrTcuArgs args);

	struct PerfStats {
		uint64_t latency = 0;
		uint64_t tbuf_stalls = 0;      // cycles stalled on TcuTbufA/TcuSharedB readiness
		uint64_t tbuf_cache_hits = 0;  // WGMMA entries with all lines already resident (cross-WGMMA reuse)
		uint64_t lmem_reads = 0;       // sum of TcuTbufA + TcuSharedB LmemReqs issued
		// Gate breakdown: which operand(s) the WGMMA gate is waiting on.
		uint64_t tbuf_stall_a_only = 0;  // A pending, B ready
		uint64_t tbuf_stall_b_only = 0;  // B pending, A ready
		uint64_t tbuf_stall_ab     = 0;  // both pending
		uint64_t tbuf_pend_a_sum   = 0;  // summed sampled outstanding A lines during stalls
		uint64_t tbuf_pend_b_sum   = 0;  // summed sampled outstanding B lines during stalls
		uint64_t tbuf_stall_samples = 0; // number of stall ticks sampled

		PerfStats& operator+=(const PerfStats& rhs) {
			this->latency               += rhs.latency;
			this->tbuf_stalls           += rhs.tbuf_stalls;
			this->tbuf_cache_hits       += rhs.tbuf_cache_hits;
			this->lmem_reads            += rhs.lmem_reads;
			this->tbuf_stall_a_only     += rhs.tbuf_stall_a_only;
			this->tbuf_stall_b_only     += rhs.tbuf_stall_b_only;
			this->tbuf_stall_ab         += rhs.tbuf_stall_ab;
			this->tbuf_pend_a_sum       += rhs.tbuf_pend_a_sum;
			this->tbuf_pend_b_sum       += rhs.tbuf_pend_b_sum;
			this->tbuf_stall_samples    += rhs.tbuf_stall_samples;
			return *this;
		}
	};

  TcuUnit(const SimContext &ctx, const char* name, Core* core);
  virtual ~TcuUnit();

#ifdef TCU_META_ENABLE
  // Metadata AGU port: TCU_LD issues load requests through the LSU block-0
  // client port; response fragments return here and accumulate into the
  // metadata SRAM.
  SimChannel<LsuReq> agu_req_out;
  SimChannel<LsuRsp> agu_rsp_in;
#endif

	void wmma(uint32_t wid,
	          uint32_t fmt_s,
	          uint32_t fmt_d,
	          uint32_t step_m,
	          uint32_t step_n,
	          uint32_t step_k,
	          const std::vector<reg_data_t>& rs1_data,
	          const std::vector<reg_data_t>& rs2_data,
	          const std::vector<reg_data_t>& rs3_data,
	          std::vector<reg_data_t>& rd_data,
	          bool is_sparse);

	void wgmma(uint32_t wid,
	           uint32_t fmt_s,
	           uint32_t fmt_d,
	           uint32_t step_m,
	           uint32_t step_n,
	           uint32_t step_k,
	           uint32_t a_desc,
	           uint32_t b_desc,
	           const std::vector<reg_data_t>& rs1_data,
	           const std::vector<reg_data_t>& rs2_data,
	           const std::vector<reg_data_t>& rs3_data,
	           std::vector<reg_data_t>& rd_data,
	           bool is_sparse,
	           uint32_t cd_nregs,
	           uint32_t is_a_smem,
	           uint32_t is_setup_uop);

	// Tile-buffer subsystem (owns abuf×Q + bbuf + LMEM arb).
	// Exposed so that `Core` can bind its single LMEM port pair.
	TcuTbuf::Ptr& tbuf();

	const PerfStats& perf_stats() const;

	// WGMMA CTA admission control. `wgmma_cta_blocked(wid)` reports whether the
	// warp's CTA is fenced out by a different CTA that owns the current WGMMA
	// lockstep slot; `wgmma_cta_admit(wid)` records the owning CTA when a head
	// uop issues. Core::issue uses these to serialize WGMMA lockstep groups
	// BEFORE a warp acquires the per-lane FU lock, so a deferred CTA can never
	// hold that lock against the CTA it is waiting for (which otherwise
	// deadlocks the TCU).
	bool wgmma_cta_blocked(uint32_t wid) const;
	void wgmma_cta_admit(uint32_t wid);

protected:
  void on_reset() override;
  void on_tick() override;

private:
	class Impl;
	Impl* impl_;

	TcuTbuf::Ptr tbuf_;
};

} // namespace vortex
