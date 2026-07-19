from __future__ import annotations

import unittest

from app.services.report_service import _display_table_value, _pdf_table_value, _table


class TablePercentDisplayTests(unittest.TestCase):
    def test_share_like_columns_render_as_percent(self) -> None:
        self.assertEqual(_display_table_value("触达占比", 0.1234), "12.3%")
        self.assertEqual(_display_table_value("share", 0.456), "45.6%")
        self.assertEqual(_display_table_value("曝光完成率", 1.234), "123.4%")

    def test_non_rate_columns_do_not_render_as_percent(self) -> None:
        self.assertEqual(_display_table_value("p_value", 0.0004), "0.0004")
        self.assertEqual(_display_table_value("count", 1200), "1,200")
        self.assertEqual(_display_table_value("p值", 0.0004), "0.0004")
        self.assertEqual(_display_table_value("数量", 1200), "1,200")

    def test_table_headers_are_localized_to_chinese_when_possible(self) -> None:
        table = _table(
            "英文表头测试",
            [
                {
                    "left": "活跃用户",
                    "right": "注册数",
                    "correlation": 0.91,
                    "p_value": 0.0004,
                    "count": 1200,
                    "share": 0.456,
                    "github_stars": 72400,
                }
            ],
        )
        self.assertEqual(
            table["columns"],
            ["左字段", "右字段", "相关系数", "p值", "数量", "占比", "GitHub星标"],
        )
        row = table["rows"][0]
        self.assertEqual(row["左字段"], "活跃用户")
        self.assertEqual(row["GitHub星标"], 72400)

    def test_pdf_table_value_wraps_and_truncates_long_text(self) -> None:
        text = "这是一个非常长的基金会项目简介字段" * 20
        rendered = _pdf_table_value("项目简介", text)
        self.assertIn("\n", rendered)
        self.assertTrue(rendered.endswith("…"))


class TableDynamicColumnTests(unittest.TestCase):
    def test_table_accepts_columns_that_appear_after_first_row(self) -> None:
        table = _table(
            "dynamic columns",
            [
                {"对象": "A", "GMV": 10},
                {"对象": "B", "GMV": 20, "延迟订单估算": 3},
            ],
        )
        self.assertIn("延迟订单估算", table["columns"])
        self.assertEqual(table["rows"][1]["延迟订单估算"], 3)


if __name__ == "__main__":
    unittest.main()
