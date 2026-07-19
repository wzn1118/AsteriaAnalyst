from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from app.services.path_service import BUSINESS_BACKGROUNDS_DIR

SUPPORTED_BACKGROUND_SUFFIXES = {".txt", ".md", ".html", ".htm", ".pdf", ".docx", ".xlsx", ".csv", ".tsv"}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _extract_document_text(path: Path, suffix: str) -> str:
    if suffix in {".txt", ".md"}:
        return _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix in {".html", ".htm"}:
        parser = _HTMLTextExtractor()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        return _clean_text("\n".join(parser.parts))
    if suffix == ".docx":
        from docx import Document

        document = Document(path)
        return _clean_text("\n".join(paragraph.text for paragraph in document.paragraphs))
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return _clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
    raise HTTPException(status_code=400, detail="Unsupported business background document type.")


def _extract_sheet_summary(path: Path, suffix: str) -> str:
    import pandas as pd

    if suffix == ".xlsx":
        workbook = pd.ExcelFile(path)
        parts: list[str] = [f"工作簿包含 {len(workbook.sheet_names)} 个 sheet。"]
        for sheet_name in workbook.sheet_names[:4]:
            frame = pd.read_excel(path, sheet_name=sheet_name)
            columns = ", ".join(frame.columns.astype(str).tolist()[:12])
            sample_rows = frame.head(3).to_dict(orient="records")
            parts.append(f"[{sheet_name}] 列：{columns}")
            parts.append(json.dumps(sample_rows, ensure_ascii=False))
        return _clean_text("\n".join(parts))
    sep = "\t" if suffix == ".tsv" else ","
    frame = pd.read_csv(path, sep=sep)
    parts = [
        f"表格包含 {len(frame)} 行、{len(frame.columns)} 列。",
        f"列：{', '.join(frame.columns.astype(str).tolist()[:20])}",
        json.dumps(frame.head(5).to_dict(orient='records'), ensure_ascii=False),
    ]
    return _clean_text("\n".join(parts))


def _extract_text(path: Path, suffix: str) -> str:
    if suffix in {".xlsx", ".csv", ".tsv"}:
        return _extract_sheet_summary(path, suffix)
    return _extract_document_text(path, suffix)


def _heading_outline(text: str) -> list[str]:
    headings = re.findall(r"^#{1,3}\s+(.+)$", text, flags=re.MULTILINE)
    if headings:
        return headings[:12]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [line for line in lines if len(line) <= 40][:10]


def _payload(context_id: str, filename: str, extracted_text: str, raw_path: Path, suffix: str) -> dict[str, Any]:
    return {
        "context_id": context_id,
        "name": Path(filename).stem,
        "filename": filename,
        "path": str(raw_path.resolve()),
        "source_type": suffix.lstrip("."),
        "char_count": len(extracted_text),
        "preview": extracted_text[:1200],
        "extracted_text": extracted_text,
        "outline": _heading_outline(extracted_text),
        "uploaded_at": _utc_now(),
    }


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "context_id": str(payload.get("context_id") or ""),
        "name": str(payload.get("name") or ""),
        "filename": str(payload.get("filename") or ""),
        "path": str(payload.get("path") or ""),
        "source_type": str(payload.get("source_type") or ""),
        "char_count": int(payload.get("char_count") or 0),
        "preview": str(payload.get("preview") or ""),
        "extracted_text": "",
        "outline": list(payload.get("outline") or []),
        "uploaded_at": str(payload.get("uploaded_at") or ""),
    }


def list_business_backgrounds(*, compact: bool = False) -> list[dict[str, Any]]:
    BUSINESS_BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for metadata_path in BUSINESS_BACKGROUNDS_DIR.glob("*/metadata.json"):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        items.append(_compact_payload(payload) if compact else payload)
    items.sort(key=lambda item: item.get("uploaded_at", ""), reverse=True)
    return items


def load_business_background(context_id: str) -> dict[str, Any]:
    metadata_path = BUSINESS_BACKGROUNDS_DIR / context_id / "metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Business background not found.")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


async def persist_business_background(upload_file: UploadFile) -> dict[str, Any]:
    BUSINESS_BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    filename = Path(upload_file.filename or "business-background").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_BACKGROUND_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Business background upload supports .txt, .md, .html, .pdf, .docx, .xlsx, .csv, and .tsv.",
        )

    context_id = uuid.uuid4().hex[:12]
    context_dir = BUSINESS_BACKGROUNDS_DIR / context_id
    context_dir.mkdir(parents=True, exist_ok=True)

    raw_path = context_dir / f"source{suffix}"
    raw_path.write_bytes(await upload_file.read())
    extracted_text = _extract_text(raw_path, suffix)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No readable business background could be extracted from the uploaded file.")

    payload = _payload(context_id, filename, extracted_text, raw_path, suffix)
    (context_dir / "metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
