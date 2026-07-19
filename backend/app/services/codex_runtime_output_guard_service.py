from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any


_ALLOWED_ENGLISH_TERMS = {
    "AOV",
    "BCG",
    "CEO",
    "CFO",
    "COO",
    "CAGR",
    "GMV",
    "KPI",
    "PDF",
    "ROI",
    "RFM",
    "SKU",
}

_MOJIBAKE_RE = re.compile(
    r"(?:锟|�|閿|鐨|涓|绋|瀹|姣|杞|澶|鏈|闁|閸|閻|粻|鐘|劕|鍣|"
    r"脙|脗|氓|莽|鍘|彶|鎶|憡|钀|鍛|勬|屽|粡|鏁|嵁|鎻|愭|丠|銆|Ã|Â|â€)"
)

_PLACEHOLDER_RE = re.compile(
    r"(?i)\b("
    r"lorem|ipsum|placeholder|todo|tbd|dummy|sample\s+text|fill\s+in|to\s+be\s+filled|"
    r"insert\s+here|not\s+available|not\s+enough\s+data|fallback|runtime|pipeline|workspace|"
    r"artifact|manifest|http\s*503|n/a"
    r")\b|"
    r"(占位|占位符|待补|待填写|这里展示|这里填写|当前数据包未提供|无法生成|未提供|暂无|无数据|空置|示例文本|样例|演示数据)"
)

_RAW_PATH_RE = re.compile(r"([A-Za-z]:\\|workspace[\\/]|codex[-_]?pipeline|\.json\b|\.csv\b|\.md\b|\.html\b)", re.IGNORECASE)


def extract_visible_text(text: str, *, artifact_type: str = "") -> str:
    raw = str(text or "")
    artifact = artifact_type.lower()
    if artifact == "html" or "<html" in raw.lower() or "<body" in raw.lower():
        raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
        raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def inspect_reader_facing_text(
    text: str,
    *,
    label: str = "artifact",
    artifact_type: str = "",
    min_visible_chars: int = 240,
    min_cjk_ratio: float = 0.18,
) -> dict[str, Any]:
    visible_text = extract_visible_text(text, artifact_type=artifact_type)
    visible_chars = len(re.findall(r"\S", visible_text))
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", visible_text))
    english_words = re.findall(r"\b[A-Za-z]{3,}\b", visible_text)
    disallowed_english = [word for word in english_words if word.upper() not in _ALLOWED_ENGLISH_TERMS]
    mojibake_matches = _MOJIBAKE_RE.findall(visible_text)
    placeholder_matches = _PLACEHOLDER_RE.findall(visible_text)
    raw_path_matches = _RAW_PATH_RE.findall(visible_text)
    question_runs = re.findall(r"\?{2,}", visible_text)
    cjk_ratio = cjk_chars / max(1, visible_chars)
    disallowed_english_ratio = len("".join(disallowed_english)) / max(1, visible_chars)
    issues: list[str] = []
    if visible_chars < min_visible_chars:
        issues.append("reader_facing_text_too_short")
    if cjk_ratio < min_cjk_ratio:
        issues.append("reader_facing_cjk_ratio_too_low")
    if mojibake_matches:
        issues.append("reader_facing_mojibake_detected")
    if placeholder_matches:
        issues.append("reader_facing_placeholder_or_filler_detected")
    if raw_path_matches:
        issues.append("reader_facing_internal_path_or_artifact_name_detected")
    if question_runs:
        issues.append("reader_facing_question_mark_runs_detected")
    if disallowed_english_ratio > 0.08:
        issues.append("reader_facing_english_leakage_detected")
    return {
        "label": label,
        "ok": not issues,
        "issues": issues,
        "visible_char_count": visible_chars,
        "cjk_char_count": cjk_chars,
        "cjk_ratio": round(cjk_ratio, 4),
        "english_word_count": len(english_words),
        "disallowed_english_word_count": len(disallowed_english),
        "disallowed_english_ratio": round(disallowed_english_ratio, 4),
        "mojibake_count": len(mojibake_matches),
        "placeholder_count": len(placeholder_matches),
        "internal_path_reference_count": len(raw_path_matches),
        "question_run_count": len(question_runs),
        "sample_disallowed_english": disallowed_english[:20],
    }


def validate_reader_facing_artifact(
    path: Path,
    *,
    label: str = "",
    artifact_type: str = "",
    min_visible_chars: int = 240,
    min_cjk_ratio: float = 0.18,
) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception as exc:
        return {
            "label": label or path.name,
            "ok": False,
            "issues": ["reader_facing_artifact_unreadable"],
            "error": str(exc),
            "visible_char_count": 0,
        }
    payload = inspect_reader_facing_text(
        text,
        label=label or path.name,
        artifact_type=artifact_type or path.suffix.lstrip("."),
        min_visible_chars=min_visible_chars,
        min_cjk_ratio=min_cjk_ratio,
    )
    payload["path"] = str(path)
    return payload


def assert_clean_reader_facing_artifacts(
    artifacts: list[tuple[Path, str, str]],
    *,
    stage_id: str,
    min_visible_chars: int = 240,
    min_cjk_ratio: float = 0.18,
) -> dict[str, Any]:
    diagnostics = [
        validate_reader_facing_artifact(
            path,
            label=label,
            artifact_type=artifact_type,
            min_visible_chars=min_visible_chars,
            min_cjk_ratio=min_cjk_ratio,
        )
        for path, label, artifact_type in artifacts
    ]
    failed = [item for item in diagnostics if not item.get("ok")]
    if failed:
        compact = [
            {
                "label": item.get("label"),
                "issues": item.get("issues"),
                "mojibake_count": item.get("mojibake_count"),
                "placeholder_count": item.get("placeholder_count"),
                "visible_char_count": item.get("visible_char_count"),
                "cjk_ratio": item.get("cjk_ratio"),
            }
            for item in failed
        ]
        raise ValueError(f"{stage_id} reader-facing quality gate failed: {compact}")
    return {"ok": True, "artifacts": diagnostics}
