from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMappingResult,
    AIMetricDerivationPlan,
)


REQUIRED_TRACE_FILES = {
    "ai_field_semantic_mapping.json": AIFieldSemanticMappingResult,
    "ai_business_routing.json": AIBusinessRoutingResult,
    "ai_metric_derivation_plan.json": AIMetricDerivationPlan,
}

REQUIRED_METRIC_LOG_COLUMNS = {
    "metric_id",
    "metric_name_cn",
    "status",
    "source_fields",
    "formula",
    "calculation_method",
    "evidence_level",
    "confidence",
    "caveat",
    "unsupported_reason",
}


def _trace_dir(output_dir: str | Path) -> Path:
    return Path(output_dir) / "outputs" / "ai_traces"


def _metric_dir(output_dir: str | Path) -> Path:
    return Path(output_dir) / "outputs" / "metric_mining"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_ai_mandatory_artifacts(output_dir: str | Path) -> dict[str, Any]:
    trace_dir = _trace_dir(output_dir)
    metric_dir = _metric_dir(output_dir)
    failure_reasons: list[str] = []
    diagnostics: dict[str, Any] = {
        "trace_dir": str(trace_dir.resolve()) if trace_dir.exists() else str(trace_dir),
        "metric_dir": str(metric_dir.resolve()) if metric_dir.exists() else str(metric_dir),
        "validated_files": [],
        "missing_files": [],
        "schema_errors": {},
        "validated_deterministic_files": [],
        "missing_deterministic_files": [],
        "warnings": [],
    }
    metric_plan_trace_id = ""

    if not trace_dir.exists():
        failure_reasons.append("outputs/ai_traces missing")

    for filename, schema in REQUIRED_TRACE_FILES.items():
        path = trace_dir / filename
        if not path.exists():
            failure_reasons.append(f"{filename} missing")
            diagnostics["missing_files"].append(filename)
            continue
        try:
            payload = _read_json(path)
        except Exception as exc:
            failure_reasons.append(f"{filename} invalid json: {exc}")
            diagnostics["schema_errors"][filename] = f"invalid json: {exc}"
            continue
        try:
            validated = schema.model_validate(payload)
        except ValidationError as exc:
            failure_reasons.append(f"{filename} schema invalid")
            diagnostics["schema_errors"][filename] = exc.errors()
            continue

        if not getattr(validated, "trace_id", ""):
            failure_reasons.append(f"{filename} trace_id missing")
        if filename == "ai_business_routing.json" and "confidence" not in payload:
            failure_reasons.append(f"{filename} confidence missing")
        if filename == "ai_business_routing.json":
            if float(getattr(validated, "confidence", 0.0)) < 0.70:
                diagnostics["warnings"].append(
                    {
                        "code": "ROUTE_CONFIDENCE_LOW",
                        "message": "ai_business_routing.json confidence below 0.70",
                        "confidence": float(getattr(validated, "confidence", 0.0)),
                        "final_route": getattr(validated, "final_route", ""),
                    }
                )
        if filename == "ai_metric_derivation_plan.json":
            metric_plan_trace_id = str(getattr(validated, "trace_id", ""))
            for idx, item in enumerate(validated.metric_plans):
                if not item.evidence_level:
                    failure_reasons.append(f"{filename} metric_plans[{idx}].evidence_level missing")
                if not item.confidence:
                    failure_reasons.append(f"{filename} metric_plans[{idx}].confidence missing")
        if filename == "ai_field_semantic_mapping.json":
            for idx, item in enumerate(validated.field_mappings):
                if item.confidence is None:
                    failure_reasons.append(f"{filename} field_mappings[{idx}].confidence missing")

        diagnostics["validated_files"].append(filename)

    result_path = metric_dir / "semantic_metric_result.json"
    if not result_path.exists():
        failure_reasons.append("semantic_metric_result.json missing")
        diagnostics["missing_deterministic_files"].append(result_path.name)
    else:
        try:
            result_payload = _read_json(result_path)
            result_errors: list[str] = []
            if not isinstance(result_payload, dict):
                result_errors.append("payload must be an object")
            else:
                if not isinstance(result_payload.get("results"), list):
                    result_errors.append("results must be a list")
                if not isinstance(result_payload.get("summary"), dict):
                    result_errors.append("summary must be an object")
                if metric_plan_trace_id and result_payload.get("trace_id") != metric_plan_trace_id:
                    result_errors.append("trace_id does not match ai_metric_derivation_plan.json")
            if result_errors:
                failure_reasons.append("semantic_metric_result.json contract invalid")
                diagnostics["schema_errors"][result_path.name] = result_errors
            else:
                diagnostics["validated_deterministic_files"].append(result_path.name)
        except Exception as exc:
            failure_reasons.append(f"semantic_metric_result.json invalid json: {exc}")
            diagnostics["schema_errors"][result_path.name] = f"invalid json: {exc}"

    log_path = metric_dir / "metric_derivation_log.csv"
    if not log_path.exists():
        failure_reasons.append("metric_derivation_log.csv missing")
        diagnostics["missing_deterministic_files"].append(log_path.name)
    else:
        try:
            with log_path.open("r", encoding="utf-8-sig", newline="") as handle:
                header = next(csv.reader(handle), [])
            missing_columns = sorted(REQUIRED_METRIC_LOG_COLUMNS.difference(header))
            if missing_columns:
                failure_reasons.append("metric_derivation_log.csv contract invalid")
                diagnostics["schema_errors"][log_path.name] = {
                    "missing_columns": missing_columns,
                }
            else:
                diagnostics["validated_deterministic_files"].append(log_path.name)
        except Exception as exc:
            failure_reasons.append(f"metric_derivation_log.csv unreadable: {exc}")
            diagnostics["schema_errors"][log_path.name] = f"unreadable: {exc}"

    if len(diagnostics["validated_files"]) != len(REQUIRED_TRACE_FILES):
        failure_reasons.append("formal pdf release required AI trace files incomplete")
    if len(diagnostics["validated_deterministic_files"]) != 2:
        failure_reasons.append("formal pdf release required deterministic metric artifacts incomplete")

    return {
        "passed": not failure_reasons,
        "failure_reasons": failure_reasons,
        "diagnostics": diagnostics,
    }
