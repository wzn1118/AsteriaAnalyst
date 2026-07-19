from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


# Clean UTF-8 Chinese markers are required for real Chinese PDFs. The legacy
# mojibake-tolerant patterns below stay in place for older artifacts, while
# these patterns make the logic parser understand normal extracted text.
_CJK_ACTION_RE = re.compile(
    r"(?:建议|应当|应该|需要|必须|优先|聚焦|改善|提升|降低|扩大|保护|修复|执行|落地|推动|优化|配置|投入|压降|复盘)"
)
_CJK_CAUSE_RE = re.compile(
    r"(?:因为|由于|因此|所以|导致|带来|驱动|源于|归因于|反映出|说明|意味着|来自|受到.+影响)"
)
_CJK_CONTRAST_RE = re.compile(
    r"(?:但是|但|然而|相较|相比|对比|比较|高于|低于|领先|落后|分化|差异|尽管|反而| versus | vs\.?)",
    re.I,
)
_CJK_ANSWER_FIRST_RE = re.compile(
    r"(?:核心|关键|主要|显著|领先|落后|增长|下降|承压|机会|风险|分化|不均衡|优先|结论|发现|判断|启示)"
)
_CJK_QUESTION_RE = re.compile(r"(?:什么|为什么|如何|哪里|哪些|是否|能否|该不该|怎么)")

_LOGIC_ARC_SEQUENCE = [
    "opening_thesis",
    "business_question",
    "diagnostic_evidence",
    "driver_explanation",
    "contrast_or_segmentation",
    "management_implication",
    "recommendation",
    "appendix_support",
]


_EXHIBIT_RE = re.compile(r"\b(?:exhibit|figure|fig\.?)\s*([0-9]+[a-z]?)\b", re.I)
_SOURCE_RE = re.compile(r"\b(?:source|sources|note|notes|copyright)\s*[:：]", re.I)
_ACTION_RE = re.compile(
    r"\b(?:should|must|need(?:s)? to|recommend|prioriti[sz]e|focus|shift|build|protect|improve|capture|reduce|increase)\b|"
    r"(?:建议|应当|应该|需要|必须|优先|聚焦|改善|提升|降低|扩大|保护|修复)"
)
_CAUSE_RE = re.compile(
    r"\b(?:because|therefore|thus|driven by|due to|as a result|lead(?:s)? to|so that)\b|"
    r"(?:因为|由于|因此|所以|导致|带来|驱动|源于)"
)
_CONTRAST_RE = re.compile(
    r"\b(?:however|but|while|whereas|although|despite|compared|versus|vs\.?)\b|"
    r"(?:但是|但|然而|相比|对比|相较|尽管|反而)"
)
_ANSWER_FIRST_RE = re.compile(
    r"\b(?:significant|uneven|strong|weak|faster|slower|decline|growth|recovery|pressure|opportunity|risk|key)\b|"
    r"(?:显著|关键|核心|主要|领先|落后|增长|下降|承压|机会|风险|分化|不均衡|优先)"
)
_QUESTION_RE = re.compile(r"[?？]|(?:what|why|how|where|which)\b|(?:什么|为什么|如何|哪里|哪些)")


def _read_pdf_pages(path: Path) -> list[str]:
    if path.suffix.lower() != ".pdf" or not path.exists():
        return []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages[:80]:
            try:
                pages.append(str(page.extract_text() or ""))
            except Exception:
                pages.append("")
        return pages
    except Exception:
        return []


def _clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", str(line or "")).strip()
    line = line.strip("-•·\u2022 ")
    return line


def _split_pages(*, source_path: Path, historical_text: str) -> list[dict[str, Any]]:
    pdf_pages = _read_pdf_pages(source_path)
    if any(page.strip() for page in pdf_pages):
        return [
            {
                "page": index,
                "text": text,
                "source": "pdf_page_text",
            }
            for index, text in enumerate(pdf_pages, start=1)
        ]
    text = str(historical_text or "")
    if not text.strip() and source_path.exists() and source_path.suffix.lower() in {".txt", ".md"}:
        try:
            text = source_path.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception:
            text = ""
    chunks = re.split(r"\n\s*(?:-{3,}|={3,}|Page\s+\d+|第\s*\d+\s*页)\s*\n", text)
    chunks = [chunk for chunk in chunks if chunk.strip()]
    if not chunks and text.strip():
        chunks = [text]
    return [
        {
            "page": index,
            "text": chunk,
            "source": "plain_text_chunk",
        }
        for index, chunk in enumerate(chunks[:80], start=1)
    ]


def _line_role(line: str, *, line_index: int) -> str:
    if _SOURCE_RE.search(line):
        return "source_or_note"
    if _EXHIBIT_RE.search(line):
        return "exhibit_reference_or_title"
    if _ACTION_RE.search(line) or _CJK_ACTION_RE.search(line):
        return "action_or_recommendation"
    if _CAUSE_RE.search(line) or _CJK_CAUSE_RE.search(line):
        return "causal_explanation"
    if _CONTRAST_RE.search(line) or _CJK_CONTRAST_RE.search(line):
        return "contrast_or_comparison"
    if line_index <= 2 and len(line) >= 24:
        return "headline_or_section_title"
    if _QUESTION_RE.search(line) or _CJK_QUESTION_RE.search(line):
        return "question_frame"
    return "body_reasoning"


def _headline_score(line: str) -> float:
    visible = len(re.findall(r"\S", line))
    if visible <= 0:
        return 0.0
    score = 0.0
    if _ANSWER_FIRST_RE.search(line) or _CJK_ANSWER_FIRST_RE.search(line):
        score += 0.45
    if _CAUSE_RE.search(line) or _CONTRAST_RE.search(line) or _CJK_CAUSE_RE.search(line) or _CJK_CONTRAST_RE.search(line):
        score += 0.25
    if 28 <= visible <= 140:
        score += 0.2
    if _QUESTION_RE.search(line) or _CJK_QUESTION_RE.search(line):
        score -= 0.15
    return max(0.0, min(1.0, score))


def _infer_page_logic_role(page_logic: dict[str, Any], *, page_index: int, page_count: int) -> str:
    role_counts = Counter(dict(page_logic.get("role_counts") or {}))
    title_score = float((dict(page_logic.get("primary_title") or {})).get("answer_first_score") or 0)
    if page_index == 1:
        return "opening_thesis"
    if page_index >= max(1, page_count - 1) and (
        role_counts.get("source_or_note", 0) >= 1 or role_counts.get("exhibit_reference_or_title", 0) >= 1
    ):
        return "appendix_support"
    if role_counts.get("action_or_recommendation", 0) >= 2:
        return "recommendation"
    if role_counts.get("question_frame", 0) >= 1 and page_index <= max(3, page_count // 3):
        return "business_question"
    if role_counts.get("contrast_or_comparison", 0) >= max(1, role_counts.get("causal_explanation", 0)):
        return "contrast_or_segmentation"
    if role_counts.get("causal_explanation", 0) >= 1:
        return "driver_explanation"
    if role_counts.get("exhibit_reference_or_title", 0) >= 1 or title_score >= 0.45:
        return "diagnostic_evidence"
    if page_index >= max(2, int(page_count * 0.7)):
        return "management_implication"
    return "diagnostic_evidence"


def _transition_rule(previous_role: str, current_role: str) -> str:
    if not previous_role:
        return "open_argument"
    if previous_role == "opening_thesis" and current_role in {"business_question", "diagnostic_evidence"}:
        return "thesis_to_question_or_evidence"
    if previous_role in {"business_question", "diagnostic_evidence"} and current_role in {"driver_explanation", "contrast_or_segmentation"}:
        return "evidence_to_driver_or_contrast"
    if previous_role in {"driver_explanation", "contrast_or_segmentation"} and current_role in {"management_implication", "recommendation"}:
        return "diagnosis_to_implication"
    if current_role == "recommendation":
        return "implication_to_action"
    if current_role == "appendix_support":
        return "main_story_to_supporting_detail"
    return f"{previous_role}_to_{current_role}"


def _build_claim_evidence_action_chain(page_logic: dict[str, Any]) -> dict[str, Any]:
    title = dict(page_logic.get("primary_title") or {})
    role_counts = dict(page_logic.get("role_counts") or {})
    evidence_markers: list[str] = []
    evidence_markers.extend([f"exhibit:{item}" for item in list(page_logic.get("exhibit_ids") or [])[:4]])
    evidence_markers.extend(list(page_logic.get("source_lines") or [])[:2])
    claim = str(title.get("text") or "").strip()
    actions = [str(item).strip() for item in list(page_logic.get("action_lines") or []) if str(item).strip()]
    causal = [str(item).strip() for item in list(page_logic.get("causal_lines") or []) if str(item).strip()]
    contrast = [str(item).strip() for item in list(page_logic.get("contrast_lines") or []) if str(item).strip()]
    return {
        "claim": claim[:260],
        "evidence_markers": evidence_markers[:6],
        "reasoning_markers": (causal + contrast)[:6],
        "action_or_implication": actions[:4],
        "has_claim": bool(claim),
        "has_evidence": bool(evidence_markers or role_counts.get("exhibit_reference_or_title") or role_counts.get("source_or_note")),
        "has_reasoning": bool(causal or contrast),
        "has_action": bool(actions),
    }


def _assign_logic_roles(page_logic: list[dict[str, Any]]) -> None:
    page_count = len(page_logic)
    previous_role = ""
    for index, page in enumerate(page_logic, start=1):
        role = _infer_page_logic_role(page, page_index=index, page_count=page_count)
        page["page_logic_role"] = role
        page["logic_role"] = role
        page["argument_step"] = role
        page["claim_evidence_action_chain"] = _build_claim_evidence_action_chain(page)
        page["transition_from_previous"] = _transition_rule(previous_role, role) if previous_role else "open_argument"
        previous_role = role


def _recommended_argument_arc(pattern: str) -> list[str]:
    if pattern == "answer_first_exhibit_led_argument":
        return [
            "opening_thesis",
            "diagnostic_evidence",
            "contrast_or_segmentation",
            "driver_explanation",
            "management_implication",
            "recommendation",
            "appendix_support",
        ]
    if pattern == "recommendation_led_management_memo":
        return [
            "opening_thesis",
            "recommendation",
            "diagnostic_evidence",
            "driver_explanation",
            "management_implication",
            "appendix_support",
        ]
    if pattern == "comparison_led_diagnosis":
        return [
            "opening_thesis",
            "business_question",
            "contrast_or_segmentation",
            "driver_explanation",
            "management_implication",
            "recommendation",
            "appendix_support",
        ]
    if pattern == "causal_diagnostic_narrative":
        return [
            "opening_thesis",
            "business_question",
            "diagnostic_evidence",
            "driver_explanation",
            "management_implication",
            "recommendation",
            "appendix_support",
        ]
    return [
        "opening_thesis",
        "business_question",
        "diagnostic_evidence",
        "management_implication",
        "recommendation",
        "appendix_support",
    ]


def _page_transition_rules(page_logic: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    for page in page_logic:
        rule = str(page.get("transition_from_previous") or "").strip()
        if not rule or rule == "open_argument":
            continue
        transitions.append(
            {
                "page": page.get("page"),
                "transition": rule,
                "target_role": page.get("page_logic_role"),
            }
        )
    return transitions[:30]


def _logic_flow_contract(
    *,
    pattern: str,
    page_logic: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    role_counts = Counter(str(page.get("page_logic_role") or "") for page in page_logic if page.get("page_logic_role"))
    chain_pages = [
        page
        for page in page_logic
        if isinstance(page.get("claim_evidence_action_chain"), dict)
        and (
            (page["claim_evidence_action_chain"].get("has_claim") and page["claim_evidence_action_chain"].get("has_evidence"))
            or page["claim_evidence_action_chain"].get("has_action")
        )
    ]
    present_arc = [role for role in _LOGIC_ARC_SEQUENCE if role_counts.get(role, 0) > 0]
    return {
        "dominant_logic_pattern": pattern,
        "title_chain_mode": "answer_first" if float(metrics.get("answer_first_title_likelihood") or 0) >= 0.35 else "section_descriptive",
        "argument_arc": present_arc or ["opening_thesis", "diagnostic_evidence", "management_implication"],
        "recommended_argument_arc": _recommended_argument_arc(pattern),
        "page_logic_role_counts": dict(role_counts),
        "claim_evidence_action_page_count": len(chain_pages),
        "claim_evidence_action_density": round(len(chain_pages) / max(1, len(page_logic)), 4),
        "transition_rules": _page_transition_rules(page_logic),
        "page_logic_role_contract": [
            {
                "role": "opening_thesis",
                "purpose": "Set the executive answer and explain what decision the report supports.",
            },
            {
                "role": "diagnostic_evidence",
                "purpose": "Use one major exhibit or table to prove one management claim.",
            },
            {
                "role": "driver_explanation",
                "purpose": "Explain why the signal happens and which drivers matter.",
            },
            {
                "role": "contrast_or_segmentation",
                "purpose": "Compare segments, channels, products, or periods to locate where the issue concentrates.",
            },
            {
                "role": "management_implication",
                "purpose": "Translate the diagnosis into management meaning before jumping to actions.",
            },
            {
                "role": "recommendation",
                "purpose": "Close the argument with concrete actions, owners, sequencing, and metric follow-up.",
            },
            {
                "role": "appendix_support",
                "purpose": "Carry detail tables, definitions, methodology, and source notes without interrupting the main argument.",
            },
        ],
    }


def _question_tree_seed(page_logic: list[dict[str, Any]]) -> dict[str, Any]:
    questions: list[dict[str, Any]] = []
    for page in page_logic:
        for item in list(page.get("logic_move_sequence") or []):
            if item == "question_frame":
                title = dict(page.get("primary_title") or {})
                questions.append(
                    {
                        "page": page.get("page"),
                        "question_or_frame": str(title.get("text") or "business question"),
                        "linked_role": page.get("page_logic_role"),
                    }
                )
                break
    if not questions:
        for page in page_logic[:5]:
            title = dict(page.get("primary_title") or {})
            if title:
                questions.append(
                    {
                        "page": page.get("page"),
                        "question_or_frame": str(title.get("text") or ""),
                        "linked_role": page.get("page_logic_role"),
                    }
                )
    return {
        "root_question": "What management decision should the adapted report support?",
        "branches": questions[:10],
    }


def _page_logic(page: dict[str, Any]) -> dict[str, Any]:
    raw_lines = [_clean_line(line) for line in str(page.get("text") or "").splitlines()]
    lines = [line for line in raw_lines if line]
    role_counts: Counter[str] = Counter()
    exhibit_ids: list[str] = []
    action_lines: list[str] = []
    causal_lines: list[str] = []
    contrast_lines: list[str] = []
    source_lines: list[str] = []
    title_candidates: list[dict[str, Any]] = []
    for index, line in enumerate(lines[:120]):
        role = _line_role(line, line_index=index)
        role_counts[role] += 1
        for match in _EXHIBIT_RE.finditer(line):
            exhibit_ids.append(match.group(1))
        if role == "action_or_recommendation":
            action_lines.append(line)
        elif role == "causal_explanation":
            causal_lines.append(line)
        elif role == "contrast_or_comparison":
            contrast_lines.append(line)
        elif role == "source_or_note":
            source_lines.append(line)
        if index <= 8 and len(line) >= 18:
            title_candidates.append(
                {
                    "line_index": index,
                    "text": line[:260],
                    "answer_first_score": round(_headline_score(line), 4),
                }
            )
    title_candidates.sort(key=lambda item: (float(item.get("answer_first_score") or 0), -int(item.get("line_index") or 0)), reverse=True)
    primary_title = title_candidates[0] if title_candidates else {}
    return {
        "page": int(page.get("page") or 0),
        "line_count": len(lines),
        "char_count": len(str(page.get("text") or "")),
        "primary_title": primary_title,
        "title_candidates": title_candidates[:4],
        "role_counts": dict(role_counts),
        "exhibit_ids": exhibit_ids[:12],
        "action_lines": action_lines[:5],
        "causal_lines": causal_lines[:5],
        "contrast_lines": contrast_lines[:5],
        "source_lines": source_lines[:5],
        "logic_move_sequence": [
            _line_role(line, line_index=index)
            for index, line in enumerate(lines[:30])
            if _line_role(line, line_index=index) != "body_reasoning"
        ][:14],
    }


def _dominant_logic_pattern(
    *,
    page_count: int,
    role_counts: Counter[str],
    exhibit_ref_count: int,
    answer_first_avg: float,
) -> str:
    if exhibit_ref_count >= max(2, page_count // 2) and answer_first_avg >= 0.35:
        return "answer_first_exhibit_led_argument"
    if role_counts.get("action_or_recommendation", 0) >= max(2, page_count):
        return "recommendation_led_management_memo"
    if role_counts.get("contrast_or_comparison", 0) >= role_counts.get("causal_explanation", 0):
        return "comparison_led_diagnosis"
    if role_counts.get("causal_explanation", 0) >= 2:
        return "causal_diagnostic_narrative"
    return "descriptive_structured_report"


def build_historical_logic_reference_payload(
    *,
    source_path: Path,
    historical_text: str = "",
) -> dict[str, Any]:
    pages = _split_pages(source_path=source_path, historical_text=historical_text)
    page_logic = [_page_logic(page) for page in pages]
    _assign_logic_roles(page_logic)
    role_counts: Counter[str] = Counter()
    exhibit_ids: list[str] = []
    title_chain: list[dict[str, Any]] = []
    action_samples: list[str] = []
    causal_samples: list[str] = []
    contrast_samples: list[str] = []
    source_samples: list[str] = []
    for page in page_logic:
        role_counts.update(dict(page.get("role_counts") or {}))
        exhibit_ids.extend(str(item) for item in list(page.get("exhibit_ids") or []) if str(item).strip())
        primary = dict(page.get("primary_title") or {})
        if primary:
            title_chain.append(
                {
                    "page": page.get("page"),
                    "title": primary.get("text"),
                    "answer_first_score": primary.get("answer_first_score"),
                }
            )
        action_samples.extend(list(page.get("action_lines") or [])[:2])
        causal_samples.extend(list(page.get("causal_lines") or [])[:2])
        contrast_samples.extend(list(page.get("contrast_lines") or [])[:2])
        source_samples.extend(list(page.get("source_lines") or [])[:2])

    page_count = len(page_logic)
    line_total = sum(int(page.get("line_count") or 0) for page in page_logic)
    answer_scores = [
        float((dict(page.get("primary_title") or {})).get("answer_first_score") or 0)
        for page in page_logic
        if page.get("primary_title")
    ]
    answer_first_avg = sum(answer_scores) / max(1, len(answer_scores))
    exhibit_counter = Counter(exhibit_ids)
    exhibit_inventory = [
        {"exhibit_id": exhibit_id, "mention_count": count}
        for exhibit_id, count in exhibit_counter.most_common(40)
    ]
    pattern = _dominant_logic_pattern(
        page_count=page_count,
        role_counts=role_counts,
        exhibit_ref_count=len(exhibit_ids),
        answer_first_avg=answer_first_avg,
    )
    metrics = {
        "page_count": page_count,
        "line_count": line_total,
        "answer_first_title_likelihood": round(answer_first_avg, 4),
        "exhibit_reference_density": round(len(exhibit_ids) / max(1, page_count), 4),
        "action_density": round(role_counts.get("action_or_recommendation", 0) / max(1, line_total), 4),
        "causal_density": round(role_counts.get("causal_explanation", 0) / max(1, line_total), 4),
        "contrast_density": round(role_counts.get("contrast_or_comparison", 0) / max(1, line_total), 4),
        "source_note_density": round(role_counts.get("source_or_note", 0) / max(1, line_total), 4),
    }
    return {
        "version": "historical-logic-reference-v1",
        "source_name": source_path.name,
        "source_path": str(source_path.resolve()) if source_path.exists() else str(source_path),
        "source_suffix": source_path.suffix.lower(),
        "available": bool(page_logic),
        "dominant_logic_pattern": pattern,
        "logic_metrics": metrics,
        "logic_flow_contract": _logic_flow_contract(
            pattern=pattern,
            page_logic=page_logic,
            metrics=metrics,
        ),
        "argument_arc": _recommended_argument_arc(pattern),
        "page_transition_rules": _page_transition_rules(page_logic),
        "question_tree_seed": _question_tree_seed(page_logic),
        "role_counts": dict(role_counts),
        "title_chain": title_chain[:30],
        "exhibit_inventory": exhibit_inventory,
        "page_logic": page_logic[:40],
        "claim_evidence_action_chains": [
            {
                "page": page.get("page"),
                "page_logic_role": page.get("page_logic_role"),
                **dict(page.get("claim_evidence_action_chain") or {}),
            }
            for page in page_logic[:40]
        ],
        "logic_samples": {
            "action_or_recommendation": action_samples[:12],
            "causal_explanation": causal_samples[:12],
            "contrast_or_comparison": contrast_samples[:12],
            "source_or_note": source_samples[:12],
        },
        "logic_rules_for_adaptation": [
            "Preserve the dominant argument pattern, but replace all historical facts and numbers with current-data evidence.",
            "Use answer-first page titles when the source title chain is answer-first.",
            "When the source is exhibit-led, each major page should connect one conclusion to one data exhibit and one management implication.",
            "Preserve source/note cadence and exhibit cross-reference rhythm when detected.",
            "Keep recommendations tied to current metrics, segments, and action candidates instead of generic advice.",
        ],
        "must_preserve_logic": [
            pattern,
            "title_chain_progression",
            "exhibit_to_claim_linkage" if exhibit_ids else "section_to_claim_linkage",
            "source_note_cadence" if role_counts.get("source_or_note", 0) else "evidence_citation_cadence",
        ],
        "must_avoid_logic": [
            "copying historical conclusions",
            "copying historical numeric values",
            "using visuals without a page-level management claim",
            "turning the deck into an unstructured long essay",
        ],
    }


def write_historical_logic_reference(
    *,
    source_path: Path,
    historical_text: str,
    output_path: Path,
    markdown_output_path: Path | None = None,
) -> dict[str, Any]:
    payload = build_historical_logic_reference_payload(
        source_path=source_path,
        historical_text=historical_text,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if markdown_output_path is not None:
        lines = [
            "# Historical Logic Reference",
            "",
            f"- Source: `{payload.get('source_name')}`",
            f"- Dominant logic pattern: `{payload.get('dominant_logic_pattern')}`",
            f"- Answer-first likelihood: `{(payload.get('logic_metrics') or {}).get('answer_first_title_likelihood')}`",
            f"- Exhibit reference density: `{(payload.get('logic_metrics') or {}).get('exhibit_reference_density')}`",
            f"- Recommended argument arc: `{', '.join(list(payload.get('argument_arc') or []))}`",
            "",
            "## Title Chain",
        ]
        for item in list(payload.get("title_chain") or [])[:12]:
            lines.append(f"- Page {item.get('page')}: {item.get('title')}")
        lines.extend(["", "## Adaptation Rules"])
        for item in list(payload.get("logic_rules_for_adaptation") or []):
            lines.append(f"- {item}")
        lines.extend(["", "## Page Logic Roles"])
        for item in list(payload.get("page_logic") or [])[:16]:
            lines.append(
                f"- Page {item.get('page')}: {item.get('page_logic_role')} / {item.get('transition_from_previous')}"
            )
        markdown_output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return payload
