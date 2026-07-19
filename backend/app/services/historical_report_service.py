from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from app.services.path_service import HISTORICAL_REPORTS_DIR

SUPPORTED_HISTORY_SUFFIXES = {".txt", ".md", ".html", ".htm", ".pdf", ".docx"}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._parts.append(text)

    def text(self) -> str:
        return "\n".join(self._parts)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _extract_text_from_html(raw_text: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(raw_text)
    return parser.text()


def _extract_text(path: Path, suffix: str) -> str:
    if suffix in {".txt", ".md"}:
        return _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix in {".html", ".htm"}:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        return _clean_text(_extract_text_from_html(raw))
    if suffix == ".docx":
        from docx import Document

        document = Document(path)
        return _clean_text("\n".join(paragraph.text for paragraph in document.paragraphs))
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return _clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
    raise HTTPException(status_code=400, detail="Unsupported historical report file type.")


def _heading_outline(text: str) -> list[str]:
    headings = re.findall(r"^#{1,3}\s+(.+)$", text, flags=re.MULTILINE)
    if headings:
        return headings[:12]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    inferred = [line for line in lines if len(line) <= 24][:8]
    return inferred


def _style_fingerprint(text: str) -> dict[str, Any]:
    return {
        "has_answer_first": any(token in text for token in ["先说结论", "结论先行", "核心判断", "一句话结论"]),
        "has_risk_section": "风险" in text,
        "has_action_section": any(token in text for token in ["动作", "建议", "下一步"]),
        "has_market_section": any(token in text for token in ["市场", "格局", "份额"]),
        "has_driver_section": any(token in text for token in ["驱动", "来源", "原因"]),
        "has_trend_section": any(token in text for token in ["趋势", "变化", "本期变化"]),
    }


def _profile_payload(template_id: str, filename: str, extracted_text: str, raw_path: Path) -> dict[str, Any]:
    return {
        "template_id": template_id,
        "name": Path(filename).stem,
        "filename": filename,
        "path": str(raw_path.resolve()),
        "word_count": len(extracted_text.split()),
        "char_count": len(extracted_text),
        "preview": extracted_text[:800],
        "extracted_text": extracted_text,
        "outline": _heading_outline(extracted_text),
        "style_fingerprint": _style_fingerprint(extracted_text),
        "uploaded_at": _utc_now(),
    }


def _compact_profile(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "template_id": str(payload.get("template_id") or ""),
        "name": str(payload.get("name") or ""),
        "filename": str(payload.get("filename") or ""),
        "path": str(payload.get("path") or ""),
        "word_count": int(payload.get("word_count") or 0),
        "char_count": int(payload.get("char_count") or 0),
        "preview": str(payload.get("preview") or ""),
        "extracted_text": "",
        "outline": list(payload.get("outline") or []),
        "style_fingerprint": dict(payload.get("style_fingerprint") or {}),
        "uploaded_at": str(payload.get("uploaded_at") or ""),
    }


def list_historical_reports(*, compact: bool = False) -> list[dict[str, Any]]:
    HISTORICAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for metadata_path in HISTORICAL_REPORTS_DIR.glob("*/metadata.json"):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        items.append(_compact_profile(payload) if compact else payload)
    items.sort(key=lambda item: item.get("uploaded_at", ""), reverse=True)
    return items


def load_historical_report(template_id: str) -> dict[str, Any]:
    metadata_path = HISTORICAL_REPORTS_DIR / template_id / "metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Historical report template not found.")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


async def persist_historical_report(upload_file: UploadFile) -> dict[str, Any]:
    HISTORICAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = Path(upload_file.filename or "historical-report").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_HISTORY_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Historical report upload supports .txt, .md, .html, .pdf, and .docx.",
        )

    template_id = uuid.uuid4().hex[:12]
    template_dir = HISTORICAL_REPORTS_DIR / template_id
    template_dir.mkdir(parents=True, exist_ok=True)

    raw_path = template_dir / f"source{suffix}"
    raw_path.write_bytes(await upload_file.read())
    extracted_text = _extract_text(raw_path, suffix)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No readable text could be extracted from the uploaded historical report.")

    payload = _profile_payload(template_id, filename, extracted_text, raw_path)
    (template_dir / "metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
