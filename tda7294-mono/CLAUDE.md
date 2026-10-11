# TDA7294 mono module — project context for Claude Code

Owner: Warren Oelofse (Currently Amped, Harare). Hands-on electronics, ~30 years.
Goal: a "definitive" 4-layer version of a hand-drawn single-sided TDA7294 board that has been
dead silent for 12 years. **Keep the proven circuit and grounding topology. Don't "improve" it away.**

## Source design
- The classic French magazine module, as republished at
  https://www.homemade-circuits.com/100-watt-power-amplifier-circuit-using-a-single-ic-tda7294/
- Values:
  - Gain set by R1 = 680 and R5 = 22k (about 33x), with C3 = 100 µF in the feedback leg.
  - Input: C2 = 1 µF and R2 = 22k.
  - Bootstrap: C4 = 100 µF, with + to pin 6.
  - Mute/standby network: R3 22k, R4 10k, R6 33k, D1 1N4148, C1/C10 10 µF.
  - Rail decoupling: 100 nF + 10 µF film (C9/C11) + bulk electrolytic.

## Decisions made with Warren
- **Mono modules, one board per channel.** Build 2 for stereo, possibly 4 later. No stereo or bridged board.
- **Speakers and supply.**
  - 4 Ω speakers.
  - Transformer: 2 × 22 V, 300 VA, fed from Victron inverters set to 240 V.
  - Idle rails are about ±33–35 V, sagging to about ±28 V at full power. The absolute limit is ±40 V.
  - The current supply works perfectly. Don't redesign it.
- **Component choices** (Warren's preference, from good past results):
  - All electrolytics: **Panasonic FC**.
  - All resistors: **1 % metal film**.
- **Fab:** 4 layers, 2 oz copper on all layers, plated through holes, ENIG finish.
- **Local rail caps.** The FC series has no 10 000 µF at 50 V, so each rail gets 2 × EEU-FC1H222
  (2200 µF 50 V, 18 × 35.5 mm, 7.5 mm pitch). The big reservoir caps stay in the PSU.
- **Optional RF input filter.** R7 = 0 Ω by default (100 Ω option); C12 = 470 pF, not fitted.
  This addresses the article's note about oscillation with high-impedance sources.
- **Possible future project:** a 2500 VA transformer salvaged from a scrapped Victron inverter.
  Its windings haven't been measured yet. Thoughts so far:
  - Its battery-side winding may or may not have a centre tap.
  - An option is to wind new 22-0-22 V secondaries on the core.
  - With a core that size, a soft-start and per-module rail fuses are essential.

## Layout rules (keep these)
- **Stackup.**

  | Layer | Contents |
  |---|---|
  | F.Cu | Signals; PGND pour on the side arms; SGND pour over the signal area |
  | In1 | SGND island under the small-signal parts; PGND everywhere else |
  | In2 | +V, full plane |
  | B.Cu | −V, full plane |

- **Ground domains.**
  - SGND: input ground, R2, C3, C1, C10, C12, and IC pins 1 and 4.
  - PGND: rail caps, C5/C6/C9/C11, the speaker return, and PSU 0 V.
  - The two domains meet only at net tie NT1 ("STAR") beside the 0 V pad.
- **Pin 14.** Feedback and bootstrap use a thin sense track taken right at pin 14.
  The speaker current uses a separate 2.5 mm track routed over PGND.
- **Net classes.**
  - Power (+V, −V, PGND, OUT): 2.5 mm track, 0.6 mm clearance, 1.6/0.8 mm via.
  - Default: 0.4 mm track, 0.4 mm clearance.
- **Pad connections.** Wide thermal spokes everywhere, except solid connections on the IC's
  +V, −V and SGND pins. IC holes are 1.1 mm.

## Files
- `gen/circuit.py` is the **single source of truth**: parts, values, footprints and pin-to-net mapping.
- `gen/gen_sch.py` builds the schematic. `gen/gen_pcb.py` builds the board: placement, tracks, zones,
  stackup, and the project file with net classes.
- `gen/render.py` produces the renders. `gen/gen_model.py` builds the TDA7294 3D model, since KiCad has none.
- `gen/check_net.py` checks the schematic netlist against `circuit.py`. `gen/drc.py` runs DRC.
- To rebuild everything (KiCad 7+ Python, run from `gen/`):
  ```
  python3 gen_sch.py ../kicad/tda7294_mono.kicad_sch
  python3 gen_pcb.py ../kicad
  python3 drc.py ../kicad/tda7294_mono.kicad_pcb
  kicad-cli sch export netlist --format kicadxml -o /tmp/net.xml ../kicad/tda7294_mono.kicad_sch && python3 check_net.py /tmp/net.xml
  python3 render.py ../kicad/tda7294_mono.kicad_pcb ../renders   # needs vtk, cairosvg, pillow
  ```
- Some paths in the scripts assume the Linux KiCad install (`/usr/share/kicad/...`) and use
  `/tmp/claude-0/...` as scratch space. Adjust these for macOS or Windows.
- Rev 1.0 status: DRC shows 0 violations and 0 unconnected; the schematic, PCB and `circuit.py` match.

## Open items before ordering
1. **Heatsink bracket and standoff holes (H1–H4) are placeholders** at the board corners.
   Get the real bracket spacing and offsets from Warren's prototype/heatsink.
2. Check the Multiwatt15 lead form of the parts on hand. The footprint is TO-220-15 StaggerOdd, vertical.
3. Do a 1:1 paper print check of the film-cap bodies (C2, C9, C11), since sizes vary by brand.
4. Fab review for 2 oz copper on the inner layers, with 0.4/0.4 mm minimum track and gap.
