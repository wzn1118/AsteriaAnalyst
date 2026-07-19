from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from app.models import CodexRunRequest, SmartReportRequest
from app.services.codex_runtime_prompt_templates import build_requirement_intent_prompt
from app.services.codex_runtime_service import run_headless_codex
from app.services.codex_runtime_task_service import cancel_codex_run_task, get_codex_run_task
from app.services.frontend_context_pack_service import write_frontend_context_pack_files
from app.services.report_design_spec_service import DEFAULT_LAYOUT_PRESET_ID, REPORT_LAYOUT_PRESETS


REPORT_INTENT_FIELDS = [
    "optimized_user_requirement",
    "detected_business_profile",
    "business_questions",
    "target_audience",
    "core_purpose",
    "expected_result",
    "analysis_depth",
    "required_detail_dimensions",
    "must_include_sections",
    "recommendation_style",
    "visual_style",
    "color_palette",
    "chart_palette_preset",
    "chart_palette_colors",
    "layout_preference",
    "pdf_design_brief",
    "forbidden_patterns",
    "output_contract",
]

LIST_INTENT_FIELDS = {
    "business_questions",
    "required_detail_dimensions",
    "must_include_sections",
    "forbidden_patterns",
    "chart_palette_colors",
}

TEXT_INTENT_FIELDS = (
    "optimized_user_requirement",
    "detected_business_profile",
    "target_audience",
    "core_purpose",
    "expected_result",
    "analysis_depth",
    "recommendation_style",
    "visual_style",
    "color_palette",
    "chart_palette_preset",
    "layout_preference",
    "pdf_design_brief",
)


def _requirement_intent_timeout(default_timeout_sec: int) -> int:
    raw_value = os.getenv("ASTERIA_REQUIREMENT_INTENT_TIMEOUT_SEC", "").strip()
    try:
        configured = int(raw_value) if raw_value else int(default_timeout_sec or 420)
    except Exception:
        configured = int(default_timeout_sec or 420)
    # The intent stage should be a fast contract generator, not a long report run.
    return max(60, min(configured, 900))


def _is_completed_like_runtime_status(status: str) -> bool:
    text = str(status or "").strip().lower()
    return text == "completed" or text.startswith("completed_")

HEAVY_METADATA_KEYS = {
    "chart_bundle",
    "scatter",
    "scatter_points",
    "points",
    "rows",
    "records",
    "data",
    "values",
    "table_data",
    "preview_rows",
    "raw_rows",
}


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if pd.isna(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return str(value)


def _clip_text(value: Any, limit: int = 3000) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _is_requirement_empty(request: SmartReportRequest) -> bool:
    fields = [
        request.user_requirement,
        request.problem_to_solve,
        request.target_audience,
        request.core_purpose,
        request.expected_result,
        request.key_constraints,
        getattr(request, "visual_style_text", ""),
        getattr(request, "required_detail_dimensions_text", ""),
    ]
    return not any(str(item or "").strip() for item in fields)


def _column_summaries(frame: pd.DataFrame, *, max_columns: int = 60, sample_values: int = 4) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for column in list(frame.columns)[:max_columns]:
        series = frame[column]
        non_null = int(series.notna().sum())
        summary: dict[str, Any] = {
            "name": str(column),
            "dtype": str(series.dtype),
            "non_null": non_null,
            "missing": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
            "sample_values": [_json_safe(item) for item in series.dropna().head(sample_values).tolist()],
        }
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().mean() >= 0.65 and numeric.notna().any():
            summary.update(
                {
                    "numeric_min": _json_safe(float(numeric.min())),
                    "numeric_max": _json_safe(float(numeric.max())),
                    "numeric_mean": _json_safe(float(numeric.mean())),
                }
            )
        summaries.append(summary)
    return summaries


def _sample_rows(frame: pd.DataFrame, *, max_rows: int = 6) -> list[dict[str, Any]]:
    records = frame.head(max_rows).to_dict(orient="records")
    return [_json_safe(record) for record in records]


def _compact_json_value(value: Any, *, depth: int = 0, max_items: int = 12) -> Any:
    if depth >= 3:
        return _clip_text(value, 500)
    if isinstance(value, dict):
        compact: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 40:
                compact["_truncated_keys"] = max(0, len(value) - 40)
                break
            key_text = str(key)
            if key_text.lower() in HEAVY_METADATA_KEYS:
                compact[key_text] = "[omitted-heavy-metadata]"
                continue
            compact[key_text] = _compact_json_value(item, depth=depth + 1, max_items=max_items)
        return compact
    if isinstance(value, (list, tuple, set)):
        values = list(value)
        compact_values = [_compact_json_value(item, depth=depth + 1, max_items=max_items) for item in values[:max_items]]
        if len(values) > max_items:
            compact_values.append({"_truncated_items": len(values) - max_items})
        return compact_values
    if isinstance(value, str):
        return _clip_text(value, 800)
    return _json_safe(value)


def _compact_dataset_metadata(dataset_metadata: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {"metadata_keys": list(dataset_metadata.keys())[:80]}
    for key in (
        "dataset_id",
        "id",
        "name",
        "filename",
        "active_sheet",
        "sheet_name",
        "row_count",
        "column_count",
        "business_profile",
        "numeric_columns",
        "categorical_columns",
        "datetime_columns",
        "text_columns",
        "sheets",
        "quality_summary",
        "schema_summary",
        "dataset_profile",
    ):
        if key in dataset_metadata:
            compact[key] = _compact_json_value(dataset_metadata.get(key), max_items=20)
    return compact


def _requested_dimensions_from_text(text: str) -> list[str]:
    candidates = [
        "media",
        "channel",
        "terminal",
        "device",
        "brand",
        "province",
        "region",
        "placement",
        "campaign",
        "category",
        "sku",
        "product",
        "customer",
        "seller",
        "content",
        "traffic_source",
        "city_tier",
        "user_segment",
        "content_category",
        "product_module",
    ]
    lower = text.lower()
    return [item for item in candidates if item in lower]


def _detected_detail_dimensions(column_summaries: list[dict[str, Any]], request: SmartReportRequest) -> list[str]:
    explicit_text = " ".join(
        [
            getattr(request, "required_detail_dimensions_text", ""),
            request.user_requirement,
            request.problem_to_solve,
            request.key_constraints,
        ]
    )
    dimensions = _requested_dimensions_from_text(explicit_text)
    aliases = {
        "media": ["media", "媒体", "媒介"],
        "channel": ["channel", "渠道"],
        "terminal": ["terminal", "device", "终端", "设备"],
        "brand": ["brand", "品牌"],
        "province": ["province", "省份"],
        "region": ["region", "区域", "地区"],
        "placement": ["placement", "点位", "广告位"],
        "campaign": ["campaign", "活动"],
        "category": ["category", "类目", "品类"],
        "sku": ["sku"],
        "product": ["product", "商品", "产品"],
        "customer": ["customer", "客户", "用户"],
        "seller": ["seller", "商家"],
        "content": ["content", "内容"],
        "traffic_source": ["traffic_source", "traffic source", "source", "utm_source"],
        "city_tier": ["city_tier", "city tier", "tier"],
        "user_segment": ["user_segment", "user segment", "segment"],
        "content_category": ["content_category", "content category", "theme"],
        "product_module": ["product_module", "product module", "module"],
    }
    for summary in column_summaries:
        name = str(summary.get("name") or "").lower()
        for canonical, tokens in aliases.items():
            if any(token.lower() in name for token in tokens) and canonical not in dimensions:
                dimensions.append(canonical)
    return dimensions[:10]


def _fallback_intent(
    *,
    request: SmartReportRequest,
    dataset_metadata: dict[str, Any],
    sheet_name: str,
    column_summaries: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    raw_requirement = "；".join(
        item
        for item in [
            request.user_requirement.strip(),
            request.problem_to_solve.strip(),
            request.core_purpose.strip(),
            request.expected_result.strip(),
        ]
        if item
    )
    dataset_name = str(dataset_metadata.get("name") or dataset_metadata.get("filename") or "当前数据集")
    optimized = raw_requirement or f"基于 `{dataset_name}` / `{sheet_name}` 自动生成一份可供管理层使用的深度经营分析报告。"
    style_text = str(getattr(request, "visual_style_text", "") or "").strip()
    style_preset = str(getattr(request, "premium_style_preset", "") or DEFAULT_LAYOUT_PRESET_ID)
    layout_preset = REPORT_LAYOUT_PRESETS.get(style_preset) or REPORT_LAYOUT_PRESETS[DEFAULT_LAYOUT_PRESET_ID]
    layout_name = str(layout_preset.get("name") or "中文财经内参")
    chart_palette_preset = str(getattr(request, "chart_palette_preset", "") or "cn_editorial_ink")
    chart_palette_colors = [
        str(item).strip()
        for item in (getattr(request, "chart_palette_colors", []) or [])
        if str(item).strip()
    ]
    dimensions = _detected_detail_dimensions(column_summaries, request)
    return {
        "optimized_user_requirement": optimized,
        "detected_business_profile": request.business_profile or "auto",
        "business_questions": [
            request.problem_to_solve.strip() or "当前数据反映的主要经营问题、机会和优先级是什么？",
            "哪些维度、类目或对象需要进入管理层行动清单？",
            "下一步应该如何安排资源、责任人与 KPI？",
        ],
        "target_audience": request.target_audience.strip() or "管理层 / 运营负责人 / 分析团队",
        "core_purpose": request.core_purpose.strip() or "形成可执行经营判断和后续行动建议",
        "expected_result": request.expected_result.strip() or "主报告 + 分析师附录 + Codex CLI 高级分析 PDF",
        "analysis_depth": "deep_dive" if request.report_style == "deep_dive" else "executive",
        "required_detail_dimensions": dimensions,
        "must_include_sections": [
            "结论先行",
            "经营诊断",
            "维度明细表",
            "管理建议",
            "30/60/90 天行动计划",
        ],
        "recommendation_style": "direct_operating_recommendations",
        "visual_style": style_text or f"采用「{layout_name}」的中文高级 PDF 版式，颜色由前端色卡控制。",
        "color_palette": style_preset,
        "layout_preference": str(layout_preset.get("page_structure") or "A4 print-friendly, premium, controlled, table-readable"),
        "chart_palette_preset": chart_palette_preset,
        "chart_palette_colors": chart_palette_colors,
        "pdf_design_brief": style_text or f"采用「{layout_name}」：{layout_preset.get('scenario') or ''}；图表和强调色使用前端色卡。",
        "forbidden_patterns": [
            "只写证据边界",
            "只给泛泛 KPI 口号",
            "把当前可分析内容推迟到下一期",
            "忽略用户指定的颜色、版式和明细类目",
        ],
        "output_contract": {
            "main_report": "Use this spec as the effective requirement for the core report.",
            "analyst_appendix_premium_pdf": "Use this spec to control depth, style, detail dimensions, and PDF design.",
            "fallback_reason": reason,
        },
    }


def _validate_intent(payload: dict[str, Any]) -> list[str]:
    missing = [field for field in REPORT_INTENT_FIELDS if field not in payload]
    if missing:
        return [f"missing required fields: {', '.join(missing)}"]
    errors: list[str] = []
    for list_field in ("business_questions", "required_detail_dimensions", "must_include_sections", "forbidden_patterns"):
        if not isinstance(payload.get(list_field), list):
            errors.append(f"{list_field} must be a list")
        elif any(isinstance(item, (dict, list, tuple, set)) for item in payload.get(list_field) or []):
            errors.append(f"{list_field} items must be scalar strings")
    for text_field in (
        "optimized_user_requirement",
        "detected_business_profile",
        "target_audience",
        "core_purpose",
        "expected_result",
        "analysis_depth",
        "recommendation_style",
        "visual_style",
        "color_palette",
        "layout_preference",
        "pdf_design_brief",
    ):
        if isinstance(payload.get(text_field), (dict, list, tuple, set)):
            errors.append(f"{text_field} must be a scalar string")
            continue
        if not str(payload.get(text_field) or "").strip():
            errors.append(f"{text_field} must be non-empty")
    if not isinstance(payload.get("output_contract"), dict):
        errors.append("output_contract must be an object")
    return errors


def _unique_text_items(items: list[Any]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        values.append(text)
    return values


def _split_list_text(value: str) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            loaded = json.loads(text)
            if isinstance(loaded, list):
                return _as_list(loaded)
        except Exception:
            pass
    normalized = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    parts = re.split(r"[\n,;|/]+|[，；、]", normalized)
    return _unique_text_items(parts)


def _as_list(value: Any, fallback: list[Any] | None = None) -> list[str]:
    fallback = fallback or []
    if value is None:
        return _unique_text_items(fallback)
    if isinstance(value, list):
        items: list[Any] = []
        for item in value:
            if isinstance(item, dict):
                label = item.get("name") or item.get("label") or item.get("dimension") or item.get("title")
                items.append(label if label is not None else json.dumps(item, ensure_ascii=False))
            elif isinstance(item, (list, tuple, set)):
                items.extend(item)
            else:
                items.append(item)
        normalized = _unique_text_items(items)
        return normalized or _unique_text_items(fallback)
    if isinstance(value, dict):
        preferred = []
        for key in ("items", "values", "dimensions", "sections", "questions", "patterns"):
            if isinstance(value.get(key), list):
                preferred.extend(value.get(key) or [])
        if not preferred:
            preferred = list(value.values())
        normalized = _as_list(preferred)
        return normalized or _unique_text_items(fallback)
    normalized = _split_list_text(str(value))
    return normalized or _unique_text_items(fallback)


def _as_text(value: Any, fallback: Any = "") -> str:
    if isinstance(value, (list, tuple, set)):
        text = ", ".join(str(item).strip() for item in value if str(item).strip())
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value or "").strip()
    if text:
        return text
    return str(fallback or "").strip()


def _normalize_color_palette(value: Any, fallback_preset: str) -> str:
    text = _as_text(value).lower()
    if text in REPORT_LAYOUT_PRESETS:
        return text
    if any(token in text for token in ("中文", "内参", "finance editorial", "editorial brief", "cn editorial")):
        return "chinese_finance_editorial"
    if any(token in text for token in ("navy", "blue", "premium", "deep blue")):
        return "navy_white_premium"
    if any(token in text for token in ("black_white", "black white", "editorial", "monochrome")):
        return "black_white_editorial"
    if text:
        return _as_text(value)
    return fallback_preset if fallback_preset in REPORT_LAYOUT_PRESETS else DEFAULT_LAYOUT_PRESET_ID


def _normalize_output_contract(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        contract = dict(value)
    elif value:
        contract = {"summary": _as_text(value)}
    else:
        contract = {}
    contract.setdefault("main_report", "Use this spec as the effective requirement for the core report.")
    contract.setdefault(
        "analyst_appendix_premium_pdf",
        "Use this spec to control depth, style, detail dimensions, and PDF design.",
    )
    return contract


def _enrich_intent_with_frontend_context(payload: dict[str, Any], frontend_context_pack: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(payload or {})
    pack = frontend_context_pack if isinstance(frontend_context_pack, dict) else {}
    directives = pack.get("context_directives") if isinstance(pack.get("context_directives"), dict) else {}
    background = pack.get("business_background") if isinstance(pack.get("business_background"), dict) else {}
    historical = pack.get("historical_reference") if isinstance(pack.get("historical_reference"), dict) else {}

    must_answer = _unique_text_items(
        [
            *list(enriched.get("business_questions") or []),
            *list(directives.get("must_answer") or []),
        ]
    )
    if must_answer:
        enriched["business_questions"] = must_answer[:6]

    required_dimensions = _unique_text_items(
        [
            *list(enriched.get("required_detail_dimensions") or []),
            *list(directives.get("detail_dimension_hints") or []),
        ]
    )
    if required_dimensions:
        enriched["required_detail_dimensions"] = required_dimensions[:16]

    must_preserve = _unique_text_items(list(directives.get("must_preserve") or []))
    tone_preferences = _unique_text_items(
        [
            *list(directives.get("tone_preferences") or []),
            *list(historical.get("tone_cues") or []),
        ]
    )
    summary_bullets = _unique_text_items(list(background.get("summary_bullets") or []))
    structure_cues = _unique_text_items(
        [
            *list(historical.get("structure_cues") or []),
            *list(historical.get("summary_bullets") or []),
        ]
    )
    domain_lexicon = _unique_text_items(list(pack.get("domain_lexicon") or []))

    output_contract = _normalize_output_contract(enriched.get("output_contract"))
    output_contract["frontend_context_priority"] = (
        "Prioritize frontend_context_pack over generic dataset inference when audience, purpose, scope, style, or detail dimensions conflict."
    )
    if must_preserve:
        output_contract["must_preserve_context"] = must_preserve[:5]
    if tone_preferences:
        output_contract["tone_preferences"] = tone_preferences[:5]
    if summary_bullets:
        output_contract["business_background_summary"] = summary_bullets[:4]
    if structure_cues:
        output_contract["historical_reference_cues"] = structure_cues[:4]
    if domain_lexicon:
        output_contract["domain_lexicon"] = domain_lexicon[:10]
    if pack.get("context_brief"):
        output_contract["context_brief"] = str(pack.get("context_brief") or "")
    enriched["output_contract"] = output_contract

    enriched["business_context_summary"] = str(pack.get("context_brief") or enriched.get("business_context_summary") or "")
    enriched["business_background_summary"] = summary_bullets[:5]
    enriched["historical_reference_cues"] = structure_cues[:5]
    enriched["must_preserve_context"] = must_preserve[:5]
    enriched["domain_lexicon"] = domain_lexicon[:12]
    return enriched


def _extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text or ""):
        try:
            loaded, _ = decoder.raw_decode(text[match.start() :])
        except Exception:
            continue
        if isinstance(loaded, dict):
            return loaded
    return None


def _load_intent_payload(json_path: Path, md_path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if json_path.exists():
        raw = json_path.read_text(encoding="utf-8-sig")
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                return loaded, []
            errors.append("intent JSON must be an object")
        except Exception as exc:
            errors.append(f"invalid intent JSON: {exc}")
            extracted = _extract_json_object(raw)
            if extracted is not None:
                errors.append("intent JSON recovered from invalid file text")
                return extracted, errors
    else:
        errors.append("00_requirement_intent.json was not created")
    if md_path.exists():
        extracted = _extract_json_object(md_path.read_text(encoding="utf-8", errors="ignore"))
        if extracted is not None:
            errors.append("intent JSON recovered from markdown")
            return extracted, errors
    return None, errors


def _write_repair_metadata(workspace: Path, metadata: dict[str, Any]) -> str:
    path = workspace / "00_requirement_intent_repair.json"
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())


def _write_raw_intent_copy(workspace: Path, payload: dict[str, Any]) -> str:
    path = workspace / "00_requirement_intent.raw.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())


def _repair_intent_payload(
    payload: dict[str, Any],
    *,
    request: SmartReportRequest,
    dataset_metadata: dict[str, Any],
    sheet_name: str,
    column_summaries: list[dict[str, Any]],
    validation_errors: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline = _fallback_intent(
        request=request,
        dataset_metadata=dataset_metadata,
        sheet_name=sheet_name,
        column_summaries=column_summaries,
        reason="repair-fill-defaults",
    )
    repaired = dict(payload or {})
    actions: list[str] = []

    for field in REPORT_INTENT_FIELDS:
        if field not in repaired or repaired.get(field) is None:
            repaired[field] = baseline.get(field)
            actions.append(f"fill_missing:{field}")

    for field in LIST_INTENT_FIELDS:
        before = repaired.get(field)
        repaired[field] = _as_list(before, baseline.get(field) if isinstance(baseline.get(field), list) else [])
        if repaired[field] != before:
            actions.append(f"normalize_list:{field}")

    detected_dimensions = _detected_detail_dimensions(column_summaries, request)
    dimension_items = _as_list(repaired.get("required_detail_dimensions"), detected_dimensions)
    for item in detected_dimensions:
        if item not in dimension_items:
            dimension_items.append(item)
            actions.append(f"add_detected_dimension:{item}")
    repaired["required_detail_dimensions"] = _unique_text_items(dimension_items)[:16]

    for field in TEXT_INTENT_FIELDS:
        before = repaired.get(field)
        repaired[field] = _as_text(before, baseline.get(field))
        if repaired[field] != before:
            actions.append(f"normalize_text:{field}")

    repaired["color_palette"] = _normalize_color_palette(
        repaired.get("color_palette"),
        str(getattr(request, "premium_style_preset", "") or DEFAULT_LAYOUT_PRESET_ID),
    )
    repaired["output_contract"] = _normalize_output_contract(repaired.get("output_contract"))
    repaired["output_contract"]["intent_repair_status"] = "repaired_from_codex_cli_output"
    repaired["output_contract"]["validation_errors_before_repair"] = validation_errors

    return repaired, {
        "status": "repaired_from_codex_cli_output",
        "validation_errors_before_repair": validation_errors,
        "repair_actions": _unique_text_items(actions),
    }


def _write_intent_files(workspace: Path, payload: dict[str, Any], markdown: str) -> dict[str, str]:
    workspace.mkdir(parents=True, exist_ok=True)
    md_path = workspace / "00_requirement_intent.md"
    json_path = workspace / "00_requirement_intent.json"
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "markdown_path": str(md_path.resolve()),
        "json_path": str(json_path.resolve()),
    }


def _intent_markdown(payload: dict[str, Any], *, source: str) -> str:
    questions = "\n".join(f"- {item}" for item in payload.get("business_questions") or [])
    dimensions = ", ".join(str(item) for item in payload.get("required_detail_dimensions") or []) or "未明确"
    sections = "\n".join(f"- {item}" for item in payload.get("must_include_sections") or [])
    return (
        "# ReportIntentSpec\n\n"
        f"- 来源：{source}\n"
        f"- 优化后需求：{payload.get('optimized_user_requirement')}\n"
        f"- 目标受众：{payload.get('target_audience')}\n"
        f"- 核心目的：{payload.get('core_purpose')}\n"
        f"- 预期结果：{payload.get('expected_result')}\n"
        f"- 视觉方向：{payload.get('visual_style')}\n"
        f"- 色彩/版式：{payload.get('color_palette')} / {payload.get('layout_preference')}\n"
        f"- 明细维度：{dimensions}\n\n"
        "## 必须回答的问题\n\n"
        f"{questions or '- 未明确'}\n\n"
        "## 必须包含的模块\n\n"
        f"{sections or '- 未明确'}\n"
    )


def apply_report_intent_to_request(request: SmartReportRequest, intent: dict[str, Any]) -> SmartReportRequest:
    payload = dict(request.model_dump())
    payload["raw_user_requirement"] = payload.get("raw_user_requirement") or request.user_requirement
    payload["raw_problem_to_solve"] = payload.get("raw_problem_to_solve") or request.problem_to_solve
    payload["raw_target_audience"] = payload.get("raw_target_audience") or request.target_audience
    optimized = str(intent.get("optimized_user_requirement") or "").strip()
    if optimized:
        payload["user_requirement"] = optimized
        payload["problem_to_solve"] = optimized
    for key in ("target_audience", "core_purpose", "expected_result"):
        value = str(intent.get(key) or "").strip()
        if value:
            payload[key] = value
    visual_style = str(intent.get("visual_style") or "").strip()
    if visual_style:
        payload["visual_style_text"] = visual_style
    dimensions = intent.get("required_detail_dimensions")
    if isinstance(dimensions, list) and dimensions:
        payload["required_detail_dimensions_text"] = ", ".join(str(item) for item in dimensions if str(item).strip())
    color_palette = str(intent.get("color_palette") or "").strip()
    if color_palette in REPORT_LAYOUT_PRESETS:
        payload["premium_style_preset"] = color_palette
    chart_palette_preset = str(intent.get("chart_palette_preset") or "").strip()
    if chart_palette_preset and not str(getattr(request, "chart_palette_preset", "") or "").strip():
        payload["chart_palette_preset"] = chart_palette_preset
    chart_palette_colors = intent.get("chart_palette_colors")
    if isinstance(chart_palette_colors, list) and not list(getattr(request, "chart_palette_colors", []) or []):
        payload["chart_palette_colors"] = [str(item).strip() for item in chart_palette_colors if str(item).strip()]
    return SmartReportRequest(**payload)


def generate_requirement_intent(
    *,
    workspace_path: str | Path,
    request: SmartReportRequest,
    dataset_metadata: dict[str, Any],
    sheet_name: str,
    frame: pd.DataFrame,
    report_id: str = "",
    timeout_sec: int = 900,
    stage_listener: Any | None = None,
    parent_report_job_id: str = "",
    runtime_child_task_creator: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    md_path = workspace / "00_requirement_intent.md"
    json_path = workspace / "00_requirement_intent.json"
    frontend_context_artifacts = write_frontend_context_pack_files(workspace, request)
    frontend_context_pack = dict(frontend_context_artifacts.get("pack") or {})
    request_payload = dict(request.model_dump())
    request_payload["frontend_context_pack"] = frontend_context_pack
    request_payload["frontend_context_brief"] = str(frontend_context_pack.get("context_brief") or "")
    request_payload["business_background_text"] = _clip_text(request_payload.get("business_background_text"), 5000)
    request_payload["historical_report_text"] = _clip_text(request_payload.get("historical_report_text"), 5000)
    columns = _column_summaries(frame)
    samples = _sample_rows(frame)
    compact_metadata = _compact_dataset_metadata(dataset_metadata)
    is_empty = _is_requirement_empty(request)
    prompt = build_requirement_intent_prompt(
        workspace_path=str(workspace),
        request_payload=request_payload,
        dataset_metadata=compact_metadata,
        sheet_name=sheet_name,
        column_summaries=columns,
        sample_rows=samples,
        user_requirement_is_empty=is_empty,
        language=request.report_language,
        frontend_context_pack_path=str(frontend_context_artifacts.get("json_path") or ""),
        frontend_context_pack_markdown_path=str(frontend_context_artifacts.get("markdown_path") or ""),
    )

    run_result: dict[str, Any] = {}
    runtime_status = "completed"
    error = ""
    effective_timeout_sec = _requirement_intent_timeout(timeout_sec)
    run_request = CodexRunRequest(
        workspace_path=str(workspace),
        prompt=prompt,
        report_id=report_id,
        parent_report_id=report_id,
        parent_report_job_id=str(parent_report_job_id or "").strip(),
        parent_stage_id="requirement_intent",
        stage_id="requirement_intent",
        purpose="smart_report:requirement_intent",
        artifact_source="00_requirement_intent.json",
        timeout_sec=effective_timeout_sec,
        capture_git_diff=True,
        dangerously_bypass_approvals_and_sandbox=False,
    )
    try:
        if runtime_child_task_creator is not None:
            child_task = runtime_child_task_creator(
                run_request,
                parent_report_id=report_id,
                parent_stage_id="requirement_intent",
                stage_id="requirement_intent",
                purpose="smart_report:requirement_intent",
                artifact_source="00_requirement_intent.json",
                stage_listener=stage_listener,
            )
            child_job_id = str(child_task.get("job_id") or "").strip()
            run_result = dict(child_task)
            deadline = time.time() + float(effective_timeout_sec)
            terminal = {"completed", "failed", "cancelled", "timed_out"}
            artifact_ready_since = 0.0
            last_artifact_size = -1
            while time.time() < deadline:
                try:
                    run_result = get_codex_run_task(child_job_id) if child_job_id else dict(run_result)
                except Exception as exc:
                    error = str(exc)
                    break
                status = str(run_result.get("status") or "").strip().lower()
                if status in terminal:
                    break
                try:
                    current_size = int(json_path.stat().st_size) if json_path.exists() else 0
                except Exception:
                    current_size = 0
                if current_size > 0 and current_size == last_artifact_size:
                    if artifact_ready_since <= 0:
                        artifact_ready_since = time.time()
                    elif time.time() - artifact_ready_since >= 2.0:
                        try:
                            candidate_intent, candidate_errors = _load_intent_payload(json_path, md_path)
                            candidate_errors = list(candidate_errors)
                            if candidate_intent is not None:
                                candidate_errors.extend(_validate_intent(candidate_intent))
                            if candidate_intent is not None and not candidate_errors:
                                runtime_status = "completed_artifact_ready"
                                try:
                                    cancel_codex_run_task(child_job_id)
                                except Exception:
                                    pass
                                break
                        except Exception:
                            artifact_ready_since = 0.0
                else:
                    artifact_ready_since = 0.0
                    last_artifact_size = current_size
                time.sleep(0.5)
            final_status = str(run_result.get("status") or "").strip().lower()
            if runtime_status != "completed_artifact_ready" and final_status and final_status != "completed":
                runtime_status = final_status
                error = error or str(run_result.get("error") or "")
        else:
            run_result = run_headless_codex(
                run_request,
                stage_listener=stage_listener,
            )
            final_status = str(run_result.get("status") or "").strip().lower()
            if final_status and final_status != "completed":
                runtime_status = final_status
                error = str(run_result.get("error") or "")
    except Exception as exc:
        runtime_status = "failed/fallback"
        error = str(exc)

    intent: dict[str, Any] | None = None
    validation_errors: list[str] = []
    repair_metadata: dict[str, Any] = {}
    raw_json_path = ""
    repair_json_path = ""
    intent, load_errors = _load_intent_payload(json_path, md_path)
    validation_errors = list(load_errors)
    if intent is not None:
        raw_json_path = _write_raw_intent_copy(workspace, intent)
        validation_errors.extend(_validate_intent(intent))

    if intent is None or validation_errors:
        if intent is not None:
            repaired, repair_metadata = _repair_intent_payload(
                intent,
                request=request,
                dataset_metadata=compact_metadata,
                sheet_name=sheet_name,
                column_summaries=columns,
                validation_errors=validation_errors,
            )
            repaired_errors = _validate_intent(repaired)
            repair_metadata["validation_errors_after_repair"] = repaired_errors
            repair_metadata["run_id"] = str(run_result.get("run_id") or "")
            repair_json_path = _write_repair_metadata(workspace, repair_metadata)
            if not repaired_errors:
                intent = repaired
                artifacts = _write_intent_files(
                    workspace,
                    intent,
                    md_path.read_text(encoding="utf-8", errors="ignore")
                    if md_path.exists() and md_path.stat().st_size > 0
                    else _intent_markdown(intent, source="codex_cli_runtime_repaired"),
                )
                runtime_status = (
                    "completed_repaired"
                    if _is_completed_like_runtime_status(runtime_status)
                    else "completed_repaired_after_runtime_error"
                )
            else:
                fallback_reason = error or "; ".join(repaired_errors) or "runtime output repair failed"
                intent = _fallback_intent(
                    request=request,
                    dataset_metadata=compact_metadata,
                    sheet_name=sheet_name,
                    column_summaries=columns,
                    reason=fallback_reason,
                )
                artifacts = _write_intent_files(
                    workspace,
                    intent,
                    _intent_markdown(intent, source=f"fallback after Codex CLI repair issue: {fallback_reason}"),
                )
                runtime_status = "fallback" if _is_completed_like_runtime_status(runtime_status) else runtime_status
        else:
            fallback_reason = error or "; ".join(validation_errors) or "runtime output validation failed"
            intent = _fallback_intent(
                request=request,
                dataset_metadata=compact_metadata,
                sheet_name=sheet_name,
                column_summaries=columns,
                reason=fallback_reason,
            )
            artifacts = _write_intent_files(
                workspace,
                intent,
                _intent_markdown(intent, source=f"fallback after Codex CLI issue: {fallback_reason}"),
            )
            runtime_status = "fallback" if _is_completed_like_runtime_status(runtime_status) else runtime_status
    else:
        if not md_path.exists() or md_path.stat().st_size <= 0:
            md_path.write_text(_intent_markdown(intent, source="codex_cli_runtime"), encoding="utf-8")
        artifacts = {
            "markdown_path": str(md_path.resolve()),
            "json_path": str(json_path.resolve()),
        }
    if intent is not None:
        intent = _enrich_intent_with_frontend_context(intent, frontend_context_pack)
        markdown_source = (
            md_path.read_text(encoding="utf-8", errors="ignore")
            if md_path.exists() and md_path.stat().st_size > 0
            else _intent_markdown(intent, source="codex_cli_runtime")
        )
        artifacts = _write_intent_files(workspace, intent, markdown_source)
    if raw_json_path:
        artifacts["raw_json_path"] = raw_json_path
    if repair_json_path:
        artifacts["repair_json_path"] = repair_json_path
    artifacts["frontend_context_pack_json_path"] = str(frontend_context_artifacts.get("json_path") or "")
    artifacts["frontend_context_pack_markdown_path"] = str(frontend_context_artifacts.get("markdown_path") or "")

    return {
        "intent": intent,
        "effective_request": apply_report_intent_to_request(request, intent),
        "artifacts": artifacts,
        "runtime_status": runtime_status,
        "run_result": run_result,
        "run_id": str(run_result.get("run_id") or ""),
        "session_id": str(run_result.get("session_id") or ""),
        "error": error,
        "validation_errors": validation_errors,
        "repair_metadata": repair_metadata,
        "workspace_path": str(workspace),
        "user_requirement_was_empty": is_empty,
        "frontend_context_pack": frontend_context_pack,
    }
