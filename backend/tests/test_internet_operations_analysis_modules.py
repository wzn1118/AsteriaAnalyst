from __future__ import annotations

import unittest

import pandas as pd

from app.services.internet_operations_analysis_modules import build_internet_operations_analysis_modules
from app.services.internet_ops_profile_service import internet_ops_field_availability_registry


class InternetOperationsAnalysisModulesTests(unittest.TestCase):
    def test_all_modules_emit_required_fields(self) -> None:
        frame = pd.DataFrame(
            {
                "user_id": [1, 2, 3],
                "DAU": [100, 120, 130],
                "new_user": [20, 24, 25],
                "retention": [0.3, 0.33, 0.35],
                "channel": ["organic", "paid", "organic"],
                "campaign_name": ["春促", "春促", "夏促"],
                "content_id": ["c1", "c2", "c3"],
                "like": [30, 40, 50],
                "conversion": [0.08, 0.09, 0.11],
                "cost": [100, 120, 130],
                "gmv": [800, 900, 1000],
                "bounce_rate": [0.2, 0.18, 0.16],
            }
        )
        registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, registry)
        self.assertEqual(len(modules), 13)
        for payload in modules.values():
            for key in [
                "module_id",
                "business_question",
                "core_conclusion",
                "evidence",
                "missing_fields",
                "action",
                "validation_metric",
                "object_level",
                "object_id",
                "conclusion_type",
                "confidence_level",
                "forbidden_actions",
                "recommended_validation_action",
                "owner_role",
                "time_requirement",
            ]:
                self.assertIn(key, payload)

    def test_insufficient_fields_do_not_force_conclusions(self) -> None:
        frame = pd.DataFrame(
            {
                "user_id": [1, 2],
                "DAU": [50, 60],
                "channel": ["organic", "paid"],
                "content_id": ["c1", "c2"],
                "like": [3, 5],
            }
        )
        registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, registry)

        self.assertIn("revenue_fields", modules["monetization_analyzer"]["missing_fields"])
        self.assertIn("不能判断商业价值", modules["monetization_analyzer"]["core_conclusion"])

        self.assertEqual(modules["campaign_operations_analyzer"]["status"], "skipped")
        self.assertIn("campaign_fields", modules["campaign_operations_analyzer"]["missing_fields"])

        self.assertIn("retention_fields", modules["retention_cohort_analyzer"]["missing_fields"])
        self.assertIn("需先补", modules["retention_cohort_analyzer"]["core_conclusion"])


if __name__ == "__main__":
    unittest.main()
