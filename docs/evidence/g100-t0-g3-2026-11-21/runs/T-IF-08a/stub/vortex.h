// Minimal host-test stand-in for the runtime <vortex.h>.
// dxa.h only needs the device handle type and the DCR write entry point.
#ifndef VORTEX_HOST_TEST_STUB_H
#define VORTEX_HOST_TEST_STUB_H

#include <cstdint>

typedef void* vx_device_h;

int vx_dcr_write(vx_device_h dev, uint32_t addr, uint32_t value);

#endif
