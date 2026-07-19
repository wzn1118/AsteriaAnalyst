from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


BANNED_READER_PHRASES = [
    "该页把当前数据证据压缩成一个可执行的管理判断",
    "重点是决定资源应投向哪里",
    "这一页应形成可执行的管理判断",
    "而不是只描述图形",
    "这页可视化把复杂结构压缩成单页经营判断",
    "历史 PDF 仅用于页面系统逆向",
    "页面节奏来自历史 PDF 视觉识别",
    "Data Coverage Page",
    "Evidence Page",
    "Module Divider",
    "排名ing",
    "缺少可验证数据证据，页面不应进入最终报告",
]


BANNED_REGEXES = [
    ("module_number_placeholder", re.compile(r"\bModule\s+\d+\b|模块\s*\d+")),
    ("all_zero_distribution", re.compile(r"最小值\s*0\s*下四分位\s*0\s*中位数\s*0\s*上四分位\s*0\s*最大值\s*0")),
    ("template_page_title", re.compile(r"\b(?:Evidence|Data Coverage|Module Divider)\s+Page\b", re.I)),
    ("unrendered_template_token", re.compile(r"\{\{|\}\}|undefined|null null", re.I)),
    ("visible_html_tag_or_class", re.compile(r"<\s*(?:section|div|figure|table)\b|<\s*章节\b|class\s*=", re.I)),
]


LOW_VALUE_TITLES = {
    "信号标签板",
    "业态与客群卡片",
    "模块导航板",
}


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


def _strip_html(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _html_page_sections(html_text: str) -> list[str]:
    return re.findall(r"(?is)<section\b[^>]*class=[\"'][^\"']*deck-page[^\"']*[\"'][^>]*>.*?</section>", html_text)


def _html_section_has_visual(section: str) -> bool:
    lower = section.lower()
    if "<img" in lower or "<svg" in lower or "<table" in lower:
        return True
    return any(
        token in lower
        for token in (
            "historical-collage",
            "summary-map",
            "action-roadmap",
            "gap-matrix",
            "kpi-strip",
            "asset-matrix",
            "visual-block",
            "exhibit-fragment",
        )
    )


def _scan_html_visual_quality(html_text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for page_number, section in enumerate(_html_page_sections(html_text), start=1):
        lower = section.lower()
        is_cover = "cover-page" in lower
        if not is_cover and not _html_section_has_visual(section):
            issues.append({"issue": "missing_primary_visual", "page_number": page_number, "severity": "blocker"})
        if not is_cover and ("<ul" in lower or "<ol" in lower) and not _html_section_has_visual(section):
            issues.append({"issue": "bullet_only_page", "page_number": page_number, "severity": "blocker"})
    return issues


def _pdf_page_texts(pdf_path: Path) -> list[str]:
    if not pdf_path.exists():
        return []
    try:
        from pypdf import PdfReader  # type: ignore

        return [re.sub(r"\s+", " ", page.extract_text() or "").strip() for page in PdfReader(str(pdf_path)).pages]
    except Exception:
        return []


def _scan_text(text: str, *, label: str, page_number: int | None = None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for phrase in BANNED_READER_PHRASES:
        count = text.count(phrase)
        if count:
            issues.append(
                {
                    "issue": "banned_reader_phrase",
                    "label": label,
                    "page_number": page_number,
                    "token": phrase,
                    "count": count,
                    "severity": "blocker",
                }
            )
    for issue_name, pattern in BANNED_REGEXES:
        matches = pattern.findall(text)
        if matches:
            issues.append(
                {
                    "issue": issue_name,
                    "label": label,
                    "page_number": page_number,
                    "count": len(matches),
                    "sample": matches[:5],
                    "severity": "blocker",
                }
            )
    sentence_candidates = [
        re.sub(r"\s+", " ", item).strip()
        for item in re.split(r"[。！？!?]\s*", text)
        if len(re.sub(r"\s+", "", item)) >= 18
    ]
    sentence_candidates = [
        sentence for sentence in sentence_candidates
        if not sentence.startswith("来源：")
        and "当前数据资产包与历史报告视觉规范" not in sentence
        and "数据来源：" not in sentence
    ]
    repeated = [
        {"sentence": sentence, "count": count}
        for sentence, count in Counter(sentence_candidates).most_common(8)
        if count >= 3
    ]
    if repeated:
        issues.append(
            {
                "issue": "repeated_reader_sentence",
                "label": label,
                "page_number": page_number,
                "repeated": repeated,
                "severity": "blocker",
            }
        )
    return issues


def _numbers_from(value: Any) -> list[float]:
    numbers: list[float] = []
    if isinstance(value, dict):
        for nested in value.values():
            numbers.extend(_numbers_from(nested))
    elif isinstance(value, list):
        for item in value:
            numbers.extend(_numbers_from(item))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        numbers.append(float(value))
    return numbers


def _asset_key(asset: dict[str, Any]) -> str:
    return str(asset.get("asset_id") or asset.get("path") or asset.get("file_name") or asset.get("title") or "")


def _asset_has_insight(asset: dict[str, Any]) -> bool:
    insight = asset.get("insight_input")
    if not isinstance(insight, dict) or not insight:
        return False
    if insight.get("rows") or insight.get("top_segments") or insight.get("bottom_segments"):
        return True
    if asset.get("source_metric_names") or asset.get("source_dimension_names"):
        return True
    return any(key in insight for key in ("raw_key", "metric_raw_key", "dimension_raw_key", "metric", "dimension"))


def _scan_asset_index(path: Path, *, asset_type: str) -> list[dict[str, Any]]:
    payload = _read_json(path)
    issues: list[dict[str, Any]] = []
    for index, asset in enumerate(list(payload.get("assets") or []), start=1):
        if not isinstance(asset, dict):
            continue
        title = str(asset.get("title") or "").strip()
        insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
        numbers = _numbers_from(insight)
        key = _asset_key(asset) or f"{asset_type}_{index}"
        if "排名ing" in title:
            issues.append({"issue": "mixed_language_asset_title", "asset_type": asset_type, "asset_key": key, "title": title, "severity": "blocker"})
        if title in LOW_VALUE_TITLES and not _asset_has_insight(asset):
            issues.append({"issue": "placeholder_collage_asset", "asset_type": asset_type, "asset_key": key, "title": title, "severity": "blocker"})
        if asset_type in {"table", "collage"} and not _asset_has_insight(asset):
            issues.append({"issue": "asset_missing_reader_insight", "asset_type": asset_type, "asset_key": key, "title": title, "severity": "warning"})
        if asset_type == "chart" and numbers and max(abs(number) for number in numbers) == 0:
            issues.append({"issue": "all_zero_chart_asset", "asset_type": asset_type, "asset_key": key, "title": title, "severity": "blocker"})
    return issues


def _scan_layout(layout_path: Path) -> list[dict[str, Any]]:
    payload = _read_json(layout_path)
    issues: list[dict[str, Any]] = []
    pages = [page for page in list(payload.get("pages") or []) if isinstance(page, dict)]
    for page in pages:
        page_number = int(page.get("page_number") or 0)
        title = str(page.get("title") or "")
        template = str(page.get("page_template_type") or "")
        asset_refs = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
        if re.search(r"\b(?:Module Divider|Evidence Page|Data Coverage Page)\b", title, flags=re.I):
            issues.append({"issue": "scaffold_page_title", "page_number": page_number, "title": title, "severity": "blocker"})
        if re.search(r"模块\s*\d+$", title):
            issues.append({"issue": "module_number_placeholder_title", "page_number": page_number, "title": title, "severity": "blocker"})
        if template != "cover_page" and not asset_refs:
            issues.append({"issue": "missing_primary_visual", "page_number": page_number, "template": template, "title": title, "severity": "blocker"})
        for asset in asset_refs:
            asset_title = str(asset.get("title") or "")
            if asset_title in LOW_VALUE_TITLES and not _asset_has_insight(asset):
                issues.append({"issue": "page_uses_placeholder_collage", "page_number": page_number, "title": title, "asset_title": asset_title, "severity": "blocker"})
    return issues


def evaluate_historical_reader_quality_gate(
    *,
    workspace: Path,
    markdown_path: Path,
    html_path: Path,
    pdf_path: Path,
    deck_layout_path: Path,
    chart_assets_index_path: Path,
    table_assets_index_path: Path,
    collage_assets_index_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    markdown_text = _read_text(markdown_path)
    html_raw_text = _read_text(html_path)
    html_reader_text = _strip_html(html_raw_text)
    pdf_pages = _pdf_page_texts(pdf_path)
    text_issues: list[dict[str, Any]] = []
    text_issues.extend(_scan_text(markdown_text, label=markdown_path.name))
    text_issues.extend(_scan_text(html_reader_text, label=html_path.name))
    text_issues.extend(_scan_html_visual_quality(html_raw_text))
    for page_number, page_text in enumerate(pdf_pages, start=1):
        text_issues.extend(_scan_text(page_text, label=pdf_path.name, page_number=page_number))
    layout_issues = _scan_layout(deck_layout_path)
    asset_issues = (
        _scan_asset_index(chart_assets_index_path, asset_type="chart")
        + _scan_asset_index(table_assets_index_path, asset_type="table")
        + _scan_asset_index(collage_assets_index_path, asset_type="collage")
    )
    issues = text_issues + layout_issues + asset_issues
    blockers = [issue for issue in issues if str(issue.get("severity") or "blocker") == "blocker"]
    payload = {
        "reader_quality_gate_version": "historical-reader-quality-gate-v1",
        "workspace_path": str(workspace.resolve()),
        "passed": not blockers,
        "blocker_count": len(blockers),
        "warning_count": len(issues) - len(blockers),
        "blocking_issues": blockers[:200],
        "all_issues": issues[:500],
        "scanned_artifacts": {
            "markdown": str(markdown_path.resolve()),
            "html": str(html_path.resolve()),
            "pdf": str(pdf_path.resolve()),
            "deck_layout": str(deck_layout_path.resolve()),
            "chart_assets": str(chart_assets_index_path.resolve()),
            "table_assets": str(table_assets_index_path.resolve()),
            "collage_assets": str(collage_assets_index_path.resolve()),
        },
        "pdf_page_count": len(pdf_pages),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload
