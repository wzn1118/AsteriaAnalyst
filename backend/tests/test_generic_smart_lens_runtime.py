from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import codex_runtime_pipeline_service as pipeline
from app.services import codex_runtime_prompt_templates as prompts


def _write_smart_lens_contract(root: Path, *, source: str = "codex_runtime_smart_lens_composer", lens_name: str = "物种形态结构分化镜头") -> tuple[Path, Path]:
    payload = {
        "version": "generic_smart_lens_contract_v1",
        "source": source,
        "lens_name": lens_name,
        "why_this_lens": "字段 species、island、sex 与指标 body_mass_g、bill_length_mm、flipper_length_mm 共同指向对象分组、形态差异和图表分区。",
        "data_theme": "企鹅形态测量",
        "primary_objects": ["species", "island"],
        "core_comparisons": ["species 与 body_mass_g", "island 与 flipper_length_mm"],
        "derived_metric_roles": ["体量承载指数解释体重与鳍长的组合差异"],
        "chart_reading_strategy": ["先看 Bxx 分区，再回到映射表核对对象和值"],
        "narrative_flow": ["从物种分组进入形态指标", "再看岛屿和性别边界"],
        "claim_boundaries": ["只能解释样本内形态差异，不能外推全部企鹅种群"],
        "forbidden_framings": ["不写经营动作和 Owner"],
    }
    md_path = root / "generic_smart_lens_contract.md"
    json_path = root / "generic_smart_lens_contract.json"
    md_path.write_text(f"# {lens_name}\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return md_path, json_path


def _write_visual_route_contract(root: Path, *, report_lens: str = "smart_lens") -> tuple[Path, Path]:
    payload = {
        "version": "generic_visual_route_contract_v2",
        "source": "codex_runtime_visual_route_decision",
        "report_lens": report_lens,
        "route_mode": "cli_field_metric_route",
        "field_roles": {
            "object_dimensions": ["species"],
            "time_dimensions": [],
            "scale_metrics": ["body_mass_g", "flipper_length_mm"],
            "count_metrics": [],
            "ratio_metrics": [],
            "quality_or_value_metrics": [],
            "risk_or_efficiency_metrics": [],
        },
        "visual_candidates": [
            {
                "candidate_id": "species_shape_partition",
                "object_dimension": "species",
                "object_key_fields": ["species"],
                "chart_form": "quadrant_bubble",
                "x_metric_id": "body_mass_g",
                "x_metric_name": "body_mass_g",
                "y_metric_id": "flipper_length_mm",
                "y_metric_name": "flipper_length_mm",
                "size_metric_id": "",
                "size_metric_name": "",
                "size_mode": "uniform_size",
                "size_reason": "没有第三个稳定规模指标时使用等尺寸，避免伪造气泡含义。",
                "quadrant_labels": {
                    "top_right": "大体量长鳍分区",
                    "top_left": "轻体量长鳍分区",
                    "bottom_left": "轻体量短鳍分区",
                    "bottom_right": "大体量短鳍分区",
                },
                "quadrant_reasoning": "体重和鳍长共同构成形态结构差异。",
                "boundary_labels": ["体重中位线", "鳍长中位线"],
                "why_selected": "species 是对象维度，body_mass_g 与 flipper_length_mm 是同粒度数值指标，适合做象限气泡图。",
                "why_rejected": "",
                "main_report_candidate": True,
                "appendix_candidate": False,
                "required_bubble": True,
            }
        ],
        "required_bubbles": ["species_shape_partition"],
        "required_quadrants": ["species_shape_partition"],
        "required_scatters": [],
        "appendix_visual_candidates": [],
        "rejected_candidates": [],
    }
    md_path = root / "generic_visual_route_contract.md"
    json_path = root / "generic_visual_route_contract.json"
    md_path.write_text("# route\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return md_path, json_path


def test_generic_pipeline_stage_order_places_smart_lens_before_question_tree() -> None:
    stages = [stage["stage_id"] for stage in pipeline._default_stage_order("generic_long_cli_pipeline")]

    assert stages.index("generic_derived_metric_discovery") < stages.index("visual_route_decision")
    assert stages.index("visual_route_decision") < stages.index("generic_smart_lens_composer")
    assert stages.index("generic_smart_lens_composer") < stages.index("question_tree")


def test_cross_table_pipeline_stage_order_places_smart_lens_before_question_tree() -> None:
    stages = [stage["stage_id"] for stage in pipeline._default_stage_order("multi_table_generic_long_cli_pipeline")]

    assert stages.index("cross_table_derived_metric_discovery") < stages.index("cross_table_visual_route_decision")
    assert stages.index("cross_table_visual_route_decision") < stages.index("cross_table_generic_smart_lens_composer")
    assert stages.index("cross_table_generic_smart_lens_composer") < stages.index("cross_table_question_tree")


def test_generic_report_lens_defaults_to_runtime_smart_lens() -> None:
    assert pipeline._infer_generic_report_lens({}) == "smart_lens"
    assert pipeline._infer_generic_report_lens({"report_lens": "generic_analytical"}) == "smart_lens"
    assert pipeline._infer_generic_report_lens({"user_requirement": "请做一个数据结构分析报告"}) == "smart_lens"


def test_generic_report_lens_only_switches_to_business_for_explicit_management_intent() -> None:
    assert pipeline._infer_generic_report_lens({"user_requirement": "请输出管理层经营建议和行动计划"}) == "business_management"
    assert pipeline._infer_generic_report_lens({"report_lens": "business_management"}) == "business_management"


def test_validate_generic_smart_lens_contract_accepts_runtime_cli_contract(tmp_path: Path) -> None:
    md_path, json_path = _write_smart_lens_contract(tmp_path)

    payload = pipeline._validate_generic_smart_lens_contract(md_path, json_path)

    assert payload["version"] == "generic_smart_lens_contract_v1"
    assert payload["source"] == "codex_runtime_smart_lens_composer"
    assert payload["lens_name"] == "物种形态结构分化镜头"


def test_validate_generic_smart_lens_contract_rejects_fixed_lens_name(tmp_path: Path) -> None:
    md_path, json_path = _write_smart_lens_contract(tmp_path, lens_name="generic smart lens")

    with pytest.raises(ValueError, match="fixed generic lens name"):
        pipeline._validate_generic_smart_lens_contract(md_path, json_path)


def test_validate_generic_smart_lens_contract_rejects_backend_source(tmp_path: Path) -> None:
    md_path, json_path = _write_smart_lens_contract(tmp_path, source="backend_deterministic_synthesis")

    with pytest.raises(ValueError, match="runtime CLI"):
        pipeline._validate_generic_smart_lens_contract(md_path, json_path)


def test_visual_route_contract_rejects_fixed_report_lens_categories(tmp_path: Path) -> None:
    md_path, json_path = _write_visual_route_contract(tmp_path, report_lens="generic_analytical")

    with pytest.raises(ValueError, match="fixed report_lens"):
        pipeline._validate_generic_visual_route_contract(md_path, json_path)


def test_visual_route_contract_normalizes_empty_lens_to_smart_lens(tmp_path: Path) -> None:
    md_path, json_path = _write_visual_route_contract(tmp_path, report_lens="")

    payload = pipeline._validate_generic_visual_route_contract(md_path, json_path)

    assert payload["report_lens"] == "smart_lens"


def test_smart_lens_usage_gate_requires_lens_name_in_report(tmp_path: Path) -> None:
    _md_path, json_path = _write_smart_lens_contract(tmp_path, lens_name="物种形态结构分化镜头")

    pipeline._validate_generic_smart_lens_contract_usage(
        "本报告采用物种形态结构分化镜头解释 species 的形态差异。",
        "",
        json_path,
    )


def test_smart_lens_usage_gate_rejects_report_that_ignores_contract_name(tmp_path: Path) -> None:
    _md_path, json_path = _write_smart_lens_contract(tmp_path, lens_name="物种形态结构分化镜头")

    with pytest.raises(ValueError, match="lens_name"):
        pipeline._validate_generic_smart_lens_contract_usage(
            "本报告只写通用数据分析，没有使用本次生成的镜头名称。",
            "",
            json_path,
        )


def test_prompt_uses_clean_smart_lens_and_partition_table_language() -> None:
    posture = prompts._generic_lens_posture({})
    table_rule = prompts._generic_figure_table_instruction({})

    assert "generic_smart_lens_contract_json" in posture
    assert "固定镜头" not in posture
    assert "经营、管理层、本周动作" in posture
    assert "分区对象清单" in table_rule
    assert "分析解释" in table_rule
    assert "Owner" not in table_rule
