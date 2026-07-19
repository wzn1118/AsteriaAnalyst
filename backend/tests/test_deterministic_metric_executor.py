from __future__ import annotations

import csv
import json
from pathlib import Path

from app.services.ai_mandatory.deterministic_metric_executor import execute_metric_plan
from app.services.ai_mandatory.schemas import (
    AIFieldSemanticMapping,
    AIFieldSemanticMappingResult,
    AIMetricDerivationPlan,
    AIMetricPlanItem,
)


def _mapping(field_name: str, canonical: str, role: str, grain: str = "") -> AIFieldSemanticMapping:
    return AIFieldSemanticMapping(
        field_name=field_name,
        canonical_concept=canonical,
        business_role=role,
        granularity_hint=grain or canonical,
        confidence=0.95,
        evidence=["semantic mapping"],
        alternative_mappings=[],
        risk_note="",
    )


def _semantic_result(mappings: list[AIFieldSemanticMapping], *, object_grain: str, time_grain: str) -> AIFieldSemanticMappingResult:
    return AIFieldSemanticMappingResult(
        inferred_business_context="test context",
        object_grain=object_grain,
        time_grain=time_grain,
        field_mappings=mappings,
        uncertain_fields=[],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-semantic-exec-001",
    )


def _plan_item(
    *,
    metric_id: str,
    metric_name_cn: str,
    metric_family: str,
    metric_type: str,
    required_field_roles: list[str],
    matched_fields: list[str],
    formula_or_logic: str,
    grain: str,
    evidence_level: str,
    confidence: float,
    calculation_feasibility: str,
    caveat: str = "",
) -> AIMetricPlanItem:
    return AIMetricPlanItem(
        metric_id=metric_id,
        metric_name_cn=metric_name_cn,
        metric_name_en=metric_id,
        metric_family=metric_family,
        business_domain="test",
        business_object="test_object",
        metric_type=metric_type,
        required_field_roles=required_field_roles,
        matched_fields=matched_fields,
        missing_fields=[],
        formula=formula_or_logic,
        grain=grain,
        time_window_requirement="",
        minimum_data_requirement="rows >= 1",
        evidence_level=evidence_level,
        confidence=confidence,
        calculation_feasibility=calculation_feasibility,
        business_question_answered="test question",
        downstream_usage=["management_report"],
        forbidden_usage=["renderer_side_field_understanding"],
        caveat=caveat,
        reason="test plan",
    )


def _plan(*items: AIMetricPlanItem) -> AIMetricDerivationPlan:
    return AIMetricDerivationPlan(
        available_metrics=[item.metric_id for item in items if item.metric_type in {"direct", "derived"}],
        unavailable_metrics=[item.metric_id for item in items if item.metric_type == "unavailable"],
        proxy_metrics=[item.metric_id for item in items if item.metric_type == "proxy"],
        diagnostic_questions=[],
        metric_plans=list(items),
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-plan-exec-001",
    )


def _result_map(payload: dict) -> dict[str, dict]:
    return {row["metric_id"]: row for row in payload["results"]}


def test_dau_calculated_from_date_user_id(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame(
        {
            "event_date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02", "2026-01-02"],
            "user_id": ["u1", "u2", "u1", "u2", "u3"],
        }
    )
    semantic = _semantic_result(
        [_mapping("event_date", "date", "time_key"), _mapping("user_id", "user_id", "user_key")],
        object_grain="user",
        time_grain="day",
    )
    plan = _plan(
        _plan_item(
            metric_id="dau_active_users",
            metric_name_cn="日活跃用户",
            metric_family="retention_metric",
            metric_type="derived",
            required_field_roles=["user_key", "time_key"],
            matched_fields=["user_id", "event_date"],
            formula_or_logic="nunique(user_id) by day(event_date)",
            grain="day",
            evidence_level="B_DERIVED",
            confidence=0.9,
            calculation_feasibility="calculable",
            caveat="",
        )
    )

    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metric = _result_map(payload)["dau_active_users"]
    assert metric["status"] == "calculated"
    assert metric["value"] == [{"period": "2026-01-01", "value": 2}, {"period": "2026-01-02", "value": 3}]


def test_retention_calculated_from_user_id_date(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame(
        {
            "event_date": ["2026-01-01", "2026-01-02", "2026-01-01", "2026-01-02", "2026-01-03"],
            "user_id": ["u1", "u1", "u2", "u3", "u3"],
        }
    )
    semantic = _semantic_result(
        [_mapping("event_date", "date", "time_key"), _mapping("user_id", "user_id", "user_key")],
        object_grain="user",
        time_grain="day",
    )
    plan = _plan(
        _plan_item(
            metric_id="retention_d1",
            metric_name_cn="D1留存",
            metric_family="retention_metric",
            metric_type="derived",
            required_field_roles=["user_key", "time_key"],
            matched_fields=["user_id", "event_date"],
            formula_or_logic="users(day+1) / users(day0)",
            grain="cohort_day",
            evidence_level="B_DERIVED",
            confidence=0.88,
            calculation_feasibility="calculable",
        )
    )
    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metric = _result_map(payload)["retention_d1"]
    assert metric["status"] == "calculated"
    assert metric["value"][0]["cohort_users"] >= 1
    assert "cohort D1 retention" in metric["calculation_method"]


def test_margin_calculated_from_revenue_cost(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame({"revenue": [100.0, 200.0], "cost": [60.0, 120.0]})
    semantic = _semantic_result(
        [_mapping("revenue", "revenue", "amount_field"), _mapping("cost", "cost", "cost_field")],
        object_grain="order",
        time_grain="day",
    )
    plan = _plan(
        _plan_item(
            metric_id="gross_margin",
            metric_name_cn="毛利率",
            metric_family="profitability_metric",
            metric_type="derived",
            required_field_roles=["amount_field", "cost_field"],
            matched_fields=["revenue", "cost"],
            formula_or_logic="(revenue - cost) / revenue",
            grain="overall",
            evidence_level="B_DERIVED",
            confidence=0.9,
            calculation_feasibility="calculable",
        )
    )
    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metric = _result_map(payload)["gross_margin"]
    assert metric["status"] == "calculated"
    assert metric["value"] == 0.4


def test_missing_cost_blocks_margin(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame({"revenue": [100.0, 200.0]})
    semantic = _semantic_result(
        [_mapping("revenue", "revenue", "amount_field")],
        object_grain="order",
        time_grain="day",
    )
    plan = _plan(
        _plan_item(
            metric_id="gross_margin",
            metric_name_cn="毛利率",
            metric_family="profitability_metric",
            metric_type="derived",
            required_field_roles=["amount_field", "cost_field"],
            matched_fields=["revenue"],
            formula_or_logic="(revenue - cost) / revenue",
            grain="overall",
            evidence_level="B_DERIVED",
            confidence=0.9,
            calculation_feasibility="calculable",
            caveat="requires cost",
        )
    )
    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metric = _result_map(payload)["gross_margin"]
    assert metric["status"] in {"unavailable", "failed"}


def test_metric_derivation_log_exists(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame({"revenue": [100.0]})
    semantic = _semantic_result([_mapping("revenue", "revenue", "amount_field")], object_grain="order", time_grain="day")
    plan = _plan(
        _plan_item(
            metric_id="total_revenue",
            metric_name_cn="总收入",
            metric_family="scale_metric",
            metric_type="derived",
            required_field_roles=["amount_field"],
            matched_fields=["revenue"],
            formula_or_logic="sum(revenue)",
            grain="overall",
            evidence_level="B_DERIVED",
            confidence=0.8,
            calculation_feasibility="calculable",
        )
    )
    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    log_path = Path(result["metric_derivation_log_path"])
    assert log_path.exists()
    with log_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows and rows[0]["metric_id"] == "total_revenue"


def test_llm_values_not_used_in_metric_result(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame({"event_date": ["2026-01-01", "2026-01-01"], "user_id": ["u1", "u2"]})
    semantic = _semantic_result(
        [_mapping("event_date", "date", "time_key"), _mapping("user_id", "user_id", "user_key")],
        object_grain="user",
        time_grain="day",
    )
    item = _plan_item(
        metric_id="dau_active_users",
        metric_name_cn="日活跃用户",
        metric_family="retention_metric",
        metric_type="derived",
        required_field_roles=["user_key", "time_key"],
        matched_fields=["user_id", "event_date"],
        formula_or_logic="llm suggested value = 999999",
        grain="day",
        evidence_level="B_DERIVED",
        confidence=0.9,
        calculation_feasibility="calculable",
    )
    plan = _plan(item)
    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metric = _result_map(payload)["dau_active_users"]
    assert metric["value"] == [{"period": "2026-01-01", "value": 2}]
    assert metric["value"] != 999999


def test_generic_sum_groupby_share_and_daily_trend_are_calculated(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame(
        {
            "date": ["2026-04-01", "2026-04-01", "2026-04-02", "2026-04-08", "2026-04-08"],
            "channel": ["search", "social", "search", "search", "social"],
            "impression": [100, 80, 120, 140, 90],
        }
    )
    semantic = _semantic_result(
        [
            _mapping("date", "date", "time_key"),
            _mapping("channel", "channel", "channel_key"),
            _mapping("impression", "impression", "impression_field"),
        ],
        object_grain="channel_day",
        time_grain="day",
    )
    plan = _plan(
        _plan_item(
            metric_id="total_impressions",
            metric_name_cn="总曝光量",
            metric_family="scale_metric",
            metric_type="direct",
            required_field_roles=["impression_field"],
            matched_fields=["impression"],
            formula_or_logic="SUM(impression)",
            grain="dataset",
            evidence_level="A_DIRECT",
            confidence=0.96,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="impressions_by_channel",
            metric_name_cn="按渠道曝光量",
            metric_family="structure_metric",
            metric_type="direct",
            required_field_roles=["channel_key", "impression_field"],
            matched_fields=["channel", "impression"],
            formula_or_logic="GROUP BY channel; SUM(impression)",
            grain="channel",
            evidence_level="A_DIRECT",
            confidence=0.95,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="channel_impression_share",
            metric_name_cn="渠道曝光占比",
            metric_family="structure_metric",
            metric_type="derived",
            required_field_roles=["channel_key", "impression_field"],
            matched_fields=["channel", "impression"],
            formula_or_logic="SUM(impression) by channel / SUM(impression) overall",
            grain="channel",
            evidence_level="B_DERIVED",
            confidence=0.94,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="daily_impressions",
            metric_name_cn="每日曝光量",
            metric_family="trend_metric",
            metric_type="direct",
            required_field_roles=["time_key", "impression_field"],
            matched_fields=["date", "impression"],
            formula_or_logic="GROUP BY date; SUM(impression)",
            grain="day",
            evidence_level="A_DIRECT",
            confidence=0.95,
            calculation_feasibility="calculable",
        ),
    )

    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metrics = _result_map(payload)

    assert metrics["total_impressions"]["status"] == "calculated"
    assert metrics["total_impressions"]["value"] == 530.0
    assert metrics["impressions_by_channel"]["status"] == "calculated"
    assert metrics["impressions_by_channel"]["value"][0] == {"dimension": "search", "value": 360.0}
    assert metrics["channel_impression_share"]["status"] == "calculated"
    assert metrics["channel_impression_share"]["value"][0]["share"] == 0.679245
    assert metrics["daily_impressions"]["status"] == "calculated"
    assert metrics["daily_impressions"]["value"] == [
        {"period": "2026-04-01", "value": 180.0},
        {"period": "2026-04-02", "value": 120.0},
        {"period": "2026-04-08", "value": 230.0},
    ]


def test_generic_active_and_returning_users_are_calculated(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame(
        {
            "date": ["2026-04-01", "2026-04-01", "2026-04-02", "2026-04-08", "2026-04-08"],
            "user_id": ["u1", "u2", "u1", "u1", "u3"],
            "channel": ["search", "social", "search", "search", "social"],
        }
    )
    semantic = _semantic_result(
        [
            _mapping("date", "date", "time_key"),
            _mapping("user_id", "user_id", "user_key"),
            _mapping("channel", "channel", "channel_key"),
        ],
        object_grain="user_channel_day",
        time_grain="day",
    )
    plan = _plan(
        _plan_item(
            metric_id="daily_active_users",
            metric_name_cn="每日活跃用户数",
            metric_family="retention_metric",
            metric_type="derived",
            required_field_roles=["user_key", "time_key"],
            matched_fields=["user_id", "date"],
            formula_or_logic="GROUP BY date; COUNT(DISTINCT user_id)",
            grain="day",
            evidence_level="B_DERIVED",
            confidence=0.92,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="channel_active_users",
            metric_name_cn="渠道活跃用户数",
            metric_family="structure_metric",
            metric_type="derived",
            required_field_roles=["channel_key", "user_key"],
            matched_fields=["channel", "user_id"],
            formula_or_logic="GROUP BY channel; COUNT(DISTINCT user_id)",
            grain="channel",
            evidence_level="B_DERIVED",
            confidence=0.9,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="returning_users",
            metric_name_cn="回访用户数",
            metric_family="retention_metric",
            metric_type="derived",
            required_field_roles=["user_key", "time_key"],
            matched_fields=["user_id", "date"],
            formula_or_logic="COUNT users with more than one active date",
            grain="observed_window",
            evidence_level="B_DERIVED",
            confidence=0.86,
            calculation_feasibility="calculable",
        ),
    )

    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metrics = _result_map(payload)

    assert metrics["daily_active_users"]["status"] == "calculated"
    assert metrics["daily_active_users"]["value"] == [
        {"period": "2026-04-01", "value": 2},
        {"period": "2026-04-02", "value": 1},
        {"period": "2026-04-08", "value": 2},
    ]
    assert metrics["channel_active_users"]["status"] == "calculated"
    active_by_channel = {row["dimension"]: row["value"] for row in metrics["channel_active_users"]["value"]}
    assert active_by_channel == {"social": 2, "search": 1}
    assert metrics["returning_users"]["status"] == "calculated"
    assert metrics["returning_users"]["value"] == {"total_users": 3, "returning_users": 1, "returning_rate": 0.333333}


def test_formula_based_ratio_difference_and_coverage_handlers_are_calculated(tmp_path: Path) -> None:
    import pandas as pd

    frame = pd.DataFrame(
        {
            "IsLate": [0, 1, 0, 0],
            "GMV": [110.0, 220.0, 330.0, 440.0],
            "FreightCost": [10.0, 20.0, 30.0, 40.0],
            "Revenue": [100.0, 200.0, 300.0, 400.0],
            "ReviewText": ["ok", None, "bad", ""],
            "CustomerID": ["c1", "c2", "c1", "c3"],
            "ReviewScore": [5, 2, 4, 1],
            "OrderPurchaseTimestamp": ["2026-04-01", "2026-04-01", "2026-04-02", "2026-04-02"],
            "DeliveredCustomerDate": ["2026-04-03", "2026-04-05", "2026-04-03", None],
            "OrderStatus": ["delivered", "shipped", "delivered", "canceled"],
        }
    )
    semantic = _semantic_result(
        [
            _mapping("IsLate", "late_flag", "status_field"),
            _mapping("GMV", "gmv", "amount_field"),
            _mapping("FreightCost", "cost", "cost_field"),
            _mapping("Revenue", "revenue", "amount_field"),
            _mapping("ReviewText", "comment_text", "text_feedback_field"),
            _mapping("CustomerID", "customer_id", "user_key"),
            _mapping("ReviewScore", "review_score", "review_score_field"),
            _mapping("OrderPurchaseTimestamp", "date", "time_key"),
            _mapping("DeliveredCustomerDate", "delivery_date", "time_key"),
            _mapping("OrderStatus", "order_status", "status_field"),
        ],
        object_grain="order",
        time_grain="day",
    )
    plan = _plan(
        _plan_item(
            metric_id="late_delivery_rate",
            metric_name_cn="晚到率",
            metric_family="risk_metric",
            metric_type="direct",
            required_field_roles=["status_field"],
            matched_fields=["IsLate"],
            formula_or_logic="SUM(IsLate) / COUNT(IsLate)",
            grain="dataset total",
            evidence_level="A_DIRECT",
            confidence=0.94,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="on_time_delivery_rate",
            metric_name_cn="准时送达率",
            metric_family="risk_metric",
            metric_type="derived",
            required_field_roles=["status_field"],
            matched_fields=["IsLate"],
            formula_or_logic="SUM(1 - IsLate) / COUNT(IsLate)",
            grain="dataset total",
            evidence_level="B_DERIVED",
            confidence=0.93,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="freight_to_gmv_ratio",
            metric_name_cn="运费占GMV比率",
            metric_family="efficiency_metric",
            metric_type="derived",
            required_field_roles=["cost_field", "amount_field"],
            matched_fields=["FreightCost", "GMV"],
            formula_or_logic="SUM(FreightCost) / SUM(GMV)",
            grain="dataset total",
            evidence_level="B_DERIVED",
            confidence=0.92,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="net_revenue_after_freight",
            metric_name_cn="扣运费后净额代理值",
            metric_family="profitability_metric",
            metric_type="proxy",
            required_field_roles=["amount_field", "cost_field"],
            matched_fields=["Revenue", "FreightCost"],
            formula_or_logic="SUM(Revenue) - SUM(FreightCost)",
            grain="dataset total",
            evidence_level="C_PROXY",
            confidence=0.76,
            calculation_feasibility="proxy_only",
            caveat="proxy only",
        ),
        _plan_item(
            metric_id="net_margin_after_freight_on_revenue",
            metric_name_cn="扣运费后净额率（Revenue口径代理）",
            metric_family="profitability_metric",
            metric_type="proxy",
            required_field_roles=["amount_field", "cost_field"],
            matched_fields=["Revenue", "FreightCost"],
            formula_or_logic="(SUM(Revenue) - SUM(FreightCost)) / SUM(Revenue)",
            grain="dataset total",
            evidence_level="C_PROXY",
            confidence=0.75,
            calculation_feasibility="proxy_only",
            caveat="proxy only",
        ),
        _plan_item(
            metric_id="review_text_coverage",
            metric_name_cn="文字评价覆盖率",
            metric_family="quality_metric",
            metric_type="derived",
            required_field_roles=["text_feedback_field"],
            matched_fields=["ReviewText"],
            formula_or_logic="COUNT(ReviewText where ReviewText.notna()) / COUNT(ReviewText)",
            grain="dataset total",
            evidence_level="B_DERIVED",
            confidence=0.95,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="distinct_customers",
            metric_name_cn="客户数",
            metric_family="scale_metric",
            metric_type="direct",
            required_field_roles=["user_key"],
            matched_fields=["CustomerID"],
            formula_or_logic="COUNT(DISTINCT CustomerID)",
            grain="dataset total",
            evidence_level="A_DIRECT",
            confidence=0.96,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="average_review_score",
            metric_name_cn="平均评分",
            metric_family="quality_metric",
            metric_type="direct",
            required_field_roles=["review_score_field"],
            matched_fields=["ReviewScore"],
            formula_or_logic="AVG(ReviewScore)",
            grain="dataset total",
            evidence_level="A_DIRECT",
            confidence=0.99,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="average_delivery_days",
            metric_name_cn="平均配送天数",
            metric_family="efficiency_metric",
            metric_type="derived",
            required_field_roles=["time_key"],
            matched_fields=["OrderPurchaseTimestamp", "DeliveredCustomerDate"],
            formula_or_logic="AVG((DeliveredCustomerDate - OrderPurchaseTimestamp).dt.total_seconds() / 86400)",
            grain="dataset total",
            evidence_level="B_DERIVED",
            confidence=0.93,
            calculation_feasibility="calculable",
        ),
        _plan_item(
            metric_id="delivered_order_rate",
            metric_name_cn="已送达订单占比",
            metric_family="risk_metric",
            metric_type="derived",
            required_field_roles=["status_field"],
            matched_fields=["OrderStatus"],
            formula_or_logic="COUNT(OrderStatus where OrderStatus == 'delivered') / COUNT(OrderStatus)",
            grain="dataset total",
            evidence_level="B_DERIVED",
            confidence=0.95,
            calculation_feasibility="calculable",
        ),
    )

    result = execute_metric_plan(output_dir=tmp_path, dataframe=frame, semantic_mapping_result=semantic, metric_plan=plan)
    payload = json.loads(Path(result["semantic_metric_result_path"]).read_text(encoding="utf-8"))
    metrics = _result_map(payload)
    assert metrics["late_delivery_rate"]["value"] == 0.25
    assert metrics["on_time_delivery_rate"]["value"] == 0.75
    assert metrics["freight_to_gmv_ratio"]["value"] == 0.090909
    assert metrics["net_revenue_after_freight"]["value"] == 900.0
    assert metrics["net_margin_after_freight_on_revenue"]["value"] == 0.9
    assert metrics["review_text_coverage"]["value"] == 0.75
    assert metrics["distinct_customers"]["value"] == 3
    assert metrics["average_review_score"]["value"] == 3.0
    assert round(metrics["average_delivery_days"]["value"], 6) == 2.333333
    assert metrics["delivered_order_rate"]["value"] == 0.5
