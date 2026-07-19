from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any
import uuid

from app.services.path_service import CODEX_RUNTIME_LEARNING_LEDGER_DIR


LEDGER_ENTRIES_DIR = CODEX_RUNTIME_LEARNING_LEDGER_DIR / "entries"
LEDGER_INDEX_PATH = CODEX_RUNTIME_LEARNING_LEDGER_DIR / "entries_index.json"
LEDGER_RECORD_INDEX_PATH = CODEX_RUNTIME_LEARNING_LEDGER_DIR / "record_index.json"
LEDGER_LOCK_PATH = CODEX_RUNTIME_LEARNING_LEDGER_DIR / ".ledger.lock"


def ensure_learning_ledger_dirs() -> None:
    CODEX_RUNTIME_LEARNING_LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER_ENTRIES_DIR.mkdir(parents=True, exist_ok=True)


def ledger_entry_path(entry_id: str) -> Path:
    ensure_learning_ledger_dirs()
    return LEDGER_ENTRIES_DIR / f"{entry_id}.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def read_learning_ledger_index() -> list[dict[str, Any]]:
    ensure_learning_ledger_dirs()
    payload = _read_json(LEDGER_INDEX_PATH, [])
    return payload if isinstance(payload, list) else []


def write_learning_ledger_index(entries: list[dict[str, Any]]) -> Path:
    ensure_learning_ledger_dirs()
    return _write_json(LEDGER_INDEX_PATH, entries)


def read_learning_ledger_record_index() -> dict[str, str]:
    ensure_learning_ledger_dirs()
    payload = _read_json(LEDGER_RECORD_INDEX_PATH, {})
    return payload if isinstance(payload, dict) else {}


def write_learning_ledger_record_index(payload: dict[str, str]) -> Path:
    ensure_learning_ledger_dirs()
    return _write_json(LEDGER_RECORD_INDEX_PATH, payload)


class _LedgerFileLock:
    def __init__(self, path: Path, *, timeout_sec: float = 10.0, poll_sec: float = 0.05) -> None:
        self._path = path
        self._timeout_sec = timeout_sec
        self._poll_sec = poll_sec
        self._fd: int | None = None

    def __enter__(self) -> "_LedgerFileLock":
        ensure_learning_ledger_dirs()
        deadline = time.time() + max(0.5, float(self._timeout_sec))
        while True:
            try:
                self._fd = os.open(str(self._path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self._fd, str(os.getpid()).encode("utf-8", errors="ignore"))
                return self
            except FileExistsError:
                if time.time() >= deadline:
                    raise TimeoutError(f"Timed out acquiring learning ledger lock: {self._path}")
                time.sleep(self._poll_sec)

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            if self._fd is not None:
                os.close(self._fd)
        finally:
            self._fd = None
            try:
                self._path.unlink()
            except FileNotFoundError:
                pass


def read_learning_ledger_entry(entry_id: str) -> dict[str, Any]:
    path = ledger_entry_path(entry_id)
    if not path.exists():
        raise FileNotFoundError(f"Learning ledger entry not found: {entry_id}")
    payload = _read_json(path, {})
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid learning ledger entry: {entry_id}")
    return payload


def write_learning_ledger_entry(payload: dict[str, Any], *, record_key: str = "") -> dict[str, Any]:
    ensure_learning_ledger_dirs()
    with _LedgerFileLock(LEDGER_LOCK_PATH):
        record_index = read_learning_ledger_record_index()
        existing_entry_id = str(record_index.get(record_key) or "").strip() if record_key else ""
        entry_id = existing_entry_id or str(payload.get("entry_id") or f"ledger-{uuid.uuid4().hex[:12]}")
        entry_payload = dict(payload)
        entry_payload["entry_id"] = entry_id
        entry_payload["record_key"] = str(record_key or entry_payload.get("record_key") or "")
        _write_json(ledger_entry_path(entry_id), entry_payload)

        index = list(read_learning_ledger_index())
        summary = dict(entry_payload.get("summary") or {})
        summary.update(
            {
                "entry_id": entry_id,
                "record_key": str(entry_payload.get("record_key") or ""),
                "source_type": str(entry_payload.get("source_type") or ""),
                "source_id": str(entry_payload.get("source_id") or ""),
                "status": str(entry_payload.get("status") or ""),
                "report_id": str(entry_payload.get("report_id") or ""),
                "linked_report_id": str(entry_payload.get("linked_report_id") or ""),
                "report_job_id": str(entry_payload.get("report_job_id") or ""),
                "pipeline_job_id": str(entry_payload.get("pipeline_job_id") or ""),
                "run_id": str(entry_payload.get("run_id") or ""),
                "created_at": str(entry_payload.get("created_at") or ""),
                "updated_at": str(entry_payload.get("updated_at") or ""),
            }
        )
        replaced = False
        for idx, item in enumerate(index):
            if str((item or {}).get("entry_id") or "") == entry_id:
                index[idx] = summary
                replaced = True
                break
        if not replaced:
            index.append(summary)
        index.sort(key=lambda item: str((item or {}).get("updated_at") or ""), reverse=True)
        write_learning_ledger_index(index)

        if record_key:
            record_index[record_key] = entry_id
            write_learning_ledger_record_index(record_index)
        return entry_payload
