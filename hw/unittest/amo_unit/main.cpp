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

// Directed check of the reservation hold deadline: a hart that leaves the LR/SC
// sequence for good leaves its station installed, and another hart must regain
// the line at the derived bound -- not earlier (the station belongs to its
// owner) and not later (an unretired reservation may not block forever).

#include "vl_simulator.h"
#include "VVX_amo_unit.h"
#include <VX_config.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>

#define CHECK(x)                                            \
  do {                                                      \
    if (x) break;                                           \
    std::fprintf(stderr, "FAILED: %s (cycle %u)\n", #x, cyc); \
    std::abort();                                           \
  } while (false)

#ifndef AMO_TURNAROUND
#define AMO_TURNAROUND 64
#endif

namespace {

constexpr int clog2(int n) { return (n <= 1) ? 0 : 1 + clog2((n + 1) / 2); }

// Mirrors VX_gpu_pkg::HART_ID_WIDTH and VX_amo_unit's RES_HOLD_CYCLES, so the
// test asserts the module's own deadline instead of a literal.
constexpr int NC_BITS = clog2(VX_CFG_NUM_CORES);
constexpr int NW_BITS = clog2(VX_CFG_NUM_WARPS);
constexpr int NT_BITS = clog2(VX_CFG_NUM_THREADS);
constexpr int HART_ID_BITS = NC_BITS + NW_BITS + NT_BITS;
constexpr int HART_ID_WIDTH = (HART_ID_BITS > 0) ? HART_ID_BITS : 1;
constexpr int NUM_HARTS = 1 << HART_ID_WIDTH;
constexpr uint32_t RES_HOLD = AMO_TURNAROUND * (NUM_HARTS + 1);

constexpr uint32_t LINE = 0x2000;  // one line, one station, fixed tag
constexpr uint32_t OWNER = 0;      // hart that abandons its reservation
constexpr uint32_t WAITER = 1;     // hart that must not be starved
constexpr uint32_t THIRD = 2;      // bystander for the write path

using Device = VVX_amo_unit;

}  // namespace

int main(int argc, char **argv) {
  Verilated::commandArgs(argc, argv);

  vl_simulator<Device> sim;
  sim->pipe_stall = 0;
  sim->compute_op = 0;
  sim->compute_unsigned = 0;
  sim->compute_width = 3;
  sim->compute_old = 0;
  sim->compute_rhs = 0;

  uint64_t ticks = sim.reset(0);
  uint32_t cyc = 1;

  // Drive a committed AMO; the look-ahead address always names the same line,
  // so the station's registered payload is present at the commit cycle.
  auto set = [&](uint32_t hart, bool lr, bool sc, bool inv) {
    sim->res_hart_id = hart;
    sim->res_reserve = lr;
    sim->res_clear = sc;
    sim->res_invalidate = inv;
    sim->res_line_addr = LINE;
    sim->res_line_addr_n = LINE;
  };
  auto edge = [&]() {
    ticks = sim.step(ticks, 2);
    ++cyc;
  };
  // Combinational SC outcome for this hart; no clock edge.
  auto holds = [&](uint32_t hart) {
    sim->res_hart_id = hart;
    sim->eval();
    return sim->res_check != 0;
  };

  std::printf("%d harts, hold deadline %u cycles\n", NUM_HARTS, RES_HOLD);

  // 1) The owner reserves the line and then leaves the LR/SC sequence: no SC,
  // no store, no further AMO from it.
  set(OWNER, false, false, false);
  edge();
  const uint32_t t_install = cyc;
  set(OWNER, true, false, false);
  edge();
  CHECK(holds(OWNER));    // installed for the owner
  CHECK(!holds(WAITER));  // and owned by that hart alone

  // 2) The waiter's retry loop runs for the whole lease. Every LR it commits is
  // refused and every SC it would issue fails, but nothing it does refreshes or
  // steals the station.
  while (cyc < t_install + RES_HOLD) {
    set(WAITER, true, false, false);
    sim->res_hart_id = WAITER;
    sim->eval();
    CHECK(sim->res_check == 0);
    edge();
  }

  // 3) Past the lease the station lapses and the waiter takes it. Without the
  // deadline it would keep failing here and the loop would never retire.
  uint32_t t_grant = 0;
  while (cyc <= t_install + RES_HOLD + 8) {
    set(WAITER, true, false, false);
    edge();
    if (holds(WAITER)) {
      t_grant = cyc;
      break;
    }
  }
  CHECK(t_grant != 0);
  CHECK(t_grant - t_install >= RES_HOLD);
  CHECK(t_grant - t_install <= RES_HOLD + 4);
  std::printf("station lapsed %u cycles after install\n", t_grant - t_install);

  // 4) The waiter's SC retires the station, so the line is free for anybody,
  // including the original owner coming back.
  set(WAITER, false, true, false);
  sim->eval();
  CHECK(sim->res_check != 0);
  edge();
  CHECK(!holds(WAITER));
  set(OWNER, true, false, false);
  edge();
  CHECK(holds(OWNER));

  // 5) A reservation consumed inside its lease is unaffected: idling well under
  // the deadline must not lapse it.
  set(OWNER, false, false, false);
  for (int i = 0; i < 200; ++i) {
    edge();
  }
  CHECK(holds(OWNER));
  set(OWNER, false, true, false);
  sim->eval();
  CHECK(sim->res_check != 0);
  edge();
  CHECK(!holds(OWNER));

  // 6) A committed write to the line still breaks a live reservation at once,
  // independent of the deadline.
  set(THIRD, true, false, false);
  edge();
  CHECK(holds(THIRD));
  set(OWNER, false, false, true);
  edge();
  CHECK(!holds(THIRD));
  set(OWNER, true, false, false);
  edge();
  CHECK(holds(OWNER));

  std::printf("PASSED!\n");
  std::printf("Simulation time: %u cycles\n", cyc);

  return 0;
}
