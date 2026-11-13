#ifndef _COMMON_H_
#define _COMMON_H_

typedef struct {
  uint32_t count;
  uint64_t dst_addr;
} kernel_arg_t;

// Per-iteration payload and the per-core sentinel written after the loop; the
// host checks both to prove the warp drained instead of wedging.
#define WSYNC_PAIRS_VALUE    0xA5A50000u
#define WSYNC_PAIRS_SENTINEL 0xC0DE0000u

#endif
