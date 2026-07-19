from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import report_agent_session_service as report_service_module


@pytest.fixture
def isolated_report_catalog_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(report_service_module, "REPORTS_DIR", reports_dir)
    return reports_dir


def _seed_report_dir(reports_dir: Path, report_id: str, manifest: dict[str, object]) -> Path:
    report_dir = reports_dir / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = report_dir / f"{report_id}-current_turn_export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_dir


def test_report_summary_prefers_manifest_business_title(isolated_report_catalog_paths: Path) -> None:
    report_id = "abc12345"
    report_dir = _seed_report_dir(
        isolated_report_catalog_paths,
        report_id,
        {
            "report_id": report_id,
            "title": "商品承接兑现镜：单日漏斗经营报告",
            "generated_at": "2026-05-11T00:00:00Z",
        },
    )

    summary = report_service_module._report_summary(report_dir, catalog_mode=True)

    assert summary["content_title"] == "商品承接兑现镜：单日漏斗经营报告"
    assert summary["title"] == "商品承接兑现镜：单日漏斗经营报告（abc12345）"


def test_report_summary_extracts_title_from_html_when_manifest_title_is_placeholder(isolated_report_catalog_paths: Path) -> None:
    report_id = "zero9abc"
    report_dir = _seed_report_dir(
        isolated_report_catalog_paths,
        report_id,
        {
            "report_id": report_id,
            "title": f"报告 {report_id}",
            "generated_at": "2026-05-11T00:00:00Z",
            "downloadables": [
                {
                    "name": f"{report_id}-generic_long_cli_report.html",
                    "file_path": str((isolated_report_catalog_paths / f"smart-report-{report_id}" / f"{report_id}-generic_long_cli_report.html").resolve()),
                    "is_main": True,
                    "type": "html",
                }
            ],
        },
    )
    (report_dir / f"{report_id}-generic_long_cli_report.html").write_text(
        """
        <html>
          <head><title>12 商品承接兑现镜：单日商品漏斗经营报告</title></head>
          <body><h1>12 商品承接兑现镜</h1></body>
        </html>
        """,
        encoding="utf-8",
    )

    summary = report_service_module._report_summary(report_dir, catalog_mode=True)

    assert summary["content_title"] == "12 商品承接兑现镜：单日商品漏斗经营报告"
    assert summary["title"] == "12 商品承接兑现镜：单日商品漏斗经营报告（zero9abc）"


def test_report_summary_extracts_title_from_markdown_when_manifest_has_no_title(isolated_report_catalog_paths: Path) -> None:
    report_id = "ops88xyz"
    report_dir = _seed_report_dir(
        isolated_report_catalog_paths,
        report_id,
        {
            "report_id": report_id,
            "generated_at": "2026-05-11T00:00:00Z",
            "downloadables": [
                {
                    "name": f"{report_id}-management_report.md",
                    "file_path": str((isolated_report_catalog_paths / f"smart-report-{report_id}" / f"{report_id}-management_report.md").resolve()),
                    "is_main": True,
                    "type": "md",
                }
            ],
        },
    )
    (report_dir / f"{report_id}-management_report.md").write_text(
        "# 用户增长报告补建交付包管理报告\n\n## 执行结论\n\n这是一份测试报告。\n",
        encoding="utf-8",
    )

    summary = report_service_module._report_summary(report_dir, catalog_mode=True)

    assert summary["content_title"] == "用户增长报告补建交付包管理报告"
    assert summary["title"] == "用户增长报告补建交付包管理报告（ops88xyz）"


def test_report_summary_extracts_title_from_nested_catalog_artifact(isolated_report_catalog_paths: Path) -> None:
    report_id = "nested001"
    report_dir = _seed_report_dir(
        isolated_report_catalog_paths,
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
    (nested_dir / "codex_sidecar_review.md").write_text(
        "# Codex sidecar review\n\nThis should not win.\n",
        encoding="utf-8",
    )

    summary = report_service_module._report_summary(report_dir, catalog_mode=True)

    assert summary["content_title"] == "R 工作流解读"
    assert summary["title"] == "R 工作流解读（nested001）"
