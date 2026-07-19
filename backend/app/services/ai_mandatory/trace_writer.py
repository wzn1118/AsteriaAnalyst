from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMappingResult,
    AIMetricDerivationPlan,
)


def _trace_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir) / "outputs" / "ai_traces"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())


def write_ai_field_semantic_mapping_trace(
    output_dir: str | Path,
    payload: AIFieldSemanticMappingResult | dict[str, Any],
) -> str:
    data = payload.model_dump(mode="json") if isinstance(payload, AIFieldSemanticMappingResult) else payload
    return _write_json(_trace_dir(output_dir) / "ai_field_semantic_mapping.json", data)


def write_ai_business_routing_trace(
    output_dir: str | Path,
    payload: AIBusinessRoutingResult | dict[str, Any],
) -> str:
    data = payload.model_dump(mode="json") if isinstance(payload, AIBusinessRoutingResult) else payload
    return _write_json(_trace_dir(output_dir) / "ai_business_routing.json", data)


def write_ai_metric_derivation_plan_trace(
    output_dir: str | Path,
    payload: AIMetricDerivationPlan | dict[str, Any],
) -> str:
    data = payload.model_dump(mode="json") if isinstance(payload, AIMetricDerivationPlan) else payload
    return _write_json(_trace_dir(output_dir) / "ai_metric_derivation_plan.json", data)


def write_ai_usage_gate_trace(
    output_dir: str | Path,
    payload: dict[str, Any],
) -> str:
    return _write_json(_trace_dir(output_dir) / "ai_usage_gate_result.json", payload)
