from __future__ import annotations

from typing import Any


WAIT_TOKENS = ("待补数据", "无法判断", "不可判断")
TRIAGE_TOKENS = ("当前可判断", "代理判断", "还需补充", "需补充", "待验证", "代理", "hypothesis", "假设")
PROXY_LABEL_TOKENS = ("proxy", "代理", "待验证", "初步")
HYPOTHESIS_LABEL_TOKENS = ("hypothesis", "假设", "待验证", "需要验证")
UNSUPPORTED_LABEL_TOKENS = ("unsupported", "不支持", "缺少", "缺失", "无法", "不可")
PROFIT_ASSERTION_TOKENS = ("毛利", "利润", "毛利率", "ROI", "CAC")
INVENTORY_ASSERTION_TOKENS = ("库存积压", "缺货", "库存周转", "滞销库存", "压货", "清仓")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _metric_rows(payload: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    if not payload:
        return []
    return list(payload.get(key) or [])


def _metric_ids(payload: dict[str, Any] | None) -> set[str]:
    ids: set[str] = set()
    if not payload:
        return ids
    for key in ["direct_metrics", "derived_metrics", "proxy_metrics", "hypothesis_metrics", "unsupported_metrics"]:
        for row in payload.get(key) or []:
            metric_id = _safe_text(row.get("metric_id"))
            metric_name = _safe_text(row.get("metric_name"))
            if metric_id:
                ids.add(metric_id)
            if metric_name:
                ids.add(metric_name)
    registry = payload.get("domain_metric_registry") or {}
    for key in ["direct_metrics", "derived_metrics", "proxy_metrics", "hypothesis_metrics", "unsupported_metrics"]:
        for item in registry.get(key) or []:
            if _safe_text(item):
                ids.add(_safe_text(item))
    return ids


def _extract_action(action_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in action_rows or []:
        normalized.append(
            {
                "priority": _safe_text(
                    row.get("priority")
                    or row.get("优先级")
                    or row.get("浼樺厛绾?")
                ),
                "action": _safe_text(
                    row.get("action")
                    or row.get("最终动作")
                    or row.get("鏈€缁堝姩浣?")
                    or row.get("recommend_action")
                ),
            }
        )
    return normalized


def _is_supplement_action(action: str) -> bool:
    lowered = _safe_text(action)
    return lowered.startswith(("补", "待补", "先补")) or "补字段" in lowered


def _legacy_0__contains_positive_term(markdown: str, token: str) -> bool:
    start = 0
    while True:
        idx = markdown.find(token, start)
        if idx < 0:
            return False
        left = markdown[max(0, idx - 12) : idx]
        if not any(neg in left for neg in ("不", "无", "缺", "待补", "无法", "不可", "禁止", "不能", "需补")):
            return True
        start = idx + len(token)


def _legacy_0__has_boundary_context(markdown: str) -> bool:
    return any(token in markdown for token in ("当前不可判断", "不能判断", "不判断", "缺成本不写", "缺库存不写", "待补后验证", "需补充"))


def _report_reads_metrics(markdown: str, payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False
    candidate_names: list[str] = []
    for key in ["direct_metrics", "derived_metrics", "proxy_metrics"]:
        for row in payload.get(key) or []:
            for value in [row.get("metric_name"), row.get("metric_id")]:
                text = _safe_text(value)
                if text and text not in candidate_names:
                    candidate_names.append(text)
    return any(name and name in markdown for name in candidate_names[:20])


def _family_attempted(metric_ids: set[str], keywords: tuple[str, ...]) -> bool:
    normalized_ids = {_normalize(item) for item in metric_ids}
    return any(any(_normalize(keyword) in metric_id for keyword in keywords) for metric_id in normalized_ids)


def universal_field_blindness_guardrail(
    *,
    business_profile: str,
    management_markdown: str,
    metric_payload: dict[str, Any] | None,
    action_rows: list[dict[str, Any]] | None,
    field_registry: dict[str, Any] | None = None,
    extra_context: dict[str, Any] | None = None,
    require_metric_payload: bool = False,
) -> dict[str, Any]:
    fail_items: list[str] = []
    markdown = _safe_text(management_markdown)
    payload = metric_payload or {}
    field_presence = payload.get("field_presence") or {}
    registry = payload.get("domain_metric_registry") or {}
    metric_ids = _metric_ids(payload)
    extracted_actions = _extract_action(action_rows or [])

    if require_metric_payload and not payload:
        fail_items.append("universal_metric_mining_result.json missing")
    if require_metric_payload and not registry:
        fail_items.append("domain_metric_registry.json missing")
    if payload and not _report_reads_metrics(markdown, payload) and any(token in markdown for token in WAIT_TOKENS):
        fail_items.append("report did not read universal metric mining result before declaring wait-for-data")

    if field_presence.get("has_object_fields") and field_presence.get("has_time_field") and field_presence.get("has_numeric_field"):
        if not _family_attempted(metric_ids, ("trend", "change", "cohort", "dau", "wau", "mau")):
            fail_items.append("object + time + numeric exists but no trend metric attempted")
    if field_presence.get("has_object_fields") and field_presence.get("has_amount_field"):
        if not _family_attempted(metric_ids, ("contribution", "share", "avgordervalue", "客单价")):
            fail_items.append("object + amount exists but no object contribution analysis attempted")
    if field_presence.get("has_object_fields") and field_presence.get("has_quantity_field"):
        if not _family_attempted(metric_ids, ("quantitycontribution", "share", "units", "销量", "结构")):
            fail_items.append("object + quantity exists but no scale/structure analysis attempted")

    if business_profile == "procurement_sales_report":
        procurement_payload = extra_context.get("procurement_metric_payload") if extra_context else {}
        checks = (procurement_payload or {}).get("quality_checks") or {}
        if field_presence.get("has_sku_field") and field_presence.get("has_amount_field") and not checks.get("has_sku_sales_ranking"):
            fail_items.append("SKU + 销售额 exists but SKU sales contribution missing")
        if field_presence.get("has_category_field") and field_presence.get("has_amount_field") and not checks.get("has_category_contribution"):
            fail_items.append("品类 + 销售额 exists but category contribution missing")
        if field_presence.get("has_supplier_field") and field_presence.get("has_amount_field") and not checks.get("has_supplier_contribution"):
            fail_items.append("供应商 + 销售额 exists but supplier contribution missing")
        if field_presence.get("has_amount_field") and field_presence.get("has_cost_field") and not checks.get("has_gross_profit_and_margin"):
            fail_items.append("销售额 + 成本 exists but gross profit/gross margin missing")
        if field_presence.get("has_inventory_field") and field_presence.get("has_quantity_field") and not checks.get("has_inventory_turnover_proxy"):
            fail_items.append("库存 + 销量 exists but sell-through/turnover proxy missing")
        if not field_presence.get("has_cost_field") and any(_contains_positive_term(markdown, token) for token in PROFIT_ASSERTION_TOKENS) and not _has_boundary_context(markdown):
            fail_items.append("no cost field but report asserts profit/ROI/CAC")
        inventory_action_asserted = any(
            any(token in row["action"] for token in INVENTORY_ASSERTION_TOKENS)
            for row in extracted_actions
        )
        if not field_presence.get("has_inventory_field") and (
            inventory_action_asserted
            or any(_contains_positive_term(markdown, token) for token in INVENTORY_ASSERTION_TOKENS)
        ) and not _has_boundary_context(markdown):
            fail_items.append("no inventory field but report asserts stock risk")

    if business_profile == "internet_operations_report":
        if field_presence.get("has_user_field") and field_presence.get("has_time_field"):
            if not _family_attempted(metric_ids, ("dau", "wau", "mau")):
                fail_items.append("user_id + date exists but DAU/WAU/MAU not attempted")
            if not _family_attempted(metric_ids, ("cohort", "retention")):
                fail_items.append("user_id + date exists but cohort retention not attempted")
        if field_presence.get("has_event_field") and field_presence.get("has_user_field"):
            if not _family_attempted(metric_ids, ("funnel", "stage")):
                fail_items.append("event_name + user_id exists but funnel not attempted")
        if field_presence.get("has_content_field"):
            if not _family_attempted(metric_ids, ("content", "interaction")):
                fail_items.append("content_id + interaction exists but content performance not attempted")
        if field_presence.get("has_channel_field") and (field_presence.get("has_user_field") or field_presence.get("has_time_field")):
            if not _family_attempted(metric_ids, ("channel", "contribution")):
                fail_items.append("channel + user_id/date exists but channel contribution not attempted")
        if not field_presence.get("has_cost_field") and any(_contains_positive_term(markdown, token) for token in ("ROI", "CAC")):
            fail_items.append("no cost field but report asserts ROI/CAC")
        if not field_presence.get("has_time_field") and any(_contains_positive_term(markdown, token) for token in ("增长", "下滑", "环比", "同比")):
            fail_items.append("no time field but report asserts growth/downtrend")

    if business_profile == "ecommerce_product_operations_report":
        if (field_presence.get("has_order_field") or _family_attempted(metric_ids, ("order_count", "ordercount", "订单数"))) and field_presence.get("has_amount_field"):
            if not _family_attempted(metric_ids, ("avgordervalue", "客单价", "transaction", "order_count")):
                fail_items.append("order + amount exists but order structure/AOV not attempted")

    if business_profile == "media_campaign_report":
        if field_presence.get("has_campaign_field") and field_presence.get("has_spend_field") and field_presence.get("has_conversion_field"):
            if not _family_attempted(metric_ids, ("cpa", "roas", "ctr", "cpc", "cpm", "efficiency")):
                fail_items.append("campaign + spend + conversion exists but media efficiency not attempted")
        if not field_presence.get("has_conversion_field") and any(_contains_positive_term(markdown, token) for token in ("转化效率", "CPA", "适合加预算")):
            fail_items.append("no conversion field but report asserts conversion efficiency")

    if payload:
        proxy_rows = _metric_rows(payload, "proxy_metrics")
        hypothesis_rows = _metric_rows(payload, "hypothesis_metrics")
        unsupported_rows = _metric_rows(payload, "unsupported_metrics")
        for row in proxy_rows:
            metric_name = _safe_text(row.get("metric_name") or row.get("metric_id"))
            if metric_name and metric_name in markdown and not any(token in markdown for token in PROXY_LABEL_TOKENS):
                fail_items.append(f"proxy metric not labeled as proxy: {metric_name}")
                break
        for row in hypothesis_rows:
            metric_name = _safe_text(row.get("metric_name") or row.get("metric_id"))
            if metric_name and metric_name in markdown and not any(token in markdown for token in HYPOTHESIS_LABEL_TOKENS):
                fail_items.append(f"hypothesis metric not labeled as hypothesis: {metric_name}")
                break
        for row in unsupported_rows:
            metric_name = _safe_text(row.get("metric_name") or row.get("metric_id"))
            if metric_name and metric_name in markdown and not any(token in markdown for token in UNSUPPORTED_LABEL_TOKENS):
                fail_items.append(f"E_UNSUPPORTED metric entered management conclusion: {metric_name}")
                break

    if extracted_actions:
        supplement_count = sum(1 for row in extracted_actions if _is_supplement_action(row["action"]))
        if supplement_count / len(extracted_actions) > 0.5:
            fail_items.append("50%+ actions are supplement-field actions")
        priorities = [row["priority"] for row in extracted_actions if row["priority"]]
        if priorities and all(priority == "P1" for priority in priorities):
            fail_items.append("all action priorities are P1")

    wait_count = sum(markdown.count(token) for token in WAIT_TOKENS)
    if wait_count >= 3 and not any(token in markdown for token in TRIAGE_TOKENS):
        fail_items.append("report overuses wait-for-data language without can-judge/proxy/need-more triage")

    return {
        "passed": not fail_items,
        "fail_items": fail_items,
        "diagnostics": {
            "metric_payload_present": bool(payload),
            "domain_registry_present": bool(registry),
            "report_reads_metric_payload": _report_reads_metrics(markdown, payload) if payload else False,
            "field_presence": field_presence,
            "action_count": len(extracted_actions),
        },
    }


def all_report_quality_gate(
    *,
    base_gate_result: dict[str, Any],
    base_score_result: dict[str, Any] | None,
    business_profile: str,
    management_markdown: str,
    metric_payload: dict[str, Any] | None,
    action_rows: list[dict[str, Any]] | None,
    field_registry: dict[str, Any] | None = None,
    extra_context: dict[str, Any] | None = None,
    require_metric_payload: bool = False,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    guardrail = universal_field_blindness_guardrail(
        business_profile=business_profile,
        management_markdown=management_markdown,
        metric_payload=metric_payload,
        action_rows=action_rows,
        field_registry=field_registry,
        extra_context=extra_context,
        require_metric_payload=require_metric_payload,
    )
    gate_result = dict(base_gate_result or {})
    score_result = dict(base_score_result or {}) if base_score_result is not None else None
    if guardrail["fail_items"]:
        gate_result["passed"] = False
        gate_result["fail_items"] = list(dict.fromkeys([*(gate_result.get("fail_items") or []), *guardrail["fail_items"]]))
        gate_result["affected_sections"] = list(
            dict.fromkeys([*(gate_result.get("affected_sections") or []), "universal_field_blindness_guardrail"])
        )
        gate_result["suggested_fixes"] = list(
            dict.fromkeys(
                [
                    *(gate_result.get("suggested_fixes") or []),
                    "Run universal metric mining first and downgrade conclusions according to evidence level before delivery.",
                ]
            )
        )
        if score_result is not None:
            raw_score = score_result.get("score")
            score_result["score"] = min(int(raw_score or 0), 89)
            score_result["passed"] = False
            score_result["hard_fail_items"] = list(
                dict.fromkeys([*(score_result.get("hard_fail_items") or []), *guardrail["fail_items"]])
            )
    return gate_result, score_result, guardrail


# Keep these clean overrides at the end so legacy mojibake constants above cannot
# make boundary statements look like unsupported positive claims.
WAIT_TOKENS = ("待补数据", "无法判断", "不可判断")
TRIAGE_TOKENS = ("当前可判断", "代理判断", "还需补充", "需补充", "待验证", "代理", "hypothesis", "假设")
PROXY_LABEL_TOKENS = ("proxy", "代理", "待验证", "初步")
HYPOTHESIS_LABEL_TOKENS = ("hypothesis", "假设", "待验证", "需要验证")
UNSUPPORTED_LABEL_TOKENS = ("unsupported", "不支持", "缺少", "缺失", "无法", "不可")
PROFIT_ASSERTION_TOKENS = ("毛利", "利润", "毛利率", "ROI", "CAC")
INVENTORY_ASSERTION_TOKENS = ("库存积压", "缺货", "库存周转", "滞销库存", "压货", "清仓")


def _contains_positive_term(markdown: str, token: str) -> bool:
    start = 0
    negative_left_context = (
        "不",
        "无",
        "缺",
        "待补",
        "无法",
        "不可",
        "禁止",
        "不能",
        "需补",
        "缺少",
        "未提供",
        "unsupported",
        "unavailable",
        "proxy",
        "代理",
        "不是正式",
    )
    negative_right_phrases = (
        "不能判断",
        "不可判断",
        "待补后验证",
        "需补充",
        "不升级为强结论",
        "不能把 FreightCost 误当成完整成本结构",
    )
    while True:
        idx = markdown.find(token, start)
        if idx < 0:
            return False
        left = markdown[max(0, idx - 24) : idx]
        right = markdown[idx : idx + 24]
        if not any(neg in left for neg in negative_left_context) and not any(phrase in right for phrase in negative_right_phrases):
            return True
        start = idx + len(token)


def _has_boundary_context(markdown: str) -> bool:
    return any(
        token in markdown
        for token in (
            "当前不可判断",
            "不能判断",
            "不判断",
            "缺成本不判断",
            "缺库存不判断",
            "缺少采购成本",
            "缺少库存",
            "待补后验证",
            "需补充",
            "不是正式毛利",
            "不能把 FreightCost 误当成完整成本结构",
        )
    )
