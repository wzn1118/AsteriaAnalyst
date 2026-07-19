from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.models import SmartReportRequest
from app.services.ecommerce_product_operations_service import (
    build_ecommerce_product_operations_analysis_modules,
    ecommerce_field_availability_registry,
    ecommerce_field_semantic_interpreter,
    run_ecommerce_codex_interpretation_chain,
    write_ecommerce_module_results,
)


def _live(result: dict) -> dict:
    payload = dict(result)
    payload.setdefault("mode", "live_codex_agentic")
    payload.setdefault("runtime_state", "live")
    payload.setdefault("degradation_state", "none")
    payload.setdefault("live_available", True)
    return payload


class EcommerceProductOperationsAnalysisTests(unittest.TestCase):
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

    def test_builds_all_required_modules(self) -> None:
        frame = self._frame()
        registry = ecommerce_field_availability_registry(frame)
        semantic = ecommerce_field_semantic_interpreter(frame, registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, registry, semantic)
        self.assertEqual(len(modules), 12)
        for name in [
            "ecommerce_overview_analyzer",
            "product_performance_analyzer",
            "category_performance_analyzer",
            "shop_seller_analyzer",
            "traffic_conversion_analyzer",
            "price_promotion_analyzer",
            "inventory_fulfillment_analyzer",
            "aftersales_review_analyzer",
            "margin_profit_analyzer",
            "anomaly_detection_analyzer",
            "product_lifecycle_analyzer",
            "ecommerce_management_diagnosis",
        ]:
            self.assertIn(name, modules)
            module = modules[name]
            for key in [
                "module_name",
                "business_question",
                "key_findings",
                "evidence",
                "missing_fields",
                "unsupported_claims",
                "recommended_actions",
                "validation_metrics",
                "confidence_level",
                "conclusion_type",
            ]:
                self.assertIn(key, module)

    def test_writes_module_result_json_files(self) -> None:
        frame = self._frame()
        registry = ecommerce_field_availability_registry(frame)
        semantic = ecommerce_field_semantic_interpreter(frame, registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, registry, semantic)
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            write_ecommerce_module_results(out_dir, modules)
            self.assertTrue((out_dir / "ecommerce_module_result_manifest.json").exists())
            self.assertTrue((out_dir / "ecommerce_overview_analyzer_module_result.json").exists())
            self.assertTrue((out_dir / "margin_profit_analyzer_module_result.json").exists())

    def test_runs_ecommerce_codex_chain_with_8_rounds(self) -> None:
        frame = self._frame()
        registry = ecommerce_field_availability_registry(frame)
        semantic = ecommerce_field_semantic_interpreter(frame, registry)
        modules = build_ecommerce_product_operations_analysis_modules(frame, registry, semantic)

        patches = [
            patch("app.services.ecommerce_product_operations_service.codex_complete_input_fields", lambda payload: _live({"completed_problem_to_solve": "形成电商经营复盘", "completed_core_purpose": "输出电商经营管理报告"})),
            patch("app.services.ecommerce_product_operations_service.codex_semantic_analysis", lambda payload: _live({"subject_type": "product_entity", "creator_profile": "当前数据以商品、类目和店铺对象为核心"})),
            patch("app.services.ecommerce_product_operations_service.codex_business_object_interpretation", lambda payload: _live({"headline": "电商对象复核完成", "drilldown_findings": [{"title": "头部对象", "deeper_read": "头部商品仍需结合售后和毛利复核", "business_move": "先复核再判断"}]})),
            patch("app.services.ecommerce_product_operations_service.codex_generic_management_question_bank", lambda payload: _live({"questions": [{"priority": i + 1, "business_question": f"Q{i+1}", "why_it_matters": "管理层关注", "can_answer_now": "部分可答", "required_fields": ["transaction_fields"], "report_section": "电商经营总览", "management_action": "复核"} for i in range(25)]})),
            patch("app.services.ecommerce_product_operations_service.codex_generic_exploratory_interpretation", lambda payload: _live({"main_findings": ["商品结构集中", "退款风险集中"], "anomalies": ["部分店铺售后偏高"], "possible_reasons": ["促销与履约错位"], "cannot_conclude": ["不能直接做利润拍板"], "next_validations": ["先做对象复核"]})),
            patch("app.services.ecommerce_product_operations_service.codex_challenge_review", lambda payload: _live({"challenge_points": [], "counter_arguments": [], "boundary_alerts": [], "unresolved_gaps": []})),
            patch("app.services.ecommerce_product_operations_service.codex_generic_long_page_plan", lambda payload: _live({"pages": payload["seed_page_plan"], "notes": ["ecommerce page plan"]})),
            patch("app.services.ecommerce_product_operations_service.codex_judge_feedback", lambda payload: _live({"verdict": "pass", "issues": [], "revise_instructions": []})),
        ]
        for item in patches:
            item.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out_dir = Path(tmp)
                result = run_ecommerce_codex_interpretation_chain(
                    output_dir=out_dir,
                    frame=frame,
                    field_registry=registry,
                    semantic_map=semantic,
                    modules=modules,
                    request=SmartReportRequest(sheet_name="Sheet1", business_profile="ecommerce_product_operations_report"),
                )
                self.assertGreaterEqual(result["call_count"], 8)
                self.assertTrue((out_dir / "ecommerce_codex_call_log.jsonl").exists())
                self.assertTrue((out_dir / "ecommerce_business_context_interpretation.md").exists())
                self.assertTrue((out_dir / "ecommerce_object_interpretation.md").exists())
                self.assertTrue((out_dir / "ecommerce_management_question_bank.md").exists())
                self.assertTrue((out_dir / "ecommerce_risk_interpretation.md").exists())
                self.assertTrue((out_dir / "ecommerce_conflict_check.md").exists())
                self.assertTrue((out_dir / "ecommerce_page_plan.md").exists())
                self.assertTrue((out_dir / "ecommerce_executive_review.md").exists())
        finally:
            for item in reversed(patches):
                item.stop()


if __name__ == "__main__":
    unittest.main()
