# zh-CHS Font Fix + Translation Coverage — Master Plan

**Branch:** `mazda-port` (current)
**Scope:** sunnypilot fork — Simplified Chinese (zh-CHS) UI improvements
**Symptom:** zh-CHS text renders as bitmap/dot-matrix (16px GNU Unifont). Translation coverage incomplete.

---

## Problem Statement

### A. Font issue

- UI is **raylib** (Python via `pyray`), not Qt. Translations are gettext `.po`, not `.ts`.
- For `UNIFONT_LANGUAGES = {th, zh-CHT, zh-CHS, ko, ja}`, `font_fallback()` in [`system/ui/lib/application.py`](file:///Users/cyonsun/Documents/Code/sunnypilot/system/ui/lib/application.py#L113-L117) replaces every font with `unifont.fnt`.
- `unifont.otf` is rasterized at **16 px** in [`selfdrive/assets/fonts/process.py`](file:///Users/cyonsun/Documents/Code/sunnypilot/selfdrive/assets/fonts/process.py#L92-L94) (intentional upstream choice — PRs #36430, #36508).
- → Chinese characters appear as 16×16 bitmap glyphs (the "dot-matrix" look).

### B. Translation coverage

- `selfdrive/ui/translations/app_zh-CHS.po`: **186/212 translated (87.7%)**, 26 untranslated strings.
- `selfdrive/ui/translations/update_translations.py` only scans `system/ui/`, `selfdrive/ui/{widgets,layouts,onroad}`.
- It MISSES `selfdrive/ui/sunnypilot/` (74 .py, 33 with `tr()`) and `selfdrive/ui/mici/` (27 .py, 9 with `tr()`).
- **448 `tr()`/`trn()`/`tr_noop()` calls in unscanned dirs** never make it into `app.pot`.

---

## Strategic Decisions (locked by user)

| Decision | Choice |
|---|---|
| CJK font | **Noto Sans SC SubsetOTF Regular + Bold** (SIL OFL 1.1; identical design to Source Han Sans SC; ~8 MB each, curl-able from `notofonts/noto-cjk` repo) |
| Translation scope | **Full**: fix scanner, translate all (~474 zh-CHS strings) |
| Other languages | Leave at current state. New `.pot` entries add empty `msgstr` to other `.po` files (pre-existing gap, not regression) |
| Traditional Chinese | Untouched (zh-CHT keeps current state) |

---

## Architectural Approach

### Font pipeline (high-level data flow)

```
NotoSansSC-{Regular,Bold}.otf  (bundled in repo, ~8 MB each)
         │
         ├── process.py  (build-time)
         │     └── chars from app_zh-CHS.po → cjk_sc char set
         │     └── rasterize @ 100 px (NOT 200 — atlas size constraint per Oracle)
         │     └── NO mipmaps for CJK (treat like UNIFONT)
         │     └── emit NotoSansSC-{Regular,Bold}.{fnt,png}
         │
         ├── application.py (runtime)
         │     ├── FontWeight.CJK_SC_NORMAL / CJK_SC_BOLD added
         │     ├── _load_fonts() loads new atlases
         │     └── _font_weights_by_id: dict[texture.id, FontWeight] (NEW)
         │           ↑ enables font_fallback() to know weight from rl.Font
         │
         └── font_fallback(font)  (called from text_measure, wrap_text, draw_text_ex patch)
               ├── lookup weight from font.texture.id (stable; pyray wraps Font objects)
               ├── if zh-CHS: weight → CJK_SC_FALLBACK_MAP[weight]
               ├── if other UNIFONT_LANGUAGES: → UNIFONT (current behavior)
               └── else: passthrough
```

### Scanner fix

`update_translations.py:14-17` extends the `chain(os.walk(...))` with two more directories. Zero-risk additive change.

---

## Workstream Breakdown

### W1. Noto Sans SC font assets

**Files added:**
- `selfdrive/assets/fonts/NotoSansSC-Regular.otf` (8 331 336 B / ~7.9 MB)
- `selfdrive/assets/fonts/NotoSansSC-Bold.otf` (8 543 168 B / ~8.1 MB)
- `selfdrive/assets/fonts/NotoSansSC-LICENSE` (SIL OFL 1.1, copied from `notofonts/noto-cjk:Sans/LICENSE`)

**Acquisition:** direct curl from `notofonts/noto-cjk` repo `main` branch:
```bash
BASE=https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans
curl -fSL -o selfdrive/assets/fonts/NotoSansSC-Regular.otf "$BASE/SubsetOTF/SC/NotoSansSC-Regular.otf"
curl -fSL -o selfdrive/assets/fonts/NotoSansSC-Bold.otf    "$BASE/SubsetOTF/SC/NotoSansSC-Bold.otf"
curl -fSL -o selfdrive/assets/fonts/NotoSansSC-LICENSE     "$BASE/LICENSE"
```

**Note:** Source Han Sans SC and Noto Sans CJK SC are the SAME font (Adobe + Google co-developed, identical glyph source). NotoSansSC SubsetOTF chosen for: curl-able URLs (no zip), 8 MB vs 16 MB for full pan-CJK, ~17k glyphs covering GB18030.

**QA:** `file selfdrive/assets/fonts/NotoSansSC-Regular.otf` shows `OpenType font data, OTTO`.

---

### W2. process.py extension (font atlas builder)

**File:** [`selfdrive/assets/fonts/process.py`](file:///Users/cyonsun/Documents/Code/sunnypilot/selfdrive/assets/fonts/process.py)

**Changes:**

1. Add `CJK_SC_LANGUAGES = {"zh-CHS"}` after `UNIFONT_LANGUAGES`.
2. Add `CJK_SC_FONT_PREFIX = "NotoSansSC"` constant.
3. Extend `_char_sets()` to compute a third set `cjk_sc` (base + chars from `app_zh-CHS.po` + zh-CHS language name `中文（简体）`).
4. Return `(base_cp, unifont_cp, cjk_sc_cp)`.
5. In `main()`, dispatch char set by font filename:
   - `unifont.*` → unifont_cp (16 px)
   - `NotoSansSC-*` → cjk_sc_cp (100 px)
   - else → base_cp (200 px)
6. Add `font_size` map entry: `"NotoSansSC-Regular.otf": 100, "NotoSansSC-Bold.otf": 100`.

**QA:**
- Run `python3 selfdrive/assets/fonts/process.py` from repo root.
- Verify `NotoSansSC-Regular.fnt`, `NotoSansSC-Regular.png`, `NotoSansSC-Bold.fnt`, `NotoSansSC-Bold.png` appear in `selfdrive/assets/fonts/`.
- Verify `.fnt` `chars count=` matches len(cjk_sc).
- Verify `.png` dimensions are reasonable (≤ 8192×8192; expect ~4096×4096 at 100 px).

---

### W3. FontWeight enum + font load

**File:** [`system/ui/lib/application.py`](file:///Users/cyonsun/Documents/Code/sunnypilot/system/ui/lib/application.py#L99-L110)

**Changes:**

1. Add to `FontWeight` enum:
   ```python
   CJK_SC_NORMAL = "NotoSansSC-Regular.fnt"
   CJK_SC_BOLD = "NotoSansSC-Bold.fnt"
   ```
2. In `GuiApplication.__init__`: add `self._font_weights_by_id: dict[int, FontWeight] = {}`.
3. In `_load_fonts()` (line 689): populate `self._font_weights_by_id[font.texture.id] = font_weight_file` after each load. **Use `font.texture.id`, NOT `id(font)`** — pyray may wrap the Font object.
4. CJK SC fonts: SKIP mipmaps + trilinear (treat like UNIFONT — saves 33% texture memory).

**QA:** Add a debug print at end of `_load_fonts` showing all `_font_weights_by_id` entries; verify 8 entries (NORMAL, MEDIUM, BOLD, SEMI_BOLD, UNIFONT, AUDIOWIDE, CJK_SC_NORMAL, CJK_SC_BOLD). Note: BIG_UI mode has NORMAL=Inter-Regular, non-BIG has NORMAL=Inter-Medium; both produce the same atlas underneath. Map count should match enum cardinality (8) modulo identical filenames.

---

### W4. font_fallback refactor

**File:** [`system/ui/lib/application.py`](file:///Users/cyonsun/Documents/Code/sunnypilot/system/ui/lib/application.py#L113-L117)

**Changes:**

```python
CJK_SC_FALLBACK_MAP: dict[FontWeight, FontWeight] = {
  FontWeight.NORMAL: FontWeight.CJK_SC_NORMAL,
  FontWeight.MEDIUM: FontWeight.CJK_SC_NORMAL,
  FontWeight.ROMAN: FontWeight.CJK_SC_NORMAL,
  FontWeight.DISPLAY_REGULAR: FontWeight.CJK_SC_NORMAL,
  FontWeight.BOLD: FontWeight.CJK_SC_BOLD,
  FontWeight.SEMI_BOLD: FontWeight.CJK_SC_BOLD,
  FontWeight.DISPLAY: FontWeight.CJK_SC_BOLD,
  # AUDIOWIDE/UNIFONT/CJK_SC_*: identity (omit)
}

def font_fallback(font: rl.Font) -> rl.Font:
  """Fall back to a language-appropriate font for CJK languages."""
  weight = gui_app._font_weights_by_id.get(font.texture.id)
  lang = multilang.language

  if lang == "zh-CHS":
    if weight is None:
      return font
    target = CJK_SC_FALLBACK_MAP.get(weight)
    return gui_app.font(target) if target is not None else font

  if multilang.requires_unifont():
    return gui_app.font(FontWeight.UNIFONT)

  return font
```

**Constraints:**
- No signature change (`font_fallback(font: rl.Font) -> rl.Font`) — preserves text_measure, wrap_text, _patch_text_functions call sites unchanged.
- Direct uses of `FontWeight.UNIFONT` (e.g. language selector at [`device.py:93`](file:///Users/cyonsun/Documents/Code/sunnypilot/selfdrive/ui/layouts/settings/device.py#L93), [`torque_settings.py:188`](file:///Users/cyonsun/Documents/Code/sunnypilot/selfdrive/ui/sunnypilot/layouts/settings/steering_sub_layouts/torque_settings.py#L188)) are intentionally untouched — they're cross-language picker UIs that need pan-CJK glyph coverage. UNIFONT remains the right choice there.

**QA:**
- Lang = "en": `font_fallback(Inter)` returns Inter (passthrough).
- Lang = "zh-CHS": `font_fallback(Inter-Medium font)` returns `gui_app.font(CJK_SC_NORMAL)`.
- Lang = "ja": `font_fallback(Inter)` returns `gui_app.font(UNIFONT)` (preserved behavior).
- Lang = "zh-CHS": `font_fallback(unifont)` returns unifont (UNIFONT not in map → identity).

---

### W5. Translation scanner fix

**File:** [`selfdrive/ui/translations/update_translations.py`](file:///Users/cyonsun/Documents/Code/sunnypilot/selfdrive/ui/translations/update_translations.py#L14-L17)

**Change:** Add two `os.walk` calls to the `chain(...)`:

```python
for root, _, filenames in chain(os.walk(SYSTEM_UI_DIR),
                                os.walk(os.path.join(UI_DIR, "widgets")),
                                os.walk(os.path.join(UI_DIR, "layouts")),
                                os.walk(os.path.join(UI_DIR, "onroad")),
                                os.walk(os.path.join(UI_DIR, "sunnypilot")),
                                os.walk(os.path.join(UI_DIR, "mici"))):
```

**QA:** Run script, count msgid entries in `app.pot` before vs after — should grow from 212 by ~300-400 (deduplicated; many tr() calls share strings).

---

### W6. Translation extraction & translation

**Steps:**

1. Run `python3 selfdrive/ui/translations/update_translations.py` from repo root.
2. New `app.pot` contains the union of strings from all scanned dirs.
3. All `app_*.po` files merged — existing translations preserved, new entries added with empty `msgstr`.
4. Translate ALL empty `msgstr` entries in `app_zh-CHS.po`:
   - 26 pre-existing untranslated
   - All newly extracted from sunnypilot/mici dirs
   - Skip plural-form (`msgid_plural`) handling — verify zero plural forms in scope first.
5. Other languages (de, en, es, fr, ja, ko, pt-BR, th, tr, uk, zh-CHT) keep existing translations; new entries remain empty (acceptable).

**Translation quality requirements:**
- Use natural Mainland Mandarin (PRC) phrasing, not Taiwan/HK style.
- Preserve format strings (`{}`, `{:.1f}`, etc.) verbatim in target.
- Preserve HTML tags (`<br>`, `<b>`).
- Technical terms: keep ACC, CAN, GPS, OSM in English. "sunnypilot" stays English (brand name).
- Match existing translation style (compare against translated portions for consistency).

**QA:**
- Re-run `update_translations.py` — should be a no-op for translated entries.
- `awk '/^msgid "/{m=$0} /^msgstr ""$/{if(m!="msgid \"\"") c++} END{print c}' app_zh-CHS.po` → 0 (no untranslated entries left).
- `python3 -c "from openpilot.system.ui.lib.multilang import load_translations; from importlib.resources import files; t,p = load_translations(files('openpilot.selfdrive.ui').joinpath('translations/app_zh-CHS.po')); print('msgstr count:', len(t))"` — prints non-zero and exits 0.

---

### W7. End-to-end verification

**Build verification:**
1. `python3 selfdrive/assets/fonts/process.py` — exit 0; new .fnt/.png present.
2. `python3 -m py_compile system/ui/lib/application.py system/ui/lib/multilang.py selfdrive/assets/fonts/process.py selfdrive/ui/translations/update_translations.py` — exit 0.
3. LSP diagnostics clean on all modified .py files.

**Manual QA (NON-NEGOTIABLE, see ULW mandate):**
4. Launch UI on macOS dev machine: `selfdrive/ui/ui.py` with `LANG=zh-CHS` env (or set `LanguageSetting=main_zh-CHS` param).
5. **Visually verify** zh-CHS text renders with proper Noto Sans SC glyphs (anti-aliased vector outlines, NOT 16×16 bitmap).
6. Verify language selector dialog still renders all 12 language options (cross-language UNIFONT path).
7. Verify English UI unchanged (regression check).
8. Verify ja/ko/zh-CHT still render with unifont (current behavior preserved).

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Atlas dimensions exceed GPU max texture size on AGNOS device | Use 100 px (not 200 px) for NotoSansSC; ~2000 chars at 100 px should fit ~4096×4096. Check actual atlas size after first build. If still too large, drop to 80 px. |
| `font.texture.id` not stable across loads | OpenGL texture IDs are deterministic within a process lifetime. Map built at `_load_fonts()`, used for the same process — safe. |
| Font binary cost (~21 MB added) | Acceptable trade-off; Inter+unifont already total ~10 MB. Total fonts dir ~31 MB, dwarfed by neural network artifacts. |
| Translation regression in non-CJK languages | Only `app_zh-CHS.po` modified; other `.po` files only get empty msgstr appended via `merge_po` — existing translations preserved. |
| Auto-translate produces wrong/inconsistent zh-CHS | Delegate to a translation specialist agent with explicit style guide; manual spot-check critical strings (alerts, settings labels). |
| Macros/format strings broken in translation | Add a sanity check: count `{`, `}`, `<`, `>` chars in msgid vs msgstr — must match. |
| process.py atlas size at high px is huge | NotoSansSC at 100 px (per Oracle); fallback to 80 px if needed. Document trade-off. |

---

## Out-of-Scope (explicitly NOT doing)

- Improving zh-CHT, ja, ko, th rendering — stay on unifont.
- Translating other languages (de, en, es, fr, ja, ko, pt-BR, th, tr, uk).
- Refactoring upstream openpilot UI files outside the font/translation pipeline.
- Changing `auto_translate.sh` (use it later if desired; for now, translate zh-CHS via specialist agent).
- Replacing UNIFONT in language selector or torque settings selector — those need pan-CJK glyphs.

---

## File Manifest (final state)

**New files:**
- `selfdrive/assets/fonts/NotoSansSC-Regular.otf`
- `selfdrive/assets/fonts/NotoSansSC-Bold.otf`
- `selfdrive/assets/fonts/NotoSansSC-LICENSE`

**Generated (gitignored, build artifacts):**
- `selfdrive/assets/fonts/NotoSansSC-Regular.fnt`
- `selfdrive/assets/fonts/NotoSansSC-Regular.png`
- `selfdrive/assets/fonts/NotoSansSC-Bold.fnt`
- `selfdrive/assets/fonts/NotoSansSC-Bold.png`

**Modified:**
- `selfdrive/assets/fonts/process.py` — add CJK SC font handling
- `system/ui/lib/application.py` — extend FontWeight, _font_weights_by_id, refactor font_fallback
- `selfdrive/ui/translations/update_translations.py` — extend scanner
- `selfdrive/ui/translations/app.pot` — regenerated
- `selfdrive/ui/translations/app_zh-CHS.po` — fully translated
- `selfdrive/ui/translations/app_*.po` (other 11 langs) — new empty msgstr entries appended (no quality regression)

---

## Success Criteria

| Criterion | Measurement |
|---|---|
| zh-CHS chars render with Noto Sans SC | Manual visual check on macOS UI launch |
| Other CJK languages unchanged | Manual check zh-CHT, ja, ko render with unifont |
| English UI unchanged | Manual check |
| `app_zh-CHS.po` 100% translated | `awk` count of empty msgstr = 0 |
| Translation extraction covers sunnypilot+mici dirs | `app.pot` msgid count grows by 300+ |
| No type errors | `lsp_diagnostics` clean on modified .py |
| process.py exits 0 | Verified by running |
