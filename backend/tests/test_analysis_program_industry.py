from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from app.models import SmartReportRequest
from app.services.analysis_program_service import (
    _expert_recall,
    _merge_ai_object_candidates,
    _merge_ai_semantic_mapping,
    _sanitize_semantic_mapping,
    build_analysis_program,
)


class AnalysisProgramIndustryTests(unittest.TestCase):
    def test_ai_generic_object_does_not_override_specific_high_confidence_object(self) -> None:
        merged = _merge_ai_object_candidates(
            [
                {
                    "object_type": "nonprofit_project_portfolio",
                    "score": 8.4,
                    "confidence": "high",
                    "observation_unit": "单个基金会项目记录",
                    "preferred_modules": ["analysis_program"],
                    "preferred_methods": ["correlation"],
                }
            ],
            {
                "object_candidates": [
                    {
                        "object_type": "generic_business_table",
                        "score": 9.5,
                        "confidence": "high",
                        "observation_unit": "单行记录",
                    }
                ]
            },
        )
        self.assertEqual(merged[0]["object_type"], "nonprofit_project_portfolio")

    def test_ai_chinese_role_aliases_map_back_to_supported_roles(self) -> None:
        merged = _merge_ai_semantic_mapping(
            {
                "columns": [
                    {"column": "本年度总支出", "best_role": "unmapped", "best_confidence": "low", "top_roles": []},
                    {"column": "本年度捐赠收入合计", "best_role": "unmapped", "best_confidence": "low", "top_roles": []},
                ],
                "role_summary": {},
            },
            {
                "column_role_hints": [
                    {"column": "本年度总支出", "role": "总支出", "confidence": "high", "score": 9},
                    {"column": "本年度捐赠收入合计", "role": "捐赠收入", "confidence": "high", "score": 9},
                ]
            },
        )
        self.assertEqual(merged["columns"][0]["best_role"], "spend")
        self.assertEqual(merged["columns"][1]["best_role"], "revenue")

    def test_foundation_columns_are_sanitized_to_domain_roles(self) -> None:
        frame = pd.DataFrame(
            {
                "基金会名称": ["A基金会", "B基金会"],
                "统一信用代码(网页基本信息)": ["123", "456"],
                "基金会类型(网页基本信息)": ["非公募", "公募"],
                "登记管理机关": ["民政部", "民政局"],
                "年度": [2024, 2024],
                "理事会召开次数": [2, 3],
            }
        )
        merged = _sanitize_semantic_mapping(
            frame,
            {
                "columns": [
                    {"column": "基金会名称", "best_role": "brand", "best_confidence": "low", "top_roles": []},
                    {"column": "统一信用代码(网页基本信息)", "best_role": "placement", "best_confidence": "low", "top_roles": []},
                    {"column": "基金会类型(网页基本信息)", "best_role": "brand", "best_confidence": "low", "top_roles": []},
                    {"column": "登记管理机关", "best_role": "brand", "best_confidence": "low", "top_roles": []},
                    {"column": "年度", "best_role": "spend", "best_confidence": "low", "top_roles": []},
                    {"column": "理事会召开次数", "best_role": "spend", "best_confidence": "low", "top_roles": []},
                ],
                "role_summary": {},
            },
        )
        best_roles = {item["column"]: item["best_role"] for item in merged["columns"]}
        self.assertEqual(best_roles["基金会名称"], "entity_name")
        self.assertEqual(best_roles["统一信用代码(网页基本信息)"], "entity_id")
        self.assertEqual(best_roles["基金会类型(网页基本信息)"], "organization_type")
        self.assertEqual(best_roles["登记管理机关"], "registry_authority")
        self.assertEqual(best_roles["年度"], "time")
        self.assertEqual(best_roles["理事会召开次数"], "governance")

    @patch("app.services.analysis_program_service.codex_classify_business_context")
    @patch("app.services.analysis_program_service.codex_synthesize_requirement")
    @patch("app.services.analysis_program_service.codex_complete_input_fields")
    def test_internet_ops_review_detected_from_ops_table(self, mock_complete, mock_requirement, mock_classify) -> None:
        mock_complete.return_value = {
            "completed_business_background_name": "运营复盘场景",
            "completed_business_background_text": "这是一份运营数据。",
            "completed_user_requirement": "生成互联网运营复盘报告",
            "completed_problem_to_solve": "解释拉新、活跃、留存和转化问题",
            "completed_target_audience": "运营负责人 / 增长负责人 / 数据分析负责人",
            "completed_core_purpose": "形成一份可用于周会复盘的运营报告",
            "completed_expected_result": "管理层主报告 + 分析附录",
            "completed_key_constraints": "",
        }
        mock_requirement.return_value = {
            "mode": "fallback",
            "refined_problem": "解释拉新、活跃、留存和转化问题",
            "refined_audience": "运营负责人 / 增长负责人 / 数据分析负责人",
            "refined_purpose": "形成一份可用于周会复盘的运营报告",
            "refined_expected_result": "管理层主报告 + 分析附录",
            "explicit_constraints": [],
            "success_criteria": ["能解释增长问题"],
            "must_answer_questions": ["新增从哪里来", "留存为什么掉"],
            "non_goals": ["不把短期波动写成长趋势"],
            "output_preferences": ["先结论后证据"],
            "ambiguity_flags": [],
            "recommended_focus": ["先看增长链路"],
            "next_step": "直接进入分析",
        }
        mock_classify.return_value = {
            "mode": "fallback",
            "task_family_candidates": [],
            "object_candidates": [],
            "column_role_hints": [],
            "notes": [],
        }
        frame = pd.DataFrame(
            {
                "user_id": [1, 2, 3, 4],
                "event_date": ["2026-04-01", "2026-04-01", "2026-04-02", "2026-04-02"],
                "channel": ["organic", "ads", "organic", "community"],
                "campaign_name": ["spring_push", "spring_push", "retention", "retention"],
                "active_users": [120, 45, 140, 60],
                "registrations": [20, 8, 18, 9],
                "retention_rate": [0.42, 0.31, 0.45, 0.36],
                "conversion_rate": [0.11, 0.08, 0.12, 0.09],
                "content_title": ["开屏活动A", "开屏活动A", "留存召回文案", "留存召回文案"],
            }
        )
        request = SmartReportRequest(
            user_requirement="请生成一份互联网运营复盘报告",
            problem_to_solve="解释拉新、活跃、留存和转化问题",
            target_audience="运营负责人 / 增长负责人 / 数据分析负责人",
            core_purpose="形成一份可用于周会复盘的运营报告",
            expected_result="管理层主报告 + 分析附录",
        )
        program = build_analysis_program(request, "互联网运营日报", "Sheet1", frame)
        self.assertEqual(program["task_model"]["primary_family"], "internet_ops_review")
        self.assertIn(program["object_candidates"][0]["object_type"], {"internet_operations_log", "content_performance_table", "crm_funnel_event_log"})
        self.assertEqual(program["learned_route"]["mode"], "mlp_router")
        self.assertEqual(program["learned_route"]["task_family_candidates"][0]["family"], "internet_ops_review")
        self.assertTrue(program["learned_route"]["writer_agent_candidates"])
        self.assertEqual(program["task_model"]["problem"], "解释拉新、活跃、留存和转化问题")
        self.assertEqual(program["task_model"]["purpose"], "形成一份可用于周会复盘的运营报告")
        self.assertIn("新增从哪里来", program["requirement_model"]["must_answer_questions"])

    @patch("app.services.analysis_program_service.codex_classify_business_context")
    @patch("app.services.analysis_program_service.codex_synthesize_requirement")
    @patch("app.services.analysis_program_service.codex_complete_input_fields")
    def test_blank_input_fields_are_filled_before_requirement_modeling(self, mock_complete, mock_requirement, mock_classify) -> None:
        mock_complete.return_value = {
            "completed_business_background_name": "基金会年度复盘场景",
            "completed_business_background_text": "基金会年度汇总与项目支出相关数据。",
            "completed_user_requirement": "请基于基金会年度汇总与项目结构生成专业复盘报告。",
            "completed_problem_to_solve": "判断哪些基金会承担主要公益支出。",
            "completed_target_audience": "基金会负责人 / 秘书处",
            "completed_core_purpose": "形成基金会年度复盘报告",
            "completed_expected_result": "主报告 + 风险清单",
            "completed_key_constraints": "只基于当前上传数据判断",
        }
        mock_requirement.return_value = {
            "mode": "fallback",
            "refined_problem": "判断哪些基金会承担主要公益支出。",
            "refined_audience": "基金会负责人 / 秘书处",
            "refined_purpose": "形成基金会年度复盘报告",
            "refined_expected_result": "主报告 + 风险清单",
            "explicit_constraints": ["只基于当前上传数据判断"],
            "success_criteria": ["能回答重点基金会问题"],
            "must_answer_questions": ["哪些基金会值得优先复盘"],
            "non_goals": ["不把基金会数据写成压测报告"],
            "output_preferences": ["先结论后证据"],
            "ambiguity_flags": [],
            "recommended_focus": ["先看基金会主体和支出结构"],
            "next_step": "直接进入分析",
        }
        mock_classify.return_value = {
            "mode": "fallback",
            "task_family_candidates": [],
            "object_candidates": [],
            "column_role_hints": [],
            "notes": [],
        }
        frame = pd.DataFrame(
            {
                "基金会名称": ["A基金会", "B基金会"],
                "统一信用代码(网页基本信息)": ["1", "2"],
                "年度": [2024, 2024],
                "本年度总支出": [1000.0, 2000.0],
                "本年度捐赠收入合计": [800.0, 1800.0],
            }
        )
        request = SmartReportRequest(sheet_name="Sheet2")
        program = build_analysis_program(request, "基金会", "Sheet2", frame)
        self.assertEqual(program["resolved_request_payload"]["problem_to_solve"], "判断哪些基金会承担主要公益支出。")
        self.assertEqual(program["resolved_request_payload"]["target_audience"], "基金会负责人 / 秘书处")
        self.assertEqual(program["resolved_request_payload"]["core_purpose"], "形成基金会年度复盘报告")

    @patch("app.services.analysis_program_service.codex_classify_business_context")
    @patch("app.services.analysis_program_service.codex_synthesize_requirement")
    def test_foundation_review_is_not_hijacked_by_benchmark_candidate(self, mock_requirement, mock_classify) -> None:
        mock_requirement.return_value = {
            "mode": "fallback",
            "refined_problem": "判断哪些基金会承担主要公益支出",
            "refined_audience": "基金会负责人 / 秘书处",
            "refined_purpose": "形成基金会年度复盘报告",
            "refined_expected_result": "主报告 + 风险清单",
            "explicit_constraints": [],
            "success_criteria": ["能输出基金会复盘判断"],
            "must_answer_questions": ["哪些基金会值得优先复盘"],
            "non_goals": ["不把基金会数据写成压测报告"],
            "output_preferences": ["先结论后证据"],
            "ambiguity_flags": [],
            "recommended_focus": ["先看基金会主体与收支结构"],
            "next_step": "直接进入分析",
        }
        mock_classify.return_value = {
            "mode": "live_codex",
            "task_family_candidates": [
                {"family": "performance_benchmark", "score": 9, "confidence": "high", "why": "误判"},
                {"family": "foundation_review", "score": 8, "confidence": "high", "why": "次选"},
            ],
            "object_candidates": [
                {"object_type": "performance_benchmark_table", "score": 9, "confidence": "high", "observation_unit": "单条可比样本", "why": "误判"},
                {"object_type": "nonprofit_project_portfolio", "score": 8, "confidence": "high", "observation_unit": "单家基金会年度汇总", "why": "正确"},
            ],
            "column_role_hints": [],
            "notes": [],
        }
        frame = pd.DataFrame(
            {
                "基金会名称": ["A基金会", "B基金会", "C基金会"],
                "统一信用代码(网页基本信息)": ["1", "2", "3"],
                "基金会类型(网页基本信息)": ["非公募", "公募", "非公募"],
                "年度": [2024, 2024, 2024],
                "本年度总支出": [1000.0, 2000.0, 1500.0],
                "本年度用于公益事业的支出": [900.0, 1600.0, 1200.0],
                "本年度捐赠收入合计": [800.0, 1800.0, 1300.0],
                "本年度收入合计": [950.0, 2100.0, 1600.0],
            }
        )
        request = SmartReportRequest(
            user_requirement="请基于基金会年度汇总与项目结构做一份专业复盘报告",
            problem_to_solve="判断哪些基金会承担主要公益支出",
            target_audience="基金会负责人 / 秘书处",
            core_purpose="形成基金会年度复盘报告",
            expected_result="主报告 + 风险清单",
        )
        program = build_analysis_program(request, "基金会", "Sheet2", frame)
        self.assertEqual(program["task_model"]["primary_family"], "foundation_review")
        self.assertEqual(program["object_candidates"][0]["object_type"], "nonprofit_project_portfolio")

    def test_expert_recall_includes_soul_fields(self) -> None:
        experts = _expert_recall(
            {"primary_family": "management_accounting_review"},
            [{"object_type": "management_accounting_statement"}],
        )
        self.assertTrue(experts)
        self.assertIn("obsession", experts[0])
        self.assertIn("signature_move", experts[0])
        self.assertIn("anti_pattern", experts[0])
        self.assertIn("voice", experts[0])

    @patch("app.services.analysis_program_service.codex_classify_business_context")
    @patch("app.services.analysis_program_service.codex_synthesize_requirement")
    @patch("app.services.analysis_program_service.codex_complete_input_fields")
    def test_management_accounting_review_detected_from_finance_table(self, mock_complete, mock_requirement, mock_classify) -> None:
        mock_complete.return_value = {
            "completed_business_background_name": "管理会计复盘场景",
            "completed_business_background_text": "这是一份经营结果、预算执行与资金占用相关数据。",
            "completed_user_requirement": "请生成管理会计分析报告。",
            "completed_problem_to_solve": "判断利润质量、预算偏差和营运资本压力。",
            "completed_target_audience": "财务负责人 / 经营负责人 / 预算控制团队",
            "completed_core_purpose": "形成财务与经营联动复盘报告",
            "completed_expected_result": "主报告 + 偏差清单 + 风险提示",
            "completed_key_constraints": "",
        }
        mock_requirement.return_value = {
            "mode": "fallback",
            "refined_problem": "判断利润质量、预算偏差和营运资本压力。",
            "refined_audience": "财务负责人 / 经营负责人 / 预算控制团队",
            "refined_purpose": "形成财务与经营联动复盘报告",
            "refined_expected_result": "主报告 + 偏差清单 + 风险提示",
            "explicit_constraints": [],
            "success_criteria": ["能解释利润和现金的关系"],
            "must_answer_questions": ["利润是否有质量", "预算偏差来自哪里"],
            "non_goals": ["不把收入增长直接写成经营改善"],
            "output_preferences": ["先结论后证据"],
            "ambiguity_flags": [],
            "recommended_focus": ["先看利润率、预算偏差与营运资本"],
            "next_step": "直接进入分析",
        }
        mock_classify.return_value = {
            "mode": "fallback",
            "task_family_candidates": [],
            "object_candidates": [],
            "column_role_hints": [],
            "notes": [],
        }
        frame = pd.DataFrame(
            {
                "期间": ["2026Q1", "2026Q1", "2026Q2", "2026Q2"],
                "责任中心": ["华东", "华南", "华东", "华南"],
                "营业收入": [1000.0, 800.0, 1100.0, 780.0],
                "营业成本": [620.0, 520.0, 670.0, 540.0],
                "净利润": [120.0, 70.0, 150.0, 40.0],
                "预算收入": [950.0, 820.0, 1080.0, 800.0],
                "实际收入": [1000.0, 800.0, 1100.0, 780.0],
                "应收账款": [180.0, 150.0, 200.0, 165.0],
                "应付账款": [120.0, 110.0, 130.0, 118.0],
                "存货": [160.0, 120.0, 170.0, 128.0],
            }
        )
        request = SmartReportRequest(
            user_requirement="请生成管理会计分析报告",
            problem_to_solve="判断利润质量、预算偏差和营运资本压力",
            target_audience="财务负责人 / 经营负责人 / 预算控制团队",
            core_purpose="形成财务与经营联动复盘报告",
            expected_result="主报告 + 偏差清单 + 风险提示",
        )
        program = build_analysis_program(request, "经营管理会计样本", "Sheet1", frame)
        self.assertEqual(program["task_model"]["primary_family"], "management_accounting_review")
        self.assertEqual(program["learned_route"]["task_family_candidates"][0]["family"], "management_accounting_review")
        self.assertTrue(any(item["agent"] == "management_accounting_writer" for item in program["learned_route"]["writer_agent_candidates"]))
        self.assertIn(program["object_candidates"][0]["object_type"], {"management_accounting_statement", "financial_budget_table"})


if __name__ == "__main__":
    unittest.main()
