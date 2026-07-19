from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
DOCS_DIR = ROOT / "docs"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def _check(
    checks: list[dict[str, Any]],
    requirement: str,
    passed: bool,
    evidence: str,
    artifact: str,
) -> None:
    checks.append(
        {
            "requirement": requirement,
            "passed": bool(passed),
            "evidence": evidence,
            "artifact": artifact,
        }
    )


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Report Preset Quality Verification",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Overall passed: {report['overall_passed']}",
        f"- Default layout preset: {report['default_layout_preset']}",
        f"- Default chart palette: {report['default_chart_palette']}",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
    ]
    for item in report["checks"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.extend(
            [
                f"- {mark}: {item['requirement']}",
                f"  Evidence: {item['evidence']}",
                f"  Artifact: `{item['artifact']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Generated Spec Snapshot",
            "",
            f"- 版式名称: {report['spec_snapshot']['layout_name']}",
            f"- 字体气质: {report['spec_snapshot']['typography_direction']}",
            f"- 文风预设: {report['spec_snapshot']['writing_preset']}",
            f"- 视觉签名: {', '.join(report['spec_snapshot']['visual_signature'])}",
            f"- 专属设计令牌: {json.dumps(report['spec_snapshot']['design_tokens'], ensure_ascii=False, sort_keys=True)}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    from app.services.report_design_spec_service import (
        DEFAULT_LAYOUT_PRESET_ID,
        build_report_design_spec,
        render_report_design_spec_markdown,
    )

    spec = build_report_design_spec()
    spec_markdown = render_report_design_spec_markdown(spec)
    checks: list[dict[str, Any]] = []

    report_design_source = _read_text(BACKEND_DIR / "app" / "services" / "report_design_spec_service.py")
    prompt_source = _read_text(BACKEND_DIR / "app" / "services" / "codex_runtime_prompt_templates.py")
    pipeline_source = _read_text(BACKEND_DIR / "app" / "services" / "codex_runtime_pipeline_service.py")
    models_source = _read_text(BACKEND_DIR / "app" / "models.py")
    frontend_source = _read_text(ROOT / "frontend" / "src" / "components" / "smart-report-studio.tsx")

    design_tokens = dict(spec.get("preset_design_tokens") or {})
    writing_contract = dict(spec.get("writing_style_contract") or {})
    visual_signature = list(spec.get("visual_signature") or [])
    chart_palette = list(spec.get("chart_palette_colors") or [])
    page_sequence = list(spec.get("page_sequence_template") or [])
    component_grammar = list(spec.get("component_grammar") or [])

    _check(
        checks,
        "默认整体报告预设必须是中文财经内参，而不是旧深蓝/FT 模板。",
        DEFAULT_LAYOUT_PRESET_ID == "chinese_finance_editorial"
        and spec.get("layout_preset_id") == "chinese_finance_editorial"
        and spec.get("layout_preset_name") == "中文财经内参",
        f"DEFAULT_LAYOUT_PRESET_ID={DEFAULT_LAYOUT_PRESET_ID}, layout_preset_name={spec.get('layout_preset_name')}",
        "backend/app/services/report_design_spec_service.py",
    )
    _check(
        checks,
        "字体预设必须明确中文 serif 标题、无衬线正文和 tabular 数字。",
        _contains_all(str(spec.get("typography_direction") or ""), ["Serif", "Noto", "tabular"])
        and _contains_all(report_design_source, ["Source Han Serif", "Noto Serif", "tabular-nums"]),
        str(spec.get("typography_direction") or ""),
        "report_design_spec.json / backend/app/services/report_design_spec_service.py",
    )
    _check(
        checks,
        "配色必须使用低饱和中文内参墨色，并包含 teal、oxblood、brass 角色。",
        spec.get("chart_palette_preset") == "cn_editorial_ink"
        and chart_palette[:4] == ["#17191c", "#214a4f", "#8f2f31", "#b08a57"]
        and all(key in design_tokens for key in ["paper", "ink", "accent", "secondary_accent", "signal"]),
        f"chart_palette_preset={spec.get('chart_palette_preset')}, colors={chart_palette[:6]}",
        "report_design_spec.json / frontend/src/components/smart-report-studio.tsx",
    )
    _check(
        checks,
        "排版层级必须覆盖封面判断、硬数字、证据边栏、exhibit、行动闭环和附录。",
        all(
            any(keyword in str(item) for item in page_sequence + component_grammar + visual_signature)
            for keyword in ["判断", "硬数字", "证据", "exhibit", "行动", "附录"]
        ),
        f"page_sequence={page_sequence}; component_grammar={component_grammar}; visual_signature={visual_signature}",
        "report_design_spec.json",
    )
    _check(
        checks,
        "文风预设必须是判断先行中文财经内参，并约束标题、段落节奏、必须使用和禁止风格。",
        writing_contract.get("preset_name") == "判断先行中文财经内参"
        and _contains_all(json.dumps(writing_contract, ensure_ascii=False), ["判断", "证据", "含义", "动作", "空泛"]),
        json.dumps(writing_contract, ensure_ascii=False),
        "report_design_spec.json / report_design_spec.md",
    )
    _check(
        checks,
        "Markdown 规格必须暴露字体、文风、版式名称和图表色卡，供运行时 prompt 阅读。",
        _contains_all(spec_markdown, ["版式名称：中文财经内参", "字体气质：", "文风预设：", "图表预设：cn_editorial_ink"]),
        "render_report_design_spec_markdown contains required reader-facing fields.",
        "backend/app/services/report_design_spec_service.py",
    )
    _check(
        checks,
        "HTML/CSS prompt 必须要求读取 writing_style_contract / 文风预设并按判断->证据->含义->动作执行。",
        _contains_all(prompt_source, ["writing_style_contract", "文风预设", "judgement -> evidence -> implication -> action/boundary"]),
        "codex runtime prompt source includes writing-style contract instructions.",
        "backend/app/services/codex_runtime_prompt_templates.py",
    )
    _check(
        checks,
        "确定性 CSS fallback 必须有 A4、中文 serif 标题、细线表格和低饱和纸面。",
        _contains_all(pipeline_source, ["@page { size: A4", "Noto Serif CJK SC", "border-top: 5px solid", "thead { display: table-header-group; }"]),
        "generic deterministic CSS contains print and editorial hierarchy rules.",
        "backend/app/services/codex_runtime_pipeline_service.py",
    )
    _check(
        checks,
        "API/request 默认值必须把 style_preset 设为 chinese_finance_editorial。",
        'style_preset: str = "chinese_finance_editorial"' in models_source
        and 'premium_style_preset: str = "chinese_finance_editorial"' in models_source,
        "SmartReportRequest and CodexRunRequest default to chinese_finance_editorial.",
        "backend/app/models.py",
    )
    _check(
        checks,
        "前端默认选择必须展示中文财经内参、中文内参墨色和文风预览。",
        _contains_all(frontend_source, ['"chinese_finance_editorial"', '"cn_editorial_ink"', "中文财经内参", "中文内参墨色", "文风"]),
        "SmartReportStudio contains default layout, palette, and writing preview labels.",
        "frontend/src/components/smart-report-studio.tsx",
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_passed": all(item["passed"] for item in checks),
        "default_layout_preset": spec.get("layout_preset_id"),
        "default_chart_palette": spec.get("chart_palette_preset"),
        "checks": checks,
        "spec_snapshot": {
            "layout_name": spec.get("layout_preset_name"),
            "typography_direction": spec.get("typography_direction"),
            "writing_preset": writing_contract.get("preset_name"),
            "visual_signature": visual_signature,
            "design_tokens": design_tokens,
        },
    }

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DOCS_DIR / "report_preset_quality_verification.json"
    md_path = DOCS_DIR / "report_preset_quality_verification.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report) + "\n", encoding="utf-8")
    print(json.dumps({"overall_passed": report["overall_passed"], "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False))
    return 0 if report["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
