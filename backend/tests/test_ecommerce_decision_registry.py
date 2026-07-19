from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.services.ecommerce_product_operations_service import (
    build_ecommerce_object_decision_registry,
    build_ecommerce_product_operations_analysis_modules,
    ecommerce_field_availability_registry,
    ecommerce_field_semantic_interpreter,
    render_ecommerce_action_table,
    write_ecommerce_decision_registry_artifacts,
)


class EcommerceDecisionRegistryTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "item_id": ["i1", "i2", "i3", "i1"],
                "sku_id": ["s1", "s2", "s3", "s1"],
                "spu_id": ["spu1", "spu2", "spu3", "spu1"],
                "shop_id": ["shop-a", "shop-b", "shop-a", "shop-a"],
                "brand": ["brand-a", "brand-b", "brand-a", "brand-a"],
                "category": ["beauty", "phone", "beauty", "beauty"],
                "price": [29.9, 199.0, 59.0, 35.0],
                "sales_volume": [100, 30, 50, 40],
                "GMV": [2990, 5970, 2950, 1400],
                "order_count": [40, 10, 20, 12],
                "inventory": [20, 5, 18, 30],
                "fulfillment_rate": [0.98, 0.94, 0.96, 0.93],
                "refund_rate": [0.03, 0.08, 0.04, 0.06],
                "review_count": [12, 5, 8, 4],
                "rating": [4.8, 4.2, 4.6, 4.1],
                "PV": [1000, 800, 950, 700],
                "UV": [400, 300, 350, 260],
                "click": [120, 60, 80, 50],
                "add_to_cart": [60, 20, 30, 15],
                "pay": [40, 10, 20, 12],
                "gross_margin": [0.35, 0.18, 0.28, 0.20],
                "ad_cost": [200, 500, 240, 180],
                "activity_id": ["a1", "a1", "a2", "a2"],
                "date": ["2026-04-01", "2026-04-02", "2026-04-03", "2026-04-04"],
            }
        )

    def test_registry_rows_have_fixed_fields(self) -> None:
        frame = self._frame()
        registry = ecommerce_field_availability_registry(frame)
        semantic = ecommerce_field_semantic_interpreter(frame, registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, registry, semantic)
        decision_registry = build_ecommerce_object_decision_registry(modules, registry)
        self.assertTrue(decision_registry["rows"])
        row = decision_registry["rows"][0]
        for key in [
            "business_profile",
            "object_level",
            "object_id",
            "object_name",
            "final_label",
            "final_action",
            "action_strength",
            "conclusion_type",
            "confidence_level",
            "evidence_summary",
            "missing_fields",
            "blocked_actions",
            "blocked_reason",
            "sample_size_flag",
            "owner_role",
            "time_requirement",
            "validation_metric",
            "success_criteria",
        ]:
            self.assertIn(key, row)

    def test_action_table_has_fixed_columns(self) -> None:
        frame = self._frame()
        registry = ecommerce_field_availability_registry(frame)
        semantic = ecommerce_field_semantic_interpreter(frame, registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, registry, semantic)
        decision_registry = build_ecommerce_object_decision_registry(modules, registry)
        action_rows = render_ecommerce_action_table(decision_registry)
        self.assertTrue(action_rows)
        row = action_rows[0]
        for key in [
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
        ]:
            self.assertIn(key, row)

    def test_writes_decision_registry_artifacts(self) -> None:
        frame = self._frame()
        registry = ecommerce_field_availability_registry(frame)
        semantic = ecommerce_field_semantic_interpreter(frame, registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, registry, semantic)
        decision_registry = build_ecommerce_object_decision_registry(modules, registry)
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            write_ecommerce_decision_registry_artifacts(out_dir, decision_registry)
            self.assertTrue((out_dir / "ecommerce_object_decision_registry.csv").exists())
            self.assertTrue((out_dir / "ecommerce_action_table.csv").exists())
            self.assertTrue((out_dir / "ecommerce_conflicting_actions_check.json").exists())
            self.assertTrue((out_dir / "ecommerce_guardrail_result.json").exists())
            conflict_payload = json.loads((out_dir / "ecommerce_conflicting_actions_check.json").read_text(encoding="utf-8"))
            self.assertIn("passed", conflict_payload)
            self.assertIn("conflicting_object_actions", conflict_payload)


if __name__ == "__main__":
    unittest.main()
