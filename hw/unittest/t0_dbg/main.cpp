// Copyright © 2019-2023
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// ============================================================================
// Verilator testbench for the T0-A JTAG debug path.
//
// Drives the five JTAG pins directly, walks the TAP through reset, reads
// IDCODE/DTMCS, then uses DMI writes and SBA word accesses to load and read
// back the 256 KB test SRAM. The boot image walks a one and a zero through
// every line of the array, with an exhaustive 32-bit walk every eighth line.
// Also checks the DMI busy status, the SBA error
// codes, the timeout path (by stalling the SRAM response) and both sides of
// the memory arbiter.
// ============================================================================

#include "VVX_t0_dbg_tb_top.h"
#include "verilated.h"
#include "VX_config.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>

#ifndef T0_IMAGE_PATH
#error "T0_IMAGE_PATH must name the toolchain-built boot image"
#endif
#ifndef T0_SHORT_IMAGE_PATH
#error "T0_SHORT_IMAGE_PATH must name the short boot image"
#endif

#define EXPECT(cond, msg) do {                                      \
    if (!(cond)) {                                                  \
        std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, msg); \
        std::exit(1);                                               \
    }                                                               \
} while (0)

static VVX_t0_dbg_tb_top* dut = nullptr;

// t0_image.S partitions the array across the four lanes of the boot warp.
static_assert(VX_CFG_NUM_THREADS == 4, "t0_image.S assumes four threads per warp");

bool sim_trace_enabled() {
    return false;
}

// One core clock cycle (posedge included).
static void core_cycle() {
    dut->clk = 0;
    dut->eval();
    dut->clk = 1;
    dut->eval();
    dut->clk = 0;
    dut->eval();
}

static void core_cycles(int n) {
    for (int i = 0; i < n; ++i) core_cycle();
}

// Freezing the core clock parks a DMI request in the DTM, which is how the
// busy-status path is exercised.
static bool core_frozen = false;

static void tck_settle() {
    if (core_frozen) {
        dut->eval();
    } else {
        core_cycles(8);
    }
}

// TCK is the slow clock: hold each phase for several core cycles so the
// two-flop synchronizers and the DM have time to settle.
static int tck_cycle(int tms, int tdi) {
    dut->jtag_tck = 0;
    dut->jtag_tms = tms;
    dut->jtag_tdi = tdi;
    dut->eval();
    tck_settle();

    dut->jtag_tck = 1;
    dut->eval();
    int tdo = dut->jtag_tdo;
    tck_settle();

    dut->jtag_tck = 0;
    dut->eval();
    tck_settle();
    return tdo;
}

static const uint8_t IR_IDCODE = 0x01;
static const uint8_t IR_BYPASS = 0x00;
static const uint8_t IR_DTMCS  = 0x10;
static const uint8_t IR_DMI    = 0x11;

static const uint8_t DM_DATA0        = 0x04;
static const uint8_t DM_DMCONTROL    = 0x10;
static const uint8_t DM_DMSTATUS     = 0x11;
static const uint8_t DM_HARTINFO     = 0x12;
static const uint8_t DM_ABSTRACTCS   = 0x16;
static const uint8_t DM_COMMAND      = 0x17;
static const uint8_t DM_ABSTRACTAUTO = 0x18;
static const uint8_t DM_SBCS         = 0x38;
static const uint8_t DM_SBADDRESS0   = 0x39;
static const uint8_t DM_SBDATA0      = 0x3c;

static void tap_reset() {
    dut->jtag_trst_n = 0;
    tck_cycle(1, 0);
    tck_cycle(1, 0);
    dut->jtag_trst_n = 1;
    for (int i = 0; i < 5; ++i) tck_cycle(1, 0);
    tck_cycle(0, 0);
}

static void ir_scan(uint8_t ir) {
    tck_cycle(1, 0); // Select-DR
    tck_cycle(1, 0); // Select-IR
    tck_cycle(0, 0); // Capture-IR
    tck_cycle(0, 0); // Shift-IR
    for (int i = 0; i < 5; ++i) {
        int tms = (i == 4) ? 1 : 0;
        tck_cycle(tms, (ir >> i) & 1);
    }
    tck_cycle(1, 0); // Update-IR
    tck_cycle(0, 0); // Run-Test/Idle
}

static uint64_t dr_scan(int bits, uint64_t din) {
    tck_cycle(1, 0); // Select-DR
    tck_cycle(0, 0); // Capture-DR
    tck_cycle(0, 0); // Shift-DR

    uint64_t dout = 0;
    for (int i = 0; i < bits; ++i) {
        int tms = (i == bits - 1) ? 1 : 0;
        int tdo = tck_cycle(tms, (int)((din >> i) & 1));
        dout |= (uint64_t)tdo << i;
    }
    tck_cycle(1, 0); // Update-DR
    tck_cycle(0, 0); // Run-Test/Idle
    return dout;
}

static void dtmcs_write(uint32_t value) {
    ir_scan(IR_DTMCS);
    (void)dr_scan(32, value);
}

struct DmiRsp {
    int      op;
    int      addr;
    uint32_t data;
};

static DmiRsp decode_dmi(uint64_t v) {
    DmiRsp r;
    r.op = (int)(v & 3u);
    r.addr = (int)((v >> 34) & 0x7fu);
    r.data = (uint32_t)((v >> 2) & 0xffffffffu);
    return r;
}

static uint64_t dmi_scan(int op, int addr, uint32_t data) {
    ir_scan(IR_DMI);
    uint64_t din = ((uint64_t)(addr & 0x7f) << 34)
                 | ((uint64_t)data << 2)
                 | (uint64_t)(op & 3);
    return dr_scan(41, din);
}

static DmiRsp dmi_xfer(int op, int addr, uint32_t data) {
    (void)dmi_scan(op, addr, data);
    return decode_dmi(dmi_scan(0, 0, 0));
}

static void dmi_write(uint8_t addr, uint32_t data) {
    DmiRsp r = dmi_xfer(2, addr, data);
    EXPECT(r.op == 0, "DMI write failed");
    EXPECT(r.addr == addr, "DMI write response address mismatch");
}

static uint32_t dmi_read(uint8_t addr) {
    DmiRsp r = dmi_xfer(1, addr, 0);
    EXPECT(r.op == 0, "DMI read failed");
    EXPECT(r.addr == addr, "DMI read response address mismatch");
    return r.data;
}

static uint32_t poll_sba() {
    uint32_t sbcs = 0;
    for (int i = 0; i < 200; ++i) {
        sbcs = dmi_read(DM_SBCS);
        if (((sbcs >> 21) & 1u) == 0) break;
    }
    return sbcs;
}

static void sba_clear_errors() {
    uint32_t v = (2u << 17); // sbaccess = 32-bit
    v |= (7u << 12);         // clear sberror
    v |= (1u << 22);         // clear sbbusyerror
    dmi_write(DM_SBCS, v);

    uint32_t sbcs = dmi_read(DM_SBCS);
    EXPECT(((sbcs >> 12) & 7u) == 0, "sberror did not clear");
    EXPECT(((sbcs >> 21) & 1u) == 0, "sbbusy did not clear");
}

static void sba_set_readonaddr(bool on) {
    uint32_t v = (2u << 17) | (1u << 22);
    if (on) v |= (1u << 20);
    dmi_write(DM_SBCS, v);

    uint32_t sbcs = dmi_read(DM_SBCS);
    EXPECT(((sbcs >> 29) & 7u) == 1, "SBCS sbversion mismatch");
    EXPECT(((sbcs >> 17) & 7u) == 2, "SBCS sbaccess is not 32-bit");
    EXPECT(((sbcs >> 20) & 1u) == (on ? 1u : 0u), "SBCS sbreadonaddr mismatch");
    EXPECT(((sbcs >> 5) & 0x7fu) == 32, "SBCS sbasize mismatch");
    EXPECT(((sbcs >> 2) & 1u) == 1, "SBCS sbaccess32 is not set");
    EXPECT(((sbcs >> 12) & 7u) == 0, "SBCS has a pending error");
}

static void sba_write(uint32_t addr, uint32_t data) {
    sba_set_readonaddr(false);
    dmi_write(DM_SBADDRESS0, addr);
    dmi_write(DM_SBDATA0, data);

    uint32_t sbcs = poll_sba();
    EXPECT(((sbcs >> 21) & 1u) == 0, "SBA write never completed");
    EXPECT(((sbcs >> 12) & 7u) == 0, "SBA write reported an error");
}

static uint32_t sba_read(uint32_t addr) {
    sba_set_readonaddr(true);
    dmi_write(DM_SBADDRESS0, addr);

    uint32_t sbcs = poll_sba();
    EXPECT(((sbcs >> 21) & 1u) == 0, "SBA read never completed");
    EXPECT(((sbcs >> 12) & 7u) == 0, "SBA read reported an error");
    return dmi_read(DM_SBDATA0);
}

// Loads a linked RV32I image at the core's startup PC.
static void load_boot_image(const char* path) {
    std::ifstream f(path, std::ios::binary);
    EXPECT(f.good(), "cannot open the T0 boot image");
    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)),
                               std::istreambuf_iterator<char>());
    EXPECT(!bytes.empty(), "the T0 boot image is empty");
    EXPECT(bytes.size() <= 0x1000u, "the T0 boot image exceeds the boot window");

    for (size_t off = 0; off < bytes.size(); off += 4) {
        uint32_t word = 0;
        for (size_t b = 0; b < 4 && off + b < bytes.size(); ++b) {
            word |= (uint32_t)bytes[off + b] << (8 * b);
        }
        sba_write(0x80000000u + (uint32_t)off, word);
    }
}

static void wait_boot() {
    for (int i = 0; i < 4000; ++i) {
        if (dut->boot_done || dut->boot_error) return;
        core_cycle();
    }
    EXPECT(false, "boot sequencer did not finish");
}

static const uint32_t MEMTEST_SIG  = 0x80001008u;
static const uint32_t MEMTEST_FAIL = 0x80001018u;
static const uint32_t MEMTEST_TAG  = 0x5a5a0000u;

// The image destroys its own code lines when the finisher tests them, so every
// boot must reload it. The signature is per lane; a zero is 'not done yet'.
static void clear_memtest() {
    for (int lane = 0; lane < VX_CFG_NUM_THREADS; ++lane) {
        sba_write(MEMTEST_SIG + 4u * (uint32_t)lane, 0);
    }
}

static void check_memtest() {
    for (int attempt = 0; attempt < 600; ++attempt) {
        uint32_t sig0 = sba_read(MEMTEST_SIG);
        if ((sig0 & 0xffff0000u) == MEMTEST_TAG) {
            bool all_done = true;
            for (int lane = 0; lane < VX_CFG_NUM_THREADS; ++lane) {
                uint32_t sig = sba_read(MEMTEST_SIG + 4u * (uint32_t)lane);
                if ((sig & 0xffff0000u) != MEMTEST_TAG) {
                    all_done = false;
                    break;
                }
            }
            if (all_done) {
                for (int lane = 0; lane < VX_CFG_NUM_THREADS; ++lane) {
                    uint32_t sig = sba_read(MEMTEST_SIG + 4u * (uint32_t)lane);
                    uint32_t fails = sig & 0xffffu;
                    if (fails != 0) {
                        uint32_t addr = sba_read(MEMTEST_FAIL + 4u * (uint32_t)lane);
                        std::fprintf(stderr,
                                     "FAIL %s:%d: walking test lane %d: %u mismatches, last at 0x%08x\n",
                                     __FILE__, __LINE__, lane, fails, addr);
                        std::exit(1);
                    }
                }
                return;
            }
        }
        core_cycles(200);
    }
    std::fprintf(stderr,
                 "memtest stalled: sig=%08x/%08x/%08x/%08x result=%08x status=%08x "
                 "line0=%08x line8=%08x dest=%08x\n",
                 sba_read(MEMTEST_SIG), sba_read(MEMTEST_SIG + 4),
                 sba_read(MEMTEST_SIG + 8), sba_read(MEMTEST_SIG + 12),
                 sba_read(0x80001000u), sba_read(0x80001004u),
                 sba_read(0x80000000u), sba_read(0x80000200u),
                 sba_read(0x8003f000u));
    EXPECT(false, "walking test did not complete");
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    dut = new VVX_t0_dbg_tb_top;

    dut->clk = 0;
    dut->reset = 1;
    dut->jtag_tck = 0;
    dut->jtag_tms = 1;
    dut->jtag_tdi = 0;
    dut->jtag_trst_n = 1;
    dut->boot_en = 0;
    dut->core_stall = 0;
    dut->sram_stall = 0;

    core_cycles(20);
    dut->reset = 0;
    core_cycles(10);

    tap_reset();

    // ---- TAP identification ------------------------------------------------
    ir_scan(IR_IDCODE);
    uint32_t idcode = (uint32_t)dr_scan(32, 0);
    EXPECT(idcode == 0x00100001u, "IDCODE mismatch");

    ir_scan(IR_BYPASS);
    EXPECT(dr_scan(8, 0) == 0, "BYPASS is not zero");

    ir_scan(IR_DTMCS);
    uint32_t dtmcs = (uint32_t)dr_scan(32, 0);
    EXPECT((dtmcs & 0xfu) == 1, "DTMCS version mismatch");
    EXPECT(((dtmcs >> 4) & 0x3fu) == 7, "DTMCS abits mismatch");
    EXPECT(((dtmcs >> 10) & 3u) == 0, "DTMCS dmistat is not clear");

    // ---- DM registers ------------------------------------------------------
    uint32_t dmstatus = dmi_read(DM_DMSTATUS);
    EXPECT((dmstatus & 0xfu) == 2, "DMSTATUS version mismatch");
    EXPECT(((dmstatus >> 7) & 1u) == 1, "DM is not authenticated");

    uint32_t abstractcs = dmi_read(DM_ABSTRACTCS);
    EXPECT((abstractcs & 0xfu) == 1, "ABSTRACTCS datacount mismatch");
    EXPECT(dmi_read(DM_HARTINFO) == 0, "HARTINFO is not zero");

    dmi_write(DM_DMCONTROL, 1);
    EXPECT(dmi_read(DM_DMCONTROL) == 1, "dmactive did not set");
    dmstatus = dmi_read(DM_DMSTATUS);
    EXPECT(((dmstatus >> 11) & 1u) == 1, "allrunning is not set");

    dmi_write(DM_DMCONTROL, 1 | (1u << 1));
    EXPECT(dut->ndmreset == 1, "ndmreset did not assert");
    dmi_write(DM_DMCONTROL, 1);
    EXPECT(dut->ndmreset == 0, "ndmreset did not deassert");

    dmi_write(DM_COMMAND, 0);
    abstractcs = dmi_read(DM_ABSTRACTCS);
    EXPECT(((abstractcs >> 8) & 7u) == 2, "COMMAND did not report not-supported");
    dmi_write(DM_ABSTRACTCS, 1u << 9);
    abstractcs = dmi_read(DM_ABSTRACTCS);
    EXPECT(((abstractcs >> 8) & 7u) == 0, "cmderr did not clear");

    DmiRsp bad = dmi_xfer(1, 0x20, 0);
    EXPECT(bad.op == 2, "unimplemented DMI address did not fail");

    ir_scan(IR_DTMCS);
    dtmcs = (uint32_t)dr_scan(32, 0);
    EXPECT(((dtmcs >> 10) & 3u) == 2, "DTMCS did not latch the failed operation");
    dtmcs_write(1u << 16); // dmireset
    ir_scan(IR_DTMCS);
    dtmcs = (uint32_t)dr_scan(32, 0);
    EXPECT(((dtmcs >> 10) & 3u) == 0, "DTMCS dmireset did not clear dmistat");

    // ---- DMI busy ----------------------------------------------------------
    // Hold the core clock so the first request stays pending in the DTM, then
    // shift a second one. It must be dropped and reported as op=3, and the DTM
    // must latch dmistat=3 until dmireset clears it.
    (void)dmi_read(DM_DMSTATUS); // start from an idle DTM
    core_frozen = true;
    (void)dmi_scan(1, DM_DMSTATUS, 0);
    {
        DmiRsp busy = decode_dmi(dmi_scan(1, DM_DMSTATUS, 0));
        EXPECT(busy.op == 3, "a second DMI access while pending did not return op=3");
    }
    ir_scan(IR_DTMCS);
    dtmcs = (uint32_t)dr_scan(32, 0);
    EXPECT(((dtmcs >> 10) & 3u) == 3, "DMI busy did not latch dmistat=3");
    dtmcs_write(1u << 16); // dmireset

    core_frozen = false;
    core_cycles(8);
    {
        DmiRsp drained = decode_dmi(dmi_scan(0, 0, 0));
        EXPECT(drained.op == 0, "the parked DMI request did not complete");
        EXPECT(drained.addr == DM_DMSTATUS, "the parked DMI response address mismatch");
    }
    ir_scan(IR_DTMCS);
    dtmcs = (uint32_t)dr_scan(32, 0);
    EXPECT(((dtmcs >> 10) & 3u) == 0, "dmireset did not clear the busy status");

    // ---- SBA load and read -------------------------------------------------
    sba_write(0x80000000u, 0xdeadbeefu);
    EXPECT(sba_read(0x80000000u) == 0xdeadbeefu, "base word mismatch");

    sba_write(0x80020000u, 0x12345678u);
    EXPECT(sba_read(0x80020000u) == 0x12345678u, "mid word mismatch");

    sba_write(0x8003fffcu, 0xcafebabeu);
    EXPECT(sba_read(0x8003fffcu) == 0xcafebabeu, "last word mismatch");

    // Byte enables must isolate adjacent words in the same line.
    sba_write(0x80000100u, 0x11223344u);
    sba_write(0x80000104u, 0x55667788u);
    EXPECT(sba_read(0x80000100u) == 0x11223344u, "word 0 disturbed by word 1 write");
    EXPECT(sba_read(0x80000104u) == 0x55667788u, "word 1 mismatch");
    sba_write(0x80000108u, 0x99aabbccu);
    EXPECT(sba_read(0x80000104u) == 0x55667788u, "word 1 disturbed by word 2 write");

    // Walk a pattern across lines spread over the whole SRAM.
    for (int i = 0; i < 32; ++i) {
        uint32_t addr = 0x80000000u + (uint32_t)i * 0x40u;
        sba_write(addr, 0xa5a50000u | (uint32_t)i);
    }
    for (int i = 0; i < 32; ++i) {
        uint32_t addr = 0x80000000u + (uint32_t)i * 0x40u;
        EXPECT(sba_read(addr) == (0xa5a50000u | (uint32_t)i), "walking pattern mismatch");
    }

    // ---- SBA error codes ---------------------------------------------------
    sba_set_readonaddr(true);
    dmi_write(DM_SBADDRESS0, 0x80040000u);
    {
        uint32_t sbcs = poll_sba();
        EXPECT(((sbcs >> 12) & 7u) == 2, "out-of-range did not return sberror=2");
    }
    sba_clear_errors();

    sba_set_readonaddr(false);
    dmi_write(DM_SBADDRESS0, 0x80000002u);
    dmi_write(DM_SBDATA0, 1);
    {
        uint32_t sbcs = poll_sba();
        EXPECT(((sbcs >> 12) & 7u) == 3, "misaligned did not return sberror=3");
    }
    sba_clear_errors();

    dmi_write(DM_SBCS, (1u << 17)); // sbaccess = 16-bit
    dmi_write(DM_SBADDRESS0, 0x80000000u);
    dmi_write(DM_SBDATA0, 2);
    {
        uint32_t sbcs = poll_sba();
        EXPECT(((sbcs >> 12) & 7u) == 4, "unsupported size did not return sberror=4");
    }
    sba_clear_errors();

    // ---- Timeout -----------------------------------------------------------
    sba_set_readonaddr(false);
    dut->sram_stall = 1;
    dmi_write(DM_SBADDRESS0, 0x80000140u);
    dmi_write(DM_SBDATA0, 0xdeadbeefu);
    {
        uint32_t sbcs = dmi_read(DM_SBCS);
        EXPECT(((sbcs >> 21) & 1u) == 1, "sbbusy cleared before the SBA drained");
        EXPECT(((sbcs >> 12) & 7u) == 1, "timeout did not return sberror=1");
    }
    dut->sram_stall = 0;
    core_cycles(10);
    {
        uint32_t sbcs = dmi_read(DM_SBCS);
        EXPECT(((sbcs >> 21) & 1u) == 0, "sbbusy did not clear after drain");
    }
    sba_clear_errors();

    sba_write(0x80000140u, 0x0badf00du);
    EXPECT(sba_read(0x80000140u) == 0x0badf00du, "SBA did not recover after timeout");

    // ---- dmactive pulse resets the DM but not the SRAM --------------------
    sba_set_readonaddr(false);
    dmi_write(DM_SBADDRESS0, 0x80000000u);
    dmi_write(DM_DMCONTROL, 0);
    EXPECT(dmi_read(DM_DMCONTROL) == 0, "dmactive did not clear");
    EXPECT(dmi_read(DM_SBADDRESS0) == 0, "DM state was not reset by dmactive=0");
    dmi_write(DM_DMCONTROL, 1);
    EXPECT(dmi_read(DM_DMCONTROL) == 1, "dmactive did not re-enable");


    // ---- Boot: load the image, release the core, read the result ----------
    // boot_en low holds the core in reset while the image is loaded.
    EXPECT(dut->core_reset == 1, "core is not held in reset while boot_en=0");
    EXPECT(dut->boot_busy == 0, "boot sequencer ran while boot_en=0");

    const uint32_t boot_result = 0x0000c0deu;
    const uint32_t boot_status = 0x600d0000u;

    load_boot_image(T0_IMAGE_PATH);
    clear_memtest();

    dut->boot_en = 1;
    wait_boot();
    EXPECT(dut->boot_done == 1 && dut->boot_error == 0, "boot did not complete");
    EXPECT(dut->core_reset == 0, "core stayed in reset after boot");
    check_memtest();
    EXPECT(sba_read(0x80001004u) == boot_status, "boot status word mismatch");
    EXPECT(sba_read(0x80001000u) == boot_result, "boot result word mismatch");

    // ndmreset holds both the core and the sequencer; boot_en alone does not
    // release them.
    dmi_write(DM_DMCONTROL, 1 | (1u << 1));
    core_cycles(4);
    EXPECT(dut->core_reset == 1, "ndmreset did not hold the core in reset");
    dut->boot_en = 0;
    core_cycles(2);
    EXPECT(dut->core_reset == 1, "core left reset while boot_en=0");
    clear_memtest();
    load_boot_image(T0_SHORT_IMAGE_PATH);
    dut->boot_en = 1;
    core_cycles(2);
    EXPECT(dut->core_reset == 1, "core left reset under ndmreset");
    EXPECT(dut->boot_done == 0 && dut->boot_busy == 0, "boot ran under ndmreset");

    dmi_write(DM_DMCONTROL, 1);
    wait_boot();
    EXPECT(dut->boot_done == 1 && dut->boot_error == 0, "boot did not restart after ndmreset");
    check_memtest();
    EXPECT(sba_read(0x80001004u) == boot_status, "restarted boot status mismatch");
    EXPECT(sba_read(0x80001000u) == boot_result, "restarted boot result mismatch");

    // A core that never accepts the CTA keeps the KMU busy; the sequencer
    // must report a timeout instead of hanging.
    dut->core_stall = 1;
    dmi_write(DM_DMCONTROL, 1 | (1u << 1));
    core_cycles(4);
    dmi_write(DM_DMCONTROL, 1);
    for (int i = 0; i < 4000 && !dut->boot_error; ++i) core_cycle();
    EXPECT(dut->boot_error == 1, "boot did not time out with a stalled core");
    EXPECT(dut->boot_busy == 0, "boot stayed busy after a timeout");
    EXPECT(dut->boot_done == 0, "timeout reported a completed boot");

    dut->core_stall = 0;
    dmi_write(DM_DMCONTROL, 1 | (1u << 1));
    core_cycles(4);
    dut->boot_en = 0;
    core_cycles(2);
    clear_memtest();
    load_boot_image(T0_SHORT_IMAGE_PATH);
    dut->boot_en = 1;
    core_cycles(2);
    dmi_write(DM_DMCONTROL, 1);
    wait_boot();
    EXPECT(dut->boot_done == 1 && dut->boot_error == 0, "boot did not recover after a timeout");
    check_memtest();
    EXPECT(sba_read(0x80001004u) == boot_status, "post-timeout boot status mismatch");
    EXPECT(sba_read(0x80001000u) == boot_result, "post-timeout boot result mismatch");

    std::printf("PASSED - T0-A JTAG load/read, DMI busy, full-array walk and boot result\n");

    delete dut;
    return 0;
}
