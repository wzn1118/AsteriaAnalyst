from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.dataset_service import build_column_summaries, clean_records
from app.services.procurement_sales_metric_mining_service import (
    build_procurement_sales_metric_mining_result,
)
from app.services.procurement_sales_profile_service import (
    field_availability_registry,
    procurement_sales_readiness_check,
)
from app.services.procurement_sales_relation_service import (
    build_procurement_sales_relation_context,
)


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
    return path


def prepare_procurement_sales_cli_grounding_workspace(
    *,
    workspace_dir: Path,
    frame: pd.DataFrame,
    dataset_name: str,
    sheet_name: str,
    request_payload: dict[str, Any] | None = None,
    business_profile_router_result: dict[str, Any] | None = None,
    universal_metric_mining_result: dict[str, Any] | None = None,
    rows_by_dimension: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Create deterministic procurement-sales grounding artifacts for the CLI pipeline."""
    workspace_dir.mkdir(parents=True, exist_ok=True)
    request_payload = dict(request_payload or {})
    business_profile_router_result = dict(business_profile_router_result or {})
    universal_metric_mining_result = dict(universal_metric_mining_result or {})
    rows_by_dimension = dict(rows_by_dimension or {})

    dataset_profile = {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "row_count": int(frame.shape[0]),
        "column_count": int(frame.shape[1]),
        "columns": [str(column) for column in frame.columns],
        "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        "sample_rows": clean_records(frame, limit=12),
        "column_summaries": build_column_summaries(frame),
        "business_profile": "procurement_sales_report",
    }
    field_registry = field_availability_registry(frame)
    readiness_check = procurement_sales_readiness_check(frame)
    metric_payload = build_procurement_sales_metric_mining_result(
        raw_data=frame,
        field_names=[str(column) for column in frame.columns],
        sample_values=[],
        data_types={str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        universal_metric_mining_result=universal_metric_mining_result,
        business_profile_router_result=business_profile_router_result,
    )
    relation_context = build_procurement_sales_relation_context(rows_by_dimension)

    dataset_profile_path = _write_json(
        workspace_dir / "source_dataset_profile.json",
        dataset_profile,
    )
    field_registry_path = _write_json(
        workspace_dir / "procurement_field_registry.json",
        field_registry,
    )
    readiness_path = _write_json(
        workspace_dir / "procurement_readiness_check.json",
        readiness_check,
    )
    metric_result_path = _write_json(
        workspace_dir / "procurement_metric_mining_result.json",
        metric_payload,
    )
    object_registry_path = _write_csv(
        workspace_dir / "procurement_object_registry.csv",
        list(metric_payload.get("object_registry_rows") or []),
    )
    opportunity_risk_path = _write_csv(
        workspace_dir / "procurement_opportunity_risk_table.csv",
        list(metric_payload.get("opportunity_risk_rows") or []),
    )
    action_table_path = _write_csv(
        workspace_dir / "procurement_action_table.csv",
        list(metric_payload.get("action_table_rows") or []),
    )
    relation_context_path = _write_json(
        workspace_dir / "procurement_relation_context.json",
        relation_context,
    )

    context_bundle = {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "business_profile": "procurement_sales_report",
        "procurement_report_mode": str(field_registry.get("report_mode") or readiness_check.get("report_mode") or ""),
        "request_payload": request_payload,
        "business_profile_router_result": business_profile_router_result,
        "source_dataset_profile_path": dataset_profile_path.name,
        "procurement_field_registry_path": field_registry_path.name,
        "procurement_readiness_check_path": readiness_path.name,
        "procurement_metric_mining_result_path": metric_result_path.name,
        "procurement_object_registry_path": object_registry_path.name,
        "procurement_opportunity_risk_table_path": opportunity_risk_path.name,
        "procurement_action_table_path": action_table_path.name,
        "procurement_relation_context_path": relation_context_path.name,
        "can_judge": list((metric_payload.get("narrative") or {}).get("can_judge") or []),
        "cannot_judge": list((metric_payload.get("narrative") or {}).get("cannot_judge") or []),
        "relation_findings": list(relation_context.get("relation_findings") or []),
        "priority_actions": [
            {
                "priority": row.get("priority", ""),
                "action": row.get("action", ""),
                "object_name": row.get("object_name", ""),
                "trigger_metric": row.get("trigger_metric", ""),
            }
            for row in list(metric_payload.get("action_table_rows") or [])[:20]
        ],
        "field_boundaries": {
            "missing_fields": list(field_registry.get("missing_field_groups") or []),
            "report_mode": field_registry.get("report_mode", ""),
            "readiness_summary": readiness_check,
        },
        "mode_specific_contract": {
            "can_do": list((metric_payload.get("narrative") or {}).get("can_judge") or []),
            "cannot_do": list((metric_payload.get("narrative") or {}).get("cannot_judge") or []),
        },
    }
    context_bundle_path = _write_json(
        workspace_dir / "procurement_context_bundle.json",
        context_bundle,
    )

    return {
        "source_dataset_profile_path": str(dataset_profile_path.resolve()),
        "procurement_field_registry_path": str(field_registry_path.resolve()),
        "procurement_readiness_check_path": str(readiness_path.resolve()),
        "procurement_metric_mining_result_path": str(metric_result_path.resolve()),
        "procurement_object_registry_path": str(object_registry_path.resolve()),
        "procurement_opportunity_risk_table_path": str(opportunity_risk_path.resolve()),
        "procurement_action_table_path": str(action_table_path.resolve()),
        "procurement_relation_context_path": str(relation_context_path.resolve()),
        "procurement_context_bundle_path": str(context_bundle_path.resolve()),
    }
