# Mazda 3 2019+ GEN2 + TI2 Port to Sunnypilot — Master Plan

**Source of truth:** MoreTore/openpilot `mazda-frogpilot` branch (FrogPilot fork, v0.9.7 era).
**Reference port (unverified):** `/Users/cyonsun/Documents/Code/openpilot-comma` `mazda-port` branch (port to commaai/openpilot v0.11+; tag `v0.11.1-mazda3-2019.0.2`; LOCAL_PASS 79/0/15).
**Target:** `/Users/cyonsun/Documents/Code/sunnypilot` (branch `mazda-port` to be created off `master`), with submodule branches `mazda-port-additions` in `panda` (sunnyhaibin/panda) and `opendbc_repo` (sunnypilot/opendbc).
**Target platform:** `MAZDA_3_2019` (GEN2 hardware + Torque Interceptor 2). GEN1 untouched.

---

## Architectural Reality (Critical)

Three-repo port: **parent (sunnypilot)** + **opendbc_repo** (sunnypilot/opendbc) + **panda** (sunnyhaibin/panda).

Sunnypilot pervasively differs from comma openpilot:

| Sunnypilot pattern | Affects |
|---|---|
| `CarController.__init__(self, dbc_names, CP, CP_SP)` | All carcontroller signatures |
| `CarController.update(self, CC, CC_SP, CS, now_nanos)` | All update() callsites |
| `CarState.__init__(self, CP, CP_SP)` | All carstate signatures |
| `CarState.update() -> tuple[structs.CarState, structs.CarStateSP]` | Returns tuple, not single struct |
| `CarState.get_can_parsers(CP, CP_SP)` | Bus parser construction |
| `CarInterface._get_params_sp(stock_cp, ret, ...)` | sunnypilot-only static hook |
| `PlatformConfigBase.sp_flags: int = 0` | Additive field, no collision |
| Mazda CarController inherits `IntelligentCruiseButtonManagementInterface` (ICBM) | `opendbc/sunnypilot/car/mazda/icbm.py` |
| Mazda `_get_params_sp` sets `intelligentCruiseButtonManagementAvailable = True` | Must preserve |
| `create_button_cmd` forwards SET_PLUS/SET_MINUS via `inc`/`dec` | Differs from comma which hardcodes 0 |
| MADS is generic; no Mazda-specific MADS code | No new MADS work needed |

Cherry-picking conversun's 13 opendbc Python commits is NOT viable; every commit conflicts. Must do manual adapted port for Python files.

Cherry-pick IS viable for: panda (2 commits clean), `opendbc/safety/modes/mazda.h` (near-verbatim), DBC files, `opendbc/can/dbc.py` checksum registration.

---

## Wave 0: Workspace Setup

**Goal:** Branches and submodule remotes ready.

| Task | Action | Verification |
|---|---|---|
| W0.1 | In `sunnypilot`: `git checkout -b mazda-port` from current `master` | `git branch --show-current` == `mazda-port` |
| W0.2 | In `sunnypilot/panda`: `git remote add conversun git@github.com:conversun/panda.git && git fetch conversun` | `git branch -r \| grep conversun/mazda-port-additions` exists |
| W0.3 | In `sunnypilot/panda`: `git checkout -b mazda-port-additions` from current HEAD (sunnyhaibin/panda master) | clean tree |
| W0.4 | In `sunnypilot/opendbc_repo`: `git remote add conversun git@github.com:conversun/opendbc.git && git fetch conversun` | `git branch -r \| grep conversun/mazda-port-additions` exists |
| W0.5 | In `sunnypilot/opendbc_repo`: `git checkout -b mazda-port-additions` from current HEAD (sunnypilot/opendbc master) | clean tree |

**Commit:** none yet.

---

## Wave 1: Panda — Mazda GEN2 Flag Constants + Ignition Hook

**Goal:** Port the 2 conversun panda commits to sunnyhaibin/panda's `mazda-port-additions` branch.

Source commits (in `openpilot-comma/panda`):
- `066ca435` — mazda: add GEN2 + TI flag constants and ignition addr
- `251bdf57` — mazda: declare len inside bus==1 ignition hook block (hotfix)

| Task | File | Action |
|---|---|---|
| W1.1 | `panda/python/__init__.py` | Add `FLAG_MAZDA_GEN2 = 2`, `FLAG_MAZDA_TORQUE_INTERCEPTOR = 8` constants. Insertion point: between `SUPPORTED_DEVICES` and `INTERNAL_DEVICES` (~line 145). |
| W1.2 | `panda/board/drivers/can_common.h` | Inside `ignition_can_hook()`: in existing `bus == 0U` block, add 0x274 GEN2 path. Add new `bus == 1U` block with `int len = GET_LEN(msg);` declaration inside, then 0x274 hook (combined patch already includes hotfix). |
| W1.3 | `panda/board/main.c` | In `set_safety_mode()` switch: add `case SAFETY_MAZDA:` between `case SAFETY_ELM327:` and `default:`, calling `set_safety_mazda(param)` semantics per conversun source. |
| W1.4 | Verification | `git -C panda log --oneline -3` shows the 2 commits; `python3 -c "from panda import Panda; print(hex(Panda.FLAG_MAZDA_GEN2 \| Panda.FLAG_MAZDA_TORQUE_INTERCEPTOR))"` outputs `0xa`. |

**Approach:** Cherry-pick `git cherry-pick 066ca435 251bdf57` from conversun. If conflicts (unlikely per exploration), resolve preferring conversun additions.

**Commit style:** Use original conversun commit messages.

---

## Wave 2: opendbc — DBC + Safety C + Checksum Registration

**Goal:** Add Mazda 2019 DBC, GEN2+TI safety hooks, checksum registration. These can be near-verbatim from conversun (no sunnypilot-specific divergence).

| Task | File | Action |
|---|---|---|
| W2.1 | `opendbc_repo/opendbc/dbc/mazda_2019.dbc` | Copy from `openpilot-comma/opendbc_repo/opendbc/dbc/mazda_2019.dbc` (642 lines). Note `mazda_3_2019.dbc` already exists in sunnypilot but the GEN2 platform's `init()` references `mazda_2019` filename. |
| W2.2 | `opendbc_repo/opendbc/safety/modes/mazda.h` | Replace sunnypilot's GEN1-only 106-line file with conversun's full 226-line GEN2+TI version. Validates: `MAZDA_2019_TX_MSGS[]`, `mazda_2019_rx_checks[]`, `mazda_gen2_safety_hooks`, `mazda_gen2_ti_safety_hooks`, `FLAG_MAZDA_GEN2`/`FLAG_MAZDA_TORQUE_INTERCEPTOR` parsing in `mazda_init`, `mazda_fwd_hook`. |
| W2.3 | `opendbc_repo/opendbc/can/dbc.py` | Add `from opendbc.car.mazda.mazdacan import mazda2019_checksum` import; add `MAZDA2019_CHECKSUM` to `SignalType` enum; register `mazda_2019` and `mazda_2023` DBC families in `get_checksum_state`. |
| W2.4 | `opendbc_repo/opendbc/safety/tests/common.py` | Add Mazda GEN2 sibling skip rule (T18b): `if attr.startswith('TestMazdaGen2') and current_test.startswith('TestMazdaGen2'): continue` inside `test_tx_hook_on_wrong_safety_mode` skip block. |
| W2.5 | Verification | (deferred — depends on Wave 3 Python files; W2 commits stand alone but tests need Python in place) |

**Commits:**
- `mazda: import mazda_2019.dbc for GEN2 + TI support`
- `mazda: add GEN2 + TI safety variants`
- `opendbc/can: add mazda_2019 checksum support` (after Wave 3 mazdacan.py exists; may need reordering)
- `safety/tests: skip wrong-safety-mode TX cross-tests for Mazda GEN2 sibling variants`

**Note:** W2.3 depends on `mazdacan.mazda2019_checksum` existing; commit ordering must place mazdacan.py change (in W3) BEFORE W2.3. Adjust commit graph.

---

## Wave 3: opendbc — Mazda Python Adapted Port (HIGH-RISK, manual work)

**Goal:** Port FrogPilot Mazda GEN2+TI logic into sunnypilot's CP_SP/CC_SP/tuple-return convention. **This is the bulk of the work.**

Source files (conversun openpilot-comma):
- `opendbc/car/mazda/values.py` (175 lines, full GEN2+TI)
- `opendbc/car/mazda/interface.py` (114 lines, full GEN2+TI _get_params)
- `opendbc/car/mazda/carstate.py` (292 lines, GEN1+GEN2 dispatch with TI state machine)
- `opendbc/car/mazda/carcontroller.py` (158 lines, full GEN2 lateral/longitudinal/TI)
- `opendbc/car/mazda/mazdacan.py` (172 lines, includes mazda2019_checksum + GEN2 builders)
- `opendbc/car/mazda/fingerprints.py` (323 lines, includes MAZDA_3_2019 entry)

Target adaptation rules:
1. **Preserve sunnypilot's signatures** — every method gets `CP_SP`/`CC_SP` params and tuple returns where applicable.
2. **Preserve ICBM inheritance** — `CarController(CarControllerBase, IntelligentCruiseButtonManagementInterface)`.
3. **Preserve `_get_params_sp`** — keep existing implementation (sets ICBM available).
4. **Preserve `create_button_cmd` GEN1 SET_PLUS/SET_MINUS forwarding semantics** — that's a sunnypilot behavior, not a regression.
5. **Add MAZDA_3_2019 to `dashcamOnly` exclusion tuple** in `interface.py`.
6. **No FrogPilot infrastructure** — strict prohibition: no `Params()`, no `frogpilot_toggles`, no `fp_ret`, no `BlendedACC`, no `FrogPilotCarState`. Only the 2 provenance comments at `values.py:49,156` allowed (per D-004 in openpilot-comma DECISIONS.md).
7. **alpha_long disabled** — per D-007 (`alphaLongitudinalAvailable = False` until ACCEL_CMD plumbing ported).
8. **TI fault transient/permanent split** — per D-010 (only ERROR=4/CRITICAL_ERROR=5 latch; INIT/STANDBY/OFF auto-recover).

| Task | File | Action |
|---|---|---|
| W3.1 | `opendbc_repo/opendbc/car/mazda/values.py` | Add to existing GEN1-only file: (a) `MazdaFlags.GEN2 = 2`, `MazdaFlags.TORQUE_INTERCEPTOR = 8`; (b) `TI_STATE` IntEnum (DISCOVER=0, OFF=1, DRIVER_OVER=2, RUN=3) with provenance comment; (c) `apply_ti_steer_torque_limits` function with provenance comment; (d) extend `CarControllerParams.__init__` from `pass` to GEN2 overrides (STEER_MAX=8000, rate limits, driver allowance) + TI_STEER constants; (e) extend `LKAS_LIMITS` with TI thresholds; (f) add `Buttons.TURN_ON = 5`; (g) add `MAZDA_3_2019 = MazdaPlatformConfig(...)` with `MazdaCarSpecs(mass=3000*CV.LB_TO_KG, wheelbase=2.725, steerRatio=18.8)`, `flags=MazdaFlags.GEN2 \| MazdaFlags.TORQUE_INTERCEPTOR`; (h) add `MazdaPlatformConfig.init()` that sets `dbc_dict={Bus.pt: 'mazda_2019', Bus.cam: 'mazda_2019', Bus.body: 'mazda_2019'}` when GEN2. Imports: `numpy as np`, `IntEnum`. |
| W3.2 | `opendbc_repo/opendbc/car/mazda/mazdacan.py` | Add `mazda2019_checksum` function (from conversun lines 4-17). Add `create_steering_control_gen2` (EPS_LKAS bus 1). Add `create_acc_cmd` (ACC bus 2, MITM HOLD/RESUME). PRESERVE existing `create_button_cmd` SET_PLUS/SET_MINUS forwarding (do NOT replace with conversun's hardcoded zeros). |
| W3.3 | `opendbc_repo/opendbc/car/mazda/interface.py` | Add `MAZDA_3_2019` to `dashcamOnly` exclusion tuple. Add GEN2 branch in `_get_params`: `safetyParam |= FLAG_MAZDA_GEN2` (and `\| FLAG_MAZDA_TORQUE_INTERCEPTOR` if TI flag set), `steerActuatorDelay=0.335`, `steerLimitTimer=0.8`, `vEgoStarting=0.2`, `stopAccel=-0.5`, `longitudinalActuatorDelay=0.35`, `startingState=True`, longitudinal tuning kpV/kiV, `alphaLongitudinalAvailable=False` (D-007). Add non-linear torque callbacks (sigmoid+linear, params from openpilot-comma values.py NON_LINEAR_TORQUE_PARAMS = (4.6, 0.6, 0.134, 0.3605)). Add `lateralTuning.torque.useSteeringAngle=True` etc. PRESERVE `_get_params_sp` exactly (do not modify ICBM-available logic). |
| W3.4 | `opendbc_repo/opendbc/car/mazda/carstate.py` | Refactor `update()` to dispatch on `MazdaFlags.GEN2`: GEN1 path stays (returns existing tuple); add `_update_gen2` returning the same tuple `(structs.CarState, structs.CarStateSP)` — adapt conversun's GEN2 update logic. Add instance attrs: `self.ti_state`, `self.ti_fault_permanent`, `self.acc_values`, `self._prev_steering_angle` initialized in `__init__(CP, CP_SP)`. Add TI state machine with D-010 transient/permanent split. Add ACC frame snapshot for MITM. Modify `get_can_parsers(CP, CP_SP)` GEN2 branch to include Bus.pt, Bus.cam, Bus.body parsers with appropriate freqs. |
| W3.5 | `opendbc_repo/opendbc/car/mazda/carcontroller.py` | Add GEN2 branches to `update(CC, CC_SP, CS, now_nanos)`: lateral via `create_steering_control_gen2` on bus 1 (gated by `CS.ti_state == TI_STATE.RUN and not ti_ramp_down`); longitudinal via `create_acc_cmd` on bus 2 with hold/resume timer state machine (HOLD_DELAY_FRAMES=50, HOLD_DURATION_FRAMES=600, RESUME_DURATION_FRAMES=50). PRESERVE ICBM `update` call and inheritance (currently called for GEN1 — gate ICBM behind `not GEN2` if needed, or extend ICBM for GEN2 if SET_PLUS/SET_MINUS works on GEN2). Use instance-based `CarControllerParams(CP)` for GEN2 limits while keeping class-level for GEN1. |
| W3.6 | `opendbc_repo/opendbc/car/mazda/fingerprints.py` | Add `CAR.MAZDA_3_2019` block to `FW_VERSIONS` dict — copy entry verbatim from conversun (lines 283-322 of openpilot-comma fingerprints.py). |
| W3.7 | `opendbc_repo/opendbc/car/torque_data/substitute.toml` | Add `MAZDA_3_2019 = "MAZDA_CX9_2021"` substitution (until real torque data exists). |
| W3.8 | `opendbc_repo/opendbc/sunnypilot/car/mazda/icbm.py` | Audit: does ICBM SET_PLUS/SET_MINUS work on GEN2? If GEN2 button protocol differs, gate `update()` to GEN1 only. Likely safe to leave alone for first pass. |
| W3.9 | `opendbc_repo/opendbc/safety/tests/test_mazda.py` | Add `TestMazdaGen2Safety` and `TestMazdaGen2TiSafety` test classes from conversun (mirror upstream pattern). |
| W3.10 | Verification (post-Wave) | Run all checks below. |

**Verifications (W3.10):**
```bash
# 1. py_compile all Mazda Python files
python3 -m py_compile \
  opendbc_repo/opendbc/car/mazda/{values,interface,carstate,carcontroller,mazdacan,fingerprints}.py \
  opendbc_repo/opendbc/can/dbc.py
# Must exit 0

# 2. Import smoke + checksum trace
cd opendbc_repo
PYTHONPATH=. python3 -c "
from opendbc.car.mazda.values import CAR, MazdaFlags, TI_STATE, apply_ti_steer_torque_limits
from opendbc.car.mazda.interface import CarInterface
from opendbc.car.mazda.carstate import CarState
from opendbc.car.mazda.carcontroller import CarController
from opendbc.car.mazda.mazdacan import mazda2019_checksum
p = CAR.MAZDA_3_2019
flags = p.config.flags
assert flags & MazdaFlags.GEN2 and flags & MazdaFlags.TORQUE_INTERCEPTOR, f'flags={hex(flags)}'
assert mazda2019_checksum(0x220, None, bytearray([1,2,3,4,5,6,7])) == 0x46
assert mazda2019_checksum(0x249, None, bytearray([0]*7)) == 0x53
print('OK flags=', hex(flags))
"
# Must print 'OK flags= 0xa'

# 3. Safety pytest
cd opendbc_repo
python3 -m pytest opendbc/safety/tests/test_mazda.py -v --rootdir=. --confcutdir=. -o addopts= --tb=short
# Expected: ~79 passed, ~15 skipped, 0 failed (matches openpilot-comma baseline)

# 4. Forbidden-token scrub
grep -nrE 'frogpilot_toggles|FrogPilot|fp_ret|FPCP|BlendedACC|CEStatus|ManualTransmission|TorqueInterceptorEnabled|RadarInterceptorEnabled|NoMRCC|NoFSC' \
  opendbc_repo/opendbc/car/mazda/ opendbc_repo/opendbc/safety/modes/mazda.h
# Allowed: 2 benign 'FrogPilot' provenance comments at values.py:~49 and ~156
# Disallowed: any other matches
grep -nE '(^|[^a-zA-Z_])Params\(' opendbc_repo/opendbc/car/mazda/*.py
# Must exit 1 (no matches)
```

**Commits (in opendbc_repo on `mazda-port-additions`):**
1. `mazda: import mazda_2019.dbc for GEN2 + TI support` (W2.1)
2. `mazda: add GEN2 + TI safety variants` (W2.2)
3. `mazda: add MAZDA_3_2019 platform with GEN2 + TI flags + TI helpers` (W3.1)
4. `mazda: add MAZDA_3_2019 FW fingerprint` (W3.6)
5. `mazda: extend interface.py for MAZDA_3_2019 (GEN2 + TI)` (W3.3)
6. `mazda: add GEN2 EPS_LKAS + TI + ACC CAN builders` (W3.2)
7. `opendbc/can: add mazda_2019 checksum support` (W2.3)
8. `mazda: extend carcontroller.py for MAZDA_3_2019 (GEN2 ACC + TI steering)` (W3.5)
9. `mazda: extend carstate.py for MAZDA_3_2019 (GEN2 + TI feedback)` (W3.4)
10. `safety/tests: skip wrong-safety-mode TX cross-tests for Mazda GEN2 sibling variants` (W2.4)
11. `safety/tests: add Mazda GEN2 + TI test classes` (W3.9)
12. `mazda: add MAZDA_3_2019 torque substitute entry` (W3.7)

---

## Wave 4: Parent (sunnypilot) — Submodule Bumps + Migration Docs

| Task | File | Action |
|---|---|---|
| W4.1 | `panda` submodule pointer | Update to `mazda-port-additions` HEAD after Wave 1. |
| W4.2 | `opendbc_repo` submodule pointer | Update to `mazda-port-additions` HEAD after Wave 3. |
| W4.3 | `docs/migration/` + repo root | Copy adapted migration docs from `openpilot-comma/docs/migration/` (MIGRATION_GUIDE.md, DECISIONS.md, ROADMAP.md, REBASE_PLAYBOOK.md, integration_log.md, T17_T18_device_verification.sh, T21_onvehicle_bringup_checklist.md, T21_cabana_capture.sh) into `sunnypilot/docs/migration/`. Separately copy `openpilot-comma/AGENTS.md` (located at REPO ROOT, not in docs/migration/) into `sunnypilot/docs/migration/AGENTS_mazda-port.md` (renamed to avoid collision with any sunnypilot-level AGENTS.md). Adapt path references from `openpilot-comma` → `sunnypilot`. Adapt submodule URL references from `conversun/*` → `sunnypilot/*` (opendbc) and `sunnyhaibin/*` (panda). Drop openpilot-comma's personal-preference items (Konik fleet server, zh-CHS UI default). |
| W4.4 | `docs/CARS.md` | Run `python3 selfdrive/car/docs.py` (or sunnypilot equivalent) to regenerate. Verify MAZDA_3_2019 row appears. |
| W4.5 | `opendbc_repo/opendbc/sunnypilot/car/car_list.json` | Run `python3 opendbc_repo/opendbc/sunnypilot/car/platform_list.py` to regenerate. Verify MAZDA_3_2019 entry. (Lives in opendbc_repo, so this commits to opendbc_repo `mazda-port-additions`, not parent.) |

**Commits (in sunnypilot on `mazda-port`):**
1. `submodule: bump panda for Mazda GEN2+TI flag constants and ignition addr`
2. `submodule: bump opendbc_repo for Mazda 3 2019 GEN2+TI port`
3. `Mazda: add Mazda 3 2019 GEN2 + TI2 migration docs`
4. `Mazda: regenerate docs/CARS.md with MAZDA_3_2019`

---

## Wave 5: Verification + Sign-off

| Task | Action |
|---|---|
| W5.1 | Run all py_compile / pytest / forbidden-token scrubs from Wave 3 verification block. |
| W5.2 | Run sunnypilot's CI-equivalent locally if possible (Linux required for safety pytest; macOS-only available now — log known limitation). |
| W5.3 | Verify branch convention: `git -C sunnypilot log --oneline mazda-port -10`, `git -C panda log --oneline mazda-port-additions -3`, `git -C opendbc_repo log --oneline mazda-port-additions -15`. |
| W5.4 | Tag `v2026.001.003-mazda3-2019.0.1` (or sunnypilot version-aligned tag) annotated in all 3 repos as recovery point. NO push to remote until on-vehicle CP-A clears. |
| W5.5 | Update master plan with Wave outcomes; mark which waves PASS/FAIL/PASS-WITH-NOTES. |

---

## What's OUT of Scope

| Item | Reason |
|---|---|
| GEN1 platforms (untouched) | Already in sunnypilot upstream |
| GEN3 / CX-30 / CX-50 / Radar Interceptor / Manual Transmission | Not in source fork |
| BlendedACC | Per D-003; longcontrol.py stays zero-diff |
| FrogPilot UI / MTSC / SLC / themes | Per D-004 |
| `routes.py` test entry for MAZDA_3_2019 | Deferred to post-CP-A (no cabana segment yet) |
| ACCEL_CMD plumbing (alpha-long enable) | P1 in ROADMAP; requires CP-C |
| On-vehicle validation | User's responsibility post-port |

---

## Risk Register

| Risk | Mitigation |
|---|---|
| sunnypilot `tuple` carstate return breaks GEN2 dispatch | Test with import smoke; check both `_update_gen1` and `_update_gen2` return same tuple shape |
| ICBM interaction with GEN2 button protocol unclear | Audit `icbm.py`; if uncertain, gate ICBM to GEN1 only via `CP.flags & MazdaFlags.GEN1` |
| Safety pytest expects 79 passes but sunnypilot's existing safety modifications may shift count | Document actual count vs expected; if delta is in known-safe areas (e.g., MADS sibling tests), accept |
| `mazda_2019.dbc` filename collision with existing `mazda_3_2019.dbc` | Confirm `MazdaPlatformConfig.init()` references `mazda_2019` filename (per conversun); if sunnypilot needs `mazda_3_2019`, adjust init() |
| Sunnypilot-specific `sp_flags` field needs population | Audit if any sunnypilot framework code requires non-zero sp_flags for Mazda; default `0` should be safe |
| `_get_params_sp` ICBM-available may need GEN2 gating | Verify ICBM works on GEN2 hardware before declaring it available; if uncertain, gate behind `not (CP.flags & MazdaFlags.GEN2)` |
| Build verification requires Linux (scons), only macOS available | Defer build verification; rely on py_compile + pytest + import smoke for code-completion sign-off |

---

## Execution Order Summary

1. Wave 0: workspace branches (5 minutes)
2. Wave 1: panda port (cherry-pick + verify) (~30 minutes)
3. Wave 2: opendbc DBC + safety C + checksum (~1 hour)
4. Wave 3: opendbc Python adapted port (HIGHEST EFFORT, ~4-6 hours; 6 substantial files to adapt)
5. Wave 4: sunnypilot parent submodule bumps + docs (~30 minutes)
6. Wave 5: verification + tag (~30 minutes)

**Total estimated effort:** 6-8 hours of focused work. Wave 3 is the dominant cost; can be parallelized across multiple subagents (one per file) if context allows.
