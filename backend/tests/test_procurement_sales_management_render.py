from __future__ import annotations

import unittest

from _procurement_sales_fixture import procurement_sales_frame
from app.services.procurement_sales_render_guard_service import report_quality_scorer, strict_quality_gate
from app.services.report_service import (
    _final_procurement_sales_management_render,
    _procurement_sales_object_decision_registry,
    _report_markdown_cn,
)


class ProcurementSalesManagementRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        registry = _procurement_sales_object_decision_registry(procurement_sales_frame())
        cls.payload = _final_procurement_sales_management_render(
            {
                "title": "Anonymous procurement sales fixture",
                "report_lens": "procurement_sales_review",
                "procurement_sales_readiness": {"report_mode": "sales_fulfillment_product_report"},
                "object_decision_registry": registry,
            }
        )
        cls.summary = "\n".join(cls.payload["executive_summary"])
        action_section = next(section for section in cls.payload["sections"] if section["id"] == "final_action_table")
        cls.action_table = action_section["tables"][0]
        cls.action_rows = cls.action_table["rows"]
        cls.payload.update(
            {
                "dataset_name": "anonymous-procurement-sales-fixture",
                "sheet_name": "Orders",
                "report_id": "public-render-fixture",
                "report_language": "zh-CN",
                "generated_at": "2026-07-20T00:00:00",
            }
        )

    def test_summary_has_five_nonempty_parts_without_legacy_objects(self) -> None:
        self.assertEqual(len(self.payload["executive_summary"]), 5)
        self.assertTrue(all(str(item).strip() for item in self.payload["executive_summary"]))
        for legacy_object in ["Health Beauty", "Telephony"]:
            self.assertNotIn(legacy_object, self.summary)

    def test_action_table_is_populated_and_matches_the_public_fixture(self) -> None:
        self.assertGreaterEqual(len(self.action_table["columns"]), 18)
        self.assertTrue(self.action_rows)
        rendered = " | ".join(
            str(value) for row in self.action_rows for value in row.values() if str(value).strip()
        )
        self.assertIn("Category A", rendered)
        self.assertNotIn("Health Beauty", rendered)
        self.assertNotIn("Telephony", rendered)
        self.assertTrue(self.payload["field_registry"])

    def test_management_render_passes_the_strict_quality_gate(self) -> None:
        result = strict_quality_gate(
            management_markdown=_report_markdown_cn(self.payload),
            total_pages=18,
            field_registry=self.payload["field_registry"],
            action_rows=self.payload["action_rows"],
        )
        self.assertTrue(result["passed"], msg=str(result))

    def test_management_render_scores_at_least_90(self) -> None:
        gate = strict_quality_gate(
            management_markdown=_report_markdown_cn(self.payload),
            total_pages=18,
            field_registry=self.payload["field_registry"],
            action_rows=self.payload["action_rows"],
        )
        score = report_quality_scorer(
            management_markdown=_report_markdown_cn(self.payload),
            field_registry=self.payload["field_registry"],
            action_rows=self.payload["action_rows"],
            strict_gate_result=gate,
            downloadable_names=[
                "management_report.pdf",
                "quality_gate_result.json",
                "report_quality_score.json",
                "blocked_action_log.csv",
                "object_decision_registry.csv",
                "field_availability_registry.json",
                "before_after_summary.md",
                "analyst_appendix.pdf",
            ],
        )
        self.assertGreaterEqual(score["score"], 90, msg=str(score))


if __name__ == "__main__":
    unittest.main()
