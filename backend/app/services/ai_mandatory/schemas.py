from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AIFieldSemanticMapping(BaseModel):
    field_name: str
    canonical_concept: str
    business_role: str
    granularity_hint: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    alternative_mappings: list[str] = Field(default_factory=list)
    risk_note: str = ""


class AIFieldSemanticMappingResult(BaseModel):
    inferred_business_context: str
    object_grain: str
    time_grain: str
    field_mappings: list[AIFieldSemanticMapping] = Field(default_factory=list)
    uncertain_fields: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utc_now)
    provider: str
    model: str
    trace_id: str


class AIBusinessRoutingResult(BaseModel):
    selected_by_user: str | None = None
    ai_route: str
    final_route: str
    confidence: float = Field(ge=0.0, le=1.0)
    alternative_routes: list[str] = Field(default_factory=list)
    reason: str
    blocked_routes: list[str] = Field(default_factory=list)
    trace_id: str


class AIMetricPlanItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metric_id: str
    metric_name_cn: str
    metric_name_en: str = ""
    metric_family: str
    business_domain: str = ""
    business_object: str = ""
    metric_type: Literal["direct", "derived", "proxy", "diagnostic", "unavailable"]
    required_field_roles: list[str] = Field(default_factory=list)
    matched_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    formula_or_logic: str = Field(default="", alias="formula")
    grain: str = ""
    time_window_requirement: str = ""
    minimum_data_requirement: str = ""
    evidence_level: Literal[
        "A_DIRECT",
        "B_DERIVED",
        "C_PROXY",
        "D_DIAGNOSTIC",
        "E_UNSUPPORTED",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    calculation_feasibility: Literal["calculable", "proxy_only", "diagnostic_only", "unsupported"]
    business_question_answered: str = ""
    allowed_downstream_usage: list[str] = Field(default_factory=list, alias="downstream_usage")
    forbidden_downstream_usage: list[str] = Field(default_factory=list, alias="forbidden_usage")
    caveat: str = ""
    reason: str = ""


class AIMetricDerivationPlan(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    available_metrics: list[str] = Field(default_factory=list)
    unavailable_metrics: list[str] = Field(default_factory=list)
    proxy_metrics: list[str] = Field(default_factory=list)
    diagnostic_questions: list[str] = Field(default_factory=list)
    metric_plans: list[AIMetricPlanItem] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utc_now)
    provider: str = ""
    model: str = ""
    trace_id: str
