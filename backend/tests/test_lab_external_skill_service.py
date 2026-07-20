from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd

from app.models import AutoAnalysisRequest
from app.services import lab_external_skill_service as skills
from app.services.auto_analysis_service import run_auto_analysis


def _skill_archive() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("anthropics-skills-main/skills/frontier-brief/SKILL.md", """---
name: Frontier Brief
description: Write concise executive frontier-analysis briefs.
license: Test fixture
---

Use this skill to turn analysis evidence into a concise executive brief.
Always preserve evidence ids and note practical next actions.
""")
        archive.writestr("anthropics-skills-main/skills/frontier-brief/reference.md", "Reference fixture")
    return buffer.getvalue()


def test_external_skill_lifecycle_uses_manifest(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ASTERIA_LAB_EXTERNAL_SKILLS_DIR", str(tmp_path / "skills"))
    monkeypatch.setattr(
        skills,
        "_download_github_archive",
        lambda source_url, ref=None: (_skill_archive(), "anthropics", "skills", ref or "main"),
    )

    installed = skills.install_lab_external_skills("https://github.com/anthropics/skills", mount=True)
    assert installed["installed_count"] == 1
    skill_id = installed["skills"][0]["id"]
    assert skill_id == "anthropics-skills-frontier-brief"
    assert installed["skills"][0]["mounted"] is True

    listed = skills.list_lab_external_skills()
    assert listed["summary"]["mounted_skill_ids"] == [skill_id]
    assert listed["skills"][0]["source_repo"] == "anthropics/skills"
    assert Path(listed["skills"][0]["skill_md_path"]).is_file()

    unmounted = skills.set_lab_external_skill_mounted(skill_id, False)
    assert unmounted["skill"]["mounted"] is False
    assert skills.lab_external_skill_runtime_context()["count"] == 0

    remounted = skills.set_lab_external_skill_mounted(skill_id, True)
    assert remounted["skill"]["mounted"] is True
    runtime_context = skills.lab_external_skill_runtime_context([skill_id])
    assert runtime_context["count"] == 1
    assert runtime_context["skills"][0]["instructions"].startswith("---")
    assert "executive brief" in runtime_context["skills"][0]["instructions"]

    deleted = skills.delete_lab_external_skill(skill_id)
    assert deleted["deleted_skill_id"] == skill_id
    assert skills.list_lab_external_skills()["summary"]["count"] == 0


def test_auto_analysis_exports_mounted_external_skill_context(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ASTERIA_LAB_EXTERNAL_SKILLS_DIR", str(tmp_path / "skills"))
    monkeypatch.setattr(
        skills,
        "_download_github_archive",
        lambda source_url, ref=None: (_skill_archive(), "anthropics", "skills", ref or "main"),
    )
    installed = skills.install_lab_external_skills("https://github.com/anthropics/skills", mount=True)
    skill_id = installed["skills"][0]["id"]

    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d", "e"],
            "revenue": [100, 240, 120, 360, 180],
            "cost": [60, 100, 90, 120, 140],
            "units": [2, 4, 3, 6, 2],
            "channel": ["search", "search", "social", "direct", "social"],
        }
    )
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            report_part="method_note",
            max_methods=2,
            max_derived_fields=8,
            external_skill_ids=[skill_id],
            smart_merge_enabled=False,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
        export_dir=tmp_path / "run",
        public_base_path="/storage/auto-analysis/demo/run-skill",
    )

    runtime_manifest = json.loads((tmp_path / "run" / "runtime_package_manifest.json").read_text(encoding="utf-8"))
    external_skill_context = json.loads((tmp_path / "run" / "external_skill_context.json").read_text(encoding="utf-8"))
    assert result["metrics"]["external_skill_count"] == 1
    assert result["data"]["external_skill_ids"] == [skill_id]
    assert result["data"]["report_part_bundle"]["external_skill_ids"] == [skill_id]
    assert runtime_manifest["external_skill_ids"] == [skill_id]
    assert runtime_manifest["external_skill_context_file"] == "external_skill_context.json"
    assert runtime_manifest["external_skill_application_required"] is True
    assert runtime_manifest["external_skill_context"]["skills"][0]["name"] == "Frontier Brief"
    assert external_skill_context["skill_ids"] == [skill_id]
    assert external_skill_context["skills"][0]["name"] == "Frontier Brief"
    assert external_skill_context["skills"][0]["instructions"].startswith("---")
    assert result["data"]["method_execution_packages"][0]["external_skill_ids"] == [skill_id]
    assert "executive brief" in result["data"]["method_execution_packages"][0]["external_skill_context"]["skills"][0]["instructions"]
    external_skill_download = next(item for item in result["downloadables"] if item["name"] == "external_skill_context.json")
    assert external_skill_download["download_kind"] == "external_skill_context"
    assert external_skill_download["external_skill_ids"] == [skill_id]
    assert external_skill_download["path"] == "/storage/auto-analysis/demo/run-skill/external_skill_context.json"
    assert "file_path" not in external_skill_download


def test_smart_merge_prompt_requires_external_skill_application() -> None:
    from app.services.auto_analysis_service import (
        _ensure_external_skill_applications,
        _smart_merge_fallback_result,
        _smart_merge_prompt,
    )

    prompt = _smart_merge_prompt()
    assert "external_skill_context.skills[].instructions" in prompt
    assert "external_skill_applications" in prompt
    brief = {
        "contract": "analysis_lab_smart_merge_brief_v1",
        "method_threads": [{"method_id": "m1", "method_run_id": "m1__run_1", "result_summary": "ok"}],
        "external_skill_applications_required": True,
        "external_skill_context": {
            "enabled": True,
            "skills": [
                {
                    "id": "anthropics-skills-frontier-brief",
                    "name": "Frontier Brief",
                    "instructions": "Use this skill to turn analysis evidence into a concise executive brief.",
                }
            ],
        },
    }
    fallback = _smart_merge_fallback_result(brief)
    assert fallback["external_skill_applications"][0]["skill_id"] == "anthropics-skills-frontier-brief"
    assert fallback["external_skill_applications"][0]["applied_rules"]
    materialized = _ensure_external_skill_applications({"headline": "runtime result"}, brief)
    assert materialized["external_skill_applications"][0]["name"] == "Frontier Brief"
    assert materialized["external_skill_application_status"] == "materialized_from_context"


def test_smart_merge_materializer_repairs_existing_result_file(tmp_path: Path) -> None:
    from app.services.auto_analysis_service import _materialize_smart_merge_payload

    brief_path = tmp_path / "smart_merge_brief.json"
    result_path = tmp_path / "smart_merge_result.json"
    report_path = tmp_path / "smart_merge_report.md"
    brief_path.write_text(
        json.dumps(
            {
                "contract": "analysis_lab_smart_merge_brief_v1",
                "dataset_name": "demo",
                "sheet_name": "Sheet1",
                "external_skill_applications_required": True,
                "external_skill_context": {
                    "enabled": True,
                    "skills": [
                        {
                            "id": "anthropics-skills-frontier-brief",
                            "name": "Frontier Brief",
                            "instructions": "Use this skill to turn analysis evidence into a concise executive brief.",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    result_path.write_text(
        json.dumps({"headline": "runtime wrote this file", "method_threads": [], "recommended_actions": []}),
        encoding="utf-8",
    )

    assert _materialize_smart_merge_payload(task={}, brief_path=brief_path, result_path=result_path, report_path=report_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["external_skill_applications"][0]["skill_id"] == "anthropics-skills-frontier-brief"
    assert payload["external_skill_application_status"] == "materialized_from_context"
    report_text = report_path.read_text(encoding="utf-8")
    assert "Smart Merge Report" in report_text
    assert "Knowledge Work Report-Flow Applications" in report_text
    assert "Frontier Brief" in report_text
    assert "Selected report-flow functions" in report_text


def test_smart_merge_report_renders_external_skill_applications() -> None:
    from app.services.auto_analysis_service import _smart_merge_markdown_report

    payload = {
        "headline": "Merged report ready",
        "method_threads": [{"method_run_id": "m1__run_1", "contribution": "Trend evidence"}],
        "cross_method_findings": [],
        "conflicts_or_limits": [],
        "recommended_actions": ["Review trend breakpoints."],
        "external_skill_applications": [
            {
                "skill_id": "anthropics-skills-frontier-brief",
                "name": "Frontier Brief",
                "selected_features": [
                    {
                        "feature_kind": "embedded_skill",
                        "feature_id": "frontier-brief",
                        "name": "Frontier Brief",
                    }
                ],
                "applied_rules": [
                    "Use concise executive framing.",
                    "Keep revision guidance explicit.",
                ],
                "output_effect": "Skill guidance shaped the synthesis output.",
                "revision_effect": "Selected functions inform the review plan.",
            }
        ],
    }

    report = _smart_merge_markdown_report(payload, {"dataset_name": "demo", "sheet_name": "Sheet1"})
    assert "Knowledge Work Report-Flow Applications" in report
    assert "### Frontier Brief" in report
    assert "Selected report-flow functions: Frontier Brief" in report
    assert "Applied rules: Use concise executive framing.; Keep revision guidance explicit." in report
    assert "Revision effect: Selected functions inform the review plan." in report


def test_main_lab_report_renders_knowledge_work_report_flow_integration(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ASTERIA_LAB_EXTERNAL_SKILLS_DIR", str(tmp_path / "skills"))
    monkeypatch.setattr(
        skills,
        "_download_github_archive",
        lambda source_url, ref=None: (_skill_archive(), "anthropics", "skills", ref or "main"),
    )
    installed = skills.install_lab_external_skills("https://github.com/anthropics/skills", mount=True)
    skill_id = installed["skills"][0]["id"]

    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d", "e"],
            "revenue": [100, 240, 120, 360, 180],
            "cost": [60, 100, 90, 120, 140],
            "units": [2, 4, 3, 6, 2],
            "channel": ["search", "search", "social", "direct", "social"],
        }
    )
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            report_part="method_note",
            max_methods=2,
            max_derived_fields=8,
            external_skill_ids=[skill_id],
            external_skill_feature_selections=[
                {
                    "plugin_id": skill_id,
                    "feature_kind": "embedded_skill",
                    "feature_id": "frontier-brief",
                    "name": "Frontier Brief",
                }
            ],
            smart_merge_enabled=False,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
        export_dir=tmp_path / "run",
        public_base_path="/storage/auto-analysis/demo/run-skill",
    )

    report_text = (tmp_path / "run" / "lab_report.md").read_text(encoding="utf-8")
    report_writer_input = json.loads((tmp_path / "run" / "report_writer_agent_input.json").read_text(encoding="utf-8"))
    quality_by_id = {
        str(check.get("id") or ""): str(check.get("status") or "")
        for check in result["data"]["lab_report"]["quality_checks"]
        if isinstance(check, dict)
    }

    assert "## Knowledge Work Report-Flow Integration" in report_text
    assert "Selected Knowledge Work plugin functions were applied inside the main Lab report flow" in report_text
    assert "Frontier Brief" in report_text
    assert quality_by_id["mounted_knowledge_work_report_flow"] == "passed"
    assert report_writer_input["report_flow_requirements"][
        "selected_knowledge_work_features_must_participate_in_main_report_flow"
    ] is True
    assert report_writer_input["selected_external_skill_features"][0]["feature_name"] == "Frontier Brief"
