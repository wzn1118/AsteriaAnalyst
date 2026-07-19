from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


HookHandler = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any] | None]


@dataclass(slots=True)
class HookRegistration:
    event: str
    name: str
    handler: HookHandler


class ReportHookRegistry:
    def __init__(self) -> None:
        self._registrations: list[HookRegistration] = []

    def register(self, event: str, name: str, handler: HookHandler) -> None:
        self._registrations.append(HookRegistration(event=event, name=name, handler=handler))

    def run(self, event: str, payload: dict[str, Any], shared_state: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for registration in self._registrations:
            if registration.event != event:
                continue
            started = _now_iso()
            try:
                result = registration.handler(payload, shared_state) or {}
                if isinstance(result, dict):
                    shared_state.update(result)
                events.append(
                    {
                        "event": event,
                        "name": registration.name,
                        "status": "completed",
                        "timestamp": started,
                        "output": result,
                    }
                )
            except Exception as exc:
                events.append(
                    {
                        "event": event,
                        "name": registration.name,
                        "status": "failed",
                        "timestamp": started,
                        "error": str(exc),
                    }
                )
        return events


def _after_semantic_hook(payload: dict[str, Any], _: dict[str, Any]) -> dict[str, Any]:
    semantic_layer = payload.get("semantic_layer", {}) or {}
    metric_cards = semantic_layer.get("metric_cards", []) or []
    important_columns = semantic_layer.get("important_columns", []) or []
    return {
        "semantic_hook_summary": {
            "runtime_state": semantic_layer.get("runtime_state") or semantic_layer.get("mode"),
            "metric_card_count": len(metric_cards),
            "important_columns": important_columns[:6],
        }
    }


def _after_relation_hook(payload: dict[str, Any], _: dict[str, Any]) -> dict[str, Any]:
    relation_context = payload.get("relation_context", {}) or {}
    dimension_profiles = relation_context.get("dimension_profiles", []) or []
    relation_findings = relation_context.get("relation_findings", []) or []
    return {
        "relation_hook_summary": {
            "dimensions": [item.get("dimension") for item in dimension_profiles[:8] if item.get("dimension")],
            "finding_count": len(relation_findings),
            "top_findings": relation_findings[:4],
        }
    }


def _after_sections_hook(payload: dict[str, Any], _: dict[str, Any]) -> dict[str, Any]:
    sections = payload.get("sections", []) or []
    return {
        "sections_hook_summary": {
            "section_count": len(sections),
            "section_ids": [str(section.get("id") or "") for section in sections[:20]],
        }
    }


def _before_gate_hook(payload: dict[str, Any], _: dict[str, Any]) -> dict[str, Any]:
    intelligence_runtime = payload.get("intelligence_runtime", {}) or {}
    fallback_layers = [item.get("layer") for item in (intelligence_runtime.get("fallback_layers") or []) if item.get("layer")]
    result = {
        "gate_hook_summary": {
            "hard_degraded": bool(intelligence_runtime.get("hard_degraded")),
            "fallback_layers": fallback_layers[:10],
        }
    }
    if intelligence_runtime.get("hard_degraded"):
        result["control"] = {
            "block_release": True,
            "reason": "hard_degraded",
        }
    return result


def _after_gate_hook(payload: dict[str, Any], _: dict[str, Any]) -> dict[str, Any]:
    gate = payload.get("release_gate", {}) or {}
    result = {
        "gate_result_summary": {
            "verdict": gate.get("verdict"),
            "score": gate.get("total_score"),
            "threshold": gate.get("threshold"),
            "blocked": str(gate.get("verdict") or "").strip().lower() != "pass",
        }
    }
    route_to = [str(item).strip() for item in (gate.get("route_to") or []) if str(item).strip()]
    verdict = str(gate.get("verdict") or "").strip().lower()
    if route_to:
        result["control"] = {
            "rerun_stage": route_to[:5],
            "reason": "gate_block",
        }
    elif verdict == "block":
        result["control"] = {
            "block_release": True,
            "reason": "gate_block",
        }
    return result


def build_default_report_hooks() -> ReportHookRegistry:
    registry = ReportHookRegistry()
    registry.register("after_semantic", "semantic-summary", _after_semantic_hook)
    registry.register("after_relation", "relation-summary", _after_relation_hook)
    registry.register("after_sections", "section-summary", _after_sections_hook)
    registry.register("before_gate", "gate-precheck", _before_gate_hook)
    registry.register("after_gate", "gate-postcheck", _after_gate_hook)
    return registry
