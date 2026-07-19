from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_REPORT_ID = "zerovarfd29a607"
DEFAULT_OUTPUT = Path("workspace/report_revision_workbench_confidence_matrix_latest.json")

CHART_REQUEST = "\u62ff\u6d3e\u751f\u6307\u6807\u548c\u5408\u9002\u7684\u6307\u6807\u505a\u6c14\u6ce1\u8c61\u9650\u56fe"
ATTACHMENT_CHART_REQUEST = "\u57fa\u4e8e\u4e0a\u4f20\u8865\u5145\u6750\u6599\u3001\u6d3e\u751f\u6307\u6807\u548c\u5408\u9002\u6307\u6807\u505a\u6c14\u6ce1\u8c61\u9650\u56fe"
TEXT_ONLY_CHART_REQUEST = "\u8fd9\u4efd\u9644\u4ef6\u53ea\u6709\u6587\u672c\uff0c\u4e5f\u8bf7\u5c3d\u91cf\u751f\u6210\u6c14\u6ce1\u8c61\u9650\u56fe\uff0c\u4e0d\u884c\u5c31\u7ed9\u6700\u63a5\u8fd1\u7684\u8bca\u65ad\u56fe"
HEADLINE_REQUEST = "\u53ea\u6539\u4e3b\u6807\u9898\u4e3a\u201c\u7ba1\u7406\u5c42\u884c\u52a8\u5468\u62a5\u201d\uff0c\u4e0d\u6539\u6570\u5b57\uff0c\u4e0d\u6539\u6b63\u6587\u3002"
SUMMARY_REQUEST = "\u53ea\u6539\u6458\u8981\u8bed\u6c14\u4e3a\u201c\u4e09\u6761\u884c\u52a8\u9879\u4f18\u5148\u201d\uff0c\u4e0d\u6539\u6807\u9898\uff0c\u4e0d\u6539\u6570\u5b57\u3002"
MAJOR_REQUEST = "\u5bf9\u8fd9\u4efd\u62a5\u544a\u505a\u7ed3\u6784\u7ea7\u5927\u6539\uff0c\u4f46\u4e0d\u6539\u4efb\u4f55\u6570\u5b57\u3002"
NUMERIC_BLOCK_REQUEST = "\u628a ROI \u6539\u6210 4.2\uff0c\u4e0d\u8981\u89e3\u91ca\u3002"
CAPTION_REQUEST = "\u6309\u6279\u6ce8\u6539\u56fe\u6ce8\uff0c\u4e0d\u8981\u6269\u6563\u6539\u5168\u6587\uff0c\u4e0d\u6539\u6570\u5b57\u3002"
GUIDANCE_START_REQUEST = "\u8bf7\u4f7f\u7528\u539f\u751f Codex \u68c0\u67e5\u8fd9\u4efd\u62a5\u544a\u7684\u4fee\u6539\u8def\u5f84\uff0c\u5148\u4e0d\u8981\u53d1\u5e03\uff0c\u8fd0\u884c\u4e2d\u7b49\u6211\u8ffd\u52a0\u5f15\u5bfc\u3002"
GUIDANCE_INJECTION = "\u8ffd\u52a0\u5f15\u5bfc\uff1a\u4f18\u5148\u56f4\u7ed5\u56fe\u8868\u6bb5\u843d\uff0c\u4e0d\u6539\u6570\u5b57\u3002"

MOJIBAKE_MARKERS = ("�", "锟", "Ã", "Â", "鑴", "鐠", "閻", "閸", "閺", "閿", "宸插", "鍥", "琛")
TERMINAL_STATUSES = {
    "completed",
    "failed",
    "failed_scope_miss",
    "failed_scope_violation",
    "failed_partial_application",
    "cancelled",
    "blocked",
}


class SmokeFailure(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _request_json(
    method: str,
    url: str,
    *,
    payload: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 240,
) -> Any:
    data = None
    req_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json; charset=utf-8")
    request = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SmokeFailure(f"{method} {url} failed: HTTP {exc.code}: {body[:1600]}") from exc
    except Exception as exc:
        raise SmokeFailure(f"{method} {url} failed: {exc}") from exc
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _multipart_upload(url: str, *, field_name: str, file_path: Path, report_id: str) -> Any:
    boundary = f"----asteria-smoke-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    body.extend(file_path.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        f"{url}?report_id={urllib.parse.quote(report_id)}",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise SmokeFailure(f"attachment upload failed: HTTP {exc.code}: {body_text[:1600]}") from exc


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def _has_mojibake(text: str) -> bool:
    return any(marker in text for marker in MOJIBAKE_MARKERS)


def _assert_no_mojibake(label: str, payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, default=str) if not isinstance(payload, str) else payload
    _assert(not _has_mojibake(text), f"{label} contains mojibake markers")


def _session(base_url: str, report_id: str, session_id: str) -> dict[str, Any]:
    return _request_json("GET", f"{base_url}/api/reports/{report_id}/agent-sessions/{session_id}")["session"]


def _workspace(session: dict[str, Any]) -> Path:
    path = Path(str(session.get("workspace_path") or ""))
    _assert(path.is_dir(), f"session workspace missing: {path}")
    return path


def _working_text(session: dict[str, Any], name: str) -> str:
    path = _workspace(session) / "working" / name
    _assert(path.is_file(), f"missing working file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def _create_session(base_url: str, report_id: str, title: str) -> str:
    payload = _request_json("POST", f"{base_url}/api/reports/{report_id}/agent-sessions", payload={"title": title})
    session_id = str((payload.get("session") or {}).get("session_id") or "")
    _assert(bool(session_id), f"session id missing in create response: {payload}")
    return session_id


def _send_message(base_url: str, report_id: str, session_id: str, message: str) -> dict[str, Any]:
    return _request_json(
        "POST",
        f"{base_url}/api/report-agent-sessions/{session_id}/messages?report_id={urllib.parse.quote(report_id)}",
        payload={"message": message},
    )


def _events(base_url: str, report_id: str, session_id: str) -> list[dict[str, Any]]:
    payload = _request_json("GET", f"{base_url}/api/report-agent-sessions/{session_id}/events?report_id={urllib.parse.quote(report_id)}&cursor=0")
    return list(payload.get("events") or [])


def _publish(base_url: str, report_id: str, session_id: str) -> dict[str, Any]:
    payload = _request_json("POST", f"{base_url}/api/report-agent-sessions/{session_id}/publish?report_id={urllib.parse.quote(report_id)}", payload={})
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    versions = list(session.get("published_versions") or [])
    _assert(versions, "publish did not add a published version")
    latest = versions[-1]
    artifacts = list(latest.get("artifacts") or [])
    artifact_types = {str(item.get("type") or "") for item in artifacts}
    _assert({"pdf", "html", "md"}.issubset(artifact_types), f"published artifacts missing pdf/html/md: {artifact_types}")
    for item in artifacts:
        file_path = item.get("file_path")
        if file_path:
            _assert(Path(str(file_path)).is_file(), f"published artifact file missing: {file_path}")
    return {"version": latest.get("version"), "published_at": latest.get("published_at"), "artifacts": artifacts}


def _check_event_schema(events: list[dict[str, Any]]) -> None:
    _assert(events, "session has no events")
    for event in events:
        for key in ("event_id", "kind", "role", "display_kind", "timestamp"):
            _assert(key in event and event.get(key) not in (None, ""), f"event missing {key}: {event}")


def _wait_terminal(base_url: str, report_id: str, session_id: str, *, timeout_sec: int = 180) -> dict[str, Any]:
    deadline = time.time() + timeout_sec
    last_session: dict[str, Any] = {}
    while time.time() < deadline:
        last_session = _session(base_url, report_id, session_id)
        status = str(last_session.get("current_turn_status") or "")
        if status in TERMINAL_STATUSES:
            return last_session
        time.sleep(1.5)
    raise SmokeFailure(f"turn did not reach terminal status within {timeout_sec}s; last={last_session.get('current_turn_status')}")


def _check_revision_outputs(session: dict[str, Any], *, expect_completed: bool = True, require_bubble: bool = True) -> dict[str, Any]:
    workspace = _workspace(session)
    working = workspace / "working"
    assets = working / "revision_visual_assets"
    plan_path = working / "revision_chart_plan.json"
    log_path = working / "revision_chart_render_log.json"
    _assert(plan_path.is_file(), f"missing revision chart plan: {plan_path}")
    _assert(log_path.is_file(), f"missing revision chart render log: {log_path}")
    _assert(assets.is_dir(), f"missing revision visual assets dir: {assets}")
    log = json.loads(log_path.read_text(encoding="utf-8"))
    rendered = list(log.get("rendered") or [])
    pngs = sorted(assets.glob("*.png"))
    csvs = sorted(assets.glob("*.csv"))
    titles = [str(item.get("title") or "") for item in rendered]
    _assert(len(rendered) >= 1, "render log has no rendered charts")
    _assert(len(pngs) >= 1, "no rendered PNG chart assets")
    _assert(len(csvs) >= 1, "no rendered CSV chart assets")
    if require_bubble:
        _assert(any(item.get("chart_type") == "bubble" for item in rendered), "bubble chart was not generated")
        _assert(any(item.get("chart_type") == "quadrant" for item in rendered), "quadrant chart was not generated")
    for item in rendered:
        if item.get("png_path"):
            _assert(Path(str(item["png_path"])).is_file(), f"rendered PNG missing: {item['png_path']}")
        if item.get("csv_path"):
            _assert(Path(str(item["csv_path"])).is_file(), f"rendered CSV missing: {item['csv_path']}")
    md = _working_text(session, "report.md")
    html = _working_text(session, "report.html")
    _assert("\u8865\u5145\u56fe\u8868\u5206\u6790" in md, "Markdown report does not include supplemental chart section")
    _assert("\u8865\u5145\u56fe\u8868\u5206\u6790" in html, "HTML report does not include supplemental chart section")
    _assert("ASTERIA_REVISION_VISUALS_START" in md, "Markdown chart marker missing")
    _assert("ASTERIA_REVISION_VISUALS_START" in html, "HTML chart marker missing")
    _assert_no_mojibake("chart titles", titles)
    if expect_completed:
        _assert(session.get("current_turn_status") == "completed", f"turn did not complete: {session.get('current_turn_status')}")
        _assert((session.get("current_turn") or {}).get("final_scope_status") == "passed", "turn final scope did not pass")
    return {
        "workspace": str(workspace),
        "plan_path": str(plan_path),
        "render_log_path": str(log_path),
        "rendered_count": len(rendered),
        "png_count": len(pngs),
        "csv_count": len(csvs),
        "chart_types": sorted({str(item.get("chart_type") or "") for item in rendered}),
        "titles": titles[:10],
    }


def _current_verification(session: dict[str, Any]) -> dict[str, Any]:
    turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
    verification = turn.get("revision_verification") if isinstance(turn.get("revision_verification"), dict) else {}
    return dict(verification or {})


def _assert_passed_without_number_change(session: dict[str, Any]) -> dict[str, Any]:
    verification = _current_verification(session)
    _assert(verification.get("passed") is True, f"verification did not pass: {verification}")
    _assert(not verification.get("numeric_changes_detected"), f"numeric changes detected: {verification}")
    _assert((session.get("current_turn") or {}).get("final_scope_status") == "passed", "final scope status is not passed")
    return verification


def _upload_csv(base_url: str, report_id: str, session_id: str, filename: str, content: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="asteria-revision-smoke-") as tmp:
        csv_path = Path(tmp) / filename
        csv_path.write_text(content, encoding="utf-8")
        return _multipart_upload(
            f"{base_url}/api/report-agent-sessions/{session_id}/attachments",
            field_name="file",
            file_path=csv_path,
            report_id=report_id,
        )


def _post_annotation(base_url: str, report_id: str, session_id: str) -> dict[str, Any]:
    session = _session(base_url, report_id, session_id)
    artifact_url = str(session.get("preview_url") or "")
    payload = {
        "annotation_id": f"smoke-{uuid.uuid4().hex[:8]}",
        "artifact_url": artifact_url or f"/storage/reports/smart-report-{report_id}/{report_id}.html",
        "artifact_name": "smoke-preview.html",
        "artifact_type": "html",
        "target_kind": "html",
        "coordinate_space": "html_document_normalized_v1",
        "points": [{"x": 0.12, "y": 0.18}, {"x": 0.44, "y": 0.18}, {"x": 0.44, "y": 0.31}, {"x": 0.12, "y": 0.31}],
        "shape": "rectangle",
        "color": "#f97316",
        "stroke_width": 2,
        "note": "\u8bf7\u628a\u8fd9\u4e2a\u533a\u57df\u5bf9\u5e94\u7684\u56fe\u6ce8\u6539\u5f97\u66f4\u50cf\u7ba1\u7406\u5c42\u590d\u6838\u63d0\u793a\u3002",
    }
    return _request_json("POST", f"{base_url}/api/report-agent-sessions/{session_id}/annotations?report_id={urllib.parse.quote(report_id)}", payload=payload)


def _run_chart_fast_path(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 chart fast path")
    response = _send_message(base_url, report_id, session_id, CHART_REQUEST)
    session = _session(base_url, report_id, session_id)
    output = _check_revision_outputs(session, expect_completed=True)
    _assert((response.get("native") or {}).get("mode") == "deterministic_chart_fast_path", "chart request did not use deterministic fast path")
    events = _events(base_url, report_id, session_id)
    _check_event_schema(events)
    kinds = [str(item.get("kind") or "") for item in events]
    for expected in ("chart_plan_created", "chart_rendered", "preview_updated", "turn_completed"):
        _assert(expected in kinds, f"missing event kind: {expected}; got {kinds}")
    publish = _publish(base_url, report_id, session_id)
    return {"session_id": session_id, "outputs": output, "event_count": len(events), "publish": publish}


def _run_attachment_chart_path(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 attachment chart")
    upload = _upload_csv(
        base_url,
        report_id,
        session_id,
        "supplemental_bubble_metrics.csv",
        "object,x_metric,y_metric,size_metric,segment\nA,12,30,100,core\nB,25,12,80,growth\nC,8,10,30,risk\nD,30,42,160,core\n",
    )
    _assert(upload.get("attachments"), "attachment upload did not register attachment")
    _send_message(base_url, report_id, session_id, ATTACHMENT_CHART_REQUEST)
    session = _session(base_url, report_id, session_id)
    output = _check_revision_outputs(session, expect_completed=True)
    events = _events(base_url, report_id, session_id)
    _check_event_schema(events)
    kinds = [str(item.get("kind") or "") for item in events]
    _assert("attachment_uploaded" in kinds, "missing attachment_uploaded event")
    _assert("data_profile_created" in kinds, "missing data_profile_created event")
    publish = _publish(base_url, report_id, session_id)
    return {"session_id": session_id, "attachment_count": len(upload.get("attachments") or []), "outputs": output, "event_count": len(events), "publish": publish}


def _run_text_only_attachment_path(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 text only attachment")
    upload = _upload_csv(
        base_url,
        report_id,
        session_id,
        "text_only_notes.csv",
        "object,note,segment\nA,needs follow up,alpha\nB,strong qualitative signal,beta\nC,missing metrics,gamma\n",
    )
    _assert(upload.get("attachments"), "text-only attachment upload did not register attachment")
    _send_message(base_url, report_id, session_id, TEXT_ONLY_CHART_REQUEST)
    session = _session(base_url, report_id, session_id)
    output = _check_revision_outputs(session, expect_completed=True, require_bubble=False)
    publish = _publish(base_url, report_id, session_id)
    return {"session_id": session_id, "outputs": output, "publish": publish}


def _run_strict_headline_edit(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 strict headline")
    _send_message(base_url, report_id, session_id, HEADLINE_REQUEST)
    session = _session(base_url, report_id, session_id)
    verification = _assert_passed_without_number_change(session)
    md = _working_text(session, "report.md")
    html = _working_text(session, "report.html")
    _assert("\u7ba1\u7406\u5c42\u884c\u52a8\u5468\u62a5" in md, "markdown title did not update")
    _assert("\u7ba1\u7406\u5c42\u884c\u52a8\u5468\u62a5" in html, "html title did not update")
    _assert("body_copy" not in verification.get("changed_targets", []), f"headline edit changed body: {verification}")
    return {"session_id": session_id, "verification": verification}


def _run_major_revision_no_number_change(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 major revision")
    _send_message(base_url, report_id, session_id, MAJOR_REQUEST)
    session = _session(base_url, report_id, session_id)
    verification = _assert_passed_without_number_change(session)
    _assert("body_copy" in verification.get("changed_targets", []) or "section_headings" in verification.get("changed_targets", []), f"major revision did not change structure/body: {verification}")
    md = _working_text(session, "report.md")
    _assert("\u7ba1\u7406\u5c42\u6539\u9020\u8bf4\u660e" in md, "major revision section missing")
    return {"session_id": session_id, "verification": verification}


def _run_numeric_change_block(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 numeric block")
    _send_message(base_url, report_id, session_id, NUMERIC_BLOCK_REQUEST)
    session = _session(base_url, report_id, session_id)
    turn = dict(session.get("current_turn") or {})
    verification = dict(turn.get("revision_verification") or {})
    _assert(turn.get("status") == "failed_scope_violation", f"numeric change was not blocked: {turn}")
    _assert(verification.get("blocked_change") is True, f"blocked_change missing: {verification}")
    events = _events(base_url, report_id, session_id)
    _assert(any(event.get("kind") == "blocked_change" for event in events), "blocked_change event missing")
    return {"session_id": session_id, "verification": verification, "event_count": len(events)}


def _run_annotation_context_path(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 annotation context")
    annotation = _post_annotation(base_url, report_id, session_id)
    _assert(annotation.get("annotation"), "annotation was not persisted")
    _send_message(base_url, report_id, session_id, CAPTION_REQUEST)
    session = _session(base_url, report_id, session_id)
    verification = _assert_passed_without_number_change(session)
    _assert("figure_caption" in verification.get("changed_targets", []) or "annotation_context" in verification.get("hit_targets", []), f"annotation caption was not used: {verification}")
    return {"session_id": session_id, "annotation_id": (annotation.get("annotation") or {}).get("annotation_id"), "verification": verification}


def _run_running_guidance_path(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 running guidance")
    _send_message(base_url, report_id, session_id, GUIDANCE_START_REQUEST)
    time.sleep(1.0)
    _send_message(base_url, report_id, session_id, GUIDANCE_INJECTION)
    events = _events(base_url, report_id, session_id)
    _check_event_schema(events)
    _assert(any(event.get("kind") == "user_guidance" for event in events), "running guidance was not injected into active turn")
    try:
        _request_json("POST", f"{base_url}/api/report-agent-sessions/{session_id}/cancel?report_id={urllib.parse.quote(report_id)}", payload={}, timeout=60)
    except Exception:
        pass
    return {"session_id": session_id, "event_count": len(events), "current_status": _session(base_url, report_id, session_id).get("current_turn_status")}


def _run_cancel_continue_path(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 cancel continue")
    _send_message(base_url, report_id, session_id, GUIDANCE_START_REQUEST)
    time.sleep(1.0)
    _request_json("POST", f"{base_url}/api/report-agent-sessions/{session_id}/cancel?report_id={urllib.parse.quote(report_id)}", payload={})
    time.sleep(1.0)
    _send_message(base_url, report_id, session_id, HEADLINE_REQUEST)
    session = _session(base_url, report_id, session_id)
    verification = _assert_passed_without_number_change(session)
    return {"session_id": session_id, "verification": verification, "turn_count": len(session.get("turns") or [])}


def _run_publish_versioning_path(base_url: str, report_id: str) -> dict[str, Any]:
    session_id = _create_session(base_url, report_id, "confidence v2 publish versioning")
    _send_message(base_url, report_id, session_id, SUMMARY_REQUEST)
    session = _session(base_url, report_id, session_id)
    _assert_passed_without_number_change(session)
    first = _publish(base_url, report_id, session_id)
    second = _publish(base_url, report_id, session_id)
    _assert(first.get("version") != second.get("version"), f"publish did not create a new version: {first} vs {second}")
    first_paths = {str(item.get("file_path") or "") for item in first.get("artifacts") or []}
    second_paths = {str(item.get("file_path") or "") for item in second.get("artifacts") or []}
    _assert(first_paths.isdisjoint(second_paths), "published versions reused artifact paths")
    return {"session_id": session_id, "first": first, "second": second}


CASE_RUNNERS: dict[str, Callable[[str, str], dict[str, Any]]] = {
    "chart_fast_path": _run_chart_fast_path,
    "attachment_chart_path": _run_attachment_chart_path,
    "text_only_attachment_path": _run_text_only_attachment_path,
    "strict_headline_edit": _run_strict_headline_edit,
    "major_revision_no_number_change": _run_major_revision_no_number_change,
    "numeric_change_block": _run_numeric_change_block,
    "annotation_context_path": _run_annotation_context_path,
    "running_guidance_path": _run_running_guidance_path,
    "cancel_continue_path": _run_cancel_continue_path,
    "publish_versioning_path": _run_publish_versioning_path,
}


def _run_case(case_name: str, runner: Callable[[str, str], dict[str, Any]], base_url: str, report_id: str) -> dict[str, Any]:
    started = _now_iso()
    try:
        detail = runner(base_url, report_id)
        return {"pass": True, "case": case_name, "started_at": started, "completed_at": _now_iso(), **detail}
    except Exception as exc:
        return {
            "pass": False,
            "case": case_name,
            "started_at": started,
            "completed_at": _now_iso(),
            "error": str(exc),
            "root_cause": type(exc).__name__,
            "fix_suggestion": _fix_suggestion(case_name, str(exc)),
        }


def _fix_suggestion(case_name: str, error: str) -> str:
    if "numeric" in case_name or "number" in error.lower():
        return "检查 revision verifier 的数字 token diff 与 blocked_change 守门。"
    if "guidance" in case_name or "cancel" in case_name:
        return "检查 native app-server turn 生命周期、active status 与 interrupt/cancel 桥接。"
    if "annotation" in case_name:
        return "检查 annotations.json、批注上下文注入和 caption_edit 验收。"
    if "attachment" in case_name or "chart" in case_name:
        return "检查附件 profile、revision_chart_plan、确定性渲染和报告嵌入链路。"
    return "检查 report-agent session 状态、事件 schema、文件 diff 和发布版本化。"


def run(base_url: str, report_id: str, *, loops: int = 1, output_path: Path | None = None) -> dict[str, Any]:
    health = _request_json("GET", f"{base_url}/health", timeout=30)
    _assert(str(health.get("status") or "") == "ok", f"backend health is not ok: {health}")
    reports = _request_json("GET", f"{base_url}/api/reports", timeout=60)
    report_items = reports.get("reports") or reports.get("items") or []
    if isinstance(report_items, list) and report_items:
        ids = {str(item.get("report_id") or item.get("id") or "") for item in report_items if isinstance(item, dict)}
        _assert(report_id in ids or not ids, f"report {report_id} not present in report catalog")

    matrix: list[dict[str, Any]] = []
    consecutive_green = 0
    started_at = _now_iso()
    for loop_index in range(1, loops + 1):
        loop_result = {"loop": loop_index, "started_at": _now_iso(), "cases": []}
        for case_name, runner in CASE_RUNNERS.items():
            case_result = _run_case(case_name, runner, base_url, report_id)
            loop_result["cases"].append(case_result)
        loop_pass = all(bool(item.get("pass")) for item in loop_result["cases"])
        loop_result["pass"] = loop_pass
        loop_result["completed_at"] = _now_iso()
        matrix.append(loop_result)
        if loop_pass:
            consecutive_green += 1
        else:
            break

    result = {
        "pass": consecutive_green >= loops,
        "base_url": base_url,
        "report_id": report_id,
        "requested_loops": loops,
        "consecutive_green": consecutive_green,
        "started_at": started_at,
        "completed_at": _now_iso(),
        "matrix": matrix,
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run report revision workbench confidence matrix smoke.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--report-id", default=DEFAULT_REPORT_ID)
    parser.add_argument("--loops", type=int, default=1)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    output_path = Path(args.output) if args.output else None
    try:
        result = run(args.base_url.rstrip("/"), args.report_id, loops=max(1, int(args.loops)), output_path=output_path)
    except SmokeFailure as exc:
        failure = {"pass": False, "error": str(exc), "base_url": args.base_url, "report_id": args.report_id, "completed_at": _now_iso()}
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(failure, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(json.dumps(failure, ensure_ascii=False, indent=2, default=str))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
