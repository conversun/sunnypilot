#!/usr/bin/env python3
from pathlib import Path
import json

import pyray as rl

FONT_DIR = Path(__file__).resolve().parent
SELFDRIVE_DIR = FONT_DIR.parents[1]
TRANSLATIONS_DIR = SELFDRIVE_DIR / "ui" / "translations"
LANGUAGES_FILE = TRANSLATIONS_DIR / "languages.json"

GLYPH_PADDING = 6
EXTRA_CHARS = "–‑✓×°§•X⚙✕◀▶✔⌫⇧␣○●↳çêüñ–‑✓×°§•€£¥"
# Languages whose primary atlas is unifont (16 px bitmap GNU Unifont).
# zh-CHS is intentionally NOT here — it has its own HarmonyOS Sans SC atlas; the
# CJK_SC_LANGUAGES branch below still seeds the unifont atlas with zh-CHS chars
# so font_fallback can drop back to unifont for codepoints HarmonyOS Sans SC lacks.
UNIFONT_LANGUAGES = {"th", "zh-CHT", "ko", "ja"}
CJK_SC_LANGUAGES = {"zh-CHS"}
CJK_SC_FONT_PREFIX = "HarmonyOS_Sans_SC"


def _languages():
  if not LANGUAGES_FILE.exists():
    return {}
  with LANGUAGES_FILE.open(encoding="utf-8") as f:
    return json.load(f)


def _gb2312_level_1() -> set[str]:
  """Return the 3 755 GB2312 Level-1 (常用字) chars — covers >99% of modern Chinese."""
  chars: set[str] = set()
  for cp in range(0x4E00, 0xA000):
    ch = chr(cp)
    try:
      enc = ch.encode("gb2312")
    except UnicodeEncodeError:
      continue
    # Level 1 is high byte 0xB0-0xD7 in GB2312 encoding
    if len(enc) == 2 and 0xB0 <= enc[0] <= 0xD7:
      chars.add(ch)
  return chars


# CJK punctuation, kana, halfwidth/fullwidth forms — always wanted in the SC atlas.
_CJK_SC_EXTRA_RANGES = (
  range(0x3000, 0x3040),  # CJK symbols & punctuation
  range(0x3040, 0x30A0),  # Hiragana
  range(0x30A0, 0x3100),  # Katakana
  range(0xFF00, 0xFFF0),  # Halfwidth/Fullwidth forms
)


def _char_sets():
  base = set(map(chr, range(32, 127))) | set(EXTRA_CHARS)
  unifont = set(base)
  cjk_sc = set(base)
  cjk_sc.update(_gb2312_level_1())
  for r in _CJK_SC_EXTRA_RANGES:
    cjk_sc.update(chr(cp) for cp in r)

  for language, code in _languages().items():
    unifont.update(language)
    if code in CJK_SC_LANGUAGES:
      cjk_sc.update(language)
    po_path = TRANSLATIONS_DIR / f"app_{code}.po"
    try:
      chars = set(po_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
      continue
    if code in CJK_SC_LANGUAGES:
      cjk_sc.update(chars)
      unifont.update(chars)
    elif code in UNIFONT_LANGUAGES:
      unifont.update(chars)
    else:
      base.update(chars)

  return (
    tuple(sorted(ord(c) for c in base)),
    tuple(sorted(ord(c) for c in unifont)),
    tuple(sorted(ord(c) for c in cjk_sc)),
  )


def _glyph_metrics(glyphs, rects, glyph_count: int):
  entries = []
  min_offset_y, max_extent = None, 0
  for idx in range(glyph_count):
    glyph = glyphs[idx]
    rect = rects[idx]
    width = int(round(rect.width))
    height = int(round(rect.height))
    offset_y = int(round(glyph.offsetY))
    min_offset_y = offset_y if min_offset_y is None else min(min_offset_y, offset_y)
    max_extent = max(max_extent, offset_y + height)
    entries.append({
      "id": glyph.value,
      "x": int(round(rect.x)),
      "y": int(round(rect.y)),
      "width": width,
      "height": height,
      "xoffset": int(round(glyph.offsetX)),
      "yoffset": offset_y,
      "xadvance": int(round(glyph.advanceX)),
    })

  if min_offset_y is None:
    raise RuntimeError("No glyphs were generated")

  line_height = int(round(max_extent - min_offset_y))
  base = int(round(max_extent))
  return entries, line_height, base


def _write_bmfont(path: Path, font_size: int, face: str, atlas_name: str, line_height: int, base: int, atlas_size, entries):
  # TODO: why doesn't raylib calculate these metrics correctly?
  if line_height != font_size:
    print("using font size for line height", atlas_name)
    line_height = font_size
  lines = [
    f"info face=\"{face}\" size=-{font_size} bold=0 italic=0 charset=\"\" unicode=1 stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=0,0 outline=0",
    f"common lineHeight={line_height} base={base} scaleW={atlas_size[0]} scaleH={atlas_size[1]} pages=1 packed=0 alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4",
    f"page id=0 file=\"{atlas_name}\"",
    f"chars count={len(entries)}",
  ]
  for entry in entries:
    lines.append(
      ("char id={id:<4} x={x:<5} y={y:<5} width={width:<5} height={height:<5} " +
       "xoffset={xoffset:<5} yoffset={yoffset:<5} xadvance={xadvance:<5} page=0  chnl=15").format(**entry)
    )
  path.write_text("\n".join(lines) + "\n")


def _process_font(font_path: Path, codepoints: tuple[int, ...]):
  print(f"Processing {font_path.name}...")

  font_size = {
    "unifont.otf": 16,  # unifont is only 16x8 or 16x16 pixels per glyph
    # HarmonyOS Sans SC at 72px holds the GB2312 Level-1 + kana + halfwidth subset
    # in an 8192x4096 atlas (~33 MB GRAY_ALPHA per weight). 72px (vs NotoSansSC's 80px)
    # compensates for HarmonyOS Sans's larger glyph metrics to keep atlas size parity.
    "HarmonyOS_Sans_SC_Regular.ttf": 72,
    "HarmonyOS_Sans_SC_Bold.ttf": 72,
  }.get(font_path.name, 200)

  data = font_path.read_bytes()
  file_buf = rl.ffi.new("unsigned char[]", data)
  cp_buffer = rl.ffi.new("int[]", codepoints)
  cp_ptr = rl.ffi.cast("int *", cp_buffer)
  glyph_count = rl.ffi.new("int *", len(codepoints))
  glyphs = rl.load_font_data(
    rl.ffi.cast("unsigned char *", file_buf), len(data), font_size, cp_ptr, len(codepoints),
    rl.FontType.FONT_DEFAULT, glyph_count
  )
  if glyphs == rl.ffi.NULL:
    raise RuntimeError("raylib failed to load font data")

  rects_ptr = rl.ffi.new("Rectangle **")
  image = rl.gen_image_font_atlas(glyphs, rects_ptr, glyph_count[0], font_size, GLYPH_PADDING, 0)
  print(f"  {font_path.name}: {len(codepoints)} codepoints → atlas {image.width}x{image.height}")
  if image.width == 0 or image.height == 0:
    raise RuntimeError("raylib returned an empty atlas")

  rects = rects_ptr[0]
  atlas_name = f"{font_path.stem}.png"
  atlas_path = FONT_DIR / atlas_name
  entries, line_height, base = _glyph_metrics(glyphs, rects, glyph_count[0])

  if not rl.export_image(image, atlas_path.as_posix()):
    raise RuntimeError("Failed to export atlas image")

  _write_bmfont(FONT_DIR / f"{font_path.stem}.fnt", font_size, font_path.stem, atlas_name, line_height, base, (image.width, image.height), entries)


def main():
  base_cp, unifont_cp, cjk_sc_cp = _char_sets()
  fonts = sorted(FONT_DIR.glob("*.ttf")) + sorted(FONT_DIR.glob("*.otf"))
  for font in fonts:
    if "emoji" in font.name.lower():
      continue
    if font.stem.lower().startswith("unifont"):
      glyphs = unifont_cp
    elif font.stem.startswith(CJK_SC_FONT_PREFIX):
      glyphs = cjk_sc_cp
    else:
      glyphs = base_cp
    _process_font(font, glyphs)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
