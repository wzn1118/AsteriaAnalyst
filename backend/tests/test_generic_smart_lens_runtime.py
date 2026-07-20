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
        "lens_storyline": [
            "先以 species 区分物种，再确认 island 的样本边界。",
            "比较 body_mass_g 和 flipper_length_mm 的形态组合。",
            "用 B01 至 B04 的象限对象池检查分区是否稳定。",
            "最后说明 sex 分层可能改变形态差异的读法。",
        ],
        "chart_to_lens_map": [
            "species_shape_partition 使用 body_mass_g 和 flipper_length_mm 展示 B01-B04 形态分区。",
        ],
        "native_vs_derived_metric_reading": [
            "body_mass_g 给出原始体量，体量承载指数把体重和鳍长组合为可比较的形态读法。",
        ],
        "object_universe_policy": {
            "coverage": "保留所有 species、island 和 sex 组合；缺失测量值显式标记而不删除对象。",
        },
        "context_understanding": {
            "source_context": "企鹅形态测量样本",
            "unit_of_analysis": "单只企鹅观测记录",
            "time_scope": "该样本未提供连续时间序列，只解释当前测量覆盖范围。",
            "table_or_field_roles": "species、island、sex 是分组字段；body_mass_g、bill_length_mm、flipper_length_mm 是形态测量字段。",
            "why_this_context_matters": "物种、岛屿和性别分层决定形态指标是否可以直接比较。",
        },
        "context_evidence_map": [
            "species 字段区分物种，支持按物种读取 body_mass_g。",
            "island 字段标记采样地点，支持检查地点边界。",
            "sex 字段说明性别分层，避免把分层差异误读为物种差异。",
            "flipper_length_mm 与 body_mass_g 共同构成 B01-B04 分区坐标。",
        ],
        "grain_context_decisions": [
            "以单只企鹅为原始粒度，再按 species 汇总；不能把不同物种直接当作同一对象。",
            "island 是分层维度而不是可加总指标；不能把岛屿数量解释为样本规模。",
        ],
        "semantic_vocabulary": [
            "species 表示物种分类。",
            "island 表示采样岛屿。",
            "body_mass_g 表示体重（克）。",
            "flipper_length_mm 表示鳍长（毫米）。",
        ],
        "context_boundaries": ["样本只支持当前观测的形态比较，不证明全部企鹅种群的因果关系。"],
        "reader_context_primer": [
            "先按 species 识别对象，再读取岛屿和性别分层。",
            "B01-B04 是图表分区标识，不是生物学分类。",
            "缺失测量值不能被当成体型较小或较大。",
        ],
        "reader_takeaways": [
            "物种之间的 body_mass_g 与 flipper_length_mm 组合存在可视化分区。",
            "岛屿和性别是解释分区差异前必须核对的边界。",
            "体量承载指数帮助将两个原始形态测量放在同一读法中。",
        ],
        "headline_conclusion": "企鹅样本的物种形态差异需要在岛屿和性别边界下，结合体重与鳍长分区解读。",
        "top_numeric_conclusions": [
            "B01 汇集体重和鳍长均低于样本中位线的对象。",
            "B02 汇集体重低于中位线、鳍长高于中位线的对象。",
            "B03 汇集体重和鳍长均高于样本中位线的对象。",
            "B04 汇集体重高于中位线、鳍长低于中位线的对象。",
            "body_mass_g、bill_length_mm、flipper_length_mm 三项测量共同支持形态比较。",
        ],
        "strongest_patterns": ["species 分组后的体重和鳍长组合比单看任一测量更能显示结构差异。"],
        "counterintuitive_findings": ["单独较高的 body_mass_g 不一定对应较长的 flipper_length_mm，需回到 Bxx 分区核对。"],
        "representative_objects": ["species 分组", "island 分层", "B01-B04 形态分区"],
        "misread_warnings": ["不要把 Bxx 分区当作新的物种，也不要将缺失测量值解释为低体量。"],
        "final_takeaways": [
            "B01 用于核对低体重、短鳍长对象。",
            "B02 用于核对低体重、长鳍长对象。",
            "B03 用于核对高体重、长鳍长对象。",
            "B04 用于核对高体重、短鳍长对象。",
            "species 是首要对象分组。",
            "island 是采样边界。",
            "sex 是必要的分层字段。",
            "body_mass_g 是原始体量测量。",
            "bill_length_mm 是补充形态测量。",
            "flipper_length_mm 是分区纵轴测量。",
        ],
        "evidence_bindings": [
            {"claim": "物种分组", "evidence_files": ["penguins.csv"], "fields_or_metrics": ["species"], "numeric_anchor": "B01", "chart_or_table": "species_shape_partition", "report_section": "对象边界"},
            {"claim": "体量差异", "evidence_files": ["penguins.csv"], "fields_or_metrics": ["body_mass_g"], "numeric_anchor": "B02", "chart_or_table": "species_shape_partition", "report_section": "形态比较"},
            {"claim": "鳍长差异", "evidence_files": ["penguins.csv"], "fields_or_metrics": ["flipper_length_mm"], "numeric_anchor": "B03", "chart_or_table": "species_shape_partition", "report_section": "形态比较"},
            {"claim": "岛屿边界", "evidence_files": ["penguins.csv"], "fields_or_metrics": ["island"], "numeric_anchor": "B04", "chart_or_table": "species_shape_partition", "report_section": "分层解释"},
            {"claim": "性别分层", "evidence_files": ["penguins.csv"], "fields_or_metrics": ["sex"], "numeric_anchor": "B01", "chart_or_table": "species_shape_partition", "report_section": "解释边界"},
        ],
        "transition_bridges": [
            "确认物种对象后，才能比较同一对象粒度下的体重和鳍长。",
            "看到形态分区后，需要用岛屿和性别检查分层是否改变读法。",
            "分层核对完成后，才能给出样本内而非总体外推的结论。",
        ],
        "lens_quality_self_audit": {"specificity": 92, "evidence_density": 90, "chart_binding": 91, "anti_template_risk": "low"},
        "anti_template_checks": [
            "拒绝通用经营镜头：数据没有经营对象或动作字段。",
            "拒绝固定研究镜头：镜头由 species、island、sex 和形态测量共同决定。",
        ],
        "concise_report_plan": ["保留镜头名称、B01-B04 分区和三条样本内结论。"],
        "full_report_plan": ["保留对象分层、图表映射、分区对象清单和证据绑定。"],
        "version_plan": {
            "concise": "展示镜头、对象和关键形态分区。",
            "default": "展示分区、分层边界和证据解释。",
            "full": "展示完整证据绑定和对象清单。",
        },
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
