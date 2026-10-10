#ifndef _COMMON_H_
#define _COMMON_H_

#include <stdint.h>

#define ASYNC_GBARRIER_NUM_ROUNDS 16

typedef struct {
  uint32_t num_cores;
  uint32_t num_groups;
  uint32_t group_size;
  uint32_t launch_id;
  uint64_t pre_addr;
  uint64_t post_addr;
  uint64_t phase_addr;
  uint64_t status_addr;
} kernel_arg_t;

#endif
