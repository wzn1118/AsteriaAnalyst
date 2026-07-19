from __future__ import annotations

from app.services.independent_industry_research_chain import (
    evaluate_industry_research_quality_gate,
)


def _valid_report_markdown() -> str:
    return """
# 行业研究报告：美妆个护电商

## 行业定位与研究边界
- chapter_judgement: 当前样本更像美妆个护零售电商的订单经营窗口，行业定位只用于解释交易结构、规则机制和 benchmark 边界。
- key_evidence: [S001] 国家统计局公开披露社会消费品零售总额和网上零售增长背景。
- data_relation: 当前上传数据对象粒度为 sku_or_product，因此行业定位必须与商品、店铺和交易结构一起解释。
- non_extrapolation_boundary: 外部资料不能替代当前上传数据的经营证据。
- manual_confirmation_needed: 当前数据主要来自哪个平台或渠道？

## 数据所反映的业务场景
- chapter_judgement: 当前上传数据主要反映商品、SKU、店铺层的交易与结构信号。
- key_evidence: [S001] 国家统计局公开披露宏观零售与线上消费背景。
- data_relation: 当前数据可直接支持交易结构和供给结构研究。
- non_extrapolation_boundary: 当前数据不能直接支持对象级经营拍板。
- manual_confirmation_needed: Revenue / GMV / FreightCost 在当前业务里各自代表什么口径？

## 行业背景
- chapter_judgement: 行业背景应围绕零售电商交易结构、市场结构与经营驱动来理解。
- key_evidence: [S001] 国家统计局公开披露宏观消费与零售结构背景。
- data_relation: 当前上传数据主要呈现交易与结构信号。
- non_extrapolation_boundary: 行业背景只提供外部环境解释。
- manual_confirmation_needed: 当前数据主要来自哪个平台或渠道？

## 平台机制
- chapter_judgement: 平台机制部分应解释规则、履约与评价治理边界。
- key_evidence: [S004] 电子商务法明确平台经营者责任、规则披露和售后边界。
- data_relation: 当前上传数据中的交易与转化指标受平台规则影响。
- non_extrapolation_boundary: 平台机制资料只能解释规则约束与背景。
- manual_confirmation_needed: 当前平台名称仍需人工确认最终应引用哪一个具体平台规则页。

## 市场结构与竞争格局
- chapter_judgement: 市场结构与竞争格局应围绕类目、店铺和供给侧分层展开。
- key_evidence: [S001] 国家统计局公开披露行业规模背景，可用于说明比较边界。
- data_relation: 当前上传数据已显示商品和店铺的结构线索。
- non_extrapolation_boundary: 外部市场结构和竞争格局资料只能作为背景比较。
- manual_confirmation_needed: 当前业务更偏平台零售经营、采销复盘，还是站外流量投放？

## 指标口径与 benchmark 可比性
- chapter_judgement: GMV、Revenue、FreightCost、order_count、rating、conversion、sales_amount、sales_volume 和 ROI 都需要先统一定义。
- key_evidence: [S001] 国家统计局公开披露行业背景，可用于说明 benchmark 的时间和统计边界。
- key_evidence: [GMV] 当前样本与行业公开 benchmark 在平台、时间窗和样本覆盖上存在差异，因此最多做方向参考。
- data_relation: 当前链已覆盖 GMV、Revenue、FreightCost、order_count、rating、conversion、sales_amount、sales_volume 和 ROI。
- non_extrapolation_boundary: benchmark 解释必须同时写明时间区间差异、平台差异、样本差异和统计口径差异。
- manual_confirmation_needed: 请确认 benchmark 只能做方向参考，还是已经具备统一的平台、时间区间和样本口径。

## 成本/利润/履约/转化边界
- chapter_judgement: 当前数据中的成本、利润、履约与转化口径并不天然完整。
- key_evidence: [FreightCost] FreightCost 只是成本片段，不等于完整履约或总成本。
- key_evidence: [ROI] 当前数据缺少完整收益/成本归因口径，ROI 无法成立，因此不能直接比较。
- data_relation: 当前数据已暴露出交易、评分和销量信号。
- non_extrapolation_boundary: 这些口径边界只能解释为什么当前不能升级为强经营判断。
- manual_confirmation_needed: 请确认利润、库存、ROI 或转化分母等关键字段是否齐全。

## 风险与监管环境
- chapter_judgement: 风险与监管环境应被视为外部背景约束。
- key_evidence: [S002] 平台监管公开资料可用于补监管、消费者权益和平台治理边界。
- data_relation: 当前上传数据只能提示这些风险与当前行业和对象粒度相关。
- non_extrapolation_boundary: 风险章节只构成背景提醒。
- manual_confirmation_needed: 当前数据主要来自哪个平台或渠道？

## 对主报告可提供的背景支持
- chapter_judgement: 行业研究链可以为主报告提供行业背景、平台机制、指标口径、benchmark 边界和风险解释。
- key_evidence: [S001] 国家统计局公开披露宏观消费和零售结构背景。
- data_relation: 当前上传数据已经限定了对象粒度与可用指标族。
- non_extrapolation_boundary: 外部资料只能做背景支持，不能替代主报告的数据证据和对象级动作判断。
- manual_confirmation_needed: 当前业务更偏平台零售经营、采销复盘，还是站外流量投放？

## 当前不能支持的经营判断
- chapter_judgement: 当前不能支持的判断主要集中在利润、ROI、对象级加码/淘汰和跨平台强 benchmark。
- key_evidence: [unsupported] 不得把当前数据派生指标写成行业 benchmark。
- data_relation: 这些限制直接来自当前数据的字段完整度、对象粒度和口径边界。
- non_extrapolation_boundary: 当利润、库存、转化分母、平台名称等关键口径不齐全时，任何对象级经营判断都必须先降级为待验证问题。
- manual_confirmation_needed: 请确认利润、库存、ROI 或转化分母等关键字段是否齐全。

## 来源说明
- chapter_judgement: 本报告正文使用的都是带 source_id 的来源事实卡。
- key_evidence: [S001] 国家统计局数据查询 / 国家统计局 / 政府或监管公开资料
- data_relation: 来源只用于补外部背景、平台规则、benchmark 和风险边界。
- non_extrapolation_boundary: 若来源只能提供宏观背景或监管边界，它就不能被提升为当前对象级经营证据。
- manual_confirmation_needed: 当前平台名称仍需人工确认最终应引用哪一个具体平台规则页。
""".strip()


def _valid_sources() -> list[dict]:
    return [
        {
            "source_id": "S001",
            "title": "国家统计局数据查询",
            "publisher": "国家统计局",
            "url": "https://data.stats.gov.cn/",
            "publish_date": "2025-03-17",
            "credibility": "high",
            "source_type": "政府或监管公开资料",
            "source_level": "page_fact",
            "verification_status": "verified_page_fact",
            "claim_summary": "公开披露宏观消费与线上零售增长背景。",
            "atomic_facts": [
                "国家统计局公开披露社会消费品零售总额和网上零售增长背景。",
            ],
            "facts": [
                "国家统计局公开披露社会消费品零售总额和网上零售增长背景。",
            ],
            "usable_for_sections": ["行业背景", "市场结构与竞争格局", "对主报告可提供的背景支持"],
            "not_usable_for_sections": ["当前对象级经营判断"],
        }
    ]


def _valid_benchmark_artifacts() -> dict:
    return {
        "benchmark_metric_registry": [{"metric_id": "GMV"}],
        "benchmark_comparability_matrix": [
            {
                "metric_id": "GMV",
                "directly_comparable": False,
                "why_not_directly_comparable": "平台、时间窗和样本覆盖存在差异。",
            }
        ],
        "platform_difference_table": [{"difference_dimension": "平台差异"}],
        "metric_definition_comparison": [{"metric_id": "GMV"}],
    }


def test_industry_research_requires_real_source_facts():
    gate, score = evaluate_industry_research_quality_gate(
        report_markdown=_valid_report_markdown().replace("key_evidence:", "evidence_list:"),
        sources=_valid_sources(),
        benchmark_artifacts=_valid_benchmark_artifacts(),
        boundary_check_payload={},
        manual_confirmation_items=["确认平台规则页"],
        source_fact_rows=[],
        insufficient_sources=False,
    )
    assert gate["passed"] is False
    assert "body_missing_source_facts" in gate["fail_items"]
    assert score["passed"] is False


def test_industry_research_fails_on_placeholder_text():
    gate, _ = evaluate_industry_research_quality_gate(
        report_markdown=_valid_report_markdown() + "\n- chapter_judgement: unclear_business_model ???",
        sources=_valid_sources(),
        benchmark_artifacts=_valid_benchmark_artifacts(),
        boundary_check_payload={},
        manual_confirmation_items=["确认平台规则页"],
        source_fact_rows=[{"来源事实": "x"}],
        insufficient_sources=False,
    )
    assert gate["passed"] is False
    assert any(item.startswith("placeholder_or_raw_uncertainty_text_present") for item in gate["fail_items"])


def test_industry_research_requires_benchmark_tables():
    gate, _ = evaluate_industry_research_quality_gate(
        report_markdown=_valid_report_markdown(),
        sources=_valid_sources(),
        benchmark_artifacts={
            "benchmark_metric_registry": [],
            "benchmark_comparability_matrix": [],
            "platform_difference_table": [],
            "metric_definition_comparison": [],
        },
        boundary_check_payload={},
        manual_confirmation_items=["确认平台规则页"],
        source_fact_rows=[{"来源事实": "x"}],
        insufficient_sources=False,
    )
    assert gate["passed"] is False
    assert "benchmark_tables_missing" in gate["fail_items"]


def test_industry_research_requires_manual_confirmation_checklist():
    gate, _ = evaluate_industry_research_quality_gate(
        report_markdown=_valid_report_markdown(),
        sources=_valid_sources(),
        benchmark_artifacts=_valid_benchmark_artifacts(),
        boundary_check_payload={},
        manual_confirmation_items=[],
        source_fact_rows=[{"来源事实": "x"}],
        insufficient_sources=False,
    )
    assert gate["passed"] is False
    assert "manual_confirmation_checklist_missing" in gate["fail_items"]


def test_industry_research_body_must_consume_sources():
    markdown = _valid_report_markdown().replace("[S001]", "[Source-Only]").replace("[S004]", "[Source-Only]")
    gate, _ = evaluate_industry_research_quality_gate(
        report_markdown=markdown,
        sources=_valid_sources(),
        benchmark_artifacts=_valid_benchmark_artifacts(),
        boundary_check_payload={},
        manual_confirmation_items=["确认平台规则页"],
        source_fact_rows=[{"来源事实": "x"}],
        insufficient_sources=False,
    )
    assert gate["passed"] is False
    assert "source_list_not_consumed_in_body" in gate["fail_items"]


def test_industry_research_fails_on_pending_platform_phrase_in_body():
    markdown = _valid_report_markdown() + "\n## 平台机制\n- chapter_judgement: 当前平台为平台待确认。"
    gate, _ = evaluate_industry_research_quality_gate(
        report_markdown=markdown,
        sources=_valid_sources(),
        benchmark_artifacts=_valid_benchmark_artifacts(),
        boundary_check_payload={},
        manual_confirmation_items=["确认平台规则页"],
        source_fact_rows=[{"来源事实": "x"}],
        insufficient_sources=False,
    )
    assert gate["passed"] is False
    assert any(item.startswith("placeholder_or_raw_uncertainty_text_present") for item in gate["fail_items"])


def test_industry_research_fails_when_body_depends_on_lead_only_source():
    sources = _valid_sources() + [
        {
            "source_id": "S099",
            "title": "行业协会线索",
            "publisher": "行业协会",
            "url": "",
            "publish_date": "待补充",
            "credibility": "medium",
            "source_type": "行业协会报告",
            "source_level": "lead_only",
            "verification_status": "lead_only",
            "claim_summary": "当前仅拿到来源线索。",
            "atomic_facts": ["当前仅定位到来源线索，尚未落到可核验的具体报告、规则页或法规条文页。"],
            "facts": ["当前仅定位到来源线索，尚未落到可核验的具体报告、规则页或法规条文页。"],
            "usable_for_sections": ["市场结构与竞争格局"],
            "not_usable_for_sections": ["当前对象级经营判断"],
        }
    ]
    markdown = _valid_report_markdown().replace("## 来源说明", "- key_evidence: [S099] 当前仅拿到行业协会线索。\n\n## 来源说明")
    gate, _ = evaluate_industry_research_quality_gate(
        report_markdown=markdown,
        sources=sources,
        benchmark_artifacts=_valid_benchmark_artifacts(),
        boundary_check_payload={},
        manual_confirmation_items=["确认平台规则页"],
        source_fact_rows=[{"来源事实": "x"}],
        insufficient_sources=False,
    )
    assert gate["passed"] is False
    assert "body_depends_on_non_fact_sources" in gate["fail_items"]
