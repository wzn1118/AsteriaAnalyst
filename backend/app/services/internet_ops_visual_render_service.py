from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


POINT_ID_COLUMN = "图中序号"
CHANNEL_SOURCE_AARRR_DETAIL = "ops_channel_source_aarrr_detail"
CHANNEL_SOURCE_AARRR_TOPN = "ops_channel_source_aarrr_topn_small_multiples"


def setup_ops_matplotlib() -> Any:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def safe_ratio(numerator: Any, denominator: Any) -> np.ndarray:
    numerator_array = np.asarray(numerator, dtype="float64")
    denominator_array = np.asarray(denominator, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.divide(
            numerator_array,
            denominator_array,
            out=np.zeros_like(numerator_array, dtype="float64"),
            where=np.isfinite(denominator_array) & (denominator_array != 0),
        )
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


def ensure_point_ids_frame(frame: pd.DataFrame, *, id_column: str = POINT_ID_COLUMN, prefix: str = "B") -> pd.DataFrame:
    working = frame.copy().reset_index(drop=True)
    for legacy_column in ["气泡编号", id_column]:
        if legacy_column in working.columns:
            working = working.drop(columns=[legacy_column])
    working.insert(0, id_column, [f"{prefix}{idx:02d}" for idx in range(1, len(working) + 1)])
    return working


def ensure_point_ids_records(
    rows: list[dict[str, Any]],
    *,
    id_column: str = POINT_ID_COLUMN,
    prefix: str = "B",
) -> tuple[list[dict[str, Any]], list[str], bool]:
    if not rows:
        return rows, [], False
    changed = False
    output: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        copied = dict(row)
        expected = f"{prefix}{idx:02d}"
        if copied.get(id_column) != expected or "气泡编号" in copied:
            changed = True
        copied.pop("气泡编号", None)
        copied[id_column] = expected
        ordered = {id_column: copied.pop(id_column)}
        ordered.update(copied)
        output.append(ordered)
    fields = [id_column] + [column for column in output[0].keys() if column != id_column]
    return output, fields, changed


def _numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([0.0] * len(frame), index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _scaled_sizes(frame: pd.DataFrame, size_column: str | None, *, minimum: float = 70.0, maximum: float = 860.0) -> np.ndarray:
    if not size_column or size_column not in frame.columns:
        return np.full(len(frame), (minimum + maximum) / 2.8)
    values = _numeric_series(frame, size_column).abs()
    max_value = float(values.max() or 0.0)
    if max_value <= 0:
        return np.full(len(frame), minimum)
    return np.clip(values / max_value * maximum, minimum, maximum).to_numpy(dtype=float)


def _offset_for_point(index: int, x_value: float, y_value: float, x_limits: tuple[float, float], y_limits: tuple[float, float]) -> tuple[int, int]:
    offsets = [
        (-22, 18),
        (20, 18),
        (0, 25),
        (-26, -4),
        (25, -16),
        (-6, -27),
        (24, 3),
        (-30, -22),
        (29, 24),
        (-18, 32),
        (34, -2),
        (-34, 8),
        (12, -34),
        (35, 14),
        (-10, -38),
        (28, -30),
        (-38, 24),
        (0, -42),
        (38, 0),
        (-38, -10),
        (14, 38),
        (-20, 40),
        (40, 18),
        (-42, 12),
        (42, -14),
        (-8, 46),
        (-46, 26),
        (20, -46),
        (-44, -26),
        (44, 30),
        (52, 4),
        (-52, 4),
        (4, 52),
        (4, -52),
    ]
    dx, dy = offsets[index % len(offsets)]
    x_min, x_max = x_limits
    y_min, y_max = y_limits
    x_span = max(x_max - x_min, 1e-9)
    y_span = max(y_max - y_min, 1e-9)
    if x_value > x_min + x_span * 0.84 and dx > 0:
        dx = -abs(dx) - 8
    if x_value < x_min + x_span * 0.14 and dx < 0:
        dx = abs(dx) + 8
    if y_value > y_min + y_span * 0.84 and dy > 0:
        dy = -abs(dy) - 8
    if y_value < y_min + y_span * 0.14 and dy < 0:
        dy = abs(dy) + 8
    return dx, dy


def annotate_all_points(
    ax: Any,
    frame: pd.DataFrame,
    *,
    x_column: str,
    y_column: str,
    id_column: str = POINT_ID_COLUMN,
    fontsize: float = 6.6,
) -> None:
    x_values = _numeric_series(frame, x_column)
    y_values = _numeric_series(frame, y_column)
    valid = frame.loc[x_values.notna() & y_values.notna()].copy()
    if valid.empty:
        return
    x_limits = ax.get_xlim()
    y_limits = ax.get_ylim()
    label_count = len(valid)
    actual_fontsize = max(4.8, min(fontsize, 7.0 - max(0, label_count - 28) * 0.035))
    for label_index, (_, row) in enumerate(valid.iterrows()):
        x_value = float(pd.to_numeric(row.get(x_column), errors="coerce") or 0.0)
        y_value = float(pd.to_numeric(row.get(y_column), errors="coerce") or 0.0)
        offset = _offset_for_point(label_index, x_value, y_value, x_limits, y_limits)
        ax.annotate(
            str(row.get(id_column) or f"B{label_index + 1:02d}"),
            (x_value, y_value),
            fontsize=actual_fontsize,
            fontweight="bold",
            xytext=offset,
            textcoords="offset points",
            ha="center",
            va="center",
            arrowprops={"arrowstyle": "-", "color": "#cbd5e1", "lw": 0.55},
            annotation_clip=False,
            bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.92},
        )


def render_labeled_scatter(
    frame: pd.DataFrame,
    png_path: Path,
    *,
    x_column: str,
    y_column: str,
    title: str,
    xlabel: str,
    ylabel: str,
    size_column: str | None = None,
    color_column: str | None = None,
    category_column: str | None = None,
    category_colors: dict[str, str] | None = None,
    cmap: str = "viridis",
    colorbar_label: str = "",
    median_lines: bool = False,
    diagonal: bool = False,
    percent_x: bool = False,
    percent_y: bool = False,
    note: str = "",
    figsize: tuple[float, float] = (10.8, 6.8),
) -> None:
    plt = setup_ops_matplotlib()
    from matplotlib.ticker import PercentFormatter

    working = ensure_point_ids_frame(frame)
    if working.empty:
        return
    working[x_column] = _numeric_series(working, x_column)
    working[y_column] = _numeric_series(working, y_column)
    sizes = _scaled_sizes(working, size_column)
    fig, ax = plt.subplots(figsize=figsize)
    scatter = None
    if category_column and category_column in working.columns:
        category_colors = category_colors or {}
        for category, part in working.groupby(category_column, dropna=False):
            part_indices = part.index.to_numpy()
            ax.scatter(
                part[x_column],
                part[y_column],
                s=sizes[part_indices],
                c=category_colors.get(str(category), "#64748b"),
                alpha=0.76,
                edgecolors="white",
                linewidths=0.8,
                label=str(category),
            )
        ax.legend(fontsize=8, loc="best", frameon=True)
    else:
        if color_column and color_column in working.columns:
            scatter = ax.scatter(
                working[x_column],
                working[y_column],
                s=sizes,
                c=_numeric_series(working, color_column),
                cmap=cmap,
                alpha=0.76,
                edgecolors="white",
                linewidths=0.8,
            )
        else:
            scatter = ax.scatter(
                working[x_column],
                working[y_column],
                s=sizes,
                color="#2563eb",
                alpha=0.76,
                edgecolors="white",
                linewidths=0.8,
            )
        if color_column and colorbar_label and scatter is not None:
            colorbar = fig.colorbar(scatter, ax=ax, shrink=0.84, pad=0.02)
            colorbar.set_label(colorbar_label)
    if median_lines:
        ax.axvline(float(working[x_column].median()), color="#334155", linestyle="--", linewidth=1)
        ax.axhline(float(working[y_column].median()), color="#334155", linestyle="--", linewidth=1)
    if diagonal:
        limit = max(float(working[x_column].max()), float(working[y_column].max()), 0.01) * 1.12
        ax.plot([0, limit], [0, limit], color="#475569", linestyle="--", linewidth=1.1)
        ax.set_xlim(-limit * 0.04, limit)
        ax.set_ylim(-limit * 0.04, limit)
    else:
        x_min = float(working[x_column].min())
        x_max = float(working[x_column].max())
        y_min = float(working[y_column].min())
        y_max = float(working[y_column].max())
        x_span = max(x_max - x_min, 1e-9)
        y_span = max(y_max - y_min, 1e-9)
        ax.set_xlim(x_min - x_span * 0.10, x_max + x_span * 0.16)
        ax.set_ylim(y_min - y_span * 0.12, y_max + y_span * 0.18)
    annotate_all_points(ax, working, x_column=x_column, y_column=y_column)
    if percent_x:
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    if percent_y:
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.2)
    if size_column:
        ax.scatter([], [], s=240, c="#94a3b8", alpha=0.45, edgecolors="white", label=f"气泡越大={size_column}")
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(handles, labels, fontsize=8, loc="best", frameon=True)
    if note:
        fig.text(0.075, 0.022, note, ha="left", va="bottom", fontsize=9, color="#334155", wrap=True)
        fig.tight_layout(rect=(0, 0.08, 1, 1))
    else:
        fig.tight_layout()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=180)
    plt.close(fig)


def build_channel_source_aarrr_detail(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or not {"channel", "traffic_source"}.issubset(frame.columns):
        return pd.DataFrame()
    working = frame.copy()
    aliases = {
        "曝光": "impressions",
        "点击": "clicks",
        "注册": "registrations",
        "激活": "activations",
        "付费用户": "paid_users",
        "收入": "revenue",
        "运营成本": "operating_cost",
        "贡献毛利": "contribution_margin",
    }
    for source, target in aliases.items():
        if target not in working.columns and source in working.columns:
            working[target] = working[source]
    sum_columns = [
        "impressions",
        "clicks",
        "registrations",
        "activations",
        "paid_users",
        "revenue",
        "operating_cost",
        "contribution_margin",
    ]
    mean_columns = ["roi", "cac", "retention_d7", "nps", "CTR", "CPM", "CPC"]
    for column in sum_columns + mean_columns:
        if column in working.columns:
            working[column] = _numeric_series(working, column)
        else:
            working[column] = 0.0
    grouped = (
        working.groupby(["channel", "traffic_source"], dropna=False)
        .agg(
            sample_size=("channel", "size"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            registrations=("registrations", "sum"),
            activations=("activations", "sum"),
            paid_users=("paid_users", "sum"),
            revenue=("revenue", "sum"),
            operating_cost=("operating_cost", "sum"),
            contribution_margin=("contribution_margin", "sum"),
            roi=("roi", "mean"),
            cac=("cac", "mean"),
            retention_d7=("retention_d7", "mean"),
            nps=("nps", "mean"),
            CTR=("CTR", "mean"),
            CPM=("CPM", "mean"),
            CPC=("CPC", "mean"),
        )
        .reset_index()
    )
    grouped["组合"] = grouped["channel"].astype(str) + " / " + grouped["traffic_source"].astype(str)
    grouped["点击率"] = safe_ratio(grouped["clicks"], grouped["impressions"])
    grouped["点击到注册率"] = safe_ratio(grouped["registrations"], grouped["clicks"])
    grouped["注册到激活率"] = safe_ratio(grouped["activations"], grouped["registrations"])
    grouped["激活到付费率"] = safe_ratio(grouped["paid_users"], grouped["activations"])
    grouped["点击到付费率"] = safe_ratio(grouped["paid_users"], grouped["clicks"])
    grouped["每付费用户收入"] = safe_ratio(grouped["revenue"], grouped["paid_users"])
    grouped["毛利率"] = safe_ratio(grouped["contribution_margin"], grouped["revenue"])
    ordered_columns = [
        "channel",
        "traffic_source",
        "组合",
        "sample_size",
        "impressions",
        "clicks",
        "registrations",
        "activations",
        "paid_users",
        "revenue",
        "operating_cost",
        "contribution_margin",
        "roi",
        "cac",
        "retention_d7",
        "nps",
        "CTR",
        "CPM",
        "CPC",
        "点击率",
        "点击到注册率",
        "注册到激活率",
        "激活到付费率",
        "点击到付费率",
        "每付费用户收入",
        "毛利率",
    ]
    return grouped[ordered_columns].sort_values(["operating_cost", "revenue"], ascending=[False, False]).reset_index(drop=True).round(6)


def select_channel_source_aarrr_topn(detail: pd.DataFrame, *, top_n: int = 12) -> tuple[pd.DataFrame, dict[str, Any]]:
    if detail.empty:
        return detail.copy(), {"top_n": 0, "selection_rules": [], "selected": []}
    working = detail.copy().reset_index(drop=True)
    working["_reason"] = [[] for _ in range(len(working))]
    selected_indices: list[int] = []

    def add_index(index: int | None, reason: str) -> None:
        if index is None or index < 0 or index >= len(working):
            return
        if index not in selected_indices:
            selected_indices.append(index)
        working.at[index, "_reason"] = list(dict.fromkeys(list(working.at[index, "_reason"]) + [reason]))

    for idx in working.sort_values("operating_cost", ascending=False).head(top_n).index.tolist():
        add_index(int(idx), "高消耗优先")
    for column, highest, reason in [
        ("roi", True, "高 roi 代表可加码样本"),
        ("roi", False, "低 roi 异常补入"),
        ("cac", True, "高 cac 异常补入"),
        ("retention_d7", False, "低留存异常补入"),
    ]:
        values = pd.to_numeric(working[column], errors="coerce") if column in working.columns else pd.Series(dtype=float)
        if values.empty or values.dropna().empty:
            continue
        index = int(values.idxmax() if highest else values.idxmin())
        add_index(index, reason)
    if len(selected_indices) < min(top_n, len(working)):
        for idx in working.sort_values("operating_cost", ascending=False).index.tolist():
            add_index(int(idx), "补足 TopN 经营覆盖")
            if len(selected_indices) >= min(top_n, len(working)):
                break
    forced = [idx for idx in selected_indices if working.at[idx, "_reason"] and "高消耗优先" not in working.at[idx, "_reason"]]
    primary = [idx for idx in selected_indices if idx not in forced]
    selected_indices = (forced + primary)[: min(top_n, len(working))]
    selected = working.loc[selected_indices].copy()
    selected["展示排序"] = range(1, len(selected) + 1)
    selected["入选原因"] = selected["_reason"].apply(lambda reasons: "；".join(reasons) if reasons else "TopN 经营覆盖")
    selected = selected.drop(columns=["_reason"])
    selected = selected[
        [
            "展示排序",
            "入选原因",
            "channel",
            "traffic_source",
            "组合",
            "sample_size",
            "impressions",
            "clicks",
            "registrations",
            "activations",
            "paid_users",
            "revenue",
            "operating_cost",
            "contribution_margin",
            "roi",
            "cac",
            "retention_d7",
            "nps",
            "点击率",
            "点击到注册率",
            "注册到激活率",
            "激活到付费率",
            "点击到付费率",
        ]
    ].reset_index(drop=True)
    payload = {
        "source": "deterministic_channel_source_aarrr_topn_selection",
        "top_n": int(len(selected)),
        "requested_top_n": int(top_n),
        "selection_rules": [
            "先按 operating_cost 取高消耗组合",
            "强制补入高 roi、低 roi、高 cac、低 retention_d7 异常组合",
            "异常项未入选时替换中性组合，总数保持 TopN",
        ],
        "selected": selected.to_dict(orient="records"),
    }
    return selected, payload


def _compact_number(value: Any) -> str:
    try:
        number = float(value)
    except Exception:
        return "0"
    abs_value = abs(number)
    if abs_value >= 100000000:
        return f"{number / 100000000:.1f}亿"
    if abs_value >= 10000:
        return f"{number / 10000:.1f}万"
    if abs_value >= 1000:
        return f"{number / 1000:.1f}千"
    return f"{number:.0f}"


def _percent(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except Exception:
        return "0.0%"


def _render_single_aarrr_axis(ax: Any, row: pd.Series, *, title_prefix: str = "") -> None:
    stages = [
        ("曝光", "impressions"),
        ("点击", "clicks"),
        ("注册", "registrations"),
        ("激活", "activations"),
        ("付费", "paid_users"),
    ]
    values = [max(float(row.get(column, 0) or 0), 0.0) for _, column in stages]
    max_value = max(values) or 1.0
    colors = ["#0f4c81", "#2563eb", "#0f766e", "#f59e0b", "#dc2626"]
    x_positions = np.arange(len(stages))
    ax.bar(x_positions, values, color=colors, alpha=0.82)
    ax.set_xticks(x_positions, [label for label, _ in stages], fontsize=8)
    ax.set_ylim(0, max_value * 1.35)
    for idx, value in enumerate(values):
        ax.text(idx, value + max_value * 0.035, _compact_number(value), ha="center", va="bottom", fontsize=7)
    rates = [
        ("点击率", row.get("点击率")),
        ("点注", row.get("点击到注册率")),
        ("注激", row.get("注册到激活率")),
        ("激付", row.get("激活到付费率")),
    ]
    rate_text = " / ".join(f"{name} {_percent(value)}" for name, value in rates)
    ax.text(
        0.02,
        0.96,
        rate_text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        color="#334155",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#d8e2ee", "alpha": 0.92},
    )
    revenue_text = f"收入 {_compact_number(row.get('revenue'))} / 成本 {_compact_number(row.get('operating_cost'))}"
    ax.text(0.02, 0.06, revenue_text, transform=ax.transAxes, ha="left", va="bottom", fontsize=7, color="#475569")
    combo = str(row.get("组合") or f"{row.get('channel')} / {row.get('traffic_source')}")
    title = f"{title_prefix}{combo}" if title_prefix else combo
    ax.set_title(title, fontsize=9, pad=6)
    ax.grid(axis="y", alpha=0.18)
    ax.tick_params(axis="y", labelsize=7)


def render_aarrr_small_multiples(
    frame: pd.DataFrame,
    png_path: Path,
    *,
    title: str,
    columns: int = 4,
    rows: int = 3,
    title_prefix_column: str | None = None,
) -> None:
    if frame.empty:
        return
    plt = setup_ops_matplotlib()
    page_size = rows * columns
    plot_data = frame.head(page_size).reset_index(drop=True)
    fig, axes = plt.subplots(rows, columns, figsize=(columns * 4.2, rows * 3.0))
    axes_array = np.asarray(axes).reshape(-1)
    for idx, ax in enumerate(axes_array):
        if idx >= len(plot_data):
            ax.axis("off")
            continue
        row = plot_data.iloc[idx]
        prefix = ""
        if title_prefix_column and title_prefix_column in row:
            prefix = f"{row.get(title_prefix_column)}. "
        _render_single_aarrr_axis(ax, row, title_prefix=prefix)
    fig.suptitle(title, fontsize=16, y=0.995)
    fig.text(
        0.03,
        0.012,
        "图注：每个小图是一组“渠道 × 流量来源”。柱高显示曝光、点击、注册、激活、付费的阶段规模；白色标签显示关键相邻转化率。具体数值和字段见图后配表。",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#334155",
    )
    fig.tight_layout(rect=(0, 0.045, 1, 0.965))
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=180)
    plt.close(fig)


def render_aarrr_all_pages(detail: pd.DataFrame, asset_dir: Path, *, rows: int = 3, columns: int = 3) -> list[Path]:
    if detail.empty:
        return []
    page_size = rows * columns
    paths: list[Path] = []
    for page_index, start in enumerate(range(0, len(detail), page_size), start=1):
        chunk = detail.iloc[start : start + page_size].reset_index(drop=True)
        png_path = asset_dir / f"ops_channel_source_aarrr_all_page_{page_index:02d}.png"
        render_aarrr_small_multiples(
            chunk,
            png_path,
            title=f"全量渠道 × 流量来源 AARRR 分页图组（第 {page_index}/{math.ceil(len(detail) / page_size)} 页）",
            columns=columns,
            rows=rows,
        )
        paths.append(png_path)
    return paths
