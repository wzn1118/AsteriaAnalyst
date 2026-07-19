from __future__ import annotations

import unittest

from app.models import SmartReportRequest
from app.services.report_service import _recommended_method_bullets, _stats_appendix_section_v2, _stats_appendix_section_v3


class MethodAppendixTests(unittest.TestCase):
    def _sample_run(self) -> dict:
        return {
            "method": "One-way ANOVA",
            "method_id": "anova",
            "request": {"target": "预估曝光", "group_column": "媒体"},
            "result": {
                "narrative": "媒体组间差异显著。",
                "metrics": {"n": 1195, "p_value": 0.00004, "effect_share": 0.019},
                "tables": [
                    {
                        "title": "Group means",
                        "columns": ["group", "mean"],
                        "rows": [
                            {"group": "快手", "mean": 200.0},
                            {"group": "芒果TV", "mean": 100.0},
                        ],
                    }
                ],
            },
        }

    def test_stats_appendix_contains_explanation_cards(self) -> None:
        section = _stats_appendix_section_v2(
            recommended_methods=[
                {
                    "id": "anova",
                    "method": "One-way ANOVA",
                    "family": "mean_tests",
                    "status": "live",
                    "goal": "比较多组均值差异",
                    "score": 6,
                }
            ],
            recommended_method_runs=[self._sample_run()],
            report_request=SmartReportRequest(
                target_audience="市场负责人 / 媒介负责人",
                core_purpose="判断媒体分组差异是否足以支持复盘动作",
            ),
            lens="media_review",
        )
        table_titles = [table["title"] for table in section["tables"]]
        self.assertIn("方法解读卡", table_titles)
        explanation_table = next(table for table in section["tables"] if table["title"] == "方法解读卡")
        self.assertIn("业务上怎么用", explanation_table["columns"])
        self.assertIn("主切片维度", explanation_table["rows"][0]["业务上怎么用"])

    def test_stats_appendix_v3_prefers_method_review_cards(self) -> None:
        section = _stats_appendix_section_v3(
            recommended_methods=[{"id": "anova", "method": "One-way ANOVA"}],
            recommended_method_runs=[self._sample_run()],
            report_request=SmartReportRequest(core_purpose="判断媒体分组差异是否足以支持复盘动作"),
            lens="media_review",
            method_reviews=[
                {
                    "method_id": "anova",
                    "method": "One-way ANOVA",
                    "result_meaning": "p值很低，说明媒体分组差异已经不是随机波动。",
                    "business_takeaway": "媒体可以作为第一层复盘切片。",
                    "caution": "不要直接把均值差异写成预算建议。",
                }
            ],
        )
        explanation_table = next(table for table in section["tables"] if table["title"] == "方法解读卡")
        self.assertIn("结果意味着什么", explanation_table["columns"])
        self.assertIn("媒体可以作为第一层复盘切片。", explanation_table["rows"][0]["业务上怎么用"])

    def test_method_execution_bullets_explain_usage(self) -> None:
        bullets = _recommended_method_bullets(
            [self._sample_run()],
            SmartReportRequest(
                target_audience="市场负责人 / 媒介负责人",
                core_purpose="判断媒体分组差异是否足以支持复盘动作",
            ),
            "media_review",
        )
        self.assertEqual(len(bullets), 1)
        self.assertIn("这个方法在回答", bullets[0])
        self.assertIn("这在当前报告里的用法是", bullets[0])

    def test_machine_learning_method_bullets_explain_usage(self) -> None:
        bullets = _recommended_method_bullets(
            [
                {
                    "method": "Random Forest",
                    "method_id": "random_forest",
                    "request": {"target": "收入", "features": ["成本", "毛利", "费用"]},
                    "result": {
                        "narrative": "随机森林已完成连续目标建模。",
                        "metrics": {"r_squared": 0.78, "rmse": 12.4},
                        "tables": [],
                    },
                }
            ],
            SmartReportRequest(
                target_audience="财务负责人 / 经营负责人",
                core_purpose="找出最值得优先复盘的经营驱动因素",
            ),
            "management_accounting_review",
        )
        self.assertEqual(len(bullets), 1)
        self.assertIn("随机森林", bullets[0])
        self.assertIn("优先复盘", bullets[0])

    def test_low_correlation_bullet_does_not_overclaim_driver_link(self) -> None:
        bullets = _recommended_method_bullets(
            [
                {
                    "method": "Correlation Matrix",
                    "method_id": "correlation",
                    "request": {"features": ["留存率", "转化率"]},
                    "result": {
                        "narrative": "",
                        "metrics": {
                            "strongest_left": "留存率",
                            "strongest_right": "转化率",
                            "strongest_correlation": 0.0011,
                        },
                        "tables": [],
                    },
                }
            ],
            SmartReportRequest(
                target_audience="增长负责人 / 运营负责人",
                core_purpose="判断留存与转化之间是否存在稳定联动",
            ),
            "internet_ops_review",
        )
        self.assertEqual(len(bullets), 1)
        self.assertIn("几乎无相关", bullets[0])
        self.assertNotIn("同一条变化链路", bullets[0])


if __name__ == "__main__":
    unittest.main()
