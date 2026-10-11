"""Generate the KiCad 7 schematic from circuit.py (labels on every pin)."""
import math
import sys
import uuid
from sexp import parse, dump, find, q, unq

sys.path.insert(0, ".")
from circuit import PARTS, FP

LIBDIR = "/usr/share/kicad/symbols"
PROJECT = "tda7294_mono"
ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, "tda7294-root"))


def U(*k):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "tda7294/" + "/".join(map(str, k))))


_libcache = {}


def libsym(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        _libcache[lib] = parse(open(f"{LIBDIR}/{lib}.kicad_sym").read())
    syms = {unq(s[1]): s for s in find(_libcache[lib], "symbol")}
    node = syms[name]
    ext = find(node, "extends")
    if ext:  # flatten derived symbol
        base = syms[unq(ext[0][1])]
        bname = unq(base[1])
        props = {unq(p[1]): p for p in find(node, "property")}
        flat = [base[0], q(lib_id)]
        for x in base[2:]:
            if isinstance(x, list) and x[0] == "property" and unq(x[1]) in props:
                flat.append(props[unq(x[1])])
            elif isinstance(x, list) and x[0] == "symbol":
                sub = list(x)
                sub[1] = q(unq(x[1]).replace(bname, name))
                flat.append(sub)
            else:
                flat.append(x)
        return flat
    out = list(node)
    out[1] = q(lib_id)
    return out


def pins_of(sym):
    """pin number -> (x, y, angle) in library coordinates."""
    res = {}
    for sub in find(sym, "symbol"):
        for p in find(sub, "pin"):
            at = find(p, "at")[0]
            num = unq(find(p, "number")[0][1])
            res[num] = (float(at[1]), float(at[2]), float(at[3]))
    return res


def xf(px, py, X, Y, rot):
    r = math.radians(rot)
    rx = px * math.cos(r) - py * math.sin(r)
    ry = px * math.sin(r) + py * math.cos(r)
    return round(X + rx, 2), round(Y - ry, 2)


# ---------------------------------------------------------------- placement
# ref: (x, y, rotation)
P = {}


def row(refs, x0, y, dx=17.78, rot=0):
    for i, r in enumerate(refs):
        P[r] = (x0 + i * dx, y, rot)


P["U1"] = (190.5, 127.0, 0)
row(["R7", "C12", "C2", "R2"], 50.8, 76.2)
row(["R5", "R1", "C3", "C4"], 50.8, 127.0)
row(["R4", "R6", "C1", "R3", "C10"], 271.78, 76.2)
P["D1"] = (271.78 + 17.78 * 0.5, 96.52, 0)
row(["C5", "C9", "C7", "C13"], 271.78, 132.08)
row(["C6", "C11", "C8", "C14"], 271.78, 172.72)
for i, r in enumerate(["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8"]):
    P[r] = (45.72, 175.26 + i * 7.62, 0)
P["NT1"] = (190.5, 182.88, 0)
row(["H1", "H2", "H3", "H4"], 271.78, 213.36, dx=15.24)

FLAGS = ["+V", "-V", "PGND", "SGND"]

TEXTS = [
    ("INPUT  (RF filter R7/C12 optional: R7 = 0R link, C12 not fitted)", 45.72, 58.42),
    ("FEEDBACK  gain = 1 + R5/R1 = 33.4x (30.5 dB)   +  BOOTSTRAP", 45.72, 109.22),
    ("MUTE / STANDBY  (J8 to +V = play, to SGND = standby)", 266.7, 58.42),
    ("+V RAIL DECOUPLING  (local; main reservoir sits in the PSU)", 266.7, 114.3),
    ("-V RAIL DECOUPLING", 266.7, 154.94),
    ("WIRE PADS", 40.64, 165.1),
    ("STAR POINT: the only SGND-PGND joint (NT1 on the PCB)", 165.1, 172.72),
    ("TDA7294 MONO MODULE  -  Currently Amped  -  4-layer, 2 oz Cu, ENIG", 165.1, 66.04),
    ("All resistors: metal film 1% 0.6 W.  All electrolytics: Panasonic FC.", 165.1, 71.12),
    ("U1 tab is at -V: insulate from heatsink.", 165.1, 152.4),
]


def eff(size=1.27, justify=None, hide=False):
    e = ["effects", ["font", ["size", str(size), str(size)]]]
    if justify:
        e.append(["justify"] + justify.split())
    if hide:
        e.append("hide")
    return e


def prop(name, val, x, y, hide=False, justify="left", pid=None):
    n = ["property", q(name), q(val), ["at", str(x), str(y), "0"]]
    if pid is not None:
        n.append(["id", str(pid)])
    n.append(eff(justify=justify, hide=hide))
    return n


def label(net, x, y, ang):
    just = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[ang]
    return ["label", q(net), ["at", str(x), str(y), str(ang)], ["fields_autoplaced"],
            eff(justify=just), ["uuid", U("lbl", net, x, y)]]


def wire(x1, y1, x2, y2):
    return ["wire", ["pts", ["xy", str(x1), str(y1)], ["xy", str(x2), str(y2)]],
            ["stroke", ["width", "0"], ["type", "default"]], ["uuid", U("w", x1, y1, x2, y2)]]


def stub_and_label(net, x, y, outward_deg, items, length=2.54):
    a = math.radians(outward_deg)
    dx, dy = round(math.cos(a) * length, 2), round(-math.sin(a) * length, 2)
    ex, ey = round(x + dx, 2), round(y + dy, 2)
    items.append(wire(x, y, ex, ey))
    ang = int(round(outward_deg)) % 360
    items.append(label(net, ex, ey, ang))


def build():
    lib_ids = sorted({v[0] for v in PARTS.values()} | {"power:PWR_FLAG"})
    libs = {lid: libsym(lid) for lid in lib_ids}
    items = []
    endpoints = []  # for the self-check

    def place(ref, lib_id, value, footprint, pins, fields, X, Y, rot, dnp=False):
        sym = libs[lib_id]
        pdef = pins_of(sym)
        is_power = ref.startswith("#")
        node = ["symbol", ["lib_id", q(lib_id)], ["at", str(X), str(Y), str(rot)],
                ["unit", "1"], ["in_bom", "no" if is_power or ref.startswith("NT") else "yes"],
                ["on_board", "no" if is_power else "yes"],
                ["dnp", "yes" if dnp else "no"], ["fields_autoplaced"], ["uuid", U("sym", ref)]]
        node.append(prop("Reference", ref, X + 3.0, Y - 1.27, hide=is_power, pid=0))
        node.append(prop("Value", value, X + 3.0, Y + 1.27, pid=1))
        node.append(prop("Footprint", footprint, X, Y, hide=True, pid=2))
        node.append(prop("Datasheet", "", X, Y, hide=True, pid=3))
        for i, (k, v) in enumerate(fields.items()):
            node.append(prop(k, v, X, Y, hide=True, pid=4 + i))
        for num in pdef:
            node.append(["pin", q(num), ["uuid", U("pin", ref, num)]])
        node.append(["instances", ["project", q(PROJECT),
                     ["path", q("/" + ROOT), ["reference", q(ref)], ["unit", "1"]]]])
        items.append(node)
        for num, (px, py, pang) in pdef.items():
            x, y = xf(px, py, X, Y, rot)
            net = pins.get(num) or pins.get(int(num) if num.isdigit() else num)
            if net is None:
                continue
            L = 5.08 if ref[:2] in ("U1", "NT") else 2.54
            stub_and_label(net, x, y, (pang + 180 + rot) % 360, items, length=L)
            endpoints.append((ref, num, net))

    for ref, (lib_id, value, fpk, pins, fields) in PARTS.items():
        X, Y, rot = P[ref]
        fields = {k: v for k, v in fields.items() if k != "DNP"}
        place(ref, lib_id, value, FP[fpk], pins, fields, X, Y, rot,
              dnp=PARTS[ref][4].get("DNP") == "yes")
    for i, net in enumerate(FLAGS):
        place(f"#FLG0{i + 1}", "power:PWR_FLAG", "PWR_FLAG", "", {"1": net}, {},
              165.1 + i * 15.24, 213.36, 0)

    for t, x, y in TEXTS:
        items.append(["text", q(t), ["at", str(x), str(y), "0"],
                      eff(size=1.778, justify="left bottom"), ["uuid", U("txt", t)]])

    doc = ["kicad_sch", ["version", "20230121"], ["generator", "eeschema"],
           ["uuid", ROOT], ["paper", q("A3")],
           ["title_block", ["title", q("TDA7294 Mono Power Amplifier Module")],
            ["date", q("2026-10-10")], ["rev", q("1.0")],
            ["company", q("Currently Amped")],
            ["comment", "1", q("After the classic French TDA7294 module; 4-layer redesign")],
            ["comment", "2", q("Rails +/-30..35 V idle, 4 ohm load")]],
           ["lib_symbols"] + [libs[k] for k in lib_ids]]
    doc += items
    doc.append(["sheet_instances", ["path", q("/"), ["page", q("1")]]])
    return doc, endpoints


if __name__ == "__main__":
    doc, ep = build()
    open(sys.argv[1], "w").write(dump(doc) + "\n")
    print("pins labelled:", len(ep))
