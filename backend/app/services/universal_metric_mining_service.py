from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd


MetricRow = dict[str, Any]


COMMON_DIRECT_SPECS: list[dict[str, Any]] = [
    {
        "metric_id": "sales_amount",
        "metric_name": "销售额/GMV",
        "aliases": ["sales_amount", "sales", "revenue", "gmv", "销售额", "成交金额", "支付金额", "gmv"],
        "aggregate": "sum",
    },
    {
        "metric_id": "order_count",
        "metric_name": "订单量",
        "aliases": ["order_count", "orders", "订单量", "订单数", "pay_order", "pay_orders"],
        "aggregate": "sum",
    },
    {
        "metric_id": "sales_volume",
        "metric_name": "销量/件数",
        "aliases": ["sales_volume", "quantity", "qty", "销量", "件数", "支付件数"],
        "aggregate": "sum",
    },
    {
        "metric_id": "price",
        "metric_name": "价格",
        "aliases": ["price", "sale_price", "selling_price", "售价", "价格", "客单价", "到手价"],
        "aggregate": "mean",
    },
    {
        "metric_id": "impression",
        "metric_name": "曝光/PV",
        "aliases": ["impression", "impressions", "曝光", "pv", "browse", "view"],
        "aggregate": "sum",
    },
    {
        "metric_id": "click",
        "metric_name": "点击",
        "aliases": ["click", "clicks", "点击"],
        "aggregate": "sum",
    },
    {
        "metric_id": "conversion",
        "metric_name": "转化/支付",
        "aliases": ["conversion", "pay", "支付", "下单", "purchase", "成交", "register", "activation"],
        "aggregate": "sum",
    },
    {
        "metric_id": "inventory",
        "metric_name": "库存",
        "aliases": ["inventory", "stock", "库存", "可售库存"],
        "aggregate": "mean",
    },
    {
        "metric_id": "refund_rate",
        "metric_name": "退款率",
        "aliases": ["refund_rate", "退款率", "退货率", "售后率"],
        "aggregate": "mean",
    },
    {
        "metric_id": "rating",
        "metric_name": "评分",
        "aliases": ["rating", "review_score", "score", "评分", "好评率", "店铺评分"],
        "aggregate": "mean",
    },
]


DOMAIN_DIRECT_SPECS: dict[str, list[dict[str, Any]]] = {
    "procurement_sales_report": [
        *COMMON_DIRECT_SPECS,
        {
            "metric_id": "gross_margin_rate",
            "metric_name": "毛利率",
            "aliases": ["gross_margin_rate", "gross_margin", "毛利率", "毛利"],
            "aggregate": "mean",
        },
        {
            "metric_id": "fulfillment_rate",
            "metric_name": "履约率",
            "aliases": ["fulfillment_rate", "履约率", "签收率", "发货率"],
            "aggregate": "mean",
        },
    ],
    "ecommerce_product_operations_report": [
        *COMMON_DIRECT_SPECS,
        {
            "metric_id": "add_to_cart",
            "metric_name": "加购",
            "aliases": ["add_to_cart", "cart", "加购"],
            "aggregate": "sum",
        },
        {
            "metric_id": "review_count",
            "metric_name": "评价量",
            "aliases": ["review_count", "comment_count", "评论量", "评价量", "review"],
            "aggregate": "sum",
        },
    ],
    "internet_operations_report": [
        {
            "metric_id": "dau",
            "metric_name": "DAU",
            "aliases": ["dau", "日活", "daily_active_users"],
            "aggregate": "sum",
        },
        {
            "metric_id": "wau",
            "metric_name": "WAU",
            "aliases": ["wau", "周活", "weekly_active_users"],
            "aggregate": "sum",
        },
        {
            "metric_id": "mau",
            "metric_name": "MAU",
            "aliases": ["mau", "月活", "monthly_active_users"],
            "aggregate": "sum",
        },
        {
            "metric_id": "register",
            "metric_name": "注册",
            "aliases": ["register", "registrations", "注册"],
            "aggregate": "sum",
        },
        {
            "metric_id": "activation",
            "metric_name": "激活",
            "aliases": ["activation", "激活"],
            "aggregate": "sum",
        },
        {
            "metric_id": "retention_d1",
            "metric_name": "D1留存",
            "aliases": ["retention_d1", "d1", "d1_retention", "d1留存"],
            "aggregate": "mean",
        },
        {
            "metric_id": "retention_d7",
            "metric_name": "D7留存",
            "aliases": ["retention_d7", "d7", "d7_retention", "d7留存"],
            "aggregate": "mean",
        },
        {
            "metric_id": "revenue",
            "metric_name": "收入",
            "aliases": ["revenue", "收入", "income"],
            "aggregate": "sum",
        },
        *[spec for spec in COMMON_DIRECT_SPECS if spec["metric_id"] in {"impression", "click", "conversion"}],
    ],
    "media_campaign_report": [
        {
            "metric_id": "impression",
            "metric_name": "曝光",
            "aliases": ["impression", "impressions", "曝光"],
            "aggregate": "sum",
        },
        {
            "metric_id": "click",
            "metric_name": "点击",
            "aliases": ["click", "clicks", "点击"],
            "aggregate": "sum",
        },
        {
            "metric_id": "ctr",
            "metric_name": "CTR",
            "aliases": ["ctr"],
            "aggregate": "mean",
        },
        {
            "metric_id": "cpm",
            "metric_name": "CPM",
            "aliases": ["cpm"],
            "aggregate": "mean",
        },
        {
            "metric_id": "cpc",
            "metric_name": "CPC",
            "aliases": ["cpc"],
            "aggregate": "mean",
        },
        {
            "metric_id": "cpa",
            "metric_name": "CPA",
            "aliases": ["cpa"],
            "aggregate": "mean",
        },
        {
            "metric_id": "spend",
            "metric_name": "消耗",
            "aliases": ["spend", "cost", "消耗", "花费"],
            "aggregate": "sum",
        },
        {
            "metric_id": "conversion",
            "metric_name": "转化",
            "aliases": ["conversion", "转化", "purchase", "pay"],
            "aggregate": "sum",
        },
    ],
    "generic_long_business_report": [
        {
            "metric_id": "amount",
            "metric_name": "金额",
            "aliases": ["amount", "budget", "actual", "spend", "revenue", "cost", "金额", "预算", "花费", "收入", "成本"],
            "aggregate": "sum",
        },
        {
            "metric_id": "progress",
            "metric_name": "进度",
            "aliases": ["progress", "completion", "progress_rate", "进度", "完成率"],
            "aggregate": "mean",
        },
        {
            "metric_id": "quality_score",
            "metric_name": "质量/评分",
            "aliases": ["quality_score", "score", "rating", "评分", "满意度"],
            "aggregate": "mean",
        },
        {
            "metric_id": "conversion",
            "metric_name": "转化/完成",
            "aliases": ["conversion", "signup", "attendance", "completion", "报名", "到课", "完成"],
            "aggregate": "sum",
        },
    ],
    "independent_industry_research_chain": [
        {"metric_id": "field_count", "metric_name": "字段数", "aliases": [], "aggregate": "count"},
        {"metric_id": "record_count", "metric_name": "记录数", "aliases": [], "aggregate": "count"},
    ],
}


DOMAIN_UNSUPPORTED_SPECS: dict[str, list[dict[str, Any]]] = {
    "procurement_sales_report": [
        {"metric_id": "roi", "metric_name": "ROI", "required": ["cost", "profit", "revenue"]},
        {"metric_id": "supplier_profit_contribution", "metric_name": "供应商利润贡献", "required": ["supplier", "profit"]},
    ],
    "ecommerce_product_operations_report": [
        {"metric_id": "profitability", "metric_name": "利润/ROI", "required": ["gross_margin", "cost", "profit"]},
        {"metric_id": "inventory_turnover", "metric_name": "库存周转", "required": ["inventory", "sales_volume", "date"]},
        {"metric_id": "funnel_breakpoint", "metric_name": "漏斗断点", "required": ["impression", "click", "add_to_cart", "pay"]},
    ],
    "internet_operations_report": [
        {"metric_id": "long_term_retention", "metric_name": "长期留存", "required": ["retention_d1", "retention_d7", "retention_d30"]},
        {"metric_id": "roi", "metric_name": "ROI", "required": ["spend", "revenue"]},
    ],
    "media_campaign_report": [
        {"metric_id": "cpa", "metric_name": "CPA", "required": ["spend", "conversion"]},
        {"metric_id": "roas", "metric_name": "ROAS", "required": ["spend", "revenue"]},
    ],
    "generic_long_business_report": [
        {"metric_id": "goal_attainment", "metric_name": "目标达成", "required": ["target", "plan", "actual"]},
        {"metric_id": "responsibility_attribution", "metric_name": "责任归因", "required": ["owner", "department"]},
    ],
    "independent_industry_research_chain": [
        {"metric_id": "external_benchmark", "metric_name": "外部 benchmark", "required": ["external_sources", "time_series"]},
    ],
}


METRIC_WAIT_TOKENS = ("待补数据", "无法判断", "不可判断")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _column_names(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def _find_column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    if not aliases:
        return None
    alias_keys = [_normalize(alias) for alias in aliases if _normalize(alias)]
    for column in _column_names(frame):
        column_key = _normalize(column)
        if any(alias == column_key or alias in column_key for alias in alias_keys):
            return column
    return None


def _numeric_series(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _aggregate(series: pd.Series, aggregate: str, frame: pd.DataFrame) -> float | int | None:
    cleaned = series.dropna()
    if aggregate == "sum":
        return float(cleaned.sum()) if not cleaned.empty else None
    if aggregate == "mean":
        return float(cleaned.mean()) if not cleaned.empty else None
    if aggregate == "count":
        return int(len(frame))
    if aggregate == "nunique":
        return int(cleaned.nunique()) if not cleaned.empty else None
    return None


def _format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        number = float(value)
        if number.is_integer():
            return f"{int(number)}"
        return f"{number:.4f}".rstrip("0").rstrip(".")
    return _safe_text(value)


def _dedupe_rows(rows: list[MetricRow]) -> list[MetricRow]:
    seen: set[tuple[str, str]] = set()
    ordered: list[MetricRow] = []
    for row in rows:
        key = (_safe_text(row.get("metric_id")), _safe_text(row.get("formula")))
        if key in seen:
            continue
        seen.add(key)
        ordered.append(row)
    return ordered


def _metric_row(
    *,
    business_profile: str,
    metric_id: str,
    metric_name: str,
    source_columns: list[str],
    formula: str,
    value: Any,
    evidence_level: str,
    confidence: str,
    metric_kind: str,
    business_meaning: str,
    note: str = "",
) -> MetricRow:
    return {
        "business_profile": business_profile,
        "metric_id": metric_id,
        "metric_name": metric_name,
        "source_columns": source_columns,
        "formula": formula,
        "value": _format_value(value),
        "evidence_level": evidence_level,
        "confidence": confidence,
        "metric_kind": metric_kind,
        "business_meaning": business_meaning,
        "note": note,
    }


def _series_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    valid = numerator.notna() & denominator.notna() & (denominator != 0)
    result = pd.Series(dtype="float64", index=denominator.index)
    result.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return result.dropna()


def _find_time_column(frame: pd.DataFrame) -> str | None:
    time_aliases = [
        "date",
        "day",
        "month",
        "week",
        "quarter",
        "year",
        "日期",
        "月份",
        "周",
        "季度",
        "年份",
        "上架时间",
        "下架时间",
    ]
    column = _find_column(frame, time_aliases)
    if column:
        return column
    for candidate in frame.columns:
        series = pd.to_datetime(frame[candidate], errors="coerce")
        if series.notna().mean() >= 0.7:
            return str(candidate)
    return None


def _find_object_columns(frame: pd.DataFrame) -> list[str]:
    aliases = [
        "item_id",
        "product_id",
        "sku_id",
        "spu_id",
        "shop_id",
        "seller_id",
        "brand",
        "category",
        "supplier",
        "campaign",
        "user_id",
        "content_id",
        "project_id",
        "course_id",
        "商品",
        "店铺",
        "类目",
        "品牌",
        "供应商",
        "用户",
        "内容",
        "项目",
        "课程",
    ]
    found: list[str] = []
    for alias in aliases:
        column = _find_column(frame, [alias])
        if column and column not in found:
            found.append(column)
    return found


def _field_presence(frame: pd.DataFrame) -> dict[str, Any]:
    object_columns = _find_object_columns(frame)
    numeric_columns = [
        str(column)
        for column in frame.columns
        if pd.api.types.is_numeric_dtype(frame[column]) or pd.to_numeric(frame[column], errors="coerce").notna().mean() >= 0.7
    ]

    amount_column = _find_column(frame, ["sales_amount", "sales", "revenue", "gmv", "amount", "销售额", "成交额", "金额", "预算", "spend", "budget"])
    quantity_column = _find_column(frame, ["units_sold", "sales_volume", "qty", "quantity", "销量", "件数", "order_count", "orders", "订单数", "订单量"])
    sku_column = _find_column(frame, ["sku", "sku_id", "item_id", "product_id", "goods_id", "商品id", "商品编码", "spu"])
    category_column = _find_column(frame, ["category", "cate", "品类", "类目", "商品类目", "一级类目", "二级类目"])
    supplier_column = _find_column(frame, ["supplier", "vendor", "供应商", "supplier_id", "vendor_id", "卖家", "商家"])
    order_column = _find_column(frame, ["order_id", "订单id", "订单号"])
    cost_column = _find_column(frame, ["cost", "unit_cost", "cogs", "成本", "采购成本", "purchase_price", "进货价"])
    inventory_column = _find_column(frame, ["inventory", "stock", "库存", "beginning_inventory", "ending_inventory", "available_stock"])
    user_column = _find_column(frame, ["user_id", "用户", "uid"])
    event_column = _find_column(frame, ["event_name", "event", "事件"])
    content_column = _find_column(frame, ["content_id", "内容id", "内容", "article_id", "post_id"])
    channel_column = _find_column(frame, ["channel", "渠道", "source"])
    campaign_column = _find_column(frame, ["campaign", "campaign_id", "活动", "活动id"])
    spend_column = _find_column(frame, ["spend", "cost", "投放成本", "预算"])
    conversion_column = _find_column(frame, ["conversion", "pay", "purchase", "转化", "支付", "成交", "下单"])

    cost_key = _normalize(cost_column or "")
    if "freight" in cost_key or "shipping" in cost_key or "logistics" in cost_key:
        cost_column = None
    spend_key = _normalize(spend_column or "")
    if "freight" in spend_key or "shipping" in spend_key or "logistics" in spend_key:
        spend_column = None
    conversion_key = _normalize(conversion_column or "")
    if "timestamp" in conversion_key or conversion_key.endswith("date") or "time" in conversion_key:
        conversion_column = None

    time_column = _find_time_column(frame) or ""
    return {
        "object_columns": object_columns,
        "time_column": time_column,
        "numeric_columns": numeric_columns,
        "has_object_fields": bool(object_columns),
        "has_time_field": bool(time_column),
        "has_numeric_field": bool(numeric_columns),
        "has_amount_field": bool(amount_column),
        "has_quantity_field": bool(quantity_column),
        "has_sku_field": bool(sku_column),
        "has_category_field": bool(category_column),
        "has_supplier_field": bool(supplier_column),
        "has_order_field": bool(order_column),
        "has_cost_field": bool(cost_column),
        "has_inventory_field": bool(inventory_column),
        "has_user_field": bool(user_column),
        "has_event_field": bool(event_column),
        "has_content_field": bool(content_column),
        "has_channel_field": bool(channel_column),
        "has_campaign_field": bool(campaign_column),
        "has_spend_field": bool(spend_column),
        "has_conversion_field": bool(conversion_column),
    }

def _direct_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    specs = DOMAIN_DIRECT_SPECS.get(business_profile, DOMAIN_DIRECT_SPECS["generic_long_business_report"])
    for spec in specs:
        if spec["metric_id"] == "field_count":
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="field_count",
                    metric_name="字段数",
                    source_columns=_column_names(frame),
                    formula="count(columns)",
                    value=len(frame.columns),
                    evidence_level="A_DIRECT",
                    confidence="high",
                    metric_kind="direct_metric",
                    business_meaning="用于判断数据结构丰富度。",
                )
            )
            continue
        if spec["metric_id"] == "record_count":
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="record_count",
                    metric_name="记录数",
                    source_columns=[],
                    formula="count(rows)",
                    value=len(frame),
                    evidence_level="A_DIRECT",
                    confidence="high",
                    metric_kind="direct_metric",
                    business_meaning="用于判断样本规模。",
                )
            )
            continue
        column = _find_column(frame, spec["aliases"])
        if not column:
            continue
        value = _aggregate(_numeric_series(frame, column), spec["aggregate"], frame)
        rows.append(
            _metric_row(
                business_profile=business_profile,
                metric_id=spec["metric_id"],
                metric_name=spec["metric_name"],
                source_columns=[column],
                formula=f"{spec['aggregate']}({column})",
                value=value,
                evidence_level="A_DIRECT",
                confidence="high",
                metric_kind="direct_metric",
                business_meaning=f"直接字段 `{column}` 可用于 {spec['metric_name']} 判断。",
            )
        )
    return _dedupe_rows(rows)


def _common_derived_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    sales_col = _find_column(frame, ["sales_amount", "sales", "revenue", "gmv", "销售额", "成交金额", "支付金额"])
    order_col = _find_column(frame, ["order_count", "orders", "订单量", "订单数"])
    if sales_col and order_col:
        ratio = _series_ratio(_numeric_series(frame, sales_col), _numeric_series(frame, order_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="average_order_value",
                    metric_name="客单价",
                    source_columns=[sales_col, order_col],
                    formula=f"{sales_col} / {order_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断交易结构和价格带质量。",
                )
            )

    impression_col = _find_column(frame, ["impression", "impressions", "曝光", "pv", "view", "browse"])
    click_col = _find_column(frame, ["click", "clicks", "点击"])
    if impression_col and click_col:
        ratio = _series_ratio(_numeric_series(frame, click_col), _numeric_series(frame, impression_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="ctr_derived",
                    metric_name="点击率",
                    source_columns=[click_col, impression_col],
                    formula=f"{click_col} / {impression_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断曝光到点击的承接效率。",
                )
            )

    spend_col = _find_column(frame, ["spend", "cost", "消耗", "花费", "actual_spend"])
    conversion_col = _find_column(frame, ["conversion", "pay", "purchase", "支付", "成交", "注册", "激活"])
    if spend_col and click_col:
        ratio = _series_ratio(_numeric_series(frame, spend_col), _numeric_series(frame, click_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="cpc_derived",
                    metric_name="CPC",
                    source_columns=[spend_col, click_col],
                    formula=f"{spend_col} / {click_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断点击获客成本。",
                )
            )
    if spend_col and impression_col:
        numerator = _numeric_series(frame, spend_col) * 1000
        ratio = _series_ratio(numerator, _numeric_series(frame, impression_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="cpm_derived",
                    metric_name="CPM",
                    source_columns=[spend_col, impression_col],
                    formula=f"{spend_col} * 1000 / {impression_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断曝光获取成本。",
                )
            )
    if spend_col and conversion_col:
        ratio = _series_ratio(_numeric_series(frame, spend_col), _numeric_series(frame, conversion_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="cpa_derived",
                    metric_name="CPA",
                    source_columns=[spend_col, conversion_col],
                    formula=f"{spend_col} / {conversion_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断单次转化成本。",
                )
            )
    if click_col and conversion_col:
        ratio = _series_ratio(_numeric_series(frame, conversion_col), _numeric_series(frame, click_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="conversion_rate_derived",
                    metric_name="转化率",
                    source_columns=[conversion_col, click_col],
                    formula=f"{conversion_col} / {click_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断点击到转化效率。",
                    note="如果点击和转化不在同一口径下，该指标需要人工复核。",
                )
            )
    order_id_col = _find_column(frame, ["order_id", "订单id", "订单号"])
    if sales_col and order_id_col and not order_col:
        distinct_orders = pd.Series(frame[order_id_col].astype(str)).replace({"": pd.NA}).dropna()
        if not distinct_orders.empty and distinct_orders.nunique() > 0:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="order_count_from_id",
                    metric_name="订单数",
                    source_columns=[order_id_col],
                    formula=f"nunique({order_id_col})",
                    value=int(distinct_orders.nunique()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用订单ID直接反推订单量。",
                )
            )
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="average_order_value_from_order_id",
                    metric_name="客单价",
                    source_columns=[sales_col, order_id_col],
                    formula=f"sum({sales_col}) / nunique({order_id_col})",
                    value=float(_numeric_series(frame, sales_col).sum() / distinct_orders.nunique()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="当订单量只有明细订单ID时，仍可计算客单价。",
                )
            )
    return rows


def _generic_contribution_and_trend_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    object_columns = _find_object_columns(frame)
    object_col = object_columns[0] if object_columns else None
    time_col = _find_time_column(frame)
    amount_col = _find_column(frame, ["sales_amount", "sales", "revenue", "gmv", "amount", "支付金额", "成交金额", "收入", "金额", "spend", "budget"])
    quantity_col = _find_column(frame, ["units_sold", "sales_volume", "qty", "quantity", "件数", "销量", "order_count", "orders", "订单数", "订单量"])

    if object_col and amount_col:
        data = pd.DataFrame({"object": frame[object_col].astype(str), "amount": _numeric_series(frame, amount_col)}).dropna()
        if not data.empty and data["amount"].sum() != 0:
            grouped = data.groupby("object", dropna=False)["amount"].sum().sort_values(ascending=False)
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="top_object_amount_contribution",
                    metric_name="对象金额贡献",
                    source_columns=[object_col, amount_col],
                    formula=f"top1(sum({amount_col}) by {object_col}) / sum({amount_col})",
                    value=float(grouped.iloc[0] / grouped.sum()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning=f"对象 `{grouped.index[0]}` 的金额贡献可用于判断集中度。",
                )
            )

    if object_col and quantity_col:
        data = pd.DataFrame({"object": frame[object_col].astype(str), "quantity": _numeric_series(frame, quantity_col)}).dropna()
        if not data.empty and data["quantity"].sum() != 0:
            grouped = data.groupby("object", dropna=False)["quantity"].sum().sort_values(ascending=False)
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="top_object_quantity_contribution",
                    metric_name="对象数量贡献",
                    source_columns=[object_col, quantity_col],
                    formula=f"top1(sum({quantity_col}) by {object_col}) / sum({quantity_col})",
                    value=float(grouped.iloc[0] / grouped.sum()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning=f"对象 `{grouped.index[0]}` 的规模贡献可用于判断结构集中度。",
                )
            )

    trend_metric_col = amount_col or quantity_col
    if object_col and time_col and trend_metric_col:
        parsed_time = pd.to_datetime(frame[time_col], errors="coerce")
        data = pd.DataFrame(
            {
                "time": parsed_time.dt.to_period("D").astype(str),
                "metric": _numeric_series(frame, trend_metric_col),
            }
        )
        data = data[data["time"] != "NaT"]
        if not data.empty and data["time"].nunique() >= 2:
            grouped = data.groupby("time", dropna=False)["metric"].sum().sort_index()
            first_value = float(grouped.iloc[0] or 0)
            last_value = float(grouped.iloc[-1] or 0)
            if first_value != 0:
                rows.append(
                    _metric_row(
                        business_profile=business_profile,
                        metric_id="overall_trend_change",
                        metric_name="趋势变化",
                        source_columns=[object_col, time_col, trend_metric_col],
                        formula=f"last(sum({trend_metric_col}) by {time_col}) / first(sum({trend_metric_col}) by {time_col}) - 1",
                        value=float((last_value - first_value) / first_value),
                        evidence_level="B_DERIVED",
                        confidence="medium",
                        metric_kind="derived_metric",
                        business_meaning="对象字段、时间字段和数值字段同时存在时，应先尝试趋势判断。",
                    )
                )
    return rows


def _procurement_ecommerce_derived_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    sku_col = _find_column(frame, ["sku_id", "item_id", "product_id", "商品id", "商品"])
    sales_col = _find_column(frame, ["sales_amount", "sales", "revenue", "gmv", "销售额", "成交金额"])
    inventory_col = _find_column(frame, ["inventory", "stock", "库存"])
    order_col = _find_column(frame, ["order_count", "orders", "订单量", "订单数"])
    review_count_col = _find_column(frame, ["review_count", "comment_count", "评论量", "评价量", "review"])
    pay_col = _find_column(frame, ["pay", "purchase", "支付", "成交"])
    add_to_cart_col = _find_column(frame, ["add_to_cart", "cart", "加购"])
    gross_profit_col = _find_column(frame, ["gross_profit", "gross_margin", "毛利"])

    if sku_col and sales_col:
        sales_series = _numeric_series(frame, sales_col)
        grouped = pd.DataFrame({sku_col: frame[sku_col].astype(str), sales_col: sales_series}).dropna()
        if not grouped.empty and grouped[sales_col].sum() != 0:
            top_share = grouped.groupby(sku_col)[sales_col].sum().sort_values(ascending=False).head(1).sum() / grouped[sales_col].sum()
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="top_object_share",
                    metric_name="头部商品销售占比",
                    source_columns=[sku_col, sales_col],
                    formula=f"top1(sum({sales_col}) by {sku_col}) / sum({sales_col})",
                    value=float(top_share),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断销售是否过度集中在少数商品。",
                )
            )

    if inventory_col and sales_col:
        ratio = _series_ratio(_numeric_series(frame, inventory_col), _numeric_series(frame, sales_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="inventory_to_sales_ratio",
                    metric_name="库存销售比",
                    source_columns=[inventory_col, sales_col],
                    formula=f"{inventory_col} / {sales_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning="可用于初步判断库存与动销是否匹配。",
                    note="这是截面代理比值，不等同于标准库存周转率。",
                )
            )

    if pay_col and add_to_cart_col:
        ratio = _series_ratio(_numeric_series(frame, pay_col), _numeric_series(frame, add_to_cart_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="pay_conversion_rate",
                    metric_name="支付转化率",
                    source_columns=[pay_col, add_to_cart_col],
                    formula=f"{pay_col} / {add_to_cart_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断加购到支付转化效率。",
                    note="仅在加购与支付口径一致时可作为强判断依据。",
                )
            )

    if gross_profit_col and sales_col:
        ratio = _series_ratio(_numeric_series(frame, gross_profit_col), _numeric_series(frame, sales_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="gross_margin_rate_derived",
                    metric_name="毛利率",
                    source_columns=[gross_profit_col, sales_col],
                    formula=f"{gross_profit_col} / {sales_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断销售额中的毛利贡献。",
                )
            )
    return rows


def _internet_derived_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    register_col = _find_column(frame, ["register", "registrations", "注册"])
    activation_col = _find_column(frame, ["activation", "激活"])
    revenue_col = _find_column(frame, ["revenue", "收入"])
    active_col = _find_column(frame, ["dau", "mau", "wau", "日活", "月活", "周活"])
    user_col = _find_column(frame, ["user_id", "用户", "uid"])
    time_col = _find_time_column(frame)

    if register_col and activation_col:
        ratio = _series_ratio(_numeric_series(frame, activation_col), _numeric_series(frame, register_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="activation_rate",
                    metric_name="激活率",
                    source_columns=[activation_col, register_col],
                    formula=f"{activation_col} / {register_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断注册到激活的承接效率。",
                )
            )

    if revenue_col and active_col:
        ratio = _series_ratio(_numeric_series(frame, revenue_col), _numeric_series(frame, active_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="revenue_per_active_user",
                    metric_name="活跃用户收入",
                    source_columns=[revenue_col, active_col],
                    formula=f"{revenue_col} / {active_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断收入与活跃规模匹配度。",
                )
            )

    if user_col and time_col:
        parsed = pd.to_datetime(frame[time_col], errors="coerce")
        grouped = pd.DataFrame({"time": parsed.dt.date, "user": frame[user_col].astype(str)}).dropna()
        if not grouped.empty:
            daily_users = grouped.groupby("time")["user"].nunique().sort_index()
            if len(daily_users) >= 2:
                change = daily_users.iloc[-1] - daily_users.iloc[0]
                rows.append(
                    _metric_row(
                        business_profile=business_profile,
                        metric_id="active_user_change",
                        metric_name="活跃用户变动",
                        source_columns=[user_col, time_col],
                        formula=f"nunique({user_col}) by {time_col}; last - first",
                        value=float(change),
                        evidence_level="B_DERIVED",
                        confidence="medium",
                        metric_kind="derived_metric",
                        business_meaning="可用于判断观察窗口内活跃用户规模变化。",
                    )
                )
    return rows


def _generic_derived_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    budget_col = _find_column(frame, ["budget", "预算", "planned_budget"])
    actual_col = _find_column(frame, ["actual_spend", "spend", "cost", "actual", "花费", "成本", "实际"])
    progress_col = _find_column(frame, ["progress", "completion", "完成率", "进度"])
    target_col = _find_column(frame, ["target", "goal", "plan", "目标", "计划值", "kpi"])

    if budget_col and actual_col:
        ratio = _series_ratio(_numeric_series(frame, actual_col), _numeric_series(frame, budget_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="budget_spend_rate",
                    metric_name="预算执行率",
                    source_columns=[actual_col, budget_col],
                    formula=f"{actual_col} / {budget_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="high",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断预算执行快慢。",
                )
            )

    if progress_col and target_col:
        ratio = _series_ratio(_numeric_series(frame, progress_col), _numeric_series(frame, target_col))
        if not ratio.empty:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="progress_to_target_ratio",
                    metric_name="进度目标比",
                    source_columns=[progress_col, target_col],
                    formula=f"{progress_col} / {target_col}",
                    value=float(ratio.mean()),
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    metric_kind="derived_metric",
                    business_meaning="可用于判断当前进度与目标值是否匹配。",
                )
            )
    return rows


def _industry_context_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    object_columns = _find_object_columns(frame)
    grain = "unknown_grain"
    if any(_find_column(frame, [alias]) for alias in ["item_id", "product_id", "sku_id", "spu_id", "商品", "sku"]):
        grain = "product_grain"
    elif any(_find_column(frame, [alias]) for alias in ["shop_id", "seller_id", "store_id", "店铺", "商家"]):
        grain = "shop_grain"
    elif any(_find_column(frame, [alias]) for alias in ["user_id", "channel", "campaign", "content_id"]):
        grain = "traffic_or_user_grain"
    return [
        _metric_row(
            business_profile=business_profile,
            metric_id="field_count",
            metric_name="字段数",
            source_columns=_column_names(frame),
            formula="count(columns)",
            value=len(frame.columns),
            evidence_level="A_DIRECT",
            confidence="high",
            metric_kind="direct_metric",
            business_meaning="用于判断数据结构复杂度。",
        ),
        _metric_row(
            business_profile=business_profile,
            metric_id="record_count",
            metric_name="记录数",
            source_columns=[],
            formula="count(rows)",
            value=len(frame),
            evidence_level="A_DIRECT",
            confidence="high",
            metric_kind="direct_metric",
            business_meaning="用于判断样本规模。",
        ),
        _metric_row(
            business_profile=business_profile,
            metric_id="object_grain_signal",
            metric_name="对象粒度信号",
            source_columns=object_columns,
            formula="match(object-like columns)",
            value=grain,
            evidence_level="C_PROXY",
            confidence="medium" if object_columns else "low",
            metric_kind="proxy_metric",
            business_meaning="用于辅助判断行业、平台和业务模式。",
        ),
    ]


def _derived_metrics(
    frame: pd.DataFrame,
    business_profile: str,
    analysis_program_derived_metrics: list[dict[str, Any]] | None = None,
) -> list[MetricRow]:
    rows = _common_derived_metrics(frame, business_profile)
    rows.extend(_generic_contribution_and_trend_metrics(frame, business_profile))
    if business_profile in {"procurement_sales_report", "ecommerce_product_operations_report"}:
        rows.extend(_procurement_ecommerce_derived_metrics(frame, business_profile))
    elif business_profile == "internet_operations_report":
        rows.extend(_internet_derived_metrics(frame, business_profile))
    elif business_profile == "generic_long_business_report":
        rows.extend(_generic_derived_metrics(frame, business_profile))
    elif business_profile == "independent_industry_research_chain":
        rows.extend(_industry_context_metrics(frame, business_profile))

    for item in analysis_program_derived_metrics or []:
        metric_id = _safe_text(item.get("metric") or item.get("metric_id") or item.get("name"))
        if not metric_id:
            continue
        rows.append(
            _metric_row(
                business_profile=business_profile,
                metric_id=metric_id,
                metric_name=_safe_text(item.get("metric_name") or metric_id),
                source_columns=list(item.get("source_fields") or []),
                formula=_safe_text(item.get("formula") or "analysis_program_derived_metric"),
                value=item.get("value") or item.get("summary") or "available_in_program_bundle",
                evidence_level="B_DERIVED",
                confidence=_safe_text(item.get("confidence") or "medium"),
                metric_kind="derived_metric",
                business_meaning=_safe_text(item.get("business_value") or "Imported from analysis program derived metrics."),
                note="Imported from analysis_program_service.",
            )
        )
    return _dedupe_rows(rows)


def _proxy_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    if business_profile in {"procurement_sales_report", "ecommerce_product_operations_report"}:
        rating_col = _find_column(frame, ["rating", "review_score", "评分", "好评率"])
        refund_col = _find_column(frame, ["refund_rate", "退款率", "退货率"])
        review_count_col = _find_column(frame, ["review_count", "comment_count", "评论量", "评价量", "review"])
        order_col = _find_column(frame, ["order_count", "orders", "订单量", "订单数"])
        if rating_col:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="quality_proxy",
                    metric_name="商品质量代理",
                    source_columns=[rating_col],
                    formula=f"mean({rating_col})",
                    value=_aggregate(_numeric_series(frame, rating_col), "mean", frame),
                    evidence_level="C_PROXY",
                    confidence="medium",
                    metric_kind="proxy_metric",
                    business_meaning="评价分可作为质量和售后体验的代理信号。",
                )
            )
        if refund_col:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="aftersales_risk_proxy",
                    metric_name="售后风险代理",
                    source_columns=[refund_col],
                    formula=f"mean({refund_col})",
                    value=_aggregate(_numeric_series(frame, refund_col), "mean", frame),
                    evidence_level="C_PROXY",
                    confidence="medium",
                    metric_kind="proxy_metric",
                    business_meaning="退款率可作为售后压力的代理信号。",
                )
            )
        if review_count_col and order_col:
            ratio = _series_ratio(_numeric_series(frame, review_count_col), _numeric_series(frame, order_col))
            if not ratio.empty:
                rows.append(
                    _metric_row(
                        business_profile=business_profile,
                        metric_id="review_per_order_proxy",
                        metric_name="单均评价量代理",
                        source_columns=[review_count_col, order_col],
                        formula=f"{review_count_col} / {order_col}",
                        value=float(ratio.mean()),
                        evidence_level="C_PROXY",
                        confidence="medium",
                        metric_kind="proxy_metric",
                        business_meaning="可作为售后和评价活跃度的代理观察项。",
                    )
                )
    elif business_profile == "internet_operations_report":
        like_col = _find_column(frame, ["like", "likes", "点赞"])
        share_col = _find_column(frame, ["share", "shares", "分享"])
        view_col = _find_column(frame, ["view", "views", "曝光", "pv"])
        if like_col and view_col:
            ratio = _series_ratio(_numeric_series(frame, like_col), _numeric_series(frame, view_col))
            if not ratio.empty:
                rows.append(
                    _metric_row(
                        business_profile=business_profile,
                        metric_id="engagement_proxy",
                        metric_name="互动率代理",
                        source_columns=[like_col, view_col],
                        formula=f"{like_col} / {view_col}",
                        value=float(ratio.mean()),
                        evidence_level="C_PROXY",
                        confidence="medium",
                        metric_kind="proxy_metric",
                        business_meaning="可作为内容吸引力的代理指标。",
                    )
                )
        if share_col and view_col:
            ratio = _series_ratio(_numeric_series(frame, share_col), _numeric_series(frame, view_col))
            if not ratio.empty:
                rows.append(
                    _metric_row(
                        business_profile=business_profile,
                        metric_id="virality_proxy",
                        metric_name="传播率代理",
                        source_columns=[share_col, view_col],
                        formula=f"{share_col} / {view_col}",
                        value=float(ratio.mean()),
                        evidence_level="C_PROXY",
                        confidence="low",
                        metric_kind="proxy_metric",
                        business_meaning="可作为传播效率的代理观察项。",
                    )
                )
    elif business_profile == "media_campaign_report":
        click_col = _find_column(frame, ["click", "clicks", "点击"])
        spend_col = _find_column(frame, ["spend", "cost", "消耗", "花费"])
        if click_col and spend_col:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="traffic_efficiency_proxy",
                    metric_name="流量效率代理",
                    source_columns=[click_col, spend_col],
                    formula=f"{click_col} / {spend_col}",
                    value=_format_value(
                        _aggregate(_series_ratio(_numeric_series(frame, click_col), _numeric_series(frame, spend_col)), "mean", frame)
                    ),
                    evidence_level="C_PROXY",
                    confidence="medium",
                    metric_kind="proxy_metric",
                    business_meaning="在缺少转化时可用作投放效率的代理观察项。",
                )
            )
    elif business_profile == "generic_long_business_report":
        risk_col = _find_column(frame, ["risk_level", "risk", "风险"])
        status_col = _find_column(frame, ["status", "状态"])
        if risk_col or status_col:
            rows.append(
                _metric_row(
                    business_profile=business_profile,
                    metric_id="execution_risk_proxy",
                    metric_name="执行风险代理",
                    source_columns=[col for col in [risk_col, status_col] if col],
                    formula="categorical risk/status scan",
                    value="available",
                    evidence_level="C_PROXY",
                    confidence="medium",
                    metric_kind="proxy_metric",
                    business_meaning="风险等级和状态字段可作为执行异常的代理观察项。",
                )
            )
    return _dedupe_rows(rows)


def _hypothesis_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    notes = {
        "procurement_sales_report": "如果补齐采购价、到货周期和库存口径，可进一步判断补货、清仓和供应商利润贡献。",
        "ecommerce_product_operations_report": "如果补齐库存、履约和售后全口径，可进一步判断高销量高售后与低销量高库存的成因。",
        "internet_operations_report": "如果补齐 cohort、D30 留存和渠道成本，可进一步判断长期用户质量与 ROI。",
        "media_campaign_report": "如果补齐转化回传和收入口径，可进一步判断 CPA、ROAS 和预算加码空间。",
        "generic_long_business_report": "如果补齐目标值、计划值和负责人，可进一步判断目标达成与责任归因。",
        "independent_industry_research_chain": "如果补齐行业、平台和外部口径资料，可进一步缩小研究问题和 benchmark 边界。",
    }
    return [
        _metric_row(
            business_profile=business_profile,
            metric_id="next_validation_question",
            metric_name="待验证问题",
            source_columns=[],
            formula="diagnostic hypothesis",
            value="requires_validation",
            evidence_level="D_HYPOTHESIS",
            confidence="low",
            metric_kind="hypothesis_metric",
            business_meaning=notes.get(business_profile, "需要补充字段后再验证。"),
        )
    ]


def _unsupported_metrics(frame: pd.DataFrame, business_profile: str) -> list[MetricRow]:
    rows: list[MetricRow] = []
    specs = DOMAIN_UNSUPPORTED_SPECS.get(business_profile, [])
    normalized_columns = [_normalize(column) for column in frame.columns]
    for spec in specs:
        missing = [
            required
            for required in spec["required"]
            if not any(_normalize(required) == column or _normalize(required) in column for column in normalized_columns)
        ]
        if not missing:
            continue
        rows.append(
            _metric_row(
                business_profile=business_profile,
                metric_id=spec["metric_id"],
                metric_name=spec["metric_name"],
                source_columns=[],
                formula="unsupported_without_required_fields",
                value="unsupported",
                evidence_level="E_UNSUPPORTED",
                confidence="unsupported",
                metric_kind="unsupported_metric",
                business_meaning=f"缺少字段: {', '.join(missing)}",
                note="Only mark unsupported after direct / derived / proxy / hypothesis checks.",
            )
        )
    return rows


def _domain_notes(
    *,
    business_profile: str,
    direct_metrics: list[MetricRow],
    derived_metrics: list[MetricRow],
    proxy_metrics: list[MetricRow],
    unsupported_metrics: list[MetricRow],
    time_column: str | None,
    object_columns: list[str],
) -> list[str]:
    notes = [
        f"metric_mining_order=direct>derived>proxy>hypothesis>unsupported",
        f"direct_metric_count={len(direct_metrics)}",
        f"derived_metric_count={len(derived_metrics)}",
        f"proxy_metric_count={len(proxy_metrics)}",
        f"unsupported_metric_count={len(unsupported_metrics)}",
    ]
    if time_column:
        notes.append(f"time_signal={time_column}")
    if object_columns:
        notes.append(f"object_signals={', '.join(object_columns[:5])}")
    if business_profile == "independent_industry_research_chain":
        notes.append("Use mined object/time/value signals only for research scoping, not for current-business conclusions.")
    return notes


def build_universal_metric_mining_result(
    *,
    frame: pd.DataFrame,
    business_profile: str,
    router_result: dict[str, Any] | None = None,
    semantic_mapping: dict[str, Any] | None = None,
    analysis_program_derived_metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    profile = _safe_text(business_profile) or "generic_long_business_report"
    field_presence = _field_presence(frame)
    direct_metrics = _direct_metrics(frame, profile)
    derived_metrics = _derived_metrics(frame, profile, analysis_program_derived_metrics)
    proxy_metrics = _proxy_metrics(frame, profile)
    hypothesis_metrics = _hypothesis_metrics(frame, profile)
    unsupported_metrics = _unsupported_metrics(frame, profile)
    time_column = _find_time_column(frame)
    object_columns = _find_object_columns(frame)

    direct_ids = {row["metric_id"] for row in direct_metrics}
    derived_ids = {row["metric_id"] for row in derived_metrics}
    proxy_ids = {row["metric_id"] for row in proxy_metrics}
    hypothesis_ids = {row["metric_id"] for row in hypothesis_metrics}
    unsupported_ids = {row["metric_id"] for row in unsupported_metrics}

    result = {
        "business_profile": profile,
        "router_result": router_result or {},
        "field_presence": field_presence,
        "semantic_mapping_summary": {
            "mapped_column_count": len((semantic_mapping or {}).get("columns") or []),
        },
        "recommended_report_chain": profile,
        "direct_metrics": direct_metrics,
        "derived_metrics": derived_metrics,
        "proxy_metrics": proxy_metrics,
        "hypothesis_metrics": hypothesis_metrics,
        "unsupported_metrics": unsupported_metrics,
        "domain_metric_registry": {
            "business_profile": profile,
            "direct_metrics": sorted(direct_ids),
            "derived_metrics": sorted(derived_ids),
            "proxy_metrics": sorted(proxy_ids),
            "hypothesis_metrics": sorted(hypothesis_ids),
            "unsupported_metrics": sorted(unsupported_ids),
            "recommended_report_chain": profile,
            "domain_specific_notes": _domain_notes(
                business_profile=profile,
                direct_metrics=direct_metrics,
                derived_metrics=derived_metrics,
                proxy_metrics=proxy_metrics,
                unsupported_metrics=unsupported_metrics,
                time_column=time_column,
                object_columns=object_columns,
            ),
        },
        "summary": {
            "time_column": time_column or "",
            "object_columns": object_columns,
            "calculable_metric_count": len(direct_metrics) + len(derived_metrics),
            "proxy_metric_count": len(proxy_metrics),
            "unsupported_metric_count": len(unsupported_metrics),
        },
    }
    return result


def _write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def write_universal_metric_mining_outputs(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result_path = out_dir / "universal_metric_mining_result.json"
    report_path = out_dir / "universal_metric_mining_report.md"
    derived_csv_path = out_dir / "derived_metrics_table.csv"
    proxy_csv_path = out_dir / "proxy_metrics_table.csv"
    unsupported_csv_path = out_dir / "unsupported_metrics_table.csv"
    confidence_csv_path = out_dir / "inference_confidence_registry.csv"
    registry_path = out_dir / "domain_metric_registry.json"

    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    registry_path.write_text(
        json.dumps(payload.get("domain_metric_registry") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    metric_headers = [
        "business_profile",
        "metric_id",
        "metric_name",
        "source_columns",
        "formula",
        "value",
        "evidence_level",
        "confidence",
        "metric_kind",
        "business_meaning",
        "note",
    ]
    _write_csv(derived_csv_path, payload.get("derived_metrics") or [], metric_headers)
    _write_csv(proxy_csv_path, payload.get("proxy_metrics") or [], metric_headers)
    _write_csv(unsupported_csv_path, payload.get("unsupported_metrics") or [], metric_headers)

    confidence_rows: list[dict[str, Any]] = []
    for group_name in ["direct_metrics", "derived_metrics", "proxy_metrics", "hypothesis_metrics", "unsupported_metrics"]:
        for row in payload.get(group_name) or []:
            confidence_rows.append(
                {
                    "business_profile": payload.get("business_profile", ""),
                    "metric_id": row.get("metric_id", ""),
                    "metric_name": row.get("metric_name", ""),
                    "metric_group": group_name,
                    "evidence_level": row.get("evidence_level", ""),
                    "confidence": row.get("confidence", ""),
                    "value": row.get("value", ""),
                    "note": row.get("note", ""),
                }
            )
    _write_csv(
        confidence_csv_path,
        confidence_rows,
        ["business_profile", "metric_id", "metric_name", "metric_group", "evidence_level", "confidence", "value", "note"],
    )

    domain_registry = payload.get("domain_metric_registry") or {}
    direct_lines = [
        f"- `{row['metric_id']}`: {row['metric_name']} ({row['value']}) [{row['evidence_level']}/{row['confidence']}]"
        for row in payload.get("direct_metrics") or []
    ] or ["- none"]
    derived_lines = [
        f"- `{row['metric_id']}`: {row['metric_name']} = {row['formula']} -> {row['value']} [{row['evidence_level']}/{row['confidence']}]"
        for row in payload.get("derived_metrics") or []
    ] or ["- none"]
    proxy_lines = [
        f"- `{row['metric_id']}`: {row['metric_name']} ({row['note'] or row['business_meaning']}) [{row['evidence_level']}/{row['confidence']}]"
        for row in payload.get("proxy_metrics") or []
    ] or ["- none"]
    hypothesis_lines = [
        f"- `{row['metric_id']}`: {row['business_meaning']} [{row['evidence_level']}/{row['confidence']}]"
        for row in payload.get("hypothesis_metrics") or []
    ] or ["- none"]
    unsupported_lines = [
        f"- `{row['metric_id']}`: {row['business_meaning']} [{row['evidence_level']}/{row['confidence']}]"
        for row in payload.get("unsupported_metrics") or []
    ] or ["- none"]
    domain_note_lines = [f"- {note}" for note in domain_registry.get("domain_specific_notes") or []] or ["- none"]

    report_lines = [
        "# universal_metric_mining_report",
        "",
        f"- business_profile: `{payload.get('business_profile', '')}`",
        f"- recommended_report_chain: `{domain_registry.get('recommended_report_chain', '')}`",
        f"- calculable_metric_count: `{payload.get('summary', {}).get('calculable_metric_count', 0)}`",
        f"- proxy_metric_count: `{payload.get('summary', {}).get('proxy_metric_count', 0)}`",
        f"- unsupported_metric_count: `{payload.get('summary', {}).get('unsupported_metric_count', 0)}`",
        "",
        "## Direct Metrics",
        *direct_lines,
        "",
        "## Derived Metrics",
        *derived_lines,
        "",
        "## Proxy Metrics",
        *proxy_lines,
        "",
        "## Hypothesis Metrics",
        *hypothesis_lines,
        "",
        "## Unsupported Metrics",
        *unsupported_lines,
        "",
        "## Domain Notes",
        *domain_note_lines,
        "",
    ]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return {
        "universal_metric_mining_result.json": str(result_path.resolve()),
        "universal_metric_mining_report.md": str(report_path.resolve()),
        "derived_metrics_table.csv": str(derived_csv_path.resolve()),
        "proxy_metrics_table.csv": str(proxy_csv_path.resolve()),
        "unsupported_metrics_table.csv": str(unsupported_csv_path.resolve()),
        "inference_confidence_registry.csv": str(confidence_csv_path.resolve()),
        "domain_metric_registry.json": str(registry_path.resolve()),
    }


def metric_mining_quality_failures(
    *,
    management_markdown: str,
    metric_payload: dict[str, Any] | None,
    business_profile: str,
) -> list[str]:
    if not metric_payload:
        return []
    calculable_metrics = [
        *(metric_payload.get("direct_metrics") or []),
        *(metric_payload.get("derived_metrics") or []),
    ]
    if not calculable_metrics:
        return []

    markdown = _safe_text(management_markdown)
    if not any(token in markdown for token in METRIC_WAIT_TOKENS):
        return []

    if business_profile == "procurement_sales_report" and any(
        token in markdown
        for token in (
            "procurement_sales_derived_metrics",
            "sku_sales_ranking",
            "category_contribution",
            "price_band_summary",
            "sales_trend",
        )
    ):
        return []

    named_metrics = [
        _safe_text(row.get("metric_name") or row.get("metric_id"))
        for row in calculable_metrics[:10]
        if _safe_text(row.get("metric_name") or row.get("metric_id"))
    ]
    if any(name and name in markdown for name in named_metrics):
        return []

    return [
        f"universal_metric_mining_detected_calculable_metrics_but_report_still_says_wait_for_data[{business_profile}]"
    ]
