from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.services.ecommerce_action_roadmap_renderer import (
    build_ecommerce_action_roadmap,
    write_ecommerce_action_roadmap_artifacts,
)
from app.services.ecommerce_product_operations_service import (
    build_ecommerce_object_decision_registry,
    build_ecommerce_product_operations_analysis_modules,
    ecommerce_field_availability_registry,
    ecommerce_field_semantic_interpreter,
)


class EcommerceActionRoadmapRendererTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        rows = []
        shops = ["淘宝旗舰店", "天猫直营店", "京东自营", "拼多多店铺"]
        categories = ["护肤", "手机", "家清", "服饰"]
        brands = ["品牌A", "品牌B", "品牌C", "品牌D"]
        for i in range(200):
            rows.append(
                {
                    "item_id": f"item-{i % 24}",
                    "sku_id": f"sku-{i % 36}",
                    "spu_id": f"spu-{i % 18}",
                    "shop_id": shops[i % len(shops)],
                    "brand": brands[i % len(brands)],
                    "category": categories[i % len(categories)],
                    "price": 49 + (i % 11) * 10,
                    "sales_volume": 20 + (i % 30),
                    "GMV": 1500 + (i % 40) * 80,
                    "order_count": 10 + (i % 25),
                    "inventory": 5 + (i % 50),
                    "fulfillment_rate": 0.90 + ((i % 8) * 0.01),
                    "refund_rate": 0.01 + ((i % 6) * 0.01),
                    "review_count": 6 + (i % 12),
                    "rating": 4.0 + ((i % 8) * 0.1),
                    "PV": 300 + (i % 120),
                    "UV": 100 + (i % 70),
                    "click": 40 + (i % 25),
                    "add_to_cart": 12 + (i % 10),
                    "pay": 9 + (i % 8),
                    "gross_margin": 0.15 + ((i % 10) * 0.02),
                    "ad_cost": 60 + (i % 15) * 10,
                    "activity_id": f"act-{i % 5}",
                    "date": f"2026-04-{(i % 20) + 1:02d}",
                }
            )
        return pd.DataFrame(rows)

    def test_roadmap_outputs_required_tables(self) -> None:
        frame = self._frame()
        field_registry = ecommerce_field_availability_registry(frame)
        semantic_map = ecommerce_field_semantic_interpreter(frame, field_registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, field_registry, semantic_map)
        registry = build_ecommerce_object_decision_registry(modules, field_registry)
        roadmap = build_ecommerce_action_roadmap(registry, field_registry)
        self.assertIn("seven_day_ecommerce_action_table", roadmap)
        self.assertIn("thirty_day_ecommerce_experiment_backlog", roadmap)
        self.assertIn("forbidden_judgement_rows", roadmap)
        self.assertTrue(roadmap["seven_day_ecommerce_action_table"])
        self.assertTrue(roadmap["thirty_day_ecommerce_experiment_backlog"])

    def test_seven_day_action_rows_have_required_columns(self) -> None:
        frame = self._frame()
        field_registry = ecommerce_field_availability_registry(frame)
        semantic_map = ecommerce_field_semantic_interpreter(frame, field_registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, field_registry, semantic_map)
        registry = build_ecommerce_object_decision_registry(modules, field_registry)
        roadmap = build_ecommerce_action_roadmap(registry, field_registry)
        row = roadmap["seven_day_ecommerce_action_table"][0]
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
        field_registry = ecommerce_field_availability_registry(frame)
        semantic_map = ecommerce_field_semantic_interpreter(frame, field_registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, field_registry, semantic_map)
        registry = build_ecommerce_object_decision_registry(modules, field_registry)
        roadmap = build_ecommerce_action_roadmap(registry, field_registry)
        row = roadmap["thirty_day_ecommerce_experiment_backlog"][0]
        required = {
            "实验编号",
            "实验假设",
            "目标对象",
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

    def test_writer_outputs_required_csv_files(self) -> None:
        frame = self._frame()
        field_registry = ecommerce_field_availability_registry(frame)
        semantic_map = ecommerce_field_semantic_interpreter(frame, field_registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, field_registry, semantic_map)
        registry = build_ecommerce_object_decision_registry(modules, field_registry)
        roadmap = build_ecommerce_action_roadmap(registry, field_registry)
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result = write_ecommerce_action_roadmap_artifacts(out_dir, roadmap)
            self.assertTrue((out_dir / "7_day_ecommerce_action_table.csv").exists())
            self.assertTrue((out_dir / "30_day_ecommerce_experiment_backlog.csv").exists())
            self.assertTrue(Path(result["seven_day_csv"]).exists())
            self.assertTrue(Path(result["thirty_day_backlog_csv"]).exists())


if __name__ == "__main__":
    unittest.main()
