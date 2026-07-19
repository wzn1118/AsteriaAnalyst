from __future__ import annotations

from app.services.generic_long_codex_chain_service import _build_page_drafts, _validate_page_drafts


def _long_cn(seed: str, count: int) -> str:
    return seed * count


def test_generic_long_page_draft_builder_records_derived_metrics_used() -> None:
    page_plan = [
        {
            "page_number": 1,
            "page_title": "派生指标诊断页",
            "management_question": "客单价是否驱动收入质量变化",
            "derived_metrics": [
                {
                    "metric_id": "aov_derived",
                    "metric_name": "客单价",
                    "value": "128",
                    "comparison": "高于基准",
                }
            ],
            "source_passes": ["metric_derivation_plan", "derived_metric_execution_review"],
        }
    ]
    ai_pages = [
        {
            "page_number": 1,
            "diagnosis": _long_cn("客单价派生指标显示收入质量正在改善，但仍需按类目复核。", 18),
            "business_interpretation": _long_cn("管理层需要把客单价变化拆到类目和渠道，避免只看收入总量。", 16),
            "evidence": [
                {
                    "metric_id": "aov_derived",
                    "metric_name": "客单价",
                    "value": "128",
                    "comparison": "高于基准",
                    "object_or_dimension": "类目",
                    "evidence_strength": "high",
                },
                {
                    "metric_id": "aov_derived",
                    "metric_name": "客单价",
                    "value": "128",
                    "comparison": "高于基准且可复核",
                    "object_or_dimension": "渠道",
                    "evidence_strength": "medium",
                }
            ],
            "recommended_action": {
                "object": "高客单价类目",
                "action": "复核高客单价类目的动销质量和补货节奏",
            },
            "data_limitations": "需要继续检查类目样本量。",
            "forbidden_misreadings": [],
        }
    ]

    drafts = _build_page_drafts(ai_pages, page_plan)

    assert drafts[0]["derived_metrics_used"][0]["metric_id"] == "aov_derived"
    assert drafts[0]["recommended_action"]["trigger_metric"] == "aov_derived"
    assert _validate_page_drafts(drafts, page_plan) is True


def test_generic_long_page_draft_validator_rejects_missing_derived_metric_usage() -> None:
    page_plan = [
        {
            "page_number": 1,
            "page_title": "派生指标诊断页",
            "management_question": "客单价是否驱动收入质量变化",
            "derived_metrics": [{"metric_id": "aov_derived", "metric_name": "客单价"}],
            "source_passes": ["metric_derivation_plan"],
        }
    ]
    drafts = [
        {
            "page_number": 1,
            "page_title": "派生指标诊断页",
            "management_question": "客单价是否驱动收入质量变化",
            "diagnosis": _long_cn("这一页没有显式记录派生指标使用。", 30),
            "evidence": [
                {
                    "metric_id": "raw_revenue",
                    "metric_name": "收入",
                    "value": "100",
                    "comparison": "高",
                    "object_or_dimension": "类目",
                    "evidence_strength": "medium",
                },
                {
                    "metric_id": "raw_orders",
                    "metric_name": "订单",
                    "value": "80",
                    "comparison": "中",
                    "object_or_dimension": "类目",
                    "evidence_strength": "medium",
                },
            ],
            "derived_metrics_used": [],
            "derived_metric_explanation": "没有使用派生指标。",
            "business_interpretation": _long_cn("管理解释没有把派生指标纳入主线，因此不应该通过。", 24),
            "recommended_action": {
                "object": "类目",
                "trigger_metric": "",
                "action": "继续观察",
            },
            "data_limitations": "无",
            "forbidden_misreadings": [],
            "source_passes": ["metric_derivation_plan"],
            "low_data_boundary_page": False,
            "ai_content_hash": "hash",
        }
    ]

    assert _validate_page_drafts(drafts, page_plan) is False
