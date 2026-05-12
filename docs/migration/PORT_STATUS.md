# Mazda Multi-Platform Community Port — Current Status & Quick Reference

**Quick reference for contributors and self-installers.**

> **For hardware install and pre-drive verification, see [`docs/HARDWARE_TI.md`](../HARDWARE_TI.md) first.**

---

## What This Project Is

This is a community port of 15 Mazda platforms from the MoreTore/openpilot `mazda-frogpilot` fork (itself based on openpilot v0.9.7) onto the current commaai/openpilot v0.11+ master architecture. The work spans three repos: `sunnypilot` (parent, branch `mazda-multi-platform-community`), `opendbc_repo` (submodule, branch `mazda-multi-platform-additions`), and `panda` (submodule, branch `mazda-multi-platform-additions`). The original single-platform port (`MAZDA_3_2019` GEN2+TI2) is preserved unchanged; this branch extends it to cover all 15 platforms. See `DECISIONS.md` D-012 for the scope expansion rationale.

---

## Platform Status Grid

| Platform | Generation | Lateral | Longitudinal | Alpha Long | Hardware Add-on | Notes |
|----------|-----------|---------|-------------|-----------|----------------|-------|
| `MAZDA_CX5` | GEN1 | Yes | Stock ACC | No | None | Upstream as-is |
| `MAZDA_CX9` | GEN1 | Yes | Stock ACC | No | None | Upstream as-is |
| `MAZDA_3` | GEN1 | Yes | Stock ACC | No | None | Upstream as-is |
| `MAZDA_6` | GEN1 | Yes | Stock ACC | No | None | Upstream as-is |
| `MAZDA_CX9_2021` | GEN1 | Yes | Stock ACC | No | None | Upstream as-is |
| `MAZDA_CX5_2022` | GEN1 | Yes | Stock ACC | No | None | Upstream as-is |
| `MAZDA_3_2019` | GEN2 | Yes | OP long (MITM) | Yes | TI2 required | Original port; alpha long available |
| `MAZDA_CX5_TI` | GEN1+TI | Yes | Stock ACC | No | TI1 required | Manual platform selection required |
| `MAZDA_CX9_TI` | GEN1+TI | Yes | Stock ACC | No | TI1 required | Manual platform selection required |
| `MAZDA_3_TI` | GEN1+TI | Yes | Stock ACC | No | TI1 required | Manual platform selection required |
| `MAZDA_6_TI` | GEN1+TI | Yes | Stock ACC | No | TI1 required | Manual platform selection required |
| `MAZDA_CX_30` | GEN2 | Yes | OP long (MITM) | Yes | TI2 required | Same arch as MAZDA_3_2019 |
| `MAZDA_CX_50` | GEN2 | Yes | OP long (MITM) | Yes | TI2 required | Same arch as MAZDA_3_2019 |
| `MAZDA_3_2023` | GEN3 | Yes | Stock ACC only | No | TI2 required | Long disabled per D-015 |
| `MAZDA_CX_30_2023` | GEN3 | Yes | Stock ACC only | No | TI2 required | Long disabled per D-015 |

**GEN1+TI note:** GEN1 and GEN1+TI variants share identical ECU firmware. The TI hardware add-on has no FW signature. You **must** manually select the correct `*_TI` variant from the comma device car-selection menu. Selecting the wrong variant produces the wrong safety mode with no auto-detection safety net. See `docs/HARDWARE_TI.md` for the full WARNING.

**GEN3 note:** Longitudinal control is disabled for GEN3 platforms. Stock MRCC pass-through only. Lateral via TI2 is the primary value add.

---

## Current State at a Glance

| Item | Value |
|------|-------|
| Parent branch | `mazda-multi-platform-community` in `sunnypilot` |
| Submodule branches | `mazda-multi-platform-additions` in `opendbc_repo` and `panda` |
| GEN1 platforms | 6 existing upstream + 4 new GEN1+TI variants |
| GEN2 platforms | `MAZDA_3_2019` (original) + `MAZDA_CX_30` + `MAZDA_CX_50` |
| GEN3 platforms | `MAZDA_3_2023` + `MAZDA_CX_30_2023` |
| Safety pytest | 281 passed / 0 failed / 45 skipped (post-T3.5) |
| On-vehicle | CP-A pending (not yet driven) |

---

## 5-Second Project Map

```
<project-root>        <- parent; work here on mazda-multi-platform-community branch
  opendbc_repo/                                       <- submodule; work on mazda-multi-platform-additions
    opendbc/car/mazda/                                <- Python: values, interface, carstate,
                                                         carcontroller, mazdacan, fingerprints
    opendbc/safety/modes/mazda.h                      <- C: GEN1 + GEN1+TI + GEN2 + GEN3 safety hooks
    opendbc/safety/tests/test_mazda.py                <- pytest (281/0/45)
    opendbc/safety/tests/common.py                    <- Mazda-vs-Mazda TX overlap skip rule
    opendbc/can/dbc.py                                <- mazda2019_checksum registration
    opendbc/dbc/mazda_2017.dbc                        <- GEN1 DBC + CAM_LKAS2 + TI_FEEDBACK (806 lines)
    opendbc/dbc/mazda_2019.dbc                        <- GEN2 DBC (642 lines)
    opendbc/dbc/mazda_2023.dbc                        <- GEN3 DBC (660 lines)
  panda/                                              <- submodule; work on mazda-multi-platform-additions
    board/drivers/can_common.h                        <- Mazda GEN2 ignition (0x274)
    board/main.c                                      <- SAFETY_MAZDA case
    python/__init__.py                                <- FLAG_MAZDA_GEN2 / _TORQUE_INTERCEPTOR / _GEN3

<source-fork-root>          <- REFERENCE ONLY: source fork (do not edit)
```

---

## Documentation Map

| Question | Read |
|----------|------|
| Starting fresh? | This file + `docs/migration/MIGRATION_GUIDE.md` |
| About to drive? | `docs/migration/T21_onvehicle_bringup_checklist.md` |
| Why this design? | `docs/migration/DECISIONS.md` |
| What's next? | `docs/migration/ROADMAP.md` |
| Pulling in upstream v0.12+? | `docs/migration/REBASE_PLAYBOOK.md` |
| Investigating an on-vehicle bug? | `docs/migration/T21_onvehicle_bringup_checklist.md (post-drive sections)` + `docs/migration/T21_cabana_capture.sh` |
| Verifying after a code change? | `docs/migration/T17_T18_device_verification.sh` (Linux/dev box only, not macOS) |
| Full SHA chain + arch deltas? | `docs/migration/MIGRATION_GUIDE.md` section "Complete Commit Chain" |
| TI hardware install? | `docs/HARDWARE_TI.md` |

---

## Hard Rules

**Scope.** This port covers all 15 platforms listed in the Platform Status Grid above. See `DECISIONS.md` D-012 for the scope expansion from the original single-platform port. Radar Interceptor and manual transmission remain out of scope per D-002/D-012.

**No FrogPilot infrastructure.** Never re-introduce `Params()` reads, `frogpilot_toggles`, `fp_ret` tuple returns, `FrogPilotCarState`, or `BlendedACC` in `selfdrive/controls/lib/longcontrol.py`. If GEN2 ACC misbehaves, blend inside `carcontroller.py` only. See D-003, D-004.

**The only legitimate FrogPilot mentions** in code are the 2 provenance comments at `opendbc/car/mazda/values.py:49,156` (algorithm origin attribution). Anything else is a blocker.

**Before any commit:**
- `python3 -m py_compile` on all changed `.py` files
- `pytest opendbc/safety/tests/test_mazda.py` on Linux/dev box (macOS native build broken)

**Commit style:** `<area>: <lowercase imperative>` — e.g., `mazda: ...`, `submodule: bump ...`, `safety/tests: ...`. Match the existing log.

**Never amend pushed commits.** Never force-push without user approval.

**When unsure about architecture:** read `DECISIONS.md` before making changes.

---

## Quick Commands

```bash
# Verify all 3 repos at expected SHA
for d in . opendbc_repo panda; do echo "$d:"; git -C $d log -1 --oneline; done

# Run safety tests (uv-managed venv with pytest, run from opendbc_repo)
cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py \
  --confcutdir=. --rootdir=. -p no:cacheprovider -o addopts=
# Expected: 281 passed, 45 skipped, 0 failed

# Static check on Mazda Python files
python3 -m py_compile \
  opendbc_repo/opendbc/car/mazda/values.py \
  opendbc_repo/opendbc/car/mazda/interface.py \
  opendbc_repo/opendbc/car/mazda/carstate.py \
  opendbc_repo/opendbc/car/mazda/carcontroller.py \
  opendbc_repo/opendbc/car/mazda/mazdacan.py \
  opendbc_repo/opendbc/car/mazda/fingerprints.py \
  opendbc_repo/opendbc/can/dbc.py
# Must exit 0 with no output

# Forbidden-token scrub (must return 0 hits except 2 known benign at values.py:49,156)
grep -nrE 'frogpilot_toggles|FrogPilot|fp_ret|FPCP|BlendedACC' \
  opendbc_repo/opendbc/car/mazda/

# Check for stale HARDWARE_TI2 references (must return 0 hits)
grep -r 'HARDWARE_TI2' docs/ README.md 2>/dev/null
```

---

## First-Time Bootstrap Checklist

- [ ] Read this document
- [ ] `cat docs/migration/MIGRATION_GUIDE.md` — full SHA chain + arch deltas
- [ ] `cat docs/migration/DECISIONS.md` — what's settled and why
- [ ] `cat docs/migration/ROADMAP.md` — what's pending
- [ ] `git log --oneline mazda-multi-platform-community -20` — recent activity
- [ ] Then ask the user: "what would you like to work on?"

---

## Key Technical Facts (Quick Reference)

| Item | Value |
|------|-------|
| GEN2 platform (original) | `MAZDA_3_2019` in `opendbc/car/mazda/values.py` |
| GEN2 flags | `FLAG_MAZDA_GEN2 = 2`, `FLAG_MAZDA_TORQUE_INTERCEPTOR = 8` |
| GEN2 combined flags | `0xa` (GEN2 + TI both set) |
| GEN1+TI flags | `FLAG_MAZDA_TORQUE_INTERCEPTOR = 8` (no GEN2 flag) |
| GEN3 flags | `FLAG_MAZDA_GEN3 = 4` |
| GEN2 steer limits | `STEER_MAX=8000`, `steerActuatorDelay=0.335s`, `steerLimitTimer=0.8s` |
| TI steer limits | `TI_STEER_MAX=600`, `TI_STEER_DELTA_UP=6`, `TI_STEER_DELTA_DOWN=15` |
| Lateral model (GEN2) | `NON_LINEAR_TORQUE_PARAMS = (4.6, 0.6, 0.134, 0.3605)` for MAZDA_3_2019 |
| GEN2 ACC bus | 0x220 bus 2 (MITM: panda blocks stock, we echo + modify HOLD/RESUME) |
| GEN2 EPS/TI bus | 0x249 bus 1 |
| TI feedback | 0x24A bus 1 |
| TI state machine | `TI_STATE` IntEnum: DISCOVER=0, OFF=1, DRIVER_OVER=2, RUN=3 |
| Hold/resume timers | 50/600/50 frames (0.5s/6.0s/0.5s at 100Hz) |
| GEN2 alpha-long | `True` for MAZDA_3_2019, MAZDA_CX_30, MAZDA_CX_50 |
| GEN3 alpha-long | `False` — long disabled per D-015 |
| GEN1+TI alpha-long | `False` — long not supported |
| Checksum | `mazda2019_checksum` in `mazdacan.py`; registered in `opendbc/can/dbc.py` |
| Safety pytest | 281 passed, 45 skipped (upstream-intentional), 0 failed |

---

*PORT_STATUS.md — mazda-multi-platform-community. Parent HEAD: see `git rev-parse HEAD`.*
