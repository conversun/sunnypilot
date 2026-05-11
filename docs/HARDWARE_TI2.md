# Mazda 3 2019 + TI2 — Hardware Reference

This branch (`mazda-3-2019-community`) targets the Mazda 3 2019+ GEN2 platform
with the **MoreTorque Torque Interceptor 2 (TI2)** hardware add-on. The TI2 is
a physical prerequisite — without it, openpilot cannot send LKAS steering
commands to the GEN2 EPS. This document is a reference, not a step-by-step
install guide; for the actual install procedure follow the vendor docs linked
below.

> [!WARNING]
> This is alpha software running on a previously-unsupported car configuration.
> You are the test pilot. The system has not been validated on your specific
> vehicle. **Always keep your hands near the wheel and be ready to take over
> immediately.** Read the [Safety Disclaimer](#safety-disclaimer) section in
> full before using this branch.

---

## Overview

The Torque Interceptor 2 (TI2) sits transparently on CAN bus 1 between the
front-sensing camera and the Mazda GEN2 EPS module. Mechanically and
electrically it is a passive relay: it forwards `EPS_LKAS (0x249)` and
`EPS_FEEDBACK (0x24B)` frames between camera and EPS while exposing those same
addresses to a panda on the comma device. To the openpilot stack the TI2 is
invisible at the protocol layer — the code reads/writes the **native GEN2 EPS
protocol** (`EPS_LKAS 0x249` on bus 1, `EPS_FEEDBACK 0x24B` on bus 1) without
any TI-specific flags or code paths.

This is intentional and is the reason `MAZDA_3_2019` is configured with
`flags=MazdaFlags.GEN2` only (no `TORQUE_INTERCEPTOR` flag). See
`docs/migration/DECISIONS.md` (D-005, D-010) for the full rationale and the
failure mode that prompted dropping the flag.

---

## Why TI2 Is Required

The Mazda GEN2 EPS module ignores LKAS torque commands from any source it
doesn't recognise as the factory front camera. Without TI2, you cannot inject
steering commands at all — the stock EPS will reject any frame the panda
sends. TI2 provides the missing torque-injection path by acting as a trusted
intermediate on the EPS torque-sensor bus.

The TI2 contains four independent ASIL-B+ microcontrollers wired to the four
torque-sensor channels of the JTEKT column EPS. The MCUs operate as two
redundant pairs and do not communicate with each other to control steering.
The worst-case failure mode is **sudden loss of power steering**, not a
runaway steering input — but this can still cause an accident if you are not
ready to take over manually.

---

## BOM

| Item | Vendor | Notes |
|---|---|---|
| **MoreTorque Torque Interceptor 2 (TI2)** | [torqueinterceptor.com](https://torqueinterceptor.com/en-us/products/torque-interceptor-2) | ~$439 USD. Includes BCM intercept harness. Made by MoreTorque (ryleymcc). |
| **BCM Intercept Harness** | [torqueinterceptor.com](https://torqueinterceptor.com/en-us/products/mazda-bcm-intercept-harness-for-openpilot) | ~$147 USD if purchased separately. Bundled with TI2. |
| **comma 3X** (or Springer A1) | [comma.ai/shop](https://comma.ai/shop/products/three) / [springerelectronics.com](https://springerelectronics.com/shop/springer-a1/) | The openpilot computer. |
| **Harness box / relay** | [comma.ai/shop/harness-box](https://comma.ai/shop/harness-box), [RetroPilot](https://shop.retropilot.org/product/oshw-relay/), or compatible | Required to enable openpilot relay (block stock camera, inject openpilot). |
| **Mazda car harness** | [comma.ai/shop](https://comma.ai/shop/products/mazda-connector) | Same connector used by upstream Mazda CX-5 2022 / CX-9 2021. |
| **Comma power v3 + OBD-C cable + mount** | [comma.ai/shop](https://comma.ai/shop) | Standard accessories. |

MoreTorque also sells an **All-in-One bundle** (~$1,317 pre-order) that includes
the TI2, Springer A1 device, harness box, harness, OBD power, RJ-45 cable,
and USB-C cable.

---

## Install Reference

This document does not duplicate the vendor's install instructions because
they evolve and the vendor's documentation is the authoritative source. Follow
the official guides in this order:

1. **TI2 install steps** —
   [MoreTorque TI2 installation guide](https://moretorques-organization.gitbook.io/ti2-installation/)
   (covers disconnect battery, BCM intercept harness, EPS connector swap,
   RJ-45 to comma device).
2. **Mazda wiring reference** —
   [commaai/openpilot wiki — Mazda](https://github.com/commaai/openpilot/wiki/Mazda)
   (harness routing photos and connector locations for 2019–2023 Mazda 3 / CX-30
   / CX-50).
3. **comma 3X mount + power** —
   [community.sunnypilot.ai — Getting started](https://community.sunnypilot.ai/t/getting-started-using-sunnypilot-in-your-supported-car/251).
4. **Vendor support channel** —
   [MoreTorque Discord](https://discord.gg/K4kfUqAMsB) for TI2 install
   questions and error-code triage (green/blue LED flash patterns).

After physical install but before flashing this branch, **always do the post-
install key-cycle test described in the MoreTorque guide** — the TI2 must boot
to its run state without throwing error flashes before you connect a comma
device.

---

## CAN Bus / Protocol Reference

| Bus | CAN ID | Message | Direction | Purpose |
|---|---|---|---|---|
| 0 | 0x240 | `STEER_TORQUE` | EPS → vehicle | Driver torque sensor (used for hands-on detection) |
| 1 | 0x249 | `EPS_LKAS` | openpilot ↔ TI2 ↔ EPS | LKAS torque command (50 Hz target) |
| 1 | 0x24A | `TI_FEEDBACK` | TI2 → openpilot | TI2 state, torque sensor mirror, fault bits |
| 1 | 0x24B | `EPS_FEEDBACK` | EPS → openpilot | Steering angle, EPS torque measurement |
| 2 | 0x220 | `ACC` | camera → vehicle (MITM by openpilot) | ACC command. Panda blocks stock; carcontroller echoes with HOLD/RESUME overrides. |

Key constants (all from `opendbc/car/mazda/values.py`):

| Constant | Value | Notes |
|---|---|---|
| `MazdaFlags.GEN2` | `2` | Set on `MAZDA_3_2019` PlatformConfig |
| `MazdaFlags.TORQUE_INTERCEPTOR` | `8` | **NOT set** for `MAZDA_3_2019` — TI2 is transparent at protocol layer |
| `steerActuatorDelay` | `0.335 s` | GEN2 EPS round-trip |
| `steerLimitTimer` | `0.8 s` | Steering hold-time on disengage |
| `STEER_MAX` (GEN2) | `8000` | Maximum LKAS torque magnitude |
| `NON_LINEAR_TORQUE_PARAMS` | `(4.6, 0.6, 0.134, 0.3605)` | Lateral plant params; may need retune on your World Model |
| `hold_delay` / `hold_timer` / `resume_timer` | `0.5 s / 6.0 s / 0.5 s` | Standstill ACC echo timing |

Full per-file architecture rationale lives in `docs/migration/DECISIONS.md`
(D-002 through D-010).

---

## Verify

The migration docs ship a complete pre-drive verification harness. Run these
**before** the first drive, in this order:

### 1. Static check on the device

```bash
bash docs/migration/T17_T18_device_verification.sh
```

Expected: all five phases (PREREQ, B static, C import + checksum trace,
D pytest, E scons) exit 0. Phase D should report **79 passed, 15 skipped,
0 failed** for the Mazda safety tests.

### 2. Boot + fingerprint

Power on the car. The UI must show **"Mazda 3 2019-24"** within ~10 seconds
of boot. If it shows "Car Unrecognized" your ECU firmware version is not in
`fingerprints.py` — run `python3 tools/car_porting/auto_fingerprint.py` on
the device and extend the platform's `FW_VERSIONS` dict.

### 3. Pre-engage CAN observation (5 min, in Park, engine running)

Sit in Park with the engine running. Do **not** engage openpilot yet. Open
cabana (or check via connect.comma.ai) and verify:

- `TI_FEEDBACK.STATE` (0x24A bus 1) reaches `3` (RUN) within 30 seconds
- `EPS_LKAS` (0x249 bus 1) is present at ~50 Hz
- `EPS_FEEDBACK` (0x24B bus 1) is present and steering angle updates as you
  turn the wheel by hand
- `ACC` frames (0x220 bus 2) are present from the camera

If `TI_FEEDBACK.STATE` does not reach RUN, the TI2 has not initialised —
power-cycle the car and check TI2 LED flash codes against the MoreTorque
documentation. **Do not engage openpilot until STATE = RUN.**

### 4. CP-A / CP-B / CP-C drives

The full bring-up protocol lives in `docs/migration/T21_onvehicle_bringup_checklist.md`.
The three checkpoints, in order:

| Checkpoint | What it tests | Speed cap | Environment |
|---|---|---|---|
| **CP-A** | Lateral engages, TI2 STATE stays RUN, no EPS fault | 30 km/h | Empty parking lot |
| **CP-B** | Lateral with TI2 active, lane centering at 30/50/80 km/h, curve handling | 80 km/h | Quiet straight road |
| **CP-C** | Longitudinal ACC echo + lateral, hold/resume, gap stability | 60–100 km/h | Quiet 4-lane highway |

After each drive, run `docs/migration/T21_cabana_capture.sh` to pull the
route and check for `steerFaultPermanent`, missing `lat_active` frames, or
bad accel frames. Triage matrices for each checkpoint live in
`T21_onvehicle_bringup_checklist.md`.

---

## Feature Status

| Feature | Status |
|---|---|
| Lateral control via TI2 | **Code complete, unvalidated on v0.11 World Model** — `NON_LINEAR_TORQUE_PARAMS` was tuned on an older WM; expect possible retune |
| Standstill ACC hold/resume | **Active** when alpha-long is OFF (stock ACC pass-through with MITM hold/resume — see D-008) |
| `alphaLongitudinalAvailable` | **True** for `MAZDA_3_2019` (and any GEN2). The toggle is exposed in non-release branches such as this community branch. |
| `openpilotLongitudinalControl` | **Off by default; on when the user enables alpha-long.** When on, carcontroller writes `ACCEL_CMD = clip(accel*200 + 2000, 1300, 2400)` into `MAZDA_2019_ACC` frame on bus 2, replacing the stock cam frame. Panda safety enforces `MAZDA_2019_LONG_LIMITS` (max=2400, min=1300, inactive=2000). |
| `steerFaultPermanent` for GEN2 | **Not wired** — the code always returns `False`. **You are the fault detector.** |
| TI2 fault handling | INIT(1)/STANDBY(2) auto-recover; only ERROR(4)/CRITICAL_ERROR(5) latch (D-010) |

See `docs/migration/ROADMAP.md` for the priority queue.

---

## Disclaimer

openpilot is alpha software. This branch runs openpilot on a car
configuration that is **not officially supported by comma.ai**. The
[comma.ai blog post on safer control of steering][comma-safety] explicitly
advises against torque interceptors. **Use this software at your own risk.**

[comma-safety]: https://blog.comma.ai/safer-control-of-steering/

Specific risks for this branch:

1. **TI2 acts directly on the EPS torque-sensor signal.** A TI2 fault mid-
   drive can cause the EPS module to see an unexpected torque reading. In
   the worst case this is a momentary steering anomaly before the EPS falls
   back to stock behavior. Practice the takeover: grab the wheel firmly and
   steer manually.

2. **`steerFaultPermanent` is not wired for GEN2.** openpilot will **not**
   self-disengage on an EPS fault. The EPS warning light on the dash is your
   only fault indicator. If it lights up, take over and pull over.

3. **ACC without BlendedACC may engage/disengage more abruptly than stock MRCC.**
   The GEN2 ACC path sends commands directly to 0x220 bus 2. Without the
   BlendedACC filter (dropped in D-003), transitions may feel sharper. This
   is expected.

4. **Lateral tuning is from a previous World Model.** `NON_LINEAR_TORQUE_PARAMS
   = (4.6, 0.6, 0.134, 0.3605)` was tuned before v0.11. At v0.11 the lateral
   feel may differ. Start slow and capture cabana logs.

5. **First drive: empty space, speed under 30 km/h only. No exceptions.**

6. By using this software you accept all responsibility for anything that
   might occur while you use it. All contributors to this fork are not liable.
   Use at your own risk. Fork contributors assume no liability for your use
   of this software or any hardware (including TI2). MoreTorque™ Torque
   Interceptor is not associated with comma.ai or sunnypilot.

---

## Further Reading

- **Architecture decisions** — `docs/migration/DECISIONS.md` (D-002 through D-010)
- **Migration guide** — `docs/migration/MIGRATION_GUIDE.md`
- **Bring-up checklist** — `docs/migration/T21_onvehicle_bringup_checklist.md`
- **Roadmap & known limitations** — `docs/migration/ROADMAP.md`
- **Port status quick reference** — `docs/migration/PORT_STATUS.md`
- **MoreTorque TI2 docs** — [moretorques-organization.gitbook.io](https://moretorques-organization.gitbook.io/openpilot-mazda-community-support)
- **MoreTorque TI2 risks page** — [moretorques-organization.gitbook.io/torque-interceptor-2/risks](https://moretorques-organization.gitbook.io/torque-interceptor-2/risks)
- **MoreTorque Discord** — [discord.gg/K4kfUqAMsB](https://discord.gg/K4kfUqAMsB)
- **commaai/openpilot wiki — Mazda** — [github.com/commaai/openpilot/wiki/Mazda](https://github.com/commaai/openpilot/wiki/Mazda)
- **sunnypilot community forum — Mazda** — [community.sunnypilot.ai/c/vehicle-talk/mazda](https://community.sunnypilot.ai/c/vehicle-talk/mazda/)
