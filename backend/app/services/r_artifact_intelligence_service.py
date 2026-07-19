from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import RWorkflowIntelligenceRequest
from app.services.codex_service import (
    build_r_artifact_intelligence_system_prompt,
    codex_interpret_r_artifact_bundle_from_files,
    codex_interpret_r_artifact_bundle_from_summary,
)
from app.services.path_service import REPORTS_DIR
from app.services.r_workflow_service import _build_r_workflow_column_registry


def _resolve_r_workflow_dir(report_id: str) -> tuple[Path, Path]:
    clean_report_id = str(report_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", clean_report_id):
        raise ValueError("report_id must contain only letters, digits, dots, underscores, or hyphens")

    reports_root = REPORTS_DIR.resolve()
    report_dir = (reports_root / f"smart-report-{clean_report_id}").resolve()
    try:
        report_dir.relative_to(reports_root)
    except ValueError as exc:
        raise ValueError("report_id resolves outside the reports directory") from exc

    workflow_dir = (report_dir / "r-workflow").resolve()
    try:
        workflow_dir.relative_to(report_dir)
    except ValueError as exc:
        raise ValueError("r-workflow resolves outside the report directory") from exc
    if not report_dir.exists():
        raise FileNotFoundError(f"Report directory not found for report_id={clean_report_id}")
    if not workflow_dir.exists():
        raise FileNotFoundError(f"R workflow directory not found for report_id={clean_report_id}")
    return report_dir, workflow_dir


def _find_required_artifact(workflow_dir: Path, pattern: str, label: str) -> Path:
    matches = sorted(workflow_dir.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"Required {label} not found under {workflow_dir}")
    return matches[0]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_excel_sheet_summaries(workbook_path: Path) -> list[dict[str, Any]]:
    sheet_summaries: list[dict[str, Any]] = []
    excel_file = pd.ExcelFile(workbook_path)
    for sheet_name in excel_file.sheet_names[:20]:
        try:
            frame = excel_file.parse(sheet_name)
        except Exception:
            continue
        trimmed = frame.head(16).copy()
        trimmed = trimmed.iloc[:, :12]
        trimmed = trimmed.where(pd.notnull(trimmed), None)
        columns = [str(column) for column in frame.columns.astype(str).tolist()[:20]]
        sheet_summaries.append(
            {
                "sheet_name": sheet_name,
                "row_count": int(len(frame)),
                "column_count": int(len(frame.columns)),
                "columns": columns,
                "sample_rows": trimmed.to_dict(orient="records"),
            }
        )
    return sheet_summaries


SUMMARY_PACK_PRIORITY_NAMES: list[str] = [
    "pca_axis_summary",
    "cluster_member_detail",
    "cluster_profile",
    "category_metric_summary",
    "budget_variance_summary",
    "overview",
    "results_index",
    "summary_stats",
    "top_categories",
    "temporal_trend",
    "top_items",
    "funnel_metrics",
    "correlation_pairs",
]

SUMMARY_PACK_PRIORITY_FILES: list[tuple[str, str]] = [
    ("pca_axis_summary", "pca_axis_summary.csv"),
    ("cluster_member_detail", "cluster_member_detail.csv"),
    ("cluster_profile", "cluster_profile.csv"),
    ("category_metric_summary", "category_metric_summary.csv"),
    ("budget_variance_summary", "budget_variance_summary.csv"),
]


def _read_artifact_table_summary(workflow_dir: Path, artifact_name: str, filename: str) -> dict[str, Any] | None:
    path = workflow_dir / filename
    if not path.exists():
        return None
    frame = _read_csv_if_exists(path)
    if frame.empty and not path.exists():
        return None
    trimmed = frame.head(16).copy()
    trimmed = trimmed.iloc[:, :12]
    trimmed = trimmed.where(pd.notnull(trimmed), None)
    return {
        "artifact_name": artifact_name,
        "file_name": filename,
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": [str(column) for column in frame.columns.astype(str).tolist()[:20]],
        "sample_rows": trimmed.to_dict(orient="records"),
    }


def _read_priority_artifact_tables(workflow_dir: Path) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for artifact_name, filename in SUMMARY_PACK_PRIORITY_FILES:
        summary = _read_artifact_table_summary(workflow_dir, artifact_name, filename)
        if summary:
            selected.append(summary)
    return selected


def _extract_pdf_text(pdf_path: Path, *, max_pages: int = 12, max_chars: int = 40000) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return ""
    parts: list[str] = []
    total_chars = 0
    for page in reader.pages[:max_pages]:
        text = page.extract_text() or ""
        if not text.strip():
            continue
        remaining = max_chars - total_chars
        if remaining <= 0:
            break
        clipped = text[:remaining]
        parts.append(clipped)
        total_chars += len(clipped)
    return "\n\n".join(parts).strip()


def _guess_business_domain(sheet_summaries: list[dict[str, Any]]) -> str:
    combined = " ".join(
        " ".join(str(col) for col in (item.get("columns") or []))
        for item in sheet_summaries
    ).lower()
    if any(token in combined for token in ["营业收入", "营业成本", "毛利", "净利润", "预算", "实际", "现金流"]):
        return "management_accounting"
    if any(token in combined for token in ["page_views", "cart_count", "buy_count", "item_id", "category_id"]):
        return "ecommerce_operations"
    if any(token in combined for token in ["impressions", "clicks", "spend", "conversions", "campaign", "media"]):
        return "media_campaign"
    if any(token in combined for token in ["active_users", "新增用户", "留存率", "渠道", "活动"]):
        return "internet_operations"
    return "generic_business"


def _build_business_context_pack(
    sheet_summaries: list[dict[str, Any]],
    pdf_excerpt: str,
    *,
    workflow_dir: Path,
) -> dict[str, Any]:
    prioritized_sheet_names = list(SUMMARY_PACK_PRIORITY_NAMES)
    selected = []
    seen = set()
    for target in prioritized_sheet_names:
        for item in sheet_summaries:
            if str(item.get("sheet_name") or "") == target and target not in seen:
                selected.append(item)
                seen.add(target)
    for item in sheet_summaries:
        name = str(item.get("sheet_name") or "")
        if name not in seen and len(selected) < 12:
            selected.append(item)
            seen.add(name)

    key_rows: list[dict[str, Any]] = []
    for item in selected:
        sample_rows = item.get("sample_rows") or []
        if sample_rows:
            key_rows.append(
                {
                    "sheet_name": item.get("sheet_name"),
                    "row_count": item.get("row_count"),
                    "sample_rows": sample_rows[:4],
                }
            )

    selected_artifact_tables = _read_priority_artifact_tables(workflow_dir)
    key_artifact_rows: list[dict[str, Any]] = []
    for item in selected_artifact_tables:
        sample_rows = item.get("sample_rows") or []
        if sample_rows:
            key_artifact_rows.append(
                {
                    "artifact_name": item.get("artifact_name"),
                    "file_name": item.get("file_name"),
                    "row_count": item.get("row_count"),
                    "sample_rows": sample_rows[:4],
                }
            )

    excerpt_lines = [line.strip() for line in pdf_excerpt.splitlines() if line.strip()]
    pdf_key_passages = excerpt_lines[:30]

    return {
        "business_domain_guess": _guess_business_domain(sheet_summaries),
        "selected_sheet_summaries": selected,
        "key_sheet_rows": key_rows,
        "selected_artifact_tables": selected_artifact_tables,
        "key_artifact_rows": key_artifact_rows,
        "pdf_key_passages": pdf_key_passages,
        "pdf_excerpt": pdf_excerpt[:12000],
    }


def _safe_slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(text or "").strip().lower()).strip("_")
    return cleaned[:48] or "followup"


def _extract_action_recommendations(result: dict[str, Any]) -> list[dict[str, Any]]:
    actions = result.get("action_recommendations") or []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(actions, 1):
        if isinstance(item, dict):
            normalized.append(
                {
                    "priority": str(item.get("priority") or ""),
                    "action": str(item.get("action") or f"action_{index}").strip(),
                    "why": str(item.get("why") or "").strip(),
                    "next_step": [str(step).strip() for step in (item.get("next_step") or []) if str(step).strip()],
                }
            )
        else:
            text = str(item or "").strip()
            if text:
                normalized.append(
                    {
                        "priority": "",
                        "action": text,
                        "why": "",
                        "next_step": [],
                    }
                )
    return normalized


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception:
            continue
    return pd.DataFrame()


def _pick_column(columns: list[str], candidates: list[str]) -> str:
    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    for column in columns:
        lower = column.lower()
        if any(candidate.lower() in lower for candidate in candidates):
            return column
    return ""


def _build_followup_tables(
    *,
    workflow_dir: Path,
    cleaned_df: pd.DataFrame,
    column_role_registry: dict[str, Any],
    action: dict[str, Any],
) -> list[dict[str, Any]]:
    action_text = " ".join(
        [
            str(action.get("action") or ""),
            str(action.get("why") or ""),
            " ".join(action.get("next_step") or []),
        ]
    )
    lower = action_text.lower()
    tables: list[dict[str, Any]] = []

    correlation_pairs = _read_csv_if_exists(workflow_dir / "correlation_pairs.csv")
    cluster_profile = _read_csv_if_exists(workflow_dir / "cluster_profile.csv")
    top_categories = _read_csv_if_exists(workflow_dir / "top_categories.csv")
    category_metric = _read_csv_if_exists(workflow_dir / "category_metric_summary.csv")
    outlier_records = _read_csv_if_exists(workflow_dir / "outlier_records.csv")
    temporal_trend = _read_csv_if_exists(workflow_dir / "temporal_trend.csv")

    if any(token in lower for token in ["口径", "去重", "看板", "重复", "高相关"]):
        if not correlation_pairs.empty:
            focus = correlation_pairs.copy()
            if "abs_correlation" in focus.columns:
                focus = focus.sort_values("abs_correlation", ascending=False)
            tables.append(
                {
                    "name": "metric_dedup_watchlist",
                    "title": "高相关口径压缩清单",
                    "frame": focus.head(30),
                }
            )

    if any(token in lower for token in ["分层", "三类经营盘", "聚类", "分群", "cluster"]):
        if not cluster_profile.empty:
            tables.append(
                {
                    "name": "cluster_management_tiers",
                    "title": "分层经营盘画像",
                    "frame": cluster_profile.head(20),
                }
            )

    if any(token in lower for token in ["责任中心", "产品线", "头部", "复盘", "类别", "渠道", "区域"]):
        if not category_metric.empty:
            focus = category_metric.copy()
            sort_cols = [col for col in ["dimension", "metric", "mean_value"] if col in focus.columns]
            if "mean_value" in focus.columns:
                focus = focus.sort_values(["dimension", "metric", "mean_value"], ascending=[True, True, False])
            tables.append(
                {
                    "name": "dimension_metric_drilldown",
                    "title": "头部分层指标复盘",
                    "frame": focus.head(60),
                }
            )
        if not top_categories.empty:
            tables.append(
                {
                    "name": "head_dimension_objects",
                    "title": "头部结构对象清单",
                    "frame": top_categories.head(40),
                }
            )

    if any(token in lower for token in ["现金", "应收", "存货", "应付", "利润", "联动"]):
        if not correlation_pairs.empty:
            focus = correlation_pairs.copy()
            cols = [str(col) for col in focus.columns]
            left_col = _pick_column(cols, ["left"])
            right_col = _pick_column(cols, ["right"])
            if left_col and right_col:
                mask = focus[left_col].astype(str).str.contains("现金|利润|应收|应付|存货", regex=True) | focus[right_col].astype(str).str.contains("现金|利润|应收|应付|存货", regex=True)
                focus = focus[mask]
            if not focus.empty:
                tables.append(
                    {
                        "name": "profit_cash_linkage",
                        "title": "利润-现金-营运资本联动清单",
                        "frame": focus.head(30),
                    }
                )

    if any(token in lower for token in ["预算", "偏差", "预算执行"]):
        dims = list(column_role_registry.get("category_dimension_columns") or [])[:2]
        budget_pairs = [
            (
                str(item.get("baseline_column") or ""),
                str(item.get("actual_column") or ""),
                str(item.get("family") or ""),
            )
            for item in (column_role_registry.get("variance_pairs") or [])
            if str(item.get("baseline_column") or "").strip() and str(item.get("actual_column") or "").strip()
        ]
        frames: list[pd.DataFrame] = []
        for budget_col, actual_col, family in budget_pairs:
            if budget_col not in cleaned_df.columns or actual_col not in cleaned_df.columns:
                continue
            if dims:
                for dim in dims:
                    grouped = cleaned_df.groupby(dim, dropna=False)[[budget_col, actual_col]].mean().reset_index()
                    grouped["metric_pair"] = f"{budget_col}/{actual_col}"
                    grouped["metric_family"] = family
                    grouped["gap"] = grouped[actual_col] - grouped[budget_col]
                    grouped["gap_rate"] = grouped["gap"] / grouped[budget_col].abs().replace({0: pd.NA})
                    frames.append(grouped)
            else:
                grouped = pd.DataFrame(
                    [
                        {
                            "dimension": "overall",
                            budget_col: cleaned_df[budget_col].mean(),
                            actual_col: cleaned_df[actual_col].mean(),
                            "metric_pair": f"{budget_col}/{actual_col}",
                            "metric_family": family,
                            "gap": cleaned_df[actual_col].mean() - cleaned_df[budget_col].mean(),
                            "gap_rate": (cleaned_df[actual_col].mean() - cleaned_df[budget_col].mean()) / abs(cleaned_df[budget_col].mean()) if cleaned_df[budget_col].mean() not in (0, None) else None,
                        }
                    ]
                )
                frames.append(grouped)
        if frames:
            tables.append(
                {
                    "name": "budget_variance_followup",
                    "title": "预算偏差复盘清单",
                    "frame": pd.concat(frames, ignore_index=True).head(60),
                }
            )

    if any(token in lower for token in ["异常", "台账", "异常样本", "尾部"]):
        if not outlier_records.empty:
            tables.append(
                {
                    "name": "outlier_focus_register",
                    "title": "异常样本专项台账",
                    "frame": outlier_records.head(80),
                }
            )

    if any(token in lower for token in ["时间", "趋势", "节奏", "波动", "运营归因"]):
        if not temporal_trend.empty:
            tables.append(
                {
                    "name": "temporal_followup",
                    "title": "时间趋势复盘清单",
                    "frame": temporal_trend.head(80),
                }
            )

    if not tables and not category_metric.empty:
        tables.append(
            {
                "name": "generic_followup_scan",
                "title": "通用分层扫描",
                "frame": category_metric.head(40),
            }
        )

    return tables


def _run_followup_execution_pack(
    *,
    workflow_dir: Path,
    flow_dir: Path,
    result: dict[str, Any],
) -> dict[str, Any]:
    actions = _extract_action_recommendations(result)
    cleaned_df = _read_csv_if_exists(workflow_dir / "cleaned_dataset.csv")
    column_role_registry = _build_r_workflow_column_registry(cleaned_df) if not cleaned_df.empty else {
        "numeric_method_columns": [],
        "category_dimension_columns": [],
        "object_dimension_columns": [],
        "temporal_columns": [],
        "excluded_from_numeric_methods": [],
    }
    followup_dir = flow_dir / "followup-actions"
    followup_dir.mkdir(parents=True, exist_ok=True)

    execution_rows: list[dict[str, Any]] = []
    generated_tables: list[dict[str, Any]] = []
    used_sheet_names: set[str] = set()
    workbook_path = followup_dir / "r-followup-executions.xlsx"

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        manifest_rows: list[dict[str, Any]] = []
        for index, action in enumerate(actions, 1):
            tables = _build_followup_tables(
                workflow_dir=workflow_dir,
                cleaned_df=cleaned_df,
                column_role_registry=column_role_registry,
                action=action,
            )
            executed = False
            table_names: list[str] = []
            for table in tables:
                frame = table["frame"]
                if frame is None or getattr(frame, "empty", True):
                    continue
                executed = True
                sheet_name = _safe_slug(f"{index}_{table['name']}")[:31]
                frame.to_excel(writer, index=False, sheet_name=sheet_name)
                table_names.append(sheet_name)
                generated_tables.append(
                    {
                        "action_index": index,
                        "action": action.get("action", ""),
                        "sheet_name": sheet_name,
                        "title": table["title"],
                        "row_count": int(len(frame)),
                    }
                )
            execution_rows.append(
                {
                    "action_index": index,
                    "priority": action.get("priority", ""),
                    "action": action.get("action", ""),
                    "why": action.get("why", ""),
                    "status": "executed" if executed else "not_runnable",
                    "executed_tables": " | ".join(table_names),
                }
            )
            manifest_rows.append(execution_rows[-1])

        pd.DataFrame(manifest_rows or [{"action_index": 0, "priority": "", "action": "", "why": "", "status": "empty", "executed_tables": ""}]).to_excel(
            writer,
            index=False,
            sheet_name="action_manifest",
        )
        pd.DataFrame(generated_tables or [{"action_index": 0, "action": "", "sheet_name": "", "title": "", "row_count": 0}]).to_excel(
            writer,
            index=False,
            sheet_name="generated_tables",
        )

    manifest_path = followup_dir / "r-followup-executions.json"
    markdown_path = followup_dir / "r-followup-executions.md"
    manifest_payload = {
        "action_executions": execution_rows,
        "generated_tables": generated_tables,
        "column_role_registry": column_role_registry,
    }
    _write_text(manifest_path, json.dumps(manifest_payload, ensure_ascii=False, indent=2))
    markdown_lines = [
        "# R Follow-up Executions",
        "",
        "## 下一步修复建议与已实跑方法",
        "",
    ]
    for row in execution_rows:
        markdown_lines.extend(
            [
                f"### {row['action_index']}. {row['action']}",
                "",
                f"- priority: {row['priority']}",
                f"- why: {row['why']}",
                f"- status: {row['status']}",
                f"- executed_tables: {row['executed_tables'] or 'none'}",
                "",
            ]
        )
    _write_text(markdown_path, "\n".join(markdown_lines))

    relative_dir = followup_dir.relative_to(REPORTS_DIR.parent).as_posix()
    downloadables = [
        {
            "name": workbook_path.name,
            "path": f"/storage/{relative_dir}/{workbook_path.name}",
            "file_path": str(workbook_path.resolve()),
            "purpose": "建议的管理动作转方法后的实跑总表。",
            "is_main": False,
            "type": "xlsx",
        },
        {
            "name": manifest_path.name,
            "path": f"/storage/{relative_dir}/{manifest_path.name}",
            "file_path": str(manifest_path.resolve()),
            "purpose": "建议动作实跑清单 JSON。",
            "is_main": False,
            "type": "json",
        },
        {
            "name": markdown_path.name,
            "path": f"/storage/{relative_dir}/{markdown_path.name}",
            "file_path": str(markdown_path.resolve()),
            "purpose": "建议动作实跑摘要 Markdown。",
            "is_main": False,
            "type": "md",
        },
    ]
    return {
        "action_executions": execution_rows,
        "generated_tables": generated_tables,
        "downloadables": downloadables,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    provided = str(result.get("markdown") or "").strip()
    if provided:
        return provided + ("\n" if not provided.endswith("\n") else "")

    lines = [
        "# R 语言及智能解读",
        "",
        f"## {str(result.get('headline') or '').strip()}",
        "",
    ]
    for title, key in [
        ("Executive Summary", "executive_summary"),
        ("Artifact Usage", "artifact_usage"),
        ("Cross Artifact Findings", "cross_artifact_findings"),
        ("Evidence Boundaries", "evidence_boundaries"),
        ("Action Recommendations", "action_recommendations"),
    ]:
        items = [str(item).strip() for item in (result.get(key) or []) if str(item).strip()]
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        lines.extend([f"- {item}" for item in items])
        lines.append("")
    sheet_findings = result.get("sheet_findings") or []
    if sheet_findings:
        lines.extend(["## Sheet Findings", ""])
        for item in sheet_findings:
            lines.extend(
                [
                    f"### {str(item.get('sheet_name') or 'unknown')}",
                    "",
                    f"- 发现：{str(item.get('finding') or '').strip()}",
                    f"- 业务意义：{str(item.get('why_it_matters') or '').strip()}",
                    f"- 证据：{str(item.get('evidence') or '').strip()}",
                    "",
                ]
            )
    followup_execution = (result.get("followup_execution") or {}).get("action_executions") or []
    if followup_execution:
        lines.extend(["## 下一步修复建议与已实跑方法", ""])
        for item in followup_execution:
            lines.extend(
                [
                    f"### {str(item.get('action_index') or '')}. {str(item.get('action') or '').strip()}",
                    "",
                    f"- priority: {str(item.get('priority') or '').strip()}",
                    f"- why: {str(item.get('why') or '').strip()}",
                    f"- status: {str(item.get('status') or '').strip()}",
                    f"- executed_tables: {str(item.get('executed_tables') or '').strip() or 'none'}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _write_html(markdown_text: str, html_path: Path) -> None:
    html_body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>R Intelligence Flow</title>
  <style>
    body {{ font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 0; padding: 32px; background: #f6f2ea; color: #1f2430; }}
    main {{ max-width: 1080px; margin: 0 auto; background: white; border-radius: 20px; padding: 28px 32px; box-shadow: 0 12px 32px rgba(0,0,0,0.06); }}
    pre {{ white-space: pre-wrap; word-break: break-word; line-height: 1.8; font-family: inherit; }}
  </style>
</head>
<body>
  <main>
    <pre>{html.escape(markdown_text)}</pre>
  </main>
</body>
</html>"""
    _write_text(html_path, html_body)


def _write_pdf(markdown_text: str, pdf_path: Path) -> Path | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return None

    font_name = "Helvetica"
    for candidate in [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simsun.ttc"]:
        if Path(candidate).exists():
            try:
                font_name = "AsteriaCN"
                pdfmetrics.registerFont(TTFont(font_name, candidate))
                break
            except Exception:
                font_name = "Helvetica"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RIntelligenceTitle",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#1f2430"),
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "RIntelligenceBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#2f3742"),
    )
    story = [Paragraph("R 语言及智能解读", title_style), Spacer(1, 4 * mm)]
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 2 * mm))
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            story.append(Paragraph(html.escape(line[3:]), title_style))
        elif line.startswith("### "):
            story.append(Paragraph(html.escape(line[4:]), title_style))
        else:
            story.append(Paragraph(html.escape(line), body_style))
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    doc.build(story)
    return pdf_path


def _build_prompt_artifact(system_prompt: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R Artifact Intelligence Prompt",
            "",
            "## System Prompt",
            "",
            system_prompt,
            "",
            "## User Payload Snapshot",
            "",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "",
        ]
    )


def run_r_artifact_intelligence_flow(
    report_id: str,
    payload: RWorkflowIntelligenceRequest,
) -> dict[str, Any]:
    report_dir, workflow_dir = _resolve_r_workflow_dir(report_id)
    workbook_path = _find_required_artifact(workflow_dir, "*-r-statistics-summary.xlsx", "R statistics workbook")
    pdf_path = _find_required_artifact(workflow_dir, "*-r-interpretation.pdf", "R interpretation PDF")

    flow_dir = workflow_dir / "intelligence-flow"
    flow_dir.mkdir(parents=True, exist_ok=True)

    codex_payload = {
        "report_id": report_id,
        "workbook_name": workbook_path.name,
        "pdf_name": pdf_path.name,
        "focus_question": payload.focus_question,
        "target_audience": payload.target_audience,
        "output_goal": payload.output_goal,
        "local_artifact_paths": {
            "workbook_path": str(workbook_path.resolve()),
            "pdf_path": str(pdf_path.resolve()),
        },
    }
    artifact_access_mode = "direct_files"
    try:
        result = codex_interpret_r_artifact_bundle_from_files(
            codex_payload,
            workbook_path=workbook_path,
            pdf_path=pdf_path,
        )
    except Exception as exc:
        sheet_summaries = _read_excel_sheet_summaries(workbook_path)
        pdf_excerpt = _extract_pdf_text(pdf_path)
        summary_payload = {
            **codex_payload,
            **_build_business_context_pack(sheet_summaries, pdf_excerpt, workflow_dir=workflow_dir),
            "direct_file_failure": str(exc),
        }
        result = codex_interpret_r_artifact_bundle_from_summary(summary_payload)
        artifact_access_mode = "summary_pack"
    if not bool(result.get("live_available")) or str(result.get("runtime_state") or "") != "live":
        raise RuntimeError(
            "R 语言及智能解读新流要求必须使用 live Codex；"
            f"当前未成功调起 live Codex。fallback_reason={result.get('fallback_reason','unknown')}"
        )
    result["artifact_access_mode"] = artifact_access_mode

    followup_pack = _run_followup_execution_pack(
        workflow_dir=workflow_dir,
        flow_dir=flow_dir,
        result=result,
    )
    result["followup_execution"] = {
        "action_executions": followup_pack.get("action_executions", []),
        "generated_tables": followup_pack.get("generated_tables", []),
    }

    markdown_text = _render_markdown(result)
    prompt_source_payload = {
        **codex_payload,
        "artifact_access_mode": artifact_access_mode,
        "uploaded_files": result.get("uploaded_files") or [],
    }
    prompt_text = _build_prompt_artifact(build_r_artifact_intelligence_system_prompt(), prompt_source_payload)

    prompt_path = flow_dir / f"{report_id}-r-codex-intelligence-prompt.md"
    json_path = flow_dir / f"{report_id}-r-codex-intelligence.json"
    markdown_path = flow_dir / f"{report_id}-r-codex-intelligence.md"
    html_path = flow_dir / f"{report_id}-r-codex-intelligence.html"
    pdf_output_path = flow_dir / f"{report_id}-r-codex-intelligence.pdf"

    _write_text(prompt_path, prompt_text)
    _write_text(markdown_path, markdown_text)
    _write_text(html_path, "")
    _write_html(markdown_text, html_path)
    _write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))
    _write_pdf(markdown_text, pdf_output_path)

    relative_dir = flow_dir.relative_to(REPORTS_DIR.parent).as_posix()
    downloadables = [
        {
            "name": pdf_output_path.name,
            "path": f"/storage/{relative_dir}/{pdf_output_path.name}",
            "file_path": str(pdf_output_path.resolve()),
            "purpose": "R 语言及智能解读 PDF。",
            "is_main": True,
            "type": "pdf",
        },
        {
            "name": markdown_path.name,
            "path": f"/storage/{relative_dir}/{markdown_path.name}",
            "file_path": str(markdown_path.resolve()),
            "purpose": "R 语言及智能解读 Markdown。",
            "is_main": False,
            "type": "md",
        },
        {
            "name": html_path.name,
            "path": f"/storage/{relative_dir}/{html_path.name}",
            "file_path": str(html_path.resolve()),
            "purpose": "R 语言及智能解读 HTML。",
            "is_main": False,
            "type": "html",
        },
        {
            "name": json_path.name,
            "path": f"/storage/{relative_dir}/{json_path.name}",
            "file_path": str(json_path.resolve()),
            "purpose": "R 语言及智能解读 JSON。",
            "is_main": False,
            "type": "json",
        },
        {
            "name": prompt_path.name,
            "path": f"/storage/{relative_dir}/{prompt_path.name}",
            "file_path": str(prompt_path.resolve()),
            "purpose": "R 语言及智能解读详细 Prompt。",
            "is_main": False,
            "type": "md",
        },
        *followup_pack.get("downloadables", []),
    ]

    return {
        "flow_name": "r_language_intelligence_flow",
        "status": "completed",
        "report_id": report_id,
        "report_dir": str(report_dir.resolve()),
        "workflow_dir": str(workflow_dir.resolve()),
        "output_dir": str(flow_dir.resolve()),
        "source_workbook_path": str(workbook_path.resolve()),
        "source_pdf_path": str(pdf_path.resolve()),
        "headline": str(result.get("headline") or ""),
        "executive_summary": [str(item).strip() for item in (result.get("executive_summary") or []) if str(item).strip()],
        "downloadables": downloadables,
        "main_downloadable": downloadables[0],
    }
