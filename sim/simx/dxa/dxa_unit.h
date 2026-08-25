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
#include "types.h"
#include "instr_trace.h"

namespace vortex {

class Core;

// DxaReq — per-SFU dispatch packet. The SFU owns the outbound SimChannel;
// DxaUnit is a plain helper sub-class of SfuUnit that decodes lanes and
// pushes onto that channel.
struct DxaReq {
  Core*    core;          // routes barrier-release back at completion
  uint64_t uuid;
  uint32_t wid;
  uint32_t desc_slot;     // descriptor table index
  uint32_t bar_id;        // RAW (pre bar_decode_id) — kept raw so that
                          // multicast offset arithmetic (bar_id + cta_idx)
                          // increments cta_no in the encoded low byte.
                          // Decoded only at the release call site.
  uint32_t cta_mask;      // multicast warp mask (>1 bit ⇒ multicast)
  uint64_t smem_addr;
  uint32_t coords[5];
};

// DXA sub-unit of the SFU. Plain (non-SimObject) class owned by SfuUnit;
// lane-decodes a DxaType trace and forwards it onto the SFU's outbound
// DxaReq channel.
class DxaUnit {
public:
  // The outbound channels live on SfuUnit (which is the SimObject).
  // req_out_ carries A-tile fetches, req_out_b_ carries B-tile fetches
  // (routed to a second DxaCore for parallel GMEM access).
  DxaUnit(Core* core, SimChannel<DxaReq>& req_out, SimChannel<DxaReq>& req_out_b)
    : core_(core), req_out_(req_out), req_out_b_(req_out_b) {}

  // Decode lanes 0..3 from the trace's source operands and try to push a
  // DxaReq on the appropriate SFU outbound channel (A or B based on
  // desc_slot). Returns the trace on success or nullptr on backpressure.
  instr_trace_t* process(instr_trace_t* trace);

private:
  Core*               core_;
  SimChannel<DxaReq>& req_out_;
  SimChannel<DxaReq>& req_out_b_;
};

} // namespace vortex
