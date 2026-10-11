"""Single source of truth for the TDA7294 mono module.

Every part: reference -> (lib_id, value, footprint, {pin: net}, extra fields).
Both the schematic and the PCB generator read this, so they cannot drift.
"""

FP = {
    "U":      "Package_TO_SOT_THT:TO-220-15_P2.54x2.54mm_StaggerOdd_Lead4.58mm_Vertical",
    "R":      "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "D":      "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
    "FC18":   "Capacitor_THT:CP_Radial_D18.0mm_P7.50mm",
    "FC10":   "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
    "FC5":    "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    "FILM10": "Capacitor_THT:C_Rect_L31.5mm_W13.0mm_P27.50mm_MKS4",
    "FILM1":  "Capacitor_THT:C_Rect_L18.0mm_W8.0mm_P15.00mm_FKS3_FKP3",
    "FILM01": "Capacitor_THT:C_Rect_L7.2mm_W3.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2",
    "PWRPAD": "Connector_Wire:SolderWire-1.5sqmm_1x01_D1.7mm_OD3.9mm",
    "SIGPAD": "Connector_Wire:SolderWire-0.5sqmm_1x01_D0.9mm_OD2.3mm",
    "TIE":    "NetTie:NetTie-2_SMD_Pad2.0mm",
    "HOLE":   "MountingHole:MountingHole_3.2mm_M3",
}

MF = "Metal film 1% 0.6W"
FC = "Panasonic FC"

# ref: (lib_id, value, fp_key, pins, fields)
PARTS = {
    "U1":  ("Amplifier_Audio:TDA7294", "TDA7294V", "U",
            {1: "SGND", 2: "IN-", 3: "IN+", 4: "SGND", 6: "BOOT", 7: "+V", 8: "-V",
             9: "STBY", 10: "MUTE", 13: "+V", 14: "OUT", 15: "-V"},
            {"Note": "Tab = -V. Insulate from heatsink (silpad + shoulder washer)"}),
    # --- gain / feedback ---------------------------------------------------
    "R1":  ("Device:R", "680", "R", {1: "IN-", 2: "FB_AC"}, {"Type": MF}),
    "R5":  ("Device:R", "22k", "R", {1: "OUT", 2: "IN-"}, {"Type": MF}),
    "C3":  ("Device:C_Polarized", "100uF 50V", "FC10", {1: "FB_AC", 2: "SGND"},
            {"Type": FC, "MPN": "EEU-FC1H101"}),
    # --- input ---------------------------------------------------------------
    "R7":  ("Device:R", "0R", "R", {1: "IN", 2: "IN_F"},
            {"Type": "0 ohm link (100R option for RF filter)"}),
    "C12": ("Device:C", "470pF", "FILM01", {1: "IN_F", 2: "SGND"},
            {"Type": "C0G/film, DO NOT FIT (RF filter option)", "DNP": "yes"}),
    "C2":  ("Device:C", "1uF 100V", "FILM1", {1: "IN_F", 2: "IN+"},
            {"Type": "MKP/MKS film, P15mm"}),
    "R2":  ("Device:R", "22k", "R", {1: "IN+", 2: "SGND"}, {"Type": MF}),
    # --- bootstrap -----------------------------------------------------------
    "C4":  ("Device:C_Polarized", "100uF 50V", "FC10", {1: "BOOT", 2: "OUT"},
            {"Type": FC, "MPN": "EEU-FC1H101", "Note": "+ to pin 6 (BOOT)"}),
    # --- mute / standby timing ----------------------------------------------
    "R4":  ("Device:R", "10k", "R", {1: "MUTE_IN", 2: "MUTE_N1"}, {"Type": MF}),
    "R6":  ("Device:R", "33k", "R", {1: "MUTE_N1", 2: "MUTE"}, {"Type": MF}),
    "D1":  ("Device:D", "1N4148", "D", {1: "MUTE_N1", 2: "MUTE"}, {}),  # 1=K 2=A
    "C1":  ("Device:C_Polarized", "10uF 50V", "FC5", {1: "MUTE", 2: "SGND"},
            {"Type": FC, "MPN": "EEU-FC1H100L"}),
    "R3":  ("Device:R", "22k", "R", {1: "MUTE_IN", 2: "STBY"}, {"Type": MF}),
    "C10": ("Device:C_Polarized", "10uF 50V", "FC5", {1: "STBY", 2: "SGND"},
            {"Type": FC, "MPN": "EEU-FC1H100L"}),
    # --- +V rail -------------------------------------------------------------
    "C5":  ("Device:C", "100nF 100V", "FILM01", {1: "+V", 2: "PGND"}, {"Type": "MKS/MKP film"}),
    "C9":  ("Device:C", "10uF 100V", "FILM10", {1: "+V", 2: "PGND"},
            {"Type": "MKS4 film (optional, as original)"}),
    "C7": ("Device:C_Polarized", "2200uF 50V", "FC18", {1: "+V", 2: "PGND"},
            {"Type": FC, "MPN": "EEU-FC1H222"}),
    "C13": ("Device:C_Polarized", "2200uF 50V", "FC18", {1: "+V", 2: "PGND"},
            {"Type": FC, "MPN": "EEU-FC1H222"}),
    # --- -V rail -------------------------------------------------------------
    "C6":  ("Device:C", "100nF 100V", "FILM01", {1: "PGND", 2: "-V"}, {"Type": "MKS/MKP film"}),
    "C11": ("Device:C", "10uF 100V", "FILM10", {1: "PGND", 2: "-V"},
            {"Type": "MKS4 film (optional, as original)"}),
    "C8": ("Device:C_Polarized", "2200uF 50V", "FC18", {1: "PGND", 2: "-V"},
            {"Type": FC, "MPN": "EEU-FC1H222"}),
    "C14": ("Device:C_Polarized", "2200uF 50V", "FC18", {1: "PGND", 2: "-V"},
            {"Type": FC, "MPN": "EEU-FC1H222"}),
    # --- star point ------------------------------------------------------------
    "NT1": ("Device:NetTie_2", "STAR", "TIE", {1: "SGND", 2: "PGND"}, {}),
    # --- wire pads -------------------------------------------------------------
    "J1":  ("Connector:Conn_01x01_Pin", "+V in", "PWRPAD", {1: "+V"}, {}),
    "J2":  ("Connector:Conn_01x01_Pin", "0V in", "PWRPAD", {1: "PGND"}, {}),
    "J3":  ("Connector:Conn_01x01_Pin", "-V in", "PWRPAD", {1: "-V"}, {}),
    "J4":  ("Connector:Conn_01x01_Pin", "SPK+", "PWRPAD", {1: "OUT"}, {}),
    "J5":  ("Connector:Conn_01x01_Pin", "SPK-", "PWRPAD", {1: "PGND"}, {}),
    "J6":  ("Connector:Conn_01x01_Pin", "Audio in", "SIGPAD", {1: "IN"}, {}),
    "J7":  ("Connector:Conn_01x01_Pin", "Audio gnd", "SIGPAD", {1: "SGND"}, {}),
    "J8":  ("Connector:Conn_01x01_Pin", "Mute (+V = play)", "SIGPAD", {1: "MUTE_IN"}, {}),
    # --- mechanical --------------------------------------------------------------
    "H1":  ("Mechanical:MountingHole", "Bracket M3", "HOLE", {}, {}),
    "H2":  ("Mechanical:MountingHole", "Bracket M3", "HOLE", {}, {}),
    "H3":  ("Mechanical:MountingHole", "Standoff M3", "HOLE", {}, {}),
    "H4":  ("Mechanical:MountingHole", "Standoff M3", "HOLE", {}, {}),
}

POWER_NETS = {"+V", "-V", "PGND", "OUT"}


def nets():
    out = {}
    for ref, (_, _, _, pins, _) in PARTS.items():
        for pin, net in pins.items():
            out.setdefault(net, []).append((ref, str(pin)))
    return out
