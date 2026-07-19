from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models import CodexRunRequest, RuntimeStageSpec, SmartReportRequest
from app.services import report_service as report_service_module
from app.services.codex_runtime_service import build_runtime_stage_request
from app.services.report_coordinator_service import ReportCoordinator


def _runtime_policy_for_lens(runtime_child_task_creator, *, business_profile: str = "", report_lens: str = "mixed_business_review") -> dict[str, object]:
    return report_service_module._runtime_policy(
        runtime_child_task_creator,
        business_profile=business_profile,
        report_lens=report_lens,
    )


def test_report_stage_registry_splits_deterministic_and_runtime_stages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    policy = report_service_module._runtime_policy(
        object(),
        business_profile="generic_long_business_report",
        report_lens="mixed_business_review",
    )
    registry = report_service_module._build_report_stage_registry(policy)

    semantic = registry["semantic_layer"]
    statistical = registry["statistical_method_selection"]
    page_plan = registry["long_report_page_plan"]

    assert semantic["stage_id"] == "semantic_layer"
    assert semantic["stage_kind"] == "runtime_stage"
    assert semantic["runner_mode"] == "runtime_first"
    assert semantic["fallback_mode"] == "local_fallback"
    assert "semantic_layer_runtime_output.json" in semantic["artifact_contract"]["primary_artifacts"]
    assert "runtime_child_job_id" in semantic["telemetry_fields"]

    assert page_plan["stage_kind"] == "runtime_stage"
    assert "page_plan.json" in page_plan["artifact_contract"]["primary_artifacts"]

    assert statistical["stage_kind"] == "deterministic_stage"
    assert statistical["runner_mode"] == "deterministic_local"
    assert statistical["fallback_mode"] == "none"
    assert "status" in statistical["telemetry_fields"]


def test_runtime_child_lineage_builder_collects_parent_child_fields() -> None:
    lineage = report_service_module._build_runtime_child_lineage(
        [
            {
                "job_id": "codex-task-001",
                "run_id": "run-001",
                "parent_report_id": "report-001",
                "parent_report_job_id": "report-task-001",
                "parent_stage_id": "semantic_layer",
                "child_index": 2,
                "stage_id": "semantic_layer",
                "purpose": "semantic_layer",
                "artifact_source": "semantic_layer_runtime_output.json",
                "runtime_state": "live",
                "degradation_state": "none",
                "status": "completed",
            }
        ]
    )

    assert lineage == [
        {
            "job_id": "codex-task-001",
            "run_id": "run-001",
            "parent_report_id": "report-001",
            "parent_report_job_id": "report-task-001",
            "parent_stage_id": "semantic_layer",
            "child_index": 2,
            "stage_id": "semantic_layer",
            "purpose": "semantic_layer",
            "artifact_source": "semantic_layer_runtime_output.json",
            "runtime_state": "live",
            "degradation_state": "none",
            "status": "completed",
        }
    ]


def test_runtime_stage_spec_builds_codex_run_request() -> None:
    spec = RuntimeStageSpec(
        stage_id="semantic_layer",
        runtime_allowed=True,
        prompt_builder=lambda ctx: "Prompt with {context_json}",
        workspace_path_builder=lambda ctx: str(ctx["report_dir"]),
        expected_artifact_files=["semantic_layer_runtime_output.json"],
        fallback_runner=lambda ctx: {"mode": "fallback"},
        timeout_sec=321,
        capture_git_diff=False,
        purpose="semantic_layer",
        context_payload_builder=lambda ctx: {"semantic_context": ctx["context_payload"]},
    )
    request = build_runtime_stage_request(
        spec,
        stage_context={"report_dir": Path("E:/agents/data-analysis-agent/workspace"), "context_payload": {"field": "value"}},
        report_id="report-001",
        dataset_id="dataset-001",
        sheet_name="Sheet1",
        user_requirement="explain semantic layer",
    )

    assert request.workspace_path.endswith("workspace")
    assert request.prompt_template == "Prompt with {context_json}"
    assert request.context_payload == {"semantic_context": {"field": "value"}}
    assert request.stage_id == "semantic_layer"
    assert request.purpose == "semantic_layer"
    assert request.timeout_sec == 321
    assert request.capture_git_diff is False


def test_runtime_stage_helper_supports_direct_runtime_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_path = tmp_path / "semantic_layer_runtime_output.json"

    def _direct_runner(request: CodexRunRequest) -> dict[str, object]:
        output_path.write_text(json.dumps(_semantic_payload("direct runtime semantic"), ensure_ascii=False), encoding="utf-8")
        return {
            "run_id": "run-direct-001",
            "status": "completed",
            "workspace_path": request.workspace_path,
            "artifact_source": "semantic_layer_runtime_output.json",
        }

    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    policy = _runtime_policy_for_lens(None)
    policy["runtime_available"] = True

    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="mixed_business_review",
        query_loop_id="report-loop-direct-runtime",
    )
    result = report_service_module._execute_runtime_stage_with_fallback(
        spec=RuntimeStageSpec(
            stage_id="semantic_layer",
            runtime_allowed=True,
            prompt_builder=lambda ctx: "Prompt with {context_json}",
            workspace_path_builder=lambda ctx: str(ctx["report_dir"]),
            expected_artifact_files=["semantic_layer_runtime_output.json"],
            fallback_runner=lambda ctx: {"mode": "fallback"},
            timeout_sec=30,
            capture_git_diff=False,
            purpose="semantic_layer",
            runtime_policy_alias="semantic",
            context_payload_builder=lambda ctx: dict(ctx["context_payload"]),
            artifact_validator=report_service_module._semantic_layer_payload_compatible,
        ),
        stage_context={"report_dir": tmp_path, "context_payload": {"field": "value"}},
        report_id="report-001",
        dataset_id="dataset-001",
        sheet_name="Sheet1",
        request=SmartReportRequest(user_requirement="请解释语义层"),
        runtime_policy=policy,
        runtime_child_task_creator=None,
        coordinator=coordinator,
        direct_runtime_runner=_direct_runner,
    )

    assert result["title"] == "direct runtime semantic"
    assert result["runtime_child_job_id"] == ""
    assert result["runtime_child_run_id"] == "run-direct-001"
    assert result["unsafe_runtime_output"] is False


def test_runtime_stage_helper_marks_unsafe_output_and_falls_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "semantic_layer_runtime_output.json").write_text(json.dumps({"bad": "payload"}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    policy = _runtime_policy_for_lens(None)
    policy["runtime_available"] = True

    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="mixed_business_review",
        query_loop_id="report-loop-unsafe-runtime",
    )
    result = report_service_module._execute_runtime_stage_with_fallback(
        spec=RuntimeStageSpec(
            stage_id="semantic_layer",
            runtime_allowed=True,
            prompt_builder=lambda ctx: "Prompt with {context_json}",
            workspace_path_builder=lambda ctx: str(ctx["report_dir"]),
            expected_artifact_files=["semantic_layer_runtime_output.json"],
            fallback_runner=lambda ctx: {"title": "local semantic", "mode": "fallback"},
            timeout_sec=30,
            capture_git_diff=False,
            purpose="semantic_layer",
            runtime_policy_alias="semantic",
            context_payload_builder=lambda ctx: dict(ctx["context_payload"]),
            artifact_validator=report_service_module._semantic_layer_payload_compatible,
        ),
        stage_context={"report_dir": tmp_path, "context_payload": {"field": "value"}},
        report_id="report-001",
        dataset_id="dataset-001",
        sheet_name="Sheet1",
        request=SmartReportRequest(user_requirement="请解释语义层"),
        runtime_policy=policy,
        runtime_child_task_creator=None,
        coordinator=coordinator,
        direct_runtime_runner=lambda request: {"run_id": "run-direct-002", "status": "completed", "workspace_path": request.workspace_path},
    )

    assert result["title"] == "local semantic"
    assert result["unsafe_runtime_output"] is True
    assert result["fallback_reason"].startswith("unsafe_runtime_output:")


def test_runtime_stage_helper_salvages_valid_artifact_after_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    runtime_output = report_dir / report_service_module.SEMANTIC_RUNTIME_OUTPUT_FILENAME

    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    monkeypatch.setattr(
        report_service_module,
        "get_codex_run_task",
        lambda job_id: {
            "job_id": job_id,
            "run_id": "run-semantic-timeout-001",
            "status": "timed_out",
            "child_index": 1,
            "parent_report_job_id": "report-task-parent-001",
        },
    )

    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="mixed_business_review",
        query_loop_id="report-loop-timeout-salvage",
    )

    def _timed_out_child_task_creator(request: CodexRunRequest, **kwargs) -> dict[str, object]:
        runtime_output.write_text(
            json.dumps(_semantic_structured_payload(), ensure_ascii=False),
            encoding="utf-8",
        )
        return {
            "job_id": "codex-task-semantic-timeout-001",
            "run_id": "",
            "parent_report_job_id": "report-task-parent-001",
            "parent_report_id": kwargs.get("parent_report_id", ""),
            "parent_stage_id": kwargs.get("parent_stage_id", ""),
            "child_index": 1,
            "stage_id": kwargs.get("stage_id", ""),
            "purpose": kwargs.get("purpose", ""),
            "artifact_source": kwargs.get("artifact_source", ""),
            "status": "running",
            "progress_percent": 0,
            "current_stage_id": "queued",
            "current_stage_title": "Task created",
            "current_stage_detail": "queued",
        }
    result = report_service_module._execute_runtime_stage_with_fallback(
        spec=RuntimeStageSpec(
            stage_id="semantic_layer",
            runtime_allowed=True,
            prompt_builder=lambda ctx: "Prompt with {context_json}",
            workspace_path_builder=lambda ctx: str(ctx["report_dir"]),
            expected_artifact_files=["semantic_layer_runtime_output.json"],
            fallback_runner=lambda ctx: {"title": "local semantic", "mode": "fallback"},
            timeout_sec=30,
            capture_git_diff=False,
            purpose="semantic_layer",
            runtime_policy_alias="semantic",
            result_artifact_source="semantic_layer_runtime_json",
            context_payload_builder=lambda ctx: dict(ctx["context_payload"]),
            artifact_validator=report_service_module._semantic_layer_payload_compatible,
            artifact_normalizer=report_service_module._normalize_semantic_layer_runtime_payload,
        ),
        stage_context={"report_dir": report_dir, "context_payload": {"field": "value"}},
        report_id="report-001",
        dataset_id="dataset-001",
        sheet_name="Sheet1",
        request=SmartReportRequest(user_requirement="请解释语义层"),
        runtime_policy=_runtime_policy_for_lens(object()),
        runtime_child_task_creator=_timed_out_child_task_creator,
        coordinator=coordinator,
    )

    assert result["title"] == "结构化语义层摘要"
    assert result["unsafe_runtime_output"] is False
    assert result["runtime_terminal_status"] == "timed_out"
    assert result["degradation_state"] == "timed_out_artifact_salvaged"
    assert isinstance(result["creator_profile"], str)
    assert isinstance(result["audience_profile"], list)
    assert all(isinstance(item, str) for item in result["evidence_points"])
    assert all(isinstance(item, str) for item in result["important_columns"])
    assert all(isinstance(item, str) for item in result["recommended_actions"])


def _semantic_payload(title: str) -> dict[str, object]:
    return {
        "title": title,
        "subject_type": "generic_subject",
        "creator_profile": "测试主体主要围绕经营数据进行记录与分析。",
        "content_domains": ["测试领域A", "测试领域B", "测试领域C"],
        "audience_profile": ["测试受众A", "测试受众B", "测试受众C"],
        "evidence_points": ["证据A", "证据B", "证据C"],
        "text_findings": ["文本发现A", "文本发现B", "文本发现C"],
        "numeric_findings": ["数值发现A", "数值发现B", "数值发现C"],
        "metric_cards": [
            {
                "metric": "gmv",
                "role": "核心指标",
                "business_meaning": "GMV 代表成交规模。",
                "management_impact": "管理层可据此判断规模走势。",
                "caution": "需结合口径核对。",
            }
        ],
        "important_columns": ["gmv", "channel", "date"],
        "recommended_actions": ["动作A", "动作B", "动作C"],
    }


def _semantic_structured_payload() -> dict[str, object]:
    return {
        "title": "结构化语义层摘要",
        "subject_type": "transaction_entity",
        "creator_profile": {
            "主体来源判断": "这是一次订单与经营抽样视角下的语义理解。",
            "组织方式": "围绕品类、商品、SKU 与供应商四层结构展开。",
        },
        "content_domains": ["采购经营分析", "供应商管理", "商品结构管理"],
        "audience_profile": {
            "核心受众": "采购负责人、经营分析人员",
            "使用建议": "适合作为排优先级与复核清单的输入。",
        },
        "evidence_points": [
            {
                "evidence": "样本规模较小，很多对象仍需复核。",
                "certainty": "高",
                "implication": "当前更适合做方向判断，不适合直接下强结论。",
            }
        ],
        "text_findings": [
            {
                "theme": "履约异常",
                "evidence": "评论文本中出现未收到货表述。",
                "interpretation": "局部样本可能涉及实际收货异常。",
                "certainty": "较高",
            }
        ],
        "numeric_findings": [
            {
                "metric": "销售额",
                "finding": "均值高于中位数，说明分布右偏。",
                "implication": "头部订单会显著放大整体表现。",
            }
        ],
        "metric_cards": [
            {
                "metric": "销售额",
                "role": "结果规模",
                "business_meaning": "用于识别主要成交贡献对象。",
                "management_impact": "可用于区分头部维护与中段承接策略。",
                "caution": "样本偏小，需防止被单笔订单放大。",
            }
        ],
        "important_columns": [
            {
                "column": "Revenue",
                "semantic_role": "核心结果字段",
                "why_important": "用于识别销售贡献与集中度。",
            }
        ],
        "recommended_actions": [
            {
                "priority": "高",
                "action": "优先复核低分对象与异常履约样本。",
                "reason": "这些对象同时承载体验风险与经营影响。",
            }
        ],
    }


def _business_background_payload(summary: str) -> dict[str, object]:
    return {
        "background_summary": summary,
        "key_points": ["背景要点A", "背景要点B", "背景要点C"],
        "decision_implications": ["决策含义A", "决策含义B", "决策含义C"],
    }


def test_semantic_layer_prefers_runtime_child_when_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    runtime_output = report_dir / report_service_module.SEMANTIC_RUNTIME_OUTPUT_FILENAME

    observed_request: dict[str, object] = {}

    def fake_runtime_child_task_creator(
        request: CodexRunRequest,
        *,
        parent_report_id: str = "",
        parent_stage_id: str = "",
        child_index: int = 0,
        stage_id: str = "",
        purpose: str = "",
        artifact_source: str = "",
        stage_listener=None,
    ) -> dict[str, object]:
        observed_request["workspace_path"] = request.workspace_path
        observed_request["parent_report_id"] = parent_report_id
        observed_request["stage_id"] = stage_id
        observed_request["purpose"] = purpose
        runtime_output.write_text(json.dumps(_semantic_payload("runtime semantic"), ensure_ascii=False), encoding="utf-8")
        if stage_listener:
            stage_listener(
                {
                    "stage_id": "runtime_child::semantic_layer::workspace_validated",
                    "title": "Runtime child: Workspace validated",
                    "detail": "semantic runtime workspace validated",
                    "timestamp": "2026-04-30T00:00:00Z",
                    "payload": {
                        "status": "running",
                        "runtime_child_job_id": "codex-task-semantic-001",
                        "runtime_child_run_id": "run-semantic-001",
                        "runtime_parent_report_id": parent_report_id,
                        "runtime_stage_id": stage_id,
                        "runtime_purpose": purpose,
                    },
                }
            )
        return {
            "job_id": "codex-task-semantic-001",
            "run_id": "",
            "parent_report_job_id": "report-task-parent-001",
            "parent_report_id": parent_report_id,
            "parent_stage_id": parent_stage_id,
            "child_index": child_index,
            "stage_id": stage_id,
            "purpose": purpose,
            "artifact_source": artifact_source,
            "status": "queued",
            "progress_percent": 0,
            "current_stage_id": "queued",
            "current_stage_title": "Task created",
            "current_stage_detail": "queued",
        }

    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    monkeypatch.setattr(
        report_service_module,
        "get_codex_run_task",
        lambda job_id: {"job_id": job_id, "run_id": "run-semantic-001", "status": "completed"},
    )
    monkeypatch.setattr(
        report_service_module,
        "codex_semantic_analysis",
        lambda semantic_context: pytest.fail("runtime success should not fall back to local semantic analysis"),
    )

    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="mixed_business_review",
        query_loop_id="report-loop-semantic-success",
    )
    result = report_service_module._semantic_layer_with_optional_runtime(
        report_dir=report_dir,
        report_id="report-001",
        dataset_id="dataset-001",
        sheet_name="Sheet1",
        request=SmartReportRequest(user_requirement="请解释语义层"),
        semantic_context={"text_columns": ["content"], "numeric_columns": ["gmv"]},
        runtime_policy=_runtime_policy_for_lens(fake_runtime_child_task_creator),
        runtime_child_task_creator=fake_runtime_child_task_creator,
        coordinator=coordinator,
    )

    assert result["title"] == "runtime semantic"
    assert result["author_mode"] == "codex_cli_runtime"
    assert result["runtime_state"] == "live"
    assert result["degradation_state"] == "none"
    assert result["artifact_source"] == "semantic_layer_runtime_json"
    assert result["parent_report_job_id"] == "report-task-parent-001"
    assert result["parent_report_id"] == "report-001"
    assert result["stage_id"] == "semantic_layer"
    assert result["purpose"] == "semantic_layer"
    assert observed_request["stage_id"] == "semantic_layer"
    assert any(event["stage_id"].startswith("runtime_child::semantic_layer::") for event in coordinator.stage_events)


def test_semantic_layer_falls_back_to_local_when_runtime_child_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    def fake_runtime_child_task_creator(
        request: CodexRunRequest,
        *,
        parent_report_id: str = "",
        parent_stage_id: str = "",
        child_index: int = 0,
        stage_id: str = "",
        purpose: str = "",
        artifact_source: str = "",
        stage_listener=None,
    ) -> dict[str, object]:
        return {
            "job_id": "codex-task-semantic-002",
            "parent_report_job_id": "report-task-parent-002",
            "parent_report_id": parent_report_id,
            "parent_stage_id": parent_stage_id,
            "child_index": child_index,
            "stage_id": stage_id,
            "purpose": purpose,
            "artifact_source": artifact_source,
            "status": "queued",
            "progress_percent": 0,
            "current_stage_id": "queued",
            "current_stage_title": "Task created",
            "current_stage_detail": "queued",
        }

    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    monkeypatch.setattr(
        report_service_module,
        "get_codex_run_task",
        lambda job_id: {"job_id": job_id, "run_id": "run-semantic-002", "status": "failed"},
    )
    monkeypatch.setattr(
        report_service_module,
        "codex_semantic_analysis",
        lambda semantic_context: {
            **_semantic_payload("local semantic"),
            "mode": "fallback",
            "runtime_state": "fallback",
            "degradation_state": "hard_fallback",
        },
    )

    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="mixed_business_review",
        query_loop_id="report-loop-semantic-fallback",
    )
    result = report_service_module._semantic_layer_with_optional_runtime(
        report_dir=report_dir,
        report_id="report-002",
        dataset_id="dataset-002",
        sheet_name="Sheet1",
        request=SmartReportRequest(user_requirement="请解释语义层"),
        semantic_context={"text_columns": ["content"], "numeric_columns": ["gmv"]},
        runtime_policy=_runtime_policy_for_lens(fake_runtime_child_task_creator),
        runtime_child_task_creator=fake_runtime_child_task_creator,
        coordinator=coordinator,
    )

    assert result["title"] == "local semantic"
    assert result["runtime_state"] == "fallback"
    assert any(event["stage_id"] == "semantic_layer_runtime_fallback" for event in coordinator.stage_events)


def test_business_background_prefers_runtime_child_when_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    runtime_output = report_dir / report_service_module.BUSINESS_BACKGROUND_RUNTIME_OUTPUT_FILENAME

    def fake_runtime_child_task_creator(
        request: CodexRunRequest,
        *,
        parent_report_id: str = "",
        parent_stage_id: str = "",
        child_index: int = 0,
        stage_id: str = "",
        purpose: str = "",
        artifact_source: str = "",
        stage_listener=None,
    ) -> dict[str, object]:
        runtime_output.write_text(json.dumps(_business_background_payload("runtime background"), ensure_ascii=False), encoding="utf-8")
        if stage_listener:
            stage_listener(
                {
                    "stage_id": "runtime_child::business_background_runtime::workspace_validated",
                    "title": "Runtime child: Workspace validated",
                    "detail": "business background runtime workspace validated",
                    "timestamp": "2026-04-30T00:00:00Z",
                    "payload": {
                        "status": "running",
                        "runtime_child_job_id": "codex-task-background-001",
                        "runtime_child_run_id": "run-background-001",
                        "runtime_parent_report_id": parent_report_id,
                        "runtime_stage_id": stage_id,
                        "runtime_purpose": purpose,
                    },
                }
            )
        return {
            "job_id": "codex-task-background-001",
            "run_id": "",
            "parent_report_job_id": "report-task-parent-010",
            "parent_report_id": parent_report_id,
            "parent_stage_id": parent_stage_id,
            "child_index": child_index,
            "stage_id": stage_id,
            "purpose": purpose,
            "artifact_source": artifact_source,
            "status": "queued",
            "progress_percent": 0,
            "current_stage_id": "queued",
            "current_stage_title": "Task created",
            "current_stage_detail": "queued",
        }

    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    monkeypatch.setattr(
        report_service_module,
        "get_codex_run_task",
        lambda job_id: {"job_id": job_id, "run_id": "run-background-001", "status": "completed"},
    )
    monkeypatch.setattr(
        report_service_module,
        "codex_business_background_analysis",
        lambda background_context: pytest.fail("runtime success should not fall back to local business background analysis"),
    )

    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="mixed_business_review",
        query_loop_id="report-loop-background-success",
    )
    result = report_service_module._business_background_with_optional_runtime(
        report_dir=report_dir,
        report_id="report-010",
        dataset_id="dataset-010",
        sheet_name="Sheet1",
        request=SmartReportRequest(user_requirement="请解释业务背景"),
        background_context={"business_background_text": "测试背景", "business_background_name": "测试场景"},
        runtime_policy=_runtime_policy_for_lens(fake_runtime_child_task_creator),
        runtime_child_task_creator=fake_runtime_child_task_creator,
        coordinator=coordinator,
    )

    assert result["background_summary"] == "runtime background"
    assert result["author_mode"] == "codex_cli_runtime"
    assert result["runtime_state"] == "live"
    assert result["degradation_state"] == "none"
    assert result["artifact_source"] == "business_background_runtime_json"
    assert result["stage_id"] == "business_background_runtime"
    assert result["purpose"] == "business_background_runtime"
    assert any(event["stage_id"].startswith("runtime_child::business_background_runtime::") for event in coordinator.stage_events)


def test_business_background_falls_back_to_local_when_runtime_child_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    def fake_runtime_child_task_creator(
        request: CodexRunRequest,
        *,
        parent_report_id: str = "",
        parent_stage_id: str = "",
        child_index: int = 0,
        stage_id: str = "",
        purpose: str = "",
        artifact_source: str = "",
        stage_listener=None,
    ) -> dict[str, object]:
        return {
            "job_id": "codex-task-background-002",
            "parent_report_job_id": "report-task-parent-011",
            "parent_report_id": parent_report_id,
            "parent_stage_id": parent_stage_id,
            "child_index": child_index,
            "stage_id": stage_id,
            "purpose": purpose,
            "artifact_source": artifact_source,
            "status": "queued",
            "progress_percent": 0,
            "current_stage_id": "queued",
            "current_stage_title": "Task created",
            "current_stage_detail": "queued",
        }

    monkeypatch.setattr(report_service_module, "load_runtime_settings_raw", lambda: {"codex_runtime_enabled": True})
    monkeypatch.setattr(
        report_service_module,
        "get_codex_run_task",
        lambda job_id: {"job_id": job_id, "run_id": "run-background-002", "status": "failed"},
    )
    monkeypatch.setattr(
        report_service_module,
        "codex_business_background_analysis",
        lambda background_context: {
            **_business_background_payload("local background"),
            "mode": "fallback",
            "runtime_state": "fallback",
            "degradation_state": "hard_fallback",
        },
    )

    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="mixed_business_review",
        query_loop_id="report-loop-background-fallback",
    )
    result = report_service_module._business_background_with_optional_runtime(
        report_dir=report_dir,
        report_id="report-011",
        dataset_id="dataset-011",
        sheet_name="Sheet1",
        request=SmartReportRequest(user_requirement="请解释业务背景"),
        background_context={"business_background_text": "测试背景", "business_background_name": "测试场景"},
        runtime_policy=_runtime_policy_for_lens(fake_runtime_child_task_creator),
        runtime_child_task_creator=fake_runtime_child_task_creator,
        coordinator=coordinator,
    )

    assert result["background_summary"] == "local background"
    assert result["runtime_state"] == "fallback"
    assert any(event["stage_id"] == "business_background_runtime_fallback" for event in coordinator.stage_events)
