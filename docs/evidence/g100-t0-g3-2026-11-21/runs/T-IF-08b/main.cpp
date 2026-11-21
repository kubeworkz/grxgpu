// T-IF-08b — DXA descriptor slot isolation (L0, host address map).
//
// Uses the same production encoder and minimal runtime stub as T-IF-08a.
// A 16 x 24 DCR register model starts at the sentinel value. For each slot n,
// the test writes a unique descriptor through program_2d(), then checks:
//   1. exactly the ten program_2d DCRs were written, all in slot n;
//   2. every word in all 15 other slots is unchanged;
//   3. every unwritten word in slot n still holds the sentinel.
// After all 16 writes, it reads back the complete 16 x 24 map.
//
// Scope: host address-map conformance only. This does not instantiate the DXA
// RTL, VX_dxa_desc_table/VX_dxa_core, or a T0 device.

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include <dxa.h>

namespace {

constexpr uint32_t kSlotBase = 0x100;
constexpr uint32_t kSlotStride = 24;
constexpr uint32_t kSlotCount = 16;
constexpr uint32_t kSlotWords = 24;
constexpr uint32_t kSentinel = 0xdeadbeefu;

struct Write {
  uint32_t addr;
  uint32_t value;
};

uint32_t g_regs[kSlotCount][kSlotWords];
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

uint32_t slot_k(uint32_t slot) {
  return (slot & 1u) ? 512u : 64u;
}

uint64_t slot_base(uint32_t slot) {
  return 0x100000000ull + uint64_t(slot) * 0x10000ull;
}

std::vector<Write> expected_writes(uint32_t slot) {
  const uint32_t dcr = kSlotBase + slot * kSlotStride;
  const uint32_t K = slot_k(slot);
  const uint64_t base = slot_base(slot);
  return {
      {dcr + 0, uint32_t(base & 0xffffffffu)},
      {dcr + 1, uint32_t(base >> 32)},
      {dcr + 2, K},
      {dcr + 3, 64u},
      {dcr + 7, K * 2u},
      {dcr + 11, 0x0au},
      {dcr + 12, 1u},
      {dcr + 13, 1u},
      {dcr + 17, 0x00100008u},
      {dcr + 20, 0u},
  };
}

void expect_writes(const char* label, const std::vector<Write>& expected) {
  if (g_writes.size() != expected.size()) {
    std::fprintf(stderr, "FAIL %s: got %zu writes, expected %zu\n",
                 label, g_writes.size(), expected.size());
    std::exit(1);
  }
  for (std::size_t i = 0; i < expected.size(); ++i) {
    if (g_writes[i].addr != expected[i].addr ||
        g_writes[i].value != expected[i].value) {
      std::fprintf(stderr,
                   "FAIL %s write %zu: got 0x%03x=0x%08x, "
                   "expected 0x%03x=0x%08x\n",
                   label, i, g_writes[i].addr, g_writes[i].value,
                   expected[i].addr, expected[i].value);
      std::exit(1);
    }
  }
}

void check_target_words(uint32_t slot, const std::vector<Write>& expected) {
  char label[32];
  std::snprintf(label, sizeof(label), "slot %u target", slot);
  const uint32_t dcr = kSlotBase + slot * kSlotStride;
  const uint32_t K = slot_k(slot);
  const uint64_t base = slot_base(slot);

  expect_u32(label, "base_lo", g_regs[slot][0],
             uint32_t(base & 0xffffffffu));
  expect_u32(label, "base_hi", g_regs[slot][1], uint32_t(base >> 32));
  expect_u32(label, "size0", g_regs[slot][2], K);
  expect_u32(label, "size1", g_regs[slot][3], 64u);
  expect_u32(label, "stride0", g_regs[slot][7], K * 2u);
  expect_u32(label, "meta", g_regs[slot][11], 0x0au);
  expect_u32(label, "estride0", g_regs[slot][12], 1u);
  expect_u32(label, "estride1", g_regs[slot][13], 1u);
  expect_u32(label, "tile01", g_regs[slot][17], 0x00100008u);
  expect_u32(label, "cfill", g_regs[slot][20], 0u);

  // The expected list is the complete write set; confirm it names the ten
  // offsets just checked and no others.
  if (expected.size() != 10) fail(label, "write count", uint32_t(expected.size()), 10u);
  for (const auto& w : expected) {
    if (w.addr < dcr || w.addr >= dcr + kSlotStride) {
      fail(label, "write outside target slot", w.addr, dcr);
    }
  }
}

} // namespace

// Model the DCR decode: every write lands in its addressed slot/word.
int vx_dcr_write(vx_device_h, uint32_t addr, uint32_t value) {
  if (addr < kSlotBase) {
    std::fprintf(stderr, "FAIL write below DXA slot map: 0x%03x\n", addr);
    std::exit(1);
  }
  const uint32_t rel = addr - kSlotBase;
  if (rel >= kSlotCount * kSlotStride) {
    std::fprintf(stderr, "FAIL write above DXA slot map: 0x%03x\n", addr);
    std::exit(1);
  }
  const uint32_t slot = rel / kSlotStride;
  const uint32_t off = rel % kSlotStride;
  g_regs[slot][off] = value;
  g_writes.push_back({addr, value});
  return 0;
}

int main() {
  for (uint32_t slot = 0; slot < kSlotCount; ++slot) {
    for (uint32_t off = 0; off < kSlotWords; ++off) {
      g_regs[slot][off] = kSentinel;
    }
  }

  uint32_t neighbor_words = 0;
  uint32_t unwritten_words = 0;

  for (uint32_t slot = 0; slot < kSlotCount; ++slot) {
    const auto expected = expected_writes(slot);

    uint32_t before[kSlotCount][kSlotWords];
    std::memcpy(before, g_regs, sizeof(g_regs));

    g_writes.clear();
    const int rc = vortex::dxa::program_2d(
        nullptr, slot, slot_base(slot), slot_k(slot), 64u,
        slot_k(slot) * 2u, 8u, 16u, 2u);
    if (rc != 0) {
      std::fprintf(stderr, "FAIL slot %u: program_2d returned %d\n", slot, rc);
      std::exit(1);
    }

    char label[32];
    std::snprintf(label, sizeof(label), "slot %u", slot);
    expect_writes(label, expected);
    check_target_words(slot, expected);

    // Every other slot must be bit-for-bit unchanged.
    for (uint32_t other = 0; other < kSlotCount; ++other) {
      if (other == slot) continue;
      for (uint32_t off = 0; off < kSlotWords; ++off) {
        if (g_regs[other][off] != before[other][off]) {
          std::fprintf(stderr,
                       "FAIL slot %u: neighbor slot %u word %u changed "
                       "0x%08x -> 0x%08x\n",
                       slot, other, off, before[other][off],
                       g_regs[other][off]);
          std::exit(1);
        }
        ++neighbor_words;
      }
    }

    // Every DCR in the target slot that program_2d does not define must stay
    // at the sentinel; a write spilling into an unused word would fail here.
    bool written[kSlotWords] = {};
    for (const auto& w : expected) {
      const uint32_t off = (w.addr - kSlotBase) % kSlotStride;
      written[off] = true;
    }
    for (uint32_t off = 0; off < kSlotWords; ++off) {
      if (!written[off]) {
        if (g_regs[slot][off] != kSentinel) {
          std::fprintf(stderr,
                       "FAIL slot %u: unwritten word %u changed to 0x%08x\n",
                       slot, off, g_regs[slot][off]);
          std::exit(1);
        }
        ++unwritten_words;
      }
    }

    std::printf("PASS slot %u: 10 writes; 15 neighbors unchanged; "
                "14 target words still sentinel\n",
                slot);
  }

  // Full-map readback: all 16 slots must simultaneously contain exactly their
  // own expected words; all other words remain the sentinel.
  uint32_t readback_words = 0;
  for (uint32_t slot = 0; slot < kSlotCount; ++slot) {
    const auto expected = expected_writes(slot);
    const uint32_t dcr = kSlotBase + slot * kSlotStride;
    check_target_words(slot, expected);
    for (uint32_t off = 0; off < kSlotWords; ++off) {
      uint32_t expected_value = kSentinel;
      for (const auto& w : expected) {
        if (w.addr == dcr + off) expected_value = w.value;
      }
      if (g_regs[slot][off] != expected_value) {
        std::fprintf(stderr,
                     "FAIL readback slot %u word %u: got 0x%08x, "
                     "expected 0x%08x\n",
                     slot, off, g_regs[slot][off], expected_value);
        std::exit(1);
      }
      ++readback_words;
    }
  }

  std::printf("PASS T-IF-08b: 16/16 slots written; %u neighbor-slot words "
              "and %u target-slot unwritten words unchanged; "
              "%u readback words, 0 mismatches\n",
              neighbor_words, unwritten_words, readback_words);
  return 0;
}
