from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path
from typing import Any


BRIEF_MD_NAME = "05_report_management_brief.md"
BRIEF_HTML_NAME = "06_report_management_brief.html"
BRIEF_PDF_NAME = "07_report_management_brief.pdf"
TABLE_READING_CARDS_NAME = "ops_table_reading_cards.json"
NARRATIVE_SECTIONS_NAME = "ops_narrative_sections.json"
MANAGEMENT_QUADRANT_INDEX_JSON_NAME = "ops_management_quadrant_index.json"
MANAGEMENT_QUADRANT_INDEX_CSV_NAME = "ops_management_quadrant_index.csv"
DERIVED_METRIC_DIAGNOSIS_CARDS_NAME = "ops_derived_metric_diagnosis_cards.json"
CHANNEL_SOURCE_KPI_CANONICAL_JSON_NAME = "ops_channel_source_kpi_canonical.json"
CHANNEL_SOURCE_KPI_CANONICAL_CSV_NAME = "ops_channel_source_kpi_canonical.csv"
MANAGEMENT_THRESHOLDS_JSON_NAME = "ops_management_thresholds.json"
EXECUTIVE_ACTION_RULES_JSON_NAME = "ops_executive_action_rules.json"
METRIC_SEMANTICS_CONTRACT_JSON_NAME = "ops_metric_semantics_contract.json"
CONSISTENCY_ISSUE_REGISTRY_JSON_NAME = "ops_consistency_issue_registry.json"

CANONICAL_CHANNEL_SOURCE_KPI_FIELDS = [
    "sample_size",
    "impressions",
    "clicks",
    "registrations",
    "activations",
    "paid_users",
    "revenue",
    "operating_cost",
    "contribution_margin",
    "roi",
    "cac",
    "retention_d7",
    "nps",
]

CANONICAL_ALIAS_FIELDS = {
    "sample_size": ["样本量"],
    "impressions": ["曝光"],
    "clicks": ["点击"],
    "registrations": ["注册"],
    "activations": ["激活"],
    "paid_users": ["付费用户"],
    "revenue": ["收入"],
    "operating_cost": ["运营成本"],
    "contribution_margin": ["贡献毛利"],
}

CORE_READING_CARD_IDS = [
    "executive_metric_summary",
    "aarrr_total",
    "aarrr_top12",
    "roi_cac_quadrant",
    "ctr_cpc_cpm",
    "cost_margin_share",
    "user_quality_bridge",
    "retention_nps_quality",
    "paid_users_revenue",
    "daily_action_board",
    "owner_schedule",
]

NARRATIVE_SECTION_CONTEXT = {
    "executive_metric_summary": {
        "title": "全盘预算效率：先判断钱有没有被好对象接住",
        "lead": "先把视角放在全盘预算效率上：关键是确认预算有没有被高回报、低成本对象接住。",
        "next": "总盘只能告诉我们效率被稀释，下一步要看漏斗断点在哪里，避免把预算动作直接压在一个总漏斗结论上。",
    },
    "aarrr_total": {
        "title": "增长漏斗总览（AARRR）：先定位断点，不直接下预算指令",
        "lead": "总漏斗负责定位阶段性断点，预算裁决需要继续拆到渠道组合。",
        "next": "断点确定之后，预算资格要回到渠道 × 流量来源组合里判断，因为同一断点在不同组合上的承接强弱并不一样。",
    },
    "aarrr_top12": {
        "title": "渠道 × 流量来源漏斗：把断点拆成可迁入和待修复组合",
        "lead": "组合级 AARRR 把总漏斗拆回具体投放对象，核心是看哪些组合能接预算、哪些组合只是在消耗。",
        "next": "漏斗只能说明转化承接，真正决定预算从哪里出来、往哪里去，还要交给 roi/cac 四象限裁决。",
    },
    "roi_cac_quadrant": {
        "title": "真实投放回报 × 获客成本：把四类对象写成预算流转顺序",
        "lead": "ROI/CAC 这张表直接回答预算从哪里出来、往哪里去。",
        "next": "预算迁移顺序确定后，还要看前段点击是否真实有效；否则高 roi 可能只是短期归因窗口里的偶然高点。",
    },
    "ctr_cpc_cpm": {
        "title": "点击率 × 点击成本：区分有效入口和虚高点击",
        "lead": "CTR/CPC/CPM 负责筛出能继续走到注册、激活、付费和回报的入口。",
        "next": "入口效率通过后，还要看成本是否变成毛利；否则点击和付费都会停留在流水层面。",
    },
    "cost_margin_share": {
        "title": "成本占比 × 毛利占比：确认预算有没有转成利润",
        "lead": "成本毛利矩阵把预算动作从增长指标拉回利润，核心问题是花出去的钱有没有换成贡献毛利。",
        "next": "利润承接看完后，下一步要把人群质量和产品活动承接接起来，但这一步只能做桥接实验，不能写成直接因果。",
    },
    "user_quality_bridge": {
        "title": "用户质量与商业承接：用实验连接两个对象池",
        "lead": "用户质量和商业化承接分别回答“哪类人值得经营”和“哪类产品活动能接住收入”。",
        "next": "桥接关系明确以后，执行层就不能再写成泛泛建议，必须落到 Day 1-Day 7 的顺序和 Owner 检查点。",
    },
    "retention_nps_quality": {
        "title": "用户质量池：决定 Day 3 保留谁、降权谁",
        "lead": "留存和 NPS 在这里用于筛出 Day 3 继续经营和暂停扩量的人群。",
        "next": "人群值得经营并不代表产品活动已经接住收入，所以还要进入商业承接表。",
    },
    "paid_users_revenue": {
        "title": "商业承接池：决定 Day 5 用哪个产品活动接住高质量人群",
        "lead": "付费用户和收入表负责判断产品/活动是否能把流量和人群转成收入、毛利和回报。",
        "next": "到这里，预算对象、入口对象、人群对象和承接对象已经拆清楚，最后要用日动作把它们排进执行顺序。",
    },
    "daily_action_board": {
        "title": "Day 1-Day 7：把经营判断排成一周动作顺序",
        "lead": "日动作把前面所有取舍按风险优先级排队。",
        "next": "动作排完以后，最后一层要看 Owner 是否真的能按对象、指标和检查点闭环。",
    },
    "owner_schedule": {
        "title": "Owner 责任视图：让每个动作能被复盘",
        "lead": "Owner 视图的价值在于把经营判断落到角色手里，避免所有事情都变成“运营负责人跟进”。",
        "next": "这条链路到 Owner 结束：前面负责判断，日动作负责排序，Owner 负责让判断在检查点上被验证。",
    },
}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_csv_rows(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _num(value: Any) -> float:
    try:
        text = str(value if value is not None else "").replace(",", "").strip()
        if not text:
            return 0.0
        return float(text)
    except Exception:
        return 0.0


def _fmt_num(value: Any, digits: int = 0) -> str:
    number = _num(value)
    if abs(number) >= 100000000:
        return f"{number / 100000000:.1f}亿"
    if abs(number) >= 10000:
        return f"{number / 10000:.1f}万"
    if digits:
        return f"{number:,.{digits}f}"
    return f"{number:,.0f}"


def _fmt_rate(value: Any) -> str:
    return f"{_num(value):.1%}"


def _fmt_value(column: str, value: Any) -> str:
    if column in {
        "点击率",
        "点击到注册率",
        "注册到激活率",
        "激活到付费率",
        "点击到付费率",
        "注册到付费率",
        "毛利率",
        "retention_d7",
        "CTR",
        "成本占比",
        "毛利占比",
        "收入占比",
        "付费用户占比",
    }:
        return _fmt_rate(value)
    if column in {"单客付费", "单客毛利", "单次点击收入", "单次点击毛利", "注册价值", "激活价值", "每付费用户收入"}:
        return f"{_num(value):,.2f}元"
    if column in {"成本回收倍数", "毛利回收倍数"}:
        return f"{_num(value):,.2f}倍"
    if column in {"roi", "cac", "nps", "CPM", "CPC", "效率分", "增长质量分", "预算效率", "获客成本"}:
        return _fmt_num(value, 2)
    if column in {"revenue", "operating_cost", "contribution_margin", "收入", "运营成本", "贡献毛利"}:
        return _fmt_num(value)
    if column in {"paid_users", "付费用户", "impressions", "clicks", "registrations", "activations", "曝光", "点击", "注册", "激活", "sample_size", "样本量"}:
        return _fmt_num(value)
    return str(value if value is not None else "").replace("|", " / ")


FIELD_LABELS = {
    "channel": "渠道",
    "traffic_source": "流量来源",
    "组合": "组合",
    "图中序号": "图中序号",
    "展示排序": "排序",
    "入选原因": "入选原因",
    "impressions": "曝光",
    "clicks": "点击",
    "registrations": "注册",
    "activations": "激活",
    "paid_users": "付费用户",
    "revenue": "收入",
    "operating_cost": "运营成本",
    "contribution_margin": "贡献毛利",
    "roi": "真实投放回报（roi）",
    "cac": "获客成本（cac）",
    "retention_d7": "7日留存",
    "nps": "口碑净推荐值（NPS）",
    "CTR": "点击率（CTR）",
    "CPM": "千次曝光成本（CPM）",
    "CPC": "单次点击成本（CPC）",
    "点击率": "点击率",
    "点击到注册率": "点击到注册率",
    "注册到激活率": "注册到激活率",
    "激活到付费率": "激活到付费率",
    "点击到付费率": "点击到付费率",
    "注册到付费率": "注册到付费率",
    "毛利率": "毛利率",
    "单客付费": "单客付费",
    "单客毛利": "单客毛利",
    "单次点击收入": "单次点击收入",
    "单次点击毛利": "单次点击毛利",
    "注册价值": "注册价值",
    "激活价值": "激活价值",
    "成本回收倍数": "成本回收倍数",
    "毛利回收倍数": "毛利回收倍数",
    "象限": "象限",
    "建议动作": "建议动作",
    "对象组合": "对象组合",
    "owner_role": "责任角色",
    "day_label": "日期槽位",
    "theme": "主题",
    "object_name": "对象",
    "this_day_action": "当日动作",
    "success_metric": "成功指标",
    "next_checkpoint": "下一检查点",
    "chart_id": "图表ID",
    "chart_title": "图表",
    "chart_type": "图表类型",
    "source_csv": "源CSV",
    "object_dimension": "对象维度",
    "band": "象限或分层",
    "object_count": "对象数量",
    "object_list": "对象清单",
    "representative_ids": "代表序号",
    "metric_range": "关键指标范围",
    "metric_distribution_summary": "关键指标分布（区间 / 平均数 / 加权平均）",
    "derived_metric_distribution_summary": "派生指标分布（区间 / 平均数 / 加权平均）",
    "derived_metric_weight_policy": "派生指标加权口径",
    "derived_metric_diagnosis": "派生指标诊断要点",
    "metric_weight_policy": "加权口径",
    "metric_mean": "平均数",
    "metric_weighted_mean": "加权平均",
    "management_action": "管理动作",
    "owner": "责任角色",
    "checkpoint": "检查点",
    "product_module": "产品模块",
    "campaign": "活动",
    "user_segment": "用户分层",
    "city_tier": "城市层级",
}


def _label(column: str) -> str:
    return FIELD_LABELS.get(column, column)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str], *, limit: int | None = None) -> str:
    display_rows = rows[:limit] if limit is not None else rows
    headers = [_label(column) for column in columns]

    def clean(value: Any) -> str:
        return str(value if value is not None else "").replace("|", " / ").replace("\n", "<br>").strip()

    lines = ["| " + " | ".join(clean(header) for header in headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in display_rows:
        lines.append("| " + " | ".join(clean(_fmt_value(column, row.get(column))) for column in columns) + " |")
    return "\n".join(lines)


def _top(rows: list[dict[str, Any]], column: str, *, reverse: bool = True, count: int = 5) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: _num(row.get(column)), reverse=reverse)[:count]


def _sum(rows: list[dict[str, Any]], column: str) -> float:
    return sum(_num(row.get(column)) for row in rows)


def _first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def _combo(row: dict[str, Any]) -> str:
    raw = str(row.get("组合") or row.get("对象组合") or f"{row.get('channel', '')} / {row.get('traffic_source', '')}")
    text = raw.replace("|", " / ").replace("×", " / ")
    text = re.sub(r"\s*/\s*", " / ", text)
    return re.sub(r"\s+", " ", text).strip(" /")


def _short_id(row: dict[str, Any]) -> str:
    return str(row.get("图中序号") or row.get("展示排序") or row.get("day_label") or "-").strip()


def _object_label(row: dict[str, Any]) -> str:
    if row.get("object_name"):
        return str(row.get("object_name") or "").replace("|", " / ")
    if row.get("对象"):
        return str(row.get("对象") or "").replace("|", " / ")
    combo = _combo(row)
    return combo if combo else _short_id(row)


def _fact_sentence(row: dict[str, Any], columns: list[str]) -> str:
    facts: list[str] = []
    for column in columns:
        value = row.get(column)
        if value is None or str(value).strip() == "":
            continue
        facts.append(f"{_label(column)} {_fmt_value(column, value)}")
    return "、".join(facts)


def _reading_line(row: dict[str, Any], columns: list[str], judgement: str) -> str:
    marker = _short_id(row)
    object_name = _object_label(row)
    facts = _fact_sentence(row, columns)
    prefix = f"{marker} {object_name}" if marker and marker != "-" else object_name
    return f"{prefix}：{facts}；判断：{judgement}。"


def _action_line(*, object_name: str, trigger: str, action: str, metric: str, checkpoint: str, owner: str) -> dict[str, str]:
    return {
        "对象": object_name,
        "触发原因": trigger,
        "后续动作": action,
        "成功指标": metric,
        "检查点": checkpoint,
        "owner": owner,
    }


def _render_action_line(action: dict[str, Any]) -> str:
    return (
        f"{action.get('对象', '待定对象')}：触发原因={action.get('触发原因', '待复核')}；"
        f"动作={action.get('后续动作', '待定动作')}；负责人={action.get('owner', '运营负责人')}；"
        f"成功指标={action.get('成功指标', 'roi / cac / contribution_margin')}；"
        f"检查点={action.get('检查点', 'Day 7 复盘')}。"
    )


def _table_card(
    *,
    card_id: str,
    table_name: str,
    table_question: str,
    conclusion: str,
    key_rows: list[str],
    follow_up_actions: list[dict[str, str]],
    cannot_infer: str,
) -> dict[str, Any]:
    return {
        "card_id": card_id,
        "table_name": table_name,
        "table_question": table_question,
        "pre_table_conclusion": conclusion,
        "key_rows": key_rows,
        "follow_up_actions": follow_up_actions,
        "cannot_infer": cannot_infer,
    }


def _card_v3(
    *,
    card_id: str,
    table_name: str,
    table_question: str,
    judgement_standard: str,
    standard_formula: str,
    object_bands: list[dict[str, Any]],
    representative_objects: list[str],
    business_conclusion: str,
    decision_path: str,
    next_moves: list[dict[str, str]],
    risk_boundary: str,
) -> dict[str, Any]:
    return {
        "card_id": card_id,
        "table_name": table_name,
        "table_question": table_question,
        "judgement_standard": judgement_standard,
        "standard_formula": standard_formula,
        "object_bands": object_bands,
        "representative_objects": representative_objects,
        "business_conclusion": business_conclusion,
        "decision_path": decision_path,
        "next_moves": next_moves,
        "risk_boundary": risk_boundary,
    }


def _band(name: str, decision: str, reading: str, objects: list[str]) -> dict[str, Any]:
    return {
        "band_name": name,
        "decision": decision,
        "standard_reading": reading,
        "objects": [item for item in objects if item],
    }


def _render_band(band: dict[str, Any]) -> str:
    objects = "；".join(str(item) for item in list(band.get("objects") or [])[:4])
    return (
        f"{band.get('band_name', '对象分层')}：{band.get('standard_reading', '')}"
        f"；取舍={band.get('decision', '')}"
        f"{'；代表对象=' + objects if objects else ''}。"
    )


def _clean_narrative_sentence(text: Any) -> str:
    cleaned = str(text if text is not None else "").strip()
    cleaned = cleaned.replace("|", " / ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _join_sentences(items: list[Any], *, limit: int = 3) -> str:
    sentences: list[str] = []
    for item in items:
        text = _clean_narrative_sentence(item)
        if not text:
            continue
        if text[-1] not in "。！？；":
            text += "。"
        sentences.append(text)
        if len(sentences) >= limit:
            break
    return "".join(sentences)


def _band_narrative(band: dict[str, Any]) -> str:
    name = _clean_narrative_sentence(band.get("band_name") or "对象层")
    reading = _clean_narrative_sentence(band.get("standard_reading") or "")
    decision = _clean_narrative_sentence(band.get("decision") or "")
    objects = "、".join(_clean_narrative_sentence(item) for item in list(band.get("objects") or [])[:3] if item)
    pieces = [name]
    if reading:
        pieces.append(reading)
    if decision:
        pieces.append(f"本周进入{decision}")
    if objects:
        pieces.append(f"代表对象是{objects}")
    return "，".join(pieces)


def _band_narrative_lines(bands: list[dict[str, Any]], *, limit: int = 4) -> str:
    lines: list[str] = []
    for band in bands[:limit]:
        line = _band_narrative(band)
        if not line:
            continue
        if line[-1] not in "。！？":
            line += "。"
        lines.append(f"- {line}")
    return "\n".join(lines)


def _action_narrative(action: dict[str, Any]) -> str:
    obj = _clean_narrative_sentence(action.get("对象") or action.get("object_name") or "待定对象")
    owner = _clean_narrative_sentence(action.get("owner") or action.get("owner_role") or "运营负责人")
    move = _clean_narrative_sentence(action.get("后续动作") or action.get("this_day_action") or "执行复核动作")
    metric = _clean_narrative_sentence(action.get("成功指标") or action.get("success_metric") or "roi / cac")
    checkpoint = _clean_narrative_sentence(action.get("检查点") or action.get("next_checkpoint") or "Day 7")
    return f"{owner}在{checkpoint}对{obj}做{move}，检查{metric}"


def _strip_contract_label_text(text: str) -> str:
    replacements = {
        "**判断标准**：": "先看",
        "**标准公式**：": "这把尺子综合",
        "**标准下的对象分层**：": "对象因此分成几类：",
        "**关键对象差异**：": "关键分化在这里：",
        "**表格问题**：": "",
        "**经营结论**：": "当前读数显示，",
        "**本周取舍**：": "本周执行上，",
        "**后续动作**：": "动作落地上，",
        "**边界说明**：": "边界上，",
        "判断标准：": "先看",
        "标准公式：": "这把尺子综合",
        "标准下的对象分层：": "对象因此分成几类：",
        "关键对象差异：": "关键分化在这里：",
        "表格问题：": "",
        "经营结论：": "当前读数显示，",
        "本周取舍：": "本周执行上，",
        "后续动作：": "动作落地上，",
        "边界说明：": "边界上，",
    }
    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"(?m)^-\s*$\n?", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def render_standard_card_as_narrative(card: dict[str, Any], context: dict[str, str] | None = None) -> str:
    context = context or {}
    card_id = str(card.get("card_id") or "")
    title = context.get("title") or str(card.get("table_name") or card_id or "核心表格")
    lead = context.get("lead") or str(card.get("table_question") or "这里先把表格证据写成经营判断。")
    next_sentence = context.get("next") or "这一节的判断会继续进入下一张表，形成预算、漏斗、利润和执行之间的闭环。"
    reps = list(card.get("representative_objects") or [])
    bands = [band for band in list(card.get("object_bands") or []) if isinstance(band, dict)]
    actions = [action for action in list(card.get("next_moves") or []) if isinstance(action, dict)]
    conclusion = _clean_narrative_sentence(card.get("business_conclusion") or "")
    decision = _clean_narrative_sentence(card.get("decision_path") or "")
    boundary = _clean_narrative_sentence(card.get("risk_boundary") or "")

    band_text = "；".join(_band_narrative(band) for band in bands[:4] if _band_narrative(band))
    reps_text = _join_sentences(reps, limit=4)
    action_text = "；".join(_action_narrative(action) for action in actions[:3])

    if card_id == "roi_cac_quadrant" and reps_text:
        first_para = (
            f"{lead}当前最值得盯住的是预算流转顺序："
            f"{reps_text}这些差异已经把对象拆成不同经营问题，低回报高成本对象先释放预算，高回报低成本对象才有资格小步承接。"
        )
    elif card_id == "user_quality_bridge" and reps_text:
        first_para = (
            f"{lead}{reps_text}这里的重点是桥接实验：高质量人群证明哪类用户值得经营，强承接产品活动证明哪类入口能接住收入；"
            "两张表之间需要实验连接，不能把人群质量和产品收入直接拼成因果。"
        )
    else:
        first_para = f"{lead}{reps_text}"

    second_para = ""
    if band_text:
        if card_id == "executive_metric_summary":
            second_para = f"{band_text}。管理层要盯住两件事：低效预算能释放多少，释放后有没有对象能接住；这也是后面继续看漏斗和象限图的原因。"
        elif card_id == "aarrr_total":
            second_para = f"{band_text}。总漏斗到这里先停住：它只告诉我们断点在哪一段，不能直接替渠道下预算指令，所以下一节必须拆到渠道 × 流量来源组合。"
        elif card_id == "aarrr_top12":
            second_para = f"{band_text}。同一批 Top12 里同时有可迁入、高消耗和承接断层组合，预算动作不能按 TopN 名次排，而要按转化承接和成本回报分流。"
        elif card_id == "roi_cac_quadrant":
            band_lines = _band_narrative_lines(bands, limit=4)
            second_para = (
                "按预算迁入资格看，四类对象构成执行顺序；为避免把不同对象的 `roi/cac` 口径混在同一句里，"
                "每一层单独列出：\n"
                f"{band_lines}\n"
                "管理上先把冻结池的新增预算停住，再让迁入池接一小段释放预算，提效池和验证池只拿到各自的测试动作。"
            )
        elif card_id == "ctr_cpc_cpm":
            band_lines = _band_narrative_lines(bands, limit=4)
            second_para = (
                "按有效获客效率看，对象会分成入口可保留、点击偏贵和承接脱节几类；"
                "不同对象的 CTR、CPC、cac 和 roi 不在同一句里合并展示：\n"
                f"{band_lines}\n"
                "这里不把 CTR 当成加码理由，只有点击继续走到注册、激活、付费并且回报不掉，才允许进入预算讨论。"
            )
        elif card_id == "cost_margin_share":
            second_para = f"按成本是否兑现成毛利看，分层直接指向预算去留：{band_text}。花钱但不产毛利的对象先迁出或降权，能把成本换成毛利的对象才保留迁入资格。"
        elif card_id == "user_quality_bridge":
            second_para = f"{band_text}。用户质量和商业承接是两张不同对象池，本节只把它们接成实验假设：先选值得经营的人群，再用强承接产品活动验证能不能接住。"
        elif card_id == "retention_nps_quality":
            second_para = f"{band_text}。Day 3 的动作由这张质量池决定：高质量组合保留经营，低质量组合先降权或修人群包，中间组合只保留验证样本。"
        elif card_id == "paid_users_revenue":
            second_para = f"{band_text}。Day 5 只让强承接组合参与桥接实验；收入高但效率弱的对象先修权益、定价或成本结构，不直接吃更多预算。"
        elif card_id == "daily_action_board":
            second_para = f"{band_text}。这是风险处理顺序：先把预算外流止住，再做迁移和承接，最后用复盘决定下周继续、降权还是转 backlog。"
        elif card_id == "owner_schedule":
            second_para = f"{band_text}。Owner 视图只保留能被复盘的责任：对象、动作、指标和检查点缺一项，就不能算进本周执行闭环。"
        else:
            second_para = f"{band_text}。本节只保留能改变经营动作的分层，无法落到对象、指标和检查点的判断不进入执行。"
    third_para = ""
    if conclusion or decision:
        third_para = f"{conclusion}{' ' if conclusion and decision else ''}{decision}"
    if action_text:
        third_para = f"{third_para} 落到本周，{action_text}。"
    fourth_para = next_sentence
    if boundary:
        fourth_para = f"{fourth_para}{boundary}"

    paragraphs = [f"### {title}", first_para, second_para, third_para, fourth_para]
    return _strip_contract_label_text("\n\n".join(part for part in paragraphs if part).strip())


def _render_table_reading_card(cards_payload: dict[str, Any], card_id: str) -> str:
    card = (cards_payload.get("cards") or {}).get(card_id)
    if not isinstance(card, dict):
        return ""
    if card.get("judgement_standard"):
        return render_standard_card_as_narrative(card, NARRATIVE_SECTION_CONTEXT.get(card_id))
    lines = [
        f"{card.get('table_question', '这张表用于把数据读成经营判断。')}",
        f"{card.get('pre_table_conclusion', '当前表格需要结合关键行和后续动作一起判断。')}",
    ]
    for item in list(card.get("key_rows") or [])[:12]:
        lines.append(str(item))
    for action in list(card.get("follow_up_actions") or [])[:5]:
        if isinstance(action, dict):
            lines.append(_action_narrative(action))
        else:
            lines.append(str(action))
    lines.append(f"边界上，{card.get('cannot_infer', '不能只凭单张表推出完整因果链，需要和相邻对象池或复盘指标验证。')}")
    return _strip_contract_label_text("\n\n".join(lines))


def _median(rows: list[dict[str, Any]], column: str) -> float:
    values = sorted(_num(row.get(column)) for row in rows if str(row.get(column) or "").strip())
    if not values:
        return 0.0
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2.0


def _roi_quadrant(row: dict[str, Any], *, roi_mid: float, cac_mid: float) -> str:
    roi_value = _num(row.get("roi"))
    cac_value = _num(row.get("cac"))
    if roi_value >= roi_mid and cac_value <= cac_mid:
        return "加码象限：高 roi / 低 cac"
    if roi_value >= roi_mid and cac_value > cac_mid:
        return "提效象限：高 roi / 高 cac"
    if roi_value < roi_mid and cac_value <= cac_mid:
        return "验证象限：低 roi / 低 cac"
    return "止损象限：低 roi / 高 cac"


def _roi_quadrant_action(quadrant: str) -> str:
    if quadrant.startswith("加码象限"):
        return "优先承接预算迁入，迁入后盯住边际 roi 是否回落"
    if quadrant.startswith("提效象限"):
        return "保留规模，先压 cac 或优化出价结构，再决定是否继续放量"
    if quadrant.startswith("验证象限"):
        return "不急于放量，先用低成本验证转化承接和毛利质量"
    return "Day 1 进入止损或降权池，避免继续吞噬预算"


def _normalize_roi_quadrant_label(quadrant: str) -> str:
    label = str(quadrant or "").strip()
    if not label:
        return ""
    mapping = {
        "加码象限": "加码象限：高 roi / 低 cac",
        "提效象限": "提效象限：高 roi / 高 cac",
        "验证象限": "验证象限：低 roi / 低 cac",
        "止损象限": "止损象限：低 roi / 高 cac",
    }
    for prefix, normalized in mapping.items():
        if label == prefix or label.startswith(prefix + "：") or label.startswith(prefix + ":"):
            return normalized
    return label


def _with_roi_quadrants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roi_mid = _median(rows, "roi")
    cac_mid = _median(rows, "cac")
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        quadrant = _normalize_roi_quadrant_label(item.get("象限") or "") or _roi_quadrant(item, roi_mid=roi_mid, cac_mid=cac_mid)
        item["象限"] = quadrant
        item["建议动作"] = str(item.get("建议动作") or "").strip() or _roi_quadrant_action(quadrant)
        item["结论"] = _roi_quadrant_action(quadrant)
        enriched.append(item)
    return enriched


def _representative_roi_quadrants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = [
        "加码象限：高 roi / 低 cac",
        "提效象限：高 roi / 高 cac",
        "验证象限：低 roi / 低 cac",
        "止损象限：低 roi / 高 cac",
    ]
    sorters = {
        "加码象限：高 roi / 低 cac": lambda row: (-_num(row.get("roi")), _num(row.get("cac"))),
        "提效象限：高 roi / 高 cac": lambda row: (-_num(row.get("operating_cost")), -_num(row.get("roi"))),
        "验证象限：低 roi / 低 cac": lambda row: (_num(row.get("cac")), -_num(row.get("paid_users"))),
        "止损象限：低 roi / 高 cac": lambda row: (-_num(row.get("operating_cost")), -_num(row.get("cac"))),
    }
    representatives: list[dict[str, Any]] = []
    for quadrant in order:
        bucket = [row for row in rows if str(row.get("象限") or "") == quadrant]
        if not bucket:
            representatives.append(
                {
                    "象限": quadrant,
                    "结论": "当前样本未落入该象限，管理上无需为该象限单独配置动作",
                    "图中序号": "-",
                    "channel": "无样本",
                    "traffic_source": "无样本",
                    "paid_users": "",
                    "revenue": "",
                    "operating_cost": "",
                    "roi": "",
                    "cac": "",
                    "建议动作": "不配置动作",
                }
            )
            continue
        item = dict(sorted(bucket, key=sorters[quadrant])[0])
        item["结论"] = _roi_quadrant_action(quadrant)
        representatives.append(item)
    return representatives


MANAGEMENT_QUADRANT_CHARTS = {
    "ops_roi_cac_quadrant": {
        "title": "真实投放回报 × 获客成本象限解读",
        "csv": "ops_roi_cac_quadrant.csv",
        "chart_type": "quadrant",
        "object_dimension": "渠道 × 流量来源",
        "key_columns": ["channel", "traffic_source"],
        "metric_columns": ["roi", "cac", "revenue", "operating_cost", "paid_users"],
        "derived_metric_columns": ["单客付费", "单客毛利", "成本回收倍数", "毛利回收倍数"],
        "band_order": ["加码象限：高 roi / 低 cac", "提效象限：高 roi / 高 cac", "验证象限：低 roi / 低 cac", "止损象限：低 roi / 高 cac"],
    },
    "ops_ctr_cpc_cpm_efficiency": {
        "title": "点击率 × 点击成本获客效率解读",
        "csv": "ops_ctr_cpc_cpm_efficiency.csv",
        "chart_type": "scatter",
        "object_dimension": "渠道 × 流量来源",
        "key_columns": ["channel", "traffic_source"],
        "metric_columns": ["点击率", "CPC", "CPM", "点击到注册率", "激活到付费率", "roi", "cac"],
        "derived_metric_columns": ["单次点击收入", "单次点击毛利", "点击到付费率", "注册到付费率", "单客付费"],
        "band_order": ["有效点击池", "虚高点击池", "贵点击池", "低影响观察池"],
    },
    "ops_cost_margin_share_matrix": {
        "title": "成本占比 × 毛利占比矩阵",
        "csv": "ops_cost_margin_share_matrix.csv",
        "chart_type": "bubble",
        "object_dimension": "渠道 × 流量来源",
        "key_columns": ["channel", "traffic_source"],
        "metric_columns": ["成本占比", "毛利占比", "预算效率", "收入", "运营成本", "贡献毛利"],
        "derived_metric_columns": ["单客付费", "单客毛利", "成本回收倍数", "毛利回收倍数"],
        "band_order": ["花钱产毛利池", "花钱吞毛利池", "低影响观察池"],
    },
    "ops_paid_users_revenue_bubble": {
        "title": "付费用户 × 收入承接气泡图",
        "csv": "ops_paid_users_revenue_bubble.csv",
        "chart_type": "bubble",
        "object_dimension": "产品模块 × 活动",
        "key_columns": ["product_module", "campaign"],
        "metric_columns": ["付费用户", "收入", "贡献毛利", "毛利率", "roi", "cac"],
        "derived_metric_columns": ["单客付费", "单客毛利", "注册价值", "激活价值", "成本回收倍数", "毛利回收倍数"],
        "band_order": ["强承接池", "高收入低效率池", "弱承接修复池", "验证承接池"],
    },
    "ops_retention_nps_quality_quadrant": {
        "title": "留存 × 口碑净推荐值质量象限图（NPS）",
        "csv": "ops_retention_nps_quality_quadrant.csv",
        "chart_type": "quadrant",
        "object_dimension": "用户分层 × 城市层级",
        "key_columns": ["user_segment", "city_tier"],
        "metric_columns": ["retention_d7", "nps", "增长质量分", "付费用户", "收入"],
        "derived_metric_columns": ["单客付费", "单客毛利", "成本回收倍数", "毛利回收倍数"],
        "band_order": ["高质量经营池", "中间验证池", "低质量降权池"],
    },
}


MANAGEMENT_BAND_ACTIONS = {
    "加码象限：高 roi / 低 cac": ("小步迁入预算，监控边际 roi 是否回落", "渠道运营", "Day 2 晚间"),
    "提效象限：高 roi / 高 cac": ("保留规模但先压 cac，再决定是否继续放量", "渠道运营", "Day 4"),
    "验证象限：低 roi / 低 cac": ("只保留低成本样本，验证承接和毛利质量", "活动运营", "Day 7 周复盘"),
    "止损象限：低 roi / 高 cac": ("Day 1 冻结或降权，避免继续吞噬预算", "运营负责人", "Day 1 收盘"),
    "有效点击池": ("保留入口并交叉复核 ROI/CAC，达标后小步放量", "渠道运营", "Day 2 晚间"),
    "虚高点击池": ("先修注册、激活和付费承接，不进入加码池", "内容运营", "Day 4"),
    "贵点击池": ("降权高价点击来源，重配流量包或出价策略", "投放运营", "Day 3"),
    "低影响观察池": ("保留观察，不占用本周预算裁决带宽", "数据分析", "Day 7"),
    "花钱产毛利池": ("保留为迁入候选，复核边际毛利是否继续成立", "渠道运营", "Day 7"),
    "花钱吞毛利池": ("迁出或降权预算，停止用收入规模为低毛利辩护", "运营负责人", "Day 2"),
    "强承接池": ("作为 Day 5 桥接实验承接模块，验证边际毛利", "产品运营", "Day 5"),
    "高收入低效率池": ("保留收入入口，但先修成本、毛利或权益结构", "产品运营", "Day 5"),
    "弱承接修复池": ("修权益和转化路径，未达标前不放量", "活动运营", "Day 7"),
    "验证承接池": ("用小样本承接实验争取扩大资格", "活动运营", "Day 7"),
    "高质量经营池": ("保留并深耕，优先匹配高毛利承接实验", "用户运营", "Day 3"),
    "中间验证池": ("继续验证城市/人群包，不直接扩大预算", "用户运营", "Day 7"),
    "低质量降权池": ("暂停粗放扩量，复核人群包和城市层级", "用户运营", "Day 3"),
}


def _object_from_columns(row: dict[str, Any], columns: list[str]) -> str:
    values = [str(row.get(column) or "").strip() for column in columns]
    values = [value for value in values if value]
    if values:
        return " / ".join(values).replace("|", " / ")
    return _object_label(row)


TOTAL_METRIC_COLUMNS = {
    "revenue",
    "operating_cost",
    "contribution_margin",
    "paid_users",
    "收入",
    "运营成本",
    "贡献毛利",
    "付费用户",
}


WEIGHT_COLUMN_CANDIDATES = {
    "exposure": ["曝光", "impressions"],
    "click": ["点击", "clicks"],
    "registration": ["注册", "registrations"],
    "activation": ["激活", "activations"],
    "paid_user": ["付费用户", "paid_users"],
    "operating_cost": ["运营成本", "operating_cost"],
    "revenue": ["收入", "revenue"],
    "sample_size": ["样本量", "sample_size", "付费用户", "paid_users"],
}


def _metric_range(rows: list[dict[str, Any]], columns: list[str]) -> str:
    parts: list[str] = []
    for column in columns:
        values = [_num(row.get(column)) for row in rows if str(row.get(column) or "").strip()]
        if not values:
            continue
        low = min(values)
        high = max(values)
        if abs(low - high) < 1e-9:
            parts.append(f"{_label(column)} {_fmt_value(column, low)}")
        else:
            parts.append(f"{_label(column)} {_fmt_value(column, low)}-{_fmt_value(column, high)}")
    return "；".join(parts)


def _present_column(rows: list[dict[str, Any]], candidates: list[str]) -> str:
    for candidate in candidates:
        if any(str(row.get(candidate) or "").strip() for row in rows):
            return candidate
    return ""


def _weight_candidates_for_metric(column: str) -> tuple[list[str], str]:
    if column in {"CTR", "点击率", "CPM"}:
        return WEIGHT_COLUMN_CANDIDATES["exposure"], "按曝光加权"
    if column in {"CPC"}:
        return WEIGHT_COLUMN_CANDIDATES["click"], "按点击加权"
    if column == "点击到注册率":
        return WEIGHT_COLUMN_CANDIDATES["click"], "按点击加权"
    if column == "注册到激活率":
        return WEIGHT_COLUMN_CANDIDATES["registration"], "按注册加权"
    if column == "激活到付费率":
        return WEIGHT_COLUMN_CANDIDATES["activation"], "按激活加权"
    if column == "点击到付费率":
        return WEIGHT_COLUMN_CANDIDATES["click"], "按点击加权"
    if column == "注册到付费率":
        return WEIGHT_COLUMN_CANDIDATES["registration"], "按注册加权"
    if column in {"单客付费", "单客毛利", "每付费用户收入"}:
        return WEIGHT_COLUMN_CANDIDATES["paid_user"], "按付费用户加权"
    if column in {"单次点击收入", "单次点击毛利"}:
        return WEIGHT_COLUMN_CANDIDATES["click"], "按点击加权"
    if column == "注册价值":
        return WEIGHT_COLUMN_CANDIDATES["registration"], "按注册加权"
    if column == "激活价值":
        return WEIGHT_COLUMN_CANDIDATES["activation"], "按激活加权"
    if column in {"成本回收倍数", "毛利回收倍数"}:
        return WEIGHT_COLUMN_CANDIDATES["operating_cost"], "按运营成本加权"
    if column in {"roi", "预算效率", "成本占比", "毛利占比"}:
        return WEIGHT_COLUMN_CANDIDATES["operating_cost"], "按运营成本加权"
    if column in {"cac", "获客成本"}:
        return [*WEIGHT_COLUMN_CANDIDATES["paid_user"], *WEIGHT_COLUMN_CANDIDATES["operating_cost"]], "按付费用户加权，缺失时按运营成本兜底"
    if column == "毛利率":
        return WEIGHT_COLUMN_CANDIDATES["revenue"], "按收入加权"
    if column in {"retention_d7", "nps", "留存质量分", "口碑质量分", "增长质量分"}:
        return WEIGHT_COLUMN_CANDIDATES["sample_size"], "按样本量加权，缺失时按付费用户兜底"
    return WEIGHT_COLUMN_CANDIDATES["sample_size"], "按样本量加权"


def _metric_distribution_items(rows: list[dict[str, Any]], columns: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for column in columns:
        values = [_num(row.get(column)) for row in rows if str(row.get(column) or "").strip()]
        if not values:
            continue
        low = min(values)
        high = max(values)
        mean = sum(values) / len(values)
        item: dict[str, Any] = {
            "metric": column,
            "metric_label": _label(column),
            "min": low,
            "max": high,
            "mean": mean,
            "count": len(values),
        }
        if column in TOTAL_METRIC_COLUMNS:
            item["total"] = sum(values)
            item["summary"] = (
                f"{_label(column)}：区间 {_fmt_value(column, low)}-{_fmt_value(column, high)}，"
                f"平均数 {_fmt_value(column, mean)}，合计 {_fmt_value(column, item['total'])}"
            )
            item["weight_policy"] = "总量指标展示合计，不写加权平均"
        else:
            candidates, policy = _weight_candidates_for_metric(column)
            weight_column = _present_column(rows, candidates)
            weighted_mean: float | None = None
            weight_sum = 0.0
            weighted_n = 0
            if weight_column:
                numerator = 0.0
                for row in rows:
                    if not str(row.get(column) or "").strip():
                        continue
                    weight = _num(row.get(weight_column))
                    if weight <= 0:
                        continue
                    numerator += _num(row.get(column)) * weight
                    weight_sum += weight
                    weighted_n += 1
                if weight_sum > 0:
                    weighted_mean = numerator / weight_sum
            item["weighted_mean"] = weighted_mean
            item["weight_column"] = weight_column
            item["weight_policy"] = f"{policy}（权重字段：{_label(weight_column) if weight_column else '无可用权重'}）"
            item["weight_sum"] = weight_sum
            item["weighted_count"] = weighted_n
            weighted_text = _fmt_value(column, weighted_mean) if weighted_mean is not None else "n/a"
            item["summary"] = (
                f"{_label(column)}：区间 {_fmt_value(column, low)}-{_fmt_value(column, high)}，"
                f"平均数 {_fmt_value(column, mean)}，加权平均 {weighted_text}"
            )
        items.append(item)
    return items


def _metric_distribution_summary(rows: list[dict[str, Any]], columns: list[str]) -> str:
    return "；".join(str(item.get("summary") or "") for item in _metric_distribution_items(rows, columns) if item.get("summary"))


def _safe_divide(numerator: Any, denominator: Any) -> float | None:
    denominator_number = _num(denominator)
    if abs(denominator_number) < 1e-12:
        return None
    return _num(numerator) / denominator_number


def _set_derived_metric(row: dict[str, Any], metric: str, value: float | None) -> None:
    if value is None:
        row.pop(metric, None)
        return
    row[metric] = value


def _with_management_derived_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        revenue = _row_number(item, "revenue")
        operating_cost = _row_number(item, "operating_cost")
        contribution_margin = _row_number(item, "contribution_margin")
        paid_users = _row_number(item, "paid_users")
        clicks = _row_number(item, "clicks")
        registrations = _row_number(item, "registrations")
        activations = _row_number(item, "activations")
        _set_derived_metric(item, "单客付费", _safe_divide(revenue, paid_users))
        _set_derived_metric(item, "单客毛利", _safe_divide(contribution_margin, paid_users))
        _set_derived_metric(item, "单次点击收入", _safe_divide(revenue, clicks))
        _set_derived_metric(item, "单次点击毛利", _safe_divide(contribution_margin, clicks))
        _set_derived_metric(item, "注册价值", _safe_divide(revenue, registrations))
        _set_derived_metric(item, "激活价值", _safe_divide(revenue, activations))
        _set_derived_metric(item, "点击到付费率", _safe_divide(paid_users, clicks))
        _set_derived_metric(item, "注册到付费率", _safe_divide(paid_users, registrations))
        _set_derived_metric(item, "成本回收倍数", _safe_divide(revenue, operating_cost))
        _set_derived_metric(item, "毛利回收倍数", _safe_divide(contribution_margin, operating_cost))
        enriched.append(item)
    return enriched


def _metric_weight_policy_summary(items: list[dict[str, Any]]) -> str:
    policies: list[str] = []
    for item in items:
        metric = str(item.get("metric_label") or item.get("metric") or "")
        policy = str(item.get("weight_policy") or "")
        if not metric or not policy:
            continue
        policies.append(f"{metric}{policy}")
    return "；".join(policies)


def _metric_mean_summary(items: list[dict[str, Any]]) -> str:
    return "；".join(
        f"{item.get('metric_label')}: {_fmt_value(str(item.get('metric') or ''), item.get('mean'))}"
        for item in items
        if item.get("mean") is not None
    )


def _metric_weighted_mean_summary(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        metric = str(item.get("metric") or "")
        label = str(item.get("metric_label") or metric)
        if metric in TOTAL_METRIC_COLUMNS:
            total = item.get("total")
            parts.append(f"{label}: 合计 {_fmt_value(metric, total)}")
            continue
        weighted_mean = item.get("weighted_mean")
        if weighted_mean is None:
            parts.append(f"{label}: 加权平均 n/a")
        else:
            parts.append(f"{label}: 加权平均 {_fmt_value(metric, weighted_mean)}")
    return "；".join(parts)


def _band_for_management_chart(chart_id: str, row: dict[str, Any], medians: dict[str, float]) -> str:
    if chart_id == "ops_roi_cac_quadrant":
        return str(row.get("象限") or "").strip() or _roi_quadrant(
            row,
            roi_mid=medians.get("roi", 0.0),
            cac_mid=medians.get("cac", 0.0),
        )
    if chart_id == "ops_ctr_cpc_cpm_efficiency":
        ctr = _num(row.get("CTR") or row.get("点击率"))
        roi = _num(row.get("roi"))
        cpc = _num(row.get("CPC"))
        cac = _num(row.get("cac"))
        if ctr >= medians.get("CTR", 0.0) and roi >= medians.get("roi", 0.0):
            return "有效点击池"
        if ctr >= medians.get("CTR", 0.0) and roi < medians.get("roi", 0.0):
            return "虚高点击池"
        if cpc >= medians.get("CPC", 0.0) or cac >= medians.get("cac", 0.0):
            return "贵点击池"
        return "低影响观察池"
    if chart_id == "ops_cost_margin_share_matrix":
        cost_share = _num(row.get("成本占比"))
        margin_share = _num(row.get("毛利占比"))
        if margin_share >= cost_share:
            return "花钱产毛利池"
        if cost_share > margin_share:
            return "花钱吞毛利池"
        return "低影响观察池"
    if chart_id == "ops_paid_users_revenue_bubble":
        revenue = _num(row.get("收入"))
        roi = _num(row.get("roi"))
        margin_rate = _num(row.get("毛利率"))
        if revenue >= medians.get("收入", 0.0) and roi >= medians.get("roi", 0.0) and margin_rate >= medians.get("毛利率", 0.0):
            return "强承接池"
        if revenue >= medians.get("收入", 0.0) and (roi < medians.get("roi", 0.0) or margin_rate < medians.get("毛利率", 0.0)):
            return "高收入低效率池"
        if revenue < medians.get("收入", 0.0) and roi < medians.get("roi", 0.0):
            return "弱承接修复池"
        return "验证承接池"
    if chart_id == "ops_retention_nps_quality_quadrant":
        growth = _num(row.get("增长质量分"))
        retention = _num(row.get("retention_d7"))
        nps = _num(row.get("nps"))
        if growth >= medians.get("增长质量分", 0.0) and retention >= medians.get("retention_d7", 0.0) and nps >= medians.get("nps", 0.0):
            return "高质量经营池"
        if growth < medians.get("增长质量分", 0.0) and (retention < medians.get("retention_d7", 0.0) or nps < medians.get("nps", 0.0)):
            return "低质量降权池"
        return "中间验证池"
    return "观察池"


def _build_management_chart_rows(chart_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spec = MANAGEMENT_QUADRANT_CHARTS[chart_id]
    if chart_id == "ops_roi_cac_quadrant":
        rows = _with_roi_quadrants(rows)
    median_columns = set(spec.get("metric_columns") or []) | {"roi", "cac", "CTR", "CPC", "收入", "毛利率", "retention_d7", "nps", "增长质量分"}
    medians = {column: _median(rows, column) for column in median_columns}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        band = _band_for_management_chart(chart_id, row, medians)
        grouped.setdefault(band, []).append(row)
    index_rows: list[dict[str, Any]] = []
    for band in list(spec.get("band_order") or grouped.keys()):
        bucket = grouped.get(str(band), [])
        if not bucket and chart_id != "ops_roi_cac_quadrant":
            continue
        bucket_with_derived = _with_management_derived_metrics(bucket)
        objects = [_object_from_columns(row, list(spec.get("key_columns") or [])) for row in bucket]
        ids = [str(row.get("图中序号") or row.get("展示排序") or "").strip() for row in bucket if str(row.get("图中序号") or row.get("展示排序") or "").strip()]
        action, owner, checkpoint = MANAGEMENT_BAND_ACTIONS.get(str(band), ("保留观察，进入周复盘", "运营负责人", "Day 7"))
        metric_columns = list(spec.get("metric_columns") or [])
        derived_metric_columns = list(spec.get("derived_metric_columns") or [])
        metric_distribution = _metric_distribution_items(bucket, metric_columns) if bucket else []
        derived_metric_distribution = _metric_distribution_items(bucket_with_derived, derived_metric_columns) if bucket_with_derived else []
        index_rows.append(
            {
                "chart_id": chart_id,
                "chart_title": spec.get("title", chart_id),
                "chart_type": spec.get("chart_type", ""),
                "source_csv": spec.get("csv", ""),
                "object_dimension": spec.get("object_dimension", ""),
                "band": band,
                "object_count": len(bucket),
                "object_list": "；".join(objects) if objects else "当前样本无对象落入该层",
                "representative_ids": " / ".join(ids[:8]) if ids else "-",
                "metric_range": _metric_range(bucket, metric_columns) if bucket else "-",
                "metric_distribution": metric_distribution,
                "metric_distribution_summary": _metric_distribution_summary(bucket, metric_columns) if bucket else "-",
                "metric_weight_policy": _metric_weight_policy_summary(metric_distribution) if metric_distribution else "-",
                "metric_mean": _metric_mean_summary(metric_distribution) if metric_distribution else "-",
                "metric_weighted_mean": _metric_weighted_mean_summary(metric_distribution) if metric_distribution else "-",
                "derived_metric_distribution": derived_metric_distribution,
                "derived_metric_distribution_summary": _metric_distribution_summary(bucket_with_derived, derived_metric_columns) if bucket_with_derived else "-",
                "derived_metric_weight_policy": _metric_weight_policy_summary(derived_metric_distribution) if derived_metric_distribution else "-",
                "derived_metric_mean": _metric_mean_summary(derived_metric_distribution) if derived_metric_distribution else "-",
                "derived_metric_weighted_mean": _metric_weighted_mean_summary(derived_metric_distribution) if derived_metric_distribution else "-",
                "derived_metric_diagnosis": _build_band_derived_metric_diagnosis(chart_id, str(band), derived_metric_distribution),
                "management_action": action,
                "owner": owner,
                "checkpoint": checkpoint,
            }
        )
    return index_rows


def build_ops_management_quadrant_index(workspace: Path) -> dict[str, Any]:
    asset_dir = workspace / "source_visual_assets"
    rows: list[dict[str, Any]] = []
    chart_payloads: list[dict[str, Any]] = []
    for chart_id, spec in MANAGEMENT_QUADRANT_CHARTS.items():
        source_rows = _read_csv_rows(asset_dir / str(spec["csv"]))
        chart_rows = _build_management_chart_rows(chart_id, source_rows) if source_rows else []
        rows.extend(chart_rows)
        chart_payloads.append(
            {
                "chart_id": chart_id,
                "chart_title": spec.get("title", chart_id),
                "source_csv": spec.get("csv"),
                "object_dimension": spec.get("object_dimension"),
                "band_count": len(chart_rows),
                "source_row_count": len(source_rows),
            }
        )
    return {
        "version": "ops_management_quadrant_index_v3",
        "source": "deterministic_management_quadrant_index",
        "chart_count": len(chart_payloads),
        "row_count": len(rows),
        "rules": {
            "roi_cac_uses_source_quadrant": True,
            "bubble_and_scatter_use_chart_specific_business_bands": True,
            "management_brief_renders_band_object_lists": True,
            "metric_distribution_includes_range_mean_and_weighted_mean": True,
            "derived_metric_distribution_includes_range_mean_and_weighted_mean": True,
            "derived_metrics_are_deterministic_not_cli_calculated": True,
        },
        "charts": chart_payloads,
        "rows": rows,
    }


def write_ops_management_quadrant_index(workspace: Path) -> dict[str, Any]:
    ensure_ops_management_fact_contracts(workspace)
    payload = build_ops_management_quadrant_index(workspace)
    json_path = workspace / MANAGEMENT_QUADRANT_INDEX_JSON_NAME
    csv_path = workspace / MANAGEMENT_QUADRANT_INDEX_CSV_NAME
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    fields = [
        "chart_id",
        "chart_title",
        "chart_type",
        "source_csv",
        "object_dimension",
        "band",
        "object_count",
        "object_list",
        "representative_ids",
        "metric_distribution_summary",
        "metric_weight_policy",
        "metric_mean",
        "metric_weighted_mean",
        "metric_range",
        "derived_metric_distribution_summary",
        "derived_metric_weight_policy",
        "derived_metric_mean",
        "derived_metric_weighted_mean",
        "derived_metric_diagnosis",
        "management_action",
        "owner",
        "checkpoint",
    ]
    _write_csv_rows(csv_path, list(payload.get("rows") or []), fields)
    return payload


def _management_quadrant_rows(payload: dict[str, Any], chart_id: str) -> list[dict[str, Any]]:
    return [row for row in list(payload.get("rows") or []) if isinstance(row, dict) and row.get("chart_id") == chart_id]


def _management_chart_index_question(chart_id: str) -> str:
    questions = {
        "ops_roi_cac_quadrant": "这张表把预算迁出、迁入、提效和验证对象拆开，管理层可以直接看到每个象限里到底有哪些组合，而不是只看一个代表点。",
        "ops_ctr_cpc_cpm_efficiency": "这张表回答前段点击到底有没有进入有效获客，避免把高 CTR 直接误读成可加码对象。",
        "ops_cost_margin_share_matrix": "这张表把“花钱产毛利”和“花钱吞毛利”的对象分开，方便先做利润保卫，再谈扩量。",
        "ops_retention_nps_quality_quadrant": "这张表回答哪些人群值得继续经营、哪些人群该降权，Day 3 的人群动作要从这里落地。",
        "ops_paid_users_revenue_bubble": "这张表回答哪些产品活动真的接住了收入和毛利，哪些只是收入高但承接效率弱。",
    }
    return questions.get(chart_id, "这张表用于把核心对象按同一把经营尺子分层，并把对象清单、指标分布和管理动作放在同一处。")


def _management_chart_band_row(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get("band") or "").startswith(prefix):
            return row
    return {}


def _management_band_summary_line(row: dict[str, Any]) -> str:
    if not row:
        return ""
    band = str(row.get("band") or "未分层")
    object_count = str(row.get("object_count") or "0")
    ids = str(row.get("representative_ids") or "未标注")
    action = str(row.get("management_action") or "待补充")
    diagnosis = str(row.get("derived_metric_diagnosis") or "").strip()
    base = f"{band}当前有{object_count}个对象，代表序号 {ids}，管理动作是{action}。"
    return f"{base}{diagnosis}" if diagnosis else base


def _management_chart_index_summary(chart_id: str, rows: list[dict[str, Any]]) -> str:
    if chart_id == "ops_roi_cac_quadrant":
        scale_up = _management_chart_band_row(rows, "加码象限")
        stoploss = _management_chart_band_row(rows, "止损象限")
        efficiency = _management_chart_band_row(rows, "提效象限")
        verify = _management_chart_band_row(rows, "验证象限")
        lines = [
            _management_band_summary_line(scale_up),
            _management_band_summary_line(stoploss),
            _management_band_summary_line(efficiency),
            _management_band_summary_line(verify),
        ]
    elif chart_id == "ops_ctr_cpc_cpm_efficiency":
        lines = [
            _management_band_summary_line(_management_chart_band_row(rows, "有效点击池")),
            _management_band_summary_line(_management_chart_band_row(rows, "虚高点击池")),
            _management_band_summary_line(_management_chart_band_row(rows, "贵点击池")),
        ]
    elif chart_id == "ops_cost_margin_share_matrix":
        lines = [
            _management_band_summary_line(_management_chart_band_row(rows, "花钱产毛利池")),
            _management_band_summary_line(_management_chart_band_row(rows, "花钱吞毛利池")),
        ]
    elif chart_id == "ops_retention_nps_quality_quadrant":
        lines = [
            _management_band_summary_line(_management_chart_band_row(rows, "高质量经营池")),
            _management_band_summary_line(_management_chart_band_row(rows, "低质量降权池")),
            _management_band_summary_line(_management_chart_band_row(rows, "中间验证池")),
        ]
    elif chart_id == "ops_paid_users_revenue_bubble":
        lines = [
            _management_band_summary_line(_management_chart_band_row(rows, "强承接池")),
            _management_band_summary_line(_management_chart_band_row(rows, "高收入低效率池")),
            _management_band_summary_line(_management_chart_band_row(rows, "弱承接修复池")),
        ]
    else:
        lines = [_management_band_summary_line(row) for row in rows[:3]]
    return "\n\n".join(line for line in lines if line).strip()


def _management_band_row(payload: dict[str, Any], chart_id: str, band_prefix: str) -> dict[str, Any]:
    for row in _management_quadrant_rows(payload, chart_id):
        if str(row.get("band") or "").startswith(band_prefix):
            return row
    return {}


def _derived_metric_diagnosis_card(payload: dict[str, Any], chart_id: str) -> dict[str, Any]:
    for card in list(payload.get("cards") or []):
        if isinstance(card, dict) and card.get("chart_id") == chart_id:
            return card
    return {}


def _derived_metric_diagnosis_text(payload: dict[str, Any], chart_id: str) -> str:
    card = _derived_metric_diagnosis_card(payload, chart_id)
    return _clean_narrative_sentence(card.get("diagnosis") or "")


DERIVED_METRIC_FORMULAS = {
    "单客付费": "收入 / 付费用户",
    "单客毛利": "贡献毛利 / 付费用户",
    "单次点击收入": "收入 / 点击",
    "单次点击毛利": "贡献毛利 / 点击",
    "注册价值": "收入 / 注册",
    "激活价值": "收入 / 激活",
    "点击到付费率": "付费用户 / 点击",
    "注册到付费率": "付费用户 / 注册",
    "成本回收倍数": "收入 / 运营成本",
    "毛利回收倍数": "贡献毛利 / 运营成本",
}


def _derived_metric_spec(metric: str) -> dict[str, Any]:
    candidates, policy = _weight_candidates_for_metric(metric)
    return {
        "metric": metric,
        "metric_label": _label(metric),
        "formula": DERIVED_METRIC_FORMULAS.get(metric, ""),
        "weight_policy": policy,
        "weight_candidates": candidates,
    }


def _derived_object_values(row: dict[str, Any], metrics: list[str]) -> dict[str, str]:
    return {
        metric: _fmt_value(metric, row.get(metric))
        for metric in metrics
        if str(row.get(metric) or "").strip()
    }


def _representative_derived_comparisons(
    *,
    chart_id: str,
    source_rows: list[dict[str, Any]],
    metrics: list[str],
) -> list[dict[str, Any]]:
    enriched = _with_management_derived_metrics(source_rows)
    if not enriched or not metrics:
        return []

    def row_payload(row: dict[str, Any], role: str) -> dict[str, Any]:
        return {
            "role": role,
            "object_name": _object_label(row),
            "chart_point_id": str(row.get("图中序号") or row.get("展示排序") or ""),
            "channel": row.get("channel", ""),
            "traffic_source": row.get("traffic_source", ""),
            "values": _derived_object_values(row, metrics),
            "canonical_kpis": {
                "roi": _fmt_value("roi", row.get("roi")),
                "cac": _fmt_value("cac", row.get("cac")),
                "收入": _fmt_value("收入", row.get("收入") or row.get("revenue")),
                "运营成本": _fmt_value("运营成本", row.get("运营成本") or row.get("operating_cost")),
                "贡献毛利": _fmt_value("贡献毛利", row.get("贡献毛利") or row.get("contribution_margin")),
                "付费用户": _fmt_value("付费用户", row.get("付费用户") or row.get("paid_users")),
            },
        }

    if chart_id == "ops_roi_cac_quadrant":
        scale_rows = [row for row in enriched if str(row.get("象限") or "").startswith("加码象限")]
        stop_rows = [row for row in enriched if str(row.get("象限") or "").startswith("止损象限")]
        best = max(scale_rows or enriched, key=lambda row: _row_number(row, "roi"))
        worst = max(stop_rows or enriched, key=lambda row: _row_number(row, "cac"))
        return [row_payload(best, "迁入代表"), row_payload(worst, "止损代表")]

    primary_metric = metrics[0]
    valid = [row for row in enriched if str(row.get(primary_metric) or "").strip()]
    if not valid:
        return [row_payload(row, "代表对象") for row in enriched[:2]]
    high = max(valid, key=lambda row: _num(row.get(primary_metric)))
    low = min(valid, key=lambda row: _num(row.get(primary_metric)))
    if high is low:
        return [row_payload(high, "代表对象")]
    return [row_payload(high, "高值代表"), row_payload(low, "低值代表")]


def _build_derived_metric_diagnosis_text(chart_id: str, band_rows: list[dict[str, Any]]) -> str:
    band_by_name = {str(row.get("band") or ""): row for row in band_rows}
    if chart_id == "ops_roi_cac_quadrant":
        scale = band_by_name.get("加码象限：高 roi / 低 cac", {})
        stop = band_by_name.get("止损象限：低 roi / 高 cac", {})
        scale_pay = _distribution_summary_value(scale, "单客付费", derived=True)
        stop_pay = _distribution_summary_value(stop, "单客付费", derived=True)
        scale_cac = _distribution_summary_value(scale, "cac")
        stop_cac = _distribution_summary_value(stop, "cac")
        scale_roi = _distribution_summary_value(scale, "roi")
        stop_roi = _distribution_summary_value(stop, "roi")
        return (
            f"ROI/CAC 的派生诊断要把客单和买客成本拆开看：加码池单客付费加权平均 {scale_pay}，止损池为 {stop_pay}，"
            f"但止损池 cac 加权平均 {stop_cac}，明显高于加码池 {scale_cac}；同时止损池 roi 加权平均 {stop_roi}，低于加码池 {scale_roi}。"
            "如果客单相近但买客成本大幅抬高，问题就不是收入承接不足，而是买客过贵和回收效率偏弱，预算应先从止损池迁出。"
        )
    if chart_id == "ops_ctr_cpc_cpm_efficiency":
        effective = band_by_name.get("有效点击池", {})
        expensive = band_by_name.get("贵点击池", {})
        return (
            f"入口效率要看点击后价值：有效点击池单次点击收入加权平均 {_distribution_summary_value(effective, '单次点击收入', derived=True)}、"
            f"单次点击毛利加权平均 {_distribution_summary_value(effective, '单次点击毛利', derived=True)}；贵点击池对应为 "
            f"{_distribution_summary_value(expensive, '单次点击收入', derived=True)} 和 {_distribution_summary_value(expensive, '单次点击毛利', derived=True)}。"
            "点击便宜或 CTR 高都不自动进入加码，只有点击继续转成收入和毛利，入口才有预算放大资格。"
        )
    if chart_id == "ops_cost_margin_share_matrix":
        positive = band_by_name.get("花钱产毛利池", {})
        negative = band_by_name.get("花钱吞毛利池", {})
        return (
            f"成本毛利页的派生诊断看回收倍数：花钱产毛利池毛利回收倍数加权平均 {_distribution_summary_value(positive, '毛利回收倍数', derived=True)}，"
            f"花钱吞毛利池为 {_distribution_summary_value(negative, '毛利回收倍数', derived=True)}；单客毛利分别为 "
            f"{_distribution_summary_value(positive, '单客毛利', derived=True)} 和 {_distribution_summary_value(negative, '单客毛利', derived=True)}。"
            "这能把“有收入”进一步拆成“是否留下毛利”，决定对象是保留迁入资格还是进入降权。"
        )
    if chart_id == "ops_paid_users_revenue_bubble":
        strong = band_by_name.get("强承接池", {})
        weak = band_by_name.get("弱承接修复池", {})
        return (
            f"付费/收入气泡图要看每个付费用户留下多少收入和毛利：强承接池单客付费加权平均 {_distribution_summary_value(strong, '单客付费', derived=True)}、"
            f"单客毛利加权平均 {_distribution_summary_value(strong, '单客毛利', derived=True)}；弱承接修复池对应为 "
            f"{_distribution_summary_value(weak, '单客付费', derived=True)} 和 {_distribution_summary_value(weak, '单客毛利', derived=True)}。"
            "如果付费人数高但单客毛利被压低，动作不是继续买量，而是修产品权益、活动承接或成本结构。"
        )
    if chart_id == "ops_retention_nps_quality_quadrant":
        high = band_by_name.get("高质量经营池", {})
        low = band_by_name.get("低质量降权池", {})
        return (
            f"用户质量页把留存口碑接到商业价值：高质量经营池单客付费加权平均 {_distribution_summary_value(high, '单客付费', derived=True)}、"
            f"单客毛利加权平均 {_distribution_summary_value(high, '单客毛利', derived=True)}；低质量降权池对应为 "
            f"{_distribution_summary_value(low, '单客付费', derived=True)} 和 {_distribution_summary_value(low, '单客毛利', derived=True)}。"
            "只有质量和单客经济性同时站得住的人群，才值得进入 Day 3 后续经营。"
        )
    return "派生指标诊断用于把图表从原始指标分层推进到单客价值、点击价值和回收效率判断。"


def build_ops_derived_metric_diagnosis_cards(
    workspace: Path,
    management_quadrant_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    management_quadrant_payload = management_quadrant_payload or build_ops_management_quadrant_index(workspace)
    asset_dir = workspace / "source_visual_assets"
    cards: list[dict[str, Any]] = []
    for chart_id, spec in MANAGEMENT_QUADRANT_CHARTS.items():
        band_rows = _management_quadrant_rows(management_quadrant_payload, chart_id)
        source_rows = _read_csv_rows(asset_dir / str(spec.get("csv") or ""))
        metrics = list(spec.get("derived_metric_columns") or [])
        band_comparisons = [
            {
                "band": row.get("band", ""),
                "object_count": row.get("object_count", 0),
                "derived_metric_distribution": row.get("derived_metric_distribution", []),
                "derived_metric_distribution_summary": row.get("derived_metric_distribution_summary", ""),
                "derived_metric_diagnosis": row.get("derived_metric_diagnosis", ""),
                "management_action": row.get("management_action", ""),
                "owner": row.get("owner", ""),
                "checkpoint": row.get("checkpoint", ""),
            }
            for row in band_rows
        ]
        representative_comparisons = _representative_derived_comparisons(
            chart_id=chart_id,
            source_rows=source_rows,
            metrics=metrics,
        )
        diagnosis = _build_derived_metric_diagnosis_text(chart_id, band_rows)
        cards.append(
            {
                "chart_id": chart_id,
                "chart_title": spec.get("title", chart_id),
                "business_question": f"{spec.get('title', chart_id)} 如何从原始指标推进到单客价值、点击价值和回收效率判断？",
                "derived_metrics": [_derived_metric_spec(metric) for metric in metrics],
                "band_comparisons": band_comparisons,
                "representative_object_comparisons": representative_comparisons,
                "diagnosis": diagnosis,
                "action_implication": "CLI 写作必须把派生指标接到预算迁入、降权、承接修复或 Day 动作，不能停留在指标解释。",
                "numbers_to_quote": [
                    text
                    for text in [
                        diagnosis,
                        *[str(row.get("derived_metric_distribution_summary") or "") for row in band_rows[:3]],
                    ]
                    if text
                ],
            }
        )
    return {
        "version": "ops_derived_metric_diagnosis_cards_v1",
        "source": "deterministic_management_derived_metric_diagnosis",
        "card_count": len(cards),
        "rules": {
            "derived_metrics_are_backend_calculated": True,
            "runtime_cli_must_write_long_form_diagnosis": True,
            "minimum_derived_metrics_per_core_chart": 2,
        },
        "cards": cards,
    }


def write_ops_derived_metric_diagnosis_cards(
    workspace: Path,
    management_quadrant_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = build_ops_derived_metric_diagnosis_cards(workspace, management_quadrant_payload)
    (workspace / DERIVED_METRIC_DIAGNOSIS_CARDS_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def _metric_distribution_fact(index_row: dict[str, Any], metric: str) -> str:
    for item in list(index_row.get("metric_distribution") or []):
        if not isinstance(item, dict) or str(item.get("metric") or "") != metric:
            continue
        label = str(item.get("metric_label") or metric)
        low = _fmt_value(metric, item.get("min"))
        high = _fmt_value(metric, item.get("max"))
        mean = _fmt_value(metric, item.get("mean"))
        if metric in TOTAL_METRIC_COLUMNS:
            return f"{label}区间 {low}-{high}、平均数 {mean}、合计 {_fmt_value(metric, item.get('total'))}"
        weighted = item.get("weighted_mean")
        weighted_text = _fmt_value(metric, weighted) if weighted is not None else "n/a"
        return f"{label}区间 {low}-{high}、平均数 {mean}、加权平均 {weighted_text}"
    return ""


def _distribution_item(payload: dict[str, Any], metric: str, *, derived: bool = False) -> dict[str, Any]:
    key = "derived_metric_distribution" if derived else "metric_distribution"
    for item in list(payload.get(key) or []):
        if isinstance(item, dict) and str(item.get("metric") or "") == metric:
            return item
    return {}


def _distribution_weighted_value(payload: dict[str, Any], metric: str, *, derived: bool = False) -> float:
    item = _distribution_item(payload, metric, derived=derived)
    if item.get("weighted_mean") is not None:
        return _num(item.get("weighted_mean"))
    return _num(item.get("mean"))


def _distribution_summary_value(payload: dict[str, Any], metric: str, *, derived: bool = False) -> str:
    item = _distribution_item(payload, metric, derived=derived)
    if not item:
        return ""
    value = item.get("weighted_mean") if item.get("weighted_mean") is not None else item.get("mean")
    return _fmt_value(metric, value)


def _build_band_derived_metric_diagnosis(chart_id: str, band: str, derived_items: list[dict[str, Any]]) -> str:
    if not derived_items:
        return "-"
    item_by_metric = {str(item.get("metric") or ""): item for item in derived_items if isinstance(item, dict)}

    def weighted(metric: str) -> str:
        item = item_by_metric.get(metric) or {}
        value = item.get("weighted_mean") if item.get("weighted_mean") is not None else item.get("mean")
        return _fmt_value(metric, value)

    if chart_id == "ops_roi_cac_quadrant":
        return f"{band}按单客付费、单客毛利和回收倍数判断预算质量；单客付费加权平均 {weighted('单客付费')}，单客毛利加权平均 {weighted('单客毛利')}，毛利回收倍数加权平均 {weighted('毛利回收倍数')}。"
    if chart_id == "ops_ctr_cpc_cpm_efficiency":
        return f"{band}按点击之后的收入和毛利承接判断入口质量；单次点击收入加权平均 {weighted('单次点击收入')}，单次点击毛利加权平均 {weighted('单次点击毛利')}，点击到付费率加权平均 {weighted('点击到付费率')}。"
    if chart_id == "ops_cost_margin_share_matrix":
        return f"{band}按单客毛利和成本回收效率判断是否花钱产毛利；单客毛利加权平均 {weighted('单客毛利')}，成本回收倍数加权平均 {weighted('成本回收倍数')}，毛利回收倍数加权平均 {weighted('毛利回收倍数')}。"
    if chart_id == "ops_paid_users_revenue_bubble":
        return f"{band}按单客付费、单客毛利和阶段价值判断商业承接；单客付费加权平均 {weighted('单客付费')}，单客毛利加权平均 {weighted('单客毛利')}，激活价值加权平均 {weighted('激活价值')}。"
    if chart_id == "ops_retention_nps_quality_quadrant":
        return f"{band}按质量对象的单客收入和单客毛利判断经营价值；单客付费加权平均 {weighted('单客付费')}，单客毛利加权平均 {weighted('单客毛利')}，毛利回收倍数加权平均 {weighted('毛利回收倍数')}。"
    return "派生指标用于把表内对象从规模读数转成经营价值判断。"


def _channel_source_key(row: dict[str, Any]) -> str:
    return f"{str(row.get('channel') or '').strip()}||{str(row.get('traffic_source') or '').strip()}"


def _row_number(row: dict[str, Any], field: str) -> float:
    value = row.get(field)
    if (value is None or str(value).strip() == "") and field in CANONICAL_ALIAS_FIELDS:
        for alias in CANONICAL_ALIAS_FIELDS[field]:
            if str(row.get(alias) or "").strip():
                value = row.get(alias)
                break
    return _num(value)


def _canonical_number_text(value: Any, *, digits: int = 6) -> str:
    number = _num(value)
    if abs(number) < 1e-12:
        return "0"
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def build_ops_channel_source_kpi_canonical(workspace: Path) -> dict[str, Any]:
    source_path = workspace / "source_visual_assets" / "ops_roi_cac_quadrant.csv"
    records: list[dict[str, Any]] = []
    for row in _read_csv_rows(source_path):
        channel = str(row.get("channel") or "").strip()
        traffic_source = str(row.get("traffic_source") or "").strip()
        if not channel or not traffic_source:
            continue
        record: dict[str, Any] = {
            "object_key": _channel_source_key(row),
            "channel": channel,
            "traffic_source": traffic_source,
            "对象组合": f"{channel} / {traffic_source}",
        }
        for field in CANONICAL_CHANNEL_SOURCE_KPI_FIELDS:
            record[field] = _row_number(row, field)
        revenue = _num(record.get("revenue"))
        operating_cost = _num(record.get("operating_cost"))
        paid_users = _num(record.get("paid_users"))
        record["roi"] = revenue / operating_cost if operating_cost else _num(record.get("roi"))
        record["cac"] = operating_cost / paid_users if paid_users else _num(record.get("cac"))
        record["毛利率"] = _num(record.get("contribution_margin")) / revenue if revenue else 0.0
        record["预算效率"] = _num(record.get("contribution_margin")) / operating_cost if operating_cost else 0.0
        records.append(record)
    records = sorted(records, key=lambda item: (str(item.get("channel") or ""), str(item.get("traffic_source") or "")))
    return {
        "version": "ops_channel_source_kpi_canonical_v1",
        "source": "source_visual_assets/ops_roi_cac_quadrant.csv",
        "grain": "channel × traffic_source",
        "key_fields": ["channel", "traffic_source"],
        "canonical_fields": CANONICAL_CHANNEL_SOURCE_KPI_FIELDS,
        "row_count": len(records),
        "rules": {
            "same_object_same_kpis_across_channel_source_charts": True,
            "roi_formula": "revenue / operating_cost",
            "cac_formula": "operating_cost / paid_users",
            "chart_csvs_may_add_visual_metrics_but_must_not_override_canonical_kpis": True,
        },
        "records": records,
    }


def write_ops_channel_source_kpi_canonical(workspace: Path) -> dict[str, Any]:
    payload = build_ops_channel_source_kpi_canonical(workspace)
    (workspace / CHANNEL_SOURCE_KPI_CANONICAL_JSON_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    _write_csv_rows(
        workspace / CHANNEL_SOURCE_KPI_CANONICAL_CSV_NAME,
        list(payload.get("records") or []),
        ["object_key", "channel", "traffic_source", "对象组合", *CANONICAL_CHANNEL_SOURCE_KPI_FIELDS, "毛利率", "预算效率"],
    )
    return payload


def build_ops_metric_semantics_contract(workspace: Path) -> dict[str, Any]:
    return {
        "version": "ops_metric_semantics_contract_v1",
        "source": "deterministic_internet_ops_metric_semantics",
        "grain_rule": "所有 reader-facing 指标先按对象粒度聚合分子分母，再计算比例/效率；禁止把行级均值展示为经营 KPI。",
        "legacy_fields": {
            "ROI": {
                "status": "legacy_source_field",
                "reader_facing_rule": "只能出现在全字段覆盖表的字段名列，不能进入经营结论、分层、Day 动作或 Owner 指标。",
            },
            "roi_avg": {
                "status": "deprecated_reader_field",
                "reader_facing_rule": "旧名兼容时必须等价于 sum(revenue)/sum(operating_cost)，不得使用 row mean。",
            },
            "cac_avg": {
                "status": "deprecated_reader_field",
                "reader_facing_rule": "旧名兼容时必须等价于 sum(operating_cost)/sum(paid_users)，不得使用 row mean。",
            },
            "cpc_avg": {
                "status": "deprecated_reader_field",
                "reader_facing_rule": "旧名兼容时必须等价于 sum(operating_cost)/sum(clicks)，不得使用源表 CPC 均值。",
            },
            "cpm_avg": {
                "status": "deprecated_reader_field",
                "reader_facing_rule": "旧名兼容时必须等价于 sum(operating_cost)*1000/sum(impressions)，不得使用源表 CPM 均值。",
            },
        },
        "metrics": {
            "roi": {"label": "真实投放回报（roi）", "formula": "sum(revenue) / sum(operating_cost)", "weight_grain": "operating_cost"},
            "cac": {"label": "获客成本（cac）", "formula": "sum(operating_cost) / sum(paid_users)", "weight_grain": "paid_users"},
            "CTR": {"label": "点击率（CTR）", "formula": "sum(clicks) / sum(impressions)", "weight_grain": "impressions"},
            "CPC": {"label": "单次点击成本（CPC）", "formula": "sum(operating_cost) / sum(clicks)", "weight_grain": "clicks"},
            "CPM": {"label": "千次曝光成本（CPM）", "formula": "sum(operating_cost) * 1000 / sum(impressions)", "weight_grain": "impressions"},
            "点击到注册率": {"formula": "sum(registrations) / sum(clicks)", "weight_grain": "clicks"},
            "注册到激活率": {"formula": "sum(activations) / sum(registrations)", "weight_grain": "registrations"},
            "激活到付费率": {"formula": "sum(paid_users) / sum(activations)", "weight_grain": "activations"},
            "点击到付费率": {"formula": "sum(paid_users) / sum(clicks)", "weight_grain": "clicks"},
            "每付费用户收入": {"formula": "sum(revenue) / sum(paid_users)", "weight_grain": "paid_users"},
            "单客付费": {"formula": "sum(revenue) / sum(paid_users)", "weight_grain": "paid_users"},
            "单客毛利": {"formula": "sum(contribution_margin) / sum(paid_users)", "weight_grain": "paid_users"},
            "注册价值": {"formula": "sum(revenue) / sum(registrations)", "weight_grain": "registrations"},
            "激活价值": {"formula": "sum(revenue) / sum(activations)", "weight_grain": "activations"},
            "毛利率": {"formula": "sum(contribution_margin) / sum(revenue)", "weight_grain": "revenue"},
            "预算效率": {"formula": "sum(contribution_margin) / sum(operating_cost)", "weight_grain": "operating_cost"},
            "成本回收倍数": {"formula": "sum(revenue) / sum(operating_cost)", "weight_grain": "operating_cost"},
            "毛利回收倍数": {"formula": "sum(contribution_margin) / sum(operating_cost)", "weight_grain": "operating_cost"},
        },
        "required_canonical_grains": [
            "渠道 × 流量来源",
            "用户分层 × 城市层级",
            "内容类型 × 活动",
            "产品模块 × 活动",
            "时间窗口",
        ],
        "blocking_rules": {
            "runtime_cli_may_write_prose_only": True,
            "runtime_cli_must_not_calculate_or_replace_numbers": True,
            "all_numbers_must_trace_to_contract_or_csv": True,
            "formula_mismatches_block_ops_review_and_pdf_render": True,
        },
    }


def write_ops_metric_semantics_contract(workspace: Path) -> dict[str, Any]:
    payload = build_ops_metric_semantics_contract(workspace)
    (workspace / METRIC_SEMANTICS_CONTRACT_JSON_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def build_ops_consistency_issue_registry(workspace: Path) -> dict[str, Any]:
    issue_specs = [
        ("OPS-001", "same_object_kpi_conflict", "Xiaohongshu / crm_push 在不同章节 roi/cac 冲突", "same_object_same_kpis_across_channel_source_charts", "internet_ops_channel_source_kpi_gate", "ops_review"),
        ("OPS-002", "same_object_kpi_conflict", "Douyin / crm_push 在不同章节 roi/cac 冲突", "same_object_same_kpis_across_channel_source_charts", "internet_ops_channel_source_kpi_gate", "ops_review"),
        ("OPS-003", "same_object_kpi_conflict", "Xiaohongshu / kol_content 在不同章节 roi/cac/转化率冲突", "same_object_same_kpis_across_channel_source_charts", "internet_ops_channel_source_kpi_gate", "ops_review"),
        ("OPS-004", "legacy_roi_mixed_usage", "ROI 与 roi 混用进入经营结论", "ROI legacy only; roi canonical", "internet_ops_metric_semantics_gate", "ops_review"),
        ("OPS-005", "point_id_scope_conflict", "B01/B02 跨图复用且无图级前缀", "chart-scoped ids such as roi_B01 / ctr_B01", "internet_ops_visual_id_scope_gate", "ops_review"),
        ("OPS-006", "ctr_band_conflict", "同对象 CTR 分层互相打架", "one primary band per object; composite label for boundary", "internet_ops_band_exclusivity_gate", "ops_review"),
        ("OPS-007", "ctr_band_conflict", "有效点击/贵点击/虚高点击互相覆盖", "mutually exclusive bands", "internet_ops_band_exclusivity_gate", "ops_review"),
        ("OPS-008", "ctr_band_conflict", "CTR/CPC/CPM 复合状态未标边界", "boundary objects marked explicitly", "internet_ops_band_exclusivity_gate", "ops_review"),
        ("OPS-009", "threshold_explanation_missing", "ROI/CAC 临界对象未解释阈值", "threshold source + mean + median + weighted mean + border band", "internet_ops_threshold_gate", "ops_review"),
        ("OPS-010", "fact hallucination", "Douyin / paid_media 正文出现运营成本 0", "text values must match canonical facts", "internet_ops_fact_backcheck_gate", "ops_review"),
        ("OPS-011", "fact hallucination", "Douyin / crm_push 正文出现贡献毛利 0", "text values must match canonical facts", "internet_ops_fact_backcheck_gate", "ops_review"),
        ("OPS-012", "action_date_conflict", "Douyin / paid_media 动作日期/动作类型冲突", "object action adjudication table", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-013", "action_date_conflict", "Douyin / kol_content 动作日期/动作类型冲突", "object action adjudication table", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-014", "gross_margin_formula_error", "data_dashboard / always_on 毛利率与收入/贡献毛利不符", "gross_margin_rate = contribution_margin / revenue", "internet_ops_formula_gate", "ops_review"),
        ("OPS-015", "gross_margin_formula_error", "template_market / winback 毛利率错误", "gross_margin_rate = contribution_margin / revenue", "internet_ops_formula_gate", "ops_review"),
        ("OPS-016", "gross_margin_formula_error", "产品商业化表毛利率口径错误", "gross_margin_rate = contribution_margin / revenue", "internet_ops_formula_gate", "ops_review"),
        ("OPS-017", "gross_margin_formula_error", "高收入低效率对象毛利率错算", "gross_margin_rate = contribution_margin / revenue", "internet_ops_formula_gate", "ops_review"),
        ("OPS-018", "gross_margin_formula_error", "低收入对象毛利率错算", "gross_margin_rate = contribution_margin / revenue", "internet_ops_formula_gate", "ops_review"),
        ("OPS-019", "gross_margin_formula_error", "商业化承接表毛利率与贡献毛利不闭合", "gross_margin_rate = contribution_margin / revenue", "internet_ops_formula_gate", "ops_review"),
        ("OPS-020", "gross_margin_formula_error", "管理版毛利率文字与表格不一致", "gross_margin_rate = contribution_margin / revenue", "internet_ops_fact_backcheck_gate", "ops_review"),
        ("OPS-021", "gross_margin_formula_error", "完整表长版毛利率与主报告不一致", "gross_margin_rate = contribution_margin / revenue", "internet_ops_artifact_freshness_gate", "ops_pdf_render"),
        ("OPS-022", "user_quality_band_conflict", "用户质量分层阈值重叠", "mutually exclusive user-quality thresholds", "internet_ops_band_exclusivity_gate", "ops_review"),
        ("OPS-023", "user_quality_action_mismatch", "用户质量执行对象没有承接用户质量分析段", "Day action object must come from user-quality canonical", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-024", "user_quality_band_conflict", "用户质量高/低/验证池标签冲突", "one primary user-quality band per object", "internet_ops_band_exclusivity_gate", "ops_review"),
        ("OPS-025", "budget_migration_conflict", "Day 2 主迁入对象不来自 ROI/CAC 迁入池", "Day 2 migration object from ROI/CAC scale-up band", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-026", "budget_migration_conflict", "Xiaohongshu / crm_push 日期/owner 冲突", "single adjudicated action sequence per object", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-027", "commercial_object_conflict", "Day 5 对象不来自产品模块 × 活动 canonical", "Day 5 object from product_module × campaign canonical", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-028", "commercial_metric_mismatch", "template_market / winback 使用不存在或不匹配字段", "success metric belongs to product campaign grain", "internet_ops_metric_grain_gate", "ops_review"),
        ("OPS-029", "commercial_metric_mismatch", "产品表用 retention_d7 做商业承接成功指标", "product campaign uses revenue/margin/paid metrics", "internet_ops_metric_grain_gate", "ops_review"),
        ("OPS-030", "unsupported_joint_object", "Day 1 五维对象硬拼", "no five-dimensional joint object unless canonical exists", "internet_ops_object_grain_gate", "ops_review"),
        ("OPS-031", "unsupported_joint_object", "冻结对象拼接渠道/流量/用户/城市/产品", "Day object must match existing canonical grain", "internet_ops_object_grain_gate", "ops_review"),
        ("OPS-032", "unsupported_joint_object", "Day 表生成未在任何 canonical 出现的联合对象", "Day object must match existing canonical grain", "internet_ops_object_grain_gate", "ops_review"),
        ("OPS-033", "owner_extra_object", "Owner 表新增 Day 表没有的对象", "Owner table object subset of Day action objects", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-034", "owner_extra_object", "Owner 日程和 Day 表对象不一致", "Owner table object subset of Day action objects", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-035", "missing_upstream_evidence", "Day 4 内容动作缺内容 × 活动证据", "Day 4 requires content_campaign canonical and analysis section", "internet_ops_day_owner_consistency_gate", "ops_review"),
        ("OPS-036", "owner_role_compression", "责任角色压扁成运营负责人 + 数据分析", "distinct channel/user/content/product/ops owner roles", "internet_ops_owner_role_gate", "ops_review"),
        ("OPS-037", "success_metric_grain_mismatch", "检查指标粒度不匹配", "success metric belongs to object grain", "internet_ops_metric_grain_gate", "ops_review"),
        ("OPS-038", "day6_metric_omission", "Day 6 复核指标遗漏 cac/contribution_margin/gross_margin_rate/budget_efficiency", "Day 6 must include required review metrics", "internet_ops_day6_metric_gate", "ops_review"),
    ]
    issues = [
        {
            "issue_id": issue_id,
            "issue_type": issue_type,
            "forbidden_pattern": forbidden_pattern,
            "expected_contract": expected_contract,
            "validator_name": validator_name,
            "blocking_stage": blocking_stage,
        }
        for issue_id, issue_type, forbidden_pattern, expected_contract, validator_name, blocking_stage in issue_specs
    ]
    return {
        "version": "ops_consistency_issue_registry_v1",
        "source": "报告口径不一致问题清单(1).docx",
        "issue_count": len(issues),
        "rules": {
            "all_issues_are_blocking": True,
            "ops_review_blocks_reader_artifact_registration": True,
            "ops_pdf_render_rechecks_artifact_freshness": True,
        },
        "issues": issues,
    }


def write_ops_consistency_issue_registry(workspace: Path) -> dict[str, Any]:
    payload = build_ops_consistency_issue_registry(workspace)
    (workspace / CONSISTENCY_ISSUE_REGISTRY_JSON_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def _sync_channel_source_derived_fields(row: dict[str, Any], fields: list[str], record: dict[str, Any], totals: dict[str, float]) -> None:
    def set_field(field: str, value: Any) -> None:
        row[field] = _canonical_number_text(value)
        if field not in fields:
            fields.append(field)

    impressions = _num(record.get("impressions"))
    clicks = _num(record.get("clicks"))
    registrations = _num(record.get("registrations"))
    activations = _num(record.get("activations"))
    paid_users = _num(record.get("paid_users"))
    revenue = _num(record.get("revenue"))
    operating_cost = _num(record.get("operating_cost"))
    contribution_margin = _num(record.get("contribution_margin"))
    derived_values = {
        "点击率": _safe_divide(clicks, impressions),
        "CTR": _safe_divide(clicks, impressions),
        "点击到注册率": _safe_divide(registrations, clicks),
        "注册到激活率": _safe_divide(activations, registrations),
        "激活到付费率": _safe_divide(paid_users, activations),
        "点击到付费率": _safe_divide(paid_users, clicks),
        "每付费用户收入": _safe_divide(revenue, paid_users),
        "单客付费": _safe_divide(revenue, paid_users),
        "单客毛利": _safe_divide(contribution_margin, paid_users),
        "单次点击收入": _safe_divide(revenue, clicks),
        "单次点击毛利": _safe_divide(contribution_margin, clicks),
        "注册价值": _safe_divide(revenue, registrations),
        "激活价值": _safe_divide(revenue, activations),
        "获客成本": _safe_divide(operating_cost, paid_users),
        "cac": _safe_divide(operating_cost, paid_users),
        "注册成本": _safe_divide(operating_cost, registrations),
        "激活成本": _safe_divide(operating_cost, activations),
        "毛利率": _safe_divide(contribution_margin, revenue),
        "roi": _safe_divide(revenue, operating_cost),
        "预算效率": _safe_divide(contribution_margin, operating_cost),
        "成本回收倍数": _safe_divide(revenue, operating_cost),
        "毛利回收倍数": _safe_divide(contribution_margin, operating_cost),
        "CPC": _safe_divide(operating_cost, clicks),
        "CPM": _safe_divide(operating_cost * 1000, impressions),
    }
    for field, value in derived_values.items():
        if field in row and value is not None:
            set_field(field, value)
    share_values = {
        "成本占比": _safe_divide(operating_cost, totals.get("operating_cost")),
        "毛利占比": _safe_divide(contribution_margin, totals.get("contribution_margin")),
        "收入占比": _safe_divide(revenue, totals.get("revenue")),
        "付费用户占比": _safe_divide(paid_users, totals.get("paid_users")),
    }
    for field, value in share_values.items():
        if field in row and value is not None:
            set_field(field, value)


def sync_channel_source_visual_kpis(workspace: Path, canonical_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    canonical_payload = canonical_payload or write_ops_channel_source_kpi_canonical(workspace)
    canonical_by_key = {
        str(record.get("object_key") or ""): record
        for record in list(canonical_payload.get("records") or [])
        if isinstance(record, dict)
    }
    canonical_totals = {
        "operating_cost": sum(_num(row.get("operating_cost")) for row in canonical_by_key.values()),
        "contribution_margin": sum(_num(row.get("contribution_margin")) for row in canonical_by_key.values()),
        "revenue": sum(_num(row.get("revenue")) for row in canonical_by_key.values()),
        "paid_users": sum(_num(row.get("paid_users")) for row in canonical_by_key.values()),
    }
    asset_dir = workspace / "source_visual_assets"
    chart_files = [
        "ops_channel_source_derived_heatmap.csv",
        "ops_channel_source_aarrr_detail.csv",
        "ops_channel_source_aarrr_topn_small_multiples.csv",
        "ops_ctr_cpc_cpm_efficiency.csv",
        "ops_cost_margin_share_matrix.csv",
    ]
    synced: list[dict[str, Any]] = []
    for filename in chart_files:
        path = asset_dir / filename
        rows = _read_csv_rows(path)
        if not rows:
            continue
        fields = list(rows[0].keys())

        def set_field(row: dict[str, Any], field: str, value: Any) -> None:
            row[field] = _canonical_number_text(value)
            if field not in fields:
                fields.append(field)

        matched = 0
        for row in rows:
            record = canonical_by_key.get(_channel_source_key(row))
            if not record:
                continue
            matched += 1
            for field in CANONICAL_CHANNEL_SOURCE_KPI_FIELDS:
                if field in row:
                    set_field(row, field, record.get(field))
                for alias in CANONICAL_ALIAS_FIELDS.get(field, []):
                    if alias in row:
                        set_field(row, alias, record.get(field))
            if "roi" in row:
                set_field(row, "roi", record.get("roi"))
            if "cac" in row:
                set_field(row, "cac", record.get("cac"))
            _sync_channel_source_derived_fields(row, fields, record, canonical_totals)
            if "对象组合" in row:
                row["对象组合"] = f"{record.get('channel')} × {record.get('traffic_source')}"
        _write_csv_rows(path, rows, fields)
        synced.append({"file": filename, "row_count": len(rows), "matched_count": matched})
    return {"canonical_row_count": len(canonical_by_key), "synced_files": synced}


def _weighted_average(rows: list[dict[str, Any]], metric: str, weight_candidates: list[str]) -> float | None:
    weight_column = _present_column(rows, weight_candidates)
    if not weight_column:
        return None
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        if not str(row.get(metric) or "").strip():
            continue
        weight = _num(row.get(weight_column))
        if weight <= 0:
            continue
        numerator += _num(row.get(metric)) * weight
        denominator += weight
    return numerator / denominator if denominator else None


def _threshold_metric_summary(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    values = [_num(row.get(metric)) for row in rows if str(row.get(metric) or "").strip()]
    candidates, policy = _weight_candidates_for_metric(metric)
    weighted = _weighted_average(rows, metric, candidates)
    return {
        "metric": metric,
        "metric_label": _label(metric),
        "count": len(values),
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
        "mean": (sum(values) / len(values)) if values else 0.0,
        "median": _median(rows, metric),
        "weighted_mean": weighted,
        "weight_policy": policy,
    }


def build_ops_management_thresholds(workspace: Path) -> dict[str, Any]:
    asset_dir = workspace / "source_visual_assets"
    chart_thresholds: list[dict[str, Any]] = []
    for chart_id, spec in MANAGEMENT_QUADRANT_CHARTS.items():
        rows = _read_csv_rows(asset_dir / str(spec["csv"]))
        if not rows:
            continue
        if chart_id == "ops_roi_cac_quadrant":
            rows = _with_roi_quadrants(rows)
        metrics = list(dict.fromkeys(list(spec.get("metric_columns") or []) + ["roi", "cac"]))
        summaries = [
            _threshold_metric_summary(rows, metric)
            for metric in metrics
            if any(str(row.get(metric) or "").strip() for row in rows)
        ]
        borderline: list[dict[str, Any]] = []
        if chart_id == "ops_roi_cac_quadrant":
            roi_mid = _median(rows, "roi")
            cac_mid = _median(rows, "cac")
            for row in rows:
                near_roi = bool(roi_mid and abs(_num(row.get("roi")) - roi_mid) / abs(roi_mid) <= 0.05)
                near_cac = bool(cac_mid and abs(_num(row.get("cac")) - cac_mid) / abs(cac_mid) <= 0.05)
                if near_roi or near_cac:
                    borderline.append(
                        {
                            "object_name": _object_from_columns(row, ["channel", "traffic_source"]),
                            "图中序号": row.get("图中序号") or "",
                            "roi": _num(row.get("roi")),
                            "cac": _num(row.get("cac")),
                            "reason": "接近 roi 或 cac 中位数切线 5% 边界带，管理上按边界对象处理",
                        }
                    )
        chart_thresholds.append(
            {
                "chart_id": chart_id,
                "chart_title": spec.get("title", chart_id),
                "threshold_basis": "中位数切线；ROI/CAC 图额外标记 5% 边界带",
                "border_band_pct": 0.05,
                "metric_summaries": summaries,
                "borderline_objects": borderline,
            }
        )
    return {
        "version": "ops_management_thresholds_v1",
        "source": "deterministic_management_thresholds",
        "rules": {
            "thresholds_must_be_explained_in_management_brief": True,
            "near_threshold_objects_are_borderline_not_hard_binary": True,
        },
        "charts": chart_thresholds,
    }


def write_ops_management_thresholds(workspace: Path) -> dict[str, Any]:
    payload = build_ops_management_thresholds(workspace)
    (workspace / MANAGEMENT_THRESHOLDS_JSON_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def _threshold_chart(payload: dict[str, Any], chart_id: str) -> dict[str, Any]:
    for chart in list(payload.get("charts") or []):
        if isinstance(chart, dict) and chart.get("chart_id") == chart_id:
            return chart
    return {}


def _threshold_metric(payload: dict[str, Any], chart_id: str, metric: str) -> dict[str, Any]:
    chart = _threshold_chart(payload, chart_id)
    for item in list(chart.get("metric_summaries") or []):
        if isinstance(item, dict) and item.get("metric") == metric:
            return item
    return {}


def _threshold_line(payload: dict[str, Any], chart_id: str, metric: str) -> str:
    item = _threshold_metric(payload, chart_id, metric)
    if not item:
        return f"{_label(metric)}暂无阈值"
    weighted = item.get("weighted_mean")
    weighted_text = _fmt_value(metric, weighted) if weighted is not None else "n/a"
    return (
        f"{_label(metric)}中位数 {_fmt_value(metric, item.get('median'))}、"
        f"平均数 {_fmt_value(metric, item.get('mean'))}、加权平均 {weighted_text}"
    )


def build_ops_executive_action_rules(workspace: Path, thresholds_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds_payload = thresholds_payload or build_ops_management_thresholds(workspace)
    asset_dir = workspace / "source_visual_assets"
    roi_rows = _with_roi_quadrants(_read_csv_rows(asset_dir / "ops_roi_cac_quadrant.csv"))
    ctr_rows = _read_csv_rows(asset_dir / "ops_ctr_cpc_cpm_efficiency.csv")
    cost_rows = _read_csv_rows(asset_dir / "ops_cost_margin_share_matrix.csv")
    paid_rows = _read_csv_rows(asset_dir / "ops_paid_users_revenue_bubble.csv")
    quality_rows = _read_csv_rows(asset_dir / "ops_retention_nps_quality_quadrant.csv")
    roi_reps = _representative_roi_quadrants(roi_rows)
    scale_up = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("加码象限")])
    stoploss = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("止损象限")])
    best_ctr = _first(_top(ctr_rows, "CTR", count=1))
    weak_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")))[:1])
    best_quality = _first(_top(quality_rows, "增长质量分", count=1))
    best_paid = _first(_top(paid_rows, "收入", count=1))
    rules = [
        {
            "rule_id": "D1_STOPLOSS_FREEZE",
            "day_label": "Day 1",
            "object_name": _combo(stoploss),
            "budget_rule": "冻结新增预算；存量转化观察保留，但不得继续放量",
            "trigger_threshold": f"roi 低于中位线且 cac 高于中位线；{_threshold_line(thresholds_payload, 'ops_roi_cac_quadrant', 'roi')}；{_threshold_line(thresholds_payload, 'ops_roi_cac_quadrant', 'cac')}",
            "stop_condition": "若 T+1 roi 仍低于中位线或 cac 仍高于中位线，继续冻结并进入下周 backlog",
            "owner": "运营负责人",
            "checkpoint": "Day 1 收盘",
            "source_evidence": "ops_roi_cac_quadrant.csv / 止损象限",
        },
        {
            "rule_id": "D2_BUDGET_MIGRATION",
            "day_label": "Day 2",
            "object_name": _combo(scale_up),
            "budget_rule": "将止损池释放预算的 20%-30% 迁入该对象；单次迁入后不连续追投",
            "trigger_threshold": "进入加码象限且付费用户规模可承接；迁入后 T+2 边际 roi 目标不低于 4.0，cac 不高于 100",
            "stop_condition": "T+2 边际 roi < 4.0 或 cac > 100，立即停止继续迁入",
            "owner": "渠道运营",
            "checkpoint": "Day 2 晚间 + T+2 复核",
            "source_evidence": "ops_roi_cac_quadrant.csv / 加码象限",
        },
        {
            "rule_id": "D3_ENTRY_EFFICIENCY_GUARD",
            "day_label": "Day 3",
            "object_name": _combo(best_ctr),
            "budget_rule": "只复制入口素材和低成本流量包，不因 CTR 单项高就扩大预算",
            "trigger_threshold": f"{_threshold_line(thresholds_payload, 'ops_ctr_cpc_cpm_efficiency', 'CTR')}；点击到注册率不得低于该池加权平均",
            "stop_condition": "点击到注册率低于池内加权平均或 roi 低于 ROI/CAC 中位线，转入承接修复",
            "owner": "内容运营 + 投放运营",
            "checkpoint": "Day 3",
            "source_evidence": "ops_ctr_cpc_cpm_efficiency.csv",
        },
        {
            "rule_id": "D4_MARGIN_GUARD",
            "day_label": "Day 4",
            "object_name": _combo(weak_margin),
            "budget_rule": "成本占比高于毛利占比的对象降权 15%-25%，释放预算只进入迁入池",
            "trigger_threshold": f"{_threshold_line(thresholds_payload, 'ops_cost_margin_share_matrix', '成本占比')}；{_threshold_line(thresholds_payload, 'ops_cost_margin_share_matrix', '毛利占比')}",
            "stop_condition": "若毛利占比未追上成本占比，继续降权，不用收入规模抵消低毛利",
            "owner": "运营负责人 + 财务 BP",
            "checkpoint": "Day 4",
            "source_evidence": "ops_cost_margin_share_matrix.csv",
        },
        {
            "rule_id": "D5_BRIDGE_EXPERIMENT",
            "day_label": "Day 5",
            "object_name": _combo(best_paid),
            "bridge_segment": _combo(best_quality),
            "budget_rule": "只用强承接产品活动承接高质量人群的小样本桥接实验，不把人群维度和产品活动维度硬拼成执行对象",
            "trigger_threshold": "高质量人群池 retention_d7 / nps 高于中位线，强承接池毛利率和 roi 不低于池内加权平均",
            "stop_condition": "实验组 contribution_margin 未提升或 retention_d7 回落，停止扩大样本",
            "owner": "用户运营 + 产品运营",
            "checkpoint": "Day 5 实验复核",
            "source_evidence": "ops_retention_nps_quality_quadrant.csv / ops_paid_users_revenue_bubble.csv",
        },
        {
            "rule_id": "D7_WEEKLY_DECISION",
            "day_label": "Day 7",
            "object_name": "预算迁移与承接实验池",
            "budget_rule": "按 T+2/T+7 检查点裁决继续加码、降权、停止或转入 backlog",
            "trigger_threshold": "继续加码需同时满足边际 roi >= 4.0、cac <= 100、贡献毛利不下降",
            "stop_condition": "任一核心阈值未达标，结束当周动作并转入复盘清单",
            "owner": "运营负责人 + 数据分析",
            "checkpoint": "Day 7 周复盘",
            "source_evidence": "ops_daily_action_plan.json / ops_management_thresholds.json",
        },
    ]
    return {
        "version": "ops_executive_action_rules_v1",
        "source": "deterministic_executive_action_rules",
        "rules": rules,
        "required_fields": ["object_name", "budget_rule", "trigger_threshold", "stop_condition", "owner", "checkpoint"],
    }


def write_ops_executive_action_rules(workspace: Path, thresholds_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = build_ops_executive_action_rules(workspace, thresholds_payload=thresholds_payload)
    (workspace / EXECUTIVE_ACTION_RULES_JSON_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def ensure_ops_management_fact_contracts(workspace: Path) -> dict[str, Any]:
    metric_semantics_payload = write_ops_metric_semantics_contract(workspace)
    issue_registry_payload = write_ops_consistency_issue_registry(workspace)
    canonical_payload = write_ops_channel_source_kpi_canonical(workspace)
    sync_payload = sync_channel_source_visual_kpis(workspace, canonical_payload)
    thresholds_payload = write_ops_management_thresholds(workspace)
    action_rules_payload = write_ops_executive_action_rules(workspace, thresholds_payload=thresholds_payload)
    return {
        "metric_semantics": metric_semantics_payload,
        "issue_registry": issue_registry_payload,
        "canonical": canonical_payload,
        "sync": sync_payload,
        "thresholds": thresholds_payload,
        "action_rules": action_rules_payload,
    }


def _management_list_items(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    raw_items = re.split(r"[；;]\s*", text)
    return [item.strip(" 。；;") for item in raw_items if item.strip(" 。；;")]


def _append_management_bullets(parts: list[str], title: str, value: Any) -> None:
    items = _management_list_items(value)
    if not items:
        return
    parts.append(f"**{title}**")
    parts.extend(f"- {item}" for item in items)


def _render_management_quadrant_index_table(payload: dict[str, Any], chart_id: str, title: str) -> str:
    rows = _management_quadrant_rows(payload, chart_id)
    if not rows:
        return ""
    table_rows: list[dict[str, Any]] = []
    for row in rows:
        table_rows.append(
            {
                "象限或分层": row.get("band") or "未分层",
                "对象数量": row.get("object_count") or 0,
                "对象清单": row.get("object_list") or "",
                "代表序号": row.get("representative_ids") or "未标注",
                "关键指标分布（区间 / 平均数 / 加权平均）": row.get("metric_distribution_summary") or "",
                "派生指标分布（区间 / 平均数 / 加权平均）": row.get("derived_metric_distribution_summary") or "",
                "管理动作": row.get("management_action") or "待补充",
                "责任角色": row.get("owner") or "待定",
                "检查点": row.get("checkpoint") or "待定",
            }
        )
    parts: list[str] = [
        f"### 核心图表象限对象清单：{title}",
        _management_chart_index_question(chart_id),
        _markdown_table(
            table_rows,
            [
                "象限或分层",
                "对象数量",
                "对象清单",
                "代表序号",
                "关键指标分布（区间 / 平均数 / 加权平均）",
                "派生指标分布（区间 / 平均数 / 加权平均）",
                "管理动作",
                "责任角色",
                "检查点",
            ],
        ),
    ]
    summary = _management_chart_index_summary(chart_id, rows)
    if summary:
        parts.append(summary)
    return "\n\n".join(part for part in parts if part).strip()


def _daily_actions(workspace: Path) -> list[dict[str, Any]]:
    payload = _read_json(workspace / "ops_daily_action_plan.json")
    rows: list[dict[str, Any]] = []
    for slot in list(payload.get("day_slots") or []):
        if not isinstance(slot, dict):
            continue
        for action in list(slot.get("actions") or [])[:3]:
            if not isinstance(action, dict):
                continue
            rows.append(
                {
                    "day_label": slot.get("day_label") or action.get("day_label") or slot.get("day_slot"),
                    "theme": slot.get("theme") or "",
                    **action,
                }
            )
    if rows:
        return rows
    return _read_csv_rows(workspace / "ops_daily_action_owner_matrix.csv")


def _legacy_build_ops_table_reading_cards_v1(workspace: Path) -> dict[str, Any]:
    asset_dir = workspace / "source_visual_assets"
    topn = _read_csv_rows(asset_dir / "ops_channel_source_aarrr_topn_small_multiples.csv")
    aarrr_total = _read_csv_rows(asset_dir / "ops_aarrr_derived_funnel_rates.csv")
    roi_rows = _with_roi_quadrants(_read_csv_rows(asset_dir / "ops_roi_cac_quadrant.csv"))
    ctr_rows = _read_csv_rows(asset_dir / "ops_ctr_cpc_cpm_efficiency.csv")
    cost_rows = _read_csv_rows(asset_dir / "ops_cost_margin_share_matrix.csv")
    paid_rows = _read_csv_rows(asset_dir / "ops_paid_users_revenue_bubble.csv")
    quality_rows = _read_csv_rows(asset_dir / "ops_retention_nps_quality_quadrant.csv")
    day_rows = _daily_actions(workspace)
    owner_rows = _read_csv_rows(workspace / "ops_daily_action_owner_matrix.csv")

    roi_reps = _representative_roi_quadrants(roi_rows)
    scale_up = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("加码象限")])
    stoploss = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("止损象限")])
    efficiency = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("提效象限")])
    verify = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("验证象限")])
    best_ctr = _first(_top(ctr_rows, "CTR", count=1))
    weak_ctr_roi = _first(sorted(ctr_rows, key=lambda row: (_num(row.get("roi")), -_num(row.get("CTR"))))[:1])
    weak_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")))[:1])
    strong_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")), reverse=True)[:1])
    best_quality = _first(_top(quality_rows, "增长质量分", count=1))
    weak_quality = _first(_top(quality_rows, "增长质量分", reverse=False, count=1))
    best_paid = _first(_top(paid_rows, "收入", count=1))
    weak_paid = _first(_top(paid_rows, "roi", reverse=False, count=1))
    topn_cost = _first(_top(topn, "operating_cost", count=1))
    topn_paid_rate = _first(_top(topn, "激活到付费率", count=1))
    topn_weak_paid_rate = _first(_top(topn, "激活到付费率", reverse=False, count=1))
    detail_source = topn or roi_rows
    total_revenue = _sum(detail_source, "revenue") or _sum(roi_rows, "revenue")
    total_cost = _sum(detail_source, "operating_cost") or _sum(roi_rows, "operating_cost")
    total_margin = _sum(detail_source, "contribution_margin") or _sum(roi_rows, "contribution_margin")
    total_paid = _sum(detail_source, "paid_users") or _sum(roi_rows, "paid_users")
    blended_roi = (total_revenue / total_cost) if total_cost else 0.0
    blended_margin_rate = (total_margin / total_revenue) if total_revenue else 0.0

    cards: dict[str, Any] = {}

    cards["executive_metric_summary"] = _table_card(
        card_id="executive_metric_summary",
        table_name="管理层总读数表",
        table_question="全盘当前是缺数据问题，还是预算效率、毛利承接和付费规模分化问题？",
        conclusion=f"当前已经可以直接做经营判断：收入约 {_fmt_num(total_revenue)}、运营成本约 {_fmt_num(total_cost)}、贡献毛利约 {_fmt_num(total_margin)}、付费用户约 {_fmt_num(total_paid)}，混合 roi 约 {_fmt_num(blended_roi, 2)}，重点不是补字段，而是迁移预算和修复承接。",
        key_rows=[
            f"收入 {_fmt_num(total_revenue)}：只能说明规模，不足以证明投放健康，必须和成本、毛利、付费用户一起读。",
            f"运营成本 {_fmt_num(total_cost)}：决定 Day 1/Day 2 的止损和预算迁移优先级。",
            f"贡献毛利 {_fmt_num(total_margin)}、毛利率 {_fmt_rate(blended_margin_rate)}：决定投放是否创造经营利润，而不是只创造流水。",
            f"混合 roi {_fmt_num(blended_roi, 2)}：低于可加码组合时，应迁移预算而不是平均加码。",
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(stoploss), trigger=f"止损象限 roi {_fmt_num(stoploss.get('roi'), 2)} / cac {_fmt_num(stoploss.get('cac'), 2)}", action="Day 1 先冻结预算", metric="roi / cac / contribution_margin", checkpoint="Day 1", owner="运营负责人"),
            _action_line(object_name=_combo(scale_up), trigger=f"加码象限 roi {_fmt_num(scale_up.get('roi'), 2)} / cac {_fmt_num(scale_up.get('cac'), 2)}", action="Day 2 小步迁入预算", metric="边际 roi / paid_users", checkpoint="Day 2", owner="渠道运营"),
            _action_line(object_name="全盘经营节奏", trigger="当前字段已足以判断", action="停止泛化补字段，改为每周按对象池复盘", metric="roi / cac / retention_d7 / nps", checkpoint="Day 7", owner="运营负责人 + 数据分析"),
        ],
        cannot_infer="总读数不能推出每个组合都健康；必须继续用组合表、象限表和承接表拆解对象。"
    )

    cards["aarrr_total"] = _table_card(
        card_id="aarrr_total",
        table_name="增长漏斗派生率总表（AARRR）",
        table_question="总漏斗哪一步折损最大，哪些阶段只能看方向、不能直接下预算结论？",
        conclusion="总漏斗只能说明全盘转化压力的位置，不能替代渠道 × 流量来源组合判断；预算动作必须落到组合漏斗和成本毛利表。",
        key_rows=[
            f"{row.get('阶段', '漏斗阶段')}：派生率 {_fmt_rate(row.get('派生率'))}，分子={row.get('分子', '')}，分母={row.get('分母', '')}；这一步用于判断漏斗断点，但不能单独指定投放对象。"
            for row in aarrr_total[:5]
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(topn_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))} 相对更强", action="Day 2 保留预算进入小步加码池，但同步看 roi 和 cac 是否恶化", metric="激活到付费率 / roi / cac", checkpoint="Day 2 晚间读数", owner="渠道运营 + 数据分析"),
            _action_line(object_name=_combo(topn_weak_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))} 偏低", action="暂停直接加码，先拆注册后承接链路和付费权益表达", metric="注册到激活率 / 激活到付费率", checkpoint="Day 4 承接复核", owner="内容运营 + 活动运营"),
            _action_line(object_name=_combo(topn_cost), trigger=f"运营成本 {_fmt_num(topn_cost.get('operating_cost'))} 对全盘影响最大", action="把该组合纳入预算迁移复盘，确认是否应迁出或提效", metric="operating_cost / contribution_margin / roi", checkpoint="Day 7 周复盘", owner="运营负责人"),
        ],
        cannot_infer="不能用总漏斗直接推出某个渠道该加码；总漏斗没有对象粒度，必须回到组合级 AARRR 和 ROI/CAC。"
    )

    cards["aarrr_top12"] = _table_card(
        card_id="aarrr_top12",
        table_name="Top12 渠道 × 流量来源 AARRR 差异表",
        table_question="哪些组合是真正能承接预算的漏斗，哪些只是消耗大或被异常补入？",
        conclusion="Top12 不是排行榜，而是预算审查池：要同时读入选原因、漏斗转化、roi、cac，不能只看曝光或消耗。",
        key_rows=[
            _reading_line(row, ["impressions", "clicks", "registrations", "activations", "paid_users", "点击率", "激活到付费率", "roi", "cac"], f"入选原因是{row.get('入选原因', 'TopN覆盖')}，后续动作取决于付费承接和成本是否同时成立")
            for row in topn[:12]
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(scale_up), trigger=f"roi {_fmt_num(scale_up.get('roi'), 2)} / cac {_fmt_num(scale_up.get('cac'), 2)}", action="把 Top12 中同类高 roi 低 cac 组合列入迁入池", metric="边际 roi / cac / paid_users", checkpoint="Day 2 晚间读数", owner="渠道运营"),
            _action_line(object_name=_combo(stoploss), trigger=f"roi {_fmt_num(stoploss.get('roi'), 2)} / cac {_fmt_num(stoploss.get('cac'), 2)}", action="冻结新增预算，先判断是否由毛利或付费率抵消高成本", metric="contribution_margin / 激活到付费率 / cac", checkpoint="Day 1 当日止损确认", owner="运营负责人"),
            _action_line(object_name=_combo(topn_weak_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))}", action="进入承接修复而非买量扩张", metric="激活到付费率 / paid_users", checkpoint="Day 4", owner="活动运营"),
        ],
        cannot_infer="Top12 入选不等于 Top12 全部可加码；高消耗入选项可能是优先止损对象。"
    )

    cards["roi_cac_quadrant"] = _table_card(
        card_id="roi_cac_quadrant",
        table_name="真实投放回报 × 获客成本四象限代表表",
        table_question="预算应从哪个象限迁出，迁入哪个象限，哪些对象只能提效或验证？",
        conclusion=f"预算先从 {_combo(stoploss)} 代表的止损象限迁出，再小步迁入 {_combo(scale_up)} 代表的加码象限；{_combo(efficiency)} 先压 cac，{_combo(verify)} 先验证承接。",
        key_rows=[
            _reading_line(row, ["paid_users", "revenue", "operating_cost", "roi", "cac"], str(row.get("结论") or row.get("建议动作") or _roi_quadrant_action(str(row.get("象限") or ""))))
            for row in roi_reps
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(stoploss), trigger=f"低 roi {_fmt_num(stoploss.get('roi'), 2)} 且高 cac {_fmt_num(stoploss.get('cac'), 2)}", action="Day 1 冻结新增预算，保留归因观察但不继续放量", metric="roi / cac / contribution_margin", checkpoint="Day 1 当日止损确认", owner="运营负责人 + 数据分析"),
            _action_line(object_name=_combo(scale_up), trigger=f"高 roi {_fmt_num(scale_up.get('roi'), 2)} 且低 cac {_fmt_num(scale_up.get('cac'), 2)}", action="Day 2 小步迁入预算，单次迁入后必须监控边际 roi", metric="边际 roi / paid_users / cac", checkpoint="Day 2 晚间读数", owner="渠道运营"),
            _action_line(object_name=f"{_combo(efficiency)} / {_combo(verify)}", trigger="分别处在提效象限和验证象限", action="提效象限先降 cac，验证象限先做低成本承接实验，不直接加码", metric="cac / 激活到付费率 / 毛利率", checkpoint="Day 7 周复盘", owner="渠道运营 + 活动运营"),
        ],
        cannot_infer="四象限不能推出无限加码；高 roi 仍需看边际回落，高 cac 也要检查是否被高毛利和高付费率抵消。"
    )

    cards["ctr_cpc_cpm"] = _table_card(
        card_id="ctr_cpc_cpm",
        table_name="点击率 × 单次点击成本 × 千次曝光成本获客效率表",
        table_question="高 CTR 是真实入口效率，还是只带来便宜点击但不能承接注册与付费？",
        conclusion=f"{_combo(best_ctr)} 代表入口吸引力较强，但是否加码要继续看点击到注册、激活到付费和 roi；{_combo(weak_ctr_roi)} 说明前段效率不能替代商业回报判断。",
        key_rows=[
            _reading_line(row, ["CTR", "CPC", "CPM", "点击到注册率", "激活到付费率", "roi", "cac"], "先看 CTR/CPC/CPM，再用注册、付费和 roi 判断是否能承接预算")
            for row in _top(ctr_rows, "CTR", count=10)
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_ctr), trigger=f"CTR {_fmt_rate(best_ctr.get('CTR'))}，点击到注册率 {_fmt_rate(best_ctr.get('点击到注册率'))}", action="保留流量入口，但只允许在 roi 不回落时加码", metric="CTR / 点击到注册率 / roi", checkpoint="Day 2 晚间读数", owner="渠道运营"),
            _action_line(object_name=_combo(weak_ctr_roi), trigger=f"roi {_fmt_num(weak_ctr_roi.get('roi'), 2)}，cac {_fmt_num(weak_ctr_roi.get('cac'), 2)}", action="不因 CTR 表现直接加码，先修落地页或权益承接", metric="点击到注册率 / 激活到付费率", checkpoint="Day 4 承接复核", owner="内容运营"),
            _action_line(object_name="CTR Top10", trigger="表内多行 CTR 接近但 roi/cac 分化", action="把 CTR 表和 ROI/CAC 表交叉复核，剔除高点击低回报对象", metric="roi / cac / paid_users", checkpoint="Day 7 周复盘", owner="数据分析"),
        ],
        cannot_infer="高 CTR 不等于高质量流量；如果点击后注册、激活或付费断裂，动作应是承接修复而不是继续买量。"
    )

    cards["cost_margin_share"] = _table_card(
        card_id="cost_margin_share",
        table_name="成本占比 × 毛利占比矩阵表",
        table_question="哪些对象花钱多但不产毛利，哪些对象虽然消耗不低但仍能保留？",
        conclusion=f"{_combo(weak_margin)} 是成本占比高于毛利占比的风险对象，{_combo(strong_margin)} 是相对能把成本转成毛利的保留对象；预算迁移不能只看成本绝对额。",
        key_rows=[
            _reading_line(row, ["revenue", "operating_cost", "contribution_margin", "成本占比", "毛利占比", "预算效率"], "成本占比高于毛利占比时进入止损或提效；毛利占比能覆盖成本占比时才有保留理由")
            for row in sorted(cost_rows, key=lambda item: _num(item.get("毛利占比")) - _num(item.get("成本占比")))[:10]
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(weak_margin), trigger=f"成本占比 {_fmt_rate(weak_margin.get('成本占比'))}，毛利占比 {_fmt_rate(weak_margin.get('毛利占比'))}", action="Day 1/Day 2 降权或迁出预算，先停止继续吞噬毛利", metric="成本占比 / 毛利占比 / 预算效率", checkpoint="Day 2", owner="运营负责人"),
            _action_line(object_name=_combo(strong_margin), trigger=f"预算效率 {_fmt_num(strong_margin.get('预算效率'), 2)}", action="保留为预算迁入候选，但复核边际毛利是否继续成立", metric="预算效率 / contribution_margin", checkpoint="Day 7", owner="渠道运营"),
            _action_line(object_name="成本占比高于毛利占比对象池", trigger="成本份额没有换来对应毛利份额", action="建立止损清单，禁止用收入规模为低毛利对象辩护", metric="毛利率 / contribution_margin", checkpoint="下周经营例会", owner="数据分析"),
        ],
        cannot_infer="低成本对象不一定值得加码；如果毛利占比也低，可能只是小盘子低影响，而不是高效率。"
    )

    cards["user_quality_bridge"] = _table_card(
        card_id="user_quality_bridge",
        table_name="用户质量与商业承接桥接判断表",
        table_question="用户质量池和商业承接池之间能不能直接连成因果链？",
        conclusion=f"{_combo(best_quality)} 只能证明人群质量强，{_combo(best_paid)} 只能证明产品活动承接强；二者之间缺少映射时，结论必须写成承接实验而非确定加码。",
        key_rows=[
            f"用户质量池：{_combo(best_quality)}，增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}、7日留存 {_fmt_rate(best_quality.get('retention_d7'))}、NPS {_fmt_num(best_quality.get('nps'), 2)}；判断是优先经营人群，不是产品承接已被证明。",
            f"商业承接池：{_combo(best_paid)}，收入 {_fmt_num(best_paid.get('收入'))}、付费用户 {_fmt_num(best_paid.get('付费用户'))}、毛利率 {_fmt_rate(best_paid.get('毛利率'))}；判断是承接组合强，不是所有高质量人群都会购买。",
            f"联动缺口：{_combo(best_quality)} → {_combo(best_paid)} 需要人群到产品活动映射或小样本实验，不能把两个独立 Top 对象拼成一条因果链。",
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_quality), trigger=f"增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)} / 7日留存 {_fmt_rate(best_quality.get('retention_d7'))}", action="Day 3 保留并深耕该人群城市组合", metric="retention_d7 / nps / paid_users", checkpoint="Day 3 晚间读数", owner="用户运营"),
            _action_line(object_name=_combo(best_paid), trigger=f"收入 {_fmt_num(best_paid.get('收入'))} / 毛利率 {_fmt_rate(best_paid.get('毛利率'))}", action="Day 5 用该产品活动做定向承接实验", metric="revenue / 毛利率 / paid_users", checkpoint="Day 5 实验复核", owner="产品负责人 + 活动运营"),
            _action_line(object_name=f"{_combo(best_quality)} × {_combo(best_paid)}", trigger="两张表粒度不同，缺少映射证据", action="只做小样本承接实验，不直接全量加码", metric="实验组 paid_users / contribution_margin / retention_d7", checkpoint="Day 7 周复盘", owner="运营负责人"),
        ],
        cannot_infer="不能从高留存高 NPS 直接推出某产品模块已经承接成功，也不能从高收入模块推出所有高质量人群都会买。"
    )

    cards["retention_nps_quality"] = _table_card(
        card_id="retention_nps_quality",
        table_name="留存 × 口碑净推荐值质量象限表",
        table_question="哪些人群城市组合值得继续经营，哪些新增即使便宜也不应优先吃预算？",
        conclusion=f"{_combo(best_quality)} 是高质量经营池，{_combo(weak_quality)} 是低质量复核池；人群质量决定 Day 3 的保留、深耕或降权。",
        key_rows=[
            _reading_line(row, ["paid_users", "revenue", "retention_d7", "nps", "增长质量分"], "增长质量分高说明可经营性更强；但仍需后续产品承接验证")
            for row in _top(quality_rows, "增长质量分", count=8)
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_quality), trigger=f"增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}", action="列为 Day 3 优先经营池", metric="retention_d7 / nps / paid_users", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name=_combo(weak_quality), trigger=f"增长质量分 {_fmt_num(weak_quality.get('增长质量分'), 2)}", action="暂停粗放扩量，先看低留存或低 NPS 的原因", metric="retention_d7 / nps", checkpoint="Day 7", owner="用户运营 + 数据分析"),
            _action_line(object_name="高质量人群池", trigger="留存和 NPS 较强但未证明商业承接", action="与产品模块表做承接实验映射", metric="paid_users / revenue / 毛利率", checkpoint="Day 5", owner="产品负责人"),
        ],
        cannot_infer="人群质量表不能单独推出收入承接成功；它只回答哪类人值得经营。"
    )

    cards["paid_users_revenue"] = _table_card(
        card_id="paid_users_revenue",
        table_name="付费用户 × 收入承接气泡表",
        table_question="哪些产品模块与活动组合真正接住了付费和收入，哪些收入高但利润或成本不可持续？",
        conclusion=f"{_combo(best_paid)} 是收入承接头部，但要用毛利率、roi、cac 判断能否继续放量；{_combo(weak_paid)} 说明收入承接表也必须保留风险侧。",
        key_rows=[
            _reading_line(row, ["paid_users", "revenue", "contribution_margin", "毛利率", "roi", "cac"], "收入和付费用户说明承接规模，毛利率与 roi 决定是否可放量")
            for row in _top(paid_rows, "收入", count=8)
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_paid), trigger=f"收入 {_fmt_num(best_paid.get('收入'))} / 毛利率 {_fmt_rate(best_paid.get('毛利率'))}", action="Day 5 作为商业承接实验主推组合", metric="revenue / contribution_margin / paid_users", checkpoint="Day 5", owner="产品负责人 + 活动运营"),
            _action_line(object_name=_combo(weak_paid), trigger=f"roi {_fmt_num(weak_paid.get('roi'), 2)} / cac {_fmt_num(weak_paid.get('cac'), 2)}", action="不要因有收入就加码，先降成本或重做权益设计", metric="roi / cac / 毛利率", checkpoint="Day 7", owner="产品负责人"),
            _action_line(object_name="产品模块 × 活动承接池", trigger="收入规模与毛利质量可能分离", action="把高收入低毛利组合和高毛利中等收入组合分开管理", metric="revenue / 毛利率 / contribution_margin", checkpoint="下周经营例会", owner="运营负责人"),
        ],
        cannot_infer="高收入不等于高质量承接；如果毛利率和 roi 不成立，收入规模越大越可能稀释利润。"
    )

    cards["daily_action_board"] = _table_card(
        card_id="daily_action_board",
        table_name="Day 1-Day 7 日动作执行表",
        table_question="动作顺序是否服务于经营风险，而不是平均分派任务？",
        conclusion="Day 1 必须先止损，Day 2 才能做预算迁移，Day 3-Day 5 分别处理人群、内容活动和产品承接，Day 6-Day 7 做口径和复盘闭环。",
        key_rows=[
            _reading_line(row, ["theme", "object_name", "owner_role", "this_day_action", "success_metric", "next_checkpoint"], "动作必须能被 owner、指标和检查点复核")
            for row in day_rows[:10]
        ],
        follow_up_actions=[
            _action_line(object_name="Day 1 止损池", trigger="高 CAC、低 roi、负毛利、低留存对象会继续吞预算", action="当日冻结新增预算并记录例外原因", metric="roi / cac / contribution_margin", checkpoint="Day 1 当日", owner="运营负责人"),
            _action_line(object_name="Day 2 预算迁移池", trigger="止损池释放预算后需要有迁入对象", action="只迁入高 roi、可承接、边际不回落组合", metric="边际 roi / paid_users", checkpoint="Day 2 晚间", owner="渠道运营"),
            _action_line(object_name="Day 7 复盘池", trigger="没有复盘会把动作变成一次性建议", action="决定继续加码、降权、转入 backlog 或结束实验", metric="roi / cac / retention_d7 / nps", checkpoint="Day 7 周复盘", owner="运营负责人 + 数据分析"),
        ],
        cannot_infer="日动作表不能证明动作已经有效，只能定义执行顺序；效果要靠 checkpoint 的指标复核。"
    )

    owner_counts: dict[str, int] = {}
    for row in owner_rows:
        owner = str(row.get("owner_role") or "未分配 owner")
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
    owner_summary_rows = [{"owner_role": owner, "任务数": count} for owner, count in sorted(owner_counts.items(), key=lambda item: item[1], reverse=True)]
    cards["owner_schedule"] = _table_card(
        card_id="owner_schedule",
        table_name="Owner 日程视图表",
        table_question="每个角色是否只拿到自己能改变的对象和指标？",
        conclusion="Owner 视图的价值不是重复日动作，而是把对象、动作、指标、检查点收敛到责任人，避免建议无人承接。",
        key_rows=[
            f"{row.get('owner_role', '未分配 owner')}：本周承接 {row.get('任务数', 0)} 条动作；判断：需要按日检查对象、指标和下一检查点是否完整。"
            for row in owner_summary_rows[:8]
        ],
        follow_up_actions=[
            _action_line(object_name="渠道运营", trigger="Day 2 预算迁移依赖渠道侧执行", action="只对高 roi 低 cac 或可提效组合调整预算", metric="roi / cac / paid_users", checkpoint="Day 2", owner="渠道运营"),
            _action_line(object_name="用户运营", trigger="Day 3 人群城市取舍需要 owner 落地", action="保留高留存高 NPS 人群，降权低质量新增池", metric="retention_d7 / nps", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name="运营负责人", trigger="跨 owner 动作需要统一复盘", action="Day 7 统一裁决加码、降权、转 backlog", metric="roi / contribution_margin / backlog 状态", checkpoint="Day 7", owner="运营负责人"),
        ],
        cannot_infer="Owner 表不能替代经营判断；它只证明责任分配，仍需回到对象表判断动作是否正确。"
    )

    payload = {
        "schema_version": "internet_ops_table_reading_cards.v1",
        "source": "deterministic_backend_table_reading",
        "rules": {
            "each_reader_facing_table_needs_pre_conclusion": True,
            "each_reader_facing_table_needs_post_reading": True,
            "follow_up_actions_require_object_owner_metric_checkpoint": True,
            "separate_confirmable_conclusion_from_hypothesis": True,
        },
        "cards": cards,
    }
    return payload


def _legacy_build_ops_table_reading_cards_v2(workspace: Path) -> dict[str, Any]:
    """Build structured reading cards for core internet-ops tables.

    This clean implementation intentionally keeps every reader-facing card in
    Chinese and derives the judgement from the same CSV assets used by charts.
    """
    asset_dir = workspace / "source_visual_assets"
    topn = _read_csv_rows(asset_dir / "ops_channel_source_aarrr_topn_small_multiples.csv")
    aarrr_total = _read_csv_rows(asset_dir / "ops_aarrr_derived_funnel_rates.csv")
    roi_rows = _with_roi_quadrants(_read_csv_rows(asset_dir / "ops_roi_cac_quadrant.csv"))
    ctr_rows = _read_csv_rows(asset_dir / "ops_ctr_cpc_cpm_efficiency.csv")
    cost_rows = _read_csv_rows(asset_dir / "ops_cost_margin_share_matrix.csv")
    paid_rows = _read_csv_rows(asset_dir / "ops_paid_users_revenue_bubble.csv")
    quality_rows = _read_csv_rows(asset_dir / "ops_retention_nps_quality_quadrant.csv")
    day_rows = _daily_actions(workspace)
    owner_rows = _read_csv_rows(workspace / "ops_daily_action_owner_matrix.csv")

    detail_source = topn or roi_rows
    total_revenue = _sum(detail_source, "revenue") or _sum(roi_rows, "revenue")
    total_cost = _sum(detail_source, "operating_cost") or _sum(roi_rows, "operating_cost")
    total_margin = _sum(detail_source, "contribution_margin") or _sum(roi_rows, "contribution_margin")
    total_paid = _sum(detail_source, "paid_users") or _sum(roi_rows, "paid_users")
    blended_roi = (total_revenue / total_cost) if total_cost else 0.0
    blended_margin_rate = (total_margin / total_revenue) if total_revenue else 0.0

    roi_reps = _representative_roi_quadrants(roi_rows)
    scale_up = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("加码象限")])
    stoploss = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("止损象限")])
    efficiency = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("提效象限")])
    verify = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("验证象限")])

    best_ctr = _first(_top(ctr_rows, "CTR", count=1))
    worst_cpc = _first(_top(ctr_rows, "CPC", count=1))
    weak_ctr_roi = _first(sorted(ctr_rows, key=lambda row: (_num(row.get("roi")), -_num(row.get("CTR"))))[:1])
    weak_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")))[:1])
    strong_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")), reverse=True)[:1])
    best_quality = _first(_top(quality_rows, "增长质量分", count=1))
    weak_quality = _first(_top(quality_rows, "增长质量分", reverse=False, count=1))
    best_paid = _first(_top(paid_rows, "收入", count=1))
    weak_paid = _first(_top(paid_rows, "roi", reverse=False, count=1))
    topn_cost = _first(_top(topn, "operating_cost", count=1))
    topn_paid_rate = _first(_top(topn, "激活到付费率", count=1))
    topn_weak_paid_rate = _first(_top(topn, "激活到付费率", reverse=False, count=1))
    topn_click_reg = _first(_top(topn, "点击到注册率", count=1))

    day1 = _first([row for row in day_rows if str(row.get("day_label") or "").lower() == "day 1"])
    day2 = _first([row for row in day_rows if str(row.get("day_label") or "").lower() == "day 2"])
    day7 = _first([row for row in day_rows if str(row.get("day_label") or "").lower() == "day 7"])

    cards: dict[str, Any] = {}

    cards["executive_metric_summary"] = _table_card(
        card_id="executive_metric_summary",
        table_name="管理层总读数表",
        table_question="当前是缺字段问题，还是预算效率、毛利承接和付费规模已经足够支撑经营判断？",
        conclusion=(
            f"当前字段已经能直接判断经营问题：收入约 {_fmt_num(total_revenue)}、运营成本约 {_fmt_num(total_cost)}、"
            f"贡献毛利约 {_fmt_num(total_margin)}、付费用户约 {_fmt_num(total_paid)}，混合 roi 约 {_fmt_num(blended_roi, 2)}、"
            f"毛利率约 {_fmt_rate(blended_margin_rate)}。核心矛盾不是补字段，而是把预算从低回报/高成本对象迁到高回报/可承接对象。"
        ),
        key_rows=[
            f"收入 {_fmt_num(total_revenue)} 说明盘子有规模，但不能单独证明投放健康，必须和成本、毛利、付费用户一起读。",
            f"运营成本 {_fmt_num(total_cost)} 决定 Day 1 止损和 Day 2 预算重排的优先级，成本越集中越不能平均优化。",
            f"贡献毛利 {_fmt_num(total_margin)}、毛利率 {_fmt_rate(blended_margin_rate)} 用来判断投放是否创造经营利润，而不只是创造流水。",
            f"混合 roi {_fmt_num(blended_roi, 2)} 低于优质组合时，结论应是迁移预算，不是全盘加码。",
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(stoploss), trigger=f"止损象限 roi {_fmt_num(stoploss.get('roi'), 2)} / cac {_fmt_num(stoploss.get('cac'), 2)}", action="Day 1 冻结预算并停止扩量", metric="roi / cac / contribution_margin", checkpoint="Day 1 收盘", owner="运营负责人"),
            _action_line(object_name=_combo(scale_up), trigger=f"加码象限 roi {_fmt_num(scale_up.get('roi'), 2)} / cac {_fmt_num(scale_up.get('cac'), 2)}", action="Day 2 小步迁入预算，避免一次性放量", metric="边际 roi / paid_users", checkpoint="Day 2 晚间", owner="渠道运营"),
            _action_line(object_name="全盘经营复盘", trigger="现有字段已覆盖漏斗、投放、毛利、留存和口碑", action="停止泛化补字段，把复盘改成对象池经营例会", metric="roi / cac / retention_d7 / nps", checkpoint="Day 7 周复盘", owner="运营负责人 + 数据分析"),
        ],
        cannot_infer="总读数不能推出每个渠道都健康，也不能证明某个产品模块已经承接成功；必须继续拆到组合表、象限表和承接表。",
    )

    cards["aarrr_total"] = _table_card(
        card_id="aarrr_total",
        table_name="增长漏斗派生率总表（AARRR）",
        table_question="全盘从曝光到付费的最大折损在哪里？这个折损能否直接转成预算动作？",
        conclusion="总漏斗只能定位全盘断点，不能替代渠道 × 流量来源组合判断；预算动作必须回到组合级 AARRR、roi/cac 和毛利承接。",
        key_rows=[
            _reading_line(row, ["派生率", "分子", "分母"], "这是全盘阶段折损位置，用来决定需要继续拆哪一段，但不能单独决定某个渠道加码。")
            for row in aarrr_total[:5]
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(topn_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))} 相对更强", action="进入 Day 2 小步加码候选，但同步监控 roi 和 cac", metric="激活到付费率 / roi / cac", checkpoint="Day 2 晚间", owner="渠道运营 + 数据分析"),
            _action_line(object_name=_combo(topn_weak_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))} 偏弱", action="先复核注册后承接和付费权益，不直接加码", metric="注册到激活率 / 激活到付费率", checkpoint="Day 4 承接复核", owner="内容运营 + 活动运营"),
            _action_line(object_name=_combo(topn_cost), trigger=f"运营成本 {_fmt_num(topn_cost.get('operating_cost'))} 对全盘影响最大", action="纳入预算迁移复盘，确认迁出、保留还是提效", metric="operating_cost / contribution_margin / roi", checkpoint="Day 7 周复盘", owner="运营负责人"),
        ],
        cannot_infer="不能用总漏斗直接推出某个渠道该加码；总漏斗没有对象粒度，必须结合组合级 AARRR 和 ROI/CAC 表。",
    )

    cards["aarrr_top12"] = _table_card(
        card_id="aarrr_top12",
        table_name="Top12 渠道 × 流量来源 AARRR 差异表",
        table_question="同样的渠道或流量来源，哪一步转化差异最大，预算应该迁到哪里？",
        conclusion=(
            f"Top12 组合不是同一个方向：{_combo(topn_click_reg)} 的点击到注册率 {_fmt_rate(topn_click_reg.get('点击到注册率'))} 更强，"
            f"{_combo(topn_weak_paid_rate)} 的激活到付费率 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))} 更弱，说明前段吸引和后段商业承接需要分开判断。"
        ),
        key_rows=[
            _reading_line(topn_click_reg, ["impressions", "clicks", "registrations", "点击率", "点击到注册率"], "前段承接更顺，适合检查是否能安全承接更多有效流量。"),
            _reading_line(topn_paid_rate, ["activations", "paid_users", "激活到付费率", "roi", "cac"], "后段付费承接更强，但仍要被 roi 和 cac 约束。"),
            _reading_line(topn_weak_paid_rate, ["activations", "paid_users", "激活到付费率", "roi", "cac"], "激活后未能变现，优先排查权益、价格或产品承接，而不是继续买量。"),
            _reading_line(topn_cost, ["operating_cost", "revenue", "contribution_margin", "roi", "cac"], "高消耗组合对全盘影响最大，必须进入预算迁移清单。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(topn_click_reg), trigger=f"点击到注册率 {_fmt_rate(topn_click_reg.get('点击到注册率'))}", action="复核落地页和注册激励，判断是否可复制到同渠道相邻流量来源", metric="点击到注册率 / registration_cost", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name=_combo(topn_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))}", action="做小额预算迁入，并监控边际付费和毛利", metric="paid_users / contribution_margin / roi", checkpoint="Day 5", owner="活动运营"),
            _action_line(object_name=_combo(topn_weak_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))}", action="暂停扩量，先做权益和产品承接实验", metric="激活到付费率 / nps / retention_d7", checkpoint="Day 7", owner="产品运营"),
        ],
        cannot_infer="组合漏斗能说明阶段效率差异，但不能单独证明内容、活动或产品模块的因果，需要与内容活动表和产品模块表做桥接实验。",
    )

    cards["roi_cac_quadrant"] = _table_card(
        card_id="roi_cac_quadrant",
        table_name="真实投放回报 × 获客成本四象限表",
        table_question="预算应该从哪些对象迁出，迁入哪些对象，哪些对象只做提效或验证？",
        conclusion=(
            f"四象限同时给出迁出和迁入方向：{_combo(stoploss)} 属于止损对象，"
            f"{_combo(scale_up)} 属于可加码对象；{_combo(efficiency)} 要先压 cac，{_combo(verify)} 要先验证承接。"
        ),
        key_rows=[
            _reading_line(scale_up, ["图中序号", "roi", "cac", "paid_users", "revenue", "operating_cost"], "高 roi / 低 cac 是迁入候选，但只能小步加码并监控边际 roi。"),
            _reading_line(stoploss, ["图中序号", "roi", "cac", "paid_users", "revenue", "operating_cost"], "低 roi / 高 cac 是 Day 1 冻结或降权对象，继续扩量会放大预算损耗。"),
            _reading_line(efficiency, ["图中序号", "roi", "cac", "paid_users", "revenue", "operating_cost"], "高 roi 但 cac 高，说明有价值但买贵了，优先做出价和流量结构提效。"),
            _reading_line(verify, ["图中序号", "roi", "cac", "paid_users", "revenue", "operating_cost"], "低 roi / 低 cac 不适合直接放量，先用低成本验证转化和毛利承接。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(stoploss), trigger=f"roi {_fmt_num(stoploss.get('roi'), 2)} 且 cac {_fmt_num(stoploss.get('cac'), 2)}", action="Day 1 冻结新增预算，只保留必要回收流量", metric="roi / cac / contribution_margin", checkpoint="Day 1", owner="渠道运营"),
            _action_line(object_name=_combo(scale_up), trigger=f"roi {_fmt_num(scale_up.get('roi'), 2)} 且 cac {_fmt_num(scale_up.get('cac'), 2)}", action="Day 2 迁入小额预算，并设边际 roi 下限", metric="边际 roi / paid_users", checkpoint="Day 2", owner="运营负责人"),
            _action_line(object_name=_combo(efficiency), trigger=f"高 roi 但 cac {_fmt_num(efficiency.get('cac'), 2)} 偏高", action="先压价和换流量包，不直接加预算", metric="cac / CPC / CPM", checkpoint="Day 3", owner="投放运营"),
        ],
        cannot_infer="象限表不能证明某个创意或活动本身有效，它只说明渠道 × 流量来源组合的预算效率和迁移优先级。",
    )

    cards["ctr_cpc_cpm"] = _table_card(
        card_id="ctr_cpc_cpm",
        table_name="点击率 × 单次点击成本 × 千次曝光成本获客效率表",
        table_question="前段获客效率是真好，还是只是点击率高但后续承接弱？",
        conclusion=(
            f"{_combo(best_ctr)} 的 CTR {_fmt_rate(best_ctr.get('CTR'))} 代表入口吸引更强；"
            f"{_combo(worst_cpc)} 的 CPC {_fmt_num(worst_cpc.get('CPC'), 2)} 说明拿点击更贵；"
            f"{_combo(weak_ctr_roi)} 需要警惕高点击但低 roi 的承接断层。"
        ),
        key_rows=[
            _reading_line(best_ctr, ["图中序号", "CTR", "CPC", "CPM", "点击到注册率", "roi", "cac"], "CTR 高只能说明入口吸引强，必须继续看点击到注册率和 roi。"),
            _reading_line(worst_cpc, ["图中序号", "CTR", "CPC", "CPM", "点击到注册率", "roi", "cac"], "点击成本高会压缩后续转化容错率，不能只靠放量解决。"),
            _reading_line(weak_ctr_roi, ["图中序号", "CTR", "CPC", "CPM", "点击到注册率", "roi", "cac"], "如果点击不差但 roi 弱，问题更可能在注册后承接或付费权益。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_ctr), trigger=f"CTR {_fmt_rate(best_ctr.get('CTR'))}", action="复制入口素材和落地页结构，但设置点击到注册率阈值", metric="CTR / 点击到注册率 / roi", checkpoint="Day 2", owner="内容运营"),
            _action_line(object_name=_combo(worst_cpc), trigger=f"CPC {_fmt_num(worst_cpc.get('CPC'), 2)}", action="降权高价点击来源，改测低成本词包或人群包", metric="CPC / cac / paid_users", checkpoint="Day 3", owner="投放运营"),
            _action_line(object_name=_combo(weak_ctr_roi), trigger=f"roi {_fmt_num(weak_ctr_roi.get('roi'), 2)} 偏弱", action="排查注册后激活和付费权益，不把高 CTR 直接当加码理由", metric="注册到激活率 / 激活到付费率", checkpoint="Day 4", owner="用户运营"),
        ],
        cannot_infer="CTR/CPC/CPM 表只能解释前段获客质量，不能单独证明后端商业化已经接住。",
    )

    cards["cost_margin_share"] = _table_card(
        card_id="cost_margin_share",
        table_name="成本占比 × 毛利占比经营质量表",
        table_question="哪些对象花钱多但不产毛利，哪些对象虽然规模不一定最大但经营质量更好？",
        conclusion=(
            f"{_combo(weak_margin)} 的成本占比 {_fmt_rate(weak_margin.get('成本占比'))} 与毛利占比 {_fmt_rate(weak_margin.get('毛利占比'))} 不匹配，"
            f"属于优先止损或提效对象；{_combo(strong_margin)} 的毛利占比 {_fmt_rate(strong_margin.get('毛利占比'))} 更能解释为什么不能只按收入排序。"
        ),
        key_rows=[
            _reading_line(weak_margin, ["图中序号", "成本占比", "毛利占比", "revenue", "operating_cost", "contribution_margin", "roi"], "成本吃得多但毛利贡献弱，继续放量会稀释经营结果。"),
            _reading_line(strong_margin, ["图中序号", "成本占比", "毛利占比", "revenue", "operating_cost", "contribution_margin", "roi"], "毛利承接更强，适合进入保留或小步加码池。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(weak_margin), trigger=f"成本占比 {_fmt_rate(weak_margin.get('成本占比'))} 高于毛利占比 {_fmt_rate(weak_margin.get('毛利占比'))}", action="Day 1 降权或冻结增量预算", metric="contribution_margin / roi", checkpoint="Day 1", owner="运营负责人"),
            _action_line(object_name=_combo(strong_margin), trigger=f"毛利占比 {_fmt_rate(strong_margin.get('毛利占比'))} 更强", action="进入 Day 2 保留池，验证边际毛利是否稳定", metric="边际 contribution_margin", checkpoint="Day 2", owner="渠道运营"),
            _action_line(object_name="成本毛利复盘表", trigger="成本占比和毛利占比分叉", action="把预算复盘从收入排序改为毛利排序", metric="毛利占比 / 成本占比差值", checkpoint="Day 7", owner="财务 BP + 运营负责人"),
        ],
        cannot_infer="成本毛利表不能解释用户为什么留下或为什么付费，只能说明经营利润承接是否值得继续投入。",
    )

    cards["user_quality_bridge"] = _table_card(
        card_id="user_quality_bridge",
        table_name="用户质量与商业化承接桥接表",
        table_question="高留存/高口碑用户是否已经被商业化承接？高收入对象是否真的有质量支撑？",
        conclusion=(
            f"{_combo(best_quality)} 的增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}、retention_d7 {_fmt_rate(best_quality.get('retention_d7'))}、nps {_fmt_num(best_quality.get('nps'), 2)} 更强；"
            f"{_combo(best_paid)} 的收入 {_fmt_num(best_paid.get('收入'))} 和付费用户 {_fmt_num(best_paid.get('付费用户'))} 更大。两张表只能形成桥接假设，不能拼成因果。"
        ),
        key_rows=[
            _reading_line(best_quality, ["图中序号", "retention_d7", "nps", "增长质量分", "roi", "cac"], "用户质量更强，适合进入人群/城市优先池，但不能直接证明商业化已经接住。"),
            _reading_line(weak_quality, ["图中序号", "retention_d7", "nps", "增长质量分", "roi", "cac"], "用户质量弱，Day 3 应先做人群和城市取舍，而不是继续追新增。"),
            _reading_line(best_paid, ["图中序号", "收入", "付费用户", "revenue", "paid_users", "roi"], "商业化规模更大，但还需要看毛利率和用户质量，不能只按收入加码。"),
            _reading_line(weak_paid, ["图中序号", "收入", "付费用户", "roi", "cac"], "收入承接弱或 roi 弱时，应先做模块/活动承接实验。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_quality), trigger=f"增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}", action="Day 3 作为优先人群/城市池，匹配高毛利产品承接", metric="retention_d7 / nps / paid_users", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name=_combo(best_paid), trigger=f"收入 {_fmt_num(best_paid.get('收入'))}", action="Day 5 复核产品模块和活动权益，确认高收入是否有毛利支撑", metric="contribution_margin / roi", checkpoint="Day 5", owner="产品运营 + 活动运营"),
            _action_line(object_name=_combo(weak_quality), trigger=f"retention_d7 {_fmt_rate(weak_quality.get('retention_d7'))}、nps {_fmt_num(weak_quality.get('nps'), 2)} 偏弱", action="降权低质量人群，不再用新增规模掩盖质量问题", metric="retention_d7 / nps", checkpoint="Day 7", owner="用户运营"),
        ],
        cannot_infer="用户质量表和商业承接表来自不同对象池，不能直接说某个产品模块导致某个人群留存；只能提出桥接实验。",
    )

    cards["retention_nps_quality"] = _table_card(
        card_id="retention_nps_quality",
        table_name="留存 × 口碑净推荐值质量象限表",
        table_question="哪些人群/区域值得保留，哪些新增会变成低质量规模？",
        conclusion=(
            f"{_combo(best_quality)} 是质量更好的候选池，retention_d7 {_fmt_rate(best_quality.get('retention_d7'))}、nps {_fmt_num(best_quality.get('nps'), 2)}；"
            f"{_combo(weak_quality)} 的质量分更弱，说明新增规模不能替代留存和口碑。"
        ),
        key_rows=[
            _reading_line(best_quality, ["图中序号", "retention_d7", "nps", "增长质量分", "paid_users", "roi"], "高留存和高口碑代表用户质量更稳，适合接入长期经营动作。"),
            _reading_line(weak_quality, ["图中序号", "retention_d7", "nps", "增长质量分", "paid_users", "roi"], "质量弱的新增会拖累后续付费和口碑，应进入降权或验证池。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_quality), trigger=f"retention_d7 {_fmt_rate(best_quality.get('retention_d7'))}、nps {_fmt_num(best_quality.get('nps'), 2)}", action="保留并匹配高毛利承接路径", metric="retention_d7 / nps / contribution_margin", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name=_combo(weak_quality), trigger=f"增长质量分 {_fmt_num(weak_quality.get('增长质量分'), 2)}", action="暂停扩量，先验证人群包和城市层级是否误配", metric="retention_d7 / nps", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name="质量象限复盘", trigger="留存和口碑分化", action="把人群策略从新增数量改为质量分层", metric="增长质量分 / paid_users", checkpoint="Day 7", owner="运营负责人"),
        ],
        cannot_infer="留存和 NPS 只能说明用户质量，不足以证明收入承接成功，仍需和产品模块/活动表连接。",
    )

    cards["paid_users_revenue"] = _table_card(
        card_id="paid_users_revenue",
        table_name="付费用户 × 收入承接表",
        table_question="哪些对象既有付费规模又有收入承接，哪些只是有量但效率弱？",
        conclusion=(
            f"{_combo(best_paid)} 的收入 {_fmt_num(best_paid.get('收入'))}、付费用户 {_fmt_num(best_paid.get('付费用户'))} 更突出；"
            f"{_combo(weak_paid)} 的 roi {_fmt_num(weak_paid.get('roi'), 2)} 较弱，说明规模和效率必须同时看。"
        ),
        key_rows=[
            _reading_line(best_paid, ["图中序号", "收入", "付费用户", "revenue", "paid_users", "roi", "cac"], "收入和付费规模更大，但必须继续看毛利和 roi 才能决定加码。"),
            _reading_line(weak_paid, ["图中序号", "收入", "付费用户", "roi", "cac"], "有付费也可能低效率，不能用付费人数替代经营回报。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_combo(best_paid), trigger=f"收入 {_fmt_num(best_paid.get('收入'))}、付费用户 {_fmt_num(best_paid.get('付费用户'))}", action="进入 Day 5 商业化承接复核，确认毛利是否同步提升", metric="contribution_margin / roi", checkpoint="Day 5", owner="产品运营"),
            _action_line(object_name=_combo(weak_paid), trigger=f"roi {_fmt_num(weak_paid.get('roi'), 2)}", action="复核定价、权益和活动成本，不直接扩大付费入口", metric="roi / cac / 毛利率", checkpoint="Day 5", owner="活动运营"),
            _action_line(object_name="付费承接池", trigger="付费规模和收入承接分化", action="把产品模块和活动组合分为加码、提效、验证、止损四类", metric="paid_users / revenue / contribution_margin", checkpoint="Day 7", owner="运营负责人"),
        ],
        cannot_infer="付费用户和收入表不能单独说明用户长期价值，LTV 和回本周期仍需要后续留存窗口继续验证。",
    )

    cards["daily_action_board"] = _table_card(
        card_id="daily_action_board",
        table_name="D1-D7 日动作执行板",
        table_question="这周每天到底做什么，动作是否从表格证据推导，而不是泛泛建议？",
        conclusion="日动作不是把本周动作改名，而是按止损、预算迁移、人群取舍、内容活动承接、商业化承接、口径复核、周复盘顺序执行。",
        key_rows=[
            _reading_line(day1, ["day_label", "theme", "object_name", "this_day_action", "success_metric", "next_checkpoint"], "Day 1 必须先处理高风险对象，避免预算继续外流。"),
            _reading_line(day2, ["day_label", "theme", "object_name", "this_day_action", "success_metric", "next_checkpoint"], "Day 2 才做预算迁移，迁入对象必须来自前面表格的高效率证据。"),
            _reading_line(day7, ["day_label", "theme", "object_name", "this_day_action", "success_metric", "next_checkpoint"], "Day 7 用复盘决定继续加码、降权或进入 backlog，不能停留在建议层。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_object_label(day1), trigger=str(day1.get("dependency") or "高风险对象优先止损"), action=str(day1.get("this_day_action") or "冻结预算并检查止损位"), metric=str(day1.get("success_metric") or "roi / cac / contribution_margin"), checkpoint=str(day1.get("next_checkpoint") or "Day 1"), owner=str(day1.get("owner_role") or "运营负责人")),
            _action_line(object_name=_object_label(day2), trigger=str(day2.get("dependency") or "预算迁移需要高效率证据"), action=str(day2.get("this_day_action") or "迁入小额预算并看边际指标"), metric=str(day2.get("success_metric") or "边际 roi / paid_users"), checkpoint=str(day2.get("next_checkpoint") or "Day 2"), owner=str(day2.get("owner_role") or "渠道运营")),
            _action_line(object_name=_object_label(day7), trigger=str(day7.get("dependency") or "周复盘需要闭环"), action=str(day7.get("this_day_action") or "决定下周加码/降权/backlog"), metric=str(day7.get("success_metric") or "roi / retention_d7 / nps"), checkpoint=str(day7.get("next_checkpoint") or "Day 7"), owner=str(day7.get("owner_role") or "运营负责人")),
        ],
        cannot_infer="日动作表不能替代复盘结果；它规定执行顺序，最终是否继续加码必须看每日检查点的真实变化。",
    )

    owner_first = _first(owner_rows)
    owner_second = _first(owner_rows[1:2])
    owner_third = _first(owner_rows[2:3])
    cards["owner_schedule"] = _table_card(
        card_id="owner_schedule",
        table_name="Owner 责任视图日程板",
        table_question="每个角色本周负责什么，如何避免所有动作都落到一句“运营负责人跟进”？",
        conclusion="Owner 视图把 D1-D7 拆成角色责任：渠道运营管预算和获客效率，用户运营管人群/城市取舍，内容与活动运营管承接，运营负责人负责止损和复盘。",
        key_rows=[
            _reading_line(owner_first, ["owner_role", "day_label", "theme", "object_name", "this_day_action", "success_metric", "next_checkpoint"], "第一责任人需要把动作落到对象和指标，不是只写跟进。"),
            _reading_line(owner_second, ["owner_role", "day_label", "theme", "object_name", "this_day_action", "success_metric", "next_checkpoint"], "跨角色动作要有检查点，否则容易变成建议清单。"),
            _reading_line(owner_third, ["owner_role", "day_label", "theme", "object_name", "this_day_action", "success_metric", "next_checkpoint"], "每个角色都要能在当日复盘时拿出数值变化。"),
        ],
        follow_up_actions=[
            _action_line(object_name=_object_label(owner_first), trigger=str(owner_first.get("theme") or "责任视图首项"), action=str(owner_first.get("this_day_action") or "按日程执行并回填检查点"), metric=str(owner_first.get("success_metric") or "roi / cac"), checkpoint=str(owner_first.get("next_checkpoint") or owner_first.get("day_label") or "Day 1"), owner=str(owner_first.get("owner_role") or "运营负责人")),
            _action_line(object_name=_object_label(owner_second), trigger=str(owner_second.get("theme") or "责任视图第二项"), action=str(owner_second.get("this_day_action") or "执行跨角色协同动作"), metric=str(owner_second.get("success_metric") or "paid_users / retention_d7"), checkpoint=str(owner_second.get("next_checkpoint") or owner_second.get("day_label") or "Day 3"), owner=str(owner_second.get("owner_role") or "用户运营")),
            _action_line(object_name=_object_label(owner_third), trigger=str(owner_third.get("theme") or "责任视图第三项"), action=str(owner_third.get("this_day_action") or "完成复盘并决定进入 backlog"), metric=str(owner_third.get("success_metric") or "contribution_margin / nps"), checkpoint=str(owner_third.get("next_checkpoint") or owner_third.get("day_label") or "Day 7"), owner=str(owner_third.get("owner_role") or "运营负责人")),
        ],
        cannot_infer="Owner 表只能说明责任分工和复盘节奏，不能证明动作已经产生效果；效果必须由下一检查点指标确认。",
    )

    return {
        "version": "ops_table_reading_cards_v2",
        "source": "deterministic_internet_ops_table_reading",
        "card_count": len(cards),
        "rules": {
            "each_reader_facing_table_needs_pre_conclusion": True,
            "each_reader_facing_table_needs_post_reading": True,
            "follow_up_actions_require_object_owner_metric_checkpoint": True,
            "separate_confirmable_conclusion_from_hypothesis": True,
        },
        "cards": cards,
    }


def build_ops_table_reading_cards(workspace: Path) -> dict[str, Any]:
    asset_dir = workspace / "source_visual_assets"
    topn = _read_csv_rows(asset_dir / "ops_channel_source_aarrr_topn_small_multiples.csv")
    aarrr_total = _read_csv_rows(asset_dir / "ops_aarrr_derived_funnel_rates.csv")
    roi_rows = _with_roi_quadrants(_read_csv_rows(asset_dir / "ops_roi_cac_quadrant.csv"))
    ctr_rows = _read_csv_rows(asset_dir / "ops_ctr_cpc_cpm_efficiency.csv")
    cost_rows = _read_csv_rows(asset_dir / "ops_cost_margin_share_matrix.csv")
    paid_rows = _read_csv_rows(asset_dir / "ops_paid_users_revenue_bubble.csv")
    quality_rows = _read_csv_rows(asset_dir / "ops_retention_nps_quality_quadrant.csv")
    day_rows = _daily_actions(workspace)
    owner_rows = _read_csv_rows(workspace / "ops_daily_action_owner_matrix.csv")

    roi_reps = _representative_roi_quadrants(roi_rows)
    scale_up = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("加码象限")])
    stoploss = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("止损象限")])
    efficiency = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("提效象限")])
    verify = _first([row for row in roi_reps if str(row.get("象限") or "").startswith("验证象限")])
    best_ctr = _first(_top(ctr_rows, "CTR", count=1))
    worst_cpc = _first(_top(ctr_rows, "CPC", count=1))
    weak_ctr_roi = _first(sorted(ctr_rows, key=lambda row: (_num(row.get("roi")), -_num(row.get("CTR"))))[:1])
    weak_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")))[:1])
    strong_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")), reverse=True)[:1])
    best_quality = _first(_top(quality_rows, "增长质量分", count=1))
    weak_quality = _first(_top(quality_rows, "增长质量分", reverse=False, count=1))
    best_paid = _first(_top(paid_rows, "收入", count=1))
    weak_paid = _first(_top(paid_rows, "roi", reverse=False, count=1))
    topn_cost = _first(_top(topn, "operating_cost", count=1))
    topn_paid_rate = _first(_top(topn, "激活到付费率", count=1))
    topn_weak_paid_rate = _first(_top(topn, "激活到付费率", reverse=False, count=1))
    topn_click_reg = _first(_top(topn, "点击到注册率", count=1))
    funnel_break = _first(_top(aarrr_total, "派生率", reverse=False, count=1))
    day1 = _first([row for row in day_rows if str(row.get("day_label") or "").lower() == "day 1"])
    day2 = _first([row for row in day_rows if str(row.get("day_label") or "").lower() == "day 2"])
    day7 = _first([row for row in day_rows if str(row.get("day_label") or "").lower() == "day 7"])

    detail_source = topn or roi_rows
    total_revenue = _sum(detail_source, "revenue") or _sum(roi_rows, "revenue")
    total_cost = _sum(detail_source, "operating_cost") or _sum(roi_rows, "operating_cost")
    total_margin = _sum(detail_source, "contribution_margin") or _sum(roi_rows, "contribution_margin")
    total_paid = _sum(detail_source, "paid_users") or _sum(roi_rows, "paid_users")
    blended_roi = (total_revenue / total_cost) if total_cost else 0.0
    blended_margin_rate = (total_margin / total_revenue) if total_revenue else 0.0

    roi_gap = _num(scale_up.get("roi")) - blended_roi
    cac_gap = _num(stoploss.get("cac")) - _num(scale_up.get("cac"))
    quality_gap = _num(best_quality.get("增长质量分")) - _num(weak_quality.get("增长质量分"))
    paid_roi_gap = _num(best_paid.get("roi")) - _num(weak_paid.get("roi"))

    cards: dict[str, Any] = {}
    cards["executive_metric_summary"] = _card_v3(
        card_id="executive_metric_summary",
        table_name="管理层总读数表",
        table_question="全盘预算是否被高回报对象充分承接？",
        judgement_standard="全盘预算是否被高回报对象充分承接",
        standard_formula="混合 roi 与代表性高回报低 CAC 组合对比，并联动收入、运营成本、贡献毛利、付费用户。",
        object_bands=[
            _band("效率稀释层", "迁出低回报预算", f"混合 roi {_fmt_num(blended_roi, 2)} 低于 {_combo(scale_up)} 的 {_fmt_num(scale_up.get('roi'), 2)}，差 {_fmt_num(roi_gap, 2)} 个点", [f"全盘收入 {_fmt_num(total_revenue)} / 运营成本 {_fmt_num(total_cost)}"]),
            _band("可迁入层", "Day 2 小步迁入", f"{_combo(scale_up)} 同时具备高 roi 和低 cac", [f"{_combo(scale_up)}：roi {_fmt_num(scale_up.get('roi'), 2)}，cac {_fmt_num(scale_up.get('cac'), 2)}"]),
            _band("冻结层", "Day 1 冻结新增预算", f"{_combo(stoploss)} 高 cac 没有换来匹配回报", [f"{_combo(stoploss)}：roi {_fmt_num(stoploss.get('roi'), 2)}，cac {_fmt_num(stoploss.get('cac'), 2)}，成本 {_fmt_num(stoploss.get('operating_cost'))}"]),
        ],
        representative_objects=[
            f"{_combo(scale_up)} 把预算转成更高回报：roi {_fmt_num(scale_up.get('roi'), 2)}、cac {_fmt_num(scale_up.get('cac'), 2)}、付费用户 {_fmt_num(scale_up.get('paid_users'))}。",
            f"{_combo(stoploss)} 是预算黑洞：roi {_fmt_num(stoploss.get('roi'), 2)}、cac {_fmt_num(stoploss.get('cac'), 2)}，与迁入层 cac 相差 {_fmt_num(cac_gap, 2)}。",
            f"总盘收入 {_fmt_num(total_revenue)}、贡献毛利 {_fmt_num(total_margin)}、毛利率 {_fmt_rate(blended_margin_rate)} 仍有经营缓冲，问题集中在预算分配效率。",
        ],
        business_conclusion=f"{_fmt_num(total_revenue)} 收入没有转化成同等强度的投放效率；混合 roi {_fmt_num(blended_roi, 2)} 距离 {_combo(scale_up)} 的 {_fmt_num(scale_up.get('roi'), 2)} 仍差 {_fmt_num(roi_gap, 2)} 个点，低回报高 CAC 组合正在稀释全盘效率。",
        decision_path=f"Day 1 冻结 {_combo(stoploss)}；Day 2 把释放预算小步迁入 {_combo(scale_up)}；Day 7 用边际 roi 和贡献毛利决定是否继续迁入。",
        next_moves=[
            _action_line(object_name=_combo(stoploss), trigger=f"roi {_fmt_num(stoploss.get('roi'), 2)} / cac {_fmt_num(stoploss.get('cac'), 2)}", action="冻结新增预算并复核归因窗口", metric="roi / cac / contribution_margin", checkpoint="Day 1", owner="运营负责人"),
            _action_line(object_name=_combo(scale_up), trigger=f"roi {_fmt_num(scale_up.get('roi'), 2)} / cac {_fmt_num(scale_up.get('cac'), 2)}", action="小步迁入预算并设边际 roi 下限", metric="边际 roi / paid_users", checkpoint="Day 2", owner="渠道运营"),
        ],
        risk_boundary="该表给出全盘预算取舍方向；产品承接和用户质量结论由后续对象表承接。",
    )

    cards["aarrr_total"] = _card_v3(
        card_id="aarrr_total",
        table_name="增长漏斗派生率总表（AARRR）",
        table_question="全盘最大转化断点在哪一段？",
        judgement_standard="全盘最大转化断点",
        standard_formula="相邻阶段派生率：点击率、点击到注册率、注册到激活率、激活到付费率、点击到付费率。",
        object_bands=[
            _band("主断点层", "优先修复", f"{funnel_break.get('阶段', '漏斗阶段')} 派生率 {_fmt_rate(funnel_break.get('派生率'))}，是全盘最紧的转化闸口", [f"{funnel_break.get('分子', '')} / {funnel_break.get('分母', '')}"]),
            _band("组合拆解层", "回到组合级复核", f"{_combo(topn_paid_rate)} 激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))}，{_combo(topn_weak_paid_rate)} 只有 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))}", [_combo(topn_paid_rate), _combo(topn_weak_paid_rate)]),
        ],
        representative_objects=[
            f"{funnel_break.get('阶段', '漏斗阶段')} 的派生率 {_fmt_rate(funnel_break.get('派生率'))} 决定本周优先排查的漏斗段。",
            f"{_combo(topn_paid_rate)} 与 {_combo(topn_weak_paid_rate)} 的激活到付费率差距，决定同一漏斗断点要拆到组合级处理。",
        ],
        business_conclusion=f"全盘最紧断点落在 {funnel_break.get('阶段', '漏斗阶段')}，预算动作不直接从总漏斗下发；先锁定断点，再用组合级 AARRR 找到承接强弱分化。",
        decision_path=f"Day 2 保留 {_combo(topn_paid_rate)} 的小步加码资格；{_combo(topn_weak_paid_rate)} 进入 Day 4 承接修复。",
        next_moves=[
            _action_line(object_name=_combo(topn_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))}", action="进入小步加码候选并同步看 roi/cac", metric="激活到付费率 / roi / cac", checkpoint="Day 2", owner="渠道运营"),
            _action_line(object_name=_combo(topn_weak_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))}", action="修复激活后付费权益和承接页", metric="注册到激活率 / 激活到付费率", checkpoint="Day 4", owner="活动运营"),
        ],
        risk_boundary="总漏斗只定位断点；预算迁移由组合级漏斗、ROI/CAC 和毛利表共同裁决。",
    )

    cards["aarrr_top12"] = _card_v3(
        card_id="aarrr_top12",
        table_name="Top12 渠道 × 流量来源 AARRR 差异表",
        table_question="哪些组合具备预算承接资格？",
        judgement_standard="组合漏斗是否具备预算承接资格",
        standard_formula="入选原因 + 点击到注册率 + 激活到付费率 + roi + cac + operating_cost。",
        object_bands=[
            _band("可迁入组合", "小步迁入", f"{_combo(topn_paid_rate)} 激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))}，后段承接更强", [_combo(topn_paid_rate)]),
            _band("承接断层组合", "先修复承接", f"{_combo(topn_weak_paid_rate)} 激活到付费率 {_fmt_rate(topn_weak_paid_rate.get('激活到付费率'))}，后段断层明显", [_combo(topn_weak_paid_rate)]),
            _band("高消耗复核组合", "裁决迁出或提效", f"{_combo(topn_cost)} 运营成本 {_fmt_num(topn_cost.get('operating_cost'))}，对全盘影响最大", [_combo(topn_cost)]),
        ],
        representative_objects=[
            f"{_combo(topn_click_reg)} 点击到注册率 {_fmt_rate(topn_click_reg.get('点击到注册率'))}，前段承接更顺。",
            f"{_combo(topn_paid_rate)} 激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))}，后段付费承接更强。",
            f"{_combo(topn_cost)} 成本 {_fmt_num(topn_cost.get('operating_cost'))}、roi {_fmt_num(topn_cost.get('roi'), 2)}、cac {_fmt_num(topn_cost.get('cac'), 2)}，优先进入预算裁决。",
        ],
        business_conclusion=f"Top12 是预算审查池，不是加码名单；{_combo(topn_paid_rate)} 具备承接资格，{_combo(topn_weak_paid_rate)} 先修复付费断层，{_combo(topn_cost)} 先做预算裁决。",
        decision_path="先按承接资格分层，再决定迁入、承接修复或高消耗复核。",
        next_moves=[
            _action_line(object_name=_combo(topn_paid_rate), trigger=f"激活到付费率 {_fmt_rate(topn_paid_rate.get('激活到付费率'))}", action="小步迁入预算", metric="paid_users / contribution_margin / roi", checkpoint="Day 5", owner="活动运营"),
            _action_line(object_name=_combo(topn_cost), trigger=f"运营成本 {_fmt_num(topn_cost.get('operating_cost'))}", action="裁决迁出、保留或提效", metric="operating_cost / contribution_margin / roi", checkpoint="Day 7", owner="运营负责人"),
        ],
        risk_boundary="组合漏斗回答承接资格；内容、活动、产品模块的归因由桥接实验验证。",
    )

    cards["roi_cac_quadrant"] = _card_v3(
        card_id="roi_cac_quadrant",
        table_name="真实投放回报 × 获客成本四象限表",
        table_question="哪些对象具备预算迁入资格？",
        judgement_standard="预算迁入资格",
        standard_formula="roi 高低 × cac 高低，并参考 paid_users、revenue、operating_cost。",
        object_bands=[
            _band("迁入池", "Day 2 小步迁入", f"{_combo(scale_up)} 高 roi / 低 cac", [f"roi {_fmt_num(scale_up.get('roi'), 2)}，cac {_fmt_num(scale_up.get('cac'), 2)}"]),
            _band("提效池", "先压获客成本", f"{_combo(efficiency)} 高 roi 但 cac 偏高", [f"roi {_fmt_num(efficiency.get('roi'), 2)}，cac {_fmt_num(efficiency.get('cac'), 2)}"]),
            _band("验证池", "低成本小样本验证", f"{_combo(verify)} cac 可控但 roi 偏低", [f"roi {_fmt_num(verify.get('roi'), 2)}，cac {_fmt_num(verify.get('cac'), 2)}"]),
            _band("冻结池", "Day 1 冻结", f"{_combo(stoploss)} 低 roi / 高 cac", [f"roi {_fmt_num(stoploss.get('roi'), 2)}，cac {_fmt_num(stoploss.get('cac'), 2)}"]),
        ],
        representative_objects=[
            f"{_combo(scale_up)} 与 {_combo(stoploss)} 的 roi 差 {_fmt_num(_num(scale_up.get('roi')) - _num(stoploss.get('roi')), 2)}，cac 差 {_fmt_num(_num(stoploss.get('cac')) - _num(scale_up.get('cac')), 2)}。",
            f"{_combo(efficiency)} 仍有回报基础，但获客成本先拖住放量资格。",
            f"{_combo(verify)} 成本压力较低，适合小样本验证而非大额迁入。",
        ],
        business_conclusion=f"预算迁移路径已经清晰：从 {_combo(stoploss)} 迁出，向 {_combo(scale_up)} 小步迁入；{_combo(efficiency)} 先提效，{_combo(verify)} 先验证。",
        decision_path="冻结池先止血，迁入池小步承接，提效池降 cac，验证池用低成本实验争取资格。",
        next_moves=[
            _action_line(object_name=_combo(stoploss), trigger=f"roi {_fmt_num(stoploss.get('roi'), 2)} / cac {_fmt_num(stoploss.get('cac'), 2)}", action="冻结新增预算", metric="roi / cac / contribution_margin", checkpoint="Day 1", owner="运营负责人"),
            _action_line(object_name=_combo(scale_up), trigger=f"roi {_fmt_num(scale_up.get('roi'), 2)} / cac {_fmt_num(scale_up.get('cac'), 2)}", action="小步迁入预算", metric="边际 roi / paid_users", checkpoint="Day 2", owner="渠道运营"),
        ],
        risk_boundary="四象限给预算资格；最终加码幅度由边际 roi 和毛利复盘裁决。",
    )

    cards["ctr_cpc_cpm"] = _card_v3(
        card_id="ctr_cpc_cpm",
        table_name="点击率 × 单次点击成本 × 千次曝光成本获客效率表",
        table_question="哪些点击是真正有效获客？",
        judgement_standard="有效获客效率",
        standard_formula="CTR + CPC + CPM + 点击到注册率 + 激活到付费率 + roi/cac。",
        object_bands=[
            _band("有效点击层", "保留入口并复核商业回报", f"{_combo(best_ctr)} CTR {_fmt_rate(best_ctr.get('CTR'))}，入口吸引最强", [_combo(best_ctr)]),
            _band("贵点击层", "降权或换流量包", f"{_combo(worst_cpc)} CPC {_fmt_num(worst_cpc.get('CPC'), 2)}，点击成本最高", [_combo(worst_cpc)]),
            _band("虚高点击层", "修承接再谈加码", f"{_combo(weak_ctr_roi)} roi {_fmt_num(weak_ctr_roi.get('roi'), 2)}，点击表现未转成回报", [_combo(weak_ctr_roi)]),
        ],
        representative_objects=[
            f"{_combo(best_ctr)} CTR {_fmt_rate(best_ctr.get('CTR'))}、点击到注册率 {_fmt_rate(best_ctr.get('点击到注册率'))}、roi {_fmt_num(best_ctr.get('roi'), 2)}。",
            f"{_combo(worst_cpc)} CPC {_fmt_num(worst_cpc.get('CPC'), 2)}、cac {_fmt_num(worst_cpc.get('cac'), 2)}。",
            f"{_combo(weak_ctr_roi)} roi {_fmt_num(weak_ctr_roi.get('roi'), 2)}，入口表现和商业回报脱节。",
        ],
        business_conclusion=f"CTR 高只给入口资格，预算资格由后续注册、付费和 roi 裁决；{_combo(best_ctr)} 可保留入口，{_combo(weak_ctr_roi)} 先修承接。",
        decision_path="有效点击层保留并交叉看 ROI/CAC；贵点击层降权；虚高点击层进入落地页和权益承接修复。",
        next_moves=[
            _action_line(object_name=_combo(best_ctr), trigger=f"CTR {_fmt_rate(best_ctr.get('CTR'))}", action="复制入口素材并设置点击到注册率阈值", metric="CTR / 点击到注册率 / roi", checkpoint="Day 2", owner="内容运营"),
            _action_line(object_name=_combo(worst_cpc), trigger=f"CPC {_fmt_num(worst_cpc.get('CPC'), 2)}", action="降权高价点击来源", metric="CPC / cac / paid_users", checkpoint="Day 3", owner="投放运营"),
        ],
        risk_boundary="该表裁决入口效率；后端商业化由付费和毛利承接表裁决。",
    )

    cards["cost_margin_share"] = _card_v3(
        card_id="cost_margin_share",
        table_name="成本占比 × 毛利占比经营质量表",
        table_question="成本是否兑现成毛利？",
        judgement_standard="成本是否兑现成毛利",
        standard_formula="毛利占比 - 成本占比，并联动 contribution_margin、roi、预算效率。",
        object_bands=[
            _band("花钱产毛利层", "保留并验证边际毛利", f"{_combo(strong_margin)} 毛利占比 {_fmt_rate(strong_margin.get('毛利占比'))} 高于成本占比 {_fmt_rate(strong_margin.get('成本占比'))}", [_combo(strong_margin)]),
            _band("花钱吞毛利层", "迁出或降权", f"{_combo(weak_margin)} 成本占比 {_fmt_rate(weak_margin.get('成本占比'))} 明显压过毛利占比 {_fmt_rate(weak_margin.get('毛利占比'))}", [_combo(weak_margin)]),
            _band("低影响观察层", "保留观察", "成本和毛利份额都低的对象先不占用本周预算裁决带宽", ["低成本低毛利对象池"]),
        ],
        representative_objects=[
            f"{_combo(strong_margin)} 预算效率 {_fmt_num(strong_margin.get('预算效率'), 2)}、贡献毛利 {_fmt_num(_row_number(strong_margin, 'contribution_margin'))}。",
            f"{_combo(weak_margin)} 预算效率 {_fmt_num(weak_margin.get('预算效率'), 2)}、运营成本 {_fmt_num(_row_number(weak_margin, 'operating_cost'))}。",
        ],
        business_conclusion=f"成本毛利标准把预算对象分成两类：{_combo(strong_margin)} 能把成本换成毛利，{_combo(weak_margin)} 正在消耗毛利空间。",
        decision_path=f"保留 {_combo(strong_margin)} 的迁入资格；{_combo(weak_margin)} 进入 Day 1/Day 2 迁出或降权。",
        next_moves=[
            _action_line(object_name=_combo(weak_margin), trigger=f"成本占比 {_fmt_rate(weak_margin.get('成本占比'))} / 毛利占比 {_fmt_rate(weak_margin.get('毛利占比'))}", action="降权或迁出预算", metric="成本占比 / 毛利占比 / 预算效率", checkpoint="Day 2", owner="运营负责人"),
            _action_line(object_name=_combo(strong_margin), trigger=f"预算效率 {_fmt_num(strong_margin.get('预算效率'), 2)}", action="保留为迁入候选并看边际毛利", metric="边际 contribution_margin", checkpoint="Day 7", owner="渠道运营"),
        ],
        risk_boundary="该表裁决利润承接；用户留存和口碑由用户质量表裁决。",
    )

    cards["user_quality_bridge"] = _card_v3(
        card_id="user_quality_bridge",
        table_name="用户质量与商业化承接桥接表",
        table_question="高质量人群能否被产品/活动承接？",
        judgement_standard="用户质量与商业承接是否形成桥接",
        standard_formula="用户质量侧：retention_d7 + nps + 增长质量分；商业承接侧：收入 + 付费用户 + 毛利率 + roi/cac。",
        object_bands=[
            _band("高质量经营池", "Day 3 深耕", f"{_combo(best_quality)} 增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}", [_combo(best_quality)]),
            _band("低质量降权池", "降权新增", f"{_combo(weak_quality)} 增长质量分低 {_fmt_num(weak_quality.get('增长质量分'), 2)}", [_combo(weak_quality)]),
            _band("强承接产品活动", "Day 5 做桥接实验", f"{_combo(best_paid)} 收入 {_fmt_num(best_paid.get('收入'))}、付费用户 {_fmt_num(best_paid.get('付费用户'))}", [_combo(best_paid)]),
            _band("弱承接产品活动", "修复权益或降权", f"{_combo(weak_paid)} roi {_fmt_num(weak_paid.get('roi'), 2)}", [_combo(weak_paid)]),
        ],
        representative_objects=[
            f"{_combo(best_quality)} 与 {_combo(weak_quality)} 的增长质量分差 {_fmt_num(quality_gap, 2)}，决定人群侧保留和降权。",
            f"{_combo(best_paid)} 与 {_combo(weak_paid)} 的 roi 差 {_fmt_num(paid_roi_gap, 2)}，决定商业承接侧加码和修复。",
            f"用户质量池和商业承接池是两把对象粒度，桥接实验负责把二者连接起来。",
        ],
        business_conclusion=f"Day 3 先锁定 {_combo(best_quality)} 这类高质量人群；Day 5 用 {_combo(best_paid)} 这类强承接产品活动做桥接实验，避免把两个独立对象池拼成假因果。",
        decision_path="高质量人群保留，低质量人群降权；强承接产品活动做定向实验，弱承接组合先修权益和毛利。",
        next_moves=[
            _action_line(object_name=_combo(best_quality), trigger=f"增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)} / retention_d7 {_fmt_rate(best_quality.get('retention_d7'))}", action="列入高质量经营池", metric="retention_d7 / nps / paid_users", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name=_combo(best_paid), trigger=f"收入 {_fmt_num(best_paid.get('收入'))} / 付费用户 {_fmt_num(best_paid.get('付费用户'))}", action="承接高质量人群小样本实验", metric="paid_users / contribution_margin / retention_d7", checkpoint="Day 5", owner="产品运营"),
        ],
        risk_boundary="桥接实验前，只能形成承接假设；实验结果决定是否扩大预算。",
    )

    cards["retention_nps_quality"] = _card_v3(
        card_id="retention_nps_quality",
        table_name="留存 × 口碑净推荐值质量象限表",
        table_question="新增用户是否值得继续经营？",
        judgement_standard="新增用户经营质量",
        standard_formula="retention_d7 + nps + 增长质量分，并参考 paid_users 和 roi。",
        object_bands=[
            _band("高质量经营池", "保留深耕", f"{_combo(best_quality)} retention_d7 {_fmt_rate(best_quality.get('retention_d7'))}、nps {_fmt_num(best_quality.get('nps'), 2)}", [_combo(best_quality)]),
            _band("低质量降权池", "暂停粗放扩量", f"{_combo(weak_quality)} 增长质量分 {_fmt_num(weak_quality.get('增长质量分'), 2)}", [_combo(weak_quality)]),
        ],
        representative_objects=[
            f"{_combo(best_quality)} 增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}，{_combo(weak_quality)} {_fmt_num(weak_quality.get('增长质量分'), 2)}，差 {_fmt_num(quality_gap, 2)}。",
            f"{_combo(best_quality)} 的 retention_d7 {_fmt_rate(best_quality.get('retention_d7'))} 和 NPS {_fmt_num(best_quality.get('nps'), 2)} 给 Day 3 保留资格。",
        ],
        business_conclusion=f"新增质量分化已经足够支撑 Day 3 取舍：{_combo(best_quality)} 保留深耕，{_combo(weak_quality)} 降权复核。",
        decision_path="预算和运营资源优先投向高质量经营池；低质量池先修人群包和城市层级。",
        next_moves=[
            _action_line(object_name=_combo(best_quality), trigger=f"增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}", action="保留并匹配商业承接实验", metric="retention_d7 / nps / paid_users", checkpoint="Day 3", owner="用户运营"),
            _action_line(object_name=_combo(weak_quality), trigger=f"增长质量分 {_fmt_num(weak_quality.get('增长质量分'), 2)}", action="暂停扩量并复核人群包", metric="retention_d7 / nps", checkpoint="Day 7", owner="用户运营"),
        ],
        risk_boundary="用户质量表裁决人群经营资格；收入承接仍由产品/活动表验证。",
    )

    cards["paid_users_revenue"] = _card_v3(
        card_id="paid_users_revenue",
        table_name="付费用户 × 收入承接表",
        table_question="产品/活动是否把用户转成收入和毛利？",
        judgement_standard="商业化承接强度",
        standard_formula="收入 + 付费用户 + 贡献毛利 + 毛利率 + roi/cac。",
        object_bands=[
            _band("强承接层", "保留并复核边际毛利", f"{_combo(best_paid)} 收入 {_fmt_num(best_paid.get('收入'))}、付费用户 {_fmt_num(best_paid.get('付费用户'))}", [_combo(best_paid)]),
            _band("高收入低效率层", "修权益和成本", f"{_combo(weak_paid)} roi {_fmt_num(weak_paid.get('roi'), 2)}", [_combo(weak_paid)]),
        ],
        representative_objects=[
            f"{_combo(best_paid)} 收入 {_fmt_num(best_paid.get('收入'))}、付费用户 {_fmt_num(best_paid.get('付费用户'))}、roi {_fmt_num(best_paid.get('roi'), 2)}。",
            f"{_combo(weak_paid)} roi {_fmt_num(weak_paid.get('roi'), 2)}、cac {_fmt_num(weak_paid.get('cac'), 2)}，承接效率弱。",
        ],
        business_conclusion=f"{_combo(best_paid)} 是当前最强商业承接对象；{_combo(weak_paid)} 显示付费或收入规模并不自动等于经营效率。",
        decision_path="强承接层进入 Day 5 定向承接；低效率层先修定价、权益和活动成本。",
        next_moves=[
            _action_line(object_name=_combo(best_paid), trigger=f"收入 {_fmt_num(best_paid.get('收入'))} / 付费用户 {_fmt_num(best_paid.get('付费用户'))}", action="复核边际毛利后承接高质量人群", metric="contribution_margin / roi", checkpoint="Day 5", owner="产品运营"),
            _action_line(object_name=_combo(weak_paid), trigger=f"roi {_fmt_num(weak_paid.get('roi'), 2)}", action="修复定价、权益和活动成本", metric="roi / cac / 毛利率", checkpoint="Day 5", owner="活动运营"),
        ],
        risk_boundary="该表裁决商业承接；长期价值由后续 LTV 和留存窗口复核。",
    )

    cards["daily_action_board"] = _card_v3(
        card_id="daily_action_board",
        table_name="D1-D7 日动作执行板",
        table_question="动作是否按经营风险优先级排序？",
        judgement_standard="经营风险优先级",
        standard_formula="stoploss > budget migration > segment choice > content/campaign bridge > monetization bridge > metric audit > weekly decision。",
        object_bands=[
            _band("先止损", "Day 1", f"{_object_label(day1)} 承接冻结/止损动作", [str(day1.get("this_day_action") or "")]),
            _band("再迁移", "Day 2", f"{_object_label(day2)} 承接预算重排", [str(day2.get("this_day_action") or "")]),
            _band("最后复盘", "Day 7", f"{_object_label(day7)} 裁决下周 backlog", [str(day7.get("this_day_action") or "")]),
        ],
        representative_objects=[
            f"Day 1：{_object_label(day1)}，指标 {day1.get('success_metric', '')}，检查点 {day1.get('next_checkpoint', '')}。",
            f"Day 2：{_object_label(day2)}，指标 {day2.get('success_metric', '')}，检查点 {day2.get('next_checkpoint', '')}。",
            f"Day 7：{_object_label(day7)}，指标 {day7.get('success_metric', '')}，检查点 {day7.get('next_checkpoint', '')}。",
        ],
        business_conclusion="日动作层按风险排序：先止损，再迁移预算，再做人群和承接，最后用周复盘裁决下周动作。",
        decision_path="Day 1 不做平均优化；Day 2 才允许迁入；Day 7 裁决继续加码、降权或进入 backlog。",
        next_moves=[
            _action_line(object_name=_object_label(day1), trigger=str(day1.get("dependency") or "高风险对象优先止损"), action=str(day1.get("this_day_action") or "冻结预算"), metric=str(day1.get("success_metric") or "roi / cac"), checkpoint=str(day1.get("next_checkpoint") or "Day 1"), owner=str(day1.get("owner_role") or "运营负责人")),
            _action_line(object_name=_object_label(day2), trigger=str(day2.get("dependency") or "预算迁移"), action=str(day2.get("this_day_action") or "小步迁入预算"), metric=str(day2.get("success_metric") or "边际 roi"), checkpoint=str(day2.get("next_checkpoint") or "Day 2"), owner=str(day2.get("owner_role") or "渠道运营")),
        ],
        risk_boundary="执行板规定动作顺序；效果由对应检查点指标确认。",
    )

    owner_first = _first(owner_rows)
    owner_second = _first(owner_rows[1:2])
    owner_third = _first(owner_rows[2:3])
    cards["owner_schedule"] = _card_v3(
        card_id="owner_schedule",
        table_name="Owner 责任视图日程板",
        table_question="责任是否能被对象、指标、检查点闭环？",
        judgement_standard="责任闭环完整度",
        standard_formula="责任角色 + 日期槽位 + 对象 + 当日动作 + 成功指标 + 下一检查点。",
        object_bands=[
            _band("可闭环责任", "当日执行", f"{owner_first.get('owner_role', '运营负责人')} 已绑定对象和检查点", [_object_label(owner_first)]),
            _band("跨角色责任", "协同执行", f"{owner_second.get('owner_role', '用户运营')} 承接跨角色动作", [_object_label(owner_second)]),
            _band("周复盘责任", "裁决下周动作", f"{owner_third.get('owner_role', '运营负责人')} 负责检查点闭环", [_object_label(owner_third)]),
        ],
        representative_objects=[
            f"{owner_first.get('owner_role', '运营负责人')}：{owner_first.get('day_label', '')}，对象 {_object_label(owner_first)}，指标 {owner_first.get('success_metric', '')}。",
            f"{owner_second.get('owner_role', '用户运营')}：{owner_second.get('day_label', '')}，对象 {_object_label(owner_second)}，指标 {owner_second.get('success_metric', '')}。",
            f"{owner_third.get('owner_role', '运营负责人')}：{owner_third.get('day_label', '')}，对象 {_object_label(owner_third)}，指标 {owner_third.get('success_metric', '')}。",
        ],
        business_conclusion="责任视图把经营判断落到角色、对象和检查点，避免动作停留在建议清单。",
        decision_path="缺对象、缺指标或缺检查点的动作不进入本周执行板；已闭环动作按日期槽位复盘。",
        next_moves=[
            _action_line(object_name=_object_label(owner_first), trigger=str(owner_first.get("theme") or "责任闭环"), action=str(owner_first.get("this_day_action") or "执行并回填检查点"), metric=str(owner_first.get("success_metric") or "roi / cac"), checkpoint=str(owner_first.get("next_checkpoint") or owner_first.get("day_label") or "Day 1"), owner=str(owner_first.get("owner_role") or "运营负责人")),
            _action_line(object_name=_object_label(owner_second), trigger=str(owner_second.get("theme") or "跨角色协同"), action=str(owner_second.get("this_day_action") or "执行协同动作"), metric=str(owner_second.get("success_metric") or "paid_users"), checkpoint=str(owner_second.get("next_checkpoint") or owner_second.get("day_label") or "Day 3"), owner=str(owner_second.get("owner_role") or "用户运营")),
        ],
        risk_boundary="责任表裁决谁执行；动作正确性仍由前面的对象表和检查点指标复核。",
    )

    return {
        "version": "ops_table_reading_cards_v3",
        "source": "deterministic_internet_ops_standard_driven_reading",
        "card_count": len(cards),
        "rules": {
            "one_judgement_standard_per_table": True,
            "object_bands_serve_the_same_standard": True,
            "business_conclusion_before_next_moves": True,
            "avoid_methodology_tone": True,
        },
        "cards": cards,
    }


def write_ops_table_reading_cards(workspace: Path) -> dict[str, Any]:
    ensure_ops_management_fact_contracts(workspace)
    payload = build_ops_table_reading_cards(workspace)
    path = workspace / TABLE_READING_CARDS_NAME
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload


def build_ops_narrative_sections(workspace: Path) -> dict[str, Any]:
    evidence_payload = write_ops_table_reading_cards(workspace)
    cards = evidence_payload.get("cards") or {}
    sections: list[dict[str, Any]] = []
    for idx, card_id in enumerate(CORE_READING_CARD_IDS, start=1):
        card = cards.get(card_id)
        if not isinstance(card, dict):
            continue
        context = NARRATIVE_SECTION_CONTEXT.get(card_id, {})
        markdown = render_standard_card_as_narrative(card, context)
        paragraphs = [
            part.strip()
            for part in re.split(r"\n{2,}", markdown)
            if part.strip() and not part.strip().startswith("### ")
        ]
        sections.append(
            {
                "section_id": card_id,
                "order": idx,
                "title": context.get("title") or card.get("table_name") or card_id,
                "source_card_id": card_id,
                "style": "continuous_business_narrative",
                "markdown": markdown,
                "paragraph_count": len(paragraphs),
                "transition": context.get("next") or "",
            }
        )
    return {
        "version": "ops_narrative_sections_v1",
        "source": TABLE_READING_CARDS_NAME,
        "section_count": len(sections),
        "rules": {
            "cards_are_evidence_not_reader_contract": True,
            "no_contract_field_headings": True,
            "chain_logic": "business_question -> split -> decision -> next_section",
        },
        "sections": sections,
    }


def write_ops_narrative_sections(workspace: Path) -> dict[str, Any]:
    payload = build_ops_narrative_sections(workspace)
    path = workspace / NARRATIVE_SECTIONS_NAME
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload


def render_ops_narrative_sections_markdown(workspace: Path) -> str:
    payload = write_ops_narrative_sections(workspace)
    sections = ["## 核心经营链路：从预算止损到承接实验"]
    for section in payload.get("sections") or []:
        if isinstance(section, dict) and section.get("markdown"):
            sections.append(str(section.get("markdown")))
    return _strip_contract_label_text("\n\n".join(section for section in sections if section).strip()) + "\n"


def render_ops_table_reading_cards_markdown(workspace: Path) -> str:
    return render_ops_narrative_sections_markdown(workspace)


def build_internet_ops_management_brief_markdown(workspace: Path) -> str:
    asset_dir = workspace / "source_visual_assets"
    fact_contracts = ensure_ops_management_fact_contracts(workspace)
    thresholds_payload = fact_contracts.get("thresholds") if isinstance(fact_contracts.get("thresholds"), dict) else {}
    action_rules_payload = fact_contracts.get("action_rules") if isinstance(fact_contracts.get("action_rules"), dict) else {}
    topn = _read_csv_rows(asset_dir / "ops_channel_source_aarrr_topn_small_multiples.csv")
    aarrr_total = _read_csv_rows(asset_dir / "ops_aarrr_derived_funnel_rates.csv")
    roi_rows = _read_csv_rows(asset_dir / "ops_roi_cac_quadrant.csv")
    ctr_rows = _read_csv_rows(asset_dir / "ops_ctr_cpc_cpm_efficiency.csv")
    cost_rows = _read_csv_rows(asset_dir / "ops_cost_margin_share_matrix.csv")
    paid_rows = _read_csv_rows(asset_dir / "ops_paid_users_revenue_bubble.csv")
    quality_rows = _read_csv_rows(asset_dir / "ops_retention_nps_quality_quadrant.csv")
    day_rows = _daily_actions(workspace)
    owner_rows = _read_csv_rows(workspace / "ops_daily_action_owner_matrix.csv")
    table_cards = write_ops_table_reading_cards(workspace)
    write_ops_narrative_sections(workspace)
    management_quadrant_index = write_ops_management_quadrant_index(workspace)
    derived_metric_diagnosis_cards = write_ops_derived_metric_diagnosis_cards(workspace, management_quadrant_index)
    roi_scale_index = _management_band_row(management_quadrant_index, "ops_roi_cac_quadrant", "加码象限")
    roi_stoploss_index = _management_band_row(management_quadrant_index, "ops_roi_cac_quadrant", "止损象限")
    ctr_effective_index = _management_band_row(management_quadrant_index, "ops_ctr_cpc_cpm_efficiency", "有效点击池")
    ctr_expensive_index = _management_band_row(management_quadrant_index, "ops_ctr_cpc_cpm_efficiency", "贵点击池")
    cost_margin_positive_index = _management_band_row(management_quadrant_index, "ops_cost_margin_share_matrix", "花钱产毛利池")
    cost_margin_negative_index = _management_band_row(management_quadrant_index, "ops_cost_margin_share_matrix", "花钱吞毛利池")
    quality_high_index = _management_band_row(management_quadrant_index, "ops_retention_nps_quality_quadrant", "高质量经营池")
    paid_strong_index = _management_band_row(management_quadrant_index, "ops_paid_users_revenue_bubble", "强承接池")
    threshold_summary_rows: list[dict[str, Any]] = []
    for chart in list(thresholds_payload.get("charts") or []):
        if not isinstance(chart, dict):
            continue
        metric_text = "；".join(
            f"{item.get('metric_label') or item.get('metric')}：中位数 {_fmt_value(str(item.get('metric') or ''), item.get('median'))} / 平均数 {_fmt_value(str(item.get('metric') or ''), item.get('mean'))} / 加权平均 {_fmt_value(str(item.get('metric') or ''), item.get('weighted_mean')) if item.get('weighted_mean') is not None else 'n/a'}"
            for item in list(chart.get("metric_summaries") or [])[:3]
            if isinstance(item, dict)
        )
        borderline = "；".join(
            str(item.get("object_name") or "")
            for item in list(chart.get("borderline_objects") or [])[:4]
            if isinstance(item, dict)
        )
        threshold_summary_rows.append(
            {
                "图表": chart.get("chart_title") or chart.get("chart_id"),
                "阈值口径": chart.get("threshold_basis") or "",
                "关键线": metric_text,
                "边界对象": borderline or "无明显边界对象",
            }
        )
    action_rule_rows = [
        {
            "日期": row.get("day_label"),
            "对象": row.get("object_name"),
            "预算规则": row.get("budget_rule"),
            "触发阈值": row.get("trigger_threshold"),
            "停止条件": row.get("stop_condition"),
            "Owner": row.get("owner"),
            "检查点": row.get("checkpoint"),
        }
        for row in list(action_rules_payload.get("rules") or [])
        if isinstance(row, dict)
    ]

    detail_source = topn or roi_rows
    total_revenue = _sum(detail_source, "revenue") or _sum(roi_rows, "revenue")
    total_cost = _sum(detail_source, "operating_cost") or _sum(roi_rows, "operating_cost")
    total_margin = _sum(detail_source, "contribution_margin") or _sum(roi_rows, "contribution_margin")
    total_paid = _sum(detail_source, "paid_users") or _sum(roi_rows, "paid_users")
    blended_roi = (total_revenue / total_cost) if total_cost else 0.0
    blended_margin_rate = (total_margin / total_revenue) if total_revenue else 0.0

    roi_rows = _with_roi_quadrants(roi_rows)
    roi_quadrant_reps = _representative_roi_quadrants(roi_rows)
    best_roi = _first(_top(roi_rows, "roi", count=1))
    worst_cac = _first(_top(roi_rows, "cac", count=1))
    scale_up_rep = _first([row for row in roi_quadrant_reps if str(row.get("象限") or "").startswith("加码象限")])
    stoploss_rep = _first([row for row in roi_quadrant_reps if str(row.get("象限") or "").startswith("止损象限")])
    best_ctr = _first(_top(ctr_rows, "CTR", count=1))
    weak_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")))[:1])
    strong_margin = _first(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")), reverse=True)[:1])
    best_paid = _first(_top(paid_rows, "收入", count=1))
    weak_paid_roi = _first(_top(paid_rows, "roi", reverse=False, count=1))
    best_quality = _first(_top(quality_rows, "增长质量分", count=1))
    weak_quality = _first(_top(quality_rows, "增长质量分", reverse=False, count=1))
    topn_first = _first(topn)
    topn_cost = _first(_top(topn, "operating_cost", count=1))

    sections: list[str] = [
        "# 互联网运营高密度精简管理版",
        "",
        "本版不按页数压缩，而按管理层决策链组织：先确认同一对象的 KPI 口径，再判断预算效率有没有被稀释，随后拆漏斗、看预算迁移、检查入口效率、验证毛利承接，最后把用户/产品桥接和 Day 1-Day 7 动作落到 owner。所有 `渠道 × 流量来源` 的 roi、cac、收入、运营成本、贡献毛利和付费用户都来自同一份权威 KPI 合同，后面的图表只追加视角，不改写事实。",
        "",
        "## 1. 管理层总判断：先止损，再重排，再加码",
        "",
        (
            f"管理层第一件事是判断预算有没有被好对象接住。Top12 重点组合合计收入 {_fmt_num(total_revenue)}、运营成本 {_fmt_num(total_cost)}、贡献毛利 {_fmt_num(total_margin)}，"
            f"但混合 roi 只有 {_fmt_num(blended_roi, 2)}，低于 {_combo(best_roi)} 的 {_fmt_num(best_roi.get('roi'), 2)}。"
            f"差距指向一个很具体的问题：好对象承接不够、差对象仍在吃预算；{_combo(worst_cac)} 的 cac 达到 {_fmt_num(worst_cac.get('cac'), 2)}，高成本没有换来同等回报。"
            f"所以本周顺序很明确：Day 1 先冻结高 CAC/低 roi/负毛利对象，Day 2 再把释放出来的 20%-30% 预算小步迁入高 roi、可承接组合，T+2 如果边际 roi 低于 4.0 或 cac 高于 100 就停止继续迁入。"
        ),
        "",
        _markdown_table(
            [
                {"指标": "收入", "当前读数": _fmt_num(total_revenue), "管理含义": "收入已进入经营盘，下一步看预算效率分层"},
                {"指标": "运营成本", "当前读数": _fmt_num(total_cost), "管理含义": "成本集中对象优先进入冻结/迁出裁决"},
                {"指标": "贡献毛利", "当前读数": _fmt_num(total_margin), "管理含义": "毛利仍有缓冲，预算迁移有操作空间"},
                {"指标": "付费用户", "当前读数": _fmt_num(total_paid), "管理含义": "付费规模支撑迁入池承接测试"},
                {"指标": "混合 roi", "当前读数": _fmt_num(blended_roi, 2), "管理含义": "低于迁入池代表对象，预算效率被稀释"},
                {"指标": "毛利率", "当前读数": _fmt_rate(blended_margin_rate), "管理含义": "负毛利或低毛利对象优先止损"},
            ],
            ["指标", "当前读数", "管理含义"],
        ),
        "",
        "### 阈值口径和边界对象",
        "",
        (
            f"后文所有象限都用同一套阈值说明，不再把接近切线的对象硬贴标签。ROI/CAC 图用中位数切线，并把距离 roi 或 cac 切线 5% 以内的对象列为边界对象；"
            f"当前 {_threshold_line(thresholds_payload, 'ops_roi_cac_quadrant', 'roi')}，{_threshold_line(thresholds_payload, 'ops_roi_cac_quadrant', 'cac')}。"
            "只比中位线高一点或低一点的对象进入验证或提效动作，避免被切线误伤。"
        ),
        "",
        _markdown_table(threshold_summary_rows, ["图表", "阈值口径", "关键线", "边界对象"], limit=5),
        "",
        _render_table_reading_card(table_cards, "executive_metric_summary"),
        "",
        "## 2. 增长漏斗：先锁定断点，再拆组合承接资格",
        "",
        (
            f"总漏斗先回答“哪一步最卡”，不能直接替某个渠道下预算动作。"
            f"{_combo(topn_first)} 被选入 Top12 的原因是“{topn_first.get('入选原因', 'TopN 经营覆盖')}”，"
            f"其曝光 {_fmt_num(topn_first.get('impressions'))}、点击 {_fmt_num(topn_first.get('clicks'))}、注册 {_fmt_num(topn_first.get('registrations'))}、激活 {_fmt_num(topn_first.get('activations'))}、付费 {_fmt_num(topn_first.get('paid_users'))}，"
            f"点击率 {_fmt_rate(topn_first.get('点击率'))}、点击到注册率 {_fmt_rate(topn_first.get('点击到注册率'))}、激活到付费率 {_fmt_rate(topn_first.get('激活到付费率'))}。"
            f"这类组合的价值在于把总断点拆成具体对象：{_combo(topn_cost)} 运营成本 {_fmt_num(topn_cost.get('operating_cost'))}，先进入预算裁决；高付费承接组合才进入迁入候选。"
        ),
        "",
        "![增长漏斗派生率图（AARRR）](source_visual_assets/ops_aarrr_derived_funnel_rates.png)",
        "",
        _markdown_table(aarrr_total, ["阶段", "派生率", "分子", "分母"], limit=5) if aarrr_total else "",
        "",
        _render_table_reading_card(table_cards, "aarrr_total"),
        "",
        "![Top12 渠道 × 流量来源 AARRR 差异图组](source_visual_assets/ops_channel_source_aarrr_topn_small_multiples.png)",
        "",
        _markdown_table(topn, ["展示排序", "channel", "traffic_source", "入选原因", "impressions", "clicks", "registrations", "activations", "paid_users", "点击率", "点击到注册率", "激活到付费率", "roi", "cac"], limit=12),
        "",
        _render_table_reading_card(table_cards, "aarrr_top12"),
        "",
        "## 3. 真实投放回报 × 获客成本：结论先行，预算要从止损象限迁向可加码象限",
        "",
        (
            f"ROI/CAC 这页直接决定预算流向：预算从“{stoploss_rep.get('象限')}”的 {_combo(stoploss_rep)} 迁出，"
            f"向“{scale_up_rep.get('象限')}”的 {_combo(scale_up_rep)} 小步迁入。"
            f"{_combo(scale_up_rep)} roi {_fmt_num(scale_up_rep.get('roi'), 2)}、cac {_fmt_num(scale_up_rep.get('cac'), 2)}、付费用户 {_fmt_num(scale_up_rep.get('paid_users'))}；"
            f"{_combo(stoploss_rep)} roi {_fmt_num(stoploss_rep.get('roi'), 2)}、cac {_fmt_num(stoploss_rep.get('cac'), 2)}、运营成本 {_fmt_num(stoploss_rep.get('operating_cost'))}。"
            f"从象限池的加权平均看，加码池{_metric_distribution_fact(roi_scale_index, 'roi')}、{_metric_distribution_fact(roi_scale_index, 'cac')}；"
            f"止损池{_metric_distribution_fact(roi_stoploss_index, 'roi')}、{_metric_distribution_fact(roi_stoploss_index, 'cac')}。"
            f"{_derived_metric_diagnosis_text(derived_metric_diagnosis_cards, 'ops_roi_cac_quadrant')}"
            f"执行上按池子处理：冻结池先止血，迁入池小步承接，提效池降 cac，验证池用低成本实验争取资格。"
        ),
        "",
        "![真实投放回报 × 获客成本象限解读](source_visual_assets/ops_roi_cac_quadrant.png)",
        "",
        _markdown_table(roi_quadrant_reps, ["象限", "结论", "图中序号", "channel", "traffic_source", "paid_users", "revenue", "operating_cost", "roi", "cac", "建议动作"], limit=4),
        "",
        _render_management_quadrant_index_table(management_quadrant_index, "ops_roi_cac_quadrant", "ROI/CAC 四象限全量渠道 × 流量来源"),
        "",
        _render_table_reading_card(table_cards, "roi_cac_quadrant"),
        "",
        "## 4. 点击率 × 单次点击成本 × 千次曝光成本：前段效率决定预算能不能放大",
        "",
        (
            f"入口效率页检查点击有没有继续变成注册、激活、付费和回报。{_combo(best_ctr)} CTR {_fmt_rate(best_ctr.get('CTR'))}、CPC {_fmt_num(best_ctr.get('CPC'), 2)}、CPM {_fmt_num(best_ctr.get('CPM'), 2)}，"
            f"入口吸引更强；但预算资格还要看点击到注册率 {_fmt_rate(best_ctr.get('点击到注册率'))}、后段付费和 roi。"
            f"分层后的加权平均进一步把入口质量拉开：有效点击池{_metric_distribution_fact(ctr_effective_index, '点击率')}、{_metric_distribution_fact(ctr_effective_index, 'CPC')}；"
            f"贵点击池{_metric_distribution_fact(ctr_expensive_index, 'CPC')}、{_metric_distribution_fact(ctr_expensive_index, 'cac')}。"
            f"{_derived_metric_diagnosis_text(derived_metric_diagnosis_cards, 'ops_ctr_cpc_cpm_efficiency')}"
            f"本周对入口的处理很窄：有效点击层保留并交叉看 ROI/CAC；贵点击层降权；虚高点击层进入落地页和权益承接修复。"
        ),
        "",
        "![点击率 × 点击成本获客效率解读](source_visual_assets/ops_ctr_cpc_cpm_efficiency.png)",
        "",
        _markdown_table(_top(ctr_rows, "CTR", count=10), ["图中序号", "channel", "traffic_source", "点击率", "点击到注册率", "注册到激活率", "激活到付费率", "roi", "cac", "对象组合"], limit=10),
        "",
        _render_management_quadrant_index_table(management_quadrant_index, "ops_ctr_cpc_cpm_efficiency", "CTR/CPC/CPM 获客效率分层"),
        "",
        _render_table_reading_card(table_cards, "ctr_cpc_cpm"),
        "",
        "## 5. 成本占比 × 毛利占比：识别“花得多但不产毛利”的对象",
        "",
        (
            f"成本毛利页把预算迁移再过一遍利润门。{_combo(weak_margin)} 成本占比 {_fmt_rate(weak_margin.get('成本占比'))}、毛利占比 {_fmt_rate(weak_margin.get('毛利占比'))}、预算效率 {_fmt_num(weak_margin.get('预算效率'), 2)}，"
            f"属于花钱吞毛利对象；{_combo(strong_margin)} 则保留为毛利承接候选。"
            f"分层后的加权平均显示，花钱产毛利池{_metric_distribution_fact(cost_margin_positive_index, '预算效率')}、{_metric_distribution_fact(cost_margin_positive_index, '毛利占比')}；"
            f"花钱吞毛利池{_metric_distribution_fact(cost_margin_negative_index, '预算效率')}、{_metric_distribution_fact(cost_margin_negative_index, '成本占比')}。"
            f"{_derived_metric_diagnosis_text(derived_metric_diagnosis_cards, 'ops_cost_margin_share_matrix')}"
            f"动作上，花钱吞毛利对象进入迁出或降权，花钱产毛利对象保留迁入资格并看边际毛利。"
        ),
        "",
        "![成本占比 × 毛利占比矩阵](source_visual_assets/ops_cost_margin_share_matrix.png)",
        "",
        _markdown_table(sorted(cost_rows, key=lambda row: _num(row.get("毛利占比")) - _num(row.get("成本占比")))[:10], ["图中序号", "channel", "traffic_source", "收入", "运营成本", "贡献毛利", "成本占比", "毛利占比", "预算效率", "对象组合"], limit=10),
        "",
        _render_management_quadrant_index_table(management_quadrant_index, "ops_cost_margin_share_matrix", "成本/毛利兑现分层"),
        "",
        _render_table_reading_card(table_cards, "cost_margin_share"),
        "",
        "## 6. 用户质量与商业化承接：用桥接标准连接两个对象池",
        "",
        (
            f"用户质量和商业承接不能硬拼成因果，但可以形成可验证的桥接实验。{_combo(best_quality)} 增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)}、7日留存 {_fmt_rate(best_quality.get('retention_d7'))}、NPS {_fmt_num(best_quality.get('nps'), 2)}，"
            f"进入 Day 3 高质量经营池；{_combo(best_paid)} 收入 {_fmt_num(best_paid.get('收入'))}、付费用户 {_fmt_num(best_paid.get('付费用户'))}、毛利率 {_fmt_rate(best_paid.get('毛利率'))}，"
            f"进入 Day 5 强承接产品活动池。{_combo(weak_quality)} 与 { _combo(weak_paid_roi)} 分别代表人群质量和商业承接的风险端。"
            f"加权平均口径下，高质量经营池{_metric_distribution_fact(quality_high_index, 'retention_d7')}、{_metric_distribution_fact(quality_high_index, 'nps')}；"
            f"强承接池{_metric_distribution_fact(paid_strong_index, '毛利率')}、{_metric_distribution_fact(paid_strong_index, 'roi')}。"
            f"{_derived_metric_diagnosis_text(derived_metric_diagnosis_cards, 'ops_retention_nps_quality_quadrant')}"
            f"{_derived_metric_diagnosis_text(derived_metric_diagnosis_cards, 'ops_paid_users_revenue_bubble')}"
            f"本周只做有边界的桥接：高质量人群保留，低质量人群降权；强承接产品活动做定向实验，弱承接组合先修权益和毛利。"
        ),
        "",
        _markdown_table(
            [
                {
                    "判断层": "用户质量池",
                    "代表对象": _combo(best_quality),
                    "关键证据": f"增长质量分 {_fmt_num(best_quality.get('增长质量分'), 2)} / 7日留存 {_fmt_rate(best_quality.get('retention_d7'))} / NPS {_fmt_num(best_quality.get('nps'), 2)}",
                    "边界说明": "产品模块承接由 Day 5 小样本实验确认",
                    "下一动作": "Day 3 保留并深耕该人群城市组合",
                },
                {
                    "判断层": "商业承接池",
                    "代表对象": _combo(best_paid),
                    "关键证据": f"收入 {_fmt_num(best_paid.get('收入'))} / 付费用户 {_fmt_num(best_paid.get('付费用户'))} / 毛利率 {_fmt_rate(best_paid.get('毛利率'))}",
                    "边界说明": "高质量人群购买偏好由桥接实验确认",
                    "下一动作": "Day 5 用该模块活动做定向承接实验",
                },
                {
                    "判断层": "联动缺口",
                    "代表对象": f"{_combo(best_quality)} → {_combo(best_paid)}",
                    "关键证据": "两张表对象粒度不同，实验或人群映射负责连接",
                    "边界说明": "桥接实验前只形成承接假设",
                    "下一动作": "用高质量人群 × 高毛利模块做小样本承接验证",
                },
            ],
            ["判断层", "代表对象", "关键证据", "边界说明", "下一动作"],
        ),
        "",
        _render_table_reading_card(table_cards, "user_quality_bridge"),
        "",
        "![留存 × 口碑净推荐值质量象限图（NPS）](source_visual_assets/ops_retention_nps_quality_quadrant.png)",
        "",
        _markdown_table(_top(quality_rows, "增长质量分", count=8), ["图中序号", "user_segment", "city_tier", "付费用户", "收入", "retention_d7", "nps", "增长质量分", "对象组合"], limit=8),
        "",
        _render_management_quadrant_index_table(management_quadrant_index, "ops_retention_nps_quality_quadrant", "留存/NPS 用户质量分层"),
        "",
        _render_table_reading_card(table_cards, "retention_nps_quality"),
        "",
        "![付费用户 × 收入承接气泡图](source_visual_assets/ops_paid_users_revenue_bubble.png)",
        "",
        _markdown_table(_top(paid_rows, "收入", count=8), ["图中序号", "product_module", "campaign", "付费用户", "收入", "贡献毛利", "毛利率", "roi", "cac", "对象组合"], limit=8),
        "",
        _render_management_quadrant_index_table(management_quadrant_index, "ops_paid_users_revenue_bubble", "付费/收入商业承接分层"),
        "",
        _render_table_reading_card(table_cards, "paid_users_revenue"),
        "",
        "## 7. Day 1-Day 7：动作顺序服从经营风险优先级",
        "",
        (
            "执行层按风险排序。Day 1 先止损，因为高 CAC、低 roi、负毛利和低留存对象会继续吞掉预算；Day 2 做渠道 × 流量来源预算迁移；Day 3-5 分别处理人群区域、内容活动、产品商业化承接；Day 6-7 做口径复核和 backlog 决策。跳过 Day 1 会放大错误对象；缺少 Day 7 复盘会切断预算迁移闭环。"
        ),
        "",
        "### 管理层可执行动作规则",
        "",
        _markdown_table(action_rule_rows, ["日期", "对象", "预算规则", "触发阈值", "停止条件", "Owner", "检查点"], limit=8),
        "",
        _markdown_table(day_rows, ["day_label", "theme", "object_name", "owner_role", "this_day_action", "success_metric", "next_checkpoint"], limit=18),
        "",
        _render_table_reading_card(table_cards, "daily_action_board"),
        "",
        "## 8. Owner 责任视图：每个角色只看自己能改变的对象",
        "",
        (
            "责任视图只保留能被对象、指标和检查点闭环的动作。渠道运营负责预算重排，用户运营负责人群和区域取舍，内容/活动运营负责承接，运营负责人和数据分析负责止损与口径复核。"
            "责任视图把图表判断转成可检查动作：每个动作绑定对象、成功指标和下一检查点。"
        ),
        "",
        _markdown_table(owner_rows, ["owner_role", "day_label", "theme", "object_name", "this_day_action", "success_metric", "next_checkpoint"], limit=16),
        "",
        _render_table_reading_card(table_cards, "owner_schedule"),
        "",
        "## 9. 30/60/90 管理层决策：本周动作进入投放控制节奏",
        "",
        (
            "**30 天**：把 Day 1-D7 的止损、预算迁移和承接实验固化为每周运营例会模板，重点看边际 roi、边际 CAC、CTR、点击到注册率、激活到付费率。"
            "**60 天**：把渠道 × 流量来源扩展到人群、城市、内容和产品模块联动，避免只在渠道层优化。"
            "**90 天**：建立增量验证或 holdout 机制，区分自然转化和投放带来的真实增量，防止高 roi 组合被归因窗口误判。"
        ),
    ]
    return _strip_contract_label_text("\n".join(part for part in sections if part is not None).strip()) + "\n"


def _split_markdown_cells(line: str) -> list[str]:
    text = line.rstrip("\n").strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def _render_inline(text: str) -> str:
    rendered = html.escape(text)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    return rendered


def render_management_brief_html(markdown_text: str, *, css_name: str = "06_report.css") -> str:
    lines = markdown_text.splitlines()
    body: list[str] = []
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if not stripped:
            idx += 1
            continue
        if stripped.startswith("|"):
            block: list[str] = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                block.append(lines[idx])
                idx += 1
            if len(block) >= 2:
                headers = _split_markdown_cells(block[0])
                rows = [_split_markdown_cells(row) for row in block[2:]]
                table_class = "report-table-block report-table-block--wide" if len(headers) > 6 else "report-table-block"
                body.append(f'<div class="{table_class}"><div class="table-scroll"><table>')
                body.append("<thead><tr>" + "".join(f"<th>{_render_inline(cell)}</th>" for cell in headers) + "</tr></thead><tbody>")
                for row in rows:
                    padded = row[: len(headers)] + [""] * max(0, len(headers) - len(row))
                    body.append("<tr>" + "".join(f"<td>{_render_inline(cell)}</td>" for cell in padded) + "</tr>")
                body.append("</tbody></table></div></div>")
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            body.append(f"<h{level}>{_render_inline(heading.group(2))}</h{level}>")
            idx += 1
            continue
        if stripped.startswith("- "):
            items: list[str] = []
            while idx < len(lines) and lines[idx].strip().startswith("- "):
                items.append(lines[idx].strip()[2:].strip())
                idx += 1
            body.append("<ul>" + "".join(f"<li>{_render_inline(item)}</li>" for item in items) + "</ul>")
            continue
        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image:
            body.append(
                f'<figure><img src="{html.escape(image.group(2))}" alt="{html.escape(image.group(1))}"><figcaption>{html.escape(image.group(1))}</figcaption></figure>'
            )
            idx += 1
            continue
        body.append(f"<p>{_render_inline(stripped)}</p>")
        idx += 1
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>互联网运营高密度精简管理版</title>",
            f'<link rel="stylesheet" href="{html.escape(css_name)}">',
            "</head>",
            "<body>",
            '<main class="report-shell management-brief-shell">',
            *body,
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def validate_management_brief(markdown_text: str, html_text: str = "", *, workspace: Path | None = None) -> dict[str, Any]:
    combined = markdown_text + "\n" + html_text
    required_terms = [
        "互联网运营高密度精简管理版",
        "Top12 渠道 × 流量来源 AARRR 差异图组",
        "Day 1",
        "Day 7",
        "roi",
        "cac",
        "结论",
        "加码象限：高 roi / 低 cac",
        "提效象限：高 roi / 高 cac",
        "验证象限：低 roi / 低 cac",
        "止损象限：低 roi / 高 cac",
        "预算流转",
        "小步迁入",
        "桥接实验",
        "冻结池",
        "检查点",
        "核心图表象限对象清单",
        "对象数量",
        "对象清单",
        "代表序号",
        "关键指标分布",
        "派生指标分布",
        "单客付费",
        "单客毛利",
        "成本回收倍数",
        "平均数",
        "加权平均",
        "权威 KPI 合同",
        "阈值口径",
        "边界对象",
        "预算规则",
        "触发阈值",
        "停止条件",
        "20%-30%",
        "边际 roi",
        "管理动作",
        "责任角色",
        "检查点",
        "有效点击池",
        "花钱产毛利池",
        "强承接池",
        "高质量经营池",
    ]
    missing = [term for term in required_terms if term not in combined]
    if missing:
        raise ValueError("management brief missing required terms: " + ", ".join(missing))
    image_refs = re.findall(r"source_visual_assets/ops_[A-Za-z0-9_\-]+\.png", combined)
    table_count = len(re.findall(r"^\|", markdown_text, flags=re.M))
    numeric_tokens = re.findall(r"(?<![A-Za-z])[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?", combined)
    if len(set(image_refs)) < 5:
        raise ValueError("management brief must include at least 5 core ops charts.")
    if table_count < 12:
        raise ValueError("management brief must include dense management tables.")
    if len(numeric_tokens) < 60:
        raise ValueError("management brief lacks concrete numeric evidence.")
    contract_terms = ["判断标准", "标准公式", "标准下的对象分层", "关键对象差异"]
    residue_contract = [term for term in contract_terms if term in combined]
    if residue_contract:
        raise ValueError("management brief must not render internal table-reading contract labels: " + ", ".join(residue_contract))
    long_paragraphs = [
        part
        for part in re.split(r"\n{2,}", markdown_text)
        if len(re.sub(r"\s+", "", part)) >= 180
        and len(re.findall(r"\d+(?:\.\d+)?%?", part)) >= 3
        and len(re.findall(r"(?:/|×)", part)) >= 2
    ]
    if len(long_paragraphs) < 6:
        raise ValueError("management brief must include continuous data-driven narrative paragraphs after core tables.")
    narrative_terms = ["预算流转", "漏斗", "入口", "毛利", "桥接实验", "Day 1", "责任角色"]
    narrative_hits = sum(1 for term in narrative_terms if term in combined)
    if narrative_hits < 6:
        raise ValueError("management brief narrative chain is incomplete.")
    required_index_sections = [
        "核心图表象限对象清单：ROI/CAC 四象限全量渠道 × 流量来源",
        "核心图表象限对象清单：CTR/CPC/CPM 获客效率分层",
        "核心图表象限对象清单：成本/毛利兑现分层",
        "核心图表象限对象清单：留存/NPS 用户质量分层",
        "核心图表象限对象清单：付费/收入商业承接分层",
    ]
    missing_index_sections = [term for term in required_index_sections if term not in combined]
    if missing_index_sections:
        raise ValueError("management brief missing quadrant/list index sections: " + ", ".join(missing_index_sections))
    if workspace is not None:
        payload_path = workspace / MANAGEMENT_QUADRANT_INDEX_JSON_NAME
        csv_path = workspace / MANAGEMENT_QUADRANT_INDEX_CSV_NAME
        if not payload_path.exists() or not csv_path.exists():
            raise ValueError("management brief missing ops_management_quadrant_index.json/csv contracts.")
        payload = _read_json(payload_path)
        if str(payload.get("version") or "") != "ops_management_quadrant_index_v3":
            raise ValueError("ops_management_quadrant_index.json must use v3.")
        index_rows = [row for row in list(payload.get("rows") or []) if isinstance(row, dict)]
        chart_ids = {str(row.get("chart_id") or "") for row in index_rows}
        required_chart_ids = set(MANAGEMENT_QUADRANT_CHARTS.keys())
        if not required_chart_ids.issubset(chart_ids):
            raise ValueError("ops_management_quadrant_index missing charts: " + ", ".join(sorted(required_chart_ids - chart_ids)))
        distribution_missing = [
            str(row.get("chart_id") or "") + "/" + str(row.get("band") or "")
            for row in index_rows
            if _num(row.get("object_count")) > 0
            and (
                "区间" not in str(row.get("metric_distribution_summary") or "")
                or "平均数" not in str(row.get("metric_distribution_summary") or "")
                or "加权平均" not in str(row.get("metric_distribution_summary") or "")
            )
        ]
        if distribution_missing:
            raise ValueError("ops_management_quadrant_index rows missing range/mean/weighted mean: " + ", ".join(distribution_missing[:8]))
        derived_distribution_missing = [
            str(row.get("chart_id") or "") + "/" + str(row.get("band") or "")
            for row in index_rows
            if _num(row.get("object_count")) > 0
            and (
                "区间" not in str(row.get("derived_metric_distribution_summary") or "")
                or "平均数" not in str(row.get("derived_metric_distribution_summary") or "")
                or "加权平均" not in str(row.get("derived_metric_distribution_summary") or "")
            )
        ]
        if derived_distribution_missing:
            raise ValueError("ops_management_quadrant_index rows missing derived range/mean/weighted mean: " + ", ".join(derived_distribution_missing[:8]))
        diagnosis_path = workspace / DERIVED_METRIC_DIAGNOSIS_CARDS_NAME
        if not diagnosis_path.exists():
            raise ValueError("management brief missing ops_derived_metric_diagnosis_cards.json contract.")
        diagnosis_payload = _read_json(diagnosis_path)
        if str(diagnosis_payload.get("version") or "") != "ops_derived_metric_diagnosis_cards_v1":
            raise ValueError("ops_derived_metric_diagnosis_cards.json version mismatch.")
        diagnosis_cards = [card for card in list(diagnosis_payload.get("cards") or []) if isinstance(card, dict)]
        diagnosis_chart_ids = {str(card.get("chart_id") or "") for card in diagnosis_cards}
        if not required_chart_ids.issubset(diagnosis_chart_ids):
            raise ValueError("ops_derived_metric_diagnosis_cards missing charts: " + ", ".join(sorted(required_chart_ids - diagnosis_chart_ids)))
        diagnosis_failures = []
        for card in diagnosis_cards:
            metrics = list(card.get("derived_metrics") or [])
            if len(metrics) < 2:
                diagnosis_failures.append(str(card.get("chart_id") or "") + "/derived_metrics")
            text = str(card.get("diagnosis") or "")
            if "加权平均" not in text or not any(term in text for term in ("单客", "单次点击", "注册价值", "激活价值", "回收倍数")):
                diagnosis_failures.append(str(card.get("chart_id") or "") + "/diagnosis_text")
        if diagnosis_failures:
            raise ValueError("ops_derived_metric_diagnosis_cards incomplete: " + ", ".join(diagnosis_failures[:8]))
        if "关键指标范围" in markdown_text:
            raise ValueError("management brief must use key metric distribution instead of old key metric range header.")
        weighted_prose = [
            part
            for part in re.split(r"\n{2,}", markdown_text)
            if "加权平均" in part and not part.lstrip().startswith("|")
        ]
        if len(weighted_prose) < 3:
            raise ValueError("management brief must cite weighted averages in prose, not only in tables.")
        canonical_path = workspace / CHANNEL_SOURCE_KPI_CANONICAL_JSON_NAME
        canonical_csv_path = workspace / CHANNEL_SOURCE_KPI_CANONICAL_CSV_NAME
        thresholds_path = workspace / MANAGEMENT_THRESHOLDS_JSON_NAME
        action_rules_path = workspace / EXECUTIVE_ACTION_RULES_JSON_NAME
        missing_fact_contracts = [
            path.name
            for path in [canonical_path, canonical_csv_path, thresholds_path, action_rules_path]
            if not path.exists()
        ]
        if missing_fact_contracts:
            raise ValueError("management brief missing fact/action contracts: " + ", ".join(missing_fact_contracts))
        canonical_payload = _read_json(canonical_path)
        if str(canonical_payload.get("version") or "") != "ops_channel_source_kpi_canonical_v1":
            raise ValueError("ops_channel_source_kpi_canonical.json version mismatch.")
        canonical_rows = {
            str(row.get("object_key") or ""): row
            for row in list(canonical_payload.get("records") or [])
            if isinstance(row, dict)
        }
        comparable_files = [
            "ops_ctr_cpc_cpm_efficiency.csv",
            "ops_cost_margin_share_matrix.csv",
            "ops_channel_source_aarrr_detail.csv",
            "ops_channel_source_aarrr_topn_small_multiples.csv",
        ]
        alias_map = {
            "revenue": ["收入"],
            "operating_cost": ["运营成本"],
            "contribution_margin": ["贡献毛利"],
            "paid_users": ["付费用户"],
        }
        inconsistencies: list[str] = []
        for filename in comparable_files:
            for row in _read_csv_rows(workspace / "source_visual_assets" / filename):
                record = canonical_rows.get(_channel_source_key(row))
                if not record:
                    continue
                for field in ["roi", "cac", "revenue", "operating_cost", "contribution_margin", "paid_users"]:
                    field_names = [field, *alias_map.get(field, [])]
                    for field_name in field_names:
                        if field_name not in row or not str(row.get(field_name) or "").strip():
                            continue
                        actual = _num(row.get(field_name))
                        expected = _num(record.get(field))
                        tolerance = max(0.01, abs(expected) * 0.0005)
                        if abs(actual - expected) > tolerance:
                            inconsistencies.append(
                                f"{filename}:{row.get('channel')}/{row.get('traffic_source')} {field_name}={actual} expected {expected}"
                            )
                if len(inconsistencies) >= 10:
                    break
            if len(inconsistencies) >= 10:
                break
        if inconsistencies:
            raise ValueError("channel-source KPI facts inconsistent across chart CSVs: " + "; ".join(inconsistencies[:10]))
        for record in canonical_rows.values():
            if _num(record.get("operating_cost")) <= 0:
                continue
            object_variants = [
                f"{record.get('channel')} / {record.get('traffic_source')}",
                f"{record.get('channel')} × {record.get('traffic_source')}",
            ]
            for variant in object_variants:
                if re.search(re.escape(str(variant)) + r".{0,120}运营成本\s*0(?:\.0+)?(?:[，,；;\s]|$)", combined, flags=re.S):
                    raise ValueError(f"management brief contradicts canonical operating_cost for {variant}.")
        thresholds_payload = _read_json(thresholds_path)
        if str(thresholds_payload.get("version") or "") != "ops_management_thresholds_v1":
            raise ValueError("ops_management_thresholds.json version mismatch.")
        threshold_failures: list[str] = []
        for chart in list(thresholds_payload.get("charts") or []):
            if not isinstance(chart, dict):
                continue
            summaries = [item for item in list(chart.get("metric_summaries") or []) if isinstance(item, dict)]
            if not summaries:
                threshold_failures.append(str(chart.get("chart_id") or "unknown_chart"))
                continue
            for item in summaries[:2]:
                if item.get("median") is None or item.get("mean") is None or ("weighted_mean" not in item):
                    threshold_failures.append(str(chart.get("chart_id") or "unknown_chart") + "/" + str(item.get("metric") or "metric"))
        if threshold_failures:
            raise ValueError("management threshold contract incomplete: " + ", ".join(threshold_failures[:8]))
        action_rules_payload = _read_json(action_rules_path)
        if str(action_rules_payload.get("version") or "") != "ops_executive_action_rules_v1":
            raise ValueError("ops_executive_action_rules.json version mismatch.")
        action_rule_failures: list[str] = []
        for rule in list(action_rules_payload.get("rules") or []):
            if not isinstance(rule, dict):
                continue
            for field in ["object_name", "budget_rule", "trigger_threshold", "stop_condition", "owner", "checkpoint"]:
                if not str(rule.get(field) or "").strip():
                    action_rule_failures.append(str(rule.get("rule_id") or "unknown_rule") + "/" + field)
            budget_rule_text = str(rule.get("budget_rule") or "")
            if (
                "%" not in budget_rule_text
                and "冻结" not in budget_rule_text
                and "小样本" not in budget_rule_text
                and "不因" not in budget_rule_text
                and "不新增" not in budget_rule_text
                and "降权" not in budget_rule_text
            ):
                action_rule_failures.append(str(rule.get("rule_id") or "unknown_rule") + "/budget_percentage_or_freeze")
            if not re.search(r"(<|>|低于|高于|不低于|不高于|未达标|未追上)", str(rule.get("stop_condition") or "") + str(rule.get("trigger_threshold") or "")):
                action_rule_failures.append(str(rule.get("rule_id") or "unknown_rule") + "/threshold_condition")
        if action_rule_failures:
            raise ValueError("executive action rules are not executable enough: " + ", ".join(action_rule_failures[:10]))
        roi_source = _with_roi_quadrants(_read_csv_rows(workspace / "source_visual_assets" / "ops_roi_cac_quadrant.csv"))
        roi_index_text = "；".join(
            str(row.get("object_list") or "")
            for row in index_rows
            if str(row.get("chart_id") or "") == "ops_roi_cac_quadrant"
        )
        missing_roi_objects = [
            _object_from_columns(row, ["channel", "traffic_source"])
            for row in roi_source
            if _object_from_columns(row, ["channel", "traffic_source"]) not in roi_index_text
        ]
        if missing_roi_objects:
            raise ValueError("ROI/CAC management quadrant index missing objects: " + ", ".join(missing_roi_objects[:12]))
    methodology_terms = ["说明盘子有规模", "必须和成本", "不能单独证明投放健康", "用来判断", "结论应是"]
    residue = [term for term in methodology_terms if term in combined]
    if residue:
        raise ValueError("management brief still contains methodology-tone table prose: " + ", ".join(residue))
    template_terms = ["这张表真正拉开的分层", "共同服务于同一个取舍"]
    template_residue = [term for term in template_terms if term in combined]
    if template_residue:
        raise ValueError("management brief still contains template-style repeated prose: " + ", ".join(template_residue))
    return {
        "image_count": len(set(image_refs)),
        "table_line_count": table_count,
        "numeric_token_count": len(numeric_tokens),
        "narrative_paragraph_count": len(long_paragraphs),
    }
