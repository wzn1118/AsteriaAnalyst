from __future__ import annotations

import json
import os
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from app.services.codex_historical_style_cli_service import run_historical_style_cli_adaptation


BCG_Q1_URL = "https://www.bcg.com/assets/2024/china-consumer-quarterly-watch-q1.pdf"
FALLBACK_DELOITTE_URL = (
    "https://www.deloitte.com/content/dam/assets-zone3/us/en/docs/industries/"
    "consumer/2024/us-consumer-business-retail-outlook-2024.pdf"
)


def _download_pdf(url: str, output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    }
    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=45) as response:
            content_type = str(response.headers.get("Content-Type") or "")
            data = response.read()
        output_path.write_bytes(data)
        return {
            "ok": output_path.exists() and output_path.stat().st_size > 10000,
            "method": "urllib",
            "url": url,
            "path": str(output_path.resolve()),
            "content_type": content_type,
            "bytes": output_path.stat().st_size if output_path.exists() else 0,
            "error": "",
        }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        curl = "curl.exe" if os.name == "nt" else "curl"
        try:
            subprocess.run(
                [
                    curl,
                    "-L",
                    "--fail",
                    "-A",
                    headers["User-Agent"],
                    "-H",
                    f"Accept: {headers['Accept']}",
                    "-H",
                    f"Accept-Language: {headers['Accept-Language']}",
                    "-o",
                    str(output_path),
                    url,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "ok": output_path.exists() and output_path.stat().st_size > 10000,
                "method": "curl",
                "url": url,
                "path": str(output_path.resolve()),
                "content_type": "",
                "bytes": output_path.stat().st_size if output_path.exists() else 0,
                "error": "",
            }
        except Exception as curl_exc:
            return {
                "ok": False,
                "method": "urllib_then_curl",
                "url": url,
                "path": str(output_path.resolve()),
                "content_type": "",
                "bytes": output_path.stat().st_size if output_path.exists() else 0,
                "error": f"{type(exc).__name__}: {exc}; curl: {type(curl_exc).__name__}: {curl_exc}",
            }


def _resolve_real_pdf(repo: Path, source_dir: Path) -> tuple[Path, dict[str, Any]]:
    env_path = os.environ.get("BCG_HISTORICAL_PDF_PATH") or os.environ.get("HISTORICAL_STYLE_PDF_PATH")
    if env_path:
        path = Path(env_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Configured historical PDF does not exist: {path}")
        return path, {
            "ok": True,
            "source": "env_path",
            "url": "",
            "path": str(path),
            "bytes": path.stat().st_size,
            "error": "",
        }

    bcg_path = source_dir / "bcg_china_consumer_quarterly_watch_q1_2024.pdf"
    bcg_result = _download_pdf(BCG_Q1_URL, bcg_path)
    if bcg_result.get("ok"):
        return bcg_path, {"source": "bcg_primary", **bcg_result}

    fallback_allowed = os.environ.get("ALLOW_REAL_PDF_FALLBACK", "1").strip() != "0"
    if not fallback_allowed:
        raise RuntimeError(f"BCG PDF download failed and fallback is disabled: {bcg_result.get('error')}")

    fallback_path = source_dir / "deloitte_2024_us_retail_industry_outlook.pdf"
    fallback_result = _download_pdf(FALLBACK_DELOITTE_URL, fallback_path)
    if fallback_result.get("ok"):
        return fallback_path, {
            "source": "deloitte_public_pdf_fallback",
            "primary_bcg_error": bcg_result.get("error"),
            **fallback_result,
        }
    raise RuntimeError(
        "No real PDF could be downloaded. "
        f"BCG error: {bcg_result.get('error')}; fallback error: {fallback_result.get('error')}"
    )


def _chart_bundle() -> dict[str, Any]:
    return {
        "category": {
            "kind": "bar",
            "title": "Member sales contribution by retail format",
            "x": ["Flagship", "Community", "Outlet", "Livestream", "Marketplace"],
            "y": [385, 246, 178, 152, 119],
        },
        "distribution": {
            "kind": "histogram",
            "title": "Basket value distribution",
            "x": ["<100", "100-199", "200-299", "300-499", "500+"],
            "y": [18, 32, 27, 16, 7],
        },
        "correlation": {
            "kind": "heatmap",
            "title": "Consumer operating driver correlation",
            "labels": ["traffic", "conversion", "basket", "repeat", "service"],
            "matrix": [
                [1.00, 0.44, 0.28, 0.22, 0.19],
                [0.44, 1.00, 0.51, 0.47, 0.38],
                [0.28, 0.51, 1.00, 0.40, 0.31],
                [0.22, 0.47, 0.40, 1.00, 0.58],
                [0.19, 0.38, 0.31, 0.58, 1.00],
            ],
        },
        "scatter": {
            "kind": "scatter",
            "title": "Discount depth vs repeat purchase",
            "x_label": "Discount depth",
            "y_label": "Repeat purchase rate",
            "points": [
                {"x": 5, "y": 0.36},
                {"x": 9, "y": 0.39},
                {"x": 12, "y": 0.43},
                {"x": 16, "y": 0.48},
                {"x": 19, "y": 0.46},
                {"x": 24, "y": 0.41},
                {"x": 29, "y": 0.37},
            ],
        },
    }


def _support_tables() -> dict[str, Any]:
    return {
        "kpi_snapshot": [
            {"metric": "gross_sales", "aggregation": "sum", "value": 1080.0},
            {"metric": "member_repeat_rate", "aggregation": "mean", "value": 0.438},
            {"metric": "gross_margin", "aggregation": "mean", "value": 0.312},
            {"metric": "service_satisfaction", "aggregation": "mean", "value": 0.884},
        ],
        "ranking_tables": [
            {
                "dimension": "retail_format",
                "rows": [
                    {"retail_format": "Flagship", "gross_sales": 385, "gross_margin": 0.35, "repeat_rate": 0.49},
                    {"retail_format": "Community", "gross_sales": 246, "gross_margin": 0.29, "repeat_rate": 0.44},
                    {"retail_format": "Outlet", "gross_sales": 178, "gross_margin": 0.22, "repeat_rate": 0.34},
                    {"retail_format": "Livestream", "gross_sales": 152, "gross_margin": 0.27, "repeat_rate": 0.39},
                ],
            },
            {
                "dimension": "consumer_segment",
                "rows": [
                    {"consumer_segment": "Value seekers", "gross_sales": 288, "gross_margin": 0.21, "repeat_rate": 0.35},
                    {"consumer_segment": "Quality upgraders", "gross_sales": 318, "gross_margin": 0.39, "repeat_rate": 0.51},
                    {"consumer_segment": "Convenience driven", "gross_sales": 226, "gross_margin": 0.31, "repeat_rate": 0.46},
                    {"consumer_segment": "Promotion sensitive", "gross_sales": 248, "gross_margin": 0.24, "repeat_rate": 0.38},
                ],
            },
        ],
        "correlation_focus": [
            {"left": "service_satisfaction", "right": "repeat_rate", "correlation": 0.58, "abs_correlation": 0.58},
            {"left": "conversion_rate", "right": "basket_value", "correlation": 0.51, "abs_correlation": 0.51},
            {"left": "discount_depth", "right": "gross_margin", "correlation": -0.46, "abs_correlation": 0.46},
        ],
        "glossary_rows": [
            {"column": "retail_format", "dtype": "category", "missing_ratio": 0.0, "unique_count": 5},
            {"column": "consumer_segment", "dtype": "category", "missing_ratio": 0.0, "unique_count": 4},
            {"column": "gross_sales", "dtype": "number", "missing_ratio": 0.0, "unique_count": 130},
            {"column": "member_repeat_rate", "dtype": "number", "missing_ratio": 0.0, "unique_count": 112},
        ],
    }


def _data_frame() -> Any:
    random.seed(20260502)
    formats = ["Flagship", "Community", "Outlet", "Livestream", "Marketplace"]
    segments = ["Value seekers", "Quality upgraders", "Convenience driven", "Promotion sensitive", "New families"]
    regions = ["East", "South", "North", "West", "Central"]
    months = pd.date_range("2024-01-01", periods=6, freq="MS")
    rows: list[dict[str, Any]] = []
    for month in months:
        for retail_format in formats:
            for segment in segments:
                for region in regions:
                    format_index = formats.index(retail_format)
                    segment_index = segments.index(segment)
                    region_index = regions.index(region)
                    traffic = 1800 + format_index * 220 + region_index * 95 + random.randint(-120, 160)
                    conversion_rate = max(0.035, min(0.32, 0.08 + segment_index * 0.016 + format_index * 0.006 + random.uniform(-0.018, 0.018)))
                    basket_value = 120 + segment_index * 18 + format_index * 9 + random.uniform(-12, 18)
                    orders = max(30, int(traffic * conversion_rate))
                    gross_sales = orders * basket_value
                    discount_depth = max(0.02, min(0.42, 0.08 + (4 - segment_index) * 0.018 + format_index * 0.012 + random.uniform(-0.025, 0.025)))
                    gross_margin = max(0.12, min(0.52, 0.35 - discount_depth * 0.42 + segment_index * 0.018 + random.uniform(-0.025, 0.025)))
                    repeat_rate = max(0.12, min(0.72, 0.28 + conversion_rate * 0.9 + gross_margin * 0.18 + random.uniform(-0.04, 0.04)))
                    service_satisfaction = max(0.55, min(0.97, 0.74 + repeat_rate * 0.18 - discount_depth * 0.08 + random.uniform(-0.035, 0.035)))
                    rows.append(
                        {
                            "month": month,
                            "retail_format": retail_format,
                            "consumer_segment": segment,
                            "region": region,
                            "traffic": traffic,
                            "orders": orders,
                            "gross_sales": round(gross_sales, 2),
                            "gross_margin": round(gross_margin, 4),
                            "conversion_rate": round(conversion_rate, 4),
                            "member_repeat_rate": round(repeat_rate, 4),
                            "basket_value": round(basket_value, 2),
                            "discount_depth": round(discount_depth, 4),
                            "service_satisfaction": round(service_satisfaction, 4),
                        }
                    )
    return pd.DataFrame(rows)


def _artifact_status(final_output: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "reverse_spec_json_path": "01_historical_reverse_spec.json",
        "data_asset_manifest_path": "historical_data_asset_manifest.json",
        "data_storyline_scan_path": "02_data_storyline_scan.json",
        "data_profile_path": "historical_data_profile.json",
        "page_plan_json_path": "02_historical_page_plan.json",
        "chart_assets_index_path": "historical_chart_assets_index.json",
        "table_assets_index_path": "historical_table_assets_index.json",
        "collage_assets_index_path": "historical_collage_assets_index.json",
        "html_artifact_path": "06_historical_style_report.html",
        "css_artifact_path": "06_historical_style_report.css",
        "pdf_artifact_path": "07_historical_style_report.pdf",
    }
    status: dict[str, Any] = {}
    for key, expected_name in expected.items():
        path = Path(str(final_output.get(key) or ""))
        status[expected_name] = {
            "path": str(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
        }
    return status


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    report_id = f"bcg-real-pdf-style-smoke-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    report_dir = repo / "workspace" / "storage" / "reports" / report_id
    source_dir = repo / "workspace" / "tmp" / "historical_sources"
    report_dir.mkdir(parents=True, exist_ok=True)

    historical_pdf_path, source_status = _resolve_real_pdf(repo, source_dir)
    source_label = str(source_status.get("source") or "real_pdf")
    historical_name = (
        "BCG China Consumer Market Quarterly Watch Q1 2024"
        if source_label == "bcg_primary"
        else "Deloitte 2024 US Retail Industry Outlook"
    )
    data_frame = _data_frame()

    result = run_historical_style_cli_adaptation(
        report_dir=report_dir,
        report_id=report_id,
        dataset_name="Consumer retail operations real-PDF smoke dataset",
        sheet_name="retail_consumer_metrics",
        historical_report_name=historical_name,
        historical_report_text="",
        historical_report_source_path=str(historical_pdf_path),
        executive_summary=[
            "The current dataset shows a split between sales scale and repeat-quality economics.",
            "Service satisfaction and repeat purchase form the strongest operating relationship.",
            "Management should separate growth formats, loyalty repair zones, and margin-risk formats.",
        ],
        section_summaries=[
            {
                "title": "Retail format economics",
                "summary": "Flagship and community formats carry different combinations of scale, margin, and loyalty.",
                "bullets": ["Flagship anchors scale", "Community needs loyalty playbooks", "Outlet needs margin guardrails"],
            },
            {
                "title": "Consumer segment diagnosis",
                "summary": "Quality upgraders show better margin and repeat behavior than promotion-sensitive segments.",
                "bullets": ["Upgrade segment deserves retention investment", "Promotion-sensitive volume should be capped"],
            },
            {
                "title": "Operating levers",
                "summary": "Service satisfaction, discount depth, and conversion quality should become the main action grid.",
                "bullets": ["Service drives repeat", "Discount depth pressures margin", "Conversion links with basket value"],
            },
        ],
        market_summary=[
            "The test context is a consumer retail management report, not a reuse of the historical PDF facts.",
            "The historical PDF is used only for deck grammar, exhibit rhythm, and page system imitation.",
        ],
        semantic_summary=[
            "Fields cover retail format, consumer segment, sales, margin, repeat purchase, basket value, discount depth, conversion, and service satisfaction.",
        ],
        user_requirement=(
            "Use the real historical PDF only as a style and page-system reference. "
            "Do not copy historical facts or numbers. Generate a Chinese management deck with exhibit-heavy pages, "
            "answer-first page titles, clear source/footer rhythm, and concrete current-period actions."
        ),
        target_audience="CEO / retail operations leadership / consumer strategy team",
        core_purpose="real_pdf_historical_style_validation",
        business_background_text=(
            "A consumer retail operator needs a management-grade diagnosis of sales quality, loyalty, margin, "
            "discount discipline, and format-level growth priorities."
        ),
        chart_bundle=_chart_bundle(),
        column_summaries=[
            {"name": "retail_format", "dtype": "category", "unique_count": 5},
            {"name": "consumer_segment", "dtype": "category", "unique_count": 4},
            {"name": "gross_sales", "dtype": "number", "unique_count": 130},
            {"name": "gross_margin", "dtype": "number", "unique_count": 104},
            {"name": "member_repeat_rate", "dtype": "number", "unique_count": 112},
            {"name": "basket_value", "dtype": "number", "unique_count": 96},
            {"name": "discount_depth", "dtype": "number", "unique_count": 70},
            {"name": "service_satisfaction", "dtype": "number", "unique_count": 91},
        ],
        support_tables=_support_tables(),
        data_frame=data_frame,
        target_page_count_min=10,
        target_page_count_max=18,
        language="zh-CN",
    )
    final_output = dict(result.get("pipeline_final_output") or {})
    output = {
        "report_id": report_id,
        "report_dir": str(report_dir.resolve()),
        "historical_pdf_path": str(historical_pdf_path.resolve()),
        "historical_source_status": source_status,
        "pipeline_job_id": result.get("pipeline_job_id"),
        "pipeline_status": result.get("pipeline_status"),
        "reason": result.get("reason"),
        "final_output": final_output,
        "artifact_status": _artifact_status(final_output),
    }
    summary_path = report_dir / "bcg_real_pdf_style_smoke_result.json"
    summary_path.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
