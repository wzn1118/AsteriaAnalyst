from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from app.models import StatisticRequest
from app.services.analysis_service import run_statistical_analysis


class MachineLearningAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(42)
        x1 = rng.normal(0, 1, 160)
        x2 = rng.normal(0, 1, 160)
        x3 = rng.normal(0, 1, 160)
        y_reg = (1.8 * x1) - (0.6 * x2) + (0.9 * x1 * x3)
        y_cls = (y_reg > np.median(y_reg)).astype(int)
        cls.frame = pd.DataFrame(
            {
                "x1": x1,
                "x2": x2,
                "x3": x3,
                "y_reg": y_reg,
                "y_cls": y_cls,
            }
        )

    def test_random_forest_runs_with_chinese_narrative(self) -> None:
        result = run_statistical_analysis(
            self.frame,
            StatisticRequest(
                dataset_id="demo",
                analysis_type="random_forest",
                target="y_reg",
                features=["x1", "x2", "x3"],
                metric_type="continuous",
            ),
        )
        self.assertEqual(result["analysis_type"], "random_forest")
        self.assertIn("随机森林", result["title"])
        self.assertIn("业务上", result["narrative"])
        self.assertTrue(result["tables"])

    def test_neural_network_runs_with_chinese_narrative(self) -> None:
        result = run_statistical_analysis(
            self.frame,
            StatisticRequest(
                dataset_id="demo",
                analysis_type="neural_network",
                target="y_reg",
                features=["x1", "x2", "x3"],
                metric_type="continuous",
            ),
        )
        self.assertEqual(result["analysis_type"], "neural_network")
        self.assertIn("神经网络", result["title"])
        self.assertIn("非线性", result["narrative"])
        self.assertTrue(result["tables"])

    def test_deep_learning_runs_with_chinese_narrative(self) -> None:
        result = run_statistical_analysis(
            self.frame,
            StatisticRequest(
                dataset_id="demo",
                analysis_type="deep_learning",
                target="y_cls",
                features=["x1", "x2", "x3"],
                metric_type="binary",
            ),
        )
        self.assertEqual(result["analysis_type"], "deep_learning")
        self.assertIn("深度学习", result["title"])
        self.assertIn("复杂", result["narrative"])
        self.assertTrue(result["tables"])


if __name__ == "__main__":
    unittest.main()
