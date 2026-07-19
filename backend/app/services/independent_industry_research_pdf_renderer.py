from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path
from typing import Any


FORBIDDEN_MAIN_REPORT_TOKENS = (
    "object_decision_registry",
    "final_label",
    "final_action",
    "行动表",
    "主报告对象",
    "management_report",
)

FORBIDDEN_R_TOKENS = (
    "R workflow",
    "R 工作流",
    "r_cleaned_data",
    "r_analysis_outputs",
    "r_visualization_outputs",
    "r_pdf_explanation",
)

FORBIDDEN_COMPLETION_TOKENS = (
    "完成主报告分析",
    "完成统计建模",
    "当前数据证明",
    "当前数据表明",
    "当前数据说明",
)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _parse_markdown_sections(report_markdown: str) -> tuple[str, list[dict[str, Any]]]:
    title = "行业研究报告"
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in report_markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("# "):
            title = line[2:].strip() or title
            continue
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = {"title": line[3:].strip(), "bullets": []}
            continue
        if current is None:
            continue
        if line.startswith("- "):
            current["bullets"].append(line[2:].strip())
        elif line.startswith("> "):
            current["bullets"].append(line[2:].strip())
        elif line.strip():
            current["bullets"].append(line.strip())
    if current:
        sections.append(current)
    return title, sections


def _claim_rows(citation_manifest: Any) -> list[dict[str, Any]]:
    if isinstance(citation_manifest, dict):
        if isinstance(citation_manifest.get("citations"), list):
            return list(citation_manifest["citations"])
        return []
    if isinstance(citation_manifest, list):
        return list(citation_manifest)
    return []


def _page_source_rows(claim_rows: list[dict[str, Any]], page_number: int, section_title: str) -> list[dict[str, Any]]:
    rows = []
    for row in claim_rows:
        if int(row.get("used_in_page") or 0) == page_number or _safe_text(row.get("used_in_section")) == section_title:
            rows.append(row)
    return rows


def _boundary_note(section_title: str) -> str:
    mapping = {
        "封面": "本报告是独立行研，不替代主报告，不输出当前数据经营结论。",
        "研究范围": "范围只限行业背景、平台机制、竞品参考、指标口径与 benchmark 边界。",
        "研究问题": "研究问题只服务行业理解，不直接生成主报告动作。",
        "行业背景": "外部资料只能解释行业背景，不得证明当前对象表现。",
        "市场结构": "市场结构只能作行业框架，不得替代当前数据中的经营结构结论。",
        "产业链与价值链": "价值链分析只用于业务理解，不得生成对象级决策。",
        "平台机制或渠道机制": "平台机制只用于解释规则与约束，不作为当前经营拍板证据。",
        "竞争格局": "竞品参考只给背景线索，不伪装成当前数据事实。",
        "用户/消费者趋势": "用户趋势只作外部参考，不能直接证明当前用户行为结果。",
        "商品/服务供给结构": "供给结构只作行业框架，不改变主报告对象标签。",
        "成本、利润与商业模式": "商业模式说明不能替代当前数据中的利润与 ROI 分析。",
        "指标口径": "口径说明只解释定义和可比边界，不替代上传数据分析。",
        "benchmark 与可比性限制": "benchmark 必须写清不可比说明、时间边界和平台差异。",
        "外部风险": "外部风险只用于行业研究背景，不替代当前经营风险判定。",
        "对主报告的背景启发": "这里只能提出背景启发，不得声称已完成主报告分析。",
        "资料来源与附录": "来源只用于行研链，不得进入主报告 object/action 决策证据。",
    }
    for key, value in mapping.items():
        if key in section_title:
            return value
    return "本页只用于行业研究背景说明，不替代当前数据分析。"


def _build_appendix(
    *,
    output_dir: Path,
    sources_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    scope_payload: dict[str, Any],
) -> str:
    question_bank_path = output_dir / "industry_research_question_bank.md"
    search_plan_path = output_dir / "industry_web_search_plan.md"
    question_text = _read_text(question_bank_path)
    search_text = _read_text(search_plan_path)
    used_source_ids = {str(row.get("source_id") or "") for row in claim_rows}
    unused_sources = [row for row in sources_rows if str(row.get("source_id") or "") not in used_source_ids]
    benchmark_limits = [
        "benchmark 只用于外部参考，不直接替代当前上传数据结果。",
        "benchmark 比较必须写清平台差异、样本边界、时间区间和指标口径。",
        "没有可比来源时只能输出不可比说明。",
    ]
    unsupported = list(scope_payload.get("unsupported_questions") or [])

    lines = [
        "# industry_research_appendix",
        "",
        "## 搜索问题",
        "",
        question_text.strip() or "- 无",
        "",
        "## 使用来源",
        "",
    ]
    for row in sources_rows:
        if str(row.get("source_id") or "") in used_source_ids:
            lines.extend(
                [
                    f"- {row.get('source_id')} {row.get('title')} / {row.get('publisher')}",
                    f"  - 来源评级：{row.get('credibility_level')}",
                    f"  - 使用位置：{', '.join(sorted(set(_safe_text(item.get('used_in_section')) for item in claim_rows if _safe_text(item.get('source_id')) == _safe_text(row.get('source_id')))))}",
                ]
            )
    lines.extend(["", "## 未采用来源", ""])
    if unused_sources:
        for row in unused_sources:
            lines.extend(
                [
                    f"- {row.get('source_id')} {row.get('title')}",
                    f"  - 未采用原因：来源未进入当前 claim manifest 或只作为线索。",
                ]
            )
    else:
        lines.append("- 无")
    lines.extend(["", "## benchmark 限制", "", *[f"- {item}" for item in benchmark_limits]])
    lines.extend(["", "## 当前资料无法支持的判断", "", *[f"- {item}" for item in unsupported]])
    lines.extend(["", "## 搜索计划摘要", "", search_text.strip() or "- 无"])
    return "\n".join(lines).strip() + "\n"


def _render_html(title: str, pages: list[dict[str, Any]]) -> str:
    sections = []
    for page in pages:
        source_html = "".join(
            f"<li>{html.escape(_safe_text(row.get('source_id')))} / {html.escape(_safe_text(row.get('source_title')))} / {html.escape(_safe_text(row.get('publisher')))}</li>"
            for row in page["sources"]
        )
        bullet_html = "".join(f"<li>{html.escape(item)}</li>" for item in page["bullets"])
        sections.append(
            f"""
            <section class="card">
              <h2>{html.escape(page['page_title'])}</h2>
              <p><strong>主题：</strong>{html.escape(page['theme'])}</p>
              <ul>{bullet_html}</ul>
              <p><strong>边界说明：</strong>{html.escape(page['boundary_note'])}</p>
              <p><strong>来源说明：</strong></p>
              <ul>{source_html or '<li>本页以边界说明为主，不额外引入外部事实。</li>'}</ul>
            </section>
            """
        )
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <title>{html.escape(title)}</title>
        <style>
          body {{
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: #0b1015;
            color: #f4efe8;
            margin: 0;
            padding: 32px;
          }}
          .card {{
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
            background: rgba(255,255,255,0.04);
          }}
          li {{ line-height: 1.8; }}
        </style>
      </head>
      <body>
        <h1>{html.escape(title)}</h1>
        {''.join(sections)}
      </body>
    </html>
    """


def _render_pdf(path: Path, title: str, pages: list[dict[str, Any]]) -> Path | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return None

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("IndustryPdfTitle", parent=styles["Heading1"], fontSize=18, leading=24, textColor=colors.HexColor("#222"))
    page_style = ParagraphStyle("IndustryPdfSection", parent=styles["Heading2"], fontSize=13, leading=18, textColor=colors.HexColor("#222"))
    body_style = ParagraphStyle("IndustryPdfBody", parent=styles["BodyText"], fontSize=9, leading=14, textColor=colors.HexColor("#444"))

    story: list[Any] = [Paragraph(html.escape(title), title_style), Spacer(1, 4 * mm)]
    for idx, page in enumerate(pages, start=1):
        if idx > 1:
            story.append(PageBreak())
        story.append(Paragraph(html.escape(page["page_title"]), page_style))
        story.append(Paragraph(html.escape(f"主题：{page['theme']}"), body_style))
        for item in page["bullets"]:
            story.append(Paragraph(html.escape(item), body_style))
        story.append(Paragraph(html.escape(f"边界说明：{page['boundary_note']}"), body_style))
        if page["sources"]:
            story.append(Paragraph("来源说明：", body_style))
            for row in page["sources"]:
                source_text = f"{_safe_text(row.get('source_id'))} / {_safe_text(row.get('source_title'))} / {_safe_text(row.get('publisher'))}"
                story.append(Paragraph(html.escape(source_text), body_style))
        else:
            story.append(Paragraph("来源说明：本页以边界说明为主，不额外引入外部事实。", body_style))
        story.append(Spacer(1, 2 * mm))

    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=16 * mm, bottomMargin=14 * mm)
    doc.build(story)
    return path


def _build_pages(
    *,
    title: str,
    report_sections: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    scope_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    cover_page = {
        "page_number": 1,
        "page_title": "封面",
        "theme": title,
        "bullets": [
            f"研究范围：{scope_payload.get('inferred_industry', '')} / {scope_payload.get('inferred_platform', '')}",
            f"目标读者：{scope_payload.get('target_reader', '')}",
        ],
        "sources": [],
        "boundary_note": "本报告为独立行业研究报告，不替代主报告，不输出当前数据经营结论。",
    }
    pages = [cover_page]
    for index, section in enumerate(report_sections, start=2):
        section_title = _safe_text(section.get("title"))
        sources = _page_source_rows(claim_rows, index, section_title)
        pages.append(
            {
                "page_number": index,
                "page_title": section_title,
                "theme": section_title,
                "bullets": list(section.get("bullets") or [])[:10],
                "sources": sources,
                "boundary_note": _boundary_note(section_title),
            }
        )
    return pages


def _audit_rows(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_content: set[str] = set()
    for page in pages:
        combined_text = " ".join(page["bullets"])
        has_source = bool(page["sources"])
        has_boundary = bool(_safe_text(page["boundary_note"]))
        specific_content = any(
            token in combined_text or token in page["page_title"] or token in page["theme"]
            for token in [
                "行业",
                "平台",
                "竞品",
                "benchmark",
                "用户",
                "消费者",
                "供给",
                "风险",
                "口径",
                "背景",
                "价值链",
                "市场",
                "成本",
                "利润",
                "来源",
                "附录",
                "封面",
            ]
        )
        has_unsupported_dataset_claim = any(token in combined_text for token in FORBIDDEN_COMPLETION_TOKENS)
        has_main_report_content = any(token in combined_text or token in page["page_title"] for token in FORBIDDEN_MAIN_REPORT_TOKENS)
        has_r_workflow_content = any(token in combined_text or token in page["boundary_note"] for token in FORBIDDEN_R_TOKENS)
        duplicate_page = combined_text in seen_content and bool(combined_text)
        seen_content.add(combined_text)
        passed = (has_source or has_boundary) and specific_content and not has_unsupported_dataset_claim and not has_main_report_content and not has_r_workflow_content and not duplicate_page
        issue_parts = []
        if not has_source and not has_boundary:
            issue_parts.append("missing_source_or_boundary")
        if not specific_content:
            issue_parts.append("weak_industry_content")
        if has_unsupported_dataset_claim:
            issue_parts.append("unsupported_dataset_claim")
        if has_main_report_content:
            issue_parts.append("main_report_content")
        if has_r_workflow_content:
            issue_parts.append("r_workflow_content")
        if duplicate_page:
            issue_parts.append("duplicate_page")
        rows.append(
            {
                "page_number": page["page_number"],
                "page_title": page["page_title"],
                "has_source": has_source,
                "has_boundary_note": has_boundary,
                "has_specific_industry_content": specific_content,
                "has_unsupported_dataset_claim": has_unsupported_dataset_claim,
                "has_main_report_content": has_main_report_content,
                "has_r_workflow_content": has_r_workflow_content,
                "passed": passed,
                "issue": ";".join(issue_parts),
            }
        )
    return rows


def render_independent_industry_research_pdf_bundle(output_dir: str | Path) -> dict[str, Any]:
    out_dir = Path(output_dir)
    report_md_path = out_dir / "industry_research_report.md"
    sources_path = out_dir / "industry_research_sources.json"
    citation_path = out_dir / "citation_manifest_industry.json"
    scope_path = out_dir / "industry_research_scope.json"
    html_path = out_dir / "industry_research_report.html"
    pdf_path = out_dir / "industry_research_report.pdf"
    appendix_path = out_dir / "industry_research_appendix.md"
    page_audit_path = out_dir / "industry_research_page_audit.csv"

    report_markdown = _read_text(report_md_path)
    title, report_sections = _parse_markdown_sections(report_markdown)
    if "行业研究报告" not in title:
        title = f"行业研究报告：{title}"
    sources_payload = _read_json(sources_path) if sources_path.exists() else {"sources": []}
    sources_rows = list(sources_payload.get("sources") or [])
    citation_payload = _read_json(citation_path) if citation_path.exists() else {"citations": []}
    claim_rows = _claim_rows(citation_payload)
    scope_payload = _read_json(scope_path) if scope_path.exists() else {}

    pages = _build_pages(
        title=title,
        report_sections=report_sections,
        claim_rows=claim_rows,
        scope_payload=scope_payload,
    )
    appendix_text = _build_appendix(
        output_dir=out_dir,
        sources_rows=sources_rows,
        claim_rows=claim_rows,
        scope_payload=scope_payload,
    )
    appendix_path.write_text(appendix_text, encoding="utf-8")
    html_path.write_text(_render_html(title, pages), encoding="utf-8")
    _render_pdf(pdf_path, title, pages)
    audit_rows = _audit_rows(pages)
    with page_audit_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0].keys()) if audit_rows else [
            "page_number",
            "page_title",
            "has_source",
            "has_boundary_note",
            "has_specific_industry_content",
            "has_unsupported_dataset_claim",
            "has_main_report_content",
            "has_r_workflow_content",
            "passed",
            "issue",
        ])
        writer.writeheader()
        if audit_rows:
            writer.writerows(audit_rows)

    return {
        "title": title,
        "page_count": len(pages),
        "html_path": str(html_path.resolve()),
        "pdf_path": str(pdf_path.resolve()) if pdf_path.exists() else "",
        "appendix_path": str(appendix_path.resolve()),
        "page_audit_path": str(page_audit_path.resolve()),
        "audit_rows": audit_rows,
    }
