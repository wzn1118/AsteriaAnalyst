from __future__ import annotations

import unittest

from app.services.internet_ops_profile_service import (
    internet_ops_action_guardrail,
    internet_ops_inference_controller,
)


class InternetOpsGuardrailTests(unittest.TestCase):
    def test_missing_cost_fields_blocks_roi_and_budget_actions(self) -> None:
        registry = {
            "has_cost_fields": False,
            "has_retention_fields": True,
            "has_revenue_fields": True,
            "has_funnel_fields": True,
            "has_channel_fields": True,
            "has_content_fields": True,
        }
        result = internet_ops_action_guardrail(
            object_level="channel",
            object_id="渠道A",
            candidate_label="渠道质量候选",
            candidate_action="加大投放",
            evidence={"conversion_rate": 0.12, "clicks": 1200},
            field_availability_registry=registry,
            sample_size={"user_count": 1000, "event_count": 5000},
        )
        self.assertTrue(result["blocked"])
        self.assertEqual(result["downgraded_action"], "待补成本后判断投放效率")
        self.assertIn("ROI最高", result["forbidden_actions"])
        self.assertNotEqual(result["action_strength"], "hard_action")

    def test_missing_retention_fields_cannot_claim_user_quality(self) -> None:
        registry = {
            "has_cost_fields": True,
            "has_retention_fields": False,
            "has_revenue_fields": True,
            "has_funnel_fields": True,
            "has_channel_fields": True,
            "has_content_fields": True,
        }
        result = internet_ops_action_guardrail(
            object_level="segment",
            object_id="用户分群A",
            candidate_label="短期活跃表现较好",
            candidate_action="用户质量高",
            evidence={"active_users": 5000, "conversion_rate": 0.08},
            field_availability_registry=registry,
            sample_size={"user_count": 5000, "event_count": 20000},
        )
        self.assertTrue(result["blocked"])
        self.assertIn("D1/D7/D30", result["conclusion"])
        self.assertIn("用户质量高", result["forbidden_actions"])

    def test_missing_revenue_fields_cannot_claim_business_value(self) -> None:
        registry = {
            "has_cost_fields": True,
            "has_retention_fields": True,
            "has_revenue_fields": False,
            "has_funnel_fields": True,
            "has_channel_fields": True,
            "has_content_fields": True,
        }
        result = internet_ops_action_guardrail(
            object_level="content",
            object_id="内容主题A",
            candidate_label="转化行为较强",
            candidate_action="商业化效率高",
            evidence={"conversion_rate": 0.18, "purchase_events": 320},
            field_availability_registry=registry,
            sample_size={"user_count": 3000, "event_count": 15000},
        )
        self.assertTrue(result["blocked"])
        self.assertIn("付费/GMV/ARPU/LTV", result["conclusion"])
        self.assertIn("商业化效率高", result["forbidden_actions"])

    def test_low_sample_object_is_downgraded(self) -> None:
        registry = {
            "has_cost_fields": True,
            "has_retention_fields": True,
            "has_revenue_fields": True,
            "has_funnel_fields": True,
            "has_channel_fields": True,
            "has_content_fields": True,
        }
        result = internet_ops_action_guardrail(
            object_level="channel",
            object_id="渠道B",
            candidate_label="增长观察对象",
            candidate_action="扩大投放",
            evidence={"conversion_rate": 0.22},
            field_availability_registry=registry,
            sample_size={"user_count": 50, "event_count": 200},
        )
        self.assertTrue(result["blocked"])
        self.assertIn(result["downgraded_action"], {"低样本观察", "低样本复核"})
        self.assertEqual(result["action_strength"], "observe_only")

    def test_inference_controller_outputs_required_fields(self) -> None:
        registry = {
            "has_cost_fields": False,
            "has_retention_fields": False,
            "has_revenue_fields": False,
            "has_funnel_fields": True,
            "has_channel_fields": True,
            "has_content_fields": True,
        }
        result = internet_ops_inference_controller(
            object_level="channel",
            object_id="渠道C",
            candidate_label="渠道流量质量候选",
            candidate_action="加大投放",
            evidence={"conversion_rate": 0.11, "active_users": 1800},
            field_availability_registry=registry,
            sample_size={"user_count": 1800, "event_count": 8200},
        )
        for key in [
            "object_level",
            "object_id",
            "evidence",
            "missing_fields",
            "conclusion",
            "conclusion_type",
            "confidence_level",
            "forbidden_actions",
            "recommended_validation_action",
            "validation_metric",
            "owner_role",
            "time_requirement",
        ]:
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
