from __future__ import annotations

from typing import Any

import pandas as pd

AUTO_BUSINESS_PROFILE = "auto"
GENERIC_BUSINESS_PROFILE = "generic_business_report"
BUSINESS_PROFILE_CONFIDENCE_THRESHOLD = 0.65

LEGACY_PROFILE_ALIASES = {
    "procurement_sales": "procurement_sales_report",
}

# Keep these Chinese routing keywords as plain UTF-8 literals.
# They are matched directly against dataset names, column headers, and business-context text.
# Replacing them with mojibake-like strings will silently break Chinese dataset routing.
ECOMMERCE_PLATFORM_TOKENS: tuple[str, ...] = (
    "taobao",
    "tmall",
    "jd",
    "jingdong",
    "pdd",
    "淘宝",
    "天猫",
    "京东",
    "拼多多",
    "抖店",
    "快手小店",
    "小红书电商",
    "跨境电商",
    "电商",
)

ECOMMERCE_DATASET_HINT_TOKENS: tuple[str, ...] = (
    "商品",
    "店铺",
    "sku",
    "spu",
    "宝贝",
    "卖家",
    "商家",
    "供应商",
)

ECOMMERCE_OBJECT_GRAIN_TOKENS: tuple[str, ...] = (
    "item_id",
    "product_id",
    "sku_id",
    "spu_id",
    "shop_id",
    "seller_id",
    "store_id",
    "brand",
    "vendor",
    "category",
    "商品id",
    "宝贝id",
    "sku",
    "spu",
    "品牌",
    "类目",
    "店铺",
    "卖家",
    "商家",
)

ECOMMERCE_GROUPS: dict[str, list[str]] = {
    "product_fields": [
        "item_id",
        "product_id",
        "spu_id",
        "sku_id",
        "商品id",
        "宝贝id",
        "商品名称",
        "sku",
        "spu",
        "规格",
        "货号",
        "款号",
        "条码",
        "商品标题",
        "product",
        "item",
        "goods",
    ],
    "category_fields": [
        "category",
        "类目",
        "一级类目",
        "二级类目",
        "三级类目",
        "叶子类目",
        "行业",
        "品类",
        "category_id",
    ],
    "shop_fields": [
        "shop_id",
        "seller_id",
        "store_id",
        "店铺",
        "卖家",
        "商家",
        "供应商",
        "品牌",
        "brand",
        "vendor",
        "seller",
        "supplier",
    ],
    "transaction_fields": [
        "order_id",
        "订单",
        "成交",
        "销量",
        "sales_volume",
        "sales",
        "销售额",
        "gmv",
        "支付金额",
        "成交金额",
        "订单量",
        "件数",
        "客单价",
        "转化率",
        "支付转化率",
        "buy_count",
        "buy_rate",
        "order_count",
        "quantity",
        "qty",
        "pay",
    ],
    "price_fields": [
        "price",
        "sale_price",
        "original_price",
        "discount_price",
        "券后价",
        "到手价",
        "售价",
        "原价",
        "优惠",
        "折扣",
    ],
    "fulfillment_after_sales_fields": [
        "发货",
        "物流",
        "签收",
        "履约",
        "退款",
        "退货",
        "售后",
        "投诉",
        "差评",
        "评分",
        "好评率",
        "dsr",
        "店铺评分",
        "fulfillment",
        "delivery",
        "refund",
        "return",
        "review_score",
        "rating",
        "comment",
        "review",
    ],
    "inventory_fields": [
        "inventory",
        "stock",
        "库存",
        "可售库存",
        "在途库存",
        "周转",
        "缺货",
    ],
    "review_fields": [
        "review",
        "comment",
        "评价",
        "评论",
        "追评",
        "问大家",
        "评分",
        "晒图",
        "差评",
        "review_count",
        "rating",
    ],
    "traffic_aux_fields": [
        "曝光",
        "浏览",
        "点击",
        "收藏",
        "加购",
        "搜索",
        "访客",
        "pv",
        "uv",
        "page_views",
        "cart_count",
        "fav_count",
    ],
}

PROCUREMENT_GROUPS: dict[str, list[str]] = {
    "supply_side": [
        "supplier",
        "vendor",
        "seller",
        "供应商",
        "采购",
        "procurement",
        "purchase",
        "purchase_cost",
        "procurement_price",
        "payment_term",
        "账期",
        "rebate",
    ],
    "inventory_profit": [
        "inventory",
        "stock",
        "库存",
        "inventory_days",
        "turnover",
        "gross_margin",
        "gross_profit",
        "profit",
        "毛利",
        "利润",
    ],
    "fulfillment_after_sales": [
        "fulfillment",
        "delivery",
        "review_score",
        "rating",
        "refund",
        "return",
        "售后",
        "履约",
        "差评",
    ],
}

INTERNET_OPS_GROUPS: dict[str, list[str]] = {
    "user_lifecycle": [
        "user_id",
        "uid",
        "visitor_id",
        "device_id",
        "user",
        "dau",
        "wau",
        "mau",
        "active",
        "retention",
        "churn",
        "reactivation",
    ],
    "traffic_engagement": [
        "pv",
        "uv",
        "page_view",
        "view",
        "session",
        "content_id",
        "content",
        "community",
        "interaction",
        "engagement",
        "author_id",
        "like",
        "comment",
        "share",
        "post_id",
        "video_id",
        "article_id",
    ],
    "channel_growth": [
        "channel",
        "campaign",
        "activity",
        "source",
        "utm_source",
        "utm_campaign",
        "acquisition",
    ],
    "conversion_monetization": [
        "conversion",
        "register",
        "login",
        "pay",
        "gmv",
        "revenue",
        "arpu",
        "ltv",
        "cac",
        "roi",
        "roas",
    ],
}

MEDIA_GROUPS: dict[str, list[str]] = {
    "campaign_structure": ["media", "campaign", "adgroup", "ad_group", "creative", "placement", "素材", "广告组", "投放", "媒体"],
    "delivery_scale": ["impression", "impressions", "exposure", "reach", "frequency", "曝光", "投放兑现"],
    "click_efficiency": ["click", "clicks", "ctr", "cpm", "cpc", "cpa", "cost", "spend", "消耗"],
    "conversion_outcome": ["conversion", "convert", "install", "purchase", "lead", "转化"],
}

PROFILE_TO_ENTRYPOINT = {
    "procurement_sales_report": "procurement_sales_report_profile",
    "ecommerce_product_operations_report": "ecommerce_product_operations_report_profile",
    "internet_operations_report": "internet_operations_report_profile",
    "media_campaign_report": "media_campaign_report_profile",
    "generic_business_report": "generic_business_report_profile",
    "generic_long_business_report": "generic_long_business_report_profile",
}

PROFILE_TO_REPORT_LENS = {
    "procurement_sales_report": "procurement_sales_review",
    "ecommerce_product_operations_report": "procurement_sales_review",
    "internet_operations_report": "internet_ops_review",
    "media_campaign_report": "media_review",
    "generic_business_report": "mixed_business_review",
    "generic_long_business_report": "mixed_business_review",
}

DEFAULT_RUNTIME_POLICY: dict[str, Any] = {
    "policy_name": "local_first_default",
    "runtime_first_stages": [],
    "deterministic_stages": [
        "statistical_scope",
        "method_execution",
        "relation_context",
        "analysis_job_graph",
        "rendering",
        "packaging",
    ],
}

RUNTIME_POLICY_BY_PROFILE: dict[str, dict[str, Any]] = {
    "generic_long_business_report": {
        "policy_name": "generic_long_runtime_first",
        "runtime_first_stages": [
            "semantic",
            "background",
            "page_plan",
            "page_generation",
            "final_polish",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
    "internet_operations_report": {
        "policy_name": "internet_ops_runtime_selective",
        "runtime_first_stages": [
            "semantic",
            "metric_interpretation",
            "method_review",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
    "media_campaign_report": {
        "policy_name": "media_campaign_runtime_selective",
        "runtime_first_stages": [
            "semantic",
            "metric_interpretation",
            "decision_summary",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
}

RUNTIME_POLICY_BY_REPORT_LENS: dict[str, dict[str, Any]] = {
    "mixed_business_review": {
        "policy_name": "mixed_business_runtime_selective",
        "runtime_first_stages": [
            "semantic",
            "background",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
    "sales_review": {
        "policy_name": "sales_runtime_selective",
        "runtime_first_stages": [
            "semantic",
            "background",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
    "procurement_sales_review": {
        "policy_name": "procurement_sales_runtime_selective",
        "runtime_first_stages": [
            "semantic",
            "background",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
    "internet_ops_review": {
        "policy_name": "internet_ops_runtime_selective",
        "runtime_first_stages": [
            "semantic",
            "metric_interpretation",
            "method_review",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
    "media_review": {
        "policy_name": "media_campaign_runtime_selective",
        "runtime_first_stages": [
            "semantic",
            "metric_interpretation",
            "decision_summary",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
    "management_accounting_review": {
        "policy_name": "management_accounting_runtime_selective",
        "runtime_first_stages": [
            "background",
            "metric_interpretation",
            "final_polish",
        ],
        "deterministic_stages": list(DEFAULT_RUNTIME_POLICY["deterministic_stages"]),
    },
}

GENERIC_LONG_REQUEST_TOKENS: tuple[str, ...] = (
    "通用经营分析",
    "管理层长报告",
    "厚报告",
    "40-50页报告",
    "35-50页报告",
    "generic long report",
)

GENERIC_LONG_GROUPS: dict[str, list[str]] = {
    "entity_fields": ["项目", "客户", "用户", "机构", "部门", "人员", "地区", "产品", "服务", "任务", "活动", "课程", "供应商", "object_id", "project", "customer", "department", "team", "region"],
    "time_fields": ["date", "month", "quarter", "year", "start", "end", "completed", "周期", "日期", "月份", "季度", "年份", "完成时间"],
    "category_fields": ["type", "category", "tag", "status", "level", "channel", "source", "region", "department", "project_type", "类型", "类别", "标签", "状态", "部门"],
    "volume_fields": ["count", "quantity", "number", "人数", "次数", "件数", "订单数", "任务数", "活动数", "服务次数", "参与人数"],
    "amount_fields": ["amount", "revenue", "cost", "budget", "expense", "price", "金额", "收入", "成本", "预算", "支出", "费用"],
    "progress_fields": ["progress", "completion", "达成率", "完成率", "milestone", "延期", "准时率", "阶段"],
    "quality_fields": ["score", "rating", "satisfaction", "complaint", "problem", "risk", "评分", "满意度", "投诉", "问题数", "风险等级"],
    "conversion_fields": ["register", "submit", "complete", "成交", "续约", "流转", "留存", "复购", "报名", "通过"],
    "people_fields": ["owner", "负责人", "执行人", "team", "岗位", "工时", "绩效", "培训"],
    "geography_fields": ["country", "province", "city", "district", "region", "store", "国家", "省", "市", "区县", "区域", "门店"],
    "text_feedback_fields": ["comment", "feedback", "remark", "note", "问题描述", "建议", "访谈", "评论", "反馈", "备注"],
    "target_fields": ["target", "plan", "budget_target", "kpi", "okr", "目标值", "计划值", "预算值", "KPI", "OKR"],
}


def normalize_business_profile(profile: str | None) -> str:
    normalized = str(profile or AUTO_BUSINESS_PROFILE).strip() or AUTO_BUSINESS_PROFILE
    return LEGACY_PROFILE_ALIASES.get(normalized, normalized)


def business_profile_entrypoint(profile: str | None) -> str:
    normalized = normalize_business_profile(profile)
    return PROFILE_TO_ENTRYPOINT.get(normalized, PROFILE_TO_ENTRYPOINT[GENERIC_BUSINESS_PROFILE])


def business_profile_report_lens(profile: str | None) -> str:
    normalized = normalize_business_profile(profile)
    return PROFILE_TO_REPORT_LENS.get(normalized, PROFILE_TO_REPORT_LENS[GENERIC_BUSINESS_PROFILE])


def runtime_policy_for_report(
    *,
    business_profile: str | None = None,
    report_lens: str | None = None,
) -> dict[str, Any]:
    normalized_profile = normalize_business_profile(business_profile)
    if normalized_profile in RUNTIME_POLICY_BY_PROFILE:
        policy = RUNTIME_POLICY_BY_PROFILE[normalized_profile]
    else:
        normalized_lens = str(report_lens or "").strip()
        policy = RUNTIME_POLICY_BY_REPORT_LENS.get(normalized_lens, DEFAULT_RUNTIME_POLICY)
    return {
        "policy_name": str(policy.get("policy_name") or DEFAULT_RUNTIME_POLICY["policy_name"]),
        "runtime_first_stages": list(policy.get("runtime_first_stages") or []),
        "deterministic_stages": list(policy.get("deterministic_stages") or []),
        "business_profile": normalized_profile,
        "report_lens": str(report_lens or "").strip(),
    }


def runtime_stage_enabled(
    stage_name: str,
    *,
    business_profile: str | None = None,
    report_lens: str | None = None,
) -> bool:
    normalized_stage = str(stage_name or "").strip().lower()
    policy = runtime_policy_for_report(
        business_profile=business_profile,
        report_lens=report_lens,
    )
    stages = {str(item).strip().lower() for item in policy.get("runtime_first_stages") or []}
    return normalized_stage in stages


def _compact(value: str) -> str:
    return "".join(ch for ch in str(value or "").lower().strip() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _column_names(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def _match_group(columns: list[str], aliases: list[str]) -> dict[str, list[str]]:
    compact_columns = {column: _compact(column) for column in columns}
    compact_aliases = {alias: _compact(alias) for alias in aliases}
    matched_columns: list[str] = []
    matched_aliases: list[str] = []
    for column, compact_column in compact_columns.items():
        if not compact_column:
            continue
        for alias, compact_alias in compact_aliases.items():
            if compact_alias and (compact_alias == compact_column or compact_alias in compact_column):
                matched_columns.append(column)
                matched_aliases.append(alias)
                break
    return {
        "matched_columns": list(dict.fromkeys(matched_columns)),
        "matched_aliases": list(dict.fromkeys(matched_aliases)),
    }


def _match_groups(columns: list[str], groups: dict[str, list[str]]) -> dict[str, Any]:
    matched_groups: list[str] = []
    matched_columns: list[str] = []
    matched_aliases: list[str] = []
    missing_groups: list[str] = []
    group_details: dict[str, dict[str, list[str]]] = {}
    for group_name, aliases in groups.items():
        detail = _match_group(columns, aliases)
        group_details[group_name] = detail
        if detail["matched_columns"]:
            matched_groups.append(group_name)
            matched_columns.extend(detail["matched_columns"])
            matched_aliases.extend(detail["matched_aliases"])
        else:
            missing_groups.append(group_name)
    matched_columns = list(dict.fromkeys(matched_columns))
    matched_aliases = list(dict.fromkeys(matched_aliases))
    confidence = round(
        min(
            1.0,
            (len(matched_groups) / max(len(groups), 1)) * 0.75
            + (min(len(matched_aliases), 10) / 10) * 0.25,
        ),
        4,
    )
    return {
        "matched_groups": matched_groups,
        "matched_columns": matched_columns,
        "matched_aliases": matched_aliases,
        "missing_core_fields": missing_groups,
        "group_details": group_details,
        "confidence": confidence,
    }


def _dataset_hint_text(dataset_name: str, request_text: str, columns: list[str]) -> str:
    return " ".join([dataset_name, request_text, *columns]).lower()


def _contains_tokens(text: str, tokens: tuple[str, ...] | list[str]) -> bool:
    compact_text = _compact(text)
    return any(_compact(token) in compact_text for token in tokens)


def _decisive_object_grain(columns: list[str]) -> str:
    grains: list[str] = []
    compact_columns = [_compact(column) for column in columns]
    if any(token in compact_columns for token in ["itemid", "productid", "商品id", "宝贝id"]):
        grains.append("商品")
    if any(token in compact_columns for token in ["skuid", "spuid", "sku", "spu"]):
        grains.append("SKU/SPU")
    if any(token in compact_columns for token in ["shopid", "sellerid", "storeid", "店铺", "卖家", "商家"]):
        grains.append("店铺")
    if any(token in compact_columns for token in ["brand", "vendor", "品牌", "供应商"]):
        grains.append("品牌/卖家")
    if any(token in compact_columns for token in ["category", "categoryid", "类目", "品类"]):
        grains.append("类目")
    return "/".join(grains) if grains else "对象粒度未定"


def _secondary_profile(primary_profile: str, scores: dict[str, dict[str, Any]]) -> str:
    candidates = []
    for profile in ["internet_operations_report", "media_campaign_report", "procurement_sales_report", "ecommerce_product_operations_report"]:
        if profile == primary_profile:
            continue
        detail = scores.get(profile) or {}
        candidates.append((detail.get("confidence", 0.0), profile))
    candidates.sort(reverse=True)
    return candidates[0][1] if candidates and candidates[0][0] >= 0.35 else ""


def route_business_profile(
    frame: pd.DataFrame,
    *,
    dataset_name: str = "",
    request_text: str = "",
    requested_business_profile: str | None = AUTO_BUSINESS_PROFILE,
) -> dict[str, Any]:
    normalized_requested = normalize_business_profile(requested_business_profile)
    columns = _column_names(frame)
    hint_text = _dataset_hint_text(dataset_name, request_text, columns)

    ecommerce_detail = _match_groups(columns, ECOMMERCE_GROUPS)
    procurement_detail = _match_groups(columns, PROCUREMENT_GROUPS)
    internet_ops_detail = _match_groups(columns, INTERNET_OPS_GROUPS)
    media_detail = _match_groups(columns, MEDIA_GROUPS)

    scores = {
        "ecommerce_product_operations_report": ecommerce_detail,
        "procurement_sales_report": procurement_detail,
        "internet_operations_report": internet_ops_detail,
        "media_campaign_report": media_detail,
    }

    decisive_field_groups = list(ecommerce_detail["matched_groups"])
    decisive_object_grain = _decisive_object_grain(columns)
    platform_hint = _contains_tokens(hint_text, ECOMMERCE_PLATFORM_TOKENS)
    ecommerce_name_hint = _contains_tokens(hint_text, ECOMMERCE_DATASET_HINT_TOKENS)

    ecommerce_groups = set(ecommerce_detail["matched_groups"])
    has_product = "product_fields" in ecommerce_groups
    has_category = "category_fields" in ecommerce_groups
    has_shop = "shop_fields" in ecommerce_groups
    has_transaction = "transaction_fields" in ecommerce_groups
    has_price = "price_fields" in ecommerce_groups
    has_fulfillment = "fulfillment_after_sales_fields" in ecommerce_groups
    has_inventory = "inventory_fields" in ecommerce_groups
    has_review = "review_fields" in ecommerce_groups
    has_object_grain = decisive_object_grain != "对象粒度未定"
    has_ecommerce_object_grain = _contains_tokens(" ".join(columns), ECOMMERCE_OBJECT_GRAIN_TOKENS)

    ecommerce_priority_hit = False
    internet_ops_priority_hit = False
    ambiguity_warning = ""
    routing_reason = ""

    if has_product and sum(1 for flag in [has_transaction, has_price, has_review, has_inventory, has_shop] if flag) >= 2:
        ecommerce_priority_hit = True
        routing_reason = "强制规则命中：商品字段同时携带交易、价格、评价、库存、店铺信号中的至少两组，必须进入 ecommerce_product_operations_report 主链。"
    if has_product and sum(1 for flag in [has_category, has_shop, has_transaction, has_price, has_fulfillment, has_inventory] if flag) >= 1:
        ecommerce_priority_hit = True
        routing_reason = "强商品经营信号成立：商品字段与类目/店铺/交易/价格/履约/库存字段至少形成两组核心组合，应优先进入电商商品经营链。"
    if has_product and has_transaction and has_review:
        ecommerce_priority_hit = True
        routing_reason = "商品字段 + 交易字段 + 评价字段同时出现，评价应视为商品口碑/售后指标，禁止推到互联网运营主链。"
    if has_product and has_shop and has_transaction:
        ecommerce_priority_hit = True
        routing_reason = "商品字段 + 店铺/卖家字段 + 交易字段同时出现，核心对象已经是商品经营对象，应进入电商经营复盘链。"
    if (platform_hint or ecommerce_name_hint) and has_object_grain and sum(1 for flag in [has_transaction, has_price, has_inventory, has_review, has_fulfillment] if flag) >= 1:
        ecommerce_priority_hit = True
        routing_reason = "数据集名称/字段明确指向电商平台，且核心对象粒度为商品/店铺/SKU，流量与评价字段只能作为商品经营辅助指标。"
    if has_ecommerce_object_grain and sum(1 for flag in [has_transaction, has_price, has_review, has_inventory, has_fulfillment] if flag) >= 2:
        ecommerce_priority_hit = True
        routing_reason = "对象粒度优先命中：当前主对象包含 item/product/sku/spu/shop/seller/brand/category，并已携带交易、价格、评价、库存或售后中的至少两类字段，不得误判为 internet_operations_report。"
    if has_review and has_object_grain and any(group in ecommerce_groups for group in ["product_fields", "shop_fields"]):
        ambiguity_warning = "评价/评论字段已与商品或店铺粒度绑定，本轮按商品口碑/售后评价处理，不按社区评论处理。"
    if has_product and any(group in ecommerce_groups for group in ["traffic_aux_fields", "review_fields"]):
        ambiguity_warning = (
            ambiguity_warning
            or "PV/UV/点击/收藏/加购/评价等字段当前只作为商品经营辅助指标，不改变主业务类型。"
        )

    content_community_signal = any(
        _compact(token) in _compact(" ".join(columns))
        for token in ["content_id", "author_id", "view", "like", "comment", "share", "post_id", "video_id", "article_id"]
    )
    if (
        not ecommerce_priority_hit
        and not has_ecommerce_object_grain
        and "user_lifecycle" in internet_ops_detail["matched_groups"]
        and "traffic_engagement" in internet_ops_detail["matched_groups"]
        and (content_community_signal or "retention" in _compact(" ".join(columns)))
    ):
        internet_ops_priority_hit = True

    final_profile = GENERIC_BUSINESS_PROFILE
    primary_detail = {
        "matched_groups": [],
        "matched_columns": [],
        "matched_aliases": [],
        "missing_core_fields": [],
        "confidence": 0.0,
    }

    if ecommerce_priority_hit:
        procurement_strength = sum(
            1
            for flag in [
                "supply_side" in procurement_detail["matched_groups"],
                "inventory_profit" in procurement_detail["matched_groups"],
                "fulfillment_after_sales" in procurement_detail["matched_groups"],
            ]
            if flag
        )
        if procurement_strength >= 2 and ("shop_fields" in ecommerce_groups or "fulfillment_after_sales_fields" in ecommerce_groups):
            final_profile = "procurement_sales_report"
            primary_detail = procurement_detail
            primary_detail = {**primary_detail, "confidence": max(float(primary_detail.get("confidence", 0.0)), 0.72)}
        else:
            final_profile = "ecommerce_product_operations_report"
            primary_detail = ecommerce_detail
        if not routing_reason:
            routing_reason = "电商商品经营信号优先，主链切到商品经营/采销复盘。"
    elif internet_ops_priority_hit:
        final_profile = "internet_operations_report"
        primary_detail = internet_ops_detail
        routing_reason = "主要对象是用户/内容/互动/留存链路，评论字段与内容对象绑定，按互联网运营主链处理。"
    else:
        ranked_profiles = sorted(
            scores.items(),
            key=lambda item: (item[1]["confidence"], len(item[1]["matched_aliases"])),
            reverse=True,
        )
        top_profile, top_detail = ranked_profiles[0] if ranked_profiles else (GENERIC_BUSINESS_PROFILE, primary_detail)
        if top_detail["confidence"] >= BUSINESS_PROFILE_CONFIDENCE_THRESHOLD:
            final_profile = top_profile
            primary_detail = top_detail
        else:
            final_profile = GENERIC_BUSINESS_PROFILE
            primary_detail = top_detail
            routing_reason = (
                f"best matched profile `{top_profile}` only reached confidence {top_detail['confidence']:.2f}; "
                "route downgraded to generic_business_report to avoid forcing a specialized template"
            )
        if not routing_reason and final_profile != GENERIC_BUSINESS_PROFILE:
            routing_reason = (
                f"matched {len(primary_detail['matched_groups'])} core field groups and "
                f"{len(primary_detail['matched_aliases'])} field signals for `{final_profile}`"
            )

    generic_detail = _match_groups(columns, GENERIC_LONG_GROUPS)
    generic_long_requested = _contains_tokens(f"{dataset_name} {request_text}", GENERIC_LONG_REQUEST_TOKENS)
    if final_profile == GENERIC_BUSINESS_PROFILE and (generic_long_requested or generic_detail["confidence"] >= 0.45):
        final_profile = "generic_long_business_report"
        primary_detail = generic_detail
        routing_reason = (
            "当前数据未稳定命中采销、电商、互联网运营或媒体投放主链；"
            "字段更适合进入通用经营分析长报告，并通过多轮解释链生成管理层厚报告。"
        )

    secondary_profile = _secondary_profile(final_profile, scores)
    if final_profile == "ecommerce_product_operations_report" and not secondary_profile:
        secondary_profile = "internet_operations_report" if internet_ops_detail["confidence"] >= 0.25 else ""

    rejected_profiles: list[dict[str, Any]] = []
    for profile, detail in scores.items():
        if profile == final_profile:
            continue
        reason = "matched signals weaker than the selected profile"
        if final_profile == "ecommerce_product_operations_report" and profile == "internet_operations_report":
            reason = "traffic/review fields are present, but object grain is product/shop/SKU and must stay in ecommerce chain"
        if final_profile == "procurement_sales_report" and profile == "internet_operations_report":
            reason = "supply/inventory/profit chain is stronger than generic internet-ops signals"
        rejected_profiles.append(
            {
                "business_profile": profile,
                "matched_groups": detail["matched_groups"],
                "missing_core_fields": detail["missing_core_fields"],
                "reason": reason,
            }
        )
    if normalized_requested not in {AUTO_BUSINESS_PROFILE, final_profile}:
        rejected_profiles.insert(
            0,
            {
                "business_profile": normalized_requested,
                "matched_groups": scores.get(normalized_requested, {}).get("matched_groups", []),
                "missing_core_fields": scores.get(normalized_requested, {}).get("missing_core_fields", []),
                "reason": "requested profile conflicts with routed dataset signals",
            },
        )

    if final_profile == "ecommerce_product_operations_report" and not ambiguity_warning and internet_ops_detail["confidence"] >= 0.35:
        ambiguity_warning = "数据同时带有浏览/点击/评价等信号，但当前只把它们视为商品经营辅助指标，不改主业务类型。"

    if final_profile == "ecommerce_product_operations_report":
        primary_detail = ecommerce_detail
        decisive_field_groups = ecommerce_detail["matched_groups"]
        if not routing_reason:
            routing_reason = "数据虽然包含评价和流量字段，但核心对象粒度为商品/店铺/SKU，且存在交易、价格、评价字段，应进入商品经营/采销复盘链。"
    elif final_profile == "procurement_sales_report":
        decisive_field_groups = list(dict.fromkeys(ecommerce_detail["matched_groups"] + procurement_detail["matched_groups"]))
    elif final_profile == "internet_operations_report":
        decisive_field_groups = internet_ops_detail["matched_groups"]
    elif final_profile == "media_campaign_report":
        decisive_field_groups = media_detail["matched_groups"]

    return {
        "business_profile": final_profile,
        "secondary_profile": secondary_profile,
        "confidence": primary_detail.get("confidence", 0.0),
        "matched_field_signals": {
            "matched_groups": primary_detail.get("matched_groups", []),
            "matched_columns": primary_detail.get("matched_columns", []),
            "matched_aliases": primary_detail.get("matched_aliases", []),
        },
        "matched_ecommerce_signals": {
            "matched_groups": ecommerce_detail["matched_groups"],
            "matched_columns": ecommerce_detail["matched_columns"],
            "matched_aliases": ecommerce_detail["matched_aliases"],
        },
        "matched_internet_ops_signals": {
            "matched_groups": internet_ops_detail["matched_groups"],
            "matched_columns": internet_ops_detail["matched_columns"],
            "matched_aliases": internet_ops_detail["matched_aliases"],
        },
        "matched_media_signals": {
            "matched_groups": media_detail["matched_groups"],
            "matched_columns": media_detail["matched_columns"],
            "matched_aliases": media_detail["matched_aliases"],
        },
        "decisive_object_grain": decisive_object_grain,
        "decisive_field_groups": decisive_field_groups,
        "missing_core_fields": primary_detail.get("missing_core_fields", []),
        "rejected_profiles": rejected_profiles,
        "routing_reason": routing_reason,
        "ambiguity_warning": ambiguity_warning,
        "requested_business_profile": normalized_requested,
        "profile_entrypoint": business_profile_entrypoint(final_profile),
        "report_lens": business_profile_report_lens(final_profile),
        "dataset_name": dataset_name,
        "request_text": request_text[:1000],
    }
