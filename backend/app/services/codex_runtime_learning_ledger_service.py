from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any

from app.services.codex_runtime_learning_ledger_store import (
    read_learning_ledger_entry,
    read_learning_ledger_index,
    write_learning_ledger_entry,
)
from app.services.codex_runtime_store import read_run_manifest
from app.services.path_service import PUBLIC_ARTIFACTS_DIR, REPORTS_DIR, REPO_ROOT


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_hash(payload: Any) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        text = str(payload)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256_path(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _storage_url_for(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(PUBLIC_ARTIFACTS_DIR).as_posix()
    except Exception:
        return ""
    return f"/storage/{relative}"


def _run_git(cwd: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _git_snapshot(cwd: Path) -> dict[str, Any]:
    try:
        code, stdout, _stderr = _run_git(cwd, ["rev-parse", "--is-inside-work-tree"])
        if code != 0 or stdout.strip().lower() != "true":
            return {"repo_path": str(cwd), "head": "", "dirty": False, "status_hash": "", "status_count": 0}
        head_code, head_stdout, _ = _run_git(cwd, ["rev-parse", "HEAD"])
        status_code, status_stdout, _ = _run_git(cwd, ["status", "--porcelain"])
        status_lines = [line for line in status_stdout.splitlines() if line.strip()] if status_code == 0 else []
        return {
            "repo_path": str(cwd.resolve()),
            "head": head_stdout.strip() if head_code == 0 else "",
            "dirty": bool(status_lines),
            "status_hash": _stable_hash(status_lines),
            "status_count": len(status_lines),
        }
    except Exception:
        return {"repo_path": str(cwd), "head": "", "dirty": False, "status_hash": "", "status_count": 0}


def _report_dir(report_id: str) -> Path:
    return REPORTS_DIR / f"smart-report-{report_id}"


def _safe_csv_rows(path: Path, *, limit: int = 2000) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows: list[dict[str, Any]] = []
            for index, row in enumerate(reader):
                if index >= limit:
                    break
                rows.append({str(key): value for key, value in row.items()})
            return rows
    except Exception:
        return []


def _summarize_method_log(path: Path) -> dict[str, Any]:
    rows = _safe_csv_rows(path)
    status_counts: dict[str, int] = {}
    completed_methods: list[str] = []
    skipped_methods: list[str] = []
    error_methods: list[str] = []
    for row in rows:
        method = str(row.get("method") or "").strip()
        status = str(row.get("status") or "").strip().lower()
        note = str(row.get("note") or "").strip().lower()
        normalized = status
        if not normalized:
            if note.startswith("completed"):
                normalized = "completed"
            elif note.startswith("skipped"):
                normalized = "skipped"
            elif note.startswith("error"):
                normalized = "error"
        if normalized:
            status_counts[normalized] = status_counts.get(normalized, 0) + 1
        if method and normalized == "completed" and method not in completed_methods:
            completed_methods.append(method)
        if method and normalized == "skipped" and method not in skipped_methods:
            skipped_methods.append(method)
        if method and normalized == "error" and method not in error_methods:
            error_methods.append(method)
    return {
        "path": str(path.resolve()),
        "storage_url": _storage_url_for(path),
        "sha256": _sha256_path(path),
        "row_count": len(rows),
        "status_counts": status_counts,
        "completed_methods": completed_methods[:80],
        "skipped_methods": skipped_methods[:80],
        "error_methods": error_methods[:80],
    }


def _method_artifact_summary(workspace: Path) -> dict[str, Any]:
    if not workspace.exists():
        return {
            "workspace_path": str(workspace),
            "method_signature_hash": "",
            "sources": [],
            "status_counts": {},
            "completed_methods": [],
            "artifact_names": [],
        }
    candidate_files = [
        workspace / "method_log.csv",
        workspace / "custom_metric_log.csv",
        workspace / "cross_table_metric_log.csv",
        workspace / "chart_visual_style.json",
        workspace / "03_custom_metric_execution.json",
        workspace / "04_cross_table_metric_execution.json",
    ]
    workbook_paths = sorted(workspace.glob("*-statistics-summary*.xlsx"))
    candidate_files.extend(workbook_paths[:2])
    method_sources: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    completed_methods: list[str] = []
    artifact_names: list[str] = []
    for path in candidate_files:
        if not path.exists():
            continue
        artifact_names.append(path.name)
        if path.name == "method_log.csv":
            summary = _summarize_method_log(path)
            method_sources.append({"kind": "method_log", **summary})
            for key, value in dict(summary.get("status_counts") or {}).items():
                status_counts[str(key)] = status_counts.get(str(key), 0) + int(value)
            for method in list(summary.get("completed_methods") or []):
                if method not in completed_methods:
                    completed_methods.append(method)
        else:
            method_sources.append(
                {
                    "kind": path.suffix.lstrip(".").lower() or "file",
                    "path": str(path.resolve()),
                    "storage_url": _storage_url_for(path),
                    "sha256": _sha256_path(path),
                    "name": path.name,
                }
            )
    payload = {
        "workspace_path": str(workspace.resolve()),
        "sources": method_sources,
        "status_counts": status_counts,
        "completed_methods": completed_methods[:120],
        "artifact_names": artifact_names[:120],
    }
    payload["method_signature_hash"] = _stable_hash(payload)
    return payload


def _prompt_ref_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    request = dict(manifest.get("request") or {}) if isinstance(manifest.get("request"), dict) else {}
    return {
        "run_id": str(manifest.get("run_id") or ""),
        "status": str(manifest.get("status") or ""),
        "stage_id": str(manifest.get("stage_id") or request.get("stage_id") or ""),
        "purpose": str(manifest.get("purpose") or request.get("purpose") or ""),
        "prompt_hash": str(manifest.get("prompt_hash") or request.get("prompt_hash") or ""),
        "prompt_preview": str(manifest.get("prompt_preview") or request.get("prompt_preview") or ""),
        "prompt_length": int(manifest.get("prompt_length") or request.get("prompt_length") or 0),
        "prompt_source": str(manifest.get("prompt_source") or ""),
        "context_payload_hash": str(request.get("context_payload_hash") or ""),
        "context_top_level_keys": list(request.get("context_top_level_keys") or []),
        "workspace_path": str(manifest.get("workspace_path") or request.get("workspace_path") or ""),
        "created_at": str(manifest.get("created_at") or ""),
    }


def _linked_run_manifests(run_ids: list[str]) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run_id in run_ids:
        normalized = str(run_id or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        try:
            manifests.append(read_run_manifest(normalized))
        except Exception:
            continue
    return manifests


def _aggregate_prompt_version(run_manifests: list[dict[str, Any]], *, extra_refs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    prompt_refs = [_prompt_ref_from_manifest(manifest) for manifest in run_manifests]
    for item in list(extra_refs or []):
        if isinstance(item, dict):
            prompt_refs.append(dict(item))
    prompt_refs = [item for item in prompt_refs if str(item.get("run_id") or item.get("prompt_hash") or "").strip()]
    return {
        "prompt_refs": prompt_refs,
        "prompt_bundle_hash": _stable_hash(prompt_refs),
        "prompt_count": len(prompt_refs),
        "prompt_hashes": [str(item.get("prompt_hash") or "") for item in prompt_refs if str(item.get("prompt_hash") or "").strip()][:120],
    }


def _aggregate_code_version(
    *,
    workspace_path: str = "",
    run_manifests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    run_manifests = run_manifests or []
    project_git = _git_snapshot(REPO_ROOT)
    workspace_git = _git_snapshot(Path(workspace_path).expanduser().resolve()) if workspace_path else {}
    linked_run_git = [
        {
            "run_id": str(manifest.get("run_id") or ""),
            "git_head_before": str(manifest.get("git_head_before") or ""),
            "git_head_after": str(manifest.get("git_head_after") or ""),
            "changed_files_count": len(list(manifest.get("changed_files") or [])),
        }
        for manifest in run_manifests
    ]
    changed_files: list[str] = []
    for manifest in run_manifests:
        for path in list(manifest.get("changed_files") or []):
            normalized = str(path or "").strip()
            if normalized and normalized not in changed_files:
                changed_files.append(normalized)
    payload = {
        "repo_root": str(REPO_ROOT.resolve()),
        "project_git": project_git,
        "workspace_path": workspace_path,
        "workspace_git": workspace_git,
        "linked_run_git": linked_run_git[:120],
        "changed_files_count": len(changed_files),
        "changed_files_sample": changed_files[:80],
    }
    payload["code_version_hash"] = _stable_hash(payload)
    return payload


def _extract_quality_outcome(*, report: dict[str, Any] | None = None, report_dir: Path | None = None) -> dict[str, Any]:
    report = report or {}
    report_id = str(report.get("report_id") or "").strip()
    resolved_report_dir = report_dir or (_report_dir(report_id) if report_id else None)
    gate_payload = dict(report.get("quality_gate_result") or {}) if isinstance(report.get("quality_gate_result"), dict) else {}
    score_payload = dict(report.get("report_quality_score") or {}) if isinstance(report.get("report_quality_score"), dict) else {}
    if resolved_report_dir:
        if not gate_payload:
            gate_payload = _safe_read_json(resolved_report_dir / f"{report_id}-quality_gate_result.json")
        if not score_payload:
            score_payload = _safe_read_json(resolved_report_dir / f"{report_id}-report_quality_score.json")
    try:
        score = float(score_payload.get("score")) if score_payload.get("score") is not None else None
    except Exception:
        score = None
    payload = {
        "score": score,
        "verdict": str(score_payload.get("verdict") or ""),
        "passed": gate_payload.get("passed"),
        "formal_pdf_allowed": report.get("formal_pdf_allowed"),
        "release_blocked": report.get("release_blocked"),
        "gate_fail_items": list(gate_payload.get("fail_items") or [])[:40],
        "weaknesses": list(score_payload.get("weaknesses") or [])[:20],
        "quality_gate_path": str((resolved_report_dir / f"{report_id}-quality_gate_result.json").resolve()) if resolved_report_dir and report_id else "",
        "quality_score_path": str((resolved_report_dir / f"{report_id}-report_quality_score.json").resolve()) if resolved_report_dir and report_id else "",
    }
    payload["quality_signature_hash"] = _stable_hash(payload)
    return payload


def _main_downloadable_summary(report: dict[str, Any]) -> dict[str, Any]:
    main = dict(report.get("main_downloadable") or {}) if isinstance(report.get("main_downloadable"), dict) else {}
    return {
        "name": str(main.get("name") or ""),
        "path": str(main.get("path") or ""),
        "file_path": str(main.get("file_path") or ""),
        "purpose": str(main.get("purpose") or ""),
        "type": str(main.get("type") or ""),
        "is_main": bool(main.get("is_main")),
    }


def capture_runtime_run_learning_ledger(run_payload: dict[str, Any]) -> dict[str, Any]:
    manifest = dict(run_payload or {})
    run_id = str(manifest.get("run_id") or "").strip()
    if not run_id:
        raise ValueError("Runtime run ledger capture requires run_id.")
    request = dict(manifest.get("request") or {}) if isinstance(manifest.get("request"), dict) else {}
    run_manifests = [manifest]
    prompt_version = _aggregate_prompt_version(run_manifests)
    code_version = _aggregate_code_version(workspace_path=str(manifest.get("workspace_path") or ""), run_manifests=run_manifests)
    method_version = _method_artifact_summary(Path(str(manifest.get("workspace_path") or "")).expanduser().resolve())
    entry = {
        "source_type": "runtime_run",
        "source_id": run_id,
        "run_id": run_id,
        "status": str(manifest.get("status") or ""),
        "workspace_path": str(manifest.get("workspace_path") or ""),
        "report_id": str(manifest.get("parent_report_id") or request.get("parent_report_id") or request.get("report_id") or ""),
        "linked_report_id": str(manifest.get("parent_report_id") or request.get("parent_report_id") or request.get("report_id") or ""),
        "report_job_id": str(manifest.get("parent_report_job_id") or request.get("parent_report_job_id") or ""),
        "prompt_version": prompt_version,
        "code_version": code_version,
        "statistical_method_version": method_version,
        "final_score": {
            "score": None,
            "passed": None,
            "formal_pdf_allowed": None,
            "release_blocked": None,
            "quality_signature_hash": "",
        },
        "artifacts": {
            "summary_path": str(manifest.get("summary_path") or ""),
            "summary_url": str(manifest.get("summary_url") or ""),
            "transcript_path": str(manifest.get("transcript_path") or ""),
            "git_diff_path": str(manifest.get("git_diff_path") or ""),
            "changed_files_count": len(list(manifest.get("changed_files") or [])),
        },
        "outcome": {
            "summary_preview": str(manifest.get("summary") or "")[:600],
            "error": str(manifest.get("error") or ""),
            "session_id": str(manifest.get("session_id") or ""),
            "exit_code": manifest.get("exit_code"),
            "transcript_entry_count": int(manifest.get("transcript_entry_count") or 0),
        },
        "created_at": str(manifest.get("created_at") or _now_iso()),
        "updated_at": _now_iso(),
    }
    entry["summary"] = {
        "label": "runtime_run",
        "score": None,
        "prompt_bundle_hash": prompt_version.get("prompt_bundle_hash"),
        "code_version_hash": code_version.get("code_version_hash"),
        "method_signature_hash": method_version.get("method_signature_hash"),
    }
    return write_learning_ledger_entry(entry, record_key=f"runtime_run:{run_id}:{entry['status']}")


def capture_pipeline_learning_ledger(manifest: dict[str, Any]) -> dict[str, Any]:
    pipeline_job_id = str(manifest.get("pipeline_job_id") or "").strip()
    if not pipeline_job_id:
        raise ValueError("Pipeline ledger capture requires pipeline_job_id.")
    workspace_path = str(manifest.get("workspace_path") or "")
    linked_report_id = str(manifest.get("linked_report_id") or "")
    run_manifests = _linked_run_manifests(list(manifest.get("linked_codex_run_ids") or []))
    prompt_version = _aggregate_prompt_version(run_manifests)
    code_version = _aggregate_code_version(workspace_path=workspace_path, run_manifests=run_manifests)
    method_version = _method_artifact_summary(Path(workspace_path).expanduser().resolve())
    quality = _extract_quality_outcome(report_dir=_report_dir(linked_report_id) if linked_report_id else None)
    entry = {
        "source_type": "pipeline",
        "source_id": pipeline_job_id,
        "pipeline_job_id": pipeline_job_id,
        "pipeline_type": str(manifest.get("pipeline_type") or ""),
        "status": str(manifest.get("status") or ""),
        "workspace_path": workspace_path,
        "linked_report_id": linked_report_id,
        "report_id": linked_report_id,
        "prompt_version": prompt_version,
        "code_version": code_version,
        "statistical_method_version": method_version,
        "final_score": quality,
        "artifacts": {
            "artifact_count": len(list(manifest.get("artifact_index") or [])),
            "artifact_names": [str(item.get("name") or "") for item in list(manifest.get("artifact_index") or [])[:80]],
            "final_output_keys": sorted(str(key) for key in dict(manifest.get("final_output") or {}).keys())[:80],
        },
        "outcome": {
            "current_stage_id": str(manifest.get("current_stage_id") or ""),
            "current_stage_title": str(manifest.get("current_stage_title") or ""),
            "current_stage_detail": str(manifest.get("current_stage_detail") or ""),
            "error": str(manifest.get("error") or ""),
            "progress_percent": int(manifest.get("progress_percent") or 0),
            "linked_codex_run_ids": list(manifest.get("linked_codex_run_ids") or []),
        },
        "created_at": str(manifest.get("created_at") or _now_iso()),
        "updated_at": _now_iso(),
    }
    entry["summary"] = {
        "label": "pipeline",
        "score": quality.get("score"),
        "pipeline_type": entry["pipeline_type"],
        "prompt_bundle_hash": prompt_version.get("prompt_bundle_hash"),
        "code_version_hash": code_version.get("code_version_hash"),
        "method_signature_hash": method_version.get("method_signature_hash"),
    }
    return write_learning_ledger_entry(entry, record_key=f"pipeline:{pipeline_job_id}:{entry['status']}")


def capture_report_learning_ledger(
    report: dict[str, Any],
    *,
    request_payload: dict[str, Any] | None = None,
    dataset_id: str = "",
    report_job_id: str = "",
) -> dict[str, Any]:
    report_id = str(report.get("report_id") or "").strip()
    if not report_id:
        raise ValueError("Report ledger capture requires report_id.")
    report_dir = _report_dir(report_id)
    linked_run_ids = list(report.get("linked_codex_run_ids") or [])
    requirement_runtime = dict(report.get("requirement_intent_runtime") or {}) if isinstance(report.get("requirement_intent_runtime"), dict) else {}
    requirement_run_id = str(requirement_runtime.get("run_id") or "").strip()
    if requirement_run_id and requirement_run_id not in linked_run_ids:
        linked_run_ids.append(requirement_run_id)
    runtime_child_jobs = list(report.get("runtime_child_jobs") or [])
    for child_job in runtime_child_jobs:
        run_id = str((child_job or {}).get("run_id") or "").strip()
        if run_id and run_id not in linked_run_ids:
            linked_run_ids.append(run_id)
    run_manifests = _linked_run_manifests(linked_run_ids)
    prompt_version = _aggregate_prompt_version(run_manifests)
    code_version = _aggregate_code_version(workspace_path=str(report_dir.resolve()), run_manifests=run_manifests)
    method_workspaces: list[Path] = []
    r_workflow = dict(report.get("r_workflow") or {}) if isinstance(report.get("r_workflow"), dict) else {}
    workflow_dir = str(r_workflow.get("workflow_dir") or "").strip()
    if workflow_dir:
        workflow_path = Path(workflow_dir)
        if not workflow_path.is_absolute():
            workflow_path = report_dir / workflow_dir
        method_workspaces.append(workflow_path.expanduser().resolve())
    method_workspaces.append(report_dir)
    method_version_items = [_method_artifact_summary(path) for path in method_workspaces if path.exists()]
    method_version = {
        "workspaces": method_version_items,
        "method_signature_hash": _stable_hash(method_version_items),
        "completed_methods": list(
            dict.fromkeys(
                method
                for item in method_version_items
                for method in list(item.get("completed_methods") or [])
            )
        )[:160],
        "status_counts": {
            key: sum(int((item.get("status_counts") or {}).get(key) or 0) for item in method_version_items)
            for key in sorted(
                {
                    key
                    for item in method_version_items
                    for key in dict(item.get("status_counts") or {}).keys()
                }
            )
        },
    }
    quality = _extract_quality_outcome(report=report, report_dir=report_dir)
    request_payload = dict(request_payload or {})
    requirement_intent = dict(report.get("requirement_intent") or {}) if isinstance(report.get("requirement_intent"), dict) else {}
    entry = {
        "source_type": "report",
        "source_id": report_id,
        "report_id": report_id,
        "linked_report_id": report_id,
        "report_job_id": str(report_job_id or report.get("parent_report_job_id") or ""),
        "dataset_id": str(dataset_id or report.get("dataset_id") or ""),
        "dataset_name": str(report.get("dataset_name") or ""),
        "sheet_name": str(report.get("sheet_name") or ""),
        "business_profile": str(report.get("business_profile") or ""),
        "report_style": str(report.get("report_style") or ""),
        "status": "completed",
        "workspace_path": str(report_dir.resolve()),
        "prompt_version": {
            **prompt_version,
            "request_payload_hash": _stable_hash(request_payload),
            "requirement_intent_hash": _stable_hash(requirement_intent),
        },
        "code_version": code_version,
        "statistical_method_version": method_version,
        "final_score": quality,
        "artifacts": {
            "report_dir": str(report_dir.resolve()),
            "main_downloadable": _main_downloadable_summary(report),
            "downloadable_count": len(list(report.get("downloadables") or [])),
            "linked_codex_pipeline_job_ids": list(report.get("linked_codex_pipeline_job_ids") or []),
        },
        "outcome": {
            "formal_pdf_allowed": report.get("formal_pdf_allowed"),
            "release_blocked": report.get("release_blocked"),
            "generic_long_cli_pipeline_status": str((report.get("generic_long_cli_pipeline") or {}).get("status") or "") if isinstance(report.get("generic_long_cli_pipeline"), dict) else "",
            "multi_table_generic_long_cli_pipeline_status": str((report.get("multi_table_generic_long_cli_pipeline") or {}).get("status") or "") if isinstance(report.get("multi_table_generic_long_cli_pipeline"), dict) else "",
            "historical_style_cli_pipeline_status": str((report.get("historical_style_cli_pipeline") or {}).get("status") or "") if isinstance(report.get("historical_style_cli_pipeline"), dict) else "",
            "r_workflow_status": str(r_workflow.get("status") or ""),
        },
        "created_at": str(report.get("generated_at") or _now_iso()),
        "updated_at": _now_iso(),
    }
    entry["summary"] = {
        "label": "report",
        "score": quality.get("score"),
        "business_profile": entry["business_profile"],
        "prompt_bundle_hash": entry["prompt_version"].get("prompt_bundle_hash"),
        "code_version_hash": code_version.get("code_version_hash"),
        "method_signature_hash": method_version.get("method_signature_hash"),
    }
    return write_learning_ledger_entry(entry, record_key=f"report:{report_id}")


def capture_report_failure_learning_ledger(
    *,
    dataset_id: str,
    report_job_id: str,
    request_payload: dict[str, Any],
    error: str,
) -> dict[str, Any]:
    code_version = _aggregate_code_version(workspace_path=str(REPO_ROOT.resolve()), run_manifests=[])
    request_payload = dict(request_payload or {})
    entry = {
        "source_type": "report_failure",
        "source_id": str(report_job_id),
        "report_job_id": str(report_job_id),
        "dataset_id": str(dataset_id),
        "status": "failed",
        "workspace_path": str(REPO_ROOT.resolve()),
        "prompt_version": {
            "prompt_refs": [],
            "prompt_bundle_hash": "",
            "prompt_count": 0,
            "prompt_hashes": [],
            "request_payload_hash": _stable_hash(request_payload),
        },
        "code_version": code_version,
        "statistical_method_version": {
            "workspaces": [],
            "method_signature_hash": "",
            "completed_methods": [],
            "status_counts": {},
        },
        "final_score": {
            "score": None,
            "passed": False,
            "formal_pdf_allowed": None,
            "release_blocked": True,
            "quality_signature_hash": "",
        },
        "artifacts": {},
        "outcome": {
            "error": str(error or ""),
            "request_preview": {
                "business_profile": str(request_payload.get("business_profile") or ""),
                "report_style": str(request_payload.get("report_style") or ""),
                "sheet_name": str(request_payload.get("sheet_name") or ""),
                "multi_table_mode": str(request_payload.get("multi_table_mode") or ""),
            },
        },
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "summary": {
            "label": "report_failure",
            "score": None,
            "business_profile": str(request_payload.get("business_profile") or ""),
            "prompt_bundle_hash": "",
            "code_version_hash": code_version.get("code_version_hash"),
            "method_signature_hash": "",
        },
    }
    return write_learning_ledger_entry(entry, record_key=f"report_failure:{report_job_id}")


def list_learning_ledger_entries(*, limit: int = 100, source_type: str = "", status: str = "") -> list[dict[str, Any]]:
    entries = list(read_learning_ledger_index())
    if source_type:
        entries = [item for item in entries if str(item.get("source_type") or "") == source_type]
    if status:
        entries = [item for item in entries if str(item.get("status") or "") == status]
    return entries[: max(1, min(int(limit or 100), 500))]


def get_learning_ledger_entry(entry_id: str) -> dict[str, Any]:
    return read_learning_ledger_entry(entry_id)
