#include <vx_spawn2.h>
#include <vx_intrinsics.h>
#include "common.h"
#include <vx_barrier.h>

__kernel void kernel_main(kernel_arg_t* __UNIFORM__ arg) {
  vortex::gbarrier bar1(1), bar2(2), bar3(3);

  auto cid = vx_core_id();
  auto wid = vx_warp_id();
  auto tid = vx_thread_id();

  auto pre_ptr    = reinterpret_cast<uint32_t*>(arg->pre_addr);
  auto post_ptr   = reinterpret_cast<uint32_t*>(arg->post_addr);
  auto phase_ptr  = reinterpret_cast<uint32_t*>(arg->phase_addr);
  auto status_ptr = reinterpret_cast<uint32_t*>(arg->status_addr);

  bool leader = (wid == 0 && tid == 0);
  uint32_t run_base = arg->launch_id * ASYNC_GBARRIER_NUM_ROUNDS * arg->num_cores;

  for (uint32_t round = 0; round < ASYNC_GBARRIER_NUM_ROUNDS; ++round) {
    uint32_t result_base = run_base + round * arg->num_cores;
    uint32_t status_index = arg->launch_id * ASYNC_GBARRIER_NUM_ROUNDS + round;
    auto& barrier = (round & 1) ? bar2 : bar1;

    if (leader) {
      pre_ptr[result_base + cid] = arg->launch_id * 1000 + (round + 1) * (cid + 1);
    }

    vx_fence();

    uint32_t phase = barrier.arrive();

    uint32_t overlap_work = ((cid + 1) * 0x9e3779b9u) ^ ((wid + 1) * 0x85ebca6bu) ^ (tid + 1) ^ round;
    for (uint32_t i = 0; i < 32; ++i) {
      overlap_work = overlap_work * 1664525u + 1013904223u;
      overlap_work ^= (overlap_work >> 13);
    }

    barrier.wait(phase);

    if (leader) {
      if (round == 0) {
        uint32_t sum = 0;
        for (uint32_t i = 0; i < arg->num_cores; ++i) {
          sum += pre_ptr[result_base + i];
        }
        post_ptr[result_base + cid] = sum + (overlap_work == 0xffffffffu);
      } else {
        post_ptr[result_base + cid] = pre_ptr[result_base + cid];
      }
      phase_ptr[result_base + cid] = phase;
    }

    vx_fence();

    bar3.arrive_and_wait();

    if (cid == 0 && leader) {
      status_ptr[status_index] = phase != ((round >> 1) & 1);
    }
  }
}
