from __future__ import annotations

from typing import Any


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() == "n/a":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _format_percent(value: Any) -> str:
    numeric = _parse_float(value)
    if numeric is None:
        return "n/a"
    return f"{numeric * 100:.1f}%"


def _pretty_label(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "未命名对象"
    return text.replace("_", " ").replace("-", " ")


def _category_role(index: int, share: float) -> str:
    if index == 1:
        return "结构头部"
    if share >= 0.1:
        return "次头部"
    if share >= 0.03:
        return "中位承接"
    return "长尾边缘"


def build_generic_rows_by_dimension(
    *,
    primary_category_column: str | None,
    category_rows: list[dict[str, Any]],
    temporal_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    outlier_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    rows_by_dimension: dict[str, list[dict[str, Any]]] = {}

    if category_rows:
        category_dimension = str(primary_category_column or "类别切片")
        category_dimension_rows: list[dict[str, Any]] = []
        for index, row in enumerate(category_rows, start=1):
            share = float(row.get("share") or 0.0)
            category_dimension_rows.append(
                {
                    "对象": _pretty_label(row.get("category")),
                    "数量": int(row.get("count") or 0),
                    "占比": share,
                    "经营判断": _category_role(index, share),
                    "判断依据": f"数量 {int(row.get('count') or 0)}、占比 {_format_percent(share)}",
                }
            )
        rows_by_dimension[category_dimension] = category_dimension_rows

    if temporal_rows:
        ordered_temporal = sorted(
            temporal_rows,
            key=lambda row: float(row.get("value") or 0.0),
            reverse=True,
        )
        peak_period = str(ordered_temporal[0].get("period") or "峰值窗口")
        trough_period = str(ordered_temporal[-1].get("period") or "低谷窗口")
        temporal_dimension_rows: list[dict[str, Any]] = []
        for row in ordered_temporal:
            period = str(row.get("period") or "时间窗口")
            value = float(row.get("value") or 0.0)
            if period == peak_period:
                role = "峰值窗口"
            elif period == trough_period:
                role = "低谷窗口"
            else:
                role = "常态窗口"
            temporal_dimension_rows.append(
                {
                    "对象": period,
                    "数值": value,
                    "经营判断": role,
                    "判断依据": f"窗口值 {value:,.2f}",
                }
            )
        rows_by_dimension["时间窗口"] = temporal_dimension_rows

    if correlation_rows:
        correlation_dimension_rows: list[dict[str, Any]] = []
        for row in correlation_rows:
            correlation = float(row.get("correlation") or 0.0)
            abs_correlation = abs(correlation)
            if abs_correlation >= 0.8:
                role = "强联动"
            elif abs_correlation >= 0.5:
                role = "中强联动"
            else:
                role = "弱联动"
            correlation_dimension_rows.append(
                {
                    "对象": f"{row.get('left')} × {row.get('right')}",
                    "相关系数": correlation,
                    "经营判断": role,
                    "判断依据": f"相关系数 {correlation:.3f}",
                }
            )
        rows_by_dimension["指标联动"] = correlation_dimension_rows

    if outlier_rows:
        outlier_dimension_rows: list[dict[str, Any]] = []
        for row in outlier_rows[:8]:
            ratio = float(row.get("outlier_ratio") or 0.0)
            outlier_dimension_rows.append(
                {
                    "对象": str(row.get("column") or "异常字段"),
                    "占比": ratio,
                    "经营判断": "高异常字段" if ratio >= 0.1 else "需复核字段",
                    "判断依据": f"异常占比 {_format_percent(ratio)}",
                }
            )
        rows_by_dimension["异常字段"] = outlier_dimension_rows

    return rows_by_dimension


def build_generic_relation_context(
    *,
    rows_by_dimension: dict[str, list[dict[str, Any]]],
    primary_category_column: str | None,
    category_rows: list[dict[str, Any]],
    temporal_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    outlier_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    dimension_profiles: list[dict[str, Any]] = []
    relation_findings: list[str] = []

    for dimension, rows in rows_by_dimension.items():
        if not rows:
            continue
        head = rows[0]
        middle = rows[len(rows) // 2] if len(rows) > 2 else rows[0]
        tail = rows[-1]
        dimension_profiles.append(
            {
                "dimension": dimension,
                "row_count": len(rows),
                "head": head,
                "middle": middle,
                "tail": tail,
            }
        )

    if category_rows:
        head = category_rows[0]
        runner_up = category_rows[1] if len(category_rows) > 1 else None
        share = float(head.get("share") or 0.0)
        if runner_up:
            gap = share - float(runner_up.get("share") or 0.0)
            relation_findings.append(
                f"`{_pretty_label(head.get('category'))}` 在 `{primary_category_column or '类别'}` 里当前占比 {_format_percent(share)}，相比第二名拉开 {_format_percent(gap)}，说明结构已经出现明确头部。"
            )
        else:
            relation_findings.append(
                f"`{_pretty_label(head.get('category'))}` 是当前唯一显著结构对象，占比 {_format_percent(share)}，后续应优先围绕它做对象级拆解。"
            )

    if len(temporal_rows) >= 2:
        peak = max(temporal_rows, key=lambda row: float(row.get("value") or 0.0))
        trough = min(temporal_rows, key=lambda row: float(row.get("value") or 0.0))
        latest = temporal_rows[-1]
        previous = temporal_rows[-2]
        prev_value = float(previous.get("value") or 0.0)
        latest_value = float(latest.get("value") or 0.0)
        delta_ratio = None if prev_value == 0 else (latest_value - prev_value) / abs(prev_value)
        relation_findings.append(
            f"时间窗口里峰值出现在 `{peak.get('period')}`，低谷出现在 `{trough.get('period')}`，说明当前不是平滑常态盘，而是存在明显节奏差。"
        )
        if delta_ratio is not None:
            relation_findings.append(
                f"最近窗口 `{latest.get('period')}` 相比 `{previous.get('period')}` 变化 {_format_percent(delta_ratio)}，后续深挖必须把当前窗口和上一窗口拆开看。"
            )

    if correlation_rows:
        top_corr = correlation_rows[0]
        relation_findings.append(
            f"`{top_corr.get('left')}` 与 `{top_corr.get('right')}` 的相关系数为 {float(top_corr.get('correlation') or 0.0):.3f}，这对指标应被放进同一条监控链，而不是分开解释。"
        )

    if outlier_rows:
        top_outlier = outlier_rows[0]
        relation_findings.append(
            f"`{top_outlier.get('column')}` 的异常占比约 {_format_percent(top_outlier.get('outlier_ratio'))}，说明这份数据里至少有一个字段会显著拉歪均值和总量判断。"
        )

    return {
        "dimension_profiles": dimension_profiles,
        "relation_findings": relation_findings[:12],
    }


def build_generic_deep_mining_context(
    *,
    dataset_name: str,
    sheet_name: str,
    request: dict[str, Any],
    report: dict[str, Any],
    primary_category_column: str | None,
    category_rows: list[dict[str, Any]],
    temporal_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    outlier_rows: list[dict[str, Any]],
    relation_context: dict[str, Any],
    context_compaction: dict[str, Any],
    background_understanding: dict[str, Any] | None = None,
    structure_agent_layer: dict[str, Any] | None = None,
    pattern_agent_layer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    compact_sections = [
        {
            "id": str(section.get("id") or ""),
            "title": str(section.get("title") or ""),
            "summary": str(section.get("summary") or ""),
            "bullets": [str(item) for item in (section.get("bullets") or [])[:4]],
        }
        for section in report.get("sections", [])[:24]
    ]
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "request": request,
        "current_report": {
            "title": report.get("title"),
            "executive_summary": report.get("executive_summary", [])[:6],
            "sections": compact_sections,
        },
        "primary_category_column": primary_category_column or "",
        "category_rows": category_rows[:12],
        "temporal_rows": temporal_rows[:12],
        "correlation_rows": correlation_rows[:8],
        "outlier_rows": outlier_rows[:8],
        "relation_context": relation_context,
        "context_compaction": context_compaction,
        "background_understanding": background_understanding or {},
        "structure_agent_layer": structure_agent_layer or {},
        "pattern_agent_layer": pattern_agent_layer or {},
    }
