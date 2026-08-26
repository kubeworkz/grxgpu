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

#include "dxa_unit.h"
#include "core.h"
#include "constants.h"
#include "debug.h"

using namespace vortex;

instr_trace_t* DxaUnit::process(instr_trace_t* trace) {
  if (req_out_.full()) {
    return nullptr;
  }

  // 4-lane wgather encoding:
  //   Lane 0: rs1=smem_addr, rs2=coord2
  //   Lane 1: rs1=meta,      rs2=coord3
  //   Lane 2: rs1=coord0,    rs2=coord4
  //   Lane 3: rs1=coord1,    rs2=cta_mask
  auto& rs1 = trace->src_data[0];
  auto& rs2 = trace->src_data[1];

  uint64_t smem_addr = static_cast<uint64_t>(rs1.at(0).u);
  uint32_t meta      = rs1.at(1).u;
  uint32_t coords[5] = {
    static_cast<uint32_t>(rs1.at(2).u),
    static_cast<uint32_t>(rs1.at(3).u),
    static_cast<uint32_t>(rs2.at(0).u),
    static_cast<uint32_t>(rs2.at(1).u),
    static_cast<uint32_t>(rs2.at(2).u),
  };
  uint32_t cta_mask  = rs2.at(3).u;
  uint32_t desc_slot = meta & 0x0fu;
  uint32_t raw_bar   = (meta >> 4) & 0x07ffffffu;
  // meta[31] = fused A+B pair flag. In pair mode the rs2 lanes carry B's
  // fields (smem_b, meta_b, coord_b0, coord_b1) instead of coords[2..4].
  bool pair = (meta & 0x80000000u) != 0;

  DxaReq req;
  req.core      = core_;
  req.uuid      = trace->uuid;
  req.wid       = trace->wid;
  req.desc_slot = desc_slot;
  // Keep raw bar_id; multicast offset arithmetic relies on encoded form
  // (cta_no in low 8 bits → bar_id + cta_idx targets next CTA's same bar).
  // Release call site decodes via bar_decode_id().
  req.bar_id    = raw_bar;
  req.cta_mask  = cta_mask;
  req.smem_addr = smem_addr;
  for (int i = 0; i < 5; ++i) req.coords[i] = coords[i];

  req.pair = pair;
  if (pair) {
    // rs2 lanes: lane0 = smem_addr_b, lane1 = meta_b,
    //            lane2 = coord_b0,    lane3 = coord_b1.
    // NOTE: lane3 rs2 is the multicast cta_mask slot in the non-pair 2D
    // encoding; in pair mode it carries B's coord1, so we MUST zero the
    // multicast mask here — otherwise a nonzero B K-offset (e.g. 16) is
    // decoded as a multicast mask and the worker releases bar_id + cta_idx
    // for garbage CTA indices, overflowing the barrier table.
    uint32_t meta_b = rs2.at(1).u;
    req.desc_slot_b = meta_b & 0x0fu;
    req.smem_addr_b = static_cast<uint64_t>(rs2.at(0).u);
    req.coords_b[0] = static_cast<uint32_t>(rs2.at(2).u);
    req.coords_b[1] = static_cast<uint32_t>(rs2.at(3).u);
    for (int i = 2; i < 5; ++i) req.coords_b[i] = 0;
    // Pair mode is 2D-only: A's coords[2..4] are unused, and multicast is
    // not supported (single-destination pair only).
    req.coords[2] = req.coords[3] = req.coords[4] = 0;
    req.cta_mask = 0;
  }

  // Barrier pre-registration is the kernel's responsibility via
  // vx_barrier_expect_tx(). The DXA pipeline only emits release events on
  // completion; pre-registration happens explicitly per-CTA so multicast
  // destinations correctly wait.

  req_out_.send(req);
  DT(4, "dxa-unit submit: core=" << core_->id() << ", wid=" << trace->wid
     << ", slot=" << desc_slot << ", bar=" << raw_bar
     << ", cta_mask=0x" << std::hex << cta_mask << std::dec);
  return trace;
}
