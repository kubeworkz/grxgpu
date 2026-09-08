#!/bin/bash
cd /tmp/yosys-0.68/build
make -j$(nproc) > /tmp/yosys_build.log 2>&1
echo "Build finished with exit code $?" >> /tmp/yosys_build.log
