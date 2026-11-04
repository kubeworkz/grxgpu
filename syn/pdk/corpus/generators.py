"""Case geometry for the conformance corpus.

Each layout is a stylised construction, not a library cell: the object is to put
one rule family exactly at its limit, or just past it, so the deck comparison
has something to disagree about. Case ids, categories and expectations come
from docs/proposals/pdk_corpus_manifest.yaml; this module only supplies shapes.
"""

import math


# -- standard-cell scaffolding ------------------------------------------


def _std_frame(B, R, cols=1):
    w = R["cell_width"] * cols
    h = R["cell_height"]
    B.rect("nwell", 0.0, h / 2, w, h / 2)
    B.rect("met1", 0.0, 0.0, w, R["rail_width"])
    B.rect("met1", 0.0, h - R["rail_width"], w, R["rail_width"])
    B.rect("tap", 0.04, 0.04, 0.12, 0.06)
    B.rect("tap", 0.04, h / 2 + 0.04, 0.12, 0.06)
    B.rect("diff", 0.12, 0.12, w - 0.24, 0.14)
    B.rect("diff", 0.12, h / 2 + 0.12, w - 0.24, 0.14)
    return w, h


def _gates(B, R, w, h, n, series=False):
    pitch = R["poly_space"] + R["poly_width"]
    for i in range(n):
        x = 0.20 + i * pitch
        B.rect("poly", x, 0.06, R["poly_width"], h - 0.12)
        B.rect("licon", x, 0.14, R["contact"], R["contact"])
        B.rect("licon", x, h / 2 + 0.14, R["contact"], R["contact"])
        B.rect("li1", x - 0.02, 0.10, R["poly_width"] + 0.04, 0.30)
        B.rect("li1", x - 0.02, h / 2 + 0.10, R["poly_width"] + 0.04, 0.30)
        if series:
            B.rect("met1", x + R["poly_width"] + 0.02, 0.12, 0.08, 0.14)


def _logic(B, R, n, series=False):
    need = 0.20 + n * (R["poly_space"] + R["poly_width"]) + 0.15
    cols = max(1, math.ceil(need / R["cell_width"]))
    w, h = _std_frame(B, R, cols)
    _gates(B, R, w, h, n, series)
    return w, h


# -- memory --------------------------------------------------------------


def memory(B, R, case):
    k = case["id"]
    if k == "mem-02":
        _sram_array(B, R, cols=32, rows=32, cw=0.30, ch=0.40)
    elif k == "mem-03":
        _bitcell(B, R)
    elif k == "mem-04":
        _decoder(B, R)
    elif k == "mem-05":
        _sense_amp(B, R)
    elif k == "mem-06":
        _driver(B, R)
    elif k == "mem-07":
        _straps(B, R)
    elif k == "mem-08":
        _macro_edge(B, R)
    else:
        raise KeyError(k)


def _sram_array(B, R, cols, rows, cw, ch):
    w, h = cols * cw, rows * ch
    B.rect("nwell", -0.20, -0.20, w + 0.40, h + 0.40)
    for r in range(rows):
        B.rect("diff", 0.0, r * ch + 0.06, w, ch - 0.24)
    for c in range(cols):
        B.rect("poly", c * cw + 0.06, -0.06, R["poly_width"], h + 0.12)
    for r in range(rows):
        for c in range(cols):
            B.rect("licon", c * cw + 0.06, r * ch + 0.10,
                   R["contact"], R["contact"])
    for r in range(0, rows, 8):
        B.rect("met1", -0.10, r * ch, w + 0.20, R["rail_width"])
    B.rect("tap", -0.20, -0.20, w + 0.40, 0.10)
    B.rect("met2", -0.10, h + 0.05, w + 0.20, 0.30)


def _bitcell(B, R):
    B.rect("nwell", -0.10, -0.10, 0.50, 0.70)
    B.rect("diff", 0.0, 0.0, 0.30, 0.12)
    B.rect("diff", 0.0, 0.32, 0.30, 0.12)
    B.rect("poly", 0.10, -0.06, R["poly_width"], 0.56)
    B.rect("licon", 0.02, 0.02, R["contact"], R["contact"])
    B.rect("licon", 0.02, 0.34, R["contact"], R["contact"])
    B.rect("li1", 0.0, 0.02, 0.10, 0.42)
    B.rect("met1", 0.0, 0.18, 0.30, R["rail_width"])


def _decoder(B, R):
    n, pitch = 16, 0.40
    B.rect("diff", 0.0, 0.0, n * pitch, 0.20)
    for i in range(n):
        x = i * pitch + 0.10
        B.rect("poly", x, 0.0, R["poly_width"], 3.0)
        B.rect("licon", x, 2.80, R["contact"], R["contact"])
        B.rect("met1", x - 0.06, 2.60, 0.30, R["rail_width"])


def _sense_amp(B, R):
    for i in range(8):
        y = i * 0.60
        B.rect("diff", 0.0, y, 0.60, 0.15)
        B.rect("poly", 0.20, y - 0.05, R["poly_width"], 0.25)
        B.rect("licon", 0.05, y + 0.02, R["contact"], R["contact"])
        B.rect("met1", 0.0, y, 0.10, 0.15)
        B.rect("met1", 0.50, y, 0.10, 0.15)


def _driver(B, R):
    B.rect("diff", 0.0, 0.0, 8.0, 0.40)
    B.rect("poly", 2.0, -0.10, R["poly_width"], 0.60)
    B.rect("met1", 0.0, 0.0, 8.0, 0.30)
    B.vias("via1", 0.20, 0.10, 12, 2, 0.60, R["via_size"])
    B.rect("met2", 0.0, 0.0, 8.0, 0.30)


def _straps(B, R):
    B.rect("met1", 0.0, 0.0, 20.0, 1.0)
    B.rect("met2", 0.0, 0.0, 20.0, 1.0)
    B.vias("via1", 0.30, 0.30, 32, 2, 0.60, R["via_size"])
    for i in range(0, 20, 4):
        B.rect("met2", i, -1.0, 0.40, 3.0)


def _macro_edge(B, R):
    _sram_array(B, R, cols=16, rows=16, cw=0.30, ch=0.40)
    # Seal ring 0.02 um from the array: below the spacing the rule requires.
    B.rect("seal", -0.02, -0.02, 4.90, 6.50)


# -- standard cells ------------------------------------------------------


def standard_cell(B, R, case):
    k = case["id"]
    if k == "sc-01":
        _logic(B, R, 1)
    elif k == "sc-02":
        _logic(B, R, 2, series=True)
    elif k == "sc-03":
        _nor2_well_shortfall(B, R)
    elif k == "sc-04":
        _logic(B, R, 3)
    elif k == "sc-05":
        _logic(B, R, 6)
    elif k == "sc-06":
        _logic(B, R, 8)
    elif k == "sc-07":
        _latch(B, R)
    elif k == "sc-08":
        _clock_buffer(B, R)
    elif k == "sc-09":
        _fill_cell(B, R)
    elif k == "sc-10":
        _tap_cell(B, R)
    elif k == "sc-11":
        _decap(B, R)
    elif k == "sc-12":
        _antenna(B, R)
    elif k == "sc-13":
        _level_shifter(B, R)
    elif k == "sc-14":
        _power_switch(B, R)
    elif k == "sc-15":
        _abutment_gap(B, R)
    else:
        raise KeyError(k)


def _nor2_well_shortfall(B, R):
    _logic(B, R, 2)
    # A second pmos device whose well stops 0.02 um short of the diffusion.
    B.rect("diff", 2.00, 0.00, 0.40, 0.15)
    B.rect("nwell", 2.00, -0.02, 0.40, 0.15)
    B.rect("poly", 2.10, -0.04, R["poly_width"], 0.23)


def _latch(B, R):
    w, h = _logic(B, R, 4)
    B.rect("met1", 0.10, 0.60, w - 0.20, 0.14)
    B.rect("li1", 0.10, 0.80, 0.14, 0.40)


def _clock_buffer(B, R):
    w, h = _std_frame(B, R, 2)
    for i in range(3):
        B.rect("poly", 0.20 + i * 0.30, 0.06, R["poly_width"], h - 0.12)
    B.rect("met1", 0.10, 0.30, w - 0.20, 0.40)


def _fill_cell(B, R):
    w, h = _std_frame(B, R, 1)
    B.rect("tap", 0.04, 0.04, w - 0.08, 0.06)
    B.rect("tap", 0.04, h / 2 + 0.04, w - 0.08, 0.06)


def _tap_cell(B, R):
    w, h = _std_frame(B, R, 1)
    for x in (0.10, w - 0.22):
        B.rect("tap", x, 0.04, 0.12, 0.06)
        B.rect("tap", x, h / 2 + 0.04, 0.12, 0.06)


def _decap(B, R):
    w, h = _std_frame(B, R, 1)
    B.rect("poly", 0.15, 0.06, 0.20, h - 0.12)
    B.rect("licon", 0.20, 0.02, R["contact"], R["contact"])


def _antenna(B, R):
    w, h = _std_frame(B, R, 1)
    B.rect("diff", w + 0.20, 0.10, 0.30, 0.20)
    B.rect("poly", w + 0.30, 0.05, R["poly_width"], 0.30)
    B.rect("licon", w + 0.32, 0.12, R["contact"], R["contact"])
    B.rect("met1", w + 0.20, 0.10, 0.30, 0.10)


def _level_shifter(B, R):
    w, h = R["cell_width"] * 2, R["cell_height"]
    B.rect("met1", 0.0, 0.0, w, R["rail_width"])
    B.rect("met1", 0.0, h - R["rail_width"], w, R["rail_width"])
    B.rect("diff", 0.12, 0.12, w - 0.24, 0.14)
    B.rect("diff", 0.12, h / 2 + 0.12, 0.18, 0.14)
    B.rect("diff", 0.92, h / 2 + 0.12, 0.18, 0.14)
    B.rect("nwell", 0.0, h / 2, 0.40, h / 2)
    B.rect("nwell", 0.80, h / 2, 0.45, h / 2)
    B.rect("met1", w / 2 + 0.05, 0.0, 0.20, h)


def _power_switch(B, R):
    w, h = _std_frame(B, R, 2)
    B.rect("diff", 0.12, h - 0.30, w - 0.24, 0.14)
    B.rect("poly", 0.20, h - 0.34, w - 0.40, R["poly_width"])


def _abutment_gap(B, R):
    w, h = _std_frame(B, R, 1)
    x = w
    B.rect("nwell", x + 0.05, h / 2, w - 0.05, h / 2)
    B.rect("met1", x, 0.0, w, R["rail_width"])
    B.rect("met1", x, h - R["rail_width"], w, R["rail_width"])
    B.rect("diff", x + 0.17, 0.12, w - 0.29, 0.14)
    B.rect("diff", x + 0.17, h / 2 + 0.12, w - 0.29, 0.14)
    B.rect("poly", x + 0.20, 0.06, R["poly_width"], h - 0.12)


# -- routing -------------------------------------------------------------


def routing(B, R, case):
    k = case["id"]
    mw, ms, g = R["min_width"], R["min_space"], R["grid_um"]
    if k == "rt-01":
        B.rect("met1", 0.0, 0.0, mw, 2.0)
    elif k == "rt-02":
        B.rect("met1", 0.0, 0.0, mw, 2.0)
        B.rect("met1", mw + ms, 0.0, mw, 2.0)
    elif k == "rt-03":
        B.rect("met1", 0.0, 0.0, mw, 2.0)
        B.rect("met1", mw + ms - g, 0.0, mw, 2.0)
    elif k == "rt-04":
        wide = 2.0
        B.rect("met1", 0.0, 0.0, wide, 2.0)
        B.rect("met1", wide + R["width_dep_space"], 0.0, wide, 2.0)
    elif k == "rt-05":
        B.rect("met1", -R["enclose"], -R["enclose"], 0.4, 0.4)
        B.rect("via1", 0.05, 0.05, R["via_size"], R["via_size"])
    elif k == "rt-06":
        B.via("via1", 0.0, 0.0, R["via_size"])
        B.rect("met1", 0.0, 0.0, R["via_size"] / 2, R["via_size"] / 2)
    elif k == "rt-07":
        B.rect("met1", -0.1, -0.1, 0.4, 0.4)
        B.rect("via1", 0.05, 0.05, R["via_size"], R["via_size"])
        B.rect("met2", -0.1, -0.1, 0.4, 0.4)
        B.rect("via2", 0.05, 0.05, R["via_size"], R["via_size"])
        B.rect("met3", -0.1, -0.1, 0.4, 0.4)
        B.rect("via3", 0.05, 0.05, R["via_size"], R["via_size"])
        B.rect("met4", -0.1, -0.1, 0.4, 0.4)
    elif k == "rt-08":
        B.rect_raw("met1", 1.0, 1.0, 0.20, 0.20)
        B.rect_raw("met1", 1.0, 1.302, 0.20, 0.20)
    elif k == "rt-09":
        _notch(B, R, R["notch"] - g)
    elif k == "rt-10":
        B.poly("met1", [(0.0, 0.0), (1.0, 0.0), (2.0, 1.0), (2.0, 1.4), (0.0, 0.4)])
    elif k == "rt-11":
        B.rect("met1", 0.0, 0.50, 2.0, mw)
        B.rect("met1", 2.0, 0.30, 0.40, 0.40)
    elif k == "rt-12":
        B.rect("met1", 0.0, 0.0, 1.0, mw)
        B.rect("met1", 1.0 + ms, mw + ms, mw, 1.0)
    elif k == "rt-13":
        B.rect("met1", 0.0, 0.0, 10.0, mw)
        B.rect("met1", 0.0, mw + ms, 10.0, mw)
    elif k == "rt-14":
        for i in range(6):
            B.rect("met1", 0.0, i * 0.60, 4.0, 0.40)
    elif k == "rt-15":
        for i in range(5):
            B.rect("met1", i * 2.0, 0.0, 0.20 + i * 0.40, 2.0)
    elif k == "rt-16":
        B.rect("met5", 0.0, 0.0, 8.0, 8.0)
        B.vias("via4", 0.5, 0.5, 10, 10, 0.70, R["via_size"])
        B.rect("met4", 0.0, 0.0, 8.0, 8.0)
    else:
        raise KeyError(k)


# -- wells and taps ------------------------------------------------------


def wells(B, R, case):
    k = case["id"]
    ns = R["nwell_space"]
    if k == "wt-01":
        B.rect("nwell", 0.0, 0.0, 2.0, 2.0)
        B.rect("nwell", 2.0 + ns, 0.0, 2.0, 2.0)
    elif k == "wt-02":
        B.rect("nwell", 0.0, 0.0, 2.0, 2.0)
        B.rect("nwell", 2.0 + ns - R["grid_um"], 0.0, 2.0, 2.0)
    elif k == "wt-03":
        B.rect("nwell", 0.0, 0.0, 4.0, 2.0)
        for x in (0.20, 0.20 + R["tap_space"], 0.20 + 2 * R["tap_space"]):
            B.rect("tap", x, 0.20, 0.12, 0.20)
    elif k == "wt-04":
        B.rect("diff", 1.0, 1.0, 2.0, 2.0)
        B.frame("tap", 0.70, 0.70, 2.60, 2.60, 0.12)
    elif k == "wt-05":
        B.rect("diff", 0.0, 0.0, 0.30, 0.40)
        B.rect("tap", R["tap_space"] + 0.30, 0.0, 0.12, 0.40)
    elif k == "wt-06":
        B.rect("nwell", 1.0, 1.0, 2.0, 2.0)
        B.rect("dnwell", 0.5, 0.5, 3.0, 3.0)
    elif k == "wt-07":
        B.rect("nwell", 0.0, 0.0, 6.0, 2.0)
        for x in range(0, 6, 1):
            B.rect("tap", x + 0.20, 0.20, 0.12, 0.20)
    elif k == "wt-08":
        B.rect("nwell", 0.0, 0.60, 3.0, 0.60)
        for x in range(0, 3):
            B.rect("met1", x, 0.0, 1.0, R["rail_width"])
    elif k == "wt-09":
        B.rect("diff", 0.5, 0.5, 1.0, 1.0)
        B.rect("nsdm", 0.35, 0.35, 1.3, 1.3)
        B.rect("psdm", 1.65, 0.35, 0.30, 1.3)
    elif k == "wt-10":
        B.rect("diff", 0.0, 0.0, 0.40, 0.40)
        B.rect("diff", 1.40, 0.0, 0.40, 0.40)
    else:
        raise KeyError(k)


# -- devices -------------------------------------------------------------


def devices(B, R, case):
    k = case["id"]
    if k == "dv-01":
        _device(B, R, length=R["poly_width"], width=0.40)
    elif k == "dv-02":
        _device(B, R, length=R["poly_width"] - R["grid_um"], width=0.40)
    elif k == "dv-03":
        _device(B, R, length=0.15, width=0.90, fingers=3)
    elif k == "dv-04":
        _device(B, R, length=0.15, width=0.60, shared=True)
    elif k == "dv-05":
        B.rect("diff", 0.0, 0.0, 1.00, 0.20)
        B.rect("poly", 0.90, -0.05, R["poly_width"], 0.30)
        B.rect("poly", 0.00, -0.05, R["poly_width"], 0.30)
    elif k == "dv-06":
        B.rect("diff", 0.0, 0.0, 1.00, 0.30)
        B.rect("poly", 0.40, -0.10, R["poly_width"], 0.50)
        B.rect("licon", 0.42, 0.10, R["contact"], R["contact"])
    elif k == "dv-07":
        B.rect("diff", 0.0, 0.0, 1.00, 0.30)
        B.rect("licon", 0.10, 0.10, R["contact"], R["contact"])
        B.rect("licon", 0.10 + R["contact"] + R["contact_space"] - R["grid_um"],
               0.10, R["contact"], R["contact"])
    elif k == "dv-08":
        _device(B, R, length=0.15, width=0.40, endcap=R["endcap"])
    elif k == "dv-09":
        B.rect("diff", 0.0, 0.0, 2.0, 2.0)
        B.vias("licon", 0.20, 0.20, 10, 10, R["contact"] + R["contact_space"],
               R["contact"])
    elif k == "dv-10":
        _device(B, R, length=0.15, width=0.40)
        _device(B, R, length=0.15, width=0.40, dx=1.20, mirror=True)
    elif k == "dv-11":
        B.rect("diff", 0.0, 0.0, 1.20, 0.60)
        B.rect("poly", 0.50, -0.10, R["poly_width"], 0.80)
        B.rect("nsdm", -0.10, -0.10, 1.40, 0.80)
    elif k == "dv-12":
        B.rect("diff", 0.0, 0.0, 1.00, 0.40)
        B.rect("poly", 0.40, -0.10, R["poly_width"], 0.60)
        B.rect("sab", 0.20, -0.10, 0.70, 0.60)
    elif k == "dv-13":
        B.rect("diff", 0.0, 0.0, 0.40, 0.40)
        B.rect("li1", 0.36, 0.0, 0.20, 0.40)
        B.rect("licon", 0.32, 0.15, R["contact"], R["contact"])
    else:
        raise KeyError(k)


def _device(B, R, length, width, fingers=1, shared=False, endcap=None,
            dx=0.0, mirror=False):
    """One transistor: the gate length is the poly width over the diffusion."""
    ec = R["endcap"] if endcap is None else endcap
    span = 0.15 + fingers * (length + R["poly_space"])
    B.rect("diff", dx, 0.0, span, width)
    for f in range(fingers):
        x = dx + 0.15 + f * (length + R["poly_space"])
        B.rect("poly", x, -ec, length, width + 2 * ec)
        B.rect("licon", x + length / 2 - R["contact"] / 2, 0.05,
               R["contact"], R["contact"])
    if shared:
        B.rect("licon", dx + 0.02, 0.05, R["contact"], R["contact"])
        B.rect("licon", dx + span - 0.11, 0.05, R["contact"], R["contact"])


# -- IO and ESD ----------------------------------------------------------


def io(B, R, case):
    k = case["id"]
    pad = R["pad_size"]
    if k == "io-01":
        B.rect("pad", 0.0, 0.0, pad, pad)
        B.frame("pass", 0.0, 0.0, pad, pad, 2.0)
    elif k == "io-02":
        B.rect("diff", 0.0, 0.0, 2.0, 0.60)
        B.rect("poly", 0.90, -0.10, R["poly_width"], 0.80)
        B.vias("licon", 0.10, 0.10, 8, 2, 0.20, R["contact"])
        B.rect("met1", 0.0, 0.0, 2.0, 0.20)
    elif k == "io-03":
        B.rect("diff", 0.0, 0.0, 20.0, 1.00)
        B.rect("met1", 0.0, 0.30, 20.0, R["min_width"])
        B.vias("licon", 0.20, 0.40, 4, 1, 1.0, R["contact"])
    elif k == "io-04":
        B.rect("met5", -2.0, -2.0, pad + 4.0, pad + 4.0)
        B.rect("pad", 0.0, 0.0, pad, pad)
    elif k == "io-05":
        B.rect("pad", 0.0, 0.0, 10.0, 10.0)
        B.rect("diff", 10.5, 0.0, 1.0, 1.0)
    elif k == "io-06":
        B.rect("diff", 1.0, 1.0, 2.0, 2.0)
        B.frame("tap", 0.60, 0.60, 2.80, 2.80, 0.14)
    elif k == "io-07":
        B.rect("met5", 0.0, 0.0, 20.0, 20.0)
        B.rect("met4", 0.0, 0.0, 20.0, 20.0)
        B.vias("via4", 1.0, 1.0, 6, 6, 3.0, R["via_size"])
    elif k == "io-08":
        B.rect("nwell", 0.0, 0.0, 4.0, 2.0)
        B.rect("nwell", 4.4, 0.0, 2.0, 2.0)
        B.rect("met1", 0.0, 0.0, 6.4, R["rail_width"])
    else:
        raise KeyError(k)


# -- seal and scribe -----------------------------------------------------


def seal(B, R, case):
    k = case["id"]
    if k == "sl-01":
        B.frame("seal", 0.0, 0.0, 20.0, 20.0, 0.60)
    elif k == "sl-02":
        for name in ("met1", "met2", "met3", "met4", "met5"):
            B.frame(name, 0.0, 0.0, 20.0, 20.0, 0.60)
        B.vias("via1", 0.20, 0.20, 3, 3, 0.30, R["via_size"])
    elif k == "sl-03":
        B.rect("diff", 1.0, 1.0, 2.0, 2.0)
        B.frame("seal", 0.0, 0.0, 4.0, 4.0, 0.60)
        B.rect("diff", 1.0, 1.0, 2.0, 2.0)
    elif k == "sl-04":
        B.rect("seal", 0.0, 0.0, 0.40, 6.0)
        B.rect("seal", 4.0, 0.0, 0.40, 6.0)
        B.rect("met1", 1.0, 0.0, 0.50, 3.0)
        B.rect("met1", 2.0, 1.0, 0.50, 3.0)
    else:
        raise KeyError(k)


# -- density and fill ----------------------------------------------------


def density(B, R, case):
    k = case["id"]
    tile = 10.0
    if k in ("df-01", "df-02", "df-03", "df-04"):
        fraction = {"df-01": R["density_min"], "df-02": R["density_max"],
                    "df-03": min(0.95, R["density_max"] + 0.10),
                    "df-04": max(0.05, R["density_min"] - 0.15)}[k]
        _density_squares(B, tile, fraction)
    elif k == "df-05":
        for i in range(20):
            for j in range(20):
                if (i + j) % 2 == 0:
                    B.rect("met1", i * 0.5, j * 0.5, 0.45, 0.45)
    elif k == "df-06":
        for i in range(10):
            B.rect("met1", 0.0, i * 1.0, 10.0, 0.70)
    elif k == "df-07":
        for i in range(20):
            B.rect("met1", i * 0.5, 0.0, 0.36, 10.0)
    elif k == "df-08":
        B.rect("met1", 0.0, 0.0, 10.0, 0.60)
        for i in range(10):
            B.rect("met2", i * 1.0, 0.30, 0.40, 0.40)
    elif k == "df-09":
        B.rect("met1", 0.0, 0.0, 8.0, 8.0)
        B.rect("met1", 9.0, 0.0, 1.0, 8.0)
        B.rect("met2", 0.0, 0.0, 8.0, 0.20)
    else:
        raise KeyError(k)


def _density_squares(B, tile, fraction):
    # Cover `fraction` of the tile with stripes; height is derived, not tuned.
    rows = 10
    height = fraction * tile / rows
    for i in range(rows):
        B.rect("met1", 0.0, i * (tile / rows), tile, height)


# -- regularity ----------------------------------------------------------


def regularity(B, R, case):
    k = case["id"]
    if k == "rg-01":
        for i in range(50):
            B.rect("poly", i * (R["poly_width"] + R["poly_space"]), 0.0,
                   R["poly_width"], 6.0)
    elif k == "rg-02":
        for i in range(30):
            B.rect("met1", i * (R["min_width"] + R["min_space"]), 0.0,
                   R["min_width"], 6.0)
    elif k == "rg-03":
        B.rect("diff", 0.0, 0.0, 6.0, 6.0)
        B.vias("licon", 0.20, 0.20, 12, 12,
               R["contact"] + R["contact_space"], R["contact"])
    elif k == "rg-04":
        for name in ("met1", "met2", "met3"):
            B.rect(name, 0.0, 0.0, 4.0, 4.0)
        B.vias("via1", 0.40, 0.40, 4, 4, 0.90, R["via_size"])
        B.vias("via2", 0.40, 0.40, 4, 4, 0.90, R["via_size"])
    elif k == "rg-05":
        w = R["cell_width"]
        B.rect("nwell", 0.0, R["cell_height"] / 2, 20 * w, R["cell_height"] / 2)
        for i in range(20):
            B.rect("met1", i * w, 0.0, w, R["rail_width"])
            B.rect("met1", i * w, R["cell_height"] - R["rail_width"], w,
                   R["rail_width"])
            B.rect("diff", i * w + 0.04, 0.12, w - 0.08, 0.14)
            B.rect("poly", i * w + 0.20, 0.06, R["poly_width"],
                   R["cell_height"] - 0.12)
    elif k == "rg-06":
        for i in range(8):
            for j in range(8):
                _bitcell_at(B, R, i * 0.30, j * 0.40)
    elif k == "rg-07":
        for i in range(12):
            B.rect("poly", i * 0.30, 0.0, R["poly_width"], 4.0)
        B.rect("poly", 12 * 0.30, 0.0, R["poly_width"], 4.0)
    else:
        raise KeyError(k)


def _bitcell_at(B, R, x, y):
    B.rect("diff", x, y, 0.30, 0.12)
    B.rect("poly", x + 0.10, y - 0.06, R["poly_width"], 0.24)
    B.rect("licon", x + 0.02, y + 0.02, R["contact"], R["contact"])


# -- marginal (exactly at a limit) ---------------------------------------


def marginal(B, R, case):
    k = case["id"]
    g = R["grid_um"]
    if k == "mg-01":
        B.rect("met1", 0.0, 0.0, R["min_width"], 2.0)
    elif k == "mg-02":
        B.rect("met1", 0.0, 0.0, R["min_width"], 2.0)
        B.rect("met1", R["min_width"] + R["min_space"], 0.0, R["min_width"], 2.0)
    elif k == "mg-03":
        side = math.ceil(math.sqrt(R["min_area"]) / g) * g
        B.rect("met1", 0.0, 0.0, side, side)
    elif k == "mg-04":
        v = R["via_size"]
        B.rect("met1", -R["enclose"], -R["enclose"],
               v + 2 * R["enclose"], v + 2 * R["enclose"])
        B.rect("via1", 0.0, 0.0, v, v)
    elif k == "mg-05":
        _density_squares(B, 10.0, R["density_max"])
    elif k == "mg-06":
        B.rect("diff", 0.0, 0.0, 0.60, 0.30)
        B.rect("poly", 0.20, -R["endcap"], R["poly_width"], 0.30 + 2 * R["endcap"])
    elif k == "mg-07":
        _notch(B, R, R["notch"])
    elif k == "mg-08":
        B.rect("met1", 0.0, 0.0, 1.0, R["min_width"])
        B.rect("met1", 1.0 + R["min_space"], R["min_width"] + R["min_space"],
               R["min_width"], 1.0)
    else:
        raise KeyError(k)


# -- cross-layer ---------------------------------------------------------


def cross_layer(B, R, case):
    k = case["id"]
    if k == "xl-01":
        B.rect("poly", 0.0, 0.0, 2.0, 0.20)
        B.rect("met1", 0.0, 0.50, 2.0, 0.20)
    elif k == "xl-02":
        B.rect("diff", 0.0, 0.0, 2.0, 0.40)
        B.rect("poly", 0.90, -0.10, R["poly_width"], 0.60)
        B.rect("licon", 0.92, 0.16, R["contact"], R["contact"])
        B.rect("met1", 0.80, 0.10, 0.60, 0.30)  # metal over the gate contact
    elif k == "xl-03":
        B.rect("poly", 0.0, 0.0, 2.0, 0.20)
        B.via("via1", 0.90, 0.05, R["via_size"])
        B.rect("met1", 0.60, -0.10, 0.60, 0.40)
    elif k == "xl-04":
        B.rect("diff", 0.0, 0.0, 2.0, 0.40)
        B.rect("licon", 0.50, 0.10, R["contact"], R["contact"])
        B.rect("met1", 0.30, 0.0, 0.60, 0.40)
    elif k == "xl-05":
        B.rect("nwell", 0.0, 0.0, 3.0, 3.0)
        B.rect("dnwell", -1.0, -1.0, 5.0, 5.0)
    elif k == "xl-06":
        B.rect("met1", 0.0, 0.0, 2.0, 2.0)
        B.rect("met1", 2.0, 0.0, 2.0, 2.0)
    else:
        raise KeyError(k)


def _notch(B, R, gap):
    """A slot opening to the right edge; `gap` is the notch width."""
    y0 = 0.40
    B.poly(
        "met1",
        [
            (0.0, 0.0), (2.0, 0.0), (2.0, y0), (1.0, y0),
            (1.0, y0 + gap), (2.0, y0 + gap), (2.0, 1.0), (0.0, 1.0),
        ],
    )


FAMILIES = {
    "memory": memory,
    "standard-cell": standard_cell,
    "routing": routing,
    "wells-and-taps": wells,
    "devices": devices,
    "io-and-esd": io,
    "seal-and-scribe": seal,
    "density-and-fill": density,
    "regularity": regularity,
    "marginal": marginal,
    "cross-layer": cross_layer,
}


def build(case, Builder, layers, dbu_um, grid_um, rules):
    family = FAMILIES.get(case["category"])
    if family is None:
        raise KeyError(f"no builder for category {case['category']!r}")
    builder = Builder(layers, dbu_um, grid_um)
    family(builder, rules, case)
    return builder
