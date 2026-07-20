from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import re

from fastapi import FastAPI, File, UploadFile
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.models import (
    AutoAnalysisRequest,
    CodexPipelineRequest,
    CodexPipelineRetryRequest,
    CodexRunRequest,
    LabMethodCardSaveRequest,
    LabExternalSkillLocalImportRequest,
    LabExternalSkillInstallRequest,
    LabFeatureTrialRunRequest,
    LabReportAgentTeamLocalImportRequest,
    LabReportAgentTeamRunRequest,
    RWorkflowIntelligenceRequest,
    ReportAgentMessageRequest,
    ReportAnnotationRequest,
    ReportAgentPublishRequest,
    ReportAgentSessionCreateRequest,
    SheetSelectionRequest,
    SmartReportRequest,
    StatisticRequest,
)
from app.services.codex_cli_resolver_service import codex_cli_health
from app.services.codex_runtime_learning_ledger_service import (
    get_learning_ledger_entry,
    list_learning_ledger_entries,
)
from app.services.path_service import (
    BUSINESS_BACKGROUNDS_DIR,
    DATASETS_DIR,
    HISTORICAL_REPORTS_DIR,
    PUBLIC_ARTIFACTS_DIR,
    REPORTS_DIR,
    RUNS_DIR,
    STORAGE_DIR,
    frontend_dist_dir,
)
from app.services.report_agent_session_service import (
    cancel_report_agent_turn,
    create_report_agent_session,
    delete_report_agent_session_attachment,
    delete_report_agent_session_annotation,
    get_report_agent_session_diff,
    list_report_agent_session_files,
    get_report_agent_session,
    get_report_detail,
    iter_report_agent_session_sse,
    list_report_agent_session_attachments,
    list_report_agent_session_annotations,
    list_report_agent_session_events,
    list_reports,
    post_report_agent_message,
    publish_report_agent_session,
    upload_report_agent_session_attachment,
    upsert_report_agent_session_annotation,
)
from app.services.lab_external_skill_service import list_mounted_lab_external_skills
from app.services.skill_mount_service import get_mounted_skills
from app.services.settings_service import load_runtime_settings
from app.services.statistical_catalog import get_catalog_summary, get_statistical_catalog


def _ensure_storage() -> None:
    for directory in [
        STORAGE_DIR,
        PUBLIC_ARTIFACTS_DIR,
        DATASETS_DIR,
        RUNS_DIR,
        REPORTS_DIR,
        HISTORICAL_REPORTS_DIR,
        BUSINESS_BACKGROUNDS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


_ensure_storage()

app = FastAPI(
    title="Asteria Analyst Engine",
    version="0.1.0",
    description="Backend for a full-stack data analysis agent.",
)

app.add_middleware(GZipMiddleware, minimum_size=2048)

def _cors_allow_origins() -> list[str]:
    configured = os.getenv("ASTERIA_CORS_ALLOW_ORIGINS", "")
    origins = [item.strip().rstrip("/") for item in configured.split(",") if item.strip()]
    return origins or ["http://localhost:3000", "http://127.0.0.1:3000"]


def _cors_allow_origin_regex() -> str | None:
    return os.getenv("ASTERIA_CORS_ALLOW_ORIGIN_REGEX") or r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?"


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_origin_regex=_cors_allow_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory=PUBLIC_ARTIFACTS_DIR), name="storage")


@app.on_event("startup")
def _start_analysis_lab_pdca_scheduler() -> None:
    from app.services.analysis_lab_pdca_service import start_analysis_lab_pdca_scheduler

    start_analysis_lab_pdca_scheduler(run_immediately=False)


@app.on_event("shutdown")
def _stop_analysis_lab_pdca_scheduler() -> None:
    from app.services.analysis_lab_pdca_service import stop_analysis_lab_pdca_scheduler

    stop_analysis_lab_pdca_scheduler()


def _mounted_skill_payload() -> dict[str, object]:
    curated = get_mounted_skills()
    external = list_mounted_lab_external_skills()
    skills = [*curated, *external]
    return {
        "summary": {
            "count": len(skills),
            "curated_count": len(curated),
            "external_count": len(external),
            "skill_ids": [str(item.get("id") or "") for item in skills if item.get("id")],
        },
        "skills": skills,
    }


def _require_codex_runtime_api_enabled() -> None:
    settings = load_runtime_settings()
    if settings.codex_runtime_api_enabled:
        return
    raise HTTPException(
        status_code=403,
        detail=(
            "Codex runtime API is disabled. "
            "Set ASTERIA_ENABLE_CODEX_RUNTIME_API=1 to enable /api/codex-runs and /api/codex-run-jobs."
        ),
    )


def _require_local_skill_installer_enabled() -> None:
    enabled = str(os.getenv("ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER", "")).strip().lower()
    if enabled in {"1", "true", "yes", "on"}:
        return
    raise HTTPException(
        status_code=403,
        detail={
            "code": "SKILL_INSTALLATION_DISABLED",
            "message": (
                "Lab skill installation and execution are disabled. "
                "Set ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1 to enable them."
            ),
        },
    )


def _safe_export_segment(value: str, fallback: str = "default") -> str:
    segment = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return segment[:80] or fallback


def _auto_analysis_export_paths(payload: AutoAnalysisRequest, *, surface: str) -> tuple[Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dataset = _safe_export_segment(payload.dataset_id, "dataset")
    sheet = _safe_export_segment(payload.active_sheet or "sheet", "sheet")
    part = _safe_export_segment(payload.report_part or "auto", "auto")
    relative = Path("auto-analysis") / dataset / f"{stamp}-{surface}-{sheet}-{part}"
    return PUBLIC_ARTIFACTS_DIR / relative, f"/storage/{relative.as_posix()}"


INTEGRATIONS = [
    {
        "name": "Next.js",
        "repo": "https://github.com/vercel/next.js",
        "purpose": "high-end front-end application shell",
    },
    {
        "name": "FastAPI",
        "repo": "https://github.com/fastapi/fastapi",
        "purpose": "API and orchestration layer",
    },
    {
        "name": "Apache ECharts",
        "repo": "https://github.com/apache/echarts",
        "purpose": "interactive visual analytics",
    },
    {
        "name": "Monaco Editor",
        "repo": "https://github.com/microsoft/monaco-editor",
        "purpose": "embedded code studio",
    },
    {
        "name": "DuckDB",
        "repo": "https://github.com/duckdb/duckdb",
        "purpose": "analytical SQL engine",
    },
    {
        "name": "scikit-learn",
        "repo": "https://github.com/scikit-learn/scikit-learn",
        "purpose": "machine learning and clustering",
    },
    {
        "name": "statsmodels",
        "repo": "https://github.com/statsmodels/statsmodels",
        "purpose": "regression, inference, and statistical tests",
    },
]


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/manifest")
def manifest() -> dict[str, object]:
    from app.services.market_intelligence_service import get_market_ecosystem_summary

    catalog_summary = get_catalog_summary()
    return {
        "product": "Asteria Analyst",
        "integrations": INTEGRATIONS,
        "supported_uploads": [".xlsx", ".csv", ".tsv", ".dta"],
        "supported_historical_reports": [".txt", ".md", ".html", ".pdf", ".docx"],
        "supported_business_backgrounds": [".txt", ".md", ".html", ".pdf", ".docx", ".xlsx", ".csv", ".tsv"],
        "supported_languages": ["python", "sql", "r"],
        "analysis_types": [
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
        ],
        "workflow_capabilities": [
            "multi-sheet fingerprinting",
            "candidate key detection",
            "cross-sheet relationship inference",
            "quality alerts",
            "analysis route recommendation",
        ],
        "runtime_configuration": [
            "api_key",
            "model",
            "base_url",
            "provider_label",
            "relay_note",
            "rscript_path",
            "codex_cli_path",
            "codex_runtime_enabled",
            "codex_workspace_root",
            "codex_runtime_api_enabled",
        ],
        "report_capabilities": [
            "executive summary",
            "quality audit",
            "relationship mapping",
            "predictive analysis",
            "segmentation",
            "experiment opportunity scan",
            "market landscape analysis",
            "tableau/stata/r handoff artifacts",
            "optional r workflow folder",
            "historical report adaptation",
        ],
        "statistics_catalog": catalog_summary,
        "market_ecosystem_summary": get_market_ecosystem_summary(),
        "mounted_skills_summary": _mounted_skill_payload()["summary"],
    }


@app.get("/api/ecosystem/market")
def market_ecosystem() -> dict[str, object]:
    from app.services.market_intelligence_service import get_market_ecosystem_catalog, get_market_ecosystem_summary

    return {
        "summary": get_market_ecosystem_summary(),
        "tools": get_market_ecosystem_catalog(),
    }


@app.get("/api/skills/mounted")
def mounted_skills() -> dict[str, object]:
    return _mounted_skill_payload()


@app.get("/api/lab/skills")
def lab_external_skills() -> dict[str, object]:
    from app.services.lab_external_skill_service import list_lab_external_skills

    return list_lab_external_skills()


@app.post("/api/lab/skills/install")
def install_lab_external_skill(payload: LabExternalSkillInstallRequest) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_external_skill_service import install_lab_external_skills

    try:
        return install_lab_external_skills(payload.source_url, payload.ref or None, mount=payload.mount)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lab/skills/import-local")
def import_local_lab_external_skill(payload: LabExternalSkillLocalImportRequest) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_external_skill_service import import_lab_external_skill_from_local_path

    try:
        return import_lab_external_skill_from_local_path(payload.local_path, mount=payload.mount)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lab/skills/{skill_id}/mount")
def mount_lab_external_skill(skill_id: str) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_external_skill_service import set_lab_external_skill_mounted

    try:
        return set_lab_external_skill_mounted(skill_id, True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/lab/skills/{skill_id}/unmount")
def unmount_lab_external_skill(skill_id: str) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_external_skill_service import set_lab_external_skill_mounted

    try:
        return set_lab_external_skill_mounted(skill_id, False)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/lab/skills/{skill_id}")
def remove_lab_external_skill(skill_id: str) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_external_skill_service import delete_lab_external_skill

    try:
        return delete_lab_external_skill(skill_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/lab/feature-trials/catalog")
def lab_feature_trial_catalog() -> dict[str, object]:
    from app.services.lab_feature_trial_service import list_lab_feature_trial_catalog

    return list_lab_feature_trial_catalog()


@app.post("/api/lab/feature-trials/run")
def run_lab_feature_trial_endpoint(payload: LabFeatureTrialRunRequest) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_feature_trial_service import run_lab_feature_trial

    try:
        return run_lab_feature_trial(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/lab/report-agent-teams")
def lab_report_agent_teams() -> dict[str, object]:
    from app.services.lab_report_agent_team_service import list_lab_report_agent_teams

    return list_lab_report_agent_teams()


@app.post("/api/lab/report-agent-teams/import-local")
def import_local_lab_report_agent_team(payload: LabReportAgentTeamLocalImportRequest) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_report_agent_team_service import import_lab_report_agent_team_from_local_path

    try:
        return import_lab_report_agent_team_from_local_path(payload.local_path, mount=payload.mount)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lab/report-agent-teams/{team_id}/mount")
def mount_lab_report_agent_team(team_id: str) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_report_agent_team_service import set_lab_report_agent_team_mounted

    try:
        return set_lab_report_agent_team_mounted(team_id, True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/lab/report-agent-teams/{team_id}/unmount")
def unmount_lab_report_agent_team(team_id: str) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_report_agent_team_service import set_lab_report_agent_team_mounted

    try:
        return set_lab_report_agent_team_mounted(team_id, False)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/lab/report-agent-teams/{team_id}")
def delete_lab_report_agent_team(team_id: str) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_report_agent_team_service import delete_lab_report_agent_team

    try:
        return delete_lab_report_agent_team(team_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/lab/report-agent-teams/run")
def run_lab_report_agent_team(payload: LabReportAgentTeamRunRequest) -> dict[str, object]:
    _require_local_skill_installer_enabled()
    from app.services.lab_report_agent_team_service import launch_lab_report_agent_team_run

    try:
        return launch_lab_report_agent_team_run(
            report_id=payload.report_id,
            dataset_id=payload.dataset_id,
            sheet_name=payload.sheet_name,
            workspace_path=payload.workspace_path,
            user_requirement=payload.user_requirement,
            team_ids=payload.team_ids,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/statistics/catalog")
def statistics_catalog() -> dict[str, object]:
    return {
        "summary": get_catalog_summary(),
        "methods": get_statistical_catalog(),
    }


@app.get("/api/runtime-settings")
def get_runtime_settings() -> dict[str, object]:
    return load_runtime_settings().model_dump()


@app.get("/api/runtime/codex-health")
def get_codex_runtime_health() -> dict[str, object]:
    return codex_cli_health()


@app.get("/api/datasets")
def datasets(compact: bool = False) -> Response:
    from app.services.dataset_catalog_service import list_datasets

    payload = json.dumps(
        {"datasets": list_datasets(compact=compact)},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return Response(content=payload, media_type="application/json")


@app.get("/api/historical-reports")
def historical_reports(compact: bool = False) -> dict[str, object]:
    from app.services.historical_report_service import list_historical_reports

    return {"templates": list_historical_reports(compact=compact)}


@app.get("/api/business-backgrounds")
def business_backgrounds(compact: bool = False) -> dict[str, object]:
    from app.services.business_background_service import list_business_backgrounds

    return {"contexts": list_business_backgrounds(compact=compact)}


@app.get("/api/historical-reports/{template_id}")
def historical_report_detail(template_id: str) -> dict[str, object]:
    from app.services.historical_report_service import load_historical_report

    return load_historical_report(template_id)


@app.get("/api/business-backgrounds/{context_id}")
def business_background_detail(context_id: str) -> dict[str, object]:
    from app.services.business_background_service import load_business_background

    return load_business_background(context_id)


@app.get("/api/datasets/{dataset_id}")
def dataset_detail(dataset_id: str, summary: bool = False) -> dict[str, object]:
    if summary:
        from app.services.dataset_catalog_service import get_dataset_summary

        payload = get_dataset_summary(dataset_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        return payload

    from app.services.dataset_service import load_dataset_metadata

    return load_dataset_metadata(dataset_id)


@app.get("/api/datasets/{dataset_id}/workflow")
def dataset_workflow(dataset_id: str) -> dict[str, object]:
    from app.services.workflow_service import build_workflow_blueprint

    return build_workflow_blueprint(dataset_id)


@app.post("/api/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)) -> dict[str, object]:
    from app.services.dataset_service import persist_dataset

    return await persist_dataset(file)


@app.post("/api/historical-reports/upload")
async def upload_historical_report(file: UploadFile = File(...)) -> dict[str, object]:
    from app.services.historical_report_service import persist_historical_report

    return await persist_historical_report(file)


@app.post("/api/business-backgrounds/upload")
async def upload_business_background(file: UploadFile = File(...)) -> dict[str, object]:
    from app.services.business_background_service import persist_business_background

    return await persist_business_background(file)


@app.post("/api/datasets/{dataset_id}/sheet")
def set_active_sheet(dataset_id: str, payload: SheetSelectionRequest) -> dict[str, object]:
    from app.services.dataset_service import activate_sheet

    return activate_sheet(dataset_id, payload.sheet_name)


@app.post("/api/statistics/run")
def statistics(payload: StatisticRequest) -> dict[str, object]:
    from app.services.analysis_service import run_statistical_analysis
    from app.services.dataset_service import load_dataset_frame

    frame, _, _ = load_dataset_frame(payload.dataset_id, payload.active_sheet)
    return run_statistical_analysis(frame, payload)


@app.get("/api/analysis/auto/methods")
def auto_analysis_methods(compact: bool = False) -> dict[str, object]:
    from app.services.auto_analysis_registry_service import auto_analysis_method_catalog

    return auto_analysis_method_catalog(compact=compact)


@app.post("/api/analysis/auto")
def auto_analysis(payload: AutoAnalysisRequest) -> dict[str, object]:
    from app.services.auto_analysis_service import run_auto_analysis
    from app.services.dataset_service import load_dataset_frame

    frame, metadata, sheet = load_dataset_frame(payload.dataset_id, payload.active_sheet)
    export_dir, public_base_path = _auto_analysis_export_paths(payload, surface="analysis-auto")
    return run_auto_analysis(
        frame,
        payload,
        dataset_name=str(metadata.get("name") or metadata.get("filename") or ""),
        sheet_name=str((sheet or {}).get("name") or payload.active_sheet or ""),
        export_dir=export_dir,
        public_base_path=public_base_path,
    )


@app.get("/api/lab/methods")
def lab_methods(compact: bool = True) -> dict[str, object]:
    from app.services.auto_analysis_registry_service import auto_analysis_method_catalog

    payload = auto_analysis_method_catalog(compact=compact)
    payload["surface"] = "lab"
    return payload


@app.post("/api/lab/method-cards")
def save_lab_method_card_endpoint(payload: LabMethodCardSaveRequest) -> dict[str, object]:
    from app.services.auto_analysis_registry_service import save_lab_method_card

    return save_lab_method_card(payload)


@app.get("/api/lab/pdca/status")
def lab_pdca_status() -> dict[str, object]:
    from app.services.analysis_lab_pdca_service import get_analysis_lab_pdca_status

    return get_analysis_lab_pdca_status()


@app.post("/api/lab/pdca/run")
def lab_pdca_run() -> dict[str, object]:
    from app.services.analysis_lab_pdca_service import run_analysis_lab_pdca_cycle

    return run_analysis_lab_pdca_cycle(trigger="manual_api")


@app.post("/api/lab/run")
def lab_run(payload: AutoAnalysisRequest) -> dict[str, object]:
    from app.services.auto_analysis_service import run_auto_analysis
    from app.services.dataset_service import load_dataset_frame

    frame, metadata, sheet = load_dataset_frame(payload.dataset_id, payload.active_sheet)
    export_dir, public_base_path = _auto_analysis_export_paths(payload, surface="lab-run")
    return run_auto_analysis(
        frame,
        payload,
        dataset_name=str(metadata.get("name") or metadata.get("filename") or ""),
        sheet_name=str((sheet or {}).get("name") or payload.active_sheet or ""),
        export_dir=export_dir,
        public_base_path=public_base_path,
    )


@app.post("/api/datasets/{dataset_id}/smart-report")
def smart_report(dataset_id: str, payload: SmartReportRequest) -> dict[str, object]:
    from app.services.report_service import generate_smart_report

    return generate_smart_report(dataset_id, payload)


@app.post("/api/datasets/{dataset_id}/smart-report-jobs")
def create_smart_report_job(dataset_id: str, payload: SmartReportRequest) -> dict[str, object]:
    from app.services.report_task_service import create_report_task

    return create_report_task(dataset_id, payload)


@app.get("/api/report-jobs/{job_id}")
def report_job_status(job_id: str) -> dict[str, object]:
    from app.services.report_task_service import get_report_task

    try:
        return get_report_task(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Report job not found.") from exc


@app.get("/api/reports")
def report_catalog(
    limit: int = 80,
    offset: int = 0,
    q: str = "",
    dataset_id: str = "",
    business_profile: str = "",
    sort_by: str = "updated_at",
    refresh_index: bool = False,
) -> dict[str, object]:
    return list_reports(
        limit=limit,
        offset=offset,
        keyword=q,
        dataset_id=dataset_id,
        business_profile=business_profile,
        sort_by=sort_by,
        refresh_index=refresh_index,
    )


@app.get("/api/reports/{report_id}")
def report_detail(report_id: str) -> dict[str, object]:
    return get_report_detail(report_id)


@app.post("/api/reports/{report_id}/agent-sessions")
def create_report_agent_workbench_session(
    report_id: str,
    payload: ReportAgentSessionCreateRequest,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return create_report_agent_session(report_id, title=payload.title)


@app.get("/api/reports/{report_id}/agent-sessions/{session_id}")
def report_agent_workbench_session(report_id: str, session_id: str) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return get_report_agent_session(report_id, session_id)


@app.post("/api/report-agent-sessions/{session_id}/messages")
def post_report_agent_workbench_message(
    session_id: str,
    payload: ReportAgentMessageRequest,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return post_report_agent_message(report_id, session_id, message=payload.message)


@app.get("/api/report-agent-sessions/{session_id}/events")
def report_agent_workbench_events(
    session_id: str,
    report_id: str,
    cursor: int = 0,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return list_report_agent_session_events(report_id, session_id, cursor=cursor)


@app.post("/api/report-agent-sessions/{session_id}/cancel")
def cancel_report_agent_workbench_turn(
    session_id: str,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return cancel_report_agent_turn(report_id, session_id)


@app.get("/api/report-agent-sessions/{session_id}/files")
def report_agent_workbench_files(
    session_id: str,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return list_report_agent_session_files(report_id, session_id)


@app.get("/api/report-agent-sessions/{session_id}/diff")
def report_agent_workbench_diff(
    session_id: str,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return get_report_agent_session_diff(report_id, session_id)


@app.get("/api/report-agent-sessions/{session_id}/attachments")
def report_agent_workbench_attachments(
    session_id: str,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return list_report_agent_session_attachments(report_id, session_id)


@app.post("/api/report-agent-sessions/{session_id}/attachments")
async def upload_report_agent_workbench_attachment(
    session_id: str,
    report_id: str,
    file: UploadFile = File(...),
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    data = await file.read()
    return upload_report_agent_session_attachment(
        report_id,
        session_id,
        filename=file.filename or "attachment",
        content_type=file.content_type or "",
        data=data,
    )


@app.delete("/api/report-agent-sessions/{session_id}/attachments/{attachment_id}")
def delete_report_agent_workbench_attachment(
    session_id: str,
    attachment_id: str,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return delete_report_agent_session_attachment(report_id, session_id, attachment_id)


@app.get("/api/report-agent-sessions/{session_id}/annotations")
def report_agent_workbench_annotations(
    session_id: str,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return list_report_agent_session_annotations(report_id, session_id)


@app.post("/api/report-agent-sessions/{session_id}/annotations")
def upsert_report_agent_workbench_annotation(
    session_id: str,
    payload: ReportAnnotationRequest,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return upsert_report_agent_session_annotation(report_id, session_id, payload.model_dump())


@app.delete("/api/report-agent-sessions/{session_id}/annotations/{annotation_id}")
def delete_report_agent_workbench_annotation(
    session_id: str,
    annotation_id: str,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return delete_report_agent_session_annotation(report_id, session_id, annotation_id)


@app.get("/api/report-agent-sessions/{session_id}/events/stream")
def report_agent_workbench_event_stream(
    session_id: str,
    report_id: str,
    cursor: int = 0,
) -> StreamingResponse:
    _require_codex_runtime_api_enabled()
    return StreamingResponse(
        iter_report_agent_session_sse(report_id, session_id, cursor=cursor),
        media_type="text/event-stream",
    )


@app.post("/api/report-agent-sessions/{session_id}/publish")
def publish_report_agent_workbench_session(
    session_id: str,
    payload: ReportAgentPublishRequest,
    report_id: str,
) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    _ = payload
    return publish_report_agent_session(report_id, session_id)


@app.get("/api/runtime/processes")
def runtime_processes(report_id: str = "", session_id: str = "", scope: str = "", limit: int = 160) -> dict[str, object]:
    from app.services.runtime_process_service import list_active_runtime_processes, list_runtime_processes

    _require_codex_runtime_api_enabled()
    if scope == "active" or not report_id:
        return list_active_runtime_processes(limit=limit)
    return list_runtime_processes(report_id, session_id=session_id)


@app.post("/api/runtime/processes/{kind}/{process_id}/cancel")
def cancel_runtime_process_endpoint(kind: str, process_id: str, report_id: str, session_id: str = "") -> dict[str, object]:
    from app.services.runtime_process_service import cancel_runtime_process

    _require_codex_runtime_api_enabled()
    return cancel_runtime_process(kind, process_id, report_id=report_id, session_id=session_id)


@app.post("/api/runtime/processes/{kind}/{process_id}/resume")
def resume_runtime_process_endpoint(kind: str, process_id: str, report_id: str, session_id: str = "") -> dict[str, object]:
    from app.services.runtime_process_service import resume_runtime_process

    _require_codex_runtime_api_enabled()
    return resume_runtime_process(kind, process_id, report_id=report_id, session_id=session_id)


@app.post("/api/reports/{report_id}/r-intelligence-flow")
def r_intelligence_flow(report_id: str, payload: RWorkflowIntelligenceRequest) -> dict[str, object]:
    from app.services.r_artifact_intelligence_service import run_r_artifact_intelligence_flow

    try:
        return run_r_artifact_intelligence_flow(report_id, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/codex-runs")
def create_codex_run(payload: CodexRunRequest) -> dict[str, object]:
    from app.services.codex_runtime_service import run_headless_codex

    _require_codex_runtime_api_enabled()
    return run_headless_codex(payload)


@app.post("/api/codex-run-jobs")
def create_codex_run_job(payload: CodexRunRequest) -> dict[str, object]:
    from app.services.codex_runtime_task_service import create_codex_run_task

    _require_codex_runtime_api_enabled()
    return create_codex_run_task(payload)


@app.get("/api/codex-run-jobs/{job_id}")
def codex_run_job_status(job_id: str) -> dict[str, object]:
    from app.services.codex_runtime_task_service import get_codex_run_task

    _require_codex_runtime_api_enabled()
    return get_codex_run_task(job_id)


@app.get("/api/codex-runs/{run_id}")
def codex_run_detail(run_id: str) -> dict[str, object]:
    from app.services.codex_runtime_service import get_codex_run

    _require_codex_runtime_api_enabled()
    return get_codex_run(run_id)


@app.get("/api/codex-runs/{run_id}/log")
def codex_run_log(run_id: str, offset: int = 0, limit_bytes: int = 256000) -> dict[str, object]:
    from app.services.codex_runtime_service import read_codex_run_log

    _require_codex_runtime_api_enabled()
    return read_codex_run_log(run_id, offset=offset, limit_bytes=limit_bytes)


@app.post("/api/codex-runs/{run_id}/cancel")
def cancel_codex_runtime_run(run_id: str) -> dict[str, object]:
    from app.services.codex_runtime_service import cancel_codex_run

    _require_codex_runtime_api_enabled()
    return cancel_codex_run(run_id)


@app.post("/api/codex-run-jobs/{job_id}/cancel")
def cancel_codex_runtime_job(job_id: str) -> dict[str, object]:
    from app.services.codex_runtime_task_service import cancel_codex_run_task

    _require_codex_runtime_api_enabled()
    return cancel_codex_run_task(job_id)


@app.get("/api/runtime-learning-ledger")
def runtime_learning_ledger(limit: int = 100, source_type: str = "", status: str = "") -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    return {
        "entries": list_learning_ledger_entries(limit=limit, source_type=source_type, status=status),
        "limit": max(1, min(int(limit or 100), 500)),
        "source_type": source_type,
        "status": status,
    }


@app.get("/api/runtime-learning-ledger/{entry_id}")
def runtime_learning_ledger_detail(entry_id: str) -> dict[str, object]:
    _require_codex_runtime_api_enabled()
    try:
        return get_learning_ledger_entry(entry_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/codex-pipeline-jobs")
def create_codex_pipeline_job(payload: CodexPipelineRequest) -> dict[str, object]:
    from app.services.codex_runtime_pipeline_service import create_pipeline_job

    _require_codex_runtime_api_enabled()
    context_payload = dict(payload.context_payload or {})
    context_payload.update(
        {
            "style_preset": payload.style_preset,
            "language": payload.language,
            "report_goal": payload.report_goal,
            "target_audience": payload.target_audience,
            "analysis_mode": payload.analysis_mode,
            "business_focus": payload.business_focus,
            "user_requirement": payload.user_requirement,
            "visual_style": payload.context_payload.get("visual_style", ""),
            "color_palette": payload.context_payload.get("color_palette", payload.style_preset),
            "layout_preference": payload.context_payload.get("layout_preference", ""),
            "pdf_design_brief": payload.context_payload.get("pdf_design_brief", ""),
            "required_detail_dimensions": payload.context_payload.get("required_detail_dimensions", []),
            "reader_facing_mode": "business_report",
            "internal_grounding_mode": "guardrail_only",
        }
    )
    return create_pipeline_job(
        pipeline_type=payload.pipeline_type,
        workspace_path=payload.workspace_path,
        linked_report_id=payload.linked_report_id,
        session_id=payload.session_id,
        context_payload=context_payload,
        auto_start=payload.auto_start,
    )


@app.get("/api/codex-pipeline-jobs/{job_id}")
def codex_pipeline_job_status(job_id: str) -> dict[str, object]:
    from app.services.codex_runtime_pipeline_service import get_pipeline_job

    _require_codex_runtime_api_enabled()
    return get_pipeline_job(job_id)


@app.post("/api/codex-pipeline-jobs/{job_id}/cancel")
def cancel_codex_pipeline_runtime_job(job_id: str) -> dict[str, object]:
    from app.services.codex_runtime_pipeline_service import cancel_pipeline_job

    _require_codex_runtime_api_enabled()
    return cancel_pipeline_job(job_id)


@app.post("/api/codex-pipeline-jobs/{job_id}/retry-stage")
def retry_codex_pipeline_stage(job_id: str, payload: CodexPipelineRetryRequest) -> dict[str, object]:
    from app.services.codex_runtime_pipeline_service import retry_pipeline_stage

    _require_codex_runtime_api_enabled()
    return retry_pipeline_stage(job_id, stage_id=payload.stage_id, auto_start=payload.auto_start)


@app.post("/api/codex-pipeline-jobs/{job_id}/register-report-output")
def register_codex_pipeline_report_output(job_id: str) -> dict[str, object]:
    from app.services.report_task_service import register_codex_pipeline_output_for_report_task

    _require_codex_runtime_api_enabled()
    try:
        return register_codex_pipeline_output_for_report_task(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _serve_frontend_file(relative_path: str) -> FileResponse:
    frontend_dir = frontend_dist_dir()
    if not frontend_dir.exists():
        raise HTTPException(status_code=404, detail="Frontend assets are unavailable.")

    resolved_frontend_dir = frontend_dir.resolve()
    target_path = (frontend_dir / relative_path).resolve()
    try:
        target_path.relative_to(resolved_frontend_dir)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Frontend asset not found.") from exc

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="Frontend asset not found.")

    return FileResponse(target_path)


@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
def home_entry() -> FileResponse:
    return _serve_frontend_file("index.html")


@app.get("/analysis", include_in_schema=False)
@app.get("/analysis/", include_in_schema=False)
@app.head("/analysis", include_in_schema=False)
@app.head("/analysis/", include_in_schema=False)
def analysis_entry() -> FileResponse:
    return _serve_frontend_file("analysis.html")


# Next static exports store route RSC payloads in nested directories, while the
# client-side router requests their flattened URL form. Serve the exported files
# through stable aliases so portable navigation has no missing-resource fallback.
@app.get("/analysis/__next.analysis.__PAGE__.txt", include_in_schema=False)
def analysis_rsc_entry() -> FileResponse:
    return _serve_frontend_file("analysis/__next.analysis/__PAGE__.txt")


@app.get("/lab", include_in_schema=False)
@app.get("/lab/", include_in_schema=False)
@app.head("/lab", include_in_schema=False)
@app.head("/lab/", include_in_schema=False)
def lab_entry() -> FileResponse:
    return _serve_frontend_file("lab.html")


@app.get("/lab/__next.lab.__PAGE__.txt", include_in_schema=False)
def lab_rsc_entry() -> FileResponse:
    return _serve_frontend_file("lab/__next.lab/__PAGE__.txt")


@app.get("/lab/method-guide", include_in_schema=False)
@app.get("/lab/method-guide/", include_in_schema=False)
@app.head("/lab/method-guide", include_in_schema=False)
@app.head("/lab/method-guide/", include_in_schema=False)
def lab_method_guide_entry() -> FileResponse:
    return _serve_frontend_file("lab/method-guide.html")


@app.get("/lab/method-guide/__next.lab.method-guide.__PAGE__.txt", include_in_schema=False)
def lab_method_guide_rsc_entry() -> FileResponse:
    return _serve_frontend_file("lab/method-guide/__next.lab/method-guide/__PAGE__.txt")


@app.get("/revision", include_in_schema=False)
@app.get("/revision/", include_in_schema=False)
@app.head("/revision", include_in_schema=False)
@app.head("/revision/", include_in_schema=False)
def revision_entry() -> FileResponse:
    return _serve_frontend_file("revision.html")


@app.get("/revision/__next.revision.__PAGE__.txt", include_in_schema=False)
def revision_rsc_entry() -> FileResponse:
    return _serve_frontend_file("revision/__next.revision/__PAGE__.txt")


@app.get("/revision/workspace", include_in_schema=False)
@app.get("/revision/workspace/", include_in_schema=False)
@app.head("/revision/workspace", include_in_schema=False)
@app.head("/revision/workspace/", include_in_schema=False)
def revision_workspace_entry() -> FileResponse:
    return _serve_frontend_file("revision/workspace.html")


@app.get("/revision/workspace/__next.revision.workspace.__PAGE__.txt", include_in_schema=False)
def revision_workspace_rsc_entry() -> FileResponse:
    return _serve_frontend_file("revision/workspace/__next.revision/workspace/__PAGE__.txt")


frontend_dir = frontend_dist_dir()
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
