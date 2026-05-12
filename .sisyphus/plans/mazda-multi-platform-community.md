# Plan — `mazda-multi-platform-community` (Scope C)

> **Status**: APPROVED (all open questions resolved with defaults). NOT yet executed.
> **Base branch**: `mazda-3-2019-community` (sunnypilot)
> **New branch**: `mazda-multi-platform-community` (sunnypilot)
> **Submodule branches**: `mazda-multi-platform-additions` in both `conversun/opendbc` and `conversun/panda`
> **Source fork (REFERENCE ONLY)**: `/Users/cyonsun/Documents/Code/openpilot-more` branch `mazda-frogpilot` HEAD `f0526a2c1`
> **Source fork remote**: `git@github.com:MoreTore/openpilot.git`

## 0. Verified Repo Facts (grounding)

| Fact | Value | Source |
|---|---|---|
| Base branch HEAD commit | `6d0cc2ddfc docs: correct alpha-long status to match current opendbc submodule` | `git log -1 --oneline mazda-3-2019-community` (verified 2026-05-12) |
| Base branch tag | **NONE** — `v0.11.1-mazda3-2019.0.2` referenced by `PORT_STATUS.md` does NOT exist; `git tag --list 'v0.11.1*'` returns empty. Treat PORT_STATUS.md as stale documentation. | `git tag --list 'v0.11.1*'` |
| Submodule URLs | `conversun/opendbc`, `conversun/panda` | `.gitmodules` |
| Current opendbc_repo SHA (verified) | **`47d7ffe4`** (tag `v2026.001.003-mazda3-2019.0.1` per `.sisyphus/plans/mazda-3-2019-community-branch.md`) | `git ls-tree mazda-3-2019-community opendbc_repo` (verified 2026-05-12) |
| Current panda SHA (verified) | **`cb1cdc6a`** | `git ls-tree mazda-3-2019-community panda` (verified 2026-05-12) |
| Existing safety pytest baseline | 79 passed / 0 failed / 15 skipped | PORT_STATUS.md |
| ICBM precedent | `opendbc/sunnypilot/car/mazda/icbm.py` (44 lines, GEN1-only, sp-param) | explore agent |
| `mazda_2017.dbc` in sunnypilot | 791 lines; **NO CAM_LKAS2 / NO TI_FEEDBACK** | explore agent |
| `mazda_2017.dbc` in source fork | 780 lines; **HAS CAM_LKAS2 (0x249) + TI_FEEDBACK (0x24A)** | explore agent |
| `mazda_2023.dbc` in source fork | 660 lines (only in source fork) | explore agent |
| Source fork TI fingerprints | SAME as base GEN1 (TI is hardware-only) | explore agent |
| Source fork test coverage for GEN2/GEN3/TI | NONE | explore agent |
| Oracle confidence (a) GEN1+TI separate variants | 90% | bg_34a4ea22 |
| Oracle confidence (B) GEN3 typed config | 85% | bg_e3c65d09 |

## 1. Top-Level Strategy

- **Branch base:** `mazda-3-2019-community` at commit `6d0cc2ddfc` (preserves current submodule SHAs `47d7ffe4` / `cb1cdc6a`).
- **Branch name:** `mazda-multi-platform-community`
- **Submodule strategy:** NEW branches `mazda-multi-platform-additions` in `conversun/opendbc` (forked from current `47d7ffe4`) and `conversun/panda` (forked from current `cb1cdc6a`). Existing branches untouched.
- **Atomic commit policy:** ~30 atomic commits across 3 repos; one logical change per commit; submodule bumps batched per-track; NO squash. Bisectable per-track.
- **TDD discipline:** tests-before-impl in T1 (GEN1+TI safety) and T3 (GEN3 safety).
- **5 tracks** with explicit independence:
  - **Track 0** = Branch + submodule scaffolding + ADR drafts (FOUNDATION)
  - **Track 1** = GEN1+TI1 (4 new CAR variants, dual-emit lateral). SMALLEST.
  - **Track 2** = GEN2 CX-30/CX-50 (2 new CAR variants). Pure data + tuning.
  - **Track 3** = GEN3 Mazda3-2023/CX-30-2023 (2 new CAR variants + GEN3 flag + carstate refactor + new DBC + new safety path). LARGEST.
  - **Track 4** = Documentation (ADRs, HARDWARE_TI.md rename, MIGRATION_GUIDE update, README surface).
- **Lock invariants** (MUST NOT regress):
  - `selfdrive/controls/lib/longcontrol.py` zero-diff vs upstream master.
  - `mazda2019_checksum` byte-perfect (6 test vectors).
  - GEN2 hold/resume constants (0.5s / 6.0s / 0.5s at 100Hz) unchanged.
  - Existing safety pytest baseline 79/0/15 must not regress (additions only).
  - Existing MAZDA_3_2019 platform behavior unchanged (no flag rewrites).
  - Existing FrogPilot provenance comments at `values.py:49,156` stay (2 known exceptions).
- **Forbidden-token scrub** (per D-004): 0 hits for `frogpilot_toggles|FrogPilot|fp_ret|FPCP|BlendedACC|TorqueInterceptorEnabled|frogpilot|RadarInterceptorEnabled|NoMRCC|NoFSC` (except 2 known provenance comments).
- **No on-vehicle testing** in this plan. Scope C is offline-verifiable only.
- **No upstream PR**: per D-011, distribute via conversun forks only.

## 2. Resolved Open Questions (defaults adopted)

| # | Question | Resolution |
|---|---|---|
| Q4 | HARDWARE_TI naming | **Rename HARDWARE_TI2.md → HARDWARE_TI.md** (single file: TI1 + TI2 + GEN3-no-TI sections) |
| Q5 | GEN1 vs GEN1+TI fingerprint disambiguation | **Manual selection** via comma device menu + bold WARNING in HARDWARE_TI.md |
| Q6 | Fingerprint provenance | Copy CX-30/CX-50/CX-30 2023 verbatim from source fork; Mazda3 2023 marked TBD with structured comment |
| Q7 | Test routes | NO new entries; structured TBD comment per platform |
| Q9 | Submodule branch name | `mazda-multi-platform-additions` |
| Q11 | Existing GEN2+TI dead code in mazda.h | LEAVE in place (smaller diff, future-proof) |

## 3. Atomic Commit Strategy

### Repo: `conversun/opendbc` branch `mazda-multi-platform-additions`

| # | Track | Subject |
|---|---|---|
| O1 | T1 | `mazda: port CAM_LKAS2 (0x249) and TI_FEEDBACK (0x24A) into mazda_2017.dbc` |
| O2 | T1 | `safety/mazda: add GEN1+TI rx_checks (mazda_ti_rx_checks) and TX whitelist (MAZDA_GEN1_TI_TX_MSGS)` |
| O3 | T1 | `safety/tests: add TestMazdaGen1TiSafety class for GEN1+TI variants` |
| O4 | T1 | `safety/tests/common: extend sibling-skip rule to cover GEN1+TI pair` |
| O5 | T2 | `mazda: route GEN2 NON_LINEAR_TORQUE_PARAMS for CX_30 and CX_50 in values.py` |
| O6 | T3 | `mazda: import mazda_2023.dbc for GEN3 platforms` |
| O7 | T3 | `opendbc/can/dbc: register mazda2019_checksum for mazda_2023.dbc (verify existing coverage)` |
| O8 | T3 | `safety/mazda: add GEN3 rx_checks (mazda_2023_rx_checks) — BRAKE 0x9F, CRUISE 0x44A bus 1, SPEED 0x215` |
| O9 | T3 | `safety/mazda: GEN3 flag handling in mazda_init (uses GEN2 TX whitelist, GEN3 rx_checks)` |
| O10 | T3 | `safety/tests: add TestMazdaGen3Safety class` |
| O11 | T3 | `safety/tests/common: extend sibling-skip rule for GEN3 pair (only if O10 produces false positives)` |

### Repo: `conversun/panda` branch `mazda-multi-platform-additions`

| # | Track | Subject |
|---|---|---|
| P1 | T3 | `mazda: add FLAG_MAZDA_GEN3 = 4 constant in python/__init__.py` |

### Repo: `sunnypilot` branch `mazda-multi-platform-community`

| # | Track | Subject |
|---|---|---|
| S1 | T0 | `submodule: point opendbc + panda to new mazda-multi-platform-additions branches` |
| S2 | T1 | `mazda: add MAZDA_CX5_TI/CX9_TI/3_TI/6_TI platforms in values.py (flags=GEN1\|TORQUE_INTERCEPTOR=9)` |
| S3 | T1 | `mazda: extend interface.py with GEN1+TI branch (safetyParam, minSteerSpeed=0, dashcamOnly=False)` |
| S4 | T1 | `mazda: extend mazdacan.py for dual-emit CAM_LKAS + CAM_LKAS2 (KEY=3294744160) on GEN1+TI` |
| S5 | T1 | `mazda: extend carcontroller.py GEN1+TI lateral path (apply_ti_steer_torque_limits, ti_lkas_allowed gate)` |
| S6 | T1 | `mazda: extend carstate.py for GEN1+TI TI_FEEDBACK reading (ti_state, ramp_down, fault per D-010)` |
| S7 | T1 | `mazda: mirror GEN1 FW_VERSIONS into TI variants in fingerprints.py` |
| S8 | T1 | `submodule: bump opendbc_repo for GEN1+TI safety + dbc + tests` |
| S9 | T2 | `mazda: add MAZDA_CX_30 and MAZDA_CX_50 PlatformConfigs (GEN2 flag) in values.py` |
| S10 | T2 | `mazda: add CX_30 and CX_50 FW_VERSIONS in fingerprints.py` |
| S11 | T2 | `submodule: bump opendbc_repo for GEN2 NON_LINEAR_TORQUE_PARAMS routing` |
| S12 | T3 | `mazda: introduce MazdaFlags.GEN3 = 4 and MazdaGenSignalConfig in values.py` |
| S13 | T3 | `mazda: add MAZDA_3_2023 and MAZDA_CX_30_2023 PlatformConfigs (GEN3 flag, mazda_2023.dbc routing)` |
| S14 | T3 | `mazda: refactor carstate.py _update_gen2 to parameterized signal config; add GEN3 signal table` |
| S15 | T3 | `mazda: extend interface.py with GEN3 branch (long disabled, alphaLong disabled)` |
| S16 | T3 | `mazda: add GEN3 fingerprints/FINGERPRINTS in fingerprints.py` |
| S17 | T3 | `submodule: bump panda for FLAG_MAZDA_GEN3` |
| S18 | T3 | `submodule: bump opendbc_repo for GEN3 safety + dbc + tests` |
| S19 | T4 | `docs/migration/DECISIONS: add D-012/D-013/D-014/D-015; mark D-002 superseded` |
| S20 | T4 | `docs/migration/PORT_STATUS: update scope and per-platform status grid` |
| S21 | T4 | `docs/migration/ROADMAP: update Out-of-Scope section` |
| S22 | T4 | `docs: rename HARDWARE_TI2.md to HARDWARE_TI.md; expand for GEN1+TI1, GEN2+TI2, GEN3` |
| S23 | T4 | `docs/migration/MIGRATION_GUIDE: add per-platform porting note + new commit chain table` |
| S24 | T4 | `docs/CARS or README: surface new supported platforms` |

## 4. Parallel Task Graph (Waves)

```
Wave 0 — FOUNDATION
  T0a (branch) → T0b (submodule branches) → T0c (clone-from-scratch verify)
  T0d (ADR drafts) || T0e (audit code vs source fork)

Wave 1 — TRACK 1 GEN1+TI (TDD, sequential within track)
  T1.1 (test_mazda.py: TestMazdaGen1TiSafety scaffold) — TEST FIRST (RED)
  T1.2 (mazda_2017.dbc: port CAM_LKAS2 + TI_FEEDBACK)
  T1.3 (safety/mazda.h: mazda_ti_rx_checks + GEN1_TI_TX_MSGS)
  T1.4 (safety/tests/common.py: sibling-skip extension if needed)
  T1.5 (safety pytest GREEN gate)
  T1.6 (values.py: 4 TI CAR variants)
  T1.7 (mazdacan.py: dual-emit)
  T1.8 (carcontroller.py: GEN1+TI lateral)
  T1.9 (carstate.py: TI_FEEDBACK reading)
  T1.10 (fingerprints.py: mirror FW)
  T1.11 (interface.py: GEN1+TI branch)
  T1.12 (verification gate)
  T1.13 (submodule bump)

Wave 2 — TRACK 2 GEN2 (parallel-with-T1 after T0c)
  T2.1 (values.py: CX_30, CX_50 PlatformConfigs)
  T2.2 (fingerprints.py: CX_30, CX_50 FW_VERSIONS)
  T2.3 (NON_LINEAR_TORQUE_PARAMS: CX_30 = CX_50 = (4.68689, 0.79999, 0.18244, 0.38763))
  T2.4 (smoke: CarParams sanity for new platforms)
  T2.5 (verification gate)

Wave 3 — TRACK 3 GEN3 (TDD, mostly sequential)
  T3.1 (test_mazda.py: TestMazdaGen3Safety scaffold) — TEST FIRST (RED)
  T3.2 (panda: FLAG_MAZDA_GEN3 = 4)
  T3.3 (mazda_2023.dbc: import from source fork)
  T3.4 (dbc.py: verify mazda2019_checksum covers mazda_2023)
  T3.5 (safety/mazda.h: GEN3 rx_checks + flag handling)
  T3.6 (safety pytest GREEN gate)
  T3.7 (values.py: MazdaFlags.GEN3 + MazdaGenSignalConfig + 2 platforms)
  T3.7b (Momus-mandated: capture GEN2 baseline CarState fixture for byte-perfect regression)
  T3.8 (carstate.py: refactor _update_gen2 to typed config; add GEN3 table) — GEN2 BYTE-PERFECT REGRESSION GATE
  T3.9 (interface.py: GEN3 branch)
  T3.10 (fingerprints.py: GEN3 entries)
  T3.11 (verification gate + GEN2 byte-perfect re-check)
  T3.12 (submodule bumps panda + opendbc)

Wave 4 — TRACK 4 Documentation (parallel within, after T1+T2+T3)
  T4.1 (DECISIONS.md ADRs)
  T4.2 (PORT_STATUS.md)
  T4.3 (ROADMAP.md)
  T4.4 (HARDWARE_TI.md rename + expand)
  T4.5 (MIGRATION_GUIDE.md)
  T4.6 (README/CARS.md)
  T4.7 (verification: lint + broken-link)

Wave 5 — FINAL VERIFICATION + PUSH
  T5.1 (clone-from-scratch local) → T5.2 (build) → T5.3 (lint full) → T5.4 (pytest)
  T5.5 (fingerprint pytest) → T5.6 (forbidden-token scrub) → T5.7 (checksum byte-perfect)
  T5.8 (push) → T5.9 (clone-from-scratch remote)
```

## 5. Task Catalogue (self-contained)

### Wave 0 — Foundation

| ID | Action | Category | load_skills | Files | Success criteria | Verification | Deps |
|---|---|---|---|---|---|---|---|
| T0a | Create `mazda-multi-platform-community` branch from `mazda-3-2019-community` tip in sunnypilot | quick | `["git-master"]` | local refs | Branch exists; HEAD = current `mazda-3-2019-community` HEAD | `git rev-parse mazda-multi-platform-community mazda-3-2019-community` returns equal SHAs | none |
| T0b | Create `mazda-multi-platform-additions` branches in conversun/opendbc (from `47d7ffe4`) and conversun/panda (from `cb1cdc6a`); push to remotes | quick | `["git-master"]` | remote refs | Both branches on remote; tips = expected SHAs | `gh api repos/conversun/opendbc/branches/mazda-multi-platform-additions --jq .commit.sha` returns 47d7ffe4adc092f42e87a4902b987009b985adf7; same for panda returns cb1cdc6a8c892ea0f1c6fed7cf791f72a8a72623 | T0a |
| T0c | Flip `.gitmodules` branch attributes; verify clean submodule update | quick | `["git-master"]` | `.gitmodules` | `git submodule update --init --recursive` exits 0 | `git -C opendbc_repo branch --show-current` returns mazda-multi-platform-additions; same for panda | T0b |
| T0d | Draft 4 ADRs (D-012 supersedes D-002; D-013 GEN1+TI Option a; D-014 GEN3 typed config; D-015 GEN3 long disabled) as scratch markdown | writing | `[]` | scratch | All 4 follow precedent format (Status/Date/Wave/Context/Decision/Rationale/Consequences/Challenge) | manual review against DECISIONS.md §D-001 template | T0a |
| T0e | Audit gap analysis: messages/signals in sunnypilot mazda_2017.dbc vs source fork | unspecified-low | `[]` | report | List of: messages to add (CAM_LKAS2, TI_FEEDBACK), KEY=3294744160, signal differences | `diff <(grep '^BO_' sunnypilot/opendbc_repo/opendbc/dbc/mazda_2017.dbc) <(grep '^BO_' openpilot-more/opendbc/mazda_2017.dbc)` | none |

**Wave 0 gate:** T0c clone-from-scratch passes before any code commits. Estimate: 30-45 min.

### Wave 1 — Track 1 GEN1+TI (TDD-FIRST)

| ID | Action | Category | load_skills | Files | Success criteria | Verification | Deps |
|---|---|---|---|---|---|---|---|
| T1.1 | Write `TestMazdaGen1TiSafety(TestMazdaSafety)` in `opendbc_repo/opendbc/safety/tests/test_mazda.py`. TX_MSGS=[{0x243,0},{0x249,1},{0x09d,0},{0x440,0}]; DRIVER_TORQUE_BUS=MAZDA_AUX(1); FLAGS=FLAG_MAZDA_TORQUE_INTERCEPTOR(8); NO GEN2 | deep | `[]` | `test_mazda.py` | Test class compiles; pytest runs RED (mazda_ti_rx_checks not yet defined) | `cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py::TestMazdaGen1TiSafety -x` returns expected ImportError or AssertionError | T0c |
| T1.2 | Port CAM_LKAS2 (BO_ 585) + TI_FEEDBACK (BO_ 586) from source fork's `mazda_2017.dbc` into sunnypilot's `opendbc_repo/opendbc/dbc/mazda_2017.dbc`. Preserve KEY range [3294744159..3294744161] | unspecified-high | `[]` | `mazda_2017.dbc` | DBC parses; messages at 0x249, 0x24A present | `grep -c '^BO_ 585 CAM_LKAS2' opendbc_repo/opendbc/dbc/mazda_2017.dbc` returns 1; `grep -c '^BO_ 586 TI_FEEDBACK'` returns 1; `python3 -c 'from opendbc.car.mazda.values import DBC; print(DBC)'` exits 0 | T0c |
| T1.3 | Add `mazda_ti_rx_checks[]` and `MAZDA_GEN1_TI_TX_MSGS[]` arrays; extend `mazda_init()` flag selection in `opendbc/safety/modes/mazda.h` | deep | `[]` | `mazda.h` | C compiles; param=8 activates GEN1+TI path | `cd opendbc_repo/opendbc/safety/tests && python -c 'from libsafety import libsafety_py'` exits 0; T1.1 pytest now passes | T1.1, T1.2 |
| T1.4 | Extend `opendbc_repo/opendbc/safety/tests/common.py` sibling-skip rule for `TestMazda*` GEN1/GEN1+TI pair (only if T1.5 reveals false positives in `test_tx_hook_on_wrong_safety_mode`) | quick | `[]` | `common.py` | 0 false positives across sibling pair | `cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py -k 'wrong_safety_mode' -v` returns 0 failures | T1.3 |
| T1.5 | Track 1 safety pytest GREEN gate | quick | `[]` | none | All Mazda safety tests pass; new TI tests add to passed count | `cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py --confcutdir=. --rootdir=. -p no:cacheprovider -o addopts=` reports `(79 + N) passed / 0 failed / (15 + M) skipped` | T1.4 |
| T1.6 | Add 4 PlatformConfigs (`MAZDA_CX5_TI`, `MAZDA_CX9_TI`, `MAZDA_3_TI`, `MAZDA_6_TI`) in `opendbc/car/mazda/values.py` with `flags=MazdaFlags.GEN1\|MazdaFlags.TORQUE_INTERCEPTOR` (=9); reuse base GEN1 CarSpecs; use `mazda_2017.dbc` | unspecified-high | `[]` | `values.py` | py_compile clean; 4 new CAR entries | `python3 -m py_compile opendbc/car/mazda/values.py` exits 0; `python3 -c 'from opendbc.car.mazda.values import CAR; print(len([c for c in CAR if str(c).endswith("_TI")]))'` returns 4 | T1.5 |
| T1.7 | Extend `mazdacan.py` `create_steering_control()` GEN1 branch: when `CP.flags & TORQUE_INTERCEPTOR`, additionally emit CAM_LKAS2 (0x249 bus 1) with KEY=3294744160, CHKSUM=apply_steer, LKAS_REQUEST=ti_apply_steer | unspecified-high | `[]` | `mazdacan.py` | New branch; non-TI GEN1 behavior unchanged | `python3 -m py_compile` exits 0; smoke: `create_steering_control(...)` for TI variant returns list of 2 CAN msgs (vs 1 for non-TI) | T1.6 |
| T1.8 | Extend `carcontroller.py` GEN1 path: compute `ti_apply_torque = apply_ti_steer_torque_limits(...)`; gate by `CS.ti_lkas_allowed`; pass to dual-emit | unspecified-high | `[]` | `carcontroller.py` | GEN1 non-TI byte-identical | `python3 -m py_compile` exits 0; diff vs base: only new GEN1+TI branches added | T1.7 |
| T1.9 | Extend `carstate.py` `_update_gen1()`: read TI_FEEDBACK (0x24A bus 1) signals STATE, RAMP_DOWN, ERROR, VIOL, VERSION_NUMBER; compute `ti_state`, `ti_lkas_allowed`, `ti_fault_permanent` per D-010 (only ERROR/CRITICAL_ERROR latch); override STEER_TORQUE source when TI flag set | deep | `[]` | `carstate.py` | py_compile; non-TI GEN1 path unchanged | `python3 -m py_compile` exits 0; manual: `cp.parsers` for MAZDA_CX5_TI includes TI_FEEDBACK; for MAZDA_CX5 does not | T1.8 |
| T1.10 | Mirror existing GEN1 FW_VERSIONS into TI variants in `fingerprints.py` (identical FW; TI is hardware add-on) | unspecified-low | `[]` | `fingerprints.py` | 4 new blocks | `python3 -m py_compile`; `python3 -c 'from opendbc.car.mazda.fingerprints import FW_VERSIONS; from opendbc.car.mazda.values import CAR; assert CAR.MAZDA_CX5_TI in FW_VERSIONS'` exits 0 | T1.9 |
| T1.11 | Extend `interface.py` `_get_params()` GEN1+TI branch: `safetyParam \|= TORQUE_INTERCEPTOR (8)`; `dashcamOnly=False`; `minSteerSpeed=0` | unspecified-high | `[]` | `interface.py` | py_compile; CarParams sane for TI variants | `python3 -m py_compile`; `python3 -c 'from opendbc.car.mazda.interface import CarInterface; from opendbc.car.mazda.values import CAR; cp = CarInterface.get_params(str(CAR.MAZDA_CX5_TI), {}, [], False, False, False); assert cp.dashcamOnly == False and cp.safetyConfigs[0].safetyParam == 8'` exits 0 | T1.10 |
| T1.12 | Track 1 verification gate (Wave 1 complete) | deep | `[]` | none | py_compile all changed `.py` clean; pytest 79+N/0/15+M green; `./tools/op.sh lint --fast opendbc/car/mazda/` clean; forbidden-token scrub 0 hits except 2 known | concatenation of T1.5 + py_compile loop + lint + grep | T1.11 |
| T1.13 | Submodule bump: `cd opendbc_repo && git push conversun mazda-multi-platform-additions; cd .. && git add opendbc_repo && git commit -m 'submodule: bump opendbc_repo for GEN1+TI safety + dbc + tests'` | quick | `["git-master"]` | submodule pointer | Clean submodule status | `git submodule status opendbc_repo` shows new SHA, no `+` prefix | T1.12 |

**Wave 1 gate:** T1.12 all four verification commands green. Estimate: 4-6h.

### Wave 2 — Track 2 GEN2 (CX-30, CX-50)

| ID | Action | Category | load_skills | Files | Success criteria | Verification | Deps |
|---|---|---|---|---|---|---|---|
| T2.1 | Add `MAZDA_CX_30` (mass=1531kg, wheelbase=2.814, steerRatio=15.5) and `MAZDA_CX_50` (same specs) PlatformConfigs in `values.py` with `flags=MazdaFlags.GEN2`; uses mazda_2019.dbc via flag-based init() | unspecified-low | `[]` | `values.py` | py_compile; 2 new CAR entries; init() routes to mazda_2019 | `python3 -m py_compile`; `python3 -c 'from opendbc.car.mazda.values import CAR, DBC; from opendbc.car import Bus; assert DBC[CAR.MAZDA_CX_30][Bus.pt] == "mazda_2019"'` exits 0 | T0c |
| T2.2 | Add CX_30 and CX_50 FW_VERSIONS blocks in `fingerprints.py` (verbatim from source fork) | unspecified-low | `[]` | `fingerprints.py` | py_compile; 2 new blocks | `python3 -m py_compile`; FW_VERSIONS dict contains both CAR entries | T2.1 |
| T2.3 | Add `NON_LINEAR_TORQUE_PARAMS` entries in `interface.py`: `CX_30 = CX_50 = (4.68689, 0.79999, 0.18244, 0.38763)` | quick | `[]` | `interface.py` | py_compile; lookup works | `python3 -m py_compile`; `python3 -c 'from opendbc.car.mazda.interface import NON_LINEAR_TORQUE_PARAMS; from opendbc.car.mazda.values import CAR; assert NON_LINEAR_TORQUE_PARAMS[CAR.MAZDA_CX_30] == (4.68689, 0.79999, 0.18244, 0.38763)'` exits 0 | T2.2 |
| T2.4 | Verify `_get_params()` returns correct CarParams for new GEN2 platforms (alphaLongitudinalAvailable=True, openpilotLongitudinalControl=False default, dashcamOnly=False) — no code change expected since logic is flag-based | unspecified-low | `[]` | none | Smoke passes | `python3 -c 'from opendbc.car.mazda.interface import CarInterface; from opendbc.car.mazda.values import CAR; cp = CarInterface.get_params(str(CAR.MAZDA_CX_30), {}, [], False, False, False); assert cp.dashcamOnly == False and cp.alphaLongitudinalAvailable == True'` exits 0 | T2.3 |
| T2.5 | Track 2 verification: full safety pytest unchanged (no new test class needed; GEN2 path already flag-keyed); fingerprint pytest clean; no submodule bump needed (no opendbc changes in T2) | quick | `[]` | none | 79/0/15 baseline maintained; fingerprint test green | `cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py` reports baseline; `pytest opendbc/car/tests/test_fingerprints.py -k mazda` exits 0 | T2.4 |

**Wave 2 gate:** T2.5 baseline + fingerprint pytest green. Estimate: 1-2h. Can run in parallel with Wave 1 after T0c.

### Wave 3 — Track 3 GEN3 (TDD-FIRST, largest)

| ID | Action | Category | load_skills | Files | Success criteria | Verification | Deps |
|---|---|---|---|---|---|---|---|
| T3.1 | Write `TestMazdaGen3Safety(TestMazdaGen2Safety)` in `test_mazda.py`; FLAGS=FLAG_MAZDA_GEN3(4); same TX_MSGS as GEN2; override speed/brake helpers for GEN3 addresses (0x215, 0x9F, CRUISE bus 1) | deep | `[]` | `test_mazda.py` | Test class compiles; pytest runs RED (FLAG_MAZDA_GEN3 undefined in panda) | `cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py::TestMazdaGen3Safety -x` returns expected import error | T0c |
| T3.2 | Add `FLAG_MAZDA_GEN3 = 4` in `panda/python/__init__.py` and `FLAG_MAZDA_GEN3 4U` in `mazda.h` | quick | `[]` | `panda/python/__init__.py`, `mazda.h` | py_compile + C compile | `python3 -m py_compile panda/python/__init__.py`; safety C compiles in libsafety smoke | T3.1 |
| T3.3 | Copy `mazda_2023.dbc` (660 lines) from `/Users/cyonsun/Documents/Code/openpilot-more/opendbc/mazda_2023.dbc` to `opendbc_repo/opendbc/dbc/mazda_2023.dbc` | unspecified-high | `[]` | `mazda_2023.dbc` | File present; parses; expected GEN3 messages present at VERIFIED addresses: EPS_LKAS=0x249 (585), EPS_FEEDBACK=0x24B (587), BRAKE_PEDAL=0x9F (159), WHEEL_SPEEDS=0x215 (533), CRUZE_STATE=0x44A (1098), **ACC=0x21E (542)**, **ACC_2=0x222 (546)** — NOTE: GEN3 uses 0x21E for ACC, NOT 0x220 like GEN2 | `wc -l opendbc_repo/opendbc/dbc/mazda_2023.dbc` returns 660; `grep -cE '^BO_ (585\|587\|159\|533\|1098\|542\|546) ' opendbc_repo/opendbc/dbc/mazda_2023.dbc` returns 7; sample parse via `python3 -c 'from opendbc.can.parser import CANParser; CANParser("mazda_2023", [], 0)'` exits 0 | T0c |
| T3.4 | Verify `opendbc/can/dbc.py` mazda2019_checksum registration covers `mazda_2023.dbc` (already done via `startswith("mazda_2019", "mazda_2023")` per current code) | quick | `[]` | `dbc.py` | Existing code covers; no change OR 1-line add | `grep -n 'mazda_2023' opendbc_repo/opendbc/can/dbc.py` returns ≥1 match | T3.3 |
| T3.5 | Add `mazda_2023_rx_checks[]` in `mazda.h` (BRAKE 0x9F bus 0 5Hz, CRUISE 0x44A bus 1 10Hz, SPEED 0x215 bus 2 30Hz, STEER_TORQUE 0x24B bus 1 50Hz, GAS 0x202 bus 2 100Hz); extend `mazda_init()` for GEN3 flag; extend rx_hook GEN3 branches | deep | `[]` | `mazda.h` | C compiles; param=4 selects GEN3 | libsafety smoke; T3.1 pytest now GREEN | T3.4 |
| T3.6 | Track 3 safety pytest GREEN gate (also verify GEN2 baseline maintained) | quick | `[]` | none | TestMazdaGen3Safety green; baseline + GEN3 = passed; failures = 0 | `cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py` reports baseline + GEN3 new green | T3.5 |
| T3.7 | Add `MazdaFlags.GEN3 = 4` + `MazdaGenSignalConfig` dataclass + 2 PlatformConfigs (MAZDA_3_2023 specs: mass=1361kg, wheelbase=2.725, steerRatio=18.8; MAZDA_CX_30_2023 specs: mass=1531kg, wheelbase=2.814, steerRatio=15.5) in `values.py`. Extend `MazdaPlatformConfig.init()`: GEN3 → mazda_2023 DBC | deep | `[]` | `values.py` | py_compile; 2 new CAR; init() routes correctly | `python3 -m py_compile`; `python3 -c 'from opendbc.car.mazda.values import CAR, DBC; from opendbc.car import Bus; assert DBC[CAR.MAZDA_3_2023][Bus.pt] == "mazda_2023"'` exits 0 | T3.6 |
| T3.7b | **NEW (Momus-mandated fixture)**: Before T3.8 refactor, generate GEN2 baseline CarState snapshot. Write `opendbc_repo/opendbc/car/mazda/tests/test_carstate_gen2_regression.py` containing: (1) synthetic CAN bus snapshot — canned `{(addr, bus): bytes}` dict covering all GEN2 RX messages (STEER 0x24B/1, BRAKE_PEDAL 0x43F/0, ENGINE_DATA 0x202/2, WHEEL_SPEEDS 0x215/2, SPEED 0x217/2, CRUZE_STATE 0x44A/0, BLINK_INFO/0, SYSTEM_SETTINGS/0, EPS_FEEDBACK 0x24B/1) with realistic seed values; (2) call current `_update_gen2()` via `CarState.update()` with this snapshot; (3) pickle resulting CarState struct to `opendbc/car/mazda/tests/fixtures/gen2_carstate_baseline.pkl`. Commit pickle as binary artifact. | deep | `[]` | `test_carstate_gen2_regression.py` (new), `fixtures/gen2_carstate_baseline.pkl` (new) | Pickle file present, loadable, contains valid CarState; baseline test green | `cd opendbc_repo && uv run python -m pytest opendbc/car/mazda/tests/test_carstate_gen2_regression.py::test_baseline_snapshot_creation -x` exits 0; `ls -la opendbc_repo/opendbc/car/mazda/tests/fixtures/gen2_carstate_baseline.pkl` shows non-empty file | T3.7 |
| T3.8 | Refactor `carstate.py` `_update_gen2()` to accept `signal_cfg: MazdaGenSignalConfig`. Add GEN2 cfg (existing constants extracted to dataclass) + GEN3 cfg (cruise_state_bus=1, brake_addr=0x9F, speed_addr=0x215, cruise_state_threshold=3, acc_state_addr=0x21E). Dispatch in `update()`. **MUST preserve byte-perfect GEN2 behavior**: T3.7b fixture must replay identically. | deep | `[]` | `carstate.py` | py_compile; GEN2 regression test passes byte-identical | py_compile; `cd opendbc_repo && uv run python -m pytest opendbc/car/mazda/tests/test_carstate_gen2_regression.py::test_gen2_byte_perfect_replay -x` exits 0 (test logic: load baseline.pkl, replay refactored `_update_gen2()` with same canned bus data, `assert refactored_carstate == baseline_carstate` field-by-field) | T3.7b |
| T3.9 | Extend `interface.py` `_get_params()` GEN3 branch: `safetyParam \|= FLAG_MAZDA_GEN3 (4)`; `openpilotLongitudinalControl=False`; `alphaLongitudinalAvailable=False`; `steerActuatorDelay=0.335` | unspecified-high | `[]` | `interface.py` | py_compile; CarParams for GEN3 has long disabled | `python3 -m py_compile`; `python3 -c 'from opendbc.car.mazda.interface import CarInterface; from opendbc.car.mazda.values import CAR; cp = CarInterface.get_params(str(CAR.MAZDA_3_2023), {}, [], False, False, False); assert cp.openpilotLongitudinalControl == False and cp.alphaLongitudinalAvailable == False'` exits 0 | T3.8 |
| T3.10 | Add GEN3 entries in `fingerprints.py`: CX_30_2023 FINGERPRINTS verbatim from source fork; MAZDA_3_2023 marked TBD with structured comment (`# TODO: capture FW via tools/car_porting/auto_fingerprint.py on real hardware — source fork has no Mazda3 2023 entries`) | unspecified-low | `[]` | `fingerprints.py` | py_compile; FINGERPRINTS dict contains CX_30_2023 | `python3 -m py_compile`; grep for TODO comment present | T3.9 |
| T3.11 | Track 3 verification gate: full pytest + py_compile + lint + GEN2 byte-perfect via T3.7b fixture + mazda2019_checksum 6-vector check | deep | `[]` | none | All gates green; GEN2 byte-identical via fixture replay AND checksum vectors | concat: T3.6 + py_compile loop + lint --fast + `cd opendbc_repo && uv run python -m pytest opendbc/car/mazda/tests/test_carstate_gen2_regression.py -x` (byte-perfect replay) + inline Python smoke recomputing 6 checksum vectors against locked values (vectors as constants in T3.7b script for reproducibility) | T3.10 |
| T3.12 | Submodule bumps: panda first (for FLAG_MAZDA_GEN3 visibility), then opendbc | quick | `["git-master"]` | submodule pointers | Both at GEN3 tips; clean status | `git submodule status` shows new SHAs, no `+` prefix | T3.11 |

**Wave 3 gate:** T3.11 + GEN2 byte-perfect regression UNCHANGED. Estimate: 6-10h.

### Wave 4 — Track 4 Documentation

| ID | Action | Category | load_skills | Files | Success criteria | Verification | Deps |
|---|---|---|---|---|---|---|---|
| T4.1 | Update `docs/migration/DECISIONS.md`: append D-012 (scope expansion supersedes D-002), D-013 (GEN1+TI Option a + reject Params() toggle), D-014 (GEN3 carstate typed config), D-015 (GEN3 long disabled); mark D-002 status as `Superseded by D-012` | writing | `[]` | `DECISIONS.md` | 4 new ADRs follow precedent format; D-002 superseded marker present | `grep -c '^## D-01[2-5]:' docs/migration/DECISIONS.md` returns 4; `grep 'Superseded by D-012' docs/migration/DECISIONS.md` returns ≥1; `./tools/op.sh lint --fast docs/` exits 0 | T1.13 + T2.5 + T3.12 |
| T4.2 | Update `docs/migration/PORT_STATUS.md`: new scope statement covering all 15 platforms; per-platform status grid; updated quick-commands; updated key technical facts | writing | `[]` | `PORT_STATUS.md` | All 15 platforms listed; tag references updated | `grep -c 'MAZDA_' docs/migration/PORT_STATUS.md` returns ≥15 unique mentions; lint clean | T4.1 |
| T4.3 | Update `docs/migration/ROADMAP.md`: Out-of-Scope table reduced (GEN3/CX-30/CX-50 removed from OoS); update priority queue if needed | writing | `[]` | `ROADMAP.md` | OoS no longer contains CX-30/CX-50/GEN3; D-012 referenced | `grep -A2 'Out of Scope' docs/migration/ROADMAP.md` shows updated table | T4.1 |
| T4.4 | Rename `docs/HARDWARE_TI2.md` → `docs/HARDWARE_TI.md` (single file covers TI1 GEN1, TI2 GEN2, GEN3-no-TI); add explicit TI1 vs TI2 comparison table; add bold WARNING about manual platform selection for GEN1 vs GEN1+TI disambiguation; update all internal refs | writing | `[]` | `HARDWARE_TI.md` (new), all docs referencing old name | File renamed; both TI variants covered; 0 broken refs | `test -f docs/HARDWARE_TI.md && ! test -f docs/HARDWARE_TI2.md`; `grep -r 'HARDWARE_TI2' docs/ README.md 2>/dev/null` returns 0 hits | T4.1 |
| T4.5 | Update `docs/migration/MIGRATION_GUIDE.md`: add per-platform porting note; new commit chain table (S1-S24 + O1-O11 + P1) | writing | `[]` | `MIGRATION_GUIDE.md` | New commit chain section; per-platform notes | `grep -c 'mazda-multi-platform' docs/migration/MIGRATION_GUIDE.md` returns ≥3 | T4.1 |
| T4.6 | Update `README.md` or `docs/CARS.md`: surface 15 supported platforms with alpha/dashcam/community labels | writing | `[]` | `README.md` or `docs/CARS.md` | All 15 platforms listed with correct status | `grep -c 'MAZDA_' README.md docs/CARS.md 2>/dev/null` returns ≥15 unique | T4.1 |
| T4.7 | Verification: `./tools/op.sh lint --fast docs/`; broken-link check; forbidden-token scrub on docs (allow 2 known provenance comments at values.py:49,156 only) | quick | `[]` | none | All clean | `./tools/op.sh lint --fast docs/` exits 0; `grep -nrE 'frogpilot_toggles\|FrogPilot\|fp_ret\|FPCP\|BlendedACC\|TorqueInterceptorEnabled' docs/` returns 0 hits | T4.6 |

**Wave 4 gate:** T4.7. Estimate: 2-3h.

### Wave 5 — Final Verification + Push

| ID | Action | Category | load_skills | Files | Success criteria | Verification | Deps |
|---|---|---|---|---|---|---|---|
| T5.1 | Clone-from-scratch local (precedent §6 with CLONE_SOURCE=local); verify 3 repo SHAs, LFS, submodules | deep | `["git-master"]` | tmp dir | All 8 protocol steps exit 0 | precedent §6 from `mazda-3-2019-community-branch.md` adapted with new SHAs | T4.7 |
| T5.2 | In fresh clone: `./tools/op.sh setup && source .venv/bin/activate && scons --minimal -j$(nproc)` | deep | `[]` | tmp clone | scons exits 0 | full build log tail shows zero errors | T5.1 |
| T5.3 | Full lint: `./tools/op.sh lint` (not --fast) | deep | `[]` | tmp clone | All 7 lint stages green | lint log shows EXIT 0 across stages | T5.2 |
| T5.4 | Full safety pytest: `cd opendbc_repo && uv run python -m pytest opendbc/safety/tests/test_mazda.py --confcutdir=. --rootdir=. -p no:cacheprovider -o addopts=` | deep | `[]` | tmp clone | `(79 + N_TI + N_GEN3) passed / 0 failed / (15 + M) skipped`; no regressions vs baseline | full pytest log | T5.3 |
| T5.5 | Fingerprint pytest: `pytest opendbc/car/tests/test_fingerprints.py -k mazda` | quick | `[]` | tmp clone | All fingerprints unique or marked ambiguous (TI variants share base FW — expect ambiguity flagged; suppress via test framework markers) | full pytest log | T5.4 |
| T5.6 | Forbidden-token scrub final: `grep -nrE 'frogpilot_toggles\|FrogPilot\|fp_ret\|FPCP\|BlendedACC\|TorqueInterceptorEnabled\|RadarInterceptorEnabled\|NoMRCC\|NoFSC' opendbc/ opendbc_repo/opendbc/car/mazda/ panda/ docs/` | quick | `[]` | tmp clone | 0 hits except 2 known provenance comments at opendbc_repo/opendbc/car/mazda/values.py:49,156 | grep output review | T5.5 |
| T5.7 | `mazda2019_checksum` byte-perfect 6-vector check (must match values locked from `mazda-3-2019-community` tip) | quick | `[]` | tmp clone | All 6 vectors UNCHANGED | inline Python: import mazda2019_checksum, compute against 6 canned input vectors, compare to expected outputs | T5.6 |
| T5.8 | Push: `git push -u conversun mazda-multi-platform-community`; push submodule branches if not already pushed in T1.13/T3.12 | quick | `["git-master"]` | remote refs | All 3 branches on conversun remotes; tip SHAs match local | `gh api repos/conversun/sunnypilot/branches/mazda-multi-platform-community --jq .commit.sha` returns local HEAD SHA; same for opendbc + panda | T5.7 |
| T5.9 | Clone-from-scratch remote (CLONE_SOURCE=remote): exercises network path end-to-end | deep | `["git-master"]` | tmp dir | All 8 protocol steps green from remote URL | precedent §6 with CLONE_SOURCE=remote and BRANCH=mazda-multi-platform-community | T5.8 |

**Wave 5 gate:** T5.9. Estimate: 60-90 min. Final DONE marker.

### Per-task discipline (applies to all tasks above)

- Code tasks: `python3 -m py_compile <changed.py>` REQUIRED before commit
- Safety tasks: subset pytest gate (`pytest test_mazda.py::<NewClass> -x`)
- All tasks: `./tools/op.sh lint --fast` clean before commit
- All commits: forbidden-token scrub clean
- Wave end: full verification gate (not per-commit)
- Commit message style: `<area>: <lowercase imperative>` per existing project log

## 6. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Fingerprint ambiguity GEN1 vs GEN1+TI (identical FW) | **HIGH** | HIGH | Manual selection via comma menu + bold WARNING in HARDWARE_TI.md |
| R2 | mazda_2023.dbc parser/checksum incompatibility | medium | high | T3.4 verify; T3.6 RED→GREEN |
| R3 | GEN3 carstate refactor breaks GEN2 byte-perfect lock | medium | **CRITICAL** | T3.8 explicit regression test; T3.11 must pass 6-vector check |
| R4 | mazda2019_checksum 6-vector lock broken | low | CRITICAL | T5.7 explicit hard gate |
| R5 | CAM_LKAS2/TI_FEEDBACK bit layout incompatible with current dbc parser | low | medium | T1.2 parse smoke; manual bit-offset cross-check |
| R6 | Sibling-skip rule false positives | medium | medium | T1.4 + T3.6 detect early; extend per D-009 |
| R7 | TX whitelist overlap across GEN1/GEN1+TI/GEN2/GEN3 | medium | medium | Pre-audit; skip extension required |
| R8 | KEY=3294744160 magic constant byte-order issue | low | HIGH | T1.7 match source fork exactly |
| R9 | mazda_2017.dbc base content drift between forks | medium | medium | T1.2 diff-by-message not by-line |
| R10 | FLAG_MAZDA_GEN3=4 collides with existing FLAG_MAZDA_LONG=16 | low | high | Audit init() flag selection |
| R11 | New CAR variants trigger test_fingerprints.py framework checks | medium | low | T5.5 catches |
| R12 | T3 carstate refactor scope creep | medium | medium | Plan enforces T3.8 = signal-table parameterization ONLY |
| R13 | Source fork has zero test coverage; ports inherit zero confidence | HIGH | HIGH | TDD-first in T1.1, T3.1; baseline built up |
| R14 | GEN3 STEER_TORQUE source differs from GEN2 | medium | medium | T3.8 signal config includes `steer_torque_source` field |
| R15 | experimentalLong vs alphaLong naming drift | low | low | Use sunnypilot convention (alpha) |
| R16 | Track 1 changes affect existing MAZDA_3_2019 | medium | low | T1.12 baseline 79/0/15 unchanged |
| R17 | MazdaFlags.GEN3=4 bit ordering vs LONG=16 | low | high | Verify no other bit-4 user |
| R18 | LFS endpoint failure | low | high | T5.1 catches |
| R19 | HARDWARE_TI rename leaves stale grep hits | medium | low | T4.4 grep verification |
| R20 | User drives on this branch without CP | HIGH | **CRITICAL** | HARDWARE_TI.md WARNING + README explicit DO NOT DRIVE |

## 7. Wall-Clock Estimates

| Wave | Work | Estimate |
|---|---|---|
| 0 | Branch + scaffolding + ADR drafts | 30-45 min |
| 1 | GEN1+TI code + tests + verification | 4-6 hours |
| 2 | GEN2 expansion (parallel with W1 after T0c) | 1-2 hours |
| 3 | GEN3 code + refactor + tests + verification | 6-10 hours |
| 4 | Docs writing + lint | 2-3 hours |
| 5 | Final verification + push | 60-90 min |
| **TOTAL** | | **14-23 hours over multiple sessions** |

## 8. Go/No-Go Checklist Before T0a Fires

- [x] All 6 open questions resolved (defaults adopted)
- [x] Branch name confirmed: `mazda-multi-platform-community`
- [x] Submodule branch confirmed: `mazda-multi-platform-additions`
- [x] Push target confirmed: `conversun/*` only
- [ ] `git status` clean on `mazda-3-2019-community` (verify before T0a)
- [ ] `git fetch origin && git fetch conversun` runs clean
- [ ] Submodules sync at `47d7ffe4` (opendbc_repo) / `cb1cdc6a` (panda) (no `+` prefix) — verified actual SHAs as of 2026-05-12; PORT_STATUS.md claims of `daa49373`/`251bdf57` are stale documentation
- [ ] Existing safety pytest baseline 79/0/15 captured before any change
- [ ] Existing `mazda2019_checksum` 6 test vectors captured (anchor)
- [ ] Read access verified to `/Users/cyonsun/Documents/Code/openpilot-more`

## 9. Final Clone-from-Scratch Verification Protocol (T5.1 + T5.9)

Mirror `mazda-3-2019-community-branch.md` §6 protocol with these adaptations:
- `BRANCH=mazda-multi-platform-community`
- `EXPECTED_OPENDBC_SHA` = TBD (set after T1.13/T2.6/T3.12 final bump)
- `EXPECTED_PANDA_SHA` = TBD (set after T3.12)
- Expected pytest: `79 + N_TI + N_GEN3 passed / 0 failed / 15 + M skipped` where N/M to be measured
- Mazda fingerprint sanity check: assert ALL 15 platforms present in CAR enum (existing 7: MAZDA_CX5, MAZDA_CX9, MAZDA_3, MAZDA_6, MAZDA_CX9_2021, MAZDA_CX5_2022, MAZDA_3_2019; + 4 GEN1+TI: MAZDA_CX5_TI, MAZDA_CX9_TI, MAZDA_3_TI, MAZDA_6_TI; + 2 GEN2: MAZDA_CX_30, MAZDA_CX_50; + 2 GEN3: MAZDA_3_2023, MAZDA_CX_30_2023)

---

*Plan version: 1.3 — Momus v1.2 re-review remediation: (1) `CarInterface.get_params()` calls fixed from 4 booleans to **3 booleans** `(alpha_long, is_release, docs)` per verified signature at `opendbc_repo/opendbc/car/interfaces.py:139-140`; (2) `Bus` import fixed from `opendbc.car.common.conversions` to **`opendbc.car`** per verified location at `opendbc_repo/opendbc/car/__init__.py:81`; (3) `candidate` arg wrapped in `str()` to match str-typed signature; (4) safetyParam assertion targets `cp.safetyConfigs[0].safetyParam`. All prior fixes retained. Awaiting Momus v1.3 re-review before T0a fires.*
