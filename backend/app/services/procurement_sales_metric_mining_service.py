from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd


FIELD_ROLE_ALIASES: dict[str, list[str]] = {
    "sku_field": ["sku", "sku_id", "item_id", "product_id", "goods_id", "商品id", "商品编码", "sku", "spu"],
    "product_name_field": ["商品名称", "品名", "product_name", "goods_name", "item_name", "title"],
    "category_field": ["category", "cate", "category_id", "商品类目", "类目", "品类", "一级类目", "二级类目", "三级类目"],
    "supplier_field": ["supplier", "supplier_id", "vendor", "vendor_id", "供应商", "供应商id", "商家", "店铺", "采销负责人"],
    "time_field": ["date", "dt", "day", "month", "stat_date", "order_date", "purchase_date", "日期", "统计日期", "订单日期", "采购日期"],
    "sales_amount_field": ["sales", "revenue", "gmv", "order_amount", "pay_amount", "销售额", "gmv", "成交金额", "支付金额"],
    "units_sold_field": ["qty_sold", "units_sold", "sales_volume", "销量", "件数", "销售数量"],
    "order_count_field": ["order_count", "orders", "订单量", "订单数", "pay_order"],
    "purchase_amount_field": ["purchase_amount", "procurement_amount", "采购金额", "进货金额"],
    "purchase_qty_field": ["purchase_qty", "procurement_qty", "采购数量", "进货数量"],
    "purchase_price_field": ["purchase_price", "procurement_price", "进货价", "采购价", "供货价"],
    "cost_field": ["cost", "unit_cost", "total_cost", "cogs", "成本", "单位成本", "总成本", "进货成本"],
    "inventory_field": ["inventory", "stock", "ending_inventory", "available_stock", "库存", "期末库存", "可售库存"],
    "beginning_inventory_field": ["beginning_inventory", "期初库存"],
    "ending_inventory_field": ["ending_inventory", "期末库存"],
    "sale_price_field": ["price", "sale_price", "list_price", "售价", "标价", "到手价"],
    "original_price_field": ["original_price", "list_price", "原价", "吊牌价"],
    "discount_field": ["discount_price", "discount", "折扣价", "折扣"],
    "promotion_field": ["promotion", "coupon", "subsidy", "campaign", "促销", "优惠券", "补贴", "活动"],
    "click_field": ["click", "clicks", "点击"],
    "conversion_field": ["conversion", "pay", "purchase", "支付", "转化"],
}


WAIT_ACTION_PREFIXES = ("补", "待补", "先补")
PROFIT_TERMS = ("毛利", "利润", "毛利率", "roi")
INVENTORY_RISK_TERMS = ("缺货", "滞销库存", "库存周转", "压货", "清仓")
NEGATION_TERMS = ("??", "??", "??", "??", "??", "??", "??", "???", "??", "???")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _find_column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized_aliases = [_normalize(alias) for alias in aliases if _normalize(alias)]
    for column in frame.columns.astype(str):
        key = _normalize(column)
        if any(alias == key or alias in key for alias in normalized_aliases):
            return str(column)
    return None


def _is_procurement_spend_ledger_mode(frame: pd.DataFrame, roles: dict[str, str]) -> bool:
    if not roles.get("supplier_field") or not roles.get("time_field") or not roles.get("sales_amount_field"):
        return False
    if roles.get("sku_field"):
        return False
    lowered_columns = [str(column).lower() for column in frame.columns]
    if any("customer" in column for column in lowered_columns):
        return False
    if any("deliver" in column or "fulfillment" in column for column in lowered_columns):
        return False
    return True


def _numeric(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _parse_time_series(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(dtype="datetime64[ns]")
    series = frame[column]
    sample = next((str(value).strip() for value in series.tolist() if str(value).strip()), "")
    dayfirst = bool(sample and len(sample) >= 10 and sample[2:3] == "/" and sample[5:6] == "/")
    return pd.to_datetime(series, errors="coerce", dayfirst=dayfirst)


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    valid = numerator.notna() & denominator.notna() & (denominator != 0)
    result = pd.Series(dtype="float64", index=denominator.index)
    result.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return result.dropna()


def _series_mean(series: pd.Series) -> float | None:
    cleaned = series.dropna()
    return float(cleaned.mean()) if not cleaned.empty else None


def _format_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        number = float(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:.4f}".rstrip("0").rstrip(".")
    return _safe_text(value)


def _infer_field_roles(frame: pd.DataFrame) -> dict[str, str]:
    roles: dict[str, str] = {}
    for role, aliases in FIELD_ROLE_ALIASES.items():
        roles[role] = _find_column(frame, aliases) or ""
    return roles


def _base_metric_row(
    *,
    metric_id: str,
    metric_name: str,
    object_type: str,
    object_id: str,
    object_name: str,
    metric_value: Any,
    benchmark_or_threshold: str,
    evidence_level: str,
    confidence: str,
    recommended_action: str,
    action_boundary: str,
    formula: str,
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "metric_name": metric_name,
        "object_type": object_type,
        "object_id": object_id,
        "object_name": object_name,
        "metric_value": _format_number(metric_value),
        "benchmark_or_threshold": benchmark_or_threshold,
        "evidence_level": evidence_level,
        "confidence": confidence,
        "recommended_action": recommended_action,
        "action_boundary": action_boundary,
        "formula": formula,
    }


def _aggregate_by_dimension(
    frame: pd.DataFrame,
    *,
    group_col: str,
    object_type: str,
    roles: dict[str, str],
) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "group": frame[group_col].astype(str),
            "sales": _numeric(frame, roles.get("sales_amount_field")),
            "units_sold": _numeric(frame, roles.get("units_sold_field")),
            "orders": _numeric(frame, roles.get("order_count_field")),
            "purchase_amount": _numeric(frame, roles.get("purchase_amount_field")),
            "purchase_qty": _numeric(frame, roles.get("purchase_qty_field")),
            "purchase_price": _numeric(frame, roles.get("purchase_price_field")),
            "cost": _numeric(frame, roles.get("cost_field")),
            "inventory": _numeric(frame, roles.get("inventory_field")),
            "beginning_inventory": _numeric(frame, roles.get("beginning_inventory_field")),
            "ending_inventory": _numeric(frame, roles.get("ending_inventory_field")),
            "sale_price": _numeric(frame, roles.get("sale_price_field")),
            "original_price": _numeric(frame, roles.get("original_price_field")),
            "click": _numeric(frame, roles.get("click_field")),
            "conversion": _numeric(frame, roles.get("conversion_field")),
        }
    )
    if not data["beginning_inventory"].dropna().empty or not data["ending_inventory"].dropna().empty:
        data["average_inventory"] = (data["beginning_inventory"].fillna(0) + data["ending_inventory"].fillna(0)) / 2
    else:
        data["average_inventory"] = data["inventory"]
    if roles.get("sale_price_field") and roles.get("purchase_price_field"):
        data["unit_gross_profit"] = data["sale_price"] - data["purchase_price"]
        data["unit_gross_margin"] = _ratio(data["unit_gross_profit"], data["sale_price"]).reindex(data.index)
    else:
        data["unit_gross_profit"] = pd.Series(dtype="float64")
        data["unit_gross_margin"] = pd.Series(dtype="float64")
    if roles.get("sales_amount_field") and roles.get("cost_field"):
        data["gross_profit"] = data["sales"] - data["cost"]
        data["gross_margin"] = _ratio(data["gross_profit"], data["sales"]).reindex(data.index)
    else:
        data["gross_profit"] = pd.Series(dtype="float64")
        data["gross_margin"] = pd.Series(dtype="float64")
    if roles.get("sale_price_field") and roles.get("original_price_field"):
        data["discount_rate"] = (1 - _ratio(data["sale_price"], data["original_price"])).reindex(data.index)
    else:
        data["discount_rate"] = pd.Series(dtype="float64")

    grouped = data.groupby("group", dropna=False).agg(
        sales=("sales", "sum"),
        units_sold=("units_sold", "sum"),
        orders=("orders", "sum"),
        purchase_amount=("purchase_amount", "sum"),
        purchase_qty=("purchase_qty", "sum"),
        inventory=("inventory", "mean"),
        average_inventory=("average_inventory", "mean"),
        sale_price=("sale_price", "mean"),
        original_price=("original_price", "mean"),
        cost=("cost", "sum"),
        gross_profit=("gross_profit", "sum"),
        gross_margin=("gross_margin", "mean"),
        unit_gross_profit=("unit_gross_profit", "mean"),
        unit_gross_margin=("unit_gross_margin", "mean"),
        discount_rate=("discount_rate", "mean"),
        click=("click", "sum"),
        conversion=("conversion", "sum"),
    ).reset_index()
    grouped = grouped.rename(columns={"group": "object_id"})
    grouped["object_type"] = object_type
    grouped["object_name"] = grouped["object_id"]

    total_sales = float(grouped["sales"].sum()) if not grouped["sales"].dropna().empty else 0.0
    if total_sales > 0:
        grouped["sales_contribution"] = grouped["sales"] / total_sales
        grouped = grouped.sort_values(["sales", "object_id"], ascending=[False, True]).reset_index(drop=True)
        grouped["sales_rank"] = grouped.index + 1
        grouped["sales_contribution_cum"] = grouped["sales_contribution"].cumsum()
        grouped["abc_class"] = grouped["sales_contribution_cum"].apply(
            lambda value: "A" if value <= 0.8 else ("B" if value <= 0.95 else "C")
        )
    else:
        grouped["sales_contribution"] = 0.0
        grouped["sales_rank"] = grouped.index + 1
        grouped["sales_contribution_cum"] = 0.0
        grouped["abc_class"] = "C"

    if roles.get("sales_amount_field") and roles.get("order_count_field"):
        grouped["avg_order_value"] = _ratio(grouped["sales"], grouped["orders"]).reindex(grouped.index)
    else:
        grouped["avg_order_value"] = pd.Series(dtype="float64")
    if roles.get("sales_amount_field") and roles.get("units_sold_field"):
        grouped["avg_selling_price"] = _ratio(grouped["sales"], grouped["units_sold"]).reindex(grouped.index)
    else:
        grouped["avg_selling_price"] = pd.Series(dtype="float64")
    if roles.get("inventory_field") and roles.get("units_sold_field"):
        grouped["sell_through_rate"] = _ratio(grouped["units_sold"], grouped["inventory"]).reindex(grouped.index)
        grouped["inventory_turnover_proxy"] = _ratio(grouped["units_sold"], grouped["average_inventory"]).reindex(grouped.index)
    else:
        grouped["sell_through_rate"] = pd.Series(dtype="float64")
        grouped["inventory_turnover_proxy"] = pd.Series(dtype="float64")
    if roles.get("purchase_qty_field") and roles.get("units_sold_field"):
        grouped["purchase_sell_ratio"] = _ratio(grouped["purchase_qty"], grouped["units_sold"]).reindex(grouped.index)
    else:
        grouped["purchase_sell_ratio"] = pd.Series(dtype="float64")
    if roles.get("purchase_amount_field") and roles.get("sales_amount_field"):
        grouped["purchase_sales_ratio"] = _ratio(grouped["purchase_amount"], grouped["sales"]).reindex(grouped.index)
    else:
        grouped["purchase_sales_ratio"] = pd.Series(dtype="float64")
    if roles.get("click_field") and roles.get("conversion_field"):
        grouped["conversion_rate"] = _ratio(grouped["conversion"], grouped["click"]).reindex(grouped.index)
    else:
        grouped["conversion_rate"] = pd.Series(dtype="float64")
    return grouped


def _price_band_summary(frame: pd.DataFrame, roles: dict[str, str]) -> list[dict[str, Any]]:
    price_col = roles.get("sale_price_field") or roles.get("sales_amount_field")
    if not price_col:
        return []
    price_series = _numeric(frame, price_col)
    if price_series.dropna().nunique() < 2:
        return []
    try:
        labels = ["low_price_band", "mid_low_price_band", "mid_high_price_band", "high_price_band"]
        bands = pd.qcut(price_series.rank(method="first"), q=4, labels=labels)
    except Exception:
        return []
    data = pd.DataFrame(
        {
            "price_band": bands.astype(str),
            "sales": _numeric(frame, roles.get("sales_amount_field")),
            "units_sold": _numeric(frame, roles.get("units_sold_field")),
            "cost": _numeric(frame, roles.get("cost_field")),
            "click": _numeric(frame, roles.get("click_field")),
            "conversion": _numeric(frame, roles.get("conversion_field")),
        }
    )
    grouped = data.groupby("price_band", dropna=False).agg(
        sales_by_price_band=("sales", "sum"),
        units_by_price_band=("units_sold", "sum"),
        cost=("cost", "sum"),
        click=("click", "sum"),
        conversion=("conversion", "sum"),
    ).reset_index()
    rows: list[dict[str, Any]] = []
    for row in grouped.to_dict(orient="records"):
        entry = {
            "price_band": row["price_band"],
            "sales_by_price_band": _format_number(row.get("sales_by_price_band")),
            "units_by_price_band": _format_number(row.get("units_by_price_band")),
            "margin_by_price_band": "",
            "conversion_by_price_band": "",
        }
        sales = float(row.get("sales_by_price_band") or 0)
        cost = float(row.get("cost") or 0)
        if sales > 0 and roles.get("cost_field"):
            entry["margin_by_price_band"] = _format_number((sales - cost) / sales)
        click = float(row.get("click") or 0)
        conversion = float(row.get("conversion") or 0)
        if click > 0 and roles.get("click_field") and roles.get("conversion_field"):
            entry["conversion_by_price_band"] = _format_number(conversion / click)
        rows.append(entry)
    return rows


def _sales_trend(frame: pd.DataFrame, roles: dict[str, str]) -> list[dict[str, Any]]:
    if not roles.get("time_field") or not roles.get("sales_amount_field"):
        return []
    parsed = _parse_time_series(frame, roles["time_field"])
    data = pd.DataFrame({"time": parsed.dt.date, "sales": _numeric(frame, roles["sales_amount_field"])})
    data = data.dropna(subset=["time"])
    if data.empty:
        return []
    grouped = data.groupby("time", dropna=False).agg(total_sales=("sales", "sum")).reset_index()
    return [{"time": str(row["time"]), "total_sales": _format_number(row["total_sales"])} for row in grouped.to_dict(orient="records")]


def _sales_growth_by_object(frame: pd.DataFrame, roles: dict[str, str], group_col: str) -> dict[str, float]:
    if not roles.get("time_field") or not roles.get("sales_amount_field"):
        return {}
    parsed = _parse_time_series(frame, roles["time_field"])
    data = pd.DataFrame(
        {
            "time": parsed.dt.to_period("M").astype(str),
            "group": frame[group_col].astype(str),
            "sales": _numeric(frame, roles["sales_amount_field"]),
        }
    )
    data = data[data["time"] != "NaT"]
    if data.empty:
        return {}
    pivot = data.groupby(["group", "time"], dropna=False).agg(sales=("sales", "sum")).reset_index()
    growth: dict[str, float] = {}
    for object_id, group in pivot.groupby("group"):
        group = group.sort_values("time")
        if len(group) < 2:
            continue
        first = float(group.iloc[0]["sales"] or 0)
        last = float(group.iloc[-1]["sales"] or 0)
        if first > 0:
            growth[str(object_id)] = (last - first) / first
    return growth


def _object_boundary(has_cost: bool, has_inventory: bool) -> str:
    boundaries: list[str] = []
    if not has_cost:
        boundaries.append("no cost -> no profit conclusion")
    if not has_inventory:
        boundaries.append("no inventory -> no stock risk conclusion")
    return "; ".join(boundaries) if boundaries else "supported_by_available_fields"


def _opportunity_and_risk_rows(
    grouped: pd.DataFrame,
    *,
    object_type: str,
    roles: dict[str, str],
    growth_map: dict[str, float],
    report_mode: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if grouped.empty:
        return [], [], []

    sales_q75 = grouped["sales"].quantile(0.75) if grouped["sales"].notna().any() else None
    sales_q25 = grouped["sales"].quantile(0.25) if grouped["sales"].notna().any() else None
    inventory_q75 = grouped["inventory"].quantile(0.75) if grouped["inventory"].notna().any() else None
    inventory_q25 = grouped["inventory"].quantile(0.25) if grouped["inventory"].notna().any() else None
    margin_q75 = grouped["gross_margin"].quantile(0.75) if grouped["gross_margin"].notna().any() else None
    margin_q25 = grouped["gross_margin"].quantile(0.25) if grouped["gross_margin"].notna().any() else None
    discount_q75 = grouped["discount_rate"].quantile(0.75) if grouped["discount_rate"].notna().any() else None
    purchase_q75 = grouped["purchase_qty"].quantile(0.75) if grouped["purchase_qty"].notna().any() else None

    has_cost = bool(roles.get("cost_field") or roles.get("purchase_price_field"))
    has_inventory = bool(roles.get("inventory_field") or roles.get("beginning_inventory_field") or roles.get("ending_inventory_field"))

    object_rows: list[dict[str, Any]] = []
    risk_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []

    for index, row in grouped.head(12).iterrows():
        object_id = _safe_text(row["object_id"])
        object_name = _safe_text(row["object_name"])
        sales_contribution = float(row.get("sales_contribution") or 0)
        spend_mode = report_mode == "procurement_spend_ledger_report"
        label = "spend_structure_review" if spend_mode else "sales_structure_review"
        action = "先做销售贡献分层并复核经营结构"
        benchmark = "top spend review" if spend_mode else "top contribution review"
        evidence_level = "A_DIRECT"
        confidence = "high"

        if sales_q75 is not None and float(row.get("sales") or 0) >= float(sales_q75):
            label = "high_sales_object"
            action = "纳入重点跟踪并复核价格带/供应节奏"
            benchmark = f"sales >= P75 ({_format_number(sales_q75)})"

        growth_value = growth_map.get(object_id)
        if growth_value is not None and growth_value >= 0.2:
            object_rows.append(
                _base_metric_row(
                    metric_id="growth_object",
                    metric_name="高增长对象",
                    object_type=object_type,
                    object_id=object_id,
                    object_name=object_name,
                    metric_value=growth_value,
                    benchmark_or_threshold="growth >= 20%",
                    evidence_level="B_DERIVED",
                    confidence="medium",
                    recommended_action="复核增长驱动并评估是否放大供给承接",
                    action_boundary=_object_boundary(has_cost, has_inventory),
                    formula="last_period_sales / first_period_sales - 1",
                )
            )

        object_rows.append(
            _base_metric_row(
                metric_id="sales_contribution",
                metric_name="销售贡献",
                object_type=object_type,
                object_id=object_id,
                object_name=object_name,
                metric_value=sales_contribution,
                benchmark_or_threshold=benchmark,
                evidence_level=evidence_level,
                confidence=confidence,
                recommended_action=action,
                action_boundary=_object_boundary(has_cost, has_inventory),
                formula="object_sales / total_sales",
            )
        )

        if has_cost and margin_q25 is not None and sales_q75 is not None:
            if float(row.get("sales") or 0) >= float(sales_q75) and float(row.get("gross_margin") or 0) <= float(margin_q25):
                risk_rows.append(
                    {
                        "priority": "P1",
                        "risk_or_opportunity": "high_sales_low_margin",
                        **_base_metric_row(
                            metric_id="high_sales_low_margin",
                            metric_name="高销售低毛利商品",
                            object_type=object_type,
                            object_id=object_id,
                            object_name=object_name,
                            metric_value=row.get("gross_margin"),
                            benchmark_or_threshold=f"gross_margin <= P25 ({_format_number(margin_q25)}) and sales >= P75 ({_format_number(sales_q75)})",
                            evidence_level="B_DERIVED",
                            confidence="high",
                            recommended_action="复核采购价、促销结构和低毛利原因",
                            action_boundary="requires cost support; do not escalate to add-budget without profit validation",
                            formula="(sales - cost) / sales",
                        ),
                    }
                )

        if has_inventory and sales_q25 is not None and inventory_q75 is not None:
            if float(row.get("sales") or 0) <= float(sales_q25) and float(row.get("inventory") or 0) >= float(inventory_q75):
                risk_rows.append(
                    {
                        "priority": "P1",
                        "risk_or_opportunity": "low_sales_high_inventory",
                        **_base_metric_row(
                            metric_id="low_sales_high_inventory",
                            metric_name="低销售高库存商品",
                            object_type=object_type,
                            object_id=object_id,
                            object_name=object_name,
                            metric_value=row.get("inventory"),
                            benchmark_or_threshold=f"inventory >= P75 ({_format_number(inventory_q75)}) and sales <= P25 ({_format_number(sales_q25)})",
                            evidence_level="B_DERIVED",
                            confidence="high",
                            recommended_action="复核滞销原因并评估清理或控采",
                            action_boundary="inventory supported; action still requires sell-through review",
                            formula="inventory and sales quantile comparison",
                        ),
                    }
                )
            if float(row.get("sales") or 0) >= float(sales_q75 or 0) and float(row.get("inventory") or 0) <= float(inventory_q25 or 0):
                risk_rows.append(
                    {
                        "priority": "P1",
                        "risk_or_opportunity": "high_sales_low_inventory",
                        **_base_metric_row(
                            metric_id="high_sales_low_inventory",
                            metric_name="高销售低库存商品",
                            object_type=object_type,
                            object_id=object_id,
                            object_name=object_name,
                            metric_value=row.get("inventory"),
                            benchmark_or_threshold=f"sales >= P75 ({_format_number(sales_q75)}) and inventory <= P25 ({_format_number(inventory_q25)})",
                            evidence_level="B_DERIVED",
                            confidence="medium",
                            recommended_action="核对可售库存与补货优先级",
                            action_boundary="inventory exists; replenish only after checking available_stock and lead time",
                            formula="inventory and sales quantile comparison",
                        ),
                    }
                )

        if has_cost and margin_q75 is not None and sales_q25 is not None:
            if float(row.get("gross_margin") or 0) >= float(margin_q75) and float(row.get("sales") or 0) <= float(sales_q25):
                risk_rows.append(
                    {
                        "priority": "P2",
                        "risk_or_opportunity": "high_margin_low_sales",
                        **_base_metric_row(
                            metric_id="high_margin_low_sales",
                            metric_name="高毛利低销量商品",
                            object_type=object_type,
                            object_id=object_id,
                            object_name=object_name,
                            metric_value=row.get("gross_margin"),
                            benchmark_or_threshold=f"gross_margin >= P75 ({_format_number(margin_q75)}) and sales <= P25 ({_format_number(sales_q25)})",
                            evidence_level="B_DERIVED",
                            confidence="medium",
                            recommended_action="小范围验证流量承接和详情转化",
                            action_boundary="profit supported; avoid direct scale-up without demand validation",
                            formula="gross_margin and sales quantile comparison",
                        ),
                    }
                )

        if purchase_q75 is not None and float(row.get("purchase_qty") or 0) >= float(purchase_q75) and float(row.get("sales") or 0) <= float(sales_q25 or 0):
            risk_rows.append(
                {
                    "priority": "P2",
                    "risk_or_opportunity": "high_purchase_low_sales",
                    **_base_metric_row(
                        metric_id="high_purchase_low_sales",
                        metric_name="高采购低销售对象",
                        object_type=object_type,
                        object_id=object_id,
                        object_name=object_name,
                        metric_value=row.get("purchase_qty"),
                        benchmark_or_threshold=f"purchase_qty >= P75 ({_format_number(purchase_q75)}) and sales <= P25 ({_format_number(sales_q25)})",
                        evidence_level="B_DERIVED",
                        confidence="medium",
                        recommended_action="复核采购节奏与订货依据",
                        action_boundary="use as procurement rhythm review, not as direct blame",
                        formula="purchase_qty and sales quantile comparison",
                    ),
                }
            )

        if discount_q75 is not None and growth_value is not None and growth_value <= 0 and float(row.get("discount_rate") or 0) >= float(discount_q75):
            risk_rows.append(
                {
                    "priority": "P2",
                    "risk_or_opportunity": "high_discount_low_growth",
                    **_base_metric_row(
                        metric_id="high_discount_low_growth",
                        metric_name="高折扣低增长对象",
                        object_type=object_type,
                        object_id=object_id,
                        object_name=object_name,
                        metric_value=row.get("discount_rate"),
                        benchmark_or_threshold=f"discount_rate >= P75 ({_format_number(discount_q75)}) and growth <= 0",
                        evidence_level="B_DERIVED",
                        confidence="medium",
                        recommended_action="复核折扣效率与价格带定位",
                        action_boundary="requires time-supported growth calculation",
                        formula="discount_rate and growth comparison",
                    ),
                }
            )

        if object_type == "sku" and str(row.get("abc_class") or "") == "C" and sales_contribution <= 0.01:
            risk_rows.append(
                {
                    "priority": "P3",
                    "risk_or_opportunity": "long_tail_low_contribution",
                    **_base_metric_row(
                        metric_id="long_tail_low_contribution",
                        metric_name="长尾低贡献SKU",
                        object_type=object_type,
                        object_id=object_id,
                        object_name=object_name,
                        metric_value=sales_contribution,
                        benchmark_or_threshold="ABC=C and contribution <= 1%",
                        evidence_level="A_DIRECT",
                        confidence="high",
                        recommended_action="纳入长尾观察并复核是否保留",
                        action_boundary=_object_boundary(has_cost, has_inventory),
                        formula="sku_sales / total_sales",
                    ),
                }
            )

    for risk in risk_rows:
        action_rows.append(
            {
                "priority": risk["priority"],
                "action": risk["recommended_action"],
                "object_type": risk["object_type"],
                "object_name": risk["object_name"],
                "trigger_metric": risk["metric_name"],
                "evidence_level": risk["evidence_level"],
                "confidence": risk["confidence"],
                "action_boundary": risk["action_boundary"],
            }
        )
    return object_rows, risk_rows, action_rows


def _concentration_risks(grouped: pd.DataFrame, *, object_type: str, metric_name: str) -> list[dict[str, Any]]:
    if grouped.empty or "sales_contribution" not in grouped.columns:
        return []
    top_row = grouped.sort_values("sales_contribution", ascending=False).iloc[0]
    share = float(top_row.get("sales_contribution") or 0)
    if share <= 0.5:
        return []
    return [
        {
            "priority": "P1",
            "risk_or_opportunity": f"{object_type}_concentration_risk",
            **_base_metric_row(
                metric_id=f"{object_type}_concentration_risk",
                metric_name=metric_name,
                object_type=object_type,
                object_id=_safe_text(top_row.get("object_id")),
                object_name=_safe_text(top_row.get("object_name")),
                metric_value=share,
                benchmark_or_threshold="top contribution > 50%",
                evidence_level="A_DIRECT",
                confidence="high",
                recommended_action=f"复核{object_type}集中度并准备分散方案",
                action_boundary="concentration risk only; do not directly淘汰 without downstream validation",
                formula="top_object_sales / total_sales",
            ),
        }
    ]


def _summary_sentence(
    roles: dict[str, str],
    payload: dict[str, Any],
    *,
    report_mode: str = "",
) -> str:
    can_judge = list(payload["narrative"]["can_judge"])
    if report_mode == "procurement_spend_ledger_report":
        lead = "当前已经具备支出金额、时间、商户或供应商对象和用途摘要字段，可以直接输出采购支出结构与治理复盘。"
        if can_judge:
            follow_up = f"当前最先可判断的是 {can_judge[0]}，可以先把这条支出问题压成治理动作。"
        else:
            follow_up = "当前可以先输出支出集中度、商户承担、用途结构和时间异常窗口，然后再决定哪些字段需要补。"
        blocked = "这一模式不能直接判断 SKU 分层、履约、客户承接、GMV/Freight/Review 或电商采销动作。"
        return f"{lead}{follow_up}{blocked}"
    if roles.get("sku_field") and roles.get("sales_amount_field"):
        lead = "当前已经具备 SKU 与销售额字段，可以直接输出对象级销售结构与动作候选。"
    elif roles.get("sales_amount_field"):
        lead = "当前已经具备销售额字段，可以先输出销售规模、结构贡献和头部对象复盘。"
    else:
        lead = "当前缺少稳定销售金额字段，管理层判断只能以字段边界和待补数清单为主。"

    if can_judge:
        follow_up = f"当前最先可判断的是 {can_judge[0]}，可以先把这条经营问题压成动作。"
    else:
        follow_up = "当前仍需先补关键字段，再升级为更强经营结论。"

    blocked = "利润、库存、采购谈判和供应商替换类强判断仍会被边界规则拦住。"
    return f"{lead}{follow_up}{blocked}"

def build_procurement_sales_metric_mining_result(
    *,
    raw_data: pd.DataFrame,
    field_names: list[str] | None = None,
    sample_values: list[str] | None = None,
    data_types: dict[str, str] | None = None,
    universal_metric_mining_result: dict[str, Any] | None = None,
    business_profile_router_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    frame = raw_data.copy()
    roles = _infer_field_roles(frame)
    report_mode = (
        "procurement_spend_ledger_report"
        if _is_procurement_spend_ledger_mode(frame, roles)
        else "procurement_sales_report"
    )
    # FreightCost is a logistics cost component, not a full profit cost field.
    cost_candidate = _normalize(roles.get("cost_field") or "")
    if cost_candidate and "freight" in cost_candidate:
        roles["cost_field"] = ""
    growth_map = _sales_growth_by_object(frame, roles, roles["sku_field"]) if roles.get("sku_field") else {}

    derived_metrics: list[dict[str, Any]] = []
    summary_tables: dict[str, list[dict[str, Any]]] = {}
    object_registry_rows: list[dict[str, Any]] = []
    opportunity_risk_rows: list[dict[str, Any]] = []
    action_table_rows: list[dict[str, Any]] = []
    can_judge: list[str] = []
    cannot_judge: list[str] = []

    if roles.get("sales_amount_field"):
        total_sales = _numeric(frame, roles["sales_amount_field"]).sum()
        derived_metrics.append(
            {
                "metric_id": "total_spend" if report_mode == "procurement_spend_ledger_report" else "total_sales",
                "metric_name": "total_spend" if report_mode == "procurement_spend_ledger_report" else "total_sales",
                "value": _format_number(total_sales),
                "formula": f"sum({roles['sales_amount_field']})",
                "evidence_level": "A_DIRECT",
                "confidence": "high",
            }
        )
        can_judge.append("销售规模")

    if report_mode == "procurement_spend_ledger_report" and can_judge:
        can_judge[-1] = "鏀嚭瑙勬ā"

    transaction_id_field = roles.get("transaction_id_field")
    if transaction_id_field:
        tx_count = int(frame[transaction_id_field].astype(str).replace({"": pd.NA}).dropna().nunique())
        derived_metrics.append(
            {
                "metric_id": "transaction_count",
                "metric_name": "transaction_count",
                "value": _format_number(tx_count),
                "formula": f"nunique({transaction_id_field})",
                "evidence_level": "A_DIRECT",
                "confidence": "high",
            }
        )
        if report_mode == "procurement_spend_ledger_report":
            can_judge.append("浜ゆ槗绗旀暟")

    if roles.get("units_sold_field"):
        total_units = _numeric(frame, roles["units_sold_field"]).sum()
        derived_metrics.append(
            {
                "metric_id": "total_units_sold",
                "metric_name": "total_units_sold",
                "value": _format_number(total_units),
                "formula": f"sum({roles['units_sold_field']})",
                "evidence_level": "A_DIRECT",
                "confidence": "high",
            }
        )
        can_judge.append("销量结构")

    if roles.get("order_count_field"):
        total_orders = _numeric(frame, roles["order_count_field"]).sum()
        derived_metrics.append(
            {
                "metric_id": "order_count",
                "metric_name": "order_count",
                "value": _format_number(total_orders),
                "formula": f"sum({roles['order_count_field']})",
                "evidence_level": "A_DIRECT",
                "confidence": "high",
            }
        )

    if roles.get("sales_amount_field") and roles.get("order_count_field"):
        aov = _series_mean(_ratio(_numeric(frame, roles["sales_amount_field"]), _numeric(frame, roles["order_count_field"])))
        derived_metrics.append(
            {
                "metric_id": "avg_order_value",
                "metric_name": "avg_order_value",
                "value": _format_number(aov),
                "formula": f"{roles['sales_amount_field']} / {roles['order_count_field']}",
                "evidence_level": "B_DERIVED",
                "confidence": "high",
            }
        )

    if roles.get("sales_amount_field") and roles.get("units_sold_field"):
        asp = _series_mean(_ratio(_numeric(frame, roles["sales_amount_field"]), _numeric(frame, roles["units_sold_field"])))
        derived_metrics.append(
            {
                "metric_id": "avg_selling_price",
                "metric_name": "avg_selling_price",
                "value": _format_number(asp),
                "formula": f"{roles['sales_amount_field']} / {roles['units_sold_field']}",
                "evidence_level": "B_DERIVED",
                "confidence": "high",
            }
        )
        can_judge.append("价格带表现")

    if roles.get("sale_price_field") and roles.get("original_price_field"):
        discount_rate = _series_mean(1 - _ratio(_numeric(frame, roles["sale_price_field"]), _numeric(frame, roles["original_price_field"])))
        derived_metrics.append(
            {
                "metric_id": "discount_rate",
                "metric_name": "discount_rate",
                "value": _format_number(discount_rate),
                "formula": f"1 - {roles['sale_price_field']} / {roles['original_price_field']}",
                "evidence_level": "B_DERIVED",
                "confidence": "high",
            }
        )

    if roles.get("sales_amount_field") and roles.get("cost_field"):
        gross_profit = _numeric(frame, roles["sales_amount_field"]).sum() - _numeric(frame, roles["cost_field"]).sum()
        gross_margin = _series_mean(_ratio(_numeric(frame, roles["sales_amount_field"]) - _numeric(frame, roles["cost_field"]), _numeric(frame, roles["sales_amount_field"])))
        derived_metrics.extend(
            [
                {
                    "metric_id": "gross_profit",
                    "metric_name": "gross_profit",
                    "value": _format_number(gross_profit),
                    "formula": f"{roles['sales_amount_field']} - {roles['cost_field']}",
                    "evidence_level": "B_DERIVED",
                    "confidence": "high",
                },
                {
                    "metric_id": "gross_margin",
                    "metric_name": "gross_margin",
                    "value": _format_number(gross_margin),
                    "formula": f"({roles['sales_amount_field']} - {roles['cost_field']}) / {roles['sales_amount_field']}",
                    "evidence_level": "B_DERIVED",
                    "confidence": "high",
                },
            ]
        )
        can_judge.append("毛利与利润结构")
    else:
        cannot_judge.append("毛利、利润、毛利率")

    if roles.get("sale_price_field") and roles.get("purchase_price_field"):
        unit_gp = _series_mean(_numeric(frame, roles["sale_price_field"]) - _numeric(frame, roles["purchase_price_field"]))
        unit_gm = _series_mean(_ratio(_numeric(frame, roles["sale_price_field"]) - _numeric(frame, roles["purchase_price_field"]), _numeric(frame, roles["sale_price_field"])))
        derived_metrics.extend(
            [
                {
                    "metric_id": "unit_gross_profit",
                    "metric_name": "unit_gross_profit",
                    "value": _format_number(unit_gp),
                    "formula": f"{roles['sale_price_field']} - {roles['purchase_price_field']}",
                    "evidence_level": "B_DERIVED",
                    "confidence": "high",
                },
                {
                    "metric_id": "unit_gross_margin",
                    "metric_name": "unit_gross_margin",
                    "value": _format_number(unit_gm),
                    "formula": f"({roles['sale_price_field']} - {roles['purchase_price_field']}) / {roles['sale_price_field']}",
                    "evidence_level": "B_DERIVED",
                    "confidence": "medium",
                },
            ]
        )

    inventory_supported = bool(roles.get("inventory_field") or roles.get("beginning_inventory_field") or roles.get("ending_inventory_field"))
    if inventory_supported and roles.get("units_sold_field"):
        inventory_series = _numeric(frame, roles.get("inventory_field")) if roles.get("inventory_field") else (_numeric(frame, roles.get("beginning_inventory_field")) + _numeric(frame, roles.get("ending_inventory_field"))) / 2
        sell_through = _series_mean(_ratio(_numeric(frame, roles["units_sold_field"]), inventory_series))
        turnover_proxy = _series_mean(_ratio(_numeric(frame, roles["units_sold_field"]), inventory_series))
        derived_metrics.extend(
            [
                {
                    "metric_id": "sell_through_rate",
                    "metric_name": "sell_through_rate",
                    "value": _format_number(sell_through),
                    "formula": f"{roles['units_sold_field']} / inventory",
                    "evidence_level": "B_DERIVED",
                    "confidence": "medium",
                },
                {
                    "metric_id": "inventory_turnover_proxy",
                    "metric_name": "inventory_turnover_proxy",
                    "value": _format_number(turnover_proxy),
                    "formula": f"{roles['units_sold_field']} / average_inventory",
                    "evidence_level": "C_PROXY",
                    "confidence": "medium",
                },
            ]
        )
        can_judge.append("库存与动销关系")
    else:
        cannot_judge.append("库存周转、滞销库存、缺货风险")

    if roles.get("purchase_qty_field") and roles.get("units_sold_field"):
        purchase_sell_ratio = _series_mean(_ratio(_numeric(frame, roles["purchase_qty_field"]), _numeric(frame, roles["units_sold_field"])))
        derived_metrics.append(
            {
                "metric_id": "purchase_sell_ratio",
                "metric_name": "purchase_sell_ratio",
                "value": _format_number(purchase_sell_ratio),
                "formula": f"{roles['purchase_qty_field']} / {roles['units_sold_field']}",
                "evidence_level": "B_DERIVED",
                "confidence": "medium",
            }
        )

    if roles.get("purchase_amount_field") and roles.get("sales_amount_field"):
        purchase_sales_ratio = _series_mean(_ratio(_numeric(frame, roles["purchase_amount_field"]), _numeric(frame, roles["sales_amount_field"])))
        derived_metrics.append(
            {
                "metric_id": "purchase_sales_ratio",
                "metric_name": "purchase_sales_ratio",
                "value": _format_number(purchase_sales_ratio),
                "formula": f"{roles['purchase_amount_field']} / {roles['sales_amount_field']}",
                "evidence_level": "B_DERIVED",
                "confidence": "medium",
            }
        )

    sku_grouped = _aggregate_by_dimension(frame, group_col=roles["sku_field"], object_type="sku", roles=roles) if roles.get("sku_field") else pd.DataFrame()
    category_grouped = _aggregate_by_dimension(frame, group_col=roles["category_field"], object_type="category", roles=roles) if roles.get("category_field") else pd.DataFrame()
    supplier_grouped = _aggregate_by_dimension(frame, group_col=roles["supplier_field"], object_type="supplier", roles=roles) if roles.get("supplier_field") else pd.DataFrame()

    if not sku_grouped.empty and roles.get("sales_amount_field"):
        summary_tables["sku_ranking"] = [
            {
                "sku": row["object_id"],
                "sales": _format_number(row["sales"]),
                "sales_contribution": _format_number(row["sales_contribution"]),
                "sales_rank": int(row["sales_rank"]),
                "abc_class": row["abc_class"],
            }
            for row in sku_grouped.head(20).to_dict(orient="records")
        ]
        can_judge.append("SKU 销售排名")

    if not category_grouped.empty and roles.get("sales_amount_field"):
        summary_tables["category_contribution"] = [
            {
                "category": row["object_id"],
                "sales": _format_number(row["sales"]),
                "sales_contribution": _format_number(row["sales_contribution"]),
            }
            for row in category_grouped.head(20).to_dict(orient="records")
        ]
        can_judge.append("品类贡献")

    if not supplier_grouped.empty and roles.get("sales_amount_field"):
        summary_tables["supplier_contribution"] = [
            {
                "supplier": row["object_id"],
                "sales": _format_number(row["sales"]),
                "sales_contribution": _format_number(row["sales_contribution"]),
            }
            for row in supplier_grouped.head(20).to_dict(orient="records")
        ]
        can_judge.append("供应商贡献")

    price_bands = _price_band_summary(frame, roles)
    if price_bands:
        summary_tables["price_band_summary"] = price_bands

    trend_rows = _sales_trend(frame, roles)
    if trend_rows:
        summary_tables["sales_trend"] = trend_rows
        can_judge.append("销售趋势")
    else:
        cannot_judge.append("趋势与增长")

    sku_objects, sku_risks, sku_actions = _opportunity_and_risk_rows(
        sku_grouped,
        object_type="sku",
        roles=roles,
        growth_map=growth_map,
        report_mode=report_mode,
    )
    object_registry_rows.extend(sku_objects)
    opportunity_risk_rows.extend(sku_risks)
    action_table_rows.extend(sku_actions)
    opportunity_risk_rows.extend(_concentration_risks(sku_grouped, object_type="sku", metric_name="头部过度集中风险"))
    opportunity_risk_rows.extend(_concentration_risks(supplier_grouped, object_type="supplier", metric_name="供应商贡献过度集中风险"))
    opportunity_risk_rows.extend(_concentration_risks(category_grouped, object_type="category", metric_name="品类结构失衡风险"))

    for grouped, object_type in [(category_grouped, "category"), (supplier_grouped, "supplier")]:
        objects, risks, actions = _opportunity_and_risk_rows(
            grouped,
            object_type=object_type,
            roles=roles,
            growth_map={},
            report_mode=report_mode,
        )
        object_registry_rows.extend(objects[:8])
        opportunity_risk_rows.extend(risks[:8])
        action_table_rows.extend(actions[:8])

    seen_action_keys: set[tuple[str, str]] = set()
    deduped_actions: list[dict[str, Any]] = []
    for action in action_table_rows:
        key = (_safe_text(action.get("object_name")), _safe_text(action.get("action")))
        if key in seen_action_keys:
            continue
        seen_action_keys.add(key)
        deduped_actions.append(action)
    if not deduped_actions and summary_tables.get("sku_ranking"):
        deduped_actions.extend(
            [
                {
                    "priority": "P2",
                    "action": "先做 SKU ABC 分层并复核头部与长尾结构",
                    "object_type": "sku",
                    "object_name": summary_tables["sku_ranking"][0]["sku"],
                    "trigger_metric": "sales_contribution",
                    "evidence_level": "A_DIRECT",
                    "confidence": "high",
                    "action_boundary": _object_boundary(
                        bool(roles.get("cost_field") or roles.get("purchase_price_field")),
                        inventory_supported,
                    ),
                }
            ]
        )

    if not roles.get("cost_field") and not roles.get("purchase_price_field"):
        action_boundary = "missing cost -> no profit judgement"
    elif not inventory_supported:
        action_boundary = "missing inventory -> no stock risk judgement"
    else:
        action_boundary = "supported_by_available_fields"
    if not deduped_actions:
        deduped_actions.append(
            {
                "priority": "P3",
                "action": "补充关键字段后复核",
                "object_type": "dataset",
                "object_name": "all_objects",
                "trigger_metric": "data_gap",
                "evidence_level": "D_HYPOTHESIS",
                "confidence": "low",
                "action_boundary": action_boundary,
            }
        )

    if report_mode == "procurement_spend_ledger_report":
        spend_can_judge: list[str] = []
        if roles.get("sales_amount_field"):
            spend_can_judge.append("支出规模")
        if transaction_id_field:
            spend_can_judge.append("交易笔数")
        if summary_tables.get("supplier_contribution"):
            spend_can_judge.append("商户/供应商集中度")
        if summary_tables.get("category_contribution"):
            spend_can_judge.append("用途/分类支出结构")
        if summary_tables.get("sales_trend"):
            spend_can_judge.append("支出时间脉冲")
        if roles.get("supplier_field") and roles.get("sales_amount_field"):
            supplier_amounts = frame[[roles["supplier_field"], roles["sales_amount_field"]]].copy()
            supplier_amounts.columns = ["supplier", "amount"]
            supplier_amounts["amount"] = pd.to_numeric(supplier_amounts["amount"], errors="coerce")
            supplier_amounts = supplier_amounts.dropna(subset=["supplier", "amount"])
            if not supplier_amounts.empty:
                merchant_repeat_rows = (
                    supplier_amounts.groupby("supplier", dropna=False)
                    .agg(transaction_count=("supplier", "size"), total_amount=("amount", "sum"))
                    .reset_index()
                    .sort_values(["transaction_count", "total_amount"], ascending=[False, False])
                )
                summary_tables["merchant_repeat_rows"] = [
                    {
                        "supplier": _safe_text(row["supplier"]),
                        "transaction_count": _format_number(row["transaction_count"]),
                        "total_amount": _format_number(row["total_amount"]),
                    }
                    for row in merchant_repeat_rows.head(20).to_dict(orient="records")
                ]
                spend_can_judge.append("重复商户支出")
        if roles.get("sales_amount_field"):
            amount_series = _numeric(frame, roles["sales_amount_field"]).dropna()
            if not amount_series.empty:
                p90 = float(amount_series.quantile(0.90))
                top_rows = frame.loc[_numeric(frame, roles["sales_amount_field"]) >= p90].head(20)
                large_transaction_rows: list[dict[str, Any]] = []
                for _, source_row in top_rows.iterrows():
                    large_transaction_rows.append(
                        {
                            "time": _safe_text(source_row.get(roles.get("time_field") or "")),
                            "supplier": _safe_text(source_row.get(roles.get("supplier_field") or "")),
                            "purpose": _safe_text(source_row.get(roles.get("category_field") or "")),
                            "amount": _format_number(source_row.get(roles["sales_amount_field"])),
                            "transaction_id": _safe_text(source_row.get(transaction_id_field or "")),
                        }
                    )
                if large_transaction_rows:
                    summary_tables["large_transaction_rows"] = large_transaction_rows
                    spend_can_judge.append("异常大额支出窗口")
        can_judge = list(dict.fromkeys(spend_can_judge))
        cannot_judge = list(
            dict.fromkeys(
                [
                    "SKU 分层",
                    "客户承接",
                    "履约判断",
                    "GMV/Freight/Review",
                    *cannot_judge,
                ]
            )
        )
        if len(deduped_actions) == 1 and str(deduped_actions[0].get("object_name") or "") == "all_objects":
            deduped_actions = []
        if summary_tables.get("supplier_contribution"):
            top_supplier = summary_tables["supplier_contribution"][0]
            deduped_actions.append(
                {
                    "priority": "P1",
                    "action": "复核头部商户/供应商的支出集中度，明确是否需要分散或追加授权",
                    "object_type": "supplier",
                    "object_name": top_supplier.get("supplier", ""),
                    "trigger_metric": "supplier_contribution",
                    "evidence_level": "A_DIRECT",
                    "confidence": "high",
                    "action_boundary": "spend-ledger only; no SKU/fulfillment/customer conclusion",
                }
            )
        if summary_tables.get("category_contribution"):
            top_purpose = summary_tables["category_contribution"][0]
            deduped_actions.append(
                {
                    "priority": "P1",
                    "action": "把头部用途/分类支出单独拆开，复核它是长期因素还是当期异常入账窗口",
                    "object_type": "category",
                    "object_name": top_purpose.get("category", ""),
                    "trigger_metric": "category_contribution",
                    "evidence_level": "A_DIRECT",
                    "confidence": "high",
                    "action_boundary": "spend-ledger only; no SKU/fulfillment/customer conclusion",
                }
            )
        if summary_tables.get("large_transaction_rows"):
            first_large_tx = summary_tables["large_transaction_rows"][0]
            deduped_actions.append(
                {
                    "priority": "P2",
                    "action": "取出大额支出窗口和样本清单，审核是否属于一次性合法高额或需要详细复核的异常交易",
                    "object_type": "transaction_window",
                    "object_name": str(first_large_tx.get("time") or ""),
                    "trigger_metric": "large_transaction_rows",
                    "evidence_level": "A_DIRECT",
                    "confidence": "high",
                    "action_boundary": "spend-ledger only; no SKU/fulfillment/customer conclusion",
                }
            )
        if not deduped_actions:
            deduped_actions.append(
                {
                    "priority": "P2",
                    "action": "先做商户/用途 ABC 分层，并复核头部支出集中度",
                    "object_type": "supplier" if roles.get("supplier_field") else "dataset",
                    "object_name": "top_suppliers_or_purposes",
                    "trigger_metric": "spend_contribution",
                    "evidence_level": "A_DIRECT",
                    "confidence": "high",
                    "action_boundary": "spend-ledger only; no SKU/fulfillment/customer conclusion",
                }
            )

    action_table_rows = deduped_actions
    summary_sentence = _summary_sentence(
        roles,
        {
            "narrative": {
                "can_judge": list(dict.fromkeys(can_judge)),
                "cannot_judge": list(dict.fromkeys(cannot_judge)),
            }
        },
        report_mode=report_mode,
    )

    quality_checks = {
        "has_sku_sales_ranking": bool(roles.get("sku_field") and roles.get("sales_amount_field") and summary_tables.get("sku_ranking")),
        "has_category_contribution": bool(roles.get("category_field") and roles.get("sales_amount_field") and summary_tables.get("category_contribution")),
        "has_supplier_contribution": bool(roles.get("supplier_field") and roles.get("sales_amount_field") and summary_tables.get("supplier_contribution")),
        "has_gross_profit_and_margin": bool(
            roles.get("sales_amount_field")
            and roles.get("cost_field")
            and {"gross_profit", "gross_margin"}.issubset({row["metric_id"] for row in derived_metrics})
        ),
        "has_inventory_turnover_proxy": bool(
            inventory_supported
            and roles.get("units_sold_field")
            and {"sell_through_rate", "inventory_turnover_proxy"}.intersection({row["metric_id"] for row in derived_metrics})
        ),
        "all_actions_are_supplement": bool(action_table_rows) and all(
            _safe_text(row.get("action")).startswith(WAIT_ACTION_PREFIXES) for row in action_table_rows
        ),
        "all_actions_are_p1": len(action_table_rows) >= 4 and all(_safe_text(row.get("priority")) == "P1" for row in action_table_rows),
    }

    return {
        "business_profile": "procurement_sales_report",
        "report_mode": report_mode,
        "field_roles": roles,
        "input_summary": {
            "field_names": field_names or frame.columns.astype(str).tolist(),
            "sample_values": sample_values or [],
            "data_types": data_types or {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
            "business_profile_router_result": business_profile_router_result or {},
            "universal_metric_mining_result": universal_metric_mining_result or {},
        },
        "narrative": {
            "can_judge": list(dict.fromkeys(can_judge)),
            "cannot_judge": list(dict.fromkeys(cannot_judge)),
            "summary_sentence": summary_sentence,
        },
        "derived_metrics": derived_metrics,
        "summary_tables": summary_tables,
        "object_registry_rows": object_registry_rows,
        "opportunity_risk_rows": opportunity_risk_rows,
        "action_table_rows": action_table_rows,
        "quality_checks": quality_checks,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def write_procurement_sales_metric_mining_outputs(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result_path = out_dir / "procurement_sales_metric_mining_result.json"
    derived_path = out_dir / "procurement_sales_derived_metrics.csv"
    registry_path = out_dir / "procurement_sales_object_registry.csv"
    opportunity_path = out_dir / "procurement_sales_opportunity_risk_table.csv"
    action_path = out_dir / "procurement_sales_action_table.csv"

    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(derived_path, payload.get("derived_metrics") or [])
    _write_csv(registry_path, payload.get("object_registry_rows") or [])
    _write_csv(opportunity_path, payload.get("opportunity_risk_rows") or [])
    _write_csv(action_path, payload.get("action_table_rows") or [])

    return {
        "procurement_sales_metric_mining_result.json": str(result_path.resolve()),
        "procurement_sales_derived_metrics.csv": str(derived_path.resolve()),
        "procurement_sales_object_registry.csv": str(registry_path.resolve()),
        "procurement_sales_opportunity_risk_table.csv": str(opportunity_path.resolve()),
        "procurement_sales_action_table.csv": str(action_path.resolve()),
    }


def _contains_positive_assertion(text: str, term: str) -> bool:
    haystack = _safe_text(text)
    start = 0
    while True:
        idx = haystack.find(term, start)
        if idx < 0:
            return False
        left = haystack[max(0, idx - 8) : idx]
        if not any(neg in left for neg in NEGATION_TERMS):
            return True
        start = idx + len(term)


def _has_boundary_context(text: str) -> bool:
    haystack = _safe_text(text)
    return any(token in haystack for token in ("当前不可判断", "不能判断", "缺少采购成本", "缺少库存", "待补数边界", "不升级为强结论"))


def procurement_sales_metric_mining_failures(
    *,
    metric_payload: dict[str, Any] | None,
    management_markdown: str,
) -> list[str]:
    if not metric_payload:
        return []

    roles = metric_payload.get("field_roles") or {}
    checks = metric_payload.get("quality_checks") or {}
    text = _safe_text(management_markdown).lower()
    failures: list[str] = []
    action_rows = list(metric_payload.get("action_table_rows") or [])
    inventory_action_asserted = any(
        any(term in _safe_text(row.get("action")) for term in INVENTORY_RISK_TERMS)
        for row in action_rows
    )

    if roles.get("sku_field") and roles.get("sales_amount_field") and not checks.get("has_sku_sales_ranking"):
        failures.append("sku+sales exists but sku ranking missing")
    if roles.get("category_field") and roles.get("sales_amount_field") and not checks.get("has_category_contribution"):
        failures.append("category+sales exists but category contribution missing")
    if roles.get("supplier_field") and roles.get("sales_amount_field") and not checks.get("has_supplier_contribution"):
        failures.append("supplier+sales exists but supplier contribution missing")
    if roles.get("sales_amount_field") and roles.get("cost_field") and not checks.get("has_gross_profit_and_margin"):
        failures.append("sales+cost exists but gross profit or gross margin missing")
    if (roles.get("inventory_field") or roles.get("beginning_inventory_field") or roles.get("ending_inventory_field")) and roles.get("units_sold_field") and not checks.get("has_inventory_turnover_proxy"):
        failures.append("inventory+units_sold exists but turnover proxy missing")

    if not roles.get("cost_field") and not roles.get("purchase_price_field"):
        if any(_contains_positive_assertion(management_markdown, term) for term in PROFIT_TERMS) and not _has_boundary_context(management_markdown):
            failures.append("profit judgement appears without cost fields")
    if not roles.get("inventory_field") and not roles.get("beginning_inventory_field") and not roles.get("ending_inventory_field"):
        if (inventory_action_asserted or any(_contains_positive_assertion(management_markdown, term) for term in INVENTORY_RISK_TERMS)) and not _has_boundary_context(management_markdown):
            failures.append("inventory judgement appears without inventory fields")

    if checks.get("all_actions_are_supplement"):
        failures.append("all procurement actions are supplement-field actions")
    if checks.get("all_actions_are_p1"):
        failures.append("all procurement actions are P1")

    return failures


# Clean overrides for user-facing Chinese boundary checks. The legacy constants
# above include mojibake tokens, which can turn explicit "cannot judge" boundary
# text into false positive profit / inventory failures.
PROFIT_TERMS = ("毛利", "利润", "毛利率", "roi", "ROI", "CAC")
INVENTORY_RISK_TERMS = ("缺货", "滞销库存", "库存周转", "压货", "清仓", "补货")
NEGATION_TERMS = (
    "不",
    "无",
    "缺",
    "待补",
    "不能",
    "不可",
    "无法",
    "禁止",
    "需补",
    "缺少",
    "未提供",
    "proxy",
    "代理",
    "no cost",
    "no inventory",
    "without cost",
    "without inventory",
)


def _legacy_0__contains_positive_assertion(text: str, term: str) -> bool:
    haystack = _safe_text(text)
    needle = _safe_text(term)
    if not needle:
        return False
    start = 0
    negative_right_phrases = (
        "不能判断",
        "不可判断",
        "待补后验证",
        "待补数边界",
        "不升级为强结论",
        "不能当成完整成本结构",
    )
    while True:
        idx = haystack.find(needle, start)
        if idx < 0:
            return False
        left = haystack[max(0, idx - 24) : idx]
        right = haystack[idx : idx + 24]
        if not any(neg in left for neg in NEGATION_TERMS) and not any(phrase in right for phrase in negative_right_phrases):
            return True
        start = idx + len(needle)


def _legacy_0__has_boundary_context(text: str) -> bool:
    haystack = _safe_text(text)
    return any(
        token in haystack
        for token in (
            "当前不可判断",
            "不能判断",
            "不能当成完整成本结构",
            "缺少采购成本",
            "缺少库存",
            "待补数边界",
            "不升级为强结论",
            "no cost -> no profit conclusion",
            "no inventory -> no stock risk conclusion",
        )
    )
FIELD_ROLE_ALIASES["category_field"].extend(
    [
        "description",
        "purpose_of_spend",
        "purposeofspend",
        "procurement_classification",
        "procurementclassification",
        "service_category_label",
        "servicecategorylabel",
    ]
)
FIELD_ROLE_ALIASES["supplier_field"].extend(
    [
        "supplier_name",
        "suppliername",
        "vendor_name",
        "vendorname",
        "merchant",
        "merchant_name",
        "merchantname",
        "seller_name",
        "sellername",
    ]
)
FIELD_ROLE_ALIASES["time_field"].extend(
    [
        "payment_date",
        "paymentdate",
        "posting_date",
        "postingdate",
        "trans_post_date",
        "transpostdate",
    ]
)
FIELD_ROLE_ALIASES["sales_amount_field"].extend(
    [
        "net_amount",
        "netamount",
        "transaction_amount",
        "transactionamount",
        "trans_line_amt",
        "translineamt",
    ]
)
FIELD_ROLE_ALIASES["transaction_id_field"] = [
    "transaction_number",
    "transactionnumber",
    "transaction_id",
    "transactionid",
    "card_transaction",
    "cardtransaction",
]
