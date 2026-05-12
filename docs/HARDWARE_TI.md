# Mazda Torque Interceptor Hardware Reference

This document covers both generations of the MoreTorque Torque Interceptor hardware used in the `mazda-multi-platform-community` branch:

- **Section 1 — TI1 (Original Torque Interceptor):** for GEN1 vehicles (Mazda 3, CX-5, CX-9, Mazda 6 pre-2021)
- **Section 2 — TI2 (Torque Interceptor 2):** for GEN2 vehicles (Mazda 3 2019+, CX-30, CX-50) and GEN3 vehicles (Mazda 3 2023+, CX-30 2023+)

> [!WARNING]
> This is alpha software running on previously-unsupported car configurations.
> You are the test pilot. The system has not been validated on your specific
> vehicle. **Always keep your hands near the wheel and be ready to take over
> immediately.** Read the [Safety Disclaimer](#safety-disclaimer) section in
> full before using this branch.

---

## Section 1 — TI1: Original Torque Interceptor (GEN1 Vehicles)

### Supported GEN1+TI Platforms

| Platform | Vehicle |
|----------|---------|
| `MAZDA_CX5_TI` | Mazda CX-5 (pre-2022) |
| `MAZDA_CX9_TI` | Mazda CX-9 (pre-2021) |
| `MAZDA_3_TI` | Mazda 3 (pre-2019) |
| `MAZDA_6_TI` | Mazda 6 |

### Overview

The Original Torque Interceptor (TI1) sits on CAN bus 1 between the front-sensing camera and the GEN1 EPS module. It intercepts the `CAM_LKAS (0x243 bus 0)` path and injects steering commands via `CAM_LKAS2 (0x249 bus 1)`. The TI1 also exposes a `TI_FEEDBACK (0x24A bus 1)` frame that reports TI state, torque sensor mirror, and fault bits.

GEN1+TI lateral control uses `TI_STEER_MAX=600` with `apply_ti_steer_torque_limits`. The standard GEN1 `CAM_LKAS (0x243)` frame is still sent on bus 0 alongside the TI frame on bus 1.

### **WARNING: Manual Platform Selection Required**

> **[!IMPORTANT]**
> **GEN1 and GEN1+TI variants share identical ECU firmware.** The TI1 hardware add-on has no firmware signature and does not change any ECU response. Auto-fingerprinting cannot distinguish a GEN1 car with TI1 installed from the same car without TI1.
>
> **You MUST manually select the correct `*_TI` variant** (e.g., `MAZDA_CX5_TI`) from the comma device car-selection menu after installation. If you select the base GEN1 variant (e.g., `MAZDA_CX5`) on a car with TI1 installed, openpilot will use the wrong safety mode. The panda will not detect this mismatch automatically.
>
> **Getting this wrong is a safety issue.** The wrong safety mode means the wrong TX whitelist and wrong torque limits. Always verify your platform selection before driving.

### CAN Bus / Protocol Reference (GEN1+TI)

| Bus | CAN ID | Message | Direction | Purpose |
|-----|--------|---------|-----------|---------|
| 0 | 0x243 | `CAM_LKAS` | openpilot | Standard GEN1 LKAS frame (still sent) |
| 1 | 0x249 | `CAM_LKAS2` | openpilot | TI1 torque injection frame (KEY=3294744160) |
| 1 | 0x24A | `TI_FEEDBACK` | TI1 | TI1 state, torque sensor mirror, fault bits |
| 0 | 0x09D | `CRZ_BTNS` | openpilot | Cruise control buttons |
| 0 | 0x440 | `LKAS_HUD` | openpilot | HUD display |

### TI1 State Machine

| State | Value | Meaning |
|-------|-------|---------|
| DISCOVER | 0 | Initializing |
| OFF | 1 | TI not active |
| DRIVER_OVER | 2 | Driver override detected |
| RUN | 3 | TI active and ready |

INIT(1)/STANDBY(2) auto-recover. Only ERROR(4)/CRITICAL_ERROR(5) latch as permanent faults (per D-010).

### BOM (GEN1+TI)

| Item | Vendor | Notes |
|------|--------|-------|
| **MoreTorque Original Torque Interceptor (TI1)** | [torqueinterceptor.com](https://torqueinterceptor.com) | Original TI hardware for GEN1 EPS |
| **comma 3X** (or Springer A1) | [comma.ai/shop](https://comma.ai/shop/products/three) | The openpilot computer |
| **Harness box / relay** | [comma.ai/shop/harness-box](https://comma.ai/shop/harness-box) | Required for openpilot relay |
| **Mazda car harness** | [comma.ai/shop](https://comma.ai/shop/products/mazda-connector) | GEN1 Mazda connector |
| **Comma power v3 + OBD-C cable + mount** | [comma.ai/shop](https://comma.ai/shop) | Standard accessories |

---

## Section 2 — TI2: Torque Interceptor 2 (GEN2 and GEN3 Vehicles)

### Supported GEN2 and GEN3 Platforms

| Platform | Vehicle | Long |
|----------|---------|------|
| `MAZDA_3_2019` | Mazda 3 2019+ | Alpha long available |
| `MAZDA_CX_30` | Mazda CX-30 2020-25 | Alpha long available |
| `MAZDA_CX_50` | Mazda CX-50 2022-25 | Alpha long available |
| `MAZDA_3_2023` | Mazda 3 2023+ | Lateral only (long disabled) |
| `MAZDA_CX_30_2023` | Mazda CX-30 2023+ | Lateral only (long disabled) |

### Overview

The Torque Interceptor 2 (TI2) sits transparently on CAN bus 1 between the front-sensing camera and the Mazda GEN2/GEN3 EPS module. Mechanically and electrically it is a passive relay: it forwards `EPS_LKAS (0x249)` and `EPS_FEEDBACK (0x24B)` frames between camera and EPS while exposing those same addresses to a panda on the comma device. To the openpilot stack the TI2 is invisible at the protocol layer — the code reads/writes the native GEN2 EPS protocol (`EPS_LKAS 0x249` on bus 1, `EPS_FEEDBACK 0x24B` on bus 1) without any TI-specific flags or code paths.

This is intentional and is the reason `MAZDA_3_2019` is configured with `flags=MazdaFlags.GEN2` only (no `TORQUE_INTERCEPTOR` flag). See `docs/migration/DECISIONS.md` (D-005, D-010) for the full rationale.

### Why TI2 Is Required

The Mazda GEN2 EPS module ignores LKAS torque commands from any source it doesn't recognise as the factory front camera. Without TI2, you cannot inject steering commands at all — the stock EPS will reject any frame the panda sends. TI2 provides the missing torque-injection path by acting as a trusted intermediate on the EPS torque-sensor bus.

The TI2 contains four independent ASIL-B+ microcontrollers wired to the four torque-sensor channels of the JTEKT column EPS. The MCUs operate as two redundant pairs and do not communicate with each other to control steering. The worst-case failure mode is **sudden loss of power steering**, not a runaway steering input — but this can still cause an accident if you are not ready to take over manually.

### CAN Bus / Protocol Reference (GEN2+TI2)

| Bus | CAN ID | Message | Direction | Purpose |
|-----|--------|---------|-----------|---------|
| 0 | 0x240 | `STEER_TORQUE` | EPS | Driver torque sensor (hands-on detection) |
| 1 | 0x249 | `EPS_LKAS` | openpilot | LKAS torque command (50 Hz target) |
| 1 | 0x24A | `TI_FEEDBACK` | TI2 | TI2 state, torque sensor mirror, fault bits |
| 1 | 0x24B | `EPS_FEEDBACK` | EPS | Steering angle, EPS torque measurement |
| 2 | 0x220 | `ACC` | camera (MITM) | ACC command. Panda blocks stock; carcontroller echoes with HOLD/RESUME overrides. |

Key constants (all from `opendbc/car/mazda/values.py`):

| Constant | Value | Notes |
|----------|-------|-------|
| `MazdaFlags.GEN2` | `2` | Set on GEN2 PlatformConfigs |
| `MazdaFlags.TORQUE_INTERCEPTOR` | `8` | **NOT set** for GEN2 — TI2 is transparent at protocol layer |
| `steerActuatorDelay` | `0.335 s` | GEN2 EPS round-trip |
| `steerLimitTimer` | `0.8 s` | Steering hold-time on disengage |
| `STEER_MAX` (GEN2) | `8000` | Maximum LKAS torque magnitude |
| `NON_LINEAR_TORQUE_PARAMS` | `(4.6, 0.6, 0.134, 0.3605)` | MAZDA_3_2019 lateral plant params |
| `hold_delay / hold_timer / resume_timer` | `0.5 s / 6.0 s / 0.5 s` | Standstill ACC echo timing |

### BOM (GEN2/GEN3 + TI2)

| Item | Vendor | Notes |
|------|--------|-------|
| **MoreTorque Torque Interceptor 2 (TI2)** | [torqueinterceptor.com](https://torqueinterceptor.com/en-us/products/torque-interceptor-2) | ~$439 USD. Includes BCM intercept harness. |
| **BCM Intercept Harness** | [torqueinterceptor.com](https://torqueinterceptor.com/en-us/products/mazda-bcm-intercept-harness-for-openpilot) | ~$147 USD if purchased separately. Bundled with TI2. |
| **comma 3X** (or Springer A1) | [comma.ai/shop](https://comma.ai/shop/products/three) / [springerelectronics.com](https://springerelectronics.com/shop/springer-a1/) | The openpilot computer. |
| **Harness box / relay** | [comma.ai/shop/harness-box](https://comma.ai/shop/harness-box), [RetroPilot](https://shop.retropilot.org/product/oshw-relay/), or compatible | Required to enable openpilot relay. |
| **Mazda car harness** | [comma.ai/shop](https://comma.ai/shop/products/mazda-connector) | Same connector used by upstream Mazda CX-5 2022 / CX-9 2021. |
| **Comma power v3 + OBD-C cable + mount** | [comma.ai/shop](https://comma.ai/shop) | Standard accessories. |

MoreTorque also sells an **All-in-One bundle** (~$1,317 pre-order) that includes the TI2, Springer A1 device, harness box, harness, OBD power, RJ-45 cable, and USB-C cable.

### Install Reference

This document does not duplicate the vendor's install instructions because they evolve and the vendor's documentation is the authoritative source. Follow the official guides in this order:

1. **TI2 install steps** —
   [MoreTorque TI2 installation guide](https://moretorques-organization.gitbook.io/ti2-installation/)
   (covers disconnect battery, BCM intercept harness, EPS connector swap, RJ-45 to comma device).
2. **Mazda wiring reference** —
   [commaai/openpilot wiki — Mazda](https://github.com/commaai/openpilot/wiki/Mazda)
   (harness routing photos and connector locations for 2019-2023 Mazda 3 / CX-30 / CX-50).
3. **comma 3X mount + power** —
   [community.sunnypilot.ai — Getting started](https://community.sunnypilot.ai/t/getting-started-using-sunnypilot-in-your-supported-car/251).
4. **Vendor support channel** —
   [MoreTorque Discord](https://discord.gg/K4kfUqAMsB) for TI2 install questions and error-code triage (green/blue LED flash patterns).

After physical install but before flashing this branch, **always do the post-install key-cycle test described in the MoreTorque guide** — the TI2 must boot to its run state without throwing error flashes before you connect a comma device.

### Verify (GEN2+TI2)

The migration docs ship a complete pre-drive verification harness. Run these **before** the first drive, in this order:

#### 1. Static check on the device

```bash
bash docs/migration/T17_T18_device_verification.sh
```

Expected: all five phases (PREREQ, B static, C import + checksum trace, D pytest, E scons) exit 0. Phase D should report **281 passed, 45 skipped, 0 failed** for the Mazda safety tests.

#### 2. Boot + fingerprint

Power on the car. The UI must show the correct platform name within ~10 seconds of boot. If it shows "Car Unrecognized" your ECU firmware version is not in `fingerprints.py` — run `python3 tools/car_porting/auto_fingerprint.py` on the device and extend the platform's `FW_VERSIONS` dict.

#### 3. Pre-engage CAN observation (5 min, in Park, engine running)

Sit in Park with the engine running. Do **not** engage openpilot yet. Open cabana (or check via connect.comma.ai) and verify:

- `TI_FEEDBACK.STATE` (0x24A bus 1) reaches `3` (RUN) within 30 seconds
- `EPS_LKAS` (0x249 bus 1) is present at ~50 Hz
- `EPS_FEEDBACK` (0x24B bus 1) is present and steering angle updates as you turn the wheel by hand
- `ACC` frames (0x220 bus 2) are present from the camera

If `TI_FEEDBACK.STATE` does not reach RUN, the TI2 has not initialised — power-cycle the car and check TI2 LED flash codes against the MoreTorque documentation. **Do not engage openpilot until STATE = RUN.**

#### 4. CP-A / CP-B / CP-C drives

The full bring-up protocol lives in `docs/migration/T21_onvehicle_bringup_checklist.md`. The three checkpoints, in order:

| Checkpoint | What it tests | Speed cap | Environment |
|------------|---------------|-----------|-------------|
| **CP-A** | Lateral engages, TI2 STATE stays RUN, no EPS fault | 30 km/h | Empty parking lot |
| **CP-B** | Lateral with TI2 active, lane centering at 30/50/80 km/h, curve handling | 80 km/h | Quiet straight road |
| **CP-C** | Longitudinal ACC echo + lateral, hold/resume, gap stability | 60-100 km/h | Quiet 4-lane highway |

After each drive, run `docs/migration/T21_cabana_capture.sh` to pull the route and check for `steerFaultPermanent`, missing `lat_active` frames, or bad accel frames.

### Feature Status (GEN2+TI2)

| Feature | Status |
|---------|--------|
| Lateral control via TI2 | **Code complete, unvalidated on v0.11 World Model** |
| Standstill ACC hold/resume | **Active** when alpha-long is OFF (stock ACC pass-through with MITM hold/resume) |
| `alphaLongitudinalAvailable` | **True** for GEN2 platforms (MAZDA_3_2019, CX_30, CX_50). Toggle exposed in non-release branches. |
| `openpilotLongitudinalControl` | **Off by default; on when user enables alpha-long.** When on, carcontroller writes `ACCEL_CMD = clip(accel*200 + 2000, 1300, 2400)` into `MAZDA_2019_ACC` frame on bus 2. |
| `alphaLongitudinalAvailable` (GEN3) | **False** — GEN3 long disabled per D-015 |
| `steerFaultPermanent` for GEN2 | **Not wired** — always returns `False`. **You are the fault detector.** |
| TI2 fault handling | INIT(1)/STANDBY(2) auto-recover; only ERROR(4)/CRITICAL_ERROR(5) latch (D-010) |

---

## Safety Disclaimer

openpilot is alpha software. This branch runs openpilot on car configurations that are **not officially supported by comma.ai**. The [comma.ai blog post on safer control of steering][comma-safety] explicitly advises against torque interceptors. **Use this software at your own risk.**

[comma-safety]: https://blog.comma.ai/safer-control-of-steering/

Specific risks for this branch:

1. **TI hardware acts directly on the EPS torque-sensor signal.** A TI fault mid-drive can cause the EPS module to see an unexpected torque reading. In the worst case this is a momentary steering anomaly before the EPS falls back to stock behavior. Practice the takeover: grab the wheel firmly and steer manually.

2. **`steerFaultPermanent` is not wired for GEN2.** openpilot will **not** self-disengage on an EPS fault. The EPS warning light on the dash is your only fault indicator. If it lights up, take over and pull over.

3. **ACC without BlendedACC may engage/disengage more abruptly than stock MRCC.** The GEN2 ACC path sends commands directly to 0x220 bus 2. Without the BlendedACC filter (dropped in D-003), transitions may feel sharper. This is expected.

4. **Lateral tuning is from a previous World Model.** `NON_LINEAR_TORQUE_PARAMS = (4.6, 0.6, 0.134, 0.3605)` was tuned before v0.11. At v0.11 the lateral feel may differ. Start slow and capture cabana logs.

5. **First drive: empty space, speed under 30 km/h only. No exceptions.**

6. By using this software you accept all responsibility for anything that might occur while you use it. All contributors to this fork are not liable. Use at your own risk. Fork contributors assume no liability for your use of this software or any hardware (including TI1/TI2). MoreTorque Torque Interceptor is not associated with comma.ai or sunnypilot.

---

## Further Reading

- **Architecture decisions** — `docs/migration/DECISIONS.md` (D-002 through D-015)
- **Migration guide** — `docs/migration/MIGRATION_GUIDE.md`
- **Bring-up checklist** — `docs/migration/T21_onvehicle_bringup_checklist.md`
- **Roadmap & known limitations** — `docs/migration/ROADMAP.md`
- **Port status quick reference** — `docs/migration/PORT_STATUS.md`
- **MoreTorque TI docs** — [moretorques-organization.gitbook.io](https://moretorques-organization.gitbook.io/openpilot-mazda-community-support)
- **MoreTorque TI2 risks page** — [moretorques-organization.gitbook.io/torque-interceptor-2/risks](https://moretorques-organization.gitbook.io/torque-interceptor-2/risks)
- **MoreTorque Discord** — [discord.gg/K4kfUqAMsB](https://discord.gg/K4kfUqAMsB)
- **commaai/openpilot wiki — Mazda** — [github.com/commaai/openpilot/wiki/Mazda](https://github.com/commaai/openpilot/wiki/Mazda)
- **sunnypilot community forum — Mazda** — [community.sunnypilot.ai/c/vehicle-talk/mazda](https://community.sunnypilot.ai/c/vehicle-talk/mazda/)
