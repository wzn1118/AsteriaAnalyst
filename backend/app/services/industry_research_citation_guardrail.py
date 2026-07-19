from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_USAGE_TYPES = {
    "industry_background",
    "market_structure",
    "platform_mechanism",
    "competitor_context",
    "consumer_trend",
    "metric_definition",
    "benchmark_reference",
    "policy_or_regulation",
    "external_risk",
    "management_reference",
}

FORBIDDEN_USAGE_TYPES = {
    "dataset_evidence",
    "current_performance_evidence",
    "object_level_decision_evidence",
    "current_sales_evidence",
    "current_user_behavior_evidence",
}

CLAIM_BLUEPRINT = [
    ("CLM-001", 4, "行业背景", "industry_background"),
    ("CLM-002", 5, "市场结构", "market_structure"),
    ("CLM-003", 6, "产业链与价值链", "market_structure"),
    ("CLM-004", 7, "平台机制或渠道机制", "platform_mechanism"),
    ("CLM-005", 8, "竞争格局", "competitor_context"),
    ("CLM-006", 9, "用户/消费者趋势", "consumer_trend"),
    ("CLM-007", 10, "商品/服务供给结构", "market_structure"),
    ("CLM-008", 11, "成本、利润与商业模式", "management_reference"),
    ("CLM-009", 12, "指标口径说明", "metric_definition"),
    ("CLM-010", 13, "benchmark 与可比性限制", "benchmark_reference"),
    ("CLM-011", 14, "外部风险与监管环境", "policy_or_regulation"),
    ("CLM-012", 15, "对主报告可提供的背景启发", "management_reference"),
]


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _credibility_rank(level: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(_safe_text(level).lower(), 0)


def _source_matches_usage(source: dict[str, Any], usage_type: str) -> int:
    source_type = _safe_text(source.get("source_type"))
    usable_for = " ".join(_safe_text(item) for item in source.get("usable_for", []))
    score = _credibility_rank(_safe_text(source.get("credibility_level")))
    if usage_type == "platform_mechanism":
        if "官方平台规则" in source_type:
            score += 10
        if "平台机制" in usable_for or "规则" in usable_for:
            score += 6
    elif usage_type in {"policy_or_regulation", "external_risk"}:
        if "政府" in source_type or "监管" in source_type:
            score += 10
        if "风险与监管" in usable_for:
            score += 6
    elif usage_type == "benchmark_reference":
        if any(token in source_type for token in ["行业协会", "研究机构", "上市公司财报", "政府", "监管"]):
            score += 8
    elif usage_type == "metric_definition":
        if "规则" in source_type or "财报" in source_type:
            score += 6
    elif usage_type == "competitor_context":
        if any(token in source_type for token in ["上市公司财报", "行业协会", "研究机构"]):
            score += 8
    elif usage_type == "consumer_trend":
        if any(token in source_type for token in ["政府", "行业协会", "研究机构"]):
            score += 8
    elif usage_type == "management_reference":
        score += 2
    else:
        if "行业背景" in usable_for or "市场结构" in usable_for:
            score += 4
    return score


def _pick_source(usage_type: str, sources: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = sorted(
        sources,
        key=lambda source: (
            _source_matches_usage(source, usage_type),
            _credibility_rank(_safe_text(source.get("credibility_level"))),
        ),
        reverse=True,
    )
    return ranked[0] if ranked else None


def _claim_text(section_title: str, scope_payload: dict[str, Any]) -> str:
    mapping = {
        "行业背景": f"{scope_payload['inferred_industry']} 的行业背景与经营语境需要结合外部来源理解，不能只凭当前上传数据推断。",
        "市场结构": "市场结构应从商品、类目、店铺、品牌、供应商和交易结构等切片理解，而不是直接把当前数据当成全市场。",
        "产业链与价值链": f"当前业务位于 `{scope_payload['value_chain_position']}`，价值链解释只服务行业理解，不替代经营拍板。",
        "平台机制或渠道机制": f"{scope_payload['inferred_platform']} 的规则、流量、评价、履约和售后机制会影响经营理解。",
        "竞争格局": "竞争格局只能作为外部参考框架，不得伪装成当前数据已经验证的事实。",
        "用户/消费者趋势": "消费者趋势只能作为背景理解与问题提示，不能直接证明当前经营对象表现。",
        "商品/服务供给结构": "供给结构研究应服务行业背景和供给侧理解，不得直接生成当前对象决策。",
        "成本、利润与商业模式": f"当前商业模式 `{scope_payload['inferred_business_model']}` 需要外部资料辅助解释，但不得替代上传数据口径。",
        "指标口径说明": "GMV、销量、转化、履约、评价与利润等指标需要先统一定义与口径边界。",
        "benchmark 与可比性限制": "benchmark 只能用于参考，必须写明口径限制、平台差异、样本边界和时间区间。",
        "外部风险与监管环境": "监管、平台规则和消费者权益环境只能用于风险背景说明，不能替代当前数据证据。",
        "对主报告可提供的背景启发": "外部资料可作为后续分析问题和背景启发，不得直接改变主报告质量评分与对象动作。",
    }
    return mapping.get(section_title, "外部资料只能作为行业研究背景，不得替代当前数据分析证据。")


def _repair_report_text(report_markdown: str) -> tuple[str, list[str], list[str]]:
    repaired = str(report_markdown or "")
    repairs: list[str] = []
    strong_conclusion_hits: list[str] = []

    replacements = {
        "当前数据证明": "可作为后续分析问题：",
        "当前数据表明": "可作为后续分析问题：",
        "当前数据说明": "可作为后续分析问题：",
        "当前数据支持加码": "可作为后续分析问题：是否值得进一步验证",
    }
    for src, dst in replacements.items():
        if src in repaired:
            strong_conclusion_hits.append(src)
            repaired = repaired.replace(src, dst)
            repairs.append(f"replace:{src}->{dst}")

    if "benchmark 与可比性限制" in repaired and "口径限制" not in repaired and "不可比" not in repaired:
        repaired = repaired.replace(
            "## 13. benchmark 与可比性限制",
            "## 13. benchmark 与可比性限制\n\n- benchmark 直接比较前必须补口径限制、不可比说明、时间区间与平台差异。",
        )
        repairs.append("append_benchmark_boundary_note")

    return repaired, strong_conclusion_hits, repairs


def run_industry_research_citation_guardrail(
    *,
    output_dir: str | Path,
    scope_payload: dict[str, Any],
    sources: list[dict[str, Any]],
    report_markdown: str,
    blocked_main_outputs: list[str],
    blocked_r_outputs: list[str],
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    repaired_markdown, strong_conclusion_hits, repairs = _repair_report_text(report_markdown)

    claim_rows: list[dict[str, Any]] = []
    external_claims_without_sources: list[str] = []
    dataset_evidence_misuse: list[str] = []
    benchmark_boundary_errors: list[str] = []
    low_credibility_support: list[str] = []

    for claim_id, used_in_page, section_title, usage_type in CLAIM_BLUEPRINT:
        claim_text = _claim_text(section_title, scope_payload)
        source = _pick_source(usage_type, sources)
        if usage_type in FORBIDDEN_USAGE_TYPES:
            dataset_evidence_misuse.append(f"{claim_id}:{usage_type}")
            continue
        if usage_type == "benchmark_reference" and not any(
            token in repaired_markdown for token in ["口径限制", "不可比", "benchmark 边界"]
        ):
            benchmark_boundary_errors.append(claim_id)
        if source is None:
            external_claims_without_sources.append(claim_id)
            repairs.append(f"remove_claim:{claim_id}")
            continue
        credibility = _safe_text(source.get("credibility_level"))
        final_usage_type = usage_type
        final_claim_text = claim_text
        if credibility == "low" and usage_type in {
            "industry_background",
            "market_structure",
            "platform_mechanism",
            "competitor_context",
            "metric_definition",
            "benchmark_reference",
            "policy_or_regulation",
            "external_risk",
        }:
            low_credibility_support.append(claim_id)
            final_usage_type = "management_reference"
            final_claim_text = f"背景线索：{claim_text}"
            repairs.append(f"downgrade_low_credibility_claim:{claim_id}")
        claim_rows.append(
            {
                "claim_id": claim_id,
                "claim_text": final_claim_text,
                "source_id": _safe_text(source.get("source_id")),
                "source_title": _safe_text(source.get("title")),
                "publisher": _safe_text(source.get("publisher")),
                "publish_date": _safe_text(source.get("publish_date")),
                "credibility_level": credibility,
                "used_in_page": used_in_page,
                "used_in_section": section_title,
                "usage_type": final_usage_type,
                "limitation": _safe_text(source.get("limitation")),
            }
        )

    main_report_contamination = any((out_dir / name).exists() for name in blocked_main_outputs)
    r_workflow_contamination = any((out_dir / name).exists() for name in blocked_r_outputs) or any(
        name in repaired_markdown for name in blocked_r_outputs
    )

    boundary_check = {
        "passed": not (
            external_claims_without_sources
            or dataset_evidence_misuse
            or benchmark_boundary_errors
            or low_credibility_support
            or strong_conclusion_hits
            or main_report_contamination
            or r_workflow_contamination
        ),
        "external_claims_without_sources": external_claims_without_sources,
        "dataset_evidence_misuse": dataset_evidence_misuse,
        "benchmark_boundary_errors": benchmark_boundary_errors,
        "main_report_contamination": main_report_contamination,
        "r_workflow_contamination": r_workflow_contamination,
        "strong_current_data_conclusions": strong_conclusion_hits,
        "repairs": repairs,
    }

    citation_manifest_path = out_dir / "citation_manifest_industry.json"
    boundary_check_path = out_dir / "industry_research_boundary_check.json"
    source_audit_path = out_dir / "industry_research_source_audit.md"
    citation_manifest_path.write_text(json.dumps(claim_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    boundary_check_path.write_text(json.dumps(boundary_check, ensure_ascii=False, indent=2), encoding="utf-8")

    audit_lines = [
        "# industry_research_source_audit",
        "",
        "## Source Audit",
        "",
    ]
    for source in sources:
        audit_lines.extend(
            [
                f"### {source.get('source_id', '')} {source.get('title', '')}",
                "",
                f"- publisher: {source.get('publisher', '')}",
                f"- credibility_level: {source.get('credibility_level', '')}",
                f"- source_type: {source.get('source_type', '')}",
                f"- usable_for: {', '.join(source.get('usable_for', []))}",
                f"- not_usable_for: {', '.join(source.get('not_usable_for', []))}",
                f"- limitation: {source.get('limitation', '')}",
                "",
            ]
        )
    audit_lines.extend(
        [
            "## Boundary Check",
            "",
            f"- external_claims_without_sources: {external_claims_without_sources}",
            f"- dataset_evidence_misuse: {dataset_evidence_misuse}",
            f"- benchmark_boundary_errors: {benchmark_boundary_errors}",
            f"- main_report_contamination: {main_report_contamination}",
            f"- r_workflow_contamination: {r_workflow_contamination}",
            f"- strong_current_data_conclusions: {strong_conclusion_hits}",
            "",
            "## Repairs",
            "",
            *([f"- {item}" for item in repairs] or ["- none"]),
        ]
    )
    source_audit_path.write_text("\n".join(audit_lines).strip() + "\n", encoding="utf-8")

    return {
        "citation_manifest_path": str(citation_manifest_path.resolve()),
        "boundary_check_path": str(boundary_check_path.resolve()),
        "source_audit_path": str(source_audit_path.resolve()),
        "citation_manifest_rows": claim_rows,
        "boundary_check": boundary_check,
        "repaired_report_markdown": repaired_markdown,
    }
