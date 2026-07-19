from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.services.codex_runtime_pipeline_service import (
    create_pipeline_job,
    get_pipeline_job,
    run_pipeline_job_to_completion,
)
from app.services.codex_runtime_pipeline_store import update_pipeline_manifest
from app.services.codex_historical_collage_asset_service import build_historical_collage_source
from app.services.codex_historical_data_context_service import write_historical_data_snapshot
from app.services.codex_historical_logic_reference_service import write_historical_logic_reference
from app.services.codex_historical_table_asset_service import build_historical_support_tables
from app.services.codex_historical_visual_reference_service import write_historical_visual_reference
from app.services.codex_historical_visual_reverse_v2_service import write_historical_visual_reverse_spec_v2
from app.services.codex_historical_chart_grammar_service import write_historical_chart_grammar_spec
from app.services.codex_service import codex_historical_report_adaptation
from app.services.settings_service import load_runtime_settings_raw


_COMPATIBILITY_KEYS = {
    "mode",
    "reason",
    "title",
    "source_name",
    "template_signals",
    "adaptation_notes",
    "adapted_report_markdown",
    "model",
    "provider_label",
    "reasoning_effort",
}


def _safe_suffix(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix else ".txt"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _pd() -> Any:
    import pandas as pd

    return pd


def _extract_historical_source_text(source_path: str, *, limit_chars: int = 80000) -> str:
    """Best-effort text extraction so a real historical PDF can be the only source input."""
    source = Path(str(source_path or "")).expanduser()
    if not source.exists() or not source.is_file():
        return ""
    suffix = source.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            return source.read_text(encoding="utf-8-sig", errors="ignore").strip()[:limit_chars]
        if suffix in {".html", ".htm"}:
            raw = source.read_text(encoding="utf-8-sig", errors="ignore")
            return raw.strip()[:limit_chars]
        if suffix == ".pdf":
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(source))
            parts: list[str] = []
            for page in reader.pages[:80]:
                parts.append(page.extract_text() or "")
            return "\n".join(parts).strip()[:limit_chars]
        if suffix == ".docx":
            from docx import Document  # type: ignore

            document = Document(str(source))
            return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()[:limit_chars]
    except Exception:
        return ""
    return ""


def _pdf_page_count(pdf_path: Path) -> int:
    if pdf_path.suffix.lower() != ".pdf" or not pdf_path.exists():
        return 0
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return 0


def _clean_lines(values: list[Any] | None, *, limit: int = 12) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if not text:
            continue
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _section_summaries_payload(section_summaries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for section in section_summaries or []:
        if not isinstance(section, dict):
            continue
        payload.append(
            {
                "title": str(section.get("title") or "").strip(),
                "summary": str(section.get("summary") or "").strip(),
                "bullets": _clean_lines(list(section.get("bullets") or []), limit=6),
            }
        )
        if len(payload) >= 16:
            break
    return payload


def _build_fallback_context(
    *,
    dataset_name: str,
    sheet_name: str,
    historical_report_name: str,
    historical_report_text: str,
    executive_summary: list[str] | None,
    section_summaries: list[dict[str, Any]] | None,
    market_summary: list[str] | None,
    semantic_summary: list[str] | None,
    mounted_skills: list[Any] | None,
    writer_agent_candidates: list[Any] | None,
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "historical_report_name": historical_report_name or "历史报告样例",
        "historical_report_text": historical_report_text,
        "mounted_skills": list(mounted_skills or []),
        "writer_agent_candidates": list(writer_agent_candidates or []),
        "executive_summary": _clean_lines(executive_summary, limit=8),
        "section_summaries": _section_summaries_payload(section_summaries),
        "market_summary": _clean_lines(market_summary, limit=8),
        "semantic_summary": _clean_lines(semantic_summary, limit=8),
    }


def _compatibility_payload(raw_payload: dict[str, Any], *, markdown_text: str = "") -> dict[str, Any]:
    payload = {key: raw_payload.get(key) for key in _COMPATIBILITY_KEYS if key in raw_payload}
    payload.setdefault("mode", "codex_cli_pipeline")
    payload.setdefault("reason", "")
    payload.setdefault("title", str(raw_payload.get("title") or "历史报告风格改写"))
    payload.setdefault("source_name", str(raw_payload.get("source_name") or "历史报告样例"))
    payload["template_signals"] = _clean_lines(list(raw_payload.get("template_signals") or []), limit=8)
    payload["adaptation_notes"] = _clean_lines(list(raw_payload.get("adaptation_notes") or []), limit=8)
    payload["adapted_report_markdown"] = str(
        markdown_text or raw_payload.get("adapted_report_markdown") or ""
    ).strip()
    return payload


def _copy_historical_source_to_workspace(
    *,
    workspace: Path,
    source_path: str,
    historical_text: str,
) -> Path:
    source = Path(str(source_path or "")).expanduser()
    if source_path and source.exists() and source.is_file():
        target = workspace / f"historical_report_source{_safe_suffix(source)}"
        target.write_bytes(source.read_bytes())
        return target
    target = workspace / "historical_report_source.md"
    target.write_text(historical_text, encoding="utf-8")
    return target


def _render_pdf_previews(pdf_path: Path, output_dir: Path, *, max_pages: int = 4) -> list[str]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"
    try:
        subprocess.run(
            [
                pdftoppm,
                "-f",
                "1",
                "-l",
                str(max_pages),
                "-png",
                str(pdf_path),
                str(prefix),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []
    return [str(path.resolve()) for path in sorted(output_dir.glob("page-*.png"))[:max_pages]]


def _build_visual_reference_payload(
    *,
    source_path: Path,
    preview_paths: list[str],
) -> dict[str, Any]:
    suffix = source_path.suffix.lower()
    page_count = _pdf_page_count(source_path)
    if suffix == ".pdf":
        suggested_visual_system = [
            "This is a real historical PDF source; reverse the rendered PDF previews and source text before deciding the page system.",
            "Corporate presentation-style report rather than plain text document layout.",
            "Cover should use bold blue brand-color geometry with a large clean title block.",
            "Content pages should use white background, strong blue section headers, and generous whitespace.",
            "Use a brand-signature zone in the top-right only when approved assets exist in the current workspace.",
            "Footer rhythm should reserve left-side source text and right-side page number.",
            "Charts and screenshots should sit inside clean framed modules rather than dense dashboard dumps.",
        ]
    else:
        suggested_visual_system = [
            "Use the historical source as a corporate layout reference rather than a plain text template.",
            "Preserve strong section hierarchy, spacious layout, and presentation-grade framing.",
        ]
    return {
        "source_name": source_path.name,
        "source_suffix": suffix or ".txt",
        "source_is_real_pdf": suffix == ".pdf",
        "source_page_count": page_count,
        "preview_page_count": len(preview_paths),
        "visual_reverse_source": "rendered_pdf_previews" if suffix == ".pdf" else "source_document",
        "preview_image_paths": preview_paths,
        "dominant_palette_hint": ["#1d8bc8", "#ffffff", "#63bf43"],
        "visual_style_tokens": [
            "corporate_blue_white",
            "presentation_report",
            "clean_module_layout",
            "section_header_bar",
            "footer_source_plus_page_number",
        ],
        "suggested_visual_system": suggested_visual_system,
    }


def _run_fallback_adaptation(
    *,
    fallback_context: dict[str, Any],
    pipeline_job_id: str = "",
    pipeline_manifest: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    fallback = codex_historical_report_adaptation(fallback_context)
    payload = _compatibility_payload(fallback)
    if error:
        payload["reason"] = str(error)
    payload["pipeline_job_id"] = pipeline_job_id
    payload["pipeline_status"] = str((pipeline_manifest or {}).get("status") or "")
    payload["pipeline_manifest"] = dict(pipeline_manifest or {})
    payload["pipeline_final_output"] = dict((pipeline_manifest or {}).get("final_output") or {})
    return payload


def run_historical_style_cli_adaptation(
    *,
    report_dir: Path,
    report_id: str,
    dataset_name: str,
    sheet_name: str,
    historical_report_name: str,
    historical_report_text: str,
    executive_summary: list[str] | None,
    section_summaries: list[dict[str, Any]] | None,
    market_summary: list[str] | None = None,
    semantic_summary: list[str] | None = None,
    user_requirement: str = "",
    target_audience: str = "",
    core_purpose: str = "",
    business_background_text: str = "",
    historical_report_source_path: str = "",
    chart_bundle: dict[str, Any] | None = None,
    column_summaries: list[dict[str, Any]] | None = None,
    support_tables: dict[str, Any] | None = None,
    data_frames: dict[str, Any] | None = None,
    data_frame: Any | None = None,
    analysis_package_context: dict[str, Any] | None = None,
    target_page_count_min: int = 16,
    target_page_count_max: int = 28,
    mounted_skills: list[Any] | None = None,
    writer_agent_candidates: list[Any] | None = None,
    parent_report_job_id: str = "",
    language: str = "zh-CN",
) -> dict[str, Any]:
    """Run historical report imitation through a dedicated Codex CLI pipeline."""
    historical_text = str(historical_report_text or "").strip()
    historical_text_source = "request_payload"
    if not historical_text and historical_report_source_path:
        historical_text = _extract_historical_source_text(historical_report_source_path)
        historical_text_source = "source_file_extraction" if historical_text else "source_file_visual_only"
    if not historical_text and historical_report_source_path:
        source_name = Path(str(historical_report_source_path or "")).name
        historical_text = (
            f"Historical report source file: {source_name}\n\n"
            "Readable text extraction was unavailable or empty. Treat the copied source file and rendered "
            "PDF previews in this workspace as the primary reverse-spec input. Reverse the visual system, "
            "page taxonomy, page furniture, chart/table/collage grammar, and appendix rhythm from those files."
        )
    if not historical_text:
        return {}

    fallback_context = _build_fallback_context(
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        historical_report_name=historical_report_name,
        historical_report_text=historical_text,
        executive_summary=executive_summary,
        section_summaries=section_summaries,
        market_summary=market_summary,
        semantic_summary=semantic_summary,
        mounted_skills=mounted_skills,
        writer_agent_candidates=writer_agent_candidates,
    )
    settings = load_runtime_settings_raw()
    if not bool(settings.get("codex_runtime_enabled", False)):
        return _run_fallback_adaptation(
            fallback_context=fallback_context,
            error="historical_style_cli_pipeline_unavailable: codex_runtime_disabled",
        )

    pipeline_manifest: dict[str, Any] = {}
    pipeline_job_id = ""
    try:
        analysis_package_context = dict(analysis_package_context or {})
        context_payload = {
            "language": language,
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "historical_report_name": historical_report_name or "历史报告样例",
            "historical_report_source_path": "",
            "historical_report_text_source": historical_text_source,
            "historical_report_text_excerpt_path": "historical_report_text_excerpt.md",
            "current_report_context_path": "current_report_context.json",
            "historical_visual_reference_path": "historical_visual_reference.json",
            "report_goal": "historical_style_adaptation",
            "analysis_mode": "historical_style_report_cli_pipeline",
            "target_audience": target_audience or "management",
            "user_requirement": user_requirement,
            "core_purpose": core_purpose,
            "business_background_text": str(business_background_text or "")[:4000],
            "parent_report_job_id": parent_report_job_id,
            "target_page_count_min": int(target_page_count_min),
            "target_page_count_max": int(target_page_count_max),
        }
        pipeline_manifest = create_pipeline_job(
            pipeline_type="historical_style_report_cli_pipeline",
            workspace_path=str(report_dir / "codex_premium" / "historical_style" / "{pipeline_job_id}"),
            linked_report_id=report_id,
            context_payload=context_payload,
            auto_start=False,
        )
        pipeline_job_id = str(pipeline_manifest.get("pipeline_job_id") or "")
        workspace = Path(str(pipeline_manifest.get("workspace_path") or "")).expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        text_excerpt = historical_text[:30000].strip()
        _write_text(workspace / "historical_report_text_excerpt.md", text_excerpt)
        effective_data_frame = data_frame
        if effective_data_frame is None and isinstance(data_frames, dict):
            ranked_frames = [
                (int(len(frame)), str(table_id), frame)
                for table_id, frame in data_frames.items()
                if frame is not None and hasattr(frame, "columns")
            ]
            if ranked_frames:
                ranked_frames.sort(key=lambda item: (item[0], item[1]), reverse=True)
                effective_data_frame = ranked_frames[0][2]
                analysis_package_context.setdefault("table_ids", [item[1] for item in ranked_frames])
                analysis_package_context.setdefault("primary_table_id", ranked_frames[0][1])
        data_snapshot_name = write_historical_data_snapshot(workspace, effective_data_frame)
        context_payload["historical_data_snapshot_path"] = data_snapshot_name
        historical_source_file = _copy_historical_source_to_workspace(
            workspace=workspace,
            source_path=historical_report_source_path,
            historical_text=historical_text,
        )
        logic_reference_payload = write_historical_logic_reference(
            source_path=historical_source_file,
            historical_text=historical_text,
            output_path=workspace / "historical_logic_reference.json",
            markdown_output_path=workspace / "historical_logic_reference.md",
        )
        preview_paths = (
            _render_pdf_previews(historical_source_file, workspace / "historical_visual_previews")
            if historical_source_file.suffix.lower() == ".pdf"
            else []
        )
        visual_reference_payload = write_historical_visual_reference(
            source_path=historical_source_file,
            preview_paths=preview_paths,
            output_path=workspace / "historical_visual_reference.json",
        )
        visual_reverse_v2_payload = write_historical_visual_reverse_spec_v2(
            workspace=workspace,
            visual_reference_path=workspace / "historical_visual_reference.json",
            preview_paths=preview_paths,
            output_path=workspace / "historical_visual_reverse_spec_v2.json",
        )
        chart_grammar_payload = write_historical_chart_grammar_spec(
            workspace=workspace,
            visual_reference_path=workspace / "historical_visual_reference.json",
            visual_reverse_spec_v2_path=workspace / "historical_visual_reverse_spec_v2.json",
            output_path=workspace / "historical_chart_grammar_spec.json",
        )
        context_payload["historical_report_source_path"] = historical_source_file.name
        context_payload["historical_source_is_real_pdf"] = bool(visual_reference_payload.get("source_is_real_pdf"))
        context_payload["historical_source_page_count"] = int(visual_reference_payload.get("source_page_count") or 0)
        context_payload["historical_visual_preview_count"] = int(visual_reference_payload.get("preview_page_count") or 0)
        context_payload["historical_report_family_hint"] = str(visual_reference_payload.get("historical_report_family_hint") or "")
        context_payload["historical_logic_reference_path"] = "historical_logic_reference.json"
        context_payload["historical_visual_reverse_spec_v2_path"] = "historical_visual_reverse_spec_v2.json"
        context_payload["historical_chart_grammar_spec_path"] = "historical_chart_grammar_spec.json"
        context_payload["historical_logic_pattern"] = str(logic_reference_payload.get("dominant_logic_pattern") or "")
        context_payload["historical_logic_available"] = bool(logic_reference_payload.get("available"))
        _write_json(workspace / "historical_chart_bundle.json", dict(chart_bundle or {}))
        context_payload["historical_chart_bundle_path"] = "historical_chart_bundle.json"
        support_tables_payload = dict(support_tables or {})
        if not support_tables_payload and (chart_bundle or column_summaries):
            pd = _pd()
            support_tables_payload = build_historical_support_tables(
                pd.DataFrame(),
                chart_bundle=chart_bundle,
                column_summaries=column_summaries,
            )
        _write_json(workspace / "historical_support_tables.json", support_tables_payload)
        context_payload["historical_support_tables_path"] = "historical_support_tables.json"
        current_report_context_payload = {
                "dataset_name": dataset_name,
                "sheet_name": sheet_name,
                "historical_report_source_name": historical_source_file.name,
                "historical_report_text_source": historical_text_source,
                "historical_source_is_real_pdf": context_payload["historical_source_is_real_pdf"],
                "historical_source_page_count": context_payload["historical_source_page_count"],
                "historical_visual_preview_count": context_payload["historical_visual_preview_count"],
                "historical_data_snapshot_path": data_snapshot_name,
                "historical_report_text_excerpt_path": "historical_report_text_excerpt.md",
                "historical_report_text_excerpt_chars": len(text_excerpt),
                "historical_logic_reference_path": "historical_logic_reference.json",
                "historical_logic_reference": logic_reference_payload,
                "historical_report_name": historical_report_name or "历史报告样例",
                "user_requirement": user_requirement,
                "target_audience": target_audience,
                "core_purpose": core_purpose,
                "business_background_text": str(business_background_text or "")[:4000],
                "target_page_count_min": int(target_page_count_min),
                "target_page_count_max": int(target_page_count_max),
                "executive_summary": _clean_lines(executive_summary, limit=10),
                "section_summaries": _section_summaries_payload(section_summaries),
                "market_summary": _clean_lines(market_summary, limit=8),
                "semantic_summary": _clean_lines(semantic_summary, limit=8),
                "chart_bundle": dict(chart_bundle or {}),
                "column_summaries": list(column_summaries or [])[:24],
                "support_tables": support_tables_payload,
                "analysis_package_context": analysis_package_context,
                "writer_agent_candidates": list(writer_agent_candidates or []),
                "mounted_skills": list(mounted_skills or []),
                "historical_visual_reference": visual_reference_payload,
                "historical_visual_reverse_spec_v2": visual_reverse_v2_payload,
                "historical_chart_grammar_spec": chart_grammar_payload,
        }
        _write_json(workspace / "current_report_context.json", current_report_context_payload)
        collage_source_payload = build_historical_collage_source(
            current_report_context=current_report_context_payload,
            support_tables=support_tables_payload,
            visual_reference=visual_reference_payload,
        )
        _write_json(workspace / "historical_collage_source.json", collage_source_payload)
        context_payload["historical_collage_source_path"] = "historical_collage_source.json"
        pipeline_manifest = update_pipeline_manifest(
            pipeline_job_id,
            {
                "context_payload": {
                    **dict(pipeline_manifest.get("context_payload") or {}),
                    **context_payload,
                }
            },
        )
        pipeline = run_pipeline_job_to_completion(pipeline_job_id)
        if str(pipeline.get("status") or "") != "completed":
            return _run_fallback_adaptation(
                fallback_context=fallback_context,
                pipeline_job_id=pipeline_job_id,
                pipeline_manifest=pipeline,
                error=f"historical_style_cli_pipeline_failed: {pipeline.get('error') or 'pipeline did not complete'}",
            )

        markdown_path = workspace / "05_historical_style_report.md"
        json_path = workspace / "05_historical_style_report.json"
        markdown_text = markdown_path.read_text(encoding="utf-8-sig")
        pipeline_payload = json.loads(json_path.read_text(encoding="utf-8-sig"))
        if not isinstance(pipeline_payload, dict):
            raise ValueError("historical_style_cli_pipeline JSON output must be an object.")

        result = _compatibility_payload(pipeline_payload, markdown_text=markdown_text)
        result.update(
            {
                "mode": "codex_cli_pipeline",
                "provider_label": "Codex CLI Runtime",
                "model": str(settings.get("model") or "gpt-5.4"),
                "reasoning_effort": str(settings.get("reasoning_effort") or ""),
                "pipeline_job_id": pipeline_job_id,
                "pipeline_status": str(pipeline.get("status") or ""),
                "pipeline_manifest": pipeline,
                "pipeline_final_output": dict(pipeline.get("final_output") or {}),
            }
        )
        return result
    except Exception as exc:
        latest_pipeline: dict[str, Any] = {}
        if pipeline_job_id:
            try:
                latest_pipeline = get_pipeline_job(pipeline_job_id)
            except Exception:
                latest_pipeline = dict(pipeline_manifest or {})
        return _run_fallback_adaptation(
            fallback_context=fallback_context,
            pipeline_job_id=pipeline_job_id,
            pipeline_manifest=latest_pipeline,
            error=f"historical_style_cli_pipeline_error: {exc}",
        )
