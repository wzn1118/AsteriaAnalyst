from __future__ import annotations

from typing import Any

import pandas as pd


INTERNET_OPS_SIGNAL_MAP: dict[str, list[str]] = {
    "traffic_fields": [
        "impressions",
        "clicks",
        "traffic_source",
        "曝光",
        "访问",
        "pv",
        "uv",
        "点击",
        "session",
        "sessions",
        "source",
        "organic",
        "paid",
        "traffic",
        "visit",
    ],
    "user_fields": [
        "registrations",
        "activations",
        "paid_users",
        "user_segment",
        "city_tier",
        "user_id",
        "uid",
        "visitor_id",
        "device_id",
        "new_user",
        "active_user",
        "register_user",
        "login_user",
        "pay_user",
        "churn_user",
        "reactivated_user",
        "新用户",
        "活跃用户",
        "注册用户",
        "登录用户",
        "付费用户",
        "流失用户",
        "回流用户",
    ],
    "funnel_fields": [
        "impressions",
        "clicks",
        "registrations",
        "activations",
        "paid_users",
        "impression",
        "visit",
        "click",
        "register",
        "login",
        "activation",
        "add_to_cart",
        "purchase",
        "pay",
        "conversion",
        "转化率",
        "注册率",
        "激活率",
        "下单率",
        "支付率",
    ],
    "retention_fields": [
        "retention_d7",
        "nps",
        "retention",
        "d1",
        "d3",
        "d7",
        "d14",
        "d30",
        "cohort",
        "复访",
        "回访",
        "留存率",
        "流失率",
    ],
    "engagement_fields": [
        "like",
        "comment",
        "share",
        "collect",
        "follow",
        "post",
        "publish",
        "watch_time",
        "duration",
        "stay_time",
        "互动",
        "点赞",
        "评论",
        "转发",
        "收藏",
        "关注",
        "停留时长",
        "完播率",
    ],
    "content_fields": [
        "content_category",
        "product_module",
        "content_id",
        "post_id",
        "article_id",
        "video_id",
        "content",
        "主题",
        "内容",
        "内容主题",
        "素材",
        "文章",
        "视频",
        "笔记",
        "title",
        "topic",
        "tag",
        "category",
        "creator",
        "author",
        "内容类型",
        "发布时间",
    ],
    "channel_fields": [
        "channel",
        "traffic_source",
        "channel",
        "source",
        "渠道",
        "来源",
        "source_name",
        "campaign",
        "utm_source",
        "utm_campaign",
        "media",
        "ad_group",
        "creative",
        "kol",
        "达人",
        "自然流量",
        "付费流量",
    ],
    "cost_fields": [
        "operating_cost",
        "cac",
        "CPC",
        "CPM",
        "cost",
        "spend",
        "budget",
        "cpc",
        "cpm",
        "cpa",
        "cac",
        "消耗",
        "预算",
        "获客成本",
    ],
    "revenue_fields": [
        "revenue",
        "contribution_margin",
        "paid_users",
        "roi",
        "ROI",
        "gmv",
        "revenue",
        "arpu",
        "arppu",
        "ltv",
        "roi",
        "roas",
        "付费金额",
        "客单价",
        "订单数",
    ],
    "campaign_fields": [
        "campaign",
        "content_category",
        "product_module",
        "activity",
        "活动",
        "活动名称",
        "campaign",
        "campaign_name",
        "event",
        "activity_id",
        "event_name",
        "campaign_name",
        "参与人数",
        "报名人数",
        "核销人数",
        "优惠券",
        "任务完成",
        "活动转化",
    ],
    "quality_fields": [
        "contribution_margin",
        "roi",
        "cac",
        "retention_d7",
        "nps",
        "退款",
        "投诉",
        "差评",
        "举报",
        "跳出率",
        "卸载",
        "流失",
        "客服问题",
        "异常流量",
    ],
    "segment_fields": [
        "user_segment",
        "city_tier",
        "地域",
        "年龄",
        "性别",
        "设备",
        "会员等级",
        "用户生命周期",
        "用户标签",
        "版本",
    ],
}

ALL_INTERNET_OPS_ANALYSIS_MODULES = [
    "traffic_overview",
    "user_scale_review",
    "growth_funnel_review",
    "retention_review",
    "engagement_review",
    "content_operations",
    "channel_operations",
    "cost_efficiency_review",
    "revenue_quality_review",
    "campaign_review",
    "quality_risk_review",
    "segment_analysis",
]

INTERNET_OPS_FORBIDDEN_TERMS_BY_FIELD = {
    "cost_fields": ["ROI", "CAC合理", "预算加码", "渠道加码", "砍渠道"],
    "retention_fields": ["长期留存好", "用户质量高", "用户黏性强"],
    "revenue_fields": ["商业价值高", "LTV高", "付费潜力已验证"],
}

INTERNET_OPS_INFERENCE_LEVEL_A = "evidence_based_decision"
INTERNET_OPS_INFERENCE_LEVEL_B = "proxy_based_inference"
INTERNET_OPS_INFERENCE_LEVEL_C = "business_hypothesis"
INTERNET_OPS_INFERENCE_LEVEL_D = "risk_flag"
INTERNET_OPS_INFERENCE_LEVEL_E = "data_required"

INTERNET_OPS_COST_BLOCKED_ACTIONS = {
    "加大投放",
    "砍掉渠道",
    "预算倾斜",
    "ROI最高",
    "投放效率最好",
    "低成本获客",
    "扩大买量",
    "CAC合理",
    "渠道加码",
}

INTERNET_OPS_RETENTION_BLOCKED_ACTIONS = {
    "用户质量高",
    "长期留存好",
    "长期价值高",
    "用户黏性强",
    "可以扩大拉新",
}

INTERNET_OPS_REVENUE_BLOCKED_ACTIONS = {
    "商业化效率高",
    "LTV高",
    "ROI高",
    "值得加码",
    "高价值用户",
    "付费潜力已验证",
}

INTERNET_OPS_FUNNEL_BLOCKED_ACTIONS = {
    "转化链路健康",
    "注册转化好",
    "支付转化好",
    "漏斗效率高",
}

INTERNET_OPS_CHANNEL_BLOCKED_ACTIONS = {
    "某渠道质量最好",
    "某渠道应加码",
    "某渠道应砍掉",
}

INTERNET_OPS_CONTENT_BLOCKED_ACTIONS = {
    "某类内容值得主推",
    "某作者表现最好",
    "内容策略有效",
}

INTERNET_OPS_LOW_SAMPLE_BLOCKED_ACTIONS = {
    "加码",
    "主推",
    "砍掉",
    "放量",
    "扩大投放",
    "扩大买量",
}

INTERNET_OPS_SOFT_ACTIONS = {
    "渠道流量质量候选",
    "待补成本后判断投放效率",
    "先观察转化质量",
    "补充消耗/CPC/CPA/CAC后复核",
    "短期活跃表现较好、留存字段缺失，需补 D1/D7/D30 后判断用户质量",
    "转化行为较强、收入字段缺失，需补付费/GMV/ARPU/LTV后判断商业价值",
    "当前只能判断单点行为，不能判断完整漏斗效率",
    "来源字段缺失，不能归因到渠道",
    "内容维度不足，只能判断整体互动表现",
    "低样本观察",
    "低样本复核",
    "补字段验证",
    "小流量测试",
    "差评归因",
    "履约链路拆分",
    "供应商观察",
    "替代供应商预研",
}


def _compact(value: str) -> str:
    return "".join(ch for ch in str(value).lower().strip() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _column_names(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def _matched_columns(columns: list[str], aliases: list[str]) -> tuple[list[str], list[str]]:
    matched_columns: list[str] = []
    matched_aliases: list[str] = []
    compact_columns = {column: _compact(column) for column in columns}
    compact_aliases = {alias: _compact(alias) for alias in aliases}
    for column, compact_column in compact_columns.items():
        if not compact_column:
            continue
        for alias, compact_alias in compact_aliases.items():
            if compact_alias and (compact_alias == compact_column or compact_alias in compact_column):
                matched_columns.append(column)
                matched_aliases.append(alias)
                break
    return list(dict.fromkeys(matched_columns)), list(dict.fromkeys(matched_aliases))


def _supported_modules(registry: dict[str, Any]) -> list[str]:
    supported: list[str] = []
    if registry["has_traffic_fields"]:
        supported.append("traffic_overview")
    if registry["has_user_fields"]:
        supported.append("user_scale_review")
    if registry["has_funnel_fields"]:
        supported.append("growth_funnel_review")
    if registry["has_retention_fields"]:
        supported.append("retention_review")
    if registry["has_engagement_fields"]:
        supported.append("engagement_review")
    if registry["has_content_fields"]:
        supported.append("content_operations")
    if registry["has_channel_fields"]:
        supported.append("channel_operations")
    if registry["has_cost_fields"]:
        supported.append("cost_efficiency_review")
    if registry["has_revenue_fields"]:
        supported.append("revenue_quality_review")
    if registry["has_campaign_fields"]:
        supported.append("campaign_review")
    if registry["has_quality_fields"]:
        supported.append("quality_risk_review")
    if registry["has_segment_fields"]:
        supported.append("segment_analysis")
    return supported


def _report_mode(registry: dict[str, Any]) -> str:
    if (
        registry["has_traffic_fields"]
        and registry["has_user_fields"]
        and registry["has_funnel_fields"]
        and registry["has_retention_fields"]
        and registry["has_engagement_fields"]
        and registry["has_content_fields"]
        and registry["has_channel_fields"]
        and registry["has_cost_fields"]
        and registry["has_revenue_fields"]
    ):
        return "full_internet_operations_report"
    if registry["has_user_fields"] and registry["has_funnel_fields"] and (registry["has_traffic_fields"] or registry["has_channel_fields"]):
        return "growth_funnel_report"
    if registry["has_content_fields"] and registry["has_engagement_fields"] and (registry["has_traffic_fields"] or registry["has_user_fields"]):
        return "content_operations_report"
    if registry["has_engagement_fields"] and registry["has_user_fields"] and (registry["has_content_fields"] or registry["has_quality_fields"]):
        return "community_operations_report"
    if registry["has_channel_fields"] and (registry["has_traffic_fields"] or registry["has_funnel_fields"]) and (registry["has_cost_fields"] or registry["has_revenue_fields"]):
        return "channel_operations_report"
    if registry["has_traffic_fields"] and registry["has_user_fields"] and (registry["has_funnel_fields"] or registry["has_retention_fields"]):
        return "app_website_operations_report"
    return "insufficient_for_operations_decision"


def internet_ops_field_availability_registry(frame: pd.DataFrame) -> dict[str, Any]:
    columns = _column_names(frame)
    matched_groups: dict[str, dict[str, list[str]]] = {}
    registry: dict[str, Any] = {"business_profile": "internet_operations_report"}
    for group_name, aliases in INTERNET_OPS_SIGNAL_MAP.items():
        matched_columns, matched_aliases = _matched_columns(columns, aliases)
        matched_groups[group_name] = {
            "matched_columns": matched_columns,
            "matched_aliases": matched_aliases,
        }
        registry[f"has_{group_name}"] = bool(matched_columns)

    available_field_groups = [group for group in INTERNET_OPS_SIGNAL_MAP if registry[f"has_{group}"]]
    missing_field_groups = [group for group in INTERNET_OPS_SIGNAL_MAP if not registry[f"has_{group}"]]
    registry["available_field_groups"] = available_field_groups
    registry["missing_field_groups"] = missing_field_groups
    registry["matched_field_signals"] = matched_groups
    registry["report_mode"] = _report_mode(registry)
    registry["supported_analysis_modules"] = _supported_modules(registry)
    registry["unsupported_analysis_modules"] = [
        module for module in ALL_INTERNET_OPS_ANALYSIS_MODULES if module not in registry["supported_analysis_modules"]
    ]
    return registry


def internet_ops_forbidden_terms(field_registry: dict[str, Any]) -> list[str]:
    forbidden_terms: list[str] = []
    if not field_registry.get("has_cost_fields", False):
        forbidden_terms.extend(INTERNET_OPS_FORBIDDEN_TERMS_BY_FIELD["cost_fields"])
    if not field_registry.get("has_retention_fields", False):
        forbidden_terms.extend(INTERNET_OPS_FORBIDDEN_TERMS_BY_FIELD["retention_fields"])
    if not field_registry.get("has_revenue_fields", False):
        forbidden_terms.extend(INTERNET_OPS_FORBIDDEN_TERMS_BY_FIELD["revenue_fields"])
    return forbidden_terms


def internet_ops_text_compliance_failures(text: str, field_registry: dict[str, Any]) -> list[str]:
    content = str(text or "")
    failures: list[str] = []
    for term in internet_ops_forbidden_terms(field_registry):
        if term in content:
            failures.append(term)
    return failures


def _internet_ops_required_groups(candidate_text: str) -> list[str]:
    text = str(candidate_text or "").strip()
    required: list[str] = []
    if text in INTERNET_OPS_COST_BLOCKED_ACTIONS or any(token in text for token in ["投放", "预算", "买量", "CAC", "ROI"]):
        required.append("cost_fields")
    if text in INTERNET_OPS_RETENTION_BLOCKED_ACTIONS or any(token in text for token in ["留存", "黏性", "长期价值", "拉新"]):
        required.append("retention_fields")
    if text in INTERNET_OPS_REVENUE_BLOCKED_ACTIONS or any(token in text for token in ["商业化", "LTV", "付费", "商业价值", "高价值用户", "ROI高"]):
        required.append("revenue_fields")
    if text in INTERNET_OPS_FUNNEL_BLOCKED_ACTIONS or any(token in text for token in ["转化链路", "漏斗", "注册转化", "支付转化"]):
        required.append("funnel_fields")
    if text in INTERNET_OPS_CHANNEL_BLOCKED_ACTIONS or any(token in text for token in ["渠道"]):
        required.append("channel_fields")
    if text in INTERNET_OPS_CONTENT_BLOCKED_ACTIONS or any(token in text for token in ["内容", "作者", "主推"]):
        required.append("content_fields")
    return list(dict.fromkeys(required))


def _group_available(registry: dict[str, Any], group_name: str) -> bool:
    return bool(registry.get(f"has_{group_name}", False))


def _owner_role_for_object_level(object_level: str) -> str:
    normalized = str(object_level or "").lower()
    if normalized in {"channel", "source"}:
        return "渠道运营 + 数据分析"
    if normalized in {"content", "creator", "author"}:
        return "内容运营 + 数据分析"
    if normalized in {"campaign", "activity"}:
        return "活动运营 + 数据分析"
    if normalized in {"funnel", "growth"}:
        return "增长运营 + 数据分析"
    if normalized in {"segment", "user", "user_segment"}:
        return "用户运营 + 数据分析"
    return "运营负责人 + 数据分析"


def _validation_payload(missing_fields: list[str]) -> tuple[str, str]:
    metrics: list[str] = []
    actions: list[str] = []
    if "referral_fields" in missing_fields:
        metrics.extend(["invite/referral/share"])
        actions.append("Referral 单独补齐后复核裂变贡献")
    if "cost_fields" in missing_fields:
        metrics.extend(["消耗", "CPC", "CPA", "CAC"])
        actions.append("补充消耗/CPC/CPA/CAC后复核")
    if "retention_fields" in missing_fields:
        metrics.extend(["D1留存率", "D7留存率", "D30留存率"])
        actions.append("补 D1/D7/D30 后判断用户质量")
    if "revenue_fields" in missing_fields:
        metrics.extend(["付费金额", "GMV", "ARPU", "LTV"])
        actions.append("补付费/GMV/ARPU/LTV后判断商业价值")
    if "funnel_fields" in missing_fields:
        metrics.extend(["注册率", "激活率", "支付率"])
        actions.append("补关键漏斗事件后复核转化链路")
    if "channel_fields" in missing_fields:
        metrics.extend(["渠道来源", "渠道转化率", "渠道流量质量"])
        actions.append("补来源字段后做渠道归因")
    if "content_fields" in missing_fields:
        metrics.extend(["互动率", "完播率", "内容转化率"])
        actions.append("补内容维度后复核内容效果")
    if not metrics:
        metrics.extend(["roi", "cac", "CTR", "retention_d7", "nps", "paid_users", "contribution_margin"])
        actions.append("按现有 KPI 进入经营动作复核")
    return " / ".join(dict.fromkeys(actions)), " / ".join(dict.fromkeys(metrics))


def internet_ops_inference_controller(
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
    user_count = int(sample_size.get("user_count") or 0)
    event_count = int(sample_size.get("event_count") or 0)
    required_groups = _internet_ops_required_groups(candidate_action) or _internet_ops_required_groups(candidate_label)
    missing_fields = [group for group in required_groups if not _group_available(field_availability_registry, group)]
    evidence_items = [
        f"{key}={value}"
        for key, value in evidence.items()
        if value not in (None, "", [], {})
    ][:5]
    proxy_evidence = " / ".join(evidence_items) if evidence_items else "当前只有局部行为证据"
    forbidden_actions: list[str] = []
    confidence_level = "high"
    conclusion_type = INTERNET_OPS_INFERENCE_LEVEL_A
    conclusion = candidate_action

    if user_count < 100 or event_count < 500:
        conclusion_type = INTERNET_OPS_INFERENCE_LEVEL_D
        confidence_level = "low"
        conclusion = "低样本观察" if user_count < 100 and event_count < 500 else "低样本复核"
        forbidden_actions = sorted(INTERNET_OPS_LOW_SAMPLE_BLOCKED_ACTIONS)
    elif missing_fields:
        confidence_level = "medium" if evidence_items else "low"
        if evidence_items:
            conclusion_type = INTERNET_OPS_INFERENCE_LEVEL_B
        else:
            conclusion_type = INTERNET_OPS_INFERENCE_LEVEL_E
        if any(group in missing_fields for group in ["cost_fields", "revenue_fields", "retention_fields", "funnel_fields", "channel_fields", "content_fields"]):
            if "cost_fields" in missing_fields:
                forbidden_actions.extend(sorted(INTERNET_OPS_COST_BLOCKED_ACTIONS))
                conclusion = "待补成本后判断投放效率"
            elif "retention_fields" in missing_fields:
                forbidden_actions.extend(sorted(INTERNET_OPS_RETENTION_BLOCKED_ACTIONS))
                conclusion = "短期活跃表现较好、留存字段缺失，需补 D1/D7/D30 后判断用户质量"
            elif "revenue_fields" in missing_fields:
                forbidden_actions.extend(sorted(INTERNET_OPS_REVENUE_BLOCKED_ACTIONS))
                conclusion = "转化行为较强、收入字段缺失，需补付费/GMV/ARPU/LTV后判断商业价值"
            elif "funnel_fields" in missing_fields:
                forbidden_actions.extend(sorted(INTERNET_OPS_FUNNEL_BLOCKED_ACTIONS))
                conclusion = "当前只能判断单点行为，不能判断完整漏斗效率"
            elif "channel_fields" in missing_fields:
                forbidden_actions.extend(sorted(INTERNET_OPS_CHANNEL_BLOCKED_ACTIONS))
                conclusion = "来源字段缺失，不能归因到渠道"
            elif "content_fields" in missing_fields:
                forbidden_actions.extend(sorted(INTERNET_OPS_CONTENT_BLOCKED_ACTIONS))
                conclusion = "内容维度不足，只能判断整体互动表现"
        if not evidence_items and conclusion_type == INTERNET_OPS_INFERENCE_LEVEL_B:
            conclusion_type = INTERNET_OPS_INFERENCE_LEVEL_C
            confidence_level = "low"

    recommended_validation_action, validation_metric = _validation_payload(missing_fields)
    if conclusion_type == INTERNET_OPS_INFERENCE_LEVEL_A:
        recommended_validation_action = recommended_validation_action or "按完整字段继续执行经营动作"
    elif not recommended_validation_action:
        recommended_validation_action = "补字段验证"
    time_requirement = "T+3 补字段并复核" if missing_fields else ("T+3 继续观察" if conclusion_type == INTERNET_OPS_INFERENCE_LEVEL_D else "T+7 复核")

    return {
        "object_level": object_level,
        "object_id": object_id,
        "final_label": "低样本观察" if conclusion_type == INTERNET_OPS_INFERENCE_LEVEL_D and (user_count < 100 or event_count < 500) else candidate_label,
        "evidence": proxy_evidence,
        "missing_fields": missing_fields,
        "conclusion": conclusion,
        "conclusion_type": conclusion_type,
        "confidence_level": confidence_level,
        "forbidden_actions": forbidden_actions,
        "recommended_validation_action": recommended_validation_action,
        "validation_metric": validation_metric,
        "owner_role": _owner_role_for_object_level(object_level),
        "time_requirement": time_requirement,
        "proxy_evidence": evidence_items,
        "business_assumption": (
            "当前结论基于代理指标或业务逻辑，仍需补字段验证"
            if conclusion_type in {INTERNET_OPS_INFERENCE_LEVEL_B, INTERNET_OPS_INFERENCE_LEVEL_C}
            else ""
        ),
    }


def internet_ops_action_guardrail(
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
    inference = internet_ops_inference_controller(
        object_level=object_level,
        object_id=object_id,
        candidate_label=candidate_label,
        candidate_action=candidate_action,
        evidence=evidence,
        field_availability_registry=field_availability_registry,
        sample_size=sample_size,
        risk_metrics=risk_metrics,
    )
    attempted = str(candidate_action or "").strip() or "观察"
    blocked_reason = ""
    downgraded_action = attempted
    action_strength = "hard_action"
    required_missing_fields = list(inference["missing_fields"])
    forbidden_actions = set(inference["forbidden_actions"])
    low_sample = inference["conclusion_type"] == INTERNET_OPS_INFERENCE_LEVEL_D and (
        "低样本" in str(inference.get("final_label") or "") or "低样本" in inference["conclusion"]
    )

    if low_sample and any(term in attempted for term in INTERNET_OPS_LOW_SAMPLE_BLOCKED_ACTIONS):
        blocked_reason = "低样本对象禁止输出强增长结论"
        downgraded_action = "低样本复核"
        action_strength = "observe_only"
    elif required_missing_fields:
        if any(group in required_missing_fields for group in ["cost_fields", "retention_fields", "revenue_fields", "funnel_fields", "channel_fields", "content_fields"]):
            blocked_reason = "缺少直接字段，禁止输出对应强经营动作"
            downgraded_action = inference["conclusion"]
            action_strength = "soft_action" if downgraded_action in INTERNET_OPS_SOFT_ACTIONS else "candidate"
    elif attempted in INTERNET_OPS_SOFT_ACTIONS:
        action_strength = "soft_action"

    if inference["conclusion_type"] != INTERNET_OPS_INFERENCE_LEVEL_A and action_strength == "hard_action":
        action_strength = "soft_action" if attempted in INTERNET_OPS_SOFT_ACTIONS else "candidate"

    return {
        "allowed": not bool(blocked_reason),
        "blocked": bool(blocked_reason),
        "downgraded_action": downgraded_action,
        "action_strength": action_strength,
        "blocked_reason": blocked_reason,
        "required_missing_fields": required_missing_fields,
        "object_level": inference["object_level"],
        "object_id": inference["object_id"],
        "evidence": inference["evidence"],
        "missing_fields": inference["missing_fields"],
        "conclusion": inference["conclusion"],
        "conclusion_type": inference["conclusion_type"],
        "confidence_level": inference["confidence_level"],
        "forbidden_actions": sorted(forbidden_actions),
        "recommended_validation_action": inference["recommended_validation_action"],
        "validation_metric": inference["validation_metric"],
        "owner_role": inference["owner_role"],
        "time_requirement": inference["time_requirement"],
        "final_label": inference.get("final_label", candidate_label),
    }
