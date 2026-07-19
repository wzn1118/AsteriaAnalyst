from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LOGIC_ROLE_SEQUENCE = [
    "opening_thesis",
    "business_question",
    "diagnostic_evidence",
    "driver_explanation",
    "contrast_or_segmentation",
    "management_implication",
    "recommendation",
    "appendix_support",
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _clean_text(value: Any, *, limit: int = 1000, fallback: str = "") -> str:
    text = " ".join(str(value or "").split()).strip()
    return (text or fallback)[:limit]


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"key": key, "value": item} for key, item in value.items()]
    if str(value or "").strip():
        return [str(value).strip()]
    return []


def _compact_items(value: Any, *, limit: int = 10) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in _as_list(value)[:limit]:
        if isinstance(item, dict):
            compact: dict[str, Any] = {}
            for key, raw in item.items():
                if isinstance(raw, (str, int, float, bool)) or raw is None:
                    compact[str(key)] = raw
                elif isinstance(raw, list):
                    compact[str(key)] = raw[:5]
                elif isinstance(raw, dict):
                    compact[str(key)] = {
                        str(sub_key): sub_value
                        for sub_key, sub_value in list(raw.items())[:6]
                        if isinstance(sub_value, (str, int, float, bool)) or sub_value is None
                    }
            output.append(compact)
        elif str(item or "").strip():
            output.append({"value": str(item).strip()})
    return output


def _metric_name(item: dict[str, Any]) -> str:
    return _clean_text(
        item.get("metric_label")
        or item.get("display_label")
        or item.get("localized_label")
        or item.get("metric_localized_label")
        or item.get("metric_raw_key")
        or item.get("raw_key")
        or item.get("metric")
        or item.get("name"),
        limit=120,
        fallback="核心指标",
    )


def _dimension_name(item: dict[str, Any]) -> str:
    return _clean_text(
        item.get("dimension_label")
        or item.get("dimension_raw_key")
        or item.get("dimension")
        or item.get("name"),
        limit=120,
        fallback="关键维度",
    )


def _role_purpose(role: str) -> str:
    return {
        "opening_thesis": "先给管理层结论，明确这份报告支持什么决策。",
        "business_question": "把业务问题拆清楚，避免后续页面变成无序图表堆叠。",
        "diagnostic_evidence": "用当前数据中的图表、表格或分层结果证明一个判断。",
        "driver_explanation": "解释现象背后的指标、维度、关系或异常驱动。",
        "contrast_or_segmentation": "通过分组、对比、矩阵或排名定位优先对象。",
        "management_implication": "把发现翻译成资源配置、运营动作或风险管理含义。",
        "recommendation": "沉淀本期可执行动作、优先级、复盘指标和下一步节奏。",
        "appendix_support": "承接明细表、口径、方法、字段说明和补充证据。",
    }.get(role, "承接当前报告的论证推进。")


def _argument_arc(
    *,
    reverse_spec: dict[str, Any],
    logic_reference: dict[str, Any],
) -> list[str]:
    for value in (
        reverse_spec.get("argument_arc"),
        (reverse_spec.get("logic_flow_contract") if isinstance(reverse_spec.get("logic_flow_contract"), dict) else {}).get("recommended_argument_arc"),
        logic_reference.get("argument_arc"),
        (logic_reference.get("logic_flow_contract") if isinstance(logic_reference.get("logic_flow_contract"), dict) else {}).get("recommended_argument_arc"),
    ):
        items = [str(item).strip() for item in _as_list(value) if str(item).strip()]
        if items:
            return items
    return list(LOGIC_ROLE_SEQUENCE)


def _storyline_metric_priorities(storyline: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _compact_items(storyline.get("metric_priorities"), limit=14) if item]


def _derived_metric_priorities(workspace: Path, storyline: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = [
        item
        for item in _compact_items(storyline.get("metric_priorities"), limit=20)
        if item.get("is_derived") or str(item.get("metric_kind") or "").lower() == "derived_metric"
    ]
    path = workspace / "historical_derived_metric_inventory.json"
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            metrics.extend(_compact_items(payload.get("metrics"), limit=16))
    deduped: dict[str, dict[str, Any]] = {}
    for item in metrics:
        key = str(item.get("raw_key") or item.get("metric_raw_key") or item.get("metric") or item.get("name") or "").strip()
        if key:
            deduped[key] = {**deduped.get(key, {}), **item, "is_derived": True, "metric_kind": "derived_metric"}
    return list(deduped.values())


def _storyline_dimension_priorities(storyline: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _compact_items(storyline.get("dimension_priorities"), limit=12) if item]


def _build_logic_modules(
    *,
    arc: list[str],
    metrics: list[dict[str, Any]],
    dimensions: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    metric_cursor = 0
    dimension_cursor = 0
    action_cursor = 0
    for index, role in enumerate(arc, start=1):
        module_metrics = metrics[metric_cursor : metric_cursor + 3] if role not in {"cover_page", "appendix_support"} else []
        module_dimensions = dimensions[dimension_cursor : dimension_cursor + 2] if role in {"diagnostic_evidence", "driver_explanation", "contrast_or_segmentation", "management_implication"} else []
        module_actions = actions[action_cursor : action_cursor + 3] if role in {"management_implication", "recommendation"} else []
        metric_cursor += len(module_metrics)
        dimension_cursor += len(module_dimensions)
        action_cursor += len(module_actions)
        modules.append(
            {
                "module_id": f"logic_module_{index:02d}",
                "logic_role": role,
                "purpose": _role_purpose(role),
                "must_answer": _module_question(role),
                "required_metrics": [_metric_name(item) for item in module_metrics],
                "required_dimensions": [_dimension_name(item) for item in module_dimensions],
                "action_candidates": module_actions,
                "claim_evidence_action_rule": {
                    "claim": "每页先写一个可判断的管理结论。",
                    "evidence": "每个结论必须绑定当前数据证据、图表、表格、分层、关系或异常信号。",
                    "action": "每个主要发现必须落到动作、优先级、资源配置、复盘指标或下一步问题。",
                },
            }
        )
    return modules


def _module_question(role: str) -> str:
    return {
        "opening_thesis": "这份报告的最高层判断是什么？",
        "business_question": "管理层真正要回答的问题是什么？",
        "diagnostic_evidence": "当前数据最强的证据支持哪个判断？",
        "driver_explanation": "什么因素正在驱动差异、增长、下降或风险？",
        "contrast_or_segmentation": "哪些对象领先、落后、分化，应该优先处理？",
        "management_implication": "这些发现对预算、资源、产品、渠道或组织动作意味着什么？",
        "recommendation": "本期应该马上做什么，按什么顺序复盘？",
        "appendix_support": "哪些明细、口径和方法支撑主报告判断？",
    }.get(role, "这一页应该推动哪个管理判断？")


def _recommendation_backbone(actions: list[dict[str, Any]], dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, item in enumerate(actions[:10], start=1):
        output.append(
            {
                "rank": index,
                "action_type": _clean_text(item.get("action_type") or item.get("type"), limit=120, fallback="经营动作"),
                "target_object": _clean_text(item.get("object_label") or item.get("candidate_id"), limit=160, fallback="重点对象"),
                "priority": _clean_text(item.get("priority"), limit=80, fallback="medium"),
                "evidence_source": _clean_text(item.get("evidence_source"), limit=180, fallback="data_storyline_scan"),
                "follow_up_metric": _metric_name(item),
            }
        )
    if output:
        return output
    for index, item in enumerate(dimensions[:6], start=1):
        output.append(
            {
                "rank": index,
                "action_type": "分层复盘",
                "target_object": _dimension_name(item),
                "priority": "medium",
                "evidence_source": "dimension_priorities",
                "follow_up_metric": "对应核心指标",
            }
        )
    return output


def build_historical_report_logic_blueprint(
    *,
    workspace: Path,
    reverse_spec: dict[str, Any],
    logic_reference: dict[str, Any],
    data_storyline: dict[str, Any],
    data_manifest: dict[str, Any],
    current_context: dict[str, Any],
    json_output_path: Path,
    markdown_output_path: Path,
) -> dict[str, Any]:
    """Build a deterministic argument blueprint for historical-style reports."""
    arc = _argument_arc(reverse_spec=reverse_spec, logic_reference=logic_reference)
    metrics = _storyline_metric_priorities(data_storyline)
    derived_metrics = _derived_metric_priorities(workspace, data_storyline)
    for item in reversed(derived_metrics[:6]):
        key = str(item.get("raw_key") or item.get("metric_raw_key") or "").strip()
        if key and not any(str(metric.get("raw_key") or metric.get("metric_raw_key") or "") == key for metric in metrics):
            metrics.insert(0, item)
    dimensions = _storyline_dimension_priorities(data_storyline)
    actions = _compact_items(data_storyline.get("action_candidates"), limit=16)
    logic_modules = _build_logic_modules(
        arc=arc,
        metrics=metrics,
        dimensions=dimensions,
        actions=actions,
    )
    headline = _clean_text(
        data_storyline.get("headline_data_story")
        or current_context.get("executive_summary")
        or current_context.get("core_purpose"),
        limit=800,
        fallback="当前数据需要形成一条从核心判断到证据、原因、启示和行动的管理层报告逻辑。",
    )
    payload = {
        "version": "historical-report-logic-blueprint-v1",
        "workspace_path": str(workspace.resolve()),
        "historical_report_family": _clean_text(reverse_spec.get("historical_report_family"), fallback="generic_chinese_analysis_deck"),
        "dominant_logic_pattern": _clean_text(
            logic_reference.get("dominant_logic_pattern")
            or (logic_reference.get("logic_flow_contract") if isinstance(logic_reference.get("logic_flow_contract"), dict) else {}).get("dominant_logic_pattern"),
            fallback="data_led_management_argument",
        ),
        "executive_thesis_seed": headline,
        "decision_question": _clean_text(
            current_context.get("user_requirement")
            or current_context.get("core_purpose")
            or "管理层应该基于当前数据优先调整什么？",
            limit=800,
        ),
        "argument_arc": arc,
        "logic_modules": logic_modules,
        "page_role_requirements": [
            {
                "logic_role": role,
                "purpose": _role_purpose(role),
                "minimum_pages": 1 if role in {"opening_thesis", "diagnostic_evidence", "management_implication", "recommendation"} else 0,
            }
            for role in LOGIC_ROLE_SEQUENCE
        ],
        "metric_to_logic_map": [
            {
                "metric": _metric_name(item),
                "preferred_logic_roles": ["diagnostic_evidence", "driver_explanation", "management_implication"],
                "is_derived": bool(item.get("is_derived") or str(item.get("metric_kind") or "") == "derived_metric"),
                "formula": item.get("formula"),
            }
            for item in metrics[:12]
        ],
        "derived_metric_focus": [
            {
                "metric": _metric_name(item),
                "formula": item.get("formula"),
                "business_meaning": item.get("business_meaning"),
                "required_logic_roles": ["driver_explanation", "management_implication", "recommendation"],
            }
            for item in derived_metrics[:10]
        ],
        "dimension_to_logic_map": [
            {
                "dimension": _dimension_name(item),
                "preferred_logic_roles": ["contrast_or_segmentation", "driver_explanation", "recommendation"],
            }
            for item in dimensions[:10]
        ],
        "recommendation_backbone": _recommendation_backbone(actions, dimensions),
        "logic_quality_gates": {
            "must_have_opening_thesis": True,
            "must_have_diagnostic_evidence": True,
            "must_have_management_implication": True,
            "must_have_recommendation": True,
            "minimum_claim_evidence_action_pages": max(4, min(12, len(arc))),
            "minimum_metric_mentions": min(6, int(data_manifest.get("metric_count") or len(metrics) or 0)),
            "minimum_derived_metric_mentions": min(3, int(data_manifest.get("derived_metric_count") or len(derived_metrics) or 0)),
            "minimum_dimension_mentions": min(3, int(data_manifest.get("dimension_count") or len(dimensions) or 0)),
        },
        "must_avoid": [
            "不要写成松散图表说明。",
            "不要只有结论没有证据。",
            "不要只有发现没有经营动作。",
            "不要复制历史报告事实、数字、品牌或旧结论。",
        ],
        "source_paths": {
            "reverse_spec": str((workspace / "01_historical_reverse_spec.json").resolve()),
            "logic_reference": str((workspace / "historical_logic_reference.json").resolve()),
            "data_storyline_scan": str((workspace / "02_data_storyline_scan.json").resolve()),
            "data_asset_manifest": str((workspace / "historical_data_asset_manifest.json").resolve()),
            "derived_metric_inventory": str((workspace / "historical_derived_metric_inventory.json").resolve()),
        },
    }
    _write_json(json_output_path, payload)
    markdown_lines = [
        "# Historical Report Logic Blueprint",
        "",
        f"- Executive thesis seed: {payload['executive_thesis_seed']}",
        f"- Decision question: {payload['decision_question']}",
        f"- Dominant logic pattern: `{payload['dominant_logic_pattern']}`",
        f"- Argument arc: {' -> '.join(payload['argument_arc'])}",
        "",
        "## Logic Modules",
    ]
    for module in logic_modules:
        markdown_lines.append(
            f"- {module['module_id']} / {module['logic_role']}: {module['must_answer']}"
        )
    markdown_lines.extend(["", "## Recommendation Backbone"])
    for item in payload["recommendation_backbone"][:10]:
        markdown_lines.append(
            f"- P{item['rank']} {item['action_type']}: {item['target_object']} / follow-up {item['follow_up_metric']}"
        )
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.write_text("\n".join(markdown_lines).strip() + "\n", encoding="utf-8")
    return payload
