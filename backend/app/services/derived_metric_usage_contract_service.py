from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


CONTRACT_FILENAME = "derived_metric_usage_contract.json"
SUMMARY_FILENAME = "derived_metric_usage_summary.json"

_DERIVED_HINT_RE = re.compile(r"(derived|custom|ratio|rate|gap|score|index|派生|衍生|自定义|综合|得分|转化|率|差额|指数)", re.I)
_FAILED_STATUS = {"failed", "failure", "error", "errored", "skipped", "skip", "blocked"}
_PLANNED_STATUS = {"planned", "planned_only", "draft", "candidate", "pending", "todo"}
_EXECUTED_SOURCES = {
    "custom_metric_values.csv",
    "derived_metric_execution_review.json",
    "03_custom_metric_execution.json",
}


def _safe_text(value: Any) -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except Exception:
            continue
    return []


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _first_text(item: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        text = _safe_text(item.get(key))
        if text:
            return text
    return ""


def _normalize_metric_id(text: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", text.strip())
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:96]


def _has_concrete_value(item: dict[str, Any]) -> bool:
    for key in ("value", "current_value", "metric_value", "computed_value", "mean", "ratio", "score", "non_null_count"):
        if _safe_text(item.get(key)):
            return True
    return False


def _source_name(source: str) -> str:
    return Path(str(source or "")).name


def _status_for(item: dict[str, Any], source: str, status_hint: str = "") -> str:
    raw_status = _safe_text(
        status_hint
        or item.get("status")
        or item.get("execution_status")
        or item.get("runtime_status")
        or item.get("derivation_status")
        or item.get("result_status")
    ).lower()
    if raw_status in _FAILED_STATUS or any(token in raw_status for token in _FAILED_STATUS):
        return "skipped" if "skip" in raw_status else "failed"
    if raw_status in _PLANNED_STATUS or any(token in raw_status for token in _PLANNED_STATUS):
        return "planned_only"
    source_file = _source_name(source)
    if _has_concrete_value(item) or source_file in _EXECUTED_SOURCES:
        return "executed"
    if "execution" in source_file and source_file.endswith(".json"):
        return "executed"
    return "planned_only"


def _is_metric_like(item: dict[str, Any]) -> bool:
    values = " ".join(_safe_text(value) for value in item.values())
    if not values:
        return False
    if any(_safe_text(item.get(key)) for key in ("metric_id", "metric_raw_key", "metric_name", "raw_key", "formula", "expression", "localized_label")):
        return True
    return bool(_DERIVED_HINT_RE.search(values))


def normalize_derived_metric_row(item: dict[str, Any], *, source: str, status_hint: str = "") -> dict[str, Any] | None:
    if not isinstance(item, dict) or not _is_metric_like(item):
        return None
    metric_id = _first_text(item, ["metric_id", "metric_raw_key", "raw_key", "id", "name", "metric_name", "localized_label", "metric"])
    metric_name = _first_text(item, ["metric_name", "localized_label", "metric_localized_label", "label", "name", "metric", "raw_key"])
    if not metric_id and not metric_name:
        return None
    metric_id = _normalize_metric_id(metric_id or metric_name)
    metric_name = metric_name or metric_id
    status = _status_for(item, source, status_hint)
    source_columns = item.get("source_columns") or item.get("input_columns") or item.get("required_fields") or item.get("columns") or []
    if isinstance(source_columns, str):
        source_columns = [part.strip() for part in re.split(r"[,;/|]", source_columns) if part.strip()]
    source_columns = [_safe_text(value) for value in _as_list(source_columns) if _safe_text(value)]
    value = _first_text(item, ["value", "current_value", "metric_value", "computed_value", "mean", "ratio", "score"])
    comparison = _first_text(item, ["comparison", "benchmark", "threshold_or_comparison", "lift", "rank", "business_interpretation"])
    can_support_current_fact = status == "executed" and bool(value or comparison)
    return {
        "metric_id": metric_id,
        "metric_name": metric_name,
        "metric_kind": _first_text(item, ["metric_kind", "kind", "type"]) or "derived_metric",
        "status": status,
        "source": source,
        "formula": _first_text(item, ["formula", "expression", "calculation", "definition"]),
        "source_columns": source_columns,
        "business_meaning": _first_text(item, ["business_meaning", "management_impact", "description", "purpose", "reason"]),
        "value": value,
        "comparison": comparison,
        "evidence_strength": _first_text(item, ["evidence_strength", "confidence", "quality"]) or ("high" if status == "executed" else "medium"),
        "can_support_current_fact": can_support_current_fact,
        "can_support_visual": status == "executed",
        "usage_policy": (
            "may_support_current_facts_charts_and_recommendations"
            if status == "executed"
            else "may_support_method_definition_and_pending_execution_only"
            if status == "planned_only"
            else "must_not_be_written_as_current_fact"
        ),
    }


def _merge_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    priority = {"executed": 4, "planned_only": 3, "skipped": 2, "failed": 1}
    for row in rows:
        metric_id = _safe_text(row.get("metric_id"))
        if not metric_id:
            continue
        existing = merged.get(metric_id)
        if not existing:
            merged[metric_id] = dict(row)
            continue
        if priority.get(str(row.get("status")), 0) >= priority.get(str(existing.get("status")), 0):
            updated = {**existing, **{key: value for key, value in row.items() if value not in ("", [], None)}}
            updated["source"] = ";".join(dict.fromkeys([*str(existing.get("source") or "").split(";"), str(row.get("source") or "")]))
            merged[metric_id] = updated
    return sorted(merged.values(), key=lambda row: (row.get("status") != "executed", str(row.get("metric_id") or "")))


def _rows_from_json_payload(payload: Any, source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        for key in ("metrics", "derived_metrics", "custom_metrics", "metric_rows", "rows", "items"):
            for item in _as_list(payload.get(key)):
                if isinstance(item, dict):
                    row = normalize_derived_metric_row(item, source=source)
                    if row:
                        rows.append(row)
        if _is_metric_like(payload):
            row = normalize_derived_metric_row(payload, source=source)
            if row:
                rows.append(row)
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                row = normalize_derived_metric_row(item, source=source)
                if row:
                    rows.append(row)
    return rows


def _context_metric_rows(value: Any, source: str = "context_payload") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_source = f"{source}.{key}"
            if any(token in key.lower() for token in ("derived", "custom", "metric_derivation", "metric_execution")):
                rows.extend(_rows_from_json_payload(child, key_source))
            elif isinstance(child, (dict, list)):
                rows.extend(_context_metric_rows(child, key_source))
    elif isinstance(value, list):
        for index, child in enumerate(value[:200]):
            if isinstance(child, (dict, list)):
                rows.extend(_context_metric_rows(child, f"{source}[{index}]"))
    return rows


def collect_derived_metric_usage_contract(
    *,
    workspace: Path,
    context_payload: dict[str, Any] | None = None,
    metric_rows: list[dict[str, Any]] | None = None,
    metric_execution: dict[str, Any] | None = None,
    historical_inventory: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    workspace = Path(workspace)
    rows: list[dict[str, Any]] = []
    for item in metric_rows or []:
        row = normalize_derived_metric_row(item, source="generic_long_metric_rows", status_hint="executed")
        if row:
            rows.append(row)
    rows.extend(_rows_from_json_payload(metric_execution or {}, "derived_metric_execution_review.json"))
    rows.extend(_rows_from_json_payload(historical_inventory or {}, "historical_derived_metric_inventory.json"))
    if context_payload:
        rows.extend(_context_metric_rows(context_payload))

    known_files = [
        "derived_metrics_table.csv",
        "custom_metric_values.csv",
        "03_custom_metric_execution.json",
        "metric_derivation_plan.json",
        "derived_metric_execution_review.json",
        "historical_derived_metric_inventory.json",
        "metric_mining/derived_metrics_table.csv",
        "metric_mining/universal_metric_mining_result.json",
        "outputs/metric_mining/derived_metrics_table.csv",
        "outputs/metric_mining/universal_metric_mining_result.json",
    ]
    for relative in known_files:
        path = workspace / relative
        if path.suffix.lower() == ".csv":
            for item in _read_csv_rows(path):
                row = normalize_derived_metric_row(item, source=relative)
                if row:
                    rows.append(row)
        elif path.suffix.lower() == ".json":
            rows.extend(_rows_from_json_payload(_read_json(path), relative))

    metrics = _merge_metric_rows(rows)
    executed = [row for row in metrics if row.get("status") == "executed"]
    planned_only = [row for row in metrics if row.get("status") == "planned_only"]
    failed = [row for row in metrics if row.get("status") in {"failed", "skipped"}]
    executable_for_gate = executed or planned_only
    required_metrics = executable_for_gate[: min(3, len(executable_for_gate))]
    contract_path = output_path or (workspace / CONTRACT_FILENAME)
    payload = {
        "version": "derived-metric-usage-contract-v1",
        "contract_path": str(contract_path.resolve()),
        "derived_metric_count": len(metrics),
        "executed_metric_count": len(executed),
        "planned_only_metric_count": len(planned_only),
        "failed_metric_count": len(failed),
        "required_metric_ids": [row["metric_id"] for row in required_metrics],
        "required_metric_names": [row["metric_name"] for row in required_metrics],
        "metrics": metrics,
        "usage_gate": {
            "enabled": bool(metrics),
            "minimum_body_metric_count": min(3, len(metrics)),
            "minimum_recommendation_metric_count": 1 if metrics else 0,
            "minimum_asset_metric_count": 1 if executed else 0,
            "fact_eligible_metric_ids": [row["metric_id"] for row in executed],
            "planned_only_metric_ids": [row["metric_id"] for row in planned_only],
            "failed_or_skipped_metric_ids": [row["metric_id"] for row in failed],
        },
    }
    _write_json(contract_path, payload)
    return payload


def _metric_lookup(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("metric_id") or ""): row for row in contract.get("metrics") or [] if row.get("metric_id")}


def _extract_metric_ids_from_value(value: Any, known_ids: set[str]) -> set[str]:
    used: set[str] = set()
    if isinstance(value, dict):
        metric_id = _safe_text(value.get("metric_id") or value.get("trigger_metric") or value.get("verification_metric"))
        if metric_id in known_ids:
            used.add(metric_id)
        for child in value.values():
            used.update(_extract_metric_ids_from_value(child, known_ids))
    elif isinstance(value, list):
        for child in value:
            used.update(_extract_metric_ids_from_value(child, known_ids))
    else:
        text = _safe_text(value)
        if text:
            for metric_id in known_ids:
                if metric_id and metric_id in text:
                    used.add(metric_id)
    return used


def summarize_derived_metric_usage(
    *,
    contract: dict[str, Any],
    page_plan: list[dict[str, Any]] | None = None,
    page_drafts: list[dict[str, Any]] | None = None,
    asset_coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lookup = _metric_lookup(contract)
    known_ids = set(lookup)
    used_ids: set[str] = set()
    body_ids: set[str] = set()
    recommendation_ids: set[str] = set()
    asset_ids: set[str] = set()
    for page in page_plan or []:
        for metric in page.get("derived_metrics") or []:
            metric_id = _safe_text(metric.get("metric_id") if isinstance(metric, dict) else metric)
            if metric_id in known_ids:
                used_ids.add(metric_id)
    for draft in page_drafts or []:
        explicit = _extract_metric_ids_from_value(draft.get("derived_metrics_used") or [], known_ids)
        evidence = _extract_metric_ids_from_value(draft.get("evidence") or [], known_ids)
        explanation = _extract_metric_ids_from_value(draft.get("derived_metric_explanation") or "", known_ids)
        action = _extract_metric_ids_from_value(draft.get("recommended_action") or {}, known_ids)
        body_ids.update(explicit | evidence | explanation)
        recommendation_ids.update(action)
        used_ids.update(explicit | evidence | explanation | action)
    for name in _as_list((asset_coverage or {}).get("used_derived_metric_names")):
        metric_id = _safe_text(name)
        if metric_id in known_ids:
            asset_ids.add(metric_id)
            used_ids.add(metric_id)
    gate = dict(contract.get("usage_gate") or {})
    minimum_body = int(gate.get("minimum_body_metric_count") or 0)
    minimum_recommendation = int(gate.get("minimum_recommendation_metric_count") or 0)
    minimum_asset = int(gate.get("minimum_asset_metric_count") or 0)
    issues: list[str] = []
    if gate.get("enabled"):
        if len(body_ids) < minimum_body:
            issues.append(f"derived_metric_body_coverage_below_minimum:{len(body_ids)}/{minimum_body}")
        if len(recommendation_ids) < minimum_recommendation:
            issues.append("derived_metric_recommendation_missing")
        if len(asset_ids) < minimum_asset:
            issues.append("derived_metric_asset_missing")
    missing_ids = [metric_id for metric_id in known_ids if metric_id not in used_ids]
    return {
        "derived_metric_count": int(contract.get("derived_metric_count") or len(known_ids)),
        "used_derived_metric_ids": sorted(used_ids),
        "used_derived_metric_names": [lookup[metric_id].get("metric_name") or metric_id for metric_id in sorted(used_ids)],
        "missing_derived_metric_ids": sorted(missing_ids),
        "missing_derived_metric_names": [lookup[metric_id].get("metric_name") or metric_id for metric_id in sorted(missing_ids)],
        "derived_metric_coverage_ratio": round(len(used_ids) / max(1, len(known_ids)), 4) if known_ids else 1.0,
        "body_metric_count": len(body_ids),
        "recommendation_metric_count": len(recommendation_ids),
        "asset_metric_count": len(asset_ids),
        "passes_gate": not issues,
        "issues": issues,
    }


def assert_derived_metric_usage_gate(contract: dict[str, Any], usage: dict[str, Any], *, stage_name: str) -> None:
    if not (contract.get("usage_gate") or {}).get("enabled"):
        return
    if usage.get("passes_gate"):
        return
    raise ValueError(f"{stage_name} derived metric usage gate failed: {usage.get('issues') or []}")
