from __future__ import annotations

import re
import unittest
from pathlib import Path

from app.services.dataset_service import load_dataset_frame
from app.services.procurement_sales_profile_service import inference_without_direct_data_controller
from app.services.report_service import _procurement_sales_object_decision_registry


def _resolve_frame(dataset_id: str):
    loaded = load_dataset_frame(dataset_id)
    if isinstance(loaded, tuple):
        for item in loaded:
            if hasattr(item, "columns"):
                return item
    return loaded


def _registry_row(rows: list[dict], object_id: str) -> dict:
    for row in rows:
        if str(row.get("object_id") or "") == object_id:
            return row
    raise AssertionError(f"object not found in registry: {object_id}")


class ProcurementSalesRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        frame = _resolve_frame("6490e1d9994d")
        cls.registry = _procurement_sales_object_decision_registry(frame)
        cls.rows = cls.registry["rows"]

    def test_sku_7663_is_not_cleared(self) -> None:
        row = _registry_row(self.rows, "SKU（尾号7663）")
        self.assertEqual(row["final_label"], "低样本规格复核")
        self.assertEqual(row["final_action"], "待补库存后判断")
        self.assertNotEqual(row["final_action"], "清理退场")

    def test_health_beauty_is_not_resource_tilt(self) -> None:
        row = _registry_row(self.rows, "Health Beauty")
        self.assertEqual(row["final_label"], "头部品类资源候选")
        self.assertEqual(row["final_action"], "待补毛利、库存、退货成本后判断是否加码")
        self.assertNotEqual(row["final_action"], "资源倾斜")

    def test_telephony_product_is_not_core_push(self) -> None:
        row = _registry_row(self.rows, "Telephony 商品（尾号48a9）")
        self.assertEqual(row["final_label"], "修复型销售头部")
        self.assertEqual(row["final_action"], "差评归因 + 履约修复 + 待补毛利后判断是否放量")
        self.assertNotEqual(row["final_action"], "核心主推")

    def test_registry_contains_inference_fields(self) -> None:
        row = _registry_row(self.rows, "Health Beauty")
        self.assertIn("conclusion_type", row)
        self.assertIn("missing_fields", row)
        self.assertIn("validation_plan", row)
        self.assertIn("confidence_level", row)

    def test_inference_without_direct_data_controller_downgrades_to_proxy_or_hypothesis(self) -> None:
        inference = inference_without_direct_data_controller(
            object_level="product",
            object_id="Telephony 商品（尾号48a9）",
            candidate_label="修复型销售头部",
            candidate_action="差评归因 + 履约修复 + 待补毛利后判断是否放量",
            evidence={"avg_fulfillment_days": 11.82},
            field_availability_registry=self.registry["field_registry"],
            sample_size={"order_count": 64, "customer_count": 61, "review_count": 64},
            risk_metrics={"low_rating_rate": 0.247, "late_rate": 0.1},
        )
        self.assertIn(inference["conclusion_type"], {"proxy_based_inference", "business_hypothesis"})
        self.assertTrue(inference["missing_fields"])
        self.assertTrue(inference["validation_plan"])

    def test_low_sample_inference_is_risk_flag(self) -> None:
        inference = inference_without_direct_data_controller(
            object_level="sku",
            object_id="SKU（尾号7663）",
            candidate_label="低样本规格复核",
            candidate_action="待补库存后判断",
            evidence={"avg_fulfillment_days": 9.0},
            field_availability_registry=self.registry["field_registry"],
            sample_size={"order_count": 5, "customer_count": 5, "review_count": 5},
            risk_metrics={"low_rating_rate": 0.0, "late_rate": 0.0},
        )
        self.assertEqual(inference["conclusion_type"], "risk_flag")
        self.assertEqual(inference["confidence_level"], "low")


if __name__ == "__main__":
    unittest.main()


class ProcurementSalesRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        frame = _resolve_frame("6490e1d9994d")
        cls.registry = _procurement_sales_object_decision_registry(frame)
        cls.rows = cls.registry["rows"]

    def test_registry_no_longer_contains_demo_object_overrides(self) -> None:
        from app.services import procurement_sales_profile_service as service

        self.assertEqual(service.HARD_OBJECT_OVERRIDES, {})

    def test_no_demo_objects_in_production_services(self) -> None:
        services_dir = Path(__file__).resolve().parents[1] / "app" / "services"
        source = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in services_dir.rglob("*.py"))
        for token in [
            "Health Beauty",
            "Telephony 商品",
            "尾号48a9",
            "尾号7663",
            "SKU（尾号7663）",
        ]:
            self.assertNotIn(token, source)

    def test_procurement_management_entrypoints_are_unique(self) -> None:
        report_service_path = Path(__file__).resolve().parents[1] / "app" / "services" / "report_service.py"
        source = report_service_path.read_text(encoding="utf-8", errors="ignore")
        for name in [
            "_management_safe_registry_rows",
            "_management_summary_from_registry",
            "_procurement_sales_management_render",
            "_final_procurement_sales_management_render",
        ]:
            matches = re.findall(rf"^def {re.escape(name)}\b", source, flags=re.MULTILINE)
            self.assertEqual(matches, [f"def {name}"])

    def test_registry_contains_inference_fields(self) -> None:
        row = next((item for item in self.rows if item.get("conclusion_type")), None)
        self.assertIsNotNone(row)
        assert row is not None
        self.assertIn("conclusion_type", row)
        self.assertIn("missing_fields", row)
        self.assertIn("validation_plan", row)
        self.assertIn("confidence_level", row)

    def test_inference_without_direct_data_controller_downgrades_to_proxy_or_hypothesis(self) -> None:
        inference = inference_without_direct_data_controller(
            object_level="product",
            object_id="sample_product",
            candidate_label="淇鍨嬮攢鍞ご閮?",
            candidate_action="宸瘎褰掑洜 + 灞ョ害淇 + 寰呰ˉ姣涘埄鍚庡垽鏂槸鍚︽斁閲?",
            evidence={"avg_fulfillment_days": 11.82},
            field_availability_registry=self.registry["field_registry"],
            sample_size={"order_count": 64, "customer_count": 61, "review_count": 64},
            risk_metrics={"low_rating_rate": 0.247, "late_rate": 0.1},
        )
        self.assertIn(inference["conclusion_type"], {"proxy_based_inference", "business_hypothesis", "evidence_based_decision"})
        self.assertIsInstance(inference["missing_fields"], list)
        self.assertTrue(inference["validation_plan"] or inference["conclusion_type"] == "evidence_based_decision")

    def test_low_sample_inference_is_risk_flag(self) -> None:
        inference = inference_without_direct_data_controller(
            object_level="sku",
            object_id="sample_sku",
            candidate_label="浣庢牱鏈鏍煎鏍?",
            candidate_action="寰呰ˉ搴撳瓨鍚庡垽鏂?",
            evidence={"avg_fulfillment_days": 9.0},
            field_availability_registry=self.registry["field_registry"],
            sample_size={"order_count": 5, "customer_count": 5, "review_count": 5},
            risk_metrics={"low_rating_rate": 0.0, "late_rate": 0.0},
        )
        self.assertEqual(inference["conclusion_type"], "risk_flag")
        self.assertEqual(inference["confidence_level"], "low")
