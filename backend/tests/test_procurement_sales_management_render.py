from __future__ import annotations

import unittest

from app.services.dataset_service import load_dataset_frame
from app.services.procurement_sales_render_guard_service import report_quality_scorer, strict_quality_gate
from app.services.report_service import (
    _final_procurement_sales_management_render,
    _procurement_sales_object_decision_registry,
    _report_markdown_cn,
)


def _resolve_frame(dataset_id: str):
    loaded = load_dataset_frame(dataset_id)
    if isinstance(loaded, tuple):
        for item in loaded:
            if hasattr(item, "columns"):
                return item
    return loaded


class ProcurementSalesManagementRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        frame = _resolve_frame("6490e1d9994d")
        registry = _procurement_sales_object_decision_registry(frame)
        cls.payload = _final_procurement_sales_management_render(
            {
                "title": "中文销售履约与商品经营复盘主报告（采购侧待补数）",
                "report_lens": "procurement_sales_review",
                "procurement_sales_readiness": {"report_mode": "sales_fulfillment_product_report"},
                "object_decision_registry": registry,
            }
        )
        cls.summary = "\n".join(cls.payload["executive_summary"])
        action_section = next(section for section in cls.payload["sections"] if section["id"] == "final_action_table")
        action_table = next(table for table in action_section["tables"] if table["title"] == "行动表")
        cls.action_rows = action_table["rows"]
        cls.payload.update(
            {
                "dataset_name": "olist-sales-fulfillment-review-test",
                "sheet_name": "Sheet1",
                "report_id": "test-render",
                "report_language": "zh-CN",
                "generated_at": "2026-04-25T00:00:00",
            }
        )

    def _find_action_row(self, object_name: str) -> dict:
        for row in self.action_rows:
            if str(row.get("对象名称") or "") == object_name:
                return row
        raise AssertionError(f"missing action row: {object_name}")

    def test_summary_has_fixed_five_parts_and_no_forbidden_terms(self) -> None:
        self.assertEqual(len(self.payload["executive_summary"]), 5)
        for needle in [
            "核心主推",
            "资源倾斜",
            "清理退场",
            "补货放量",
            "继续主推",
            "重点投放",
            "预算倾斜",
            "同一条监控链",
            "release gate",
            "下一轮",
        ]:
            self.assertNotIn(needle, self.summary)

    def test_summary_includes_required_objects(self) -> None:
        for needle in ["Health Beauty", "Telephony 商品（尾号48a9）", "SKU（尾号7663）"]:
            self.assertIn(needle, self.summary)

    def test_action_table_uses_sanitized_blocked_actions(self) -> None:
        health = self._find_action_row("Health Beauty")
        self.assertIn("强资源动作（已拦截）", str(health.get("被拦截动作") or ""))
        self.assertNotIn("资源倾斜", str(health.get("被拦截动作") or ""))
        self.assertNotIn("核心主推", str(health.get("被拦截动作") or ""))

        telephony = self._find_action_row("Telephony 商品（尾号48a9）")
        self.assertIn("强资源动作（已拦截）", str(telephony.get("被拦截动作") or ""))
        self.assertNotIn("核心主推", str(telephony.get("被拦截动作") or ""))
        self.assertNotIn("继续主推", str(telephony.get("被拦截动作") or ""))
        self.assertNotIn("资源倾斜", str(telephony.get("被拦截动作") or ""))

        sku7663 = self._find_action_row("SKU（尾号7663）")
        self.assertIn("库存处置动作（已拦截）", str(sku7663.get("被拦截动作") or ""))
        self.assertNotIn("清理退场", str(sku7663.get("被拦截动作") or ""))
        self.assertNotIn("停止补货", str(sku7663.get("被拦截动作") or ""))
        self.assertNotIn("并柜", str(sku7663.get("被拦截动作") or ""))
        self.assertNotIn("移出主推池", str(sku7663.get("被拦截动作") or ""))

    def test_management_render_passes_strict_quality_gate(self) -> None:
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


class ProcurementSalesManagementRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        frame = _resolve_frame("6490e1d9994d")
        registry = _procurement_sales_object_decision_registry(frame)
        cls.payload = _final_procurement_sales_management_render(
            {
                "title": "涓枃閿€鍞饱绾︿笌鍟嗗搧缁忚惀澶嶇洏涓绘姤鍛婏紙閲囪喘渚у緟琛ユ暟锛?",
                "report_lens": "procurement_sales_review",
                "procurement_sales_readiness": {"report_mode": "sales_fulfillment_product_report"},
                "object_decision_registry": registry,
            }
        )
        cls.summary = "\n".join(cls.payload["executive_summary"])
        action_section = next(section for section in cls.payload["sections"] if section["id"] == "final_action_table")
        action_table = action_section["tables"][0]
        cls.action_rows = action_table["rows"]
        cls.payload.update(
            {
                "dataset_name": "olist-sales-fulfillment-review-test",
                "sheet_name": "Sheet1",
                "report_id": "test-render",
                "report_language": "zh-CN",
                "generated_at": "2026-04-25T00:00:00",
            }
        )

    def test_summary_has_fixed_five_parts_and_no_forbidden_terms(self) -> None:
        self.assertEqual(len(self.payload["executive_summary"]), 5)
        for needle in [
            "鏍稿績涓绘帹",
            "璧勬簮鍊炬枩",
            "娓呯悊閫€鍦?",
            "琛ヨ揣鏀鹃噺",
            "缁х画涓绘帹",
            "閲嶇偣鎶曟斁",
            "棰勭畻鍊炬枩",
            "鍚屼竴鏉＄洃鎺ч摼",
            "release gate",
            "涓嬩竴杞?",
        ]:
            self.assertNotIn(needle, self.summary)

    def test_summary_no_longer_anchors_on_demo_objects(self) -> None:
        for needle in ["Health Beauty", "Telephony 鍟嗗搧锛堝熬鍙?8a9锛?", "SKU锛堝熬鍙?663锛?"]:
            self.assertNotIn(needle, self.summary)

    def test_action_table_uses_sanitized_blocked_actions(self) -> None:
        blocked_text = " | ".join(str(value) for row in self.action_rows for value in row.values())
        for needle in ["璧勬簮鍊炬枩", "鏍稿績涓绘帹", "娓呯悊閫€鍦?", "鍋滄琛ヨ揣", "骞舵煖", "绉诲嚭涓绘帹姹?"]:
            self.assertNotIn(needle, blocked_text)

    def test_management_render_passes_strict_quality_gate(self) -> None:
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
