from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.models import SmartReportRequest
from app.services.independent_industry_research_orchestrator import (
    run_independent_industry_research_orchestrator,
)


class IndependentIndustryResearchOrchestratorTests(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "item_id": ["i1", "i2", "i3"],
                "shop_id": ["shop-a", "shop-b", "shop-a"],
                "category": ["beauty", "phone", "beauty"],
                "price": [29.9, 199.0, 59.0],
                "sales_volume": [100, 30, 50],
                "GMV": [2990, 5970, 2950],
                "review_count": [12, 5, 8],
                "rating": [4.8, 4.2, 4.6],
            }
        )

    def test_disabled_mode_skips_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-disabled"
            result = run_independent_industry_research_orchestrator(
                report_dir=report_dir,
                report_id="disabled01",
                dataset_name="淘宝商品聚合数据",
                sheet_name="Sheet1",
                frame=self._frame(),
                request=SmartReportRequest(
                    sheet_name="Sheet1",
                    industry_research_standalone_enabled=False,
                ),
                router_result={"business_profile": "ecommerce_product_operations_report"},
                deep_context_understanding={"summary": "x"},
                main_report_job_id="main-1",
                r_workflow_job_id="r-1",
            )
            self.assertFalse(result["industry_research_chain_executed"])
            self.assertEqual(result["industry_research_mode"], "disabled")
            self.assertFalse((report_dir / "outputs" / "industry_research").exists())

    def test_enabled_mode_writes_independent_outputs_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-enabled"
            result = run_independent_industry_research_orchestrator(
                report_dir=report_dir,
                report_id="enabled01",
                dataset_name="淘宝商品聚合数据",
                sheet_name="Sheet1",
                frame=self._frame(),
                request=SmartReportRequest(
                    sheet_name="Sheet1",
                    industry_research_standalone_enabled=True,
                    use_r_workflow=True,
                    user_requirement="输出行业研究报告",
                    problem_to_solve="分析平台机制与竞品参考",
                ),
                router_result={
                    "business_profile": "ecommerce_product_operations_report",
                    "secondary_profile": "internet_operations_report",
                    "decisive_object_grain": "商品/店铺/SKU",
                    "routing_reason": "商品经营主链",
                },
                deep_context_understanding={
                    "summary": "deep context",
                    "universal_metric_mining_result": {
                        "business_profile": "ecommerce_product_operations_report",
                        "domain_metric_registry": {
                            "recommended_report_chain": "ecommerce_product_operations_report",
                            "direct_metrics": ["gmv", "sales_volume"],
                            "derived_metrics": ["average_order_value"],
                            "proxy_metrics": ["review_per_order_proxy"],
                            "unsupported_metrics": ["profitability"],
                        },
                        "derived_metrics": [{"metric_id": "average_order_value"}],
                        "proxy_metrics": [{"metric_id": "review_per_order_proxy"}],
                    },
                    "domain_metric_registry": {
                        "recommended_report_chain": "ecommerce_product_operations_report",
                        "direct_metrics": ["gmv", "sales_volume"],
                        "derived_metrics": ["average_order_value"],
                        "proxy_metrics": ["review_per_order_proxy"],
                        "unsupported_metrics": ["profitability"],
                    },
                },
                main_report_job_id="main-1",
                r_workflow_job_id="r-1",
            )
            output_dir = report_dir / "outputs" / "industry_research"
            self.assertTrue(result["industry_research_chain_executed"])
            self.assertTrue(output_dir.exists())
            for filename in [
                "industry_research_scope.md",
                "industry_research_scope.json",
                "business_scene_inference.json",
                "industry_data_context_summary.md",
                "industry_data_context_summary.json",
                "source_fact_table.csv",
                "industry_research_question_bank_from_data.md",
                "industry_research_boundary_from_data.md",
                "industry_research_question_bank.md",
                "industry_web_search_plan.md",
                "industry_research_sources.json",
                "industry_context_analysis.md",
                "industry_benchmark_synthesis.md",
                "industry_platform_mechanism.md",
                "industry_competitor_context.md",
                "industry_metric_definition.md",
                "benchmark_metric_registry.json",
                "benchmark_comparability_matrix.json",
                "platform_difference_table.json",
                "metric_definition_comparison.json",
                "benchmark_comparability_matrix.csv",
                "metric_definition_comparison.csv",
                "platform_difference_table.csv",
                "industry_risk_scan.md",
                "industry_regulation_risk.json",
                "industry_research_report.md",
                "industry_research_report.pdf",
                "industry_research_report.html",
                "citation_manifest_industry.json",
                "industry_research_boundary_check.json",
                "industry_research_source_audit.md",
                "industry_research_appendix.md",
                "manual_confirmation_checklist.md",
                "industry_research_acceptance_report.md",
                "router_metric_chain_integration.md",
                "industry_research_page_audit.csv",
                "industry_research_quality_score.json",
                "industry_research_quality_gate_result.json",
                "stage_trace.json",
                "stage_trace.md",
            ]:
                self.assertTrue((output_dir / filename).exists(), msg=filename)
            for forbidden in [
                "management_report.pdf",
                "management_report.html",
                "analyst_appendix.xlsx",
                "r_cleaned_data",
                "r_analysis_outputs",
                "r_visualization_outputs",
                "r_pdf_explanation",
            ]:
                self.assertFalse((output_dir / forbidden).exists(), msg=forbidden)
            self.assertIn("uploaded_file_name", result["shared_inputs_used"])
            self.assertIn("sheet_names", result["shared_inputs_used"])
            self.assertIn("business_profile_router_result.json", result["shared_inputs_used"])
            self.assertIn("universal_metric_mining_result.json", result["shared_inputs_used"])
            self.assertIn("domain_metric_registry.json", result["shared_inputs_used"])
            boundary = json.loads(
                (output_dir / "industry_research_boundary_check.json").read_text(
                    encoding="utf-8"
                )
            )
            scope = json.loads((output_dir / "industry_research_scope.json").read_text(encoding="utf-8"))
            self.assertTrue(scope["research_topics"])
            self.assertTrue(all(topic.get("expected_facts") for topic in scope["research_topics"]))
            self.assertTrue(all(topic.get("unsupported_claims") for topic in scope["research_topics"]))
            self.assertTrue(all(topic.get("required_source_types") for topic in scope["research_topics"]))
            self.assertTrue(all(topic.get("depends_on_dataset_signals") for topic in scope["research_topics"]))
            data_context = json.loads((output_dir / "industry_data_context_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(data_context["dataset_name"], "淘宝商品聚合数据")
            self.assertEqual(data_context["sheet_name"], "Sheet1")
            self.assertGreater(data_context["row_count"], 0)
            self.assertGreater(data_context["column_count"], 0)
            self.assertTrue(data_context["object_like_fields"])
            self.assertTrue(data_context["amount_like_fields"])
            self.assertTrue(data_context["candidate_business_objects"])
            self.assertTrue(data_context["candidate_observation_units"])
            self.assertTrue(data_context["can_support_what"])
            self.assertTrue(data_context["cannot_support_what"])
            self.assertIn("field_role_evidence", data_context)
            self.assertIn("sample_value_evidence", data_context)
            self.assertIn("ambiguous_fields", data_context)
            self.assertTrue(data_context["used_router_result"])
            self.assertTrue(data_context["used_universal_metric_mining"])
            self.assertTrue(data_context["used_domain_metric_registry"])
            self.assertIn("router_context", data_context)
            self.assertIn("GMV", data_context["field_role_evidence"])
            self.assertIn("item_id", data_context["field_role_evidence"])
            self.assertTrue(data_context["field_role_evidence"]["GMV"]["evidence"])
            self.assertTrue(data_context["field_role_evidence"]["item_id"]["evidence"])

            scene = json.loads((output_dir / "business_scene_inference.json").read_text(encoding="utf-8"))
            self.assertTrue(scene["inferred_industry"])
            self.assertTrue(scene["inferred_platform"])
            self.assertTrue(scene["value_chain_position"])
            self.assertTrue(scene["evidence_from_dataset"])
            self.assertIn("candidate_business_contexts", scene)
            self.assertIn("manual_confirmation_needed", scene)
            self.assertIn("metric_mining_context", scene)
            if scene["inferred_platform"] in {"行业/平台待确认", "平台电商（待确认）"} or scene["inferred_business_model"] == "unclear_business_model":
                self.assertTrue(scene["why_uncertain"])
                self.assertTrue(scene["top_candidates"])
                self.assertTrue(scene["required_manual_confirmation"])

            self.assertTrue(boundary["passed"])
            self.assertTrue(boundary["data_context_read"])
            self.assertTrue(boundary["industry_data_context_summary_generated"])
            self.assertEqual(boundary["current_dataset_claim_errors"], [])
            self.assertEqual(boundary["stage_6_section_failures"], [])
            self.assertEqual(boundary["stage_7_benchmark_failures"], [])
            self.assertEqual(boundary["stage_8_risk_failures"], [])
            self.assertEqual(boundary["external_claims_without_sources"], [])
            self.assertEqual(boundary["dataset_evidence_misuse"], [])
            self.assertEqual(boundary["benchmark_boundary_errors"], [])
            self.assertFalse(boundary["main_report_contamination"])
            self.assertFalse(boundary["r_workflow_contamination"])
            stage_trace = json.loads((output_dir / "stage_trace.json").read_text(encoding="utf-8"))
            stage_ids = [item["stage_id"] for item in stage_trace["stages"]]
            self.assertEqual(
                stage_ids,
                [
                    "stage_1_dataset_grounding",
                    "stage_2_business_scene_inference",
                    "stage_3_research_plan_generation",
                    "stage_4_source_search_and_collection",
                    "stage_5_source_fact_extraction",
                    "stage_6_platform_mechanism_analysis",
                    "stage_7_benchmark_comparability_analysis",
                    "stage_8_risk_and_regulation_analysis",
                    "stage_9_report_synthesis",
                    "stage_10_appendix_and_tables",
                    "stage_11_quality_gate",
                    "stage_12_release_packaging",
                ],
            )
            self.assertTrue(all("input_artifacts" in item for item in stage_trace["stages"]))
            self.assertTrue(all("output_artifacts" in item for item in stage_trace["stages"]))
            report_markdown = (output_dir / "industry_research_report.md").read_text(encoding="utf-8")
            for section_title in [
                "行业定位与研究边界",
                "数据所反映的业务场景",
                "行业背景",
                "平台机制",
                "市场结构与竞争格局",
                "指标口径与 benchmark 可比性",
                "成本/利润/履约/转化边界",
                "风险与监管环境",
                "对主报告可提供的背景支持",
                "当前不能支持的经营判断",
                "来源说明",
            ]:
                self.assertIn(f"## {section_title}", report_markdown)
            for banned in [
                "建议后续研究",
                "可从",
                "应重点关注",
                "更适合研究",
                "当前只形成框架",
                "当前只给出方向",
                "???",
                "unclear_business_model",
                "具体平台未识别",
                "商业模式待补充确认",
            ]:
                self.assertNotIn(banned, report_markdown)
            self.assertNotIn("行业/平台待确认", report_markdown)
            self.assertIn("[S", report_markdown)
            self.assertIn("chapter_judgement:", report_markdown)
            self.assertIn("key_evidence:", report_markdown)
            self.assertIn("data_relation:", report_markdown)
            self.assertIn("non_extrapolation_boundary:", report_markdown)
            question_bank = (output_dir / "industry_research_question_bank.md").read_text(encoding="utf-8")
            self.assertIn("why_it_matters", question_bank)
            sources_payload = json.loads((output_dir / "industry_research_sources.json").read_text(encoding="utf-8"))
            self.assertTrue(sources_payload["sources"])
            self.assertTrue(all(source.get("atomic_facts") for source in sources_payload["sources"]))
            self.assertTrue(all(source.get("claim_summary") for source in sources_payload["sources"]))
            self.assertTrue(all("usable_for_sections" in source for source in sources_payload["sources"]))
            self.assertTrue(all(source.get("verification_status") for source in sources_payload["sources"]))
            self.assertTrue(all(source.get("page_or_section_hint") for source in sources_payload["sources"]))
            self.assertTrue(any(source.get("source_level") in {"page_fact", "document_fact"} for source in sources_payload["sources"]))
            for source in sources_payload["sources"]:
                if source.get("source_level") == "lead_only":
                    self.assertNotEqual(source.get("verification_status"), "verified_page_fact")
            source_fact_table = pd.read_csv(output_dir / "source_fact_table.csv")
            self.assertFalse(source_fact_table.empty)
            self.assertIn("原子事实", source_fact_table.columns)
            self.assertIn("结论摘要", source_fact_table.columns)
            self.assertIn("核验状态", source_fact_table.columns)
            self.assertIn("可支持平台机制", source_fact_table.columns)
            source_audit = (output_dir / "industry_research_source_audit.md").read_text(encoding="utf-8")
            self.assertIn("claim_summary", source_audit)
            self.assertIn("atomic_facts", source_audit)
            context_md = (output_dir / "industry_context_analysis.md").read_text(encoding="utf-8")
            mechanism_md = (output_dir / "industry_platform_mechanism.md").read_text(encoding="utf-8")
            competitor_md = (output_dir / "industry_competitor_context.md").read_text(encoding="utf-8")
            for markdown in [context_md, mechanism_md, competitor_md]:
                self.assertIn("section_conclusion", markdown)
                self.assertIn("source_backed_facts", markdown)
                self.assertIn("relation_to_uploaded_data", markdown)
                self.assertIn("unsupported_claims", markdown)
                self.assertIn("manual_confirmation_needed", markdown)
                self.assertNotIn("当前更适合从", markdown)
                self.assertNotIn("更适合从", markdown)
                self.assertNotIn("需要单独研究", markdown)
                self.assertNotIn("仅形成框架", markdown)
                self.assertNotIn("当前只给出研究方向", markdown)
                self.assertNotIn("当前仅定位到机构索引页", markdown)
            self.assertIn("[S", context_md)
            self.assertIn("[S", mechanism_md)
            self.assertIn("[S", competitor_md)
            benchmark_registry = json.loads((output_dir / "benchmark_metric_registry.json").read_text(encoding="utf-8"))
            benchmark_matrix = json.loads((output_dir / "benchmark_comparability_matrix.json").read_text(encoding="utf-8"))
            metric_definition = json.loads((output_dir / "metric_definition_comparison.json").read_text(encoding="utf-8"))
            self.assertTrue(benchmark_registry)
            self.assertTrue(benchmark_matrix)
            self.assertTrue(metric_definition)
            self.assertTrue(all(row.get("source_backed_facts") for row in benchmark_matrix))
            covered_metrics = {row["metric_id"] for row in benchmark_registry}
            self.assertEqual(
                covered_metrics,
                {"GMV", "Revenue", "FreightCost", "order_count", "rating", "conversion", "sales_amount", "sales_volume", "ROI"},
            )
            self.assertTrue(any(not row["directly_comparable"] for row in benchmark_matrix))
            benchmark_matrix_csv = pd.read_csv(output_dir / "benchmark_comparability_matrix.csv")
            metric_definition_csv = pd.read_csv(output_dir / "metric_definition_comparison.csv")
            platform_difference_csv = pd.read_csv(output_dir / "platform_difference_table.csv")
            self.assertFalse(benchmark_matrix_csv.empty)
            self.assertFalse(metric_definition_csv.empty)
            self.assertFalse(platform_difference_csv.empty)
            self.assertIn("不可直接可比原因", benchmark_matrix_csv.columns)
            self.assertIn("行业常见口径", metric_definition_csv.columns)
            self.assertIn("差异维度", platform_difference_csv.columns)
            risk_scan = (output_dir / "industry_risk_scan.md").read_text(encoding="utf-8")
            self.assertIn("source_backed_facts", risk_scan)
            self.assertIn("background_risk_note", risk_scan)
            self.assertIn("benchmark_interpretation_note", risk_scan)
            regulation_risk = json.loads((output_dir / "industry_regulation_risk.json").read_text(encoding="utf-8"))
            self.assertTrue(regulation_risk)
            self.assertTrue(all(risk.get("source_backed_facts") for risk in regulation_risk))
            self.assertTrue(all("background_only" in risk for risk in regulation_risk))
            self.assertTrue(all(risk.get("background_risk_note") for risk in regulation_risk))
            self.assertTrue(all("affects_benchmark_interpretation" in risk for risk in regulation_risk))
            self.assertTrue(all(risk.get("benchmark_interpretation_note") for risk in regulation_risk))
            risk_topics = {risk["risk_topic"] for risk in regulation_risk}
            self.assertEqual(
                risk_topics,
                {"平台规则变化", "履约/售后监管", "消费者权益", "价格竞争/低价策略", "数据本身不支持的经营判断风险"},
            )
            appendix_md = (output_dir / "industry_research_appendix.md").read_text(encoding="utf-8")
            self.assertIn("来源事实展开表", appendix_md)
            self.assertIn("原子事实", appendix_md)
            self.assertIn("核验状态", appendix_md)
            self.assertIn("benchmark 可比性矩阵", appendix_md)
            self.assertIn("指标口径对照表", appendix_md)
            self.assertIn("平台差异表", appendix_md)
            self.assertIn("需要人工确认的问题清单", appendix_md)
            self.assertIn("当前数据与外部资料的证据边界表", appendix_md)
            manual_confirmation_md = (output_dir / "manual_confirmation_checklist.md").read_text(encoding="utf-8")
            self.assertTrue(manual_confirmation_md.strip())
            self.assertIn("M01", manual_confirmation_md)
            acceptance_md = (output_dir / "industry_research_acceptance_report.md").read_text(encoding="utf-8")
            for section_title in [
                "本次测试数据",
                "是否通过",
                "不通过原因",
                "仍需人工确认的部分",
                "当前最强章节",
                "当前最弱章节",
                "关键验收观察",
                "总判断",
            ]:
                self.assertIn(f"## {section_title}", acceptance_md)
            self.assertNotIn("???", acceptance_md)
            citation_manifest = json.loads((output_dir / "citation_manifest_industry.json").read_text(encoding="utf-8"))
            self.assertTrue(citation_manifest["citations"])
            self.assertTrue(all(item.get("publish_date") for item in citation_manifest["citations"]))
            self.assertTrue(all(item.get("citation_snippet") for item in citation_manifest["citations"]))
            self.assertTrue(all(item.get("page_or_section_hint") for item in citation_manifest["citations"]))
            self.assertTrue(all(item.get("source_level") for item in citation_manifest["citations"]))
            self.assertTrue(all(item.get("verification_status") for item in citation_manifest["citations"]))
            self.assertTrue(all("atomic_facts" in item for item in citation_manifest["citations"]))
            self.assertTrue(all("citation_count" in item for item in citation_manifest["citations"]))
            integration_md = (output_dir / "router_metric_chain_integration.md").read_text(encoding="utf-8")
            self.assertIn("stage_1.used_router_result: True", integration_md)
            self.assertIn("stage_1.used_universal_metric_mining: True", integration_md)
            self.assertIn("stage_3.router_context.business_profile", integration_md)
            self.assertIn("stage_7.router_context.business_profile", integration_md)
            self.assertIn("stage_11.data_context_read: True", integration_md)

    def test_enabled_mode_fails_without_universal_metric_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-no-metric-context"
            result = run_independent_industry_research_orchestrator(
                report_dir=report_dir,
                report_id="enabled02",
                dataset_name="娣樺疂鍟嗗搧鑱氬悎鏁版嵁",
                sheet_name="Sheet1",
                frame=self._frame(),
                request=SmartReportRequest(
                    sheet_name="Sheet1",
                    industry_research_standalone_enabled=True,
                    user_requirement="杈撳嚭琛屼笟鐮旂┒鎶ュ憡",
                ),
                router_result={"business_profile": "ecommerce_product_operations_report"},
                deep_context_understanding={"summary": "deep context only"},
                main_report_job_id="main-1",
                r_workflow_job_id="r-1",
            )
            output_dir = report_dir / "outputs" / "industry_research"
            boundary = json.loads((output_dir / "industry_research_boundary_check.json").read_text(encoding="utf-8"))
            gate = json.loads((output_dir / "industry_research_quality_gate_result.json").read_text(encoding="utf-8"))
            self.assertFalse(boundary["passed"])
            self.assertFalse(boundary["data_context_read"])
            self.assertFalse(gate["passed"])
            self.assertIn("industry_research_chain_did_not_read_universal_metric_mining_result", gate["data_context_failures"])
            self.assertFalse(result["success"])

    def test_stage2_downgrades_cleanly_when_router_result_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "smart-report-missing-router"
            result = run_independent_industry_research_orchestrator(
                report_dir=report_dir,
                report_id="enabled03",
                dataset_name="淘宝商品聚合数据",
                sheet_name="Sheet1",
                frame=self._frame(),
                request=SmartReportRequest(
                    sheet_name="Sheet1",
                    industry_research_standalone_enabled=True,
                    user_requirement="输出行业研究报告",
                ),
                router_result={},
                deep_context_understanding={
                    "summary": "deep context",
                    "universal_metric_mining_result": {
                        "business_profile": "ecommerce_product_operations_report",
                        "domain_metric_registry": {
                            "recommended_report_chain": "ecommerce_product_operations_report",
                            "direct_metrics": ["gmv", "sales_volume"],
                            "derived_metrics": ["average_order_value"],
                            "proxy_metrics": ["review_per_order_proxy"],
                            "unsupported_metrics": ["profitability"],
                        },
                    },
                    "domain_metric_registry": {
                        "recommended_report_chain": "ecommerce_product_operations_report",
                        "direct_metrics": ["gmv", "sales_volume"],
                        "derived_metrics": ["average_order_value"],
                        "proxy_metrics": ["review_per_order_proxy"],
                        "unsupported_metrics": ["profitability"],
                    },
                },
                main_report_job_id="main-1",
                r_workflow_job_id="r-1",
            )
            output_dir = report_dir / "outputs" / "industry_research"
            scene = json.loads((output_dir / "business_scene_inference.json").read_text(encoding="utf-8"))
            self.assertTrue(scene["manual_confirmation_needed"])
            self.assertTrue(scene["why_uncertain"])
            self.assertTrue(scene["required_manual_confirmation"])
            self.assertTrue(any("router_result" in note for note in scene["ambiguity_notes"]))
            self.assertTrue(scene["candidate_business_contexts"])
            integration_md = (output_dir / "router_metric_chain_integration.md").read_text(encoding="utf-8")
            self.assertIn("router_result.business_profile: `missing`", integration_md)
            self.assertTrue(result["industry_research_chain_executed"])


if __name__ == "__main__":
    unittest.main()
