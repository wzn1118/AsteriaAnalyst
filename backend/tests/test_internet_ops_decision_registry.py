from __future__ import annotations

import unittest

import pandas as pd

from app.services.internet_operations_analysis_modules import build_internet_operations_analysis_modules
from app.services.internet_ops_decision_registry_service import (
    build_internet_ops_object_decision_registry,
    render_internet_ops_action_table,
)
from app.services.internet_ops_profile_service import internet_ops_field_availability_registry


class InternetOpsDecisionRegistryTests(unittest.TestCase):
    def test_registry_enforces_unique_final_action_per_object(self) -> None:
        frame = pd.DataFrame(
            {
                "user_id": list(range(1, 601)),
                "DAU": [100 + (i % 20) for i in range(600)],
                "new_user": [12 + (i % 5) for i in range(600)],
                "retention": [0.25 + ((i % 5) * 0.01) for i in range(600)],
                "channel": ["organic", "paid", "social", "search"] * 150,
                "campaign_name": ["春促", "夏促", "会员日"] * 200,
                "content_id": ["c1", "c2", "c3", "c4", "c5"] * 120,
                "like": [5 + (i % 4) for i in range(600)],
                "comment": [2 + (i % 3) for i in range(600)],
                "share": [1 + (i % 2) for i in range(600)],
                "conversion": [0.05 + ((i % 4) * 0.01) for i in range(600)],
                "cost": [20 + (i % 8) for i in range(600)],
                "gmv": [120 + (i % 30) for i in range(600)],
            }
        )
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        self.assertEqual(registry["business_profile"], "internet_operations_report")
        self.assertEqual(registry["conflicting_object_actions"], [])
        seen = {}
        for row in registry["rows"]:
            key = row["object_id"]
            value = (row["final_label"], row["final_action"])
            self.assertNotIn(key, seen)
            seen[key] = value

    def test_channel_missing_cost_cannot_output_budget_action(self) -> None:
        frame = pd.DataFrame(
            {
                "user_id": list(range(1, 601)),
                "DAU": [100 + (i % 20) for i in range(600)],
                "channel": ["organic", "paid"] * 300,
                "conversion": [0.08 + ((i % 2) * 0.01) for i in range(600)],
            }
        )
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        row = next(item for item in registry["rows"] if item["object_id"] == "channel_portfolio")
        self.assertEqual(row["final_label"], "成本待补渠道")
        self.assertNotIn("预算", row["final_action"])
        self.assertNotIn("砍", row["final_action"])

    def test_user_missing_revenue_cannot_output_high_value_user(self) -> None:
        frame = pd.DataFrame(
            {
                "user_id": list(range(1, 601)),
                "DAU": [100 + (i % 20) for i in range(600)],
                "new_user": [10 + (i % 3) for i in range(600)],
                "retention": [0.2 + ((i % 4) * 0.01) for i in range(600)],
            }
        )
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        row = next(item for item in registry["rows"] if item["object_id"] == "monetization_users")
        self.assertNotIn("高价值用户", row["final_label"])
        self.assertEqual(row["final_label"], "付费潜力待验证用户群")

    def test_low_sample_object_only_outputs_low_sample_action(self) -> None:
        frame = pd.DataFrame(
            {
                "user_id": [1, 2, 3, 4, 5],
                "DAU": [10, 12, 8, 15, 11],
                "channel": ["organic", "paid", "social", "search", "organic"],
                "conversion": [0.05, 0.03, 0.02, 0.04, 0.03],
            }
        )
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        row = next(item for item in registry["rows"] if item["object_id"] == "channel_portfolio")
        self.assertIn(row["final_label"], {"低样本渠道复核", "低样本复核"})
        self.assertIn(row["final_action"], {"低样本复核", "低样本观察"})

    def test_action_table_has_required_columns(self) -> None:
        frame = pd.DataFrame(
            {
                "user_id": list(range(1, 601)),
                "DAU": [100 + (i % 20) for i in range(600)],
                "channel": ["organic", "paid"] * 300,
                "conversion": [0.08 + ((i % 2) * 0.01) for i in range(600)],
            }
        )
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        rows = render_internet_ops_action_table(registry)
        self.assertTrue(rows)
        required = {
            "优先级",
            "对象层级",
            "对象名称",
            "最终标签",
            "触发证据",
            "现有证据类型",
            "缺失字段",
            "被拦截动作",
            "最终动作",
            "负责人角色",
            "时间要求",
            "验证指标",
            "成功标准",
            "结论强度",
            "置信度",
        }
        self.assertTrue(required.issubset(rows[0].keys()))


if __name__ == "__main__":
    unittest.main()
