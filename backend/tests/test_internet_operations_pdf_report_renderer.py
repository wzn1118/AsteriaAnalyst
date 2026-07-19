from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.services.internet_operations_analysis_modules import build_internet_operations_analysis_modules
from app.services.internet_ops_decision_registry_service import (
    build_internet_ops_object_decision_registry,
    render_internet_ops_action_table,
)
from app.services.internet_operations_pdf_report_renderer import build_internet_operations_management_variant
from app.services.internet_ops_profile_service import internet_ops_field_availability_registry
from app.services.report_service import _write_pdf_report_cn


class InternetOperationsPdfRendererTests(unittest.TestCase):
    def _synthetic_frame(self) -> pd.DataFrame:
        rows = []
        channels = ["organic", "paid", "social", "search"]
        campaigns = ["春促", "夏促", "会员日"]
        contents = ["c1", "c2", "c3", "c4", "c5"]
        for i in range(600):
            rows.append(
                {
                    "user_id": i + 1,
                    "DAU": 80 + (i % 25),
                    "new_user": 10 + (i % 9),
                    "retention": 0.22 + ((i % 7) * 0.01),
                    "channel": channels[i % len(channels)],
                    "campaign_name": campaigns[i % len(campaigns)],
                    "content_id": contents[i % len(contents)],
                    "like": 5 + (i % 6),
                    "comment": 2 + (i % 4),
                    "share": 1 + (i % 3),
                    "conversion": 0.04 + ((i % 5) * 0.01),
                    "cost": 20 + (i % 11),
                    "gmv": 120 + (i % 35),
                    "bounce_rate": 0.15 + ((i % 4) * 0.01),
                }
            )
        return pd.DataFrame(rows)

    def test_renderer_builds_35_page_sections(self) -> None:
        frame = self._synthetic_frame()
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        action_table = render_internet_ops_action_table(registry)
        report = {
            "report_id": "internetopsrenderer01",
            "title": "placeholder",
            "dataset_name": "synthetic internet ops dataset",
            "sheet_name": "Sheet1",
            "generated_at": "2026-04-25T00:00:00Z",
            "business_profile": "internet_operations_report",
            "report_lens": "internet_ops_review",
            "internet_ops_field_availability_registry": field_registry,
            "internet_operations_analysis_modules": modules,
            "internet_ops_object_decision_registry": registry,
            "internet_ops_action_table": action_table,
            "sections": [],
            "executive_summary": [],
        }
        variant = build_internet_operations_management_variant(report)
        self.assertIsNotNone(variant)
        self.assertEqual(len(variant["sections"]), 35)
        self.assertNotIn("采销", variant["title"])

    def test_renderer_outputs_pdf_between_35_and_50_pages(self) -> None:
        try:
            from pypdf import PdfReader
        except Exception:
            self.skipTest("pypdf unavailable")

        frame = self._synthetic_frame()
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        action_table = render_internet_ops_action_table(registry)
        report = {
            "report_id": "internetopsrenderer02",
            "title": "placeholder",
            "dataset_name": "synthetic internet ops dataset",
            "sheet_name": "Sheet1",
            "generated_at": "2026-04-25T00:00:00Z",
            "business_profile": "internet_operations_report",
            "report_lens": "internet_ops_review",
            "internet_ops_field_availability_registry": field_registry,
            "internet_operations_analysis_modules": modules,
            "internet_ops_object_decision_registry": registry,
            "internet_ops_action_table": action_table,
            "sections": [],
            "executive_summary": [],
        }
        variant = build_internet_operations_management_variant(report)
        self.assertIsNotNone(variant)
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = _write_pdf_report_cn(Path(tmp), "management_report", variant)
            self.assertIsNotNone(pdf_path)
            self.assertTrue(Path(pdf_path).exists())
            pages = len(PdfReader(str(pdf_path)).pages)
            self.assertGreaterEqual(pages, 35)
            self.assertLessEqual(pages, 50)


if __name__ == "__main__":
    unittest.main()
