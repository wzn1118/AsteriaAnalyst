from __future__ import annotations

import unittest

import pandas as pd

from app.models import StatisticRequest
from app.services.analysis_service import run_correlation


class AnalysisServiceTests(unittest.TestCase):
    def test_run_correlation_includes_pairwise_p_values(self) -> None:
        frame = pd.DataFrame(
            {
                "活跃用户": [10, 20, 30, 40, 50, 60],
                "留存用户": [8, 16, 23, 31, 39, 46],
                "转化用户": [1, 2, 2, 4, 5, 6],
            }
        )
        result = run_correlation(
            frame,
            StatisticRequest(dataset_id="test", analysis_type="correlation", features=["活跃用户", "留存用户", "转化用户"]),
        )
        top_rows = result["tables"][0]["rows"]
        self.assertIn("p_value", result["tables"][0]["columns"])
        self.assertIsNotNone(top_rows[0]["p_value"])
        self.assertIsNotNone(result["metrics"]["strongest_p_value"])


if __name__ == "__main__":
    unittest.main()
