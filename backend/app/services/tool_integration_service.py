from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

from app.services.path_service import PUBLIC_ARTIFACTS_DIR, REPORTS_DIR


def _asset_slug(dataset_id: str, sheet_name: str) -> str:
    return f"{dataset_id}-{sheet_name}-{uuid.uuid4().hex[:8]}"


def _asset_dir(dataset_id: str, sheet_name: str) -> Path:
    path = REPORTS_DIR / f"tool-assets-{_asset_slug(dataset_id, sheet_name)}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _public_path(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(PUBLIC_ARTIFACTS_DIR).as_posix()
        return f"/storage/{relative}"
    except ValueError:
        return ""


def generate_tool_assets(
    *,
    dataset_id: str,
    dataset_name: str,
    sheet_name: str,
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    asset_dir = _asset_dir(dataset_id, sheet_name)
    integrations: list[dict[str, Any]] = []

    integrations.extend(_generate_sweetviz_asset(asset_dir, dataset_name, sheet_name, frame))
    integrations.extend(_generate_missingno_assets(asset_dir, sheet_name, frame))
    integrations.extend(_generate_plotly_assets(asset_dir, sheet_name, frame))
    integrations.extend(_generate_evidently_assets(asset_dir, sheet_name, frame))

    return integrations


def _generate_sweetviz_asset(asset_dir: Path, dataset_name: str, sheet_name: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    import sweetviz as sv

    target = asset_dir / f"sweetviz-{sheet_name}.html"
    report = sv.analyze(frame)
    report.show_html(filepath=str(target), open_browser=False, layout="widescreen", scale=None)
    return [
        {
            "tool_name": "Sweetviz",
            "repo_url": "https://github.com/fbdesignpro/sweetviz",
            "asset_type": "html",
            "title": f"{dataset_name} / {sheet_name} Sweetviz profile",
            "path": _public_path(target),
            "note": "自动 EDA HTML 报告，适合快速浏览字段分布和目标关系。",
        }
    ]


def _generate_missingno_assets(asset_dir: Path, sheet_name: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    import matplotlib.pyplot as plt
    import missingno as msno

    assets: list[dict[str, Any]] = []

    matrix_path = asset_dir / f"missingno-matrix-{sheet_name}.png"
    ax = msno.matrix(frame, figsize=(12, 5), sparkline=False)
    ax.figure.tight_layout()
    ax.figure.savefig(matrix_path, dpi=180, bbox_inches="tight")
    plt.close(ax.figure)
    assets.append(
        {
            "tool_name": "missingno",
            "repo_url": "https://github.com/ResidentMario/missingno",
            "asset_type": "image",
            "title": f"{sheet_name} missingness matrix",
            "path": _public_path(matrix_path),
            "note": "用缺失矩阵快速看数据空洞、列块缺失和记录连续性。",
        }
    )

    bar_path = asset_dir / f"missingno-bar-{sheet_name}.png"
    ax = msno.bar(frame, figsize=(12, 5), fontsize=10)
    ax.figure.tight_layout()
    ax.figure.savefig(bar_path, dpi=180, bbox_inches="tight")
    plt.close(ax.figure)
    assets.append(
        {
            "tool_name": "missingno",
            "repo_url": "https://github.com/ResidentMario/missingno",
            "asset_type": "image",
            "title": f"{sheet_name} missingness bar",
            "path": _public_path(bar_path),
            "note": "从列维度展示缺失量级，适合定位优先治理字段。",
        }
    )

    return assets


def _generate_plotly_assets(asset_dir: Path, sheet_name: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    import plotly.express as px

    from app.services.dataset_service import numeric_columns

    assets: list[dict[str, Any]] = []
    numeric = [column for column in numeric_columns(frame) if column in frame.columns][:4]
    if len(numeric) >= 2:
        scatter_path = asset_dir / f"plotly-scatter-{sheet_name}.html"
        sample = frame[numeric[:2]].dropna().head(2000).copy()
        fig = px.scatter(
            sample,
            x=numeric[0],
            y=numeric[1],
            title=f"{sheet_name}: {numeric[0]} vs {numeric[1]}",
            opacity=0.6,
        )
        fig.write_html(str(scatter_path), include_plotlyjs="cdn", full_html=True)
        assets.append(
            {
                "tool_name": "Plotly",
                "repo_url": "https://github.com/plotly/plotly.py",
                "asset_type": "html",
                "title": f"{sheet_name} interactive scatter",
                "path": _public_path(scatter_path),
                "note": "交互式散点图，适合放大查看局部聚集与极端样本。",
            }
        )
    if numeric:
        hist_path = asset_dir / f"plotly-hist-{sheet_name}.html"
        sample = frame[[numeric[0]]].dropna().head(5000).copy()
        fig = px.histogram(sample, x=numeric[0], title=f"{sheet_name}: {numeric[0]} distribution")
        fig.write_html(str(hist_path), include_plotlyjs="cdn", full_html=True)
        assets.append(
            {
                "tool_name": "Plotly",
                "repo_url": "https://github.com/plotly/plotly.py",
                "asset_type": "html",
                "title": f"{sheet_name} interactive histogram",
                "path": _public_path(hist_path),
                "note": "交互式分布图，适合看长尾、偏态和离群区间。",
            }
        )
    return assets


def _generate_evidently_assets(asset_dir: Path, sheet_name: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    from evidently import Report
    from evidently.presets import DataSummaryPreset

    snapshot = Report([DataSummaryPreset()]).run(current_data=frame)
    target = asset_dir / f"evidently-summary-{sheet_name}.html"
    snapshot.save_html(str(target))

    summary_dict = snapshot.dump_dict()
    metric_cards: list[dict[str, Any]] = []
    for item in summary_dict.get("metric_results", {}).values():
        display_name = item.get("display_name")
        value = item.get("value")
        if display_name and isinstance(value, dict):
            metric_cards.append({"name": display_name, "value": value})
        if len(metric_cards) >= 4:
            break

    return [
        {
            "tool_name": "Evidently",
            "repo_url": "https://github.com/evidentlyai/evidently",
            "asset_type": "html",
            "title": f"{sheet_name} evidently summary",
            "path": _public_path(target),
            "note": "标准化数据总结 HTML，可作为额外的质量与数据画像视角。",
            "summary_cards": metric_cards,
        }
    ]
