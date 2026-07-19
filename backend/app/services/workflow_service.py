from __future__ import annotations

import re
from typing import Any

import pandas as pd

from app.services.dataset_service import load_all_sheet_frames

GENERIC_JOIN_COLUMNS = {
    "g",
    "year",
    "month",
    "day",
    "date",
    "team",
    "league",
    "pos",
    "country",
    "state",
    "city",
    "name",
    "type",
    "status",
    "class",
}


def normalise_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def singularise(value: str) -> str:
    if value.endswith("ies") and len(value) > 3:
        return value[:-3] + "y"
    if value.endswith("s") and len(value) > 3:
        return value[:-1]
    return value


def is_id_like(column_name: str) -> bool:
    lower = column_name.lower()
    normalised = normalise_name(column_name)
    return lower == "id" or lower.endswith("_id") or normalised.endswith("id")


def is_generic_join_column(column_name: str) -> bool:
    return normalise_name(column_name) in GENERIC_JOIN_COLUMNS


def is_ratio_like(column_name: str) -> bool:
    lower = column_name.lower()
    return any(
        token in lower
        for token in [
            "ratio",
            "rate",
            "share",
            "ctr",
            "cvr",
            "cpc",
            "cpm",
            "roi",
            "score",
            "率",
            "占比",
            "完成率",
            "渗透率",
        ]
    )


def semantic_keys(sheet_name: str, column_name: str) -> set[str]:
    keys = {f"exact:{normalise_name(column_name)}"}
    normalised_sheet = normalise_name(sheet_name)
    singular_sheet = singularise(normalised_sheet)
    lower = column_name.lower()
    normalised_column = normalise_name(column_name)

    if lower == "id":
        keys.add(f"entity:{normalised_sheet}")
        keys.add(f"entity:{singular_sheet}")
    if lower.endswith("_id"):
        entity = normalise_name(lower[:-3])
        if entity:
            keys.add(f"entity:{entity}")
            keys.add(f"entity:{singularise(entity)}")
    elif normalised_column.endswith("id") and normalised_column != "id":
        entity = normalised_column[:-2]
        if entity:
            keys.add(f"entity:{entity}")
            keys.add(f"entity:{singularise(entity)}")
    return keys


def build_column_map(sheet_name: str, frame: pd.DataFrame) -> dict[str, set[str]]:
    return {
        str(column): semantic_keys(sheet_name, str(column))
        for column in frame.columns.astype(str).tolist()
    }


def uniqueness_ratio(series: pd.Series) -> float:
    non_null = series.dropna()
    if non_null.empty:
        return 0.0
    return float(non_null.nunique() / len(non_null))


def missing_ratio(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float(series.isna().mean())


def mixed_type_columns(frame: pd.DataFrame) -> list[str]:
    mixed: list[str] = []
    for column in frame.columns.astype(str).tolist():
        series = frame[column].dropna()
        if series.empty or pd.api.types.is_numeric_dtype(series):
            continue
        as_numeric = pd.to_numeric(series.astype(str), errors="coerce")
        numeric_share = float(as_numeric.notna().mean())
        if 0.2 < numeric_share < 0.8:
            mixed.append(column)
    return mixed


def candidate_keys(frame: pd.DataFrame) -> list[dict[str, Any]]:
    keys: list[dict[str, Any]] = []
    for column in frame.columns.astype(str).tolist():
        series = frame[column]
        if is_ratio_like(column) or is_generic_join_column(column):
            continue
        ratio = uniqueness_ratio(frame[column])
        missing = missing_ratio(frame[column])
        if pd.api.types.is_numeric_dtype(series) and not is_id_like(column):
            continue
        if ratio >= 0.98 and missing <= 0.02:
            keys.append(
                {
                    "column": column,
                    "uniqueness_ratio": round(ratio, 4),
                    "missing_ratio": round(missing, 4),
                }
            )
    keys.sort(key=lambda item: (-item["uniqueness_ratio"], item["missing_ratio"]))
    return keys[:5]


def high_cardinality_columns(frame: pd.DataFrame) -> list[str]:
    items: list[str] = []
    for column in frame.columns.astype(str).tolist():
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series):
            continue
        if series.nunique(dropna=True) > max(30, int(len(frame) * 0.2)):
            items.append(column)
    return items[:5]


def infer_sheet_role(frame: pd.DataFrame, datetime_cols: list[str], numeric_cols: list[str]) -> str:
    if len(frame) == 0:
        return "empty"
    if datetime_cols and numeric_cols:
        return "event_or_timeseries_fact"
    if len(frame.columns) <= 10 and not numeric_cols:
        return "dimension_lookup"
    if len(frame.columns) > 40:
        return "wide_analytical_table"
    return "analytical_fact"


def profile_sheet(sheet_name: str, frame: pd.DataFrame) -> dict[str, Any]:
    numeric_cols = frame.select_dtypes(include=["number", "bool"]).columns.astype(str).tolist()
    datetime_cols = [
        str(column)
        for column in frame.columns
        if pd.api.types.is_datetime64_any_dtype(frame[column])
    ]
    categorical_cols = [
        str(column)
        for column in frame.columns
        if str(column) not in numeric_cols and str(column) not in datetime_cols
    ]
    overall_missing = float(frame.isna().mean().mean()) if len(frame.columns) else 0.0
    duplicate_ratio = (
        float(frame.duplicated().mean()) if len(frame) and len(frame.columns) else 0.0
    )

    return {
        "name": sheet_name,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "role": infer_sheet_role(frame, datetime_cols, numeric_cols),
        "numeric_columns": numeric_cols[:12],
        "datetime_columns": datetime_cols[:6],
        "categorical_columns": categorical_cols[:12],
        "candidate_keys": candidate_keys(frame),
        "high_cardinality_columns": high_cardinality_columns(frame),
        "mixed_type_columns": mixed_type_columns(frame),
        "overall_missing_ratio": round(overall_missing, 4),
        "duplicate_row_ratio": round(duplicate_ratio, 4),
    }


def detect_relationships(sheet_frames: list[tuple[dict[str, Any], pd.DataFrame]]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    for left_index, (left_sheet, left_frame) in enumerate(sheet_frames):
        left_map = build_column_map(left_sheet["name"], left_frame)
        for right_sheet, right_frame in sheet_frames[left_index + 1 :]:
            right_map = build_column_map(right_sheet["name"], right_frame)
            for left_column, left_keys in left_map.items():
                for right_column, right_keys in right_map.items():
                    shared_keys = left_keys & right_keys
                    if not shared_keys:
                        continue

                    entity_match = any(key.startswith("entity:") for key in shared_keys)
                    exact_match = (
                        f"exact:{normalise_name(left_column)}" in shared_keys
                        and f"exact:{normalise_name(right_column)}" in shared_keys
                    )

                    left_unique_ratio = uniqueness_ratio(left_frame[left_column])
                    right_unique_ratio = uniqueness_ratio(right_frame[right_column])
                    uniqueness_score = max(left_unique_ratio, right_unique_ratio)

                    if (
                        not entity_match
                        and is_generic_join_column(left_column)
                        and is_generic_join_column(right_column)
                        and uniqueness_score < 0.98
                    ):
                        continue

                    if not entity_match and not exact_match:
                        continue

                    if (
                        exact_match
                        and not entity_match
                        and left_unique_ratio < 0.1
                        and right_unique_ratio < 0.1
                    ):
                        continue

                    left_series = left_frame[left_column].dropna().astype(str)
                    right_series = right_frame[right_column].dropna().astype(str)
                    if left_series.empty or right_series.empty:
                        continue

                    left_set = set(left_series.unique().tolist())
                    right_set = set(right_series.unique().tolist())
                    overlap = left_set & right_set
                    overlap_ratio = len(overlap) / max(1, min(len(left_set), len(right_set)))
                    if overlap_ratio < 0.25:
                        continue

                    left_unique = left_unique_ratio >= 0.95
                    right_unique = right_unique_ratio >= 0.95
                    if left_unique and right_unique:
                        relation = "one_to_one"
                    elif left_unique or right_unique:
                        relation = "one_to_many"
                    else:
                        relation = "many_to_many"

                    confidence = overlap_ratio * 0.55 + uniqueness_score * 0.25
                    if entity_match:
                        confidence += 0.25
                    if exact_match:
                        confidence += 0.08
                    if relation == "many_to_many":
                        confidence -= 0.08

                    relationships.append(
                        {
                            "left_sheet": left_sheet["name"],
                            "left_column": left_column,
                            "right_sheet": right_sheet["name"],
                            "right_column": right_column,
                            "relationship_type": relation,
                            "overlap_ratio": round(overlap_ratio, 4),
                            "confidence_score": round(max(0.0, min(1.0, confidence)), 4),
                            "match_type": "entity" if entity_match else "exact",
                        }
                    )
    relationships.sort(
        key=lambda item: (
            item["confidence_score"],
            item["overlap_ratio"],
            1 if item["relationship_type"] != "many_to_many" else 0,
        ),
        reverse=True,
    )
    return relationships[:10]


def build_alerts(sheet_profiles: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for profile in sheet_profiles:
        if profile["overall_missing_ratio"] >= 0.2:
            alerts.append(
                {
                    "severity": "high",
                    "sheet": profile["name"],
                    "title": "High missingness",
                    "detail": f"Average column missing ratio is {profile['overall_missing_ratio']:.1%}.",
                }
            )
        if profile["duplicate_row_ratio"] >= 0.05:
            alerts.append(
                {
                    "severity": "medium",
                    "sheet": profile["name"],
                    "title": "Duplicate rows detected",
                    "detail": f"Duplicate row ratio is {profile['duplicate_row_ratio']:.1%}.",
                }
            )
        if profile["mixed_type_columns"]:
            alerts.append(
                {
                    "severity": "medium",
                    "sheet": profile["name"],
                    "title": "Mixed-type columns",
                    "detail": f"Columns {', '.join(profile['mixed_type_columns'][:3])} mix numeric and text-like values.",
                }
            )
    if len(relationships) == 0 and len(sheet_profiles) > 1:
        alerts.append(
            {
                "severity": "medium",
                "sheet": "all",
                "title": "No confident joins yet",
                "detail": "Multiple sheets exist but no strong join keys were detected automatically.",
            }
        )
    return alerts


def workflow_mode(sheet_profiles: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> str:
    has_datetime = any(profile["datetime_columns"] for profile in sheet_profiles)
    if len(sheet_profiles) > 1 and relationships:
        return "multi_source_relational_analysis"
    if has_datetime:
        return "temporal_analytical_modeling"
    if any(profile["candidate_keys"] for profile in sheet_profiles):
        return "entity_level_inference"
    return "general_exploratory_analysis"


def complexity_score(sheet_profiles: list[dict[str, Any]], alerts: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> int:
    score = 18
    score += min(24, max(0, len(sheet_profiles) - 1) * 8)
    score += min(18, len(relationships) * 4)
    score += min(18, sum(1 for profile in sheet_profiles if profile["columns"] > 30) * 6)
    score += min(12, sum(1 for alert in alerts if alert["severity"] == "high") * 6)
    score += min(10, sum(1 for profile in sheet_profiles if profile["mixed_type_columns"]) * 5)
    return max(0, min(100, score))


def quality_score(sheet_profiles: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> int:
    penalty = 0
    for profile in sheet_profiles:
        penalty += int(profile["overall_missing_ratio"] * 35)
        penalty += int(profile["duplicate_row_ratio"] * 35)
        penalty += len(profile["mixed_type_columns"]) * 3
    penalty += sum(6 if alert["severity"] == "high" else 3 for alert in alerts)
    return max(0, min(100, 92 - penalty))


def recommended_sequence(mode: str, relationships: list[dict[str, Any]], sheet_profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps = [
        {
            "step": "source_fingerprint",
            "title": "Source fingerprinting",
            "why": "Lock down sheet roles, candidate keys, and variable types before analysis.",
            "priority": "high",
        },
        {
            "step": "quality_gate",
            "title": "Quality gate",
            "why": "Resolve missingness, duplicates, and mixed-type columns before inference.",
            "priority": "high",
        },
    ]
    if relationships:
        steps.append(
            {
                "step": "relationship_modeling",
                "title": "Cross-sheet relationship modeling",
                "why": "Build join paths and resolve one-to-many vs many-to-many ambiguity.",
                "priority": "high",
            }
        )
    if any(profile["datetime_columns"] for profile in sheet_profiles):
        steps.append(
            {
                "step": "temporal_grain_check",
                "title": "Temporal grain check",
                "why": "Validate event grain, time gaps, and aggregation windows before trend analysis.",
                "priority": "medium",
            }
        )
    steps.extend(
        [
            {
                "step": "analysis_route_selection",
                "title": "Analysis route selection",
                "why": f"Current dataset is best treated as {mode.replace('_', ' ')}.",
                "priority": "high",
            },
            {
                "step": "execution_notebook",
                "title": "Code-assisted execution",
                "why": "Use Python/SQL runner only after the structural plan is stable.",
                "priority": "medium",
            },
        ]
    )
    return steps


def suggested_tracks(sheet_profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    if any(profile["datetime_columns"] and profile["numeric_columns"] for profile in sheet_profiles):
        tracks.append(
            {
                "name": "trend-and-seasonality",
                "analyses": ["correlation", "pca"],
                "reason": "Datetime and numeric measures coexist, so temporal structure is likely important.",
            }
        )
    if any(profile["numeric_columns"] and profile["categorical_columns"] for profile in sheet_profiles):
        tracks.append(
            {
                "name": "driver-analysis",
                "analyses": ["ols", "anova", "ttest", "logit", "ab_test"],
                "reason": "There are enough measures and segments to support inferential work.",
            }
        )
    if any(len(profile["numeric_columns"]) >= 3 for profile in sheet_profiles):
        tracks.append(
            {
                "name": "segmentation",
                "analyses": ["kmeans", "pca"],
                "reason": "Multiple numeric measures are available for latent pattern discovery.",
            }
        )
    return tracks


def build_workflow_blueprint(dataset_id: str) -> dict[str, Any]:
    metadata, sheet_frames = load_all_sheet_frames(dataset_id)
    profiles = [
        profile_sheet(sheet["name"], frame)
        for sheet, frame in sheet_frames
    ]
    relationships = detect_relationships(sheet_frames)
    alerts = build_alerts(profiles, relationships)
    mode = workflow_mode(profiles, relationships)

    return {
        "dataset_id": metadata["dataset_id"],
        "dataset_name": metadata["name"],
        "workflow_mode": mode,
        "complexity_score": complexity_score(profiles, alerts, relationships),
        "quality_score": quality_score(profiles, alerts),
        "sheet_profiles": profiles,
        "relationships": relationships,
        "alerts": alerts,
        "recommended_sequence": recommended_sequence(mode, relationships, profiles),
        "suggested_tracks": suggested_tracks(profiles),
        "recommended_entry_sheet": metadata.get("active_sheet"),
    }
