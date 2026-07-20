from __future__ import annotations

import copy
import sys
import types
from pathlib import Path

import pytest

from app.services import runtime_process_service as runtime_service_module


@pytest.fixture
def isolated_runtime_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(runtime_service_module, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime_service_module, "TASK_DIR", tmp_path / "runs" / "report_tasks")
    monkeypatch.setattr(runtime_service_module, "CODEX_RUNTIME_TASKS_DIR", tmp_path / "runs" / "codex_tasks")
    monkeypatch.setattr(runtime_service_module, "CODEX_PIPELINE_JOBS_DIR", tmp_path / "runs" / "codex_pipeline_jobs")
    return reports_dir


def _seed_report_dir(reports_dir: Path, report_id: str) -> Path:
    report_dir = reports_dir / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def test_resume_runtime_process_retries_stale_pipeline(
    isolated_runtime_paths: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_id = "resume-stale-001"
    _seed_report_dir(isolated_runtime_paths, report_id)
    pipeline_job_id = "pipeline-stale-001"
    manifest_state = {
        "pipeline_job_id": pipeline_job_id,
        "pipeline_type": "generic_long_cli_pipeline",
        "status": "running",
        "linked_report_id": report_id,
        "workspace_path": str((isolated_runtime_paths / f"smart-report-{report_id}" / "workspace").resolve()),
        "current_stage_id": "review",
        "current_stage_title": "Review",
        "stage_order": [{"stage_id": "review"}],
        "result_summary": {},
    }
    retry_calls: list[dict[str, object]] = []
    update_calls: list[dict[str, object]] = []

    def fake_read_pipeline_manifest(process_id: str) -> dict[str, object]:
        assert process_id == pipeline_job_id
        return copy.deepcopy(manifest_state)

    def fake_update_pipeline_manifest(process_id: str, payload: dict[str, object]) -> dict[str, object]:
        assert process_id == pipeline_job_id
        nonlocal manifest_state
        merged = copy.deepcopy(manifest_state)
        for key, value in payload.items():
            if key == "result_summary":
                merged[key] = {**dict(merged.get(key) or {}), **dict(value or {})}
            else:
                merged[key] = value
        manifest_state = merged
        update_calls.append(copy.deepcopy(payload))
        return copy.deepcopy(manifest_state)

    def fake_pipeline_runtime_observation(manifest: dict[str, object]) -> dict[str, object]:
        status = str(manifest.get("status") or "")
        if status == "running":
            return {
                "is_stale": True,
                "stale_reason": "pipeline_has_no_live_codex_task_evidence_1200s_gt_600s",
                "observed_status": "stale_running",
            }
        return {"is_stale": False, "stale_reason": "", "observed_status": status}

    def fake_preflight(manifest: dict[str, object], *, repair: bool = False) -> dict[str, object]:
        assert repair is True
        assert str(manifest.get("status") or "") == "failed"
        return {
            "resume_strategy": "retry_current_stage",
            "retry_stage_id": "review",
            "blocking_missing_inputs": [],
        }

    def fake_retry_pipeline_stage(process_id: str, *, stage_id: str, auto_start: bool = True, auto_retry: bool = False) -> dict[str, object]:
        retry_calls.append(
            {
                "process_id": process_id,
                "stage_id": stage_id,
                "auto_start": auto_start,
                "auto_retry": auto_retry,
            }
        )
        return {
            "pipeline_job_id": process_id,
            "pipeline_type": "generic_long_cli_pipeline",
            "workspace_path": str((isolated_runtime_paths / "retries" / process_id).resolve()),
        }

    monkeypatch.setattr(runtime_service_module, "read_pipeline_manifest", fake_read_pipeline_manifest)
    monkeypatch.setattr(runtime_service_module, "update_pipeline_manifest", fake_update_pipeline_manifest)
    monkeypatch.setattr(runtime_service_module, "_pipeline_runtime_observation", fake_pipeline_runtime_observation)
    monkeypatch.setattr(runtime_service_module, "_pipeline_resume_preflight", fake_preflight)
    monkeypatch.setattr(
        runtime_service_module,
        "list_runtime_processes",
        lambda report_id, session_id="": {"report_id": report_id, "processes": []},
    )
    fake_pipeline_module = types.ModuleType("app.services.codex_runtime_pipeline_service")
    fake_pipeline_module.retry_pipeline_stage = fake_retry_pipeline_stage
    monkeypatch.setitem(sys.modules, "app.services.codex_runtime_pipeline_service", fake_pipeline_module)

    response = runtime_service_module.resume_runtime_process("pipeline", pipeline_job_id, report_id=report_id)

    assert response["action"] == "resume"
    assert response["retry_stage_id"] == "review"
    assert response["resume_strategy"] == "retry_current_stage"
    assert retry_calls == [
        {
            "process_id": pipeline_job_id,
            "stage_id": "review",
            "auto_start": True,
            "auto_retry": False,
        }
    ]
    assert manifest_state["status"] == "failed"
    assert "Runtime resume marked stale pipeline as failed for safe retry" in str(manifest_state["error"])
    assert manifest_state["result_summary"]["stale_recovered_from_status"] == "running"
    assert manifest_state["result_summary"]["stale_recovered_stage_id"] == "review"
    assert manifest_state["result_summary"]["stale_recovery_reason"] == "pipeline_has_no_live_codex_task_evidence_1200s_gt_600s"
    assert any("current_stage_detail" in payload for payload in update_calls)


def test_resume_runtime_process_returns_blocked_payload_for_missing_inputs(
    isolated_runtime_paths: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_id = "resume-blocked-001"
    _seed_report_dir(isolated_runtime_paths, report_id)
    pipeline_job_id = "pipeline-blocked-001"
    manifest = {
        "pipeline_job_id": pipeline_job_id,
        "pipeline_type": "generic_long_cli_pipeline",
        "status": "failed",
        "linked_report_id": report_id,
        "workspace_path": str((isolated_runtime_paths / f"smart-report-{report_id}" / "workspace").resolve()),
        "current_stage_id": "review",
        "current_stage_title": "Review",
        "stage_order": [{"stage_id": "review"}],
    }

    monkeypatch.setattr(runtime_service_module, "read_pipeline_manifest", lambda _process_id: copy.deepcopy(manifest))
    monkeypatch.setattr(
        runtime_service_module,
        "_pipeline_runtime_observation",
        lambda _manifest: {"is_stale": False, "stale_reason": "", "observed_status": "failed"},
    )
    monkeypatch.setattr(
        runtime_service_module,
        "_pipeline_resume_preflight",
        lambda _manifest, *, repair=False: {
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "missing_reader_required_top12_combo_table",
            "repair_rule_id": "internet_ops_top12_combo_table",
            "retry_stage_id": "ops_chart_insights",
            "blocking_missing_inputs": ["source_visual_assets/ops_channel_source_aarrr_topn_small_multiples.csv"],
        },
    )
    monkeypatch.setattr(
        runtime_service_module,
        "list_runtime_processes",
        lambda report_id, session_id="": {"report_id": report_id, "processes": []},
    )

    response = runtime_service_module.resume_runtime_process("pipeline", pipeline_job_id, report_id=report_id)

    assert response["action"] == "resume_blocked"
    assert response["resume_strategy"] == "blocked_missing_inputs"
    assert response["resume_issue_kind"] == "missing_reader_required_top12_combo_table"
    assert response["repair_rule_id"] == "internet_ops_top12_combo_table"
    assert response["retry_stage_id"] == "ops_chart_insights"
    assert response["blocking_missing_inputs"] == ["source_visual_assets/ops_channel_source_aarrr_topn_small_multiples.csv"]
    assert response["result"]["resume_strategy"] == "blocked_missing_inputs"


def test_resume_runtime_process_rebuilds_workspace_and_restarts_pipeline(
    isolated_runtime_paths: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_id = "resume-rebuild-001"
    _seed_report_dir(isolated_runtime_paths, report_id)
    pipeline_job_id = "pipeline-rebuild-001"
    manifest = {
        "pipeline_job_id": pipeline_job_id,
        "pipeline_type": "generic_long_cli_pipeline",
        "status": "failed",
        "linked_report_id": report_id,
        "workspace_path": str((isolated_runtime_paths / f"smart-report-{report_id}" / "workspace").resolve()),
        "current_stage_id": "review",
        "current_stage_title": "Review",
        "stage_order": [{"stage_id": "review"}],
    }
    start_calls: list[dict[str, object]] = []

    def fake_create_generic_long_cli_pipeline_from_completed_report(target_report_id: str, *, auto_start: bool = True) -> dict[str, object]:
        start_calls.append({"report_id": target_report_id, "auto_start": auto_start})
        return {
            "pipeline_job_id": "pipeline-restarted-001",
            "pipeline_type": "generic_long_cli_pipeline",
            "workspace_path": str((isolated_runtime_paths / f"smart-report-{target_report_id}" / "codex_runtime_rebuild").resolve()),
        }

    monkeypatch.setattr(runtime_service_module, "read_pipeline_manifest", lambda _process_id: copy.deepcopy(manifest))
    monkeypatch.setattr(
        runtime_service_module,
        "_pipeline_runtime_observation",
        lambda _manifest: {"is_stale": False, "stale_reason": "", "observed_status": "failed"},
    )
    monkeypatch.setattr(
        runtime_service_module,
        "_pipeline_resume_preflight",
        lambda _manifest, *, repair=False: {
            "resume_strategy": "rebuild_workspace_then_restart_pipeline",
            "resume_issue_kind": "missing_pipeline_workspace",
            "workspace_rebuild_path": str((isolated_runtime_paths / f"smart-report-{report_id}" / "codex_runtime_rebuild").resolve()),
            "blocking_missing_inputs": [],
        },
    )
    monkeypatch.setattr(
        runtime_service_module,
        "list_runtime_processes",
        lambda report_id, session_id="": {"report_id": report_id, "processes": []},
    )
    fake_report_service = types.ModuleType("app.services.report_service")
    fake_report_service.create_generic_long_cli_pipeline_from_completed_report = (
        fake_create_generic_long_cli_pipeline_from_completed_report
    )
    monkeypatch.setitem(sys.modules, "app.services.report_service", fake_report_service)

    response = runtime_service_module.resume_runtime_process("pipeline", pipeline_job_id, report_id=report_id)

    assert response["action"] == "rebuild_workspace_then_restart_pipeline"
    assert response["resume_strategy"] == "rebuild_workspace_then_restart_pipeline"
    assert response["resume_issue_kind"] == "missing_pipeline_workspace"
    assert response["pipeline_job_id"] == "pipeline-restarted-001"
    assert response["pipeline_type"] == "generic_long_cli_pipeline"
    assert response["workspace_rebuild_path"].endswith("codex_runtime_rebuild")
    assert start_calls == [{"report_id": report_id, "auto_start": True}]


@pytest.mark.parametrize(
    ("result_resume_strategy", "expected_resume_strategy"),
    [
        (None, "start_generic_long_cli_pipeline"),
        ("resume_existing_bootstrap", "resume_existing_bootstrap"),
    ],
)
def test_resume_runtime_bootstrap_starts_generic_long_cli_pipeline(
    isolated_runtime_paths: Path,
    monkeypatch: pytest.MonkeyPatch,
    result_resume_strategy: str | None,
    expected_resume_strategy: str,
) -> None:
    report_id = "bootstrap-start-001"
    _seed_report_dir(isolated_runtime_paths, report_id)
    start_calls: list[dict[str, object]] = []

    def fake_create_generic_long_cli_pipeline_from_completed_report(target_report_id: str, *, auto_start: bool = True) -> dict[str, object]:
        start_calls.append({"report_id": target_report_id, "auto_start": auto_start})
        result: dict[str, object] = {
            "pipeline_job_id": "pipeline-bootstrap-001",
            "pipeline_type": "generic_long_cli_pipeline",
            "workspace_path": str((isolated_runtime_paths / f"smart-report-{target_report_id}" / "codex_runtime_rebuild").resolve()),
        }
        if result_resume_strategy:
            result["resume_strategy"] = result_resume_strategy
        return result

    monkeypatch.setattr(
        runtime_service_module,
        "_completed_report_cli_bootstrap_status",
        lambda _report_id: {"can_start_generic_long_cli": True, "missing_required_assets": []},
    )
    monkeypatch.setattr(
        runtime_service_module,
        "list_runtime_processes",
        lambda report_id, session_id="": {"report_id": report_id, "processes": []},
    )
    fake_report_service = types.ModuleType("app.services.report_service")
    fake_report_service.create_generic_long_cli_pipeline_from_completed_report = (
        fake_create_generic_long_cli_pipeline_from_completed_report
    )
    monkeypatch.setitem(sys.modules, "app.services.report_service", fake_report_service)

    response = runtime_service_module.resume_runtime_process("runtime_bootstrap", report_id, report_id=report_id)

    assert response["action"] == "resume"
    assert response["resume_strategy"] == expected_resume_strategy
    assert response["pipeline_job_id"] == "pipeline-bootstrap-001"
    assert response["pipeline_type"] == "generic_long_cli_pipeline"
    assert start_calls == [{"report_id": report_id, "auto_start": True}]


def test_resume_runtime_bootstrap_returns_blocked_payload_when_assets_are_missing(
    isolated_runtime_paths: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_id = "bootstrap-blocked-001"
    _seed_report_dir(isolated_runtime_paths, report_id)

    monkeypatch.setattr(
        runtime_service_module,
        "_completed_report_cli_bootstrap_status",
        lambda _report_id: {
            "can_start_generic_long_cli": False,
            "missing_required_assets": ["original_source_dataset", "reader_report_or_analysis_outputs"],
        },
    )
    monkeypatch.setattr(
        runtime_service_module,
        "list_runtime_processes",
        lambda report_id, session_id="": {"report_id": report_id, "processes": []},
    )

    response = runtime_service_module.resume_runtime_process("runtime_bootstrap", report_id, report_id=report_id)

    assert response["action"] == "start_generic_long_cli_blocked"
    assert response["resume_strategy"] == "blocked_missing_inputs"
    assert response["blocking_missing_inputs"] == ["original_source_dataset", "reader_report_or_analysis_outputs"]
    assert response["result"]["can_start_generic_long_cli"] is False
