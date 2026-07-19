from __future__ import annotations

import html
from typing import Any


class MissingStructuredPageDraftError(RuntimeError):
    pass


def _text(value: Any) -> str:
    return str(value or "").strip()


def _join(values: list[str], default: str = "无") -> str:
    cleaned = [_text(value) for value in values if _text(value)]
    return " / ".join(cleaned) if cleaned else default


def _table(title: str, rows: list[dict[str, Any]], note: str = "") -> dict[str, Any]:
    return {
        "title": title,
        "columns": list(rows[0].keys()) if rows else [],
        "rows": rows,
        "note": note,
    }


def _draft_lookup(page_drafts: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(item.get("page_number") or 0): item for item in page_drafts}


def _summary(report_mode: str, field_registry: dict[str, Any], registry_rows: list[dict[str, Any]]) -> list[str]:
    available = [str(item) for item in field_registry.get("available_field_groups") or []]
    missing = [str(item) for item in field_registry.get("missing_field_groups") or []]
    rows = registry_rows[:3]
    bullets = [
        f"本报告为 generic_long_business_report，当前按 `{report_mode}` 口径输出，适用于无法稳定归入采销、电商、互联网运营或媒体投放模板的数据集。",
        f"当前可判断内容主要来自：{', '.join(available[:6]) or '基础结构字段'}；当前不能判断内容主要来自：{', '.join(missing[:6]) or '无明显硬缺口'}。",
        "最重要的问题是：先识别主对象、异常对象与字段边界，再决定未来 7 天谁做什么、未来 30 天验证哪些改进假设。",
    ]
    if rows:
        bullets.append(
            "最值得优先复核的对象包括："
            + "；".join(
                f"{row.get('object_name') or row.get('object_id')}（{row.get('final_label')} / {row.get('final_action')}）"
                for row in rows
            )
        )
    bullets.append("本报告中的所有正式动作均来自 generic_object_decision_registry，不允许各章节自行写最终动作。")
    return bullets[:5]


def _action_summary(action: dict[str, Any]) -> str:
    return "；".join(
        [
            f"对象={_text(action.get('object'))}",
            f"触发指标={_text(action.get('trigger_metric'))}",
            f"当前值={_text(action.get('current_value'))}",
            f"阈值/比较={_text(action.get('threshold_or_comparison'))}",
            f"负责人={_text(action.get('owner_role'))}",
            f"动作={_text(action.get('action'))}",
            f"截止时间={_text(action.get('deadline'))}",
            f"验证指标={_text(action.get('verification_metric'))}",
        ]
    )


def _ensure_valid_drafts(page_plan: list[dict[str, Any]], page_drafts: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    if not (35 <= len(page_plan) <= 50):
        raise MissingStructuredPageDraftError(f"invalid_page_plan_count:{len(page_plan)}")
    draft_map = _draft_lookup(page_drafts)
    if len(draft_map) != len(page_plan):
        raise MissingStructuredPageDraftError(f"draft_count_mismatch:{len(draft_map)}!={len(page_plan)}")
    for page in page_plan:
        number = int(page.get("page_number") or 0)
        draft = draft_map.get(number)
        if not draft:
            raise MissingStructuredPageDraftError(number)
        required = ["diagnosis", "evidence", "business_interpretation", "recommended_action", "derived_metric_explanation", "ai_content_hash"]
        for key in required:
            if not draft.get(key):
                raise MissingStructuredPageDraftError(f"{number}:{key}")
    return draft_map


def build_generic_long_management_variant(report: dict[str, Any], chain_payload: dict[str, Any]) -> dict[str, Any] | None:
    if str(report.get("business_profile") or "") != "generic_long_business_report":
        return None

    field_registry = report.get("generic_field_availability_registry") or {}
    registry_payload = report.get("generic_object_decision_registry") or {}
    registry_rows = list(registry_payload.get("rows") or [])
    action_rows = list(report.get("generic_action_table") or [])
    roadmap_payload = report.get("generic_action_roadmap") or {}
    seven_day_rows = list(roadmap_payload.get("seven_day_action_table") or [])
    backlog_rows = list(roadmap_payload.get("thirty_day_improvement_backlog") or [])
    forbidden_rows = [row for row in (roadmap_payload.get("forbidden_judgement_rows") or []) if row]
    page_plan = list((chain_payload.get("long_report_page_plan") or {}).get("pages") or [])
    page_drafts = list(chain_payload.get("page_drafts") or [])

    if not field_registry:
        return None
    draft_map = _ensure_valid_drafts(page_plan, page_drafts)

    title = "《通用经营分析长报告：结构、效率、质量、进度与改进路线图复盘》"
    summary = _summary(str(field_registry.get("report_mode") or "generic_management_review"), field_registry, registry_rows)

    object_table_upper = _table("对象级行动表（上）", action_rows[:15], "对象级行动表必须来自 generic_object_decision_registry。")
    object_table_lower = _table("对象级行动表（下）", action_rows[15:30], "超过 30 行的对象动作继续进入附录。")
    seven_day_table = _table("7日动作表", seven_day_rows[:20], "每条动作必须带负责人、截止时间、验证标准与护栏指标。")
    backlog_table_upper = _table("30日改进 backlog（上）", backlog_rows[:12], "保留优先级更高的改进假设。")
    backlog_table_lower = _table("30日改进 backlog（下）", backlog_rows[12:24], "保留中期验证实验。")
    field_rows = (
        [{"字段组": group, "是否可用": "是"} for group in field_registry.get("available_field_groups") or []]
        + [{"字段组": group, "是否可用": "否"} for group in field_registry.get("missing_field_groups") or []]
    )
    data_gap_rows = [
        {
            "优先级": ("P0" if idx < 4 else "P1" if idx < 8 else "P2"),
            "缺失字段组": group,
            "为什么重要": "该字段组缺失会直接限制管理结论强度",
            "补齐后可判断": "补齐后可升级对象判断、趋势判断或财务判断",
        }
        for idx, group in enumerate(field_registry.get("missing_field_groups") or [])
    ]

    sections: list[dict[str, Any]] = []
    for page in page_plan:
        page_number = int(page["page_number"])
        draft = draft_map[page_number]
        title_text = _text(page.get("page_title"))
        evidence_rows = [
            {
                "metric_id": item.get("metric_id", ""),
                "metric_name": item.get("metric_name", ""),
                "value": item.get("value", ""),
                "comparison": item.get("comparison", ""),
                "object_or_dimension": item.get("object_or_dimension", ""),
                "evidence_strength": item.get("evidence_strength", ""),
            }
            for item in draft.get("evidence") or []
        ]
        tables = [_table("evidence_table", evidence_rows, "本页证据必须引用 metric_id。")]
        if "数据范围与字段可用性" in title_text:
            tables.append(_table("字段可用性", field_rows[:24], "所有结论都必须服从字段可用性边界。"))
        if "主对象识别" in title_text:
            tables.append(
                _table(
                    "主对象识别",
                    [
                        {
                            "对象层级": row.get("object_level", ""),
                            "对象名称": row.get("object_name") or row.get("object_id", ""),
                            "最终标签": row.get("final_label", ""),
                            "最终动作": row.get("final_action", ""),
                        }
                        for row in registry_rows[:10]
                    ],
                    "主对象识别用于确定全文拆解粒度。",
                )
            )
        if "重点对象复核表" in title_text:
            tables.append(_table("重点对象复核表", action_rows[:12], "列出最值得复核的对象、证据、缺失字段和复核动作。"))
        if "对象级行动表（上）" in title_text:
            tables.append(object_table_upper)
        if "对象级行动表（下）" in title_text:
            tables.append(object_table_lower)
        if "7日动作表" in title_text:
            tables.append(seven_day_table)
        if "30日改进 backlog（上）" in title_text:
            tables.append(backlog_table_upper)
        if "30日改进 backlog（下）" in title_text:
            tables.append(backlog_table_lower)
        if "禁止误判清单" in title_text:
            tables.append(_table("禁止误判清单", forbidden_rows[:15], "列出当前数据下不能得出的结论及原因。"))
        if "数据补充优先级" in title_text:
            tables.append(_table("数据补充优先级", data_gap_rows[:12], "按 P0/P1/P2 列出字段补充优先级。"))

        sections.append(
            {
                "id": f"generic_long_page_{page_number:03d}",
                "title": f"{page_number}. {title_text}",
                "summary": f"业务问题：{_text(draft.get('management_question') or page.get('management_question'))}",
                "bullets": [
                    f"管理问题：{_text(draft.get('management_question') or page.get('management_question'))}",
                    f"诊断判断：{_text(draft.get('diagnosis'))}",
                    f"指标推导：{_text(draft.get('derived_metric_explanation'))}",
                    f"业务解释：{_text(draft.get('business_interpretation'))}",
                    f"建议动作：{_action_summary(draft.get('recommended_action') or {})}",
                    f"数据边界：{_text(draft.get('data_limitations'))}",
                    f"禁止误读：{_join(list(draft.get('forbidden_misreadings') or []), default='无')}",
                    f"AI内容指纹：{_text(draft.get('ai_content_hash'))[:12]}",
                    f"来源链路：{_join(list(draft.get('source_passes') or []), default='generic_long_codex_chain')}",
                ],
                "tables": tables,
                "charts": [],
                "page_break_before": page_number > 1,
            }
        )

    return {
        "title": title,
        "dataset_name": report["dataset_name"],
        "sheet_name": report["sheet_name"],
        "report_id": report["report_id"],
        "generated_at": report["generated_at"],
        "report_language": report.get("report_language", "zh-CN"),
        "report_lens": report.get("report_lens", "mixed_business_review"),
        "business_profile": "generic_long_business_report",
        "executive_summary": summary,
        "sections": sections,
        "action_rows": action_rows,
        "field_registry": field_registry,
    }


def build_generic_long_appendix_variant(report: dict[str, Any], chain_payload: dict[str, Any]) -> dict[str, Any]:
    field_registry = report.get("generic_field_availability_registry") or {}
    registry_payload = report.get("generic_object_decision_registry") or {}
    registry_rows = list(registry_payload.get("rows") or [])
    semantic_map = chain_payload.get("field_semantic_map") or {}
    metric_plan = chain_payload.get("metric_derivation_plan") or {}
    metric_review = chain_payload.get("derived_metric_execution_review") or {}
    question_bank = (chain_payload.get("management_question_bank") or {}).get("questions") or []
    object_level = (chain_payload.get("object_level_interpretation") or {}).get("rows") or []
    page_plan = (chain_payload.get("long_report_page_plan") or {}).get("pages") or []
    sections = [
        {
            "id": "appendix_field_semantic_map",
            "title": "字段语义映射附录",
            "summary": "保留字段语义映射、人工确认风险和样例值。",
            "bullets": ["附录用于分析师复核字段语义和业务口径。"],
            "tables": [
                _table(
                    "field_semantic_map",
                    [
                        {
                            "字段": row.get("field_name", ""),
                            "业务含义": row.get("guessed_business_meaning", ""),
                            "指标类型": row.get("metric_type", ""),
                            "可用于": _join(list(row.get("usable_for") or []), default="无"),
                            "不可用于": _join(list(row.get("not_usable_for") or []), default="无"),
                            "需人工确认": "是" if row.get("needs_manual_confirmation") else "否",
                        }
                        for row in semantic_map.get("rows", [])
                    ],
                    "附录保留更完整的字段语义细节。",
                )
            ],
            "charts": [],
        },
        {
            "id": "appendix_metric_derivation",
            "title": "派生指标附录",
            "summary": "保留 metric_derivation_plan 和 derived_metric_execution_review。",
            "bullets": ["每个指标都带 metric_id，后续页面和证据表必须引用它。"],
            "tables": [
                _table("metric_derivation_plan", metric_plan.get("metrics", [])),
                _table("derived_metric_execution_review", metric_review.get("metrics", [])),
            ],
            "charts": [],
        },
        {
            "id": "appendix_object_registry",
            "title": "对象级注册表附录",
            "summary": "保留完整 generic_object_decision_registry 与对象解释。",
            "bullets": ["所有最终动作仍然只读取 generic_object_decision_registry。"],
            "tables": [
                _table(
                    "generic_object_decision_registry",
                    [
                        {
                            "对象层级": row.get("object_level", ""),
                            "对象名称": row.get("object_name") or row.get("object_id", ""),
                            "最终标签": row.get("final_label", ""),
                            "最终动作": row.get("final_action", ""),
                            "缺失字段": _join(list(row.get("missing_fields") or []), default="无"),
                            "结论类型": row.get("conclusion_type", ""),
                            "置信度": row.get("confidence_level", ""),
                        }
                        for row in registry_rows
                    ],
                    "对象动作和结论强度都在这里收口。",
                ),
                _table("object_level_interpretation", object_level),
            ],
            "charts": [],
        },
        {
            "id": "appendix_question_bank",
            "title": "问题库与页面规划附录",
            "summary": "保留 20 个管理问题与 35-50 页 PageSpec 规划。",
            "bullets": ["用于证明每个核心章节都可追溯到 AI 解释链。"],
            "tables": [
                _table("management_question_bank", question_bank),
                _table("long_report_page_plan", page_plan),
            ],
            "charts": [],
        },
    ]
    return {
        "title": f"{report['title']}（analyst_appendix）",
        "dataset_name": report["dataset_name"],
        "sheet_name": report["sheet_name"],
        "report_id": report["report_id"],
        "generated_at": report["generated_at"],
        "report_language": report.get("report_language", "zh-CN"),
        "report_lens": report.get("report_lens", "mixed_business_review"),
        "business_profile": "generic_long_business_report",
        "executive_summary": ["本附录保留 generic_long 多轮解读链的字段语义、派生指标、问题库、对象解释和页面规划明细。"],
        "sections": sections,
    }


def render_generic_long_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report.get('title', 'Generic Long Report')}",
        "",
        f"- 数据集：`{report.get('dataset_name', '')}`",
        f"- 工作表：`{report.get('sheet_name', '')}`",
        f"- 报告语言：`{report.get('report_language', 'zh-CN')}`",
        f"- 生成时间：`{report.get('generated_at', '')}`",
        "",
        "## 管理层摘要",
        "",
    ]
    for bullet in report.get("executive_summary", []) or []:
        lines.append(f"- {bullet}")
    lines.extend(["", "## 管理层正文", ""])
    for section in report.get("sections", []) or []:
        lines.extend(["", f"## {section.get('title', '')}", "", str(section.get("summary", "")), ""])
        for bullet in section.get("bullets", []) or []:
            lines.append(f"- {bullet}")
        for table in section.get("tables", []) or []:
            columns = list(table.get("columns") or [])
            rows = list(table.get("rows") or [])
            if not columns:
                continue
            lines.extend(["", f"### {table.get('title', 'table')}", ""])
            lines.append("| " + " | ".join(columns) + " |")
            lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
            for row in rows:
                lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
            note = str(table.get("note") or "").strip()
            if note:
                lines.extend(["", note])
    return "\n".join(lines).strip() + "\n"


def render_generic_long_html(report: dict[str, Any]) -> str:
    sections_html: list[str] = []
    for section in report.get("sections", []) or []:
        bullets = "".join(f"<li>{html.escape(str(item))}</li>" for item in (section.get("bullets") or []))
        table_html = []
        for table in section.get("tables", []) or []:
            columns = list(table.get("columns") or [])
            rows = list(table.get("rows") or [])
            if not columns:
                continue
            header = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
            body = []
            for row in rows:
                body.append("<tr>" + "".join(f"<td>{html.escape(str(row.get(column, '')))}</td>" for column in columns) + "</tr>")
            note = str(table.get("note") or "").strip()
            note_html = f"<p class='table-note'>{html.escape(note)}</p>" if note else ""
            table_html.append(
                f"<div class='table-block'><h3>{html.escape(str(table.get('title', 'table')))}</h3><table><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table>{note_html}</div>"
            )
        sections_html.append(
            f"<section id='{html.escape(str(section.get('id', 'section')))}'>"
            f"<h2>{html.escape(str(section.get('title', '')))}</h2>"
            f"<p>{html.escape(str(section.get('summary', '')))}</p>"
            f"<ul>{bullets}</ul>"
            f"{''.join(table_html)}"
            f"</section>"
        )

    summary_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in (report.get("executive_summary") or []))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(str(report.get('title', 'Generic Long Report')))}</title>
  <style>
    body {{ font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 0; padding: 32px; background: #f6f3ee; color: #1f2430; }}
    main {{ max-width: 1080px; margin: 0 auto; }}
    section {{ background: white; border-radius: 18px; padding: 20px 22px; margin-top: 18px; box-shadow: 0 10px 28px rgba(0,0,0,0.06); }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    ul {{ margin: 0; padding-left: 18px; line-height: 1.7; }}
    .meta {{ color: #5b6573; line-height: 1.8; }}
    .section-label {{ margin-top: 28px; color: #5b6573; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 14px; }}
    th, td {{ border: 1px solid #d8dee8; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f6fb; }}
    .table-note {{ margin: 8px 0 0; color: #5b6573; font-size: 13px; line-height: 1.7; }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(str(report.get('title', 'Generic Long Report')))}</h1>
    <p class="meta">数据集：{html.escape(str(report.get('dataset_name', '')))} / 工作表：{html.escape(str(report.get('sheet_name', '')))}</p>
    <section>
      <h2>管理层摘要</h2>
      <ul>{summary_html}</ul>
    </section>
    <div class="section-label">管理层正文</div>
    {''.join(sections_html)}
  </main>
</body>
</html>"""
