#include <vx_intrinsics.h>
#include "common.h"

// The drain held by a WSYNC must release so the warp reaches the sentinel, and
// the store issued before each pair must be visible to the host afterwards.
// This guards progress and store visibility, not the rule that releases the
// drain: the fixed-threshold and in-flight-count forms are indistinguishable
// here because an older WSYNC commits before the next one is evaluated.
int main() {
  kernel_arg_t* __UNIFORM__ arg = (kernel_arg_t*)csr_read(VX_CSR_MSCRATCH);
  uint32_t count = arg->count;
  uint32_t* dst_ptr = (uint32_t*)arg->dst_addr;
  uint32_t core = vx_core_id();

  for (uint32_t i = 0; i < count; ++i) {
    dst_ptr[i] = WSYNC_PAIRS_VALUE ^ i;
    vx_wsync();
    vx_wsync();
  }

  dst_ptr[count + core] = WSYNC_PAIRS_SENTINEL | core;
  return 0;
}
