from __future__ import annotations

import unittest

from app.services.ecommerce_render_guard_service import (
    ecommerce_quality_gate,
    ecommerce_report_quality_scorer,
)


class EcommerceRenderGuardServiceTests(unittest.TestCase):
    def _action_rows(self) -> list[dict[str, str]]:
        return [
            {
                "优先级": "P1",
                "对象层级": "商品",
                "对象名称": "商品A",
                "最终标签": "核心商品候选",
                "触发证据": "GMV高",
                "现有证据类型": "evidence_based_decision",
                "缺失字段": "",
                "被拦截动作": "",
                "最终动作": "复核商品详情页",
                "负责人角色": "商品运营",
                "时间要求": "T+7",
                "验证指标": "支付转化率",
                "成功标准": "转化回升",
                "结论强度": "candidate",
                "置信度": "medium",
            }
        ]

    def _seven_day_rows(self) -> list[dict[str, str]]:
        return [
            {
                "优先级": "P1",
                "动作": "复核",
                "对象": "商品A",
                "负责人角色": "商品运营",
                "输入数据": "GMV / 点击 / 支付",
                "产出结果": "复核结论",
                "截止时间": "T+7",
                "验证标准": "完成复核",
                "护栏指标": "不得越权",
                "依赖字段": "conversion_fields",
                "当前结论强度": "candidate",
            }
        ]

    def _backlog_rows(self) -> list[dict[str, str]]:
        return [
            {
                "实验编号": "ECOM-EXP-001",
                "实验假设": "详情页承接优化后支付转化率会提升",
                "目标对象": "商品A",
                "实验动作": "详情页测试",
                "核心指标": "支付转化率",
                "护栏指标": "退款率",
                "样本要求": "50单",
                "数据依赖": "conversion_fields",
                "预计周期": "14-30天",
                "成功标准": "支付转化率提升",
                "失败后处理": "回退版本",
                "结论类型": "business_hypothesis",
            }
        ]

    def test_quality_gate_fails_on_margin_forbidden_terms(self) -> None:
        field_registry = {
            "has_margin_cost_fields": False,
            "has_inventory_fields": True,
            "has_traffic_fields": True,
            "has_conversion_fields": True,
            "has_aftersales_fields": True,
            "has_review_fields": True,
            "has_fulfillment_fields": True,
            "has_time_fields": True,
        }
        text = "\n".join(
            [
                "《电商商品经营复盘报告：销售、转化、库存、履约与口碑分析》",
                "字段边界：缺毛利/成本。",
                "利润高，ROI高，值得加码。",
            ]
        )
        result = ecommerce_quality_gate(
            management_markdown=text,
            total_pages=38,
            business_profile="ecommerce_product_operations_report",
            field_registry=field_registry,
            action_rows=self._action_rows(),
            seven_day_rows=self._seven_day_rows(),
            backlog_rows=self._backlog_rows(),
            codex_call_count=8,
            section_ids=[],
            router_result={"business_profile": "ecommerce_product_operations_report"},
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing_margin_cost_fields" in item for item in result["fail_items"]))

    def test_report_quality_scorer_caps_score_when_gate_fails(self) -> None:
        field_registry = {
            "has_margin_cost_fields": False,
            "has_inventory_fields": True,
            "has_traffic_fields": True,
            "has_conversion_fields": True,
            "has_aftersales_fields": True,
            "has_review_fields": True,
            "has_fulfillment_fields": True,
            "has_time_fields": True,
        }
        text = "利润高 ROI高 值得加码"
        gate = {"passed": False, "fail_items": ["missing_margin_cost_fields_but_found:ROI高"]}
        result = ecommerce_report_quality_scorer(
            management_markdown=text,
            total_pages=38,
            business_profile="ecommerce_product_operations_report",
            field_registry=field_registry,
            action_rows=self._action_rows(),
            seven_day_rows=self._seven_day_rows(),
            backlog_rows=self._backlog_rows(),
            codex_call_count=8,
            gate_result=gate,
            section_ids=[],
            router_result={"business_profile": "ecommerce_product_operations_report"},
        )
        self.assertLessEqual(result["score"], 89)
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
