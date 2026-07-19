from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import SmartReportRequest
from app.services.ai_mandatory import (
    execute_metric_plan,
    map_fields_with_ai,
    plan_metrics_with_ai,
    route_business_context_with_ai,
    validate_ai_mandatory_artifacts,
    write_ai_usage_gate_trace,
)
from app.services.ai_mandatory.schemas import AIBusinessRoutingResult
from app.services.analysis_program_service import build_analysis_program
from app.services.business_profile_router import (
    business_profile_entrypoint,
    business_profile_report_lens,
    route_business_profile,
)
from app.services.codex_service import codex_statistical_scope
from app.services.dataset_service import (
    build_column_summaries,
    categorical_columns,
    datetime_columns,
    load_all_sheet_frames,
    load_dataset_frame,
    load_dataset_metadata,
    numeric_columns,
)
from app.services.job_graph_service import JobNode, execute_job_graph
from app.services.market_intelligence_service import build_market_intelligence
from app.services.path_service import REPORTS_DIR
from app.services.workflow_service import build_workflow_blueprint


def _step(
    step_id: str,
    title: str,
    status: str,
    detail: str,
    *,
    output: str = "",
    category: str = "engineering",
) -> dict[str, Any]:
    return {
        "id": step_id,
        "title": title,
        "status": status,
        "detail": detail,
        "output": output,
        "category": category,
    }


def _honor_explicit_business_profile(router_result: dict[str, Any], request: SmartReportRequest) -> dict[str, Any]:
    requested = str(getattr(request, "business_profile", "") or "").strip()
    if not requested or requested == "auto":
        return router_result
    return {
        **(router_result or {}),
        "business_profile": requested,
        "profile_entrypoint": business_profile_entrypoint(requested),
        "report_lens": business_profile_report_lens(requested),
        "routing_reason": f"Explicit business_profile requested by user: {requested}",
    }


def _resolve_multi_sheet_names(metadata: dict[str, Any], request: SmartReportRequest) -> list[str]:
    available = [str(item["name"]) for item in metadata.get("sheets", [])]
    selected = [name for name in request.selected_sheets if name in available]
    if selected:
        return selected
    if request.sheet_name and request.sheet_name in available:
        return [request.sheet_name]
    if metadata.get("active_sheet") in available:
        return [str(metadata["active_sheet"])]
    return available[:1]


def _selected_sheet_frames(
    dataset_id: str,
    metadata: dict[str, Any],
    selected_sheet_names: list[str],
) -> list[tuple[dict[str, Any], pd.DataFrame]]:
    _, all_frames = load_all_sheet_frames(dataset_id)
    selected = set(selected_sheet_names)
    return [(sheet, frame.copy()) for sheet, frame in all_frames if str(sheet["name"]) in selected]


def _merge_selected_sheet_frames(
    metadata: dict[str, Any],
    sheet_frames: list[tuple[dict[str, Any], pd.DataFrame]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged_parts: list[pd.DataFrame] = []
    for sheet, frame in sheet_frames:
        working = frame.copy()
        working["来源工作表"] = str(sheet["name"])
        merged_parts.append(working)
    merged = pd.concat(merged_parts, ignore_index=True, sort=False) if merged_parts else pd.DataFrame()
    synthetic_sheet = {
        "name": f"合并分析({'+'.join(str(sheet['name']) for sheet, _ in sheet_frames)})",
        "storage_file": "",
        "rows": int(len(merged)),
        "columns": int(len(merged.columns)),
    }
    return merged, synthetic_sheet


def _resolved_request_from_program(request: SmartReportRequest, program_bundle: dict[str, Any]) -> SmartReportRequest:
    payload = dict(request.model_dump())
    resolved = program_bundle.get("resolved_request_payload") or {}
    for key, value in resolved.items():
        if key in payload and not str(payload.get(key) or "").strip() and str(value or "").strip():
            payload[key] = value
    return SmartReportRequest(**payload)


def _ai_trace_output_dir(ai_trace_output_dir: str | Path | None) -> Path:
    if ai_trace_output_dir:
        path = Path(ai_trace_output_dir)
    else:
        path = REPORTS_DIR / "_ai_router_tmp" / f"orchestration-{uuid.uuid4().hex[:12]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _field_semantic_mapper_inputs(frame: pd.DataFrame) -> dict[str, Any]:
    summaries = build_column_summaries(frame)
    inferred_data_types = {str(item["name"]): str(item.get("dtype") or "") for item in summaries}
    sample_values = {str(item["name"]): list(item.get("sample_values") or []) for item in summaries}
    missing_rate = {str(item["name"]): float(item.get("missing_ratio") or 0.0) for item in summaries}
    unique_count = {str(item["name"]): int(item.get("unique_count") or 0) for item in summaries}
    numeric_distribution = {
        str(item["name"]): dict(item.get("stats") or {})
        for item in summaries
        if isinstance(item.get("stats"), dict) and any(key in item["stats"] for key in ["mean", "std", "min", "max"])
    }
    top_values = {
        str(item["name"]): list((item.get("stats") or {}).get("top_values") or [])
        for item in summaries
        if isinstance(item.get("stats"), dict) and "top_values" in item["stats"]
    }
    date_parse_rate: dict[str, float] = {}
    for column in frame.columns.astype(str):
        series = pd.to_datetime(frame[column], errors="coerce")
        date_parse_rate[column] = float(series.notna().mean()) if len(series) else 0.0
    return {
        "dataframe_profile": {
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "column_summaries": summaries,
        },
        "field_names": frame.columns.astype(str).tolist(),
        "inferred_data_types": inferred_data_types,
        "sample_values": sample_values,
        "missing_rate": missing_rate,
        "unique_count": unique_count,
        "numeric_distribution": numeric_distribution,
        "top_values": top_values,
        "date_parse_rate": date_parse_rate,
    }


def _ai_quality_dir(output_dir: Path) -> Path:
    path = output_dir / "outputs" / "quality"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_ai_usage_gate_result(output_dir: Path, payload: dict[str, Any]) -> str:
    quality_path = _ai_quality_dir(output_dir) / "ai_usage_gate_result.json"
    quality_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_ai_usage_gate_trace(output_dir, payload)
    return str(quality_path.resolve())


def _normalize_failure_code(exc: Exception) -> str:
    if exc.__class__.__name__ == "AIRequiredButUnavailableError":
        return "AI_REQUIRED_BUT_UNAVAILABLE"
    return exc.__class__.__name__ or "AI_MANDATORY_FAILED"


def _run_ai_mandatory_chain(
    *,
    frame: pd.DataFrame,
    dataset_name: str,
    sheet_name: str,
    request: SmartReportRequest,
    request_text: str,
    trace_output_dir: Path,
) -> dict[str, Any]:
    semantic_inputs = _field_semantic_mapper_inputs(frame)
    dataframe_profile = dict(semantic_inputs["dataframe_profile"])
    date_parse_rate = semantic_inputs.get("date_parse_rate") or {}
    time_points = [
        column
        for column, ratio in date_parse_rate.items()
        if float(ratio or 0.0) >= 0.7
    ]
    if time_points:
        time_col = time_points[0]
        parsed = pd.to_datetime(frame[time_col], errors="coerce").dropna()
        if not parsed.empty:
            dataframe_profile["time_profile"] = {
                "time_column": time_col,
                "distinct_time_points": int(parsed.dt.normalize().nunique()),
                "window_days": float((parsed.max() - parsed.min()).days) if len(parsed) > 1 else 0.0,
            }

    result: dict[str, Any] = {
        "passed": False,
        "formal_pdf_allowed": False,
        "failure_code": "",
        "failure_reason": "",
        "data_profile": dataframe_profile,
        "semantic_mapping_result": {},
        "routing_result": {},
        "metric_plan": {},
        "semantic_metric_result": {},
        "metric_derivation_log_path": "",
        "ai_usage_gate_result": {},
        "quality_gate_path": "",
        "trace_output_dir": str(trace_output_dir.resolve()),
    }

    try:
        semantic_mapping_result = map_fields_with_ai(
            output_dir=trace_output_dir,
            dataframe_profile=dataframe_profile,
            file_name=dataset_name,
            sheet_name=sheet_name,
            user_task_description=request_text,
            field_names=semantic_inputs["field_names"],
            inferred_data_types=semantic_inputs["inferred_data_types"],
            sample_values=semantic_inputs["sample_values"],
            missing_rate=semantic_inputs["missing_rate"],
            unique_count=semantic_inputs["unique_count"],
            numeric_distribution=semantic_inputs["numeric_distribution"],
            top_values=semantic_inputs["top_values"],
            date_parse_rate=semantic_inputs["date_parse_rate"],
        )
        deterministic_router_result = route_business_profile(
            frame,
            dataset_name=dataset_name,
            request_text=request_text,
            requested_business_profile=request.business_profile,
        )
        ai_routing_result = route_business_context_with_ai(
            output_dir=trace_output_dir,
            user_selected_report_type=request.business_profile,
            semantic_mapping_result=semantic_mapping_result,
            deterministic_data_profile=deterministic_router_result,
            file_name=dataset_name,
            sheet_name=sheet_name,
            user_task_description=request_text,
        )
        final_route = str(ai_routing_result.final_route or deterministic_router_result["business_profile"])
        allowed_request_routes = {
            "procurement_sales_report",
            "ecommerce_product_operations_report",
            "internet_operations_report",
            "media_campaign_report",
            "generic_business_report",
            "generic_long_business_report",
            "auto",
        }
        if final_route not in allowed_request_routes:
            final_route = str(deterministic_router_result.get("business_profile") or "generic_business_report")
        router_result = {
            **deterministic_router_result,
            "business_profile": final_route,
            "selected_by_user": ai_routing_result.selected_by_user,
            "ai_route": ai_routing_result.ai_route,
            "final_route": ai_routing_result.final_route,
            "confidence": ai_routing_result.confidence,
            "alternative_routes": ai_routing_result.alternative_routes,
            "reason": ai_routing_result.reason,
            "blocked_routes": ai_routing_result.blocked_routes,
            "trace_id": ai_routing_result.trace_id,
            "ai_semantic_trace_id": semantic_mapping_result.trace_id,
            "deterministic_router_input": deterministic_router_result,
            "profile_entrypoint": business_profile_entrypoint(final_route),
            "report_lens": business_profile_report_lens(final_route),
            "routing_uncertainty_report_generated": ai_routing_result.confidence < 0.70,
        }
        routing_result = ai_routing_result.model_dump(mode="json")

        semantic_roles = [mapping.business_role for mapping in semantic_mapping_result.field_mappings]
        metric_plan = plan_metrics_with_ai(
            output_dir=trace_output_dir,
            semantic_mapping_result=semantic_mapping_result,
            routing_result=AIBusinessRoutingResult.model_validate(routing_result),
            dataframe_profile=dataframe_profile,
            user_task_description=request_text,
            available_field_roles=semantic_roles,
            object_grain=semantic_mapping_result.object_grain,
            time_grain=semantic_mapping_result.time_grain,
            business_route=router_result["business_profile"],
            existing_metric_registry=None,
            user_selected_analysis_depth=request.report_style,
        )
        metric_result = execute_metric_plan(
            output_dir=trace_output_dir,
            dataframe=frame,
            semantic_mapping_result=semantic_mapping_result,
            metric_plan=metric_plan,
        )
        ai_usage_gate_result = validate_ai_mandatory_artifacts(trace_output_dir)
        ai_usage_gate_result["formal_pdf_allowed"] = bool(ai_usage_gate_result.get("passed"))
        ai_usage_gate_result["business_profile"] = router_result["business_profile"]
        quality_gate_path = _write_ai_usage_gate_result(trace_output_dir, ai_usage_gate_result)

        result.update(
            {
                "passed": bool(ai_usage_gate_result.get("passed")),
                "formal_pdf_allowed": bool(ai_usage_gate_result.get("passed")),
                "semantic_mapping_result": semantic_mapping_result.model_dump(mode="json"),
                "routing_result": routing_result,
                "router_result": router_result,
                "metric_plan": metric_plan.model_dump(mode="json"),
                "semantic_metric_result": metric_result["result_payload"],
                "semantic_metric_result_path": metric_result["semantic_metric_result_path"],
                "metric_derivation_log_path": metric_result["metric_derivation_log_path"],
                "ai_usage_gate_result": ai_usage_gate_result,
                "quality_gate_path": quality_gate_path,
            }
        )
        if not ai_usage_gate_result.get("passed"):
            result["failure_code"] = "AI_USAGE_GATE_FAILED"
            result["failure_reason"] = "; ".join(ai_usage_gate_result.get("failure_reasons") or ["AI usage gate failed"])
        return result
    except Exception as exc:
        failure_payload = {
            "passed": False,
            "formal_pdf_allowed": False,
            "failure_code": _normalize_failure_code(exc),
            "failure_reason": str(exc),
            "failure_reasons": [str(exc)],
        }
        quality_gate_path = _write_ai_usage_gate_result(trace_output_dir, failure_payload)
        result.update(
            {
                "failure_code": failure_payload["failure_code"],
                "failure_reason": failure_payload["failure_reason"],
                "ai_usage_gate_result": failure_payload,
                "quality_gate_path": quality_gate_path,
            }
        )
        return result


def _build_ai_router_result(
    *,
    frame: pd.DataFrame,
    dataset_name: str,
    sheet_name: str,
    request: SmartReportRequest,
    request_text: str,
    trace_output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    allowed_request_routes = {
        "procurement_sales_report",
        "ecommerce_product_operations_report",
        "internet_operations_report",
        "media_campaign_report",
        "generic_business_report",
        "generic_long_business_report",
        "auto",
    }
    deterministic_router_result = route_business_profile(
        frame,
        dataset_name=dataset_name,
        request_text=request_text,
        requested_business_profile=request.business_profile,
    )
    semantic_inputs = _field_semantic_mapper_inputs(frame)
    semantic_mapping_result = map_fields_with_ai(
        output_dir=trace_output_dir,
        dataframe_profile=semantic_inputs["dataframe_profile"],
        file_name=dataset_name,
        sheet_name=sheet_name,
        user_task_description=request_text,
        field_names=semantic_inputs["field_names"],
        inferred_data_types=semantic_inputs["inferred_data_types"],
        sample_values=semantic_inputs["sample_values"],
        missing_rate=semantic_inputs["missing_rate"],
        unique_count=semantic_inputs["unique_count"],
        numeric_distribution=semantic_inputs["numeric_distribution"],
        top_values=semantic_inputs["top_values"],
        date_parse_rate=semantic_inputs["date_parse_rate"],
    )
    ai_routing_result = route_business_context_with_ai(
        output_dir=trace_output_dir,
        user_selected_report_type=request.business_profile,
        semantic_mapping_result=semantic_mapping_result,
        deterministic_data_profile=deterministic_router_result,
        file_name=dataset_name,
        sheet_name=sheet_name,
        user_task_description=request_text,
    )
    final_route = str(ai_routing_result.final_route or deterministic_router_result["business_profile"])
    if final_route not in allowed_request_routes:
        final_route = str(deterministic_router_result.get("business_profile") or "generic_business_report")
    router_result = {
        **deterministic_router_result,
        "business_profile": final_route,
        "selected_by_user": ai_routing_result.selected_by_user,
        "ai_route": ai_routing_result.ai_route,
        "final_route": ai_routing_result.final_route,
        "confidence": ai_routing_result.confidence,
        "alternative_routes": ai_routing_result.alternative_routes,
        "reason": ai_routing_result.reason,
        "blocked_routes": ai_routing_result.blocked_routes,
        "trace_id": ai_routing_result.trace_id,
        "ai_semantic_trace_id": semantic_mapping_result.trace_id,
        "deterministic_router_input": deterministic_router_result,
        "profile_entrypoint": business_profile_entrypoint(final_route),
        "report_lens": business_profile_report_lens(final_route),
        "routing_uncertainty_report_generated": ai_routing_result.confidence < 0.70,
    }
    return router_result, {
        "semantic_mapping_result": semantic_mapping_result.model_dump(mode="json"),
        "ai_routing_result": ai_routing_result.model_dump(mode="json"),
        "trace_output_dir": str(trace_output_dir.resolve()),
    }


def build_report_orchestration(
    dataset_id: str,
    request: SmartReportRequest,
    *,
    ai_trace_output_dir: str | Path | None = None,
) -> dict[str, Any]:
    metadata = load_dataset_metadata(dataset_id)
    blueprint = build_workflow_blueprint(dataset_id)
    selected_sheet_names = _resolve_multi_sheet_names(metadata, request)
    multi_mode = request.multi_table_mode
    trace_output_dir = _ai_trace_output_dir(ai_trace_output_dir)

    long_chain_mode = "full" if request.report_style == "deep_dive" else "compressed"
    execution_steps: list[dict[str, Any]] = [
        _step(
            "intake_resolution",
            "输入整理",
            "completed",
            "先读取当前请求、工作簿元信息和用户填写字段，确定本次会话的输入范围。",
            output=f"数据集 `{metadata['name']}`，选择工作表：{'、'.join(selected_sheet_names)}。",
        ),
        _step(
            "workbook_parse",
            "工作簿解析",
            "completed",
            "先从工作簿层识别工作表角色、关系、推荐入口表和整体 workflow。",
            output=f"推荐 workflow：`{blueprint.get('workflow_mode', 'general_exploratory_analysis')}`；入口表：`{blueprint.get('recommended_entry_sheet') or selected_sheet_names[0]}`。",
        ),
    ]
    routing_request_text = " ".join(
        [
            request.user_requirement,
            request.problem_to_solve,
            request.target_audience,
            request.core_purpose,
            request.expected_result,
            request.key_constraints,
        ]
    )

    if multi_mode == "separate" and len(selected_sheet_names) > 1:
        sheet_frames = _selected_sheet_frames(dataset_id, metadata, selected_sheet_names)
        router_frame, _ = _merge_selected_sheet_frames(metadata, sheet_frames)
        ai_mandatory = _run_ai_mandatory_chain(
            frame=router_frame,
            dataset_name=str(metadata.get("name") or ""),
            sheet_name="combined_workbook_view",
            request=request,
            request_text=routing_request_text,
            trace_output_dir=trace_output_dir,
        )
        router_result = ai_mandatory.get("router_result") or route_business_profile(
            router_frame,
            dataset_name=str(metadata.get("name") or ""),
            request_text=routing_request_text,
            requested_business_profile=request.business_profile,
        )
        router_result = _honor_explicit_business_profile(router_result, request)
        routed_request = request.model_copy(update={"business_profile": router_result["business_profile"]})
        execution_steps.extend(
            [
                _step(
                    "route_selection",
                    "路线选择",
                    "completed",
                    "检测到当前为多表分开分析模式，先生成工作簿级总控报告，再逐表派发子任务。",
                    output=f"共 {len(selected_sheet_names)} 张表进入逐表子任务。",
                ),
                _step(
                    "child_dispatch",
                    "子任务分发",
                    "completed",
                    "当前模式会按工作表拆分多个独立子报告，避免不同粒度的表被强行合并。",
                    output="逐表子报告会由上层并发派发。",
                ),
            ]
        )
        thinking_steps = [
            _step(
                "primary_question",
                "先问什么",
                "completed",
                "先判断这些表该分开看还是一起看，而不是先跑统计。",
                output="优先回答工作表之间的关系和入口表。",
                category="thinking",
            ),
            _step(
                "boundary",
                "边界控制",
                "completed",
                "分开分析模式下不强行把不同粒度的表混成一个观察单位。",
                output="主报告做总控，子报告做逐表深挖。",
                category="thinking",
            ),
        ]
        return {
            "metadata": metadata,
            "blueprint": blueprint,
            "selected_sheet_names": selected_sheet_names,
            "multi_mode": multi_mode,
            "long_chain_mode": long_chain_mode,
            "request": routed_request,
            "business_profile_router": router_result,
            "ai_mandatory": ai_mandatory,
            "execution_steps": execution_steps,
            "thinking_steps": thinking_steps,
        }

    if multi_mode == "combined" and len(selected_sheet_names) > 1:
        sheet_frames = _selected_sheet_frames(dataset_id, metadata, selected_sheet_names)
        router_frame, _ = _merge_selected_sheet_frames(metadata, sheet_frames)
        ai_mandatory = _run_ai_mandatory_chain(
            frame=router_frame,
            dataset_name=str(metadata.get("name") or ""),
            sheet_name="combined_workbook_view",
            request=request,
            request_text=routing_request_text,
            trace_output_dir=trace_output_dir,
        )
        router_result = ai_mandatory.get("router_result") or route_business_profile(
            router_frame,
            dataset_name=str(metadata.get("name") or ""),
            request_text=routing_request_text,
            requested_business_profile=request.business_profile,
        )
        router_result = _honor_explicit_business_profile(router_result, request)
        routed_request = request.model_copy(update={"business_profile": router_result["business_profile"]})
        relationship_count = sum(
            1
            for item in blueprint.get("relationships", [])
            if item.get("left_sheet") in selected_sheet_names and item.get("right_sheet") in selected_sheet_names
        )
        execution_steps.extend(
            [
                _step(
                    "route_selection",
                    "路线选择",
                    "completed",
                    "检测到当前为组合分析模式，先做工作簿级总览，再决定是否值得联表。",
                    output=f"所选表之间高置信关系 {relationship_count} 条。",
                ),
                _step(
                    "combined_summary",
                    "组合总览",
                    "completed",
                    "当前模式保留各表身份，不把不同观察单位强制合并。",
                    output="输出工作表总览、跨表关系和入口建议。",
                ),
            ]
        )
        thinking_steps = [
            _step(
                "primary_question",
                "先问什么",
                "completed",
                "组合分析先回答这些表如何一起被使用，再决定是否联表。",
                output="先看工作表角色和高置信关系。",
                category="thinking",
            ),
            _step(
                "boundary",
                "边界控制",
                "completed",
                "关系弱时只做并列解释，不强行做联表因果或联合统计。",
                output="多表模式优先结构判断，后置强统计。",
                category="thinking",
            ),
        ]
        return {
            "metadata": metadata,
            "blueprint": blueprint,
            "selected_sheet_names": selected_sheet_names,
            "multi_mode": multi_mode,
            "long_chain_mode": long_chain_mode,
            "request": routed_request,
            "business_profile_router": router_result,
            "ai_mandatory": ai_mandatory,
            "execution_steps": execution_steps,
            "thinking_steps": thinking_steps,
        }

    if multi_mode == "merge" and len(selected_sheet_names) > 1:
        sheet_frames = _selected_sheet_frames(dataset_id, metadata, selected_sheet_names)
        frame, sheet = _merge_selected_sheet_frames(metadata, sheet_frames)
        execution_steps.append(
            _step(
                "route_selection",
                "路线选择",
                "completed",
                "检测到当前为一键合并分析模式，先把选中工作表纵向拼接，再按一张总表进入分析程序。",
                output=f"合并后观察单位为 `{sheet['name']}`，并增加 `来源工作表` 字段。",
            )
        )
    else:
        frame, metadata, sheet = load_dataset_frame(dataset_id, request.sheet_name)
        execution_steps.append(
            _step(
                "route_selection",
                "路线选择",
                "completed",
                "当前按单表模式进入分析程序。",
                output=f"当前工作表：`{sheet['name']}`。",
            )
        )

    ai_mandatory = _run_ai_mandatory_chain(
        frame=frame,
        dataset_name=str(metadata.get("name") or ""),
        sheet_name=str(sheet["name"]),
        request=request,
        request_text=routing_request_text,
        trace_output_dir=trace_output_dir,
    )
    router_result = ai_mandatory.get("router_result") or route_business_profile(
        frame,
        dataset_name=str(metadata.get("name") or ""),
        request_text=routing_request_text,
        requested_business_profile=request.business_profile,
    )
    router_result = _honor_explicit_business_profile(router_result, request)
    routed_request = request.model_copy(update={"business_profile": router_result["business_profile"]})
    execution_steps.append(
        _step(
            "business_profile_router",
            "业务类型路由",
            "completed",
            "所有报告在进入分析主链前，先统一识别业务类型，避免直接套错采销、运营或投放模板。",
            output=(
                f"当前识别为 `{router_result['business_profile']}`；"
                f"confidence={router_result['confidence']:.2f}；"
                f"entrypoint=`{router_result['profile_entrypoint']}`。"
            ),
        )
    )

    def run_program_bundle(_: dict[str, Any]) -> dict[str, Any]:
        return build_analysis_program(routed_request, metadata["name"], sheet["name"], frame)

    def run_profile_bundle(_: dict[str, Any]) -> dict[str, Any]:
        numeric_cols = numeric_columns(frame)
        analysis_numeric_cols = [column for column in numeric_cols if "id" not in column.lower()]
        temporal_cols = datetime_columns(frame)
        categorical_cols = categorical_columns(frame, numeric_cols, temporal_cols)
        return {
            "numeric_cols": numeric_cols,
            "analysis_numeric_cols": analysis_numeric_cols,
            "temporal_cols": temporal_cols,
            "categorical_cols": categorical_cols,
            "working_numeric_cols": analysis_numeric_cols or numeric_cols,
        }

    def run_resolved_request(results: dict[str, Any]) -> SmartReportRequest:
        return _resolved_request_from_program(routed_request, results["program_bundle"])

    def run_statistical_scope(results: dict[str, Any]) -> dict[str, Any]:
        profile = results["profile_bundle"]
        resolved_request = results["resolved_request"]
        program_bundle = results["program_bundle"]
        return codex_statistical_scope(
            {
                "dataset_name": metadata["name"],
                "sheet_name": sheet["name"],
                "numeric_columns": profile["working_numeric_cols"],
                "temporal_columns": profile["temporal_cols"],
                "column_profiles": metadata.get("column_summaries", []),
                "semantic_mapping": program_bundle.get("semantic_mapping", {}),
                "object_candidates": program_bundle.get("object_candidates", []),
                "task_model": program_bundle.get("task_model", {}),
                "user_requirement": resolved_request.user_requirement,
                "problem_to_solve": resolved_request.problem_to_solve,
                "target_audience": resolved_request.target_audience,
                "core_purpose": resolved_request.core_purpose,
            }
        )

    def run_market_intelligence(results: dict[str, Any]) -> dict[str, Any]:
        profile = results["profile_bundle"]
        resolved_request = results["resolved_request"]
        return build_market_intelligence(
            frame=frame,
            numeric_cols=profile["working_numeric_cols"],
            categorical_cols=profile["categorical_cols"],
            temporal_cols=profile["temporal_cols"],
            request_text=" ".join(
                [
                    resolved_request.user_requirement,
                    resolved_request.problem_to_solve,
                    resolved_request.target_audience,
                    resolved_request.core_purpose,
                    resolved_request.expected_result,
                    resolved_request.key_constraints,
                ]
            ),
        )

    def run_expert_summary(results: dict[str, Any]) -> dict[str, Any]:
        program_bundle = results["program_bundle"]
        experts = program_bundle.get("experts") or []
        task_model = program_bundle.get("task_model") or {}
        return {
            "primary_family": task_model.get("primary_family", "mixed_business_review"),
            "experts": experts,
            "summary": "、".join(item.get("expert", "") for item in experts[:2]) or "通用分析负责人",
        }

    graph = execute_job_graph(
        [
            JobNode(
                job_id="program_bundle",
                title="任务建模与对象识别",
                detail="先锁定需求、对象、字段语义和专家视角，形成分析程序。",
                category="engineering",
                parallel_group="planning",
                runner=run_program_bundle,
                formatter=lambda output: f"主业务家族 `{(output.get('task_model') or {}).get('primary_family', 'mixed_business_review')}`。",
            ),
            JobNode(
                job_id="profile_bundle",
                title="上传解析与字段画像",
                detail="先拆 numeric / categorical / temporal 结构，为后续统计和语义层准备底稿。",
                category="engineering",
                parallel_group="planning",
                runner=run_profile_bundle,
                formatter=lambda output: f"数值字段 {len(output['working_numeric_cols'])} 个，分类字段 {len(output['categorical_cols'])} 个。",
            ),
            JobNode(
                job_id="resolved_request",
                title="输入补齐结果落地",
                detail="把需求补齐后的结果回写到有效请求，确保后续节点都用同一版输入。",
                category="engineering",
                dependencies=("program_bundle",),
                runner=run_resolved_request,
                formatter=lambda output: output.problem_to_solve or output.user_requirement or "围绕核心问题组织。",
            ),
            JobNode(
                job_id="statistical_scope",
                title="统计执行守门",
                detail="决定哪些字段能进入相关性、方法实跑和建模，避免时间字段或索引字段误入统计。",
                category="engineering",
                dependencies=("program_bundle", "profile_bundle", "resolved_request"),
                parallel_group="analysis",
                runner=run_statistical_scope,
                formatter=lambda output: f"纳入统计字段 {len(output.get('keep_numeric_columns', []))} 个。",
            ),
            JobNode(
                job_id="market_intelligence",
                title="网络检索 / 市场知识拼接位",
                detail="并行构建市场与结构层判断，为后续正文和策略层提供额外上下文。",
                category="engineering",
                dependencies=("profile_bundle", "resolved_request"),
                parallel_group="analysis",
                runner=run_market_intelligence,
                formatter=lambda output: "市场层已完成准备。" if output.get("ready") else "当前未识别出稳定市场切片。",
            ),
            JobNode(
                job_id="expert_summary",
                title="专家层汇总",
                detail="把当前激活的专家视角压成可直接进入正文和 trace 的专家层摘要。",
                category="engineering",
                dependencies=("program_bundle",),
                parallel_group="analysis",
                runner=run_expert_summary,
                formatter=lambda output: output.get("summary", "通用分析负责人"),
            ),
        ],
        max_workers=4,
    )

    results = graph["results"]
    program_bundle = results["program_bundle"]
    program_bundle["ai_mandatory"] = ai_mandatory
    program_bundle["ai_field_semantic_mapping"] = ai_mandatory.get("semantic_mapping_result") or {}
    program_bundle["ai_business_routing"] = ai_mandatory.get("routing_result") or {}
    program_bundle["ai_metric_derivation_plan"] = ai_mandatory.get("metric_plan") or {}
    program_bundle["semantic_metric_result"] = ai_mandatory.get("semantic_metric_result") or {}
    program_bundle["metric_derivation_log_path"] = ai_mandatory.get("metric_derivation_log_path") or ""
    program_bundle["semantic_metric_result_path"] = ai_mandatory.get("semantic_metric_result_path") or ""
    program_bundle["ai_usage_gate_result"] = ai_mandatory.get("ai_usage_gate_result") or {}
    resolved_request = results["resolved_request"]
    analysis_program = program_bundle.get("program") or {}
    hypotheses = program_bundle.get("hypotheses") or []
    primary_hypothesis = hypotheses[0]["title"] if hypotheses else (program_bundle.get("task_model") or {}).get("primary_family", "mixed_business_review")
    backup_hypothesis = hypotheses[1]["title"] if len(hypotheses) > 1 else "当前没有更强的副解释"

    execution_steps.extend(
        [
            _step(
                "job_graph_dispatch",
                "并行 job graph 调度",
                "completed",
                "把上传解析、任务建模、统计守门、市场层和专家层拆成独立 job，并按依赖关系并发执行。",
                output="planning / analysis 两个并行组已完成调度。",
            ),
            _step(
                "requirement_modeling",
                "任务建模",
                "completed",
                "把需求补齐、对象识别和主问题锁成统一分析程序。",
                output="已生成需求模型和主解释路径。",
            ),
            _step(
                "statistical_execution",
                "统计执行",
                "completed",
                "统计守门和后续方法执行都挂在 job graph 上，不再串行等待。",
                output=f"当前统计守门保留 {len(results['statistical_scope'].get('keep_numeric_columns', []))} 个字段。",
            ),
            _step(
                "network_retrieval",
                "网络检索",
                "completed",
                "把网络/外部响应型能力放进并行组里，与本地统计和对象识别同时推进。",
                output="市场层与语义层会继续作为并行节点进入后续阶段。",
            ),
            _step(
                "specialist_activation",
                "专家层汇总",
                "completed",
                "专家层不再只是配置表，而是作为单独节点并入并行调度。",
                output=results["expert_summary"].get("summary", "通用分析负责人"),
            ),
            *[
                {
                    "id": item["id"],
                    "title": item["title"],
                    "status": item["status"],
                    "detail": item["detail"],
                    "output": item.get("output", ""),
                    "category": item["category"],
                    "parallel_group": item.get("parallel_group", ""),
                }
                for item in graph["steps"]
                if item["status"] == "completed"
            ],
            _step(
                "report_assembly",
                "报告组装",
                "completed",
                "把统计结果、语义判断、市场层和风险边界合成主报告。",
                output="进入中文主报告生成。",
            ),
        ]
    )

    thinking_steps = [
        _step(
            "primary_question",
            "先问什么",
            "completed",
            (program_bundle.get("task_model") or {}).get("problem", "先定义当前数据到底服务于什么业务判断"),
            output="正文围绕问题组织，而不是围绕方法目录组织。",
            category="thinking",
        ),
        _step(
            "primary_explanation",
            "主解释",
            "completed",
            primary_hypothesis,
            output="当前作为正文主线的解释路径。",
            category="thinking",
        ),
        _step(
            "backup_explanation",
            "备选解释",
            "completed",
            backup_hypothesis,
            output="当前作为补充模块和风险对照的解释路径。",
            category="thinking",
        ),
        _step(
            "evidence_priority",
            "证据优先级",
            "completed",
            "；".join(analysis_program.get("core_outcomes", [])[:2] + analysis_program.get("explanatory_slices", [])[:2]) or "先看核心结果变量和关键切片。",
            output="决定哪些证据进入正文、哪些只留附录。",
            category="thinking",
        ),
        _step(
            "confidence_boundary",
            "边界控制",
            "completed",
            "；".join(analysis_program.get("cannot_analyze", [])[:2]) or "当前没有显著禁区。",
            output="避免把弱证据写成强判断。",
            category="thinking",
        ),
    ]

    return {
        "metadata": metadata,
        "blueprint": blueprint,
        "selected_sheet_names": selected_sheet_names,
        "multi_mode": multi_mode,
        "long_chain_mode": long_chain_mode,
        "frame": program_bundle["frame"],
        "sheet": sheet,
        "request": resolved_request,
        "business_profile_router": router_result,
        "ai_mandatory": ai_mandatory,
        "program_bundle": program_bundle,
        "statistical_scope": results["statistical_scope"],
        "market_intelligence": results["market_intelligence"],
        "execution_steps": execution_steps,
        "thinking_steps": thinking_steps,
        "job_graph": graph["steps"],
        "expert_summary": results["expert_summary"],
    }
