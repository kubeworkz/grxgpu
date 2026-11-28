// T-IF-08a — DXA host encoder / descriptor-word equivalence (L0).
//
// Exercises the production encoder in sw/runtime/include/dxa.h:
//   program_2d(), set_layout(), set_tile_geometry()
// for the frozen G100-T0-G2-SGEMM-1.0 A and B descriptor shapes at K=64 and
// K=512. The expected DCR words below are written from the ABI constants in
// sw/VX_types.h and the field widths in hw/rtl/dxa/VX_dxa_pkg.sv; they are
// not computed with the encoder's own packing helpers.
//
// Scope: software conformance only. This host test does not instantiate the
// DXA RTL, does not exercise slot isolation, and makes no T0 device claim.

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

#include <dxa.h>

namespace {

struct Write {
  uint32_t addr;
  uint32_t value;
};

struct DecodedDesc {
  uint64_t base;
  uint32_t size0;
  uint32_t size1;
  uint32_t stride0;
  uint32_t meta;
  uint32_t estride0;
  uint32_t estride1;
  uint32_t tile01;
  uint32_t cfill;
};

std::vector<Write> g_writes;

[[noreturn]] void fail(const char* label, const char* field,
                       uint32_t got, uint32_t expected) {
  std::fprintf(stderr, "FAIL %s %s: got 0x%08x, expected 0x%08x\n",
               label, field, got, expected);
  std::exit(1);
}

void expect_u32(const char* label, const char* field,
                uint32_t got, uint32_t expected) {
  if (got != expected) fail(label, field, got, expected);
}

uint32_t word_at(const std::vector<Write>& writes, uint32_t addr,
                 const char* label) {
  for (const auto& w : writes) {
    if (w.addr == addr) return w.value;
  }
  std::fprintf(stderr, "FAIL %s: missing DCR 0x%03x\n", label, addr);
  std::exit(1);
}

DecodedDesc decode_program(const std::vector<Write>& writes, uint32_t dcr,
                           const char* label) {
  if (writes.size() != 10) {
    std::fprintf(stderr, "FAIL %s: expected 10 program writes, got %zu\n",
                 label, writes.size());
    std::exit(1);
  }
  DecodedDesc d;
  d.base = (uint64_t(word_at(writes, dcr + 1, label)) << 32) |
           word_at(writes, dcr + 0, label);
  d.size0 = word_at(writes, dcr + 2, label);
  d.size1 = word_at(writes, dcr + 3, label);
  d.stride0 = word_at(writes, dcr + 7, label);
  d.meta = word_at(writes, dcr + 11, label);
  d.estride0 = word_at(writes, dcr + 12, label);
  d.estride1 = word_at(writes, dcr + 13, label);
  d.tile01 = word_at(writes, dcr + 17, label);
  d.cfill = word_at(writes, dcr + 20, label);
  return d;
}

void check_program(const char* label, const DecodedDesc& d,
                   uint64_t base, uint32_t size0, uint32_t size1,
                   uint32_t stride0, uint32_t tile01) {
  if (d.base != base) {
    std::fprintf(stderr, "FAIL %s base: got 0x%016llx, expected 0x%016llx\n",
                 label, static_cast<unsigned long long>(d.base),
                 static_cast<unsigned long long>(base));
    std::exit(1);
  }
  expect_u32(label, "size0", d.size0, size0);
  expect_u32(label, "size1", d.size1, size1);
  expect_u32(label, "stride0", d.stride0, stride0);
  expect_u32(label, "meta.rank", d.meta & 0x7u, 2u);
  expect_u32(label, "meta.elem", (d.meta >> 3) & 0x3u, 1u);
  expect_u32(label, "meta.layout", (d.meta >> 5) & 0x3u, 0u);
  expect_u32(label, "estride0", d.estride0, 1u);
  expect_u32(label, "estride1", d.estride1, 1u);
  expect_u32(label, "tile01", d.tile01, tile01);
  expect_u32(label, "cfill", d.cfill, 0u);
  std::printf("PASS %s: decoded base/sizes/stride/meta/tiles/cfill\n", label);
}

void expect_writes(const char* label, const std::vector<Write>& expected) {
  bool ok = g_writes.size() == expected.size();
  if (ok) {
    for (std::size_t i = 0; i < expected.size(); ++i) {
      if (g_writes[i].addr != expected[i].addr ||
          g_writes[i].value != expected[i].value) {
        ok = false;
        break;
      }
    }
  }
  if (!ok) {
    std::fprintf(stderr, "FAIL %s: captured %zu writes\n", label,
                 g_writes.size());
    for (std::size_t i = 0; i < g_writes.size(); ++i) {
      std::fprintf(stderr, "  got [%zu] 0x%03x = 0x%08x\n", i,
                   g_writes[i].addr, g_writes[i].value);
    }
    std::fprintf(stderr, "  expected %zu writes\n", expected.size());
    for (std::size_t i = 0; i < expected.size(); ++i) {
      std::fprintf(stderr, "  exp [%zu] 0x%03x = 0x%08x\n", i,
                   expected[i].addr, expected[i].value);
    }
    std::exit(1);
  }
  std::printf("PASS %s: %zu writes\n", label, expected.size());
}

void run_case(uint32_t K) {
  // Frozen workload geometry: M=N=64, NUM_THREADS=4, WGMMA_NRC=16, FP16.
  // xtileM=4, xtileN=16, tileK=8, tcN=2, cta_M=4 warps * 4 = 16.
  constexpr uint32_t M = 64;
  constexpr uint32_t N = 64;
  constexpr uint32_t cta_M = 16;
  constexpr uint32_t tileK = 8;
  constexpr uint32_t xtileN = 16;
  constexpr uint32_t tcN = 2;
  constexpr uint32_t elem_bytes = 2;

  constexpr uint64_t baseA = 0x123456789abcdef0ull;
  constexpr uint64_t baseB = 0xfedcba9876543210ull;

  // slot 0 @ 0x100: base_lo, base_hi, size0=K, size1=M, stride0=K*2,
  // meta=rank2|elem2, estride0=1, estride1=1, tiles=(M-tile 16, K-tile 8),
  // cfill=0.
  const std::vector<Write> expectedA = {
      {0x100, 0x9abcdef0u},
      {0x101, 0x12345678u},
      {0x102, K},
      {0x103, M},
      {0x107, K * elem_bytes},
      {0x10b, 0x0au},
      {0x10c, 1u},
      {0x10d, 1u},
      {0x111, 0x00100008u},
      {0x114, 0u},
  };

  // slot 1 @ 0x118: base_lo, base_hi, size0=N, size1=K, stride0=N*2,
  // meta=rank2|elem2, estride0=1, estride1=1, tiles=(N-tile 16, K-tile 8),
  // cfill=0.
  const std::vector<Write> expectedB = {
      {0x118, 0x76543210u},
      {0x119, 0xfedcba98u},
      {0x11a, N},
      {0x11b, K},
      {0x11f, N * elem_bytes},
      {0x123, 0x0au},
      {0x124, 1u},
      {0x125, 1u},
      {0x129, 0x00080010u},
      {0x12c, 0u},
  };

  g_writes.clear();
  int rc = vortex::dxa::program_2d(nullptr, 0, baseA, K, M,
                                   K * elem_bytes, tileK, cta_M,
                                   elem_bytes);
  if (rc != 0) {
    std::fprintf(stderr, "FAIL program_2d A returned %d\n", rc);
    std::exit(1);
  }
  expect_writes("K descriptor A (row-major)", expectedA);
  check_program("K descriptor A decode", decode_program(g_writes, 0x100,
                                                        "A decode"),
                baseA, K, M, K * elem_bytes, 0x00100008u);

  g_writes.clear();
  rc = vortex::dxa::program_2d(nullptr, 1, baseB, N, K,
                               N * elem_bytes, xtileN, tileK,
                               elem_bytes);
  if (rc != 0) {
    std::fprintf(stderr, "FAIL program_2d B returned %d\n", rc);
    std::exit(1);
  }
  expect_writes("K descriptor B (base words)", expectedB);
  check_program("K descriptor B decode", decode_program(g_writes, 0x118,
                                                        "B decode"),
                baseB, N, K, N * elem_bytes, 0x00080010u);

  // BLOCK_MAJOR overwrites only META at slot 1: rank2|elem2|layout(3)<<5.
  g_writes.clear();
  rc = vortex::dxa::set_layout(nullptr, 1, vortex::dxa::Layout::BlockMajor,
                               /*rank=*/2, elem_bytes);
  if (rc != 0) {
    std::fprintf(stderr, "FAIL set_layout returned %d\n", rc);
    std::exit(1);
  }
  expect_writes("K descriptor B (BlockMajor meta)", {{0x123, 0x6au}});
  {
    const uint32_t meta = word_at(g_writes, 0x123, "B layout meta");
    expect_u32("K descriptor B layout", "rank", meta & 0x7u, 2u);
    expect_u32("K descriptor B layout", "elem", (meta >> 3) & 0x3u, 1u);
    expect_u32("K descriptor B layout", "layout", (meta >> 5) & 0x3u, 3u);
    std::printf("PASS K descriptor B layout decode: rank/elem/layout\n");
  }

  // The WGMMA tile geometry rides ESTRIDE2 at slot 1.
  g_writes.clear();
  rc = vortex::dxa::set_tile_geometry(nullptr, 1, tcN);
  if (rc != 0) {
    std::fprintf(stderr, "FAIL set_tile_geometry returned %d\n", rc);
    std::exit(1);
  }
  expect_writes("K descriptor B (tile geometry)", {{0x126, tcN}});
  expect_u32("K descriptor B tile geometry", "estride2",
             word_at(g_writes, 0x126, "B tile geometry"), tcN);
  std::printf("PASS K descriptor B tile geometry decode: tcN\n");
}

} // namespace

// Fail at compile time if the ABI constants this test hard-codes drift.
static_assert(VX_DCR_DXA_DESC_BASE == 0x100, "DXA descriptor base moved");
static_assert(VX_DCR_DXA_DESC_STRIDE == 24, "DXA descriptor stride moved");
static_assert(VX_DCR_DXA_DESC_COUNT == 16, "DXA descriptor slot count moved");
static_assert(VX_DCR_DXA_DESC_BASE_LO_OFF == 0, "base_lo offset moved");
static_assert(VX_DCR_DXA_DESC_BASE_HI_OFF == 1, "base_hi offset moved");
static_assert(VX_DCR_DXA_DESC_SIZE0_OFF == 2, "size0 offset moved");
static_assert(VX_DCR_DXA_DESC_SIZE1_OFF == 3, "size1 offset moved");
static_assert(VX_DCR_DXA_DESC_STRIDE0_OFF == 7, "stride0 offset moved");
static_assert(VX_DCR_DXA_DESC_META_OFF == 11, "meta offset moved");
static_assert(VX_DCR_DXA_DESC_ESTRIDE0_OFF == 12, "estride0 offset moved");
static_assert(VX_DCR_DXA_DESC_ESTRIDE1_OFF == 13, "estride1 offset moved");
static_assert(VX_DCR_DXA_DESC_ESTRIDE2_OFF == 14, "estride2 offset moved");
static_assert(VX_DCR_DXA_DESC_TILESIZE01_OFF == 17, "tilesize01 offset moved");
static_assert(VX_DCR_DXA_DESC_CFILL_OFF == 20, "cfill offset moved");

// Capture every DCR write. The encoder must emit exactly the expected list.
int vx_dcr_write(vx_device_h, uint32_t addr, uint32_t value) {
  g_writes.push_back({addr, value});
  return 0;
}

int main() {
  for (uint32_t K : {64u, 512u}) {
    run_case(K);
  }
  std::printf("PASS T-IF-08a: frozen A/B descriptors at K=64 and K=512; "
              "44 expected DCR writes, 8 decoded descriptor checks, "
              "0 mismatches\n");
  return 0;
}
