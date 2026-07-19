from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.models import SmartReportRequest
from app.services.challenge_service import summarize_revision_routes
from app.services.codex_service import (
    _fallback_business_synthesis,
    _fallback_challenge_review,
    _fallback_decision_design,
    _fallback_evidence_digest,
    _fallback_insight_mining,
    _fallback_judge_feedback,
)
from app.services.report_service import _run_reasoning_chain


class ReasoningChainTests(unittest.TestCase):
    def test_evidence_digest_layer_compresses_evidence(self) -> None:
        result = _fallback_evidence_digest(
            "fallback",
            {
                "requirement_layer": {"must_answer_questions": ["先判断谁该优先复盘"]},
                "metric_interpretation_layer": {"metric_cards": [{"metric": "留存率", "business_meaning": "留存率当前是关键效率指标。"}]},
                "method_review_layer": {"method_reviews": [{"method": "ANOVA", "result_meaning": "当前没有证据说明不同渠道整体已经稳定拉开。"}]},
            },
        )
        self.assertTrue(result["priority_evidence"])
        self.assertIn("留存率", " ".join(result["priority_evidence"]))

    def test_insight_mining_layer_extracts_priorities(self) -> None:
        result = _fallback_insight_mining(
            "fallback",
            {
                "evidence_digest_layer": {
                    "priority_evidence": ["渠道差异不显著", "活动总量和均值要分开看"],
                    "key_methods": ["ANOVA=>渠道差异不显著"],
                }
            },
        )
        self.assertTrue(result["priority_insights"])
        self.assertIn("活动总量和均值要分开看", " ".join(result["important_findings"]))

    def test_challenge_layer_marks_overreach(self) -> None:
        result = _fallback_challenge_review(
            "fallback",
            {
                "insight_mining_layer": {
                    "important_findings": ["社群最优先", "活动需要继续观察"],
                },
                "evidence_digest_layer": {"key_boundaries": ["不能把样本内现象直接写成强结论"]},
            },
        )
        self.assertTrue(result["challenge_points"])
        self.assertIn("不能把样本内现象直接写成强结论", " ".join(result["boundary_alerts"]))

    def test_business_judgement_layer_absorbs_challenge(self) -> None:
        result = _fallback_business_synthesis(
            "fallback",
            {
                "request": {"core_purpose": "优化资源分配"},
                "business_background_layer": {"decision_implications": ["建议必须服务资源分配"]},
                "insight_mining_layer": {"important_findings": ["渠道差异不显著"]},
                "challenge_layer": {"boundary_alerts": ["不能直接按渠道切预算"]},
            },
        )
        self.assertIn("优化资源分配", result["management_summary"])
        self.assertIn("不能直接按渠道切预算", " ".join(result["strategic_implications"]))

    def test_decision_design_layer_generates_priority_and_sequence(self) -> None:
        result = _fallback_decision_design(
            "fallback",
            {
                "business_judgement_layer": {"judgement_points": ["先拆渠道×活动", "再看内容承接"]},
                "challenge_layer": {"unresolved_gaps": ["需要补充分母口径"]},
            },
        )
        self.assertGreaterEqual(len(result["priority_actions"]), 2)
        self.assertEqual(result["priority_actions"][0]["priority"], "P1")
        self.assertEqual(result["priority_actions"][0]["sequence"], 1)

    def test_judge_routes_revise_by_problem_type(self) -> None:
        result = _fallback_judge_feedback(
            "fallback",
            {
                "business_judgement_layer": {},
                "decision_design_layer": {},
                "final_polish_layer": {},
            },
        )
        routes = summarize_revision_routes(result)
        self.assertEqual(result["verdict"], "revise")
        self.assertTrue(routes["business"])
        self.assertTrue(routes["decision"])
        self.assertTrue(routes["polish"])

    @patch("app.services.report_service.build_analysis_program")
    @patch("app.services.report_service.run_statistical_analysis")
    @patch("app.services.report_service.codex_judge_feedback")
    @patch("app.services.report_service.codex_final_polish")
    @patch("app.services.report_service.codex_decision_design")
    @patch("app.services.report_service.codex_business_synthesis")
    @patch("app.services.report_service.codex_challenge_review")
    @patch("app.services.report_service.codex_insight_mining")
    @patch("app.services.report_service.codex_evidence_digest")
    def test_deep_dive_runs_full_chain_without_repeating_bottom_analysis(
        self,
        mock_digest,
        mock_insight,
        mock_challenge,
        mock_business,
        mock_decision,
        mock_polish,
        mock_judge,
        mock_run_stats,
        mock_build_program,
    ) -> None:
        mock_digest.return_value = {"priority_evidence": ["A"], "key_boundaries": []}
        mock_insight.return_value = {"important_findings": ["B"], "priority_insights": []}
        mock_challenge.return_value = {"challenge_points": [], "boundary_alerts": [], "counter_arguments": [], "unresolved_gaps": []}
        mock_business.return_value = {"management_summary": "summary", "judgement_points": ["J1"], "strategic_implications": [], "focus_decisions": []}
        mock_decision.return_value = {"decision_headline": "headline", "priority_actions": [{"priority": "P1", "action": "Do", "rationale": "Because", "sequence": 1, "expected_signal": "signal"}], "scenario_options": [], "validation_agenda": [], "management_questions": []}
        mock_polish.return_value = {"polished_executive_summary": ["S1"], "section_overrides": [], "narrative_upgrades": []}
        mock_judge.return_value = {"verdict": "pass", "issues": [], "revise_instructions": [], "route_summary": []}

        report = {"sections": [], "executive_summary": []}
        result = _run_reasoning_chain(
            metadata={"name": "demo"},
            sheet={"name": "Sheet1"},
            frame=pd.DataFrame({"x": [1, 2], "y": [3, 4]}),
            request=SmartReportRequest(report_style="deep_dive"),
            report_lens="internet_ops_review",
            program_bundle={"lens": "internet_ops_review", "resolved_request_payload": {}},
            report=report,
            requirement_layer={"must_answer_questions": ["Q1"]},
            data_understanding={"overview": [], "useful_parts": []},
            semantic_layer={},
            metric_interpretation_layer={},
            method_review_layer={},
            business_background_layer={},
            business_object_layer={},
            codex_layer={},
            historical_report_adaptation=None,
        )
        self.assertIn("evidence_digest_layer", result)
        self.assertIn("judge_feedback_layer", result)
        mock_run_stats.assert_not_called()
        mock_build_program.assert_not_called()

    def test_key_path_duplicate_definitions_cleaned(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        files = [
            (repository_root / "backend" / "app" / "services" / "codex_service.py", ["codex_internet_ops_review", "_fallback_internet_ops_review"]),
            (repository_root / "backend" / "app" / "services" / "report_service.py", ["_stats_appendix_section_v3"]),
        ]
        for path, names in files:
            module = ast.parse(path.read_text(encoding="utf-8"))
            counts: dict[str, int] = {}
            for node in module.body:
                if isinstance(node, ast.FunctionDef):
                    counts[node.name] = counts.get(node.name, 0) + 1
            for name in names:
                self.assertEqual(counts.get(name, 0), 1, f"{name} duplicated in {path}")


if __name__ == "__main__":
    unittest.main()
