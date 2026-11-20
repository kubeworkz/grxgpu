# G100-T0 ECC Closure — S0 Decision Signoff

**Status:** Draft, unsigned. Signoff turns this into the S0 gate record.
**Date:** 2026-11-20.
**Plan under signoff:** [G100-T0 ECC Closure Plan](../../proposals/g100_t0_ecc_closure_plan.md) (§2 decisions, §4 register map, §7 test-SRAM recommendation).
**Pinned source:** `ff550c27570f17b0c8242be42257043d3de4ffa7`, tree `cf6b2f8657fcba985dd9007fa403231c3d800301`.
**Configuration evidence:** proposed T0 `CONFIGS`, SHA-256 `cd5336232fa98454009574121e0b25cc98feb3530a50675874ba98738c154cda`, archived at [proposed-config.txt](../g100-t0-g1-audit-2026-11-20/proposed-config.txt). Resolved values used below: XLEN=32, L1 line 64 B, DCache word 8 B, DCache 1 bank × 4 ways, ICache word 4 B, LMEM 16 KB × 4 banks.

Each decision gets one signature. `Accept with condition` requires the condition text to be appended to this record; `Reject` returns the decision to the plan.

**Signoff rule:** S0 is closed only when every decision is `Accept` or `Accept with condition`, the conditions are written down, and the Architecture and Verification signatures are present. No RTL starts before that.

---

## 1. Signoff summary

| ID | Decision | Chosen option | RTL evidence | Signature |
|---|---|---|---|---|
| D1 | Codeword width | Hsiao SECDED (32,39) and (64,72); 32+7 for LMEM/ICache slices at XLEN=32, 64+8 for DCache and XLEN=64 | `VX_local_mem.sv:264-270`, `VX_cache_data.sv:185-200`, `VX_cache_tags.sv:66`, `VX_config.toml:206,210,220,265,266` | ☐ |
| D2 | Correctable errors | Correct, count, latch first; no bus error or exception | `VX_mem_bus_if.sv:27-40` (no error field) | ☐ |
| D3 | Uncorrectable errors | Never silently correct; LMEM sticky flag, cache line invalidate; no per-request signalling | `VX_cache_tags.sv:119,132,135`; `VX_mem_bus_if.sv:37-40` | ☐ |
| D4 | Counters | 32-bit saturating per array, plus first-fault record (array, bank, way/set, word, syndrome); no per-bank counts | `VX_local_mem.sv:264-306`; `VX_cache_data.sv:123-200`; `VX_config.toml:230,266` | ☐ |
| D5 | Partial writes | Read-modify-write only; full-codeword writes bypass; one extra read cycle | `VX_sp_ram.sv:43-46,81-84`; `VX_local_mem.sv:295`; `VX_cache_data.sv:172` | ☐ |
| D6 | Line-clear encoding | Forward-looking: any line clear added in S4 writes encoded zeros | `VX_cache_data.sv:172,180`; `VX_sp_ram.sv:17-30,81-84` | ☐ |
| D7 | Scope exclusions | Tags and dirty-byte masks unprotected at T0 | `VX_cache_tags.sv:66,119,207-220`; `VX_cache_data.sv:123-130` | ☐ |
| D8 | Scrub | No background scrubber at T0 | No scrub path in `VX_local_mem.sv` or `VX_cache_*.sv` | ☐ |
| D9 | Decode contract | 64 KB status window at 0x8010_0000, two exact comparators, gap rejected; delta review + containment test | `VX_dm_sba.sv:55,90`; `VX_t0_test_sram.sv:51`; `VX_mem_bus_if.sv:20` | ☐ |
| D10 | Injection | `{array, bank, lane, bit, double}`, one-shot, off by default | `VX_config.toml:230,266`; `VX_t0_dbg_tb_top.sv:143` | ☐ |
| D11 | Readout shape | Line-granular reads, total decode, hold valid until ready | `VX_mem_bus_if.sv:17-32`; `VX_dm_sba.sv:48,55,58,82,111-119`; `VX_t0_core_attach.sv:114-117,126,142-154` | ☐ |
| D12 | Placement and gating | Demux + status block inside `VX_t0_dbg_top`; SBA-only writes; core writes ignored | `VX_t0_dbg_top.sv:76-77,206-211`; `VX_t0_dbg_tb_top.sv:135-143`; `VX_t0_mem_arb.sv` (owner internal) | ☐ |
| D13 | T0-A evidence | TSRAM-only counters; three-array counters simulation evidence until a cluster build | `VX_t0_dbg_tb_top.sv:143`; `VX_mem_unit.sv:219`; `VX_cache.sv:309` | ☐ |
| D14 | Test SRAM | Protect with SECDED 64+8 per 64-bit lane, RMW, counters; parity fallback | `VX_t0_test_sram.sv:46-65`; `VX_dm_sba.sv:58` | ☐ |

---

## 2. Decision records

Each record is: chosen option, the pinned-RTL evidence behind it, the condition to check, and the signature slot.

### D1 — Codeword width

**Chosen option.** Parameterised Hsiao SECDED with (32, 39) and (64, 72) codewords: 32+7 for 32-bit words, 64+8 for 64-bit words. At the T0 config that is LMEM 32+7 (4 B words), ICache 32+7 per slice (16 slices per 64 B line), DCache 64+8 per slice (8 slices per 64 B line). The baseline's "64+8" applies unchanged to 64-bit words and XLEN=64 builds. Pairing two 32-bit LMEM words into one 64+8 codeword is rejected because it turns every 4-byte store into a wider read-modify-write for no coding benefit.

**Pinned-RTL evidence.**
- LMEM word size is `VX_CFG_XLEN/8` = 4 B and the bank is a `VX_sp_ram` with `WRENW = WORD_SIZE` (`hw/rtl/mem/VX_local_mem.sv:264-270`).
- DCache word is 8 B and the line 64 B at the proposed config (`VX_config.toml:206,210,220`; resolved values in the archived config).
- ICache word is 4 B (`hw/rtl/VX_gpu_pkg.sv:1288`), line 64 B.
- Data arrays are `VX_sp_ram` slices with byte enables (`hw/rtl/cache/VX_cache_data.sv:185-200`), so per-word protection is structural, not an add-on.

**Cross-document caveat.** Accepting 32+7 for the 32-bit LMEM and ICache slices requires an explicit baseline amendment, not a checklist-only edit; DCache and XLEN=64 builds stay 64+8. The sites that still assume 64+8 on all three arrays or 12.5% overhead are:

- Requirement text: `docs/proposals/g100_production_baseline.md:207` (ECC row) and `:299-301` (ECC paragraph); `docs/grxgpu_g100_t0_tapeout_checklist.md:110-112` (SECDED width), `:122-124` (72-bit injection) and `:127-129` (12.5% area).
- Derived estimates: `docs/proposals/g100_production_baseline.md:211` (0.2 mm² ECC) and `:46` (10.8 mm² with ECC); `docs/grxgpu_g100_t0_tapeout_checklist.md:9` (header 10.8 mm²) and `:151-154` (10.8 mm² including ECC).
- Unaffected: the test-SRAM 64+8-per-64-bit-lane figures in the plan §7 and the audit's `:108`.
- Ready-to-apply amendment: [D1 32+7 baseline and checklist amendment](../../proposals/g100_t0_ecc_d1_32_7_amendment.md).

**Condition to check.** Confirm the XLEN=64 build really uses 72-bit words in LMEM and that both widths instantiate in the codec bench.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D2 — Correctable errors

**Chosen option.** Correct silently, count once, latch the first fault; no bus error, no exception.

**Pinned-RTL evidence.** The memory response struct carries only `data` and `tag` (`hw/rtl/mem/VX_mem_bus_if.sv:37-40`); there is no error bit to raise without changing every cache, LSU and local-memory port. Counters plus a sticky flag fit the existing interfaces.

**Condition to check.** Confirm no consumer already assumes a response bit pattern that a corrected word would break; sweep the corrected word through the cache and LSU benches in S3/S4.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D3 — Uncorrectable errors

**Chosen option.** Never silently correct. LMEM returns the stored word and sets a sticky per-array flag; a cache invalidates the line so the next access refetches. Per-request error signalling (bus error or precise exception) is a T0-B item.

**Pinned-RTL evidence.** The tag store already has a per-way invalidate path (`hw/rtl/cache/VX_cache_tags.sv:114,119,132`), so line invalidation is expressible without a new interface. The LMEM bank has no error port (`hw/rtl/mem/VX_local_mem.sv:264-306`), which is why the LMEM case is a sticky flag only.

**Condition to check.** Confirm an invalidated line cannot be re-read from stale data in the data array before refill (data array is way-addressed and tag-gated, so invalidation must prevent the hit).

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D4 — Counters

**Chosen option.** 32-bit saturating corrected/uncorrected counters per array, plus a sticky first-fault record (array, bank, way/set or line, word, syndrome, correctable/uncorrectable). Per-bank counters are omitted; the fault record names the bank.

**Pinned-RTL evidence.** LMEM has four banks (`VX_config.toml:266`; the per-bank loop is `hw/rtl/mem/VX_local_mem.sv` `g_data_store`), DCache has one bank and four ways (`VX_config.toml:206,230`), and the cache data array folds the way into the address (`hw/rtl/cache/VX_cache_data.sv` `data_addr`). One counter per array therefore needs bank/way in the fault record to be actionable.

**Condition to check.** Confirm saturation and clear-on-write semantics match the firmware/JTAG tool expectations documented in the bring-up procedure.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D5 — Partial writes

**Chosen option.** Read-modify-write is the only partial-write path; full-codeword writes bypass the read. An extra read cycle precedes a partial write; nothing else in the bank changes.

**Pinned-RTL evidence.** `VX_sp_ram` has one address port and merges byte-enabled writes in the array (`hw/rtl/libs/VX_sp_ram.sv:43-46,81-84`), so check bits cannot be updated from a partial write without first reading the old codeword. LMEM already has a read-after-write hazard interlock that the RMW must not defeat (`hw/rtl/mem/VX_local_mem.sv:295-306`), and the cache slice write path is fill/store only (`hw/rtl/cache/VX_cache_data.sv:172`).

**Condition to check.** Confirm the extra read cycle is visible in the cycle budget and does not break the LMEM hazard interlock or the cache pipeline contract; measure in S3/S4.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D6 — Line-clear encoding

**Chosen option.** Forward-looking rule for S4: if S4 adds a data-array line clear, or any path that writes a whole line without the fill encoder, it must write encoded zeros so the line has valid check bits. The decision does not describe current behaviour and does not require adding a clear.

**Pinned-RTL evidence.** The pinned data array is not written on init or flush: `slice_write` covers fill and hit-store only (`hw/rtl/cache/VX_cache_data.sv:172,180`), `init` reaches only the dirty-byte masks, and the RAM defaults to `INIT_ENABLE=0` / `INIT_VALUE=0` with the ASIC init macro empty (`hw/rtl/libs/VX_sp_ram.sv:17-30,81-84`). The plan was corrected on 2026-11-20 to state the rule this way.

**Condition to check.** S4 must confirm that any line-clear path it introduces goes through the encoder; if S4 adds no clear, the decision is satisfied by construction. Do not add a data-array clear solely to satisfy it.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D7 — Tag and dirty-byte exclusions

**Chosen option.** Tag arrays and dirty-byte masks are unprotected at T0; the requirement covers the three data arrays only. Recorded as a deliberate exclusion, not an oversight.

**Pinned-RTL evidence.** The tag store is one folded RAM with per-way write enables and `TAG_ENTRYW = sectors + tag` (`hw/rtl/cache/VX_cache_tags.sv:66,207-220`), so per-way ECC would need per-way codewords and a change to the tag-compare path. Dirty bytes are a separate 1-bit LUTRAM store (`hw/rtl/cache/VX_cache_data.sv:123-130`).

**Condition to check.** Keep the exclusion visible in the checklist and audit so it is not read as full-array coverage.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D8 — No scrubber

**Chosen option.** No background scrubber at T0; a correctable error is observed only when the word is read.

**Pinned-RTL evidence.** Neither `VX_local_mem` nor the cache data path has a walker or periodic read; there is no idle-time memory engine in the T0 top (`hw/rtl/dbg/VX_t0_dbg_top.sv`). Counters therefore record accessed words only.

**Condition to check.** Say so in the bring-up procedure; do not present the corrected counter as an inventory of latent errors.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D9 — Address-decode contract and window

**Chosen option.** A 64 KB status window at 0x8010_0000 (`addr[31:16]==16'h8010`), admitted by a second exact comparator in SBA; the SRAM window and decode are unchanged. Every accepted address is claimed by exactly one slave; the 0x8004_0000–0x800F_FFFF gap and everything above 0x8010_FFFF stay rejected. The change is gated by a delta review of the security review and a containment test.

**Pinned-RTL evidence.**
- SBA compares byte bits [31:18] against `14'h2000` (`hw/rtl/dbg/VX_dm_sba.sv:90`) and drives the bus with the line address `addr_q[31:6]` (`:55`).
- The SRAM compares line bits [25:12] against `14'h2000` (`hw/rtl/dbg/VX_t0_test_sram.sv:51`); since line = byte[31:6], those are the **same byte bits [31:18]**.
- The bus address width is `MEM_ADDR_WIDTH - CLOG2(DATA_SIZE)` = 26 (`hw/rtl/mem/VX_mem_bus_if.sv:20`), so the demux compares `line[25:10]` for the 64 KB window — the same bits as SBA's `addr[31:16]`.
- The security review's containment claim is the "window equals memory" property (`docs/proposals/g100_t0_debug_security_review.md` §5).

**Condition to check.** The containment test must enumerate the aligned boundaries (0x7FFF_FFFC, 0x8000_0000, 0x8003_FFFC, 0x8004_0000, 0x800F_FFFC, 0x8010_0000, 0x8010_FFFC, 0x8011_0000, 0x8020_0000), register offsets and random addresses from both masters, and assert one-hot demux selection.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D10 — Injection register

**Chosen option.** One-shot `{array, bank, lane, bit, double}` register; applies to the next read of the selected array and bank; off by default and enabled only in the bring-up configuration; can only flip one bit and never write data or check bits.

**Pinned-RTL evidence.** LMEM has four banks (`VX_config.toml:266`), so an "any bank" injection is not reproducible. The T0-A harness has no LMEM/cache arrays (`hw/unittest/t0_dbg/VX_t0_dbg_tb_top.sv:143`), so absent-array injection must be rejected rather than left dangling. No injection port exists today; the register is a new, reviewed surface.

**Condition to check.** Security review addendum records the default, the enable mechanism and the removal path; the test proves exactly one fault and no effect when disabled.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D11 — Line-granular, total readout

**Chosen option.** The status slave is 512-bit/64-byte-line; reads return the whole addressed line; writes decode from the byte enables; it answers every line in its window (zeros for unmapped) and holds `rsp_valid` until `rsp_ready`.

**Pinned-RTL evidence.**
- `VX_mem_bus_if #(.DATA_SIZE(64))` is 64 **bytes** wide: 512-bit data, 64-bit byteen, 26-bit line address (`hw/rtl/mem/VX_mem_bus_if.sv:17-32`).
- SBA extracts a 32-bit lane at `{lane_q,5'b0}` with `lane_q = addr[5:2]` and places write data at the same lane; byteen is `64'hF << addr[5:0]` (`hw/rtl/dbg/VX_dm_sba.sv:48,58,82`).
- Core reads reach the bus with `req_data = '0` and no byteen; only core writes set data/byteen (`hw/rtl/dbg/VX_t0_core_attach.sv:126,142-154`). Responses are extracted by lane (`:114-117`), so a line-granular response serves both masters.
- An unanswered request times out into `ST_DRAIN`, which has no timeout (`hw/rtl/dbg/VX_dm_sba.sv:111-119`), and the arbiter holds the core until the response arrives.

**Condition to check.** Total-decode test: unmapped register 0x120 and an unmapped line in the window must return zeros and complete, not hang. Line-read test at offsets 0x00 and 0x04 must land each register at its byte offset.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D12 — Placement and master gating

**Chosen option.** Demux and status block inside `VX_t0_dbg_top`, between the arbiter and the `mem_bus_if` port, on an internal 64-byte interface. The arbiter exports its owner so writes are SBA-only; core writes are ignored; the SRAM window and decode are untouched.

**Pinned-RTL evidence.** The arbiter's output is wired directly to the top-level `mem_bus_if` port (`hw/rtl/dbg/VX_t0_dbg_top.sv:206-211`); the TB pass-through connects that port to the SRAM (`hw/unittest/t0_dbg/VX_t0_dbg_tb_top.sv:135-143`). A demux in the TB would not exist in silicon. `VX_t0_mem_arb` keeps `owner` internal and the bus carries no master id, so an owner sideband is required to gate writes.

**Condition to check.** The T0 TB must show the status block answering through the chip top, and the containment test must prove a core write to `INJECT` has no effect.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D13 — T0-A evidence scope

**Chosen option.** T0-A evidence is TSRAM-only: `CAPABILITY` marks LMEM/ICACHE/DCACHE absent, injection for them is rejected, and the T0 transcript evidences TSRAM counters. The three-array counters are simulation evidence in their own benches until a cluster-level build exists. The arrays are still required to be protected in RTL.

**Pinned-RTL evidence.** The T0 harness instantiates the core and the test SRAM only (`hw/unittest/t0_dbg/VX_t0_dbg_tb_top.sv:143`); LMEM is instantiated in `VX_mem_unit` (`hw/rtl/core/VX_mem_unit.sv:219`) and the caches in `VX_cache` (`hw/rtl/cache/VX_cache.sv:309`), neither of which is in the T0-A top.

**Condition to check.** The audit and checklist must not claim T0 silicon evidence for the three arrays; the G1 exit criterion is worded TSRAM-only.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

### D14 — Test SRAM protection

**Chosen option.** Protect the test SRAM with the same SECDED wrapper, 64+8 per 64-bit lane (8 lanes per 512-bit line), byte-enable RMW and counters in the status block. Fallback if area or schedule forces a cut: per-lane parity with a sticky counter; leaving it bare is a recorded deferral to T0-B, not compliance.

**Pinned-RTL evidence.** The SRAM is a plain `reg [511:0] mem [4096]` with 64 byte enables (`hw/rtl/dbg/VX_t0_test_sram.sv:46-65`); SBA stores are 4 bytes (`hw/rtl/dbg/VX_dm_sba.sv:58`), so every SBA store is a partial codeword and takes the RMW path. It is the only array available to carry ECC in T0-A.

**Condition to check.** Area delta recorded; the JTAG store/read test still passes through the RMW path; the address window is unchanged.

**Signoff.** ☐ Accept ☐ Accept with condition ☐ Reject — Name: __________ Date: __________ Notes: ______________________

---

## 3. Open caveats carried into signoff

| # | Caveat | Effect on signoff |
|---|---|---|
| C1 | D6 is forward-looking: the pinned RTL does not write the data array on init/flush (`hw/rtl/cache/VX_cache_data.sv:172,180`; `VX_sp_ram.sv:17-30,81-84`) | Accept with the S4 condition; no data-array clear is required to satisfy it |
| C2 | D3 relies on a sticky flag for LMEM because the response struct has no error field (`VX_mem_bus_if.sv:37-40`) | Accept with the T0-B item recorded |
| C3 | D9/D11 compare the same byte bits in two representations (byte address at SBA, line address at the demux) | Accept with the boundary/one-hot test as the condition |
| C4 | D13 narrows T0 silicon evidence to the TSRAM | Accept only with the audit/checklist wording updated |
| C5 | The test-SRAM decision (D14) is a recommendation, not an approved baseline change | Accept, or record the parity fallback or deferral explicitly |

## 4. Gate record

**Outcome:** ☐ S0 closed ☐ S0 closed with conditions ☐ S0 rejected

**Conditions / actions:**

1. ______________________________________________________________
2. ______________________________________________________________
3. ______________________________________________________________

**Architecture:** ______________________ Date: __________
**Verification:** ______________________ Date: __________
**Security review (D9–D12):** ______________________ Date: __________
**Program (scope and holds):** ______________________ Date: __________

**Recording note.** This signoff covers the S0 design decisions only. It does not authorize starting RTL, does not change the G0 commercial hold, G4 purchases, G5 implementation, G6 tapeout or production release, and does not close the G1 ECC blocker. The plan's exit criteria in §6 remain the closure condition.
