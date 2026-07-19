from __future__ import annotations

import argparse
import json
import mimetypes
import os
import random
import string
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
TMP_DIR = ROOT / "tmp" / "load_stress"
DEFAULT_BASE_URL = "http://127.0.0.1:8787"


MEDIA = ["Bilibili", "快手", "优酷", "芒果TV", "小红书", "微博", "抖音"]
TERMINALS = ["PHONE端", "PAD端", "多屏(PC+移动)", "OTT", "移动端(PAD+PHONE)"]
BRANDS = ["珍护", "铂萃", "塞纳牧", "有机A2", "托菲尔", "基础款"]
CAMPAIGNS = ["开屏", "信息流", "全屏闪屏", "前贴片", "暂停广告", "品牌专区"]
PROVINCES = ["上海", "北京", "广东", "江苏", "浙江", "山东", "四川", "湖北"]


def _http_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=7200) as response:
        return json.loads(response.read().decode("utf-8"))


def _multipart_upload(url: str, file_path: Path) -> dict[str, Any]:
    boundary = f"----AsteriaBoundary{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()
    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=7200) as response:
        return json.loads(response.read().decode("utf-8"))


def _random_point(indexes: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    brands = rng.choice(BRANDS, size=len(indexes))
    campaigns = rng.choice(CAMPAIGNS, size=len(indexes))
    suffix = rng.choice(["程序化PD池", "品牌专区", "PDB100%推送比", "无退回", "剧场TOP3"], size=len(indexes))
    return np.char.add(
        np.char.add(np.char.add(brands.astype(str), "-"), campaigns.astype(str)),
        np.char.add("-", suffix.astype(str)),
    )


def _build_frame(row_count: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base_date = datetime(2025, 1, 1)
    date_offsets = rng.integers(0, 180, size=row_count)
    dates = pd.to_datetime([base_date + timedelta(days=int(offset)) for offset in date_offsets])

    media = rng.choice(MEDIA, size=row_count)
    terminal = rng.choice(TERMINALS, size=row_count)
    brand = rng.choice(BRANDS, size=row_count)
    province = rng.choice(PROVINCES, size=row_count)
    point = _random_point(np.arange(row_count), rng)

    estimated_impressions = rng.lognormal(mean=12.1, sigma=0.65, size=row_count).astype(np.int64)
    ctr = rng.uniform(0.002, 0.12, size=row_count)
    estimated_clicks = np.round(estimated_impressions * ctr * rng.uniform(0.5, 1.05, size=row_count)).astype(np.int64)
    monitored_impressions = np.round(estimated_impressions * rng.uniform(0.78, 1.28, size=row_count)).astype(np.int64)
    monitored_clicks = np.round(monitored_impressions * ctr * rng.uniform(0.8, 1.45, size=row_count)).astype(np.int64)

    exposure_completion_rate = monitored_impressions / np.maximum(estimated_impressions, 1)
    click_completion_rate = monitored_clicks / np.maximum(estimated_clicks, 1)
    click_rate = monitored_clicks / np.maximum(monitored_impressions, 1)

    budget = np.round(monitored_impressions / 1000 * rng.uniform(18, 120, size=row_count), 2)
    conversion_rate = rng.uniform(0.002, 0.04, size=row_count)
    conversions = np.round(monitored_clicks * conversion_rate).astype(np.int64)
    cpa = budget / np.maximum(conversions, 1)

    frame = pd.DataFrame(
        {
            "日期": dates,
            "媒体": media,
            "终端": terminal,
            "品牌": brand,
            "省份": province,
            "点位": point,
            "预算": budget,
            "预估曝光": estimated_impressions,
            "预估点击": estimated_clicks,
            "监测曝光": monitored_impressions,
            "监测点击": monitored_clicks,
            "曝光完成率": exposure_completion_rate,
            "点击完成率": click_completion_rate,
            "点击率": click_rate,
            "转化数": conversions,
            "CPA": np.round(cpa, 4),
        }
    )

    # Inject a small amount of realistic placeholder noise.
    if row_count >= 10_000:
        dash_index = rng.choice(frame.index.to_numpy(), size=max(1, row_count // 250), replace=False)
        frame.loc[dash_index, "点击完成率"] = np.nan
    return frame


def _write_case_csv(row_count: int, seed: int) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    path = TMP_DIR / f"stress-{row_count:,}".replace(",", "_")
    csv_path = Path(str(path) + ".csv")
    frame = _build_frame(row_count, seed)
    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return csv_path


def _backend_process_stats() -> dict[str, Any]:
    cmd = (
        "$conn = Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue | "
        "Where-Object { $_.State -eq 'Listen' } | "
        "Select-Object -First 1; "
        "if (-not $conn) { return '{\"status\":\"down\"}' }; "
        "$p = Get-Process -Id $conn.OwningProcess; "
        "$obj = [pscustomobject]@{"
        "status='up'; pid=$p.Id; cpu=$p.CPU; working_set_mb=[math]::Round($p.WorkingSet64/1MB,2); "
        "private_memory_mb=[math]::Round($p.PrivateMemorySize64/1MB,2)}; "
        "$obj | ConvertTo-Json -Compress"
    )
    raw = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    if not raw:
        return {"status": "unknown"}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"status": "unknown", "raw": raw}


def run_case(base_url: str, row_count: int, seed: int, report_style: str) -> dict[str, Any]:
    csv_path = _write_case_csv(row_count, seed)
    case_result: dict[str, Any] = {
        "row_count": row_count,
        "seed": seed,
        "file_path": str(csv_path),
        "file_size_mb": round(csv_path.stat().st_size / 1024 / 1024, 2),
        "report_style": report_style,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }

    before_stats = _backend_process_stats()
    case_result["backend_before"] = before_stats

    upload_started = time.perf_counter()
    dataset = _multipart_upload(f"{base_url}/api/datasets/upload", csv_path)
    upload_elapsed = time.perf_counter() - upload_started
    case_result["upload_seconds"] = round(upload_elapsed, 2)
    case_result["dataset_id"] = dataset["dataset_id"]
    case_result["detected_rows"] = dataset["row_count"]
    case_result["detected_columns"] = dataset["column_count"]
    case_result["numeric_columns"] = dataset["numeric_columns"]
    case_result["datetime_columns"] = dataset["datetime_columns"]
    case_result["categorical_columns"] = dataset["categorical_columns"]

    report_started = time.perf_counter()
    report = _http_json(
        f"{base_url}/api/datasets/{dataset['dataset_id']}/smart-report",
        method="POST",
        payload={
            "report_style": report_style,
            "report_language": "zh-CN",
            "user_requirement": "请基于全量投放明细做中文全量压测复盘，覆盖媒体、终端、点位、效率、异常和建议。",
            "problem_to_solve": "验证系统在海量数据下的导入、推理和报告生成稳定性。",
            "target_audience": "产品负责人 / 数据负责人 / 工程负责人",
            "core_purpose": "海量数据压测与性能评估",
            "expected_result": "一份完整中文报告和性能结论",
            "key_constraints": "优先保证端到端生成成功，并记录耗时与潜在瓶颈。",
        },
    )
    report_elapsed = time.perf_counter() - report_started
    case_result["report_seconds"] = round(report_elapsed, 2)
    case_result["report_id"] = report["report_id"]
    case_result["section_count"] = len(report["sections"])
    case_result["downloadable_count"] = len(report["downloadables"])
    case_result["main_downloadable"] = report["main_downloadable"]["path"]

    after_stats = _backend_process_stats()
    case_result["backend_after"] = after_stats
    case_result["total_seconds"] = round(upload_elapsed + report_elapsed, 2)
    case_result["completed_at"] = datetime.now().isoformat(timespec="seconds")
    return case_result


def write_reports(results: list[dict[str, Any]], markdown_path: Path, json_path: Path) -> None:
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 海量数据压测报告",
        "",
        f"- 执行时间: {datetime.now().isoformat(timespec='seconds')}",
        f"- 压测案例数: {len(results)}",
        "",
        "| 行数 | 文件大小(MB) | 上传耗时(s) | 报告耗时(s) | 总耗时(s) | 报告章节数 | 主报告 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in results:
        if "error" in item:
            lines.append(
                f"| {item['row_count']:,} | - | - | - | - | - | FAILED: {item['error']} |"
            )
        else:
            lines.append(
                "| {row_count:,} | {file_size_mb:.2f} | {upload_seconds:.2f} | {report_seconds:.2f} | {total_seconds:.2f} | {section_count} | {main_downloadable} |".format(
                    **item
                )
            )

    lines.extend(["", "## 案例详情", ""])
    for item in results:
        if "error" in item:
            lines.extend(
                [
                    f"### {item['row_count']:,} rows",
                    f"- 结果: 失败",
                    f"- 错误: `{item['error']}`",
                    "",
                ]
            )
            continue
        lines.extend(
            [
                f"### {item['row_count']:,} rows",
                f"- 数据集: `{item['dataset_id']}`",
                f"- 上传耗时: `{item['upload_seconds']:.2f}s`",
                f"- 报告耗时: `{item['report_seconds']:.2f}s`",
                f"- 总耗时: `{item['total_seconds']:.2f}s`",
                f"- 导入识别: `{item['detected_rows']}` rows / `{item['detected_columns']}` columns",
                f"- 数值列数: `{len(item['numeric_columns'])}`，时间列数: `{len(item['datetime_columns'])}`，分类列数: `{len(item['categorical_columns'])}`",
                f"- 后端前状态: `{item['backend_before']}`",
                f"- 后端后状态: `{item['backend_after']}`",
                f"- 主报告: `{item['main_downloadable']}`",
                "",
            ]
        )

    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local large-data load stress tests against Asteria Analyst.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100000, 300000, 1000000])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report-style", choices=["executive", "deep_dive"], default="executive")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for index, size in enumerate(args.sizes):
        print(f"[load-stress] running case {index + 1}/{len(args.sizes)} with {size:,} rows")
        try:
            result = run_case(args.base_url.rstrip("/"), size, args.seed + index, args.report_style)
            results.append(result)
            print(
                f"[load-stress] done {size:,} rows: upload={result['upload_seconds']:.2f}s "
                f"report={result['report_seconds']:.2f}s total={result['total_seconds']:.2f}s"
            )
        except urllib.error.HTTPError as error:
            payload = error.read().decode("utf-8", errors="ignore")
            results.append(
                {
                    "row_count": size,
                    "seed": args.seed + index,
                    "error": f"HTTP {error.code}: {payload}",
                    "started_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            print(f"[load-stress] failed {size:,} rows: HTTP {error.code}")
        except Exception as error:  # noqa: BLE001
            results.append(
                {
                    "row_count": size,
                    "seed": args.seed + index,
                    "error": str(error),
                    "started_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            print(f"[load-stress] failed {size:,} rows: {error}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = REPORTS_DIR / f"load-stress-{stamp}.json"
    markdown_path = REPORTS_DIR / f"load-stress-{stamp}.md"
    write_reports(results, markdown_path, json_path)
    print(f"[load-stress] wrote {markdown_path}")
    print(f"[load-stress] wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
