// Copyright © 2019-2023
// Licensed under the Apache License, Version 2.0.

// ============================================================================
// Verilator integration test for VX_cp_core (full CP).
//
// Wires the three CP interfaces against synthetic models:
//   - AXI-Lite slave host: drives W/AW + AR transactions for control.
//   - AXI4 master upstream: 16 KiB byte-addressed memory model (host
//     pinned ring + completion slot live here).
//   - gpu_if (Vortex side): tiny FSM that responds to gpu.start by
//     pulsing gpu.busy for a few cycles.
//
// End-to-end happy-path sequence:
//   1. Seed one profiled NOP on the final physical ring line and a second
//      at ring offset zero, with padding-only cache lines before the boundary.
//   2. Program regs:
//        Q_RING_BASE_LO/HI = ring_base
//        Q_CMPL_ADDR_LO/HI = cmpl_slot
//        Q_RING_SIZE_LOG2  = 12 (4 KiB)
//        Q_CONTROL.enable  = 1, Q_CONTROL.profile = 1
//        CP_CTRL.enable_global = 1
//   3. Ring the doorbell with a monotonic tail past the physical ring end.
//   4. Watch both commands retire and the head advance across the wrap.
//   5. Verify the completion sequence and coherent head snapshot.
//
// NOP retires without bidding for a resource; this exercises regfile → fetch
// → unpack → engine → completion and host-visible head reporting.
// ============================================================================

#include "vl_simulator.h"
#include "VVX_cp_core_top.h"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#ifndef TRACE_START_TIME
#define TRACE_START_TIME 0ull
#endif
#ifndef TRACE_STOP_TIME
#define TRACE_STOP_TIME -1ull
#endif

static uint64_t timestamp = 0;
static bool     trace_en  = false;
double sc_time_stamp() { return timestamp; }
bool   sim_trace_enabled() { return trace_en; }
void   sim_trace_enable(bool e) { trace_en = e; }

#define EXPECT(cond, msg) do { \
    if (!(cond)) { \
        std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, msg); \
        std::exit(1); \
    } \
} while (0)

// ---- cmd_t pack (header at MSB word, profile_slot at LSB words) ----
static constexpr int F_PROFILE_BIT = 0;
static void emit_nop_profiled(uint8_t* cl, uint64_t profile_slot) {
    std::memset(cl, 0, 64);
    cl[0] = 0x00;                // opcode = NOP
    cl[1] = 1u << F_PROFILE_BIT; // flags  = F_PROFILE (so it's not padding)
    // NOP profiled size = 12 B; profile_slot at tail (offset 4..11)
    for (int i = 0; i < 8; ++i) cl[4 + i] = (uint8_t)(profile_slot >> (8*i));
}

// ============================================================================
// Synthetic AXI4 slave (memory model).
// ============================================================================
struct AxiSlave {
    static constexpr uint64_t MEM_BASE = 0x1000;
    static constexpr int      MEM_SIZE = 16 * 1024;
    uint8_t mem[MEM_SIZE] = {0};

    bool         r_inflight = false;
    uint64_t     r_addr     = 0;
    uint8_t      r_id       = 0;

    bool         aw_taken   = false;
    uint64_t     aw_addr    = 0;
    uint8_t      aw_id      = 0;
    bool         b_pending  = false;
    uint8_t      b_id       = 0;

    void mem_write_cl(uint64_t addr, const uint8_t* src) {
        for (int i = 0; i < 64; ++i) {
            int64_t a = (int64_t)addr - (int64_t)MEM_BASE + i;
            if (a >= 0 && a < MEM_SIZE) mem[a] = src[i];
        }
    }
    void mem_read_cl(uint64_t addr, uint32_t* dst) const {
        for (int w = 0; w < 16; ++w) {
            uint32_t v = 0;
            for (int b = 0; b < 4; ++b) {
                int64_t a = (int64_t)addr - (int64_t)MEM_BASE + w*4 + b;
                if (a >= 0 && a < MEM_SIZE) v |= (uint32_t)mem[a] << (8 * b);
            }
            dst[w] = v;
        }
    }
    uint64_t mem_read64(uint64_t addr) const {
        uint64_t v = 0;
        for (int i = 0; i < 8; ++i) {
            int64_t a = (int64_t)addr - (int64_t)MEM_BASE + i;
            if (a >= 0 && a < MEM_SIZE) v |= (uint64_t)mem[a] << (8 * i);
        }
        return v;
    }

    template <typename T>
    void comb_drive(T* top) {
        top->m_arready = !r_inflight;
        top->m_rvalid = r_inflight;
        top->m_rid    = r_id;
        top->m_rlast  = 1;
        top->m_rresp  = 0;
        if (r_inflight) mem_read_cl(r_addr, top->m_rdata);

        top->m_awready = !aw_taken;
        top->m_wready  = aw_taken && !b_pending;
        top->m_bvalid  = b_pending;
        top->m_bid     = b_id;
        top->m_bresp   = 0;
    }
    template <typename T>
    void posedge_update(T* top) {
        if (top->m_arvalid && top->m_arready) {
            r_inflight = true; r_addr = top->m_araddr; r_id = top->m_arid;
        } else if (r_inflight && top->m_rvalid && top->m_rready) {
            r_inflight = false;
        }
        if (top->m_awvalid && top->m_awready) {
            aw_taken = true; aw_addr = top->m_awaddr; aw_id = top->m_awid;
        }
        if (aw_taken && top->m_wvalid && top->m_wready) {
            // Write low 64 b of wdata at aw_addr.
            uint64_t v = ((uint64_t)top->m_wdata[1] << 32) | top->m_wdata[0];
            for (int i = 0; i < 8; ++i) {
                int64_t a = (int64_t)aw_addr - (int64_t)MEM_BASE + i;
                if (a >= 0 && a < MEM_SIZE) mem[a] = (uint8_t)(v >> (8 * i));
            }
            aw_taken = false; b_pending = true; b_id = aw_id;
        }
        if (b_pending && top->m_bvalid && top->m_bready) b_pending = false;
    }
};

// ============================================================================
// Synthetic gpu_if model. Pulses dcr_req_ready always; pulses busy for
// a few cycles after start. dcr_rsp is unused in this NOP test.
// ============================================================================
struct GpuModel {
    int busy_cnt = 0;
    template <typename T>
    void comb_drive(T* top) {
        top->gpu_dcr_req_ready = 1;
        top->gpu_dcr_rsp_valid = 0;
        top->gpu_dcr_rsp_data  = 0;
        top->gpu_busy = (busy_cnt > 0);
    }
    template <typename T>
    void posedge_update(T* top) {
        if (top->gpu_start) busy_cnt = 4;
        else if (busy_cnt > 0) busy_cnt--;
    }
};

template <typename T>
static void cycle(vl_simulator<T>& sim, AxiSlave& slave, GpuModel& gpu,
                  uint64_t& tick) {
    auto* top = sim.operator->();
    slave.comb_drive(top);
    gpu.comb_drive(top);
    top->eval();
    slave.comb_drive(top);
    gpu.comb_drive(top);
    top->eval();
    slave.posedge_update(top);
    gpu.posedge_update(top);
    tick = sim.step(tick, 2);
    slave.comb_drive(top);
    gpu.comb_drive(top);
    top->eval();
}

// ---- AXI-Lite W and R helpers (drive the host control plane) ----
template <typename T>
static void axil_write(vl_simulator<T>& sim, AxiSlave& slave, GpuModel& gpu,
                       uint64_t& tick, uint16_t addr, uint32_t data) {
    // Drive AW + W + bready continuously; sample bvalid each cycle.
    sim->s_awvalid = 1; sim->s_awaddr = addr;
    sim->s_wvalid  = 1; sim->s_wdata = data; sim->s_wstrb = 0xF;
    sim->s_bready  = 1;
    bool aw_done = false, w_done = false;
    for (int g = 0; g < 32; ++g) {
        cycle(sim, slave, gpu, tick);
        if (!aw_done && sim->s_awready) { aw_done = true; sim->s_awvalid = 0; }
        if (!w_done  && sim->s_wready)  { w_done  = true; sim->s_wvalid  = 0; }
        if (aw_done && w_done && sim->s_bvalid) {
            sim->s_bready = 0;
            return;
        }
    }
    EXPECT(false, "axil_write: B never asserted within 32 cycles");
}

template <typename T>
static uint32_t axil_read(vl_simulator<T>& sim, AxiSlave& slave, GpuModel& gpu,
                          uint64_t& tick, uint16_t addr) {
    // Drive AR and rready continuously; sample rvalid each cycle. When
    // rvalid + rready handshake, capture rdata and clear both.
    sim->s_arvalid = 1; sim->s_araddr = addr;
    sim->s_rready  = 1;
    bool ar_done = false;
    uint32_t captured = 0;
    for (int g = 0; g < 32; ++g) {
        cycle(sim, slave, gpu, tick);
        if (!ar_done && sim->s_arready) {
            ar_done = true;
            sim->s_arvalid = 0;
        }
        if (sim->s_rvalid) {
            captured = sim->s_rdata;
            sim->s_rready = 0;
            return captured;
        }
    }
    EXPECT(false, "axil_read: R never asserted");
    return 0;
}

// Register offsets matching VX_cp_axil_regfile.
static constexpr uint16_t CP_CTRL          = 0x000;
static constexpr uint16_t CP_DEV_CAPS      = 0x008;
static constexpr uint16_t Q0_BASE          = 0x100;
static constexpr uint16_t Q_RING_BASE_LO   = 0x00;
static constexpr uint16_t Q_RING_BASE_HI   = 0x04;
static constexpr uint16_t Q_CMPL_ADDR_LO   = 0x10;
static constexpr uint16_t Q_CMPL_ADDR_HI   = 0x14;
static constexpr uint16_t Q_RING_SIZE_LOG2 = 0x18;
static constexpr uint16_t Q_CONTROL        = 0x1C;
static constexpr uint16_t Q_TAIL_LO        = 0x20;
static constexpr uint16_t Q_TAIL_HI        = 0x24;
static constexpr uint16_t Q_SEQNUM         = 0x28;
static constexpr uint16_t Q_HEAD_SNAP_LO   = 0x34;
static constexpr uint16_t Q_HEAD_SNAP_HI   = 0x38;

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    vl_simulator<VVX_cp_core_top> sim;
    uint64_t tick = 0;
    AxiSlave slave;
    GpuModel gpu;

    // Idle inputs before reset.
    sim->s_awvalid = sim->s_wvalid = sim->s_bready = 0;
    sim->s_arvalid = sim->s_rready = 0;
    tick = sim.reset(tick);

    // Sanity: CP_DEV_CAPS readable.
    {
        uint32_t v = axil_read(sim, slave, gpu, tick, CP_DEV_CAPS);
        EXPECT((v & 0xff) == 1, "DEV_CAPS NUM_QUEUES");
    }

    // ----- Seed commands on both sides of the physical ring boundary -----
    constexpr uint64_t RING_BASE = AxiSlave::MEM_BASE;
    constexpr uint64_t RING_BYTES = 1u << 12;
    constexpr uint64_t CMPL_ADDR = AxiSlave::MEM_BASE + 0x200;
    {
        uint8_t cl[64];
        emit_nop_profiled(cl, /*profile_slot=*/0xCAFEBABEull);
        slave.mem_write_cl(RING_BASE + RING_BYTES - 64, cl);
        // The first retired command writes sequence number zero.
        for (int i = 0; i < 8; ++i)
            slave.mem[CMPL_ADDR - AxiSlave::MEM_BASE + i] = 0xFF;
    }

    // ----- Program the queue regs -----
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_RING_BASE_LO,
               (uint32_t)(RING_BASE & 0xffffffffu));
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_RING_BASE_HI,
               (uint32_t)(RING_BASE >> 32));
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_CMPL_ADDR_LO,
               (uint32_t)(CMPL_ADDR & 0xffffffffu));
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_CMPL_ADDR_HI,
               (uint32_t)(CMPL_ADDR >> 32));
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_RING_SIZE_LOG2, 12);
    // Q_CONTROL: enable=1, profile_en=1, prio=2.
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_CONTROL,
               1u | (2u << 2) | (1u << 4));
    // CP_CTRL.enable_global = 1
    axil_write(sim, slave, gpu, tick, CP_CTRL, 1);

    // Consume the padding up to the final physical line, then publish two
    // command lines spanning the end-to-start ring wrap.
    constexpr uint64_t PRE_WRAP_TAIL = RING_BYTES - 64;
    constexpr uint64_t FINAL_TAIL = RING_BYTES + 64;
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_TAIL_LO,
               (uint32_t)PRE_WRAP_TAIL);
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_TAIL_HI, 0);
    for (int g = 0; g < 1000 && sim->dbg_q0_head != PRE_WRAP_TAIL; ++g)
        cycle(sim, slave, gpu, tick);
    EXPECT(sim->dbg_q0_head == PRE_WRAP_TAIL,
           "fetch did not consume padding up to the physical ring boundary");
    EXPECT(slave.mem_read64(CMPL_ADDR) == 0xFFFFFFFFFFFFFFFFull,
           "padding before the boundary unexpectedly retired a command");
    {
        uint8_t cl[64];
        emit_nop_profiled(cl, /*profile_slot=*/0xDEADBEEFull);
        slave.mem_write_cl(RING_BASE, cl);
    }

    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_TAIL_LO,
               (uint32_t)FINAL_TAIL);
    axil_write(sim, slave, gpu, tick, Q0_BASE + Q_TAIL_HI, 0);

    // Verify the registers were programmed before waiting.
    {
        uint32_t rb_lo = axil_read(sim, slave, gpu, tick, Q0_BASE + Q_RING_BASE_LO);
        uint32_t ctrl  = axil_read(sim, slave, gpu, tick, Q0_BASE + Q_CONTROL);
        uint32_t cp    = axil_read(sim, slave, gpu, tick, CP_CTRL);
        std::fprintf(stderr, "[verify] ring_base_lo=0x%x q_ctrl=0x%x cp_ctrl=0x%x dbg_enabled=%d dbg_tail=0x%lx\n",
                     rb_lo, ctrl, cp, sim->dbg_q0_enabled, (unsigned long)sim->dbg_q0_tail);
    }

    // ----- Wait for both commands to retire across the ring wrap -----
    for (int g = 0; g < 1000 && sim->dbg_q0_head != FINAL_TAIL; ++g)
        cycle(sim, slave, gpu, tick);
    EXPECT(sim->dbg_q0_head == FINAL_TAIL,
           "consumer head did not advance monotonically across ring wrap");
    EXPECT(slave.mem_read64(CMPL_ADDR) == 1,
           "completion slot did not record the second retired command");
    EXPECT(axil_read(sim, slave, gpu, tick, Q0_BASE + Q_SEQNUM) == 2,
           "queue sequence count did not reach two after the wrapped commands");
    uint32_t head_lo = axil_read(sim, slave, gpu, tick, Q0_BASE + Q_HEAD_SNAP_LO);
    uint32_t head_hi = axil_read(sim, slave, gpu, tick, Q0_BASE + Q_HEAD_SNAP_HI);
    EXPECT((((uint64_t)head_hi << 32) | head_lo) == FINAL_TAIL,
           "head snapshot MMIO pair did not publish wrapped consumer head");
    std::printf("PASSED — CP end-to-end: wrapped two-line ring, consumer head=%llu, retired=2\n",
                (unsigned long long)FINAL_TAIL);
    return 0;
}
