from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.internet_ops_profile_service import (
    internet_ops_field_availability_registry,
    internet_ops_inference_controller,
)


def _compact(value: str) -> str:
    return "".join(ch for ch in str(value).lower().strip() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _first_matching_column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    columns = [str(column) for column in frame.columns]
    compact_aliases = [_compact(alias) for alias in aliases]
    for column in columns:
        compact_column = _compact(column)
        if any(alias and (alias == compact_column or alias in compact_column) for alias in compact_aliases):
            return column
    return None


def _numeric_series(frame: pd.DataFrame, aliases: list[str]) -> pd.Series | None:
    column = _first_matching_column(frame, aliases)
    if not column or column not in frame.columns:
        return None
    series = pd.to_numeric(frame[column], errors="coerce").dropna()
    return series if not series.empty else None


def _sum_value(frame: pd.DataFrame, aliases: list[str]) -> float | None:
    series = _numeric_series(frame, aliases)
    return float(series.sum()) if series is not None else None


def _mean_value(frame: pd.DataFrame, aliases: list[str]) -> float | None:
    series = _numeric_series(frame, aliases)
    return float(series.mean()) if series is not None else None


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if abs(float(value)) >= 1000:
        return f"{float(value):,.0f}"
    if isinstance(value, int) or float(value).is_integer():
        return f"{float(value):.0f}"
    return f"{float(value):.2f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1%}"


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def _first_available_metric(frame: pd.DataFrame, candidates: list[tuple[str, list[str], str]]) -> tuple[str | None, float | None, str]:
    for label, aliases, method in candidates:
        value = _mean_value(frame, aliases) if method == "mean" else _sum_value(frame, aliases)
        if value is not None:
            return label, value, method
    return None, None, ""


def _sample_size(frame: pd.DataFrame) -> dict[str, Any]:
    user_column = _first_matching_column(frame, ["user_id", "uid", "visitor_id", "device_id", "用户id"])
    user_count = int(frame[user_column].nunique()) if user_column and user_column in frame.columns else int(len(frame))
    return {
        "user_count": user_count,
        "event_count": int(len(frame)),
    }


def _module_payload(
    *,
    module_id: str,
    business_question: str,
    object_level: str,
    object_id: str,
    candidate_label: str,
    candidate_action: str,
    evidence: dict[str, Any],
    registry: dict[str, Any],
    sample_size: dict[str, Any],
) -> dict[str, Any]:
    inference = internet_ops_inference_controller(
        object_level=object_level,
        object_id=object_id,
        candidate_label=candidate_label,
        candidate_action=candidate_action,
        evidence=evidence,
        field_availability_registry=registry,
        sample_size=sample_size,
    )
    return {
        "module_id": module_id,
        "business_question": business_question,
        "object_level": inference["object_level"],
        "object_id": inference["object_id"],
        "core_conclusion": inference["conclusion"],
        "evidence": inference["evidence"],
        "missing_fields": inference["missing_fields"],
        "action": inference["recommended_validation_action"],
        "validation_metric": inference["validation_metric"],
        "conclusion_type": inference["conclusion_type"],
        "confidence_level": inference["confidence_level"],
        "forbidden_actions": inference["forbidden_actions"],
        "recommended_validation_action": inference["recommended_validation_action"],
        "owner_role": inference["owner_role"],
        "time_requirement": inference["time_requirement"],
        "sample_size": sample_size,
        "status": "active" if inference["conclusion_type"] != "data_required" else "insufficient",
    }


def north_star_metric_selector(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    management_candidates = [
        ("收入 revenue", ["revenue", "收入", "付费金额"], "sum"),
        ("贡献毛利 contribution_margin", ["contribution_margin", "贡献毛利", "毛利"], "sum"),
        ("真实投放回报 roi", ["roi"], "mean"),
        ("付费用户 paid_users", ["paid_users", "pay_user", "付费用户"], "sum"),
        ("7日留存 retention_d7", ["retention_d7", "d7", "D7", "7日留存"], "mean"),
        ("NPS", ["nps", "NPS"], "mean"),
    ]
    selected_name, selected_value, selected_method = _first_available_metric(frame, management_candidates)
    if selected_name is None:
        legacy_candidates = [
        ("DAU", ["dau", "日活"]),
        ("有效活跃用户", ["active_user", "活跃用户"]),
        ("注册转化用户", ["register_user", "注册用户"]),
        ("付费用户", ["pay_user", "付费用户"]),
        ("GMV", ["gmv"]),
        ("内容互动用户", ["engaged_user", "互动用户", "like"]),
        ("社区有效互动", ["comment", "share", "互动"]),
        ("活动完成用户", ["task_complete", "完成用户", "任务完成"]),
        ("留存用户", ["retained_user", "retention", "留存用户"]),
        ]
        selected_name, selected_value, selected_method = _first_available_metric(
            frame,
            [(label, aliases, "sum") for label, aliases in legacy_candidates],
        )
    missing = [] if selected_name else ["north_star_metric"]
    label = "当前北极星指标组合" if selected_name else "北极星指标待确认"
    action = "按 revenue / contribution_margin / roi / paid_users / retention_d7 / nps 建立北极星经营看板" if selected_name else "补关键增长结果字段后复核北极星指标稳定性"
    evidence = {
        "selected_metric": selected_name or "待补字段",
        "selected_value": _format_number(selected_value),
        "aggregation_method": selected_method,
        "available_groups": ", ".join(registry.get("available_field_groups", [])),
    }
    result = _module_payload(
        module_id="north_star_metric_selector",
        business_question="当前互联网运营盘子最适合临时用哪个北极星指标来统一复盘？",
        object_level="dataset",
        object_id="north_star_metric",
        candidate_label=label,
        candidate_action=action,
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    result["core_conclusion"] = (
        f"{label}可直接落在 `{selected_name}`，当前值约 {_format_number(selected_value)}。管理层应同步看 revenue、contribution_margin、roi、paid_users、retention_d7 与 nps，而不是等待补字段。"
        if selected_name
        else "当前缺少可稳定支撑北极星指标的核心字段，需先补字段。"
    )
    result["missing_fields"] = missing
    if selected_name:
        result["status"] = "active"
        result["conclusion_type"] = "evidence_based_decision"
    return result


def aarrr_funnel_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    stage_values = {
        "Acquisition": _sum_value(frame, ["impressions", "impression", "visit", "曝光", "访问", "pv", "uv"]),
        "Click": _sum_value(frame, ["clicks", "click", "点击"]),
        "Registration": _sum_value(frame, ["registrations", "register", "注册"]),
        "Activation": _sum_value(frame, ["activations", "activation", "login", "激活", "注册"]),
        "Retention": _mean_value(frame, ["retention_d7", "retention", "retained_user", "留存用户", "d1", "d7", "d30"]),
        "Revenue": _sum_value(frame, ["revenue", "gmv", "paid_users", "pay_user", "付费金额", "订单数"]),
        "Referral": _sum_value(frame, ["share", "invite", "referral", "转发"]),
    }
    gaps = [stage for stage, value in stage_values.items() if value is None]
    evidence = {stage: _format_number(value) for stage, value in stage_values.items()}
    core_stages = ["Acquisition", "Click", "Registration", "Activation", "Retention", "Revenue"]
    core_gaps = [stage for stage in core_stages if stage_values.get(stage) is None]
    referral_gap = "Referral" in gaps
    conclusion = "AARRR 主链路可直接判断，Referral 单独作为裂变缺口备注" if not core_gaps else "AARRR 主链路仍存在核心断点"
    result = _module_payload(
        module_id="aarrr_funnel_analyzer",
        business_question="当前互联网运营数据能否支撑 Acquisition、Activation、Retention、Revenue、Referral 的完整判断？",
        object_level="funnel",
        object_id="aarrr",
        candidate_label="AARRR链路盘点",
        candidate_action="按 impressions -> clicks -> registrations -> activations -> paid_users -> revenue 拆解 AARRR 漏斗" if not core_gaps else "补关键漏斗事件后复核转化链路",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    result["core_conclusion"] = f"{conclusion}；核心断点：{', '.join(core_gaps) if core_gaps else '无'}；Referral缺口：{'是' if referral_gap else '否'}。"
    result["missing_fields"] = ["referral_fields"] if referral_gap and not core_gaps else (["funnel_fields"] if core_gaps else [])
    if not core_gaps:
        result["status"] = "active"
        result["conclusion_type"] = "evidence_based_decision"
    return result


def traffic_structure_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    traffic_values = {
        "自然流量": _sum_value(frame, ["organic", "自然流量"]),
        "付费流量": _sum_value(frame, ["paid", "付费流量"]),
        "渠道流量": _sum_value(frame, ["impressions", "clicks", "channel", "traffic_source", "source", "渠道"]),
        "内容流量": _sum_value(frame, ["content_category", "content", "content_id", "内容"]),
        "搜索流量": _sum_value(frame, ["search", "搜索"]),
        "社交流量": _sum_value(frame, ["social", "社交", "share"]),
    }
    total = sum(value for value in traffic_values.values() if value is not None) or None
    top_name = None
    top_value = None
    for name, value in traffic_values.items():
        if value is not None and (top_value is None or value > top_value):
            top_name, top_value = name, value
    evidence = {
        name: f"{_format_number(value)} / {_format_percent(_safe_ratio(value, total))}"
        for name, value in traffic_values.items()
        if value is not None
    }
    result = _module_payload(
        module_id="traffic_structure_analyzer",
        business_question="当前流量结构里，自然、付费、渠道、内容、搜索、社交流量分别承担什么规模和风险？",
        object_level="traffic",
        object_id="traffic_structure",
        candidate_label="流量结构观察",
        candidate_action="渠道池加码/降权/止损/观察分层" if registry.get("has_channel_fields", False) else "补来源字段后做渠道归因",
        evidence=evidence or {"traffic_signal": "当前缺少稳定流量分层字段"},
        registry=registry,
        sample_size=_sample_size(frame),
    )
    result["core_conclusion"] = (
        f"当前流量结构里 `{top_name}` 规模最高，约 {_format_number(top_value)}。"
        if top_name
        else "当前缺少足够的流量结构字段，不能稳定判断流量构成。"
    )
    if not registry.get("has_traffic_fields", False):
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "traffic_fields"]))
    return result


def user_growth_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    values = {
        "新增用户": _sum_value(frame, ["registrations", "new_user", "新增用户", "register_user"]),
        "激活用户": _sum_value(frame, ["activations", "activation", "激活"]),
        "付费用户": _sum_value(frame, ["paid_users", "pay_user", "付费用户"]),
        "回流用户": _sum_value(frame, ["reactivated_user", "回流用户"]),
        "沉默用户": _sum_value(frame, ["silent_user", "沉默用户"]),
        "流失用户": _sum_value(frame, ["churn_user", "流失用户"]),
        "retention_d7": _mean_value(frame, ["retention_d7", "d7", "D7", "7日留存"]),
        "nps": _mean_value(frame, ["nps", "NPS"]),
        "roi": _mean_value(frame, ["roi"]),
        "cac": _mean_value(frame, ["cac", "CAC"]),
    }
    evidence = {key: _format_number(value) for key, value in values.items() if value is not None}
    has_segment_evidence = registry.get("has_segment_fields", False) or {"user_segment", "city_tier"}.intersection(set(str(column) for column in frame.columns))
    action = "基于 user_segment × city_tier 做用户分层加码/降权/止损/观察" if has_segment_evidence else "补真实用户分层字段后复核"
    result = _module_payload(
        module_id="user_growth_analyzer",
        business_question="新增、活跃、回流、沉默、流失用户分别如何变化，规模增长和质量增长是否一致？",
        object_level="user",
        object_id="user_growth",
        candidate_label="用户增长复核",
        candidate_action=action,
        evidence=evidence or {"user_signal": "当前缺少稳定用户规模字段"},
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if has_segment_evidence:
        result["core_conclusion"] = "当前已具备 user_segment、city_tier、retention_d7、nps、roi、cac、paid_users 等信号，可直接做用户分层对象池取舍。"
        result["missing_fields"] = []
        result["status"] = "active"
        result["conclusion_type"] = "evidence_based_decision"
    else:
        result["core_conclusion"] = "当前缺少稳定用户分层字段，用户对象池需要补真实分群后再拆。"
        result["missing_fields"] = ["segment_fields"]
    return result


def funnel_conversion_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    stages = [
        ("曝光到点击", _sum_value(frame, ["impression", "曝光"]), _sum_value(frame, ["click", "点击"])),
        ("点击到注册", _sum_value(frame, ["click", "点击"]), _sum_value(frame, ["register", "注册"])),
        ("注册到激活", _sum_value(frame, ["register", "注册"]), _sum_value(frame, ["activation", "激活"])),
        ("激活到付费", _sum_value(frame, ["activation", "激活"]), _sum_value(frame, ["pay", "付费用户", "purchase"])),
        ("付费到复购", _sum_value(frame, ["pay", "purchase", "付费用户"]), _sum_value(frame, ["repurchase", "复购"])),
    ]
    stage_rows = []
    worst_stage = None
    worst_rate = None
    for name, left, right in stages:
        rate = _safe_ratio(right, left)
        stage_rows.append({"stage": name, "left": _format_number(left), "right": _format_number(right), "rate": _format_percent(rate)})
        if rate is not None and (worst_rate is None or rate < worst_rate):
            worst_stage, worst_rate = name, rate
    result = _module_payload(
        module_id="funnel_conversion_analyzer",
        business_question="曝光到点击、点击到注册、注册到激活、激活到付费、付费到复购里，最大流失环节在哪里？",
        object_level="funnel",
        object_id="conversion_funnel",
        candidate_label="漏斗转化复核",
        candidate_action="当前只能判断单点行为，不能判断完整漏斗效率" if not registry.get("has_funnel_fields", False) else "进入漏斗转化断点修复",
        evidence={row["stage"]: row["rate"] for row in stage_rows},
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if worst_stage:
        result["core_conclusion"] = f"当前最大流失环节在 `{worst_stage}`，转化率约 { _format_percent(worst_rate) }。"
    else:
        result["core_conclusion"] = "当前漏斗关键节点字段不足，只能输出漏斗缺口。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "funnel_fields"]))
    result["evidence"] = stage_rows
    return result


def retention_cohort_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "D1": _format_percent(_mean_value(frame, ["d1", "D1"])),
        "D7": _format_percent(_mean_value(frame, ["d7", "D7"])),
        "D30": _format_percent(_mean_value(frame, ["d30", "D30"])),
        "cohort": _first_matching_column(frame, ["cohort"]),
    }
    result = _module_payload(
        module_id="retention_cohort_analyzer",
        business_question="D1、D7、D30 或 cohort 留存是否可判断，若不可判断缺什么？",
        object_level="retention",
        object_id="retention_cohort",
        candidate_label="留存复核",
        candidate_action="补 D1/D7/D30 后判断用户质量" if not registry.get("has_retention_fields", False) else "进入留存窗口复核",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_retention_fields", False):
        result["core_conclusion"] = "当前留存字段已具备，可继续做 D1/D7/D30 或 cohort 复核。"
    else:
        result["core_conclusion"] = "当前没有稳定 retention_fields，需先补 D1/D7/D30 或 cohort 字段。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "retention_fields"]))
    return result


def content_operations_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    exposure = _sum_value(frame, ["impression", "曝光", "pv"])
    engagement = _sum_value(frame, ["like", "comment", "share", "互动"])
    conversion = _sum_value(frame, ["conversion", "purchase", "pay"])
    evidence = {
        "exposure": _format_number(exposure),
        "engagement": _format_number(engagement),
        "conversion": _format_number(conversion),
    }
    result = _module_payload(
        module_id="content_operations_analyzer",
        business_question="内容曝光、点击、互动、分享、收藏、完播、评论之间，哪些内容是高曝光低互动、高互动低转化或待验证候选？",
        object_level="content",
        object_id="content_operations",
        candidate_label="内容运营复核",
        candidate_action="内容维度不足，只能判断整体互动表现" if not registry.get("has_content_fields", False) else "内容承接优化",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_content_fields", False):
        result["core_conclusion"] = "当前可先基于内容维度识别高曝光低互动、高互动低转化和待验证内容候选。"
    else:
        result["core_conclusion"] = "内容字段不足，只能保留整体互动表现观察。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "content_fields"]))
    return result


def content_asset_matrix(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    exposure = _sum_value(frame, ["impression", "曝光", "pv"])
    engagement = _sum_value(frame, ["like", "comment", "share", "互动"])
    evidence = {
        "高曝光+高互动": "核心内容资产候选" if exposure and engagement else "待验证",
        "高曝光+低互动": "标题/人群错配" if exposure and not engagement else "待验证",
        "低曝光+高互动": "待放量验证" if engagement and not exposure else "待验证",
        "低曝光+低互动": "低优先级观察",
    }
    result = _module_payload(
        module_id="content_asset_matrix",
        business_question="内容资产四象限里，哪些内容是核心资产候选、错配对象、待放量对象或低优先级观察对象？",
        object_level="content",
        object_id="content_asset_matrix",
        candidate_label="内容资产矩阵",
        candidate_action="内容维度不足，只能判断整体互动表现" if not registry.get("has_content_fields", False) else "小流量测试",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_content_fields", False) and registry.get("has_engagement_fields", False):
        result["core_conclusion"] = "当前可以用高曝光/高互动四象限做内容资产候选和待放量验证。"
    else:
        result["core_conclusion"] = "内容或互动字段不足，暂不能稳定形成内容资产矩阵。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "content_fields", "engagement_fields"]))
    return result


def channel_operations_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    scale = _sum_value(frame, ["impressions", "clicks", "channel", "source", "渠道"])
    conversion = _mean_value(frame, ["conversion_rate", "CTR", "转化率"])
    cost = _sum_value(frame, ["operating_cost", "cost", "spend", "消耗"])
    evidence = {
        "channel_scale_signal": _format_number(scale),
        "conversion_rate": _format_percent(conversion),
        "cost_signal": _format_number(cost),
        "roi": _format_number(_mean_value(frame, ["roi"])),
        "cac": _format_number(_mean_value(frame, ["cac", "CAC"])),
    }
    result = _module_payload(
        module_id="channel_operations_analyzer",
        business_question="渠道规模、渠道转化、渠道质量、渠道成本之间，当前能判断到哪一层？",
        object_level="channel",
        object_id="channel_operations",
        candidate_label="渠道运营复核",
        candidate_action="渠道池加码/降权/止损/观察",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_channel_fields", False):
        result["core_conclusion"] = "当前可直接复核渠道规模、CTR、roi、cac 与成本表现，并将渠道池拆成加码、降权、止损、观察四类。"
        result["missing_fields"] = []
        result["status"] = "active"
        result["conclusion_type"] = "evidence_based_decision"
    else:
        result["core_conclusion"] = "当前缺少稳定渠道来源字段，需先补来源字段后再做渠道池取舍。"
        result["missing_fields"] = ["channel_fields"]
    return result


def campaign_operations_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "参与人数": _format_number(_sum_value(frame, ["参与人数", "participant", "join_count"])),
        "报名人数": _format_number(_sum_value(frame, ["报名人数", "register_count"])),
        "完成人数": _format_number(_sum_value(frame, ["任务完成", "complete_count", "activity_complete"])),
        "核销人数": _format_number(_sum_value(frame, ["核销人数", "writeoff_count"])),
    }
    result = _module_payload(
        module_id="campaign_operations_analyzer",
        business_question="活动参与、报名、完成、核销、转化、复访是否可稳定复盘？",
        object_level="campaign",
        object_id="campaign_operations",
        candidate_label="活动运营复核",
        candidate_action="活动承接复核" if registry.get("has_campaign_fields", False) else "补关键漏斗事件后复核转化链路",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_campaign_fields", False):
        result["core_conclusion"] = "当前活动字段已具备，可继续看参与、完成、核销与转化承接。"
    else:
        result["core_conclusion"] = "活动字段不足，当前跳过活动复盘，不强行生成结论。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "campaign_fields"]))
        result["status"] = "skipped"
    return result


def community_operations_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "发帖": _format_number(_sum_value(frame, ["post", "发帖"])),
        "评论": _format_number(_sum_value(frame, ["comment", "评论"])),
        "互动": _format_number(_sum_value(frame, ["interaction", "互动", "like"])),
        "UGC贡献": _format_number(_sum_value(frame, ["ugc", "user_generated_content", "发帖"])),
    }
    result = _module_payload(
        module_id="community_operations_analyzer",
        business_question="社区里的发帖、评论、互动、核心用户、沉默用户和 UGC 贡献能否稳定判断？",
        object_level="community",
        object_id="community_operations",
        candidate_label="社区运营复核",
        candidate_action="社区互动复核" if registry.get("has_engagement_fields", False) else "低样本观察",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_engagement_fields", False):
        result["core_conclusion"] = "当前可先看互动、评论和 UGC 贡献，识别社区承接活跃度。"
    else:
        result["core_conclusion"] = "社区互动字段不足，当前跳过社区模块。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "engagement_fields"]))
        result["status"] = "skipped"
    return result


def monetization_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "订单": _format_number(_sum_value(frame, ["order", "订单数", "purchase"])),
        "GMV": _format_number(_sum_value(frame, ["gmv"])),
        "收入": _format_number(_sum_value(frame, ["revenue", "付费金额"])),
        "ARPU": _format_number(_mean_value(frame, ["arpu"])),
        "ARPPU": _format_number(_mean_value(frame, ["arppu"])),
        "LTV": _format_number(_mean_value(frame, ["ltv"])),
    }
    result = _module_payload(
        module_id="monetization_analyzer",
        business_question="订单、GMV、收入、ARPU、ARPPU、复购、LTV 当前能判断到哪一层？",
        object_level="monetization",
        object_id="monetization",
        candidate_label="商业化复核",
        candidate_action="转化行为较强、收入字段缺失，需补付费/GMV/ARPU/LTV后判断商业价值" if not registry.get("has_revenue_fields", False) else "商业化效率复核",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_revenue_fields", False):
        result["core_conclusion"] = "当前收入字段具备，可继续复核商业化效率与用户价值。"
    else:
        result["core_conclusion"] = "当前只能分析转化行为，收入字段缺失，不能判断商业价值。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "revenue_fields"]))
    return result


def risk_and_anomaly_analyzer(frame: pd.DataFrame, registry: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "负毛利样本": _format_number((_numeric_series(frame, ["contribution_margin"]) < 0).sum() if _numeric_series(frame, ["contribution_margin"]) is not None else None),
        "低 roi 均值": _format_number(_mean_value(frame, ["roi"])),
        "高 CAC 均值": _format_number(_mean_value(frame, ["cac", "CAC"])),
        "retention_d7": _format_percent(_mean_value(frame, ["retention_d7", "d7", "D7"])),
        "nps": _format_number(_mean_value(frame, ["nps", "NPS"])),
        "跳出率": _format_percent(_mean_value(frame, ["bounce_rate", "跳出率"])),
        "卸载": _format_number(_sum_value(frame, ["uninstall", "卸载"])),
        "投诉": _format_number(_sum_value(frame, ["complaint", "投诉"])),
        "差评": _format_number(_sum_value(frame, ["bad_review", "差评"])),
        "举报": _format_number(_sum_value(frame, ["report", "举报"])),
        "异常流量": _format_number(_sum_value(frame, ["abnormal_traffic", "异常流量"])),
    }
    result = _module_payload(
        module_id="risk_and_anomaly_analyzer",
        business_question="当前异常到底更像真实增长、活动拉动、渠道波动、样本噪声，还是数据采集问题？",
        object_level="risk",
        object_id="risk_anomaly",
        candidate_label="风险与异常复核",
        candidate_action="风险与异常节点止损复核",
        evidence=evidence,
        registry=registry,
        sample_size=_sample_size(frame),
    )
    if registry.get("has_quality_fields", False) or registry.get("has_cost_fields", False) or registry.get("has_revenue_fields", False):
        result["core_conclusion"] = "当前可基于负毛利、高 CAC、低 roi、低 retention_d7、低 NPS 直接形成风险与异常止损清单。"
        result["missing_fields"] = []
        result["status"] = "active"
        result["conclusion_type"] = "evidence_based_decision"
    else:
        result["core_conclusion"] = "质量与异常字段不足，当前只能做基础风险提示。"
        result["missing_fields"] = list(dict.fromkeys([*result["missing_fields"], "quality_fields"]))
    return result


def build_internet_operations_analysis_modules(
    frame: pd.DataFrame,
    registry: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    effective_registry = registry or internet_ops_field_availability_registry(frame)
    modules = {
        "north_star_metric_selector": north_star_metric_selector(frame, effective_registry),
        "aarrr_funnel_analyzer": aarrr_funnel_analyzer(frame, effective_registry),
        "traffic_structure_analyzer": traffic_structure_analyzer(frame, effective_registry),
        "user_growth_analyzer": user_growth_analyzer(frame, effective_registry),
        "funnel_conversion_analyzer": funnel_conversion_analyzer(frame, effective_registry),
        "retention_cohort_analyzer": retention_cohort_analyzer(frame, effective_registry),
        "content_operations_analyzer": content_operations_analyzer(frame, effective_registry),
        "content_asset_matrix": content_asset_matrix(frame, effective_registry),
        "channel_operations_analyzer": channel_operations_analyzer(frame, effective_registry),
        "campaign_operations_analyzer": campaign_operations_analyzer(frame, effective_registry),
        "community_operations_analyzer": community_operations_analyzer(frame, effective_registry),
        "monetization_analyzer": monetization_analyzer(frame, effective_registry),
        "risk_and_anomaly_analyzer": risk_and_anomaly_analyzer(frame, effective_registry),
    }
    return modules


def write_internet_operations_module_results(
    output_dir: str | Path,
    modules: dict[str, dict[str, Any]],
) -> list[str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    written_paths: list[str] = []
    for module_id, payload in modules.items():
        module_path = output_path / f"{module_id}_module_result.json"
        module_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written_paths.append(str(module_path))
    return written_paths
