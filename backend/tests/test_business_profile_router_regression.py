from __future__ import annotations

import unittest

import pandas as pd

from app.services.business_profile_router import route_business_profile


class BusinessProfileRouterRegressionTests(unittest.TestCase):
    def test_procurement_sales_dataset_routes_correctly(self) -> None:
        frame = pd.DataFrame(
            columns=[
                "SKU",
                "商品",
                "类目",
                "supplier",
                "order_count",
                "fulfillment_days",
                "review_score",
                "inventory_days",
                "gross_margin",
            ]
        )
        result = route_business_profile(frame, dataset_name="procurement_sales")
        self.assertEqual(result["business_profile"], "procurement_sales_report")
        self.assertEqual(result["profile_entrypoint"], "procurement_sales_report_profile")
        self.assertEqual(result["report_lens"], "procurement_sales_review")
        self.assertGreaterEqual(result["confidence"], 0.65)

    def test_internet_operations_dataset_routes_correctly(self) -> None:
        frame = pd.DataFrame(
            columns=[
                "user_id",
                "DAU",
                "PV",
                "UV",
                "channel",
                "content_id",
                "click",
                "register",
                "retention",
                "conversion",
                "revenue",
            ]
        )
        result = route_business_profile(frame, dataset_name="internet_operations")
        self.assertEqual(result["business_profile"], "internet_operations_report")
        self.assertEqual(result["profile_entrypoint"], "internet_operations_report_profile")
        self.assertEqual(result["report_lens"], "internet_ops_review")
        self.assertGreaterEqual(result["confidence"], 0.65)

    def test_media_campaign_dataset_routes_correctly(self) -> None:
        frame = pd.DataFrame(
            columns=[
                "media",
                "impression",
                "click",
                "CTR",
                "CPM",
                "CPC",
                "spend",
                "conversion",
                "campaign",
            ]
        )
        result = route_business_profile(frame, dataset_name="media_campaign")
        self.assertEqual(result["business_profile"], "media_campaign_report")
        self.assertEqual(result["profile_entrypoint"], "media_campaign_report_profile")
        self.assertEqual(result["report_lens"], "media_review")
        self.assertGreaterEqual(result["confidence"], 0.65)


if __name__ == "__main__":
    unittest.main()
