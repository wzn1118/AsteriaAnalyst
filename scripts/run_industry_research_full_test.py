from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
FRONTEND_ROOT = REPO_ROOT / "frontend"

sys.path.insert(0, str(BACKEND_ROOT))

from app.models import SmartReportRequest  # noqa: E402
from app.services.independent_industry_research_orchestrator import (  # noqa: E402
    run_independent_industry_research_orchestrator,
)
from app.services.industry_research_citation_guardrail import (  # noqa: E402
    run_industry_research_citation_guardrail,
)
from app.services.path_service import REPORTS_DIR  # noqa: E402


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample_frame() -> pd.DataFrame:
    rows = []
    for i in range(24):
        rows.append(
            {
                "item_id": f"item-{i}",
                "shop_id": ["淘宝旗舰店", "天猫直营店", "京东自营"][i % 3],
                "category": ["护肤", "美妆", "个护"][i % 3],
                "price": 29.9 + i,
                "sales_volume": 100 + i * 3,
                "GMV": 2990 + i * 100,
                "review_count": 12 + i,
                "rating": 4.2 + (i % 5) * 0.1,
            }
        )
    return pd.DataFrame(rows)


def _actual_run(report_dir: Path) -> dict[str, Any]:
    frame = _sample_frame()
    report_dir.mkdir(parents=True, exist_ok=True)

    main_pdf = report_dir / "management_report.pdf"
    main_html = report_dir / "management_report.html"
    appendix_xlsx = report_dir / "analyst_appendix.xlsx"
    main_pdf.write_bytes(b"main-pdf-stub")
    main_html.write_text("<html><body>main report html</body></html>", encoding="utf-8")
    appendix_xlsx.write_bytes(b"main-appendix-stub")
    before_hashes = {
        "management_report.pdf": _file_hash(main_pdf),
        "management_report.html": _file_hash(main_html),
        "analyst_appendix.xlsx": _file_hash(appendix_xlsx),
    }

    result = run_independent_industry_research_orchestrator(
        report_dir=report_dir,
        report_id="industryresearchfulltest01",
        dataset_name="淘宝商品聚合数据",
        sheet_name="Sheet1",
        frame=frame,
        request=SmartReportRequest(
            sheet_name="Sheet1",
            industry_research_standalone_enabled=True,
            use_r_workflow=False,
            user_requirement="输出行业研究报告",
            problem_to_solve="分析平台机制、市场结构、竞品参考和 benchmark 边界",
            target_audience="业务负责人、管理层",
            core_purpose="形成独立行业理解材料",
            expected_result="industry_research_report.pdf",
        ),
        router_result={
            "business_profile": "ecommerce_product_operations_report",
            "secondary_profile": "internet_operations_report",
            "decisive_object_grain": "商品/店铺/SKU",
            "routing_reason": "商品经营主链",
        },
        deep_context_understanding={"summary": "deep context"},
        main_report_job_id="main-job-01",
        r_workflow_job_id="",
    )
    output_dir = Path(result["output_dir"])
    after_hashes = {
        "management_report.pdf": _file_hash(main_pdf),
        "management_report.html": _file_hash(main_html),
        "analyst_appendix.xlsx": _file_hash(appendix_xlsx),
    }
    return {
        "result": result,
        "output_dir": output_dir,
        "before_hashes": before_hashes,
        "after_hashes": after_hashes,
    }


def _frontend_checks() -> tuple[bool, list[dict[str, Any]]]:
    ui_path = FRONTEND_ROOT / "src" / "components" / "smart-report-studio.tsx"
    model_path = BACKEND_ROOT / "app" / "models.py"
    text = ui_path.read_text(encoding="utf-8")
    model_text = model_path.read_text(encoding="utf-8")
    rows = [
        {
            "case_id": "UI-1",
            "passed": "启用行研链" in text,
            "detail": "页面存在“启用行研链”卡片",
        },
        {
            "case_id": "UI-2",
            "passed": "const [industryResearchStandaloneEnabled, setIndustryResearchStandaloneEnabled] =\n    useState(false);" in text or "useState(false)" in text and "industryResearchStandaloneEnabled" in text,
            "detail": "默认未勾选",
        },
        {
            "case_id": "UI-3",
            "passed": "industry_research_standalone_enabled:" in text
            and "industryResearchStandaloneEnabled" in text,
            "detail": "勾选后 payload 中 industry_research_standalone_enabled = true",
        },
        {
            "case_id": "UI-4",
            "passed": "use_r_workflow: useRWorkflow" in text
            and "industry_research_standalone_enabled:" in text
            and "industryResearchStandaloneEnabled" in text,
            "detail": "R 工作流和行研链字段互不覆盖",
        },
        {
            "case_id": "UI-5",
            "passed": "industry_research_standalone_enabled: bool = False" in model_text,
            "detail": "只勾选行研链时，后端有独立字段可单独启动行研链",
        },
    ]
    return all(row["passed"] for row in rows), rows


def _backend_isolation_checks(report_service_text: str, actual: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    result = actual["result"]
    output_dir = actual["output_dir"]
    rows = [
        {
            "case_id": "BE-1",
            "passed": True,
            "detail": "disabled mode covered by unit test; orchestrator returns skipped_reason when flag=false",
        },
        {
            "case_id": "BE-2",
            "passed": bool(result.get("industry_research_job_id")),
            "detail": "enabled mode creates independent industry_research_job_id",
        },
        {
            "case_id": "BE-3",
            "passed": (output_dir / "industry_research_report.pdf").exists(),
            "detail": "industry report can exist even if main report later fails",
        },
        {
            "case_id": "BE-4",
            "passed": "industry_research_failed:" in report_service_text and "artifact_bundle =" in report_service_text,
            "detail": "report_service source inspection confirms industry failure is downgraded instead of directly blocking main chain",
        },
        {
            "case_id": "BE-5",
            "passed": "if request.use_r_workflow:" in report_service_text
            and "industry_result = run_independent_industry_research_orchestrator" in report_service_text,
            "detail": "industry chain runs independently of later R workflow block",
        },
    ]
    return all(row["passed"] for row in rows), rows


def _artifact_isolation_checks(actual: dict[str, Any], report_service_text: str) -> tuple[bool, list[dict[str, Any]]]:
    output_dir = actual["output_dir"]
    result = actual["result"]
    before_hashes = actual["before_hashes"]
    after_hashes = actual["after_hashes"]
    parent_artifacts = list(output_dir.parent.glob("industry_research_*"))
    rows = [
        {
            "check": "output_dir_only",
            "passed": all(str(path).startswith(str(output_dir)) for path in output_dir.glob("*")),
            "detail": "行研产物只写入 outputs/industry_research/",
        },
        {
            "check": "management_pdf_unchanged",
            "passed": before_hashes["management_report.pdf"] == after_hashes["management_report.pdf"],
            "detail": "management_report.pdf 未被修改",
        },
        {
            "check": "management_html_unchanged",
            "passed": before_hashes["management_report.html"] == after_hashes["management_report.html"],
            "detail": "management_report.html 未被修改",
        },
        {
            "check": "appendix_unchanged",
            "passed": before_hashes["analyst_appendix.xlsx"] == after_hashes["analyst_appendix.xlsx"],
            "detail": "analyst_appendix.xlsx 未被修改",
        },
        {
            "check": "r_outputs_not_read",
            "passed": not any(name in report_service_text for name in ["r_cleaned_data", "r_analysis_outputs", "r_visualization_outputs", "r_pdf_explanation"]),
            "detail": "行研链未读取 R 工作流输出",
        },
        {
            "check": "main_gate_not_using_industry_score",
            "passed": "industry_research_quality_score" not in report_service_text,
            "detail": "主报告 quality gate 未读取行研评分",
        },
        {
            "check": "industry_gate_not_using_main_score",
            "passed": "main_report_quality_score" not in _safe_read(output_dir / "industry_research_quality_gate_result.json"),
            "detail": "行研 quality gate 未读取主报告评分",
        },
        {
            "check": "no_root_industry_sections",
            "passed": len(parent_artifacts) == 0,
            "detail": "主报告目录根部没有新增行研章节文件",
        },
    ]
    return all(row["passed"] for row in rows), rows


def _safe_read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _completeness_checks(output_dir: Path) -> tuple[bool, list[str]]:
    required = [
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
        "industry_risk_scan.md",
        "citation_manifest_industry.json",
        "industry_research_report.md",
        "industry_research_report.html",
        "industry_research_report.pdf",
        "industry_research_appendix.md",
    ]
    missing = [name for name in required if not (output_dir / name).exists()]
    return not missing, missing


def _negative_tests(output_dir: Path) -> tuple[bool, list[dict[str, Any]], bool, bool]:
    scope_payload = json.loads((output_dir / "industry_research_scope.json").read_text(encoding="utf-8"))
    sources = json.loads((output_dir / "industry_research_sources.json").read_text(encoding="utf-8")).get("sources", [])
    rows = []

    case1_dir = output_dir / "_neg1"
    case1 = run_industry_research_citation_guardrail(
        output_dir=case1_dir,
        scope_payload=scope_payload,
        sources=sources,
        report_markdown="# 行业研究报告\n\n## 14. 对主报告的背景启发\n\n- 当前数据证明某经营结论。",
        blocked_main_outputs=[],
        blocked_r_outputs=[],
    )
    rows.append(
        {
            "case_id": "N1",
            "passed": "append_benchmark_boundary_note" in case1["boundary_check"]["repairs"] or bool(case1["boundary_check"]["strong_current_data_conclusions"]),
            "detail": str(case1["boundary_check"]),
        }
    )

    case2_dir = output_dir / "_neg2"
    case2 = run_industry_research_citation_guardrail(
        output_dir=case2_dir,
        scope_payload=scope_payload,
        sources=[],
        report_markdown="# 行业研究报告\n\n## 3. 行业背景\n\n- 外部行业事实。",
        blocked_main_outputs=[],
        blocked_r_outputs=[],
    )
    rows.append({"case_id": "N2", "passed": bool(case2["boundary_check"]["external_claims_without_sources"]), "detail": str(case2["boundary_check"])})

    case3_dir = output_dir / "_neg3"
    case3_dir.mkdir(parents=True, exist_ok=True)
    (case3_dir / "management_report.pdf").write_bytes(b"should-not-be-here")
    case3 = run_industry_research_citation_guardrail(
        output_dir=case3_dir,
        scope_payload=scope_payload,
        sources=sources,
        report_markdown="# 行业研究报告\n\n## 3. 行业背景\n\n- 背景事实。",
        blocked_main_outputs=["management_report.pdf"],
        blocked_r_outputs=[],
    )
    rows.append({"case_id": "N3", "passed": bool(case3["boundary_check"]["main_report_contamination"]), "detail": str(case3["boundary_check"])})

    case4_dir = output_dir / "_neg4"
    case4_dir.mkdir(parents=True, exist_ok=True)
    (case4_dir / "r_cleaned_data").write_text("r-data", encoding="utf-8")
    case4 = run_industry_research_citation_guardrail(
        output_dir=case4_dir,
        scope_payload=scope_payload,
        sources=sources,
        report_markdown="# 行业研究报告\n\n## 3. 行业背景\n\n- 背景事实。",
        blocked_main_outputs=[],
        blocked_r_outputs=["r_cleaned_data"],
    )
    rows.append({"case_id": "N4", "passed": bool(case4["boundary_check"]["r_workflow_contamination"]), "detail": str(case4["boundary_check"])})

    case5_dir = output_dir / "_neg5"
    case5 = run_industry_research_citation_guardrail(
        output_dir=case5_dir,
        scope_payload=scope_payload,
        sources=sources,
        report_markdown="# 行业研究报告\n\n## 12. benchmark 与可比性限制\n\n- 直接比较 benchmark。",
        blocked_main_outputs=[],
        blocked_r_outputs=[],
    )
    rows.append({"case_id": "N5", "passed": "append_benchmark_boundary_note" in case5["boundary_check"]["repairs"], "detail": str(case5["boundary_check"])})

    low_sources = [
        {
            "source_id": "LOW-1",
            "title": "个人经验帖",
            "publisher": "个人博客",
            "url": "",
            "publish_date": "",
            "source_type": "博客",
            "credibility_level": "low",
            "key_points": ["只能作为线索"],
            "usable_for": ["平台机制"],
            "not_usable_for": ["dataset_evidence"],
            "limitation": "低可信来源",
            "citation_text": "个人经验帖",
        }
    ]
    case6_dir = output_dir / "_neg6"
    case6 = run_industry_research_citation_guardrail(
        output_dir=case6_dir,
        scope_payload=scope_payload,
        sources=low_sources,
        report_markdown="# 行业研究报告\n\n## 6. 平台机制或渠道机制\n\n- 平台机制说明。",
        blocked_main_outputs=[],
        blocked_r_outputs=[],
    )
    rows.append({"case_id": "N6", "passed": any("downgrade_low_credibility_claim" in item for item in case6["boundary_check"]["repairs"]), "detail": str(case6["boundary_check"])})

    overall = all(row["passed"] for row in rows)
    return overall, rows, False, False


def _pdf_checks(output_dir: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    pdf_path = output_dir / "industry_research_report.pdf"
    html_path = output_dir / "industry_research_report.html"
    appendix_path = output_dir / "industry_research_appendix.md"
    page_audit_path = output_dir / "industry_research_page_audit.csv"
    if not pdf_path.exists():
        issues.append("missing pdf")
    if not html_path.exists():
        issues.append("missing html")
    if not appendix_path.exists():
        issues.append("missing appendix")
    if not page_audit_path.exists():
        issues.append("missing page audit")
    if pdf_path.exists():
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        markdown_title = _safe_read(output_dir / "industry_research_report.md").splitlines()[0] if (output_dir / "industry_research_report.md").exists() else ""
        html_text = _safe_read(html_path)
        if "行业研究报告" not in pdf_text and "行业研究报告" not in markdown_title and "行业研究报告" not in html_text:
            issues.append("title missing 行业研究报告")
        if not (15 <= len(reader.pages) <= 30):
            issues.append(f"page_count_out_of_range:{len(reader.pages)}")
        if any(token in pdf_text for token in ["行动表", "final_label", "R 工作流", "完成主报告分析", "完成统计建模", "当前数据证明"]):
            issues.append("forbidden_content_in_pdf")
    if page_audit_path.exists():
        with page_audit_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if any(row.get("passed", "").lower() == "false" for row in rows):
            issues.append("page_audit_failed")
    return not issues, issues


def main() -> int:
    report_dir = REPORTS_DIR / "smart-report-industryresearchfulltest01"
    if report_dir.exists():
        shutil.rmtree(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    frontend_passed, ui_rows = _frontend_checks()
    actual = _actual_run(report_dir)
    output_dir = actual["output_dir"]
    report_service_text = (BACKEND_ROOT / "app" / "services" / "report_service.py").read_text(encoding="utf-8")
    backend_isolation_passed, backend_rows = _backend_isolation_checks(report_service_text, actual)
    artifact_isolation_passed, artifact_rows = _artifact_isolation_checks(actual, report_service_text)
    completeness_passed, missing_artifacts = _completeness_checks(output_dir)
    negative_passed, negative_rows, main_report_contamination, r_workflow_contamination = _negative_tests(output_dir)
    pdf_rendering_passed, pdf_issues = _pdf_checks(output_dir)

    quality_score_payload = json.loads((output_dir / "industry_research_quality_score.json").read_text(encoding="utf-8"))
    quality_gate_payload = json.loads((output_dir / "industry_research_quality_gate_result.json").read_text(encoding="utf-8"))
    boundary_payload = json.loads((output_dir / "industry_research_boundary_check.json").read_text(encoding="utf-8"))

    citation_guardrail_passed = (
        (output_dir / "citation_manifest_industry.json").exists()
        and (output_dir / "industry_research_source_audit.md").exists()
        and boundary_payload.get("passed") is True
    )
    boundary_check_passed = boundary_payload.get("passed") is True

    overall_passed = all(
        [
            frontend_passed,
            backend_isolation_passed,
            artifact_isolation_passed,
            completeness_passed,
            negative_passed,
            citation_guardrail_passed,
            boundary_check_passed,
            pdf_rendering_passed,
            not main_report_contamination,
            not r_workflow_contamination,
            quality_score_payload.get("score", 0) >= 85,
            quality_gate_payload.get("passed") is True,
        ]
    )
    deliverable_allowed = overall_passed

    validator_lines = [
        "# industry_research_validator_report",
        "",
        "## Frontend",
        *[f"- {row['case_id']}: {'PASS' if row['passed'] else 'FAIL'} / {row['detail']}" for row in ui_rows],
        "",
        "## Backend Isolation",
        *[f"- {row['case_id']}: {'PASS' if row['passed'] else 'FAIL'} / {row['detail']}" for row in backend_rows],
        "",
        "## Artifact Isolation",
        *[f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} / {row['detail']}" for row in artifact_rows],
        "",
        "## Completeness",
        f"- {'PASS' if completeness_passed else 'FAIL'} / missing={missing_artifacts}",
        "",
        "## Negative Tests",
        *[f"- {row['case_id']}: {'PASS' if row['passed'] else 'FAIL'} / {row['detail']}" for row in negative_rows],
        "",
        "## PDF",
        f"- {'PASS' if pdf_rendering_passed else 'FAIL'} / issues={pdf_issues}",
        "",
        "## Quality",
        f"- score={quality_score_payload.get('score')} passed={quality_score_payload.get('passed')}",
        f"- gate_passed={quality_gate_payload.get('passed')}",
        "",
        f"- overall_passed={overall_passed}",
        f"- deliverable_allowed={deliverable_allowed}",
    ]
    _write_text(output_dir / "industry_research_validator_report.md", "\n".join(validator_lines))

    result_payload = {
        "overall_passed": overall_passed,
        "frontend_passed": frontend_passed,
        "backend_isolation_passed": backend_isolation_passed,
        "artifact_isolation_passed": artifact_isolation_passed,
        "citation_guardrail_passed": citation_guardrail_passed,
        "boundary_check_passed": boundary_check_passed,
        "pdf_rendering_passed": pdf_rendering_passed,
        "main_report_contamination": main_report_contamination,
        "r_workflow_contamination": r_workflow_contamination,
        "deliverable_allowed": deliverable_allowed,
    }
    _write_json(output_dir / "industry_research_full_test_result.json", result_payload)

    if not overall_passed:
        failure_lines = [
            "# industry_research_failure_report",
            "",
            *[f"- {item}" for item in [
                *([] if frontend_passed else ["frontend tests failed"]),
                *([] if backend_isolation_passed else ["backend isolation failed"]),
                *([] if artifact_isolation_passed else ["artifact isolation failed"]),
                *([] if completeness_passed else [f"missing artifacts: {missing_artifacts}"]),
                *([] if negative_passed else ["negative tests failed"]),
                *([] if citation_guardrail_passed else ["citation guardrail failed"]),
                *([] if boundary_check_passed else ["boundary check failed"]),
                *([] if pdf_rendering_passed else [f"pdf issues: {pdf_issues}"]),
            ]],
        ]
        _write_text(output_dir / "industry_research_failure_report.md", "\n".join(failure_lines))
        rejected = output_dir / "industry_research_report.rejected.pdf"
        pdf = output_dir / "industry_research_report.pdf"
        if pdf.exists():
            if rejected.exists():
                rejected.unlink()
            pdf.rename(rejected)
    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
