from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from app.services.codex_historical_localization_service import localize_historical_text


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return localize_historical_text(text, fallback=fallback) or fallback


def _safe_id(value: Any, *, fallback: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value or "").strip()).strip("_")
    return text[:60] or fallback


def _format_value(value: Any) -> str:
    try:
        number = float(value)
    except Exception:
        return localize_historical_text(value)
    if abs(number) >= 10000:
        return f"{number / 10000:.1f}万"
    if abs(number) >= 100:
        return f"{number:,.0f}"
    if abs(number) >= 1:
        return f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{number:.2%}"


def _as_records(value: Any, *, limit: int = 12) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    records: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            records.append(dict(item))
        elif str(item or "").strip():
            records.append({"label": str(item).strip()})
        if len(records) >= limit:
            break
    return records


def build_historical_collage_source(
    *,
    current_report_context: dict[str, Any] | None = None,
    support_tables: dict[str, Any] | None = None,
    visual_reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic source material for non-chart, non-table deck collage blocks."""
    current_report_context = dict(current_report_context or {})
    support_tables = dict(support_tables or {})
    visual_reference = dict(visual_reference or {})

    tag_items: list[dict[str, Any]] = []
    for item in _as_records(current_report_context.get("column_summaries"), limit=24):
        name = _clean_text(item.get("name") or item.get("column"))
        if not name:
            continue
        tag_items.append(
            {
                "label": name,
                "kind": _clean_text(item.get("dtype"), fallback="field"),
                "weight": item.get("unique_count") or item.get("non_null_count") or 1,
            }
        )
    for token in list(visual_reference.get("visual_style_tokens") or [])[:10]:
        label = _clean_text(token)
        if label:
            tag_items.append({"label": label, "kind": "style", "weight": 2})

    segment_badges: list[dict[str, Any]] = []
    for table in _as_records(support_tables.get("ranking_tables"), limit=6):
        dimension = _clean_text(table.get("dimension"), fallback="dimension")
        rows = _as_records(table.get("rows"), limit=4)
        for row in rows:
            label = _clean_text(row.get(dimension) or row.get("label") or next(iter(row.values()), ""))
            if not label:
                continue
            metric_bits = []
            for key, value in list(row.items())[:5]:
                if str(key) == dimension:
                    continue
                metric_bits.append(f"{localize_historical_text(key)}: {_format_value(value)}")
            segment_badges.append(
                {
                    "dimension": dimension,
                    "label": label,
                    "metrics": metric_bits[:3],
                }
            )

    benchmark_callouts: list[dict[str, Any]] = []
    for row in _as_records(support_tables.get("kpi_snapshot"), limit=10):
        benchmark_callouts.append(
            {
                "metric": _clean_text(row.get("metric"), fallback="metric"),
                "value": row.get("value"),
                "aggregation": _clean_text(row.get("aggregation"), fallback="snapshot"),
                "interpretation": "作为对标或差距页的确定性指标提示。",
            }
        )

    summary_map_nodes: list[dict[str, Any]] = []
    kpi_clauses = [
        "作为规模判断锚点。",
        "用于校验增长是否由真实交易支撑。",
        "用于判断价格与结构质量。",
        "用于判断收入质量和利润弹性。",
        "用于定位流量到订单的效率缺口。",
        "用于识别客群粘性和复购基础。",
    ]
    for index, row in enumerate(benchmark_callouts[:6], start=1):
        metric = _clean_text(row.get("metric"), fallback="指标")
        value = _format_value(row.get("value"))
        if metric and str(value).strip():
            clause = kpi_clauses[(index - 1) % len(kpi_clauses)]
            summary_map_nodes.append(
                {
                    "node_id": f"kpi_{index}",
                    "label": f"{metric}当前读数为{value}，{clause}",
                    "kind": "kpi",
                }
            )
    for index, table in enumerate(_as_records(support_tables.get("ranking_tables"), limit=5), start=1):
        dimension = _clean_text(table.get("dimension"), fallback="维度")
        metric = _clean_text(table.get("metric"), fallback="指标")
        rows = _as_records(table.get("rows"), limit=8)
        if not rows:
            continue
        first = rows[0]
        last = rows[-1]
        first_label = _clean_text(first.get(dimension) or first.get("label") or next(iter(first.values()), ""))
        last_label = _clean_text(last.get(dimension) or last.get("label") or next(iter(last.values()), ""))
        first_value = first.get("value")
        last_value = last.get("value")
        if first_label and first_value is not None and last_label and last_value is not None:
            summary_map_nodes.append(
                {
                    "node_id": f"rank_{index}",
                    "label": f"{dimension}中{first_label}在{metric}上达到{_format_value(first_value)}，{last_label}为{_format_value(last_value)}。",
                    "kind": "ranking",
                }
            )

    module_tiles: list[dict[str, Any]] = []
    for index, section in enumerate(_as_records(current_report_context.get("section_summaries"), limit=8), start=1):
        module_tiles.append(
            {
                "module": _clean_text(section.get("title"), fallback=f"Module {index}"),
                "summary": _clean_text(section.get("summary"), fallback="该模块用于承接当前数据的主要分层判断。"),
                "role": "analysis_module",
            }
        )
    if not module_tiles:
        for index, text in enumerate(list(current_report_context.get("executive_summary") or [])[:5], start=1):
            module_tiles.append(
                {
                    "module": f"模块 {index}",
                    "summary": _clean_text(text),
                    "role": "executive_signal",
                }
            )

    action_roadmap: list[dict[str, Any]] = []
    for index, row in enumerate(benchmark_callouts[:6], start=1):
        action_roadmap.append(
            {
                "step": index,
                "focus": row.get("metric"),
                "basis": row.get("value"),
                "action": "将该信号转化为分层经营动作，并指定责任对象。",
            }
        )
    for index, badge in enumerate(segment_badges[:6], start=len(action_roadmap) + 1):
        action_roadmap.append(
            {
                "step": index,
                "focus": badge.get("label"),
                "basis": " / ".join(list(badge.get("metrics") or [])[:2]),
                "action": "为该分层定义差异化经营动作。",
            }
        )

    varied_roadmap: list[dict[str, Any]] = []
    metric_actions = [
        "{metric} 当前为 {value}，本周期先把该指标拆到主要区域和渠道，定位贡献最高与拖累最大的两个对象。",
        "{metric} 当前为 {value}，运营负责人需要把高贡献对象纳入加码清单，同时给低位对象设置复盘阈值。",
        "{metric} 当前为 {value}，财务/经营侧应同步看规模、毛利和折扣，避免只追单一增量。",
        "{metric} 当前为 {value}，下周复盘时优先检查头部对象是否可复制、尾部对象是否需要修复或退出。",
    ]
    segment_actions = [
        "{segment} 的关键依据是 {basis}，建议用一页动作表拆成保量、提效、控损三类任务。",
        "{segment} 的关键依据是 {basis}，先确认负责团队，再把异常指标落到渠道、类目或客群对象。",
        "{segment} 的关键依据是 {basis}，建议保留优势动作，同时给低表现指标设置七天观察口径。",
        "{segment} 的关键依据是 {basis}，后续页面应追踪其对销售额、订单量和毛利率的联动影响。",
    ]
    for index, row in enumerate(benchmark_callouts[:6], start=1):
        metric = _clean_text(row.get("metric"), fallback=f"指标{index}")
        raw_value = row.get("value")
        value = _format_value(raw_value) if raw_value is not None else "当前样本值"
        varied_roadmap.append(
            {
                "step": index,
                "focus": metric,
                "basis": value,
                "action": metric_actions[(index - 1) % len(metric_actions)].format(metric=metric, value=value),
            }
        )
    for offset, badge in enumerate(segment_badges[:6], start=1):
        index = len(varied_roadmap) + 1
        segment = _clean_text(badge.get("label"), fallback=f"分层{offset}")
        basis = _clean_text(" / ".join(list(badge.get("metrics") or [])[:2]), fallback="核心指标组合")
        varied_roadmap.append(
            {
                "step": index,
                "focus": segment,
                "basis": basis,
                "action": segment_actions[(offset - 1) % len(segment_actions)].format(segment=segment, basis=basis),
            }
        )
    if varied_roadmap:
        action_roadmap = varied_roadmap[:12]

    gap_matrix_blocks: list[dict[str, Any]] = []
    for index, item in enumerate(benchmark_callouts[:8], start=1):
        gap_matrix_blocks.append(
            {
                "zone": f"Gap {index}",
                "metric": item.get("metric"),
                "signal": item.get("value"),
                "management_use": "用于对标、差距或优先级比较页",
            }
        )

    return {
        "tag_board": tag_items[:32],
        "segment_badges": segment_badges[:18],
        "benchmark_callouts": benchmark_callouts[:12],
        "summary_map_nodes": summary_map_nodes[:16],
        "module_tiles": module_tiles[:10],
        "action_roadmap": action_roadmap[:12],
        "gap_matrix_blocks": gap_matrix_blocks[:12],
        "visual_style_tokens": list(visual_reference.get("visual_style_tokens") or [])[:16],
        "recommended_page_roles": [
            "collage_preference_page",
            "summary_map_page",
            "comparison_matrix_page",
            "persona_badge_page",
        ],
    }


def _render_tag_board(title: str, items: list[dict[str, Any]]) -> str:
    tags: list[str] = []
    for index, item in enumerate(items[:32], start=1):
        label = html.escape(_clean_text(item.get("label"), fallback=f"tag {index}")[:36])
        kind = html.escape(_clean_text(item.get("kind"), fallback="signal")[:18])
        weight = item.get("weight") or 1
        try:
            size = 14 + min(18, max(0, float(weight)) % 19)
        except Exception:
            size = 16
        tags.append(
            f'<span class="collage-tag" style="font-size:{size:.0f}px"><b>{label}</b><small>{kind}</small></span>'
        )
    body = "".join(tags) or '<p class="empty">暂无标签资产。</p>'
    return (
        '<section class="historical-collage-asset tag-board">'
        f"<h3>{html.escape(title)}</h3><div class=\"tag-grid\">{body}</div></section>"
    )


def _render_badges(title: str, badges: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for badge in badges[:18]:
        metrics = "".join(
            f"<li>{html.escape(_clean_text(metric))}</li>" for metric in list(badge.get("metrics") or [])[:3]
        )
        cards.append(
            '<article class="badge-card">'
            f'<p class="badge-kicker">{html.escape(_clean_text(badge.get("dimension"), fallback="分层"))}</p>'
            f'<h4>{html.escape(_clean_text(badge.get("label"), fallback="分层"))}</h4>'
            f"<ul>{metrics}</ul>"
            "</article>"
        )
    body = "".join(cards) or '<p class="empty">暂无客群卡片资产。</p>'
    return (
        '<section class="historical-collage-asset badge-board">'
        f"<h3>{html.escape(title)}</h3><div class=\"badge-grid\">{body}</div></section>"
    )


def _render_callouts(title: str, callouts: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for item in callouts[:12]:
        cards.append(
            '<article class="callout-card">'
            f'<p>{html.escape(_clean_text(item.get("aggregation"), fallback="快照"))}</p>'
            f'<h4>{html.escape(_clean_text(item.get("metric"), fallback="指标"))}</h4>'
            f'<strong>{html.escape(str(item.get("value") if item.get("value") is not None else ""))}</strong>'
            "</article>"
        )
    body = "".join(cards) or '<p class="empty">暂无指标提示资产。</p>'
    return (
        '<section class="historical-collage-asset callout-board">'
        f"<h3>{html.escape(title)}</h3><div class=\"callout-grid\">{body}</div></section>"
    )


def _render_summary_map(title: str, nodes: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    kind_labels = {
        "kpi": "KPI",
        "ranking": "排名",
        "executive": "结论",
        "section": "模块",
    }
    for node in nodes[:16]:
        kind = str(node.get("kind") or "").strip()
        cards.append(
            '<article class="summary-node">'
            f'<span>{html.escape(kind_labels.get(kind, _clean_text(kind, fallback="节点")))}</span>'
            f'<p>{html.escape(_clean_text(node.get("label"), fallback="摘要节点")[:90])}</p>'
            "</article>"
        )
    body = "".join(cards) or '<p class="empty">暂无摘要地图节点。</p>'
    return (
        '<section class="historical-collage-asset summary-map">'
        f"<h3>{html.escape(title)}</h3><div class=\"summary-grid\">{body}</div></section>"
    )


def _render_module_tiles(title: str, tiles: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for tile in tiles[:10]:
        cards.append(
            '<article class="module-tile">'
            f'<span>{html.escape(_clean_text(tile.get("role"), fallback="模块"))}</span>'
            f'<h4>{html.escape(_clean_text(tile.get("module"), fallback="模块"))}</h4>'
            f'<p>{html.escape(_clean_text(tile.get("summary"), fallback="模块摘要")[:120])}</p>'
            "</article>"
        )
    body = "".join(cards) or '<p class="empty">暂无模块导航资产。</p>'
    return (
        '<section class="historical-collage-asset module-board">'
        f"<h3>{html.escape(title)}</h3><div class=\"module-grid\">{body}</div></section>"
    )


def _render_action_roadmap(title: str, actions: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for item in actions[:6]:
        basis = _format_value(item.get("basis")) if item.get("basis") is not None else ""
        cards.append(
            '<article class="roadmap-step">'
            f'<strong>{html.escape(str(item.get("step") or ""))}</strong>'
            f'<h4>{html.escape(_clean_text(item.get("focus"), fallback="优先项"))}</h4>'
            f'<p class="basis">{html.escape(basis)}</p>'
            f'<p>{html.escape(_clean_text(item.get("action"), fallback="经营动作"))}</p>'
            "</article>"
        )
    body = "".join(cards) or '<p class="empty">暂无行动路线图资产。</p>'
    return (
        '<section class="historical-collage-asset action-roadmap">'
        f"<h3>{html.escape(title)}</h3><div class=\"roadmap-grid\">{body}</div></section>"
    )


def _render_gap_matrix(title: str, blocks: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for item in blocks[:12]:
        signal = _clean_text(item.get("signal")) if item.get("signal") is not None else ""
        cards.append(
            '<article class="gap-card">'
            f'<span>{html.escape(_clean_text(item.get("zone"), fallback="差距"))}</span>'
            f'<h4>{html.escape(_clean_text(item.get("metric"), fallback="指标"))}</h4>'
            f'<strong>{html.escape(signal)}</strong>'
            f'<p>{html.escape(_clean_text(item.get("management_use"), fallback="管理用途"))}</p>'
            "</article>"
        )
    body = "".join(cards) or '<p class="empty">暂无差距矩阵资产。</p>'
    return (
        '<section class="historical-collage-asset gap-matrix">'
        f"<h3>{html.escape(title)}</h3><div class=\"gap-grid\">{body}</div></section>"
    )


def _asset_metadata(path: Path, *, asset_id: str, title: str, role: str, story_role: str = "", management_use: str = "") -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "asset_type": "collage",
        "kind": "collage",
        "title": localize_historical_text(title, fallback=title),
        "file_name": path.name,
        "path": str(path.resolve()),
        "recommended_page_role": role,
        "story_role": story_role or role,
        "management_use": management_use,
    }


def _collage_rows_have_reader_value(asset_id: str, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    if asset_id == "tag_board":
        data_tags = [
            row for row in rows
            if str(row.get("kind") or "").strip().lower() not in {"style", "visual", "theme"}
            and str(row.get("label") or "").strip()
        ]
        return len(data_tags) >= 3
    if asset_id == "segment_badges":
        return any(str(row.get("label") or "").strip() and list(row.get("metrics") or []) for row in rows)
    if asset_id == "benchmark_callouts":
        return any(str(row.get("metric") or "").strip() and row.get("value") is not None for row in rows)
    if asset_id == "summary_map":
        return len([row for row in rows if str(row.get("label") or "").strip()]) >= 2
    if asset_id == "module_navigation":
        return any(
            str(row.get("module") or "").strip()
            and not re.fullmatch(r"Module\s+\d+", str(row.get("module") or "").strip(), flags=re.I)
            and str(row.get("summary") or "").strip()
            for row in rows
        )
    if asset_id == "action_roadmap":
        return any(str(row.get("focus") or "").strip() and str(row.get("basis") or "").strip() for row in rows)
    if asset_id == "gap_matrix":
        return any(str(row.get("metric") or "").strip() and str(row.get("signal") or "").strip() for row in rows)
    return True


def _collage_source_key(asset_id: str) -> str:
    return {
        "tag_board": "tag_board",
        "segment_badges": "segment_badges",
        "benchmark_callouts": "benchmark_callouts",
        "summary_map": "summary_map_nodes",
        "module_navigation": "module_tiles",
        "action_roadmap": "action_roadmap",
        "gap_matrix": "gap_matrix_blocks",
    }.get(asset_id, asset_id)


def _collage_insight_input(asset_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    metric_names: list[str] = []
    dimension_names: list[str] = []
    for row in rows:
        for key in ("metric", "focus"):
            value = str(row.get(key) or "").strip()
            if value and value not in metric_names:
                metric_names.append(value)
        for key in ("dimension", "zone", "kind"):
            value = str(row.get(key) or "").strip()
            if value and value not in dimension_names:
                dimension_names.append(value)
    return {
        "source_key": _collage_source_key(asset_id),
        "rows": rows[:12],
        "source_metric_names": metric_names[:12],
        "source_dimension_names": dimension_names[:12],
    }


def render_historical_collage_asset_pack(
    *,
    workspace: Path,
    collage_source_path: Path,
    asset_dir_name: str = "historical_collage_assets",
    index_name: str = "historical_collage_assets_index.json",
) -> dict[str, Any]:
    payload = json.loads(collage_source_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        payload = {}
    asset_dir = workspace / asset_dir_name
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, Any]] = []

    definitions = [
        (
            "tag_board",
            "信号标签板",
            "collage_preference_page",
            "tag_board",
            "用于扉页、目录前页或风格信号页，快速建立主题词与分析氛围。",
            _render_tag_board("信号标签板", _as_records(payload.get("tag_board"), limit=32)),
        ),
        (
            "segment_badges",
            "业态与客群卡片",
            "persona_badge_page",
            "segment_badges",
            "用于展示重点分层对象及其关键指标画像。",
            _render_badges("业态与客群卡片", _as_records(payload.get("segment_badges"), limit=18)),
        ),
        (
            "benchmark_callouts",
            "关键指标提示板",
            "comparison_matrix_page",
            "benchmark_callouts",
            "用于对标、差距或优先级比较页。",
            _render_callouts("关键指标提示板", _as_records(payload.get("benchmark_callouts"), limit=12)),
        ),
        (
            "summary_map",
            "执行摘要地图",
            "summary_map_page",
            "summary_map",
            "用于执行摘要或综合判断页，压缩核心结论节点。",
            _render_summary_map("执行摘要地图", _as_records(payload.get("summary_map_nodes"), limit=16)),
        ),
        (
            "module_navigation",
            "模块导航板",
            "module_divider_page",
            "module_navigation",
            "用于模块扉页或目录后的导航页。",
            _render_module_tiles("模块导航板", _as_records(payload.get("module_tiles"), limit=10)),
        ),
        (
            "action_roadmap",
            "行动路线图",
            "summary_map_page",
            "action_roadmap",
            "用于行动路线图与阶段动作页。",
            _render_action_roadmap("行动路线图", _as_records(payload.get("action_roadmap"), limit=12)),
        ),
        (
            "gap_matrix",
            "差距矩阵",
            "comparison_matrix_page",
            "gap_matrix",
            "用于差距比较、优先级矩阵和修复区判断页。",
            _render_gap_matrix("差距矩阵", _as_records(payload.get("gap_matrix_blocks"), limit=12)),
        ),
    ]
    for asset_id, title, role, story_role, management_use, content in definitions:
        source_key = _collage_source_key(asset_id)
        source_rows = _as_records(payload.get(source_key), limit=32)
        if not _collage_rows_have_reader_value(asset_id, source_rows):
            continue
        path = asset_dir / f"{_safe_id(asset_id, fallback='collage')}.html"
        _write_text(path, content)
        metadata = _asset_metadata(path, asset_id=asset_id, title=title, role=role, story_role=story_role, management_use=management_use)
        insight_input = _collage_insight_input(asset_id, source_rows)
        metadata["insight_input"] = insight_input
        metadata["source_metric_names"] = insight_input.get("source_metric_names") or []
        metadata["source_dimension_names"] = insight_input.get("source_dimension_names") or []
        assets.append(metadata)

    index_payload = {
        "asset_dir": str(asset_dir.resolve()),
        "collage_count": len(assets),
        "assets": assets,
        "source_name": collage_source_path.name,
    }
    index_path = workspace / index_name
    _write_text(index_path, json.dumps(index_payload, ensure_ascii=False, indent=2))
    return {
        "index_path": str(index_path.resolve()),
        "asset_dir": str(asset_dir.resolve()),
        "collage_count": len(assets),
        "assets": assets,
    }
