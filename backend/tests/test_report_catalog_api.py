from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

import app.services.path_service as path_service_module
import app.services.report_catalog_index_service as report_catalog_index_service
import app.services.report_agent_session_service as report_service_module
from app.main import app


def _seed_report_dir(reports_dir: Path, report_id: str, manifest: dict[str, object]) -> Path:
    report_dir = reports_dir / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"{report_id}-current_turn_export_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report_dir


def test_report_catalog_api_returns_content_title_from_nested_artifact(tmp_path, monkeypatch) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(path_service_module, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(report_service_module, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(report_catalog_index_service, "REPORT_CATALOG_DB_PATH", storage_dir / "report_catalog.db")
    monkeypatch.setattr(
        report_catalog_index_service,
        "_INDEX_STATE",
        {
            "expires_at": 0.0,
            "last_scan_started_at": "",
            "last_scan_completed_at": "",
            "last_scan_count": 0,
            "is_refreshing": False,
            "refresh_mode": "",
            "last_error": "",
            "known_report_count": 0,
            "is_partial": False,
        },
    )

    report_id = "nestedapi1"
    report_dir = _seed_report_dir(
        reports_dir,
        report_id,
        {
            "report_id": report_id,
            "generated_at": "2026-05-11T00:00:00Z",
        },
    )
    nested_dir = report_dir / "r-workflow"
    nested_dir.mkdir(parents=True, exist_ok=True)
    (nested_dir / f"{report_id}-r-interpretation.html").write_text(
        """
        <html>
          <head><title>R 工作流解读</title></head>
          <body><h1>R 工作流解读</h1></body>
        </html>
        """,
        encoding="utf-8",
    )

    client = TestClient(app)
    list_response = client.get("/api/reports?limit=20")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["returned_count"] == 1
    assert list_payload["reports"][0]["content_title"] == "R 工作流解读"
    assert list_payload["reports"][0]["title"] == f"R 工作流解读（{report_id}）"

    detail_response = client.get(f"/api/reports/{report_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["content_title"] == "R 工作流解读"
    assert detail_payload["title"] == f"R 工作流解读（{report_id}）"


def test_report_catalog_api_search_uses_fts_without_sqlite_alias_error(tmp_path, monkeypatch) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(path_service_module, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(report_service_module, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(report_catalog_index_service, "REPORT_CATALOG_DB_PATH", storage_dir / "report_catalog.db")
    monkeypatch.setattr(
        report_catalog_index_service,
        "_INDEX_STATE",
        {
            "expires_at": 0.0,
            "last_scan_started_at": "",
            "last_scan_completed_at": "",
            "last_scan_count": 0,
            "is_refreshing": False,
            "refresh_mode": "",
            "last_error": "",
            "known_report_count": 0,
            "is_partial": False,
        },
    )

    report_id = "searchfts1"
    report_dir = _seed_report_dir(
        reports_dir,
        report_id,
        {
            "report_id": report_id,
            "title": "经营诊断周报",
            "generated_at": "2026-05-11T00:00:00Z",
        },
    )
    (report_dir / f"{report_id}-management_report.md").write_text(
        "# 经营诊断周报\n\n本周搜索词覆盖经营诊断、利润结构、区域对比。\n",
        encoding="utf-8",
    )

    client = TestClient(app)
    response = client.get("/api/reports", params={"q": "经营诊断", "limit": 20})
    assert response.status_code == 200
    payload = response.json()
    assert payload["returned_count"] >= 1
    assert any(item["report_id"] == report_id for item in payload["reports"])
