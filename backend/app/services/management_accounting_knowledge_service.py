from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.models import SmartReportRequest


KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "management_accounting_cards.json"


def _load_cards() -> list[dict[str, Any]]:
    with KNOWLEDGE_PATH.open("r", encoding="utf-8") as handle:
        cards = json.load(handle)
    return [dict(card) for card in cards]


def get_management_accounting_cards() -> list[dict[str, Any]]:
    return _load_cards()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def match_management_accounting_cards(
    *,
    dataset_name: str,
    request: SmartReportRequest,
    columns: list[str],
    limit: int = 4,
) -> list[dict[str, Any]]:
    joined = " ".join(
        [
            dataset_name,
            request.user_requirement,
            request.problem_to_solve,
            request.target_audience,
            request.core_purpose,
            request.expected_result,
            request.business_background_name,
            request.business_background_text,
            " ".join(columns),
        ]
    ).lower()
    scored: list[dict[str, Any]] = []
    for card in _load_cards():
        score = sum(1 for token in card.get("trigger_tokens", []) if token.lower() in joined)
        if score <= 0:
            continue
        scored.append({**card, "match_score": score})
    scored.sort(key=lambda item: (-int(item["match_score"]), item["title"]))
    if not scored:
        scored = _load_cards()
    return scored[:limit]


def _match_column(columns: list[str], token_groups: list[list[str]]) -> str | None:
    normalized = [(column, _normalize_text(column)) for column in columns]
    for group in token_groups:
        for column, lower in normalized:
            if all(token in lower for token in group):
                return column
    for group in token_groups:
        for column, lower in normalized:
            if any(token in lower for token in group):
                return column
    return None


def _pair_budget_actual_columns(columns: list[str]) -> list[tuple[str, str, str]]:
    budget_candidates = [column for column in columns if any(token in _normalize_text(column) for token in ["预算", "budget", "plan"])]
    actual_candidates = [column for column in columns if any(token in _normalize_text(column) for token in ["实际", "actual", "本期", "发生"])]
    pairs: list[tuple[str, str, str]] = []
    used_actual: set[str] = set()

    def _strip_tokens(text: str, tokens: list[str]) -> str:
        value = text
        for token in tokens:
            value = value.replace(token, "")
        return value.strip("_- /")

    for budget_col in budget_candidates:
        budget_norm = _normalize_text(budget_col)
        budget_stem = _strip_tokens(budget_norm, ["预算", "budget", "plan", "金额", "值", "额"])
        best_actual = None
        for actual_col in actual_candidates:
            if actual_col in used_actual:
                continue
            actual_norm = _normalize_text(actual_col)
            actual_stem = _strip_tokens(actual_norm, ["实际", "actual", "本期", "发生", "金额", "值", "额"])
            if budget_stem and actual_stem and budget_stem == actual_stem:
                best_actual = actual_col
                break
        if not best_actual and len(actual_candidates) == 1 and actual_candidates[0] not in used_actual:
            best_actual = actual_candidates[0]
        if not best_actual:
            continue
        used_actual.add(best_actual)
        label = budget_stem or _normalize_text(budget_col)
        pairs.append((label, budget_col, best_actual))
    return pairs[:6]


def _to_numeric(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() >= 0.6:
        return numeric
    if pd.api.types.is_numeric_dtype(series):
        return numeric
    cleaned = (
        series.astype(str)
        .str.replace(r"[£$,]", "", regex=True)
        .str.replace(r"[()]", "", regex=True)
        .str.replace(r"\s+", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0, 0.0):
        return None
    try:
        value = float(numerator) / float(denominator)
    except Exception:
        return None
    if not np.isfinite(value):
        return None
    return value


def _sum_column(frame: pd.DataFrame, column: str | None) -> float | None:
    if not column or column not in frame.columns:
        return None
    series = _to_numeric(frame[column]).dropna()
    if series.empty:
        return None
    return float(series.sum())


def build_management_accounting_context(
    *,
    frame: pd.DataFrame,
    request: SmartReportRequest,
    dataset_name: str,
    program_bundle: dict[str, Any],
) -> dict[str, Any] | None:
    task_model = program_bundle.get("task_model", {})
    family = str(task_model.get("primary_family") or "")
    columns = frame.columns.astype(str).tolist()
    joined_columns = " ".join(columns).lower()
    finance_tokens = ["收入", "利润", "成本", "费用", "资产", "负债", "现金", "预算", "actual", "budget", "profit", "cash", "asset", "liability"]
    if family not in {"management_accounting_review", "procurement_sales_review"} and not any(token in joined_columns for token in finance_tokens):
        return None

    cards = match_management_accounting_cards(dataset_name=dataset_name, request=request, columns=columns, limit=5)

    revenue_col = _match_column(columns, [["营业收入"], ["收入"], ["revenue"], ["sales"], ["amount"], ["value involved"], ["spend"]])
    cost_col = _match_column(columns, [["营业成本"], ["成本"], ["cogs"], ["cost"]])
    gross_profit_col = _match_column(columns, [["毛利"], ["gross", "profit"]])
    operating_profit_col = _match_column(columns, [["营业利润"], ["operating", "profit"], ["ebit"]])
    net_profit_col = _match_column(columns, [["净利润"], ["profit"], ["盈余"]])
    cash_col = _match_column(columns, [["经营现金流"], ["现金流"], ["cash"]])
    receivable_col = _match_column(columns, [["应收"], ["receivable"]])
    payable_col = _match_column(columns, [["应付"], ["payable"]])
    inventory_col = _match_column(columns, [["存货"], ["inventory"]])
    assets_col = _match_column(columns, [["总资产"], ["资产"], ["assets"]])
    liabilities_col = _match_column(columns, [["总负债"], ["负债"], ["liabilities"]])
    equity_col = _match_column(columns, [["所有者权益"], ["权益"], ["equity"]])
    entity_col = _match_column(
        columns,
        [["事业部"], ["部门"], ["责任中心"], ["成本中心"], ["利润中心"], ["主体"], ["公司"], ["产品线"], ["supplier"], ["vendor"], ["supplier information"], ["entity"], ["segment"]],
    )

    revenue_total = _sum_column(frame, revenue_col)
    cost_total = _sum_column(frame, cost_col)
    gross_profit_total = _sum_column(frame, gross_profit_col)
    operating_profit_total = _sum_column(frame, operating_profit_col)
    net_profit_total = _sum_column(frame, net_profit_col)
    cash_total = _sum_column(frame, cash_col)
    assets_total = _sum_column(frame, assets_col)
    liabilities_total = _sum_column(frame, liabilities_col)
    equity_total = _sum_column(frame, equity_col)
    receivable_total = _sum_column(frame, receivable_col)
    inventory_total = _sum_column(frame, inventory_col)
    payable_total = _sum_column(frame, payable_col)

    if gross_profit_total is None and revenue_total is not None and cost_total is not None:
        gross_profit_total = revenue_total - cost_total

    margin_rows: list[dict[str, Any]] = []
    for label, numerator in [
        ("毛利率", gross_profit_total),
        ("营业利润率", operating_profit_total),
        ("净利率", net_profit_total),
        ("经营现金流/收入", cash_total),
    ]:
        ratio = _safe_div(numerator, revenue_total)
        if ratio is None:
            continue
        margin_rows.append({"指标": label, "值": ratio, "解释": "用来判断收入规模之外的盈利质量与现金含量。"})

    leverage_rows: list[dict[str, Any]] = []
    asset_liability_ratio = _safe_div(liabilities_total, assets_total)
    debt_equity_ratio = _safe_div(liabilities_total, equity_total)
    if asset_liability_ratio is not None:
        leverage_rows.append({"指标": "资产负债率", "值": asset_liability_ratio, "解释": "衡量资产中有多少比例由负债支持。"})
    if debt_equity_ratio is not None:
        leverage_rows.append({"指标": "负债权益比", "值": debt_equity_ratio, "解释": "衡量财务杠杆和权益缓冲厚度。"})

    working_capital_rows: list[dict[str, Any]] = []
    if receivable_total is not None:
        working_capital_rows.append({"项目": "应收类占用", "金额": receivable_total, "解释": "回款慢会直接占用现金。"})
    if inventory_total is not None:
        working_capital_rows.append({"项目": "存货占用", "金额": inventory_total, "解释": "备货与周转节奏会影响现金占压。"})
    if payable_total is not None:
        working_capital_rows.append({"项目": "应付支撑", "金额": payable_total, "解释": "供应商信用会缓冲资金压力。"})
    if any(value is not None for value in [receivable_total, inventory_total, payable_total]):
        proxy = (receivable_total or 0.0) + (inventory_total or 0.0) - (payable_total or 0.0)
        working_capital_rows.append({"项目": "营运资本占用代理值", "金额": proxy, "解释": "应收加存货减应付，帮助判断增长是否在吞噬现金。"})

    budget_rows: list[dict[str, Any]] = []
    for label, budget_col, actual_col in _pair_budget_actual_columns(columns):
        budget_total = _sum_column(frame, budget_col)
        actual_total = _sum_column(frame, actual_col)
        if budget_total is None or actual_total is None:
            continue
        variance = actual_total - budget_total
        variance_rate = _safe_div(variance, budget_total)
        budget_rows.append(
            {
                "预算主题": label or actual_col,
                "预算值": budget_total,
                "实际值": actual_total,
                "偏差额": variance,
                "偏差率": variance_rate,
            }
        )
    budget_rows.sort(key=lambda row: abs(float(row["偏差额"])), reverse=True)
    budget_rows = budget_rows[:8]

    slice_rows: list[dict[str, Any]] = []
    if entity_col and revenue_col:
        grouped = (
            frame[[entity_col, revenue_col] + ([net_profit_col] if net_profit_col else [])]
            .copy()
            .assign(**{revenue_col: _to_numeric(frame[revenue_col])})
        )
        if net_profit_col:
            grouped[net_profit_col] = _to_numeric(frame[net_profit_col])
        grouped = grouped.dropna(subset=[entity_col, revenue_col])
        if not grouped.empty:
            agg_map = {revenue_col: "sum"}
            if net_profit_col:
                agg_map[net_profit_col] = "sum"
            summary = (
                grouped.groupby(entity_col, dropna=False)
                .agg(agg_map)
                .reset_index()
                .sort_values(revenue_col, ascending=False)
                .head(8)
            )
            total_revenue = float(summary[revenue_col].sum()) if not summary.empty else 0.0
            for _, row in summary.iterrows():
                slice_rows.append(
                    {
                        "经营切片": str(row[entity_col]),
                        "收入合计": float(row[revenue_col]),
                        "收入占比": _safe_div(float(row[revenue_col]), total_revenue),
                        **({"净利润合计": float(row[net_profit_col])} if net_profit_col else {}),
                    }
                )

    totals_rows: list[dict[str, Any]] = []
    for label, value in [
        ("收入总量", revenue_total),
        ("成本总量", cost_total),
        ("毛利总量", gross_profit_total),
        ("营业利润总量", operating_profit_total),
        ("净利润总量", net_profit_total),
        ("经营现金流总量", cash_total),
        ("资产总量", assets_total),
        ("负债总量", liabilities_total),
        ("权益总量", equity_total),
    ]:
        if value is None:
            continue
        totals_rows.append({"指标": label, "数值": value})

    summary_bullets: list[str] = []
    if revenue_total is not None and revenue_total > 0:
        summary_bullets.append(f"当前样本可先按支出/金额总盘子复盘，核心金额约为 {revenue_total:,.2f}。")
    if revenue_total is not None and net_profit_total is not None:
        margin = _safe_div(net_profit_total, revenue_total)
        if margin is not None:
            summary_bullets.append(f"当前样本收入总量与净利润总量可联动复盘，净利率约为 {margin:.1%}，适合先区分规模增长和质量增长。")
    if budget_rows:
        top_budget = budget_rows[0]
        direction = "超预算" if float(top_budget["偏差额"]) > 0 else "低于预算"
        summary_bullets.append(f"预算执行偏差最大的主题是 {top_budget['预算主题']}，当前 {direction}，应优先做偏差归因。")
    if working_capital_rows:
        summary_bullets.append("当前数据已具备营运资本复盘条件，建议把应收、存货、应付与利润一起看，避免只看利润不看现金压力。")
    if leverage_rows:
        top_leverage = leverage_rows[0]
        summary_bullets.append(f"当前财务结构可直接进入杠杆与偿债压力复盘，优先指标为 {top_leverage['指标']}。")
    if slice_rows:
        summary_bullets.append(f"经营切片层已有明显头部对象，建议先围绕 {slice_rows[0]['经营切片']} 做第一轮责任归属与支出集中度排查。")

    return {
        "cards": cards,
        "summary_bullets": summary_bullets,
        "totals_rows": totals_rows,
        "margin_rows": margin_rows,
        "budget_rows": budget_rows,
        "working_capital_rows": working_capital_rows,
        "leverage_rows": leverage_rows,
        "slice_rows": slice_rows,
        "detected_columns": {
            "revenue": revenue_col,
            "cost": cost_col,
            "gross_profit": gross_profit_col,
            "operating_profit": operating_profit_col,
            "net_profit": net_profit_col,
            "cash": cash_col,
            "receivable": receivable_col,
            "payable": payable_col,
            "inventory": inventory_col,
            "assets": assets_col,
            "liabilities": liabilities_col,
            "equity": equity_col,
            "entity": entity_col,
        },
    }
