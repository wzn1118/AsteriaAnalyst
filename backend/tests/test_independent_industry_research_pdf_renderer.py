from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from app.services.independent_industry_research_pdf_renderer import (
    render_independent_industry_research_pdf_bundle,
)


class IndependentIndustryResearchPdfRendererTests(unittest.TestCase):
    def _seed_files(self, output_dir: Path) -> None:
        (output_dir / "industry_research_report.md").write_text(
            "\n".join(
                [
                    "# 行业研究报告：平台零售电商 / 淘宝/天猫",
                    "",
                    "## 1. 封面",
                    "",
                    "- 报告名称：行业研究报告：平台零售电商 / 淘宝/天猫",
                    "- 目标读者：管理层",
                    "",
                    "## 2. 研究范围",
                    "",
                    "- 只解释行业背景、平台机制、竞品参考与 benchmark 边界。",
                    "",
                    "## 3. 研究问题",
                    "",
                    "- 当前平台规则如何影响商品经营？",
                    "",
                    "## 4. 行业背景",
                    "",
                    "- 当前行业背景需要结合外部来源理解。",
                    "",
                    "## 5. 市场结构",
                    "",
                    "- 当前更适合从商品、类目、店铺与品牌结构理解市场格局。",
                    "",
                    "## 6. 产业链与价值链",
                    "",
                    "- 当前价值链位置：平台内商品经营与交易承接。",
                    "",
                    "## 7. 平台机制或渠道机制",
                    "",
                    "- 平台规则、流量、评价、履约和售后机制会影响经营理解。",
                    "",
                    "## 8. 竞争格局",
                    "",
                    "- 竞争格局只作为外部参考框架。",
                    "",
                    "## 9. 用户/消费者趋势",
                    "",
                    "- 用户趋势只作背景参考。",
                    "",
                    "## 10. 供给结构",
                    "",
                    "- 供给结构研究只用于业务理解。",
                    "",
                    "## 11. 商业模式与利润机制",
                    "",
                    "- 当前商业模式需要外部资料辅助解释。",
                    "",
                    "## 12. 指标口径",
                    "",
                    "- GMV、销量、转化、履约、评价和利润口径必须先统一定义。",
                    "",
                    "## 13. benchmark 与可比性限制",
                    "",
                    "- benchmark 只能作为参考，必须写清口径限制与不可比说明。",
                    "",
                    "## 14. 外部风险",
                    "",
                    "- 监管、平台规则与消费者权益环境会影响行业理解。",
                    "",
                    "## 15. 对主报告的背景启发",
                    "",
                    "- 可为主报告提供背景启发，但不替代主报告分析。",
                    "",
                    "## 16. 资料来源与附录",
                    "",
                    "- S001 淘宝规则频道 / 淘宝规则 / credibility=high",
                    "- S002 天猫规则中心 / 天猫规则 / credibility=high",
                    "- S003 Alibaba Group 投资者关系 / Alibaba Group / credibility=high",
                    "- S004 国家统计局数据查询 / 国家统计局 / credibility=high",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (output_dir / "industry_research_sources.json").write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "source_id": "S001",
                            "title": "淘宝规则频道",
                            "publisher": "淘宝规则",
                            "url": "https://rulechannel.taobao.com/",
                            "publish_date": "",
                            "source_type": "官方平台规则",
                            "credibility_level": "high",
                            "usable_for": ["平台机制"],
                            "not_usable_for": ["dataset_evidence"],
                            "limitation": "规则说明不等于经营结果",
                        },
                        {
                            "source_id": "S002",
                            "title": "天猫规则中心",
                            "publisher": "天猫规则",
                            "url": "https://rule.tmall.com/",
                            "publish_date": "",
                            "source_type": "官方平台规则",
                            "credibility_level": "high",
                            "usable_for": ["平台机制"],
                            "not_usable_for": ["dataset_evidence"],
                            "limitation": "规则说明不等于经营结果",
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (output_dir / "citation_manifest_industry.json").write_text(
            json.dumps(
                [
                    {
                        "claim_id": "CLM-001",
                        "claim_text": "行业背景需要外部来源解释。",
                        "source_id": "S001",
                        "source_title": "淘宝规则频道",
                        "publisher": "淘宝规则",
                        "publish_date": "",
                        "credibility_level": "high",
                        "used_in_page": 4,
                        "used_in_section": "4. 行业背景",
                        "usage_type": "industry_background",
                        "limitation": "规则说明不等于经营结果",
                    },
                    {
                        "claim_id": "CLM-004",
                        "claim_text": "平台规则、流量、评价、履约和售后机制会影响经营理解。",
                        "source_id": "S002",
                        "source_title": "天猫规则中心",
                        "publisher": "天猫规则",
                        "publish_date": "",
                        "credibility_level": "high",
                        "used_in_page": 7,
                        "used_in_section": "7. 平台机制或渠道机制",
                        "usage_type": "platform_mechanism",
                        "limitation": "规则说明不等于经营结果",
                    },
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (output_dir / "industry_context_analysis.md").write_text("# industry_context_analysis\n\n- 行业背景说明。\n", encoding="utf-8")
        (output_dir / "industry_benchmark_synthesis.md").write_text("# industry_benchmark_synthesis\n\n- benchmark 只用于参考。\n", encoding="utf-8")
        (output_dir / "industry_metric_definition.md").write_text("# industry_metric_definition\n\n- 统一口径说明。\n", encoding="utf-8")
        (output_dir / "industry_risk_scan.md").write_text("# industry_risk_scan\n\n- 风险扫描说明。\n", encoding="utf-8")
        (output_dir / "industry_research_scope.json").write_text(
            json.dumps(
                {
                    "inferred_industry": "平台零售电商",
                    "inferred_platform": "淘宝/天猫",
                    "inferred_business_model": "platform_marketplace_ecommerce",
                    "value_chain_position": "平台内商品经营与交易承接",
                    "target_reader": "管理层",
                    "unsupported_questions": ["当前数据能否直接证明经营拍板。"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (output_dir / "industry_research_question_bank.md").write_text("# industry_research_question_bank\n\n- 平台规则如何影响经营？\n", encoding="utf-8")
        (output_dir / "industry_web_search_plan.md").write_text("# industry_web_search_plan\n\n- query\n", encoding="utf-8")
        (output_dir / "management_report.pdf").write_text("do-not-touch", encoding="utf-8")

    def test_renderer_outputs_required_files_and_does_not_touch_main_report(self) -> None:
        try:
            from pypdf import PdfReader
        except Exception:
            self.skipTest("pypdf unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs" / "industry_research"
            output_dir.mkdir(parents=True, exist_ok=True)
            self._seed_files(output_dir)
            main_report_path = output_dir / "management_report.pdf"
            before = main_report_path.read_text(encoding="utf-8")

            result = render_independent_industry_research_pdf_bundle(output_dir)

            self.assertTrue((output_dir / "industry_research_report.pdf").exists())
            self.assertTrue((output_dir / "industry_research_report.html").exists())
            self.assertTrue((output_dir / "industry_research_appendix.md").exists())
            self.assertTrue((output_dir / "industry_research_page_audit.csv").exists())
            self.assertEqual(main_report_path.read_text(encoding="utf-8"), before)
            self.assertGreaterEqual(result["page_count"], 15)
            self.assertLessEqual(result["page_count"], 30)
            pages = len(PdfReader(str(output_dir / "industry_research_report.pdf")).pages)
            self.assertGreaterEqual(pages, 15)
            self.assertLessEqual(pages, 30)

    def test_page_audit_has_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "outputs" / "industry_research"
            output_dir.mkdir(parents=True, exist_ok=True)
            self._seed_files(output_dir)
            render_independent_industry_research_pdf_bundle(output_dir)
            with (output_dir / "industry_research_page_audit.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            row = rows[0]
            for key in [
                "page_number",
                "page_title",
                "has_source",
                "has_boundary_note",
                "has_specific_industry_content",
                "has_unsupported_dataset_claim",
                "has_main_report_content",
                "has_r_workflow_content",
                "passed",
                "issue",
            ]:
                self.assertIn(key, row)


if __name__ == "__main__":
    unittest.main()
