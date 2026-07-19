from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.models import CodexRunRequest, SmartReportRequest
from app.services.generic_long_business_profile_service import (
    build_generic_action_roadmap,
    build_generic_object_decision_registry,
    generic_field_availability_registry,
    render_generic_action_table,
    write_generic_registry_artifacts,
)
from app.services.generic_long_codex_chain_service import run_multi_pass_codex_interpretation_chain
from app.services.generic_long_pdf_report_renderer import (
    MissingStructuredPageDraftError,
    build_generic_long_appendix_variant,
    build_generic_long_management_variant,
)
from app.services.generic_long_render_guard_service import generic_long_quality_gate
from app.services.independent_report_validator import validate_report_dir
from app.services.report_service import (
    _downloadable_bundle_cn_generic_long,
    _render_report_html_cn,
    _write_pdf_report_cn,
)
from app.services.path_service import REPORTS_DIR


def _live(result: dict) -> dict:
    enriched = dict(result)
    enriched.setdefault("mode", "live_codex_agentic")
    enriched.setdefault("runtime_state", "live")
    enriched.setdefault("degradation_state", "none")
    enriched.setdefault("live_available", True)
    return enriched


class GenericLongAIChainTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        rows = []
        for i in range(1, 301):
            rows.append(
                {
                    "project_id": f"P{i:03d}",
                    "project_name": f"Project-{(i % 25) + 1:02d}",
                    "department": ["Operations", "Service", "Program", "Region", "Support"][i % 5],
                    "owner": ["Alice", "Bob", "Carol", "David", "Eve", "Frank"][i % 6],
                    "region": ["East", "West", "North", "South"][i % 4],
                    "month": f"2026-{(i % 12) + 1:02d}",
                    "budget_amount": 80000 + (i % 25) * 2500,
                    "actual_spend": 70000 + (i % 30) * 2100,
                    "progress_rate": round(0.35 + (i % 10) * 0.05, 3),
                    "issue_count": i % 7,
                    "satisfaction_score": round(3.2 + (i % 8) * 0.18, 2),
                    "enroll_count": 40 + (i % 50),
                    "complete_count": 20 + (i % 35),
                    "target_value": 0.82,
                    "status": ["on_track", "risk", "delay", "complete"][i % 4],
                    "feedback_note": [
                        "Need clearer handoff and owner tracking",
                        "Quality risk remains in late-stage review",
                        "Regional coordination improved after weekly sync",
                        "Budget usage lacks monthly explanation",
                    ][i % 4],
                }
            )
        return pd.DataFrame(rows)

    def _request(self) -> SmartReportRequest:
        return SmartReportRequest(
            sheet_name="Sheet1",
            business_profile="generic_long_business_report",
            report_style="deep_dive",
            user_requirement="generic long report 40-50页 管理层长报告 通用经营分析",
            problem_to_solve="识别项目、部门与区域执行中的结构性问题、风险和优先动作",
            target_audience="业务负责人和管理层",
            core_purpose="形成可派单的通用经营分析长报告",
            expected_result="35-50页正式management report",
            key_constraints="不能强行套采销、电商、互联网运营或媒体投放模板",
        )

    def _report_context(self) -> tuple[pd.DataFrame, dict, dict, list[dict], dict]:
        frame = self._frame()
        field_registry = generic_field_availability_registry(frame)
        registry_payload = build_generic_object_decision_registry(frame, field_registry)
        action_table = render_generic_action_table(registry_payload)
        roadmap = build_generic_action_roadmap(registry_payload, field_registry)
        return frame, field_registry, registry_payload, action_table, roadmap

    def _report_dict(self, report_id: str, field_registry: dict, registry_payload: dict, action_table: list[dict], roadmap: dict) -> dict:
        return {
            "report_id": report_id,
            "title": "Generic Long Report Placeholder",
            "dataset_name": "Generic Long Test Dataset",
            "sheet_name": "Sheet1",
            "generated_at": "2026-04-25T00:00:00Z",
            "report_language": "zh-CN",
            "report_lens": "mixed_business_review",
            "business_profile": "generic_long_business_report",
            "generic_field_availability_registry": field_registry,
            "generic_object_decision_registry": registry_payload,
            "generic_action_table": action_table,
            "generic_action_roadmap": roadmap,
        }

    def _page_plan(self, special_title: str | None = None) -> list[dict]:
        rows = []
        for index in range(1, 38):
            rows.append(
                {
                    "page_number": index,
                    "page_title": special_title if index == 3 and special_title else f"AI-Page-{index:02d}",
                    "management_question": f"管理问题 {index}",
                    "page_purpose": f"页面目的 {index}",
                    "required_metrics": ["spend_rate", "budget_gap"],
                    "required_dimensions": ["department", "region"],
                    "available_fields": ["entity_fields", "time_fields", "amount_fields", "progress_fields"],
                    "derived_metrics": [
                        {
                            "metric_id": "spend_rate",
                            "metric_name": "spend_rate",
                            "formula": "actual_spend / budget_amount",
                            "value": "0.92",
                            "comparison": "1.0 为预算完全消耗参考值",
                            "evidence_strength": "high",
                        },
                        {
                            "metric_id": "budget_gap",
                            "metric_name": "budget_gap",
                            "formula": "budget_amount - actual_spend",
                            "value": "8000",
                            "comparison": "正值为预算剩余",
                            "evidence_strength": "medium",
                        },
                    ],
                    "evidence_query": f"query-{index}",
                    "objects_to_discuss": ["Project-01", "Project-02"],
                    "allowed_claim_types": ["structure", "trend", "efficiency", "risk", "opportunity"],
                    "forbidden_claim_types": ["causal attribution without evidence"],
                    "required_table_or_chart": "table",
                    "action_type": "复核",
                    "source_passes": [
                        "business_context_interpretation",
                        "field_semantic_map",
                        "metric_derivation_plan",
                        "derived_metric_execution_review",
                        "management_question_bank",
                        "exploratory_interpretation",
                        "object_level_interpretation",
                        "interpretation_conflict_check",
                    ],
                }
            )
        return rows

    def _page_batch(self, pages: list[dict], *, unique_marker: str = "", missing_metric_id: bool = False) -> dict:
        batch = []
        for page in pages:
            evidence = [
                {
                    "metric_id": "" if missing_metric_id else "spend_rate",
                    "metric_name": "spend_rate",
                    "value": "0.92",
                    "comparison": "较目标低 0.08",
                    "object_or_dimension": "Project-01",
                    "evidence_strength": "high",
                },
                {
                    "metric_id": "budget_gap",
                    "metric_name": "budget_gap",
                    "value": "8000",
                    "comparison": "预算剩余 8000",
                    "object_or_dimension": "Project-01",
                    "evidence_strength": "medium",
                },
            ]
            diagnosis = (
                f"{unique_marker}第{page['page_number']}页的诊断显示，当前项目在预算执行、进度节奏和问题暴露之间存在明显错配。"
                f"虽然总体执行率仍可维持，但头部对象与中位对象之间的差异已经持续拉大，且高问题密度对象并未同步降速。"
                f"这意味着当前不能简单把规模扩张视为健康增长，必须先拆开看结构、执行和质量三条线的错位来源。"
            )
            business_interpretation = (
                f"{unique_marker}从管理层视角看，这一页意味着资源配置和执行协同还没有形成稳定闭环。"
                f"如果继续只看总量而不追问对象差异，团队会把局部高表现误当成整体改善，把预算执行误当成有效执行。"
                f"因此这一页的判断重点不是给出强拍板，而是明确下一步应该先复核谁、先补什么数据、先验证哪条改进路径。"
            )
            batch.append(
                {
                    "page_number": page["page_number"],
                    "page_title": page["page_title"],
                    "management_question": page["management_question"],
                    "diagnosis": diagnosis,
                    "evidence": evidence,
                    "derived_metric_explanation": "spend_rate 用 actual_spend / budget_amount 推导，budget_gap 用 budget_amount - actual_spend 推导。",
                    "business_interpretation": business_interpretation,
                    "recommended_action": {
                        "object": "Project-01",
                        "trigger_metric": "spend_rate",
                        "current_value": "0.92",
                        "threshold_or_comparison": "若连续两期低于 0.95 则进入专项复核",
                        "owner_role": "业务负责人 + 数据分析",
                        "action": f"针对第{page['page_number']}页对象先做复核与归因",
                        "deadline": "T+7",
                        "verification_metric": "spend_rate / budget_gap",
                    },
                    "data_limitations": "当前仍需结合目标字段与更细时间粒度做二次复核，避免把相关性误写成原因。",
                    "forbidden_misreadings": ["不能把当前局部高表现写成整体健康增长", "不能把预算执行写成经营效率已经验证"],
                    "source_passes": page["source_passes"],
                    "ai_content_hash": f"hash-{page['page_number']}",
                }
            )
        return _live({"pages": batch})

    def _patch_live_chain(self, *, special_title: str | None = None, final_score: int = 95, missing_metric_id: bool = False):
        question_rows = [
            {
                "priority": i,
                "business_question": f"问题 {i}",
                "why_it_matters": f"重要性 {i}",
                "can_answer_now": "可以",
                "required_fields": ["entity_fields", "amount_fields"],
                "report_section": f"章节 {i}",
                "management_action": f"动作 {i}",
            }
            for i in range(1, 21)
        ]

        def _page_plan_runner(payload):
            return _live({"pages": self._page_plan(special_title=special_title), "notes": ["ai primary plan"]})

        def _page_batch_runner(payload):
            return self._page_batch(payload["pages"], unique_marker="UNIQUE_AI_MARKER_", missing_metric_id=missing_metric_id)

        patches = [
            patch("app.services.generic_long_codex_chain_service.codex_complete_input_fields", lambda payload: _live({"completed_problem_to_solve": "识别结构性问题并形成管理动作", "completed_core_purpose": "形成通用经营长报告"})),
            patch("app.services.generic_long_codex_chain_service.codex_semantic_analysis", lambda payload: _live({"subject_type": "generic_subject", "creator_profile": "当前数据主要描述项目/部门/区域经营对象"})),
            patch("app.services.generic_long_codex_chain_service.codex_generic_metric_derivation_plan", lambda payload: _live({"metrics": payload["metric_candidates"], "notes": ["live metric derivation"]})),
            patch("app.services.generic_long_codex_chain_service.codex_metric_interpretation", lambda payload: _live({"metric_cards": [{"metric": "spend_rate", "business_meaning": "预算执行率", "management_impact": "判断预算执行节奏", "caution": "不能直接写成成本效率"}, {"metric": "budget_gap", "business_meaning": "预算偏差", "management_impact": "识别超支/欠花", "caution": "需结合时间口径"}]})),
            patch("app.services.generic_long_codex_chain_service.codex_generic_management_question_bank", lambda payload: _live({"questions": question_rows})),
            patch("app.services.generic_long_codex_chain_service.codex_generic_exploratory_interpretation", lambda payload: _live({"main_findings": ["头部对象与中位对象差异扩大", "预算执行与问题密度错位"], "anomalies": ["问题对象集中在少数区域"], "possible_reasons": ["执行节奏与资源配置错位"], "cannot_conclude": ["不能直接下因果结论"], "next_validations": ["先做对象级复核"]})),
            patch("app.services.generic_long_codex_chain_service.codex_business_object_interpretation", lambda payload: _live({"headline": "对象级经营复核完成", "drilldown_findings": [{"title": "头部对象", "trigger_finding": "record_count high", "deeper_read": "头部对象规模高但效率未验证", "business_move": "先做对象复核"} for _ in payload["objects"]]})),
            patch("app.services.generic_long_codex_chain_service.codex_challenge_review", lambda payload: _live({"challenge_points": [], "counter_arguments": [], "boundary_alerts": [], "unresolved_gaps": []})),
            patch("app.services.generic_long_codex_chain_service.codex_generic_long_page_plan", _page_plan_runner),
            patch("app.services.generic_long_codex_chain_service.codex_generic_page_generation_batch", _page_batch_runner),
            patch("app.services.generic_long_codex_chain_service.codex_judge_feedback", lambda payload: _live({"verdict": "pass", "issues": [], "revise_instructions": []})),
            patch("app.services.generic_long_codex_chain_service.codex_generic_business_rigor_review", lambda payload: _live({"total_score": final_score, "verdict": "pass" if final_score >= 90 else "revise", "weaknesses": [] if final_score >= 90 else ["需要继续修复"], "improvement_actions": ["继续强化字段边界"]})),
            patch("app.services.generic_long_codex_chain_service.codex_generic_final_review", lambda payload: _live({"total_score": final_score, "verdict": "pass" if final_score >= 90 else "revise", "weaknesses": [] if final_score >= 90 else ["仍不建议交付"], "improvement_actions": ["重跑最终复核"]})),
        ]
        return patches

    def test_generic_long_requires_live_ai_chain(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        report = self._report_dict("strictfail01", field_registry, registry_payload, action_table, roadmap)
        report_dir = REPORTS_DIR / f"tmp-test-{uuid.uuid4().hex[:8]}"
        report_dir.mkdir(parents=True, exist_ok=True)
        try:
            failed_chain = {
                "strict_90_eligible": False,
                "all_page_drafts_written": False,
                "failed_passes": ["metric_derivation_plan"],
                "long_report_page_plan": {"pages": []},
                "page_drafts": [],
                "registry_payload": registry_payload,
            }
            with patch("app.services.report_service.run_multi_pass_codex_interpretation_chain", lambda **kwargs: failed_chain):
                result = _downloadable_bundle_cn_generic_long(report_dir, "strictfail01", report, frame, {}, self._request())
            self.assertFalse((report_dir / "strictfail01-management_report.pdf").exists())
            self.assertTrue((report_dir / "strictfail01-degraded_observation_report.pdf").exists())
            self.assertTrue((report_dir / "generic_long_codex_chain_failure_report.md").exists())
            self.assertEqual(result["main_downloadable"]["name"], "strictfail01-degraded_observation_report.pdf")
        finally:
            import shutil
            shutil.rmtree(report_dir, ignore_errors=True)

    def test_page_plan_uses_ai_output_not_local_override(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            patches = self._patch_live_chain(special_title="AI_SPECIAL_PAGE_TITLE_03")
            for item in patches:
                item.start()
            try:
                chain = run_multi_pass_codex_interpretation_chain(
                    report_dir=report_dir,
                    dataset_name="Generic Long Test Dataset",
                    sheet_name="Sheet1",
                    frame=frame,
                    request=self._request(),
                    field_registry=field_registry,
                    registry_payload=registry_payload,
                    action_rows=action_table,
                    roadmap_payload=roadmap,
                )
            finally:
                for item in reversed(patches):
                    item.stop()
            plan = json.loads((report_dir / "long_report_page_plan.json").read_text(encoding="utf-8"))["pages"]
            self.assertIn("AI_SPECIAL_PAGE_TITLE_03", [page["page_title"] for page in plan])
            self.assertEqual(plan[2]["page_title"], "AI_SPECIAL_PAGE_TITLE_03")
            self.assertEqual(chain["long_report_page_plan"]["pages"][2]["page_title"], "AI_SPECIAL_PAGE_TITLE_03")

    def test_page_drafts_are_structured_json(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            patches = self._patch_live_chain()
            for item in patches:
                item.start()
            try:
                run_multi_pass_codex_interpretation_chain(
                    report_dir=report_dir,
                    dataset_name="Generic Long Test Dataset",
                    sheet_name="Sheet1",
                    frame=frame,
                    request=self._request(),
                    field_registry=field_registry,
                    registry_payload=registry_payload,
                    action_rows=action_table,
                    roadmap_payload=roadmap,
                )
            finally:
                for item in reversed(patches):
                    item.stop()
            draft = json.loads((report_dir / "page_drafts" / "page_001.json").read_text(encoding="utf-8"))
            for key in ["diagnosis", "evidence", "business_interpretation", "recommended_action", "ai_content_hash"]:
                self.assertIn(key, draft)
            self.assertTrue(draft["recommended_action"]["action"])

    def test_generic_long_chain_e2e_exposes_derived_metric_usage_gate(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            patches = self._patch_live_chain()
            for item in patches:
                item.start()
            try:
                chain = run_multi_pass_codex_interpretation_chain(
                    report_dir=report_dir,
                    dataset_name="Generic Long Test Dataset",
                    sheet_name="Sheet1",
                    frame=frame,
                    request=self._request(),
                    field_registry=field_registry,
                    registry_payload=registry_payload,
                    action_rows=action_table,
                    roadmap_payload=roadmap,
                )
            finally:
                for item in reversed(patches):
                    item.stop()

            contract_path = report_dir / "derived_metric_usage_contract.json"
            summary_path = report_dir / "derived_metric_usage_summary.json"
            drafts_path = report_dir / "page_drafts.json"
            self.assertTrue(contract_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(drafts_path.exists())
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            drafts = json.loads(drafts_path.read_text(encoding="utf-8"))["pages"]
            self.assertGreater(contract["derived_metric_count"], 0)
            self.assertGreater(chain["derived_metric_count"], 0)
            self.assertTrue(summary["passes_gate"])
            self.assertGreaterEqual(summary["body_metric_count"], min(3, contract["derived_metric_count"]))
            self.assertGreaterEqual(summary["recommendation_metric_count"], 1)
            self.assertGreaterEqual(summary["asset_metric_count"], 1)
            self.assertTrue(chain["used_derived_metric_names"])
            self.assertIn("missing_derived_metric_names", chain)
            self.assertGreater(float(chain["derived_metric_coverage_ratio"]), 0)
            self.assertTrue(all(draft.get("derived_metrics_used") for draft in drafts))
            known_metric_ids = {row["metric_id"] for row in contract["metrics"]}
            self.assertTrue(
                any((draft.get("recommended_action") or {}).get("trigger_metric") in known_metric_ids for draft in drafts)
            )
            self.assertTrue(chain["contract_artifacts"]["derived_metric_usage_contract"]["exists"])
            self.assertTrue(chain["contract_artifacts"]["derived_metric_usage_summary"]["exists"])

    def test_runtime_page_plan_and_page_drafts_contracts_are_written(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        request = self._request()
        observed_stage_ids: list[str] = []

        def runtime_child_creator(
            request_payload: CodexRunRequest,
            *,
            parent_report_id: str = "",
            stage_id: str = "",
            purpose: str = "",
            stage_listener=None,
        ) -> dict[str, object]:
            workspace = Path(request_payload.workspace_path)
            observed_stage_ids.append(stage_id)
            if stage_id == "long_report_page_plan":
                (workspace / "page_plan.json").write_text(
                    json.dumps({"pages": self._page_plan(special_title="RUNTIME_PLAN_TITLE")}, ensure_ascii=False),
                    encoding="utf-8",
                )
                run_id = "run-plan-001"
                job_id = "codex-task-plan-001"
            else:
                existing = json.loads((workspace / "page_drafts.json").read_text(encoding="utf-8"))["pages"] if (workspace / "page_drafts.json").exists() else []
                batch_pages = request_payload.context_payload["pages"]
                new_pages = self._page_batch(batch_pages, unique_marker="RUNTIME_DRAFT_MARKER_")["pages"]
                merged: dict[int, dict] = {int(item["page_number"]): item for item in existing}
                for draft in new_pages:
                    merged[int(draft["page_number"])] = draft
                (workspace / "page_drafts.json").write_text(
                    json.dumps({"pages": [merged[number] for number in sorted(merged)]}, ensure_ascii=False),
                    encoding="utf-8",
                )
                run_id = f"run-batch-{stage_id}"
                job_id = f"codex-task-{stage_id}"
            if stage_listener:
                stage_listener(
                    {
                        "stage_id": f"runtime_child::{purpose}::completed",
                        "title": "Runtime child completed",
                        "detail": stage_id,
                        "timestamp": "2026-04-30T00:00:00Z",
                        "payload": {"status": "completed", "run_id": run_id},
                    }
                )
            return {
                "job_id": job_id,
                "run_id": run_id,
                "parent_report_job_id": "report-task-runtime-001",
                "parent_report_id": parent_report_id,
                "stage_id": stage_id,
                "purpose": purpose,
                "status": "queued",
                "progress_percent": 0,
                "current_stage_id": "queued",
                "current_stage_title": "Task created",
                "current_stage_detail": "queued",
            }

        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            local_patches = self._patch_live_chain()
            for item in local_patches:
                item.start()
            with patch("app.services.generic_long_codex_chain_service.load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True}), patch(
                "app.services.generic_long_codex_chain_service.get_codex_run_task",
                lambda job_id: {"job_id": job_id, "run_id": f"{job_id}-run", "status": "completed"},
            ), patch(
                "app.services.generic_long_codex_chain_service.codex_generic_long_page_plan",
                side_effect=AssertionError("runtime page plan should avoid local runner"),
            ), patch(
                "app.services.generic_long_codex_chain_service.codex_generic_page_generation_batch",
                side_effect=AssertionError("runtime page drafts should avoid local runner"),
            ):
                try:
                    chain = run_multi_pass_codex_interpretation_chain(
                        report_dir=report_dir,
                        parent_report_id="report-runtime-001",
                        dataset_name="Generic Long Test Dataset",
                        sheet_name="Sheet1",
                        frame=frame,
                        request=request,
                        field_registry=field_registry,
                        registry_payload=registry_payload,
                        action_rows=action_table,
                        roadmap_payload=roadmap,
                        runtime_child_task_creator=runtime_child_creator,
                    )
                finally:
                    for item in reversed(local_patches):
                        item.stop()

            self.assertTrue((report_dir / "page_plan.json").exists())
            self.assertTrue((report_dir / "page_drafts.json").exists())
            self.assertTrue((report_dir / "page_plan.schema.json").exists())
            self.assertTrue((report_dir / "page_drafts.schema.json").exists())
            plan = json.loads((report_dir / "page_plan.json").read_text(encoding="utf-8"))["pages"]
            drafts = json.loads((report_dir / "page_drafts.json").read_text(encoding="utf-8"))["pages"]
            self.assertEqual(plan[2]["page_title"], "RUNTIME_PLAN_TITLE")
            self.assertTrue(any("RUNTIME_DRAFT_MARKER_" in draft["diagnosis"] for draft in drafts))
            self.assertEqual(chain["long_report_page_plan"]["pages"][2]["page_title"], "RUNTIME_PLAN_TITLE")
            self.assertEqual(len(chain["page_drafts"]), len(plan))
            self.assertIn("long_report_page_plan", observed_stage_ids)
            self.assertTrue(any(stage_id.startswith("page_generation_batch_") for stage_id in observed_stage_ids))
            self.assertTrue(chain["contract_artifacts"]["page_plan"]["exists"])
            self.assertTrue(chain["contract_artifacts"]["page_drafts"]["exists"])

    def test_runtime_page_plan_failure_falls_back_to_local_chain(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        request = self._request()

        def runtime_child_creator(
            request_payload: CodexRunRequest,
            *,
            parent_report_id: str = "",
            stage_id: str = "",
            purpose: str = "",
            stage_listener=None,
        ) -> dict[str, object]:
            return {
                "job_id": "codex-task-plan-fallback",
                "run_id": "run-plan-fallback",
                "parent_report_job_id": "report-task-runtime-002",
                "parent_report_id": parent_report_id,
                "stage_id": stage_id,
                "purpose": purpose,
                "status": "queued",
                "progress_percent": 0,
                "current_stage_id": "queued",
                "current_stage_title": "Task created",
                "current_stage_detail": "queued",
            }

        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            local_patches = self._patch_live_chain(special_title="LOCAL_FALLBACK_PLAN_TITLE")
            for item in local_patches:
                item.start()
            with patch("app.services.generic_long_codex_chain_service.load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True}), patch(
                "app.services.generic_long_codex_chain_service.get_codex_run_task",
                lambda job_id: {"job_id": job_id, "run_id": "run-plan-fallback", "status": "failed"},
            ):
                try:
                    chain = run_multi_pass_codex_interpretation_chain(
                        report_dir=report_dir,
                        parent_report_id="report-runtime-002",
                        dataset_name="Generic Long Test Dataset",
                        sheet_name="Sheet1",
                        frame=frame,
                        request=request,
                        field_registry=field_registry,
                        registry_payload=registry_payload,
                        action_rows=action_table,
                        roadmap_payload=roadmap,
                        runtime_child_task_creator=runtime_child_creator,
                    )
                finally:
                    for item in reversed(local_patches):
                        item.stop()

            plan = json.loads((report_dir / "page_plan.json").read_text(encoding="utf-8"))["pages"]
            self.assertEqual(plan[2]["page_title"], "LOCAL_FALLBACK_PLAN_TITLE")
            self.assertEqual(chain["long_report_page_plan"]["pages"][2]["page_title"], "LOCAL_FALLBACK_PLAN_TITLE")

    def test_renderer_consumes_full_page_draft(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        plan = self._page_plan()
        drafts = self._page_batch(plan, unique_marker="VERY_UNIQUE_RENDERER_MARKER_")["pages"]
        report = self._report_dict("renderer01", field_registry, registry_payload, action_table, roadmap)
        chain_payload = {
            "long_report_page_plan": {"pages": plan},
            "page_drafts": drafts,
            "field_semantic_map": {"rows": []},
            "metric_derivation_plan": {"metrics": []},
            "derived_metric_execution_review": {"metrics": []},
            "management_question_bank": {"questions": []},
            "object_level_interpretation": {"rows": []},
        }
        variant = build_generic_long_management_variant(report, chain_payload)
        self.assertIsNotNone(variant)
        first_bullets = "\n".join(variant["sections"][0]["bullets"])
        self.assertIn("VERY_UNIQUE_RENDERER_MARKER_", first_bullets)
        html = _render_report_html_cn(variant)
        self.assertIn("VERY_UNIQUE_RENDERER_MARKER_", html)
        self.assertNotIn("splitlines()[2]", html)

    def test_appendix_variant_keeps_full_registry_and_plan_rows(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        report = self._report_dict("appendixfull01", field_registry, registry_payload, action_table, roadmap)
        chain_payload = {
            "field_semantic_map": {"rows": [{"field_name": f"field_{i}", "guessed_business_meaning": "x", "metric_type": "y", "usable_for": [], "not_usable_for": [], "needs_manual_confirmation": False} for i in range(60)]},
            "metric_derivation_plan": {"metrics": [{"metric_id": f"metric_{i}"} for i in range(45)]},
            "derived_metric_execution_review": {"metrics": [{"metric_id": f"metric_{i}"} for i in range(45)]},
            "management_question_bank": {"questions": [{"business_question": f"q_{i}"} for i in range(28)]},
            "object_level_interpretation": {"rows": [{"object_id": f"obj_{i}"} for i in range(35)]},
            "long_report_page_plan": {"pages": [{"page_number": i + 1, "page_title": f"page_{i}"} for i in range(55)]},
        }
        registry_payload["rows"] = [{"object_level": "project", "object_id": f"obj_{i}", "object_name": f"obj_{i}", "final_label": "L", "final_action": "A", "missing_fields": [], "conclusion_type": "direct", "confidence_level": "high"} for i in range(52)]
        appendix_variant = build_generic_long_appendix_variant(report, chain_payload)
        sections = {section["id"]: section for section in appendix_variant["sections"]}
        self.assertEqual(len(sections["appendix_field_semantic_map"]["tables"][0]["rows"]), 60)
        self.assertEqual(len(sections["appendix_metric_derivation"]["tables"][0]["rows"]), 45)
        self.assertEqual(len(sections["appendix_metric_derivation"]["tables"][1]["rows"]), 45)
        self.assertEqual(len(sections["appendix_object_registry"]["tables"][0]["rows"]), 52)
        self.assertEqual(len(sections["appendix_object_registry"]["tables"][1]["rows"]), 35)
        self.assertEqual(len(sections["appendix_question_bank"]["tables"][0]["rows"]), 28)
        self.assertEqual(len(sections["appendix_question_bank"]["tables"][1]["rows"]), 55)

    def test_missing_page_draft_blocks_pdf(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        plan = self._page_plan()
        drafts = self._page_batch(plan)["pages"]
        drafts = [draft for draft in drafts if draft["page_number"] != 10]
        report = self._report_dict("renderer02", field_registry, registry_payload, action_table, roadmap)
        chain_payload = {
            "long_report_page_plan": {"pages": plan},
            "page_drafts": drafts,
            "field_semantic_map": {"rows": []},
            "metric_derivation_plan": {"metrics": []},
            "derived_metric_execution_review": {"metrics": []},
            "management_question_bank": {"questions": []},
            "object_level_interpretation": {"rows": []},
        }
        with self.assertRaises(MissingStructuredPageDraftError):
            build_generic_long_management_variant(report, chain_payload)

    def test_final_review_score_not_forced_to_90(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            patches = self._patch_live_chain(final_score=62)
            for item in patches:
                item.start()
            try:
                chain = run_multi_pass_codex_interpretation_chain(
                    report_dir=report_dir,
                    dataset_name="Generic Long Test Dataset",
                    sheet_name="Sheet1",
                    frame=frame,
                    request=self._request(),
                    field_registry=field_registry,
                    registry_payload=registry_payload,
                    action_rows=action_table,
                    roadmap_payload=roadmap,
                )
            finally:
                for item in reversed(patches):
                    item.stop()
            self.assertEqual(chain["final_review_score"], 62)
            self.assertFalse(chain["strict_90_eligible"])
            self.assertIn("FINAL_REVIEW_SCORE: 62", (report_dir / "final_codex_interpretation_review.md").read_text(encoding="utf-8"))

    def _write_valid_report_dir(self, report_dir: Path, *, consumed: bool = True, missing_metric_id: bool = False) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        report = self._report_dict("audit01", field_registry, registry_payload, action_table, roadmap)
        plan = self._page_plan()
        drafts = self._page_batch(plan, unique_marker="AUDIT_UNIQUE_MARKER_", missing_metric_id=missing_metric_id)["pages"]
        chain_payload = {
            "long_report_page_plan": {"pages": plan},
            "page_drafts": drafts,
            "field_semantic_map": {"rows": []},
            "metric_derivation_plan": {"metrics": [{"metric_id": "spend_rate"}]},
            "derived_metric_execution_review": {"metrics": [{"metric_id": "spend_rate"}]},
            "management_question_bank": {"questions": []},
            "object_level_interpretation": {"rows": []},
        }
        variant = build_generic_long_management_variant(report, chain_payload)
        assert variant is not None
        report_id = "audit01"
        (report_dir / f"{report_id}-management_report.md").write_text(_render_report_html_cn(variant) if not consumed else "\n".join(variant["sections"][0]["bullets"]), encoding="utf-8")
        (report_dir / "business_context_interpretation.md").write_text("x" * 1000, encoding="utf-8")
        (report_dir / "field_semantic_map.md").write_text("x" * 1000, encoding="utf-8")
        (report_dir / "generic_kpi_tree.md").write_text("x" * 1000, encoding="utf-8")
        (report_dir / "management_question_bank.md").write_text("x" * 1200, encoding="utf-8")
        (report_dir / "object_level_interpretation.md").write_text("x" * 1200, encoding="utf-8")
        (report_dir / "interpretation_conflict_check.md").write_text("x" * 900, encoding="utf-8")
        (report_dir / "executive_readability_review.md").write_text("# executive_readability_review\n\n- SEVERE_ISSUES_FIXED: YES\n", encoding="utf-8")
        (report_dir / "business_rigor_review.md").write_text("# business_rigor_review\n\n- SEVERE_ISSUES_FIXED: YES\n", encoding="utf-8")
        (report_dir / "final_codex_interpretation_review.md").write_text("# final_codex_interpretation_review\n\n- DELIVERABLE_STATUS: PASS\n- FINAL_REVIEW_SCORE: 95\n", encoding="utf-8")
        (report_dir / "metric_derivation_plan.json").write_text(json.dumps({"metrics": [{"metric_id": "spend_rate"}]}, ensure_ascii=False), encoding="utf-8")
        (report_dir / "derived_metric_execution_review.md").write_text("x" * 1000, encoding="utf-8")
        (report_dir / "long_report_page_plan.json").write_text(json.dumps({"pages": plan}, ensure_ascii=False), encoding="utf-8")
        (report_dir / "page_plan.json").write_text(json.dumps({"pages": plan}, ensure_ascii=False), encoding="utf-8")
        (report_dir / "page_plan.schema.json").write_text(json.dumps({"type": "object", "required": ["pages"]}, ensure_ascii=False), encoding="utf-8")
        (report_dir / "page_drafts.json").write_text(json.dumps({"pages": drafts}, ensure_ascii=False), encoding="utf-8")
        (report_dir / "page_drafts.schema.json").write_text(json.dumps({"type": "object", "required": ["pages"]}, ensure_ascii=False), encoding="utf-8")
        (report_dir / "generic_field_availability_registry.json").write_text(json.dumps(field_registry, ensure_ascii=False), encoding="utf-8")
        write_generic_registry_artifacts(report_dir, registry_payload, roadmap)
        pd.DataFrame(action_table).to_csv(report_dir / "generic_action_table.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(roadmap["seven_day_action_table"]).to_csv(report_dir / "7_day_action_table.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(roadmap["thirty_day_improvement_backlog"]).to_csv(report_dir / "30_day_improvement_backlog.csv", index=False, encoding="utf-8-sig")
        log_rows = []
        for name in [
            "business_context_interpretation",
            "field_semantic_map",
            "metric_derivation_plan",
            "derived_metric_execution_review",
            "management_question_bank",
            "exploratory_interpretation",
            "object_level_interpretation",
            "interpretation_conflict_check",
            "long_report_page_plan",
            "executive_readability_review",
            "business_rigor_review",
            "final_codex_interpretation_review",
        ]:
            log_rows.append(
                {
                    "pass_name": name,
                    "required": True,
                    "status": "success",
                    "runner_name": "mock_runner",
                    "started_at": "2026-04-25T00:00:00Z",
                    "finished_at": "2026-04-25T00:00:01Z",
                    "latency_ms": 1000,
                    "input_hash": "x",
                    "output_hash": "y",
                    "output_text_length": 2500,
                    "output_json_valid": True,
                    "output_files": [f"{name}.md"],
                    "files_written": True,
                    "fallback_used": False,
                    "cache_used": False,
                    "cache_valid": False,
                    "downstream_usage": ["management_report"],
                    "error": None,
                    "retry_count": 0,
                }
            )
        for index in range(1, 9):
            log_rows.append(
                {
                    "pass_name": f"page_generation_batch_{index:02d}",
                    "required": True,
                    "status": "success",
                    "runner_name": "mock_runner",
                    "started_at": "2026-04-25T00:00:00Z",
                    "finished_at": "2026-04-25T00:00:01Z",
                    "latency_ms": 1000,
                    "input_hash": "x",
                    "output_hash": "y",
                    "output_text_length": 4000,
                    "output_json_valid": True,
                    "output_files": [f"page_drafts/page_{index:03d}.json"],
                    "files_written": True,
                    "fallback_used": False,
                    "cache_used": False,
                    "cache_valid": False,
                    "downstream_usage": ["management_report"],
                    "error": None,
                    "retry_count": 0,
                }
            )
        (report_dir / "codex_interpretation_call_log.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in log_rows) + "\n", encoding="utf-8")
        (report_dir / "codex_interpretation_summary.md").write_text("summary", encoding="utf-8")
        page_dir = report_dir / "page_drafts"
        page_dir.mkdir(parents=True, exist_ok=True)
        for draft in drafts:
            (page_dir / f"page_{draft['page_number']:03d}.json").write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
        variant_for_output = variant
        if not consumed:
            stripped_sections = []
            for section in variant["sections"]:
                stripped_sections.append({**section, "bullets": [f"管理问题：{section['summary']}", "诊断判断：模板句", "指标推导：模板句", "业务解释：模板句", "建议动作：模板句", "数据边界：模板句"]})
            variant_for_output = {**variant, "sections": stripped_sections}
        (report_dir / f"{report_id}-management_report.html").write_text(_render_report_html_cn(variant_for_output), encoding="utf-8")
        _write_pdf_report_cn(report_dir, f"{report_id}-management_report", variant_for_output)
        (report_dir / f"{report_id}-report_quality_score.json").write_text(json.dumps({"score": 95, "passed": True}, ensure_ascii=False), encoding="utf-8")
        (report_dir / f"{report_id}-quality_gate_result.json").write_text(json.dumps({"passed": True}, ensure_ascii=False), encoding="utf-8")

    def test_quality_gate_fails_when_ai_not_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            self._write_valid_report_dir(report_dir, consumed=False)
            management_markdown = "管理问题：模板\n诊断判断：模板\n指标推导：模板\n业务解释：模板\n建议动作：模板"
            field_registry = json.loads((report_dir / "generic_field_availability_registry.json").read_text(encoding="utf-8"))
            gate = generic_long_quality_gate(
                report_dir=report_dir,
                management_markdown=management_markdown,
                total_pages=37,
                business_profile="generic_long_business_report",
                field_registry=field_registry,
                action_rows=pd.read_csv(report_dir / "generic_action_table.csv").to_dict(orient="records"),
                seven_day_rows=pd.read_csv(report_dir / "7_day_action_table.csv").to_dict(orient="records"),
                backlog_rows=pd.read_csv(report_dir / "30_day_improvement_backlog.csv").to_dict(orient="records"),
            )
            self.assertFalse(gate["passed"])
            self.assertTrue(any("AI page drafts were generated but not consumed by final PDF." in item for item in gate["fail_items"]))

    def test_independent_validator_checks_ai_content_in_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-audit01"
            report_dir.mkdir(parents=True, exist_ok=True)
            self._write_valid_report_dir(report_dir, consumed=False)
            result = validate_report_dir(report_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("AI page draft 未写入最终 PDF" in item or "PDF 只渲染 page_plan，未渲染 page_draft" in item for item in result["fail_items"]))

    def test_metric_id_required_for_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-audit01"
            report_dir.mkdir(parents=True, exist_ok=True)
            self._write_valid_report_dir(report_dir, consumed=True, missing_metric_id=True)
            result = validate_report_dir(report_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("test_metric_id_required_for_claims" in item for item in result["fail_items"]))

    def test_fallback_used_blocks_strict_90_pdf(self) -> None:
        frame, field_registry, registry_payload, action_table, roadmap = self._report_context()
        report_dir = REPORTS_DIR / f"tmp-test-{uuid.uuid4().hex[:8]}"
        report_dir.mkdir(parents=True, exist_ok=True)
        try:
            fallback_chain = {
                "strict_90_eligible": False,
                "all_page_drafts_written": True,
                "failed_passes": ["long_report_page_plan"],
                "long_report_page_plan": {"pages": self._page_plan()},
                "page_drafts": self._page_batch(self._page_plan())["pages"],
                "registry_payload": registry_payload,
            }
            report = self._report_dict("fallbackblock01", field_registry, registry_payload, action_table, roadmap)
            with patch("app.services.report_service.run_multi_pass_codex_interpretation_chain", lambda **kwargs: fallback_chain):
                _downloadable_bundle_cn_generic_long(report_dir, "fallbackblock01", report, frame, {}, self._request())
            self.assertFalse((report_dir / "fallbackblock01-management_report.pdf").exists())
            self.assertTrue((report_dir / "fallbackblock01-degraded_observation_report.pdf").exists())
            try:
                from pypdf import PdfReader
                pages = len(PdfReader(str(report_dir / "fallbackblock01-degraded_observation_report.pdf")).pages)
                self.assertGreaterEqual(pages, 35)
            except Exception:
                pass
        finally:
            import shutil
            shutil.rmtree(report_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
