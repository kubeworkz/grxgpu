# P0-C PIC/EIC owner review agenda

**Status:** Review agenda; no geometry, workload, optical primitive, or physical shot-rate requirement is approved by this document. P0-C remains **OPEN**.<br>
**Decision owner:** Dave Cook (PIC/EIC and GPU workload/link authority)<br>
**Target:** Dec 12, 2026<br>
**Current sizing point for review:** logical 128×64, batch 16, 25 MS/s. This is a provisional engineering sizing assumption, based on the first-board canary and models—not a measured physical PTA capability or an approved customer workload.

## Decisions to make

1. **Workload and scope:** Is the first-board canary's 64→16 FC3 operation a valid sizing proxy, or should a separate GPU/customer workload drive this decision? The canary describes 1,000 logical vectors in jobs of 16 and says one vector is one shot; that is a workload convention, not a definition of one physical mesh firing. Confirm 6-bit activation/weight assumptions and distinguish ADC conversion bits from logical output encoding; label anything not owner-approved as a test assumption.
2. **Geometry meaning:** Does 128×64 describe logical tile dimensions for sizing? Confirm rows, columns, input/output mapping, padding/tiling, detector count, and usable versus nominal cells. Do not interpret it as selecting an optical primitive.
3. **Optical architecture boundary:** What primitive and signal representation are being evaluated (e.g. field/coherent versus power/intensity)? How do connectivity, summation/readout, signed values, accumulation, and output mapping implement the stated operation? Record alternatives and defer selection explicitly if unresolved. The approved 2-D direction alone does not answer this.
4. **Rate envelope and units:** Is 25 MS/s a useful provisional target, or should P0-C carry a bounded range or multiple operating points? Separately define (a) one physical primitive/tile firing, (b) one completed logical vector after all tiling/partial sums, and (c) one batch/job of 16 vectors. The agenda’s “one vector per shot” does not establish that those units are identical. Evaluate both Case A (16 sequential logical-vector shots per batch) and Case B (one firing represents 16 simultaneous vectors) until the owner selects a counting contract. State sustained versus peak, settling/calibration, duty, and weight-update/residency assumptions. Do not substitute modulator baud/line rate for optical shot rate.
5. **Receiver and source feasibility:** What measured or selected-IP values support detector count, receiver noise versus bandwidth/rate, responsivity, optical loss, source type/power/noise/wavelength, and thermal/safety limits? If no sourced values exist, record a bounded analysis range and its assumptions—not a pass.
6. **EIC/GPU feed constraints:** Confirm activation/weight residency, buffering and accumulation assumptions, whether the 57.6 GB/s per-direction UCIe-S module is a sizing assumption or selected configuration, and the resulting link/module range at each candidate operating point. Resolve enough to keep the operating point within the board path, or record the dependency and owner.

## Evidence to bring or request

- Workload/canary manifest, exact logical shapes and batch semantics; identify any customer workload separately and mark approval status.
- PIC block diagram and connectivity/readout sketch for the candidate primitive; EIC↔PIC boundary, converters, buffers, accumulator, clocks/resets, and resource counts.
- Source/receiver datasheets or authorized supplier/IP evidence with revision, operating conditions, and access-controlled evidence location. Record receiver noise-versus-rate, detector responsivity/count, source limits, and end-to-end loss budget; note missing parameters explicitly.
- Reproducible calculation inputs and outputs for link traffic, buffer demand, receiver/source power, and weight programming at proposed low/nominal/high rates. Include model revision/command and separate sourced facts from assumptions.
- Candidate operating-point table: geometry, batch, physical firings per logical vector, rate unit, precision, weight reload/residency, optical assumptions, separately reported per-direction payload and overhead, link/module count, receiver/source budget, limiting constraint, and confidence/evidence class (target, modeled, sourced, measured). Label whether traffic uses packed logical bytes or the wider X2 traffic model (byte operands/ADC codes and accumulated outputs); do not mix their results.
- Written disposition for each open choice: selected, bounded for study, or deferred—with rationale, owner, due date, dependency, and affected gate.

## Meeting closeout

Record whether to retain or revise **128×64 / batch 16 / 25 MS/s as provisional only**; do not label it a requirement until owner-approved workload and topology-specific evidence support it. Update the blocker tracker with dated decisions, evidence paths and hashes, and unresolved items. Preserve P0-C as **OPEN** until the geometry/rate/workload envelope and its source or explicit bounded operating points are approved. A model result is not optical-device or hardware qualification evidence.
