from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.services.business_analysis_package_service import build_business_analysis_package
from app.services.codex_historical_chart_asset_service import render_historical_chart_asset_pack
from app.services.codex_historical_collage_asset_service import (
    build_historical_collage_source,
    render_historical_collage_asset_pack,
)
from app.services.codex_historical_deck_layout_service import render_historical_deck_layout_pack
from app.services.codex_historical_html_asset_injection_service import ensure_historical_deck_assets_embedded
from app.services.codex_historical_logic_reference_service import build_historical_logic_reference_payload
from app.services.codex_historical_report_logic_service import build_historical_report_logic_blueprint
from app.services.codex_historical_table_asset_service import render_historical_table_asset_pack
from app.services.codex_historical_localization_service import localize_historical_text, looks_like_mojibake
from app.services.codex_historical_visual_reference_service import (
    _chart_grammar_contract_from_primitives,
    _dominant_chart_grammar,
    _layout_harmony_features,
)
from app.services.codex_runtime_output_guard_service import validate_reader_facing_artifact
from app.services.codex_runtime_pipeline_service import (
    create_pipeline_job,
    _default_stage_order,
    _validate_historical_page_plan,
    run_pipeline,
)
from app.services.codex_runtime_pipeline_store import pipeline_dir


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_historical_localization_outputs_clean_chinese_labels() -> None:
    labels = {
        "Strategy consulting deck": "咨询式经营报告",
        "gross_sales": "销售额",
        "historical_support_tables": "历史支持表",
        "Priority Action Table": "优先行动表",
    }

    for raw, expected in labels.items():
        localized = localize_historical_text(raw)
        assert localized == expected
        assert not looks_like_mojibake(localized)


def test_reader_facing_output_guard_blocks_garbage_and_placeholders(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text(
        "# 经营报告\n\n"
        "这里展示 placeholder，Sources：historical_data_asset_manifest.json，"
        "并包含乱码 鍘嗗彶鎶ュ憡 与待补内容。",
        encoding="utf-8",
    )

    result = validate_reader_facing_artifact(
        bad,
        label="bad.md",
        artifact_type="markdown",
        min_visible_chars=20,
        min_cjk_ratio=0.18,
    )

    assert not result["ok"]
    assert "reader_facing_mojibake_detected" in result["issues"]
    assert "reader_facing_placeholder_or_filler_detected" in result["issues"]
    assert "reader_facing_internal_path_or_artifact_name_detected" in result["issues"]


def test_business_analysis_package_writes_shared_contract_files(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "channel": ["平台", "直营", "平台", "批发", "直营", "社交电商"],
            "category": ["A", "A", "B", "B", "C", "C"],
            "region": ["东区", "东区", "南区", "南区", "北区", "西区"],
            "revenue": [420, 310, 180, 145, 95, 88],
            "gross_margin": [0.29, 0.38, 0.24, 0.31, 0.33, 0.27],
            "repeat_purchase_rate": [0.44, 0.56, 0.37, 0.49, 0.46, 0.41],
            "inventory_turns": [4.2, 5.8, 3.9, 4.5, 4.7, 4.1],
            "service_level": [0.91, 0.95, 0.87, 0.89, 0.9, 0.88],
        }
    )
    package = build_business_analysis_package(
        workspace=tmp_path,
        data_frame=frame,
        column_summaries=[{"name": "channel", "dtype": "category"}],
    )

    assert (tmp_path / "historical_data_profile.json").is_file()
    assert (tmp_path / "historical_metric_inventory.json").is_file()
    assert (tmp_path / "historical_derived_metric_inventory.json").is_file()
    assert (tmp_path / "historical_dimension_metric_cube.json").is_file()
    assert (tmp_path / "historical_cross_dimension_priority_tables.json").is_file()
    assert (tmp_path / "historical_segment_scorecards.json").is_file()
    assert (tmp_path / "historical_action_candidates.json").is_file()
    manifest = package["manifest"]
    assert manifest["metric_count"] >= 4
    assert manifest["dimension_count"] >= 3
    assert "localized_label_map" in manifest
    assert "asset_ready_views" in manifest
    assert "derived_metric_inventory" in manifest["asset_ready_views"]
    assert "cross_dimension_priority_tables" in manifest["asset_ready_views"]


def test_business_analysis_package_promotes_context_derived_metrics(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "channel": ["SEO", "Paid", "SEO", "Direct", "Paid", "Direct"],
            "revenue": [1200, 900, 1600, 800, 700, 1100],
            "orders": [40, 20, 50, 18, 16, 28],
            "users": [300, 180, 360, 150, 130, 210],
        }
    )
    context_path = tmp_path / "current_report_context.json"
    _write_json(
        context_path,
        {
            "analysis_package_context": {
                "derived_metrics": [
                    {
                        "metric_id": "aov_derived",
                        "metric_name": "客单价",
                        "metric_type": "amount",
                        "formula": "revenue / orders",
                        "source_columns": ["revenue", "orders"],
                        "business_meaning": "衡量每笔订单的收入质量。",
                        "status": "executed",
                        "mean": 32.4,
                        "non_null": 6,
                    }
                ]
            }
        },
    )

    package = build_business_analysis_package(
        workspace=tmp_path,
        data_frame=frame,
        current_report_context_path=context_path,
    )
    support_tables = package["support_tables"]

    assert package["manifest"]["derived_metric_count"] >= 1
    assert (tmp_path / "historical_derived_metric_inventory.json").is_file()
    assert any(item["raw_key"] == "aov_derived" for item in package["derived_metric_inventory"]["metrics"])
    assert any(row["metric_raw_key"] == "aov_derived" for row in support_tables["derived_metric_rows"])
    assert any(row["metric_raw_key"] == "aov_derived" for row in support_tables["kpi_snapshot"])


def test_historical_pipeline_data_context_pack_writes_derived_metric_usage_contract(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "channel": ["SEO", "Paid", "SEO", "Direct", "Paid", "Direct"],
            "revenue": [1200, 900, 1600, 800, 700, 1100],
            "orders": [40, 20, 50, 18, 16, 28],
            "users": [300, 180, 360, 150, 130, 210],
        }
    )
    frame.to_csv(tmp_path / "historical_data_snapshot.csv", index=False, encoding="utf-8-sig")
    _write_json(
        tmp_path / "current_report_context.json",
        {
            "dataset_name": "derived metric pipeline smoke",
            "analysis_package_context": {
                "derived_metrics": [
                    {
                        "metric_id": "aov_derived",
                        "metric_name": "客单价",
                        "metric_type": "amount",
                        "formula": "revenue / orders",
                        "source_columns": ["revenue", "orders"],
                        "business_meaning": "衡量每笔订单收入质量",
                        "status": "executed",
                        "mean": 32.4,
                        "non_null": 6,
                    }
                ]
            },
        },
    )
    manifest = create_pipeline_job(
        pipeline_type="historical_style_report_cli_pipeline",
        workspace_path=str(tmp_path),
        stage_order=[
            {
                "stage_id": "data_context_pack",
                "title": "Data Context Pack",
                "kind": "backend",
                "retryable": True,
                "expected_artifacts": [
                    "historical_data_asset_manifest.json",
                    "historical_derived_metric_inventory.json",
                    "derived_metric_usage_contract.json",
                ],
            }
        ],
        context_payload={
            "historical_data_snapshot_path": "historical_data_snapshot.csv",
            "current_report_context_path": "current_report_context.json",
        },
    )
    try:
        result = run_pipeline(manifest["pipeline_job_id"])
        contract_path = tmp_path / "derived_metric_usage_contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        assert result["stage_outputs"]["data_context_pack"]["status"] == "completed"
        assert contract_path.is_file()
        assert contract["derived_metric_count"] >= 1
        assert any(item["metric_id"] == "aov_derived" for item in contract["metrics"])
        assert result["context_payload"]["derived_metric_usage_contract_path"] == "derived_metric_usage_contract.json"
        assert any(item["name"] == "derived_metric_usage_contract.json" for item in result["artifact_index"])
    finally:
        import shutil

        shutil.rmtree(pipeline_dir(manifest["pipeline_job_id"]), ignore_errors=True)


def test_table_asset_pack_renders_derived_metric_matrix(tmp_path: Path) -> None:
    support_tables_path = tmp_path / "historical_support_tables.json"
    _write_json(
        support_tables_path,
        {
            "kpi_snapshot": [{"metric": "收入", "metric_raw_key": "revenue", "value": 1000}],
            "derived_metric_rows": [
                {
                    "metric": "客单价",
                    "metric_raw_key": "aov_derived",
                    "formula": "revenue / orders",
                    "business_meaning": "衡量订单质量",
                }
            ],
        },
    )

    pack = render_historical_table_asset_pack(workspace=tmp_path, support_tables_path=support_tables_path)
    table_ids = {asset.get("table_id") for asset in pack["assets"]}

    assert "derived_metric_matrix" in table_ids
    assert (tmp_path / "historical_table_assets" / "derived_metric_matrix_table.html").is_file()
    derived_asset = next(asset for asset in pack["assets"] if asset.get("table_id") == "derived_metric_matrix")
    assert "aov_derived" in derived_asset["insight_input"]["used_metric_names"]


def test_business_analysis_package_adds_deeper_data_methods(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=12, freq="MS"),
            "channel": ["direct", "marketplace", "direct", "social", "marketplace", "direct"] * 2,
            "region": ["east", "south", "north", "west"] * 3,
            "revenue": [100, 130, 115, 90, 160, 145, 170, 180, 999, 155, 190, 210],
            "gross_margin": [0.32, 0.34, 0.31, 0.29, 0.35, 0.33, 0.36, 0.37, 0.2, 0.35, 0.38, 0.39],
            "repeat_rate": [0.42, None, 0.39, 0.37, 0.45, 0.43, 0.46, None, 0.35, 0.44, 0.47, 0.48],
        }
    )

    package = build_business_analysis_package(workspace=tmp_path, data_frame=frame)
    manifest = package["manifest"]

    assert (tmp_path / "historical_missingness_diagnostics.json").is_file()
    assert (tmp_path / "historical_outlier_influence_summary.json").is_file()
    assert (tmp_path / "historical_time_trend_slices.json").is_file()
    assert (tmp_path / "historical_concentration_diagnostics.json").is_file()
    assert manifest["missingness_issue_count"] >= 1
    assert manifest["outlier_metric_count"] >= 1
    assert manifest["time_trend_count"] >= 1
    assert manifest["concentration_signal_count"] >= 1
    assert "time_trend_slices" in manifest["asset_ready_views"]
    assert package["time_trend_slices"]["trends"]
    assert package["outlier_influence_summary"]["outliers"]


def test_business_analysis_package_multi_table_tracks_table_profiles(tmp_path: Path) -> None:
    orders = pd.DataFrame(
        {
            "order_id": [1, 2, 3, 4],
            "customer_id": ["c1", "c2", "c1", "c3"],
            "channel": ["平台", "直营", "平台", "社交电商"],
            "revenue": [120, 140, 110, 90],
            "gross_margin": [0.25, 0.34, 0.29, 0.31],
        }
    )
    customers = pd.DataFrame(
        {
            "customer_id": ["c1", "c2", "c3"],
            "region": ["东区", "南区", "西区"],
            "segment": ["高价值", "成长型", "价格敏感"],
            "repeat_purchase_rate": [0.56, 0.49, 0.38],
        }
    )
    package = build_business_analysis_package(
        workspace=tmp_path,
        data_frames={"orders": orders, "customers": customers},
        data_frame=orders,
    )

    profile = package["data_profile"]
    assert profile["table_count"] == 2
    assert any(item["table_id"] == "orders" for item in profile["tables"])
    assert any(item["table_id"] == "customers" for item in profile["tables"])
    assert (tmp_path / "historical_data_asset_manifest.json").is_file()


def test_historical_stage_order_uses_reverse_spec_and_layout_packs() -> None:
    stages = _default_stage_order("historical_style_report_cli_pipeline")
    stage_ids = [stage["stage_id"] for stage in stages]
    stage_by_id = {stage["stage_id"]: stage for stage in stages}

    assert stage_ids[:6] == [
        "pdf_visual_parse",
        "source_region_profile_pack",
        "text_logic_parse",
        "visual_semantic_spec",
        "chart_grammar_compile",
        "source_chart_grammar_profile_pack",
    ]
    assert stage_ids[6:11] == ["reverse_spec", "data_context_pack", "data_storyline_scan", "report_logic_blueprint", "page_plan"]
    assert stage_by_id["reverse_spec"]["depends_on"] == ["source_chart_grammar_profile_pack"]
    assert "template_intake" not in stage_ids
    assert stage_ids[stage_ids.index("table_asset_pack") + 1] == "collage_asset_pack"
    assert stage_ids[stage_ids.index("collage_asset_pack") + 1] == "visual_asset_render"
    assert stage_ids[stage_ids.index("visual_asset_render") + 1] == "deck_layout_pack"
    assert stage_ids[stage_ids.index("deck_layout_pack") + 1] == "html_css_package"


def test_layout_harmony_features_detect_balance_and_spacing() -> None:
    harmony = _layout_harmony_features(
        page_metrics={"text_density": {"avg_text_chars": 920, "avg_line_count": 34}},
        edge_features={"average": {"center_ink_ratio": 0.045}},
        region_features={
            "available": True,
            "average_regions": {
                "title_region_norm": [0.08, 0.05, 0.92, 0.14],
                "primary_visual_region_norm": [0.08, 0.2, 0.7, 0.62],
                "right_annotation_region_norm": [0.73, 0.2, 0.92, 0.62],
                "narrative_region_norm": [0.08, 0.68, 0.92, 0.84],
                "footer_region_norm": [0.08, 0.91, 0.92, 0.96],
                "margin_norm": {"left": 0.08, "right": 0.08, "top": 0.05, "bottom": 0.04},
                "right_annotation_column_likelihood": 0.32,
                "two_column_narrative_likelihood": 0.28,
            },
        },
        primitive_features={
            "average_primitives": {
                "horizontal_rule_count": 4,
                "vertical_rule_count": 2,
                "narrative_line_count": 5,
                "footer_line_count": 1,
            }
        },
        dominant_orientation="portrait",
    )

    assert harmony["available"]
    assert harmony["balance_mode"] == "visual_with_right_annotation"
    assert harmony["recommended_content_columns"] == 2
    assert harmony["harmony_score"] >= 0.8
    assert "reserve_footer_clearance" in harmony["harmony_rules"]


def test_chart_grammar_contract_prefers_detected_visual_language() -> None:
    primitives = {
        "axis_likelihood": 0.74,
        "legend_likelihood": 0.42,
        "vertical_bar_likelihood": 0.68,
        "horizontal_bar_likelihood": 0.18,
        "line_chart_likelihood": 0.32,
        "scatter_likelihood": 0.12,
        "table_grid_likelihood": 0.08,
    }

    dominant = _dominant_chart_grammar(primitives)
    contract = _chart_grammar_contract_from_primitives(primitives, dominant)

    assert dominant == "vertical_bar_chart"
    assert "vertical_bar" in contract["preferred_chart_kinds"]
    assert "axis_based_exhibit" in contract["chart_grammar_tokens"]
    assert contract["axis_likelihood"] == 0.74


def test_collage_and_deck_layout_asset_packs_are_deterministic(tmp_path: Path) -> None:
    current_context = {
        "dataset_name": "ops_smoke",
        "sheet_name": "main",
        "target_page_count_min": 28,
        "target_page_count_max": 40,
        "executive_summary": ["Channel mix requires budget reallocation.", "Retention varies by source."],
        "section_summaries": [{"title": "Channel diagnosis", "summary": "Paid traffic is volatile."}],
        "column_summaries": [
            {"name": "channel", "dtype": "category", "unique_count": 4},
            {"name": "revenue", "dtype": "number", "unique_count": 200},
        ],
    }
    support_tables = {
        "kpi_snapshot": [
            {"metric": "revenue", "aggregation": "sum", "value": 1000},
            {"metric": "retention_d7", "aggregation": "mean", "value": 0.42},
        ],
        "ranking_tables": [
            {
                "dimension": "channel",
                "rows": [
                    {"channel": "SEO", "revenue": 600, "row_count": 30},
                    {"channel": "Paid", "revenue": 240, "row_count": 18},
                ],
            }
        ],
    }
    visual_reference = {"visual_style_tokens": ["corporate_blue_white", "module_divider"]}
    collage_source = build_historical_collage_source(
        current_report_context=current_context,
        support_tables=support_tables,
        visual_reference=visual_reference,
    )
    collage_source_path = tmp_path / "historical_collage_source.json"
    _write_json(collage_source_path, collage_source)

    collage_pack = render_historical_collage_asset_pack(
        workspace=tmp_path,
        collage_source_path=collage_source_path,
    )
    assert collage_pack["collage_count"] >= 7
    assert (tmp_path / "historical_collage_assets_index.json").is_file()

    reverse_spec_path = tmp_path / "01_historical_reverse_spec.json"
    _write_json(
        reverse_spec_path,
        {
            "source_name": "Yili-like sample",
            "historical_report_family": "brand_analysis_deck_yili_family",
            "template_signals": ["blue corporate deck"],
            "section_blueprint": [],
            "tone_rules": [],
            "must_preserve": [],
            "must_avoid": [],
            "unsupported_or_softened_sections": [],
        },
    )
    page_plan_path = tmp_path / "02_historical_page_plan.json"
    _write_json(
        page_plan_path,
        {
            "page_count_target": {
                "recommended": 32,
                "min": 28,
                "max": 40,
                "hard_floor": 24,
                "hard_ceiling": 44,
                "family_target": "Yili deck family",
            },
            "page_type_sequence": [
                {"page_template_type": "cover_page", "title": "Cover"},
                {"page_template_type": "toc_navigation_page", "title": "TOC"},
                {"page_template_type": "module_divider_page", "title": "Module"},
                {"page_template_type": "thesis_chart_page", "title": "Chart"},
                {"page_template_type": "comparison_matrix_page", "title": "Comparison"},
                {"page_template_type": "ranking_table_page", "title": "Ranking"},
                {"page_template_type": "summary_map_page", "title": "Summary"},
                {"page_template_type": "appendix_detail_table_page", "title": "Appendix"},
            ],
        },
    )
    _write_json(
        tmp_path / "historical_chart_assets_index.json",
        {
            "chart_count": 1,
            "assets": [
                {
                    "title": "Trend",
                    "path": str((tmp_path / "trend.svg").resolve()),
                    "file_name": "trend.svg",
                    "recommended_page_role": "thesis_chart_page",
                }
            ],
        },
    )
    _write_json(
        tmp_path / "historical_table_assets_index.json",
        {
            "table_count": 1,
            "assets": [
                {
                    "title": "KPI",
                    "path": str((tmp_path / "kpi.html").resolve()),
                    "file_name": "kpi.html",
                    "recommended_page_role": "kpi_scorecard_page",
                }
            ],
        },
    )
    current_context_path = tmp_path / "current_report_context.json"
    _write_json(current_context_path, current_context)

    layout_pack = render_historical_deck_layout_pack(
        workspace=tmp_path,
        reverse_spec_path=reverse_spec_path,
        page_plan_path=page_plan_path,
        chart_assets_index_path=tmp_path / "historical_chart_assets_index.json",
        table_assets_index_path=tmp_path / "historical_table_assets_index.json",
        collage_assets_index_path=Path(collage_pack["index_path"]),
        current_report_context_path=current_context_path,
    )

    assert layout_pack["historical_report_family"] == "brand_analysis_deck_yili_family"
    assert layout_pack["page_count"] >= 12
    assert layout_pack["template_counts"]["module_divider_page"] >= 3
    assert layout_pack["template_counts"]["collage_preference_page"] >= 1
    assert (tmp_path / "historical_deck_layout_pack.json").is_file()
    layout_payload = json.loads((tmp_path / "historical_deck_layout_pack.json").read_text(encoding="utf-8"))
    assert layout_payload["report_logic_contract"]["applied_page_count"] == layout_payload["page_count"]
    assert layout_payload["quality_metrics"]["report_logic"]["logic_role_coverage_score"] > 0
    assert all("logic_role" in page for page in layout_payload["pages"])


def test_chart_asset_pack_derives_more_than_base_four_charts(tmp_path: Path) -> None:
    chart_bundle_path = tmp_path / "historical_chart_bundle.json"
    _write_json(
        chart_bundle_path,
        {
            "distribution": {
                "title": "Revenue Distribution",
                "x": ["A", "B", "C", "D", "E"],
                "y": [10, 20, 35, 22, 13],
            },
            "category": {
                "title": "Channel Mix",
                "x": ["SEO", "Paid", "Referral", "Direct", "Community"],
                "y": [520, 240, 180, 140, 90],
            },
            "correlation": {
                "title": "Metric Correlation",
                "labels": ["revenue", "orders", "retention", "cac"],
                "matrix": [
                    [1, 0.82, 0.41, -0.22],
                    [0.82, 1, 0.35, -0.31],
                    [0.41, 0.35, 1, -0.18],
                    [-0.22, -0.31, -0.18, 1],
                ],
            },
            "scatter": {
                "title": "CAC vs Retention",
                "x_label": "CAC",
                "y_label": "Retention",
                "points": [[10, 0.3], [12, 0.33], [18, 0.42], [22, 0.36], [28, 0.48], [32, 0.52], [36, 0.41], [42, 0.58]],
            },
        },
    )

    pack = render_historical_chart_asset_pack(
        workspace=tmp_path,
        chart_bundle_path=chart_bundle_path,
    )

    chart_ids = {asset["chart_id"] for asset in pack["assets"]}
    assert pack["chart_count"] >= 12
    assert {
        "category_share_donut",
        "category_pareto",
        "category_value_bridge",
        "category_priority_bubble",
        "distribution_cumulative",
        "correlation_top_pairs",
        "scatter_quadrant",
        "scatter_portfolio_matrix",
    }.issubset(chart_ids)
    localized_titles = {asset.get("localized_title") for asset in pack["assets"] if asset.get("status") == "completed"}
    assert "渠道收入结构 价值桥" in localized_titles
    assert "获客成本 x 留存 2x2 组合矩阵" in localized_titles


def test_chart_asset_pack_honors_chart_grammar_contract(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "historical_visual_reference.json",
        {
            "style_transfer_contract": {
                "colors": {"accent": "#0b7f5c", "background": "#ffffff"},
                "furniture": {"source_footer": True},
                "chart_style": {
                    "chart_grammar_contract": {
                        "dominant_chart_grammar": "vertical_bar_chart",
                        "preferred_chart_kinds": ["vertical_bar", "line", "histogram"],
                        "avoid_chart_kinds": ["decorative_donut"],
                        "chart_grammar_tokens": ["axis_based_exhibit"],
                    }
                },
                "visual_primitives": {
                    "available": True,
                    "dominant_visual_grammar": "vertical_bar_chart",
                    "chart_grammar_contract": {
                        "dominant_chart_grammar": "vertical_bar_chart",
                        "preferred_chart_kinds": ["vertical_bar", "line", "histogram"],
                    },
                },
            },
            "visual_style_signature": {"background_mode": "white_document"},
        },
    )
    chart_bundle_path = tmp_path / "historical_chart_bundle.json"
    _write_json(
        chart_bundle_path,
        {
            "category": {
                "title": "Channel Mix",
                "x": ["A", "B", "C"],
                "y": [120, 90, 60],
            }
        },
    )

    pack = render_historical_chart_asset_pack(
        workspace=tmp_path,
        chart_bundle_path=chart_bundle_path,
    )

    category_asset = next(asset for asset in pack["assets"] if asset["chart_id"] == "category_mix")
    assert category_asset["kind"] == "vertical_bar"
    assert category_asset["visual_contract_tokens"]["matched_chart_grammar"]
    assert category_asset["visual_contract_tokens"]["dominant_chart_grammar"] == "vertical_bar_chart"


def test_deck_layout_adds_chart_pages_when_plan_underuses_assets(tmp_path: Path) -> None:
    reverse_spec_path = tmp_path / "01_historical_reverse_spec.json"
    page_plan_path = tmp_path / "02_historical_page_plan.json"
    chart_assets_index = tmp_path / "historical_chart_assets_index.json"
    table_assets_index = tmp_path / "historical_table_assets_index.json"
    collage_assets_index = tmp_path / "historical_collage_assets_index.json"
    context_path = tmp_path / "current_report_context.json"
    _write_json(
        reverse_spec_path,
        {
            "source_name": "Yili-like sample",
            "historical_report_family": "brand_analysis_deck_yili_family",
        },
    )
    _write_json(
        page_plan_path,
        {
            "page_count_target": {"recommended": 28, "min": 24, "max": 40},
            "page_type_sequence": [
                {"page_template_type": "cover_page", "title": "Cover"},
                {"page_template_type": "toc_navigation_page", "title": "TOC"},
                {"page_template_type": "module_divider_page", "title": "Module"},
                {"page_template_type": "summary_map_page", "title": "Summary"},
            ],
        },
    )
    _write_json(
        chart_assets_index,
        {
            "chart_count": 6,
            "assets": [
                {
                    "title": f"Chart {index}",
                    "path": str((tmp_path / f"chart_{index}.svg").resolve()),
                    "file_name": f"chart_{index}.svg",
                    "recommended_page_role": "thesis_chart_page",
                }
                for index in range(1, 7)
            ],
        },
    )
    _write_json(table_assets_index, {"table_count": 0, "assets": []})
    _write_json(collage_assets_index, {"collage_count": 0, "assets": []})
    _write_json(context_path, {"dataset_name": "ops"})

    layout_pack = render_historical_deck_layout_pack(
        workspace=tmp_path,
        reverse_spec_path=reverse_spec_path,
        page_plan_path=page_plan_path,
        chart_assets_index_path=chart_assets_index,
        table_assets_index_path=table_assets_index,
        collage_assets_index_path=collage_assets_index,
        current_report_context_path=context_path,
    )

    assert layout_pack["page_count"] >= 10
    assert layout_pack["template_counts"]["thesis_chart_page"] >= 6
    chart_pages = [item for item in layout_pack["pages"] if item["page_template_type"] == "thesis_chart_page"]
    assert all(page["asset_refs"] and page["asset_refs"][0]["asset_type"] == "chart" for page in chart_pages)
    page = chart_pages[0]
    assert "management_thesis" in page
    assert "storyline_source" in page
    assert "fallback_points_source" in page
    assert "primary_asset_role" in page


def test_deck_layout_counts_derived_metric_coverage(tmp_path: Path) -> None:
    reverse_spec_path = tmp_path / "01_historical_reverse_spec.json"
    page_plan_path = tmp_path / "02_historical_page_plan.json"
    chart_assets_index = tmp_path / "historical_chart_assets_index.json"
    table_assets_index = tmp_path / "historical_table_assets_index.json"
    collage_assets_index = tmp_path / "historical_collage_assets_index.json"
    data_manifest_path = tmp_path / "historical_data_asset_manifest.json"
    metric_inventory_path = tmp_path / "historical_metric_inventory.json"
    derived_inventory_path = tmp_path / "historical_derived_metric_inventory.json"

    _write_json(reverse_spec_path, {"historical_report_family": "generic_chinese_analysis_deck"})
    _write_json(page_plan_path, {"page_type_sequence": [{"page_template_type": "cover_page", "title": "Cover"}]})
    _write_json(chart_assets_index, {"chart_count": 0, "assets": []})
    _write_json(
        table_assets_index,
        {
            "table_count": 1,
            "assets": [
                {
                    "table_id": "derived_metric_matrix",
                    "title": "派生指标矩阵",
                    "recommended_page_role": "appendix_glossary_page",
                    "asset_type": "table",
                    "insight_input": {
                        "used_metric_names": ["aov_derived"],
                        "rows": [{"metric_raw_key": "aov_derived", "formula": "revenue / orders"}],
                    },
                }
            ],
        },
    )
    _write_json(collage_assets_index, {"collage_count": 0, "assets": []})
    _write_json(
        metric_inventory_path,
        {
            "metrics": [
                {"raw_key": "revenue", "localized_label": "收入"},
                {"raw_key": "aov_derived", "localized_label": "客单价", "metric_kind": "derived_metric", "is_derived": True},
            ]
        },
    )
    _write_json(
        derived_inventory_path,
        {
            "derived_metric_count": 1,
            "metrics": [{"raw_key": "aov_derived", "localized_label": "客单价", "metric_kind": "derived_metric", "is_derived": True}],
        },
    )
    _write_json(
        data_manifest_path,
        {
            "metric_count": 2,
            "derived_metric_count": 1,
            "dimension_count": 0,
            "source_artifacts": {
                "metric_inventory": str(metric_inventory_path.resolve()),
                "derived_metric_inventory": str(derived_inventory_path.resolve()),
            },
        },
    )

    layout_pack = render_historical_deck_layout_pack(
        workspace=tmp_path,
        reverse_spec_path=reverse_spec_path,
        page_plan_path=page_plan_path,
        chart_assets_index_path=chart_assets_index,
        table_assets_index_path=table_assets_index,
        collage_assets_index_path=collage_assets_index,
        data_asset_manifest_path=data_manifest_path,
    )
    data_coverage = layout_pack["quality_metrics"]["data_coverage"]

    assert data_coverage["available_derived_metric_count"] == 1
    assert data_coverage["used_derived_metric_count"] == 1
    assert "aov_derived" in data_coverage["used_derived_metric_names"]


def test_html_asset_injection_adds_missing_chart_pages(tmp_path: Path) -> None:
    chart_dir = tmp_path / "historical_chart_assets"
    chart_dir.mkdir()
    svg_path = chart_dir / "chart_1.svg"
    svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
    html_path = tmp_path / "06_historical_style_report.html"
    css_path = tmp_path / "06_historical_style_report.css"
    layout_path = tmp_path / "historical_deck_layout_pack.json"
    html_path.write_text(
        "<html><head><link rel='stylesheet' href='06_historical_style_report.css'></head><body><section>base</section></body></html>",
        encoding="utf-8",
    )
    css_path.write_text("@page { size: A4; margin: 0; }\nsection { break-after: page; }", encoding="utf-8")
    _write_json(
        layout_path,
        {
            "pages": [
                {
                    "page_template_type": "thesis_chart_page",
                    "title": "Chart page",
                    "module": "diagnosis",
                    "asset_refs": [
                        {
                            "asset_type": "chart",
                            "title": "Injected Chart",
                            "path": str(svg_path.resolve()),
                            "file_name": svg_path.name,
                        }
                    ],
                }
            ]
        },
    )

    result = ensure_historical_deck_assets_embedded(
        workspace=tmp_path,
        html_path=html_path,
        css_path=css_path,
        deck_layout_pack_path=layout_path,
    )

    html_text = html_path.read_text(encoding="utf-8")
    css_text = css_path.read_text(encoding="utf-8")
    assert result["injected_asset_count"] == 1
    assert "historical-auto-asset-page" in html_text
    assert "historical_chart_assets/chart_1.svg" in html_text
    assert "historical-auto-asset-page" in css_text


def test_page_plan_validator_normalizes_target_and_yili_page_families(tmp_path: Path) -> None:
    markdown_path = tmp_path / "02_historical_page_plan.md"
    json_path = tmp_path / "02_historical_page_plan.json"
    markdown_path.write_text("# Page plan\n", encoding="utf-8")
    _write_json(
        json_path,
        {
            "page_count_target": 32,
            "page_type_sequence": [
                "cover_page",
                "toc_navigation_page",
                "module_divider_page",
                "thesis_chart_page",
                "comparison_matrix_page",
                "ranking_table_page",
                "summary_map_page",
                "appendix_detail_table_page",
            ],
            "module_plan": {},
            "hero_pages": [],
            "required_visual_pages": [],
            "required_table_pages": [],
            "required_appendix_pages": [],
            "asset_usage_plan": {},
            "page_density_rules": {},
        },
    )

    payload = _validate_historical_page_plan(
        markdown_path,
        json_path,
        historical_report_family="brand_analysis_deck_yili_family",
    )

    assert payload["page_count_target"]["hard_floor"] == 32
    assert payload["page_count_target"]["hard_ceiling"] == 32
    assert payload["page_count_target"]["family_target"]
    assert payload["page_type_sequence"][0]["page_template_type"] == "cover_page"
    assert payload["page_type_sequence"][0]["logic_role"] == "opening_thesis"
    assert isinstance(payload["page_type_sequence"][3]["claim_evidence_action"], dict)
    assert payload["logic_flow_plan"]


def test_historical_logic_reference_outputs_argument_contract(tmp_path: Path) -> None:
    payload = build_historical_logic_reference_payload(
        source_path=tmp_path / "sample.md",
        historical_text=(
            "Executive thesis: growth is uneven and management must prioritize high-retention segments.\n"
            "What should leadership fix first?\n"
            "Exhibit 1 shows that the premium segment leads revenue and repeat purchase.\n"
            "This is driven by channel mix and service level differences.\n\n"
            "However, low-frequency users remain below target compared with core users.\n"
            "Therefore the team should improve onboarding and protect high-value demand.\n"
            "Source: sample operating dataset.\n"
        ),
    )

    assert payload["available"]
    assert payload["logic_flow_contract"]["dominant_logic_pattern"]
    assert "opening_thesis" in payload["logic_flow_contract"]["recommended_argument_arc"]
    assert payload["claim_evidence_action_chains"]
    assert payload["page_logic"][0]["logic_role"] == "opening_thesis"


def test_report_logic_blueprint_combines_history_and_data_storyline(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "historical_derived_metric_inventory.json",
        {
            "derived_metric_count": 1,
            "metrics": [
                {
                    "raw_key": "aov_derived",
                    "localized_label": "客单价",
                    "metric_kind": "derived_metric",
                    "is_derived": True,
                    "formula": "revenue / orders",
                    "business_meaning": "衡量订单收入质量",
                }
            ],
        },
    )
    blueprint = build_historical_report_logic_blueprint(
        workspace=tmp_path,
        reverse_spec={
            "historical_report_family": "mckinsey_consulting_deck_family",
            "argument_arc": ["opening_thesis", "diagnostic_evidence", "management_implication", "recommendation"],
        },
        logic_reference={
            "available": True,
            "dominant_logic_pattern": "answer_first_exhibit_led_argument",
        },
        data_storyline={
            "headline_data_story": "渠道增长分化，复购和服务水平决定下一阶段优先级。",
            "metric_priorities": [
                {"metric_raw_key": "revenue", "metric_label": "收入"},
                {"metric_raw_key": "repeat_rate", "metric_label": "复购率"},
            ],
            "dimension_priorities": [
                {"dimension_raw_key": "channel", "dimension_label": "渠道"},
                {"dimension_raw_key": "region", "dimension_label": "区域"},
            ],
            "action_candidates": [
                {"action_type": "资源重配", "object_label": "高复购渠道", "priority": "high", "metric_label": "复购率"}
            ],
        },
        data_manifest={"metric_count": 8, "derived_metric_count": 1, "dimension_count": 4},
        current_context={"user_requirement": "找出经营增长抓手"},
        json_output_path=tmp_path / "03_report_logic_blueprint.json",
        markdown_output_path=tmp_path / "03_report_logic_blueprint.md",
    )

    assert (tmp_path / "03_report_logic_blueprint.json").is_file()
    assert (tmp_path / "03_report_logic_blueprint.md").is_file()
    assert blueprint["dominant_logic_pattern"] == "answer_first_exhibit_led_argument"
    assert blueprint["argument_arc"][0] == "opening_thesis"
    assert blueprint["logic_modules"]
    assert blueprint["logic_quality_gates"]["minimum_derived_metric_mentions"] == 1
    assert blueprint["derived_metric_focus"][0]["metric"] == "客单价"
    assert any(item["is_derived"] for item in blueprint["metric_to_logic_map"])
    assert blueprint["recommendation_backbone"][0]["target_object"] == "高复购渠道"
