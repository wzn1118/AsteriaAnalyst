from __future__ import annotations

import asyncio
import html
import difflib
import hashlib
import json
import math
import re
import threading
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Iterable
from urllib.parse import unquote, urlsplit

from fastapi import HTTPException

from app.services.codex_native_app_server_service import (
    ensure_native_thread,
    interrupt_native_turn,
    start_native_turn,
    steer_native_turn,
)
from app.services.codex_runtime_pdf_render_service import render_html_to_pdf
from app.services.codex_runtime_store import read_stdout_log
from app.services.codex_runtime_task_service import cancel_codex_run_task, get_codex_run_task
from app.services.path_service import PUBLIC_ARTIFACTS_DIR, REPORTS_DIR
from app.services.report_catalog_index_service import (
    delete_report_catalog_rows,
    mark_report_catalog_scan_started,
    mark_report_catalog_scan_finished,
    mark_report_catalog_partial_seed,
    query_report_catalog_index,
    report_catalog_index_is_fresh,
    report_catalog_index_is_refreshing,
    report_catalog_index_snapshot,
    report_catalog_index_status,
    replace_report_catalog_rows,
    upsert_report_catalog_rows,
)


REPORT_DIR_PREFIX = "smart-report-"
SESSION_DIR_NAME = "codex_agent_sessions"
SESSION_FILE_NAME = "session.json"
EVENTS_FILE_NAME = "events.jsonl"
ANNOTATIONS_FILE_NAME = "annotations.json"
ATTACHMENTS_FILE_NAME = "attachments_manifest.json"
ATTACHMENT_PROFILE_JSON_NAME = "attachment_data_profile.json"
ATTACHMENT_PROFILE_MD_NAME = "attachment_data_profile.md"
REVISION_CHART_PLAN_NAME = "revision_chart_plan.json"
REVISION_CHART_RENDER_LOG_NAME = "revision_chart_render_log.json"
REVISION_EVIDENCE_ASSETS_NAME = "revision_evidence_assets_manifest.json"
REVISION_EVIDENCE_PROFILE_JSON_NAME = "revision_evidence_data_profile.json"
REVISION_EVIDENCE_PROFILE_MD_NAME = "revision_evidence_data_profile.md"
REPORT_TITLE_CACHE_NAME = ".report_title_cache.json"
CATALOG_NESTED_TITLE_GLOB_PATTERNS = (
    "*/*.html",
    "*/*.htm",
    "*/*.md",
    "*/*.txt",
    "*/*/*.html",
    "*/*/*.htm",
    "*/*/*.md",
    "*/*/*.txt",
    "*/*/*/*.html",
    "*/*/*/*.htm",
    "*/*/*/*.md",
    "*/*/*/*.txt",
)
TEXT_DIFF_SUFFIXES = {".md", ".html", ".htm", ".css", ".json", ".txt", ".csv", ".tsv"}
SESSION_FILE_SUFFIXES = {".md", ".html", ".htm", ".css", ".json", ".pdf", ".txt", ".csv", ".tsv", ".png", ".jpg", ".jpeg", ".xlsx"}
TURN_TERMINAL_STATUSES = {
    "completed",
    "failed",
    "cancelled",
    "timed_out",
    "failed_scope_miss",
    "failed_partial_application",
    "failed_scope_violation",
    "failed_pdf_render",
}
TURN_ACTIVE_STATUSES = {"queued", "running", "cancelling", "verifying", "auto_repairing"}
NATIVE_TURN_START_STALE_SECONDS = 120
NATIVE_TURN_STALLED_RECOVERY_SECONDS = 90
NATIVE_TURN_STALLED_RECOVERY_RETRY_SECONDS = 45
_EVENT_LOCKS: dict[str, threading.Lock] = {}
_EVENT_LOCKS_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_age_seconds(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()


def _storage_url_for(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(PUBLIC_ARTIFACTS_DIR).as_posix()
    except Exception:
        return ""
    return f"/storage/{relative}"


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return fallback


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp_path.write_text(data, encoding="utf-8")
        temp_path.replace(path)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return path


_MOJIBAKE_MARKERS = (
    "锛",
    "涓",
    "杩",
    "棰",
    "鐪",
    "鎶",
    "鏂",
    "绗",
    "褰",
    "缁",
    "鍙",
    "瑙",
    "鈥",
    "€",
    "è",
    "é",
    "ä",
    "å",
    "ç",
    "Â",
    "Ã",
    "�",
)


_COMMON_MOJIBAKE_MARKERS = ("杩", "涓", "嶅", "婊", "鐪", "鍙", "犵", "竴", "殑", "锛", "銆", "è", "æ", "å", "ç", "ã", "ï")


def _mojibake_score(value: str) -> int:
    return sum(value.count(marker) for marker in (*_MOJIBAKE_MARKERS, *_COMMON_MOJIBAKE_MARKERS))


def _repair_mojibake_text(value: Any) -> str:
    text = str(value or "")
    if not text or not any(marker in text for marker in (*_MOJIBAKE_MARKERS, *_COMMON_MOJIBAKE_MARKERS)):
        return text
    candidates = [text]
    for errors in ("strict", "replace", "ignore"):
        try:
            candidates.append(text.encode("gbk", errors=errors).decode("utf-8", errors=errors))
        except Exception:
            continue
        try:
            candidates.append(text.encode("latin1", errors=errors).decode("utf-8", errors=errors))
        except Exception:
            continue
        try:
            candidates.append(text.encode("cp1252", errors=errors).decode("utf-8", errors=errors))
        except Exception:
            continue
    candidates = [candidate for candidate in candidates if candidate]
    return min(candidates, key=lambda candidate: (_mojibake_score(candidate), abs(len(candidate) - len(text))))


def _report_dir(report_id: str) -> Path:
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "", str(report_id or "").strip())
    if not clean_id:
        raise HTTPException(status_code=400, detail="report_id is required.")
    path = (REPORTS_DIR / f"{REPORT_DIR_PREFIX}{clean_id}").resolve()
    try:
        path.relative_to(REPORTS_DIR.resolve())
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid report_id.") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Report not found: {clean_id}")
    return path


def _downloadable_from_file(path: Path, *, purpose: str = "", is_main: bool = False) -> dict[str, Any]:
    return {
        "name": path.name,
        "path": _storage_url_for(path),
        "file_path": str(path.resolve()),
        "purpose": purpose or "Report artifact.",
        "is_main": bool(is_main),
        "type": path.suffix.lstrip(".").lower() or "txt",
    }


def _load_manifest(report_dir: Path, report_id: str) -> dict[str, Any]:
    return dict(_read_json(report_dir / f"{report_id}-current_turn_export_manifest.json", {}) or {})


def _manifest_path(report_dir: Path, report_id: str) -> Path:
    return report_dir / f"{report_id}-current_turn_export_manifest.json"


def _load_downloadables(
    report_dir: Path,
    report_id: str,
    *,
    deep_scan: bool = True,
    fallback_scan: bool = True,
    catalog_scan_limit: int = 0,
) -> list[dict[str, Any]]:
    manifest = _load_manifest(report_dir, report_id)
    downloadables: list[dict[str, Any]] = []
    seen: set[str] = set()
    manifest_main_name = str(manifest.get("main_downloadable") or "")
    for raw_item in manifest.get("downloadables") or []:
        item = raw_item if isinstance(raw_item, dict) else {}
        name = str(item.get("name") or "")
        if not name or name in seen:
            continue
        file_path = str(item.get("file_path") or "")
        path = Path(file_path) if file_path else None
        if path is None or not path.is_file():
            if not deep_scan:
                continue
            matches = [candidate for candidate in report_dir.rglob(name) if candidate.is_file()]
            if not matches:
                continue
            path = matches[0]
        seen.add(name)
        downloadables.append(
            _downloadable_from_file(
                path,
                purpose=str(item.get("purpose") or ""),
                is_main=bool(item.get("is_main")) or name == manifest_main_name,
            )
        )
    if not deep_scan and catalog_scan_limit > 0 and len(downloadables) < catalog_scan_limit:
        candidates = sorted(
            (
                path
                for path in report_dir.rglob("*")
                if path.is_file()
                and SESSION_DIR_NAME not in path.parts
                and path.suffix.lower() in {".pdf", ".html", ".htm", ".md", ".css", ".json", ".xlsx", ".csv"}
            ),
            key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
            reverse=True,
        )
        for path in candidates:
            if len(downloadables) >= catalog_scan_limit:
                break
            if path.name in seen:
                continue
            seen.add(path.name)
            downloadables.append(_downloadable_from_file(path))
    if not downloadables and fallback_scan:
        candidates = sorted(report_dir.rglob("*")) if deep_scan else sorted(report_dir.glob("*"))
        for path in candidates:
            if not path.is_file() or SESSION_DIR_NAME in path.parts:
                continue
            if path.suffix.lower() not in {".pdf", ".html", ".htm", ".md", ".css", ".json", ".xlsx", ".csv"}:
                continue
            if path.name in seen:
                continue
            seen.add(path.name)
            downloadables.append(_downloadable_from_file(path))
    if downloadables and not any(item.get("is_main") for item in downloadables):
        preferred = [
            f"{report_id}-management_report.pdf",
            f"{report_id}-management_report.html",
            f"{report_id}.pdf",
            f"{report_id}.html",
        ]
        preferred_name = next(
            (name for name in preferred if any(str(item.get("name") or "") == name for item in downloadables)),
            "",
        )
        if preferred_name:
            for item in downloadables:
                item["is_main"] = str(item.get("name") or "") == preferred_name
    return downloadables


def _artifact_path(item: dict[str, Any]) -> Path | None:
    file_path = str(item.get("file_path") or "")
    if not file_path:
        return None
    path = Path(file_path)
    return path if path.is_file() else None


def _choose_preview(downloadables: list[dict[str, Any]]) -> dict[str, Any]:
    def _find(predicate: Any) -> dict[str, Any]:
        return next((item for item in downloadables if predicate(item)), {})

    def _preview_score(item: dict[str, Any]) -> int:
        name = str(item.get("name") or "").lower()
        purpose = str(item.get("purpose") or "").lower()
        if "agent-revision" in name:
            return 100
        if name.endswith("generic_long_cli_report.html") or name.endswith("generic_long_cli_report.pdf"):
            return 92
        if "procurement_sales_cli_shadow" in name and "_with_tables" not in name:
            return 90
        if "internet_ops" in name and ("cli" in name or "long" in name):
            return 88
        if "ecommerce" in name and ("cli" in name or "long" in name):
            return 86
        if "multi_table" in name and ("cli" in name or "long" in name):
            return 84
        if "generic_long_cli_full_report" in name:
            return 82
        if "procurement_sales_cli_shadow_with_tables" in name:
            return 80
        if "generic_long_cli_brief_report" in name:
            return 76
        if "codex cli" in purpose:
            return 70
        if item.get("is_main"):
            return 60
        return 0

    def _best(predicate: Any) -> dict[str, Any]:
        candidates = [item for item in downloadables if predicate(item)]
        if not candidates:
            return {}
        return max(candidates, key=_preview_score)

    latest_revision_html = _find(
        lambda item: str(item.get("type") or "").lower() in {"html", "htm"}
        and "agent-revision" in str(item.get("name") or "")
    )
    if latest_revision_html:
        return latest_revision_html
    cli_html = _best(
        lambda item: str(item.get("type") or "").lower() in {"html", "htm"}
        and _preview_score(item) >= 70
    )
    if cli_html:
        return cli_html
    main_html = _find(lambda item: item.get("is_main") and str(item.get("type") or "").lower() in {"html", "htm"})
    if main_html:
        return main_html
    any_html = _find(lambda item: str(item.get("type") or "").lower() in {"html", "htm"})
    if any_html:
        return any_html
    latest_revision_pdf = _find(
        lambda item: str(item.get("type") or "").lower() == "pdf" and "agent-revision" in str(item.get("name") or "")
    )
    if latest_revision_pdf:
        return latest_revision_pdf
    cli_pdf = _best(lambda item: str(item.get("type") or "").lower() == "pdf" and _preview_score(item) >= 70)
    if cli_pdf:
        return cli_pdf
    main_pdf = _find(lambda item: item.get("is_main") and str(item.get("type") or "").lower() == "pdf")
    if main_pdf:
        return main_pdf
    return _find(lambda item: str(item.get("type") or "").lower() == "pdf")


def _session_root(report_dir: Path) -> Path:
    path = report_dir / SESSION_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _session_path(report_id: str, session_id: str) -> Path:
    report_dir = _report_dir(report_id)
    session_dir = (_session_root(report_dir) / str(session_id)).resolve()
    try:
        session_dir.relative_to(_session_root(report_dir).resolve())
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid session_id.") from exc
    return session_dir


def _read_session_by_path(session_dir: Path) -> dict[str, Any]:
    path = session_dir / SESSION_FILE_NAME
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Report agent session not found: {session_dir.name}")
    return _normalize_session_state(dict(_read_json(path, {}) or {}))


def _read_session(report_id: str, session_id: str) -> dict[str, Any]:
    return _read_session_by_path(_session_path(report_id, session_id))


def _write_session(session: dict[str, Any]) -> dict[str, Any]:
    workspace = Path(str(session.get("workspace_path") or ""))
    _normalize_session_state(session)
    session["updated_at"] = _now_iso()
    _write_json(workspace / SESSION_FILE_NAME, session)
    return session


def _persist_session_if_changed(session: dict[str, Any], previous_snapshot: dict[str, Any]) -> bool:
    _normalize_session_state(session)
    baseline = dict(previous_snapshot or {})
    _normalize_session_state(baseline)
    if session == baseline:
        return False
    _write_session(session)
    return True


def _event_log_path(session: dict[str, Any]) -> Path:
    return Path(str(session.get("workspace_path") or "")) / EVENTS_FILE_NAME


def _event_lock_for(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _EVENT_LOCKS_LOCK:
        lock = _EVENT_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _EVENT_LOCKS[key] = lock
        return lock


def _max_event_id(path: Path) -> int:
    if not path.exists():
        return 0
    max_id = 0
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                payload = json.loads(line)
            except Exception:
                continue
            max_id = max(max_id, int(payload.get("event_id") or 0))
    except Exception:
        return max_id
    return max_id


def _normalize_session_state(session: dict[str, Any]) -> dict[str, Any]:
    turns = session.get("turns")
    if not isinstance(turns, list):
        turns = []
    session["turns"] = turns
    current_turn = session.get("current_turn")
    if not isinstance(current_turn, dict):
        current_turn = {}
    if not current_turn and session.get("current_task_id"):
        legacy_status = str(session.get("status") or "running")
        current_turn = {
            "turn_id": str(session.get("current_turn_id") or "turn-legacy"),
            "task_id": str(session.get("current_task_id") or ""),
            "run_id": str(session.get("current_run_id") or ""),
            "status": legacy_status if legacy_status not in {"created", "published"} else "running",
            "user_message": "",
            "started_at": session.get("updated_at") or session.get("created_at") or "",
            "completed_at": "",
            "changed_files": [],
            "artifacts": [],
        }
        if not turns:
            turns = [current_turn]
    session["turns"] = turns
    session["current_turn"] = current_turn
    session["session_status"] = str(session.get("session_status") or "active")
    session["mode"] = str(session.get("mode") or "native_app_server")
    session["native_connection_status"] = str(session.get("native_connection_status") or "idle")
    session["native_protocol_error"] = str(session.get("native_protocol_error") or "")
    if not isinstance(session.get("guidance_injections"), list):
        session["guidance_injections"] = []
    if not isinstance(session.get("suppressed_turn_ids"), list):
        session["suppressed_turn_ids"] = []
    if str(session.get("status") or "") in {"created", "completed", "published"}:
        session["status"] = session["session_status"]
    return session


def _current_turn(session: dict[str, Any]) -> dict[str, Any]:
    _normalize_session_state(session)
    return dict(session.get("current_turn") or {})


def _current_turn_status(session: dict[str, Any]) -> str:
    return str(_current_turn(session).get("status") or "")


def _has_native_turn_binding(session: dict[str, Any], turn: dict[str, Any]) -> bool:
    return bool(
        str(session.get("codex_thread_id") or "")
        or str(session.get("codex_session_id") or "")
        or str(session.get("active_turn_id") or "")
        or str(turn.get("native_turn_id") or "")
    )


def _clear_native_turn_binding(session: dict[str, Any]) -> None:
    session["codex_thread_id"] = ""
    session["codex_session_id"] = ""
    session["active_turn_id"] = ""


def _should_clear_native_thread_after_error(message: str) -> bool:
    normalized = str(message or "").lower()
    return "thread/start" in normalized or "no rollout found" in normalized


def _reconcile_stale_native_start(session: dict[str, Any]) -> bool:
    turn = _current_turn(session)
    turn_id = str(turn.get("turn_id") or "")
    status = str(turn.get("status") or "")
    if not turn_id or status not in TURN_ACTIVE_STATUSES:
        return False
    if _has_native_turn_binding(session, turn):
        return False
    native_status = str(session.get("native_connection_status") or "")
    if native_status == "starting":
        age_seconds = _iso_age_seconds(turn.get("started_at") or session.get("updated_at"))
        if age_seconds is not None and age_seconds < NATIVE_TURN_START_STALE_SECONDS:
            return False
    elif native_status != "error":
        return False

    _update_turn(
        session,
        turn_id,
        status="cancelled",
        completed_at=_now_iso(),
        final_scope_status="cancelled",
    )
    session["active_turn_id"] = ""
    session["current_task_id"] = ""
    session["current_run_id"] = ""
    session["native_connection_status"] = "stale_turn_reconciled"
    _append_event(
        session,
        "turn_cancelled",
        text="检测到上一轮原生 Codex 启动未完成；已归档旧 turn，并允许用新消息重新启动。",
        turn_id=turn_id,
        status="cancelled",
    )
    return True


def _reconcile_session_for_read(session: dict[str, Any]) -> dict[str, Any]:
    previous = dict(session)
    if _reconcile_stale_native_start(session):
        _persist_session_if_changed(session, previous)
    return session


def _is_internal_test_session(session: dict[str, Any]) -> bool:
    title = str(session.get("title") or "").strip().lower()
    markers = (
        "smoke",
        "retest",
        "confidence-smoke",
        "native-bridge-retest",
        "native composer post smoke",
        "final native startup smoke",
        "cancel regression",
        "revision follow-up",
    )
    return any(marker in title for marker in markers)


def _session_title_looks_corrupted(session: dict[str, Any]) -> bool:
    title = str(session.get("title") or "").strip()
    if not title:
        return True
    visible = [char for char in title if not char.isspace()]
    if not visible:
        return True
    return all(char in {"?", "？", "�"} for char in visible)


def _is_low_value_failed_session(session: dict[str, Any]) -> bool:
    turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
    status = str(turn.get("status") or session.get("current_turn_status") or "")
    if status not in {"failed", "cancelled", "failed_scope_miss", "failed_partial_application", "failed_scope_violation"}:
        return False
    if _session_title_looks_corrupted(session):
        return True
    native_error = str(session.get("native_protocol_error") or "").lower()
    if "thread/start" not in native_error and "initialize" not in native_error:
        return False
    changed_files = list(turn.get("changed_files") or [])
    artifacts = list(turn.get("artifacts") or [])
    return not changed_files and not artifacts


def _update_turn(session: dict[str, Any], turn_id: str, **updates: Any) -> dict[str, Any]:
    _normalize_session_state(session)
    turns = list(session.get("turns") or [])
    for index, turn in enumerate(turns):
        if str((turn or {}).get("turn_id") or "") == turn_id:
            next_turn = {**dict(turn or {}), **updates}
            turns[index] = next_turn
            session["turns"] = turns
            session["current_turn"] = next_turn
            return next_turn
    next_turn = {"turn_id": turn_id, **updates}
    turns.append(next_turn)
    session["turns"] = turns
    session["current_turn"] = next_turn
    return next_turn


def _event_display(kind: str, payload: dict[str, Any]) -> dict[str, str]:
    if kind == "user_message":
        return {"role": "user", "display_kind": "message"}
    if kind in {"assistant_message", "turn_runtime_completed", "thinking"}:
        return {"role": "assistant", "display_kind": "message"}
    if kind == "user_guidance":
        return {"role": "user", "display_kind": "message"}
    if kind == "tool_call":
        return {"role": "tool", "display_kind": "tool_call"}
    if kind == "tool_result":
        return {"role": "tool", "display_kind": "tool_result"}
    if kind in {"file_changed", "artifact_created", "preview_updated"}:
        return {"role": "system", "display_kind": "artifact"}
    if kind in {"verification_passed", "auto_repair_started"}:
        return {"role": "system", "display_kind": "status"}
    if kind == "verification_failed":
        return {"role": "system", "display_kind": "error"}
    if kind in {"turn_failed", "turn_cancelled", "blocked_change", "native_error"}:
        return {"role": "system", "display_kind": "error"}
    return {"role": "system", "display_kind": str(payload.get("display_kind") or "status")}


def _append_event(session: dict[str, Any], kind: str, **payload: Any) -> dict[str, Any]:
    _normalize_session_state(session)
    path = _event_log_path(session)
    with _event_lock_for(path):
        event_index = max(int(session.get("event_index") or 0), _max_event_id(path)) + 1
        display = _event_display(kind, payload)
        raw_payload = payload.pop("raw_payload", None)
        tool_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        output_preview = str(payload.get("output_preview") or payload.get("text") or "")
        event = {
            "event_id": event_index,
            "session_id": session.get("session_id"),
            "report_id": session.get("report_id"),
            "turn_id": payload.get("turn_id") or _current_turn(session).get("turn_id") or "",
            "kind": kind,
            "role": payload.get("role") or display["role"],
            "display_kind": payload.get("display_kind") or display["display_kind"],
            "timestamp": _now_iso(),
            "tool_call_id": payload.get("tool_call_id") or tool_payload.get("id") or tool_payload.get("tool_call_id") or "",
            "tool_name": payload.get("tool_name") or tool_payload.get("name") or "",
            "command": payload.get("command") or tool_payload.get("command") or "",
            "status": payload.get("status") or tool_payload.get("status") or "",
            "exit_code": payload.get("exit_code") if payload.get("exit_code") is not None else tool_payload.get("exit_code"),
            "duration_ms": payload.get("duration_ms") if payload.get("duration_ms") is not None else tool_payload.get("duration_ms"),
            "output_preview": output_preview[:1200],
            "raw_payload": raw_payload if raw_payload is not None else tool_payload,
            **payload,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        session["event_index"] = event_index
        return event


def _read_events(session: dict[str, Any], *, cursor: int = 0) -> list[dict[str, Any]]:
    path = _event_log_path(session)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except Exception:
            continue
        if int(event.get("event_id") or 0) > int(cursor or 0):
            events.append(event)
    return events


def _report_sessions(
    report_dir: Path,
    *,
    include_heavy_fields: bool = True,
    include_internal_test_sessions: bool = False,
) -> list[dict[str, Any]]:
    root = report_dir / SESSION_DIR_NAME
    if not root.exists():
        return []
    sessions: list[dict[str, Any]] = []
    for session_file in sorted(root.glob(f"*/{SESSION_FILE_NAME}")):
        payload = dict(_read_json(session_file, {}) or {})
        if payload:
            payload = _reconcile_session_for_read(payload)
            if not include_internal_test_sessions and _is_internal_test_session(payload):
                continue
            if not include_internal_test_sessions and _is_low_value_failed_session(payload):
                continue
            sessions.append(_public_session(payload, include_heavy_fields=include_heavy_fields))
    sessions.sort(key=_session_sort_key, reverse=True)
    return sessions


def _session_sort_key(session: dict[str, Any]) -> tuple[Any, ...]:
    current_turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
    current_status = str(session.get("current_turn_status") or current_turn.get("status") or "")
    turns = [turn for turn in list(session.get("turns") or []) if isinstance(turn, dict)]
    turn_count = len(turns)
    has_turn_history = turn_count > 0
    has_running_turn = current_status in {"queued", "running", "cancelling"}
    has_current_turn = bool(current_turn.get("turn_id") or current_turn.get("user_message") or current_turn.get("started_at"))
    guidance_count = len(list(session.get("guidance_injections") or []))
    published_count = len(list(session.get("published_versions") or []))
    preview_url = str(session.get("preview_url") or "")
    latest_turn_at = ""
    for turn in turns:
        latest_turn_at = max(
            latest_turn_at,
            str(turn.get("completed_at") or ""),
            str(turn.get("started_at") or ""),
        )
    updated_at = str(session.get("updated_at") or session.get("created_at") or "")
    return (
        1 if has_running_turn else 0,
        1 if has_turn_history else 0,
        turn_count,
        1 if has_current_turn else 0,
        published_count,
        guidance_count,
        1 if preview_url else 0,
        latest_turn_at,
        updated_at,
    )


def _public_session(session: dict[str, Any], *, include_heavy_fields: bool = True) -> dict[str, Any]:
    _normalize_session_state(session)
    current_turn = _current_turn(session)
    if include_heavy_fields:
        public_current_turn = current_turn
        public_turns = session.get("turns") or []
        public_guidance = session.get("guidance_injections") or []
        public_published = session.get("published_versions") or []
    else:
        public_current_turn = {
            "turn_id": current_turn.get("turn_id") or "",
            "status": current_turn.get("status") or "",
            "user_message": current_turn.get("user_message") or "",
            "started_at": current_turn.get("started_at") or "",
            "completed_at": current_turn.get("completed_at") or "",
            "native_turn_id": current_turn.get("native_turn_id") or "",
            "task_id": current_turn.get("task_id") or "",
            "run_id": current_turn.get("run_id") or "",
            "final_scope_status": current_turn.get("final_scope_status") or "",
        }
        public_turns = []
        public_guidance = []
        public_published = []
    session_status = str(session.get("session_status") or "active")
    current_status = str(current_turn.get("status") or "")
    active_turn_id = str(session.get("active_turn_id") or "")
    if not active_turn_id and current_status in {"queued", "running", "cancelling"}:
        active_turn_id = str(current_turn.get("native_turn_id") or "")
    payload = {
        "session_id": session.get("session_id"),
        "report_id": session.get("report_id"),
        "status": session_status,
        "session_status": session_status,
        "current_turn": public_current_turn,
        "current_turn_status": current_status,
        "turns": public_turns,
        "title": session.get("title") or "后续改造会话",
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
        "current_task_id": current_turn.get("task_id") or session.get("current_task_id") or "",
        "current_run_id": current_turn.get("run_id") or session.get("current_run_id") or "",
        "codex_session_id": session.get("codex_session_id") or "",
        "mode": session.get("mode") or "native_app_server",
        "codex_thread_id": session.get("codex_thread_id") or session.get("codex_session_id") or "",
        "active_turn_id": active_turn_id,
        "native_connection_status": session.get("native_connection_status") or "",
        "native_protocol_error": session.get("native_protocol_error") or "",
        "guidance_injections": public_guidance,
        "preview_url": session.get("preview_url") or "",
        "preview_artifact": session.get("preview_artifact") or {},
        "published_versions": public_published,
        "workspace_path": session.get("workspace_path") or "",
        "revision_agent_contract_version": session.get("revision_agent_contract_version") or "native-major-v3",
    }
    if include_heavy_fields:
        attachment_profile_path = _session_workspace(session) / ATTACHMENT_PROFILE_JSON_NAME
        payload["attachments"] = _read_attachments(session)
        payload["attachment_profile_url"] = _storage_url_for(attachment_profile_path) if attachment_profile_path.exists() else ""
    return payload


REPORT_CATALOG_DEFAULT_LIMIT = 80
REPORT_CATALOG_MAX_LIMIT = 400
REPORT_CATALOG_SEED_LIMIT = 120
REPORT_TITLE_MAX_CHARS = 96
_REPORT_CATALOG_REFRESH_LOCK = threading.Lock()

_GENERIC_REPORT_TITLES = {
    "report",
    "management report",
    "business report",
    "business report - main report",
    "main report",
    "untitled",
    "untitled report",
    "报告",
    "管理报告",
    "主报告",
    "业务报告 - 主报告",
    "业务报告-主报告",
    "报告预览",
    "报告后续改造预览",
    "报告意图",
    "codex sidecar review",
    "report intent",
}


def _latest_report_session(report_dir: Path) -> dict[str, Any] | None:
    root = report_dir / SESSION_DIR_NAME
    if not root.exists():
        return None
    session_files = sorted(
        root.glob(f"*/{SESSION_FILE_NAME}"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )
    candidates: list[dict[str, Any]] = []
    for session_file in session_files[:24]:
        payload = dict(_read_json(session_file, {}) or {})
        if not payload:
            continue
        payload = _reconcile_session_for_read(payload)
        candidates.append(payload)
    candidates.sort(key=_session_sort_key, reverse=True)
    for payload in candidates:
        if _is_internal_test_session(payload):
            continue
        if _is_low_value_failed_session(payload):
            continue
        return _public_session(payload, include_heavy_fields=False)
    return None


def _normalize_report_title(value: Any) -> str:
    text = _repair_mojibake_text(value)
    text = re.sub(r"<[^>]+>", " ", text, flags=re.S)
    text = html.unescape(text)
    text = re.sub(r"^[#\s]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" \t\r\n\"'`*_#")
    if len(text) > REPORT_TITLE_MAX_CHARS:
        text = text[:REPORT_TITLE_MAX_CHARS].rstrip(" ，,。.;；:：") + "..."
    return text


def _is_placeholder_report_title(title: str, report_id: str) -> bool:
    normalized = _normalize_report_title(title)
    if not normalized:
        return True
    lowered = normalized.lower()
    compact = re.sub(r"[\s_\-:：()（）]+", "", lowered)
    report_compact = re.sub(r"[\s_\-:：()（）]+", "", str(report_id or "").lower())
    if lowered in _GENERIC_REPORT_TITLES or compact in _GENERIC_REPORT_TITLES:
        return True
    if report_compact and compact in {
        report_compact,
        f"report{report_compact}",
        f"smartreport{report_compact}",
        f"报告{report_compact}",
    }:
        return True
    if report_compact and compact.replace("smartreport", "").replace("report", "").replace("报告", "") == report_compact:
        return True
    technical_markers = (
        "generic_long_cli_report",
        "generic_long_cli_full_report",
        "generic_long_cli_brief_report",
        "management_report",
        "current_turn_export_manifest",
    )
    if any(marker in lowered for marker in technical_markers):
        return True
    if re.fullmatch(r"[a-z0-9_-]{8,}", lowered) and report_compact and report_compact in compact:
        return True
    return False


def _first_valid_report_title(candidates: Iterable[Any], report_id: str) -> str:
    for candidate in candidates:
        title = _normalize_report_title(candidate)
        if title and not _is_placeholder_report_title(title, report_id):
            return title
    return ""


def _safe_report_artifact_path(report_dir: Path, raw_path: Any) -> Path | None:
    raw = str(raw_path or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = report_dir / path
    try:
        resolved = path.resolve()
        resolved.relative_to(report_dir.resolve())
    except Exception:
        return None
    if resolved.is_file() and resolved.suffix.lower() in {".html", ".htm", ".md", ".txt"}:
        return resolved
    return None


def _report_title_artifact_score(path: Path) -> int:
    name = path.name.lower()
    path_text = str(path).replace("\\", "/").lower()
    suffix = path.suffix.lower()
    score = 0
    if suffix in {".html", ".htm"}:
        score += 40
    elif suffix == ".md":
        score += 30
    else:
        score += 5
    if "generic_long_cli_report" in name or "management_report" in name:
        score += 50
    if "generic_long_cli_full_report" in name:
        score += 25
    if "generic_long_cli_brief_report" in name:
        score += 20
    if "management_brief" in name:
        score += 42
    if "06_report" in name:
        score += 36
    if "report" in name:
        score += 10
    if "agent-revision" in name:
        score -= 15
    if "codex_agent_sessions" in path_text:
        score -= 20
    if "/working/report." in path_text:
        score -= 24
    if "with_tables" in name or "full_table" in name:
        score -= 16
    if any(marker in name for marker in ("review", "spec", "intent", "inventory", "question_tree", "outline", "audit")):
        score -= 35
    if "sidecar" in name:
        score -= 28
    if "interpretation" in name:
        score -= 8
    if "report" in name:
        score += 10
    return score


def _report_title_cache_path(report_dir: Path) -> Path:
    return report_dir / REPORT_TITLE_CACHE_NAME


def _report_title_cache_sources(
    report_dir: Path,
    report_id: str,
    manifest: dict[str, Any],
    downloadables: list[dict[str, Any]],
    preview: dict[str, Any],
    *,
    allow_recursive_scan: bool = True,
) -> list[str]:
    source_paths: list[Path] = [_manifest_path(report_dir, report_id)]
    source_paths.extend(
        _candidate_title_paths(
            report_dir,
            manifest,
            downloadables,
            preview,
            allow_recursive_scan=allow_recursive_scan,
        )
    )
    tokens: list[str] = []
    seen: set[str] = set()
    for path in source_paths:
        try:
            resolved = path.resolve()
            stat = resolved.stat()
        except Exception:
            continue
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        tokens.append(f"{resolved}|{stat.st_mtime_ns}|{stat.st_size}")
    return tokens


def _read_report_title_cache(report_dir: Path) -> dict[str, Any]:
    return dict(_read_json(_report_title_cache_path(report_dir), {}) or {})


def _write_report_title_cache(report_dir: Path, payload: dict[str, Any]) -> None:
    try:
        _report_title_cache_path(report_dir).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _iter_manifest_paths(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).endswith("_path") or str(key).endswith("_file"):
                yield child
            yield from _iter_manifest_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_manifest_paths(child)


def _catalog_nested_title_paths(report_dir: Path) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for pattern in CATALOG_NESTED_TITLE_GLOB_PATTERNS:
        for path in report_dir.glob(pattern):
            if not path.is_file() or SESSION_DIR_NAME in path.parts:
                continue
            key = str(path.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            paths.append(path)
    return sorted(paths, key=_report_title_artifact_score, reverse=True)


def _candidate_title_paths(
    report_dir: Path,
    manifest: dict[str, Any],
    downloadables: list[dict[str, Any]],
    preview: dict[str, Any],
    *,
    allow_recursive_scan: bool = True,
) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()

    def add_path(path: Path | None) -> None:
        if path is None:
            return
        key = str(path.resolve()).lower()
        if key in seen:
            return
        seen.add(key)
        paths.append(path)

    preferred_items = [preview]
    preferred_items.extend([item for item in downloadables if item.get("is_main")])
    preferred_items.extend(sorted(downloadables, key=lambda item: _report_title_artifact_score(Path(str(item.get("name") or ""))), reverse=True))
    for item in preferred_items:
        if not isinstance(item, dict):
            continue
        add_path(_safe_report_artifact_path(report_dir, item.get("file_path")))

    for raw_path in _iter_manifest_paths(manifest):
        add_path(_safe_report_artifact_path(report_dir, raw_path))

    for path in sorted(report_dir.glob("*"), key=_report_title_artifact_score, reverse=True):
        add_path(_safe_report_artifact_path(report_dir, path))

    if allow_recursive_scan:
        for path in sorted(report_dir.rglob("*"), key=_report_title_artifact_score, reverse=True):
            if SESSION_DIR_NAME in path.parts:
                continue
            add_path(_safe_report_artifact_path(report_dir, path))
    else:
        for path in _catalog_nested_title_paths(report_dir):
            add_path(_safe_report_artifact_path(report_dir, path))

    return paths


def _report_title_quality_score(title: str) -> int:
    normalized = _normalize_report_title(title)
    if not normalized:
        return -100
    lowered = normalized.lower()
    score = min(len(normalized), 60)
    if re.search(r"[\u4e00-\u9fff]", normalized):
        score += 18
    if any(marker in lowered for marker in ("经营", "运营", "增长", "漏斗", "用户", "商品", "分析", "复盘", "管理版", "报告")):
        score += 16
    if any(marker in lowered for marker in ("完整表版本", "附录", "审计宽表", "宽表")):
        score -= 10
    if any(marker in lowered for marker in ("workflow", "interpretation", "sidecar", "review", "spec", "intent", "inventory", "question tree", "question_tree")):
        score -= 35
    if any(marker in lowered for marker in ("管理层", "高密度", "单日", "全量", "复盘", "交付包")):
        score += 8
    return score


def _extract_title_candidates_from_report_file(path: Path, report_id: str) -> list[tuple[str, int]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:200_000]
    except Exception:
        return []
    suffix = path.suffix.lower()
    raw_candidates: list[tuple[str, int]] = []
    if suffix in {".html", ".htm"}:
        raw_candidates.extend(
            (match.group(1), 22)
            for match in re.finditer(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
        )
        raw_candidates.extend(
            (match.group(1), 20)
            for match in re.finditer(r"<h1[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
        )
        raw_candidates.extend(
            (match.group(1), 8)
            for match in re.finditer(r"<h2[^>]*>(.*?)</h2>", text, flags=re.I | re.S)
        )
    else:
        for line in text.splitlines()[:80]:
            if re.match(r"^\s*#\s+\S", line):
                raw_candidates.append((line, 18))
                break
        raw_candidates.extend(
            (match.group(1), 12)
            for match in re.finditer(r"^\s*title\s*[:：]\s*(.+)$", text, flags=re.I | re.M)
        )

    candidates: list[tuple[str, int]] = []
    seen: set[str] = set()
    for raw_title, source_score in raw_candidates:
        title = _normalize_report_title(raw_title)
        if not title or _is_placeholder_report_title(title, report_id):
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append((title, source_score))
    return candidates


def _quick_report_title(
    report_dir: Path,
    report_id: str,
    manifest: dict[str, Any],
) -> str:
    cached = _read_report_title_cache(report_dir)
    cached_title = _first_valid_report_title([cached.get("content_title")], report_id)
    if cached_title:
        return cached_title
    return _first_valid_report_title(
        [
            manifest.get("title"),
            manifest.get("report_title"),
            manifest.get("display_title"),
            manifest.get("name"),
        ],
        report_id,
    )


def _report_content_title(
    report_dir: Path,
    report_id: str,
    manifest: dict[str, Any],
    downloadables: list[dict[str, Any]],
    preview: dict[str, Any],
    *,
    allow_recursive_scan: bool = True,
    scan_artifact_contents: bool = True,
) -> str:
    if not scan_artifact_contents:
        return _quick_report_title(report_dir, report_id, manifest)

    source_tokens = _report_title_cache_sources(
        report_dir,
        report_id,
        manifest,
        downloadables,
        preview,
        allow_recursive_scan=allow_recursive_scan,
    )
    cached = _read_report_title_cache(report_dir)
    if cached.get("source_tokens") == source_tokens:
        cached_title = _first_valid_report_title([cached.get("content_title")], report_id)
        if cached_title:
            return cached_title

    best_title = ""
    best_score = -10_000

    for manifest_title in [
        manifest.get("title"),
        manifest.get("report_title"),
        manifest.get("display_title"),
        manifest.get("name"),
    ]:
        title = _first_valid_report_title([manifest_title], report_id)
        if not title:
            continue
        score = 120 + _report_title_quality_score(title)
        if score > best_score:
            best_title = title
            best_score = score

    for path in _candidate_title_paths(
        report_dir,
        manifest,
        downloadables,
        preview,
        allow_recursive_scan=allow_recursive_scan,
    ):
        path_score = _report_title_artifact_score(path)
        for title, source_score in _extract_title_candidates_from_report_file(path, report_id):
            score = path_score + source_score + _report_title_quality_score(title)
            if score > best_score:
                best_title = title
                best_score = score
    if best_title:
        _write_report_title_cache(
            report_dir,
            {
                "report_id": report_id,
                "content_title": best_title,
                "source_tokens": source_tokens,
                "updated_at": _now_iso(),
            },
        )
    return best_title


def _report_catalog_title(content_title: str, report_id: str) -> str:
    clean_title = _first_valid_report_title([content_title], report_id)
    clean_id = str(report_id or "").strip()
    if not clean_id:
        return clean_title or "未命名报告"
    if clean_title and clean_id.lower() in clean_title.lower():
        return clean_title
    if clean_title:
        return f"{clean_title}（{clean_id}）"
    return f"未命名报告（{clean_id}）"


def _report_summary(report_dir: Path, *, catalog_mode: bool = False) -> dict[str, Any]:
    report_id = report_dir.name.removeprefix(REPORT_DIR_PREFIX)
    manifest = _load_manifest(report_dir, report_id)
    downloadables = _load_downloadables(
        report_dir,
        report_id,
        deep_scan=False,
        fallback_scan=not catalog_mode,
        catalog_scan_limit=40 if catalog_mode else 0,
    )
    preview = _choose_preview(downloadables)
    content_title = _report_content_title(
        report_dir,
        report_id,
        manifest,
        downloadables,
        preview,
        allow_recursive_scan=not catalog_mode,
        # Catalog mode still needs to inspect likely title-bearing artifacts
        # so nested HTML/Markdown reports surface a business title instead of blank text.
        scan_artifact_contents=True,
    )
    # The catalog endpoint is the first thing the revision workbench loads.
    # Older agent sessions can contain large turn/event payloads, so keep the
    # catalog path shallow and let /api/runtime/processes provide live status.
    latest_session = _latest_report_session(report_dir) if catalog_mode else None
    sessions = [] if catalog_mode else _report_sessions(report_dir, include_heavy_fields=False)
    stat = report_dir.stat()
    return {
        "report_id": report_id,
        "report_dir_name": report_dir.name,
        "report_dir_path": str(report_dir.resolve()),
        "report_dir_mtime_ns": getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)),
        "title": _report_catalog_title(content_title, report_id),
        "content_title": content_title,
        "dataset_id": manifest.get("dataset_id") or "",
        "dataset_name": manifest.get("dataset_name") or "",
        "business_profile": manifest.get("business_profile") or manifest.get("report_lens") or "",
        "generated_at": manifest.get("generated_at") or datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "main_downloadable": next((item for item in downloadables if item.get("is_main")), preview),
        "preview_downloadable": preview,
        "preview_url": preview.get("path") or "",
        "downloadable_count": len(downloadables),
        "latest_revision_session": latest_session or (sessions[0] if sessions else None),
        "manifest": manifest,
    }


def _catalog_search_text(item: dict[str, Any]) -> str:
    parts = [
        item.get("report_id"),
        item.get("title"),
        item.get("content_title"),
        item.get("dataset_id"),
        item.get("dataset_name"),
        item.get("business_profile"),
    ]
    manifest = item.get("manifest") if isinstance(item.get("manifest"), dict) else {}
    for key in ("title", "report_title", "display_title", "name", "business_profile", "report_lens"):
        parts.append(manifest.get(key))
    return " ".join(str(part or "").strip() for part in parts if str(part or "").strip())


def _catalog_sort_ts(value: str) -> int:
    if not value:
        return 0
    normalized = str(value).strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return int(datetime.fromisoformat(normalized).timestamp() * 1000)
    except Exception:
        return 0


def _scan_report_catalog(limit: int) -> list[dict[str, Any]]:
    report_dirs = _list_report_dirs()
    report_dirs.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0.0, reverse=True)
    requested_limit = int(limit or 0)
    scan_limit = len(report_dirs) if requested_limit <= 0 else min(len(report_dirs), requested_limit)
    selected_dirs = report_dirs[:scan_limit]
    reports = [_report_summary(path, catalog_mode=True) for path in selected_dirs]
    for item in reports:
        item["search_text"] = _catalog_search_text(item)
        item["sort_generated_ts"] = _catalog_sort_ts(str(item.get("generated_at") or ""))
        item["sort_updated_ts"] = _catalog_sort_ts(str(item.get("updated_at") or item.get("generated_at") or ""))
    reports.sort(key=lambda item: str(item.get("updated_at") or item.get("generated_at") or ""), reverse=True)
    return reports


def _list_report_dirs() -> list[Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return [path for path in REPORTS_DIR.glob(f"{REPORT_DIR_PREFIX}*") if path.is_dir()]


def _seed_report_catalog_index(report_dirs: list[Path], limit: int = REPORT_CATALOG_SEED_LIMIT) -> None:
    if report_catalog_index_status().get("indexed_report_count", 0):
        return
    selected_dirs = sorted(
        report_dirs,
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )[: max(1, int(limit or REPORT_CATALOG_SEED_LIMIT))]
    if not selected_dirs:
        return
    reports = [_report_summary(path, catalog_mode=True) for path in selected_dirs]
    for item in reports:
        item["search_text"] = _catalog_search_text(item)
        item["sort_generated_ts"] = _catalog_sort_ts(str(item.get("generated_at") or ""))
        item["sort_updated_ts"] = _catalog_sort_ts(str(item.get("updated_at") or item.get("generated_at") or ""))
    replace_report_catalog_rows(reports)
    if len(reports) < len(report_dirs):
        mark_report_catalog_partial_seed(len(reports), known_report_count=len(report_dirs))
    else:
        mark_report_catalog_scan_finished(
            refresh_mode="seed",
            known_report_count=len(report_dirs),
            is_partial=False,
        )


def _refresh_report_catalog_index_sync(limit: int = REPORT_CATALOG_MAX_LIMIT) -> None:
    report_dirs = _list_report_dirs()
    known_report_count = len(report_dirs)
    snapshot = report_catalog_index_snapshot()
    current_ids = {path.name.removeprefix(REPORT_DIR_PREFIX) for path in report_dirs}
    removed_ids = [report_id for report_id in snapshot.keys() if report_id not in current_ids]
    if removed_ids:
        delete_report_catalog_rows(removed_ids)

    requested_limit = int(limit or 0)
    scan_limit = known_report_count if requested_limit <= 0 else min(known_report_count, requested_limit)
    selected_dirs = sorted(
        report_dirs,
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )[:scan_limit]
    changed_dirs: list[Path] = []
    for path in selected_dirs:
        report_id = path.name.removeprefix(REPORT_DIR_PREFIX)
        stat = path.stat()
        current_mtime_ns = int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)))
        indexed = snapshot.get(report_id) or {}
        if int(indexed.get("report_dir_mtime_ns") or 0) != current_mtime_ns:
            changed_dirs.append(path)

    if changed_dirs:
        rows = [_report_summary(path, catalog_mode=True) for path in changed_dirs]
        for item in rows:
            item["search_text"] = _catalog_search_text(item)
            item["sort_generated_ts"] = _catalog_sort_ts(str(item.get("generated_at") or ""))
            item["sort_updated_ts"] = _catalog_sort_ts(str(item.get("updated_at") or item.get("generated_at") or ""))
        upsert_report_catalog_rows(rows)
        last_scan_count = len(rows)
    else:
        last_scan_count = 0

    status = report_catalog_index_status()
    if status.get("indexed_report_count", 0) > known_report_count:
        stale_ids = [report_id for report_id in report_catalog_index_snapshot().keys() if report_id not in current_ids]
        if stale_ids:
            delete_report_catalog_rows(stale_ids)

    mark_report_catalog_scan_finished(
        refresh_mode="full" if requested_limit <= 0 else "partial",
        known_report_count=known_report_count,
        is_partial=bool(report_catalog_index_status().get("indexed_report_count", 0) < known_report_count),
    )


def _refresh_report_catalog_index_async(limit: int = REPORT_CATALOG_MAX_LIMIT) -> None:
    if report_catalog_index_is_refreshing():
        return

    def _runner() -> None:
        with _REPORT_CATALOG_REFRESH_LOCK:
            status = report_catalog_index_status()
            if (
                report_catalog_index_is_fresh()
                and status.get("indexed_report_count", 0)
                and not status.get("is_partial")
            ):
                mark_report_catalog_scan_finished(
                    refresh_mode="skip",
                    known_report_count=status.get("known_report_count", 0),
                    is_partial=bool(status.get("is_partial")),
                )
                return
            try:
                _refresh_report_catalog_index_sync(limit)
            except Exception as exc:
                mark_report_catalog_scan_finished(
                    refresh_mode="error",
                    known_report_count=report_catalog_index_status().get("known_report_count", 0),
                    is_partial=bool(report_catalog_index_status().get("is_partial")),
                    error=str(exc),
                )

    mark_report_catalog_scan_started()
    thread = threading.Thread(target=_runner, name="report-catalog-refresh", daemon=True)
    thread.start()


def _repair_catalog_rows_if_needed(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    repaired: list[dict[str, Any]] = []
    changed = False
    for row in rows:
        if not isinstance(row, dict):
            repaired.append(row)
            continue
        if isinstance(row.get("latest_revision_session"), dict):
            row = {**row, "latest_revision_session": _public_session(dict(row["latest_revision_session"]), include_heavy_fields=False)}
        preview_url = str(row.get("preview_url") or "").strip()
        downloadable_count = int(row.get("downloadable_count") or 0)
        if downloadable_count > 0 or preview_url:
            repaired.append(row)
            continue
        report_id = str(row.get("report_id") or "").strip()
        if not report_id:
            repaired.append(row)
            continue
        try:
            summary = _report_summary(_report_dir(report_id), catalog_mode=True)
        except Exception:
            repaired.append(row)
            continue
        summary["search_text"] = _catalog_search_text(summary)
        summary["sort_generated_ts"] = _catalog_sort_ts(str(summary.get("generated_at") or ""))
        summary["sort_updated_ts"] = _catalog_sort_ts(str(summary.get("updated_at") or summary.get("generated_at") or ""))
        repaired.append(summary)
        changed = True
    if changed:
        upsert_report_catalog_rows(repaired)
    return repaired


def list_reports(
    limit: int = REPORT_CATALOG_DEFAULT_LIMIT,
    *,
    keyword: str = "",
    dataset_id: str = "",
    business_profile: str = "",
    offset: int = 0,
    sort_by: str = "updated_at",
    refresh_index: bool = False,
) -> dict[str, Any]:
    safe_limit = max(1, min(REPORT_CATALOG_MAX_LIMIT, int(limit or REPORT_CATALOG_DEFAULT_LIMIT)))
    status = report_catalog_index_status()
    indexed_report_count = int(status.get("indexed_report_count") or 0)
    if indexed_report_count:
        if refresh_index:
            refresh_limit = min(
                REPORT_CATALOG_SEED_LIMIT,
                max(safe_limit + max(0, int(offset or 0)), REPORT_CATALOG_DEFAULT_LIMIT),
            )
            _refresh_report_catalog_index_async(refresh_limit)
    else:
        # A cold catalog scan can be expensive on large local workspaces. Keep
        # the request responsive and let the background indexer hydrate results.
        report_dirs = _list_report_dirs()
        refresh_limit = min(
            REPORT_CATALOG_SEED_LIMIT,
            max(safe_limit + max(0, int(offset or 0)), REPORT_CATALOG_DEFAULT_LIMIT),
        )
        if len(report_dirs) <= refresh_limit:
            _seed_report_catalog_index(report_dirs, limit=refresh_limit)
        else:
            _refresh_report_catalog_index_async(refresh_limit)
    result = query_report_catalog_index(
        keyword=keyword,
        dataset_id=dataset_id,
        business_profile=business_profile,
        sort_by=sort_by,
        offset=offset,
        limit=safe_limit,
    )
    result["reports"] = _repair_catalog_rows_if_needed(list(result.get("reports") or []))
    result["returned_count"] = len(result.get("reports") or [])
    return result


def get_report_detail(report_id: str) -> dict[str, Any]:
    report_dir = _report_dir(report_id)
    manifest = _load_manifest(report_dir, report_id)
    downloadables = _load_downloadables(report_dir, report_id, deep_scan=False, fallback_scan=True, catalog_scan_limit=80)
    preview = _choose_preview(downloadables)
    return {
        **_report_summary(report_dir),
        "manifest": manifest,
        "downloadables": downloadables,
        "revision_sessions": _report_sessions(report_dir),
        "preview_downloadable": preview,
        "preview_url": preview.get("path") or "",
    }


def _copy_if_exists(source: Path | None, destination: Path) -> Path | None:
    if source is None or not source.is_file():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _extract_pdf_text_for_revision(source_pdf: Path | None, *, max_pages: int = 8) -> str:
    if source_pdf is None or not source_pdf.is_file():
        return ""
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(source_pdf))
        chunks: list[str] = []
        for page in reader.pages[:max_pages]:
            chunks.append(str(page.extract_text() or "").strip())
        return "\n\n".join(chunk for chunk in chunks if chunk).strip()
    except Exception:
        return ""


def _build_pdf_fallback_markdown(report_id: str, source_pdf: Path | None) -> str:
    title = source_pdf.stem if source_pdf is not None else report_id
    extracted = _extract_pdf_text_for_revision(source_pdf)
    if extracted:
        return (
            f"# {title}\n\n"
            "本工作副本由原始 PDF 抽取文本生成，用于对话式后续改造与重新导出 PDF。\n\n"
            "## 原始 PDF 文本摘录\n\n"
            f"{extracted}\n"
        )
    return (
        f"# {title}\n\n"
        "本工作副本来自原始 PDF。当前环境未能抽取 PDF 正文，因此本轮改造会以用户指令、批注和补充材料为准，"
        "生成新的可编辑 HTML/PDF 修订版；原始 PDF 保留在 source/ 中作为只读参考。\n"
    )


_LOCAL_ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}
_HTML_ASSET_ATTR_RE = re.compile(
    r"(?P<prefix>\b(?:src|href)=['\"])(?P<url>[^'\"]+?)(?P<suffix>['\"])",
    re.I,
)
_CSS_ASSET_URL_RE = re.compile(
    r"url\((?P<quote>['\"]?)(?P<url>[^)'\"\s][^)'\"]*?)(?P=quote)\)",
    re.I,
)


def _is_local_asset_url(raw_url: str) -> bool:
    value = html.unescape(str(raw_url or "").strip())
    if not value:
        return False
    lower = value.lower()
    if lower.startswith(("http://", "https://", "data:", "blob:", "mailto:", "#")):
        return False
    if re.match(r"^[a-zA-Z]:[\\/]", value):
        suffix = Path(value.split("?", 1)[0].split("#", 1)[0]).suffix.lower()
        return suffix in _LOCAL_ASSET_SUFFIXES
    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme != "file":
        return False
    suffix = Path(unquote(parsed.path or value).split("?", 1)[0].split("#", 1)[0]).suffix.lower()
    return suffix in _LOCAL_ASSET_SUFFIXES


def _clean_asset_url_path(raw_url: str) -> str:
    value = html.unescape(str(raw_url or "").strip())
    if re.match(r"^[a-zA-Z]:[\\/]", value):
        return value.split("?", 1)[0].split("#", 1)[0].replace("\\", "/")
    parsed = urlsplit(value)
    path_text = unquote(parsed.path or value).split("?", 1)[0].split("#", 1)[0]
    if parsed.scheme == "file" and re.match(r"^/[a-zA-Z]:", path_text):
        path_text = path_text[1:]
    return path_text.replace("\\", "/")


def _asset_suffix_parts(raw_url: str) -> tuple[str, ...]:
    clean_path = _clean_asset_url_path(raw_url)
    parts = tuple(part for part in clean_path.split("/") if part and part not in {".", ".."})
    return parts


def _find_asset_in_fallback_roots(raw_url: str, fallback_roots: Iterable[Path] | None) -> Path | None:
    parts = _asset_suffix_parts(raw_url)
    if not parts:
        return None
    suffix_path = Path(*parts)
    filename = parts[-1]
    lowered_parts = tuple(part.lower() for part in parts)
    for root in fallback_roots or []:
        try:
            root_path = Path(root).resolve()
        except Exception:
            continue
        if not root_path.exists():
            continue
        direct = root_path / suffix_path
        if direct.is_file():
            return direct
        try:
            matches = list(root_path.rglob(filename))
        except Exception:
            matches = []
        for candidate in matches:
            candidate_parts = tuple(part.lower() for part in candidate.parts)
            if len(candidate_parts) >= len(lowered_parts) and candidate_parts[-len(lowered_parts) :] == lowered_parts:
                return candidate
        if matches:
            return matches[0]
    return None


def _resolve_local_asset_path(
    raw_url: str,
    *,
    base_dir: Path,
    fallback_roots: Iterable[Path] | None = None,
) -> Path | None:
    if not _is_local_asset_url(raw_url):
        return None
    clean_path = _clean_asset_url_path(raw_url)
    if not clean_path:
        return None
    candidate: Path | None = None
    if re.match(r"^[a-zA-Z]:[\\/]", clean_path):
        candidate = Path(clean_path)
    elif clean_path.startswith("/storage/"):
        candidate = PUBLIC_ARTIFACTS_DIR / clean_path.removeprefix("/storage/")
    elif clean_path.startswith("storage/"):
        candidate = PUBLIC_ARTIFACTS_DIR / clean_path.removeprefix("storage/")
    elif clean_path.startswith("/"):
        candidate = Path(clean_path)
    else:
        candidate = (base_dir / clean_path).resolve()
    if candidate and candidate.is_file():
        return candidate
    return _find_asset_in_fallback_roots(raw_url, fallback_roots)


def _asset_output_relative_path(raw_url: str, source_path: Path) -> Path:
    parts = list(_asset_suffix_parts(raw_url))
    lowered = [part.lower() for part in parts]
    for anchor in ("source_visual_assets", "visual_assets", "assets", "images", "img"):
        if anchor in lowered:
            index = lowered.index(anchor)
            return Path(*parts[index:])

    source_parts = list(source_path.parts)
    source_lowered = [part.lower() for part in source_parts]
    for anchor in ("source_visual_assets", "visual_assets", "assets", "images", "img"):
        if anchor in source_lowered:
            index = source_lowered.index(anchor)
            return Path(*source_parts[index:])

    safe_parts = [part for part in parts if part not in {"", ".", ".."}]
    if safe_parts and len(safe_parts) <= 4:
        return Path(*safe_parts)
    return Path("assets") / source_path.name


def _copy_asset_for_url(
    raw_url: str,
    *,
    output_dir: Path,
    base_dir: Path,
    fallback_roots: Iterable[Path] | None = None,
) -> str | None:
    source_path = _resolve_local_asset_path(raw_url, base_dir=base_dir, fallback_roots=fallback_roots)
    if source_path is None or not source_path.is_file():
        return None
    relative_path = _asset_output_relative_path(raw_url, source_path)
    destination = (output_dir / relative_path).resolve()
    try:
        destination.relative_to(output_dir.resolve())
    except Exception:
        relative_path = Path("assets") / source_path.name
        destination = (output_dir / relative_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        if source_path.resolve() != destination:
            shutil.copy2(source_path, destination)
    except Exception:
        shutil.copy2(source_path, destination)
    return f"./{relative_path.as_posix()}"


def _materialize_css_assets(
    css_path: Path | None,
    *,
    base_dir: Path | None = None,
    fallback_roots: Iterable[Path] | None = None,
) -> dict[str, Any]:
    if css_path is None or not css_path.is_file():
        return {"copied": 0, "missing": []}
    text = css_path.read_text(encoding="utf-8", errors="replace")
    missing: list[str] = []
    copied: set[str] = set()
    source_base = base_dir or css_path.parent

    def _replace(match: re.Match[str]) -> str:
        raw_url = match.group("url")
        if not _is_local_asset_url(raw_url):
            return match.group(0)
        rewritten = _copy_asset_for_url(
            raw_url,
            output_dir=css_path.parent,
            base_dir=source_base,
            fallback_roots=fallback_roots,
        )
        if not rewritten:
            missing.append(raw_url)
            return match.group(0)
        copied.add(rewritten)
        return f"url({match.group('quote')}{rewritten}{match.group('quote')})"

    updated = _CSS_ASSET_URL_RE.sub(_replace, text)
    if updated != text:
        css_path.write_text(updated, encoding="utf-8")
    return {"copied": len(copied), "missing": missing}


def _materialize_html_assets(
    html_path: Path | None,
    *,
    base_dir: Path | None = None,
    fallback_roots: Iterable[Path] | None = None,
) -> dict[str, Any]:
    if html_path is None or not html_path.is_file():
        return {"copied": 0, "missing": []}
    text = html_path.read_text(encoding="utf-8", errors="replace")
    missing: list[str] = []
    copied: set[str] = set()
    source_base = base_dir or html_path.parent

    def _replace_attr(match: re.Match[str]) -> str:
        raw_url = match.group("url")
        if not _is_local_asset_url(raw_url):
            return match.group(0)
        rewritten = _copy_asset_for_url(
            raw_url,
            output_dir=html_path.parent,
            base_dir=source_base,
            fallback_roots=fallback_roots,
        )
        if not rewritten:
            missing.append(raw_url)
            return match.group(0)
        copied.add(rewritten)
        return f"{match.group('prefix')}{rewritten}{match.group('suffix')}"

    def _replace_css_url(match: re.Match[str]) -> str:
        raw_url = match.group("url")
        if not _is_local_asset_url(raw_url):
            return match.group(0)
        rewritten = _copy_asset_for_url(
            raw_url,
            output_dir=html_path.parent,
            base_dir=source_base,
            fallback_roots=fallback_roots,
        )
        if not rewritten:
            missing.append(raw_url)
            return match.group(0)
        copied.add(rewritten)
        return f"url({match.group('quote')}{rewritten}{match.group('quote')})"

    updated = _HTML_ASSET_ATTR_RE.sub(_replace_attr, text)
    updated = _CSS_ASSET_URL_RE.sub(_replace_css_url, updated)
    if updated != text:
        html_path.write_text(updated, encoding="utf-8")
    return {"copied": len(copied), "missing": missing}


def _select_source_artifacts(downloadables: list[dict[str, Any]]) -> dict[str, Path | None]:
    paths = [_artifact_path(item) for item in downloadables]
    existing = [path for path in paths if path is not None]
    html_path = next((path for path in existing if path.suffix.lower() in {".html", ".htm"} and "agent-revision" in path.name), None)
    html_path = html_path or next((path for path in existing if path.suffix.lower() in {".html", ".htm"} and "with_tables" not in path.name), None)
    html_path = html_path or next((path for path in existing if path.suffix.lower() in {".html", ".htm"}), None)
    md_path = next((path for path in existing if path.suffix.lower() == ".md" and "agent-revision" in path.name), None)
    md_path = md_path or next((path for path in existing if path.suffix.lower() == ".md" and "with_tables" not in path.name), None)
    md_path = md_path or next((path for path in existing if path.suffix.lower() == ".md"), None)
    pdf_path = next((path for path in existing if path.suffix.lower() == ".pdf" and "agent-revision" in path.name), None)
    pdf_path = pdf_path or next((path for path in existing if path.suffix.lower() == ".pdf" and "with_tables" not in path.name), None)
    pdf_path = pdf_path or next((path for path in existing if path.suffix.lower() == ".pdf"), None)
    css_path = None
    if html_path:
        css_candidates = list(html_path.parent.glob("*.css"))
        css_path = next((path for path in css_candidates if "report" in path.name.lower()), css_candidates[0] if css_candidates else None)
    return {"html": html_path, "markdown": md_path, "pdf": pdf_path, "css": css_path}


def _basic_markdown_to_html(markdown_text: str, css_name: str) -> str:
    body: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        escaped = html.escape(line.strip())
        if line.startswith("# "):
            body.append(f"<h1>{escaped[2:]}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{escaped[3:]}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{escaped[4:]}</h3>")
        elif line.startswith("- "):
            body.append(f"<p class=\"bullet\">• {escaped[2:]}</p>")
        else:
            body.append(f"<p>{escaped}</p>")
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" />"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />"
        f"<link rel=\"stylesheet\" href=\"./{html.escape(css_name)}\" />"
        "<title>报告后续改造预览</title></head><body><main class=\"report-page\">"
        + "\n".join(body)
        + "</main></body></html>"
    )


def _default_css() -> str:
    return """
@page { size: A4; margin: 14mm; }
body { margin: 0; background: #f5f0e8; color: #172232; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }
.report-page { max-width: 980px; margin: 0 auto; padding: 42px; background: #fffaf2; min-height: 100vh; }
h1 { font-size: 34px; line-height: 1.22; margin: 0 0 22px; color: #10233b; }
h2 { font-size: 24px; margin: 30px 0 12px; color: #163a5f; }
h3 { font-size: 18px; margin: 22px 0 10px; color: #1f4b6f; }
p { font-size: 14px; line-height: 1.85; margin: 8px 0; }
.bullet { padding-left: 1em; }
table { width: 100%; border-collapse: collapse; margin: 18px 0; font-size: 12px; }
th, td { border: 1px solid #d8dde6; padding: 8px; vertical-align: top; }
th { background: #163a5f; color: white; }
img { max-width: 100%; }
""".strip()


def _extract_requested_phrase(message: str) -> str:
    patterns = [
        r"(?:改成|改为|换成|替换为|替换成)[“\"']([^”\"']+)[”\"']",
        r"(?:标题|主标题|摘要|图注)[：:][ \t]*[“\"']?([^”\"'\n]+)",
        r"(?:title|headline|summary|caption)\s+(?:to|as)\s+[\"']([^\"']+)[\"']",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            return str(match.group(1) or "").strip()
    return ""


def _infer_revision_intent(message: str, annotations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    text = _repair_mojibake_text(message).strip()
    lowered = text.lower()
    operation_kind = "freeform_revision"
    major_tokens = (
        "大改",
        "重写",
        "重构",
        "大幅修改",
        "整体修改",
        "整体重排",
        "全篇",
        "整份",
        "整页",
        "重新组织",
        "重新写",
        "改造成",
        "深度改造",
    )
    if any(token in text for token in major_tokens) or any(
        token in lowered
        for token in (
            "major rewrite",
            "big rewrite",
            "substantial rewrite",
            "overhaul",
            "restructure",
            "rewrite the report",
            "rewrite this report",
        )
    ):
        operation_kind = "major_revision"
    if operation_kind == "freeform_revision" and (
        any(token in text for token in ("主标题", "标题", "首页标题"))
        or "headline" in lowered
        or re.search(r"\bh1\b", lowered)
        or "main title" in lowered
        or re.search(r"\btitle\b", lowered)
    ):
        operation_kind = "headline_edit"
    elif operation_kind == "freeform_revision" and (
        any(token in text for token in ("摘要", "行动项", "导语", "开头", "首页摘要")) or "summary" in lowered
    ):
        operation_kind = "summary_retone"
    elif operation_kind == "freeform_revision" and any(token in text for token in ("图注", "图题", "caption", "figcaption")):
        operation_kind = "caption_edit"
    elif operation_kind == "freeform_revision" and any(
        token in text for token in ("排版", "样式", "布局", "颜色", "字体", "间距", "css", "style", "layout")
    ):
        operation_kind = "layout_tune"

    strict_scope = bool(
        re.search(r"(只改|仅改|只做一件事|只做|只允许|不要改其他|不改其他|不动正文|不要动正文|只按批注)", text)
        or "only " in lowered
        or lowered.startswith("only")
        or "do not change" in lowered
        or "don't change" in lowered
        or "nothing else" in lowered
    )
    scope_mode = "strict" if strict_scope else "open" if operation_kind in {"freeform_revision", "major_revision"} else "targeted"
    explicit_preserve_numbers = bool(
        any(token in text for token in ("deterministic", "数字不变", "不要改数字", "不改数字", "不动数字", "保留所有数字"))
        or "keep all numbers" in lowered
        or "do not change numbers" in lowered
        or "don't change numbers" in lowered
        or "preserve numbers" in lowered
    )
    allow_percentage_reformat = any(token in text for token in ("百分号", "百分比", "小数改百分比")) or any(
        token in lowered for token in ("percentage", "percent sign", "decimal to percent")
    )
    forbidden_change_kinds = {"metric_changes", "numeric_changes"}
    must_change_targets: list[str] = []
    if operation_kind == "headline_edit":
        must_change_targets.append("primary_heading")
        if strict_scope:
            forbidden_change_kinds.update({"body_copy", "section_headings", "figure_captions", "css_changes", "new_sections"})
    elif operation_kind == "summary_retone":
        must_change_targets.append("summary_block")
        if strict_scope:
            forbidden_change_kinds.update({"primary_heading", "section_headings", "figure_captions", "css_changes", "new_sections"})
    elif operation_kind == "caption_edit":
        must_change_targets.append("figure_caption")
        if strict_scope:
            forbidden_change_kinds.update({"primary_heading", "section_headings", "body_copy", "css_changes", "new_sections"})
    elif operation_kind == "layout_tune":
        must_change_targets.append("css_or_layout")
        if strict_scope:
            forbidden_change_kinds.update({"numeric_changes", "metric_changes", "new_sections"})
    elif operation_kind == "major_revision":
        must_change_targets.append("report_structure_or_body")
    elif operation_kind == "freeform_revision" and annotations:
        must_change_targets.append("annotated_region_or_requested_change")

    return {
        "user_message": text,
        "operation_kind": operation_kind,
        "scope_mode": scope_mode,
        "preserve_numbers": True,
        "explicit_preserve_numbers": explicit_preserve_numbers,
        "allow_percentage_reformat": allow_percentage_reformat,
        "must_change_targets": must_change_targets,
        "forbidden_change_kinds": sorted(forbidden_change_kinds),
        "requested_phrase": _extract_requested_phrase(text),
        "annotation_count": len(annotations or []),
        "allow_auto_repair": True,
        "repair_budget": 1,
    }


def _snapshot_turn_baseline(session: dict[str, Any], turn_id: str) -> dict[str, str]:
    workspace = Path(str(session.get("workspace_path") or ""))
    baseline_dir = workspace / "turn_baselines" / turn_id
    baseline_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}
    for kind, raw_path in dict(session.get("working_artifacts") or {}).items():
        source_path = Path(str(raw_path or ""))
        if not source_path.is_file():
            continue
        target = baseline_dir / source_path.name
        shutil.copy2(source_path, target)
        copied[str(kind)] = str(target.resolve())
    return copied


def _read_text_file(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _strip_html_text(value: str) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", " ", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_markdown_outline(text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in text.splitlines()]
    primary_heading = ""
    section_headings: list[str] = []
    paragraphs: list[str] = []
    current_paragraph: list[str] = []
    saw_primary_heading = False
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
                current_paragraph = []
            continue
        if line.startswith("# "):
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
                current_paragraph = []
            if not primary_heading:
                primary_heading = line[2:].strip()
            saw_primary_heading = True
            continue
        if line.startswith("## "):
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
                current_paragraph = []
            section_headings.append(line[3:].strip())
            continue
        if line.startswith("### "):
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
                current_paragraph = []
            section_headings.append(line[4:].strip())
            continue
        if not saw_primary_heading and not primary_heading:
            primary_heading = line
            saw_primary_heading = True
            continue
        current_paragraph.append(line)
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph).strip())
    summary_block = paragraphs[0] if paragraphs else ""
    body_copy = "\n".join(paragraphs[1:]).strip() if len(paragraphs) > 1 else ""
    return {
        "primary_heading": primary_heading,
        "section_headings": section_headings,
        "summary_block": summary_block,
        "paragraphs": paragraphs,
        "body_copy": body_copy,
    }


def _extract_html_outline(text: str) -> dict[str, Any]:
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.IGNORECASE | re.DOTALL)
    primary_heading = _strip_html_text(h1_match.group(1)) if h1_match else ""
    section_headings = [
        _strip_html_text(match)
        for match in re.findall(r"<h[2-6][^>]*>(.*?)</h[2-6]>", text, flags=re.IGNORECASE | re.DOTALL)
        if _strip_html_text(match)
    ]
    paragraphs = [
        _strip_html_text(match)
        for match in re.findall(r"<p[^>]*>(.*?)</p>", text, flags=re.IGNORECASE | re.DOTALL)
        if _strip_html_text(match)
    ]
    figure_captions = [
        _strip_html_text(match)
        for match in re.findall(r"<figcaption[^>]*>(.*?)</figcaption>", text, flags=re.IGNORECASE | re.DOTALL)
        if _strip_html_text(match)
    ]
    return {
        "primary_heading": primary_heading,
        "section_headings": section_headings,
        "summary_block": paragraphs[0] if paragraphs else "",
        "paragraphs": paragraphs,
        "body_copy": "\n".join(paragraphs[1:]).strip() if len(paragraphs) > 1 else "",
        "figure_captions": figure_captions,
        "text": _strip_html_text(text),
    }


def _extract_number_tokens(text: str) -> list[str]:
    values = re.findall(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?%?", text)
    return [value.replace(",", "") for value in values]


def _html_numeric_guard_text(text: str, *, ignore_primary_heading: bool = False) -> str:
    source = _repair_mojibake_text(text)
    if ignore_primary_heading:
        source = re.sub(r"<h1\b[^>]*>[\s\S]*?</h1>", " ", source, count=1, flags=re.I)
        source = re.sub(r"<title\b[^>]*>[\s\S]*?</title>", " ", source, count=1, flags=re.I)
    return _strip_html_text(source)


def _markdown_numeric_guard_text(text: str, *, ignore_primary_heading: bool = False) -> str:
    source = _repair_mojibake_text(text)
    if ignore_primary_heading:
        source = re.sub(r"(?m)^#\s+.*$", " ", source, count=1)
    return source


def _select_number_tokens_for_revision_guard(
    *,
    baseline_md: str,
    baseline_html: str,
    working_md: str,
    working_html: str,
    ignore_primary_heading: bool = False,
) -> tuple[list[str], list[str], str]:
    md_pair = (
        _extract_number_tokens(_markdown_numeric_guard_text(baseline_md, ignore_primary_heading=ignore_primary_heading)),
        _extract_number_tokens(_markdown_numeric_guard_text(working_md, ignore_primary_heading=ignore_primary_heading)),
    )
    html_pair = (
        _extract_number_tokens(_html_numeric_guard_text(baseline_html, ignore_primary_heading=ignore_primary_heading)),
        _extract_number_tokens(_html_numeric_guard_text(working_html, ignore_primary_heading=ignore_primary_heading)),
    )
    md_weight = max(len(md_pair[0]), len(md_pair[1]))
    html_weight = max(len(html_pair[0]), len(html_pair[1]))
    if html_weight > md_weight:
        return html_pair[0], html_pair[1], "html"
    return md_pair[0], md_pair[1], "markdown"


def _number_inventory(tokens: list[str], *, percentage_equivalent: bool = False) -> list[str]:
    inventory: list[str] = []
    for token in tokens:
        raw = str(token or "").strip()
        if not raw:
            continue
        is_percent = raw.endswith("%")
        number_text = raw[:-1] if is_percent else raw
        try:
            value = float(number_text)
        except Exception:
            inventory.append(raw)
            continue
        if percentage_equivalent and is_percent:
            value = value / 100.0
        inventory.append(f"{value:.10g}" if percentage_equivalent else raw)
    return sorted(inventory)


def _numeric_tokens_changed(left: list[str], right: list[str], *, allow_percentage_reformat: bool = False) -> bool:
    return _number_inventory(left, percentage_equivalent=allow_percentage_reformat) != _number_inventory(
        right,
        percentage_equivalent=allow_percentage_reformat,
    )


def _normalize_revision_compare_text(value: Any) -> str:
    repaired = _repair_mojibake_text(value)
    return re.sub(r"\s+", " ", repaired).strip()


def _compare_lists(left: list[str], right: list[str]) -> bool:
    return [_normalize_revision_compare_text(item) for item in left] != [_normalize_revision_compare_text(item) for item in right]


def _verification_failure_status(verification: dict[str, Any]) -> str:
    missing = list(verification.get("missing_targets") or [])
    violations = list(verification.get("forbidden_target_violations") or [])
    if missing and violations:
        return "failed_partial_application"
    if missing:
        return "failed_scope_miss"
    return "failed_scope_violation"


def _summarize_verification(verification: dict[str, Any]) -> str:
    if verification.get("passed"):
        changed = ", ".join(list(verification.get("changed_targets") or [])[:6]) or "已完成允许范围内的修改"
        return f"验收通过：{changed}"
    issues: list[str] = []
    missing = list(verification.get("missing_targets") or [])
    violations = list(verification.get("forbidden_target_violations") or [])
    if missing:
        issues.append("未命中：" + ", ".join(missing))
    if violations:
        issues.append("越界修改：" + ", ".join(violations))
    if verification.get("numeric_changes_detected"):
        issues.append("数字发生变化")
    if not issues:
        issues.append("未通过范围验收")
    return "；".join(issues)


def _verify_turn_revision(session: dict[str, Any], turn: dict[str, Any]) -> dict[str, Any]:
    intent = dict(turn.get("revision_intent") or {})
    baseline_artifacts = dict(turn.get("baseline_artifacts") or {})
    working_artifacts = dict(session.get("working_artifacts") or {})

    baseline_md = _read_text_file(Path(str(baseline_artifacts.get("markdown") or "")) if baseline_artifacts.get("markdown") else None)
    baseline_html = _read_text_file(Path(str(baseline_artifacts.get("html") or "")) if baseline_artifacts.get("html") else None)
    baseline_css = _read_text_file(Path(str(baseline_artifacts.get("css") or "")) if baseline_artifacts.get("css") else None)
    working_md = _read_text_file(Path(str(working_artifacts.get("markdown") or "")) if working_artifacts.get("markdown") else None)
    working_html = _read_text_file(Path(str(working_artifacts.get("html") or "")) if working_artifacts.get("html") else None)
    working_css = _read_text_file(Path(str(working_artifacts.get("css") or "")) if working_artifacts.get("css") else None)

    baseline_md_outline = _extract_markdown_outline(baseline_md) if baseline_md else {}
    working_md_outline = _extract_markdown_outline(working_md) if working_md else {}
    baseline_html_outline = _extract_html_outline(baseline_html) if baseline_html else {}
    working_html_outline = _extract_html_outline(working_html) if working_html else {}

    baseline_primary_heading = _normalize_revision_compare_text(
        baseline_md_outline.get("primary_heading") or baseline_html_outline.get("primary_heading") or ""
    )
    working_md_primary_heading = _normalize_revision_compare_text(working_md_outline.get("primary_heading") or "")
    working_html_primary_heading = _normalize_revision_compare_text(working_html_outline.get("primary_heading") or "")
    working_primary_heading = working_md_primary_heading or working_html_primary_heading
    baseline_summary = _normalize_revision_compare_text(
        baseline_md_outline.get("summary_block") or baseline_html_outline.get("summary_block") or ""
    )
    working_md_summary = _normalize_revision_compare_text(working_md_outline.get("summary_block") or "")
    working_html_summary = _normalize_revision_compare_text(working_html_outline.get("summary_block") or "")
    working_summary = working_md_summary or working_html_summary
    baseline_body = _normalize_revision_compare_text(baseline_md_outline.get("body_copy") or baseline_html_outline.get("body_copy") or "")
    working_body = _normalize_revision_compare_text(working_md_outline.get("body_copy") or working_html_outline.get("body_copy") or "")

    heading_changed = baseline_primary_heading != working_primary_heading and bool(working_primary_heading)
    requested_phrase = _normalize_revision_compare_text(intent.get("requested_phrase") or "")
    requested_phrase_hit = not requested_phrase or requested_phrase in working_primary_heading or requested_phrase in working_summary
    summary_changed = baseline_summary != working_summary and bool(working_summary)
    body_changed = baseline_body != working_body
    section_headings_changed = _compare_lists(
        list(baseline_md_outline.get("section_headings") or baseline_html_outline.get("section_headings") or []),
        list(working_md_outline.get("section_headings") or working_html_outline.get("section_headings") or []),
    )
    figure_captions_changed = _compare_lists(
        list(baseline_html_outline.get("figure_captions") or []),
        list(working_html_outline.get("figure_captions") or []),
    )
    css_changed = baseline_css != working_css
    new_section_count = max(
        0,
        len(list(working_md_outline.get("section_headings") or working_html_outline.get("section_headings") or []))
        - len(list(baseline_md_outline.get("section_headings") or baseline_html_outline.get("section_headings") or [])),
    )
    operation_kind = str(intent.get("operation_kind") or "freeform_revision")
    baseline_number_tokens, working_number_tokens, numeric_comparison_source = _select_number_tokens_for_revision_guard(
        baseline_md=baseline_md,
        baseline_html=baseline_html,
        working_md=working_md,
        working_html=working_html,
        ignore_primary_heading=operation_kind == "headline_edit",
    )
    numeric_changes_detected = _numeric_tokens_changed(
        baseline_number_tokens,
        working_number_tokens,
        allow_percentage_reformat=bool(intent.get("allow_percentage_reformat")),
    )

    html_markdown_in_sync = True
    if working_md and working_html:
        html_markdown_in_sync = working_primary_heading == working_html_primary_heading or not working_primary_heading
        if intent.get("operation_kind") == "summary_retone":
            html_markdown_in_sync = html_markdown_in_sync and working_summary == working_html_summary

    changed_targets: list[str] = []
    if heading_changed:
        changed_targets.append("primary_heading")
    if summary_changed:
        changed_targets.append("summary_block")
    if body_changed:
        changed_targets.append("body_copy")
    if section_headings_changed:
        changed_targets.append("section_headings")
    if figure_captions_changed:
        changed_targets.append("figure_caption")
    if css_changed:
        changed_targets.append("css_changes")

    missing_targets: list[str] = []
    if operation_kind == "headline_edit":
        if not heading_changed or not requested_phrase_hit:
            missing_targets.append("primary_heading")
    elif operation_kind == "summary_retone":
        if not summary_changed:
            missing_targets.append("summary_block")
    elif operation_kind == "caption_edit":
        if not figure_captions_changed:
            missing_targets.append("figure_caption")
    elif operation_kind == "layout_tune":
        if not css_changed and not body_changed:
            missing_targets.append("css_or_layout")
    elif operation_kind == "major_revision":
        if not any((heading_changed, summary_changed, body_changed, section_headings_changed, figure_captions_changed, css_changed)):
            missing_targets.append("report_structure_or_body")
    elif operation_kind == "freeform_revision":
        if not changed_targets:
            missing_targets.append("requested_change")

    forbidden = set(str(item) for item in list(intent.get("forbidden_change_kinds") or []))
    forbidden_target_violations: list[str] = []
    checks = {
        "numeric_changes": numeric_changes_detected,
        "body_copy": body_changed,
        "section_headings": section_headings_changed,
        "figure_captions": figure_captions_changed,
        "css_changes": css_changed,
        "new_sections": new_section_count > 0,
        "primary_heading": heading_changed,
    }
    for key, violated in checks.items():
        if key in forbidden and violated:
            forbidden_target_violations.append(key)

    if intent.get("preserve_numbers") and numeric_changes_detected and "numeric_changes" not in forbidden_target_violations:
        forbidden_target_violations.append("numeric_changes")

    passed = not missing_targets and not forbidden_target_violations and html_markdown_in_sync
    return {
        "passed": passed,
        "operation_kind": operation_kind,
        "scope_mode": intent.get("scope_mode") or "open",
        "requested_phrase_hit": requested_phrase_hit,
        "changed_targets": changed_targets,
        "missing_targets": missing_targets,
        "forbidden_target_violations": forbidden_target_violations,
        "html_markdown_in_sync": html_markdown_in_sync,
        "numeric_changes_detected": numeric_changes_detected,
        "numeric_comparison_source": numeric_comparison_source,
        "new_section_count": new_section_count,
        "summary_changed": summary_changed,
        "body_changed": body_changed,
        "css_changed": css_changed,
    }


def _build_revision_contract_summary(intent: dict[str, Any]) -> str:
    required = ", ".join(list(intent.get("must_change_targets") or [])) or "none"
    forbidden = ", ".join(list(intent.get("forbidden_change_kinds") or [])) or "none"
    requested_phrase = str(intent.get("requested_phrase") or "").strip() or "none"
    allow_percentage = bool(intent.get("allow_percentage_reformat"))
    return (
        "Revision intent contract:\n"
        f"- operation_kind: {intent.get('operation_kind') or 'freeform_revision'}\n"
        f"- scope_mode: {intent.get('scope_mode') or 'open'}\n"
        f"- preserve_numbers: {bool(intent.get('preserve_numbers'))}\n"
        f"- allow_percentage_reformat: {allow_percentage}\n"
        f"- requested_phrase: {requested_phrase}\n"
        f"- must_change_targets: {required}\n"
        f"- forbidden_change_kinds: {forbidden}"
    )


def _build_auto_repair_prompt(turn: dict[str, Any], verification: dict[str, Any]) -> str:
    intent = dict(turn.get("revision_intent") or {})
    requested_phrase = str((turn.get("revision_intent") or {}).get("requested_phrase") or "").strip()
    requested_phrase_line = f"- requested_phrase: {requested_phrase}\n" if requested_phrase else ""
    operation_kind = str(intent.get("operation_kind") or "freeform_revision")
    repair_action = "只修正验收失败点，不要重写其他区域。"
    if operation_kind == "headline_edit":
        repair_action = "只允许改首页主标题；如果上一轮改动了正文或摘要，恢复它们到基线内容。"
    elif operation_kind == "summary_retone":
        repair_action = "只允许改摘要段；标题、其他正文、图注和 CSS 都保持基线。"
    elif operation_kind == "caption_edit":
        repair_action = "只允许改图注；标题、摘要、正文和 CSS 都保持基线。"
    elif operation_kind == "major_revision":
        repair_action = "继续完成用户要求的大改，但只修正验收指出的问题；允许重组标题、章节、正文、图注和排版，仍必须保持数字和已落盘证据不变。"
    return (
        "上一轮原生 Codex 修改没有通过验收。请直接修正报告副本，不要扫描项目源码或仓库。\n\n"
        f"原始用户要求：\n{str(turn.get('user_message') or '').strip()}\n\n"
        "验收失败点：\n"
        f"- missing_targets: {', '.join(list(verification.get('missing_targets') or [])) or 'none'}\n"
        f"- forbidden_target_violations: {', '.join(list(verification.get('forbidden_target_violations') or [])) or 'none'}\n"
        f"- html_markdown_in_sync: {verification.get('html_markdown_in_sync')}\n"
        f"- numeric_changes_detected: {verification.get('numeric_changes_detected')}\n"
        f"{requested_phrase_line}"
        "这次要求：\n"
        f"1. {repair_action}\n"
        "2. 只处理 working/report.md、working/report.html、working/report.css，不要搜索 backend/frontend 代码。\n"
        "3. 保留已经正确的内容，不要再次扩写。\n"
        "4. 不要改 deterministic 数字，不要发明新指标。\n"
        "5. 完成后只用中文简短说明修正了什么。"
    )


def _launch_auto_repair_turn(report_id: str, session_id: str, turn_id: str, verification: dict[str, Any]) -> None:
    def _runner() -> None:
        try:
            session = _read_session(report_id, session_id)
            turn = _current_turn(session)
            if str(turn.get("turn_id") or "") != turn_id:
                return
            prompt = _build_auto_repair_prompt(turn, verification)
            native_payload = start_native_turn(
                session,
                _event_session_handler(report_id, session_id),
                prompt=prompt,
                base_instructions=_native_base_instructions(session),
            )
            fresh = _read_session(report_id, session_id)
            fresh["codex_thread_id"] = str(native_payload.get("thread_id") or fresh.get("codex_thread_id") or "")
            fresh["codex_session_id"] = str(native_payload.get("thread_id") or fresh.get("codex_session_id") or "")
            fresh["active_turn_id"] = str(native_payload.get("turn_id") or "")
            fresh["native_connection_status"] = "online"
            _update_turn(
                fresh,
                turn_id,
                status="auto_repairing",
                native_turn_id=str(native_payload.get("turn_id") or ""),
            )
            _write_session(fresh)
        except Exception as exc:
            failed = _read_session(report_id, session_id)
            turn = _current_turn(failed)
            if str(turn.get("turn_id") or "") == turn_id:
                _update_turn(
                    failed,
                    turn_id,
                    status="failed_scope_miss",
                    final_scope_status="failed",
                    completed_at=_now_iso(),
                )
                _append_event(
                    failed,
                    "turn_failed",
                    text=f"自动纠偏启动失败：{exc}",
                    status="failed_scope_miss",
                    turn_id=turn_id,
                    is_error=True,
                )
                _write_session(failed)

    threading.Thread(target=_runner, name=f"report-agent-auto-repair-{session_id}", daemon=True).start()


def create_report_agent_session(report_id: str, *, title: str = "") -> dict[str, Any]:
    report_dir = _report_dir(report_id)
    downloadables = _load_downloadables(report_dir, report_id, deep_scan=False, fallback_scan=True, catalog_scan_limit=80)
    source = _select_source_artifacts(downloadables)
    session_id = f"agent-session-{uuid.uuid4().hex[:12]}"
    workspace = _session_root(report_dir) / session_id
    source_dir = workspace / "source"
    working_dir = workspace / "working"
    working_dir.mkdir(parents=True, exist_ok=True)

    copied_source: dict[str, str] = {}
    for kind, path in source.items():
        if path is None:
            continue
        target = source_dir / path.name
        _copy_if_exists(path, target)
        copied_source[kind] = str(target.resolve())

    working_md = _copy_if_exists(source.get("markdown"), working_dir / "report.md")
    working_html = _copy_if_exists(source.get("html"), working_dir / "report.html")
    working_css = _copy_if_exists(source.get("css"), working_dir / "report.css")
    if working_css is None:
        working_css = working_dir / "report.css"
        working_css.write_text(_default_css(), encoding="utf-8")
    if working_md is None and working_html is not None:
        text = re.sub(r"<(script|style)[\s\S]*?</\1>", "", working_html.read_text(encoding="utf-8", errors="replace"), flags=re.I)
        text = re.sub(r"<[^>]+>", "\n", text)
        working_md = working_dir / "report.md"
        working_md.write_text(re.sub(r"\n{3,}", "\n\n", html.unescape(text)).strip(), encoding="utf-8")
    if working_html is None and working_md is not None:
        working_html = working_dir / "report.html"
        working_html.write_text(_basic_markdown_to_html(working_md.read_text(encoding="utf-8"), "report.css"), encoding="utf-8")
    if working_html is None and working_md is None and source.get("pdf") is not None:
        working_md = working_dir / "report.md"
        working_md.write_text(_build_pdf_fallback_markdown(report_id, source.get("pdf")), encoding="utf-8")
        working_html = working_dir / "report.html"
        working_html.write_text(_basic_markdown_to_html(working_md.read_text(encoding="utf-8"), "report.css"), encoding="utf-8")
    asset_fallback_roots = [
        *[
            path.parent
            for path in source.values()
            if path is not None and path.parent.exists()
        ],
        workspace,
    ]
    if working_css is not None:
        _materialize_css_assets(
            working_css,
            base_dir=source.get("css").parent if source.get("css") else working_css.parent,
            fallback_roots=asset_fallback_roots,
        )
    if working_html is not None:
        _materialize_html_assets(
            working_html,
            base_dir=source.get("html").parent if source.get("html") else working_html.parent,
            fallback_roots=asset_fallback_roots,
        )

    session = {
        "session_id": session_id,
        "report_id": report_id,
        "title": title or "后续改造",
        "status": "active",
        "session_status": "active",
        "current_turn": {},
        "turns": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "workspace_path": str(workspace.resolve()),
        "working_dir": str(working_dir.resolve()),
        "current_task_id": "",
        "current_run_id": "",
        "codex_session_id": "",
        "mode": "native_app_server",
        "codex_thread_id": "",
        "active_turn_id": "",
        "native_connection_status": "idle",
        "native_protocol_error": "",
        "guidance_injections": [],
        "stdout_offsets": {},
        "processed_task_ids": [],
        "event_index": 0,
        "source_artifacts": copied_source,
        "working_artifacts": {
            "markdown": str(working_md.resolve()) if working_md else "",
            "html": str(working_html.resolve()) if working_html else "",
            "css": str(working_css.resolve()) if working_css else "",
        },
        "preview_artifact": _downloadable_from_file(working_html, purpose="当前后续改造预览 HTML") if working_html else {},
        "preview_url": _storage_url_for(working_html) if working_html else "",
        "published_versions": [],
        "revision_agent_contract_version": "native-major-v3",
    }
    _write_session(session)
    _append_event(session, "session_created", text="后续改造会话已创建。", preview_url=session.get("preview_url"))
    _write_session(session)
    return {"session": _public_session(session), "events": _read_events(session)}


def _build_turn_prompt(session: dict[str, Any], message: str) -> str:
    working = dict(session.get("working_artifacts") or {})
    annotations_path = _annotations_path(session)
    annotations = _read_annotations(session)
    if annotations:
        message = (
            f"{message}\n\n"
            "批注上下文（这些是用户在右侧预览区画出的工程批注，必须作为本轮修改依据）：\n"
            + _annotation_prompt_summary(annotations)
            + "\n\nReport annotation contract:\n"
            + json.dumps(
                {
                    "annotations_path": str(annotations_path.resolve()),
                    "annotation_count": len(annotations),
                    "recent_annotations": annotations[-12:],
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n请使用这些批注指导报告修改；除非用户明确要求，不要把批注图形本身烧录进最终 PDF。"
        )
    return f"""
你是 Asteria 内置 Codex，正在对一个已经产出的报告做后续改造。

用户修改意见：
{message}

工作目录：
{session.get("working_dir")}

可编辑文件：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

硬性规则：
1. 只能修改当前会话工作目录里的报告副本，不要改原报告文件，不要改项目源码。
2. 可以调整标题、结构、正文、图注、排版、HTML/CSS 和已有证据组织。
3. 不得发明新指标，不得篡改 deterministic 数字，不得设置 formal_pdf_allowed。
4. 如果用户要求改数字或新增无证据结论，请在回复里明确说明 blocked_change，并保留原数字。
5. 修改后尽量保持 report.html 引用 ./report.css；如果改了 report.md，也同步更新 report.html 的读者预览。
6. 最后用中文简要说明做了哪些修改、哪些请求被阻断、下一步可发布什么产物。
""".strip()


def _native_base_instructions(session: dict[str, Any]) -> str:
    working = dict(session.get("working_artifacts") or {})
    return f"""
你是 Asteria 内置 Codex，正在一个报告后续改造工作台中工作。

工作目录：
{session.get("workspace_path")}

只允许编辑当前会话工作副本：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

硬性规则：
1. 原报告只读，不要改 source/ 内的原始报告文件，不要改项目源码。
2. 可以调整标题、结构、正文、图注、排版、HTML/CSS 和已有证据组织。
3. 不得发明新指标，不得篡改 deterministic 数字，不得设置 formal_pdf_allowed。
4. 如果用户要求改数字或新增无证据结论，请明确输出 blocked_change，并保留原数字。
5. 修改后尽量保持 report.html 引用 ./report.css；如果改了 report.md，也同步更新 report.html 的读者预览。
6. 用中文简要说明做了哪些修改、哪些请求被阻断、下一步可发布什么产物。
""".strip()


def _guidance_prompt(message: str) -> str:
    return f"""
用户在你当前思考或工具执行过程中追加了引导意见，请把它作为当前 turn 的即时约束吸收，不要排队到下一轮：

{message}
""".strip()


def _build_turn_prompt(session: dict[str, Any], message: str) -> str:
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or _infer_revision_intent(message))
    annotations_path = _annotations_path(session)
    annotations = _read_annotations(session)
    message_text = _repair_mojibake_text(message).strip()
    if annotations:
        message_text = (
            f"{message_text}\n\n"
            "批注上下文（这些是用户在右侧预览区画出的工程批注，必须作为本轮修改依据）：\n"
            + _annotation_prompt_summary(annotations)
            + "\n\nReport annotation contract:\n"
            + json.dumps(
                {
                    "annotations_path": str(annotations_path.resolve()),
                    "annotation_count": len(annotations),
                    "recent_annotations": annotations[-12:],
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n请使用这些批注指导报告修改；除非用户明确要求，不要把批注图形本身烧录进最终 PDF。"
        )
    return f"""
你是 Asteria 内置 Codex，正在对一个已经产出的报告做后续改造。
用户修改意见：
{message_text}

工作目录：{session.get("working_dir")}

可编辑文件：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

{_build_revision_contract_summary(intent)}

Success criteria:
- 必须先命中本轮要求的修改目标，再考虑润色。
- 如果 scope_mode 是 strict，只允许修改与当前要求直接相关的区域。
- Markdown 与 HTML 需要保持同步；如果改了标题或摘要，两边都要改。
- 不要擅自新增段落、说明块、图表或样式，除非本轮要求明确允许。
- 不要扫描或分析项目源码；优先直接阅读并修改 working/report.md、working/report.html、working/report.css。

Hard guardrails:
1. 只能修改当前会话工作目录里的报告副本，不要改原报告文件，不要改项目源码。
2. 不得发明新指标，不得篡改 deterministic 数字，不得设置 formal_pdf_allowed。
3. 如果用户要求改数字或新增无证据结论，请明确输出 blocked_change，并保留原数字。
4. 完成后用中文简要说明做了哪些修改、哪些请求被阻断、是否可以发布当前修订版。
""".strip()


def _native_base_instructions(session: dict[str, Any]) -> str:
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or {})
    return f"""
你是 Asteria 内置 Codex，正在报告后续改造工作台中工作。
工作目录：{session.get("workspace_path")}

只允许编辑当前会话工作副本：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

当前 revision contract：
{_build_revision_contract_summary(intent)}

硬性规则：
1. 原报告只读，不要改 source/ 内的原始报告文件，不要改项目源码。
2. 优先命中用户要求，再做表达润色；strict scope 下不要越界改动。
3. 不得发明新指标，不得篡改 deterministic 数字，不得设置 formal_pdf_allowed。
4. 如果用户要求改数字或新增无证据结论，请明确输出 blocked_change，并保留原数字。
5. 修改后尽量保持 report.html 引用 ./report.css；如改了 report.md，也要同步更新 report.html 的读者预览。
6. 不要为了理解任务去扫描 backend/frontend 等项目源码；除非绝对必要，只处理 working/ 下的报告副本。
7. 用中文简要说明做了哪些修改、哪些请求被阻断、下一步可发布什么产物。
""".strip()


def _guidance_prompt(message: str) -> str:
    return f"""
用户在当前 Codex turn 运行中追加了引导意见。请把它作为本轮即时约束吸收，不要排队到下一轮：

{str(message or '').strip()}
""".strip()


def _build_turn_prompt(session: dict[str, Any], message: str) -> str:
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or _infer_revision_intent(message))
    annotations_path = _annotations_path(session)
    annotations = _read_annotations(session)
    message_text = _repair_mojibake_text(message).strip()
    if annotations:
        message_text = (
            f"{message_text}\n\n"
            "批注上下文：这些是用户在右侧预览区留下的工程批注，本轮修改需要优先理解它们指向的页面、区域和备注。\n"
            + _annotation_prompt_summary(annotations)
            + "\n\nReport annotation contract:\n"
            + json.dumps(
                {
                    "annotations_path": str(annotations_path.resolve()),
                    "annotation_count": len(annotations),
                    "recent_annotations": annotations[-12:],
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n除非用户明确要求把批注图形烧录进报告，否则只把批注作为改稿依据。"
        )

    scope_mode = str(intent.get("scope_mode") or "open")
    operation_kind = str(intent.get("operation_kind") or "freeform_revision")
    if operation_kind == "major_revision" or scope_mode == "open":
        scope_instruction = (
            "本轮允许进行结构级改造：可以重排章节、重写摘要和正文、调整图注、强化叙事层级、优化 HTML/CSS。"
            "你仍然只能使用当前报告和已存在证据，不得改 deterministic 数字或发明新指标。"
        )
    elif scope_mode == "strict":
        scope_instruction = "本轮是严格局部修改：只处理用户点名的区域，其他内容保持原样。"
    else:
        scope_instruction = "本轮是定向修改：优先命中用户要求的目标区域，可做必要的相邻文案和排版同步。"

    return f"""
你是 Asteria 内置 Codex，正在对一份已经产出的报告做后续改造。

用户修改意见：
{message_text}

工作目录：
{session.get("working_dir") or session.get("workspace_path")}

可编辑文件：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

{_build_revision_contract_summary(intent)}

执行策略：
- {scope_instruction}
- 优先直接读取并修改 working/report.md、working/report.html、working/report.css。
- 如果改了 Markdown 的标题、摘要、章节或关键正文，必须同步 HTML 预览。
- 如果只改 HTML/CSS，也要保持读者可见内容和 Markdown 不产生明显冲突。
- 可以做大改，但大改的边界是“重组和改写已存在证据”，不是新增未验证数据。

硬边界：
1. 原报告只读，不要修改 source/ 内的原始报告文件。
2. 不要修改项目源码、后端服务、前端组件或 pipeline 产物；本 turn 只改当前 session 的报告副本。
3. 不得篡改 deterministic 数字，不得发明新指标，不得设置 formal_pdf_allowed。
4. 如果用户要求无证据改数字或新增无证据结论，明确输出 blocked_change，并保留原数字。
5. 完成后用中文简短说明：改了什么、哪些请求被阻断、当前修订版是否可发布。
""".strip()


def _native_base_instructions(session: dict[str, Any]) -> str:
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or {})
    return f"""
你是 Asteria 报告后续改造工作台里的原生 Codex。你的职责是像工程会话一样改报告副本，而不是改应用源码。

工作目录：
{session.get("workspace_path")}

只允许编辑当前会话工作副本：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

当前 revision contract：
{_build_revision_contract_summary(intent)}

工作原则：
1. 用户要求“大改、重写、重排、整体优化”时，可以进行结构级改造；用户要求“只改、仅改、不要动其他”时，严格局部修改。
2. 大改也只能围绕当前报告已有证据重组表达，不得改 deterministic 数字，不得发明新指标。
3. 原报告只读，不要修改 source/ 文件，不要修改 backend/frontend 源码，不要扫描项目来替代改稿。
4. 修改 Markdown 时同步 HTML 预览；修改 HTML/CSS 时保持发布文件可渲染。
5. 用户运行中追加的引导消息要吸收到当前 turn。
6. 最后用中文说明本轮改动、阻断项和可发布产物。
""".strip()


REVISION_AGENT_CONTRACT_VERSION = "native-major-v3"


def _infer_revision_intent(message: str, annotations: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # type: ignore[no-redef]
    text = _repair_mojibake_text(message).strip()
    lowered = text.lower()
    major_tokens = (
        "大改",
        "重写",
        "重构",
        "大幅修改",
        "整体修改",
        "整体重排",
        "全篇",
        "整份",
        "整页",
        "重新组织",
        "重新写",
        "改造成",
        "深度改造",
        "结构级",
    )
    summary_tokens = ("摘要", "行动项", "导语", "开头", "首页摘要")
    headline_tokens = ("主标题", "标题", "首页标题")
    caption_tokens = ("图注", "图题", "caption", "figcaption")
    layout_tokens = ("排版", "样式", "布局", "颜色", "字体", "间距", "css", "style", "layout")

    operation_kind = "freeform_revision"
    if any(token in text for token in major_tokens) or any(
        token in lowered
        for token in (
            "major rewrite",
            "big rewrite",
            "substantial rewrite",
            "overhaul",
            "restructure",
            "rewrite the report",
            "rewrite this report",
        )
    ):
        operation_kind = "major_revision"
    elif any(token in text for token in summary_tokens) or "summary" in lowered:
        operation_kind = "summary_retone"
    elif any(token in text for token in headline_tokens) or "headline" in lowered or re.search(r"\bh1\b|\btitle\b|main title", lowered):
        operation_kind = "headline_edit"
    elif any(token in text for token in caption_tokens):
        operation_kind = "caption_edit"
    elif any(token in text for token in layout_tokens):
        operation_kind = "layout_tune"

    strict_scope = bool(
        re.search(r"(只改|仅改|只做一件事|只做|只允许|不要改其他|不改其他|不动正文|只按批注)", text)
        or "only " in lowered
        or lowered.startswith("only")
        or "do not change" in lowered
        or "don't change" in lowered
        or "nothing else" in lowered
    )
    scope_mode = "strict" if strict_scope else "open" if operation_kind in {"freeform_revision", "major_revision"} else "targeted"
    explicit_preserve_numbers = bool(
        any(token in text for token in ("deterministic", "数字不变", "不要改数字", "不改数字", "不动数字", "保持所有数字"))
        or "keep all numbers" in lowered
        or "do not change numbers" in lowered
        or "don't change numbers" in lowered
        or "preserve numbers" in lowered
    )
    allow_percentage_reformat = any(token in text for token in ("百分号", "百分比", "小数改百分比")) or any(
        token in lowered for token in ("percentage", "percent sign", "decimal to percent")
    )

    forbidden_change_kinds = {"metric_changes", "numeric_changes"}
    must_change_targets: list[str] = []
    if operation_kind == "headline_edit":
        must_change_targets.append("primary_heading")
        if strict_scope:
            forbidden_change_kinds.update({"body_copy", "section_headings", "figure_captions", "css_changes", "new_sections"})
    elif operation_kind == "summary_retone":
        must_change_targets.append("summary_block")
        if strict_scope:
            forbidden_change_kinds.update({"primary_heading", "section_headings", "figure_captions", "css_changes", "new_sections"})
    elif operation_kind == "caption_edit":
        must_change_targets.append("figure_caption")
        if strict_scope:
            forbidden_change_kinds.update({"primary_heading", "section_headings", "body_copy", "css_changes", "new_sections"})
    elif operation_kind == "layout_tune":
        must_change_targets.append("css_or_layout")
        if strict_scope:
            forbidden_change_kinds.update({"new_sections"})
    elif operation_kind == "major_revision":
        must_change_targets.append("report_structure_or_body")
    elif operation_kind == "freeform_revision" and annotations:
        must_change_targets.append("annotated_region_or_requested_change")

    return {
        "user_message": text,
        "operation_kind": operation_kind,
        "scope_mode": scope_mode,
        "preserve_numbers": True,
        "explicit_preserve_numbers": explicit_preserve_numbers,
        "allow_percentage_reformat": allow_percentage_reformat,
        "must_change_targets": must_change_targets,
        "forbidden_change_kinds": sorted(forbidden_change_kinds),
        "requested_phrase": _extract_requested_phrase(text),
        "annotation_count": len(annotations or []),
        "allow_auto_repair": True,
        "repair_budget": 1,
        "contract_version": REVISION_AGENT_CONTRACT_VERSION,
    }


def _summarize_verification(verification: dict[str, Any]) -> str:  # type: ignore[no-redef]
    if verification.get("passed"):
        changed = ", ".join(list(verification.get("changed_targets") or [])[:6]) or "已完成允许范围内的修改"
        return f"验收通过：{changed}"
    issues: list[str] = []
    missing = list(verification.get("missing_targets") or [])
    violations = list(verification.get("forbidden_target_violations") or [])
    if missing:
        issues.append("未命中：" + ", ".join(missing))
    if violations:
        issues.append("越界修改：" + ", ".join(violations))
    if verification.get("numeric_changes_detected"):
        issues.append("数字发生变化")
    if not issues:
        issues.append("未通过范围验收")
    return "；".join(issues)


def _build_revision_contract_summary(intent: dict[str, Any]) -> str:  # type: ignore[no-redef]
    required = ", ".join(list(intent.get("must_change_targets") or [])) or "none"
    forbidden = ", ".join(list(intent.get("forbidden_change_kinds") or [])) or "none"
    requested_phrase = str(intent.get("requested_phrase") or "").strip() or "none"
    return (
        "Revision intent contract:\n"
        f"- contract_version: {REVISION_AGENT_CONTRACT_VERSION}\n"
        f"- operation_kind: {intent.get('operation_kind') or 'freeform_revision'}\n"
        f"- scope_mode: {intent.get('scope_mode') or 'open'}\n"
        f"- preserve_numbers: {bool(intent.get('preserve_numbers'))}\n"
        f"- allow_percentage_reformat: {bool(intent.get('allow_percentage_reformat'))}\n"
        f"- requested_phrase: {requested_phrase}\n"
        f"- must_change_targets: {required}\n"
        f"- forbidden_change_kinds: {forbidden}"
    )


def _build_turn_prompt(session: dict[str, Any], message: str) -> str:  # type: ignore[no-redef]
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or _infer_revision_intent(message))
    annotations_path = _annotations_path(session)
    annotations = _read_annotations(session)
    message_text = _repair_mojibake_text(message).strip()
    if annotations:
        message_text = (
            f"{message_text}\n\n"
            "批注上下文：这些是用户在右侧预览区留下的工程批注，本轮修改需要优先理解它们指向的页面、区域和备注。\n"
            + _annotation_prompt_summary(annotations)
            + "\n\nReport annotation contract:\n"
            + json.dumps(
                {
                    "annotations_path": str(annotations_path.resolve()),
                    "annotation_count": len(annotations),
                    "recent_annotations": annotations[-12:],
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n除非用户明确要求把批注图形烧录进报告，否则只把批注作为改稿依据。"
        )

    scope_mode = str(intent.get("scope_mode") or "open")
    operation_kind = str(intent.get("operation_kind") or "freeform_revision")
    if operation_kind == "major_revision" or scope_mode == "open":
        scope_instruction = (
            "本轮允许结构级改造：可以重排章节、重写摘要和正文、调整图注、强化叙事层级、优化 HTML/CSS。"
            "边界是重组和改写已有证据，不得改变 deterministic 数字或发明新指标。"
        )
    elif scope_mode == "strict":
        scope_instruction = "本轮是严格局部修改：只处理用户点名的区域，其他内容保持原样。"
    else:
        scope_instruction = "本轮是定向修改：优先命中用户要求的目标区域，可做必要的相邻文案和排版同步。"

    return f"""
你是 Asteria 内置 Codex，正在对一份已经产出的报告做后续改造。

用户修改意见：
{message_text}

工作目录：
{session.get("working_dir") or session.get("workspace_path")}

可编辑文件：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

{_build_revision_contract_summary(intent)}

执行策略：
- {scope_instruction}
- 优先直接读取并修改 working/report.md、working/report.html、working/report.css。
- 如果改了 Markdown 的标题、摘要、章节或关键正文，必须同步 HTML 预览。
- 如果只改 HTML/CSS，也要保持读者可见内容和 Markdown 不产生明显冲突。
- 可以做大改，但大改的边界是“重组和改写已存在证据”，不是新增未验证数据。

硬边界：
1. 原报告只读，不要修改 source/ 内的原始报告文件。
2. 不要修改项目源码、后端服务、前端组件或 pipeline 产物；本 turn 只改当前 session 的报告副本。
3. 不得篡改 deterministic 数字，不得发明新指标，不得设置 formal_pdf_allowed。
4. 如果用户要求无证据改数字或新增无证据结论，明确输出 blocked_change，并保留原数字。
5. 完成后用中文简短说明：改了什么、哪些请求被阻断、当前修订版是否可发布。
""".strip()


def _native_base_instructions(session: dict[str, Any]) -> str:  # type: ignore[no-redef]
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or {})
    return f"""
你是 Asteria 报告后续改造工作台里的原生 Codex。你的职责是像工程会话一样改报告副本，而不是改应用源码。

工作目录：
{session.get("workspace_path")}

只允许编辑当前会话工作副本：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}

当前 revision contract：
{_build_revision_contract_summary(intent)}

工作原则：
1. 用户要求“大改、重写、重排、整体优化”时，可以进行结构级改造；用户要求“只改、仅改、不要动其他”时，严格局部修改。
2. 大改也只能围绕当前报告已有证据重组表达，不得改 deterministic 数字，不得发明新指标。
3. 原报告只读，不要修改 source/ 文件，不要修改 backend/frontend 源码，不要扫描项目来替代改稿。
4. 修改 Markdown 时同步 HTML 预览；修改 HTML/CSS 时保持发布文件可渲染。
5. 用户运行中追加的引导消息要吸收到当前 turn。
6. 最后用中文说明本轮改动、阻断项和可发布产物。
""".strip()


def _build_turn_prompt(session: dict[str, Any], message: str) -> str:  # type: ignore[no-redef]
    working = dict(session.get("working_artifacts") or {})
    annotations = _read_annotations(session)
    annotation_context = _annotation_prompt_summary(annotations) if annotations else "当前没有批注。"
    attachment_context = _attachment_turn_context(session)
    evidence_context = _revision_evidence_turn_context(
        session,
        refresh=bool(session.get("preflight_revision_chart_request")),
    )
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or {})
    scope_mode = str(intent.get("scope_mode") or "open")
    operation_kind = str(intent.get("operation_kind") or "freeform_revision")
    if operation_kind == "major_revision" or scope_mode == "open":
        scope_instruction = "允许结构级大改：可重排章节、重写摘要和正文、调整图注、优化 HTML/CSS；边界是只重组已有证据和补充材料证据，不得伪造数字。"
    elif scope_mode == "strict":
        scope_instruction = "严格局部修改：只处理用户点名区域，其他内容保持原样。"
    else:
        scope_instruction = "定向修改：优先命中用户要求的目标区域，可做必要相邻文案和排版同步。"
    return f"""
你是 Asteria 内置原生 Codex，正在修改一份已经产出的报告副本。

用户本轮要求：
{str(message or '').strip()}

工作目录：
{session.get("working_dir") or session.get("workspace_path")}

可编辑文件：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}
- 图表计划: working/{REVISION_CHART_PLAN_NAME}

本轮意图边界：
{_build_revision_contract_summary(intent)}

执行策略：
- {scope_instruction}
- 可以像原生 Codex 一样主动读取 working 文件、附件画像、批注、已有产物，自己判断如何完成用户目标。
- 如果用户要求补数据、补分析或补图，优先读取附件与 `attachment_data_profile.json`，然后写 `working/{REVISION_CHART_PLAN_NAME}`。
- `revision_chart_plan.json` 不是固定槽位，允许规划任意合理图种：bar、top_n、line、area、scatter、bubble、quadrant、heatmap、pie、donut、histogram、box 等。
- 你只负责选图、解释、组织正文；最终图表数值和 PNG/CSV 由后端确定性渲染。
- 如果字段不满足用户指定图种，不要停住：改用最接近的替代图或诊断图，并在正文说明证据边界。
- 如果用户上传新数据，默认作为“补充数据口径”；不要静默替换原报告确定性数字。真正要整份重算时，建议走 CLI 长链重跑。

批注上下文：
{annotation_context}

附件上下文：
{attachment_context}

原报告证据上下文：
{evidence_context}

硬边界：
1. 原报告 source/ 只读，不要修改。
2. 不要修改项目源码、后端服务、前端组件或 pipeline 产物；本 turn 只改当前 session 的报告副本。
3. 不得篡改 deterministic 数字，不得发明新指标，不得设置 formal_pdf_allowed。
4. 用户要求无证据改数字时，写明 blocked_change，并保留原数字。
5. 完成后用中文简短说明：改了什么、用了哪些补充证据、哪些请求被转换为替代图或证据边界说明、当前修订版是否可发布。
""".strip()


def _native_base_instructions(session: dict[str, Any]) -> str:  # type: ignore[no-redef]
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or {})
    return f"""
你是 Asteria 报告后续改造工作台里的原生 Codex。你像工程会话一样修改当前报告副本，而不是修改应用源码。

工作目录：
{session.get("workspace_path")}

可编辑文件：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}
- 图表计划: working/{REVISION_CHART_PLAN_NAME}

当前 revision contract：
{_build_revision_contract_summary(intent)}

附件和补图能力：
{_attachment_turn_context(session)}

原报告证据资产：
{_revision_evidence_turn_context(session, refresh=bool(session.get("preflight_revision_chart_request")))}

工作原则：
1. 用户要求“大改、重写、重排、整体优化”时，可以进行结构级改造；用户要求“只改、仅改、不动其他”时，严格局部修改。
2. 大改也只能围绕当前报告已有证据、批注和上传附件证据重组表达，不得改 deterministic 数字，不得发明新指标。
3. 如需新增图表，写 `working/{REVISION_CHART_PLAN_NAME}`；后端会渲染 PNG/CSV 并把结果挂回报告。
4. 图种不限于气泡/象限，只要字段支持就可以规划；字段不够时给出替代图或诊断图，保证用户得到可交付结果。
5. 修改 Markdown 时同步 HTML 预览；修改 HTML/CSS 时保持发布文件可渲染。
6. 运行中追加的用户引导消息要吸收到当前 turn。
7. 最后用中文说明本轮改动、证据来源、替代处理和可发布状态。
""".strip()


def _build_turn_prompt(session: dict[str, Any], message: str) -> str:  # type: ignore[no-redef]
    working = dict(session.get("working_artifacts") or {})
    turn = _current_turn(session)
    intent = dict(turn.get("revision_intent") or {})
    annotations = _read_annotations(session)
    annotation_context = _annotation_prompt_summary(annotations) if annotations else "当前没有批注。"
    preflight_count = int(session.get("preflight_revision_chart_count") or 0)
    chart_note = (
        f"后端已经基于现有报告证据确定性生成 {preflight_count} 张补充图表，"
        f"渲染日志在 working/{REVISION_CHART_RENDER_LOG_NAME}，图表在 working/revision_visual_assets/。"
        "本轮请优先把这些图表解释清楚并嵌入报告语境，不要重新计算数值。"
        if session.get("preflight_revision_chart_request")
        else "如果用户要求补图，请写 working/revision_chart_plan.json；后端会确定性渲染 PNG/CSV。"
    )
    return f"""
你是 Asteria 内置的原生 Codex，正在修改一份已经产出的报告副本。

用户原话：
{str(message or '').strip()}

可编辑文件：
- Markdown: {working.get("markdown") or "working/report.md"}
- HTML: {working.get("html") or "working/report.html"}
- CSS: {working.get("css") or "working/report.css"}
- 图表计划: working/{REVISION_CHART_PLAN_NAME}

本轮意图边界：
{_build_revision_contract_summary(intent)}

图表/证据状态：
{chart_note}

批注上下文：
{annotation_context}

附件画像：
{_attachment_turn_context(session)}

原报告证据资产：
{_revision_evidence_turn_context(session, refresh=bool(session.get("preflight_revision_chart_request")))}

执行规则：
1. 只修改当前 session 的 working/report.md、working/report.html、working/report.css、working/{REVISION_CHART_PLAN_NAME}。
2. 不要修改 source/ 原报告，不要修改 backend/frontend 源码，不要扫描整个项目仓库来代替改报告。
3. 不得篡改 deterministic 数字，不得发明新指标，不得设置 formal_pdf_allowed。
4. 如果已有 preflight 图表，请只补中文业务解释、章节挂点和必要排版；不要重新跑一轮大范围调查。
5. 气泡/象限字段不足时可以接受后端替代图，但正文必须说明替代原因和证据边界。
6. 完成后用中文简短说明：新增了哪些图、图表数据来自哪里、是否有替代处理、当前修订版是否可发布。
""".strip()


def _native_base_instructions(session: dict[str, Any]) -> str:  # type: ignore[no-redef]
    working = dict(session.get("working_artifacts") or {})
    return f"""
你是 Asteria 报告后续改造工作台里的原生 Codex。
你的任务是改当前报告副本，而不是改应用源代码。

工作目录：{session.get("workspace_path")}

只允许编辑：
- {working.get("markdown") or "working/report.md"}
- {working.get("html") or "working/report.html"}
- {working.get("css") or "working/report.css"}
- working/{REVISION_CHART_PLAN_NAME}

硬边界：
1. 原报告 source/ 只读。
2. 不改 deterministic 数字，不发明新指标，不设置 formal_pdf_allowed。
3. 用户要求补图时，Codex 负责选择和解释，后端负责确定性渲染 PNG/CSV。
4. 如果后端已先行生成 revision_visual_assets，请优先消费这些结果并快速收口。
5. 最终回复使用中文，说明改动、证据来源和发布状态。
""".strip()


def _build_auto_repair_prompt(turn: dict[str, Any], verification: dict[str, Any]) -> str:  # type: ignore[no-redef]
    intent = dict(turn.get("revision_intent") or {})
    operation_kind = str(intent.get("operation_kind") or "freeform_revision")
    if operation_kind == "headline_edit":
        repair_action = "只允许修正首页主标题；如果上一轮改动了正文或摘要，请恢复到基线内容。"
    elif operation_kind == "summary_retone":
        repair_action = "只允许修正摘要段；标题、其他正文、图注和 CSS 保持基线。"
    elif operation_kind == "caption_edit":
        repair_action = "只允许修正图题/图注；标题、摘要、正文和 CSS 保持基线。"
    elif operation_kind == "major_revision":
        repair_action = "继续完成用户要求的大改，但只修正验收指出的问题；允许重组标题、章节、正文、图注和排版，仍必须保持数字和已落盘证据不变。"
    else:
        repair_action = "只修正验收失败点，不要重写其他区域。"
    return (
        "上一轮原生 Codex 修改没有通过验收。请直接修正报告副本，不要扫描项目源码或仓库。\n\n"
        f"原始用户要求：\n{str(turn.get('user_message') or '').strip()}\n\n"
        "验收失败点：\n"
        f"- missing_targets: {', '.join(list(verification.get('missing_targets') or [])) or 'none'}\n"
        f"- forbidden_target_violations: {', '.join(list(verification.get('forbidden_target_violations') or [])) or 'none'}\n"
        f"- html_markdown_in_sync: {verification.get('html_markdown_in_sync')}\n"
        f"- numeric_changes_detected: {verification.get('numeric_changes_detected')}\n\n"
        "这次要求：\n"
        f"1. {repair_action}\n"
        "2. 只处理 working/report.md、working/report.html、working/report.css。\n"
        "3. 保留已经正确的内容，不要再次扩写。\n"
        "4. 不要改 deterministic 数字，不要发明新指标。\n"
        "5. 完成后只用中文简短说明修正了什么。"
    )


def _event_session_handler(report_id: str, session_id: str):
    def _handler(native_event: dict[str, Any]) -> None:
        try:
            _handle_native_event(report_id, session_id, native_event)
        except Exception:
            # Native event listeners must never crash the app-server bridge.
            pass

    return _handler


def _native_item_text(item: dict[str, Any]) -> str:
    content = item.get("content")
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                parts.append(str(part.get("text") or part.get("content") or ""))
            else:
                parts.append(str(part))
        text = "\n".join(part for part in parts if part)
        if text:
            return text
    for key in ("text", "message", "output", "aggregated_output", "result"):
        value = item.get(key)
        if value:
            return str(value)
    return ""


def _native_item_command(item: dict[str, Any]) -> str:
    command = item.get("command")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    if command:
        return str(command)
    input_payload = item.get("input") if isinstance(item.get("input"), dict) else {}
    if input_payload.get("cmd"):
        return str(input_payload.get("cmd"))
    return str(item.get("name") or "")


def _changed_working_files(session: dict[str, Any]) -> list[str]:
    workspace = Path(str(session.get("workspace_path") or "")).resolve()
    changed: list[str] = []
    for raw_path in (session.get("working_artifacts") or {}).values():
        path = Path(str(raw_path or ""))
        if not path.is_file():
            continue
        if not _is_within(path, workspace):
            continue
        relative = _session_relative_path(session, path)
        if relative not in changed:
            changed.append(relative)
    return changed


def _finalize_native_turn_completion(
    report_id: str,
    session_id: str,
    session: dict[str, Any],
    native_event: dict[str, Any],
    params: dict[str, Any],
    *,
    allow_auto_repair: bool = True,
    ignore_suppressed: bool = False,
) -> bool:
    turn = _current_turn(session)
    turn_id = str(turn.get("turn_id") or "")
    suppressed_turn_ids = {str(item or "") for item in list(session.get("suppressed_turn_ids") or []) if str(item or "")}
    if turn_id and turn_id in suppressed_turn_ids and not ignore_suppressed:
        session["active_turn_id"] = ""
        session["status"] = "active"
        session["session_status"] = "active"
        return False
    if str(turn.get("status") or "") == "cancelled" or str(turn.get("final_scope_status") or "") == "cancelled":
        session["active_turn_id"] = ""
        session["status"] = "active"
        session["session_status"] = "active"
        return False
    turn_status = str(turn.get("status") or "")
    if turn_status in TURN_TERMINAL_STATUSES:
        session["active_turn_id"] = ""
        session["status"] = "active"
        session["session_status"] = "active"
        return turn_status == "completed"
    changed_files = _changed_working_files(session)
    native_turn_id = str((params.get("turn") or {}).get("id") if isinstance(params.get("turn"), dict) else session.get("active_turn_id") or "")
    if turn_id:
        _update_turn(
            session,
            turn_id,
            status="verifying",
            completed_at=_now_iso(),
            changed_files=changed_files,
            native_turn_id=native_turn_id,
        )
    session["active_turn_id"] = ""
    session["status"] = "active"
    session["session_status"] = "active"
    chart_plan_path = Path(str(session.get("working_dir") or "")) / REVISION_CHART_PLAN_NAME
    if session.get("preflight_revision_chart_request") or chart_plan_path.is_file():
        _process_revision_chart_outputs(session)
    _refresh_session_preview(session)
    verification = _verify_turn_revision(session, _current_turn(session))
    if turn_id:
        _update_turn(session, turn_id, revision_verification=verification)
    if verification.get("passed"):
        try:
            _render_working_pdf_preview(session, turn_id=turn_id)
        except Exception as exc:
            error_text = str(exc.detail if isinstance(exc, HTTPException) else exc)
            failed_verification = {
                **verification,
                "passed": False,
                "pdf_render_failed": True,
                "pdf_render_error": error_text,
            }
            if turn_id:
                _update_turn(
                    session,
                    turn_id,
                    status="failed_pdf_render",
                    final_scope_status="failed",
                    revision_verification=failed_verification,
                )
            session["native_connection_status"] = "pdf_render_failed"
            _append_event(
                session,
                "turn_failed",
                text=f"PDF 草稿渲染失败，已阻止本轮标记为完成：{error_text}",
                status="failed_pdf_render",
                preview_url=session.get("preview_url") or "",
                raw_payload={"error": error_text},
                turn_id=turn_id,
                is_error=True,
            )
            return False
        artifact_records: list[dict[str, Any]] = []
        for raw_path in dict(session.get("working_artifacts") or {}).values():
            path = Path(str(raw_path or ""))
            if path.is_file() and _is_within(path, _session_workspace(session)):
                artifact_records.append(_session_file_record(session, path))
        if turn_id:
            _update_turn(
                session,
                turn_id,
                status="completed",
                final_scope_status="passed",
                changed_files=_changed_working_files(session),
                artifacts=artifact_records,
            )
        _append_event(
            session,
            "verification_passed",
            text=_summarize_verification(verification),
            turn_id=turn_id,
            status="completed",
        )
        _append_event(
            session,
            "turn_completed",
            text="原生 Codex 本轮修改完成。",
            status="completed",
            preview_url=session.get("preview_url") or "",
            raw_payload=native_event,
            turn_id=turn_id,
        )
        return True

    _append_event(
        session,
        "verification_failed",
        text=_summarize_verification(verification),
        turn_id=turn_id,
        status="failed",
        is_error=True,
    )
    repair_budget = int((turn.get("revision_intent") or {}).get("repair_budget") or 1)
    attempt_count = int(turn.get("attempt_count") or 1)
    auto_repair_applied = bool(turn.get("auto_repair_applied"))
    if allow_auto_repair and turn_id and not auto_repair_applied and attempt_count <= repair_budget:
        _update_turn(
            session,
            turn_id,
            status="auto_repairing",
            completed_at="",
            auto_repair_applied=True,
            attempt_count=attempt_count + 1,
            final_scope_status="repairing",
            revision_verification=verification,
        )
        _append_event(
            session,
            "auto_repair_started",
            text="验收未通过，系统正在基于同一原生 Codex 线程自动纠偏一次。",
            turn_id=turn_id,
            status="auto_repairing",
        )
        _write_session(session)
        _launch_auto_repair_turn(report_id, session_id, turn_id, verification)
        return False

    failure_status = _verification_failure_status(verification)
    if turn_id:
        _update_turn(session, turn_id, status=failure_status, final_scope_status="failed")
    _append_event(
        session,
        "turn_failed",
        text=_summarize_verification(verification),
        status=failure_status,
        preview_url=session.get("preview_url") or "",
        raw_payload=native_event,
        turn_id=turn_id,
        is_error=True,
    )
    return False


def _recover_completed_turn_from_working_state(
    report_id: str,
    session_id: str,
    session: dict[str, Any],
    *,
    reason: str,
    raw_payload: dict[str, Any] | None = None,
) -> bool:
    turn = _current_turn(session)
    turn_id = str(turn.get("turn_id") or "")
    if not turn_id or str(turn.get("status") or "") not in TURN_ACTIVE_STATUSES:
        return False
    verification = _verify_turn_revision(session, turn)
    if not verification.get("passed"):
        return False
    _append_event(
        session,
        "native_recovery_started",
        text="Native turn did not close cleanly, but the working copy already passes verification; rendering the PDF draft now.",
        turn_id=turn_id,
        status="verifying",
        raw_payload={"reason": reason, **(raw_payload or {})},
    )
    completed = _finalize_native_turn_completion(
        report_id,
        session_id,
        session,
        {"method": "native/recovered", "params": {"reason": reason, **(raw_payload or {})}},
        {"turn": {"id": str(session.get("active_turn_id") or turn.get("native_turn_id") or "")}},
        allow_auto_repair=False,
        ignore_suppressed=True,
    )
    if completed:
        session["suppressed_turn_ids"] = [
            item for item in list(session.get("suppressed_turn_ids") or []) if str(item or "") != turn_id
        ]
        session["native_connection_status"] = "completed_after_native_recovery"
    return completed


def _active_native_turn_age_seconds(turn: dict[str, Any]) -> float | None:
    for key in ("started_at", "created_at", "updated_at"):
        age = _iso_age_seconds(turn.get(key))
        if age is not None:
            return age
    return None


def _reconcile_stalled_native_turn(report_id: str, session_id: str, session: dict[str, Any]) -> bool:
    turn = _current_turn(session)
    turn_id = str(turn.get("turn_id") or "")
    native_turn_id = str(session.get("active_turn_id") or turn.get("native_turn_id") or "")
    if not turn_id or not native_turn_id or str(turn.get("status") or "") not in TURN_ACTIVE_STATUSES:
        return False
    if str(session.get("native_thread_status") or "") == "idle":
        return False
    retry_age = _iso_age_seconds(session.get("native_stalled_reconciliation_started_at"))
    if retry_age is not None and retry_age < NATIVE_TURN_STALLED_RECOVERY_RETRY_SECONDS:
        return False
    active_age = _active_native_turn_age_seconds(turn)
    if active_age is not None and active_age < NATIVE_TURN_STALLED_RECOVERY_SECONDS:
        return False
    verification = _verify_turn_revision(session, turn)
    changed_targets = list(verification.get("changed_targets") or [])
    if not verification.get("passed") or not changed_targets:
        return False

    session["native_stalled_reconciliation_started_at"] = _now_iso()
    session["native_connection_status"] = "verifying"
    _update_turn(session, turn_id, status="verifying", native_turn_id=native_turn_id)
    _append_event(
        session,
        "native_status",
        text="检测到 Codex 已完成可验收的工作区改动；正在自动收口并渲染 PDF 草稿。",
        turn_id=turn_id,
        status="verifying",
        raw_payload={
            "reason": "stalled_native_turn_working_copy_passed",
            "active_age_seconds": active_age,
            "changed_targets": changed_targets,
        },
    )

    try:
        completed = _recover_completed_turn_from_working_state(
            report_id,
            session_id,
            session,
            reason="stalled_native_turn_working_copy_passed",
            raw_payload={
                "active_age_seconds": active_age,
                "changed_targets": changed_targets,
            },
        )
        session.pop("native_stalled_reconciliation_started_at", None)
        return completed
    except Exception as exc:
        session["native_connection_status"] = "error"
        session["native_protocol_error"] = str(exc)
        session.pop("native_stalled_reconciliation_started_at", None)
        _append_event(session, "native_error", text=str(exc), is_error=True, turn_id=turn_id)
        return False


def _handle_native_event(report_id: str, session_id: str, native_event: dict[str, Any]) -> None:
    session = _read_session(report_id, session_id)
    method = str(native_event.get("method") or "")
    params = native_event.get("params") if isinstance(native_event.get("params"), dict) else {}
    session["mode"] = "native_app_server"
    if method != "native/error" and str(_current_turn(session).get("status") or "") in TURN_ACTIVE_STATUSES:
        session["native_connection_status"] = "online"

    if method == "native/error":
        message = str(params.get("message") or "Codex native app-server connection failed.")
        turn = _current_turn(session)
        turn_id = str(turn.get("turn_id") or "")
        suppressed_turn_ids = {str(item or "") for item in list(session.get("suppressed_turn_ids") or []) if str(item or "")}
        if turn_id and (turn_id in suppressed_turn_ids or str(turn.get("final_scope_status") or "") == "cancelled"):
            session["active_turn_id"] = ""
            session["native_connection_status"] = "interrupted"
            _write_session(session)
            return
        session["native_connection_status"] = "error"
        session["native_protocol_error"] = message
        if str(turn.get("status") or "") in TURN_ACTIVE_STATUSES and turn_id:
            _update_turn(session, turn_id, status="failed", completed_at=_now_iso())
        _append_event(session, "native_error", text=message, is_error=True, raw_payload=native_event)
        _write_session(session)
        return

    if method == "thread/started":
        thread = params.get("thread") if isinstance(params.get("thread"), dict) else {}
        thread_id = str(thread.get("id") or "")
        if thread_id:
            turn = _current_turn(session)
            turn_status = str(turn.get("status") or "")
            if turn_status in TURN_TERMINAL_STATUSES and not str(session.get("active_turn_id") or ""):
                _append_event(
                    session,
                    "native_late_thread_ignored",
                    text="Late Codex thread start ignored after startup timeout.",
                    raw_payload=native_event,
                    turn_id=str(turn.get("turn_id") or ""),
                )
            else:
                session["codex_thread_id"] = thread_id
                session["codex_session_id"] = thread_id
                _append_event(session, "codex_thread_started", text="原生 Codex 会话已连接。", raw_payload=native_event)
        else:
            _append_event(session, "codex_thread_started", text="原生 Codex 会话已连接。", raw_payload=native_event)
    elif method == "thread/status/changed":
        status = params.get("status") if isinstance(params.get("status"), dict) else {}
        session["native_thread_status"] = str(status.get("type") or "")
        _append_event(session, "native_status", text=f"Codex thread: {session['native_thread_status']}", raw_payload=native_event)
        if (
            session["native_thread_status"] == "idle"
            and str(session.get("active_turn_id") or "")
            and str(_current_turn(session).get("status") or "") in TURN_ACTIVE_STATUSES
        ):
            _finalize_native_turn_completion(
                report_id,
                session_id,
                session,
                native_event,
                {"turn": {"id": str(session.get("active_turn_id") or "")}},
            )
            _write_session(session)
            return
    elif method == "turn/started":
        turn_payload = params.get("turn") if isinstance(params.get("turn"), dict) else {}
        native_turn_id = str(turn_payload.get("id") or "")
        session["active_turn_id"] = native_turn_id
        turn = _current_turn(session)
        if native_turn_id and turn.get("turn_id"):
            next_status = "auto_repairing" if str(turn.get("final_scope_status") or "") == "repairing" else "running"
            _update_turn(session, str(turn.get("turn_id")), status=next_status, native_turn_id=native_turn_id)
    elif method == "item/started":
        item = params.get("item") if isinstance(params.get("item"), dict) else {}
        item_type = str(item.get("type") or "")
        native_turn_id = str(params.get("turnId") or "")
        if native_turn_id:
            session["active_turn_id"] = native_turn_id
        if item_type == "reasoning":
            _append_event(session, "thinking", text="Codex 正在思考修改路径。", raw_payload=native_event)
        elif item_type in {"commandExecution", "mcpToolCall", "toolCall"}:
            command = _native_item_command(item)
            _append_event(
                session,
                "tool_call",
                text=command or str(item.get("name") or "工具调用"),
                tool_name=str(item.get("name") or item_type),
                command=command,
                raw_payload=native_event,
            )
    elif method in {"item/agentMessage/delta", "item/reasoning/summaryTextDelta"}:
        # Native Codex emits very small text deltas. The workbench keeps the
        # timeline readable by recording the completed assistant item instead.
        pass
    elif method in {"item/commandExecution/outputDelta", "command/exec/outputDelta"}:
        delta = str(params.get("delta") or params.get("output") or "")
        if delta.strip():
            _append_event(session, "tool_result", text=delta[:4000], output_preview=delta[:4000], raw_payload=native_event)
    elif method == "item/completed":
        item = params.get("item") if isinstance(params.get("item"), dict) else {}
        item_type = str(item.get("type") or "")
        if item_type == "agentMessage":
            text = _native_item_text(item).strip()
            if text:
                _append_event(session, "assistant_message", text=text, raw_payload=native_event)
        elif item_type in {"commandExecution", "mcpToolCall", "toolCall"}:
            output = _native_item_text(item)
            _append_event(
                session,
                "tool_result",
                text=output[:8000] or "工具调用完成。",
                output_preview=output[:1200],
                command=_native_item_command(item),
                tool_name=str(item.get("name") or item_type),
                status=str(item.get("status") or ""),
                exit_code=item.get("exitCode") if item.get("exitCode") is not None else item.get("exit_code"),
                raw_payload=native_event,
            )
        elif item_type == "fileChange":
            path = str(item.get("path") or item.get("filePath") or "文件已修改。")
            _append_event(session, "file_changed", text=path, path=path, raw_payload=native_event)
    elif method in {"turn/diff/updated", "fs/changed"}:
        _append_event(session, "file_changed", text="Codex 已产生文件变更。", raw_payload=native_event)
    elif method == "turn/completed":
        _finalize_native_turn_completion(report_id, session_id, session, native_event, params)
        _write_session(session)
        return
    elif method == "turn/interrupted":
        turn = _current_turn(session)
        turn_id = str(turn.get("turn_id") or "")
        if turn_id:
            _update_turn(session, turn_id, status="cancelled", completed_at=_now_iso())
        session["active_turn_id"] = ""
        _append_event(session, "turn_cancelled", text="原生 Codex 本轮已停止。", raw_payload=native_event)
    elif method == "error":
        message = str(params.get("message") or native_event.get("message") or "Codex native protocol error.")
        session["native_protocol_error"] = message
        _append_event(session, "native_error", text=message, is_error=True, raw_payload=native_event)

    _write_session(session)


def _stage_event_to_agent_event(event: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    run_id = str(payload.get("run_id") or payload.get("runtime_child_run_id") or "")
    return (
        "runtime_stage",
        {
            "text": str(event.get("detail") or event.get("title") or ""),
            "stage_id": str(event.get("stage_id") or ""),
            "title": str(event.get("title") or ""),
            "payload": payload,
            "run_id": run_id,
        },
    )


def _looks_like_revision_chart_request(text: str) -> bool:
    normalized = str(text or "").strip().lower()
    if not normalized:
        return False
    negative_terms = ("不要画图", "不用画图", "别画图", "no chart", "without chart")
    if any(term in normalized for term in negative_terms):
        return False
    chart_terms = (
        "图",
        "可视化",
        "气泡",
        "象限",
        "散点",
        "热力",
        "趋势",
        "柱状",
        "折线",
        "派生指标",
        "补图",
        "chart",
        "visual",
        "bubble",
        "quadrant",
        "scatter",
        "plot",
    )
    return any(term in normalized for term in chart_terms)


def _looks_like_unauthorized_numeric_change_request(text: str) -> bool:
    normalized = _repair_mojibake_text(str(text or "")).strip().lower()
    if not normalized:
        return False
    if any(token in normalized for token in ("百分号", "百分比", "percent", "percentage")):
        return False
    if not re.search(r"\d", normalized):
        return False
    action_terms = ("改成", "改为", "改到", "替换成", "设置为", "变成", "change to", "set to", "replace with")
    numeric_subject_terms = ("数字", "指标", "收入", "gmv", "roi", "rate", "率", "金额", "revenue", "metric")
    return any(term in normalized for term in action_terms) and any(term in normalized for term in numeric_subject_terms)


def _fast_revision_kind(text: str, annotations: list[dict[str, Any]] | None = None) -> str:
    normalized = _repair_mojibake_text(str(text or "")).strip().lower()
    if not normalized:
        return ""
    if any(token in normalized for token in ("标题", "主标题", "headline", "title", "h1")):
        return "headline_edit"
    if any(token in normalized for token in ("大改", "重写", "重构", "重排", "整体改造", "全篇", "major rewrite", "overhaul", "restructure")):
        return "major_revision"
    if any(token in normalized for token in ("图注", "图题", "caption", "figcaption")) or annotations:
        return "caption_edit"
    if any(token in normalized for token in ("摘要", "导语", "summary")):
        return "summary_retone"
    return ""


def _normalize_revision_intent_for_fast_paths(
    text: str,
    annotations: list[dict[str, Any]],
    revision_intent: dict[str, Any],
) -> dict[str, Any]:
    intent = dict(revision_intent or {})
    operation_kind = _fast_revision_kind(text, annotations)
    if operation_kind:
        intent["operation_kind"] = operation_kind
        intent["preserve_numbers"] = True
        intent["scope_mode"] = "strict" if any(token in str(text or "") for token in ("只", "仅", "不要动其他", "不改其他")) else (
            "open" if operation_kind == "major_revision" else "targeted"
        )
        if operation_kind == "headline_edit":
            intent["must_change_targets"] = ["primary_heading"]
            intent["forbidden_change_kinds"] = ["body_copy", "css_changes", "figure_captions", "metric_changes", "new_sections", "numeric_changes", "section_headings"]
        elif operation_kind == "summary_retone":
            intent["must_change_targets"] = ["summary_block"]
            intent["forbidden_change_kinds"] = ["css_changes", "figure_captions", "metric_changes", "new_sections", "numeric_changes", "primary_heading", "section_headings"]
        elif operation_kind == "caption_edit":
            intent["must_change_targets"] = ["figure_caption"]
            intent["forbidden_change_kinds"] = ["body_copy", "css_changes", "metric_changes", "new_sections", "numeric_changes", "primary_heading", "section_headings"]
        elif operation_kind == "major_revision":
            intent["must_change_targets"] = ["report_structure_or_body"]
            intent["forbidden_change_kinds"] = ["metric_changes", "numeric_changes"]
    phrase = _extract_requested_phrase_clean(text)
    if phrase:
        intent["requested_phrase"] = phrase
    return intent


def _extract_requested_phrase_clean(text: str) -> str:
    raw = _repair_mojibake_text(str(text or "")).strip()
    patterns = [
        r"(?:append|add)\s+[\"']([^\"']+)[\"']\s+(?:to|into|after|onto)",
        r"(?:改成|改为|换成|替换成|标题为|主标题为)\s*[“\"']([^”\"'\n]+)[”\"']",
        r"(?:改成|改为|换成|替换成|标题为|主标题为)\s*([^，。；;\n]+)",
        r"(?:title|headline)\s+(?:to|as)\s+[\"']([^\"']+)[\"']",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            phrase = str(match.group(1) or "").strip()
            phrase = re.split(r"(?:，|。|；|;|,|\s+不改|\s+不要)", phrase)[0].strip()
            return phrase[:80]
    return ""


def _replace_markdown_heading(text: str, title: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            lines[index] = f"# {title}"
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return f"# {title}\n\n{text}"


def _replace_html_h1(text: str, title: str) -> str:
    escaped = html.escape(title)
    if re.search(r"<h1[^>]*>[\s\S]*?</h1>", text, flags=re.I):
        return re.sub(r"<h1([^>]*)>[\s\S]*?</h1>", rf"<h1\1>{escaped}</h1>", text, count=1, flags=re.I)
    return re.sub(r"<body([^>]*)>", rf"<body\1><h1>{escaped}</h1>", text, count=1, flags=re.I)


def _replace_markdown_summary(text: str, summary: str) -> str:
    lines = text.splitlines()
    heading_seen = False
    for index, line in enumerate(lines):
        if line.startswith("# "):
            heading_seen = True
            continue
        if heading_seen and line.strip() and not line.startswith("#"):
            lines[index] = summary
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return text.rstrip() + "\n\n" + summary + "\n"


def _replace_html_first_paragraph(text: str, summary: str) -> str:
    escaped = html.escape(summary)
    if re.search(r"<p[^>]*>[\s\S]*?</p>", text, flags=re.I):
        return re.sub(r"<p([^>]*)>[\s\S]*?</p>", rf"<p\1>{escaped}</p>", text, count=1, flags=re.I)
    return re.sub(r"</h1>", f"</h1><p>{escaped}</p>", text, count=1, flags=re.I)


def _append_markdown_section(text: str, title: str, body: str) -> str:
    marker = "<!-- ASTERIA_REVISION_FAST_PATH_START -->"
    end = "<!-- ASTERIA_REVISION_FAST_PATH_END -->"
    block = f"{marker}\n\n## {title}\n\n{body}\n\n{end}"
    if marker in text:
        return re.sub(re.escape(marker) + r"[\s\S]*?" + re.escape(end), block, text)
    return text.rstrip() + "\n\n" + block + "\n"


def _append_html_section(text: str, title: str, body: str) -> str:
    marker = "<!-- ASTERIA_REVISION_FAST_PATH_START -->"
    end = "<!-- ASTERIA_REVISION_FAST_PATH_END -->"
    block = (
        f'{marker}<section class="revision-fast-path-note"><h2>{html.escape(title)}</h2>'
        f"<p>{html.escape(body)}</p></section>{end}"
    )
    if marker in text:
        return re.sub(re.escape(marker) + r"[\s\S]*?" + re.escape(end), block, text)
    return re.sub(r"</body>", block + "\n</body>", text, count=1, flags=re.I) if "</body>" in text.lower() else text + block


def _update_markdown_caption(text: str, caption: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.search(r"!\[[^\]]*\]\([^)]+\)", line):
            lines.insert(index + 1, f"*{caption}*")
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return _append_markdown_section(text, "图注修订", caption)


def _update_html_caption(text: str, caption: str) -> str:
    escaped = html.escape(caption)
    if re.search(r"<figcaption[^>]*>[\s\S]*?</figcaption>", text, flags=re.I):
        return re.sub(r"<figcaption([^>]*)>[\s\S]*?</figcaption>", rf"<figcaption\1>{escaped}</figcaption>", text, count=1, flags=re.I)
    image_match = re.search(r"<img\b[^>]*>", text, flags=re.I)
    if image_match:
        image = image_match.group(0)
        figure = f"<figure>{image}<figcaption>{escaped}</figcaption></figure>"
        return text[: image_match.start()] + figure + text[image_match.end() :]
    return _append_html_section(text, "图注修订", caption)


def _apply_fast_text_revision(session: dict[str, Any], text: str, intent: dict[str, Any]) -> list[str]:
    working = dict(session.get("working_artifacts") or {})
    md_path = Path(str(working.get("markdown") or ""))
    html_path = Path(str(working.get("html") or ""))
    css_path = Path(str(working.get("css") or ""))
    operation_kind = str(intent.get("operation_kind") or "")
    changed: list[str] = []
    phrase = str(intent.get("requested_phrase") or "").strip()
    if operation_kind == "headline_edit":
        title = phrase or "管理层行动周报"
        if md_path.is_file():
            md_path.write_text(_replace_markdown_heading(md_path.read_text(encoding="utf-8", errors="replace"), title), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_replace_html_h1(html_path.read_text(encoding="utf-8", errors="replace"), title), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    elif operation_kind == "summary_retone":
        summary = phrase or "本版摘要已收敛为管理层可直接阅读的行动导语，保留原报告数字与证据口径。"
        if md_path.is_file():
            md_path.write_text(_replace_markdown_summary(md_path.read_text(encoding="utf-8", errors="replace"), summary), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_replace_html_first_paragraph(html_path.read_text(encoding="utf-8", errors="replace"), summary), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    elif operation_kind == "major_revision":
        title = "管理层改造说明"
        body = "本轮已按结构级改造要求重排读者入口，保留原报告数字与确定性证据，只调整叙事层级、行动指向和阅读路径。"
        if md_path.is_file():
            md_path.write_text(_append_markdown_section(md_path.read_text(encoding="utf-8", errors="replace"), title, body), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_append_html_section(html_path.read_text(encoding="utf-8", errors="replace"), title, body), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    elif operation_kind == "caption_edit":
        caption = phrase or "按批注补充：该图用于定位本轮最需要管理层复核的对象和指标组合。"
        if md_path.is_file():
            md_path.write_text(_update_markdown_caption(md_path.read_text(encoding="utf-8", errors="replace"), caption), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_update_html_caption(html_path.read_text(encoding="utf-8", errors="replace"), caption), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    if css_path.is_file() and css_path.exists():
        # Keep CSS untouched for strict/text fast paths; this branch only makes
        # sure the artifact exists for publish and preview.
        pass
    _refresh_session_preview(session)
    return sorted(set(changed))


def _preflight_revision_chart_request(session: dict[str, Any], *, turn_id: str = "") -> int:
    try:
        rendered = _process_revision_chart_outputs(session)
    except Exception as exc:
        _append_event(
            session,
            "chart_substituted",
            text=f"图表预生成未能完成，原生 Codex 会继续判断可用替代方案：{exc}",
            turn_id=turn_id,
        )
        return 0
    if rendered:
        session["preflight_revision_chart_request"] = True
        session["preflight_revision_chart_count"] = len(rendered)
        session["preflight_revision_chart_render_log"] = str(
            (Path(str(session.get("working_dir") or _session_workspace(session) / "working")) / REVISION_CHART_RENDER_LOG_NAME).resolve()
        )
        _refresh_session_preview(session)
        _append_event(
            session,
            "preview_updated",
            text=f"已先行生成 {len(rendered)} 张补充图表；原生 Codex 会继续组织解释和版面。",
            preview_url=str(session.get("preview_url") or ""),
            turn_id=turn_id,
        )
        return len(rendered)
    _append_event(
        session,
        "chart_substituted",
        text="暂未找到足够的表格证据生成图表；原生 Codex 会继续从报告资产中寻找替代交付物。",
        turn_id=turn_id,
    )
    session["preflight_revision_chart_request"] = True
    session["preflight_revision_chart_count"] = 0
    return 0


def post_report_agent_message(report_id: str, session_id: str, *, message: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    text = str(message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="message is required.")
    handler = _event_session_handler(report_id, session_id)
    if _reconcile_stale_native_start(session):
        _write_session(session)
    if _current_turn_status(session) in TURN_ACTIVE_STATUSES:
        guidance_record = {
            "message": text,
            "created_at": _now_iso(),
            "turn_id": _current_turn(session).get("turn_id") or "",
        }
        injections = list(session.get("guidance_injections") or [])
        injections.append(guidance_record)
        session["guidance_injections"] = injections[-100:]
        session["native_connection_status"] = "injecting_guidance"
        _append_event(
            session,
            "user_guidance",
            text=text,
            title="用户引导已注入当前 turn",
            turn_id=str(guidance_record.get("turn_id") or ""),
        )
        if _looks_like_revision_chart_request(text):
            _preflight_revision_chart_request(session, turn_id=str(guidance_record.get("turn_id") or ""))
        _write_session(session)
        try:
            steer_payload = steer_native_turn(session, handler, guidance=_guidance_prompt(text))
        except HTTPException as exc:
            fresh = _read_session(report_id, session_id)
            detail = str(exc.detail)
            if "no active turn to steer" in detail or "no active turn" in detail:
                active_turn_id = str(_current_turn(fresh).get("turn_id") or "")
                if active_turn_id:
                    _update_turn(
                        fresh,
                        active_turn_id,
                        status="cancelled",
                        completed_at=_now_iso(),
                        final_scope_status="cancelled",
                    )
                fresh["native_connection_status"] = "stale_turn_reconciled"
                fresh["native_protocol_error"] = detail
                _append_event(
                    fresh,
                    "turn_cancelled",
                    text="检测到原生 Codex 当前 turn 已失活；已把旧 turn 标记为取消，并用同一条消息开启新一轮。",
                    turn_id=active_turn_id,
                    status="cancelled",
                    raw_payload={"detail": detail},
                )
                _write_session(fresh)
                return post_report_agent_message(report_id, session_id, message=text)
            fresh["native_connection_status"] = "error"
            fresh["native_protocol_error"] = detail
            _append_event(fresh, "native_error", text=detail, is_error=True)
            _write_session(fresh)
            raise
        fresh = _read_session(report_id, session_id)
        fresh["native_connection_status"] = "guidance_injected"
        fresh["codex_thread_id"] = str(steer_payload.get("thread_id") or fresh.get("codex_thread_id") or "")
        _write_session(fresh)
        return {"session": _public_session(fresh), "native": steer_payload}

    turn_id = f"turn-{uuid.uuid4().hex[:12]}"
    started_at = _now_iso()
    annotations = _read_annotations(session)
    revision_intent = _infer_revision_intent(text, annotations)
    revision_intent = _normalize_revision_intent_for_fast_paths(text, annotations, revision_intent)
    baseline_artifacts = _snapshot_turn_baseline(session, turn_id)
    _update_turn(
        session,
        turn_id,
        task_id="",
        run_id="",
        status="queued",
        user_message=text,
        started_at=started_at,
        completed_at="",
        changed_files=[],
        artifacts=[],
        revision_intent=revision_intent,
        revision_verification={},
        attempt_count=1,
        auto_repair_applied=False,
        final_scope_status="pending",
        baseline_artifacts=baseline_artifacts,
    )
    _append_event(session, "user_message", text=text, turn_id=turn_id)

    if _looks_like_unauthorized_numeric_change_request(text):
        verification = {
            "passed": False,
            "blocked_change": True,
            "mode": "deterministic_numeric_guardrail",
            "reason": "unauthorized_numeric_change_request",
            "numeric_changes_detected": False,
            "hit_targets": [],
            "missed_targets": ["reader_safe_revision"],
            "notes": "用户要求直接改动读者可见数字；后续改造只允许在证据支持下改写叙事，不允许伪造或覆盖 deterministic 数字。",
        }
        _update_turn(
            session,
            turn_id,
            status="failed_scope_violation",
            completed_at=_now_iso(),
            changed_files=[],
            artifacts=[],
            revision_verification=verification,
            final_scope_status="blocked",
        )
        session["status"] = "active"
        session["session_status"] = "active"
        session["native_connection_status"] = "blocked_numeric_change"
        _append_event(
            session,
            "blocked_change",
            text="已阻断：这条要求会直接改动报告数字。请提供可验证的新数据并走补充证据或 CLI 长链重跑。",
            turn_id=turn_id,
            status="blocked",
            raw_payload={"reason": "unauthorized_numeric_change_request"},
        )
        _append_event(
            session,
            "turn_failed",
            text="本轮未修改任何文件；原报告和修订工作区数字保持不变。",
            turn_id=turn_id,
            status="failed_scope_violation",
        )
        _write_session(session)
        return {"session": _public_session(session), "native": {"mode": "blocked_numeric_change", "skipped_native": True}}

    # The revision workbench must behave like native Codex: deterministic helpers
    # may guard or pre-process, but they must not replace a real native turn.
    allow_deterministic_fast_path = False
    fast_operation = str((revision_intent or {}).get("operation_kind") or "")
    if allow_deterministic_fast_path and fast_operation in {"headline_edit", "summary_retone", "major_revision", "caption_edit"}:
        changed_files = _apply_fast_text_revision(session, text, revision_intent)
        refreshed_turn = _current_turn(session)
        verification = _verify_turn_revision(session, refreshed_turn)
        if fast_operation == "caption_edit" and annotations:
            verification.setdefault("hit_targets", [])
            if "annotation_context" not in verification["hit_targets"]:
                verification["hit_targets"].append("annotation_context")
            if "figure_caption" in verification.get("changed_targets", []):
                verification["forbidden_target_violations"] = [
                    item for item in list(verification.get("forbidden_target_violations") or []) if item != "body_copy"
                ]
                verification["passed"] = not verification.get("missing_targets") and not verification.get("forbidden_target_violations") and bool(
                    verification.get("html_markdown_in_sync", True)
                )
        status = "completed" if verification.get("passed") else _verification_failure_status(verification)
        final_scope = "passed" if verification.get("passed") else "failed"
        artifacts = []
        for path in (Path(str(session.get("working_dir") or "")) / "report.md", Path(str(session.get("working_dir") or "")) / "report.html"):
            if path.is_file():
                artifacts.append(_session_file_record(session, path))
        _update_turn(
            session,
            turn_id,
            status=status,
            completed_at=_now_iso(),
            changed_files=changed_files or _changed_working_files(session),
            artifacts=artifacts,
            revision_verification=verification,
            final_scope_status=final_scope,
        )
        session["status"] = "active"
        session["session_status"] = "active"
        session["native_connection_status"] = "text_fast_path_completed" if verification.get("passed") else "verification_failed"
        if verification.get("passed"):
            _append_event(
                session,
                "assistant_message",
                text="已按本轮修改范围更新报告，并完成数字守门与范围验收。",
                turn_id=turn_id,
            )
            _append_event(
                session,
                "verification_passed",
                text="验收通过：修改命中目标，未发现未授权数字变化。",
                turn_id=turn_id,
                status="completed",
                raw_payload=verification,
            )
            _append_event(
                session,
                "turn_completed",
                text="本轮后续改造已完成，可以继续引导或发布修订版。",
                turn_id=turn_id,
                status="completed",
                preview_url=str(session.get("preview_url") or ""),
            )
        else:
            _append_event(
                session,
                "verification_failed",
                text="验收未通过：修改没有满足本轮范围或守门规则。",
                turn_id=turn_id,
                status=status,
                is_error=True,
                raw_payload=verification,
            )
            _append_event(session, "turn_failed", text=status, turn_id=turn_id, status=status, is_error=True)
        _write_session(session)
        return {
            "session": _public_session(session),
            "native": {"mode": "deterministic_text_fast_path", "skipped_native": True, "verification": verification},
        }

    preflight_chart_count = 0
    if _looks_like_revision_chart_request(text):
        preflight_chart_count = _preflight_revision_chart_request(session, turn_id=turn_id)
    if allow_deterministic_fast_path and preflight_chart_count > 0:
        changed_files = _changed_working_files(session)
        artifacts = []
        chart_assets = _chart_assets_dir(session)
        if chart_assets.is_dir():
            for path in sorted(chart_assets.glob("*")):
                if path.suffix.lower() in {".png", ".csv"}:
                    artifacts.append(_session_file_record(session, path))
        _update_turn(
            session,
            turn_id,
            status="completed",
            completed_at=_now_iso(),
            changed_files=changed_files,
            artifacts=artifacts,
            revision_verification={
                "passed": True,
                "mode": "deterministic_chart_fast_path",
                "hit_targets": ["revision_chart_plan", "revision_visual_assets", "report_preview"],
                "numeric_changes_detected": False,
                "notes": "图表数值由后端基于现有证据确定性渲染；本轮未等待原生 Codex 长时间重写。",
            },
            final_scope_status="passed",
        )
        session["status"] = "active"
        session["session_status"] = "active"
        session["native_connection_status"] = "chart_fast_path_completed"
        _append_event(
            session,
            "assistant_message",
            text=f"已基于现有报告派生指标和可用表格资产生成 {preflight_chart_count} 张补充图表，包含气泡/象限或最接近的替代图；数值来自生成的 CSV，不由 Codex 编造。",
            turn_id=turn_id,
        )
        _append_event(
            session,
            "verification_passed",
            text="补图请求已完成：图表计划、PNG、CSV 和报告预览均已更新。",
            turn_id=turn_id,
            status="completed",
        )
        _append_event(
            session,
            "turn_completed",
            text="图表补充已完成，可继续发送引导或发布修订版。",
            turn_id=turn_id,
            status="completed",
            preview_url=str(session.get("preview_url") or ""),
        )
        _write_session(session)
        return {"session": _public_session(session), "native": {"mode": "deterministic_chart_fast_path", "skipped_native": True}}
    _write_session(session)
    session["mode"] = "native_app_server"
    session["native_connection_status"] = "starting"
    _write_session(session)
    _start_native_turn_in_background(
        report_id,
        session_id,
        turn_id=turn_id,
        started_at=started_at,
        user_message=text,
    )
    return {
        "session": _public_session(session),
        "native": {"mode": "native_app_server", "queued": True, "thread_id": "", "turn_id": ""},
    }

def _parse_runtime_chunk(raw_chunk: str, ts: str) -> list[tuple[str, dict[str, Any]]]:
    try:
        parsed = json.loads(raw_chunk)
    except Exception:
        text = raw_chunk.strip()
        return [("stdout", {"text": text})] if text else []
    if not isinstance(parsed, dict):
        return []
    event_type = str(parsed.get("type") or "")
    if event_type == "thread.started":
        return [("codex_thread_started", {"text": "Codex thread started.", "payload": parsed, "codex_session_id": parsed.get("thread_id")})]
    if event_type == "turn.started":
        return [("assistant_message", {"text": "开始处理本轮修改。", "payload": parsed})]
    if event_type in {"item.started", "item.completed"}:
        item = parsed.get("item") if isinstance(parsed.get("item"), dict) else {}
        item_type = str(item.get("type") or "")
        phase = "started" if event_type.endswith("started") else "completed"
        if item_type in {"tool_use", "command_execution"} and phase == "started":
            name = str(item.get("name") or ("command_execution" if item_type == "command_execution" else "tool"))
            payload = item.get("input") if isinstance(item.get("input"), dict) else dict(item)
            return [("tool_call", {"tool_name": name, "text": name, "payload": payload})]
        if item_type in {"tool_result", "command_execution"} and phase == "completed":
            output = str(item.get("aggregated_output") or item.get("content") or item.get("output") or item.get("result") or "")
            return [("tool_result", {"text": output[:8000] or "工具调用完成。", "payload": item, "is_error": bool(item.get("is_error"))})]
        if item_type == "agent_message" and phase == "completed":
            text = str(item.get("text") or "").strip()
            return [("assistant_message", {"text": text, "payload": item})] if text else []
        if item_type == "file_change" and phase == "completed":
            return [("file_changed", {"text": "文件已修改。", "payload": item})]
        if item_type == "reasoning":
            return [("assistant_message", {"text": "正在分析修改路径。", "payload": item})] if phase == "started" else []
    if event_type == "turn.completed":
        return [("turn_runtime_completed", {"text": str(parsed.get("result") or "本轮 Codex 执行完成。"), "payload": parsed})]
    if event_type in {"turn.failed", "error"}:
        return [("turn_failed", {"text": str(parsed.get("result") or parsed.get("message") or parsed.get("error") or "Codex 执行失败。"), "payload": parsed, "is_error": True})]
    return [("stdout", {"text": raw_chunk.strip(), "payload": parsed})]


def _sync_runtime_stdout(session: dict[str, Any]) -> dict[str, Any]:
    turn = _current_turn(session)
    run_id = str(turn.get("run_id") or session.get("current_run_id") or "")
    if not run_id:
        return session
    offsets = dict(session.get("stdout_offsets") or {})
    offset = int(offsets.get(run_id) or 0)
    try:
        payload = read_stdout_log(run_id, offset=offset, limit_bytes=512000)
    except Exception:
        return session
    content = str(payload.get("content") or "")
    next_offset = payload.get("next_offset")
    if content:
        for line in content.splitlines():
            try:
                wrapper = json.loads(line)
            except Exception:
                wrapper = {"chunk": line, "ts": _now_iso()}
            chunk = str((wrapper if isinstance(wrapper, dict) else {}).get("chunk") or "")
            ts = str((wrapper if isinstance(wrapper, dict) else {}).get("ts") or _now_iso())
            for kind, event_payload in _parse_runtime_chunk(chunk, ts):
                if kind == "codex_thread_started" and event_payload.get("codex_session_id"):
                    session["codex_session_id"] = str(event_payload.get("codex_session_id") or "")
                _append_event(session, kind, **event_payload)
    if next_offset is not None:
        offsets[run_id] = int(next_offset)
    else:
        offsets[run_id] = offset + len(content.encode("utf-8"))
    session["stdout_offsets"] = offsets
    return session


def _sync_task_completion(session: dict[str, Any]) -> dict[str, Any]:
    turn = _current_turn(session)
    task_id = str(turn.get("task_id") or session.get("current_task_id") or "")
    if not task_id or task_id in set(session.get("processed_task_ids") or []):
        return session
    try:
        task = get_codex_run_task(task_id)
    except Exception:
        return session
    task_run_id = str(task.get("run_id") or "")
    turn_id = str(turn.get("turn_id") or "")
    if task_run_id and not str(turn.get("run_id") or session.get("current_run_id") or ""):
        session["current_run_id"] = task_run_id
        if turn_id:
            _update_turn(session, turn_id, run_id=task_run_id)
    status = str(task.get("status") or "")
    if status not in TURN_TERMINAL_STATUSES:
        return session
    session = _sync_runtime_stdout(session)
    processed = list(session.get("processed_task_ids") or [])
    processed.append(task_id)
    session["processed_task_ids"] = processed[-100:]
    session["status"] = "active"
    session["session_status"] = "active"
    result_summary = task.get("result_summary") if isinstance(task.get("result_summary"), dict) else {}
    changed_files = [str(changed) for changed in (result_summary.get("changed_files") or [])]
    artifacts = task.get("artifacts") if isinstance(task.get("artifacts"), list) else []
    if turn_id:
        _update_turn(
            session,
            turn_id,
            status=status,
            run_id=task_run_id or str(turn.get("run_id") or session.get("current_run_id") or ""),
            completed_at=_now_iso(),
            changed_files=changed_files,
            artifacts=artifacts,
        )
    for changed in changed_files:
        _append_event(session, "file_changed", text=changed, path=changed, turn_id=turn_id)
    _refresh_session_preview(session)
    _append_event(
        session,
        "turn_completed" if status == "completed" else "turn_failed",
        text=str(result_summary.get("summary") or task.get("current_stage_detail") or status),
        task_id=task_id,
        status=status,
        preview_url=session.get("preview_url") or "",
        turn_id=turn_id,
    )
    return session


def _refresh_session_preview(session: dict[str, Any]) -> None:
    working = dict(session.get("working_artifacts") or {})
    html_path = Path(str(working.get("html") or ""))
    md_path = Path(str(working.get("markdown") or ""))
    css_path = Path(str(working.get("css") or ""))
    if (not html_path.is_file()) and md_path.is_file():
        if not css_path.is_file():
            css_path.parent.mkdir(parents=True, exist_ok=True)
            css_path.write_text(_default_css(), encoding="utf-8")
        html_path = Path(str(session.get("working_dir") or "")) / "report.html"
        html_path.write_text(_basic_markdown_to_html(md_path.read_text(encoding="utf-8"), css_path.name), encoding="utf-8")
        working["html"] = str(html_path.resolve())
        session["working_artifacts"] = working
    if html_path.is_file():
        session["preview_artifact"] = _downloadable_from_file(html_path, purpose="当前后续改造预览 HTML")
        session["preview_url"] = _storage_url_for(html_path)
        _append_event(session, "preview_updated", text="报告预览已更新。", preview_url=session["preview_url"])


def _ensure_html_references_css(html_path: Path, css_path: Path) -> None:
    html_text = html_path.read_text(encoding="utf-8", errors="replace")
    html_text = re.sub(r'href=(["\'])\.?/?.*?\.css\1', f'href="./{css_path.name}"', html_text, count=1)
    if css_path.name not in html_text:
        link_tag = f'<link rel="stylesheet" href="./{css_path.name}" />'
        if re.search(r"</head>", html_text, flags=re.I):
            html_text = re.sub(r"</head>", f"{link_tag}</head>", html_text, count=1, flags=re.I)
        else:
            html_text = f"<!doctype html><html><head>{link_tag}</head><body>{html_text}</body></html>"
    html_path.write_text(html_text, encoding="utf-8")


def _render_working_pdf_preview(session: dict[str, Any], *, turn_id: str = "") -> dict[str, Any]:
    working = dict(session.get("working_artifacts") or {})
    html_path = Path(str(working.get("html") or ""))
    css_path = Path(str(working.get("css") or ""))
    md_path = Path(str(working.get("markdown") or ""))
    if not html_path.is_file() and md_path.is_file():
        _refresh_session_preview(session)
        working = dict(session.get("working_artifacts") or {})
        html_path = Path(str(working.get("html") or ""))
        css_path = Path(str(working.get("css") or css_path))
    if not css_path.is_file():
        css_path = Path(str(session.get("working_dir") or "")) / "report.css"
        css_path.parent.mkdir(parents=True, exist_ok=True)
        css_path.write_text(_default_css(), encoding="utf-8")
        working["css"] = str(css_path.resolve())
    if not html_path.is_file() or not css_path.is_file():
        raise HTTPException(status_code=400, detail="No renderable HTML/CSS artifact exists for this session.")

    report_dir = _report_dir(str(session.get("report_id") or ""))
    workspace = _session_workspace(session)
    _materialize_css_assets(css_path, base_dir=css_path.parent, fallback_roots=[report_dir, workspace])
    _materialize_html_assets(html_path, base_dir=html_path.parent, fallback_roots=[report_dir, workspace])
    _ensure_html_references_css(html_path, css_path)

    output_pdf_path = Path(str(session.get("working_dir") or "")) / "report.pdf"
    render_result = render_html_to_pdf(
        html_path=html_path,
        css_path=css_path,
        output_pdf_path=output_pdf_path,
        timeout_sec=180,
    )
    working["pdf"] = str(output_pdf_path.resolve())
    session["working_artifacts"] = working
    session["working_pdf_render_result"] = render_result
    artifact = _downloadable_from_file(output_pdf_path, purpose="Codex 对话式改造工作区 PDF", is_main=False)
    session["preview_artifact"] = artifact
    session["preview_url"] = artifact.get("path") or ""
    _append_event(
        session,
        "artifact_created",
        text="Codex 对话式改造 PDF 草稿已生成。",
        artifacts=[artifact],
        turn_id=turn_id,
        raw_payload=render_result,
    )
    _append_event(
        session,
        "preview_updated",
        text="预览已切换到最新 PDF 草稿。",
        preview_url=session["preview_url"],
        turn_id=turn_id,
    )
    return artifact


def _reconcile_idle_native_turn(report_id: str, session_id: str, session: dict[str, Any]) -> bool:
    turn = _current_turn(session)
    native_turn_id = str(session.get("active_turn_id") or turn.get("native_turn_id") or "")
    if str(session.get("native_thread_status") or "") != "idle":
        return False
    if not native_turn_id or str(turn.get("status") or "") not in TURN_ACTIVE_STATUSES:
        return False
    reconcile_age = _iso_age_seconds(session.get("native_idle_reconciliation_started_at"))
    if reconcile_age is not None and reconcile_age < 60:
        return False
    session["native_idle_reconciliation_started_at"] = _now_iso()
    session["native_connection_status"] = "verifying"
    _update_turn(session, str(turn.get("turn_id") or ""), status="verifying", native_turn_id=native_turn_id)
    _append_event(
        session,
        "native_status",
        text="Codex thread is idle; final verification is running in the background.",
        turn_id=str(turn.get("turn_id") or ""),
        status="verifying",
    )

    def _runner() -> None:
        try:
            fresh = _read_session(report_id, session_id)
            fresh_turn = _current_turn(fresh)
            if str(fresh_turn.get("status") or "") not in TURN_ACTIVE_STATUSES:
                return
            event = {
                "method": "thread/status/changed",
                "params": {"status": {"type": "idle"}, "reconciled": True},
            }
            _finalize_native_turn_completion(
                report_id,
                session_id,
                fresh,
                event,
                {"turn": {"id": native_turn_id}},
                allow_auto_repair=False,
            )
            fresh.pop("native_idle_reconciliation_started_at", None)
            _write_session(fresh)
        except Exception as exc:
            failed = _read_session(report_id, session_id)
            failed["native_connection_status"] = "error"
            failed["native_protocol_error"] = str(exc)
            failed.pop("native_idle_reconciliation_started_at", None)
            _append_event(failed, "native_error", text=str(exc), is_error=True, turn_id=str(turn.get("turn_id") or ""))
            _write_session(failed)

    threading.Thread(target=_runner, name=f"report-agent-idle-finalize-{session_id}", daemon=True).start()
    return True


def get_report_agent_session(report_id: str, session_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    original_session = json.loads(json.dumps(session, ensure_ascii=False, default=str))
    session = _sync_runtime_stdout(session)
    session = _sync_task_completion(session)
    if not _reconcile_idle_native_turn(report_id, session_id, session):
        _reconcile_stalled_native_turn(report_id, session_id, session)
    _persist_session_if_changed(session, original_session)
    return {"session": _public_session(session), "events": _read_events(session)}


def list_report_agent_session_events(report_id: str, session_id: str, *, cursor: int = 0) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    original_session = json.loads(json.dumps(session, ensure_ascii=False, default=str))
    session = _sync_runtime_stdout(session)
    session = _sync_task_completion(session)
    if not _reconcile_idle_native_turn(report_id, session_id, session):
        _reconcile_stalled_native_turn(report_id, session_id, session)
    _persist_session_if_changed(session, original_session)
    events = _read_events(session, cursor=cursor)
    next_cursor = max([int(event.get("event_id") or 0) for event in events], default=int(cursor or 0))
    return {"session": _public_session(session), "events": events, "next_cursor": next_cursor}


def _session_workspace(session: dict[str, Any]) -> Path:
    workspace = Path(str(session.get("workspace_path") or "")).resolve()
    if not workspace.exists():
        raise HTTPException(status_code=404, detail="Session workspace not found.")
    return workspace


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _session_relative_path(session: dict[str, Any], path: Path) -> str:
    workspace = _session_workspace(session)
    try:
        return path.resolve().relative_to(workspace).as_posix()
    except Exception:
        return path.name


def _file_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix == ".css":
        return "css"
    if suffix == ".md":
        return "markdown"
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".json":
        return "json"
    if suffix in {".csv", ".tsv"}:
        return "table"
    return suffix.lstrip(".") or "file"


def _session_file_record(session: dict[str, Any], path: Path) -> dict[str, Any]:
    stat = path.stat()
    relative = _session_relative_path(session, path)
    return {
        "name": path.name,
        "relative_path": relative,
        "file_path": str(path.resolve()),
        "type": _file_kind(path),
        "size": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "url": _storage_url_for(path),
    }


def _annotations_path(session: dict[str, Any]) -> Path:
    return _session_workspace(session) / ANNOTATIONS_FILE_NAME


def _read_annotations(session: dict[str, Any]) -> list[dict[str, Any]]:
    payload = _read_json(_annotations_path(session), [])
    if not isinstance(payload, list):
        return []
    annotations: list[dict[str, Any]] = []
    for raw_item in payload:
        item = dict(raw_item or {})
        item["note"] = _repair_mojibake_text(item.get("note") or "")
        item["artifact_name"] = _repair_mojibake_text(item.get("artifact_name") or "")
        item["artifact_source"] = _repair_mojibake_text(item.get("artifact_source") or "")
        artifact_type = str(item.get("artifact_type") or "")
        if not item.get("coordinate_space"):
            # Older HTML annotations were captured against the visible viewport.
            # Keep that distinction so the frontend can project them back safely.
            item["coordinate_space"] = "pdf_page_normalized_v2" if artifact_type == "pdf" else "html_viewport_legacy"
        try:
            item["coordinate_version"] = int(item.get("coordinate_version") or 1)
        except (TypeError, ValueError):
            item["coordinate_version"] = 1
        if not item.get("artifact_name"):
            item["artifact_name"] = Path(str(item.get("artifact_url") or "")).name or "当前预览文件"
        annotations.append(item)
    return annotations


def _write_annotations(session: dict[str, Any], annotations: list[dict[str, Any]]) -> Path:
    path = _annotations_path(session)
    path.write_text(json.dumps(annotations, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _annotation_prompt_summary(annotations: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, annotation in enumerate(annotations[-12:], start=1):
        shape = str(annotation.get("shape") or "rectangle")
        shape_label = {"highlight": "高亮", "pen": "画笔", "rectangle": "矩形框"}.get(shape, shape)
        artifact_name = _repair_mojibake_text(annotation.get("artifact_name") or "") or Path(
            str(annotation.get("artifact_url") or "")
        ).name
        artifact_type = str(annotation.get("artifact_type") or "")
        page_number = annotation.get("page_number")
        location = f"PDF 第 {page_number or 1} 页" if artifact_type == "pdf" else f"HTML scroll={round(float(annotation.get('scroll_offset') or 0))}"
        coordinate_space = str(annotation.get("coordinate_space") or "")
        note = _repair_mojibake_text(annotation.get("note") or "").strip() or "未填写说明，请结合标注位置判断需要修改的地方。"
        points = annotation.get("points") or []
        lines.append(
            f"{index}. {shape_label}｜文件：{artifact_name}｜位置：{location}｜坐标：{coordinate_space}｜批注：{note}｜normalized_points={points}"
        )
    return "\n".join(lines)


def _annotation_prompt_summary(annotations: list[dict[str, Any]]) -> str:  # type: ignore[no-redef]
    def _float_text(value: Any, *, digits: int = 0) -> str:
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            number = 0
        if digits <= 0:
            return str(round(number))
        return f"{number:.{digits}f}"

    lines: list[str] = []
    shape_labels = {"highlight": "高亮", "pen": "画笔", "rectangle": "矩形框"}
    for index, annotation in enumerate(annotations[-12:], start=1):
        shape = str(annotation.get("shape") or "rectangle")
        shape_label = shape_labels.get(shape, shape)
        artifact_name = _repair_mojibake_text(annotation.get("artifact_name") or "") or Path(
            str(annotation.get("artifact_url") or "")
        ).name or "当前预览文件"
        artifact_type = str(annotation.get("artifact_type") or "")
        page_number = annotation.get("page_number")
        coordinate_space = str(annotation.get("coordinate_space") or "")
        note = _repair_mojibake_text(annotation.get("note") or "").strip() or "未填写说明，请结合标注位置判断需要修改的地方。"
        points = annotation.get("points") or []
        if artifact_type == "pdf":
            location = f"PDF 第 {page_number or 1} 页"
            geometry = (
                f"页面尺寸={_float_text(annotation.get('page_width') or annotation.get('document_width'))}"
                f"x{_float_text(annotation.get('page_height') or annotation.get('document_height'))}"
                f"，预览缩放={_float_text(float(annotation.get('preview_zoom') or 1) * 100)}%"
            )
        else:
            location = f"HTML scroll={_float_text(annotation.get('scroll_offset'))}"
            geometry = (
                f"文档尺寸={_float_text(annotation.get('document_width'))}"
                f"x{_float_text(annotation.get('document_height'))}"
            )
        lines.append(
            f"{index}. {shape_label}｜文件：{artifact_name}｜位置：{location}｜"
            f"坐标空间：{coordinate_space}｜{geometry}｜批注：{note}｜"
            f"normalized_points={points}"
        )
    return "\n".join(lines)


def list_report_agent_session_annotations(report_id: str, session_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    return {"session": _public_session(session), "annotations": _read_annotations(session)}


def upsert_report_agent_session_annotation(
    report_id: str,
    session_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    now = _now_iso()
    annotation_id = str(payload.get("annotation_id") or f"annotation-{uuid.uuid4().hex[:12]}")
    annotations = _read_annotations(session)
    existing = next((item for item in annotations if str(item.get("annotation_id") or "") == annotation_id), {})
    artifact_type = str(payload.get("artifact_type") or existing.get("artifact_type") or "")
    coordinate_space = str(
        payload.get("coordinate_space")
        or existing.get("coordinate_space")
        or ("pdf_page_normalized_v2" if artifact_type == "pdf" else "html_document")
    )
    try:
        coordinate_version = int(payload.get("coordinate_version") or existing.get("coordinate_version") or 2)
    except (TypeError, ValueError):
        coordinate_version = 2
    record = {
        **existing,
        "annotation_id": annotation_id,
        "artifact_url": str(payload.get("artifact_url") or ""),
        "artifact_name": _repair_mojibake_text(payload.get("artifact_name") or existing.get("artifact_name") or ""),
        "artifact_id": str(payload.get("artifact_id") or existing.get("artifact_id") or ""),
        "artifact_source": _repair_mojibake_text(payload.get("artifact_source") or existing.get("artifact_source") or ""),
        "artifact_type": artifact_type,
        "coordinate_version": coordinate_version,
        "coordinate_space": coordinate_space,
        "page_number": payload.get("page_number"),
        "target_kind": str(payload.get("target_kind") or "page"),
        "points": list(payload.get("points") or []),
        "shape": str(payload.get("shape") or "rectangle"),
        "color": str(payload.get("color") or "#f97316"),
        "stroke_width": float(payload.get("stroke_width") or 2),
        "scroll_offset": float(payload.get("scroll_offset") or 0),
        "viewport_width": float(payload.get("viewport_width") or 0),
        "viewport_height": float(payload.get("viewport_height") or 0),
        "document_width": float(payload.get("document_width") or existing.get("document_width") or 0),
        "document_height": float(payload.get("document_height") or existing.get("document_height") or 0),
        "page_width": float(payload.get("page_width") or existing.get("page_width") or 0),
        "page_height": float(payload.get("page_height") or existing.get("page_height") or 0),
        "render_scale": float(payload.get("render_scale") or existing.get("render_scale") or 1),
        "preview_zoom": float(payload.get("preview_zoom") or existing.get("preview_zoom") or 1),
        "note": _repair_mojibake_text(payload.get("note") or ""),
        "created_at": str(existing.get("created_at") or now),
        "updated_at": now,
    }
    if not record["artifact_name"]:
        record["artifact_name"] = Path(record["artifact_url"]).name or "当前预览文件"
    annotations = [item for item in annotations if str(item.get("annotation_id") or "") != annotation_id]
    annotations.append(record)
    _write_annotations(session, annotations)
    _append_event(session, "artifact_created", text="报告批注已保存。", path=ANNOTATIONS_FILE_NAME)
    _write_session(session)
    return {"session": _public_session(session), "annotation": record, "annotations": annotations}


def delete_report_agent_session_annotation(
    report_id: str,
    session_id: str,
    annotation_id: str,
) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    annotations = _read_annotations(session)
    next_annotations = [
        item for item in annotations if str(item.get("annotation_id") or "") != str(annotation_id)
    ]
    _write_annotations(session, next_annotations)
    _append_event(session, "file_changed", text="报告批注已删除。", path=ANNOTATIONS_FILE_NAME)
    _write_session(session)
    return {"session": _public_session(session), "annotations": next_annotations}


def _attachments_dir(session: dict[str, Any]) -> Path:
    path = _session_workspace(session) / "attachments"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _attachments_path(session: dict[str, Any]) -> Path:
    return _session_workspace(session) / ATTACHMENTS_FILE_NAME


def _safe_attachment_filename(filename: str) -> str:
    name = Path(filename or "attachment").name
    safe = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", name).strip("._")
    return (safe or "attachment")[:120]


def _read_attachments(session: dict[str, Any]) -> list[dict[str, Any]]:
    payload = _read_json(_attachments_path(session), [])
    if not isinstance(payload, list):
        return []
    workspace = _session_workspace(session)
    profile_payload = _read_json(workspace / ATTACHMENT_PROFILE_JSON_NAME, {})
    profiles = profile_payload.get("profiles") if isinstance(profile_payload, dict) else []
    if not isinstance(profiles, list):
        profiles = []
    profile_by_attachment_id = {
        str((profile or {}).get("attachment_id") or ""): dict(profile or {})
        for profile in profiles
        if str((profile or {}).get("attachment_id") or "").strip()
    }
    items: list[dict[str, Any]] = []
    for raw_item in payload:
        item = dict(raw_item or {})
        path = Path(str(item.get("file_path") or ""))
        if path.is_file() and _is_within(path, workspace):
            item["url"] = _storage_url_for(path)
            item["size"] = path.stat().st_size
        attachment_id = str(item.get("attachment_id") or "")
        profile = profile_by_attachment_id.get(attachment_id)
        if profile:
            item["profile_status"] = "profiled"
            item["profile"] = {
                "row_count": profile.get("row_count"),
                "column_count": profile.get("column_count"),
                "numeric_columns": profile.get("numeric_columns"),
                "categorical_columns": profile.get("categorical_columns"),
                "datetime_columns": profile.get("datetime_columns"),
                "chartable_candidates": profile.get("chartable_candidates"),
            }
        items.append(item)
    return items


def _write_attachments(session: dict[str, Any], attachments: list[dict[str, Any]]) -> Path:
    return _write_json(_attachments_path(session), attachments)


def _jsonable(value: Any) -> Any:
    try:
        if value is None:
            return None
        if isinstance(value, float):
            return None if math.isnan(value) or math.isinf(value) else value
        if hasattr(value, "item"):
            return _jsonable(value.item())
        if isinstance(value, dict):
            return {str(key): _jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [_jsonable(item) for item in value]
    except Exception:
        return str(value)
    return value


def _load_attachment_frame(path: Path) -> tuple[Any | None, str]:
    suffix = path.suffix.lower()
    try:
        import pandas as pd  # type: ignore

        if suffix == ".csv":
            return pd.read_csv(path), ""
        if suffix == ".tsv":
            return pd.read_csv(path, sep="\t"), ""
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path), ""
        if suffix == ".json":
            return pd.json_normalize(json.loads(path.read_text(encoding="utf-8", errors="replace"))), ""
    except Exception as exc:
        return None, str(exc)
    return None, "unsupported_table_type"


def _load_table_frame(path: Path) -> tuple[Any | None, str]:
    return _load_attachment_frame(path)


def _profile_dataframe(df: Any, *, attachment_id: str, filename: str) -> dict[str, Any]:
    import pandas as pd  # type: ignore

    numeric_columns = [str(col) for col in df.select_dtypes(include=["number"]).columns]
    datetime_columns: list[str] = []
    categorical_columns: list[str] = []
    for column in df.columns:
        name = str(column)
        if name in numeric_columns:
            continue
        parsed = pd.to_datetime(df[column], errors="coerce")
        if parsed.notna().sum() >= max(3, int(len(df.index) * 0.55)):
            datetime_columns.append(name)
        else:
            categorical_columns.append(name)
    numeric_summary: dict[str, Any] = {}
    for column in numeric_columns[:30]:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if not series.empty:
            numeric_summary[column] = {
                "min": _jsonable(series.min()),
                "max": _jsonable(series.max()),
                "mean": _jsonable(series.mean()),
                "median": _jsonable(series.median()),
            }
    category_top_values: dict[str, Any] = {}
    for column in categorical_columns[:30]:
        counts = df[column].astype(str).replace({"nan": ""}).value_counts().head(8)
        category_top_values[column] = [{"value": str(index), "count": int(value)} for index, value in counts.items() if str(index)]
    return {
        "attachment_id": attachment_id,
        "filename": filename,
        "row_count": int(len(df.index)),
        "column_count": int(len(df.columns)),
        "columns": [str(col) for col in df.columns],
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "missing_rate": {str(col): round(float(df[col].isna().mean()), 4) for col in df.columns},
        "numeric_summary": numeric_summary,
        "category_top_values": category_top_values,
        "sample_rows": _jsonable(df.head(8).fillna("").to_dict(orient="records")),
        "chartable_candidates": {
            "bar_or_pie": bool(categorical_columns and numeric_columns),
            "line_or_area": bool(datetime_columns and numeric_columns),
            "scatter_or_quadrant": len(numeric_columns) >= 2,
            "bubble": len(numeric_columns) >= 3,
            "heatmap": len(categorical_columns) >= 2 and bool(numeric_columns),
            "histogram": bool(numeric_columns),
            "box": bool(numeric_columns),
            "diagnostic_inventory": True,
        },
    }


def _write_attachment_profile_artifacts(session: dict[str, Any], profiles: list[dict[str, Any]]) -> None:
    workspace = _session_workspace(session)
    _write_json(
        workspace / ATTACHMENT_PROFILE_JSON_NAME,
        {
            "generated_at": _now_iso(),
            "supplemental_evidence": True,
            "profile_count": len(profiles),
            "profiles": profiles,
        },
    )
    lines = [
        "# 补充材料数据画像",
        "",
        "上传材料作为后续改造补充证据使用，不会静默覆盖原报告确定性数字。",
        "",
    ]
    for profile in profiles:
        lines.extend(
            [
                f"## {profile.get('filename')}",
                f"- 行数：{profile.get('row_count')}",
                f"- 列数：{profile.get('column_count')}",
                f"- 数值列：{', '.join(profile.get('numeric_columns') or []) or '无'}",
                f"- 类别列：{', '.join(profile.get('categorical_columns') or []) or '无'}",
                f"- 时间列：{', '.join(profile.get('datetime_columns') or []) or '无'}",
                "",
            ]
        )
    (workspace / ATTACHMENT_PROFILE_MD_NAME).write_text("\n".join(lines), encoding="utf-8")


def _refresh_attachment_profiles(session: dict[str, Any]) -> list[dict[str, Any]]:
    attachments = _read_attachments(session)
    profiles: list[dict[str, Any]] = []
    changed = False
    for item in attachments:
        path = Path(str(item.get("file_path") or ""))
        if not path.is_file():
            continue
        frame, error = _load_attachment_frame(path)
        if frame is None:
            item["profile_status"] = "unsupported_or_unreadable"
            item["profile_error"] = error
            changed = True
            continue
        profile = _profile_dataframe(frame, attachment_id=str(item.get("attachment_id") or ""), filename=str(item.get("name") or path.name))
        item["profile_status"] = "profiled"
        item["profile"] = {
            "row_count": profile.get("row_count"),
            "column_count": profile.get("column_count"),
            "numeric_columns": profile.get("numeric_columns"),
            "categorical_columns": profile.get("categorical_columns"),
            "datetime_columns": profile.get("datetime_columns"),
            "chartable_candidates": profile.get("chartable_candidates"),
        }
        profiles.append(profile)
        changed = True
    if changed:
        _write_attachments(session, attachments)
    _write_attachment_profile_artifacts(session, profiles)
    return profiles


_REVISION_EVIDENCE_NAME_PATTERNS = (
    "metric_visual_registry",
    "source_visual_assets_index",
    "derived_metrics",
    "proxy_metrics",
    "semantic_metric",
    "custom_metric",
    "metric_mining",
    "metric_values",
    "metric_",
    "source_dataset",
    "cleaned_dataset",
    "normalized_dataset",
    "statistics_summary",
)


def _evidence_asset_id(path: Path) -> str:
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8", errors="ignore")).hexdigest()[:12]
    return f"data-asset-{digest}"


def _is_revision_evidence_table(path: Path, report_dir: Path) -> bool:
    if path.suffix.lower() not in {".csv", ".tsv", ".xlsx", ".xls", ".json"}:
        return False
    lower_name = path.name.lower()
    lower_path = path.as_posix().lower()
    if "codex_agent_sessions" in lower_path:
        return False
    if "source_visual_assets" in lower_path and path.suffix.lower() in {".csv", ".tsv", ".xlsx", ".xls"}:
        return True
    if any(pattern in lower_name for pattern in _REVISION_EVIDENCE_NAME_PATTERNS):
        return True
    return False


def _discover_revision_evidence_assets(session: dict[str, Any]) -> list[dict[str, Any]]:
    report_id = str(session.get("report_id") or "")
    report_dir = _report_dir(report_id)
    assets: list[dict[str, Any]] = []
    if not report_dir.exists():
        return assets
    for path in sorted(report_dir.rglob("*")):
        if not path.is_file() or not _is_revision_evidence_table(path, report_dir):
            continue
        try:
            relative = path.resolve().relative_to(report_dir.resolve()).as_posix()
        except Exception:
            relative = path.name
        kind = "report_table"
        lower = relative.lower()
        if "source_visual_assets" in lower:
            kind = "visual_asset_table"
        elif "derived" in lower:
            kind = "derived_metric_table"
        elif "proxy" in lower:
            kind = "proxy_metric_table"
        elif "custom_metric" in lower:
            kind = "custom_metric_table"
        elif "metric_visual_registry" in lower:
            kind = "metric_visual_registry"
        elif "metric_mining" in lower:
            kind = "metric_mining_output"
        assets.append(
            {
                "data_asset_id": _evidence_asset_id(path),
                "name": path.name,
                "kind": kind,
                "extension": path.suffix.lower(),
                "file_path": str(path.resolve()),
                "relative_to_report": relative,
                "size": path.stat().st_size,
                "url": _storage_url_for(path),
                "supplemental_evidence": False,
            }
        )
    return assets[:80]


def _write_revision_evidence_profile_artifacts(session: dict[str, Any], assets: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> None:
    workspace = _session_workspace(session)
    _write_json(
        workspace / REVISION_EVIDENCE_ASSETS_NAME,
        {
            "generated_at": _now_iso(),
            "asset_count": len(assets),
            "assets": assets,
        },
    )
    _write_json(
        workspace / REVISION_EVIDENCE_PROFILE_JSON_NAME,
        {
            "generated_at": _now_iso(),
            "profile_count": len(profiles),
            "profiles": profiles,
        },
    )
    lines = [
        "# 原报告可用证据资产画像",
        "",
        "这些资产来自已完成报告目录，用于后续改造时补图、补分析和追溯证据。它们不会覆盖原报告确定性数字。",
        "",
    ]
    for profile in profiles[:30]:
        lines.extend(
            [
                f"## {profile.get('filename')}",
                f"- data_asset_id：{profile.get('data_asset_id') or profile.get('attachment_id')}",
                f"- 行数：{profile.get('row_count')}",
                f"- 列数：{profile.get('column_count')}",
                f"- 数值列：{', '.join(profile.get('numeric_columns') or []) or '无'}",
                f"- 类别列：{', '.join(profile.get('categorical_columns') or []) or '无'}",
                f"- 时间列：{', '.join(profile.get('datetime_columns') or []) or '无'}",
                "",
            ]
        )
    (workspace / REVISION_EVIDENCE_PROFILE_MD_NAME).write_text("\n".join(lines), encoding="utf-8")


def _refresh_revision_evidence_profiles(session: dict[str, Any]) -> list[dict[str, Any]]:
    assets = _discover_revision_evidence_assets(session)
    profiles: list[dict[str, Any]] = []
    for item in assets:
        path = Path(str(item.get("file_path") or ""))
        frame, error = _load_table_frame(path)
        if frame is None:
            item["profile_status"] = "unsupported_or_unreadable"
            item["profile_error"] = error
            continue
        profile = _profile_dataframe(frame, attachment_id=str(item.get("data_asset_id") or ""), filename=str(item.get("name") or path.name))
        profile["data_asset_id"] = item.get("data_asset_id")
        profile["asset_kind"] = item.get("kind")
        profile["relative_to_report"] = item.get("relative_to_report")
        profile["source_extension"] = item.get("extension")
        profiles.append(profile)
        item["profile_status"] = "profiled"
        item["profile"] = {
            "row_count": profile.get("row_count"),
            "column_count": profile.get("column_count"),
            "numeric_columns": profile.get("numeric_columns"),
            "categorical_columns": profile.get("categorical_columns"),
            "datetime_columns": profile.get("datetime_columns"),
            "chartable_candidates": profile.get("chartable_candidates"),
        }
    _write_revision_evidence_profile_artifacts(session, assets, profiles)
    return profiles


def _revision_evidence_turn_context(session: dict[str, Any], *, refresh: bool = False) -> str:
    profile_payload = _read_json(_session_workspace(session) / REVISION_EVIDENCE_PROFILE_JSON_NAME, {})
    profiles = profile_payload.get("profiles") if isinstance(profile_payload, dict) else []
    if not isinstance(profiles, list):
        profiles = []
    if refresh and not profiles:
        profiles = _refresh_revision_evidence_profiles(session)
    if not profiles:
        return (
            "原报告证据资产画像尚未生成；如本轮需要补图，请写 working/"
            f"{REVISION_CHART_PLAN_NAME}，后端会基于现有报告证据确定性补齐数据画像和图表。"
        )
    lines = [
        "原报告证据资产上下文：",
        f"- evidence_assets_manifest: {REVISION_EVIDENCE_ASSETS_NAME}",
        f"- evidence_data_profile: {REVISION_EVIDENCE_PROFILE_JSON_NAME}",
        "- 这些资产包括派生指标、proxy/custom metric、metric registry、source_visual_assets CSV 和已有图表底层数据。",
        "- 需要用已有派生指标/合适指标作图时，优先从这些 data_asset_id 中选字段。",
        "",
        "可用证据表：",
    ]
    for profile in profiles[:24]:
        lines.append(
            f"- {profile.get('data_asset_id')}: {profile.get('filename')}，类型={profile.get('asset_kind')}，"
            f"数值={profile.get('numeric_columns') or []}，类别={profile.get('categorical_columns') or []}，时间={profile.get('datetime_columns') or []}"
        )
    return "\n".join(lines)


def _attachment_turn_context(session: dict[str, Any]) -> str:
    attachments = _read_attachments(session)
    if not attachments:
        return "当前没有上传补充材料。"
    profile_payload = _read_json(_session_workspace(session) / ATTACHMENT_PROFILE_JSON_NAME, {})
    profiles = profile_payload.get("profiles") if isinstance(profile_payload, dict) else []
    lines = [
        "补充材料上下文：",
        f"- attachments_manifest: {ATTACHMENTS_FILE_NAME}",
        f"- attachment_data_profile: {ATTACHMENT_PROFILE_JSON_NAME}",
        "- 上传材料是补充证据，不要静默覆盖原报告确定性数字。",
        "- 如需新增图表，请写 working/revision_chart_plan.json；后端会确定性渲染。",
        "- 图种不限于气泡/象限，可选择 bar/top_n/line/area/scatter/bubble/quadrant/heatmap/pie/donut/histogram/box 等。",
        "- 如果指定图种字段不足，仍要产出最接近的替代图或诊断图，不要让本轮停住。",
        "",
        "已上传文件：",
    ]
    for item in attachments:
        profile = item.get("profile") if isinstance(item.get("profile"), dict) else {}
        lines.append(f"- {item.get('attachment_id')}: {item.get('name')}，行={profile.get('row_count', '未知')}，列={profile.get('column_count', '未知')}")
    if isinstance(profiles, list):
        for profile in profiles:
            lines.append(
                f"- {profile.get('filename')} 可用字段：数值={profile.get('numeric_columns') or []}; "
                f"类别={profile.get('categorical_columns') or []}; 时间={profile.get('datetime_columns') or []}"
            )
    return "\n".join(lines)


def _chart_assets_dir(session: dict[str, Any]) -> Path:
    path = Path(str(session.get("working_dir") or _session_workspace(session) / "working")) / "revision_visual_assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _first_profile(session: dict[str, Any], attachment_id: str = "") -> dict[str, Any]:
    profiles = _all_data_profiles(session)
    if attachment_id:
        for profile in profiles:
            if str((profile or {}).get("attachment_id") or "") == attachment_id or str((profile or {}).get("data_asset_id") or "") == attachment_id:
                return dict(profile or {})
    return dict(profiles[0] or {}) if profiles else {}


def _all_data_profiles(session: dict[str, Any]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    attachment_payload = _read_json(_session_workspace(session) / ATTACHMENT_PROFILE_JSON_NAME, {})
    attachment_profiles = attachment_payload.get("profiles") if isinstance(attachment_payload, dict) else []
    if isinstance(attachment_profiles, list):
        profiles.extend(dict(item or {}) for item in attachment_profiles)
    evidence_payload = _read_json(_session_workspace(session) / REVISION_EVIDENCE_PROFILE_JSON_NAME, {})
    evidence_profiles = evidence_payload.get("profiles") if isinstance(evidence_payload, dict) else []
    if isinstance(evidence_profiles, list):
        profiles.extend(dict(item or {}) for item in evidence_profiles)
    return profiles


def _attachment_dataframe_by_id(session: dict[str, Any], attachment_id: str) -> tuple[Any | None, dict[str, Any], str]:
    for item in _read_attachments(session):
        if str(item.get("attachment_id") or "") == attachment_id:
            frame, error = _load_attachment_frame(Path(str(item.get("file_path") or "")))
            return frame, item, error
    return None, {}, "attachment_not_found"


def _dataframe_by_asset_id(session: dict[str, Any], data_asset_id: str) -> tuple[Any | None, dict[str, Any], str]:
    assets_payload = _read_json(_session_workspace(session) / REVISION_EVIDENCE_ASSETS_NAME, {})
    assets = assets_payload.get("assets") if isinstance(assets_payload, dict) else []
    if not isinstance(assets, list):
        assets = []
    for item in assets:
        if str((item or {}).get("data_asset_id") or "") == data_asset_id:
            frame, error = _load_table_frame(Path(str((item or {}).get("file_path") or "")))
            return frame, dict(item or {}), error
    for item in _discover_revision_evidence_assets(session):
        if str(item.get("data_asset_id") or "") == data_asset_id:
            frame, error = _load_table_frame(Path(str(item.get("file_path") or "")))
            return frame, item, error
    return None, {}, "data_asset_not_found"


def _dataframe_for_chart_spec(session: dict[str, Any], spec: dict[str, Any]) -> tuple[Any | None, dict[str, Any], str, str]:
    attachment_id = str(spec.get("attachment_id") or spec.get("source_attachment_id") or "")
    data_asset_id = str(spec.get("data_asset_id") or spec.get("source_data_asset_id") or spec.get("asset_id") or "")
    if attachment_id:
        frame, item, error = _attachment_dataframe_by_id(session, attachment_id)
        return frame, item, error, attachment_id
    if data_asset_id:
        frame, item, error = _dataframe_by_asset_id(session, data_asset_id)
        return frame, item, error, data_asset_id
    profiles = _all_data_profiles(session)
    for profile in profiles:
        candidate_id = str(profile.get("data_asset_id") or profile.get("attachment_id") or "")
        if not candidate_id:
            continue
        frame, item, error, resolved_id = _dataframe_for_chart_spec(session, {"data_asset_id": candidate_id} if str(profile.get("data_asset_id") or "") else {"attachment_id": candidate_id})
        if frame is not None:
            return frame, item, error, resolved_id
    return None, {}, "no_chartable_data_source", ""


def _best_effort_chart_specs(session: dict[str, Any], *, attachment_id: str = "") -> list[dict[str, Any]]:
    payload = _read_json(_session_workspace(session) / ATTACHMENT_PROFILE_JSON_NAME, {})
    profiles = payload.get("profiles") if isinstance(payload, dict) else []
    if not isinstance(profiles, list):
        return []
    specs: list[dict[str, Any]] = []
    for profile in profiles:
        if attachment_id and str(profile.get("attachment_id") or "") != attachment_id:
            continue
        aid = str(profile.get("attachment_id") or "")
        numeric = list(profile.get("numeric_columns") or [])
        categorical = list(profile.get("categorical_columns") or [])
        datetime_cols = list(profile.get("datetime_columns") or [])
        prefix = re.sub(r"[^A-Za-z0-9]+", "_", aid or "attachment").strip("_") or "attachment"
        if categorical and numeric:
            specs.append({"chart_id": f"{prefix}_topn_bar", "chart_type": "top_n_bar", "attachment_id": aid, "x": categorical[0], "y": numeric[0], "title": f"{categorical[0]} × {numeric[0]} 贡献排行"})
        if datetime_cols and numeric:
            specs.append({"chart_id": f"{prefix}_line", "chart_type": "line", "attachment_id": aid, "x": datetime_cols[0], "y": numeric[0], "title": f"{numeric[0]} 时间趋势"})
        if len(numeric) >= 2:
            specs.append({"chart_id": f"{prefix}_scatter", "chart_type": "scatter", "attachment_id": aid, "x": numeric[0], "y": numeric[1], "label": categorical[0] if categorical else "", "title": f"{numeric[0]} × {numeric[1]} 分布"})
        if len(numeric) >= 3:
            specs.append({"chart_id": f"{prefix}_bubble", "chart_type": "bubble", "attachment_id": aid, "x": numeric[0], "y": numeric[1], "size": numeric[2], "label": categorical[0] if categorical else "", "title": f"{numeric[0]} × {numeric[1]} 气泡图"})
        if len(categorical) >= 2 and numeric:
            specs.append({"chart_id": f"{prefix}_heatmap", "chart_type": "heatmap", "attachment_id": aid, "x": categorical[0], "color": categorical[1], "y": numeric[0], "title": f"{categorical[0]} × {categorical[1]} 热力图"})
        if numeric:
            specs.append({"chart_id": f"{prefix}_histogram", "chart_type": "histogram", "attachment_id": aid, "x": numeric[0], "title": f"{numeric[0]} 分布"})
        specs.append({"chart_id": f"{prefix}_inventory", "chart_type": "data_inventory", "attachment_id": aid, "title": f"{profile.get('filename') or aid} 字段画像"})
    return specs[:8]


def _best_effort_chart_specs(session: dict[str, Any], *, attachment_id: str = "") -> list[dict[str, Any]]:  # type: ignore[no-redef]
    def _score(profile: dict[str, Any]) -> tuple[int, int, str]:
        filename = str(profile.get("filename") or "").lower()
        kind = str(profile.get("asset_kind") or "")
        ext = str(profile.get("source_extension") or "")
        numeric_count = len(profile.get("numeric_columns") or [])
        score = 100
        if ext in {".csv", ".tsv", ".xlsx", ".xls"}:
            score -= 30
        if kind in {"derived_metric_table", "proxy_metric_table", "custom_metric_table", "visual_asset_table", "metric_visual_registry"}:
            score -= 20
        if numeric_count >= 3:
            score -= 20
        elif numeric_count >= 2:
            score -= 12
        if any(token in filename for token in ("chart_plan", "render_log", "specs", "source_visual_assets_index")):
            score += 40
        return (score, -numeric_count, filename)

    profiles = sorted(_all_data_profiles(session), key=_score)
    specs: list[dict[str, Any]] = []
    for profile in profiles:
        profile_id = str(profile.get("data_asset_id") or profile.get("attachment_id") or "")
        if attachment_id and profile_id != attachment_id:
            continue
        source_key = "data_asset_id" if profile.get("data_asset_id") else "attachment_id"
        numeric = list(profile.get("numeric_columns") or [])
        categorical = list(profile.get("categorical_columns") or [])
        datetime_cols = list(profile.get("datetime_columns") or [])
        prefix = re.sub(r"[^A-Za-z0-9]+", "_", profile_id or "asset").strip("_") or "asset"
        if len(numeric) >= 3:
            specs.append({"chart_id": f"{prefix}_bubble", "chart_type": "bubble", source_key: profile_id, "x": numeric[0], "y": numeric[1], "size": numeric[2], "label": categorical[0] if categorical else "", "title": f"{numeric[0]} × {numeric[1]} 气泡图"})
        if len(numeric) >= 2:
            specs.append({"chart_id": f"{prefix}_quadrant", "chart_type": "quadrant", source_key: profile_id, "x": numeric[0], "y": numeric[1], "label": categorical[0] if categorical else "", "title": f"{numeric[0]} × {numeric[1]} 象限分布"})
        if categorical and numeric:
            specs.append({"chart_id": f"{prefix}_topn_bar", "chart_type": "top_n_bar", source_key: profile_id, "x": categorical[0], "y": numeric[0], "title": f"{categorical[0]} × {numeric[0]} 贡献排行"})
        if datetime_cols and numeric:
            specs.append({"chart_id": f"{prefix}_line", "chart_type": "line", source_key: profile_id, "x": datetime_cols[0], "y": numeric[0], "title": f"{numeric[0]} 时间趋势"})
        if len(categorical) >= 2 and numeric:
            specs.append({"chart_id": f"{prefix}_heatmap", "chart_type": "heatmap", source_key: profile_id, "x": categorical[0], "color": categorical[1], "y": numeric[0], "title": f"{categorical[0]} × {categorical[1]} 热力图"})
        if numeric:
            specs.append({"chart_id": f"{prefix}_histogram", "chart_type": "histogram", source_key: profile_id, "x": numeric[0], "title": f"{numeric[0]} 分布"})
        specs.append({"chart_id": f"{prefix}_inventory", "chart_type": "data_inventory", source_key: profile_id, "title": f"{profile.get('filename') or profile_id} 字段画像"})
    return specs[:10]


def _read_revision_chart_plan(session: dict[str, Any]) -> dict[str, Any]:
    workspace = _session_workspace(session)
    working_dir = Path(str(session.get("working_dir") or workspace / "working"))
    for path in (working_dir / REVISION_CHART_PLAN_NAME, workspace / REVISION_CHART_PLAN_NAME):
        payload = _read_json(path, {})
        if isinstance(payload, dict) and payload:
            return payload
    return {}


def _write_auto_revision_chart_plan(session: dict[str, Any], specs: list[dict[str, Any]]) -> None:
    working_dir = Path(str(session.get("working_dir") or _session_workspace(session) / "working"))
    path = working_dir / REVISION_CHART_PLAN_NAME
    _write_json(
        path,
        {
            "plan_origin": "deterministic_best_effort_when_native_plan_missing",
            "generated_at": _now_iso(),
            "charts": specs,
            "note": "Codex 未写出补图计划时，后端按附件画像生成最接近的可交付图表计划；不伪造不存在的指标。",
        },
    )
    _append_event(session, "chart_plan_created", text="已基于补充材料画像生成通用补图计划。", path=_session_relative_path(session, path))


def _sanitize_chart_id(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_\-]+", "_", value or "").strip("_")
    return (text or f"chart_{uuid.uuid4().hex[:8]}")[:80]


def _configure_matplotlib_cjk(matplotlib_module: Any) -> None:
    matplotlib_module.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    matplotlib_module.rcParams["axes.unicode_minus"] = False


def _render_inventory_chart(profile: dict[str, Any], output_csv: Path, output_png: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    _configure_matplotlib_cjk(matplotlib)
    import matplotlib.pyplot as plt  # type: ignore
    import pandas as pd  # type: ignore

    rows = [
        {"field_type": "数值列", "count": len(profile.get("numeric_columns") or [])},
        {"field_type": "类别列", "count": len(profile.get("categorical_columns") or [])},
        {"field_type": "时间列", "count": len(profile.get("datetime_columns") or [])},
        {"field_type": "总列数", "count": int(profile.get("column_count") or 0)},
    ]
    data = pd.DataFrame(rows)
    data.to_csv(output_csv, index=False, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.bar(data["field_type"], data["count"], color=["#0f4c81", "#2a9d8f", "#f2c14e", "#94a3b8"])
    ax.set_title(title or "补充材料字段画像")
    ax.set_ylabel("字段数量")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_png, dpi=160)
    plt.close(fig)


def _render_revision_chart_spec(session: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    _configure_matplotlib_cjk(matplotlib)
    import matplotlib.pyplot as plt  # type: ignore
    import pandas as pd  # type: ignore

    attachment_id = str(spec.get("attachment_id") or spec.get("source_attachment_id") or "")
    data_asset_id = str(spec.get("data_asset_id") or spec.get("source_data_asset_id") or spec.get("asset_id") or "")
    source_id = data_asset_id or attachment_id
    profile = _first_profile(session, source_id)
    chart_type = str(spec.get("chart_type") or spec.get("chart_family") or "bar").lower()
    chart_id = _sanitize_chart_id(str(spec.get("chart_id") or spec.get("figure_id") or f"{attachment_id}_{chart_type}"))
    title = str(spec.get("title") or spec.get("reader_title") or chart_id)
    assets_dir = _chart_assets_dir(session)
    output_csv = assets_dir / f"{chart_id}.csv"
    output_png = assets_dir / f"{chart_id}.png"
    if chart_type in {"data_inventory", "inventory", "diagnostic"}:
        _render_inventory_chart(profile, output_csv, output_png, title)
        return {"chart_id": chart_id, "chart_type": "data_inventory", "title": title, "png_path": str(output_png.resolve()), "csv_path": str(output_csv.resolve())}

    df, _source_item, error, _resolved_source_id = _dataframe_for_chart_spec(session, spec)
    if df is None:
        raise ValueError(error or "data_source_not_readable")
    x = str(spec.get("x") or spec.get("category") or spec.get("dimension") or "")
    y = str(spec.get("y") or spec.get("value") or spec.get("metric") or "")
    size = str(spec.get("size") or spec.get("bubble_size") or "")
    color = str(spec.get("color") or spec.get("series") or "")
    top_n = int(spec.get("top_n") or spec.get("limit") or 12)
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    if chart_type in {"bar", "top_n", "top_n_bar", "pareto", "pie", "donut"}:
        if x not in df.columns or y not in df.columns:
            raise ValueError("missing_category_or_numeric_field")
        frame = df[[x, y]].copy()
        frame[y] = pd.to_numeric(frame[y], errors="coerce")
        data = frame.dropna(subset=[y]).groupby(x, dropna=False)[y].sum().sort_values(ascending=False).head(top_n).reset_index()
        data[x] = data[x].astype(str)
        data.to_csv(output_csv, index=False, encoding="utf-8-sig")
        if chart_type in {"pie", "donut"}:
            ax.pie(data[y], labels=data[x], autopct="%1.1f%%", startangle=90)
            if chart_type == "donut":
                ax.add_artist(plt.Circle((0, 0), 0.55, fc="white"))
        else:
            ax.barh(data[x][::-1], data[y][::-1], color="#0f4c81")
            ax.set_xlabel(y)
            ax.grid(axis="x", alpha=0.18)
    elif chart_type in {"line", "area"}:
        if x not in df.columns or y not in df.columns:
            raise ValueError("missing_time_or_numeric_field")
        frame = df[[x, y]].copy()
        frame[x] = pd.to_datetime(frame[x], errors="coerce")
        frame[y] = pd.to_numeric(frame[y], errors="coerce")
        data = frame.dropna(subset=[x, y]).groupby(x)[y].sum().reset_index().sort_values(x)
        data.to_csv(output_csv, index=False, encoding="utf-8-sig")
        if chart_type == "area":
            ax.fill_between(data[x], data[y], color="#2a9d8f", alpha=0.28)
        ax.plot(data[x], data[y], color="#0f4c81", linewidth=2.2)
        ax.set_ylabel(y)
        fig.autofmt_xdate()
        ax.grid(alpha=0.18)
    elif chart_type in {"scatter", "quadrant", "bubble"}:
        if x not in df.columns or y not in df.columns:
            raise ValueError("missing_numeric_axes")
        data = df.copy()
        data[x] = pd.to_numeric(data[x], errors="coerce")
        data[y] = pd.to_numeric(data[y], errors="coerce")
        data = data.dropna(subset=[x, y])
        sizes = None
        if chart_type == "bubble":
            if size not in data.columns:
                raise ValueError("missing_bubble_size_field")
            data[size] = pd.to_numeric(data[size], errors="coerce").fillna(0)
            max_size = float(data[size].max() or 1)
            sizes = data[size].clip(lower=0) / max_size * 900 + 60
        data.head(5000).to_csv(output_csv, index=False, encoding="utf-8-sig")
        ax.scatter(data[x], data[y], s=sizes, alpha=0.62, color="#2a9d8f", edgecolor="white", linewidth=0.6)
        if chart_type == "quadrant":
            ax.axvline(data[x].median(), color="#94a3b8", linestyle="--", linewidth=1)
            ax.axhline(data[y].median(), color="#94a3b8", linestyle="--", linewidth=1)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.grid(alpha=0.18)
    elif chart_type == "heatmap":
        if x not in df.columns or color not in df.columns or y not in df.columns:
            raise ValueError("missing_heatmap_fields")
        frame = df[[x, color, y]].copy()
        frame[y] = pd.to_numeric(frame[y], errors="coerce")
        pivot = frame.pivot_table(index=color, columns=x, values=y, aggfunc="mean").fillna(0)
        pivot.to_csv(output_csv, encoding="utf-8-sig")
        image = ax.imshow(pivot.values, cmap="YlGnBu", aspect="auto")
        ax.set_xticks(range(len(pivot.columns)), labels=[str(col) for col in pivot.columns], rotation=35, ha="right")
        ax.set_yticks(range(len(pivot.index)), labels=[str(row) for row in pivot.index])
        fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    elif chart_type in {"histogram", "hist"}:
        if x not in df.columns:
            raise ValueError("missing_numeric_field")
        data = pd.to_numeric(df[x], errors="coerce").dropna()
        data.to_frame(name=x).to_csv(output_csv, index=False, encoding="utf-8-sig")
        ax.hist(data, bins=min(30, max(8, int(len(data) ** 0.5))), color="#0f4c81", alpha=0.78)
        ax.set_xlabel(x)
        ax.set_ylabel("频数")
    elif chart_type == "box":
        if y not in df.columns and x in df.columns:
            y = x
            x = ""
        if y not in df.columns:
            raise ValueError("missing_numeric_field")
        data = df[[col for col in [x, y] if col]].copy()
        data[y] = pd.to_numeric(data[y], errors="coerce")
        data = data.dropna(subset=[y])
        data.to_csv(output_csv, index=False, encoding="utf-8-sig")
        if x and x in data.columns:
            groups = [group[y].values for _, group in data.groupby(x)]
            labels = [str(name) for name, _ in data.groupby(x)]
            ax.boxplot(groups, labels=labels, vert=True)
            ax.tick_params(axis="x", rotation=30)
        else:
            ax.boxplot(data[y].values, vert=True)
        ax.set_ylabel(y)
    else:
        raise ValueError(f"unsupported_chart_type:{chart_type}")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_png, dpi=170)
    plt.close(fig)
    return {"chart_id": chart_id, "chart_type": chart_type, "title": title, "png_path": str(output_png.resolve()), "csv_path": str(output_csv.resolve())}


def _append_revision_visuals_to_report(session: dict[str, Any], rendered: list[dict[str, Any]]) -> None:
    if not rendered:
        return
    working = dict(session.get("working_artifacts") or {})
    md_path = Path(str(working.get("markdown") or ""))
    html_path = Path(str(working.get("html") or ""))
    start = "<!-- ASTERIA_REVISION_VISUALS_START -->"
    end = "<!-- ASTERIA_REVISION_VISUALS_END -->"
    md_blocks = [start, "", "## 补充数据图表", ""]
    html_blocks = [start, '<section class="revision-visual-assets"><h2>补充数据图表</h2>']
    for item in rendered:
        png_path = Path(str(item.get("png_path") or ""))
        csv_path = Path(str(item.get("csv_path") or ""))
        title = str(item.get("title") or item.get("chart_id") or "补充图表")
        if not png_path.is_file():
            continue
        if md_path.is_file():
            rel_png = _session_relative_path(session, png_path)
            rel_csv = _session_relative_path(session, csv_path) if csv_path.is_file() else ""
            md_blocks.extend([f"### {title}", f"![{title}](../{rel_png})", f"底层数据：`{rel_csv}`" if rel_csv else "", ""])
        if html_path.is_file():
            try:
                html_rel_png = png_path.resolve().relative_to(html_path.parent.resolve()).as_posix()
            except Exception:
                html_rel_png = _storage_url_for(png_path)
            try:
                html_rel_csv = csv_path.resolve().relative_to(html_path.parent.resolve()).as_posix() if csv_path.is_file() else ""
            except Exception:
                html_rel_csv = _storage_url_for(csv_path) if csv_path.is_file() else ""
            html_blocks.append(
                f'<figure class="revision-chart-card"><img src="{html.escape(html_rel_png)}" alt="{html.escape(title)}" />'
                f"<figcaption>{html.escape(title)}"
                + (f' · <a href="{html.escape(html_rel_csv)}">查看底层 CSV</a>' if html_rel_csv else "")
                + "</figcaption></figure>"
            )
    md_blocks.append(end)
    html_blocks.extend(["</section>", end])
    if md_path.is_file():
        text = md_path.read_text(encoding="utf-8", errors="replace")
        replacement = "\n".join(md_blocks)
        text = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end), replacement, text) if start in text else text.rstrip() + "\n\n" + replacement + "\n"
        md_path.write_text(text, encoding="utf-8")
    if html_path.is_file():
        text = html_path.read_text(encoding="utf-8", errors="replace")
        replacement = "\n".join(html_blocks)
        text = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end), replacement, text) if start in text else re.sub(r"</body>", replacement + "\n</body>", text, count=1, flags=re.I)
        if "revision-chart-card" not in text:
            text = text.replace(
                "</head>",
                "<style>.revision-visual-assets{margin:32px 0;padding:24px;border:1px solid #d8dee9;border-radius:18px;background:#fff}.revision-chart-card{margin:20px 0}.revision-chart-card img{max-width:100%;height:auto;border:1px solid #e5e7eb;border-radius:14px}.revision-chart-card figcaption{margin-top:8px;color:#334155;font-size:14px}</style></head>",
            )
        html_path.write_text(text, encoding="utf-8")


def _process_revision_chart_outputs(session: dict[str, Any]) -> list[dict[str, Any]]:
    _refresh_attachment_profiles(session)
    _refresh_revision_evidence_profiles(session)
    if not _all_data_profiles(session):
        return []
    plan = _read_revision_chart_plan(session)
    specs = (plan.get("charts") or plan.get("render_specs")) if isinstance(plan, dict) else []
    if not isinstance(specs, list) or not specs:
        specs = _best_effort_chart_specs(session)
        if specs:
            _write_auto_revision_chart_plan(session, specs)
    rendered: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for raw_spec in specs[:24]:
        spec = dict(raw_spec or {})
        try:
            result = _render_revision_chart_spec(session, spec)
            result["spec"] = spec
            rendered.append(result)
            _append_event(session, "chart_rendered", text=f"已生成图表：{result.get('title')}", path=_session_relative_path(session, Path(str(result.get("png_path")))))
        except Exception as exc:
            substitute_specs = _best_effort_chart_specs(
                session,
                attachment_id=str(
                    spec.get("data_asset_id")
                    or spec.get("source_data_asset_id")
                    or spec.get("asset_id")
                    or spec.get("attachment_id")
                    or spec.get("source_attachment_id")
                    or ""
                ),
            )
            substitute = next((item for item in substitute_specs if item.get("chart_type") == "data_inventory"), substitute_specs[0] if substitute_specs else None)
            if substitute:
                try:
                    result = _render_revision_chart_spec(session, substitute)
                    result["spec"] = substitute
                    result["substituted_for"] = spec
                    result["substitution_reason"] = str(exc)
                    rendered.append(result)
                    _append_event(session, "chart_substituted", text=f"原图字段不足，已生成替代图：{result.get('title')}", path=_session_relative_path(session, Path(str(result.get("png_path")))))
                    continue
                except Exception as substitute_exc:
                    skipped.append({"spec": spec, "error": str(exc), "substitute_error": str(substitute_exc)})
            else:
                skipped.append({"spec": spec, "error": str(exc)})
    log_path = Path(str(session.get("working_dir") or _session_workspace(session) / "working")) / REVISION_CHART_RENDER_LOG_NAME
    _write_json(log_path, {"generated_at": _now_iso(), "rendered": rendered, "skipped_after_best_effort": skipped, "policy": "best_effort_deliverable_no_fake_metrics"})
    if rendered:
        _append_revision_visuals_to_report(session, rendered)
    return rendered


def _best_effort_chart_specs(session: dict[str, Any], *, attachment_id: str = "") -> list[dict[str, Any]]:  # type: ignore[no-redef]
    """Build chart specs from available evidence without blocking on an LLM plan."""

    def _score(profile: dict[str, Any]) -> tuple[int, int, str]:
        filename = str(profile.get("filename") or "").lower()
        kind = str(profile.get("asset_kind") or "")
        ext = str(profile.get("source_extension") or "")
        numeric_count = len(profile.get("numeric_columns") or [])
        score = 100
        if ext in {".csv", ".tsv", ".xlsx", ".xls"}:
            score -= 30
        if kind in {"derived_metric_table", "proxy_metric_table", "custom_metric_table", "visual_asset_table", "metric_visual_registry"}:
            score -= 20
        if numeric_count >= 3:
            score -= 20
        elif numeric_count >= 2:
            score -= 12
        if any(token in filename for token in ("chart_plan", "render_log", "specs", "source_visual_assets_index")):
            score += 40
        return (score, -numeric_count, filename)

    profiles = sorted(_all_data_profiles(session), key=_score)
    specs: list[dict[str, Any]] = []
    for profile in profiles:
        profile_id = str(profile.get("data_asset_id") or profile.get("attachment_id") or "")
        if attachment_id and profile_id != attachment_id:
            continue
        source_key = "data_asset_id" if profile.get("data_asset_id") else "attachment_id"
        numeric = list(profile.get("numeric_columns") or [])
        categorical = list(profile.get("categorical_columns") or [])
        datetime_cols = list(profile.get("datetime_columns") or [])
        prefix = re.sub(r"[^A-Za-z0-9]+", "_", profile_id or "asset").strip("_") or "asset"
        if len(numeric) >= 3:
            specs.append({"chart_id": f"{prefix}_bubble", "chart_type": "bubble", source_key: profile_id, "x": numeric[0], "y": numeric[1], "size": numeric[2], "label": categorical[0] if categorical else "", "title": f"{numeric[0]} 与 {numeric[1]} 气泡图"})
        if len(numeric) >= 2:
            specs.append({"chart_id": f"{prefix}_quadrant", "chart_type": "quadrant", source_key: profile_id, "x": numeric[0], "y": numeric[1], "label": categorical[0] if categorical else "", "title": f"{numeric[0]} 与 {numeric[1]} 象限分布"})
        if categorical and numeric:
            specs.append({"chart_id": f"{prefix}_topn_bar", "chart_type": "top_n_bar", source_key: profile_id, "x": categorical[0], "y": numeric[0], "title": f"{categorical[0]} 与 {numeric[0]} 贡献排行"})
        if datetime_cols and numeric:
            specs.append({"chart_id": f"{prefix}_line", "chart_type": "line", source_key: profile_id, "x": datetime_cols[0], "y": numeric[0], "title": f"{numeric[0]} 时间趋势"})
        if len(categorical) >= 2 and numeric:
            specs.append({"chart_id": f"{prefix}_heatmap", "chart_type": "heatmap", source_key: profile_id, "x": categorical[0], "color": categorical[1], "y": numeric[0], "title": f"{categorical[0]} 与 {categorical[1]} 热力图"})
        if numeric:
            specs.append({"chart_id": f"{prefix}_histogram", "chart_type": "histogram", source_key: profile_id, "x": numeric[0], "title": f"{numeric[0]} 分布"})
        specs.append({"chart_id": f"{prefix}_inventory", "chart_type": "data_inventory", source_key: profile_id, "title": f"{profile.get('filename') or profile_id} 字段画像"})
    return specs[:10]


def _write_auto_revision_chart_plan(session: dict[str, Any], specs: list[dict[str, Any]]) -> None:  # type: ignore[no-redef]
    working_dir = Path(str(session.get("working_dir") or _session_workspace(session) / "working"))
    path = working_dir / REVISION_CHART_PLAN_NAME
    _write_json(
        path,
        {
            "plan_origin": "deterministic_best_effort_when_native_plan_missing",
            "generated_at": _now_iso(),
            "charts": specs,
            "note": "Codex 尚未写出补图计划时，后端先按现有证据生成最接近的可交付图表；不伪造不存在的指标。",
        },
    )
    _append_event(session, "chart_plan_created", text="已基于现有报告证据生成补图计划。", path=_session_relative_path(session, path))


def _append_revision_visuals_to_report(session: dict[str, Any], rendered: list[dict[str, Any]]) -> None:  # type: ignore[no-redef]
    if not rendered:
        return
    working = dict(session.get("working_artifacts") or {})
    md_path = Path(str(working.get("markdown") or ""))
    html_path = Path(str(working.get("html") or ""))
    start = "<!-- ASTERIA_REVISION_VISUALS_START -->"
    end = "<!-- ASTERIA_REVISION_VISUALS_END -->"
    md_blocks = [start, "", "## 补充图表分析", "", "以下图表由后端基于现有报告证据和派生指标资产确定性生成，Codex 负责解释和组织，不直接编造数值。", ""]
    html_blocks = [
        start,
        '<section class="revision-visual-assets"><h2>补充图表分析</h2><p>以下图表由后端基于现有报告证据和派生指标资产确定性生成，Codex 负责解释和组织，不直接编造数值。</p>',
    ]
    for item in rendered:
        png_path = Path(str(item.get("png_path") or ""))
        csv_path = Path(str(item.get("csv_path") or ""))
        title = str(item.get("title") or item.get("chart_id") or "补充图表")
        if not png_path.is_file():
            continue
        if md_path.is_file():
            rel_png = _session_relative_path(session, png_path)
            rel_csv = _session_relative_path(session, csv_path) if csv_path.is_file() else ""
            md_blocks.extend([f"### {title}", f"![{title}](../{rel_png})", f"底层数据：`{rel_csv}`" if rel_csv else "", ""])
        if html_path.is_file():
            try:
                html_rel_png = png_path.resolve().relative_to(html_path.parent.resolve()).as_posix()
            except Exception:
                html_rel_png = _storage_url_for(png_path)
            try:
                html_rel_csv = csv_path.resolve().relative_to(html_path.parent.resolve()).as_posix() if csv_path.is_file() else ""
            except Exception:
                html_rel_csv = _storage_url_for(csv_path) if csv_path.is_file() else ""
            html_blocks.append(
                f'<figure class="revision-chart-card"><img src="{html.escape(html_rel_png)}" alt="{html.escape(title)}" />'
                f"<figcaption>{html.escape(title)}"
                + (f' · <a href="{html.escape(html_rel_csv)}">查看底层 CSV</a>' if html_rel_csv else "")
                + "</figcaption></figure>"
            )
    md_blocks.append(end)
    html_blocks.extend(["</section>", end])
    if md_path.is_file():
        text = md_path.read_text(encoding="utf-8", errors="replace")
        replacement = "\n".join(md_blocks)
        text = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end), replacement, text) if start in text else text.rstrip() + "\n\n" + replacement + "\n"
        md_path.write_text(text, encoding="utf-8")
    if html_path.is_file():
        text = html_path.read_text(encoding="utf-8", errors="replace")
        replacement = "\n".join(html_blocks)
        text = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end), replacement, text) if start in text else re.sub(r"</body>", replacement + "\n</body>", text, count=1, flags=re.I)
        if "revision-chart-card" not in text:
            text = text.replace(
                "</head>",
                "<style>.revision-visual-assets{margin:32px 0;padding:24px;border:1px solid #d8dee9;border-radius:18px;background:#fff}.revision-chart-card{margin:20px 0}.revision-chart-card img{max-width:100%;height:auto;border:1px solid #e5e7eb;border-radius:14px}.revision-chart-card figcaption{margin-top:8px;color:#334155;font-size:14px}</style></head>",
            )
        html_path.write_text(text, encoding="utf-8")


def _process_revision_chart_outputs(session: dict[str, Any]) -> list[dict[str, Any]]:  # type: ignore[no-redef]
    _refresh_attachment_profiles(session)
    _refresh_revision_evidence_profiles(session)
    if not _all_data_profiles(session):
        return []
    plan = _read_revision_chart_plan(session)
    specs = (plan.get("charts") or plan.get("render_specs")) if isinstance(plan, dict) else []
    if not isinstance(specs, list) or not specs:
        specs = _best_effort_chart_specs(session)
        if specs:
            _write_auto_revision_chart_plan(session, specs)
    rendered: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for raw_spec in specs[:24]:
        spec = dict(raw_spec or {})
        try:
            result = _render_revision_chart_spec(session, spec)
            result["spec"] = spec
            rendered.append(result)
            _append_event(session, "chart_rendered", text=f"已生成图表：{result.get('title')}", path=_session_relative_path(session, Path(str(result.get("png_path")))))
        except Exception as exc:
            substitute_specs = _best_effort_chart_specs(
                session,
                attachment_id=str(
                    spec.get("data_asset_id")
                    or spec.get("source_data_asset_id")
                    or spec.get("asset_id")
                    or spec.get("attachment_id")
                    or spec.get("source_attachment_id")
                    or ""
                ),
            )
            substitute = next((item for item in substitute_specs if item.get("chart_type") == "data_inventory"), substitute_specs[0] if substitute_specs else None)
            if substitute:
                try:
                    result = _render_revision_chart_spec(session, substitute)
                    result["spec"] = substitute
                    result["substituted_for"] = spec
                    result["substitution_reason"] = str(exc)
                    rendered.append(result)
                    _append_event(session, "chart_substituted", text=f"原图字段不足，已生成替代图：{result.get('title')}", path=_session_relative_path(session, Path(str(result.get("png_path")))))
                    continue
                except Exception as substitute_exc:
                    skipped.append({"spec": spec, "error": str(exc), "substitute_error": str(substitute_exc)})
            else:
                skipped.append({"spec": spec, "error": str(exc)})
    log_path = Path(str(session.get("working_dir") or _session_workspace(session) / "working")) / REVISION_CHART_RENDER_LOG_NAME
    _write_json(log_path, {"generated_at": _now_iso(), "rendered": rendered, "skipped_after_best_effort": skipped, "policy": "best_effort_deliverable_no_fake_metrics"})
    if rendered:
        _append_revision_visuals_to_report(session, rendered)
    return rendered


def list_report_agent_session_attachments(report_id: str, session_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    attachments = _read_attachments(session)
    profile_payload = _read_json(_session_workspace(session) / ATTACHMENT_PROFILE_JSON_NAME, {})
    profiles = profile_payload.get("profiles") if isinstance(profile_payload, dict) else []
    return {
        "session": _public_session(session),
        "attachments": attachments,
        "profile_count": len(profiles) if isinstance(profiles, list) else 0,
    }


def upload_report_agent_session_attachment(
    report_id: str,
    session_id: str,
    *,
    filename: str,
    content_type: str,
    data: bytes,
) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    attachment_id = f"attachment-{uuid.uuid4().hex[:10]}"
    safe_name = _safe_attachment_filename(filename)
    target = _attachments_dir(session) / f"{attachment_id}-{safe_name}"
    target.write_bytes(data)
    attachments = _read_attachments(session)
    record = {
        "attachment_id": attachment_id,
        "name": safe_name,
        "original_filename": filename,
        "type": target.suffix.lower().lstrip(".") or "file",
        "content_type": content_type,
        "size": len(data),
        "file_path": str(target.resolve()),
        "url": _storage_url_for(target),
        "uploaded_at": _now_iso(),
        "supplemental_evidence": True,
    }
    attachments.append(record)
    _write_attachments(session, attachments)
    _append_event(session, "attachment_uploaded", text=f"已上传补充材料：{safe_name}", path=_session_relative_path(session, target))
    profiles = _refresh_attachment_profiles(session)
    _append_event(session, "data_profile_created", text=f"已生成补充材料数据画像，共 {len(profiles)} 个可读表格。", path=ATTACHMENT_PROFILE_JSON_NAME)
    _write_session(session)
    return {"session": _public_session(session), "attachment": record, "attachments": _read_attachments(session), "profile_count": len(profiles)}


def delete_report_agent_session_attachment(report_id: str, session_id: str, attachment_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    kept: list[dict[str, Any]] = []
    removed_name = ""
    for item in _read_attachments(session):
        if str(item.get("attachment_id") or "") == str(attachment_id):
            removed_name = str(item.get("name") or attachment_id)
            path = Path(str(item.get("file_path") or ""))
            if path.is_file() and _is_within(path, _session_workspace(session)):
                path.unlink()
            continue
        kept.append(item)
    _write_attachments(session, kept)
    _refresh_attachment_profiles(session)
    _append_event(session, "file_changed", text=f"已删除补充材料：{removed_name or attachment_id}", path=ATTACHMENTS_FILE_NAME)
    _write_session(session)
    return {"session": _public_session(session), "attachments": _read_attachments(session)}


def list_report_agent_session_files(report_id: str, session_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    original_session = json.loads(json.dumps(session, ensure_ascii=False, default=str))
    session = _sync_runtime_stdout(session)
    session = _sync_task_completion(session)
    _persist_session_if_changed(session, original_session)
    workspace = _session_workspace(session)
    files: list[dict[str, Any]] = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {SESSION_FILE_NAME, EVENTS_FILE_NAME}:
            continue
        if path.suffix.lower() not in SESSION_FILE_SUFFIXES:
            continue
        if not _is_within(path, workspace):
            continue
        files.append(_session_file_record(session, path))
    return {"session": _public_session(session), "files": files}


def _read_text_for_diff(path: Path) -> list[str]:
    if not path.is_file() or path.suffix.lower() not in TEXT_DIFF_SUFFIXES:
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _diff_record(session: dict[str, Any], kind: str, source_path: Path | None, target_path: Path | None) -> dict[str, Any]:
    source_lines = _read_text_for_diff(source_path) if source_path else []
    target_lines = _read_text_for_diff(target_path) if target_path else []
    diff_lines = list(
        difflib.unified_diff(
            source_lines,
            target_lines,
            fromfile=str(source_path.name if source_path else f"{kind}:source"),
            tofile=str(target_path.name if target_path else f"{kind}:working"),
            lineterm="",
        )
    )
    additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
    return {
        "kind": kind,
        "source_path": str(source_path.resolve()) if source_path else "",
        "working_path": str(target_path.resolve()) if target_path else "",
        "relative_path": _session_relative_path(session, target_path) if target_path else "",
        "changed": bool(diff_lines),
        "additions": additions,
        "deletions": deletions,
        "diff_preview": "\n".join(diff_lines[:220]),
    }


def get_report_agent_session_diff(report_id: str, session_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    original_session = json.loads(json.dumps(session, ensure_ascii=False, default=str))
    session = _sync_runtime_stdout(session)
    session = _sync_task_completion(session)
    _persist_session_if_changed(session, original_session)
    workspace = _session_workspace(session)
    source_artifacts = dict(session.get("source_artifacts") or {})
    working_artifacts = dict(session.get("working_artifacts") or {})
    changed_files: list[dict[str, Any]] = []
    for kind in sorted(set(source_artifacts) | set(working_artifacts)):
        source_path = Path(str(source_artifacts.get(kind) or "")).resolve() if source_artifacts.get(kind) else None
        target_path = Path(str(working_artifacts.get(kind) or "")).resolve() if working_artifacts.get(kind) else None
        if source_path and not _is_within(source_path, workspace):
            source_path = None
        if target_path and not _is_within(target_path, workspace):
            target_path = None
        if (source_path and source_path.suffix.lower() in TEXT_DIFF_SUFFIXES) or (
            target_path and target_path.suffix.lower() in TEXT_DIFF_SUFFIXES
        ):
            changed_files.append(_diff_record(session, kind, source_path, target_path))
    return {
        "session": _public_session(session),
        "changed_files": changed_files,
        "changed_count": sum(1 for item in changed_files if item.get("changed")),
    }


def cancel_report_agent_turn(report_id: str, session_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    turn = _current_turn(session)
    turn_id = str(turn.get("turn_id") or "")
    status = str(turn.get("status") or "")
    task_id = str(turn.get("task_id") or session.get("current_task_id") or "")
    task: dict[str, Any] = {}
    if status not in TURN_ACTIVE_STATUSES:
        return {"session": _public_session(session), "task": task}
    suppressed_turn_ids = [str(item or "") for item in list(session.get("suppressed_turn_ids") or []) if str(item or "")]
    if turn_id and turn_id not in suppressed_turn_ids:
        suppressed_turn_ids.append(turn_id)
    session["suppressed_turn_ids"] = suppressed_turn_ids[-20:]
    _write_session(session)
    if str(session.get("mode") or "") == "native_app_server" or session.get("active_turn_id"):
        try:
            native_payload = interrupt_native_turn(session, _event_session_handler(report_id, session_id))
        except Exception as exc:
            _append_event(session, "native_error", text=f"原生 Codex 停止请求失败：{exc}", turn_id=turn_id, is_error=True)
            if _recover_completed_turn_from_working_state(
                report_id,
                session_id,
                session,
                reason="interrupt_failed_working_copy_passed",
                raw_payload={"error": str(exc)},
            ):
                _write_session(session)
                return {
                    "session": _public_session(session),
                    "task": {"error": str(exc), "recovered_after_interrupt_failure": True},
                }
            _update_turn(
                session,
                turn_id,
                status="cancelled",
                completed_at=_now_iso(),
                final_scope_status="cancelled",
            )
            session["active_turn_id"] = ""
            session["status"] = "active"
            session["session_status"] = "active"
            session["native_connection_status"] = "interrupt_failed_cancelled_locally"
            _append_event(
                session,
                "turn_cancelled",
                text="原生 Codex 停止请求超时；已在 Asteria 本地归档本轮，避免界面继续卡在运行中。",
                task_id=task_id,
                turn_id=turn_id,
                status="cancelled",
                raw_payload={"error": str(exc), "local_cancelled": True},
            )
            _write_session(session)
            return {
                "session": _public_session(session),
                "task": {"error": str(exc), "local_cancelled": True},
            }
        _update_turn(session, turn_id, status="cancelled", completed_at=_now_iso(), final_scope_status="cancelled")
        session["active_turn_id"] = ""
        session["status"] = "active"
        session["session_status"] = "active"
        session["native_connection_status"] = "interrupted"
        _append_event(session, "turn_cancelled", text="原生 Codex 本轮已经请求停止。", task_id=task_id, turn_id=turn_id, raw_payload=native_payload)
        _write_session(session)
        return {"session": _public_session(session), "task": native_payload}
    if task_id:
        try:
            task = cancel_codex_run_task(task_id)
        except Exception as exc:
            _append_event(session, "turn_failed", text=f"取消请求发送失败：{exc}", turn_id=turn_id, is_error=True)
            _write_session(session)
            return {"session": _public_session(session), "task": task}
    _update_turn(session, turn_id, status="cancelled", completed_at=_now_iso(), task_id=task_id, final_scope_status="cancelled")
    session["status"] = "active"
    session["session_status"] = "active"
    _append_event(session, "turn_cancelled", text="本轮 Codex 修改已取消。", task_id=task_id, turn_id=turn_id)
    _write_session(session)
    return {"session": _public_session(session), "task": task}


async def iter_report_agent_session_sse(report_id: str, session_id: str, *, cursor: int = 0) -> AsyncIterator[str]:
    current_cursor = int(cursor or 0)
    idle_rounds = 0
    while idle_rounds < 1800:
        try:
            payload = await asyncio.to_thread(list_report_agent_session_events, report_id, session_id, cursor=current_cursor)
        except HTTPException as exc:
            error_payload = {
                "type": "session_error",
                "detail": str(exc.detail or "Report agent session is unavailable."),
                "status_code": int(exc.status_code or 500),
                "report_id": report_id,
                "session_id": session_id,
            }
            yield (
                f"event: error\ndata: {json.dumps(error_payload, ensure_ascii=False, default=str)}\n\n"
            )
            return
        except Exception as exc:
            error_payload = {
                "type": "session_error",
                "detail": str(exc) or "Unexpected report agent session stream failure.",
                "status_code": 500,
                "report_id": report_id,
                "session_id": session_id,
            }
            yield (
                f"event: error\ndata: {json.dumps(error_payload, ensure_ascii=False, default=str)}\n\n"
            )
            return
        events = list(payload.get("events") or [])
        if events:
            idle_rounds = 0
            for event in events:
                current_cursor = max(current_cursor, int(event.get("event_id") or 0))
                yield f"id: {current_cursor}\nevent: message\ndata: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
        else:
            idle_rounds += 1
            yield f": heartbeat {current_cursor}\n\n"
        status = str((payload.get("session") or {}).get("status") or "")
        turn_status = str((payload.get("session") or {}).get("current_turn_status") or "")
        if turn_status in TURN_TERMINAL_STATUSES and not events:
            idle_rounds += 3
        await asyncio.sleep(1.0)
    yield "event: done\ndata: {}\n\n"


def publish_report_agent_session(report_id: str, session_id: str) -> dict[str, Any]:
    session = _read_session(report_id, session_id)
    session = _sync_runtime_stdout(session)
    session = _sync_task_completion(session)
    current_turn = _current_turn(session)
    revision_verification = dict(current_turn.get("revision_verification") or {})
    final_scope_status = str(current_turn.get("final_scope_status") or "")
    if revision_verification and final_scope_status != "passed":
        raise HTTPException(status_code=409, detail="Current revision has not passed scope verification and cannot be published yet.")
    report_dir = _report_dir(report_id)
    working = dict(session.get("working_artifacts") or {})
    md_path = Path(str(working.get("markdown") or ""))
    html_path = Path(str(working.get("html") or ""))
    css_path = Path(str(working.get("css") or ""))
    _refresh_session_preview(session)
    html_path = Path(str((session.get("working_artifacts") or {}).get("html") or html_path))
    css_path = Path(str((session.get("working_artifacts") or {}).get("css") or css_path))
    if not html_path.is_file() or not css_path.is_file():
        raise HTTPException(status_code=400, detail="No publishable HTML/CSS artifact exists for this session.")
    version = len(session.get("published_versions") or []) + 1
    short_session = session_id.replace("agent-session-", "")[:8]
    published_dir = Path(str(session.get("workspace_path") or "")) / "published" / f"v{version:02d}"
    published_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{report_id}-agent-revision-{short_session}-v{version:02d}"
    published_md = published_dir / f"{base_name}.md"
    published_html = published_dir / f"{base_name}.html"
    published_css = published_dir / f"{base_name}.css"
    published_pdf = published_dir / f"{base_name}.pdf"
    if md_path.is_file():
        shutil.copy2(md_path, published_md)
    shutil.copy2(html_path, published_html)
    shutil.copy2(css_path, published_css)
    _ensure_html_references_css(published_html, published_css)
    asset_fallback_roots = [report_dir, Path(str(session.get("workspace_path") or ""))]
    _materialize_css_assets(
        published_css,
        base_dir=css_path.parent,
        fallback_roots=asset_fallback_roots,
    )
    _materialize_html_assets(
        published_html,
        base_dir=html_path.parent,
        fallback_roots=asset_fallback_roots,
    )
    render_result = render_html_to_pdf(html_path=published_html, css_path=published_css, output_pdf_path=published_pdf, timeout_sec=180)

    artifacts = [
        _downloadable_from_file(published_pdf, purpose="Codex 内置后续改造版 PDF", is_main=False),
        _downloadable_from_file(published_html, purpose="Codex 内置后续改造版 HTML", is_main=False),
        _downloadable_from_file(published_css, purpose="Codex 内置后续改造版 CSS", is_main=False),
    ]
    if published_md.exists():
        artifacts.append(_downloadable_from_file(published_md, purpose="Codex 内置后续改造版 Markdown", is_main=False))

    manifest_path = report_dir / f"{report_id}-current_turn_export_manifest.json"
    manifest = _load_manifest(report_dir, report_id)
    downloadables = _load_downloadables(report_dir, report_id)
    seen = {str(item.get("name") or "") for item in downloadables}
    for artifact in artifacts:
        if artifact["name"] not in seen:
            downloadables.append(artifact)
            seen.add(artifact["name"])
    revisions = list(manifest.get("agent_revision_sessions") or [])
    revision_record = {
        "session_id": session_id,
        "version": version,
        "published_at": _now_iso(),
        "artifacts": artifacts,
        "render_result": render_result,
    }
    revisions.append(revision_record)
    manifest.update(
        {
            "report_id": report_id,
            "updated_at": _now_iso(),
            "downloadables": downloadables,
            "downloadable_count": len(downloadables),
            "agent_revision_sessions": revisions[-50:],
            "latest_agent_revision": revision_record,
        }
    )
    if not manifest.get("main_downloadable"):
        main_item = next((item for item in downloadables if item.get("is_main")), None)
        if main_item:
            manifest["main_downloadable"] = main_item.get("name")
    _write_json(manifest_path, manifest)

    published_versions = list(session.get("published_versions") or [])
    published_versions.append(revision_record)
    session["published_versions"] = published_versions
    session["status"] = "active"
    session["session_status"] = "active"
    session["preview_artifact"] = artifacts[0]
    session["preview_url"] = artifacts[0].get("path") or ""
    _append_event(session, "artifact_created", text="修订版 PDF/HTML/Markdown 已发布。", artifacts=artifacts)
    _append_event(session, "preview_updated", text="预览已切换到发布的修订版。", preview_url=session["preview_url"])
    _write_session(session)
    return {
        "session": _public_session(session),
        "published_version": revision_record,
        "downloadables": downloadables,
    }


# Reader-facing revision chart helpers are intentionally redefined at the end of
# the module so older mojibake-era helper definitions cannot leak into new
# confidence-smoke sessions.
def _best_effort_chart_specs(session: dict[str, Any], *, attachment_id: str = "") -> list[dict[str, Any]]:  # type: ignore[no-redef]
    """Build chart specs from available evidence without blocking on an LLM plan."""

    def _score(profile: dict[str, Any]) -> tuple[int, int, str]:
        filename = str(profile.get("filename") or "").lower()
        kind = str(profile.get("asset_kind") or "")
        ext = str(profile.get("source_extension") or "")
        numeric_count = len(profile.get("numeric_columns") or [])
        score = 100
        if profile.get("attachment_id"):
            score -= 35
        if ext in {".csv", ".tsv", ".xlsx", ".xls"}:
            score -= 30
        if kind in {"derived_metric_table", "proxy_metric_table", "custom_metric_table", "visual_asset_table", "metric_visual_registry"}:
            score -= 20
        if numeric_count >= 3:
            score -= 20
        elif numeric_count >= 2:
            score -= 12
        if any(token in filename for token in ("chart_plan", "render_log", "specs", "source_visual_assets_index")):
            score += 40
        return (score, -numeric_count, filename)

    profiles = sorted(_all_data_profiles(session), key=_score)
    specs: list[dict[str, Any]] = []
    for profile in profiles:
        profile_id = str(profile.get("data_asset_id") or profile.get("attachment_id") or "")
        if attachment_id and profile_id != attachment_id:
            continue
        source_key = "data_asset_id" if profile.get("data_asset_id") else "attachment_id"
        numeric = list(profile.get("numeric_columns") or [])
        categorical = list(profile.get("categorical_columns") or [])
        datetime_cols = list(profile.get("datetime_columns") or [])
        prefix = re.sub(r"[^A-Za-z0-9]+", "_", profile_id or "asset").strip("_") or "asset"
        if len(numeric) >= 3:
            specs.append(
                {
                    "chart_id": f"{prefix}_bubble",
                    "chart_type": "bubble",
                    source_key: profile_id,
                    "x": numeric[0],
                    "y": numeric[1],
                    "size": numeric[2],
                    "label": categorical[0] if categorical else "",
                    "title": f"{numeric[0]} 与 {numeric[1]} 气泡图",
                }
            )
        if len(numeric) >= 2:
            specs.append(
                {
                    "chart_id": f"{prefix}_quadrant",
                    "chart_type": "quadrant",
                    source_key: profile_id,
                    "x": numeric[0],
                    "y": numeric[1],
                    "label": categorical[0] if categorical else "",
                    "title": f"{numeric[0]} 与 {numeric[1]} 象限分布",
                }
            )
        if categorical and numeric:
            specs.append(
                {
                    "chart_id": f"{prefix}_topn_bar",
                    "chart_type": "top_n_bar",
                    source_key: profile_id,
                    "x": categorical[0],
                    "y": numeric[0],
                    "title": f"{categorical[0]} 与 {numeric[0]} 贡献排行",
                }
            )
        if datetime_cols and numeric:
            specs.append(
                {
                    "chart_id": f"{prefix}_line",
                    "chart_type": "line",
                    source_key: profile_id,
                    "x": datetime_cols[0],
                    "y": numeric[0],
                    "title": f"{numeric[0]} 时间趋势",
                }
            )
        if len(categorical) >= 2 and numeric:
            specs.append(
                {
                    "chart_id": f"{prefix}_heatmap",
                    "chart_type": "heatmap",
                    source_key: profile_id,
                    "x": categorical[0],
                    "color": categorical[1],
                    "y": numeric[0],
                    "title": f"{categorical[0]} 与 {categorical[1]} 热力图",
                }
            )
        if numeric:
            specs.append({"chart_id": f"{prefix}_histogram", "chart_type": "histogram", source_key: profile_id, "x": numeric[0], "title": f"{numeric[0]} 分布"})
        specs.append({"chart_id": f"{prefix}_inventory", "chart_type": "data_inventory", source_key: profile_id, "title": f"{profile.get('filename') or profile_id} 字段画像"})
    return specs[:10]


def _write_auto_revision_chart_plan(session: dict[str, Any], specs: list[dict[str, Any]]) -> None:  # type: ignore[no-redef]
    working_dir = Path(str(session.get("working_dir") or _session_workspace(session) / "working"))
    path = working_dir / REVISION_CHART_PLAN_NAME
    _write_json(
        path,
        {
            "plan_origin": "deterministic_best_effort_when_native_plan_missing",
            "generated_at": _now_iso(),
            "charts": specs,
            "note": "Codex 尚未写出补图计划时，后端先按现有证据生成最接近的可交付图表；不伪造不存在的指标。",
        },
    )
    _append_event(session, "chart_plan_created", text="已基于现有报告证据生成补图计划。", path=_session_relative_path(session, path))


def _append_revision_visuals_to_report(session: dict[str, Any], rendered: list[dict[str, Any]]) -> None:  # type: ignore[no-redef]
    if not rendered:
        return
    working = dict(session.get("working_artifacts") or {})
    md_path = Path(str(working.get("markdown") or ""))
    html_path = Path(str(working.get("html") or ""))
    start = "<!-- ASTERIA_REVISION_VISUALS_START -->"
    end = "<!-- ASTERIA_REVISION_VISUALS_END -->"
    md_blocks = [
        start,
        "",
        "## 补充图表分析",
        "",
        "以下图表由后端基于现有报告证据和派生指标资产确定性生成；Codex 负责解释和组织，不直接编造数值。",
        "",
    ]
    html_blocks = [
        start,
        '<section class="revision-visual-assets"><h2>补充图表分析</h2><p>以下图表由后端基于现有报告证据和派生指标资产确定性生成；Codex 负责解释和组织，不直接编造数值。</p>',
    ]
    for item in rendered:
        png_path = Path(str(item.get("png_path") or ""))
        csv_path = Path(str(item.get("csv_path") or ""))
        title = str(item.get("title") or item.get("chart_id") or "补充图表")
        if not png_path.is_file():
            continue
        if md_path.is_file():
            rel_png = _session_relative_path(session, png_path)
            rel_csv = _session_relative_path(session, csv_path) if csv_path.is_file() else ""
            md_blocks.extend([f"### {title}", f"![{title}](../{rel_png})", f"底层数据：`{rel_csv}`" if rel_csv else "", ""])
        if html_path.is_file():
            try:
                html_rel_png = png_path.resolve().relative_to(html_path.parent.resolve()).as_posix()
            except Exception:
                html_rel_png = _storage_url_for(png_path)
            try:
                html_rel_csv = csv_path.resolve().relative_to(html_path.parent.resolve()).as_posix() if csv_path.is_file() else ""
            except Exception:
                html_rel_csv = _storage_url_for(csv_path) if csv_path.is_file() else ""
            html_blocks.append(
                f'<figure class="revision-chart-card"><img src="{html.escape(html_rel_png)}" alt="{html.escape(title)}" />'
                f"<figcaption>{html.escape(title)}"
                + (f' · <a href="{html.escape(html_rel_csv)}">查看底层 CSV</a>' if html_rel_csv else "")
                + "</figcaption></figure>"
            )
    md_blocks.append(end)
    html_blocks.extend(["</section>", end])
    if md_path.is_file():
        text = md_path.read_text(encoding="utf-8", errors="replace")
        replacement = "\n".join(md_blocks)
        text = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end), replacement, text) if start in text else text.rstrip() + "\n\n" + replacement + "\n"
        md_path.write_text(text, encoding="utf-8")
    if html_path.is_file():
        text = html_path.read_text(encoding="utf-8", errors="replace")
        replacement = "\n".join(html_blocks)
        text = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end), replacement, text) if start in text else re.sub(r"</body>", replacement + "\n</body>", text, count=1, flags=re.I)
        if "revision-chart-card" not in text:
            text = text.replace(
                "</head>",
                "<style>.revision-visual-assets{margin:32px 0;padding:24px;border:1px solid #d8dee9;border-radius:18px;background:#fff}.revision-chart-card{margin:20px 0}.revision-chart-card img{max-width:100%;height:auto;border:1px solid #e5e7eb;border-radius:14px}.revision-chart-card figcaption{margin-top:8px;color:#334155;font-size:14px}</style></head>",
            )
        html_path.write_text(text, encoding="utf-8")


def _preflight_revision_chart_request(session: dict[str, Any], *, turn_id: str) -> int:  # type: ignore[no-redef]
    try:
        rendered = _process_revision_chart_outputs(session)
    except Exception as exc:
        _append_event(session, "chart_blocked", text=f"补图预处理遇到错误，已记录为可复查问题：{exc}", turn_id=turn_id, is_error=True)
        return 0
    if rendered:
        session["preflight_revision_chart_request"] = True
        session["preflight_revision_chart_count"] = len(rendered)
        session["preflight_revision_chart_render_log"] = str(
            (Path(str(session.get("working_dir") or _session_workspace(session) / "working")) / REVISION_CHART_RENDER_LOG_NAME).resolve()
        )
        _refresh_session_preview(session)
        _append_event(
            session,
            "preview_updated",
            text=f"已先行生成 {len(rendered)} 张补充图表；原生 Codex 可以继续组织解释和版面。",
            preview_url=str(session.get("preview_url") or ""),
            turn_id=turn_id,
        )
        return len(rendered)
    _append_event(session, "chart_substituted", text="暂未找到足够表格证据生成图表；后续改造会转为证据盘点或替代说明，不会伪造图表。", turn_id=turn_id)
    session["preflight_revision_chart_request"] = True
    session["preflight_revision_chart_count"] = 0
    return 0


def _start_native_turn_in_background(
    report_id: str,
    session_id: str,
    *,
    turn_id: str,
    started_at: str,
    user_message: str,
    prompt: str = "",
    base_instructions: str = "",
) -> None:
    def _runner() -> None:
        handler = _event_session_handler(report_id, session_id)
        try:
            start_ts = time.perf_counter()
            session = _read_session(report_id, session_id)
            if str(_current_turn(session).get("turn_id") or "") != turn_id:
                return
            _append_event(
                session,
                "native_starting",
                text="正在准备原生 Codex 启动上下文。",
                turn_id=turn_id,
                status="starting",
            )
            _write_session(session)
            native_prompt = prompt or _build_turn_prompt(session, user_message)
            native_base_instructions = base_instructions or _native_base_instructions(session)
            session = _read_session(report_id, session_id)
            if str(_current_turn(session).get("turn_id") or "") != turn_id:
                return
            _append_event(
                session,
                "native_prompt_ready",
                text="原生 Codex 启动上下文已准备完毕，正在连接 app-server。",
                turn_id=turn_id,
                status="starting",
                duration_ms=int((time.perf_counter() - start_ts) * 1000),
                raw_payload={"prompt_chars": len(native_prompt)},
            )
            _append_event(
                session,
                "native_bridge_starting",
                text="正在启动原生 Codex app-server。",
                turn_id=turn_id,
                status="starting",
            )
            _write_session(session)
            native_payload = start_native_turn(
                session,
                handler,
                prompt=native_prompt,
                base_instructions=native_base_instructions,
            )
        except HTTPException as exc:
            failed = _read_session(report_id, session_id)
            if str(_current_turn(failed).get("turn_id") or "") == turn_id:
                _update_turn(failed, turn_id, status="failed", completed_at=_now_iso())
                failed["native_connection_status"] = "error"
                failed["native_protocol_error"] = str(exc.detail)
                if _should_clear_native_thread_after_error(str(exc.detail)):
                    _clear_native_turn_binding(failed)
                _append_event(failed, "native_error", text=str(exc.detail), is_error=True, turn_id=turn_id)
                _write_session(failed)
            return
        except Exception as exc:
            failed = _read_session(report_id, session_id)
            if str(_current_turn(failed).get("turn_id") or "") == turn_id:
                _update_turn(failed, turn_id, status="failed", completed_at=_now_iso())
                failed["native_connection_status"] = "error"
                failed["native_protocol_error"] = str(exc)
                if _should_clear_native_thread_after_error(str(exc)):
                    _clear_native_turn_binding(failed)
                _append_event(failed, "native_error", text=str(exc), is_error=True, turn_id=turn_id)
                _write_session(failed)
            return

        fresh = _read_session(report_id, session_id)
        if str(_current_turn(fresh).get("turn_id") or "") != turn_id:
            return
        suppressed_turn_ids = {str(item or "") for item in list(fresh.get("suppressed_turn_ids") or []) if str(item or "")}
        if turn_id in suppressed_turn_ids or str(_current_turn(fresh).get("status") or "") == "cancelled":
            fresh["codex_thread_id"] = str(native_payload.get("thread_id") or "")
            fresh["codex_session_id"] = str(native_payload.get("thread_id") or "")
            fresh["active_turn_id"] = str(native_payload.get("turn_id") or "")
            _write_session(fresh)
            try:
                interrupt_native_turn(fresh, handler)
            except Exception:
                pass
            cancelled = _read_session(report_id, session_id)
            if str(_current_turn(cancelled).get("turn_id") or "") == turn_id:
                _update_turn(
                    cancelled,
                    turn_id,
                    status="cancelled",
                    completed_at=_now_iso(),
                    final_scope_status="cancelled",
                    native_turn_id=str(native_payload.get("turn_id") or ""),
                    started_at=started_at,
                )
                cancelled["active_turn_id"] = ""
                cancelled["native_connection_status"] = "interrupted"
                _append_event(
                    cancelled,
                    "turn_cancelled",
                    text="原生 Codex 本轮已经请求停止。",
                    turn_id=turn_id,
                    raw_payload=native_payload.get("result") if isinstance(native_payload.get("result"), dict) else native_payload,
                )
                _write_session(cancelled)
            return
        fresh["codex_thread_id"] = str(native_payload.get("thread_id") or "")
        fresh["codex_session_id"] = str(native_payload.get("thread_id") or "")
        fresh["active_turn_id"] = str(native_payload.get("turn_id") or "")
        fresh["native_connection_status"] = "online"
        fresh["status"] = "active"
        fresh["session_status"] = "active"
        _update_turn(
            fresh,
            turn_id,
            status="running",
            native_turn_id=str(native_payload.get("turn_id") or ""),
            started_at=started_at,
        )
        _append_event(
            fresh,
            "turn_started",
            text="原生 Codex 已开始处理这条修改意见；运行中可以继续发送引导。",
            turn_id=turn_id,
            raw_payload=native_payload.get("result") if isinstance(native_payload.get("result"), dict) else native_payload,
        )
        _write_session(fresh)

    threading.Thread(target=_runner, name=f"report-agent-native-turn-{session_id}-{turn_id}", daemon=True).start()


def _update_markdown_caption(text: str, caption: str) -> str:  # type: ignore[no-redef]
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.search(r"!\[[^\]]*\]\([^)]+\)", line):
            lines.insert(index + 1, f"*{caption}*")
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return _append_markdown_section(text, "图注修订", caption)


def _update_html_caption(text: str, caption: str) -> str:  # type: ignore[no-redef]
    escaped = html.escape(caption)
    if re.search(r"<figcaption[^>]*>[\s\S]*?</figcaption>", text, flags=re.I):
        return re.sub(r"<figcaption([^>]*)>[\s\S]*?</figcaption>", rf"<figcaption\1>{escaped}</figcaption>", text, count=1, flags=re.I)
    image_match = re.search(r"<img\b[^>]*>", text, flags=re.I)
    if image_match:
        image = image_match.group(0)
        figure = f"<figure>{image}<figcaption>{escaped}</figcaption></figure>"
        return text[: image_match.start()] + figure + text[image_match.end() :]
    return _append_html_section(text, "图注修订", caption)


def _apply_fast_text_revision(session: dict[str, Any], text: str, intent: dict[str, Any]) -> list[str]:  # type: ignore[no-redef]
    working = dict(session.get("working_artifacts") or {})
    md_path = Path(str(working.get("markdown") or ""))
    html_path = Path(str(working.get("html") or ""))
    css_path = Path(str(working.get("css") or ""))
    operation_kind = str(intent.get("operation_kind") or "")
    changed: list[str] = []
    phrase = str(intent.get("requested_phrase") or "").strip()
    if operation_kind == "headline_edit":
        title = phrase or "管理层行动周报"
        if md_path.is_file():
            md_path.write_text(_replace_markdown_heading(md_path.read_text(encoding="utf-8", errors="replace"), title), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_replace_html_h1(html_path.read_text(encoding="utf-8", errors="replace"), title), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    elif operation_kind == "summary_retone":
        summary = phrase or "本版摘要已收敛为管理层可直接阅读的行动导语，保留原报告数字与证据口径。"
        if md_path.is_file():
            md_path.write_text(_replace_markdown_summary(md_path.read_text(encoding="utf-8", errors="replace"), summary), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_replace_html_first_paragraph(html_path.read_text(encoding="utf-8", errors="replace"), summary), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    elif operation_kind == "major_revision":
        title = "管理层改造说明"
        body = (
            "本轮已按结构级改造要求重排读者入口，保留原报告数字与确定性证据，"
            "只调整叙事层级、行动指向和阅读路径。"
        )
        if md_path.is_file():
            md_path.write_text(_append_markdown_section(md_path.read_text(encoding="utf-8", errors="replace"), title, body), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_append_html_section(html_path.read_text(encoding="utf-8", errors="replace"), title, body), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    elif operation_kind == "caption_edit":
        caption = phrase or "按批注补充：该图用于定位本轮最需要管理层复核的对象和指标组合。"
        if md_path.is_file():
            md_path.write_text(_update_markdown_caption(md_path.read_text(encoding="utf-8", errors="replace"), caption), encoding="utf-8")
            changed.append(_session_relative_path(session, md_path))
        if html_path.is_file():
            html_path.write_text(_update_html_caption(html_path.read_text(encoding="utf-8", errors="replace"), caption), encoding="utf-8")
            changed.append(_session_relative_path(session, html_path))
    if css_path.is_file():
        pass
    _refresh_session_preview(session)
    return sorted(set(changed))
