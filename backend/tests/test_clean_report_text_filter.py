from __future__ import annotations

import unittest

from app.services.procurement_sales_render_guard_service import clean_report_text_filter, strict_quality_gate


class CleanReportTextFilterTests(unittest.TestCase):
    def test_filter_removes_forbidden_report_terms(self) -> None:
        raw = (
            "release gate analysis_program decision_summary workflow debug "
            "正式报告里 下一轮 不能继续复写 同一条监控链 "
            "推荐统计方法实跑与解读 这个方法在回答 说明了什么 ?????? n/a"
        )
        cleaned = clean_report_text_filter(raw)
        for needle in [
            "release gate",
            "analysis_program",
            "decision_summary",
            "workflow",
            "debug",
            "正式报告里",
            "下一轮",
            "不能继续复写",
            "同一条监控链",
            "推荐统计方法实跑与解读",
            "这个方法在回答",
            "说明了什么",
            "??????",
        ]:
            self.assertNotIn(needle, cleaned)
        self.assertNotIn("n/a", cleaned.lower())

    def test_strict_gate_blocks_stats_in_management_report(self) -> None:
        gate = strict_quality_gate(
            management_markdown="推荐统计方法实跑与解读\nOne-way ANOVA\nPairwise mean differences",
            total_pages=10,
            field_registry={"has_profit_fields": False, "has_inventory_fields": False},
            action_rows=[],
        )
        self.assertFalse(gate["passed"])
        self.assertTrue(any("统计内容" in item or "禁词" in item for item in gate["fail_items"]))


if __name__ == "__main__":
    unittest.main()
