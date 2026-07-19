from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.services.codex_historical_style_cli_service import run_historical_style_cli_adaptation


def _chart_bundle() -> dict:
    return {
        "distribution": {
            "kind": "histogram",
            "title": "Gross margin distribution by category",
            "x": ["0-10%", "10-20%", "20-30%", "30-40%", "40-50%", "50%+"],
            "y": [8, 19, 34, 27, 16, 7],
        },
        "category": {
            "kind": "bar",
            "title": "Revenue mix by channel",
            "x": ["Marketplace", "Direct store", "Wholesale", "Social commerce", "Retail partner"],
            "y": [420, 310, 180, 145, 95],
        },
        "correlation": {
            "kind": "heatmap",
            "title": "Operating driver correlation map",
            "labels": ["revenue", "margin", "inventory_turns", "repeat_rate", "service_level"],
            "matrix": [
                [1.00, 0.58, 0.22, 0.46, 0.35],
                [0.58, 1.00, 0.41, 0.53, 0.48],
                [0.22, 0.41, 1.00, 0.37, 0.55],
                [0.46, 0.53, 0.37, 1.00, 0.62],
                [0.35, 0.48, 0.55, 0.62, 1.00],
            ],
        },
        "scatter": {
            "kind": "scatter",
            "title": "Price index vs repeat purchase rate",
            "x_label": "Price index",
            "y_label": "Repeat purchase rate",
            "points": [
                {"x": 88, "y": 0.41},
                {"x": 91, "y": 0.45},
                {"x": 96, "y": 0.48},
                {"x": 101, "y": 0.52},
                {"x": 106, "y": 0.50},
                {"x": 112, "y": 0.47},
                {"x": 118, "y": 0.43},
                {"x": 124, "y": 0.39},
                {"x": 129, "y": 0.34},
            ],
        },
    }


def _support_tables() -> dict:
    return {
        "kpi_snapshot": [
            {"metric": "net_revenue", "aggregation": "sum", "value": 1150.0},
            {"metric": "gross_margin", "aggregation": "mean", "value": 0.318},
            {"metric": "repeat_purchase_rate", "aggregation": "mean", "value": 0.472},
            {"metric": "inventory_turns", "aggregation": "mean", "value": 5.8},
            {"metric": "service_level", "aggregation": "mean", "value": 0.913},
        ],
        "ranking_tables": [
            {
                "dimension": "channel",
                "rows": [
                    {"channel": "Marketplace", "net_revenue": 420, "gross_margin": 0.29, "repeat_purchase_rate": 0.44, "row_count": 128},
                    {"channel": "Direct store", "net_revenue": 310, "gross_margin": 0.38, "repeat_purchase_rate": 0.56, "row_count": 84},
                    {"channel": "Wholesale", "net_revenue": 180, "gross_margin": 0.24, "repeat_purchase_rate": 0.37, "row_count": 51},
                    {"channel": "Social commerce", "net_revenue": 145, "gross_margin": 0.34, "repeat_purchase_rate": 0.49, "row_count": 47},
                ],
            },
            {
                "dimension": "category",
                "rows": [
                    {"category": "Core skincare", "net_revenue": 360, "gross_margin": 0.41, "repeat_purchase_rate": 0.58, "row_count": 72},
                    {"category": "Entry set", "net_revenue": 260, "gross_margin": 0.22, "repeat_purchase_rate": 0.36, "row_count": 96},
                    {"category": "Premium anti-aging", "net_revenue": 240, "gross_margin": 0.46, "repeat_purchase_rate": 0.51, "row_count": 43},
                    {"category": "Travel size", "net_revenue": 118, "gross_margin": 0.19, "repeat_purchase_rate": 0.28, "row_count": 68},
                ],
            },
            {
                "dimension": "region",
                "rows": [
                    {"region": "East", "net_revenue": 420, "gross_margin": 0.34, "service_level": 0.94, "row_count": 112},
                    {"region": "South", "net_revenue": 310, "gross_margin": 0.32, "service_level": 0.91, "row_count": 88},
                    {"region": "North", "net_revenue": 218, "gross_margin": 0.27, "service_level": 0.87, "row_count": 64},
                    {"region": "West", "net_revenue": 202, "gross_margin": 0.29, "service_level": 0.89, "row_count": 59},
                ],
            },
        ],
        "correlation_focus": [
            {"left": "repeat_rate", "right": "service_level", "correlation": 0.62, "abs_correlation": 0.62},
            {"left": "gross_margin", "right": "repeat_rate", "correlation": 0.53, "abs_correlation": 0.53},
            {"left": "inventory_turns", "right": "service_level", "correlation": 0.55, "abs_correlation": 0.55},
        ],
        "glossary_rows": [
            {"column": "channel", "dtype": "category", "missing_ratio": 0.0, "unique_count": 5, "top_values": "Marketplace / Direct store"},
            {"column": "category", "dtype": "category", "missing_ratio": 0.0, "unique_count": 6, "top_values": "Core skincare / Entry set"},
            {"column": "gross_margin", "dtype": "number", "missing_ratio": 0.0, "unique_count": 120, "top_values": ""},
            {"column": "repeat_purchase_rate", "dtype": "number", "missing_ratio": 0.0, "unique_count": 118, "top_values": ""},
        ],
    }


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    report_id = f"mckinsey-style-smoke-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    report_dir = repo / "workspace" / "storage" / "reports" / report_id
    report_dir.mkdir(parents=True, exist_ok=True)
    historical_seed = """
# McKinsey public report style seed

Source family: McKinsey & Company public strategy / consumer demand report.
Reference URL: https://www.mckinsey.com/industries/consumer-packaged-goods/our-insights/the-consumer-demand-recovery-and-lasting-effects-of-covid-19

Reusable style only:
- Strategy-consulting report posture: answer-first titles, pyramid logic, management implications, and recommendation cadence.
- Page system: title page, executive summary, section dividers, exhibit-heavy body pages, boxed implications, callout statistics, and appendix/detail pages.
- Visual language: clean white background, black/gray text, restrained blue accents, sparse page furniture, exhibit numbers, chart captions, and source footers.
- Data expression: one main message per page; charts and matrices are exhibits, not decoration; every exhibit should support a management implication.
- Story rhythm: context -> demand signal -> operating issue tree -> segment/channel economics -> implications -> actions.
- Do not copy historical facts, numbers, brand marks, or old conclusions.
""".strip()
    result = run_historical_style_cli_adaptation(
        report_dir=report_dir,
        report_id=report_id,
        dataset_name="CPG operating model sample",
        sheet_name="business_metrics",
        historical_report_name="McKinsey public consumer demand report",
        historical_report_text=historical_seed,
        historical_report_source_path="",
        executive_summary=[
            "Growth is concentrated in direct and marketplace channels, but margin quality differs sharply.",
            "Repeat purchase and service level form the strongest operating relationship in the current sample.",
            "The management agenda should separate scale candidates from margin repair and service reliability zones.",
        ],
        section_summaries=[
            {"title": "Channel economics", "summary": "Direct store has lower revenue share but higher margin and repeat quality.", "bullets": ["Marketplace scales volume", "Direct store protects margin"]},
            {"title": "Category portfolio", "summary": "Premium and core categories carry stronger economics than entry and travel-size products.", "bullets": ["Core skincare is a scale anchor", "Entry set requires margin repair"]},
            {"title": "Operating reliability", "summary": "Service level links with repeat behavior and should become a front-line operating KPI.", "bullets": ["Service level is a repeat-rate lever", "Regional reliability gaps remain visible"]},
        ],
        market_summary=[
            "Consumer demand is recovering unevenly across channels and categories.",
            "Management needs a consulting-style issue tree that translates metrics into actions.",
        ],
        semantic_summary=[
            "Fields represent channel, region, category, revenue, margin, repeat behavior, inventory turns, and service level.",
        ],
        user_requirement=(
            "模仿麦肯锡公开报告的咨询 deck 风格，用中文输出；要有 answer-first 标题、issue tree、exhibit 页、"
            "渠道/品类/区域经营建议、动作路线图、附录明细，视觉克制高级，图表和表格要多。"
        ),
        target_audience="CEO / strategy and operations leadership",
        core_purpose="strategy_consulting_operating_diagnosis",
        business_background_text="A consumer goods company needs a management-grade operating diagnosis across channels, categories, regions, margin, repeat purchase, inventory turns, and service reliability.",
        chart_bundle=_chart_bundle(),
        column_summaries=[
            {"name": "channel", "dtype": "category", "unique_count": 5},
            {"name": "category", "dtype": "category", "unique_count": 6},
            {"name": "region", "dtype": "category", "unique_count": 4},
            {"name": "net_revenue", "dtype": "number", "unique_count": 140},
            {"name": "gross_margin", "dtype": "number", "unique_count": 120},
            {"name": "repeat_purchase_rate", "dtype": "number", "unique_count": 118},
            {"name": "inventory_turns", "dtype": "number", "unique_count": 88},
            {"name": "service_level", "dtype": "number", "unique_count": 92},
        ],
        support_tables=_support_tables(),
        target_page_count_min=28,
        target_page_count_max=40,
        language="zh-CN",
    )
    output = {
        "report_id": report_id,
        "report_dir": str(report_dir.resolve()),
        "pipeline_job_id": result.get("pipeline_job_id"),
        "pipeline_status": result.get("pipeline_status"),
        "reason": result.get("reason"),
        "final_output": result.get("pipeline_final_output"),
    }
    summary_path = report_dir / "mckinsey_style_smoke_result.json"
    summary_path.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
