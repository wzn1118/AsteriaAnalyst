from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.models import RWorkflowIntelligenceRequest
from app.services.path_service import REPORTS_DIR
from app.services.r_artifact_intelligence_service import run_r_artifact_intelligence_flow


class RArtifactIntelligenceServiceTests(unittest.TestCase):
    def _prepare_r_workflow_bundle(self, report_id: str) -> Path:
        report_dir = REPORTS_DIR / f"smart-report-{report_id}"
        if report_dir.exists():
            shutil.rmtree(report_dir)
        workflow_dir = report_dir / "r-workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workbook_path = workflow_dir / f"{report_id}-r-statistics-summary.xlsx"
        with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
            pd.DataFrame(
                [
                    {"field": "report_id", "value": report_id},
                    {"field": "dataset_name", "value": "demo"},
                ]
            ).to_excel(writer, index=False, sheet_name="overview")
            pd.DataFrame(
                [
                    {"column": "gmv", "mean": 1125, "median": 1100},
                    {"column": "orders", "mean": 11.25, "median": 11},
                ]
            ).to_excel(writer, index=False, sheet_name="summary_stats")
            pd.DataFrame(
                [
                    {"sheet_name": "summary_stats", "row_count": 2, "path": "summary_stats.csv"},
                ]
            ).to_excel(writer, index=False, sheet_name="results_index")
        pd.DataFrame(
            [
                {"category": "A", "gmv": 1000, "orders": 10},
                {"category": "B", "gmv": 1200, "orders": 12},
            ]
        ).to_csv(workflow_dir / "cleaned_dataset.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(
            [
                {"dimension": "category", "category": "A", "metric": "gmv", "mean_value": 1000},
                {"dimension": "category", "category": "B", "metric": "gmv", "mean_value": 1200},
            ]
        ).to_csv(workflow_dir / "category_metric_summary.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(
            [
                {"component": "PC1", "axis_label": "规模-效率主轴", "variance_share": 0.42},
                {"component": "PC2", "axis_label": "风险-收益主轴", "variance_share": 0.23},
            ]
        ).to_csv(workflow_dir / "pca_axis_summary.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(
            [
                {"cluster": 1, "member_id": "A", "evidence": "高GMV高订单"},
                {"cluster": 2, "member_id": "B", "evidence": "高风险高波动"},
            ]
        ).to_csv(workflow_dir / "cluster_member_detail.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(
            [
                {"cluster": 1, "gmv_mean": 1100, "orders_mean": 11},
                {"cluster": 2, "gmv_mean": 900, "orders_mean": 9},
            ]
        ).to_csv(workflow_dir / "cluster_profile.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(
            [
                {"metric_pair": "预算/实际", "dimension": "category", "gap": 120, "gap_rate": 0.08},
            ]
        ).to_csv(workflow_dir / "budget_variance_summary.csv", index=False, encoding="utf-8-sig")

        pdf_path = workflow_dir / f"{report_id}-r-interpretation.pdf"
        try:
            from reportlab.pdfgen import canvas
        except Exception:
            self.skipTest("reportlab unavailable")
        canvas_obj = canvas.Canvas(str(pdf_path))
        canvas_obj.drawString(72, 800, "R workflow interpretation")
        canvas_obj.drawString(72, 780, "GMV and orders both increased after grouping.")
        canvas_obj.save()
        return report_dir

    def test_run_r_artifact_intelligence_flow_writes_standalone_outputs(self) -> None:
        report_id = "rinteltest01"
        report_dir = self._prepare_r_workflow_bundle(report_id)

        fake_result = {
            "headline": "已基于 R 统计总表与 PDF 形成独立智能解读。",
            "executive_summary": ["GMV 和 orders 是当前最重要的两个数值主轴。"],
            "artifact_usage": ["使用了 workbook 的 summary_stats 与 results_index，以及 PDF 摘录。"],
            "sheet_findings": [
                {
                    "sheet_name": "summary_stats",
                    "finding": "gmv 与 orders 都有稳定数值画像。",
                    "why_it_matters": "它们适合作为经营主线指标。",
                    "evidence": "gmv mean=1125; orders mean=11.25",
                }
            ],
            "cross_artifact_findings": ["PDF 叙述层和 workbook 数值层基本一致。"],
            "evidence_boundaries": ["当前只验证了 summary_stats 层，不代表所有统计方法都已深挖。"],
            "action_recommendations": ["优先围绕 GMV 与 orders 做进一步分层复盘。"],
            "markdown": "# R 语言及智能解读\n\n- GMV 和 orders 是当前最重要的两个数值主轴。\n",
            "live_available": True,
            "runtime_state": "live",
            "artifact_access_mode": "direct_files",
        }

        with patch(
            "app.services.r_artifact_intelligence_service.codex_interpret_r_artifact_bundle_from_files",
            return_value=fake_result,
        ):
            result = run_r_artifact_intelligence_flow(
                report_id,
                RWorkflowIntelligenceRequest(
                    focus_question="哪些指标最值得优先复盘",
                    target_audience="经营负责人",
                    output_goal="独立智能解读",
                ),
            )

        output_dir = Path(result["output_dir"])
        self.assertTrue(output_dir.exists())
        self.assertEqual(result["status"], "completed")
        names = [item["name"] for item in result["downloadables"]]
        self.assertTrue(any(name.endswith("-r-codex-intelligence.pdf") for name in names))
        self.assertTrue(any(name.endswith("-r-codex-intelligence.json") for name in names))
        self.assertTrue(any(name.endswith("-r-codex-intelligence-prompt.md") for name in names))
        self.assertIn("r-followup-executions.xlsx", names)
        prompt_path = output_dir / f"{report_id}-r-codex-intelligence-prompt.md"
        self.assertTrue(prompt_path.exists())
        prompt_text = prompt_path.read_text(encoding="utf-8")
        self.assertIn("standalone R artifact intelligence agent", prompt_text)
        self.assertIn(f"{report_id}-r-statistics-summary.xlsx", prompt_text)
        self.assertIn("start from business object, management question, and decision impact", prompt_text)
        self.assertIn("artifact_access_mode", prompt_text)

        shutil.rmtree(report_dir, ignore_errors=True)

    def test_run_r_artifact_intelligence_flow_rejects_non_live_result(self) -> None:
        report_id = "rintelfallback01"
        report_dir = self._prepare_r_workflow_bundle(report_id)

        fake_result = {
            "headline": "fallback",
            "executive_summary": ["fallback summary"],
            "artifact_usage": [],
            "sheet_findings": [],
            "cross_artifact_findings": [],
            "evidence_boundaries": [],
            "action_recommendations": [],
            "markdown": "# fallback\n",
            "live_available": False,
            "runtime_state": "fallback",
            "fallback_reason": "timeout",
        }

        with patch(
            "app.services.r_artifact_intelligence_service.codex_interpret_r_artifact_bundle_from_files",
            side_effect=RuntimeError("file_upload_failed"),
        ), patch(
            "app.services.r_artifact_intelligence_service.codex_interpret_r_artifact_bundle_from_summary",
            return_value=fake_result,
        ):
            with self.assertRaises(RuntimeError):
                run_r_artifact_intelligence_flow(
                    report_id,
                    RWorkflowIntelligenceRequest(
                        focus_question="必须 live Codex",
                    ),
                )

        shutil.rmtree(report_dir, ignore_errors=True)

    def test_summary_pack_prioritizes_pca_and_cluster_artifacts_when_direct_files_fail(self) -> None:
        report_id = "rintelsummary01"
        report_dir = self._prepare_r_workflow_bundle(report_id)
        captured_payload: dict[str, object] = {}

        def _fake_summary(summary_payload):
            captured_payload.update(summary_payload)
            return {
                "headline": "summary pack ok",
                "executive_summary": ["读取到 PCA 与聚类证据。"],
                "artifact_usage": ["使用了 summary_pack。"],
                "sheet_findings": [],
                "cross_artifact_findings": [],
                "evidence_boundaries": [],
                "action_recommendations": [],
                "markdown": "# summary\n",
                "live_available": True,
                "runtime_state": "live",
            }

        with patch(
            "app.services.r_artifact_intelligence_service.codex_interpret_r_artifact_bundle_from_files",
            side_effect=RuntimeError("file_upload_failed"),
        ), patch(
            "app.services.r_artifact_intelligence_service.codex_interpret_r_artifact_bundle_from_summary",
            side_effect=_fake_summary,
        ):
            result = run_r_artifact_intelligence_flow(
                report_id,
                RWorkflowIntelligenceRequest(
                    focus_question="请优先看主轴和聚类成员",
                ),
            )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(captured_payload.get("direct_file_failure"), "file_upload_failed")
        artifact_tables = captured_payload.get("selected_artifact_tables") or []
        artifact_names = [str(item.get("artifact_name") or "") for item in artifact_tables]
        self.assertEqual(
            artifact_names[:5],
            [
                "pca_axis_summary",
                "cluster_member_detail",
                "cluster_profile",
                "category_metric_summary",
                "budget_variance_summary",
            ],
        )
        key_artifact_rows = captured_payload.get("key_artifact_rows") or []
        self.assertTrue(any(str(item.get("artifact_name") or "") == "pca_axis_summary" for item in key_artifact_rows))
        self.assertTrue(any(str(item.get("artifact_name") or "") == "cluster_member_detail" for item in key_artifact_rows))

        shutil.rmtree(report_dir, ignore_errors=True)

    def test_run_r_artifact_intelligence_flow_requires_r_workflow_artifacts(self) -> None:
        report_id = "rintelmissing01"
        report_dir = REPORTS_DIR / f"smart-report-{report_id}"
        if report_dir.exists():
            shutil.rmtree(report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)

        with self.assertRaises(FileNotFoundError):
            run_r_artifact_intelligence_flow(report_id, RWorkflowIntelligenceRequest())

        shutil.rmtree(report_dir, ignore_errors=True)

    def test_run_r_artifact_intelligence_flow_rejects_path_traversal_report_id(self) -> None:
        with self.assertRaises(ValueError):
            run_r_artifact_intelligence_flow("../../private-r-workflow", RWorkflowIntelligenceRequest())


if __name__ == "__main__":
    unittest.main()
