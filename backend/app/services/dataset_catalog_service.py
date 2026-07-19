from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.path_service import DATASETS_DIR

DATASET_LIST_CACHE_TTL_SECONDS = 60.0
DATASET_LIST_COMPACT_CACHE_VERSION = 2
DATASET_LIST_DISK_CACHE_PATH = DATASETS_DIR.parent / "dataset_catalog_cache.json"
DATASET_LIST_COMPACT_DISK_CACHE_PATH = DATASETS_DIR.parent / "dataset_catalog_compact_cache.json"
_DATASET_LIST_CACHE_LOCK = threading.Lock()
_DATASET_LIST_CACHE_TEMPLATE: dict[str, Any] = {
    "expires_at": 0.0,
    "signature": (),
    "items": [],
}
_DATASET_LIST_CACHES: dict[str, dict[str, Any]] = {
    "full": dict(_DATASET_LIST_CACHE_TEMPLATE),
    "compact": dict(_DATASET_LIST_CACHE_TEMPLATE),
}


def invalidate_dataset_list_cache() -> None:
    with _DATASET_LIST_CACHE_LOCK:
        for cache in _DATASET_LIST_CACHES.values():
            cache.update({"expires_at": 0.0, "signature": (), "items": []})
    for cache_path in (DATASET_LIST_DISK_CACHE_PATH, DATASET_LIST_COMPACT_DISK_CACHE_PATH):
        try:
            cache_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _compact_column_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(summary.get("name") or ""),
        "dtype": str(summary.get("dtype") or ""),
        "missing_count": _safe_int(summary.get("missing_count")),
        "missing_ratio": _safe_float(summary.get("missing_ratio")),
        "unique_count": _safe_int(summary.get("unique_count")),
        "sample_values": [],
        "stats": {},
    }


def _compact_sheet(sheet: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(sheet.get("name") or ""),
        "storage_file": str(sheet.get("storage_file") or ""),
        "rows": _safe_int(sheet.get("rows")),
        "columns": _safe_int(sheet.get("columns")),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _dataset_list_item(metadata: dict[str, Any], *, compact: bool = False) -> dict[str, Any]:
    column_summaries = (
        []
        if compact
        else [
            _compact_column_summary(summary)
            for summary in metadata.get("column_summaries", [])
            if isinstance(summary, dict)
        ]
    )
    item = {
        "dataset_id": str(metadata.get("dataset_id") or ""),
        "name": str(metadata.get("name") or ""),
        "filename": str(metadata.get("filename") or ""),
        "active_sheet": str(metadata.get("active_sheet") or ""),
        "sheets": [
            _compact_sheet(sheet)
            for sheet in metadata.get("sheets", [])
            if isinstance(sheet, dict)
        ],
        "row_count": _safe_int(metadata.get("row_count")),
        "column_count": _safe_int(metadata.get("column_count")),
        "numeric_columns": [] if compact else _string_list(metadata.get("numeric_columns")),
        "categorical_columns": [] if compact else _string_list(metadata.get("categorical_columns")),
        "datetime_columns": [] if compact else _string_list(metadata.get("datetime_columns")),
        "missing_cells": _safe_int(metadata.get("missing_cells")),
        "sample_rows": [],
        "chart_bundle": {},
        "column_summaries": column_summaries,
        "last_updated": str(metadata.get("last_updated") or ""),
    }
    if metadata.get("public_source"):
        item["public_source"] = str(metadata.get("public_source") or "")
    return item


def _metadata_signature(metadata_paths: list[Path]) -> tuple[tuple[str, int, int], ...]:
    signature: list[tuple[str, int, int]] = []
    for path in metadata_paths:
        try:
            stat = path.stat()
        except OSError:
            signature.append((str(path), 0, 0))
            continue
        signature.append((str(path), int(stat.st_mtime_ns), int(stat.st_size)))
    return tuple(signature)


def _signature_for_json(signature: tuple[tuple[str, int, int], ...]) -> list[list[Any]]:
    return [[path, mtime_ns, size] for path, mtime_ns, size in signature]


def _disk_cache_path(compact: bool) -> Path:
    return DATASET_LIST_COMPACT_DISK_CACHE_PATH if compact else DATASET_LIST_DISK_CACHE_PATH


def _cache_key(compact: bool) -> str:
    return "compact" if compact else "full"


def _load_disk_cache(signature: tuple[tuple[str, int, int], ...], *, compact: bool) -> list[dict[str, Any]] | None:
    try:
        payload = json.loads(_disk_cache_path(compact).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if compact and payload.get("compact_cache_version") != DATASET_LIST_COMPACT_CACHE_VERSION:
        return None
    if payload.get("signature") != _signature_for_json(signature):
        return None
    items = payload.get("items")
    if not isinstance(items, list):
        return None
    return [dict(item) for item in items if isinstance(item, dict)]


def _write_disk_cache(
    signature: tuple[tuple[str, int, int], ...],
    items: list[dict[str, Any]],
    *,
    compact: bool,
) -> None:
    try:
        _disk_cache_path(compact).write_text(
            json.dumps(
                {
                    "signature": _signature_for_json(signature),
                    "items": items,
                    **({"compact_cache_version": DATASET_LIST_COMPACT_CACHE_VERSION} if compact else {}),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


def list_datasets(*, compact: bool = False) -> list[dict[str, Any]]:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    now_ts = datetime.now(timezone.utc).timestamp()
    cache_key = _cache_key(compact)
    with _DATASET_LIST_CACHE_LOCK:
        cache = _DATASET_LIST_CACHES.setdefault(cache_key, dict(_DATASET_LIST_CACHE_TEMPLATE))
        if (
            now_ts < float(cache.get("expires_at") or 0.0)
            and isinstance(cache.get("items"), list)
        ):
            return [dict(item) for item in list(cache.get("items") or [])]

    metadata_paths = sorted(DATASETS_DIR.glob("*/metadata.json"))
    signature = _metadata_signature(metadata_paths)
    with _DATASET_LIST_CACHE_LOCK:
        cache = _DATASET_LIST_CACHES.setdefault(cache_key, dict(_DATASET_LIST_CACHE_TEMPLATE))
        if (
            cache.get("signature") == signature
            and now_ts < float(cache.get("expires_at") or 0.0)
            and isinstance(cache.get("items"), list)
        ):
            return [dict(item) for item in list(cache.get("items") or [])]

    disk_items = _load_disk_cache(signature, compact=compact)
    if disk_items is not None:
        with _DATASET_LIST_CACHE_LOCK:
            cache = _DATASET_LIST_CACHES.setdefault(cache_key, dict(_DATASET_LIST_CACHE_TEMPLATE))
            cache.update(
                {
                    "expires_at": now_ts + DATASET_LIST_CACHE_TTL_SECONDS,
                    "signature": signature,
                    "items": [dict(item) for item in disk_items],
                }
            )
        return disk_items

    items: list[dict[str, Any]] = []
    for metadata_path in metadata_paths:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(metadata, dict):
            items.append(_dataset_list_item(metadata, compact=compact))
    items.sort(key=lambda item: item.get("last_updated", ""), reverse=True)

    with _DATASET_LIST_CACHE_LOCK:
        cache = _DATASET_LIST_CACHES.setdefault(cache_key, dict(_DATASET_LIST_CACHE_TEMPLATE))
        cache.update(
            {
                "expires_at": now_ts + DATASET_LIST_CACHE_TTL_SECONDS,
                "signature": signature,
                "items": [dict(item) for item in items],
            }
        )
    _write_disk_cache(signature, items, compact=compact)
    return items


def get_dataset_summary(dataset_id: str) -> dict[str, Any] | None:
    clean_id = str(dataset_id or "").strip()
    if not clean_id:
        return None
    metadata_path = DATASETS_DIR / clean_id / "metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    return _dataset_list_item(metadata, compact=False)
