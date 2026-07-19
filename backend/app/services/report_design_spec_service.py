from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_LAYOUT_PRESET_ID = "chinese_finance_editorial"

REPORT_LAYOUT_PRESETS: dict[str, dict[str, Any]] = {
    "chinese_finance_editorial": {
        "name": "中文财经内参",
        "scenario": "管理层经营复盘、策略判断、质量评测和投研式深度报告。",
        "page_structure": "封面以大标题、判断导语、三枚硬数字和一条编辑判断线建立主题；正文采用主栏叙事、右侧证据边栏、轻量 exhibit 和行动表递进。",
        "table_style": "表格使用细线、等宽数字、低底纹和清楚分组；只高亮异常、责任、动作和时间点，不做厚重表头。",
        "chart_style": "图表像财经评论插图：低饱和主色、直接标注、短图注和结论句；避免仪表盘、霓虹渐变和无解释大图。",
        "appendix_style": "附录按来源、口径、底表、行动追踪和补充证据装订，保持可复核但不抢正文。",
        "aesthetic_keywords": ["中文财经", "内参", "编辑判断", "细线表格", "证据闭环", "高级克制"],
    },
    "navy_white_premium": {
        "name": "深蓝白高级商务",
        "scenario": "正式经营报告、管理层汇报。",
        "page_structure": "深蓝封面、白底正文、结论条、KPI 摘要、证据模块和行动页递进。",
        "table_style": "深蓝表头、细灰分隔、关键行用浅色底纹突出，适合经营明细表。",
        "chart_style": "图表使用用户色卡，深色主轴线配少量强调色，强调稳重和可读性。",
        "appendix_style": "附录以清晰分组表、方法说明和下载索引为主，不抢正文层级。",
        "aesthetic_keywords": ["深蓝", "白底", "高端商务", "克制", "管理层"],
    },
    "black_white_editorial": {
        "name": "黑白编辑部",
        "scenario": "投资 memo、审计报告、正式长文。",
        "page_structure": "黑白封面、长文专栏、页眉脚注、编号章节和证据脚注。",
        "table_style": "黑白线框、强标题弱装饰，数字列保持等宽和紧凑。",
        "chart_style": "低饱和灰阶图表，必要时只用一个强调色突出结论。",
        "appendix_style": "附录像编辑部档案，按证据编号和表格主题连续装订。",
        "aesthetic_keywords": ["黑白", "editorial", "长文", "正式", "克制"],
    },
    "swiss_grid_consulting": {
        "name": "瑞士网格咨询风",
        "scenario": "高密度、秩序感、咨询公司风格。",
        "page_structure": "严格十二栅格、左侧章节索引、右侧证据区和结论区对齐。",
        "table_style": "网格化表格、紧凑行高、固定数字列宽，适合多指标对比。",
        "chart_style": "图表和注释卡严格对齐栅格，避免装饰性漂浮元素。",
        "appendix_style": "附录按编号矩阵呈现，便于复核和交叉引用。",
        "aesthetic_keywords": ["瑞士网格", "咨询", "秩序", "高密度", "理性"],
    },
    "boardroom_briefing": {
        "name": "董事会简报风",
        "scenario": "结论先行、决策条、关键证据模块。",
        "page_structure": "每章先给董事会判断条，再放关键证据、风险、待决事项。",
        "table_style": "表格突出决策字段、责任人、影响程度和时间窗口。",
        "chart_style": "图表配决策含义卡，避免纯展示型图册。",
        "appendix_style": "附录只保留董事会可能追问的依据和明细。",
        "aesthetic_keywords": ["董事会", "决策", "结论先行", "严肃", "高层"],
    },
    "strategy_matrix": {
        "name": "战略矩阵风",
        "scenario": "象限、优先级、组合管理。",
        "page_structure": "以战略象限、优先级矩阵、组合路线图组织章节。",
        "table_style": "表格突出优先级、影响力、可执行性和资源投入。",
        "chart_style": "优先使用矩阵、气泡、象限、路线图和组合图。",
        "appendix_style": "附录保留各象限对象清单和评价口径。",
        "aesthetic_keywords": ["战略", "矩阵", "象限", "组合管理", "优先级"],
    },
    "financial_times_longform": {
        "name": "金融时报长文风",
        "scenario": "长文分析、表格、脚注、克制高级。",
        "page_structure": "长文叙事、窄栏脚注、关键数字边注和章节导语。",
        "table_style": "轻表格、细线、脚注丰富，强调阅读节奏。",
        "chart_style": "低饱和图表配长注释，像财经专题而不是仪表盘。",
        "appendix_style": "附录以来源、口径、底表和补充证据顺序呈现。",
        "aesthetic_keywords": ["财经长文", "脚注", "克制", "专题", "高级"],
    },
    "burgundy_premium_proposal": {
        "name": "酒红高端提案",
        "scenario": "品牌、电商、高客单、投资人材料。",
        "page_structure": "酒红章节封面、金色强调条、故事化论证和提案页。",
        "table_style": "表格用深酒红表头和浅金强调关键列。",
        "chart_style": "图表强调品牌质感，避免过多高饱和颜色。",
        "appendix_style": "附录保持精致目录和证据卡，不做粗糙数据堆叠。",
        "aesthetic_keywords": ["酒红", "金色", "高端", "品牌", "提案"],
    },
    "green_growth_war_room": {
        "name": "绿色增长作战室",
        "scenario": "增长、留存、效率改善。",
        "page_structure": "增长目标、漏斗卡、机会池、行动闭环四段式。",
        "table_style": "表格突出增长率、留存、效率、优先处理对象。",
        "chart_style": "绿色系趋势、漏斗、分群图，强调改善空间。",
        "appendix_style": "附录保留实验假设、分群明细和追踪口径。",
        "aesthetic_keywords": ["增长", "绿色", "作战室", "效率", "闭环"],
    },
    "orange_gold_retail_command": {
        "name": "橙金零售指挥台",
        "scenario": "零售、电商、商品、采销。",
        "page_structure": "商品经营总览、类目/店铺/库存/履约模块化排布。",
        "table_style": "橙金强调畅销、滞销、异常和动作列。",
        "chart_style": "适合排行、贡献、结构、气泡和对象池图。",
        "appendix_style": "附录按商品池、类目池和异常清单装订。",
        "aesthetic_keywords": ["橙金", "零售", "电商", "商品", "指挥台"],
    },
    "graphite_finance_audit": {
        "name": "石墨财务审计",
        "scenario": "财务、预算、风控、合规。",
        "page_structure": "审计摘要、差异解释、风险等级、整改清单。",
        "table_style": "石墨灰表格、强数字对齐、差异列和风险色标。",
        "chart_style": "柱线结合、瀑布图、差异图，强调口径和金额。",
        "appendix_style": "附录保留凭证、口径、异常记录和复核路径。",
        "aesthetic_keywords": ["石墨", "财务", "审计", "风控", "合规"],
    },
    "cobalt_saas_ops_console": {
        "name": "钴蓝 SaaS 运营台",
        "scenario": "互联网运营、漏斗、AARRR。",
        "page_structure": "漏斗、 cohort、用户分层、增长动作按运营台呈现。",
        "table_style": "表格突出渠道、转化、留存、付费和异常波动。",
        "chart_style": "蓝青色系漏斗、折线、热力和分群图。",
        "appendix_style": "附录保留渠道明细、用户分层和实验口径。",
        "aesthetic_keywords": ["钴蓝", "SaaS", "运营台", "漏斗", "增长"],
    },
    "minimalist_white_paper": {
        "name": "极简白皮书",
        "scenario": "研究型报告、方法型说明。",
        "page_structure": "大留白、短标题、方法说明、证据和结论逐步展开。",
        "table_style": "极简线框表格，减少底纹和装饰。",
        "chart_style": "少量关键图配充分解释，不追求图量。",
        "appendix_style": "附录像研究白皮书，清楚记录方法、数据和限制。",
        "aesthetic_keywords": ["极简", "白皮书", "研究", "留白", "清洁"],
    },
    "data_lab_monograph": {
        "name": "数据实验室专著",
        "scenario": "统计、模型、R 工作流、严肃分析。",
        "page_structure": "问题、方法、结果、解释、稳健性和附录按专著组织。",
        "table_style": "统计表保留检验值、p 值、置信区间和样本量。",
        "chart_style": "强调坐标、图例、注释和统计解释，避免装饰。",
        "appendix_style": "厚附录保留 R 产物、方法日志和统计总表。",
        "aesthetic_keywords": ["数据实验室", "统计", "模型", "专著", "严谨"],
    },
    "executive_one_page_expanded": {
        "name": "高管一页纸扩展版",
        "scenario": "结论先行、重点动作、少而重。",
        "page_structure": "首页像一页纸摘要，后续页只展开关键证据和行动。",
        "table_style": "表格只保留最关键字段，动作列突出。",
        "chart_style": "每页最多一到两个核心图，配强结论。",
        "appendix_style": "附录轻量，服务高管追问。",
        "aesthetic_keywords": ["高管", "一页纸", "重点", "简洁", "行动"],
    },
    "analyst_atlas": {
        "name": "分析师图谱",
        "scenario": "大量证据、附录、索引型报告。",
        "page_structure": "证据索引、图谱目录、主题章节和厚附录交织。",
        "table_style": "表格保留索引编号、来源、口径和引用位置。",
        "chart_style": "多图但有清晰分组和图号，避免散乱。",
        "appendix_style": "附录是核心资产，需可检索、可复核。",
        "aesthetic_keywords": ["分析师", "图谱", "索引", "证据", "附录"],
    },
    "premium_magazine_report": {
        "name": "高级杂志式报告",
        "scenario": "对外展示、商业故事、强视觉。",
        "page_structure": "大标题、图文跨页、故事化章节和视觉焦点页。",
        "table_style": "表格被设计成编辑模块，不像原始数据表。",
        "chart_style": "图表可更大、更视觉化，但必须保留数值解释。",
        "appendix_style": "附录收束为资料页，不破坏主报告美感。",
        "aesthetic_keywords": ["杂志", "展示", "商业故事", "视觉", "高级"],
    },
    "enterprise_control_tower": {
        "name": "企业控制塔",
        "scenario": "KPI、预警、动作闭环。",
        "page_structure": "控制塔首页、预警列表、KPI 模块、责任闭环。",
        "table_style": "表格突出状态灯、阈值、负责人和截止日期。",
        "chart_style": "使用看板式趋势、预警、排行和结构图。",
        "appendix_style": "附录保留每个预警的证据链和历史记录。",
        "aesthetic_keywords": ["控制塔", "KPI", "预警", "闭环", "企业"],
    },
    "category_management_manual": {
        "name": "类目管理手册",
        "scenario": "电商类目、SKU、店铺、商品池。",
        "page_structure": "类目总览、SKU 池、店铺池、动作手册和复盘口径。",
        "table_style": "表格按类目/SKU/店铺分层，强调对象和动作。",
        "chart_style": "贡献、集中度、排名、气泡和异常图优先。",
        "appendix_style": "附录保留对象池全集、派生指标和异常 case。",
        "aesthetic_keywords": ["类目", "SKU", "店铺", "商品池", "手册"],
    },
    "supply_chain_war_room": {
        "name": "供应链战情室",
        "scenario": "履约、库存、路线、异常处理。",
        "page_structure": "履约风险、路线异常、库存压力和处置队列。",
        "table_style": "表格突出路线、延迟、库存、异常等级和升级规则。",
        "chart_style": "路线图、风险矩阵、延迟分布和异常排行。",
        "appendix_style": "附录保留路线明细、异常样本和处置记录。",
        "aesthetic_keywords": ["供应链", "战情室", "履约", "库存", "路线"],
    },
    "procurement_reconciliation_review": {
        "name": "采购彩账复核",
        "scenario": "供应商、用途、付款窗口、明细审计。",
        "page_structure": "采购概览、供应商分层、账期窗口、异常复核。",
        "table_style": "表格突出供应商、用途、金额、付款和风险。",
        "chart_style": "供应商集中度、金额结构、账期趋势和异常对比。",
        "appendix_style": "附录保留账款明细、供应商清单和复核口径。",
        "aesthetic_keywords": ["采销", "对账", "供应商", "付款", "复核"],
    },
    "internet_growth_console": {
        "name": "互联网增长控制台",
        "scenario": "渠道、漏斗、留存、用户分层。",
        "page_structure": "渠道效率、漏斗断点、留存分层、增长实验。",
        "table_style": "表格突出渠道、成本、转化、留存和实验建议。",
        "chart_style": "漏斗、分群、留存曲线、渠道对比和气泡图。",
        "appendix_style": "附录保留渠道全集、实验清单和分群口径。",
        "aesthetic_keywords": ["互联网", "增长", "渠道", "漏斗", "用户分层"],
    },
    "media_buying_postmortem": {
        "name": "媒体投放复盘",
        "scenario": "预算、ROI、素材、渠道效率。",
        "page_structure": "预算流向、效率诊断、素材/渠道组合和复盘动作。",
        "table_style": "表格突出预算、转化、CPA、ROI、素材和渠道。",
        "chart_style": "预算结构、ROI 气泡、渠道对比和效率矩阵。",
        "appendix_style": "附录保留媒体明细、素材明细和口径说明。",
        "aesthetic_keywords": ["媒体投放", "复盘", "ROI", "预算", "渠道"],
    },
    "risk_committee_materials": {
        "name": "风险委员会材料",
        "scenario": "异常、合规、边界、复核路径。",
        "page_structure": "风险摘要、严重度分层、证据链、复核与处置。",
        "table_style": "表格突出风险等级、触发条件、证据和处置状态。",
        "chart_style": "异常分布、风险矩阵、趋势和责任分布图。",
        "appendix_style": "附录完整保留复核路径和原始异常清单。",
        "aesthetic_keywords": ["风险委员会", "异常", "合规", "复核", "稳健"],
    },
    "fund_ic_memo": {
        "name": "基金 IC 备忘录",
        "scenario": "投资判断、商业化、风险收益。",
        "page_structure": "投资结论、市场/产品/财务证据、风险收益和投后计划。",
        "table_style": "表格突出投资判断、证据、风险、估值和里程碑。",
        "chart_style": "市场结构、增长曲线、商业化路径和风险矩阵。",
        "appendix_style": "附录保留尽调材料、假设和敏感性分析。",
        "aesthetic_keywords": ["基金 IC", "投资", "备忘录", "商业化", "风险收益"],
    },
    "founder_strategy_notes": {
        "name": "创始人战略笔记",
        "scenario": "产品路线、商业路径、组织动作。",
        "page_structure": "战略判断、产品路线、商业路径、组织动作和节奏。",
        "table_style": "表格突出路线选择、取舍、负责人和时间点。",
        "chart_style": "路线图、优先级矩阵、增长路径和组织动作图。",
        "appendix_style": "附录保留备选路径和关键假设。",
        "aesthetic_keywords": ["创始人", "战略", "产品路线", "商业路径", "组织动作"],
    },
    "art_school_editorial_blueprint": {
        "name": "艺术学院编辑蓝图",
        "scenario": "高审美、深蓝白、留白、编辑感。",
        "page_structure": "留白封面、编辑式章节、蓝图线框和精选视觉证据。",
        "table_style": "表格更像展陈说明卡，减少密集边框，突出关键对象。",
        "chart_style": "图表像作品说明，留白充分，注释清晰，色彩克制。",
        "appendix_style": "附录保持画册式目录，不把主报告拖成数据仓库。",
        "aesthetic_keywords": ["艺术学院", "编辑蓝图", "留白", "深蓝白", "高审美"],
    },
    "gallery_whitespace": {
        "name": "画廊留白风",
        "scenario": "少图高质、对象突出、版面安静。",
        "page_structure": "大留白、单页单焦点、对象卡和极简说明。",
        "table_style": "表格只做精选对象卡和小型对比表。",
        "chart_style": "少量高质量图表，图下解释充分，不堆图。",
        "appendix_style": "附录分开装订，避免破坏画廊式主视觉。",
        "aesthetic_keywords": ["画廊", "留白", "安静", "精选", "对象突出"],
    },
    "dense_table_compendium": {
        "name": "密集表格汇编",
        "scenario": "完整版、审计长版、大量明细表。",
        "page_structure": "目录清晰、章节密集、表格为主、少量解释卡。",
        "table_style": "高密度表格、重复表头、续表编号和分页保护。",
        "chart_style": "图表作为辅助，不占用过多页数。",
        "appendix_style": "附录非常完整，适合审计和复核。",
        "aesthetic_keywords": ["密集", "表格", "汇编", "完整版", "审计"],
    },
    "premium_visual_atlas": {
        "name": "高级图册型报告",
        "scenario": "多图、多解释卡、视觉证据强。",
        "page_structure": "图册目录、视觉证据页、解释卡、数据来源索引。",
        "table_style": "表格服务图表解释，保留简洁证据矩阵。",
        "chart_style": "多图但每图都有观察、含义、动作和证据。",
        "appendix_style": "附录保留图表数据源和未入正文的视觉证据。",
        "aesthetic_keywords": ["图册", "多图", "解释卡", "视觉证据", "高级"],
    },
    "split_column_dossier": {
        "name": "左右分栏档案风",
        "scenario": "证据与判断并列，适合复核。",
        "page_structure": "左栏证据、右栏判断，形成档案式复核页面。",
        "table_style": "表格放左侧或下方，右侧写判断和动作。",
        "chart_style": "图表与旁注并列，避免读者来回翻页。",
        "appendix_style": "附录保持同样的证据/判断双栏逻辑。",
        "aesthetic_keywords": ["分栏", "档案", "证据", "判断", "复核"],
    },
    "monochrome_accent_research": {
        "name": "单色强调研究报告",
        "scenario": "克制、专业、少量强调色。",
        "page_structure": "单色系统、重点强调块、研究型章节。",
        "table_style": "黑白灰为主，只用一个强调色标识关键列。",
        "chart_style": "图表保持单色调，强调色只用于核心系列。",
        "appendix_style": "附录克制统一，不出现多余装饰。",
        "aesthetic_keywords": ["单色", "强调", "研究", "克制", "专业"],
    },
    "warm_consumer_insight": {
        "name": "暖色消费者洞察",
        "scenario": "消费、品牌、渠道、用户画像。",
        "page_structure": "用户画像、场景洞察、渠道表现、品牌动作。",
        "table_style": "表格突出人群、场景、渠道和消费行为。",
        "chart_style": "暖色系分群图、偏好图、渠道结构和行为路径。",
        "appendix_style": "附录保留用户分层和问卷/行为明细。",
        "aesthetic_keywords": ["暖色", "消费者", "品牌", "用户画像", "洞察"],
    },
    "cool_precision_operations": {
        "name": "冷色精密运营",
        "scenario": "效率、监控、自动化、严谨控制。",
        "page_structure": "监控总览、效率诊断、异常处理、自动化建议。",
        "table_style": "表格突出阈值、状态、异常、负责人和自动化机会。",
        "chart_style": "冷色系趋势、散点、热力和监控图。",
        "appendix_style": "附录保留监控规则、阈值和执行日志。",
        "aesthetic_keywords": ["冷色", "精密", "运营", "自动化", "监控"],
    },
    "frontline_action_manual": {
        "name": "一线行动手册",
        "scenario": "任务卡、负责人、检查点、30/60/90。",
        "page_structure": "角色队列、任务卡、验收指标、阻塞升级和节奏表。",
        "table_style": "表格像工单，强调对象、动作、负责人、截止时间和验收。",
        "chart_style": "图表只作为任务证据入口，不做管理层故事主角。",
        "appendix_style": "附录保留任务来源和复核清单。",
        "aesthetic_keywords": ["一线", "任务卡", "负责人", "检查点", "行动手册"],
    },
    "thick_appendix_binder": {
        "name": "厚附录装订册",
        "scenario": "统计表、源数据、方法和证据全部保留。",
        "page_structure": "主报告短，附录长，目录和索引非常清楚。",
        "table_style": "大表可拆成续表，保留字段说明和口径。",
        "chart_style": "图表配编号和来源，方便回查。",
        "appendix_style": "附录是重点，按方法、源数据、统计、证据完整装订。",
        "aesthetic_keywords": ["厚附录", "装订册", "源数据", "方法", "证据"],
    },
    "dark_cover_white_body": {
        "name": "深色封面白色正文",
        "scenario": "高级交付 PDF，封面强、正文清爽。",
        "page_structure": "强视觉深色封面、白底正文、清楚章节分隔。",
        "table_style": "正文表格保持白底清爽，关键表头呼应封面主色。",
        "chart_style": "图表以正文可读为先，用封面色作为统一线索。",
        "appendix_style": "附录回到白底，确保打印和复核友好。",
        "aesthetic_keywords": ["深色封面", "白色正文", "高级交付", "清爽", "正式"],
    },
}

LAYOUT_PRESET_ARCHETYPES: dict[str, str] = {
    "chinese_finance_editorial": "cn_editorial",
    "navy_white_premium": "executive",
    "black_white_editorial": "editorial",
    "swiss_grid_consulting": "grid",
    "boardroom_briefing": "boardroom",
    "strategy_matrix": "matrix",
    "financial_times_longform": "longform",
    "burgundy_premium_proposal": "proposal",
    "green_growth_war_room": "war_room",
    "orange_gold_retail_command": "command",
    "graphite_finance_audit": "audit",
    "cobalt_saas_ops_console": "console",
    "minimalist_white_paper": "minimal",
    "data_lab_monograph": "monograph",
    "executive_one_page_expanded": "one_page",
    "analyst_atlas": "atlas",
    "premium_magazine_report": "magazine",
    "enterprise_control_tower": "control_tower",
    "category_management_manual": "manual",
    "supply_chain_war_room": "war_room",
    "procurement_reconciliation_review": "audit",
    "internet_growth_console": "console",
    "media_buying_postmortem": "postmortem",
    "risk_committee_materials": "risk",
    "fund_ic_memo": "ic_memo",
    "founder_strategy_notes": "strategy_notes",
    "art_school_editorial_blueprint": "art_blueprint",
    "gallery_whitespace": "gallery",
    "dense_table_compendium": "table_binder",
    "premium_visual_atlas": "visual_atlas",
    "split_column_dossier": "dossier",
    "monochrome_accent_research": "monochrome",
    "warm_consumer_insight": "consumer",
    "cool_precision_operations": "precision_ops",
    "frontline_action_manual": "frontline",
    "thick_appendix_binder": "appendix_binder",
    "dark_cover_white_body": "dark_cover",
}

LAYOUT_PRESET_FIDELITY_CONTRACTS: dict[str, dict[str, Any]] = {
    "chinese_finance_editorial": {
        "similarity_target": "必须像原创中文财经内参/经营评论报告：有编辑判断、证据边栏、轻表格和明确行动出口，而不是仿报纸头版、深蓝商务模板或卡片仪表盘。",
        "typography_direction": "中文标题使用高质量宋体系或 Source Han Serif/Noto Serif SC 气质；正文使用 Noto Sans SC 或同级无衬线；数字使用 tabular-nums；标题不要粗黑堆砌，标签不要全大写英文。",
        "writing_style_contract": {
            "preset_name": "判断先行中文财经内参",
            "voice": "克制、具体、有编辑判断；面向管理层和投研读者，不写模板化总结。",
            "headline_style": "标题先给判断，再给对象或变量；避免只写“分析”“概览”“总结”。",
            "paragraph_rhythm": "每段按判断 -> 证据 -> 含义 -> 动作/边界推进，短句建立立场，长句补足证据。",
            "must_use": ["判断句", "硬数字锚点", "证据边栏语气", "行动闭环句", "必要的数据边界"],
            "must_avoid": ["空泛形容词堆砌", "日志式过程复述", "过度免责声明", "英文模板腔", "只有风险没有动作"],
            "section_openers": ["本页先给结论", "关键变化不在总量，而在结构", "需要管理层立即看的不是更多指标，而是"],
        },
        "visual_signature": ["大号中文主标题", "编辑判断导语", "三枚硬数字", "右侧证据边栏", "细线 exhibit", "低饱和图表", "行动闭环表", "来源脚注"],
        "must_have": ["封面必须有明确判断句和 3 个以内硬数字", "正文必须出现证据边栏或侧注", "关键图表必须配一句管理含义", "行动建议必须落到对象、动作、责任人或时间点", "表格必须可打印、可扫读、数字右对齐"],
        "reference_style_profile": {
            "style_origin": "原创中文财经评论与企业内参融合风格；只借鉴编辑节奏，不复刻任何外部报纸或品牌。",
            "paper_tone": "冷白或瓷白纸面，少量暖灰分隔；避免粉色新闻纸、米黄复古底和纯白 PPT 背景。",
            "layout_rhythm": "cover judgement -> hard-number strip -> narrative analysis -> evidence side rail -> exhibit/table -> action close.",
            "type_mood": "Chinese serif editorial headlines, compact sans body, tabular figures, restrained labels.",
            "chart_mood": "thin rules, direct labels, muted teal/oxblood/brass accents, one clear takeaway per chart.",
            "brand_boundary": "No external newspaper masthead, logo, trademark lockup, proprietary font, or official affiliation claim.",
        },
        "design_tokens": {
            "paper": "#f6f5ef",
            "ink": "#17191c",
            "muted_ink": "#60656b",
            "rule": "#c8c3b8",
            "accent": "#214a4f",
            "secondary_accent": "#8f2f31",
            "signal": "#b08a57",
            "cool_note": "#e7ecea",
            "warm_note": "#eee5d8",
        },
        "prohibited_brand_assets": ["Financial Times logo", "FT official masthead", "official newspaper masthead", "proprietary font files", "external trademark lockup"],
        "must_avoid": ["不要使用 FT 或任何外部报纸官方报头", "不要做成粉色新闻纸仿制", "不要大面积深蓝封面加白底卡片", "不要圆角卡片墙", "不要使用紫蓝渐变或霓虹图表", "不要让文案停留在日志摘要", "不要把行动建议藏进附录"],
    },
    "navy_white_premium": {
        "similarity_target": "必须像正式经营汇报，而不是普通深蓝皮肤。",
        "typography_direction": "稳重无衬线标题，数字和表格使用紧凑等宽感。",
        "visual_signature": ["深色封面", "白底正文", "KPI 条", "证据表", "行动清单"],
        "must_have": ["封面必须有深色标题区", "首个分析页必须有结论和 KPI 摘要", "表格必须有管理层可扫读的重点行"],
        "must_avoid": ["不要做成泛蓝色卡片墙", "不要用花哨渐变", "不要让附录抢正文层级"],
    },
    "black_white_editorial": {
        "similarity_target": "必须像正式编辑部 memo，而不是灰色仪表盘。",
        "typography_direction": "强标题、细分隔线、长文段落和脚注优先。",
        "visual_signature": ["黑白标题页", "编号 exhibit", "脚注带", "侧注", "细线表格"],
        "must_have": ["必须出现长文导语", "必须保留脚注/来源区", "图表必须克制低饱和"],
        "must_avoid": ["不要大圆角 KPI 卡片", "不要多彩商业风", "不要删除来源"],
    },
    "swiss_grid_consulting": {
        "similarity_target": "必须像瑞士网格咨询材料，元素严格对齐。",
        "typography_direction": "窄字距无衬线、小标题编号、信息密度高。",
        "visual_signature": ["12 栅格", "左侧索引栏", "矩阵单元", "细规则线", "微型 KPI"],
        "must_have": ["每页必须体现网格对齐", "矩阵页必须有编号解释", "页脚必须有规则线或索引"],
        "must_avoid": ["不要随机宽度卡片", "不要居中漂浮布局", "不要过度留白"],
    },
    "boardroom_briefing": {
        "similarity_target": "必须像董事会决策材料，而不是分析散文。",
        "typography_direction": "短标题、决策条、风险等级和建议并列。",
        "visual_signature": ["决策条", "董事会问题卡", "证据/建议双栏", "风险取舍框", "决议表"],
        "must_have": ["每个主体页必须有待决策事项", "必须有风险/取舍", "必须有决议或行动出口"],
        "must_avoid": ["不要把结论藏到段落末尾", "不要做成视觉图册", "不要缺少决策语言"],
    },
    "strategy_matrix": {
        "similarity_target": "必须像战略组合管理材料，矩阵是视觉主骨架。",
        "typography_direction": "矩阵标题、象限标签、资源动作短句。",
        "visual_signature": ["四象限", "优先级带", "气泡矩阵", "资源分配表", "Now/Next/Later"],
        "must_have": ["必须出现象限或优先级矩阵", "对象必须落入象限", "必须解释资源配置"],
        "must_avoid": ["不要只有列表没有矩阵", "不要隐藏对象清单", "不要让色块无意义"],
    },
    "financial_times_longform": {
        "similarity_target": "高度贴近 Financial Times 纸媒头版网格：salmon/pink 新闻纸、超大 serif masthead、顶部青色/酒红 promo 条、主图+巨型标题+右侧 Briefing。不得复制 FT logo、官方报头、商标或声称官方授权。",
        "typography_direction": "Financier-like 超大 serif masthead 与头条，紧凑正文多栏，Metric-like 无衬线小标签、图表和市场表。",
        "visual_signature": ["salmon 新闻纸底色", "超大 serif masthead", "青色/酒红顶部 promo 条", "主图横跨中栏", "右侧 Briefing 栏", "巨型头条", "红点摘要", "多栏正文", "World Markets 小表"],
        "must_have": ["页面顶部必须有接近报纸头版的超大 masthead 区，但不得写 Financial Times 官方报头", "masthead 下必须有青色和酒红 promo 横条", "首屏必须有左侧短新闻、中部大图、右侧 Briefing 的三栏骨架", "主标题必须是超大 serif 两行以上，下面有红点摘要", "正文必须是紧凑多栏新闻纸排版", "底部必须有二级新闻、World Markets 小表或广告占位"],
        "reference_style_profile": {
            "reference_artifact": "Financial Times front page, 11 May 2026, public front-page image used as structural reference only.",
            "paper_tone": "FT paper/salmon newsprint surface; avoid pure white corporate slide backgrounds.",
            "layout_rhythm": "front page newspaper grid: huge masthead, two promo bands, hero image strip, right Briefing rail, giant headline, bullet standfirst, multi-column body, bottom markets/ad modules.",
            "type_mood": "Financier-like serif headline mood with Metric-like sans labels; use available system/web-safe approximations only.",
            "chart_mood": "restrained FT-style editorial chart/table language: thin rules, claret dots, teal highlight, dense World Markets table.",
            "brand_boundary": "Do not copy Financial Times logo, official masthead, trademark, proprietary font files, or claim affiliation.",
            "composition_blueprint": ["masthead", "promo-ribbon-pair", "lead-story-left", "hero-image-center", "briefing-right-rail", "giant-headline", "red-dot-standfirst", "multi-column-copy", "secondary-story-grid", "world-markets-table", "ad-block"],
        },
        "design_tokens": {
            "paper": "#fff1e5",
            "ink": "#262a33",
            "muted_ink": "#6b625c",
            "rule": "#c9b8a4",
            "accent": "#990f3d",
            "secondary_accent": "#0d7680",
            "promo_teal": "#00a6c8",
            "promo_claret": "#b33b68",
            "newsprint_shadow": "#e6d0bb",
        },
        "prohibited_brand_assets": ["Financial Times logo", "FT official masthead", "official trademark lockup", "proprietary font files"],
        "must_avoid": ["不要使用 FT logo 或 Financial Times 官方报头", "不要写出完整 FINANCIAL TIMES masthead", "不要深色封面", "不要圆角卡片墙", "不要把图表堆成 BI 仪表盘", "不要只做单栏长文页", "不要使用高饱和商业渐变"],
    },
    "burgundy_premium_proposal": {
        "similarity_target": "必须像高端提案材料，品牌感强但不浮夸。",
        "typography_direction": "大标题、短段落、金色细线、故事化小标题。",
        "visual_signature": ["酒红封面", "金色细线", "提案声明卡", "品牌指标卡", "下一步面板"],
        "must_have": ["必须有提案式机会判断", "必须有方案页", "强调色必须少量使用"],
        "must_avoid": ["不要廉价红金大面积铺色", "不要像后台看板", "不要堆满明细表"],
    },
    "green_growth_war_room": {
        "similarity_target": "必须像增长作战室，目标、漏斗和行动闭环清楚。",
        "typography_direction": "运营短句、状态标签、实验命名。",
        "visual_signature": ["增长漏斗", "机会池", "实验卡", "动作队列", "复盘表"],
        "must_have": ["必须有增长目标和漏斗", "必须有实验/动作闭环", "必须标记负责人或检查点"],
        "must_avoid": ["不要只写趋势", "不要缺少行动出口", "不要把异常放到附录才出现"],
    },
    "orange_gold_retail_command": {
        "similarity_target": "必须像零售/电商经营指挥台，商品对象是主角。",
        "typography_direction": "强对象名、排名标签、动作短句。",
        "visual_signature": ["商品池表", "排名条", "异常卡", "气泡对象图", "行动矩阵"],
        "must_have": ["必须露出类目/SKU/店铺对象", "必须有贡献和异常", "必须有对象级动作"],
        "must_avoid": ["不要抽象 KPI 空转", "不要隐藏商品明细", "不要让表格没人话解释"],
    },
    "graphite_finance_audit": {
        "similarity_target": "必须像财务审计复核材料，证据链和金额口径优先。",
        "typography_direction": "金额右对齐、风险等级、复核路径清楚。",
        "visual_signature": ["审计范围框", "差异表", "风险标签", "复核路径", "金额卡"],
        "must_have": ["必须有口径和范围", "必须有异常/差异明细", "必须有复核路径"],
        "must_avoid": ["不要艺术化弱化风险", "不要删来源", "不要让金额列难扫读"],
    },
    "cobalt_saas_ops_console": {
        "similarity_target": "必须像 SaaS 运营控制台，漏斗和分层清楚。",
        "typography_direction": "模块化无衬线、漏斗阶段标签、实验语言。",
        "visual_signature": ["KPI 顶栏", "漏斗卡", "分群模块", "实验卡", "趋势控制台"],
        "must_have": ["必须有漏斗/渠道/分层结构", "必须有转化或留存视角", "必须有实验建议"],
        "must_avoid": ["不要写成长文白皮书", "不要只有表格", "不要隐藏渠道表现"],
    },
    "minimalist_white_paper": {
        "similarity_target": "必须像极简白皮书，安静、严肃、可读。",
        "typography_direction": "清晰标题、正文优先、少装饰。",
        "visual_signature": ["白底封面", "细线章节", "方法框", "轻量图注", "安静 callout"],
        "must_have": ["必须有方法和发现", "必须留足空白", "表格必须轻量"],
        "must_avoid": ["不要密集卡片", "不要多彩装饰", "不要牺牲阅读性"],
    },
    "data_lab_monograph": {
        "similarity_target": "必须像数据实验室专著，方法和结果都严谨。",
        "typography_direction": "章节编号、统计表题、置信度注释。",
        "visual_signature": ["方法框", "统计结果表", "模型卡", "诊断图", "稳健性说明"],
        "must_have": ["必须有方法/数据/结果结构", "统计表必须完整", "必须保留解释与边界"],
        "must_avoid": ["不要把统计表做成装饰", "不要隐藏样本/方法", "不要删除 p 值或样本量"],
    },
    "executive_one_page_expanded": {
        "similarity_target": "必须像高管一页纸扩展材料，少而重。",
        "typography_direction": "大数字、短结论、风险 chip。",
        "visual_signature": ["一页总览", "大数字", "must-do 卡", "风险 chip", "下钻页"],
        "must_have": ["首页必须有结论/数字/动作/风险", "后续页只展开一个主题", "弱指标不得抢主位"],
        "must_avoid": ["不要首页空泛", "不要后续重复首页", "不要放太多弱指标"],
    },
    "analyst_atlas": {
        "similarity_target": "必须像分析师证据图谱，大量索引可追溯。",
        "typography_direction": "索引编号、证据标签、交叉引用。",
        "visual_signature": ["证据图谱", "主题地图", "指标矩阵", "交叉引用", "附录目录"],
        "must_have": ["必须有证据索引", "必须有主题/指标交叉引用", "附录必须可导航"],
        "must_avoid": ["不要没有索引", "不要删除证据编号", "不要多图失去分组"],
    },
    "premium_magazine_report": {
        "similarity_target": "必须像高级商业杂志式报告，有视觉叙事。",
        "typography_direction": "大标题、特写导语、图文节奏。",
        "visual_signature": ["hero spread", "特写卡", "大图页", "故事图注", "视觉分隔页"],
        "must_have": ["必须有封面故事感", "必须有大图或大标题页", "每个视觉证据必须解释"],
        "must_avoid": ["不要牺牲数字解释", "不要变成普通 PPT", "不要每页都卡片墙"],
    },
    "enterprise_control_tower": {
        "similarity_target": "必须像企业控制塔，KPI、预警和闭环是主轴。",
        "typography_direction": "状态灯、阈值、责任闭环。",
        "visual_signature": ["红黄绿 KPI", "告警卡", "阈值带", "责任闭环", "监控表"],
        "must_have": ["必须有状态灯或阈值", "必须有预警和责任人", "必须有下次检查点"],
        "must_avoid": ["不要只有趋势", "不要缺阈值", "不要隐藏责任闭环"],
    },
    "category_management_manual": {
        "similarity_target": "必须像类目管理手册，类目/SKU/店铺对象明确。",
        "typography_direction": "手册步骤、对象表、指标解释。",
        "visual_signature": ["手册步骤卡", "对象任务表", "指标解释框", "复核清单", "目录标签"],
        "must_have": ["必须有对象池", "必须有类目/SKU/店铺任务", "必须有复核表"],
        "must_avoid": ["不要只有管理层摘要", "不要缺具体对象", "不要像营销画册"],
    },
    "supply_chain_war_room": {
        "similarity_target": "必须像供应链战情室，路线和异常处理优先。",
        "typography_direction": "状态短句、路线标签、升级规则。",
        "visual_signature": ["状态灯", "异常队列", "路线风险卡", "责任升级表", "战情页脚"],
        "must_have": ["必须有路线/履约/异常", "必须有处理动作", "必须有升级规则"],
        "must_avoid": ["不要只讲趋势", "不要隐藏异常", "不要杂志化柔化战情"],
    },
    "procurement_reconciliation_review": {
        "similarity_target": "必须像采购彩账复核，供应商、用途和付款窗口清楚。",
        "typography_direction": "审计标签、金额列、复核口径。",
        "visual_signature": ["供应商表", "付款窗口", "异常账项", "复核卡", "用途分布"],
        "must_have": ["必须有供应商维度", "必须有金额/用途/付款窗口", "必须有复核清单"],
        "must_avoid": ["不要删除明细", "不要弱化异常", "不要变成普通经营总结"],
    },
    "internet_growth_console": {
        "similarity_target": "必须像互联网增长控制台，渠道和用户路径明确。",
        "typography_direction": "漏斗阶段、渠道标签、用户分层。",
        "visual_signature": ["渠道卡", "漏斗图", "留存表", "分层矩阵", "实验建议"],
        "must_have": ["必须有渠道/漏斗/留存", "必须有用户分层", "必须有下一轮实验"],
        "must_avoid": ["不要忽略渠道", "不要只有 KPI", "不要缺行动建议"],
    },
    "media_buying_postmortem": {
        "similarity_target": "必须像媒体投放复盘，预算、ROI、素材清楚。",
        "typography_direction": "复盘时间线、ROI 标签、预算流。",
        "visual_signature": ["复盘时间线", "预算流", "ROI 气泡", "素材卡", "下一轮表"],
        "must_have": ["必须有预算和结果", "必须解释偏差原因", "必须有下一轮优化"],
        "must_avoid": ["不要只给结果", "不要隐藏低效渠道", "不要泛泛建议"],
    },
    "risk_committee_materials": {
        "similarity_target": "必须像风险委员会材料，风险等级和证据链优先。",
        "typography_direction": "风险矩阵、严重度带、复核路径。",
        "visual_signature": ["风险矩阵", "严重度带", "证据链", "控制动作表", "复核路径"],
        "must_have": ["必须有风险等级", "必须有证据链", "必须有处置和复核"],
        "must_avoid": ["不要弱化风险等级", "不要删除边界", "不要大留白杂志风"],
    },
    "fund_ic_memo": {
        "similarity_target": "必须像基金 IC 备忘录，投资判断和风险收益清楚。",
        "typography_direction": "投资 thesis、假设表、敏感性面板。",
        "visual_signature": ["投资结论框", "风险收益表", "假设卡", "敏感性面板", "里程碑"],
        "must_have": ["必须有投资结论", "必须有商业化和风险收益", "必须有假设或情景"],
        "must_avoid": ["不要像产品宣传册", "不要缺风险", "不要商业化空泛"],
    },
    "founder_strategy_notes": {
        "similarity_target": "必须像创始人战略笔记，路线、取舍、组织动作直接。",
        "typography_direction": "笔记式短标题、路线图、取舍表。",
        "visual_signature": ["战略笔记", "路线图", "取舍表", "组织动作卡", "假设日志"],
        "must_have": ["必须有路线和取舍", "必须有组织动作", "必须有节奏或阶段"],
        "must_avoid": ["不要太像审计报告", "不要缺取舍", "不要只做漂亮摘要"],
    },
    "art_school_editorial_blueprint": {
        "similarity_target": "必须像艺术学院编辑蓝图，高审美、留白、深蓝白。",
        "typography_direction": "编辑导语、细线、非对称网格。",
        "visual_signature": ["蓝图线", "编辑侧注", "画廊证据卡", "安静表格", "策展附录"],
        "must_have": ["必须有留白和编辑感", "必须有精选视觉证据", "必须保持克制"],
        "must_avoid": ["不要满屏表格", "不要重阴影卡片", "不要色彩喧宾夺主"],
    },
    "gallery_whitespace": {
        "similarity_target": "必须像画廊留白报告，少图高质，对象突出。",
        "typography_direction": "展签式说明、单对象标题、低密度。",
        "visual_signature": ["展签", "单焦点页", "对象底座", "安静图注", "极简索引"],
        "must_have": ["每页必须有单一焦点", "必须有展签式解释", "留白必须明显"],
        "must_avoid": ["不要多图拥挤", "不要大面积表格", "不要厚边框"],
    },
    "dense_table_compendium": {
        "similarity_target": "必须像密集表格汇编，完整、可打印、可审计。",
        "typography_direction": "小字号表头、续表标记、字段说明。",
        "visual_signature": ["续表", "表格索引", "密集图注", "重复表头", "审计注释"],
        "must_have": ["必须保留明细", "必须有目录和索引", "宽表必须拆分可读"],
        "must_avoid": ["不要横向滚动", "不要删明细", "不要把表格变图片"],
    },
    "premium_visual_atlas": {
        "similarity_target": "必须像高级图册型报告，视觉证据强且每图有解释。",
        "typography_direction": "图号、图注、解释卡、证据条。",
        "visual_signature": ["图册目录", "大图卡", "figure-notes", "图表证据条", "视觉来源地图"],
        "must_have": ["必须多图且每图解释", "必须有指标使用地图", "必须有视觉来源"],
        "must_avoid": ["不要图表无解释", "不要只放表格", "不要把图都堆到末尾"],
    },
    "split_column_dossier": {
        "similarity_target": "必须像左右分栏档案，证据与判断并列。",
        "typography_direction": "档案编号、证据栏、判断栏。",
        "visual_signature": ["证据/判断分栏", "档案编号", "对象档案卡", "复核问题", "来源带"],
        "must_have": ["必须左右分栏", "必须证据和判断并列", "必须保留来源"],
        "must_avoid": ["不要单栏长文到底", "不要证据判断分离太远", "不要隐藏来源"],
    },
    "monochrome_accent_research": {
        "similarity_target": "必须像单色强调研究报告，克制、专业、少量强调。",
        "typography_direction": "单色标题、研究表、低调 callout。",
        "visual_signature": ["单色标题", "单强调线", "安静 KPI", "研究表", "低调 callout"],
        "must_have": ["必须大部分黑白灰", "强调色只用于关键点", "表格必须清爽"],
        "must_avoid": ["不要多彩花哨", "不要渐变背景", "不要大面积彩色底"],
    },
    "warm_consumer_insight": {
        "similarity_target": "必须像暖色消费者洞察，用户、场景、渠道可感知。",
        "typography_direction": "画像卡、旅程条、洞察引语。",
        "visual_signature": ["用户画像", "旅程条", "渠道卡", "洞察引语", "分群表"],
        "must_have": ["必须有用户/场景", "必须有渠道或画像", "必须有洞察句"],
        "must_avoid": ["不要过冷审计风", "不要只有 KPI", "不要忽略场景"],
    },
    "cool_precision_operations": {
        "similarity_target": "必须像冷色精密运营材料，效率、监控、阈值清楚。",
        "typography_direction": "精密状态栏、阈值表、异常日志。",
        "visual_signature": ["精密状态栏", "阈值表", "自动化卡", "异常日志", "控制闭环"],
        "must_have": ["必须有阈值和状态", "必须有异常样本", "必须有控制点"],
        "must_avoid": ["不要温暖杂志风", "不要缺阈值", "不要隐藏异常"],
    },
    "frontline_action_manual": {
        "similarity_target": "必须像一线行动手册，任务可执行而不是报告压缩版。",
        "typography_direction": "角色队列、工单卡、验收标准。",
        "visual_signature": ["角色队列", "工单卡", "验收标准", "阻塞升级", "证据入口"],
        "must_have": ["必须有负责人角色", "必须有截止时间和验收", "必须有阻塞升级"],
        "must_avoid": ["不要写成管理层报告", "不要只有复核二字", "不要缺具体对象"],
    },
    "thick_appendix_binder": {
        "similarity_target": "必须像厚附录装订册，完整证据和目录是主角。",
        "typography_direction": "附录目录、长表、方法日志、来源索引。",
        "visual_signature": ["附录目录", "装订标签", "长表", "方法日志框", "来源索引"],
        "must_have": ["必须有多级目录", "必须保留长表和方法", "必须可追溯"],
        "must_avoid": ["不要删附录", "不要无目录", "不要把长表压成图片"],
    },
    "dark_cover_white_body": {
        "similarity_target": "必须像深色封面 + 白色正文的高级交付 PDF。",
        "typography_direction": "强封面标题、正文干净、章节色块呼应。",
        "visual_signature": ["深色 hero 封面", "白底正文卡", "章节分隔", "清洁表格", "封面色强调"],
        "must_have": ["封面必须强", "正文必须白底可打印", "章节页必须呼应封面"],
        "must_avoid": ["不要全篇深色", "不要正文过暗", "不要封面正文断裂"],
    },
}

LAYOUT_ARCHETYPE_CONTRACTS: dict[str, dict[str, Any]] = {
    "cn_editorial": {
        "visual_density": "中高密度，首页像内参封面，正文保持清楚阅读节奏。",
        "cover_treatment": "冷白纸面、中文大标题、判断导语、三枚硬数字和一条细线版头；避免复古新闻纸和厚重色块。",
        "page_grid": "A4 使用主栏 + 右侧证据边栏；关键 exhibit 横跨主栏，行动表全宽收束。",
        "page_sequence_template": ["封面判断", "核心摘要", "证据边栏", "深度分析", "关键 exhibit", "行动闭环", "来源附录"],
        "component_grammar": ["cn-editorial-masthead", "judgement-deck", "hard-number-strip", "evidence-rail", "thin-rule-exhibit", "action-closure-table", "source-footnote"],
        "forbidden_layout_patterns": ["不要仿外部报纸头版", "不要做仪表盘卡片墙", "不要使用厚重阴影", "不要让字体层级失控", "不要让表格像后台截图"],
    },
    "executive": {
        "visual_density": "中高密度，首页信息密集，正文留足呼吸感。",
        "cover_treatment": "深色横幅封面，标题下放 3 个关键结论胶囊和一条决策副标题。",
        "page_grid": "A4 单栏正文 + 双栏证据区；KPI 卡片按 3 列网格排布。",
        "page_sequence_template": ["封面", "结论先行页", "KPI 总览", "核心诊断", "证据图表页", "行动计划", "附录"],
        "component_grammar": ["executive-thesis-bar", "kpi-strip", "decision-card", "evidence-grid", "owner-action-table"],
        "forbidden_layout_patterns": ["不要整篇只有白底卡片", "不要把所有图表堆到最后", "不要用花哨渐变压过数字"],
    },
    "editorial": {
        "visual_density": "中密度，长文优先，图表像编辑部插图。",
        "cover_treatment": "黑白大标题封面，细线分隔，保留日期、作者、版本和摘要栏。",
        "page_grid": "正文采用窄栏长文 + 右侧边注；表格全宽但低装饰。",
        "page_sequence_template": ["封面", "编辑摘要", "长文正文", "插图证据", "脚注与方法", "附录档案"],
        "component_grammar": ["editorial-deck", "pull-quote", "side-note", "numbered-exhibit", "footnote-band"],
        "forbidden_layout_patterns": ["不要使用彩色商业看板风", "不要用大圆角卡片堆叠", "不要把脚注和来源删掉"],
    },
    "grid": {
        "visual_density": "高密度，所有元素严格对齐。",
        "cover_treatment": "网格封面，左上标题、右下关键数字，保留细规则线。",
        "page_grid": "12 栅格系统；左侧 2 栅格目录索引，右侧 10 栅格内容。",
        "page_sequence_template": ["封面", "目录索引", "问题树", "矩阵诊断", "图表证据", "执行路线", "附录索引"],
        "component_grammar": ["grid-index-rail", "evidence-cell", "matrix-panel", "micro-kpi", "rule-line-footer"],
        "forbidden_layout_patterns": ["不要中心漂浮布局", "不要元素随机宽度", "不要过度留白导致咨询感变弱"],
    },
    "boardroom": {
        "visual_density": "中高密度，少装饰，多决策信号。",
        "cover_treatment": "董事会材料封面，突出议题、需决策事项和一行总判断。",
        "page_grid": "每页顶部固定决策条，正文 2 列：证据与建议并列。",
        "page_sequence_template": ["封面", "需决策事项", "董事会判断", "关键证据", "风险和取舍", "决议草案", "附录"],
        "component_grammar": ["decision-strip", "board-question-card", "evidence-vs-recommendation", "risk-tradeoff-box", "resolution-table"],
        "forbidden_layout_patterns": ["不要写成普通分析报告", "不要把决策事项藏在正文末尾", "不要过度图册化"],
    },
    "matrix": {
        "visual_density": "高密度，矩阵和象限必须成为视觉主骨架。",
        "cover_treatment": "封面展示 2x2 或优先级坐标暗纹，标题短而强。",
        "page_grid": "矩阵页使用全宽象限；解释区在右侧或下方以编号卡呈现。",
        "page_sequence_template": ["封面", "战略问题", "核心矩阵", "对象分布", "优先级路线", "资源配置", "附录清单"],
        "component_grammar": ["priority-matrix", "quadrant-map", "bubble-legend", "resource-allocation-table", "move-now-next-later"],
        "forbidden_layout_patterns": ["不要只有列表没有矩阵", "不要把象限解释拆散到多页", "不要隐藏对象清单"],
    },
    "longform": {
        "visual_density": "中密度，阅读节奏像财经专题。",
        "cover_treatment": "报纸式标题、导语、摘要和细线分隔，避免大面积色块。",
        "page_grid": "长文单栏为主，穿插窄表、边注和 exhibit。",
        "page_sequence_template": ["封面", "导语", "长文分析", "关键 exhibit", "数据表", "脚注", "附录"],
        "component_grammar": ["newspaper-lede", "inline-exhibit", "small-multiple-note", "source-footnote", "thin-rule-table"],
        "forbidden_layout_patterns": ["不要做成仪表盘", "不要让图表抢走长文节奏", "不要使用厚重阴影"],
    },
    "proposal": {
        "visual_density": "中密度，视觉有仪式感。",
        "cover_treatment": "酒红或深色封面，大留白，金色细线强调。",
        "page_grid": "提案页使用大标题、双栏商业叙事和精选证据卡。",
        "page_sequence_template": ["封面", "机会判断", "商业故事", "证据页", "方案页", "行动路线", "附录"],
        "component_grammar": ["premium-divider", "proposal-claim-card", "brand-metric-card", "gold-accent-line", "next-step-panel"],
        "forbidden_layout_patterns": ["不要像后台看板", "不要堆满细碎表格", "不要使用廉价高饱和撞色"],
    },
    "war_room": {
        "visual_density": "高密度，像指挥室，强调状态和处置。",
        "cover_treatment": "战情室封面，状态灯、异常数量、处置优先级并列。",
        "page_grid": "状态栏 + 任务列 + 异常表；每页都要有动作出口。",
        "page_sequence_template": ["封面", "风险雷达", "异常队列", "路线/对象诊断", "处置任务", "升级规则", "附录"],
        "component_grammar": ["status-light-strip", "exception-queue", "route-risk-card", "owner-escalation-table", "war-room-footer"],
        "forbidden_layout_patterns": ["不要只讲趋势不派单", "不要把异常放到附录才出现", "不要使用过度柔和的杂志风"],
    },
    "command": {
        "visual_density": "高密度，适合商品和经营对象管理。",
        "cover_treatment": "指挥台封面，放经营对象、核心指标和本期动作入口。",
        "page_grid": "对象池卡片 + 贡献/集中度图 + 明细表三段式。",
        "page_sequence_template": ["封面", "经营总览", "对象池", "贡献结构", "异常样本", "动作清单", "附录全集"],
        "component_grammar": ["object-pool-card", "ranked-contribution-table", "bubble-object-map", "exception-case-card", "action-roadmap"],
        "forbidden_layout_patterns": ["不要只用抽象 KPI", "不要隐藏类目/SKU/店铺对象", "不要让表格没有人话解释"],
    },
    "audit": {
        "visual_density": "高密度，证据和口径优先。",
        "cover_treatment": "审计封面，列明范围、口径、金额/风险总览。",
        "page_grid": "左侧口径说明，右侧差异/异常证据；表格全宽。",
        "page_sequence_template": ["封面", "范围与口径", "差异总览", "异常明细", "复核路径", "整改清单", "附录底表"],
        "component_grammar": ["audit-scope-box", "variance-table", "risk-severity-chip", "reconciliation-grid", "traceability-footer"],
        "forbidden_layout_patterns": ["不要删除来源和口径", "不要过度艺术化", "不要弱化异常等级"],
    },
    "console": {
        "visual_density": "高密度，控制台式模块化。",
        "cover_treatment": "控制台封面，漏斗/渠道/用户分层模块预览。",
        "page_grid": "顶部 KPI 条，下面 2x2 模块网格；每个模块配图和动作。",
        "page_sequence_template": ["封面", "漏斗总览", "渠道效率", "用户分层", "留存/转化", "实验建议", "附录"],
        "component_grammar": ["console-kpi-bar", "funnel-card", "segment-module", "experiment-card", "trend-console"],
        "forbidden_layout_patterns": ["不要长文压过运营看板", "不要只有表格没有模块", "不要把渠道明细藏起来"],
    },
    "minimal": {
        "visual_density": "低到中密度，留白和可读性优先。",
        "cover_treatment": "白底封面，极简标题、短摘要和细线。",
        "page_grid": "单栏正文，少量窄图和精选表格。",
        "page_sequence_template": ["封面", "摘要", "问题", "方法", "发现", "建议", "附录"],
        "component_grammar": ["white-space-title", "thin-rule-section", "minimal-table", "quiet-callout", "method-note"],
        "forbidden_layout_patterns": ["不要密集卡片", "不要多彩装饰", "不要为了视觉牺牲阅读"],
    },
    "monograph": {
        "visual_density": "高密度，方法和结果并重。",
        "cover_treatment": "专著封面，标题、研究问题、方法索引和版本。",
        "page_grid": "章节编号清晰；结果表、图和解释按学术报告节奏展开。",
        "page_sequence_template": ["封面", "研究问题", "方法与数据", "统计结果", "解释", "稳健性", "厚附录"],
        "component_grammar": ["method-box", "stat-result-table", "confidence-note", "model-card", "appendix-cross-ref"],
        "forbidden_layout_patterns": ["不要隐藏方法口径", "不要把统计表做成装饰", "不要删除 p 值/样本量"],
    },
    "one_page": {
        "visual_density": "首页极高密度，后续低密度展开。",
        "cover_treatment": "第一页即总览，包含结论、数字、动作和风险。",
        "page_grid": "首页 3x3 关键模块；后续每页只展开一个主题。",
        "page_sequence_template": ["一页纸总览", "关键数字", "核心证据", "行动细化", "附录"],
        "component_grammar": ["one-page-dashboard", "big-number", "must-do-card", "risk-chip", "detail-drilldown"],
        "forbidden_layout_patterns": ["不要首页空泛", "不要后续页重复首页", "不要放太多弱指标"],
    },
    "atlas": {
        "visual_density": "高密度，索引和图谱优先。",
        "cover_treatment": "图谱封面，展示证据目录和主题地图。",
        "page_grid": "每章开头有索引图，正文按证据编号交叉引用。",
        "page_sequence_template": ["封面", "证据图谱", "主题章节", "指标矩阵", "图表索引", "附录全集"],
        "component_grammar": ["atlas-map", "evidence-index", "cross-reference-chip", "artifact-table", "appendix-directory"],
        "forbidden_layout_patterns": ["不要没有索引", "不要把证据编号删掉", "不要让多图失去分组"],
    },
    "magazine": {
        "visual_density": "中密度，高视觉冲击但必须可读。",
        "cover_treatment": "杂志式封面，大标题、大图/大色块和短导语。",
        "page_grid": "跨页图文、特写页、故事页和视觉焦点页交替。",
        "page_sequence_template": ["封面", "故事导语", "视觉证据", "商业判断", "对象特写", "行动页", "附录"],
        "component_grammar": ["hero-spread", "feature-card", "large-figure-page", "story-caption", "visual-breaker"],
        "forbidden_layout_patterns": ["不要牺牲数值解释", "不要每页都做成卡片墙", "不要变成普通 PPT"],
    },
    "control_tower": {
        "visual_density": "高密度，KPI 和预警优先。",
        "cover_treatment": "控制塔封面，放红黄绿状态、关键阈值和本期风险。",
        "page_grid": "状态条固定在页眉；预警、趋势、动作三列布局。",
        "page_sequence_template": ["封面", "KPI 状态", "预警详情", "趋势监控", "责任闭环", "下周检查", "附录"],
        "component_grammar": ["traffic-light-kpi", "alert-card", "threshold-band", "owner-loop", "monitoring-table"],
        "forbidden_layout_patterns": ["不要没有状态灯", "不要只给趋势不设阈值", "不要隐藏责任闭环"],
    },
    "manual": {
        "visual_density": "高密度，手册化、对象化。",
        "cover_treatment": "手册封面，列出对象类型、任务入口和使用说明。",
        "page_grid": "对象池页、任务页、复核页分开；每页有明确对象清单。",
        "page_sequence_template": ["封面", "使用说明", "对象池", "类目/SKU/店铺任务", "指标解释", "复核表", "附录全集"],
        "component_grammar": ["manual-step-card", "object-task-table", "metric-explain-box", "checklist-panel", "catalog-tab"],
        "forbidden_layout_patterns": ["不要只写管理层摘要", "不要缺具体对象", "不要把手册做成营销画册"],
    },
    "postmortem": {
        "visual_density": "中高密度，复盘路径清晰。",
        "cover_treatment": "复盘封面，预算、结果、偏差和主要原因并列。",
        "page_grid": "事实-原因-动作三段式；渠道/素材分层展示。",
        "page_sequence_template": ["封面", "预算与结果", "偏差诊断", "渠道/素材复盘", "ROI 解释", "下轮优化", "附录"],
        "component_grammar": ["postmortem-timeline", "budget-flow", "roi-bubble", "creative-card", "next-round-table"],
        "forbidden_layout_patterns": ["不要只给结果不解释原因", "不要隐藏低效渠道", "不要把动作写成泛泛建议"],
    },
    "risk": {
        "visual_density": "高密度，风险等级和复核路径优先。",
        "cover_treatment": "风险委员会封面，列出高风险事项、触发条件和处置状态。",
        "page_grid": "风险矩阵 + 证据链 + 复核路径三块固定结构。",
        "page_sequence_template": ["封面", "风险摘要", "风险矩阵", "证据链", "处置建议", "复核路径", "附录"],
        "component_grammar": ["risk-matrix", "severity-band", "evidence-chain", "control-action-table", "review-path"],
        "forbidden_layout_patterns": ["不要弱化风险等级", "不要用杂志式大留白", "不要删掉边界和复核路径"],
    },
    "ic_memo": {
        "visual_density": "中高密度，投资判断优先。",
        "cover_treatment": "IC memo 封面，投资结论、核心假设和风险收益比。",
        "page_grid": "左侧投资判断，右侧证据/风险；表格强调假设和敏感性。",
        "page_sequence_template": ["封面", "投资结论", "市场与产品", "商业化", "风险收益", "投后计划", "附录"],
        "component_grammar": ["investment-thesis-box", "risk-return-table", "assumption-card", "sensitivity-panel", "milestone-roadmap"],
        "forbidden_layout_patterns": ["不要像产品宣传册", "不要缺风险收益", "不要把商业化写得空泛"],
    },
    "strategy_notes": {
        "visual_density": "中密度，像创始人战略备忘。",
        "cover_treatment": "笔记式封面，短标题、战略问题和路线摘要。",
        "page_grid": "路线图 + 取舍表 + 组织动作，保留手记感但不草率。",
        "page_sequence_template": ["封面", "战略判断", "路线图", "取舍表", "组织动作", "节奏", "附录假设"],
        "component_grammar": ["strategy-note", "roadmap-strip", "tradeoff-table", "org-action-card", "assumption-log"],
        "forbidden_layout_patterns": ["不要太像审计报告", "不要缺取舍", "不要只做漂亮摘要"],
    },
    "art_blueprint": {
        "visual_density": "低到中密度，视觉精致，像编辑蓝图。",
        "cover_treatment": "深蓝白留白封面，细蓝图线、窄字距标题和精选引言。",
        "page_grid": "非对称编辑网格；左侧留白，右侧图文证据卡。",
        "page_sequence_template": ["留白封面", "编辑导语", "蓝图分区", "精选图表", "对象展陈", "行动页", "轻附录"],
        "component_grammar": ["blueprint-line", "editorial-aside", "gallery-evidence-card", "quiet-table", "curated-appendix"],
        "forbidden_layout_patterns": ["不要满屏表格", "不要卡片阴影过重", "不要让色彩喧宾夺主"],
    },
    "gallery": {
        "visual_density": "低密度，少而精。",
        "cover_treatment": "画廊式封面，单一焦点和大量留白。",
        "page_grid": "单页单对象或单图，说明文字像展签。",
        "page_sequence_template": ["封面", "对象展签", "精选证据", "对比页", "结论页", "附录入口"],
        "component_grammar": ["gallery-label", "single-focus-page", "object-plinth", "quiet-caption", "minimal-index"],
        "forbidden_layout_patterns": ["不要多图同页拥挤", "不要大面积表格", "不要使用厚边框"],
    },
    "table_binder": {
        "visual_density": "极高密度，表格必须可打印。",
        "cover_treatment": "装订册封面，目录、范围和表格索引。",
        "page_grid": "表格全宽，续表和分组标题固定；解释卡短而靠近表格。",
        "page_sequence_template": ["封面", "目录", "总表", "分组表", "异常表", "复核表", "附录底表"],
        "component_grammar": ["continuation-table", "table-index", "dense-caption", "repeat-header", "audit-note"],
        "forbidden_layout_patterns": ["不要横向滚动", "不要删明细", "不要把表格变成图片"],
    },
    "visual_atlas": {
        "visual_density": "中高密度，多图但强解释。",
        "cover_treatment": "图册封面，展示图号、主题和视觉证据摘要。",
        "page_grid": "每页 1-2 张主图 + 解释卡 + 证据数字，图表必须成组。",
        "page_sequence_template": ["封面", "图册目录", "主图页", "图表组合页", "指标使用地图", "行动图谱", "附录图源"],
        "component_grammar": ["figure-index", "large-visual-card", "figure-notes-panel", "chart-evidence-strip", "visual-source-map"],
        "forbidden_layout_patterns": ["不要图表无解释", "不要把图都挤在末尾", "不要只放表格不放视觉证据"],
    },
    "dossier": {
        "visual_density": "中高密度，左右证据判断并列。",
        "cover_treatment": "档案封面，编号、主题、复核状态和摘要。",
        "page_grid": "左证据、右判断；底部保留来源和下一步。",
        "page_sequence_template": ["封面", "档案索引", "证据/判断页", "对象档案", "复核问题", "结论", "附录"],
        "component_grammar": ["evidence-judgment-split", "dossier-id", "case-file-card", "review-question", "source-band"],
        "forbidden_layout_patterns": ["不要单栏长文到底", "不要证据和判断分离太远", "不要隐藏来源"],
    },
    "monochrome": {
        "visual_density": "中密度，单色克制。",
        "cover_treatment": "单色封面，标题和唯一强调色细线。",
        "page_grid": "黑白灰为主体，强调色只用于关键数字和图表主系列。",
        "page_sequence_template": ["封面", "摘要", "发现", "证据", "行动", "附录"],
        "component_grammar": ["mono-title", "single-accent-rule", "quiet-kpi", "research-table", "subtle-callout"],
        "forbidden_layout_patterns": ["不要多色花哨", "不要渐变背景", "不要大面积彩色底"],
    },
    "consumer": {
        "visual_density": "中密度，人物/场景感更强。",
        "cover_treatment": "温暖封面，突出消费场景、用户画像和洞察句。",
        "page_grid": "画像卡、渠道卡、行为路径和证据图组合。",
        "page_sequence_template": ["封面", "用户画像", "场景洞察", "渠道表现", "行为路径", "品牌动作", "附录"],
        "component_grammar": ["persona-card", "journey-strip", "channel-card", "insight-quote", "segment-table"],
        "forbidden_layout_patterns": ["不要过冷的审计风", "不要只有 KPI 没有画像", "不要忽略渠道/场景"],
    },
    "precision_ops": {
        "visual_density": "高密度，精密监控感。",
        "cover_treatment": "冷色监控封面，阈值、状态和异常摘要。",
        "page_grid": "监控条、异常列表、自动化机会和责任闭环。",
        "page_sequence_template": ["封面", "监控总览", "阈值状态", "异常处理", "自动化机会", "复核节奏", "附录"],
        "component_grammar": ["precision-status-bar", "threshold-table", "automation-card", "exception-log", "control-loop"],
        "forbidden_layout_patterns": ["不要温暖杂志风", "不要缺阈值", "不要隐藏异常样本"],
    },
    "frontline": {
        "visual_density": "高密度但任务优先，少讲故事。",
        "cover_treatment": "行动手册封面，角色、任务数量、今日优先级。",
        "page_grid": "角色队列 + 任务卡 + 验收标准，图表只作为证据入口。",
        "page_sequence_template": ["封面", "今日派单", "角色队列", "任务卡", "验收标准", "阻塞升级", "附录证据"],
        "component_grammar": ["role-queue", "workorder-card", "acceptance-criteria", "blocker-escalation", "evidence-link"],
        "forbidden_layout_patterns": ["不要写成管理层报告", "不要缺负责人和截止时间", "不要只有复核二字没有动作"],
    },
    "appendix_binder": {
        "visual_density": "极高密度，附录是主角。",
        "cover_treatment": "装订册封面，主报告摘要和完整附录索引。",
        "page_grid": "主报告短，附录多级目录、续表和交叉引用。",
        "page_sequence_template": ["封面", "主摘要", "附录目录", "统计表", "源数据表", "方法日志", "证据索引"],
        "component_grammar": ["appendix-toc", "binder-tab", "long-table", "method-log-box", "source-index"],
        "forbidden_layout_patterns": ["不要删附录", "不要让附录无目录", "不要把长表压成图片"],
    },
    "dark_cover": {
        "visual_density": "中密度，封面强、正文干净。",
        "cover_treatment": "深色强封面，白色正文保持清爽，章节页呼应封面。",
        "page_grid": "封面强视觉；正文使用白底单栏/双栏混排。",
        "page_sequence_template": ["深色封面", "白底摘要", "正文分析", "图表页", "行动页", "附录"],
        "component_grammar": ["dark-hero-cover", "white-body-card", "section-divider", "clean-table", "cover-color-accent"],
        "forbidden_layout_patterns": ["不要全篇深色背景", "不要正文过暗影响打印", "不要封面和正文断裂"],
    },
}

DEFAULT_CHART_PALETTES: dict[str, list[str]] = {
    "cn_editorial_ink": ["#17191c", "#214a4f", "#8f2f31", "#b08a57", "#5f737b", "#7b6d61"],
    "navy_gold_boardroom": ["#052b5f", "#0f4c81", "#f2c14e", "#2a9d8f", "#c2410c", "#94a3b8"],
    "ink_blue_slate": ["#111827", "#1d4ed8", "#38bdf8", "#0f766e", "#be123c", "#64748b"],
    "black_white_editorial": ["#111827", "#374151", "#6b7280", "#9ca3af", "#d1d5db"],
    "emerald_teal_growth": ["#064e3b", "#0f766e", "#14b8a6", "#5eead4", "#84cc16", "#64748b"],
    "amber_copper_retail": ["#7c2d12", "#b45309", "#f59e0b", "#facc15", "#15803d", "#78716c"],
    "burgundy_luxury": ["#4c0519", "#9f1239", "#d4af37", "#f8e7a2", "#166534", "#64748b"],
    "cobalt_cyan_saas": ["#1e3a8a", "#2563eb", "#06b6d4", "#10b981", "#f97316", "#64748b"],
    "graphite_mint_finance": ["#1f2937", "#475569", "#2dd4bf", "#059669", "#e11d48", "#94a3b8"],
    "terracotta_sand_consumer": ["#7c2d12", "#c65d3b", "#f4d35e", "#2a9d8f", "#bc4749", "#9a8c7a"],
    "indigo_rose_media": ["#312e81", "#4f46e5", "#f472b6", "#22c55e", "#fb7185", "#64748b"],
    "forest_lime_ops": ["#14532d", "#166534", "#84cc16", "#22c55e", "#ea580c", "#64748b"],
    "steel_violet_product": ["#334155", "#7c3aed", "#a78bfa", "#14b8a6", "#f43f5e", "#94a3b8"],
    "navy_white_premium": ["#0f2a44", "#1f6f8b", "#d8a24a", "#1f7a5b", "#b4532a", "#64748b"],
}


def _read_value(source: Any, key: str, default: Any = "") -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _first_non_empty_text(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"none", "null"}:
            return text
    return default


def normalize_hex_color(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if re.fullmatch(r"#[0-9a-fA-F]{3}", text):
        return "#" + "".join(ch * 2 for ch in text[1:]).lower()
    if HEX_COLOR_RE.fullmatch(text):
        return text.lower()
    return ""


def coerce_hex_color_list(value: Any, *, limit: int = 12) -> tuple[list[str], list[str]]:
    if isinstance(value, dict):
        raw_items = list(value.values())
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = re.findall(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", str(value or ""))

    colors: list[str] = []
    warnings: list[str] = []
    for item in raw_items:
        raw = str(item or "").strip()
        if not raw:
            continue
        normalized = normalize_hex_color(raw)
        if not normalized:
            warnings.append(f"ignored invalid chart color: {raw}")
            continue
        if normalized not in colors:
            colors.append(normalized)
        if len(colors) >= limit:
            break
    return colors, warnings


def _palette_from_preset(preset: str) -> list[str]:
    return list(DEFAULT_CHART_PALETTES.get(str(preset or "").strip()) or DEFAULT_CHART_PALETTES["cn_editorial_ink"])


def _normalize_layout_preset_id(value: Any) -> tuple[str, dict[str, Any], list[str]]:
    preset_id = str(value or "").strip() or DEFAULT_LAYOUT_PRESET_ID
    warnings: list[str] = []
    if preset_id not in REPORT_LAYOUT_PRESETS:
        warnings.append(f"unknown premium_style_preset ignored: {preset_id}")
        preset_id = DEFAULT_LAYOUT_PRESET_ID
    return preset_id, REPORT_LAYOUT_PRESETS[preset_id], warnings


def _layout_keywords_text(layout: dict[str, Any]) -> str:
    keywords = layout.get("aesthetic_keywords") or []
    if isinstance(keywords, (list, tuple)):
        return "、".join(str(item) for item in keywords if str(item).strip())
    return str(keywords or "")


def _build_layout_detail_contract(preset_id: str, layout: dict[str, Any]) -> dict[str, Any]:
    archetype = LAYOUT_PRESET_ARCHETYPES.get(preset_id, "executive")
    archetype_contract = dict(LAYOUT_ARCHETYPE_CONTRACTS.get(archetype) or LAYOUT_ARCHETYPE_CONTRACTS["executive"])
    fidelity_contract = dict(LAYOUT_PRESET_FIDELITY_CONTRACTS.get(preset_id) or {})
    component_grammar = list(archetype_contract.get("component_grammar") or [])
    page_sequence = list(archetype_contract.get("page_sequence_template") or [])
    forbidden = list(archetype_contract.get("forbidden_layout_patterns") or [])
    visual_signature = list(fidelity_contract.get("visual_signature") or [])
    must_have = list(fidelity_contract.get("must_have") or [])
    must_avoid = list(fidelity_contract.get("must_avoid") or [])
    writing_style_contract = dict(fidelity_contract.get("writing_style_contract") or {})
    return {
        "preset_id": preset_id,
        "archetype": archetype,
        "读者可见名称": layout.get("name"),
        "相似度目标": fidelity_contract.get("similarity_target") or f"必须稳定呈现“{layout.get('name')}”的视觉语法，而不是普通换色模板。",
        "字体气质": fidelity_contract.get("typography_direction") or "中文经营报告优先：标题清楚、正文紧凑、表格数字可扫读。",
        "文风预设": writing_style_contract,
        "视觉签名": visual_signature,
        "必须出现": must_have,
        "禁止误用": must_avoid,
        "参考风格画像": fidelity_contract.get("reference_style_profile") or {},
        "专属设计令牌": fidelity_contract.get("design_tokens") or {},
        "禁止品牌资产": fidelity_contract.get("prohibited_brand_assets") or [],
        "视觉密度": archetype_contract.get("visual_density"),
        "封面处理": archetype_contract.get("cover_treatment"),
        "栅格系统": archetype_contract.get("page_grid"),
        "章节节奏": layout.get("page_structure"),
        "表格页语法": layout.get("table_style"),
        "图表页语法": layout.get("chart_style"),
        "附录导航": layout.get("appendix_style"),
        "写作语气": writing_style_contract.get("voice") or "结论先行、证据具体、动作清楚。",
        "页面序列": page_sequence,
        "组件语法": component_grammar,
        "禁用版式": forbidden,
        "落地要求": [
            "至少在封面、首个分析页、表格页、图表页和附录页体现该版式差异。",
            "不要只替换颜色；必须改变页面结构、信息密度、表格组织和图表解释框架。",
            "颜色由 chart_palette_colors 决定，版式由本合同决定；两者必须协同而不是互相覆盖。",
            "必须满足 preset_fidelity_contract 的相似度目标、视觉签名、必须出现和禁止误用规则。",
        ],
        "验收规则": [
            "读者不看下拉选项，仅看 PDF 前两页，也应能判断当前采用了哪个版式家族。",
            "如果输出只是深色封面 + 白底卡片，且无法体现视觉签名，则视为版式失败。",
            "如果命中了“禁止误用”中的任一项，必须重写 HTML/CSS，而不是继续渲染 PDF。",
        ],
    }


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    normalized = normalize_hex_color(color) or "#000000"
    return int(normalized[1:3], 16), int(normalized[3:5], 16), int(normalized[5:7], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, int(channel))):02x}" for channel in rgb)


def _mix_hex(color: str, target: str, weight: float) -> str:
    left = _hex_to_rgb(color)
    right = _hex_to_rgb(target)
    weight = max(0.0, min(1.0, float(weight)))
    return _rgb_to_hex(tuple(round(left[index] * (1 - weight) + right[index] * weight) for index in range(3)))


def _relative_luminance(color: str) -> float:
    def channel(value: int) -> float:
        value = value / 255
        if value <= 0.03928:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = _hex_to_rgb(color)
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast_ratio(left: str, right: str) -> float:
    lum_left = _relative_luminance(left)
    lum_right = _relative_luminance(right)
    lighter = max(lum_left, lum_right)
    darker = min(lum_left, lum_right)
    return (lighter + 0.05) / (darker + 0.05)


def _best_text_color(background: str) -> str:
    return "#ffffff" if _contrast_ratio(background, "#ffffff") >= _contrast_ratio(background, "#111827") else "#111827"


def _distinct_chart_series(colors: list[str]) -> list[str]:
    series: list[str] = []
    for index, color in enumerate(colors[:12]):
        normalized = normalize_hex_color(color)
        if not normalized:
            continue
        if normalized in series:
            normalized = _mix_hex(normalized, "#ffffff" if index % 2 else "#000000", 0.16)
        series.append(normalized)
    return series or _palette_from_preset("cn_editorial_ink")


def build_harmonized_color_system(chart_series: list[str]) -> dict[str, Any]:
    series = _distinct_chart_series(chart_series)
    dark_sorted = sorted(series, key=_relative_luminance)
    light_sorted = sorted(series, key=_relative_luminance, reverse=True)
    primary = dark_sorted[0]
    secondary = dark_sorted[1] if len(dark_sorted) > 1 else _mix_hex(primary, "#ffffff", 0.22)
    accent_candidates = [color for color in series if color not in {primary, secondary}]
    accent = accent_candidates[0] if accent_candidates else light_sorted[0]
    table_header = primary
    return {
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "neutral": "#64748b",
        "background": "#ffffff",
        "surface": _mix_hex(light_sorted[0], "#ffffff", 0.86),
        "subtle": _mix_hex(accent, "#ffffff", 0.88),
        "table_header": table_header,
        "table_header_text": _best_text_color(table_header),
        "primary_text": _best_text_color(primary),
        "accent_text": _best_text_color(accent),
        "divider": _mix_hex(primary, "#ffffff", 0.72),
        "chart_series": series,
    }


def build_report_design_spec(
    *,
    request: Any | None = None,
    requirement_intent: dict[str, Any] | None = None,
    context_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    requirement_intent = requirement_intent or {}
    context_payload = context_payload or {}
    request_payload = _read_value(context_payload, "request", {}) or {}

    explicit_colors, warnings = coerce_hex_color_list(
        _read_value(request, "chart_palette_colors")
        or context_payload.get("chart_palette_colors")
        or request_payload.get("chart_palette_colors")
    )
    intent_colors, intent_warnings = coerce_hex_color_list(requirement_intent.get("chart_palette_colors"))
    warnings.extend(intent_warnings)

    raw_chart_palette_preset = _first_non_empty_text(
        _read_value(request, "chart_palette_preset")
        if request is not None
        else None,
        context_payload.get("chart_palette_preset"),
        request_payload.get("chart_palette_preset") if isinstance(request_payload, dict) else None,
        context_payload.get("style_preset"),
        context_payload.get("premium_style_preset"),
        requirement_intent.get("chart_palette_preset"),
    )
    chart_palette_preset = raw_chart_palette_preset or "cn_editorial_ink"
    premium_style_preset = _first_non_empty_text(
        _read_value(request, "premium_style_preset")
        if request is not None
        else None,
        context_payload.get("style_preset"),
        context_payload.get("premium_style_preset"),
        request_payload.get("premium_style_preset") if isinstance(request_payload, dict) else None,
        default=DEFAULT_LAYOUT_PRESET_ID,
    )
    layout_preset_id, layout_preset, layout_warnings = _normalize_layout_preset_id(premium_style_preset)
    warnings.extend(layout_warnings)

    if explicit_colors:
        chart_series = explicit_colors
        color_source = "frontend_chart_palette_colors"
    elif raw_chart_palette_preset:
        chart_series = _palette_from_preset(raw_chart_palette_preset)
        color_source = "frontend_chart_palette_preset"
    elif intent_colors:
        chart_series = intent_colors
        color_source = "requirement_intent_chart_palette_colors"
    else:
        chart_series = _palette_from_preset("cn_editorial_ink")
        color_source = "default_palette"

    harmonized_colors = build_harmonized_color_system(chart_series)

    visual_style = str(
        _read_value(request, "visual_style_text")
        or context_payload.get("visual_style")
        or request_payload.get("visual_style_text")
        or requirement_intent.get("visual_style")
        or ""
    ).strip()
    layout_preference = str(
        context_payload.get("layout_preference")
        or requirement_intent.get("layout_preference")
        or layout_preset.get("page_structure")
        or "A4 print-friendly, table-readable, management-report layout"
    ).strip()
    pdf_design_brief = str(
        context_payload.get("pdf_design_brief")
        or requirement_intent.get("pdf_design_brief")
        or visual_style
        or f"采用「{layout_preset.get('name')}」版式：{layout_preset.get('scenario')}颜色由前端色卡控制。"
    ).strip()
    layout_grammar = {
        "版式名称": layout_preset.get("name"),
        "适用场景": layout_preset.get("scenario"),
        "页面结构": layout_preset.get("page_structure"),
        "表格风格": layout_preset.get("table_style"),
        "图表风格": layout_preset.get("chart_style"),
        "附录风格": layout_preset.get("appendix_style"),
        "审美关键词": layout_preset.get("aesthetic_keywords"),
    }
    layout_detail_contract = _build_layout_detail_contract(layout_preset_id, layout_preset)
    preset_fidelity_contract = {
        "相似度目标": layout_detail_contract.get("相似度目标"),
        "字体气质": layout_detail_contract.get("字体气质"),
        "视觉签名": layout_detail_contract.get("视觉签名") or [],
        "文风预设": layout_detail_contract.get("文风预设") or {},
        "必须出现": layout_detail_contract.get("必须出现") or [],
        "禁止误用": layout_detail_contract.get("禁止误用") or [],
        "参考风格画像": layout_detail_contract.get("参考风格画像") or {},
        "专属设计令牌": layout_detail_contract.get("专属设计令牌") or {},
        "禁止品牌资产": layout_detail_contract.get("禁止品牌资产") or [],
        "验收规则": layout_detail_contract.get("验收规则") or [],
    }

    return {
        "version": "report_design_spec_v1",
        "style_preset": layout_preset_id,
        "premium_style_preset": layout_preset_id,
        "layout_preset_id": layout_preset_id,
        "layout_preset_name": layout_preset.get("name"),
        "layout_preset_description": layout_preset.get("scenario"),
        "layout_grammar": layout_grammar,
        "layout_detail_contract": layout_detail_contract,
        "preset_fidelity_contract": preset_fidelity_contract,
        "visual_signature": preset_fidelity_contract["视觉签名"],
        "preset_must_have": preset_fidelity_contract["必须出现"],
        "preset_must_avoid": preset_fidelity_contract["禁止误用"],
        "reference_style_profile": preset_fidelity_contract["参考风格画像"],
        "preset_design_tokens": preset_fidelity_contract["专属设计令牌"],
        "prohibited_brand_assets": preset_fidelity_contract["禁止品牌资产"],
        "preset_acceptance_checks": preset_fidelity_contract["验收规则"],
        "layout_archetype": layout_detail_contract.get("archetype"),
        "page_sequence_template": layout_detail_contract.get("页面序列"),
        "component_grammar": layout_detail_contract.get("组件语法"),
        "cover_treatment": layout_detail_contract.get("封面处理"),
        "grid_system": layout_detail_contract.get("栅格系统"),
        "visual_density": layout_detail_contract.get("视觉密度"),
        "forbidden_layout_patterns": layout_detail_contract.get("禁用版式"),
        "typography_direction": layout_detail_contract.get("字体气质"),
        "writing_style_contract": layout_detail_contract.get("文风预设") or {},
        "similarity_target": layout_detail_contract.get("相似度目标"),
        "page_composition_rules": layout_preset.get("page_structure"),
        "table_presentation_rules": layout_preset.get("table_style"),
        "chart_presentation_rules": layout_preset.get("chart_style"),
        "appendix_presentation_rules": layout_preset.get("appendix_style"),
        "aesthetic_keywords": layout_preset.get("aesthetic_keywords"),
        "版式名称": layout_preset.get("name"),
        "适用场景": layout_preset.get("scenario"),
        "页面结构": layout_preset.get("page_structure"),
        "表格风格": layout_preset.get("table_style"),
        "图表风格": layout_preset.get("chart_style"),
        "附录风格": layout_preset.get("appendix_style"),
        "审美关键词": layout_preset.get("aesthetic_keywords"),
        "详细版式合同": layout_detail_contract,
        "预设逼真度合同": preset_fidelity_contract,
        "相似度目标": layout_detail_contract.get("相似度目标"),
        "字体气质": layout_detail_contract.get("字体气质"),
        "文风预设": layout_detail_contract.get("文风预设") or {},
        "视觉签名": layout_detail_contract.get("视觉签名"),
        "必须出现": layout_detail_contract.get("必须出现"),
        "禁止误用": layout_detail_contract.get("禁止误用"),
        "参考风格画像": layout_detail_contract.get("参考风格画像"),
        "专属设计令牌": layout_detail_contract.get("专属设计令牌"),
        "禁止品牌资产": layout_detail_contract.get("禁止品牌资产"),
        "验收规则": layout_detail_contract.get("验收规则"),
        "封面处理": layout_detail_contract.get("封面处理"),
        "栅格系统": layout_detail_contract.get("栅格系统"),
        "页面序列": layout_detail_contract.get("页面序列"),
        "组件语法": layout_detail_contract.get("组件语法"),
        "禁用版式": layout_detail_contract.get("禁用版式"),
        "visual_style": visual_style,
        "color_palette": str(requirement_intent.get("color_palette") or chart_palette_preset or premium_style_preset),
        "chart_palette_preset": chart_palette_preset,
        "chart_palette_colors": chart_series[:12],
        "color_source": color_source,
        "layout_preference": layout_preference,
        "pdf_design_brief": pdf_design_brief,
        "typography_brief": str(layout_detail_contract.get("字体气质") or "中文经营报告优先：标题清楚、正文紧凑、表格数字可扫读。"),
        "writing_style_brief": str((layout_detail_contract.get("文风预设") or {}).get("voice") or "结论先行、证据具体、动作清楚。"),
        "table_style_brief": str(layout_preset.get("table_style") or "表头、边框、分组标签和重点行使用色卡主色与强调色；A4 打印不裁切。"),
        "chart_style_brief": str(layout_preset.get("chart_style") or "所有图表系列色优先使用 chart_palette_colors，按用户选择顺序分配。"),
        "print_constraints": {
            "page_size": "A4",
            "avoid_horizontal_scroll": True,
            "repeat_table_headers": True,
            "embed_chart_notes": True,
        },
        "color_harmony": {
            "mode": "auto_harmonized_from_frontend_palette",
            "ratio": {
                "primary": "60%",
                "secondary": "25%",
                "accent": "10%",
                "neutral": "5%",
            },
            "role_rules": [
                "Use primary for headings, table headers, cover blocks, and section anchors.",
                "Use secondary for chart contrast, subheads, and supporting rule lines.",
                "Use accent sparingly for highlights, callouts, selected KPI chips, and figure evidence markers.",
                "Use neutral and surface colors for dense tables, appendix areas, and separators.",
            ],
            "accessibility": {
                "table_header_contrast": round(
                    _contrast_ratio(harmonized_colors["table_header"], harmonized_colors["table_header_text"]),
                    2,
                ),
                "primary_text": harmonized_colors["primary_text"],
                "accent_text": harmonized_colors["accent_text"],
            },
        },
        "derived_colors": harmonized_colors,
        "validation_warnings": warnings,
    }


def render_report_design_spec_markdown(spec: dict[str, Any]) -> str:
    colors = ", ".join(str(item) for item in spec.get("chart_palette_colors") or [])
    derived = spec.get("derived_colors") or {}
    keywords = spec.get("审美关键词") or spec.get("aesthetic_keywords") or []
    if isinstance(keywords, (list, tuple)):
        keyword_text = "、".join(str(item) for item in keywords if str(item).strip())
    else:
        keyword_text = str(keywords or "")
    page_sequence = " → ".join(str(item) for item in spec.get("页面序列") or spec.get("page_sequence_template") or [])
    component_grammar = "、".join(str(item) for item in spec.get("组件语法") or spec.get("component_grammar") or [])
    forbidden_layouts = "；".join(str(item) for item in spec.get("禁用版式") or spec.get("forbidden_layout_patterns") or [])
    visual_signature = "、".join(str(item) for item in spec.get("视觉签名") or spec.get("visual_signature") or [])
    must_have = "；".join(str(item) for item in spec.get("必须出现") or spec.get("preset_must_have") or [])
    must_avoid = "；".join(str(item) for item in spec.get("禁止误用") or spec.get("preset_must_avoid") or [])
    acceptance_checks = "；".join(str(item) for item in spec.get("验收规则") or spec.get("preset_acceptance_checks") or [])
    reference_style = spec.get("参考风格画像") or spec.get("reference_style_profile") or {}
    design_tokens = spec.get("专属设计令牌") or spec.get("preset_design_tokens") or {}
    writing_style = spec.get("文风预设") or spec.get("writing_style_contract") or {}
    prohibited_brand_assets = "；".join(str(item) for item in spec.get("禁止品牌资产") or spec.get("prohibited_brand_assets") or [])
    reference_style_text = "；".join(f"{key}: {value}" for key, value in reference_style.items()) if isinstance(reference_style, dict) else str(reference_style or "")
    design_tokens_text = "；".join(f"{key}: {value}" for key, value in design_tokens.items()) if isinstance(design_tokens, dict) else str(design_tokens or "")
    if isinstance(writing_style, dict):
        writing_style_text = "；".join(
            f"{key}: {'、'.join(str(item) for item in value) if isinstance(value, list) else value}"
            for key, value in writing_style.items()
        )
    else:
        writing_style_text = str(writing_style or "")
    return "\n".join(
        [
            "# 报告颜色与版式规格",
            "",
            "## 中文高级 PDF 版式",
            "",
            f"- 版式名称：{spec.get('版式名称') or spec.get('layout_preset_name') or ''}",
            f"- 版式 ID：{spec.get('layout_preset_id') or spec.get('style_preset') or ''}",
            f"- 适用场景：{spec.get('适用场景') or spec.get('layout_preset_description') or ''}",
            f"- 页面结构：{spec.get('页面结构') or spec.get('page_composition_rules') or ''}",
            f"- 表格风格：{spec.get('表格风格') or spec.get('table_presentation_rules') or ''}",
            f"- 图表风格：{spec.get('图表风格') or spec.get('chart_presentation_rules') or ''}",
            f"- 附录风格：{spec.get('附录风格') or spec.get('appendix_presentation_rules') or ''}",
            f"- 审美关键词：{keyword_text}",
            f"- 视觉密度：{spec.get('visual_density') or ''}",
            f"- 封面处理：{spec.get('封面处理') or spec.get('cover_treatment') or ''}",
            f"- 栅格系统：{spec.get('栅格系统') or spec.get('grid_system') or ''}",
            f"- 页面序列：{page_sequence}",
            f"- 组件语法：{component_grammar}",
            f"- 禁用版式：{forbidden_layouts}",
            f"- 相似度目标：{spec.get('相似度目标') or spec.get('similarity_target') or ''}",
            f"- 字体气质：{spec.get('字体气质') or spec.get('typography_direction') or ''}",
            f"- 文风预设：{writing_style_text}",
            f"- 视觉签名：{visual_signature}",
            f"- 必须出现：{must_have}",
            f"- 禁止误用：{must_avoid}",
            f"- 参考风格画像：{reference_style_text}",
            f"- 专属设计令牌：{design_tokens_text}",
            f"- 禁止品牌资产：{prohibited_brand_assets}",
            f"- 验收规则：{acceptance_checks}",
            "",
            "## 前端色卡",
            "",
            f"- 色卡来源：{spec.get('color_source') or ''}",
            f"- 图表色卡：{colors}",
            f"- 主色：{derived.get('primary') or ''}",
            f"- 强调色：{derived.get('accent') or ''}",
            f"- 图表预设：{spec.get('chart_palette_preset') or ''}",
            f"- 视觉要求：{spec.get('visual_style') or ''}",
            f"- 版式要求：{spec.get('layout_preference') or ''}",
            f"- PDF 设计说明：{spec.get('pdf_design_brief') or ''}",
        ]
    ) + "\n"


def write_report_design_spec_files(
    workspace_dir: Path,
    *,
    request: Any | None = None,
    requirement_intent: dict[str, Any] | None = None,
    context_payload: dict[str, Any] | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    spec = build_report_design_spec(
        request=request,
        requirement_intent=requirement_intent,
        context_payload=context_payload,
    )
    json_path = workspace_dir / "report_design_spec.json"
    md_path = workspace_dir / "report_design_spec.md"
    json_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_report_design_spec_markdown(spec), encoding="utf-8")
    return json_path, md_path, spec
