from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from app.services.codex_historical_localization_service import (
    localize_historical_record,
    localize_historical_text,
)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _pd() -> Any:
    import pandas as pd

    return pd


def _metric_candidates(frame: Any) -> list[tuple[str, str]]:
    preferred = [
        ("revenue", "sum"),
        ("contribution_margin", "sum"),
        ("operating_cost", "sum"),
        ("paid_users", "sum"),
        ("orders", "sum"),
        ("registrations", "sum"),
        ("activations", "sum"),
        ("clicks", "sum"),
        ("impressions", "sum"),
        ("roi", "mean"),
        ("retention_d7", "mean"),
        ("retention_d30", "mean"),
        ("nps", "mean"),
        ("cac", "mean"),
    ]
    existing = []
    columns = {str(col).strip(): col for col in frame.columns}
    for name, agg in preferred:
        if name in columns:
            existing.append((name, agg))
    return existing


def _dimension_candidates(frame: Any) -> list[str]:
    pd = _pd()
    priority_tokens = [
        "channel",
        "traffic_source",
        "user_segment",
        "region",
        "city",
        "tier",
        "campaign",
        "product",
        "module",
        "category",
        "brand",
        "source",
    ]
    candidates: list[str] = []
    for column in frame.columns:
        name = str(column).strip()
        if not name:
            continue
        unique_count = int(frame[column].nunique(dropna=True))
        if unique_count < 2 or unique_count > 40:
            continue
        if any(token in name.lower() for token in priority_tokens):
            candidates.append(name)
    if candidates:
        return candidates[:6]
    fallback: list[str] = []
    for column in frame.columns:
        name = str(column).strip()
        if not name:
            continue
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
            continue
        unique_count = int(series.nunique(dropna=True))
        if 2 <= unique_count <= 20:
            fallback.append(name)
    return fallback[:6]


def _format_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            if abs(value) <= 1 and abs(value) > 0:
                return f"{value:.2%}"
            return f"{value:,.2f}".rstrip("0").rstrip(".")
        return f"{value:,}"
    return localize_historical_text(value)


def _share_is_reader_meaningful(row: dict[str, Any]) -> bool:
    semantics = str(row.get("share_semantics") or "").strip()
    share = row.get("share_of_total")
    if semantics and semantics != "contribution_share":
        return False
    try:
        share_value = float(share)
    except Exception:
        return False
    return share_value > 1e-9


def _drop_unmeaningful_share(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(row)
    if "share_of_total" in cleaned and not _share_is_reader_meaningful(cleaned):
        cleaned.pop("share_of_total", None)
    cleaned.pop("share_semantics", None)
    return cleaned


def _share_column_has_reader_value(rows: list[dict[str, Any]], header: str) -> bool:
    if "占比" not in str(header) and "share" not in str(header).lower():
        return True
    for row in rows:
        value = row.get(header)
        if value in (None, ""):
            continue
        try:
            if abs(float(value)) > 1e-9:
                return True
        except Exception:
            return True
    return False


def _display_title(value: Any) -> str:
    raw = str(value or "").strip()
    mapping = {
        "KPI Snapshot": "核心 KPI 快照",
        "Derived Metric Matrix": "派生指标矩阵",
        "Dimension Signal Matrix": "维度信号矩阵",
        "Priority Action Table": "优先行动表",
        "Correlation Focus": "相关关系重点表",
        "Metric & Dimension Glossary": "指标与维度口径表",
        "Appendix Detail Table": "附录明细表",
        "Segment Scorecards": "细分对象评分卡",
        "Cross-Dimension Priority Matrix": "交叉维度优先级矩阵",
    }
    return mapping.get(raw, localize_historical_text(raw, fallback=raw))


def _display_header(value: Any) -> str:
    raw = str(value or "").strip()
    mapping = {
        "dimension": "维度",
        "rank": "排名",
        "segment": "分层对象",
        "signal_pack": "关键信号",
        "metric": "指标",
        "value": "数值",
        "dtype": "字段类型",
        "column": "字段",
        "missing_ratio": "缺失率",
        "unique_count": "唯一值数",
        "top_values": "高频值",
        "priority_zone": "优先区域",
        "current_signal": "当前信号",
        "management_question": "管理问题",
        "action_lens": "行动视角",
        "top_segment": "头部分层",
        "top_value": "头部数值",
        "bottom_segment": "尾部分层",
        "bottom_value": "尾部数值",
        "top_分层": "头部分层",
        "top_数值": "头部数值",
        "bottom_分层": "尾部分层",
        "bottom_数值": "尾部数值",
        "metric_raw_key": "原始指标",
        "dimension_raw_key": "维度原始字段",
        "dimension_localized_label": "维度",
        "segment_raw_value": "分层原始值",
        "segment_localized_label": "分层对象",
        "metric_localized_label": "指标",
        "scorecard_id": "评分卡",
        "share_of_total": "总量占比",
        "lift_vs_overall": "相对整体",
        "management_signal": "管理信号",
        "formula": "公式",
        "status": "状态",
        "interpretation": "解释",
    }
    if raw in mapping:
        return mapping[raw]
    localized = localize_historical_text(raw, fallback=raw)
    return localized.replace("top_", "头部").replace("bottom_", "尾部")


def _compact_segment_scorecard_rows(rows: list[dict[str, Any]], *, limit: int = 18) -> list[dict[str, Any]]:
    compact_rows: list[dict[str, Any]] = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue
        compact_rows.append(
            {
                "维度": localize_historical_text(row.get("dimension_localized_label") or row.get("dimension_raw_key") or ""),
                "分层对象": localize_historical_text(row.get("segment_localized_label") or row.get("segment_raw_value") or ""),
                "指标": localize_historical_text(row.get("metric_localized_label") or row.get("metric_raw_key") or ""),
                "当前值": row.get("value"),
                "总量占比": row.get("share_of_total"),
                "相对整体": row.get("lift_vs_overall"),
                "排名": row.get("rank"),
                "管理信号": localize_historical_text(row.get("management_signal") or ""),
            }
        )
    return compact_rows


def _compact_cross_dimension_rows(rows: list[dict[str, Any]], *, limit: int = 18) -> list[dict[str, Any]]:
    compact_rows: list[dict[str, Any]] = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue
        dimension_a = localize_historical_text(row.get("dimension_a_label") or row.get("dimension_a") or "")
        dimension_b = localize_historical_text(row.get("dimension_b_label") or row.get("dimension_b") or "")
        value_a = localize_historical_text(row.get("dimension_a_value_label") or row.get("dimension_a_value_raw") or "")
        value_b = localize_historical_text(row.get("dimension_b_value_label") or row.get("dimension_b_value_raw") or "")
        compact_rows.append(
            {
                "维度组合": f"{dimension_a} × {dimension_b}".strip(" ×"),
                "对象组合": f"{value_a} × {value_b}".strip(" ×"),
                "指标": localize_historical_text(row.get("metric_label") or row.get("metric") or ""),
                "当前值": row.get("value"),
                "总量占比": row.get("share_of_total"),
                "相对整体": row.get("lift_vs_overall"),
                "优先区域": localize_historical_text(row.get("priority_zone") or ""),
                "样本数": row.get("n"),
                "排名": row.get("rank"),
            }
        )
    return compact_rows


def _safe_id(value: Any, *, fallback: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value or "").strip()).strip("_")
    return text[:60] or fallback


def _asset_metadata(
    path: Path,
    *,
    table_id: str,
    title: str,
    role: str,
    insight_input: dict[str, Any] | None = None,
    story_role: str = "",
    management_use: str = "",
) -> dict[str, Any]:
    return {
        "table_id": table_id,
        "asset_type": "table",
        "kind": "table",
        "title": localize_historical_text(title, fallback=title),
        "file_name": path.name,
        "path": str(path.resolve()),
        "recommended_page_role": role,
        "insight_input": dict(insight_input or {}),
        "story_role": story_role or role,
        "management_use": management_use,
    }


def _records_from_frame(frame: Any, *, limit: int = 8) -> list[dict[str, Any]]:
    records = frame.head(limit).to_dict(orient="records")
    return [{str(key): value for key, value in row.items()} for row in records]


def _build_dimension_matrix_rows(ranking_tables: list[dict[str, Any]], *, limit: int = 12) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for table in ranking_tables:
        if not isinstance(table, dict):
            continue
        dimension = str(table.get("dimension") or "dimension")
        for rank, row in enumerate(list(table.get("rows") or [])[:3], start=1):
            if not isinstance(row, dict):
                continue
            label = row.get(dimension)
            if label is None:
                label = next(iter(row.values()), "")
            metric_values = [
                f"{key}: {_format_scalar(value)}"
                for key, value in list(row.items())[:5]
                if str(key) != dimension
            ]
            rows.append(
                {
                    "dimension": dimension,
                    "rank": rank,
                    "segment": label,
                    "signal_pack": " / ".join(metric_values[:3]),
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def _build_priority_action_rows(
    kpi_rows: list[dict[str, Any]],
    ranking_tables: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in kpi_rows[:5]:
        metric_name = str(item.get("metric") or "该指标")
        rows.append(
            {
                "priority_zone": metric_name,
                "current_signal": _format_scalar(item.get("value")),
                "management_question": f"{metric_name} 当前由哪个分层对象贡献或拖累？",
                "action_lens": "按分层、趋势和贡献度拆解，并明确责任对象",
            }
        )
    for item in correlation_rows[:4]:
        rows.append(
            {
                "priority_zone": f"{item.get('left')} x {item.get('right')}",
                "current_signal": _format_scalar(item.get("correlation")),
                "management_question": "这组关系是可控经营杠杆，还是共同结果变量？",
                "action_lens": "先按分层复核，再隔离可控驱动项",
            }
        )
    for table in ranking_tables[:3]:
        dimension = str(table.get("dimension") or "dimension")
        rows.append(
            {
                "priority_zone": dimension,
                "current_signal": f"{len(list(table.get('rows') or []))} 个分层对象已排序",
                "management_question": f"{dimension} 中哪些头部/尾部对象需要差异化动作？",
                "action_lens": "头尾分层、预算转移和异常复盘",
            }
        )
    return rows[:limit]


def _build_appendix_detail_rows(ranking_tables: list[dict[str, Any]], glossary_rows: list[dict[str, Any]], *, limit: int = 18) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for table in ranking_tables:
        dimension = str(table.get("dimension") or "dimension")
        for row in list(table.get("rows") or [])[:3]:
            if not isinstance(row, dict):
                continue
            compact = dict(list(row.items())[:5])
            compact["source_dimension"] = dimension
            rows.append(compact)
            if len(rows) >= limit:
                return rows
    for row in glossary_rows[:limit]:
        if isinstance(row, dict):
            rows.append(dict(row))
    return rows[:limit]


def build_historical_support_tables(
    frame: Any,
    *,
    chart_bundle: dict[str, Any] | None = None,
    column_summaries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    pd = _pd()
    metrics = _metric_candidates(frame)
    dimensions = _dimension_candidates(frame)
    kpi_rows: list[dict[str, Any]] = []
    for metric_name, agg in metrics[:10]:
        series = pd.to_numeric(frame[metric_name], errors="coerce")
        if agg == "sum":
            value = float(series.fillna(0).sum())
        else:
            value = float(series.dropna().mean()) if not series.dropna().empty else 0.0
        kpi_rows.append({"metric": metric_name, "aggregation": agg, "value": value})

    ranking_tables: list[dict[str, Any]] = []
    metric_aggs = {name: agg for name, agg in metrics[:6]}
    for dimension in dimensions:
        group_frame = frame.copy()
        group_frame[dimension] = group_frame[dimension].fillna("Missing").astype(str)
        agg_map: dict[str, Any] = {"row_count": (dimension, "count")}
        for metric_name, agg in metric_aggs.items():
            if agg == "sum":
                agg_map[metric_name] = (metric_name, "sum")
            else:
                agg_map[metric_name] = (metric_name, "mean")
        grouped = (
            group_frame.groupby(dimension, dropna=False)
            .agg(**agg_map)
            .reset_index()
            .sort_values(metric_aggs.keys().__iter__().__next__() if metric_aggs else "row_count", ascending=False)
            .head(10)
        )
        ranking_tables.append(
            {
                "dimension": dimension,
                "rows": _records_from_frame(grouped, limit=10),
            }
        )

    correlation_rows: list[dict[str, Any]] = []
    correlation = (chart_bundle or {}).get("correlation") or {}
    labels = list(correlation.get("labels") or [])
    matrix = list(correlation.get("matrix") or [])
    for left_index, left in enumerate(labels):
        for right_index, right in enumerate(labels):
            if right_index <= left_index:
                continue
            try:
                value = float(matrix[left_index][right_index])
            except Exception:
                continue
            correlation_rows.append(
                {
                    "left": str(left),
                    "right": str(right),
                    "correlation": value,
                    "abs_correlation": abs(value),
                }
            )
    correlation_rows.sort(key=lambda item: item["abs_correlation"], reverse=True)

    glossary_rows: list[dict[str, Any]] = []
    for item in list(column_summaries or [])[:24]:
        if not isinstance(item, dict):
            continue
        top_values = []
        stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
        for entry in list(stats.get("top_values") or [])[:3]:
            if not isinstance(entry, dict):
                continue
            label = str(entry.get("label") or "").strip()
            count = entry.get("count")
            if label:
                top_values.append(f"{label} ({count})" if count is not None else label)
        glossary_rows.append(
            {
                "column": str(item.get("name") or ""),
                "dtype": str(item.get("dtype") or ""),
                "missing_ratio": item.get("missing_ratio"),
                "unique_count": item.get("unique_count"),
                "top_values": " / ".join(top_values),
            }
        )

    dimension_matrix_rows = _build_dimension_matrix_rows(ranking_tables)
    priority_action_rows = _build_priority_action_rows(kpi_rows, ranking_tables, correlation_rows)
    appendix_detail_rows = _build_appendix_detail_rows(ranking_tables, glossary_rows)

    return {
        "kpi_snapshot": kpi_rows,
        "ranking_tables": ranking_tables,
        "correlation_focus": correlation_rows[:12],
        "glossary_rows": glossary_rows,
        "dimension_matrix": dimension_matrix_rows,
        "priority_action_table": priority_action_rows,
        "appendix_detail_rows": appendix_detail_rows,
    }


def _render_html_table(
    title: str,
    rows: list[dict[str, Any]],
    *,
    max_rows: int = 8,
    max_columns: int = 6,
) -> str:
    title = _display_title(title)
    rows = [localize_historical_record(_drop_unmeaningful_share(row)) for row in rows if isinstance(row, dict)]
    if not rows:
        return (
            f'<section class="historical-table-asset" data-row-count="0" data-rendered-row-count="0" '
            f'data-hidden-row-count="0" data-column-count="0"><h3>{html.escape(title)}</h3>'
            "<p>当前数据没有可展示的明细行，页面不应作为主分析页使用。</p></section>"
        )
    all_headers = list(rows[0].keys())
    headers = [header for header in all_headers if _share_column_has_reader_value(rows, header)]
    if not headers:
        headers = all_headers
    headers = headers[: max(1, max_columns)]
    rendered_rows = rows[: max(1, max_rows)]
    hidden_rows = max(0, len(rows) - len(rendered_rows))
    hidden_columns = max(0, len(all_headers) - len(headers))
    thead = "".join(f"<th>{html.escape(_display_header(header))}</th>" for header in headers)
    body_rows: list[str] = []
    for row in rendered_rows:
        cells = "".join(
            f"<td>{html.escape(_format_scalar(row.get(header)))}</td>" for header in headers
        )
        body_rows.append(f"<tr>{cells}</tr>")
    note_bits = [f"显示 {len(rendered_rows)} / {len(rows)} 行"]
    if hidden_rows:
        note_bits.append(f"{hidden_rows} 行进入附录或后续明细页")
    if hidden_columns:
        note_bits.append(f"{hidden_columns} 个低优先字段被摘要")
    note = "；".join(note_bits)
    return (
        f'<section class="historical-table-asset" data-table-title="{html.escape(title)}" '
        f'data-row-count="{len(rows)}" data-rendered-row-count="{len(rendered_rows)}" '
        f'data-hidden-row-count="{hidden_rows}" data-column-count="{len(headers)}" '
        f'data-hidden-column-count="{hidden_columns}"><h3>{html.escape(title)}</h3>'
        f'<table><thead><tr>{thead}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'
        f'<p class="table-note">{html.escape(note)}</p></section>'
    )


def render_historical_table_asset_pack(
    *,
    workspace: Path,
    support_tables_path: Path,
    asset_dir_name: str = "historical_table_assets",
    index_name: str = "historical_table_assets_index.json",
) -> dict[str, Any]:
    support_tables = json.loads(support_tables_path.read_text(encoding="utf-8-sig"))
    if not isinstance(support_tables, dict):
        support_tables = {}
    asset_dir = workspace / asset_dir_name
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, Any]] = []

    kpi_rows = list(support_tables.get("kpi_snapshot") or [])
    if kpi_rows:
        path = asset_dir / "kpi_snapshot_table.html"
        _write_text(path, _render_html_table("KPI Snapshot", kpi_rows))
        assets.append(_asset_metadata(path, table_id="kpi_snapshot", title="KPI Snapshot", role="kpi_scorecard_page", story_role="kpi_scorecard", management_use="用于高层快速读取核心指标现状。"))

    derived_metric_rows = [row for row in list(support_tables.get("derived_metric_rows") or []) if isinstance(row, dict)]
    if derived_metric_rows:
        metric_names = [
            str(row.get("metric_raw_key") or row.get("metric") or "").strip()
            for row in derived_metric_rows
            if str(row.get("metric_raw_key") or row.get("metric") or "").strip()
        ]
        path = asset_dir / "derived_metric_matrix_table.html"
        _write_text(path, _render_html_table("Derived Metric Matrix", derived_metric_rows[:24]))
        assets.append(
            _asset_metadata(
                path,
                table_id="derived_metric_matrix",
                title="Derived Metric Matrix",
                role="appendix_glossary_page",
                insight_input={
                    "rows": derived_metric_rows[:24],
                    "metric_names": metric_names[:24],
                    "used_metric_names": metric_names[:24],
                    "is_derived_metric_table": True,
                },
                story_role="derived_metric_matrix",
                management_use="用于把派生指标口径、公式、当前值和经营含义纳入正文与附录。",
            )
        )

    for index, item in enumerate(list(support_tables.get("ranking_tables") or [])[:12], start=1):
        if not isinstance(item, dict):
            continue
        rows = list(item.get("rows") or [])
        dimension = str(item.get("dimension") or f"dimension_{index}")
        path = asset_dir / f"ranking_{index:02d}_{_safe_id(dimension, fallback='dimension')}.html"
        ranking_title = f"{dimension} 排名"
        _write_text(path, _render_html_table(ranking_title, rows))
        assets.append(
            _asset_metadata(
                path,
                table_id=f"ranking_{_safe_id(dimension, fallback='dimension')}",
                title=ranking_title,
                role="ranking_table_page",
                insight_input=item,
                story_role="dimension_ranking",
                management_use="用于识别维度内的头部与尾部对象。",
            )
        )

    correlation_rows = list(support_tables.get("correlation_focus") or [])
    if correlation_rows:
        path = asset_dir / "correlation_focus_table.html"
        _write_text(path, _render_html_table("Correlation Focus", correlation_rows))
        assets.append(_asset_metadata(path, table_id="correlation_focus", title="Correlation Focus", role="comparison_matrix_page", story_role="relationship_focus", management_use="用于突出最值得管理层关注的强相关组合。"))

    dimension_matrix_rows = list(support_tables.get("dimension_matrix") or [])
    if not dimension_matrix_rows:
        dimension_matrix_rows = _build_dimension_matrix_rows(list(support_tables.get("ranking_tables") or []))
    if dimension_matrix_rows:
        path = asset_dir / "dimension_signal_matrix.html"
        _write_text(path, _render_html_table("Dimension Signal Matrix", dimension_matrix_rows))
        assets.append(
            _asset_metadata(
                path,
                table_id="dimension_signal_matrix",
                title="Dimension Signal Matrix",
                role="comparison_matrix_page",
                insight_input={"rows": dimension_matrix_rows},
                story_role="dimension_signal_matrix",
                management_use="用于比较不同维度在关键指标上的强弱差异。",
            )
        )

    priority_action_rows = list(support_tables.get("priority_action_table") or [])
    if not priority_action_rows:
        priority_action_rows = _build_priority_action_rows(
            kpi_rows,
            list(support_tables.get("ranking_tables") or []),
            correlation_rows,
        )
    if priority_action_rows:
        path = asset_dir / "priority_action_table.html"
        _write_text(path, _render_html_table("Priority Action Table", priority_action_rows))
        assets.append(
            _asset_metadata(
                path,
                table_id="priority_action_table",
                title="Priority Action Table",
                role="summary_map_page",
                insight_input={"actions": priority_action_rows},
                story_role="priority_actions",
                management_use="用于把关键信号直接转成优先动作清单。",
            )
        )

    segment_scorecards = list(support_tables.get("segment_scorecards") or [])
    if segment_scorecards:
        path = asset_dir / "segment_scorecards_table.html"
        compact_scorecards = _compact_segment_scorecard_rows(segment_scorecards, limit=18)
        _write_text(path, _render_html_table("Segment Scorecards", compact_scorecards))
        assets.append(
            _asset_metadata(
                path,
                table_id="segment_scorecards",
                title="Segment Scorecards",
                role="kpi_scorecard_page",
                insight_input={"rows": compact_scorecards},
                story_role="segment_scorecards",
                management_use="用于展示重点分层对象的多指标记分卡。",
            )
        )

    cross_dimension_tables = list(support_tables.get("cross_dimension_priority_tables") or [])
    if cross_dimension_tables:
        first_table = cross_dimension_tables[0] if isinstance(cross_dimension_tables[0], dict) else {}
        rows = _compact_cross_dimension_rows(list(first_table.get("rows") or []), limit=18)
        if rows:
            path = asset_dir / "cross_dimension_priority_matrix.html"
            _write_text(path, _render_html_table("Cross-Dimension Priority Matrix", rows))
            assets.append(
                _asset_metadata(
                    path,
                    table_id="cross_dimension_priority_matrix",
                    title="Cross-Dimension Priority Matrix",
                    role="comparison_matrix_page",
                    insight_input=first_table,
                    story_role="cross_dimension_priority_matrix",
                    management_use="用于展示二维对象池中的优先级与修复区分布。",
                )
            )

    glossary_rows = list(support_tables.get("glossary_rows") or [])
    if glossary_rows:
        path = asset_dir / "glossary_table.html"
        _write_text(path, _render_html_table("Metric & Dimension Glossary", glossary_rows))
        assets.append(_asset_metadata(path, table_id="glossary", title="Metric & Dimension Glossary", role="appendix_glossary_page", story_role="appendix_glossary", management_use="用于附录口径说明与字段释义。"))

    appendix_detail_rows = list(support_tables.get("appendix_detail_rows") or [])
    if not appendix_detail_rows:
        appendix_detail_rows = _build_appendix_detail_rows(list(support_tables.get("ranking_tables") or []), glossary_rows)
    if appendix_detail_rows:
        path = asset_dir / "appendix_detail_table.html"
        _write_text(path, _render_html_table("Appendix Detail Table", appendix_detail_rows))
        assets.append(_asset_metadata(path, table_id="appendix_detail_table", title="Appendix Detail Table", role="appendix_detail_table_page", story_role="appendix_detail", management_use="用于附录中的明细行与二维对象明细。"))

    index_payload = {
        "asset_dir": str(asset_dir.resolve()),
        "table_count": len(assets),
        "assets": assets,
    }
    index_path = workspace / index_name
    _write_text(index_path, json.dumps(index_payload, ensure_ascii=False, indent=2))
    return {
        "index_path": str(index_path.resolve()),
        "asset_dir": str(asset_dir.resolve()),
        "table_count": len(assets),
        "assets": assets,
    }
