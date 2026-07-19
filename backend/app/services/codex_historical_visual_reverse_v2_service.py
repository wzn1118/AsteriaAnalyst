from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return 0, 0


def _page_family(page_index: int, source_page_count: int, visual_reference: dict[str, Any]) -> str:
    tokens = {str(token) for token in list(visual_reference.get("visual_style_tokens") or [])}
    if page_index == 1:
        return "cover_or_opening_exhibit"
    if source_page_count <= 10 and "bcg_quarterly_watch" in tokens:
        return "short_consulting_watch_exhibit"
    return "historical_analysis_deck_page"


def build_historical_visual_reverse_spec_v2(
    *,
    workspace: Path,
    visual_reference_payload: dict[str, Any],
    preview_paths: list[str] | None = None,
) -> dict[str, Any]:
    contract = visual_reference_payload.get("style_transfer_contract")
    if not isinstance(contract, dict):
        contract = {}
    regions = contract.get("regions")
    if not isinstance(regions, dict):
        regions = {}
    chart_style = contract.get("chart_style")
    if not isinstance(chart_style, dict):
        chart_style = {}
    source_page_count = int(visual_reference_payload.get("source_page_count") or len(preview_paths or []) or 0)
    pages: list[dict[str, Any]] = []
    for index, preview in enumerate(list(preview_paths or [])[: max(1, source_page_count)], start=1):
        path = Path(preview)
        if not path.is_absolute():
            path = workspace / path
        width, height = _image_size(path)
        pages.append(
            {
                "source_page_number": index,
                "preview_path": str(path.resolve()) if path.exists() else str(path),
                "preview_width": width,
                "preview_height": height,
                "page_family": _page_family(index, source_page_count, visual_reference_payload),
                "layout_regions": {
                    "title_region_norm": regions.get("title_region_norm") or [],
                    "primary_visual_region_norm": regions.get("primary_visual_region_norm") or [],
                    "right_annotation_region_norm": regions.get("right_annotation_region_norm") or [],
                    "narrative_region_norm": regions.get("narrative_region_norm") or [],
                    "footer_region_norm": regions.get("footer_region_norm") or [],
                },
                "chart_grammar_tokens": list(chart_style.get("chart_grammar_tokens") or []),
                "dominant_chart_grammar": str(chart_style.get("dominant_chart_grammar") or ""),
                "furniture_rules": dict(contract.get("furniture") or {}),
            }
        )
    if not pages:
        pages.append(
            {
                "source_page_number": 1,
                "preview_path": "",
                "page_family": _page_family(1, source_page_count, visual_reference_payload),
                "layout_regions": {
                    "title_region_norm": regions.get("title_region_norm") or [],
                    "primary_visual_region_norm": regions.get("primary_visual_region_norm") or [],
                    "right_annotation_region_norm": regions.get("right_annotation_region_norm") or [],
                    "narrative_region_norm": regions.get("narrative_region_norm") or [],
                    "footer_region_norm": regions.get("footer_region_norm") or [],
                },
                "chart_grammar_tokens": list(chart_style.get("chart_grammar_tokens") or []),
                "dominant_chart_grammar": str(chart_style.get("dominant_chart_grammar") or ""),
                "furniture_rules": dict(contract.get("furniture") or {}),
            }
        )
    return {
        "visual_reverse_spec_version": "historical-visual-reverse-v2",
        "workspace_path": str(workspace.resolve()),
        "source_is_real_pdf": bool(visual_reference_payload.get("source_is_real_pdf")),
        "source_page_count": source_page_count,
        "historical_report_family_hint": str(visual_reference_payload.get("historical_report_family_hint") or ""),
        "page_taxonomy": sorted({str(page.get("page_family") or "") for page in pages if page.get("page_family")}),
        "typography_tokens": dict((contract.get("typography") if isinstance(contract.get("typography"), dict) else {}) or {}),
        "color_tokens": dict(contract.get("colors") or {}),
        "furniture_rules": dict(contract.get("furniture") or {}),
        "chart_grammar_tokens": list(chart_style.get("chart_grammar_tokens") or []),
        "dominant_chart_grammar": str(chart_style.get("dominant_chart_grammar") or ""),
        "pages": pages,
    }


def write_historical_visual_reverse_spec_v2(
    *,
    workspace: Path,
    visual_reference_path: Path,
    preview_paths: list[str] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    payload = build_historical_visual_reverse_spec_v2(
        workspace=workspace,
        visual_reference_payload=_read_json(visual_reference_path),
        preview_paths=preview_paths,
    )
    target = output_path or workspace / "historical_visual_reverse_spec_v2.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload
