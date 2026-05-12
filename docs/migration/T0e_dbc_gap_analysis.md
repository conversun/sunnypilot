# T0e — DBC Gap Analysis: mazda_2017.dbc (sunnypilot vs mazda-frogpilot source fork)

**Wave**: Multi-platform Wave 0
**Date**: 2026-05-12
**Source fork**: `/Users/cyonsun/Documents/Code/openpilot-more/opendbc/mazda_2017.dbc` (branch `mazda-frogpilot`, HEAD `f0526a2c1`)
**Sunnypilot file**: `opendbc_repo/opendbc/dbc/mazda_2017.dbc` (branch `mazda-multi-platform-additions`, SHA `47d7ffe4`)

## Summary

The sunnypilot `mazda_2017.dbc` (used by all GEN1 platforms) **lacks two messages** that the source fork's `mazda_2017.dbc` carries. These messages are required for GEN1+TI1 (Original Torque Interceptor) operation.

| Aspect | Sunnypilot | Source Fork |
|---|---|---|
| `CAM_LKAS2` (0x249, bus 1) — TI LKAS request frame | **MISSING** | Present |
| `TI_FEEDBACK` (0x24A, bus 1) — TI state + torque sensor mirror | **MISSING** | Present |

T1.2 must port these two `BO_` definitions verbatim into sunnypilot's DBC.

## Message Definitions to Port (verbatim from source fork)

### `CAM_LKAS2` (0x249, 8 bytes) — bus 1 TX (openpilot → TI hardware)

```
BO_ 585 CAM_LKAS2: 8 XXX
 SG_ LKAS_REQUEST : 3|12@0+ (1,-2048) [0|2048] "" XXX
 SG_ CHKSUM : 19|12@0+ (1,-2048) [0|2048] "" XXX
 SG_ KEY : 39|32@0+ (1,0) [3294744159|3294744161] "" XXX
```

**Key constants**:
- `KEY` range `[3294744159|3294744161]` — the magic authentication constant the TI device validates. `mazdacan.py:create_steering_control()` GEN1+TI dual-emit path must send `KEY = 3294744160` (midpoint).
- `LKAS_REQUEST` is the steer torque command, offset `-2048`, scale `1`, signed via 12-bit field with offset.
- `CHKSUM` is computed by sender (openpilot via panda).

### `TI_FEEDBACK` (0x24A, 8 bytes) — bus 1 RX (TI hardware → openpilot)

```
BO_ 586 TI_FEEDBACK: 8 XXX
 SG_ TI_TORQUE_SENSOR : 7|8@0+ (1,-127) [-85|85] "" XXX
 SG_ CHKSUM : 15|8@0+ (1,-127) [-127|128] "" XXX
 SG_ VERSION_NUMBER : 23|8@0+ (1,0) [0|255] "" XXX
 SG_ STATE : 31|8@0+ (1,0) [0|3] "" XXX
 SG_ VIOL : 39|8@0+ (1,0) [0|255] "" XXX
 SG_ ERROR : 47|8@0+ (1,0) [0|255] "" XXX
 SG_ RAMP_DOWN : 55|8@0+ (1,0) [0|1] "" XXX
 SG_ SPARE : 63|8@0+ (1,0) [0|255] "" XXX
```

**Signal map for T1.9 carstate.py GEN1+TI extension**:

| Signal | Range | Purpose | Used by |
|---|---|---|---|
| `TI_TORQUE_SENSOR` | -85..85 | Mirror of EPS torque sensor as seen by TI | Override of stock STEER_TORQUE when TI active |
| `STATE` | 0..3 | TI state machine: 0=DISCOVER, 1=OFF, 2=DRIVER_OVER, 3=RUN | `ti_state`, `ti_lkas_allowed` |
| `VIOL` | 0..255 | Violation count (non-zero = TI saw unexpected behavior) | Diagnostics |
| `ERROR` | 0..255 | Error code (0 = no error) | `ti_fault_permanent` per D-010 (only ERROR/CRITICAL_ERROR latch) |
| `RAMP_DOWN` | 0..1 | TI is reducing torque (handoff to driver) | `ti_lkas_allowed = (state == RUN and not ramp_down)` |
| `VERSION_NUMBER` | 0..255 | TI firmware version | Diagnostics |
| `CHKSUM` | -127..128 | TI-computed checksum (offset -127) | Receiver validates |

## Other Mazda DBCs Checked

- `mazda_2019.dbc` (GEN2): present in both sunnypilot and source fork. Used by MAZDA_3_2019 currently. No changes needed for GEN2 expansion (CX-30, CX-50) — flag-based routing already covers it.
- `mazda_2023.dbc` (GEN3): **MISSING** from sunnypilot. Present in source fork at 660 lines. T3.3 ports verbatim. Already analyzed for ACC=0x21E + ACC_2=0x222 (NOT 0x220 like GEN2).
- `mazda_radar.dbc`: present in both. Not used by Scope C (RADAR_INTERCEPTOR is out-of-scope per D-012).

## Source Fork Line Counts

- `mazda_2017.dbc` (source fork): 780 lines
- `mazda_2017.dbc` (sunnypilot): 791 lines (slightly longer — base content drift from upstream openpilot, NOT a regression)
- `mazda_2023.dbc` (source fork): 660 lines (not in sunnypilot)

The 11-line diff between the two `mazda_2017.dbc` files needs to be examined message-by-message during T1.2 to ensure the port is additive (only adds CAM_LKAS2 + TI_FEEDBACK, doesn't modify or delete existing signals).

## T1.2 Action Items

1. Append the two `BO_` blocks above (CAM_LKAS2 and TI_FEEDBACK) to `opendbc_repo/opendbc/dbc/mazda_2017.dbc`.
2. Preserve KEY range `[3294744159|3294744161]` exactly — the magic constant is hardware-authentication critical.
3. Verify with: `grep -cE '^BO_ 585 CAM_LKAS2' opendbc_repo/opendbc/dbc/mazda_2017.dbc` returns 1; same for `^BO_ 586 TI_FEEDBACK`.
4. Smoke test DBC parses: `python3 -c "from opendbc.car.mazda.values import DBC"` exits 0.

## Risk Notes

- **R5 (plan §6)**: Bit layout incompatibility. The signal bit offsets use Motorola/big-endian (`@0+`) convention. Verify the sunnypilot DBC machinery handles this consistently (it should — it's the same format used by existing Mazda messages).
- **R8 (plan §6)**: KEY constant byte order. 3294744160 = 0xC4520AA0. The `@0+` byte order means the upper byte is at bit 39 (Motorola convention). T1.7 mazdacan.py must pack this correctly.
- **R9 (plan §6)**: base content drift (791 vs 780 lines). T1.2 should diff-by-message, not diff-by-line, to avoid contaminating with upstream changes.

---

*T0e_dbc_gap_analysis.md — Multi-platform Wave 0 / T0e completed 2026-05-12. Anchor for T1.2 DBC port.*
