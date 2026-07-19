from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from starlette.datastructures import UploadFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models import SmartReportRequest  # noqa: E402
from app.services.codex_service import codex_judge_report, codex_summarize_eval_feedback  # noqa: E402
from app.services.dataset_service import persist_dataset  # noqa: E402
from app.services.report_service import _management_section_ids, generate_smart_report  # noqa: E402


TMP_DIR = PROJECT_ROOT / "tmp" / "large_report_eval"
OUT_DIR = PROJECT_ROOT / "reports"
TMP_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


MEDIA = ["Bilibili", "快手", "优酷", "芒果TV", "小红书", "微博", "抖音"]
TERMINALS = ["PHONE端", "PAD端", "多屏(PC+移动)", "OTT", "移动端(PAD+PHONE)"]
BRANDS = ["珍护", "铂萃", "塞纳牧", "有机A2", "托菲尔", "基础款"]
CAMPAIGNS = ["开屏", "信息流", "全屏闪屏", "前贴片", "暂停广告", "品牌专区"]
PROVINCES = ["上海", "北京", "广东", "江苏", "浙江", "山东", "四川", "湖北"]
OPS_CHANNELS = ["自然", "广告", "社群", "联盟", "搜索", "Push"]
OPS_ACTIVITIES = ["拉新活动", "召回活动", "内容上新", "会员促活", "搜索冲量"]
RESP_CENTERS = ["华东大区", "华南大区", "电商事业部", "线下零售", "品牌中心", "供应链中心"]


def _report_payload(report: dict[str, Any], scenario: str) -> dict[str, Any]:
    management_ids = _management_section_ids()
    management_sections = [section for section in report["sections"] if section["id"] in management_ids]
    appendix_sections = [section for section in report["sections"] if section["id"] not in management_ids]
    management_markdown_lines: list[str] = []
    for section in management_sections[:12]:
        management_markdown_lines.append(f"## {section['title']}")
        if section.get("summary"):
            management_markdown_lines.append(str(section["summary"]))
        for bullet in section.get("bullets", [])[:5]:
            management_markdown_lines.append(f"- {bullet}")
        for table in section.get("tables", [])[:3]:
            management_markdown_lines.append(f"### {table['title']}")
            if table.get("columns"):
                management_markdown_lines.append("| " + " | ".join(str(column) for column in table["columns"]) + " |")
                management_markdown_lines.append("| " + " | ".join(["---"] * len(table["columns"])) + " |")
                for row in table.get("rows", [])[:5]:
                    management_markdown_lines.append(
                        "| " + " | ".join(str(row.get(column, "")) for column in table["columns"]) + " |"
                    )
    return {
        "scenario": scenario,
        "title": report["title"],
        "dataset_name": report["dataset_name"],
        "sheet_name": report["sheet_name"],
        "executive_summary": report["executive_summary"][:8],
        "management_sections": [
            {
                "id": section["id"],
                "title": section["title"],
                "summary": section["summary"],
                "bullets": section["bullets"][:5],
                "tables": [
                    {
                        "title": table["title"],
                        "columns": table.get("columns", [])[:8],
                        "rows": [
                            {column: row.get(column, "") for column in table.get("columns", [])[:8]}
                            for row in table.get("rows", [])[:5]
                        ],
                    }
                    for table in section.get("tables", [])[:3]
                ],
            }
            for section in management_sections[:12]
        ],
        "appendix_titles": [
            {
                "id": section["id"],
                "title": section["title"],
                "table_titles": [table["title"] for table in section.get("tables", [])[:2]],
            }
            for section in appendix_sections[:12]
        ],
        "report_structure": {
            "management_section_count": len(management_sections),
            "appendix_section_count": len(appendix_sections),
            "total_section_count": len(report["sections"]),
        },
        "management_markdown_excerpt": "\n".join(management_markdown_lines)[:12000],
    }


def _make_media_frame(row_count: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base_date = datetime(2025, 1, 1)
    dates = pd.to_datetime([base_date + timedelta(days=int(offset)) for offset in rng.integers(0, 180, size=row_count)])
    estimated_impressions = rng.lognormal(mean=12.0, sigma=0.6, size=row_count).astype(np.int64)
    ctr = rng.uniform(0.002, 0.08, size=row_count)
    estimated_clicks = np.round(estimated_impressions * ctr * rng.uniform(0.6, 1.0, size=row_count)).astype(np.int64)
    monitored_impressions = np.round(estimated_impressions * rng.uniform(0.82, 1.22, size=row_count)).astype(np.int64)
    monitored_clicks = np.round(monitored_impressions * ctr * rng.uniform(0.75, 1.35, size=row_count)).astype(np.int64)
    budget = np.round(monitored_impressions / 1000 * rng.uniform(18, 120, size=row_count), 2)
    conversions = np.round(monitored_clicks * rng.uniform(0.003, 0.04, size=row_count)).astype(np.int64)
    cpa = budget / np.maximum(conversions, 1)
    return pd.DataFrame(
        {
            "日期": dates,
            "媒体": rng.choice(MEDIA, size=row_count),
            "终端": rng.choice(TERMINALS, size=row_count),
            "品牌": rng.choice(BRANDS, size=row_count),
            "省份": rng.choice(PROVINCES, size=row_count),
            "点位": rng.choice(CAMPAIGNS, size=row_count),
            "预算": budget,
            "预估曝光": estimated_impressions,
            "预估点击": estimated_clicks,
            "监测曝光": monitored_impressions,
            "监测点击": monitored_clicks,
            "曝光完成率": monitored_impressions / np.maximum(estimated_impressions, 1),
            "点击完成率": monitored_clicks / np.maximum(estimated_clicks, 1),
            "点击率": monitored_clicks / np.maximum(monitored_impressions, 1),
            "转化数": conversions,
            "CPA": np.round(cpa, 4),
        }
    )


def _make_management_accounting_frame(row_count: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base_date = datetime(2025, 1, 1)
    periods = [base_date + timedelta(days=int(offset)) for offset in rng.integers(0, 365, size=row_count)]
    revenue = rng.lognormal(mean=8.2, sigma=0.45, size=row_count)
    cost = revenue * rng.uniform(0.48, 0.82, size=row_count)
    opex = revenue * rng.uniform(0.08, 0.25, size=row_count)
    gross_profit = revenue - cost
    net_profit = gross_profit - opex
    budget_revenue = revenue * rng.uniform(0.9, 1.08, size=row_count)
    budget_cost = cost * rng.uniform(0.9, 1.08, size=row_count)
    receivable = revenue * rng.uniform(0.1, 0.34, size=row_count)
    inventory = cost * rng.uniform(0.08, 0.28, size=row_count)
    payable = cost * rng.uniform(0.05, 0.22, size=row_count)
    cash_flow = net_profit - receivable * 0.25 - inventory * 0.1 + payable * 0.18
    assets = revenue * rng.uniform(1.1, 2.8, size=row_count)
    liabilities = assets * rng.uniform(0.22, 0.68, size=row_count)
    equity = assets - liabilities
    return pd.DataFrame(
        {
            "日期": pd.to_datetime(periods),
            "责任中心": rng.choice(RESP_CENTERS, size=row_count),
            "产品线": rng.choice(BRANDS, size=row_count),
            "营业收入": np.round(revenue, 2),
            "营业成本": np.round(cost, 2),
            "费用": np.round(opex, 2),
            "毛利": np.round(gross_profit, 2),
            "净利润": np.round(net_profit, 2),
            "预算收入": np.round(budget_revenue, 2),
            "实际收入": np.round(revenue, 2),
            "预算成本": np.round(budget_cost, 2),
            "实际成本": np.round(cost, 2),
            "应收账款": np.round(receivable, 2),
            "应付账款": np.round(payable, 2),
            "存货": np.round(inventory, 2),
            "经营现金流": np.round(cash_flow, 2),
            "总资产": np.round(assets, 2),
            "总负债": np.round(liabilities, 2),
            "所有者权益": np.round(equity, 2),
        }
    )


def _make_ops_frame(row_count: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base_date = datetime(2025, 1, 1)
    dates = pd.to_datetime([base_date + timedelta(days=int(offset)) for offset in rng.integers(0, 240, size=row_count)])
    active_users = rng.lognormal(mean=8.0, sigma=0.5, size=row_count).astype(np.int64)
    new_users = np.round(active_users * rng.uniform(0.06, 0.28, size=row_count)).astype(np.int64)
    retained_users = np.round(active_users * rng.uniform(0.22, 0.62, size=row_count)).astype(np.int64)
    orders = np.round(active_users * rng.uniform(0.01, 0.06, size=row_count)).astype(np.int64)
    return pd.DataFrame(
        {
            "日期": dates,
            "渠道": rng.choice(OPS_CHANNELS, size=row_count),
            "活动": rng.choice(OPS_ACTIVITIES, size=row_count),
            "内容主题": rng.choice(["品牌故事", "福利活动", "攻略教程", "产品卖点", "用户案例"], size=row_count),
            "活跃用户": active_users,
            "新增用户": new_users,
            "留存用户": retained_users,
            "留存率": retained_users / np.maximum(active_users, 1),
            "转化率": rng.uniform(0.01, 0.09, size=row_count),
            "订单数": orders,
        }
    )


def _upload_frame(frame: pd.DataFrame, filename: str) -> dict[str, Any]:
    bio = BytesIO()
    frame.to_csv(bio, index=False, encoding="utf-8-sig")
    bio.seek(0)
    upload = UploadFile(filename=filename, file=bio)
    return asyncio.run(persist_dataset(upload))


def _run_report(dataset_id: str, scenario: str) -> dict[str, Any]:
    requests = {
        "media": SmartReportRequest(
            report_style="deep_dive",
            user_requirement="请输出一份面向管理层的投放复盘报告",
            problem_to_solve="判断哪些投放单元真正贡献规模与效率，哪些应该优先复盘或收缩",
            target_audience="市场负责人 / 媒介负责人 / 管理层",
            core_purpose="形成投放复盘与预算动作判断",
            expected_result="一份中文主报告",
        ),
        "management": SmartReportRequest(
            report_style="deep_dive",
            user_requirement="请输出一份面向财务和经营负责人的管理会计分析报告",
            problem_to_solve="判断利润质量、预算偏差、资金占用和责任中心问题",
            target_audience="财务负责人 / 经营负责人 / 管理层",
            core_purpose="形成财务经营联动复盘",
            expected_result="一份中文主报告",
        ),
        "ops": SmartReportRequest(
            report_style="deep_dive",
            user_requirement="请输出一份互联网运营复盘报告",
            problem_to_solve="判断新增、留存和转化的主要差异及后续优化重点",
            target_audience="增长负责人 / 运营负责人 / 管理层",
            core_purpose="形成运营复盘与增长动作判断",
            expected_result="一份中文主报告",
        ),
    }
    return generate_smart_report(dataset_id, requests[scenario])


def _score_should_retry(score: dict[str, Any]) -> bool:
    if score.get("mode") != "fallback":
        return False
    reason = str(score.get("reason") or "").lower()
    return any(
        token in reason
        for token in [
            "503",
            "502",
            "timed out",
            "timeout",
            "temporarily unavailable",
            "read operation timed out",
            "getaddrinfo failed",
            "bad gateway",
        ]
    )


def _score_report(report: dict[str, Any], scenario: str) -> dict[str, Any]:
    payload = _report_payload(report, scenario)
    original_effort = os.environ.get("OPENAI_REASONING_EFFORT")
    os.environ["OPENAI_REASONING_EFFORT"] = os.getenv("ASTERIA_JUDGE_EFFORT", "low")
    try:
        score: dict[str, Any] = {}
        for attempt in range(4):
            score = codex_judge_report(payload)
            if not _score_should_retry(score):
                return score
            time.sleep(4 * (attempt + 1))
        return score
    finally:
        if original_effort is None:
            os.environ.pop("OPENAI_REASONING_EFFORT", None)
        else:
            os.environ["OPENAI_REASONING_EFFORT"] = original_effort


def _build_cases(row_count: int, replicates: int) -> list[tuple[str, pd.DataFrame, str]]:
    cases: list[tuple[str, pd.DataFrame, str]] = []
    for replicate in range(replicates):
        suffix = f"r{replicate + 1}"
        cases.extend(
            [
                ("media", _make_media_frame(row_count, 42 + replicate), f"eval-media-{row_count}-{suffix}.csv"),
                ("management", _make_management_accounting_frame(row_count, 43 + replicate), f"eval-management-{row_count}-{suffix}.csv"),
                ("ops", _make_ops_frame(row_count, 44 + replicate), f"eval-ops-{row_count}-{suffix}.csv"),
            ]
        )
    return cases


def _summarize_scores(results: list[dict[str, Any]]) -> dict[str, Any]:
    weakness_counter: dict[str, int] = {}
    mode_counter: dict[str, int] = {}
    live_scores: list[int] = []
    for item in results:
        score = item["score"]
        mode = str(score.get("mode") or "unknown")
        mode_counter[mode] = mode_counter.get(mode, 0) + 1
        if mode != "fallback":
            live_scores.append(int(score.get("total_score", 0)))
        for weakness in score.get("weaknesses", []):
            weakness_counter[str(weakness)] = weakness_counter.get(str(weakness), 0) + 1

    eval_summary = {
        "average_score": round(sum(int(item["score"].get("total_score", 0)) for item in results) / len(results), 2),
        "live_average_score": round(sum(live_scores) / len(live_scores), 2) if live_scores else None,
        "live_score_count": len(live_scores),
        "score_modes": mode_counter,
        "common_weaknesses": sorted(weakness_counter.items(), key=lambda pair: pair[1], reverse=True),
        "results": results,
    }
    eval_summary["codex_feedback_summary"] = codex_summarize_eval_feedback(
        {
            "average_score": eval_summary["average_score"],
            "live_average_score": eval_summary["live_average_score"],
            "live_score_count": eval_summary["live_score_count"],
            "score_modes": eval_summary["score_modes"],
            "common_weaknesses": eval_summary["common_weaknesses"][:12],
            "results": [
                {
                    "scenario": item["scenario"],
                    "score": item["score"].get("total_score"),
                    "mode": item["score"].get("mode"),
                    "weaknesses": item["score"].get("weaknesses", [])[:5],
                    "improvement_actions": item["score"].get("improvement_actions", [])[:5],
                }
                for item in results
            ],
        }
    )
    return eval_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run large-report Codex evaluation.")
    parser.add_argument("--row-count", type=int, default=120_000, help="Rows per synthetic dataset.")
    parser.add_argument("--replicates", type=int, default=1, help="How many seeds to run per scenario.")
    args = parser.parse_args(argv)

    os.environ.setdefault("ASTERIA_DISABLE_TOOL_ASSETS", "1")
    os.environ.setdefault("MPLBACKEND", "Agg")
    started = time.time()
    cases = _build_cases(args.row_count, args.replicates)
    results: list[dict[str, Any]] = []
    for scenario, frame, filename in cases:
        dataset = _upload_frame(frame, filename)
        report = _run_report(dataset["dataset_id"], scenario)
        score = _score_report(report, scenario)
        results.append(
            {
                "scenario": scenario,
                "dataset_id": dataset["dataset_id"],
                "row_count": int(len(frame)),
                "report_id": report["report_id"],
                "main_downloadable": report["main_downloadable"]["path"],
                "score": score,
            }
        )
        print(f"[large-report-eval] {scenario}: report={report['report_id']} score={score.get('total_score')}")

    eval_summary = _summarize_scores(results)
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.time() - started, 2),
        "row_count": args.row_count,
        "replicates": args.replicates,
        **eval_summary,
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = OUT_DIR / f"large-report-eval-{stamp}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[large-report-eval] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
