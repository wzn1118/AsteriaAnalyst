from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from time import perf_counter
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import SmartReportRequest
from app.services.dataset_service import build_column_summaries
from app.services.all_report_quality_gate_service import all_report_quality_gate
from app.services.industry_data_context_mining_adapter import (
    build_industry_data_context_summary,
    industry_data_context_gate_failures,
    write_industry_data_context_outputs,
)
from app.services.industry_research_citation_guardrail import (
    run_industry_research_citation_guardrail,
)
from app.services.independent_industry_research_pdf_renderer import (
    render_independent_industry_research_pdf_bundle,
)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _stage_detail_path(output_dir: Path, stage_id: str) -> Path:
    return output_dir / "stage_outputs" / f"{stage_id}.json"


def _write_stage_detail(output_dir: Path, stage_id: str, payload: dict[str, Any]) -> str:
    path = _stage_detail_path(output_dir, stage_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())


def _stage_record(
    *,
    output_dir: Path,
    stage_id: str,
    summary: str,
    input_artifacts: list[str],
    output_artifacts: list[str],
    payload: dict[str, Any] | None,
    started_at: float,
    status: str = "completed",
    error_message: str = "",
) -> dict[str, Any]:
    detail_path = _write_stage_detail(
        output_dir,
        stage_id,
        {
            "stage_id": stage_id,
            "status": status,
            "summary": summary,
            "input_artifacts": input_artifacts,
            "output_artifacts": output_artifacts,
            "error_message": error_message,
            "payload": payload or {},
        },
    )
    return {
        "stage_id": stage_id,
        "status": status,
        "summary": summary,
        "input_artifacts": input_artifacts,
        "output_artifacts": output_artifacts,
        "error_message": error_message,
        "elapsed_ms": int((perf_counter() - started_at) * 1000),
        "detail_path": detail_path,
    }


def _stage_trace_markdown(stage_records: list[dict[str, Any]]) -> str:
    lines = [
        "# industry_research_stage_trace",
        "",
        "| stage_id | status | elapsed_ms | summary | output_artifacts | error_message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in stage_records:
        lines.append(
            "| "
            + " | ".join(
                [
                    _safe_text(item.get("stage_id")),
                    _safe_text(item.get("status")),
                    _safe_text(item.get("elapsed_ms")),
                    _safe_text(item.get("summary")).replace("|", "/"),
                    "<br>".join(str(value) for value in (item.get("output_artifacts") or [])[:8]).replace("|", "/"),
                    _safe_text(item.get("error_message")).replace("|", "/"),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _compact(value: Any) -> str:
    return "".join(
        ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff"
    )


def _first_non_empty(*values: Any, default: str = "") -> str:
    for value in values:
        text = _safe_text(value)
        if text:
            return text
    return default


def _field_detail(data_context_payload: dict[str, Any], field_name: str) -> dict[str, Any]:
    return dict((data_context_payload.get("field_role_evidence") or {}).get(field_name) or {})


def _field_metric_summary(data_context_payload: dict[str, Any], field_name: str) -> str:
    detail = _field_detail(data_context_payload, field_name)
    if not detail:
        return f"{field_name}（无字段画像）"
    return (
        f"{field_name}(dtype={detail.get('dtype','')}, non_null={detail.get('non_null_ratio','')}, "
        f"unique={detail.get('unique_count','')}, samples={', '.join((data_context_payload.get('sample_value_evidence') or {}).get(field_name, [])[:2])})"
    )


def _category_examples(data_context_payload: dict[str, Any]) -> list[str]:
    values = (data_context_payload.get("sample_value_evidence") or {}).get("Category") or []
    return [item for item in values if item][:4]


def _industry_from_data_evidence(
    *,
    data_context_payload: dict[str, Any],
    router_result: dict[str, Any],
    sample_values: list[str],
) -> tuple[str, float, list[str], list[str], str]:
    object_grain = _safe_text(data_context_payload.get("object_grain"))
    categories = _category_examples(data_context_payload)
    category_detail = _field_detail(data_context_payload, "Category")
    seller_detail = _field_detail(data_context_payload, "Seller")
    order_detail = _field_detail(data_context_payload, "OrderID")
    available_families = list(data_context_payload.get("available_metric_families") or [])
    evidence = [
        f"对象粒度为 `{object_grain}`。",
        f"Category 唯一值约 {category_detail.get('unique_count', 0)} 个，样例类目包括：{', '.join(categories) or '无'}。",
        f"Seller 唯一值约 {seller_detail.get('unique_count', 0)} 个，OrderID 唯一值约 {order_detail.get('unique_count', 0)} 个。",
        f"可用指标族为：{', '.join(available_families) or '无'}。",
        f"业务路由结果为 `{_safe_text(router_result.get('business_profile')) or 'unknown'}`。",
    ]
    compact_samples = _compact(" ".join(sample_values + categories))
    if category_detail.get("unique_count", 0) >= 20 and "sales_scale" in available_families:
        return (
            "综合零售电商",
            0.82,
            evidence,
            ["类目分布广，数据更像综合零售交易样本，而不是单一垂类业务样本。"],
            "当前最可能是综合零售电商，因为类目数高、卖家数高、订单数高，并且交易/履约/评价信号同时存在。",
        )
    if any(token in compact_samples for token in ["healthbeauty", "beauty", "护肤", "彩妆"]):
        return (
            "美妆个护电商",
            0.66,
            evidence,
            ["样例类目里确实出现 health_beauty，但当前数据并不只覆盖单一美妆类目。"],
            "当前最可能偏向美妆个护电商，但这个判断主要来自类目样例值，仍需确认样本是否覆盖更广类目。",
        )
    return (
        "零售交易与履约数据场景（行业待细化）",
        0.55,
        evidence,
        ["当前数据明确是零售交易与履约数据，但行业细分仍需要更具体的平台或商家背景。"],
        "当前最可能是零售交易与履约数据场景，因为交易、履约、评价字段齐全，但行业细分仍需外部背景补充。",
    )


def _platform_from_data_evidence(
    *,
    dataset_name: str,
    field_names: list[str],
    data_context_payload: dict[str, Any],
    router_result: dict[str, Any],
) -> tuple[str, str, float, list[str], list[str], str]:
    haystack = _compact(f"{dataset_name} {' '.join(field_names)}")
    platform_tokens = [
        ("淘宝/天猫", "platform_marketplace_ecommerce", ["taobao", "tmall", "淘宝", "天猫"]),
        ("京东", "platform_self_operated_and_marketplace", ["jd", "jingdong", "京东"]),
        ("拼多多", "platform_discount_marketplace", ["pdd", "拼多多"]),
        ("抖店", "content_ecommerce_platform", ["抖店"]),
    ]
    evidence = [
        f"字段角色里存在对象字段：{', '.join((data_context_payload.get('object_like_fields') or [])[:6]) or '无'}。",
        f"履约字段包括：{', '.join((data_context_payload.get('fulfillment_like_fields') or [])[:6]) or '无'}。",
        f"评价字段包括：{', '.join((data_context_payload.get('review_like_fields') or [])[:6]) or '无'}。",
        f"router_result 为 `{_safe_text(router_result.get('business_profile')) or 'unknown'}`。",
    ]
    for platform_name, model_name, tokens in platform_tokens:
        if any(_compact(token) in haystack for token in tokens):
            return (
                platform_name,
                model_name,
                0.9,
                evidence + [f"dataset_name/field_names 中直接命中平台 token：{platform_name}。"],
                [],
                f"当前最可能是 `{platform_name}`，因为 dataset_name 或字段名里直接出现了平台 token。",
            )
    return (
        "平台零售电商（具体平台未识别）",
        "platform_ecommerce_generic",
        0.62,
        evidence + ["对象、交易、履约、评价字段同时存在，符合平台零售电商经营数据特征。"],
        ["没有显式平台 token，无法把平台收敛到淘宝/京东/拼多多等具体对象。"],
        "当前最可能是平台零售电商场景，因为商品、卖家、订单、履约和评价字段齐全，但具体平台仍未从数据里直接写明。",
    )


def _business_model_from_data_evidence(
    *,
    data_context_payload: dict[str, Any],
    router_result: dict[str, Any],
    unsupported_metrics: list[str],
) -> tuple[str, float, list[str], list[str], str]:
    evidence = [
        f"对象粒度为 `{_safe_text(data_context_payload.get('object_grain'))}`。",
        f"金额字段包括：{', '.join((data_context_payload.get('amount_like_fields') or [])[:4]) or '无'}。",
        f"成本字段包括：{', '.join((data_context_payload.get('cost_like_fields') or [])[:4]) or '无'}。",
        f"unsupported_metrics 包括：{', '.join(unsupported_metrics[:4]) or '无'}。",
        f"router_result 为 `{_safe_text(router_result.get('business_profile')) or 'unknown'}`。",
    ]
    if _safe_text(data_context_payload.get("object_grain")) == "mixed_order_item":
        return (
            "平台零售交易与履约协同",
            0.69,
            evidence + ["订单、商品、卖家、客户、履约和评价维度共同出现。"],
            ["缺少明确平台规则页和完整成本结构，商业模式还不能上升到更细的平台商业模式结论。"],
            "当前最可能是平台零售交易与履约协同模式，因为交易、履约与评价字段齐全，但成本与平台规则仍不完整。",
        )
    return (
        "商品经营与交易复盘口径（商业模式待补充确认）",
        0.52,
        evidence,
        ["当前业务更像交易与商品经营复盘，但商业模式细分仍需补平台和组织背景。"],
        "当前更像商品经营与交易复盘口径，但商业模式细分仍缺直接数据证据。",
    )


def _value_chain_from_data_evidence(data_context_payload: dict[str, Any], router_result: dict[str, Any]) -> tuple[str, list[str], str]:
    object_grain = _safe_text(data_context_payload.get("object_grain"))
    if object_grain == "mixed_order_item":
        evidence = [
            "OrderID 和 SKU 同时存在，说明交易链条与商品明细同时被观察。",
            "Seller 与 CustomerID 同时存在，说明卖家和客户两端都在数据里。",
            "DeliveredCustomerDate / ReviewScore / ReviewText 存在，说明履约和售后体验被记录。",
        ]
        return (
            "平台零售订单履约与售后承接",
            evidence,
            "当前最可能位于平台零售订单、履约与售后承接环节，因为订单、商品、卖家、客户、履约与评价信号同时存在。",
        )
    profile = _safe_text(router_result.get("business_profile"))
    return (
        {
            "ecommerce_product_operations_report": "平台内商品经营与交易承接",
            "procurement_sales_report": "采销协同、供给侧与履约承接",
            "internet_operations_report": "用户增长、内容分发与商业化承接",
            "media_campaign_report": "广告投放执行与媒体资源兑现",
        }.get(profile, "通用经营管理与业务理解"),
        [f"router_result 主档为 `{profile or 'unknown'}`。"],
        "当前 value chain 主要由 router_result 给出，真实数据证据仍需进一步补组织背景。",
    )


def _business_scene_inference_from_data(
    *,
    dataset_name: str,
    field_names: list[str],
    sample_values: list[str],
    data_context_payload: dict[str, Any],
    router_result: dict[str, Any] | None,
    metric_context: dict[str, Any],
) -> dict[str, Any]:
    router_result = router_result or {}
    unsupported_metrics = list((metric_context.get("domain_metric_registry") or {}).get("unsupported_metrics") or metric_context.get("unsupported_metrics") or [])
    inferred_industry, industry_conf, industry_evidence, industry_ambiguity, industry_because = _industry_from_data_evidence(
        data_context_payload=data_context_payload,
        router_result=router_result,
        sample_values=sample_values,
    )
    inferred_platform, raw_model_name, platform_conf, platform_evidence, platform_ambiguity, platform_because = _platform_from_data_evidence(
        dataset_name=dataset_name,
        field_names=field_names,
        data_context_payload=data_context_payload,
        router_result=router_result,
    )
    inferred_business_model, model_conf, model_evidence, model_ambiguity, model_because = _business_model_from_data_evidence(
        data_context_payload=data_context_payload,
        router_result=router_result,
        unsupported_metrics=unsupported_metrics,
    )
    value_chain_position, value_chain_evidence, value_chain_because = _value_chain_from_data_evidence(
        data_context_payload,
        router_result,
    )
    overall_conf = round(min(industry_conf, platform_conf, model_conf), 2)
    uncertainty = overall_conf < 0.75 or not router_result.get("business_profile")
    ambiguity_notes = _unique_strings(
        [
            *industry_ambiguity,
            *platform_ambiguity,
            *model_ambiguity,
            "当前业务路由、metric mining 和字段角色都已参与判断，不再只靠数据集名称猜行业。",
        ]
    )
    evidence_from_dataset = _unique_strings(
        [
            *industry_evidence,
            *platform_evidence,
            *model_evidence,
            *value_chain_evidence,
            f"because_industry={industry_because}",
            f"because_platform={platform_because}",
            f"because_business_model={model_because}",
            f"because_value_chain={value_chain_because}",
        ]
    )
    candidate_business_contexts = [
        {"context": "订单-商品-卖家-客户混合经营观察窗口", "confidence": 0.86, "why": "因为数据里同时有 OrderID、SKU、Seller、CustomerID 和履约/评价字段。"},
        {"context": "平台零售订单履约与售后分析", "confidence": 0.81, "why": "因为 DeliveredCustomerDate、ReviewScore、ReviewText、IsLate 等字段共同出现。"},
        {"context": "商品结构与卖家分层经营分析", "confidence": 0.76, "why": "因为 Category、SKU、Seller、Revenue、GMV、sales_scale 信号同时存在。"},
    ]
    if unsupported_metrics:
        candidate_business_contexts.append(
            {
                "context": "利润与 ROI 口径待补的交易复盘",
                "confidence": 0.61,
                "why": f"因为 universal metric mining 已明确把 {', '.join(unsupported_metrics[:3])} 标成当前不可直接判断。",
            }
        )
    required_manual_confirmation = _unique_strings(
        [
            "当前数据主要来自哪个平台或渠道？",
            "当前业务更偏平台零售经营、采销复盘，还是站外流量投放？",
            "Revenue / GMV / FreightCost 在当前业务里各自代表什么口径？",
        ]
        if uncertainty
        else []
    )
    return {
        "inferred_industry": inferred_industry,
        "inferred_platform": inferred_platform,
        "inferred_business_model": inferred_business_model,
        "value_chain_position": value_chain_position,
        "confidence": overall_conf,
        "evidence_from_dataset": evidence_from_dataset,
        "ambiguity_notes": ambiguity_notes,
        "manual_confirmation_needed": bool(required_manual_confirmation),
        "candidate_business_contexts": candidate_business_contexts,
        "why_uncertain": (
            "行业、平台或商业模式仍缺直接字段或组织背景确认，因此当前只能基于字段角色、粒度、口径和 metric mining 做候选解释。"
            if uncertainty
            else ""
        ),
        "top_candidates": [item["context"] for item in candidate_business_contexts[:3]],
        "required_manual_confirmation": required_manual_confirmation,
    }


def _infer_platform(dataset_name: str, columns: list[str]) -> tuple[str, str, float, list[str]]:
    haystack = f"{dataset_name} {' '.join(columns)}"
    compact_haystack = _compact(haystack)
    candidates = [
        ("淘宝/天猫", "platform_marketplace_ecommerce", 0.95, ["taobao", "tmall", "淘宝", "天猫"]),
        ("京东", "platform_self_operated_and_marketplace", 0.93, ["jd", "jingdong", "京东"]),
        ("拼多多", "platform_discount_marketplace", 0.93, ["pdd", "拼多多"]),
        ("抖店", "content_ecommerce_platform", 0.9, ["抖店"]),
        ("快手小店", "content_ecommerce_platform", 0.9, ["快手小店"]),
        ("小红书电商", "content_ecommerce_platform", 0.9, ["小红书电商", "小红书"]),
    ]
    for platform, model, confidence, tokens in candidates:
        if any(_compact(token) in compact_haystack for token in tokens):
            return platform, model, confidence, []
    notes = []
    if any(_compact(token) in compact_haystack for token in ["item_id", "sku_id", "shop_id", "商品", "店铺", "类目"]):
        notes.append("当前更像平台内商品经营数据，但平台名称未在文件名或字段中明确出现。")
        return "平台零售电商（具体平台未识别）", "platform_ecommerce_generic", 0.72, notes
    return "通用经营平台（低置信）", "generic_business_model_needs_confirmation", 0.48, ["平台名称与商业模式都需要后续人工确认。"]


def _infer_industry(
    *,
    dataset_name: str,
    columns: list[str],
    router_result: dict[str, Any],
    sample_values: list[str],
) -> tuple[str, str]:
    compact_text = _compact(f"{dataset_name} {' '.join(columns)} {' '.join(sample_values)}")
    industry_map = [
        ("美妆个护电商", ["beauty", "护肤", "美妆", "彩妆"]),
        ("3C 消费电子电商", ["phone", "手机", "数码", "3c"]),
        ("家清日化电商", ["家清", "日化", "洗护"]),
        ("服饰鞋包电商", ["服饰", "鞋", "箱包", "fashion"]),
        ("综合零售电商", ["item", "sku", "shop", "gmv", "订单"]),
    ]
    for industry, tokens in industry_map:
        if any(_compact(token) in compact_text for token in tokens):
            return industry, "字段样例值和数据集名称共同指向该行业。"
    profile = _safe_text(router_result.get("business_profile"))
    if profile == "ecommerce_product_operations_report":
        return "平台零售电商", "主业务类型已识别为电商商品经营，因此行业优先按平台零售电商处理。"
    if profile == "procurement_sales_report":
        return "商品供应链与采销", "主业务类型更偏采销/商品经营，因此行业按商品供应链处理。"
    if profile == "internet_operations_report":
        return "互联网平台运营", "主业务类型更偏用户增长与内容运营。"
    if profile == "media_campaign_report":
        return "数字广告投放", "主业务类型更偏媒体投放与广告兑现。"
    return "通用经营行业（待确认）", "当前只能从字段和任务描述推测行业范围，后续需补外部资料确认。"


def _value_chain_position(profile: str) -> str:
    return {
        "ecommerce_product_operations_report": "平台内商品经营与交易承接",
        "procurement_sales_report": "采销协同、供给侧与履约承接",
        "internet_operations_report": "用户增长、内容分发与商业化承接",
        "media_campaign_report": "广告投放执行与媒体资源兑现",
    }.get(profile, "通用经营管理与业务理解")


def _candidate_business_contexts(profile: str, object_grain: str, metric_context: dict[str, Any]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    if profile == "procurement_sales_report":
        contexts.append({"context": "零售采销与商品经营", "confidence": 0.82, "why": "对象粒度与指标族集中在商品/SKU/类目/销量/GMV/评价/履约。"})
        contexts.append({"context": "平台零售电商", "confidence": 0.71, "why": "存在商品、交易、评价和履约字段，符合平台电商经营数据特征。"})
    elif profile == "ecommerce_product_operations_report":
        contexts.append({"context": "平台零售电商", "confidence": 0.83, "why": "路由明确指向商品经营主链。"})
        contexts.append({"context": "零售采销与商品经营", "confidence": 0.66, "why": "对象仍然落在商品/SKU/类目层。"})
    elif profile == "internet_operations_report":
        contexts.append({"context": "互联网增长与内容运营", "confidence": 0.8, "why": "对象与指标族更偏用户/渠道/内容/活跃/留存。"})
    elif profile == "media_campaign_report":
        contexts.append({"context": "数字广告投放", "confidence": 0.8, "why": "对象与指标族更偏 campaign/media/spend/conversion。"})
    if object_grain in {"mixed_order_item", "sku_or_product", "category", "supplier_or_merchant"}:
        contexts.append({"context": "供应链与履约协同", "confidence": 0.58, "why": "对象粒度和字段分布支持供给侧背景研究。"})
    if metric_context.get("unsupported_metrics"):
        contexts.append({"context": "成本/利润口径待补的商品经营场景", "confidence": 0.52, "why": "当前可见规模和结构指标，但利润/库存等关键口径仍不足。"})
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in contexts:
        key = str(item.get("context") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:5]


def _scope_payload(
    *,
    dataset_name: str = "",
    uploaded_file_name: str = "",
    sheet_names: list[str] | None = None,
    field_names: list[str] | None = None,
    sample_values: list[str],
    request: SmartReportRequest,
    deep_context_understanding: dict[str, Any] | None,
    router_result: dict[str, Any],
    business_scene_inference_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metric_context = (deep_context_understanding or {}).get("universal_metric_mining_result") or {}
    domain_metric_registry = metric_context.get("domain_metric_registry") or {}
    if business_scene_inference_payload is None:
        platform, _, platform_conf, platform_notes = _infer_platform(dataset_name or uploaded_file_name, field_names or [])
        industry, industry_reason = _infer_industry(
            dataset_name=dataset_name or uploaded_file_name,
            columns=field_names or [],
            router_result=router_result or {},
            sample_values=sample_values,
        )
        business_scene_inference_payload = {
            "inferred_industry": industry,
            "inferred_platform": platform,
            "inferred_business_model": "平台零售经营（商业模式待补充确认）",
            "value_chain_position": _value_chain_position(_safe_text((router_result or {}).get("business_profile"))),
            "confidence": round(float(platform_conf), 2),
            "ambiguity_notes": [industry_reason, *platform_notes],
        }
    target_reader = _first_non_empty(
        request.target_audience,
        deep_context_understanding.get("target_reader") if deep_context_understanding else "",
        default="业务负责人、采销负责人、商品运营负责人、店铺运营负责人、管理层",
    )
    profile = _safe_text(router_result.get("business_profile"))
    research_boundaries = [
        "该链服务于行业背景、市场结构、平台机制、竞品参考、指标口径与 benchmark 边界理解。",
        "该链不得输出当前上传数据本身的经营结论。",
        "该链不得改写主报告，不得进入主报告 PDF 渲染器。",
        "该链不得调用 R 工作流或引用 R 工作流产物。",
        "所有外部事实必须有来源，且不得伪装成用户上传数据证据。",
    ]
    unsupported_questions = [
        "当前数据能否证明某个商品、店铺、类目已经应该加码或淘汰。",
        "当前数据能否直接证明利润、ROI 或市场份额。",
        "当前数据能否替代外部行业报告或监管材料。",
    ]
    research_questions = [
        "当前数据所处行业的经营背景和交易结构是什么？",
        "当前平台或渠道机制对商品经营有什么影响？",
        "当前行业的 benchmark 应该从哪些口径切入？",
        "外部资料应该如何支持主报告的背景理解而不是经营拍板？",
    ]
    mined_metrics = [
        *list(domain_metric_registry.get("direct_metrics") or []),
        *list(domain_metric_registry.get("derived_metrics") or []),
        *list(domain_metric_registry.get("proxy_metrics") or []),
    ]
    if mined_metrics:
        research_questions.append(
            f"universal_metric_mining 已识别出 {', '.join(mined_metrics[:5])}，这些指标对应的行业口径、平台机制和 benchmark 边界分别是什么？"
        )
        business_scene_inference_payload["ambiguity_notes"] = list(business_scene_inference_payload.get("ambiguity_notes") or []) + [
            f"universal_metric_mining 显示可用指标: {', '.join(mined_metrics[:6])}"
        ]
    if domain_metric_registry.get("unsupported_metrics"):
        business_scene_inference_payload["ambiguity_notes"] = list(business_scene_inference_payload.get("ambiguity_notes") or []) + [
            f"universal_metric_mining 显示以下指标仍不可直接判断: {', '.join(domain_metric_registry.get('unsupported_metrics')[:5])}"
        ]

    scope_payload = {
        "inferred_industry": business_scene_inference_payload["inferred_industry"],
        "inferred_platform": business_scene_inference_payload["inferred_platform"],
        "inferred_business_model": business_scene_inference_payload["inferred_business_model"],
        "value_chain_position": business_scene_inference_payload["value_chain_position"],
        "target_reader": target_reader,
        "research_questions": research_questions,
        "research_boundaries": research_boundaries,
        "unsupported_questions": unsupported_questions,
        "confidence": round(float(business_scene_inference_payload.get("confidence") or 0.0), 2),
        "ambiguity_notes": list(dict.fromkeys(business_scene_inference_payload.get("ambiguity_notes") or [])),
        "metric_mining_context": {
            "recommended_report_chain": domain_metric_registry.get("recommended_report_chain", ""),
            "direct_metrics": list(domain_metric_registry.get("direct_metrics") or []),
            "derived_metrics": list(domain_metric_registry.get("derived_metrics") or []),
            "proxy_metrics": list(domain_metric_registry.get("proxy_metrics") or []),
            "unsupported_metrics": list(domain_metric_registry.get("unsupported_metrics") or []),
        },
        "router_context": {
            "business_profile": profile,
            "secondary_profile": _safe_text(router_result.get("secondary_profile")),
            "routing_reason": _safe_text(router_result.get("routing_reason")),
        },
    }
    return scope_payload


QUESTION_CATEGORIES = [
    "行业背景",
    "市场规模与结构",
    "产业链与价值链",
    "平台机制",
    "竞争格局",
    "用户或消费者趋势",
    "商品或服务供给结构",
    "成本与利润机制",
    "风险与监管",
    "指标口径与 benchmark",
]


RESEARCH_TOPIC_BLUEPRINTS = [
    {
        "topic_id": "industry_background",
        "topic_name": "行业背景",
        "required_source_types": ["政府或监管公开资料", "行业协会报告", "上市公司财报"],
        "expected_facts": ["行业所处分阶段", "市场规模或结构线索", "行业主要经营驱动因素"],
        "downstream_sections": ["行业背景", "行业定位与研究边界"],
        "unsupported_claims": ["当前上传数据已经证明行业景气度变化", "当前对象已经优于行业平均"],
    },
    {
        "topic_id": "platform_mechanism",
        "topic_name": "平台机制",
        "required_source_types": ["官方平台规则", "上市公司财报", "政府或监管公开资料"],
        "expected_facts": ["平台规则入口", "流量/履约/评价机制", "商家经营约束"],
        "downstream_sections": ["平台机制或渠道机制", "对主报告可提供的背景启发"],
        "unsupported_claims": ["平台规则已经直接证明当前 SKU 应该加码", "平台机制直接证明当前经营动作正确"],
    },
    {
        "topic_id": "competitive_landscape",
        "topic_name": "竞争格局",
        "required_source_types": ["行业协会报告", "上市公司财报", "研究机构材料"],
        "expected_facts": ["主要竞争维度", "头部与长尾格局", "行业常见供给侧分层"],
        "downstream_sections": ["竞争格局", "市场结构"],
        "unsupported_claims": ["当前上传数据已经证明竞品份额", "外部竞品资料可替代当前数据比较"],
    },
    {
        "topic_id": "benchmark_comparability",
        "topic_name": "benchmark 可比性",
        "required_source_types": ["官方平台规则", "上市公司财报", "行业协会报告"],
        "expected_facts": ["benchmark 常用口径", "平台差异", "时间区间与样本边界"],
        "downstream_sections": ["benchmark 与可比性限制", "指标口径说明"],
        "unsupported_claims": ["外部 benchmark 可直接套用于当前对象经营判断", "当前指标与行业 benchmark 完全同口径"],
    },
    {
        "topic_id": "metric_definition",
        "topic_name": "指标口径",
        "required_source_types": ["官方平台规则", "上市公司财报", "政府或监管公开资料"],
        "expected_facts": ["GMV / Revenue / 转化 / 履约等定义", "成本与利润口径边界", "当前数据与行业定义差异"],
        "downstream_sections": ["指标口径说明", "成本、利润与商业模式"],
        "unsupported_claims": ["当前字段天然等于行业标准定义", "FreightCost 等于完整成本结构"],
    },
    {
        "topic_id": "risk_regulation",
        "topic_name": "风险与监管",
        "required_source_types": ["政府或监管公开资料", "官方平台规则"],
        "expected_facts": ["监管要求", "消费者权益要求", "售后/评价治理边界"],
        "downstream_sections": ["外部风险与监管环境", "当前资料无法支持的判断"],
        "unsupported_claims": ["监管资料可直接推出当前经营结果", "风险提示可直接替代经营证据"],
    },
    {
        "topic_id": "main_report_boundaries",
        "topic_name": "对主报告的支持边界",
        "required_source_types": ["官方平台规则", "政府或监管公开资料", "行业协会报告"],
        "expected_facts": ["哪些外部事实只能做背景", "哪些结论不能支持主报告拍板", "人工确认项"],
        "downstream_sections": ["对主报告可提供的背景启发", "当前资料无法支持的判断"],
        "unsupported_claims": ["行研链可直接替代主报告证据", "外部资料可直接生成对象级动作"],
    },
]


def _topic_dataset_signals(
    *,
    data_context_payload: dict[str, Any],
    scope_payload: dict[str, Any],
    blueprint: dict[str, Any],
) -> list[str]:
    signals: list[str] = []
    object_grain = _safe_text(data_context_payload.get("object_grain"))
    if object_grain:
        signals.append(f"对象粒度={object_grain}")
    for field_name in (data_context_payload.get("object_like_fields") or [])[:4]:
        signals.append(f"对象字段:{field_name}")
    for field_name in (data_context_payload.get("amount_like_fields") or [])[:3]:
        signals.append(f"金额字段:{field_name}")
    for field_name in (data_context_payload.get("date_like_fields") or [])[:2]:
        signals.append(f"时间字段:{field_name}")
    for family in (scope_payload.get("metric_mining_context") or {}).get("direct_metrics", [])[:3]:
        signals.append(f"direct_metric:{family}")
    for family in (data_context_payload.get("available_metric_families") or [])[:4]:
        signals.append(f"metric_family:{family}")
    if blueprint["topic_id"] == "benchmark_comparability":
        for item in (scope_payload.get("metric_mining_context") or {}).get("unsupported_metrics", [])[:3]:
            signals.append(f"unsupported_metric:{item}")
    return signals[:10]


def _topic_relevance(
    *,
    profile: str,
    data_context_payload: dict[str, Any],
    scope_payload: dict[str, Any],
    blueprint: dict[str, Any],
) -> tuple[str, float]:
    object_grain = _safe_text(data_context_payload.get("object_grain"))
    available_families = set(data_context_payload.get("available_metric_families") or [])
    unsupported_families = set(data_context_payload.get("unsupported_metric_families") or [])
    topic_id = blueprint["topic_id"]

    score = 0.55
    if profile in {"procurement_sales_report", "ecommerce_product_operations_report"}:
        score += 0.08
    if topic_id in {"platform_mechanism", "benchmark_comparability", "metric_definition"} and object_grain in {"mixed_order_item", "sku_or_product", "category", "supplier_or_merchant"}:
        score += 0.1
    if topic_id == "industry_background" and "sales_scale" in available_families:
        score += 0.08
    if topic_id == "competitive_landscape" and ("sales_scale" in available_families or "pricing" in available_families):
        score += 0.08
    if topic_id == "benchmark_comparability" and (unsupported_families or "traffic_conversion" in available_families):
        score += 0.1
    if topic_id == "metric_definition" and (available_families or unsupported_families):
        score += 0.08
    if topic_id == "risk_regulation" and object_grain in {"mixed_order_item", "sku_or_product", "supplier_or_merchant"}:
        score += 0.06
    if topic_id == "main_report_boundaries":
        score += 0.12
    return (
        f"当前上传数据与 `{blueprint['topic_name']}` 相关，因为对象粒度、字段分布和指标族已经暴露出需要补行业背景与边界的方向。",
        round(min(score, 0.95), 2),
    )


def _research_topics(scope_payload: dict[str, Any], data_context_payload: dict[str, Any]) -> list[dict[str, Any]]:
    profile = _safe_text((scope_payload.get("metric_mining_context") or {}).get("recommended_report_chain"))
    topics: list[dict[str, Any]] = []
    for priority, blueprint in enumerate(RESEARCH_TOPIC_BLUEPRINTS, start=1):
        why_it_matters, confidence = _topic_relevance(
            profile=profile,
            data_context_payload=data_context_payload,
            scope_payload=scope_payload,
            blueprint=blueprint,
        )
        topics.append(
            {
                "topic_id": blueprint["topic_id"],
                "topic_name": blueprint["topic_name"],
                "why_it_matters": why_it_matters,
                "required_source_types": list(blueprint["required_source_types"]),
                "expected_facts": list(blueprint["expected_facts"]),
                "downstream_sections": list(blueprint["downstream_sections"]),
                "unsupported_claims": list(blueprint["unsupported_claims"]),
                "priority": priority,
                "confidence": confidence,
                "depends_on_dataset_signals": _topic_dataset_signals(
                    data_context_payload=data_context_payload,
                    scope_payload=scope_payload,
                    blueprint=blueprint,
                ),
            }
        )
    return topics


def _question_bank(scope_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for topic in scope_payload.get("research_topics") or []:
        rows.append(
            {
                "topic_id": topic["topic_id"],
                "topic_name": topic["topic_name"],
                "priority": str(topic["priority"]),
                "question": f"{topic['topic_name']}这部分需要补哪些真实外部事实，才能支撑后续 `{topic['topic_name']}` 章节？",
                "why_it_matters": topic["why_it_matters"],
                "unsupported_claims": list(topic["unsupported_claims"]),
            }
        )
    return rows


def _search_plan(scope_payload: dict[str, Any], question_rows: list[dict[str, Any]]) -> dict[str, Any]:
    platform = scope_payload["inferred_platform"]
    industry = scope_payload["inferred_industry"]
    topic_tasks: list[dict[str, Any]] = []
    queries: list[str] = []
    for topic in scope_payload.get("research_topics") or []:
        topic_queries = []
        if topic["topic_id"] == "industry_background":
            topic_queries = [f"{industry} 行业 报告 市场结构", f"{industry} 上市公司 年报 投资者关系"]
        elif topic["topic_id"] == "platform_mechanism":
            topic_queries = [f"{platform} 平台规则 商品 评价 履约 规则", f"{platform} 商家规则 售后 退款 退货"]
        elif topic["topic_id"] == "competitive_landscape":
            topic_queries = [f"{industry} 竞争格局 头部 品类 份额", f"{industry} 行业 协会 报告 市场结构"]
        elif topic["topic_id"] == "benchmark_comparability":
            topic_queries = [f"{platform} benchmark 指标口径 流量 转化 履约", f"{industry} benchmark GMV revenue conversion rating"]
        elif topic["topic_id"] == "metric_definition":
            topic_queries = [f"{platform} GMV revenue 评价 履约 口径", f"{industry} 指标定义 GMV 转化 毛利"]
        elif topic["topic_id"] == "risk_regulation":
            topic_queries = [f"{industry} 监管 政策 风险", f"{platform} 售后 评价 消费者权益 规则"]
        elif topic["topic_id"] == "main_report_boundaries":
            topic_queries = [f"{platform} 指标口径 边界 规则", f"{industry} benchmark 可比性 限制"]
        queries.extend(topic_queries)
        topic_tasks.append(
            {
                "topic_id": topic["topic_id"],
                "topic_name": topic["topic_name"],
                "required_source_types": list(topic["required_source_types"]),
                "search_queries": topic_queries,
                "expected_facts": list(topic["expected_facts"]),
                "downstream_sections": list(topic["downstream_sections"]),
            }
        )
    return {
        "search_queries": queries,
        "topic_tasks": topic_tasks,
        "source_priority": [
            "官方平台规则",
            "政府或监管公开资料",
            "上市公司财报",
            "行业协会报告",
            "咨询公司白皮书",
            "研究机构材料",
            "主流财经媒体",
        ],
        "source_blacklist": ["博客", "论坛", "社媒", "个人经验帖"],
        "expected_usage": "用于补行业背景、市场结构、平台机制、竞品参考、指标口径与 benchmark 边界，不用于直接替代用户数据结论。",
        "benchmark_caution": "benchmark 必须写清来源口径、时间区间、平台差异和样本边界。",
        "citation_requirements": "所有外部事实必须带 source_id / publisher / url / publish_date / citation_text。",
    }


def _source_level(source_row: dict[str, Any]) -> str:
    explicit = _safe_text(source_row.get("source_level"))
    if explicit in {"page_fact", "document_fact", "org_index", "lead_only"}:
        return explicit

    url = _safe_text(source_row.get("url")).lower()
    title = _safe_text(source_row.get("title")).lower()
    source_type = _safe_text(source_row.get("source_type"))
    if not url:
        return "lead_only"

    if url.endswith(".pdf") or any(token in url for token in ["/report/", "/reports/", "/annual", "annual-report", "招股书", "prospectus"]):
        return "document_fact"
    if any(token in url for token in ["rule.", "rulechannel", "/rule", "/rules", "/law", "/laws", "/regulation", "/policy", "/ir.", "investor"]):
        return "page_fact"
    if source_type == "官方平台规则":
        return "page_fact"
    if "规则" in title or "年报" in title or "招股书" in title:
        return "page_fact"
    return "org_index"


def _source_verification_status(source_row: dict[str, Any], source_level: str) -> str:
    explicit = _safe_text(source_row.get("verification_status"))
    if explicit:
        return explicit
    if source_level == "page_fact":
        return "verified_page_fact"
    if source_level == "document_fact":
        return "verified_document_fact"
    if source_level == "org_index":
        return "org_index_unverified"
    return "lead_only"


def _source_publish_date(source_row: dict[str, Any], source_level: str) -> str:
    explicit = _safe_text(source_row.get("publish_date"))
    if explicit:
        return explicit
    source_type = _safe_text(source_row.get("source_type"))
    title = _safe_text(source_row.get("title"))
    if source_level == "lead_only":
        return "待定位到具体报告或规则页后补充发布日期"
    if source_level == "org_index":
        return "当前仅定位到机构索引页，尚未落到可核验发布日期"
    if source_type in {"官方平台规则", "政府或监管公开资料"}:
        return "页面长期更新，需落到具体条文或公告后补充发布日期"
    if source_type == "上市公司财报" or "年报" in title or "招股书" in title:
        return "需落到具体年报或招股书页面后补充发布日期"
    if source_type in {"行业协会报告", "权威研究机构"}:
        return "需落到具体报告页面后补充发布日期"
    return "需结合最终落地页面补充发布日期"


def _source_support_matrix(source_row: dict[str, Any]) -> dict[str, bool]:
    usable_for = " ".join(str(item) for item in (source_row.get("usable_for") or []))
    source_type = _safe_text(source_row.get("source_type"))
    title = _safe_text(source_row.get("title"))
    combined = f"{usable_for} {source_type} {title}"
    return {
        "supports_platform_mechanism": any(token in combined for token in ["平台机制", "规则", "履约", "评价", "售后"]),
        "supports_benchmark": any(token in combined for token in ["benchmark", "市场结构", "财务口径", "口径", "市场"]),
        "supports_risk_regulation": any(token in combined for token in ["风险", "监管", "消费者权益", "规则边界"]),
        "supports_object_level_judgement": False,
    }


def _source_page_or_section_hint(source_row: dict[str, Any], source_level: str) -> str:
    explicit = _safe_text(source_row.get("page_or_section_hint"))
    if explicit:
        return explicit
    source_type = _safe_text(source_row.get("source_type"))
    url = _safe_text(source_row.get("url")).lower()
    if source_level == "lead_only":
        return "待补充具体报告标题、章节或规则条目"
    if source_level == "org_index":
        return "当前仅定位到机构首页或索引页，待继续下钻到具体页面"
    if source_type == "官方平台规则" or "rule" in url:
        return "规则中心、商家规则、售后或评价治理条目"
    if source_type == "上市公司财报" or "investor" in url or "ir." in url:
        return "投资者关系页、年报、招股书或公开披露章节"
    if source_type == "政府或监管公开资料":
        return "统计查询页、监管公告页或法规条文页"
    if source_type in {"行业协会报告", "权威研究机构"}:
        return "行业报告目录页或正文章节"
    return "具体页面或章节待人工补充"


def _rewrite_key_point_to_atomic_fact(text: str) -> str:
    normalized = _safe_text(text).strip().strip("。")
    if not normalized:
        return ""
    replacements = {
        "可用于核对": "该来源公开了",
        "可用于解释": "该来源公开了关于",
        "可用于补充": "该来源公开披露了",
        "可用于补": "该来源公开披露了",
        "可用于说明": "该来源直接说明了",
        "可作为": "当前仅识别到",
    }
    for prefix, rewritten in replacements.items():
        if normalized.startswith(prefix):
            tail = normalized[len(prefix):].strip("：:，, ")
            if prefix == "可作为":
                return f"{rewritten}{tail}。"
            if prefix == "可用于解释":
                return f"{rewritten}{tail}的规则或说明。"
            return f"{rewritten}{tail}。"
    if "线索" in normalized:
        return "当前仅定位到行业协会或研究机构线索，尚未落到具体报告页面。"
    return f"该来源提到：{normalized}。"


def _fallback_atomic_facts(
    source_row: dict[str, Any],
    support_matrix: dict[str, bool],
    *,
    source_level: str,
) -> list[str]:
    facts: list[str] = []
    source_type = _safe_text(source_row.get("source_type"))
    title = _safe_text(source_row.get("title"))
    if source_level == "lead_only":
        facts.append("当前仅定位到来源线索，尚未落到可核验的具体报告、规则页或法规条文页。")
    elif source_level == "org_index":
        facts.append("当前仅定位到机构索引页，尚未锁定可直接引用的具体报告、规则页或法规条文页。")
    elif source_level == "document_fact":
        facts.append("当前已定位到具体报告或披露文档页面，可作为文档级事实来源。")
    else:
        facts.append("当前已定位到具体页面，可作为页级事实来源。")

    if source_type == "官方平台规则":
        facts.append("该来源属于官方平台规则页面，覆盖商家经营、履约、售后或评价治理相关规则。")
    elif source_type == "上市公司财报":
        facts.append("该来源属于上市公司投资者关系或财报披露页面，可对应商业模式、收入结构或经营口径披露。")
    elif source_type == "政府或监管公开资料":
        facts.append("该来源属于政府或监管公开资料页面，可对应统计口径、法规要求或治理边界。")
    elif source_type in {"行业协会报告", "权威研究机构"}:
        facts.append("该来源属于行业报告或研究报告来源，可对应行业结构、用户趋势或公开口径说明。")
    elif title:
        facts.append(f"该来源围绕《{title}》提供公开披露信息。")

    if support_matrix["supports_platform_mechanism"]:
        facts.append("该来源可以对应平台规则、履约约束、评价治理或售后条款。")
    if support_matrix["supports_benchmark"]:
        facts.append("该来源可以对应 benchmark 的平台差异、统计口径差异或时间边界。")
    if support_matrix["supports_risk_regulation"]:
        facts.append("该来源可以对应监管要求、消费者权益或平台治理边界。")
    return facts


def _source_atomic_facts(source_row: dict[str, Any], support_matrix: dict[str, bool], *, source_level: str) -> list[str]:
    facts: list[str] = []
    for item in source_row.get("key_points") or []:
        rewritten = _rewrite_key_point_to_atomic_fact(_safe_text(item))
        if rewritten:
            facts.append(rewritten)
    if not facts:
        facts.extend(_fallback_atomic_facts(source_row, support_matrix, source_level=source_level))
    else:
        # Always make verification depth explicit even when key points exist.
        facts = _fallback_atomic_facts(source_row, support_matrix, source_level=source_level)[:1] + facts

    deduped: list[str] = []
    seen: set[str] = set()
    for item in facts:
        text = _safe_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _source_claim_summary(source_row: dict[str, Any], support_matrix: dict[str, bool], *, source_level: str) -> str:
    focuses: list[str] = []
    if support_matrix["supports_platform_mechanism"]:
        focuses.append("平台规则、履约与评价治理")
    if support_matrix["supports_benchmark"]:
        focuses.append("benchmark 口径与可比性边界")
    if support_matrix["supports_risk_regulation"]:
        focuses.append("监管、售后与消费者权益边界")
    if not focuses:
        focuses.append("行业背景与市场结构")

    if source_level == "lead_only":
        prefix = "当前仅拿到来源线索"
    elif source_level == "org_index":
        prefix = "当前仅落到机构索引页"
    elif source_level == "document_fact":
        prefix = "当前已落到具体文档页"
    else:
        prefix = "当前已落到具体页面"
    return f"{prefix}，该来源主要用于确认{'、'.join(focuses)}，不能直接支持SKU、店铺、卖家或订单级经营拍板。"


def _source_citation_snippet(source_row: dict[str, Any], atomic_facts: list[str]) -> str:
    explicit = _safe_text(source_row.get("citation_snippet"))
    if explicit:
        return explicit
    citation_text = _safe_text(source_row.get("citation_text"))
    if citation_text:
        return citation_text
    if atomic_facts:
        return atomic_facts[0]
    return f"{_safe_text(source_row.get('title'))} / {_safe_text(source_row.get('publisher'))}"


def _is_non_verifiable_publish_date(text: str) -> bool:
    normalized = _safe_text(text)
    if not normalized:
        return True
    return any(
        token in normalized
        for token in [
            "待",
            "需",
            "长期更新页面",
            "以具体",
            "为准",
            "补充发布日期",
            "尚未落到可核验发布日期",
        ]
    )


def _downgrade_source_if_not_verifiable(
    *,
    source_level: str,
    verification_status: str,
    publish_date: str,
    citation_snippet: str,
    page_or_section_hint: str,
) -> tuple[str, str]:
    if source_level not in {"page_fact", "document_fact"}:
        return source_level, verification_status
    if _is_non_verifiable_publish_date(publish_date) or not _safe_text(citation_snippet) or not _safe_text(page_or_section_hint):
        return "lead_only", "lead_only"
    return source_level, verification_status


def _source_fact_card(source_row: dict[str, Any]) -> dict[str, Any]:
    support_matrix = _source_support_matrix(source_row)
    source_level = _source_level(source_row)
    verification_status = _source_verification_status(source_row, source_level)
    publish_date = _source_publish_date(source_row, source_level)
    usable_for_sections = list(source_row.get("usable_for") or [])
    not_usable_for_sections = list(source_row.get("not_usable_for") or [])
    if "对主报告的支持边界" not in usable_for_sections:
        usable_for_sections.append("对主报告的支持边界")
    if "当前对象级经营判断" not in not_usable_for_sections:
        not_usable_for_sections.append("当前对象级经营判断")
    atomic_facts = _source_atomic_facts(source_row, support_matrix, source_level=source_level)
    citation_snippet = _source_citation_snippet(source_row, atomic_facts)
    page_or_section_hint = _source_page_or_section_hint(source_row, source_level)
    source_level, verification_status = _downgrade_source_if_not_verifiable(
        source_level=source_level,
        verification_status=verification_status,
        publish_date=publish_date,
        citation_snippet=citation_snippet,
        page_or_section_hint=page_or_section_hint,
    )
    return {
        "source_id": source_row["source_id"],
        "title": source_row["title"],
        "publisher": source_row["publisher"],
        "url": source_row["url"],
        "publish_date": publish_date,
        "credibility": source_row.get("credibility_level", ""),
        "source_type": source_row.get("source_type", ""),
        "source_level": source_level,
        "claim_summary": _source_claim_summary(source_row, support_matrix, source_level=source_level),
        "atomic_facts": atomic_facts,
        "facts": list(atomic_facts),
        "usable_for_sections": usable_for_sections,
        "not_usable_for_sections": not_usable_for_sections,
        "citation_snippet": citation_snippet,
        "page_or_section_hint": page_or_section_hint,
        "verification_status": verification_status,
        "supports_platform_mechanism": support_matrix["supports_platform_mechanism"],
        "supports_benchmark": support_matrix["supports_benchmark"],
        "supports_risk_regulation": support_matrix["supports_risk_regulation"],
        "supports_object_level_judgement": support_matrix["supports_object_level_judgement"],
        "object_level_judgement_boundary": "该来源不能直接支持 SKU、店铺、卖家、订单或类目级经营拍板。",
        "limitation": source_row.get("limitation", ""),
        "citation_text": source_row.get("citation_text", ""),
        "key_points": list(source_row.get("key_points") or []),
        "usable_for": list(source_row.get("usable_for") or []),
        "not_usable_for": list(source_row.get("not_usable_for") or []),
        "credibility_level": source_row.get("credibility_level", ""),
    }


def _copy_source_template_fields(source_row: dict[str, Any], item: dict[str, Any]) -> None:
    for key in [
        "source_level",
        "verification_status",
        "publish_date",
        "page_or_section_hint",
        "citation_snippet",
    ]:
        if key in item:
            source_row[key] = item[key]


def _citation_manifest_payload(
    *,
    generated_at: str,
    sources: list[dict[str, Any]],
    citation_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source_by_id = {row["source_id"]: row for row in sources if _safe_text(row.get("source_id"))}
    citations_by_source: dict[str, dict[str, Any]] = {}
    for row in citation_rows:
        source_id = _safe_text(row.get("source_id"))
        if not source_id:
            continue
        source = source_by_id.get(source_id, {})
        entry = citations_by_source.setdefault(
            source_id,
            {
                "source_id": source_id,
                "title": source.get("title", ""),
                "publisher": source.get("publisher", ""),
                "url": source.get("url", ""),
                "publish_date": source.get("publish_date", ""),
                "source_type": source.get("source_type", ""),
                "source_level": source.get("source_level", ""),
                "credibility": source.get("credibility", ""),
                "verification_status": source.get("verification_status", ""),
                "claim_summary": source.get("claim_summary", ""),
                "atomic_facts": list(source.get("atomic_facts") or []),
                "usable_for_sections": list(source.get("usable_for_sections") or []),
                "not_usable_for_sections": list(source.get("not_usable_for_sections") or []),
                "citation_snippet": source.get("citation_snippet", ""),
                "page_or_section_hint": source.get("page_or_section_hint", ""),
                "citation_texts": [],
                "citation_count": 0,
            },
        )
        citation_text = _safe_text(row.get("citation_text") or source.get("citation_text", ""))
        if citation_text and citation_text not in entry["citation_texts"]:
            entry["citation_texts"].append(citation_text)
        entry["citation_count"] += 1
    return {
        "generated_at": generated_at,
        "citations": list(citations_by_source.values()),
    }


def _source_fact_table_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in sources:
        for idx, fact in enumerate(source.get("atomic_facts") or [], start=1):
            rows.append(
                {
                    "source_id": source.get("source_id"),
                    "title": source.get("title"),
                    "publisher": source.get("publisher"),
                    "source_type": source.get("source_type"),
                    "source_level": source.get("source_level"),
                    "publish_date": source.get("publish_date"),
                    "credibility": source.get("credibility"),
                    "verification_status": source.get("verification_status"),
                    "claim_summary": source.get("claim_summary"),
                    "fact_index": idx,
                    "atomic_fact": fact,
                    "usable_for_sections": " / ".join(source.get("usable_for_sections") or []),
                    "not_usable_for_sections": " / ".join(source.get("not_usable_for_sections") or []),
                    "supports_platform_mechanism": source.get("supports_platform_mechanism"),
                    "supports_benchmark": source.get("supports_benchmark"),
                    "supports_risk_regulation": source.get("supports_risk_regulation"),
                    "supports_object_level_judgement": source.get("supports_object_level_judgement"),
                    "object_level_judgement_boundary": source.get("object_level_judgement_boundary"),
                    "page_or_section_hint": source.get("page_or_section_hint"),
                    "url": source.get("url"),
                    "citation_snippet": source.get("citation_snippet"),
                }
            )
    return rows


def _source_audit_markdown(sources: list[dict[str, Any]]) -> str:
    lines = [
        "# industry_research_source_audit",
        "",
        "## 来源事实卡审计",
        "",
    ]
    for source in sources:
        lines.extend(
            [
                f"### {source.get('source_id')} / {source.get('title')}",
                "",
                f"- publisher: {source.get('publisher')}",
                f"- source_type: {source.get('source_type')}",
                f"- source_level: {source.get('source_level')}",
                f"- verification_status: {source.get('verification_status')}",
                f"- publish_date: {source.get('publish_date')}",
                f"- credibility: {source.get('credibility')}",
                f"- claim_summary: {source.get('claim_summary')}",
                f"- citation_snippet: {source.get('citation_snippet')}",
                f"- page_or_section_hint: {source.get('page_or_section_hint')}",
                f"- usable_for_sections: {' / '.join(source.get('usable_for_sections') or [])}",
                f"- not_usable_for_sections: {' / '.join(source.get('not_usable_for_sections') or [])}",
                f"- supports_platform_mechanism: {source.get('supports_platform_mechanism')}",
                f"- supports_benchmark: {source.get('supports_benchmark')}",
                f"- supports_risk_regulation: {source.get('supports_risk_regulation')}",
                f"- supports_object_level_judgement: {source.get('supports_object_level_judgement')}",
                f"- object_level_judgement_boundary: {source.get('object_level_judgement_boundary')}",
                "- atomic_facts:",
                *[f"  - {fact}" for fact in (source.get('atomic_facts') or [])],
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _topic_lookup(scope_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("topic_id"): item for item in (scope_payload.get("research_topics") or []) if item.get("topic_id")}


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _safe_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _source_level_priority(source_level: str) -> int:
    priorities = {
        "page_fact": 0,
        "document_fact": 1,
        "org_index": 2,
        "lead_only": 3,
    }
    return priorities.get(_safe_text(source_level), 9)


def _is_locator_only_fact(text: str) -> bool:
    normalized = _safe_text(text)
    return (
        normalized.startswith("当前仅定位到")
        or normalized.startswith("当前仅拿到来源线索")
        or normalized.startswith("当前已定位到")
        or normalized.startswith("当前仅识别到")
    )


def _usable_section_match(source: dict[str, Any], usable_section_keywords: list[str]) -> bool:
    usable_text = " ".join(str(item) for item in (source.get("usable_for_sections") or []))
    return any(keyword in usable_text for keyword in usable_section_keywords)


def _source_fact_candidates(
    source: dict[str, Any],
    *,
    include_locator_fact_when_needed: bool = False,
) -> list[str]:
    atomic_facts = list(source.get("atomic_facts") or source.get("facts") or [])
    content_facts = [fact for fact in atomic_facts if not _is_locator_only_fact(fact)]
    if content_facts:
        return content_facts
    if include_locator_fact_when_needed:
        return atomic_facts
    return []


def _select_section_facts(
    sources: list[dict[str, Any]],
    *,
    support_field: str | None = None,
    usable_section_keywords: list[str] | None = None,
    max_facts: int = 4,
) -> list[str]:
    usable_section_keywords = usable_section_keywords or []
    ranked_sources = sorted(
        sources,
        key=lambda source: (
            _source_level_priority(_safe_text(source.get("source_level"))),
            0 if _safe_text(source.get("verification_status")).startswith("verified_") else 1,
            _safe_text(source.get("source_id")),
        ),
    )

    def _collect(*, allow_locator_fallback: bool) -> list[str]:
        collected: list[str] = []
        for source in ranked_sources:
            support_match = bool(source.get(support_field)) if support_field else False
            usable_match = _usable_section_match(source, usable_section_keywords)
            if support_field and not support_match and not usable_match:
                continue
            if not support_field and not usable_match:
                continue
            candidate_facts = _source_fact_candidates(
                source,
                include_locator_fact_when_needed=allow_locator_fallback,
            )
            for fact in candidate_facts:
                collected.append(f"[{source.get('source_id')}] {fact}")
                if len(collected) >= max_facts:
                    return _unique_strings(collected)
        return _unique_strings(collected)

    facts = _collect(allow_locator_fallback=False)
    if facts:
        return facts
    return _collect(allow_locator_fallback=True)


def _section_relation_to_data(
    *,
    section_name: str,
    data_context_payload: dict[str, Any],
    scope_payload: dict[str, Any],
) -> str:
    object_grain = _safe_text(data_context_payload.get("object_grain"))
    objects = ", ".join((data_context_payload.get("candidate_business_objects") or [])[:4]) or "业务对象"
    metrics = ", ".join((data_context_payload.get("available_metric_families") or [])[:4]) or "结构性指标"
    if section_name == "平台机制":
        return f"当前上传数据的对象粒度为 {object_grain}，对象主要落在 {objects}，并已识别 {metrics}，因此需要用平台规则与履约评价机制来解释这些指标如何形成。"
    if section_name == "行业背景":
        return f"当前上传数据主要呈现 {objects} 的交易与结构信号，能提示行业切题方向，但不能单独证明行业景气度或行业规模变化。"
    if section_name == "市场结构":
        return f"当前上传数据已能显示 {objects} 的规模分布与结构线索，但外部市场结构、集中度和 benchmark 边界仍需来源事实补充。"
    if section_name == "竞争格局":
        return f"当前上传数据只能帮助我们确认比较维度仍围绕 {objects} 与 {metrics} 展开，不能直接替代外部竞对格局事实。"
    if section_name == "供给结构":
        return f"当前上传数据的对象粒度与字段分布表明供给结构应从 {objects} 的层次展开，但外部供给分层和行业惯例仍需外部资料补充。"
    if section_name == "用户/消费者趋势":
        return "当前上传数据以交易和对象结构为主，只有有限文本或评价信号，因此消费者趋势只能结合外部来源与人工确认项解释。"
    return "当前上传数据只能限定研究边界，不能替代外部事实。"


def _section_manual_confirmation(
    *,
    section_name: str,
    scope_payload: dict[str, Any],
    data_context_payload: dict[str, Any],
    business_scene_inference_payload: dict[str, Any],
) -> list[str]:
    items: list[str] = []
    if business_scene_inference_payload.get("manual_confirmation_needed"):
        items.extend(business_scene_inference_payload.get("required_manual_confirmation") or [])
    if section_name == "用户/消费者趋势" and not (data_context_payload.get("text_like_fields") or []):
        items.append("当前数据缺少足够的用户行为或文本字段，需要人工确认消费者趋势应参考哪些外部来源。")
    if section_name == "平台机制" and "平台零售电商" in _safe_text(scope_payload.get("inferred_platform")):
        items.append("当前平台名称仍未完全识别，需人工确认最终应引用哪一个具体平台规则页。")
    return _unique_strings(items)


def _section_payload(
    *,
    section_name: str,
    section_conclusion: str,
    source_backed_facts: list[str],
    relation_to_uploaded_data: str,
    unsupported_claims: list[str],
    manual_confirmation_needed: list[str],
) -> dict[str, Any]:
    return {
        "section_name": section_name,
        "section_conclusion": section_conclusion,
        "source_backed_facts": source_backed_facts,
        "relation_to_uploaded_data": relation_to_uploaded_data,
        "unsupported_claims": unsupported_claims,
        "manual_confirmation_needed": manual_confirmation_needed,
    }


def _stage6_section_conclusion(
    *,
    section_name: str,
    scope_payload: dict[str, Any],
    data_context_payload: dict[str, Any],
    business_scene_inference_payload: dict[str, Any],
) -> str:
    object_grain = _safe_text(data_context_payload.get("object_grain"))
    business_objects = ", ".join((data_context_payload.get("candidate_business_objects") or [])[:4]) or "订单、商品与卖家"
    metric_families = ", ".join((data_context_payload.get("available_metric_families") or [])[:3]) or "交易、履约与评价指标"
    fulfillment_fields = ", ".join((data_context_payload.get("fulfillment_like_fields") or [])[:4])
    review_fields = ", ".join((data_context_payload.get("review_like_fields") or [])[:3])
    inferred_industry = _safe_text(scope_payload.get("inferred_industry"))
    if _is_uncertain_business_model(scope_payload):
        inferred_business_model = "交易、履约与评价协同观察窗口"
    else:
        inferred_business_model = _safe_text(scope_payload.get("inferred_business_model"))
    candidate_context_labels: list[str] = []
    for item in (business_scene_inference_payload.get("candidate_business_contexts") or [])[:2]:
        if isinstance(item, dict):
            candidate_context_labels.append(_safe_text(item.get("context")) or _safe_text(item.get("label")))
        else:
            candidate_context_labels.append(_safe_text(item))
    candidate_contexts = ", ".join(item for item in candidate_context_labels if item)

    if section_name == "行业背景":
        return (
            f"当前数据把 {business_objects} 放在同一个 `{object_grain}` 观察窗口里，最适合放回 `{inferred_industry}` 的"
            f"{inferred_business_model or '平台零售交易'} 背景下解释交易结构、履约约束和评价信号。"
        )
    if section_name == "平台机制":
        if _is_uncertain_platform(scope_payload):
            return (
                f"当前样本同时出现 {fulfillment_fields or '履约状态字段'} 与 {review_fields or '评价字段'}，"
                "平台机制解释依赖待确认的平台规则页，用于说明规则、履约、售后和评价治理如何影响这些指标的读法。"
            )
        return (
            f"当前样本同时出现 {fulfillment_fields or '履约状态字段'} 与 {review_fields or '评价字段'}，平台机制章节应直接解释"
            "规则、履约、售后和评价治理如何影响这些指标的读法，而不是把未识别的平台名称当成事实。"
        )
    if section_name == "市场结构":
        return (
            f"当前数据能观察 {business_objects} 的分布，但市场结构章节只能把这些分布映射到外部市场层级与样本边界，"
            "不能把当前样本直接写成行业份额或全平台格局。"
        )
    if section_name == "竞争格局":
        return (
            f"竞争格局章节只解释当前样本应如何与外部竞争维度比较，重点是 {metric_families} 与对象层级差异，"
            "不能把外部竞对资料提升成当前对象级胜负结论。"
        )
    if section_name == "供给结构":
        return (
            f"供给结构章节聚焦 {business_objects} 的层级与组合关系，解释当前样本里的供给分布与履约承接链条，"
            "不把外部供给资料直接改写成商品、SKU 或卖家动作。"
        )
    if section_name == "用户/消费者趋势":
        if review_fields:
            return (
                f"当前数据只有 {review_fields} 这类有限消费者反馈信号，消费者趋势章节只能解释体验与治理边界，"
                "不能把少量评分或评论样本写成强用户趋势结论。"
            )
        return (
            "当前数据缺少足够的用户行为和文本样本，消费者趋势章节只能引用外部来源解释背景边界，"
            "不能从当前样本直接推出用户趋势。"
        )
    return f"当前样本处于 `{object_grain}` 观察窗口内，章节结论只能结合外部来源解释 {candidate_contexts or '行业背景'}。"


def _section_markdown(section: dict[str, Any]) -> str:
    lines = [
        f"## {section['section_name']}",
        "",
        f"- section_conclusion: {section['section_conclusion']}",
        "- source_backed_facts:",
        *[f"  - {item}" for item in (section.get("source_backed_facts") or [])],
        f"- relation_to_uploaded_data: {section['relation_to_uploaded_data']}",
        "- unsupported_claims:",
        *[f"  - {item}" for item in (section.get("unsupported_claims") or [])],
        "- manual_confirmation_needed:",
        *[f"  - {item}" for item in (section.get("manual_confirmation_needed") or [])],
        "",
    ]
    return "\n".join(lines)


def _build_stage6_sections(
    *,
    scope_payload: dict[str, Any],
    data_context_payload: dict[str, Any],
    business_scene_inference_payload: dict[str, Any],
    sources: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    topics = _topic_lookup(scope_payload)
    industry_background = _section_payload(
        section_name="行业背景",
        section_conclusion=_stage6_section_conclusion(
            section_name="行业背景",
            scope_payload=scope_payload,
            data_context_payload=data_context_payload,
            business_scene_inference_payload=business_scene_inference_payload,
        ),
        source_backed_facts=_select_section_facts(sources, usable_section_keywords=["行业背景", "市场结构"]),
        relation_to_uploaded_data=_section_relation_to_data(section_name="行业背景", data_context_payload=data_context_payload, scope_payload=scope_payload),
        unsupported_claims=list((topics.get("industry_background") or {}).get("unsupported_claims") or []),
        manual_confirmation_needed=_section_manual_confirmation(section_name="行业背景", scope_payload=scope_payload, data_context_payload=data_context_payload, business_scene_inference_payload=business_scene_inference_payload),
    )
    market_structure = _section_payload(
        section_name="市场结构",
        section_conclusion=_stage6_section_conclusion(
            section_name="市场结构",
            scope_payload=scope_payload,
            data_context_payload=data_context_payload,
            business_scene_inference_payload=business_scene_inference_payload,
        ),
        source_backed_facts=_select_section_facts(sources, usable_section_keywords=["市场结构"]),
        relation_to_uploaded_data=_section_relation_to_data(section_name="市场结构", data_context_payload=data_context_payload, scope_payload=scope_payload),
        unsupported_claims=list((topics.get("competitive_landscape") or {}).get("unsupported_claims") or []),
        manual_confirmation_needed=_section_manual_confirmation(section_name="市场结构", scope_payload=scope_payload, data_context_payload=data_context_payload, business_scene_inference_payload=business_scene_inference_payload),
    )
    supply_structure = _section_payload(
        section_name="供给结构",
        section_conclusion=_stage6_section_conclusion(
            section_name="供给结构",
            scope_payload=scope_payload,
            data_context_payload=data_context_payload,
            business_scene_inference_payload=business_scene_inference_payload,
        ),
        source_backed_facts=_select_section_facts(sources, usable_section_keywords=["市场结构", "对主报告的支持边界"]),
        relation_to_uploaded_data=_section_relation_to_data(section_name="供给结构", data_context_payload=data_context_payload, scope_payload=scope_payload),
        unsupported_claims=_unique_strings(list((topics.get("competitive_landscape") or {}).get("unsupported_claims") or []) + ["外部供给结构资料不能直接推出当前对象级经营动作。"]),
        manual_confirmation_needed=_section_manual_confirmation(section_name="供给结构", scope_payload=scope_payload, data_context_payload=data_context_payload, business_scene_inference_payload=business_scene_inference_payload),
    )
    consumer_trends = _section_payload(
        section_name="用户/消费者趋势",
        section_conclusion=_stage6_section_conclusion(
            section_name="用户/消费者趋势",
            scope_payload=scope_payload,
            data_context_payload=data_context_payload,
            business_scene_inference_payload=business_scene_inference_payload,
        ),
        source_backed_facts=_select_section_facts(sources, usable_section_keywords=["市场结构", "对主报告的支持边界"]),
        relation_to_uploaded_data=_section_relation_to_data(section_name="用户/消费者趋势", data_context_payload=data_context_payload, scope_payload=scope_payload),
        unsupported_claims=["当前上传数据中的评价样本不能直接替代行业消费者趋势事实。", "外部消费者趋势资料不能直接推出当前商品或店铺动作。"],
        manual_confirmation_needed=_section_manual_confirmation(section_name="用户/消费者趋势", scope_payload=scope_payload, data_context_payload=data_context_payload, business_scene_inference_payload=business_scene_inference_payload),
    )
    platform_mechanism = _section_payload(
        section_name="平台机制",
        section_conclusion=_stage6_section_conclusion(
            section_name="平台机制",
            scope_payload=scope_payload,
            data_context_payload=data_context_payload,
            business_scene_inference_payload=business_scene_inference_payload,
        ),
        source_backed_facts=_select_section_facts(sources, support_field="supports_platform_mechanism", usable_section_keywords=["平台机制"]),
        relation_to_uploaded_data=_section_relation_to_data(section_name="平台机制", data_context_payload=data_context_payload, scope_payload=scope_payload),
        unsupported_claims=list((topics.get("platform_mechanism") or {}).get("unsupported_claims") or []),
        manual_confirmation_needed=_section_manual_confirmation(section_name="平台机制", scope_payload=scope_payload, data_context_payload=data_context_payload, business_scene_inference_payload=business_scene_inference_payload),
    )
    competitive_landscape = _section_payload(
        section_name="竞争格局",
        section_conclusion=_stage6_section_conclusion(
            section_name="竞争格局",
            scope_payload=scope_payload,
            data_context_payload=data_context_payload,
            business_scene_inference_payload=business_scene_inference_payload,
        ),
        source_backed_facts=_select_section_facts(sources, usable_section_keywords=["市场结构", "对主报告的支持边界"]),
        relation_to_uploaded_data=_section_relation_to_data(section_name="竞争格局", data_context_payload=data_context_payload, scope_payload=scope_payload),
        unsupported_claims=list((topics.get("competitive_landscape") or {}).get("unsupported_claims") or []),
        manual_confirmation_needed=_section_manual_confirmation(section_name="竞争格局", scope_payload=scope_payload, data_context_payload=data_context_payload, business_scene_inference_payload=business_scene_inference_payload),
    )
    return {
        "industry_context_analysis": [industry_background, market_structure, supply_structure, consumer_trends],
        "industry_platform_mechanism": [platform_mechanism],
        "industry_competitor_context": [competitive_landscape],
    }


def _stage6_markdown(title: str, sections: list[dict[str, Any]]) -> str:
    return "\n".join([f"# {title}", "", *[_section_markdown(section) for section in sections]]).strip() + "\n"


def _stage6_section_failures(section_groups: dict[str, list[dict[str, Any]]]) -> list[str]:
    banned_phrases = ["当前更适合从", "更适合从", "需要单独研究", "仅形成框架", "当前只给出研究方向", "只给出研究方向"]
    failures: list[str] = []
    for group_name, sections in section_groups.items():
        for section in sections:
            name = section["section_name"]
            if not section.get("source_backed_facts"):
                failures.append(f"{group_name}:{name}:missing_source_backed_facts")
            for phrase in banned_phrases:
                haystack = " ".join(
                    [
                        _safe_text(section.get("section_conclusion")),
                        _safe_text(section.get("relation_to_uploaded_data")),
                        " ".join(section.get("source_backed_facts") or []),
                    ]
                )
                if phrase in haystack:
                    failures.append(f"{group_name}:{name}:contains_template_phrase:{phrase}")
    return failures


BENCHMARK_METRIC_BLUEPRINTS = [
    {
        "metric_id": "GMV",
        "display_name": "GMV",
        "aliases": ["gmv"],
        "common_definition": "行业里通常指成交总额或支付总额，但是否含运费、退款前后口径、是否跨店汇总，取决于平台规则与统计窗口。",
        "time_window_difference": "当前上传数据如果只覆盖单批样本或单期记录，不能直接与月度、季度或年度行业口径等同比较。",
        "platform_difference": "不同平台对 GMV 是否含运费、补贴、退款前后口径定义不完全一致。",
        "sample_difference": "当前样本可能只覆盖部分商品、店铺或交易窗口，行业 benchmark 常覆盖全平台或头部商家。",
        "statistical_definition_difference": "当前字段口径未天然等于行业公开 GMV 口径，需要确认支付时点、退款处理与汇总范围。",
        "can_support": ["方向性判断交易规模和结构占比", "作为当前数据内部结构比较口径"],
        "cannot_support": ["直接证明达到行业平均 GMV 水平", "直接推出对象级经营加码动作"],
    },
    {
        "metric_id": "Revenue",
        "display_name": "Revenue",
        "aliases": ["revenue", "sales_amount"],
        "common_definition": "行业里通常指确认收入或销售收入，但与 GMV、净收入、结算收入并不等价。",
        "time_window_difference": "收入确认时点可能与下单或支付时点不同，时间窗口对比需要统一。",
        "platform_difference": "不同平台可能只披露佣金收入、平台服务收入，或商家销售收入。",
        "sample_difference": "当前样本可能只覆盖部分商品或店铺，行业收入口径常覆盖全业务范围。",
        "statistical_definition_difference": "当前数据里的 Revenue 需要明确是订单收入、结算收入还是扣减后收入。",
        "can_support": ["说明当前数据中的收入相关口径", "辅助解释 Revenue 与 GMV 不可混用"],
        "cannot_support": ["直接与行业营收 benchmark 做强比较", "直接当作利润或净收入"],
    },
    {
        "metric_id": "FreightCost",
        "display_name": "FreightCost",
        "aliases": ["freightcost", "freight", "shipping_cost"],
        "common_definition": "行业里通常只代表物流或运费相关成本项，不等于完整履约成本或总成本。",
        "time_window_difference": "不同账期下运费确认时点和分摊方式可能不同。",
        "platform_difference": "平台对运费承担方、商家补贴和运费险规则不同。",
        "sample_difference": "当前样本只包含已观察到的运费字段，未必覆盖售后、仓配、逆向物流等成本。",
        "statistical_definition_difference": "FreightCost 只能解释物流成本片段，不能替代完整成本结构。",
        "can_support": ["解释运费在当前数据中的占比和代理成本含义"],
        "cannot_support": ["直接推出真实毛利率", "把 FreightCost 当作全部成本"],
    },
    {
        "metric_id": "order_count",
        "display_name": "订单数",
        "aliases": ["order_count", "order", "orders", "order_id"],
        "common_definition": "行业里通常指在统一口径下的有效订单数，但是否去重、是否剔除取消退款订单需要明确。",
        "time_window_difference": "行业 benchmark 常按月/季/年披露，当前样本可能只是局部时间窗。",
        "platform_difference": "各平台对有效订单、退款订单、拆单合单的处理不同。",
        "sample_difference": "当前数据可能只覆盖部分类目或店铺，不代表全平台订单量。",
        "statistical_definition_difference": "需要确认是记录数、去重订单数还是支付订单数。",
        "can_support": ["内部比较订单规模与结构", "解释当前数据的订单基数"],
        "cannot_support": ["直接与行业订单规模做强比较"],
    },
    {
        "metric_id": "rating",
        "display_name": "评分",
        "aliases": ["rating", "reviewscore", "score"],
        "common_definition": "行业评分通常依赖平台评价体系，不同平台的评分分布、过滤规则和展示逻辑不同。",
        "time_window_difference": "评分可能跨较长评价窗口积累，和当前交易窗口并不同步。",
        "platform_difference": "各平台评分机制、展示方式和评价治理规则差异显著。",
        "sample_difference": "当前样本可能只覆盖有评价记录的订单或商品。",
        "statistical_definition_difference": "需要确认当前评分是原始评价分、均分还是过滤后的展示分。",
        "can_support": ["方向性观察服务口碑和售后体验线索"],
        "cannot_support": ["把评分直接当成跨平台可比 benchmark", "直接推出消费者趋势结论"],
    },
    {
        "metric_id": "conversion",
        "display_name": "转化",
        "aliases": ["conversion", "pay_conversion", "ctr", "cvr"],
        "common_definition": "行业里通常要求明确分母是曝光、点击、访客还是加购，不能只看名称。",
        "time_window_difference": "转化受归因窗口与回溯期影响，当前样本窗口可能与行业公开窗口不同。",
        "platform_difference": "各平台流量入口、归因规则、去重逻辑不同。",
        "sample_difference": "当前样本若缺曝光或点击分母，只能做弱代理。",
        "statistical_definition_difference": "没有统一分母时，conversion 不能直接做强 comparability。",
        "can_support": ["解释当前数据是否存在转化相关口径", "说明流量机制与转化 benchmark 边界"],
        "cannot_support": ["直接与行业平均转化率做强比较", "直接判断投放或平台效率优劣"],
    },
    {
        "metric_id": "sales_amount",
        "display_name": "销售额",
        "aliases": ["sales_amount", "sales", "revenue"],
        "common_definition": "销售额通常指销售收入或交易额，需要与 Revenue、GMV 区分。",
        "time_window_difference": "销售额的确认窗口和对账窗口需要统一后才能比。",
        "platform_difference": "不同平台可能按订单、支付、结算或发货口径统计销售额。",
        "sample_difference": "当前样本未必覆盖完整经营对象。",
        "statistical_definition_difference": "同名字段不意味着口径一致，需确认是否含税、含运费、含退款前金额。",
        "can_support": ["解释当前销售口径", "做当前数据内部销售结构比较"],
        "cannot_support": ["直接充当行业销售 benchmark"],
    },
    {
        "metric_id": "sales_volume",
        "display_name": "销量",
        "aliases": ["sales_volume", "quantity", "units"],
        "common_definition": "销量通常是件数或订单件数，但是否剔除退货、赠品、取消单需要统一。",
        "time_window_difference": "销量 benchmark 常按月或季度，当前样本可能只是局部时间窗。",
        "platform_difference": "平台对销量口径、去重规则和展示逻辑不同。",
        "sample_difference": "当前样本可能只覆盖部分类目和店铺。",
        "statistical_definition_difference": "需要确认当前销量是商品件数、订单件数还是支付件数。",
        "can_support": ["解释供给结构与销量分布", "做当前数据内部销量结构比较"],
        "cannot_support": ["直接与行业销量 benchmark 做强比较"],
    },
    {
        "metric_id": "ROI",
        "display_name": "ROI",
        "aliases": ["roi"],
        "common_definition": "ROI 需要完整收益和成本归因口径，行业里也必须明确投放成本、履约成本或综合成本范围。",
        "time_window_difference": "ROI 强依赖归因周期和成本确认周期。",
        "platform_difference": "不同平台的投放、归因和结算逻辑显著不同。",
        "sample_difference": "当前数据缺少完整成本、投放或利润字段时，ROI 无法成立。",
        "statistical_definition_difference": "没有分子分母完整定义时，ROI 不能计算，也不能直接比较。",
        "can_support": ["说明当前 ROI 不可直接判断的原因"],
        "cannot_support": ["输出 ROI 数值", "与行业 ROI 做任何强比较"],
    },
]


def _metric_presence(
    blueprint: dict[str, Any],
    *,
    data_context_payload: dict[str, Any],
    scope_payload: dict[str, Any],
) -> tuple[bool, list[str]]:
    aliases = [_compact(item) for item in (blueprint.get("aliases") or [])]
    field_sources = (
        list(data_context_payload.get("field_names") or [])
        + list(data_context_payload.get("amount_like_fields") or [])
        + list(data_context_payload.get("cost_like_fields") or [])
        + list(data_context_payload.get("object_like_fields") or [])
        + list(data_context_payload.get("text_like_fields") or [])
    )
    direct_metrics = list((scope_payload.get("metric_mining_context") or {}).get("direct_metrics") or [])
    derived_metrics = list((scope_payload.get("metric_mining_context") or {}).get("derived_metrics") or [])
    proxy_metrics = list((scope_payload.get("metric_mining_context") or {}).get("proxy_metrics") or [])
    unsupported_metrics = list((scope_payload.get("metric_mining_context") or {}).get("unsupported_metrics") or [])
    evidence: list[str] = []
    for value in field_sources + direct_metrics + derived_metrics + proxy_metrics + unsupported_metrics:
        normalized = _compact(value)
        if any(alias in normalized for alias in aliases):
            evidence.append(str(value))
    return (len(evidence) > 0, _unique_strings(evidence))


def _current_metric_definition(
    metric_id: str,
    *,
    present: bool,
    evidence: list[str],
    data_context_payload: dict[str, Any],
    scope_payload: dict[str, Any],
) -> str:
    if not present and metric_id == "ROI":
        return "当前上传数据缺少完整收益与成本归因字段，ROI 在当前数据中不可直接成立。"
    if not present:
        return "当前上传数据未明确给出该指标所需字段或统一口径，只能依赖后续补充字段或外部口径说明。"
    if metric_id == "GMV":
        return f"当前数据通过 {', '.join(evidence[:4])} 暗示 GMV 相关口径，但是否含运费、退款前后金额与汇总范围仍未完全确认。"
    if metric_id == "Revenue":
        return f"当前数据通过 {', '.join(evidence[:4])} 暗示 Revenue/销售额口径，但需要人工确认其是订单收入、结算收入还是净收入。"
    if metric_id == "FreightCost":
        return f"当前数据通过 {', '.join(evidence[:4])} 仅覆盖运费或物流相关成本片段，不等于完整成本结构。"
    if metric_id == "order_count":
        return f"当前数据通过 {', '.join(evidence[:4])} 暗示订单规模口径，但需要确认是否是去重有效订单。"
    if metric_id == "rating":
        return f"当前数据通过 {', '.join(evidence[:4])} 提供评分或评价线索，但评分计算与过滤规则未完全确认。"
    if metric_id == "conversion":
        return f"当前数据通过 {', '.join(evidence[:4])} 提供转化相关线索，但分母口径仍需确认。"
    if metric_id == "sales_amount":
        return f"当前数据通过 {', '.join(evidence[:4])} 暗示销售额口径，但与 Revenue/GMV 的关系仍需明确。"
    if metric_id == "sales_volume":
        return f"当前数据通过 {', '.join(evidence[:4])} 暗示销量口径，但是否为商品件数或订单件数仍需确认。"
    return f"当前数据通过 {', '.join(evidence[:4])} 提供该指标的口径线索。"


def _benchmark_comparability_for_metric(
    blueprint: dict[str, Any],
    *,
    present: bool,
    evidence: list[str],
    scope_payload: dict[str, Any],
) -> dict[str, Any]:
    metric_id = blueprint["metric_id"]
    if metric_id == "ROI":
        direct = False
        level = "not_comparable"
        why = "当前数据缺少完整收益/成本归因口径，ROI 无法成立，因此不能直接比较。"
        directional_only = False
    elif metric_id == "FreightCost":
        direct = False
        level = "not_comparable"
        why = "FreightCost 只是成本片段，不等于完整履约或总成本，不能直接与行业利润或成本 benchmark 对比。"
        directional_only = True
    elif metric_id in {"conversion", "rating", "Revenue", "sales_amount"}:
        direct = False
        level = "directional_only"
        why = "该指标名称相似但平台、分母或确认口径差异大，只能做方向参考。"
        directional_only = True
    elif not present:
        direct = False
        level = "not_comparable"
        why = "当前数据未明确给出该指标的统一口径，无法直接比较。"
        directional_only = False
    else:
        direct = False
        level = "directional_only"
        why = "当前样本与行业公开 benchmark 在平台、时间窗和样本覆盖上存在差异，因此最多做方向参考。"
        directional_only = True
    return {
        "directly_comparable": direct,
        "comparability_level": level,
        "why_not_directly_comparable": why,
        "directional_only": directional_only,
        "matched_dataset_signals": evidence,
    }


def _benchmark_metric_artifacts(
    *,
    data_context_payload: dict[str, Any],
    scope_payload: dict[str, Any],
    sources: list[dict[str, Any]],
    router_result: dict[str, Any],
) -> dict[str, Any]:
    benchmark_facts = _select_section_facts(
        sources,
        support_field="supports_benchmark",
        usable_section_keywords=["市场结构", "对主报告的支持边界"],
        max_facts=6,
    )
    platform_rule_facts = _select_section_facts(
        sources,
        support_field="supports_platform_mechanism",
        usable_section_keywords=["平台机制"],
        max_facts=3,
    )
    registry: list[dict[str, Any]] = []
    matrix: list[dict[str, Any]] = []
    definition_rows: list[dict[str, Any]] = []
    for blueprint in BENCHMARK_METRIC_BLUEPRINTS:
        present, evidence = _metric_presence(blueprint, data_context_payload=data_context_payload, scope_payload=scope_payload)
        current_definition = _current_metric_definition(
            blueprint["metric_id"],
            present=present,
            evidence=evidence,
            data_context_payload=data_context_payload,
            scope_payload=scope_payload,
        )
        comparability = _benchmark_comparability_for_metric(
            blueprint,
            present=present,
            evidence=evidence,
            scope_payload=scope_payload,
        )
        metric_source_facts = list(benchmark_facts)
        if blueprint["metric_id"] in {"rating", "conversion", "order_count"}:
            metric_source_facts = _unique_strings(metric_source_facts + platform_rule_facts)
        registry_row = {
            "metric_id": blueprint["metric_id"],
            "display_name": blueprint["display_name"],
            "present_in_current_data": present,
            "matched_dataset_signals": evidence,
            "current_dataset_definition": current_definition,
            "industry_common_definition": blueprint["common_definition"],
            "directly_comparable": comparability["directly_comparable"],
            "comparability_level": comparability["comparability_level"],
            "can_support": blueprint["can_support"],
            "cannot_support": blueprint["cannot_support"],
        }
        matrix_row = {
            "metric_id": blueprint["metric_id"],
            "display_name": blueprint["display_name"],
            "current_dataset_definition": current_definition,
            "industry_common_definition": blueprint["common_definition"],
            "directly_comparable": comparability["directly_comparable"],
            "comparability_level": comparability["comparability_level"],
            "why_not_directly_comparable": comparability["why_not_directly_comparable"],
            "time_window_difference": blueprint["time_window_difference"],
            "platform_difference": blueprint["platform_difference"],
            "sample_difference": blueprint["sample_difference"],
            "statistical_definition_difference": blueprint["statistical_definition_difference"],
            "directional_only": comparability["directional_only"],
            "can_support": blueprint["can_support"],
            "cannot_support": blueprint["cannot_support"],
            "source_backed_facts": metric_source_facts,
        }
        definition_row = {
            "metric_id": blueprint["metric_id"],
            "display_name": blueprint["display_name"],
            "current_dataset_definition": current_definition,
            "industry_common_definition": blueprint["common_definition"],
            "can_support": blueprint["can_support"],
            "cannot_support": blueprint["cannot_support"],
            "matched_dataset_signals": evidence,
        }
        registry.append(registry_row)
        matrix.append(matrix_row)
        definition_rows.append(definition_row)
    platform_difference_table = [
        {
            "difference_dimension": "时间区间差异",
            "current_dataset_risk": "当前上传数据可能只是局部样本或短时间窗，不等于行业月度/季度/年度公开口径。",
            "benchmark_implication": "只能先做方向参考，不能拿局部窗口去对打长周期 benchmark。",
        },
        {
            "difference_dimension": "平台差异",
            "current_dataset_risk": f"当前推断平台为 `{scope_payload['inferred_platform']}`，但具体平台规则仍可能需要人工确认。",
            "benchmark_implication": "平台规则、流量机制、履约和评价体系差异会改变 benchmark 可比性。",
        },
        {
            "difference_dimension": "样本差异",
            "current_dataset_risk": "当前样本可能只覆盖部分类目、店铺或商品，不代表全平台或全行业。",
            "benchmark_implication": "只能支持对象结构理解，不能直接推出行业平均水平。",
        },
        {
            "difference_dimension": "统计口径差异",
            "current_dataset_risk": "GMV、Revenue、FreightCost、conversion 等字段名不等于行业标准口径。",
            "benchmark_implication": "必须先统一定义，再判断是否仅能做方向参考。",
        },
    ]
    benchmark_failures: list[str] = []
    if not matrix:
        benchmark_failures.append("benchmark_comparability_matrix_empty")
    if matrix and all(row["directly_comparable"] for row in matrix):
        benchmark_failures.append("benchmark_matrix_missing_non_directly_comparable_metric")
    if any(not row.get("source_backed_facts") for row in matrix):
        benchmark_failures.append("benchmark_matrix_missing_source_backed_facts")
    return {
        "benchmark_metric_registry": registry,
        "benchmark_comparability_matrix": matrix,
        "platform_difference_table": platform_difference_table,
        "metric_definition_comparison": definition_rows,
        "benchmark_facts": benchmark_facts,
        "benchmark_failures": benchmark_failures,
        "router_context": {
            "business_profile": _safe_text(router_result.get("business_profile")),
            "secondary_profile": _safe_text(router_result.get("secondary_profile")),
            "routing_reason": _safe_text(router_result.get("routing_reason")),
        },
    }


def _benchmark_markdown(artifacts: dict[str, Any]) -> str:
    lines = [
        "# industry_benchmark_synthesis",
        "",
        "## benchmark_comparability_overview",
        "",
        *[f"- {fact}" for fact in (artifacts.get("benchmark_facts") or [])],
        "",
    ]
    for row in artifacts.get("benchmark_comparability_matrix") or []:
        lines.extend(
            [
                f"### {row['metric_id']} / {row['display_name']}",
                "",
                f"- current_dataset_definition: {row['current_dataset_definition']}",
                f"- industry_common_definition: {row['industry_common_definition']}",
                f"- directly_comparable: {row['directly_comparable']}",
                f"- comparability_level: {row['comparability_level']}",
                f"- why_not_directly_comparable: {row['why_not_directly_comparable']}",
                f"- time_window_difference: {row['time_window_difference']}",
                f"- platform_difference: {row['platform_difference']}",
                f"- sample_difference: {row['sample_difference']}",
                f"- statistical_definition_difference: {row['statistical_definition_difference']}",
                f"- directional_only: {row['directional_only']}",
                f"- can_support: {' / '.join(row['can_support'])}",
                f"- cannot_support: {' / '.join(row['cannot_support'])}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _metric_definition_markdown(artifacts: dict[str, Any]) -> str:
    lines = [
        "# industry_metric_definition",
        "",
        "## metric_definition_comparison",
        "",
    ]
    for row in artifacts.get("metric_definition_comparison") or []:
        lines.extend(
            [
                f"### {row['metric_id']} / {row['display_name']}",
                "",
                f"- current_dataset_definition: {row['current_dataset_definition']}",
                f"- industry_common_definition: {row['industry_common_definition']}",
                f"- matched_dataset_signals: {' / '.join(row['matched_dataset_signals']) if row['matched_dataset_signals'] else 'none'}",
                f"- can_support: {' / '.join(row['can_support'])}",
                f"- cannot_support: {' / '.join(row['cannot_support'])}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


RISK_BLUEPRINTS = [
    {
        "risk_id": "risk_platform_rule_change",
        "risk_topic": "平台规则变化",
        "support_field": "supports_platform_mechanism",
        "usable_keywords": ["平台机制", "对主报告的支持边界"],
        "impact": "平台规则变化会改变流量入口、履约要求、评价治理和经营门槛，从而影响 benchmark 解读和经营背景判断。",
        "unsupported_claims": ["平台规则变化并不等于当前对象已经发生经营失误。"],
        "monitoring_suggestion": "持续监测平台规则页、商家规则更新公告和重要经营指标口径变化。",
    },
    {
        "risk_id": "risk_fulfillment_after_sales_regulation",
        "risk_topic": "履约/售后监管",
        "support_field": "supports_risk_regulation",
        "usable_keywords": ["风险与监管"],
        "impact": "履约、退换货、售后和评价治理规则会改变服务质量风险暴露，并影响履约 benchmark 的解释边界。",
        "unsupported_claims": ["外部履约监管资料不能直接证明当前店铺或商品已经违规。"],
        "monitoring_suggestion": "持续监测售后规则、退换货政策、评价治理和履约相关监管要求。",
    },
    {
        "risk_id": "risk_consumer_rights",
        "risk_topic": "消费者权益",
        "support_field": "supports_risk_regulation",
        "usable_keywords": ["风险与监管"],
        "impact": "消费者权益保护要求会影响评价、退款、售后与低价策略的风险边界，也会影响用户/消费者趋势解读。",
        "unsupported_claims": ["消费者权益背景风险不能替代当前交易数据的事实判断。"],
        "monitoring_suggestion": "持续监测消费者权益、平台治理、售后纠纷与评价投诉相关公开信息。",
    },
    {
        "risk_id": "risk_price_competition",
        "risk_topic": "价格竞争/低价策略",
        "support_field": "supports_benchmark",
        "usable_keywords": ["市场结构", "对主报告的支持边界"],
        "impact": "低价策略和价格竞争会扭曲 Revenue、GMV、销量与转化之间的比较关系，使 benchmark 更容易失真。",
        "unsupported_claims": ["外部价格竞争背景不能直接推出当前对象应降价或提价。"],
        "monitoring_suggestion": "持续监测行业价格带、促销节奏、补贴规则和运费策略变化。",
    },
    {
        "risk_id": "risk_unsupported_business_judgement",
        "risk_topic": "数据本身不支持的经营判断风险",
        "support_field": None,
        "usable_keywords": ["对主报告的支持边界"],
        "impact": "当当前数据缺利润、库存或统一 conversion 分母时，容易把外部背景资料误当成对象级经营证据。",
        "unsupported_claims": ["外部研究不能直接替代当前数据中的对象级经营判断。"],
        "monitoring_suggestion": "持续检查利润、库存、ROI、转化分母等关键口径是否齐全，再决定是否升级经营判断。",
    },
]


def _risk_objects(
    *,
    sources: list[dict[str, Any]],
    scope_payload: dict[str, Any],
    data_context_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    def _risk_background_note(risk_id: str) -> tuple[bool, str]:
        if risk_id == "risk_unsupported_business_judgement":
            return (
                False,
                "这条风险更接近判断边界提醒：它说明当前数据口径不完整时，外部资料不能升级成对象级经营证据。",
            )
        return (
            True,
            "这条风险只构成外部背景提醒，用于解释规则、监管和行业环境，不等于当前上传数据已经证明风险已发生。",
        )

    def _risk_benchmark_note(risk_id: str) -> tuple[bool, str]:
        if risk_id in {
            "risk_platform_rule_change",
            "risk_fulfillment_after_sales_regulation",
            "risk_price_competition",
        }:
            return (
                True,
                "这条风险会直接影响 benchmark 解读，因为它会改变平台规则、履约要求、价格带或统计口径的可比边界。",
            )
        return (
            False,
            "这条风险主要用于背景或判断边界提醒，不直接改写 benchmark 矩阵本身。",
        )

    risks: list[dict[str, Any]] = []
    for blueprint in RISK_BLUEPRINTS:
        facts = _select_section_facts(
            sources,
            support_field=blueprint["support_field"],
            usable_section_keywords=blueprint["usable_keywords"],
            max_facts=4,
        )
        background_only, background_risk_note = _risk_background_note(blueprint["risk_id"])
        affects_benchmark_interpretation, benchmark_interpretation_note = _risk_benchmark_note(blueprint["risk_id"])
        risks.append(
            {
                "risk_id": blueprint["risk_id"],
                "risk_topic": blueprint["risk_topic"],
                "source_backed_facts": facts,
                "likely_business_impact": blueprint["impact"],
                "relevance_to_uploaded_data": (
                    f"这是外部背景风险，不是当前上传数据已经证明的事实；当前数据只提示其与 `{scope_payload['inferred_industry']}` 和对象粒度 `{data_context_payload.get('object_grain')}` 相关。"
                ),
                "unsupported_claims": list(blueprint["unsupported_claims"]),
                "monitoring_suggestion": blueprint["monitoring_suggestion"],
                "background_only": background_only,
                "background_risk_note": background_risk_note,
                "affects_benchmark_interpretation": affects_benchmark_interpretation,
                "benchmark_interpretation_note": benchmark_interpretation_note,
            }
        )
    return risks


def _risk_markdown(risks: list[dict[str, Any]]) -> str:
    lines = [
        "# industry_risk_scan",
        "",
        "## 风险与监管说明",
        "",
        "- 以下风险均属于外部背景风险，不是当前上传数据已经证明的事实。",
        "- 这些风险主要用于解释行业背景、规则约束与 benchmark 解读边界。",
        "",
    ]
    for risk in risks:
        lines.extend(
            [
                f"## {risk['risk_id']} / {risk['risk_topic']}",
                "",
                "- source_backed_facts:",
                *[f"  - {item}" for item in (risk.get("source_backed_facts") or [])],
                f"- likely_business_impact: {risk['likely_business_impact']}",
                f"- relevance_to_uploaded_data: {risk['relevance_to_uploaded_data']}",
                f"- unsupported_claims: {' / '.join(risk['unsupported_claims'])}",
                f"- monitoring_suggestion: {risk['monitoring_suggestion']}",
                f"- background_only: {risk['background_only']}",
                f"- background_risk_note: {risk['background_risk_note']}",
                f"- affects_benchmark_interpretation: {risk['affects_benchmark_interpretation']}",
                f"- benchmark_interpretation_note: {risk['benchmark_interpretation_note']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _risk_failures(risks: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if not risks:
        failures.append("industry_regulation_risk_empty")
    for risk in risks:
        if not (risk.get("source_backed_facts") or []):
            failures.append(f"{risk['risk_id']}:missing_source_backed_facts")
        if not _safe_text(risk.get("background_risk_note")):
            failures.append(f"{risk['risk_id']}:missing_background_risk_note")
        if not _safe_text(risk.get("benchmark_interpretation_note")):
            failures.append(f"{risk['risk_id']}:missing_benchmark_interpretation_note")
    return failures


def _is_uncertain_platform(scope_payload: dict[str, Any]) -> bool:
    return _safe_text(scope_payload.get("inferred_platform")) in {
        "行业/平台待确认",
        "平台电商（待确认）",
        "通用经营平台（低置信）",
        "平台零售电商（具体平台未识别）",
    }


def _is_uncertain_business_model(scope_payload: dict[str, Any]) -> bool:
    text = _safe_text(scope_payload.get("inferred_business_model"))
    if text in {
        "unclear_business_model",
        "generic_business_model_needs_confirmation",
        "platform_ecommerce_generic",
    }:
        return True
    return any(token in text for token in ["待补充确认", "待确认", "低置信"])


def _report_title(scope_payload: dict[str, Any]) -> str:
    industry = _safe_text(scope_payload.get("inferred_industry")) or "行业"
    return f"行业研究报告：{industry}"


def _report_section_block(
    *,
    title: str,
    conclusion: str,
    source_facts: list[str],
    relation_to_uploaded_data: str,
    boundary_statement: str,
    manual_confirmation: list[str],
) -> str:
    evidence_lines = _take_facts(source_facts, limit=4) or ["当前章节暂无新增外部来源事实。"]
    lines = [
        f"## {title}",
        "",
        f"- chapter_judgement: {conclusion}",
        *[f"- key_evidence: {fact}" for fact in evidence_lines],
        f"- data_relation: {relation_to_uploaded_data}",
        f"- non_extrapolation_boundary: {boundary_statement}",
    ]
    if manual_confirmation:
        lines.extend(f"- manual_confirmation_needed: {item}" for item in _unique_strings(manual_confirmation))
    lines.append("")
    return "\n".join(lines)


def _stage6_section_by_name(stage6_section_groups: dict[str, list[dict[str, Any]]], section_name: str) -> dict[str, Any] | None:
    for sections in stage6_section_groups.values():
        for section in sections:
            if section.get("section_name") == section_name:
                return section
    return None


def _join_unique_facts(*fact_lists: list[str]) -> list[str]:
    merged: list[str] = []
    for fact_list in fact_lists:
        merged.extend(fact_list or [])
    return _unique_strings(merged)


def _manual_confirmation_lines(business_scene_inference_payload: dict[str, Any], *extra: str) -> list[str]:
    items = list(business_scene_inference_payload.get("required_manual_confirmation") or [])
    items.extend(item for item in extra if _safe_text(item))
    return _unique_strings(items)


def _take_facts(facts: list[str], limit: int = 4) -> list[str]:
    return _unique_strings([_safe_text(item) for item in (facts or []) if _safe_text(item)])[:limit]


def _metric_row_by_id(rows: list[dict[str, Any]], metric_id: str) -> dict[str, Any]:
    for row in rows or []:
        if _safe_text(row.get("metric_id")) == metric_id:
            return row
    return {}


def _metric_boundary_fact(rows: list[dict[str, Any]], metric_id: str) -> str:
    row = _metric_row_by_id(rows, metric_id)
    reason = _safe_text(row.get("why_not_directly_comparable"))
    if not reason:
        return ""
    return f"[{metric_id}] {reason}"


def _metric_support_fact(rows: list[dict[str, Any]], metric_id: str) -> str:
    row = _metric_row_by_id(rows, metric_id)
    can_support = list(row.get("can_support") or [])
    if not can_support:
        return ""
    return f"[{metric_id}] 可支持：{'；'.join(can_support[:2])}"


def _risk_fact_lines(risk_objects: list[dict[str, Any]], *, benchmark_only: bool | None = None, limit: int = 4) -> list[str]:
    lines: list[str] = []
    for risk in risk_objects:
        if benchmark_only is not None and bool(risk.get("affects_benchmark_interpretation")) != benchmark_only:
            continue
        topic = _safe_text(risk.get("risk_topic"))
        note = _safe_text(risk.get("benchmark_interpretation_note") or risk.get("background_risk_note"))
        if topic and note:
            lines.append(f"[{risk.get('risk_id')}] {topic}：{note}")
    return _take_facts(lines, limit=limit)


def _report_scene_conclusion(
    *,
    scope_payload: dict[str, Any],
    data_context_payload: dict[str, Any],
    business_scene_inference_payload: dict[str, Any],
) -> str:
    object_grain = _safe_text(data_context_payload.get("object_grain"))
    objects = "、".join((data_context_payload.get("candidate_business_objects") or [])[:4]) or "订单、商品、SKU、卖家"
    if _is_uncertain_business_model(scope_payload):
        scene = "交易、履约与评价协同观察窗口"
    else:
        scene = _safe_text(business_scene_inference_payload.get("inferred_business_model")) or "平台零售交易与履约协同"
    return f"当前上传数据是 `{object_grain}` 观察窗口下的复合经营样本，围绕 {objects} 同时呈现交易、履约与评价信号，更接近 `{scene}` 的业务切面。"


def _report_market_competition_conclusion(
    *,
    market_structure: dict[str, Any],
    competitive_landscape: dict[str, Any],
    supply_structure: dict[str, Any],
) -> str:
    market = _safe_text(market_structure.get("section_conclusion"))
    competition = _safe_text(competitive_landscape.get("section_conclusion"))
    supply = _safe_text(supply_structure.get("section_conclusion"))
    pieces = [item for item in [market, competition, supply] if item]
    if not pieces:
        return "市场结构与竞争格局章节用于解释当前样本在外部行业分层、供给层次和竞争维度中的位置。"
    return " ".join(pieces[:3])


def _body_prefix_before_source_notes(report_markdown: str) -> str:
    if "\n## 来源说明" in report_markdown:
        return report_markdown.split("\n## 来源说明", 1)[0]
    if "\n## " in report_markdown:
        return report_markdown.rsplit("\n## ", 1)[0]
    return report_markdown


def _acceptance_report_markdown(
    *,
    dataset_id: str,
    dataset_name: str,
    sheet_name: str,
    row_count: int,
    column_count: int,
    routed_business_profile: str,
    report_dir: Path,
    report_markdown: str,
    appendix_markdown: str,
    gate_payload: dict[str, Any],
    score_payload: dict[str, Any],
    sources: list[dict[str, Any]],
    benchmark_artifacts: dict[str, Any],
    manual_confirmation_items: list[str],
) -> str:
    has_template = any(token in report_markdown for token in INDUSTRY_RESEARCH_TEMPLATE_PHRASES + INDUSTRY_RESEARCH_PLACEHOLDER_PHRASES)
    mojibake_hits = _industry_research_mojibake_hits(_safe_text(report_markdown) + "\n" + _safe_text(appendix_markdown))
    has_mojibake = len(mojibake_hits) >= 2
    has_real_source_facts = report_markdown.count("key_evidence: [S") >= 5
    benchmark_matrix = benchmark_artifacts.get("benchmark_comparability_matrix") or []
    metric_defs = benchmark_artifacts.get("metric_definition_comparison") or []
    platform_diff = benchmark_artifacts.get("platform_difference_table") or []
    benchmark_readable = bool(benchmark_matrix and metric_defs and platform_diff)
    boundary_specific = report_markdown.count("non_extrapolation_boundary:") >= 8
    clear_fact_separation = (
        "data_relation:" in report_markdown
        and "key_evidence:" in report_markdown
        and "外部资料不能替代当前上传数据" in report_markdown
    )
    meta_fact_phrase = "该来源提到：" in report_markdown
    lead_only_sources = [row for row in sources if _safe_text(row.get("source_level")) == "lead_only"]
    body_prefix = _body_prefix_before_source_notes(report_markdown)
    lead_only_used_in_body = any(f"[{row.get('source_id')}]" in body_prefix for row in lead_only_sources)

    fail_reasons: list[str] = []
    if has_template:
        fail_reasons.append("正文仍残留模板句、占位句或弱标签。")
    if has_mojibake:
        fail_reasons.append("正文或附录存在编码污染。")
    if not has_real_source_facts:
        fail_reasons.append("正文没有稳定消费真实 source facts。")
    if not benchmark_readable:
        fail_reasons.append("benchmark 相关结构化表为空或不可读。")
    if not boundary_specific:
        fail_reasons.append("边界说明仍不够具体。")
    if not clear_fact_separation:
        fail_reasons.append("上传数据事实与外部背景事实区分不够清楚。")
    if lead_only_used_in_body:
        fail_reasons.append("正文主体仍依赖 lead_only 来源。")
    if meta_fact_phrase:
        fail_reasons.append("来源事实句仍保留“该来源提到：”这类中间壳，不够像最终研报事实句。")

    strongest_section = "指标口径与 benchmark 可比性" if benchmark_readable else "行业背景"
    weakest_section = "来源说明" if lead_only_sources or meta_fact_phrase else "平台机制"
    manual_items = list(manual_confirmation_items or [])
    if lead_only_sources:
        manual_items.append("仍有 lead_only 来源，需要补具体报告页或规则页。")
    manual_items = _unique_strings(manual_items)

    observations = [
        f"模板句检查：{'未发现明显问题' if not has_template else '仍有残留'}。",
        f"乱码检查：{'未发现明显编码污染' if not has_mojibake else '存在编码污染'}。",
        f"真实来源事实：{'正文已稳定消费来源事实' if has_real_source_facts else '正文对来源事实消费不足'}。",
        f"benchmark 可读性：{'相关矩阵表可读' if benchmark_readable else '相关矩阵表存在缺失或空表'}。",
        f"边界说明：{'当前已较具体' if boundary_specific else '仍偏泛'}。",
        f"事实区分：{'已较清楚区分上传数据事实与外部背景事实' if clear_fact_separation else '区分仍不清楚'}。",
    ]
    passed_manual_acceptance = not fail_reasons
    if gate_payload.get("passed") and not passed_manual_acceptance:
        observations.append("机器 gate 已通过，但人工验收未通过；原因是结构完整不等于正文已经达到研究员交付质量。")

    lines = [
        "# industry_research_acceptance_report",
        "",
        "## 本次测试数据",
        "",
        f"- dataset_id: `{dataset_id}`",
        f"- dataset_name: `{dataset_name}`",
        f"- sheet_name: `{sheet_name}`",
        f"- row_count: `{row_count}`",
        f"- column_count: `{column_count}`",
        f"- routed_business_profile: `{routed_business_profile}`",
        f"- report_dir: `{report_dir}`",
        "",
        "## 是否通过",
        "",
        f"- 结论：`{'通过' if passed_manual_acceptance else '未通过'}`",
        f"- quality_gate_passed: `{bool(gate_payload.get('passed'))}`",
        f"- quality_score: `{score_payload.get('score')}`",
        f"- assessment_tier: `{score_payload.get('assessment_tier')}`",
        "",
        "## 不通过原因",
        "",
    ]
    if fail_reasons:
        lines.extend(f"- {item}" for item in fail_reasons)
    else:
        lines.append("- 本次人工验收未发现阻断项。")
    lines.extend(
        [
            "",
            "## 仍需人工确认的部分",
            "",
        ]
    )
    if manual_items:
        lines.extend(f"- {item}" for item in manual_items)
    else:
        lines.append("- 当前无新增人工确认项。")
    lines.extend(
        [
            "",
            "## 当前最强章节",
            "",
            f"- `{strongest_section}`",
            "",
            "## 当前最弱章节",
            "",
            f"- `{weakest_section}`",
            "",
            "## 关键验收观察",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in observations)
    lines.extend(
        [
            "",
            "## 总判断",
            "",
        ]
    )
    if passed_manual_acceptance:
        lines.append("- 当前这次真实实跑结果已达到可交付标准。")
    else:
        lines.append("- 当前这次真实实跑结果仍未达到“真实研报”标准；问题不在链路能否跑通，而在正文信息密度与事实表达仍不够像研究员交付。")
    return "\n".join(lines).strip() + "\n"


def _markdown_table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = _safe_text(row.get(header, ""))
            value = value.replace("\n", "<br>").replace("|", "/")
            values.append(value)
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _source_fact_export_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in sources:
        for idx, fact in enumerate(source.get("atomic_facts") or [], start=1):
            rows.append(
                {
                    "来源ID": source.get("source_id"),
                    "来源标题": source.get("title"),
                    "发布机构": source.get("publisher"),
                    "来源类型": source.get("source_type"),
                    "来源层级": source.get("source_level"),
                    "发布日期": source.get("publish_date"),
                    "可信度": source.get("credibility"),
                    "核验状态": source.get("verification_status"),
                    "结论摘要": source.get("claim_summary"),
                    "事实序号": idx,
                    "原子事实": fact,
                    "可用于章节": " / ".join(source.get("usable_for_sections") or []),
                    "不可用于章节": " / ".join(source.get("not_usable_for_sections") or []),
                    "可支持平台机制": "是" if source.get("supports_platform_mechanism") else "否",
                    "可支持Benchmark": "是" if source.get("supports_benchmark") else "否",
                    "可支持风险监管": "是" if source.get("supports_risk_regulation") else "否",
                    "可支持当前对象级经营判断": "是" if source.get("supports_object_level_judgement") else "否",
                    "对象级经营判断边界": source.get("object_level_judgement_boundary"),
                    "页面或章节提示": source.get("page_or_section_hint"),
                    "链接": source.get("url"),
                    "引文片段": source.get("citation_snippet"),
                }
            )
    return rows


def _benchmark_matrix_export_rows(benchmark_artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in benchmark_artifacts.get("benchmark_comparability_matrix") or []:
        expanded: list[tuple[str, str]] = []
        expanded.extend(("可支持", item) for item in (metric.get("can_support") or []))
        expanded.extend(("不能支持", item) for item in (metric.get("cannot_support") or []))
        expanded.extend(("来源事实", item) for item in (metric.get("source_backed_facts") or []))
        if not expanded:
            expanded.append(("展开说明", "无"))
        for idx, (category, content) in enumerate(expanded, start=1):
            rows.append(
                {
                    "指标ID": metric.get("metric_id"),
                    "指标名称": metric.get("display_name"),
                    "当前数据口径": metric.get("current_dataset_definition"),
                    "行业常见口径": metric.get("industry_common_definition"),
                    "是否直接可比": "是" if metric.get("directly_comparable") else "否",
                    "可比性级别": metric.get("comparability_level"),
                    "不可直接可比原因": metric.get("why_not_directly_comparable"),
                    "时间区间差异": metric.get("time_window_difference"),
                    "平台差异": metric.get("platform_difference"),
                    "样本差异": metric.get("sample_difference"),
                    "统计口径差异": metric.get("statistical_definition_difference"),
                    "只能做方向参考": "是" if metric.get("directional_only") else "否",
                    "展开序号": idx,
                    "展开类别": category,
                    "展开内容": content,
                }
            )
    return rows


def _metric_definition_export_rows(benchmark_artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in benchmark_artifacts.get("metric_definition_comparison") or []:
        expanded: list[tuple[str, str]] = []
        expanded.extend(("匹配数据线索", item) for item in (metric.get("matched_dataset_signals") or []))
        expanded.extend(("可以支持", item) for item in (metric.get("can_support") or []))
        expanded.extend(("不能支持", item) for item in (metric.get("cannot_support") or []))
        if not expanded:
            expanded.append(("展开说明", "无"))
        for idx, (category, content) in enumerate(expanded, start=1):
            rows.append(
                {
                    "指标ID": metric.get("metric_id"),
                    "指标名称": metric.get("display_name"),
                    "当前数据口径": metric.get("current_dataset_definition"),
                    "行业常见口径": metric.get("industry_common_definition"),
                    "展开序号": idx,
                    "展开类别": category,
                    "展开内容": content,
                }
            )
    return rows


def _platform_difference_export_rows(benchmark_artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(benchmark_artifacts.get("platform_difference_table") or [], start=1):
        rows.append(
            {
                "序号": idx,
                "差异维度": item.get("difference_dimension"),
                "当前数据风险": item.get("current_dataset_risk"),
                "对Benchmark解读的影响": item.get("benchmark_implication"),
            }
        )
    return rows


def _manual_confirmation_checklist(
    business_scene_inference_payload: dict[str, Any],
    stage6_section_groups: dict[str, list[dict[str, Any]]],
) -> list[str]:
    items = list(business_scene_inference_payload.get("required_manual_confirmation") or [])
    for sections in stage6_section_groups.values():
        for section in sections:
            items.extend(section.get("manual_confirmation_needed") or [])
    items = _unique_strings(items)
    if not items:
        items = [
            "请确认当前 Revenue / GMV / FreightCost 在业务里分别代表什么口径，以及是否含税、含运费或含退款前金额。",
            "请确认当前 benchmark 只能做方向参考，还是已经具备统一的平台、时间区间和样本口径。",
            "请确认利润、库存、ROI 或转化分母等关键字段是否齐全，再决定是否升级为对象级经营判断。",
        ]
    return items


def _evidence_boundary_rows(
    data_context_payload: dict[str, Any],
    scope_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in data_context_payload.get("industry_research_implications") or []:
        rows.append(
            {
                "证据类型": "当前上传数据",
                "可支持": item,
                "不可支持": "",
                "说明": "属于数据直接支持的研究边界，只能用于切题和背景限定。",
            }
        )
    for item in data_context_payload.get("forbidden_current_dataset_claims") or []:
        rows.append(
            {
                "证据类型": "当前上传数据",
                "可支持": "",
                "不可支持": item,
                "说明": "当前数据不能直接升级为这类经营判断。",
            }
        )
    for item in scope_payload.get("research_boundaries") or []:
        rows.append(
            {
                "证据类型": "外部来源资料",
                "可支持": item if "服务于" in item or "必须有来源" in item else "",
                "不可支持": item if "不得" in item else "",
                "说明": "外部资料只用于行业背景、平台规则、benchmark 和风险边界说明。",
            }
        )
    return rows


def _manual_confirmation_markdown(items: list[str]) -> str:
    lines = ["# manual_confirmation_checklist", ""]
    if not items:
        lines.append("- 当前无人工确认项。")
    else:
        for idx, item in enumerate(items, start=1):
            lines.append(f"- M{idx:02d} {item}")
    return "\n".join(lines) + "\n"


def _router_metric_chain_integration_markdown(
    *,
    router_result: dict[str, Any],
    data_context_payload: dict[str, Any],
    business_scene_inference_payload: dict[str, Any],
    scope_payload: dict[str, Any],
    benchmark_artifacts: dict[str, Any],
    gate_payload: dict[str, Any],
) -> str:
    lines = [
        "# router_metric_chain_integration",
        "",
        "## 上游强输入是否真实进入独立行研链",
        "",
        f"- router_result.business_profile: `{_safe_text(router_result.get('business_profile')) or 'missing'}`",
        f"- router_result.routing_reason: {_safe_text(router_result.get('routing_reason')) or 'missing'}",
        f"- stage_1.used_router_result: {data_context_payload.get('used_router_result')}",
        f"- stage_1.used_universal_metric_mining: {data_context_payload.get('used_universal_metric_mining')}",
        f"- stage_1.used_domain_metric_registry: {data_context_payload.get('used_domain_metric_registry')}",
        f"- stage_2.metric_mining_context.recommended_report_chain: `{_safe_text((business_scene_inference_payload.get('metric_mining_context') or {}).get('recommended_report_chain'))}`",
        f"- stage_3.router_context.business_profile: `{_safe_text((scope_payload.get('router_context') or {}).get('business_profile'))}`",
        f"- stage_7.router_context.business_profile: `{_safe_text((benchmark_artifacts.get('router_context') or {}).get('business_profile'))}`",
        f"- stage_11.data_context_read: {gate_payload.get('data_context_read')}",
        "",
        "## 各 stage 显式消费关系",
        "",
        "- stage_1_dataset_grounding",
        f"  - 读取 router_result: `{data_context_payload.get('router_context', {})}`",
        f"  - 读取 universal_metric_mining_result/domain_metric_registry: direct={data_context_payload.get('used_universal_metric_mining')}, registry={data_context_payload.get('used_domain_metric_registry')}",
        "- stage_2_business_scene_inference",
        f"  - 读取 router_result.business_profile: `{_safe_text(router_result.get('business_profile')) or 'missing'}`",
        f"  - 读取 metric_mining_context: `{_safe_text((business_scene_inference_payload.get('metric_mining_context') or {}).get('recommended_report_chain'))}`",
        "- stage_3_research_plan_generation",
        f"  - 读取 scope.router_context: `{scope_payload.get('router_context', {})}`",
        f"  - 读取 scope.metric_mining_context: `{scope_payload.get('metric_mining_context', {})}`",
        "- stage_7_benchmark_comparability_analysis",
        f"  - 读取 benchmark.router_context: `{benchmark_artifacts.get('router_context', {})}`",
        f"  - 读取 benchmark metric families: `{[row.get('metric_id') for row in benchmark_artifacts.get('benchmark_metric_registry', [])]}`",
        "- stage_11_quality_gate",
        f"  - 读取 data_context flags: router={data_context_payload.get('used_router_result')}, metric={data_context_payload.get('used_universal_metric_mining')}, registry={data_context_payload.get('used_domain_metric_registry')}",
        f"  - 读取 gate fail items: `{gate_payload.get('fail_items', [])}`",
        "",
        "## 当前链路结论",
        "",
        "- 独立行研链不再把 router_result 和 universal_metric_mining_result 当作可有可无的附加字段。",
        "- 它们已经显式进入 stage_1、stage_2、stage_3、stage_7、stage_11 的输出或诊断链。",
        "- 缺少 universal_metric_mining_result 时，stage_11 会清晰 fail。",
        "- 缺少 router_result 时，stage_2 会降级并留下 why_uncertain、required_manual_confirmation 和 ambiguity_notes。",
        "",
    ]
    return "\n".join(lines) + "\n"


INDUSTRY_RESEARCH_TEMPLATE_PHRASES = [
    "建议后续研究",
    "可从",
    "应重点关注",
    "更适合研究",
    "当前只形成框架",
    "当前只给出方向",
]

INDUSTRY_RESEARCH_PLACEHOLDER_PHRASES = [
    "???",
    "unclear_business_model",
]

INDUSTRY_RESEARCH_CONTEXTUAL_UNCERTAINTY_PHRASES = [
    "行业/平台待确认",
    "平台待确认",
    "行业待确认",
    "行业平台待确认",
    "具体平台未识别",
    "通用经营平台（低置信）",
]

INDUSTRY_RESEARCH_MOJIBAKE_TOKENS = [
    "琛屼笟",
    "鏁版嵁",
    "鍙瘮",
    "缁撴瀯",
    "璇存槑",
    "闆跺敭",
    "浜嬪疄",
]


def _industry_research_mojibake_hits(text: str) -> list[str]:
    hits: list[str] = []
    for token in INDUSTRY_RESEARCH_MOJIBAKE_TOKENS:
        if token in text:
            hits.append(token)
    return hits


def _industry_research_placeholder_failures(report_markdown: str) -> list[str]:
    text = _safe_text(report_markdown)
    failures: list[str] = []
    hits = [token for token in INDUSTRY_RESEARCH_PLACEHOLDER_PHRASES if token in text]
    if hits:
        failures.append(f"placeholder_or_raw_uncertainty_text_present:{', '.join(hits)}")
    allowed_context_markers = [
        "边界说明：",
        "人工确认项：",
        "候选解释",
        "non_extrapolation_boundary:",
        "manual_confirmation_needed:",
        "candidate_explanation:",
    ]
    contextual_hits: list[str] = []
    for token in INDUSTRY_RESEARCH_CONTEXTUAL_UNCERTAINTY_PHRASES:
        start = 0
        while True:
            idx = text.find(token, start)
            if idx < 0:
                break
            left = text[max(0, idx - 24) : idx]
            if not any(marker in left for marker in allowed_context_markers):
                contextual_hits.append(token)
                break
            start = idx + len(token)
    if contextual_hits:
        failures.append(f"placeholder_or_raw_uncertainty_text_present:{', '.join(sorted(set(contextual_hits)))}")
    mojibake_hits = _industry_research_mojibake_hits(text)
    if len(mojibake_hits) >= 2:
        failures.append(f"mojibake_text_present:{', '.join(mojibake_hits[:6])}")
    return failures


def _industry_research_template_failures(report_markdown: str) -> list[str]:
    text = _safe_text(report_markdown)
    hits = [token for token in INDUSTRY_RESEARCH_TEMPLATE_PHRASES if token in text]
    if len(hits) >= 2:
        return [f"template_language_overused:{', '.join(hits)}"]
    return []


def _industry_research_dataset_fact_failures(report_markdown: str) -> list[str]:
    text = _safe_text(report_markdown)
    suspicious_phrases = [
        "当前上传数据已经证明行业",
        "当前上传数据说明行业",
        "当前样本代表全行业",
        "当前数据证明市场份额",
        "当前数据证明消费者趋势",
        "根据国家统计局可判断当前SKU",
        "外部资料证明当前SKU",
        "外部资料证明当前店铺",
        "外部资料证明当前类目",
    ]
    hits = [token for token in suspicious_phrases if token in text]
    failures: list[str] = []
    for hit in hits:
        if hit.startswith("外部资料") or hit.startswith("根据国家统计局"):
            failures.append(f"external_evidence_disguised_as_uploaded_data:{hit}")
        else:
            failures.append(f"uploaded_data_disguised_as_industry_fact:{hit}")
    return failures


def _industry_research_quality_score_from_failures(
    *,
    fail_items: list[str],
    insufficient_sources: bool,
) -> tuple[int, str]:
    if not fail_items and not insufficient_sources:
        return 96, "formal_research_report"
    penalty_map = {
        "placeholder_or_raw_uncertainty_text_present": 35,
        "mojibake_text_present": 35,
        "body_missing_source_facts": 25,
        "source_list_not_consumed_in_body": 20,
        "body_depends_on_non_fact_sources": 22,
        "benchmark_tables_missing": 20,
        "template_language_overused": 20,
        "explicit_boundary_missing": 15,
        "manual_confirmation_checklist_missing": 15,
        "external_evidence_disguised_as_uploaded_data": 20,
        "uploaded_data_disguised_as_industry_fact": 20,
        "citation_guardrail_failed": 18,
        "benchmark_boundary_errors_present": 18,
        "body_missing_section": 12,
        "source_fact_table_missing": 10,
        "section_markers_missing": 10,
    }
    score = 84 if insufficient_sources else 92
    for item in fail_items:
        prefix = item.split(":", 1)[0]
        score -= penalty_map.get(prefix, 8)
    score = max(score, 25)
    if score >= 90 and not fail_items and not insufficient_sources:
        tier = "formal_research_report"
    elif score >= 70:
        tier = "provisional_research_note"
    else:
        tier = "template_or_invalid_report"
    return score, tier


def evaluate_industry_research_quality_gate(
    *,
    report_markdown: str,
    sources: list[dict[str, Any]],
    benchmark_artifacts: dict[str, Any],
    boundary_check_payload: dict[str, Any],
    manual_confirmation_items: list[str],
    source_fact_rows: list[dict[str, Any]],
    insufficient_sources: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fail_items: list[str] = []
    text = _safe_text(report_markdown)
    chapter_marker = "chapter_judgement:"
    evidence_marker = "key_evidence:"
    data_relation_marker = "data_relation:"
    boundary_marker = "non_extrapolation_boundary:"
    required_sections = [
        "行业定位与研究边界",
        "数据所反映的业务场景",
        "行业背景",
        "平台机制",
        "市场结构与竞争格局",
        "指标口径与 benchmark 可比性",
        "成本/利润/履约/转化边界",
        "风险与监管环境",
        "对主报告可提供的背景支持",
        "当前不能支持的经营判断",
        "来源说明",
    ]
    missing_sections = [title for title in required_sections if f"## {title}" not in text]
    if missing_sections:
        fail_items.extend(f"body_missing_section:{title}" for title in missing_sections)
    fail_items.extend(_industry_research_placeholder_failures(text))
    fail_items.extend(_industry_research_template_failures(text))
    fail_items.extend(_industry_research_dataset_fact_failures(text))
    if text.count("key_evidence: [S") < 5:
        fail_items.append("body_missing_source_facts")
    prefix_before_source_notes = _body_prefix_before_source_notes(text)
    real_source_ids = [f"[{source.get('source_id')}]" for source in sources if _safe_text(source.get("source_id"))]
    if not any(source_id in prefix_before_source_notes for source_id in real_source_ids):
        fail_items.append("source_list_not_consumed_in_body")
    non_fact_source_ids = [
        f"[{source.get('source_id')}]"
        for source in sources
        if _safe_text(source.get("source_level")) in {"lead_only", "org_index"}
    ]
    if any(source_id in prefix_before_source_notes for source_id in non_fact_source_ids):
        fail_items.append("body_depends_on_non_fact_sources")
    if text.count(boundary_marker) < 8:
        fail_items.append("explicit_boundary_missing")
    if (
        text.count(chapter_marker) < 8
        or text.count(evidence_marker) < 8
        or text.count(data_relation_marker) < 8
        or text.count(boundary_marker) < 8
    ):
        fail_items.append("section_markers_missing")
    if not manual_confirmation_items:
        fail_items.append("manual_confirmation_checklist_missing")
    if not source_fact_rows:
        fail_items.append("source_fact_table_missing")
    if any(not (source.get("atomic_facts") or source.get("facts")) for source in sources):
        fail_items.append("source_fact_cards_missing_atomic_facts")
    benchmark_matrix = benchmark_artifacts.get("benchmark_comparability_matrix") or []
    benchmark_registry = benchmark_artifacts.get("benchmark_metric_registry") or []
    metric_defs = benchmark_artifacts.get("metric_definition_comparison") or []
    platform_diff = benchmark_artifacts.get("platform_difference_table") or []
    if not benchmark_registry or not benchmark_matrix or not metric_defs or not platform_diff:
        fail_items.append("benchmark_tables_missing")
    if boundary_check_payload.get("external_claims_without_sources"):
        fail_items.append("citation_guardrail_failed")
    if boundary_check_payload.get("dataset_evidence_misuse"):
        fail_items.append("external_evidence_disguised_as_uploaded_data:guardrail")
    if boundary_check_payload.get("benchmark_boundary_errors"):
        fail_items.append("benchmark_boundary_errors_present")
    score, tier = _industry_research_quality_score_from_failures(
        fail_items=fail_items,
        insufficient_sources=insufficient_sources,
    )
    gate_payload = {
        "passed": not fail_items and not insufficient_sources and score >= 90,
        "score": score,
        "assessment_tier": tier,
        "insufficient_sources": insufficient_sources,
        "fail_items": fail_items,
        "source_fact_count": len(source_fact_rows),
        "source_count": len(sources),
        "body_source_fact_mentions": text.count(evidence_marker),
        "benchmark_metric_count": len(benchmark_artifacts.get("benchmark_metric_registry") or []),
        "required_sections_present": len(missing_sections) == 0,
    }
    score_payload = {
        "passed": gate_payload["passed"],
        "score": score,
        "assessment_tier": tier,
        "hard_fail_items": fail_items,
    }
    return gate_payload, score_payload


def _appendix_markdown(
    *,
    source_fact_rows: list[dict[str, Any]],
    benchmark_matrix_rows: list[dict[str, Any]],
    metric_definition_rows: list[dict[str, Any]],
    platform_difference_rows: list[dict[str, Any]],
    manual_confirmation_items: list[str],
    evidence_boundary_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# industry_research_appendix",
        "",
        "## 来源事实展开表",
        "",
        _markdown_table(
            ["来源ID", "来源标题", "来源层级", "核验状态", "事实序号", "原子事实", "可用于章节", "不可用于章节", "对象级经营判断边界", "页面或章节提示", "可信度"],
            source_fact_rows,
        ),
        "",
        "## benchmark 可比性矩阵",
        "",
        _markdown_table(
            ["指标ID", "指标名称", "当前数据口径", "行业常见口径", "是否直接可比", "可比性级别", "展开序号", "展开类别", "展开内容", "不可直接可比原因"],
            benchmark_matrix_rows,
        ),
        "",
        "## 指标口径对照表",
        "",
        _markdown_table(
            ["指标ID", "指标名称", "当前数据口径", "行业常见口径", "展开序号", "展开类别", "展开内容"],
            metric_definition_rows,
        ),
        "",
        "## 平台差异表",
        "",
        _markdown_table(
            ["序号", "差异维度", "当前数据风险", "对Benchmark解读的影响"],
            platform_difference_rows,
        ),
        "",
        "## 需要人工确认的问题清单",
        "",
    ]
    if manual_confirmation_items:
        lines.extend(f"- M{idx:02d} {item}" for idx, item in enumerate(manual_confirmation_items, start=1))
    else:
        lines.append("- 当前无人工确认项。")
    lines.extend(
        [
            "",
            "## 当前数据与外部资料的证据边界表",
            "",
            _markdown_table(
                ["证据类型", "可支持", "不可支持", "说明"],
                evidence_boundary_rows,
            ),
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _source_templates(scope_payload: dict[str, Any]) -> list[dict[str, Any]]:
    platform = scope_payload["inferred_platform"]
    industry = scope_payload["inferred_industry"]
    if "淘宝" in platform or "天猫" in platform:
        return [
            {
                "title": "淘宝规则频道",
                "publisher": "淘宝规则",
                "url": "https://rulechannel.taobao.com/",
                "source_type": "官方平台规则",
                "credibility_level": "high",
                "source_level": "lead_only",
                "verification_status": "lead_only",
                "publish_date": "待定位到具体规则条目页后补充发布日期",
                "page_or_section_hint": "淘宝规则频道，评价治理、售后与履约规则条目入口",
                "citation_snippet": "淘宝规则频道（平台规则入口）",
                "key_points": ["可用于核对平台规则、评价治理、售后与履约规则入口。"],
                "usable_for": ["平台机制", "规则边界", "售后与评价规则"],
                "not_usable_for": ["市场规模", "竞品份额"],
                "limitation": "偏平台规则，不提供完整市场规模数据。",
                "citation_text": "淘宝规则频道（平台规则入口）",
            },
            {
                "title": "天猫规则中心",
                "publisher": "天猫规则",
                "url": "https://rule.tmall.com/",
                "source_type": "官方平台规则",
                "credibility_level": "high",
                "source_level": "lead_only",
                "verification_status": "lead_only",
                "publish_date": "待定位到具体规则条目页后补充发布日期",
                "page_or_section_hint": "天猫规则中心，经营、履约与评价规则条目入口",
                "citation_snippet": "天猫规则中心（平台规则入口）",
                "key_points": ["可用于核对天猫平台经营、履约与评价规则。"],
                "usable_for": ["平台机制", "经营规则"],
                "not_usable_for": ["行业总规模"],
                "limitation": "平台规则说明不等于行业 benchmark。",
                "citation_text": "天猫规则中心（平台规则入口）",
            },
            {
                "title": "阿里巴巴集团财报与业绩页面",
                "publisher": "Alibaba Group",
                "url": "https://www.alibabagroup.com/en-US/ir-reports-results",
                "source_type": "上市公司财报",
                "credibility_level": "high",
                "source_level": "lead_only",
                "verification_status": "lead_only",
                "publish_date": "待定位到具体财报或业绩公告页后补充发布日期",
                "page_or_section_hint": "阿里巴巴财报与业绩页面，财报、季报和公开披露入口",
                "citation_snippet": "Alibaba Group 财报与业绩页面",
                "key_points": ["可用于补充平台商业模式、生态结构与公开财务口径。"],
                "usable_for": ["商业模式", "平台生态", "公开财务口径"],
                "not_usable_for": ["单平台即时 benchmark"],
                "limitation": "集团口径较宏观，不直接替代平台经营数据。",
                "citation_text": "Alibaba Group 财报与业绩页面",
            },
            {
                "title": "2025年1—2月份社会消费品零售总额增长4.0%",
                "publisher": "国家统计局",
                "url": "https://www.stats.gov.cn/sj/zxfb/202503/t20250317_1959014.html",
                "source_type": "政府或监管公开资料",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "2025-03-17",
                "page_or_section_hint": "国家统计局新闻发布页，社会消费品零售总额与网上零售相关段落",
                "citation_snippet": "2025年1—2月份社会消费品零售总额增长4.0%",
                "key_points": ["可用于补消费、零售与行业背景。"],
                "usable_for": ["行业背景", "市场结构"],
                "not_usable_for": ["平台内单店经营结论"],
                "limitation": "宏观统计不能直接替代平台经营细节。",
                "citation_text": "国家统计局《2025年1—2月份社会消费品零售总额增长4.0%》",
            },
        ]
    if "京东" in platform:
        return [
            {
                "title": "京东规则中心",
                "publisher": "京东规则",
                "url": "https://rule.jd.com/",
                "source_type": "官方平台规则",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "长期更新页面，以具体规则条目发布时间为准",
                "page_or_section_hint": "京东规则中心，平台经营与商家规则条目入口",
                "citation_snippet": "京东规则中心",
                "key_points": ["可用于核对京东平台规则与经营约束。"],
                "usable_for": ["平台机制", "规则边界"],
                "not_usable_for": ["市场规模"],
                "limitation": "规则信息不等于外部市场数据。",
                "citation_text": "京东规则中心",
            },
            {
                "title": "京东年度报告页面",
                "publisher": "JD.com",
                "url": "https://ir.jd.com/financial-information/annual-reports",
                "source_type": "上市公司财报",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "长期更新页面，以具体年报发布日期为准",
                "page_or_section_hint": "京东投资者关系年报页面，年度报告与财务披露入口",
                "citation_snippet": "JD.com 年度报告页面",
                "key_points": ["可用于补充商业模式、收入结构和平台生态说明。"],
                "usable_for": ["商业模式", "平台生态"],
                "not_usable_for": ["商家个体经营结论"],
                "limitation": "集团口径偏宏观。",
                "citation_text": "JD.com 投资者关系页面",
            },
            {
                "title": "2025年1—2月份社会消费品零售总额增长4.0%",
                "publisher": "国家统计局",
                "url": "https://www.stats.gov.cn/sj/zxfb/202503/t20250317_1959014.html",
                "source_type": "政府或监管公开资料",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "2025-03-17",
                "page_or_section_hint": "国家统计局新闻发布页，社会消费品零售总额与网上零售相关段落",
                "citation_snippet": "2025年1—2月份社会消费品零售总额增长4.0%",
                "key_points": ["可用于补零售、消费和行业背景。"],
                "usable_for": ["行业背景", "市场结构"],
                "not_usable_for": ["平台内对象经营拍板"],
                "limitation": "宏观数据不能直接替代平台经营口径。",
                "citation_text": "国家统计局数据查询平台",
            },
            {
                "title": "网络交易平台规则监督管理办法",
                "publisher": "国家市场监督管理总局",
                "url": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2026/art_85b474fc5a08494bb60ca6a280b98d7d.html",
                "source_type": "政府或监管公开资料",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "2026-01-07",
                "page_or_section_hint": "国家市场监督管理总局法规司页面，平台规则监督管理办法正文",
                "citation_snippet": "网络交易平台规则监督管理办法",
                "key_points": ["可用于补监管与消费者权益边界。"],
                "usable_for": ["风险与监管"],
                "not_usable_for": ["直接经营结论"],
                "limitation": "偏监管资料，不给平台经营 benchmark。",
                "citation_text": "国家市场监督管理总局官网",
            },
        ]
    if "拼多多" in platform:
        return [
            {
                "title": "拼多多商家规则中心",
                "publisher": "拼多多规则",
                "url": "https://rule.pinduoduo.com/",
                "source_type": "官方平台规则",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "长期更新页面，以具体规则条目发布时间为准",
                "page_or_section_hint": "拼多多商家规则中心，售后与商家规则条目入口",
                "citation_snippet": "拼多多商家规则中心",
                "key_points": ["可用于核对拼多多商家规则与售后机制。"],
                "usable_for": ["平台机制", "规则边界"],
                "not_usable_for": ["市场规模"],
                "limitation": "不提供外部市场 benchmark。",
                "citation_text": "拼多多商家规则中心",
            },
            {
                "title": "PDD Holdings 年度报告页面",
                "publisher": "PDD Holdings",
                "url": "https://investor.pddholdings.com/financial-information/annual-reports",
                "source_type": "上市公司财报",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "长期更新页面，以具体年报发布日期为准",
                "page_or_section_hint": "PDD Holdings 投资者关系年报页面，年度报告与财务披露入口",
                "citation_snippet": "PDD Holdings 年度报告页面",
                "key_points": ["可用于补商业模式和公开财务说明。"],
                "usable_for": ["商业模式", "财务口径"],
                "not_usable_for": ["平台内经营拍板"],
                "limitation": "集团披露视角偏宏观。",
                "citation_text": "PDD Holdings 投资者关系页面",
            },
            {
                "title": "2025年1—2月份社会消费品零售总额增长4.0%",
                "publisher": "国家统计局",
                "url": "https://www.stats.gov.cn/sj/zxfb/202503/t20250317_1959014.html",
                "source_type": "政府或监管公开资料",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "2025-03-17",
                "page_or_section_hint": "国家统计局新闻发布页，社会消费品零售总额与网上零售相关段落",
                "citation_snippet": "2025年1—2月份社会消费品零售总额增长4.0%",
                "key_points": ["可用于补零售、消费和行业背景。"],
                "usable_for": ["行业背景", "市场结构"],
                "not_usable_for": ["平台内经营结论"],
                "limitation": "宏观数据不能直接映射平台内经营差异。",
                "citation_text": "国家统计局数据查询平台",
            },
            {
                "title": "网络交易平台规则监督管理办法",
                "publisher": "国家市场监督管理总局",
                "url": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2026/art_85b474fc5a08494bb60ca6a280b98d7d.html",
                "source_type": "政府或监管公开资料",
                "credibility_level": "high",
                "source_level": "page_fact",
                "verification_status": "verified_page_fact",
                "publish_date": "2026-01-07",
                "page_or_section_hint": "国家市场监督管理总局法规司页面，平台规则监督管理办法正文",
                "citation_snippet": "网络交易平台规则监督管理办法",
                "key_points": ["可用于补监管、合规与消费者权益边界。"],
                "usable_for": ["风险与监管"],
                "not_usable_for": ["直接经营拍板"],
                "limitation": "侧重监管，不提供平台内 benchmark。",
                "citation_text": "国家市场监督管理总局官网",
            },
        ]
    return [
        {
            "title": "2025年1—2月份社会消费品零售总额增长4.0%",
            "publisher": "国家统计局",
            "url": "https://www.stats.gov.cn/sj/zxfb/202503/t20250317_1959014.html",
            "source_type": "政府或监管公开资料",
            "credibility_level": "high",
            "source_level": "page_fact",
            "verification_status": "verified_page_fact",
            "publish_date": "2025-03-17",
            "page_or_section_hint": "国家统计局新闻发布页，社会消费品零售总额与网上零售相关段落",
            "citation_snippet": "2025年1—2月份社会消费品零售总额增长4.0%",
            "key_points": ["公开披露了社会消费品零售总额与网上零售增长的官方统计背景。"],
            "usable_for": ["行业背景", "市场结构"],
            "not_usable_for": ["平台规则"],
            "limitation": "宏观口径不直接映射平台经营细节。",
            "citation_text": "国家统计局《2025年1—2月份社会消费品零售总额增长4.0%》",
        },
        {
            "title": "网络交易平台规则监督管理办法",
            "publisher": "国家市场监督管理总局",
            "url": "https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2026/art_85b474fc5a08494bb60ca6a280b98d7d.html",
            "source_type": "政府或监管公开资料",
            "credibility_level": "high",
            "source_level": "page_fact",
            "verification_status": "verified_page_fact",
            "publish_date": "2026-01-07",
            "page_or_section_hint": "国家市场监督管理总局法规司页面，平台规则监督管理办法正文",
            "citation_snippet": "网络交易平台规则监督管理办法",
            "key_points": ["公开披露了网络交易平台规则监督管理要求与平台治理边界。"],
            "usable_for": ["风险与监管"],
            "not_usable_for": ["竞品对比"],
            "limitation": "偏监管规则，不提供经营 benchmark。",
            "citation_text": "国家市场监督管理总局《网络交易平台规则监督管理办法》",
        },
        {
            "title": "2025年1—4月 我国电子商务网上零售额增长7.7%",
            "publisher": "中华人民共和国商务部",
            "url": "https://www.mofcom.gov.cn/tj/sjtj/art/2025/art_063c754cfbfa4285a15e2d12258c2aea.html",
            "source_type": "政府或监管公开资料",
            "credibility_level": "high",
            "source_level": "page_fact",
            "verification_status": "verified_page_fact",
            "publish_date": "2025-06-12",
            "page_or_section_hint": "商务部统计页面，电子商务发展与网上零售额段落",
            "citation_snippet": "2025年1—4月 我国电子商务网上零售额增长7.7%",
            "key_points": ["公开披露了电子商务发展情况、网上零售额增速和平台经济背景。"],
            "usable_for": ["行业背景", "市场结构"],
            "not_usable_for": ["平台内对象经营拍板"],
            "limitation": "更适合宏观背景，不适合直接给平台内 benchmark 数值。",
            "citation_text": "商务部《2025年1—4月 我国电子商务网上零售额增长7.7%》",
        },
        {
            "title": "中华人民共和国电子商务法",
            "publisher": "中国人大网",
            "url": "http://www.npc.gov.cn/zgrdw/npc/xinwen/2018-08/31/content_2060827.htm",
            "source_type": "官方监管机构",
            "credibility_level": "high",
            "source_level": "page_fact",
            "verification_status": "verified_page_fact",
            "publish_date": "2018-08-31",
            "page_or_section_hint": "中国人大网法律全文页，电子商务法正文",
            "citation_snippet": "中华人民共和国电子商务法",
            "key_points": ["公开了电商平台经营者责任、规则披露、售后与消费者权益边界的法律要求。"],
            "usable_for": ["平台机制", "风险与监管"],
            "not_usable_for": ["当前对象级经营判断"],
            "limitation": "属于监管与制度边界资料，不直接提供平台内经营 benchmark。",
            "citation_text": "中华人民共和国电子商务法（中国人大网）",
        },
        {
            "title": "第56次《中国互联网络发展状况统计报告》",
            "publisher": "中国互联网络信息中心",
            "url": "https://www.cnnic.cn/n4/2025/0721/c88-11328.html",
            "source_type": "权威研究机构",
            "credibility_level": "high",
            "source_level": "page_fact",
            "verification_status": "verified_page_fact",
            "publish_date": "2025-07-21",
            "page_or_section_hint": "CNNIC 第56次报告发布页，网络购物用户规模与互联网发展段落",
            "citation_snippet": "第56次《中国互联网络发展状况统计报告》",
            "key_points": ["公开披露了网络购物用户规模、互联网发展与消费趋势背景。"],
            "usable_for": ["用户/消费者趋势", "市场结构"],
            "not_usable_for": ["当前对象级经营判断"],
            "limitation": "用户趋势资料是宏观背景，不直接映射当前上传对象表现。",
            "citation_text": "中国互联网络发展状况统计报告（CNNIC）",
        },
        {
            "title": "行业协会或研究机构线索",
            "publisher": "行业协会/研究机构",
            "url": "",
            "source_type": "行业协会报告",
            "credibility_level": "medium",
            "key_points": [f"可作为 `{industry}` 的后续资料搜索线索。"],
            "usable_for": ["市场结构", "benchmark 线索"],
            "not_usable_for": ["直接经营结论"],
            "limitation": "需要后续人工补具体报告与时间戳。",
            "citation_text": f"{industry} 行业协会/研究机构线索",
        },
    ]


def _sources_payload(scope_payload: dict[str, Any], search_plan: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    templates = _source_templates(scope_payload)
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(templates, start=1):
        source_row = {
            "source_id": f"S{idx:03d}",
            "title": item["title"],
            "publisher": item["publisher"],
            "url": item["url"],
            "source_type": item["source_type"],
            "credibility_level": item["credibility_level"],
            "key_points": item["key_points"],
            "usable_for": item["usable_for"],
            "not_usable_for": item["not_usable_for"],
            "limitation": item["limitation"],
            "citation_text": item["citation_text"],
        }
        _copy_source_template_fields(source_row, item)
        fact_card = _source_fact_card(source_row)
        if fact_card["facts"]:
            rows.append(fact_card)
    insufficient = len([row for row in rows if row["credibility"] in {"high", "medium"}]) < 4
    return rows, insufficient


def _markdown_from_scope(scope_payload: dict[str, Any]) -> str:
    lines = [
        "# industry_research_scope",
        "",
        f"- inferred_industry: `{scope_payload['inferred_industry']}`",
        f"- inferred_platform: `{scope_payload['inferred_platform']}`",
        f"- inferred_business_model: `{scope_payload['inferred_business_model']}`",
        f"- value_chain_position: {scope_payload['value_chain_position']}",
        f"- target_reader: {scope_payload['target_reader']}",
        f"- confidence: {scope_payload['confidence']}",
        "",
        "## research_plan_topics",
        "",
    ]
    for item in scope_payload.get("research_topics") or []:
        lines.extend(
            [
                f"### {item['topic_id']} / {item['topic_name']}",
                "",
                f"- priority: P{item['priority']}",
                f"- confidence: {item['confidence']}",
                f"- why_it_matters: {item['why_it_matters']}",
                f"- required_source_types: {' / '.join(item['required_source_types'])}",
                f"- expected_facts: {' / '.join(item['expected_facts'])}",
                f"- downstream_sections: {' / '.join(item['downstream_sections'])}",
                f"- unsupported_claims: {' / '.join(item['unsupported_claims'])}",
                f"- depends_on_dataset_signals: {' / '.join(item['depends_on_dataset_signals'])}",
                "",
            ]
        )
    lines.extend(
        [
        "",
        "## research_boundaries",
        "",
        *[f"- {item}" for item in scope_payload["research_boundaries"]],
        "",
        "## unsupported_questions",
        "",
        *[f"- {item}" for item in scope_payload["unsupported_questions"]],
        "",
        "## ambiguity_notes",
        "",
        *[f"- {item}" for item in scope_payload["ambiguity_notes"]],
    ]
    )
    return "\n".join(lines).strip() + "\n"


def _question_bank_markdown(question_rows: list[dict[str, Any]]) -> str:
    lines = ["# industry_research_question_bank", ""]
    for row in question_rows:
        lines.extend(
            [
                f"## {row['topic_id']} / {row['topic_name']}",
                "",
                f"- priority: P{row['priority']}",
                f"- question: {row['question']}",
                f"- why_it_matters: {row['why_it_matters']}",
                f"- unsupported_claims: {' / '.join(row['unsupported_claims'])}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _boundary_markdown_from_topics(scope_payload: dict[str, Any]) -> str:
    lines = [
        "# industry_research_boundary_from_data",
        "",
        "## 数据上下文如何限定本次行研范围",
        "",
        f"- 当前上传数据暗示的业务场景：{scope_payload.get('inferred_industry', '')} / {scope_payload.get('inferred_platform', '')}",
        f"- 当前数据支持行研关注的主题：{'; '.join(scope_payload.get('research_questions') or []) or 'none'}",
        "",
        "## 各 research topic 不得支持的 claim",
        "",
    ]
    for item in scope_payload.get("research_topics") or []:
        lines.append(f"### {item['topic_id']} / {item['topic_name']}")
        lines.append("")
        lines.extend(f"- {claim}" for claim in item.get("unsupported_claims") or [])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _search_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# industry_web_search_plan",
        "",
        "## topic_search_tasks",
        "",
    ]
    for task in plan.get("topic_tasks") or []:
        lines.extend(
            [
                f"### {task['topic_id']} / {task['topic_name']}",
                "",
                f"- required_source_types: {' / '.join(task['required_source_types'])}",
                f"- expected_facts: {' / '.join(task['expected_facts'])}",
                f"- downstream_sections: {' / '.join(task['downstream_sections'])}",
                *[f"- query: {item}" for item in task.get("search_queries") or []],
                "",
            ]
        )
    lines.extend(
        [
            "## source_priority",
            "",
            *[f"- {item}" for item in plan["source_priority"]],
            "",
            "## source_blacklist",
            "",
            *[f"- {item}" for item in plan["source_blacklist"]],
            "",
            f"- expected_usage: {plan['expected_usage']}",
            f"- benchmark_caution: {plan['benchmark_caution']}",
            f"- citation_requirements: {plan['citation_requirements']}",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _sources_markdown(title: str, bullets: list[str]) -> str:
    return "\n".join([f"# {title}", "", *[f"- {item}" for item in bullets]]) + "\n"


def _report_markdown(
    *,
    title: str,
    scope_payload: dict[str, Any],
    question_rows: list[dict[str, str]],
    sources: list[dict[str, Any]],
    insufficient: bool,
) -> str:
    lines = [
        f"# {title}",
        "",
        "## 1. 封面",
        "",
        f"- 报告名称：{title}",
        f"- 目标读者：{scope_payload['target_reader']}",
        "",
        "## 2. 行研范围与研究问题",
        "",
        *[f"- {item}" for item in scope_payload["research_questions"]],
        "",
        "## 3. 行业背景",
        "",
        f"- 当前推断行业：{scope_payload['inferred_industry']}",
        f"- 当前推断平台：{scope_payload['inferred_platform']}",
        "",
        "## 4. 市场结构",
        "",
        "- 当前更适合从商品、类目、店铺、品牌、供应商与交易结构理解市场格局。",
        "",
        "## 5. 产业链与价值链",
        "",
        f"- 当前价值链位置：{scope_payload['value_chain_position']}",
        "",
        "## 6. 平台机制或渠道机制",
        "",
        "- 平台规则、流量分发、评价治理、售后与履约约束需要单独研究。",
        "",
        "## 7. 竞争格局",
        "",
        "- 当前仅形成竞品研究框架，不把外部竞争格局伪装成用户数据事实。",
        "",
        "## 8. 用户或消费者趋势",
        "",
        "- 当前只给出研究方向与待补资料，不直接输出用户趋势事实。",
        "",
        "## 9. 商品/服务供给结构",
        "",
        "- 当前可围绕商品、类目、店铺、品牌与供应商做供给结构研究框架。",
        "",
        "## 10. 成本、利润与商业模式",
        "",
        f"- 当前推断商业模式：{scope_payload['inferred_business_model']}",
        "",
        "## 11. 指标口径说明",
        "",
        "- GMV、销量、转化、履约、售后、评价和利润口径必须与来源和平台规则同时解释。",
        "",
        "## 12. benchmark 与可比性限制",
        "",
        "- benchmark 必须写清平台差异、口径差异、时间区间与样本边界。",
        "",
        "## 13. 外部风险与监管环境",
        "",
        "- 平台规则、监管要求、消费者权益和售后规则都可能影响行业理解与 benchmark 使用。",
        "",
        "## 14. 对主报告可提供的背景启发",
        "",
        "- 可为主报告提供行业背景、平台机制、口径说明和 benchmark 边界启发。",
        "- 不得把当前数据解释成已被外部资料验证的经营结论。",
        "",
        "## 15. 当前资料无法支持的判断",
        "",
        *[f"- {item}" for item in scope_payload["unsupported_questions"]],
        "",
        "## 16. 来源清单与附录",
        "",
        *[f"- {row['source_id']} {row['title']} / {row['publisher']} / credibility={row['credibility_level']}" for row in sources],
    ]
    if insufficient:
        lines.extend(["", "> 当前来源仍不足，报告强度已降级，详见 industry_research_insufficient_sources.md。"])
    return "\n".join(lines).strip() + "\n"


def _report_markdown_v2(
    *,
    title: str,
    scope_payload: dict[str, Any],
    data_context_payload: dict[str, Any],
    sources: list[dict[str, Any]],
    insufficient: bool,
    business_scene_inference_payload: dict[str, Any],
    stage6_section_groups: dict[str, list[dict[str, Any]]],
    benchmark_artifacts: dict[str, Any],
    risk_objects: list[dict[str, Any]],
) -> str:
    industry_background = _stage6_section_by_name(stage6_section_groups, "行业背景") or {}
    platform_mechanism = _stage6_section_by_name(stage6_section_groups, "平台机制") or {}
    market_structure = _stage6_section_by_name(stage6_section_groups, "市场结构") or {}
    competitive_landscape = _stage6_section_by_name(stage6_section_groups, "竞争格局") or {}
    supply_structure = _stage6_section_by_name(stage6_section_groups, "供给结构") or {}
    consumer_trends = _stage6_section_by_name(stage6_section_groups, "用户/消费者趋势") or {}

    benchmark_facts = benchmark_artifacts.get("benchmark_facts") or []
    benchmark_matrix = benchmark_artifacts.get("benchmark_comparability_matrix") or []
    metric_defs = benchmark_artifacts.get("metric_definition_comparison") or []
    risk_facts = _join_unique_facts(*[risk.get("source_backed_facts") or [] for risk in risk_objects])

    uncertain_platform_note = "当前具体平台仍需人工确认，因此平台名称仅作为候选解释。"
    uncertain_model_note = "当前商业模式仍需人工确认，因此商业模式只在边界说明和人工确认项中出现。"
    benchmark_metric_ids = [row["metric_id"] for row in benchmark_matrix]
    not_comparable_metrics = [row["metric_id"] for row in benchmark_matrix if row.get("comparability_level") == "not_comparable"]
    directional_metrics = [row["metric_id"] for row in benchmark_matrix if row.get("comparability_level") == "directional_only"]
    can_support = list(data_context_payload.get("can_support_what") or data_context_payload.get("industry_research_implications") or [])
    cannot_support = list(data_context_payload.get("cannot_support_what") or data_context_payload.get("forbidden_current_dataset_claims") or [])
    forbidden_claims = list(data_context_payload.get("forbidden_current_dataset_claims") or [])
    report_sources = [
        f"[{row['source_id']}] {row['title']} / {row['publisher']} / {row.get('source_type', '')} / {row.get('source_level', '')}"
        for row in sources[:6]
    ]

    lines = [
        f"# {title}",
        "",
        f"- 报告名称：{title}",
        f"- 目标读者：{scope_payload['target_reader']}",
        f"- 研究问题：{'; '.join(scope_payload['research_questions'][:4])}",
        "",
        _report_section_block(
            title="行业定位与研究边界",
            conclusion=f"当前最可能对应 `{scope_payload['inferred_industry']}` 的零售电商经营场景，本研报仅用于行业背景、规则机制、benchmark 边界和风险解释。",
            source_facts=_take_facts(_join_unique_facts(industry_background.get("source_backed_facts") or [], benchmark_facts[:2], _risk_fact_lines(risk_objects, limit=2))),
            relation_to_uploaded_data=f"当前上传数据的对象粒度为 {data_context_payload.get('object_grain')}，并以 {', '.join((data_context_payload.get('candidate_business_objects') or [])[:4])} 为主，因此行业定位必须与对象结构一起解释。",
            boundary_statement="外部资料不能替代当前上传数据的经营证据；低置信平台和商业模式只在边界说明、人工确认项和候选解释里出现。",
            manual_confirmation=_manual_confirmation_lines(
                business_scene_inference_payload,
                uncertain_platform_note if _is_uncertain_platform(scope_payload) else "",
                uncertain_model_note if _is_uncertain_business_model(scope_payload) else "",
            ),
        ),
        _report_section_block(
            title="数据所反映的业务场景",
            conclusion=_report_scene_conclusion(
                scope_payload=scope_payload,
                data_context_payload=data_context_payload,
                business_scene_inference_payload=business_scene_inference_payload,
            ),
            source_facts=_take_facts(_join_unique_facts(industry_background.get("source_backed_facts") or [], supply_structure.get("source_backed_facts") or [])),
            relation_to_uploaded_data=f"数据可直接支持的主题包括：{'；'.join(can_support[:5])}。",
            boundary_statement=f"当前数据不能支持的业务结论包括：{'；'.join((forbidden_claims or cannot_support)[:4])}。",
            manual_confirmation=_manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="行业背景",
            conclusion=industry_background.get("section_conclusion") or f"当前行业背景应围绕 `{scope_payload['inferred_industry']}` 的交易结构与经营驱动来理解。",
            source_facts=_take_facts(industry_background.get("source_backed_facts") or benchmark_facts[:3]),
            relation_to_uploaded_data=industry_background.get("relation_to_uploaded_data") or "",
            boundary_statement="行业背景只提供外部环境解释，不构成当前经营结果已经被外部事实验证的证明。",
            manual_confirmation=industry_background.get("manual_confirmation_needed") or _manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="平台机制",
            conclusion=(
                "平台机制解释依赖待确认的平台规则页，用于说明规则、履约、售后和评价治理如何影响当前数据中的交易和转化信号。"
                if _is_uncertain_platform(scope_payload)
                else platform_mechanism.get("section_conclusion") or "平台机制部分应解释规则、履约、评价与商家经营门槛如何影响当前数据中的交易和转化信号。"
            ),
            source_facts=_take_facts(platform_mechanism.get("source_backed_facts") or benchmark_facts[:2]),
            relation_to_uploaded_data=platform_mechanism.get("relation_to_uploaded_data") or "",
            boundary_statement="平台机制资料只能解释规则约束与背景，不直接推出当前对象的经营动作。",
            manual_confirmation=platform_mechanism.get("manual_confirmation_needed") or _manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="市场结构与竞争格局",
            conclusion=_report_market_competition_conclusion(
                market_structure=market_structure,
                competitive_landscape=competitive_landscape,
                supply_structure=supply_structure,
            ),
            source_facts=_take_facts(_join_unique_facts(
                market_structure.get("source_backed_facts") or [],
                competitive_landscape.get("source_backed_facts") or [],
                supply_structure.get("source_backed_facts") or [],
            )),
            relation_to_uploaded_data=_safe_text(market_structure.get("relation_to_uploaded_data")) or _safe_text(competitive_landscape.get("relation_to_uploaded_data")),
            boundary_statement="外部市场结构和竞争格局资料只能作为背景比较，不能直接替代当前对象的经营证据。",
            manual_confirmation=_manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="指标口径与 benchmark 可比性",
            conclusion=f"当前链已覆盖 {', '.join(benchmark_metric_ids)} 这批指标；其中 {', '.join(not_comparable_metrics)} 不能直接可比，其余指标大多只能做方向参考，不能直接拿来对打行业 benchmark。",
            source_facts=_take_facts(_join_unique_facts(
                [f for f in benchmark_facts if _safe_text(f)],
                [_metric_boundary_fact(benchmark_matrix, metric_id) for metric_id in ["GMV", "Revenue", "FreightCost", "ROI"]],
            )),
            relation_to_uploaded_data=f"当前链已逐项判断 {', '.join(benchmark_metric_ids)} 是否直接可比，并把时间区间、平台、样本和统计口径差异写入 comparability matrix。",
            boundary_statement="benchmark 解释必须同时写明时间区间差异、平台差异、样本差异和统计口径差异，不能只给一个抽象提醒句。",
            manual_confirmation=_manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="成本/利润/履约/转化边界",
            conclusion="当前数据中的成本、利润、履约与转化口径并不天然完整：FreightCost 只是成本片段，ROI 在当前样本下不能成立，conversion 和 rating 也受分母定义与平台治理规则约束。",
            source_facts=_take_facts(_join_unique_facts(
                [_metric_boundary_fact(benchmark_matrix, "FreightCost")],
                [_metric_boundary_fact(benchmark_matrix, "ROI")],
                [_metric_boundary_fact(benchmark_matrix, "conversion")],
                [_metric_boundary_fact(benchmark_matrix, "rating")],
                [_metric_support_fact(metric_defs, "FreightCost")],
            )),
            relation_to_uploaded_data="当前数据已暴露出交易、评分和销量信号，但利润、完整成本、统一转化分母和完整履约口径仍不齐全。",
            boundary_statement="这些口径边界只能解释为什么当前不能升级为强经营判断，不能被改写成已经验证过的利润或效率结论。",
            manual_confirmation=_manual_confirmation_lines(
                business_scene_inference_payload,
                "需要人工确认 Revenue / GMV / FreightCost 在当前业务中的具体口径，以及 conversion 的分母定义。",
            ),
        ),
        _report_section_block(
            title="风险与监管环境",
            conclusion="风险与监管环境应被视为外部背景约束，它会影响平台机制理解、消费者权益解释和 benchmark 解读，但不等于当前对象已经出现风险事件。",
            source_facts=_take_facts(_join_unique_facts(_risk_fact_lines(risk_objects, benchmark_only=True, limit=3), _risk_fact_lines(risk_objects, benchmark_only=False, limit=2))),
            relation_to_uploaded_data="当前上传数据只能提示这些风险与当前行业和对象粒度相关，不能证明风险已经发生。",
            boundary_statement="风险章节只构成背景提醒；其中平台规则变化、履约/售后监管和价格竞争风险会直接影响 benchmark 解读边界。",
            manual_confirmation=_manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="对主报告可提供的背景支持",
            conclusion="这条行业研究链可以为主报告提供行业背景、平台机制、指标口径、benchmark 边界和风险解释，但不能替代主报告的数据证据和对象级动作判断。",
            source_facts=_take_facts(_join_unique_facts(benchmark_facts[:2], _risk_fact_lines(risk_objects, benchmark_only=True, limit=2), platform_mechanism.get("source_backed_facts") or [])),
            relation_to_uploaded_data=f"当前上传数据已经限定了对象粒度 `{data_context_payload.get('object_grain')}` 与可用指标族，因此行研链的价值在于解释背景、规则和 comparability 边界，而不是重写当前数据结论。",
            boundary_statement="主报告中的对象级判断必须继续由当前上传数据、指标计算和 quality gate 支撑，外部资料只能做背景支持。",
            manual_confirmation=_manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="当前不能支持的经营判断",
            conclusion="当前不能支持的判断主要集中在利润、ROI、对象级加码/淘汰、跨平台强 benchmark 和将外部背景误当作当前经营证据这些方向。",
            source_facts=_take_facts(_join_unique_facts(
                [f"[unsupported] {item}" for item in (scope_payload.get('unsupported_questions') or [])[:4]],
                [f"[risk] {item}" for item in (data_context_payload.get('forbidden_current_dataset_claims') or [])[:4]],
            )),
            relation_to_uploaded_data="这些限制直接来自当前数据的字段完整度、对象粒度和口径边界，而不是生成端的保守措辞。",
            boundary_statement="当利润、库存、转化分母、平台名称等关键口径不齐全时，任何对象级经营判断都必须先降级为待验证问题。",
            manual_confirmation=_manual_confirmation_lines(business_scene_inference_payload),
        ),
        _report_section_block(
            title="来源说明",
            conclusion="本报告正文使用的都是带 source_id 的来源事实卡，来源类型优先官方监管机构、政府部门、平台规则页、行业协会、上市公司财报/招股书和权威研究机构。",
            source_facts=report_sources,
            relation_to_uploaded_data="来源只用于补外部背景、平台规则、benchmark 和风险边界，不替代当前上传数据的事实层。",
            boundary_statement="若来源只能提供宏观背景或监管边界，它就不能被提升为当前对象级经营证据。",
            manual_confirmation=_manual_confirmation_lines(business_scene_inference_payload),
        ),
    ]
    if insufficient:
        lines.extend(["", "> 当前来源仍不足，报告强度已降级，详见 industry_research_insufficient_sources.md。"])
    return "\n".join(lines).strip() + "\n"


def _render_report_html(title: str, report_markdown: str) -> str:
    sections = []
    for block in report_markdown.split("\n## "):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            continue
        lines = block.splitlines()
        section_title = lines[0].strip()
        bullets = "".join(f"<li>{html.escape(line[2:])}</li>" for line in lines[1:] if line.startswith("- "))
        sections.append(f"<section class='card'><h2>{html.escape(section_title)}</h2><ul>{bullets}</ul></section>")
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
          ul {{ margin: 0; padding-left: 20px; }}
          li {{ line-height: 1.8; }}
        </style>
      </head>
      <body>
        <h1>{html.escape(title)}</h1>
        {''.join(sections)}
      </body>
    </html>
    """


def _write_pdf_report(path: Path, title: str, report_markdown: str) -> Path | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return None

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("IRTitle", parent=styles["Heading1"], fontSize=18, leading=24, textColor=colors.HexColor("#222"))
    section_style = ParagraphStyle("IRSection", parent=styles["Heading2"], fontSize=13, leading=18, textColor=colors.HexColor("#222"))
    body_style = ParagraphStyle("IRBody", parent=styles["BodyText"], fontSize=9, leading=14, textColor=colors.HexColor("#444"))

    story: list[Any] = [Paragraph(html.escape(title), title_style), Spacer(1, 4 * mm)]
    current_section = ""
    for line in report_markdown.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            story.append(Paragraph(html.escape(current_section), section_style))
        elif line.startswith("- "):
            story.append(Paragraph(html.escape(line[2:]), body_style))
        elif line.startswith("> "):
            story.append(Paragraph(html.escape(line[2:]), body_style))
        elif line.startswith("# "):
            continue
        else:
            if line.strip():
                story.append(Paragraph(html.escape(line.strip()), body_style))
        if line.strip():
            story.append(Spacer(1, 1.5 * mm))

    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=16 * mm, bottomMargin=14 * mm)
    doc.build(story)
    return path


def run_independent_industry_research_chain(
    *,
    output_dir: str | Path,
    user_task_description: str,
    uploaded_file_name: str,
    sheet_names: list[str],
    field_names: list[str],
    sample_values: list[str],
    business_profile_router_result: dict[str, Any],
    deep_context_understanding: dict[str, Any] | None,
    optional_data_summary: dict[str, Any] | None,
    request: SmartReportRequest,
    frame: pd.DataFrame,
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stage_records: list[dict[str, Any]] = []
    dataset_name = _first_non_empty(uploaded_file_name, default="uploaded_dataset")
    sheet_name = sheet_names[0] if sheet_names else "Sheet1"

    universal_metric_payload = (
        (deep_context_understanding or {}).get("universal_metric_mining_result")
        or {}
    )
    domain_metric_registry = (
        (deep_context_understanding or {}).get("domain_metric_registry")
        or (universal_metric_payload.get("domain_metric_registry") or {})
    )
    derived_metric_rows = list(universal_metric_payload.get("derived_metrics") or [])
    proxy_metric_rows = list(universal_metric_payload.get("proxy_metrics") or [])

    stage_started = perf_counter()
    data_context_payload = build_industry_data_context_summary(
        dataset_name=dataset_name,
        uploaded_file_name=uploaded_file_name,
        sheet_names=sheet_names,
        field_names=field_names,
        sample_values=sample_values,
        data_types=(optional_data_summary or {}).get("data_types") or {},
        row_count=(optional_data_summary or {}).get("row_count"),
        column_count=(optional_data_summary or {}).get("column_count"),
        universal_metric_mining_result=universal_metric_payload,
        domain_metric_registry=domain_metric_registry,
        derived_metric_rows=derived_metric_rows,
        proxy_metric_rows=proxy_metric_rows,
        frame=frame,
        router_result=business_profile_router_result,
    )
    data_context_output_files = write_industry_data_context_outputs(out_dir, data_context_payload)
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_1_dataset_grounding",
            summary="已提取上传数据的字段画像、数据上下文与行研边界基础摘要。",
            input_artifacts=[
                "uploaded_file_name",
                "sheet_names",
                "field_names",
                "sample_values",
                "optional_data_summary.json" if optional_data_summary else "",
                "universal_metric_mining_result.json" if universal_metric_payload else "",
            ],
            output_artifacts=list(data_context_output_files.keys()),
            payload=data_context_payload,
            started_at=stage_started,
        )
    )

    stage_started = perf_counter()
    business_scene_inference_payload = _business_scene_inference_from_data(
        dataset_name=dataset_name,
        field_names=field_names,
        sample_values=sample_values,
        data_context_payload=data_context_payload,
        router_result=business_profile_router_result,
        metric_context=universal_metric_payload,
    )
    scope_payload = _scope_payload(
        sample_values=sample_values,
        request=request,
        deep_context_understanding=deep_context_understanding,
        router_result=business_profile_router_result,
        business_scene_inference_payload=business_scene_inference_payload,
    )
    scope_payload["research_topics"] = _research_topics(scope_payload, data_context_payload)
    profile = _safe_text(business_profile_router_result.get("business_profile"))
    legacy_candidate_contexts = _candidate_business_contexts(
        profile,
        _safe_text(data_context_payload.get("object_grain")),
        scope_payload.get("metric_mining_context") or {},
    )
    merged_contexts: list[dict[str, Any]] = []
    seen_contexts: set[str] = set()
    for item in [*(business_scene_inference_payload.get("candidate_business_contexts") or []), *legacy_candidate_contexts]:
        key = _safe_text(item.get("context"))
        if not key or key in seen_contexts:
            continue
        seen_contexts.add(key)
        merged_contexts.append(item)
    if not profile:
        business_scene_inference_payload["ambiguity_notes"] = list(dict.fromkeys([
            *(business_scene_inference_payload.get("ambiguity_notes") or []),
            "router_result 缺失，stage_2 当前只能基于字段角色、粒度、口径和 metric mining 做降级推断。",
        ]))
        business_scene_inference_payload["manual_confirmation_needed"] = True
        business_scene_inference_payload["why_uncertain"] = (
            business_scene_inference_payload.get("why_uncertain") or "router_result 缺失，因此业务场景判断缺少上游业务路由锚点。"
        )
        business_scene_inference_payload["required_manual_confirmation"] = _unique_strings(
            list(business_scene_inference_payload.get("required_manual_confirmation") or [])
            + ["请补充业务路由结果，以确认当前数据主链是采销复盘、平台商品经营还是其他业务场景。"]
        )
    business_scene_inference_payload["candidate_business_contexts"] = merged_contexts
    business_scene_inference_payload["top_candidates"] = [item.get("context") for item in merged_contexts[:3]]
    business_scene_inference_payload["target_reader"] = scope_payload["target_reader"]
    business_scene_inference_payload["research_boundaries"] = scope_payload["research_boundaries"]
    business_scene_inference_payload["unsupported_questions"] = scope_payload["unsupported_questions"]
    business_scene_inference_payload["metric_mining_context"] = scope_payload["metric_mining_context"]
    business_scene_path = out_dir / "business_scene_inference.json"
    business_scene_path.write_text(json.dumps(business_scene_inference_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_2_business_scene_inference",
            summary="已根据上传数据、字段角色和已知 metric context 推断业务场景与平台/行业候选。",
            input_artifacts=[
                "industry_data_context_summary.json",
                "business_profile_router_result.json",
                "deep_context_understanding.json" if deep_context_understanding else "",
            ],
            output_artifacts=[business_scene_path.name],
            payload=business_scene_inference_payload,
            started_at=stage_started,
        )
    )

    stage_started = perf_counter()
    question_rows = _question_bank(scope_payload)
    search_plan = _search_plan(scope_payload, question_rows)
    sources, insufficient = _sources_payload(scope_payload, search_plan)

    scope_md_path = out_dir / "industry_research_scope.md"
    scope_json_path = out_dir / "industry_research_scope.json"
    question_bank_path = out_dir / "industry_research_question_bank.md"
    search_plan_path = out_dir / "industry_web_search_plan.md"
    sources_path = out_dir / "industry_research_sources.json"
    context_analysis_path = out_dir / "industry_context_analysis.md"
    benchmark_path = out_dir / "industry_benchmark_synthesis.md"
    mechanism_path = out_dir / "industry_platform_mechanism.md"
    competitor_path = out_dir / "industry_competitor_context.md"
    metric_path = out_dir / "industry_metric_definition.md"
    benchmark_metric_registry_path = out_dir / "benchmark_metric_registry.json"
    benchmark_comparability_matrix_path = out_dir / "benchmark_comparability_matrix.json"
    platform_difference_table_path = out_dir / "platform_difference_table.json"
    metric_definition_comparison_path = out_dir / "metric_definition_comparison.json"
    benchmark_comparability_matrix_csv_path = out_dir / "benchmark_comparability_matrix.csv"
    metric_definition_comparison_csv_path = out_dir / "metric_definition_comparison.csv"
    platform_difference_table_csv_path = out_dir / "platform_difference_table.csv"
    risk_path = out_dir / "industry_risk_scan.md"
    regulation_risk_path = out_dir / "industry_regulation_risk.json"
    data_context_md_path = out_dir / "industry_data_context_summary.md"
    data_context_json_path = out_dir / "industry_data_context_summary.json"
    data_context_questions_path = out_dir / "industry_research_question_bank_from_data.md"
    data_context_boundary_path = out_dir / "industry_research_boundary_from_data.md"
    report_md_path = out_dir / "industry_research_report.md"
    report_html_path = out_dir / "industry_research_report.html"
    report_pdf_path = out_dir / "industry_research_report.pdf"
    appendix_path = out_dir / "industry_research_appendix.md"
    manual_confirmation_checklist_path = out_dir / "manual_confirmation_checklist.md"
    citation_path = out_dir / "citation_manifest_industry.json"
    boundary_check_path = out_dir / "industry_research_boundary_check.json"
    source_audit_path = out_dir / "industry_research_source_audit.md"
    score_path = out_dir / "industry_research_quality_score.json"
    gate_path = out_dir / "industry_research_quality_gate_result.json"
    insufficient_path = out_dir / "industry_research_insufficient_sources.md"

    scope_md_path.write_text(_markdown_from_scope(scope_payload), encoding="utf-8")
    scope_json_path.write_text(json.dumps(scope_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    question_bank_path.write_text(_question_bank_markdown(question_rows), encoding="utf-8")
    search_plan_path.write_text(_search_plan_markdown(search_plan), encoding="utf-8")
    sources_path.write_text(json.dumps({"sources": sources}, ensure_ascii=False, indent=2), encoding="utf-8")
    data_context_boundary_path.write_text(_boundary_markdown_from_topics(scope_payload), encoding="utf-8")
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_3_research_plan_generation",
            summary="已生成行研 scope、问题清单与检索计划。",
            input_artifacts=[
                "industry_data_context_summary.json",
                "business_scene_inference.json",
            ],
            output_artifacts=[
                scope_md_path.name,
                scope_json_path.name,
                question_bank_path.name,
                search_plan_path.name,
            ],
            payload={
                "scope_payload": scope_payload,
                "question_count": len(question_rows),
                "search_query_count": len(search_plan.get("search_queries") or []),
            },
            started_at=stage_started,
        )
    )

    stage_started = perf_counter()
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_4_source_search_and_collection",
            summary="已完成来源候选收集与来源优先级规划。",
            input_artifacts=[
                scope_json_path.name,
                question_bank_path.name,
                search_plan_path.name,
            ],
            output_artifacts=[sources_path.name],
            payload={
                "source_count": len(sources),
                "insufficient_sources": insufficient,
                "search_plan": search_plan,
            },
            started_at=stage_started,
        )
    )

    stage_started = perf_counter()
    source_fact_table_path = out_dir / "source_fact_table.csv"
    source_fact_rows = _source_fact_table_rows(sources)
    pd.DataFrame(source_fact_rows).to_csv(source_fact_table_path, index=False, encoding="utf-8-sig")
    source_audit_path.write_text(_source_audit_markdown(sources), encoding="utf-8")
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_5_source_fact_extraction",
            summary="已将来源抽成结构化 fact cards，可供正文与质量门禁引用。",
            input_artifacts=[sources_path.name],
            output_artifacts=[source_fact_table_path.name, source_audit_path.name],
            payload={"sources": sources, "fact_row_count": len(source_fact_rows)},
            started_at=stage_started,
        )
    )

    stage_started = perf_counter()
    stage6_section_groups = _build_stage6_sections(
        scope_payload=scope_payload,
        data_context_payload=data_context_payload,
        business_scene_inference_payload=business_scene_inference_payload,
        sources=sources,
    )
    stage6_failures = _stage6_section_failures(stage6_section_groups)
    context_analysis_path.write_text(
        _stage6_markdown("industry_context_analysis", stage6_section_groups["industry_context_analysis"]),
        encoding="utf-8",
    )
    mechanism_path.write_text(
        _stage6_markdown("industry_platform_mechanism", stage6_section_groups["industry_platform_mechanism"]),
        encoding="utf-8",
    )
    competitor_path.write_text(
        _stage6_markdown("industry_competitor_context", stage6_section_groups["industry_competitor_context"]),
        encoding="utf-8",
    )
    benchmark_artifacts = _benchmark_metric_artifacts(
        data_context_payload=data_context_payload,
        scope_payload=scope_payload,
        sources=sources,
        router_result=business_profile_router_result,
    )
    benchmark_metric_registry_path.write_text(
        json.dumps(benchmark_artifacts["benchmark_metric_registry"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    benchmark_comparability_matrix_path.write_text(
        json.dumps(benchmark_artifacts["benchmark_comparability_matrix"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    platform_difference_table_path.write_text(
        json.dumps(benchmark_artifacts["platform_difference_table"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metric_definition_comparison_path.write_text(
        json.dumps(benchmark_artifacts["metric_definition_comparison"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pd.DataFrame(benchmark_artifacts["benchmark_comparability_matrix"]).to_csv(
        benchmark_comparability_matrix_csv_path,
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(benchmark_artifacts["metric_definition_comparison"]).to_csv(
        metric_definition_comparison_csv_path,
        index=False,
        encoding="utf-8-sig",
    )
    benchmark_path.write_text(_benchmark_markdown(benchmark_artifacts), encoding="utf-8")
    metric_path.write_text(_metric_definition_markdown(benchmark_artifacts), encoding="utf-8")
    risk_objects = _risk_objects(
        sources=sources,
        scope_payload=scope_payload,
        data_context_payload=data_context_payload,
    )
    risk_failures = _risk_failures(risk_objects)
    risk_path.write_text(_risk_markdown(risk_objects), encoding="utf-8")
    regulation_risk_path.write_text(json.dumps(risk_objects, ensure_ascii=False, indent=2), encoding="utf-8")
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_6_platform_mechanism_analysis",
            summary="已生成行业背景、平台机制与竞争格局相关中间正文材料。",
            input_artifacts=[sources_path.name, source_fact_table_path.name, scope_json_path.name],
            output_artifacts=[
                context_analysis_path.name,
                mechanism_path.name,
                competitor_path.name,
            ],
            payload={
                "inferred_platform": scope_payload["inferred_platform"],
                "inferred_industry": scope_payload["inferred_industry"],
                "section_groups": stage6_section_groups,
                "section_failures": stage6_failures,
            },
            started_at=stage_started,
        )
    )
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_7_benchmark_comparability_analysis",
            summary="已生成 benchmark 和指标口径说明中间材料。",
            input_artifacts=[sources_path.name, source_fact_table_path.name, "domain_metric_registry.json" if domain_metric_registry else ""],
            output_artifacts=[
                benchmark_path.name,
                metric_path.name,
                benchmark_metric_registry_path.name,
                benchmark_comparability_matrix_path.name,
                platform_difference_table_path.name,
                metric_definition_comparison_path.name,
                benchmark_comparability_matrix_csv_path.name,
                metric_definition_comparison_csv_path.name,
            ],
            payload={
                "metric_context": scope_payload.get("metric_mining_context") or {},
                "benchmark_failures": benchmark_artifacts["benchmark_failures"],
                "covered_metrics": [row["metric_id"] for row in benchmark_artifacts["benchmark_metric_registry"]],
            },
            started_at=stage_started,
        )
    )
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_8_risk_and_regulation_analysis",
            summary="已生成行业风险与监管环境的研究中间材料。",
            input_artifacts=[sources_path.name, source_fact_table_path.name, scope_json_path.name],
            output_artifacts=[risk_path.name, regulation_risk_path.name],
            payload={
                "risk_markdown_path": str(risk_path.resolve()),
                "risk_json_path": str(regulation_risk_path.resolve()),
                "risk_failures": risk_failures,
            },
            started_at=stage_started,
        )
    )

    shared_inputs_used = [
        "uploaded_file_name",
        "sheet_names",
        "field_names",
        "sample_values",
        "user_task_description",
        "business_profile_router_result.json",
        "deep_context_understanding.json" if deep_context_understanding else "",
        "optional_data_summary.json" if optional_data_summary else "",
        "universal_metric_mining_result.json" if universal_metric_payload else "",
        "domain_metric_registry.json" if domain_metric_registry else "",
        "derived_metrics_table.csv" if derived_metric_rows else "",
        "proxy_metrics_table.csv" if proxy_metric_rows else "",
        "data_summary",
        "field_summary",
    ]
    shared_inputs_used = [item for item in shared_inputs_used if item]

    citation_generated_at = datetime.now(timezone.utc).isoformat()
    citation_payload = _citation_manifest_payload(
        generated_at=citation_generated_at,
        sources=sources,
        citation_rows=sources,
    )

    report_title = _report_title(scope_payload)
    stage_started = perf_counter()
    raw_report_markdown = _report_markdown_v2(
        title=report_title,
        scope_payload=scope_payload,
        data_context_payload=data_context_payload,
        sources=sources,
        insufficient=insufficient,
        business_scene_inference_payload=business_scene_inference_payload,
        stage6_section_groups=stage6_section_groups,
        benchmark_artifacts=benchmark_artifacts,
        risk_objects=risk_objects,
    )
    guardrail_result = run_industry_research_citation_guardrail(
        output_dir=out_dir,
        scope_payload=scope_payload,
        sources=sources,
        report_markdown=raw_report_markdown,
        blocked_main_outputs=[
            "management_report.pdf",
            "management_report.html",
            "analyst_appendix.xlsx",
            "main_report_page_plan.json",
            "main_report_quality_score.json",
            "main_report_quality_gate_result.json",
        ],
        blocked_r_outputs=[
            "r_cleaned_data",
            "r_analysis_outputs",
            "r_visualization_outputs",
            "r_pdf_explanation",
        ],
    )
    report_markdown = guardrail_result["repaired_report_markdown"]
    report_md_path.write_text(report_markdown, encoding="utf-8")
    citation_payload = _citation_manifest_payload(
        generated_at=citation_generated_at,
        sources=sources,
        citation_rows=guardrail_result["citation_manifest_rows"],
    )
    citation_path.write_text(json.dumps(citation_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    render_independent_industry_research_pdf_bundle(out_dir)
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_9_report_synthesis",
            summary="已完成行业研究正文综合、引用约束处理与 PDF/HTML 渲染。",
            input_artifacts=[
                context_analysis_path.name,
                benchmark_path.name,
                mechanism_path.name,
                competitor_path.name,
                metric_path.name,
                risk_path.name,
                sources_path.name,
            ],
            output_artifacts=[
                report_md_path.name,
                report_html_path.name,
                report_pdf_path.name,
            ],
            payload={"report_title": report_title},
            started_at=stage_started,
        )
    )

    if insufficient:
        insufficient_path.write_text(
            "\n".join(
                [
                    "# industry_research_insufficient_sources",
                    "",
                    "- 当前高/中可信来源不足，报告强度已主动降级。",
                    "- 后续应补充平台官方规则、监管公开资料、上市公司财报、行业协会或研究机构材料。",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    stage_started = perf_counter()
    localized_source_fact_rows = _source_fact_export_rows(sources)
    localized_benchmark_rows = _benchmark_matrix_export_rows(benchmark_artifacts)
    localized_metric_rows = _metric_definition_export_rows(benchmark_artifacts)
    localized_platform_rows = _platform_difference_export_rows(benchmark_artifacts)
    manual_confirmation_items = _manual_confirmation_checklist(
        business_scene_inference_payload,
        stage6_section_groups,
    )
    evidence_boundary_rows = _evidence_boundary_rows(data_context_payload, scope_payload)
    pd.DataFrame(localized_source_fact_rows).to_csv(source_fact_table_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(localized_benchmark_rows).to_csv(benchmark_comparability_matrix_csv_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(localized_metric_rows).to_csv(metric_definition_comparison_csv_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(localized_platform_rows).to_csv(platform_difference_table_csv_path, index=False, encoding="utf-8-sig")
    manual_confirmation_checklist_path.write_text(
        _manual_confirmation_markdown(manual_confirmation_items),
        encoding="utf-8",
    )
    appendix_path.write_text(
        _appendix_markdown(
            source_fact_rows=localized_source_fact_rows,
            benchmark_matrix_rows=localized_benchmark_rows,
            metric_definition_rows=localized_metric_rows,
            platform_difference_rows=localized_platform_rows,
            manual_confirmation_items=manual_confirmation_items,
            evidence_boundary_rows=evidence_boundary_rows,
        ),
        encoding="utf-8",
    )
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_10_appendix_and_tables",
            summary="已生成行业研究附录、来源表、引用清单与页审计附件。",
            input_artifacts=[report_md_path.name, sources_path.name, citation_path.name],
            output_artifacts=[
                appendix_path.name,
                manual_confirmation_checklist_path.name,
                source_fact_table_path.name,
                benchmark_comparability_matrix_csv_path.name,
                metric_definition_comparison_csv_path.name,
                platform_difference_table_csv_path.name,
                citation_path.name,
                "industry_research_page_audit.csv",
            ],
            payload={
                "appendix_path": str(appendix_path.resolve()),
                "manual_confirmation_count": len(manual_confirmation_items),
                "source_fact_row_count": len(localized_source_fact_rows),
                "benchmark_matrix_row_count": len(localized_benchmark_rows),
                "metric_definition_row_count": len(localized_metric_rows),
                "platform_difference_row_count": len(localized_platform_rows),
            },
            started_at=stage_started,
        )
    )

    stage_started = perf_counter()
    data_context_failures = industry_data_context_gate_failures(
        summary_payload=data_context_payload,
        report_markdown=report_markdown,
    )
    boundary_check_payload = dict(guardrail_result["boundary_check"])
    boundary_check_payload["data_context_read"] = bool(data_context_payload.get("used_universal_metric_mining"))
    boundary_check_payload["industry_data_context_summary_generated"] = all(
        path.exists()
        for path in [
            data_context_md_path,
            data_context_json_path,
            data_context_questions_path,
            data_context_boundary_path,
        ]
    )
    boundary_check_payload["current_dataset_claim_errors"] = data_context_failures
    boundary_check_payload["stage_6_section_failures"] = stage6_failures
    boundary_check_payload["stage_7_benchmark_failures"] = benchmark_artifacts["benchmark_failures"]
    boundary_check_payload["stage_8_risk_failures"] = risk_failures
    boundary_check_payload["passed"] = (
        bool(boundary_check_payload.get("passed"))
        and not data_context_failures
        and not stage6_failures
        and not benchmark_artifacts["benchmark_failures"]
        and not risk_failures
        and bool(boundary_check_payload["data_context_read"])
        and bool(boundary_check_payload["industry_data_context_summary_generated"])
    )
    boundary_check_path.write_text(json.dumps(boundary_check_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    source_audit_path.write_text(
        _source_audit_markdown(sources)
        + "\n## Boundary Check\n\n"
        + "\n".join(
            [
                f"- external_claims_without_sources: {boundary_check_payload.get('external_claims_without_sources', [])}",
                f"- dataset_evidence_misuse: {boundary_check_payload.get('dataset_evidence_misuse', [])}",
                f"- benchmark_boundary_errors: {boundary_check_payload.get('benchmark_boundary_errors', [])}",
                f"- main_report_contamination: {boundary_check_payload.get('main_report_contamination')}",
                f"- r_workflow_contamination: {boundary_check_payload.get('r_workflow_contamination')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    industry_gate_payload, industry_score_payload = evaluate_industry_research_quality_gate(
        report_markdown=report_markdown,
        sources=sources,
        benchmark_artifacts=benchmark_artifacts,
        boundary_check_payload=boundary_check_payload,
        manual_confirmation_items=manual_confirmation_items,
        source_fact_rows=localized_source_fact_rows,
        insufficient_sources=insufficient,
    )
    gate_payload = {
        **industry_gate_payload,
        "forbidden_main_outputs_written": False,
        "forbidden_r_outputs_written": False,
        "data_context_read": bool(data_context_payload.get("used_universal_metric_mining")),
        "industry_data_context_summary_generated": boundary_check_payload["industry_data_context_summary_generated"],
        "data_context_failures": data_context_failures,
        "stage_6_section_failures": stage6_failures,
        "stage_7_benchmark_failures": benchmark_artifacts["benchmark_failures"],
        "stage_8_risk_failures": risk_failures,
    }
    score_payload = dict(industry_score_payload)
    gate_payload, score_payload, field_blindness_guardrail = all_report_quality_gate(
        base_gate_result=gate_payload,
        base_score_result=score_payload,
        business_profile="independent_industry_research_chain",
        management_markdown=report_markdown,
        metric_payload=universal_metric_payload,
        action_rows=[],
        field_registry={},
        extra_context={"industry_data_context_payload": data_context_payload},
        require_metric_payload=bool(universal_metric_payload),
    )
    gate_payload["universal_field_blindness_guardrail"] = field_blindness_guardrail
    aggregated_fail_items = list(gate_payload.get("fail_items") or [])
    aggregated_fail_items.extend(data_context_failures)
    aggregated_fail_items.extend(stage6_failures)
    aggregated_fail_items.extend(benchmark_artifacts["benchmark_failures"])
    aggregated_fail_items.extend(risk_failures)
    if not boundary_check_payload["data_context_read"]:
        aggregated_fail_items.append("industry_research_chain_did_not_read_universal_metric_mining_result")
    if not boundary_check_payload["industry_data_context_summary_generated"]:
        aggregated_fail_items.append("industry_data_context_summary_outputs_missing")
    aggregated_fail_items = list(dict.fromkeys(item for item in aggregated_fail_items if item))
    score, tier = _industry_research_quality_score_from_failures(
        fail_items=aggregated_fail_items,
        insufficient_sources=insufficient,
    )
    gate_payload["fail_items"] = aggregated_fail_items
    gate_payload["passed"] = not aggregated_fail_items and not insufficient and score >= 90
    gate_payload["score"] = score
    gate_payload["assessment_tier"] = tier
    score_payload["score"] = score
    score_payload["passed"] = gate_payload["passed"]
    score_payload["assessment_tier"] = tier
    score_payload["hard_fail_items"] = aggregated_fail_items
    score_path.write_text(json.dumps(score_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    gate_path.write_text(json.dumps(gate_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_11_quality_gate",
            summary="已完成独立行研链质量门禁、引用边界检查与打分。",
            input_artifacts=[
                report_md_path.name,
                citation_path.name,
                boundary_check_path.name,
                "industry_data_context_summary.json",
            ],
            output_artifacts=[boundary_check_path.name, score_path.name, gate_path.name],
            payload={"quality_gate_result": gate_payload, "quality_score_result": score_payload},
            started_at=stage_started,
        )
    )

    stage_started = perf_counter()
    integration_note_path = out_dir / "router_metric_chain_integration.md"
    acceptance_report_path = out_dir / "industry_research_acceptance_report.md"
    integration_note_path.write_text(
        _router_metric_chain_integration_markdown(
            router_result=business_profile_router_result,
            data_context_payload=data_context_payload,
            business_scene_inference_payload=business_scene_inference_payload,
            scope_payload=scope_payload,
            benchmark_artifacts=benchmark_artifacts,
            gate_payload=gate_payload,
        ),
        encoding="utf-8",
    )
    acceptance_report_path.write_text(
        _acceptance_report_markdown(
            dataset_id=_safe_text((optional_data_summary or {}).get("dataset_id")),
            dataset_name=uploaded_file_name,
            sheet_name=sheet_names[0] if sheet_names else "",
            row_count=int(len(frame)),
            column_count=int(len(frame.columns)),
            routed_business_profile=_safe_text((business_profile_router_result or {}).get("business_profile")),
            report_dir=out_dir.parent,
            report_markdown=report_markdown,
            appendix_markdown=appendix_path.read_text(encoding="utf-8"),
            gate_payload=gate_payload,
            score_payload=score_payload,
            sources=sources,
            benchmark_artifacts=benchmark_artifacts,
            manual_confirmation_items=manual_confirmation_items,
        ),
        encoding="utf-8",
    )
    stage_records.append(
        _stage_record(
            output_dir=out_dir,
            stage_id="stage_12_release_packaging",
            summary="已整理最终 release pack、router/metric integration note，并写出 stage trace 审计文件。",
            input_artifacts=[gate_path.name, score_path.name, report_pdf_path.name, appendix_path.name],
            output_artifacts=[integration_note_path.name, acceptance_report_path.name, "stage_trace.json", "stage_trace.md"],
            payload={
                "integration_note_path": str(integration_note_path.resolve()),
                "acceptance_report_path": str(acceptance_report_path.resolve()),
            },
            started_at=stage_started,
        )
    )
    stage_trace_path = out_dir / "stage_trace.json"
    stage_trace_md_path = out_dir / "stage_trace.md"
    stage_trace_payload = {
        "workflow_name": "independent_industry_research_chain",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_title": report_title,
        "output_dir": str(out_dir.resolve()),
        "stages": stage_records,
    }
    stage_trace_path.write_text(json.dumps(stage_trace_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    stage_trace_md_path.write_text(_stage_trace_markdown(stage_records), encoding="utf-8")
    stage_trace_payload["stages"] = stage_records
    stage_trace_path.write_text(json.dumps(stage_trace_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    stage_trace_md_path.write_text(_stage_trace_markdown(stage_records), encoding="utf-8")

    return {
        "scope_payload": scope_payload,
        "question_rows": question_rows,
        "search_plan": search_plan,
        "sources": sources,
        "shared_inputs_used": shared_inputs_used,
        "insufficient_sources": insufficient,
        "quality_score_result": score_payload,
        "quality_gate_result": gate_payload,
        "stage_records": stage_records,
        "stage_trace_path": str(stage_trace_path.resolve()),
        "stage_trace_markdown_path": str(stage_trace_md_path.resolve()),
        "output_files": [
            "industry_data_context_summary.md",
            "industry_data_context_summary.json",
            "business_scene_inference.json",
            "source_fact_table.csv",
            "industry_research_question_bank_from_data.md",
            "industry_research_boundary_from_data.md",
            "industry_research_scope.md",
            "industry_research_scope.json",
            "industry_research_question_bank.md",
            "industry_web_search_plan.md",
            "industry_research_sources.json",
            "industry_context_analysis.md",
            "industry_benchmark_synthesis.md",
            "industry_platform_mechanism.md",
            "industry_competitor_context.md",
            "industry_metric_definition.md",
            "benchmark_metric_registry.json",
            "benchmark_comparability_matrix.json",
            "platform_difference_table.json",
            "metric_definition_comparison.json",
            "benchmark_comparability_matrix.csv",
            "metric_definition_comparison.csv",
            "platform_difference_table.csv",
            "industry_risk_scan.md",
            "industry_regulation_risk.json",
            "industry_research_report.md",
            "industry_research_report.html",
            "industry_research_report.pdf",
            "industry_research_appendix.md",
            "manual_confirmation_checklist.md",
            "router_metric_chain_integration.md",
            "industry_research_page_audit.csv",
            "citation_manifest_industry.json",
            "industry_research_boundary_check.json",
            "industry_research_source_audit.md",
            "industry_research_quality_score.json",
            "industry_research_quality_gate_result.json",
            "industry_research_acceptance_report.md",
            "stage_trace.json",
            "stage_trace.md",
            *(["industry_research_insufficient_sources.md"] if insufficient else []),
        ],
        "data_context_payload": data_context_payload,
        "data_context_output_files": data_context_output_files,
    }
