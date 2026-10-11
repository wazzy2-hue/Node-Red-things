# TDA7294 Mono Module — 4-layer "definitive" board (rev 1.0)

Redesign of the classic French TDA7294 module (as published on homemade-circuits.com) that has run
silently on the prototype for 12 years. Same circuit and values; new board.

Build two for a stereo pair (four for the 4-channel idea). One mono design = one fab order.

## Folder contents

| Path | What it is |
|---|---|
| `kicad/` | KiCad 7 project: `tda7294_mono.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, plus `3dmodels/` (TDA7294 Multiwatt15 model) |
| `fab/gerbers/` | Gerbers (4 copper layers, mask, silk, outline) + separate PTH/NPTH Excellon drill files and drill maps |
| `fab/tda7294_mono_BOM.csv` | Grouped bill of materials |
| `fab/tda7294_mono_schematic.pdf` | Schematic |
| `renders/` | 3D renders and flat top/bottom views |
| `gen/` | Python that generates everything from one netlist (`circuit.py`) — edit there and re-run |

Opens in KiCad 7 or newer (KiCad 8/9 will offer to upgrade the files).

## Board

- 130 × 80 mm, 1.6 mm, 4 layers, **2 oz copper on all layers**, **ENIG**, black mask / white silk
- Heatsink along the top edge. The TDA7294 tab back face sits on the board edge.
- H1/H2 (top corners): M3 heatsink bracket holes. H3/H4: M3 standoffs.
  **These hole positions are placeholders.** Check them against your brackets before ordering.

### Stackup

| Layer | Use |
|---|---|
| F.Cu | All signal routing. PGND pour on the side arms; SGND pour over the signal area |
| In1 | Ground: SGND island under the small-signal parts, PGND everywhere else |
| In2 | +V plane, full board |
| B.Cu | −V plane, full board (one short MUTE track crosses under the IC) |

The supply rails each get a full 2 oz plane. The +V and −V planes are 0.2 mm apart, so they
also act as distributed decoupling.

### Grounding (carried over from the original)

- **SGND**: input ground, R2, C3, C1, C10, C12, and IC pins 1 and 4.
- **PGND**: rail cap centre point, C5/C6/C9/C11, speaker return, PSU 0 V.
- They meet at exactly one place: **NT1, the net tie marked STAR**, beside the 0 V pad.
  KiCad's DRC enforces this, so the separation can't be lost by an edit.
- The speaker output track runs over PGND, not over the signal-ground island.
- Feedback (R5) and bootstrap (C4) are taken directly at pin 14 by a thin sense track.
  The speaker current leaves pin 14 by a separate 2.5 mm track.

### Design rules

| Class | Nets | Track | Clearance | Via |
|---|---|---|---|---|
| Power | +V, −V, PGND, OUT | 2.5 mm | 0.6 mm | 1.6 / 0.8 mm |
| Default | everything else | 0.4 mm | 0.4 mm | 0.8 / 0.4 mm |

The 0.6 mm clearance covers 80 V rail-to-rail with margin.

Plane connections use wide thermal spokes (1.0–1.2 mm) so heavy copper can still be hand-soldered.
The exception is the IC's +V/−V/SGND pins, which have **solid** connections. Use a hot iron there.

IC holes are opened to 1.1 mm for the Multiwatt legs.

DRC: 0 violations, 0 unconnected. The schematic netlist, the PCB pads and `circuit.py` were
cross-checked and match.

## Changes from the original

- **Local rail caps.** Each rail gets 2 × Panasonic FC 2200 µF 50 V (EEU-FC1H222, 18 × 35.5 mm)
  instead of one 10 000 µF. That is 4400 µF of very low-ESR capacitance right at the chip.
  The FC series doesn't go to 10 000 µF at 50 V, and 35 V is too close to your ±33–35 V idle
  rails. Keep the big reservoir caps in the PSU, as you have now.
- **All electrolytics Panasonic FC, 50 V.**
  - C3, C4: 100 µF (EEU-FC1H101)
  - C1, C10: 10 µF (EEU-FC1H100L)
- **All resistors metal film 1 % 0.6 W.**
- **C4 polarity: + to pin 6 (BOOT).** This is marked on the silkscreen.
- **Optional RF input filter.**
  - R7 is fitted as a 0 Ω link by default. Change it to 100 Ω if you want the filter.
  - C12 (470 pF) is not fitted by default.
  - The original article noted a slight tendency to oscillate from high-impedance sources.
- **C9/C11 (10 µF film) kept.** The original author called them optional, but your proven build has them.
- **Wire pads along the bottom edge.** From left to right: +V, IN, GND, 0V, MUTE, SPK+, SPK−, −V.
  - Tie MUTE to +V for play, or to GND for standby.

## Fab order notes

- 4 layers, 1.6 mm, 2 oz outer and 2 oz inner copper, ENIG, black mask, white silk.
- Use the stackup in the board file or the house equivalent (prepreg 0.2 / core ~0.9 / prepreg 0.2).
- Check the minimum track/gap for 2 oz copper with your fab. This design uses 0.4/0.4 mm.

## Before ordering — please verify

1. **Heatsink bracket and standoff hole positions**, against your hardware.
2. **The Multiwatt15 lead form of the TDA7294s you have.** The footprint is the standard
   "StaggerOdd" vertical form, the same one the original board uses.
3. **The tab insulation kit**: mica or silpad, plus a shoulder washer. The tab is at −V.
4. **Print the top layer 1:1** (from the KiCad PCB editor) and lay your actual parts on it,
   especially the film caps. Their bodies vary by brand.

The 3D models are generic KiCad library models, recoloured where noted. The TDA7294 model is a
simplified outline built for this project.
