# P0-C integration package — reconciliation memo

**Status:** Draft reconciliation for owner review. No P0-C selection, register activation, or signature is asserted. **P0-C remains OPEN.**<br>
**Prepared:** 2026-10-18<br>
**Review sequence proposed:** P0-C-a bounded analysis by 2026-11-20; P0-C-b owner decisions targeted 2026-12-12. The Dec 3 architecture-review target remains separate.

## Read first: dispositions of supplied findings

| ID | Reconciliation |
|---|---|
| F-1 Schedule | Confirmed conflict: the mesh checklist targets Dec 3, 2026; current P0-C target is Dec 12. Proposed split: bounded ranges and unresolved/deferred labels by Nov 20; decisions only on Dec 12. The scale/workload envelope and source/receiver conclusions stay OPEN at Dec 3 unless their inputs are resolved earlier. |
| F-2 Batch semantics | Confirmed ambiguity. “Batch 16” is a batch-size statement; the agenda’s “one vector per shot” points toward Case A, but it does not define physical firing versus full logical-vector completion. Keep Case A and Case B distinct below. The supplied claim that Case B exceeds one 57.6-GB/s module by ~22% is not supported by per-direction arithmetic; it adds full-duplex directions together. |
| F-3 Weight updates | Conditional, not a settled device limit. The source plan uses `Tw = 10 µs` as a *plausible thermo-optic model point*; it does not establish a measured thermal time constant for the selected primitive. If a complete weight-set update takes 10 µs, 25 MS/s vector shots imply reuse over at least 250 shots (at least 16 whole batches of 16, i.e. 256 shots); updating every 16-shot batch would request 1.5625 M updates/s. The board plan instead identifies TFLT as Pockels-class with ~25-ps optical settling. Optical settling and digital weight-load time must be budgeted separately. No primitive is selected by this memo. |
| F-4 Primitive/spec | Not verifiable from this workspace: the cited `PTA-MESH-§2-SPEC-001` is absent. Do not state that coherent encoding or physical N=8–16 is a ratified baseline. Request the exact revision/path/hash; until received, treat both as unverified assumptions. |
| F-5 Logical/physical mapping | Material dependency. If a 16×16 physical mesh is assumed and a full logical 128-output × 64-input matrix is tiled, the arithmetic is 8×4 = 32 physical tile firings per logical vector, with partial-sum handling across four K tiles. A 64→16 canary FC3 instead requires 1×4 = 4 firings under that same assumed mapping. This is a model of mapping, not evidence of a built N=16 primitive. |
| F-6 Link configuration | 57.6 GB/s/direction is a documented sizing assumption: 16 lanes × 32 GT/s ÷ 8 × 0.9 assumed efficiency. It is not a selected endpoint configuration. Record a sizing assumption by Nov 20; defer selected IP/config evidence to the proposed V6/2027-02-12 dependency only if the owner register confirms it. |
| F-7 Precision | Partly consistent, partly unresolved. The canary plan states 6-bit activations, tile-trained 6-bit weights, and an 8-bit output representation. The board plan’s v1 budget states a 7-bit ADC. ADC conversion precision versus logical output encoding must be reconciled; the supplied 12-bit ADC assertion is not substantiated by a local §2 spec. |
| F-8 Status | Required: P0-C remains **OPEN**. A bounded-for-study disposition or provisional sizing point does not close it. |

## 1. Schedule reconciliation proposal

The cited owner register v1.0 and its rows are not present in this workspace. The table below transcribes the supplied row IDs as **proposed changes**, not as a verified edit or supersession of a controlled register. See the [proposed register v1.1 change record](grxcp_p0c_owner_register_v1.1_proposal.md).

| Supplied row | v1.0 date | Proposed split | Dec 3 review treatment |
|---|---:|---|---|
| R-04 — §1 scale/workload envelope | Nov 20 | Bounded-range record Nov 20; selected envelope Dec 12 | Keep scale/workload row OPEN |
| R-08 — §1 P0-C reconciliation | Nov 20 | Preliminary reconciliation Nov 20; final Dec 12 | Preliminary only; no selection |
| R-13 — §2 source/receiver | Nov 20 | Bounded analysis Nov 20; selected values Dec 12 | Keep source/receiver row OPEN absent evidence |
| R-17 — §2 link budget | Nov 20 | Bounded model Nov 20; selected configuration/values Dec 12 or later dependency | Keep assumptions labeled; no selected link claim |
| R-36 — §3 §5.4 UCIe IP record | Nov 20 | Sizing-assumption record Nov 20; selected config proposed for 2027-02-12 with V6 | No selected configuration by Dec 3 |

**Recommended sequence:** P0-C-a (Nov 20) publishes ranges, model inputs, confidence classes, and “bounded for study”/“deferred” entries only. P0-C-b (Dec 12) is the target for Dave Cook to select, bound, or defer D-1…D-6 with rationale and evidence. Nov 20/Feb 12 row IDs and dates remain proposals pending the controlled register and owner approval.

## 2. Technical reconciliation and corrected calculations

### 2.1 Define the traffic basis before comparing to UCIe

Calculations below use packed 6-bit activation inputs, 8-bit logical outputs, decimal GB/s, and no packet/header overhead unless specifically shown. The canary's 6-bit weights are resident; traffic to load/program them is modeled separately. They use the full-duplex 57.6-GB/s-per-direction figure from `pta_chiplet_link.py` as an assumed cap; inbound and outbound are checked separately. These are ideal packed payload calculations, not the existing X2 model: X2 uses one byte per operand/ADC code and four bytes per accumulated output and accounts for padding/K tiling. Recompute after output accumulation, encoding/framing, selected FLIT mode, and physical mapping are known. No PCIe/UCIe endpoint configuration or physical measurements are available.

| Case | Meaning of “shot” and batch | Per firing payload (in / out) | At the stated rate | Link implication |
|---|---|---:|---:|---|
| A-FC3 | One logical 64→16 vector per shot; batch 16 means 16 sequential vector shots | 48 B / 16 B | At 25 M vector shots/s: 1.20 / 0.40 GB/s | One module on payload; 16-output canary case |
| A-full | One logical 128×64 vector per shot; batch 16 means 16 sequential vector shots | 48 B / 128 B | At 25 M vector shots/s: 1.20 / 3.20 GB/s | One module on payload; not the canary’s 16-output FC3 |
| B-FC3 | One firing represents 16 simultaneous 64→16 vectors | 768 B / 256 B | At 25 M batch firings/s: 19.20 / 6.40 GB/s | One module on payload; 400 M logical vectors/s assumed |
| B-full | One firing represents 16 simultaneous full 128-output vectors | 768 B / 2,048 B | At 25 M batch firings/s: 19.20 / 51.20 GB/s | One module on payload, but only 6.40 GB/s outbound headroom before any overhead |
| B-full + 12% overhead | Same as B-full; 12% is an illustrative overhead assumption, not selected IP data | 768 B / 2,048 B | 21.504 / 57.344 GB/s | Still nominally below 57.6 outbound by 0.256 GB/s (0.44%); not a robust margin |

At Case B full-output and 25 M *batch firings*/s, 70.4 GB/s is the sum of two directions and cannot be compared with a full-duplex per-direction module rating. The modeled no-overhead outbound ceiling is 28.125 M batch firings/s; with the illustrative 12% multiplier it is 25.112 M/s. Neither overhead nor sustainable rate is measured. If instead one UCIe module is half-duplex or imposes different directional sharing, use the selected IP contract, not this assumption.

Weights change the result if loaded over the same link. The full logical 128×64 six-bit image is 6,144 B; the 64×16 canary submatrix is 768 B. At Case A 25 M vector/s, batch size 16 implies 1.5625 M batches/s. Reloading the full 128×64 weight image once per batch adds 9.60 GB/s inbound; activation plus that reload is 10.80 GB/s inbound. For FC3’s 64×16 weights, reloading once per 16-vector batch adds 1.20 GB/s, making 2.40 GB/s inbound including activations. These are explicit reload scenarios, not a claim that weights must reload each batch. If retained across Q batches, divide the image-load term by Q. At Case B’s 25 M batch firings/s, reloading the full image every firing would add 153.6 GB/s inbound and require at least three assumed modules; the payload-only B cases therefore require weight residency across multiple firings.

### 2.2 Physical firings, thermal assumptions, and analog rate

For an assumed N=16 mesh, full logical 128×64 mapping gives 32 physical tile firings per vector; the canary FC3 64→16 mapping gives four. Thus 25 M logical vectors/s would require 800 M or 100 M aggregate physical tile firings/s respectively if all firings are serialized in the count. Parallel physical tiles change per-tile rate and area, not total firing work. The N=16 mapping remains unverified and cannot be written as an implementation requirement.

The supplied 10-µs thermo-optic statement is not supported as a measured device constant by the local docs: the source calls `Tw = 10 µs` a plausible thermo-optic model point. Conditionally, if a complete weight-set update incurs that delay, 25 M vector shots/s imply 250 shots during one update interval. A batch of 16 spans only 640 ns; 16 batches (256 shots) span 10.24 µs. Thus the model requires weights reused across roughly 16 batches, not merely fixed for one batch, if that full 10-µs cost is serial and applies to a whole weight set. This does not price an EIC banked/overlapped load path. TFLT’s ~25-ps Pockels optical settling in the board plan does not establish the EIC’s weight-load bandwidth.

The supplied “12.5 GHz analog bandwidth” claim is rejected: 25 MS/s has a 12.5-MHz Nyquist frequency for an ideal band-limited sampled signal, not 12.5 GHz. Even 12.5 MHz is only a sampling-theory reference, not an analog front-end requirement for an unspecified waveform. Derive actual bandwidth/settling from modulation waveform, hold/settle tolerance, receiver/TIA response, and device data. UCIe NRZ signaling is a separate link layer and does not specify the optical analog bandwidth.

### 2.3 Precision and detector claims

Keep three quantities distinct: ADC conversion resolution, logical result encoding, and any I/Q readout. The local board plan v1 gives a 7-bit ADC target; the first-board canary says an 8-bit output ADC/representation. Clarify whether the latter is ADC bits or post-conversion output format. Do not repeat the supplied “12-bit ADC” as fact without the missing spec artifact. Similarly, 128×2 I/Q ADC channels and 512 photodiodes are conditional examples only; they require a selected coherent/direct-readout mapping. An N=16 tiled design would have different physical detector counts and readout reuse. Source power, loss, receiver noise, TIA bandwidth, and thermal limits remain **unknown/unmeasured**; no operating point is proven feasible by this package.

## 3. Dec 3 architecture review impact

- Carry the scale/workload envelope and source/receiver decisions **OPEN** through Dec 3 if they depend on P0-C-b; use P0-C-a’s bounded analysis only as review input.
- Do not report §2 signal representation or mesh connectivity as closed from the unavailable §2-SPEC-001. Existing checklist rows remain governed by their actual signed artifacts; this package supplies no signatures.
- The register statuses “closed conditional,” dates, and claimed Nov 6 signatures in the supplied text are not independently verifiable here. The review chair should attach their evidence IDs and hashes before using those statuses.
- Review record must state: **“P0-C remains OPEN. The 128×64 / batch-16 / 25-MS/s point is provisional engineering sizing only, not an approved requirement. Model calculations are not optical-device or hardware qualification evidence.”**

## 4. Evidence and provenance limits

The workspace contains the P0-C agenda, tracker, canary plan, board plan, and analysis scripts, but not `PTA-MESH-OWNER-REG-001 v1.0`, `PTA-MESH-§2-SPEC-001`, or `PTA-MESH-§1-EV-001`. Their row IDs, assumed coherent N=8–16 spec, 12-bit ADC claim, signatures, and dates in the supplied package are therefore treated as externally supplied, unverified inputs. This memo does not mark those artifacts present, activate a register revision, sign a decision, or change P0-C from OPEN.
