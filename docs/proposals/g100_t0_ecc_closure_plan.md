# G100-T0 ECC Closure Plan

**Status:** Draft for review — planning only, no RTL implemented.
**Date:** 2026-11-20.
**Target:** T0 pin `ff550c27570f17b0c8242be42257043d3de4ffa7` (tree `cf6b2f8657fcba985dd9007fa403231c3d800301`).
**Scope owner:** unassigned.
**Related records:** [T0 production baseline](g100_production_baseline.md) ·
[T0 tapeout checklist](../grxgpu_g100_t0_tapeout_checklist.md) ·
[G1 evidence audit](../grxgpu_g100_t0_g1_evidence_audit.md) ·
[T0 debug security review](g100_t0_debug_security_review.md).

This plan closes the ECC item of the G1 blocker: a SECDED codec, an ECC bank
RAM with byte-enable read-modify-write, benches, counter readout for LMEM,
ICache and DCache, and a disposition for the unprotected T0 test SRAM. It is a
plan only. Nothing here authorizes RTL work to start, and nothing here changes
the G0 commercial hold, purchase decisions, G5 implementation, G6 tapeout or
production release; those remain on hold.

---

## 1. State at the pin

Verified on 2026-11-20 against the pinned tree:

| Area | Pinned state | Source |
|---|---|---|
| ECC RTL | No SECDED module, ECC bank wrapper or ECC bench exists at any revision | `git log --all` over the paths named by the removed CI lanes |
| LMEM | 16 KB per core (`LMEM_LOG_SIZE=14`), 4 banks, 32-bit words at XLEN=32, four `VX_sp_ram` banks with 4-bit byte enables | `hw/rtl/mem/VX_local_mem.sv`, `VX_config.toml` |
| DCache data | 64 B line, 8 B word, 1 bank per cache, 4 ways; 8 word slices per line, 64 bits each | `hw/rtl/cache/VX_cache_data.sv`, proposed config |
| ICache data | 64 B line, 4 B word; 16 word slices per line, 32 bits each | `hw/rtl/cache/VX_cache_data.sv`, `VX_gpu_pkg.sv` |
| Test SRAM | 4096 × 512-bit lines (256 KB), byte-enable writes, no check bits, decoded as line address `addr[25:12]==14'h2000` (byte window `0x8000_0000`–`0x8003_FFFF`) | `hw/rtl/dbg/VX_t0_test_sram.sv` |
| Debug readout | SBA rejects any address outside `addr[31:18]==14'h2000` (the same `0x8000_0000`–`0x8003_FFFF` window); that whole window is test SRAM, leaving no spare decode | `hw/rtl/dbg/VX_dm_sba.sv` |
| T0 harness | `VX_t0_dbg_tb_top` instantiates the core and the test SRAM only; LMEM, ICache and DCache are not in the T0-A path | `hw/unittest/t0_dbg/VX_t0_dbg_tb_top.sv` |
| CI | The `hw-ecc` and `hw-ecc-ram` lanes were removed on 2026-11-20 because the targets never existed | `ci/testcases/unittest.yaml` |

Three consequences drive the plan. First, ECC cannot be "restored"; it has to be
built. Second, at T0-A the only array that exists in the debug harness is the
test SRAM, so the counter-readout path cannot be exercised in silicon unless
that array is protected (§7). Third, the counters have to be readable over SBA,
and the SBA window is a reviewed security boundary: the
[T0 debug security review](g100_t0_debug_security_review.md) treats its
hard-wired window-equals-memory property as the block's most important
containment guarantee. Adding a status window widens that surface, so it needs
a delta review and a containment test, not just a second address comparator
(§2.9, §3 S5).

## 2. Design decisions to freeze before code

These are the decisions that must be signed off first; each one changes the
RTL shape, so changing it later is expensive.

1. **Codeword width.** SECDED is defined per codeword, not per array. Use a
   parameterised Hsiao codec with (32, 39) and (64, 72) instances: 39-bit
   codewords for 32-bit words and 72-bit codewords for 64-bit words. At the T0
   configuration that means LMEM 32+7 (4 B words), ICache 32+7 per slice
   (16 slices per line), DCache 64+8 per slice (8 slices per line). The
   baseline's "64+8" applies unchanged to 64-bit words and to XLEN=64 builds.
   *Alternative rejected:* pairing two 32-bit LMEM words into one 64+8 codeword
   turns every 4-byte store into a read-modify-write of a wider word for no
   coding benefit at T0.
2. **Correctable errors** are corrected silently, counted, and the first one is
   latched. No bus error, no exception.
3. **Uncorrectable errors** are never silently corrected. LMEM returns the
   stored word and raises a sticky per-array flag; a cache invalidates the line
   so the next access refetches from memory. Per-request error signalling
   (bus error or precise exception) is out of scope for T0 and recorded as a
   T0-B item, because it changes the core's memory interface.
4. **Counters are 32-bit saturating**, one corrected and one uncorrected
   counter per array, plus a sticky first-fault record (array, bank, way/set or
   line, word, syndrome, correctable/uncorrectable). Per-bank counters are not
   worth the registers at T0; the first-fault record identifies the bank.
5. **Read-modify-write is the only partial-write path.** A write whose byte
   enables do not cover the whole codeword reads the codeword, merges the
   enabled bytes, re-encodes and writes back. Full-codeword writes bypass the
   read. This costs an extra read cycle before the write; nothing else in the
   bank changes.
6. **Cache init and flush write encoded zeros**, not raw zeros, so an
   initialised line has valid check bits. This is a real correctness trap: the
   current arrays are initialised with plain zeros.
7. **Tag arrays and dirty-byte masks are out of scope.** The baseline names the
   three data arrays. Protecting tags needs per-way codewords in the folded tag
   store and changes the tag-compare path; record it as a deliberate exclusion
   with rationale rather than leaving it implicit.
8. **No background scrubber at T0.** A correctable error is only observed when
   the word is read. State this in the checklist so the counter is not read as
   a scrubber's inventory.
9. **The address-decode contract stays exact.** Widening SBA is a change to the
   debug surface, so it is gated by a delta review of the security review and by
   a containment test. Every address SBA accepts must be claimed by exactly one
   slave; each slave decode must be a subset of an SBA-accepted window; the SRAM
   decode must not change; the gap between the two windows must be rejected.
   The review's "window equals memory" property becomes "window equals mapped
   slaves", and the test proves the two cannot drift apart.
10. **The injection register is a reviewed backdoor.** It is off by default,
   enabled only by the bring-up configuration, can only flip one bit on one
   read, and can never write data or check bits. Its presence, default and
   removal path go in the security-review addendum and the checklist.

## 3. Work breakdown, in effort order

Effort is in engineer-days and is a planning estimate, not a measurement. Each
stage ends at a gate; a stage that fails its gate does not hand off.

| # | Stage | Depends on | Effort | Exit gate |
|---|---|---|---|---|
| S0 | Freeze §2 decisions and the register map | — | 1–2 | Review signoff on this document |
| S1 | SECDED codec + exhaustive bench | S0 | 4–6 | `hw-ecc` lane green in CI |
| S2 | ECC bank RAM wrapper + bench | S1 | 4–6 | `hw-ecc-ram` lane green in CI |
| S3 | LMEM integration | S2 | 3–4 | `local_mem` bench with ECC cases green |
| S4 | ICache/DCache integration | S2 | 8–12 | `cache` bench green, no timing-path regression |
| S5 | Counters, status CSR, SBA readout, security delta review | S0, S2 | 6–8 | T0 TB reads counters over SBA; containment test green; security-review addendum signed |
| S6 | Test SRAM protection (recommended, §7) | S2, S5 | 3–4 | T0 TB injects and reads back over SBA |
| S7 | System verification, synthesis delta, records | S3–S6 | 4–6 | G1 ECC exit criteria met (§6) |

Total: roughly 33–48 engineer-days, about eight weeks for one engineer. S1/S2
and S5 can run in parallel with S3/S4 once the interfaces are frozen.

### S0 — Freeze the design

Deliverable: this document approved with the §2 decisions and the register map
in §4. No code.

### S1 — SECDED codec

Deliverables:

- `hw/rtl/libs/VX_ecc_secded.sv`: parameterised encoder/decoder, `DATAW` of 32
  or 64, returning corrected data plus `syndrome`, `correctable` and
  `uncorrectable`. Pure combinational; no state, no counters.
- `hw/unittest/ecc/`: bench driving encode → inject → decode.

Verification:

- For several data patterns (all zeros, all ones, walking-1 over every data
  bit, 10,000 random words): encode, then inject every single-bit error over
  the full codeword (39 or 72 positions) and require exact correction; inject
  every double-bit pair (741 / 2,556 pairs) and require detection with no
  false correction; check that a clean codeword reports no error.
- Elaborate both `DATAW` values in the bench, so the 64+8 baseline instance is
  covered even though T0 is XLEN=32.
- Wire `hw-ecc` back into `ci/testcases/unittest.yaml` with
  `run: "make -C hw/unittest run-ecc"` and `touches` naming the codec and the
  bench, once the target exists.

### S2 — ECC bank RAM

Deliverables:

- `hw/rtl/libs/VX_ecc_ram.sv`: wraps a `VX_sp_ram`/`VX_dp_ram` bank. Parameters:
  data width, codeword data width, byte enables, read latency. Decodes on read,
  encodes on write, performs the read-modify-write when `byteen` is partial,
  and exposes `corrected`/`uncorrected` pulses, syndrome and lane index.
- `hw/unittest/ecc_ram/`: bench for the wrapper.

Verification:

- Every byte-enable mask: 256 masks at 64-bit words, 16 at 32-bit words, each
  through the RMW path followed by a read-back that must match the merged word
  with no error.
- Full-word writes must not touch the read port (assert the bypass), and must
  leave correct check bits.
- Preload single-bit faults in data and check bits: corrected, counted, data
  matches; preload double-bit faults: detected, data not silently corrected.
- Back-to-back write/read and read-during-RMW sequences must not return stale
  or half-merged data.
- Wire `hw-ecc-ram` back into the catalog with
  `run: "make -C hw/unittest run-ecc-ram"`.

### S3 — LMEM

Deliverables: `VX_local_mem` instantiates one wrapper per bank (4 banks), with
per-bank error pulses aggregated to the array counters. The DMA port uses the
same write path, so it inherits RMW and must be included in the bench.

Verification: extend `hw/unittest/local_mem` with ECC cases — partial and full
writes, DMA and LSU access to the same bank, fault injection on read, counter
increments. Confirm the existing read-after-write hazard interlock still holds
with the extra RMW cycle, and record the cycle delta.

### S4 — ICache and DCache

Deliverables: `VX_cache_data` swaps each `VX_sp_ram` slice for the wrapper.
Fills encode every slice of the installed sector; writebacks and flushes decode
before driving the memory side; init writes encoded zeros (§2.6). On
`uncorrected`, the bank invalidates the line and counts it.

Verification:

- Extend `hw/unittest/cache`: fill → read, store → writeback, init and flush
  all produce clean reads; inject a correctable error into a line and require
  the corrected word plus a counter; inject an uncorrectable error and require
  the line to be invalidated, the counter to move, and no corrected-looking
  data to reach the core interface.
- Confirm the DCache read path still meets its pipeline contract: decode sits
  after the array read, so the added delay is a mux, not a new stage. Measure
  it; do not assume it.

### S5 — Counters, readout and the debug surface

Deliverables:

- Per-array saturating counters and first-fault registers at the array
  boundary (`VX_local_mem`, `VX_cache_data`/`VX_cache_bank`).
- `hw/rtl/dbg/VX_t0_ecc_status.sv`: a 64-bit-bus slave with the register map in
  §4, byte-enable writes, one-cycle response, clear-on-write for sticky bits.
  Only the control, clear and injection registers accept writes; counters and
  fault records are read-only.
- `hw/rtl/dbg/VX_t0_mem_demux.sv` (or a decode in `VX_t0_mem_arb`): claims the
  CSR window before the test SRAM and forwards everything else unchanged. The
  SRAM window and the CSR window are defined once as shared localparams and
  compared exactly, so SBA, the demux and the SRAM cannot drift apart.
- Widen the SBA decode in `VX_dm_sba.sv` to admit the CSR window
  (`addr[31:20]==12'h801`, i.e. 0x8010_0000) in addition to the test-SRAM
  window, as two exact comparators. Everything outside both windows keeps the
  existing `sberror=2` path, including the `0x8004_0000`–`0x800F_FFFF` gap.
- A one-shot injection register in the status block: `{array, lane, bit,
  double}` applies to the next read of that array. Guard it with a
  configuration bit that is on for T0-A bring-up silicon and off for
  production, so the backdoor is explicit rather than always present.
- An addendum to the [debug security review](g100_t0_debug_security_review.md).
  It updates §2 (what the path can reach) with the status window and injection
  register, restates the containment property as "every SBA-accepted address is
  claimed by exactly one slave", confirms that G-8's production gate is
  unchanged, and records the tests below under §7. This is a delta review of a
  changed surface, not a rewrite of the 2026-11-03 review.

Verification:

- A new `hw/unittest/ecc_status` bench (or a `t0_dbg` test) writes and reads
  every register, checks saturation and clear-on-write, checks that the
  injection register produces exactly one fault, and checks that read-only
  registers ignore writes.
- **Decoder-agreement/containment test**, in the same bench and repeated in the
  T0 TB with the SRAM present. Sweep `0x7FFF_FFFF`, `0x8000_0000`,
  `0x8003_FFFF`, `0x8004_0000`, `0x800F_FFFF`, `0x8010_0000`, `0x801F_FFFF`
  and `0x8020_0000`, plus random addresses, from both SBA and core masters:
  each access either reaches exactly the intended slave or returns `sberror=2`;
  a status-window write leaves the SRAM checksum unchanged and an SRAM write
  leaves the status registers unchanged; `oob` never asserts for a
  status-window access; misaligned and unsupported-size accesses keep
  `sberror=3` and `4`. Assert the demux select is one-hot for every accepted
  address, so a future third window cannot silently overlap.
- Add a catalog lane for the bench. This test also covers security-review §7
  test 1 (out-of-window SBA access), which the review lists as untested today.

### S6 — Test SRAM

See §7 for the recommendation. If accepted: instantiate the wrapper on the test
SRAM's 8 × 64-bit lanes (576 bits stored per 512-bit line), route its counters
to the status block as the TSRAM array, and verify through JTAG/SBA that a
4-byte store still reads back correctly through the RMW path and that injected
faults appear in the counters.

### S7 — System verification and records

- T0 TB: boot, halt, SBA read/write at base/middle/last word, then inject a
  correctable and an uncorrectable error and read both counters and the
  first-fault record. Archive the transcript and log with checksums under
  `docs/evidence/g100-t0-ecc-<date>/`.
- Run the affected `cache`, `local_mem` and `t0` benches, plus the `model_parity`
  cases that cover cache and LMEM traffic. ECC must not change retirement; if
  the RMW cycle moves any parity case, update the SimX timing model in the same
  change (the lockstep rule), never the tolerance.
- Synthesis: record area and timing delta for the three arrays plus the test
  SRAM against the T0 baseline. No area claim without the report.
- Update the checklist ECC status, inventory row and blocker, the baseline ECC
  row, and the audit's ECC disposition. The audit's G1 item closes only when
  the benches are in CI, the T0 transcript exists, the area/timing delta is
  recorded and an independent reviewer signs off.

## 4. Status register map

32-bit registers in a 64-bit bus window, little-endian, byte-enable writes,
one-cycle response. Sticky bits clear on write-1.

| Offset | Name | Contents |
|---|---|---|
| 0x000 | ID | magic and version |
| 0x004 | CAPABILITY | bitmap of arrays present (LMEM, ICACHE, DCACHE, TSRAM) |
| 0x008 | GLOBAL_STATUS | OR of per-array uncorrectable/overflow flags |
| 0x00C | GLOBAL_CONTROL | clear-all, injection enable (bring-up only) |
| 0x100 + 0x20·n | CORRECTED | saturating corrected-error count, array `n` |
| +0x004 | UNCORRECTED | saturating uncorrectable-error count |
| +0x008 | FAULT_INFO | valid, correctable, array, bank, lane, syndrome |
| +0x00C | FAULT_ADDR | line or word address low 32 bits |
| +0x010 | FAULT_DETAIL | way/set or word index, high address bits |
| +0x018 | INJECT | one-shot `{array, lane, bit, double}` |
| +0x01C | ARRAY_STATUS | per-array sticky flags and overflow |

Array index `n`: 0 LMEM, 1 ICACHE, 2 DCACHE, 3 TSRAM.

**Security constraints.** The block is a leaf slave: it mirrors no write to the
bus and cannot reach the SRAM, and the demux is the only connection between the
two windows. Writes are accepted only to `GLOBAL_CONTROL`, the per-array clear
bits and `INJECT`. Those constraints are what the containment test checks and
what the security-review addendum records.

## 5. Verification matrix

| Claim | Proved by |
|---|---|
| Codec corrects every single-bit error and detects every double-bit error | `hw/unittest/ecc` |
| RMW preserves every byte-enable combination and full-word writes bypass it | `hw/unittest/ecc_ram` |
| LMEM banks are protected and the DMA path is covered | `hw/unittest/local_mem` |
| Cache fills, stores, writebacks, init and flush are protected; UE invalidates | `hw/unittest/cache` |
| Counters, saturation, first-fault capture and injection work | `hw/unittest/ecc_status` |
| Counters are readable over SBA and faults are observable on the T0 path | `hw/unittest/t0_dbg` transcript |
| Every SBA-accepted address is claimed by exactly one slave; the window gap is rejected | containment test in `hw/unittest/ecc_status` and the T0 TB |
| The status window cannot read or write SRAM and SRAM accesses cannot alias into the status block | containment test |
| The injection register flips exactly one bit on one read and is off outside bring-up | `hw/unittest/ecc_status` plus security-review addendum |
| No timing-model divergence | `model_parity` cases for cache/LMEM traffic |
| Area and timing cost | synthesis report against the T0 baseline |

CI hygiene: every new bench gets a catalog lane only when its Makefile target
exists; `python ci/testcase.py lint` must report the new count. The lanes
removed on 2026-11-20 come back under the same ids (`hw-ecc`, `hw-ecc-ram`)
with `touches` naming the real files.

## 6. G1 exit criteria for the ECC item

The ECC item leaves `BLOCKED` only when all of the following exist:

1. Codec and ECC RAM benches green in CI.
2. LMEM and cache benches green with injected correctable and uncorrectable
   errors.
3. A T0 transcript showing boot, injection through the debug path, counter and
   first-fault readback.
4. The security-review addendum for the widened SBA window and the injection
   register is approved, and the decoder-agreement/containment test is green.
5. A recorded area/timing delta; parity cases pass or the SimX model is updated.
6. A recorded test-SRAM disposition with evidence.
7. Independent review signoff, and updated checklist, baseline and audit rows.

Until then the audit keeps ECC as `BLOCKED` and G1 as `NOT PASSED`.

## 7. Test SRAM recommendation

**Recommendation: protect the test SRAM with the same SECDED wrapper, 64+8 per
64-bit lane, byte-enable RMW, counters in the status block.**

Rationale:

- At T0-A the only array in the debug harness is the test SRAM. Without
  protection, T0 silicon has no ECC-bearing array, so checklist §7 step 6
  (inject a correctable and an uncorrectable error through the debug path,
  confirm the counters) cannot be run at all, and the readout path has no real
  source to prove.
- The wrapper, codec and counters are already built and benched for the caches;
  the marginal RTL is one wrapper instance and a 576-bit line instead of 512
  (12.5% more bits: 256 Kbit on a 2 Mbit array), plus one cycle on each 4-byte
  SBA store while it performs the RMW. At JTAG bring-up rates that cycle is
  irrelevant.
- It turns the existing JTAG memory test into the ECC bring-up test, and it
  keeps a single codec in the tree instead of a second, test-only encoding.

Costs and risks: 12.5% more array bits and a longer store path on the debug
port; a double-bit error in the test SRAM now invalidates a line rather than
returning it silently, which is the desired behaviour but must be documented in
the bring-up procedure. Protection does not move the array: the wrapper sits
behind the same 0x8000_0000 window, so the security review's
window-equals-memory property still holds, and the containment test runs with
the ECC-enabled SRAM rather than a stub.

Fallback if area or schedule forces a cut: parity per 64-bit lane (8 bits per
line, 1.6% overhead) with a sticky counter, no correction. This still gives a
real observable fault path, but it cannot demonstrate correction, so the
checklist step would have to be rewritten to say "detect" rather than "correct
and confirm". Leaving the array unprotected is the third option and is
acceptable only if the ECC silicon evidence moves to T0-B; it must then be
recorded as a deferral, not as compliance.

## 8. Risks and open questions

| Risk | Impact | Mitigation |
|---|---|---|
| Codeword-width policy not signed off | Rework of codec and all three arrays | S0 gate; §2.1 |
| Uncorrectable errors are only flagged, not signalled per request | Silent corruption between fault and the next counter read | Sticky flag plus line invalidation in caches; record as T0-B item |
| RMW adds a cycle to partial writes | `model_parity` divergence on store-heavy cases | Measure in S3/S4; model it in SimX in the same change |
| Decode adds delay after the array read | Cache pipeline timing | Measure at S4; keep decode combinational in the response stage |
| Tag arrays remain unprotected | Undetected tag corruption | Recorded exclusion with rationale; revisit for T0-B |
| No scrubber | Latent correctable errors are invisible until read | Documented; T0-B item |
| No T0-A arrays besides the test SRAM | ECC silicon evidence otherwise impossible | §7 recommendation |
| Widening SBA changes a surface the security review calls the block's main containment guarantee | Debug escape, or a silent divergence between SBA, the demux and the SRAM | Delta review of the security review; two exact comparators from shared constants; boundary/aliasing containment test as an S5 gate |
| The injection register becomes a production backdoor | Arbitrary fault injection in a shipped part | Off by default, config-gated for bring-up, one-shot one-bit only, recorded in the security-review addendum and the checklist |
| Decoder drift when a later window is added | Overlapping decodes, aliasing, or an accepted address with no slave | One-hot demux assertion in the test; single-sourced window constants; the review's window-equals-memory rule |
| Area/timing not yet measured | Baseline claims unsupported | Synthesis report required at S7 |

## 9. Sequencing summary

1. S0 freeze (1–2 d) — decisions, register map and the scope of the security
   delta review.
2. S1 codec and S2 wrapper with their benches (8–12 d) — the foundation, and
   the two CI lanes that were removed come back here.
3. S3 LMEM (3–4 d) — the simplest real array; proves the bank integration.
4. S5 counters, CSR, security review and containment test (6–8 d) — can start
   once S2 lands, in parallel with S4; the review starts at S0.
5. S4 ICache/DCache (8–12 d) — the largest and highest-risk stage.
6. S6 test SRAM (3–4 d) — reuses S2 and S5.
7. S7 verification and records (4–6 d) — the evidence package for G1.

The commercial hold, G4 purchases, G5 implementation, G6 tapeout and the
production-release gate are untouched by this plan.
