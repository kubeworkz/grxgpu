# GRXGPU G100

GRXGPU G100 is an open-source RISC-V GPU built on the Vortex architecture. It is a **GPU** — not a GPGPU — with hardware tensor cores, warp-group matrix multiply-accumulate (WGMMA), a data transfer accelerator (DXA), and a graphics fixed-function pipeline.

GRXGPU extends Vortex's RISC-V ISA with GPU-native instructions: WGMMA for dense matrix math, DXA for asynchronous tile fetches from global memory into shared memory, and structured sparsity support. The result is a GPU that can run tensor-core GEMM, ray tracing, and graphics workloads on a configurable RISC-V core mesh.

## Architecture

- **Core mesh**: N independent RISC-V cores, each a full in-order pipeline with hardware threads
- **Tensor cores (TCU)**: per-core WGMMA units supporting fp32, fp16, bf16, tf32, fp8, bf8, and 2:4 structured sparsity
- **DXA**: hardware data transfer accelerator for asynchronous 2D tile fetches (global → shared memory)
- **Graphics pipeline**: rasterizer, texture units, output mergers
- **Ray tracing**: BVH traversal, ray-box and ray-triangle intersection
- **Memory**: per-core LMEM, optional L1/L2/L3 caches, DSMEM for cross-core communication
- **Command Processor**: hardware-accelerated kernel dispatch and management

## Supported Formats

| Format | Input | Accumulator | Status |
|--------|-------|-------------|--------|
| fp32   | ✅    | ✅           | Verified |
| fp16   | ✅    | ✅           | Verified |
| bf16   | ✅    | ✅           | Verified |
| tf32   | ✅    | ✅           | Verified |
| fp8    | ✅    | ✅           | Verified |
| bf8    | ✅    | ✅           | Verified |
| int8   | ✅    | ✅           | Verified |

## Performance

| Benchmark | Config | Result |
|-----------|--------|--------|
| SGEMM K=512 (64×64) | fp16 → fp32 | IPC 1.752, 275K cycles |
| SGEMM K=512 (64×64) | bf16 → fp32 | IPC 1.752, 275K cycles |
| TGM FSM K=512 | 67× instruction reduction vs SW K-loop | 7K vs 483K instrs |
| SGEMM 1024³ | G100 config | PASSED, 111M cycles |

## Directory Structure

- `hw/` — RTL hardware sources
- `sw/` — Software: kernel, runtime, drivers
- `sim/` — Simulators (SimX, RTL)
- `tests/` — Regression tests and benchmarks
- `docs/` — Documentation and design proposals
- `ci/` — Continuous integration scripts
- `VX_config.toml` — Hardware configuration (single source of truth)

## Quick Start

### Prerequisites

- Ubuntu 22.04 or compatible
- RISC-V GNU toolchain (installed via `ci/toolchain_install.sh`)

### Build

```sh
git clone --depth=1 --recursive https://github.com/kubeworkz/grxgpu.git
cd grxgpu
sudo ./ci/install_dependencies.sh
mkdir build && cd build
../configure --xlen=32 --tooldir=$HOME/tools
./ci/toolchain_install.sh
make -s
make install
export VORTEX_PATH=$(pwd)/install
export PKG_CONFIG_PATH=$VORTEX_PATH/lib/pkgconfig:$PKG_CONFIG_PATH
```

### Run a test

```sh
# SGEMM with tensor cores (fp16 → fp32)
cd tests/regression/sgemm_tcu_wg_dxa
make
LD_LIBRARY_PATH=$VORTEX_PATH/lib ./sgemm_tcu_wg_dxa -m 64 -n 64 -k 512

# bf16 SGEMM
cd tests/regression/sgemm_tcu_bf16
make
LD_LIBRARY_PATH=$VORTEX_PATH/lib ./sgemm_tcu_bf16 -m 64 -n 64 -k 512
```

### Run on RTL simulator

```sh
./ci/blackbox.sh --cores=1 --app=vecadd --driver=rtlsim
```

## Configuration

Edit `VX_config.toml` to change hardware parameters:

```toml
VX_CFG_NUM_CORES = 128        # Number of RISC-V cores
VX_CFG_NUM_WARPS = 4          # Warps per core
VX_CFG_NUM_THREADS = 4        # Threads per warp
VX_CFG_ISSUE_WIDTH = 4        # Pipeline issue width
VX_CFG_EXT_TCU_ENABLE = true  # Tensor core unit
VX_CFG_EXT_DXA_ENABLE = true  # Data transfer accelerator
VX_CFG_TCU_WGMMA_ENABLE = true # Warp-group MMA
```

After editing, re-run `../configure` from your build directory to propagate changes.

## Compiler Toolchain

GRXGPU uses **[VOLT](https://github.com/vortexgpgpu/Volt)** (Vortex-Optimized Lightweight Toolchain), an LLVM-based SIMT compiler. See the [VOLT repo](https://github.com/vortexgpgpu/Volt) for build instructions.

## Documentation

- [Design proposals](docs/proposals/) — architectural proposals and experiment results
- [Reply to grxcp team](docs/reply_to_grxgpu_team.md) — multi-core bug analysis
- [Debugging guide](docs/debugging.md) — runtime trace and debug options
- [Simulation backends](docs/simulation.md) — SimX, RTL, FPGA

## Citation

If you use GRXGPU in your research, please cite the original Vortex paper:

```
@inproceedings{10.1145/3466752.3480128,
  author = {Tine, Blaise and Yalamarthy, Krishna Praveen and Elsabbagh, Fares and Hyesoon, Kim},
  title = {Vortex: Extending the RISC-V ISA for GPGPU and 3D-Graphics},
  year = {2021},
  publisher = {Association for Computing Machinery},
  doi = {10.1145/3466752.3480128},
}
```

## License

Apache License 2.0
