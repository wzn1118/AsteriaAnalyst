from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _render_pdf_pages_for_density(pdf_path: Path, *, max_pages: int = 12) -> list[Path]:
    if not pdf_path.exists():
        return []
    executable = shutil.which("pdftoppm")
    if not executable:
        return []
    temp_root = Path(tempfile.mkdtemp(prefix="historical-density-"))
    prefix = temp_root / "page"
    command = [
        executable,
        "-png",
        "-f",
        "1",
        "-l",
        str(max(1, max_pages)),
        "-r",
        "72",
        str(pdf_path),
        str(prefix),
    ]
    try:
        subprocess.run(command, check=False, capture_output=True, text=True, timeout=60)
    except Exception:
        return []
    return sorted(temp_root.glob("page-*.png"))


def _image_ink_features(image: Any, box_norm: list[float] | None = None) -> dict[str, float]:
    width, height = image.size
    box = _norm_box(box_norm or [])
    if box:
        x0 = max(0, min(width - 1, int(box[0] * width)))
        y0 = max(0, min(height - 1, int(box[1] * height)))
        x1 = max(x0 + 1, min(width, int(box[2] * width)))
        y1 = max(y0 + 1, min(height, int(box[3] * height)))
    else:
        x0, y0, x1, y1 = 0, 0, width, height
    total = max(1, (x1 - x0) * (y1 - y0))
    ink = 0
    colored_ink = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = image.getpixel((x, y))
            brightness = (r + g + b) / 3
            if brightness < 242:
                ink += 1
            if brightness < 248 and max(r, g, b) - min(r, g, b) >= 22 and 35 < max(r, g, b) < 252:
                colored_ink += 1
    return {
        "ink_ratio": round(ink / total, 4),
        "colored_ink_ratio": round(colored_ink / total, 4),
    }


def _source_relative_density_score(generated: float, source: float, *, tolerance: float) -> float:
    if source <= 0:
        return 1.0
    return round(max(0.0, 1.0 - abs(generated - source) / max(0.001, tolerance)), 4)


def _raster_density_scan(workspace: Path, pdf_path: Path, deck_layout: dict[str, Any], html_text: str = "") -> dict[str, Any]:
    pages = [page for page in list(deck_layout.get("pages") or []) if isinstance(page, dict)]
    sections = _sections(html_text) if html_text else []
    rendered_paths = _render_pdf_pages_for_density(pdf_path, max_pages=min(12, max(1, len(pages))))
    if not rendered_paths:
        return {"available": False, "page_density_scores": [], "raster_density_blocking_issues": []}
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return {"available": False, "page_density_scores": [], "raster_density_blocking_issues": []}
    source_profiles = _source_profile_lookup(workspace)
    page_scores: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    source_relative_scores: list[float] = []
    source_relative_color_scores: list[float] = []
    for index, image_path in enumerate(rendered_paths, start=1):
        page = pages[index - 1] if index - 1 < len(pages) else {}
        template = str(page.get("page_template_type") or "")
        if template == "cover_page":
            continue
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            continue
        width, height = image.size
        ink_features = _image_ink_features(image)
        ink_ratio = float(ink_features.get("ink_ratio") or 0)
        colored_ratio = float(ink_features.get("colored_ink_ratio") or 0)
        # Content pages with real exhibit charts/tables should not look like
        # mostly blank canvases. This catches the failure mode that layout boxes
        # match but rendered ink is visually too sparse for a reader.
        min_ink = 0.038 if template in {"thesis_chart_page", "heatmap_leverage_page", "scatter_diagnosis_page"} else 0.032
        if ink_ratio < min_ink:
            issues.append({
                "issue": "raster_ink_density_too_low",
                "page_number": index,
                "template": template,
                "ink_ratio": round(ink_ratio, 4),
                "threshold": min_ink,
                "severity": "blocker",
            })
        page_scores.append({
            "page_number": index,
            "template": template,
            "ink_ratio": round(ink_ratio, 4),
            "colored_ink_ratio": round(colored_ratio, 4),
            "image_path": str(image_path),
            "width": width,
            "height": height,
        })
        section = sections[index - 1] if index - 1 < len(sections) else ""
        visual_region = _primary_visual_ink_score(image, page, section=section)
        if visual_region:
            page_scores[-1]["primary_visual_ink_ratio"] = visual_region["ink_ratio"]
            page_scores[-1]["primary_visual_colored_ink_ratio"] = visual_region["colored_ink_ratio"]
            page_scores[-1]["primary_visual_box_norm"] = visual_region["box_norm"]
            min_visual_ink = 0.028 if template in {"thesis_chart_page", "heatmap_leverage_page", "scatter_diagnosis_page"} else 0.024
            if visual_region["ink_ratio"] < min_visual_ink:
                issues.append({
                    "issue": "primary_visual_region_too_sparse",
                    "page_number": index,
                    "template": template,
                    "ink_ratio": visual_region["ink_ratio"],
                    "threshold": min_visual_ink,
                    "severity": "blocker",
                })
        profile = source_profiles.get(str(page.get("source_region_profile_id") or ""))
        preview_path = Path(str((profile or {}).get("preview_path") or ""))
        if profile and preview_path.exists():
            try:
                source_image = Image.open(preview_path).convert("RGB")
            except Exception:
                source_image = None
            if source_image is not None:
                source_features = _image_ink_features(source_image)
                source_visual_features = _image_ink_features(source_image, _norm_box(profile.get("primary_visual_box_norm")))
                source_ink = float(source_features.get("ink_ratio") or 0)
                source_colored = float(source_features.get("colored_ink_ratio") or 0)
                source_visual_ink = float(source_visual_features.get("ink_ratio") or 0)
                source_visual_colored = float(source_visual_features.get("colored_ink_ratio") or 0)
                page_scores[-1].update(
                    {
                        "matched_source_page_number": int(profile.get("source_page_number") or 0),
                        "source_ink_ratio": round(source_ink, 4),
                        "source_colored_ink_ratio": round(source_colored, 4),
                        "source_primary_visual_ink_ratio": round(source_visual_ink, 4),
                        "source_primary_visual_colored_ink_ratio": round(source_visual_colored, 4),
                        "source_relative_ink_delta": round(abs(ink_ratio - source_ink), 4),
                        "source_relative_colored_ink_delta": round(abs(colored_ratio - source_colored), 4),
                    }
                )
                density_score = _source_relative_density_score(ink_ratio, source_ink, tolerance=0.07)
                color_score = _source_relative_density_score(colored_ratio, source_colored, tolerance=0.035)
                page_scores[-1]["source_relative_density_score"] = density_score
                page_scores[-1]["source_relative_color_score"] = color_score
                source_relative_scores.append(density_score)
                source_relative_color_scores.append(color_score)
                if source_ink - ink_ratio > 0.032:
                    issues.append(
                        {
                            "issue": "source_relative_ink_density_too_low",
                            "page_number": index,
                            "template": template,
                            "generated_ink_ratio": round(ink_ratio, 4),
                            "source_ink_ratio": round(source_ink, 4),
                            "delta": round(source_ink - ink_ratio, 4),
                            "threshold": 0.032,
                            "severity": "blocker",
                        }
                    )
                if abs(colored_ratio - source_colored) > 0.028:
                    issues.append(
                        {
                            "issue": "source_relative_palette_density_mismatch",
                            "page_number": index,
                            "template": template,
                            "generated_colored_ink_ratio": round(colored_ratio, 4),
                            "source_colored_ink_ratio": round(source_colored, 4),
                            "delta": round(abs(colored_ratio - source_colored), 4),
                            "threshold": 0.028,
                            "severity": "blocker",
                        }
                    )
    return {
        "available": True,
        "page_density_scores": page_scores,
        "raster_density_blocking_issues": issues,
        "source_relative_density_score": round(sum(source_relative_scores) / max(1, len(source_relative_scores)), 4) if source_relative_scores else 0.0,
        "source_relative_color_score": round(sum(source_relative_color_scores) / max(1, len(source_relative_color_scores)), 4) if source_relative_color_scores else 0.0,
        "low_raster_density_page_numbers": sorted({
            int(issue.get("page_number") or 0)
            for issue in issues
            if int(issue.get("page_number") or 0) > 0
        }),
    }


def _primary_visual_ink_score(image: Any, page: dict[str, Any], *, section: str = "") -> dict[str, Any]:
    rendered_box = _rendered_primary_visual_box_norm(section)
    if rendered_box:
        primary = rendered_box
    else:
        primary = []
    contract = page.get("region_layout_contract") if isinstance(page.get("region_layout_contract"), dict) else {}
    regions = contract.get("layout_regions") if isinstance(contract.get("layout_regions"), dict) else page.get("layout_regions")
    if not primary:
        if not isinstance(regions, dict):
            return {}
        primary = _norm_box(regions.get("primary_visual"))
    if not primary:
        return {}
    if not rendered_box:
        right = _norm_box(regions.get("right_annotation")) if isinstance(regions, dict) else []
        if right and right[0] > primary[0]:
            primary[2] = min(primary[2], max(primary[0] + 0.1, right[0] - 0.025))
    width, height = image.size
    x0 = max(0, min(width - 1, int(primary[0] * width)))
    y0 = max(0, min(height - 1, int(primary[1] * height)))
    x1 = max(x0 + 1, min(width, int(primary[2] * width)))
    y1 = max(y0 + 1, min(height, int(primary[3] * height)))
    total = max(1, (x1 - x0) * (y1 - y0))
    ink = 0
    colored_ink = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = image.getpixel((x, y))
            brightness = (r + g + b) / 3
            if brightness < 242:
                ink += 1
            if brightness < 248 and max(r, g, b) - min(r, g, b) >= 22 and 35 < max(r, g, b) < 252:
                colored_ink += 1
    return {
        "ink_ratio": round(ink / total, 4),
        "colored_ink_ratio": round(colored_ink / total, 4),
        "box_norm": [round(value, 4) for value in primary],
    }


def _rendered_primary_visual_box_norm(section: str) -> list[float]:
    if not section:
        return []
    style_match = re.search(r"\bstyle=[\"']([^\"']+)[\"']", section)
    if not style_match:
        return []
    style = style_match.group(1)

    def mm_var(name: str) -> float:
        match = re.search(rf"--{re.escape(name)}\s*:\s*([0-9.]+)mm", style)
        if not match:
            return 0.0
        try:
            return float(match.group(1))
        except Exception:
            return 0.0

    width_mm = 210.0
    height_mm = 297.0
    left = mm_var("region-content-left")
    right = mm_var("region-content-right")
    visual_top = mm_var("region-visual-top")
    visual_height = mm_var("region-visual-height")
    visual_offset = mm_var("region-visual-offset")
    right_width = mm_var("region-right-annotation-width")
    if visual_top <= 0 or visual_height <= 0:
        return []
    section_gap = 5.0
    x0 = max(0.0, min(width_mm, left))
    x1 = width_mm - max(0.0, right)
    if right_width > 0:
        x1 = max(x0 + 18.0, x1 - right_width - section_gap)
    y0 = max(0.0, min(height_mm, visual_top + max(0.0, visual_offset)))
    y1 = max(y0 + 12.0, min(height_mm, y0 + visual_height))
    return [x0 / width_mm, y0 / height_mm, x1 / width_mm, y1 / height_mm]


def _sections(html_text: str) -> list[str]:
    return re.findall(r"(?is)<section\b[^>]*class=[\"'][^\"']*deck-page[^\"']*[\"'][^>]*>.*?</section>", html_text)


def _strip(text: str) -> str:
    text = re.sub(r"(?is)<script\b[^>]*>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style\b[^>]*>.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_GENERIC_COPY_PATTERNS = [
    r"不缺少数据",
    r"资源重新排序",
    r"持续关注",
    r"转化为行动",
    r"真正的管理抓手",
    r"当前数据证据",
    r"页面不应进入",
    r"管理层应(?!.*\d)",
    r"头部与尾部差异",
    r"放成头部放大",
]


def _has_numeric_evidence(text: str) -> bool:
    return bool(re.search(r"\d+(?:\.\d+)?\s*(?:%|万|亿|个|元|单|次|分|名)?", str(text or "")))


def _heading_texts(section: str) -> list[str]:
    raw = re.findall(r"(?is)<(?:h2|h3|figcaption)\b[^>]*>(.*?)</(?:h2|h3|figcaption)>", section)
    return [_strip(item) for item in raw if _strip(item)]


def _table_blocks(section: str) -> list[str]:
    return re.findall(r"(?is)<section\b[^>]*class=[\"'][^\"']*historical-table-asset[^\"']*[\"'][^>]*>.*?</section>", section)


def _attr_int(fragment: str, name: str) -> int:
    match = re.search(rf'{re.escape(name)}=["\'](\d+)["\']', fragment)
    if not match:
        return 0
    try:
        return int(match.group(1))
    except Exception:
        return 0


def _has_primary_visual(section: str) -> bool:
    lower = section.lower()
    if "<img" in lower or "<svg" in lower or "<table" in lower:
        return True
    visual_classes = [
        "historical-collage",
        "summary-map",
        "action-roadmap",
        "gap-matrix",
        "asset-matrix",
        "kpi-strip",
        "exhibit-fragment",
        "chart-panel",
        "visual-block",
    ]
    return any(token in lower for token in visual_classes)


def _norm_box(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        return []
    try:
        box = [max(0.0, min(1.0, float(item))) for item in value]
    except Exception:
        return []
    if box[2] <= box[0] or box[3] <= box[1]:
        return []
    return box


def _box_area(box: list[float]) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1]) if len(box) == 4 else 0.0


def _box_iou(left: Any, right: Any) -> float:
    lbox = _norm_box(left)
    rbox = _norm_box(right)
    if not lbox or not rbox:
        return 0.0
    ix0 = max(lbox[0], rbox[0])
    iy0 = max(lbox[1], rbox[1])
    ix1 = min(lbox[2], rbox[2])
    iy1 = min(lbox[3], rbox[3])
    intersection = _box_area([ix0, iy0, ix1, iy1])
    union = _box_area(lbox) + _box_area(rbox) - intersection
    return round(intersection / union, 4) if union > 0 else 0.0


def _source_profile_lookup(workspace: Path) -> dict[str, dict[str, Any]]:
    payload = _read_json(workspace / "historical_source_region_profile_pack.json")
    profiles = {}
    for item in list(payload.get("profiles") or []):
        if not isinstance(item, dict):
            continue
        profile_id = str(item.get("source_region_profile_id") or "")
        if profile_id:
            profiles[profile_id] = item
    return profiles


def _profile_regions(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": profile.get("title_box_norm") or [],
        "primary_visual": profile.get("primary_visual_box_norm") or [],
        "right_annotation": profile.get("right_annotation_box_norm") or [],
        "narrative": profile.get("narrative_box_norm") or [],
        "footer": profile.get("footer_box_norm") or [],
    }


def _right_region_is_numeric_chart_column(profile: dict[str, Any]) -> bool:
    primitives = profile.get("detected_visual_primitives")
    primitives = primitives if isinstance(primitives, dict) else {}
    try:
        right_numeric = float(primitives.get("right_numeric_column_likelihood") or 0)
    except Exception:
        right_numeric = 0.0
    right_box = _norm_box(profile.get("right_annotation_box_norm"))
    visual_box = _norm_box(profile.get("primary_visual_box_norm"))
    narrative_box = _norm_box(profile.get("narrative_box_norm"))
    if right_numeric < 0.45 or not right_box or not visual_box or not narrative_box:
        return False
    overlaps_visual_y = right_box[1] >= visual_box[1] - 0.04 and right_box[3] <= visual_box[3] + 0.06
    narrative_height = max(0.0, narrative_box[3] - narrative_box[1])
    return overlaps_visual_y and narrative_height >= 0.12


def _region_quality_scan(workspace: Path, html_text: str, deck_layout: dict[str, Any]) -> dict[str, Any]:
    source_profiles = _source_profile_lookup(workspace)
    sections = _sections(html_text)
    pages = [page for page in list(deck_layout.get("pages") or []) if isinstance(page, dict)]
    page_scores: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    right_required = 0
    right_matched = 0
    for index, page in enumerate(pages, start=1):
        template = str(page.get("page_template_type") or "")
        if template == "cover_page":
            continue
        profile_id = str(page.get("source_region_profile_id") or "")
        contract = page.get("region_layout_contract") if isinstance(page.get("region_layout_contract"), dict) else {}
        rendered_regions = contract.get("layout_regions") if isinstance(contract.get("layout_regions"), dict) else page.get("layout_regions")
        rendered_regions = rendered_regions if isinstance(rendered_regions, dict) else {}
        profile = source_profiles.get(profile_id)
        if not profile:
            issues.append({"issue": "missing_source_region_profile_binding", "page_number": index, "severity": "blocker"})
            continue
        source_regions = _profile_regions(profile)
        title_iou = _box_iou(rendered_regions.get("title"), source_regions.get("title"))
        visual_iou = _box_iou(rendered_regions.get("primary_visual"), source_regions.get("primary_visual"))
        narrative_iou = _box_iou(rendered_regions.get("narrative"), source_regions.get("narrative"))
        footer_iou = _box_iou(rendered_regions.get("footer"), source_regions.get("footer"))
        right_source = _norm_box(source_regions.get("right_annotation"))
        right_rendered = _norm_box(rendered_regions.get("right_annotation"))
        right_numeric_column = _right_region_is_numeric_chart_column(profile)
        right_source_required = _box_area(right_source) >= 0.035 and not right_numeric_column
        if right_source_required:
            right_required += 1
        right_ok = (not right_source_required) or _box_iou(right_rendered, right_source) >= 0.55
        if right_ok and right_source_required:
            right_matched += 1
        html_section = sections[index - 1] if index - 1 < len(sections) else ""
        has_right_mode = "region-mode-visual_with_right_annotation" in html_section or "region-mode-visual_with_right_delta" in html_section
        if right_source_required and not has_right_mode:
            issues.append({"issue": "right_annotation_region_not_rendered", "page_number": index, "severity": "blocker"})
        if title_iou < 0.65:
            issues.append({"issue": "title_region_iou_below_threshold", "page_number": index, "title_region_iou": title_iou, "severity": "blocker"})
        if visual_iou < 0.65:
            issues.append({"issue": "visual_region_iou_below_threshold", "page_number": index, "visual_region_iou": visual_iou, "severity": "blocker"})
        page_scores.append(
            {
                "page_number": index,
                "source_region_profile_id": profile_id,
                "matched_source_page_number": int(profile.get("source_page_number") or 0),
                "title_region_iou": title_iou,
                "visual_region_iou": visual_iou,
                "narrative_region_iou": narrative_iou,
                "footer_region_iou": footer_iou,
                "right_annotation_required": right_source_required,
                "right_numeric_column_not_reader_annotation": right_numeric_column,
                "right_annotation_presence_match": bool(right_ok and (not right_source_required or has_right_mode)),
                "region_score": round((title_iou * 0.28) + (visual_iou * 0.42) + (narrative_iou * 0.16) + (footer_iou * 0.14), 4),
            }
        )
    region_score = round(sum(float(item.get("region_score") or 0) for item in page_scores) / max(1, len(page_scores)), 4)
    right_match_ratio = round(right_matched / max(1, right_required), 4) if right_required else 1.0
    failed_pages = sorted({int(issue.get("page_number") or 0) for issue in issues if int(issue.get("page_number") or 0) > 0})
    return {
        "region_similarity_score": region_score,
        "page_region_scores": page_scores,
        "right_annotation_presence_match": right_match_ratio,
        "region_blocking_issues": issues,
        "failed_region_page_numbers": failed_pages,
        "matched_source_page_numbers": sorted({
            int(item.get("matched_source_page_number") or 0)
            for item in page_scores
            if int(item.get("matched_source_page_number") or 0) > 0
        }),
    }


def _chart_kind_aliases(kind: str) -> set[str]:
    normalized = str(kind or "").strip().lower()
    groups = [
        {"right_labeled_index_line", "indexed_multi_line", "line", "indexed_trend"},
        {"paired_horizontal_bar_with_delta", "paired_horizontal_bar", "horizontal_bar", "grouped_bar", "bar"},
        {"pareto"},
        {"waterfall", "waterfall_bridge", "value_bridge"},
        {
            "matrix_table_with_group_headers",
            "table_grid",
            "heatmap",
            "matrix",
            "table",
            "matrix_table_with_group_headers",
            "kpi_scorecard",
            "ranking_detail_table",
            "priority_action_table",
            "gap_or_benchmark_collage",
            "summary_map",
            "collage_grid",
        },
        {"grouped_bar", "vertical_bar", "bar", "pareto"},
        {"scatter_quadrant", "scatter", "portfolio_matrix"},
        {"stacked_bar_share", "share_map", "donut", "bar"},
        {"waterfall", "waterfall_bridge", "value_bridge"},
    ]
    for group in groups:
        if normalized in group:
            return set(group)
    return {normalized} if normalized else set()


def _chart_type_quality_scan(deck_layout: dict[str, Any], visual_manifest: dict[str, Any]) -> dict[str, Any]:
    manifest_by_page = {
        int(item.get("page_number") or 0): item
        for item in list(visual_manifest.get("page_visual_bindings") or [])
        if isinstance(item, dict) and int(item.get("page_number") or 0) > 0
    }
    page_scores: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    fallback_reasons: list[dict[str, Any]] = []
    for page in [item for item in list(deck_layout.get("pages") or []) if isinstance(item, dict)]:
        page_number = int(page.get("page_number") or 0)
        template = str(page.get("page_template_type") or "")
        if template == "cover_page":
            continue
        required = str(page.get("required_chart_kind") or "").strip().lower()
        if not required:
            continue
        asset_refs = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
        chart_assets = [
            asset for asset in asset_refs
            if str(asset.get("asset_type") or "") in {"chart", "table", "collage"}
        ]
        manifest_binding = manifest_by_page.get(page_number, {})
        if not chart_assets and str(manifest_binding.get("asset_type") or "") == "chart":
            chart_assets = [{"kind": manifest_binding.get("renderer_kind"), "asset_id": manifest_binding.get("asset_id")}]
        if not chart_assets:
            issues.append({"issue": "chart_grammar_missing_chart_asset", "page_number": page_number, "required_chart_kind": required, "severity": "blocker"})
            page_scores.append({"page_number": page_number, "required_chart_kind": required, "asset_kind": "", "chart_grammar_score": 0.0})
            continue
        fallback = {str(item or "").strip().lower() for item in list(page.get("fallback_chart_kinds") or []) if str(item or "").strip()}
        best_score = -1.0
        best_kind = ""
        best_reason = ""
        for asset in chart_assets:
            binding = page.get("visual_asset_binding") if isinstance(page.get("visual_asset_binding"), dict) else {}
            kind = str(binding.get("primary_chart_kind_family") or asset.get("kind") or "").strip().lower()
            if kind == required or kind in _chart_kind_aliases(required):
                score, reason = 1.0, "required_chart_kind_match"
            else:
                fallback_aliases: set[str] = set()
                for item in fallback:
                    fallback_aliases.update(_chart_kind_aliases(item))
                if kind in fallback or kind in fallback_aliases:
                    score, reason = 0.48, "fallback_chart_kind_match"
                else:
                    score, reason = 0.0, "chart_kind_mismatch"
            if score > best_score:
                best_score = score
                best_kind = kind
                best_reason = reason
        if best_score < 0.65:
            issues.append({
                "issue": "chart_type_similarity_below_threshold",
                "page_number": page_number,
                "required_chart_kind": required,
                "asset_kind": best_kind,
                "severity": "blocker",
            })
        if required in {"right_labeled_index_line", "indexed_multi_line"} and best_reason != "required_chart_kind_match":
            issues.append({
                "issue": "chart_grammar_fallback",
                "page_number": page_number,
                "required_chart_kind": required,
                "asset_kind": best_kind,
                "reason": best_reason,
                "severity": "blocker",
            })
        elif best_reason != "required_chart_kind_match" and best_score < 0.8:
            issues.append({
                "issue": "soft_chart_grammar_fallback_below_reader_threshold",
                "page_number": page_number,
                "required_chart_kind": required,
                "asset_kind": best_kind,
                "reason": best_reason,
                "severity": "blocker",
            })
        if best_reason != "required_chart_kind_match":
            fallback_reasons.append({
                "page_number": page_number,
                "required_chart_kind": required,
                "asset_kind": best_kind,
                "reason": best_reason or str(page.get("chart_fallback_reason") or ""),
            })
        page_scores.append({
            "page_number": page_number,
            "source_chart_grammar_profile_id": str(page.get("source_chart_grammar_profile_id") or ""),
            "required_chart_kind": required,
            "asset_kind": best_kind,
            "chart_grammar_score": round(max(0.0, best_score), 4),
            "match_reason": best_reason,
        })
    score = round(sum(float(item.get("chart_grammar_score") or 0) for item in page_scores) / max(1, len(page_scores)), 4)
    if page_scores and score < 0.75:
        issues.append({
            "issue": "chart_type_match_score_below_threshold",
            "chart_type_match_score": score,
            "severity": "blocker",
        })
    return {
        "chart_type_match_score": score,
        "page_chart_grammar_scores": page_scores,
        "failed_chart_grammar_page_numbers": sorted({
            int(issue.get("page_number") or 0)
            for issue in issues
            if int(issue.get("page_number") or 0) > 0
        }),
        "chart_fallback_reasons": fallback_reasons,
        "chart_grammar_blocking_issues": issues,
    }


def _profile_id_source_page_number(value: Any) -> int:
    match = re.search(r"(\d+)$", str(value or "").strip())
    if not match:
        return 0
    try:
        return int(match.group(1))
    except Exception:
        return 0


def _source_reference_consistency_scan(deck_layout: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    page_scores: list[dict[str, Any]] = []
    for page in [item for item in list(deck_layout.get("pages") or []) if isinstance(item, dict)]:
        page_number = int(page.get("page_number") or 0)
        template = str(page.get("page_template_type") or "")
        if template == "cover_page":
            continue
        region_profile = str(page.get("source_region_profile_id") or "")
        chart_profile = str(page.get("source_chart_grammar_profile_id") or "")
        region_source = _profile_id_source_page_number(region_profile)
        chart_source = _profile_id_source_page_number(chart_profile)
        aligned = bool(region_source and chart_source and region_source == chart_source)
        page_scores.append(
            {
                "page_number": page_number,
                "source_region_profile_id": region_profile,
                "source_chart_grammar_profile_id": chart_profile,
                "region_source_page_number": region_source,
                "chart_source_page_number": chart_source,
                "source_reference_aligned": aligned,
            }
        )
        if region_source > 0 and chart_source > 0 and region_source != chart_source:
            issues.append(
                {
                    "issue": "source_reference_profile_mismatch",
                    "page_number": page_number,
                    "template": template,
                    "source_region_profile_id": region_profile,
                    "source_chart_grammar_profile_id": chart_profile,
                    "severity": "blocker",
                }
            )
    aligned_count = sum(1 for item in page_scores if item.get("source_reference_aligned"))
    return {
        "source_reference_alignment_score": round(aligned_count / max(1, len(page_scores)), 4) if page_scores else 1.0,
        "page_source_reference_scores": page_scores,
        "source_reference_blocking_issues": issues,
        "failed_source_reference_page_numbers": sorted({
            int(issue.get("page_number") or 0)
            for issue in issues
            if int(issue.get("page_number") or 0) > 0
        }),
    }


def _source_region_overuse_scan(deck_layout: dict[str, Any]) -> dict[str, Any]:
    pages = [
        page for page in list(deck_layout.get("pages") or [])
        if isinstance(page, dict) and str(page.get("page_template_type") or "") != "cover_page"
    ]
    source_numbers: list[int] = []
    for page in pages:
        contract = page.get("region_layout_contract") if isinstance(page.get("region_layout_contract"), dict) else {}
        source_number = int(contract.get("source_page_number") or 0)
        if source_number <= 0:
            profile = str(page.get("source_region_profile_id") or "")
            match = re.search(r"(\d+)$", profile)
            source_number = int(match.group(1)) if match else 0
        if source_number > 0:
            source_numbers.append(source_number)
    counts: dict[int, int] = {}
    for source_number in source_numbers:
        counts[source_number] = counts.get(source_number, 0) + 1
    max_share = max(counts.values()) / max(1, len(source_numbers)) if source_numbers else 0.0
    unique_count = len(counts)
    issues: list[dict[str, Any]] = []
    if len(pages) >= 6 and unique_count < min(3, len(pages)):
        issues.append({
            "issue": "source_region_overreuse",
            "severity": "blocker",
            "matched_source_page_count": unique_count,
            "generated_content_page_count": len(pages),
            "source_page_usage_counts": {str(key): value for key, value in counts.items()},
        })
    if max_share > 0.55 and len(pages) >= 6:
        issues.append({
            "issue": "source_region_single_page_overdominance",
            "severity": "blocker",
            "max_source_page_share": round(max_share, 4),
            "source_page_usage_counts": {str(key): value for key, value in counts.items()},
        })
    return {
        "source_page_usage_counts": {str(key): value for key, value in counts.items()},
        "source_page_overuse_count": sum(max(0, count - 3) for count in counts.values()),
        "source_region_overuse_blocking_issues": issues,
    }


_WEAK_READER_TITLE_PATTERNS = (
    r"阅读路径",
    r"主要发现",
    r"执行摘要地图",
    r"核心指标指数化趋势对比",
    r"头部与尾部差异",
    r"管理层应同时",
    r"当前经营表现复盘",
    r"^\s*[^，。；:：]{1,12}\s*排名\s*$",
)


def _weak_reader_title(title: Any) -> str:
    text = str(title or "").strip()
    if not text:
        return "empty_title"
    for pattern in _WEAK_READER_TITLE_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            return pattern
    if re.search(r"^(图表|Exhibit)\s*\d+\s*$", text, flags=re.I):
        return "bare_exhibit_number"
    if len(text) < 10:
        return "too_short"
    if not re.search(r"(高于|低于|领先|落后|贡献|波动|差距|修复|放大|优先|转化率|销售额|订单量|毛利|客单价|复购|满意度|库存|退货|流量|\d)", text):
        return "no_answer_first_signal"
    return ""


def _page_role_quality_scan(deck_layout: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for page in [item for item in list(deck_layout.get("pages") or []) if isinstance(item, dict)]:
        page_number = int(page.get("page_number") or 0)
        template = str(page.get("page_template_type") or "")
        assets = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
        primary = assets[0] if assets else {}
        asset_type = str(primary.get("asset_type") or "")
        binding = page.get("visual_asset_binding") if isinstance(page.get("visual_asset_binding"), dict) else {}
        family = str(binding.get("primary_chart_kind_family") or primary.get("kind") or "")
        title = str(page.get("title") or "")
        if template in {"appendix_glossary_page", "appendix_detail_table_page"} and asset_type == "chart":
            issues.append({
                "issue": "appendix_page_bound_to_core_chart",
                "page_number": page_number,
                "template": template,
                "asset_kind": family,
                "severity": "blocker",
            })
        if template == "summary_map_page" and asset_type == "chart" and family in {"bar", "pareto", "waterfall", "waterfall_bridge"}:
            issues.append({
                "issue": "summary_map_page_bound_to_single_chart",
                "page_number": page_number,
                "template": template,
                "asset_kind": family,
                "severity": "blocker",
            })
        if re.search(r"^(图表|Exhibit)\s*\d+\s*$", title.strip(), flags=re.I):
            issues.append({
                "issue": "weak_exhibit_title",
                "page_number": page_number,
                "template": template,
                "title": title,
                "severity": "blocker",
            })
        if template not in {"cover_page", "toc_navigation_page", "module_divider_page"}:
            weak_reason = _weak_reader_title(title)
            if weak_reason:
                issues.append({
                    "issue": "weak_exhibit_title",
                    "page_number": page_number,
                    "template": template,
                    "title": title,
                    "weak_title_reason": weak_reason,
                    "severity": "blocker",
                })
    return issues


def _visual_semantic_quality_scan(workspace: Path) -> dict[str, Any]:
    """Block real-PDF runs when the semantic visual contract is underfilled."""

    semantic_path = workspace / "visual_semantic_spec.json"
    visual_reference_path = workspace / "historical_visual_reference.json"
    semantic = _read_json(semantic_path)
    visual_reference = _read_json(visual_reference_path)
    section_presence = dict((semantic.get("semantic_coverage") or {}).get("section_presence") or {})
    if not section_presence:
        section_presence = {
            "color_tokens": bool(semantic.get("color_tokens")),
            "page_tokens": bool(semantic.get("page_tokens")),
            "layout_tokens": bool(semantic.get("layout_tokens")),
            "furniture_tokens": bool(semantic.get("furniture_tokens")),
            "visual_primitives": bool(semantic.get("visual_primitives")),
            "chart_grammar_tokens": bool(semantic.get("chart_grammar_tokens")),
            "layout_region_contract": bool(semantic.get("layout_region_contract")),
            "text_logic_contract": bool(semantic.get("text_logic_contract")),
        }
    coverage_score = float((semantic.get("semantic_coverage") or {}).get("score") or 0)
    if coverage_score <= 0:
        coverage_score = round(sum(1 for enabled in section_presence.values() if enabled) / max(1, len(section_presence)), 4)
    source_is_real_pdf = bool(semantic.get("source_is_real_pdf") or visual_reference.get("source_is_real_pdf"))
    issues: list[dict[str, Any]] = []
    if source_is_real_pdf and coverage_score < 0.75:
        issues.append(
            {
                "issue": "visual_semantic_spec_underfilled",
                "coverage_score": round(coverage_score, 4),
                "threshold": 0.75,
                "section_presence": section_presence,
                "severity": "blocker",
            }
        )
    missing_required = [
        key for key in ("color_tokens", "layout_region_contract", "chart_grammar_tokens", "text_logic_contract")
        if not section_presence.get(key)
    ]
    if source_is_real_pdf and missing_required:
        issues.append(
            {
                "issue": "visual_semantic_required_sections_missing",
                "missing_sections": missing_required,
                "severity": "blocker",
            }
        )
    source_roles = visual_reference.get("source_palette_roles")
    if not isinstance(source_roles, dict):
        source_roles = (visual_reference.get("visual_style_signature") or {}).get("source_palette_roles")
    source_roles = source_roles if isinstance(source_roles, dict) else {}
    semantic_colors = semantic.get("color_tokens") if isinstance(semantic.get("color_tokens"), dict) else {}
    drift_keys = []
    if str(source_roles.get("palette_source") or "") == "pdf_preview_pixels":
        for key in ("accent", "secondary", "positive_delta", "negative_delta", "table_header_fill", "series_palette"):
            if key in source_roles and key in semantic_colors and semantic_colors.get(key) != source_roles.get(key):
                drift_keys.append(key)
    if drift_keys:
        issues.append(
            {
                "issue": "visual_semantic_palette_role_drift",
                "drift_keys": drift_keys,
                "source_palette_roles": {key: source_roles.get(key) for key in drift_keys},
                "semantic_color_tokens": {key: semantic_colors.get(key) for key in drift_keys},
                "severity": "blocker",
            }
        )
    return {
        "visual_semantic_spec_path": str(semantic_path.resolve()) if semantic_path.exists() else "",
        "visual_semantic_spec_version": str(semantic.get("visual_semantic_spec_version") or ""),
        "visual_semantic_spec_coverage_score": round(coverage_score, 4),
        "visual_semantic_section_presence": section_presence,
        "visual_semantic_blocking_issues": issues,
    }


def _name_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _asset_key(asset: dict[str, Any]) -> str:
    return str(asset.get("path") or asset.get("file_name") or asset.get("asset_id") or asset.get("title") or "").strip()


def _binding_asset_key(page: dict[str, Any]) -> str:
    binding = page.get("visual_asset_binding") if isinstance(page.get("visual_asset_binding"), dict) else {}
    key = str(binding.get("primary_asset_key") or "").strip()
    if key:
        return key
    assets = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
    return _asset_key(assets[0]) if assets else ""


def _binding_asset_family(page: dict[str, Any]) -> str:
    binding = page.get("visual_asset_binding") if isinstance(page.get("visual_asset_binding"), dict) else {}
    family = str(binding.get("primary_chart_kind_family") or "").strip()
    if family:
        return family
    assets = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
    if not assets:
        return ""
    asset = assets[0]
    asset_type = str(asset.get("asset_type") or "").strip()
    kind = str(asset.get("kind") or "").strip()
    return f"{asset_type}:{kind}" if asset_type or kind else ""


def _asset_binding_quality_scan(deck_layout: dict[str, Any]) -> dict[str, Any]:
    pages = [page for page in list(deck_layout.get("pages") or []) if isinstance(page, dict)]
    core_pages = [page for page in pages if str(page.get("page_template_type") or "") != "cover_page"]
    primary_keys: list[str] = []
    used_metrics: set[str] = set()
    used_dimensions: set[str] = set()
    low_visual_density_pages: list[int] = []
    family_counts: dict[str, int] = {}
    page_scores: list[dict[str, Any]] = []
    for page in core_pages:
        page_number = int(page.get("page_number") or 0)
        key = _binding_asset_key(page)
        family = _binding_asset_family(page)
        if key:
            primary_keys.append(key)
        if family:
            family_counts[family] = family_counts.get(family, 0) + 1
        binding = page.get("visual_asset_binding") if isinstance(page.get("visual_asset_binding"), dict) else {}
        used_metrics.update(_name_set(binding.get("metric_refs")))
        used_dimensions.update(_name_set(binding.get("dimension_refs")))
        if not used_metrics or not used_dimensions:
            for asset in list(page.get("asset_refs") or []):
                if not isinstance(asset, dict):
                    continue
                used_metrics.update(_name_set(asset.get("source_metric_names")))
                used_dimensions.update(_name_set(asset.get("source_dimension_names")))
        density = page.get("page_visual_density_plan") if isinstance(page.get("page_visual_density_plan"), dict) else {}
        target_ratio = float(density.get("visual_area_ratio_target") or 0)
        if target_ratio and target_ratio < 0.42:
            low_visual_density_pages.append(page_number)
        page_scores.append({
            "page_number": page_number,
            "primary_asset_key": key,
            "primary_asset_family": family,
            "visual_area_ratio_target": round(target_ratio, 4),
            "metric_refs": sorted(_name_set(binding.get("metric_refs"))),
            "dimension_refs": sorted(_name_set(binding.get("dimension_refs"))),
        })
    counts: dict[str, int] = {}
    for key in primary_keys:
        counts[key] = counts.get(key, 0) + 1
    overused = sorted([key for key, count in counts.items() if count > 2])
    overuse_excess = sum(max(0, count - 2) for count in counts.values())
    primary_asset_reuse_score = max(0.0, 1.0 - overuse_excess / max(1, len(primary_keys))) if primary_keys else 1.0
    key_diversity = min(1.0, len(set(primary_keys)) / max(1, min(5, len(primary_keys)))) if primary_keys else 1.0
    family_diversity = min(1.0, len(family_counts) / max(1, min(5, len(primary_keys)))) if primary_keys else 1.0
    chart_diversity_score = key_diversity * 0.45 + family_diversity * 0.55
    quality_metrics = deck_layout.get("quality_metrics") if isinstance(deck_layout.get("quality_metrics"), dict) else {}
    data_coverage = quality_metrics.get("data_coverage") if isinstance(quality_metrics.get("data_coverage"), dict) else {}
    available_metric_count = int(data_coverage.get("available_metric_count") or len(used_metrics))
    available_dimension_count = int(data_coverage.get("available_dimension_count") or len(used_dimensions))
    metric_target = min(6, available_metric_count) if available_metric_count >= 8 else max(1, available_metric_count)
    dimension_target = min(3, available_dimension_count) if available_dimension_count >= 4 else max(1, available_dimension_count)
    metric_score = min(1.0, len(used_metrics) / max(1, metric_target)) if available_metric_count else 1.0
    dimension_score = min(1.0, len(used_dimensions) / max(1, dimension_target)) if available_dimension_count else 1.0
    metric_dimension_coverage_score = metric_score * 0.58 + dimension_score * 0.42
    layout_density_score = 1.0 - min(1.0, len([p for p in low_visual_density_pages if p > 0]) / max(1, len(core_pages)))
    issues: list[dict[str, Any]] = []
    if overused:
        issues.append({"issue": "primary_asset_reused_too_many_times", "overused_asset_ids": overused, "severity": "blocker"})
    if primary_asset_reuse_score < 0.8:
        issues.append({"issue": "primary_asset_reuse_score_below_threshold", "primary_asset_reuse_score": round(primary_asset_reuse_score, 4), "severity": "blocker"})
    if chart_diversity_score < 0.7:
        issues.append({"issue": "chart_diversity_score_below_threshold", "chart_diversity_score": round(chart_diversity_score, 4), "severity": "blocker"})
    if metric_dimension_coverage_score < 0.7:
        issues.append({"issue": "metric_dimension_coverage_score_below_threshold", "metric_dimension_coverage_score": round(metric_dimension_coverage_score, 4), "severity": "blocker"})
    if low_visual_density_pages:
        issues.append({"issue": "low_visual_density_pages_detected", "page_numbers": sorted({p for p in low_visual_density_pages if p > 0}), "severity": "blocker"})
    return {
        "primary_asset_counts": counts,
        "primary_asset_family_counts": family_counts,
        "overused_asset_ids": overused,
        "primary_asset_reuse_score": round(primary_asset_reuse_score, 4),
        "chart_diversity_score": round(chart_diversity_score, 4),
        "metric_dimension_coverage_score": round(metric_dimension_coverage_score, 4),
        "layout_density_score": round(layout_density_score, 4),
        "low_visual_density_page_numbers": sorted({p for p in low_visual_density_pages if p > 0}),
        "used_metric_names": sorted(used_metrics),
        "used_dimension_names": sorted(used_dimensions),
        "page_asset_binding_scores": page_scores,
        "asset_binding_blocking_issues": issues,
    }


def _bullet_only(section: str) -> bool:
    lower = section.lower()
    if not ("<ul" in lower or "<ol" in lower):
        return False
    return not _has_primary_visual(section)


def _page_issue_scan(html_text: str, deck_layout: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    sections = _sections(html_text)
    pages = [page for page in list(deck_layout.get("pages") or []) if isinstance(page, dict)]
    for index, section in enumerate(sections, start=1):
        page = pages[index - 1] if index - 1 < len(pages) else {}
        template = str(page.get("page_template_type") or "")
        text = _strip(section)
        if template != "cover_page" and not _has_primary_visual(section):
            issues.append({"issue": "missing_primary_visual", "page_number": index, "template": template, "severity": "blocker"})
        if _bullet_only(section):
            issues.append({"issue": "bullet_only_page", "page_number": index, "template": template, "severity": "blocker"})
        if template != "cover_page" and len(text) < 80:
            issues.append({"issue": "page_text_too_thin", "page_number": index, "template": template, "visible_chars": len(text), "severity": "blocker"})
        if re.search(r"\{\{|\}\}|undefined|null null|Module\s+\d+|Data Coverage Page|Evidence Page|<\s*(?:section|div|figure|table)\b|<\s*章节\b|class\s*=", text, flags=re.I):
            issues.append({"issue": "placeholder_copy", "page_number": index, "template": template, "severity": "blocker"})
        if re.search("\u5360\u6bd4" + r"\s*0(?:\.0+)?%?", text):
            issues.append({"issue": "meaningless_zero_share_copy", "page_number": index, "template": template, "severity": "blocker"})
        if re.search(r"\b(?:action_roadmap|benchmark_callouts|summary_map_nodes|segment_badges|tag_board|gap_matrix_blocks)\b|[\u4e00-\u9fff]+_[\u4e00-\u9fffA-Za-z]+|主判断来自", text):
            issues.append({"issue": "reader_visible_internal_label", "page_number": index, "template": template, "severity": "blocker"})
        headings = _heading_texts(section)
        for left, right in zip(headings, headings[1:]):
            if left and right and left == right:
                issues.append({"issue": "duplicate_visual_heading", "page_number": index, "template": template, "heading": left, "severity": "blocker"})
                break
        for pattern in _GENERIC_COPY_PATTERNS:
            if re.search(pattern, text) and not _has_numeric_evidence(text):
                issues.append({"issue": "generic_management_copy", "page_number": index, "template": template, "pattern": pattern, "severity": "blocker"})
                break
        if "管理解读" in text or "行动含义" in text or "管理含义" in text:
            numeric_sentence_count = len(re.findall(r"[^。；;.!?]*\d+(?:\.\d+)?[^。；;.!?]*[。；;.!?]", text))
            action_specific = bool(re.search(r"(负责人|区域|渠道|品类|客群|门店|平台|预算|修复|放大|压降|复盘|下钻|优先)", text))
            if numeric_sentence_count < 2:
                issues.append({"issue": "no_numeric_evidence_sentence", "page_number": index, "template": template, "numeric_sentence_count": numeric_sentence_count, "severity": "blocker"})
            if not action_specific:
                issues.append({"issue": "weak_action_specificity", "page_number": index, "template": template, "severity": "blocker"})
        for table in _table_blocks(section):
            hidden_rows = _attr_int(table, "data-hidden-row-count")
            rendered_rows = _attr_int(table, "data-rendered-row-count")
            if rendered_rows > 12:
                issues.append({"issue": "table_rendered_rows_exceed_readable_limit", "page_number": index, "template": template, "rendered_rows": rendered_rows, "severity": "blocker"})
            if hidden_rows > 0 and "table-note" not in table:
                issues.append({"issue": "table_hidden_rows_without_summary_note", "page_number": index, "template": template, "hidden_rows": hidden_rows, "severity": "blocker"})
        sentences = [item.strip() for item in re.split(r"[。；;.!?]", text) if len(item.strip()) >= 12]
        seen: dict[str, int] = {}
        for sentence in sentences:
            key = re.sub(r"\d+(?:\.\d+)?", "#", sentence)
            seen[key] = seen.get(key, 0) + 1
        repeated_visual_card_pattern = "badge-card" in section.lower() or "summary-node" in section.lower()
        if any(count >= 2 for count in seen.values()) and not repeated_visual_card_pattern:
            issues.append({"issue": "duplicate_reader_sentence", "page_number": index, "template": template, "severity": "blocker"})
        if any(count >= 3 for count in seen.values()) and not repeated_visual_card_pattern:
            issues.append({"issue": "repeated_sentence_pattern", "page_number": index, "template": template, "severity": "blocker"})
    for page in pages:
        page_number = int(page.get("page_number") or 0)
        template = str(page.get("page_template_type") or "")
        assets = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
        if template != "cover_page" and not assets:
            issues.append({"issue": "layout_missing_primary_asset_ref", "page_number": page_number, "template": template, "severity": "blocker"})
    return issues


def evaluate_historical_screenshot_quality_gate(
    *,
    workspace: Path,
    html_path: Path,
    pdf_path: Path,
    deck_layout_path: Path,
    page_blueprint_contract_path: Path | None = None,
    visual_asset_manifest_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Reader-facing visual gate.

    This is intentionally conservative. It does not try to claim pixel-perfect
    similarity; it blocks the concrete failure mode the user surfaced: pages
    that render as title plus bullets, pages with no primary visual, and pages
    with scaffold copy.
    """

    html_text = _read_text(html_path)
    deck_layout = _read_json(deck_layout_path)
    blueprint = _read_json(page_blueprint_contract_path) if page_blueprint_contract_path and page_blueprint_contract_path.exists() else {}
    visual_manifest = _read_json(visual_asset_manifest_path) if visual_asset_manifest_path and visual_asset_manifest_path.exists() else {}
    issues = _page_issue_scan(html_text, deck_layout)
    region_quality = _region_quality_scan(workspace, html_text, deck_layout)
    issues.extend(list(region_quality.get("region_blocking_issues") or []))
    chart_type_quality = _chart_type_quality_scan(deck_layout, visual_manifest)
    issues.extend(list(chart_type_quality.get("chart_grammar_blocking_issues") or []))
    source_reference_quality = _source_reference_consistency_scan(deck_layout)
    issues.extend(list(source_reference_quality.get("source_reference_blocking_issues") or []))
    asset_binding_quality = _asset_binding_quality_scan(deck_layout)
    issues.extend(list(asset_binding_quality.get("asset_binding_blocking_issues") or []))
    source_region_overuse = _source_region_overuse_scan(deck_layout)
    issues.extend(list(source_region_overuse.get("source_region_overuse_blocking_issues") or []))
    visual_semantic_quality = _visual_semantic_quality_scan(workspace)
    issues.extend(list(visual_semantic_quality.get("visual_semantic_blocking_issues") or []))
    page_role_issues = _page_role_quality_scan(deck_layout)
    issues.extend(page_role_issues)
    raster_density_quality = _raster_density_scan(workspace, pdf_path, deck_layout, html_text)
    issues.extend(list(raster_density_quality.get("raster_density_blocking_issues") or []))
    missing_from_manifest = [
        int(page) for page in list(visual_manifest.get("missing_primary_visual_page_numbers") or [])
        if str(page).strip()
    ]
    for page_number in missing_from_manifest:
        issues.append({"issue": "visual_asset_manifest_missing_page_visual", "page_number": page_number, "severity": "blocker"})
    pages = [page for page in list(deck_layout.get("pages") or []) if isinstance(page, dict)]
    non_cover = [page for page in pages if str(page.get("page_template_type") or "") != "cover_page"]
    missing_visual_count = sum(1 for issue in issues if issue.get("issue") in {"missing_primary_visual", "layout_missing_primary_asset_ref", "visual_asset_manifest_missing_page_visual"})
    bullet_count = sum(1 for issue in issues if issue.get("issue") == "bullet_only_page")
    low_info_count = sum(1 for issue in issues if issue.get("issue") in {"generic_management_copy", "weak_action_specificity", "no_numeric_evidence_sentence", "duplicate_reader_sentence", "repeated_sentence_pattern", "reader_visible_internal_label", "meaningless_zero_share_copy"})
    duplicate_heading_count = sum(1 for issue in issues if issue.get("issue") == "duplicate_visual_heading")
    table_issue_count = sum(1 for issue in issues if str(issue.get("issue") or "").startswith("table_"))
    region_overflow_count = sum(1 for issue in issues if str(issue.get("issue") or "") in {"region_overflow", "visual_region_iou_below_threshold", "title_region_iou_below_threshold", "right_annotation_region_not_rendered"})
    weak_logic_pages = sorted({
        int(issue.get("page_number") or 0)
        for issue in issues
        if issue.get("issue") in {
            "generic_management_copy",
            "weak_action_specificity",
            "no_numeric_evidence_sentence",
            "duplicate_reader_sentence",
            "repeated_sentence_pattern",
            "weak_exhibit_title",
            "reader_visible_internal_label",
            "meaningless_zero_share_copy",
        }
        and int(issue.get("page_number") or 0) > 0
    })
    chart_grammar_fallback_pages = sorted({
        int(issue.get("page_number") or 0)
        for issue in issues
        if issue.get("issue") in {"chart_grammar_fallback", "soft_chart_grammar_fallback_below_reader_threshold"}
        and int(issue.get("page_number") or 0) > 0
    })
    chart_type_match_score = float(chart_type_quality.get("chart_type_match_score") or 0)
    primary_asset_reuse_score = float(asset_binding_quality.get("primary_asset_reuse_score") or 0)
    chart_diversity_score = float(asset_binding_quality.get("chart_diversity_score") or 0)
    metric_dimension_coverage_score = float(asset_binding_quality.get("metric_dimension_coverage_score") or 0)
    layout_density_score = float(asset_binding_quality.get("layout_density_score") or 0)
    low_raster_density_pages = list(raster_density_quality.get("low_raster_density_page_numbers") or [])
    raster_visual_density_scores: list[float] = []
    for score in list(raster_density_quality.get("page_density_scores") or []):
        if not isinstance(score, dict) or score.get("primary_visual_ink_ratio") is None:
            continue
        template = str(score.get("template") or "")
        target = 0.055 if template in {"thesis_chart_page", "heatmap_leverage_page", "scatter_diagnosis_page"} else 0.048
        try:
            raster_visual_density_scores.append(min(1.0, float(score.get("primary_visual_ink_ratio") or 0) / target))
        except Exception:
            continue
    raster_visual_density_score = (
        sum(raster_visual_density_scores) / max(1, len(raster_visual_density_scores))
        if raster_visual_density_scores
        else 0.0
    )
    source_relative_density_score = float(raster_density_quality.get("source_relative_density_score") or 0)
    source_relative_color_score = float(raster_density_quality.get("source_relative_color_score") or 0)
    visual_similarity_proxy = 1.0 - min(1.0, missing_visual_count / max(1, len(non_cover)))
    if raster_visual_density_scores:
        visual_similarity_proxy = min(visual_similarity_proxy, raster_visual_density_score)
    if source_relative_density_score > 0:
        visual_similarity_proxy = min(visual_similarity_proxy, source_relative_density_score)
    if source_relative_color_score > 0:
        visual_similarity_proxy = min(visual_similarity_proxy, source_relative_color_score)
    page_blueprint_score = 1.0
    if blueprint:
        blueprint_pages = [page for page in list(blueprint.get("pages") or []) if isinstance(page, dict)]
        required = [
            page for page in blueprint_pages
            if str(page.get("page_template_type") or "") != "cover_page"
            and bool((page.get("required_data_assets") if isinstance(page.get("required_data_assets"), dict) else {}).get("primary_visual_required"))
        ]
        page_blueprint_score = 1.0 - min(1.0, missing_visual_count / max(1, len(required)))
    blockers = [issue for issue in issues if str(issue.get("severity") or "blocker") == "blocker"]
    failed_pages = sorted(
        {
            int(issue.get("page_number") or 0)
            for issue in blockers
            if int(issue.get("page_number") or 0) > 0
        }
    )
    payload = {
        "screenshot_quality_gate_version": "historical-screenshot-quality-gate-v1",
        "workspace_path": str(workspace.resolve()),
        "passed": not blockers,
        "visual_similarity_score": round(max(0.0, visual_similarity_proxy), 4),
        "raster_visual_density_score": round(max(0.0, raster_visual_density_score), 4),
        "source_relative_density_score": round(max(0.0, source_relative_density_score), 4),
        "source_relative_color_score": round(max(0.0, source_relative_color_score), 4),
        "region_similarity_score": float(region_quality.get("region_similarity_score") or 0),
        "page_region_scores": list(region_quality.get("page_region_scores") or []),
        "right_annotation_presence_match": float(region_quality.get("right_annotation_presence_match") or 0),
        "region_overflow_count": region_overflow_count,
        "failed_region_page_numbers": list(region_quality.get("failed_region_page_numbers") or []),
        "matched_source_page_numbers": list(region_quality.get("matched_source_page_numbers") or []),
        "source_page_usage_counts": dict(source_region_overuse.get("source_page_usage_counts") or {}),
        "source_page_overuse_count": int(source_region_overuse.get("source_page_overuse_count") or 0),
        "visual_semantic_spec_path": str(visual_semantic_quality.get("visual_semantic_spec_path") or ""),
        "visual_semantic_spec_version": str(visual_semantic_quality.get("visual_semantic_spec_version") or ""),
        "visual_semantic_spec_coverage_score": float(visual_semantic_quality.get("visual_semantic_spec_coverage_score") or 0),
        "visual_semantic_section_presence": dict(visual_semantic_quality.get("visual_semantic_section_presence") or {}),
        "chart_type_match_score": round(chart_type_match_score, 4),
        "source_reference_alignment_score": float(source_reference_quality.get("source_reference_alignment_score") or 0),
        "page_source_reference_scores": list(source_reference_quality.get("page_source_reference_scores") or []),
        "failed_source_reference_page_numbers": list(source_reference_quality.get("failed_source_reference_page_numbers") or []),
        "page_chart_grammar_scores": list(chart_type_quality.get("page_chart_grammar_scores") or []),
        "failed_chart_grammar_page_numbers": list(chart_type_quality.get("failed_chart_grammar_page_numbers") or []),
        "chart_fallback_reasons": list(chart_type_quality.get("chart_fallback_reasons") or []),
        "primary_asset_reuse_score": round(primary_asset_reuse_score, 4),
        "chart_diversity_score": round(chart_diversity_score, 4),
        "metric_dimension_coverage_score": round(metric_dimension_coverage_score, 4),
        "layout_density_score": round(layout_density_score, 4),
        "raster_density_available": bool(raster_density_quality.get("available")),
        "page_raster_density_scores": list(raster_density_quality.get("page_density_scores") or []),
        "overused_asset_ids": list(asset_binding_quality.get("overused_asset_ids") or []),
        "primary_asset_counts": dict(asset_binding_quality.get("primary_asset_counts") or {}),
        "primary_asset_family_counts": dict(asset_binding_quality.get("primary_asset_family_counts") or {}),
        "low_visual_density_page_numbers": sorted(set(list(asset_binding_quality.get("low_visual_density_page_numbers") or []) + low_raster_density_pages)),
        "white_space_issue_pages": sorted(set(list(asset_binding_quality.get("low_visual_density_page_numbers") or []) + low_raster_density_pages)),
        "chart_grammar_fallback_pages": chart_grammar_fallback_pages,
        "weak_logic_pages": weak_logic_pages,
        "page_asset_binding_scores": list(asset_binding_quality.get("page_asset_binding_scores") or []),
        "used_metric_names": list(asset_binding_quality.get("used_metric_names") or []),
        "used_dimension_names": list(asset_binding_quality.get("used_dimension_names") or []),
        "page_blueprint_coverage_score": round(max(0.0, page_blueprint_score), 4),
        "bullet_only_page_count": bullet_count,
        "missing_visual_page_count": missing_visual_count,
        "low_information_page_count": low_info_count,
        "duplicate_heading_count": duplicate_heading_count,
        "table_clip_issue_count": table_issue_count,
        "failed_page_numbers": failed_pages,
        "reader_quality_blockers": blockers[:200],
        "blocking_issues": blockers[:200],
        "all_issues": issues[:500],
        "scanned_artifacts": {
            "html": str(html_path.resolve()),
            "pdf": str(pdf_path.resolve()) if pdf_path.exists() else "",
            "deck_layout": str(deck_layout_path.resolve()),
            "page_blueprint_contract": str(page_blueprint_contract_path.resolve()) if page_blueprint_contract_path else "",
            "visual_asset_manifest": str(visual_asset_manifest_path.resolve()) if visual_asset_manifest_path else "",
        },
    }
    target = output_path or workspace / "historical_screenshot_quality_gate.json"
    _write_json(target, payload)
    return payload
