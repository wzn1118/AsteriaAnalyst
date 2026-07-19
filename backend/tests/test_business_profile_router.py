from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from app.models import SmartReportRequest
from app.services.ai_mandatory.schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMappingResult,
)
from app.services.business_profile_router import (
    ECOMMERCE_GROUPS,
    ECOMMERCE_PLATFORM_TOKENS,
    MEDIA_GROUPS,
    PROCUREMENT_GROUPS,
    route_business_profile,
    runtime_policy_for_report,
    runtime_stage_enabled,
)
from app.services.orchestration_service import build_report_orchestration


class BusinessProfileRouterTests(unittest.TestCase):
    def test_chinese_routing_tokens_remain_utf8_literals(self) -> None:
        self.assertIn("淘宝", ECOMMERCE_PLATFORM_TOKENS)
        self.assertIn("天猫", ECOMMERCE_PLATFORM_TOKENS)
        self.assertIn("京东", ECOMMERCE_PLATFORM_TOKENS)
        self.assertIn("拼多多", ECOMMERCE_PLATFORM_TOKENS)
        self.assertIn("商品名称", ECOMMERCE_GROUPS["product_fields"])
        self.assertIn("一级类目", ECOMMERCE_GROUPS["category_fields"])
        self.assertIn("供应商", PROCUREMENT_GROUPS["supply_side"])
        self.assertIn("采购", PROCUREMENT_GROUPS["supply_side"])
        self.assertIn("广告组", MEDIA_GROUPS["campaign_structure"])
        self.assertIn("曝光", MEDIA_GROUPS["delivery_scale"])
        self.assertIn("消耗", MEDIA_GROUPS["click_efficiency"])
        self.assertIn("转化", MEDIA_GROUPS["conversion_outcome"])

        flattened_tokens = []
        flattened_tokens.extend(ECOMMERCE_PLATFORM_TOKENS)
        for groups in (ECOMMERCE_GROUPS, PROCUREMENT_GROUPS, MEDIA_GROUPS):
            for values in groups.values():
                flattened_tokens.extend(values)

        common_mojibake_fragments = ("鍟", "娣", "閿", "搴", "鍗", "渚", "绫", "璁", "璺", "鐢")
        joined_tokens = " ".join(flattened_tokens)
        for fragment in common_mojibake_fragments:
            self.assertNotIn(fragment, joined_tokens)

    def test_routes_internet_operations_report_from_ops_fields(self) -> None:
        frame = pd.DataFrame(
            columns=["user_id", "DAU", "retention", "channel", "content_id", "conversion"]
        )
        result = route_business_profile(frame, dataset_name="ops-demo")
        self.assertEqual(result["business_profile"], "internet_operations_report")
        self.assertGreaterEqual(result["confidence"], 0.65)
        self.assertEqual(result["profile_entrypoint"], "internet_operations_report_profile")

    def test_routes_procurement_sales_report_from_procurement_fields(self) -> None:
        frame = pd.DataFrame(columns=["SKU", "supplier", "inventory", "gross_margin"])
        result = route_business_profile(frame, dataset_name="procurement-demo")
        self.assertEqual(result["business_profile"], "procurement_sales_report")
        self.assertGreaterEqual(result["confidence"], 0.65)
        self.assertEqual(result["profile_entrypoint"], "procurement_sales_report_profile")

    def test_routes_generic_when_confidence_is_low(self) -> None:
        frame = pd.DataFrame(columns=["alpha", "beta", "gamma"])
        result = route_business_profile(frame, dataset_name="generic-demo")
        self.assertEqual(result["business_profile"], "generic_business_report")
        self.assertLess(result["confidence"], 0.65)

    def test_runtime_policy_prefers_business_profile_over_shared_lens(self) -> None:
        policy = runtime_policy_for_report(
            business_profile="generic_long_business_report",
            report_lens="mixed_business_review",
        )
        self.assertIn("page_plan", policy["runtime_first_stages"])
        self.assertIn("page_generation", policy["runtime_first_stages"])
        self.assertTrue(
            runtime_stage_enabled(
                "final_polish",
                business_profile="generic_long_business_report",
                report_lens="mixed_business_review",
            )
        )

    def test_runtime_policy_uses_lens_fallback_for_management_accounting(self) -> None:
        policy = runtime_policy_for_report(
            business_profile="",
            report_lens="management_accounting_review",
        )
        self.assertEqual(policy["policy_name"], "management_accounting_runtime_selective")
        self.assertIn("background", policy["runtime_first_stages"])
        self.assertIn("metric_interpretation", policy["runtime_first_stages"])
        self.assertFalse(
            runtime_stage_enabled(
                "semantic",
                business_profile="",
                report_lens="management_accounting_review",
            )
        )

    @patch("app.services.orchestration_service.build_market_intelligence")
    @patch("app.services.orchestration_service.codex_statistical_scope")
    @patch("app.services.orchestration_service.build_analysis_program")
    @patch("app.services.orchestration_service.route_business_context_with_ai")
    @patch("app.services.orchestration_service.map_fields_with_ai")
    @patch("app.services.orchestration_service.build_workflow_blueprint")
    @patch("app.services.orchestration_service.load_dataset_frame")
    @patch("app.services.orchestration_service.load_dataset_metadata")
    def test_orchestration_forces_router_before_program_build(
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
        frame = pd.DataFrame(
            {
                "user_id": [1, 2],
                "DAU": [100, 110],
                "retention": [0.4, 0.42],
                "channel": ["organic", "paid"],
                "content_id": ["c1", "c2"],
                "conversion": [0.11, 0.12],
            }
        )
        metadata = {
            "name": "运营数据集",
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
            inferred_business_context="互联网运营场景",
            object_grain="user_day",
            time_grain="day",
            field_mappings=[],
            uncertain_fields=[],
            provider="OpenAI",
            model="gpt-5.4",
            trace_id="trace-semantic-001",
        )
        mock_ai_router.return_value = AIBusinessRoutingResult(
            selected_by_user=None,
            ai_route="internet_operations_report",
            final_route="internet_operations_report",
            confidence=0.92,
            alternative_routes=["generic_long_business_report"],
            reason="user/day/retention signals dominate",
            blocked_routes=[],
            trace_id="trace-route-001",
        )

        def _program_side_effect(routed_request: SmartReportRequest, *_args):
            self.assertEqual(routed_request.business_profile, "internet_operations_report")
            return {
                "frame": frame,
                "task_model": {"primary_family": "sales_review", "problem": "判断增长表现"},
                "object_candidates": [{"object_type": "internet_operations_log"}],
                "resolved_request_payload": {"problem_to_solve": "判断增长表现"},
                "program": {"core_outcomes": ["DAU"], "explanatory_slices": ["channel"], "cannot_analyze": []},
                "experts": [{"expert": "增长分析师"}],
                "hypotheses": [{"title": "internet_operations_log"}, {"title": "backup"}],
            }

        mock_program.side_effect = _program_side_effect
        mock_scope.return_value = {"keep_numeric_columns": ["DAU", "conversion"], "exclude_numeric_columns": []}
        mock_market.return_value = {"ready": False}

        result = build_report_orchestration("demo", SmartReportRequest())
        self.assertEqual(result["business_profile_router"]["business_profile"], "internet_operations_report")
        self.assertEqual(result["business_profile_router"]["profile_entrypoint"], "internet_operations_report_profile")
        self.assertEqual(result["request"].business_profile, "internet_operations_report")


if __name__ == "__main__":
    unittest.main()
