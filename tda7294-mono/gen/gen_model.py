"""Approximate 3D model (VRML 2.0) of the TDA7294V in Multiwatt15 vertical.

KiCad's library has no TO-220-15 / Multiwatt15 model, so this one is built to
the datasheet outline closely enough for clearance checks and renders.
Footprint frame: pad 1 at origin, odd row at y=0, even row at y=-5.08 (toward
the heatsink), tab back face at y=-9.855.  VRML unit = 2.54 mm (KiCad convention).
"""
import sys

U = 2.54
Z0 = 4.0            # underside of the plastic body above the board
BODY_TOP = 14.4
TAB_TOP = 21.6
X0, X1 = 8.89 - 9.8, 8.89 + 9.8
Y_TAB, Y_TABF, Y_FRONT = -9.855, -8.255, -5.35
Y_LEG = -6.8


def box(x0, x1, y0, y1, z0, z1):
    # footprint coords (y down) -> model coords (y up)
    pts = [(x, -y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return pts, faces


def shape(boxes, rgb, spec=(0.2, 0.2, 0.2), shin=0.3):
    pts, idx = [], []
    for b in boxes:
        p, f = box(*b)
        base = len(pts)
        pts += p
        idx += [tuple(base + i for i in face) for face in f]
    ptxt = ", ".join(f"{x / U:.4f} {y / U:.4f} {z / U:.4f}" for x, y, z in pts)
    itxt = ", ".join(" ".join(map(str, f)) + " -1" for f in idx)
    return (f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {rgb[0]} {rgb[1]} {rgb[2]} "
            f"specularColor {spec[0]} {spec[1]} {spec[2]} shininess {shin} }} }}\n"
            f"  geometry IndexedFaceSet {{ solid FALSE coord Coordinate {{ point [ {ptxt} ] }}\n"
            f"  coordIndex [ {itxt} ] }} }}\n")


def build():
    body = [(X0, X1, Y_TABF, Y_FRONT, Z0, BODY_TOP)]
    tab = [(X0, X1, Y_TAB, Y_TABF, Z0, TAB_TOP)]
    # tab hole drawn as a dark square insert on both faces
    hole = [(8.89 - 1.8, 8.89 + 1.8, Y_TAB - 0.01, Y_TABF + 0.01, TAB_TOP - 5.6, TAB_TOP - 2.0)]
    legs = []
    for n in range(15):
        x = n * 1.27
        yp = 0.0 if n % 2 == 0 else -5.08
        w = 0.35
        legs.append((x - w, x + w, yp - 0.25, yp + 0.25, -3.0, 2.3))          # through board
        legs.append((x - w, x + w, min(yp, Y_LEG), max(yp, Y_LEG), 2.0, 2.5))  # formed bend
        legs.append((x - w, x + w, Y_LEG - 0.25, Y_LEG + 0.25, 2.0, Z0 + 0.1))
    return ("#VRML V2.0 utf8\n# TDA7294V Multiwatt15 (approximate)\n" +
            shape(body, (0.08, 0.08, 0.09)) +
            shape(tab, (0.78, 0.78, 0.80), spec=(0.9, 0.9, 0.9), shin=0.6) +
            shape(hole, (0.02, 0.02, 0.02)) +
            shape(legs, (0.82, 0.82, 0.84), spec=(0.8, 0.8, 0.8), shin=0.5))


if __name__ == "__main__":
    open(sys.argv[1], "w").write(build())
