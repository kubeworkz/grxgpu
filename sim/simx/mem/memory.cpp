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

#include <VX_types.h>
#include "memory.h"
#include <vector>
#include <queue>
#include <sstream>
#include <unordered_map>
#include <iostream>
#include <stdlib.h>
#include <dram_sim.h>

#include "mem_block_pool.h"
#include "constants.h"
#include "types.h"
#include "amo/amo_ops.h"
#include "debug.h"
#include "VX_config.h"

using namespace vortex;

class Memory::Impl {
private:
	Memory*   simobject_;
	Config    config_;
	std::vector<std::pair<uint32_t, MemRsp>> pending_amo_rsps_;
	MemCrossBar::Ptr mem_xbar_;
	DramSim   dram_sim_;
	RAM*      ram_;
	Memory::PreSendHook pre_send_hook_;
	mutable PerfStats perf_stats_;
	struct DramCallbackArgs {
		Memory::Impl* memsim;
		MemReq request;
		uint32_t bank_id;
		std::shared_ptr<mem_block_t> rsp_data;  // captured at request time for reads
	};

public:
	Impl(Memory* simobject, const Config& config)
		: simobject_(simobject)
		, config_(config)
		, dram_sim_(config.num_banks, config.block_size, config.clock_ratio)
		, ram_(nullptr)
	{
		char sname[100];
		snprintf(sname, 100, "%s-xbar", simobject->name().c_str());
		mem_xbar_ = MemCrossBar::Create(sname, ArbiterType::RoundRobin, config.num_ports, config.num_banks,
			[lg2_block_size = log2ceil(config.block_size), num_banks = config.num_banks](const MemCrossBar::ReqType& req) {
    	// Custom logic to calculate the output index using bank interleaving
			return (uint32_t)((req.addr >> lg2_block_size) & (num_banks-1));
		});
		for (uint32_t i = 0; i < config.num_ports; ++i) {
			simobject->mem_req_in.at(i).bind(&mem_xbar_->ReqIn.at(i));
			mem_xbar_->RspOut.at(i).bind(&simobject->mem_rsp_out.at(i));
		}
	}

	~Impl() {}

	const PerfStats& perf_stats() const {
		perf_stats_.bank_stalls = mem_xbar_->collisions();
		return perf_stats_;
	}

	void reset() {
		dram_sim_.reset();
	}

	void tick() {
		dram_sim_.tick();
		// retry AMO responses that hit a full response channel earlier
		for (auto it = pending_amo_rsps_.begin(); it != pending_amo_rsps_.end(); ) {
			if (mem_xbar_->RspIn.at(it->first).try_send(it->second)) {
				DT(3, simobject_->name() << " mem-amo-rsp" << it->first << ": " << it->second);
				it = pending_amo_rsps_.erase(it);
			} else {
				++it;
			}
		}

		for (uint32_t i = 0; i < config_.num_banks; ++i) {
			if (mem_xbar_->ReqOut.at(i).empty())
				continue;

			auto& mem_req = mem_xbar_->ReqOut.at(i).peek();

#if VX_CFG_EXT_A_ENABLED
			if (memop_is_amo_rmw(mem_req.op)) {
				// Shared RMW executor: every global atomic RMW lands here, so
				// same-address RMWs serialize per DRAM bank and no update can
				// be lost to a private cache's stale copy.
				// NOTE: must run BEFORE the generic read/write block below;
				// memop_is_write() is true for RMW AMOs and the generic path
				// would store the raw operand into RAM first.
				execute_amo_rmw(mem_req, i);
				mem_xbar_->ReqOut.at(i).pop();
				continue;
			}
#endif
			std::shared_ptr<mem_block_t> rsp_data;
			if (ram_) {
				uint64_t line_addr = mem_req.addr & ~uint64_t(VX_CFG_MEM_BLOCK_SIZE - 1);
				// Cache fills/writebacks are simulator-internal traffic and
				// don't carry the kernel's intent (e.g. a write-back cache
				// reads a write-only buffer to fill the line on write-miss,
				// since memory buses lack per-region read/write permissions).
				// Suppress ACL for the duration; ACL still guards upload/download.
				ram_->enable_acl(false);
				if (mem_req.is_write()) {
					// Apply byte-enabled write to RAM at request arrival.
					// IO_COUT-range bytes are tapped to the print buffer and
					// not stored in RAM.
					if (mem_req.data) {
						for (uint32_t b = 0; b < VX_CFG_MEM_BLOCK_SIZE; ++b) {
							if (mem_req.byteen & (1ull << b)) {
								uint8_t value = (*mem_req.data)[b];
								ram_->write(&value, line_addr + b, 1);
							}
						}
					}
				} else {
					// Capture the line at request time; response carries it back.
					rsp_data = make_mem_block();
					ram_->read(rsp_data->data(), line_addr, VX_CFG_MEM_BLOCK_SIZE);
				}
				ram_->enable_acl(true);
			}

			if (pre_send_hook_) {
				pre_send_hook_(mem_req);
			}

			// enqueue the request to the memory system
			auto req_args = new DramCallbackArgs{this, mem_req, i, rsp_data};
			dram_sim_.send_request(
				mem_req.addr,
				mem_req.is_write(),
				[](void* arg)->bool {
					auto rsp_args = reinterpret_cast<const DramCallbackArgs*>(arg);
					if (rsp_args->request.is_write()) {
						delete rsp_args;
						return true;
					} else {
								MemRsp mem_rsp{rsp_args->request.tag, rsp_args->request.hart_id, rsp_args->request.uuid};
						mem_rsp.data = rsp_args->rsp_data;
						if (rsp_args->memsim->mem_xbar_->RspIn.at(rsp_args->bank_id).try_send(mem_rsp)) {
							DT(3, rsp_args->memsim->simobject_->name() << " mem-rsp" << rsp_args->bank_id << ": " << mem_rsp);
							delete rsp_args;
							return true;
						}
					}
					return false; // stall
				},
				req_args
			);

			DT(3, simobject_->name() << " mem-req" << i << ": " << mem_req);
			mem_xbar_->ReqOut.at(i).pop();
		}
	}

#if VX_CFG_EXT_A_ENABLED
	void execute_amo_rmw(const MemReq& req, uint32_t bank_id) {
		const uint8_t width     = (__builtin_popcountll(req.byteen) >= 8) ? 3 : 2;
		const uint32_t n        = 1u << width;
		const uint32_t byte_off = (uint32_t)(req.addr & (VX_CFG_MEM_BLOCK_SIZE - 1));
		const uint64_t rhs = req.data
			? amo_load_word(req.data->data(), byte_off, width)
			: 0ull;
		uint64_t old_word = 0;
		if (ram_) {
			ram_->enable_acl(false);
			uint8_t word[8];
			ram_->read(word, req.addr + byte_off, n);
			old_word = amo_load_word(word, 0, width);
			ram_->enable_acl(true);
		}
		auto rmw = amo_compute(req.op, width, old_word, rhs, req.flags.amo_unsigned);
		if (ram_) {
			ram_->enable_acl(false);
			uint8_t word[8];
			amo_store_word(word, 0, width, rmw.new_word);
			for (uint32_t b = 0; b < n; ++b) {
				ram_->write(&word[b], req.addr + byte_off + b, 1);
			}
			ram_->enable_acl(true);
		}
		auto rsp_block = make_mem_block();
		std::memset(rsp_block->data(), 0, rsp_block->size());
		amo_store_word(rsp_block->data(), byte_off, width, rmw.ret_word);
		MemRsp mem_rsp{req.tag, req.hart_id, req.uuid};
		mem_rsp.data = rsp_block;
		if (mem_xbar_->RspIn.at(bank_id).try_send(mem_rsp)) {
			DT(3, simobject_->name() << " mem-amo-rsp" << bank_id << ": " << mem_rsp);
		} else {
			pending_amo_rsps_.emplace_back(bank_id, mem_rsp);
		}
	}
#endif

	void attach_ram(RAM* ram) {
		ram_ = ram;
	}

	void set_pre_send_hook(Memory::PreSendHook hook) {
		pre_send_hook_ = std::move(hook);
	}
};

///////////////////////////////////////////////////////////////////////////////

Memory::Memory(const SimContext& ctx, const char* name, const Config& config)
	: SimObject<Memory>(ctx, name)
	, mem_req_in(config.num_ports, this)
	, mem_rsp_out(config.num_ports, this)
	, impl_(new Impl(this, config))
{}

Memory::~Memory() {
  delete impl_;
}

void Memory::on_reset() {
  impl_->reset();
}

void Memory::on_tick() {
  impl_->tick();
}

void Memory::attach_ram(RAM* ram) {
  impl_->attach_ram(ram);
}

void Memory::set_pre_send_hook(PreSendHook hook) {
  impl_->set_pre_send_hook(std::move(hook));
}

const Memory::PerfStats &Memory::perf_stats() const {
	return impl_->perf_stats();
}