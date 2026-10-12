# Virtual BMS for Victron (Node-RED)

A software "virtual BMS" that reads your real BMS's cell data, computes **granular**
charge limits, and feeds them to the Victron system through a virtual
`com.victronenergy.battery` service. It lets you:

- **Head off high cells** — fold charge current/voltage back as the top cell approaches
  a ceiling, so the pack never gets pushed into overvoltage.
- **Hold absorption until the pack is synced** — stay at the absorption target until
  **every cell is within 0.08 V of each other _or_ at/above 3.55 V per cell**, then
  release to float and treat the pack as 100 %.

> **Safety first.** This is an *optimisation layer*, not a protection device. Program
> conservative charge limits directly into your **MPPTs and inverter/charger** as the
> hardware failsafe. If Node-RED hangs, MQTT drops, or the GX reboots, those hardware
> limits — and your real hardware BMS's own cutoffs — must still keep the pack safe.
> The flow's watchdog backs this up: if cell data goes stale it falls to conservative
> limits (SAFE mode), but it is never the last line of defence.

## The three versions

The control core (state machine, fold-back, watchdog, virtual-battery output,
keep-alive) is **byte-identical** in all three. Only the ingest front-end differs, so
you run the one that matches your cell-data source and can diff it against a sibling
when troubleshooting.

| File | Use when your cells come from |
|------|-------------------------------|
| `vbms-v1-dbus-serialbattery.json` | A BMS via **dbus-serialbattery** (JK/JBD/Daly/Seplos/Pace…). Reads `N/+/battery/+/System/Max\|MinCellVoltage`. |
| `vbms-v2-native-can.json` | A **native CAN-bus BMS** (Pylontech/BYD/Lynx…). Same Victron topics, but many CAN BMSes publish only Min/Max cell voltage — confirm both update. |
| `vbms-v3-custom-mqtt.json` | A BMS on **its own MQTT topics**. Edit the `mqtt-in` topic and the `INGEST (custom)` parser to match your payload. |

All three reuse your existing MQTT broker config node (`localhost:1883`). If you import
them into a different Node-RED, repoint the `mqtt in`/`mqtt out` nodes at your broker.

## Install

1. In Node-RED: **Menu → Import**, paste one file's JSON (or import the file), **Import**.
2. Make sure the `node-red-contrib-victron` palette is installed and recent enough to
   provide the **Virtual Device** node (`victron-virtual`). Open the **VBMS virtual
   battery** node and confirm *Device = Battery*; set capacity and voltage preset for
   your pack.
3. Open the **CONFIG** function node, set your pack parameters (see below), **Deploy**.
4. In the GX: **Settings → DVCC → enable DVCC**, then set the **controlling BMS** (and,
   if you like, the **battery monitor**) to this virtual battery. The whole system will
   then obey the CVL/CCL/DCL this flow computes.
5. Verify in the **decision** debug node (sidebar) that `maxCell`/`minCell` update and
   the stage advances BULK → ABSORB → FLOAT as expected **before** you rely on it.

## Tuning (the CONFIG node)

Defaults are LiFePO4, 16S (≈48 V). Change `cellCount` for your series count; all pack
voltages are derived from the per-cell numbers × `cellCount`.

| Key | Default | Meaning |
|-----|---------|---------|
| `cellCount` | 16 | Series cells (16S≈48 V, 8S≈24 V, 4S≈12 V). |
| `cellSyncV` | 3.55 | A cell at/above this counts as full. |
| `cellBalanceDelta` | 0.08 | Max−min at/below this counts as balanced. |
| `cellProtectV` | 3.60 | Fold-back begins above this (top cell). |
| `cellMaxV` | 3.65 | Software ceiling: CCL→0, CVL clamped to `cellMaxV × cellCount`. |
| `cellFloatV` | 3.375 | Per-cell float target. |
| `chargeMax` | 100 | Normal charge-current limit (A). |
| `chargeHoldMin` | 5 | CCL floor during float (A). |
| `dischargeMax` | 200 | Discharge-current limit (A). |
| `watchdogMs` | 20000 | No fresh cell data this long → SAFE mode. |
| `absorbHoldMaxMs` | 7200000 | Cap balance-hold at 2 h, then float anyway. |
| `safeCellV` / `safeChargeMax` | 3.45 / 20 | Conservative SAFE-mode fallback. |

**Sync condition:** `minCell ≥ cellSyncV` **OR** `(maxCell − minCell) ≤ cellBalanceDelta`.

## How the control works

```
        ┌────────────────────────── fold-back overlay (any stage) ──────────────────────────┐
        │  if maxCell > cellProtectV:  CCL ramps chargeMax → 0 as maxCell → cellMaxV          │
        │                              CVL clamped to cellMaxV × cellCount                    │
        └────────────────────────────────────────────────────────────────────────────────────┘

  BULK ──(maxCell ≥ cellSyncV  OR  packV ≥ absorb target)──▶ ABSORB ──(synced)──▶ FLOAT
   ▲   CVL = sync×N, CCL = chargeMax        CVL = sync×N, CCL = chargeMax   CVL = float×N
   │                                        holds here, tapering & balancing  CCL = chargeHoldMin
   └──────────────(maxCell drops & SOC < 95%)───────────────────────────────────┘

  SAFE (overlay): stale/missing cell data → CVL = safeCellV×N, CCL = safeChargeMax
                  (the charge stage is preserved and resumes when data returns)
```

The controller runs every 2 s. It settles the stage first, then derives the limits, so
the stage label and the commanded limits are always consistent. All thresholds use a
small epsilon so a pack sitting exactly on a limit behaves correctly.

## Troubleshooting

- The node under **CONTROLLER** shows a live status: stage, CVL, CCL, delta, and any
  note. Red = SAFE, green = FLOAT, yellow = charging.
- Stuck in **SAFE**? Cell data isn't arriving. Check the ingest `mqtt in` topics and the
  **decision** debug for `maxCell`/`minCell`. For Victron MQTT, values stop streaming
  without a keep-alive — this flow publishes `R/<portal>/keepalive` every 30 s once it
  has learned the portal ID from an incoming `N/<portal>/…` message.
- Virtual battery not selectable as controlling BMS? Some Venus OS / palette versions had
  a bug where virtual batteries didn't appear in the picker. Update the palette and
  firmware.
- Victron advises battery charge parameters be supplied by a dbus battery service (which
  is exactly what the virtual device is) rather than by raw MQTT writes — this flow does
  it the supported way.

## Verified against

- `com.victronenergy.battery` D-Bus spec — `Info/MaxChargeVoltage`,
  `Info/MaxChargeCurrent`, `Info/MaxDischargeCurrent`, `Dc/0/*`, `Soc`,
  `System/Min|MaxCellVoltage`, `Alarms/HighCellVoltage`, `Alarms/CellImbalance`.
- `node-red-contrib-victron` virtual battery node — input contract
  `msg.payload = { "Info/MaxChargeVoltage": 56.0, … }`, paths without the leading slash;
  `msg.connected` to take the service offline.

The state machine was simulated through a full charge cycle (bulk → fold-back → sync →
float → re-bulk) and a watchdog dropout before release.
