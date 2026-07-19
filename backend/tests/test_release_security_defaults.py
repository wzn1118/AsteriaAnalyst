from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import INTEGRATIONS, app, r_intelligence_flow
from app.models import RWorkflowIntelligenceRequest, RuntimeSettingsRequest, RuntimeSettingsResponse
from app.services import settings_service
from app.services.path_service import DATASETS_DIR, PUBLIC_ARTIFACTS_DIR, RUNS_DIR, SETTINGS_PATH


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def test_storage_mount_exposes_only_public_artifacts() -> None:
    storage_mount = next(route for route in app.routes if getattr(route, "path", None) == "/storage")

    assert Path(storage_mount.app.directory).resolve() == PUBLIC_ARTIFACTS_DIR
    assert not _is_within(DATASETS_DIR, PUBLIC_ARTIFACTS_DIR)
    assert not _is_within(RUNS_DIR, PUBLIC_ARTIFACTS_DIR)
    assert not _is_within(SETTINGS_PATH, PUBLIC_ARTIFACTS_DIR)


def test_release_disables_code_execution_and_runtime_settings_write_routes() -> None:
    paths = {getattr(route, "path", None): set(getattr(route, "methods", set())) for route in app.routes}

    assert "/api/code/execute" not in paths
    assert paths["/api/runtime-settings"] == {"GET"}


def test_backend_manifest_no_longer_advertises_sheetjs() -> None:
    integration_names = {str(integration["name"]) for integration in INTEGRATIONS}

    assert "SheetJS" not in integration_names


def test_codex_runtime_api_requires_explicit_environment_opt_in(tmp_path: Path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "codex_runtime_api_enabled": True,
                "codex_dangerously_bypass_approvals_and_sandbox": True,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_service, "SETTINGS_PATH", settings_path)
    monkeypatch.delenv("ASTERIA_CODEX_RUNTIME_ENABLED", raising=False)
    monkeypatch.delenv("ASTERIA_ENABLE_CODEX_RUNTIME_API", raising=False)
    monkeypatch.delenv("ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME", raising=False)

    disabled = settings_service.load_runtime_settings_raw()
    assert disabled["codex_runtime_enabled"] is False
    assert disabled["codex_runtime_api_enabled"] is False
    assert disabled["codex_dangerously_bypass_approvals_and_sandbox"] is False

    monkeypatch.setenv("ASTERIA_CODEX_RUNTIME_ENABLED", "true")
    monkeypatch.setenv("ASTERIA_ENABLE_CODEX_RUNTIME_API", "true")
    enabled = settings_service.load_runtime_settings_raw()
    assert enabled["codex_runtime_enabled"] is True
    assert enabled["codex_runtime_api_enabled"] is True

    monkeypatch.setenv("ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME", "true")
    unsandboxed = settings_service.load_runtime_settings_raw()
    assert unsandboxed["codex_dangerously_bypass_approvals_and_sandbox"] is True


def test_r_intelligence_route_rejects_traversal_report_id() -> None:
    try:
        r_intelligence_flow(r"..\..\private", RWorkflowIntelligenceRequest())
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "report_id" in str(exc.detail)
    else:
        raise AssertionError("Traversal report_id was accepted")


def test_runtime_models_default_to_disabled_codex_runtime_api() -> None:
    assert RuntimeSettingsRequest().codex_runtime_enabled is False
    assert RuntimeSettingsRequest().codex_runtime_api_enabled is False
    assert RuntimeSettingsResponse().codex_runtime_enabled is False
    assert RuntimeSettingsResponse().codex_runtime_api_enabled is False


def test_lab_skill_mutation_and_execution_routes_fail_closed(monkeypatch) -> None:
    monkeypatch.delenv("ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER", raising=False)
    client = TestClient(app)
    requests = [
        ("post", "/api/lab/skills/install", {"source_url": "https://github.com/example/repo"}),
        ("post", "/api/lab/skills/import-local", {"local_path": "E:/missing-skill"}),
        ("post", "/api/lab/skills/example/mount", None),
        ("post", "/api/lab/skills/example/unmount", None),
        ("delete", "/api/lab/skills/example", None),
        (
            "post",
            "/api/lab/feature-trials/run",
            {"dataset_id": "dataset", "plugin_id": "plugin", "feature_kind": "command", "feature_id": "feature"},
        ),
        ("post", "/api/lab/report-agent-teams/import-local", {"local_path": "E:/missing-team"}),
        ("post", "/api/lab/report-agent-teams/example/mount", None),
        ("post", "/api/lab/report-agent-teams/example/unmount", None),
        ("delete", "/api/lab/report-agent-teams/example", None),
        ("post", "/api/lab/report-agent-teams/run", {}),
    ]

    for method, path, payload in requests:
        response = getattr(client, method)(path, json=payload) if payload is not None else getattr(client, method)(path)
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SKILL_INSTALLATION_DISABLED"

    assert client.get("/api/lab/skills").status_code == 200
    assert client.get("/api/lab/report-agent-teams").status_code == 200
