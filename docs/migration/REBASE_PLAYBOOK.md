# Mazda GEN2 Fork — Upstream Merge Playbook

**For:** whoever pulls in a new upstream sunnypilot release months from now.
**Scope:** 3-repo merge of the Mazda GEN2 port onto a newer `sunnypilot/sunnypilot` master.
**Filename:** kept as `REBASE_PLAYBOOK.md` because other migration docs link to it — the workflow inside is a merge, not a rebase.

> **This branch merges, it does not rebase.** Every upstream sync in this
> fork's history is a merge commit (`git log --merges`). Rebasing 70+ fork
> commits onto a moved upstream re-resolves every conflict once per commit.
> Merging resolves each conflict once. Do not switch to rebase.

## Branch map

Read this first — the branch names have changed over time.

| Repo | Branch | Remote |
|------|--------|--------|
| sunnypilot (parent) | `mazda-port` | `conversun` (SSH), `origin` = upstream sunnypilot |
| `opendbc_repo` | `mazda-gen2-oplong-lowspeed` | `origin` = `conversun/opendbc` |
| `panda` | `mazda-gen2-sync` | `conversun/panda` |

Older docs mention `mazda-port-additions` in the submodules. Those branches
still exist but are **not** what the parent's gitlinks point at. Always confirm
with `git -C <submodule> branch --show-current` before starting.

There are no `mazda-port-v*` recovery tags. Use dated backup branches instead
(created in the pre-merge checklist below).

---

## Pre-Merge Checklist

```bash
cd /Users/cyonsun/Documents/Code/sunnypilot

# 1. All three repos clean (an untracked `prebuilt` in the parent is normal)
git status --short
git -C opendbc_repo status --short
git -C panda status --short

# 2. Dated backup branches — these are the recovery point
DATE=$(date +%Y%m%d)
git branch -f mazda-port-backup-$DATE HEAD
git -C opendbc_repo branch -f mazda-backup-$DATE HEAD
git -C panda branch -f mazda-backup-$DATE HEAD

# 3. Note the starting SHAs
git rev-parse --short HEAD
git -C opendbc_repo rev-parse --short HEAD
git -C panda rev-parse --short HEAD

# 4. Raise the rename limit BEFORE merging (see "Directory restructures" below)
git config merge.renameLimit 5000
git config diff.renameLimit 5000
```

### Scout the conflict surface before committing to anything

```bash
git fetch --all --prune
MB=$(git merge-base HEAD origin/master)

# How far behind, and how many fork commits are at risk
git rev-list --left-right --count origin/master...HEAD   # left=upstream  right=fork

# Which files both sides touched — this is your real conflict list
comm -12 <(git diff --name-only $MB..HEAD | sort) \
         <(git diff --name-only $MB..origin/master | sort)

# Dry-run the whole merge without touching the worktree
git merge-tree --write-tree HEAD origin/master | head -60
```

`git merge-tree` is the highest-value step here. It prints every conflict
without creating any state to clean up. Use it to decide whether to proceed now
or set aside a longer block of time.

---

## Merge Order

**Submodules first, parent last.** The parent's gitlinks must point at
submodule commits that already exist, otherwise you commit a dangling pointer.

### Step 1: opendbc_repo

Find the upstream target from the parent's `origin/master`, not from the
submodule's own remote — the submodule remote is the fork:

```bash
git ls-tree origin/master opendbc_repo panda    # upstream's expected SHAs

cd opendbc_repo
git fetch --all --prune
git config merge.renameLimit 5000
git checkout mazda-gen2-oplong-lowspeed
git merge --no-ff <upstream-opendbc-sha> \
  -m "Merge upstream sunnypilot/opendbc master (<sha>) into Mazda GEN2 port"
```

### Step 2: panda

```bash
cd ../panda
git fetch --all --prune
git config merge.renameLimit 5000
git checkout mazda-gen2-sync
git merge --no-ff <upstream-panda-sha> \
  -m "Merge upstream sunnypilot/panda master (<sha>) into Mazda GEN2"
```

Conflicts here are rare. The only fork changes are `FLAG_MAZDA_GEN2 = 2` /
`FLAG_MAZDA_TORQUE_INTERCEPTOR = 8` in `python/__init__.py` and the
`case SAFETY_MAZDA:` block in `board/main.c`.

### Step 3: parent

```bash
cd ..
git merge --no-ff --no-commit origin/master
```

`--no-commit` lets you inspect and fix everything before anything is recorded.
Resolve conflicts (recipes below), then point the gitlinks at the **merged**
submodule SHAs:

```bash
git -C opendbc_repo rev-parse HEAD
git -C panda rev-parse HEAD
git add opendbc_repo panda

git submodule sync --recursive
git submodule update --init --recursive
git submodule status          # no line may start with + or -
```

A `+` prefix means the checked-out commit differs from the gitlink. A `-`
means the submodule was never initialised — usually because upstream **moved**
its path (see below).

---

## Directory restructures (the expensive case)

Upstream occasionally moves large parts of the tree. In July 2026, PRs #38219 /
#38220 / #38223 moved `cereal/`, `common/`, `selfdrive/`, `system/`,
`sunnypilot/` and `third_party/` — 1325 files — into a nested `openpilot/`
directory, replacing this fork's `openpilot/` symlink pack.

When that happens:

**Raise `merge.renameLimit` first.** Git's default is 1000. Above that it
silently stops detecting renames, and instead of following your fork's changes
to the new paths it reports every file as delete+add. Set it to 5000 *before*
merging. This one setting is the difference between ~20 conflicts and ~1300.

**Symlink-vs-directory conflicts are expected.** Git reports
`directory in the way of openpilot/common from HEAD; moving it to
openpilot/common~HEAD instead`. Accept upstream's real directories; the fork's
symlinks are obsolete.

**`AU` status = fork-added file that git followed to the new path.** Just
`git add` it — the content is fine, only the location changed.

**Clean up the old tree afterwards.** `git rm` leaves behind untracked
`__pycache__`, stale `.o` / `.a` build artefacts, and submodule worktrees at
the old paths. Stale `.pyc` files at an importable path cause runtime errors
that are very hard to trace back:

```bash
for d in cereal common selfdrive system sunnypilot third_party; do
  [ -e "$d" ] && echo "$d: tracked=$(git ls-files -- $d | wc -l)"
done
# tracked=0 means it is pure leftover — safe to delete
```

**Check for submodules that changed path.** `sunnypilot/neural_network_data`
moved to `openpilot/sunnypilot/neural_network_data`. The old worktree survives
as an untracked directory and the new path stays empty until you re-init. If
left half-migrated, `git submodule update --init --recursive` fails and takes
the device updater down with it.

**Verify no fork change was silently dropped.** Rename detection is good but
not infallible:

```bash
MB=$(git merge-base mazda-port-backup-$DATE origin/master)
git diff --name-only -M $MB mazda-port-backup-$DATE \
  | sed -E 's#^(cereal|common|selfdrive|system|sunnypilot|third_party)/#openpilot/\1/#' \
  | while read f; do
      git cat-file -e "HEAD:$f" 2>/dev/null || [ -e "$f" ] || echo "MISSING: $f"
    done
```

Investigate every hit. Some are legitimate — a file the fork deliberately
deleted that upstream also deleted, or a file upstream renamed across
directories (`system/version.py` → `common/version.py`) that the sed above does
not cover.

---

## Conflict Resolution Recipes

### i18n wrappers vs upstream rewrites (the common case)

Most parent-repo conflicts are this shape: the fork wrapped a string in
`tr()` / `tr_noop()`, and upstream changed the surrounding code. **Take both** —
upstream's logic plus the fork's wrapper. Do not pick a side.

Example from the 2026.003.000 merge — upstream added driver-monitoring lockout
minutes, the fork had wrapped the old string:

```python
# Fork side:     NoEntryAlert(tr_noop("Distraction Level Too High"))
# Upstream side: NoEntryAlert("Too Distracted", f"{mins_left} minute{...} Left", ...)
# Resolution:    upstream's structure, fork's i18n, fork's plural convention
return NoEntryAlert(tr_noop("Too Distracted"),
                    tr("{count} minute(s) Left").format(count=mins_left),
                    priority=Priority.HIGH)
```

Match the existing plural convention (`{count} second(s) remaining...`), not
Python f-string pluralisation.

**Any new `tr()` / `tr_noop()` string must be regenerated into the catalogue**,
or it silently falls back to English at runtime:

```bash
python openpilot/selfdrive/ui/translations/update_translations.py
```

This regenerator also wants to inject hundreds of empty sunnypilot/mici entries
into the 11 upstream language files, because this fork widens the extraction
scope. Revert those — only `app.pot` and `app_zh-CHS.po` are fork-maintained:

```bash
git checkout -- openpilot/selfdrive/ui/translations/app_{de,en,es,fr,ja,ko,pt-BR,th,tr,uk,zh-CHT}.po
```

### `.gitattributes`

Preserve the CJK font LFS opt-out, re-prefixed to any new path. This fork
cannot push to the upstream GitLab LFS server, so the HarmonyOS fonts are
stored as plain git blobs:

```
openpilot/selfdrive/assets/fonts/NotoSansSC-*.otf -filter -diff -merge binary
openpilot/selfdrive/assets/fonts/HarmonyOS_Sans_SC_*.ttf -filter -diff -merge binary
```

### `.gitmodules`

Keep the fork URLs (`conversun/opendbc`, `conversun/panda`), accept upstream's
paths. This usually auto-merges correctly — verify rather than assume.

### `opendbc/car/mazda/values.py`

Preserve:
- the `MAZDA_3_2019 = MazdaPlatformConfig(...)` block
- `MazdaFlags.GEN2 = 2` and `MazdaFlags.TORQUE_INTERCEPTOR = 8`
- `class TI_STATE(IntEnum)` and `apply_ti_steer_torque_limits(...)`
- GEN2-specific `CarControllerParams` (STEER_MAX=8000)

Note `MAZDA_3_2019` currently sets `flags=MazdaFlags.GEN2` only — the
`TORQUE_INTERCEPTOR` flag was deliberately dropped from the platform in
`354ad8405`. The TI code paths remain for other configurations.

### `opendbc/car/mazda/{interface,carstate,carcontroller}.py`

Preserve the GEN2 branches: `_update_gen2`, the `Bus.main`/`Bus.cam`/`Bus.aux`
parser lists, `TI_FEEDBACK` (0x24A) / `EPS_LKAS` (0x249) / `EPS_FEEDBACK`
(0x24B) parsing, the ACC hold/resume timers (50 / 600 / 50 frames), and
`steerActuatorDelay = 0.335`.

### `opendbc/safety/modes/mazda.h`

Preserve `MAZDA_2019_TX_MSGS[]` (`{0x249, 1}`, `{0x220, 2}`),
`mazda_2019_rx_checks[]`, and the `mazda_gen2_safety_hooks` /
`mazda_gen2_ti_safety_hooks` structs.

### `opendbc/safety/tests/common.py`

Preserve the sibling-mode skip rule:

```python
if attr.startswith('TestMazdaGen2') and current_test.startswith('TestMazdaGen2'):
    continue
```

### `opendbc/can/dbc.py`

Preserve the `mazda_2019` checksum registration. Currently:

```python
elif dbc_name.startswith(("mazda_2019", "mazda_2023")):
```

---

## Post-Merge Verification

```bash
# 1. No conflict markers survived
git grep -n "^<<<<<<<\|^>>>>>>>" -- . && echo "MARKERS LEFT" || echo "clean"

# 2. Lint — scope is openpilot/ only, matching scripts/lint/lint.sh
uvx ruff check openpilot --quiet
```

Compare the ruff output against a pre-merge baseline before treating anything
as a regression. Run the same command on the backup branch — this fork carries
a handful of long-standing ISC002/E501 findings in its i18n files.

```bash
# 3. Mazda safety suite — the hard gate
cd opendbc_repo
python3 -m pytest opendbc/safety/tests/ -q \
  --rootdir=. --confcutdir=. -o addopts= \
  --ignore=opendbc/safety/tests/misra
```

Last known-good (2026.003.000 merge): **7796 passed, 3200 skipped, 16201
subtests, 0 failed**. `test_mazda.py` alone: 233 passed, 44 skipped.

MISRA mutation tests need `cppcheck`, which is usually not installed locally —
hence `--ignore`. They still must pass in CI.

```bash
# 4. Mazda platform smoke
cd opendbc_repo
PYTHONPATH=. python3 -c "
from opendbc.car.mazda.values import CAR, MazdaFlags, TI_STATE
from opendbc.car.mazda.mazdacan import mazda2019_checksum
from opendbc.can.dbc import get_checksum_state
flags = CAR.MAZDA_3_2019.config.flags
assert flags & MazdaFlags.GEN2, hex(flags)
assert get_checksum_state('mazda_2019') is not None
assert mazda2019_checksum(0x220, None, bytearray([1,2,3,4,5,6,7])) == 0x46
assert mazda2019_checksum(0x249, None, bytearray([0]*7)) == 0x53
print('OK flags=', hex(flags))
"
# Expect: OK flags= 0x2
```

### Python environment caveat

Upstream moved native dependencies to PyPI `comma-deps-*` wheels, published
only for linux and **macOS arm64**. On an Intel Mac `uv sync` fails outright.
Workaround for running the safety tests:

```bash
uv venv /tmp/sv --python 3.12
VIRTUAL_ENV=/tmp/sv uv pip install numpy cffi scons pytest pycapnp
PATH=/tmp/sv/bin:$PATH VIRTUAL_ENV=/tmp/sv /tmp/sv/bin/python -m pytest ...
```

On the device, the interpreter is `/usr/local/venv/bin/python3` — **not** the
system `python3` and not a repo-local `.venv`. Testing device code with the
wrong interpreter produces bogus `ModuleNotFoundError`s.

---

## Pushing

Push submodules before the parent, or the gitlinks dangle.

The `gh` OAuth token typically lacks the `workflow` scope, so an upstream merge
that touches `.github/workflows/` gets rejected over HTTPS. The submodule
remotes are HTTPS by default — push them over SSH instead:

```bash
git -C opendbc_repo push git@github.com:conversun/opendbc.git mazda-gen2-oplong-lowspeed
git -C panda push git@github.com:conversun/panda.git mazda-gen2-sync
git push conversun mazda-port
```

If the parent push fails with `git@gitlab.com: Permission denied (publickey)`,
that is git-lfs trying to upload upstream's new LFS objects to the sunnypilot
GitLab LFS server, which this fork cannot write to. The objects already exist
upstream, so skip the hook:

```bash
git push --no-verify conversun mazda-port
```

---

## Device update after a large merge

A merge that restructures directories or bumps AGNOS will **not** install
cleanly through the normal updater. The device runs the *old* `updated.py`
against the *new* code tree it just fetched, and old code cannot find files
that moved.

### Symptoms and causes

| Symptom | Cause |
|---------|-------|
| `LastUpdateException: No such file or directory: .../system/hardware/tici/agnos.json` | Old `updated.py` looks in the old path; upstream moved it to `openpilot/common/hardware/tici/agnos.json` |
| Log stops at `git reset in progress`, no traceback, process respawns | Stale `.git/index.lock` in the overlay — every `git reset` exits 128 instantly |
| `git submodule update --init --recursive` hangs or fails | A submodule changed path; old worktree left behind, new path empty |
| `/data/openpilot has been modified, skipping overlay update installation` | `launch_chffrplus.sh` runs `find .git -newer .overlay_init`; **any** git operation on the device trips this |

### The escape hatch: reset the device directly

The overlay exists to protect against a power cut *during download*. Once the
code is downloaded and verified, it buys nothing — and the `.overlay_init`
timestamp check turns into a race you cannot win, because `updated` refreshes
that file on its own schedule.

Just reset the worktree:

```bash
ssh comma@<device-ip>

sudo systemctl stop comma
sudo pkill -9 -f "manager.py|system.updated|selfdrive\."
sudo tmux kill-server
sudo umount -l /data/safe_staging/merged
sudo rm -rf /data/safe_staging

cd /data/openpilot
git fetch origin mazda-port
git reset --hard <target-sha>

# Delete old-layout leftovers — stale .pyc and .o files break the rebuild
for d in cereal common selfdrive system sunnypilot third_party; do
  [ -e "$d" ] && rm -rf "$d"
done

git submodule sync --recursive
git submodule update --init --recursive
git submodule status         # no + or - prefixes

rm -f prebuilt               # force a full rebuild
sudo systemctl start comma
```

The device reboots once on its own if the AGNOS slot changed. First boot after
this takes 10-20 minutes to compile. `prebuilt` and `/data/safe_staging`
reappearing afterwards is correct — `build.py` writes the first, `updated`
rebuilds the second against the new layout.

### Verify

```bash
cat /VERSION                                    # AGNOS version
cd /data/openpilot && git rev-parse --short HEAD
cat /data/params/d/UpdaterCurrentDescription
pgrep -af "openpilot\."                         # processes on new module paths
```

### If AGNOS needs flashing separately

The AGNOS image is sparse and streams straight to the inactive slot, so it does
not consume `/data`. To flash it by hand without the updater:

```python
# /usr/local/venv/bin/python3, PYTHONPATH=/data/openpilot
from openpilot.common.hardware.tici.agnos import (
    flash_agnos_update, get_target_slot_number, verify_agnos_update)
mp = "/data/safe_staging/merged/openpilot/common/hardware/tici/agnos.json"
slot = get_target_slot_number()
flash_agnos_update(mp, slot, log)
verify_agnos_update(mp, slot)   # must be True
```

Run it under `setsid` — a plain `nohup` over SSH gets reaped when the session
closes. Once flashed it stays flashed; `verify_agnos_update` tells you whether
a re-flash is actually needed before spending 4.7 GB again.

---

## After a Successful Merge

1. Tag the recovery point in all three repos:

   ```bash
   DATE=$(date +%Y%m%d)
   git -C opendbc_repo tag -a mazda-merge-$DATE -m "post-merge onto upstream $DATE"
   git -C panda tag -a mazda-merge-$DATE -m "post-merge onto upstream $DATE"
   git tag -a mazda-merge-$DATE -m "post-merge onto upstream $DATE"
   ```

2. Update the stale-path audit in the six `AGENTS.md` files if upstream moved
   directories. Every `file://` link must resolve:

   ```bash
   for f in AGENTS.md openpilot/{selfdrive,system,sunnypilot}/AGENTS.md \
            openpilot/sunnypilot/{sunnylink,selfdrive/controls/lib}/AGENTS.md; do
     grep -o 'file:///Users/[^)#]*' "$f" | sed 's#file://##' | sort -u \
       | while read p; do [ -e "$p" ] || echo "MISSING [$f]: $p"; done
   done
   ```

3. Run CP-A from `T21_onvehicle_bringup_checklist.md` before returning to daily
   use. A new upstream driving model can change lateral feel even when the
   Mazda code is untouched.

4. If the new World Model oscillates, reduce `a` in `NON_LINEAR_TORQUE_PARAMS`
   (currently 4.6) by 10-15%.

---

## When it all goes wrong

```
Merge conflict in opendbc_repo?
  -> In opendbc/car/mazda/ or opendbc/safety/modes/mazda.h?
       YES -> conflict recipes above; preserve GEN2 additions
       NO  -> take upstream

Conflict in the parent?
  -> Submodule gitlink?      -> git add opendbc_repo panda
  -> tr()/tr_noop() vs upstream rewrite? -> take BOTH sides
  -> symlink vs directory?   -> take upstream's directory
  -> in docs/migration/?     -> keep ours

Safety tests fail beyond the expected skips?
  -> test_tx_hook_on_wrong_safety_mode: the T18b skip rule in common.py was lost
  -> other GEN2 tests: check mazda.h TX_MSGS / rx_checks

Want to start over?
  -> git merge --abort
  -> git reset --hard mazda-backup-<date>   (the branches from the checklist)
```

---

*Rewritten after the 2026.003.000 merge (upstream's 1325-file `openpilot/`
restructure). Recovery points are dated `mazda-*-backup-<date>` branches, not
tags.*
