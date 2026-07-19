from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from app.services.path_service import REPORTS_DIR


STRATEGY_DIR = REPORTS_DIR.parent / "strategy"
STRATEGY_FILE = STRATEGY_DIR / "optimized-report-strategy.json"

FAMILIES = [
    "media_review",
    "internet_ops_review",
    "management_accounting_review",
    "sales_review",
    "foundation_review",
]

SECTION_POOL: dict[str, list[str]] = {
    "media_review": [
        "decision_summary",
        "business_judgement",
        "decision_design",
        "method_execution",
        "data_scope",
        "media_overview",
        "kpi_scorecard",
        "media_dimension_scorecards",
        "market_landscape",
        "delivery_gap",
        "media_daily_trend",
        "window_change",
        "combo_diagnostics",
        "stability_review",
        "risk_alerts",
        "action_matrix",
        "action_roadmap",
    ],
    "internet_ops_review": [
        "decision_summary",
        "business_judgement",
        "decision_design",
        "method_execution",
        "ops_topline",
        "ops_channel_scorecard",
        "ops_activity_scorecard",
        "ops_content_scorecard",
        "ops_combo_impact",
        "numeric",
        "category",
        "temporal",
        "risk_alerts",
        "action_roadmap",
    ],
    "management_accounting_review": [
        "decision_summary",
        "business_judgement",
        "decision_design",
        "method_execution",
        "data_scope",
        "management_accounting_profitability",
        "management_accounting_budget",
        "management_accounting_capital",
        "management_accounting_responsibility",
        "management_accounting_playbook",
        "numeric",
        "category",
        "temporal",
        "risk_alerts",
        "action_roadmap",
    ],
    "sales_review": [
        "decision_summary",
        "business_judgement",
        "decision_design",
        "method_execution",
        "market_landscape",
        "market_opportunity",
        "numeric",
        "category",
        "temporal",
        "risk_alerts",
        "action_roadmap",
    ],
    "foundation_review": [
        "decision_summary",
        "business_judgement",
        "decision_design",
        "method_execution",
        "foundation_top_funds",
        "foundation_structure",
        "foundation_priority_review",
        "foundation_top_projects",
        "numeric",
        "category",
        "temporal",
        "risk_alerts",
        "action_roadmap",
    ],
}
ALL_SECTION_CANDIDATES = sorted({section for values in SECTION_POOL.values() for section in values})

PROCESS_SECTIONS = {
    "analysis_program",
    "expert_recall",
    "object_recognition",
    "quality",
    "relationships",
    "method_execution",
    "semantic",
    "semantic_expansion",
    "report_navigation",
    "field_dictionary",
    "stats_appendix",
    "data_profile_appendix",
    "sample_rows",
}


def _family_one_hot(family: str) -> list[float]:
    return [1.0 if item == family else 0.0 for item in FAMILIES]


def _section_vector(family: str, selected_sections: list[str]) -> list[float]:
    selected = set(selected_sections)
    return [1.0 if section in selected else 0.0 for section in ALL_SECTION_CANDIDATES]


def _sample_context(rng: np.random.Generator, family: str) -> dict[str, float]:
    return {
        "has_time": float(rng.random() > 0.1),
        "has_dimensions": float(rng.random() > 0.15),
        "has_actions": float(rng.random() > 0.2),
        "has_risk": float(rng.random() > 0.2),
        "has_metric_cards": float(rng.random() > 0.25),
        "has_overview": float(rng.random() > 0.1),
        "has_trend_strength": float(rng.random()),
        "has_structure_strength": float(rng.random()),
        "has_actionability": float(rng.random()),
    }


def _proxy_score(family: str, selected_sections: list[str], context: dict[str, float]) -> float:
    selected = set(selected_sections)
    score = 25.0

    must_have = {
        "media_review": ["decision_summary", "business_judgement", "decision_design", "media_overview", "media_dimension_scorecards", "media_daily_trend", "action_matrix"],
        "internet_ops_review": ["decision_summary", "business_judgement", "decision_design", "ops_topline", "ops_channel_scorecard", "ops_activity_scorecard", "ops_content_scorecard", "ops_combo_impact"],
        "management_accounting_review": ["decision_summary", "business_judgement", "decision_design", "management_accounting_profitability", "management_accounting_budget", "management_accounting_capital", "management_accounting_playbook"],
        "sales_review": ["decision_summary", "business_judgement", "decision_design", "market_landscape", "market_opportunity", "action_roadmap"],
        "foundation_review": ["decision_summary", "business_judgement", "decision_design", "foundation_top_funds", "foundation_structure", "foundation_priority_review"],
    }
    for section in must_have.get(family, []):
        if section in selected:
            score += 7.5
    if "decision_summary" in selected:
        score += 8.5
    if "business_judgement" in selected:
        score += 7.0
    if "decision_design" in selected:
        score += 7.0
    if "action_roadmap" in selected:
        score += 5.0
    if "risk_alerts" in selected:
        score += 4.0
    if "data_scope" in selected:
        score += 2.0

    if family == "media_review":
        score += context["has_overview"] * (8.0 if "media_overview" in selected else -8.0)
        score += context["has_dimensions"] * (9.0 if "media_dimension_scorecards" in selected else -10.0)
        score += context["has_time"] * (8.0 if "media_daily_trend" in selected else -9.0)
        score += context["has_actions"] * (8.0 if "action_matrix" in selected else -9.0)
    elif family == "internet_ops_review":
        score += context["has_overview"] * (8.0 if "ops_topline" in selected else -8.0)
        score += context["has_dimensions"] * (8.0 if "ops_channel_scorecard" in selected else -8.0)
        score += context["has_actions"] * (7.5 if "ops_activity_scorecard" in selected else -7.5)
        score += context["has_dimensions"] * (7.0 if "ops_combo_impact" in selected else -6.5)
        score += context["has_time"] * (6.5 if "temporal" in selected else -7.0)
    elif family == "management_accounting_review":
        score += context["has_overview"] * (8.0 if "management_accounting_profitability" in selected else -10.0)
        score += context["has_dimensions"] * (7.5 if "management_accounting_responsibility" in selected else -7.5)
        score += context["has_actions"] * (7.5 if "management_accounting_playbook" in selected else -8.0)
        score += context["has_time"] * (5.0 if "temporal" in selected else -4.0)

    low_signal_penalties = 0.0
    for section in selected:
        if section in PROCESS_SECTIONS:
            low_signal_penalties += 8.0
        if section == "predictive":
            low_signal_penalties += 9.0 if family in {"media_review", "internet_ops_review"} else 4.0
        if section == "semantic":
            low_signal_penalties += 6.0
        if section in {"management_story", "meeting_ready", "boss_qa", "confidence_boundary", "question_tree", "planning_axes"}:
            low_signal_penalties += 8.5
    score -= low_signal_penalties

    score += context["has_actionability"] * (4.5 if "action_matrix" in selected or "management_accounting_playbook" in selected or "ops_activity_scorecard" in selected else -5.0)
    score += context["has_structure_strength"] * (4.0 if "market_landscape" in selected or "ops_channel_scorecard" in selected or "management_accounting_responsibility" in selected else -3.0)
    score += context["has_trend_strength"] * (4.0 if "media_daily_trend" in selected or "temporal" in selected else -3.0)

    return float(max(0.0, min(100.0, score)))


def _feature_row(family: str, context: dict[str, float], selected_sections: list[str]) -> np.ndarray:
    return np.array(
        [
            *_family_one_hot(family),
            context["has_time"],
            context["has_dimensions"],
            context["has_actions"],
            context["has_risk"],
            context["has_metric_cards"],
            context["has_overview"],
            context["has_trend_strength"],
            context["has_structure_strength"],
            context["has_actionability"],
            *_section_vector(family, selected_sections),
        ],
        dtype=float,
    )


def train_report_strategy_optimizer(num_trials: int = 12000, seed: int = 42) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    features: list[np.ndarray] = []
    scores: list[float] = []
    trial_rows: list[dict[str, Any]] = []

    for _ in range(num_trials):
        family = str(rng.choice(FAMILIES))
        pool = SECTION_POOL[family]
        size = int(rng.integers(max(4, len(pool) // 3), len(pool) + 1))
        selected = rng.choice(pool, size=size, replace=False).tolist()
        context = _sample_context(rng, family)
        score = _proxy_score(family, selected, context)
        features.append(_feature_row(family, context, selected))
        scores.append(score)
        trial_rows.append(
            {
                "family": family,
                "selected_sections": selected,
                "proxy_score": round(score, 4),
            }
        )

    matrix = np.vstack(features)
    targets = np.array(scores, dtype=float)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    model = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=220, random_state=seed, early_stopping=True)
    model.fit(scaled, targets)

    best_strategies: dict[str, Any] = {}
    search_iterations = max(500, min(4000, num_trials // 2))
    for family in FAMILIES:
        pool = SECTION_POOL[family]
        best_sections = pool[:]
        best_proxy = -1.0
        for _ in range(search_iterations):
            size = int(rng.integers(max(4, len(pool) // 3), len(pool) + 1))
            selected = rng.choice(pool, size=size, replace=False).tolist()
            context = _sample_context(rng, family)
            prediction = float(model.predict(scaler.transform([_feature_row(family, context, selected)]))[0])
            actual = _proxy_score(family, selected, context)
            blended = 0.6 * prediction + 0.4 * actual
            if blended > best_proxy:
                best_proxy = blended
                best_sections = selected
        best_strategies[family] = {
            "management_section_ids": best_sections,
            "proxy_score": round(best_proxy, 4),
        }

    payload = {
        "num_trials": int(num_trials),
        "seed": seed,
        "train_r2": round(float(model.score(scaled, targets)), 4),
        "best_strategies": best_strategies,
    }
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    STRATEGY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


@lru_cache(maxsize=1)
def load_optimized_report_strategy() -> dict[str, Any]:
    if STRATEGY_FILE.exists():
        try:
            return json.loads(STRATEGY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return train_report_strategy_optimizer()


def get_optimized_report_strategy(family: str) -> dict[str, Any]:
    payload = load_optimized_report_strategy()
    return {
        "metadata": {
            "num_trials": payload.get("num_trials", 0),
            "train_r2": payload.get("train_r2"),
        },
        **payload.get("best_strategies", {}).get(family, {"management_section_ids": SECTION_POOL.get(family, []), "proxy_score": None}),
    }
