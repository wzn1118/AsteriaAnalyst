from __future__ import annotations

from typing import Any


def build_challenge_context(
    *,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    request: dict[str, Any],
    evidence_digest_layer: dict[str, Any],
    insight_mining_layer: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "request": request,
        "evidence_digest_layer": evidence_digest_layer,
        "insight_mining_layer": insight_mining_layer,
    }


def challenge_section(layer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not layer:
        return None
    bullets = [str(item).strip() for item in (layer.get("counter_arguments") or []) if str(item).strip()]
    bullets.extend(str(item).strip() for item in (layer.get("boundary_alerts") or [])[:3] if str(item).strip())
    if not bullets:
        return None
    rows = [
        {
            "被挑战结论": item.get("claim"),
            "挑战点": item.get("challenge"),
            "问题类型": item.get("issue_type"),
            "严重度": item.get("severity"),
        }
        for item in (layer.get("challenge_points") or [])[:10]
        if item.get("claim")
    ]
    return {
        "id": "challenge_layer",
        "title": "反证与边界层",
        "summary": "这部分专门唱反调，目的是把过度解释、因果越界和样本问题提前挑出来，让后面的判断更可信。",
        "bullets": bullets[:6],
        "tables": [
            {
                "title": "挑战清单",
                "columns": ["被挑战结论", "挑战点", "问题类型", "严重度"],
                "rows": rows,
            }
        ]
        if rows
        else [],
        "charts": [],
    }


def summarize_revision_routes(layer: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped = {"business": [], "decision": [], "polish": []}
    for item in (layer.get("issues") or []):
        route = str(item.get("route_to") or "").strip()
        if route == "business_synthesis":
            grouped["business"].append(item)
        elif route == "decision_design":
            grouped["decision"].append(item)
        elif route == "final_polish":
            grouped["polish"].append(item)
    return grouped
