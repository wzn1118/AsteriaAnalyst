from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _join_list(values: list[str], *, default: str) -> str:
    cleaned = [_text(value) for value in values if _text(value)]
    return " / ".join(cleaned) if cleaned else default


def _make_table(title: str, rows: list[dict[str, Any]], note: str = "") -> dict[str, Any]:
    columns = list(rows[0].keys()) if rows else []
    return {
        "title": title,
        "columns": columns,
        "rows": rows,
        "note": note,
    }


def _compact_tables(sections: list[dict[str, Any]], *, max_rows: int = 6) -> list[dict[str, Any]]:
    compacted: list[dict[str, Any]] = []
    for section in sections:
        copied = {**section}
        copied_tables = []
        for table in section.get("tables", []) or []:
            copied_table = dict(table)
            copied_table["rows"] = list((table.get("rows") or [])[:max_rows])
            copied_tables.append(copied_table)
        copied["tables"] = copied_tables
        compacted.append(copied)
    return compacted


def _report_section_lookup(report: dict[str, Any], section_id: str) -> dict[str, Any] | None:
    for section in report.get("sections", []) or []:
        if str(section.get("id") or "") == section_id:
            return section
    return None


def _existing_sections(report: dict[str, Any], section_ids: list[str]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for section_id in section_ids:
        section = _report_section_lookup(report, section_id)
        if section:
            sections.append(section)
    return sections


def _page_section(
    *,
    section_id: str,
    title: str,
    business_question: str,
    core_conclusion: str,
    evidence: str,
    boundary: str,
    action_plan: str,
    tables: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "summary": f"业务问题：{business_question}",
        "bullets": [
            f"核心结论：{core_conclusion}",
            f"证据：{evidence}",
            f"字段边界：{boundary}",
            f"动作或验证计划：{action_plan}",
        ],
        "tables": tables or [],
        "charts": [],
        "page_break_before": True,
    }


def _module_payload(modules: dict[str, dict[str, Any]], module_id: str) -> dict[str, Any]:
    return modules.get(module_id) or {
        "core_conclusion": "当前模块结果缺失，需先补模块输出。",
        "evidence": "当前无有效证据",
        "missing_fields": [],
        "recommended_validation_action": "补字段验证",
        "validation_metric": "关键指标补齐",
        "status": "insufficient",
    }


def _registry_row(registry_rows: list[dict[str, Any]], object_id: str) -> dict[str, Any] | None:
    return next((row for row in registry_rows if str(row.get("object_id") or "") == object_id), None)


def _title_from_registry(field_registry: dict[str, Any]) -> str:
    matched = field_registry.get("matched_field_signals") or {}
    content_aliases = (matched.get("content_fields") or {}).get("matched_aliases") or []
    engagement_aliases = (matched.get("engagement_fields") or {}).get("matched_aliases") or []
    channel_aliases = (matched.get("channel_fields") or {}).get("matched_aliases") or []
    user_aliases = (matched.get("user_fields") or {}).get("matched_aliases") or []
    if any(alias in {"post", "comment", "follow", "互动", "评论", "关注"} for alias in engagement_aliases + content_aliases):
        return "《社区运营数据分析报告：活跃、互动、留存与成员结构复盘》"
    if field_registry.get("has_channel_fields") and field_registry.get("has_cost_fields"):
        return "《渠道投放与增长运营复盘报告：流量质量、转化效率与成本回收》"
    if field_registry.get("has_content_fields") and field_registry.get("has_engagement_fields"):
        return "《内容运营数据分析报告：流量、互动、转化与内容资产复盘》"
    if field_registry.get("has_user_fields") and field_registry.get("has_funnel_fields"):
        return "《用户增长数据分析报告：获客、激活、留存与转化复盘》"
    return "《互联网运营数据分析报告：增长、转化、留存与内容效率复盘》"


def _summary_bullets(
    *,
    title: str,
    field_registry: dict[str, Any],
    modules: dict[str, dict[str, Any]],
    registry_rows: list[dict[str, Any]],
) -> list[str]:
    north_star = _module_payload(modules, "north_star_metric_selector")
    aarrr = _module_payload(modules, "aarrr_funnel_analyzer")
    channel = _registry_row(registry_rows, "channel_portfolio")
    content = _registry_row(registry_rows, "content_portfolio")
    user_segment = _registry_row(registry_rows, "user_segment_portfolio")
    return [
        f"报告定位：{title}，当前按 `{field_registry.get('report_mode', 'app_website_operations_report')}` 口径输出。",
        f"北极星判断：{north_star.get('core_conclusion', '')}",
        f"AARRR 总览：{aarrr.get('core_conclusion', '')}",
        f"渠道对象：{channel.get('final_label', '待补渠道判断')}；动作：{channel.get('final_action', '补字段验证')}" if channel else "渠道对象：当前缺少稳定渠道判断。",
        f"内容/用户对象：{content.get('final_label', '待补内容判断')} / {user_segment.get('final_label', '待补用户判断')}" if content and user_segment else "内容/用户对象：当前以补字段和复核为主。",
    ][:5]


def build_internet_operations_management_variant(report: dict[str, Any]) -> dict[str, Any] | None:
    if str(report.get("business_profile") or "") != "internet_operations_report":
        return None
    field_registry = report.get("internet_ops_field_availability_registry") or {}
    modules = report.get("internet_operations_analysis_modules") or {}
    registry_payload = report.get("internet_ops_object_decision_registry") or {}
    registry_rows = list(registry_payload.get("rows") or [])
    action_rows = list(report.get("internet_ops_action_table") or [])
    roadmap_payload = report.get("internet_ops_action_roadmap") or {}
    seven_day_rows = list(roadmap_payload.get("seven_day_action_table") or [])
    backlog_rows = list(roadmap_payload.get("thirty_day_growth_experiment_backlog") or [])
    forbidden_rows = list(roadmap_payload.get("forbidden_judgement_rows") or [])
    if not field_registry or not modules:
        return None

    title = _title_from_registry(field_registry)
    summary_bullets = _summary_bullets(
        title=title,
        field_registry=field_registry,
        modules=modules,
        registry_rows=registry_rows,
    )

    supported = field_registry.get("supported_analysis_modules") or []
    unsupported = field_registry.get("unsupported_analysis_modules") or []
    data_range_rows = [
        {"字段组": group, "是否可用": "是", "说明": "当前字段已具备"}
        for group in field_registry.get("available_field_groups") or []
    ] + [
        {"字段组": group, "是否可用": "否", "说明": "当前字段缺失"}
        for group in field_registry.get("missing_field_groups") or []
    ]

    missing_fields = field_registry.get("missing_field_groups") or []
    blocked_actions = []
    for row in registry_rows:
        for action in row.get("blocked_actions") or []:
            if action and action not in blocked_actions:
                blocked_actions.append(str(action))

    north_star = _module_payload(modules, "north_star_metric_selector")
    aarrr = _module_payload(modules, "aarrr_funnel_analyzer")
    traffic = _module_payload(modules, "traffic_structure_analyzer")
    user_growth = _module_payload(modules, "user_growth_analyzer")
    funnel = _module_payload(modules, "funnel_conversion_analyzer")
    retention = _module_payload(modules, "retention_cohort_analyzer")
    content_ops = _module_payload(modules, "content_operations_analyzer")
    content_matrix = _module_payload(modules, "content_asset_matrix")
    channel_ops = _module_payload(modules, "channel_operations_analyzer")
    campaign_ops = _module_payload(modules, "campaign_operations_analyzer")
    community_ops = _module_payload(modules, "community_operations_analyzer")
    monetization = _module_payload(modules, "monetization_analyzer")
    risk = _module_payload(modules, "risk_and_anomaly_analyzer")

    channel_row = _registry_row(registry_rows, "channel_portfolio") or {}
    content_row = _registry_row(registry_rows, "content_portfolio") or {}
    user_row = _registry_row(registry_rows, "user_segment_portfolio") or {}
    campaign_row = _registry_row(registry_rows, "campaign_portfolio") or {}
    community_row = _registry_row(registry_rows, "community_portfolio") or {}
    monetization_row = _registry_row(registry_rows, "monetization_users") or {}
    funnel_row = _registry_row(registry_rows, "growth_funnel") or {}
    risk_row = _registry_row(registry_rows, "risk_anomaly") or {}

    sections = [
        _page_section(
            section_id="internet_ops_data_scope",
            title="数据范围与字段可用性",
            business_question="当前这份互联网运营数据能支撑哪些运营复盘模块？",
            core_conclusion=f"当前可用字段组为 {', '.join(field_registry.get('available_field_groups') or ['无'])}；缺失字段组为 {', '.join(field_registry.get('missing_field_groups') or ['无'])}。",
            evidence=f"支持模块：{', '.join(supported or ['无'])}",
            boundary=f"缺失字段组：{', '.join(missing_fields or ['无'])}",
            action_plan="优先按字段可用性决定模块能否进入管理层正文。",
            tables=[_make_table("字段可用性总表", data_range_rows[:20])],
        ),
        _page_section(
            section_id="internet_ops_can_judge",
            title="当前可判断内容与不可判断内容",
            business_question="当前能稳定输出哪些运营判断，哪些结论必须压住？",
            core_conclusion=f"当前可判断：{', '.join(supported or ['无'])}；当前不可判断：{', '.join(unsupported or ['无'])}。",
            evidence=f"禁止误判动作示例：{', '.join(blocked_actions[:8] or ['无'])}",
            boundary="字段不足的模块只输出代理指标判断、风险提示或补字段动作，不输出强增长拍板。",
            action_plan="先按模块边界组织管理层复盘，再决定是否进入更强动作。",
        ),
        _page_section(
            section_id="internet_ops_north_star",
            title="北极星指标判断",
            business_question=north_star["business_question"],
            core_conclusion=north_star["core_conclusion"],
            evidence=str(north_star["evidence"]),
            boundary=f"缺失字段：{_join_list(list(north_star.get('missing_fields') or []), default='无')}",
            action_plan=f"{north_star['recommended_validation_action']}；验证指标：{north_star['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_aarrr",
            title="AARRR 漏斗总览",
            business_question=aarrr["business_question"],
            core_conclusion=aarrr["core_conclusion"],
            evidence=str(aarrr["evidence"]),
            boundary=f"缺失字段：{_join_list(list(aarrr.get('missing_fields') or []), default='无')}",
            action_plan=f"{aarrr['recommended_validation_action']}；验证指标：{aarrr['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_acquisition",
            title="获客分析",
            business_question="当前获客规模来自哪里，能否稳定判断获客结构？",
            core_conclusion=traffic["core_conclusion"],
            evidence=str(traffic["evidence"]),
            boundary=f"交通/来源字段边界：{_join_list(list(traffic.get('missing_fields') or []), default='无')}",
            action_plan=f"{traffic['recommended_validation_action']}；验证指标：{traffic['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_activation",
            title="激活分析",
            business_question="新增到激活的承接是否稳定，当前最大阻塞在哪里？",
            core_conclusion=funnel["core_conclusion"],
            evidence=str(funnel["evidence"]),
            boundary=f"激活与漏斗字段边界：{_join_list(list(funnel.get('missing_fields') or []), default='无')}",
            action_plan=f"{funnel['recommended_validation_action']}；验证指标：{funnel['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_retention",
            title="留存分析或留存字段缺口",
            business_question=retention["business_question"],
            core_conclusion=retention["core_conclusion"],
            evidence=str(retention["evidence"]),
            boundary=f"留存字段边界：{_join_list(list(retention.get('missing_fields') or []), default='无')}",
            action_plan=f"{retention['recommended_validation_action']}；验证指标：{retention['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_revenue",
            title="收入分析或收入字段缺口",
            business_question=monetization["business_question"],
            core_conclusion=monetization["core_conclusion"],
            evidence=str(monetization["evidence"]),
            boundary=f"收入字段边界：{_join_list(list(monetization.get('missing_fields') or []), default='无')}",
            action_plan=f"{monetization['recommended_validation_action']}；验证指标：{monetization['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_referral",
            title="传播/分享分析或字段缺口",
            business_question="传播和分享链路是否可判断，当前能看到哪些代理信号？",
            core_conclusion="当前传播判断优先看分享、互动与转介绍代理信号；字段不足时只输出传播缺口。",
            evidence=str(aarrr["evidence"]),
            boundary=f"传播字段边界：{_join_list(['engagement_fields' if not field_registry.get('has_engagement_fields') else ''], default='无')}",
            action_plan="补分享/转介绍字段后，再判断 Referral 效率。",
        ),
        _page_section(
            section_id="internet_ops_traffic_structure",
            title="流量结构分析",
            business_question=traffic["business_question"],
            core_conclusion=traffic["core_conclusion"],
            evidence=str(traffic["evidence"]),
            boundary=f"流量结构字段边界：{_join_list(list(traffic.get('missing_fields') or []), default='无')}",
            action_plan=f"{traffic['recommended_validation_action']}；验证指标：{traffic['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_user_growth",
            title="用户增长分析",
            business_question=user_growth["business_question"],
            core_conclusion=user_growth["core_conclusion"],
            evidence=str(user_growth["evidence"]),
            boundary=f"用户增长字段边界：{_join_list(list(user_growth.get('missing_fields') or []), default='无')}",
            action_plan=f"{user_growth['recommended_validation_action']}；验证指标：{user_growth['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_funnel_conversion",
            title="漏斗转化分析",
            business_question=funnel["business_question"],
            core_conclusion=funnel["core_conclusion"],
            evidence=str(funnel["evidence"]),
            boundary=f"漏斗字段边界：{_join_list(list(funnel.get('missing_fields') or []), default='无')}",
            action_plan=f"{funnel['recommended_validation_action']}；验证指标：{funnel['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_user_segment",
            title="用户分层分析",
            business_question="当前用户分层应该优先关注高活跃、流失风险、回流还是付费潜力？",
            core_conclusion=f"{user_row.get('object_name', '用户分层')} 当前标签为 {user_row.get('final_label', '待补字段')}。",
            evidence=user_row.get("evidence_summary", "当前无稳定用户分层证据"),
            boundary=f"缺失字段：{_join_list(list(user_row.get('missing_fields') or []), default='无')}",
            action_plan=f"{user_row.get('final_action', '补字段验证')}；负责人：{user_row.get('owner_role', '用户运营')}；验证指标：{user_row.get('validation_metric', '关键指标补齐')}",
        ),
        _page_section(
            section_id="internet_ops_content_overview",
            title="内容运营总览",
            business_question=content_ops["business_question"],
            core_conclusion=content_ops["core_conclusion"],
            evidence=str(content_ops["evidence"]),
            boundary=f"内容字段边界：{_join_list(list(content_ops.get('missing_fields') or []), default='无')}",
            action_plan=f"{content_ops['recommended_validation_action']}；验证指标：{content_ops['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_content_matrix",
            title="内容资产矩阵",
            business_question=content_matrix["business_question"],
            core_conclusion=content_matrix["core_conclusion"],
            evidence=str(content_matrix["evidence"]),
            boundary=f"矩阵字段边界：{_join_list(list(content_matrix.get('missing_fields') or []), default='无')}",
            action_plan=f"{content_matrix['recommended_validation_action']}；验证指标：{content_matrix['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_high_exposure_low_engagement",
            title="高曝光低互动内容",
            business_question="哪些内容当前高曝光但互动承接弱，说明标题、人群或分发可能错配？",
            core_conclusion="高曝光低互动内容优先进入标题/人群错配复核，不直接扩大分发。",
            evidence=str(content_matrix["evidence"]),
            boundary=f"缺失字段：{_join_list(list(content_matrix.get('missing_fields') or []), default='无')}",
            action_plan="先做内容样本复核，再决定是否调整标题、人群或渠道分发。",
        ),
        _page_section(
            section_id="internet_ops_low_exposure_high_engagement",
            title="低曝光高互动内容",
            business_question="哪些内容当前曝光不高但互动效率高，适合进入待放量验证？",
            core_conclusion="低曝光高互动内容只进入待放量验证池，不直接认定为主推内容。",
            evidence=str(content_matrix["evidence"]),
            boundary=f"缺失字段：{_join_list(list(content_matrix.get('missing_fields') or []), default='无')}",
            action_plan="用小流量测试验证放量后互动和转化是否仍保持稳定。",
        ),
        _page_section(
            section_id="internet_ops_high_engagement_low_conversion",
            title="高互动低转化内容",
            business_question="哪些内容互动表现不错，但商业化或转化承接偏弱？",
            core_conclusion=content_ops["core_conclusion"],
            evidence=str(content_ops["evidence"]),
            boundary=f"收入/漏斗边界：{_join_list(list(content_ops.get('missing_fields') or []), default='无')}",
            action_plan="优先核查内容转化承接，而不是直接认定内容策略有效。",
        ),
        _page_section(
            section_id="internet_ops_channel_overview",
            title="渠道运营总览",
            business_question=channel_ops["business_question"],
            core_conclusion=channel_ops["core_conclusion"],
            evidence=str(channel_ops["evidence"]),
            boundary=f"渠道字段边界：{_join_list(list(channel_ops.get('missing_fields') or []), default='无')}",
            action_plan=f"{channel_ops['recommended_validation_action']}；验证指标：{channel_ops['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_channel_quality",
            title="渠道流量质量",
            business_question="哪些渠道是高转化候选，哪些渠道存在低质流量风险？",
            core_conclusion=f"渠道对象当前标签：{channel_row.get('final_label', '待补渠道判断')}。",
            evidence=channel_row.get("evidence_summary", "当前缺少稳定渠道证据"),
            boundary=f"缺失字段：{_join_list(list(channel_row.get('missing_fields') or []), default='无')}",
            action_plan=f"{channel_row.get('final_action', '补字段验证')}；验证指标：{channel_row.get('validation_metric', '关键指标补齐')}",
        ),
        _page_section(
            section_id="internet_ops_channel_conversion",
            title="渠道转化质量",
            business_question="渠道之间的转化质量有没有拉开，能不能支持继续验证？",
            core_conclusion=channel_ops["core_conclusion"],
            evidence=str(channel_ops["evidence"]),
            boundary=f"转化/成本边界：{_join_list(list(channel_ops.get('missing_fields') or []), default='无')}",
            action_plan="只在字段支持时继续比较渠道转化与承接质量。",
        ),
        _page_section(
            section_id="internet_ops_channel_cost",
            title="渠道成本缺口或成本效率",
            business_question="当前是否可以判断渠道成本效率，还是只能先补成本字段？",
            core_conclusion="有成本字段时才讨论成本效率；缺成本字段时只保留流量与转化表现。",
            evidence=str(channel_ops["evidence"]),
            boundary=f"成本字段边界：{_join_list(list(channel_ops.get('missing_fields') or []), default='无')}",
            action_plan=f"{channel_ops['recommended_validation_action']}；验证指标：{channel_ops['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_campaign",
            title="活动运营分析",
            business_question=campaign_ops["business_question"],
            core_conclusion=campaign_ops["core_conclusion"],
            evidence=str(campaign_ops["evidence"]),
            boundary=f"活动字段边界：{_join_list(list(campaign_ops.get('missing_fields') or []), default='无')}",
            action_plan=f"{campaign_ops['recommended_validation_action']}；验证指标：{campaign_ops['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_community",
            title="社区运营分析",
            business_question=community_ops["business_question"],
            core_conclusion=community_ops["core_conclusion"],
            evidence=str(community_ops["evidence"]),
            boundary=f"社区字段边界：{_join_list(list(community_ops.get('missing_fields') or []), default='无')}",
            action_plan=f"{community_ops['recommended_validation_action']}；验证指标：{community_ops['validation_metric']}",
        ),
        *(
            [dict(section) for section in (report.get("internet_ops_management_core_sections") or [])]
            or _existing_sections(
                report,
                [
                    "ops_topline",
                    "ops_channel_scorecard",
                    "ops_channel_impact",
                    "ops_activity_scorecard",
                    "ops_activity_impact",
                    "ops_content_scorecard",
                    "ops_content_impact",
                    "ops_combo_impact",
                    "ops_combo_direct_actions",
                    "ops_specialist_judgement",
                    "ops_specialist_actions",
                ],
            )
        ),
        _page_section(
            section_id="internet_ops_monetization",
            title="付费与商业化分析",
            business_question=monetization["business_question"],
            core_conclusion=monetization["core_conclusion"],
            evidence=str(monetization["evidence"]),
            boundary=f"收入字段边界：{_join_list(list(monetization.get('missing_fields') or []), default='无')}",
            action_plan=f"{monetization['recommended_validation_action']}；验证指标：{monetization['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_risk_users",
            title="风险用户与异常行为",
            business_question="哪些用户、页面或节点当前更像风险对象，而不是健康增长对象？",
            core_conclusion=f"风险对象当前标签：{risk_row.get('final_label', '风险与异常复核')}。",
            evidence=risk_row.get("evidence_summary", "当前缺少稳定风险对象证据"),
            boundary=f"缺失字段：{_join_list(list(risk_row.get('missing_fields') or []), default='无')}",
            action_plan=f"{risk_row.get('final_action', '补字段验证')}；验证指标：{risk_row.get('validation_metric', '关键指标补齐')}",
        ),
        _page_section(
            section_id="internet_ops_anomaly",
            title="异常波动分析",
            business_question=risk["business_question"],
            core_conclusion=risk["core_conclusion"],
            evidence=str(risk["evidence"]),
            boundary=f"质量与异常边界：{_join_list(list(risk.get('missing_fields') or []), default='无')}",
            action_plan=f"{risk['recommended_validation_action']}；验证指标：{risk['validation_metric']}",
        ),
        _page_section(
            section_id="internet_ops_problem_diagnosis",
            title="运营问题诊断",
            business_question="当前互联网运营盘子的主要问题更偏获客、激活、留存、内容、渠道还是数据缺口？",
            core_conclusion="当前问题诊断必须同时考虑流量结构、漏斗断点、留存缺口、内容承接和成本/收入字段边界。",
            evidence=f"支持模块：{', '.join(supported or ['无'])}；缺失模块：{', '.join(unsupported or ['无'])}",
            boundary=f"缺失字段组：{', '.join(missing_fields or ['无'])}",
            action_plan="先把问题定位到具体链路，再决定是修复、补字段还是做实验验证。",
        ),
        _page_section(
            section_id="internet_ops_action_table",
            title="对象级行动表",
            business_question="当前有哪些对象已经形成唯一标签和唯一动作，可以直接派单？",
            core_conclusion="对象级行动表只读取统一对象动作主表，不允许模块各自写动作。",
            evidence=f"对象数：{len(registry_rows)}；冲突数：{len(registry_payload.get('conflicting_object_actions') or [])}",
            boundary="若同一 object_id 出现多个 final_action，quality gate 必须直接 fail。",
            action_plan="以下动作表可直接派单执行。",
            tables=[_make_table("对象级行动表", action_rows[:12], note="主报告正文保留管理层可执行动作；更长明细进入附录。")] if action_rows else [],
        ),
        _page_section(
            section_id="internet_ops_7day_actions",
            title="7日运营动作表",
            business_question="未来 7 天最值得优先推进的运营动作是什么？",
            core_conclusion="7 日动作优先围绕补字段、复核转化承接、验证渠道质量和小流量内容测试展开。",
            evidence="动作来源：对象级行动表 + 当前字段缺口。",
            boundary="缺字段时只安排补字段和验证动作，不安排强经营动作。",
            action_plan="按负责人和时间要求推进 T+3 / T+7 动作。",
            tables=[_make_table("7日运营动作表", seven_day_rows[:10])] if seven_day_rows else [],
        ),
        _page_section(
            section_id="internet_ops_30day_backlog",
            title="30日增长实验 backlog",
            business_question="未来 30 天哪些实验最值得排进 backlog？",
            core_conclusion="增长实验 backlog 只围绕字段已经支持或能通过小流量验证的环节展开。",
            evidence="实验来源：漏斗断点、内容资产候选、渠道质量候选、留存缺口。",
            boundary="缺长期留存、成本或收入字段时，不把实验写成已验证增长杠杆。",
            action_plan="优先做小流量验证、埋点补齐和承接链路实验。",
            tables=[_make_table("30日增长实验 backlog", backlog_rows[:10])] if backlog_rows else [],
        ),
        _page_section(
            section_id="internet_ops_forbidden_judgements",
            title="禁止误判清单",
            business_question="当前有哪些结论不能下，哪些词不能写进正式判断？",
            core_conclusion="缺字段时，必须把结论降级为代理指标判断、业务假设、风险提示或补字段动作。",
            evidence=f"被拦截动作：{', '.join(blocked_actions[:10] or ['无'])}",
            boundary="禁止把 ROI、高价值用户、长期黏性、内容主推、渠道砍掉等词写成事实。",
            action_plan="所有正式动作统一从对象动作主表读取。",
            tables=[_make_table("禁止误判清单", forbidden_rows[:10])] if forbidden_rows else [],
        ),
        _page_section(
            section_id="internet_ops_data_gap_priority",
            title="数据补充优先级",
            business_question="当前最该优先补哪些字段，补齐后能升级哪些结论？",
            core_conclusion=f"当前最高优先级缺口为：{', '.join(missing_fields[:6] or ['无'])}。",
            evidence=f"缺失字段组：{', '.join(missing_fields or ['无'])}",
            boundary="缺字段时，管理层正文只输出边界和补字段计划。",
            action_plan="先补成本、留存、收入、漏斗和内容/渠道关键字段，再升级增长判断。",
            tables=[_make_table("数据补充优先级", [{"缺失字段组": group, "补齐后可判断": "升级相应运营模块结论"} for group in missing_fields[:12]])],
        ),
        _page_section(
            section_id="internet_ops_roadmap",
            title="管理层行动路线图",
            business_question="管理层下一步该如何排优先级、配人、排时序？",
            core_conclusion="行动路线图按补字段 -> 复核关键对象 -> 小流量验证 -> 复盘升级的顺序推进。",
            evidence=f"对象级动作数：{len(action_rows)}；重点对象：{', '.join(row.get('object_name', '') for row in registry_rows[:5])}",
            boundary="没有直接字段支撑前，不进入强增长加码或强预算动作。",
            action_plan="优先推动渠道、内容、用户、活动、风险五类对象的验证动作闭环。",
        ),
        _page_section(
            section_id="internet_ops_appendix_note",
            title="附录说明",
            business_question="主报告之外，还有哪些内容会进入附录，主报告本身独立够不够读？",
            core_conclusion="主报告已包含结论、证据、字段边界、行动表、负责人、时间要求和验证指标，可独立阅读。",
            evidence="附录保留完整明细、大表、多维拆解和统计支撑，不替代主报告的核心信息。",
            boundary="禁止使用“完整表格请查看附件”替代主报告核心信息。",
            action_plan="附录用于延伸复盘，不影响管理层主报告独立使用。",
        ),
    ]

    variant = {
        **report,
        "title": title,
        "executive_summary": summary_bullets[:5],
        "sections": _compact_tables(sections, max_rows=6),
        "strategy_management_ids": [section["id"] for section in sections],
    }
    return variant
