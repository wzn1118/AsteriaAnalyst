from __future__ import annotations

from statistics import median
from typing import Any


def _parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() == "n/a":
        return None
    if text.endswith("%"):
        try:
            return float(text[:-1]) / 100.0
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def _sales_share(row: dict[str, Any]) -> float:
    return _parse_number(row.get("销售额占比")) or 0.0


def _customer_count(row: dict[str, Any]) -> float:
    return _parse_number(row.get("客户覆盖")) or 0.0


def _order_count(row: dict[str, Any]) -> float:
    return _parse_number(row.get("订单覆盖")) or 0.0


def _repeat_share(row: dict[str, Any]) -> float:
    return _parse_number(row.get("复购客户占比")) or 0.0


def _risk_score(row: dict[str, Any]) -> float:
    low_review = _parse_number(row.get("低分评价占比")) or 0.0
    late_rate = _parse_number(row.get("逾期率")) or 0.0
    return low_review + late_rate


def _representative_middle_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(rows) < 3:
        return rows[0] if rows else None
    body = rows[1:-1]
    if not body:
        return rows[len(rows) // 2]

    candidate_pool = [
        row for row in body
        if _customer_count(row) >= 20 or _order_count(row) >= 20 or _sales_share(row) >= 0.001
    ]
    if not candidate_pool:
        candidate_pool = body

    sales_values = [_sales_share(row) for row in candidate_pool if _sales_share(row) > 0]
    customer_values = [_customer_count(row) for row in candidate_pool if _customer_count(row) > 0]
    order_values = [_order_count(row) for row in candidate_pool if _order_count(row) > 0]
    repeat_values = [_repeat_share(row) for row in candidate_pool if _repeat_share(row) > 0]

    target_sales = median(sales_values) if sales_values else 0.0
    target_customers = median(customer_values) if customer_values else 0.0
    target_orders = median(order_values) if order_values else 0.0
    target_repeat = median(repeat_values) if repeat_values else 0.0

    def score(row: dict[str, Any]) -> float:
        sales = _sales_share(row)
        customers = _customer_count(row)
        orders = _order_count(row)
        repeat = _repeat_share(row)
        sales_gap = abs(sales - target_sales) / (target_sales + 1e-6)
        customer_gap = abs(customers - target_customers) / (target_customers + 1.0)
        order_gap = abs(orders - target_orders) / (target_orders + 1.0)
        repeat_gap = abs(repeat - target_repeat) / (target_repeat + 1e-6) if target_repeat > 0 else 0.0
        return sales_gap + customer_gap + order_gap + repeat_gap

    return min(candidate_pool, key=score)


def _representative_tail_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    positive_rows = [row for row in rows if _sales_share(row) > 0]
    if positive_rows:
        return min(positive_rows, key=lambda row: (_sales_share(row), _customer_count(row), _order_count(row)))
    return rows[-1]


def representative_rows_for_dimension(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any] | None]:
    if not rows:
        return {"head": None, "middle": None, "tail": None}
    return {
        "head": rows[0],
        "middle": _representative_middle_row(rows),
        "tail": _representative_tail_row(rows),
    }


def build_procurement_sales_relation_context(rows_by_dimension: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    dimension_profiles: list[dict[str, Any]] = []
    relation_findings: list[str] = []

    for dimension in ["品类", "商品", "SKU", "供应商"]:
        rows = rows_by_dimension.get(dimension) or []
        if not rows:
            continue
        representative_rows = representative_rows_for_dimension(rows)
        head = representative_rows["head"]
        middle = representative_rows["middle"]
        tail = representative_rows["tail"]
        profile = {
            "dimension": dimension,
            "row_count": len(rows),
            "head": head,
            "middle": middle,
            "tail": tail,
        }
        dimension_profiles.append(profile)

        if head and middle and head.get("对象") != middle.get("对象"):
            relation_findings.append(
                f"{dimension}层头部是 `{head.get('对象')}`，中位代表是 `{middle.get('对象')}`，说明这层不是单一头部结构，需要把头部打法和中段承接拆开看。"
            )
        if tail and tail.get("对象") not in {head.get("对象"), middle.get("对象") if middle else None}:
            relation_findings.append(
                f"{dimension}层底部对象是 `{tail.get('对象')}`，更适合单独看清理或止损边界，而不是混在观察池里。"
            )

    supplier_rows = rows_by_dimension.get("供应商") or []
    if supplier_rows:
        sales_head = supplier_rows[0]
        customer_head = max(supplier_rows, key=_customer_count)
        if customer_head.get("对象") != sales_head.get("对象"):
            relation_findings.append(
                f"供应商层存在“双头部”：结果贡献头部是 `{sales_head.get('对象')}`，客户承接头部是 `{customer_head.get('对象')}`，后续动作不能只跟着销售额走。"
            )

    return {
        "dimension_profiles": dimension_profiles,
        "relation_findings": relation_findings[:12],
    }
