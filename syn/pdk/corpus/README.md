# Conformance corpus generators

Generates the 104 layouts listed in
[docs/proposals/pdk_corpus_manifest.yaml](../../../docs/proposals/pdk_corpus_manifest.yaml),
as assumed by [the harness specification](../../../docs/proposals/open_pdk_harness_spec.md) §2.

**Status:** skeletons. Each layout is a stylised construction that puts one rule
family at its limit or just past it. These are not library cells, and they have
not been checked against any real deck: `layers.example.json` and
`rules.example.json` are placeholders and say so in their headers. The harness
supplies the layer map and rule table that ship with the PDK descriptor.

## Running

Requires the KLayout Python module and PyYAML.

```bash
python syn/pdk/corpus/generate.py --list                 # case inventory
python syn/pdk/corpus/generate.py --out build/corpus     # write GDS + run.json
python syn/pdk/corpus/generate.py --out build/corpus --only rt-
python syn/pdk/corpus/generate.py --out build/corpus \
    --layers path/to/layers.json --rules path/to/rules.json
```

`run.json` records the manifest, layer map and rule table digests, plus the
shape count and SHA-256 of every layout, so a harness run can be tied to the
exact inputs that produced it.

## What is generated

103 layouts. `mem-01` is `status: exists` in the manifest and points at
[gen_16kb_sram.tcl](../../gen_16kb_sram.tcl), so the driver records it as
supplied instead of regenerating a layout the evidence manifest already holds.

| Category | Cases | Generator |
|---|---|---|
| memory | 8 | bitcell, array, decoder, sense amp, driver, straps, macro edge |
| standard-cell | 15 | frame plus gates; fill, tap, decap, antenna, level shifter, abutment |
| routing | 16 | width, spacing, notch, grid, via enclosure, slotting, via-in-pad |
| wells-and-taps | 10 | well spacing, taps, guard rings, latch-up distance, deep nwell |
| devices | 13 | gate length, fingers, contacts, endcap, matched pair, thick oxide |
| io-and-esd | 8 | pad, diode, clamp, coverage, guard ring, boundary |
| seal-and-scribe | 4 | corners, continuity, spacing, scribe structures |
| density-and-fill | 9 | density band, checkerboard, slotting, fill legality |
| regularity | 7 | poly, metal, contact and via arrays, gate array, tile |
| marginal | 8 | every limit hit exactly, so the deck must not flag it |
| cross-layer | 6 | contact-overlap prohibitions, well overlaps, block boundaries |

## Inputs

`layers.example.json` maps a symbolic name (`met1`, `via1`, `sab`, …) to a GDS
layer and datatype, plus `dbu_um`. `rules.example.json` carries `grid_um` and
the limits the generators use: width, spacing, area, notch, enclosure, contact,
poly, endcap, well, tap, rail, cell, pad and density. Adding a technology means
supplying these two tables, not editing geometry — the same rule the descriptor
contract applies to the flows.

## What has been verified

- Every generated GDS reads back with a top cell and non-empty shape count.
- The single-layer routing and marginal cases were checked with KLayout's own
  `width_check`, `space_check`, `notch_check` and region area: clean cases sit
  exactly at the limit and report zero violations at that limit, and their
  violation twins report at least one. For example `rt-02` (spacing 140 dbu)
  reports nothing at 140 and one pair at 141, while `rt-03` (135 dbu) reports at
  140; `mg-07` (notch 100 dbu) reports nothing at 100 and one pair at 101.
- The min-area case covers 50,625 dbu² against a 50,000 dbu² requirement.

## What has not been verified

- Nothing here has been run against a real DRC/LVS deck. Cell-level cases are
  stylised and must be re-checked when a library and deck exist; expect to
  adjust geometry, not expectations.
- The manifest's LVS, PEX, Liberty and timing criteria are not exercised by
  these layouts — they are corpus inputs for the harness, which does not exist
  yet.
