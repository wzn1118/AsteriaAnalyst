from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from app.services.ai_mandatory.schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMappingResult,
)
from app.models import SmartReportRequest
from app.services.orchestration_service import build_report_orchestration


class OrchestrationServiceTests(unittest.TestCase):
    @patch("app.services.orchestration_service.build_market_intelligence")
    @patch("app.services.orchestration_service.codex_statistical_scope")
    @patch("app.services.orchestration_service.build_analysis_program")
    @patch("app.services.orchestration_service.route_business_context_with_ai")
    @patch("app.services.orchestration_service.map_fields_with_ai")
    @patch("app.services.orchestration_service.build_workflow_blueprint")
    @patch("app.services.orchestration_service.load_dataset_frame")
    @patch("app.services.orchestration_service.load_dataset_metadata")
    def test_single_route_builds_real_execution_trace(
        self,
        mock_metadata,
        mock_load_frame,
        mock_blueprint,
        mock_semantic_mapper,
        mock_ai_router,
        mock_program,
        mock_scope,
        mock_market,
    ) -> None:
        frame = pd.DataFrame({"日期": ["2026-04-01"], "收入": [100.0], "成本": [60.0]})
        metadata = {
            "name": "测试数据集",
            "active_sheet": "Sheet1",
            "sheets": [{"name": "Sheet1"}],
            "column_summaries": [],
        }
        mock_metadata.return_value = metadata
        mock_load_frame.return_value = (frame, metadata, {"name": "Sheet1"})
        mock_blueprint.return_value = {
            "workflow_mode": "general_exploratory_analysis",
            "recommended_entry_sheet": "Sheet1",
            "sheet_profiles": [{"name": "Sheet1", "role": "analytical_fact"}],
            "relationships": [],
        }
        mock_semantic_mapper.return_value = AIFieldSemanticMappingResult(
            inferred_business_context="缁忚惀鏁版嵁鍦烘櫙",
            object_grain="transaction_day",
            time_grain="day",
            field_mappings=[],
            uncertain_fields=[],
            provider="OpenAI",
            model="gpt-5.4",
            trace_id="trace-semantic-001",
        )
        mock_ai_router.return_value = AIBusinessRoutingResult(
            selected_by_user=None,
            ai_route="generic_business_report",
            final_route="generic_business_report",
            confidence=0.85,
            alternative_routes=["generic_long_business_report"],
            reason="signals point to general business review",
            blocked_routes=[],
            trace_id="trace-route-001",
        )
        mock_program.return_value = {
            "frame": frame,
            "task_model": {"primary_family": "sales_review", "problem": "判断经营表现"},
            "object_candidates": [{"object_type": "sales_transaction_panel"}],
            "resolved_request_payload": {"problem_to_solve": "判断经营表现"},
            "program": {"core_outcomes": ["收入"], "explanatory_slices": ["日期"], "cannot_analyze": []},
            "experts": [{"expert": "经营分析师"}],
            "hypotheses": [{"title": "sales_transaction_panel"}, {"title": "backup"}],
        }
        mock_scope.return_value = {"keep_numeric_columns": ["收入", "成本"], "exclude_numeric_columns": []}
        mock_market.return_value = {"ready": False}

        result = build_report_orchestration(
            "demo",
            SmartReportRequest(problem_to_solve="判断经营表现"),
        )
        step_ids = [item["id"] for item in result["execution_steps"]]
        self.assertIn("route_selection", step_ids)
        self.assertIn("requirement_modeling", step_ids)
        self.assertIn("specialist_activation", step_ids)
        self.assertEqual(result["request"].problem_to_solve, "判断经营表现")
        self.assertEqual(result["program_bundle"]["task_model"]["primary_family"], "sales_review")
        graph_ids = [item["id"] for item in result["job_graph"] if item["status"] == "completed"]
        self.assertIn("program_bundle", graph_ids)
        self.assertIn("profile_bundle", graph_ids)
        self.assertIn("statistical_scope", graph_ids)
        self.assertIn("expert_summary", graph_ids)

    @patch("app.services.orchestration_service.build_workflow_blueprint")
    @patch("app.services.orchestration_service.route_business_context_with_ai")
    @patch("app.services.orchestration_service.map_fields_with_ai")
    @patch("app.services.orchestration_service.load_all_sheet_frames")
    @patch("app.services.orchestration_service.load_dataset_metadata")
    def test_combined_route_stays_at_workbook_level(
        self,
        mock_metadata,
        mock_load_all,
        mock_semantic_mapper,
        mock_ai_router,
        mock_blueprint,
    ) -> None:
        metadata = {
            "name": "多表数据集",
            "active_sheet": "Sheet1",
            "sheets": [{"name": "Sheet1"}, {"name": "Sheet2"}],
        }
        mock_metadata.return_value = metadata
        mock_load_all.return_value = (
            metadata,
            [
                ({"name": "Sheet1"}, pd.DataFrame({"A": [1]})),
                ({"name": "Sheet2"}, pd.DataFrame({"B": [2]})),
            ],
        )
        mock_blueprint.return_value = {
            "workflow_mode": "multi_source_relational_analysis",
            "recommended_entry_sheet": "Sheet1",
            "sheet_profiles": [],
            "relationships": [{"left_sheet": "Sheet1", "right_sheet": "Sheet2"}],
        }
        mock_semantic_mapper.return_value = AIFieldSemanticMappingResult(
            inferred_business_context="澶氳〃缁忚惀鍦烘櫙",
            object_grain="generic_business_object",
            time_grain="unknown",
            field_mappings=[],
            uncertain_fields=[],
            provider="OpenAI",
            model="gpt-5.4",
            trace_id="trace-semantic-002",
        )
        mock_ai_router.return_value = AIBusinessRoutingResult(
            selected_by_user=None,
            ai_route="generic_long_business_report",
            final_route="generic_long_business_report",
            confidence=0.82,
            alternative_routes=["generic_business_report"],
            reason="multi-table mixed business context",
            blocked_routes=[],
            trace_id="trace-route-002",
        )

        result = build_report_orchestration(
            "demo",
            SmartReportRequest(
                selected_sheets=["Sheet1", "Sheet2"],
                multi_table_mode="combined",
            ),
        )
        self.assertEqual(result["multi_mode"], "combined")
        self.assertNotIn("frame", result)
        self.assertEqual(result["selected_sheet_names"], ["Sheet1", "Sheet2"])
        self.assertTrue(any("组合分析模式" in item["detail"] for item in result["execution_steps"]))


if __name__ == "__main__":
    unittest.main()
