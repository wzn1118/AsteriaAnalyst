from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.services.path_service import REPO_ROOT


def _codex_skills_root() -> Path:
    configured = os.getenv("CODEX_SKILLS_ROOT") or os.getenv("CODEX_HOME")
    if configured:
        root = Path(configured).expanduser()
        return (root / "skills").resolve() if root.name != "skills" else root.resolve()
    return (Path.home() / ".codex" / "skills").resolve()


def _project_skills_root() -> Path:
    configured = os.getenv("ASTERIA_PROJECT_ROOT")
    project_root = Path(configured).expanduser().resolve() if configured else REPO_ROOT
    return (project_root / "skills").resolve()


CODEX_SKILLS_ROOT = _codex_skills_root()
PROJECT_SKILLS_ROOT = _project_skills_root()


CURATED_SKILL_MOUNTS = [
    {
        "id": "analysis-delivery-workflow",
        "name": "Analysis Delivery Workflow",
        "path": PROJECT_SKILLS_ROOT / "analysis-delivery-workflow" / "SKILL.md",
        "role": "把粗需求、上传数据、输出格式选择和可下载交付物串成主工作流。",
        "mount_reason": "作为当前产品的主分析 workflow skill。",
    },
    {
        "id": "spreadsheet",
        "name": "Spreadsheet",
        "path": CODEX_SKILLS_ROOT / "spreadsheet" / "SKILL.md",
        "role": "处理 xlsx/csv/tsv 的读取、分析、透视和结构化输出。",
        "mount_reason": "对 Excel 数据、结果表和后续工作簿交付最直接相关。",
    },
    {
        "id": "pdf",
        "name": "PDF",
        "path": CODEX_SKILLS_ROOT / "pdf" / "SKILL.md",
        "role": "读取、抽取和验证 PDF 历史文件。",
        "mount_reason": "支撑历史报告 PDF 上传与抽取。",
    },
    {
        "id": "doc",
        "name": "DOCX",
        "path": CODEX_SKILLS_ROOT / "doc" / "SKILL.md",
        "role": "读取、编辑和验证 docx 历史文件与交付件。",
        "mount_reason": "支撑历史报告 Word 上传与后续文档交付。",
    },
    {
        "id": "slides",
        "name": "Slides",
        "path": CODEX_SKILLS_ROOT / "slides" / "SKILL.md",
        "role": "生成和编辑 PPT 汇报稿。",
        "mount_reason": "后续要把分析结果升级成管理层汇报 deck。",
    },
    {
        "id": "write",
        "name": "Write",
        "path": CODEX_SKILLS_ROOT / "deepscientist-write" / "SKILL.md",
        "role": "把证据转成更完整、更可信的报告写作输出。",
        "mount_reason": "用于提升历史报告仿写和正式报告写作品质。",
    },
    {
        "id": "mentor",
        "name": "Mentor",
        "path": CODEX_SKILLS_ROOT / "deepscientist-mentor" / "SKILL.md",
        "role": "做产品味道、结构判断和高标准校准。",
        "mount_reason": "避免报告和工作台走向泛化 AI 模板风格。",
    },
]


def get_mounted_skills() -> list[dict[str, Any]]:
    mounted: list[dict[str, Any]] = []
    for item in CURATED_SKILL_MOUNTS:
        path = Path(item["path"])
        if not path.exists():
            continue
        mounted.append(
            {
                "id": item["id"],
                "name": item["name"],
                "path": str(path),
                "role": item["role"],
                "mount_reason": item["mount_reason"],
            }
        )
    return mounted


def get_mounted_skill_summary() -> dict[str, Any]:
    mounted = get_mounted_skills()
    return {
        "count": len(mounted),
        "skill_ids": [item["id"] for item in mounted],
    }
