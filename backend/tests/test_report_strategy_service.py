from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import report_strategy_service as strategy_service


class ReportStrategyServiceTests(unittest.TestCase):
    def test_strategy_optimizer_runs_and_returns_family_strategies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            strategy_service.load_optimized_report_strategy.cache_clear()
            with (
                patch.object(strategy_service, "STRATEGY_DIR", tmp_path),
                patch.object(strategy_service, "STRATEGY_FILE", tmp_path / "optimized-report-strategy.json"),
            ):
                payload = strategy_service.train_report_strategy_optimizer(num_trials=200, seed=7)
                self.assertEqual(payload["num_trials"], 200)
                self.assertIn("media_review", payload["best_strategies"])
                self.assertIn("management_accounting_review", payload["best_strategies"])
                self.assertTrue(payload["best_strategies"]["media_review"]["management_section_ids"])
                self.assertTrue((tmp_path / "optimized-report-strategy.json").exists())


if __name__ == "__main__":
    unittest.main()
