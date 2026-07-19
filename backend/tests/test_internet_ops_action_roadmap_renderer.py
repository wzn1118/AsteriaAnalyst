from __future__ import annotations

import unittest

import pandas as pd

from app.services.internet_ops_action_roadmap_renderer import build_internet_ops_action_roadmap
from app.services.internet_operations_analysis_modules import build_internet_operations_analysis_modules
from app.services.internet_ops_decision_registry_service import build_internet_ops_object_decision_registry
from app.services.internet_ops_profile_service import internet_ops_field_availability_registry


class InternetOpsActionRoadmapRendererTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        rows = []
        channels = ["organic", "paid", "social", "search"]
        campaigns = ["春促", "夏促", "会员日"]
        contents = ["c1", "c2", "c3", "c4", "c5"]
        for i in range(600):
            rows.append(
                {
                    "user_id": i + 1,
                    "DAU": 80 + (i % 25),
                    "new_user": 10 + (i % 9),
                    "retention": 0.22 + ((i % 7) * 0.01),
                    "channel": channels[i % len(channels)],
                    "campaign_name": campaigns[i % len(campaigns)],
                    "content_id": contents[i % len(contents)],
                    "like": 5 + (i % 6),
                    "comment": 2 + (i % 4),
                    "share": 1 + (i % 3),
                    "conversion": 0.04 + ((i % 5) * 0.01),
                    "cost": 20 + (i % 11),
                    "gmv": 120 + (i % 35),
                    "bounce_rate": 0.15 + ((i % 4) * 0.01),
                }
            )
        return pd.DataFrame(rows)

    def test_roadmap_outputs_required_tables(self) -> None:
        frame = self._frame()
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        roadmap = build_internet_ops_action_roadmap(registry, field_registry)
        self.assertIn("seven_day_action_table", roadmap)
        self.assertIn("thirty_day_growth_experiment_backlog", roadmap)
        self.assertIn("forbidden_judgement_rows", roadmap)
        self.assertTrue(roadmap["seven_day_action_table"])
        self.assertTrue(roadmap["thirty_day_growth_experiment_backlog"])

    def test_seven_day_action_rows_have_required_columns(self) -> None:
        frame = self._frame()
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        roadmap = build_internet_ops_action_roadmap(registry, field_registry)
        row = roadmap["seven_day_action_table"][0]
        required = {
            "优先级",
            "动作",
            "对象",
            "负责人角色",
            "输入数据",
            "产出结果",
            "截止时间",
            "验证标准",
            "护栏指标",
            "依赖字段",
            "当前结论强度",
        }
        self.assertTrue(required.issubset(row.keys()))

    def test_backlog_rows_have_required_columns(self) -> None:
        frame = self._frame()
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        roadmap = build_internet_ops_action_roadmap(registry, field_registry)
        row = roadmap["thirty_day_growth_experiment_backlog"][0]
        required = {
            "实验编号",
            "实验假设",
            "目标用户",
            "实验对象",
            "实验动作",
            "核心指标",
            "护栏指标",
            "样本要求",
            "数据依赖",
            "预计周期",
            "成功标准",
            "失败后处理",
            "结论类型",
        }
        self.assertTrue(required.issubset(row.keys()))


if __name__ == "__main__":
    unittest.main()
