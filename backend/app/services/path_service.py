from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "AsteriaAnalyst"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = REPO_ROOT / "workspace"
RUNTIME_CANDIDATE_ROOTS = [
    (REPO_ROOT / "workspace" / "runtime").resolve(),
    (REPO_ROOT / "runtime").resolve(),
]


def app_data_dir() -> Path:
    override = os.getenv("ASTERIA_DATA_DIR")
    if override:
        path = Path(override).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    if getattr(sys, "frozen", False):
        base = Path(os.getenv("APPDATA", Path.home() / ".asteria-analyst"))
        path = (base / APP_NAME).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    path = (WORKSPACE_ROOT / "storage").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return PROJECT_ROOT


def frontend_dist_dir() -> Path:
    bundled = runtime_root() / "frontend_dist"
    if bundled.exists():
        return bundled
    dev_export = REPO_ROOT / "frontend" / "out"
    if dev_export.exists():
        return dev_export
    return bundled


def bundled_rscript_candidates() -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()
    for root in RUNTIME_CANDIDATE_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.glob("R-*")):
            for candidate in [
                path / "bin" / "Rscript.exe",
                path / "bin" / "x64" / "Rscript.exe",
            ]:
                key = str(candidate.resolve()) if candidate.exists() else str(candidate)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(candidate)
    return candidates


def bundled_codex_cli_candidates() -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()
    candidate_names = ["codex.exe", "codex.cmd", "codex"]
    roots = [
        runtime_root(),
        REPO_ROOT,
        REPO_ROOT / "runtime",
        REPO_ROOT / "workspace" / "runtime",
        REPO_ROOT / "tools",
        PROJECT_ROOT / "tools",
        REPO_ROOT / "vendor",
        PROJECT_ROOT / "vendor",
        REPO_ROOT / "frontend" / "node_modules" / ".bin",
        REPO_ROOT / "node_modules" / ".bin",
    ]
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if local_app_data:
        roots.append(Path(local_app_data) / "OpenAI" / "Codex" / "bin")
    app_data = os.getenv("APPDATA", "")
    if app_data:
        roots.append(Path(app_data) / "npm")

    subdirs = [
        Path("."),
        Path("codex"),
        Path("codex") / "bin",
        Path("openai-codex"),
        Path("openai-codex") / "bin",
    ]
    for root in roots:
        for subdir in subdirs:
            for name in candidate_names:
                candidate = (root / subdir / name).expanduser()
                key = str(candidate).lower()
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(candidate)
    return candidates


STORAGE_DIR = app_data_dir()
DATASETS_DIR = STORAGE_DIR / "datasets"
RUNS_DIR = STORAGE_DIR / "runs"
# This is the only directory exposed through the application's static route.
# Keep private settings, datasets, and runtime state outside this subtree.
PUBLIC_ARTIFACTS_DIR = (STORAGE_DIR / "public_artifacts").resolve()
REPORTS_DIR = PUBLIC_ARTIFACTS_DIR / "reports"
HISTORICAL_REPORTS_DIR = STORAGE_DIR / "historical_reports"
BUSINESS_BACKGROUNDS_DIR = STORAGE_DIR / "business_backgrounds"
SETTINGS_PATH = STORAGE_DIR / "settings.json"
CODEX_RUNTIME_DIR = RUNS_DIR / "codex_runtime"
CODEX_RUNTIME_RUNS_DIR = CODEX_RUNTIME_DIR / "runs"
CODEX_RUNTIME_TASKS_DIR = CODEX_RUNTIME_DIR / "tasks"
CODEX_RUNTIME_LEARNING_LEDGER_DIR = CODEX_RUNTIME_DIR / "learning_ledger"
