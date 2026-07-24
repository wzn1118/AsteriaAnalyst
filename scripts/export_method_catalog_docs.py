"""Export the public Chinese method catalog from Asteria's backend registries.

Run from the repository root:
    backend\\.venv\\Scripts\\python.exe scripts\\export_method_catalog_docs.py
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
DOCS_DIR = ROOT / "docs"

sys.path.insert(0, str(BACKEND_DIR))

from app.services.auto_analysis_registry_service import auto_analysis_method_catalog  # noqa: E402
from app.services.statistical_catalog import get_catalog_summary, get_statistical_catalog  # noqa: E402


FAMILY_LABELS = {
    "association": "关联分析",
    "categorical_association": "分类关联",
    "causal": "因果探查",
    "causal_panel": "面板因果",
    "comparison": "差异比较",
    "descriptive": "描述统计",
    "distribution_assumption": "分布假设",
    "experimentation": "实验分析",
    "machine_learning": "机器学习",
    "mean_tests": "均值检验",
    "multivariate": "多变量分析",
    "nonparametric": "非参数检验",
    "psychometrics": "心理测量",
    "regression_glm": "广义线性模型",
    "report_part": "报告部件",
    "statistical": "统计推断与稳健性",
    "survival": "生存分析",
    "time_series": "时间序列",
}

ROLE_LABELS = {
    "binary": "二元字段",
    "binary_group": "二元分组",
    "categorical": "分类字段",
    "categorical_pair": "两个分类字段",
    "count": "计数字段",
    "covariate": "协变量",
    "effect_size": "效应量",
    "event_type": "事件类型",
    "features": "特征字段",
    "group": "分组字段",
    "grouped": "分组结构",
    "grouped_numeric": "分组数值结构",
    "multi_categorical": "多分类字段",
    "multi_class": "多分类目标",
    "multi_item_scale": "多题项量表",
    "multi_numeric": "多个数值字段",
    "numeric": "数值字段",
    "numeric_or_binary": "数值或二元目标",
    "numeric_or_categorical": "数值或分类字段",
    "ordered": "有序字段",
    "ordered_category": "有序分类目标",
    "outcome": "结果字段",
    "paired": "配对标识",
    "panel": "面板标识",
    "positive_numeric": "正值数值字段",
    "proportion": "比例字段",
    "strata": "分层字段",
    "target": "目标字段",
    "time": "时间字段",
    "time_to_event": "生存时长",
    "within_subject_factor": "受试内因子",
    "x": "自变量",
    "y": "因变量",
    "m": "中介变量",
    "moderator": "调节变量",
    "latent": "潜变量",
    "repeated_measure": "重复测量结构",
    "multi_group_scale": "多组量表",
}

STATUS_LABELS = {
    "live": "可运行",
    "catalog": "目录条目",
    "planned": "规划条目",
}

FAMILY_ORDER = [
    "descriptive",
    "distribution_assumption",
    "mean_tests",
    "nonparametric",
    "categorical_association",
    "association",
    "regression_glm",
    "machine_learning",
    "multivariate",
    "time_series",
    "experimentation",
    "causal",
    "causal_panel",
    "survival",
    "psychometrics",
    "statistical",
    "comparison",
    "report_part",
]


def escape_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def role_labels(roles: list[str]) -> str:
    return "、".join(ROLE_LABELS.get(role, role.replace("_", " ")) for role in roles)


def family_label(family: str) -> str:
    return FAMILY_LABELS.get(family, family.replace("_", " "))


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def render_statistics_catalog() -> str:
    methods = get_statistical_catalog()
    summary = get_catalog_summary()
    lab_cards = auto_analysis_method_catalog(compact=True)["methods"]
    live_lab_stat_cards = [
        card
        for card in lab_cards
        if card["status"] == "live" and card["source"] == "statistical_catalog"
    ]
    live_lab_concepts = {
        str(card["base_method_id"])
        for card in live_lab_stat_cards
    }
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for method in methods:
        grouped[str(method["family"])].append(method)

    lines = [
        "# Asteria Analyst 统计方法与 Analysis Lab 目录",
        "",
        "> 本文档由 `scripts/export_method_catalog_docs.py` 从后端注册表生成。变更方法后请重新执行生成器，再提交本文件。",
        "",
        "## 目录范围",
        "",
        f"- 统计方法注册总数：`{summary['total_methods']}`",
        f"- 可运行统计方法：`{summary['live_methods']}`",
        f"- 目录方法：`{summary['catalog_methods']}`",
        (
            "- Analysis Lab 可运行统计方法卡："
            f"`{len(live_lab_stat_cards)}` 张，覆盖 "
            f"`{len(live_lab_concepts)}` 个可运行统计方法概念。"
        ),
        "- 方法数据源：`backend/app/services/statistical_catalog.py`；Lab 卡片注册源：`backend/app/services/auto_analysis_registry_service.py`。",
        "",
        "### 状态说明",
        "",
        "| 状态 | 含义 |",
        "| --- | --- |",
        "| 可运行 | 已连接执行器，可在 Analysis Lab 配置字段并产生运行产物。 |",
        "| 目录条目 | 已登记方法目标与字段契约，用于选型、路线规划与后续执行器接入。 |",
        "| 规划条目 | 已登记在 Lab 方法空间中，用于产品路线与能力编排。 |",
        "",
        "### 字段角色速查",
        "",
        "| 角色 | 使用方式 |",
        "| --- | --- |",
        "| 数值字段 | 金额、次数、评分、时长、连续型指标。 |",
        "| 分类字段 | 地区、渠道、产品线、客户类型等离散分组。 |",
        "| 时间字段 | 日期、周、月、季度或有稳定排序的时间戳。 |",
        "| 目标字段 | 待解释、预测或比较的结果变量。 |",
        "| 特征字段 | 用于解释或预测目标字段的输入变量集合。 |",
        "| 配对标识 / 受试内因子 | 同一对象前后测量、重复测量或匹配样本结构。 |",
        "| 面板标识 / 分层字段 | 个体-时间面板、分层实验或多层数据结构。 |",
        "",
        "## 结果解读与交付",
        "",
        "| 方法族 | 优先查看的结果 | 常见交付判断 |",
        "| --- | --- | --- |",
        "| 描述统计 | 样本量、缺失、均值/中位数、分位数、集中度 | 识别水平、波动、长尾和头部贡献。 |",
        "| 分布假设 | 检验统计量、p 值、残差诊断 | 选择参数检验、稳健方法或变换策略。 |",
        "| 均值与非参数检验 | 组间差异、置信区间、p 值、效应量 | 判断差异方向、大小与业务价值。 |",
        "| 分类关联 | 列联表、期望频数、关联强度 | 判断分类变量是否相关并量化关联强度。 |",
        "| 关联分析 | 相关系数、方向、强度、显著性 | 区分线性、秩相关、偏相关和非线性关联。 |",
        "| 回归与机器学习 | 系数/重要性、拟合优度、误差、诊断 | 解释驱动因素、预测表现与稳定性。 |",
        "| 多变量与聚类 | 方差解释、载荷、簇规模、轮廓线索 | 完成降维、分群或群体结构识别。 |",
        "| 时间序列 | 趋势、季节性、滞后、平稳性、残差 | 判断时间结构并选择预测或监控路线。 |",
        "| 实验、因果与生存 | 处理效应、对照证据、风险率/生存率 | 形成实验决策、因果评估或留存分析结论。 |",
        "",
        "## 全量统计方法注册表",
        "",
    ]

    extra_families = sorted(set(grouped) - set(FAMILY_ORDER))
    for family in [*FAMILY_ORDER, *extra_families]:
        entries = grouped.get(family)
        if not entries:
            continue
        entries.sort(key=lambda entry: str(entry["id"]))
        live = sum(entry["status"] == "live" for entry in entries)
        lines.extend(
            [
                f"### {family_label(family)}（{len(entries)} 项；可运行 {live} 项）",
                "",
                "| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for entry in entries:
            lines.append(
                "| `{id}` | {name} | {goal} | {roles} | {status} |".format(
                    id=escape_cell(entry["id"]),
                    name=escape_cell(entry["name"]),
                    goal=escape_cell(entry["goal"]),
                    roles=escape_cell(role_labels(list(entry["variable_types"]))),
                    status=status_label(str(entry["status"])),
                )
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_lab_inventory() -> str:
    lab_catalog = auto_analysis_method_catalog(compact=True)
    cards = list(lab_catalog["methods"])
    status_counts = Counter(str(card["status"]) for card in cards)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for card in cards:
        grouped[str(card["family_label"])].append(card)

    lines = [
        "# Analysis Lab 方法卡索引",
        "",
        "> 本文档由 `scripts/export_method_catalog_docs.py` 生成，记录当前 Lab 注册表中的全部方法卡。",
        "",
        "## 运行状态",
        "",
        f"- 方法卡总数：`{len(cards)}`",
        f"- 可运行：`{status_counts['live']}`",
        f"- 目录条目：`{status_counts['catalog']}`",
        f"- 规划条目：`{status_counts['planned']}`",
        "- API：`GET /api/lab/methods?compact=true`；全量字段可通过 `compact=false` 获取。",
        "",
        "## 使用约定",
        "",
        "每张方法卡保存方法身份、字段角色、可选运行模式与产物合约。`live` 卡可在 Lab 中绑定数据集字段并运行；卡片产物按方法契约输出 JSON、CSV、XLSX、Markdown，部分方法额外提供图表、SVG、HTML 或图像规格。",
        "",
        "## 全量方法卡",
        "",
    ]

    for family in sorted(grouped):
        entries = sorted(grouped[family], key=lambda entry: str(entry["id"]))
        family_status = Counter(str(entry["status"]) for entry in entries)
        lines.extend(
            [
                f"### {family}（{len(entries)} 张；可运行 {family_status['live']} 张）",
                "",
                "| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for entry in entries:
            lines.append(
                "| `{id}` | {method} | {output} | {roles} | {status} | {source} |".format(
                    id=escape_cell(entry["id"]),
                    method=escape_cell(entry["method_concept_label"]),
                    output=escape_cell(entry["method_output_label"]),
                    roles=escape_cell("、".join(entry["role_labels"])),
                    status=status_label(str(entry["status"])),
                    source=escape_cell(entry["source"]),
                )
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    statistics_path = DOCS_DIR / "statistical_methods_zh.md"
    lab_path = DOCS_DIR / "lab_method_inventory_zh.md"
    statistics_path.write_text(render_statistics_catalog(), encoding="utf-8", newline="\n")
    lab_path.write_text(render_lab_inventory(), encoding="utf-8", newline="\n")
    print(f"wrote {statistics_path.relative_to(ROOT)}")
    print(f"wrote {lab_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
