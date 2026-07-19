from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.services.ecommerce_product_operations_service import (
    build_ecommerce_product_operations_analysis_modules,
    ecommerce_field_availability_registry,
    ecommerce_field_semantic_interpreter,
    ecommerce_text_boundary_failures,
    product_operations_analysis_modules,
    write_ecommerce_registry_artifacts,
)


class EcommerceFieldRegistryTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "item_id": ["i1", "i2", "i3"],
                "sku_id": ["s1", "s2", "s3"],
                "shop_id": ["shop-a", "shop-b", "shop-a"],
                "category": ["beauty", "phone", "beauty"],
                "price": [29.9, 199.0, 59.0],
                "sales_volume": [100, 30, 50],
                "GMV": [2990, 5970, 2950],
                "inventory": [20, 5, 18],
                "fulfillment_rate": [0.98, 0.94, 0.96],
                "refund_rate": [0.03, 0.08, 0.04],
                "review_count": [12, 5, 8],
                "rating": [4.8, 4.2, 4.6],
                "PV": [1000, 800, 950],
                "add_to_cart": [120, 60, 80],
                "pay": [40, 10, 20],
                "activity_id": ["a1", "a1", "a2"],
                "date": ["2026-04-01", "2026-04-02", "2026-04-03"],
            }
        )

    def test_ecommerce_registry_detects_field_groups(self) -> None:
        registry = ecommerce_field_availability_registry(self._frame())
        self.assertEqual(registry["business_profile"], "ecommerce_product_operations_report")
        self.assertTrue(registry["has_product_fields"])
        self.assertTrue(registry["has_category_fields"])
        self.assertTrue(registry["has_shop_seller_fields"])
        self.assertTrue(registry["has_transaction_fields"])
        self.assertTrue(registry["has_price_fields"])
        self.assertTrue(registry["has_traffic_fields"])
        self.assertTrue(registry["has_conversion_fields"])
        self.assertTrue(registry["has_inventory_fields"])
        self.assertTrue(registry["has_review_fields"])
        self.assertTrue(registry["has_aftersales_fields"])
        self.assertTrue(registry["has_time_fields"])
        self.assertIn(registry["report_mode"], {
            "full_ecommerce_product_operations_report",
            "product_sales_review",
            "category_performance_review",
            "traffic_conversion_review",
            "inventory_fulfillment_review",
            "review_aftersales_review",
            "margin_profit_review",
        })

    def test_semantic_interpreter_outputs_rows(self) -> None:
        registry = ecommerce_field_availability_registry(self._frame())
        semantic = ecommerce_field_semantic_interpreter(self._frame(), registry)
        self.assertEqual(semantic["business_profile"], "ecommerce_product_operations_report")
        self.assertTrue(semantic["rows"])
        sample = next(row for row in semantic["rows"] if row["field_name"] == "item_id")
        self.assertIn("field_group", sample)
        self.assertIn("sample_values", sample)
        self.assertIn("missing_ratio", sample)
        self.assertIn("unique_count", sample)

    def test_product_modules_only_read_registry(self) -> None:
        registry = ecommerce_field_availability_registry(self._frame())
        semantic = ecommerce_field_semantic_interpreter(self._frame(), registry)
        modules = build_ecommerce_product_operations_analysis_modules(self._frame(), registry, semantic)
        wrapped = product_operations_analysis_modules(self._frame(), registry, semantic)
        self.assertEqual(set(modules.keys()), set(wrapped.keys()))
        self.assertIn("ecommerce_overview_analyzer", modules)
        self.assertIn("traffic_conversion_analyzer", modules)

    def test_boundary_failures_detect_missing_field_overreach(self) -> None:
        registry = ecommerce_field_availability_registry(self._frame())
        registry["has_margin_cost_fields"] = False
        registry["has_inventory_fields"] = False
        text = "当前毛利和 ROI 很高，适合补货放量。"
        failures = ecommerce_text_boundary_failures(text, registry)
        self.assertTrue(any("missing_margin_cost_fields" in item for item in failures))
        self.assertTrue(any("missing_inventory_fields" in item for item in failures))

    def test_registry_artifacts_are_written(self) -> None:
        registry = ecommerce_field_availability_registry(self._frame())
        semantic = ecommerce_field_semantic_interpreter(self._frame(), registry)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_ecommerce_registry_artifacts(output_dir, registry, semantic)
            self.assertTrue((output_dir / "ecommerce_field_availability_registry.json").exists())
            self.assertTrue((output_dir / "ecommerce_field_semantic_map.json").exists())
            self.assertTrue((output_dir / "ecommerce_field_semantic_map.md").exists())
            loaded = json.loads((output_dir / "ecommerce_field_availability_registry.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded["business_profile"], "ecommerce_product_operations_report")


if __name__ == "__main__":
    unittest.main()
