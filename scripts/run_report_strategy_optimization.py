from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.report_strategy_service import STRATEGY_FILE, train_report_strategy_optimizer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the report strategy optimizer.")
    parser.add_argument("--num-trials", type=int, default=12_000, help="Proxy optimization trial count.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()
    payload = train_report_strategy_optimizer(num_trials=args.num_trials, seed=args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"WROTE={STRATEGY_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
