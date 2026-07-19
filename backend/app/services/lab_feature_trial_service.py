from __future__ import annotations

import csv
import json
import math
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import LabFeatureTrialRunRequest
from app.services.dataset_service import load_dataset_frame
from app.services.lab_external_skill_service import list_lab_external_skills
from app.services.path_service import PUBLIC_ARTIFACTS_DIR


TRIAL_ROOT = PUBLIC_ARTIFACTS_DIR / "lab_feature_trials"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_slug(value: str, fallback: str = "feature") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip().lower()).strip(".-")
    return slug[:80] or fallback


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _public_path(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(PUBLIC_ARTIFACTS_DIR).as_posix()
        return f"/storage/{relative}"
    except Exception:
        return ""


def _feature_items(skill: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for command in list(skill.get("commands") or []):
        if not isinstance(command, dict):
            continue
        name = str(command.get("name") or "").strip()
        if not name:
            continue
        items.append(
            {
                "feature_kind": "command",
                "feature_id": name,
                "name": name,
                "description": command.get("description") or "",
                "path": command.get("path") or "",
            }
        )
    for plugin_skill in list(skill.get("plugin_skills") or []):
        if not isinstance(plugin_skill, dict):
            continue
        feature_id = str(plugin_skill.get("id") or plugin_skill.get("path") or "").strip()
        if not feature_id:
            continue
        items.append(
            {
                "feature_kind": "embedded_skill",
                "feature_id": feature_id,
                "name": plugin_skill.get("name") or feature_id,
                "description": plugin_skill.get("description") or "",
                "path": plugin_skill.get("path") or plugin_skill.get("skill_md_path") or "",
            }
        )
    return items


def list_lab_feature_trial_catalog() -> dict[str, Any]:
    payload = list_lab_external_skills()
    plugins: list[dict[str, Any]] = []
    feature_count = 0
    for skill in list(payload.get("skills") or []):
        if not isinstance(skill, dict) or skill.get("package_kind") != "claude_plugin":
            continue
        features = _feature_items(skill)
        feature_count += len(features)
        plugins.append(
            {
                "plugin_id": skill.get("id") or "",
                "plugin_name": skill.get("name") or "",
                "plugin_version": skill.get("plugin_version") or "",
                "mounted": bool(skill.get("mounted")),
                "feature_count": len(features),
                "features": features,
            }
        )
    return {
        "contract": "analysis_lab_feature_trial_catalog_v1",
        "plugin_count": len(plugins),
        "feature_count": feature_count,
        "plugins": plugins,
    }


def _resolve_plugin_and_feature(plugin_id: str, feature_kind: str, feature_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    clean_plugin_id = str(plugin_id or "").strip()
    clean_feature_kind = str(feature_kind or "").strip()
    clean_feature_id = str(feature_id or "").strip()
    for skill in list(list_lab_external_skills().get("skills") or []):
        if not isinstance(skill, dict) or skill.get("id") != clean_plugin_id:
            continue
        features = _feature_items(skill)
        for feature in features:
            if feature.get("feature_kind") == clean_feature_kind and feature.get("feature_id") == clean_feature_id:
                return skill, feature
        raise ValueError(f"Feature not found in plugin: {clean_feature_id}")
    raise FileNotFoundError(f"Plugin not found: {clean_plugin_id}")


def _column_role(column: str) -> str:
    lower = column.lower()
    if any(token in lower for token in ["date", "time", "month", "year", "day", "period", "week"]):
        return "time"
    if any(token in lower for token in ["amount", "revenue", "sales", "cost", "price", "profit", "margin", "budget", "spend", "gmv"]):
        return "financial_metric"
    if any(token in lower for token in ["id", "code", "account", "invoice", "order", "transaction", "journal"]):
        return "identifier"
    if any(token in lower for token in ["status", "stage", "flag", "approved", "control", "risk"]):
        return "control_status"
    if any(token in lower for token in ["customer", "vendor", "supplier", "product", "category", "region", "channel", "segment", "owner"]):
        return "dimension"
    return "general"


def _feature_keywords(feature: dict[str, Any], plugin: dict[str, Any]) -> set[str]:
    text = " ".join(
        [
            str(plugin.get("name") or ""),
            str(plugin.get("description") or ""),
            str(feature.get("name") or ""),
            str(feature.get("description") or ""),
            str(feature.get("path") or ""),
        ]
    ).lower()
    tokens = {token for token in re.split(r"[^a-z0-9_]+", text) if len(token) >= 3}
    synonyms = {
        "variance": {"variance", "delta", "budget", "actual", "change", "trend", "month"},
        "reconciliation": {"reconciliation", "match", "duplicate", "amount", "invoice", "transaction", "date"},
        "journal": {"journal", "entry", "account", "debit", "credit", "amount", "date"},
        "audit": {"audit", "control", "risk", "approval", "sample", "exception"},
        "sox": {"sox", "control", "approval", "risk", "evidence", "exception"},
        "statement": {"statement", "income", "revenue", "cost", "profit", "margin"},
        "forecast": {"forecast", "trend", "date", "time", "revenue", "sales"},
        "sales": {"sales", "pipeline", "customer", "revenue", "deal", "region"},
        "marketing": {"campaign", "channel", "conversion", "spend", "revenue", "cohort"},
        "support": {"ticket", "customer", "sla", "status", "priority", "resolution"},
        "hr": {"employee", "headcount", "role", "department", "attrition", "performance"},
    }
    expanded = set(tokens)
    for token in list(tokens):
        expanded.update(synonyms.get(token, set()))
    return expanded


def _profile_frame(frame: pd.DataFrame, plugin: dict[str, Any], feature: dict[str, Any]) -> dict[str, Any]:
    numeric_columns = frame.select_dtypes(include=["number", "bool"]).columns.astype(str).tolist()
    datetime_columns = [
        str(column)
        for column in frame.columns
        if pd.api.types.is_datetime64_any_dtype(frame[column])
    ]
    categorical_columns = [
        str(column)
        for column in frame.columns.astype(str).tolist()
        if column not in numeric_columns and column not in datetime_columns
    ]
    keywords = _feature_keywords(feature, plugin)
    field_scores: list[dict[str, Any]] = []
    for column in frame.columns.astype(str).tolist():
        series = frame[column]
        lower = column.lower()
        role = _column_role(column)
        score = 8
        matched = sorted(token for token in keywords if token and token in lower)
        score += len(matched) * 18
        if role in {"financial_metric", "time", "identifier", "control_status", "dimension"}:
            score += 14
        if pd.api.types.is_numeric_dtype(series):
            score += 10
        if pd.api.types.is_datetime64_any_dtype(series):
            score += 10
        missing_rate = float(series.isna().mean()) if len(series) else 0.0
        if missing_rate < 0.1:
            score += 5
        elif missing_rate > 0.4:
            score -= 10
        field_scores.append(
            {
                "column": column,
                "role": role,
                "dtype": str(series.dtype),
                "missing_rate": round(missing_rate, 4),
                "unique_count": int(series.nunique(dropna=True)),
                "score": max(0, min(100, score)),
                "matched_keywords": matched[:8],
            }
        )
    field_scores.sort(key=lambda item: (-int(item["score"]), str(item["column"])))
    return {
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "duplicate_row_count": int(frame.duplicated().sum()) if len(frame) else 0,
        "top_fields": field_scores[:12],
        "field_scores": field_scores,
        "sample_rows": _json_safe(frame.head(8).to_dict(orient="records")),
    }


def _readiness(profile: dict[str, Any]) -> tuple[int, list[str]]:
    score = 30
    reasons: list[str] = []
    if profile["row_count"] > 0:
        score += 12
        reasons.append("dataset has readable rows")
    if profile["numeric_columns"]:
        score += 14
        reasons.append("numeric fields can support quantified enhancement")
    if profile["categorical_columns"]:
        score += 10
        reasons.append("dimension fields can segment the result")
    if profile["datetime_columns"]:
        score += 10
        reasons.append("time fields can support trend or close-period checks")
    high_fields = [item for item in profile["top_fields"] if int(item.get("score") or 0) >= 50]
    score += min(24, len(high_fields) * 4)
    if high_fields:
        reasons.append(f"{len(high_fields)} fields match the selected function strongly")
    if profile["duplicate_row_count"]:
        score += 4
        reasons.append("duplicate rows can be used for reconciliation or audit checks")
    return min(100, score), reasons[:6]


def _recommended_actions(plugin: dict[str, Any], feature: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    fields = [item["column"] for item in profile["top_fields"][:5]]
    actions = [
        f"Run `{feature.get('name')}` with plugin `{plugin.get('name')}` on this dataset once.",
        f"Use the top matched fields first: {', '.join(fields) if fields else 'no strong field match yet'}.",
        "Compare the trial summary against the baseline profile before making it part of the full Lab run.",
    ]
    if profile["datetime_columns"]:
        actions.append("Add a time split so the enhancement can show trend or period-over-period impact.")
    if profile["numeric_columns"]:
        actions.append("Export numeric before/after checks as CSV/XLSX in the full run.")
    return actions


def _trial_report_markdown(
    *,
    trial_id: str,
    plugin: dict[str, Any],
    feature: dict[str, Any],
    readiness_score: int,
    readiness_reasons: list[str],
    profile: dict[str, Any],
    actions: list[str],
) -> str:
    field_lines = [
        f"| {item['column']} | {item['role']} | {item['dtype']} | {item['score']} | {item['missing_rate']} |"
        for item in profile["top_fields"][:12]
    ]
    return "\n".join(
        [
            f"# Feature Trial: {feature.get('name')}",
            "",
            f"- Trial ID: `{trial_id}`",
            f"- Plugin: `{plugin.get('name')}` (`{plugin.get('id')}`)",
            f"- Feature kind: `{feature.get('feature_kind')}`",
            f"- Readiness score: `{readiness_score}/100`",
            "",
            "## Enhancement Effect",
            "Baseline only profiles the dataset. The selected plugin feature adds a domain-specific lens, field ranking, and a ready-to-run Lab payload for a single enhanced pass.",
            "",
            "## Readiness Reasons",
            *[f"- {item}" for item in readiness_reasons],
            "",
            "## Top Matched Fields",
            "| Field | Role | Dtype | Score | Missing rate |",
            "| --- | --- | --- | ---: | ---: |",
            *field_lines,
            "",
            "## Recommended Next Actions",
            *[f"- {item}" for item in actions],
            "",
        ]
    )


def run_lab_feature_trial(request: LabFeatureTrialRunRequest) -> dict[str, Any]:
    plugin, feature = _resolve_plugin_and_feature(request.plugin_id, request.feature_kind, request.feature_id)
    frame, metadata, sheet = load_dataset_frame(request.dataset_id, request.active_sheet or None)
    profile = _profile_frame(frame, plugin, feature)
    readiness_score, readiness_reasons = _readiness(profile)
    actions = _recommended_actions(plugin, feature, profile)
    created_at = _now_iso()
    trial_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_safe_slug(plugin.get('id') or '')}-{_safe_slug(feature.get('feature_id') or '')}-{uuid.uuid4().hex[:8]}"
    trial_dir = (TRIAL_ROOT / trial_id).resolve()
    trial_dir.mkdir(parents=True, exist_ok=True)
    suggested_goal = (
        f"Use {plugin.get('name')} / {feature.get('name')} to enhance this dataset once. "
        "Focus on the matched fields, quantify what changed compared with the baseline profile, and keep CSV/XLSX/JSON artifacts."
    )
    recommended_lab_run_payload = {
        "dataset_id": request.dataset_id,
        "active_sheet": request.active_sheet or None,
        "user_goal": request.user_goal or suggested_goal,
        "report_part": "auto",
        "selected_report_parts": ["executive_summary", "visual_gallery", "appendix", "method_note"],
        "max_methods": 6,
        "external_skill_ids": [plugin.get("id")],
        "execution_mode": "smart_merge",
        "cli_interpretation_enabled": True,
        "business_interpretation_enabled": True,
        "method_independent_output_enabled": True,
        "smart_merge_enabled": True,
    }
    trial_payload = {
        "contract": "analysis_lab_feature_trial_v1",
        "trial_id": trial_id,
        "created_at": created_at,
        "dataset": {
            "dataset_id": request.dataset_id,
            "name": metadata.get("name") or metadata.get("filename") or "",
            "sheet_name": (sheet or {}).get("name") or request.active_sheet or "",
        },
        "plugin": {
            "id": plugin.get("id"),
            "name": plugin.get("name"),
            "version": plugin.get("plugin_version") or "",
            "source_repo": plugin.get("source_repo") or "",
        },
        "feature": feature,
        "baseline_profile": {
            "row_count": profile["row_count"],
            "column_count": profile["column_count"],
            "numeric_column_count": len(profile["numeric_columns"]),
            "categorical_column_count": len(profile["categorical_columns"]),
            "datetime_column_count": len(profile["datetime_columns"]),
            "duplicate_row_count": profile["duplicate_row_count"],
        },
        "enhancement_effect": {
            "readiness_score": readiness_score,
            "readiness_reasons": readiness_reasons,
            "summary": "This trial turns a mounted plugin feature into a selectable single-pass enhancement over the current dataset.",
            "top_fields": profile["top_fields"][:8],
            "recommended_actions": actions,
        },
        "sample_rows": profile["sample_rows"],
        "recommended_lab_run_payload": recommended_lab_run_payload,
    }
    json_path = trial_dir / "trial.json"
    csv_path = trial_dir / "field_scores.csv"
    md_path = trial_dir / "trial_report.md"
    json_path.write_text(json.dumps(_json_safe(trial_payload), ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["column", "role", "dtype", "missing_rate", "unique_count", "score", "matched_keywords"],
        )
        writer.writeheader()
        for row in profile["field_scores"]:
            writer.writerow({**row, "matched_keywords": ", ".join(row.get("matched_keywords") or [])})
    md_path.write_text(
        _trial_report_markdown(
            trial_id=trial_id,
            plugin=plugin,
            feature=feature,
            readiness_score=readiness_score,
            readiness_reasons=readiness_reasons,
            profile=profile,
            actions=actions,
        ),
        encoding="utf-8",
    )
    trial_payload["artifacts"] = {
        "directory": str(trial_dir),
        "json_path": str(json_path),
        "csv_path": str(csv_path),
        "report_path": str(md_path),
        "json_url": _public_path(json_path),
        "csv_url": _public_path(csv_path),
        "report_url": _public_path(md_path),
    }
    return _json_safe(trial_payload)
