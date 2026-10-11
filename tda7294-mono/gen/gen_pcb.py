"""Build the 4-layer TDA7294 mono module PCB (KiCad 7 pcbnew API).

Coordinates below are board-local mm: origin = top-left corner of the board,
y grows downward, the heatsink sits along the TOP edge (y = 0).
"""
import json
import os
import sys
import uuid

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from circuit import PARTS, FP, POWER_NETS  # noqa: E402

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "../kicad"
NAME = "tda7294_mono"
PCB = os.path.join(OUT_DIR, NAME + ".kicad_pcb")
PRO = os.path.join(OUT_DIR, NAME + ".kicad_pro")
FPDIR = "/usr/share/kicad/footprints"

W, H = 130.0, 80.0           # board size
OX, OY = 50.0, 40.0          # where the board sits on the drawing sheet
MM = pcbnew.FromMM

# ---------------------------------------------------------------- placement
# ref: (x, y, orientation_deg) of the footprint origin (= pad 1 for all THT parts)
PIN1_X = 65.0 - 8.89         # U1 centred on the board
PIN_ROW = 9.9                # odd-pin row; tab back face lands on the board edge
PLACE = {
    "U1":  (PIN1_X, PIN_ROW, 0),
    # +V side (left)
    "C9":  (9.0, 26.0, 270),
    "C7":  (22.25, 24.0, 0),
    "C13": (22.25, 50.0, 0),
    "C5":  (30.0, 5.5, 270),
    # -V side (right)
    "C11": (121.0, 26.0, 270),
    "C8":  (100.25, 24.0, 0),
    "C14": (100.25, 50.0, 0),
    "C6":  (88.0, 10.5, 90),
    # feedback / bootstrap (left of the IC, fed by the under-body lanes)
    "C4":  (47.0, 20.0, 180),
    "R5":  (42.0, 28.0, 0),
    "R1":  (52.16, 32.0, 270),
    "C3":  (52.16, 49.0, 180),
    # input
    "R2":  (58.65, 56.0, 180),
    "C2":  (43.65, 64.0, 0),
    "C12": (40.5, 57.0, 0),
    "R7":  (37.0, 67.16, 90),
    # mute / standby
    "C10": (66.27, 15.0, 0),
    "R3":  (66.27, 30.16, 90),
    "R4":  (66.27, 40.0, 0),
    "R6":  (76.43, 36.0, 90),
    "D1":  (71.5, 36.0, 90),
    "C1":  (74.2, 21.0, 180),
    # star + wire pads (bottom edge)
    "NT1": (49.0, 72.0, 0),
    "J1":  (14.0, 75.0, 0),
    "J6":  (37.0, 70.0, 0),
    "J7":  (42.0, 70.0, 0),
    "J2":  (57.0, 75.0, 0),
    "J8":  (66.27, 75.0, 0),
    "J4":  (80.0, 75.0, 0),
    "J5":  (88.0, 75.0, 0),
    "J3":  (116.0, 75.0, 0),
    # mechanical
    "H1":  (5.0, 5.0, 0),
    "H2":  (125.0, 5.0, 0),
    "H3":  (5.0, 75.0, 0),
    "H4":  (125.0, 75.0, 0),
}

# silkscreen reference positions that would otherwise collide (board coords)
REF_POS = {"C4": (38.0, 15.5), "R5": (47.1, 26.4), "C3": (43.0, 49.0), "C2": (51.2, 69.6),
           "R2": (53.6, 54.4), "C12": (43.0, 55.0)}

SIG_W = 0.4      # small-signal track width
BOOT_W = 0.5
OUT_W = 2.5      # speaker output
LANE_OUT = 1.75  # under-body lanes (y)
LANE_BOOT = 3.05
LANE_MUTE_B = 2.4

# (net, layer, width, [points])
TRACKS = [
    # IN-: pin 2 exits left at row level, drops to R5/R1
    ("IN-", "F", SIG_W, [(PIN1_X + 1.27, 4.82), (52.16, 4.82), (52.16, 28.0)]),
    ("IN-", "F", SIG_W, [(52.16, 28.0), (52.16, 32.0)]),
    # BOOT: pin 6 -> upper lane -> C4+
    ("BOOT", "F", BOOT_W, [(PIN1_X + 5 * 1.27, 4.82), (PIN1_X + 5 * 1.27, LANE_BOOT),
                           (47.0, LANE_BOOT), (47.0, 20.0)]),
    # OUT sense lane: pin 14 -> top lane -> C4- -> R5 (feedback taken at the pin)
    ("OUT", "F", SIG_W, [(PIN1_X + 13 * 1.27, 4.82), (PIN1_X + 13 * 1.27, LANE_OUT),
                         (42.0, LANE_OUT), (42.0, 20.0), (42.0, 28.0)]),
    # OUT power: pin 14 -> right -> down the right of the signal area -> SPK+
    ("OUT", "F", 1.5, [(PIN1_X + 13 * 1.27, 4.82), (75.5, 4.82)]),
    ("OUT", "F", OUT_W, [(75.5, 4.82), (80.0, 4.82), (80.0, 75.0)]),
    # FB_AC: R1 -> C3+
    ("FB_AC", "F", SIG_W, [(52.16, 42.16), (52.16, 49.0)]),
    # IN+: pin 3 straight down through R2 to C2
    ("IN+", "F", SIG_W, [(PIN1_X + 2 * 1.27, PIN_ROW), (58.65, 56.0), (58.65, 64.0)]),
    # input: J6 -> R7 -> C12 -> C2
    ("IN", "F", SIG_W, [(37.0, 70.0), (37.0, 67.16)]),
    ("IN_F", "F", SIG_W, [(37.0, 57.0), (40.5, 57.0), (40.5, 64.0), (43.65, 64.0)]),
    # star point: NT1 sits in a pour keep-out and is reached by two short tracks
    ("SGND", "F", 1.0, [(47.0, 72.0), (42.0, 72.0), (42.0, 70.0)]),
    ("PGND", "F", 2.0, [(51.0, 72.0), (57.0, 72.0), (57.0, 75.0)]),
    # STBY: pin 9 -> C10+ -> R3
    ("STBY", "F", SIG_W, [(PIN1_X + 8 * 1.27, PIN_ROW), (66.27, 15.0), (66.27, 20.0)]),
    # MUTE_IN: R3 -> R4 -> J8
    ("MUTE_IN", "F", SIG_W, [(66.27, 30.16), (66.27, 40.0), (66.27, 75.0)]),
    # MUTE_N1: R4 -> R6, D1 K -> R6
    ("MUTE_N1", "F", SIG_W, [(76.43, 40.0), (76.43, 36.0)]),
    ("MUTE_N1", "F", SIG_W, [(71.5, 36.0), (76.43, 36.0)]),
    # MUTE: pin 10 on the bottom layer -> lane -> R6 pin 2, then D1 A and C1+ on top
    ("MUTE", "B", SIG_W, [(PIN1_X + 9 * 1.27, 4.82), (PIN1_X + 9 * 1.27, LANE_MUTE_B),
                          (76.43, LANE_MUTE_B), (76.43, 25.84)]),
    ("MUTE", "F", SIG_W, [(76.43, 25.84), (74.2, 23.6), (74.2, 21.0)]),
    ("MUTE", "F", SIG_W, [(71.5, 28.38), (71.5, 27.0), (74.2, 23.6)]),
]

# ------------------------------------------------------------------ zones
SGND_ISLAND = [(35.5, 0.0), (78.0, 0.0), (78.0, 69.0), (49.0, 69.0), (49.0, 73.4),
               (33.0, 73.4), (33.0, 64.0), (35.5, 64.0)]
NT1_KEEPOUT = [(45.0, 70.4), (53.0, 70.4), (53.0, 73.6), (45.0, 73.6)]
VIAS = [("SGND", 44.5, 72.0, 0.8, 0.4), ("PGND", 54.0, 72.0, 1.6, 0.8)]
# PGND stitching (F.Cu pour <-> In1 plane) along the arms and the bottom bus
VIAS += [("PGND", x, y, 1.2, 0.6) for x, y in [
    (33.0, 14.0), (33.0, 37.0), (31.5, 62.0), (14.0, 64.0), (5.0, 40.0), (16.0, 12.0),
    (83.0, 14.0), (83.0, 37.0), (83.0, 62.0), (116.0, 64.0), (125.0, 40.0), (114.0, 12.0),
    (25.0, 78.0), (47.0, 78.0), (61.5, 78.0), (73.0, 78.0), (95.0, 78.0), (105.0, 78.0)]]
# SGND stitching inside the island
VIAS += [("SGND", x, y, 0.8, 0.4) for x, y in [
    (38.0, 30.0), (46.0, 38.0), (61.5, 30.0), (61.5, 45.0), (72.0, 50.0), (72.0, 62.0), (40.0, 12.0)]]
FULL = [(0, 0), (W, 0), (W, H), (0, H)]

SILK = [
    ("+V", 14.0, 70.5, 1.5), ("0V", 57.0, 70.5, 1.5), ("-V", 116.0, 70.5, 1.5),
    ("SPK+", 80.0, 70.5, 1.2), ("SPK-", 88.0, 70.5, 1.2),
    ("IN", 34.6, 70.0, 1.0), ("GND", 45.0, 69.9, 0.8), ("MUTE", 66.27, 78.6, 1.0),
    ("STAR", 49.0, 74.6, 1.0),
    ("TDA7294 MONO  rev 1.0", 100.0, 63.0, 1.5),
    ("Currently Amped  2026", 100.0, 66.0, 1.2),
    ("HEATSINK EDGE  U1 TAB = -V", 98.0, 2.6, 0.9),
]

# ------------------------------------------------------------------ project
NETCLASS = {
    "Default": dict(clearance=0.4, track_width=0.4, via_diameter=0.8, via_drill=0.4),
    "Power": dict(clearance=0.6, track_width=2.5, via_diameter=1.6, via_drill=0.8),
}


def write_project():
    def nc(name, d):
        return {"name": name, "clearance": d["clearance"], "track_width": d["track_width"],
                "via_diameter": d["via_diameter"], "via_drill": d["via_drill"],
                "microvia_diameter": 0.3, "microvia_drill": 0.1,
                "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
                "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
                "schematic_color": "rgba(0, 0, 0, 0.000)", "wire_width": 6, "bus_width": 12}
    root = str(uuid.uuid5(uuid.NAMESPACE_URL, "tda7294-root"))
    pro = {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {"board_outline_line_width": 0.15, "copper_line_width": 0.2,
                             "silk_line_width": 0.15, "silk_text_size_h": 1.0,
                             "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
                "rules": {"min_clearance": 0.2, "min_copper_edge_clearance": 0.5,
                          "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
                          "min_through_hole_diameter": 0.3, "min_track_width": 0.2,
                          "min_via_annular_width": 0.13, "min_via_diameter": 0.5,
                          "min_silk_clearance": 0.0, "min_text_height": 0.8,
                          "min_text_thickness": 0.08},
                "rule_severities": {"silk_over_copper": "ignore", "silk_overlap": "ignore",
                                    "silk_edge_clearance": "ignore",
                                    "lib_footprint_issues": "ignore",
                                    "lib_footprint_mismatch": "ignore"},
                "track_widths": [0.0, 0.4, 0.5, 1.5, 2.5],
                "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                                   {"diameter": 1.6, "drill": 0.8}],
            },
            "layer_presets": [], "viewports": [],
        },
        "boards": [],
        "meta": {"filename": NAME + ".kicad_pro", "version": 1},
        "net_settings": {
            "classes": [nc(k, v) for k, v in NETCLASS.items()],
            "meta": {"version": 3},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in sorted(POWER_NETS)],
        },
        "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[root, ""]],
        "text_variables": {},
    }
    with open(PRO, "w") as f:
        json.dump(pro, f, indent=2)


# ------------------------------------------------------------------ helpers
def V(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))


LAYER = {"F": pcbnew.F_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu, "B": pcbnew.B_Cu}


def build():
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    for lay, nm in [(pcbnew.F_Cu, "F.Cu"), (pcbnew.In1_Cu, "In1.GND"),
                    (pcbnew.In2_Cu, "In2.PosRail"), (pcbnew.B_Cu, "B.NegRail")]:
        board.SetLayerName(lay, nm)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))

    nets = {}

    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    root = str(uuid.uuid5(uuid.NAMESPACE_URL, "tda7294-root"))
    for ref, (lib_id, value, fpk, pins, fields) in PARTS.items():
        lib, fname = FP[fpk].split(":")
        fp = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fname)
        fp.SetFPID(pcbnew.LIB_ID(lib, fname))
        fp.SetReference(ref)
        fp.SetValue(value)
        sym_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, "tda7294/sym/" + ref))
        fp.SetPath(pcbnew.KIID_PATH("/" + sym_uuid))
        for k, v in fields.items():
            if k != "DNP":
                fp.SetProperty(k, v)
        if fields.get("DNP") == "yes" or ref.startswith("NT"):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
        if ref == "U1":
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = "${KIPRJMOD}/3dmodels/TDA7294_Multiwatt15V.wrl"
            m.m_Show = True
            fp.Models().clear()
            fp.Models().push_back(m)
        x, y, rot = PLACE[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        if ref[0] in "JH" or ref.startswith("NT"):
            fp.Reference().SetVisible(False)
        if ref in REF_POS:
            fp.Reference().SetPosition(V(*REF_POS[ref]))
        for pad in fp.Pads():
            num = pad.GetNumber()
            key = int(num) if num.isdigit() else num
            if key in pins:
                pad.SetNet(net(pins[key]))
            if ref == "U1":
                pad.SetDrillSize(pcbnew.VECTOR2I(MM(1.1), MM(1.1)))
                if key in pins and pins[key] in ("+V", "-V", "SGND"):
                    pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        board.Add(fp)

    # board outline with 2 mm corner radius
    r = 2.0
    segs = [((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r))]
    for a, b in segs:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(*a))
        s.SetEnd(V(*b))
        s.SetWidth(MM(0.15))
        board.Add(s)
    k = r * (1 - 0.7071068)
    for st, md, en in [((0, r), (k, k), (r, 0)), ((W - r, 0), (W - k, k), (W, r)),
                       ((W, H - r), (W - k, H - k), (W - r, H)), ((r, H), (k, H - k), (0, H - r))]:
        a = pcbnew.PCB_SHAPE(board)
        a.SetShape(pcbnew.SHAPE_T_ARC)
        a.SetLayer(pcbnew.Edge_Cuts)
        a.SetArcGeometry(V(*st), V(*md), V(*en))
        a.SetWidth(MM(0.15))
        board.Add(a)

    for netname, lay, w, pts in TRACKS:
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(V(x1, y1))
            t.SetEnd(V(x2, y2))
            t.SetWidth(MM(w))
            t.SetLayer(LAYER[lay])
            t.SetNet(net(netname))
            board.Add(t)

    def zone(layer, netname, poly, prio, clearance=0.5, spoke=1.0, gap=0.5):
        z = pcbnew.ZONE(board)
        z.SetLayer(LAYER[layer])
        z.SetNet(net(netname))
        ol = z.Outline()
        ol.NewOutline()
        for x, y in poly:
            p = V(x, y)
            ol.Append(p.x, p.y)
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(clearance))
        z.SetMinThickness(MM(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(gap))
        z.SetThermalReliefSpokeWidth(MM(spoke))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetZoneName(f"{netname}_{layer}")
        board.Add(z)

    zone("In1", "SGND", SGND_ISLAND, 2)
    zone("In1", "PGND", FULL, 1)
    zone("F", "SGND", SGND_ISLAND, 2, clearance=0.5)
    zone("F", "PGND", FULL, 1, clearance=0.6)
    zone("In2", "+V", FULL, 1, spoke=1.2)
    zone("B", "-V", FULL, 1, spoke=1.2)

    ko = pcbnew.ZONE(board)
    ko.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ko.SetLayerSet(ls)
    ko.SetDoNotAllowCopperPour(True)
    ko.SetDoNotAllowTracks(False)
    ko.SetDoNotAllowVias(False)
    ko.SetDoNotAllowPads(False)
    ko.SetDoNotAllowFootprints(False)
    ol = ko.Outline()
    ol.NewOutline()
    for x, y in NT1_KEEPOUT:
        p = V(x, y)
        ol.Append(p.x, p.y)
    ko.SetZoneName("star_keepout")
    board.Add(ko)

    for netname, x, y, d, drill in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y))
        v.SetWidth(MM(d))
        v.SetDrill(MM(drill))
        v.SetNet(net(netname))
        board.Add(v)

    for text, x, y, size in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(V(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
        t.SetTextThickness(MM(size * 0.15))
        board.Add(t)
    return board


STACKUP = """    (stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.07))
      (layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.07))
      (layer "dielectric 2" (type "core") (thickness 0.9) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.07))
      (layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.07))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )
"""


def patch_stackup(path):
    s = open(path).read()
    if "(stackup" in s:
        a = s.index("    (stackup")
        depth, i = 0, a
        while True:
            if s[i] == "(":
                depth += 1
            elif s[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        s = s[:a] + STACKUP.rstrip("\n") + s[i + 1:]
    else:
        s = s.replace("  (setup\n", "  (setup\n" + STACKUP, 1)
    open(path, "w").write(s)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    b = build()
    pcbnew.SaveBoard(PCB, b, True)
    patch_stackup(PCB)
    write_project()
    b = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b, True)
    print("saved", PCB)
