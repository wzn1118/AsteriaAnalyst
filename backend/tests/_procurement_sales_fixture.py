from __future__ import annotations

import pandas as pd


def procurement_sales_frame() -> pd.DataFrame:
    """Return a small anonymous order fixture suitable for public CI."""
    products = [
        ("product-alpha", "sku-alpha-small", "category-a", "supplier-one", 120.0, 150.0),
        ("product-beta", "sku-beta-standard", "category-a", "supplier-one", 85.0, 105.0),
        ("product-gamma", "sku-gamma-large", "category-b", "supplier-two", 210.0, 260.0),
    ]
    rows: list[dict[str, object]] = []
    for index in range(18):
        product_id, sku_id, category, supplier, sale_price, original_price = products[index % len(products)]
        ordered_day = (index % 9) + 1
        delivered_day = ordered_day + 2 + (1 if index % 5 == 0 else 0)
        estimated_day = ordered_day + 3
        units_sold = 1 + (index % 4)
        rows.append(
            {
                "order_id": f"order-{index + 1:03d}",
                "customer_id": f"customer-{(index % 11) + 1:03d}",
                "product_id": product_id,
                "sku_id": sku_id,
                "category": category,
                "supplier": supplier,
                "order_purchase_timestamp": f"2026-01-{ordered_day:02d}",
                "delivered_customer_date": f"2026-01-{delivered_day:02d}",
                "estimated_delivery_date": f"2026-01-{estimated_day:02d}",
                "review_score": 2 + (index % 4),
                "review_comment": "anonymous fixture review",
                "sales_amount": sale_price * units_sold,
                "units_sold": units_sold,
                "sale_price": sale_price,
                "original_price": original_price,
            }
        )
    return pd.DataFrame(rows)
