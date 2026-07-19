from __future__ import annotations

import csv
import html
import json
import math
import os
import re
import shutil
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any


REPORT_ID = "980002b32f89"
JOB_ID = "codex-pipeline-2f10600298ed"

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.internet_ops_visual_render_service import (  # noqa: E402
    CHANNEL_SOURCE_AARRR_DETAIL,
    CHANNEL_SOURCE_AARRR_TOPN,
    build_channel_source_aarrr_detail,
    ensure_point_ids_records,
    render_aarrr_all_pages,
    render_aarrr_small_multiples,
    render_labeled_scatter,
    select_channel_source_aarrr_topn,
)
from app.services.internet_ops_management_brief_service import (  # noqa: E402
    BRIEF_HTML_NAME,
    BRIEF_MD_NAME,
    BRIEF_PDF_NAME,
    CHANNEL_SOURCE_KPI_CANONICAL_CSV_NAME,
    CHANNEL_SOURCE_KPI_CANONICAL_JSON_NAME,
    DERIVED_METRIC_DIAGNOSIS_CARDS_NAME,
    EXECUTIVE_ACTION_RULES_JSON_NAME,
    MANAGEMENT_QUADRANT_INDEX_CSV_NAME,
    MANAGEMENT_QUADRANT_INDEX_JSON_NAME,
    MANAGEMENT_THRESHOLDS_JSON_NAME,
    TABLE_READING_CARDS_NAME,
    build_internet_ops_management_brief_markdown,
    ensure_ops_management_fact_contracts,
    render_ops_table_reading_cards_markdown,
    render_management_brief_html,
    validate_management_brief,
    write_ops_derived_metric_diagnosis_cards,
)

REPORT_ROOT = REPO_ROOT / "workspace" / "storage" / "reports" / f"smart-report-{REPORT_ID}"
JOB_ROOT = REPORT_ROOT / "codex_premium" / "internet_ops_shadow" / JOB_ID
BUNDLE_ROOT = REPORT_ROOT / "internet_ops_cli_shadow_bundle"
ASSET_ROOT = JOB_ROOT / "source_visual_assets"

ROOT_MD = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow.md"
ROOT_HTML = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow.html"
ROOT_CSS = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow.css"
ROOT_PDF = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow.pdf"
ROOT_MD_BRIEF = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow_management_brief.md"
ROOT_HTML_BRIEF = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow_management_brief.html"
ROOT_PDF_BRIEF = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow_management_brief.pdf"
ROOT_TABLE_READING_CARDS = REPORT_ROOT / f"{REPORT_ID}-ops_table_reading_cards.json"
ROOT_CHART_NARRATIVE_SECTIONS = REPORT_ROOT / f"{REPORT_ID}-ops_chart_narrative_sections.json"
ROOT_MANAGEMENT_QUADRANT_INDEX_JSON = REPORT_ROOT / f"{REPORT_ID}-ops_management_quadrant_index.json"
ROOT_MANAGEMENT_QUADRANT_INDEX_CSV = REPORT_ROOT / f"{REPORT_ID}-ops_management_quadrant_index.csv"
ROOT_DERIVED_METRIC_DIAGNOSIS_CARDS = REPORT_ROOT / f"{REPORT_ID}-ops_derived_metric_diagnosis_cards.json"
ROOT_CHANNEL_SOURCE_KPI_CANONICAL_JSON = REPORT_ROOT / f"{REPORT_ID}-ops_channel_source_kpi_canonical.json"
ROOT_CHANNEL_SOURCE_KPI_CANONICAL_CSV = REPORT_ROOT / f"{REPORT_ID}-ops_channel_source_kpi_canonical.csv"
ROOT_MANAGEMENT_THRESHOLDS_JSON = REPORT_ROOT / f"{REPORT_ID}-ops_management_thresholds.json"
ROOT_EXECUTIVE_ACTION_RULES_JSON = REPORT_ROOT / f"{REPORT_ID}-ops_executive_action_rules.json"
ROOT_MD_WITH_TABLES = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow_with_tables.md"
ROOT_HTML_WITH_TABLES = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow_with_tables.html"
ROOT_PDF_WITH_TABLES = REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow_with_tables.pdf"

JOB_MD = JOB_ROOT / "05_report.md"
JOB_HTML = JOB_ROOT / "06_report.html"
JOB_CSS = JOB_ROOT / "06_report.css"
JOB_PDF = JOB_ROOT / "07_report.pdf"
JOB_MD_BRIEF = JOB_ROOT / BRIEF_MD_NAME
JOB_HTML_BRIEF = JOB_ROOT / BRIEF_HTML_NAME
JOB_PDF_BRIEF = JOB_ROOT / BRIEF_PDF_NAME
JOB_TABLE_READING_CARDS = JOB_ROOT / TABLE_READING_CARDS_NAME
JOB_CHART_NARRATIVE_SECTIONS = JOB_ROOT / "ops_chart_narrative_sections.json"
JOB_MANAGEMENT_QUADRANT_INDEX_JSON = JOB_ROOT / MANAGEMENT_QUADRANT_INDEX_JSON_NAME
JOB_MANAGEMENT_QUADRANT_INDEX_CSV = JOB_ROOT / MANAGEMENT_QUADRANT_INDEX_CSV_NAME
JOB_DERIVED_METRIC_DIAGNOSIS_CARDS = JOB_ROOT / DERIVED_METRIC_DIAGNOSIS_CARDS_NAME
JOB_MD_WITH_TABLES = JOB_ROOT / "05_report_with_tables.md"
JOB_HTML_WITH_TABLES = JOB_ROOT / "06_report_with_tables.html"
JOB_PDF_WITH_TABLES = JOB_ROOT / "07_report_with_tables.pdf"

BUNDLE_HTML = BUNDLE_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow.html"
BUNDLE_HTML_BRIEF = BUNDLE_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow_management_brief.html"
BUNDLE_CSS = BUNDLE_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow.css"
BUNDLE_ASSET_ROOT = BUNDLE_ROOT / "source_visual_assets"


FIELD_LABELS = {
    "date": "日期",
    "channel": "渠道",
    "traffic_source": "流量来源",
    "city_tier": "城市层级",
    "user_segment": "用户分层",
    "content_category": "内容类型",
    "product_module": "产品模块",
    "campaign": "活动",
    "time_window": "时间窗口",
    "sample_size": "样本量",
    "impressions": "曝光量",
    "clicks": "点击量",
    "registrations": "注册量",
    "activations": "激活量",
    "paid_users": "付费用户数",
    "revenue": "收入",
    "operating_cost": "运营成本",
    "contribution_margin": "贡献毛利",
    "retention_d7": "7日留存率",
    "nps": "口碑净推荐值（NPS）",
    "CTR": "点击率（CTR）",
    "点击到注册率": "点击到注册率",
    "注册到激活率": "注册到激活率",
    "激活到付费率": "激活到付费率",
    "每付费用户收入": "每付费用户收入",
    "毛利率": "毛利率",
    "roi": "真实投放回报（roi）",
    "cac": "获客成本（cac）",
    "组合": "组合",
    "象限": "象限",
    "建议动作": "建议动作",
    "效率分": "效率分",
    "对象组合": "对象组合",
    "阶段": "阶段",
    "派生率": "派生率",
    "分子": "分子",
    "分母": "分母",
    "止损原因": "止损原因",
    "样本数": "样本数",
    "字段名": "字段名",
    "中文名称": "中文名称",
    "字段类型": "字段类型",
    "是否存在": "是否存在",
    "非空率": "非空率",
    "样本值": "样本值",
    "参与派生指标": "参与派生指标",
    "主报告用途": "主报告用途",
    "覆盖值": "覆盖值",
    "点击率": "点击率",
    "点击到付费率": "点击到付费率",
    "注册成本": "注册成本",
    "激活成本": "激活成本",
    "成本占比": "成本占比",
    "毛利占比": "毛利占比",
    "收入占比": "收入占比",
    "付费用户占比": "付费用户占比",
    "预算效率": "预算效率",
    "留存质量分": "留存质量分",
    "口碑质量分": "口碑质量分",
    "增长质量分": "增长质量分",
    "CPM": "千次曝光成本（CPM）",
    "CPC": "单次点击成本（CPC）",
    "ROI": "兼容投放回报（ROI）",
    "边际 roi 代理": "边际 roi 代理",
    "边际 CAC 代理": "边际 CAC 代理",
}


CHART_TITLES = {
    "ops_aarrr_derived_funnel_rates.csv": "增长漏斗派生率图（AARRR）",
    "ops_channel_source_aarrr_detail.csv": "渠道 × 流量来源 AARRR 全量组合明细",
    "ops_channel_source_aarrr_topn_small_multiples.csv": "Top12 渠道 × 流量来源 AARRR 差异图组",
    "ops_anomaly_stoploss_reason_chart.csv": "异常止损派生原因图",
    "ops_channel_source_derived_heatmap.csv": "渠道 × 流量来源派生指标热力图",
    "ops_content_campaign_conversion_matrix.csv": "内容类型 × 活动承接矩阵",
    "ops_cost_margin_share_matrix.csv": "成本占比 × 毛利占比矩阵",
    "ops_ctr_cpc_cpm_efficiency.csv": "点击率 × 单次点击成本 × 千次曝光成本获客效率图（CTR / CPC / CPM）",
    "ops_derived_metric_matrix.csv": "派生指标矩阵图",
    "ops_full_field_coverage_matrix.csv": "全字段覆盖矩阵",
    "ops_paid_users_revenue_bubble.csv": "付费用户 × 收入承接气泡图",
    "ops_product_campaign_monetization_matrix.csv": "产品模块 × 活动商业化矩阵",
    "ops_retention_nps_quality_quadrant.csv": "留存 × 口碑净推荐值质量象限图（NPS）",
    "ops_roi_cac_quadrant.csv": "真实投放回报 × 获客成本四象限图（roi / cac）",
    "ops_time_window_derived_trends.csv": "时间窗口派生指标趋势图",
    "ops_user_city_quality_matrix.csv": "用户分层 × 城市层级质量矩阵",
}

POINT_MAPPING_CSV_NAMES = {
    "ops_cost_margin_share_matrix.csv",
    "ops_ctr_cpc_cpm_efficiency.csv",
    "ops_paid_users_revenue_bubble.csv",
    "ops_retention_nps_quality_quadrant.csv",
    "ops_roi_cac_quadrant.csv",
}

AARRR_SPECIAL_CSV_NAMES = {
    "ops_aarrr_derived_funnel_rates.csv",
    "ops_channel_source_aarrr_detail.csv",
    "ops_channel_source_aarrr_topn_small_multiples.csv",
}


CHART_EXPLANATIONS = {
    "ops_aarrr_derived_funnel_rates.csv": "这张图解释 AARRR 漏斗每一步的派生率，配表保留阶段、分子和分母，方便复核每个转化率不是凭空估算。",
    "ops_channel_source_aarrr_detail.csv": "这张表是渠道 × 流量来源组合级 AARRR 权威明细，保留每个组合的阶段规模、关键转化率、收入成本和质量字段。",
    "ops_channel_source_aarrr_topn_small_multiples.csv": "这张小倍图展示 Top12 渠道 × 流量来源组合的规模与转化差异，配表保留每个入选组合的阶段规模、转化率和入选原因。",
    "ops_anomaly_stoploss_reason_chart.csv": "这张图解释止损原因分布，配表保留每类异常原因的样本数，支持 Day 1 止损对象追溯。",
    "ops_channel_source_derived_heatmap.csv": "这张热力图用于比较渠道 × 流量来源的投放效率，配表展开全部规模、成本、收入、留存和派生效率字段。",
    "ops_content_campaign_conversion_matrix.csv": "这张矩阵用于检查内容类型 × 活动承接，配表展开全部漏斗和财务派生字段，避免只看颜色不看口径。",
    "ops_cost_margin_share_matrix.csv": "这张矩阵用于比较成本占比与毛利占比，配表保留每个对象的成本、毛利、占比和效率字段。",
    "ops_ctr_cpc_cpm_efficiency.csv": "这张图用于解释 CTR / CPC / CPM 的获客效率关系，配表保留全量效率字段与经营规模字段。",
    "ops_derived_metric_matrix.csv": "这张矩阵是派生指标总览，配表保留每个组合的漏斗、质量、roi、cac、象限和动作字段。",
    "ops_full_field_coverage_matrix.csv": "这张矩阵说明 24 个源字段是否被使用，配表保留字段名、中文名、类型、非空率和主报告用途。",
    "ops_paid_users_revenue_bubble.csv": "这张气泡图解释付费用户与收入承接，配表保留产品模块、活动和全部商业化派生字段。",
    "ops_product_campaign_monetization_matrix.csv": "这张矩阵用于检查产品模块 × 活动商业化承接，配表保留全部收入、成本、毛利和效率字段。",
    "ops_retention_nps_quality_quadrant.csv": "这张象限图解释留存与口碑质量，配表保留用户分层、城市层级及全部质量/效率字段。",
    "ops_roi_cac_quadrant.csv": "这张象限图解释投放回报与获客成本的取舍，配表保留渠道、流量来源、漏斗规模、收入成本、质量效率、象限和动作字段。",
    "ops_time_window_derived_trends.csv": "这张趋势图用于看时间窗口内派生指标变化，配表保留每个时间窗口的全量趋势字段。",
    "ops_user_city_quality_matrix.csv": "这张矩阵用于比较用户分层 × 城市层级，配表保留全部漏斗、质量、收入成本和效率字段。",
}


def _chart_title(csv_name: str) -> str:
    return CHART_TITLES.get(csv_name, Path(csv_name).stem)


def _chart_type_from_name(csv_name: str) -> str:
    name = csv_name.lower()
    if "quadrant" in name:
        return "象限图"
    if "bubble" in name:
        return "气泡图"
    if "heatmap" in name or "matrix" in name:
        return "矩阵/热力图"
    if "trend" in name:
        return "趋势图"
    if "funnel" in name or "aarrr" in name:
        return "漏斗图"
    if "reason" in name:
        return "原因分布图"
    return "派生图"


def _chart_how_to_read(csv_name: str) -> str:
    chart_type = _chart_type_from_name(csv_name)
    if chart_type == "象限图":
        return "先看对象落在哪个象限，再结合坐标值和对象规模判断加码、提效、验证或止损，不要只看点的位置。"
    if chart_type == "气泡图":
        return "先读横轴和纵轴的业务含义，再用气泡大小判断规模权重，最后回到配表核对成本、收入、留存等完整字段。"
    if chart_type == "矩阵/热力图":
        return "先按横纵维度定位对象组合，再看颜色深浅代表的派生指标强弱，最后用配表确认具体数值和字段口径。"
    if chart_type == "趋势图":
        return "沿时间窗口看方向、拐点和断层，再用配表里的边际 roi / 边际 CAC 代理判断是否继续加码。"
    if chart_type == "漏斗图":
        return "按漏斗阶段从上到下看转化率，重点核对每一步的分子和分母，避免把口径不同的转化率混用。"
    return "先读图形呈现的排序或分布，再回到下方全量配表核对每个对象的完整字段。"


def _chart_watch_points(csv_name: str, headers: list[str]) -> str:
    preferred = [
        "样本量",
        "曝光",
        "点击",
        "注册",
        "激活",
        "付费用户",
        "收入",
        "运营成本",
        "贡献毛利",
        "点击率",
        "点击到注册率",
        "激活到付费率",
        "毛利率",
        "roi",
        "cac",
        "retention_d7",
        "nps",
        "CTR",
        "CPM",
        "CPC",
        "象限",
        "建议动作",
    ]
    selected = [item for item in preferred if item in headers][:8]
    if not selected:
        selected = headers[:8]
    return "重点看 " + " / ".join(_header_label(item) for item in selected) + "，同时关注高低断层、异常值和对象排序是否与建议动作一致。"


def _row_identity(row: dict[str, Any]) -> str:
    key_sets = [
        ["channel", "traffic_source"],
        ["content_category", "campaign"],
        ["product_module", "campaign"],
        ["user_segment", "city_tier"],
        ["time_window"],
        ["字段名"],
        ["阶段"],
        ["止损原因"],
        ["对象组合"],
        ["组合"],
    ]
    for keys in key_sets:
        values = [str(row.get(key) or "").strip() for key in keys if str(row.get(key) or "").strip()]
        if values:
            return " / ".join(values)
    for value in row.values():
        text = str(value or "").strip()
        if text and _safe_float(text) is None:
            return text[:80]
    return "整体"


def _numeric_column_values(rows: list[dict[str, Any]], column: str) -> list[tuple[dict[str, Any], float]]:
    pairs: list[tuple[dict[str, Any], float]] = []
    for row in rows:
        value = _safe_float(row.get(column))
        if value is not None:
            pairs.append((row, value))
    return pairs


def _fact_for_extreme(rows: list[dict[str, Any]], column: str, *, highest: bool = True) -> str:
    pairs = _numeric_column_values(rows, column)
    if not pairs:
        return ""
    row, value = sorted(pairs, key=lambda pair: pair[1], reverse=highest)[0]
    direction = "最高" if highest else "最低"
    meaning = "；业务含义：" + _business_meaning_for_metric(column) if _is_percent_column(column) else ""
    return f"{_row_identity(row)} 的{_header_label(column)}{direction}，为 {_fmt_for_column(column, value)}{meaning}"


def _median_for_column(rows: list[dict[str, Any]], column: str) -> float:
    values = sorted(value for _, value in _numeric_column_values(rows, column))
    if not values:
        return 0.0
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2.0


def _roi_quadrant(row: dict[str, Any], *, roi_mid: float, cac_mid: float) -> str:
    roi_value = _safe_float(row.get("roi")) or 0.0
    cac_value = _safe_float(row.get("cac")) or 0.0
    if roi_value >= roi_mid and cac_value <= cac_mid:
        return "加码象限：高 roi / 低 cac"
    if roi_value >= roi_mid and cac_value > cac_mid:
        return "提效象限：高 roi / 高 cac"
    if roi_value < roi_mid and cac_value <= cac_mid:
        return "验证象限：低 roi / 低 cac"
    return "止损象限：低 roi / 高 cac"


def _roi_quadrant_action(quadrant: str) -> str:
    if quadrant.startswith("加码象限"):
        return "优先承接预算迁入，但必须监控边际 roi 是否回落"
    if quadrant.startswith("提效象限"):
        return "保留规模，先压 cac 或优化出价结构，再决定是否继续放量"
    if quadrant.startswith("验证象限"):
        return "不急于放量，先用低成本验证转化承接和毛利质量"
    return "Day 1 进入止损或降权池，避免继续吞噬预算"


def _with_roi_quadrants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roi_mid = _median_for_column(rows, "roi")
    cac_mid = _median_for_column(rows, "cac")
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        quadrant = str(item.get("象限") or "").strip() or _roi_quadrant(item, roi_mid=roi_mid, cac_mid=cac_mid)
        item["象限"] = quadrant
        item["建议动作"] = str(item.get("建议动作") or "").strip() or _roi_quadrant_action(quadrant)
        item["结论"] = _roi_quadrant_action(quadrant)
        enriched.append(item)
    return enriched


def _representative_roi_quadrants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = [
        "加码象限：高 roi / 低 cac",
        "提效象限：高 roi / 高 cac",
        "验证象限：低 roi / 低 cac",
        "止损象限：低 roi / 高 cac",
    ]
    sorters = {
        "加码象限：高 roi / 低 cac": lambda row: (-( _safe_float(row.get("roi")) or 0.0), _safe_float(row.get("cac")) or 0.0),
        "提效象限：高 roi / 高 cac": lambda row: (-( _safe_float(row.get("operating_cost")) or 0.0), -( _safe_float(row.get("roi")) or 0.0)),
        "验证象限：低 roi / 低 cac": lambda row: (_safe_float(row.get("cac")) or 0.0, -( _safe_float(row.get("paid_users")) or 0.0)),
        "止损象限：低 roi / 高 cac": lambda row: (-( _safe_float(row.get("operating_cost")) or 0.0), -( _safe_float(row.get("cac")) or 0.0)),
    }
    representatives: list[dict[str, Any]] = []
    for quadrant in order:
        bucket = [row for row in rows if str(row.get("象限") or "") == quadrant]
        if not bucket:
            representatives.append(
                {
                    "象限": quadrant,
                    "结论": "当前样本未落入该象限，管理上无需为该象限单独配置动作",
                    "图中序号": "-",
                    "channel": "无样本",
                    "traffic_source": "无样本",
                    "paid_users": "",
                    "revenue": "",
                    "operating_cost": "",
                    "roi": "",
                    "cac": "",
                    "建议动作": "不配置动作",
                }
            )
            continue
        item = dict(sorted(bucket, key=sorters[quadrant])[0])
        item["结论"] = _roi_quadrant_action(quadrant)
        representatives.append(item)
    return representatives


def _chart_numeric_facts(csv_name: str, rows: list[dict[str, Any]], headers: list[str]) -> list[str]:
    if not rows:
        return ["当前配表没有可用行，无法提取具体数值。"]

    if csv_name == "ops_roi_cac_quadrant.csv":
        rows = _with_roi_quadrants(rows)
        reps = _representative_roi_quadrants(rows)
        facts = [
            _fact_for_extreme(rows, "roi", highest=True),
            _fact_for_extreme(rows, "cac", highest=True),
            _fact_for_extreme(rows, "cac", highest=False),
        ]
        for row in reps:
            facts.append(
                f"{row.get('象限')}代表对象为 {_row_identity(row)}，真实投放回报（roi）={_fmt(row.get('roi'))}、获客成本（cac）={_fmt(row.get('cac'))}、结论={row.get('结论')}"
            )
        return [fact for fact in facts if fact][:6]

    if csv_name == "ops_aarrr_derived_funnel_rates.csv":
        return [
            f"{row.get('阶段')} 的派生率为 {_fmt_for_column('派生率', row.get('派生率'))}，分子={row.get('分子')}，分母={row.get('分母')}；业务含义：{_business_meaning_for_metric('派生率')}"
            for row in rows
        ][:5]

    if csv_name in {"ops_channel_source_aarrr_detail.csv", "ops_channel_source_aarrr_topn_small_multiples.csv"}:
        facts = [
            _fact_for_extreme(rows, "operating_cost", highest=True),
            _fact_for_extreme(rows, "roi", highest=True),
            _fact_for_extreme(rows, "cac", highest=True),
            _fact_for_extreme(rows, "retention_d7", highest=False),
        ]
        first = rows[0]
        facts.append(
            f"{_row_identity(first)} 的曝光={_fmt(first.get('impressions'))}、点击={_fmt(first.get('clicks'))}、注册={_fmt(first.get('registrations'))}、激活={_fmt(first.get('activations'))}、付费={_fmt(first.get('paid_users'))}，点击率={_fmt_for_column('点击率', first.get('点击率'))}、激活到付费率={_fmt_for_column('激活到付费率', first.get('激活到付费率'))}"
        )
        return [fact for fact in facts if fact][:5]

    if csv_name == "ops_anomaly_stoploss_reason_chart.csv":
        pairs = _numeric_column_values(rows, "样本数")
        pairs = sorted(pairs, key=lambda pair: pair[1], reverse=True)
        return [f"{row.get('止损原因')} 涉及样本数 {_fmt(value)}" for row, value in pairs[:5]]

    if csv_name == "ops_full_field_coverage_matrix.csv":
        present = sum(1 for row in rows if str(row.get("是否存在") or "") == "是")
        min_non_null = min((_safe_float(row.get("非空率")) or 0.0 for row in rows), default=0.0)
        sample_fields = " / ".join(str(row.get("字段名") or "") for row in rows[:6])
        return [
            f"全字段覆盖表共 {len(rows)} 个字段，其中存在字段 {present} 个，最低非空率为 {_fmt_for_column('非空率', min_non_null)}；业务含义：{_business_meaning_for_metric('非空率')}",
            f"前 6 个字段为 {sample_fields}，字段名只作为字段值保留，不作为裸表头",
        ]

    if csv_name == "ops_time_window_derived_trends.csv":
        facts = []
        if rows:
            first = rows[0]
            last = rows[-1]
            facts.append(
                f"时间窗口从 {_row_identity(first)} 到 {_row_identity(last)}；末期收入={_fmt(last.get('收入'))}、真实投放回报（roi）={_fmt(last.get('roi'))}、获客成本（cac）={_fmt(last.get('cac'))}"
            )
        for column in ["边际 roi 代理", "边际 CAC 代理", "收入", "付费用户"]:
            fact = _fact_for_extreme(rows, column, highest=True)
            if fact:
                facts.append(fact)
        return facts[:5]

    preferred_metrics = [
        "增长质量分",
        "预算效率",
        "收入",
        "贡献毛利",
        "运营成本",
        "付费用户",
        "点击率",
        "点击到注册率",
        "激活到付费率",
        "毛利率",
        "roi",
        "cac",
        "retention_d7",
        "nps",
        "CTR",
        "CPM",
        "CPC",
        "样本量",
    ]
    facts = []
    for column in preferred_metrics:
        if column in headers:
            fact = _fact_for_extreme(rows, column, highest=(column not in {"cac", "CPM", "CPC", "运营成本"}))
            if fact:
                facts.append(fact)
        if len(facts) >= 4:
            break
    if len(facts) < 2:
        for header in headers:
            fact = _fact_for_extreme(rows, header, highest=True)
            if fact:
                facts.append(fact)
            if len(facts) >= 3:
                break
    return facts[:5] or [f"配表共 {len(rows)} 行，字段包括 " + " / ".join(_header_label(item) for item in headers[:8])]


def _chart_judgement(csv_name: str, rows: list[dict[str, Any]], headers: list[str]) -> str:
    facts = _chart_numeric_facts(csv_name, rows, headers)
    primary = facts[0] if facts else f"配表共 {len(rows)} 行。"
    if "roi_cac" in csv_name:
        return primary + "；结论不是单向止损，而是四象限预算迁移：加码象限承接迁入，提效象限先压 cac，验证象限低成本试承接，止损象限 Day 1 冻结。"
    if "funnel" in csv_name:
        return primary + "；AARRR 的图解要落到具体转化率和组合差异，不能只说漏斗有断点。"
    if "bubble" in csv_name:
        return primary + "；气泡大小只提示规模，最终判断要回到收入、付费用户和毛利等数值。"
    if "quadrant" in csv_name:
        return primary + "；象限图要用坐标值和对象规模解释，不能只看点在左上/右下。"
    if "heatmap" in csv_name or "matrix" in csv_name:
        return primary + "；热力颜色只是索引，经营结论要回到全量配表里的对象数值。"
    return primary + "；图解需要把对象、数值和下一步取舍连起来。"


def _chart_action_implication(csv_name: str, rows: list[dict[str, Any]], headers: list[str]) -> str:
    if csv_name == "ops_roi_cac_quadrant.csv":
        rows = _with_roi_quadrants(rows)
        reps = _representative_roi_quadrants(rows)
        stoploss = [row for row in reps if str(row.get("象限") or "").startswith("止损象限")]
        scale_up = [row for row in reps if str(row.get("象限") or "").startswith("加码象限")]
        if stoploss:
            scale_text = "，同时把 " + " / ".join(_row_identity(row) for row in scale_up) + " 作为 Day 2 小步迁入对象" if scale_up else ""
            return "优先把 " + " / ".join(_row_identity(row) for row in stoploss) + " 放入 Day 1 止损或降权复核" + scale_text + "。"
    if "channel_source" in csv_name or "ctr_cpc_cpm" in csv_name:
        return "用于 Day 2 渠道 × 流量来源预算重排，优先比较高成本低回报对象和高效率可加码对象。"
    if "user_city" in csv_name or "retention_nps" in csv_name:
        return "用于 Day 3 人群与城市层级取舍，优先保留高留存/高口碑组合，压缩低质量高成本组合。"
    if "content_campaign" in csv_name:
        return "用于 Day 4 内容与活动承接调整，优先处理转化断层明显的内容活动组合。"
    if "product_campaign" in csv_name or "paid_users_revenue" in csv_name:
        return "用于 Day 5 产品模块 × 活动商业化承接，优先比较付费用户、收入和贡献毛利。"
    if "time_window" in csv_name:
        return "用于 Day 7 周复盘，判断是否继续加码、降权或转入 backlog。"
    if "anomaly" in csv_name:
        return "用于 Day 1 异常冻结和止损清单排序。"
    return "用于把图中的对象差异接到本周动作、成功指标和下一检查点。"


def _point_ref(row: dict[str, Any]) -> str:
    point_id = str(row.get("图中序号") or row.get("气泡编号") or "").strip()
    identity = _row_identity(row)
    return f"{point_id} {identity}" if point_id else identity


def _row_metrics(row: dict[str, Any], columns: list[str]) -> str:
    parts: list[str] = []
    for column in columns:
        if column not in row:
            continue
        value = row.get(column)
        if value is None or str(value).strip() == "":
            continue
        parts.append(f"{_header_label(column)} {_fmt_for_column(column, value)}")
    return "、".join(parts)


def _unique_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = str(row.get("图中序号") or row.get("气泡编号") or _row_identity(row))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _extreme_row(rows: list[dict[str, Any]], column: str, *, highest: bool = True) -> dict[str, Any]:
    pairs = _numeric_column_values(rows, column)
    if not pairs:
        return {}
    return sorted(pairs, key=lambda pair: pair[1], reverse=highest)[0][0]


def _representative_point_rows(csv_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    if csv_name == "ops_roi_cac_quadrant.csv":
        return _unique_rows([row for row in _representative_roi_quadrants(_with_roi_quadrants(rows)) if str(row.get("图中序号") or "") != "-"])
    if csv_name == "ops_ctr_cpc_cpm_efficiency.csv":
        return _unique_rows([
            _extreme_row(rows, "CTR", highest=True),
            _extreme_row(rows, "CPC", highest=True),
            _extreme_row(rows, "roi", highest=False),
            _extreme_row(rows, "点击到注册率", highest=True),
        ])
    if csv_name == "ops_cost_margin_share_matrix.csv":
        return _unique_rows([
            sorted(rows, key=lambda row: (_safe_float(row.get("毛利占比")) or 0.0) - (_safe_float(row.get("成本占比")) or 0.0), reverse=True)[0],
            sorted(rows, key=lambda row: (_safe_float(row.get("毛利占比")) or 0.0) - (_safe_float(row.get("成本占比")) or 0.0))[0],
            _extreme_row(rows, "运营成本", highest=True),
        ])
    if csv_name == "ops_paid_users_revenue_bubble.csv":
        return _unique_rows([
            _extreme_row(rows, "收入", highest=True),
            _extreme_row(rows, "付费用户", highest=True),
            _extreme_row(rows, "roi", highest=False),
        ])
    if csv_name == "ops_retention_nps_quality_quadrant.csv":
        return _unique_rows([
            _extreme_row(rows, "增长质量分", highest=True),
            _extreme_row(rows, "增长质量分", highest=False),
            _extreme_row(rows, "nps", highest=True),
        ])
    return _unique_rows(rows[:4])


def _point_chart_narrative(csv_name: str, title: str, rows: list[dict[str, Any]], *, include_paired_tables: bool) -> list[str]:
    reps = _representative_point_rows(csv_name, rows)
    while len(reps) < min(3, len(rows)):
        reps = _unique_rows(reps + rows[: min(4, len(rows))])
    if csv_name == "ops_roi_cac_quadrant.csv":
        metrics = ["roi", "cac", "paid_users", "revenue", "operating_cost", "象限", "建议动作"]
        opening = "这张四象限图回答的是预算流转问题：横轴是获客成本（cac），纵轴是真实投放回报（roi），颜色代表迁入、提效、验证和冻结等处理通道，图中 Bxx 只负责定位对象，具体字段要回到配表复核。"
        bridge = "读这张图时不要把四类对象当成并列标签，而要按顺序处理：冻结池先释放预算，迁入池小步承接，提效池先压 cac，验证池只用低成本样本争取资格。"
    elif csv_name == "ops_ctr_cpc_cpm_efficiency.csv":
        metrics = ["CTR", "CPC", "CPM", "点击到注册率", "激活到付费率", "roi", "cac"]
        opening = "这张获客效率图回答的是点击是否有效：横轴是单次点击成本（CPC），纵轴是点击率（CTR），点位越靠上代表入口吸引越强，但是否进入预算迁入池还要看注册、付费和 roi。"
        bridge = "所以图里高 CTR 的点不能直接等同于高商业回报；只有点击继续转成注册、激活、付费并且 roi 没断，才算有效入口。"
    elif csv_name == "ops_cost_margin_share_matrix.csv":
        metrics = ["成本占比", "毛利占比", "收入", "运营成本", "贡献毛利", "预算效率", "roi"]
        opening = "这张成本毛利矩阵回答的是钱有没有变成利润：横轴看成本占比，纵轴看毛利占比，越偏向成本高而毛利低的位置，越像预算吞噬点。"
        bridge = "它把前面的预算迁移再过一遍利润门，避免把高收入但低毛利的对象误判成可加码对象。"
    elif csv_name == "ops_paid_users_revenue_bubble.csv":
        metrics = ["付费用户", "收入", "贡献毛利", "毛利率", "roi", "cac"]
        opening = "这张气泡图回答的是商业承接强度：横轴和纵轴看付费用户与收入，气泡规模提示承接体量，但真正能否放大要同时看贡献毛利、毛利率和 roi。"
        bridge = "因此气泡大只代表规模进入视野，不代表可以直接加码；配表会把收入、付费、毛利和成本放在同一个序号下复核。"
    elif csv_name == "ops_retention_nps_quality_quadrant.csv":
        metrics = ["retention_d7", "nps", "增长质量分", "付费用户", "收入", "roi", "cac"]
        opening = "这张质量象限回答的是新增用户值不值得继续经营：横轴看 7 日留存，纵轴看口碑净推荐值（NPS），图中序号把人群/城市组合和完整经营指标接回配表。"
        bridge = "它只能裁决人群质量，不能直接证明商业承接已经成功；下一步需要和产品模块、活动承接或 Day 5 桥接实验连起来。"
    else:
        metrics = ["收入", "运营成本", "贡献毛利", "roi", "cac", "retention_d7", "nps"]
        opening = f"这张{_chart_type_from_name(csv_name)}回答的是对象之间的数值分化，图中序号用于把每个点接回配表的完整字段。"
        bridge = "图形负责暴露差异，配表负责复核字段，动作取舍要同时看规模、效率和质量。"
    details = "；".join(
        f"{_point_ref(row)} 的{_row_metrics(row, metrics)}"
        for row in reps[:4]
        if row
    )
    table_sentence = (
        f"图后配表以“图中序号”为第一列，覆盖 {Path(csv_name).name} 的 {len(rows)} 行对象和全部字段；读者可以用 Bxx 先在图上定位，再在续表里核对漏斗、成本、收入、质量和动作字段。"
        if not include_paired_tables
        else f"图后全量配表覆盖 {Path(csv_name).name} 的 {len(rows)} 行对象和全部字段，宽字段只拆续表，不截断对象。"
    )
    return [opening, f"关键分化已经能落到具体点位：{details}。{bridge}", table_sentence]


def _aarrr_total_narrative(rows: list[dict[str, Any]]) -> list[str]:
    sorted_rows = sorted(rows, key=lambda row: _safe_float(row.get("派生率")) or 1.0)
    weakest = sorted_rows[0] if sorted_rows else {}
    strongest = sorted_rows[-1] if sorted_rows else {}
    stage_lines = "；".join(
        f"{row.get('阶段')} {_fmt_for_column('派生率', row.get('派生率'))}（{row.get('分子')} / {row.get('分母')}）"
        for row in rows[:5]
    )
    return [
        "这张总漏斗图只回答一个问题：全盘最大的转化断点在哪里。它按 AARRR 阶段展示相邻转化率，分子和分母写在配表里，用来防止把不同口径的转化率混在一起。",
        f"当前阶段读数是：{stage_lines}。最紧的闸口是 {weakest.get('阶段', '未知阶段')}，派生率 {_fmt_for_column('派生率', weakest.get('派生率'))}；相对更顺的阶段是 {strongest.get('阶段', '未知阶段')}，派生率 {_fmt_for_column('派生率', strongest.get('派生率'))}。这说明总盘先定位断点，不直接决定预算迁移。",
        "图后的阶段配表把每个转化率的分子、分母和口径列出来；预算动作要继续下钻到渠道 × 流量来源组合，因为同一个总断点在不同组合上的损耗位置并不一样。",
    ]


def _aarrr_combo_narrative(rows: list[dict[str, Any]], *, include_paired_tables: bool) -> list[str]:
    candidates = _unique_rows([
        _extreme_row(rows, "roi", highest=True),
        _extreme_row(rows, "operating_cost", highest=True),
        _extreme_row(rows, "cac", highest=True),
        _extreme_row(rows, "激活到付费率", highest=False),
        rows[0] if rows else {},
    ])
    while len(candidates) < min(4, len(rows)):
        candidates = _unique_rows(candidates + rows[:6])
    details = "；".join(
        f"{_row_identity(row)} 曝光 {_fmt(row.get('impressions'))}、点击 {_fmt(row.get('clicks'))}、注册 {_fmt(row.get('registrations'))}、激活 {_fmt(row.get('activations'))}、付费 {_fmt(row.get('paid_users'))}，点击率 {_fmt_for_column('点击率', row.get('点击率'))}、点击到注册率 {_fmt_for_column('点击到注册率', row.get('点击到注册率'))}、激活到付费率 {_fmt_for_column('激活到付费率', row.get('激活到付费率'))}"
        for row in candidates[:4]
        if row
    )
    table_mode = "Top12 配表保留每个入选组合的阶段规模、转化率、收入成本和入选原因" if not include_paired_tables else "长版继续展开全量组合分页图和全量组合配表"
    return [
        "这组 AARRR 小倍图回答的是：同一个总漏斗断点，落到渠道 × 流量来源组合之后，谁有预算承接资格，谁只是高消耗或后段断层。每个小图同时看阶段规模和相邻转化率，不能只看比例或只看规模。",
        f"Top 组合的差异已经很具体：{details}。这些组合分别覆盖高承接、高消耗、断层和待验证对象，后续预算迁移必须按组合处理，而不是按全局漏斗平均处理。",
        f"{table_mode}；读者可以用组合名称回到配表核对曝光、点击、注册、激活、付费、roi、cac、留存和收入成本，再决定 Day 2 迁入还是 Day 4/Day 5 修复承接。",
    ]


def build_chart_narrative_card(
    csv_name: str,
    headers: list[str],
    row_count: int,
    rows: list[dict[str, Any]] | None = None,
    *,
    include_paired_tables: bool = True,
) -> dict[str, Any]:
    data_rows = rows or []
    title = _chart_title(csv_name)
    if csv_name == "ops_aarrr_derived_funnel_rates.csv":
        paragraphs = _aarrr_total_narrative(data_rows)
        references = [str(row.get("阶段") or "") for row in data_rows[:5] if row.get("阶段")]
    elif csv_name in {"ops_channel_source_aarrr_detail.csv", "ops_channel_source_aarrr_topn_small_multiples.csv"}:
        paragraphs = _aarrr_combo_narrative(data_rows, include_paired_tables=include_paired_tables)
        references = [_row_identity(row) for row in data_rows[:12]]
    elif csv_name in POINT_MAPPING_CSV_NAMES:
        paragraphs = _point_chart_narrative(csv_name, title, data_rows, include_paired_tables=include_paired_tables)
        references = [str(row.get("图中序号") or "") for row in _representative_point_rows(csv_name, data_rows) if row.get("图中序号")]
    else:
        evidence = _chart_numeric_facts(csv_name, data_rows, headers)
        how = _chart_how_to_read(csv_name)
        action = _chart_action_implication(csv_name, data_rows, headers)
        paired = (
            f"图后配表保留 {Path(csv_name).name} 的 {row_count} 行底层数据，字段较宽时按续表拆开。"
            if include_paired_tables
            else f"默认读者版保留图解和关键配表线索，完整字段在长版中展开；当前底层数据为 {Path(csv_name).name}，共 {row_count} 行。"
        )
        paragraphs = [
            f"{title}回答的是{_chart_type_from_name(csv_name)}里的对象分化。{how}",
            "关键数值是：" + "；".join(evidence[:4]) + "。这些数值决定这张图不是装饰，而是用来识别机会、风险或复盘断层。",
            f"{action}{paired}",
        ]
        references = [_row_identity(row) for row in data_rows[:5]]
    numeric_tokens = [
        token
        for token in re.findall(r"(?<![A-Za-z])[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?", "\n".join(paragraphs))
        if any(char.isdigit() for char in token)
    ]
    return {
        "chart_id": Path(csv_name).stem,
        "title": title,
        "chart_type": _chart_type_from_name(csv_name),
        "png_path": f"source_visual_assets/{Path(csv_name).with_suffix('.png').name}",
        "csv_path": f"source_visual_assets/{csv_name}",
        "row_count": row_count,
        "references": [ref for ref in references if ref],
        "paragraphs": paragraphs,
        "numeric_token_count": len(numeric_tokens),
    }


def _chart_explanation_block(
    csv_name: str,
    headers: list[str],
    row_count: int,
    rows: list[dict[str, Any]] | None = None,
    *,
    include_paired_tables: bool = True,
) -> list[str]:
    card = build_chart_narrative_card(
        csv_name,
        headers,
        row_count,
        rows,
        include_paired_tables=include_paired_tables,
    )
    return [f"**图解**：{paragraph}" if idx == 0 else paragraph for idx, paragraph in enumerate(card["paragraphs"])]


ROI_COLUMN_GROUPS = [
    ("对象与样本", ["channel", "traffic_source", "sample_size", "组合"]),
    ("漏斗规模", ["channel", "traffic_source", "impressions", "clicks", "registrations", "activations", "paid_users"]),
    ("收入成本", ["channel", "traffic_source", "revenue", "operating_cost", "contribution_margin"]),
    (
        "质量与前段效率",
        ["channel", "traffic_source", "retention_d7", "nps", "CTR", "点击到注册率", "注册到激活率"],
    ),
    (
        "付费与财务效率",
        ["channel", "traffic_source", "激活到付费率", "每付费用户收入", "毛利率", "roi", "cac"],
    ),
    ("象限决策", ["channel", "traffic_source", "象限", "建议动作", "效率分"]),
]


REPORT_CSS = """
@page { size: A4; margin: 16mm 13mm; }
:root { --ink:#0f172a; --muted:#475569; --navy:#082f49; --blue:#0f4c81; --gold:#f2c14e; --line:#d8e2ee; --soft:#f7fbff; }
* { box-sizing: border-box; }
body { margin:0; font-family:"Noto Serif SC","Microsoft YaHei",serif; color:var(--ink); background:linear-gradient(135deg,#f7fbff,#eef5fb 45%,#fffaf0); line-height:1.68; }
.report-shell { max-width:1120px; margin:0 auto; padding:44px 42px 80px; background:rgba(255,255,255,.96); box-shadow:0 24px 80px rgba(15,23,42,.14); }
.cover { border:1px solid var(--line); border-left:10px solid var(--blue); padding:28px 32px; margin-bottom:28px; background:linear-gradient(120deg,#fff,#eef6ff); }
h1 { margin:0 0 10px; font-size:34px; color:var(--navy); line-height:1.22; }
h2 { break-after:avoid; page-break-after:avoid; margin-top:34px; padding-top:18px; border-top:2px solid var(--line); color:var(--navy); font-size:24px; }
h3 { break-after:avoid; page-break-after:avoid; color:#123b63; font-size:18px; margin-top:24px; }
h4 { break-after:avoid; page-break-after:avoid; color:#123b63; font-size:15.5px; line-height:1.55; margin:24px 0 12px; padding:10px 12px; border-left:4px solid var(--blue); border-radius:10px; background:#f4f9ff; }
p { margin:10px 0; }
ul, ol { padding-left:1.35em; }
li { margin:4px 0; }
.management-brief-shell p { margin:13px 0; }
.management-brief-shell ul { margin:10px 0 20px; padding-left:1.55em; }
.management-brief-shell li { margin:7px 0; line-height:1.72; }
.table-scroll { width:100%; overflow-x:auto; margin:12px 0 22px; }
.report-table-block { break-inside:auto; page-break-inside:auto; margin:16px 0 24px; }
.report-table-block table { width:100%; border-collapse:collapse; table-layout:fixed; background:#fff; border:1px solid var(--line); font-size:12.2px; }
.report-table-block--wide table { font-size:10.4px; }
thead { display:table-header-group; }
tfoot { display:table-footer-group; }
tr { break-inside:avoid; page-break-inside:avoid; }
th, td { border:1px solid var(--line); padding:7px 8px; vertical-align:top; overflow-wrap:anywhere; word-break:break-word; hyphens:auto; }
th { background:#eaf4ff; color:#123b63; font-weight:800; }
tbody tr:nth-child(even) td { background:#f8fbff; }
.figure-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin:24px 0 36px; }
figure { margin:0; padding:14px; border:1px solid var(--line); border-radius:14px; background:#fff; break-inside:avoid; page-break-inside:avoid; }
figure img { width:100%; height:auto; display:block; border-radius:10px; border:1px solid #e2e8f0; }
figcaption { font-weight:700; color:var(--navy); margin-top:10px; }
.figure-notes { margin-top:8px; font-size:13px; color:var(--muted); }
.daily-card { border:1px solid var(--line); border-left:6px solid var(--gold); border-radius:14px; padding:14px 18px; margin:12px 0; background:#fffdf7; break-inside:avoid; page-break-inside:avoid; }
@media print {
  body { background:#fff; }
  .report-shell { box-shadow:none; padding:0; max-width:none; }
  .table-scroll { overflow:visible; }
  .report-table-block { break-inside:auto; page-break-inside:auto; }
  .report-table-block table { table-layout:fixed; }
  .report-table-block--wide table { font-size:9.2px; }
  th, td { padding:5px 6px; }
  figure { page-break-inside:avoid; break-inside:avoid; }
  .figure-grid { grid-template-columns:1fr; }
}
""".strip()


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv_dicts(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if math.isfinite(parsed):
        return parsed
    return None


def _fmt(value: Any, digits: int = 4) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return str(value or "")
    if abs(parsed) >= 1000:
        return f"{parsed:,.0f}"
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def _is_percent_column(column: str) -> bool:
    normalized = str(column or "").strip().lower()
    if not normalized:
        return False
    non_percent = {
        "date",
        "channel",
        "traffic_source",
        "city_tier",
        "user_segment",
        "content_category",
        "product_module",
        "campaign",
        "time_window",
        "sample_size",
        "impressions",
        "clicks",
        "registrations",
        "activations",
        "paid_users",
        "revenue",
        "operating_cost",
        "contribution_margin",
        "cac",
        "cpc",
        "cpm",
        "nps",
        "roi",
        "roi_proxy",
    }
    if normalized in non_percent:
        return False
    exact = {
        "ctr",
        "retention_d7",
        "点击率",
        "点击到注册率",
        "注册到激活率",
        "激活到付费率",
        "点击到付费率",
        "毛利率",
        "派生率",
        "非空率",
        "成本占比",
        "毛利占比",
        "收入占比",
        "付费用户占比",
    }
    if column in exact or normalized in exact:
        return True
    percent_tokens = ("率", "占比", "share", "rate", "ratio", "percent", "percentage")
    if any(token in normalized for token in ("roi", "cpc", "cpm", "cac", "nps")):
        return False
    return any(token in normalized for token in percent_tokens)


def _fmt_for_column(column: str, value: Any, digits: int = 2) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return str(value or "")
    if _is_percent_column(column):
        percent_value = parsed * 100 if abs(parsed) <= 1.5 else parsed
        return f"{percent_value:.{digits}f}%".rstrip("0").rstrip(".").replace(".%", "%")
    return _fmt(value)


def _business_meaning_for_metric(column: str) -> str:
    label = _header_label(column)
    meanings = {
        "CTR": "点击率代表曝光后的前段吸引效率，只说明素材和入口能否把人拉进来，不能单独代表收入质量。",
        "点击率": "点击率代表曝光后的前段吸引效率，只说明素材和入口能否把人拉进来，不能单独代表收入质量。",
        "点击到注册率": "点击到注册率代表落地页和注册门槛的承接效率，偏低通常指向承接页、表单或权益表达问题。",
        "注册到激活率": "注册到激活率代表新用户从留资到首个有效行为的启动效率，偏低说明新手路径或首触价值不够顺。",
        "激活到付费率": "激活到付费率代表商业化临门一脚，偏低说明产品权益、价格或活动承接没有把活跃转成收入。",
        "点击到付费率": "点击到付费率是从流量到收入的端到端效率，适合用来比较渠道和流量来源是否真正带来付费。",
        "毛利率": "毛利率代表收入扣除运营成本后的利润质量，毛利率低说明规模增长可能没有带来可持续利润。",
        "成本占比": "成本占比代表预算消耗权重，成本占比高但产出占比低就是预算错配，需要降权或止损。",
        "毛利占比": "毛利占比代表利润贡献权重，毛利占比高的对象更适合进入保留或加码池。",
        "收入占比": "收入占比代表收入贡献权重，需要和成本占比、毛利占比一起看，避免只按收入规模加码。",
        "付费用户占比": "付费用户占比代表付费人群贡献权重，需要和收入占比一起判断是否靠少数高客单支撑。",
        "retention_d7": "7日留存率代表用户质量和后续可经营性，留存低会削弱 ROI 和 LTV 的持续性。",
        "派生率": "派生率是漏斗相邻步骤的转化口径，用来定位断点，而不是泛泛描述漏斗变窄。",
        "非空率": "非空率代表字段可用程度，非空率低的字段只能做辅助判断，不能作为核心经营结论。",
    }
    return meanings.get(column) or meanings.get(label) or f"{label} 是比例型指标，业务上要和规模、成本、收入或毛利一起判断，不能只看百分比高低。"


def _percent_metric_meaning_summary(headers: list[str], *, limit: int = 5) -> str:
    percent_columns = [column for column in headers if _is_percent_column(column)]
    if not percent_columns:
        return ""
    parts = [
        f"{_header_label(column)}：{_business_meaning_for_metric(column)}"
        for column in percent_columns[:limit]
    ]
    return "；".join(parts)


def _pearson(left: list[float], right: list[float]) -> float | None:
    n = len(left)
    if n < 3:
        return None
    mean_l = sum(left) / n
    mean_r = sum(right) / n
    cov = sum((x - mean_l) * (y - mean_r) for x, y in zip(left, right))
    var_l = sum((x - mean_l) ** 2 for x in left)
    var_r = sum((y - mean_r) ** 2 for y in right)
    if var_l <= 0 or var_r <= 0:
        return None
    return max(min(cov / math.sqrt(var_l * var_r), 1.0), -1.0)


def _pearson_p_value(r_value: float, n: int) -> float:
    if n < 4:
        return 1.0
    bounded = max(min(abs(r_value), 0.999999), 0.0)
    if bounded >= 0.999999:
        return 0.0
    # Fisher-z normal approximation; good enough for the deterministic preview table.
    z_score = math.atanh(bounded) * math.sqrt(max(n - 3, 1))
    return max(min(2.0 * (1.0 - NormalDist().cdf(abs(z_score))), 1.0), 0.0)


def _ci95(r_value: float, n: int) -> tuple[float, float]:
    if n <= 3 or abs(r_value) >= 0.999999:
        return (r_value, r_value)
    z_value = math.atanh(max(min(r_value, 0.999999), -0.999999))
    stderr = 1.0 / math.sqrt(n - 3)
    return (math.tanh(z_value - 1.96 * stderr), math.tanh(z_value + 1.96 * stderr))


def _significance_label(p_value: float, q_value: float, n: int) -> str:
    if n < 8:
        return "样本不足"
    if p_value < 0.05 and q_value < 0.05:
        return "显著"
    if p_value < 0.10 or q_value < 0.10:
        return "边缘显著"
    return "不显著"


def _add_bh_q_values(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed = [
        (idx, float(_safe_float(row.get("p_value"))))
        for idx, row in enumerate(rows)
        if _safe_float(row.get("p_value")) is not None
    ]
    m = len(indexed)
    if not m:
        return rows
    sorted_pairs = sorted(indexed, key=lambda pair: pair[1], reverse=True)
    prev_q = 1.0
    q_values: dict[int, float] = {}
    for rank_from_end, (idx, p_value) in enumerate(sorted_pairs, start=1):
        rank = m - rank_from_end + 1
        q_value = min(prev_q, p_value * m / max(rank, 1))
        prev_q = q_value
        q_values[idx] = max(min(q_value, 1.0), 0.0)
    for idx, row in enumerate(rows):
        q_value = q_values.get(idx, 1.0)
        row["q_value_bh"] = q_value
        p_value = _safe_float(row.get("p_value"))
        row["significance_label"] = _significance_label(float(p_value) if p_value is not None else 1.0, q_value, int(row.get("n") or 0))
    return rows


def rebuild_correlation_significance() -> list[dict[str, Any]]:
    source_path = JOB_ROOT / "source_dataset.csv"
    rows = _read_csv_dicts(source_path)
    if not rows:
        return []

    headers = list(rows[0].keys())
    numeric_columns: dict[str, list[float | None]] = {}
    for header in headers:
        values = [_safe_float(row.get(header)) for row in rows]
        valid = [value for value in values if value is not None]
        if len(valid) >= 8 and len(valid) / max(len(rows), 1) >= 0.65:
            numeric_columns[header] = values

    correlation_rows: list[dict[str, Any]] = []
    names = list(numeric_columns)
    for i, left_name in enumerate(names):
        for right_name in names[i + 1 :]:
            paired_left: list[float] = []
            paired_right: list[float] = []
            for left_value, right_value in zip(numeric_columns[left_name], numeric_columns[right_name]):
                if left_value is None or right_value is None:
                    continue
                paired_left.append(left_value)
                paired_right.append(right_value)
            r_value = _pearson(paired_left, paired_right)
            if r_value is None:
                continue
            n = len(paired_left)
            p_value = _pearson_p_value(r_value, n)
            ci_low, ci_high = _ci95(r_value, n)
            correlation_rows.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "n": n,
                    "pearson_r": r_value,
                    "pearson_correlation": r_value,
                    "correlation": r_value,
                    "abs_correlation": abs(r_value),
                    "p_value": p_value,
                    "ci95_low": ci_low,
                    "ci95_high": ci_high,
                }
            )

    _add_bh_q_values(correlation_rows)
    correlation_rows.sort(key=lambda row: float(row.get("abs_correlation") or 0), reverse=True)

    preview_fields = [
        "left",
        "right",
        "n",
        "pearson_r",
        "pearson_correlation",
        "correlation",
        "abs_correlation",
        "p_value",
        "q_value_bh",
        "significance_label",
        "ci95_low",
        "ci95_high",
    ]
    _write_csv_dicts(JOB_ROOT / "source_correlation_preview.csv", correlation_rows[:120], preview_fields)
    _write_csv_dicts(ASSET_ROOT / "generic_correlation_bubble.csv", correlation_rows[:60], preview_fields)
    return correlation_rows


def redraw_cost_margin_share_chart() -> None:
    csv_path = ASSET_ROOT / "ops_cost_margin_share_matrix.csv"
    png_path = ASSET_ROOT / "ops_cost_margin_share_matrix.png"
    rows = _read_csv_dicts(csv_path)
    if not rows:
        return
    try:
        import matplotlib.pyplot as plt
        from matplotlib.ticker import PercentFormatter
    except Exception:
        return

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    numbered_rows = []
    for idx, row in enumerate(rows, start=1):
        numbered = dict(row)
        numbered["图中序号"] = str(numbered.get("图中序号") or numbered.get("气泡编号") or f"B{idx:02d}")
        numbered.pop("气泡编号", None)
        numbered_rows.append(numbered)
    if numbered_rows:
        fields = ["图中序号"] + [column for column in numbered_rows[0].keys() if column != "图中序号"]
        _write_csv_dicts(csv_path, numbered_rows, fields)

    clean_rows = []
    for row in numbered_rows:
        cost_share = _safe_float(row.get("成本占比"))
        margin_share = _safe_float(row.get("毛利占比"))
        revenue = _safe_float(row.get("收入")) or 0.0
        budget_efficiency = _safe_float(row.get("预算效率")) or 0.0
        if cost_share is None or margin_share is None:
            continue
        clean_rows.append(
            {
                **row,
                "_cost_share": cost_share,
                "_margin_share": margin_share,
                "_revenue": revenue,
                "_budget_efficiency": budget_efficiency,
                "_gap": margin_share - cost_share,
                "_bubble_no": str(row.get("图中序号") or ""),
            }
        )
    if not clean_rows:
        return

    max_revenue = max(row["_revenue"] for row in clean_rows) or 1.0
    sizes = [max(75, min(820, row["_revenue"] / max_revenue * 820)) for row in clean_rows]
    fig, ax = plt.subplots(figsize=(12.6, 8.7))
    scatter = ax.scatter(
        [row["_cost_share"] for row in clean_rows],
        [row["_margin_share"] for row in clean_rows],
        s=sizes,
        c=[row["_budget_efficiency"] for row in clean_rows],
        cmap="RdYlGn",
        alpha=0.78,
        edgecolors="white",
        linewidths=0.9,
    )
    max_axis = max(
        max(row["_cost_share"] for row in clean_rows),
        max(row["_margin_share"] for row in clean_rows),
        0.01,
    ) * 1.10
    axis_limit = max_axis * 1.18
    ax.plot([0, axis_limit], [0, axis_limit], linestyle="--", color="#475569", linewidth=1.2)
    ax.text(
        axis_limit * 0.57,
        axis_limit * 0.68,
        "虚线：毛利占比 = 成本占比\n线上方=毛利贡献高于预算消耗\n线下方=预算消耗高于毛利贡献",
        fontsize=9.5,
        color="#334155",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.92},
    )

    def label_row(row: dict[str, Any], *, offset: tuple[int, int], ha: str = "left") -> None:
        name = str(row.get("对象组合") or f"{row.get('channel')} / {row.get('traffic_source')}")
        ax.annotate(
            f"{row['_bubble_no']} {name}\n成本{row['_cost_share']:.1%} / 毛利{row['_margin_share']:.1%}",
            (row["_cost_share"], row["_margin_share"]),
            fontsize=8,
            xytext=offset,
            textcoords="offset points",
            ha=ha,
            va="center",
            arrowprops={"arrowstyle": "-", "color": "#94a3b8", "lw": 0.8},
            annotation_clip=False,
            bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "#e2e8f0", "alpha": 0.82},
        )

    label_offsets = [
        (-24, 18),
        (20, 18),
        (0, 26),
        (-28, -4),
        (26, -16),
        (-6, -28),
        (24, 2),
        (-30, -22),
        (28, 24),
        (-18, 32),
        (34, -2),
        (-34, 8),
        (12, -34),
        (34, 14),
        (-10, -38),
        (28, -30),
        (-38, 24),
        (0, -42),
        (38, 0),
        (-38, -10),
        (14, 38),
        (-20, 40),
        (40, 18),
        (-42, 12),
        (42, -14),
        (-8, 46),
        (-46, 26),
        (20, -46),
        (-44, -26),
        (44, 30),
    ]
    for idx, row in enumerate(clean_rows):
        offset = label_offsets[idx % len(label_offsets)]
        if row["_cost_share"] > axis_limit * 0.78:
            offset = (-38, 16)
        if row["_cost_share"] < axis_limit * 0.12 and offset[0] < 0:
            offset = (abs(offset[0]) + 8, offset[1])
        if row["_margin_share"] < axis_limit * 0.12 and offset[1] < 0:
            offset = (offset[0], abs(offset[1]) + 10)
        ax.annotate(
            row["_bubble_no"],
            (row["_cost_share"], row["_margin_share"]),
            fontsize=6.8,
            fontweight="bold",
            xytext=offset,
            textcoords="offset points",
            ha="center",
            va="center",
            arrowprops={"arrowstyle": "-", "color": "#cbd5e1", "lw": 0.55},
            annotation_clip=False,
            bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.9},
        )

    weak_rows = sorted(clean_rows, key=lambda item: item["_gap"])[:3]
    strong_rows = sorted(clean_rows, key=lambda item: item["_gap"], reverse=True)[:3]
    ax.set_xlim(-axis_limit * 0.04, axis_limit)
    ax.set_ylim(-axis_limit * 0.04, axis_limit)
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax.set_title("成本占比 × 毛利占比矩阵：预算消耗是否换来毛利贡献", fontsize=15, pad=12)
    ax.set_xlabel("成本占比（预算消耗份额）")
    ax.set_ylabel("毛利占比（利润贡献份额）")
    ax.grid(alpha=0.2)
    colorbar = fig.colorbar(scatter, ax=ax, shrink=0.86, pad=0.02)
    colorbar.set_label("预算效率：贡献毛利 / 运营成本")
    ax.scatter([], [], s=260, c="#94a3b8", alpha=0.45, edgecolors="white", label="气泡越大=收入规模越大")
    ax.legend(loc="lower right", fontsize=8, frameon=True)
    best = strong_rows[0]
    worst = weak_rows[0]
    fig.text(
        0.08,
        0.025,
        "图注：每个气泡代表一个“渠道 × 流量来源”组合，图上 B01-B30 全部标注，编号对应下方配表第一列；"
        "横轴是预算消耗份额，纵轴是利润贡献份额，"
        "颜色越绿代表预算效率越高，气泡越大代表收入规模越大。"
        f" 本图结论：{best.get('对象组合')} 成本占比 {best['_cost_share']:.1%}、毛利占比 {best['_margin_share']:.1%}，"
        f"优先加码；{worst.get('对象组合')} 成本占比 {worst['_cost_share']:.1%}、毛利占比 {worst['_margin_share']:.1%}，"
        "优先止损或降权。完整对象和全字段见配表。",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#334155",
        wrap=True,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(png_path, dpi=180)
    plt.close(fig)


def redraw_labeled_point_charts() -> None:
    try:
        import pandas as pd
    except Exception:
        return
    specs = [
        {
            "csv": "ops_roi_cac_quadrant.csv",
            "png": "ops_roi_cac_quadrant.png",
            "x": "cac",
            "y": "roi",
            "title": "真实投放回报 × 获客成本四象限图（roi / cac）：渠道 × 流量来源",
            "xlabel": "获客成本（cac）",
            "ylabel": "真实投放回报（roi）",
            "size": "paid_users",
            "category": "象限",
            "colors": {"加码象限": "#16a34a", "提效象限": "#f59e0b", "验证象限": "#2563eb", "止损象限": "#dc2626"},
            "median": True,
            "note": "图注：图内每个点只标短序号 B01...，完整渠道、流量来源、漏斗规模、收入成本、质量效率和动作字段见图后配表。",
        },
        {
            "csv": "ops_ctr_cpc_cpm_efficiency.csv",
            "png": "ops_ctr_cpc_cpm_efficiency.png",
            "x": "CPC",
            "y": "CTR",
            "title": "点击率 × 单次点击成本 × 千次曝光成本获客效率图（CTR / CPC / CPM）",
            "xlabel": "单次点击成本（CPC）",
            "ylabel": "点击率（CTR）",
            "size": "CPM",
            "color": "点击到注册率",
            "cmap": "viridis",
            "colorbar": "点击到注册率",
            "percent_y": True,
            "note": "图注：横轴越低越省点击成本，纵轴越高代表入口吸引更强，气泡越大代表千次曝光成本越高；完整对象和值见配表。",
        },
        {
            "csv": "ops_paid_users_revenue_bubble.csv",
            "png": "ops_paid_users_revenue_bubble.png",
            "x": "付费用户",
            "y": "收入",
            "title": "付费用户 × 收入承接气泡图",
            "xlabel": "付费用户",
            "ylabel": "收入",
            "size": "贡献毛利",
            "color": "毛利率",
            "cmap": "YlGnBu",
            "colorbar": "毛利率",
            "note": "图注：气泡越大代表贡献毛利越高，颜色代表毛利率；完整产品模块、活动和商业化字段见配表。",
        },
        {
            "csv": "ops_retention_nps_quality_quadrant.csv",
            "png": "ops_retention_nps_quality_quadrant.png",
            "x": "retention_d7",
            "y": "nps",
            "title": "留存 × 口碑净推荐值质量象限图（NPS）",
            "xlabel": "7日留存（retention_d7）",
            "ylabel": "口碑净推荐值（NPS）",
            "size": "付费用户",
            "color": "增长质量分",
            "cmap": "RdYlGn",
            "colorbar": "增长质量分",
            "median": True,
            "percent_x": True,
            "note": "图注：右上代表留存和口碑都更强，左下需要体验修复或降权观察；完整用户分层、城市层级和值见配表。",
        },
    ]
    for spec in specs:
        csv_path = ASSET_ROOT / str(spec["csv"])
        rows = _ensure_point_ids(_read_csv_dicts(csv_path), csv_path)
        if not rows:
            continue
        frame = pd.DataFrame(rows)
        render_labeled_scatter(
            frame,
            ASSET_ROOT / str(spec["png"]),
            x_column=str(spec["x"]),
            y_column=str(spec["y"]),
            title=str(spec["title"]),
            xlabel=str(spec["xlabel"]),
            ylabel=str(spec["ylabel"]),
            size_column=str(spec.get("size") or "") or None,
            color_column=str(spec.get("color") or "") or None,
            category_column=str(spec.get("category") or "") or None,
            category_colors=spec.get("colors") if isinstance(spec.get("colors"), dict) else None,
            cmap=str(spec.get("cmap") or "viridis"),
            colorbar_label=str(spec.get("colorbar") or ""),
            median_lines=bool(spec.get("median")),
            percent_x=bool(spec.get("percent_x")),
            percent_y=bool(spec.get("percent_y")),
            note=str(spec.get("note") or ""),
            figsize=(11.2, 7.0),
        )


def rebuild_channel_source_aarrr_assets() -> None:
    try:
        import pandas as pd
    except Exception:
        return
    source_path = ASSET_ROOT / "ops_roi_cac_quadrant.csv"
    if not source_path.exists():
        return
    source_frame = pd.read_csv(source_path, encoding="utf-8-sig")
    detail = build_channel_source_aarrr_detail(source_frame)
    if detail.empty:
        return
    detail_path = ASSET_ROOT / f"{CHANNEL_SOURCE_AARRR_DETAIL}.csv"
    detail.to_csv(detail_path, index=False, encoding="utf-8-sig")
    topn, selection_payload = select_channel_source_aarrr_topn(detail, top_n=12)
    topn_path = ASSET_ROOT / f"{CHANNEL_SOURCE_AARRR_TOPN}.csv"
    topn.to_csv(topn_path, index=False, encoding="utf-8-sig")
    (JOB_ROOT / "ops_channel_source_aarrr_topn_selection.json").write_text(
        json.dumps(selection_payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    render_aarrr_small_multiples(
        topn,
        ASSET_ROOT / f"{CHANNEL_SOURCE_AARRR_TOPN}.png",
        title="Top12 渠道 × 流量来源 AARRR 差异图组",
        columns=4,
        rows=3,
        title_prefix_column="展示排序",
    )
    render_aarrr_all_pages(detail, ASSET_ROOT, rows=3, columns=3)


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value if value is not None else "").replace("|", " / ").replace("\n", "<br>").strip()

    lines = ["| " + " | ".join(clean(header) for header in headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        padded = list(row)[: len(headers)] + [""] * max(0, len(headers) - len(row))
        lines.append("| " + " | ".join(clean(value) for value in padded) + " |")
    return "\n".join(lines)


def build_roi_full_list_section(*, include_paired_tables: bool = True) -> str:
    csv_path = ASSET_ROOT / "ops_roi_cac_quadrant.csv"
    rows = _ensure_point_ids(_read_csv_dicts(csv_path), csv_path)
    if not rows:
        return ""
    rows = _with_roi_quadrants(rows)
    quadrant_reps = _representative_roi_quadrants(rows)
    display_rows = rows
    headers = list(rows[0].keys())
    conclusion_headers = ["象限", "管理结论", "代表对象", "图中序号", "真实投放回报（roi）", "获客成本（cac）", "收入", "运营成本", "付费用户", "动作边界"]
    conclusion_rows = [
        [
            row.get("象限"),
            row.get("结论"),
            _row_identity(row),
            row.get("图中序号"),
            _fmt_for_column("roi", row.get("roi")),
            _fmt_for_column("cac", row.get("cac")),
            _fmt_for_column("revenue", row.get("revenue")),
            _fmt_for_column("operating_cost", row.get("operating_cost")),
            _fmt_for_column("paid_users", row.get("paid_users")),
            row.get("建议动作"),
        ]
        for row in quadrant_reps
    ]
    parts = [
        "## 真实投放回报 × 获客成本四象限全列表",
        "",
        "**结论**：这张图不是只告诉读者“哪些对象要止损”，而是给出完整预算迁移方向：加码象限负责承接迁入，提效象限先压获客成本，验证象限用低成本测试承接，止损象限 Day 1 冻结或降权。下面先放四象限结论索引，再放图和全量配表，避免读者只看到同一方向的高成本样本。",
        "",
        "### 真实投放回报 × 获客成本四象限结论索引",
        "",
        _markdown_table(conclusion_headers, conclusion_rows),
        "",
        "这组表以 `source_visual_assets/ops_roi_cac_quadrant.csv` 为权威源，所有底层行和所有底层列都进入主报告。为保证 PDF 不丢列、不横向溢出，按对象、漏斗规模、收入成本、效率质量、象限决策拆成续表，并在每张续表重复“渠道 / 流量来源”。",
        "",
        "![真实投放回报 × 获客成本四象限图（roi / cac）](source_visual_assets/ops_roi_cac_quadrant.png)",
        "",
        *_chart_explanation_block("ops_roi_cac_quadrant.csv", headers, len(rows), rows, include_paired_tables=include_paired_tables),
        "",
    ]
    if include_paired_tables:
        total = len(ROI_COLUMN_GROUPS)
        for idx, (group_title, columns) in enumerate(ROI_COLUMN_GROUPS, start=1):
            headers = [FIELD_LABELS.get(column, column) for column in columns]
            table_rows = [[_fmt_for_column(column, row.get(column)) for column in columns] for row in display_rows]
            parts.extend(
                [
                    f"### 真实投放回报 × 获客成本四象限全列表（续表 {idx}/{total}：{group_title}，全 {len(display_rows)} 行）",
                    "",
                    _markdown_table(headers, table_rows),
                    "",
            ]
        )
    else:
        chunks = _split_csv_columns_with_keys(list(rows[0].keys()), ["图中序号"], values_per_chunk=7)
        for idx, columns in enumerate(chunks, start=1):
            table_headers = [_header_label(column) for column in columns]
            table_rows = [[_fmt_for_column(column, row.get(column)) for column in columns] for row in rows]
            parts.extend(
                [
                    f"### 真实投放回报 × 获客成本四象限图：图中序号映射配表（续表 {idx}/{len(chunks)}，全 {len(rows)} 行）",
                    "",
                    _markdown_table(table_headers, table_rows),
                    "",
                ]
            )
    return "\n".join(parts).strip()


def build_correlation_significance_section(correlation_rows: list[dict[str, Any]]) -> str:
    if not correlation_rows:
        return ""
    headers = ["左侧指标", "右侧指标", "样本量 n", "相关系数 r", "p 值", "q 值（BH）", "95% CI", "显著性结论"]
    table_rows = []
    for row in correlation_rows:
        table_rows.append(
            [
                row.get("left", ""),
                row.get("right", ""),
                row.get("n", ""),
                _fmt(row.get("pearson_r"), 4),
                _fmt(row.get("p_value"), 5),
                _fmt(row.get("q_value_bh"), 5),
                f"{_fmt(row.get('ci95_low'), 4)} ~ {_fmt(row.get('ci95_high'), 4)}",
                row.get("significance_label", ""),
            ]
        )
    return "\n".join(
        [
            "## 相关性显著性检验",
            "",
            "相关性统一采用 Pearson 相关系数，并补充样本量 n、p 值、BH 校正后的 q 值、95% 置信区间和显著性结论。显著性规则固定为：p < 0.05 且 q < 0.05 为显著；p < 0.10 或 q < 0.10 为边缘显著；n < 8 不做显著性结论。",
            "",
            _markdown_table(headers, table_rows),
        ]
    )


def _header_label(column: str) -> str:
    if column in FIELD_LABELS:
        return FIELD_LABELS[column]
    if any("\u4e00" <= char <= "\u9fff" for char in column):
        return column
    return "字段：" + column


def _split_csv_columns(headers: list[str]) -> list[list[str]]:
    key_priority = [
        "图中序号",
        "channel",
        "traffic_source",
        "city_tier",
        "user_segment",
        "content_category",
        "product_module",
        "campaign",
        "time_window",
        "字段名",
        "阶段",
        "止损原因",
        "对象组合",
        "组合",
    ]
    key_columns = [column for column in key_priority if column in headers][:3]
    value_columns = [column for column in headers if column not in key_columns]
    if len(headers) <= 8:
        return [headers]
    chunks: list[list[str]] = []
    for start in range(0, len(value_columns), 5):
        chunk = key_columns + value_columns[start : start + 5]
        chunks.append(chunk)
    return chunks


def _split_csv_columns_with_keys(headers: list[str], key_columns: list[str], *, values_per_chunk: int = 5) -> list[list[str]]:
    keys = [column for column in key_columns if column in headers]
    value_columns = [column for column in headers if column not in keys]
    if len(headers) <= len(keys) + values_per_chunk:
        return [headers]
    return [keys + value_columns[start : start + values_per_chunk] for start in range(0, len(value_columns), values_per_chunk)]


def _ensure_point_ids(rows: list[dict[str, Any]], csv_path: Path) -> list[dict[str, Any]]:
    numbered_rows, fields, changed = ensure_point_ids_records(rows)
    if changed and numbered_rows:
        _write_csv_dicts(csv_path, numbered_rows, fields)
    return numbered_rows


def build_channel_source_aarrr_section(*, include_paired_tables: bool = True) -> str:
    total_rows = _read_csv_dicts(ASSET_ROOT / "ops_aarrr_derived_funnel_rates.csv")
    topn_rows = _read_csv_dicts(ASSET_ROOT / f"{CHANNEL_SOURCE_AARRR_TOPN}.csv")
    detail_rows = _read_csv_dicts(ASSET_ROOT / f"{CHANNEL_SOURCE_AARRR_DETAIL}.csv")
    if not total_rows and not topn_rows:
        return ""
    parts: list[str] = []
    if total_rows:
        total_headers = list(total_rows[0].keys())
        parts.extend(
            [
                "## 增长漏斗总览（AARRR）",
                "",
                "总漏斗用于判断整张运营表的整体断点；组合漏斗用于判断同一总盘下不同渠道和流量来源为什么表现不同，二者必须一起看。",
                "",
                *_chart_explanation_block("ops_aarrr_derived_funnel_rates.csv", total_headers, len(total_rows), total_rows, include_paired_tables=True),
                "",
                "![增长漏斗派生率图（AARRR）](source_visual_assets/ops_aarrr_derived_funnel_rates.png)",
                "",
                "### 增长漏斗总览（AARRR）配表",
                "",
                _markdown_table([_header_label(column) for column in total_headers], [[_fmt_for_column(column, row.get(column)) for column in total_headers] for row in total_rows]),
                "",
            ]
        )
    if topn_rows:
        topn_headers = list(topn_rows[0].keys())
        parts.extend(
            [
                "## Top12 渠道 × 流量来源 AARRR 差异图组",
                "",
                "这组图不是把 AARRR 只画成一个总漏斗，而是把 Top12 渠道 × 流量来源组合逐一展开：每个小图同时展示阶段规模与关键相邻转化率，便于直接定位预算和承接断点。",
                "",
                *_chart_explanation_block(f"{CHANNEL_SOURCE_AARRR_TOPN}.csv", topn_headers, len(topn_rows), topn_rows, include_paired_tables=True),
                "",
                f"![Top12 渠道 × 流量来源 AARRR 差异图组](source_visual_assets/{CHANNEL_SOURCE_AARRR_TOPN}.png)",
                "",
                "## Top12 组合漏斗配表",
                "",
            ]
        )
        chunks = _split_csv_columns_with_keys(topn_headers, ["展示排序", "channel", "traffic_source"], values_per_chunk=6)
        for idx, columns in enumerate(chunks, start=1):
            parts.extend(
                [
                    f"### Top12 组合漏斗配表（续表 {idx}/{len(chunks)}，全 {len(topn_rows)} 行）",
                    "",
                    _markdown_table(
                        [_header_label(column) for column in columns],
                        [[_fmt_for_column(column, row.get(column)) for column in columns] for row in topn_rows],
                    ),
                    "",
                ]
            )
    if include_paired_tables and detail_rows:
        detail_headers = list(detail_rows[0].keys())
        page_paths = sorted(ASSET_ROOT.glob("ops_channel_source_aarrr_all_page_*.png"))
        parts.extend(
            [
                "## 全量渠道 × 流量来源 AARRR 分页图组（完整表版本）",
                "",
                "完整表版本会展开全部渠道 × 流量来源组合。图页按 3 × 3 分页，配表保留每个组合的全量阶段规模、转化率、收入成本和质量字段，不截断组合。",
                "",
            ]
        )
        for page_path in page_paths:
            page_label = page_path.stem.replace("ops_channel_source_aarrr_all_page_", "第 ") + " 页"
            parts.extend([f"![全量渠道 × 流量来源 AARRR 分页图组（{page_label}）](source_visual_assets/{page_path.name})", ""])
        chunks = _split_csv_columns_with_keys(detail_headers, ["channel", "traffic_source", "组合"], values_per_chunk=7)
        for idx, columns in enumerate(chunks, start=1):
            parts.extend(
                [
                    f"### 全量组合漏斗配表（续表 {idx}/{len(chunks)}，全 {len(detail_rows)} 行）",
                    "",
                    _markdown_table(
                        [_header_label(column) for column in columns],
                        [[_fmt_for_column(column, row.get(column)) for column in columns] for row in detail_rows],
                    ),
                    "",
                ]
            )
    return "\n".join(parts).strip()


def build_full_visual_data_section(*, include_paired_tables: bool = True) -> str:
    csv_paths = sorted(path for path in ASSET_ROOT.glob("ops_*.csv") if path.name not in {"ops_roi_cac_quadrant.csv", *AARRR_SPECIAL_CSV_NAMES})
    if not csv_paths:
        return ""
    if include_paired_tables:
        parts = [
            "## 派生指标图组：一图一表全量展示",
            "",
            "以下每张派生图都直接配一组底层全量表。宽表按列组拆成续表，重复关键对象列；不再使用 top-N 摘要代替全量图表数据。若图形本身是气泡图或象限图，配表会完整保留图背后的全部字段，并补充解释图形如何用于经营判断。",
            "",
        ]
    else:
        parts = [
            "## 派生指标图组：序号图与图级配表",
            "",
            "默认读者版不是不配表：点图、气泡图和象限图在图内只标短序号，并在图后用“图中序号”配表承接该图底层 CSV 的全部字段和值；只有开启完整表版本时才额外生成超长宽表报告。",
            "",
        ]
    for path in csv_paths:
        rows = _read_csv_dicts(path)
        if path.name in POINT_MAPPING_CSV_NAMES:
            rows = _ensure_point_ids(rows, path)
        if not rows:
            continue
        headers = list(rows[0].keys())
        chunks = _split_csv_columns(headers)
        chart_title = CHART_TITLES.get(path.name, path.stem)
        image_path = path.with_suffix(".png")
        parts.extend(
            [
                f"### {chart_title}",
                "",
                *_chart_explanation_block(path.name, headers, len(rows), rows, include_paired_tables=include_paired_tables),
                "",
            ]
        )
        if image_path.exists():
            parts.extend([f"![{chart_title}]({image_path.relative_to(JOB_ROOT).as_posix()})", ""])
        else:
            parts.extend(["图形文件未在 `source_visual_assets` 中生成，因此本节以完整底层表和口径说明替代图片展示。", ""])
        if include_paired_tables:
            for idx, columns in enumerate(chunks, start=1):
                suffix = f"（配表 {idx}/{len(chunks)}，全 {len(rows)} 行）" if len(chunks) > 1 else f"（配表，全 {len(rows)} 行）"
                table_headers = [_header_label(column) for column in columns]
                table_rows = [[_fmt_for_column(column, row.get(column)) for column in columns] for row in rows]
                parts.extend(
                    [
                        f"#### {chart_title}：底层全量数据{suffix}",
                        "",
                        _markdown_table(table_headers, table_rows),
                        "",
                    ]
                )
        elif path.name in POINT_MAPPING_CSV_NAMES:
            point_chunks = _split_csv_columns_with_keys(headers, ["图中序号"], values_per_chunk=7)
            for idx, columns in enumerate(point_chunks, start=1):
                table_headers = [_header_label(column) for column in columns]
                table_rows = [[_fmt_for_column(column, row.get(column)) for column in columns] for row in rows]
                parts.extend(
                    [
                        f"#### {chart_title}：图中序号映射配表（续表 {idx}/{len(point_chunks)}，全 {len(rows)} 行）",
                        "",
                        _markdown_table(table_headers, table_rows),
                        "",
                    ]
                )
        else:
            key_columns = [
                column
                for column in ["阶段", "止损原因", "字段名", "channel", "traffic_source", "content_category", "campaign", "product_module", "user_segment", "city_tier", "time_window", "对象组合", "组合"]
                if column in headers
            ][:2]
            chunks = _split_csv_columns_with_keys(headers, key_columns, values_per_chunk=7)
            for idx, columns in enumerate(chunks, start=1):
                table_headers = [_header_label(column) for column in columns]
                table_rows = [[_fmt_for_column(column, row.get(column)) for column in columns] for row in rows]
                parts.extend(
                    [
                        f"#### {chart_title}：图级配表（续表 {idx}/{len(chunks)}，全 {len(rows)} 行）",
                        "",
                        _markdown_table(table_headers, table_rows),
                        "",
                    ]
                )
    return "\n".join(parts).strip()


def write_visual_explanation_manifest() -> None:
    chart_rows: list[dict[str, Any]] = []
    narrative_sections: list[dict[str, Any]] = []
    for csv_path in sorted(ASSET_ROOT.glob("ops_*.csv")):
        rows = _read_csv_dicts(csv_path)
        headers = list(rows[0].keys()) if rows else []
        chart_id = csv_path.stem
        csv_name = csv_path.name
        narrative_card = build_chart_narrative_card(csv_name, headers, len(rows), rows, include_paired_tables=False)
        narrative_sections.append(narrative_card)
        chart_rows.append(
            {
                "chart_id": chart_id,
                "title": _chart_title(csv_name),
                "chart_type": _chart_type_from_name(csv_name),
                "png_path": f"source_visual_assets/{chart_id}.png",
                "csv_path": f"source_visual_assets/{csv_name}",
                "how_to_read": _chart_how_to_read(csv_name),
                "what_to_watch": _chart_watch_points(csv_name, headers),
                "numeric_evidence": _chart_numeric_facts(csv_name, rows, headers),
                "management_interpretation": CHART_EXPLANATIONS.get(csv_name, "这张图用于把派生指标转成对象判断，帮助读者从图形回到经营动作。"),
                "value_based_judgement": _chart_judgement(csv_name, rows, headers),
                "action_implication": _chart_action_implication(csv_name, rows, headers),
                "paired_table_rule": f"正文图解必须说明 `{csv_name}` 如何通过图中序号或组合名称回到配表复核；宽表只能拆续表，不能截断行或列。",
                "reader_narrative": narrative_card,
                "required_reader_blocks": ["图解", "对象数值", "配表衔接", "链路承接"],
                "row_count": len(rows),
                "columns": headers,
            }
        )
    payload = {
        "source": "deterministic_internet_ops_visual_explanation_manifest",
        "chart_count": len(chart_rows),
        "required_reader_blocks": ["图解", "对象数值", "配表衔接", "链路承接"],
        "charts": chart_rows,
    }
    (JOB_ROOT / "ops_visual_explanation_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    chart_narrative_payload = {
        "version": "ops_chart_narrative_sections_v1",
        "source": "deterministic_internet_ops_chart_narrative",
        "section_count": len(narrative_sections),
        "rules": {
            "visual_manifest_is_evidence_not_reader_structure": True,
            "no_label_blocks": True,
            "point_charts_require_bxx_references": True,
            "aarrr_requires_stage_sizes_and_conversion_rates": True,
        },
        "sections": narrative_sections,
    }
    JOB_CHART_NARRATIVE_SECTIONS.write_text(
        json.dumps(chart_narrative_payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    manifest_path = JOB_ROOT / "ops_derived_visual_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
        if isinstance(manifest, dict):
            by_chart_id = {row["chart_id"]: row for row in chart_rows}
            charts = []
            for chart in list(manifest.get("charts") or []):
                if isinstance(chart, dict):
                    chart_id = str(chart.get("chart_id") or "")
                    if chart_id in by_chart_id:
                        chart["reader_explanation"] = by_chart_id[chart_id]
                    charts.append(chart)
            if charts:
                manifest["charts"] = charts
                manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _split_markdown_cells(line: str) -> list[str]:
    text = line.rstrip("\n").strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def _normalize_cells(cells: list[str], expected: int, headers: list[str]) -> list[str]:
    cleaned = [cell.replace("|", " / ").strip() for cell in cells]
    if expected <= 0:
        return cleaned
    if len(cleaned) == expected:
        return cleaned
    if len(cleaned) < expected:
        return cleaned + [""] * (expected - len(cleaned))

    excess = len(cleaned) - expected
    merge_index = None
    merge_candidates = ["对象", "组合", "说明", "动作", "建议", "结论", "依赖", "原因", "用途", "检查点"]
    for idx, header in enumerate(headers):
        if any(token in header for token in merge_candidates):
            merge_index = idx
            break
    if merge_index is None:
        merge_index = 0
    merged = (
        cleaned[:merge_index]
        + [" / ".join(part for part in cleaned[merge_index : merge_index + excess + 1] if part)]
        + cleaned[merge_index + excess + 1 :]
    )
    if len(merged) > expected:
        merged = merged[: expected - 1] + [" / ".join(merged[expected - 1 :])]
    return merged[:expected] + [""] * max(0, expected - len(merged))


def normalize_markdown_tables(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    output: list[str] = []
    idx = 0
    while idx < len(lines):
        if not lines[idx].lstrip().startswith("|"):
            output.append(lines[idx])
            idx += 1
            continue

        block: list[str] = []
        while idx < len(lines) and lines[idx].lstrip().startswith("|"):
            block.append(lines[idx])
            idx += 1
        if len(block) < 2:
            output.extend(block)
            continue

        headers = _split_markdown_cells(block[0])
        separator = _split_markdown_cells(block[1])
        expected = len(headers)
        if not _is_table_separator(separator):
            output.extend(block)
            continue

        output.append("| " + " | ".join(cell.replace("|", " / ") for cell in headers) + " |")
        output.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in block[2:]:
            cells = _normalize_cells(_split_markdown_cells(row), expected, headers)
            output.append("| " + " | ".join(cells) + " |")
    return "\n".join(output).strip() + "\n"


def _remove_section(markdown_text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}.*?(?=^##\s+|\Z)", flags=re.M | re.S)
    return pattern.sub("", markdown_text).strip() + "\n"


def _insert_before_appendix(markdown_text: str, section: str) -> str:
    if not section.strip():
        return markdown_text
    anchor = "\n## 30/60/90"
    idx = markdown_text.find(anchor)
    if idx >= 0:
        return markdown_text[:idx].rstrip() + "\n\n" + section.strip() + "\n" + markdown_text[idx:]
    return markdown_text.rstrip() + "\n\n" + section.strip() + "\n"


def rebuild_markdown(correlation_rows: list[dict[str, Any]], *, include_paired_tables: bool = True) -> str:
    source = JOB_MD if JOB_MD.exists() else ROOT_MD
    markdown_text = source.read_text(encoding="utf-8", errors="ignore")
    markdown_text = _remove_section(markdown_text, "真实投放回报 × 获客成本四象限全列表")
    markdown_text = _remove_section(markdown_text, "真实投放回报 × 获客成本四象限图（roi / cac）")
    markdown_text = _remove_section(markdown_text, "相关性显著性检验")
    markdown_text = _remove_section(markdown_text, "派生图底层全量数据附表")
    markdown_text = _remove_section(markdown_text, "派生指标图组")
    markdown_text = _remove_section(markdown_text, "派生指标图组：一图一表全量展示")
    markdown_text = _remove_section(markdown_text, "增长漏斗总览（AARRR）")
    markdown_text = _remove_section(markdown_text, "Top12 渠道 × 流量来源 AARRR 差异图组")
    markdown_text = _remove_section(markdown_text, "Top12 组合漏斗配表")
    markdown_text = _remove_section(markdown_text, "全量渠道 × 流量来源 AARRR 分页图组（完整表版本）")
    markdown_text = _remove_section(markdown_text, "核心表格读表与后续动作")
    markdown_text = _remove_section(markdown_text, "核心表格判断标准与经营取舍")
    markdown_text = _remove_section(markdown_text, "核心经营链路：从预算止损到承接实验")
    # Remove legacy standalone derived images. They will be reinserted only in
    # chart+explanation+full-table sections below.
    markdown_text = re.sub(
        r"\n*!\[[^\]]*\]\(source_visual_assets/ops_[^)]+\.png\)\n*",
        "\n\n",
        markdown_text,
    )
    markdown_text = _insert_before_appendix(markdown_text, build_channel_source_aarrr_section(include_paired_tables=include_paired_tables))
    markdown_text = _insert_before_appendix(markdown_text, build_roi_full_list_section(include_paired_tables=include_paired_tables))
    markdown_text = _insert_before_appendix(markdown_text, build_correlation_significance_section(correlation_rows))
    markdown_text = _insert_before_appendix(markdown_text, build_full_visual_data_section(include_paired_tables=include_paired_tables))
    markdown_text = _insert_before_appendix(markdown_text, render_ops_table_reading_cards_markdown(JOB_ROOT))
    markdown_text = markdown_text.replace("**判断标准**：", "先看")
    markdown_text = markdown_text.replace("**标准公式**：", "这把尺子综合")
    markdown_text = markdown_text.replace("**标准下的对象分层**：", "对象因此分成几类：")
    markdown_text = markdown_text.replace("**关键对象差异**：", "关键分化在这里：")
    markdown_text = markdown_text.replace("**经营结论**：", "当前读数显示，")
    markdown_text = markdown_text.replace("**本周取舍**：", "本周执行上，")
    markdown_text = markdown_text.replace("**表格问题**：", "")
    markdown_text = markdown_text.replace("**后续动作**：", "动作落地上，")
    markdown_text = markdown_text.replace("**边界说明**：", "边界上，")
    markdown_text = normalize_markdown_tables(markdown_text)
    return markdown_text


def _render_inline(text: str) -> str:
    rendered = html.escape(text)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    return rendered


def markdown_to_html(markdown_text: str, *, css_name: str) -> str:
    lines = markdown_text.splitlines()
    body: list[str] = []
    idx = 0
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            body.append("</ul>")
            in_list = False

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if not stripped:
            close_list()
            idx += 1
            continue

        if stripped.startswith("|"):
            close_list()
            block: list[str] = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                block.append(lines[idx])
                idx += 1
            if len(block) >= 2:
                headers = _split_markdown_cells(block[0])
                expected = len(headers)
                rows = [_normalize_cells(_split_markdown_cells(row), expected, headers) for row in block[2:]]
                table_class = "report-table-block report-table-block--wide" if expected > 6 else "report-table-block"
                body.append(f'<div class="{table_class}"><div class="table-scroll"><table>')
                body.append("<thead><tr>" + "".join(f"<th>{_render_inline(cell)}</th>" for cell in headers) + "</tr></thead>")
                body.append("<tbody>")
                for row in rows:
                    body.append("<tr>" + "".join(f"<td>{_render_inline(cell)}</td>" for cell in row) + "</tr>")
                body.append("</tbody></table></div></div>")
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            close_list()
            level = min(len(heading.group(1)), 3)
            body.append(f"<h{level}>{_render_inline(heading.group(2))}</h{level}>")
            idx += 1
            continue

        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image:
            close_list()
            alt = html.escape(image.group(1))
            src = html.escape(image.group(2))
            body.append(
                f'<figure><img src="{src}" alt="{alt}"><figcaption>{alt}</figcaption></figure>'
            )
            idx += 1
            continue

        list_item = re.match(r"^[-*]\s+(.+)$", stripped)
        if list_item:
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{_render_inline(list_item.group(1))}</li>")
            idx += 1
            continue

        close_list()
        body.append(f"<p>{_render_inline(stripped)}</p>")
        idx += 1

    close_list()
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>互联网运营分析报告</title>",
            f'<link rel="stylesheet" href="{html.escape(css_name)}">',
            "</head>",
            "<body>",
            '<main class="report-shell">',
            *body,
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def validate_tables(markdown_text: str, html_text: str) -> None:
    errors: list[str] = []
    blocks = re.findall(r"((?:^\|.*\n?)+)", markdown_text, flags=re.M)
    for index, block in enumerate(blocks, start=1):
        rows = [line for line in block.splitlines() if line.strip().startswith("|")]
        if len(rows) < 2:
            continue
        counts = [len(_split_markdown_cells(row)) for row in rows]
        if len(set(counts)) > 1:
            errors.append(f"Markdown 表 {index} 行列不一致：{sorted(set(counts))}")
    for index, table in enumerate(re.findall(r"<table\b[^>]*>(.*?)</table>", html_text, flags=re.I | re.S), start=1):
        counts = []
        for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, flags=re.I | re.S):
            count = len(re.findall(r"<t[dh]\b", row, flags=re.I))
            if count:
                counts.append(count)
        if counts and len(set(counts)) > 1:
            errors.append(f"HTML 表 {index} 行列不一致：{sorted(set(counts))}")
    if errors:
        raise RuntimeError("; ".join(errors[:20]))


def validate_current_outputs(markdown_text: str, html_text: str, *, require_paired_tables: bool = True) -> dict[str, Any]:
    validate_tables(markdown_text, html_text)
    combined = markdown_text + "\n" + html_text
    forbidden_label_pattern = re.compile(r"(\*\*)?(数值证据|经营判断|动作指向|配表关系)(\*\*)?\s*[：:]")
    residue_terms = sorted({match.group(2) for match in forbidden_label_pattern.finditer(combined)})
    forbidden_phrases = [
        "图形解释必须绑定具体数值",
        "用于把图中的对象差异转成 owner 动作",
    ]
    residue_terms.extend([term for term in forbidden_phrases if term in combined])
    if residue_terms:
        raise RuntimeError("报告仍残留字段式图解或内部提示：" + ", ".join(residue_terms))
    required_terms = [
        "样本量 n",
        "相关系数 r",
        "p 值",
        "q 值（BH）",
        "显著性结论",
        "图解",
        "配表",
        "关键分化",
        "图中序号",
        "结论",
        "%",
        "真实投放回报 × 获客成本四象限结论索引",
        "加码象限：高 roi / 低 cac",
        "提效象限：高 roi / 高 cac",
        "验证象限：低 roi / 低 cac",
        "止损象限：低 roi / 高 cac",
    ]
    if require_paired_tables:
        required_terms.extend(
            [
                "真实投放回报 × 获客成本四象限全列表",
                "派生指标图组：一图一表全量展示",
            ]
        )
    else:
        required_terms.extend(
            [
                "派生指标图组：序号图与图级配表",
                "图中序号映射配表",
                "默认读者版不是不配表",
                "增长漏斗总览（AARRR）",
                "Top12 渠道 × 流量来源 AARRR 差异图组",
                "Top12 组合漏斗配表",
                "B01",
            ]
        )
    missing = [term for term in required_terms if term not in combined]
    if missing:
        raise RuntimeError("报告缺少必需文本：" + ", ".join(missing))
    chart_narrative_hits = len(re.findall(r"\*\*图解\*\*|图解：", combined))
    if chart_narrative_hits < 10:
        raise RuntimeError(f"图表连续图解不足：仅发现 {chart_narrative_hits} 段")
    if JOB_CHART_NARRATIVE_SECTIONS.exists():
        chart_payload = json.loads(JOB_CHART_NARRATIVE_SECTIONS.read_text(encoding="utf-8"))
    elif ROOT_CHART_NARRATIVE_SECTIONS.exists():
        chart_payload = json.loads(ROOT_CHART_NARRATIVE_SECTIONS.read_text(encoding="utf-8"))
    else:
        raise RuntimeError("缺少 ops_chart_narrative_sections.json")
    if str(chart_payload.get("version") or "") != "ops_chart_narrative_sections_v1":
        raise RuntimeError("ops_chart_narrative_sections.json 版本不正确")
    chart_sections = chart_payload.get("sections")
    if not isinstance(chart_sections, list) or len(chart_sections) < 10:
        raise RuntimeError("ops_chart_narrative_sections.json 未覆盖足够的 reader-facing 图表")
    bxx_markers = set(re.findall(r"\bB\d{2}\b", combined))
    if len(bxx_markers) < 10:
        raise RuntimeError("图中短序号不足，点图/气泡图/象限图未充分标注")
    roi_rows = _read_csv_dicts(ASSET_ROOT / "ops_roi_cac_quadrant.csv")
    if roi_rows:
        if require_paired_tables:
            missing_columns = [
                FIELD_LABELS.get(column, column)
                for column in roi_rows[0].keys()
                if FIELD_LABELS.get(column, column) not in combined and column not in combined
            ]
            if missing_columns:
                raise RuntimeError("ROI × CAC 全列表缺少列：" + ", ".join(missing_columns))
        missing_pairs = []
        for row in roi_rows:
            channel = str(row.get("channel") or "").strip()
            traffic_source = str(row.get("traffic_source") or "").strip()
            if not channel or not traffic_source:
                continue
            variants = [
                f"{channel} / {traffic_source}",
                f"{channel}|{traffic_source}",
                f"{channel} | {traffic_source}",
                f"{channel}｜{traffic_source}",
            ]
            if not any(variant in combined for variant in variants):
                missing_pairs.append(f"{channel} / {traffic_source}")
        if require_paired_tables and missing_pairs:
            raise RuntimeError("ROI × CAC 全列表缺少对象行：" + ", ".join(missing_pairs[:20]))
    topn_rows = _read_csv_dicts(ASSET_ROOT / f"{CHANNEL_SOURCE_AARRR_TOPN}.csv")
    detail_rows = _read_csv_dicts(ASSET_ROOT / f"{CHANNEL_SOURCE_AARRR_DETAIL}.csv")
    if len(topn_rows) < min(12, len(detail_rows) if detail_rows else 12):
        raise RuntimeError("Top12 渠道 × 流量来源 AARRR 组合漏斗不足 12 个或未正确生成")
    if topn_rows and f"{CHANNEL_SOURCE_AARRR_TOPN}.png" not in combined:
        raise RuntimeError("主报告缺少 Top12 渠道 × 流量来源 AARRR 小倍图")
    if require_paired_tables:
        all_page_refs = list(ASSET_ROOT.glob("ops_channel_source_aarrr_all_page_*.png"))
        if detail_rows and all_page_refs and "全量渠道 × 流量来源 AARRR 分页图组" not in combined:
            raise RuntimeError("完整表版本缺少全量渠道 × 流量来源 AARRR 分页图组")
    return {
        "markdown_tables": len(re.findall(r"((?:^\|.*\n?)+)", markdown_text, flags=re.M)),
        "html_tables": len(re.findall(r"<table\b", html_text, flags=re.I)),
        "roi_columns": len(roi_rows[0].keys()) if roi_rows else 0,
        "aarrr_topn_rows": len(topn_rows),
        "aarrr_detail_rows": len(detail_rows),
    }


def copy_asset_tree() -> None:
    BUNDLE_ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    for asset in ASSET_ROOT.glob("*"):
        if asset.is_file():
            shutil.copy2(asset, BUNDLE_ASSET_ROOT / asset.name)


def update_current_turn_manifest_with_management_brief() -> None:
    manifest_path = REPORT_ROOT / f"{REPORT_ID}-current_turn_export_manifest.json"
    if not manifest_path.exists():
        return
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    downloadables = list(payload.get("downloadables") or [])
    replacement_names = {
        ROOT_MD_BRIEF.name,
        ROOT_HTML_BRIEF.name,
        ROOT_PDF_BRIEF.name,
        ROOT_MD_WITH_TABLES.name,
        ROOT_HTML_WITH_TABLES.name,
        ROOT_PDF_WITH_TABLES.name,
        ROOT_MANAGEMENT_QUADRANT_INDEX_JSON.name,
        ROOT_MANAGEMENT_QUADRANT_INDEX_CSV.name,
        ROOT_DERIVED_METRIC_DIAGNOSIS_CARDS.name,
        ROOT_CHANNEL_SOURCE_KPI_CANONICAL_JSON.name,
        ROOT_CHANNEL_SOURCE_KPI_CANONICAL_CSV.name,
        ROOT_MANAGEMENT_THRESHOLDS_JSON.name,
        ROOT_EXECUTIVE_ACTION_RULES_JSON.name,
    }
    downloadables = [item for item in downloadables if str((item or {}).get("name") or "") not in replacement_names]
    entries = [
        (ROOT_PDF_BRIEF, "pdf", "互联网运营高密度精简管理版 PDF"),
        (ROOT_MD_BRIEF, "md", "互联网运营高密度精简管理版 Markdown"),
        (BUNDLE_HTML_BRIEF if BUNDLE_HTML_BRIEF.exists() else ROOT_HTML_BRIEF, "html", "互联网运营高密度精简管理版 HTML"),
        (ROOT_MANAGEMENT_QUADRANT_INDEX_JSON, "json", "管理版核心图表象限对象清单合同 JSON"),
        (ROOT_MANAGEMENT_QUADRANT_INDEX_CSV, "csv", "管理版核心图表象限对象清单 CSV"),
        (ROOT_DERIVED_METRIC_DIAGNOSIS_CARDS, "json", "管理版派生指标深度解读合同 JSON"),
        (ROOT_CHANNEL_SOURCE_KPI_CANONICAL_JSON, "json", "渠道 × 流量来源权威 KPI 合同 JSON"),
        (ROOT_CHANNEL_SOURCE_KPI_CANONICAL_CSV, "csv", "渠道 × 流量来源权威 KPI 合同 CSV"),
        (ROOT_MANAGEMENT_THRESHOLDS_JSON, "json", "管理版象限阈值口径合同 JSON"),
        (ROOT_EXECUTIVE_ACTION_RULES_JSON, "json", "管理版可执行动作规则合同 JSON"),
    ]
    for path, file_type, purpose in entries:
        if not path.exists():
            continue
        downloadables.append(
            {
                "name": path.name,
                "path": f"/storage/{path.relative_to(REPO_ROOT / 'workspace' / 'storage').as_posix()}",
                "file_path": str(path.resolve()),
                "type": file_type,
                "purpose": purpose,
                "is_main": False,
                "size_bytes": path.stat().st_size,
            }
        )
    full_table_entries = [
        (ROOT_PDF_WITH_TABLES, "pdf", "完整表版本（长版审计 PDF）"),
        (ROOT_MD_WITH_TABLES, "md", "完整表版本（长版审计 Markdown）"),
        (ROOT_HTML_WITH_TABLES, "html", "完整表版本（长版审计 HTML）"),
    ]
    for path, file_type, purpose in full_table_entries:
        if not path.exists():
            continue
        downloadables.append(
            {
                "name": path.name,
                "path": f"/storage/{path.relative_to(REPO_ROOT / 'workspace' / 'storage').as_posix()}",
                "file_path": str(path.resolve()),
                "type": file_type,
                "purpose": purpose,
                "is_main": False,
                "size_bytes": path.stat().st_size,
            }
        )
    payload["downloadables"] = downloadables
    payload["downloadable_count"] = len(downloadables)
    payload.setdefault("internet_ops_management_brief", {})
    payload["internet_ops_management_brief"].update(
        {
            "markdown_path": str(ROOT_MD_BRIEF.resolve()) if ROOT_MD_BRIEF.exists() else "",
            "html_path": str((BUNDLE_HTML_BRIEF if BUNDLE_HTML_BRIEF.exists() else ROOT_HTML_BRIEF).resolve())
            if (BUNDLE_HTML_BRIEF.exists() or ROOT_HTML_BRIEF.exists())
            else "",
            "pdf_path": str(ROOT_PDF_BRIEF.resolve()) if ROOT_PDF_BRIEF.exists() else "",
        }
    )
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def cleanup_optional_variant_outputs(*, generate_full_table_version: bool) -> None:
    legacy_suffix = "_no" + "_tables"
    paths = [
        REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow{legacy_suffix}.md",
        REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow{legacy_suffix}.html",
        REPORT_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow{legacy_suffix}.pdf",
        JOB_ROOT / f"05_report{legacy_suffix}.md",
        JOB_ROOT / f"06_report{legacy_suffix}.html",
        JOB_ROOT / f"07_report{legacy_suffix}.pdf",
        BUNDLE_ROOT / f"{REPORT_ID}-internet_ops_cli_shadow{legacy_suffix}.html",
    ]
    if not generate_full_table_version:
        paths.extend(
            [
                ROOT_MD_WITH_TABLES,
                ROOT_HTML_WITH_TABLES,
                ROOT_PDF_WITH_TABLES,
                JOB_MD_WITH_TABLES,
                JOB_HTML_WITH_TABLES,
                JOB_PDF_WITH_TABLES,
            ]
        )
    for path in paths:
        if path.is_file():
            path.unlink()


def render_pdf(*, html_path: Path = JOB_HTML, css_path: Path = JOB_CSS, output_pdf_path: Path = JOB_PDF) -> dict[str, Any]:
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.services.codex_runtime_pdf_render_service import render_html_to_pdf

    return render_html_to_pdf(html_path=html_path, css_path=css_path, output_pdf_path=output_pdf_path, timeout_sec=900)


def main() -> None:
    generate_full_table_version = os.getenv("GENERATE_FULL_TABLE_VERSION", "0").strip().lower() in {"1", "true", "yes", "on"}
    correlation_rows = rebuild_correlation_significance()
    rebuild_channel_source_aarrr_assets()
    ensure_ops_management_fact_contracts(JOB_ROOT)
    write_ops_derived_metric_diagnosis_cards(JOB_ROOT)
    redraw_cost_margin_share_chart()
    redraw_labeled_point_charts()
    write_visual_explanation_manifest()
    markdown_text = rebuild_markdown(correlation_rows, include_paired_tables=False)
    markdown_with_tables = rebuild_markdown(correlation_rows, include_paired_tables=True) if generate_full_table_version else ""
    html_text = markdown_to_html(markdown_text, css_name=JOB_CSS.name)
    html_with_tables = markdown_to_html(markdown_with_tables, css_name=JOB_CSS.name) if generate_full_table_version else ""
    management_brief_markdown = build_internet_ops_management_brief_markdown(JOB_ROOT)
    management_brief_html = render_management_brief_html(management_brief_markdown, css_name=JOB_CSS.name)
    validation = validate_current_outputs(markdown_text, html_text, require_paired_tables=False)
    validation_with_tables = (
        validate_current_outputs(markdown_with_tables, html_with_tables, require_paired_tables=True)
        if generate_full_table_version
        else {}
    )
    management_brief_validation = validate_management_brief(management_brief_markdown, management_brief_html, workspace=JOB_ROOT)

    JOB_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    BUNDLE_ROOT.mkdir(parents=True, exist_ok=True)
    cleanup_optional_variant_outputs(generate_full_table_version=generate_full_table_version)

    JOB_MD.write_text(markdown_text, encoding="utf-8")
    ROOT_MD.write_text(markdown_text, encoding="utf-8")
    JOB_MD_BRIEF.write_text(management_brief_markdown, encoding="utf-8")
    ROOT_MD_BRIEF.write_text(management_brief_markdown, encoding="utf-8")
    if JOB_TABLE_READING_CARDS.exists():
        ROOT_TABLE_READING_CARDS.write_text(JOB_TABLE_READING_CARDS.read_text(encoding="utf-8"), encoding="utf-8")
    if JOB_MANAGEMENT_QUADRANT_INDEX_JSON.exists():
        ROOT_MANAGEMENT_QUADRANT_INDEX_JSON.write_text(
            JOB_MANAGEMENT_QUADRANT_INDEX_JSON.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    if JOB_MANAGEMENT_QUADRANT_INDEX_CSV.exists():
        ROOT_MANAGEMENT_QUADRANT_INDEX_CSV.write_text(
            JOB_MANAGEMENT_QUADRANT_INDEX_CSV.read_text(encoding="utf-8-sig"),
            encoding="utf-8-sig",
        )
    if JOB_DERIVED_METRIC_DIAGNOSIS_CARDS.exists():
        ROOT_DERIVED_METRIC_DIAGNOSIS_CARDS.write_text(
            JOB_DERIVED_METRIC_DIAGNOSIS_CARDS.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    for source, target, encoding in [
        (JOB_ROOT / CHANNEL_SOURCE_KPI_CANONICAL_JSON_NAME, ROOT_CHANNEL_SOURCE_KPI_CANONICAL_JSON, "utf-8"),
        (JOB_ROOT / CHANNEL_SOURCE_KPI_CANONICAL_CSV_NAME, ROOT_CHANNEL_SOURCE_KPI_CANONICAL_CSV, "utf-8-sig"),
        (JOB_ROOT / MANAGEMENT_THRESHOLDS_JSON_NAME, ROOT_MANAGEMENT_THRESHOLDS_JSON, "utf-8"),
        (JOB_ROOT / EXECUTIVE_ACTION_RULES_JSON_NAME, ROOT_EXECUTIVE_ACTION_RULES_JSON, "utf-8"),
    ]:
        if source.exists():
            target.write_text(source.read_text(encoding=encoding), encoding=encoding)
    if JOB_CHART_NARRATIVE_SECTIONS.exists():
        ROOT_CHART_NARRATIVE_SECTIONS.write_text(
            JOB_CHART_NARRATIVE_SECTIONS.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    if generate_full_table_version:
        JOB_MD_WITH_TABLES.write_text(markdown_with_tables, encoding="utf-8")
        ROOT_MD_WITH_TABLES.write_text(markdown_with_tables, encoding="utf-8")

    JOB_CSS.write_text(REPORT_CSS, encoding="utf-8")
    ROOT_CSS.write_text(REPORT_CSS, encoding="utf-8")
    BUNDLE_CSS.write_text(REPORT_CSS, encoding="utf-8")

    JOB_HTML.write_text(html_text, encoding="utf-8")
    ROOT_HTML.write_text(markdown_to_html(markdown_text, css_name=ROOT_CSS.name), encoding="utf-8")
    BUNDLE_HTML.write_text(markdown_to_html(markdown_text, css_name=BUNDLE_CSS.name), encoding="utf-8")
    JOB_HTML_BRIEF.write_text(management_brief_html, encoding="utf-8")
    ROOT_HTML_BRIEF.write_text(render_management_brief_html(management_brief_markdown, css_name=ROOT_CSS.name), encoding="utf-8")
    BUNDLE_HTML_BRIEF.write_text(render_management_brief_html(management_brief_markdown, css_name=BUNDLE_CSS.name), encoding="utf-8")
    if generate_full_table_version:
        JOB_HTML_WITH_TABLES.write_text(html_with_tables, encoding="utf-8")
        ROOT_HTML_WITH_TABLES.write_text(markdown_to_html(markdown_with_tables, css_name=ROOT_CSS.name), encoding="utf-8")

    copy_asset_tree()
    render_result = render_pdf(html_path=JOB_HTML, css_path=JOB_CSS, output_pdf_path=JOB_PDF)
    shutil.copy2(JOB_PDF, ROOT_PDF)
    render_result_brief = render_pdf(html_path=JOB_HTML_BRIEF, css_path=JOB_CSS, output_pdf_path=JOB_PDF_BRIEF)
    shutil.copy2(JOB_PDF_BRIEF, ROOT_PDF_BRIEF)
    render_result_with_tables: dict[str, Any] = {}
    if generate_full_table_version:
        render_result_with_tables = render_pdf(html_path=JOB_HTML_WITH_TABLES, css_path=JOB_CSS, output_pdf_path=JOB_PDF_WITH_TABLES)
        shutil.copy2(JOB_PDF_WITH_TABLES, ROOT_PDF_WITH_TABLES)
    update_current_turn_manifest_with_management_brief()

    result = {
        **validation,
        "generate_full_table_version": generate_full_table_version,
        "full_table_variant": validation_with_tables,
        "management_brief_variant": management_brief_validation,
        "correlation_rows": len(correlation_rows),
        "job_pdf_bytes": JOB_PDF.stat().st_size if JOB_PDF.exists() else 0,
        "root_pdf_bytes": ROOT_PDF.stat().st_size if ROOT_PDF.exists() else 0,
        "job_pdf_management_brief_bytes": JOB_PDF_BRIEF.stat().st_size if JOB_PDF_BRIEF.exists() else 0,
        "root_pdf_management_brief_bytes": ROOT_PDF_BRIEF.stat().st_size if ROOT_PDF_BRIEF.exists() else 0,
        "job_pdf_with_tables_bytes": JOB_PDF_WITH_TABLES.stat().st_size if generate_full_table_version and JOB_PDF_WITH_TABLES.exists() else 0,
        "root_pdf_with_tables_bytes": ROOT_PDF_WITH_TABLES.stat().st_size if generate_full_table_version and ROOT_PDF_WITH_TABLES.exists() else 0,
        "render_engine": render_result.get("engine"),
        "render_engine_management_brief": render_result_brief.get("engine"),
        "render_engine_with_tables": render_result_with_tables.get("engine"),
        "reader_outputs": {
            "markdown": str(ROOT_MD),
            "html": str(ROOT_HTML),
            "pdf": str(ROOT_PDF),
        },
        "management_brief_outputs": {
            "markdown": str(ROOT_MD_BRIEF),
            "html": str(ROOT_HTML_BRIEF),
            "pdf": str(ROOT_PDF_BRIEF),
            "table_reading_cards": str(ROOT_TABLE_READING_CARDS),
            "chart_narrative_sections": str(ROOT_CHART_NARRATIVE_SECTIONS),
            "management_quadrant_index_json": str(ROOT_MANAGEMENT_QUADRANT_INDEX_JSON),
            "management_quadrant_index_csv": str(ROOT_MANAGEMENT_QUADRANT_INDEX_CSV),
            "derived_metric_diagnosis_cards": str(ROOT_DERIVED_METRIC_DIAGNOSIS_CARDS),
        },
        "full_table_outputs": (
            {
                "markdown": str(ROOT_MD_WITH_TABLES),
                "html": str(ROOT_HTML_WITH_TABLES),
                "pdf": str(ROOT_PDF_WITH_TABLES),
            }
            if generate_full_table_version
            else {}
        ),
    }
    (JOB_ROOT / "pdf_table_correlation_repair_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
