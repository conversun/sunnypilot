"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

PRC level-1 administrative divisions for the OSM offline map downloader.

Why this lives here, not in mapd's nation_bounding_boxes.json:
  Upstream pfeiferj/mapd v1.12.0 (the binary sunnypilot ships) only knows about
  countries and US states. There is no built-in concept of a "Chinese province".
  Rather than fork the binary or stand up a custom download menu, we exploit
  mapd v1's existing OSMDownloadBounds escape hatch — when that param is set to
  a single Bounds JSON, mapd downloads exactly that bbox and labels it "CUSTOM".
  See https://github.com/pfeiferj/mapd/blob/v1.12.0/download.go.

So this module is consumed in two places:
  1. selfdrive/ui/sunnypilot/layouts/settings/osm.py — populates the province
     selector dialog when the user picks China as the country.
  2. sunnypilot/mapd/mapd_manager.py — translates the selected province ref
     into an OSMDownloadBounds JSON write right before triggering mapd.

Bounding boxes were sourced from the cn-mazda frogpilot fork's curated
mapd_download_menu.json (each province widened to a generous rectangle that
encloses the OSM admin_level=4 boundary). mapd quantises every bbox to 1°
tiles via GROUP_AREA_BOX_DEGREES, so sub-degree precision here is irrelevant.

Note on Taiwan: mapd's stock nation menu already exposes "TW" as a top-level
country, so it is reachable from the existing Country picker without going
through this list. It is also included here for completeness so users who
think of it as a province can find it under China. The two paths download
slightly different bboxes (the entry below is wider than mapd's stock TW
bbox), but both cover the island; pick whichever fits your mental model.
"""


CHINA_NATION_REF = "CN"


# (ref, display_name, bbox)
# - ref: ISO 3166-2 code suffix (e.g. "BJ" for CN-BJ). Used as TreeNode ref and
#   stored in the OsmStateName param so the existing osm.py UI flow can reuse
#   its state-selection plumbing for provinces.
# - display_name: Simplified Chinese only, per project preference.
# - bbox: covers the province with a ~0.5° safety margin. mapd v1 quantises to
#   1° tiles, so this is intentionally generous.
CHINA_PROVINCES: list[tuple[str, str, dict[str, float]]] = [
  # Direct-administered municipalities
  ("BJ", "北京",   {"min_lon": 115.42, "min_lat": 39.44, "max_lon": 117.50, "max_lat": 41.06}),
  ("TJ", "天津",   {"min_lon": 116.71, "min_lat": 38.55, "max_lon": 118.06, "max_lat": 40.25}),
  ("SH", "上海",   {"min_lon": 120.85, "min_lat": 30.68, "max_lon": 122.20, "max_lat": 31.88}),
  ("CQ", "重庆",   {"min_lon": 105.29, "min_lat": 28.16, "max_lon": 110.20, "max_lat": 32.20}),

  # North China provinces
  ("HE", "河北",   {"min_lon": 113.45, "min_lat": 36.05, "max_lon": 119.85, "max_lat": 42.62}),
  ("SX", "山西",   {"min_lon": 110.22, "min_lat": 34.58, "max_lon": 114.58, "max_lat": 40.74}),

  # Northeast provinces
  ("LN", "辽宁",   {"min_lon": 118.83, "min_lat": 38.72, "max_lon": 125.78, "max_lat": 43.43}),
  ("JL", "吉林",   {"min_lon": 121.63, "min_lat": 40.86, "max_lon": 131.31, "max_lat": 46.30}),
  ("HL", "黑龙江", {"min_lon": 121.18, "min_lat": 43.43, "max_lon": 135.09, "max_lat": 53.56}),

  # East China provinces
  ("JS", "江苏",   {"min_lon": 116.36, "min_lat": 30.76, "max_lon": 121.95, "max_lat": 35.12}),
  ("ZJ", "浙江",   {"min_lon": 118.02, "min_lat": 27.04, "max_lon": 123.00, "max_lat": 31.18}),
  ("AH", "安徽",   {"min_lon": 114.90, "min_lat": 29.41, "max_lon": 119.65, "max_lat": 34.65}),
  ("FJ", "福建",   {"min_lon": 115.84, "min_lat": 23.55, "max_lon": 120.72, "max_lat": 28.32}),
  ("JX", "江西",   {"min_lon": 113.57, "min_lat": 24.49, "max_lon": 118.47, "max_lat": 30.08}),
  ("SD", "山东",   {"min_lon": 114.80, "min_lat": 34.38, "max_lon": 122.71, "max_lat": 38.40}),
  ("TW", "台湾",   {"min_lon": 119.31, "min_lat": 21.90, "max_lon": 122.07, "max_lat": 26.39}),

  # Central China provinces
  ("HA", "河南",   {"min_lon": 110.36, "min_lat": 31.39, "max_lon": 116.65, "max_lat": 36.37}),
  ("HB", "湖北",   {"min_lon": 108.36, "min_lat": 29.03, "max_lon": 116.13, "max_lat": 33.27}),
  ("HN", "湖南",   {"min_lon": 108.78, "min_lat": 24.64, "max_lon": 114.26, "max_lat": 30.13}),

  # South China provinces / SARs
  ("GD", "广东",   {"min_lon": 109.66, "min_lat": 20.21, "max_lon": 117.31, "max_lat": 25.52}),
  ("GX", "广西",   {"min_lon": 104.46, "min_lat": 20.90, "max_lon": 112.06, "max_lat": 26.39}),
  ("HI", "海南",   {"min_lon": 108.62, "min_lat": 17.96, "max_lon": 111.05, "max_lat": 20.16}),
  ("HK", "香港",   {"min_lon": 113.83, "min_lat": 22.15, "max_lon": 114.51, "max_lat": 22.57}),
  ("MO", "澳门",   {"min_lon": 113.52, "min_lat": 22.10, "max_lon": 113.60, "max_lat": 22.22}),

  # Southwest provinces / autonomous region
  ("SC", "四川",   {"min_lon":  97.35, "min_lat": 26.05, "max_lon": 108.55, "max_lat": 34.32}),
  ("GZ", "贵州",   {"min_lon": 103.61, "min_lat": 24.62, "max_lon": 109.62, "max_lat": 29.22}),
  ("YN", "云南",   {"min_lon":  97.53, "min_lat": 21.14, "max_lon": 106.20, "max_lat": 29.23}),
  ("XZ", "西藏",   {"min_lon":  78.40, "min_lat": 26.85, "max_lon":  99.13, "max_lat": 36.50}),

  # Northwest provinces / autonomous regions
  ("SN", "陕西",   {"min_lon": 105.49, "min_lat": 31.71, "max_lon": 111.25, "max_lat": 39.59}),
  ("GS", "甘肃",   {"min_lon":  92.13, "min_lat": 32.59, "max_lon": 108.71, "max_lat": 42.80}),
  ("QH", "青海",   {"min_lon":  89.35, "min_lat": 31.60, "max_lon": 103.07, "max_lat": 39.21}),
  ("NX", "宁夏",   {"min_lon": 104.28, "min_lat": 35.24, "max_lon": 107.66, "max_lat": 39.39}),
  ("XJ", "新疆",   {"min_lon":  73.45, "min_lat": 34.34, "max_lon":  96.40, "max_lat": 49.18}),

  # Inner Mongolia autonomous region
  ("NM", "内蒙古", {"min_lon":  97.17, "min_lat": 37.40, "max_lon": 126.07, "max_lat": 53.34}),
]


_BY_REF: dict[str, tuple[str, dict[str, float]]] = {ref: (name, bbox) for ref, name, bbox in CHINA_PROVINCES}


def get_province_bbox(ref: str) -> dict[str, float] | None:
  """Return the bounding box dict for a province ref, or None if unknown."""
  entry = _BY_REF.get(ref)
  return entry[1] if entry else None


def get_province_name(ref: str) -> str | None:
  """Return the Chinese display name for a province ref, or None if unknown."""
  entry = _BY_REF.get(ref)
  return entry[0] if entry else None
