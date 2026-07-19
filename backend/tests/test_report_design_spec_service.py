from pathlib import Path

from app.models import SmartReportRequest
from app.services.codex_runtime_pipeline_service import create_pipeline_job
from app.services.codex_runtime_prompt_templates import (
    build_chart_insights_prompt,
    build_ecommerce_html_css_prompt,
    build_historical_style_html_css_prompt,
    build_html_css_prompt,
    build_multi_table_html_css_prompt,
)
from app.services.report_design_spec_service import (
    REPORT_LAYOUT_PRESETS,
    build_report_design_spec,
    render_report_design_spec_markdown,
    write_report_design_spec_files,
)
from app.services.r_workflow_service import _resolve_r_workflow_chart_style


def test_report_design_spec_preserves_frontend_palette_order() -> None:
    request = SmartReportRequest(
        chart_palette_preset="burgundy_luxury",
        chart_palette_colors=["#052b5f", "#f2c14e", "#2a9d8f"],
        visual_style_text="酒红、金色、绿色，正式经营汇报。",
    )

    spec = build_report_design_spec(request=request)

    assert spec["chart_palette_colors"] == ["#052b5f", "#f2c14e", "#2a9d8f"]
    assert spec["color_source"] == "frontend_chart_palette_colors"
    assert spec["derived_colors"]["primary"] == "#052b5f"
    assert spec["derived_colors"]["accent"] == "#f2c14e"
    assert spec["derived_colors"]["chart_series"] == ["#052b5f", "#f2c14e", "#2a9d8f"]
    assert spec["color_harmony"]["ratio"]["primary"] == "60%"
    assert spec["derived_colors"]["table_header_text"] in {"#ffffff", "#111827"}


def test_report_design_spec_writes_workspace_files(tmp_path: Path) -> None:
    request = SmartReportRequest(
        premium_style_preset="art_school_editorial_blueprint",
        chart_palette_colors=["#4c0519", "#d4af37", "#166534"],
        visual_style_text="高端消费风格，表格要克制。",
    )

    json_path, md_path, spec = write_report_design_spec_files(tmp_path, request=request)

    assert json_path.name == "report_design_spec.json"
    assert md_path.name == "report_design_spec.md"
    assert json_path.exists()
    assert md_path.exists()
    assert spec["chart_palette_colors"] == ["#4c0519", "#d4af37", "#166534"]
    assert spec["layout_preset_id"] == "art_school_editorial_blueprint"
    assert spec["layout_preset_name"] == "艺术学院编辑蓝图"
    assert spec["版式名称"] == "艺术学院编辑蓝图"
    assert "#d4af37" in md_path.read_text(encoding="utf-8")
    assert "版式名称：艺术学院编辑蓝图" in md_path.read_text(encoding="utf-8")


def test_report_design_spec_accepts_all_chinese_layout_presets() -> None:
    assert len(REPORT_LAYOUT_PRESETS) >= 36
    for preset_id, preset in REPORT_LAYOUT_PRESETS.items():
        request = SmartReportRequest(premium_style_preset=preset_id)
        spec = build_report_design_spec(request=request)
        assert spec["layout_preset_id"] == preset_id
        assert spec["layout_preset_name"] == preset["name"]
        assert spec["版式名称"] == preset["name"]
        assert spec["页面结构"]
        assert spec["表格风格"]
        assert spec["图表风格"]
        assert spec["附录风格"]
        assert spec["layout_detail_contract"]["页面序列"]
        assert spec["layout_detail_contract"]["组件语法"]
        assert spec["layout_detail_contract"]["禁用版式"]
        assert spec["preset_fidelity_contract"]["相似度目标"]
        assert spec["preset_fidelity_contract"]["视觉签名"]
        assert spec["preset_fidelity_contract"]["必须出现"]
        assert spec["preset_fidelity_contract"]["禁止误用"]
        assert spec["preset_acceptance_checks"]
        assert "reference_style_profile" in spec
        assert "preset_design_tokens" in spec
        assert "prohibited_brand_assets" in spec
        assert spec["cover_treatment"]
        assert spec["grid_system"]


def test_report_design_spec_financial_times_preset_has_strong_fidelity_contract() -> None:
    spec = build_report_design_spec(
        request=SmartReportRequest(premium_style_preset="financial_times_longform")
    )

    contract = spec["preset_fidelity_contract"]

    assert spec["layout_preset_name"] == "金融时报长文风"
    assert "Financial Times 纸媒头版网格" in contract["相似度目标"]
    assert "Financier-like" in contract["字体气质"]
    assert "超大 serif masthead" in contract["视觉签名"]
    assert "右侧 Briefing 栏" in contract["视觉签名"]
    assert "World Markets 小表" in contract["视觉签名"]
    assert "salmon" in contract["参考风格画像"]["paper_tone"]
    assert contract["专属设计令牌"]["paper"] == "#fff1e5"
    assert contract["专属设计令牌"]["promo_teal"] == "#00a6c8"
    assert "briefing-right-rail" in contract["参考风格画像"]["composition_blueprint"]
    assert "Financial Times logo" in contract["禁止品牌资产"]
    assert any("不要使用 FT logo" in item for item in contract["禁止误用"])
    assert any("青色和酒红 promo 横条" in item for item in contract["必须出现"])
    markdown = render_report_design_spec_markdown(spec)
    assert "相似度目标" in markdown
    assert "视觉签名" in markdown
    assert "禁止误用" in markdown
    assert "参考风格画像" in markdown
    assert "专属设计令牌" in markdown
    assert "#fff1e5" in markdown


def test_report_design_spec_layout_presets_have_distinct_choreography() -> None:
    category = build_report_design_spec(
        request=SmartReportRequest(premium_style_preset="category_management_manual")
    )
    frontline = build_report_design_spec(
        request=SmartReportRequest(premium_style_preset="frontline_action_manual")
    )
    atlas = build_report_design_spec(
        request=SmartReportRequest(premium_style_preset="premium_visual_atlas")
    )

    assert category["page_sequence_template"] != frontline["page_sequence_template"]
    assert frontline["page_sequence_template"] != atlas["page_sequence_template"]
    assert "object-task-table" in category["component_grammar"]
    assert "workorder-card" in frontline["component_grammar"]
    assert "large-visual-card" in atlas["component_grammar"]
    assert "不要只替换颜色" in category["layout_detail_contract"]["落地要求"][1]


def test_report_design_spec_unknown_layout_falls_back_with_warning() -> None:
    request = SmartReportRequest(premium_style_preset="unknown_layout")
    spec = build_report_design_spec(request=request)

    assert spec["layout_preset_id"] == "navy_white_premium"
    assert spec["layout_preset_name"] == "深蓝白高级商务"
    assert "unknown premium_style_preset ignored: unknown_layout" in spec["validation_warnings"]


def test_report_design_spec_harmonizes_arbitrary_colors() -> None:
    request = SmartReportRequest(
        chart_palette_preset="custom_color_wheel",
        chart_palette_colors=["#123abc", "#c0ffee", "#fa8072", "#00aaff"],
    )

    spec = build_report_design_spec(request=request)

    assert spec["chart_palette_colors"] == ["#123abc", "#c0ffee", "#fa8072", "#00aaff"]
    assert spec["color_source"] == "frontend_chart_palette_colors"
    assert spec["color_harmony"]["mode"] == "auto_harmonized_from_frontend_palette"
    assert spec["color_harmony"]["ratio"] == {
        "primary": "60%",
        "secondary": "25%",
        "accent": "10%",
        "neutral": "5%",
    }
    assert spec["derived_colors"]["chart_series"] == ["#123abc", "#c0ffee", "#fa8072", "#00aaff"]
    assert spec["derived_colors"]["primary"] == "#123abc"
    assert spec["derived_colors"]["table_header_text"] == "#ffffff"


def test_create_pipeline_job_persists_report_design_spec(tmp_path: Path) -> None:
    manifest = create_pipeline_job(
        pipeline_type="ecommerce_long_cli_pipeline",
        workspace_path=str(tmp_path / "{pipeline_job_id}"),
        context_payload={
            "chart_palette_preset": "burgundy_luxury",
            "chart_palette_colors": ["#4c0519", "#d4af37", "#166534"],
            "visual_style": "酒红金色，管理层 PDF。",
        },
        auto_start=False,
    )

    workspace = Path(str(manifest["workspace_path"]))
    spec_path = workspace / "report_design_spec.json"

    assert spec_path.exists()
    assert manifest["context_payload"]["report_design_spec_path"] == "report_design_spec.json"
    assert manifest["context_payload"]["chart_palette_colors"] == ["#4c0519", "#d4af37", "#166534"]
    assert manifest["context_payload"]["report_design_spec"]["derived_colors"]["accent"] == "#d4af37"


def test_r_workflow_chart_style_uses_frontend_palette() -> None:
    request = SmartReportRequest(
        chart_palette_preset="navy_gold_boardroom",
        chart_palette_colors=["#4c0519", "#d4af37", "#166534"],
    )

    style = _resolve_r_workflow_chart_style(request)

    assert style["primary"] == "#4c0519"
    assert style["accent"] == "#166534"
    assert style["category_colors"] == ["#4c0519", "#d4af37", "#166534"]


def test_runtime_prompts_reference_report_design_spec() -> None:
    context_payload = {
        "report_design_spec_path": "report_design_spec.json",
        "chart_palette_colors": ["#4c0519", "#d4af37", "#166534"],
    }

    chart_prompt = build_chart_insights_prompt(
        workspace_path="workspace",
        markdown_report_path="05_report.md",
        visual_asset_index_path="source_visual_assets_index.json",
        context_payload=context_payload,
    )
    html_prompt = build_html_css_prompt(
        workspace_path="workspace",
        markdown_report_path="05_report.md",
        chart_insights_path="chart_insights.json",
        context_payload=context_payload,
    )

    assert "Report design spec JSON: report_design_spec.json" in chart_prompt
    assert "chart_palette_colors" in chart_prompt
    assert "Report design spec JSON: report_design_spec.json" in html_prompt
    assert "chart_palette_colors" in html_prompt
    assert "版式名称" in html_prompt
    assert "页面结构" in html_prompt
    assert "表格风格" in html_prompt
    assert "图表风格" in html_prompt
    assert "layout_detail_contract" in html_prompt
    assert "preset_fidelity_contract" in html_prompt
    assert "reference_style_profile" in html_prompt
    assert "preset_design_tokens" in html_prompt
    assert "prohibited_brand_assets" in html_prompt
    assert "visual_signature" in html_prompt
    assert "page_sequence_template" in html_prompt
    assert "component_grammar" in html_prompt
    assert "financial_times_longform" in html_prompt
    assert "salmon/off-white" in html_prompt


def test_specialized_html_prompts_reference_report_design_spec() -> None:
    context_payload = {
        "report_design_spec_path": "report_design_spec.json",
        "chart_palette_colors": ["#4c0519", "#d4af37", "#166534"],
    }

    multi_table_prompt = build_multi_table_html_css_prompt(
        workspace_path="workspace",
        markdown_report_path="08_report.md",
        chart_insights_path="chart_insights.json",
        context_payload=context_payload,
    )
    historical_prompt = build_historical_style_html_css_prompt(
        workspace_path="workspace",
        markdown_report_path="05_historical_style_report.md",
        template_intake_path="01_historical_reverse_spec.json",
        page_plan_path="04_page_plan.json",
        visual_reference_path="historical_visual_reference.json",
        context_payload=context_payload,
    )

    assert "Report design spec JSON: report_design_spec.json" in multi_table_prompt
    assert "chart_palette_colors" in multi_table_prompt
    assert "版式名称" in multi_table_prompt
    assert "页面结构" in multi_table_prompt
    assert "layout_detail_contract" in multi_table_prompt
    assert "preset_fidelity_contract" in multi_table_prompt
    assert "reference_style_profile" in multi_table_prompt
    assert "component_grammar" in multi_table_prompt
    assert "Report design spec JSON: report_design_spec.json" in historical_prompt
    assert "chart_palette_colors" in historical_prompt
    assert "版式名称" in historical_prompt
    assert "layout_detail_contract" in historical_prompt
    assert "preset_fidelity_contract" in historical_prompt
    assert "prohibited_brand_assets" in historical_prompt


def test_ecommerce_html_prompt_uses_chinese_layout_contract() -> None:
    prompt = build_ecommerce_html_css_prompt(
        workspace_path="workspace",
        markdown_report_path="05_report.md",
        chart_insights_path="chart_insights.json",
        context_payload={"report_design_spec_path": "report_design_spec.json"},
        style_preset="category_management_manual",
    )

    assert "Report design spec JSON: report_design_spec.json" in prompt
    assert "版式名称" in prompt
    assert "页面结构" in prompt
    assert "表格风格" in prompt
    assert "图表风格" in prompt
    assert "layout_detail_contract" in prompt
    assert "preset_fidelity_contract" in prompt
    assert "preset_design_tokens" in prompt
    assert "相似度目标" in prompt
    assert "视觉签名" in prompt
    assert "组件语法" in prompt
    assert "style_preset" in prompt
