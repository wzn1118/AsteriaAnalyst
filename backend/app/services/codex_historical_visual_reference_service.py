from __future__ import annotations

import json
import math
import re
import colorsys
from collections import Counter
from pathlib import Path
from typing import Any


def _pdf_reader(pdf_path: Path) -> Any | None:
    try:
        from pypdf import PdfReader  # type: ignore

        return PdfReader(str(pdf_path))
    except Exception:
        return None


def _page_count(source_path: Path) -> int:
    if source_path.suffix.lower() != ".pdf" or not source_path.exists():
        return 0
    reader = _pdf_reader(source_path)
    if reader is None:
        return 0
    try:
        return len(reader.pages)
    except Exception:
        return 0


def _page_metrics(source_path: Path, *, max_pages: int = 24) -> dict[str, Any]:
    if source_path.suffix.lower() != ".pdf" or not source_path.exists():
        return {
            "page_sizes": [],
            "orientation_counts": {},
            "median_width": 0,
            "median_height": 0,
            "text_density": {},
            "title_footer_rhythm": {},
            "suspected_area_stats": {},
            "keyword_counts": {},
        }
    reader = _pdf_reader(source_path)
    if reader is None:
        return {
            "page_sizes": [],
            "orientation_counts": {},
            "median_width": 0,
            "median_height": 0,
            "text_density": {},
            "title_footer_rhythm": {},
            "suspected_area_stats": {},
            "keyword_counts": {},
        }

    page_sizes: list[dict[str, Any]] = []
    orientation_counts: Counter[str] = Counter()
    text_lengths: list[int] = []
    line_counts: list[int] = []
    chart_like_pages = 0
    table_like_pages = 0
    source_footer_pages = 0
    exhibit_pages = 0
    title_lengths: list[int] = []
    footer_lengths: list[int] = []
    keyword_counter: Counter[str] = Counter()
    pages = list(reader.pages[:max_pages])
    for index, page in enumerate(pages, start=1):
        try:
            box = page.mediabox
            width = float(box.width)
            height = float(box.height)
        except Exception:
            width = 0.0
            height = 0.0
        orientation = "landscape" if width > height else "portrait"
        orientation_counts[orientation] += 1
        page_sizes.append(
            {
                "page": index,
                "width": round(width, 2),
                "height": round(height, 2),
                "orientation": orientation,
            }
        )
        try:
            text = str(page.extract_text() or "")
        except Exception:
            text = ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text_lengths.append(len(text))
        line_counts.append(len(lines))
        first_line = lines[0] if lines else ""
        last_lines = " ".join(lines[-3:]) if lines else ""
        title_lengths.append(len(first_line))
        footer_lengths.append(len(last_lines))
        lower = text.lower()
        for key, patterns in {
            "bcg": ["bcg", "boston consulting group", "quarterly watch"],
            "mckinsey": ["mckinsey", "mckinsey & company", "mckinsey global institute"],
            "yili": ["伊利", "液态奶", "云图"],
            "exhibit": ["exhibit", "figure"],
            "source_footer": ["source:", "sources:", "notes:", "copyright"],
        }.items():
            keyword_counter[key] += sum(1 for pattern in patterns if pattern in lower or pattern in text)
        if re.search(r"\b(exhibit|figure|chart|graph)\b", lower) or len(re.findall(r"%|bps|yoy|cagr", lower)) >= 3:
            chart_like_pages += 1
        if re.search(r"\b(table|matrix|rank|segment|scorecard)\b", lower) or text.count("|") >= 6:
            table_like_pages += 1
        if re.search(r"\b(source|notes?|copyright|confidential)\b", lower):
            source_footer_pages += 1
        if re.search(r"\b(exhibit|figure)\s*\d+", lower):
            exhibit_pages += 1

    widths = sorted(size["width"] for size in page_sizes if size["width"])
    heights = sorted(size["height"] for size in page_sizes if size["height"])
    return {
        "page_sizes": page_sizes,
        "orientation_counts": dict(orientation_counts),
        "median_width": widths[len(widths) // 2] if widths else 0,
        "median_height": heights[len(heights) // 2] if heights else 0,
        "text_density": {
            "sampled_page_count": len(pages),
            "avg_text_chars": round(sum(text_lengths) / max(1, len(text_lengths)), 2),
            "avg_line_count": round(sum(line_counts) / max(1, len(line_counts)), 2),
            "dense_text_page_count": sum(1 for value in text_lengths if value >= 1400),
            "sparse_visual_page_count": sum(1 for value in text_lengths if 0 < value < 600),
        },
        "title_footer_rhythm": {
            "avg_first_line_chars": round(sum(title_lengths) / max(1, len(title_lengths)), 2),
            "avg_last_three_line_chars": round(sum(footer_lengths) / max(1, len(footer_lengths)), 2),
            "source_footer_page_count": source_footer_pages,
            "exhibit_number_page_count": exhibit_pages,
        },
        "suspected_area_stats": {
            "chart_like_page_count": chart_like_pages,
            "table_like_page_count": table_like_pages,
            "text_heavy_page_count": sum(1 for value in text_lengths if value >= 1400),
            "visual_heavy_page_count": sum(1 for value in text_lengths if 0 < value < 700),
        },
        "keyword_counts": dict(keyword_counter),
    }


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    text = str(value or "").strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", text):
        return None
    return int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _mix_hex(color: str, other: str = "#ffffff", ratio: float = 0.72) -> str:
    rgb = _hex_to_rgb(color)
    other_rgb = _hex_to_rgb(other)
    if not rgb or not other_rgb:
        return color
    ratio = max(0.0, min(1.0, ratio))
    mixed = tuple(int(round(rgb[i] * (1.0 - ratio) + other_rgb[i] * ratio)) for i in range(3))
    return _rgb_to_hex(mixed)  # type: ignore[arg-type]


def _color_distance(left: str, right: str) -> float:
    left_rgb = _hex_to_rgb(left)
    right_rgb = _hex_to_rgb(right)
    if not left_rgb or not right_rgb:
        return 0.0
    return math.sqrt(sum((left_rgb[i] - right_rgb[i]) ** 2 for i in range(3)))


def _dedupe_palette(colors: list[str], *, min_distance: float = 34.0, limit: int = 8) -> list[str]:
    selected: list[str] = []
    for color in colors:
        if not _hex_to_rgb(color):
            continue
        if all(_color_distance(color, existing) >= min_distance for existing in selected):
            selected.append(color.lower())
        if len(selected) >= limit:
            break
    return selected


def _palette_roles(accent: str, accents: list[str], role_candidates: list[str]) -> dict[str, Any]:
    accent = accent if _hex_to_rgb(accent) else "#1f5f9f"
    series = _dedupe_palette([accent, *accents, *role_candidates, "#b05738", "#5f7fa8", "#7a6f56"], min_distance=58, limit=8)
    while len(series) < 5:
        series.append(["#1f5f9f", "#63bf43", "#b05738", "#5f7fa8", "#7a6f56"][len(series)])
    warm = [
        color for color in series
        if (rgb := _hex_to_rgb(color))
        and (colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)[0] <= 0.12
             or colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)[0] >= 0.92)
    ]
    secondary = next((color for color in series[1:] if _color_distance(color, accent) >= 42), series[1])
    return {
        "accent": accent,
        "secondary": secondary,
        "positive_delta": accent,
        "negative_delta": warm[0] if warm else series[2],
        "series_palette": series[:6],
        "secondary_palette": series[1:6],
        "table_header_fill": _mix_hex(accent, "#ffffff", 0.72),
        "table_header_strong_fill": _mix_hex(accent, "#ffffff", 0.58),
        "footnote_gray": "#6f7377",
        "palette_source": "pdf_preview_pixels",
    }


def _diverse_role_candidates(counter: Counter[str]) -> list[str]:
    top_common = [color for color, _count in counter.most_common(12)]
    hue_best: dict[int, tuple[int, str]] = {}
    for color, count in counter.items():
        rgb = _hex_to_rgb(color)
        if not rgb:
            continue
        h, s, v = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
        if s < 0.08 or v < 0.18:
            continue
        bucket = int(h * 12) % 12
        score = int(count * (1.0 + s))
        if bucket not in hue_best or score > hue_best[bucket][0]:
            hue_best[bucket] = (score, color)
    by_hue = [color for _score, color in sorted(hue_best.values(), reverse=True)]
    return _dedupe_palette([*top_common, *by_hue], min_distance=48, limit=16)


def _image_palette(preview_paths: list[str], *, max_colors: int = 6) -> dict[str, Any]:
    palette_counter: Counter[str] = Counter()
    accent_counter: Counter[str] = Counter()
    role_counter: Counter[str] = Counter()
    image_samples: list[dict[str, Any]] = []
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return {
            "dominant_palette_hint": ["#ffffff", "#1f5f9f", "#d7e7f2"],
            "image_samples": [],
            "image_analysis_available": False,
        }

    for index, raw_path in enumerate(preview_paths[:6], start=1):
        path = Path(str(raw_path)).expanduser()
        if not path.exists():
            continue
        try:
            image = Image.open(path).convert("RGB")
            width, height = image.size
            small = image.resize((80, 80))
            colors = small.getcolors(maxcolors=6400) or []
            total = sum(count for count, _rgb in colors) or 1
            brightness_values: list[float] = []
            saturation_values: list[float] = []
            for count, rgb in colors:
                r, g, b = rgb
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                saturation = (max(rgb) - min(rgb)) / max(1, max(rgb))
                brightness_values.extend([brightness] * min(count, 16))
                saturation_values.extend([saturation] * min(count, 16))
                quantized = _rgb_to_hex((round(r / 16) * 16, round(g / 16) * 16, round(b / 16) * 16))
                if brightness < 0.96:
                    palette_counter[hex_color] += count
                if 0.18 <= brightness <= 0.88 and saturation >= 0.18:
                    accent_counter[hex_color] += count
                if 0.12 <= brightness <= 0.92 and saturation >= 0.14:
                    role_counter[quantized] += count
            ink_ratio = sum(count for count, rgb in colors if sum(rgb) / 3 < 242) / total
            image_samples.append(
                {
                    "page": index,
                    "path": str(path.resolve()),
                    "width": width,
                    "height": height,
                    "orientation": "landscape" if width > height else "portrait",
                    "ink_ratio": round(float(ink_ratio), 4),
                    "brightness_mean": round(float(sum(brightness_values) / max(1, len(brightness_values))), 4),
                    "saturation_mean": round(float(sum(saturation_values) / max(1, len(saturation_values))), 4),
                }
            )
        except Exception:
            continue
    dominant = [color for color, _count in palette_counter.most_common(max_colors)]
    if not dominant:
        dominant = ["#ffffff", "#1f5f9f", "#d7e7f2"]
    accents = [color for color, _count in accent_counter.most_common(max_colors)]
    if not accents:
        accents = [color for color in dominant if color.lower() != "#ffffff"][:max_colors] or ["#1f5f9f"]
    role_candidates = _diverse_role_candidates(role_counter)
    roles = _palette_roles(accents[0], accents, role_candidates)
    return {
        "dominant_palette_hint": dominant,
        "accent_palette_hint": accents,
        "source_palette_roles": roles,
        "source_role_palette_candidates": _dedupe_palette(role_candidates, limit=12),
        "image_samples": image_samples,
        "image_analysis_available": bool(image_samples),
    }


def _edge_ink_features(preview_paths: list[str]) -> dict[str, Any]:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return {"available": False, "pages": [], "average": {}}

    pages: list[dict[str, Any]] = []
    for index, raw_path in enumerate(preview_paths[:8], start=1):
        path = Path(str(raw_path)).expanduser()
        if not path.exists():
            continue
        try:
            image = Image.open(path).convert("RGB").resize((120, 160))
        except Exception:
            continue
        width, height = image.size
        pixels = image.load()

        def ink_ratio(x0: int, x1: int, y0: int, y1: int) -> float:
            ink = 0
            total = max(1, (x1 - x0) * (y1 - y0))
            for x in range(x0, x1):
                for y in range(y0, y1):
                    r, g, b = pixels[x, y]
                    if (r + g + b) / 3 < 242:
                        ink += 1
            return round(ink / total, 4)

        pages.append(
            {
                "page": index,
                "left_edge_ink_ratio": ink_ratio(0, max(1, width // 12), 0, height),
                "right_edge_ink_ratio": ink_ratio(width - max(1, width // 12), width, 0, height),
                "top_edge_ink_ratio": ink_ratio(0, width, 0, max(1, height // 14)),
                "bottom_edge_ink_ratio": ink_ratio(0, width, height - max(1, height // 14), height),
                "center_ink_ratio": ink_ratio(width // 5, width - width // 5, height // 5, height - height // 5),
            }
        )
    if not pages:
        return {"available": False, "pages": [], "average": {}}
    keys = [key for key in pages[0] if key.endswith("_ink_ratio")]
    average = {
        key: round(sum(float(page.get(key) or 0) for page in pages) / max(1, len(pages)), 4)
        for key in keys
    }
    return {"available": True, "pages": pages, "average": average}


def _clip_ratio(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _norm_box(box: tuple[int, int, int, int] | None, *, width: int, height: int) -> list[float]:
    if box is None or width <= 0 or height <= 0:
        return []
    x0, y0, x1, y1 = box
    return [
        _clip_ratio(x0 / width),
        _clip_ratio(y0 / height),
        _clip_ratio(x1 / width),
        _clip_ratio(y1 / height),
    ]


def _bbox_from_points(points: list[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def _expand_box(
    box: tuple[int, int, int, int] | None,
    *,
    width: int,
    height: int,
    pad_x: int = 4,
    pad_y: int = 4,
) -> tuple[int, int, int, int] | None:
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return max(0, x0 - pad_x), max(0, y0 - pad_y), min(width, x1 + pad_x), min(height, y1 + pad_y)


def _average_region_box(pages: list[dict[str, Any]], key: str) -> list[float]:
    boxes = [list(page.get(key) or []) for page in pages if len(list(page.get(key) or [])) == 4]
    if not boxes:
        return []
    return [round(sum(float(box[index]) for box in boxes) / len(boxes), 4) for index in range(4)]


def _clusters_from_indexes(indexes: list[int], *, max_gap: int = 1) -> list[list[int]]:
    if not indexes:
        return []
    clusters: list[list[int]] = []
    current: list[int] = []
    previous = indexes[0] - max_gap - 2
    for index in sorted(set(indexes)):
        if current and index > previous + max_gap + 1:
            clusters.append(current)
            current = []
        current.append(index)
        previous = index
    if current:
        clusters.append(current)
    return clusters


def _int_box_from_norm(box: list[float], *, width: int, height: int) -> tuple[int, int, int, int] | None:
    if not isinstance(box, list) or len(box) != 4:
        return None
    try:
        x0 = int(max(0, min(width - 1, float(box[0]) * width)))
        y0 = int(max(0, min(height - 1, float(box[1]) * height)))
        x1 = int(max(x0 + 1, min(width, float(box[2]) * width)))
        y1 = int(max(y0 + 1, min(height, float(box[3]) * height)))
    except Exception:
        return None
    return x0, y0, x1, y1


def _visual_region_features(preview_paths: list[str]) -> dict[str, Any]:
    """Infer normalized page regions from rendered PDF preview images.

    The goal is not OCR-level precision. It gives downstream renderers a real
    page skeleton: where the title, main visual, annotation column, narrative
    strip, and footer live in the source PDF.
    """

    try:
        from PIL import Image  # type: ignore
    except Exception:
        return {"available": False, "pages": [], "average_regions": {}, "reason": "missing_pillow"}

    pages: list[dict[str, Any]] = []
    for index, raw_path in enumerate(preview_paths[:8], start=1):
        path = Path(str(raw_path)).expanduser()
        if not path.exists():
            continue
        try:
            image = Image.open(path).convert("RGB")
        except Exception:
            continue
        source_width, source_height = image.size
        if source_width <= 0 or source_height <= 0:
            continue
        target_width = 180 if source_height >= source_width else 240
        target_height = max(80, int(round(target_width * source_height / max(1, source_width))))
        image = image.resize((target_width, target_height))
        width, height = image.size
        pixels = image.load()
        row_ink = [0 for _ in range(height)]
        row_color = [0 for _ in range(height)]
        col_ink = [0 for _ in range(width)]
        col_color = [0 for _ in range(width)]
        ink_points: list[tuple[int, int]] = []
        color_points: list[tuple[int, int]] = []
        strong_points: list[tuple[int, int]] = []

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                saturation = (max(r, g, b) - min(r, g, b)) / max(1, max(r, g, b))
                is_ink = brightness < 0.95
                is_strong = brightness < 0.88
                is_color = saturation >= 0.14 and 0.16 <= brightness <= 0.96
                if is_ink:
                    row_ink[y] += 1
                    col_ink[x] += 1
                    ink_points.append((x, y))
                if is_strong:
                    strong_points.append((x, y))
                if is_color:
                    row_color[y] += 1
                    col_color[x] += 1
                    color_points.append((x, y))

        content_box = _expand_box(_bbox_from_points(ink_points), width=width, height=height, pad_x=2, pad_y=2)
        if content_box is None:
            continue
        x0, y0, x1, y1 = content_box
        mean_row = sum(row_ink) / max(1, height)
        active_threshold = max(1.5, mean_row * 0.42)

        title_bottom = int(min(height * 0.24, max(y0 + height * 0.085, y0 + 12)))
        blank_run = 0
        for y in range(max(0, y0 + 8), min(height, int(height * 0.34))):
            if row_ink[y] <= active_threshold * 0.35:
                blank_run += 1
                if blank_run >= max(3, int(height * 0.012)):
                    title_bottom = max(y0 + 10, y - blank_run + 1)
                    break
            elif blank_run:
                blank_run = 0

        color_box = _bbox_from_points(
            [
                point
                for point in color_points
                if title_bottom <= point[1] <= int(height * 0.78)
            ]
        )
        visual_box = _expand_box(color_box, width=width, height=height, pad_x=5, pad_y=5)
        if visual_box is None or (visual_box[3] - visual_box[1]) < height * 0.08:
            dense_points = [
                point
                for point in strong_points
                if title_bottom <= point[1] <= int(height * 0.72)
                and x0 <= point[0] <= x1
            ]
            visual_box = _expand_box(_bbox_from_points(dense_points), width=width, height=height, pad_x=5, pad_y=5)
        if visual_box is None:
            visual_box = (
                x0,
                max(title_bottom, int(height * 0.18)),
                x1,
                min(int(height * 0.62), y1),
            )
        vx0, vy0, vx1, vy1 = visual_box
        if vy1 <= vy0:
            vy0, vy1 = max(title_bottom, int(height * 0.18)), min(int(height * 0.62), y1)
        visual_box = (vx0, vy0, vx1, vy1)

        footer_rows = [
            y
            for y in range(max(0, int(height * 0.78)), height)
            if row_ink[y] >= active_threshold * 0.38
        ]
        footer_start = max(int(height * 0.88), y1 - max(8, int(height * 0.04)))
        if footer_rows:
            clusters: list[list[int]] = []
            current: list[int] = []
            previous = -10
            for y in footer_rows:
                if current and y > previous + 2:
                    clusters.append(current)
                    current = []
                current.append(y)
                previous = y
            if current:
                clusters.append(current)
            bottom_cluster = clusters[-1]
            # Treat only the bottom note/page-number band as footer. Dense
            # lower commentary above 78-86% should stay in narrative/body.
            footer_start = max(int(height * 0.86), min(bottom_cluster) - max(2, int(height * 0.012)))
        footer_box = (x0, footer_start, x1, min(height, y1 + 1))
        narrative_start = min(max(vy1 + max(3, int(height * 0.012)), int(height * 0.50)), footer_start - 4)
        narrative_box = (x0, narrative_start, x1, max(narrative_start + 1, footer_start))

        right_x0 = int(width * 0.72)
        right_points = [
            point
            for point in ink_points
            if point[0] >= right_x0 and vy0 <= point[1] <= vy1
        ]
        right_box = _expand_box(_bbox_from_points(right_points), width=width, height=height, pad_x=3, pad_y=3)
        left_visual_ink = sum(
            1
            for point in ink_points
            if vx0 <= point[0] < int(width * 0.55) and vy0 <= point[1] <= vy1
        )
        right_visual_ink = len(right_points)
        visual_area = max(1, (vx1 - vx0) * max(1, vy1 - vy0))
        right_annotation_likelihood = min(
            1.0,
            (right_visual_ink / max(1, visual_area * 0.22)) * 0.65
            + (right_visual_ink / max(1, left_visual_ink + right_visual_ink)) * 0.35,
        )
        if right_box is None and right_annotation_likelihood >= 0.16:
            right_box = (right_x0, vy0, x1, vy1)

        ny0, ny1 = narrative_box[1], narrative_box[3]
        mid_x0, mid_x1 = int(width * 0.46), int(width * 0.54)
        left_narrative = sum(1 for point in ink_points if x0 <= point[0] < mid_x0 and ny0 <= point[1] <= ny1)
        center_narrative = sum(1 for point in ink_points if mid_x0 <= point[0] <= mid_x1 and ny0 <= point[1] <= ny1)
        right_narrative = sum(1 for point in ink_points if mid_x1 < point[0] <= x1 and ny0 <= point[1] <= ny1)
        two_column_likelihood = 0.0
        if left_narrative > 0 and right_narrative > 0:
            center_ratio = center_narrative / max(1, left_narrative + right_narrative)
            two_column_likelihood = min(1.0, 0.35 + max(0.0, 0.16 - center_ratio) * 3.0)

        page_payload = {
            "page": index,
            "path": str(path.resolve()),
            "source_width": source_width,
            "source_height": source_height,
            "analysis_width": width,
            "analysis_height": height,
            "content_bbox_norm": _norm_box(content_box, width=width, height=height),
            "title_region_norm": _norm_box((x0, y0, x1, title_bottom), width=width, height=height),
            "primary_visual_region_norm": _norm_box(visual_box, width=width, height=height),
            "right_annotation_region_norm": _norm_box(right_box, width=width, height=height),
            "narrative_region_norm": _norm_box(narrative_box, width=width, height=height),
            "footer_region_norm": _norm_box(footer_box, width=width, height=height),
            "margin_norm": {
                "left": _clip_ratio(x0 / width),
                "right": _clip_ratio(1 - x1 / width),
                "top": _clip_ratio(y0 / height),
                "bottom": _clip_ratio(1 - y1 / height),
            },
            "visual_to_page_height_ratio": _clip_ratio((vy1 - vy0) / height),
            "narrative_to_page_height_ratio": _clip_ratio((narrative_box[3] - narrative_box[1]) / height),
            "right_annotation_column_likelihood": _clip_ratio(right_annotation_likelihood),
            "two_column_narrative_likelihood": _clip_ratio(two_column_likelihood),
            "ink_ratio": _clip_ratio(len(ink_points) / max(1, width * height)),
            "colored_ink_ratio": _clip_ratio(len(color_points) / max(1, width * height)),
        }
        pages.append(page_payload)

    if not pages:
        return {"available": False, "pages": [], "average_regions": {}, "reason": "no_preview_pages"}

    # Cover/TOC pages often have very different vertical rhythms. For the
    # reusable content-page contract, prefer body exhibit pages when enough
    # preview pages are available.
    content_region_pages = pages[2:] if len(pages) >= 4 else pages
    margin_keys = ["left", "right", "top", "bottom"]
    average_margin = {
        key: round(sum(float((page.get("margin_norm") or {}).get(key) or 0) for page in content_region_pages) / max(1, len(content_region_pages)), 4)
        for key in margin_keys
    }
    avg_right_annotation = sum(float(page.get("right_annotation_column_likelihood") or 0) for page in content_region_pages) / max(1, len(content_region_pages))
    avg_two_column = sum(float(page.get("two_column_narrative_likelihood") or 0) for page in content_region_pages) / max(1, len(content_region_pages))
    average_regions = {
        "content_bbox_norm": _average_region_box(content_region_pages, "content_bbox_norm"),
        "title_region_norm": _average_region_box(content_region_pages, "title_region_norm"),
        "primary_visual_region_norm": _average_region_box(content_region_pages, "primary_visual_region_norm"),
        "right_annotation_region_norm": _average_region_box(content_region_pages, "right_annotation_region_norm"),
        "narrative_region_norm": _average_region_box(content_region_pages, "narrative_region_norm"),
        "footer_region_norm": _average_region_box(content_region_pages, "footer_region_norm"),
        "margin_norm": average_margin,
        "primary_visual_height_ratio": round(
            sum(float(page.get("visual_to_page_height_ratio") or 0) for page in content_region_pages) / max(1, len(content_region_pages)),
            4,
        ),
        "narrative_height_ratio": round(
            sum(float(page.get("narrative_to_page_height_ratio") or 0) for page in content_region_pages) / max(1, len(content_region_pages)),
            4,
        ),
        "right_annotation_column_likelihood": _clip_ratio(avg_right_annotation),
        "two_column_narrative_likelihood": _clip_ratio(avg_two_column),
    }
    return {
        "available": True,
        "version": "visual-region-parser-v1",
        "sampled_page_count": len(pages),
        "content_region_sampled_page_count": len(content_region_pages),
        "content_region_page_numbers": [int(page.get("page") or 0) for page in content_region_pages],
        "pages": pages,
        "average_regions": average_regions,
    }


def _visual_primitive_features(preview_paths: list[str], region_features: dict[str, Any]) -> dict[str, Any]:
    """Detect reusable visual primitives inside the source PDF previews.

    Regions answer "where"; primitives answer "what lives there": bar matrix,
    table grid, right-side numeric columns, source-note bands, rule lines, and
    typography scale. This gives later stages a visual grammar without relying
    on a hard-coded report family.
    """

    try:
        from PIL import Image  # type: ignore
    except Exception:
        return {"available": False, "pages": [], "average_primitives": {}, "reason": "missing_pillow"}

    region_pages = {
        int(page.get("page") or 0): page
        for page in list(region_features.get("pages") or [])
        if isinstance(page, dict)
    }
    average_regions = dict(region_features.get("average_regions") or {})
    pages: list[dict[str, Any]] = []
    for index, raw_path in enumerate(preview_paths[:8], start=1):
        path = Path(str(raw_path)).expanduser()
        if not path.exists():
            continue
        try:
            image = Image.open(path).convert("RGB")
        except Exception:
            continue
        source_width, source_height = image.size
        target_width = 240 if source_height >= source_width else 300
        target_height = max(90, int(round(target_width * source_height / max(1, source_width))))
        image = image.resize((target_width, target_height))
        width, height = image.size
        pixels = image.load()
        page_region = region_pages.get(index) or {}

        def region_box(key: str, fallback: list[float]) -> tuple[int, int, int, int]:
            raw_box = list(page_region.get(key) or average_regions.get(key) or fallback)
            parsed = _int_box_from_norm(raw_box, width=width, height=height)
            if parsed is None:
                return _int_box_from_norm(fallback, width=width, height=height) or (0, 0, width, height)
            return parsed

        title_box = region_box("title_region_norm", [0.04, 0.03, 0.96, 0.12])
        visual_box = region_box("primary_visual_region_norm", [0.06, 0.18, 0.94, 0.62])
        right_box = region_box("right_annotation_region_norm", [0.72, 0.18, 0.95, 0.62])
        narrative_box = region_box("narrative_region_norm", [0.06, 0.62, 0.94, 0.9])
        footer_box = region_box("footer_region_norm", [0.06, 0.9, 0.94, 0.97])

        row_ink = [0 for _ in range(height)]
        row_color = [0 for _ in range(height)]
        col_ink = [0 for _ in range(width)]
        col_color = [0 for _ in range(width)]
        visual_row_color = [0 for _ in range(height)]
        visual_row_ink = [0 for _ in range(height)]
        visual_col_ink = [0 for _ in range(width)]
        visual_col_color = [0 for _ in range(width)]
        title_ink_points: list[tuple[int, int]] = []

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                saturation = (max(r, g, b) - min(r, g, b)) / max(1, max(r, g, b))
                is_ink = brightness < 0.94
                is_dark = brightness < 0.82
                is_color = saturation >= 0.16 and 0.14 <= brightness <= 0.95
                if is_ink:
                    row_ink[y] += 1
                    col_ink[x] += 1
                    if visual_box[0] <= x < visual_box[2] and visual_box[1] <= y < visual_box[3]:
                        visual_row_ink[y] += 1
                        visual_col_ink[x] += 1
                    if title_box[0] <= x < title_box[2] and title_box[1] <= y < title_box[3] and is_dark:
                        title_ink_points.append((x, y))
                if is_color:
                    row_color[y] += 1
                    col_color[x] += 1
                    if visual_box[0] <= x < visual_box[2] and visual_box[1] <= y < visual_box[3]:
                        visual_row_color[y] += 1
                        visual_col_color[x] += 1
                if is_dark and visual_box[0] <= x < visual_box[2] and visual_box[1] <= y < visual_box[3]:
                    visual_row_ink[y] += 1
                    visual_col_ink[x] += 1

        visual_width = max(1, visual_box[2] - visual_box[0])
        visual_height = max(1, visual_box[3] - visual_box[1])
        visual_color_rows = [
            y
            for y in range(visual_box[1], visual_box[3])
            if visual_row_color[y] >= max(4, int(visual_width * 0.06))
        ]
        bar_clusters = _clusters_from_indexes(visual_color_rows, max_gap=1)
        bar_clusters = [cluster for cluster in bar_clusters if len(cluster) >= 2]
        bar_centers = [(cluster[0] + cluster[-1]) / 2 for cluster in bar_clusters]
        bar_gaps = [bar_centers[i + 1] - bar_centers[i] for i in range(len(bar_centers) - 1)]
        small_pair_gaps = [gap for gap in bar_gaps if 3 <= gap <= max(9, visual_height * 0.08)]
        bar_cluster_count = len(bar_clusters)
        horizontal_bar_likelihood = min(
            1.0,
            (bar_cluster_count / 8) * 0.55
            + (sum(visual_row_color[y] for y in visual_color_rows) / max(1, len(visual_color_rows) * visual_width)) * 0.45
            if visual_color_rows
            else 0.0,
        )
        paired_bar_likelihood = min(1.0, len(small_pair_gaps) / max(1, bar_cluster_count // 2)) if bar_cluster_count >= 4 else 0.0

        visual_color_cols = [
            x
            for x in range(visual_box[0], visual_box[2])
            if visual_col_color[x] >= max(3, int(visual_height * 0.05))
        ]
        vertical_bar_clusters = [cluster for cluster in _clusters_from_indexes(visual_color_cols, max_gap=1) if len(cluster) >= 2]
        vertical_bar_likelihood = min(
            1.0,
            (len(vertical_bar_clusters) / 8) * 0.52
            + (
                sum(visual_col_color[x] for x in visual_color_cols) / max(1, len(visual_color_cols) * visual_height) * 0.48
                if visual_color_cols
                else 0.0
            ),
        )

        visual_ink_rows = [
            y
            for y in range(visual_box[1], visual_box[3])
            if visual_row_ink[y] >= max(8, int(visual_width * 0.35))
        ]
        visual_ink_cols = [
            x
            for x in range(visual_box[0], visual_box[2])
            if visual_col_ink[x] >= max(6, int(visual_height * 0.30))
        ]
        horizontal_rule_clusters = _clusters_from_indexes(visual_ink_rows, max_gap=1)
        vertical_rule_clusters = _clusters_from_indexes(visual_ink_cols, max_gap=1)
        horizontal_rule_count = len([cluster for cluster in horizontal_rule_clusters if len(cluster) <= 4])
        vertical_rule_count = len([cluster for cluster in vertical_rule_clusters if len(cluster) <= 4])
        table_grid_likelihood = min(1.0, (horizontal_rule_count / 8) * 0.55 + (vertical_rule_count / 5) * 0.45)
        bottom_axis_rows = [
            y
            for y in range(max(visual_box[1], visual_box[3] - max(4, visual_height // 8)), visual_box[3])
            if visual_row_ink[y] >= max(8, int(visual_width * 0.35))
        ]
        left_axis_cols = [
            x
            for x in range(visual_box[0], min(visual_box[2], visual_box[0] + max(4, visual_width // 8)))
            if visual_col_ink[x] >= max(6, int(visual_height * 0.28))
        ]
        axis_likelihood = min(
            1.0,
            (len(bottom_axis_rows) / max(1, visual_height * 0.04)) * 0.45
            + (len(left_axis_cols) / max(1, visual_width * 0.04)) * 0.35
            + min(0.2, (horizontal_rule_count + vertical_rule_count) / 24),
        )
        gridline_density = min(1.0, (horizontal_rule_count + vertical_rule_count) / 14)
        colored_area_ratio = sum(visual_row_color[y] for y in range(visual_box[1], visual_box[3])) / max(1, visual_width * visual_height)
        color_row_span = len(visual_color_rows) / max(1, visual_height)
        color_col_span = len(visual_color_cols) / max(1, visual_width)
        line_chart_likelihood = min(
            1.0,
            axis_likelihood * 0.35
            + color_col_span * 0.42
            + color_row_span * 0.23
            - max(horizontal_bar_likelihood, vertical_bar_likelihood) * 0.25,
        )
        coarse_cols = 12
        coarse_rows = 8
        active_cells = 0
        sparse_cells = 0
        for gy in range(coarse_rows):
            y0 = visual_box[1] + int(gy * visual_height / coarse_rows)
            y1 = visual_box[1] + int((gy + 1) * visual_height / coarse_rows)
            for gx in range(coarse_cols):
                x0 = visual_box[0] + int(gx * visual_width / coarse_cols)
                x1 = visual_box[0] + int((gx + 1) * visual_width / coarse_cols)
                total = max(1, (x1 - x0) * (y1 - y0))
                colored = 0
                for yy in range(y0, y1):
                    for xx in range(x0, x1):
                        r, g, b = pixels[xx, yy]
                        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                        saturation = (max(r, g, b) - min(r, g, b)) / max(1, max(r, g, b))
                        if saturation >= 0.16 and 0.14 <= brightness <= 0.95:
                            colored += 1
                density = colored / total
                if density >= 0.012:
                    active_cells += 1
                    if density <= 0.22:
                        sparse_cells += 1
        scatter_likelihood = min(
            1.0,
            (active_cells / max(1, coarse_cols * coarse_rows)) * 1.15
            + (sparse_cells / max(1, active_cells)) * 0.35
            - max(horizontal_bar_likelihood, vertical_bar_likelihood, table_grid_likelihood) * 0.28,
        )
        cx = (visual_box[0] + visual_box[2]) / 2
        cy = (visual_box[1] + visual_box[3]) / 2
        ring_colored = 0
        center_colored = 0
        ring_total = 0
        center_total = 0
        max_radius = min(visual_width, visual_height) / 2
        for y in range(visual_box[1], visual_box[3], 2):
            for x in range(visual_box[0], visual_box[2], 2):
                radius = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max(1, max_radius)
                if radius > 1.0:
                    continue
                r, g, b = pixels[x, y]
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                saturation = (max(r, g, b) - min(r, g, b)) / max(1, max(r, g, b))
                colored = saturation >= 0.16 and 0.14 <= brightness <= 0.95
                if radius <= 0.34:
                    center_total += 1
                    center_colored += 1 if colored else 0
                elif 0.42 <= radius <= 0.92:
                    ring_total += 1
                    ring_colored += 1 if colored else 0
        ring_density = ring_colored / max(1, ring_total)
        center_density = center_colored / max(1, center_total)
        donut_or_pie_likelihood = min(1.0, max(0.0, ring_density * 2.8 - center_density * 1.4))

        right_width = max(1, right_box[2] - right_box[0])
        right_height = max(1, right_box[3] - right_box[1])
        right_ink_rows = [
            y
            for y in range(right_box[1], right_box[3])
            if row_ink[y] >= max(2, int(right_width * 0.03))
        ]
        right_row_clusters = _clusters_from_indexes(right_ink_rows, max_gap=2)
        right_annotation_density = sum(
            1
            for y in range(right_box[1], right_box[3])
            for x in range(right_box[0], right_box[2])
            if sum(pixels[x, y]) / 3 < 240
        ) / max(1, right_width * right_height)
        right_numeric_column_likelihood = min(
            1.0,
            right_annotation_density * 4.0 + min(0.45, len(right_row_clusters) / 14),
        )
        right_color_count = 0
        narrative_color_count = 0
        for y in range(right_box[1], right_box[3]):
            for x in range(right_box[0], right_box[2]):
                r, g, b = pixels[x, y]
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                saturation = (max(r, g, b) - min(r, g, b)) / max(1, max(r, g, b))
                if saturation >= 0.16 and 0.14 <= brightness <= 0.95:
                    right_color_count += 1
        for y in range(narrative_box[1], narrative_box[3]):
            for x in range(narrative_box[0], narrative_box[2]):
                r, g, b = pixels[x, y]
                brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                saturation = (max(r, g, b) - min(r, g, b)) / max(1, max(r, g, b))
                if saturation >= 0.16 and 0.14 <= brightness <= 0.95:
                    narrative_color_count += 1
        narrative_width = max(1, narrative_box[2] - narrative_box[0])
        legend_likelihood = min(
            1.0,
            right_color_count / max(1, right_width * right_height) * 4.5
            + narrative_color_count / max(1, narrative_width * max(1, narrative_box[3] - narrative_box[1])) * 2.2
            + min(0.25, len(right_row_clusters) / 20),
        )

        footer_width = max(1, footer_box[2] - footer_box[0])
        footer_rows = [
            y
            for y in range(footer_box[1], footer_box[3])
            if row_ink[y] >= max(2, int(footer_width * 0.02))
        ]
        footer_line_clusters = _clusters_from_indexes(footer_rows, max_gap=2)
        narrative_rows = [
            y
            for y in range(narrative_box[1], narrative_box[3])
            if row_ink[y] >= max(2, int(narrative_width * 0.02))
        ]
        narrative_line_clusters = _clusters_from_indexes(narrative_rows, max_gap=2)
        title_bbox = _bbox_from_points(title_ink_points)
        title_height_ratio = 0.0
        title_width_ratio = 0.0
        if title_bbox is not None:
            title_height_ratio = (title_bbox[3] - title_bbox[1]) / max(1, title_box[3] - title_box[1])
            title_width_ratio = (title_bbox[2] - title_bbox[0]) / max(1, title_box[2] - title_box[0])

        page_payload = {
            "page": index,
            "path": str(path.resolve()),
            "horizontal_bar_likelihood": _clip_ratio(horizontal_bar_likelihood),
            "paired_bar_likelihood": _clip_ratio(paired_bar_likelihood),
            "vertical_bar_likelihood": _clip_ratio(vertical_bar_likelihood),
            "line_chart_likelihood": _clip_ratio(line_chart_likelihood),
            "scatter_likelihood": _clip_ratio(scatter_likelihood),
            "donut_or_pie_likelihood": _clip_ratio(donut_or_pie_likelihood),
            "axis_likelihood": _clip_ratio(axis_likelihood),
            "legend_likelihood": _clip_ratio(legend_likelihood),
            "gridline_density": _clip_ratio(gridline_density),
            "colored_area_ratio": _clip_ratio(colored_area_ratio),
            "bar_cluster_count": int(bar_cluster_count),
            "bar_pair_gap_median_px": round(sorted(bar_gaps)[len(bar_gaps) // 2], 2) if bar_gaps else 0,
            "table_grid_likelihood": _clip_ratio(table_grid_likelihood),
            "horizontal_rule_count": int(horizontal_rule_count),
            "vertical_rule_count": int(vertical_rule_count),
            "right_numeric_column_likelihood": _clip_ratio(right_numeric_column_likelihood),
            "right_annotation_density": round(right_annotation_density, 4),
            "right_annotation_line_count": int(len(right_row_clusters)),
            "footer_line_count": int(len(footer_line_clusters)),
            "narrative_line_count": int(len(narrative_line_clusters)),
            "title_height_ratio": _clip_ratio(title_height_ratio),
            "title_width_ratio": _clip_ratio(title_width_ratio),
        }
        page_payload["visual_grammar_guess"] = _dominant_chart_grammar(page_payload)
        pages.append(page_payload)

    if not pages:
        return {"available": False, "pages": [], "average_primitives": {}, "reason": "no_preview_pages"}

    content_pages = pages[2:] if len(pages) >= 4 else pages
    numeric_keys = [
        "horizontal_bar_likelihood",
        "paired_bar_likelihood",
        "vertical_bar_likelihood",
        "line_chart_likelihood",
        "scatter_likelihood",
        "donut_or_pie_likelihood",
        "axis_likelihood",
        "legend_likelihood",
        "gridline_density",
        "colored_area_ratio",
        "bar_cluster_count",
        "table_grid_likelihood",
        "horizontal_rule_count",
        "vertical_rule_count",
        "right_numeric_column_likelihood",
        "right_annotation_density",
        "right_annotation_line_count",
        "footer_line_count",
        "narrative_line_count",
        "title_height_ratio",
        "title_width_ratio",
    ]
    average = {
        key: round(sum(float(page.get(key) or 0) for page in content_pages) / max(1, len(content_pages)), 4)
        for key in numeric_keys
    }
    guesses = Counter(str(page.get("visual_grammar_guess") or "") for page in content_pages)
    dominant_grammar = _dominant_chart_grammar(average, guesses)
    chart_grammar_contract = _chart_grammar_contract_from_primitives(average, dominant_grammar)
    return {
        "available": True,
        "version": "visual-primitive-parser-v2",
        "sampled_page_count": len(pages),
        "content_primitive_sampled_page_count": len(content_pages),
        "content_primitive_page_numbers": [int(page.get("page") or 0) for page in content_pages],
        "dominant_visual_grammar": dominant_grammar,
        "chart_grammar_contract": chart_grammar_contract,
        "grammar_counts": dict(guesses),
        "pages": pages,
        "average_primitives": average,
    }


def _box_height(box: Any) -> float:
    if not isinstance(box, list) or len(box) != 4:
        return 0.0
    try:
        return max(0.0, min(1.0, float(box[3]) - float(box[1])))
    except Exception:
        return 0.0


def _box_width(box: Any) -> float:
    if not isinstance(box, list) or len(box) != 4:
        return 0.0
    try:
        return max(0.0, min(1.0, float(box[2]) - float(box[0])))
    except Exception:
        return 0.0


def _vertical_gap(upper: Any, lower: Any) -> float:
    if not isinstance(upper, list) or len(upper) != 4 or not isinstance(lower, list) or len(lower) != 4:
        return 0.0
    try:
        return max(0.0, min(1.0, float(lower[1]) - float(upper[3])))
    except Exception:
        return 0.0


def _dominant_chart_grammar(average_primitives: dict[str, Any], guesses: Counter[str] | None = None) -> str:
    if guesses:
        guessed = str(guesses.most_common(1)[0][0] if guesses else "").strip()
        if guessed and guessed != "chart_or_text_exhibit":
            return guessed
    scores = {
        "paired_horizontal_bar_matrix": max(
            float(average_primitives.get("paired_bar_likelihood") or 0),
            min(
                1.0,
                float(average_primitives.get("horizontal_bar_likelihood") or 0)
                + float(average_primitives.get("right_numeric_column_likelihood") or 0) * 0.45,
            ),
        ),
        "horizontal_bar_chart": float(average_primitives.get("horizontal_bar_likelihood") or 0),
        "vertical_bar_chart": float(average_primitives.get("vertical_bar_likelihood") or 0),
        "line_chart": float(average_primitives.get("line_chart_likelihood") or 0),
        "scatter_plot": float(average_primitives.get("scatter_likelihood") or 0),
        "table_grid": float(average_primitives.get("table_grid_likelihood") or 0),
        "donut_or_pie": float(average_primitives.get("donut_or_pie_likelihood") or 0),
    }
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score >= 0.28 else "chart_or_text_exhibit"


def _chart_grammar_contract_from_primitives(average_primitives: dict[str, Any], dominant: str) -> dict[str, Any]:
    tokens: list[str] = []
    if float(average_primitives.get("axis_likelihood") or 0) >= 0.35:
        tokens.append("axis_based_exhibit")
    if float(average_primitives.get("legend_likelihood") or 0) >= 0.2:
        tokens.append("legend_or_callout_block")
    if float(average_primitives.get("right_numeric_column_likelihood") or 0) >= 0.22:
        tokens.append("right_numeric_annotation_column")
    if float(average_primitives.get("gridline_density") or 0) >= 0.35:
        tokens.append("visible_grid_or_rule_system")
    if dominant == "paired_horizontal_bar_matrix":
        preferred = ["paired_horizontal_bar", "right_annotation_columns", "table_grid", "heatmap", "bar"]
        avoid = ["decorative_donut", "generic_card_only"]
    elif dominant == "horizontal_bar_chart":
        preferred = ["bar", "paired_horizontal_bar", "pareto", "waterfall_bridge"]
        avoid = ["decorative_donut"]
    elif dominant == "vertical_bar_chart":
        preferred = ["vertical_bar", "histogram", "pareto", "line"]
        avoid = ["decorative_donut"]
    elif dominant == "line_chart":
        preferred = ["line", "indexed_trend", "pareto", "scatter"]
        avoid = ["decorative_donut", "table_grid"]
    elif dominant == "scatter_plot":
        preferred = ["scatter", "scatter_quadrant", "portfolio_matrix", "bubble"]
        avoid = ["decorative_donut"]
    elif dominant == "table_grid":
        preferred = ["table_grid", "heatmap", "matrix", "ranking_table", "paired_horizontal_bar"]
        avoid = ["decorative_donut", "generic_card_only"]
    elif dominant == "donut_or_pie":
        preferred = ["donut", "share_map", "stacked_bar", "pareto"]
        avoid = ["generic_card_only"]
    else:
        preferred = ["bar", "line", "heatmap", "scatter", "matrix"]
        avoid = ["generic_card_only"]
    return {
        "version": "chart-grammar-contract-v1",
        "dominant_chart_grammar": dominant,
        "chart_grammar_tokens": tokens,
        "preferred_chart_kinds": preferred,
        "avoid_chart_kinds": avoid,
        "axis_likelihood": round(float(average_primitives.get("axis_likelihood") or 0), 4),
        "legend_likelihood": round(float(average_primitives.get("legend_likelihood") or 0), 4),
        "gridline_density": round(float(average_primitives.get("gridline_density") or 0), 4),
        "horizontal_bar_likelihood": round(float(average_primitives.get("horizontal_bar_likelihood") or 0), 4),
        "vertical_bar_likelihood": round(float(average_primitives.get("vertical_bar_likelihood") or 0), 4),
        "line_chart_likelihood": round(float(average_primitives.get("line_chart_likelihood") or 0), 4),
        "scatter_likelihood": round(float(average_primitives.get("scatter_likelihood") or 0), 4),
        "donut_or_pie_likelihood": round(float(average_primitives.get("donut_or_pie_likelihood") or 0), 4),
        "right_numeric_column_likelihood": round(float(average_primitives.get("right_numeric_column_likelihood") or 0), 4),
    }


def _layout_harmony_features(
    *,
    page_metrics: dict[str, Any],
    edge_features: dict[str, Any],
    region_features: dict[str, Any],
    primitive_features: dict[str, Any],
    dominant_orientation: str,
) -> dict[str, Any]:
    """Derive page balance, whitespace, gap, and visual/text rhythm rules."""

    average_regions = dict(region_features.get("average_regions") or {})
    average_primitives = dict(primitive_features.get("average_primitives") or {})
    title_box = list(average_regions.get("title_region_norm") or [])
    visual_box = list(average_regions.get("primary_visual_region_norm") or [])
    narrative_box = list(average_regions.get("narrative_region_norm") or [])
    footer_box = list(average_regions.get("footer_region_norm") or [])
    right_box = list(average_regions.get("right_annotation_region_norm") or [])
    margins = dict(average_regions.get("margin_norm") or {})
    region_available = bool(region_features.get("available") and title_box and visual_box and footer_box)

    visual_height = _box_height(visual_box)
    narrative_height = _box_height(narrative_box)
    title_height = _box_height(title_box)
    visual_width = _box_width(visual_box)
    right_width = _box_width(right_box)
    total_body_height = max(0.01, visual_height + narrative_height)
    visual_text_ratio = _clip_ratio(visual_height / total_body_height)
    title_visual_gap = _vertical_gap(title_box, visual_box)
    visual_narrative_gap = _vertical_gap(visual_box, narrative_box)
    footer_clearance = _vertical_gap(narrative_box if narrative_height else visual_box, footer_box)

    left_margin = float(margins.get("left") or 0.06)
    right_margin = float(margins.get("right") or 0.06)
    top_margin = float(margins.get("top") or 0.06)
    bottom_margin = float(margins.get("bottom") or 0.05)
    margin_avg = (left_margin + right_margin + top_margin + bottom_margin) / 4
    margin_mode = "compact" if margin_avg < 0.045 else ("generous" if margin_avg >= 0.09 else "standard")
    left_right_balance = _clip_ratio(1 - min(1.0, abs(left_margin - right_margin) / max(0.01, left_margin + right_margin)))

    avg_text_chars = float((page_metrics.get("text_density") or {}).get("avg_text_chars") or 0)
    avg_line_count = float((page_metrics.get("text_density") or {}).get("avg_line_count") or 0)
    avg_ink = float((edge_features.get("average") or {}).get("center_ink_ratio") or 0)
    primitive_line_count = (
        float(average_primitives.get("horizontal_rule_count") or 0)
        + float(average_primitives.get("vertical_rule_count") or 0)
        + float(average_primitives.get("narrative_line_count") or 0)
        + float(average_primitives.get("footer_line_count") or 0)
    )
    density_score = _clip_ratio(
        (avg_text_chars / 2200) * 0.38
        + (avg_line_count / 80) * 0.22
        + (avg_ink / 0.18) * 0.2
        + (primitive_line_count / 34) * 0.2
    )
    density_mode = "dense" if density_score >= 0.62 else ("sparse" if density_score <= 0.32 else "moderate")

    right_annotation_likelihood = float(average_regions.get("right_annotation_column_likelihood") or 0)
    two_column_likelihood = float(average_regions.get("two_column_narrative_likelihood") or 0)
    if right_annotation_likelihood >= 0.22 or right_width >= 0.16:
        balance_mode = "visual_with_right_annotation"
    elif visual_text_ratio >= 0.68:
        balance_mode = "visual_first"
    elif visual_text_ratio <= 0.48:
        balance_mode = "text_first"
    else:
        balance_mode = "balanced_exhibit"

    recommended_columns = 2 if (right_annotation_likelihood >= 0.18 or two_column_likelihood >= 0.35) else 1
    if dominant_orientation == "portrait" and density_mode == "dense":
        recommended_columns = max(recommended_columns, 2)
    visual_weight = {
        "visual_first": 0.68,
        "text_first": 0.52,
        "visual_with_right_annotation": 0.64,
        "balanced_exhibit": 0.58,
    }.get(balance_mode, 0.58)
    if visual_text_ratio:
        visual_weight = max(0.48, min(0.74, (visual_weight + visual_text_ratio) / 2))
    section_gap_norm = max(0.012, min(0.055, (title_visual_gap + max(visual_narrative_gap, 0.01)) / 2))
    harmony_checks = {
        "has_title_visual_gap": title_visual_gap >= 0.01,
        "has_visual_narrative_gap": visual_narrative_gap >= 0.008 or narrative_height == 0,
        "has_footer_clearance": footer_clearance >= 0.012 or not footer_box,
        "left_right_margin_balanced": left_right_balance >= 0.72,
        "visual_area_not_tiny": visual_height >= 0.24 or visual_width >= 0.55,
    }
    harmony_rules = [
        "keep_title_visual_gap",
        "reserve_footer_clearance",
        "align_title_visual_narrative_to_same_content_edges",
        "avoid_crowding_exhibit_and_commentary",
    ]
    if balance_mode == "visual_with_right_annotation":
        harmony_rules.append("preserve_right_annotation_column")
    if density_mode == "dense":
        harmony_rules.append("use_compact_but_regular_vertical_spacing")
    elif density_mode == "sparse":
        harmony_rules.append("protect_generous_whitespace_and_reduce_card_noise")

    return {
        "available": region_available,
        "version": "layout-harmony-v1",
        "balance_mode": balance_mode,
        "density_mode": density_mode,
        "margin_mode": margin_mode,
        "title_height_ratio": round(title_height, 4),
        "visual_height_ratio": round(visual_height, 4),
        "narrative_height_ratio": round(narrative_height, 4),
        "title_visual_gap_ratio": round(title_visual_gap, 4),
        "visual_narrative_gap_ratio": round(visual_narrative_gap, 4),
        "footer_clearance_ratio": round(footer_clearance, 4),
        "left_right_balance": left_right_balance,
        "white_space_ratio_hint": _clip_ratio(1 - max(avg_ink, 0.0)),
        "density_score": density_score,
        "harmony_score": _clip_ratio(sum(1 for ok in harmony_checks.values() if ok) / max(1, len(harmony_checks))),
        "recommended_content_columns": recommended_columns,
        "recommended_visual_text_ratio": round(visual_weight, 4),
        "recommended_section_gap_ratio": round(section_gap_norm, 4),
        "recommended_page_grid": f"{dominant_orientation}_{balance_mode}_{density_mode}",
        "harmony_checks": harmony_checks,
        "harmony_rules": harmony_rules,
    }


def _build_visual_style_signature(
    *,
    source_path: Path,
    page_count: int,
    page_metrics: dict[str, Any],
    palette: dict[str, Any],
    edge_features: dict[str, Any],
    region_features: dict[str, Any],
    primitive_features: dict[str, Any],
    family_hint: dict[str, Any],
) -> dict[str, Any]:
    orientation_counts = dict(page_metrics.get("orientation_counts") or {})
    dominant_orientation = "landscape" if int(orientation_counts.get("landscape") or 0) > int(orientation_counts.get("portrait") or 0) else "portrait"
    avg_edges = dict(edge_features.get("average") or {})
    left_edge = float(avg_edges.get("left_edge_ink_ratio") or 0)
    center_ink = float(avg_edges.get("center_ink_ratio") or 0)
    bottom_edge = float(avg_edges.get("bottom_edge_ink_ratio") or 0)
    title_footer = dict(page_metrics.get("title_footer_rhythm") or {})
    suspected = dict(page_metrics.get("suspected_area_stats") or {})
    accent = str((palette.get("accent_palette_hint") or palette.get("dominant_palette_hint") or ["#1f5f9f"])[0])
    if accent.lower() in {"#ffffff", "#fefefe", "#fdfdfd"}:
        accent = "#1f5f9f"
    background = "#ffffff"
    samples = list((palette.get("image_samples") or []))
    avg_brightness = sum(float(item.get("brightness_mean") or 1) for item in samples) / max(1, len(samples))
    avg_ink = sum(float(item.get("ink_ratio") or 0) for item in samples) / max(1, len(samples))
    has_side_rail = left_edge >= max(0.08, center_ink * 1.7)
    has_footer_rule = bottom_edge >= 0.015 or int(title_footer.get("source_footer_page_count") or 0) > 0
    exhibit_mode = "numbered_exhibit" if int(title_footer.get("exhibit_number_page_count") or 0) > 0 else "implicit_figures"
    density = "chart_first" if int(suspected.get("chart_like_page_count") or 0) >= max(1, page_count // 3) else "balanced"
    if int(suspected.get("text_heavy_page_count") or 0) >= max(1, page_count // 2):
        density = "text_heavy"
    chart_grammar_mode = "generic_chart_first"
    page_body_structure = "single_visual_or_table"
    if dominant_orientation == "portrait" and exhibit_mode == "numbered_exhibit" and density == "text_heavy":
        chart_grammar_mode = "exhibit_horizontal_bar_matrix"
        page_body_structure = "large_exhibit_then_two_column_commentary"
    average_regions = dict(region_features.get("average_regions") or {})
    if float(average_regions.get("right_annotation_column_likelihood") or 0) >= 0.28:
        chart_grammar_mode = "exhibit_horizontal_bar_matrix"
    if float(average_regions.get("two_column_narrative_likelihood") or 0) >= 0.45:
        page_body_structure = "large_exhibit_then_two_column_commentary"
    average_primitives = dict(primitive_features.get("average_primitives") or {})
    dominant_visual_grammar = str(primitive_features.get("dominant_visual_grammar") or "")
    chart_grammar_contract = dict(primitive_features.get("chart_grammar_contract") or {})
    if dominant_visual_grammar == "paired_horizontal_bar_matrix" or (
        float(average_primitives.get("horizontal_bar_likelihood") or 0) >= 0.42
        and float(average_primitives.get("right_numeric_column_likelihood") or 0) >= 0.25
    ):
        chart_grammar_mode = "exhibit_horizontal_bar_matrix"
    elif dominant_visual_grammar == "table_grid":
        chart_grammar_mode = "table_grid_exhibit"
    elif dominant_visual_grammar == "vertical_bar_chart":
        chart_grammar_mode = "axis_vertical_bar_exhibit"
    elif dominant_visual_grammar == "line_chart":
        chart_grammar_mode = "axis_line_exhibit"
    elif dominant_visual_grammar == "scatter_plot":
        chart_grammar_mode = "scatter_relationship_exhibit"
    elif dominant_visual_grammar == "donut_or_pie":
        chart_grammar_mode = "share_composition_exhibit"
    layout_harmony = _layout_harmony_features(
        page_metrics=page_metrics,
        edge_features=edge_features,
        region_features=region_features,
        primitive_features=primitive_features,
        dominant_orientation=dominant_orientation,
    )
    return {
        "version": "visual-style-signature-v1",
        "source_name": source_path.name,
        "source_page_count": page_count,
        "page_orientation": dominant_orientation,
        "page_size_mode": "a4_landscape" if dominant_orientation == "landscape" else "a4_portrait",
        "background_mode": "white_document" if avg_brightness >= 0.88 else "colored_or_dark_document",
        "ink_density": round(avg_ink, 4),
        "accent_color": accent,
        "dominant_palette": list(palette.get("dominant_palette_hint") or [])[:8],
        "accent_palette": list(palette.get("accent_palette_hint") or [])[:8],
        "source_palette_roles": dict(palette.get("source_palette_roles") or {}),
        "source_role_palette_candidates": list(palette.get("source_role_palette_candidates") or [])[:12],
        "side_rail": {
            "present": bool(has_side_rail),
            "left_edge_ink_ratio": round(left_edge, 4),
            "center_ink_ratio": round(center_ink, 4),
        },
        "footer_system": {
            "present": bool(has_footer_rule),
            "mode": "source_note_page_number" if has_footer_rule else "minimal_page_number",
            "bottom_edge_ink_ratio": round(bottom_edge, 4),
        },
        "exhibit_system": {
            "mode": exhibit_mode,
            "chart_like_page_count": int(suspected.get("chart_like_page_count") or 0),
            "table_like_page_count": int(suspected.get("table_like_page_count") or 0),
            "chart_grammar_mode": chart_grammar_mode,
        },
        "density_system": {
            "mode": density,
            "text_density": dict(page_metrics.get("text_density") or {}),
            "suspected_area_stats": suspected,
            "page_body_structure": page_body_structure,
        },
        "region_system": {
            "available": bool(region_features.get("available")),
            "version": region_features.get("version") or "visual-region-parser-unavailable",
            "sampled_page_count": int(region_features.get("sampled_page_count") or 0),
            "average_regions": average_regions,
        },
        "primitive_system": {
            "available": bool(primitive_features.get("available")),
            "version": primitive_features.get("version") or "visual-primitive-parser-unavailable",
            "sampled_page_count": int(primitive_features.get("sampled_page_count") or 0),
            "dominant_visual_grammar": dominant_visual_grammar,
            "chart_grammar_contract": chart_grammar_contract,
            "grammar_counts": dict(primitive_features.get("grammar_counts") or {}),
            "average_primitives": average_primitives,
        },
        "layout_harmony_system": layout_harmony,
        "weak_family_hint": family_hint.get("historical_report_family_hint"),
        "family_signal_tokens": list(family_hint.get("family_signal_tokens") or []),
    }


def _build_style_transfer_contract(signature: dict[str, Any]) -> dict[str, Any]:
    orientation = str(signature.get("page_orientation") or "landscape")
    source_pages = int(signature.get("source_page_count") or 0)
    accent = str(signature.get("accent_color") or "#1f5f9f")
    palette_roles = dict(signature.get("source_palette_roles") or {})
    series_palette = [
        str(item or "").strip()
        for item in list(palette_roles.get("series_palette") or [])
        if re.fullmatch(r"#[0-9a-fA-F]{6}", str(item or "").strip())
    ]
    secondary_palette = [
        str(item or "").strip()
        for item in list(palette_roles.get("secondary_palette") or [])
        if re.fullmatch(r"#[0-9a-fA-F]{6}", str(item or "").strip())
    ]
    side_rail = bool((signature.get("side_rail") or {}).get("present"))
    footer_mode = str((signature.get("footer_system") or {}).get("mode") or "minimal_page_number")
    exhibit_mode = str((signature.get("exhibit_system") or {}).get("mode") or "implicit_figures")
    chart_grammar_mode = str((signature.get("exhibit_system") or {}).get("chart_grammar_mode") or "generic_chart_first")
    region_system = dict(signature.get("region_system") or {})
    average_regions = dict(region_system.get("average_regions") or {})
    primitive_system = dict(signature.get("primitive_system") or {})
    average_primitives = dict(primitive_system.get("average_primitives") or {})
    chart_grammar_contract = dict(primitive_system.get("chart_grammar_contract") or {})
    layout_harmony = dict(signature.get("layout_harmony_system") or {})
    if orientation == "portrait":
        page = {"orientation": "portrait", "width_mm": 210, "height_mm": 297, "margin_top_mm": 20, "margin_x_mm": 18}
        target_pages = {"min": max(4, min(source_pages or 7, 8)), "max": max(8, min(max(source_pages + 3, 8), 14))}
    else:
        page = {"orientation": "landscape", "width_mm": 297, "height_mm": 210, "margin_top_mm": 18, "margin_x_mm": 20}
        target_pages = {"min": max(8, min(source_pages or 16, 24)), "max": max(14, min(max(source_pages + 8, 18), 60))}
    preferred_chart_families = ["line", "indexed_trend", "grouped_bar", "stacked_bar", "matrix", "scatter"]
    if chart_grammar_mode == "exhibit_horizontal_bar_matrix":
        preferred_chart_families = [
            "paired_horizontal_bar",
            "right_annotation_columns",
            "grouped_bar",
            "indexed_trend",
            "matrix",
            "line",
        ]
    elif chart_grammar_mode == "table_grid_exhibit":
        preferred_chart_families = ["table_grid", "ranking_table", "matrix", "heatmap", "paired_horizontal_bar"]
    if average_regions:
        margins = dict(average_regions.get("margin_norm") or {})
        page["margin_top_mm"] = round(max(8, min(34, float(margins.get("top") or 0.06) * float(page["height_mm"]))), 1)
        page["margin_x_mm"] = round(max(8, min(34, max(float(margins.get("left") or 0.06), float(margins.get("right") or 0.06)) * float(page["width_mm"]))), 1)
    primary_visual_ratio = 0.58 if orientation == "portrait" else 0.68
    if average_regions:
        primary_visual_ratio = max(0.42, min(0.76, float(average_regions.get("primary_visual_height_ratio") or primary_visual_ratio)))
    two_column_likelihood = float(average_regions.get("two_column_narrative_likelihood") or 0)
    right_annotation_likelihood = float(average_regions.get("right_annotation_column_likelihood") or 0)
    region_contract = {
        "available": bool(region_system.get("available")),
        "version": region_system.get("version") or "visual-region-parser-unavailable",
        "average_regions": average_regions,
        "right_annotation_column_likelihood": round(right_annotation_likelihood, 4),
        "two_column_narrative_likelihood": round(two_column_likelihood, 4),
        "title_region_norm": average_regions.get("title_region_norm") or [],
        "primary_visual_region_norm": average_regions.get("primary_visual_region_norm") or [],
        "right_annotation_region_norm": average_regions.get("right_annotation_region_norm") or [],
        "narrative_region_norm": average_regions.get("narrative_region_norm") or [],
        "footer_region_norm": average_regions.get("footer_region_norm") or [],
        "margin_norm": average_regions.get("margin_norm") or {},
    }
    primitive_contract = {
        "available": bool(primitive_system.get("available")),
        "version": primitive_system.get("version") or "visual-primitive-parser-unavailable",
        "dominant_visual_grammar": primitive_system.get("dominant_visual_grammar") or "unknown",
        "chart_grammar_contract": chart_grammar_contract,
        "grammar_counts": dict(primitive_system.get("grammar_counts") or {}),
        "horizontal_bar_likelihood": round(float(average_primitives.get("horizontal_bar_likelihood") or 0), 4),
        "paired_bar_likelihood": round(float(average_primitives.get("paired_bar_likelihood") or 0), 4),
        "vertical_bar_likelihood": round(float(average_primitives.get("vertical_bar_likelihood") or 0), 4),
        "line_chart_likelihood": round(float(average_primitives.get("line_chart_likelihood") or 0), 4),
        "scatter_likelihood": round(float(average_primitives.get("scatter_likelihood") or 0), 4),
        "donut_or_pie_likelihood": round(float(average_primitives.get("donut_or_pie_likelihood") or 0), 4),
        "axis_likelihood": round(float(average_primitives.get("axis_likelihood") or 0), 4),
        "legend_likelihood": round(float(average_primitives.get("legend_likelihood") or 0), 4),
        "gridline_density": round(float(average_primitives.get("gridline_density") or 0), 4),
        "colored_area_ratio": round(float(average_primitives.get("colored_area_ratio") or 0), 4),
        "bar_cluster_count": round(float(average_primitives.get("bar_cluster_count") or 0), 4),
        "table_grid_likelihood": round(float(average_primitives.get("table_grid_likelihood") or 0), 4),
        "right_numeric_column_likelihood": round(float(average_primitives.get("right_numeric_column_likelihood") or 0), 4),
        "right_annotation_line_count": round(float(average_primitives.get("right_annotation_line_count") or 0), 4),
        "footer_line_count": round(float(average_primitives.get("footer_line_count") or 0), 4),
        "narrative_line_count": round(float(average_primitives.get("narrative_line_count") or 0), 4),
        "horizontal_rule_count": round(float(average_primitives.get("horizontal_rule_count") or 0), 4),
        "vertical_rule_count": round(float(average_primitives.get("vertical_rule_count") or 0), 4),
        "title_height_ratio": round(float(average_primitives.get("title_height_ratio") or 0), 4),
        "title_width_ratio": round(float(average_primitives.get("title_width_ratio") or 0), 4),
    }
    recommended_columns = int(layout_harmony.get("recommended_content_columns") or 0)
    if recommended_columns <= 0:
        recommended_columns = 2 if (orientation == "portrait" and two_column_likelihood >= 0.35) else (2 if orientation == "portrait" else 1)
    recommended_visual_text_ratio = float(layout_harmony.get("recommended_visual_text_ratio") or primary_visual_ratio)
    harmony_contract = {
        "available": bool(layout_harmony.get("available")),
        "version": layout_harmony.get("version") or "layout-harmony-unavailable",
        "balance_mode": layout_harmony.get("balance_mode") or "balanced_exhibit",
        "density_mode": layout_harmony.get("density_mode") or ((signature.get("density_system") or {}).get("mode") or "moderate"),
        "margin_mode": layout_harmony.get("margin_mode") or "standard",
        "recommended_content_columns": recommended_columns,
        "recommended_visual_text_ratio": round(max(0.42, min(0.76, recommended_visual_text_ratio)), 4),
        "recommended_section_gap_ratio": round(float(layout_harmony.get("recommended_section_gap_ratio") or 0.025), 4),
        "recommended_page_grid": layout_harmony.get("recommended_page_grid") or f"{orientation}_balanced_exhibit",
        "white_space_ratio_hint": layout_harmony.get("white_space_ratio_hint"),
        "title_visual_gap_ratio": layout_harmony.get("title_visual_gap_ratio"),
        "visual_narrative_gap_ratio": layout_harmony.get("visual_narrative_gap_ratio"),
        "footer_clearance_ratio": layout_harmony.get("footer_clearance_ratio"),
        "left_right_balance": layout_harmony.get("left_right_balance"),
        "harmony_score": layout_harmony.get("harmony_score"),
        "harmony_rules": list(layout_harmony.get("harmony_rules") or []),
        "harmony_checks": dict(layout_harmony.get("harmony_checks") or {}),
    }
    return {
        "version": "style-transfer-contract-v1",
        "page": page,
        "colors": {
            "background": "#ffffff",
            "accent": accent,
            "accent_soft": _mix_hex(accent, "#ffffff", 0.82),
            "text": "#4a4a4a",
            "heading": accent,
            "muted": "#8a8a8a",
            "rule": "#d6d6d6",
            "secondary": palette_roles.get("secondary") or (secondary_palette[0] if secondary_palette else "#f59e0b"),
            "positive_delta": palette_roles.get("positive_delta") or accent,
            "negative_delta": palette_roles.get("negative_delta") or "#b05738",
            "table_header_fill": palette_roles.get("table_header_fill") or _mix_hex(accent, "#ffffff", 0.72),
            "table_header_strong_fill": palette_roles.get("table_header_strong_fill") or _mix_hex(accent, "#ffffff", 0.58),
            "footnote_gray": palette_roles.get("footnote_gray") or "#6f7377",
            "series_palette": series_palette[:6] or [accent, "#f59e0b", "#b05738", "#5f7fa8", "#7a6f56"],
            "secondary_palette": secondary_palette[:6],
            "palette_source": palette_roles.get("palette_source") or "pdf_preview_pixels",
        },
        "furniture": {
            "side_rail": side_rail,
            "footer_mode": footer_mode,
            "exhibit_mode": exhibit_mode,
            "source_note_footer": footer_mode == "source_note_page_number",
            "logo_zone": "reserved_not_copied",
        },
        "layout": {
            "body_columns": recommended_columns,
            "primary_visual_ratio": round(primary_visual_ratio, 4),
            "visual_text_ratio": harmony_contract["recommended_visual_text_ratio"],
            "density_mode": harmony_contract["density_mode"],
            "balance_mode": harmony_contract["balance_mode"],
            "title_style": "answer_first_exhibit" if exhibit_mode == "numbered_exhibit" else "section_headline",
            "target_pages": target_pages,
        },
        "chart_style": {
            "preferred_chart_families": list(chart_grammar_contract.get("preferred_chart_kinds") or preferred_chart_families),
            "preferred_chart_kinds": list(chart_grammar_contract.get("preferred_chart_kinds") or preferred_chart_families),
            "avoid_chart_families_when_possible": ["decorative_donut", "generic_card_only"],
            "avoid_chart_kinds": list(chart_grammar_contract.get("avoid_chart_kinds") or ["decorative_donut", "generic_card_only"]),
            "chart_density_mode": (signature.get("density_system") or {}).get("mode") or "balanced",
            "chart_grammar_mode": chart_grammar_mode,
            "dominant_chart_grammar": chart_grammar_contract.get("dominant_chart_grammar") or primitive_contract.get("dominant_visual_grammar"),
            "chart_grammar_contract": chart_grammar_contract,
            "chart_grammar_tokens": list(chart_grammar_contract.get("chart_grammar_tokens") or []),
            "axis_likelihood": chart_grammar_contract.get("axis_likelihood", primitive_contract.get("axis_likelihood")),
            "legend_likelihood": chart_grammar_contract.get("legend_likelihood", primitive_contract.get("legend_likelihood")),
            "gridline_density": chart_grammar_contract.get("gridline_density", primitive_contract.get("gridline_density")),
            "right_annotation_columns": right_annotation_likelihood >= 0.18 or float(primitive_contract.get("right_numeric_column_likelihood") or 0) >= 0.25,
            "visual_primitive_grammar": primitive_contract.get("dominant_visual_grammar"),
            "table_grid_likelihood": primitive_contract.get("table_grid_likelihood"),
            "paired_bar_likelihood": primitive_contract.get("paired_bar_likelihood"),
            "right_numeric_column_likelihood": primitive_contract.get("right_numeric_column_likelihood"),
            "footer_line_count": primitive_contract.get("footer_line_count"),
        },
        "regions": region_contract,
        "visual_primitives": primitive_contract,
        "layout_harmony": harmony_contract,
    }


def _family_hint(source_path: Path, page_metrics: dict[str, Any], palette: dict[str, Any]) -> dict[str, Any]:
    name = source_path.name.lower()
    page_count = int(page_metrics.get("text_density", {}).get("sampled_page_count") or 0)
    orientation_counts = dict(page_metrics.get("orientation_counts") or {})
    keyword_counts = dict(page_metrics.get("keyword_counts") or {})
    landscape_pages = int(orientation_counts.get("landscape") or 0)
    chart_pages = int(page_metrics.get("suspected_area_stats", {}).get("chart_like_page_count") or 0)
    table_pages = int(page_metrics.get("suspected_area_stats", {}).get("table_like_page_count") or 0)
    tokens: list[str] = []
    if int(keyword_counts.get("mckinsey") or 0) > 0:
        family = "mckinsey_consulting_deck_family"
        tokens.extend(["pyramid_storyline", "answer_first_titles", "consulting_exhibit"])
    elif int(keyword_counts.get("bcg") or 0) > 0:
        family = "mckinsey_consulting_deck_family"
        tokens.extend(["short_consulting_watch", "bcg_quarterly_watch", "white_exhibit_pages", "source_footer", "consulting_exhibit"])
    elif int(keyword_counts.get("yili") or 0) > 0:
        family = "brand_analysis_deck_yili_family"
        tokens.extend(["brand_analysis", "module_dividers", "blue_white_long_deck"])
    elif "mckinsey" in name:
        family = "mckinsey_consulting_deck_family"
        tokens.extend(["pyramid_storyline", "answer_first_titles", "consulting_exhibit"])
    elif "bcg" in name or "quarterly" in name:
        family = "generic_chinese_analysis_deck"
        tokens.extend(["short_consulting_watch", "white_exhibit_pages", "source_footer"])
    elif "yili" in name or "伊利" in source_path.name:
        family = "brand_analysis_deck_yili_family"
        tokens.extend(["brand_analysis", "module_dividers", "blue_white_long_deck"])
    elif landscape_pages >= max(1, page_count // 2) and chart_pages + table_pages >= 2:
        family = "generic_chinese_analysis_deck"
        tokens.extend(["presentation_deck", "exhibit_driven"])
    else:
        family = "management_report_light_blue_family"
        tokens.extend(["management_report", "light_blue_corporate"])
    return {
        "historical_report_family_hint": family,
        "family_signal_tokens": tokens,
        "landscape_ratio": round(landscape_pages / max(1, page_count), 4),
        "chart_table_signal_count": chart_pages + table_pages,
        "palette_available": bool(palette.get("image_analysis_available")),
        "keyword_counts": keyword_counts,
    }


def build_historical_visual_reference_payload(
    *,
    source_path: Path,
    preview_paths: list[str] | None = None,
) -> dict[str, Any]:
    preview_paths = [str(Path(path).expanduser().resolve()) for path in list(preview_paths or [])]
    suffix = source_path.suffix.lower()
    page_count = _page_count(source_path)
    page_metrics = _page_metrics(source_path)
    palette = _image_palette(preview_paths)
    family_hint = _family_hint(source_path, page_metrics, palette)
    edge_features = _edge_ink_features(preview_paths)
    region_features = _visual_region_features(preview_paths)
    primitive_features = _visual_primitive_features(preview_paths, region_features)
    visual_style_signature = _build_visual_style_signature(
        source_path=source_path,
        page_count=page_count,
        page_metrics=page_metrics,
        palette=palette,
        edge_features=edge_features,
        region_features=region_features,
        primitive_features=primitive_features,
        family_hint=family_hint,
    )
    style_transfer_contract = _build_style_transfer_contract(visual_style_signature)
    layout_harmony_features = dict(visual_style_signature.get("layout_harmony_system") or {})
    orientation_counts = dict(page_metrics.get("orientation_counts") or {})
    dominant_orientation = "landscape" if int(orientation_counts.get("landscape") or 0) >= int(orientation_counts.get("portrait") or 0) else "portrait"
    chart_pages = int(page_metrics.get("suspected_area_stats", {}).get("chart_like_page_count") or 0)
    table_pages = int(page_metrics.get("suspected_area_stats", {}).get("table_like_page_count") or 0)
    preview_count = len(preview_paths)
    visual_tokens = [
        "real_pdf_source" if suffix == ".pdf" else "document_source",
        f"{dominant_orientation}_page_system",
        "rendered_pdf_previews" if preview_count else "text_only_reference",
    ]
    visual_tokens.extend(family_hint.get("family_signal_tokens") or [])
    if chart_pages:
        visual_tokens.append("chart_dense_exhibit_rhythm")
    if table_pages:
        visual_tokens.append("table_matrix_pages")
    return {
        "source_name": source_path.name,
        "source_suffix": suffix or ".txt",
        "source_is_real_pdf": suffix == ".pdf",
        "source_page_count": page_count,
        "preview_page_count": preview_count,
        "visual_reverse_source": "rendered_pdf_previews" if suffix == ".pdf" and preview_count else ("pdf_text_and_metadata" if suffix == ".pdf" else "source_document"),
        "preview_image_paths": preview_paths,
        "dominant_palette_hint": palette.get("dominant_palette_hint") or ["#ffffff", "#1f5f9f", "#d7e7f2"],
        "accent_palette_hint": palette.get("accent_palette_hint") or ["#1f5f9f"],
        "source_palette_roles": palette.get("source_palette_roles") or {},
        "source_role_palette_candidates": palette.get("source_role_palette_candidates") or [],
        "page_orientation_summary": {
            "dominant_orientation": dominant_orientation,
            "orientation_counts": orientation_counts,
        },
        "page_size_summary": {
            "median_width": page_metrics.get("median_width") or 0,
            "median_height": page_metrics.get("median_height") or 0,
            "sampled_page_sizes": page_metrics.get("page_sizes") or [],
        },
        "margin_rhythm": {
            "inferred_mode": "wide_presentation_margins" if dominant_orientation == "landscape" else "document_margins",
            "confidence": 0.7 if preview_count else 0.35,
        },
        "title_footer_rhythm": page_metrics.get("title_footer_rhythm") or {},
        "suspected_area_stats": page_metrics.get("suspected_area_stats") or {},
        "keyword_counts": page_metrics.get("keyword_counts") or {},
        "text_density": page_metrics.get("text_density") or {},
        "image_preview_stats": {
            "image_analysis_available": bool(palette.get("image_analysis_available")),
            "samples": palette.get("image_samples") or [],
            "edge_ink_features": edge_features,
            "visual_region_features": region_features,
            "visual_primitive_features": primitive_features,
        },
        "visual_region_features": region_features,
        "visual_primitive_features": primitive_features,
        "layout_harmony_features": layout_harmony_features,
        "visual_style_signature": visual_style_signature,
        "style_transfer_contract": style_transfer_contract,
        "historical_report_family_hint": family_hint.get("historical_report_family_hint"),
        "family_signal_tokens": family_hint.get("family_signal_tokens") or [],
        "visual_style_tokens": sorted(set(str(token) for token in visual_tokens if str(token).strip())),
        "suggested_visual_system": {
            "read_first": "Use this JSON as the primary real-PDF visual reference before reading text.",
            "reverse_targets": [
                "page orientation",
                "page furniture",
                "exhibit rhythm",
                "chart/table density",
                "source/footer rhythm",
                "palette",
                "title/chart/narrative/footer region proportions",
                "chart/table/text primitive grammar",
                "layout harmony: whitespace, visual/text balance, gaps, grid, footer clearance, and alignment rhythm",
            ],
            "do_not_copy": [
                "old facts",
                "old logos",
                "old figures",
                "proprietary brand marks",
            ],
            "fallback_rule": "If image preview analysis is unavailable, rely on PDF page metadata and extracted text density but mark lower visual confidence.",
        },
    }


def write_historical_visual_reference(
    *,
    source_path: Path,
    preview_paths: list[str] | None,
    output_path: Path,
) -> dict[str, Any]:
    payload = build_historical_visual_reference_payload(
        source_path=source_path,
        preview_paths=preview_paths,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload
