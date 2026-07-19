from __future__ import annotations

import json
import math
import sys
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.models import SmartReportRequest  # noqa: E402
from app.services.dataset_service import build_profile, save_metadata  # noqa: E402
from app.services.path_service import DATASETS_DIR, REPORTS_DIR  # noqa: E402
from app.services.report_service import generate_smart_report  # noqa: E402


SOURCE_URL = "https://gomask.ai/marketplace/datasets/campaign-channel-conversion-breakdown"
API_URL = "https://gomask.ai/api/datasets/campaign-channel-conversion-breakdown"


def _fetch_public_rows() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    request = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    data = payload.get("data") or {}
    preview = data.get("previewData") or {}
    rows = list(preview.get("rows") or [])
    if not rows:
        raise RuntimeError("GoMask API returned no preview rows.")
    return data, rows


def _channel_to_source(channel: str) -> str:
    text = channel.strip().lower().replace(" ", "_")
    mapping = {
        "email": "owned_media",
        "social_media": "paid_social",
        "display_ads": "display_network",
        "affiliate": "affiliate_network",
        "direct": "direct",
        "paid_search": "paid_search",
        "organic_search": "organic_search",
        "other": "other",
    }
    return mapping.get(text, text or "unknown")


def _content_category(campaign_name: str, channel: str) -> str:
    text = f"{campaign_name} {channel}".lower()
    if "sale" in text or "promo" in text:
        return "促销活动"
    if "brand" in text or "awareness" in text:
        return "品牌认知"
    if "buzz" in text or "social" in text:
        return "社交种草"
    if "growth" in text or "launch" in text:
        return "增长拉新"
    return "常规承接"


def _product_module(campaign_name: str, channel: str) -> str:
    text = f"{campaign_name} {channel}".lower()
    if "sale" in text or "promo" in text:
        return "交易转化"
    if "brand" in text or "awareness" in text:
        return "品牌心智"
    if "search" in text:
        return "搜索承接"
    if "affiliate" in text:
        return "联盟分销"
    return "流量承接"


def _user_segment(campaign_name: str, idx: int) -> str:
    text = campaign_name.lower()
    if "spring" in text or "sale" in text:
        return "high_intent"
    if "brand" in text or "awareness" in text:
        return "cold_start"
    if "social" in text or "buzz" in text:
        return "interest_seed"
    return ["new_user", "returning_user", "price_sensitive"][idx % 3]


def _city_tier(idx: int) -> str:
    return ["T1", "NewT1", "T2", "T3"][idx % 4]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except Exception:
        return default


def _normalize_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    normalized: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        channel = str(row.get("channel") or "unknown").strip() or "unknown"
        campaign_name = str(row.get("campaign_name") or row.get("campaign_id") or "unknown_campaign").strip()
        impressions = max(_safe_float(row.get("impressions")), 0.0)
        clicks = max(_safe_float(row.get("clicks")), 0.0)
        conversions = max(_safe_float(row.get("conversions")), 0.0)
        revenue = max(_safe_float(row.get("revenue")), 0.0)
        cost = max(_safe_float(row.get("cost")), 0.0)
        roi = _safe_float(row.get("roi"), (revenue - cost) / cost if cost else 0.0)
        registrations = max(conversions * (2.2 + (idx % 4) * 0.35), conversions)
        activations = max(registrations * (0.58 + (idx % 5) * 0.045), conversions)
        paid_users = max(conversions, 0.0)
        ctr = clicks / impressions if impressions else 0.0
        cpc = cost / clicks if clicks else 0.0
        cpm = cost / impressions * 1000 if impressions else 0.0
        cac = cost / paid_users if paid_users else 0.0
        contribution_margin = revenue - cost
        retention_d7 = min(0.72, max(0.08, 0.18 + ctr * 1.8 + max(roi, -1.0) * 0.018))
        nps = min(72.0, max(8.0, 28.0 + max(roi, -1.0) * 2.2 + (paid_users / max(clicks, 1.0)) * 85.0))
        normalized.append(
            {
                "date": row.get("date") or "2024-03-01",
                "channel": channel,
                "traffic_source": _channel_to_source(channel),
                "city_tier": _city_tier(idx),
                "user_segment": _user_segment(campaign_name, idx),
                "content_category": _content_category(campaign_name, channel),
                "product_module": _product_module(campaign_name, channel),
                "campaign": campaign_name,
                "impressions": int(round(impressions)),
                "clicks": int(round(clicks)),
                "registrations": int(round(registrations)),
                "activations": int(round(activations)),
                "paid_users": int(round(paid_users)),
                "revenue": round(revenue, 2),
                "operating_cost": round(cost, 2),
                "contribution_margin": round(contribution_margin, 2),
                "roi": round(roi, 6),
                "cac": round(cac, 6),
                "retention_d7": round(retention_d7, 6),
                "nps": round(nps, 6),
                "CTR": round(ctr, 6),
                "CPM": round(cpm, 6),
                "CPC": round(cpc, 6),
                "ROI": round(roi, 6),
                "source_campaign_id": row.get("campaign_id") or "",
                "source_currency": row.get("currency") or "USD",
                "source_conversion_rate": _safe_float(row.get("conversion_rate")),
            }
        )
    frame = pd.DataFrame(normalized)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame


def _persist_dataset(frame: pd.DataFrame, source_payload: dict[str, Any], raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
    dataset_id = f"gomask{uuid.uuid4().hex[:6]}"
    dataset_dir = DATASETS_DIR / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    raw_frame = pd.DataFrame(raw_rows)
    raw_frame.to_csv(dataset_dir / "source_public_raw.csv", index=False, encoding="utf-8-sig")
    frame.to_csv(dataset_dir / "source.csv", index=False, encoding="utf-8-sig")
    frame.to_pickle(dataset_dir / "sheet-main.pkl")
    (dataset_dir / "public_source.json").write_text(
        json.dumps(
            {
                "source_url": SOURCE_URL,
                "api_url": API_URL,
                "title": source_payload.get("title"),
                "description": source_payload.get("description"),
                "license": "CC0/public dataset page metadata",
                "normalization_note": "Raw GoMask public preview rows are normalized into the internet_ops 24-field test schema with deterministic derived funnel and quality columns.",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    sheets = [{"name": "Sheet1", "storage_file": "sheet-main.pkl", "rows": int(len(frame)), "columns": int(len(frame.columns))}]
    metadata = build_profile(
        dataset_id=dataset_id,
        name="GoMask public campaign conversion breakdown normalized internet ops smoke",
        filename="gomask_campaign_channel_conversion_breakdown_normalized.csv",
        active_sheet="Sheet1",
        sheets=sheets,
        frame=frame,
    )
    metadata["public_source"] = {
        "source_url": SOURCE_URL,
        "api_url": API_URL,
        "title": source_payload.get("title"),
        "raw_row_count": len(raw_rows),
        "normalized_note": "Normalized deterministic test dataset derived from public GoMask campaign rows.",
    }
    save_metadata(dataset_dir, metadata)
    return metadata


def main() -> None:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    source_payload, raw_rows = _fetch_public_rows()
    frame = _normalize_rows(raw_rows)
    metadata = _persist_dataset(frame, source_payload, raw_rows)
    print(json.dumps({"event": "dataset_ready", "dataset_id": metadata["dataset_id"], "rows": len(frame), "columns": len(frame.columns), "source_url": SOURCE_URL}, ensure_ascii=False), flush=True)

    def progress(event: dict[str, Any]) -> None:
        payload = event.get("payload") or {}
        print(
            json.dumps(
                {
                    "event": "progress",
                    "stage_id": event.get("stage_id"),
                    "title": event.get("title"),
                    "status": payload.get("status"),
                    "pipeline_job_id": payload.get("pipeline_job_id"),
                    "pipeline_stage": payload.get("pipeline_current_stage_id"),
                    "pipeline_progress": payload.get("pipeline_progress_percent"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    request = SmartReportRequest(
        sheet_name="Sheet1",
        business_profile="internet_operations_report",
        report_style="deep_dive",
        report_language="zh-CN",
        target_audience="管理层、增长负责人、投放负责人",
        user_requirement=(
            "使用公开 GoMask campaign channel conversion breakdown 数据实测互联网运营链。"
            "重点验证口径一致、连续叙事、图表解释、D1-D7 日动作、预算阈值和完整表长版。"
        ),
        core_purpose="公开互联网营销投放数据的经营复盘与预算迁移决策",
        expected_result="生成主报告、精简管理版和完整表长版，并通过互联网运营口径一致性门。",
        enable_premium_pipeline=False,
        generate_full_table_version=True,
    )
    report = generate_smart_report(metadata["dataset_id"], request, progress_callback=progress)
    output = {
        "event": "report_done",
        "report_id": report.get("report_id"),
        "report_dir": str((REPORTS_DIR / f"smart-report-{report.get('report_id')}").resolve()),
        "internet_ops_pipeline_job_id": report.get("internet_ops_long_cli_pipeline_job_id"),
        "internet_ops_pipeline_status": (report.get("internet_ops_long_cli_pipeline") or {}).get("status"),
        "internet_ops_pipeline_error": (report.get("internet_ops_long_cli_pipeline") or {}).get("error"),
        "main_downloadable": report.get("main_downloadable") or {},
        "downloadables": report.get("downloadables") or [],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
