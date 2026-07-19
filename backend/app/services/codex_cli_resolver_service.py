from __future__ import annotations

import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.services.path_service import bundled_codex_cli_candidates
from app.services.settings_service import load_runtime_settings_raw

_CODEX_CLI_HEALTH_TTL_SECONDS = 20.0
_CODEX_CLI_HEALTH_LOCK = threading.Lock()
_CODEX_CLI_HEALTH_CACHE: dict[str, Any] = {
    "expires_at": 0.0,
    "payload": None,
    "refreshing": False,
    "settings_fingerprint": "",
}


def _append_unique(candidates: list[Path | str], value: Path | str | None) -> None:
    if value is None:
        return
    text = str(value).strip()
    if not text:
        return
    lowered = text.lower()
    if all(str(candidate).lower() != lowered for candidate in candidates):
        candidates.append(value)


def codex_cli_candidates(settings: dict[str, Any] | None = None) -> list[Path | str]:
    payload = settings or load_runtime_settings_raw()
    candidates: list[Path | str] = []
    configured = str(payload.get("codex_cli_path") or "").strip()
    if configured and configured != "codex":
        _append_unique(candidates, Path(configured).expanduser())
    for candidate in bundled_codex_cli_candidates():
        _append_unique(candidates, candidate)
    _append_unique(candidates, configured or "codex")
    _append_unique(candidates, "codex")
    return candidates


def resolve_codex_cli_command(settings: dict[str, Any] | None = None) -> str:
    for candidate in codex_cli_candidates(settings):
        text = str(candidate).strip()
        if not text:
            continue
        path = Path(text).expanduser()
        if path.exists() and path.is_file():
            return str(path.resolve())
        discovered = shutil.which(text)
        if discovered:
            return discovered
    raise HTTPException(
        status_code=500,
        detail=(
            "Codex CLI not found. Install Codex globally, set ASTERIA_CODEX_CLI_PATH, "
            "or bundle it under runtime/codex/bin/codex(.exe)."
        ),
    )


def _codex_health_payload(payload: dict[str, Any]) -> dict[str, Any]:
    checked: list[str] = []
    for candidate in codex_cli_candidates(payload):
        text = str(candidate)
        if text not in checked:
            checked.append(text)
    try:
        command = resolve_codex_cli_command(payload)
    except HTTPException as exc:
        return {
            "available": False,
            "resolved_path": "",
            "version": "",
            "app_server_available": False,
            "checked_candidates": checked,
            "error": str(exc.detail),
            "portable_hint": "Place codex.exe/codex.cmd at runtime/codex/bin/ or set ASTERIA_CODEX_CLI_PATH.",
        }

    version = ""
    app_server_available = False
    error = ""
    try:
        version_proc = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
        version = (version_proc.stdout or version_proc.stderr or "").strip()
    except Exception as exc:
        error = str(exc)
    try:
        help_proc = subprocess.run(
            [command, "app-server", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
        app_server_available = help_proc.returncode == 0 and "app-server" in ((help_proc.stdout or "") + (help_proc.stderr or ""))
    except Exception as exc:
        error = error or str(exc)

    return {
        "available": True,
        "resolved_path": command,
        "version": version,
        "app_server_available": app_server_available,
        "checked_candidates": checked,
        "error": error,
        "portable_hint": "For offline/portable machines, bundle Codex at runtime/codex/bin/codex(.exe) or set ASTERIA_CODEX_CLI_PATH.",
    }


def _initial_codex_health_payload(payload: dict[str, Any]) -> dict[str, Any]:
    checked: list[str] = []
    for candidate in codex_cli_candidates(payload):
        text = str(candidate)
        if text not in checked:
            checked.append(text)
    try:
        command = resolve_codex_cli_command(payload)
    except HTTPException as exc:
        return {
            "available": False,
            "resolved_path": "",
            "version": "",
            "checked_candidates": checked,
            "app_server_available": False,
            "error": str(exc.detail),
            "portable_hint": "Place codex.exe/codex.cmd at runtime/codex/bin/ or set ASTERIA_CODEX_CLI_PATH.",
        }
    return {
        "available": True,
        "resolved_path": command,
        "version": "",
        "checked_candidates": checked,
        "is_checking": True,
        "portable_hint": "For offline/portable machines, bundle Codex at runtime/codex/bin/codex(.exe) or set ASTERIA_CODEX_CLI_PATH.",
    }


def _refresh_codex_cli_health(payload: dict[str, Any], fingerprint: str) -> None:
    result = _codex_health_payload(payload)
    with _CODEX_CLI_HEALTH_LOCK:
        _CODEX_CLI_HEALTH_CACHE["payload"] = dict(result)
        _CODEX_CLI_HEALTH_CACHE["expires_at"] = time.monotonic() + _CODEX_CLI_HEALTH_TTL_SECONDS
        _CODEX_CLI_HEALTH_CACHE["settings_fingerprint"] = fingerprint
        _CODEX_CLI_HEALTH_CACHE["refreshing"] = False


def _start_codex_cli_health_refresh(payload: dict[str, Any], fingerprint: str) -> None:
    worker = threading.Thread(
        target=_refresh_codex_cli_health,
        args=(dict(payload), fingerprint),
        daemon=True,
        name="codex-cli-health-refresh",
    )
    worker.start()


def codex_cli_health(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = settings or load_runtime_settings_raw()
    fingerprint = str(payload)
    now = time.monotonic()
    with _CODEX_CLI_HEALTH_LOCK:
        cached_payload = _CODEX_CLI_HEALTH_CACHE.get("payload")
        expires_at = float(_CODEX_CLI_HEALTH_CACHE.get("expires_at") or 0.0)
        cached_fingerprint = str(_CODEX_CLI_HEALTH_CACHE.get("settings_fingerprint") or "")
        refreshing = bool(_CODEX_CLI_HEALTH_CACHE.get("refreshing"))
        if cached_payload is not None and cached_fingerprint == fingerprint and expires_at > now:
            return dict(cached_payload)
        if cached_payload is not None and cached_fingerprint == fingerprint:
            if not refreshing:
                _CODEX_CLI_HEALTH_CACHE["refreshing"] = True
                _start_codex_cli_health_refresh(payload, fingerprint)
            return dict(cached_payload)
        if not refreshing:
            initial = _initial_codex_health_payload(payload)
            _CODEX_CLI_HEALTH_CACHE["payload"] = dict(initial)
            _CODEX_CLI_HEALTH_CACHE["expires_at"] = now + 2.0
            _CODEX_CLI_HEALTH_CACHE["settings_fingerprint"] = fingerprint
            _CODEX_CLI_HEALTH_CACHE["refreshing"] = True
            _start_codex_cli_health_refresh(payload, fingerprint)
            return dict(initial)

    cached_payload = _CODEX_CLI_HEALTH_CACHE.get("payload")
    if cached_payload is not None:
        return dict(cached_payload)
    result = _initial_codex_health_payload(payload)
    return dict(result)
