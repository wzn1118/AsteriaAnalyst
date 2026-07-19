from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.codex_historical_style_cli_service import run_historical_style_cli_adaptation  # noqa: E402


CASE_CONFIGS: dict[str, dict[str, Any]] = {
    "bcg": {
        "name": "BCG China Consumer Market Quarterly Watch Q1 2024",
        "url": "https://www.bcg.com/assets/2024/china-consumer-quarterly-watch-q1.pdf",
        "env": "BCG_HISTORICAL_PDF_PATH",
        "min_pages": 5,
        "max_pages": 16,
    },
    "mckinsey": {
        "name": "McKinsey public consulting PDF",
        "url": "",
        "env": "MCKINSEY_HISTORICAL_PDF_PATH",
        "min_pages": 8,
        "max_pages": 60,
    },
    "yili": {
        "name": "Yili historical brand analysis PDF",
        "url": "",
        "env": "YILI_HISTORICAL_PDF_PATH",
        "min_pages": 24,
        "max_pages": 60,
    },
    "custom": {
        "name": "Custom real historical PDF",
        "url": "",
        "env": "HISTORICAL_STYLE_PDF_PATH",
        "min_pages": 4,
        "max_pages": 80,
    },
}


def _download_pdf(url: str, output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 historical-style-regression/1.0",
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
    }
    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=60) as response:
            data = response.read()
            content_type = str(response.headers.get("Content-Type") or "")
        output_path.write_bytes(data)
        ok = output_path.exists() and output_path.stat().st_size > 10000
        return {
            "ok": ok,
            "url": url,
            "path": str(output_path.resolve()),
            "content_type": content_type,
            "bytes": output_path.stat().st_size if output_path.exists() else 0,
            "error": "" if ok else "downloaded file is too small",
        }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "url": url,
            "path": str(output_path.resolve()),
            "content_type": "",
            "bytes": output_path.stat().st_size if output_path.exists() else 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _resolve_pdf(case: str, *, pdf_path: str, url: str, offline: bool, source_dir: Path) -> tuple[Path, dict[str, Any]]:
    config = CASE_CONFIGS[case]
    explicit = pdf_path or os.environ.get(str(config.get("env") or "")) or os.environ.get("HISTORICAL_STYLE_PDF_PATH", "")
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Historical PDF path does not exist: {path}")
        return path, {"source": "local_path", "path": str(path), "bytes": path.stat().st_size, "ok": True, "error": ""}
    download_url = url or str(config.get("url") or "")
    if offline or not download_url:
        raise FileNotFoundError(
            f"No local PDF configured for case `{case}`. Pass --pdf-path or set {config.get('env')}."
        )
    target = source_dir / f"{case}_historical_source.pdf"
    result = _download_pdf(download_url, target)
    if not result.get("ok"):
        raise RuntimeError(f"Could not download real PDF for `{case}`: {result.get('error')}")
    return target, {"source": "download", **result}


def _rich_consumer_ops_frame(seed: int = 20260502, rows_count: int = 480) -> pd.DataFrame:
    random.seed(seed)
    regions = ["East", "South", "North", "West"]
    channels = ["Marketplace", "Direct store", "Wholesale", "Social commerce", "Retail partner"]
    categories = ["Core skincare", "Entry set", "Premium anti-aging", "Travel size", "Body care", "Seasonal bundle"]
    segments = ["Value seekers", "Quality upgraders", "Convenience driven", "Promotion sensitive"]
    start = date(2026, 1, 1)
    rows: list[dict[str, Any]] = []
    for index in range(rows_count):
        region = regions[index % len(regions)]
        channel = channels[(index // 2) % len(channels)]
        category = categories[(index // 3) % len(categories)]
        segment = segments[(index // 5) % len(segments)]
        base = 90 + regions.index(region) * 9 + channels.index(channel) * 8 + categories.index(category) * 4
        seasonality = 1 + 0.16 * math.sin(index / 23)
        order_count = int((base + random.randint(-18, 28)) * seasonality)
        basket_value = 58 + categories.index(category) * 7 + channels.index(channel) * 3 + random.random() * 12
        gross_sales = order_count * basket_value
        discount_depth = 0.04 + channels.index(channel) * 0.012 + random.random() * 0.08
        gross_margin = 0.25 + categories.index(category) * 0.021 - discount_depth * 0.16 + random.random() * 0.035
        rows.append(
            {
                "date": start + timedelta(days=index % 120),
                "region": region,
                "channel": channel,
                "category": category,
                "consumer_segment": segment,
                "gross_sales": round(gross_sales, 2),
                "order_count": order_count,
                "basket_value": round(basket_value, 2),
                "gross_margin": round(gross_margin, 4),
                "conversion_rate": round(0.032 + channels.index(channel) * 0.006 + random.random() * 0.02, 4),
                "repeat_purchase_rate": round(0.18 + segments.index(segment) * 0.055 + random.random() * 0.05, 4),
                "service_satisfaction": round(3.55 + segments.index(segment) * 0.14 + random.random() * 0.55, 2),
                "inventory_turns": round(4.8 + categories.index(category) * 0.42 + random.random() * 1.6, 2),
                "discount_depth": round(discount_depth, 4),
                "refund_rate": round(0.012 + categories.index(category) * 0.004 + random.random() * 0.012, 4),
                "traffic_index": round(80 + channels.index(channel) * 8 + random.random() * 35, 2),
            }
        )
    return pd.DataFrame(rows)


def _column_summaries(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "name": str(column),
            "dtype": str(frame[column].dtype),
            "missing_ratio": float(frame[column].isna().mean()),
            "unique_count": int(frame[column].nunique(dropna=True)),
        }
        for column in frame.columns
    ]


def _case_requirement(case: str) -> str:
    if case == "mckinsey":
        return (
            "Use a real strategy-consulting deck rhythm: answer-first page titles, issue-tree logic, exhibit pages, "
            "source/footer rhythm, concise executive recommendations, and action roadmap. Reader-facing text must be Chinese."
        )
    if case == "yili":
        return (
            "Replicate a long Chinese brand-analysis deck structure with module divider pages, dense chart/table pages, "
            "summary maps, and appendix detail pages. Reader-facing text must be Chinese."
        )
    if case == "bcg":
        return (
            "Replicate a compact consulting quarterly-watch PDF rhythm: white exhibit pages, short management headlines, "
            "source/footer rhythm, and high data density. Reader-facing text must be Chinese."
        )
    return (
        "Reverse the real historical PDF into a reusable deck system, then generate a current-data Chinese business report "
        "with strong visuals, tables, and action recommendations."
    )


def _run_case(case: str, *, pdf_path: Path, report_root: Path, source_info: dict[str, Any]) -> dict[str, Any]:
    frame = _rich_consumer_ops_frame(seed=20260502 + len(case))
    report_id = f"historical-real-pdf-{case}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    report_dir = report_root / report_id
    report_dir.mkdir(parents=True, exist_ok=True)
    result = run_historical_style_cli_adaptation(
        report_dir=report_dir,
        report_id=report_id,
        dataset_name=f"{case} regression consumer operations",
        sheet_name="business_metrics",
        historical_report_name=str(CASE_CONFIGS[case]["name"]),
        historical_report_text="",
        historical_report_source_path=str(pdf_path),
        executive_summary=[
            "The current dataset contains channel, region, category, segment, sales, margin, repeat, service, inventory, discount, refund, and traffic signals.",
            "The regression should prove that a real historical PDF can control page system and visual rhythm while current data controls findings.",
        ],
        section_summaries=[
            {"title": "Growth structure", "summary": "Compare channels, regions, and categories by gross sales, orders, and traffic.", "bullets": ["Scale concentration", "Traffic conversion"]},
            {"title": "Economics and retention", "summary": "Diagnose margin, discount, repeat purchase, service satisfaction, and refund risk.", "bullets": ["Margin pressure", "Retention signal"]},
            {"title": "Management actions", "summary": "Translate top/bottom segments and relationships into operating actions.", "bullets": ["Prioritize growth cells", "Repair weak economics"]},
        ],
        market_summary=[
            "Consumer demand is uneven across channels and segments.",
            "Management needs a deck that connects signals to decisions rather than a generic narrative.",
        ],
        semantic_summary=[
            "Fields cover operating scale, conversion, retention, profitability, service, inventory, pricing, and risk.",
        ],
        user_requirement=_case_requirement(case),
        target_audience="CEO / strategy / operations leadership",
        core_purpose="real_pdf_historical_style_regression",
        business_background_text=(
            "This smoke case validates historical-style runtime CLI using a real PDF as style source and a rich consumer operations dataset as current evidence."
        ),
        chart_bundle={},
        column_summaries=_column_summaries(frame),
        support_tables={},
        data_frame=frame,
        target_page_count_min=int(CASE_CONFIGS[case].get("min_pages") or 8),
        target_page_count_max=int(CASE_CONFIGS[case].get("max_pages") or 40),
        language="zh-CN",
    )
    final_output = dict(result.get("pipeline_final_output") or {})
    blocking_issues = list(final_output.get("quality_blocking_issues") or [])
    pass_gate = (
        str(result.get("pipeline_status") or "") == "completed"
        and float(final_output.get("overall_style_score") or 0) >= 0.75
        and float(final_output.get("data_coverage_score") or 0) >= 0.7
        and float(final_output.get("language_quality_score") or 0) >= 0.9
        and not blocking_issues
    )
    return {
        "case": case,
        "report_id": report_id,
        "report_dir": str(report_dir.resolve()),
        "source_info": source_info,
        "pipeline_job_id": result.get("pipeline_job_id"),
        "pipeline_status": result.get("pipeline_status"),
        "reason": result.get("reason"),
        "passed": pass_gate,
        "overall_style_score": final_output.get("overall_style_score"),
        "page_type_coverage_score": final_output.get("page_type_coverage_score"),
        "visual_density_score": final_output.get("visual_density_score"),
        "data_coverage_score": final_output.get("data_coverage_score"),
        "language_quality_score": final_output.get("language_quality_score"),
        "family_match": final_output.get("family_match"),
        "blocking_issues": blocking_issues,
        "rendered_page_count": final_output.get("rendered_page_count"),
        "planned_page_count": final_output.get("planned_page_count"),
        "historical_report_family": final_output.get("historical_report_family"),
        "final_output": final_output,
    }


def _write_markdown_summary(results: list[dict[str, Any]], output_path: Path) -> None:
    lines = [
        "# Historical Real PDF Regression",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Cases: `{len(results)}`",
        f"- Passed: `{sum(1 for item in results if item.get('passed'))}`",
        "",
        "| Case | Passed | Family | Overall | Data | Language | Pages | Blocking issues |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in results:
        lines.append(
            "| {case} | {passed} | {family} | {overall} | {data} | {language} | {pages} | {issues} |".format(
                case=item.get("case"),
                passed="yes" if item.get("passed") else "no",
                family=item.get("historical_report_family") or "",
                overall=item.get("overall_style_score") or "",
                data=item.get("data_coverage_score") or "",
                language=item.get("language_quality_score") or "",
                pages=item.get("rendered_page_count") or "",
                issues=", ".join(item.get("blocking_issues") or []),
            )
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run historical-style CLI regression against real PDF samples.")
    parser.add_argument("--case", choices=["bcg", "mckinsey", "yili", "custom", "all"], default="bcg")
    parser.add_argument("--pdf-path", default="", help="Local PDF path. Required for custom/offline cases unless env var is set.")
    parser.add_argument("--url", default="", help="Override source PDF URL for the selected case.")
    parser.add_argument("--offline", action="store_true", help="Do not download; require --pdf-path or env var.")
    parser.add_argument("--output-root", default=str(PROJECT_ROOT / "workspace" / "storage" / "reports"))
    args = parser.parse_args()

    source_dir = PROJECT_ROOT / "workspace" / "tmp" / "historical_real_pdf_sources"
    report_root = Path(args.output_root).expanduser().resolve()
    report_root.mkdir(parents=True, exist_ok=True)

    cases = ["bcg", "mckinsey", "yili"] if args.case == "all" else [args.case]
    results: list[dict[str, Any]] = []
    for case in cases:
        try:
            path, source_info = _resolve_pdf(
                case,
                pdf_path=args.pdf_path if len(cases) == 1 else "",
                url=args.url if len(cases) == 1 else "",
                offline=bool(args.offline),
                source_dir=source_dir,
            )
            results.append(_run_case(case, pdf_path=path, report_root=report_root, source_info=source_info))
        except Exception as exc:
            results.append(
                {
                    "case": case,
                    "report_id": "",
                    "report_dir": "",
                    "source_info": {},
                    "pipeline_job_id": "",
                    "pipeline_status": "failed",
                    "reason": f"{type(exc).__name__}: {exc}",
                    "passed": False,
                    "overall_style_score": 0,
                    "page_type_coverage_score": 0,
                    "visual_density_score": 0,
                    "data_coverage_score": 0,
                    "language_quality_score": 0,
                    "family_match": "",
                    "blocking_issues": [f"case_failed: {type(exc).__name__}: {exc}"],
                    "rendered_page_count": 0,
                    "planned_page_count": 0,
                    "historical_report_family": "",
                    "final_output": {},
                }
            )

    run_id = f"historical-real-pdf-regression-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    output_dir = PROJECT_ROOT / "workspace" / "tmp" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "result_count": len(results),
        "passed_count": sum(1 for item in results if item.get("passed")),
        "results": results,
    }
    summary_path = output_dir / "regression_summary.json"
    report_path = output_dir / "regression_summary.md"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_markdown_summary(results, report_path)
    print(json.dumps({"summary_path": str(summary_path.resolve()), "report_path": str(report_path.resolve()), **summary}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
