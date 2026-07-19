from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _join(values: list[str], default: str = "无") -> str:
    cleaned = [_text(value) for value in values if _text(value)]
    return " / ".join(cleaned) if cleaned else default


def _table(title: str, rows: list[dict[str, Any]], note: str = "") -> dict[str, Any]:
    return {
        "title": title,
        "columns": list(rows[0].keys()) if rows else [],
        "rows": rows,
        "note": note,
    }


def _title(report: dict[str, Any], field_registry: dict[str, Any]) -> str:
    dataset_name = str(report.get("dataset_name") or "")
    if any(token in dataset_name for token in ["淘宝", "天猫"]):
        return "《淘宝/天猫商品经营分析报告：商品、店铺、类目与评价售后复盘》"
    if "京东" in dataset_name:
        return "《京东商品经营与采销复盘报告：销售、库存、履约与评价表现》"
    if field_registry.get("has_shop_seller_fields") and field_registry.get("has_traffic_fields") and field_registry.get("has_conversion_fields"):
        return "《店铺经营分析报告：流量、转化、成交、售后与商品结构复盘》"
    if field_registry.get("has_margin_cost_fields") and field_registry.get("has_inventory_fields") and field_registry.get("has_fulfillment_fields"):
        return "《采销经营复盘报告：商品结构、供应商表现、库存履约与毛利风险》"
    return "《电商商品经营复盘报告：销售、转化、库存、履约与口碑分析》"


def _module_payload(modules: dict[str, dict[str, Any]], name: str) -> dict[str, Any]:
    return modules.get(name) or {
        "business_question": "当前模块结果缺失",
        "key_findings": ["当前模块结果缺失，需先补模块输出。"],
        "evidence": {},
        "missing_fields": [],
        "unsupported_claims": [],
        "recommended_actions": ["补字段验证"],
        "validation_metrics": ["关键指标补齐"],
        "confidence_level": "low",
        "conclusion_type": "data_required",
    }


def _registry_row(rows: list[dict[str, Any]], object_level: str) -> dict[str, Any] | None:
    return next((row for row in rows if str(row.get("object_level") or "") == object_level), None)


def _boundary_text(field_registry: dict[str, Any], module_payload: dict[str, Any]) -> str:
    missing = list(dict.fromkeys(list(module_payload.get("missing_fields") or [])))
    if missing:
        return f"当前缺失字段组：{', '.join(missing)}；因此不能直接下强经营拍板。"
    return "当前字段边界已满足该模块的基础判断，但仍需按对象层继续复核。"


def _gap_bullets(importance: str, missing_fields: list[str], cannot_conclude: list[str], next_fields: list[str], next_metrics: list[str]) -> list[str]:
    return [
        f"该模块为什么重要：{importance}",
        f"当前缺哪些字段：{', '.join(missing_fields) if missing_fields else '无明显缺口'}",
        f"当前不能得出哪些结论：{'; '.join(cannot_conclude) if cannot_conclude else '无'}",
        f"下一步补什么字段：{', '.join(next_fields) if next_fields else '无'}",
        f"补齐后看什么指标：{', '.join(next_metrics) if next_metrics else '关键经营指标'}",
    ]


def _page_section(
    section_id: str,
    title: str,
    business_question: str,
    core_finding: str,
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
            f"核心发现：{core_finding}",
            f"证据：{evidence}",
            f"字段边界：{boundary}",
            f"管理动作或验证计划：{action_plan}",
        ],
        "tables": tables or [],
        "charts": [],
        "page_break_before": True,
    }


def _summary(field_registry: dict[str, Any], registry_rows: list[dict[str, Any]]) -> list[str]:
    can_judge = [
        "商品经营结构",
        "类目经营结构",
        "店铺/商家承接",
        "库存履约边界",
        "评价与售后风险",
        "毛利/成本边界" if field_registry.get("has_margin_cost_fields") else "毛利/成本字段缺口",
    ]
    cannot = []
    if not field_registry.get("has_margin_cost_fields", False):
        cannot.append("不能判断利润、ROI、加码价值")
    if not field_registry.get("has_inventory_fields", False):
        cannot.append("不能判断补货、清仓、压货")
    if not field_registry.get("has_fulfillment_fields", False):
        cannot.append("不能判断物流和发货问题")
    if not field_registry.get("has_aftersales_fields", False):
        cannot.append("不能判断退款退货风险")
    if not field_registry.get("has_review_fields", False):
        cannot.append("不能判断口碑")
    if not field_registry.get("has_traffic_fields", False):
        cannot.append("不能判断曝光和点击问题")
    if not field_registry.get("has_conversion_fields", False):
        cannot.append("不能判断漏斗断点")
    if not field_registry.get("has_time_fields", False):
        cannot.append("不能判断趋势、环比、同比")
    top_rows = registry_rows[:3]
    bullets = [
        f"当前能判断：{', '.join(can_judge[:5])}。",
        f"当前不能判断：{'; '.join(cannot[:5]) or '无明显硬缺口'}。",
    ]
    if top_rows:
        bullets.append("当前最值得优先复核的对象包括：" + "；".join(f"{row['object_name']}（{row['final_label']} / {row['final_action']}）" for row in top_rows))
    bullets.append("未来 7 天优先做补字段、复核、归因、修复和小范围验证，不直接下越权强动作。")
    bullets.append("所有正式动作都读取电商对象决策注册表，不允许各章节自行写最终动作。")
    return bullets[:5]


def build_ecommerce_management_variant(report: dict[str, Any]) -> dict[str, Any] | None:
    if str(report.get("business_profile") or "") != "ecommerce_product_operations_report":
        return None

    field_registry = report.get("ecommerce_field_availability_registry") or {}
    modules = report.get("product_operations_analysis_modules") or {}
    registry_payload = report.get("ecommerce_object_decision_registry") or {}
    registry_rows = list(registry_payload.get("rows") or [])
    action_rows = list(report.get("ecommerce_action_table") or [])
    roadmap_payload = report.get("ecommerce_action_roadmap") or {}
    seven_day_rows = list(roadmap_payload.get("seven_day_ecommerce_action_table") or [])
    backlog_rows = list(roadmap_payload.get("thirty_day_ecommerce_experiment_backlog") or [])
    forbidden_rows = list(roadmap_payload.get("forbidden_judgement_rows") or [])
    if not field_registry or not modules:
        return None

    title = _title(report, field_registry)
    summary = _summary(field_registry, registry_rows)
    overview = _module_payload(modules, "ecommerce_overview_analyzer")
    product = _module_payload(modules, "product_performance_analyzer")
    category = _module_payload(modules, "category_performance_analyzer")
    shop = _module_payload(modules, "shop_seller_analyzer")
    funnel = _module_payload(modules, "traffic_conversion_analyzer")
    price = _module_payload(modules, "price_promotion_analyzer")
    inventory = _module_payload(modules, "inventory_fulfillment_analyzer")
    aftersales = _module_payload(modules, "aftersales_review_analyzer")
    margin = _module_payload(modules, "margin_profit_analyzer")
    anomaly = _module_payload(modules, "anomaly_detection_analyzer")
    lifecycle = _module_payload(modules, "product_lifecycle_analyzer")
    diagnosis = _module_payload(modules, "ecommerce_management_diagnosis")

    product_row = _registry_row(registry_rows, "product") or {}
    category_row = _registry_row(registry_rows, "category") or {}
    shop_row = _registry_row(registry_rows, "shop_seller") or {}
    brand_row = _registry_row(registry_rows, "brand") or {}
    supplier_row = _registry_row(registry_rows, "supplier") or {}

    field_rows = (
        [{"字段组": group, "是否可用": "是"} for group in field_registry.get("available_field_groups") or []]
        + [{"字段组": group, "是否可用": "否"} for group in field_registry.get("missing_field_groups") or []]
    )
    metric_tree_rows = [
        {"指标层": "规模", "指标示例": "GMV / 销量 / 订单量 / 商品数 / 店铺数 / 类目数"},
        {"指标层": "结构", "指标示例": "商品结构 / 类目结构 / 店铺结构 / 品牌结构"},
        {"指标层": "转化", "指标示例": "点击率 / 加购率 / 支付转化率"},
        {"指标层": "库存履约", "指标示例": "库存 / 周转 / 履约率 / 发货时效"},
        {"指标层": "评价售后", "指标示例": "评分 / 差评 / 退款率 / 退货率 / 投诉"},
        {"指标层": "毛利成本", "指标示例": "毛利率 / 成本 / 广告费 / 平台费用 / 利润"},
    ]
    object_grain_rows = [
        {"对象粒度": "商品", "说明": "商品经营主对象"},
        {"对象粒度": "SKU", "说明": "规格层结构与履约复盘"},
        {"对象粒度": "类目", "说明": "类目经营结构与风险"},
        {"对象粒度": "店铺", "说明": "店铺承接与售后复盘"},
        {"对象粒度": "品牌", "说明": "品牌表现与口碑复核"},
        {"对象粒度": "供应商", "说明": "供应商/商家履约与毛利边界复核"},
    ]
    action_table_upper = _table("对象级行动表", action_rows[:15], "所有正式动作均来自电商对象决策注册表。")
    action_table_lower = _table("对象级行动表（续）", action_rows[15:30], "超过 30 行的对象动作继续进入附录。") if action_rows[15:30] else None
    seven_day_table = _table("7日经营动作表", seven_day_rows[:20], "每条动作必须带负责人、截止时间和验证标准。")
    backlog_table = _table("30日经营实验 backlog", backlog_rows[:20], "实验类型包括商品、流量、转化、库存、售后、店铺/供应商。")
    data_gap_rows = [
        {
            "优先级": ("P0" if idx < 4 else "P1" if idx < 8 else "P2"),
            "缺失字段组": group,
            "为什么重要": "该字段缺口会直接限制经营结论强度",
            "补齐后看什么": "补齐后可升级商品、类目、店铺、库存、履约或利润判断",
        }
        for idx, group in enumerate(field_registry.get("missing_field_groups") or [])
    ]

    sections = [
        _page_section(
            section_id="ecommerce_cover",
            title="封面与报告定位",
            business_question="当前这份报告的业务定位是什么？",
            core_finding=f"当前主报告定位为电商商品经营复盘，当前 report_mode 为 {field_registry.get('report_mode', '')}。",
            evidence="报告主链围绕商品、类目、店铺、品牌、供应商、交易、库存、履约、评价与售后展开。",
            boundary="流量、评价、加购、支付等字段只作为商品经营辅助指标，不改变主业务类型。",
            action_plan="先按电商经营口径看商品结构、交易转化、库存履约、售后口碑，再决定动作。",
        ),
        _page_section(
            section_id="ecommerce_management_summary",
            title="管理层摘要",
            business_question="当前最重要的经营结论与动作是什么？",
            core_finding=summary[0],
            evidence="；".join(summary[1:3]),
            boundary=summary[1],
            action_plan=summary[-1],
        ),
        _page_section(
            section_id="ecommerce_data_scope",
            title="数据范围与字段可用性",
            business_question="当前数据能支持哪些电商经营判断？",
            core_finding=f"当前可用字段组为 {', '.join(field_registry.get('available_field_groups') or [])}。",
            evidence=f"缺失字段组为 {', '.join(field_registry.get('missing_field_groups') or []) or '无'}。",
            boundary="所有电商模块只能读取电商字段可用性注册表判断字段边界。",
            action_plan="字段缺失章节必须明确写清不可判断内容与补字段方向。",
            tables=[_table("字段可用性", field_rows[:24])],
        ),
        _page_section(
            section_id="ecommerce_can_and_cannot_judge",
            title="当前能判断与不能判断的内容",
            business_question="当前哪些结论可以稳判，哪些必须压住？",
            core_finding="当前可以稳判商品结构、类目结构、店铺承接、库存履约边界、评价售后边界与毛利成本边界。",
            evidence="不能判断的内容会进入禁止误判清单，不再被正文强行输出。",
            boundary="缺毛利/成本、库存、履约、售后、评价、流量、转化、时间时，都禁止越权结论。",
            action_plan="先看禁止误判清单，再看对象级行动表。",
        ),
        _page_section(
            section_id="ecommerce_object_grain",
            title="核心对象粒度识别：商品、SKU、类目、店铺、品牌、供应商",
            business_question="当前电商数据的核心对象粒度是什么？",
            core_finding="当前主粒度围绕商品、SKU、类目、店铺、品牌与供应商展开。",
            evidence="对象粒度决定后续动作应由商品运营、类目负责人、店铺运营、采销或供应链来承接。",
            boundary="禁止把电商商品粒度误改成互联网运营用户/内容粒度。",
            action_plan="按对象粒度分别复核商品、类目、店铺、品牌、供应商。",
            tables=[_table("对象粒度识别", object_grain_rows)],
        ),
        _page_section(
            section_id="ecommerce_kpi_tree",
            title="电商经营指标体系",
            business_question="当前电商经营该用什么指标体系看盘？",
            core_finding="指标体系按规模、结构、转化、库存履约、评价售后、毛利成本组织。",
            evidence="不同字段组进入不同模块，避免把流量、库存、售后和利润混成一锅。",
            boundary="缺字段时，该指标层只能输出字段缺口和复核动作。",
            action_plan="围绕 KPI 树看整体盘面、对象差异和问题诊断。",
            tables=[_table("电商经营指标体系", metric_tree_rows)],
        ),
        _page_section("ecommerce_overview", "整体经营盘面", overview["business_question"], "；".join(overview["key_findings"]), str(overview["evidence"]), _boundary_text(field_registry, overview), _join(overview["recommended_actions"], default="补字段验证")),
        _page_section("ecommerce_gmv_order_mix", "GMV / 销量 / 订单结构", "GMV、销量与订单结构当前呈现什么分布？", "当前整体规模信号已经足以先做结构复盘。", str(overview["evidence"]), _boundary_text(field_registry, overview), "按 GMV、销量、订单量与客单价继续拆对象结构。"),
        _page_section("ecommerce_product_structure", "商品结构分析", product["business_question"], "；".join(product["key_findings"]), str(product["evidence"]), _boundary_text(field_registry, product), _join(product["recommended_actions"], default="商品结构复核")),
        _page_section("ecommerce_core_product", "核心商品候选", "哪些商品目前可视为核心商品候选？", f"{product_row.get('final_label', '核心商品候选待复核')}；动作：{product_row.get('final_action', '商品结构复核')}", product_row.get("evidence_summary", "当前依据商品结构、销售和售后代理指标识别候选对象。"), _join(product_row.get("missing_fields") or [], default="无明显缺口"), product_row.get("final_action", "商品结构复核")),
        _page_section("ecommerce_high_traffic_low_conversion", "高流量低转化商品", "哪些商品当前更像高流量低转化对象？", "若流量和转化字段具备，可优先识别高流量低转化商品。", str(product["evidence"]), _boundary_text(field_registry, product), "先做商品转化断点归因，再决定详情页或价格修复。"),
        _page_section("ecommerce_high_sales_high_aftersales", "高销量高售后商品", "哪些商品销售高但售后风险偏高？", "高销量高售后对象优先进入售后与口碑复核。", str(aftersales["evidence"]), _boundary_text(field_registry, aftersales), _join(aftersales["recommended_actions"], default="售后风险复核")),
        _page_section("ecommerce_low_sales_high_inventory", "低销量高库存商品", "哪些商品可能出现低销量高库存？", "库存与销量代理信号可用于识别供需错位风险。", str(inventory["evidence"]), _boundary_text(field_registry, inventory), _join(inventory["recommended_actions"], default="库存复核")),
        _page_section("ecommerce_category_review", "类目经营分析", category["business_question"], "；".join(category["key_findings"]), str(category["evidence"]), _boundary_text(field_registry, category), _join(category["recommended_actions"], default="类目复核")),
        _page_section("ecommerce_shop_review", "店铺/商家/供应商分析", shop["business_question"], "；".join(shop["key_findings"]), str(shop["evidence"]), _boundary_text(field_registry, shop), _join(shop["recommended_actions"], default="店铺/商家复核")),
        _page_section("ecommerce_brand_review", "品牌表现分析", "品牌当前能否稳定判断增长、口碑和转化？", f"{brand_row.get('final_label', '品牌待复核')}；动作：{brand_row.get('final_action', '品牌复核')}", brand_row.get("evidence_summary", "当前品牌层优先看类目、店铺与口碑代理信号。"), _join(brand_row.get("missing_fields") or [], default="无明显缺口"), brand_row.get("final_action", "品牌复核")),
        _page_section("ecommerce_price_promotion", "价格带与促销分析", price["business_question"], "；".join(price["key_findings"]), str(price["evidence"]), _boundary_text(field_registry, price), _join(price["recommended_actions"], default="价格促销复核")),
        _page_section("ecommerce_traffic_structure", "流量结构分析", "当前流量结构与商品承接当前能判断到哪一层？", "流量字段只服务商品经营辅助分析，不改变主业务类型。", str(product["evidence"]), _boundary_text(field_registry, product), "若缺流量字段，则只输出流量字段缺口。"),
        _page_section("ecommerce_funnel", "商品转化漏斗分析", funnel["business_question"], "；".join(funnel["key_findings"]), str(funnel["evidence"]), _boundary_text(field_registry, funnel), _join(funnel["recommended_actions"], default="漏斗断点归因")),
        _page_section("ecommerce_cart_favorite_pay", "加购、收藏与支付转化分析", "加购、收藏和支付转化里，当前最大损耗在哪里？", "当前优先复核加购、收藏、支付三段的损耗顺序。", str(funnel["evidence"]), _boundary_text(field_registry, funnel), "先做商品详情页、价格带与支付承接复核。"),
        _page_section("ecommerce_inventory", "库存与周转分析", inventory["business_question"], "；".join(inventory["key_findings"]), str(inventory["evidence"]), _boundary_text(field_registry, inventory), _join(inventory["recommended_actions"], default="库存复核")),
        _page_section("ecommerce_inventory_gap", "缺货、压货与库存字段缺口", "当前能否直接判断缺货、压货和库存周转？", "缺库存字段时，正文只能输出库存字段缺口，不能直接下补货或清仓动作。", str(inventory["evidence"]), _boundary_text(field_registry, inventory), "优先补库存、可售库存、周转字段后再判断供需关系。"),
        _page_section("ecommerce_fulfillment", "履约与物流分析", "履约与物流当前能否稳定判断？", "履约字段具备时可以复核发货与签收时效；缺字段时只能写履约缺口。", str(inventory["evidence"]), _boundary_text(field_registry, inventory), "先补发货、签收、履约率口径，再判断履约问题。"),
        _page_section("ecommerce_aftersales", "售后退款退货分析", aftersales["business_question"], "；".join(aftersales["key_findings"]), str(aftersales["evidence"]), _boundary_text(field_registry, aftersales), _join(aftersales["recommended_actions"], default="售后风险复核")),
        _page_section("ecommerce_review", "评价与口碑分析", "当前评价与口碑是否可稳定判断？", "评价字段具备时可以识别口碑待复核对象；缺评价字段时只能写评价缺口。", str(aftersales["evidence"]), _boundary_text(field_registry, aftersales), "先做差评、评分和问大家复核。"),
        _page_section("ecommerce_bad_review", "差评与投诉风险", "哪些对象更像差评或投诉风险对象？", "高销量高差评、高退款与低评分高曝光对象优先进入风险复核。", str(aftersales["evidence"]), _boundary_text(field_registry, aftersales), "做售后、口碑与商品体验归因。"),
        _page_section("ecommerce_margin_profit", "毛利、成本与利润分析或字段缺口", margin["business_question"], "；".join(margin["key_findings"]), str(margin["evidence"]), _boundary_text(field_registry, margin), _join(margin["recommended_actions"], default="毛利复核")),
        _page_section("ecommerce_promotion_impact", "大促/活动影响分析", "活动与大促当前能否判断其经营影响？", "大促和活动需要同时结合价格、交易和时间字段看，不得脱离字段边界写结论。", str(price["evidence"]), _join(["promotion_fields" if not field_registry.get("has_promotion_fields") else ""], default="无明显缺口"), "优先复核活动价、补贴和活动承接表现。"),
        _page_section("ecommerce_anomaly", "异常波动分析", anomaly["business_question"], "；".join(anomaly["key_findings"]), str(anomaly["evidence"]), _boundary_text(field_registry, anomaly), _join(anomaly["recommended_actions"], default="异常复核")),
        _page_section("ecommerce_lifecycle", "商品生命周期分析", lifecycle["business_question"], "；".join(lifecycle["key_findings"]), str(lifecycle["evidence"]), _boundary_text(field_registry, lifecycle), _join(lifecycle["recommended_actions"], default="生命周期复核")),
        _page_section("ecommerce_management_diagnosis", "经营问题诊断", diagnosis["business_question"], "；".join(diagnosis["key_findings"][:5]), "问题诊断页聚合商品、类目、店铺、库存、售后和毛利缺口。", _boundary_text(field_registry, diagnosis), _join(diagnosis["recommended_actions"], default="问题诊断复核")),
        _page_section("ecommerce_action_table", "对象级行动表", "当前对象级最终动作是什么？", "对象级行动表是正文唯一正式动作源。", "所有最终动作都来自电商对象决策注册表。", "正文、摘要、图注和路线图都只能读取对象决策注册表。", "按优先级派单执行。", tables=[action_table_upper]),
        *(
            [
                _page_section("ecommerce_action_table_more", "对象级行动表（续）", "如果对象表较长，剩余对象动作是什么？", "续表保留其余对象动作。", "动作字段与主表一致。", "仍然只读对象决策注册表。", "继续按优先级执行。", tables=[action_table_lower]),
            ]
            if action_table_lower
            else []
        ),
        _page_section("ecommerce_7day_actions", "7日经营动作表", "未来 7 天谁做什么？", "7 日动作表用于短周期派单。", "动作类型仅允许补字段、复核、归因、修复、小范围验证。", "不得出现直接加码、直接砍货、直接清仓等越权动作。", "按 T+3/T+5/T+7/T+14 执行。", tables=[seven_day_table]),
        _page_section("ecommerce_30day_backlog", "30日经营实验 backlog", "未来 30 天验证哪些经营实验？", "30 日 backlog 用于商品、流量、转化、库存、售后和店铺实验。", "实验必须写清核心指标、护栏指标、样本要求和失败后处理。", "缺字段时只保留验证型实验，不写拍板结论。", "按实验编号推进。", tables=[backlog_table]),
        _page_section("ecommerce_forbidden_judgement", "禁止误判清单", "当前数据下哪些结论不能得出？", "禁止误判清单用于明确字段边界。", "缺毛利/成本、库存、履约、售后、评价、流量、转化、时间时，都有明确禁断结论。", "这些禁断结论不得出现在正文。", "先补字段，再升级结论。", tables=[_table("禁止误判清单", forbidden_rows[:15])]),
        _page_section("ecommerce_data_gap_priority", "数据补充优先级", "当前最需要先补哪些字段？", "字段补充优先级按 P0/P1/P2 排列。", "字段缺口会直接限制利润、库存、履约、售后、口碑、漏斗和趋势判断。", "先补高价值字段，再做强动作。", "按优先级补齐并复核。", tables=[_table("数据补充优先级", data_gap_rows[:15])]),
        _page_section("ecommerce_roadmap", "管理层行动路线图", "管理层接下来怎么排动作顺序？", "路线图按商品、类目、店铺、库存、售后和毛利问题组织。", "短期先补字段和复核，中期做实验与小范围验证。", "严禁越过字段边界直接拍板。", "按 T+1/T+3/T+7/T+14/T+30 推进。"),
        _page_section("ecommerce_appendix_note", "附录：字段解释与口径说明", "附录保留什么？", "附录只保留字段解释、模块结果、对象决策注册表和实验明细。", "主报告必须能独立阅读，不依赖附件才能看懂核心结论。", "分析附录放 analyst_appendix.xlsx。", "需要时继续下钻分析。"),
    ]

    return {
        "title": title,
        "dataset_name": report["dataset_name"],
        "sheet_name": report["sheet_name"],
        "report_id": report["report_id"],
        "generated_at": report["generated_at"],
        "report_language": report.get("report_language", "zh-CN"),
        "report_lens": report.get("report_lens", "procurement_sales_review"),
        "business_profile": "ecommerce_product_operations_report",
        "executive_summary": summary,
        "sections": sections,
        "strategy_management_ids": [str(section.get("id") or "") for section in sections],
        "field_registry": field_registry,
    }


def build_ecommerce_appendix_variant(report: dict[str, Any]) -> dict[str, Any]:
    field_registry = report.get("ecommerce_field_availability_registry") or {}
    semantic_map = report.get("ecommerce_field_semantic_map") or {}
    modules = report.get("product_operations_analysis_modules") or {}
    registry_payload = report.get("ecommerce_object_decision_registry") or {}
    rows = list(registry_payload.get("rows") or [])
    sections = [
        {
            "id": "appendix_field_semantics",
            "title": "字段解释与口径说明",
            "summary": "附录保留字段语义、字段组和业务口径说明。",
            "bullets": ["主报告已压缩为管理层版，详细字段解释留在附录中。"],
            "tables": [
                _table(
                    "ecommerce_field_semantic_map",
                    [
                        {
                            "字段": row.get("field_name", ""),
                            "业务含义": row.get("guessed_business_meaning", ""),
                            "字段组": row.get("field_group", ""),
                            "可用于": _join(list(row.get("usable_for") or []), default="无"),
                            "不可用于": _join(list(row.get("not_usable_for") or []), default="无"),
                        }
                        for row in semantic_map.get("rows", [])
                    ],
                )
            ],
            "charts": [],
        },
        {
            "id": "appendix_modules",
            "title": "模块结果附录",
            "summary": "附录保留所有电商模块结果明细。",
            "bullets": ["模块结果明细用于分析师复核，不再进入管理层正文。"],
            "tables": [
                _table(
                    "module_results",
                    [
                        {
                            "模块": name,
                            "问题": payload.get("business_question", ""),
                            "结论类型": payload.get("conclusion_type", ""),
                            "置信度": payload.get("confidence_level", ""),
                            "缺失字段": _join(list(payload.get("missing_fields") or []), default="无"),
                        }
                        for name, payload in modules.items()
                    ],
                )
            ],
            "charts": [],
        },
        {
            "id": "appendix_registry",
            "title": "对象决策注册表附录",
            "summary": "附录保留 ecommerce_object_decision_registry 与 action table 明细。",
            "bullets": ["所有最终动作都从 registry 收口。"],
            "tables": [
                _table("ecommerce_object_decision_registry", rows),
                _table("ecommerce_action_table", report.get("ecommerce_action_table") or []),
            ],
            "charts": [],
        },
    ]
    return {
        "title": f"{report.get('title', '电商经营报告')}（analyst_appendix）",
        "dataset_name": report["dataset_name"],
        "sheet_name": report["sheet_name"],
        "report_id": report["report_id"],
        "generated_at": report["generated_at"],
        "report_language": report.get("report_language", "zh-CN"),
        "report_lens": report.get("report_lens", "procurement_sales_review"),
        "business_profile": "ecommerce_product_operations_report",
        "executive_summary": ["本附录保留字段语义、模块结果、对象决策注册表和行动表明细。"],
        "sections": sections,
    }


def build_ecommerce_full_variant(
    report: dict[str, Any],
    management_variant: dict[str, Any],
    appendix_variant: dict[str, Any],
) -> dict[str, Any]:
    return {
        **report,
        "title": management_variant.get("title") or report.get("title") or "电商商品经营复盘报告",
        "executive_summary": list(management_variant.get("executive_summary") or []),
        "sections": [
            *(management_variant.get("sections") or []),
            *(appendix_variant.get("sections") or []),
        ],
        "business_profile": "ecommerce_product_operations_report",
    }
