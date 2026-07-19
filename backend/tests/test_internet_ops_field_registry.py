from __future__ import annotations

import unittest

import pandas as pd

from app.services.internet_ops_profile_service import (
    internet_ops_field_availability_registry,
    internet_ops_text_compliance_failures,
)
from app.services.report_service import (
    _ops_dimension_effect_section,
    _ops_activity_scorecard_section,
    _ops_channel_scorecard_section,
    _ops_content_scorecard_rows,
    _ops_topline_section,
)


class InternetOpsFieldRegistryTests(unittest.TestCase):
    def test_registry_detects_ops_field_groups(self) -> None:
        frame = pd.DataFrame(
            columns=[
                "user_id",
                "DAU",
                "retention",
                "channel",
                "content_id",
                "conversion",
                "like",
                "campaign_name",
                "region",
            ]
        )
        registry = internet_ops_field_availability_registry(frame)
        self.assertTrue(registry["has_user_fields"])
        self.assertTrue(registry["has_funnel_fields"])
        self.assertTrue(registry["has_retention_fields"])
        self.assertTrue(registry["has_content_fields"])
        self.assertTrue(registry["has_channel_fields"])
        self.assertTrue(registry["has_engagement_fields"])
        self.assertTrue(registry["has_campaign_fields"])
        self.assertIn(registry["report_mode"], {"growth_funnel_report", "content_operations_report", "app_website_operations_report"})

    def test_missing_cost_retention_revenue_fields_trigger_text_failures(self) -> None:
        registry = {
            "has_cost_fields": False,
            "has_retention_fields": False,
            "has_revenue_fields": False,
        }
        text = "当前 ROI 很高，用户黏性强，商业价值高，可以预算加码。"
        failures = internet_ops_text_compliance_failures(text, registry)
        self.assertIn("ROI", failures)
        self.assertIn("用户黏性强", failures)
        self.assertIn("商业价值高", failures)
        self.assertIn("预算加码", failures)

    def test_ops_sections_are_blocked_by_registry_when_field_group_missing(self) -> None:
        frame = pd.DataFrame(
            {
                "渠道": ["A", "B"],
                "活动": ["春促", "春促"],
                "内容主题": ["视频", "图文"],
                "活跃用户": [100, 120],
            }
        )
        self.assertIsNone(_ops_channel_scorecard_section(frame, {"has_channel_fields": False}))
        self.assertIsNone(_ops_activity_scorecard_section(frame, {"has_campaign_fields": False}))
        self.assertEqual(_ops_content_scorecard_rows(frame, {"has_content_fields": False}), [])
        self.assertIsNone(
            _ops_dimension_effect_section(
                "demo",
                frame,
                dimension_column="渠道",
                label="渠道",
                section_id="ops_channel_impact",
                field_registry={"has_channel_fields": False},
            )
        )
        self.assertIsNone(
            _ops_topline_section(
                frame,
                {
                    "has_user_fields": False,
                    "has_funnel_fields": False,
                    "has_retention_fields": False,
                    "has_revenue_fields": False,
                    "has_traffic_fields": False,
                },
            )
        )


if __name__ == "__main__":
    unittest.main()
