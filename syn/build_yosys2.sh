#!/bin/bash
set -e
cd /tmp
if [ ! -d yosys-0.69-src ]; then
  git clone --depth 1 --branch yosys-0.68 https://github.com/YosysHQ/yosys.git yosys-0.68-src 2>&1 || \
  git clone --depth 1 https://github.com/YosysHQ/yosys.git yosys-0.68-src 2>&1
fi
cd yosys-0.68-src
# Build with PREFIX pointing to our install location
make config-gcc
make -j$(nproc) PREFIX=/home/ubuntu/yosys-new2 PRESDLIBS="" 2>&1 | tail -5
echo "=== Build done ==="
