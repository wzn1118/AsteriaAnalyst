from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype


OBJECT_HINTS = [
    "sku",
    "item",
    "product",
    "goods",
    "category",
    "brand",
    "seller",
    "shop",
    "store",
    "vendor",
    "supplier",
    "customer",
    "user",
    "city",
    "state",
]
AMOUNT_HINTS = ["revenue", "gmv", "amount", "price", "sales", "spend", "budget", "cost", "freight"]
COST_HINTS = ["cost", "freight", "shipping", "cogs", "procurement", "purchase"]
INVENTORY_HINTS = ["inventory", "stock", "turnover", "days_of_inventory", "sell_through"]
TIME_HINTS = ["date", "time", "timestamp", "created", "updated", "purchase", "delivered", "delivery", "estimated"]
FULFILLMENT_HINTS = ["deliver", "delivery", "delay", "late", "refund", "return", "status", "ship", "freight"]
REVIEW_HINTS = ["review", "rating", "score", "comment", "feedback"]
TEXT_HINTS = ["text", "comment", "note", "content", "title", "description", "review"]
ORDER_KEY_HINTS = ["orderid", "order_id", "order"]
CUSTOMER_KEY_HINTS = ["customerid", "customer_id", "customer", "user"]
SELLER_KEY_HINTS = ["seller", "shop", "store", "merchant", "vendor", "supplier"]
PRODUCT_DIMENSION_HINTS = ["weight", "length", "height", "width", "dimension", "size"]


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _sample_values(series: pd.Series, limit: int = 4) -> list[str]:
    samples: list[str] = []
    for item in series.dropna().head(limit).tolist():
        text = _safe_text(item)
        if text:
            samples.append(text[:120])
    return samples


def _metric_families(metric_ids: list[str]) -> list[str]:
    families: set[str] = set()
    for metric_id in metric_ids:
        key = _normalize(metric_id)
        if any(token in key for token in ["sales", "gmv", "revenue", "order", "unit", "quantity"]):
            families.add("sales_scale")
        if any(token in key for token in ["price", "aov", "discount"]):
            families.add("pricing")
        if any(token in key for token in ["inventory", "stock", "sellthrough", "turnover", "daysofinventory"]):
            families.add("inventory")
        if any(token in key for token in ["grossmargin", "grossprofit", "profit", "margin", "roi"]):
            families.add("profitability")
        if any(token in key for token in ["purchase", "procurement", "supplier"]):
            families.add("procurement_supply")
        if any(token in key for token in ["click", "ctr", "conversion", "pay", "cart", "impression"]):
            families.add("traffic_conversion")
        if any(token in key for token in ["review", "rating", "refund", "aftersales"]):
            families.add("reputation_aftersales")
        if any(token in key for token in ["retention", "active", "activation", "dau", "mau", "wau"]):
            families.add("user_retention")
    return sorted(families)


def _field_profile(series: pd.Series) -> dict[str, Any]:
    non_null_count = int(series.notna().sum())
    total_count = int(len(series))
    unique_count = int(series.dropna().nunique())
    unique_ratio = round(unique_count / max(non_null_count, 1), 4)
    sample_values = _sample_values(series)
    return {
        "dtype": str(series.dtype),
        "non_null_ratio": round(non_null_count / max(total_count, 1), 4),
        "non_null_count": non_null_count,
        "unique_count": unique_count,
        "unique_ratio": unique_ratio,
        "sample_values": sample_values,
    }


def _contains_hint(name: str, hints: list[str]) -> bool:
    normalized = _normalize(name)
    return any(_normalize(item) in normalized for item in hints)


def _status_like(samples: list[str]) -> bool:
    if not samples:
        return False
    statuses = {"delivered", "shipped", "canceled", "processing", "approved", "invoiced"}
    normalized = {_normalize(item) for item in samples}
    return any(item in normalized for item in statuses)


def _score_like(samples: list[str]) -> bool:
    if not samples:
        return False
    try:
        numeric = [float(item) for item in samples]
    except Exception:
        return False
    return all(0 <= item <= 5 for item in numeric)


def _field_role_model(field_name: str, series: pd.Series) -> dict[str, Any]:
    profile = _field_profile(series)
    samples = profile["sample_values"]
    normalized_name = _normalize(field_name)
    roles: list[str] = []
    evidence: list[str] = []
    candidate_roles: list[str] = []
    ambiguous_reason = ""

    if is_datetime64_any_dtype(series):
        roles.append("time")
        evidence.append(f"数据类型是 `{profile['dtype']}`，且样例值为时间戳：{', '.join(samples[:2])}")
        if _contains_hint(field_name, FULFILLMENT_HINTS):
            roles.append("fulfillment")
            evidence.append("字段名包含 delivery / delivered / estimated 等履约信号，属于履约时点。")

    if is_numeric_dtype(series):
        if _contains_hint(field_name, AMOUNT_HINTS):
            roles.append("amount")
            evidence.append(f"字段名含金额信号，且样例值是连续数值：{', '.join(samples[:3])}")
        if _contains_hint(field_name, COST_HINTS):
            roles.append("cost")
            evidence.append("字段名含 freight / cost / shipping 等成本信号，指向成本片段。")
        if _contains_hint(field_name, FULFILLMENT_HINTS):
            roles.append("fulfillment")
            evidence.append("字段名含 delay / late / delivery 等履约信号，且数值表现为时长或布尔状态。")
        if _contains_hint(field_name, REVIEW_HINTS) or (_score_like(samples) and "score" in normalized_name):
            roles.append("review")
            evidence.append(f"字段名或样例值表现为评分体系，唯一值结构={profile['unique_count']}。")
        if _contains_hint(field_name, INVENTORY_HINTS):
            roles.append("inventory")
            evidence.append("字段名含 inventory / stock / turnover 等库存信号。")
        if _contains_hint(field_name, PRODUCT_DIMENSION_HINTS):
            candidate_roles.extend(["product_attribute_numeric", "logistics_attribute"])
            ambiguous_reason = "这是商品物理属性，不等于金额、成本、库存或对象维度。"
            evidence.append("字段名是重量/长宽高等物理属性，适合保留为模糊字段。")

    if not is_numeric_dtype(series) and not is_datetime64_any_dtype(series):
        if _contains_hint(field_name, TEXT_HINTS):
            roles.append("text")
            evidence.append(f"字段名含 text/comment/review 等文本信号，样例值为：{', '.join(samples[:2])}")
        if _contains_hint(field_name, REVIEW_HINTS):
            roles.append("review")
            evidence.append("字段名含 review / rating / score 等评价信号。")
        if _status_like(samples) or _contains_hint(field_name, FULFILLMENT_HINTS):
            roles.append("fulfillment")
            evidence.append(f"样例值包含订单/履约状态，如：{', '.join(samples[:3])}")
        if _contains_hint(field_name, OBJECT_HINTS) or profile["unique_ratio"] > 0.05:
            roles.append("object")
            evidence.append(
                f"字段具备对象维度特征：唯一值 {profile['unique_count']}，唯一率 {profile['unique_ratio']}，样例值 {', '.join(samples[:2])}"
            )
        if _contains_hint(field_name, ORDER_KEY_HINTS):
            candidate_roles.append("observation_key")
            ambiguous_reason = "OrderID 既是分析对象键，也是观察单位主键。"
            evidence.append("字段名含 order_id，说明它更像观察单位主键，而不是商品对象。")
        if _contains_hint(field_name, CUSTOMER_KEY_HINTS):
            candidate_roles.append("customer_dimension")
            ambiguous_reason = ambiguous_reason or "CustomerID 更像客户维度，不应被简单并入商品对象。"
            evidence.append("字段名含 customer_id，说明它是客户维度。")
        if _contains_hint(field_name, SELLER_KEY_HINTS):
            candidate_roles.append("seller_dimension")
            evidence.append("字段名含 seller/shop/vendor，说明它是卖家或店铺维度。")

    if field_name == "Quantity" and profile["unique_count"] == 1:
        candidate_roles.append("line_item_quantity")
        ambiguous_reason = "Quantity 在当前样本中恒等于 1，更像明细行数量占位，而不是有区分度的经营指标。"
        evidence.append("当前真实样本中 Quantity 唯一值为 1，区分度不足。")

    roles = list(dict.fromkeys(roles))
    candidate_roles = list(dict.fromkeys(candidate_roles))
    if not roles and not candidate_roles:
        candidate_roles = ["unclassified"]
        ambiguous_reason = "当前没有足够证据把该字段稳定归到目标角色。"
        evidence.append("字段没有明确的名称信号，样例值也不足以稳定归类。")

    return {
        "assigned_roles": roles,
        "evidence": evidence,
        "candidate_roles": candidate_roles,
        "ambiguous_reason": ambiguous_reason,
        **profile,
    }


def _object_grain(field_roles: dict[str, dict[str, Any]]) -> str:
    has_order = any(_contains_hint(name, ORDER_KEY_HINTS) for name in field_roles)
    has_product = any(_contains_hint(name, ["sku", "item", "product", "goods"]) for name in field_roles)
    has_customer = any(_contains_hint(name, CUSTOMER_KEY_HINTS) for name in field_roles)
    has_seller = any(_contains_hint(name, SELLER_KEY_HINTS) for name in field_roles)
    if has_order and has_product and (has_customer or has_seller):
        return "mixed_order_item"
    if has_product:
        return "sku_or_product"
    if any(_contains_hint(name, ["category"]) for name in field_roles):
        return "category"
    if has_seller:
        return "supplier_or_merchant"
    return "generic_business_object"


def _fields_with_role(field_roles: dict[str, dict[str, Any]], role: str) -> list[str]:
    return [name for name, detail in field_roles.items() if role in detail.get("assigned_roles", [])]


def _candidate_business_objects(object_grain: str, field_roles: dict[str, dict[str, Any]]) -> list[str]:
    mapping = {
        "mixed_order_item": ["订单", "商品", "SKU", "卖家", "客户"],
        "sku_or_product": ["SKU", "商品", "SPU", "类目"],
        "category": ["类目", "品类", "商品组"],
        "supplier_or_merchant": ["卖家", "店铺", "商家", "商品"],
        "generic_business_object": ["业务对象", "记录单元", "主题维度"],
    }
    candidates = list(mapping.get(object_grain, ["业务对象"]))
    if _fields_with_role(field_roles, "review"):
        candidates.append("评价/售后对象")
    return list(dict.fromkeys(candidates))[:6]


def _candidate_observation_units(object_grain: str, field_roles: dict[str, dict[str, Any]]) -> list[str]:
    units: list[str] = []
    if any(_contains_hint(name, ORDER_KEY_HINTS) for name in field_roles):
        units.append("订单主键记录")
    if object_grain in {"mixed_order_item", "sku_or_product"}:
        units.append("订单商品明细")
    if any(_contains_hint(name, CUSTOMER_KEY_HINTS) for name in field_roles):
        units.append("客户维度切片")
    if any(_contains_hint(name, SELLER_KEY_HINTS) for name in field_roles):
        units.append("卖家/店铺维度切片")
    if _fields_with_role(field_roles, "fulfillment"):
        units.append("履约状态观察窗口")
    return list(dict.fromkeys(units))[:6] or ["通用业务记录"]


def _infer_context(
    *,
    business_profile: str,
    object_grain: str,
    field_roles: dict[str, dict[str, Any]],
    available_metric_families: list[str],
    router_result: dict[str, Any] | None,
) -> str:
    router_profile = _safe_text((router_result or {}).get("business_profile"))
    if object_grain == "mixed_order_item":
        if router_profile:
            return f"当前上传数据更像平台零售订单、商品、卖家、客户、履约与评价混合观察窗口，且 router_result 将主链识别为 `{router_profile}`。"
        return "当前上传数据更像平台零售订单、商品、卖家、客户、履约与评价混合观察窗口，而不是纯 SKU 或纯采销汇总表。"
    if business_profile == "procurement_sales_report":
        return "当前上传数据更像零售采销、商品经营或供应链复盘场景。"
    if business_profile == "ecommerce_product_operations_report":
        return "当前上传数据更像平台电商商品经营与交易转化场景。"
    if "reputation_aftersales" in available_metric_families and "sales_scale" in available_metric_families:
        return "当前上传数据更像交易、履约、评价复合场景。"
    return "当前上传数据只能支持形成通用业务背景与研究范围推断。"


def _implications(
    *,
    object_grain: str,
    available_metric_families: list[str],
    unsupported_metric_families: list[str],
    field_roles: dict[str, dict[str, Any]],
) -> list[str]:
    implications: list[str] = []
    if object_grain == "mixed_order_item":
        implications.append("当前数据可同时支持订单履约、商品结构、卖家差异和评价体验的复合分析。")
    if "sales_scale" in available_metric_families:
        implications.append("当前数据可支持交易规模、结构集中度和对象分层分析。")
    if _fields_with_role(field_roles, "fulfillment"):
        implications.append("当前数据可支持履约时效、晚到、售后体验和交付差异分析。")
    if _fields_with_role(field_roles, "review"):
        implications.append("当前数据可支持评分、评论和售后口碑的结构差异分析。")
    if "profitability" in unsupported_metric_families:
        implications.append("当前数据缺完整成本口径，因此不能直接推出真实利润与 ROI。")
    return implications or ["当前数据更多用于限定研究边界，而不是直接增加行业事实密度。"]


def _research_questions_from_data(
    *,
    object_grain: str,
    available_metric_families: list[str],
    unsupported_metric_families: list[str],
    field_roles: dict[str, dict[str, Any]],
) -> list[str]:
    questions: list[str] = []
    if object_grain == "mixed_order_item":
        questions.append("订单、商品、卖家与客户维度混合出现时，哪些行业背景最能解释当前履约与评价差异？")
    if _fields_with_role(field_roles, "fulfillment"):
        questions.append("当前数据已显露履约与晚到信号，行研应补哪些平台履约规则与售后边界？")
    if _fields_with_role(field_roles, "review"):
        questions.append("当前数据已显露评分与评论信号，行研应如何解释平台评价机制与消费者权益边界？")
    if "sales_scale" in available_metric_families:
        questions.append("当前数据已能看交易结构，行研应补哪些市场结构、集中度和 benchmark 边界？")
    if "profitability" in unsupported_metric_families:
        questions.append("缺少完整成本字段时，行研应如何补充毛利结构、成本构成与 ROI 不可比原因？")
    return questions[:10]


def _field_role_evidence(frame: pd.DataFrame) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], list[dict[str, Any]]]:
    field_roles: dict[str, dict[str, Any]] = {}
    sample_value_evidence: dict[str, list[str]] = {}
    ambiguous_fields: list[dict[str, Any]] = []
    for field_name in frame.columns.astype(str).tolist():
        detail = _field_role_model(field_name, frame[field_name])
        field_roles[field_name] = {
            "assigned_roles": detail["assigned_roles"],
            "evidence": detail["evidence"],
            "dtype": detail["dtype"],
            "non_null_ratio": detail["non_null_ratio"],
            "unique_count": detail["unique_count"],
            "unique_ratio": detail["unique_ratio"],
        }
        sample_value_evidence[field_name] = list(detail["sample_values"])
        if detail["candidate_roles"]:
            ambiguous_fields.append(
                {
                    "field": field_name,
                    "candidate_roles": detail["candidate_roles"],
                    "reason": detail["ambiguous_reason"],
                    "evidence": detail["evidence"],
                }
            )
    return field_roles, sample_value_evidence, ambiguous_fields


def build_industry_data_context_summary(
    *,
    dataset_name: str,
    uploaded_file_name: str,
    sheet_names: list[str],
    field_names: list[str],
    sample_values: list[str],
    data_types: dict[str, str] | None,
    row_count: int | None,
    column_count: int | None,
    universal_metric_mining_result: dict[str, Any] | None,
    domain_metric_registry: dict[str, Any] | None,
    derived_metric_rows: list[dict[str, Any]] | None,
    proxy_metric_rows: list[dict[str, Any]] | None,
    frame: pd.DataFrame | None = None,
    router_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metric_payload = universal_metric_mining_result or {}
    registry = domain_metric_registry or metric_payload.get("domain_metric_registry") or {}
    business_profile = _safe_text(registry.get("recommended_report_chain") or metric_payload.get("business_profile"))
    direct_metric_ids = list(registry.get("direct_metrics") or [])
    derived_metric_ids = list(
        registry.get("derived_metrics")
        or [row.get("metric_id") for row in metric_payload.get("derived_metrics") or [] if row.get("metric_id")]
    )
    proxy_metric_ids = list(
        registry.get("proxy_metrics")
        or [row.get("metric_id") for row in metric_payload.get("proxy_metrics") or [] if row.get("metric_id")]
    )
    unsupported_metric_ids = list(registry.get("unsupported_metrics") or [])

    if frame is not None:
        inferred_data_types = {str(col): str(frame[col].dtype) for col in frame.columns}
        real_row_count = int(len(frame))
        real_col_count = int(len(frame.columns))
        field_roles, sample_value_evidence, ambiguous_fields = _field_role_evidence(frame)
    else:
        inferred_data_types = data_types or {}
        real_row_count = int(row_count or 0)
        real_col_count = int(column_count or len(field_names))
        field_roles = {
            field: {
                "assigned_roles": [],
                "evidence": [f"仅有外部传入 data_types={inferred_data_types.get(field, '')}，缺少真实 frame，当前无法做更深字段建模。"],
                "dtype": inferred_data_types.get(field, ""),
                "non_null_ratio": None,
                "unique_count": None,
                "unique_ratio": None,
            }
            for field in field_names
        }
        sample_value_evidence = {field: [] for field in field_names}
        ambiguous_fields = []

    object_grain = _object_grain(field_roles)
    object_like_fields = _fields_with_role(field_roles, "object")
    amount_like_fields = _fields_with_role(field_roles, "amount")
    cost_like_fields = _fields_with_role(field_roles, "cost")
    inventory_like_fields = _fields_with_role(field_roles, "inventory")
    date_like_fields = _fields_with_role(field_roles, "time")
    text_like_fields = _fields_with_role(field_roles, "text")
    fulfillment_like_fields = _fields_with_role(field_roles, "fulfillment")
    review_like_fields = _fields_with_role(field_roles, "review")

    available_metric_families = _metric_families(direct_metric_ids)
    derived_metric_families = _metric_families(derived_metric_ids)
    proxy_metric_families = _metric_families(proxy_metric_ids)
    unsupported_metric_families = _metric_families(unsupported_metric_ids)

    payload = {
        "dataset_name": dataset_name or uploaded_file_name,
        "sheet_name": sheet_names[0] if sheet_names else "Sheet1",
        "row_count": real_row_count,
        "column_count": real_col_count,
        "inferred_business_context_from_data": _infer_context(
            business_profile=business_profile,
            object_grain=object_grain,
            field_roles=field_roles,
            available_metric_families=available_metric_families,
            router_result=router_result,
        ),
        "object_grain": object_grain,
        "object_like_fields": object_like_fields,
        "amount_like_fields": amount_like_fields,
        "cost_like_fields": cost_like_fields,
        "inventory_like_fields": inventory_like_fields,
        "date_like_fields": date_like_fields,
        "text_like_fields": text_like_fields,
        "fulfillment_like_fields": fulfillment_like_fields,
        "review_like_fields": review_like_fields,
        "candidate_business_objects": _candidate_business_objects(object_grain, field_roles),
        "candidate_observation_units": _candidate_observation_units(object_grain, field_roles),
        "available_metric_families": available_metric_families,
        "derived_metric_families": derived_metric_families,
        "proxy_metric_families": proxy_metric_families,
        "unsupported_metric_families": unsupported_metric_families,
        "industry_research_implications": _implications(
            object_grain=object_grain,
            available_metric_families=available_metric_families,
            unsupported_metric_families=unsupported_metric_families,
            field_roles=field_roles,
        ),
        "research_questions_generated_from_data": _research_questions_from_data(
            object_grain=object_grain,
            available_metric_families=available_metric_families + derived_metric_families,
            unsupported_metric_families=unsupported_metric_families,
            field_roles=field_roles,
        ),
        "forbidden_current_dataset_claims": [
            "不得写当前业务销售表现优秀或较差。",
            "不得对当前 SKU、供应商、渠道给出对象级经营决策。",
            "不得把当前数据派生指标写成行业 benchmark。",
            "不得把外部资料写成当前数据证据。",
        ],
        "can_support_what": _implications(
            object_grain=object_grain,
            available_metric_families=available_metric_families,
            unsupported_metric_families=unsupported_metric_families,
            field_roles=field_roles,
        ),
        "cannot_support_what": [
            "对象级经营动作拍板",
            "真实毛利、ROI、市场份额等需要外部或成本口径支持的结论",
            "写当前业务销售表现优秀或较差",
            "对当前 SKU、供应商、渠道给出对象级经营决策",
            "把当前数据派生指标写成行业 benchmark",
            "把外部资料写成当前数据证据",
        ],
        "sheet_names": sheet_names,
        "field_names": field_names,
        "data_types": inferred_data_types,
        "derived_metric_ids": derived_metric_ids,
        "proxy_metric_ids": proxy_metric_ids,
        "used_universal_metric_mining": bool(metric_payload),
        "used_domain_metric_registry": bool(registry),
        "used_derived_metrics_table": bool(derived_metric_rows or derived_metric_ids),
        "used_proxy_metrics_table": bool(proxy_metric_rows or proxy_metric_ids),
        "used_router_result": bool(router_result),
        "router_context": {
            "business_profile": _safe_text((router_result or {}).get("business_profile")),
            "secondary_profile": _safe_text((router_result or {}).get("secondary_profile")),
            "routing_reason": _safe_text((router_result or {}).get("routing_reason")),
            "decisive_object_grain": _safe_text((router_result or {}).get("decisive_object_grain")),
        },
        "field_role_evidence": field_roles,
        "sample_value_evidence": sample_value_evidence,
        "ambiguous_fields": ambiguous_fields,
    }
    return payload


def _summary_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# industry_data_context_summary",
        "",
        f"- dataset_name: `{payload.get('dataset_name', '')}`",
        f"- sheet_name: `{payload.get('sheet_name', '')}`",
        f"- row_count: `{payload.get('row_count', 0)}`",
        f"- column_count: `{payload.get('column_count', 0)}`",
        f"- inferred_business_context_from_data: {payload.get('inferred_business_context_from_data', '')}",
        f"- object_grain: `{payload.get('object_grain', '')}`",
        "",
        "## object_like_fields",
        *[f"- {item}" for item in payload.get("object_like_fields") or ["none"]],
        "",
        "## amount_like_fields",
        *[f"- {item}" for item in payload.get("amount_like_fields") or ["none"]],
        "",
        "## cost_like_fields",
        *[f"- {item}" for item in payload.get("cost_like_fields") or ["none"]],
        "",
        "## inventory_like_fields",
        *[f"- {item}" for item in payload.get("inventory_like_fields") or ["none"]],
        "",
        "## date_like_fields",
        *[f"- {item}" for item in payload.get("date_like_fields") or ["none"]],
        "",
        "## text_like_fields",
        *[f"- {item}" for item in payload.get("text_like_fields") or ["none"]],
        "",
        "## candidate_business_objects",
        *[f"- {item}" for item in payload.get("candidate_business_objects") or ["none"]],
        "",
        "## candidate_observation_units",
        *[f"- {item}" for item in payload.get("candidate_observation_units") or ["none"]],
        "",
        "## can_support_what",
        *[f"- {item}" for item in payload.get("can_support_what") or ["none"]],
        "",
        "## cannot_support_what",
        *[f"- {item}" for item in payload.get("cannot_support_what") or ["none"]],
        "",
        "## field_role_evidence",
        "",
    ]
    for field, detail in payload.get("field_role_evidence", {}).items():
        lines.extend(
            [
                f"### {field}",
                f"- assigned_roles: {' / '.join(detail.get('assigned_roles') or ['none'])}",
                f"- dtype: {detail.get('dtype', '')}",
                f"- non_null_ratio: {detail.get('non_null_ratio', '')}",
                f"- unique_count: {detail.get('unique_count', '')}",
                f"- unique_ratio: {detail.get('unique_ratio', '')}",
                *[f"- evidence: {item}" for item in detail.get("evidence") or ["none"]],
                "",
            ]
        )
    lines.extend(
        [
            "## sample_value_evidence",
            "",
        ]
    )
    for field, values in payload.get("sample_value_evidence", {}).items():
        lines.append(f"- {field}: {' / '.join(values or ['none'])}")
    lines.extend(["", "## ambiguous_fields", ""])
    for item in payload.get("ambiguous_fields", []) or [{"field": "none", "candidate_roles": [], "reason": "none", "evidence": []}]:
        lines.extend(
            [
                f"### {item.get('field', '')}",
                f"- candidate_roles: {' / '.join(item.get('candidate_roles') or ['none'])}",
                f"- reason: {item.get('reason', '')}",
                *[f"- evidence: {e}" for e in item.get("evidence") or ["none"]],
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _question_bank_from_data_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# industry_research_question_bank_from_data",
            "",
            *[f"- {item}" for item in payload.get("research_questions_generated_from_data") or ["none"]],
            "",
        ]
    )


def _boundary_from_data_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# industry_research_boundary_from_data",
            "",
            "## 数据上下文如何限定本次行研范围",
            "",
            f"- 当前上传数据暗示的业务场景：{payload.get('inferred_business_context_from_data', '')}",
            f"- 当前数据支持行研关注的主题：{'; '.join(payload.get('industry_research_implications') or []) or 'none'}",
            f"- 当前数据无法支持的当前业务结论：{'; '.join(payload.get('forbidden_current_dataset_claims') or []) or 'none'}",
            "- 行研资料只能提供外部背景、平台机制、指标口径和 benchmark 边界参考，不能替代当前数据分析。",
            "",
        ]
    )


def write_industry_data_context_outputs(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_md_path = out_dir / "industry_data_context_summary.md"
    summary_json_path = out_dir / "industry_data_context_summary.json"
    question_md_path = out_dir / "industry_research_question_bank_from_data.md"
    boundary_md_path = out_dir / "industry_research_boundary_from_data.md"
    summary_md_path.write_text(_summary_markdown(payload), encoding="utf-8")
    summary_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    question_md_path.write_text(_question_bank_from_data_markdown(payload), encoding="utf-8")
    boundary_md_path.write_text(_boundary_from_data_markdown(payload), encoding="utf-8")
    return {
        "industry_data_context_summary.md": str(summary_md_path.resolve()),
        "industry_data_context_summary.json": str(summary_json_path.resolve()),
        "industry_research_question_bank_from_data.md": str(question_md_path.resolve()),
        "industry_research_boundary_from_data.md": str(boundary_md_path.resolve()),
    }


def industry_data_context_gate_failures(
    *,
    summary_payload: dict[str, Any] | None,
    report_markdown: str,
) -> list[str]:
    failures: list[str] = []
    payload = summary_payload or {}
    if not payload.get("used_universal_metric_mining"):
        failures.append("industry_research_chain_did_not_read_universal_metric_mining_result")
    if not payload:
        failures.append("industry_data_context_summary_missing")
    markdown = _safe_text(report_markdown)

    def _contains_positive_pattern(pattern: str) -> bool:
        start = 0
        while True:
            idx = markdown.find(pattern, start)
            if idx < 0:
                return False
            left = markdown[max(0, idx - 16) : idx]
            if not any(token in left for token in ["无法支持", "不得", "不能", "不可", "禁止", "仅作", "示例", "边界说明"]):
                return True
            start = idx + len(pattern)

    forbidden_patterns = [
        "当前数据证明行业",
        "当前数据说明行业",
        "当前业务销售表现优秀",
        "当前业务销售表现较差",
        "建议加码当前SKU",
        "建议淘汰当前SKU",
        "建议替换当前供应商",
    ]
    if any(_contains_positive_pattern(pattern) for pattern in forbidden_patterns):
        failures.append("industry_report_turns_dataset_context_into_industry_fact_or_current_business_conclusion")
    return failures
