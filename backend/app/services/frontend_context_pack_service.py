from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from app.models import SmartReportRequest


_DETAIL_DIMENSION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("media", ("media", "媒介", "媒体")),
    ("channel", ("channel", "渠道")),
    ("terminal", ("terminal", "device", "终端", "设备")),
    ("brand", ("brand", "品牌")),
    ("province", ("province", "省份")),
    ("region", ("region", "区域", "地区")),
    ("placement", ("placement", "点位", "广告位")),
    ("campaign", ("campaign", "活动", "投放")),
    ("category", ("category", "类目", "品类")),
    ("sku", ("sku",)),
    ("product", ("product", "商品", "产品")),
    ("customer", ("customer", "客户", "用户")),
    ("seller", ("seller", "商家", "供应商")),
    ("content", ("content", "内容", "素材")),
)

_BACKGROUND_SIGNAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("growth_goal", ("增长", "转化", "拉新", "留存", "活跃")),
    ("brand_focus", ("品牌", "心智", "认知", "声量", "传播")),
    ("media_delivery", ("投放", "曝光", "点击", "CTR", "CPM", "CPC", "CPA")),
    ("channel_structure", ("渠道", "媒介", "终端", "点位", "区域")),
    ("commercial_constraint", ("预算", "ROI", "成本", "毛利", "利润")),
    ("risk_or_pressure", ("风险", "压力", "波动", "预警", "下滑")),
    ("decision_window", ("本期", "本周", "本月", "季度", "复盘", "行动")),
)

_TONE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("conclusion_first", ("结论", "摘要", "要点", "总览", "结论先行")),
    ("management_language", ("管理层", "经营", "动作", "建议", "复盘")),
    ("evidence_dense", ("数据", "指标", "证据", "明细", "附录")),
    ("editorial_style", ("内参", "纪要", "评论", "研判", "洞察")),
)


def _clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text, flags=re.S)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clip_text(value: Any, limit: int) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    normalized = text.replace("\n", " ")
    parts = re.split(r"(?<=[。！？!?；;])\s+|(?<=[。！？!?；;])", normalized)
    return [part.strip(" -\t") for part in parts if part.strip(" -\t")]


def _split_constraints(text: str) -> list[str]:
    normalized = _clean_text(text)
    if not normalized:
        return []
    parts = re.split(r"[\n,;；，、|]+", normalized)
    seen: set[str] = set()
    values: list[str] = []
    for part in parts:
        item = part.strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        values.append(item)
    return values[:6]


def _heading_like_lines(text: str, *, limit: int = 5) -> list[str]:
    lines = [line.strip(" -#\t") for line in _clean_text(text).splitlines()]
    picked: list[str] = []
    for line in lines:
        if not line or len(line) > 28:
            continue
        if len(line) < 4:
            continue
        if line in picked:
            continue
        picked.append(line)
        if len(picked) >= limit:
            break
    return picked


def _score_sentence(sentence: str) -> float:
    lowered = sentence.lower()
    score = 0.0
    for _, tokens in _BACKGROUND_SIGNAL_RULES:
        if any(token.lower() in lowered for token in tokens):
            score += 1.0
    if len(sentence) >= 18:
        score += 0.4
    if len(sentence) <= 120:
        score += 0.2
    return score


def _top_sentences(text: str, *, limit: int = 5) -> list[str]:
    candidates = _split_sentences(text)
    ranked = sorted(
        ((-_score_sentence(sentence), index, sentence) for index, sentence in enumerate(candidates)),
        key=lambda item: (item[0], item[1]),
    )
    picked: list[str] = []
    for _, _, sentence in ranked:
        if sentence in picked:
            continue
        picked.append(sentence)
        if len(picked) >= limit:
            break
    return picked


def _detected_detail_dimensions(text: str) -> list[str]:
    lowered = _clean_text(text).lower()
    hints: list[str] = []
    for canonical, tokens in _DETAIL_DIMENSION_RULES:
        if any(token.lower() in lowered for token in tokens) and canonical not in hints:
            hints.append(canonical)
    return hints[:10]


def _detected_signals(text: str) -> list[str]:
    lowered = _clean_text(text).lower()
    signals: list[str] = []
    for label, tokens in _BACKGROUND_SIGNAL_RULES:
        if any(token.lower() in lowered for token in tokens):
            signals.append(label)
    return signals[:8]


def _tone_cues(text: str) -> list[str]:
    lowered = _clean_text(text).lower()
    cues: list[str] = []
    for label, tokens in _TONE_RULES:
        if any(token.lower() in lowered for token in tokens):
            cues.append(label)
    return cues[:6]


def _domain_lexicon(*parts: str) -> list[str]:
    combined = " ".join(_clean_text(part) for part in parts if _clean_text(part))
    hints = _detected_detail_dimensions(combined)
    signals = _detected_signals(combined)
    return [*hints, *signals][:12]


def build_frontend_context_pack(request: SmartReportRequest) -> dict[str, Any]:
    background_text = _clean_text(request.business_background_text)
    historical_text = _clean_text(request.historical_report_text)
    requirement_focus = "；".join(
        item
        for item in [
            request.user_requirement.strip(),
            request.problem_to_solve.strip(),
            request.core_purpose.strip(),
            request.expected_result.strip(),
        ]
        if item
    )
    background_summary = _top_sentences(background_text, limit=5)
    historical_summary = _top_sentences(historical_text, limit=4)
    historical_headings = _heading_like_lines(historical_text, limit=5)
    detail_dimension_hints = _detected_detail_dimensions(
        " ".join(
            [
                request.required_detail_dimensions_text,
                request.user_requirement,
                request.problem_to_solve,
                request.business_background_name,
                request.business_background_text,
            ]
        )
    )
    constraints = _split_constraints(request.key_constraints)
    tone_preferences = [
        item
        for item in [
            request.visual_style_text.strip(),
            request.historical_report_name.strip(),
            *historical_headings[:2],
        ]
        if item
    ][:5]
    must_answer = [
        item
        for item in [
            request.problem_to_solve.strip(),
            request.user_requirement.strip(),
            *background_summary[:2],
        ]
        if item
    ][:5]
    must_preserve = [
        item
        for item in [
            request.target_audience.strip(),
            request.expected_result.strip(),
            *constraints[:3],
        ]
        if item
    ][:5]
    context_brief_parts = [
        f"目标受众：{request.target_audience.strip()}" if request.target_audience.strip() else "",
        f"核心目的：{request.core_purpose.strip()}" if request.core_purpose.strip() else "",
        f"核心问题：{request.problem_to_solve.strip()}" if request.problem_to_solve.strip() else "",
        f"预期结果：{request.expected_result.strip()}" if request.expected_result.strip() else "",
        f"背景摘要：{'；'.join(background_summary[:2])}" if background_summary else "",
        f"历史参考：{'；'.join(historical_headings[:2] or historical_summary[:2])}" if (historical_headings or historical_summary) else "",
        f"明细维度倾向：{', '.join(detail_dimension_hints)}" if detail_dimension_hints else "",
    ]
    context_brief = "\n".join(part for part in context_brief_parts if part)
    return {
        "version": "frontend_context_pack_v1",
        "input_presence": {
            "user_requirement": bool(request.user_requirement.strip()),
            "problem_to_solve": bool(request.problem_to_solve.strip()),
            "target_audience": bool(request.target_audience.strip()),
            "core_purpose": bool(request.core_purpose.strip()),
            "expected_result": bool(request.expected_result.strip()),
            "key_constraints": bool(request.key_constraints.strip()),
            "business_background_text": bool(background_text),
            "historical_report_text": bool(historical_text),
            "visual_style_text": bool(request.visual_style_text.strip()),
            "required_detail_dimensions_text": bool(request.required_detail_dimensions_text.strip()),
        },
        "requirement_stack": {
            "user_requirement": request.user_requirement.strip(),
            "problem_to_solve": request.problem_to_solve.strip(),
            "target_audience": request.target_audience.strip(),
            "core_purpose": request.core_purpose.strip(),
            "expected_result": request.expected_result.strip(),
            "key_constraints": constraints,
        },
        "business_background": {
            "name": request.business_background_name.strip(),
            "summary_bullets": background_summary,
            "signal_labels": _detected_signals(background_text),
            "source_excerpt": _clip_text(background_text, 1800),
        },
        "historical_reference": {
            "name": request.historical_report_name.strip(),
            "structure_cues": historical_headings,
            "summary_bullets": historical_summary,
            "tone_cues": _tone_cues(historical_text),
            "source_excerpt": _clip_text(historical_text, 1600),
            "usage_rule": "Historical report is style/structure reference only, not factual evidence.",
        },
        "context_directives": {
            "must_answer": must_answer,
            "must_preserve": must_preserve,
            "detail_dimension_hints": detail_dimension_hints,
            "tone_preferences": tone_preferences,
        },
        "domain_lexicon": _domain_lexicon(
            request.user_requirement,
            request.problem_to_solve,
            request.business_background_name,
            request.business_background_text,
            request.historical_report_name,
            request.required_detail_dimensions_text,
        ),
        "context_brief": context_brief,
    }


def render_frontend_context_pack_markdown(pack: dict[str, Any]) -> str:
    requirement_stack = pack.get("requirement_stack") if isinstance(pack.get("requirement_stack"), dict) else {}
    business_background = pack.get("business_background") if isinstance(pack.get("business_background"), dict) else {}
    historical_reference = pack.get("historical_reference") if isinstance(pack.get("historical_reference"), dict) else {}
    directives = pack.get("context_directives") if isinstance(pack.get("context_directives"), dict) else {}
    return "\n".join(
        [
            "# Frontend Context Pack",
            "",
            f"- 目标受众：{requirement_stack.get('target_audience') or '未显式提供'}",
            f"- 核心目的：{requirement_stack.get('core_purpose') or '未显式提供'}",
            f"- 核心问题：{requirement_stack.get('problem_to_solve') or requirement_stack.get('user_requirement') or '未显式提供'}",
            f"- 预期结果：{requirement_stack.get('expected_result') or '未显式提供'}",
            "",
            "## Business Background",
            *[f"- {item}" for item in list(business_background.get("summary_bullets") or [])[:5]],
            "",
            "## Historical Reference",
            *[f"- {item}" for item in list(historical_reference.get("structure_cues") or [])[:5]],
            *[f"- {item}" for item in list(historical_reference.get("summary_bullets") or [])[:3]],
            "",
            "## Directives",
            f"- 必须回答：{'；'.join(str(item) for item in list(directives.get('must_answer') or [])[:5]) or '未显式提供'}",
            f"- 必须保留：{'；'.join(str(item) for item in list(directives.get('must_preserve') or [])[:5]) or '未显式提供'}",
            f"- 明细维度：{', '.join(str(item) for item in list(directives.get('detail_dimension_hints') or [])[:10]) or '未显式提供'}",
            f"- 语气/风格：{'；'.join(str(item) for item in list(directives.get('tone_preferences') or [])[:5]) or '未显式提供'}",
            "",
            "## Context Brief",
            str(pack.get("context_brief") or "未生成简报"),
            "",
        ]
    )


def write_frontend_context_pack_files(workspace_path: str | Path, request: SmartReportRequest) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    pack = build_frontend_context_pack(request)
    json_path = workspace / "00_frontend_context_pack.json"
    md_path = workspace / "00_frontend_context_pack.md"
    json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_frontend_context_pack_markdown(pack), encoding="utf-8")
    return {
        "pack": pack,
        "json_path": str(json_path.resolve()),
        "markdown_path": str(md_path.resolve()),
    }
