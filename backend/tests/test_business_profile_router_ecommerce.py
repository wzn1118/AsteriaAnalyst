from __future__ import annotations

import unittest

import pandas as pd

from app.services.business_profile_router import route_business_profile


class BusinessProfileRouterEcommerceTests(unittest.TestCase):
    def test_taobao_product_aggregate_routes_to_ecommerce(self) -> None:
        frame = pd.DataFrame(
            columns=["item_id", "shop_id", "category", "price", "sales_volume", "GMV", "review_count", "rating", "refund_rate"]
        )
        result = route_business_profile(frame, dataset_name="淘宝商品聚合数据")
        self.assertEqual(result["business_profile"], "ecommerce_product_operations_report")
        self.assertEqual(result["profile_entrypoint"], "ecommerce_product_operations_report_profile")
        self.assertEqual(result["report_lens"], "procurement_sales_review")
        self.assertIn("商品", result["decisive_object_grain"])
        self.assertIn("matched_media_signals", result)
        self.assertEqual(result["secondary_profile"], "internet_operations_report")

    def test_jd_procurement_routes_to_procurement_or_ecommerce(self) -> None:
        frame = pd.DataFrame(
            columns=["sku_id", "brand", "supplier", "order_count", "inventory", "gross_margin", "fulfillment_rate", "review_score"]
        )
        result = route_business_profile(frame, dataset_name="京东采销数据")
        self.assertIn(result["business_profile"], {"procurement_sales_report", "ecommerce_product_operations_report"})
        self.assertIn("SKU/SPU", result["decisive_object_grain"])

    def test_content_community_routes_to_internet_ops(self) -> None:
        frame = pd.DataFrame(
            columns=["content_id", "author_id", "view", "like", "comment", "share", "retention", "user_id"]
        )
        result = route_business_profile(frame, dataset_name="内容社区数据")
        self.assertEqual(result["business_profile"], "internet_operations_report")
        self.assertEqual(result["profile_entrypoint"], "internet_operations_report_profile")

    def test_media_campaign_routes_to_media(self) -> None:
        frame = pd.DataFrame(
            columns=["campaign", "media", "impression", "click", "CTR", "CPC", "spend", "conversion"]
        )
        result = route_business_profile(frame, dataset_name="广告投放数据")
        self.assertEqual(result["business_profile"], "media_campaign_report")
        self.assertIn("campaign_structure", result["matched_media_signals"]["matched_groups"])

    def test_mixed_ecommerce_traffic_routes_to_ecommerce_with_secondary_ops(self) -> None:
        frame = pd.DataFrame(
            columns=["item_id", "sku_id", "PV", "UV", "click", "add_to_cart", "pay", "GMV", "review_count", "shop_id"]
        )
        result = route_business_profile(frame, dataset_name="混合电商流量数据")
        self.assertEqual(result["business_profile"], "ecommerce_product_operations_report")
        self.assertEqual(result["secondary_profile"], "internet_operations_report")
        self.assertIn("SKU/SPU", result["decisive_object_grain"])
        self.assertTrue(result["ambiguity_warning"])

    def test_product_review_fields_do_not_route_to_internet_ops(self) -> None:
        frame = pd.DataFrame(
            columns=["item_id", "sku_id", "shop_id", "comment", "review_count", "rating", "GMV"]
        )
        result = route_business_profile(frame, dataset_name="电商评论口碑数据")
        self.assertEqual(result["business_profile"], "ecommerce_product_operations_report")
        self.assertNotEqual(result["business_profile"], "internet_operations_report")


if __name__ == "__main__":
    unittest.main()
