from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.models import SmartReportRequest
from app.services.ecommerce_action_roadmap_renderer import build_ecommerce_action_roadmap
from app.services.ecommerce_pdf_report_renderer import (
    build_ecommerce_appendix_variant,
    build_ecommerce_management_variant,
)
from app.services.ecommerce_product_operations_service import (
    build_ecommerce_object_decision_registry,
    build_ecommerce_product_operations_analysis_modules,
    ecommerce_field_availability_registry,
    ecommerce_field_semantic_interpreter,
    render_ecommerce_action_table,
)
from app.services.report_service import _downloadable_bundle_cn_ecommerce, _write_pdf_report_cn


class EcommercePdfRendererTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        rows = []
        shops = ["淘宝旗舰店", "天猫直营店", "京东自营", "拼多多店铺"]
        categories = ["护肤", "手机", "家清", "服饰"]
        brands = ["品牌A", "品牌B", "品牌C", "品牌D"]
        for i in range(420):
            rows.append(
                {
                    "item_id": f"item-{i % 48}",
                    "sku_id": f"sku-{i % 72}",
                    "spu_id": f"spu-{i % 30}",
                    "shop_id": shops[i % len(shops)],
                    "brand": brands[i % len(brands)],
                    "category": categories[i % len(categories)],
                    "price": 39 + (i % 15) * 8,
                    "sales_volume": 10 + (i % 35),
                    "GMV": 900 + (i % 60) * 50,
                    "order_count": 8 + (i % 20),
                    "inventory": 5 + (i % 40),
                    "fulfillment_rate": 0.90 + ((i % 7) * 0.01),
                    "refund_rate": 0.01 + ((i % 5) * 0.01),
                    "review_count": 4 + (i % 14),
                    "rating": 4.0 + ((i % 9) * 0.1),
                    "PV": 300 + (i % 150),
                    "UV": 120 + (i % 90),
                    "click": 30 + (i % 30),
                    "add_to_cart": 10 + (i % 12),
                    "pay": 6 + (i % 10),
                    "gross_margin": 0.12 + ((i % 8) * 0.03),
                    "ad_cost": 40 + (i % 20) * 10,
                    "activity_id": f"act-{i % 6}",
                    "date": f"2026-04-{(i % 28) + 1:02d}",
                }
            )
        return pd.DataFrame(rows)

    def _report(self) -> dict:
        frame = self._frame()
        field_registry = ecommerce_field_availability_registry(frame)
        semantic_map = ecommerce_field_semantic_interpreter(frame, field_registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, field_registry, semantic_map)
        registry_payload = build_ecommerce_object_decision_registry(modules, field_registry)
        action_table = render_ecommerce_action_table(registry_payload)
        roadmap_payload = build_ecommerce_action_roadmap(registry_payload, field_registry)
        return {
            "report_id": "ecommercepdf01",
            "title": "placeholder",
            "dataset_name": "淘宝商品聚合数据",
            "sheet_name": "Sheet1",
            "generated_at": "2026-04-26T00:00:00Z",
            "report_language": "zh-CN",
            "business_profile": "ecommerce_product_operations_report",
            "report_lens": "procurement_sales_review",
            "ecommerce_field_availability_registry": field_registry,
            "ecommerce_field_semantic_map": semantic_map,
            "product_operations_analysis_modules": modules,
            "ecommerce_object_decision_registry": registry_payload,
            "ecommerce_action_table": action_table,
            "ecommerce_action_roadmap": roadmap_payload,
            "sections": [],
            "executive_summary": [],
        }

    def test_renderer_builds_38_page_sections(self) -> None:
        report = self._report()
        variant = build_ecommerce_management_variant(report)
        self.assertIsNotNone(variant)
        self.assertEqual(len(variant["sections"]), 38)
        self.assertIn("商品经营", variant["title"])
        self.assertNotIn("互联网运营", variant["title"])
        self.assertNotIn("媒体投放", variant["title"])

    def test_renderer_outputs_pdf_between_35_and_50_pages(self) -> None:
        try:
            from pypdf import PdfReader
        except Exception:
            self.skipTest("pypdf unavailable")

        report = self._report()
        variant = build_ecommerce_management_variant(report)
        self.assertIsNotNone(variant)
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = _write_pdf_report_cn(Path(tmp), "management_report", variant)
            self.assertIsNotNone(pdf_path)
            self.assertTrue(Path(pdf_path).exists())
            pages = len(PdfReader(str(pdf_path)).pages)
            self.assertGreaterEqual(pages, 35)
            self.assertLessEqual(pages, 50)

    def test_appendix_variant_builds(self) -> None:
        report = self._report()
        appendix_variant = build_ecommerce_appendix_variant(report)
        self.assertIsNotNone(appendix_variant)
        self.assertGreaterEqual(len(appendix_variant["sections"]), 3)

    def test_appendix_variant_keeps_full_registry_rows(self) -> None:
        report = self._report()
        appendix_variant = build_ecommerce_appendix_variant(report)
        registry_section = next(section for section in appendix_variant["sections"] if section["id"] == "appendix_registry")
        registry_table = next(table for table in registry_section["tables"] if table["title"] == "ecommerce_object_decision_registry")
        self.assertEqual(
            len(registry_table["rows"]),
            len(report["ecommerce_object_decision_registry"]["rows"]),
        )

    def test_downloadable_bundle_outputs_required_files(self) -> None:
        try:
            from pypdf import PdfReader
        except Exception:
            self.skipTest("pypdf unavailable")

        report = self._report()
        frame = self._frame()

        def _fake_chain(*, output_dir, **kwargs):
            output_dir = Path(output_dir)
            (output_dir / "ecommerce_page_plan.json").write_text('{"pages":[{"page_number":1,"page_title":"封面与报告定位"}]}', encoding="utf-8")
            (output_dir / "ecommerce_page_plan.md").write_text("# ecommerce_page_plan\n", encoding="utf-8")
            (output_dir / "ecommerce_codex_call_log.jsonl").write_text(
                "\n".join(json.dumps({"pass_name": f"pass_{i}", "status": "success"}, ensure_ascii=False) for i in range(1, 9)) + "\n",
                encoding="utf-8",
            )
            (output_dir / "ecommerce_business_context_interpretation.md").write_text("# ecommerce_business_context_interpretation\n", encoding="utf-8")
            (output_dir / "ecommerce_object_interpretation.md").write_text("# ecommerce_object_interpretation\n", encoding="utf-8")
            (output_dir / "ecommerce_management_question_bank.md").write_text("# ecommerce_management_question_bank\n", encoding="utf-8")
            (output_dir / "ecommerce_conflict_check.md").write_text("# ecommerce_conflict_check\n", encoding="utf-8")
            (output_dir / "ecommerce_executive_review.md").write_text("# ecommerce_executive_review\n", encoding="utf-8")
            return {"call_count": 8}

        def _fake_negative_tests(output_dir):
            path = Path(output_dir) / "ecommerce_negative_test_report.md"
            path.write_text("# ecommerce_negative_test_report\n\n- ok\n", encoding="utf-8")
            return path, [{"case_id": "A", "validator_passed": True, "validator_score": 95}]

        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-ecommercebundle01"
            with patch("app.services.report_service.run_ecommerce_codex_interpretation_chain", _fake_chain), patch("app.services.report_service._run_ecommerce_negative_tests", _fake_negative_tests):
                result = _downloadable_bundle_cn_ecommerce(
                    report_dir=report_dir,
                    report_id="ecommercebundle01",
                    report=report,
                    frame=frame,
                    market_intelligence={},
                    request=SmartReportRequest(
                        sheet_name="Sheet1",
                        business_profile="ecommerce_product_operations_report",
                        report_style="deep_dive",
                    ),
                )
            self.assertTrue((report_dir / "ecommercebundle01-management_report.pdf").exists())
            self.assertTrue((report_dir / "ecommercebundle01-management_report.html").exists())
            self.assertTrue((report_dir / "ecommercebundle01-analyst_appendix.xlsx").exists())
            self.assertTrue((report_dir / "7_day_ecommerce_action_table.csv").exists())
            self.assertTrue((report_dir / "30_day_ecommerce_experiment_backlog.csv").exists())
            self.assertTrue((report_dir / "ecommerce_page_plan.json").exists())
            self.assertTrue((report_dir / "ecommercebundle01-before_after_summary.md").exists())
            pages = len(PdfReader(str(report_dir / "ecommercebundle01-management_report.pdf")).pages)
            self.assertGreaterEqual(pages, 35)
            self.assertLessEqual(pages, 50)
            self.assertEqual(result["main_downloadable"]["name"], "ecommercebundle01-management_report.pdf")


if __name__ == "__main__":
    unittest.main()
