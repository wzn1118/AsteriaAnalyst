from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from app.services.path_service import STORAGE_DIR


REPORT_CATALOG_DB_PATH = STORAGE_DIR / "report_catalog.db"
REPORT_CATALOG_INDEX_TTL_SECONDS = 180.0
REPORT_CATALOG_INDEX_ERROR_BACKOFF_SECONDS = 15.0

_DB_LOCK = threading.Lock()
_INDEX_STATE_LOCK = threading.Lock()
_SCHEMA_LOCK = threading.Lock()
_SCHEMA_READY_FOR = ""
_INDEX_STATE: dict[str, Any] = {
    "expires_at": 0.0,
    "last_scan_started_at": "",
    "last_scan_completed_at": "",
    "last_scan_count": 0,
    "is_refreshing": False,
    "refresh_mode": "",
    "last_error": "",
    "known_report_count": 0,
    "is_partial": False,
}


def _connect() -> sqlite3.Connection:
    REPORT_CATALOG_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(REPORT_CATALOG_DB_PATH, check_same_thread=False, timeout=10.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA synchronous=NORMAL;")
    connection.execute("PRAGMA temp_store=MEMORY;")
    connection.execute("PRAGMA busy_timeout=10000;")
    return connection


def ensure_report_catalog_index() -> None:
    global _SCHEMA_READY_FOR
    schema_key = str(REPORT_CATALOG_DB_PATH.resolve())
    if _SCHEMA_READY_FOR == schema_key:
        return
    with _SCHEMA_LOCK:
        if _SCHEMA_READY_FOR == schema_key:
            return
        with _connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS report_catalog_index (
                    report_id TEXT PRIMARY KEY,
                    report_dir_name TEXT NOT NULL,
                    report_dir_path TEXT NOT NULL,
                    report_dir_mtime_ns INTEGER NOT NULL DEFAULT 0,
                    generated_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL DEFAULT '',
                    content_title TEXT NOT NULL DEFAULT '',
                    dataset_id TEXT NOT NULL DEFAULT '',
                    dataset_name TEXT NOT NULL DEFAULT '',
                    business_profile TEXT NOT NULL DEFAULT '',
                    preview_url TEXT NOT NULL DEFAULT '',
                    downloadable_count INTEGER NOT NULL DEFAULT 0,
                    manifest_json TEXT NOT NULL DEFAULT '{}',
                    main_downloadable_json TEXT NOT NULL DEFAULT '{}',
                    preview_downloadable_json TEXT NOT NULL DEFAULT '{}',
                    latest_revision_session_json TEXT NOT NULL DEFAULT 'null',
                    search_text TEXT NOT NULL DEFAULT '',
                    last_indexed_at TEXT NOT NULL DEFAULT '',
                    sort_generated_ts INTEGER NOT NULL DEFAULT 0,
                    sort_updated_ts INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_report_catalog_updated_ts
                    ON report_catalog_index(sort_updated_ts DESC, report_id DESC);

                CREATE INDEX IF NOT EXISTS idx_report_catalog_generated_ts
                    ON report_catalog_index(sort_generated_ts DESC, report_id DESC);

                CREATE INDEX IF NOT EXISTS idx_report_catalog_dataset_id
                    ON report_catalog_index(dataset_id);

                CREATE INDEX IF NOT EXISTS idx_report_catalog_business_profile
                    ON report_catalog_index(business_profile);

                CREATE VIRTUAL TABLE IF NOT EXISTS report_catalog_fts
                USING fts5(
                    report_id,
                    title,
                    content_title,
                    dataset_id,
                    dataset_name,
                    business_profile,
                    search_text,
                    content='',
                    tokenize='unicode61'
                );
                """
            )
        _SCHEMA_READY_FOR = schema_key


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def _json_loads(raw: str, fallback: Any) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return fallback


def _apply_index_state(
    *,
    expires_at: float | None = None,
    last_scan_started_at: str | None = None,
    last_scan_completed_at: str | None = None,
    last_scan_count: int | None = None,
    is_refreshing: bool | None = None,
    refresh_mode: str | None = None,
    last_error: str | None = None,
    known_report_count: int | None = None,
    is_partial: bool | None = None,
) -> None:
    with _INDEX_STATE_LOCK:
        if expires_at is not None:
            _INDEX_STATE["expires_at"] = float(expires_at)
        if last_scan_started_at is not None:
            _INDEX_STATE["last_scan_started_at"] = str(last_scan_started_at)
        if last_scan_completed_at is not None:
            _INDEX_STATE["last_scan_completed_at"] = str(last_scan_completed_at)
        if last_scan_count is not None:
            _INDEX_STATE["last_scan_count"] = int(last_scan_count)
        if is_refreshing is not None:
            _INDEX_STATE["is_refreshing"] = bool(is_refreshing)
        if refresh_mode is not None:
            _INDEX_STATE["refresh_mode"] = str(refresh_mode)
        if last_error is not None:
            _INDEX_STATE["last_error"] = str(last_error)
        if known_report_count is not None:
            _INDEX_STATE["known_report_count"] = int(known_report_count)
        if is_partial is not None:
            _INDEX_STATE["is_partial"] = bool(is_partial)


def _fts_query_for(keyword: str) -> str:
    tokens = [segment.strip() for segment in keyword.replace("/", " ").replace("-", " ").split() if segment.strip()]
    if not tokens:
        return ""
    normalized: list[str] = []
    for token in tokens[:8]:
        safe = token.replace('"', '""')
        normalized.append(f'"{safe}"*')
    return " AND ".join(normalized)


def _keyword_prefers_like_search(keyword: str) -> bool:
    text = str(keyword or "").strip()
    if not text:
        return False
    return any(ord(char) > 127 for char in text)


def _upsert_report_catalog_row(cursor: sqlite3.Cursor, row: dict[str, Any], indexed_at: str) -> None:
    report_id = str(row.get("report_id") or "").strip()
    if not report_id:
        return
    cursor.execute(
        """
        INSERT INTO report_catalog_index (
            report_id,
            report_dir_name,
            report_dir_path,
            report_dir_mtime_ns,
            generated_at,
            updated_at,
            title,
            content_title,
            dataset_id,
            dataset_name,
            business_profile,
            preview_url,
            downloadable_count,
            manifest_json,
            main_downloadable_json,
            preview_downloadable_json,
            latest_revision_session_json,
            search_text,
            last_indexed_at,
            sort_generated_ts,
            sort_updated_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(report_id) DO UPDATE SET
            report_dir_name=excluded.report_dir_name,
            report_dir_path=excluded.report_dir_path,
            report_dir_mtime_ns=excluded.report_dir_mtime_ns,
            generated_at=excluded.generated_at,
            updated_at=excluded.updated_at,
            title=excluded.title,
            content_title=excluded.content_title,
            dataset_id=excluded.dataset_id,
            dataset_name=excluded.dataset_name,
            business_profile=excluded.business_profile,
            preview_url=excluded.preview_url,
            downloadable_count=excluded.downloadable_count,
            manifest_json=excluded.manifest_json,
            main_downloadable_json=excluded.main_downloadable_json,
            preview_downloadable_json=excluded.preview_downloadable_json,
            latest_revision_session_json=excluded.latest_revision_session_json,
            search_text=excluded.search_text,
            last_indexed_at=excluded.last_indexed_at,
            sort_generated_ts=excluded.sort_generated_ts,
            sort_updated_ts=excluded.sort_updated_ts
        """,
        (
            report_id,
            str(row.get("report_dir_name") or ""),
            str(row.get("report_dir_path") or ""),
            int(row.get("report_dir_mtime_ns") or 0),
            str(row.get("generated_at") or ""),
            str(row.get("updated_at") or ""),
            str(row.get("title") or ""),
            str(row.get("content_title") or ""),
            str(row.get("dataset_id") or ""),
            str(row.get("dataset_name") or ""),
            str(row.get("business_profile") or ""),
            str(row.get("preview_url") or ""),
            int(row.get("downloadable_count") or 0),
            _json_dumps(row.get("manifest") or {}),
            _json_dumps(row.get("main_downloadable") or {}),
            _json_dumps(row.get("preview_downloadable") or {}),
            _json_dumps(row.get("latest_revision_session")),
            str(row.get("search_text") or ""),
            indexed_at,
            int(row.get("sort_generated_ts") or 0),
            int(row.get("sort_updated_ts") or 0),
        ),
    )
    cursor.execute("DELETE FROM report_catalog_fts WHERE report_id = ?", (report_id,))
    cursor.execute(
        """
        INSERT INTO report_catalog_fts (
            report_id,
            title,
            content_title,
            dataset_id,
            dataset_name,
            business_profile,
            search_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            str(row.get("title") or ""),
            str(row.get("content_title") or ""),
            str(row.get("dataset_id") or ""),
            str(row.get("dataset_name") or ""),
            str(row.get("business_profile") or ""),
            str(row.get("search_text") or ""),
        ),
    )


def replace_report_catalog_rows(rows: list[dict[str, Any]]) -> None:
    ensure_report_catalog_index()
    indexed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with _DB_LOCK:
        with _connect() as connection:
            cursor = connection.cursor()
            cursor.execute("BEGIN")
            try:
                cursor.execute("DELETE FROM report_catalog_index")
                cursor.execute("DELETE FROM report_catalog_fts")

                for row in rows:
                    _upsert_report_catalog_row(cursor, row, indexed_at)
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    _apply_index_state(
        expires_at=time.monotonic() + REPORT_CATALOG_INDEX_TTL_SECONDS,
        last_scan_completed_at=indexed_at,
        last_scan_count=len(rows),
        last_error="",
        is_partial=False,
    )


def upsert_report_catalog_rows(rows: list[dict[str, Any]]) -> None:
    ensure_report_catalog_index()
    indexed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    applied_count = 0
    with _DB_LOCK:
        with _connect() as connection:
            cursor = connection.cursor()
            cursor.execute("BEGIN")
            try:
                for row in rows:
                    report_id = str(row.get("report_id") or "").strip()
                    if not report_id:
                        continue
                    _upsert_report_catalog_row(cursor, row, indexed_at)
                    applied_count += 1
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    _apply_index_state(
        expires_at=time.monotonic() + REPORT_CATALOG_INDEX_TTL_SECONDS,
        last_scan_completed_at=indexed_at,
        last_scan_count=applied_count,
        last_error="",
    )


def delete_report_catalog_rows(report_ids: list[str]) -> None:
    ids = [str(report_id or "").strip() for report_id in report_ids if str(report_id or "").strip()]
    if not ids:
        return
    ensure_report_catalog_index()
    with _DB_LOCK:
        with _connect() as connection:
            cursor = connection.cursor()
            cursor.execute("BEGIN")
            try:
                cursor.executemany("DELETE FROM report_catalog_index WHERE report_id = ?", [(report_id,) for report_id in ids])
                cursor.executemany("DELETE FROM report_catalog_fts WHERE report_id = ?", [(report_id,) for report_id in ids])
                connection.commit()
            except Exception:
                connection.rollback()
                raise


def mark_report_catalog_scan_started() -> None:
    _apply_index_state(
        last_scan_started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        is_refreshing=True,
        last_error="",
    )


def mark_report_catalog_scan_finished(
    *,
    refresh_mode: str = "",
    known_report_count: int | None = None,
    is_partial: bool | None = None,
    error: str = "",
) -> None:
    _apply_index_state(
        expires_at=time.monotonic()
        + (REPORT_CATALOG_INDEX_ERROR_BACKOFF_SECONDS if error else REPORT_CATALOG_INDEX_TTL_SECONDS),
        last_scan_completed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        is_refreshing=False,
        refresh_mode=refresh_mode,
        known_report_count=known_report_count,
        is_partial=is_partial,
        last_error=error,
    )


def mark_report_catalog_partial_seed(count: int, *, known_report_count: int) -> None:
    _apply_index_state(
        last_scan_count=count,
        known_report_count=known_report_count,
        is_partial=True,
        refresh_mode="seed",
    )


def report_catalog_index_is_refreshing() -> bool:
    with _INDEX_STATE_LOCK:
        return bool(_INDEX_STATE.get("is_refreshing"))


def report_catalog_index_is_fresh() -> bool:
    with _INDEX_STATE_LOCK:
        return float(_INDEX_STATE.get("expires_at") or 0.0) > time.monotonic()


def report_catalog_index_status() -> dict[str, Any]:
    ensure_report_catalog_index()
    with _connect() as connection:
        total_count = int(connection.execute("SELECT COUNT(*) AS count FROM report_catalog_index").fetchone()["count"])
    with _INDEX_STATE_LOCK:
        return {
            "database_path": str(REPORT_CATALOG_DB_PATH.resolve()),
            "is_fresh": float(_INDEX_STATE.get("expires_at") or 0.0) > time.monotonic(),
            "last_scan_started_at": str(_INDEX_STATE.get("last_scan_started_at") or ""),
            "last_scan_completed_at": str(_INDEX_STATE.get("last_scan_completed_at") or ""),
            "last_scan_count": int(_INDEX_STATE.get("last_scan_count") or 0),
            "is_refreshing": bool(_INDEX_STATE.get("is_refreshing")),
            "refresh_mode": str(_INDEX_STATE.get("refresh_mode") or ""),
            "last_error": str(_INDEX_STATE.get("last_error") or ""),
            "known_report_count": int(_INDEX_STATE.get("known_report_count") or 0),
            "is_partial": bool(_INDEX_STATE.get("is_partial")),
            "indexed_report_count": total_count,
        }


def report_catalog_index_snapshot() -> dict[str, dict[str, Any]]:
    ensure_report_catalog_index()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT report_id, report_dir_mtime_ns, updated_at, last_indexed_at
            FROM report_catalog_index
            """
        ).fetchall()
    return {
        str(row["report_id"] or ""): {
            "report_dir_mtime_ns": int(row["report_dir_mtime_ns"] or 0),
            "updated_at": str(row["updated_at"] or ""),
            "last_indexed_at": str(row["last_indexed_at"] or ""),
        }
        for row in rows
        if str(row["report_id"] or "").strip()
    }


def report_catalog_index_report_dirs(*, limit: int = 0) -> list[Path]:
    ensure_report_catalog_index()
    safe_limit = max(0, int(limit or 0))
    sql = """
        SELECT report_dir_path
        FROM report_catalog_index
        WHERE report_dir_path != ''
        ORDER BY sort_updated_ts DESC, report_id DESC
    """
    params: list[Any] = []
    if safe_limit:
        sql += " LIMIT ?"
        params.append(safe_limit)
    with _connect() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [Path(str(row["report_dir_path"] or "")) for row in rows if str(row["report_dir_path"] or "").strip()]


def query_report_catalog_index(
    *,
    keyword: str = "",
    dataset_id: str = "",
    business_profile: str = "",
    sort_by: str = "updated_at",
    offset: int = 0,
    limit: int = 80,
) -> dict[str, Any]:
    ensure_report_catalog_index()
    sort_key = "sort_generated_ts" if str(sort_by or "") == "generated_at" else "sort_updated_ts"
    safe_limit = max(1, min(400, int(limit or 80)))
    safe_offset = max(0, int(offset or 0))
    where_parts = ["1=1"]
    params: list[Any] = []
    join_fts = False
    fts_query = _fts_query_for(keyword)
    if fts_query and not _keyword_prefers_like_search(keyword):
        join_fts = True
        where_parts.append("fts.rowid = idx.rowid")
        where_parts.append("report_catalog_fts MATCH ?")
        params.append(fts_query)
    elif str(keyword or "").strip():
        like_term = f"%{str(keyword).strip()}%"
        where_parts.append(
            "(idx.report_id LIKE ? OR idx.title LIKE ? OR idx.content_title LIKE ? OR idx.dataset_name LIKE ? OR idx.business_profile LIKE ?)"
        )
        params.extend([like_term, like_term, like_term, like_term, like_term])
    if str(dataset_id or "").strip():
        where_parts.append("idx.dataset_id = ?")
        params.append(str(dataset_id).strip())
    if str(business_profile or "").strip():
        where_parts.append("idx.business_profile = ?")
        params.append(str(business_profile).strip())

    source = "report_catalog_index AS idx"
    if join_fts:
        source += " JOIN report_catalog_fts AS fts ON fts.rowid = idx.rowid"

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT
            idx.report_id,
            idx.generated_at,
            idx.updated_at,
            idx.title,
            idx.content_title,
            idx.dataset_id,
            idx.dataset_name,
            idx.business_profile,
            idx.preview_url,
            idx.downloadable_count,
            idx.main_downloadable_json,
            idx.preview_downloadable_json,
            idx.latest_revision_session_json
        FROM {source}
        WHERE {where_sql}
        ORDER BY idx.{sort_key} DESC, idx.report_id DESC
        LIMIT ? OFFSET ?
    """
    count_sql = f"SELECT COUNT(*) AS count FROM {source} WHERE {where_sql}"
    with _connect() as connection:
        rows = connection.execute(sql, [*params, safe_limit, safe_offset]).fetchall()
        total = int(connection.execute(count_sql, params).fetchone()["count"])
        dataset_rows = connection.execute(
            "SELECT dataset_id, dataset_name, COUNT(*) AS count FROM report_catalog_index WHERE dataset_id != '' GROUP BY dataset_id, dataset_name ORDER BY count DESC, dataset_name ASC LIMIT 30"
        ).fetchall()
        profile_rows = connection.execute(
            "SELECT business_profile, COUNT(*) AS count FROM report_catalog_index WHERE business_profile != '' GROUP BY business_profile ORDER BY count DESC, business_profile ASC LIMIT 30"
        ).fetchall()

    reports = [
        {
            "report_id": str(row["report_id"] or ""),
            "generated_at": str(row["generated_at"] or ""),
            "updated_at": str(row["updated_at"] or ""),
            "title": str(row["title"] or ""),
            "content_title": str(row["content_title"] or ""),
            "dataset_id": str(row["dataset_id"] or ""),
            "dataset_name": str(row["dataset_name"] or ""),
            "business_profile": str(row["business_profile"] or ""),
            "preview_url": str(row["preview_url"] or ""),
            "downloadable_count": int(row["downloadable_count"] or 0),
            "main_downloadable": _json_loads(str(row["main_downloadable_json"] or "{}"), {}),
            "preview_downloadable": _json_loads(str(row["preview_downloadable_json"] or "{}"), {}),
            "latest_revision_session": _json_loads(str(row["latest_revision_session_json"] or "null"), None),
        }
        for row in rows
    ]
    return {
        "reports": reports,
        "total_count": total,
        "returned_count": len(reports),
        "offset": safe_offset,
        "limit": safe_limit,
        "filters": {
            "keyword": str(keyword or ""),
            "dataset_id": str(dataset_id or ""),
            "business_profile": str(business_profile or ""),
            "sort_by": "generated_at" if sort_key == "sort_generated_ts" else "updated_at",
        },
        "stats": {
            "datasets": [
                {
                    "dataset_id": str(row["dataset_id"] or ""),
                    "dataset_name": str(row["dataset_name"] or ""),
                    "count": int(row["count"] or 0),
                }
                for row in dataset_rows
            ],
            "business_profiles": [
                {
                    "business_profile": str(row["business_profile"] or ""),
                    "count": int(row["count"] or 0),
                }
                for row in profile_rows
            ],
        },
        "index_status": report_catalog_index_status(),
    }
