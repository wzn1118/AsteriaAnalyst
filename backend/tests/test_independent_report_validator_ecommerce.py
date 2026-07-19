from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.services.ecommerce_action_roadmap_renderer import (
    build_ecommerce_action_roadmap,
    write_ecommerce_action_roadmap_artifacts,
)
from app.services.ecommerce_pdf_report_renderer import build_ecommerce_management_variant
from app.services.ecommerce_product_operations_service import (
    build_ecommerce_object_decision_registry,
    build_ecommerce_product_operations_analysis_modules,
    ecommerce_field_availability_registry,
    ecommerce_field_semantic_interpreter,
    render_ecommerce_action_table,
    write_ecommerce_decision_registry_artifacts,
    write_ecommerce_registry_artifacts,
    write_ecommerce_module_results,
)
from app.services.independent_report_validator import validate_report_dir
from app.services.report_service import _render_report_html_cn, _report_markdown_cn, _write_pdf_report_cn


class EcommerceIndependentValidatorTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        rows = []
        for i in range(320):
            rows.append(
                {
                    "item_id": f"item-{i % 36}",
                    "sku_id": f"sku-{i % 60}",
                    "spu_id": f"spu-{i % 20}",
                    "shop_id": ["淘宝旗舰店", "天猫直营店", "京东自营", "拼多多店铺"][i % 4],
                    "brand": ["品牌A", "品牌B", "品牌C", "品牌D"][i % 4],
                    "category": ["护肤", "手机", "家清", "服饰"][i % 4],
                    "price": 39 + (i % 12) * 7,
                    "sales_volume": 8 + (i % 18),
                    "GMV": 900 + (i % 40) * 45,
                    "order_count": 6 + (i % 16),
                    "inventory": 5 + (i % 28),
                    "fulfillment_rate": 0.90 + ((i % 6) * 0.01),
                    "refund_rate": 0.01 + ((i % 4) * 0.01),
                    "review_count": 4 + (i % 10),
                    "rating": 4.0 + ((i % 6) * 0.1),
                    "PV": 240 + (i % 80),
                    "UV": 100 + (i % 60),
                    "click": 30 + (i % 20),
                    "add_to_cart": 8 + (i % 10),
                    "pay": 6 + (i % 8),
                    "gross_margin": 0.15 + ((i % 5) * 0.02),
                    "ad_cost": 30 + (i % 10) * 10,
                    "date": f"2026-04-{(i % 20) + 1:02d}",
                }
            )
        return pd.DataFrame(rows)

    def _prepare_report_dir(self, report_dir: Path, *, inject_forbidden: bool = False) -> None:
        report_id = report_dir.name.replace("smart-report-", "")
        frame = self._frame()
        field_registry = ecommerce_field_availability_registry(frame)
        semantic_map = ecommerce_field_semantic_interpreter(frame, field_registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, field_registry, semantic_map)
        registry_payload = build_ecommerce_object_decision_registry(modules, field_registry)
        action_rows = render_ecommerce_action_table(registry_payload)
        roadmap_payload = build_ecommerce_action_roadmap(registry_payload, field_registry)
        report = {
            "report_id": report_id,
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
            "ecommerce_action_table": action_rows,
            "ecommerce_action_roadmap": roadmap_payload,
        }
        variant = build_ecommerce_management_variant(report)
        self.assertIsNotNone(variant)
        if inject_forbidden:
            variant["sections"][0]["bullets"].append("利润高，ROI高，值得加码。")
            field_registry["has_margin_cost_fields"] = False

        (report_dir / f"{report_id}-management_report.html").write_text(_render_report_html_cn(variant), encoding="utf-8")
        (report_dir / f"{report_id}-management_report.md").write_text(_report_markdown_cn(variant), encoding="utf-8")
        _write_pdf_report_cn(report_dir, f"{report_id}-management_report", variant)

        write_ecommerce_registry_artifacts(report_dir, field_registry, semantic_map)
        write_ecommerce_module_results(report_dir, modules)
        write_ecommerce_decision_registry_artifacts(report_dir, registry_payload)
        write_ecommerce_action_roadmap_artifacts(report_dir, roadmap_payload)

        (report_dir / "ecommerce_codex_call_log.jsonl").write_text(
            "\n".join(json.dumps({"pass_name": f"pass_{i}", "status": "success"}, ensure_ascii=False) for i in range(1, 9)) + "\n",
            encoding="utf-8",
        )
        (report_dir / f"{report_id}-business_profile_router_result.json").write_text(
            json.dumps({"business_profile": "ecommerce_product_operations_report", "decisive_object_grain": "商品/店铺/SKU"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (report_dir / f"{report_id}-quality_gate_result.json").write_text(
            json.dumps({"passed": not inject_forbidden}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (report_dir / f"{report_id}-report_quality_score.json").write_text(
            json.dumps({"score": 95 if not inject_forbidden else 62}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def test_validator_passes_for_compliant_ecommerce_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-ecomvalidator01"
            report_dir.mkdir(parents=True, exist_ok=True)
            self._prepare_report_dir(report_dir, inject_forbidden=False)
            result = validate_report_dir(report_dir)
            self.assertTrue(result["passed"])
            self.assertEqual(result["business_profile"], "ecommerce_product_operations_report")

    def test_validator_fails_for_forbidden_margin_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-ecomvalidator02"
            report_dir.mkdir(parents=True, exist_ok=True)
            self._prepare_report_dir(report_dir, inject_forbidden=True)
            result = validate_report_dir(report_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("缺 margin_cost_fields" in item for item in result["field_boundary_errors"]))


if __name__ == "__main__":
    unittest.main()
