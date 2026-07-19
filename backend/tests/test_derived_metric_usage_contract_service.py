from __future__ import annotations

import json
from pathlib import Path

from app.services.derived_metric_usage_contract_service import (
    collect_derived_metric_usage_contract,
    summarize_derived_metric_usage,
)


def test_collect_contract_separates_executed_planned_and_failed_metrics(tmp_path: Path) -> None:
    (tmp_path / "metric_derivation_plan.json").write_text(
        json.dumps(
            {
                "metrics": [
                    {
                        "metric_id": "margin_rate_derived",
                        "metric_name": "毛利率",
                        "formula": "profit / revenue",
                        "status": "planned_only",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    contract = collect_derived_metric_usage_contract(
        workspace=tmp_path,
        metric_rows=[
            {
                "metric_id": "aov_derived",
                "metric_name": "客单价",
                "formula": "revenue / orders",
                "value": "128.5",
                "comparison": "高于基准 8%",
            }
        ],
        metric_execution={
            "metrics": [
                {
                    "metric_id": "failed_metric",
                    "metric_name": "失败指标",
                    "execution_status": "failed",
                }
            ]
        },
    )

    assert (tmp_path / "derived_metric_usage_contract.json").is_file()
    assert contract["derived_metric_count"] == 3
    assert contract["executed_metric_count"] == 1
    assert contract["planned_only_metric_count"] == 1
    assert contract["failed_metric_count"] == 1
    rows = {row["metric_id"]: row for row in contract["metrics"]}
    assert rows["aov_derived"]["can_support_current_fact"] is True
    assert rows["margin_rate_derived"]["usage_policy"] == "may_support_method_definition_and_pending_execution_only"
    assert rows["failed_metric"]["usage_policy"] == "must_not_be_written_as_current_fact"


def test_usage_summary_enforces_body_recommendation_and_asset_coverage(tmp_path: Path) -> None:
    contract = collect_derived_metric_usage_contract(
        workspace=tmp_path,
        metric_rows=[
            {"metric_id": "aov_derived", "metric_name": "客单价", "value": "128"},
            {"metric_id": "conversion_rate_derived", "metric_name": "转化率", "value": "0.18"},
        ],
    )
    summary = summarize_derived_metric_usage(
        contract=contract,
        page_plan=[
            {
                "page_number": 1,
                "derived_metrics": [{"metric_id": "aov_derived"}, {"metric_id": "conversion_rate_derived"}],
            }
        ],
        page_drafts=[
            {
                "derived_metrics_used": [{"metric_id": "aov_derived"}, {"metric_id": "conversion_rate_derived"}],
                "recommended_action": {"trigger_metric": "aov_derived"},
            }
        ],
        asset_coverage={"used_derived_metric_names": ["aov_derived"]},
    )

    assert summary["passes_gate"] is True
    assert summary["derived_metric_coverage_ratio"] == 1.0
    assert set(summary["used_derived_metric_ids"]) == {"aov_derived", "conversion_rate_derived"}


def test_usage_summary_fails_when_derived_metrics_stay_out_of_body(tmp_path: Path) -> None:
    contract = collect_derived_metric_usage_contract(
        workspace=tmp_path,
        metric_rows=[{"metric_id": "aov_derived", "metric_name": "客单价", "value": "128"}],
    )
    summary = summarize_derived_metric_usage(
        contract=contract,
        page_plan=[{"page_number": 1, "derived_metrics": [{"metric_id": "aov_derived"}]}],
        page_drafts=[{"diagnosis": "没有使用派生指标", "recommended_action": {}}],
        asset_coverage={},
    )

    assert summary["passes_gate"] is False
    assert "derived_metric_recommendation_missing" in summary["issues"]


def test_contract_preserves_historical_support_table_metric_raw_key(tmp_path: Path) -> None:
    contract = collect_derived_metric_usage_contract(
        workspace=tmp_path,
        context_payload={
            "historical_support_tables": {
                "derived_metric_rows": [
                    {
                        "metric_raw_key": "aov_derived",
                        "metric": "客单价",
                        "formula": "revenue / orders",
                        "mean": 32.5,
                        "business_meaning": "衡量每笔订单收入质量",
                    }
                ]
            }
        },
    )

    assert contract["derived_metric_count"] == 1
    assert contract["metrics"][0]["metric_id"] == "aov_derived"
    assert contract["metrics"][0]["status"] == "executed"
