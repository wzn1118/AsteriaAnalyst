from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

from app.services.path_service import RUNS_DIR


CODEX_PIPELINE_DIR = RUNS_DIR / "codex_pipeline"
CODEX_PIPELINE_JOBS_DIR = CODEX_PIPELINE_DIR / "jobs"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_codex_pipeline_dirs() -> None:
    CODEX_PIPELINE_JOBS_DIR.mkdir(parents=True, exist_ok=True)


def pipeline_dir(pipeline_job_id: str) -> Path:
    ensure_codex_pipeline_dirs()
    path = CODEX_PIPELINE_JOBS_DIR / str(pipeline_job_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def pipeline_manifest_path(pipeline_job_id: str) -> Path:
    return pipeline_dir(pipeline_job_id) / "pipeline.json"


def pipeline_stage_artifacts_path(pipeline_job_id: str) -> Path:
    return pipeline_dir(pipeline_job_id) / "stage_artifacts.json"


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp_path = path.with_name(f"{path.name}.tmp-{uuid.uuid4().hex[:8]}")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _default_pipeline_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    pipeline_job_id = str(payload.get("pipeline_job_id") or f"codex-pipeline-{uuid.uuid4().hex[:12]}")
    created_at = str(payload.get("created_at") or _now_iso())
    return {
        "pipeline_job_id": pipeline_job_id,
        "pipeline_type": str(payload.get("pipeline_type") or ""),
        "workspace_path": str(payload.get("workspace_path") or ""),
        "context_payload": dict(payload.get("context_payload") or {}),
        "session_id": str(payload.get("session_id") or ""),
        "stage_order": list(payload.get("stage_order") or []),
        "current_stage": dict(payload.get("current_stage") or {}),
        "stage_outputs": dict(payload.get("stage_outputs") or {}),
        "artifact_index": list(payload.get("artifact_index") or []),
        "final_output": dict(payload.get("final_output") or {}),
        "linked_report_id": str(payload.get("linked_report_id") or ""),
        "linked_codex_run_ids": list(payload.get("linked_codex_run_ids") or []),
        "linked_codex_task_ids": list(payload.get("linked_codex_task_ids") or []),
        "status": str(payload.get("status") or "queued"),
        "error": str(payload.get("error") or ""),
        "progress_percent": int(payload.get("progress_percent") or 0),
        "current_stage_id": str(payload.get("current_stage_id") or "queued"),
        "current_stage_title": str(payload.get("current_stage_title") or "Pipeline created"),
        "current_stage_detail": str(payload.get("current_stage_detail") or "Pipeline is waiting for execution."),
        "stage_events": list(payload.get("stage_events") or []),
        "created_at": created_at,
        "updated_at": str(payload.get("updated_at") or created_at),
        "result_summary": dict(payload.get("result_summary") or {}),
    }


def _normalize_manifest_for_write(manifest: dict[str, Any]) -> dict[str, Any]:
    if str(manifest.get("status") or "") == "completed":
        if str(manifest.get("current_stage_id") or "") in {"", "queued"}:
            manifest["current_stage_id"] = "completed"
        if str(manifest.get("current_stage_title") or "") in {"", "Pipeline created"}:
            manifest["current_stage_title"] = "Pipeline completed"
        if str(manifest.get("current_stage_detail") or "") in {"", "Pipeline is waiting for execution."}:
            manifest["current_stage_detail"] = "Pipeline completed."
        manifest["progress_percent"] = 100
        current_stage = dict(manifest.get("current_stage") or {})
        if str(current_stage.get("stage_id") or "") in {"", "queued"}:
            manifest["current_stage"] = {
                "stage_id": "completed",
                "title": "Pipeline Completed",
                "status": "completed",
                "attempt": int(current_stage.get("attempt") or 1),
                "started_at": str(current_stage.get("started_at") or ""),
                "run_id": str(current_stage.get("run_id") or ""),
                "task_id": str(current_stage.get("task_id") or ""),
                "detail": "Pipeline completed.",
            }
    return manifest


def create_pipeline_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    manifest = _normalize_manifest_for_write(_default_pipeline_manifest(payload))
    pipeline_job_id = str(manifest["pipeline_job_id"])
    _write_json(pipeline_manifest_path(pipeline_job_id), manifest)
    _write_json(pipeline_stage_artifacts_path(pipeline_job_id), {"pipeline_job_id": pipeline_job_id, "artifacts": []})
    return manifest


def read_pipeline_manifest(pipeline_job_id: str) -> dict[str, Any]:
    path = pipeline_manifest_path(pipeline_job_id)
    if not path.exists():
        raise FileNotFoundError(f"Codex pipeline job not found: {pipeline_job_id}")
    manifest = _read_json(path)
    if not isinstance(manifest, dict):
        raise ValueError(f"Invalid Codex pipeline manifest: {pipeline_job_id}")
    normalized = _normalize_manifest_for_write(dict(manifest))
    if normalized != manifest:
        normalized["updated_at"] = _now_iso()
        _write_json(path, normalized)
    return normalized


def update_pipeline_manifest(pipeline_job_id: str, updates: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    manifest = read_pipeline_manifest(pipeline_job_id)
    merged_updates = dict(updates or {})
    merged_updates.update(kwargs)
    manifest.update(merged_updates)
    manifest = _normalize_manifest_for_write(manifest)
    manifest["updated_at"] = _now_iso()
    _write_json(pipeline_manifest_path(pipeline_job_id), manifest)
    return manifest


def persist_stage_artifact_metadata(
    pipeline_job_id: str,
    *,
    stage_id: str,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    manifest = read_pipeline_manifest(pipeline_job_id)
    artifacts_path = pipeline_stage_artifacts_path(pipeline_job_id)
    artifact_store = _read_json(artifacts_path) if artifacts_path.exists() else {"pipeline_job_id": pipeline_job_id, "artifacts": []}
    artifacts = list(artifact_store.get("artifacts") or [])

    artifact_id = str(artifact.get("artifact_id") or f"artifact-{uuid.uuid4().hex[:12]}")
    stage_artifact = {
        "artifact_id": artifact_id,
        "stage_id": stage_id,
        "name": str(artifact.get("name") or ""),
        "path": str(artifact.get("path") or ""),
        "storage_url": str(artifact.get("storage_url") or ""),
        "artifact_type": str(artifact.get("artifact_type") or ""),
        "role": str(artifact.get("role") or "stage_output"),
        "is_primary": bool(artifact.get("is_primary", False)),
        "created_at": str(artifact.get("created_at") or _now_iso()),
    }
    artifacts.append(stage_artifact)
    artifact_store = {
        "pipeline_job_id": pipeline_job_id,
        "artifacts": artifacts,
    }
    _write_json(artifacts_path, artifact_store)

    manifest_artifact_index = list(manifest.get("artifact_index") or [])
    manifest_artifact_index.append(stage_artifact)

    stage_outputs = dict(manifest.get("stage_outputs") or {})
    current_stage_output = dict(stage_outputs.get(stage_id) or {})
    output_files = list(current_stage_output.get("output_files") or [])
    artifact_name = stage_artifact["name"]
    if artifact_name and artifact_name not in output_files:
        output_files.append(artifact_name)
    current_stage_output["output_files"] = output_files
    stage_outputs[stage_id] = current_stage_output

    manifest.update(
        {
            "artifact_index": manifest_artifact_index,
            "stage_outputs": stage_outputs,
            "updated_at": _now_iso(),
        }
    )
    _write_json(pipeline_manifest_path(pipeline_job_id), manifest)
    return stage_artifact
