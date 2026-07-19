from __future__ import annotations

import json
import os
import sys
from typing import Any

from app.models import RuntimeSettingsRequest, RuntimeSettingsResponse
from app.services.path_service import REPO_ROOT, SETTINGS_PATH, bundled_rscript_candidates

DEFAULT_SETTINGS = {
    "api_key": "",
    "model": "gpt-5.4",
    "base_url": "",
    "provider_label": "OpenAI",
    "relay_note": "Blank Base URL uses the official OpenAI Responses API endpoint.",
    "rscript_path": "",
    "reasoning_effort": "xhigh",
    "codex_cli_path": "codex",
    "codex_runtime_enabled": False,
    "codex_workspace_root": "",
    "codex_search_enabled": False,
    "codex_timeout_sec": 1800,
    "codex_dangerously_bypass_approvals_and_sandbox": False,
    "codex_use_login_auth": True,
    "codex_runtime_api_enabled": False,
}


def _mask_api_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * max(4, len(value) - 8)}{value[-4:]}"


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "")).strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return default


def _env_int(name: str, default: int) -> int:
    raw = str(os.getenv(name, "")).strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_settings() -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "")
    model = os.getenv("OPENAI_MODEL", DEFAULT_SETTINGS["model"])
    reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", DEFAULT_SETTINGS["reasoning_effort"])
    rscript_path = os.getenv("ASTERIA_RSCRIPT_PATH", "")
    codex_cli_path = os.getenv("ASTERIA_CODEX_CLI_PATH", DEFAULT_SETTINGS["codex_cli_path"])
    codex_workspace_root = os.getenv("ASTERIA_CODEX_WORKSPACE_ROOT", DEFAULT_SETTINGS["codex_workspace_root"])
    relay_note = "Loaded from environment variables." if any([api_key, base_url]) else ""
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "provider_label": DEFAULT_SETTINGS["provider_label"],
        "relay_note": relay_note,
        "rscript_path": rscript_path,
        "reasoning_effort": reasoning_effort,
        "codex_cli_path": codex_cli_path,
        "codex_runtime_enabled": _env_bool("ASTERIA_CODEX_RUNTIME_ENABLED", DEFAULT_SETTINGS["codex_runtime_enabled"]),
        "codex_workspace_root": codex_workspace_root,
        "codex_search_enabled": _env_bool("ASTERIA_CODEX_SEARCH_ENABLED", DEFAULT_SETTINGS["codex_search_enabled"]),
        "codex_timeout_sec": _env_int("ASTERIA_CODEX_TIMEOUT_SEC", DEFAULT_SETTINGS["codex_timeout_sec"]),
        "codex_dangerously_bypass_approvals_and_sandbox": _env_bool(
            "ASTERIA_CODEX_BYPASS_APPROVALS_AND_SANDBOX",
            DEFAULT_SETTINGS["codex_dangerously_bypass_approvals_and_sandbox"],
        ),
        "codex_use_login_auth": _env_bool("ASTERIA_CODEX_USE_LOGIN_AUTH", DEFAULT_SETTINGS["codex_use_login_auth"]),
        "codex_runtime_api_enabled": _env_bool(
            "ASTERIA_ENABLE_CODEX_RUNTIME_API",
            DEFAULT_SETTINGS["codex_runtime_api_enabled"],
        ),
    }


def load_runtime_settings_raw() -> dict[str, Any]:
    payload = {**DEFAULT_SETTINGS, **_env_settings()}
    stored_has_workspace_root = False
    if SETTINGS_PATH.exists():
        try:
            stored = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            payload.update({key: stored.get(key, payload[key]) for key in DEFAULT_SETTINGS})
            stored_has_workspace_root = "codex_workspace_root" in stored
        except json.JSONDecodeError:
            pass
    # Codex execution is off until explicitly enabled by the deployment environment.
    # Persisted local settings must never re-enable it after a release restart.
    payload["codex_runtime_enabled"] = _env_bool(
        "ASTERIA_CODEX_RUNTIME_ENABLED",
        DEFAULT_SETTINGS["codex_runtime_enabled"],
    )
    payload["codex_runtime_api_enabled"] = _env_bool(
        "ASTERIA_ENABLE_CODEX_RUNTIME_API",
        DEFAULT_SETTINGS["codex_runtime_api_enabled"],
    )
    # A persisted preference is not sufficient to remove Codex sandbox protections.
    # Operators must explicitly authorize an unsandboxed runtime in the environment.
    payload["codex_dangerously_bypass_approvals_and_sandbox"] = bool(
        payload.get("codex_dangerously_bypass_approvals_and_sandbox", False)
    ) and _env_bool("ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME", False)
    env_has_workspace_root = "ASTERIA_CODEX_WORKSPACE_ROOT" in os.environ
    if (
        not str(payload.get("codex_workspace_root") or "").strip()
        and not stored_has_workspace_root
        and not env_has_workspace_root
        and not getattr(sys, "frozen", False)
    ):
        payload["codex_workspace_root"] = str(REPO_ROOT.resolve())
    if not str(payload.get("rscript_path") or "").strip():
        for candidate in bundled_rscript_candidates():
            if candidate.exists():
                payload["rscript_path"] = str(candidate.resolve())
                break
    return payload


def load_runtime_settings() -> RuntimeSettingsResponse:
    payload = load_runtime_settings_raw()
    return RuntimeSettingsResponse(
        api_key_masked=_mask_api_key(payload["api_key"]),
        has_api_key=bool(payload["api_key"]),
        model=payload["model"],
        base_url=payload["base_url"],
        provider_label=payload["provider_label"],
        relay_note=payload["relay_note"],
        rscript_path=payload["rscript_path"],
        reasoning_effort=payload["reasoning_effort"],
        codex_cli_path=payload["codex_cli_path"],
        codex_runtime_enabled=bool(payload["codex_runtime_enabled"]),
        codex_workspace_root=str(payload["codex_workspace_root"] or ""),
        codex_search_enabled=bool(payload["codex_search_enabled"]),
        codex_timeout_sec=int(payload["codex_timeout_sec"]),
        codex_dangerously_bypass_approvals_and_sandbox=bool(
            payload["codex_dangerously_bypass_approvals_and_sandbox"]
        ),
        codex_use_login_auth=bool(payload["codex_use_login_auth"]),
        codex_runtime_api_enabled=bool(payload["codex_runtime_api_enabled"]),
    )


def save_runtime_settings(payload: RuntimeSettingsRequest) -> RuntimeSettingsResponse:
    current = load_runtime_settings_raw()
    next_payload = payload.model_dump()
    if not next_payload["api_key"] and current.get("api_key"):
        next_payload["api_key"] = current["api_key"]

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(next_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return load_runtime_settings()
