# PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-10 04:31 SGT
**Commit:** df5e478d1
**Branch:** mazda-port

## OVERVIEW

sunnypilot is a fork of comma.ai openpilot (Level-2 driver assistance). Multi-language: Python 3.12 + C++17 + Cython + STM32 C firmware. Build = SCons. Pkg mgr = uv. Runs on comma three/3X (AGNOS/larch64), Linux PC, macOS arm64.

## STRUCTURE

```
sunnypilot/
├── selfdrive/      # Driving stack (controlsd, plannerd, modeld, locationd, ui)
├── system/         # System services (manager, hardware, loggerd, athena, updated)
├── common/         # Shared C++/Python utils + Params (key-value persistent store)
├── cereal/         # Cap'n Proto messaging spec - see cereal/README.md
├── msgq_repo/      # SUBMODULE - IPC backend; symlinked as msgq/
├── opendbc_repo/   # SUBMODULE (FORK: conversun/opendbc) - car interfaces + safety; symlinked as opendbc/
├── panda/          # SUBMODULE (FORK: conversun/panda) - STM32 firmware
├── rednose_repo/   # SUBMODULE - EKF library; symlinked as rednose/
├── tinygrad_repo/  # SUBMODULE (FORK: sunnypilot/tinygrad) - ML inference
├── teleoprtc_repo/ # SUBMODULE - WebRTC for body
├── sunnypilot/     # FORK-SPECIFIC code (MADS, sunnylink, mapd, modeld_v2, NNLC, ...)
├── openpilot/      # SYMLINK PACK -> ../{common,selfdrive,system,...} (namespace pkg)
├── tools/          # Dev tools: cabana, replay, sim, joystick, op.sh
├── third_party/    # Vendored native deps (acados, raylib, json11)
├── docs/           # User + migration docs
├── release/        # Release build/CI scripts
├── site_scons/     # Custom SCons builders (cython, compilation_db, rednose_filter)
├── scripts/lint/   # lint.sh + check_*.sh
├── SConstruct      # Root build orchestrator
├── pyproject.toml  # Python deps, ruff, ty, pytest, codespell config
├── conftest.py     # Root pytest fixtures (OpenpilotPrefix isolation)
├── launch_openpilot.sh    # Device entry; routes to hardware-specific launcher
├── launch_chffrplus.sh    # Main launcher (overlay updates -> manager.py)
└── launch_env.sh   # Thread caps, AGNOS_VERSION
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add a managed daemon | [system/manager/process_config.py](file:///Users/cyonsun/Documents/Code/sunnypilot/system/manager/process_config.py) |
| Add a cereal message | [cereal/log.capnp](file:///Users/cyonsun/Documents/Code/sunnypilot/cereal/log.capnp) (stock) or [cereal/custom.capnp](file:///Users/cyonsun/Documents/Code/sunnypilot/cereal/custom.capnp) (fork-only) |
| Add a Params key | [common/params_keys.h](file:///Users/cyonsun/Documents/Code/sunnypilot/common/params_keys.h) |
| Add a sunnypilot feature | `sunnypilot/...` mirroring upstream layout, with `_ext.py` suffix to extend |
| Add safety logic | [opendbc/safety/](file:///Users/cyonsun/Documents/Code/sunnypilot/opendbc_repo/opendbc/safety) (C, MISRA) - tests MUST pass with 100% coverage |
| Add a car port | [opendbc/car/{brand}/](file:///Users/cyonsun/Documents/Code/sunnypilot/opendbc_repo/opendbc/car) + [opendbc/sunnypilot/{brand}/](file:///Users/cyonsun/Documents/Code/sunnypilot/opendbc_repo/opendbc/sunnypilot) for SP extensions |
| Modify UI | [selfdrive/ui/](file:///Users/cyonsun/Documents/Code/sunnypilot/selfdrive/ui) (Raylib Python) + [selfdrive/ui/sunnypilot/](file:///Users/cyonsun/Documents/Code/sunnypilot/selfdrive/ui/sunnypilot) for SP screens |
| Modify settings UI | [sunnypilot/sunnylink/settings_ui_src/](file:///Users/cyonsun/Documents/Code/sunnypilot/sunnypilot/sunnylink/settings_ui_src) -> compile via [tools/compile_settings_ui.py](file:///Users/cyonsun/Documents/Code/sunnypilot/sunnypilot/sunnylink/tools/compile_settings_ui.py) |
| Add a test | Co-locate as `tests/test_*.py` next to module |
| Run on PC | [tools/op.sh](file:///Users/cyonsun/Documents/Code/sunnypilot/tools/op.sh) (`op setup`, `op build`, `op test`, `op lint`, `op sim`) |

## CONVENTIONS (DEVIATIONS FROM STANDARD)

### Python
- **Indent: 2 spaces** (NOT 4). Lines: 160 max. Quote style: `preserve`.
- **Type checker: `ty`** (Astral) - NOT mypy. Many rules ignored - see [pyproject.toml](file:///Users/cyonsun/Documents/Code/sunnypilot/pyproject.toml#L215-L253).
- **Test runner: pytest** with `pytest-xdist -n auto --dist=loadgroup`. NEVER `unittest`.
- **Imports: ALWAYS `from openpilot.X import Y`** (banned: bare `from common.X`, `from selfdrive.X`, `from system.X`, `from tools.X`, `from third_party.X`).
- **NEVER use `time.time()`** - use `time.monotonic()` (banned via TID251).
- **NEVER use `unittest`** - use `pytest` (banned via TID251).
- **NEVER call `pytest.main()`** directly (special-handling banned via TID251).

### Raylib UI (banned APIs - use wrappers)
- `pyray.measure_text_ex` -> `openpilot.system.ui.lib.text_measure`
- `pyray.is_mouse_button_pressed/released` -> `Widget._handle_mouse_press/release`
- `pyray.draw_text` -> use a function taking `font` argument (e.g., `rl.draw_font_ex`)
- `pyray.draw_texture` -> `rl.draw_texture_ex`
- `#include "third_party/raylib/include/raylib.h"` -> `#include "system/ui/raylib/raylib.h"`

### C++
- **Werror enforced.** `-std=c++1z` (C++17), `-std=gnu11` (C). `-Wshadow` (full on Darwin/larch64, `-Wshadow=local` elsewhere).
- **System library whitelist enforced** by SConstruct - see [SConstruct:49-53](file:///Users/cyonsun/Documents/Code/sunnypilot/SConstruct#L49-L53). Allowed: `EGL GLESv2 GL Qt5* dl drm gbm m pthread`. Anything else MUST be vendored.
- Linker flags: `-Wl,--as-needed -Wl,--no-undefined` (Linux only).

### Cython
- `.pyx` compiles to `.cpp` (NOT `.c`). Suffix: `CYTHONCFILESUFFIX=".cpp"`.
- Cython env REMOVES `-Werror`. Use `# cython: language_level = 3`.
- Generated `*_pyx.cpp` files are gitignored - DO NOT commit.

### Lint Pipeline ([scripts/lint/lint.sh](file:///Users/cyonsun/Documents/Code/sunnypilot/scripts/lint/lint.sh))
1. ruff
2. `check_added_large_files --maxkb=120`
3. `check_shebang_scripts_are_executable`
4. `check_shebang_format` (Python: `#!/usr/bin/env python3`, Bash: `#!/usr/bin/env bash`)
5. `check_nomerge_comments` - see Anti-patterns
6. `ty` (skipped with `--fast`)
7. `codespell` (skipped with `--fast`)

Post-commit hook auto-runs `op lint --fast`. Install via `op post-commit`.

## ANTI-PATTERNS (THIS PROJECT)

### SAFETY-CRITICAL (banned -> fork loses comma.ai access)
- **NEVER disable/nerf driver monitoring** - [docs/SAFETY.md:38](file:///Users/cyonsun/Documents/Code/sunnypilot/docs/SAFETY.md#L38)
- **NEVER disable/nerf excessive actuation checks** - [docs/SAFETY.md:39](file:///Users/cyonsun/Documents/Code/sunnypilot/docs/SAFETY.md#L39)
- **NEVER modify `opendbc/safety/` without preserving full test suite + 100% coverage** - [docs/SAFETY.md:40-42](file:///Users/cyonsun/Documents/Code/sunnypilot/docs/SAFETY.md#L40-L42)

### CEREAL SCHEMA (breaks log compat)
- **NEVER change Cap'n Proto identifiers** (e.g. `@0x81c2f05a394cf4af`) or field IDs (`@107`)
- **NEVER change which struct a field points to**
- **NEVER modify stock message struct field semantics** in a fork - create new structs in [cereal/custom.capnp](file:///Users/cyonsun/Documents/Code/sunnypilot/cereal/custom.capnp) instead
- All cereal fields MUST be SI units unless name says otherwise

### CODE / WORKFLOW
- **NO `# NOMERGE`/`// NOMERGE` comments** - lint blocks them ([scripts/lint/check_nomerge_comments.sh](file:///Users/cyonsun/Documents/Code/sunnypilot/scripts/lint/check_nomerge_comments.sh))
- **NO files >120 KB** committed (lint blocks)
- **NO `as any` / `@ts-ignore` equivalents** - DO NOT silence ty/ruff with broad ignores
- **NO `time.time()`** - use `time.monotonic()`
- **NO type-suppression comments** when fixing real bugs
- **DO NOT add deps outside `commaai/dependencies` whitelist** - non-vendored system libs raise `UserError` from SConstruct
- **DO NOT include unsupported cars in upstream platforms** - put in `opendbc/sunnypilot/`
- **NO 500+ line PRs** ([docs/CONTRIBUTING.md:33](file:///Users/cyonsun/Documents/Code/sunnypilot/docs/CONTRIBUTING.md#L33))

### MPC SOLVERS (silent staleness)
- `selfdrive/controls/lib/{lateral,longitudinal}_mpc_lib/`: imports outside the constants block do NOT trigger rebuild. Touch the file or run `scons --clean`.

## COMMANDS

```bash
# First-time setup
./tools/op.sh setup                  # apt deps + uv sync + submodules + LFS

# Daily dev
source .venv/bin/activate
scons -j$(nproc)                     # Full build
scons --minimal                      # Skip tests/tools (fast)
scons --verbose                      # Show full compiler invocations
./tools/op.sh build                  # PC: scons | AGNOS: system/manager/build.py

# Lint
./tools/op.sh lint                   # Full (ruff + ty + codespell + checks)
./tools/op.sh lint --fast            # Skip ty + codespell

# Test
pytest                               # Default test paths from pyproject.toml
pytest -m 'not slow'                 # Skip slow tests
pytest sunnypilot/                   # All sunnypilot tests
pytest selfdrive/controls/tests/     # Specific module

# Safety tests (different framework!)
cd opendbc_repo/opendbc/safety/tests && bash test.sh   # unittest + 100% coverage gate

# Process replay regression (NOT in default pytest collection)
python selfdrive/test/process_replay/test_processes.py

# Sim
./tools/op.sh sim                    # MetaDrive bridge + UI

# Tools
./tools/op.sh cabana                 # CAN visualizer
./tools/op.sh replay                 # Route replay
./tools/op.sh juggle                 # plotjuggler
```

## NOTES

- **`openpilot/` is a SYMLINK PACK** -> back to `common/`, `selfdrive/`, etc. Enables `from openpilot.X import Y` namespacing. NEVER edit files via the `openpilot/` path - edit the source.
- **`opendbc/` is a SYMLINK** -> `opendbc_repo/opendbc/`. Same for `msgq` -> `msgq_repo/msgq`. Both submodules ARE forks (URL: `conversun/opendbc`, `conversun/panda`).
- **Process manager `manager.py` is the supervisor** - all daemons defined in [process_config.py](file:///Users/cyonsun/Documents/Code/sunnypilot/system/manager/process_config.py). To run a single daemon for testing: `python -m openpilot.selfdrive.controls.controlsd` (after `op_activate_venv`).
- **Two model runners coexist**: stock `selfdrive/modeld/` (SNPE/PC) and sunnypilot's `sunnypilot/modeld_v2/` (tinygrad). Switched via `ModelManagerSP.Runner` cereal enum.
- **Generated files (DO NOT commit, DO NOT edit):** `*_pyx.cpp`, `cereal/gen/`, `cereal/services.h`, `selfdrive/locationd/models/generated/`, `panda/board/obj/`, `compile_commands.json`, `c_generated_code/` (acados).
- **AGNOS = comma 3/3X OS** (Ubuntu-based, larch64). `/AGNOS` file marks device. `/TICI` for tici hardware. `larch64` is the SCons arch tag.
- **Safety message lag = automatic disengage**: any monitored CAN msg lagging >1s causes `controls_allowed=false`. Affects feature additions reading new messages.
- **Submodule URLs are FORKED** for panda + opendbc + tinygrad. `git submodule update --remote` will pull from sunnypilot/conversun forks, not commaai upstream.
- Pre-existing branch `mazda-port` is in-progress car port work - see [docs/migration/](file:///Users/cyonsun/Documents/Code/sunnypilot/docs/migration).
