from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.codex_runtime_pipeline_service import (  # noqa: E402
    get_pipeline_job,
    run_pipeline,
)


def _emit(log_path: Path, payload: dict[str, Any]) -> None:
    payload = dict(payload)
    payload["watcher_ts"] = _dt.datetime.now().isoformat(timespec="seconds")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        handle.flush()


def _summary(manifest: dict[str, Any]) -> dict[str, Any]:
    stage_outputs = dict(manifest.get("stage_outputs") or {})
    return {
        "status": manifest.get("status"),
        "current_stage_id": manifest.get("current_stage_id"),
        "current_stage_title": manifest.get("current_stage_title"),
        "progress_percent": manifest.get("progress_percent"),
        "error": manifest.get("error"),
        "completed_stages": [
            key for key, value in stage_outputs.items()
            if isinstance(value, dict) and value.get("status") == "completed"
        ],
        "failed_stages": [
            key for key, value in stage_outputs.items()
            if isinstance(value, dict) and value.get("status") == "failed"
        ],
        "final_output": manifest.get("final_output") or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and watch a Codex pipeline job until terminal status.")
    parser.add_argument("pipeline_job_id")
    parser.add_argument("--log", default=str(PROJECT_ROOT / "workspace" / "tmp" / "codex_pipeline_watch.log"))
    parser.add_argument("--sleep", type=float, default=2.0)
    parser.add_argument("--max-iterations", type=int, default=48)
    args = parser.parse_args()

    log_path = Path(args.log).expanduser().resolve()
    terminal_statuses = {"completed", "failed", "cancelled"}
    job_id = str(args.pipeline_job_id)
    _emit(log_path, {"event": "start", "pipeline_job_id": job_id})

    for iteration in range(max(1, int(args.max_iterations))):
        manifest = get_pipeline_job(job_id)
        _emit(log_path, {"event": "before_run", "iteration": iteration, **_summary(manifest)})
        if str(manifest.get("status") or "") in terminal_statuses:
            _emit(log_path, {"event": "terminal", "iteration": iteration, **_summary(manifest)})
            return 0
        manifest = run_pipeline(job_id)
        _emit(log_path, {"event": "after_run", "iteration": iteration, **_summary(manifest)})
        if str(manifest.get("status") or "") in terminal_statuses:
            _emit(log_path, {"event": "terminal", "iteration": iteration, **_summary(manifest)})
            return 0 if str(manifest.get("status") or "") == "completed" else 2
        time.sleep(max(0.0, float(args.sleep)))

    manifest = get_pipeline_job(job_id)
    _emit(log_path, {"event": "iteration_guard", **_summary(manifest)})
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
