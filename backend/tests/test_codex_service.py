from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.services.codex_service import (
    _fallback_business_background_analysis,
    _fallback_business_object_interpretation,
    _fallback_commercial_dimension_review,
    _fallback_internet_ops_review,
    _fallback_method_review,
    _fallback_metric_interpretation,
    _fallback_management_accounting_review,
    _fallback_statistical_scope,
    _ground_requirement_result,
    _json_default,
    _normalize_requirement_result,
    _request_codex_json,
    _request_codex_agentic_json,
    codex_generate_r_workflow,
    codex_classify_business_context,
    codex_complete_input_fields,
    codex_judge_report,
    codex_management_accounting_review,
    codex_summarize_eval_feedback,
    codex_statistical_scope,
)


class CodexServiceTests(unittest.TestCase):
    def test_json_default_handles_datetime_like_values(self) -> None:
        payload = {
            "ts": pd.Timestamp("2026-04-18 12:34:56"),
            "dt": datetime(2026, 4, 18, 12, 34, 56),
            "date": date(2026, 4, 18),
            "path": Path("C:/demo/file.xlsx"),
        }
        text = json.dumps(payload, ensure_ascii=False, default=_json_default)
        self.assertIn("2026-04-18T12:34:56", text)
        self.assertIn("2026-04-18", text)
        self.assertIn("file.xlsx", text)

    def test_normalize_requirement_result_flattens_list_like_text_fields(self) -> None:
        normalized = _normalize_requirement_result(
            {
                "refined_problem": ["先识别主题", "再形成动作"],
                "refined_audience": ["管理层", "执行层"],
                "success_criteria": "能回答核心问题",
                "must_answer_questions": ["问题A", "问题B"],
            }
        )
        self.assertEqual(normalized["refined_problem"], "先识别主题；再形成动作")
        self.assertEqual(normalized["refined_audience"], "管理层；执行层")
        self.assertEqual(normalized["success_criteria"], ["能回答核心问题"])

    def test_ground_requirement_result_preserves_explicit_user_problem(self) -> None:
        grounded = _ground_requirement_result(
            {
                "refined_problem": "当前原始需求几乎为空，无法直接确定分析主题",
                "refined_audience": "目标受众未明确",
                "refined_purpose": "输出目的未明确",
                "refined_expected_result": "",
                "explicit_constraints": [],
                "must_answer_questions": [],
                "ambiguity_flags": ["核心业务问题仍偏模糊", "目标受众未明确"],
                "next_step": "先确认问题",
            },
            {
                "problem_to_solve": "判断哪些基金会承担主要公益支出",
                "target_audience": "基金会负责人 / 秘书处",
                "core_purpose": "形成内部复盘报告",
                "expected_result": "主报告 + 风险清单",
                "key_constraints": "只基于当前上传数据判断",
            },
        )
        self.assertEqual(grounded["refined_problem"], "判断哪些基金会承担主要公益支出")
        self.assertEqual(grounded["refined_audience"], "基金会负责人 / 秘书处")
        self.assertEqual(grounded["refined_purpose"], "形成内部复盘报告")
        self.assertIn("判断哪些基金会承担主要公益支出", grounded["must_answer_questions"])

    def test_fallback_statistical_scope_keeps_metrics_but_excludes_year(self) -> None:
        result = _fallback_statistical_scope(
            "fallback",
            {
                "numeric_columns": ["年度", "本年度总支出", "本年度收入合计"],
                "temporal_columns": ["年度"],
                "column_profiles": [
                    {"column": "年度", "unique_count": 1, "std": 0},
                    {"column": "本年度总支出", "unique_count": 10, "std": 100},
                    {"column": "本年度收入合计", "unique_count": 10, "std": 120},
                ],
            },
        )
        self.assertEqual(result["keep_numeric_columns"], ["本年度总支出", "本年度收入合计"])
        self.assertEqual(result["exclude_numeric_columns"][0]["column"], "年度")

    def test_fallback_management_accounting_review_generates_domain_output(self) -> None:
        result = _fallback_management_accounting_review(
            "fallback",
            {
                "knowledge_cards": [{"title": "利润质量与收益结构"}],
                "summary_bullets": ["当前样本收入总量与净利润总量可联动复盘。"],
                "margin_rows": [{"指标": "净利率", "值": 0.12}],
                "budget_rows": [{"预算主题": "收入", "偏差额": 120.0}],
                "working_capital_rows": [{"项目": "应收类占用", "金额": 180.0}],
                "leverage_rows": [{"指标": "资产负债率", "值": 0.45}],
                "slice_rows": [{"经营切片": "华东"}],
            },
        )
        self.assertIn("管理会计", result["management_summary"])
        self.assertTrue(result["key_findings"])
        self.assertTrue(result["metric_interpretations"])
        self.assertTrue(result["managerial_actions"])

    def test_fallback_metric_interpretation_uses_actual_stats_and_method_results(self) -> None:
        result = _fallback_metric_interpretation(
            "fallback",
            {
                "core_purpose": "判断投放效果与资源优先级",
                "problem_to_solve": "解释关键指标为什么重要",
                "metric_candidates": [
                    {
                        "metric": "预估点击",
                        "role": "过程/效率指标",
                        "management_question": "它直接服务于当前投放复盘。",
                        "caution": "点击口径需要确认。",
                    }
                ],
                "numeric_summaries": [
                    {
                        "metric": "预估点击",
                        "n": 1000,
                        "mean": 776.92,
                        "median": 31.0,
                        "std": 1200.5,
                        "p25": 12.0,
                        "p75": 205.0,
                    }
                ],
                "method_findings": [
                    {
                        "method": "One-way ANOVA",
                        "metrics": ["预估点击"],
                        "result": "不同媒体之间已形成稳定差异，p=0.0004。",
                    }
                ],
            },
        )
        self.assertEqual(result["metric_cards"][0]["metric"], "预估点击")
        self.assertIn("均值 776.92", result["metric_cards"][0]["business_meaning"])
        self.assertIn("One-way ANOVA", result["metric_cards"][0]["management_impact"])

    def test_fallback_method_review_explains_rmse_in_target_units(self) -> None:
        result = _fallback_method_review(
            "fallback",
            {
                "report_lens": "internet_ops_review",
                "core_purpose": "判断哪些渠道值得优先复盘留存用户",
                "method_runs": [
                    {
                        "method": "神经网络",
                        "method_id": "neural_network",
                        "target": "留存用户",
                        "metrics": {
                            "r_squared": 0.999,
                            "rmse": 25.0,
                            "mae": 15.2,
                            "mean_actual": 320.0,
                        },
                    }
                ],
            },
        )
        review = result["method_reviews"][0]
        self.assertIn("25.000 个 `留存用户` 单位", review["result_meaning"])
        self.assertIn("7.8%", review["result_meaning"])
        self.assertIn("对象排序", review["business_takeaway"])

    def test_fallback_business_background_analysis_links_background_to_decision(self) -> None:
        result = _fallback_business_background_analysis(
            "fallback",
            {
                "report_lens": "internet_ops_review",
                "business_background_name": "渠道活动运营效果分析",
                "business_background_text": "评估渠道与活动效果，为内容策略和资源分配提供依据。",
                "core_purpose": "优化资源分配与策略设计",
                "channel_rows": [{"渠道": "社群"}],
                "activity_rows": [{"活动": "内容上新"}],
                "content_rows": [{"内容主题": "品牌故事"}],
            },
        )
        self.assertIn("渠道活动运营效果分析", result["background_summary"])
        self.assertTrue(any("社群" in item or "内容上新" in item or "品牌故事" in item for item in result["key_points"]))

    def test_fallback_business_object_interpretation_reads_objects(self) -> None:
        result = _fallback_business_object_interpretation(
            "fallback",
            {
                "report_lens": "internet_ops_review",
                "channel_rows": [{"渠道": "社群"}],
                "activity_rows": [{"活动": "内容上新"}],
                "content_rows": [{"内容主题": "品牌故事"}],
            },
        )
        self.assertTrue(result["object_meanings"])
        joined = " ".join(str(item) for item in result["object_meanings"])
        self.assertIn("社群", joined)
        self.assertIn("内容上新", joined)
        self.assertIn("品牌故事", joined)

    def test_fallback_commercial_dimension_review_generates_dimension_actions(self) -> None:
        result = _fallback_commercial_dimension_review(
            "fallback",
            {
                "rows_by_dimension": {
                    "品类": [{"对象": "驱蚊", "销售额总量": "100,000"}],
                    "SKU": [{"对象": "六神止痒花露水", "销售额总量": "50,000"}],
                }
            },
        )
        self.assertIn("京东采销", result["management_summary"])
        self.assertTrue(result["dimension_reviews"])
        self.assertTrue(result["priority_actions"])

    def test_fallback_internet_ops_review_generates_domain_output(self) -> None:
        result = _fallback_internet_ops_review(
            "fallback",
            {
                "topline_rows": [{"核心指标": "活跃用户总量", "总量": "3,384,332", "均值": "3,384", "中位数": "2,977"}],
                "channel_rows": [{"渠道": "社群", "活跃占比": "16.8%", "留存率": "42.1%", "转化率": "5.0%"}],
                "activity_rows": [{"活动": "内容上新", "活跃用户": "4,000", "订单数": "120"}],
                "content_rows": [{"内容主题": "品牌故事", "活跃用户": "5,000"}],
                "method_findings": [{"method": "Correlation Matrix", "result": "活跃用户与留存用户强相关。"}],
            },
        )
        self.assertIn("互联网运营", result["management_summary"])
        self.assertTrue(result["key_findings"])
        self.assertTrue(result["metric_interpretations"])
        self.assertTrue(result["managerial_actions"])
        self.assertTrue(result["validation_agenda"])

    @patch("app.services.codex_service.load_runtime_settings_raw")
    @patch("app.services.codex_service._responses_request")
    def test_request_codex_agentic_json_prefers_bounded_direct_json(self, mock_request, mock_settings) -> None:
        mock_settings.return_value = {
            "api_key": "sk-test",
            "model": "gpt-5.4",
            "base_url": "https://api.openai.com/v1",
            "provider_label": "OpenAI",
            "reasoning_effort": "high",
        }
        mock_request.return_value = {
            "id": "resp_1",
            "output_text": json.dumps({"answer": "ok"}, ensure_ascii=False),
            "output": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir, patch("app.services.codex_service.CODEX_CACHE_DIR", Path(tmpdir)):
            result = _request_codex_agentic_json(
                system_prompt="test",
                user_payload={"a": 1, "b": 2},
                tool_specs=[
                    {
                        "name": "lookup_context",
                        "description": "lookup",
                        "parameters": {
                            "type": "object",
                            "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                            "required": ["fields"],
                            "additionalProperties": False,
                        },
                        "handler": lambda args: {key: args for key in args.get("fields", [])},
                    }
                ],
                fallback_builder=lambda reason, payload: {"reason": reason, "payload": payload},
            )
        self.assertEqual(result["answer"], "ok")
        self.assertEqual(result["mode"], "live_codex_agentic")
        self.assertEqual(result["runtime_state"], "live")
        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(mock_request.call_args.kwargs["timeout_seconds"], 30)

    @patch("app.services.codex_service.load_runtime_settings_raw")
    @patch("app.services.codex_service._responses_request")
    def test_request_codex_agentic_json_uses_local_substitute_on_timeout(self, mock_request, mock_settings) -> None:
        mock_settings.return_value = {
            "api_key": "sk-test",
            "model": "gpt-5.4",
            "base_url": "https://api.openai.com/v1",
            "provider_label": "OpenAI",
            "reasoning_effort": "high",
        }
        mock_request.side_effect = TimeoutError("direct structured response timed out")

        with tempfile.TemporaryDirectory() as tmpdir, patch("app.services.codex_service.CODEX_CACHE_DIR", Path(tmpdir)):
            result = _request_codex_agentic_json(
                system_prompt="test",
                user_payload={"a": 1, "b": 2},
                tool_specs=[],
                fallback_builder=lambda reason, payload: {"reason": reason, "payload": payload},
            )
        self.assertEqual(result["mode"], "local_deterministic_agentic_substitute")
        self.assertEqual(result["runtime_state"], "local")
        self.assertEqual(result["degradation_state"], "soft_local")

    @patch("app.services.codex_service.load_runtime_settings_raw")
    @patch("app.services.codex_service._responses_request")
    def test_request_codex_json_reuses_disk_cache(self, mock_request, mock_settings) -> None:
        mock_settings.return_value = {
            "api_key": "sk-test",
            "model": "gpt-5.4",
            "base_url": "https://api.openai.com/v1",
            "provider_label": "OpenAI",
            "reasoning_effort": "high",
        }
        mock_request.return_value = {
            "id": "resp_cache_json",
            "output_text": json.dumps({"answer": "cached ok"}, ensure_ascii=False),
            "output": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir, patch("app.services.codex_service.CODEX_CACHE_DIR", Path(tmpdir)):
            first = _request_codex_json(
                system_prompt="cache-test",
                user_payload={"x": 1},
                fallback_builder=lambda reason, payload: {"reason": reason, "payload": payload},
            )
            self.assertEqual(first["answer"], "cached ok")
            self.assertFalse(first.get("cache_hit"))
            self.assertEqual(mock_request.call_count, 1)

            mock_request.reset_mock()
            second = _request_codex_json(
                system_prompt="cache-test",
                user_payload={"x": 1},
                fallback_builder=lambda reason, payload: {"reason": reason, "payload": payload},
            )
            self.assertEqual(second["answer"], "cached ok")
            self.assertTrue(second.get("cache_hit"))
            self.assertEqual(second["runtime_state"], "cached")
            self.assertEqual(mock_request.call_count, 0)

    @patch("app.services.codex_service.load_runtime_settings_raw")
    @patch("app.services.codex_service._responses_request")
    def test_request_codex_agentic_json_reuses_disk_cache(self, mock_request, mock_settings) -> None:
        mock_settings.return_value = {
            "api_key": "sk-test",
            "model": "gpt-5.4",
            "base_url": "https://api.openai.com/v1",
            "provider_label": "OpenAI",
            "reasoning_effort": "high",
        }
        mock_request.return_value = {
            "id": "resp_cache_agentic",
            "output_text": json.dumps({"answer": "agentic cached ok"}, ensure_ascii=False),
            "output": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir, patch("app.services.codex_service.CODEX_CACHE_DIR", Path(tmpdir)):
            first = _request_codex_agentic_json(
                system_prompt="agentic-cache-test",
                user_payload={"x": 2},
                tool_specs=[],
                fallback_builder=lambda reason, payload: {"reason": reason, "payload": payload},
            )
            self.assertEqual(first["answer"], "agentic cached ok")
            self.assertFalse(first.get("cache_hit"))
            self.assertEqual(mock_request.call_count, 1)

            mock_request.reset_mock()
            second = _request_codex_agentic_json(
                system_prompt="agentic-cache-test",
                user_payload={"x": 2},
                tool_specs=[],
                fallback_builder=lambda reason, payload: {"reason": reason, "payload": payload},
            )
            self.assertEqual(second["answer"], "agentic cached ok")
            self.assertTrue(second.get("cache_hit"))
            self.assertEqual(second["runtime_state"], "cached")
            self.assertEqual(mock_request.call_count, 0)

    @patch("app.services.codex_service._request_codex_agentic_json")
    def test_native_entrypoints_route_through_agentic_helper(self, mock_agentic) -> None:
        mock_agentic.return_value = {"mode": "live_codex_agentic"}
        self.assertEqual(codex_complete_input_fields({"columns": ["a"]})["mode"], "live_codex_agentic")
        self.assertEqual(codex_statistical_scope({"numeric_columns": ["x"]})["mode"], "live_codex_agentic")
        self.assertEqual(codex_management_accounting_review({"summary_bullets": []})["mode"], "live_codex_agentic")
        self.assertEqual(codex_classify_business_context({"headers": ["a"]})["mode"], "live_codex_agentic")
        self.assertEqual(codex_judge_report({"executive_summary": []})["mode"], "live_codex_agentic")
        self.assertEqual(codex_summarize_eval_feedback({"results": []})["mode"], "live_codex_agentic")
        self.assertEqual(mock_agentic.call_count, 6)

    @patch("app.services.codex_service._request_codex_agentic_json")
    def test_codex_generate_r_workflow_replaces_unsafe_live_script(self, mock_agentic) -> None:
        mock_agentic.return_value = {
            "mode": "live_codex_agentic",
            "runtime_state": "live",
            "live_available": True,
            "model": "gpt-5.4",
            "provider_label": "OpenAI",
            "reasoning_effort": "low",
            "overview": "live",
            "clean_script": "clean",
            "run_script": "run",
            "analysis_script": "\n".join(
                [
                    "numeric_complete <- na.omit(df[numeric_cols])",
                    "if (nrow(numeric_complete) >= 5) {",
                    "  pca_fit <- prcomp(numeric_complete, center = TRUE, scale. = TRUE)",
                    "  km <- kmeans(numeric_complete[, seq_len(min(ncol(numeric_complete), 4)), drop = FALSE], centers = 3)",
                    "}",
                ]
            ),
            "expected_outputs": [],
        }

        result = codex_generate_r_workflow(
            {
                "dataset_name": "demo",
                "sheet_name": "Sheet1",
                "report_lens": "generic_business_review",
                "columns": ["date", "gmv", "orders"],
                "numeric_columns": ["gmv", "orders"],
                "categorical_columns": [],
                "object_columns": ["item_id"],
                "temporal_columns": ["date"],
                "column_role_registry": {},
                "sample_rows": [],
            }
        )

        self.assertEqual(result["mode"], "validated_safe_fallback")
        self.assertIn("pca_candidate_cols", result["analysis_script"])
        self.assertIn("cluster_feature_pool", result["analysis_script"])
        self.assertIn("cluster_member_detail.csv", result["analysis_script"])


if __name__ == "__main__":
    unittest.main()
