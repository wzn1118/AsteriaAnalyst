from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app.models import CodexRunRequest
from app.models import SmartReportRequest
import app.services.report_task_service as report_task_service_module
from app.services.report_task_service import create_report_task, get_report_task


def test_report_task_runs_and_exposes_progress() -> None:
    def fake_generate(
        dataset_id: str,
        request: SmartReportRequest,
        progress_callback=None,
        report_job_id: str = "",
        runtime_child_task_creator=None,
    ):
        if progress_callback:
            progress_callback(
                {
                    "stage_id": "init",
                    "title": "初始化协调器",
                    "detail": "任务已经进入主报告链。",
                    "timestamp": "2026-04-28T00:00:00Z",
                    "payload": {"status": "running"},
                }
            )
            progress_callback(
                {
                    "stage_id": "rendering",
                    "title": "开始渲染报告产物",
                    "detail": "正在生成主报告和附录。",
                    "timestamp": "2026-04-28T00:00:02Z",
                    "payload": {"status": "running"},
                }
            )
        return {
            "report_id": "demo-report-001",
            "dataset_name": "demo-dataset",
            "sheet_name": "Sheet1",
            "main_downloadable": {
                "name": "demo-report-001-management_report.pdf",
                "path": "/storage/reports/demo-report-001-management_report.pdf",
                "purpose": "main",
                "is_main": True,
                "type": "pdf",
            },
            "downloadables": [],
            "formal_pdf_allowed": True,
            "release_blocked": False,
        }

    with patch("app.services.report_task_service.generate_smart_report", side_effect=fake_generate):
        task = create_report_task("demo-dataset-id", SmartReportRequest())
        for _ in range(50):
            snapshot = get_report_task(task["job_id"])
            if snapshot["status"] == "completed":
                break
            time.sleep(0.05)
        else:
            raise AssertionError("task did not complete in time")

    assert snapshot["status"] == "completed"
    assert snapshot["progress_percent"] == 100
    assert snapshot["result"]["report_id"] == "demo-report-001"
    assert snapshot["result_summary"]["main_downloadable"] == "demo-report-001-management_report.pdf"
    assert any(event["stage_id"] == "rendering" for event in snapshot["stage_events"])


def test_report_task_registers_runtime_child_jobs_and_progress() -> None:
    def fake_create_codex_run_task(
        request: CodexRunRequest,
        *,
        parent_report_job_id: str = "",
        parent_report_id: str = "",
        parent_stage_id: str = "",
        child_index: int = 0,
        stage_id: str = "",
        purpose: str = "",
        artifact_source: str = "",
        stage_listener=None,
        return_full: bool = False,
    ):
        child_task = {
            "job_id": "codex-task-child-001",
            "run_id": "run-child-001",
            "parent_report_job_id": parent_report_job_id,
            "parent_report_id": parent_report_id,
            "parent_stage_id": parent_stage_id or "post_report_runtime_review",
            "child_index": child_index or 1,
            "stage_id": stage_id,
            "purpose": purpose,
            "artifact_source": artifact_source or "runtime_post_report_review.md",
            "status": "queued",
            "progress_percent": 0,
            "current_stage_id": "queued",
            "current_stage_title": "Task created",
            "current_stage_detail": "queued",
        }
        if stage_listener:
            stage_listener(
                {
                    "stage_id": "runtime_child::post_report_runtime_review::workspace_validated",
                    "title": "Runtime child: Workspace validated",
                    "detail": "Workspace validated for runtime child job.",
                    "timestamp": "2026-04-30T00:00:01Z",
                    "payload": {
                        "status": "running",
                        "source": "runtime_child_task",
                        "runtime_child_job_id": child_task["job_id"],
                        "runtime_child_run_id": child_task["run_id"],
                        "runtime_parent_report_job_id": parent_report_job_id,
                        "runtime_parent_report_id": parent_report_id,
                        "runtime_parent_stage_id": "post_report_runtime_review",
                        "runtime_child_index": 1,
                        "runtime_stage_id": stage_id,
                        "runtime_purpose": purpose,
                        "artifact_source": "runtime_post_report_review.md",
                        "runtime_child_status": "running",
                        "runtime_child_progress_percent": 20,
                        "runtime_child_current_stage_id": "workspace_validated",
                        "runtime_child_current_stage_title": "Workspace validated",
                        "runtime_child_current_stage_detail": "Workspace validated for runtime child job.",
                    },
                }
            )
        return child_task

    def fake_generate(
        dataset_id: str,
        request: SmartReportRequest,
        progress_callback=None,
        report_job_id: str = "",
        runtime_child_task_creator=None,
    ):
        if progress_callback:
            progress_callback(
                {
                    "stage_id": "init",
                    "title": "Coordinator init",
                    "detail": "Main report task started.",
                    "timestamp": "2026-04-30T00:00:00Z",
                    "payload": {"status": "running"},
                }
            )
        assert runtime_child_task_creator is not None
        child_task = runtime_child_task_creator(
            CodexRunRequest(workspace_path="C:\\temp\\asteria-workspace", prompt="runtime child review"),
            parent_report_id="demo-report-002",
            stage_id="post_report_runtime_review",
            purpose="post_report_runtime_review",
        )
        return {
            "report_id": "demo-report-002",
            "dataset_name": "demo-dataset",
            "sheet_name": "Sheet1",
            "main_downloadable": {
                "name": "demo-report-002-management_report.pdf",
                "path": "/storage/reports/demo-report-002-management_report.pdf",
                "purpose": "main",
                "is_main": True,
                "type": "pdf",
            },
            "downloadables": [],
            "formal_pdf_allowed": True,
            "release_blocked": False,
            "runtime_child_jobs": [
                {
                    **child_task,
                    "status": "completed",
                    "progress_percent": 100,
                    "current_stage_id": "completed",
                    "current_stage_title": "Runtime child completed",
                    "current_stage_detail": "Runtime child finished successfully.",
                }
            ],
        }

    with patch("app.services.report_task_service.create_codex_run_task", side_effect=fake_create_codex_run_task), patch(
        "app.services.report_task_service.generate_smart_report",
        side_effect=fake_generate,
    ):
        task = create_report_task("demo-dataset-id", SmartReportRequest())
        for _ in range(50):
            snapshot = get_report_task(task["job_id"])
            if snapshot["status"] == "completed":
                break
            time.sleep(0.05)
        else:
            raise AssertionError("task did not complete in time")

    assert snapshot["status"] == "completed"
    assert snapshot["runtime_child_job_ids"] == ["codex-task-child-001"]
    assert len(snapshot["runtime_child_jobs"]) == 1
    assert snapshot["runtime_child_jobs"][0]["parent_report_job_id"] == snapshot["job_id"]
    assert snapshot["runtime_child_jobs"][0]["parent_stage_id"] == "post_report_runtime_review"
    assert snapshot["runtime_child_jobs"][0]["child_index"] == 1
    assert snapshot["runtime_child_jobs"][0]["stage_id"] == "post_report_runtime_review"
    assert snapshot["runtime_child_jobs"][0]["author_mode"] == "codex_cli_runtime"
    assert snapshot["runtime_child_jobs"][0]["runtime_state"] == "live"
    assert snapshot["runtime_child_jobs"][0]["degradation_state"] == "none"
    assert snapshot["runtime_child_jobs"][0]["artifact_source"] == "runtime_post_report_review.md"
    assert snapshot["result_summary"]["runtime_child_job_ids"] == ["codex-task-child-001"]
    assert any(event["stage_id"].startswith("runtime_child::post_report_runtime_review::") for event in snapshot["stage_events"])


def test_create_report_task_rejects_when_active_limit_is_exceeded(tmp_path: Path) -> None:
    rejection_log = tmp_path / "queue_rejections.jsonl"
    active_task = {
        "job_id": "report-task-active-001",
        "dataset_id": "demo-dataset-id",
        "status": "running",
        "progress_percent": 50,
    }

    with patch.dict(report_task_service_module._TASKS, {"report-task-active-001": active_task}, clear=True), patch.object(
        report_task_service_module,
        "QUEUE_REJECTION_LOG_PATH",
        rejection_log,
    ), patch.object(
        report_task_service_module,
        "MAX_ACTIVE_REPORT_TASKS",
        1,
    ), patch.object(
        report_task_service_module._TASK_EXECUTOR,
        "submit",
    ) as mocked_submit:
        try:
            create_report_task("demo-dataset-id", SmartReportRequest())
        except HTTPException as exc:
            assert exc.status_code == 429
            assert "Too many active report jobs" in str(exc.detail)
        else:
            raise AssertionError("expected admission control to reject the task")

    mocked_submit.assert_not_called()
    assert rejection_log.exists()
    rows = [json.loads(line) for line in rejection_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["event"] == "report_task_queue_rejected"
    assert rows[0]["dataset_id"] == "demo-dataset-id"
    assert rows[0]["active_task_count"] == 1
    assert rows[0]["limit"] == 1
