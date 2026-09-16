#!/usr/bin/env python3
"""Move drain loop from before start pulse to after it (GRXCP team fix)."""
import sys

path = "/home/ubuntu/grxgpu/sim/rtlsim/processor.cpp"
with open(path, "r") as f:
    content = f.read()

# Step 1: Remove drain block from before start pulse
old_block = """    // drain any residual busy from the previous frame before starting a new one.
    // busy is already high after reset and at the end of every frame; if we
    // pulse start while busy is high, the wait-for-busy loop exits immediately
    // and the drain loop exits after one tick, executing only ~1/2300 of the frame.
    constexpr uint32_t DRAIN_TIMEOUT = 100000;
    for (uint32_t i = 0; device_->busy && i < DRAIN_TIMEOUT; ++i) {
      this->tick();
    }

    // pulse start for one cycle"""

new_block = """    // pulse start for one cycle"""

if old_block not in content:
    print("ERROR: old drain block not found", file=sys.stderr)
    sys.exit(1)

content = content.replace(old_block, new_block)

# Step 2: Insert drain block after start pulse, before wait-for-busy
old_wait = """    // Upper bound on the post-start wait for busy (see below); a no-work frame
    // never asserts busy, so the wait must not be unbounded.
    constexpr uint32_t NO_WORK_TIMEOUT = 100000;

    // wait for device to go busy."""

new_wait = """    // Upper bound on the post-start wait for busy (see below); a no-work frame
    // never asserts busy, so the wait must not be unbounded.
    constexpr uint32_t NO_WORK_TIMEOUT = 100000;

    // drain any residual busy from the previous frame before starting a new one.
    // busy is already high after reset and at the end of every frame; if we
    // pulse start while busy is high, the wait-for-busy loop exits immediately
    // and the drain loop exits after one tick, executing only ~1/2300 of the frame.
    constexpr uint32_t DRAIN_TIMEOUT = 100000;
    for (uint32_t i = 0; device_->busy && i < DRAIN_TIMEOUT; ++i) {
      this->tick();
    }

    // wait for device to go busy."""

if old_wait not in content:
    print("ERROR: wait-for-busy block not found", file=sys.stderr)
    sys.exit(1)

content = content.replace(old_wait, new_wait)

with open(path, "w") as f:
    f.write(content)

print("Drain loop moved after start pulse")
