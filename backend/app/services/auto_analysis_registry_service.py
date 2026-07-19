from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import Any

from app.services.statistical_catalog import get_statistical_catalog


DEFAULT_SPEC_PATH = Path(__file__).with_name("auto_analysis_specs.json")
DEFAULT_LEARNED_METHOD_PATH = Path(__file__).resolve().parents[3] / "workspace" / "storage" / "auto_analysis_learned_methods.json"


def _zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


FAMILY_LABELS = {
    "descriptive": _zh(r"\u63cf\u8ff0\u7edf\u8ba1"),
    "association": _zh(r"\u5173\u8054\u5206\u6790"),
    "categorical_association": _zh(r"\u5206\u7c7b\u5173\u8054"),
    "comparison": _zh(r"\u5dee\u5f02\u6bd4\u8f83"),
    "distribution_assumption": _zh(r"\u5206\u5e03\u5047\u8bbe"),
    "mean_tests": _zh(r"\u5747\u503c\u68c0\u9a8c"),
    "nonparametric": _zh(r"\u975e\u53c2\u6570\u68c0\u9a8c"),
    "regression": _zh(r"\u56de\u5f52\u5efa\u6a21"),
    "regression_glm": _zh(r"\u5e7f\u4e49\u7ebf\u6027\u6a21\u578b"),
    "machine_learning": _zh(r"\u673a\u5668\u5b66\u4e60"),
    "multivariate": _zh(r"\u591a\u53d8\u91cf\u5206\u6790"),
    "time_series": _zh(r"\u65f6\u95f4\u5e8f\u5217"),
    "causal": _zh(r"\u56e0\u679c\u63a2\u67e5"),
    "causal_panel": _zh(r"\u9762\u677f\u56e0\u679c"),
    "survival": _zh(r"\u751f\u5b58\u5206\u6790"),
    "experimentation": _zh(r"\u5b9e\u9a8c\u5206\u6790"),
    "psychometrics": _zh(r"\u5fc3\u7406\u6d4b\u91cf"),
    "visual": _zh(r"\u53ef\u89c6\u5316"),
    "report_part": _zh(r"\u62a5\u544a\u90e8\u4ef6"),
    "learned": _zh(r"\u5df2\u5b66\u4e60\u65b9\u6cd5"),
    "statistical": _zh(r"\u7edf\u8ba1\u65b9\u6cd5"),
}

METHOD_LABELS = {
    "profile": _zh(r"\u753b\u50cf"),
    "rank": _zh(r"\u6392\u540d"),
    "distribution": _zh(r"\u5206\u5e03"),
    "segment": _zh(r"\u5206\u5c42"),
    "coverage": _zh(r"\u8986\u76d6\u60c5\u51b5"),
    "missingness": _zh(r"\u7f3a\u5931\u60c5\u51b5"),
    "correlation": _zh(r"\u76f8\u5173\u6027"),
    "mutual_information": _zh(r"\u4e92\u4fe1\u606f"),
    "distance": _zh(r"\u8ddd\u79bb"),
    "partial": _zh(r"\u504f\u76f8\u5173"),
    "network": _zh(r"\u5173\u7cfb\u7f51\u7edc"),
    "mean": _zh(r"\u5747\u503c"),
    "median": _zh(r"\u4e2d\u4f4d\u6570"),
    "variance": _zh(r"\u65b9\u5dee"),
    "proportion": _zh(r"\u5360\u6bd4"),
    "post_hoc": _zh(r"\u4e8b\u540e\u68c0\u9a8c"),
    "linear": _zh(r"\u7ebf\u6027"),
    "logistic": _zh(r"\u903b\u8f91"),
    "poisson": _zh(r"\u6cca\u677e"),
    "robust": _zh(r"\u7a33\u5065"),
    "regularized": _zh(r"\u6b63\u5219\u5316"),
    "quantile": _zh(r"\u5206\u4f4d\u6570"),
    "tree": _zh(r"\u51b3\u7b56\u6811"),
    "forest": _zh(r"\u968f\u673a\u68ee\u6797"),
    "boosting": _zh(r"\u63d0\u5347\u6a21\u578b"),
    "neighbors": _zh(r"\u8fd1\u90bb"),
    "neural": _zh(r"\u795e\u7ecf\u7f51\u7edc"),
    "importance": _zh(r"\u91cd\u8981\u6027"),
    "trend": _zh(r"\u8d8b\u52bf"),
    "seasonality": _zh(r"\u5b63\u8282\u6027"),
    "lag": _zh(r"\u6ede\u540e"),
    "forecast": _zh(r"\u9884\u6d4b"),
    "change_point": _zh(r"\u62d0\u70b9"),
    "calendar": _zh(r"\u65e5\u5386"),
    "did": _zh(r"\u53cc\u91cd\u5dee\u5206"),
    "matching": _zh(r"\u5339\u914d"),
    "uplift": _zh(r"\u589e\u91cf"),
    "synthetic_control": _zh(r"\u5408\u6210\u63a7\u5236"),
    "sensitivity": _zh(r"\u654f\u611f\u6027"),
    "bubble": _zh(r"\u6c14\u6ce1\u56fe"),
    "bar": _zh(r"\u6761\u5f62\u56fe"),
    "column": _zh(r"\u67f1\u72b6\u56fe"),
    "line": _zh(r"\u6298\u7ebf\u56fe"),
    "area": _zh(r"\u9762\u79ef\u56fe"),
    "stacked_area": _zh(r"\u5806\u79ef\u9762\u79ef\u56fe"),
    "sparkline": _zh(r"\u8ff7\u4f60\u8d8b\u52bf\u7ebf"),
    "histogram": _zh(r"\u76f4\u65b9\u56fe"),
    "density": _zh(r"\u5bc6\u5ea6\u56fe"),
    "boxplot": _zh(r"\u7bb1\u7ebf\u56fe"),
    "violin": _zh(r"\u5c0f\u63d0\u7434\u56fe"),
    "strip": _zh(r"\u6761\u5e26\u6563\u70b9\u56fe"),
    "beeswarm": _zh(r"\u8702\u7fa4\u56fe"),
    "ecdf": _zh(r"\u7ecf\u9a8c\u5206\u5e03\u56fe"),
    "qqplot": _zh(r"\u6b63\u6001 Q-Q \u56fe"),
    "quadrant": _zh(r"\u8c61\u9650\u56fe"),
    "scatter": _zh(r"\u6563\u70b9\u56fe"),
    "hexbin": _zh(r"\u516d\u8fb9\u5f62\u5bc6\u5ea6\u56fe"),
    "contour": _zh(r"\u7b49\u9ad8\u7ebf\u56fe"),
    "pairplot": _zh(r"\u6210\u5bf9\u6563\u70b9\u77e9\u9635"),
    "parallel_coordinates": _zh(r"\u5e73\u884c\u5750\u6807\u56fe"),
    "heatmap": _zh(r"\u70ed\u529b\u77e9\u9635"),
    "calendar_heatmap": _zh(r"\u65e5\u5386\u70ed\u529b\u56fe"),
    "cohort_matrix": _zh(r"\u961f\u5217\u77e9\u9635"),
    "small_multiple": _zh(r"\u5c0f\u591a\u56fe"),
    "slopegraph": _zh(r"\u5761\u5ea6\u56fe"),
    "bump_chart": _zh(r"\u6392\u540d\u8d8b\u52bf\u56fe"),
    "streamgraph": _zh(r"\u6d41\u5f62\u56fe"),
    "waterfall": _zh(r"\u7011\u5e03\u56fe"),
    "funnel": _zh(r"\u6f0f\u6597\u56fe"),
    "radar": _zh(r"\u96f7\u8fbe\u56fe"),
    "bullet": _zh(r"\u5b50\u5f39\u56fe"),
    "gauge": _zh(r"\u4eea\u8868\u76d8"),
    "treemap": _zh(r"\u6811\u56fe"),
    "sunburst": _zh(r"\u65ed\u65e5\u56fe"),
    "marimekko": _zh(r"\u9a6c\u8d5b\u514b\u56fe"),
    "sankey": _zh(r"\u6851\u57fa\u56fe"),
    "alluvial": _zh(r"\u6cb3\u6d41\u56fe"),
    "chord": _zh(r"\u5f26\u56fe"),
    "geo_map": _zh(r"\u5730\u7406\u5730\u56fe"),
    "choropleth": _zh(r"\u5206\u7ea7\u7740\u8272\u5730\u56fe"),
    "flow_map": _zh(r"\u6d41\u5411\u5730\u56fe"),
    "control_chart": _zh(r"\u63a7\u5236\u56fe"),
    "candlestick": _zh(r"\u8701\u70db\u56fe"),
    "summary": _zh(r"\u6982\u89c8"),
    "executive_summary": _zh(r"\u7ba1\u7406\u6458\u8981"),
    "chapter": _zh(r"\u7ae0\u8282"),
    "visual_gallery": _zh(r"\u56fe\u7ec4\u89e3\u8bfb"),
    "appendix": _zh(r"\u9644\u5f55"),
    "method_note": _zh(r"\u65b9\u6cd5\u8bf4\u660e"),
    "field_glossary": _zh(r"\u5b57\u6bb5\u89e3\u91ca"),
    "evidence_index": _zh(r"\u8bc1\u636e\u7d22\u5f15"),
    "action_plan": _zh(r"\u884c\u52a8\u5efa\u8bae"),
}

REPORT_PART_METHOD_LABELS = {
    "summary": _zh(r"\u7efc\u5408\u6458\u8981"),
    "executive_summary": _zh(r"\u7ba1\u7406\u6458\u8981"),
    "chapter": _zh(r"\u5206\u6790\u7ae0\u8282"),
    "visual_gallery": _zh(r"\u56fe\u7ec4\u89e3\u8bfb"),
    "appendix": _zh(r"\u5206\u6790\u9644\u5f55"),
    "method_note": _zh(r"\u65b9\u6cd5\u8bf4\u660e"),
    "field_glossary": _zh(r"\u5b57\u6bb5\u89e3\u91ca"),
    "evidence_index": _zh(r"\u8bc1\u636e\u7d22\u5f15"),
    "action_plan": _zh(r"\u884c\u52a8\u5efa\u8bae"),
}

FINANCIAL_VISUAL_DOMAINS: list[dict[str, str]] = [
    {"id": "equity_return", "label": _zh(r"\u6743\u76ca\u6536\u76ca"), "role": "time_window"},
    {"id": "index_breadth", "label": _zh(r"\u6307\u6570\u5e7f\u5ea6"), "role": "time_window"},
    {"id": "sector_rotation", "label": _zh(r"\u884c\u4e1a\u8f6e\u52a8"), "role": "grouped"},
    {"id": "style_rotation", "label": _zh(r"\u98ce\u683c\u8f6e\u52a8"), "role": "grouped"},
    {"id": "factor_exposure", "label": _zh(r"\u56e0\u5b50\u66b4\u9732"), "role": "field_set"},
    {"id": "factor_return", "label": _zh(r"\u56e0\u5b50\u6536\u76ca"), "role": "time_window"},
    {"id": "factor_crowding", "label": _zh(r"\u56e0\u5b50\u62e5\u6324"), "role": "field_set"},
    {"id": "valuation_spread", "label": _zh(r"\u4f30\u503c\u5229\u5dee"), "role": "field_pair"},
    {"id": "valuation_percentile", "label": _zh(r"\u4f30\u503c\u5206\u4f4d"), "role": "single_field"},
    {"id": "earnings_revision", "label": _zh(r"\u76c8\u5229\u9884\u6d4b\u4fee\u6b63"), "role": "time_window"},
    {"id": "analyst_consensus", "label": _zh(r"\u5206\u6790\u5e08\u4e00\u81f4\u9884\u671f"), "role": "field_set"},
    {"id": "fund_flow", "label": _zh(r"\u8d44\u91d1\u6d41\u5411"), "role": "time_window"},
    {"id": "northbound_flow", "label": _zh(r"\u5317\u5411\u8d44\u91d1"), "role": "time_window"},
    {"id": "etf_flow", "label": _zh(r"ETF \u6d41\u91cf"), "role": "time_window"},
    {"id": "liquidity_depth", "label": _zh(r"\u6d41\u52a8\u6027\u6df1\u5ea6"), "role": "field_set"},
    {"id": "turnover_heat", "label": _zh(r"\u6362\u624b\u70ed\u5ea6"), "role": "single_field"},
    {"id": "volume_price", "label": _zh(r"\u91cf\u4ef7\u5173\u7cfb"), "role": "field_pair"},
    {"id": "volatility_surface", "label": _zh(r"\u6ce2\u52a8\u7387\u66f2\u9762"), "role": "field_set"},
    {"id": "option_skew", "label": _zh(r"\u671f\u6743\u504f\u5ea6"), "role": "field_pair"},
    {"id": "implied_volatility", "label": _zh(r"\u9690\u542b\u6ce2\u52a8\u7387"), "role": "time_window"},
    {"id": "drawdown_recovery", "label": _zh(r"\u56de\u64a4\u4fee\u590d"), "role": "time_window"},
    {"id": "risk_budget", "label": _zh(r"\u98ce\u9669\u9884\u7b97"), "role": "field_set"},
    {"id": "var_contribution", "label": _zh(r"VaR \u8d21\u732e"), "role": "field_set"},
    {"id": "portfolio_attribution", "label": _zh(r"\u7ec4\u5408\u5f52\u56e0"), "role": "field_set"},
    {"id": "benchmark_tracking", "label": _zh(r"\u57fa\u51c6\u8ddf\u8e2a"), "role": "field_pair"},
    {"id": "position_concentration", "label": _zh(r"\u6301\u4ed3\u96c6\u4e2d\u5ea6"), "role": "entity_level"},
    {"id": "holding_overlap", "label": _zh(r"\u6301\u4ed3\u91cd\u5408"), "role": "field_set"},
    {"id": "macro_cycle", "label": _zh(r"\u5b8f\u89c2\u5468\u671f"), "role": "time_window"},
    {"id": "policy_signal", "label": _zh(r"\u653f\u7b56\u4fe1\u53f7"), "role": "time_window"},
    {"id": "rate_curve", "label": _zh(r"\u5229\u7387\u66f2\u7ebf"), "role": "time_window"},
    {"id": "credit_spread", "label": _zh(r"\u4fe1\u7528\u5229\u5dee"), "role": "field_pair"},
    {"id": "inflation_expectation", "label": _zh(r"\u901a\u80c0\u9884\u671f"), "role": "time_window"},
    {"id": "currency_pressure", "label": _zh(r"\u6c47\u7387\u538b\u529b"), "role": "time_window"},
    {"id": "commodity_term_structure", "label": _zh(r"\u5546\u54c1\u671f\u9650\u7ed3\u6784"), "role": "field_set"},
    {"id": "futures_basis", "label": _zh(r"\u671f\u8d27\u57fa\u5dee"), "role": "field_pair"},
    {"id": "event_impact", "label": _zh(r"\u4e8b\u4ef6\u51b2\u51fb"), "role": "time_window"},
    {"id": "earnings_event", "label": _zh(r"\u8d22\u62a5\u4e8b\u4ef6"), "role": "time_window"},
    {"id": "sentiment_index", "label": _zh(r"\u60c5\u7eea\u6307\u6570"), "role": "time_window"},
    {"id": "news_heat", "label": _zh(r"\u65b0\u95fb\u70ed\u5ea6"), "role": "time_window"},
    {"id": "social_attention", "label": _zh(r"\u793e\u4ea4\u5173\u6ce8"), "role": "time_window"},
    {"id": "esg_score", "label": _zh(r"ESG \u8bc4\u5206"), "role": "field_set"},
    {"id": "carbon_exposure", "label": _zh(r"\u78b3\u66b4\u9732"), "role": "field_set"},
    {"id": "supply_chain", "label": _zh(r"\u4f9b\u5e94\u94fe"), "role": "entity_level"},
    {"id": "regional_capital", "label": _zh(r"\u533a\u57df\u8d44\u672c"), "role": "entity_level"},
    {"id": "peer_comparison", "label": _zh(r"\u540c\u4e1a\u6bd4\u8f83"), "role": "grouped"},
    {"id": "product_profitability", "label": _zh(r"\u4ea7\u54c1\u76c8\u5229"), "role": "grouped"},
    {"id": "customer_cohort", "label": _zh(r"\u5ba2\u7fa4\u961f\u5217"), "role": "grouped"},
    {"id": "scenario_stress", "label": _zh(r"\u60c5\u666f\u538b\u529b"), "role": "field_set"},
    {"id": "forecast_distribution", "label": _zh(r"\u9884\u6d4b\u5206\u5e03"), "role": "time_window"},
    {"id": "alpha_decay", "label": _zh(r"Alpha \u8870\u51cf"), "role": "time_window"},
]

FINANCIAL_VISUAL_PATTERNS: list[dict[str, str]] = [
    {"id": "heatmap_matrix", "label": _zh(r"\u70ed\u529b\u77e9\u9635"), "intent": _zh(r"\u5c55\u793a\u4ea4\u53c9\u7ef4\u5ea6\u5f3a\u5f31")},
    {"id": "ranked_bar_ladder", "label": _zh(r"\u6392\u540d\u68af\u5f62\u6761\u5f62\u56fe"), "intent": _zh(r"\u5c55\u793a\u6392\u540d\u548c\u68af\u5ea6\u5dee")},
    {"id": "slope_change_panel", "label": _zh(r"\u53d8\u5316\u5761\u5ea6\u9762\u677f"), "intent": _zh(r"\u6bd4\u8f83\u524d\u540e\u53d8\u5316\u65b9\u5411")},
    {"id": "waterfall_bridge", "label": _zh(r"\u6865\u63a5\u7011\u5e03\u56fe"), "intent": _zh(r"\u62c6\u89e3\u589e\u51cf\u8d21\u732e")},
    {"id": "sankey_flow", "label": _zh(r"\u6d41\u5411\u6851\u57fa\u56fe"), "intent": _zh(r"\u89e3\u91ca\u8d44\u91d1\u6216\u7ed3\u6784\u6d41\u8f6c")},
    {"id": "chord_relation", "label": _zh(r"\u5173\u8054\u5f26\u56fe"), "intent": _zh(r"\u5c55\u793a\u591a\u5bf9\u591a\u8054\u52a8")},
    {"id": "quadrant_decision_map", "label": _zh(r"\u51b3\u7b56\u8c61\u9650\u56fe"), "intent": _zh(r"\u5c06\u5bf9\u8c61\u5206\u5165\u56db\u7c7b\u884c\u52a8\u533a")},
    {"id": "bubble_rank_map", "label": _zh(r"\u6c14\u6ce1\u6392\u540d\u5730\u56fe"), "intent": _zh(r"\u540c\u65f6\u5c55\u793a\u89c4\u6a21\u3001\u6392\u540d\u548c\u5206\u7ec4")},
    {"id": "bump_ranking_flow", "label": _zh(r"\u6392\u540d\u6d41\u52a8\u56fe"), "intent": _zh(r"\u8ffd\u8e2a\u6392\u540d\u968f\u65f6\u95f4\u53d8\u5316")},
    {"id": "calendar_heatmap", "label": _zh(r"\u65e5\u5386\u70ed\u529b\u56fe"), "intent": _zh(r"\u5c55\u793a\u65e5\u5ea6\u5bc6\u96c6\u6ce2\u52a8")},
    {"id": "cohort_retention_grid", "label": _zh(r"\u961f\u5217\u7559\u5b58\u7f51\u683c"), "intent": _zh(r"\u6bd4\u8f83\u4e0d\u540c\u961f\u5217\u7684\u5ef6\u7eed\u8868\u73b0")},
    {"id": "small_multiple_wall", "label": _zh(r"\u5c0f\u591a\u56fe\u5899"), "intent": _zh(r"\u5e76\u5217\u5bf9\u6bd4\u591a\u4e2a\u5bf9\u8c61")},
    {"id": "bullet_target_band", "label": _zh(r"\u76ee\u6807\u5b50\u5f39\u56fe"), "intent": _zh(r"\u5bf9\u6bd4\u76ee\u6807\u3001\u5b9e\u9645\u548c\u533a\u95f4")},
    {"id": "gauge_risk_band", "label": _zh(r"\u98ce\u9669\u4eea\u8868\u76d8"), "intent": _zh(r"\u7ed9\u51fa\u9608\u503c\u533a\u95f4\u4e0e\u5f53\u524d\u4f4d\u7f6e")},
    {"id": "fan_forecast_cone", "label": _zh(r"\u6247\u5f62\u9884\u6d4b\u9525"), "intent": _zh(r"\u5c55\u793a\u9884\u6d4b\u4e0d\u786e\u5b9a\u6027")},
    {"id": "uncertainty_ribbon", "label": _zh(r"\u4e0d\u786e\u5b9a\u6027\u5e26"), "intent": _zh(r"\u5c55\u793a\u4e2d\u5fc3\u8d8b\u52bf\u548c\u7f6e\u4fe1\u533a\u95f4")},
    {"id": "drawdown_curve", "label": _zh(r"\u56de\u64a4\u66f2\u7ebf"), "intent": _zh(r"\u8ffd\u8e2a\u4ece\u9ad8\u70b9\u5230\u4fee\u590d\u7684\u635f\u5931")},
    {"id": "rolling_window_strip", "label": _zh(r"\u6eda\u52a8\u7a97\u53e3\u5e26"), "intent": _zh(r"\u89c2\u5bdf\u6eda\u52a8\u6307\u6807\u7684\u5e73\u6ed1\u53d8\u5316")},
    {"id": "regime_timeline", "label": _zh(r"\u72b6\u6001\u5206\u6bb5\u65f6\u95f4\u8f74"), "intent": _zh(r"\u6807\u6ce8\u5e02\u573a\u6216\u4e1a\u52a1\u72b6\u6001\u5207\u6362")},
    {"id": "contribution_stack", "label": _zh(r"\u8d21\u732e\u5806\u53e0\u56fe"), "intent": _zh(r"\u5c55\u793a\u5404\u9879\u5bf9\u603b\u4f53\u7684\u8d21\u732e")},
    {"id": "exposure_radar", "label": _zh(r"\u66b4\u9732\u96f7\u8fbe\u56fe"), "intent": _zh(r"\u5c55\u793a\u591a\u7ef4\u66b4\u9732\u8f6e\u5ed3")},
    {"id": "correlation_network", "label": _zh(r"\u76f8\u5173\u7f51\u7edc\u56fe"), "intent": _zh(r"\u5c55\u793a\u8282\u70b9\u95f4\u5173\u8054\u7ed3\u6784")},
    {"id": "density_contour", "label": _zh(r"\u5bc6\u5ea6\u7b49\u9ad8\u56fe"), "intent": _zh(r"\u89c2\u5bdf\u4e24\u7ef4\u5206\u5e03\u5bc6\u96c6\u533a")},
    {"id": "beeswarm_outlier", "label": _zh(r"\u8702\u7fa4\u5f02\u5e38\u70b9\u56fe"), "intent": _zh(r"\u5c55\u793a\u4e2a\u4f53\u5206\u5e03\u548c\u5f02\u5e38\u503c")},
    {"id": "treemap_structure", "label": _zh(r"\u7ed3\u6784\u6811\u56fe"), "intent": _zh(r"\u5c55\u793a\u5c42\u7ea7\u5360\u6bd4")},
    {"id": "sunburst_hierarchy", "label": _zh(r"\u5c42\u7ea7\u65ed\u65e5\u56fe"), "intent": _zh(r"\u4ece\u5185\u5230\u5916\u5c55\u793a\u5c42\u7ea7\u7ed3\u6784")},
    {"id": "alluvial_transition", "label": _zh(r"\u8fc1\u79fb\u6cb3\u6d41\u56fe"), "intent": _zh(r"\u5c55\u793a\u7c7b\u522b\u4e4b\u95f4\u8fc1\u79fb")},
    {"id": "marimekko_share", "label": _zh(r"\u4efd\u989d\u9a6c\u8d5b\u514b\u56fe"), "intent": _zh(r"\u540c\u65f6\u8868\u8fbe\u5360\u6bd4\u548c\u89c4\u6a21")},
    {"id": "control_band", "label": _zh(r"\u63a7\u5236\u5e26\u56fe"), "intent": _zh(r"\u5c55\u793a\u8d85\u51fa\u9608\u503c\u7684\u5f02\u5e38")},
    {"id": "candlestick_panel", "label": _zh(r"\u8721\u70db\u9762\u677f\u56fe"), "intent": _zh(r"\u5c55\u793a OHLC \u6216\u533a\u95f4\u6ce2\u52a8")},
    {"id": "spread_ladder", "label": _zh(r"\u5229\u5dee\u9636\u68af\u56fe"), "intent": _zh(r"\u5c55\u793a\u5229\u5dee\u5c42\u7ea7\u548c\u5f02\u5e38\u8df3\u53d8")},
    {"id": "zscore_signal_strip", "label": _zh(r"Z \u5206\u6570\u4fe1\u53f7\u5e26"), "intent": _zh(r"\u7528\u6807\u51c6\u5316\u4f4d\u7f6e\u8bc6\u522b\u6781\u7aef")},
]

FINANCIAL_VISUAL_OUTPUT_TYPES = ["chart", "image_spec", "report_section", "text", "table", "data"]

STATISTICAL_VISUAL_OUTPUT_TYPES = ["chart", "image_spec", "report_section", "text", "table", "data"]

STATISTICAL_VISUAL_DOMAINS: list[dict[str, str]] = [
    {"id": "distribution_shape", "label": "Distribution shape", "role": "single_field", "goal": "inspect skew, modality, tails and range for one measured variable"},
    {"id": "tail_outlier", "label": "Tail and outlier structure", "role": "single_field", "goal": "separate ordinary variation from extreme observations"},
    {"id": "missingness_pattern", "label": "Missingness pattern", "role": "field_set", "goal": "show where missing values concentrate across variables and records"},
    {"id": "data_quality", "label": "Data quality profile", "role": "field_set", "goal": "summarize completeness, invalid values and duplicate signals"},
    {"id": "group_balance", "label": "Group balance diagnostic", "role": "grouped", "goal": "compare sample size and baseline balance across groups"},
    {"id": "group_difference", "label": "Group difference evidence", "role": "grouped", "goal": "show group separation, overlap and practical effect magnitude"},
    {"id": "effect_size", "label": "Effect size view", "role": "field_pair", "goal": "display magnitude and interval evidence instead of only significance"},
    {"id": "categorical_composition", "label": "Categorical composition", "role": "categorical", "goal": "compare category shares, concentration and rare levels"},
    {"id": "contingency_structure", "label": "Contingency structure", "role": "field_pair", "goal": "visualize cross-tab association and residual cells"},
    {"id": "ordinal_response", "label": "Ordinal response profile", "role": "categorical", "goal": "show ordered category shifts and threshold behavior"},
    {"id": "relationship_strength", "label": "Relationship strength", "role": "field_pair", "goal": "inspect association direction, strength and influential points"},
    {"id": "nonlinear_relationship", "label": "Nonlinear relationship", "role": "field_pair", "goal": "reveal curved, segmented or saturating relationships"},
    {"id": "correlation_structure", "label": "Correlation structure", "role": "field_set", "goal": "summarize pairwise dependency patterns across variables"},
    {"id": "partial_association", "label": "Partial association", "role": "field_set", "goal": "show association remaining after accounting for covariates"},
    {"id": "interaction_effect", "label": "Interaction effect", "role": "field_set", "goal": "display whether one predictor changes the effect of another"},
    {"id": "multivariate_projection", "label": "Multivariate projection", "role": "field_set", "goal": "compress many variables into interpretable low-dimensional views"},
    {"id": "cluster_structure", "label": "Cluster structure", "role": "field_set", "goal": "inspect natural grouping, separation and cluster stability"},
    {"id": "dimension_reduction", "label": "Dimension reduction", "role": "field_set", "goal": "show variance, component scores and feature contribution"},
    {"id": "factor_loading", "label": "Factor loading pattern", "role": "field_set", "goal": "interpret latent factor loadings and cross-loading structure"},
    {"id": "model_fit", "label": "Model fit diagnostic", "role": "field_set", "goal": "compare fitted values, observed values and fit quality"},
    {"id": "residual_pattern", "label": "Residual pattern", "role": "field_set", "goal": "detect heteroscedasticity, curvature and influential residuals"},
    {"id": "calibration", "label": "Calibration diagnostic", "role": "field_set", "goal": "compare predicted probabilities or scores with observed outcomes"},
    {"id": "feature_importance", "label": "Feature importance", "role": "field_set", "goal": "rank predictors and show contribution uncertainty"},
    {"id": "prediction_error", "label": "Prediction error", "role": "field_set", "goal": "visualize error distribution, bias and subgroup error patterns"},
    {"id": "causal_balance", "label": "Causal balance", "role": "field_set", "goal": "check covariate balance before and after adjustment"},
    {"id": "treatment_effect", "label": "Treatment effect heterogeneity", "role": "field_set", "goal": "show effect variation across groups, strata or scores"},
    {"id": "experiment_response", "label": "Experiment response", "role": "grouped", "goal": "compare experimental arms over outcomes and segments"},
    {"id": "dose_response", "label": "Dose response", "role": "field_pair", "goal": "show how response changes over ordered exposure levels"},
    {"id": "time_trend", "label": "Time trend", "role": "time_window", "goal": "show trend, level shifts and sustained movement over time"},
    {"id": "seasonality_pattern", "label": "Seasonality pattern", "role": "time_window", "goal": "separate repeating seasonal structure from trend"},
    {"id": "autocorrelation_pattern", "label": "Autocorrelation pattern", "role": "time_window", "goal": "inspect lag dependency and serial structure"},
    {"id": "change_point", "label": "Change point", "role": "time_window", "goal": "locate structural breaks, regime switches and abrupt shifts"},
    {"id": "forecast_uncertainty", "label": "Forecast uncertainty", "role": "time_window", "goal": "display expected path together with interval evidence"},
    {"id": "longitudinal_trajectory", "label": "Longitudinal trajectory", "role": "time_window", "goal": "show subject-level or group-level repeated measurements"},
    {"id": "survival_curve", "label": "Survival curve", "role": "time_window", "goal": "show event-free probability over follow-up time"},
    {"id": "hazard_comparison", "label": "Hazard comparison", "role": "time_window", "goal": "compare event intensity patterns across groups"},
    {"id": "spatial_hotspot", "label": "Spatial hotspot", "role": "entity_level", "goal": "show geographic clustering and local concentration"},
    {"id": "spatial_autocorrelation", "label": "Spatial autocorrelation", "role": "entity_level", "goal": "inspect whether nearby locations have similar values"},
    {"id": "network_centrality", "label": "Network centrality", "role": "entity_level", "goal": "show node influence, bridges and connected components"},
    {"id": "community_structure", "label": "Community structure", "role": "entity_level", "goal": "detect modular groups and cross-community ties"},
    {"id": "text_topic", "label": "Text topic structure", "role": "field_set", "goal": "visualize topic prevalence and document-topic association"},
    {"id": "sentiment_distribution", "label": "Sentiment distribution", "role": "field_set", "goal": "show sentiment spread, subgroup contrast and drift"},
    {"id": "survey_weighting", "label": "Survey weighting", "role": "field_set", "goal": "compare weighted and unweighted estimates across strata"},
    {"id": "reliability_scale", "label": "Reliability scale", "role": "field_set", "goal": "inspect item consistency, scale score spread and reliability evidence"},
    {"id": "quality_control", "label": "Quality control", "role": "time_window", "goal": "monitor process stability, rule violations and unusual variation"},
    {"id": "eda_numeric_overview", "label": "EDA numeric overview", "role": "single_field", "goal": "summarize central tendency, spread, shape and unusual numeric records"},
    {"id": "eda_categorical_overview", "label": "EDA categorical overview", "role": "categorical", "goal": "show category counts, sparse levels and concentration before modeling"},
    {"id": "robust_summary", "label": "Robust summary", "role": "single_field", "goal": "compare resistant summaries with ordinary summaries under skew or extreme values"},
    {"id": "sample_coverage", "label": "Sample coverage", "role": "field_set", "goal": "show which populations, strata or records are represented in the data"},
    {"id": "duplicate_record_structure", "label": "Duplicate record structure", "role": "field_set", "goal": "locate repeated records and repeated key patterns before analysis"},
    {"id": "data_validation_rules", "label": "Data validation rules", "role": "field_set", "goal": "visualize rule failures, invalid ranges and inconsistent field combinations"},
    {"id": "measurement_error", "label": "Measurement error", "role": "single_field", "goal": "inspect noise, rounding, heaping and implausible measurement patterns"},
    {"id": "distribution_comparison", "label": "Distribution comparison", "role": "grouped", "goal": "compare outcome shape and spread across independent groups"},
    {"id": "subgroup_variability", "label": "Subgroup variability", "role": "grouped", "goal": "show whether variation differs across subgroups or settings"},
    {"id": "baseline_covariate_balance", "label": "Baseline covariate balance", "role": "grouped", "goal": "compare pre-analysis covariates across groups before estimating effects"},
    {"id": "paired_change", "label": "Paired change", "role": "field_pair", "goal": "show within-unit before-after movement and direction of change"},
    {"id": "agreement_reliability", "label": "Agreement reliability", "role": "field_set", "goal": "assess consistency among repeated measures or related ratings"},
    {"id": "inter_rater_agreement", "label": "Inter-rater agreement", "role": "field_set", "goal": "show rater consistency, disagreement cells and uncertain labels"},
    {"id": "item_response_pattern", "label": "Item response pattern", "role": "field_set", "goal": "inspect survey or assessment item response distributions and gaps"},
    {"id": "scale_score_profile", "label": "Scale score profile", "role": "field_set", "goal": "summarize composite scale scores and item contribution patterns"},
    {"id": "latent_construct", "label": "Latent construct", "role": "field_set", "goal": "visualize hidden construct structure across observed indicators"},
    {"id": "principal_component_variance", "label": "Principal component variance", "role": "field_set", "goal": "show component variance explained and loading contribution"},
    {"id": "manifold_structure", "label": "Manifold structure", "role": "field_set", "goal": "inspect nonlinear high-dimensional structure in a low-dimensional view"},
    {"id": "outlier_influence", "label": "Outlier influence", "role": "field_set", "goal": "identify observations that materially change estimates or fitted patterns"},
    {"id": "leverage_structure", "label": "Leverage structure", "role": "field_set", "goal": "show predictor-space points that can dominate model estimates"},
    {"id": "heteroscedasticity_pattern", "label": "Heteroscedasticity pattern", "role": "field_set", "goal": "detect changing residual variance across fitted values or predictors"},
    {"id": "nonlinear_fit_shape", "label": "Nonlinear fit shape", "role": "field_pair", "goal": "show curvature, thresholds or saturation in a modeled relationship"},
    {"id": "regularization_path", "label": "Regularization path", "role": "field_set", "goal": "compare coefficient shrinkage and feature entry across penalty levels"},
    {"id": "classifier_threshold", "label": "Classifier threshold", "role": "field_set", "goal": "compare classification outcomes across candidate decision thresholds"},
    {"id": "confusion_error_profile", "label": "Confusion error profile", "role": "field_set", "goal": "translate model mistakes into false positive and false negative structure"},
    {"id": "calibration_by_group", "label": "Calibration by group", "role": "field_set", "goal": "compare predicted probabilities with observed outcomes across groups"},
    {"id": "feature_contribution", "label": "Feature contribution", "role": "field_set", "goal": "show how predictors contribute to model predictions or fitted effects"},
    {"id": "prediction_interval", "label": "Prediction interval", "role": "field_set", "goal": "display expected predictions together with uncertainty intervals"},
    {"id": "counterfactual_contrast", "label": "Counterfactual contrast", "role": "field_set", "goal": "compare observed outcomes with estimated counterfactual outcomes"},
    {"id": "propensity_overlap", "label": "Propensity overlap", "role": "field_set", "goal": "inspect common support before matching or weighting"},
    {"id": "instrument_strength", "label": "Instrument strength", "role": "field_set", "goal": "show relevance and weak-instrument warnings for instrumental designs"},
    {"id": "discontinuity_window", "label": "Discontinuity window", "role": "field_pair", "goal": "inspect observations around an assignment threshold"},
    {"id": "mediation_path", "label": "Mediation path", "role": "field_set", "goal": "visualize direct, indirect and mediated pathways among variables"},
    {"id": "sensitivity_bounds", "label": "Sensitivity bounds", "role": "field_set", "goal": "show how conclusions change under alternative assumptions"},
    {"id": "randomization_check", "label": "Randomization check", "role": "grouped", "goal": "test whether randomized groups look balanced before outcome analysis"},
    {"id": "assignment_flow", "label": "Assignment flow", "role": "grouped", "goal": "show allocation, exclusion and analysis-set movement in an experiment"},
    {"id": "experiment_power", "label": "Experiment power", "role": "field_set", "goal": "visualize detectable effects across sample sizes and variance assumptions"},
    {"id": "sequential_monitoring", "label": "Sequential monitoring", "role": "time_window", "goal": "track accumulating evidence while guarding against premature conclusions"},
    {"id": "factorial_response", "label": "Factorial response", "role": "grouped", "goal": "show main effects and interactions in multi-factor experiments"},
    {"id": "block_design_balance", "label": "Block design balance", "role": "grouped", "goal": "verify representation within blocks, strata or matched sets"},
    {"id": "survey_response_pattern", "label": "Survey response pattern", "role": "field_set", "goal": "show response rates, item completion and respondent coverage"},
    {"id": "sample_weight_effect", "label": "Sample weight effect", "role": "field_set", "goal": "compare estimates before and after applying sample weights"},
    {"id": "nonresponse_pattern", "label": "Nonresponse pattern", "role": "field_set", "goal": "detect where nonresponse concentrates across respondent groups"},
    {"id": "questionnaire_item_quality", "label": "Questionnaire item quality", "role": "field_set", "goal": "inspect item difficulty, discrimination and missing response patterns"},
    {"id": "education_growth", "label": "Education growth", "role": "time_window", "goal": "show learning progression or assessment change across time"},
    {"id": "student_performance_distribution", "label": "Student performance distribution", "role": "grouped", "goal": "compare achievement spread across classes, programs or cohorts"},
    {"id": "classroom_fairness", "label": "Classroom fairness", "role": "grouped", "goal": "compare outcomes across learner groups while preserving uncertainty"},
    {"id": "clinical_endpoint", "label": "Clinical endpoint", "role": "grouped", "goal": "compare patient outcomes across treatment, site or subgroup"},
    {"id": "patient_trajectory", "label": "Patient trajectory", "role": "time_window", "goal": "show repeated patient measurements and clinically relevant changes"},
    {"id": "public_health_incidence", "label": "Public health incidence", "role": "time_window", "goal": "track disease or event rates over time and place"},
    {"id": "epidemiology_cluster", "label": "Epidemiology cluster", "role": "entity_level", "goal": "show local clustering of cases or exposures across areas"},
    {"id": "survival_strata", "label": "Survival strata", "role": "time_window", "goal": "compare time-to-event patterns across strata or care pathways"},
    {"id": "lab_measurement_qc", "label": "Laboratory measurement QC", "role": "time_window", "goal": "monitor repeated measurements, controls and assay drift"},
    {"id": "manufacturing_process_stability", "label": "Manufacturing process stability", "role": "time_window", "goal": "track process location, spread and special-cause variation"},
    {"id": "defect_classification", "label": "Defect classification", "role": "categorical", "goal": "show defect type frequency, severity and co-occurrence"},
    {"id": "service_queue_pattern", "label": "Service queue pattern", "role": "time_window", "goal": "visualize waiting time, backlog and service-level variation"},
    {"id": "operations_capacity", "label": "Operations capacity", "role": "grouped", "goal": "compare workload, throughput and constraint patterns across units"},
    {"id": "inventory_process_variation", "label": "Inventory process variation", "role": "time_window", "goal": "track counts, replenishment timing and unusual depletion patterns"},
    {"id": "spatial_accessibility", "label": "Spatial accessibility", "role": "entity_level", "goal": "show distance, service coverage and local access gaps"},
    {"id": "environmental_exposure", "label": "Environmental exposure", "role": "entity_level", "goal": "map exposure intensity and spatial gradients across areas"},
    {"id": "regional_inequality", "label": "Regional inequality", "role": "entity_level", "goal": "compare outcomes and uncertainty across geographic regions"},
    {"id": "mobility_flow", "label": "Mobility flow", "role": "entity_level", "goal": "show movement between places, groups or states over time"},
    {"id": "network_bridge", "label": "Network bridge", "role": "entity_level", "goal": "identify bridge nodes, isolates and cross-group connections"},
    {"id": "network_diffusion", "label": "Network diffusion", "role": "entity_level", "goal": "show how information, behavior or events spread through a network"},
    {"id": "text_frequency", "label": "Text frequency", "role": "field_set", "goal": "show term frequency, document coverage and salient word groups"},
]

STATISTICAL_VISUAL_PATTERNS: list[dict[str, str]] = [
    {"id": "diagnostic_panel", "label": "Diagnostic panel", "intent": "combine summary marks, reference bands and annotated exceptions"},
    {"id": "stratified_dotplot", "label": "Stratified dot plot", "intent": "show individual observations beside grouped summaries"},
    {"id": "density_ridge", "label": "Density ridge", "intent": "compare distribution shape across groups or time slices"},
    {"id": "quantile_band", "label": "Quantile band", "intent": "show median, spread and outer quantiles in one view"},
    {"id": "small_multiple_grid", "label": "Small-multiple grid", "intent": "repeat the same statistical view across segments"},
    {"id": "heatmap_matrix", "label": "Heatmap matrix", "intent": "encode magnitude or residual strength across two dimensions"},
    {"id": "slope_change_view", "label": "Slope change view", "intent": "compare before-after direction and magnitude"},
    {"id": "uncertainty_ribbon", "label": "Uncertainty ribbon", "intent": "show central tendency together with interval evidence"},
    {"id": "threshold_band", "label": "Threshold band", "intent": "mark expected, warning and exception zones"},
    {"id": "rank_interval_plot", "label": "Rank interval plot", "intent": "rank units while preserving uncertainty or spread"},
    {"id": "annotated_reference_view", "label": "Annotated reference view", "intent": "compare observations against statistical reference values and labels"},
    {"id": "comparative_lollipop", "label": "Comparative lollipop plot", "intent": "compare units, groups or strata with compact ranked markers"},
    {"id": "residual_annotation_map", "label": "Residual annotation map", "intent": "highlight fitted-versus-observed exceptions and structured residual signals"},
    {"id": "violin_summary", "label": "Violin summary", "intent": "show distribution density together with robust summary marks"},
    {"id": "boxen_interval", "label": "Boxen interval plot", "intent": "show nested quantile intervals for detailed spread comparison"},
    {"id": "histogram_facets", "label": "Histogram facets", "intent": "compare binned distributions across groups or time slices"},
    {"id": "ecdf_step_view", "label": "ECDF step view", "intent": "show cumulative distribution differences without binning choices"},
    {"id": "qq_reference_plot", "label": "Q-Q reference plot", "intent": "compare observed quantiles with a reference distribution"},
    {"id": "forest_interval_plot", "label": "Forest interval plot", "intent": "compare estimates and confidence intervals across subgroups"},
    {"id": "raincloud_view", "label": "Raincloud view", "intent": "combine density, raw observations and summary intervals"},
    {"id": "mosaic_tile_view", "label": "Mosaic tile view", "intent": "show categorical association through proportional tiles"},
    {"id": "flow_transition_map", "label": "Flow transition map", "intent": "show movement or state changes between categories"},
    {"id": "network_node_link", "label": "Network node-link view", "intent": "show nodes, ties and structural clusters"},
    {"id": "map_choropleth_layer", "label": "Map choropleth layer", "intent": "show spatial intensity and local differences across regions"},
]

ROLE_LABELS = {
    "single_field": _zh(r"\u5355\u5b57\u6bb5"),
    "field_pair": _zh(r"\u5b57\u6bb5\u5bf9"),
    "field_set": _zh(r"\u5b57\u6bb5\u7ec4"),
    "grouped": _zh(r"\u5206\u7ec4"),
    "time_window": _zh(r"\u65f6\u95f4\u7a97\u53e3"),
    "entity_level": _zh(r"\u5bf9\u8c61\u7ea7"),
    "full_dataset": _zh(r"\u5168\u6570\u636e\u96c6"),
    "derived_metric": _zh(r"\u6d3e\u751f\u6307\u6807"),
    "continuous": _zh(r"\u8fde\u7eed\u53d8\u91cf"),
    "numeric": _zh(r"\u6570\u503c\u5b57\u6bb5"),
    "measure": _zh(r"\u5ea6\u91cf\u6307\u6807"),
    "categorical": _zh(r"\u5206\u7c7b\u5b57\u6bb5"),
    "dimension": _zh(r"\u7ef4\u5ea6\u5b57\u6bb5"),
}

OUTPUT_LABELS = {
    "text": _zh(r"\u6587\u5b57\u89e3\u8bfb"),
    "table": _zh(r"\u8868\u683c"),
    "data": _zh(r"\u7ed3\u6784\u5316\u6570\u636e"),
    "chart": _zh(r"\u56fe\u8868"),
    "image_spec": _zh(r"\u56fe\u7247\u89c4\u683c"),
    "report_section": _zh(r"\u62a5\u544a\u6bb5\u843d"),
}

NO_IMAGE_OUTPUT_TYPES = ["text", "table", "data"]
FULL_OUTPUT_TYPES = ["text", "table", "data", "chart", "image_spec", "report_section"]
STATISTICAL_OUTPUT_VARIANTS = ["text", "table", "data", "chart", "image_spec", "report_section"]
VISUAL_OUTPUT_FAMILIES = {"visual", "report_part"}
REPORT_SECTION_OUTPUT_TYPES = ["report_section", "text", "table", "data"]
VISUAL_DEFAULT_OUTPUT_TYPES = ["chart", "text"]
TEXTUAL_DEFAULT_OUTPUT_TYPES = ["text", "table", "data"]
STATISTICAL_VISUAL_FAMILIES = {"time_series", "survival"}
STATISTICAL_VISUAL_METHOD_IDS = {
    "lorenz_curve",
    "pareto_analysis",
    "cohort_summary",
    "segmented_kpi_breakdown",
    "correlation",
    "correspondence_analysis",
    "seasonal_decomposition",
    "autocorrelation",
    "partial_autocorrelation",
    "prophet_style_trend",
    "kaplan_meier",
    "nelson_aalen",
    "pca",
    "factor_analysis",
    "kmeans",
    "hierarchical_clustering",
    "dbscan",
    "gaussian_mixture",
}
STATISTICAL_VISUAL_NAME_HINTS = (
    "curve",
    "plot",
    "chart",
    "matrix",
    "heatmap",
    "decomposition",
    "trend",
    "clustering",
    "correspondence",
)


def _default_output_types_for_method(family: str, requested_output: str = "") -> list[str]:
    output = str(requested_output or "").strip()
    if family in VISUAL_OUTPUT_FAMILIES or output in {"chart", "image_spec", "report_section"}:
        candidates = [output, *FULL_OUTPUT_TYPES] if output else FULL_OUTPUT_TYPES
        return list(dict.fromkeys(item for item in candidates if item))
    candidates = [output, *NO_IMAGE_OUTPUT_TYPES] if output else NO_IMAGE_OUTPUT_TYPES
    return list(dict.fromkeys(item for item in candidates if item))


def _method_supports_visual_outputs(method: dict[str, Any]) -> bool:
    family = str(method.get("family") or "").strip()
    if family in VISUAL_OUTPUT_FAMILIES:
        return True
    if family not in STATISTICAL_VISUAL_FAMILIES and method.get("source") != "statistical_catalog":
        return False
    method_id = str(method.get("base_method_id") or method.get("id") or "").strip()
    if method_id in STATISTICAL_VISUAL_METHOD_IDS:
        return True
    if family in STATISTICAL_VISUAL_FAMILIES:
        return True
    haystack = " ".join(
        str(method.get(key) or "").lower()
        for key in ("id", "name", "goal", "method_concept_label")
    )
    return any(hint in haystack for hint in STATISTICAL_VISUAL_NAME_HINTS)


def _catalog_output_variants_for_method(method: dict[str, Any]) -> list[str]:
    return STATISTICAL_OUTPUT_VARIANTS if _method_supports_visual_outputs(method) else NO_IMAGE_OUTPUT_TYPES


def _generated_method_supports_visual_outputs(family: str, method_name: str) -> bool:
    if family in VISUAL_OUTPUT_FAMILIES:
        return True
    if family in STATISTICAL_VISUAL_FAMILIES:
        return True
    if family in {"association", "categorical_association", "time_series", "machine_learning", "multivariate"}:
        return True
    if family in {"descriptive", "distribution_assumption"} and method_name in {"distribution", "rank"}:
        return True
    return any(hint in method_name for hint in STATISTICAL_VISUAL_NAME_HINTS)


def _stable_output_types_for_generated_method(family: str, method_name: str) -> list[str]:
    if family == "report_part":
        return REPORT_SECTION_OUTPUT_TYPES
    if family == "visual":
        return FULL_OUTPUT_TYPES
    if _generated_method_supports_visual_outputs(family, method_name):
        return FULL_OUTPUT_TYPES
    return NO_IMAGE_OUTPUT_TYPES


def _default_output_types_for_generated_method(family: str, method_name: str, stable_outputs: list[str]) -> list[str]:
    if family == "report_part":
        candidates = ["report_section", "text"]
    elif family == "visual":
        candidates = VISUAL_DEFAULT_OUTPUT_TYPES
    elif "chart" in stable_outputs and (family in {"association", "categorical_association", "time_series"} or method_name in {"distribution", "rank"}):
        candidates = ["chart", "text", "table"]
    else:
        candidates = TEXTUAL_DEFAULT_OUTPUT_TYPES
    return [item for item in candidates if item in stable_outputs]


def _runtime_capability_metadata(
    *,
    stable_outputs: list[str],
    default_outputs: list[str],
    binding_roles: list[str],
    compatibility_alias_ids: list[str] | None = None,
    output_modes: list[str] | None = None,
    granularity_modes: list[str] | None = None,
    analysis_kind: str = "analysis",
    render_profile: dict[str, Any] | None = None,
    report_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stable = list(dict.fromkeys(stable_outputs))
    defaults = list(dict.fromkeys(default_outputs))
    roles = list(dict.fromkeys(binding_roles))
    outputs = list(dict.fromkeys(output_modes or stable))
    granularities = list(dict.fromkeys(granularity_modes or roles))
    return {
        "stable_output_types": stable,
        "default_output_types": defaults,
        "runtime_required": True,
        "runtime_executor": "codex_cli",
        "cli_runtime_available": True,
        "runtime_block_reason": "",
        "runtime_binding_roles": roles,
        "output_modes": outputs,
        "granularity_modes": granularities,
        "runtime_dimensions": {
            "analysis": [analysis_kind],
            "render": outputs,
            "report": ["method_card", "report_section", "evidence_index"],
            "run": granularities,
        },
        "run_metadata_schema": {
            "output_mode": outputs,
            "granularity": granularities,
            "analysis_kind": analysis_kind,
            "render_profile": dict(render_profile or {}),
            "report_profile": dict(report_profile or {}),
            "field_binding_roles": roles,
        },
        "artifact_contract": {
            "contract": "analysis_lab_runtime_artifacts_v2",
            "method_identity_is_concept": True,
            "outputs_are_runtime_modes": True,
            "granularity_is_runtime_metadata": True,
            "required_artifacts": ["json", "csv", "xlsx", "markdown"],
            "optional_artifacts": ["png", "svg", "html", "image_spec"],
        },
        "compatibility_alias_ids": list(dict.fromkeys(compatibility_alias_ids or [])),
    }


@lru_cache(maxsize=4)
def load_auto_analysis_specs() -> dict[str, Any]:
    configured = os.getenv("ASTERIA_AUTO_ANALYSIS_SPEC_PATH", "").strip()
    spec_path = Path(configured) if configured else DEFAULT_SPEC_PATH
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("auto analysis spec must be a JSON object")
    return payload


def _generated_method_registry(specs: dict[str, Any]) -> list[dict[str, Any]]:
    generation = specs.get("method_generation") if isinstance(specs.get("method_generation"), dict) else {}
    families = generation.get("families") if isinstance(generation.get("families"), dict) else {}
    outputs = list(generation.get("outputs") or [])
    granularities = list(generation.get("granularities") or [])
    registry: list[dict[str, Any]] = []
    for family, methods in families.items():
        if str(family) == "report_part":
            for method_name in list(methods or []):
                part_id = str(method_name or "").strip()
                if not part_id:
                    continue
                part_label = REPORT_PART_METHOD_LABELS.get(part_id, part_id.replace("_", " "))
                method_id = f"report_part_{part_id}"
                registry.append(
                    {
                        "id": method_id,
                        "name": part_label,
                        "name_zh": part_label,
                        "family": "report_part",
                        "goal": f"Generate the {part_id} report part from routed evidence, tables, charts and method outputs.",
                        "method_concept_label": part_label,
                        "status": "planned",
                        "output_types": ["report_section", "text", "table", "data"],
                        "required_roles": ["full_dataset"],
                        "source": "auto_analysis_specs",
                        "catalog_output_variant": "report_section",
                        "base_method_id": method_id,
                        "bundle_id": method_id,
                        "bundle_title_zh": part_label,
                        "parent_method_title": part_label,
                        **_runtime_capability_metadata(
                            stable_outputs=["report_section", "text", "table", "data"],
                            default_outputs=["report_section", "text"],
                            binding_roles=["full_dataset"],
                            compatibility_alias_ids=[f"report_part_{part_id}_full_dataset_report_section"],
                            output_modes=["report_section", "text", "table", "data"],
                            granularity_modes=["full_dataset"],
                            analysis_kind="report_part",
                            render_profile={"report_part_id": part_id},
                            report_profile={"report_part_id": part_id, "requires_evidence": True},
                        ),
                    }
                )
            continue
        for method_name in list(methods or []):
            family_text = str(family)
            method_name_text = str(method_name)
            stable_outputs = [
                output
                for output in _stable_output_types_for_generated_method(family_text, method_name_text)
                if output in outputs
            ]
            if not stable_outputs:
                continue
            method_id = f"{family_text}_{method_name_text}"
            bundle_id = f"{family_text}_{method_name_text}"
            concept_label = METHOD_LABELS.get(method_name_text, method_name_text.replace("_", " "))
            default_outputs = _default_output_types_for_generated_method(family_text, method_name_text, stable_outputs)
            binding_roles = list(dict.fromkeys(str(item) for item in granularities if str(item).strip()))
            compatibility_alias_ids = [
                f"{family_text}_{method_name_text}_{granularity}_{output}"
                for granularity in binding_roles
                for output in stable_outputs
            ]
            registry.append(
                {
                    "id": method_id,
                    "name": " ".join(part.title() for part in method_id.split("_")),
                    "family": family_text,
                    "goal": (
                        f"Run the {method_name_text} method as one independent analysis card; "
                        "choose output and granularity through run metadata instead of separate method IDs."
                    ),
                    "status": "planned",
                    "output_types": stable_outputs,
                    "required_roles": binding_roles,
                    "source": "auto_analysis_specs",
                    "catalog_output_variant": default_outputs[0] if default_outputs else stable_outputs[0],
                    "base_method_id": bundle_id,
                    "bundle_id": bundle_id,
                    "bundle_title_zh": concept_label,
                    "parent_method_title": concept_label,
                    "method_concept_label": concept_label,
                    **_runtime_capability_metadata(
                        stable_outputs=stable_outputs,
                        default_outputs=default_outputs,
                        binding_roles=binding_roles,
                        compatibility_alias_ids=compatibility_alias_ids,
                        output_modes=stable_outputs,
                        granularity_modes=binding_roles,
                        analysis_kind=family_text,
                        render_profile={
                            "method": method_name_text,
                            "visual_capable": _generated_method_supports_visual_outputs(family_text, method_name_text),
                        },
                        report_profile={
                            "can_write_report_section": "report_section" in stable_outputs,
                            "default_report_mode": "report_section" if "report_section" in stable_outputs else "method_note",
                        },
                    ),
                }
            )
    return registry


def _generated_financial_visual_registry() -> list[dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    for domain, pattern in product(FINANCIAL_VISUAL_DOMAINS, FINANCIAL_VISUAL_PATTERNS):
        domain_id = str(domain["id"])
        pattern_id = str(pattern["id"])
        base_id = f"visual_finance_{domain_id}_{pattern_id}"
        title = f"{domain['label']}{_zh(r'\u30fb')}{pattern['label']}"
        role = str(domain.get("role") or "field_set")
        goal = (
            f"{title}: {pattern['intent']}; build Wind-style financial visual evidence "
            "with output type and granularity chosen at runtime."
        )
        compatibility_alias_ids = [f"{base_id}_{role}_{output}" for output in FINANCIAL_VISUAL_OUTPUT_TYPES]
        registry.append(
            {
                "id": base_id,
                "name": " ".join(part.title() for part in base_id.split("_")),
                "name_zh": title,
                "family": "visual",
                "goal": goal,
                "method_concept_label": title,
                "status": "planned",
                "output_types": FINANCIAL_VISUAL_OUTPUT_TYPES,
                "required_roles": [role],
                "source": "financial_visual_catalog",
                "base_method_id": base_id,
                "bundle_id": base_id,
                "bundle_title_zh": title,
                "parent_method_title": title,
                "visual_domain_id": domain_id,
                "visual_domain_label": domain["label"],
                "visual_pattern_id": pattern_id,
                "visual_pattern_label": pattern["label"],
                "visual_intent": pattern["intent"],
                **_runtime_capability_metadata(
                    stable_outputs=FINANCIAL_VISUAL_OUTPUT_TYPES,
                    default_outputs=["chart", "image_spec", "report_section"],
                    binding_roles=[role],
                    compatibility_alias_ids=compatibility_alias_ids,
                    output_modes=FINANCIAL_VISUAL_OUTPUT_TYPES,
                    granularity_modes=[role, "time_window", "entity_level", "grouped", "full_dataset"],
                    analysis_kind="financial_visual",
                    render_profile={
                        "visual_domain_id": domain_id,
                        "visual_pattern_id": pattern_id,
                        "chart_pattern": pattern_id,
                        "style_reference": "wind_research_report",
                    },
                    report_profile={
                        "report_voice": "sell_side_research",
                        "caption_required": True,
                        "interpretation_required": True,
                    },
                ),
            }
        )
    return registry


def _generated_statistical_visual_registry() -> list[dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    for domain, pattern in product(STATISTICAL_VISUAL_DOMAINS, STATISTICAL_VISUAL_PATTERNS):
        domain_id = str(domain["id"])
        pattern_id = str(pattern["id"])
        base_id = f"visual_stat_{domain_id}_{pattern_id}"
        title = f"{domain['label']} - {pattern['label']}"
        role = str(domain.get("role") or "field_set")
        goal = (
            f"{title}: {domain['goal']}; {pattern['intent']}. "
            "This is a non-financial statistical visualization method."
        )
        compatibility_alias_ids = [f"{base_id}_{role}_{output}" for output in STATISTICAL_VISUAL_OUTPUT_TYPES]
        registry.append(
            {
                "id": base_id,
                "name": title,
                "name_zh": title,
                "family": "visual",
                "goal": goal,
                "method_concept_label": title,
                "status": "planned",
                "output_types": STATISTICAL_VISUAL_OUTPUT_TYPES,
                "required_roles": [role],
                "source": "statistical_visual_catalog",
                "base_method_id": base_id,
                "bundle_id": base_id,
                "bundle_title": title,
                "bundle_title_zh": title,
                "bundle_title_en": title,
                "parent_method_title": title,
                "visual_domain_id": domain_id,
                "visual_domain_label": domain["label"],
                "visual_pattern_id": pattern_id,
                "visual_pattern_label": pattern["label"],
                "visual_intent": pattern["intent"],
                "non_financial_statistical_visual": True,
                "allowed_domain": "non_financial",
                "excluded_domain": "finance",
                **_runtime_capability_metadata(
                    stable_outputs=STATISTICAL_VISUAL_OUTPUT_TYPES,
                    default_outputs=["chart", "image_spec", "report_section"],
                    binding_roles=[role],
                    compatibility_alias_ids=compatibility_alias_ids,
                    output_modes=STATISTICAL_VISUAL_OUTPUT_TYPES,
                    granularity_modes=[role, "single_field", "field_pair", "field_set", "grouped", "time_window", "entity_level", "full_dataset"],
                    analysis_kind="statistical_visual",
                    render_profile={
                        "visual_domain_id": domain_id,
                        "visual_pattern_id": pattern_id,
                        "chart_pattern": pattern_id,
                        "style_reference": "statistical_report",
                        "non_financial": True,
                    },
                    report_profile={
                        "report_voice": "statistical_interpretation",
                        "caption_required": True,
                        "interpretation_required": True,
                        "avoid_financial_framing": True,
                    },
                ),
            }
        )
    return registry


def _expand_statistical_method_variants(method: dict[str, Any]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    method_id = str(method.get("id") or "").strip()
    if not method_id:
        return expanded
    family = str(method.get("family") or "statistical")
    bundle_title = str(method.get("name") or method_id.replace("_", " ").title())
    stable_outputs = _catalog_output_variants_for_method(method)
    default_outputs = VISUAL_DEFAULT_OUTPUT_TYPES if _method_supports_visual_outputs(method) else TEXTUAL_DEFAULT_OUTPUT_TYPES
    for variant in _catalog_output_variants_for_method(method):
        expanded.append(
            {
                **method,
                "id": f"{method_id}_{variant}",
                "output_types": [variant],
                "catalog_output_variant": variant,
                "base_method_id": method_id,
                "bundle_id": method_id,
                "bundle_title": bundle_title,
                **_runtime_capability_metadata(
                    stable_outputs=stable_outputs,
                    default_outputs=[item for item in default_outputs if item in stable_outputs],
                    binding_roles=_string_list(method.get("required_roles")),
                ),
            }
        )
    return expanded


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _has_cjk(value: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in str(value or ""))


def _compact_goal_label(goal: str) -> str:
    text = str(goal or "").strip().strip(" .,:;，。：；")
    if not _has_cjk(text):
        return ""
    prefixes = [
        _zh(r"\u7528\u4e8e"),
        _zh(r"\u63cf\u8ff0"),
        _zh(r"\u751f\u6210"),
        _zh(r"\u5206\u6790"),
        _zh(r"\u68c0\u9a8c"),
        _zh(r"\u68c0\u6d4b"),
        _zh(r"\u4f30\u8ba1"),
        _zh(r"\u8bc4\u4f30"),
        _zh(r"\u6bd4\u8f83"),
        _zh(r"\u8bc6\u522b"),
        _zh(r"\u5c55\u793a"),
        _zh(r"\u8861\u91cf"),
        _zh(r"\u5efa\u6a21"),
        _zh(r"\u9884\u6d4b"),
        _zh(r"\u5224\u65ad"),
        _zh(r"\u8ba1\u7b97"),
        _zh(r"\u7ed8\u5236"),
        _zh(r"\u6267\u884c"),
        _zh(r"\u8fdb\u884c"),
    ]
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if text.startswith(prefix) and len(text) > len(prefix) + 1:
                text = text[len(prefix) :].strip(" .,:;，。：；")
                changed = True
                break
    return text


def _learned_method_path() -> Path:
    configured = os.getenv("ASTERIA_AUTO_ANALYSIS_LEARNED_METHODS_PATH", "").strip()
    if configured:
        return Path(configured)
    specs = load_auto_analysis_specs()
    configured_from_specs = str(specs.get("learned_methods_path") or "").strip()
    if configured_from_specs:
        path = Path(configured_from_specs)
        return path if path.is_absolute() else DEFAULT_SPEC_PATH.parent / path
    return DEFAULT_LEARNED_METHOD_PATH


def load_learned_methods() -> list[dict[str, Any]]:
    learned_path = _learned_method_path()
    if not learned_path.exists():
        return []
    try:
        payload = json.loads(learned_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(payload, dict):
        candidates = payload.get("methods") or payload.get("items") or []
    elif isinstance(payload, list):
        candidates = payload
    else:
        candidates = []
    methods: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        method_id = str(item.get("id") or "").strip()
        if not method_id:
            continue
        methods.append(
            {
                "id": method_id,
                "name": str(item.get("name") or method_id.replace("_", " ").title()),
                "family": str(item.get("family") or "learned"),
                "goal": str(item.get("goal") or item.get("description") or ""),
                "status": str(item.get("status") or "learned"),
                "output_types": _string_list(item.get("output_types") or item.get("outputs")) or ["text", "table", "data"],
                "required_roles": _string_list(item.get("required_roles") or item.get("variable_types") or item.get("roles")),
                "source": "learned_methods",
                "learned_from": str(item.get("learned_from") or item.get("source") or learned_path.name),
                "tags": _string_list(item.get("tags")),
                "field_bindings": dict(item.get("field_bindings") or {}),
                "selection_mode": str(item.get("selection_mode") or ""),
                "object_selection": dict(item.get("object_selection") or {}),
                "statistical_options": dict(item.get("statistical_options") or {}),
                "report_value_hooks": _string_list(item.get("report_value_hooks")),
                "usage_guidance": list(item.get("usage_guidance") or []),
                "base_method_id": str(item.get("base_method_id") or ""),
                "bundle_id": str(item.get("bundle_id") or item.get("id") or ""),
                "bundle_title": str(item.get("bundle_title") or item.get("name") or ""),
            }
        )
    return methods


def _safe_method_id_segment(value: Any, fallback: str = "custom") -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9_\-\u4e00-\u9fff]+", "_", text, flags=re.UNICODE)
    text = re.sub(r"_+", "_", text).strip("_-")
    return text[:80] or fallback


def _read_learned_method_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"methods": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"methods": []}
    if isinstance(payload, dict):
        methods = payload.get("methods") or payload.get("items") or []
        return {**payload, "methods": methods if isinstance(methods, list) else []}
    if isinstance(payload, list):
        return {"methods": payload}
    return {"methods": []}


def save_lab_method_card(payload: Any) -> dict[str, Any]:
    source_method = dict(getattr(payload, "source_method", {}) or {})
    base_method_id = str(getattr(payload, "base_method_id", "") or source_method.get("id") or "").strip()
    display_name = str(getattr(payload, "name", "") or source_method.get("name_zh") or source_method.get("name") or base_method_id or "Custom Lab Method").strip()
    family = str(getattr(payload, "family", "") or source_method.get("family") or "learned").strip() or "learned"
    output_types = _string_list(getattr(payload, "output_types", None) or source_method.get("output_types")) or ["text", "table", "data"]
    required_roles = _string_list(getattr(payload, "required_roles", None) or source_method.get("required_roles"))
    field_bindings = dict(getattr(payload, "field_bindings", {}) or {})
    selection_mode = str(getattr(payload, "selection_mode", "") or "fields").strip() or "fields"
    statistical_options = dict(getattr(payload, "statistical_options", {}) or {})
    learned_path = _learned_method_path()
    learned_path.parent.mkdir(parents=True, exist_ok=True)
    stored = _read_learned_method_payload(learned_path)
    methods = [item for item in list(stored.get("methods") or []) if isinstance(item, dict)]
    custom_id = f"learned_{_safe_method_id_segment(base_method_id or display_name)}_{_safe_method_id_segment(selection_mode)}"
    if field_bindings:
        custom_id = f"{custom_id}_{_safe_method_id_segment('_'.join(sorted(field_bindings.keys())), 'bindings')}"
    method_record = {
        "id": custom_id,
        "name": display_name,
        "family": family,
        "goal": str(getattr(payload, "description", "") or source_method.get("goal_zh") or source_method.get("goal") or ""),
        "description": str(getattr(payload, "description", "") or ""),
        "status": "learned",
        "output_types": output_types,
        "required_roles": required_roles,
        "source": "lab_method_card_editor",
        "learned_from": base_method_id or source_method.get("id") or "lab_method_card_editor",
        "base_method_id": base_method_id,
        "bundle_id": custom_id,
        "bundle_title": display_name,
        "field_bindings": field_bindings,
        "selection_mode": selection_mode,
        "object_selection": dict(getattr(payload, "object_selection", {}) or {}),
        "statistical_options": statistical_options,
        "report_value_hooks": _string_list(getattr(payload, "report_value_hooks", None)),
        "usage_guidance": list(getattr(payload, "usage_guidance", []) or []),
        "tags": list(dict.fromkeys([*_string_list(getattr(payload, "tags", None)), "lab_saved_method_card", family])),
    }
    remaining = [item for item in methods if str(item.get("id") or "") != custom_id]
    stored["methods"] = [*remaining, method_record]
    learned_path.write_text(json.dumps(stored, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {
        "status": "saved",
        "method": method_record,
        "learned_method_path": str(learned_path),
        "method_count": len(stored["methods"]),
    }


def _dedupe_methods(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    ordered_ids: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for item in registry:
        method_id = str(item.get("id") or "").strip()
        if not method_id:
            continue
        if method_id not in seen:
            seen.add(method_id)
            ordered_ids.append(method_id)
            by_id[method_id] = item
            continue
        if item.get("source") == "learned_methods":
            by_id[method_id] = {**by_id[method_id], **item}
    return [by_id[method_id] for method_id in ordered_ids]


def _method_bundle_id(method: dict[str, Any]) -> str:
    configured = str(method.get("bundle_id") or method.get("base_method_id") or "").strip()
    if configured:
        return configured
    variant = str(method.get("catalog_output_variant") or "").strip()
    method_id = str(method.get("id") or "").strip()
    if variant and method_id.endswith(f"_{variant}"):
        return method_id[: -(len(variant) + 1)]
    return method_id


def _method_bundle_title(method: dict[str, Any]) -> str:
    configured = str(method.get("bundle_title_zh") or method.get("parent_method_title") or "").strip()
    if configured:
        return configured
    return _method_concept_label(method)


def _method_alias_ids(method: dict[str, Any]) -> list[str]:
    aliases = _string_list(method.get("compatibility_alias_ids"))
    method_id = str(method.get("id") or "").strip()
    if method_id == "descriptive_profile":
        aliases.extend(["descriptive_profile_single_field_text", "descriptive_profile_single_field_text_text"])
    elif method_id == "descriptive_profile_single_field_text":
        aliases.append("descriptive_profile_single_field_text_text")
    return list(dict.fromkeys(alias for alias in aliases if alias and alias != method_id))


def method_alias_map(registry: list[dict[str, Any]] | None = None) -> dict[str, str]:
    source = registry if registry is not None else get_auto_analysis_method_registry()
    aliases: dict[str, str] = {}
    for method in source:
        method_id = str(method.get("id") or "").strip()
        if not method_id:
            continue
        aliases.setdefault(method_id, method_id)
        for alias in _method_alias_ids(method):
            aliases.setdefault(alias, method_id)
    return aliases


def canonical_method_ids(method_ids: list[str] | set[str] | tuple[str, ...], registry: list[dict[str, Any]] | None = None) -> list[str]:
    aliases = method_alias_map(registry)
    canonical: list[str] = []
    seen: set[str] = set()
    for method_id in method_ids:
        value = str(method_id or "").strip()
        if not value:
            continue
        resolved = aliases.get(value, value)
        if resolved in seen:
            continue
        seen.add(resolved)
        canonical.append(resolved)
    return canonical


def get_auto_analysis_method_registry() -> list[dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    for item in get_statistical_catalog():
        base_method = {
            "id": str(item.get("id") or ""),
            "name": str(item.get("name") or ""),
            "family": str(item.get("family") or "statistical"),
            "goal": str(item.get("goal") or ""),
            "status": "live" if str(item.get("status") or "") == "live" else "catalog",
            "output_types": ["text", "table", "data"],
            "required_roles": list(item.get("variable_types") or []),
            "source": "statistical_catalog",
            "bundle_id": str(item.get("id") or ""),
            "bundle_title": str(item.get("name") or item.get("id") or ""),
            "bundle_title_en": str(item.get("name") or item.get("id") or ""),
        }
        registry.extend(_expand_statistical_method_variants(base_method))
    registry.extend(_generated_method_registry(load_auto_analysis_specs()))
    registry.extend(_generated_statistical_visual_registry())
    registry.extend(load_learned_methods())
    return _dedupe_methods(registry)


def summarize_method_registry(registry: list[dict[str, Any]]) -> dict[str, Any]:
    families = sorted({str(item.get("family") or "") for item in registry if str(item.get("family") or "").strip()})
    sources: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for item in registry:
        source = str(item.get("source") or "unknown")
        status = str(item.get("status") or "unknown")
        sources[source] = sources.get(source, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "total_methods": len(registry),
        "live_or_catalog_methods": sum(1 for item in registry if item.get("status") in {"live", "catalog"}),
        "planned_methods": sum(1 for item in registry if item.get("status") == "planned"),
        "learned_methods": sources.get("learned_methods", 0),
        "families": families,
        "sources": dict(sorted(sources.items())),
        "statuses": dict(sorted(statuses.items())),
        "learned_method_path": str(_learned_method_path()),
    }


def _label(mapping: dict[str, str], value: str) -> str:
    return mapping.get(value, value.replace("_", " "))


def _method_token_label(method: dict[str, Any]) -> str:
    method_id = _method_bundle_id(method) or str(method.get("id") or "")
    parts = [part for part in method_id.split("_") if part]
    for size in range(len(parts), 0, -1):
        for index in range(len(parts) - size + 1):
            token = "_".join(parts[index : index + size])
            if token in METHOD_LABELS:
                return METHOD_LABELS[token]
    return ""


def _method_goal_label(method: dict[str, Any]) -> str:
    configured = str(method.get("method_concept_label") or method.get("name_zh") or "").strip()
    if _has_cjk(configured):
        return configured
    if str(method.get("source") or "") == "statistical_catalog":
        return ""
    return _compact_goal_label(str(method.get("goal") or ""))


def _method_name_zh(method: dict[str, Any]) -> str:
    method_id = str(method.get("id") or "")
    family = str(method.get("family") or "")
    family_label = _label(FAMILY_LABELS, family)
    separator = _zh(r"\u30fb")
    method_label = _method_concept_label(method)
    role_labels = [_label(ROLE_LABELS, item) for item in _string_list(method.get("required_roles"))[:1]]
    output_labels = [_label(OUTPUT_LABELS, item) for item in _string_list(method.get("output_types"))[:1]]
    suffix = separator.join([*role_labels, *output_labels])
    suffix_text = f"{separator}{suffix}" if suffix else ""
    return f"{family_label}{separator}{method_label or str(method.get('name') or method_id)}{suffix_text}"


def _method_concept_label(method: dict[str, Any]) -> str:
    if str(method.get("source") or "") == "statistical_catalog":
        method_name = str(method.get("name") or "").strip()
        if method_name:
            return method_name
    goal_label = _method_goal_label(method)
    if goal_label:
        return goal_label
    token_label = _method_token_label(method)
    if token_label:
        return token_label
    method_id = _method_bundle_id(method) or str(method.get("id") or "")
    return str(method.get("name") or method_id).replace("_", " ")


def _source_label(source: str) -> str:
    if source == "statistical_catalog":
        return _zh(r"\u7edf\u8ba1\u76ee\u5f55")
    if source == "statistical_visual_catalog":
        return _zh(r"\u975e\u91d1\u878d\u7edf\u8ba1\u53ef\u89c6\u5316\u76ee\u5f55")
    if source == "auto_analysis_specs":
        return _zh(r"\u81ea\u52a8\u751f\u6210\u76ee\u5f55")
    if source == "learned_methods":
        return _zh(r"\u5df2\u5b66\u4e60\u65b9\u6cd5")
    return source or _zh(r"\u76ee\u5f55\u65b9\u6cd5")


def _status_label(status: str) -> str:
    if status == "live":
        return _zh(r"\u53ef\u76f4\u63a5\u8fd0\u884c")
    if status == "catalog":
        return _zh(r"\u76ee\u5f55\u53ef\u9009")
    if status == "planned":
        return _zh(r"\u89c4\u5212\u53ef\u7f16\u6392")
    return status or _zh(r"\u53ef\u7f16\u6392")


def _method_goal_zh(family: str, outputs: list[str], concept_label: str) -> str:
    family_label = _label(FAMILY_LABELS, family)
    output_text = "\u3001".join(_label(OUTPUT_LABELS, item) for item in outputs) or _zh(r"\u7ed3\u6784\u5316\u7ed3\u679c")
    concept = concept_label or family_label
    return _zh(r"\u7528\u4e8e") + f"{concept}" + _zh(r"\uff0c\u8f93\u51fa") + output_text


def _recommended_selection_mode(family: str, outputs: list[str], roles: list[str]) -> str:
    role_set = set(roles)
    output_set = set(outputs)
    if "entity_level" in role_set:
        return "object"
    if "full_dataset" in role_set and not (family == "visual" or {"chart", "image_spec"} & output_set):
        return "all_rows"
    return "fields"


def _binding_controls_for_method(family: str, outputs: list[str], roles: list[str]) -> list[str]:
    role_set = set(roles)
    output_set = set(outputs)
    if "entity_level" in role_set:
        return ["object_selection", "group", "label", "derived_metrics"]
    if "full_dataset" in role_set and not (family == "visual" or {"chart", "image_spec"} & output_set):
        return ["dataset_scope", "derived_metrics"]
    controls: list[str] = []
    if family == "visual" or {"chart", "image_spec"} & output_set:
        controls.extend(["x", "y", "group", "label"])
    elif family == "categorical_association" and "strata" in role_set:
        controls.extend(["target", "group", "features"])
    elif family == "categorical_association" and {"paired", "within_subject_factor"} & role_set:
        controls.extend(["target", "features"])
    elif "within_subject_factor" in role_set:
        controls.extend(["target", "features"])
    elif family == "association" and "covariate" in role_set:
        controls.extend(["target", "features"])
    elif family == "association" and "numeric" in role_set:
        controls.extend(["target", "features", "group"])
    elif family == "mean_tests" and {"categorical", "numeric"} <= role_set:
        controls.extend(["target", "group", "features"])
    elif family == "mean_tests" and "categorical" in role_set:
        controls.extend(["target", "group", "features"])
    elif "field_pair" in role_set or family in {"association", "categorical_association", "comparison", "causal", "causal_panel"}:
        controls.extend(["x", "y", "group"])
    elif "field_set" in role_set or family in {"regression", "regression_glm", "machine_learning", "multivariate"}:
        controls.extend(["target", "features", "group"])
    elif family == "nonparametric" and ({"categorical", "binary_group"} & role_set):
        controls.extend(["target", "group"])
    elif "single_field" in role_set:
        controls.append("target")
    else:
        controls.extend(["target", "features"])
    if "time_window" in role_set or "ordered" in role_set or family == "time_series":
        controls.append("time")
    if "derived_metric" in role_set or family in {"causal", "causal_panel", "time_series"}:
        controls.append("derived_metrics")
    return list(dict.fromkeys(controls))


def _selection_mode_label(mode: str) -> str:
    return {
        "fields": _zh(r"\u5b57\u6bb5\u7ed1\u5b9a"),
        "all_rows": _zh(r"\u5168\u8868\u8fd0\u884c"),
        "object": _zh(r"\u91cd\u70b9\u5bf9\u8c61"),
    }.get(mode, mode)


def _control_label(control: str) -> str:
    return {
        "target": _zh(r"\u76ee\u6807\u6307\u6807"),
        "field": _zh(r"\u5355\u5b57\u6bb5"),
        "features": _zh(r"\u7279\u5f81\u5b57\u6bb5"),
        "x": "X",
        "y": "Y",
        "group": _zh(r"\u5206\u7ec4\u5b57\u6bb5"),
        "label": _zh(r"\u6807\u7b7e\u5b57\u6bb5"),
        "entity": _zh(r"\u5bf9\u8c61\u5b57\u6bb5"),
        "time": _zh(r"\u65f6\u95f4\u5b57\u6bb5"),
        "derived_metrics": _zh(r"\u6d3e\u751f\u6307\u6807"),
        "dataset_scope": _zh(r"\u6570\u636e\u8303\u56f4"),
        "object_selection": _zh(r"\u5bf9\u8c61\u9009\u62e9"),
    }.get(control, control)


def _method_card_edit_capabilities(*, family: str, outputs: list[str], roles: list[str], selection_mode: str) -> dict[str, Any]:
    controls = _binding_controls_for_method(family, outputs, roles)
    selection_modes = ["fields", "all_rows", "object"]
    output_set = set(outputs)
    freedom_score = 45 + min(30, len(controls) * 5) + min(15, len(output_set) * 3)
    if "derived_metrics" in controls:
        freedom_score += 5
    if "object_selection" in controls or "entity_level" in set(roles):
        freedom_score += 5
    return {
        "editable_fields": controls,
        "editable_field_labels": [_control_label(item) for item in controls],
        "selection_modes": selection_modes,
        "selection_mode_labels": [
            {
                "mode": mode,
                "label": _selection_mode_label(mode),
                "recommended": mode == selection_mode,
            }
            for mode in selection_modes
        ],
        "run_controls": [
            "append_run",
            "single_run",
            "batch_merge",
            "smart_field_match",
            "reset_binding",
        ],
        "run_control_labels": [
            _zh(r"\u8ffd\u52a0\u8fd0\u884c\u5b9e\u4f8b"),
            _zh(r"\u5355\u72ec\u6267\u884c"),
            _zh(r"\u6279\u91cf\u5408\u5e76"),
            _zh(r"\u667a\u80fd\u5339\u914d\u5b57\u6bb5"),
            _zh(r"\u56de\u5230\u9ed8\u8ba4\u7ed1\u5b9a"),
        ],
        "freedom_score": min(100, freedom_score),
    }


def _method_identity(method: dict[str, Any], *, concept: str, outputs: list[str], roles: list[str]) -> dict[str, str]:
    method_id = str(method.get("id") or "").strip()
    bundle_title = str(method.get("bundle_title_zh") or method.get("bundle_title") or method.get("parent_method_title") or concept or method_id).strip()
    variant = str(method.get("catalog_output_variant") or (outputs[0] if outputs else "")).strip()
    output_label = _label(OUTPUT_LABELS, variant or (outputs[0] if outputs else ""))
    role_labels = [_label(ROLE_LABELS, item) for item in roles]
    role_text = _zh(r"\u3001").join(role_labels) or _zh(r"\u5f53\u524d\u6570\u636e")
    output_labels = [_label(OUTPUT_LABELS, item) for item in outputs]
    output_text = _zh(r"\u3001").join(output_labels) or output_label or _zh(r"\u7ed3\u6784\u5316\u7ed3\u679c")
    separator = _zh(r"\u30fb")
    submethod_title = separator.join(item for item in [bundle_title, role_text, output_label] if item)
    goal = str(method.get("goal") or "").strip()
    if not goal:
        goal = f"{concept} / {role_text} / {output_label}"
    return {
        "method_id": method_id,
        "bundle_title": bundle_title,
        "submethod_title": submethod_title,
        "variant": variant,
        "output_label": output_label,
        "output_text": output_text,
        "role_text": role_text,
        "goal": goal,
    }


def _method_output_usage_sentence(identity: dict[str, str]) -> str:
    output_label = identity["output_label"]
    title = identity["submethod_title"] or identity["bundle_title"]
    if output_label == _zh(r"\u6587\u5b57\u89e3\u8bfb"):
        return f"{title} \u7528\u6765\u628a\u65b9\u6cd5\u7ed3\u679c\u7ffb\u6210\u5c0f\u767d\u80fd\u8bfb\u61c2\u7684\u6587\u5b57\uff0c\u91cd\u70b9\u8bf4\u660e\u65b9\u5411\u3001\u5dee\u5f02\u3001\u5f02\u5e38\u6216\u7ba1\u7406\u542b\u4e49\u3002"
    if output_label == _zh(r"\u8868\u683c"):
        return f"{title} \u7528\u6765\u628a\u7ed3\u679c\u6574\u7406\u6210\u53ef\u5bf9\u8d26\u7684\u8868\u683c\uff0c\u9002\u5408\u68c0\u67e5\u6837\u672c\u91cf\u3001\u5206\u7ec4\u3001\u6307\u6807\u548c\u4e2d\u95f4\u8bc1\u636e\u3002"
    if output_label == _zh(r"\u7ed3\u6784\u5316\u6570\u636e"):
        return f"{title} \u7528\u6765\u4ea7\u751f\u53ef\u590d\u7528\u7684\u7ed3\u6784\u5316\u6570\u636e\uff0c\u65b9\u4fbf\u540e\u7eed\u5408\u5e76\u3001\u4e0b\u8f7d\u3001\u4e8c\u6b21\u7ed8\u56fe\u6216\u5199\u5165\u62a5\u544a\u8bc1\u636e\u94fe\u3002"
    if output_label == _zh(r"\u56fe\u8868"):
        return f"{title} \u7528\u6765\u751f\u6210\u53ef\u89c6\u5316\u56fe\u8868\uff0c\u8ba9\u8d8b\u52bf\u3001\u5206\u5e03\u3001\u5206\u7ec4\u5dee\u5f02\u6216\u5f02\u5e38\u70b9\u4e00\u773c\u53ef\u89c1\u3002"
    if output_label == _zh(r"\u56fe\u7247\u89c4\u683c"):
        return f"{title} \u7528\u6765\u751f\u6210\u56fe\u7247\u89c4\u683c\uff0c\u8bf4\u6e05\u56fe\u5f62\u7c7b\u578b\u3001\u5b57\u6bb5\u7ed1\u5b9a\u548c\u6807\u6ce8\u8981\u6c42\uff0c\u4fbf\u4e8e\u540e\u7eed\u6e32\u67d3\u4e3a\u56fe\u3002"
    if output_label == _zh(r"\u62a5\u544a\u6bb5\u843d"):
        return f"{title} \u7528\u6765\u76f4\u63a5\u5199\u51fa\u62a5\u544a\u6bb5\u843d\uff0c\u628a\u65b9\u6cd5\u80cc\u666f\u3001\u7ed3\u679c\u3001\u9650\u5236\u548c\u884c\u52a8\u542b\u4e49\u8fde\u6210\u4e00\u6bb5\u53ef\u4ea4\u4ed8\u6587\u5b57\u3002"
    return f"{title} \u7528\u6765\u4ea7\u751f {output_label or identity['output_text']}\uff0c\u8bf7\u6309\u8fd9\u5f20\u5361\u7684\u5b57\u6bb5\u548c\u53e3\u5f84\u89e3\u8bfb\u3002"


def _method_role_usage_sentence(identity: dict[str, str], *, roles: list[str], selection_mode: str) -> str:
    title = identity["submethod_title"] or identity["bundle_title"]
    role_text = identity["role_text"]
    role_set = set(roles)
    if "time_window" in role_set or "time" in role_set:
        return f"{title} \u9700\u8981\u5148\u786e\u8ba4\u65f6\u95f4\u5b57\u6bb5\u548c\u65f6\u95f4\u7a97\u53e3\uff0c\u518d\u89e3\u91ca\u8d8b\u52bf\u3001\u5b63\u8282\u6027\u3001\u6ede\u540e\u6216\u62d0\u70b9\u3002"
    if "entity_level" in role_set:
        return f"{title} \u9700\u8981\u5148\u9009\u5bf9\u8c61\u5b57\u6bb5\u548c\u5bf9\u8c61\u503c\uff0c\u4f8b\u5982\u5ba2\u6237\u3001\u95e8\u5e97\u3001SKU \u6216\u533a\u57df\uff0c\u518d\u6bd4\u8f83\u8fd9\u4e9b\u5bf9\u8c61\u7684\u8868\u73b0\u3002"
    if "full_dataset" in role_set:
        return f"{title} \u4f7f\u7528\u5168\u8868\u6570\u636e\uff0c\u4e0d\u4f9d\u8d56\u5355\u4e2a\u5b57\u6bb5\uff0c\u9002\u5408\u505a\u603b\u89c8\u3001\u9644\u5f55\u3001\u8bc1\u636e\u7d22\u5f15\u6216\u62a5\u544a\u7ec4\u4ef6\u3002"
    if "derived_metric" in role_set:
        return f"{title} \u4f1a\u4f7f\u7528\u6d3e\u751f\u6307\u6807\uff0c\u8bf7\u5148\u786e\u8ba4\u6307\u6807\u516c\u5f0f\u548c\u4e1a\u52a1\u53e3\u5f84\uff0c\u518d\u89e3\u8bfb\u7ed3\u679c\u3002"
    if selection_mode == "object":
        return f"{title} \u5efa\u8bae\u7528\u5bf9\u8c61\u6a21\u5f0f\u8fd0\u884c\uff0c\u5148\u9009\u5bf9\u8c61\u548c\u5206\u7ec4\uff0c\u518d\u8ba9\u7ec4\u5185\u5b50\u65b9\u6cd5\u5171\u4eab\u540c\u4e00\u53e3\u5f84\u3002"
    return f"{title} \u9700\u8981\u914d\u7f6e {role_text}\uff0c\u5b57\u6bb5\u4e0d\u786e\u5b9a\u65f6\u5148\u7528\u667a\u80fd\u63a8\u8350\uff0c\u518d\u6309\u4e1a\u52a1\u53e3\u5f84\u5fae\u8c03\u3002"


def _method_family_reading_sentence(*, family: str, identity: dict[str, str]) -> str:
    title = identity["submethod_title"] or identity["bundle_title"]
    if family in {"association", "categorical_association"}:
        return f"\u8bfb {title} \u65f6\uff0c\u5148\u770b\u5173\u8054\u5f3a\u5f31\u548c\u65b9\u5411\uff0c\u518d\u8bf4\u660e\u5b83\u53ea\u662f\u5173\u8054\u8bc1\u636e\uff0c\u4e0d\u80fd\u5355\u72ec\u8bc1\u660e\u56e0\u679c\u3002"
    if family in {"comparison", "mean_tests", "nonparametric"}:
        return f"\u8bfb {title} \u65f6\uff0c\u5148\u770b\u7ec4\u95f4\u5dee\u5f02\u548c\u6837\u672c\u91cf\uff0c\u518d\u770b\u663e\u8457\u6027\u6216\u6548\u5e94\u91cf\uff0c\u6700\u540e\u5224\u65ad\u5dee\u5f02\u662f\u5426\u6709\u4e1a\u52a1\u4ef7\u503c\u3002"
    if family in {"regression", "regression_glm"}:
        return f"\u8bfb {title} \u65f6\uff0c\u5148\u770b\u76ee\u6807\u548c\u7279\u5f81\u662f\u5426\u9009\u5bf9\uff0c\u518d\u770b\u7cfb\u6570\u65b9\u5411\u3001\u663e\u8457\u6027\u3001\u62df\u5408\u5ea6\u548c\u6b8b\u5dee\u98ce\u9669\u3002"
    if family == "machine_learning":
        return f"\u8bfb {title} \u65f6\uff0c\u5148\u770b\u9a8c\u8bc1\u8868\u73b0\uff0c\u518d\u770b\u7279\u5f81\u91cd\u8981\u6027\u6216\u5206\u7fa4\u662f\u5426\u80fd\u88ab\u4e1a\u52a1\u547d\u540d\u3002"
    if family == "time_series":
        return f"\u8bfb {title} \u65f6\uff0c\u5148\u770b\u65f6\u95f4\u7c92\u5ea6\u662f\u5426\u4e00\u81f4\uff0c\u518d\u770b\u8d8b\u52bf\u3001\u5468\u671f\u3001\u5f02\u5e38\u70b9\u548c\u9884\u6d4b\u533a\u95f4\u3002"
    if family == "visual":
        return f"\u8bfb {title} \u65f6\uff0c\u5148\u68c0\u67e5\u5750\u6807\u8f74\u3001\u5206\u7ec4\u548c\u6807\u7b7e\u662f\u5426\u6b63\u786e\uff0c\u518d\u628a\u56fe\u4e0a\u6a21\u5f0f\u8f6c\u6210\u53ef\u9a8c\u8bc1\u7684\u7edf\u8ba1\u95ee\u9898\u3002"
    if family == "report_part":
        return f"\u8bfb {title} \u65f6\uff0c\u8981\u786e\u8ba4\u5b83\u5199\u7684\u662f\u62a5\u544a\u7ec4\u4ef6\uff0c\u5fc5\u987b\u5f15\u7528\u65b9\u6cd5\u8bc1\u636e\u3001\u8868\u683c\u548c\u56fe\u8868\uff0c\u4e0d\u80fd\u7a7a\u5199\u7ed3\u8bba\u3002"
    return f"\u8bfb {title} \u65f6\uff0c\u5148\u770b\u8fd9\u5f20\u5361\u7684\u8f93\u51fa\u662f {identity['output_text']}\uff0c\u518d\u6838\u5bf9\u5b57\u6bb5\u53e3\u5f84\u3001\u6837\u672c\u91cf\u548c\u7ed3\u8bba\u8fb9\u754c\u3002"


def _method_usage_guidance(*, method: dict[str, Any], family: str, concept: str, outputs: list[str], roles: list[str], selection_mode: str) -> list[dict[str, str]]:
    identity = _method_identity(method, concept=concept, outputs=outputs, roles=roles)
    title = identity["submethod_title"] or identity["bundle_title"]
    output_text = _zh(r"\u3001").join(_label(OUTPUT_LABELS, item) for item in outputs) or _zh(r"\u7ed3\u6784\u5316\u7ed3\u679c")
    role_text = _zh(r"\u3001").join(_label(ROLE_LABELS, item) for item in roles) or _zh(r"\u5f53\u524d\u6570\u636e")
    rows = [
        {
            "title": _zh(r"\u8fd9\u5f20\u5361\u4f55\u65f6\u7528"),
            "detail": f"{title} \u662f\u72ec\u7acb\u65b9\u6cd5\u5361\uff08id: {identity['method_id']}\uff09\uff0c\u7528\u6765\u56de\u7b54\u300c{identity['goal']}\u300d\uff1b{_method_output_usage_sentence(identity)}",
        },
        {
            "title": _zh(r"\u5b57\u6bb5\u600e\u4e48\u9009"),
            "detail": _method_role_usage_sentence(identity, roles=roles, selection_mode=selection_mode),
        },
        {
            "title": _zh(r"\u8bfb\u7ed3\u679c\u5148\u770b"),
            "detail": _method_family_reading_sentence(family=family, identity=identity) + _zh(r"\u63a8\u8350\u8fd0\u884c\u6a21\u5f0f\uff1a") + _selection_mode_label(selection_mode) + _zh(r"\uff1b\u672c\u5361\u8f93\u51fa\uff1a") + output_text + _zh(r"\u3002"),
        },
    ]
    if family in {"regression", "regression_glm", "machine_learning", "multivariate"}:
        rows.append(
            {
                "title": _zh(r"\u7ed3\u8bba\u8fb9\u754c"),
                "detail": _zh(r"\u5efa\u6a21\u7c7b\u65b9\u6cd5\u9700\u4fdd\u7559\u76ee\u6807\u3001\u7279\u5f81\u548c\u5206\u7ec4\u53e3\u5f84\uff0c\u907f\u514d\u628a\u76f8\u5173\u5f53\u6210\u56e0\u679c\u3002"),
            }
        )
    elif family in {"association", "categorical_association", "comparison"}:
        rows.append(
            {
                "title": _zh(r"\u89e3\u91ca\u8def\u5f84"),
                "detail": _zh(r"\u5148\u770b\u5dee\u5f02\u6216\u5173\u8054\u662f\u5426\u7a33\u5b9a\uff0c\u518d\u628a\u4e1a\u52a1\u5f71\u54cd\u5199\u6210\u53ef\u6267\u884c\u884c\u52a8\u3002"),
            }
        )
    elif family == "time_series":
        rows.append(
            {
                "title": _zh(r"\u65f6\u95f4\u53e3\u5f84"),
                "detail": _zh(r"\u4f18\u5148\u7ed1\u5b9a\u65f6\u95f4\u5b57\u6bb5\u548c\u76ee\u6807\u6307\u6807\uff0c\u518d\u5224\u65ad\u8d8b\u52bf\u3001\u5b63\u8282\u6027\u548c\u5f02\u5e38\u62d0\u70b9\u3002"),
            }
        )
    elif family == "visual" or {"chart", "image_spec"} & set(outputs):
        rows.append(
            {
                "title": _zh(r"\u56fe\u8868\u7528\u6cd5"),
                "detail": _zh(r"\u8bf7\u628a x/y\u3001\u5206\u7ec4\u548c\u6807\u7b7e\u5b57\u6bb5\u8bbe\u6e05\u695a\uff0c\u8ba9\u56fe\u50cf\u80fd\u76f4\u63a5\u652f\u6491\u62a5\u544a\u7ed3\u8bba\u3002"),
            }
        )
    return rows


def _method_report_value_hooks(*, family: str, outputs: list[str], roles: list[str]) -> list[str]:
    hooks = [
        _zh(r"\u628a\u65b9\u6cd5\u5361\u7ed1\u5b9a\u3001\u8fd0\u884c\u5b9e\u4f8b\u548c\u8bc1\u636e\u5f15\u7528\u4e32\u8d77\u6765\uff0c\u8ba9\u62a5\u544a\u7ed3\u8bba\u53ef\u8ffd\u6eaf\u3002"),
        _zh(r"\u4f18\u5148\u4f7f\u7528\u80fd\u4ea7\u751f\u56fe\u3001CSV/Excel \u548c\u89e3\u8bfb\u7684\u65b9\u6cd5\uff0c\u63d0\u9ad8\u4ea4\u4ed8\u4ef7\u503c\u3002"),
    ]
    if "derived_metric" in roles:
        hooks.append(_zh(r"\u53ef\u628a\u6d3e\u751f\u6307\u6807\u89e3\u91ca\u4e3a\u7ba1\u7406\u53e3\u5f84\uff0c\u907f\u514d\u62a5\u544a\u53ea\u505c\u7559\u5728\u539f\u59cb\u5b57\u6bb5\u3002"))
    if family in {"regression", "regression_glm", "machine_learning", "multivariate"}:
        hooks.append(_zh(r"\u9002\u5408\u62bd\u53d6\u9a71\u52a8\u56e0\u7d20\u3001\u91cd\u8981\u6027\u6216\u5206\u7fa4\u7ed3\u6784\uff0c\u652f\u6491\u884c\u52a8\u4f18\u5148\u7ea7\u3002"))
    if family == "visual" or {"chart", "image_spec"} & set(outputs):
        hooks.append(_zh(r"\u56fe\u8868\u4ea7\u7269\u53ef\u76f4\u63a5\u8fdb\u5165\u56fe\u6587\u53d9\u4e8b\u548c\u5ba2\u6237\u4ea4\u4ed8\u6e05\u5355\u3002"))
    return hooks


def _method_card_sections(
    *,
    method: dict[str, Any],
    family: str,
    concept: str,
    outputs: list[str],
    roles: list[str],
    output_labels: list[str],
    role_labels: list[str],
) -> list[dict[str, str]]:
    identity = _method_identity(method, concept=concept, outputs=outputs, roles=roles)
    title = identity["submethod_title"] or identity["bundle_title"]
    output_text = _zh(r"\u3001").join(output_labels) or _zh(r"\u7ed3\u6784\u5316\u7ed3\u679c")
    role_text = _zh(r"\u3001").join(role_labels) or _zh(r"\u5f53\u524d\u6570\u636e")
    role_set = set(roles)
    output_set = set(outputs)
    identity_sections = [
        {
            "kind": "method_identity",
            "label": _zh(r"\u65b9\u6cd5\u5361\u8eab\u4efd"),
            "value": f"{title} / id: {identity['method_id']}",
            "help": f"\u8fd9\u662f\u4e00\u5f20\u72ec\u7acb\u65b9\u6cd5\u5361\uff0c\u4e0d\u4e0e\u540c\u7c7b\u65b9\u6cd5\u5171\u7528\u4ecb\u7ecd\uff1b\u5b83\u4e13\u95e8\u4ea7\u51fa {identity['output_label']}\u3002",
        },
        {
            "kind": "method_question",
            "label": _zh(r"\u5b83\u8981\u56de\u7b54\u4ec0\u4e48"),
            "value": identity["goal"],
            "help": f"\u7528\u8fd9\u5f20\u5361\u65f6\uff0c\u8bf7\u628a\u95ee\u9898\u6536\u675f\u5230\u300c{title}\u300d\u7684\u5b57\u6bb5\u3001\u8f93\u51fa\u548c\u7ed3\u8bba\u8fb9\u754c\u4e0a\u3002",
        },
    ]
    if "entity_level" in role_set:
        return [
            *identity_sections,
            {
                "kind": "object_selection",
                "label": _zh(r"\u91cd\u70b9\u5bf9\u8c61"),
                "value": f"{title} \u6309\u6807\u7b7e\u3001\u5206\u7ec4\u6216\u6837\u672c\u70b9\u9009\u5b9a\u5173\u952e\u5bf9\u8c61",
                "help": _zh(r"\u9002\u5408\u5148\u6311\u51fa\u9700\u8981\u8ffd\u8e2a\u7684\u5ba2\u6237\u3001\u95e8\u5e97\u3001SKU \u6216\u533a\u57df\uff0c\u518d\u6267\u884c\u65b9\u6cd5\u3002"),
            },
            {
                "kind": "merge_strategy",
                "label": _zh(r"\u5408\u5e76\u53e3\u5f84"),
                "value": _zh(r"\u652f\u6301\u667a\u80fd\u5408\u5e76\u548c\u624b\u52a8\u5408\u5e76"),
                "help": _zh(r"\u7528\u4e8e\u628a\u591a\u4e2a\u5bf9\u8c61\u7684\u7ed3\u679c\u6536\u655b\u5230\u540c\u4e00\u6279\u7ba1\u7406\u7ed3\u8bba\u3002"),
            },
            {
                "kind": "output",
                "label": _zh(r"\u4ea7\u51fa"),
                "value": f"{identity['output_label']} / {output_text}",
                "help": _zh(r"\u4ea7\u51fa\u4f1a\u4fdd\u7559\u5bf9\u8c61\u9009\u62e9\u548c\u8bc1\u636e\u6307\u9488\uff0c\u65b9\u4fbf\u540e\u7eed\u590d\u6838\u3002"),
            },
        ]
    if family == "visual" or {"chart", "image_spec"} & output_set:
        return [
            *identity_sections,
            {
                "kind": "visual_binding",
                "label": _zh(r"\u56fe\u5f62\u7ed1\u5b9a"),
                "value": f"{title} \u8981\u660e\u786e x/y\u3001\u5206\u7ec4\u548c\u6807\u7b7e\u5b57\u6bb5",
                "help": _zh(r"\u53ea\u6709\u53ef\u89c6\u5316\u65b9\u6cd5\u624d\u4f1a\u751f\u6210\u56fe\u8868\u6216\u56fe\u7247\u89c4\u683c\u3002"),
            },
            {
                "kind": "visual_reading",
                "label": _zh(r"\u770b\u56fe\u76ee\u6807"),
                "value": f"{concept} / {identity['output_label']} / {output_text}",
                "help": _zh(r"\u7528\u6765\u8bc6\u522b\u8d8b\u52bf\u3001\u5206\u5e03\u3001\u8c61\u9650\u3001\u5f02\u5e38\u6216\u7ed3\u6784\u5dee\u5f02\u3002"),
            },
        ]
    if "full_dataset" in role_set:
        return [
            *identity_sections,
            {
                "kind": "dataset_scope",
                "label": _zh(r"\u5206\u6790\u8303\u56f4"),
                "value": f"{title} \u4f7f\u7528\u5168\u8868\u8bb0\u5f55\u53c2\u4e0e",
                "help": _zh(r"\u9002\u5408\u505a\u603b\u89c8\u3001\u6458\u8981\u3001\u9644\u5f55\u6216\u5168\u5c40\u8bc1\u636e\u7d22\u5f15\u3002"),
            },
            {"kind": "output", "label": _zh(r"\u4ea7\u51fa"), "value": f"{identity['output_label']} / {output_text}", "help": _zh(r"\u4e0d\u4f9d\u8d56\u5355\u4e2a\u5b57\u6bb5\u7684\u5c40\u90e8\u89c6\u56fe\u3002")},
        ]
    if family == "time_series":
        return [
            *identity_sections,
            {"kind": "time_axis", "label": _zh(r"\u65f6\u95f4\u8f74"), "value": f"{title} \u9700\u7ed1\u5b9a\u65f6\u95f4\u548c\u76ee\u6807\u6307\u6807", "help": _zh(r"\u7528\u4e8e\u8bc6\u522b\u8d8b\u52bf\u3001\u6ede\u540e\u3001\u5b63\u8282\u6027\u6216\u62d0\u70b9\u3002")},
            {"kind": "output", "label": _zh(r"\u4ea7\u51fa"), "value": f"{identity['output_label']} / {output_text}", "help": _zh(r"\u4f1a\u8fde\u540c\u8d8b\u52bf\u8bc1\u636e\u548c\u98ce\u9669\u89e3\u8bfb\u4e00\u8d77\u8f93\u51fa\u3002")},
        ]
    if family in {"association", "categorical_association", "comparison"}:
        return [
            *identity_sections,
            {"kind": "relationship", "label": _zh(r"\u5173\u7cfb\u68c0\u67e5"), "value": f"{title} / {role_text}", "help": _zh(r"\u7528\u6765\u5224\u65ad\u5b57\u6bb5\u4e4b\u95f4\u662f\u5426\u6709\u7a33\u5b9a\u5173\u8054\u3001\u5dee\u5f02\u6216\u5206\u5c42\u4fe1\u53f7\u3002")},
            {"kind": "output", "label": _zh(r"\u4ea7\u51fa"), "value": f"{identity['output_label']} / {output_text}", "help": _zh(r"\u9002\u5408\u8fdb\u5165\u89e3\u91ca\u7ae0\u8282\u6216\u8bc1\u636e\u7d22\u5f15\u3002")},
        ]
    if family in {"regression", "regression_glm", "machine_learning", "multivariate"}:
        return [
            *identity_sections,
            {"kind": "model_binding", "label": _zh(r"\u5efa\u6a21\u7ed1\u5b9a"), "value": f"{title} \u9700\u533a\u5206\u76ee\u6807\u548c\u7279\u5f81", "help": _zh(r"\u7528\u4e8e\u4f30\u8ba1\u9a71\u52a8\u56e0\u7d20\u3001\u91cd\u8981\u6027\u6216\u5206\u7fa4\u7ed3\u6784\u3002")},
            {"kind": "output", "label": _zh(r"\u4ea7\u51fa"), "value": f"{identity['output_label']} / {output_text}", "help": _zh(r"\u5148\u4ea7\u751f\u53ef\u5ba1\u8ba1\u7684\u6a21\u578b\u5019\u9009\u5408\u7ea6\uff0c\u518d\u7531\u8fd0\u884c\u65f6\u7ee7\u7eed\u6267\u884c\u3002")},
        ]
    return [
        *identity_sections,
        {"kind": "method_scope", "label": _zh(r"\u5206\u6790\u4fa7\u91cd"), "value": f"{title} / {concept} / {role_text}", "help": _zh(r"\u7528\u4e8e\u628a\u539f\u59cb\u6570\u636e\u8f6c\u6210\u53ef\u590d\u6838\u7684\u65b9\u6cd5\u7ed3\u679c\u3002")},
        {"kind": "output", "label": _zh(r"\u4ea7\u51fa"), "value": f"{identity['output_label']} / {output_text}", "help": _zh(r"\u4f1a\u4fdd\u7559\u8bc1\u636e\u5f15\u7528\u548c\u8fd0\u884c\u4ea7\u7269\u5408\u7ea6\u3002")},
    ]


def method_display_metadata(method: dict[str, Any], *, compact: bool = False) -> dict[str, Any]:
    family = str(method.get("family") or "")
    outputs = _string_list(method.get("output_types"))
    roles = _string_list(method.get("required_roles"))
    selection_mode = _recommended_selection_mode(family, outputs, roles)
    family_label = _label(FAMILY_LABELS, family)
    output_labels = [_label(OUTPUT_LABELS, item) for item in outputs]
    role_labels = [_label(ROLE_LABELS, item) for item in roles]
    concept = _method_concept_label(method)
    edit_capabilities = _method_card_edit_capabilities(
        family=family,
        outputs=outputs,
        roles=roles,
        selection_mode=selection_mode,
    )
    identity = _method_identity(method, concept=concept, outputs=outputs, roles=roles)
    usage_guidance = _method_usage_guidance(
        method=method,
        family=family,
        concept=concept,
        outputs=outputs,
        roles=roles,
        selection_mode=selection_mode,
    )
    report_value_hooks = _method_report_value_hooks(family=family, outputs=outputs, roles=roles)
    if isinstance(method.get("usage_guidance"), list) and method.get("usage_guidance"):
        usage_guidance = [item for item in list(method.get("usage_guidance") or []) if isinstance(item, dict)]
    configured_hooks = _string_list(method.get("report_value_hooks"))
    if configured_hooks:
        report_value_hooks = list(dict.fromkeys([*configured_hooks, *report_value_hooks]))
    source = str(method.get("source") or "")
    status = str(method.get("status") or "")
    mode_label = {
        "object": _zh(r"\u91cd\u70b9\u5bf9\u8c61"),
        "all_rows": _zh(r"\u5168\u8868\u8fd0\u884c"),
        "fields": _zh(r"\u5b57\u6bb5\u7ed1\u5b9a"),
    }.get(selection_mode, selection_mode)
    base_goal = str(method.get("goal") or "").strip()
    output_text = _zh(r"\u3001").join(output_labels) or _zh(r"\u7ed3\u6784\u5316\u7ed3\u679c")
    role_text = _zh(r"\u3001").join(role_labels) or _zh(r"\u5f53\u524d\u6570\u636e")
    title = identity["submethod_title"] or identity["bundle_title"] or concept
    if family == "visual" or {"chart", "image_spec"} & set(outputs):
        description = f"{title} \u628a {role_text} \u8f6c\u6210{identity['output_label']}\uff0c\u7528\u6765\u770b\u6e05 {concept} \u7684\u8d8b\u52bf\u3001\u5dee\u5f02\u3001\u8c61\u9650\u6216\u5f02\u5e38\u70b9\u3002"
    elif selection_mode == "object":
        description = f"{title} \u4f18\u5148\u9762\u5411\u5df2\u6311\u9009\u7684\u91cd\u70b9\u5bf9\u8c61\uff0c\u7528 {identity['output_label']} \u8ffd\u8e2a\u5ba2\u6237\u3001\u95e8\u5e97\u3001SKU \u6216\u533a\u57df\u7b49\u5173\u952e\u5355\u5143\u7684\u8868\u73b0\u3002"
    elif selection_mode == "all_rows":
        description = f"{title} \u4f7f\u7528\u5168\u8868\u8bb0\u5f55\uff0c\u4ea7\u51fa {identity['output_label']} \u6765\u751f\u6210\u603b\u89c8\u3001\u6458\u8981\u3001\u9644\u5f55\u6216\u8bc1\u636e\u7d22\u5f15\u3002"
    elif family == "time_series":
        description = f"{title} \u805a\u7126\u65f6\u95f4\u8f74\u548c\u76ee\u6807\u6307\u6807\uff0c\u7528 {identity['output_label']} \u5224\u65ad\u8d8b\u52bf\u3001\u6ede\u540e\u3001\u5b63\u8282\u6027\u6216\u98ce\u9669\u62d0\u70b9\u3002"
    elif family in {"association", "categorical_association", "comparison"}:
        description = f"{title} \u7528 {identity['output_label']} \u68c0\u67e5 {role_text} \u4e4b\u95f4\u7684\u5173\u8054\u3001\u5dee\u5f02\u6216\u5206\u5c42\u4fe1\u53f7\uff0c\u5e2e\u52a9\u89e3\u91ca\u53d8\u5316\u6765\u6e90\u3002"
    elif family in {"regression", "regression_glm", "machine_learning", "multivariate"}:
        description = f"{title} \u628a\u76ee\u6807\u4e0e\u7279\u5f81\u5206\u5f00\uff0c\u7528 {identity['output_label']} \u4f30\u8ba1\u9a71\u52a8\u56e0\u7d20\u3001\u91cd\u8981\u6027\u6216\u53ef\u9884\u6d4b\u4fe1\u53f7\u3002"
    elif base_goal:
        description = f"{title}: {base_goal}"
    else:
        description = f"{title} \u7528\u4e8e\u628a\u6570\u636e\u7ed3\u679c\u8f6c\u6210 {identity['output_label']} \uff0c\u5f62\u6210\u53ef\u5ba1\u8ba1\u3001\u53ef\u7ee7\u7eed\u8fd0\u884c\u7684\u5206\u6790\u7ed3\u8bba\u3002"
    tags = [
        family_label,
        concept,
        mode_label,
        _status_label(status),
        _source_label(source),
        *output_labels[:3],
        *role_labels[:3],
    ]
    if family == "visual" or {"chart", "image_spec"} & set(outputs):
        tags.append(_zh(r"\u56fe\u8868\u4ea7\u7269"))
    if "report_section" in outputs:
        tags.append(_zh(r"\u53ef\u5199\u62a5\u544a\u6bb5"))
    period = _zh(r"\u3002")
    shared = {
        "method_card_contract": "analysis_lab_method_card_freedom_v2_unique_per_method",
        "edit_capabilities": edit_capabilities,
        "usage_guidance": usage_guidance,
        "report_value_hooks": report_value_hooks,
        "card_description": description if description.endswith(period) else description + period,
        "card_tags": list(dict.fromkeys([item for item in tags if item])),
        "card_sections": _method_card_sections(
            method=method,
            family=family,
            concept=concept,
            outputs=outputs,
            roles=roles,
            output_labels=output_labels,
            role_labels=role_labels,
        ),
    }
    if compact:
        return {
            "family_label": family_label,
            "output_labels": output_labels,
            "role_labels": role_labels,
            "binding_controls": _binding_controls_for_method(family, outputs, roles),
            "recommended_selection_mode": selection_mode,
            **shared,
        }
    return {
        "family_label": family_label,
        "output_labels": output_labels,
        "role_labels": role_labels,
        "binding_controls": _binding_controls_for_method(family, outputs, roles),
        "recommended_selection_mode": selection_mode,
        **shared,
    }


def auto_analysis_method_catalog(*, compact: bool = False) -> dict[str, Any]:
    registry = get_auto_analysis_method_registry()
    methods: list[dict[str, Any]] = []
    for method in registry:
        family = str(method.get("family") or "")
        outputs = _string_list(method.get("output_types"))
        stable_outputs = _string_list(method.get("stable_output_types")) or outputs
        roles = _string_list(method.get("required_roles"))
        display = method_display_metadata(method, compact=compact)
        bundle_id = _method_bundle_id(method)
        bundle_title = _method_bundle_title(method)
        concept_label = _method_concept_label(method)
        output_variant = str(method.get("catalog_output_variant") or (outputs[0] if outputs else ""))
        submethod_label = _label(OUTPUT_LABELS, output_variant or (outputs[0] if outputs else ""))
        submethod_role_label = _zh(r"\u3001").join(_label(ROLE_LABELS, item) for item in roles[:2])
        separator = _zh(r"\u30fb")
        method_payload = {
            "id": str(method.get("id") or ""),
            "name": str(method.get("name") or ""),
            "name_zh": _method_name_zh(method),
            "base_method_id": str(method.get("base_method_id") or bundle_id),
            "family": family,
            "bundle_id": bundle_id,
            "bundle_title": bundle_title,
            "bundle_title_zh": bundle_title,
            "bundle_title_en": str(method.get("bundle_title_en") or method.get("bundle_title") or method.get("name") or ""),
            "parent_method_id": bundle_id,
            "parent_method_title": bundle_title,
            "method_concept_label": concept_label,
            "output_variant": output_variant,
            "method_output_label": submethod_label,
            "submethod_label": submethod_label,
            "submethod_title": separator.join(item for item in [bundle_title, submethod_role_label, submethod_label] if item),
            "status": str(method.get("status") or ""),
            "source": str(method.get("source") or ""),
            "output_types": stable_outputs,
            "stable_output_types": stable_outputs,
            "default_output_types": _string_list(method.get("default_output_types")) or outputs,
            "required_roles": roles,
            "runtime_required": bool(method.get("runtime_required", True)),
            "runtime_executor": str(method.get("runtime_executor") or "codex_cli"),
            "cli_runtime_available": bool(method.get("cli_runtime_available", True)),
            "runtime_block_reason": str(method.get("runtime_block_reason") or ""),
            "runtime_binding_roles": _string_list(method.get("runtime_binding_roles")) or roles,
            "compatibility_alias_ids": _method_alias_ids(method),
            "field_bindings": dict(method.get("field_bindings") or {}),
            "selection_mode": str(method.get("selection_mode") or ""),
            "object_selection": dict(method.get("object_selection") or {}),
            "statistical_options": dict(method.get("statistical_options") or {}),
            **display,
        }
        if str(method.get("source") or "") == "statistical_visual_catalog":
            method_payload.update(
                {
                    "visual_domain_id": str(method.get("visual_domain_id") or ""),
                    "visual_domain_label": str(method.get("visual_domain_label") or ""),
                    "visual_pattern_id": str(method.get("visual_pattern_id") or ""),
                    "visual_pattern_label": str(method.get("visual_pattern_label") or ""),
                    "visual_intent": str(method.get("visual_intent") or ""),
                    "non_financial_statistical_visual": bool(method.get("non_financial_statistical_visual", True)),
                    "allowed_domain": str(method.get("allowed_domain") or "non_financial"),
                    "excluded_domain": str(method.get("excluded_domain") or "finance"),
                }
            )
        if not compact:
            method_payload.update(
                {
                    "goal": str(method.get("goal") or ""),
                    "goal_zh": _method_goal_zh(family, stable_outputs, concept_label),
                    "output_modes": _string_list(method.get("output_modes")) or stable_outputs,
                    "granularity_modes": _string_list(method.get("granularity_modes")) or roles,
                    "runtime_dimensions": dict(method.get("runtime_dimensions") or {}),
                    "run_metadata_schema": dict(method.get("run_metadata_schema") or {}),
                    "artifact_contract": dict(method.get("artifact_contract") or {}),
                }
            )
        methods.append(method_payload)
    return {
        "methods": methods,
        "summary": summarize_method_registry(registry),
        "priority_method_ids": sorted(priority_method_ids(registry)),
        "report_parts": report_part_ids(),
        "compact": compact,
        "method_aliases": method_alias_map(registry),
    }


def priority_method_ids(registry: list[dict[str, Any]] | None = None) -> set[str]:
    specs = load_auto_analysis_specs()
    raw_ids = [str(item) for item in list(specs.get("priority_method_ids") or []) if str(item).strip()]
    return set(canonical_method_ids(raw_ids, registry))


def report_part_ids() -> list[str]:
    specs = load_auto_analysis_specs()
    return [str(item) for item in list(specs.get("report_parts") or []) if str(item).strip()]
