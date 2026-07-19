from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException
from websockets.exceptions import WebSocketException
from websockets.sync.client import ClientConnection, connect

from app.services.codex_cli_resolver_service import resolve_codex_cli_command
from app.services.settings_service import load_runtime_settings_raw


NativeEventHandler = Callable[[dict[str, Any]], None]
INITIALIZE_TIMEOUT_SEC = 20
# Fresh desktop app-server startups can take longer than a minute before the
# thread/start response arrives, especially when several Codex bridges exist.
THREAD_HANDSHAKE_TIMEOUT_SEC = 180
TURN_START_TIMEOUT_SEC = 90
TURN_STEER_TIMEOUT_SEC = 45


class NativeCodexUnavailable(RuntimeError):
    pass


class _PendingRequest:
    def __init__(self) -> None:
        self.event = threading.Event()
        self.response: dict[str, Any] | None = None


class _NativeBridge:
    def __init__(self, *, session_key: str, workspace_path: Path, event_handler: NativeEventHandler) -> None:
        self.session_key = session_key
        self.workspace_path = workspace_path
        self.event_handler = event_handler
        self.process: subprocess.Popen[str] | None = None
        self.ws: ClientConnection | None = None
        self.url = ""
        self.pending: dict[str, _PendingRequest] = {}
        self.pending_lock = threading.Lock()
        self.send_lock = threading.Lock()
        self.reader_thread: threading.Thread | None = None
        self.initialized = False
        self.closed = False
        self.thread_id = ""

    def start(self) -> None:
        if self.ws is not None and self.process is not None and self.process.poll() is None:
            return
        if self.process is not None and self.process.poll() is None and self.ws is None:
            try:
                self.process.terminate()
            except Exception:
                pass
        command = _resolve_codex_command()
        port = _free_port()
        self.url = f"ws://127.0.0.1:{port}"
        try:
            self.process = subprocess.Popen(
                [command, "app-server", "--analytics-default-enabled", "--listen", self.url],
                cwd=str(self.workspace_path),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise NativeCodexUnavailable(f"Failed to start Codex app-server: {exc}") from exc

        last_error: Exception | None = None
        for _ in range(450):
            if self.process.poll() is not None:
                raise NativeCodexUnavailable("Codex app-server exited during startup.")
            try:
                # Long native turns can keep the app-server busy for minutes.
                # Disable client-side keepalive pings so a healthy long turn is
                # not mistaken for a broken bridge.
                self.ws = connect(self.url, open_timeout=1, ping_interval=None)
                break
            except Exception as exc:  # pragma: no cover - platform timing
                last_error = exc
                time.sleep(0.1)
        if self.ws is None:
            raise NativeCodexUnavailable(f"Failed to connect to Codex app-server: {last_error}")

        self.closed = False
        self.reader_thread = threading.Thread(target=self._read_loop, name=f"codex-native-{self.session_key}", daemon=True)
        self.reader_thread.start()
        self.request(
            "initialize",
            {
                "clientInfo": {"name": "asteria-report-agent", "version": "0.1"},
                "capabilities": {"experimentalApi": True},
            },
            timeout_sec=INITIALIZE_TIMEOUT_SEC,
        )
        self.initialized = True

    def close(self) -> None:
        self.closed = True
        try:
            if self.ws is not None:
                self.ws.close()
        except Exception:
            pass
        try:
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
        except Exception:
            pass

    def _send_jsonrpc_response(self, request_id: str, *, result: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> None:
        if self.ws is None:
            return
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
        if error is not None:
            payload["error"] = error
        else:
            payload["result"] = result or {}
        with self.send_lock:
            self.ws.send(json.dumps(payload, ensure_ascii=False))

    def _tool_request_answers(self, params: dict[str, Any]) -> dict[str, Any]:
        answers: dict[str, Any] = {}
        for question in list(params.get("questions") or []):
            if not isinstance(question, dict):
                continue
            question_id = str(question.get("id") or "").strip()
            if not question_id:
                continue
            options = list(question.get("options") or [])
            picked_value = ""
            if options:
                first = options[0] if isinstance(options[0], dict) else {}
                for key in ("value", "id", "label", "text"):
                    candidate = str(first.get(key) or "").strip() if isinstance(first, dict) else ""
                    if candidate:
                        picked_value = candidate
                        break
            answers[question_id] = {"answers": [picked_value] if picked_value else []}
        return {"answers": answers}

    def _handle_server_request(self, request_id: str, method: str, params: dict[str, Any]) -> None:
        result: dict[str, Any] | None = None
        error: dict[str, Any] | None = None
        if method == "item/commandExecution/requestApproval":
            result = {"decision": "acceptForSession"}
        elif method == "item/fileChange/requestApproval":
            result = {"decision": "acceptForSession"}
        elif method == "applyPatchApproval":
            result = {"decision": "approved_for_session"}
        elif method == "execCommandApproval":
            result = {"decision": "approved_for_session"}
        elif method == "item/tool/requestUserInput":
            result = self._tool_request_answers(params)
        elif method == "mcpServer/elicitation/request":
            result = {"action": "decline"}
        else:
            error = {"code": -32601, "message": f"Unsupported server request: {method}"}
        self.event_handler(
            {
                "method": "native/server_request",
                "params": {
                    "request_id": request_id,
                    "method": method,
                    "auto_response": result,
                    "error": error,
                },
            }
        )
        self._send_jsonrpc_response(request_id, result=result, error=error)

    def _read_loop(self) -> None:
        while not self.closed and self.ws is not None:
            try:
                raw = self.ws.recv(timeout=1)
            except TimeoutError:
                continue
            except Exception as exc:
                self.ws = None
                if not self.closed:
                    self.event_handler({"method": "native/error", "params": {"message": str(exc)}})
                return
            try:
                message = json.loads(raw)
            except Exception:
                self.event_handler({"method": "native/raw", "params": {"text": str(raw)}})
                continue
            response_id = str(message.get("id") or "")
            method = str(message.get("method") or "")
            if response_id and method:
                params = message.get("params") if isinstance(message.get("params"), dict) else {}
                self._handle_server_request(response_id, method, params)
                continue
            if response_id:
                with self.pending_lock:
                    pending = self.pending.get(response_id)
                if pending is not None:
                    pending.response = message
                    pending.event.set()
                    continue
            self.event_handler(message)

    def request(self, method: str, params: dict[str, Any], *, timeout_sec: int = 30) -> dict[str, Any]:
        self.start_if_needed()
        if self.ws is None:
            raise NativeCodexUnavailable("Codex app-server websocket is not connected.")
        request_id = uuid.uuid4().hex
        pending = _PendingRequest()
        with self.pending_lock:
            self.pending[request_id] = pending
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        try:
            with self.send_lock:
                self.ws.send(json.dumps(payload, ensure_ascii=False))
        except (OSError, WebSocketException) as exc:
            with self.pending_lock:
                self.pending.pop(request_id, None)
            self.ws = None
            raise NativeCodexUnavailable(f"Failed to send Codex app-server request: {exc}") from exc
        if not pending.event.wait(max(1, timeout_sec)):
            with self.pending_lock:
                self.pending.pop(request_id, None)
            raise NativeCodexUnavailable(f"Codex app-server request timed out: {method}")
        with self.pending_lock:
            self.pending.pop(request_id, None)
        response = pending.response or {}
        if response.get("error"):
            raise NativeCodexUnavailable(json.dumps(response.get("error"), ensure_ascii=False, default=str))
        return dict(response.get("result") or {})

    def start_if_needed(self) -> None:
        if self.ws is None or self.process is None or self.process.poll() is not None:
            self.start()


_BRIDGES: dict[str, _NativeBridge] = {}
_BRIDGES_LOCK = threading.Lock()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def list_native_bridge_processes() -> list[dict[str, Any]]:
    with _BRIDGES_LOCK:
        bridges = list(_BRIDGES.items())
    items: list[dict[str, Any]] = []
    for key, bridge in bridges:
        process = bridge.process
        pid = process.pid if process is not None else None
        return_code = process.poll() if process is not None else None
        items.append(
            {
                "session_key": key,
                "pid": pid,
                "status": "running" if process is not None and return_code is None else "stopped",
                "thread_id": bridge.thread_id,
                "url": bridge.url,
                "workspace_path": str(bridge.workspace_path),
                "closed": bool(bridge.closed),
            }
        )
    return items


def _resolve_codex_command() -> str:
    try:
        return resolve_codex_cli_command(load_runtime_settings_raw())
    except HTTPException as exc:
        raise NativeCodexUnavailable(str(exc.detail)) from exc


def _native_enabled() -> bool:
    value = str(load_runtime_settings_raw().get("report_agent_native_codex_enabled") or "").strip().lower()
    if value:
        return value not in {"0", "false", "no", "off"}
    return str(os.environ.get("ASTERIA_REPORT_AGENT_NATIVE_CODEX_ENABLED", "1")).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _bridge_key(session: dict[str, Any]) -> str:
    return f"{session.get('report_id')}:{session.get('session_id')}"


def ensure_native_bridge(session: dict[str, Any], event_handler: NativeEventHandler) -> _NativeBridge:
    if not _native_enabled():
        raise HTTPException(status_code=503, detail="native_unavailable: Codex native app-server mode is disabled.")
    workspace_path = Path(str(session.get("workspace_path") or "")).resolve()
    if not workspace_path.is_dir():
        raise HTTPException(status_code=400, detail="Session workspace is not available for native Codex.")
    key = _bridge_key(session)
    with _BRIDGES_LOCK:
        bridge = _BRIDGES.get(key)
        if bridge is None:
            bridge = _NativeBridge(session_key=key, workspace_path=workspace_path, event_handler=event_handler)
            _BRIDGES[key] = bridge
        else:
            bridge.event_handler = event_handler
    try:
        bridge.start_if_needed()
    except NativeCodexUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"native_unavailable: {exc}") from exc
    return bridge


def ensure_native_thread(session: dict[str, Any], event_handler: NativeEventHandler, *, base_instructions: str) -> dict[str, Any]:
    bridge = ensure_native_bridge(session, event_handler)
    existing_thread_id = str(session.get("codex_thread_id") or session.get("codex_session_id") or bridge.thread_id or "")
    cwd = str(Path(str(session.get("workspace_path") or "")).resolve())
    if existing_thread_id and bridge.thread_id == existing_thread_id:
        return {"bridge": bridge, "thread_id": existing_thread_id, "result": {"thread": {"id": existing_thread_id}}}
    settings = load_runtime_settings_raw()
    model = str(settings.get("model") or "gpt-5.4").strip() or "gpt-5.4"
    try:
        if existing_thread_id:
            result = bridge.request(
                "thread/resume",
                {
                    "threadId": existing_thread_id,
                    "cwd": cwd,
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "baseInstructions": base_instructions,
                    "persistExtendedHistory": True,
                },
                timeout_sec=THREAD_HANDSHAKE_TIMEOUT_SEC,
            )
        else:
            result = bridge.request(
                "thread/start",
                {
                    "cwd": cwd,
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "model": model,
                    "baseInstructions": base_instructions,
                    "persistExtendedHistory": True,
                },
                timeout_sec=THREAD_HANDSHAKE_TIMEOUT_SEC,
            )
    except NativeCodexUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"native_unavailable: {exc}") from exc
    thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
    thread_id = str(thread.get("id") or existing_thread_id or "")
    if not thread_id:
        raise HTTPException(status_code=503, detail="native_unavailable: Codex app-server did not return a thread id.")
    bridge.thread_id = thread_id
    return {"bridge": bridge, "thread_id": thread_id, "result": result}


def start_native_turn(
    session: dict[str, Any],
    event_handler: NativeEventHandler,
    *,
    prompt: str,
    base_instructions: str,
) -> dict[str, Any]:
    thread_payload = ensure_native_thread(session, event_handler, base_instructions=base_instructions)
    bridge: _NativeBridge = thread_payload["bridge"]
    thread_id = str(thread_payload["thread_id"])
    try:
        result = bridge.request(
            "turn/start",
            {
                "threadId": thread_id,
                "cwd": str(Path(str(session.get("workspace_path") or "")).resolve()),
                "approvalPolicy": "never",
                "input": [{"type": "text", "text": prompt}],
            },
            timeout_sec=TURN_START_TIMEOUT_SEC,
        )
    except NativeCodexUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"native_unavailable: {exc}") from exc
    turn = result.get("turn") if isinstance(result.get("turn"), dict) else {}
    return {"thread_id": thread_id, "turn_id": str(turn.get("id") or ""), "result": result}


def steer_native_turn(session: dict[str, Any], event_handler: NativeEventHandler, *, guidance: str) -> dict[str, Any]:
    bridge = ensure_native_bridge(session, event_handler)
    thread_id = str(session.get("codex_thread_id") or session.get("codex_session_id") or bridge.thread_id or "")
    turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
    native_turn_id = str(session.get("active_turn_id") or turn.get("native_turn_id") or "")
    if not thread_id or not native_turn_id:
        raise HTTPException(status_code=409, detail="native_unavailable: no active native Codex turn can accept guidance.")
    try:
        result = bridge.request(
            "turn/steer",
            {
                "threadId": thread_id,
                "expectedTurnId": native_turn_id,
                "input": [{"type": "text", "text": guidance}],
            },
            timeout_sec=TURN_STEER_TIMEOUT_SEC,
        )
    except NativeCodexUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"native_unavailable: {exc}") from exc
    return {"thread_id": thread_id, "turn_id": native_turn_id, "result": result}


def interrupt_native_turn(session: dict[str, Any], event_handler: NativeEventHandler) -> dict[str, Any]:
    bridge = ensure_native_bridge(session, event_handler)
    thread_id = str(session.get("codex_thread_id") or session.get("codex_session_id") or bridge.thread_id or "")
    turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
    native_turn_id = str(session.get("active_turn_id") or turn.get("native_turn_id") or "")
    if not thread_id or not native_turn_id:
        return {"thread_id": thread_id, "turn_id": native_turn_id, "result": {}}
    try:
        result = bridge.request(
            "turn/interrupt",
            {"threadId": thread_id, "turnId": native_turn_id},
            timeout_sec=15,
        )
    except NativeCodexUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"native_unavailable: {exc}") from exc
    return {"thread_id": thread_id, "turn_id": native_turn_id, "result": result}
