from __future__ import annotations

import json
import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException

import app.services.report_agent_session_service as session_service


def test_iter_report_agent_session_sse_emits_error_event_for_missing_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_missing(*args, **kwargs):
        raise HTTPException(status_code=404, detail="Report agent session not found: missing")

    monkeypatch.setattr(session_service, "list_report_agent_session_events", _raise_missing)

    async def _read_first_event() -> str:
        return await anext(session_service.iter_report_agent_session_sse("report-1", "session-1"))

    payload = asyncio.run(_read_first_event())

    assert payload.startswith("event: error\n")
    assert "response already started" not in payload.lower()
    json_payload = json.loads(payload.split("data: ", 1)[1].strip())
    assert json_payload["status_code"] == 404
    assert json_payload["session_id"] == "session-1"


def test_list_report_agent_session_events_does_not_rewrite_updated_at_without_state_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reports_dir = tmp_path / "reports"
    report_id = "report-1"
    session_id = "session-1"
    workspace = reports_dir / f"smart-report-{report_id}" / "codex_agent_sessions" / session_id
    workspace.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(session_service, "REPORTS_DIR", reports_dir)

    original_updated_at = "2026-05-10T00:00:00Z"
    session_payload = {
        "session_id": session_id,
        "report_id": report_id,
        "workspace_path": str(workspace.resolve()),
        "created_at": "2026-05-09T00:00:00Z",
        "updated_at": original_updated_at,
        "status": "active",
        "session_status": "active",
        "current_turn": {},
        "turns": [],
    }
    (workspace / session_service.SESSION_FILE_NAME).write_text(
        json.dumps(session_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(session_service, "_sync_runtime_stdout", lambda session: session)
    monkeypatch.setattr(session_service, "_sync_task_completion", lambda session: session)

    payload = session_service.list_report_agent_session_events(report_id, session_id, cursor=0)

    assert payload["session"]["updated_at"] == original_updated_at
    stored = json.loads((workspace / session_service.SESSION_FILE_NAME).read_text(encoding="utf-8"))
    assert stored["updated_at"] == original_updated_at


def test_list_report_agent_session_events_persists_updated_at_when_sync_changes_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reports_dir = tmp_path / "reports"
    report_id = "report-2"
    session_id = "session-2"
    workspace = reports_dir / f"smart-report-{report_id}" / "codex_agent_sessions" / session_id
    workspace.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(session_service, "REPORTS_DIR", reports_dir)

    original_updated_at = "2026-05-10T00:00:00Z"
    session_payload = {
        "session_id": session_id,
        "report_id": report_id,
        "workspace_path": str(workspace.resolve()),
        "created_at": "2026-05-09T00:00:00Z",
        "updated_at": original_updated_at,
        "status": "active",
        "session_status": "active",
        "current_turn": {},
        "turns": [],
    }
    (workspace / session_service.SESSION_FILE_NAME).write_text(
        json.dumps(session_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    def _mark_online(session: dict[str, object]) -> dict[str, object]:
        session["native_connection_status"] = "online"
        return session

    monkeypatch.setattr(session_service, "_sync_runtime_stdout", _mark_online)
    monkeypatch.setattr(session_service, "_sync_task_completion", lambda session: session)

    payload = session_service.list_report_agent_session_events(report_id, session_id, cursor=0)

    assert payload["session"]["native_connection_status"] == "online"
    stored = json.loads((workspace / session_service.SESSION_FILE_NAME).read_text(encoding="utf-8"))
    assert stored["native_connection_status"] == "online"
    assert stored["updated_at"] != original_updated_at


def _basic_revision_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    public_artifacts_dir = tmp_path / "public"
    reports_dir = public_artifacts_dir / "reports"
    report_id = "report-pdf"
    session_id = "agent-session-test"
    workspace = reports_dir / f"smart-report-{report_id}" / session_service.SESSION_DIR_NAME / session_id
    working_dir = workspace / "working"
    working_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(session_service, "PUBLIC_ARTIFACTS_DIR", public_artifacts_dir)
    monkeypatch.setattr(session_service, "REPORTS_DIR", reports_dir)

    md_path = working_dir / "report.md"
    html_path = working_dir / "report.html"
    css_path = working_dir / "report.css"
    md_path.write_text("# Original\n\nBody", encoding="utf-8")
    html_path.write_text(
        "<!doctype html><html><head><link rel=\"stylesheet\" href=\"report.css\" /></head><body><h1>Revised</h1></body></html>",
        encoding="utf-8",
    )
    css_path.write_text("body { font-family: sans-serif; }", encoding="utf-8")
    turn = {
        "turn_id": "turn-1",
        "status": "running",
        "started_at": "2026-05-17T00:00:00Z",
        "revision_intent": {"operation_kind": "freeform_revision"},
        "baseline_artifacts": {},
    }
    return {
        "session_id": session_id,
        "report_id": report_id,
        "workspace_path": str(workspace.resolve()),
        "working_dir": str(working_dir.resolve()),
        "status": "active",
        "session_status": "active",
        "active_turn_id": "native-1",
        "current_turn": dict(turn),
        "turns": [dict(turn)],
        "working_artifacts": {
            "markdown": str(md_path.resolve()),
            "html": str(html_path.resolve()),
            "css": str(css_path.resolve()),
        },
        "created_at": "2026-05-17T00:00:00Z",
        "updated_at": "2026-05-17T00:00:00Z",
    }


def test_render_working_pdf_preview_updates_session_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)

    def _fake_render(*, html_path: Path, css_path: Path, output_pdf_path: Path, timeout_sec: int) -> dict[str, object]:
        assert html_path.is_file()
        assert css_path.is_file()
        output_pdf_path.write_bytes(b"%PDF-1.4\n% test pdf\n")
        return {"pdf_path": str(output_pdf_path), "bytes": output_pdf_path.stat().st_size, "timeout_sec": timeout_sec}

    monkeypatch.setattr(session_service, "render_html_to_pdf", _fake_render)

    artifact = session_service._render_working_pdf_preview(session, turn_id="turn-1")

    assert artifact["type"] == "pdf"
    assert Path(str(session["working_artifacts"]["pdf"])).is_file()
    assert session["preview_artifact"]["type"] == "pdf"
    assert str(session["preview_url"]).endswith("/report.pdf")


def test_native_turn_completion_requires_pdf_render_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)

    def _fake_render(*, html_path: Path, css_path: Path, output_pdf_path: Path, timeout_sec: int) -> dict[str, object]:
        output_pdf_path.write_bytes(b"%PDF-1.4\n% test pdf\n")
        return {"pdf_path": str(output_pdf_path), "bytes": output_pdf_path.stat().st_size}

    monkeypatch.setattr(session_service, "render_html_to_pdf", _fake_render)
    monkeypatch.setattr(session_service, "_verify_turn_revision", lambda _session, _turn: {"passed": True, "changed_targets": ["body_copy"]})

    completed = session_service._finalize_native_turn_completion(
        "report-pdf",
        "agent-session-test",
        session,
        {"method": "turn/completed"},
        {"turn": {"id": "native-1"}},
    )

    assert completed is True
    assert session["current_turn"]["status"] == "completed"
    assert session["current_turn"]["final_scope_status"] == "passed"
    assert any(item["type"] == "pdf" for item in session["current_turn"]["artifacts"])


def test_native_turn_completion_fails_when_pdf_render_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)

    def _raise_render(*, html_path: Path, css_path: Path, output_pdf_path: Path, timeout_sec: int) -> dict[str, object]:
        raise RuntimeError("edge render unavailable")

    monkeypatch.setattr(session_service, "render_html_to_pdf", _raise_render)
    monkeypatch.setattr(session_service, "_verify_turn_revision", lambda _session, _turn: {"passed": True, "changed_targets": ["body_copy"]})

    completed = session_service._finalize_native_turn_completion(
        "report-pdf",
        "agent-session-test",
        session,
        {"method": "turn/completed"},
        {"turn": {"id": "native-1"}},
    )

    assert completed is False
    assert session["current_turn"]["status"] == "failed_pdf_render"
    assert session["current_turn"]["final_scope_status"] == "failed"
    assert session["current_turn"]["revision_verification"]["pdf_render_failed"] is True


def test_revision_verification_repairs_mojibake_before_markdown_html_sync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)
    working = session["working_artifacts"]
    baseline_dir = Path(str(session["workspace_path"])) / "turn_baselines" / "turn-1"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_md = baseline_dir / "report.md"
    baseline_html = baseline_dir / "report.html"
    baseline_css = baseline_dir / "report.css"
    baseline_md.write_text("# Asteria 中文智能分析报告\n\nBody", encoding="utf-8")
    baseline_html.write_text("<html><body><h1>Asteria 中文智能分析报告</h1><p>Body</p></body></html>", encoding="utf-8")
    baseline_css.write_text("body { font-family: sans-serif; }", encoding="utf-8")

    revised_title = "Asteria 中文智能分析报告 (interactive PDF draft verification)"
    mojibake_title = revised_title.encode("utf-8").decode("latin1")
    Path(str(working["markdown"])).write_text(f"# {mojibake_title}\n\nBody", encoding="utf-8")
    Path(str(working["html"])).write_text(f"<html><body><h1>{revised_title}</h1><p>Body</p></body></html>", encoding="utf-8")

    turn = dict(session["current_turn"])
    turn["revision_intent"] = {
        "operation_kind": "headline_edit",
        "requested_phrase": "(interactive PDF draft verification)",
        "forbidden_change_kinds": ["body_copy", "css_changes", "numeric_changes", "section_headings"],
    }
    turn["baseline_artifacts"] = {
        "markdown": str(baseline_md.resolve()),
        "html": str(baseline_html.resolve()),
        "css": str(baseline_css.resolve()),
    }

    verification = session_service._verify_turn_revision(session, turn)

    assert verification["passed"] is True
    assert verification["html_markdown_in_sync"] is True


def test_headline_revision_number_suffix_does_not_trip_numeric_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)
    working = session["working_artifacts"]
    baseline_dir = Path(str(session["workspace_path"])) / "turn_baselines" / "turn-1"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_md = baseline_dir / "report.md"
    baseline_html = baseline_dir / "report.html"
    baseline_css = baseline_dir / "report.css"
    baseline_md.write_text("# Original\n\nBody keeps 100 unchanged.", encoding="utf-8")
    baseline_html.write_text("<html><body><h1>Original</h1><p>Body keeps 100 unchanged.</p></body></html>", encoding="utf-8")
    baseline_css.write_text("body { font-family: sans-serif; }", encoding="utf-8")

    Path(str(working["markdown"])).write_text("# Original (phase 3)\n\nBody keeps 100 unchanged.", encoding="utf-8")
    Path(str(working["html"])).write_text(
        "<html><head><title>Original (phase 3)</title></head><body><h1>Original (phase 3)</h1><p>Body keeps 100 unchanged.</p></body></html>",
        encoding="utf-8",
    )

    turn = dict(session["current_turn"])
    turn["revision_intent"] = {
        "operation_kind": "headline_edit",
        "requested_phrase": "(phase 3)",
        "preserve_numbers": True,
        "forbidden_change_kinds": ["body_copy", "css_changes", "numeric_changes", "section_headings"],
    }
    turn["baseline_artifacts"] = {
        "markdown": str(baseline_md.resolve()),
        "html": str(baseline_html.resolve()),
        "css": str(baseline_css.resolve()),
    }

    verification = session_service._verify_turn_revision(session, turn)

    assert verification["passed"] is True
    assert verification["numeric_changes_detected"] is False


def test_headline_revision_still_blocks_body_numeric_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)
    working = session["working_artifacts"]
    baseline_dir = Path(str(session["workspace_path"])) / "turn_baselines" / "turn-1"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_md = baseline_dir / "report.md"
    baseline_html = baseline_dir / "report.html"
    baseline_css = baseline_dir / "report.css"
    baseline_md.write_text("# Original\n\nBody keeps 100 unchanged.", encoding="utf-8")
    baseline_html.write_text("<html><body><h1>Original</h1><p>Body keeps 100 unchanged.</p></body></html>", encoding="utf-8")
    baseline_css.write_text("body { font-family: sans-serif; }", encoding="utf-8")

    Path(str(working["markdown"])).write_text("# Original (phase 3)\n\nBody keeps 101 changed.", encoding="utf-8")
    Path(str(working["html"])).write_text(
        "<html><body><h1>Original (phase 3)</h1><p>Body keeps 101 changed.</p></body></html>",
        encoding="utf-8",
    )

    turn = dict(session["current_turn"])
    turn["revision_intent"] = {
        "operation_kind": "headline_edit",
        "requested_phrase": "(phase 3)",
        "preserve_numbers": True,
        "forbidden_change_kinds": ["body_copy", "css_changes", "numeric_changes", "section_headings"],
    }
    turn["baseline_artifacts"] = {
        "markdown": str(baseline_md.resolve()),
        "html": str(baseline_html.resolve()),
        "css": str(baseline_css.resolve()),
    }

    verification = session_service._verify_turn_revision(session, turn)

    assert verification["passed"] is False
    assert verification["numeric_changes_detected"] is True
    assert "numeric_changes" in verification["forbidden_target_violations"]


def test_cancel_recovers_valid_native_working_copy_to_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)
    working = session["working_artifacts"]
    baseline_dir = Path(str(session["workspace_path"])) / "turn_baselines" / "turn-1"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_md = baseline_dir / "report.md"
    baseline_html = baseline_dir / "report.html"
    baseline_css = baseline_dir / "report.css"
    baseline_md.write_text("# Original\n\nBody keeps 100 unchanged.", encoding="utf-8")
    baseline_html.write_text("<html><body><h1>Original</h1><p>Body keeps 100 unchanged.</p></body></html>", encoding="utf-8")
    baseline_css.write_text("body { font-family: sans-serif; }", encoding="utf-8")
    Path(str(working["markdown"])).write_text("# Original (phase 3)\n\nBody keeps 100 unchanged.", encoding="utf-8")
    Path(str(working["html"])).write_text(
        "<html><body><h1>Original (phase 3)</h1><p>Body keeps 100 unchanged.</p></body></html>",
        encoding="utf-8",
    )
    session["current_turn"]["revision_intent"] = {
        "operation_kind": "headline_edit",
        "requested_phrase": "(phase 3)",
        "preserve_numbers": True,
        "forbidden_change_kinds": ["body_copy", "css_changes", "numeric_changes", "section_headings"],
    }
    session["current_turn"]["baseline_artifacts"] = {
        "markdown": str(baseline_md.resolve()),
        "html": str(baseline_html.resolve()),
        "css": str(baseline_css.resolve()),
    }
    session["turns"] = [dict(session["current_turn"])]
    session_service._write_session(session)

    def _raise_interrupt(*args, **kwargs):
        raise RuntimeError("turn/interrupt timed out")

    def _fake_render(*, html_path: Path, css_path: Path, output_pdf_path: Path, timeout_sec: int) -> dict[str, object]:
        output_pdf_path.write_bytes(b"%PDF-1.4\n% recovered pdf\n")
        return {"pdf_path": str(output_pdf_path), "bytes": output_pdf_path.stat().st_size}

    monkeypatch.setattr(session_service, "interrupt_native_turn", _raise_interrupt)
    monkeypatch.setattr(session_service, "render_html_to_pdf", _fake_render)

    result = session_service.cancel_report_agent_turn("report-pdf", "agent-session-test")

    assert result["task"]["recovered_after_interrupt_failure"] is True
    assert result["session"]["current_turn"]["status"] == "completed"
    assert result["session"]["current_turn"]["final_scope_status"] == "passed"
    assert result["session"]["preview_artifact"]["type"] == "pdf"


def test_polling_recovers_stalled_native_working_copy_to_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _basic_revision_session(tmp_path, monkeypatch)
    working = session["working_artifacts"]
    baseline_dir = Path(str(session["workspace_path"])) / "turn_baselines" / "turn-1"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_md = baseline_dir / "report.md"
    baseline_html = baseline_dir / "report.html"
    baseline_css = baseline_dir / "report.css"
    baseline_md.write_text("# Original\n\nBody keeps 100 unchanged.", encoding="utf-8")
    baseline_html.write_text("<html><body><h1>Original</h1><p>Body keeps 100 unchanged.</p></body></html>", encoding="utf-8")
    baseline_css.write_text("body { font-family: sans-serif; }", encoding="utf-8")
    Path(str(working["markdown"])).write_text("# Original (phase 3)\n\nBody keeps 100 unchanged.", encoding="utf-8")
    Path(str(working["html"])).write_text(
        "<html><body><h1>Original (phase 3)</h1><p>Body keeps 100 unchanged.</p></body></html>",
        encoding="utf-8",
    )
    session["native_thread_status"] = "active"
    session["native_connection_status"] = "online"
    session["current_turn"]["revision_intent"] = {
        "operation_kind": "headline_edit",
        "requested_phrase": "(phase 3)",
        "preserve_numbers": True,
        "forbidden_change_kinds": ["body_copy", "css_changes", "numeric_changes", "section_headings"],
    }
    session["current_turn"]["baseline_artifacts"] = {
        "markdown": str(baseline_md.resolve()),
        "html": str(baseline_html.resolve()),
        "css": str(baseline_css.resolve()),
    }
    session["turns"] = [dict(session["current_turn"])]
    session_service._write_session(session)

    def _fake_render(*, html_path: Path, css_path: Path, output_pdf_path: Path, timeout_sec: int) -> dict[str, object]:
        output_pdf_path.write_bytes(b"%PDF-1.4\n% recovered from polling\n")
        return {"pdf_path": str(output_pdf_path), "bytes": output_pdf_path.stat().st_size}

    monkeypatch.setattr(session_service, "NATIVE_TURN_STALLED_RECOVERY_SECONDS", 0)
    monkeypatch.setattr(session_service, "NATIVE_TURN_STALLED_RECOVERY_RETRY_SECONDS", 0)
    monkeypatch.setattr(session_service, "render_html_to_pdf", _fake_render)

    payload = session_service.list_report_agent_session_events("report-pdf", "agent-session-test", cursor=0)

    assert payload["session"]["current_turn"]["status"] == "completed"
    assert payload["session"]["current_turn"]["final_scope_status"] == "passed"
    assert payload["session"]["native_connection_status"] == "completed_after_native_recovery"
    assert payload["session"]["preview_artifact"]["type"] == "pdf"
    assert any(event["kind"] == "native_recovery_started" for event in payload["events"])
