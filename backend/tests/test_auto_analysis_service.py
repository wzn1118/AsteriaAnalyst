from __future__ import annotations

from collections import Counter, defaultdict
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from app.models import AutoAnalysisRequest, LabMethodCardSaveRequest
from app.services.auto_analysis_causal_service import build_causal_executor_tables
from app.services.auto_analysis_method_executor_service import execute_method_card_assets
from app.services.auto_analysis_registry_service import auto_analysis_method_catalog, get_auto_analysis_method_registry, save_lab_method_card
import app.services.auto_analysis_service as auto_analysis_service
from app.main import manifest
from app.models import StatisticRequest
from app.services.analysis_service import run_statistical_analysis
from app.services.auto_analysis_service import (
    LARGE_SAMPLE_DEFAULT_CHUNK_SIZE,
    LARGE_SAMPLE_FINE_CHUNK_SIZE,
    _attach_report_writer_agents,
    _build_report_writer_agent_input,
    _chart_export_ref,
    _chart_business_question,
    _chart_sampling_note,
    _deterministic_agent_review_payload,
    _business_field_label,
    _large_sample_policy_for_frame,
    _markdown_to_lab_report_html,
    _method_visual_marker,
    _reader_facing_html,
    _reader_facing_internal_leakage_hits,
    _reader_visible_html_text,
    _register_lab_report_catalog,
    _skeptical_report_writer_review,
    run_auto_analysis,
)


def _write_lab_report_agent_review_fixture(export_dir: Path) -> None:
    actions = [
        ("P0", "收入与成本的差距是否稳定", "优先复核高收入低成本订单，检查渠道投放是否存在可放大的利润机会。"),
        ("P1", "渠道结构是否解释收入波动", "优先检查搜索与社交渠道的收入贡献，诊断样本不足造成的风险判断偏差。"),
        ("P1", "单位销量是否支撑收入增长", "复核单位销量与收入的同步关系，识别需要继续培育的高转化机会。"),
        ("P2", "成本异常是否影响利润判断", "检查成本高于收入增速的记录，校正后再形成正式业务判断。"),
        ("P2", "行动是否能落到责任人", "优先把图表证据映射到渠道负责人，复核机会清单后进入行动跟踪。"),
    ]
    export_dir.joinpath("lab_report_agent_reviews.json").write_text(
        json.dumps(
            {
                "contract": "analysis_lab_agent_reviews_v1",
                "runtime_status": "completed",
                "reviewer_count": 3,
                "agent_reviews": [
                    {
                        "agent_id": "claim-reviewer",
                        "agent_name": "Claim Reviewer",
                        "claim_review": {"summary": "核心判断均可追溯到图表、方法包和数值证据。"},
                        "business_action_review": {"summary": "行动项具备优先级、责任提示和复核边界。"},
                        "chart_relevance_review": {"summary": "主文图表覆盖收入、成本、单位销量和渠道问题。"},
                    },
                    {
                        "agent_id": "action-reviewer",
                        "agent_name": "Action Reviewer",
                        "claim_review": {"summary": "未发现把方法状态当作业务结论的问题。"},
                        "business_action_review": {"summary": "建议保持 5 条动作，避免模板化扩写。"},
                        "chart_relevance_review": {"summary": "图表引用足以支撑行动矩阵。"},
                    },
                    {
                        "agent_id": "chart-reviewer",
                        "agent_name": "Chart Reviewer",
                        "claim_review": {"summary": "证据链覆盖关键图表和方法运行。"},
                        "business_action_review": {"summary": "行动均包含优先、复核、检查、机会或风险等执行词。"},
                        "chart_relevance_review": {"summary": "业务图表应进入主文，方法截图只进入附录索引。"},
                    },
                ],
                "consolidated_actions": [
                    {
                        "priority": priority,
                        "business_question": question,
                        "action": action,
                        "evidence_refs": [f"chart:fixture:{index}", f"method_run_fixture_{index}"],
                        "owner_hint": f"复核边界：由业务负责人确认字段口径和样本覆盖后执行第 {index} 项。",
                    }
                    for index, (priority, question, action) in enumerate(actions, start=1)
                ],
                "cited_chart_refs": ["chart:fixture:1", "chart:fixture:2", "chart:fixture:3"],
                "cited_method_run_ids": ["method_run_fixture_1", "method_run_fixture_2", "method_run_fixture_3"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_auto_analysis_registry_is_extensible_and_large_enough() -> None:
    registry = get_auto_analysis_method_registry()
    assert len(registry) >= 4000
    assert any(item["id"] == "visual_bubble" for item in registry)
    assert any(item["id"] == "visual_quadrant" for item in registry)


def test_auto_analysis_method_catalog_exposes_chinese_frontend_metadata() -> None:
    catalog = auto_analysis_method_catalog()
    methods = catalog["methods"]

    assert catalog["summary"]["total_methods"] >= 2000
    assert catalog["priority_method_ids"]
    assert "financial_visual_catalog" not in catalog["summary"]["sources"]
    assert not any(item["source"] == "financial_visual_catalog" for item in methods)
    assert any(item["family"] == "visual" and "bubble" in item["id"] for item in methods)
    assert any(item["family"] == "visual" and "waterfall" in item["id"] for item in methods)
    visual_methods = [
        item
        for item in methods
        if item["family"] == "visual" or {"chart", "image_spec"} & set(item["output_types"])
    ]
    assert len(visual_methods) >= 700
    bubble = next(item for item in methods if item["family"] == "visual" and "bubble" in item["id"])
    assert bubble["name_zh"]
    assert bubble["family_label"]
    assert bubble["goal_zh"].startswith("\u7528\u4e8e")
    assert bubble["output_labels"]
    assert bubble["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
    assert bubble["edit_capabilities"]["freedom_score"] >= 60
    assert "智能匹配字段" in bubble["edit_capabilities"]["run_control_labels"]
    assert any(item["recommended"] for item in bubble["edit_capabilities"]["selection_mode_labels"])
    assert bubble["usage_guidance"]
    assert bubble["report_value_hooks"]
    assert {"text", "table", "data", "chart", "image_spec", "report_section"}.issubset(set(bubble["output_types"]))
    descriptive = next(item for item in methods if item["id"] == "descriptive_profile")
    assert set(descriptive["output_types"]) == {"text", "table", "data"}
    assert "chart" not in descriptive["output_types"]
    assert "image_spec" not in descriptive["output_types"]
    compact_catalog = auto_analysis_method_catalog(compact=True)
    compact_bubble = next(item for item in compact_catalog["methods"] if item["id"] == bubble["id"])
    assert compact_bubble["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
    assert compact_bubble["usage_guidance"]
    assert compact_bubble["edit_capabilities"]["editable_field_labels"]


def test_auto_analysis_method_catalog_cards_are_unique_and_frontend_runnable() -> None:
    catalog = auto_analysis_method_catalog(compact=True)
    methods = catalog["methods"]

    method_ids = [str(item.get("id") or "") for item in methods]
    duplicate_ids = {method_id: count for method_id, count in Counter(method_ids).items() if method_id and count > 1}
    alias_targets: dict[str, set[str]] = defaultdict(set)
    for method in methods:
        method_id = str(method.get("id") or "")
        aliases = [method_id, *list(method.get("compatibility_alias_ids") or [])]
        for alias in aliases:
            alias = str(alias or "").strip()
            if alias:
                alias_targets[alias].add(method_id)
    alias_collisions = {
        alias: sorted(targets)
        for alias, targets in alias_targets.items()
        if len(targets) > 1
    }

    assert len(methods) >= 4000
    assert all(method_ids)
    assert not duplicate_ids
    assert not alias_collisions
    assert len(alias_targets) >= len(methods)
    assert all(item["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method" for item in methods)
    assert all(item["runtime_executor"] for item in methods)
    assert all(item["edit_capabilities"]["editable_field_labels"] for item in methods)
    assert all(item["edit_capabilities"]["run_control_labels"] for item in methods)
    assert all(item["binding_controls"] for item in methods)
    assert all(item["usage_guidance"] for item in methods)
    assert all(item["report_value_hooks"] for item in methods)
    assert all(item["stable_output_types"] for item in methods)
    assert all(item["default_output_types"] for item in methods)


def test_auto_analysis_catalog_has_500_non_financial_statistical_visual_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = catalog["methods"]
    visual_cards = [item for item in methods if item["source"] == "statistical_visual_catalog"]
    visual_ids = [item["id"] for item in visual_cards]
    domain_pattern_pairs = {
        (item.get("visual_domain_id"), item.get("visual_pattern_id"))
        for item in visual_cards
    }
    finance_terms = re.compile(r"stock|market|portfolio|trading|revenue|profit|margin|cash|roi", re.I)

    assert len(visual_cards) >= 500
    assert len(visual_ids) == len(set(visual_ids))
    assert len(domain_pattern_pairs) == len(visual_cards)
    assert all(item["family"] == "visual" for item in visual_cards)
    assert all(item.get("allowed_domain") == "non_financial" for item in visual_cards)
    assert all(item.get("excluded_domain") == "finance" for item in visual_cards)
    assert all(item.get("base_method_id") == item["id"] for item in visual_cards)
    assert all({"chart", "image_spec", "report_section"}.issubset(set(item["output_types"])) for item in visual_cards)
    assert not any(finance_terms.search(" ".join(str(item.get(key) or "") for key in ("id", "name", "goal"))) for item in visual_cards)


def test_auto_analysis_registry_excludes_financial_visual_cards_by_default() -> None:
    registry = get_auto_analysis_method_registry()
    assert not any(item.get("source") == "financial_visual_catalog" for item in registry)
    assert not any(str(item.get("id") or "").startswith("visual_finance_") for item in registry)


def test_auto_analysis_catalog_exposes_extended_statistics_and_data_analysis_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "missingness_mechanism_diagnostic_data",
        "cohens_d_effect_size_data",
        "multiple_testing_correction_data",
        "vif_multicollinearity_data",
        "cross_validation_data",
        "shap_explanation_data",
        "dag_assumption_review_data",
        "propensity_score_matching_data",
        "forecast_backtesting_data",
        "cuped_adjustment_data",
        "stratified_sampling_design_data",
        "power_curve_analysis_data",
        "ratio_metric_delta_method_data",
        "zero_inflation_diagnostic_data",
        "generalized_additive_model_data",
        "cluster_robust_standard_errors_data",
        "parallel_trends_diagnostic_data",
        "double_machine_learning_data",
        "population_stability_index_data",
        "conformal_prediction_data",
        "datasheet_for_dataset_data",
        "analysis_lineage_map_data",
        "bayesian_prior_predictive_check_data",
        "bayesian_hierarchical_model_data",
        "topic_model_lda_data",
        "text_embedding_similarity_data",
        "network_pagerank_data",
        "community_detection_louvain_data",
        "moran_i_spatial_autocorrelation_data",
        "geographically_weighted_regression_data",
        "privacy_k_anonymity_data",
        "differential_privacy_budget_data",
        "data_contract_validation_data",
        "data_quality_scorecard_data",
        "metric_anomaly_root_cause_data",
        "model_performance_monitor_data",
        "uplift_evaluation_qini_data",
        "funnel_step_conversion_data",
        "survival_retention_model_data",
    }

    assert expected_ids.issubset(methods)
    extended_catalog_cards = [
        item
        for item in methods.values()
        if item["source"] == "statistical_catalog" and item["status"] == "catalog" and item["base_method_id"] in {method_id.rsplit("_", 1)[0] for method_id in expected_ids}
    ]
    assert len(extended_catalog_cards) >= len(expected_ids)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "catalog"
        assert method["source"] == "statistical_catalog"
        assert method["usage_guidance"]
        assert method["report_value_hooks"]
        assert method["card_sections"]
        assert "data" in method["stable_output_types"]
        assert method["edit_capabilities"]["editable_field_labels"]

    assert methods["missingness_mechanism_diagnostic_data"]["family"] == "descriptive"
    assert methods["cohens_d_effect_size_data"]["family"] == "comparison"
    assert methods["vif_multicollinearity_data"]["family"] == "regression_glm"
    assert methods["cross_validation_data"]["family"] == "machine_learning"
    assert methods["dag_assumption_review_data"]["family"] == "causal"
    assert methods["forecast_backtesting_data"]["family"] == "time_series"
    assert methods["cuped_adjustment_data"]["family"] == "experimentation"
    assert methods["generalized_additive_model_data"]["family"] == "regression_glm"
    assert methods["population_stability_index_data"]["family"] == "machine_learning"
    assert methods["analysis_lineage_map_data"]["family"] == "statistical"
    assert methods["topic_model_lda_data"]["family"] == "multivariate"
    assert methods["text_embedding_similarity_data"]["family"] == "association"
    assert methods["network_pagerank_data"]["family"] == "multivariate"
    assert methods["geographically_weighted_regression_data"]["family"] == "regression_glm"
    assert methods["privacy_k_anonymity_data"]["family"] == "descriptive"
    assert methods["model_performance_monitor_data"]["family"] == "machine_learning"
    assert methods["survival_retention_model_data"]["family"] == "survival"


def test_auto_analysis_catalog_exposes_variance_and_welch_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "levene_data",
        "brown_forsythe_data",
        "bartlett_data",
        "welch_anova_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert "data" in method["stable_output_types"]
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"levene", "brown_forsythe", "bartlett", "welch_anova"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_repeated_measure_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "repeated_measures_anova_data",
        "friedman_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert {"target", "features"}.issubset(set(method["binding_controls"]))
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"repeated_measures_anova", "friedman"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_multifactor_mean_test_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "two_way_anova_data",
        "ancova_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "mean_tests"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert {"target", "group", "features"}.issubset(set(method["binding_controls"]))
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"two_way_anova", "ancova"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_distribution_diagnostic_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "shapiro_wilk_data",
        "dagostino_k2_data",
        "jarque_bera_data",
        "kolmogorov_smirnov_1samp_data",
        "anderson_darling_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "distribution_assumption"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {
        "shapiro_wilk",
        "dagostino_k2",
        "jarque_bera",
        "kolmogorov_smirnov_1samp",
        "anderson_darling",
    }.issubset(capability_types)


def test_auto_analysis_catalog_exposes_regression_diagnostic_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "breusch_pagan_data",
        "white_test_data",
        "durbin_watson_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "distribution_assumption"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert "data" in method["stable_output_types"]
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"breusch_pagan", "white_test", "durbin_watson"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_regularized_regression_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "ridge_regression_data",
        "lasso_regression_data",
        "elastic_net_data",
        "robust_regression_data",
        "quantile_regression_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "regression_glm"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert {"target", "features"}.issubset(set(method["edit_capabilities"]["editable_fields"]))
        assert "data" in method["stable_output_types"]
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"ridge_regression", "lasso_regression", "elastic_net", "robust_regression", "quantile_regression"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_time_series_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "moving_average_data",
        "autocorrelation_data",
        "partial_autocorrelation_data",
        "ljung_box_data",
        "adf_test_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "time_series"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert "time" in method["edit_capabilities"]["editable_fields"]
        assert "chart" in method["stable_output_types"]
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"moving_average", "autocorrelation", "partial_autocorrelation", "ljung_box", "adf_test"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_descriptive_concentration_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "quantile_profile_data",
        "trimmed_mean_data",
        "winsorized_summary_data",
        "gini_coefficient_data",
        "pareto_analysis_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "descriptive"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"quantile_profile", "trimmed_mean", "winsorized_summary", "gini_coefficient", "pareto_analysis"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_foundational_descriptive_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "descriptive_summary_data",
        "frequency_table_data",
        "cross_tabulation_data",
        "pivot_summary_data",
        "segmented_kpi_breakdown_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "descriptive"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"descriptive_summary", "frequency_table", "cross_tabulation", "pivot_summary", "segmented_kpi_breakdown"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_bivariate_association_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "pearson_correlation_data",
        "spearman_correlation_data",
        "kendall_tau_data",
        "point_biserial_data",
        "eta_squared_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "association"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"pearson_correlation", "spearman_correlation", "kendall_tau", "point_biserial", "eta_squared"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_advanced_association_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "partial_correlation_data",
        "distance_correlation_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "association"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    assert {"target", "features"}.issubset(set(methods["partial_correlation_data"]["binding_controls"]))
    capability_types = set(manifest()["analysis_types"])
    assert {"partial_correlation", "distance_correlation"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_extended_mean_test_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {"one_sample_ttest_data", "paired_ttest_data", "z_test_mean_data"}

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "mean_tests"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"one_sample_ttest", "paired_ttest", "z_test_mean"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_nonparametric_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "wilcoxon_signed_rank_data",
        "sign_test_data",
        "mood_median_data",
        "ks_two_sample_data",
        "runs_test_data",
        "median_test_data",
        "fligner_killeen_data",
        "permutation_test_data",
        "bootstrap_ci_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "nonparametric"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {
        "wilcoxon_signed_rank",
        "sign_test",
        "mood_median",
        "ks_two_sample",
        "runs_test",
        "median_test",
        "fligner_killeen",
        "permutation_test",
        "bootstrap_ci",
    }.issubset(capability_types)


def test_auto_analysis_catalog_exposes_categorical_association_strength_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "cramers_v_data",
        "phi_coefficient_data",
        "theils_u_data",
        "goodman_kruskal_lambda_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "categorical_association"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["edit_capabilities"]["freedom_score"] >= 58
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    capability_types = set(manifest()["analysis_types"])
    assert {"cramers_v", "phi_coefficient", "theils_u", "goodman_kruskal_lambda"}.issubset(capability_types)


def test_auto_analysis_catalog_exposes_categorical_agreement_live_cards() -> None:
    catalog = auto_analysis_method_catalog()
    methods = {item["id"]: item for item in catalog["methods"]}
    expected_ids = {
        "mcnemar_data",
        "cochran_q_data",
        "cmh_test_data",
        "cohens_kappa_data",
    }

    assert expected_ids.issubset(methods)
    for method_id in expected_ids:
        method = methods[method_id]
        assert method["status"] == "live"
        assert method["source"] == "statistical_catalog"
        assert method["family"] == "categorical_association"
        assert method["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
        assert method["usage_guidance"]
        assert method["report_value_hooks"]

    assert {"target", "features"}.issubset(set(methods["mcnemar_data"]["binding_controls"]))
    assert {"target", "features"}.issubset(set(methods["cochran_q_data"]["binding_controls"]))
    assert {"target", "group", "features"}.issubset(set(methods["cmh_test_data"]["binding_controls"]))
    assert {"target", "features"}.issubset(set(methods["cohens_kappa_data"]["binding_controls"]))
    capability_types = set(manifest()["analysis_types"])
    assert {"mcnemar", "cochran_q", "cmh_test", "cohens_kappa"}.issubset(capability_types)


def test_auto_analysis_registry_can_learn_runtime_methods(monkeypatch, tmp_path) -> None:
    learned_path = tmp_path / "learned_methods.json"
    learned_path.write_text(
        json.dumps(
            {
                "methods": [
                    {
                        "id": "report_part_evidence_index_management_bridge_full_dataset_report_section",
                        "name": "Evidence Index Management Bridge",
                        "family": "report_part",
                        "goal": "Turn evidence references into an auditable management-facing report section.",
                        "output_types": ["report_section", "table"],
                        "required_roles": ["full_dataset"],
                        "tags": ["learned", "evidence_index"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ASTERIA_AUTO_ANALYSIS_LEARNED_METHODS_PATH", str(learned_path))

    registry = get_auto_analysis_method_registry()
    learned = next(item for item in registry if item["id"] == "report_part_evidence_index_management_bridge_full_dataset_report_section")
    assert learned["source"] == "learned_methods"

    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d"],
            "revenue": [100, 240, 120, 360],
            "cost": [60, 100, 90, 120],
            "units": [2, 4, 3, 6],
            "channel": ["search", "search", "social", "direct"],
        }
    )
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(dataset_id="demo", active_sheet="Sheet1", report_part="evidence_index", max_methods=24),
        dataset_name="demo",
        sheet_name="Sheet1",
    )
    summary = result["data"]["method_registry_summary"]
    assert summary["learned_methods"] == 1
    assert summary["sources"]["learned_methods"] == 1
    learned_route = next(item for item in result["data"]["routed_methods"] if item["id"] == learned["id"])
    assert learned_route["executor_hint"] == "report_section_writer"
    assert learned_route["method_card"]["field_bindings"]["dataset_scope"] == "all_rows"
    assert "evidence_index" in learned_route["method_card"]["report_slots"]
    learned_execution = next(item for item in result["data"]["method_card_executions"] if item["method_id"] == learned["id"])
    assert learned_execution["executor_hint"] == "report_section_writer"
    assert learned_execution["status"] == "ready"
    assert learned_execution["result_ref"].startswith("report_part:")
    learned_asset = next(item for item in result["data"]["method_execution_assets"] if item["method_id"] == learned["id"])
    assert learned_asset["asset_type"] == "report_section_contract"
    assert learned_asset["asset_ref"].startswith("report_part:")
    assert "evidence_refs" in learned_asset["payload"]


def test_lab_method_card_editor_can_save_reusable_method(monkeypatch, tmp_path) -> None:
    learned_path = tmp_path / "learned_methods.json"
    monkeypatch.setenv("ASTERIA_AUTO_ANALYSIS_LEARNED_METHODS_PATH", str(learned_path))

    saved = save_lab_method_card(
        LabMethodCardSaveRequest(
            base_method_id="descriptive_profile_single_field_text",
            name="客单价画像复用卡",
            description="保存客单价字段绑定，用于后续高价值报告复用。",
            family="descriptive",
            output_types=["text", "table", "data"],
            required_roles=["single_field", "derived_metric"],
            field_bindings={"target": "客单价", "derived_metrics": ["客单价分层"]},
            selection_mode="fields",
            statistical_options={"alpha": 0.1, "hypothesis": "larger"},
            report_value_hooks=["把客单价画像沉淀为经营质量判断。"],
            usage_guidance=[{"title": "复用场景", "detail": "每次订单数据导入后先跑客单价画像。"}],
            tags=["客单价", "经营质量"],
            source_method={"id": "descriptive_profile_single_field_text", "family": "descriptive"},
        )
    )

    assert saved["status"] == "saved"
    assert learned_path.is_file()
    catalog = auto_analysis_method_catalog(compact=True)
    learned = next(item for item in catalog["methods"] if item["id"] == saved["method"]["id"])
    assert learned["source"] == "learned_methods"
    assert learned["method_card_contract"] == "analysis_lab_method_card_freedom_v2_unique_per_method"
    assert learned["edit_capabilities"]["editable_field_labels"]
    assert learned["field_bindings"]["target"] == "客单价"
    assert learned["selection_mode"] == "fields"
    assert learned["statistical_options"]["alpha"] == 0.1
    assert learned["statistical_options"]["hypothesis"] == "larger"
    assert learned["usage_guidance"][0]["title"] == "复用场景"
    assert "把客单价画像沉淀为经营质量判断。" in learned["report_value_hooks"]
    assert learned["output_types"] == ["text", "table", "data"]


def test_saved_method_card_defaults_drive_runtime_method_binding(monkeypatch, tmp_path) -> None:
    learned_path = tmp_path / "learned_methods.json"
    monkeypatch.setenv("ASTERIA_AUTO_ANALYSIS_LEARNED_METHODS_PATH", str(learned_path))

    saved = save_lab_method_card(
        LabMethodCardSaveRequest(
            base_method_id="descriptive_profile_single_field_text",
            name="客单价复用画像",
            description="保存字段绑定后应可直接作为运行默认值复用。",
            family="descriptive",
            output_types=["text", "table", "data"],
            required_roles=["single_field"],
            field_bindings={"field": "客单价", "target": "客单价"},
            selection_mode="fields",
            source_method={"id": "descriptive_profile_single_field_text", "family": "descriptive"},
        )
    )
    learned_id = saved["method"]["id"]
    frame = pd.DataFrame(
        {
            "订单": ["a", "b", "c", "d"],
            "客单价": [120, 240, 180, 320],
            "渠道": ["搜索", "搜索", "社交", "直营"],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=[learned_id],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    route = next(item for item in result["data"]["routed_methods"] if item["id"] == learned_id)
    method_card = route["method_card"]
    assert method_card["field_bindings"]["field"] == "客单价"
    assert method_card["field_bindings"]["target"] == "客单价"
    assert method_card["selection_mode"] == "fields"
    assert method_card["binding_source"] == "saved_method_card"


def test_lab_report_public_contract_filters_internal_tokens_and_duplicates_actions() -> None:
    charts = [
        {"kind": "bubble", "x_label": "revenue", "y_label": "cost"},
        {"kind": "quadrant", "x_label": "revenue", "y_label": "cost"},
        {"kind": "histogram", "x_label": "revenue", "y_label": ""},
        {"kind": "heatmap", "x_label": "", "y_label": ""},
        {"kind": "line", "x_label": "date", "y_label": "revenue"},
    ]
    chart_refs = [_chart_export_ref(chart, index) for index, chart in enumerate(charts, start=1)]
    assert len(set(chart_refs)) == len(chart_refs)
    assert chart_refs[0] == "chart:001-bubble-revenue-cost"
    assert chart_refs[1] == "chart:002-quadrant-revenue-cost"

    payload = _deterministic_agent_review_payload(
        request=AutoAnalysisRequest(dataset_id="demo", active_sheet="Sheet1"),
        dataset_name="demo",
        sheet_name="Sheet1",
        charts=charts,
        method_execution_packages=[
            {"method_run_id": "method_package_001"},
            {"method_run_id": "method_package_002"},
            {"method_run_id": "method_package_003"},
        ],
        generated_at="2026-05-31T00:00:00Z",
    )
    actions = [item["action"] for item in payload["consolidated_actions"]]
    assert len(actions) >= 5
    assert len(set(actions)) == len(actions)
    assert actions[0] != actions[1]
    assert "气泡" in actions[0]
    assert "象限" in actions[1]
    assert not _reader_facing_internal_leakage_hits(
        "## 审稿结论\n证据根目录：已生成并列入下载清单。\n图表证据 001-bubble-revenue-cost"
    )
    assert set(
        _reader_facing_internal_leakage_hits(
            "runtime_status=deterministic_agent_review_completed method_package_001 method_artifacts external_skill anthropics Agent 审稿"
        )
    ) >= {"runtime_status", "method_package", "method_artifacts", "external_skill", "anthropics", "Agent 审稿"}


def test_reader_facing_html_preserves_links_but_hides_internal_paths() -> None:
    markdown = "\n".join(
        [
            "# 测试报告",
            "VISUAL: title=方法预览; image=method_artifacts/method_001/preview.png; csv=method_artifacts/method_001/data.csv; xlsx=method_artifacts/method_001/data.xlsx; json=method_artifacts/method_001/data.json; question=这个方法产物支撑了报告中的哪一条判断？; insight=预览图展示关键行; impact=发布前复核 CSV、XLSX 和 JSON; boundary=正式结论仍需回到证据文件; evidence=方法证据 001",
            "",
            "| 路径 | 说明 |",
            "| --- | --- |",
            "| method_artifacts/method_001/data.csv | 可下载文件 |",
        ]
    )
    html = _reader_facing_html(_markdown_to_lab_report_html(markdown, "测试报告"))
    visible_text = _reader_visible_html_text(html)

    assert 'href="method_artifacts/method_001/data.csv"' in html
    assert 'src="method_artifacts/method_001/preview.png"' in html
    assert "method_artifacts" not in visible_text
    assert "方法证据文件已加入下载清单" in visible_text
    assert not _reader_facing_internal_leakage_hits(visible_text)


def test_reader_facing_markdown_renders_chart_markers_as_figure_blocks() -> None:
    markdown = "\n".join(
        [
            "# Demo",
            "CHART: title=Revenue chart; kind=scatter; image=chart_assets/001/chart.png; json=chart_assets/001/chart.json; question=What changed?; insight=Revenue rose; impact=Prioritize growth; boundary=Correlation only; evidence_detail=rows=50,000、corr=1.00; evidence=chart file",
        ]
    )
    reader_markdown = auto_analysis_service._reader_facing_markdown(markdown)

    assert "CHART:" not in reader_markdown
    assert "kind=" not in reader_markdown
    assert "image=" not in reader_markdown
    assert "#### Figure 1:" in reader_markdown
    assert "![Revenue chart](chart_assets/001/chart.png)" in reader_markdown
    assert "[JSON 证据](chart_assets/001/chart.json)" in reader_markdown
    assert "读图问题：What changed?" in reader_markdown
    assert "证据数字：rows=50,000" in reader_markdown
    assert not _reader_facing_internal_leakage_hits(reader_markdown)
    html = _reader_facing_html(_markdown_to_lab_report_html(reader_markdown, "Demo"))
    assert 'class="markdown-embedded-image"' in html
    assert '<img src="chart_assets/001/chart.png"' in html


def test_method_visual_marker_and_sampling_note_are_reader_facing_chinese() -> None:
    marker = _method_visual_marker(
        {
            "method_run_id": "method_package_001",
            "method_name": "收入分布",
            "artifact_exports": {
                "preview_png_path": "E:/tmp/report/method_artifacts/method_001/preview.png",
                "data_csv_path": "E:/tmp/report/method_artifacts/method_001/data.csv",
                "data_xlsx_path": "E:/tmp/report/method_artifacts/method_001/data.xlsx",
                "data_json_path": "E:/tmp/report/method_artifacts/method_001/data.json",
            },
        }
    )
    assert "这个方法产物支撑了报告中的哪一条判断" in marker
    assert "Which method output" not in marker
    assert "The preview image" not in marker

    note = _chart_sampling_note(
        {
            "points": [{"x": 1, "y": 2}],
            "sample_policy": {
                "rendered_point_count": 2500,
                "analysis_row_count": 5000,
                "full_row_count": 50000,
                "chunk_size": 2500,
                "chunk_count": 20,
            },
        }
    )
    assert "读图只代表渲染密度" in note
    assert "5,000 行分析工作样本" in note
    assert "50,000 行全量数据/分块证据复核" in note

    assert _business_field_label("derived__month__date") == "月份：日期"
    assert _business_field_label("derived__ratio__revenue__of__cost") == "比值：收入占成本"
    assert _chart_business_question({"business_question": "revenue 与 cost 是否存在异常偏离？"}) == "收入与成本是否存在异常偏离？"


def test_large_sample_lab_report_catalog_registration_returns_without_touching_slow_library(monkeypatch, tmp_path: Path) -> None:
    markdown_path = tmp_path / "lab_report.md"
    html_path = tmp_path / "lab_report.html"
    seed_path = tmp_path / "lab_report_revision_seed.json"
    markdown_path.write_text("# 报告\n", encoding="utf-8")
    html_path.write_text("<html></html>", encoding="utf-8")
    seed_path.write_text("{}", encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("large-sample registration must not touch the slow report library")

    monkeypatch.setattr(auto_analysis_service.shutil, "copy2", fail_if_called)
    monkeypatch.setattr(auto_analysis_service, "upsert_report_catalog_rows", fail_if_called)

    result = _register_lab_report_catalog(
        report_id="large-sample-demo",
        title="Large Sample Demo",
        request=AutoAnalysisRequest(dataset_id="demo", active_sheet="Sheet1"),
        dataset_name="demo",
        sheet_name="Sheet1",
        markdown_path=markdown_path,
        html_path=html_path,
        seed_path=seed_path,
        generated_at="2026-05-31T00:00:00Z",
        source_export_dir=tmp_path,
        lab_report_meta={"quality_status": "passed"},
        large_sample_policy={"large_sample": True, "row_count": 50_000},
    )

    assert result["catalog_status"] == "skipped_large_sample_sync"
    assert result["report_dir"] == str(tmp_path.resolve())
    assert result["html_path"] == "lab_report.html"


def test_large_sample_policy_splits_50000_rows_into_2500_or_1250_chunks() -> None:
    frame = pd.DataFrame({"revenue": range(50_000), "cost": range(50_000)})
    policy = _large_sample_policy_for_frame(frame)

    assert policy["chunking_enabled"] is True
    assert policy["default_chunk_size"] == LARGE_SAMPLE_DEFAULT_CHUNK_SIZE == 2500
    assert policy["default_chunk_count"] == 20
    assert policy["fine_chunk_size"] == LARGE_SAMPLE_FINE_CHUNK_SIZE == 1250
    assert policy["fine_chunk_count"] == 40


def test_report_writer_agent_uses_chunk_evidence_and_direct_answers() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=5000, freq="D"),
            "revenue": [100 + index * 0.5 + (index % 30) * 2 for index in range(5000)],
            "cost": [80 + index * 0.3 for index in range(5000)],
        }
    )
    charts = [
        {
            "kind": "line",
            "title": "Revenue trend",
            "x_label": "date",
            "y_label": "revenue",
            "x": [str(item.date()) for item in frame["date"].iloc[::100].head(50)],
            "y": [float(item) for item in frame["revenue"].iloc[::100].head(50)],
        },
        {
            "kind": "scatter",
            "title": "Revenue cost relation",
            "x_label": "revenue",
            "y_label": "cost",
            "points": [[float(row.revenue), float(row.cost)] for row in frame.iloc[::100].head(50).itertuples()],
        },
    ]
    policy = _large_sample_policy_for_frame(frame)
    agent = _attach_report_writer_agents(
        charts=charts,
        full_frame=frame,
        analysis_frame=frame.iloc[::10].copy(),
        large_sample_policy=policy,
        generated_at="2026-05-31T00:00:00Z",
    )

    assert agent["runtime_status"] == "passed"
    assert agent["contract"] == "analysis_lab_report_writer_agent_v2"
    assert agent["fallback_policy"] == "fail_quality_gate_when_stage_output_missing"
    assert charts[0]["sample_policy"]["chunk_size"] == 2500
    assert charts[0]["sample_policy"]["chunk_count"] == 2
    required_stages = {
        "evidence_analyst_agent",
        "skill_router_agent",
        "business_judgment_agent",
        "narrative_writer_agent",
        "figure_caption_agent",
        "skeptical_review_agent",
        "final_editor_agent",
    }
    for chart in charts:
        writer = chart["report_writer_agent"]
        assert writer["contract"] == "analysis_lab_chart_report_writer_agent_v2"
        assert writer["pipeline_status"] == "passed"
        assert writer["direct_answer"]
        assert writer["business_judgment"]
        assert writer["caption"]
        assert writer["recommended_action"]
        assert writer["chunk_evidence"]["chunk_size"] == 2500
        assert len(writer["evidence_numbers"]) >= 2
        assert required_stages.issubset(writer.keys())
        assert writer["evidence_analyst_agent"]["sample_scope"]["full_row_count"] == 5000
        assert writer["skill_router_agent"]["selected_skill"] in {
            "time_series_trend",
            "scatter_quadrant_efficiency",
        }
        assert writer["business_judgment_agent"]["business_judgment"]
        assert writer["narrative_writer_agent"]["reader_first_paragraph"]
        assert writer["figure_caption_agent"]["caption"]
        assert writer["figure_caption_agent"]["sample_scope"]["text"]
        assert writer["skeptical_review_agent"]["passed"] is True
        assert writer["final_editor_agent"]["final_caption"]
        forbidden = ["继续观察", "建议复核", "优先看离群点", "只能证明当前样本", "fallback PNG renderer"]
        assert not any(token in writer["business_judgment"] + writer["caption"] for token in forbidden)
    input_contract = _build_report_writer_agent_input(
        request=AutoAnalysisRequest(dataset_id="demo", active_sheet="Sheet1", user_goal="management report"),
        dataset_name="demo.csv",
        sheet_name="Sheet1",
        selected={"target": "revenue"},
        field_profiles=[{"field": "revenue", "semantic_role": "metric"}],
        charts=charts,
        method_execution_packages=[],
        large_sample_policy=policy,
        generated_at="2026-05-31T00:00:00Z",
    )
    assert input_contract["contract"] == "analysis_lab_report_writer_agent_input_v1"
    assert input_contract["normal_path_required"] is True
    assert input_contract["chart_inputs"][0]["required_output"]["minimum_evidence_numbers"] == 2
    assert input_contract["chart_inputs"][0]["sample_scope"]["full_row_count"] == 5000


def test_skeptical_report_writer_review_rejects_vague_or_missing_stage_agent() -> None:
    review = _skeptical_report_writer_review(
        [
            {
                "contract": "analysis_lab_chart_report_writer_agent_v1",
                "direct_answer": "建议复核后继续观察",
                "business_judgment": "建议复核后继续观察",
                "caption": "只能证明当前样本",
                "recommended_action": "",
                "sampling_note": "",
                "evidence_numbers": [{"label": "count", "value": "1"}],
                "source_refs": [],
            }
        ]
    )

    assert review["passed"] is False
    issue_names = {item["issue"] for item in review["issues"]}
    assert "missing_required_agent_fields" in issue_names
    assert "insufficient_numeric_evidence" in issue_names
    assert "forbidden_boilerplate" in issue_names
    assert "missing_stage_agent" in issue_names


def test_method_card_executors_emit_reusable_association_and_time_assets() -> None:
    frame = pd.DataFrame(
        {
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "revenue": [100, 150, 210],
            "cost": [40, 70, 90],
            "units": [2, 3, 5],
        }
    )
    routed_methods = [
        {
            "id": "association_correlation_field_set_data",
            "method_card": {
                "method_id": "association_correlation_field_set_data",
                "executor_hint": "association_executor",
                "field_bindings": {"x": "revenue", "y": "cost", "features": ["units"]},
                "binding_quality": "ready",
                "report_slots": ["chapter"],
                "evidence_refs": ["data:selected_fields"],
            },
        },
        {
            "id": "time_series_trend_time_window_table",
            "method_card": {
                "method_id": "time_series_trend_time_window_table",
                "executor_hint": "time_series_diagnostic_executor",
                "field_bindings": {"time": "order_date", "target": "revenue"},
                "binding_quality": "ready",
                "report_slots": ["chapter"],
                "evidence_refs": ["table:time_series_diagnostics"],
            },
        },
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    association = next(item for item in assets if item["asset_type"] == "association_scan")
    trend = next(item for item in assets if item["asset_type"] == "time_series_summary")
    assert association["payload"]["top_pairs"]
    assert association["payload"]["fields"] == ["revenue", "cost", "units"]
    assert trend["payload"]["target"] == "revenue"
    assert trend["payload"]["change"] == 110


def test_method_card_executor_runs_live_statistical_catalog_card() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100, 150, 210, 260, 330],
            "cost": [40, 70, 90, 120, 160],
            "units": [2, 3, 5, 6, 8],
        }
    )
    routed_methods = [
        {
            "id": "correlation_table",
            "method_card": {
                "method_id": "correlation_table",
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["table"],
                "field_bindings": {"features": ["revenue", "cost", "units"]},
                "binding_quality": "ready",
                "report_slots": ["appendix", "evidence_index"],
                "evidence_refs": ["data:selected_fields"],
            },
        }
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    statistical = next(item for item in assets if item["asset_type"] == "statistical_result")
    payload = statistical["payload"]
    assert payload["analysis_type"] == "correlation"
    assert payload["metrics"]["column_count"] == 3
    assert payload["tables"]
    assert payload["chart"]["kind"] == "heatmap"


def test_method_card_executor_runs_variance_assumption_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "score": [10, 11, 9, 10, 12, 9, 10, 11, 1, 30, 5, 40, 15, 50, -10, 60],
            "segment": ["A"] * 8 + ["B"] * 8,
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "score", "group": "segment"},
                "statistical_options": {"alpha": 0.01},
            },
        }
        for method_id in ["brown_forsythe_data", "bartlett_data"]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"brown_forsythe", "bartlett"} == set(payloads)
    assert payloads["brown_forsythe"]["metrics"]["center"] == "median"
    assert payloads["bartlett"]["metrics"]["center"] == "mean-normality-sensitive"
    for payload in payloads.values():
        assert payload["request"]["alpha"] == 0.01
        assert payload["metrics"]["decision"] == "variance_heterogeneous"
        assert payload["tables"][0]["rows"]


def test_method_card_executor_runs_repeated_measure_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "baseline": [10, 12, 9, 11, 13, 8, 14, 10, 12, 9, 11, 13],
            "month_1": [12, 14, 11, 13, 15, 10, 16, 12, 14, 11, 13, 15],
            "month_2": [15, 17, 14, 16, 18, 13, 19, 15, 17, 14, 16, 18],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "baseline", "features": ["month_1", "month_2"]},
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id in ["repeated_measures_anova_data", "friedman_data"]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"repeated_measures_anova", "friedman"} == set(payloads)
    assert payloads["repeated_measures_anova"]["metrics"]["condition_count"] == 3
    assert payloads["repeated_measures_anova"]["metrics"]["decision"] == "significant"
    assert payloads["friedman"]["metrics"]["kendalls_w"] > 0.8
    assert payloads["friedman"]["metrics"]["decision"] == "significant"
    for payload in payloads.values():
        assert payload["request"]["features"] == ["month_1", "month_2"]
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_multifactor_mean_test_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "score": [
                10,
                11,
                12,
                13,
                15,
                16,
                17,
                18,
                17,
                18,
                19,
                20,
                25,
                26,
                27,
                28,
                14,
                15,
                16,
                17,
                20,
                21,
                22,
                23,
            ],
            "channel": ["organic"] * 8 + ["paid"] * 8 + ["partner"] * 8,
            "region": (["east"] * 4 + ["west"] * 4) * 3,
            "baseline": [8, 9, 10, 11, 12, 13, 14, 15, 10, 11, 12, 13, 16, 17, 18, 19, 11, 12, 13, 14, 15, 16, 17, 18],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id, bindings in [
            ("two_way_anova_data", {"target": "score", "group": "channel", "features": ["region"]}),
            ("ancova_data", {"target": "score", "group": "channel", "features": ["baseline"]}),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"two_way_anova", "ancova"} == set(payloads)
    assert payloads["two_way_anova"]["metrics"]["factor_a"] == "channel"
    assert payloads["two_way_anova"]["metrics"]["factor_b"] == "region"
    assert payloads["two_way_anova"]["metrics"]["decision"] == "significant"
    assert payloads["ancova"]["metrics"]["covariate"] == "baseline"
    assert payloads["ancova"]["metrics"]["decision"] == "significant"
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_extended_mean_test_catalog_cards() -> None:
    before = [10 + (index % 10) for index in range(40)]
    after = [value + 2 + (1 if index % 4 == 0 else 0) for index, value in enumerate(before)]
    frame = pd.DataFrame(
        {
            "score": [101 + (index % 5) for index in range(40)],
            "before": before,
            "after": after,
        }
    )
    routed_methods = [
        {
            "id": "one_sample_ttest_data",
            "method_card": {
                "method_id": "one_sample_ttest_data",
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "score"},
                "statistical_options": {"test_value": 100, "alpha": 0.01},
            },
        },
        {
            "id": "z_test_mean_data",
            "method_card": {
                "method_id": "z_test_mean_data",
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "score"},
                "statistical_options": {"test_value": 100, "population_std": 2.5, "alpha": 0.01},
            },
        },
        {
            "id": "paired_ttest_data",
            "method_card": {
                "method_id": "paired_ttest_data",
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "after", "features": ["before"]},
                "statistical_options": {"alpha": 0.01},
            },
        },
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"one_sample_ttest", "z_test_mean", "paired_ttest"} == set(payloads)
    assert payloads["one_sample_ttest"]["request"]["test_value"] == 100
    assert payloads["z_test_mean"]["request"]["population_std"] == 2.5
    assert payloads["paired_ttest"]["request"]["features"] == ["before"]
    for payload in payloads.values():
        assert payload["request"]["alpha"] == 0.01
        assert payload["metrics"]["decision"] == "significant"
        assert payload["tables"][0]["rows"]


def test_method_card_executor_runs_nonparametric_catalog_cards() -> None:
    before = [10 + (index % 10) for index in range(32)]
    after = [value + 2 + (1 if index % 3 == 0 else 0) for index, value in enumerate(before)]
    frame = pd.DataFrame(
        {
            "before": before,
            "after": after,
            "score": [
                10,
                11,
                9,
                12,
                10,
                11,
                9,
                10,
                18,
                22,
                20,
                21,
                19,
                23,
                18,
                22,
                30,
                38,
                27,
                35,
                32,
                45,
                28,
                40,
                3,
                50,
                5,
                60,
                -10,
                70,
                8,
                90,
            ],
            "segment": ["A"] * 8 + ["B"] * 8 + ["C"] * 8 + ["D"] * 8,
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": alpha},
            },
        }
        for method_id, bindings, alpha in [
            ("wilcoxon_signed_rank_data", {"target": "after", "features": ["before"]}, 0.01),
            ("sign_test_data", {"target": "after", "features": ["before"]}, 0.01),
            ("median_test_data", {"target": "score", "group": "segment"}, 0.05),
            ("fligner_killeen_data", {"target": "score", "group": "segment"}, 0.05),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"wilcoxon_signed_rank", "sign_test", "median_test", "fligner_killeen"} == set(payloads)
    assert payloads["wilcoxon_signed_rank"]["request"]["features"] == ["before"]
    assert payloads["sign_test"]["metrics"]["positive_pairs"] > payloads["sign_test"]["metrics"]["negative_pairs"]
    assert payloads["median_test"]["metrics"]["decision"] == "significant"
    assert payloads["fligner_killeen"]["metrics"]["decision"] == "variance_heterogeneous"
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"


def test_method_card_executor_runs_categorical_association_strength_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "segment": ["enterprise"] * 30 + ["self_serve"] * 30,
            "converted": ["yes"] * 24 + ["no"] * 6 + ["yes"] * 7 + ["no"] * 23,
            "risk_band": ["low"] * 16 + ["medium"] * 10 + ["high"] * 4 + ["low"] * 5 + ["medium"] * 8 + ["high"] * 17,
            "outcome": ["expand"] * 14 + ["renew"] * 10 + ["churn"] * 6 + ["expand"] * 4 + ["renew"] * 8 + ["churn"] * 18,
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id, bindings in [
            ("cramers_v_data", {"target": "outcome", "group": "risk_band"}),
            ("phi_coefficient_data", {"target": "converted", "group": "segment"}),
            ("theils_u_data", {"target": "outcome", "group": "risk_band"}),
            ("goodman_kruskal_lambda_data", {"target": "outcome", "group": "risk_band"}),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"cramers_v", "phi_coefficient", "theils_u", "goodman_kruskal_lambda"} == set(payloads)
    assert payloads["cramers_v"]["metrics"]["cramers_v"] > 0.3
    assert payloads["phi_coefficient"]["metrics"]["absolute_phi"] > 0.45
    assert payloads["theils_u"]["metrics"]["theils_u"] > 0.1
    assert payloads["goodman_kruskal_lambda"]["metrics"]["lambda"] > 0.1
    assert payloads["theils_u"]["metrics"]["reverse_theils_u"] >= 0
    assert payloads["goodman_kruskal_lambda"]["metrics"]["reverse_lambda"] >= 0
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_categorical_agreement_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "before": ["no"] * 16 + ["yes"] * 10 + ["no"] * 6 + ["yes"] * 8,
            "after": ["yes"] * 16 + ["no"] * 10 + ["no"] * 6 + ["yes"] * 8,
            "survey_a": [1] * 14 + [0] * 6 + [1] * 10 + [0] * 10,
            "survey_b": [1] * 10 + [0] * 10 + [1] * 14 + [0] * 6,
            "survey_c": [1] * 6 + [0] * 14 + [1] * 16 + [0] * 4,
            "exposure": ["treated"] * 10 + ["control"] * 10 + ["treated"] * 10 + ["control"] * 10,
            "outcome": ["success"] * 8 + ["failure"] * 2 + ["success"] * 3 + ["failure"] * 7 + ["success"] * 7 + ["failure"] * 3 + ["success"] * 2 + ["failure"] * 8,
            "segment": ["enterprise"] * 20 + ["self_serve"] * 20,
            "reviewer_a": ["approve"] * 18 + ["reject"] * 4 + ["approve"] * 4 + ["reject"] * 14,
            "reviewer_b": ["approve"] * 16 + ["reject"] * 6 + ["approve"] * 6 + ["reject"] * 12,
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id, bindings in [
            ("mcnemar_data", {"target": "after", "features": ["before"]}),
            ("cochran_q_data", {"target": "survey_c", "features": ["survey_a", "survey_b"]}),
            ("cmh_test_data", {"target": "outcome", "group": "exposure", "features": ["segment"]}),
            ("cohens_kappa_data", {"target": "reviewer_b", "features": ["reviewer_a"]}),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"mcnemar", "cochran_q", "cmh_test", "cohens_kappa"} == set(payloads)
    assert payloads["mcnemar"]["request"]["features"] == ["before"]
    assert payloads["mcnemar"]["metrics"]["discordant_pairs"] == 26
    assert payloads["cochran_q"]["metrics"]["condition_count"] == 3
    assert payloads["cmh_test"]["metrics"]["strata_count"] == 2
    assert payloads["cohens_kappa"]["metrics"]["kappa"] > 0.45
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_distribution_diagnostic_catalog_cards() -> None:
    values = [
        -1.62,
        -1.28,
        -1.01,
        -0.88,
        -0.72,
        -0.55,
        -0.38,
        -0.21,
        -0.05,
        0.08,
        0.19,
        0.33,
        0.47,
        0.62,
        0.79,
        0.91,
        1.08,
        1.27,
        1.45,
        1.7,
    ]
    frame = pd.DataFrame({"score": values})
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "score"},
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id in [
            "shapiro_wilk_data",
            "dagostino_k2_data",
            "jarque_bera_data",
            "kolmogorov_smirnov_1samp_data",
            "anderson_darling_data",
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"shapiro_wilk", "dagostino_k2", "jarque_bera", "kolmogorov_smirnov_1samp", "anderson_darling"} == set(payloads)
    assert payloads["shapiro_wilk"]["metrics"]["shapiro_w"] > 0
    assert payloads["dagostino_k2"]["metrics"]["k2_statistic"] >= 0
    assert payloads["jarque_bera"]["metrics"]["jarque_bera_statistic"] >= 0
    assert payloads["kolmogorov_smirnov_1samp"]["metrics"]["reference_distribution"] == "normal"
    assert payloads["anderson_darling"]["metrics"]["anderson_darling_statistic"] > 0
    assert len(payloads["anderson_darling"]["tables"]) == 2
    for payload in payloads.values():
        assert payload["metrics"]["sample_size"] == len(values)
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_descriptive_concentration_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [5, 7, 9, 10, 11, 12, 14, 16, 22, 35, 60, 140],
            "product": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id, bindings in [
            ("quantile_profile_data", {"target": "revenue"}),
            ("trimmed_mean_data", {"target": "revenue"}),
            ("winsorized_summary_data", {"target": "revenue"}),
            ("gini_coefficient_data", {"target": "revenue"}),
            ("pareto_analysis_data", {"target": "revenue", "group": "product"}),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"quantile_profile", "trimmed_mean", "winsorized_summary", "gini_coefficient", "pareto_analysis"} == set(payloads)
    assert payloads["quantile_profile"]["metrics"]["p95"] > payloads["quantile_profile"]["metrics"]["median"]
    assert payloads["trimmed_mean"]["metrics"]["trimmed_mean"] < payloads["trimmed_mean"]["metrics"]["raw_mean"]
    assert payloads["winsorized_summary"]["metrics"]["winsorized_mean"] < payloads["winsorized_summary"]["metrics"]["raw_mean"]
    assert payloads["gini_coefficient"]["metrics"]["gini"] > 0.4
    assert payloads["pareto_analysis"]["metrics"]["top_20_share"] > 0.5
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_foundational_descriptive_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100, 80, 75, 60, 45, 30, 24, 18, 14, 9, 6, 4],
            "channel": ["search", "search", "social", "social", "email", "email", "direct", "direct", "partner", "partner", "retail", "retail"],
            "region": ["east", "east", "east", "west", "west", "west", "north", "north", "south", "south", "south", "south"],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id, bindings in [
            ("descriptive_summary_data", {"target": "revenue"}),
            ("frequency_table_data", {"target": "channel"}),
            ("cross_tabulation_data", {"target": "region", "group": "channel"}),
            ("pivot_summary_data", {"target": "revenue", "group": "channel"}),
            ("segmented_kpi_breakdown_data", {"target": "revenue", "group": "region"}),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"descriptive_summary", "frequency_table", "cross_tabulation", "pivot_summary", "segmented_kpi_breakdown"} == set(payloads)
    assert payloads["descriptive_summary"]["metrics"]["sample_size"] == len(frame)
    assert payloads["frequency_table"]["metrics"]["category_count"] == 6
    assert payloads["cross_tabulation"]["metrics"]["row_categories"] == 6
    assert payloads["pivot_summary"]["metrics"]["top_group"] == "search"
    assert payloads["segmented_kpi_breakdown"]["metrics"]["top_mean_group"] == "east"
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_bivariate_association_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [10, 20, 30, 45, 60, 80, 95, 120, 150, 190, 230, 280],
            "ad_spend": [2, 3, 5, 7, 9, 12, 14, 18, 24, 30, 37, 45],
            "rank_signal": [1, 2, 3, 5, 4, 6, 7, 8, 10, 9, 11, 12],
            "is_enterprise": ["no", "no", "no", "no", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes"],
            "segment": ["starter"] * 4 + ["growth"] * 4 + ["enterprise"] * 4,
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id, bindings in [
            ("pearson_correlation_data", {"target": "revenue", "features": ["ad_spend"]}),
            ("spearman_correlation_data", {"target": "revenue", "features": ["rank_signal"]}),
            ("kendall_tau_data", {"target": "revenue", "features": ["rank_signal"]}),
            ("point_biserial_data", {"target": "revenue", "group": "is_enterprise"}),
            ("eta_squared_data", {"target": "revenue", "group": "segment"}),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"pearson_correlation", "spearman_correlation", "kendall_tau", "point_biserial", "eta_squared"} == set(payloads)
    assert payloads["pearson_correlation"]["metrics"]["correlation"] > 0.95
    assert payloads["spearman_correlation"]["metrics"]["correlation"] > 0.9
    assert payloads["kendall_tau"]["metrics"]["correlation"] > 0.8
    assert payloads["point_biserial"]["metrics"]["abs_correlation"] > 0.6
    assert payloads["eta_squared"]["metrics"]["eta_squared"] > 0.6
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] in {"bar", "scatter"}
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_advanced_association_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "demand": [12, 18, 25, 37, 49, 66, 82, 101, 128, 160, 197, 240],
            "price": [3, 5, 8, 11, 14, 18, 22, 27, 33, 40, 48, 57],
            "seasonality": [1, 2, 1, 3, 2, 4, 3, 5, 4, 6, 5, 7],
            "nonlinear_signal": [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6],
            "u_shape_outcome": [25, 16, 9, 4, 1, 0, 1, 4, 9, 16, 25, 36],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"bootstrap_iterations": 199},
            },
        }
        for method_id, bindings in [
            ("partial_correlation_data", {"target": "demand", "features": ["price", "seasonality"]}),
            ("distance_correlation_data", {"target": "u_shape_outcome", "features": ["nonlinear_signal"]}),
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"partial_correlation", "distance_correlation"} == set(payloads)
    assert payloads["partial_correlation"]["metrics"]["covariates"] == ["seasonality"]
    assert payloads["partial_correlation"]["metrics"]["abs_correlation"] > 0.8
    assert payloads["distance_correlation"]["metrics"]["distance_correlation"] > 0.45
    assert payloads["distance_correlation"]["metrics"]["permutations"] == 199
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "scatter"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_regression_diagnostic_catalog_cards() -> None:
    x = list(range(1, 41))
    residual = [((-1) ** index) * (value / 6) for index, value in enumerate(x)]
    frame = pd.DataFrame(
        {
            "revenue": [50 + 3 * value + residual[index] for index, value in enumerate(x)],
            "ad_spend": x,
            "season_index": [(index % 4) + 1 for index in range(40)],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "revenue", "features": ["ad_spend", "season_index"]},
                "statistical_options": {"alpha": 0.05},
            },
        }
        for method_id in ["breusch_pagan_data", "white_test_data", "durbin_watson_data"]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"breusch_pagan", "white_test", "durbin_watson"} == set(payloads)
    for analysis_type in ["breusch_pagan", "white_test"]:
        payload = payloads[analysis_type]
        assert payload["metrics"]["sample_size"] == 40
        assert payload["metrics"]["feature_count"] == 2
        assert payload["metrics"]["p_value"] is not None
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "scatter"
        assert "Decision cue:" in payload["narrative"]

    durbin_payload = payloads["durbin_watson"]
    assert durbin_payload["metrics"]["sample_size"] == 40
    assert 0 <= durbin_payload["metrics"]["durbin_watson_statistic"] <= 4
    assert durbin_payload["tables"][0]["rows"]
    assert durbin_payload["chart"]["kind"] == "scatter"
    assert "Decision cue:" in durbin_payload["narrative"]


def test_method_card_executor_runs_regularized_regression_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [20 + index * 3 + (index % 5) * 1.5 + (25 if index == 18 else 0) for index in range(40)],
            "ad_spend": [index + 1 for index in range(40)],
            "price": [10 + (index % 7) for index in range(40)],
            "season": [(index % 4) + 1 for index in range(40)],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"target": "revenue", "features": ["ad_spend", "price", "season"]},
                "statistical_options": {"regularization_strength": 0.1, "l1_ratio": 0.4, "quantile": 0.75},
            },
        }
        for method_id in [
            "ridge_regression_data",
            "lasso_regression_data",
            "elastic_net_data",
            "robust_regression_data",
            "quantile_regression_data",
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"ridge_regression", "lasso_regression", "elastic_net", "robust_regression", "quantile_regression"} == set(payloads)
    for analysis_type in ["ridge_regression", "lasso_regression", "elastic_net"]:
        payload = payloads[analysis_type]
        assert payload["metrics"]["sample_size"] == 40
        assert payload["metrics"]["regularization_strength"] == 0.1
        assert payload["metrics"]["strongest_term"] == "ad_spend"
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]

    assert payloads["elastic_net"]["metrics"]["l1_ratio"] == 0.4
    assert payloads["robust_regression"]["metrics"]["sample_size"] == 40
    assert payloads["robust_regression"]["metrics"]["strongest_term"] == "ad_spend"
    assert payloads["quantile_regression"]["metrics"]["quantile"] == 0.75
    assert payloads["quantile_regression"]["metrics"]["strongest_term"] == "ad_spend"
    for payload in [payloads["robust_regression"], payloads["quantile_regression"]]:
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_robust_inference_catalog_cards() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=36).astype(str),
            "score": [10, 11, 12, 13, 12, 14, 15, 13, 16, 17, 18, 16, 30, 32, 35, 34, 36, 38, 40, 39, 41, 43, 44, 46, 20, 22, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31],
            "segment": ["A"] * 12 + ["B"] * 12 + ["C"] * 12,
        }
    )
    bindings_by_method = {
        "mood_median_data": {"target": "score", "group": "segment"},
        "ks_two_sample_data": {"target": "score", "group": "segment"},
        "runs_test_data": {"target": "score", "time": "date"},
        "permutation_test_data": {"target": "score", "group": "segment"},
        "bootstrap_ci_data": {"target": "score"},
    }
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": bindings,
                "statistical_options": {"alpha": 0.05, "bootstrap_iterations": 300},
            },
        }
        for method_id, bindings in bindings_by_method.items()
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"mood_median", "ks_two_sample", "runs_test", "permutation_test", "bootstrap_ci"} == set(payloads)
    assert payloads["mood_median"]["metrics"]["sample_size"] == 36
    assert payloads["ks_two_sample"]["metrics"]["sample_a_size"] == 12
    assert payloads["runs_test"]["metrics"]["sample_size"] == 36
    assert payloads["permutation_test"]["metrics"]["iterations"] == 300
    assert payloads["bootstrap_ci"]["metrics"]["iterations"] == 300
    for payload in payloads.values():
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] == "bar"
        assert "Decision cue:" in payload["narrative"]


def test_method_card_executor_runs_time_series_catalog_cards() -> None:
    dates = pd.date_range("2026-01-01", periods=48, freq="D")
    frame = pd.DataFrame(
        {
            "date": dates.astype(str),
            "revenue": [100 + index * 2 + (8 if index % 7 in {5, 6} else 0) + ((-1) ** index) * 1.5 for index in range(48)],
        }
    )
    routed_methods = [
        {
            "id": method_id,
            "method_card": {
                "method_id": method_id,
                "executor_hint": "statistical_analysis_executor",
                "output_types": ["data"],
                "field_bindings": {"time": "date", "target": "revenue"},
                "statistical_options": {"alpha": 0.05, "window": 5, "lag": 8},
            },
        }
        for method_id in [
            "moving_average_data",
            "autocorrelation_data",
            "partial_autocorrelation_data",
            "ljung_box_data",
            "adf_test_data",
        ]
    ]

    assets = execute_method_card_assets(frame, routed_methods, [])
    payloads = {
        item["payload"]["analysis_type"]: item["payload"]
        for item in assets
        if item["asset_type"] == "statistical_result"
    }

    assert {"moving_average", "autocorrelation", "partial_autocorrelation", "ljung_box", "adf_test"} == set(payloads)
    assert payloads["moving_average"]["metrics"]["window"] == 5
    assert payloads["autocorrelation"]["metrics"]["lag_count"] == 8
    assert payloads["partial_autocorrelation"]["metrics"]["lag_count"] >= 1
    assert payloads["ljung_box"]["metrics"]["p_value"] is not None
    assert payloads["adf_test"]["metrics"]["p_value"] is not None
    for payload in payloads.values():
        assert payload["metrics"]["sample_size"] == 48
        assert payload["tables"][0]["rows"]
        assert payload["chart"]["kind"] in {"bar", "scatter"}
        assert payload["request"]["group_column"] == "date"
        assert "Decision cue:" in payload["narrative"]


def test_categorical_association_strength_boundaries_are_explicit() -> None:
    non_binary_frame = pd.DataFrame(
        {
            "segment": ["A", "A", "B", "B", "C", "C"],
            "outcome": ["yes", "no", "yes", "no", "yes", "no"],
        }
    )
    with pytest.raises(ValueError, match="2x2"):
        run_statistical_analysis(
            non_binary_frame,
            StatisticRequest(
                dataset_id="demo",
                analysis_type="phi_coefficient",
                target="outcome",
                group_column="segment",
            ),
        )

    constant_outcome_frame = pd.DataFrame(
        {
            "segment": ["A", "A", "B", "B"],
            "outcome": ["yes", "yes", "yes", "yes"],
        }
    )
    for analysis_type in ["theils_u", "goodman_kruskal_lambda"]:
        with pytest.raises(ValueError, match="at least two"):
            run_statistical_analysis(
                constant_outcome_frame,
                StatisticRequest(
                    dataset_id="demo",
                    analysis_type=analysis_type,
                    target="outcome",
                    group_column="segment",
                ),
            )


def test_categorical_agreement_boundaries_are_explicit() -> None:
    paired_frame = pd.DataFrame(
        {
            "before": ["no", "yes", "no", "yes"],
            "after": ["yes", "yes", "no", "no"],
            "segment": ["A", "A", "B", "B"],
            "outcome": ["success", "failure", "success", "failure"],
        }
    )
    with pytest.raises(ValueError, match="paired binary feature"):
        run_statistical_analysis(
            paired_frame,
            StatisticRequest(dataset_id="demo", analysis_type="mcnemar", target="after"),
        )

    with pytest.raises(ValueError, match="at least three related binary columns"):
        run_statistical_analysis(
            paired_frame,
            StatisticRequest(dataset_id="demo", analysis_type="cochran_q", target="after", features=["before"]),
        )

    with pytest.raises(ValueError, match="stratification column"):
        run_statistical_analysis(
            paired_frame,
            StatisticRequest(dataset_id="demo", analysis_type="cmh_test", target="outcome", group_column="segment"),
        )

    with pytest.raises(ValueError, match="two categorical rating columns"):
        run_statistical_analysis(
            paired_frame,
            StatisticRequest(dataset_id="demo", analysis_type="cohens_kappa", target="after"),
        )


def test_repeated_measure_boundaries_are_explicit() -> None:
    repeated_frame = pd.DataFrame(
        {
            "baseline": [1.0, 2.0, 3.0, 4.0],
            "month_1": [1.2, 2.2, 3.2, 4.2],
            "month_2": [1.5, None, 3.5, 4.5],
        }
    )
    with pytest.raises(ValueError, match="at least three repeated numeric columns"):
        run_statistical_analysis(
            repeated_frame,
            StatisticRequest(dataset_id="demo", analysis_type="repeated_measures_anova", target="baseline", features=["month_1"]),
        )

    with pytest.raises(ValueError, match="at least three complete subjects"):
        run_statistical_analysis(
            repeated_frame.iloc[:2],
            StatisticRequest(dataset_id="demo", analysis_type="friedman", target="baseline", features=["month_1", "month_2"]),
        )


def test_multifactor_mean_boundaries_are_explicit() -> None:
    frame = pd.DataFrame(
        {
            "score": [1, 2, 3, 4, 5, 6],
            "channel": ["A", "A", "B", "B", "A", "B"],
            "region": ["east"] * 6,
            "baseline": [1, 2, 3, 4, 5, 6],
        }
    )
    with pytest.raises(ValueError, match="second categorical factor"):
        run_statistical_analysis(
            frame,
            StatisticRequest(dataset_id="demo", analysis_type="two_way_anova", target="score", group_column="channel"),
        )

    with pytest.raises(ValueError, match="at least two levels"):
        run_statistical_analysis(
            frame,
            StatisticRequest(dataset_id="demo", analysis_type="two_way_anova", target="score", group_column="channel", features=["region"]),
        )

    with pytest.raises(ValueError, match="non-constant numeric covariate"):
        run_statistical_analysis(
            frame.assign(baseline=1),
            StatisticRequest(dataset_id="demo", analysis_type="ancova", target="score", group_column="channel", features=["baseline"]),
        )


def test_distribution_diagnostic_boundaries_are_explicit() -> None:
    tiny_frame = pd.DataFrame({"score": [1.0, 2.0]})
    with pytest.raises(ValueError, match="at least 3"):
        run_statistical_analysis(
            tiny_frame,
            StatisticRequest(dataset_id="demo", analysis_type="shapiro_wilk", target="score"),
        )

    short_frame = pd.DataFrame({"score": [1.0, 2.0, 3.0, 4.0, 5.0]})
    with pytest.raises(ValueError, match="at least 8"):
        run_statistical_analysis(
            short_frame,
            StatisticRequest(dataset_id="demo", analysis_type="dagostino_k2", target="score"),
        )

    constant_frame = pd.DataFrame({"score": [7.0] * 12})
    for analysis_type in [
        "shapiro_wilk",
        "dagostino_k2",
        "jarque_bera",
        "kolmogorov_smirnov_1samp",
        "anderson_darling",
    ]:
        with pytest.raises(ValueError, match="non-constant"):
            run_statistical_analysis(
                constant_frame,
                StatisticRequest(dataset_id="demo", analysis_type=analysis_type, target="score"),
            )


def test_descriptive_concentration_boundaries_are_explicit() -> None:
    one_row_frame = pd.DataFrame({"revenue": [100]})
    with pytest.raises(ValueError, match="at least two"):
        run_statistical_analysis(
            one_row_frame,
            StatisticRequest(dataset_id="demo", analysis_type="quantile_profile", target="revenue"),
        )

    negative_frame = pd.DataFrame({"revenue": [10, -3, 5], "product": ["A", "B", "C"]})
    for analysis_type in ["gini_coefficient", "pareto_analysis"]:
        with pytest.raises(ValueError, match="non-negative"):
            run_statistical_analysis(
                negative_frame,
                StatisticRequest(
                    dataset_id="demo",
                    analysis_type=analysis_type,
                    target="revenue",
                    group_column="product" if analysis_type == "pareto_analysis" else None,
                ),
            )

    zero_frame = pd.DataFrame({"revenue": [0, 0, 0], "product": ["A", "B", "C"]})
    for analysis_type in ["gini_coefficient", "pareto_analysis"]:
        with pytest.raises(ValueError, match="positive total"):
            run_statistical_analysis(
                zero_frame,
                StatisticRequest(
                    dataset_id="demo",
                    analysis_type=analysis_type,
                    target="revenue",
                    group_column="product" if analysis_type == "pareto_analysis" else None,
                ),
            )

    with pytest.raises(ValueError, match="grouping column"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3]}),
            StatisticRequest(dataset_id="demo", analysis_type="pareto_analysis", target="revenue"),
        )


def test_foundational_descriptive_boundaries_are_explicit() -> None:
    one_row_frame = pd.DataFrame({"revenue": [100]})
    with pytest.raises(ValueError, match="at least two"):
        run_statistical_analysis(
            one_row_frame,
            StatisticRequest(dataset_id="demo", analysis_type="descriptive_summary", target="revenue"),
        )

    with pytest.raises(ValueError, match="categorical field"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3]}),
            StatisticRequest(dataset_id="demo", analysis_type="frequency_table"),
        )

    with pytest.raises(ValueError, match="second categorical field"):
        run_statistical_analysis(
            pd.DataFrame({"channel": ["A", "B", "A"]}),
            StatisticRequest(dataset_id="demo", analysis_type="cross_tabulation", target="channel"),
        )

    with pytest.raises(ValueError, match="grouping column"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3]}),
            StatisticRequest(dataset_id="demo", analysis_type="pivot_summary", target="revenue"),
        )

    with pytest.raises(ValueError, match="grouping column"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3]}),
            StatisticRequest(dataset_id="demo", analysis_type="segmented_kpi_breakdown", target="revenue"),
        )


def test_bivariate_association_boundaries_are_explicit() -> None:
    with pytest.raises(ValueError, match="second numeric field"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3]}),
            StatisticRequest(dataset_id="demo", analysis_type="pearson_correlation", target="revenue"),
        )

    with pytest.raises(ValueError, match="non-constant"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 1, 1], "ad_spend": [2, 3, 4]}),
            StatisticRequest(dataset_id="demo", analysis_type="spearman_correlation", target="revenue", features=["ad_spend"]),
        )

    with pytest.raises(ValueError, match="exactly two"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3, 4, 5, 6], "segment": ["A", "B", "C", "A", "B", "C"]}),
            StatisticRequest(dataset_id="demo", analysis_type="point_biserial", target="revenue", group_column="segment"),
        )

    with pytest.raises(ValueError, match="at least two groups"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3, 4], "segment": ["A", "A", "A", "A"]}),
            StatisticRequest(dataset_id="demo", analysis_type="eta_squared", target="revenue", group_column="segment"),
        )

    with pytest.raises(ValueError, match="at least one numeric covariate"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3, 4, 5, 6], "ad_spend": [2, 3, 4, 5, 6, 7]}),
            StatisticRequest(dataset_id="demo", analysis_type="partial_correlation", target="revenue", features=["ad_spend"]),
        )

    with pytest.raises(ValueError, match="non-constant numeric fields"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 1, 1, 1], "ad_spend": [2, 3, 4, 5]}),
            StatisticRequest(dataset_id="demo", analysis_type="distance_correlation", target="revenue", features=["ad_spend"]),
        )


def test_regression_diagnostic_boundaries_are_explicit() -> None:
    with pytest.raises(ValueError, match="at least one numeric feature"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}),
            StatisticRequest(dataset_id="demo", analysis_type="breusch_pagan", target="revenue"),
        )

    with pytest.raises(ValueError, match="Not enough complete rows"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3, 4, 5], "ad_spend": [2, 3, 4, 5, 6]}),
            StatisticRequest(dataset_id="demo", analysis_type="white_test", target="revenue", features=["ad_spend"]),
        )

    with pytest.raises(ValueError, match="non-constant numeric target"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1.0] * 14, "ad_spend": list(range(14))}),
            StatisticRequest(dataset_id="demo", analysis_type="durbin_watson", target="revenue", features=["ad_spend"]),
        )

    with pytest.raises(ValueError, match="non-constant numeric features"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": list(range(14)), "ad_spend": [3.0] * 14}),
            StatisticRequest(dataset_id="demo", analysis_type="breusch_pagan", target="revenue", features=["ad_spend"]),
        )


def test_regularized_regression_boundaries_are_explicit() -> None:
    with pytest.raises(ValueError, match="at least one numeric feature"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": list(range(14))}),
            StatisticRequest(dataset_id="demo", analysis_type="ridge_regression", target="revenue"),
        )

    with pytest.raises(ValueError, match="Not enough complete rows"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1, 2, 3], "ad_spend": [2, 3, 4]}),
            StatisticRequest(dataset_id="demo", analysis_type="quantile_regression", target="revenue", features=["ad_spend"]),
        )

    with pytest.raises(ValueError, match="non-constant numeric target"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": [1.0] * 14, "ad_spend": list(range(14))}),
            StatisticRequest(dataset_id="demo", analysis_type="robust_regression", target="revenue", features=["ad_spend"]),
        )

    with pytest.raises(ValueError, match="non-constant numeric features"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": list(range(14)), "ad_spend": [3.0] * 14}),
            StatisticRequest(dataset_id="demo", analysis_type="lasso_regression", target="revenue", features=["ad_spend"]),
        )


def test_robust_inference_boundaries_are_explicit() -> None:
    with pytest.raises(ValueError, match="grouping column"):
        run_statistical_analysis(
            pd.DataFrame({"score": [1, 2, 3, 4, 5, 6]}),
            StatisticRequest(dataset_id="demo", analysis_type="mood_median", target="score"),
        )

    with pytest.raises(ValueError, match="At least two groups"):
        run_statistical_analysis(
            pd.DataFrame({"score": [1, 2, 3, 4], "segment": ["A", "A", "A", "A"]}),
            StatisticRequest(dataset_id="demo", analysis_type="ks_two_sample", target="score", group_column="segment"),
        )

    with pytest.raises(ValueError, match="at least 10"):
        run_statistical_analysis(
            pd.DataFrame({"score": [1, 2, 3, 4]}),
            StatisticRequest(dataset_id="demo", analysis_type="runs_test", target="score"),
        )

    with pytest.raises(ValueError, match="at least two observations per group"):
        run_statistical_analysis(
            pd.DataFrame({"score": [1, 2, 3], "segment": ["A", "A", "B"]}),
            StatisticRequest(dataset_id="demo", analysis_type="permutation_test", target="score", group_column="segment"),
        )

    with pytest.raises(ValueError, match="non-constant"):
        run_statistical_analysis(
            pd.DataFrame({"score": [7.0] * 8}),
            StatisticRequest(dataset_id="demo", analysis_type="bootstrap_ci", target="score"),
        )


def test_time_series_boundaries_are_explicit() -> None:
    with pytest.raises(ValueError, match="time field"):
        run_statistical_analysis(
            pd.DataFrame({"revenue": list(range(12))}),
            StatisticRequest(dataset_id="demo", analysis_type="moving_average", target="revenue"),
        )

    with pytest.raises(ValueError, match="at least 8"):
        run_statistical_analysis(
            pd.DataFrame({"date": pd.date_range("2026-01-01", periods=4), "revenue": [1, 2, 3, 4]}),
            StatisticRequest(dataset_id="demo", analysis_type="autocorrelation", target="revenue", group_column="date"),
        )

    with pytest.raises(ValueError, match="non-constant"):
        run_statistical_analysis(
            pd.DataFrame({"date": pd.date_range("2026-01-01", periods=12), "revenue": [7.0] * 12}),
            StatisticRequest(dataset_id="demo", analysis_type="adf_test", target="revenue", group_column="date"),
        )


def test_auto_analysis_routes_live_statistical_card_into_local_execution() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100, 150, 210, 260, 330, 390],
            "cost": [40, 70, 90, 120, 160, 200],
            "units": [2, 3, 5, 6, 8, 10],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["correlation_table"],
            method_field_bindings={"correlation_table": {"features": ["revenue", "cost", "units"]}},
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    route = result["data"]["routed_methods"][0]
    assert route["method_card"]["executor_hint"] == "statistical_analysis_executor"
    execution = result["data"]["method_card_executions"][0]
    assert execution["asset_type"] == "statistical_result"
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    asset = result["data"]["method_execution_assets"][0]
    assert asset["payload"]["analysis_type"] == "correlation"
    assert asset["payload"]["metrics"]["column_count"] == 3


def test_auto_analysis_statistical_options_reach_live_executor() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100, 150, 210, 260, 330, 390, 450, 510, 580, 650, 720, 800],
            "cost": [40, 70, 90, 120, 160, 200, 230, 280, 330, 380, 420, 470],
            "units": [2, 3, 5, 6, 8, 10, 11, 13, 15, 17, 19, 22],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["kmeans_data"],
            method_run_specs=[
                {
                    "run_id": "kmeans-custom",
                    "method_id": "kmeans_data",
                    "label": "Two-cluster segmentation",
                    "field_bindings": {"features": ["revenue", "cost", "units"]},
                    "statistical_options": {"clusters": 2},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    asset = result["data"]["method_execution_assets"][0]
    assert asset["payload"]["analysis_type"] == "kmeans"
    assert asset["payload"]["request"]["clusters"] == 2
    assert asset["payload"]["metrics"]["clusters"] == 2


def test_auto_analysis_runs_one_sample_mean_card_with_test_value() -> None:
    frame = pd.DataFrame({"score": [101 + (index % 5) for index in range(40)]})

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["z_test_mean_data"],
            method_run_specs=[
                {
                    "run_id": "z-test-custom",
                    "method_id": "z_test_mean_data",
                    "field_bindings": {"target": "score"},
                    "statistical_options": {"test_value": 100, "population_std": 2.5, "alpha": 0.01},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "z_test_mean"
    assert payload["request"]["test_value"] == 100
    assert payload["request"]["population_std"] == 2.5
    assert payload["metrics"]["decision"] == "significant"
    assert payload["metrics"]["population_std_supplied"] is True


def test_auto_analysis_runs_nonparametric_variance_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "score": [10, 11, 9, 10, 12, 9, 10, 11, 1, 30, 5, 40, 15, 50, -10, 60, 8, 9, 10, 11, 10, 9, 10, 12],
            "segment": ["A"] * 8 + ["B"] * 8 + ["C"] * 8,
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["fligner_killeen_data"],
            method_run_specs=[
                {
                    "run_id": "fligner-custom",
                    "method_id": "fligner_killeen_data",
                    "field_bindings": {"target": "score", "group": "segment"},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Variance heterogeneity" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "fligner_killeen"
    assert payload["metrics"]["decision"] == "variance_heterogeneous"
    assert payload["metrics"]["groups"] == 3
    assert payload["tables"][0]["rows"]


def test_auto_analysis_runs_categorical_association_strength_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "risk_band": ["low"] * 16 + ["medium"] * 10 + ["high"] * 4 + ["low"] * 5 + ["medium"] * 8 + ["high"] * 17,
            "outcome": ["expand"] * 14 + ["renew"] * 10 + ["churn"] * 6 + ["expand"] * 4 + ["renew"] * 8 + ["churn"] * 18,
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["theils_u_data"],
            method_run_specs=[
                {
                    "run_id": "theils-u-custom",
                    "method_id": "theils_u_data",
                    "field_bindings": {"target": "outcome", "group": "risk_band"},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "categorical association" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "theils_u"
    assert payload["metrics"]["theils_u"] > 0.1
    assert payload["metrics"]["decision"] == "directional_association"
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_categorical_agreement_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "reviewer_a": ["approve"] * 18 + ["reject"] * 4 + ["approve"] * 4 + ["reject"] * 14,
            "reviewer_b": ["approve"] * 16 + ["reject"] * 6 + ["approve"] * 6 + ["reject"] * 12,
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["cohens_kappa_data"],
            method_run_specs=[
                {
                    "run_id": "cohens-kappa-custom",
                    "method_id": "cohens_kappa_data",
                    "field_bindings": {"target": "reviewer_b", "features": ["reviewer_a"]},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Kappa" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "cohens_kappa"
    assert payload["metrics"]["kappa"] > 0.45
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_distribution_diagnostic_card_with_guidance() -> None:
    frame = pd.DataFrame({"score": [-2.1, -1.4, -0.8, -0.4, -0.1, 0.2, 0.4, 0.7, 1.1, 1.6, 2.0, 3.9]})

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["jarque_bera_data"],
            method_run_specs=[
                {
                    "run_id": "jarque-bera-custom",
                    "method_id": "jarque_bera_data",
                    "field_bindings": {"target": "score"},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "normality" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "jarque_bera"
    assert payload["metrics"]["jarque_bera_statistic"] >= 0
    assert payload["metrics"]["sample_size"] == 12
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_descriptive_concentration_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [5, 7, 9, 10, 11, 12, 14, 16, 22, 35, 60, 140],
            "product": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["pareto_analysis_data"],
            method_run_specs=[
                {
                    "run_id": "pareto-custom",
                    "method_id": "pareto_analysis_data",
                    "field_bindings": {"target": "revenue", "group": "product"},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "top" in execution["result_summary"].lower()
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "pareto_analysis"
    assert payload["metrics"]["top_20_share"] > 0.5
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_foundational_descriptive_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100, 80, 75, 60, 45, 30, 24, 18, 14, 9, 6, 4],
            "region": ["east", "east", "east", "west", "west", "west", "north", "north", "south", "south", "south", "south"],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["segmented_kpi_breakdown_data"],
            method_run_specs=[
                {
                    "run_id": "segmented-kpi-custom",
                    "method_id": "segmented_kpi_breakdown_data",
                    "field_bindings": {"target": "revenue", "group": "region"},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "KPI" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "segmented_kpi_breakdown"
    assert payload["metrics"]["top_mean_group"] == "east"
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_bivariate_association_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [10, 20, 30, 45, 60, 80, 95, 120, 150, 190, 230, 280],
            "ad_spend": [2, 3, 5, 7, 9, 12, 14, 18, 24, 30, 37, 45],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["pearson_correlation_data"],
            method_run_specs=[
                {
                    "run_id": "pearson-custom",
                    "method_id": "pearson_correlation_data",
                    "field_bindings": {"target": "revenue", "features": ["ad_spend"]},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Pearson" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "pearson_correlation"
    assert payload["metrics"]["correlation"] > 0.95
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_advanced_association_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "demand": [12, 18, 25, 37, 49, 66, 82, 101, 128, 160, 197, 240],
            "price": [3, 5, 8, 11, 14, 18, 22, 27, 33, 40, 48, 57],
            "seasonality": [1, 2, 1, 3, 2, 4, 3, 5, 4, 6, 5, 7],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["partial_correlation_data"],
            method_run_specs=[
                {
                    "run_id": "partial-correlation-custom",
                    "method_id": "partial_correlation_data",
                    "field_bindings": {"target": "demand", "features": ["price", "seasonality"]},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Partial" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "partial_correlation"
    assert payload["metrics"]["covariates"] == ["seasonality"]
    assert payload["metrics"]["abs_correlation"] > 0.8
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_regression_diagnostic_card_with_guidance() -> None:
    x = list(range(1, 41))
    residual = [((-1) ** index) * (value / 6) for index, value in enumerate(x)]
    frame = pd.DataFrame(
        {
            "revenue": [50 + 3 * value + residual[index] for index, value in enumerate(x)],
            "ad_spend": x,
            "season_index": [(index % 4) + 1 for index in range(40)],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["breusch_pagan_data"],
            method_run_specs=[
                {
                    "run_id": "breusch-pagan-custom",
                    "method_id": "breusch_pagan_data",
                    "field_bindings": {"target": "revenue", "features": ["ad_spend", "season_index"]},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Breusch-Pagan" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "breusch_pagan"
    assert payload["metrics"]["sample_size"] == 40
    assert payload["metrics"]["p_value"] is not None
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_regularized_regression_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [20 + index * 3 + (index % 5) * 1.5 + (25 if index == 18 else 0) for index in range(40)],
            "ad_spend": [index + 1 for index in range(40)],
            "price": [10 + (index % 7) for index in range(40)],
            "season": [(index % 4) + 1 for index in range(40)],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["elastic_net_data"],
            method_run_specs=[
                {
                    "run_id": "elastic-net-custom",
                    "method_id": "elastic_net_data",
                    "field_bindings": {"target": "revenue", "features": ["ad_spend", "price", "season"]},
                    "statistical_options": {"regularization_strength": 0.1, "l1_ratio": 0.4},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Elastic Net" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "elastic_net"
    assert payload["metrics"]["regularization_strength"] == 0.1
    assert payload["metrics"]["l1_ratio"] == 0.4
    assert payload["metrics"]["strongest_term"] == "ad_spend"
    assert payload["request"]["features"] == ["ad_spend", "price", "season"]
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_robust_inference_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "score": [10, 11, 12, 13, 12, 14, 15, 13, 16, 17, 18, 16, 30, 32, 35, 34, 36, 38, 40, 39, 41, 43, 44, 46],
            "segment": ["A"] * 12 + ["B"] * 12,
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["permutation_test_data"],
            method_run_specs=[
                {
                    "run_id": "permutation-custom",
                    "method_id": "permutation_test_data",
                    "field_bindings": {"target": "score", "group": "segment"},
                    "statistical_options": {"bootstrap_iterations": 300, "alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Permutation test" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "permutation_test"
    assert payload["metrics"]["iterations"] == 300
    assert payload["request"]["bootstrap_iterations"] == 300
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_time_series_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=48, freq="D").astype(str),
            "revenue": [100 + index * 2 + (8 if index % 7 in {5, 6} else 0) for index in range(48)],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["moving_average_data"],
            method_run_specs=[
                {
                    "run_id": "moving-average-custom",
                    "method_id": "moving_average_data",
                    "field_bindings": {"time": "date", "target": "revenue"},
                    "statistical_options": {"window": 5, "lag": 8},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Moving average" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "moving_average"
    assert payload["metrics"]["window"] == 5
    assert payload["request"]["group_column"] == "date"
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_auto_analysis_runs_variance_homogeneity_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "score": [10, 11, 9, 10, 12, 9, 10, 11, 1, 30, 5, 40, 15, 50, -10, 60, 8, 9, 10, 11, 10, 9, 10, 12],
            "segment": ["A"] * 8 + ["B"] * 8 + ["C"] * 8,
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["levene_data"],
            method_run_specs=[
                {
                    "run_id": "levene-custom",
                    "method_id": "levene_data",
                    "field_bindings": {"target": "score", "group": "segment"},
                    "statistical_options": {"alpha": 0.01},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "prefer Welch ANOVA" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "levene"
    assert payload["request"]["alpha"] == 0.01
    assert payload["metrics"]["decision"] == "variance_heterogeneous"
    assert payload["metrics"]["groups"] == 3
    assert payload["metrics"]["max_min_variance_ratio"] > 10
    assert payload["tables"][0]["rows"]


def test_auto_analysis_runs_welch_anova_card_with_alpha_option() -> None:
    frame = pd.DataFrame(
        {
            "score": [10, 11, 9, 12, 10, 11, 9, 10, 18, 22, 20, 21, 19, 23, 18, 22, 30, 38, 27, 35, 32, 45, 28, 40],
            "segment": ["A"] * 8 + ["B"] * 8 + ["C"] * 8,
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["welch_anova_data"],
            method_run_specs=[
                {
                    "run_id": "welch-custom",
                    "method_id": "welch_anova_data",
                    "field_bindings": {"target": "score", "group": "segment"},
                    "statistical_options": {"alpha": 0.01},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "welch_anova"
    assert payload["request"]["alpha"] == 0.01
    assert payload["metrics"]["decision"] == "significant"
    assert payload["metrics"]["groups"] == 3
    assert payload["metrics"]["df_den"] > 0
    assert payload["chart"]["kind"] == "bar"


def test_auto_analysis_runs_repeated_measure_card_with_guidance() -> None:
    frame = pd.DataFrame(
        {
            "baseline": [10, 12, 9, 11, 13, 8, 14, 10, 12, 9, 11, 13],
            "month_1": [12, 14, 11, 13, 15, 10, 16, 12, 14, 11, 13, 15],
            "month_2": [15, 17, 14, 16, 18, 13, 19, 15, 17, 14, 16, 18],
        }
    )

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["friedman_data"],
            method_run_specs=[
                {
                    "run_id": "friedman-custom",
                    "method_id": "friedman_data",
                    "field_bindings": {"target": "baseline", "features": ["month_1", "month_2"]},
                    "statistical_options": {"alpha": 0.05},
                }
            ],
            max_methods=1,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    execution = result["data"]["method_card_executions"][0]
    assert execution["runtime_status"] == "local_statistical_execution_completed"
    assert "Friedman" in execution["result_summary"]
    asset = result["data"]["method_execution_assets"][0]
    payload = asset["payload"]
    assert payload["analysis_type"] == "friedman"
    assert payload["metrics"]["decision"] == "significant"
    assert payload["metrics"]["condition_count"] == 3
    assert payload["tables"][0]["rows"]
    assert "Decision cue:" in payload["narrative"]


def test_causal_executor_tolerates_duplicate_column_names() -> None:
    frame = pd.DataFrame(
        [
            ["2026-01-01", 100, 10, 11, "search"],
            ["2026-01-02", 150, 20, 21, "search"],
            ["2026-01-03", 130, 30, 31, "social"],
            ["2026-01-04", 210, 40, 41, "direct"],
            ["2026-01-05", 240, 50, 51, "direct"],
        ],
        columns=["order_date", "revenue", "driver", "driver", "channel"],
    )

    tables = build_causal_executor_tables(
        frame,
        selected={"target": "revenue", "features": ["driver"], "group": "channel"},
        field_profiles=[
            {"column": "order_date", "role": "time", "semantic_tags": ["time"]},
            {"column": "revenue", "role": "measure", "semantic_tags": []},
            {"column": "driver", "role": "measure", "semantic_tags": []},
            {"column": "channel", "role": "dimension", "semantic_tags": []},
        ],
    )

    assert tables
    assert tables[0]["rows"][0]["driver"] == "driver"
    assert "lag1_correlation" in tables[0]["rows"][0]


def test_auto_analysis_generates_derived_fields_and_visual_contracts() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d"],
            "revenue": [100, 240, 120, 360],
            "cost": [60, 100, 90, 120],
            "units": [2, 4, 3, 6],
            "channel": ["search", "search", "social", "direct"],
        }
    )
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(dataset_id="demo", active_sheet="Sheet1"),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    chart_kinds = {chart["kind"] for chart in result["charts"]}
    assert result["metrics"]["method_registry_total"] >= 500
    assert result["metrics"]["routed_method_count"] > 0
    assert result["metrics"]["derived_field_count"] > 0
    assert result["metrics"]["field_relationship_count"] > 0
    assert result["metrics"]["field_semantic_route_field_count"] >= result["metrics"]["field_count"]
    assert result["metrics"]["field_semantic_route_derived_field_count"] == result["metrics"]["derived_field_count"]
    assert result["metrics"]["chart_count"] >= 8
    assert result["metrics"]["evidence_table_count"] == 8
    assert result["metrics"]["method_card_count"] == result["metrics"]["routed_method_count"]
    assert result["metrics"]["method_execution_count"] == result["metrics"]["routed_method_count"]
    assert result["metrics"]["method_execution_asset_count"] == result["metrics"]["routed_method_count"]
    assert result["metrics"]["report_part_asset_count"] > result["metrics"]["report_part_count"]
    assert {"bubble", "quadrant", "scatter", "histogram", "heatmap", "forecast", "cluster-scatter", "anomaly-scatter"}.issubset(chart_kinds)
    table_titles = {table["title"] for table in result["tables"]}
    relationship_table = next(table for table in result["tables"] if table["title"] == "\u5b57\u6bb5\u5173\u7cfb\u56fe\u8c31")
    semantic_route_table = next(table for table in result["tables"] if table["title"] == "\u5b57\u6bb5\u8bed\u4e49\u8def\u7531\u7b56\u7565")
    assert {"field", "source", "business_meaning", "analysis_roles", "compatible_method_families", "recommended_report_parts", "management_use"}.issubset(set(semantic_route_table["columns"]))
    assert any(row["source"] == "derived_field" for row in semantic_route_table["rows"])
    assert any("visual_gallery" in row["recommended_report_parts"] for row in semantic_route_table["rows"])
    assert {"left_field", "right_field", "relationship_type", "strength", "management_interpretation", "recommended_use"}.issubset(set(relationship_table["columns"]))
    assert {"derived_from", "numeric_correlation"} & {row["relationship_type"] for row in relationship_table["rows"]}
    assert result["data"]["field_relationships"]
    assert result["data"]["field_semantic_route_plan"]["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
    assert result["data"]["field_semantic_route_plan"]["rows"]
    assert any(table["title"] == "\u5b57\u6bb5\u7406\u89e3\u4e0e\u89d2\u8272\u8bc6\u522b" for table in result["tables"])
    assert {"\u9884\u6d4b\u98ce\u9669\u6458\u8981", "\u5206\u7fa4\u753b\u50cf", "\u5f02\u5e38 Top-N", "\u9a71\u52a8\u5047\u8bbe", "\u65f6\u95f4\u5e8f\u5217\u8bca\u65ad", "\u56e0\u679c\u5019\u9009\u8def\u5f84", "\u56e0\u679c\u8f7b\u91cf\u6267\u884c\u7ed3\u679c", "\u884c\u52a8\u4f18\u5148\u7ea7\u8bc4\u5206"}.issubset(table_titles)
    time_table = next(table for table in result["tables"] if table["title"] == "\u65f6\u95f4\u5e8f\u5217\u8bca\u65ad")
    assert {"source_ref", "recommended_method", "next_step"}.issubset(set(time_table["columns"]))
    causal_table = next(table for table in result["tables"] if table["title"] == "\u56e0\u679c\u5019\u9009\u8def\u5f84")
    assert {"recommended_design", "readiness_score", "caveat"}.issubset(set(causal_table["columns"]))
    executor_table = next(table for table in result["tables"] if table["title"] == "\u56e0\u679c\u8f7b\u91cf\u6267\u884c\u7ed3\u679c")
    assert {"effect_estimate", "standardized_effect", "stratified_effect_estimate", "bootstrap_ci_low", "bootstrap_ci_high", "ci_excludes_zero", "executor_quality", "lag1_correlation", "priority_score"}.issubset(set(executor_table["columns"]))
    priority_table = next(table for table in result["tables"] if table["title"] == "\u884c\u52a8\u4f18\u5148\u7ea7\u8bc4\u5206")
    assert {"source_ref", "score_reason", "recommended_owner", "next_step"}.issubset(set(priority_table["columns"]))
    assert {"time_series_diagnostic", "causal_candidate_path", "causal_light_executor"}.issubset({row["evidence"] for row in priority_table["rows"]})
    assert "\ufffd" not in result["narrative"]
    assert result["data"]["report_part_contract"]["can_generate"]
    assert result["data"]["method_cards"]
    assert result["data"]["method_card_executions"]
    assert result["data"]["method_execution_assets"]
    manifest = result["data"]["report_part_asset_manifest"]
    assert manifest
    assert any(row["report_part_id"] == "executive_summary" and row["asset_kind"] == "text" for row in manifest)
    assert any(row["report_part_id"] == "visual_gallery" and row["asset_kind"] == "image" for row in manifest)
    assert any(row["source"] == "method_execution_asset" for row in manifest)
    blueprints = result["data"]["report_part_generation_blueprints"]
    assert result["metrics"]["report_part_generation_blueprint_count"] == len(result["report_parts"])
    assert {item["report_part_id"] for item in blueprints} == {part["id"] for part in result["report_parts"]}
    method_note_blueprint = next(item for item in blueprints if item["report_part_id"] == "method_note")
    assert method_note_blueprint["runtime_handoff"]["target"] == "codex_cli_exec_runtime"
    assert method_note_blueprint["runtime_handoff"]["must_use_pre_method_audit"] is True
    assert method_note_blueprint["runtime_handoff"]["must_use_method_route_evidence"] is True
    assert method_note_blueprint["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
    assert method_note_blueprint["method_evidence_count"] > 0
    assert "table:pre_method_routing_audit" in method_note_blueprint["input_contract"]["pre_method_audit_refs"]
    assert "data:method_route_evidence" in method_note_blueprint["input_contract"]["route_evidence_refs"]
    assert any(table["title"] == "\u62a5\u544a\u90e8\u4ef6\u751f\u6210\u84dd\u56fe" for table in result["tables"])
    manifest_table = next(table for table in result["tables"] if table["title"] == "\u62a5\u544a\u90e8\u4ef6\u8d44\u4ea7\u6e05\u5355")
    assert {"report_part_id", "asset_kind", "asset_ref", "source", "management_use"}.issubset(set(manifest_table["columns"]))
    assert result["data"]["method_executor_registry_summary"]["total_executors"] >= 8
    first_card = result["data"]["method_cards"][0]
    assert {"field_bindings", "executor_hint", "report_slots", "evidence_refs", "binding_quality", "semantic_field_routes", "semantic_route_refs", "runtime_field_selection_contract"}.issubset(first_card)
    assert first_card["executor_hint"]
    assert first_card["runtime_field_selection_contract"]["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
    assert "table:field_semantic_route_plan" in first_card["evidence_refs"]
    first_execution = result["data"]["method_card_executions"][0]
    assert {"execution_id", "method_id", "executor_hint", "status", "result_ref", "asset_type", "asset_ref", "semantic_route_refs", "result_summary", "next_step"}.issubset(first_execution)
    first_asset = result["data"]["method_execution_assets"][0]
    assert {"execution_id", "method_id", "asset_type", "asset_ref", "payload"}.issubset(first_asset)
    assert isinstance(first_asset["payload"], dict)
    assert {"runtime_field_selection_contract", "semantic_field_routes", "semantic_route_refs"}.issubset(first_asset["payload"])
    assert first_asset["payload"]["runtime_field_selection_contract"]["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
    assert {"executive_summary", "evidence_index"}.issubset({part["id"] for part in result["report_parts"]})


def test_auto_analysis_records_pre_method_audit_and_route_evidence() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "revenue": [100, 240, 120, 360],
            "cost": [60, 100, 90, 120],
            "units": [2, 4, 3, 6],
            "channel": ["search", "search", "social", "direct"],
        }
    )
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(dataset_id="demo", active_sheet="Sheet1", report_part="method_note", max_methods=16, max_derived_fields=16),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    pre_audit = result["data"]["pre_method_routing_audit"]
    route_evidence = result["data"]["method_route_evidence"]
    assert pre_audit
    assert route_evidence
    assert pre_audit[1]["stage"] == "smart_derived_field_preprocessing"
    assert pre_audit[1]["completed_before_method_routing"] is True
    assert pre_audit[-1]["stage"] == "method_routing"
    assert pre_audit[-1]["completed_before_method_routing"] is False
    assert result["metrics"]["pre_method_audit_stage_count"] == len(pre_audit)
    assert result["metrics"]["method_route_evidence_count"] == len(route_evidence)
    assert result["data"]["report_part_contract"]["route_policy"].startswith("pre-method audit + smart derived preprocessing")
    assert any(row["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing" for row in route_evidence)
    assert any("derived_fields_completed_before_method_routing" in row["pre_method_preprocessing_status"] for row in route_evidence)
    method_note = next(part for part in result["report_parts"] if part["id"] == "method_note")
    table_titles = {table["title"] for table in method_note["tables"]}
    assert "\u65b9\u6cd5\u9009\u62e9\u524d\u7f6e\u5ba1\u8ba1" in table_titles
    assert "\u65b9\u6cd5\u8def\u7531\u8bc1\u636e\u660e\u7ec6" in table_titles
    assert any(row["management_use"].startswith("Audit method routing") for row in route_evidence)
    assert any(row["executor_hint"] for row in route_evidence)


def test_auto_analysis_field_glossary_includes_field_relationship_graph() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d", "e", "f"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"],
            "revenue": [100, 240, 120, 360, 180, 410],
            "cost": [60, 100, 90, 120, 140, 190],
            "units": [2, 4, 3, 6, 2, 7],
            "channel": ["search", "search", "social", "direct", "social", "direct"],
        }
    )
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            report_part="field_glossary",
            max_methods=10,
            max_derived_fields=16,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    assert result["metrics"]["report_part_count"] == 1
    assert result["report_parts"][0]["id"] == "field_glossary"
    table_titles = {table["title"] for table in result["report_parts"][0]["tables"]}
    assert "\u5b57\u6bb5\u7406\u89e3\u4e0e\u89d2\u8272\u8bc6\u522b" in table_titles
    assert "\u5b57\u6bb5\u8bed\u4e49\u8def\u7531\u7b56\u7565" in table_titles
    assert "\u5b57\u6bb5\u5173\u7cfb\u56fe\u8c31" in table_titles
    assert result["report_parts"][0]["data"]["field_semantic_route_plan"]["status"] == "ready"
    assert result["report_parts"][0]["data"]["field_relationships"]
    assert "data:field_semantic_route_plan" in result["report_parts"][0]["evidence_refs"]
    assert "table:field_relationship_graph" in result["report_parts"][0]["evidence_refs"]


def test_auto_analysis_respects_selected_methods_and_derived_fields() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d", "e"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
            "revenue": [100, 240, 120, 360, 180],
            "cost": [60, 100, 90, 120, 140],
            "units": [2, 4, 3, 6, 2],
            "channel": ["search", "search", "social", "direct", "social"],
        }
    )
    probe = run_auto_analysis(
        frame,
        AutoAnalysisRequest(dataset_id="demo", active_sheet="Sheet1", max_derived_fields=12),
        dataset_name="demo",
        sheet_name="Sheet1",
    )
    selected_derived = probe["data"]["derived_field_options"][0]["field"]

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            selected_method_ids=["visual_bubble"],
            selected_derived_fields=[selected_derived],
            execution_mode="separate",
            max_derived_fields=12,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    assert result["metrics"]["selected_method_count"] == 1
    assert result["metrics"]["selected_derived_field_count"] == 1
    assert result["data"]["method_selection"]["matched_method_count"] == 1
    assert {item["id"] for item in result["data"]["routed_methods"]}.issubset({"visual_bubble"})
    assert all(item["selected"] == (item["field"] == selected_derived) for item in result["data"]["derived_field_options"])
    assert result["data"]["method_downloads"]
    assert result["data"]["method_downloads"][0]["file_name"].endswith(".json")
    assert result["data"]["smart_merge_download"]["execution_mode"] == "separate"


def test_auto_analysis_can_generate_a_requested_report_part() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d", "e"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
            "revenue": [100, 240, 120, 360, 180],
            "cost": [60, 100, 90, 120, 140],
            "units": [2, 4, 3, 6, 2],
            "channel": ["search", "search", "social", "direct", "social"],
        }
    )
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            report_part="action_plan",
            max_methods=12,
            max_derived_fields=16,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    chart_kinds = {chart["kind"] for chart in result["charts"]}
    assert {"line", "forecast", "cluster-scatter", "anomaly-scatter"}.issubset(chart_kinds)
    assert result["metrics"]["report_part_count"] == 1
    assert result["data"]["report_part_contract"]["generated_part_ids"] == ["action_plan"]
    assert result["report_parts"][0]["id"] == "action_plan"
    assert result["report_parts"][0]["tables"][0]["title"] == "\u8c61\u9650\u884c\u52a8\u5efa\u8bae"
    assert {"\u9884\u6d4b\u98ce\u9669\u6458\u8981", "\u5206\u7fa4\u753b\u50cf", "\u5f02\u5e38 Top-N", "\u9a71\u52a8\u5047\u8bbe", "\u65f6\u95f4\u5e8f\u5217\u8bca\u65ad", "\u56e0\u679c\u5019\u9009\u8def\u5f84", "\u56e0\u679c\u8f7b\u91cf\u6267\u884c\u7ed3\u679c", "\u884c\u52a8\u4f18\u5148\u7ea7\u8bc4\u5206"}.issubset({table["title"] for table in result["report_parts"][0]["tables"]})
    assert result["report_parts"][0]["data"]["action_priority_scores"]
    assert "next=" in result["report_parts"][0]["bullets"][0]
    assert result["data"]["routed_methods"]
    assert all(item.get("method_card") for item in result["data"]["routed_methods"])
    route_reasons = {reason for item in result["data"]["routed_methods"] for reason in item.get("route_reasons", [])}
    assert "semantic_field_binding" in route_reasons
    assert "semantic_method_family_match" in route_reasons
    assert "semantic_report_part_match" in route_reasons
    assert "field_relationship_evidence" in route_reasons
    assert len(result["data"]["method_card_executions"]) == len(result["data"]["routed_methods"])
    assert len(result["data"]["method_execution_assets"]) == len(result["data"]["routed_methods"])
    assert len(result["data"]["method_execution_packages"]) == len(result["data"]["routed_methods"])
    assert all(asset.get("runtime_handoff") for asset in result["data"]["method_execution_assets"])
    assert all(
        asset["runtime_handoff"]["task"].startswith("execute_method_asset:")
        for asset in result["data"]["method_execution_assets"]
    )
    assert all(
        asset["runtime_handoff"]["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
        for asset in result["data"]["method_execution_assets"]
    )
    assert all(package["runtime_handoff_count"] >= 1 for package in result["data"]["method_execution_packages"])
    assert all(
        package["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
        for package in result["data"]["method_execution_packages"]
    )
    method_downloads = result["data"]["method_downloads"]
    assert all(download.get("package_ref", "").startswith("data:method_execution_packages:") for download in method_downloads)
    assert all(download.get("runtime_handoff_count", 0) >= 1 for download in method_downloads)
    method_downloadables = [item for item in result["downloadables"] if item.get("download_kind") == "single_method_json"]
    assert method_downloadables
    assert all(item.get("package_ref", "").startswith("data:method_execution_packages:") for item in method_downloadables)
    assert result["metrics"]["report_part_asset_count"] == len(result["data"]["report_part_asset_manifest"])
    assert result["metrics"]["report_part_generation_blueprint_count"] == 1
    assert {item["report_part_id"] for item in result["data"]["report_part_generation_blueprints"]} == {"action_plan"}
    action_blueprint = result["report_parts"][0]["data"]["generation_blueprint"]
    assert action_blueprint["report_part_id"] == "action_plan"
    assert action_blueprint["runtime_handoff"]["task"] == "generate_report_part:action_plan"
    assert action_blueprint["runtime_handoff"]["must_preserve_evidence_refs"] is True
    assert {"text", "table", "structured_data"}.issubset(set(action_blueprint["required_asset_kinds"]))
    assert action_blueprint["readiness"] in {"ready", "partial"}
    assert "data:report_part_generation_blueprints" in result["report_parts"][0]["evidence_refs"]
    assert {row["report_part_id"] for row in result["data"]["report_part_asset_manifest"]} == {"action_plan"}
    assert any("runtime_handoff" in row.get("payload_keys", "") for row in result["data"]["report_part_asset_manifest"])
    assert {"text", "table", "image", "structured_data"}.issubset({row["asset_kind"] for row in result["report_parts"][0]["data"]["asset_manifest"]})
    assert "table:report_part_asset_manifest" in result["report_parts"][0]["evidence_refs"]
    assert len(result["data"]["evidence_tables"]) == 8
    executor_table = next(table for table in result["data"]["evidence_tables"] if table["title"] == "\u56e0\u679c\u8f7b\u91cf\u6267\u884c\u7ed3\u679c")
    assert executor_table["rows"][0]["bootstrap_iterations"] > 0
    scores = [item["route_score"] for item in result["data"]["routed_methods"]]
    assert scores == sorted(scores, reverse=True)


def test_auto_analysis_can_generate_requested_report_part_bundle() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d", "e", "f"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"],
            "revenue": [100, 240, 120, 360, 180, 410],
            "cost": [60, 100, 90, 120, 140, 190],
            "units": [2, 4, 3, 6, 2, 7],
            "channel": ["search", "search", "social", "direct", "social", "direct"],
        }
    )
    requested_parts = ["executive_summary", "appendix", "evidence_index"]

    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            report_part="auto",
            selected_report_parts=requested_parts,
            max_methods=18,
            max_derived_fields=16,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
    )

    assert result["metrics"]["report_part_count"] == len(requested_parts)
    assert result["metrics"]["requested_report_part_count"] == len(requested_parts)
    assert result["data"]["report_part_contract"]["requested_report_parts"] == requested_parts
    assert result["data"]["report_part_contract"]["generated_part_ids"] == requested_parts
    assert [part["id"] for part in result["report_parts"]] == requested_parts
    assert any(item["name"].endswith("report_part_bundle.json") for item in result["downloadables"])
    assert result["data"]["report_part_bundle"]["generated_part_ids"] == requested_parts
    assert {item["report_part_id"] for item in result["data"]["report_part_generation_blueprints"]} == set(requested_parts)
    assert result["metrics"]["report_part_generation_blueprint_count"] == len(requested_parts)
    assert all(
        blueprint["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
        for blueprint in result["data"]["report_part_generation_blueprints"]
    )
    assert "table:pre_method_routing_audit" in result["data"]["report_part_generation_blueprints"][0]["input_contract"]["pre_method_audit_refs"]
    assert all(row["report_part_id"] in requested_parts for row in result["data"]["report_part_asset_manifest"])
    assert {row["report_part_id"] for row in result["data"]["report_part_asset_manifest"]} == set(requested_parts)
    assert any(set(item.get("route_context", {}).get("requested_parts", [])) == set(requested_parts) for item in result["data"]["routed_methods"])
    assert result["data"]["smart_merge_download"]["requested_report_parts"] == requested_parts


def test_auto_analysis_can_export_runtime_packages(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d", "e"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
            "revenue": [100, 240, 120, 360, 180],
            "cost": [60, 100, 90, 120, 140],
            "units": [2, 4, 3, 6, 2],
            "channel": ["search", "search", "social", "direct", "social"],
        }
    )
    _write_lab_report_agent_review_fixture(tmp_path)
    result = run_auto_analysis(
        frame,
        AutoAnalysisRequest(
            dataset_id="demo",
            active_sheet="Sheet1",
            report_part="action_plan",
            max_methods=6,
            max_derived_fields=12,
        ),
        dataset_name="demo",
        sheet_name="Sheet1",
        export_dir=tmp_path,
        public_base_path="/storage/auto-analysis/demo/run-1",
    )

    assert (tmp_path / "report_part_bundle.json").is_file()
    assert (tmp_path / "method_execution_packages.json").is_file()
    assert (tmp_path / "runtime_package_manifest.json").is_file()
    assert (tmp_path / "method_artifact_index.json").is_file()
    assert (tmp_path / "method_artifact_index.csv").is_file()
    assert (tmp_path / "method_artifact_index.xlsx").is_file()
    assert (tmp_path / "method_artifact_integrity.json").is_file()
    assert (tmp_path / "chart_asset_index.json").is_file()
    assert (tmp_path / "chart_asset_index.csv").is_file()
    assert (tmp_path / "codex_method_interpretation_input.json").is_file()
    assert (tmp_path / "codex_method_interpretations.json").is_file()
    assert (tmp_path / "codex_method_interpretations.md").is_file()
    assert (tmp_path / "lab_report_agent_review_input.json").is_file()
    assert (tmp_path / "lab_report_agent_review_prompt.md").is_file()
    assert (tmp_path / "lab_report_agent_reviews.json").is_file()
    assert (tmp_path / "lab_report_agent_reviews.md").is_file()
    assert (tmp_path / "report_writer_agent_input.json").is_file()
    assert (tmp_path / "report_writer_agent_result.json").is_file()
    assert (tmp_path / "lab_report.md").is_file()
    assert (tmp_path / "lab_report.html").is_file()
    assert (tmp_path / "lab_report.json").is_file()
    assert (tmp_path / "lab_report_revision_seed.json").is_file()
    assert (tmp_path / "delivery_manifest.json").is_file()
    exported_packages = json.loads((tmp_path / "method_execution_packages.json").read_text(encoding="utf-8"))
    report_part_bundle = json.loads((tmp_path / "report_part_bundle.json").read_text(encoding="utf-8"))
    runtime_manifest = json.loads((tmp_path / "runtime_package_manifest.json").read_text(encoding="utf-8"))
    method_artifact_index = json.loads((tmp_path / "method_artifact_index.json").read_text(encoding="utf-8"))
    method_artifact_integrity = json.loads((tmp_path / "method_artifact_integrity.json").read_text(encoding="utf-8"))
    chart_asset_index = json.loads((tmp_path / "chart_asset_index.json").read_text(encoding="utf-8"))
    report_writer_input = json.loads((tmp_path / "report_writer_agent_input.json").read_text(encoding="utf-8"))
    report_writer_agent = json.loads((tmp_path / "report_writer_agent_result.json").read_text(encoding="utf-8"))
    method_interpretation_input = json.loads((tmp_path / "codex_method_interpretation_input.json").read_text(encoding="utf-8"))
    method_interpretations = json.loads((tmp_path / "codex_method_interpretations.json").read_text(encoding="utf-8"))
    agent_reviews = json.loads((tmp_path / "lab_report_agent_reviews.json").read_text(encoding="utf-8"))
    lab_report_markdown = (tmp_path / "lab_report.md").read_text(encoding="utf-8")
    lab_report_html = (tmp_path / "lab_report.html").read_text(encoding="utf-8")
    lab_report_json = json.loads((tmp_path / "lab_report.json").read_text(encoding="utf-8"))
    revision_seed = json.loads((tmp_path / "lab_report_revision_seed.json").read_text(encoding="utf-8"))
    delivery_manifest = json.loads((tmp_path / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert len(exported_packages) == len(result["data"]["method_execution_packages"])
    assert method_artifact_index["method_count"] == len(exported_packages)
    assert method_artifact_index["rows"][0]["data_csv_path"].endswith("/data.csv")
    assert method_artifact_index["rows"][0]["integrity_status"] == "complete"
    assert method_artifact_integrity["method_count"] == len(exported_packages)
    assert method_artifact_integrity["integrity_status"] == "passed"
    assert method_artifact_integrity["complete_count"] == len(exported_packages)
    assert method_artifact_integrity["incomplete_count"] == 0
    assert method_artifact_integrity["rows"][0]["integrity_status"] == "complete"
    assert {item["name"] for item in method_artifact_integrity["rows"][0]["files"]} == {"data.json", "data.csv", "data.xlsx", "preview.png", "README.md"}
    assert all(item["exists"] and item["size_bytes"] > 0 and item["status"] == "ok" for item in method_artifact_integrity["rows"][0]["files"])
    assert "file_path" not in json.dumps(method_artifact_integrity, ensure_ascii=False)
    assert not re.search(r"(?i)(?:/tmp/|[a-z]:[/\\])", json.dumps(method_artifact_integrity, ensure_ascii=False))
    assert method_interpretation_input["method_count"] == len(exported_packages)
    assert method_interpretation_input["tasks"][0]["artifact_paths"]["png"].endswith("/preview.png")
    assert method_interpretations["method_count"] == len(exported_packages)
    assert method_interpretations["interpretations"][0]["status"] == "local_numeric_cli_analysis_completed"
    assert method_interpretations["interpretations"][0]["numeric_profile"]["row_count"] >= 1
    assert "waiting_for_codex_cli" not in json.dumps(method_interpretations, ensure_ascii=False)
    assert runtime_manifest["method_package_count"] == len(exported_packages)
    assert runtime_manifest["runtime_handoff_count"] >= len(exported_packages)
    assert runtime_manifest["report_part_dispatch_count"] == len(report_part_bundle["generation_blueprints"])
    assert runtime_manifest["runtime_dispatch_count"] == len(exported_packages) + runtime_manifest["report_part_dispatch_count"]
    assert runtime_manifest["dispatch_plan_count"] == runtime_manifest["runtime_dispatch_count"]
    assert runtime_manifest["method_artifact_summary"]["method_count"] == len(exported_packages)
    assert runtime_manifest["chart_asset_summary"]["chart_count"] >= 1
    assert runtime_manifest["chart_asset_summary"]["integrity_status"] == "passed"
    assert runtime_manifest["method_artifact_summary"]["index_json_path"].endswith("method_artifact_index.json")
    assert runtime_manifest["method_artifact_summary"]["integrity_path"].endswith("method_artifact_integrity.json")
    assert runtime_manifest["method_artifact_summary"]["integrity_status"] == "passed"
    assert runtime_manifest["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
    assert len(runtime_manifest["method_dispatch_plan"]) == len(exported_packages)
    assert len(runtime_manifest["report_part_dispatch_plan"]) == runtime_manifest["report_part_dispatch_count"]
    assert len(runtime_manifest["dispatch_plan"]) == runtime_manifest["runtime_dispatch_count"]
    assert runtime_manifest["dispatch_plan"][0]["package_ref"].startswith("data:method_execution_packages:")
    assert runtime_manifest["dispatch_plan"][0]["runtime_tasks"]
    assert any(item["task"].startswith("generate_report_part:") for item in runtime_manifest["report_part_dispatch_plan"])
    assert all(item["blueprint_ref"].startswith("data:report_part_generation_blueprints:") for item in runtime_manifest["report_part_dispatch_plan"])
    first_package = exported_packages[0]
    first_package_path = tmp_path / first_package["file_name"]
    assert first_package_path.is_file()
    first_package_payload = json.loads(first_package_path.read_text(encoding="utf-8"))
    assert first_package_payload["runtime_handoff_count"] >= 1
    assert first_package_payload["runtime_handoffs"][0]["task"].startswith("execute_method_asset:")
    first_artifact = first_package_payload["artifact_exports"]
    assert (tmp_path / first_artifact["folder"] / "data.json").is_file()
    assert (tmp_path / first_artifact["folder"] / "data.csv").is_file()
    assert (tmp_path / first_artifact["folder"] / "data.xlsx").is_file()
    assert (tmp_path / first_artifact["folder"] / "preview.png").is_file()
    assert first_artifact["integrity_status"] == "complete"
    assert all(item["status"] == "ok" for item in first_artifact["file_statuses"])
    assert first_package_payload["codex_interpretation"]["preview_png_path"].endswith("/preview.png")
    real_result_package = next(item for item in exported_packages if item["execution"].get("result_rows"))
    real_result_artifact = real_result_package["artifact_exports"]
    real_result_csv = tmp_path / real_result_artifact["folder"] / "data.csv"
    real_result_header = real_result_csv.read_text(encoding="utf-8-sig").splitlines()[0]
    assert "package_id" not in real_result_header
    assert "route_score" not in real_result_header
    assert any(token in real_result_header for token in ["字段", "变量", "目标指标", "图表引用", "报告槽位"])
    first_summary = report_part_bundle["method_execution_package_summaries"][0]
    assert first_summary["package_ref"] == f"data:method_execution_packages:{first_package['package_id']}"
    assert first_summary["asset_count"] >= 1
    assert first_summary["asset_refs"]
    assert first_summary["runtime_tasks"]
    assert "追溯标识：方法证据" in lab_report_markdown
    assert "证据索引：已生成 JSON、CSV、XLSX 三种格式" in lab_report_markdown
    assert "证据完整性：" in lab_report_markdown
    assert 8 <= sum(1 for line in lab_report_markdown.splitlines() if line.startswith("## ")) <= 12
    assert "## 研究摘要" in lab_report_markdown
    assert "## 研究问题与结论" in lab_report_markdown
    assert "## 研究设计与方法" in lab_report_markdown
    assert "## 图文叙事" in lab_report_markdown
    assert "## 商用交付检查" in lab_report_markdown
    assert "## 复核结论" in lab_report_markdown
    assert "## 审稿结论" not in lab_report_markdown
    assert "### 关键数字总览" in lab_report_markdown
    assert "### 核心业务判断" in lab_report_markdown
    assert "## 行动优先级矩阵" in lab_report_markdown
    assert "## 业务证据链" in lab_report_markdown
    assert "## 图表与数值证据" in lab_report_markdown
    assert "### 可视化图表证据" in lab_report_markdown
    assert "### 表格与数值证据" in lab_report_markdown
    assert "### 业务信号判断" in lab_report_markdown
    assert "## 证据附录" in lab_report_markdown
    assert "### 方法证据索引" in lab_report_markdown
    assert "业务图表数量" in lab_report_markdown
    assert "判断：" in lab_report_markdown
    assert "图中展示" in lab_report_markdown
    assert "关键证据：" in lab_report_markdown
    assert "业务行动" in lab_report_markdown
    assert "复核边界：" in lab_report_markdown
    assert "证据引用" in lab_report_markdown
    assert "商用交付口径" in lab_report_markdown
    assert "商业用途" in lab_report_markdown
    assert "审稿结论" not in lab_report_markdown
    assert "审稿记录" not in lab_report_markdown
    assert "Figure " in lab_report_markdown
    assert re.search(r"(?m)^!\[[^\]]+\]\(chart_assets/[^)]+\.png\)", lab_report_markdown)
    assert "可嵌入图像数量" in lab_report_markdown
    assert "正式对外发布前仍需责任人复核字段口径和业务事实" not in lab_report_markdown
    assert "CHART: title=" not in lab_report_markdown
    assert "evidence_detail=" not in lab_report_markdown
    assert "读图问题：" in lab_report_markdown
    assert "业务影响：" in lab_report_markdown
    assert "证据数字：" in lab_report_markdown
    assert "route_score" not in lab_report_markdown
    assert "asset_index" not in lab_report_markdown
    assert "Visible numeric evidence" not in lab_report_markdown
    assert "completed with" not in lab_report_markdown
    assert "method_package" not in lab_report_markdown
    assert "chart_asset " not in lab_report_markdown
    assert "method_artifact " not in lab_report_markdown
    assert "runtime_status" not in lab_report_markdown
    assert "Agent 审稿" not in lab_report_markdown
    assert "claim_review" not in lab_report_markdown
    assert "business_action_review" not in lab_report_markdown
    assert "chart_relevance_review" not in lab_report_markdown
    assert not re.search(r"(?i)(?:/tmp/[^\s|)>\]\"']+|[a-z]:[/\\][^\s|)>\]\"']+)", lab_report_markdown)
    assert "[JSON 证据](method_artifacts/" in lab_report_markdown
    assert "[CSV 数据](method_artifacts/" in lab_report_markdown
    assert "[Excel 表格](method_artifacts/" in lab_report_markdown
    assert "![管理摘要](method_artifacts/" in lab_report_markdown
    assert "VISUAL: title=" not in lab_report_markdown
    assert "方法运行" in lab_report_markdown
    assert "业务指标" in lab_report_markdown
    assert "完整性：完整" in lab_report_markdown
    assert "data-design-skill=\"frontend-design\"" in lab_report_html
    assert "class=\"report-shell\"" in lab_report_html
    assert "class=\"report-toc\"" in lab_report_html
    assert "business-chart" in lab_report_html
    assert "markdown-embedded-image" in lab_report_html
    assert "<img src=\"chart_assets/" in lab_report_html
    assert "visual-question" in lab_report_html
    assert "visual-impact" in lab_report_html
    assert "visual-boundary" in lab_report_html
    assert "visual-evidence" in lab_report_html
    assert "读图问题：" in lab_report_html
    assert "关键发现：" in lab_report_html
    assert "业务影响：" in lab_report_html
    assert "证据包：" in lab_report_html
    assert "PNG 已加载" in lab_report_html
    assert "图片未加载：" in lab_report_html
    assert "<table>" in lab_report_html
    assert "preview.png" in lab_report_html
    assert "data.csv" in lab_report_html
    assert "data.xlsx" in lab_report_html
    assert "data.json" in lab_report_html
    assert agent_reviews["runtime_status"] in {"completed", "agent_review_completed"}
    assert len(agent_reviews["agent_reviews"]) == 3
    assert len(agent_reviews["consolidated_actions"]) == 5
    assert report_writer_agent["runtime_status"] == "passed"
    assert report_writer_input["contract"] == "analysis_lab_report_writer_agent_input_v1"
    assert report_writer_agent["contract"] == "analysis_lab_report_writer_agent_v2"
    assert report_writer_input["contract"] != report_writer_agent["contract"]
    assert report_writer_agent["input_ref"] == "report_writer_agent_input.json"
    assert len(report_writer_agent["chart_agents"]) >= 1
    assert report_writer_agent["chart_agents"][0]["direct_answer"]
    assert report_writer_agent["chart_agents"][0]["caption"]
    assert report_writer_agent["chart_agents"][0]["sampling_note"]
    assert report_writer_agent["chart_agents"][0]["evidence_analyst_agent"]["sample_scope"]
    assert report_writer_agent["chart_agents"][0]["skeptical_review_agent"]["passed"] is True
    lab_report_meta = result["data"]["lab_report"]
    failed_quality_checks = [check for check in lab_report_meta["quality_checks"] if check["status"] != "passed"]
    assert lab_report_meta["quality_status"] == "passed", failed_quality_checks
    assert lab_report_meta["failed_check_count"] == 0
    assert lab_report_meta["json_file_name"] == "lab_report.json"
    assert lab_report_meta["json_path"] == "/storage/auto-analysis/demo/run-1/lab_report.json"
    assert lab_report_json["report_id"] == lab_report_meta["report_id"]
    assert lab_report_json["quality_status"] == "passed"
    assert lab_report_json["lab_report_json_downloadable"]["path"] == "/storage/auto-analysis/demo/run-1/lab_report.json"
    assert {check["id"]: check["status"] for check in lab_report_meta["quality_checks"]}["commercial_quality_gate"] == "passed"
    assert {check["id"]: check["status"] for check in lab_report_meta["quality_checks"]}["structured_chart_captions"] == "passed"
    assert {check["id"]: check["status"] for check in lab_report_meta["quality_checks"]}["reader_facing_internal_leakage"] == "passed"
    assert {check["id"]: check["status"] for check in lab_report_meta["quality_checks"]}["markdown_image_delivery"] == "passed"
    assert {check["id"]: check["status"] for check in lab_report_meta["quality_checks"]}["reader_visible_local_path_absence"] == "passed"
    assert "追溯标识：-" not in lab_report_markdown
    assert chart_asset_index["chart_count"] >= 1
    assert chart_asset_index["complete_count"] == chart_asset_index["chart_count"]
    assert len({row["chart_ref"] for row in chart_asset_index["rows"]}) == chart_asset_index["chart_count"]
    assert "file_path" not in json.dumps(chart_asset_index, ensure_ascii=False)
    assert not re.search(r"(?i)(?:/tmp/|[a-z]:[/\\])", json.dumps(chart_asset_index, ensure_ascii=False))
    assert chart_asset_index["rows"][0]["direct_answer"]
    assert chart_asset_index["rows"][0]["recommended_action"]
    assert chart_asset_index["rows"][0]["sample_scope"]
    assert chart_asset_index["rows"][0]["evidence_numbers"]
    first_chart_row = chart_asset_index["rows"][0]
    assert (tmp_path / first_chart_row["folder"] / "chart.png").is_file()
    assert first_chart_row["direct_answer"]
    assert first_chart_row["caption"]
    assert first_chart_row["sampling_note"]
    visual_packages = [item for item in exported_packages if item.get("family") == "visual"]
    if visual_packages:
        assert all((item.get("artifact_exports") or {}).get("preview_kind") == "business_chart" for item in visual_packages)
        visual_csv_text = (tmp_path / visual_packages[0]["artifact_exports"]["folder"] / "data.csv").read_text(encoding="utf-8-sig")
        assert "关键证据" in visual_csv_text or "图中展示" in visual_csv_text
        assert "每个点代表一条记录" not in visual_csv_text
    assert revision_seed["method_package_summaries"][0]["package_ref"] == first_summary["package_ref"]
    assert revision_seed["method_package_refs"][0] == first_summary["package_ref"]
    assert revision_seed["method_artifact_summary"]["method_count"] == len(exported_packages)
    assert revision_seed["method_artifact_summary"]["integrity_status"] == "passed"
    exported_downloads = {item["name"]: item for item in result["downloadables"]}
    assert exported_downloads["delivery_manifest.json"]["path"] == "/storage/auto-analysis/demo/run-1/delivery_manifest.json"
    assert exported_downloads["delivery_manifest.json"]["category"] == "客户交付清单"
    assert exported_downloads["delivery_manifest.json"]["type_label"] == "JSON 证据"
    assert exported_downloads["lab_report.json"]["path"] == "/storage/auto-analysis/demo/run-1/lab_report.json"
    assert exported_downloads["lab_report.json"]["category"] == "主报告 JSON"
    assert exported_downloads["lab_report.json"]["type_label"] == "JSON 证据"
    assert exported_downloads["runtime_package_manifest.json"]["path"] == "/storage/auto-analysis/demo/run-1/runtime_package_manifest.json"
    assert exported_downloads["method_artifact_index.json"]["path"] == "/storage/auto-analysis/demo/run-1/method_artifact_index.json"
    assert exported_downloads["method_artifact_integrity.json"]["path"] == "/storage/auto-analysis/demo/run-1/method_artifact_integrity.json"
    assert exported_downloads["codex_method_interpretations.json"]["path"] == "/storage/auto-analysis/demo/run-1/codex_method_interpretations.json"
    assert exported_downloads["report_writer_agent_result.json"]["path"] == "/storage/auto-analysis/demo/run-1/report_writer_agent_result.json"
    assert exported_downloads["runtime_package_manifest.json"]["method_package_count"] == runtime_manifest["method_package_count"]
    assert exported_downloads["runtime_package_manifest.json"]["runtime_handoff_count"] == runtime_manifest["runtime_handoff_count"]
    assert exported_downloads["runtime_package_manifest.json"]["dispatch_plan_count"] == runtime_manifest["dispatch_plan_count"]
    assert exported_downloads["runtime_package_manifest.json"]["report_part_dispatch_count"] == runtime_manifest["report_part_dispatch_count"]
    assert exported_downloads["runtime_package_manifest.json"]["runtime_dispatch_count"] == runtime_manifest["runtime_dispatch_count"]
    assert exported_downloads["runtime_package_manifest.json"]["pre_method_preprocessing_status"] == "derived_fields_completed_before_method_routing"
    assert exported_downloads["method_execution_packages.json"]["method_package_count"] == runtime_manifest["method_package_count"]
    assert exported_downloads["report_part_bundle.json"]["path"] == "/storage/auto-analysis/demo/run-1/report_part_bundle.json"
    assert exported_downloads[first_package["file_name"]]["path"].startswith("/storage/auto-analysis/demo/run-1/")
    assert all("file_path" not in item for item in result["downloadables"])
    assert not re.search(r"(?i)(?:/tmp/|[a-z]:[/\\])", json.dumps(result["downloadables"], ensure_ascii=False))
    assert all(item.get("category") for item in result["downloadables"])
    assert all(item.get("type_label") for item in result["downloadables"])
    assert all(not re.search(r"\b(?:in-memory|runtime export|contract|agent output)\b", str(item.get("purpose") or ""), re.I) for item in result["downloadables"])
    assert delivery_manifest["contract"] == "analysis_lab_customer_delivery_manifest_v1"
    assert delivery_manifest["quality"]["status"] == "passed"
    assert delivery_manifest["coverage"]["chart_count"] >= 1
    assert delivery_manifest["coverage"]["method_count"] == len(exported_packages)
    assert delivery_manifest["coverage"]["downloadable_count"] == len(result["downloadables"])
    assert {"主报告 HTML", "业务图表文件", "方法证据文件", "客户交付清单"}.issubset({row["类别"] for row in delivery_manifest["category_summary"]})
    delivery_manifest_text = json.dumps(delivery_manifest, ensure_ascii=False)
    assert "file_path" not in delivery_manifest_text
    assert not re.search(r"(?i)(?:/tmp/|[a-z]:[/\\])", delivery_manifest_text)
    assert any(item["name"] == "lab_report.html" and item["category"] == "主报告 HTML" for item in delivery_manifest["downloadables"])
    assert any(item["name"] == "lab_report.json" and item["category"] == "主报告 JSON" for item in delivery_manifest["downloadables"])
    assert any(item["name"] == "lab_report.json" for item in delivery_manifest["main_files"])
    assert any(item["path"].endswith(".png") and item["type_label"] == "PNG 图像" for item in delivery_manifest["downloadables"])
    assert any(item["path"].endswith(".csv") and item["type_label"] == "CSV 数据" for item in delivery_manifest["downloadables"])
    assert any(item["path"].endswith(".xlsx") and item["type_label"] == "Excel 表格" for item in delivery_manifest["downloadables"])
