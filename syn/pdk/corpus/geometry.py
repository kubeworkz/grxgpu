"""Layout construction helpers for the conformance corpus.

Coordinates are microns at the call sites and database units in the layout.
Rectangles snap to the rule file's manufacturing grid; the `raw` variants exist
only for the cases that deliberately sit off that grid.
"""

import klayout.db as db


class Builder:
    def __init__(self, layers, dbu_um, grid_um):
        self.layers = layers
        self.dbu = float(dbu_um)
        self.grid = float(grid_um)
        self.layout = db.Layout()
        self.layout.dbu = self.dbu
        self.top = self.layout.create_cell("top")

    # -- coordinates ----------------------------------------------------

    def snap(self, value):
        return round(round(value / self.grid) * self.grid, 6)

    def u(self, value):
        return int(round(self.snap(value) / self.dbu))

    def raw(self, value):
        return int(round(value / self.dbu))

    # -- shapes ---------------------------------------------------------

    def layer(self, name):
        try:
            number, datatype = self.layers[name]
        except KeyError:
            raise KeyError(f"layer {name!r} missing from the layer map") from None
        return self.layout.layer(number, datatype)

    def rect(self, name, x, y, w, h):
        shapes = self.top.shapes(self.layer(name))
        shapes.insert(db.Box(self.u(x), self.u(y), self.u(x + w), self.u(y + h)))

    def rect_raw(self, name, x, y, w, h):
        shapes = self.top.shapes(self.layer(name))
        shapes.insert(
            db.Box(self.raw(x), self.raw(y), self.raw(x + w), self.raw(y + h))
        )

    def poly(self, name, points):
        polygon = db.Polygon([db.Point(self.u(x), self.u(y)) for x, y in points])
        self.top.shapes(self.layer(name)).insert(polygon)

    def frame(self, name, x, y, w, h, t):
        self.rect(name, x, y, w, t)
        self.rect(name, x, y + h - t, w, t)
        self.rect(name, x, y + t, t, h - 2 * t)
        self.rect(name, x + w - t, y + t, t, h - 2 * t)

    # -- arrays ---------------------------------------------------------

    def via(self, name, x, y, size):
        self.rect(name, x, y, size, size)

    def vias(self, name, x, y, cols, rows, pitch, size):
        for i in range(cols):
            for j in range(rows):
                self.rect(name, x + i * pitch, y + j * pitch, size, size)

    def count(self):
        return sum(self.top.shapes(i).size() for i in range(self.layout.layers()))

    def write(self, path):
        self.layout.write(str(path))
