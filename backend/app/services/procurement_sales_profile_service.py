from __future__ import annotations

import re
from typing import Any

import pandas as pd


SALES_FIELD_TOKENS: tuple[str, ...] = (
    "gmv",
    "revenue",
    "netamount",
    "net amount",
    "net_amount",
    "transactionamount",
    "transaction amount",
    "transaction_amount",
    "translineamt",
    "trans line amt",
    "trans_line_amt",
    "quantity",
    "ordercount",
    "order_count",
    "orderid",
    "order_id",
    "customercount",
    "customer_count",
    "customerid",
    "customer_id",
    "conversion",
    "aov",
    "salestrend",
    "sales_trend",
    "category",
    "product",
    "sku",
)

SUPPLIER_ENTITY_FIELD_TOKENS: tuple[str, ...] = (
    "supplier",
    "suppliername",
    "supplier name",
    "supplier_name",
    "vendor",
    "vendorname",
    "vendor name",
    "vendor_name",
    "merchant",
    "merchantname",
    "merchant name",
    "merchant_name",
    "seller",
    "sellername",
    "seller name",
    "seller_name",
    "store",
    "shop",
)

LEDGER_TIME_FIELD_TOKENS: tuple[str, ...] = (
    "date",
    "paymentdate",
    "payment date",
    "payment_date",
    "postingdate",
    "posting date",
    "posting_date",
    "transpostdate",
    "trans post date",
    "trans_post_date",
    "purchasedate",
    "purchase date",
    "purchase_date",
)

PURPOSE_FIELD_TOKENS: tuple[str, ...] = (
    "description",
    "purposeofspend",
    "purpose of spend",
    "purpose_of_spend",
    "procurementclassification",
    "procurement classification",
    "procurement_classification",
    "servicecategorylabel",
    "service category label",
    "service_category_label",
    "servicecategory",
    "service_category",
    "category",
)

TRANSACTION_ID_FIELD_TOKENS: tuple[str, ...] = (
    "transactionnumber",
    "transaction number",
    "transaction_number",
    "transactionid",
    "transaction id",
    "transaction_id",
    "cardtransaction",
    "card transaction",
    "card_transaction",
)

CUSTOMER_ENTITY_FIELD_TOKENS: tuple[str, ...] = (
    "customerid",
    "customer_id",
    "customername",
    "customer_name",
    "customer",
)

SKU_ENTITY_FIELD_TOKENS: tuple[str, ...] = (
    "sku",
    "product",
    "productid",
    "product_id",
    "itemid",
    "item_id",
    "goodsid",
    "goods_id",
)

FULFILLMENT_FIELD_TOKENS: tuple[str, ...] = (
    "orderstatus",
    "order_status",
    "deliveredcustomerdate",
    "delivered_customer_date",
    "estimateddeliverydate",
    "estimated_delivery_date",
    "deliverydays",
    "delivery_days",
    "delaydays",
    "delay_days",
    "islate",
    "late",
    "fulfillment",
    "履约",
    "发货",
    "逾期",
    "签收",
)

REVIEW_FIELD_TOKENS: tuple[str, ...] = (
    "reviewscore",
    "review_score",
    "reviewtext",
    "review_text",
    "lowratingrate",
    "low_rating_rate",
    "reviewkeywords",
    "review_keywords",
    "评价",
    "低分",
    "差评",
    "投诉",
)

PROFIT_FIELD_TOKENS: tuple[str, ...] = (
    "grossprofit",
    "gross_profit",
    "grossmargin",
    "gross_margin",
    "netprofit",
    "net_profit",
    "毛利",
    "毛利率",
    "净利",
    "净利润",
)

INVENTORY_FIELD_TOKENS: tuple[str, ...] = (
    "stockqty",
    "stock_qty",
    "availablestock",
    "available_stock",
    "safetystock",
    "safety_stock",
    "inventorydays",
    "inventory_days",
    "inventoryturnover",
    "inventory_turnover",
    "sellthroughrate",
    "sell_through_rate",
    "stockoutrate",
    "stockout_rate",
    "overstockqty",
    "overstock_qty",
    "slowmovingdays",
    "slow_moving_days",
    "replenishmentqty",
    "replenishment_qty",
    "inventory",
    "stock",
    "库存",
    "周转",
    "缺货",
    "滞销",
    "补货",
)

PROCUREMENT_PRICE_FIELD_TOKENS: tuple[str, ...] = (
    "purchasecost",
    "purchase_cost",
    "procurementprice",
    "procurement_price",
    "supplyprice",
    "supply_price",
    "purchasequantity",
    "purchase_quantity",
    "purchaseorder",
    "purchase_order",
    "purchasecycle",
    "purchase_cycle",
    "leadtime",
    "lead_time",
    "supplierquote",
    "supplier_quote",
    "采购价",
    "采购成本",
    "供货价",
    "采购周期",
    "采购批次",
)

SUPPLIER_DELIVERY_FIELD_TOKENS: tuple[str, ...] = (
    "supplierdeliveryrate",
    "supplier_delivery_rate",
    "ontimedeliveryrate",
    "on_time_delivery_rate",
    "delaytimes",
    "delay_times",
    "fulfillmentgap",
    "fulfillment_gap",
    "交付",
    "延迟",
    "履约",
)

PAYMENT_TERM_FIELD_TOKENS: tuple[str, ...] = (
    "paymentterm",
    "payment_term",
    "rebate",
    "账期",
    "结算",
    "合同",
    "返利",
)

RETURN_COST_FIELD_TOKENS: tuple[str, ...] = (
    "returncost",
    "return_cost",
    "aftersalescost",
    "after_sales_cost",
    "qualitylosscost",
    "quality_loss_cost",
    "退货成本",
    "售后成本",
    "质量损失成本",
)

ALTERNATIVE_SUPPLIER_FIELD_TOKENS: tuple[str, ...] = (
    "alternativesupplier",
    "alternative_supplier",
    "替代供应商",
)

SUPPLIER_CONTRACT_FIELD_TOKENS: tuple[str, ...] = (
    "suppliercontract",
    "supplier_contract",
    "contractterm",
    "contract_term",
    "合同",
    "合约",
)

COMPETITOR_PRICE_FIELD_TOKENS: tuple[str, ...] = (
    "competitorprice",
    "competitor_price",
    "priceindex",
    "price_index",
    "discountrate",
    "discount_rate",
    "竞品价",
    "价格指数",
)

SCALE_ACTIONS = {
    "主推",
    "核心主推",
    "资源倾斜",
    "预算倾斜",
    "加码",
    "继续主推",
    "重点投放",
    "重点合作",
}
INVENTORY_ACTIONS = {
    "补货",
    "补货放量",
    "清仓",
    "清理退场",
    "停止补货",
    "并柜",
    "移出主推池",
    "停止采购",
}
PROCUREMENT_ACTIONS = {
    "压价",
    "成本优化",
    "采购成本优化",
    "价格谈判空间",
    "供应商让利空间",
}
SUPPLIER_ACCOUNTABILITY_ACTIONS = {
    "直接替换供应商",
    "供应商履约问责",
    "淘汰供应商",
    "直接替换",
}
LOW_SAMPLE_BLOCKED_ACTIONS = {
    "主推",
    "核心主推",
    "资源倾斜",
    "清退",
    "清理退场",
    "重点合作",
    "直接替换",
}

HARD_OBJECT_OVERRIDES: dict[str, dict[str, Any]] = {}
PROFIT_FORBIDDEN_PHRASES = (
    "当前已具备毛利率口径",
    "毛利率",
    "毛利贡献",
    "利润质量",
    "促销后毛利",
    "毛利空间",
)

BANNED_REPORT_PATTERNS = [
    r"release[_ ]gate",
    r"analysis_program",
    r"decision_summary",
    r"\bworkflow\b",
    r"\bdebug\b",
    r"正式报告里",
    r"下一轮",
    r"不能继续复写",
    r"同一条监控链",
]

INFERENCE_LEVEL_A = "evidence_based_decision"
INFERENCE_LEVEL_B = "proxy_based_inference"
INFERENCE_LEVEL_C = "business_hypothesis"
INFERENCE_LEVEL_D = "risk_flag"
INFERENCE_LEVEL_E = "data_required"

SOFT_ALLOWED_ACTIONS = {
    "进入候选池",
    "暂停追加资源",
    "低样本复核",
    "补字段验证",
    "小流量测试",
    "差评归因",
    "履约链路拆分",
    "供应商观察",
    "替代供应商预研",
    "差评归因 + 履约修复 + 待补毛利后判断是否放量",
    "降权控量，修履约和低分后再恢复",
    "待补毛利、库存、退货成本后判断是否加码",
    "待补库存后判断",
    "待补采购价后评估",
    "履约链路待拆分",
}


def _lowered_columns(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    columns = [str(column) for column in frame.columns.astype(str).tolist()]
    lowered = [column.lower() for column in columns]
    return columns, lowered


def _collect_columns(columns: list[str], lowered: list[str], tokens: tuple[str, ...]) -> list[str]:
    matched: list[str] = []
    for column, lowered_column in zip(columns, lowered):
        if any(token in lowered_column for token in tokens):
            if column not in matched:
                matched.append(column)
    return matched


def field_availability_registry(frame: pd.DataFrame) -> dict[str, Any]:
    columns, lowered = _lowered_columns(frame)

    sales_fields = _collect_columns(columns, lowered, SALES_FIELD_TOKENS)
    supplier_entity_fields = _collect_columns(columns, lowered, SUPPLIER_ENTITY_FIELD_TOKENS)
    ledger_time_fields = _collect_columns(columns, lowered, LEDGER_TIME_FIELD_TOKENS)
    purpose_fields = _collect_columns(columns, lowered, PURPOSE_FIELD_TOKENS)
    transaction_id_fields = _collect_columns(columns, lowered, TRANSACTION_ID_FIELD_TOKENS)
    customer_entity_fields = _collect_columns(columns, lowered, CUSTOMER_ENTITY_FIELD_TOKENS)
    sku_entity_fields = _collect_columns(columns, lowered, SKU_ENTITY_FIELD_TOKENS)
    fulfillment_fields = _collect_columns(columns, lowered, FULFILLMENT_FIELD_TOKENS)
    review_fields = _collect_columns(columns, lowered, REVIEW_FIELD_TOKENS)
    profit_fields = _collect_columns(columns, lowered, PROFIT_FIELD_TOKENS)
    inventory_fields = _collect_columns(columns, lowered, INVENTORY_FIELD_TOKENS)
    procurement_price_fields = _collect_columns(columns, lowered, PROCUREMENT_PRICE_FIELD_TOKENS)
    supplier_delivery_fields = _collect_columns(columns, lowered, SUPPLIER_DELIVERY_FIELD_TOKENS)
    payment_term_fields = _collect_columns(columns, lowered, PAYMENT_TERM_FIELD_TOKENS)
    return_cost_fields = _collect_columns(columns, lowered, RETURN_COST_FIELD_TOKENS)
    alternative_supplier_fields = _collect_columns(columns, lowered, ALTERNATIVE_SUPPLIER_FIELD_TOKENS)
    supplier_contract_fields = _collect_columns(columns, lowered, SUPPLIER_CONTRACT_FIELD_TOKENS)
    competitor_price_fields = _collect_columns(columns, lowered, COMPETITOR_PRICE_FIELD_TOKENS)

    has_sales_fields = bool(sales_fields)
    has_supplier_entity_fields = bool(supplier_entity_fields)
    has_ledger_time_fields = bool(ledger_time_fields)
    has_purpose_fields = bool(purpose_fields)
    has_transaction_id_fields = bool(transaction_id_fields)
    has_customer_entity_fields = bool(customer_entity_fields)
    has_sku_entity_fields = bool(sku_entity_fields)
    has_fulfillment_fields = bool(fulfillment_fields)
    has_review_fields = bool(review_fields)
    has_profit_fields = bool(profit_fields)
    has_inventory_fields = bool(inventory_fields)
    has_procurement_price_fields = bool(procurement_price_fields)
    has_supplier_delivery_fields = bool(supplier_delivery_fields)
    has_payment_term_fields = bool(payment_term_fields)
    has_return_cost_fields = bool(return_cost_fields)
    has_supplier_contract_fields = bool(supplier_contract_fields)
    has_competitor_price_fields = bool(competitor_price_fields)

    if (
        has_sales_fields
        and has_profit_fields
        and has_inventory_fields
        and has_procurement_price_fields
        and has_supplier_delivery_fields
    ):
        report_mode = "full_procurement_sales_decision_report"
    elif (
        has_sales_fields
        and has_ledger_time_fields
        and has_supplier_entity_fields
        and not has_sku_entity_fields
        and not has_customer_entity_fields
        and not has_fulfillment_fields
    ):
        report_mode = "procurement_spend_ledger_report"
    elif has_sales_fields and has_fulfillment_fields and has_review_fields:
        report_mode = "sales_fulfillment_product_report"
    elif has_sales_fields:
        report_mode = "sales_structure_report"
    else:
        report_mode = "insufficient_for_decision"

    missing_field_groups = [
        group
        for group, present in [
            ("sales_fields", has_sales_fields),
            ("supplier_entity_fields", has_supplier_entity_fields),
            ("ledger_time_fields", has_ledger_time_fields),
            ("purpose_fields", has_purpose_fields),
            ("transaction_id_fields", has_transaction_id_fields),
            ("fulfillment_fields", has_fulfillment_fields),
            ("review_fields", has_review_fields),
            ("profit_fields", has_profit_fields),
            ("inventory_fields", has_inventory_fields),
            ("procurement_price_fields", has_procurement_price_fields),
            ("supplier_delivery_fields", has_supplier_delivery_fields),
            ("payment_term_fields", has_payment_term_fields),
            ("return_cost_fields", has_return_cost_fields),
            ("supplier_contract_fields", has_supplier_contract_fields),
            ("competitor_price_fields", has_competitor_price_fields),
        ]
        if not present
    ]

    return {
        "business_profile": "procurement_sales",
        "report_mode": report_mode,
        "mode": report_mode,
        "has_sales_fields": has_sales_fields,
        "has_supplier_entity_fields": has_supplier_entity_fields,
        "has_ledger_time_fields": has_ledger_time_fields,
        "has_purpose_fields": has_purpose_fields,
        "has_transaction_id_fields": has_transaction_id_fields,
        "has_customer_entity_fields": has_customer_entity_fields,
        "has_sku_entity_fields": has_sku_entity_fields,
        "has_fulfillment_fields": has_fulfillment_fields,
        "has_review_fields": has_review_fields,
        "has_profit_fields": has_profit_fields,
        "has_inventory_fields": has_inventory_fields,
        "has_procurement_price_fields": has_procurement_price_fields,
        "has_supplier_delivery_fields": has_supplier_delivery_fields,
        "has_payment_term_fields": has_payment_term_fields,
        "has_return_cost_fields": has_return_cost_fields,
        "has_supplier_contract_fields": has_supplier_contract_fields,
        "has_competitor_price_fields": has_competitor_price_fields,
        "missing_field_groups": missing_field_groups,
        "missing_domains": missing_field_groups,
        "field_coverage": {
            "sales_fields": sales_fields,
            "supplier_entity_fields": supplier_entity_fields,
            "ledger_time_fields": ledger_time_fields,
            "purpose_fields": purpose_fields,
            "transaction_id_fields": transaction_id_fields,
            "customer_entity_fields": customer_entity_fields,
            "sku_entity_fields": sku_entity_fields,
            "fulfillment_fields": fulfillment_fields,
            "review_fields": review_fields,
            "profit_fields": profit_fields,
            "inventory_fields": inventory_fields,
            "procurement_price_fields": procurement_price_fields,
            "supplier_delivery_fields": supplier_delivery_fields,
            "payment_term_fields": payment_term_fields,
            "return_cost_fields": return_cost_fields,
            "alternative_supplier_fields": alternative_supplier_fields,
            "supplier_contract_fields": supplier_contract_fields,
            "competitor_price_fields": competitor_price_fields,
            "sales": sales_fields,
            "procurement": procurement_price_fields,
            "profit": profit_fields,
            "inventory": inventory_fields,
            "supplier": supplier_entity_fields or supplier_delivery_fields or alternative_supplier_fields,
            "purpose": purpose_fields,
            "time": ledger_time_fields or fulfillment_fields,
            "after_sales": review_fields,
            "price_power": [],
        },
        "field_coverage_flags": {
            "sales": has_sales_fields,
            "supplier_entity": has_supplier_entity_fields,
            "ledger_time": has_ledger_time_fields,
            "purpose": has_purpose_fields,
            "transaction_id": has_transaction_id_fields,
            "procurement": has_procurement_price_fields,
            "profit": has_profit_fields,
            "inventory": has_inventory_fields,
            "supplier": bool(supplier_entity_fields or supplier_delivery_fields or alternative_supplier_fields),
            "price_power": False,
            "after_sales": has_review_fields,
        },
        "requirements": {
            "profit_required": profit_fields,
            "inventory_required": inventory_fields,
            "procurement_required": procurement_price_fields,
            "supplier_delivery_required": supplier_delivery_fields,
            "alternative_supplier_required": alternative_supplier_fields,
            "contract_required": payment_term_fields,
            "return_cost_required": return_cost_fields,
            "supplier_contract_required": supplier_contract_fields,
            "competitor_price_required": competitor_price_fields,
        },
        "capabilities": {
            "can_use_profit_language": has_profit_fields,
            "can_use_inventory_actions": has_inventory_fields,
            "can_use_procurement_actions": has_procurement_price_fields,
            "can_blame_supplier_delivery": has_supplier_delivery_fields,
            "can_replace_supplier": has_supplier_delivery_fields and bool(alternative_supplier_fields),
            "can_use_spend_governance_language": report_mode == "procurement_spend_ledger_report",
            "can_use_supplier_concentration": bool(has_supplier_entity_fields and has_sales_fields),
            "can_use_purpose_segmentation": bool(has_purpose_fields and has_sales_fields),
            "can_use_time_pulse": bool(has_ledger_time_fields and has_sales_fields),
        },
    }


def procurement_sales_readiness_check(frame: pd.DataFrame) -> dict[str, Any]:
    return field_availability_registry(frame)


def low_sample_guard(
    *,
    order_count: float | None = None,
    customer_count: float | None = None,
    review_count: float | None = None,
    low_rating_rate: float | None = None,
    late_rate: float | None = None,
) -> dict[str, Any]:
    order_count = float(order_count or 0.0)
    customer_count = float(customer_count or 0.0)
    review_count = float(review_count or 0.0)
    low_sample = order_count < 10 or customer_count < 10
    review_thin = review_count < 20
    if low_sample:
        return {
            "is_low_sample": True,
            "label": "低样本保护",
            "reason": "订单或客户样本不足，禁止输出主推、清退、重点合作和直接替换等强动作。",
        }
    if review_thin and ((low_rating_rate or 0.0) >= 0.5 or (late_rate or 0.0) >= 0.5):
        return {
            "is_low_sample": True,
            "label": "低样本波动",
            "reason": "低分率或逾期率来自过小样本，只能作为风险提示，不能升级成强结论。",
        }
    return {"is_low_sample": False, "label": "", "reason": ""}


def _direct_field_requirements_for_action(candidate_action: str) -> list[str]:
    action = str(candidate_action or "").strip()
    requirements: list[str] = []
    if action in SCALE_ACTIONS or "放量" in action or "加码" in action:
        requirements.extend(["profit_fields", "inventory_fields", "return_cost_fields"])
    if action in INVENTORY_ACTIONS:
        requirements.extend(["inventory_fields"])
    if action in PROCUREMENT_ACTIONS:
        requirements.extend(["procurement_price_fields"])
    if action in SUPPLIER_ACCOUNTABILITY_ACTIONS:
        requirements.extend(["supplier_delivery_fields"])
    return list(dict.fromkeys(requirements))


def _field_group_available(registry: dict[str, Any], field_group: str) -> bool:
    mapping = {
        "sales_fields": "has_sales_fields",
        "fulfillment_fields": "has_fulfillment_fields",
        "review_fields": "has_review_fields",
        "profit_fields": "has_profit_fields",
        "inventory_fields": "has_inventory_fields",
        "procurement_price_fields": "has_procurement_price_fields",
        "supplier_delivery_fields": "has_supplier_delivery_fields",
        "payment_term_fields": "has_payment_term_fields",
        "return_cost_fields": "has_return_cost_fields",
        "supplier_contract_fields": "has_supplier_contract_fields",
        "competitor_price_fields": "has_competitor_price_fields",
    }
    return bool(registry.get(mapping.get(field_group, ""), False))


def inference_without_direct_data_controller(
    *,
    object_level: str,
    object_id: str,
    candidate_label: str,
    candidate_action: str,
    evidence: dict[str, Any] | None,
    field_availability_registry: dict[str, Any],
    sample_size: dict[str, Any] | None = None,
    risk_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = evidence or {}
    sample_size = sample_size or {}
    risk_metrics = risk_metrics or {}
    order_count = float(sample_size.get("order_count") or 0.0)
    customer_count = float(sample_size.get("customer_count") or 0.0)
    review_count = float(sample_size.get("review_count") or 0.0)
    low_rating_rate = float(risk_metrics.get("low_rating_rate") or 0.0)
    late_rate = float(risk_metrics.get("late_rate") or 0.0)

    required_direct_fields = _direct_field_requirements_for_action(candidate_action)
    missing_fields = [field for field in required_direct_fields if not _field_group_available(field_availability_registry, field)]
    proxy_evidence: list[str] = []
    business_assumption = ""
    validation_plan = "补字段验证"
    confidence_level = "high"
    prohibited_actions: list[str] = []
    conclusion_type = INFERENCE_LEVEL_A

    if order_count < 10 or customer_count < 10:
        conclusion_type = INFERENCE_LEVEL_D
        confidence_level = "low"
        validation_plan = "继续观察一周期并补充订单样本"
        business_assumption = "当前订单或客户样本偏低，现有波动更适合作为风险提示。"
    elif missing_fields:
        for label, value in [
            ("逾期率", late_rate),
            ("平均履约天数", risk_metrics.get("avg_fulfillment_days")),
            ("低分评价占比", low_rating_rate),
            ("订单覆盖", order_count),
            ("客户覆盖", customer_count),
        ]:
            if value not in (None, "", 0, 0.0):
                proxy_evidence.append(f"{label}={value}")

        if proxy_evidence and any(field in missing_fields for field in ["supplier_delivery_fields", "inventory_fields"]):
            conclusion_type = INFERENCE_LEVEL_B
            confidence_level = "medium"
            validation_plan = "补充直接字段后验证代理结论是否成立"
        elif proxy_evidence:
            conclusion_type = INFERENCE_LEVEL_C
            confidence_level = "low" if "profit_fields" in missing_fields else "medium"
            validation_plan = "基于当前代理指标做小流量验证或补字段复核"
            business_assumption = "当前结论基于代理指标和业务逻辑，不能视为已被直接字段证实。"
        else:
            conclusion_type = INFERENCE_LEVEL_E
            confidence_level = "low"
            validation_plan = "补齐关键字段后再生成正式经营结论"
            business_assumption = "当前缺少支持该动作的直接字段，暂不能做有效判断。"

    if conclusion_type != INFERENCE_LEVEL_A:
        prohibited_actions.extend([action for action in [candidate_action] if action])
    if review_count < 20 and low_rating_rate:
        proxy_evidence.append("低分率仅作风险提示")
        if conclusion_type == INFERENCE_LEVEL_A:
            conclusion_type = INFERENCE_LEVEL_D
            confidence_level = "low"
            validation_plan = "补充评价样本后再判断"

    output_conclusion = {
        INFERENCE_LEVEL_A: candidate_action,
        INFERENCE_LEVEL_B: f"代理指标显示：{candidate_label or object_id}存在待验证风险或机会",
        INFERENCE_LEVEL_C: f"业务假设：{candidate_label or object_id}可能存在承接不足或结构机会，需待验证",
        INFERENCE_LEVEL_D: "低样本风险提示",
        INFERENCE_LEVEL_E: "需要补齐关键字段后再判断",
    }[conclusion_type]

    return {
        "object": object_id,
        "current_evidence": " / ".join(proxy_evidence) if proxy_evidence else (business_assumption or "现有直接证据不足"),
        "missing_fields": missing_fields,
        "output_conclusion": output_conclusion,
        "conclusion_type": conclusion_type,
        "confidence_level": confidence_level,
        "prohibited_actions": prohibited_actions,
        "proxy_evidence": proxy_evidence,
        "business_assumption": business_assumption,
        "validation_plan": validation_plan,
    }


def action_guardrail(
    *,
    object_level: str,
    object_id: str = "",
    candidate_label: str = "",
    candidate_action: str | None = None,
    evidence: dict[str, Any] | None = None,
    field_availability_registry: dict[str, Any] | None = None,
    sample_size: dict[str, Any] | None = None,
    risk_metrics: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    attempted_action: str | None = None,
    order_count: float | None = None,
    customer_count: float | None = None,
    review_count: float | None = None,
    low_rating_rate: float | None = None,
    late_rate: float | None = None,
) -> dict[str, Any]:
    source_registry = field_availability_registry or registry or {}
    if sample_size:
        order_count = sample_size.get("order_count", order_count)
        customer_count = sample_size.get("customer_count", customer_count)
        review_count = sample_size.get("review_count", review_count)
    if risk_metrics:
        low_rating_rate = risk_metrics.get("low_rating_rate", low_rating_rate)
        late_rate = risk_metrics.get("late_rate", late_rate)
    attempted = str(candidate_action or attempted_action or "").strip() or "观察"
    capabilities = source_registry.get("capabilities") or {}
    blocked_reason = ""
    required_missing_fields: list[str] = []
    downgraded_action = attempted
    action_strength = "hard_action"
    inference = inference_without_direct_data_controller(
        object_level=object_level,
        object_id=object_id,
        candidate_label=candidate_label,
        candidate_action=attempted,
        evidence=evidence,
        field_availability_registry=source_registry,
        sample_size={
            "order_count": order_count,
            "customer_count": customer_count,
            "review_count": review_count,
        },
        risk_metrics={
            "low_rating_rate": low_rating_rate,
            "late_rate": late_rate,
            "avg_fulfillment_days": (evidence or {}).get("avg_fulfillment_days"),
        },
    )

    sample_guard = low_sample_guard(
        order_count=order_count,
        customer_count=customer_count,
        review_count=review_count,
        low_rating_rate=low_rating_rate,
        late_rate=late_rate,
    )
    if sample_guard["is_low_sample"] and attempted in LOW_SAMPLE_BLOCKED_ACTIONS:
        return {
            "allowed": False,
            "blocked": True,
            "downgraded_action": "低优先级复核" if object_level == "sku" else "样本不足人工复核",
            "action_strength": "observe_only",
            "blocked_reason": sample_guard["reason"],
            "required_missing_fields": [],
            "inference": inference,
        }

    if attempted in SCALE_ACTIONS and not capabilities.get("can_use_profit_language"):
        blocked_reason = "缺毛利/利润字段"
        required_missing_fields = ["gross_profit", "gross_margin", "net_profit"]
        downgraded_action = "资源候选待补利润字段"
        action_strength = "candidate"
    elif attempted in INVENTORY_ACTIONS and not capabilities.get("can_use_inventory_actions"):
        blocked_reason = "缺库存/周转字段"
        required_missing_fields = ["stock_qty", "available_stock", "inventory_days", "inventory_turnover"]
        downgraded_action = "待补库存后判断" if object_level == "sku" else "低优先级复核"
        action_strength = "candidate" if object_level != "sku" else "soft_action"
    elif attempted in PROCUREMENT_ACTIONS and not capabilities.get("can_use_procurement_actions"):
        blocked_reason = "缺采购价/采购成本字段"
        required_missing_fields = ["purchase_cost", "procurement_price", "supply_price"]
        downgraded_action = "待补采购价后评估"
        action_strength = "candidate"
    elif attempted in SUPPLIER_ACCOUNTABILITY_ACTIONS and not capabilities.get("can_blame_supplier_delivery"):
        blocked_reason = "缺供应商交付字段"
        required_missing_fields = ["supplier_delivery_rate", "on_time_delivery_rate", "delay_times"]
        downgraded_action = "履约链路待拆分"
        action_strength = "candidate"
    elif attempted in {"差评归因", "履约修复", "口碑修复", "履约排查", "暂停新增主推承接", "暂停追加流量"}:
        action_strength = "soft_action"
    elif attempted in {"观察", "低优先级复核", "样本不足人工复核", "待补库存后判断", "待补采购价后评估", "资源候选待补利润字段"}:
        action_strength = "candidate"

    if inference["conclusion_type"] != INFERENCE_LEVEL_A and action_strength == "hard_action":
        if attempted in SOFT_ALLOWED_ACTIONS or any(term in attempted for term in ["修复", "归因", "观察", "验证", "拆分"]):
            action_strength = "soft_action"
        else:
            action_strength = "candidate"
    if inference["conclusion_type"] != INFERENCE_LEVEL_A and not blocked_reason:
        required_missing_fields = list(dict.fromkeys([*required_missing_fields, *inference["missing_fields"]]))

    return {
        "allowed": not bool(blocked_reason),
        "blocked": bool(blocked_reason),
        "downgraded_action": downgraded_action,
        "action_strength": action_strength,
        "blocked_reason": blocked_reason,
        "required_missing_fields": required_missing_fields,
        "inference": inference,
    }


def conclusion_strength_controller(
    *,
    readiness: dict[str, Any],
    desired_action: str,
    object_level: str,
    order_count: float | None = None,
    customer_count: float | None = None,
    review_count: float | None = None,
    low_rating_rate: float | None = None,
    late_rate: float | None = None,
) -> dict[str, str]:
    guarded = action_guardrail(
        registry=readiness,
        attempted_action=desired_action,
        object_level=object_level,
        order_count=order_count,
        customer_count=customer_count,
        review_count=review_count,
        low_rating_rate=low_rating_rate,
        late_rate=late_rate,
    )
    strength_label = {
        "observe_only": "仅观察信号",
        "candidate": "可初步判断",
        "soft_action": "轻动作",
        "hard_action": "可直接决策" if readiness.get("report_mode") == "full_procurement_sales_decision_report" else "可初步判断",
    }.get(guarded["action_strength"], "可初步判断")
    return {
        "action": guarded["downgraded_action"],
        "strength": strength_label,
        "boundary": guarded["blocked_reason"] or "当前结论强度已按字段完整度和样本量自动降级。",
    }


def global_decision_resolver(
    *,
    object_id: str,
    object_level: str,
    all_candidate_labels: list[str],
    all_candidate_actions: list[str],
    evidence_bundle: dict[str, Any],
    missing_fields: list[str],
    sample_size_flags: dict[str, Any],
    risk_flags: list[str],
    business_mode: str,
    conclusion_strength: str,
) -> dict[str, Any]:
    desired_label = next((item for item in all_candidate_labels if str(item).strip()), "待复核对象")
    attempted_actions = [str(item).strip() for item in all_candidate_actions if str(item).strip()]
    desired_action = attempted_actions[0] if attempted_actions else "观察"
    guarded = action_guardrail(
        registry={
            "capabilities": {
                "can_use_profit_language": "profit_fields" not in missing_fields,
                "can_use_inventory_actions": "inventory_fields" not in missing_fields,
                "can_use_procurement_actions": "procurement_price_fields" not in missing_fields,
                "can_blame_supplier_delivery": "supplier_delivery_fields" not in missing_fields,
            },
            "report_mode": business_mode,
        },
        attempted_action=desired_action,
        object_level=object_level,
        order_count=sample_size_flags.get("order_count"),
        customer_count=sample_size_flags.get("customer_count"),
        review_count=sample_size_flags.get("review_count"),
        low_rating_rate=sample_size_flags.get("low_rating_rate"),
        late_rate=sample_size_flags.get("late_rate"),
    )
    blocked_actions = [action for action in attempted_actions if action != guarded["downgraded_action"]]
    final_label = desired_label
    final_action = guarded["downgraded_action"]
    action_strength = guarded["action_strength"]
    blocked_reason = guarded["blocked_reason"]
    required_missing_fields = list(dict.fromkeys([*missing_fields, *guarded["required_missing_fields"]]))[:6]
    inference = guarded.get("inference") or {}

    if HARD_OBJECT_OVERRIDES and object_id in HARD_OBJECT_OVERRIDES:
        override = HARD_OBJECT_OVERRIDES[object_id]
        final_label = str(override["final_label"])
        final_action = str(override["final_action"])
        action_strength = str(override["action_strength"])
        blocked_actions = list(override["blocked_actions"])
        blocked_reason = str(override["blocked_reason"])

    return {
        "object_id": object_id,
        "object_level": object_level,
        "final_label": final_label,
        "final_action": final_action,
        "action_strength": action_strength,
        "blocked_actions": blocked_actions,
        "blocked_reason": blocked_reason,
        "reason_for_block": blocked_reason,
        "evidence_summary": " / ".join(str(item).strip() for item in (evidence_bundle.get("facts") or [])[:4] if str(item).strip()),
        "next_required_data": required_missing_fields,
        "risk_flags": risk_flags[:6],
        "business_mode": business_mode,
        "conclusion_strength": conclusion_strength,
        "conclusion_type": inference.get("conclusion_type", INFERENCE_LEVEL_A),
        "missing_fields": list(dict.fromkeys(inference.get("missing_fields") or required_missing_fields)),
        "proxy_evidence": inference.get("proxy_evidence") or [],
        "business_assumption": inference.get("business_assumption", ""),
        "validation_plan": inference.get("validation_plan", ""),
        "confidence_level": inference.get("confidence_level", "high"),
        "prohibited_actions": inference.get("prohibited_actions") or blocked_actions,
    }


def clean_report_text_filter(text: str) -> str:
    cleaned = str(text or "")
    replacements = {
        "release gate": "",
        "release_gate": "",
        "analysis_program": "",
        "decision_summary": "",
        "workflow": "",
        "debug": "",
        "正式报告里": "",
        "下一轮": "",
        "不能继续复写": "",
        "同一条监控链": "同一组经营指标",
        "推荐统计方法实跑与解读": "统计结论附录",
        "这个方法在回答": "统计结果说明",
        "说明了什么": "业务含义",
        "当前已具备毛利率口径": "当前利润字段待补齐",
        "毛利贡献": "利润贡献待补数",
        "利润质量": "利润表现",
        "促销后毛利": "促销后利润待补数",
        "毛利空间": "利润空间待补数",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    cleaned = re.sub(r"\?{4,}", "", cleaned)
    cleaned = cleaned.replace("n/a", "待补数")
    cleaned = re.sub(r"[，。]{2,}", "。", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def strict_quality_gate(
    *,
    management_markdown: str,
    total_pages: int,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    fail_items: list[str] = []
    affected_sections: list[str] = []
    text = management_markdown

    if total_pages > 50:
        fail_items.append("management_report 超过 50 页")
        affected_sections.append("management_report")

    for pattern in BANNED_REPORT_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            fail_items.append(f"management_report 出现内部或调试词：{pattern}")
            affected_sections.append("management_report")

    if not field_registry.get("has_profit_fields", False):
        for phrase in PROFIT_FORBIDDEN_PHRASES:
            if phrase in text:
                fail_items.append(f"缺利润字段时出现禁词：{phrase}")
                affected_sections.append("management_report")
                break

    if not field_registry.get("has_profit_fields", False):
        for row in action_rows:
            action = str(row.get("最终动作") or "")
            if any(term in action for term in ["核心主推", "主推", "资源倾斜", "预算倾斜", "加码", "继续主推"]):
                fail_items.append(f"缺利润字段却出现强资源动作：{row.get('对象名称', 'unknown')}")
                affected_sections.append("action_table")
                break

    if not field_registry.get("has_inventory_fields", False):
        for row in action_rows:
            action = str(row.get("最终动作") or "")
            if any(term in action for term in ["补货", "清仓", "清理退场", "停止补货", "并柜", "移出主推池"]):
                if "待补" not in action and "复核" not in action:
                    fail_items.append(f"缺库存字段却出现库存动作：{row.get('对象名称', 'unknown')}")
                    affected_sections.append("action_table")
                    break

    return {
        "passed": not fail_items,
        "fail_items": fail_items,
        "affected_sections": sorted(set(affected_sections)),
        "suggested_fixes": [] if not fail_items else ["先清理被禁利润/库存表达，再导出正式管理层版本。"],
    }
