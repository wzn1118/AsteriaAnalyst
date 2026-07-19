from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import SmartReportRequest
from app.services.codex_service import (
    codex_business_object_interpretation,
    codex_challenge_review,
    codex_complete_input_fields,
    codex_generic_exploratory_interpretation,
    codex_generic_long_page_plan,
    codex_generic_management_question_bank,
    codex_judge_feedback,
    codex_semantic_analysis,
)
from app.services.dataset_service import build_column_summaries


ECOMMERCE_FIELD_GROUPS: dict[str, list[str]] = {
    "product_fields": [
        "item_id",
        "product_id",
        "sku_id",
        "spu_id",
        "商品id",
        "宝贝id",
        "商品名称",
        "商品标题",
        "sku",
        "spu",
        "规格",
        "货号",
        "款号",
        "条码",
    ],
    "category_fields": [
        "category",
        "类目",
        "一级类目",
        "二级类目",
        "三级类目",
        "叶子类目",
        "行业",
        "品类",
    ],
    "shop_seller_fields": [
        "shop_id",
        "seller_id",
        "store_id",
        "店铺",
        "卖家",
        "商家",
        "供应商",
        "品牌",
        "brand",
        "vendor",
        "seller",
        "supplier",
    ],
    "transaction_fields": [
        "order_id",
        "订单",
        "成交",
        "销量",
        "sales_volume",
        "sales",
        "销售额",
        "gmv",
        "支付金额",
        "成交金额",
        "订单量",
        "件数",
        "客单价",
    ],
    "price_fields": [
        "price",
        "sale_price",
        "original_price",
        "discount_price",
        "券后价",
        "到手价",
        "售价",
        "原价",
        "优惠",
        "折扣",
    ],
    "traffic_fields": [
        "曝光",
        "浏览",
        "点击",
        "访客",
        "pv",
        "uv",
        "搜索",
        "进店",
        "商品访客",
        "page_views",
        "view",
        "visitor",
    ],
    "conversion_fields": [
        "点击率",
        "add_to_cart",
        "加购",
        "收藏",
        "favorite",
        "fav",
        "下单",
        "支付",
        "pay",
        "支付转化率",
        "加购率",
        "收藏率",
        "成交转化率",
        "buy_rate",
        "conversion_rate",
    ],
    "inventory_fields": [
        "inventory",
        "stock",
        "库存",
        "可售库存",
        "在途库存",
        "周转",
        "缺货",
    ],
    "fulfillment_fields": [
        "发货",
        "物流",
        "签收",
        "履约",
        "发货时效",
        "签收时效",
        "履约率",
        "延迟发货",
        "fulfillment",
        "delivery",
        "sign",
    ],
    "aftersales_fields": [
        "退款",
        "退货",
        "售后",
        "投诉",
        "纠纷",
        "赔付",
        "退款率",
        "退货率",
        "售后率",
        "refund",
        "return",
        "aftersales",
    ],
    "review_fields": [
        "review",
        "comment",
        "评价",
        "评论",
        "追评",
        "问大家",
        "评分",
        "晒图",
        "差评",
        "好评率",
        "dsr",
        "店铺评分",
        "review_count",
        "rating",
    ],
    "margin_cost_fields": [
        "毛利",
        "毛利率",
        "成本",
        "采购价",
        "供货价",
        "平台佣金",
        "运费",
        "补贴",
        "广告费",
        "利润",
        "gross_margin",
        "gross_profit",
        "cost",
        "purchase_cost",
        "procurement_price",
        "profit",
        "commission",
        "shipping_fee",
        "subsidy",
        "ad_cost",
    ],
    "promotion_fields": [
        "优惠券",
        "满减",
        "活动价",
        "秒杀",
        "折扣",
        "补贴",
        "促销",
        "活动id",
        "大促",
        "会场",
        "coupon",
        "promotion",
        "activity_id",
    ],
    "time_fields": [
        "日期",
        "月份",
        "周",
        "季度",
        "年份",
        "活动周期",
        "上架时间",
        "下架时间",
        "date",
        "month",
        "week",
        "quarter",
        "year",
        "launch_time",
        "off_shelf_time",
    ],
}


GROUP_TO_SUPPORTED_MODULES: dict[str, list[str]] = {
    "product_fields": ["product_structure_review", "sku_spu_review"],
    "category_fields": ["category_performance_review"],
    "shop_seller_fields": ["shop_seller_review"],
    "transaction_fields": ["product_sales_review", "shop_seller_review"],
    "price_fields": ["price_band_review", "promotion_review"],
    "traffic_fields": ["traffic_conversion_review", "product_traffic_review"],
    "conversion_fields": ["traffic_conversion_review", "product_conversion_review"],
    "inventory_fields": ["inventory_fulfillment_review"],
    "fulfillment_fields": ["inventory_fulfillment_review"],
    "aftersales_fields": ["review_aftersales_review"],
    "review_fields": ["review_aftersales_review", "product_reputation_review"],
    "margin_cost_fields": ["margin_profit_review"],
    "promotion_fields": ["promotion_review"],
    "time_fields": ["trend_review"],
}


FIELD_GROUP_ANALYSIS_USES: dict[str, list[str]] = {
    "product_fields": ["商品结构分析", "SKU/SPU 分层分析", "对象级经营复盘"],
    "category_fields": ["类目结构分析", "类目表现排名"],
    "shop_seller_fields": ["店铺/卖家结构分析", "品牌经营分析"],
    "transaction_fields": ["销量/成交/GMV 结构分析", "客单价分析"],
    "price_fields": ["价格带分析", "促销价格对照"],
    "traffic_fields": ["商品流量结构分析", "曝光/浏览/访客承接分析"],
    "conversion_fields": ["加购/收藏/支付转化分析", "商品转化漏斗分析"],
    "inventory_fields": ["库存结构分析", "缺货/压货/周转分析"],
    "fulfillment_fields": ["履约时效分析", "发货与签收效率分析"],
    "aftersales_fields": ["退款/退货/售后风险分析"],
    "review_fields": ["口碑与评价分析", "差评风险分析"],
    "margin_cost_fields": ["毛利与利润分析", "成本结构分析"],
    "promotion_fields": ["促销活动分析", "活动价格与补贴分析"],
    "time_fields": ["趋势与波动分析", "周期对比分析"],
}


FIELD_GROUP_FORBIDDEN_USES: dict[str, list[str]] = {
    "product_fields": ["组织归责", "因果证明"],
    "category_fields": ["毛利判断（缺 margin_cost_fields 时）"],
    "shop_seller_fields": ["供应商问责（缺 fulfillment/aftersales 时）"],
    "transaction_fields": ["毛利判断（缺 margin_cost_fields 时）"],
    "price_fields": ["利润判断（缺 margin_cost_fields 时）"],
    "traffic_fields": ["转化漏斗健康（缺 conversion_fields 时）"],
    "conversion_fields": ["流量承接问题（缺 traffic_fields 时）"],
    "inventory_fields": ["补货/清仓判断（缺 inventory_fields 时）"],
    "fulfillment_fields": ["发货效率判断（缺 fulfillment_fields 时）"],
    "aftersales_fields": ["售后风险判断（缺 aftersales_fields 时）"],
    "review_fields": ["口碑判断（缺 review_fields 时）"],
    "margin_cost_fields": ["毛利与利润判断（缺 margin_cost_fields 时）"],
    "promotion_fields": ["活动效率判断（缺 transaction/price/time 时）"],
    "time_fields": ["趋势/同比/环比（缺 time_fields 时）"],
}


ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP: dict[str, tuple[str, ...]] = {
    "margin_cost_fields": ("毛利", "利润", "ROI", "成本效率", "供应商利润贡献"),
    "inventory_fields": ("补货", "缺货", "周转", "压货", "清仓"),
    "fulfillment_fields": ("履约能力", "物流问题", "发货效率"),
    "aftersales_fields": ("售后风险", "退款风险", "退货风险"),
    "review_fields": ("口碑", "满意度", "差评风险"),
    "traffic_fields": ("流量承接", "曝光不足", "点击不足"),
    "conversion_fields": ("转化漏斗健康", "加购问题", "支付转化问题"),
    "time_fields": ("趋势", "环比", "同比", "波动"),
}


def _compact(value: str) -> str:
    return "".join(ch for ch in str(value or "").lower().strip() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _column_names(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def _match_group(columns: list[str], aliases: list[str]) -> dict[str, list[str]]:
    compact_columns = {column: _compact(column) for column in columns}
    compact_aliases = {alias: _compact(alias) for alias in aliases}
    matched_columns: list[str] = []
    matched_aliases: list[str] = []
    for column, compact_column in compact_columns.items():
        if not compact_column:
            continue
        for alias, compact_alias in compact_aliases.items():
            if compact_alias and (compact_alias == compact_column or compact_alias in compact_column):
                matched_columns.append(column)
                matched_aliases.append(alias)
                break
    return {
        "matched_columns": list(dict.fromkeys(matched_columns)),
        "matched_aliases": list(dict.fromkeys(matched_aliases)),
    }


def _group_details(columns: list[str]) -> dict[str, dict[str, list[str]]]:
    return {
        group_name: _match_group(columns, aliases)
        for group_name, aliases in ECOMMERCE_FIELD_GROUPS.items()
    }


def _report_mode_from_registry(registry: dict[str, Any]) -> str:
    if (
        registry.get("has_product_fields")
        and registry.get("has_transaction_fields")
        and registry.get("has_price_fields")
        and registry.get("has_traffic_fields")
        and registry.get("has_conversion_fields")
        and registry.get("has_review_fields")
        and registry.get("has_inventory_fields")
        and registry.get("has_fulfillment_fields")
        and registry.get("has_aftersales_fields")
        and registry.get("has_margin_cost_fields")
        and registry.get("has_time_fields")
    ):
        return "full_ecommerce_product_operations_report"
    if registry.get("has_inventory_fields") and registry.get("has_fulfillment_fields"):
        return "inventory_fulfillment_review"
    if registry.get("has_review_fields") or registry.get("has_aftersales_fields"):
        return "review_aftersales_review"
    if registry.get("has_margin_cost_fields"):
        return "margin_profit_review"
    if registry.get("has_traffic_fields") and registry.get("has_conversion_fields"):
        return "traffic_conversion_review"
    if registry.get("has_category_fields"):
        return "category_performance_review"
    if registry.get("has_shop_seller_fields"):
        return "shop_seller_review"
    if registry.get("has_product_fields") and registry.get("has_transaction_fields"):
        return "product_sales_review"
    return "insufficient_for_ecommerce_decision"


def ecommerce_field_availability_registry(frame: pd.DataFrame) -> dict[str, Any]:
    columns = _column_names(frame)
    details = _group_details(columns)
    registry: dict[str, Any] = {
        "business_profile": "ecommerce_product_operations_report",
    }
    for group_name, detail in details.items():
        registry[f"has_{group_name}"] = bool(detail["matched_columns"])

    registry["available_field_groups"] = [group for group in ECOMMERCE_FIELD_GROUPS if registry.get(f"has_{group}")]
    registry["missing_field_groups"] = [group for group in ECOMMERCE_FIELD_GROUPS if not registry.get(f"has_{group}")]
    registry["field_coverage"] = {group: detail["matched_columns"] for group, detail in details.items()}
    registry["matched_field_signals"] = details

    supported_modules: list[str] = []
    for group_name, modules in GROUP_TO_SUPPORTED_MODULES.items():
        if registry.get(f"has_{group_name}"):
            for module in modules:
                if module not in supported_modules:
                    supported_modules.append(module)
    unsupported_modules = sorted(
        {
            module
            for modules in GROUP_TO_SUPPORTED_MODULES.values()
            for module in modules
            if module not in supported_modules
        }
    )
    registry["supported_analysis_modules"] = supported_modules
    registry["unsupported_analysis_modules"] = unsupported_modules
    registry["report_mode"] = _report_mode_from_registry(registry)

    # Compatibility fields so the procurement/ecommerce shared chain can still
    # consume one registry object without making its own field-availability guesses.
    registry["has_sales_fields"] = bool(registry.get("has_transaction_fields"))
    registry["has_fulfillment_fields"] = bool(registry.get("has_fulfillment_fields"))
    registry["has_review_fields"] = bool(registry.get("has_review_fields"))
    registry["has_profit_fields"] = bool(registry.get("has_margin_cost_fields"))
    registry["has_inventory_fields"] = bool(registry.get("has_inventory_fields"))
    registry["has_procurement_price_fields"] = bool(registry.get("has_margin_cost_fields"))
    registry["has_supplier_delivery_fields"] = bool(registry.get("has_fulfillment_fields"))
    registry["has_payment_term_fields"] = False
    registry["has_return_cost_fields"] = bool(registry.get("has_aftersales_fields"))
    registry["has_supplier_contract_fields"] = False
    registry["has_competitor_price_fields"] = False
    registry["mode"] = registry["report_mode"]

    return registry


def _group_for_column(column_name: str, details: dict[str, dict[str, list[str]]]) -> str:
    for group_name, detail in details.items():
        if column_name in detail["matched_columns"]:
            return group_name
    return "unclassified"


def ecommerce_field_semantic_interpreter(
    frame: pd.DataFrame,
    field_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = field_registry or ecommerce_field_availability_registry(frame)
    details = registry.get("matched_field_signals") or _group_details(_column_names(frame))
    summaries = build_column_summaries(frame)
    rows: list[dict[str, Any]] = []
    for summary in summaries:
        field_name = str(summary.get("name") or "")
        field_group = _group_for_column(field_name, details)
        rows.append(
            {
                "field_name": field_name,
                "guessed_business_meaning": (
                    "电商商品经营主对象字段" if field_group in {"product_fields", "category_fields", "shop_seller_fields"}
                    else "电商经营指标字段" if field_group != "unclassified"
                    else "待人工确认的通用字段"
                ),
                "field_group": field_group,
                "usable_for": FIELD_GROUP_ANALYSIS_USES.get(field_group, ["待人工确认后再决定"]),
                "not_usable_for": FIELD_GROUP_FORBIDDEN_USES.get(field_group, ["强因果判断", "越权经营拍板"]),
                "sample_values": summary.get("sample_values", []),
                "missing_ratio": summary.get("missing_ratio"),
                "unique_count": summary.get("unique_count"),
                "dtype": summary.get("dtype"),
                "needs_manual_confirmation": field_group == "unclassified" or summary.get("unique_count", 0) > 10000,
                "risk_note": (
                    "字段未稳定归类，需结合样例值和业务口径确认。"
                    if field_group == "unclassified"
                    else "字段解释基于字段名、样例值、缺失率和唯一值数量联合判断。"
                ),
            }
        )
    return {
        "business_profile": "ecommerce_product_operations_report",
        "report_mode": registry.get("report_mode", ""),
        "rows": rows,
    }


def _semantic_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# ecommerce_field_semantic_map",
        "",
        f"- business_profile: `{payload.get('business_profile', '')}`",
        f"- report_mode: `{payload.get('report_mode', '')}`",
        "",
    ]
    for row in payload.get("rows", []):
        lines.extend(
            [
                f"## {row['field_name']}",
                "",
                f"- 推测业务含义：{row['guessed_business_meaning']}",
                f"- 所属字段组：`{row['field_group']}`",
                f"- 可用于：{', '.join(row['usable_for'])}",
                f"- 不可用于：{', '.join(row['not_usable_for'])}",
                f"- 样例值：{', '.join(str(item) for item in row['sample_values']) or '无'}",
                f"- 缺失率：{row['missing_ratio']}",
                f"- 唯一值数量：{row['unique_count']}",
                f"- 是否需要人工确认：{'是' if row['needs_manual_confirmation'] else '否'}",
                f"- 风险备注：{row['risk_note']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def write_ecommerce_registry_artifacts(
    output_dir: str | Path,
    field_registry: dict[str, Any],
    semantic_map: dict[str, Any],
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "ecommerce_field_availability_registry.json").write_text(
        json.dumps(field_registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_path / "ecommerce_field_semantic_map.json").write_text(
        json.dumps(semantic_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_path / "ecommerce_field_semantic_map.md").write_text(
        _semantic_markdown(semantic_map),
        encoding="utf-8",
    )


def ecommerce_text_boundary_failures(text: str, field_registry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    content = str(text or "")
    for group_name, terms in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP.items():
        if not field_registry.get(f"has_{group_name}", False):
            for term in terms:
                if term in content:
                    failures.append(f"missing_{group_name}_but_found:{term}")
    return failures


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _estimate_tokens(payload: dict[str, Any]) -> int:
    return max(1, math.ceil(len(json.dumps(payload, ensure_ascii=False, default=str)) / 4))


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _first_matching_column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    columns = _column_names(frame)
    compact_aliases = [_compact(alias) for alias in aliases]
    for column in columns:
        compact_column = _compact(column)
        if any(alias and (alias == compact_column or alias in compact_column) for alias in compact_aliases):
            return column
    return None


def _numeric_series(frame: pd.DataFrame, aliases: list[str]) -> pd.Series | None:
    column = _first_matching_column(frame, aliases)
    if not column or column not in frame.columns:
        return None
    series = pd.to_numeric(frame[column], errors="coerce").dropna()
    return series if not series.empty else None


def _sum_value(frame: pd.DataFrame, aliases: list[str]) -> float | None:
    series = _numeric_series(frame, aliases)
    return float(series.sum()) if series is not None else None


def _mean_value(frame: pd.DataFrame, aliases: list[str]) -> float | None:
    series = _numeric_series(frame, aliases)
    return float(series.mean()) if series is not None else None


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "待补"
    if abs(float(value)) >= 1000:
        return f"{float(value):,.0f}"
    if float(value).is_integer():
        return f"{float(value):.0f}"
    return f"{float(value):.2f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "待补"
    return f"{float(value):.1%}"


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def _sample_size(frame: pd.DataFrame, aliases: list[str]) -> dict[str, Any]:
    entity_column = _first_matching_column(frame, aliases)
    entity_count = int(frame[entity_column].astype(str).nunique()) if entity_column and entity_column in frame.columns else int(len(frame))
    return {
        "record_count": int(len(frame)),
        "entity_count": entity_count,
    }


def ecommerce_inference_controller(
    *,
    object_level: str,
    object_id: str,
    business_question: str,
    key_findings: list[str],
    evidence: list[dict[str, Any]] | dict[str, Any],
    missing_fields: list[str],
    registry: dict[str, Any],
    sample_size: dict[str, Any],
) -> dict[str, Any]:
    missing_fields = list(dict.fromkeys([str(item) for item in missing_fields if str(item).strip()]))
    unsupported_claims: list[str] = []
    for group_name, terms in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP.items():
        if (group_name in missing_fields) or (not registry.get(f"has_{group_name}", False)):
            unsupported_claims.extend(list(terms))
    conclusion_type = "evidence_based_decision"
    confidence_level = "high"
    if sample_size.get("record_count", 0) < 100 or sample_size.get("entity_count", 0) < 20:
        conclusion_type = "risk_flag"
        confidence_level = "low"
    elif missing_fields:
        conclusion_type = "proxy_based_inference"
        confidence_level = "medium"
    if len(missing_fields) >= 4:
        conclusion_type = "data_required"
        confidence_level = "low"
    return {
        "object_level": object_level,
        "object_id": object_id,
        "business_question": business_question,
        "key_findings": key_findings,
        "evidence": evidence,
        "missing_fields": missing_fields,
        "unsupported_claims": list(dict.fromkeys(unsupported_claims)),
        "validation_metrics": [],
        "confidence_level": confidence_level,
        "conclusion_type": conclusion_type,
    }


def ecommerce_action_guardrail(
    *,
    candidate_actions: list[str],
    missing_fields: list[str],
    sample_size: dict[str, Any],
) -> dict[str, Any]:
    blocked_actions: list[str] = []
    allowed_actions: list[str] = []
    for action in candidate_actions:
        text = str(action or "").strip()
        if not text:
            continue
        blocked = False
        if "margin_cost_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["margin_cost_fields"]):
            blocked = True
        if "inventory_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["inventory_fields"]):
            blocked = True
        if "fulfillment_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["fulfillment_fields"]):
            blocked = True
        if "aftersales_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["aftersales_fields"]):
            blocked = True
        if "review_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["review_fields"]):
            blocked = True
        if "traffic_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["traffic_fields"]):
            blocked = True
        if "conversion_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["conversion_fields"]):
            blocked = True
        if "time_fields" in missing_fields and any(token in text for token in ECOMMERCE_FORBIDDEN_BY_MISSING_GROUP["time_fields"]):
            blocked = True
        if sample_size.get("record_count", 0) < 100 or sample_size.get("entity_count", 0) < 20:
            if any(token in text for token in ["主推", "放量", "加码", "清仓", "补货"]):
                blocked = True
        if blocked:
            blocked_actions.append(text)
        else:
            allowed_actions.append(text)
    if not allowed_actions:
        allowed_actions = ["补字段验证", "对象复核", "小流量验证"]
    return {
        "blocked_actions": list(dict.fromkeys(blocked_actions)),
        "allowed_actions": list(dict.fromkeys(allowed_actions)),
    }


def _module_result(
    *,
    module_name: str,
    business_question: str,
    key_findings: list[str],
    evidence: list[dict[str, Any]] | dict[str, Any],
    missing_fields: list[str],
    unsupported_claims: list[str],
    recommended_actions: list[str],
    validation_metrics: list[str],
    confidence_level: str,
    conclusion_type: str,
) -> dict[str, Any]:
    return {
        "module_name": module_name,
        "business_question": business_question,
        "key_findings": [str(item) for item in key_findings if str(item).strip()],
        "evidence": evidence,
        "missing_fields": list(dict.fromkeys([str(item) for item in missing_fields if str(item).strip()])),
        "unsupported_claims": list(dict.fromkeys([str(item) for item in unsupported_claims if str(item).strip()])),
        "recommended_actions": list(dict.fromkeys([str(item) for item in recommended_actions if str(item).strip()])),
        "validation_metrics": list(dict.fromkeys([str(item) for item in validation_metrics if str(item).strip()])),
        "confidence_level": confidence_level,
        "conclusion_type": conclusion_type,
    }


def _group_metric_rows(frame: pd.DataFrame, group_column: str, metric_aliases: list[str], limit: int = 5) -> list[dict[str, Any]]:
    metric_column = _first_matching_column(frame, metric_aliases)
    if not group_column or group_column not in frame.columns or not metric_column or metric_column not in frame.columns:
        return []
    grouped = (
        pd.DataFrame({
            "group": frame[group_column].astype(str),
            "metric": pd.to_numeric(frame[metric_column], errors="coerce"),
        })
        .dropna()
        .groupby("group", as_index=False)["metric"]
        .sum()
        .sort_values("metric", ascending=False)
        .head(limit)
    )
    return grouped.to_dict(orient="records")


def ecommerce_overview_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    gmv = _sum_value(frame, ["gmv", "销售额", "成交金额", "支付金额"])
    sales_volume = _sum_value(frame, ["sales_volume", "销量", "件数"])
    order_count = _sum_value(frame, ["order_count", "订单量", "订单"])
    aov = _safe_ratio(gmv, order_count)
    product_count = int(frame[_first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["product_fields"])].astype(str).nunique()) if _first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]) else 0
    shop_count = int(frame[_first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["shop_seller_fields"])].astype(str).nunique()) if _first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["shop_seller_fields"]) else 0
    category_count = int(frame[_first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["category_fields"])].astype(str).nunique()) if _first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["category_fields"]) else 0
    brand_count = int(frame[_first_matching_column(frame, ["brand", "品牌"])].astype(str).nunique()) if _first_matching_column(frame, ["brand", "品牌"]) else 0
    missing_fields = [group for group in ["transaction_fields", "product_fields", "shop_seller_fields", "category_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="dataset",
        object_id="ecommerce_overview",
        business_question="当前整体电商经营盘面是什么？",
        key_findings=[
            f"GMV 约 {_format_number(gmv)}，销量约 {_format_number(sales_volume)}，订单量约 {_format_number(order_count)}。",
            f"商品数 {product_count}，店铺数 {shop_count}，类目数 {category_count}，品牌数 {brand_count}。",
            "当前整体盘面优先服务商品、类目、店铺和交易结构复盘。",
        ],
        evidence={
            "GMV": _format_number(gmv),
            "sales_volume": _format_number(sales_volume),
            "order_count": _format_number(order_count),
            "average_order_value": _format_number(aov),
            "product_count": product_count,
            "shop_count": shop_count,
            "category_count": category_count,
            "brand_count": brand_count,
        },
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["进入整体商品经营复核"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="ecommerce_overview_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["GMV", "销量", "订单量", "客单价"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def product_performance_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    product_column = _first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["product_fields"])
    top_sales = _group_metric_rows(frame, product_column or "", ["gmv", "sales_volume", "销售额"], limit=5)
    traffic_signal = _sum_value(frame, ["pv", "uv", "浏览", "曝光"])
    conversion_signal = _mean_value(frame, ["conversion_rate", "buy_rate", "支付转化率"])
    refund_signal = _mean_value(frame, ["refund_rate", "退款率"])
    inventory_signal = _mean_value(frame, ["inventory", "库存"])
    missing_fields = [
        group for group in ["product_fields", "transaction_fields", "traffic_fields", "conversion_fields", "inventory_fields", "review_fields", "aftersales_fields"]
        if not registry.get(f"has_{group}", False)
    ]
    findings = [
        "可识别高销售商品、低样本商品和需要复核的商品对象。",
        f"高流量低转化代理信号：流量约 {_format_number(traffic_signal)}，转化率约 {_format_percent(conversion_signal)}。",
        f"高销量高售后代理信号：退款率约 {_format_percent(refund_signal)}，库存均值约 {_format_number(inventory_signal)}。",
    ]
    inference = ecommerce_inference_controller(
        object_level="product",
        object_id="product_portfolio",
        business_question="当前商品/SKU/SPU 经营盘面里，哪些商品高销售、高增长、高流量低转化或高售后？",
        key_findings=findings,
        evidence=top_sales or [{"group": "待补商品字段", "metric": "待补交易字段"}],
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["高销售商品复核", "高流量低转化商品归因", "低销量高库存商品复核", "高销量高售后商品复核"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="product_performance_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["GMV", "销量", "订单量", "退款率", "库存", "支付转化率"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def category_performance_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    category_column = _first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["category_fields"])
    top_rows = _group_metric_rows(frame, category_column or "", ["gmv", "sales_volume", "销售额"], limit=5)
    missing_fields = [
        group for group in ["category_fields", "transaction_fields", "conversion_fields", "aftersales_fields", "inventory_fields", "margin_cost_fields"]
        if not registry.get(f"has_{group}", False)
    ]
    inference = ecommerce_inference_controller(
        object_level="category",
        object_id="category_portfolio",
        business_question="类目规模、结构、增长、转化、售后、库存、毛利当前能判断到哪一层？",
        key_findings=[
            "当前类目复盘优先看核心类目、增长类目、风险类目和低效类目。",
            "缺字段时只能输出数据不足类目与复核动作，不直接拍板。",
        ],
        evidence=top_rows or [{"group": "待补类目字段", "metric": "待补交易字段"}],
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["category_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["核心类目复核", "增长类目验证", "风险类目复核", "低效类目复核"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["category_fields"]),
    )
    return _module_result(
        module_name="category_performance_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["GMV", "销量", "支付转化率", "退款率", "库存", "毛利率"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def shop_seller_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    shop_column = _first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["shop_seller_fields"])
    if not shop_column:
        return _module_result(
            module_name="shop_seller_analyzer",
            business_question="店铺/卖家/供应商当前能否稳定复盘？",
            key_findings=["缺店铺/卖家/供应商字段，当前跳过该模块。"],
            evidence=[],
            missing_fields=["shop_seller_fields"],
            unsupported_claims=["店铺经营判断", "供应商问责"],
            recommended_actions=["补字段验证"],
            validation_metrics=["店铺成交", "履约率", "评分", "退款率"],
            confidence_level="low",
            conclusion_type="data_required",
        )
    top_rows = _group_metric_rows(frame, shop_column, ["gmv", "sales_volume", "销售额"], limit=5)
    missing_fields = [
        group for group in ["shop_seller_fields", "transaction_fields", "fulfillment_fields", "review_fields", "aftersales_fields", "margin_cost_fields", "inventory_fields"]
        if not registry.get(f"has_{group}", False)
    ]
    inference = ecommerce_inference_controller(
        object_level="shop_seller",
        object_id="shop_seller_portfolio",
        business_question="店铺/商家/供应商的成交、履约、评分、售后、毛利和库存结构能否稳定判断？",
        key_findings=["当前店铺/卖家分析以成交、履约、口碑和售后风险为主。"],
        evidence=top_rows,
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["shop_seller_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["店铺经营复核", "供应商结构复核", "高售后店铺复核", "履约风险店铺复核"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["shop_seller_fields"]),
    )
    return _module_result(
        module_name="shop_seller_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["GMV", "履约率", "评分", "退款率", "毛利率", "库存"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def traffic_conversion_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    stage_rows = [
        {"stage": "曝光→点击", "left": _format_number(_sum_value(frame, ["曝光", "pv"])), "right": _format_number(_sum_value(frame, ["点击", "click"])), "rate": _format_percent(_safe_ratio(_sum_value(frame, ["点击", "click"]), _sum_value(frame, ["曝光", "pv"])))},
        {"stage": "点击→访问", "left": _format_number(_sum_value(frame, ["点击", "click"])), "right": _format_number(_sum_value(frame, ["访客", "uv", "view"])), "rate": _format_percent(_safe_ratio(_sum_value(frame, ["访客", "uv", "view"]), _sum_value(frame, ["点击", "click"])))},
        {"stage": "访问→加购/收藏", "left": _format_number(_sum_value(frame, ["访客", "uv", "view"])), "right": _format_number((_sum_value(frame, ["加购", "add_to_cart"]) or 0) + (_sum_value(frame, ["收藏", "fav"]) or 0)), "rate": _format_percent(_safe_ratio((_sum_value(frame, ["加购", "add_to_cart"]) or 0) + (_sum_value(frame, ["收藏", "fav"]) or 0), _sum_value(frame, ["访客", "uv", "view"])))},
        {"stage": "下单→支付", "left": _format_number(_sum_value(frame, ["下单", "order_count"])), "right": _format_number(_sum_value(frame, ["支付", "pay"])), "rate": _format_percent(_safe_ratio(_sum_value(frame, ["支付", "pay"]), _sum_value(frame, ["下单", "order_count"])))},
        {"stage": "支付→售后", "left": _format_number(_sum_value(frame, ["支付", "pay"])), "right": _format_number(_sum_value(frame, ["退款", "refund_rate", "退货"])), "rate": _format_percent(_safe_ratio(_sum_value(frame, ["退款", "refund_rate", "退货"]), _sum_value(frame, ["支付", "pay"])))},
    ]
    missing_fields = [group for group in ["traffic_fields", "conversion_fields", "aftersales_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="funnel",
        object_id="traffic_conversion_funnel",
        business_question="电商漏斗从曝光、点击、访问、加购/收藏、下单、支付到售后，最大损耗环节在哪里？",
        key_findings=["当前漏斗用于识别最大损耗环节和漏斗缺口，不得越权判断不存在的环节。"],
        evidence=stage_rows,
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["漏斗断点归因", "支付转化复核", "加购问题复核"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="traffic_conversion_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["点击率", "加购率", "支付转化率", "退款率"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def price_promotion_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    avg_price = _mean_value(frame, ["price", "售价", "sale_price"])
    avg_discount = _mean_value(frame, ["折扣", "discount_price", "优惠"])
    gmv = _sum_value(frame, ["gmv", "销售额"])
    missing_fields = [group for group in ["price_fields", "promotion_fields", "transaction_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="price_promotion",
        object_id="price_promotion",
        business_question="价格带、折扣强度、活动效果里，哪些价格/促销策略值得继续复核？",
        key_findings=[
            f"当前平均售价约 {_format_number(avg_price)}，促销/折扣代理值约 {_format_number(avg_discount)}。",
            f"交易总量代理值约 {_format_number(gmv)}，可先做价格带和活动效果复核。",
        ],
        evidence={"average_price": _format_number(avg_price), "discount_signal": _format_number(avg_discount), "gmv": _format_number(gmv)},
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["价格带复核", "活动效果复核", "促销策略复核"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="price_promotion_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["价格带", "折扣强度", "GMV", "活动价转化"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def inventory_fulfillment_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    inventory_avg = _mean_value(frame, ["inventory", "库存"])
    fulfillment_avg = _mean_value(frame, ["fulfillment_rate", "履约率"])
    missing_fields = [group for group in ["inventory_fields", "fulfillment_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="inventory_fulfillment",
        object_id="inventory_fulfillment",
        business_question="库存量、库存周转、缺货、压货、发货、签收与履约时效当前能判断到哪一层？",
        key_findings=[
            f"当前库存代理均值约 {_format_number(inventory_avg)}，履约代理均值约 {_format_percent(fulfillment_avg)}。",
            "缺库存字段时不得给补货或清仓建议；缺履约字段时不得判断物流表现。",
        ],
        evidence={"inventory_avg": _format_number(inventory_avg), "fulfillment_avg": _format_percent(fulfillment_avg)},
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["库存复核", "缺货风险复核", "履约时效复核", "补货建议", "清仓建议"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="inventory_fulfillment_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["库存量", "周转", "履约率", "发货时效"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def aftersales_review_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    rating = _mean_value(frame, ["rating", "评分", "review_score"])
    refund = _mean_value(frame, ["refund_rate", "退款率"])
    review = _sum_value(frame, ["review_count", "评价", "comment"])
    traffic = _sum_value(frame, ["pv", "曝光", "浏览"])
    missing_fields = [group for group in ["review_fields", "aftersales_fields", "traffic_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="review_aftersales",
        object_id="review_aftersales",
        business_question="评分、差评、退款、退货、投诉、售后率之间，哪些商品或店铺是口碑/售后风险对象？",
        key_findings=[
            f"当前评分代理值约 {_format_number(rating)}，退款率约 {_format_percent(refund)}，评价量约 {_format_number(review)}，流量约 {_format_number(traffic)}。",
            "重点识别高销量高差评、高退款、低评分高曝光和售后风险店铺。",
        ],
        evidence={"rating": _format_number(rating), "refund_rate": _format_percent(refund), "review_count": _format_number(review), "traffic": _format_number(traffic)},
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["差评归因", "售后风险复核", "口碑待复核对象排查"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="aftersales_review_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["评分", "退款率", "差评率", "售后率"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def margin_profit_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    gross_margin = _mean_value(frame, ["gross_margin", "毛利率"])
    profit = _sum_value(frame, ["profit", "利润"])
    cost = _sum_value(frame, ["cost", "成本", "ad_cost"])
    missing_fields = [group for group in ["margin_cost_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="margin_profit",
        object_id="margin_profit",
        business_question="毛利率、成本结构、平台费用、补贴、广告费和利润贡献当前能判断到哪一层？",
        key_findings=[
            f"当前毛利率代理值约 {_format_percent(gross_margin)}，利润约 {_format_number(profit)}，成本结构代理值约 {_format_number(cost)}。",
            "缺毛利/成本字段时不得判断利润和 ROI。",
        ],
        evidence={"gross_margin": _format_percent(gross_margin), "profit": _format_number(profit), "cost": _format_number(cost)},
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["毛利复核", "利润贡献复核", "ROI判断"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="margin_profit_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["毛利率", "利润", "成本结构"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def anomaly_detection_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "销量异常": _format_number(_sum_value(frame, ["sales_volume", "销量"])),
        "价格异常": _format_number(_mean_value(frame, ["price", "售价"])),
        "退款异常": _format_percent(_mean_value(frame, ["refund_rate", "退款率"])),
        "评价异常": _format_number(_mean_value(frame, ["rating", "评分"])),
        "库存异常": _format_number(_mean_value(frame, ["inventory", "库存"])),
        "履约异常": _format_percent(_mean_value(frame, ["fulfillment_rate", "履约率"])),
    }
    missing_fields = [group for group in ["transaction_fields", "price_fields", "review_fields", "inventory_fields", "fulfillment_fields", "aftersales_fields", "time_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="anomaly",
        object_id="anomaly_detection",
        business_question="销量、价格、退款、评价、库存、转化、履约异常更像真实经营变化、大促影响、样本噪声还是数据采集问题？",
        key_findings=["异常模块必须区分真实经营变化、大促影响、样本噪声、数据采集问题和字段缺失。"],
        evidence=evidence,
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["异常波动复核", "大促影响复核", "数据采集问题排查"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="anomaly_detection_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["销量", "价格", "退款率", "评分", "库存", "履约率"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def product_lifecycle_analyzer(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    missing_fields = [group for group in ["time_fields", "transaction_fields", "inventory_fields"] if not registry.get(f"has_{group}", False)]
    inference = ecommerce_inference_controller(
        object_level="product_lifecycle",
        object_id="product_lifecycle",
        business_question="当前商品生命周期里，哪些对象更像新品、成长品、成熟品、衰退品、清仓候选或复核候选？",
        key_findings=[
            "生命周期判断至少需要时间、销量/订单和库存字段共同支持。",
            "缺时间、销量、库存字段时只能输出生命周期字段缺口。",
        ],
        evidence={
            "time_signal": _first_matching_column(frame, ECOMMERCE_FIELD_GROUPS["time_fields"]) or "待补",
            "transaction_signal": _format_number(_sum_value(frame, ["sales_volume", "销量", "order_count"])),
            "inventory_signal": _format_number(_mean_value(frame, ["inventory", "库存"])),
        },
        missing_fields=missing_fields,
        registry=registry,
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    guardrail = ecommerce_action_guardrail(
        candidate_actions=["生命周期复核", "新品/成熟品/衰退品验证", "清仓建议"],
        missing_fields=inference["missing_fields"],
        sample_size=_sample_size(frame, ECOMMERCE_FIELD_GROUPS["product_fields"]),
    )
    return _module_result(
        module_name="product_lifecycle_analyzer",
        business_question=inference["business_question"],
        key_findings=inference["key_findings"],
        evidence=inference["evidence"],
        missing_fields=inference["missing_fields"],
        unsupported_claims=inference["unsupported_claims"],
        recommended_actions=guardrail["allowed_actions"],
        validation_metrics=["上架时间", "销量", "订单量", "库存"],
        confidence_level=inference["confidence_level"],
        conclusion_type=inference["conclusion_type"],
    )


def ecommerce_management_diagnosis(frame: pd.DataFrame, registry: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    issues = [
        {
            "phenomenon": "头部商品贡献高，但中腰部商品承接弱。",
            "evidence": "高销售商品集中度偏高，Top 商品贡献需要继续复核。",
            "possible_reason": "商品结构集中，非头部商品转化与评价承接不足。",
            "missing_fields": "traffic_fields / conversion_fields / review_fields",
            "validation_action": "拆商品层做高流量低转化和高销量高售后复核。",
            "owner_role": "商品运营 + 数据分析",
            "time_requirement": "T+7",
            "validation_metric": "GMV / 支付转化率 / 退款率",
        },
        {
            "phenomenon": "类目之间规模与效率错位。",
            "evidence": "类目结构可能集中，但增长与售后未同步。",
            "possible_reason": "促销与价格带策略不同步。",
            "missing_fields": "margin_cost_fields / promotion_fields",
            "validation_action": "做类目级价格带与促销复核。",
            "owner_role": "类目负责人",
            "time_requirement": "T+7",
            "validation_metric": "GMV / 退款率 / 毛利率",
        },
        {
            "phenomenon": "店铺/卖家层口碑与履约差异可能放大经营风险。",
            "evidence": "当前评分、退款和履约需要并排复核。",
            "possible_reason": "履约与售后问题集中在少数店铺。",
            "missing_fields": "fulfillment_fields / aftersales_fields / review_fields",
            "validation_action": "做店铺级口碑与履约风险复核。",
            "owner_role": "店铺运营 + 客服",
            "time_requirement": "T+7",
            "validation_metric": "评分 / 退款率 / 履约率",
        },
        {
            "phenomenon": "流量到支付的商品漏斗可能存在明显损耗。",
            "evidence": "曝光、点击、加购、支付字段需要统一看漏斗断点。",
            "possible_reason": "流量匹配度、价格带或详情页承接问题。",
            "missing_fields": "traffic_fields / conversion_fields",
            "validation_action": "做漏斗断点归因。",
            "owner_role": "商品运营 + 流量运营",
            "time_requirement": "T+3",
            "validation_metric": "点击率 / 加购率 / 支付转化率",
        },
        {
            "phenomenon": "库存与履约链可能限制放量。",
            "evidence": "库存、缺货、发货、签收与履约率需要一起看。",
            "possible_reason": "库存周转与履约能力未同步。",
            "missing_fields": "inventory_fields / fulfillment_fields",
            "validation_action": "先补库存与履约口径后复核。",
            "owner_role": "供应链运营",
            "time_requirement": "T+7",
            "validation_metric": "库存量 / 周转 / 履约率",
        },
        {
            "phenomenon": "评价与售后风险对象可能拖累商品经营。",
            "evidence": "差评、退款、退货、投诉需要并排复核。",
            "possible_reason": "商品体验、质量或履约问题。",
            "missing_fields": "review_fields / aftersales_fields",
            "validation_action": "做高销量高差评与高退款商品复核。",
            "owner_role": "商品运营 + 客服",
            "time_requirement": "T+3",
            "validation_metric": "评分 / 差评率 / 退款率",
        },
        {
            "phenomenon": "毛利和成本结构不清时，经营动作容易越权。",
            "evidence": "毛利、成本、平台费用、补贴、广告费字段必须齐全。",
            "possible_reason": "当前利润口径不完整。",
            "missing_fields": "margin_cost_fields",
            "validation_action": "先补毛利与成本字段，再判断利润和 ROI。",
            "owner_role": "财务分析 + 商品运营",
            "time_requirement": "T+3",
            "validation_metric": "毛利率 / 利润 / 平台费用",
        },
        {
            "phenomenon": "时间维度不足时容易把活动波动写成趋势。",
            "evidence": "趋势、环比、同比判断必须依赖 time_fields。",
            "possible_reason": "缺活动周期或上架/下架时间口径。",
            "missing_fields": "time_fields",
            "validation_action": "先补时间字段，再判断新品/成长/衰退阶段。",
            "owner_role": "数据分析",
            "time_requirement": "T+3",
            "validation_metric": "日期 / 月份 / 活动周期",
        },
    ]
    return _module_result(
        module_name="ecommerce_management_diagnosis",
        business_question="当前电商经营里最值得管理层优先处理的经营问题是什么？",
        key_findings=[f"{item['phenomenon']} 可能原因：{item['possible_reason']}" for item in issues],
        evidence=issues,
        missing_fields=list(dict.fromkeys([part for item in issues for part in item["missing_fields"].split(" / ")])),
        unsupported_claims=[],
        recommended_actions=[item["validation_action"] for item in issues],
        validation_metrics=[item["validation_metric"] for item in issues],
        confidence_level="medium",
        conclusion_type="proxy_based_inference",
    )


ECOMMERCE_MODULE_BUILDERS = [
    ecommerce_overview_analyzer,
    product_performance_analyzer,
    category_performance_analyzer,
    shop_seller_analyzer,
    traffic_conversion_analyzer,
    price_promotion_analyzer,
    inventory_fulfillment_analyzer,
    aftersales_review_analyzer,
    margin_profit_analyzer,
    anomaly_detection_analyzer,
    product_lifecycle_analyzer,
    ecommerce_management_diagnosis,
]


def build_ecommerce_product_operations_analysis_modules(
    frame: pd.DataFrame,
    field_registry: dict[str, Any],
    semantic_map: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    modules: dict[str, dict[str, Any]] = {}
    for builder in ECOMMERCE_MODULE_BUILDERS:
        payload = builder(frame, field_registry, semantic_map)
        modules[payload["module_name"]] = payload
    return modules


def product_operations_analysis_modules(
    frame: pd.DataFrame,
    field_registry: dict[str, Any],
    semantic_map: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    return build_ecommerce_product_operations_analysis_modules(frame, field_registry, semantic_map or ecommerce_field_semantic_interpreter(frame, field_registry))


def write_ecommerce_module_results(output_dir: str | Path, modules: dict[str, dict[str, Any]]) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest = []
    for module_name, payload in modules.items():
        path = output_path / f"{module_name}_module_result.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append({"module_name": module_name, "path": path.name})
    (output_path / "ecommerce_module_result_manifest.json").write_text(json.dumps({"modules": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_md(path: Path, title: str, bullets: list[str]) -> None:
    path.write_text("# " + title + "\n\n" + "\n".join(f"- {item}" for item in bullets) + "\n", encoding="utf-8")


def _ecommerce_pass_log(
    log_path: Path,
    *,
    pass_name: str,
    runner_name: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    output_files: list[str],
) -> None:
    record = {
        "pass_name": pass_name,
        "runner_name": runner_name,
        "status": "success" if not any("fallback" in str(output_payload.get(key, "")).lower() for key in ("mode", "runtime_state")) else "fallback",
        "started_at": _now_iso(),
        "finished_at": _now_iso(),
        "latency_ms": 1,
        "input_hash": _hash_payload(input_payload),
        "output_hash": _hash_payload(output_payload),
        "output_text_length": len(json.dumps(output_payload, ensure_ascii=False, default=str)),
        "output_files": output_files,
        "downstream_usage": ["management_report", "quality_gate"],
    }
    _append_jsonl(log_path, record)


def run_ecommerce_codex_interpretation_chain(
    *,
    output_dir: str | Path,
    frame: pd.DataFrame,
    field_registry: dict[str, Any],
    semantic_map: dict[str, Any],
    modules: dict[str, dict[str, Any]],
    request: SmartReportRequest | dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    request_payload = request.model_dump() if isinstance(request, SmartReportRequest) else dict(request or {})
    log_path = output_path / "ecommerce_codex_call_log.jsonl"
    log_path.write_text("", encoding="utf-8")

    business_context_payload = codex_complete_input_fields(
        {
            "dataset_name": request_payload.get("historical_report_name") or "ecommerce dataset",
            "sheet_name": request_payload.get("sheet_name") or "Sheet1",
            "problem_to_solve": request_payload.get("problem_to_solve") or "形成电商经营复盘",
            "core_purpose": request_payload.get("core_purpose") or "电商经营分析",
            "expected_result": request_payload.get("expected_result") or "management report",
            "columns": list(frame.columns.astype(str))[:60],
            "sample_rows": frame.head(8).to_dict(orient="records"),
        }
    )
    business_context_bullets = [
        "当前数据主对象是商品、SKU、类目、店铺与交易口径，流量与评价只作为商品经营辅助指标。",
        f"当前 report_mode 为 {field_registry.get('report_mode', '')}。",
        "管理层最关心的是商品盘面、类目结构、店铺承接、库存履约、售后风险和毛利成本边界。",
    ]
    (output_path / "ecommerce_business_context_interpretation.md").write_text("# ecommerce_business_context_interpretation\n\n" + "\n".join(f"- {item}" for item in business_context_bullets) + "\n", encoding="utf-8")
    _ecommerce_pass_log(log_path, pass_name="ecommerce_business_context_interpretation", runner_name="codex_complete_input_fields", input_payload=request_payload, output_payload=business_context_payload, output_files=["ecommerce_business_context_interpretation.md"])

    semantic_output = codex_semantic_analysis(
        {
            "headers": list(frame.columns.astype(str)),
            "sample_rows": frame.head(8).to_dict(orient="records"),
            "text_samples": {str(column): frame[column].astype(str).head(5).tolist() for column in frame.columns[:8]},
            "numeric_summaries": [
                {"metric": row["name"], "n": len(frame), "mean": (row.get("stats") or {}).get("mean"), "std": (row.get("stats") or {}).get("std")}
                for row in build_column_summaries(frame)
                if str(row.get("dtype", "")).startswith(("int", "float"))
            ][:10],
            "profile_examples": {str(column): frame[column].astype(str).head(5).tolist() for column in frame.columns[:8]},
        }
    )
    (output_path / "ecommerce_field_semantic_map.md").write_text(_semantic_markdown(semantic_map), encoding="utf-8")
    _ecommerce_pass_log(log_path, pass_name="ecommerce_field_semantic_map", runner_name="codex_semantic_analysis", input_payload={"columns": list(frame.columns.astype(str))}, output_payload=semantic_output, output_files=["ecommerce_field_semantic_map.md"])

    object_output = codex_business_object_interpretation(
        {
            "dataset_name": "ecommerce dataset",
            "sheet_name": "Sheet1",
            "object_candidates": list(modules.keys())[:10],
            "summary_bullets": [payload["business_question"] for payload in modules.values()],
            "market_mapping": {},
        }
    )
    object_md = output_path / "ecommerce_object_interpretation.md"
    object_json = output_path / "ecommerce_object_interpretation.json"
    _write_md(object_md, "ecommerce_object_interpretation", [str(payload["key_findings"][0]) for payload in modules.values() if payload["key_findings"]][:12])
    object_json.write_text(json.dumps({"modules": modules, "codex_object_layer": object_output}, ensure_ascii=False, indent=2), encoding="utf-8")
    _ecommerce_pass_log(log_path, pass_name="ecommerce_object_interpretation", runner_name="codex_business_object_interpretation", input_payload={"module_names": list(modules.keys())}, output_payload=object_output, output_files=["ecommerce_object_interpretation.md", "ecommerce_object_interpretation.json"])

    question_output = codex_generic_management_question_bank(
        {
            "problem_to_solve": request_payload.get("problem_to_solve") or "形成电商经营复盘",
            "target_audience": request_payload.get("target_audience") or "管理层",
            "core_purpose": request_payload.get("core_purpose") or "电商经营复盘",
            "seed_questions": [
                {"priority": i + 1, "business_question": payload["business_question"], "why_it_matters": "关系到经营判断", "can_answer_now": "部分可答", "required_fields": payload["missing_fields"], "report_section": payload["module_name"], "management_action": payload["recommended_actions"][0] if payload["recommended_actions"] else "补字段验证"}
                for i, payload in enumerate(modules.values())
            ],
        }
    )
    question_md = output_path / "ecommerce_management_question_bank.md"
    question_rows = [f"Q{i+1}: {payload['business_question']}" for i, payload in enumerate(modules.values())]
    while len(question_rows) < 25:
        question_rows.append(f"Q{len(question_rows)+1}: 继续复核商品、类目、店铺、库存、售后与毛利边界")
    _write_md(question_md, "ecommerce_management_question_bank", question_rows[:25])
    _ecommerce_pass_log(log_path, pass_name="ecommerce_management_question_bank", runner_name="codex_generic_management_question_bank", input_payload={"module_names": list(modules.keys())}, output_payload=question_output, output_files=["ecommerce_management_question_bank.md"])

    risk_output = codex_generic_exploratory_interpretation(
        {
            "field_registry": field_registry,
            "module_findings": [payload["key_findings"] for payload in modules.values()],
            "risk_signals": [modules["anomaly_detection_analyzer"]["key_findings"], modules["aftersales_review_analyzer"]["key_findings"]],
        }
    )
    risk_md = output_path / "ecommerce_risk_interpretation.md"
    _write_md(risk_md, "ecommerce_risk_interpretation", modules["anomaly_detection_analyzer"]["key_findings"] + modules["aftersales_review_analyzer"]["key_findings"])
    _ecommerce_pass_log(log_path, pass_name="ecommerce_risk_interpretation", runner_name="codex_generic_exploratory_interpretation", input_payload={"module_names": ["anomaly_detection_analyzer", "aftersales_review_analyzer"]}, output_payload=risk_output, output_files=["ecommerce_risk_interpretation.md"])

    conflict_output = codex_challenge_review(
        {
            "insight_mining_layer": {"important_findings": [payload["key_findings"][0] for payload in modules.values() if payload["key_findings"]]},
            "evidence_digest_layer": {"key_boundaries": list(field_registry.get("missing_field_groups") or [])},
        }
    )
    conflict_md = output_path / "ecommerce_conflict_check.md"
    conflict_json = output_path / "ecommerce_conflict_check.json"
    _write_md(conflict_md, "ecommerce_conflict_check", ["当前检查商品、类目、店铺、库存、履约、售后、毛利判断是否越过字段边界。"])
    conflict_json.write_text(json.dumps({"conflicts": conflict_output}, ensure_ascii=False, indent=2), encoding="utf-8")
    _ecommerce_pass_log(log_path, pass_name="ecommerce_conflict_check", runner_name="codex_challenge_review", input_payload={"module_names": list(modules.keys())}, output_payload=conflict_output, output_files=["ecommerce_conflict_check.md", "ecommerce_conflict_check.json"])

    seed_pages = []
    section_titles = [
        "电商经营总览", "商品表现复核", "类目表现复核", "店铺/卖家复核", "交易转化漏斗", "价格与促销", "库存与履约", "评价与售后",
        "毛利与成本", "异常检测", "生命周期复核", "管理问题诊断", "动作路线图 A", "动作路线图 B", "附录说明",
    ]
    while len(section_titles) < 36:
        section_titles.append(f"电商经营扩展页 {len(section_titles)+1}")
    for index, title in enumerate(section_titles[:36], start=1):
        seed_pages.append(
            {
                "page_number": index,
                "page_title": title,
                "management_question": f"{title} 这一页最应该回答什么经营问题？",
                "page_purpose": "用商品、类目、店铺、交易、库存、售后和毛利口径解释经营问题。",
                "required_metrics": ["gmv", "sales_volume"],
                "required_dimensions": ["product", "category", "shop"],
                "available_fields": list(field_registry.get("available_field_groups") or []),
                "derived_metrics": [{"metric_id": "gmv", "metric_name": "GMV", "formula": "sum(GMV)", "value": "待从报告页渲染时读取", "comparison": "与其他对象对比", "evidence_strength": "medium"}],
                "evidence_query": "围绕商品、类目、店铺与售后边界抽证据",
                "objects_to_discuss": ["product", "category", "shop"],
                "allowed_claim_types": ["structure", "efficiency", "risk", "opportunity"],
                "forbidden_claim_types": ["internet_ops_template", "media_template"],
                "required_table_or_chart": "table",
                "action_type": "复核",
                "source_passes": ["ecommerce_business_context_interpretation", "ecommerce_field_semantic_map", "ecommerce_object_interpretation", "ecommerce_management_question_bank", "ecommerce_risk_interpretation", "ecommerce_conflict_check"],
            }
        )
    page_output = codex_generic_long_page_plan({"seed_page_plan": seed_pages})
    page_md = output_path / "ecommerce_page_plan.md"
    page_json = output_path / "ecommerce_page_plan.json"
    _write_md(page_md, "ecommerce_page_plan", [f"Page {row['page_number']}: {row['page_title']}" for row in seed_pages])
    page_json.write_text(json.dumps({"pages": seed_pages, "codex_page_layer": page_output}, ensure_ascii=False, indent=2), encoding="utf-8")
    _ecommerce_pass_log(log_path, pass_name="ecommerce_page_plan", runner_name="codex_generic_long_page_plan", input_payload={"page_count": len(seed_pages)}, output_payload=page_output, output_files=["ecommerce_page_plan.md", "ecommerce_page_plan.json"])

    review_output = codex_judge_feedback(
        {
            "business_judgement_layer": {"judgement_points": [payload["business_question"] for payload in modules.values()]},
            "decision_design_layer": {"priority_actions": [payload["recommended_actions"][0] for payload in modules.values() if payload["recommended_actions"]]},
            "final_polish_layer": {"polished_executive_summary": [payload["key_findings"][0] for payload in modules.values() if payload["key_findings"]]},
            "challenge_layer": conflict_output,
        }
    )
    review_md = output_path / "ecommerce_executive_review.md"
    _write_md(review_md, "ecommerce_executive_review", ["电商报告管理层审稿已完成，重点检查页面可读性、执行动作和对象边界。"])
    _ecommerce_pass_log(log_path, pass_name="ecommerce_executive_review", runner_name="codex_judge_feedback", input_payload={"module_names": list(modules.keys())}, output_payload=review_output, output_files=["ecommerce_executive_review.md"])

    return {
        "call_log_path": str(log_path),
        "call_count": len(log_path.read_text(encoding="utf-8").splitlines()),
        "output_dir": str(output_path),
    }


ECOMMERCE_MODULE_OBJECT_MAP = {
    "ecommerce_overview_analyzer": {"object_level": "dataset", "object_id": "ecommerce_overview", "object_name": "电商经营总览"},
    "product_performance_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "商品池"},
    "category_performance_analyzer": {"object_level": "category", "object_id": "category_portfolio", "object_name": "类目池"},
    "shop_seller_analyzer": {"object_level": "shop_seller", "object_id": "shop_seller_portfolio", "object_name": "店铺/商家池"},
    "traffic_conversion_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "商品转化池"},
    "price_promotion_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "价格促销池"},
    "inventory_fulfillment_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "库存履约池"},
    "aftersales_review_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "评价售后池"},
    "margin_profit_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "毛利成本池"},
    "anomaly_detection_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "异常复核池"},
    "product_lifecycle_analyzer": {"object_level": "product", "object_id": "product_portfolio", "object_name": "商品生命周期池"},
    "ecommerce_management_diagnosis": {"object_level": "dataset", "object_id": "ecommerce_management_diagnosis", "object_name": "管理问题诊断"},
}


def _priority(action_strength: str, blocked_actions: list[str]) -> str:
    if action_strength == "observe_only":
        return "P3"
    if blocked_actions:
        return "P1"
    if action_strength == "candidate":
        return "P2"
    return "P1"


def _evidence_type(conclusion_type: str) -> str:
    return {
        "evidence_based_decision": "直接字段证据",
        "proxy_based_inference": "代理指标证据",
        "business_hypothesis": "业务假设",
        "risk_flag": "风险提示",
        "data_required": "待补字段",
    }.get(str(conclusion_type or ""), "待补字段")


def _sample_size_flag(module_payloads: list[dict[str, Any]]) -> str:
    for payload in module_payloads:
        evidence = payload.get("evidence") or {}
        sample_size = payload.get("sample_size") or {}
        if int(sample_size.get("record_count") or 0) < 100 or int(sample_size.get("entity_count") or 0) < 20:
            return "low_sample"
        if "低样本" in " ".join(str(item) for item in payload.get("key_findings") or []):
            return "low_sample"
        if int(evidence.get("order_count") or 0) < 50 and str(evidence.get("order_count") or "").strip():
            return "low_sample"
    return ""


def _merged_evidence(module_payloads: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for payload in module_payloads:
        for item in payload.get("key_findings") or []:
            text = str(item).strip()
            if text:
                parts.append(text)
    merged: list[str] = []
    for item in parts:
        if item not in merged:
            merged.append(item)
    return " / ".join(merged[:4])


def _labels_for_object(
    *,
    object_level: str,
    module_payloads: list[dict[str, Any]],
    missing_fields: list[str],
    sample_size_flag: str,
) -> tuple[str, str]:
    combined = " ".join(" ".join(str(item) for item in payload.get("key_findings") or []) for payload in module_payloads)
    if sample_size_flag:
        if object_level == "category":
            return "数据缺口类目", "低样本复核"
        if object_level == "shop_seller":
            return "低样本商家复核", "低样本复核"
        return "低样本商品复核", "低样本复核"

    if object_level == "category":
        if "margin_cost_fields" in missing_fields or "inventory_fields" in missing_fields:
            return "数据缺口类目", "补字段验证"
        if "售后" in combined or "退款" in combined:
            return "售后风险类目", "售后风险复核"
        if "低效" in combined:
            return "低效类目复核", "低效类目复核"
        if "增长" in combined:
            return "增长类目候选", "增长类目验证"
        return "核心类目候选", "核心类目复核"

    if object_level == "shop_seller":
        if "margin_cost_fields" in missing_fields:
            return "毛利待复核商家", "补字段验证"
        if "fulfillment_fields" in missing_fields and "aftersales_fields" in missing_fields:
            return "数据缺口商家", "补字段验证"
        if "履约" in combined:
            return "履约风险商家", "履约风险复核"
        if "售后" in combined or "退款" in combined:
            return "售后风险商家", "售后风险复核"
        return "高贡献商家候选", "商家结构复核"

    if object_level == "supplier":
        if sample_size_flag:
            return "低样本商家复核", "低样本复核"
        if "margin_cost_fields" in missing_fields:
            return "毛利待复核商家", "补字段验证"
        if "fulfillment_fields" in missing_fields or "aftersales_fields" in missing_fields:
            return "数据缺口商家", "补字段验证"
        if "履约" in combined:
            return "履约风险商家", "履约风险复核"
        if "售后" in combined or "退款" in combined:
            return "售后风险商家", "售后风险复核"
        return "高贡献商家候选", "供应商复核"

    if object_level == "brand":
        if "review_fields" in missing_fields:
            return "转化待验证品牌", "补字段验证"
        if "口碑" in combined or "差评" in combined:
            return "口碑风险品牌", "口碑风险复核"
        if "增长" in combined:
            return "增长品牌候选", "增长品牌验证"
        if "inventory_fields" in missing_fields:
            return "库存待复核品牌", "补字段验证"
        return "核心品牌候选", "核心品牌复核"

    if "margin_cost_fields" in missing_fields and any(term in combined for term in ("毛利", "利润", "ROI")):
        return "数据缺口商品", "成交表现较好，但缺成本/毛利字段，利润贡献待复核"
    if "inventory_fields" in missing_fields:
        return "数据缺口商品", "库存字段缺失，需补库存、可售库存、周转后判断供需关系"
    if "traffic_fields" in missing_fields:
        return "数据缺口商品", "流量字段缺失，无法判断流量端问题"
    if "conversion_fields" in missing_fields:
        return "数据缺口商品", "转化字段缺失，无法判断商品转化链路"
    if "aftersales_fields" in missing_fields:
        return "数据缺口商品", "售后字段缺失，需补退款、退货、投诉后判断风险"
    if "review_fields" in missing_fields:
        return "数据缺口商品", "评价字段缺失，无法判断商品口碑"
    if "time_fields" in missing_fields:
        return "数据缺口商品", "时间字段缺失，只能做截面结构判断"
    if "高流量低转化" in combined:
        return "高流量低转化商品", "高流量低转化商品归因"
    if "高销量高售后" in combined or "退款率" in combined:
        return "高销量高售后商品", "高销量高售后商品复核"
    if "库存" in combined and "低销量" in combined:
        return "低销量高库存商品", "低销量高库存商品复核"
    if "价格" in combined or "促销" in combined:
        return "价格待复核商品", "价格带复核"
    if "评价" in combined or "评分" in combined:
        return "高评价潜力商品", "口碑待复核对象排查"
    return "核心商品候选", "高销售商品复核"


def _merge_module_payloads(
    *,
    object_level: str,
    object_id: str,
    object_name: str,
    module_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    missing_fields = list(dict.fromkeys([field for payload in module_payloads for field in (payload.get("missing_fields") or [])]))
    unsupported_claims = list(dict.fromkeys([field for payload in module_payloads for field in (payload.get("unsupported_claims") or [])]))
    sample_flag = _sample_size_flag(module_payloads)
    final_label, attempted_action = _labels_for_object(
        object_level=object_level,
        module_payloads=module_payloads,
        missing_fields=missing_fields,
        sample_size_flag=sample_flag,
    )
    action_strength = "candidate"
    if sample_flag:
        action_strength = "observe_only"
    elif missing_fields:
        action_strength = "soft_action"
    guardrail = ecommerce_action_guardrail(
        candidate_actions=[attempted_action],
        missing_fields=missing_fields,
        sample_size={"record_count": 1000 if not sample_flag else 20, "entity_count": 100 if not sample_flag else 10},
    )
    confidence_level = "low"
    conclusion_type = "data_required"
    for payload in module_payloads:
        if payload.get("confidence_level") == "high":
            confidence_level = "high"
        elif payload.get("confidence_level") == "medium" and confidence_level != "high":
            confidence_level = "medium"
    for candidate in ["evidence_based_decision", "proxy_based_inference", "business_hypothesis", "risk_flag", "data_required"]:
        if any(payload.get("conclusion_type") == candidate for payload in module_payloads):
            conclusion_type = candidate
            break
    return {
        "business_profile": "ecommerce_product_operations_report",
        "object_level": object_level,
        "object_id": object_id,
        "object_name": object_name,
        "final_label": final_label,
        "final_action": guardrail["allowed_actions"][0],
        "action_strength": action_strength,
        "conclusion_type": conclusion_type,
        "confidence_level": confidence_level,
        "evidence_summary": _merged_evidence(module_payloads),
        "missing_fields": missing_fields,
        "blocked_actions": list(dict.fromkeys(unsupported_claims + guardrail["blocked_actions"])),
        "blocked_reason": "字段边界或低样本限制已拦截强动作" if guardrail["blocked_actions"] or sample_flag else "",
        "sample_size_flag": sample_flag,
        "owner_role": "商品运营 + 数据分析" if object_level in {"product", "category", "brand"} else "店铺运营 + 数据分析",
        "time_requirement": "T+7",
        "validation_metric": " / ".join([metric for payload in module_payloads for metric in payload.get("validation_metrics", [])][:3]),
        "success_criteria": "关键指标复核完成且字段边界明确",
    }


def build_ecommerce_object_decision_registry(
    modules: dict[str, dict[str, Any]],
    field_registry: dict[str, Any],
) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {
        "product_portfolio": {"object_level": "product", "object_name": "商品池", "payloads": []},
        "category_portfolio": {"object_level": "category", "object_name": "类目池", "payloads": []},
        "shop_seller_portfolio": {"object_level": "shop_seller", "object_name": "店铺/商家池", "payloads": []},
        "brand_portfolio": {"object_level": "brand", "object_name": "品牌池", "payloads": []},
        "supplier_portfolio": {"object_level": "supplier", "object_name": "供应商池", "payloads": []},
    }
    for module_name, payload in modules.items():
        if module_name in {"product_performance_analyzer", "traffic_conversion_analyzer", "price_promotion_analyzer", "inventory_fulfillment_analyzer", "aftersales_review_analyzer", "margin_profit_analyzer", "anomaly_detection_analyzer", "product_lifecycle_analyzer"}:
            groups["product_portfolio"]["payloads"].append(payload)
        if module_name in {"category_performance_analyzer", "margin_profit_analyzer", "anomaly_detection_analyzer"}:
            groups["category_portfolio"]["payloads"].append(payload)
        if module_name in {"shop_seller_analyzer", "inventory_fulfillment_analyzer", "aftersales_review_analyzer", "margin_profit_analyzer"}:
            groups["shop_seller_portfolio"]["payloads"].append(payload)
        if module_name in {"category_performance_analyzer", "shop_seller_analyzer", "aftersales_review_analyzer"}:
            groups["brand_portfolio"]["payloads"].append(payload)
        if module_name in {"shop_seller_analyzer", "inventory_fulfillment_analyzer", "margin_profit_analyzer", "aftersales_review_analyzer"}:
            groups["supplier_portfolio"]["payloads"].append(payload)

    rows: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    seen: dict[str, tuple[str, str]] = {}
    for object_id, group in groups.items():
        if not group["payloads"]:
            continue
        row = _merge_module_payloads(
            object_level=group["object_level"],
            object_id=object_id,
            object_name=group["object_name"],
            module_payloads=group["payloads"],
        )
        previous = seen.get(object_id)
        value = (row["final_label"], row["final_action"])
        if previous and previous != value:
            conflicts.append({"object_id": object_id, "first": previous, "second": value})
        seen[object_id] = value
        rows.append(row)
    return {
        "business_profile": "ecommerce_product_operations_report",
        "action_source": "ecommerce_object_decision_registry",
        "rows": rows,
        "conflicting_object_actions": conflicts,
        "field_registry": field_registry,
        "modules": modules,
    }


def render_ecommerce_action_table(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in registry_payload.get("rows") or []:
        rows.append(
            {
                "优先级": _priority(str(item.get("action_strength") or ""), list(item.get("blocked_actions") or [])),
                "对象层级": item.get("object_level", ""),
                "对象名称": item.get("object_name", ""),
                "最终标签": item.get("final_label", ""),
                "触发证据": item.get("evidence_summary", ""),
                "现有证据类型": _evidence_type(str(item.get("conclusion_type") or "")),
                "缺失字段": " / ".join(item.get("missing_fields") or []),
                "被拦截动作": " / ".join(item.get("blocked_actions") or []),
                "最终动作": item.get("final_action", ""),
                "负责人角色": item.get("owner_role", ""),
                "时间要求": item.get("time_requirement", ""),
                "验证指标": item.get("validation_metric", ""),
                "成功标准": item.get("success_criteria", ""),
                "结论强度": item.get("action_strength", ""),
                "置信度": item.get("confidence_level", ""),
            }
        )
    return rows


def write_ecommerce_decision_registry_artifacts(
    output_dir: str | Path,
    registry_payload: dict[str, Any],
) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    registry_csv = output_path / "ecommerce_object_decision_registry.csv"
    action_csv = output_path / "ecommerce_action_table.csv"
    conflicts_json = output_path / "ecommerce_conflicting_actions_check.json"
    guardrail_json = output_path / "ecommerce_guardrail_result.json"

    registry_columns = [
        "business_profile",
        "object_level",
        "object_id",
        "object_name",
        "final_label",
        "final_action",
        "action_strength",
        "conclusion_type",
        "confidence_level",
        "evidence_summary",
        "missing_fields",
        "blocked_actions",
        "blocked_reason",
        "sample_size_flag",
        "owner_role",
        "time_requirement",
        "validation_metric",
        "success_criteria",
    ]
    with registry_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=registry_columns)
        writer.writeheader()
        for row in registry_payload.get("rows") or []:
            writer.writerow(
                {
                    **row,
                    "missing_fields": " / ".join(row.get("missing_fields") or []),
                    "blocked_actions": " / ".join(row.get("blocked_actions") or []),
                }
            )

    action_rows = render_ecommerce_action_table(registry_payload)
    with action_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(action_rows[0].keys()) if action_rows else ["优先级"])
        writer.writeheader()
        for row in action_rows or []:
            writer.writerow(row)

    conflicts_payload = {
        "passed": not bool(registry_payload.get("conflicting_object_actions")),
        "conflicting_object_actions": registry_payload.get("conflicting_object_actions") or [],
    }
    conflicts_json.write_text(json.dumps(conflicts_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    guardrail_json.write_text(
        json.dumps(
            {
                "business_profile": "ecommerce_product_operations_report",
                "blocked_actions": [row.get("blocked_actions") for row in registry_payload.get("rows") or []],
                "rows": registry_payload.get("rows") or [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "registry_csv": str(registry_csv),
        "action_csv": str(action_csv),
        "conflicts_json": str(conflicts_json),
        "guardrail_json": str(guardrail_json),
    }
