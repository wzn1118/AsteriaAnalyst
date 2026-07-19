from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.services.codex_runtime_pipeline_service import (
    _validate_internet_ops_daily_action_contract,
    _validate_internet_ops_derived_matrix_gate,
    _validate_internet_ops_media_buying_control_gate,
)
from app.services.internet_operations_analysis_modules import (
    build_internet_operations_analysis_modules,
)
from app.services.internet_ops_action_roadmap_renderer import (
    build_internet_ops_action_roadmap,
)
from app.services.internet_ops_decision_registry_service import (
    build_internet_ops_object_decision_registry,
)
from app.services.internet_ops_profile_service import internet_ops_field_availability_registry
from app.services.report_service import _write_internet_ops_cli_evidence_pack


PLACEHOLDER_ACTION = "\u8865\u5b57\u6bb5\u9a8c\u8bc1"
ACTION_KPIS = "roi / cac / CTR / retention_d7 / nps / paid_users / contribution_margin"


def _internet_ops_frame(row_count: int = 720) -> pd.DataFrame:
    channels = ["Douyin", "Xiaohongshu", "Baidu", "AppStore"]
    traffic_sources = ["feed", "search", "kol", "store"]
    city_tiers = ["T1", "T2", "T3"]
    user_segments = ["new", "active", "paid"]
    content_categories = ["short_video", "live", "article"]
    product_modules = ["growth", "membership", "commerce"]
    campaigns = ["spring", "summer", "retention"]
    rows: list[dict[str, object]] = []
    for index in range(row_count):
        paid_users = 18 + (index % 17)
        revenue = 900 + (index % 31) * 21
        cost = 260 + (index % 19) * 12
        margin = revenue - cost
        roi = revenue / cost
        rows.append(
            {
                "date": f"2026-04-{(index % 28) + 1:02d}",
                "channel": channels[index % len(channels)],
                "traffic_source": traffic_sources[index % len(traffic_sources)],
                "city_tier": city_tiers[index % len(city_tiers)],
                "user_segment": user_segments[index % len(user_segments)],
                "content_category": content_categories[index % len(content_categories)],
                "product_module": product_modules[index % len(product_modules)],
                "campaign": campaigns[index % len(campaigns)],
                "impressions": 20000 + index * 17,
                "clicks": 1100 + index * 3,
                "registrations": 360 + (index % 23),
                "activations": 210 + (index % 19),
                "paid_users": paid_users,
                "revenue": revenue,
                "operating_cost": cost,
                "contribution_margin": margin,
                "roi": round(roi, 4),
                "ROI": round(roi, 4),
                "cac": round(cost / paid_users, 4),
                "retention_d7": round(0.18 + (index % 9) * 0.015, 4),
                "nps": 22 + (index % 25),
                "CTR": round((1100 + index * 3) / (20000 + index * 17), 6),
                "CPM": round(cost / max(1, (20000 + index * 17) / 1000), 4),
                "CPC": round(cost / max(1, 1100 + index * 3), 4),
            }
        )
    # Force a few deterministic stoploss examples for Day 1.
    for index in range(0, min(8, len(rows))):
        rows[index]["contribution_margin"] = -150 - index
        rows[index]["roi"] = 0.55
        rows[index]["ROI"] = 0.55
        rows[index]["cac"] = 120 + index
        rows[index]["retention_d7"] = 0.05
        rows[index]["nps"] = 8
    return pd.DataFrame(rows)


class InternetOpsDailyActionContractTests(unittest.TestCase):
    def test_modern_ops_fields_do_not_fall_back_to_placeholder_actions(self) -> None:
        frame = _internet_ops_frame()
        field_registry = internet_ops_field_availability_registry(frame)
        modules = build_internet_operations_analysis_modules(frame, field_registry)
        registry = build_internet_ops_object_decision_registry(modules, field_registry)
        roadmap = build_internet_ops_action_roadmap(registry, field_registry)

        critical_object_ids = {
            "north_star_metric",
            "growth_funnel",
            "channel_portfolio",
            "user_segment_portfolio",
            "risk_anomaly",
        }
        rows = {row["object_id"]: row for row in registry["rows"]}
        for object_id in critical_object_ids:
            self.assertIn(object_id, rows)
            row_text = json.dumps(rows[object_id], ensure_ascii=False)
            self.assertNotIn(PLACEHOLDER_ACTION, row_text)
            self.assertNotIn("user_count / event_count", row_text)
            self.assertIn(ACTION_KPIS, row_text)

        channel_action = str(rows["channel_portfolio"]["final_action"])
        for action_word in ["\u52a0\u7801", "\u964d\u6743", "\u6b62\u635f", "\u89c2\u5bdf"]:
            self.assertIn(action_word, channel_action)
        self.assertIn("\u6b62\u635f", str(rows["risk_anomaly"]["final_action"]))
        self.assertTrue(roadmap["seven_day_action_table"])
        self.assertNotIn(PLACEHOLDER_ACTION, json.dumps(roadmap, ensure_ascii=False))

    def test_daily_action_pack_contains_day_1_through_day_7_contract(self) -> None:
        frame = _internet_ops_frame()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            evidence = _write_internet_ops_cli_evidence_pack(
                workspace_dir=workspace,
                frame=frame,
            )
            self.assertIn("ops_daily_action_plan_path", evidence)
            _validate_internet_ops_daily_action_contract(workspace)

            payload = json.loads((workspace / "ops_daily_action_plan.json").read_text(encoding="utf-8"))
            labels = [slot["day_label"] for slot in payload["day_slots"]]
            self.assertEqual(labels, [f"Day {index}" for index in range(1, 8)])
            flattened = [
                action
                for slot in payload["day_slots"]
                for action in slot.get("actions", [])
            ]
            self.assertTrue(flattened)
            for action in flattened:
                for key in [
                    "object_name",
                    "owner_role",
                    "this_day_action",
                    "success_metric",
                    "next_checkpoint",
                ]:
                    self.assertTrue(str(action.get(key) or "").strip())
                action_text = json.dumps(action, ensure_ascii=False)
                self.assertNotIn(PLACEHOLDER_ACTION, action_text)
                self.assertNotIn("user_count / event_count", action_text)
            self.assertTrue((workspace / "ops_daily_action_owner_matrix.csv").exists())

    def test_full_field_and_derived_visual_contract_contains_all_fields_and_12_charts(self) -> None:
        frame = _internet_ops_frame()
        required_fields = [
            "date",
            "channel",
            "traffic_source",
            "city_tier",
            "user_segment",
            "content_category",
            "product_module",
            "campaign",
            "impressions",
            "clicks",
            "registrations",
            "activations",
            "paid_users",
            "revenue",
            "operating_cost",
            "contribution_margin",
            "roi",
            "cac",
            "retention_d7",
            "nps",
            "CTR",
            "CPM",
            "CPC",
            "ROI",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            _write_internet_ops_cli_evidence_pack(workspace_dir=workspace, frame=frame)

            matrix = pd.read_csv(workspace / "ops_full_field_metric_matrix.csv", encoding="utf-8-sig")
            self.assertEqual(set(required_fields), set(matrix["字段名"].astype(str)))
            catalog = pd.read_csv(workspace / "ops_derived_metric_catalog.csv", encoding="utf-8-sig")
            self.assertGreaterEqual(catalog.shape[0], 18)
            for column in ["指标名称", "公式", "来源字段", "经营用途"]:
                self.assertIn(column, catalog.columns)
            self.assertIn("日动作关系（Day）", catalog.columns)

            asset_dir = workspace / "source_visual_assets"
            self.assertGreaterEqual(len(list(asset_dir.glob("ops_*.png"))), 12)
            self.assertGreaterEqual(len(list(asset_dir.glob("ops_*.csv"))), 12)
            manifest = json.loads((workspace / "ops_derived_visual_manifest.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(manifest.get("charts", [])), 12)

            chart_refs = "\n".join(str(item["png_path"]) for item in manifest["charts"])
            combined = (
                "派生指标矩阵 真实投放回报 × 获客成本 点击到注册 激活到付费 毛利率 "
                "全字段覆盖与派生口径总表 派生指标目录 派生指标图组 "
                "全字段覆盖矩阵 增长漏斗派生率图（AARRR） 真实投放回报 × 获客成本四象限图（roi / cac）\n"
                + " ".join(required_fields)
                + "\n"
                + chart_refs
            )
            _validate_internet_ops_derived_matrix_gate(combined, workspace=workspace)

    def test_media_buying_control_gate_rejects_sku_placeholder_hack(self) -> None:
        with self.assertRaisesRegex(ValueError, "SKU compatibility"):
            _validate_internet_ops_media_buying_control_gate(
                "This internet-ops workbook does not use SKU. SKU compatibility marker."
            )

    def test_media_buying_control_gate_requires_paid_media_knowledge(self) -> None:
        weak_report = (
            "Day 1 先止损，Day 2 重排预算。"
            "报告只有渠道排行和本周动作，没有投放经营控制。"
        )
        with self.assertRaisesRegex(ValueError, "paid-media control"):
            _validate_internet_ops_media_buying_control_gate(weak_report)

        strong_report = (
            "投放运营控制台：预算节奏和预算消耗决定 Day 1 止损；"
            "边际 roi 与边际 CAC 决定 Day 2 加码或降权；"
            "归因窗口要和 campaign 周期对齐；"
            "增量实验、holdout 和对照组验证 paid_media 是否真实增量；"
            "素材疲劳、频控、学习期、出价策略、人群重叠、LTV 和回本周期进入 owner 复盘。"
        )
        _validate_internet_ops_media_buying_control_gate(strong_report)

    def test_derived_matrix_gate_requires_matrix_and_quadrant_language(self) -> None:
        with self.assertRaisesRegex(ValueError, "derived metric matrix"):
            _validate_internet_ops_derived_matrix_gate("只有普通渠道排行，没有矩阵和象限。")

        _validate_internet_ops_derived_matrix_gate(
            "派生指标矩阵展示 点击率（CTR）、点击到注册、激活到付费、毛利率、真实投放回报（roi）、获客成本（cac）；"
            "真实投放回报 × 获客成本四象限图（roi / cac）把对象分成加码、提效、验证和止损。"
        )


if __name__ == "__main__":
    unittest.main()
