from __future__ import annotations

import re
import unittest
from pathlib import Path

from _procurement_sales_fixture import procurement_sales_frame
from app.services.procurement_sales_profile_service import inference_without_direct_data_controller
from app.services.report_service import _procurement_sales_object_decision_registry


class ProcurementSalesRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = _procurement_sales_object_decision_registry(procurement_sales_frame())
        cls.rows = cls.registry["rows"]

    def test_registry_is_built_from_anonymous_fixture_rows(self) -> None:
        self.assertTrue(self.rows)
        rendered = "\n".join(str(row) for row in self.rows)
        for legacy_object in ["Health Beauty", "Telephony"]:
            self.assertNotIn(legacy_object, rendered)

    def test_registry_has_inference_boundary_fields(self) -> None:
        row = next((item for item in self.rows if item.get("conclusion_type")), None)
        self.assertIsNotNone(row)
        assert row is not None
        for field in ["conclusion_type", "missing_fields", "validation_plan", "confidence_level"]:
            self.assertIn(field, row)

    def test_registry_has_no_demo_object_override(self) -> None:
        from app.services import procurement_sales_profile_service as service

        self.assertEqual(service.HARD_OBJECT_OVERRIDES, {})

    def test_production_services_contain_no_legacy_demo_objects(self) -> None:
        services_dir = Path(__file__).resolve().parents[1] / "app" / "services"
        source = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in services_dir.rglob("*.py"))
        for token in ["Health Beauty", "Telephony"]:
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

    def test_missing_direct_data_downgrades_to_a_bounded_conclusion(self) -> None:
        inference = inference_without_direct_data_controller(
            object_level="product",
            object_id="anonymous-product",
            candidate_label="test label",
            candidate_action="test action",
            evidence={"avg_fulfillment_days": 11.82},
            field_availability_registry=self.registry["field_registry"],
            sample_size={"order_count": 64, "customer_count": 61, "review_count": 64},
            risk_metrics={"low_rating_rate": 0.247, "late_rate": 0.1},
        )
        self.assertIn(
            inference["conclusion_type"],
            {"proxy_based_inference", "business_hypothesis", "evidence_based_decision"},
        )
        self.assertIsInstance(inference["missing_fields"], list)
        self.assertTrue(inference["validation_plan"] or inference["conclusion_type"] == "evidence_based_decision")

    def test_low_sample_inference_is_a_risk_flag(self) -> None:
        inference = inference_without_direct_data_controller(
            object_level="sku",
            object_id="anonymous-sku",
            candidate_label="test label",
            candidate_action="test action",
            evidence={"avg_fulfillment_days": 9.0},
            field_availability_registry=self.registry["field_registry"],
            sample_size={"order_count": 5, "customer_count": 5, "review_count": 5},
            risk_metrics={"low_rating_rate": 0.0, "late_rate": 0.0},
        )
        self.assertEqual(inference["conclusion_type"], "risk_flag")
        self.assertEqual(inference["confidence_level"], "low")


if __name__ == "__main__":
    unittest.main()
