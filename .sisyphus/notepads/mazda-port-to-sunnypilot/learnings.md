# Learnings — mazda-port-to-sunnypilot

## 2026-05-09 Session Start: Initial State Assessment

### Wave 0 Status: COMPLETE
- sunnypilot is on `mazda-port` branch ✅
- panda is on `mazda-port-additions` branch, has `conversun` remote ✅
- opendbc_repo is on `mazda-port-additions` branch, has `conversun` remote ✅

### Source repo location
- openpilot-comma: `/Users/cyonsun/Documents/Code/openpilot-comma` (also on `mazda-port` branch)
- Source panda: `/Users/cyonsun/Documents/Code/openpilot-comma/panda`
- Source opendbc_repo: `/Users/cyonsun/Documents/Code/openpilot-comma/opendbc_repo`

### Sunnypilot-specific conventions
- `CarController.__init__(self, dbc_names, CP, CP_SP)` — extra CP_SP param
- `CarController.update(self, CC, CC_SP, CS, now_nanos)` — extra CC_SP param
- `CarState.__init__(self, CP, CP_SP)` — extra CP_SP param
- `CarState.update()` returns `tuple[structs.CarState, structs.CarStateSP]`
- `CarState.get_can_parsers(CP, CP_SP)` — extra CP_SP param
- `CarInterface._get_params_sp(stock_cp, ret, ...)` — sunnypilot-only static hook; DO NOT MODIFY
- `PlatformConfigBase.sp_flags: int = 0` — additive field, safe default
- Mazda CarController inherits `IntelligentCruiseButtonManagementInterface` (ICBM)
- `_get_params_sp` sets `intelligentCruiseButtonManagementAvailable = True`

### Current state of target files (opendbc_repo on mazda-port-additions):
- `values.py`: GEN1-only (103 lines) — MazdaFlags.GEN1=1, no GEN2/TI
- `mazda.h`: GEN1-only (106 lines) — needs full GEN2+TI 226-line replacement
- `mazda_2019.dbc`: MISSING — source is `openpilot-comma/opendbc_repo/opendbc/dbc/mazda_2019.dbc`
- `mazda_3_2019.dbc`: EXISTS in opendbc_repo (sunnypilot keeps this for GEN1?)
- `dbc.py`: no mazda2019 checksum entry
- `panda/python/__init__.py`: no FLAG_MAZDA_GEN2 or FLAG_MAZDA_TORQUE_INTERCEPTOR
- `panda/board/main.c`: no SAFETY_MAZDA GEN2 case
- `panda/board/drivers/can_common.h`: no 0x274 GEN2 ignition hook

### Design decisions from plan
- alpha_long DISABLED per D-007 (alphaLongitudinalAvailable=False)
- TI fault: only ERROR=4/CRITICAL_ERROR=5 latch; INIT/STANDBY/OFF auto-recover (D-010)
- NO FrogPilot infrastructure: no Params(), no frogpilot_toggles, no fp_ret, no BlendedACC
- Only 2 benign FrogPilot provenance comments allowed (values.py ~49 and ~156)
- create_button_cmd GEN1 SET_PLUS/SET_MINUS forwarding PRESERVED (not conversun's hardcoded 0)
- mazda2019_checksum test vectors: checksum(0x220, None, [1,2,3,4,5,6,7]) == 0x46; checksum(0x249, None, [0]*7) == 0x53
- MAZDA_3_2019 torque substitute: "MAZDA_CX9_2021"
- Nonlinear torque params: NON_LINEAR_TORQUE_PARAMS = (4.6, 0.6, 0.134, 0.3605)
- Hold/resume timer: HOLD_DELAY_FRAMES=50, HOLD_DURATION_FRAMES=600, RESUME_DURATION_FRAMES=50

### Commit ordering for opendbc_repo mazda-port-additions (per plan)
1. mazda_2019.dbc copy (W2.1)
2. mazda.h GEN2+TI replacement (W2.2)
3. values.py GEN2 extension (W3.1)
4. fingerprints.py MAZDA_3_2019 entry (W3.6)
5. interface.py GEN2 extension (W3.3)
6. mazdacan.py GEN2 builders (W3.2)
7. dbc.py checksum (W2.3) — after mazdacan.py
8. carcontroller.py GEN2 extension (W3.5)
9. carstate.py GEN2 extension (W3.4)
10. safety/tests/common.py GEN2 sibling skip (W2.4)
11. test_mazda.py GEN2+TI test classes (W3.9)
12. substitute.toml MAZDA_3_2019 entry (W3.7)

## 2026-05-09 W3.4: carstate.py GEN2 extension

### Commit
- `7df8a96d` on `mazda-port-additions` — "mazda: extend carstate.py for MAZDA_3_2019 (GEN2 + TI feedback)"
- 1 file changed, 160 insertions(+), 2 deletions(-)

### What was done
- Added `DT_CTRL`, `CarControllerParams`, `MazdaFlags`, `TI_STATE` imports
- Added GEN2-only attrs in `__init__`: `self.params`, `self._prev_steering_angle`, `self.ti_state`, `self.acc_values`
- `update()` now dispatches to `_update_gen1()` or `_update_gen2()` based on `MazdaFlags.GEN2`
- `_update_gen1()` — exact original GEN1 logic preserved (no changes)
- `_update_gen2()` — full GEN2 + TI feedback path: wheel speeds from cam bus, imperial/metric unit handling, TI 4-MCU fault detection, numerical steeringRateDeg, EPS_FEEDBACK torque, binary brake, CRUZE_STATE cruise, ACC snapshot for T11
- `get_can_parsers()` — GEN2 branch with pt/cam/body bus message lists
- Compile verified: `python3 -m py_compile` exits 0

## 2026-05-09 W3.5: carcontroller.py GEN2 extension

### Commit
- `b0813b9d` on `mazda-port-additions` — "mazda: extend carcontroller.py for MAZDA_3_2019 (GEN2 ACC + TI steering)"
- 1 file changed, 133 insertions(+), 37 deletions(-)

### What was done
- Added GEN2 lateral branch: instance-based `self.params.STEER_MAX` (8000), TI torque-interceptor path with `apply_ti_steer_torque_limits`, TI fault gate (zero torque when TI_STATE != RUN)
- Added GEN2 longitudinal branch: standstill frame tracking, ACC hold/resume logic at 50 Hz with HOLD_DELAY_FRAMES=50, HOLD_DURATION_FRAMES=600, RESUME_DURATION_FRAMES=50
- GEN1 path preserved 1:1 from upstream baseline using class-level `CarControllerParams.STEER_MAX` (800)
- ICBM gated to GEN1 only (inside `else:` branch) — GEN2 uses different button protocol
- Instance-based `self.params = CarControllerParams(CP)` for GEN2/GEN1 STEER_MAX split
- `ti_apply_torque_last` tracked separately (not yet used for separate TI CAN message)
- `LongCtrlState` imported from `structs.CarControl.Actuators.LongControlState` (same pattern as honda/hyundai/gm/ford/toyota)
- Compile verified: `python3 -m py_compile` exits 0
