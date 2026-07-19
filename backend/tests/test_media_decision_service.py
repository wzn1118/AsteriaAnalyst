from __future__ import annotations

import unittest

import pandas as pd

from app.services.media_decision_service import (
    analyze_data_scope,
    build_bias_review,
    build_media_decision_context,
    compute_weighted_metrics,
    parse_placement_field,
)


DATE = "event_date"
MEDIA = "media_name"
DEVICE = "device_name"
PLACEMENT = "placement_name"
EST_REACH = "estimated_impressions"
ACT_REACH = "actual_impressions"
EST_CLICK = "estimated_clicks"
ACT_CLICK = "actual_clicks"
SPEND = "spend_cost"


def _program_bundle() -> dict:
    return {
        "semantic_mapping": {
            "role_summary": {
                "time": [{"column": DATE, "confidence": "high"}],
                "media": [{"column": MEDIA, "confidence": "high"}],
                "device": [{"column": DEVICE, "confidence": "high"}],
                "placement": [{"column": PLACEMENT, "confidence": "high"}],
                "reach": [{"column": ACT_REACH, "confidence": "high"}, {"column": EST_REACH, "confidence": "high"}],
                "interaction": [{"column": ACT_CLICK, "confidence": "high"}, {"column": EST_CLICK, "confidence": "high"}],
                "spend": [{"column": SPEND, "confidence": "high"}],
            }
        }
    }


class MediaDecisionServiceTests(unittest.TestCase):
    def test_filename_range_conflict_detected(self) -> None:
        frame = pd.DataFrame(
            {
                DATE: ["2025-03-01", "2025-03-02", "2025-07-13"],
                MEDIA: ["A", "A", "A"],
                DEVICE: ["PHONE", "PHONE", "PHONE"],
                PLACEMENT: ["open-PDB-youku", "open-PDB-youku", "open-PDB-youku"],
                EST_REACH: [100, 120, 150],
                ACT_REACH: [110, 118, 148],
                EST_CLICK: [10, 12, 15],
                ACT_CLICK: [11, 13, 16],
                SPEND: [1000, 1000, 1000],
            }
        )
        scope = analyze_data_scope(frame, "xx-0711-0713.xlsx", _program_bundle())
        self.assertTrue(scope["filename_conflict"])
        self.assertEqual(scope["time_grain"], "daily")

    def test_weighted_ctr_differs_from_row_average(self) -> None:
        frame = pd.DataFrame(
            {
                DATE: ["2025-07-11", "2025-07-11"],
                MEDIA: ["A", "B"],
                DEVICE: ["PHONE", "PHONE"],
                PLACEMENT: ["open-PDB-youku", "feed-PMP-youku"],
                EST_REACH: [1000, 10],
                ACT_REACH: [1000, 10],
                EST_CLICK: [10, 5],
                ACT_CLICK: [10, 5],
                SPEND: [1000, 100],
            }
        )
        metrics = compute_weighted_metrics(frame, _program_bundle())
        self.assertAlmostEqual(metrics["overall"]["weighted_ctr"], 15 / 1010, places=6)
        self.assertAlmostEqual(metrics["distributions"]["ctr"]["row_mean"], (0.01 + 0.5) / 2, places=6)
        self.assertNotAlmostEqual(metrics["overall"]["weighted_ctr"], metrics["distributions"]["ctr"]["row_mean"], places=3)

    def test_click_delivery_high_risk_detected(self) -> None:
        frame = pd.DataFrame(
            {
                DATE: ["2025-07-11", "2025-07-12"],
                MEDIA: ["A", "A"],
                DEVICE: ["PHONE", "PHONE"],
                PLACEMENT: ["open-PDB-youku", "open-PDB-youku"],
                EST_REACH: [1000, 1000],
                ACT_REACH: [1100, 1100],
                EST_CLICK: [10, 10],
                ACT_CLICK: [60, 60],
                SPEND: [1000, 1000],
            }
        )
        metrics = compute_weighted_metrics(frame, _program_bundle())
        self.assertTrue(metrics["click_risk"])
        self.assertGreater(metrics["overall"]["weighted_click_delivery"], 1.8)

    def test_small_sample_high_ctr_not_scaled(self) -> None:
        rows = []
        for day in ["2025-07-11", "2025-07-12", "2025-07-13"]:
            rows.append({DATE: day, MEDIA: "A", DEVICE: "PHONE", PLACEMENT: "hero-open-PDB-youku", EST_REACH: 1000, ACT_REACH: 1000, EST_CLICK: 40, ACT_CLICK: 40, SPEND: 1000})
            rows.append({DATE: day, MEDIA: "B", DEVICE: "PHONE", PLACEMENT: "small-flash-PDB-bili", EST_REACH: 20, ACT_REACH: 20, EST_CLICK: 10, ACT_CLICK: 10, SPEND: 100})
        frame = pd.DataFrame(rows)
        context = build_media_decision_context(frame, _program_bundle(), "0711-0713.xlsx")
        actions = {row["对象"]: row["动作"] for row in context["actions"]}
        target = next(key for key in actions if "small-flash-PDB-bili" in key)
        self.assertNotEqual(actions[target], "优先放量验证")

    def test_latest_window_incomplete_degrades(self) -> None:
        rows = []
        for day in ["2025-07-01", "2025-07-02", "2025-07-03", "2025-07-04"]:
            for _ in range(5):
                rows.append({DATE: day, MEDIA: "A", DEVICE: "PHONE", PLACEMENT: "open-PDB-youku", EST_REACH: 100, ACT_REACH: 100, EST_CLICK: 10, ACT_CLICK: 10, SPEND: 100})
        rows.append({DATE: "2025-07-05", MEDIA: "A", DEVICE: "PHONE", PLACEMENT: "open-PDB-youku", EST_REACH: 20, ACT_REACH: 20, EST_CLICK: 2, ACT_CLICK: 2, SPEND: 20})
        frame = pd.DataFrame(rows)
        context = build_media_decision_context(frame, _program_bundle(), "0701-0705.xlsx")
        self.assertTrue(context["window_change"]["latest_window_incomplete"])
        self.assertTrue(any("最新窗口疑似不完整" in item for item in context["high_risk_warnings"]))

    def test_placement_parse_high_and_low_confidence(self) -> None:
        rich_frame = pd.DataFrame({PLACEMENT: ["铂萃-全屏闪屏-图片【程序化PD池】-Bilibili", "珍护-前贴片-PDB-优酷"]})
        rich = parse_placement_field(rich_frame.assign(**{DATE: "2025-07-11"}), _program_bundle())
        self.assertIn(rich["confidence"], {"medium", "high"})
        poor_frame = pd.DataFrame({PLACEMENT: ["A", "B"]})
        poor = parse_placement_field(poor_frame.assign(**{DATE: "2025-07-11"}), _program_bundle())
        self.assertEqual(poor["confidence"], "low")

    def test_bias_review_sorted_by_contribution(self) -> None:
        frame = pd.DataFrame(
            {
                DATE: ["2025-07-11", "2025-07-11"],
                MEDIA: ["A", "B"],
                DEVICE: ["PHONE", "PHONE"],
                PLACEMENT: ["hero-open-PDB-youku", "small-flash-PDB-bili"],
                EST_REACH: [10000, 10],
                ACT_REACH: [9000, 0],
                EST_CLICK: [100, 2],
                ACT_CLICK: [90, 0],
                SPEND: [1000, 10],
            }
        )
        review = build_bias_review(frame, _program_bundle())
        self.assertEqual(review["rows"][0]["对象"], "A / PHONE / hero-open-PDB-youku")

    def test_cpm_mode_uses_delivery_for_actions(self) -> None:
        rows = []
        for day in ["2025-07-11", "2025-07-12", "2025-07-13"]:
            rows.append({DATE: day, MEDIA: "A", DEVICE: "PHONE", PLACEMENT: "brand-headline-PDB-youku", EST_REACH: 1000, ACT_REACH: 1020, EST_CLICK: 50, ACT_CLICK: 10, SPEND: 1000})
            rows.append({DATE: day, MEDIA: "B", DEVICE: "PHONE", PLACEMENT: "full-flash-PDB-bilibili", EST_REACH: 120, ACT_REACH: 120, EST_CLICK: 2, ACT_CLICK: 2, SPEND: 100})
        frame = pd.DataFrame(rows)
        context = build_media_decision_context(frame, _program_bundle(), "0711-0713.xlsx")
        self.assertEqual(context["measurement_mode"]["mode"], "cpm_delivery")
        actions = {row["对象"]: row["动作"] for row in context["actions"]}
        target = next(key for key in actions if "brand-headline-PDB-youku" in key)
        self.assertEqual(actions[target], "优先放量验证")

    def test_marketing_dimension_reviews_exist(self) -> None:
        rows = []
        for day in ["2025-07-11", "2025-07-12"]:
            rows.append({DATE: day, MEDIA: "A", DEVICE: "PHONE", PLACEMENT: "铂萃-全屏闪屏-图片【程序化PD池】-Bilibili", EST_REACH: 1000, ACT_REACH: 1020, EST_CLICK: 20, ACT_CLICK: 10, SPEND: 1000})
            rows.append({DATE: day, MEDIA: "B", DEVICE: "PHONE", PLACEMENT: "珍护-前贴片-PDB-优酷", EST_REACH: 800, ACT_REACH: 780, EST_CLICK: 10, ACT_CLICK: 5, SPEND: 900})
        frame = pd.DataFrame(rows)
        context = build_media_decision_context(frame, _program_bundle(), "0711-0712.xlsx")
        reviews = context["parsed_dimension_reviews"]
        self.assertGreater(len(reviews["product_line"]), 0)
        self.assertGreater(len(reviews["ad_format"]), 0)
        self.assertGreater(len(reviews["trading_mode"]), 0)


if __name__ == "__main__":
    unittest.main()
