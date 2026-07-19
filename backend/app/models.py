from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field


RuntimePromptBuilder = Callable[[dict[str, Any]], str]
RuntimeWorkspacePathBuilder = Callable[[dict[str, Any]], str]
RuntimeContextPayloadBuilder = Callable[[dict[str, Any]], dict[str, Any]]
RuntimeFallbackRunner = Callable[[dict[str, Any]], dict[str, Any]]
RuntimeArtifactValidator = Callable[[dict[str, Any]], bool]
RuntimeArtifactNormalizer = Callable[[dict[str, Any]], dict[str, Any] | None]
RuntimeDirectRunner = Callable[["CodexRunRequest"], dict[str, Any]]


@dataclass(slots=True)
class RuntimeStageSpec:
    stage_id: str
    runtime_allowed: bool
    prompt_builder: RuntimePromptBuilder
    workspace_path_builder: RuntimeWorkspacePathBuilder
    expected_artifact_files: list[str] = field(default_factory=list)
    fallback_runner: RuntimeFallbackRunner | None = None
    timeout_sec: int = 180
    capture_git_diff: bool = False
    purpose: str = ""
    runtime_policy_alias: str = ""
    result_artifact_source: str = ""
    context_payload_builder: RuntimeContextPayloadBuilder | None = None
    artifact_validator: RuntimeArtifactValidator | None = None
    artifact_normalizer: RuntimeArtifactNormalizer | None = None
    direct_runtime_runner: RuntimeDirectRunner | None = None


class SheetSelectionRequest(BaseModel):
    sheet_name: str


class StatisticRequest(BaseModel):
    dataset_id: str
    analysis_type: Literal[
        "correlation",
        "pearson_correlation",
        "spearman_correlation",
        "kendall_tau",
        "partial_correlation",
        "distance_correlation",
        "point_biserial",
        "eta_squared",
        "descriptive_summary",
        "frequency_table",
        "cross_tabulation",
        "pivot_summary",
        "quantile_profile",
        "trimmed_mean",
        "winsorized_summary",
        "gini_coefficient",
        "pareto_analysis",
        "segmented_kpi_breakdown",
        "ols",
        "ridge_regression",
        "lasso_regression",
        "elastic_net",
        "robust_regression",
        "quantile_regression",
        "anova",
        "two_way_anova",
        "ancova",
        "logit",
        "random_forest",
        "neural_network",
        "deep_learning",
        "pca",
        "kmeans",
        "ttest",
        "paired_ttest",
        "one_sample_ttest",
        "z_test_mean",
        "ab_test",
        "repeated_measures_anova",
        "chi_square",
        "fisher_exact",
        "mcnemar",
        "cochran_q",
        "cmh_test",
        "cramers_v",
        "phi_coefficient",
        "theils_u",
        "goodman_kruskal_lambda",
        "cohens_kappa",
        "mann_whitney",
        "wilcoxon_signed_rank",
        "sign_test",
        "kruskal",
        "friedman",
        "mood_median",
        "ks_two_sample",
        "runs_test",
        "median_test",
        "fligner_killeen",
        "permutation_test",
        "bootstrap_ci",
        "poisson_glm",
        "normality",
        "shapiro_wilk",
        "dagostino_k2",
        "jarque_bera",
        "kolmogorov_smirnov_1samp",
        "anderson_darling",
        "breusch_pagan",
        "white_test",
        "durbin_watson",
        "moving_average",
        "autocorrelation",
        "partial_autocorrelation",
        "ljung_box",
        "adf_test",
        "tukey_hsd",
        "levene",
        "brown_forsythe",
        "bartlett",
        "welch_anova",
    ]
    target: str | None = None
    features: list[str] = Field(default_factory=list)
    group_column: str | None = None
    group_a: str | None = None
    group_b: str | None = None
    components: int = 2
    clusters: int = 3
    window: int = 3
    lag: int = 12
    regularization_strength: float = 1.0
    l1_ratio: float = 0.5
    quantile: float = 0.5
    bootstrap_iterations: int = 1000
    metric_type: Literal["auto", "continuous", "binary"] = "auto"
    alpha: float = 0.05
    hypothesis: Literal["two-sided", "larger", "smaller"] = "two-sided"
    test_value: float = 0.0
    population_std: float | None = None
    success_value: str | int | float | bool | None = None
    active_sheet: str | None = None


class AutoAnalysisRequest(BaseModel):
    dataset_id: str
    active_sheet: str | None = None
    user_goal: str = ""
    report_part: str = "auto"
    selected_report_parts: list[str] = Field(default_factory=list)
    max_methods: int = 24
    max_derived_fields: int = 64
    max_chart_points: int = 160
    selected_method_ids: list[str] = Field(default_factory=list)
    selected_derived_fields: list[str] = Field(default_factory=list)
    selected_fields: dict[str, Any] = Field(default_factory=dict)
    derived_metric_edits: list[dict[str, Any]] = Field(default_factory=list)
    method_field_bindings: dict[str, dict[str, Any]] = Field(default_factory=dict)
    method_run_specs: list[dict[str, Any]] = Field(default_factory=list)
    external_skill_ids: list[str] = Field(default_factory=list)
    external_skill_feature_selections: list[dict[str, Any]] = Field(default_factory=list)
    execution_mode: Literal["auto", "separate", "smart_merge"] = "smart_merge"
    cli_interpretation_enabled: bool = True
    business_interpretation_enabled: bool = True
    method_independent_output_enabled: bool = True
    smart_merge_enabled: bool = True


class LabExternalSkillInstallRequest(BaseModel):
    source_url: str = "https://github.com/anthropics/knowledge-work-plugins"
    ref: str = ""
    mount: bool = True


class LabExternalSkillLocalImportRequest(BaseModel):
    local_path: str = ""
    mount: bool = True


class LabFeatureTrialRunRequest(BaseModel):
    dataset_id: str
    active_sheet: str | None = None
    plugin_id: str
    feature_kind: Literal["command", "embedded_skill"]
    feature_id: str
    user_goal: str = ""


class LabReportAgentTeamLocalImportRequest(BaseModel):
    local_path: str = ""
    mount: bool = True


class LabReportAgentTeamRunRequest(BaseModel):
    report_id: str = ""
    dataset_id: str = ""
    sheet_name: str = ""
    workspace_path: str = ""
    user_requirement: str = ""
    team_ids: list[str] = Field(default_factory=list)


class LabMethodCardSaveRequest(BaseModel):
    base_method_id: str = ""
    name: str = ""
    description: str = ""
    family: str = "learned"
    output_types: list[str] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    field_bindings: dict[str, Any] = Field(default_factory=dict)
    selection_mode: Literal["fields", "all_rows", "object"] = "fields"
    object_selection: dict[str, Any] = Field(default_factory=dict)
    statistical_options: dict[str, Any] = Field(default_factory=dict)
    report_value_hooks: list[str] = Field(default_factory=list)
    usage_guidance: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_method: dict[str, Any] = Field(default_factory=dict)


class CodeExecutionRequest(BaseModel):
    dataset_id: str
    language: Literal["python", "sql", "r"] = "python"
    code: str
    active_sheet: str | None = None


class RuntimeSettingsRequest(BaseModel):
    api_key: str = ""
    model: str = "gpt-5.4"
    base_url: str = ""
    provider_label: str = "OpenAI"
    relay_note: str = "Blank Base URL uses the official OpenAI Responses API endpoint."
    rscript_path: str = ""
    reasoning_effort: Literal["minimal", "low", "medium", "high", "xhigh"] = "xhigh"
    codex_cli_path: str = "codex"
    codex_runtime_enabled: bool = False
    codex_workspace_root: str = ""
    codex_search_enabled: bool = False
    codex_timeout_sec: int = 1800
    codex_dangerously_bypass_approvals_and_sandbox: bool = False
    codex_use_login_auth: bool = True
    codex_runtime_api_enabled: bool = False


class RuntimeSettingsResponse(BaseModel):
    api_key_masked: str = ""
    has_api_key: bool = False
    model: str = "gpt-5.4"
    base_url: str = ""
    provider_label: str = "OpenAI"
    relay_note: str = "Blank Base URL uses the official OpenAI Responses API endpoint."
    rscript_path: str = ""
    reasoning_effort: Literal["minimal", "low", "medium", "high", "xhigh"] = "xhigh"
    codex_cli_path: str = "codex"
    codex_runtime_enabled: bool = False
    codex_workspace_root: str = ""
    codex_search_enabled: bool = False
    codex_timeout_sec: int = 1800
    codex_dangerously_bypass_approvals_and_sandbox: bool = False
    codex_use_login_auth: bool = True
    codex_runtime_api_enabled: bool = False


class SmartReportRequest(BaseModel):
    sheet_name: str | None = None
    selected_sheets: list[str] = Field(default_factory=list)
    multi_table_mode: Literal["single", "merge", "separate", "combined"] = "single"
    business_profile: Literal[
        "auto",
        "procurement_sales",
        "procurement_sales_report",
        "ecommerce_product_operations_report",
        "internet_operations_report",
        "media_campaign_report",
        "generic_business_report",
        "generic_long_business_report",
    ] = "auto"
    report_style: Literal["executive", "deep_dive"] = "deep_dive"
    report_language: Literal["zh-CN"] = "zh-CN"
    report_part: str = "auto"
    selected_report_parts: list[str] = Field(default_factory=list)
    user_requirement: str = ""
    problem_to_solve: str = ""
    target_audience: str = ""
    core_purpose: str = ""
    expected_result: str = ""
    key_constraints: str = ""
    historical_report_template_id: str = ""
    historical_report_text: str = ""
    historical_report_name: str = ""
    business_background_text: str = ""
    business_background_name: str = ""
    use_r_workflow: bool = False
    industry_research_standalone_enabled: bool = False
    enable_premium_pipeline: bool = False
    generate_full_table_version: bool = False
    enable_generic_business_runtime: bool = False
    premium_target: Literal["analyst_appendix"] = "analyst_appendix"
    premium_style_preset: str = "chinese_finance_editorial"
    chart_palette_preset: str = "cn_editorial_ink"
    chart_palette_colors: list[str] = Field(default_factory=list)
    visual_style_text: str = ""
    required_detail_dimensions_text: str = ""
    raw_user_requirement: str = ""
    raw_problem_to_solve: str = ""
    raw_target_audience: str = ""


class RWorkflowIntelligenceRequest(BaseModel):
    focus_question: str = ""
    target_audience: str = ""
    output_goal: str = ""


class CodexRunRequest(BaseModel):
    workspace_path: str
    prompt: str = ""
    prompt_template: str = ""
    user_requirement: str = ""
    context_payload: dict[str, Any] = Field(default_factory=dict)
    report_id: str = ""
    parent_report_id: str = ""
    parent_report_job_id: str = ""
    parent_stage_id: str = ""
    child_index: int = 0
    dataset_id: str = ""
    sheet_name: str = ""
    stage_id: str = ""
    purpose: str = "generic"
    artifact_source: str = ""
    model: str = ""
    search: bool = False
    timeout_sec: int = 1800
    capture_git_diff: bool = True
    resume_session_id: str = ""
    dangerously_bypass_approvals_and_sandbox: bool = False


class CodexTranscriptEntry(BaseModel):
    kind: str
    ts: str
    text: str = ""
    name: str = ""
    is_error: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)


class CodexRunResponse(BaseModel):
    run_id: str
    status: str
    workspace_path: str
    parent_report_id: str = ""
    parent_report_job_id: str = ""
    parent_stage_id: str = ""
    child_index: int = 0
    artifact_source: str = ""
    session_id: str = ""
    summary: str = ""
    changed_files: list[str] = Field(default_factory=list)
    git_diff_path: str = ""
    git_diff_url: str = ""
    transcript_path: str = ""
    transcript_url: str = ""
    stdout_path: str = ""
    stdout_url: str = ""
    stderr_path: str = ""
    stderr_url: str = ""
    summary_path: str = ""
    summary_url: str = ""
    created_at: str
    updated_at: str
    error: str = ""
    transcript_entry_count: int = 0


class CodexRunTaskResponse(BaseModel):
    job_id: str
    run_id: str = ""
    parent_report_job_id: str = ""
    parent_report_id: str = ""
    parent_stage_id: str = ""
    child_index: int = 0
    stage_id: str = ""
    purpose: str = ""
    artifact_source: str = ""
    status: str
    progress_percent: int
    current_stage_id: str = ""
    current_stage_title: str = ""
    current_stage_detail: str = ""
    created_at: str
    updated_at: str
    error: str = ""


class CodexPipelineRequest(BaseModel):
    pipeline_type: Literal[
        "r_workflow_premium_pdf",
        "analyst_appendix_premium_pdf",
        "generic_long_cli_pipeline",
        "ecommerce_long_cli_pipeline",
        "procurement_sales_long_cli_pipeline",
        "internet_ops_long_cli_pipeline",
        "multi_table_generic_long_cli_pipeline",
        "historical_style_report_cli_pipeline",
    ] = "r_workflow_premium_pdf"
    workspace_path: str
    linked_report_id: str = ""
    session_id: str = ""
    style_preset: str = "chinese_finance_editorial"
    language: Literal["zh-CN"] = "zh-CN"
    report_goal: str = "business_deep_analysis"
    target_audience: str = "management"
    analysis_mode: str = "business_deep_analysis"
    business_focus: str = ""
    user_requirement: str = ""
    context_payload: dict[str, Any] = Field(default_factory=dict)
    auto_start: bool = True


class CodexPipelineRetryRequest(BaseModel):
    stage_id: str
    auto_start: bool = True


class CodexPipelineResponse(BaseModel):
    pipeline_job_id: str
    pipeline_type: str
    workspace_path: str
    status: str
    session_id: str = ""
    progress_percent: int = 0
    current_stage_id: str = ""
    current_stage_title: str = ""
    current_stage_detail: str = ""
    linked_report_id: str = ""
    linked_codex_run_ids: list[str] = Field(default_factory=list)
    error: str = ""
    created_at: str = ""
    updated_at: str = ""
    artifact_index: list[dict[str, Any]] = Field(default_factory=list)
    final_output: dict[str, Any] = Field(default_factory=dict)


class ReportAgentSessionCreateRequest(BaseModel):
    title: str = ""


class ReportAgentMessageRequest(BaseModel):
    message: str


class ReportAgentPublishRequest(BaseModel):
    note: str = ""


class ReportAnnotationRequest(BaseModel):
    annotation_id: str = ""
    artifact_url: str
    artifact_name: str = ""
    artifact_id: str = ""
    artifact_source: str = ""
    artifact_type: Literal["html", "pdf"]
    coordinate_version: int = 2
    coordinate_space: str = ""
    page_number: int | None = None
    target_kind: Literal["page", "html"] = "page"
    points: list[dict[str, float]] = Field(default_factory=list)
    shape: Literal["pen", "rectangle", "highlight"] = "rectangle"
    color: str = "#f97316"
    stroke_width: float = 2
    scroll_offset: float = 0
    viewport_width: float = 0
    viewport_height: float = 0
    document_width: float = 0
    document_height: float = 0
    page_width: float = 0
    page_height: float = 0
    render_scale: float = 1
    preview_zoom: float = 1
    note: str = ""
