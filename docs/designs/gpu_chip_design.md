# Vortex G100 — NVIDIA-Style GPU Chip Design with CUDA-Style Integration

**Status:** Chip-level design specification (paper design / implementation target).
**Scope:** the full GPU chip — compute hierarchy, SM microarchitecture, SIMT
execution, memory hierarchy, interconnect, and the CUDA-style programming
model — for a new device codenamed **G100**.
**Baseline reference:** the compute/memory blueprint of NVIDIA's Volta →
Hopper generation (V100 / A100 / H100) as summarized in the NAS KB article
*Basics on NVIDIA GPU Hardware Architecture*
([Article ID 704](https://www.nas.nasa.gov/hecc/support/kb/entry/704/), last
updated 2025-09-25).
**Implementation substrate:** the Vortex RISC-V GPGPU stack. Wherever the
design maps onto an existing Vortex block (KMU, CTA dispatch, TCU, cache
hierarchy, AMO, clusters, DXA), it is cited; genuinely new capability is
flagged as **new**.
**Related docs:** [microarchitecture](microarchitecture.md),
[cta_clustering_and_dispatch](cta_clustering_and_dispatch.md),
[tensor_core_wgmma_engine](tensor_core_wgmma_engine.md),
[cache_subsystem](cache_subsystem.md),
[command_processor](command_processor.md),
[mmu_optimization_proposal](../proposals/mmu_optimization_proposal.md).

---

## 1. Motivation and design principles

The task: design a GPU chip that follows the NVIDIA hardware blueprint —
thousands of simple scalar cores organized into SMs, warp-based SIMT
execution, a register-heavy per-SM datapath, a combined L1/shared memory, a
shared L2, high-bandwidth HBM, and a high-bandwidth chip-to-chip
interconnect — with a CUDA-style programming model (threads → blocks →
grids, shared memory, barriers, tensor cores), implemented on the open
Vortex stack so the design is simulatable, synthesizable, and testable today.

The article's key observations that drive every decision below:

1. **Throughput over latency.** GPUs have only two cache levels (L1/L2), no
   L3, and hide memory latency with massive thread-level parallelism
   (asynchronous SIMT), not with out-of-order execution.
2. **CUDA cores are simple, scalar, in-order.** Parallelism comes from
   thousands of cores, not from complex per-core logic.
3. **The warp (32 threads) is the unit of scheduling.** A warp executes one
   instruction across 32 lanes — the GPU analogue of a CPU SIMD vector.
4. **The thread block is the unit of co-residency and cooperation**: one
   block per SM, synchronized by barriers, sharing a low-latency shared
   memory.
5. **Registers are the biggest on-chip store** (256 KB/SM — larger than
   L1/shared memory on V100/A100), enabling many resident threads.
6. **Tensor cores** accelerate D=A×B+C with mixed precision, at 2–8× the
   FP32 rate.

Design principles for G100:

- **Configurability first.** Every structural choice is a
  `VX_config.toml` knob so the same RTL spans a tiny FPGA part and the
  flagship ASIC configuration.
- **One kernel at a time per device** (as today): single global VA space,
  single grid walk, no per-queue context — the CUDA-style model without the
  multi-process machinery.
- **Reuse the Vortex ISA and pipeline**; add only what the NVIDIA blueprint
  requires (per-SM unified L1/shared carve-out at H100 scale, HBM3e, NVLink).
- **SimX is the timing model; RTL must match it cycle-for-cycle** (project
  `model_parity` rule).

---

## 2. Design targets — comparison with V100 / A100 / H100

Flagship configuration (see §11 for the config table). Numbers for
V100/A100/H100 are from the article.

| Resource | V100 | A100 | H100 (GH200) | **G100 (target)** |
|---|---|---|---|---|
| Streaming Multiprocessors | 80 | 108 | 132 | **128** (8 clusters × 16 cores) |
| FP32 CUDA cores / SM | 64 | 64 | 128 | **128** |
| FP64 CUDA cores / SM | 32 | 32 | 64 | **64** |
| Tensor cores / SM (gen) | 8 (1st) | 4 (3rd) | 4 (4th) | **4 (5th)** |
| Registers / SM | 65,536 (256 KB) | 65,536 (256 KB) | 65,536 (256 KB) | **65,536 (256 KB)** |
| Combined L1/shared / SM | 128 KB (96 KB smem) | 192 KB (164 KB smem) | 256 KB (228 KB smem) | **256 KB (228 KB smem)** |
| L2 (shared) | 6,144 KB | 40 MB | 60 MB | **64 MB** (8 × 8 MB slices) |
| Device memory | HBM2 40 GB, 900 GB/s | HBM2e 80 GB, ~2 TB/s | HBM3 96 GB, 3.35–4 TB/s | **HBM3e 128 GB, ~6.4 TB/s** |
| NVLink | 6× 300 GB/s | 12× 600 GB/s | 18× 900 GB/s | **18× ~1.8 TB/s** |
| Host interface | PCIe 3.0 x16 (32 GB/s) | PCIe 4.0 x16 (64 GB/s) | PCIe 5.0 x16 (128 GB/s) / NVLink-C2C (900 GB/s) | **PCIe 6.0 x16 (256 GB/s) or NVLink-C2C** |
| Clock | 1530 MHz | 1410 MHz | 1980 MHz | **~2.0 GHz** |
| Compute capability | 7.0 | 8.0 | 9.0 | **10.0 (design target)** |

The G100 sits at H100-class scale with a next-generation memory/interconnect
budget: 128 SMs at 2.0 GHz (vs 132 at 1.98 GHz), HBM3e at ~2× H100's
bandwidth, and NVLink-class chip-to-chip bandwidth.

---

## 3. Chip-level architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              G100 die                                       │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Cluster 0   │  │  Cluster 1   │  │  Cluster 2   │  │  Cluster 3   │    │
│  │ (GPC-style)  │  │              │  │              │  │              │    │
│  │  16 cores    │  │  16 cores    │  │  16 cores    │  │  16 cores    │    │
│  │  + SMEM/L1   │  │  + SMEM/L1   │  │  + SMEM/L1   │  │  + SMEM/L1   │    │
│  │  + RASTER    │  │  + TEX/OM    │  │  + RTU       │  │  + TEX/OM    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│         └───────────── crossbar fabric (L2 interconnect) ─────┘            │
│                              │          │                                  │
│            ┌─────────────┐   │          │   ┌─────────────┐                │
│            │ L2 slice 0  │◄──┘          └──►│ L2 slice 3  │                │
│            │ (8 MB)      │   ┌───────────┐  │ (8 MB)      │                │
│            └─────────────┘   │ L2 slice  │  └─────────────┘                │
│            ┌─────────────┐   │ 1,2 (8MB) │  ┌─────────────┐                │
│            │ L2 slice 4  │   └───────────┘  │ L2 slice 7  │                │
│            └─────────────┘                  └─────────────┘                │
│    ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│    │ HBM3e ctrl │  │ HBM3e ctrl │  │ HBM3e ctrl │  │ HBM3e ctrl │   (6–8    │
│    │  (stack)   │  │  (stack)   │  │  (stack)   │  │  (stack)   │   stacks)│
│    └────────────┘  └────────────┘  └────────────┘  └────────────┘          │
│                                                                             │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐         │
│  │  NVLink    │   │  NVLink    │   │  NVLink    │   │  NVLink    │  18 links│
│  │  PHY/ctrl  │   │  PHY/ctrl  │   │  PHY/ctrl  │   │  PHY/ctrl  │         │
│  └────────────┘   └────────────┘   └────────────┘   └────────────┘         │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Host interface: PCIe 6.0 x16 core + NVLink-C2C (Grace-style CPU) │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────┘
```

- **Cluster = GPC.** Each cluster is an independent "GPU within a GPU":
  its own set of cores, its own L2 slice partition, its own graphics /
  ray-tracing fixed-function blocks (Vortex already has RASTER/TEX/OM/RTU
  per-socket units). Clusters are the unit of partitioning for the L2 and
  the NVLink/HBM controllers.
- **Crossbar fabric** interconnects clusters to L2 slices (Vortex's
  `VX_mem_arb` fabric scales to this topology; **new**: a 2D mesh option for
  >8 clusters).
- **L2 is partitioned into slices** (8 × 8 MB for the flagship), each a
  banked, sectored, write-back cache with its own MSHRs and AMO support
  (Vortex's L3/LLC machinery generalizes to this; see
  [cache_subsystem](cache_subsystem.md) and
  [multicache_amo_coherence](multicache_amo_coherence.md)).
- **HBM3e controllers** at the die edge; **NVLink PHYs** at the corners;
  **host interface** block on one edge.

---

## 4. Compute hierarchy: GPU → cluster → core (SM)

The article's hierarchy (GPU → SM → CUDA/Tensor cores) maps onto Vortex's
hierarchy (processor → cluster → socket → core):

| NVIDIA term | G100 / Vortex term | Notes |
|---|---|---|
| GPU / device / coprocessor | GPU / processor | PCIe device; 1 GPU per node (or N via NVLink) |
| GPC (graphics processing cluster) | **Cluster** (`VX_CFG_NUM_CLUSTERS`) | shares L2 slice; own fixed-function units |
| SM (streaming multiprocessor) | **Core** (`VX_CFG_NUM_CORES`) | executes one thread block (CTA) at a time |
| SM sub-partition (H100) | **Socket** (`VX_CFG_SOCKET_SIZE`) | group of cores sharing an L1 (Vortex's socket = L1-sharing group) |
| CUDA core (FP32/FP64 lane) | **ALU / FPU lane** | scalar, in-order, no private cache |
| Tensor core | **TCU** (tensor core unit) | WGMMA engine, see [tensor_core_wgmma_engine](tensor_core_wgmma_engine.md) |
| Warp scheduler | **Warp scheduler** in `VX_scheduler` | one per SM partition |
| Thread block / CTA | **CTA** (`VX_cta_dispatch`) | fixed-stride LMEM slot, see [cta_clustering_and_dispatch](cta_clustering_and_dispatch.md) |
| Thread block cluster | **CTA cluster** (`CLUSTER_DIM_*` DCRs) | DSMEM via DXA multicast |
| Grid | **Grid walk** in the KMU | DCR-programmed |

Total SMs = `VX_CFG_NUM_CORES × VX_CFG_NUM_CLUSTERS`
(`VX_CSR_NUM_CORES` reports exactly this product).

---

## 5. SM (Streaming Multiprocessor) design

Flagship SM: **128 FP32 + 64 FP64 + 4 tensor cores + 4 LD/ST units**, 4 warp
schedulers, 256 KB registers, 256 KB combined L1/shared memory, 64 resident
warps (2,048 threads) target.

```
                        ┌────────────────── SM (core) ──────────────────┐
                        │                                                │
   warp schedulers ───► │  Partition 0    Partition 1    Part. 2  Part. 3│
   (4 × 1 instr/cyc)    │  ┌──────────┐  ┌──────────┐  ┌──────┐ ┌──────┐ │
                        │  │32 FP32   │  │32 FP32   │  │ ...  │ │ ...  │ │
                        │  │16 FP64   │  │16 FP64   │  │      │ │      │ │
                        │  │1 TC      │  │1 TC      │  │1 TC  │ │1 TC  │ │
                        │  │1 LSU     │  │1 LSU     │  │1 LSU │ │1 LSU │ │
                        │  │1 SFU     │  │1 SFU     │  │1 SFU │ │1 SFU │ │
                        │  └────┬─────┘  └────┬─────┘  └──┬───┘ └──┬───┘ │
                        │       │             │           │        │      │
                        │  ┌────▼─────────────▼───────────▼────────▼───┐  │
                        │  │  Register file: 65,536 × 32-bit (256 KB)  │  │
                        │  │  4 GPR banks, 2 VGPR banks                │  │
                        │  └───────────────────────────────────────────┘  │
                        │  ┌───────────────────────────────────────────┐  │
                        │  │  Combined L1/shared memory (256 KB)       │  │
                        │  │  carve-out: 0–228 KB shared, rest L1      │  │
                        │  └───────────────────────────────────────────┘  │
                        └────────────────────────────────────────────────┘
```

### 5.1 Warp scheduling

- **4 warp schedulers**, one per SM partition, each issuing **1 instruction
  per cycle** (4 instr/cycle/SM sustained). This is the H100 model and the
  default `VX_CFG_ISSUE_WIDTH` scaling target.
- Scheduler state per warp: PC, active thread mask, IPDOM stack for
  divergence reconvergence (`SPLIT`/`JOIN`/`PRED`), scoreboard, inflight
  tracker — all present in `VX_scheduler` today.
- Round-robin / oldest-first arbitration among ready warps; the 64 resident
  warps give each scheduler 16 warps to hide latency.

### 5.2 Execution units

| Unit | Lanes (flagship) | Notes |
|---|---|---|
| ALU (INT) | 128 (shared with FP32) | integer, logic, branch; H100-style FP32/INT dual-use lanes |
| FPU (FP32) | 128 | 32/partition; FMA, IEEE 754 single precision |
| FPU (FP64) | 64 | 2:1 ratio to FP32 (H100-class) |
| LSU | 4 × 32 lanes = 128 B/cycle | coalesced warp loads/stores; shared with TCU metadata path |
| SFU | 4 | warp control, CSRs, transcendentals |
| TCU | 4 tensor cores | see §10 |

The 6-stage pipeline (Schedule → Fetch → Decode → Issue → Execute →
Commit) is unchanged from [microarchitecture](microarchitecture.md); the
G100 work is in unit width, register/smem capacity, and the carve-out.

### 5.3 Registers

- 65,536 × 32-bit registers (256 KB) per SM — **larger than L1/shared**,
  exactly as the article stresses for V100/A100.
- 4 GPR banks + 2 VGPR banks (`VX_CFG_NUM_GPR_BANKS=4`,
  `VX_CFG_NUM_VGPR_BANKS=2`) for multi-port operand collection.
- Register allocation is per-thread and private; occupancy is bounded by
  registers/thread (compiler-driven, as in CUDA).

### 5.4 Combined L1/shared memory

- **256 KB combined L1 data cache + shared memory** per SM, with the
  application-configurable carve-out: **0–228 KB shared, remainder L1**
  (H100 numbers). Static shared memory is capped at 48 KB; above that,
  dynamic shared memory (the article's compatibility rule).
- **new vs. today:** Vortex currently has a fixed per-core LMEM (local
  memory) plus a separate dcache. G100 introduces the **unified carve-out**
  at H100 scale, with the shared-memory share backed by the LMEM port and
  the cache share by the dcache port, partitioned at kernel launch (see
  §11).
- Bank-conflict-free access for 32-thread warps; 128-byte L1 line size (a
  full warp's worth of data — the article's L1 line definition).

### 5.5 Occupancy

Resident CTAs per SM = min over the three resource bounds:

```
CTAs/SM = min( floor(warps_available / warps_per_CTA),
               floor(registers / (registers_per_thread × threads_per_CTA)),
               floor(smem / smem_per_CTA) )
```

With 64 warps, 256 KB registers, 228 KB smem: a 256-thread (8-warp) CTA with
32 regs/thread and 32 KB smem fits 8 CTAs/SM — 2,048 resident threads, the
latency-hiding engine the article describes.

---

## 6. SIMT execution: warps, divergence, barriers

- **Warp = 32 threads** (`VX_CFG_NUM_THREADS=32` flagship; configurable
  1/2/4/8/16/32). 1 warp instruction = 32 scalar ops across the lanes — the
  GPU analogue of a CPU SIMD vector (xmm/ymm/zmm on 4/8/16 elements), per
  the article.
- **Divergence**: `SPLIT` pushes the reconvergence state onto the IPDOM
  stack; `JOIN` pops it; `PRED` predicates lanes. This is NVIDIA's
  reconvergence-stack model, already in the Vortex ISA.
- **Barriers**: `BAR id,count` stalls a warp until `count` warps reach the
  barrier. Per-SM barriers (`VX_CFG_NUM_BARRIERS=8`, `MAX_BAR_EVENTS=32`),
  plus a **global barrier** across cores (`VX_gbar_unit`) — the substrate
  for CUDA cooperative `grid.sync()`.
- **Launch**: `WSPAWN count, addr` activates `count` warps at `addr`;
  `TMC` sets the initial thread mask. A CTA is expanded into warps by
  `VX_cta_dispatch` (one warp/cycle) and its per-lane TIDs are precomputed
  by the TID ripple pipeline.
- **Block size rule**: thread blocks should be a multiple of 32 (warp
  scheduling granularity); 256 is the common choice — enforced by the
  runtime's launch validation.

---

## 7. Memory hierarchy

The article's levels, with G100 targets. Latencies are approximations and
scale with the article's measured numbers.

| Level | Size (flagship) | Latency (target) | Notes |
|---|---|---|---|
| Registers | 256 KB/SM | 1–2 cyc | private to thread; 4 B/reg |
| Shared memory | 0–228 KB/SM | ~20–30 cyc | per-block, low-latency cooperation |
| L1 data cache | 256 KB/SM (minus smem) | ~20–30 cyc | 128 B lines; shared by SM lanes |
| L2 | 64 MB (chip) | ~200 cyc | shared by all SMs; AMO point; sectored |
| HBM3e (global/local/const/texture) | 128 GB | 200–1000 cyc (~100–500 ns) | off-chip; ~6.4 TB/s |

Bandwidth chain (per SM): 128 B/cyc L1 → 64 B/cyc/partition L2 → HBM3e
aggregate ~6.4 TB/s. Latency is hidden by 2,048 resident threads/SM, not by
out-of-order execution — the article's central point.

### 7.1 Memory spaces (CUDA-style)

| CUDA space | G100 implementation |
|---|---|
| `register` | per-thread register file |
| `__shared__` | LMEM carve-out; DXA multicast for cluster fills (DSMEM) |
| `global` | HBM3e via L2; read/write, cross-block |
| `local` | per-thread spill space (up to 512 KB/thread) in device memory |
| `constant` | 64 KB read-only, broadcast; constant cache path |
| `texture` | TEX units + TCACHE (already in Vortex) |

### 7.2 Virtual memory

- Single global VA space, one page table per device, SATP programmed once
  at init — CUDA-unified-memory-style SVM (see the VM hierarchy proposal).
- SV32 (RV32) / SV39 (RV64); TLB hierarchy (L1 per core → L2 per cluster →
  L3 chip-wide, centralized PTW) per
  [mmu_optimization_proposal](../proposals/mmu_optimization_proposal.md).
- **new**: peer-address decoding for NVLink remote memory (see §8).

---

## 8. Interconnect and host interface

### 8.1 NVLink (GPU-to-GPU and C2C)

- **18 NVLink 4.0/5.0 links**, ~1.8 TB/s bidirectional aggregate — the
  article's progression (6/12/18 links for V100/A100/H100) continues.
- **NVLink-C2C** (chip-to-chip, Grace-Hopper style): 900 GB/s bidirectional
  coherent CPU attach for a GH200-like superchip.
- **new**: NVLink transport/PHY RTL is not in Vortex today; the design
  specifies a link layer (packet framing, credit flow control, remote
  atomic) and a memory-side adapter that maps remote addresses into the L2
  fabric. FPGA prototype uses the U55C HBM + high-speed transceivers as a
  stand-in.

### 8.2 Host interface

- PCIe 6.0 x16 (~256 GB/s bidirectional) for the discrete form factor, or
  NVLink-C2C for the superchip form factor — mirroring the GH200's two
  attach modes.
- Host DMA path via the command processor (`VX_cp`), untranslated on the
  host side, translated through the device TLB hierarchy on the device side
  (per the VM proposal's CP/DMA split).

---

## 9. CUDA-style programming model integration

The full CUDA-style stack maps onto Vortex software and hardware today:

| CUDA concept | G100 / Vortex implementation |
|---|---|
| `kernel<<<grid, block, smem, stream>>>(...)` | runtime queue → command processor → DCRs → KMU grid walk |
| `threadIdx/blockIdx/blockDim/gridDim` | CTA CSRs (`VX_CSR_CTA_*`) + TID ripple pipeline |
| `__syncthreads()` | `BAR` |
| `grid.sync()` (cooperative launch) | global barrier (`VX_gbar_unit`) |
| `__shared__` | LMEM carve-out |
| thread block clusters / DSMEM | `CLUSTER_DIM_{X,Y,Z}` DCRs → consecutive LMEM slots → DXA multicast |
| WMMA / WGMMA, tensor cores | TCU (`vx_tensor.h`, `wgmma_context`) |
| `atomicAdd` etc. | AMO unit at the LLC |
| `cudaMalloc` / unified memory | single VA space, SVM |
| `cudaStreams` | hardware queues / command processor |
| warp primitives (`__shfl`, `__ballot`) | warp-level ops via thread mask / TMC |
| `cudaMemcpyAsync` | DXA async copy + multicast |

### 9.1 Kernel launch sequence

1. Host enqueues a kernel command (grid dims, block dims, smem size, arg
   pointer, stream) into a hardware queue.
2. The **command processor** (`VX_cp`) decodes it and writes DCRs:
   `GRID_DIM_{X,Y,Z}`, `BLOCK_DIM_{X,Y,Z}`, `CLUSTER_DIM_{X,Y,Z}`, smem
   carve-out, entry point, param pointer.
3. The **KMU** walks the grid (two-level nested for clusters) and emits one
   `kmu_req_t` per CTA, with cluster members contiguous in dispatch order.
4. `VX_cta_dispatch` admits each CTA into a **fixed-stride LMEM slot**,
   expands it into warps, and precomputes per-lane TIDs.
5. Warps activate via `WSPAWN`, execute the kernel body, and retire; the
   dispatcher reclaims the slot out-of-order when the last warp exits.
6. Completion reports back to the host through the command processor.

### 9.2 Software stack

The same CUDA-style model is exposed as OpenCL 1.2, HIP (chipStar), and
Vulkan — so "CUDA-style integration" is delivered without a proprietary
compiler: the VOLT LLVM toolchain lowers the kernel language to the Vortex
RISC-V ISA extension (TMC/WSPAWN/SPLIT/JOIN/PRED/BAR, TCU).

---

## 10. Tensor cores

- **4 fifth-generation tensor cores per SM** (up from 8×1st-gen V100,
  4×3rd-gen A100, 4×4th-gen H100).
- Each core: **512 FP16 FMA/clock** → 2,048 FMA/clock/SM (4,096 FLOP/clock/
  SM) — 2× the per-SM FP16 rate the article cites for A100.
- Formats: FP16, BF16, TF32, FP64, FP8 (e4m3), INT8/INT4, and block-scaled
  MX (mxfp8/mxfp4) — the Vortex TCU already implements these format paths
  (`VX_CFG_TCU_*_ENABLE`), with **new** FP8/TF32/FP64 enabled in the
  flagship config.
- WGMMA warpgroup MMA with k-major/block-major shared-memory descriptors,
  2:4 structured sparsity (2× throughput), and the lockstep single-CTA
  gate — per [tensor_core_wgmma_engine](tensor_core_wgmma_engine.md).
- Peak tensor throughput: see §12.

---

## 11. Configurability

Every structural choice is a knob so the same RTL spans the FPGA prototype
and the flagship ASIC. Flagship values in bold.

The flagship preset is captured as a commented block at the top of
[VX_config.toml](../../VX_config.toml) and applied at build time via
`CONFIGS` overrides (the repo default stays the small FPGA/simulation
baseline). Verified to resolve with `ci/gen_config.py --cflags`.

| Design decision | Config key | Flagship / notes |
|---|---|---|
| Clusters (GPCs) | `VX_CFG_NUM_CLUSTERS` | **8** (power of 2) |
| Cores per cluster (SMs) | `VX_CFG_NUM_CORES` | **16** → 128 SMs total |
| Cores per L1-sharing socket | `VX_CFG_SOCKET_SIZE` | **4** |
| Warps per core (resident) | `VX_CFG_NUM_WARPS` | **64** (16/scheduler) |
| Threads per warp | `VX_CFG_NUM_THREADS` | **32** (CUDA-compatible) |
| Issue width | `VX_CFG_ISSUE_WIDTH` | derived from `NUM_WARPS`; **4** schedulers |
| Barriers | `VX_CFG_NUM_BARRIERS` / `MAX_BAR_EVENTS` | **8** / **32** |
| GPR banks / VGPR banks | `VX_CFG_NUM_GPR_BANKS` / `NUM_VGPR_BANKS` | **4** / **2** |
| Register file | (per-SM, fixed) | 65,536 × 32-bit = 256 KB |
| L1/shared carve-out | **new**: `VX_CFG_LMEM_LOG_SIZE` + carve-out DCR | 256 KB combined; smem 0–228 KB |
| L2 size / ways / banks | `VX_CFG_L2_*` | **8 MB per cluster × 8 = 64 MB total**, 8-way |
| L3 (optional) | `VX_CFG_L3_*` | off in flagship (L2 = LLC) |
| Device memory | **new**: HBM3e controller | 128 GB, ~6.4 TB/s |
| NVLink | **new**: `VX_CFG_NV_ENABLE`, links | 18 links, ~1.8 TB/s |
| TCU formats | `VX_CFG_TCU_{FP16,BF16,TF32,FP8,INT8,MX,SPARSE,WGMMA}_ENABLE` | all on in flagship |

---

## 12. Performance model

At 2.0 GHz, 128 SMs. FLOP counts are FMA×2.

| Precision | Per-SM FLOPS/clk | Peak |
|---|---|---|
| FP64 | 64 × 2 = 128 | 128 × 128 × 2.0e9 = **32.8 TFLOPS** |
| FP32 | 128 × 2 = 256 | 128 × 256 × 2.0e9 = **65.5 TFLOPS** |
| TF32 (tensor) | 4096/2 | **524 TFLOPS** |
| FP16 (tensor, dense) | 4096 | **1.05 PFLOPS** |
| FP16 (tensor, 2:4 sparse) | 8192 | **2.1 PFLOPS** |
| FP8 (tensor, dense) | 8192 | **2.1 PFLOPS** |
| FP8 (tensor, 2:4 sparse) | 16384 | **4.2 PFLOPS** |
| INT8 (tensor) | 8192 | **2.1 POPS** |

Memory/interconnect bandwidth: HBM3e **~6.4 TB/s**, NVLink **~1.8 TB/s**
bidirectional, PCIe 6.0 x16 **256 GB/s** bidirectional.

Arithmetic intensity (FP16 dense vs HBM): 1.05e15 / 6.4e12 ≈ **164 FLOP/B** —
a memory-bound ceiling the tensor cores will hit on dense GEMMs, which is
exactly why the HBM3e bandwidth budget matters.

---

## 13. Implementation roadmap

Phases land on the Vortex stack; each phase keeps SimX↔RTL parity green
(project `model_parity` rule) and ends with regression passing.

- **Phase 0 — Config sweep (SimX).** Add flagship config to
  `VX_config.toml`; validate the execution model at NUM_THREADS=32,
  NUM_WARPS=64, 8×16 topology in SimX before touching RTL.
- **Phase 1 — SM at H100 scale.** 128 FP32 + 64 FP64 lanes, 4-way issue,
  64 warps; RTL + SimX parity on `sgemm`/`vecadd`.
- **Phase 2 — Unified L1/shared carve-out.** Per-kernel smem/L1 partition
  DCR; `__shared__` beyond 48 KB via dynamic allocation; DXA multicast
  fills.
- **Phase 3 — Memory hierarchy.** 8-cluster × 8 MB L2 slices; crossbar
  fabric; AMO at the LLC; TLB hierarchy (per VM proposal).
- **Phase 4 — Tensor cores.** Enable FP8/TF32/FP64 + sparsity + WGMMA in
  the flagship TCU config; parity on `sgemm_tcu_wg`/`sgemm_tcu_wg_dxa_mcast`.
- **Phase 5 — HBM3e + NVLink.** Memory controller, NVLink link/transport
  layer, remote-address decode into the L2 fabric; FPGA prototype on U55C
  (HBM + high-speed transceivers).
- **Phase 6 — Host interface.** PCIe 6.0 core and/or NVLink-C2C attach;
  coherent host-memory path (SVM).
- **Phase 7 — ASIC.** Synopsys flow (SYNOPSYS=1), PPA analysis per
  [synthesis_analysis](../synthesis_analysis.md), tape-out prep.

---

## 14. Verification plan

- **Parity**: every phase adds or extends `model_parity` cases (SimX vs
  rtlsim: exact retired-instruction match, cycle agreement within tolerance)
  — the project's hard gate.
- **RTL verification** on the `xrt` path (the canonical RTL path), not just
  rtlsim.
- **Microbenchmarks**: `sgemm_tcu`, `sgemm_tcu_wg_dxa_mcast`, `vecadd`,
  plus new bandwidth (`hbm_bw`), cluster-DSMEM (`cluster_peer`), and
  multi-GPU (`nvlink_ring`) tests.
- **Perf gates**: roofline analysis (`perf/roofline.py`) with golden
  baselines; never hand-edit baselines.
- **Synthesis gates**: U55C closure at target frequency; PPA report per
  phase.

---

## 15. Open questions

1. **NVLink on FPGA**: pin budget and transceiver count on the U55C
   prototype — may force a reduced link count (e.g., 4 links) for bring-up.
2. **L2 slice count vs crossbar cost**: 8 slices is the flagship; the mesh
  option for >8 clusters needs a fabric-area study.
3. **smem carve-out granularity**: 1 KB steps vs 8 KB steps — affects
  allocation efficiency and the LMEM/dcache port split.
4. **DSMEM across NVLink**: peer SMEM access between GPUs (not just within
  a cluster) is a follow-on; requires remote-atomic support in the L2.
5. **Register file banking**: 4 GPR banks may bottleneck 4-way issue at
  2 GHz; a 6–8 bank split is the fallback.

---

## 16. References

- NAS KB — *Basics on NVIDIA GPU Hardware Architecture*,
  <https://www.nas.nasa.gov/hecc/support/kb/entry/704/> (the V100/A100/H100
  numbers cited throughout).
- NVIDIA *Tesla V100 GPU Architecture* white paper.
- NVIDIA *A100 Tensor Core GPU Architecture* white paper.
- NVIDIA *H100 Tensor Core GPU Architecture* white paper.
- Vortex: *Extending the RISC-V ISA for GPGPU and 3D-Graphics* (MICRO'21).
- Vortex design docs: [microarchitecture](microarchitecture.md),
  [tensor_core_wgmma_engine](tensor_core_wgmma_engine.md),
  [cta_clustering_and_dispatch](cta_clustering_and_dispatch.md),
  [cache_subsystem](cache_subsystem.md),
  [command_processor](command_processor.md).
