from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.services.codex_service import (
    codex_complete_input_fields,
    codex_generic_chain_judge,
    codex_generic_chain_polish,
    codex_generic_deep_mining,
    codex_generic_pattern_mining,
    codex_generic_structure_mining,
)
from app.services.generic_deep_mining_service import build_generic_deep_mining_context


def _background_understanding_context(
    *,
    dataset_name: str,
    sheet_name: str,
    request: dict[str, Any],
    report: dict[str, Any],
    context_compaction: dict[str, Any],
) -> dict[str, Any]:
    raw_rows = context_compaction.get("raw_rows", {}) or {}
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "business_background_name": request.get("business_background_name", ""),
        "business_background_text": request.get("business_background_text", ""),
        "user_requirement": request.get("user_requirement", ""),
        "problem_to_solve": request.get("problem_to_solve", ""),
        "target_audience": request.get("target_audience", ""),
        "core_purpose": request.get("core_purpose", ""),
        "expected_result": request.get("expected_result", ""),
        "key_constraints": request.get("key_constraints", ""),
        "columns": raw_rows.get("columns", [])[:32],
        "sample_rows": raw_rows.get("sample_rows", [])[:10],
        "report_sections": [
            {
                "id": section.get("id"),
                "title": section.get("title"),
                "summary": section.get("summary"),
            }
            for section in report.get("sections", [])[:16]
        ],
    }


def _generic_structure_context(
    *,
    dataset_name: str,
    sheet_name: str,
    request: dict[str, Any],
    context_compaction: dict[str, Any],
    relation_context: dict[str, Any],
    background_understanding_agent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "request": request,
        "context_compaction": context_compaction,
        "relation_context": relation_context,
        "background_understanding_agent": background_understanding_agent,
    }


def _generic_pattern_context(
    *,
    dataset_name: str,
    sheet_name: str,
    request: dict[str, Any],
    temporal_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    outlier_rows: list[dict[str, Any]],
    relation_context: dict[str, Any],
    context_compaction: dict[str, Any],
    background_understanding_agent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "request": request,
        "temporal_rows": temporal_rows[:12],
        "correlation_rows": correlation_rows[:8],
        "outlier_rows": outlier_rows[:8],
        "relation_context": relation_context,
        "context_compaction": context_compaction,
        "background_understanding_agent": background_understanding_agent,
    }


def _generic_polish_context(
    *,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    report: dict[str, Any],
    background_understanding_agent: dict[str, Any],
    structure_mining_agent: dict[str, Any],
    pattern_mining_agent: dict[str, Any],
    generic_deep_mining_agent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "current_report": {
            "title": report.get("title"),
            "executive_summary": report.get("executive_summary", [])[:6],
            "sections": [
                {
                    "id": section.get("id"),
                    "title": section.get("title"),
                    "summary": section.get("summary"),
                    "bullets": (section.get("bullets") or [])[:4],
                }
                for section in report.get("sections", [])[:20]
            ],
        },
        "background_understanding_agent": background_understanding_agent,
        "structure_agent_layer": structure_mining_agent,
        "pattern_agent_layer": pattern_mining_agent,
        "generic_deep_mining_layer": generic_deep_mining_agent,
    }


def _generic_judge_context(
    *,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    report: dict[str, Any],
    background_understanding_agent: dict[str, Any],
    structure_mining_agent: dict[str, Any],
    pattern_mining_agent: dict[str, Any],
    generic_deep_mining_agent: dict[str, Any],
    polish_agent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "executive_summary": report.get("executive_summary", [])[:6],
        "background_understanding_agent": background_understanding_agent,
        "structure_mining_agent": structure_mining_agent,
        "pattern_mining_agent": pattern_mining_agent,
        "generic_deep_mining_agent": generic_deep_mining_agent,
        "polish_agent": polish_agent,
    }


def run_generic_agent_workflow(
    *,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    request: dict[str, Any],
    report: dict[str, Any],
    primary_category_column: str | None,
    category_rows: list[dict[str, Any]],
    temporal_rows: list[dict[str, Any]],
    correlation_rows: list[dict[str, Any]],
    outlier_rows: list[dict[str, Any]],
    relation_context: dict[str, Any],
    context_compaction: dict[str, Any],
    max_revision_rounds: int = 4,
) -> dict[str, Any]:
    workflow_id = f"generic-agent-chain-{uuid4().hex[:10]}"
    stage_events: list[dict[str, Any]] = []

    def record(agent_id: str, output: dict[str, Any]) -> None:
        stage_events.append(
            {
                "agent_id": agent_id,
                "runtime_state": output.get("runtime_state") or output.get("mode"),
                "headline": output.get("headline")
                or output.get("decision_headline")
                or output.get("brief_rationale")
                or "",
            }
        )

    background_understanding_agent = codex_complete_input_fields(
        _background_understanding_context(
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            request=request,
            report=report,
            context_compaction=context_compaction,
        )
    )
    record("background_understanding_agent", background_understanding_agent)

    structure_mining_agent = codex_generic_structure_mining(
        _generic_structure_context(
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            request=request,
            context_compaction=context_compaction,
            relation_context=relation_context,
            background_understanding_agent=background_understanding_agent,
        )
    )
    record("structure_mining_agent", structure_mining_agent)

    pattern_mining_agent = codex_generic_pattern_mining(
        _generic_pattern_context(
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            request=request,
            temporal_rows=temporal_rows,
            correlation_rows=correlation_rows,
            outlier_rows=outlier_rows,
            relation_context=relation_context,
            context_compaction=context_compaction,
            background_understanding_agent=background_understanding_agent,
        )
    )
    record("pattern_mining_agent", pattern_mining_agent)

    generic_deep_mining_agent = codex_generic_deep_mining(
        build_generic_deep_mining_context(
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            request=request,
            report=report,
            primary_category_column=primary_category_column,
            category_rows=category_rows,
            temporal_rows=temporal_rows,
            correlation_rows=correlation_rows,
            outlier_rows=outlier_rows,
            relation_context=relation_context,
            context_compaction=context_compaction,
            background_understanding=background_understanding_agent,
            structure_agent_layer=structure_mining_agent,
            pattern_agent_layer=pattern_mining_agent,
        )
    )
    record("generic_deep_mining_agent", generic_deep_mining_agent)

    polish_agent = codex_generic_chain_polish(
        _generic_polish_context(
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            report_lens=report_lens,
            report=report,
            background_understanding_agent=background_understanding_agent,
            structure_mining_agent=structure_mining_agent,
            pattern_mining_agent=pattern_mining_agent,
            generic_deep_mining_agent=generic_deep_mining_agent,
        )
    )
    record("polish_agent", polish_agent)

    judge_agent = codex_generic_chain_judge(
        _generic_judge_context(
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            report_lens=report_lens,
            report=report,
            background_understanding_agent=background_understanding_agent,
            structure_mining_agent=structure_mining_agent,
            pattern_mining_agent=pattern_mining_agent,
            generic_deep_mining_agent=generic_deep_mining_agent,
            polish_agent=polish_agent,
        )
    )
    record("judge_agent", judge_agent)

    revision_rounds = 0
    target_score = int(judge_agent.get("target_score") or 90)
    while int(judge_agent.get("total_score") or 0) < target_score and revision_rounds < max_revision_rounds:
        revision_rounds += 1
        route_to = [str(item) for item in (judge_agent.get("route_to") or []) if str(item).strip()]
        if not route_to:
            route_to = ["generic_deep_mining_agent", "polish_agent"]
        if "background_understanding_agent" in route_to:
            background_understanding_agent = codex_complete_input_fields(
                _background_understanding_context(
                    dataset_name=dataset_name,
                    sheet_name=sheet_name,
                    request=request,
                    report=report,
                    context_compaction=context_compaction,
                )
            )
            record("background_understanding_agent_rerun", background_understanding_agent)
        if "structure_mining_agent" in route_to:
            structure_mining_agent = codex_generic_structure_mining(
                _generic_structure_context(
                    dataset_name=dataset_name,
                    sheet_name=sheet_name,
                    request=request,
                    context_compaction=context_compaction,
                    relation_context=relation_context,
                    background_understanding_agent=background_understanding_agent,
                )
            )
            record("structure_mining_agent_rerun", structure_mining_agent)
        if "pattern_mining_agent" in route_to:
            pattern_mining_agent = codex_generic_pattern_mining(
                _generic_pattern_context(
                    dataset_name=dataset_name,
                    sheet_name=sheet_name,
                    request=request,
                    temporal_rows=temporal_rows,
                    correlation_rows=correlation_rows,
                    outlier_rows=outlier_rows,
                    relation_context=relation_context,
                    context_compaction=context_compaction,
                    background_understanding_agent=background_understanding_agent,
                )
            )
            record("pattern_mining_agent_rerun", pattern_mining_agent)
        if "generic_deep_mining_agent" in route_to or "background_understanding_agent" in route_to or "structure_mining_agent" in route_to or "pattern_mining_agent" in route_to:
            generic_deep_mining_agent = codex_generic_deep_mining(
                build_generic_deep_mining_context(
                    dataset_name=dataset_name,
                    sheet_name=sheet_name,
                    request=request,
                    report=report,
                    primary_category_column=primary_category_column,
                    category_rows=category_rows,
                    temporal_rows=temporal_rows,
                    correlation_rows=correlation_rows,
                    outlier_rows=outlier_rows,
                    relation_context=relation_context,
                    context_compaction=context_compaction,
                    background_understanding=background_understanding_agent,
                    structure_agent_layer=structure_mining_agent,
                    pattern_agent_layer=pattern_mining_agent,
                )
            )
            record("generic_deep_mining_agent_rerun", generic_deep_mining_agent)

        polish_agent = codex_generic_chain_polish(
            _generic_polish_context(
                dataset_name=dataset_name,
                sheet_name=sheet_name,
                report_lens=report_lens,
                report=report,
                background_understanding_agent=background_understanding_agent,
                structure_mining_agent=structure_mining_agent,
                pattern_mining_agent=pattern_mining_agent,
                generic_deep_mining_agent=generic_deep_mining_agent,
            )
        )
        record("polish_agent_rerun", polish_agent)

        judge_agent = codex_generic_chain_judge(
            _generic_judge_context(
                dataset_name=dataset_name,
                sheet_name=sheet_name,
                report_lens=report_lens,
                report=report,
                background_understanding_agent=background_understanding_agent,
                structure_mining_agent=structure_mining_agent,
                pattern_mining_agent=pattern_mining_agent,
                generic_deep_mining_agent=generic_deep_mining_agent,
                polish_agent=polish_agent,
            )
        )
        record("judge_agent_rerun", judge_agent)
        target_score = int(judge_agent.get("target_score") or 90)

    return {
        "workflow_id": workflow_id,
        "stage_events": stage_events,
        "background_understanding_agent": background_understanding_agent,
        "structure_mining_agent": structure_mining_agent,
        "pattern_mining_agent": pattern_mining_agent,
        "generic_deep_mining_agent": generic_deep_mining_agent,
        "polish_agent": polish_agent,
        "judge_agent": judge_agent,
        "final_followup_layer": polish_agent,
        "release_ready": int(judge_agent.get("total_score") or 0) >= int(judge_agent.get("target_score") or 90)
        and str(judge_agent.get("verdict") or "").strip().lower() == "pass",
        "revision_rounds": revision_rounds,
    }
