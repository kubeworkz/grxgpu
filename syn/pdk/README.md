# PDK descriptors

The `syn/` flows take every technology value from a descriptor here instead of
naming libraries, cells or layers inline, so moving a flow to another process
is a new descriptor rather than a script edit. `sky130hd` is the default.

```bash
PDK=sky130hd openroad syn/gen_16kb_sram.tcl
syn/pdk/render.sh --pdk sky130hd syn/synth_grxgpu.ys /tmp/synth_grxgpu.ys
```

`PDK` selects `<name>.pdk` in this directory. Tcl flows `source pdk.tcl` and
call `pdk_load`, then read fields with `pdk <FIELD>`; Yosys flows are templates
whose `@<FIELD>@` placeholders `render.sh` expands from the same file.

## Fields

`KEY=VALUE`, `#` comments, values with spaces quoted. Anything a flow reads
must be present — `pdk_load` fails on a missing required field and `render.sh`
fails on an unresolved placeholder, so a half-filled descriptor cannot produce
a silently wrong result.

| Field | Meaning |
|---|---|
| `PDK_NAME`, `PDK_DESCRIPTION`, `PDK_NODE_NM` | Identity; `PDK_NODE_NM` drives no timing, only labels and scaling notes |
| `PDK_READY` | `1` when these are the values the flows should map against, `0` for a skeleton. `pdk_load` refuses a `0`, and CI requires a `1` to be complete |
| `PDK_LIBERTY` | Typical-corner `.lib` both the synthesis and RAM flows map against |
| `PDK_TECH_LEF`, `PDK_CELL_LEF` | Technology LEF and merged cell LEF |
| `PDK_POWER_NET`, `PDK_GROUND_NET` | Supply net names handed to `generate_ram` |

For `generate_ram` (`pdk_require_orram` enforces this set):

| Field | Meaning |
|---|---|
| `PDK_STORAGE_CELL`, `PDK_TRISTATE_CELL`, `PDK_INV_CELL`, `PDK_TAP_CELL` | Bit cell, read buffer, inverter, well-tap |
| `PDK_FILLER_CELLS` | Filler set, space separated |
| `PDK_MAX_TAP_DIST` | Tap spacing in µm |
| `PDK_ROUTING_LAYER` | `<layer> <pitch_um>` for signal routing |
| `PDK_VER_LAYER`, `PDK_HOR_LAYER` | `<layer> <pitch_um> <spacing_um>` power straps |
| `PDK_HAS_ORRAM` | `1` when the cell set above can build a macro, else `0` |

## Adding a technology

Copy `sky130hd.pdk`, fill in the new process's liberty, LEFs, cell set and
stack, and invoke the flows with `PDK=<name>`. A descriptor is usable for
synthesis with only the identity and library fields; `PDK_HAS_ORRAM=0` keeps
the RAM generator from being run against a cell set that has no tristate read
buffers or tap cells.

## A process whose libraries have not landed

`openrpdk28.pdk` is the 28 nm skeleton: identity filled, every library, cell and
layer field empty, `PDK_READY=0`. `pdk_load` refuses it and lists what the PDK
still has to supply, so no flow can report numbers against a process that has no
cells; the descriptor is usable the moment those fields are filled and
`PDK_READY` flips to `1`, with no script edit.

Descriptor paths are literal. An install elsewhere is a copied descriptor, not
a `PDK_ROOT` override — the descriptor is then the record of which library
revision a flow produced its numbers against.
