from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.services.codex_runtime_service as crs
import app.services.codex_runtime_store as crstore
import app.services.codex_runtime_task_service as crtask
import app.services.settings_service as ss
from app.main import app
from app.models import CodexRunRequest, RuntimeSettingsResponse


class CodexRuntimeSecurityTests(unittest.TestCase):
    def test_load_runtime_settings_raw_defaults_workspace_root_in_dev(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            with patch.object(ss, "SETTINGS_PATH", settings_path), patch.object(
                ss.sys, "frozen", False, create=True
            ), patch.dict(
                "os.environ",
                {
                    key: value
                    for key, value in {}
                },
                clear=False,
            ):
                payload = ss.load_runtime_settings_raw()
        self.assertTrue(str(payload.get("codex_workspace_root") or "").strip())

    def test_run_headless_codex_rejects_empty_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = CodexRunRequest(workspace_path=tmp, user_requirement="test")
            with patch.object(
                crs,
                "load_runtime_settings_raw",
                return_value={
                    "codex_runtime_enabled": True,
                    "codex_workspace_root": "",
                    "codex_cli_path": "codex",
                    "model": "gpt-5.4",
                    "codex_search_enabled": False,
                    "codex_timeout_sec": 1800,
                    "codex_dangerously_bypass_approvals_and_sandbox": False,
                    "codex_use_login_auth": True,
                    "api_key": "",
                    "base_url": "",
                },
            ):
                with self.assertRaises(HTTPException) as raised:
                    crs.run_headless_codex(request)
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("workspace root", str(raised.exception.detail).lower())

    def test_run_headless_codex_requires_explicit_unsandboxed_runtime_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = CodexRunRequest(
                workspace_path=tmp,
                user_requirement="test",
                dangerously_bypass_approvals_and_sandbox=True,
            )
            with patch.object(
                crs,
                "load_runtime_settings_raw",
                return_value={
                    "codex_runtime_enabled": True,
                    "codex_workspace_root": tmp,
                    "codex_cli_path": "codex",
                    "model": "gpt-5.4",
                    "codex_search_enabled": False,
                    "codex_timeout_sec": 1800,
                    "codex_dangerously_bypass_approvals_and_sandbox": False,
                    "codex_use_login_auth": True,
                    "api_key": "",
                    "base_url": "",
                },
            ), patch.object(crs, "_resolve_codex_command", return_value="codex"), patch.dict(
                crs.os.environ,
                {"ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME": ""},
            ):
                with self.assertRaises(HTTPException) as raised:
                    crs.run_headless_codex(request)
        self.assertEqual(raised.exception.status_code, 403)
        self.assertIn("unsandboxed", str(raised.exception.detail).lower())

    def test_prepare_codex_subprocess_env_prepends_working_python(self) -> None:
        env = crs._prepare_codex_subprocess_env(
            {
                "api_key": "secret-key",
                "base_url": "https://example.test/v1",
            }
        )
        self.assertEqual(env["OPENAI_API_KEY"], "secret-key")
        self.assertEqual(env["OPENAI_BASE_URL"], "https://example.test/v1")
        self.assertTrue(env["PYTHON"])
        self.assertEqual(env["UV_PYTHON"], env["PYTHON"])
        self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
        self.assertTrue(env["PATH"].split(crs.os.pathsep)[0])

    def test_runtime_api_route_rejects_when_api_switch_disabled(self) -> None:
        client = TestClient(app)
        with patch(
            "app.main.load_runtime_settings",
            return_value=RuntimeSettingsResponse(codex_runtime_api_enabled=False),
        ), patch("app.services.codex_runtime_service.run_headless_codex") as mocked_run:
            response = client.post("/api/codex-runs", json={"workspace_path": "E:\\temp"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Codex runtime API is disabled", response.json()["detail"])
        mocked_run.assert_not_called()

    def test_runtime_api_route_allows_when_api_switch_enabled(self) -> None:
        client = TestClient(app)
        fake_result = {
            "run_id": "run_123",
            "status": "completed",
            "workspace_path": "E:\\temp",
            "session_id": "",
            "summary": "",
            "changed_files": [],
            "git_diff_path": "",
            "git_diff_url": "",
            "transcript_path": "",
            "transcript_url": "",
            "stdout_path": "",
            "stdout_url": "",
            "stderr_path": "",
            "stderr_url": "",
            "summary_path": "",
            "summary_url": "",
            "created_at": "2026-04-30T00:00:00Z",
            "updated_at": "2026-04-30T00:00:00Z",
            "error": "",
            "transcript_entry_count": 0,
        }
        with patch(
            "app.main.load_runtime_settings",
            return_value=RuntimeSettingsResponse(codex_runtime_api_enabled=True),
        ), patch("app.services.codex_runtime_service.run_headless_codex", return_value=fake_result) as mocked_run:
            response = client.post("/api/codex-runs", json={"workspace_path": "E:\\temp"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["run_id"], "run_123")
        mocked_run.assert_called_once()

    def test_runtime_resume_route_returns_blocked_payload(self) -> None:
        client = TestClient(app)
        fake_result = {
            "action": "resume_blocked",
            "kind": "pipeline",
            "id": "pipeline-001",
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "missing_reader_required_top12_combo_table",
            "blocking_missing_inputs": ["source_visual_assets/ops_channel_source_aarrr_topn_small_multiples.csv"],
            "processes": [],
            "report_id": "report-001",
            "result": {"resume_strategy": "blocked_missing_inputs"},
        }
        with patch(
            "app.main.load_runtime_settings",
            return_value=RuntimeSettingsResponse(codex_runtime_api_enabled=True),
        ), patch("app.services.runtime_process_service.resume_runtime_process", return_value=fake_result) as mocked_resume:
            response = client.post("/api/runtime/processes/pipeline/pipeline-001/resume?report_id=report-001")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["action"], "resume_blocked")
        self.assertEqual(payload["resume_strategy"], "blocked_missing_inputs")
        self.assertEqual(
            payload["blocking_missing_inputs"],
            ["source_visual_assets/ops_channel_source_aarrr_topn_small_multiples.csv"],
        )
        mocked_resume.assert_called_once_with("pipeline", "pipeline-001", report_id="report-001", session_id="")

    def test_runtime_resume_route_returns_rebuild_workspace_payload(self) -> None:
        client = TestClient(app)
        fake_result = {
            "action": "rebuild_workspace_then_restart_pipeline",
            "kind": "pipeline",
            "id": "pipeline-002",
            "pipeline_job_id": "pipeline-restarted-002",
            "pipeline_type": "generic_long_cli_pipeline",
            "resume_strategy": "rebuild_workspace_then_restart_pipeline",
            "resume_issue_kind": "missing_pipeline_workspace",
            "workspace_rebuild_path": "E:\\temp\\report-002\\codex_runtime_rebuild",
            "processes": [],
            "report_id": "report-002",
            "result": {
                "pipeline_job_id": "pipeline-restarted-002",
                "pipeline_type": "generic_long_cli_pipeline",
                "workspace_path": "E:\\temp\\report-002\\codex_runtime_rebuild",
            },
        }
        with patch(
            "app.main.load_runtime_settings",
            return_value=RuntimeSettingsResponse(codex_runtime_api_enabled=True),
        ), patch("app.services.runtime_process_service.resume_runtime_process", return_value=fake_result) as mocked_resume:
            response = client.post("/api/runtime/processes/pipeline/pipeline-002/resume?report_id=report-002")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["action"], "rebuild_workspace_then_restart_pipeline")
        self.assertEqual(payload["pipeline_job_id"], "pipeline-restarted-002")
        self.assertEqual(payload["resume_strategy"], "rebuild_workspace_then_restart_pipeline")
        mocked_resume.assert_called_once_with("pipeline", "pipeline-002", report_id="report-002", session_id="")

    def test_write_run_manifest_redacts_prompt_and_request_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            with patch.object(crstore, "CODEX_RUNTIME_RUNS_DIR", base_dir / "runs"), patch.object(
                crstore, "CODEX_RUNTIME_TASKS_DIR", base_dir / "tasks"
            ):
                run_id = "run_redact_01"
                payload = {
                    "run_id": run_id,
                    "status": "preparing",
                    "workspace_path": "E:\\workspace",
                    "parent_report_id": "report-001",
                    "parent_report_job_id": "report-task-001",
                    "parent_stage_id": "semantic_layer",
                    "child_index": 2,
                    "artifact_source": "semantic_layer_runtime_output.json",
                    "prompt": "Very sensitive prompt body with internal details",
                    "request": {
                        "workspace_path": "E:\\workspace",
                        "parent_report_id": "report-001",
                        "parent_report_job_id": "report-task-001",
                        "parent_stage_id": "semantic_layer",
                        "child_index": 2,
                        "artifact_source": "semantic_layer_runtime_output.json",
                        "prompt": "Very sensitive prompt body with internal details",
                        "user_requirement": "Investigate confidential planning assumptions",
                        "context_payload": {"secret_metric": 42, "nested": {"foo": "bar"}},
                        "purpose": "generic",
                    },
                }
                path = crstore.write_run_manifest(run_id, payload)
                stored = json.loads(path.read_text(encoding="utf-8"))

        self.assertNotIn("prompt", stored)
        self.assertTrue(stored.get("prompt_redacted"))
        self.assertTrue(stored.get("prompt_hash"))
        self.assertTrue(stored.get("prompt_preview"))
        self.assertIn("request", stored)
        self.assertEqual(stored["parent_report_id"], "report-001")
        self.assertEqual(stored["parent_report_job_id"], "report-task-001")
        self.assertEqual(stored["parent_stage_id"], "semantic_layer")
        self.assertEqual(stored["child_index"], 2)
        self.assertEqual(stored["artifact_source"], "semantic_layer_runtime_output.json")
        self.assertNotIn("prompt", stored["request"])
        self.assertNotIn("user_requirement", stored["request"])
        self.assertNotIn("context_payload", stored["request"])
        self.assertEqual(stored["request"]["parent_report_id"], "report-001")
        self.assertEqual(stored["request"]["parent_report_job_id"], "report-task-001")
        self.assertEqual(stored["request"]["parent_stage_id"], "semantic_layer")
        self.assertEqual(stored["request"]["child_index"], 2)
        self.assertEqual(stored["request"]["artifact_source"], "semantic_layer_runtime_output.json")
        self.assertTrue(stored["request"].get("request_redacted"))
        self.assertGreater(stored["request"].get("context_size", 0), 0)
        self.assertIn("secret_metric", stored["request"].get("context_top_level_keys", []))

    def test_create_codex_run_task_persists_redacted_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            request = CodexRunRequest(
                workspace_path="E:\\workspace",
                prompt="Highly sensitive runtime prompt",
                user_requirement="Need to inspect private report files",
                context_payload={"report_text": "internal", "risk_level": "high"},
                parent_report_id="report-001",
                parent_report_job_id="report-task-001",
                parent_stage_id="semantic_layer",
                child_index=3,
                artifact_source="semantic_layer_runtime_output.json",
            )
            with patch.object(crtask, "task_path", lambda job_id: (base_dir / f"{job_id}.json")), patch.object(
                crtask._TASK_EXECUTOR, "submit", return_value=None
            ):
                response = crtask.create_codex_run_task(request)
                stored = json.loads((base_dir / f"{response['job_id']}.json").read_text(encoding="utf-8"))

        self.assertIn("request", stored)
        self.assertEqual(stored["parent_report_id"], "report-001")
        self.assertEqual(stored["parent_report_job_id"], "report-task-001")
        self.assertEqual(stored["parent_stage_id"], "semantic_layer")
        self.assertEqual(stored["child_index"], 3)
        self.assertEqual(stored["artifact_source"], "semantic_layer_runtime_output.json")
        self.assertNotIn("prompt", stored["request"])
        self.assertNotIn("user_requirement", stored["request"])
        self.assertNotIn("context_payload", stored["request"])
        self.assertEqual(stored["request"]["parent_report_id"], "report-001")
        self.assertEqual(stored["request"]["parent_report_job_id"], "report-task-001")
        self.assertEqual(stored["request"]["parent_stage_id"], "semantic_layer")
        self.assertEqual(stored["request"]["child_index"], 3)
        self.assertEqual(stored["request"]["artifact_source"], "semantic_layer_runtime_output.json")
        self.assertTrue(stored["request"].get("prompt_hash"))
        self.assertTrue(stored["request"].get("prompt_preview"))
        self.assertGreater(stored["request"].get("context_size", 0), 0)

    def test_create_codex_run_task_propagates_parent_metadata_to_external_stage_listener(self) -> None:
        observed_events: list[dict[str, object]] = []

        def fake_run_headless_codex(request: CodexRunRequest, *, stage_listener=None):
            if stage_listener:
                stage_listener(
                    {
                        "stage_id": "workspace_validated",
                        "title": "Workspace validated",
                        "detail": "Workspace passed validation.",
                        "timestamp": "2026-04-30T00:00:00Z",
                        "payload": {"status": "running"},
                    }
                )
            return {
                "run_id": "run-parent-001",
                "session_id": "",
                "summary": "done",
                "changed_files": [],
                "git_diff_url": "",
                "transcript_url": "",
                "status": "completed",
                "error": "",
            }

        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            request = CodexRunRequest(workspace_path="E:\\workspace", prompt="runtime child task")
            with patch.object(crtask, "task_path", lambda job_id: (base_dir / f"{job_id}.json")), patch.object(
                crtask,
                "run_headless_codex",
                side_effect=fake_run_headless_codex,
            ), patch.object(
                crtask._TASK_EXECUTOR,
                "submit",
                side_effect=lambda fn, *args: fn(*args),
            ):
                task = crtask.create_codex_run_task(
                    request,
                    parent_report_job_id="report-task-parent-001",
                    parent_report_id="report-001",
                    parent_stage_id="semantic_layer",
                    child_index=4,
                    stage_id="semantic_runtime_review",
                    purpose="semantic_runtime_review",
                    artifact_source="semantic_layer_runtime_output.json",
                    stage_listener=observed_events.append,
                    return_full=True,
                )

        self.assertEqual(task["parent_report_job_id"], "report-task-parent-001")
        self.assertEqual(task["parent_report_id"], "report-001")
        self.assertEqual(task["parent_stage_id"], "semantic_layer")
        self.assertEqual(task["child_index"], 4)
        self.assertEqual(task["stage_id"], "semantic_runtime_review")
        self.assertEqual(task["purpose"], "semantic_runtime_review")
        self.assertEqual(task["artifact_source"], "semantic_layer_runtime_output.json")
        self.assertTrue(observed_events)
        event = observed_events[0]
        payload = dict(event.get("payload") or {})
        self.assertTrue(str(event.get("stage_id") or "").startswith("runtime_child::semantic_runtime_review::"))
        self.assertEqual(payload.get("runtime_parent_report_job_id"), "report-task-parent-001")
        self.assertEqual(payload.get("runtime_parent_report_id"), "report-001")
        self.assertEqual(payload.get("runtime_parent_stage_id"), "semantic_layer")
        self.assertEqual(payload.get("runtime_child_index"), 4)
        self.assertEqual(payload.get("runtime_stage_id"), "semantic_runtime_review")
        self.assertEqual(payload.get("runtime_purpose"), "semantic_runtime_review")
        self.assertEqual(payload.get("runtime_child_job_id"), task["job_id"])
        self.assertEqual(payload.get("author_mode"), "codex_cli_runtime")
        self.assertEqual(payload.get("runtime_state"), "live")
        self.assertEqual(payload.get("artifact_source"), "semantic_layer_runtime_output.json")

    def test_get_codex_run_task_normalizes_legacy_telemetry_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            legacy_job_id = "codex-task-legacy-001"
            legacy_payload = {
                "job_id": legacy_job_id,
                "run_id": "run-legacy-001",
                "status": "completed",
                "progress_percent": 100,
                "current_stage_id": "completed",
                "current_stage_title": "done",
                "current_stage_detail": "done",
                "created_at": "2026-04-30T00:00:00Z",
                "updated_at": "2026-04-30T00:00:00Z",
                "error": "",
                "parent_report_id": "report-legacy-001",
                "request": {"workspace_path": "E:\\workspace", "stage_id": "legacy_stage", "purpose": "legacy_purpose"},
            }
            (base_dir / f"{legacy_job_id}.json").write_text(json.dumps(legacy_payload, ensure_ascii=False), encoding="utf-8")
            with patch.object(crtask, "task_path", lambda job_id: (base_dir / f"{job_id}.json")):
                loaded = crtask.get_codex_run_task(legacy_job_id)

        self.assertEqual(loaded["author_mode"], "codex_cli_runtime")
        self.assertEqual(loaded["runtime_state"], "live")
        self.assertEqual(loaded["degradation_state"], "none")
        self.assertEqual(loaded["artifact_source"], "codex_runtime_task")
        self.assertEqual(loaded["stage_id"], "legacy_stage")
        self.assertEqual(loaded["purpose"], "legacy_purpose")


if __name__ == "__main__":
    unittest.main()
