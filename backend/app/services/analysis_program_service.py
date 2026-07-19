from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from app.models import SmartReportRequest
from app.services.codex_service import codex_classify_business_context, codex_complete_input_fields, codex_synthesize_requirement
from app.services.frontend_context_pack_service import build_frontend_context_pack


TASK_FAMILIES: dict[str, list[str]] = {
    "media_review": ["投放", "媒体", "campaign", "media", "曝光", "点击", "渠道", "触达"],
    "sales_review": ["销售", "销量", "sku", "spu", "订单", "交易", "收入", "gmv"],
    "procurement_sales_review": ["采销", "采购", "供应商", "卖家", "seller", "supplier", "库存", "补货", "周转", "履约", "售后", "差评", "复购", "gmv", "sku", "订单", "销量", "销售"],
    "foundation_review": ["基金会", "公益", "捐赠", "项目", "服务领域", "资助", "支出", "收入", "理事会", "慈善"],
    "management_accounting_review": ["财务", "会计", "管理会计", "预算", "实际", "偏差", "利润", "毛利", "净利", "资产", "负债", "现金流", "营运资本", "成本中心", "利润中心", "budget", "variance", "profit", "cash", "working capital", "procurement", "contract", "supplier", "vendor", "purchase order", "purchase card", "waiver", "spend", "payment"],
    "pricing_review": ["价格", "促销", "折扣", "price", "promotion"],
    "consumer_research": ["问卷", "survey", "消费者", "满意度", "attitude"],
    "brand_listening": ["舆情", "social", "topic", "情绪", "brand", "评论", "帖子"],
    "channel_review": ["渠道", "门店", "region", "地区", "终端", "经销"],
    "experiment_review": ["实验", "ab", "a/b", "lift", "treatment", "control", "实验组"],
    "performance_benchmark": ["压测", "性能", "benchmark", "stress", "load", "稳定性", "吞吐", "latency"],
}


OBJECT_RULES: dict[str, dict[str, Any]] = {
    "media_performance_log": {
        "tokens": ["媒体", "campaign", "点位", "曝光", "点击", "终端", "预算"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "market", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "chi_square", "pca"],
        "observation_unit": "单条投放明细 / 单个投放单元在某个时间窗口内的表现",
    },
    "sales_transaction_panel": {
        "tokens": ["销售", "订单", "门店", "sku", "spu", "销量", "收入", "价格", "渠道"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "market", "growth", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "pca", "kmeans"],
        "observation_unit": "单条交易 / 单个商品在某个时间或渠道切片下的表现",
    },
    "nonprofit_project_portfolio": {
        "tokens": ["基金会", "公益", "捐赠", "项目名称", "项目简介", "项目地点", "项目收入", "项目支出", "服务领域", "理事会", "慈善"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "market", "growth", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "pca", "kmeans"],
        "observation_unit": "单个基金会项目记录 / 单家基金会在年度下的项目与收支切片",
    },
    "internet_operations_log": {
        "tokens": ["运营", "增长", "拉新", "活跃", "留存", "转化", "渠道", "活动", "用户", "funnel", "retention", "cohort", "activation", "campaign", "event"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "growth", "predictive", "experimentation", "confidence_boundary"],
        "preferred_methods": ["correlation", "logit", "ab_test", "ttest", "mann_whitney", "chi_square", "kmeans"],
        "observation_unit": "单日渠道记录 / 单场活动记录 / 单个用户阶段在某时间切片下的运营表现",
    },
    "content_performance_table": {
        "tokens": ["内容", "标题", "作者", "发布时间", "阅读", "点赞", "评论", "收藏", "分享", "互动", "播放", "完播", "content", "title", "author", "publish", "engagement"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "growth", "confidence_boundary"],
        "preferred_methods": ["correlation", "anova", "kruskal", "pca", "kmeans"],
        "observation_unit": "单篇内容 / 单位发布时间窗口下的内容表现记录",
    },
    "crm_funnel_event_log": {
        "tokens": ["用户", "注册", "留存", "转化", "漏斗", "event", "session", "member"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "predictive", "experimentation", "confidence_boundary"],
        "preferred_methods": ["correlation", "logit", "ab_test", "ttest", "mann_whitney", "chi_square"],
        "observation_unit": "单个用户 / 单次事件 / 单个漏斗节点记录",
    },
    "survey_response_table": {
        "tokens": ["问卷", "满意度", "题目", "选项", "量表", "survey", "nps"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "semantic", "category", "segmentation", "confidence_boundary"],
        "preferred_methods": ["chi_square", "ttest", "mann_whitney", "kruskal", "kmeans", "pca"],
        "observation_unit": "单个受访者 / 单份问卷响应",
    },
    "brand_social_listening": {
        "tokens": ["帖子", "评论", "舆情", "微博", "小红书", "抖音", "topic", "sentiment"],
        "modules": ["decision_summary", "analysis_program", "quality", "semantic", "semantic_expansion", "category", "temporal", "confidence_boundary"],
        "preferred_methods": ["chi_square", "correlation", "kmeans"],
        "observation_unit": "单条帖子 / 评论 / 品牌内容样本",
    },
    "financial_budget_table": {
        "tokens": ["预算", "成本", "收入", "利润", "费用", "roi", "预算执行"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "numeric", "temporal", "predictive", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "pca", "poisson_glm"],
        "observation_unit": "单个预算科目 / 单个期间 / 单个业务单元的财务记录",
    },
    "management_accounting_statement": {
        "tokens": ["预算", "实际", "偏差", "收入", "成本", "费用", "毛利", "净利润", "现金流", "资产", "负债", "权益", "应收", "应付", "存货", "成本中心", "利润中心", "budget", "actual", "variance", "profit", "cash", "assets", "liabilities", "inventory", "receivable", "payable"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "numeric", "category", "temporal", "predictive", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "pca", "kmeans"],
        "observation_unit": "单个期间 / 单个责任中心 / 单个业务单元 / 单条财务科目记录",
    },
    "procurement_spend_register": {
        "tokens": ["procurement", "contract", "supplier", "vendor", "purchase", "payment", "spend", "waiver", "card", "transaction", "invoice", "commitment", "pipeline"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "numeric", "category", "temporal", "market", "growth", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "pca"],
        "observation_unit": "单笔采购支出 / 单个合同 / 单张采购卡交易 / 单个供应商在某期间下的支出记录",
    },
    "experiment_result_table": {
        "tokens": ["实验组", "对照组", "lift", "ab", "treatment", "control", "uplift"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "experimentation", "confidence_boundary"],
        "preferred_methods": ["ab_test", "ttest", "mann_whitney", "chi_square", "fisher_exact"],
        "observation_unit": "单个实验单元 / 单个分组样本",
    },
    "regional_time_series_performance": {
        "tokens": ["地区", "省份", "城市", "region", "time", "month", "日期", "波次"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "numeric", "category", "temporal", "growth", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "pca"],
        "observation_unit": "单个地区 / 时间切片下的表现记录",
    },
    "performance_benchmark_table": {
        "tokens": ["stress", "benchmark", "load", "压测", "性能", "吞吐", "延迟", "稳定性"],
        "modules": ["decision_summary", "analysis_program", "quality", "method_execution", "numeric", "temporal", "confidence_boundary"],
        "preferred_methods": ["correlation", "normality", "anova", "kruskal", "chi_square", "pca"],
        "observation_unit": "单条压测样本 / 单次合成性能记录",
    },
}

EXPERT_RULES: dict[str, list[dict[str, Any]]] = {
    "internet_ops_review": [
        {
            "expert": "互联网运营分析负责人",
            "focus": "优先解释新增、活跃、留存和转化到底由哪些渠道、活动和内容驱动",
            "priority_questions": ["新增主要从哪里来", "留存下降或提升出现在什么环节", "哪些动作真正带来稳定增长"],
            "evidence_preference": ["渠道/活动/内容切片", "新增与活跃指标", "留存与转化指标", "时间窗口", "异常样本"],
            "decision_outputs": ["增长动作清单", "运营复盘结论", "需要继续验证的假设"],
            "guardrails": ["不把短期波动直接写成长期增长趋势", "不把相关关系直接写成增长因果"],
        },
        {
            "expert": "内容与用户增长分析负责人",
            "focus": "优先识别内容主题、发布节奏和用户行为之间的增长承接关系",
            "priority_questions": ["哪些内容更能承接新增与互动", "哪些发布节奏更稳", "哪些高表现内容只是偶发峰值"],
            "evidence_preference": ["内容字段", "互动指标", "发布时间", "分群结构"],
            "decision_outputs": ["内容优化方向", "节奏调整建议", "重点复盘清单"],
            "guardrails": ["不把爆款样本直接写成稳定方法论", "不在缺少内容语义时强写创意策略结论"],
        },
    ],
    "foundation_review": [
        {
            "expert": "公益项目组合分析负责人",
            "focus": "项目结构、支出集中度、服务领域分布和项目组合平衡",
            "priority_questions": ["支出主要投向哪些项目与领域", "哪些基金会项目承担了主要资源", "项目组合是否过于集中"],
            "evidence_preference": ["项目支出", "项目收入", "服务领域", "基金会名称", "项目地点"],
            "decision_outputs": ["重点项目复盘清单", "领域结构优化建议", "资源集中度提示"],
            "guardrails": ["不把单年样本直接写成长期公益战略", "不把项目金额高低直接写成项目质量高低"],
        },
        {
            "expert": "基金会经营与合规分析负责人",
            "focus": "收支结构、年度支出纪律、资金使用边界和风险提示",
            "priority_questions": ["支出结构是否健康", "收入与支出是否存在明显失衡", "哪些记录值得优先排查或补字段"],
            "evidence_preference": ["本年度总支出", "项目收入", "项目支出", "年度", "理事会召开次数"],
            "decision_outputs": ["财务结构复盘", "风险排查清单", "后续补数建议"],
            "guardrails": ["不把样本内收支结构直接写成合规结论", "不在缺乏完整财务口径时下经营优劣结论"],
        },
    ],
    "management_accounting_review": [
        {
            "expert": "管理会计经营分析负责人",
            "focus": "优先判断利润质量、预算偏差、责任中心表现和结构性成本压力",
            "priority_questions": ["增长是否带来真实利润质量改善", "预算偏差来自结构问题还是执行问题", "哪些责任中心在拖累整体经营"],
            "evidence_preference": ["收入与利润指标", "预算与实际偏差", "责任中心或业务单元切片", "成本与费用结构"],
            "decision_outputs": ["经营质量复盘", "预算偏差归因", "责任中心优先级清单"],
            "guardrails": ["不把收入增长直接写成经营改善", "不在缺少利润和现金联动证据时下强结论"],
        },
        {
            "expert": "预算与绩效控制负责人",
            "focus": "优先解释预算达成、偏差额、偏差率以及滚动修正方向",
            "priority_questions": ["最大偏差发生在哪些科目或单元", "偏差是否具有连续性", "下一轮预算和预测该如何调整"],
            "evidence_preference": ["预算列", "实际列", "偏差列", "时间切片", "业务单元切片"],
            "decision_outputs": ["预算调整建议", "偏差排查清单", "滚动预测议程"],
            "guardrails": ["不把单期偏差直接写成长期失控", "不在预算口径不一致时输出强管理建议"],
        },
        {
            "expert": "资金与营运资本分析负责人",
            "focus": "优先判断应收、存货、应付、现金流和杠杆对经营韧性的影响",
            "priority_questions": ["利润是否同步转成现金", "营运资本是否在吞噬增长", "资产负债结构是否在加重压力"],
            "evidence_preference": ["经营现金流", "应收应付存货", "资产负债权益", "利润指标"],
            "decision_outputs": ["现金压力判断", "营运资本排查清单", "财务韧性预警"],
            "guardrails": ["不把利润表结论直接当成现金结论", "不在缺少资产负债口径时夸大偿债风险"],
        },
    ],
    "procurement_sales_review": [
        {
            "expert": "采销经营分析负责人",
            "focus": "优先判断商品/SKU结构、卖家协同、履约售后和经营结果是否形成闭环",
            "priority_questions": ["哪些商品值得继续主推或承接", "哪些卖家/供应商需要优先修复履约与口碑", "哪些对象该补货、调结构或收缩"],
            "evidence_preference": ["商品/SKU 切片", "卖家/供应商切片", "订单覆盖", "客户覆盖", "评价与履约指标", "时间窗口"],
            "decision_outputs": ["采销动作清单", "商品与卖家协同判断", "售后履约修复优先级"],
            "guardrails": ["不把销售额头部直接写成经营最优", "不在缺少采购成本时假装给出完整采购利润结论"],
        },
        {
            "expert": "供应链与履约协同分析负责人",
            "focus": "优先解释库存、补货、卖家履约和售后问题如何反噬商品经营结果",
            "priority_questions": ["哪些问题是履约造成的", "哪些问题是售后口碑造成的", "哪些问题已经需要调整补货和合作策略"],
            "evidence_preference": ["履约时效", "逾期率", "低分评价占比", "退货/售后信号", "订单与复购承接"],
            "decision_outputs": ["履约修复动作", "卖家分层建议", "风险对象清单"],
            "guardrails": ["不把单一低分样本写成普遍质量结论", "不把观察性履约问题直接写成供应商淘汰结论"],
        },
    ],
    "media_review": [
        {
            "expert": "媒体策略分析师",
            "focus": "规模、效率、达成、异常窗口、预算迁移",
            "priority_questions": ["预算投向是否集中在高效率单元", "哪些媒体和终端组合贡献主要结果", "哪些时间窗口需要单独复盘"],
            "evidence_preference": ["规模指标", "效率指标", "媒体 × 终端 × 时间切片", "异常窗口样本"],
            "decision_outputs": ["预算加码方向", "预算收缩方向", "异常单元排查清单"],
            "guardrails": ["不把点击直接写成效果", "不把单次异常写成长期规律"],
        },
        {
            "expert": "品牌投放复盘分析师",
            "focus": "品牌 × 媒体 × 终端切片与投放单元优先级",
            "priority_questions": ["品牌资源分布是否失衡", "头部投放单元是否承担主要结果", "哪些组合值得形成固定复盘口径"],
            "evidence_preference": ["品牌切片", "投放单元结构", "结果集中度", "头尾分化"],
            "decision_outputs": ["品牌资源拆分建议", "头部单元重点复盘清单"],
            "guardrails": ["不把样本结构直接写成市场格局"],
        },
    ],
    "sales_review": [
        {
            "expert": "经营分析师",
            "focus": "结构、趋势、份额、价格带与增长动量",
            "priority_questions": ["增长来自哪里", "结构变化是否健康", "哪些切片正在拖累整体表现"],
            "evidence_preference": ["收入与销量", "份额结构", "时间趋势", "价格带"],
            "decision_outputs": ["增长来源判断", "结构优化建议"],
            "guardrails": ["不把样本内结构直接写成行业格局"],
        },
        {
            "expert": "品类分析师",
            "focus": "头尾分化、渠道差异、商品角色与动销表现",
            "priority_questions": ["头部商品承担了多少结果", "长尾是否低效占用资源", "渠道之间的商品角色是否不同"],
            "evidence_preference": ["SKU/SPU 切片", "渠道差异", "头尾分化", "动销率"],
            "decision_outputs": ["头部加码清单", "尾部清理与优化清单"],
            "guardrails": ["不把偶发爆款写成稳定趋势"],
        },
    ],
    "consumer_research": [
        {
            "expert": "消费者研究员",
            "focus": "样本质量、分群、关键差异、态度与行为线索",
            "priority_questions": ["样本结构是否可用", "关键差异来自哪类人群", "哪些构念值得进入策略讨论"],
            "evidence_preference": ["样本质量", "题项结构", "分群结果", "差异检验"],
            "decision_outputs": ["核心人群画像", "沟通与产品输入建议"],
            "guardrails": ["不把弱样本信号写成消费者事实"],
        },
    ],
    "brand_listening": [
        {
            "expert": "品牌研究分析师",
            "focus": "主题、情绪、品牌联想与事件冲击",
            "priority_questions": ["品牌被如何讨论", "哪些主题带来正负情绪变化", "事件冲击持续了多久"],
            "evidence_preference": ["主题聚类", "情绪分布", "时间峰值", "高传播样本"],
            "decision_outputs": ["品牌联想判断", "传播主题建议"],
            "guardrails": ["不把少量文本样本写成品牌共识"],
        },
        {
            "expert": "风险监测分析师",
            "focus": "风险表达、异常峰值与负面波动来源",
            "priority_questions": ["负面峰值来自哪些主题和时间窗口", "哪些表达值得列入风险清单"],
            "evidence_preference": ["负面样本", "峰值窗口", "高扩散风险表达"],
            "decision_outputs": ["风险清单", "预警与应对建议"],
            "guardrails": ["不把观察性线索写成已确认危机"],
        },
    ],
    "experiment_review": [
        {
            "expert": "因果推断分析师",
            "focus": "实验效应、边界、放量条件与复验优先级",
            "priority_questions": ["效果是否稳定", "是否满足放量条件", "哪些风险需要复验"],
            "evidence_preference": ["组间差异", "效应量", "置信区间", "样本量"],
            "decision_outputs": ["放量建议", "复验建议", "停止建议"],
            "guardrails": ["不把弱效应写成已证实增长驱动"],
        },
    ],
    "performance_benchmark": [
        {
            "expert": "性能评估分析师",
            "focus": "稳定性、吞吐、资源边界与瓶颈归因",
            "priority_questions": ["当前稳定上限在哪里", "瓶颈出现在上传、分析还是导出", "是否需要工程级重构"],
            "evidence_preference": ["耗时", "内存", "成功率", "大样本拐点"],
            "decision_outputs": ["扩容优先级", "工程改造顺序"],
            "guardrails": ["不把压测样本写成真实市场表现"],
        },
    ],
}


ROLE_RULES: dict[str, list[str]] = {
    "spend": ["预算", "成本", "花费", "支出", "expense", "expenditure", "spend", "cost", "budget"],
    "reach": ["曝光", "展现", "impression", "reach"],
    "interaction": ["点击", "互动", "click", "engagement"],
    "conversion": ["转化", "下单", "注册", "留存", "converted", "conversion", "quantity", "qty", "销量", "销售量", "件数"],
    "revenue": ["收入", "捐赠", "资助", "funding", "donation", "gmv", "sales", "revenue", "成交额"],
    "price": ["价格", "price", "售价", "折扣"],
    "inventory": ["库存", "in stock", "存货"],
    "time": ["日期", "时间", "date", "time", "month", "year", "day"],
    "brand": ["品牌", "brand"],
    "category": ["品类", "类目", "分类", "category", "cat"],
    "product": ["商品", "商品名", "产品", "product", "item name", "product name", "description"],
    "sku": ["sku", "sku_id", "商品sku", "货号", "stockcode", "stock code"],
    "spu": ["spu", "spu_id", "商品spu"],
    "media": ["媒体", "media", "platform"],
    "channel": ["渠道", "channel", "门店", "店铺", "服务领域", "领域"],
    "device": ["终端", "device", "pad", "phone", "pc", "ott"],
    "region": ["地区", "省份", "城市", "项目地点", "地点", "location", "region", "province", "city"],
    "placement": ["点位", "版位", "广告位", "资源位", "placement", "slot", "position", "inventory_unit"],
    "audience": ["人群", "用户", "member", "customer", "customerid", "customer id", "客户", "segment"],
    "text_semantic": ["标题", "内容", "文本", "comment", "post", "message", "title", "content"],
    "experiment_group": ["实验组", "对照组", "group", "variant", "treatment", "control"],
    "entity_name": ["基金会名称", "机构名称", "主体名称", "组织名称", "company name", "entity name"],
    "entity_id": ["统一信用代码", "信用代码", "注册号", "机构代码", "registration code", "entity id"],
    "organization_type": ["基金会类型", "机构类型", "组织类型", "organization type"],
    "registry_authority": ["登记管理机关", "监管机关", "登记机关", "主管机关"],
    "governance": ["理事会", "召开次数", "治理", "board"],
}


EXPERT_SOUL_RULES: dict[str, dict[str, str]] = {
    "internet_ops_review": {
        "obsession": "增长不能只看拉新峰值，必须把新增、留存、转化连成一条链。",
        "signature_move": "会先拆渠道、活动、内容三层承接关系，再决定问题出在获客、激活还是留存。",
        "anti_pattern": "最反感把短期活动峰值写成长期增长方法论。",
        "voice": "先讲哪里在真实贡献增长，再讲哪里只是看上去热闹。",
        "proof_standard": "至少同时看到规模、效率和稳定性三类证据才愿意给强动作建议。",
    },
    "foundation_review": {
        "obsession": "公益数据先看资源投向和结构边界，再看金额大小。",
        "signature_move": "会先锁主体、领域、项目，再看集中度、节奏和异常对象。",
        "anti_pattern": "最反感把金额高低直接写成项目价值高低。",
        "voice": "先说资源投向是否清楚，再说哪些主体和项目值得优先复盘。",
        "proof_standard": "只有主体、领域和项目三层都能对上时，才会把判断抬进管理层正文。",
    },
    "management_accounting_review": {
        "obsession": "收入不是终点，利润质量、现金转换和责任归属才是管理会计真正关心的盘子。",
        "signature_move": "会先把规模、利润率、预算偏差和营运资本并排，再追责任中心。",
        "anti_pattern": "最反感把收入增长直接写成经营改善。",
        "voice": "先讲增长有没有质量，再讲偏差和资金压力来自哪里。",
        "proof_standard": "至少同时看到利润、现金或预算偏差中的两条证据线，才会下经营强判断。",
    },
    "media_review": {
        "obsession": "投放判断先看兑现和稳定性，不被单个高CTR带偏。",
        "signature_move": "会先拆媒体、终端、点位和窗口，再讨论预算迁移。",
        "anti_pattern": "最反感把显著性或高点击直接写成值得加码。",
        "voice": "先说哪些资源位真的在稳定贡献结果，再说哪些只是表面热闹。",
        "proof_standard": "只有规模、效率、兑现和稳定性同时成立，才会给放量类结论。",
    },
    "sales_review": {
        "obsession": "经营增长要拆成规模、结构、利润和动销，而不是只看收入曲线。",
        "signature_move": "会先看头部和尾部，再看渠道、价格带和时间节奏。",
        "anti_pattern": "最反感把样本内结构直接写成行业格局。",
        "voice": "先说增长来自哪里，再说结构是不是健康。",
        "proof_standard": "至少同时有结构变化和结果变化两条证据，才会上升到资源动作。",
    },
    "consumer_research": {
        "obsession": "平均值会骗人，真正的洞察通常藏在分群和异质性里。",
        "signature_move": "会先验样本质量，再拆人群差异、场景差异和态度结构。",
        "anti_pattern": "最反感把弱样本信号写成消费者共识。",
        "voice": "先说谁和谁不一样，再说这些差异对策略意味着什么。",
        "proof_standard": "只有样本质量和差异证据都站得住，才会输出强人群判断。",
    },
    "brand_listening": {
        "obsession": "声量只是表层，真正要看的是主题、情绪、主体和事件链。",
        "signature_move": "会先把事件性噪音和持续性认知拆开，再决定风险级别。",
        "anti_pattern": "最反感把短期声量或少量负面样本直接写成品牌危机。",
        "voice": "先说讨论在放大什么，再说哪些内容值得响应、哪些只该监测。",
        "proof_standard": "只有主题、情绪和时间窗口三层同时对上，才会升到风险判断。",
    },
    "experiment_review": {
        "obsession": "实验结果不是看 uplift 漂不漂亮，而是看能不能推广。",
        "signature_move": "会先对样本量、显著性、边界和复验条件做门槛判断。",
        "anti_pattern": "最反感把方向性结果直接写成已证实有效。",
        "voice": "先说这次实验能不能信，再说要不要推。",
        "proof_standard": "只有显著性、样本量和边界条件都过线，才会支持 rollout。",
    },
    "performance_benchmark": {
        "obsession": "性能不是跑过一次就算稳，真正要看边界、波动和瓶颈位置。",
        "signature_move": "会先拆导入、分析、导出三段耗时，再找资源瓶颈。",
        "anti_pattern": "最反感把压测样本直接写成真实市场表现。",
        "voice": "先说系统边界，再说工程动作顺序。",
        "proof_standard": "只有稳定性、成功率和耗时边界同时清楚，才会给工程优先级判断。",
    },
    "mixed_business_review": {
        "obsession": "先识别对象，再谈结论强弱。",
        "signature_move": "会先定义观察单位、结果变量和切片，再决定正文主线。",
        "anti_pattern": "最反感把猜测写成事实。",
        "voice": "先讲边界，再讲结论。",
        "proof_standard": "对象、口径和结果变量至少三者稳定两者以上，才会给强判断。",
    },
}


EXPERT_SOUL_OVERRIDES: dict[str, dict[str, str]] = {
    "互联网运营分析负责人": {
        "obsession": "只认真正可持续的增长，不认一日冲高。",
        "signature_move": "先抓留存和承接，再回头看拉新质量。",
    },
    "内容与用户增长分析负责人": {
        "obsession": "内容不是素材池，而是增长承接器。",
        "signature_move": "先拆主题、节奏、互动，再判断哪些内容值得复制。",
    },
    "公益项目组合分析负责人": {
        "obsession": "资源配置必须落到主体、领域和项目，不能只停在总盘子。",
    },
    "基金会经营与合规分析负责人": {
        "obsession": "金额之外，先看结构和边界。",
    },
    "管理会计经营分析负责人": {
        "obsession": "先分清规模增长和质量增长，再谈经营改善。",
    },
    "预算与绩效控制负责人": {
        "signature_move": "先拆偏差额，再拆偏差率，最后才问责任归属。",
    },
    "资金与营运资本分析负责人": {
        "obsession": "利润如果转不成现金，就不算真正稳。",
    },
    "媒体策略分析师": {
        "obsession": "预算迁移一定要建立在兑现和稳定性上。",
    },
    "品牌投放复盘分析师": {
        "signature_move": "先看头部单元和组合差异，再谈品牌资源倾斜。",
    },
}


OBJECT_FAMILY_HINTS: dict[str, str] = {
    "media_performance_log": "media_review",
    "sales_transaction_panel": "sales_review",
    "nonprofit_project_portfolio": "foundation_review",
    "internet_operations_log": "internet_ops_review",
    "content_performance_table": "internet_ops_review",
    "crm_funnel_event_log": "internet_ops_review",
    "survey_response_table": "consumer_research",
    "brand_social_listening": "brand_listening",
    "financial_budget_table": "management_accounting_review",
    "management_accounting_statement": "management_accounting_review",
    "procurement_spend_register": "management_accounting_review",
    "experiment_result_table": "experiment_review",
    "regional_time_series_performance": "sales_review",
    "performance_benchmark_table": "performance_benchmark",
}

FAMILY_STRUCTURE_PRIORS: dict[str, dict[str, tuple[int, int]]] = {
    "media_review": {"numeric": (6, 13), "categorical": (3, 7), "datetime": (1, 3), "text": (0, 3), "columns": (11, 22), "rows": (500, 200000)},
    "sales_review": {"numeric": (5, 12), "categorical": (3, 8), "datetime": (1, 3), "text": (0, 2), "columns": (10, 20), "rows": (300, 150000)},
    "procurement_sales_review": {"numeric": (6, 15), "categorical": (4, 10), "datetime": (1, 3), "text": (0, 3), "columns": (12, 30), "rows": (200, 180000)},
    "foundation_review": {"numeric": (4, 10), "categorical": (2, 6), "datetime": (1, 3), "text": (0, 2), "columns": (8, 18), "rows": (50, 50000)},
    "management_accounting_review": {"numeric": (8, 17), "categorical": (2, 6), "datetime": (1, 3), "text": (0, 2), "columns": (12, 24), "rows": (80, 80000)},
    "consumer_research": {"numeric": (2, 8), "categorical": (4, 12), "datetime": (0, 2), "text": (0, 3), "columns": (8, 25), "rows": (80, 60000)},
    "brand_listening": {"numeric": (1, 5), "categorical": (2, 6), "datetime": (1, 3), "text": (1, 4), "columns": (6, 16), "rows": (100, 120000)},
    "experiment_review": {"numeric": (3, 8), "categorical": (1, 4), "datetime": (0, 2), "text": (0, 2), "columns": (6, 16), "rows": (60, 50000)},
    "performance_benchmark": {"numeric": (5, 12), "categorical": (1, 4), "datetime": (1, 2), "text": (0, 1), "columns": (8, 18), "rows": (500, 200000)},
    "mixed_business_review": {"numeric": (4, 10), "categorical": (2, 7), "datetime": (0, 2), "text": (0, 2), "columns": (8, 20), "rows": (100, 120000)},
}

WRITER_AGENT_PRESETS: dict[str, list[dict[str, str]]] = {
    "media_review": [
        {"agent": "media_strategy_writer", "style": "4A 投放复盘", "focus": "规模、效率、兑现、异常和动作矩阵"},
        {"agent": "media_management_writer", "style": "管理层周会版", "focus": "一句话判断、风险和预算动作"},
    ],
    "internet_ops_review": [
        {"agent": "growth_ops_writer", "style": "增长复盘", "focus": "新增、活跃、留存、转化和承接链路"},
        {"agent": "content_growth_writer", "style": "内容运营复盘", "focus": "渠道、活动、内容与节奏"},
    ],
    "management_accounting_review": [
        {"agent": "management_accounting_writer", "style": "财务经营联动", "focus": "利润质量、预算偏差、营运资本"},
        {"agent": "budget_control_writer", "style": "预算执行复盘", "focus": "偏差归因、责任中心和风险"},
    ],
    "procurement_sales_review": [
        {"agent": "procurement_sales_writer", "style": "采销一体经营决策", "focus": "商品结构、供应商协同、履约售后与经营动作"},
        {"agent": "merch_supply_writer", "style": "商品经营与供给协同", "focus": "主推/承接/清理、补货周转、卖家与口碑风险"},
    ],
    "foundation_review": [
        {"agent": "foundation_portfolio_writer", "style": "公益项目复盘", "focus": "资金去向、项目结构和执行节奏"},
        {"agent": "foundation_governance_writer", "style": "基金会管理汇报", "focus": "主体、领域、风险和补数"},
    ],
    "sales_review": [
        {"agent": "sales_growth_writer", "style": "经营销售复盘", "focus": "结构、趋势、份额和增长来源"},
        {"agent": "category_writer", "style": "品类拆解", "focus": "头尾结构、价格带和渠道差异"},
    ],
    "consumer_research": [
        {"agent": "consumer_insight_writer", "style": "研究洞察版", "focus": "分群、差异和策略输入"},
    ],
    "brand_listening": [
        {"agent": "brand_risk_writer", "style": "舆情与品牌联想", "focus": "主题、情绪、事件和风险"},
    ],
    "experiment_review": [
        {"agent": "causal_experiment_writer", "style": "实验决策版", "focus": "效果边界、放量条件和复验"},
    ],
    "performance_benchmark": [
        {"agent": "benchmark_writer", "style": "性能评测版", "focus": "边界、瓶颈和工程动作"},
    ],
    "mixed_business_review": [
        {"agent": "universal_market_writer", "style": "通用业务分析", "focus": "先识别对象，再组织主线"},
    ],
}


def _soulize_expert(family: str, expert: dict[str, Any]) -> dict[str, Any]:
    soul = {
        **EXPERT_SOUL_RULES.get("mixed_business_review", {}),
        **EXPERT_SOUL_RULES.get(family, {}),
        **EXPERT_SOUL_OVERRIDES.get(str(expert.get("expert") or ""), {}),
    }
    enriched = dict(expert)
    for key, value in soul.items():
        enriched.setdefault(key, value)
    return enriched


def _routing_normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value or "").lower())


def _routing_vocabulary() -> list[str]:
    tokens: set[str] = set()
    for items in TASK_FAMILIES.values():
        for token in items:
            normalized = _routing_normalize_text(token)
            if normalized:
                tokens.add(normalized)
    for rule in OBJECT_RULES.values():
        for token in rule.get("tokens", []):
            normalized = _routing_normalize_text(token)
            if normalized:
                tokens.add(normalized)
    return sorted(tokens)


def _routing_text_candidates(frame: pd.DataFrame) -> int:
    count = 0
    for column in frame.columns.astype(str):
        series = frame[column]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            sample = [str(item) for item in series.dropna().astype(str).head(8).tolist() if str(item).strip()]
            if any(len(item) >= 8 for item in sample):
                count += 1
    return count


def _routing_feature_vector(
    *,
    dataset_name: str,
    request_text: str,
    columns: list[str],
    row_count: int,
    column_count: int,
    numeric_count: int,
    categorical_count: int,
    datetime_count: int,
    text_count: int,
) -> np.ndarray:
    vocab = _routing_vocabulary()
    normalized = _routing_normalize_text(" ".join([dataset_name, request_text, *columns]))
    token_features = [1.0 if token in normalized else 0.0 for token in vocab]
    safe_columns = max(column_count, 1)
    structural = [
        np.log1p(max(row_count, 0)),
        float(column_count),
        float(numeric_count),
        float(categorical_count),
        float(datetime_count),
        float(text_count),
        float(numeric_count) / safe_columns,
        float(categorical_count) / safe_columns,
        float(datetime_count) / safe_columns,
        float(text_count) / safe_columns,
    ]
    return np.array([*token_features, *structural], dtype=float)


def _synthetic_route_text(rng: np.random.Generator, family: str, object_type: str) -> str:
    family_tokens = TASK_FAMILIES.get(family, [])
    object_tokens = OBJECT_RULES.get(object_type, {}).get("tokens", [])
    other_tokens = [
        token
        for other_family, tokens in TASK_FAMILIES.items()
        if other_family != family
        for token in tokens
    ]
    selected_family = rng.choice(family_tokens, size=min(len(family_tokens), int(rng.integers(2, 5))), replace=False).tolist() if family_tokens else []
    selected_object = rng.choice(object_tokens, size=min(len(object_tokens), int(rng.integers(2, 5))), replace=False).tolist() if object_tokens else []
    noise = rng.choice(other_tokens, size=min(len(other_tokens), int(rng.integers(0, 3))), replace=False).tolist() if other_tokens else []
    return " ".join([*selected_family, *selected_object, *noise, family, object_type])


@lru_cache(maxsize=1)
def _build_learned_route_router() -> dict[str, Any]:
    rng = np.random.default_rng(42)
    features: list[np.ndarray] = []
    family_labels: list[str] = []
    object_labels: list[str] = []
    for object_type, family in OBJECT_FAMILY_HINTS.items():
        priors = FAMILY_STRUCTURE_PRIORS.get(family, FAMILY_STRUCTURE_PRIORS["mixed_business_review"])
        for _ in range(220):
            column_count = int(rng.integers(priors["columns"][0], priors["columns"][1]))
            numeric_max = max(min(priors["numeric"][1], max(column_count - 2, 1)), 1)
            numeric_low = min(priors["numeric"][0], numeric_max)
            numeric_count = int(rng.integers(numeric_low, numeric_max + 1)) if numeric_max >= numeric_low else numeric_max

            remaining_after_numeric = max(column_count - numeric_count, 1)
            categorical_max = max(min(priors["categorical"][1], remaining_after_numeric), 1)
            categorical_low = min(priors["categorical"][0], categorical_max)
            categorical_count = int(rng.integers(categorical_low, categorical_max + 1)) if categorical_max >= categorical_low else categorical_max

            remaining_after_category = max(column_count - numeric_count - categorical_count, 0)
            datetime_max = max(min(priors["datetime"][1], remaining_after_category), 0)
            datetime_low = min(priors["datetime"][0], datetime_max)
            datetime_count = int(rng.integers(datetime_low, datetime_max + 1)) if datetime_max >= datetime_low and datetime_max > 0 else datetime_max

            remaining_after_datetime = max(column_count - numeric_count - categorical_count - datetime_count, 0)
            text_max = max(min(priors["text"][1], remaining_after_datetime), 0)
            text_low = min(priors["text"][0], text_max)
            text_count = int(rng.integers(text_low, text_max + 1)) if text_max >= text_low and text_max > 0 else text_max
            synthetic_columns = [
                f"col_{index}_{token}"
                for index, token in enumerate(
                    OBJECT_RULES.get(object_type, {}).get("tokens", [])[: max(3, min(8, column_count))]
                )
            ]
            feature = _routing_feature_vector(
                dataset_name=f"{family}_{object_type}_sample",
                request_text=_synthetic_route_text(rng, family, object_type),
                columns=synthetic_columns,
                row_count=int(rng.integers(priors["rows"][0], priors["rows"][1])),
                column_count=column_count,
                numeric_count=numeric_count,
                categorical_count=categorical_count,
                datetime_count=datetime_count,
                text_count=text_count,
            )
            features.append(feature)
            family_labels.append(family)
            object_labels.append(object_type)

    matrix = np.vstack(features)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    family_classes = sorted(set(family_labels))
    family_index = {label: index for index, label in enumerate(family_classes)}
    object_classes = sorted(set(object_labels))
    object_index = {label: index for index, label in enumerate(object_classes)}
    family_targets = np.array([family_index[label] for label in family_labels], dtype=int)
    object_targets = np.array([object_index[label] for label in object_labels], dtype=int)
    family_model = MLPClassifier(hidden_layer_sizes=(96, 48), max_iter=500, random_state=42, early_stopping=True)
    family_model.fit(scaled, family_targets)
    object_model = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42, early_stopping=True)
    object_model.fit(scaled, object_targets)
    return {
        "scaler": scaler,
        "family_model": family_model,
        "object_model": object_model,
        "family_classes": family_classes,
        "object_classes": object_classes,
        "training_sample_count": int(len(features)),
        "family_train_accuracy": round(float(family_model.score(scaled, family_targets)), 4),
        "object_train_accuracy": round(float(object_model.score(scaled, object_targets)), 4),
    }


def _route_confidence(probability: float) -> str:
    if probability >= 0.75:
        return "high"
    if probability >= 0.45:
        return "medium"
    return "low"


def _learned_route_hints(request: SmartReportRequest, dataset_name: str, frame: pd.DataFrame) -> dict[str, Any]:
    router = _build_learned_route_router()
    columns = frame.columns.astype(str).tolist()
    numeric_count = int(sum(pd.api.types.is_numeric_dtype(frame[column]) for column in columns))
    datetime_count = int(sum(pd.api.types.is_datetime64_any_dtype(frame[column]) for column in columns))
    categorical_count = int(max(len(columns) - numeric_count - datetime_count, 0))
    text_count = _routing_text_candidates(frame)
    request_text = " ".join(
        [
            request.user_requirement,
            request.problem_to_solve,
            request.target_audience,
            request.core_purpose,
            request.expected_result,
            request.key_constraints,
            request.business_background_name,
            request.business_background_text,
        ]
    )
    vector = _routing_feature_vector(
        dataset_name=dataset_name,
        request_text=request_text,
        columns=columns[:40],
        row_count=int(len(frame)),
        column_count=int(len(columns)),
        numeric_count=numeric_count,
        categorical_count=categorical_count,
        datetime_count=datetime_count,
        text_count=text_count,
    )
    scaled = router["scaler"].transform([vector])
    family_probabilities = router["family_model"].predict_proba(scaled)[0]
    family_classes = router["family_classes"]
    object_probabilities = router["object_model"].predict_proba(scaled)[0]
    object_classes = router["object_classes"]
    family_candidates = sorted(
        [
            {
                "family": str(label),
                "score": round(float(probability) * 10, 2),
                "confidence": _route_confidence(float(probability)),
                "why": "深度学习路由器综合字段、结构和需求文本后给出的业务家族判断。",
            }
            for label, probability in zip(family_classes, family_probabilities)
        ],
        key=lambda item: float(item["score"]),
        reverse=True,
    )[:4]
    object_candidates = sorted(
        [
            {
                "object_type": str(label),
                "score": round(float(probability) * 10, 2),
                "confidence": _route_confidence(float(probability)),
                "observation_unit": OBJECT_RULES.get(str(label), {}).get("observation_unit", "单行记录对应一个现实世界观察单位"),
                "why": "深度学习路由器综合字段、结构和需求文本后给出的对象判断。",
            }
            for label, probability in zip(object_classes, object_probabilities)
        ],
        key=lambda item: float(item["score"]),
        reverse=True,
    )[:4]
    top_family = family_candidates[0]["family"] if family_candidates else "mixed_business_review"
    return {
        "mode": "mlp_router",
        "training_sample_count": router["training_sample_count"],
        "family_train_accuracy": router["family_train_accuracy"],
        "object_train_accuracy": router["object_train_accuracy"],
        "task_family_candidates": family_candidates,
        "object_candidates": object_candidates,
        "writer_agent_candidates": WRITER_AGENT_PRESETS.get(top_family, WRITER_AGENT_PRESETS["mixed_business_review"]),
    }


def _merge_learned_route(
    task_model: dict[str, Any],
    object_candidates: list[dict[str, Any]],
    learned_route: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    merged_task_model = dict(task_model)
    merged_objects = [dict(item) for item in object_candidates]
    family_candidates = list(learned_route.get("task_family_candidates") or [])
    object_route_candidates = list(learned_route.get("object_candidates") or [])
    if family_candidates:
        top_family = family_candidates[0]
        current_top_score = float((merged_task_model.get("family_candidates") or [{}])[0].get("score", 0) or 0)
        current_confidence = _confidence_value((merged_task_model.get("family_candidates") or [{}])[0].get("confidence", "low"))
        top_confidence = _confidence_value(top_family.get("confidence", "low"))
        top_score = float(top_family.get("score", 0) or 0)
        if (
            merged_task_model.get("primary_family") == "mixed_business_review"
            or (top_confidence > current_confidence)
            or (top_score >= current_top_score + 1.0)
            or (top_confidence >= 2 and top_score >= 7.0)
        ):
            merged_task_model["primary_family"] = str(top_family.get("family") or merged_task_model.get("primary_family"))
        existing_families = {item.get("family") for item in family_candidates[:2]}
        merged_task_model["family_candidates"] = [
            *family_candidates[:2],
            *[item for item in merged_task_model.get("family_candidates", []) if item.get("family") not in existing_families][:2],
        ][:4]
    if object_route_candidates:
        by_object = {item["object_type"]: dict(item) for item in merged_objects}
        top_object_type = str(object_route_candidates[0].get("object_type") or "") if object_route_candidates else ""
        top_object_score = float(object_route_candidates[0].get("score", 0) or 0) if object_route_candidates else 0.0
        for candidate in object_route_candidates[:3]:
            object_type = str(candidate.get("object_type") or "")
            if not object_type:
                continue
            current = by_object.get(object_type)
            if not current or float(candidate.get("score", 0)) > float(current.get("score", 0)):
                by_object[object_type] = {
                    "object_type": object_type,
                    "score": round(float(candidate.get("score", 0)), 2),
                    "confidence": str(candidate.get("confidence") or "low"),
                    "observation_unit": candidate.get("observation_unit") or OBJECT_RULES.get(object_type, {}).get("observation_unit", "单行记录对应一个现实世界观察单位"),
                    "preferred_modules": OBJECT_RULES.get(object_type, {}).get("modules", ["decision_summary", "analysis_program", "quality", "confidence_boundary"]),
                    "preferred_methods": OBJECT_RULES.get(object_type, {}).get("preferred_methods", ["correlation"]),
                }
        merged_objects = sorted(
            by_object.values(),
            key=lambda item: (float(item.get("score", 0)), _confidence_value(item.get("confidence", "low"))),
            reverse=True,
        )[:4]
        if top_object_type and top_object_score >= 7.0:
            top_match = next((item for item in merged_objects if item.get("object_type") == top_object_type), None)
            if top_match:
                merged_objects = [top_match, *[item for item in merged_objects if item is not top_match]]
    return merged_task_model, merged_objects

AI_ROLE_ALIASES: dict[str, str] = {
    "机构名称": "entity_name",
    "主体名称": "entity_name",
    "基金会名称": "entity_name",
    "品牌": "brand",
    "品类": "category",
    "类目": "category",
    "商品": "product",
    "商品名称": "product",
    "产品": "product",
    "SKU": "sku",
    "SPU": "spu",
    "机构类型": "organization_type",
    "基金会类型": "organization_type",
    "服务领域": "channel",
    "领域": "channel",
    "地区": "region",
    "注册地": "region",
    "项目地点": "region",
    "省份": "region",
    "城市": "region",
    "时间": "time",
    "日期": "time",
    "年度": "time",
    "报告年度": "time",
    "成立日期": "time",
    "收入": "revenue",
    "总收入": "revenue",
    "捐赠收入": "revenue",
    "资助收入": "revenue",
    "支出": "spend",
    "总支出": "spend",
    "公益支出": "spend",
    "成本": "spend",
    "价格": "price",
    "库存": "inventory",
    "曝光": "reach",
    "触达": "reach",
    "互动": "interaction",
    "点击": "interaction",
    "转化": "conversion",
    "留存": "conversion",
    "实验分组": "experiment_group",
    "文本语义": "text_semantic",
    "统一信用代码": "entity_id",
    "机构唯一标识": "entity_id",
    "登记管理机关": "registry_authority",
    "治理活动指标": "governance",
}

MEDIA_VALUE_KEYWORDS = [
    "bilibili",
    "抖音",
    "快手",
    "小红书",
    "微博",
    "优酷",
    "芒果",
    "腾讯",
    "京东",
    "淘宝",
]

DEVICE_VALUE_KEYWORDS = [
    "phone",
    "pc",
    "ott",
    "pad",
    "移动端",
    "多屏",
    "大屏",
]

PLACEMENT_VALUE_KEYWORDS = [
    "开屏",
    "前贴片",
    "暂停",
    "信息流",
    "闪屏",
    "banner",
    "top",
    "程序化",
    "pdb",
    "pd池",
    "资源位",
    "广告位",
]

CHANNEL_VALUE_KEYWORDS = [
    "门店",
    "直营",
    "经销",
    "电商",
    "淘宝",
    "京东",
    "天猫",
]

BRAND_VALUE_HINTS = [
    "品牌",
    "系列",
]

REGION_VALUE_KEYWORDS = [
    "华东",
    "华南",
    "华北",
    "上海",
    "北京",
    "广东",
    "江苏",
    "浙江",
    "山东",
    "四川",
]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def _keyword_score(text: str, keywords: list[str]) -> float:
    return float(sum(1.0 for keyword in keywords if keyword.lower() in text))


def _format_confidence(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _confidence_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, 0)


def _series_is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series)


def _series_is_datetime(series: pd.Series) -> bool:
    return pd.api.types.is_datetime64_any_dtype(series)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _column_profile(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    series = frame[column]
    non_null = series.dropna()
    unique_ratio = float(non_null.nunique() / max(len(non_null), 1)) if len(non_null) else 0.0
    return {
        "column": column,
        "dtype": str(series.dtype),
        "missing_ratio": float(series.isna().mean()) if len(series) else 0.0,
        "unique_ratio": unique_ratio,
        "is_numeric": _series_is_numeric(series),
        "is_datetime": _series_is_datetime(series),
        "sample_values": non_null.astype(str).head(5).tolist(),
    }


def _value_signal(values: list[str], keywords: list[str]) -> float:
    joined = " ".join(value.lower() for value in values[:8])
    return float(sum(1.0 for keyword in keywords if keyword.lower() in joined))


def _placement_pattern_score(values: list[str]) -> float:
    score = 0.0
    for value in values[:8]:
        if any(token in value for token in ["-", "【", "】", "（", "）", "(", ")"]):
            score += 0.4
        if len(value) >= 12:
            score += 0.2
    return score


def _build_requirement_context(request: SmartReportRequest, dataset_name: str, sheet_name: str) -> dict[str, Any]:
    frontend_context_pack = build_frontend_context_pack(request)
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "user_requirement": request.user_requirement,
        "problem_to_solve": request.problem_to_solve,
        "target_audience": request.target_audience,
        "core_purpose": request.core_purpose,
        "expected_result": request.expected_result,
        "key_constraints": request.key_constraints,
        "business_background_name": request.business_background_name,
        "business_background_text": request.business_background_text[:4000],
        "historical_report_name": request.historical_report_name,
        "historical_report_text": request.historical_report_text[:4000],
        "frontend_context_pack": frontend_context_pack,
        "frontend_context_brief": str(frontend_context_pack.get("context_brief") or ""),
    }


def _resolved_request(request: SmartReportRequest, completed_inputs: dict[str, Any]) -> SmartReportRequest:
    payload = request.model_dump()
    mapping = {
        "business_background_name": "completed_business_background_name",
        "business_background_text": "completed_business_background_text",
        "user_requirement": "completed_user_requirement",
        "problem_to_solve": "completed_problem_to_solve",
        "target_audience": "completed_target_audience",
        "core_purpose": "completed_core_purpose",
        "expected_result": "completed_expected_result",
        "key_constraints": "completed_key_constraints",
    }
    for field, completed_key in mapping.items():
        if not str(payload.get(field) or "").strip():
            completed_value = str(completed_inputs.get(completed_key) or "").strip()
            if completed_value:
                payload[field] = completed_value
    return SmartReportRequest(**payload)


def _task_model(request: SmartReportRequest, dataset_name: str, requirement_model: dict[str, Any] | None = None) -> dict[str, Any]:
    requirement_model = requirement_model or {}
    frontend_context_pack = build_frontend_context_pack(request)
    refined_problem = str(requirement_model.get("refined_problem") or "").strip()
    refined_audience = str(requirement_model.get("refined_audience") or "").strip()
    refined_purpose = str(requirement_model.get("refined_purpose") or "").strip()
    refined_expected_result = str(requirement_model.get("refined_expected_result") or "").strip()
    explicit_constraints = [str(item).strip() for item in requirement_model.get("explicit_constraints", []) if str(item).strip()]
    full_text = " ".join(
        [
            dataset_name,
            request.user_requirement,
            request.problem_to_solve,
            request.target_audience,
            request.core_purpose,
            request.expected_result,
            request.key_constraints,
            request.business_background_name,
            request.business_background_text,
            str(frontend_context_pack.get("context_brief") or ""),
            " ".join(str(item) for item in frontend_context_pack.get("domain_lexicon", [])[:8]),
            refined_problem,
            refined_audience,
            refined_purpose,
            refined_expected_result,
            " ".join(explicit_constraints),
            " ".join(str(item) for item in requirement_model.get("must_answer_questions", [])[:4]),
            " ".join(str(item) for item in requirement_model.get("recommended_focus", [])[:4]),
        ]
    )
    normalized = _normalize_text(full_text)
    candidates = []
    for family, keywords in TASK_FAMILIES.items():
        score = _keyword_score(normalized, keywords)
        if family == "performance_benchmark" and dataset_name.lower().startswith("stress-"):
            score += 3.0
        if score > 0:
            candidates.append(
                {
                    "family": family,
                    "score": round(score, 2),
                    "confidence": _format_confidence(min(1.0, score / 5.0)),
                }
            )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    primary = candidates[0]["family"] if candidates else "mixed_business_review"
    return {
        "problem": refined_problem or request.problem_to_solve.strip() or request.user_requirement.strip() or "尚未显式给出单一问题，系统按决策支持任务处理。",
        "audience": refined_audience or request.target_audience.strip() or "业务负责人 / 分析负责人 / 工程负责人",
        "purpose": refined_purpose or request.core_purpose.strip() or request.expected_result.strip() or "形成可用于决策的专业报告",
        "expected_result": refined_expected_result or request.expected_result.strip() or "一份主报告与配套附件",
        "constraints": explicit_constraints or [item.strip() for item in request.key_constraints.replace("；", "\n").replace(";", "\n").splitlines() if item.strip()][:5],
        "success_criteria": [str(item) for item in requirement_model.get("success_criteria", []) if str(item).strip()][:5],
        "must_answer_questions": [str(item) for item in requirement_model.get("must_answer_questions", []) if str(item).strip()][:5],
        "non_goals": [str(item) for item in requirement_model.get("non_goals", []) if str(item).strip()][:5],
        "output_preferences": [str(item) for item in requirement_model.get("output_preferences", []) if str(item).strip()][:5],
        "ambiguity_flags": [str(item) for item in requirement_model.get("ambiguity_flags", []) if str(item).strip()][:5],
        "recommended_focus": [str(item) for item in requirement_model.get("recommended_focus", []) if str(item).strip()][:5],
        "primary_family": primary,
        "family_candidates": candidates[:4],
    }


def _recognize_objects(frame: pd.DataFrame, dataset_name: str, task_family: str, request: SmartReportRequest) -> list[dict[str, Any]]:
    joined_columns = " ".join(frame.columns.astype(str).tolist()).lower()
    joined_context = " ".join(
        [
            dataset_name.lower(),
            task_family.lower(),
            joined_columns,
            request.business_background_name.lower(),
            request.business_background_text.lower(),
        ]
    )
    candidates: list[dict[str, Any]] = []
    for object_type, rule in OBJECT_RULES.items():
        score = _keyword_score(joined_context, rule["tokens"])
        if task_family == "performance_benchmark" and object_type == "performance_benchmark_table":
            score += 3.0
        if object_type == "nonprofit_project_portfolio":
            signature_hits = sum(1 for token in ["基金会", "项目名称", "项目收入", "项目支出", "服务领域"] if token in joined_columns)
            score += signature_hits * 1.4
            if task_family == "foundation_review":
                score += 2.0
        if object_type == "internet_operations_log":
            signature_hits = sum(1 for token in ["运营", "增长", "留存", "转化", "活跃", "渠道", "活动", "event", "funnel", "cohort"] if token in joined_context)
            score += signature_hits * 0.8
            if task_family == "internet_ops_review":
                score += 2.0
        if object_type == "management_accounting_statement":
            signature_hits = sum(1 for token in ["预算", "实际", "偏差", "利润", "毛利", "净利润", "现金流", "资产", "负债", "应收", "应付", "存货", "成本中心", "利润中心", "budget", "variance", "cash", "profit"] if token in joined_context)
            score += signature_hits * 0.9
            if task_family == "management_accounting_review":
                score += 2.0
        if object_type == "content_performance_table":
            signature_hits = sum(1 for token in ["内容", "标题", "作者", "发布", "阅读", "点赞", "评论", "收藏", "分享", "播放", "content", "title", "author"] if token in joined_context)
            score += signature_hits * 0.8
            if task_family == "internet_ops_review":
                score += 1.5
        if score <= 0:
            continue
        candidates.append(
            {
                "object_type": object_type,
                "score": round(score, 2),
                "confidence": _format_confidence(min(1.0, score / 6.0)),
                "observation_unit": rule["observation_unit"],
                "preferred_modules": rule["modules"],
                "preferred_methods": rule["preferred_methods"],
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    if not candidates:
        candidates.append(
            {
                "object_type": "generic_business_table",
                "score": 0.1,
                "confidence": "low",
                "observation_unit": "单行记录对应一个现实世界观察单位",
                "preferred_modules": ["decision_summary", "analysis_program", "quality", "method_execution", "confidence_boundary"],
                "preferred_methods": ["correlation", "normality", "pca"],
            }
        )
    return candidates[:4]


def _semantic_mapping(frame: pd.DataFrame) -> dict[str, Any]:
    column_mappings: list[dict[str, Any]] = []
    role_summary: dict[str, list[dict[str, Any]]] = {}
    for column in frame.columns.astype(str).tolist():
        profile = _column_profile(frame, column)
        normalized_name = _normalize_text(column)
        value_samples = profile["sample_values"]
        role_candidates: list[dict[str, Any]] = []
        for role, keywords in ROLE_RULES.items():
            score = _keyword_score(normalized_name, keywords)
            if role == "time" and profile["is_datetime"]:
                score += 2.5
            if role in {"spend", "reach", "interaction", "conversion", "revenue", "price"} and profile["is_numeric"]:
                score += 1.0
            if role in {"brand", "media", "channel", "device", "region", "audience", "experiment_group"} and not profile["is_numeric"]:
                score += 0.8
            if role == "text_semantic" and not profile["is_numeric"] and profile["unique_ratio"] >= 0.3:
                score += 0.6
            if role == "media":
                score += _value_signal(value_samples, MEDIA_VALUE_KEYWORDS) * 0.9
            elif role == "device":
                score += _value_signal(value_samples, DEVICE_VALUE_KEYWORDS) * 0.9
            elif role == "placement":
                score += _value_signal(value_samples, PLACEMENT_VALUE_KEYWORDS) * 0.8
                score += _placement_pattern_score(value_samples)
            elif role == "channel":
                score += _value_signal(value_samples, CHANNEL_VALUE_KEYWORDS) * 0.8
            elif role == "brand":
                score += _value_signal(value_samples, BRAND_VALUE_HINTS) * 0.6
                score -= _value_signal(value_samples, PLACEMENT_VALUE_KEYWORDS) * 0.9
                score -= _value_signal(value_samples, MEDIA_VALUE_KEYWORDS) * 0.7
                if _placement_pattern_score(value_samples) >= 1.0:
                    score -= 1.0
            elif role == "region":
                score += _value_signal(value_samples, REGION_VALUE_KEYWORDS) * 0.8
            if score <= 0:
                continue
            role_candidates.append(
                {
                    "role": role,
                    "score": round(score, 2),
                    "confidence": _format_confidence(min(1.0, score / 4.0)),
                }
            )
        role_candidates.sort(key=lambda item: item["score"], reverse=True)
        mapping = {
            "column": column,
            "dtype": profile["dtype"],
            "top_roles": role_candidates[:3],
            "best_role": role_candidates[0]["role"] if role_candidates else "unmapped",
            "best_confidence": role_candidates[0]["confidence"] if role_candidates else "low",
            "missing_ratio": round(profile["missing_ratio"], 4),
            "unique_ratio": round(profile["unique_ratio"], 4),
        }
        column_mappings.append(mapping)
        if role_candidates:
            role_summary.setdefault(role_candidates[0]["role"], []).append(
                {
                    "column": column,
                    "confidence": role_candidates[0]["confidence"],
                }
            )
    return {"columns": column_mappings, "role_summary": role_summary}


def _rank_hypotheses(task_model: dict[str, Any], object_candidates: list[dict[str, Any]], semantic_mapping: dict[str, Any]) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []
    primary_family = task_model["primary_family"]
    role_summary = semantic_mapping["role_summary"]
    for candidate in object_candidates[:3]:
        base_score = float(candidate["score"])
        if primary_family == "performance_benchmark" and candidate["object_type"] == "performance_benchmark_table":
            base_score += 2.0
        if candidate["object_type"] == "media_performance_log" and {"media", "reach", "interaction"} <= set(role_summary.keys()):
            base_score += 1.5
        if candidate["object_type"] == "sales_transaction_panel" and {"revenue", "price", "channel"} & set(role_summary.keys()):
            base_score += 1.2
        hypotheses.append(
            {
                "title": candidate["object_type"],
                "score": round(base_score, 2),
                "confidence": _format_confidence(min(1.0, base_score / 7.0)),
                "why": f"对象识别候选 `{candidate['object_type']}` 与当前任务 `{primary_family}` 匹配度较高。",
            }
        )
    hypotheses.sort(key=lambda item: item["score"], reverse=True)
    return hypotheses


def _build_ai_classification_context(
    request: SmartReportRequest,
    dataset_name: str,
    frame: pd.DataFrame,
    task_model: dict[str, Any],
    object_candidates: list[dict[str, Any]],
    semantic_mapping: dict[str, Any],
    requirement_model: dict[str, Any],
) -> dict[str, Any]:
    frontend_context_pack = build_frontend_context_pack(request)
    column_profiles: list[dict[str, Any]] = []
    for column in frame.columns.astype(str).tolist()[:24]:
        profile = _column_profile(frame, column)
        column_profiles.append(
            {
                "column": column,
                "dtype": profile["dtype"],
                "missing_ratio": round(profile["missing_ratio"], 4),
                "unique_ratio": round(profile["unique_ratio"], 4),
                "is_numeric": profile["is_numeric"],
                "is_datetime": profile["is_datetime"],
                "sample_values": profile["sample_values"][:5],
            }
        )
    return {
        "dataset_name": dataset_name,
        "user_requirement": request.user_requirement,
        "problem_to_solve": request.problem_to_solve,
        "target_audience": request.target_audience,
        "core_purpose": request.core_purpose,
        "expected_result": request.expected_result,
        "key_constraints": request.key_constraints,
        "business_background_name": request.business_background_name,
        "business_background_text": request.business_background_text[:4000],
        "frontend_context_pack": frontend_context_pack,
        "frontend_context_brief": str(frontend_context_pack.get("context_brief") or ""),
        "columns": frame.columns.astype(str).tolist()[:40],
        "column_profiles": column_profiles,
        "sample_rows": frame.head(6).where(pd.notnull(frame.head(6)), None).astype(object).to_dict(orient="records"),
        "heuristic_task_model": task_model,
        "heuristic_object_candidates": object_candidates[:4],
        "heuristic_semantic_mapping": semantic_mapping.get("columns", [])[:12],
        "requirement_model": requirement_model,
    }


def _confidence_value(label: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(str(label or "low"), 0)


def _normalize_ai_role(role: str) -> str | None:
    role = str(role or "").strip()
    if not role:
        return None
    if role in ROLE_RULES:
        return role
    normalized = _normalize_text(role)
    for alias, mapped in AI_ROLE_ALIASES.items():
        alias_normalized = _normalize_text(alias)
        if normalized == alias_normalized or alias_normalized in normalized:
            return mapped
    return None


def _set_mapping_role(mapping: dict[str, Any], role: str, confidence: str = "high") -> None:
    top_roles = [entry for entry in mapping.get("top_roles", []) if entry.get("role") != role]
    mapping["top_roles"] = [{"role": role, "score": 9.0, "confidence": confidence}, *top_roles][:3]
    mapping["best_role"] = role
    mapping["best_confidence"] = confidence


def _sanitize_semantic_mapping(frame: pd.DataFrame, semantic_mapping: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "columns": [dict(item) for item in semantic_mapping.get("columns", [])],
        "role_summary": {},
    }
    metric_tokens = ["收入", "支出", "捐赠", "公益", "金额", "总额", "次数", "占比", "率", "roi"]
    for item in merged["columns"]:
        column = str(item.get("column") or "")
        lower = column.lower()
        if any(token in lower for token in ["invoiceno", "invoice_no", "invoice number", "invoice no", "订单号"]) and item.get("best_role") != "entity_id":
            _set_mapping_role(item, "entity_id", "high")
        elif ("统一信用代码" in column or "信用代码" in column) and item.get("best_role") != "entity_id":
            _set_mapping_role(item, "entity_id", "high")
        elif any(token in column for token in ["基金会名称", "机构名称", "主体名称"]) and item.get("best_role") != "entity_name":
            _set_mapping_role(item, "entity_name", "high")
        elif any(token in lower for token in ["customerid", "customer_id", "customer id", "客户id", "客户编号"]) and item.get("best_role") != "audience":
            _set_mapping_role(item, "audience", "high")
        elif any(token in column for token in ["基金会类型", "机构类型", "组织类型"]) and item.get("best_role") != "organization_type":
            _set_mapping_role(item, "organization_type", "high")
        elif "登记管理机关" in column and item.get("best_role") != "registry_authority":
            _set_mapping_role(item, "registry_authority", "high")
        elif "理事会" in column and "次数" in column and item.get("best_role") != "governance":
            _set_mapping_role(item, "governance", "high")
        elif "活动" in column and not pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") not in {"channel", "experiment_group"}:
            _set_mapping_role(item, "channel", "medium")
        elif any(token in column for token in ["品类", "类目"]) and not pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "category":
            _set_mapping_role(item, "category", "high")
        elif any(token in lower for token in ["stockcode", "stock_code", "stock code"]) and item.get("best_role") != "sku":
            _set_mapping_role(item, "sku", "high")
        elif any(token in lower for token in ["sku", "sku_id", "商品sku", "货号"]) and item.get("best_role") != "sku":
            _set_mapping_role(item, "sku", "high")
        elif any(token in lower for token in ["spu", "spu_id", "商品spu"]) and item.get("best_role") != "spu":
            _set_mapping_role(item, "spu", "high")
        elif any(token in lower for token in ["description", "item description"]) and not pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "product":
            _set_mapping_role(item, "product", "high")
        elif any(token in column for token in ["商品", "商品名", "产品"]) and not pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "product":
            _set_mapping_role(item, "product", "high")
        elif any(token in column for token in ["内容主题", "主题"]) and not pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "text_semantic":
            _set_mapping_role(item, "text_semantic", "high")
        elif any(token in lower for token in ["quantity", "qty"]) and pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "conversion":
            _set_mapping_role(item, "conversion", "high")
        elif any(token in lower for token in ["unitprice", "unit_price", "unit price"]) and pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "price":
            _set_mapping_role(item, "price", "high")
        elif lower == "country" and not pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "region":
            _set_mapping_role(item, "region", "high")
        elif any(token in column for token in ["活跃用户", "曝光", "触达"]) and pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "reach":
            _set_mapping_role(item, "reach", "high")
        elif any(token in column for token in ["新增用户", "注册数", "留存用户", "留存率", "转化率", "订单数", "转化数"]) and pd.api.types.is_numeric_dtype(frame[column]) and item.get("best_role") != "conversion":
            _set_mapping_role(item, "conversion", "high")
        elif column.strip() in {"年度", "年份"} and pd.api.types.is_numeric_dtype(frame[column]):
            _set_mapping_role(item, "time", "high")
        elif any(token in lower for token in ["date", "time"]) and not any(token in lower for token in ["spend", "revenue", "income", "cost", "donation", "roi"]) and pd.api.types.is_numeric_dtype(frame[column]):
            _set_mapping_role(item, "time", "medium")

    role_summary: dict[str, list[dict[str, Any]]] = {}
    for item in merged["columns"]:
        if item.get("best_role") and item.get("best_role") != "unmapped":
            role_summary.setdefault(item["best_role"], []).append({"column": item["column"], "confidence": item.get("best_confidence", "low")})
    merged["role_summary"] = role_summary
    return merged


def _merge_ai_task_model(task_model: dict[str, Any], ai_hints: dict[str, Any]) -> dict[str, Any]:
    ai_candidates = list(ai_hints.get("task_family_candidates") or [])
    if not ai_candidates:
        return task_model
    ai_candidates = sorted(ai_candidates, key=lambda item: float(item.get("score", 0)), reverse=True)
    merged = dict(task_model)
    merged["family_candidates"] = ai_candidates[:4]
    top = ai_candidates[0]
    if _confidence_value(top.get("confidence", "low")) >= 1:
        merged["primary_family"] = str(top.get("family") or merged["primary_family"])
    return merged


def _merge_ai_object_candidates(object_candidates: list[dict[str, Any]], ai_hints: dict[str, Any]) -> list[dict[str, Any]]:
    ai_candidates = list(ai_hints.get("object_candidates") or [])
    if not ai_candidates:
        return object_candidates
    by_object = {item["object_type"]: dict(item) for item in object_candidates}
    specific_confident = any(
        item.get("object_type") != "generic_business_table"
        and _confidence_value(item.get("confidence", "low")) >= 1
        for item in object_candidates
    )
    for item in ai_candidates:
        object_type = str(item.get("object_type") or "")
        if not object_type:
            continue
        if object_type == "generic_business_table" and specific_confident:
            continue
        incoming = {
            "object_type": object_type,
            "score": round(float(item.get("score", 0)), 2),
            "confidence": str(item.get("confidence") or "low"),
            "observation_unit": item.get("observation_unit") or by_object.get(object_type, {}).get("observation_unit") or "单行记录对应一个现实世界观察单位",
            "preferred_modules": by_object.get(object_type, {}).get("preferred_modules", ["decision_summary", "analysis_program", "quality", "method_execution", "confidence_boundary"]),
            "preferred_methods": by_object.get(object_type, {}).get("preferred_methods", ["correlation", "normality", "pca"]),
        }
        current = by_object.get(object_type)
        if not current or float(incoming["score"]) > float(current.get("score", 0)):
            by_object[object_type] = incoming
    merged = list(by_object.values())
    merged.sort(
        key=lambda item: (
            float(item.get("score", 0)) - (2.0 if item.get("object_type") == "generic_business_table" and specific_confident else 0.0),
            _confidence_value(item.get("confidence", "low")),
        ),
        reverse=True,
    )
    return merged[:4]


def _merge_ai_semantic_mapping(semantic_mapping: dict[str, Any], ai_hints: dict[str, Any]) -> dict[str, Any]:
    column_hints = list(ai_hints.get("column_role_hints") or [])
    if not column_hints:
        return semantic_mapping
    merged = {
        "columns": [dict(item) for item in semantic_mapping.get("columns", [])],
        "role_summary": {key: list(value) for key, value in semantic_mapping.get("role_summary", {}).items()},
    }
    by_column = {item["column"]: item for item in merged["columns"]}
    for hint in column_hints:
        column = str(hint.get("column") or "")
        role = _normalize_ai_role(str(hint.get("role") or ""))
        confidence = str(hint.get("confidence") or "low")
        if not column or not role or column not in by_column:
            continue
        current = by_column[column]
        if _confidence_value(confidence) >= _confidence_value(current.get("best_confidence", "low")):
            top_roles = [entry for entry in current.get("top_roles", []) if entry.get("role") != role]
            current["top_roles"] = [{"role": role, "score": round(float(hint.get("score", 0) or 0), 2), "confidence": confidence}, *top_roles][:3]
            current["best_role"] = role
            current["best_confidence"] = confidence
    role_summary: dict[str, list[dict[str, Any]]] = {}
    for item in merged["columns"]:
        if item.get("best_role") and item.get("best_role") != "unmapped":
            role_summary.setdefault(item["best_role"], []).append({"column": item["column"], "confidence": item.get("best_confidence", "low")})
    merged["role_summary"] = role_summary
    return merged


def _add_ratio_metric(frame: pd.DataFrame, numerator: str, denominator: str, name: str) -> tuple[pd.DataFrame, dict[str, Any]] | None:
    num = pd.to_numeric(frame[numerator], errors="coerce")
    den = pd.to_numeric(frame[denominator], errors="coerce")
    usable = den.notna() & (den != 0) & num.notna()
    if usable.mean() < 0.8:
        return None
    enriched = frame.copy()
    enriched[name] = np.where(usable, num / den, np.nan)
    return enriched, {
        "metric": name,
        "formula": f"{numerator} / {denominator}",
        "confidence": "high",
    }


def _derived_metrics(frame: pd.DataFrame, semantic_mapping: dict[str, Any]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    role_summary = semantic_mapping["role_summary"]
    enriched = frame.copy()
    metrics: list[dict[str, Any]] = []

    def first(role: str) -> str | None:
        candidates = role_summary.get(role, [])
        return candidates[0]["column"] if candidates else None

    spend = first("spend")
    reach = first("reach")
    interaction = first("interaction")
    conversion = first("conversion")
    revenue = first("revenue")
    price = first("price")

    if not revenue and conversion and price and "销售额" not in enriched.columns:
        qty_series = pd.to_numeric(enriched[conversion], errors="coerce")
        price_series = pd.to_numeric(enriched[price], errors="coerce")
        usable = qty_series.notna() & price_series.notna()
        if usable.mean() >= 0.8:
            enriched["销售额"] = np.where(usable, qty_series * price_series, np.nan)
            metrics.append(
                {
                    "metric": "销售额",
                    "formula": f"{conversion} * {price}",
                    "confidence": "high",
                }
            )

    metric_specs = [
        (interaction, reach, "CTR"),
        (spend, reach, "CPM"),
        (spend, interaction, "CPC"),
        (conversion, interaction, "CVR"),
        (revenue, spend, "ROI"),
    ]
    for numerator, denominator, name in metric_specs:
        if not numerator or not denominator or numerator == denominator or name in enriched.columns:
            continue
        if name == "ROI":
            denominator_text = str(denominator or "").lower()
            pseudo_cost_tokens = ("freight", "shipping", "delivery", "logistic", "物流", "运费", "履约")
            if any(token in denominator_text for token in pseudo_cost_tokens):
                continue
        built = _add_ratio_metric(enriched, numerator, denominator, name)
        if built:
            enriched, info = built
            metrics.append(info)
    return enriched, metrics




def _existing_efficiency_metrics(frame: pd.DataFrame) -> list[str]:
    keywords = [
        "rate",
        "ratio",
        "retention",
        "conversion",
        "ctr",
        "cvr",
        "engagement",
        "留存",
        "转化",
        "活跃",
        "互动",
        "完成率",
        "激活",
        "打开率",
    ]
    metrics: list[str] = []
    for column in frame.columns.astype(str).tolist():
        lower = column.lower()
        if any(token in lower or token in column for token in keywords):
            if pd.api.types.is_numeric_dtype(frame[column]):
                metrics.append(column)
    return metrics[:6]


def _detect_procurement_sales_fusion(
    *,
    task_model: dict[str, Any],
    object_candidates: list[dict[str, Any]],
    request: SmartReportRequest,
    dataset_name: str,
    frame: pd.DataFrame,
) -> dict[str, Any]:
    columns = [str(column) for column in frame.columns.astype(str).tolist()[:48]]
    joined = " ".join(
        [
            dataset_name,
            request.user_requirement,
            request.problem_to_solve,
            request.target_audience,
            request.core_purpose,
            request.expected_result,
            request.key_constraints,
            request.business_background_name,
            request.business_background_text,
            " ".join(columns),
        ]
    )
    normalized = _normalize_text(joined)
    procurement_tokens = [
        "procurement",
        "contract",
        "supplier",
        "vendor",
        "purchase",
        "payment",
        "spend",
        "waiver",
        "invoice",
        "commitment",
        "pipeline",
        "合同",
        "采购",
        "供应商",
        "支付",
        "支出",
        "采购卡",
        "成本",
    ]
    sales_tokens = [
        "sales",
        "gmv",
        "order",
        "customer",
        "sku",
        "spu",
        "product",
        "description",
        "stockcode",
        "quantity",
        "unitprice",
        "inventory",
        "profit",
        "销量",
        "销售额",
        "订单",
        "客户",
        "商品",
        "货号",
        "库存",
        "毛利",
        "退货",
    ]
    commercial_column_tokens = [
        "sku",
        "spu",
        "product",
        "description",
        "stockcode",
        "quantity",
        "unitprice",
        "invoice",
        "customer",
        "sales",
        "gmv",
        "profit",
        "inventory",
        "category",
        "商品",
        "销量",
        "销售额",
        "订单",
        "客户",
        "库存",
    ]
    procurement_hits = sum(token in normalized for token in procurement_tokens)
    sales_hits = sum(token in normalized for token in sales_tokens)
    commercial_column_hits = sum(any(token in str(column).lower() for token in commercial_column_tokens) for column in columns)
    object_types = {str(item.get("object_type") or "") for item in object_candidates}
    has_management_object = bool(object_types & {"management_accounting_statement", "financial_budget_table", "procurement_spend_register"})
    has_sales_object = "sales_transaction_panel" in object_types
    current_family = str(task_model.get("primary_family") or "")
    has_strong_sales_side = has_sales_object or (commercial_column_hits >= 3 and sales_hits >= 2)
    enabled = (
        has_strong_sales_side
        and (has_management_object or procurement_hits >= 2 or current_family == "management_accounting_review")
    )
    prefer_management = enabled and (
        has_management_object or current_family == "management_accounting_review"
    )
    summary = ""
    if enabled:
        summary = "当前数据同时出现采购/责任控制和商品/SKU经营信号，报告应按采销一体化来组织，而不是把采购与销售拆成两份互斥结论。"
    return {
        "procurement_sales_management": enabled,
        "prefer_management_accounting": prefer_management,
        "procurement_hits": procurement_hits,
        "sales_hits": sales_hits,
        "commercial_column_hits": commercial_column_hits,
        "summary": summary,
    }


def _analysis_program(
    task_model: dict[str, Any],
    object_candidates: list[dict[str, Any]],
    semantic_mapping: dict[str, Any],
    derived_metrics: list[dict[str, Any]],
    frame: pd.DataFrame,
) -> dict[str, Any]:
    primary_object = object_candidates[0]
    role_summary = semantic_mapping["role_summary"]
    body_modules = list(primary_object["preferred_modules"])
    appendix_modules = ["method_catalog", "raw_tables"]
    family = task_model["primary_family"]
    fusion_mode = str(task_model.get("fusion_mode") or "")
    if family == "media_review":
        body_modules = ["analysis_program", "quality", "method_execution", "numeric", "category", "temporal", "market", "semantic", "confidence_boundary"]
    elif family == "internet_ops_review":
        body_modules = ["analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "growth", "predictive", "confidence_boundary"]
    elif family == "foundation_review":
        body_modules = ["analysis_program", "quality", "method_execution", "semantic", "numeric", "category", "temporal", "market", "growth", "confidence_boundary"]
    elif family == "management_accounting_review":
        body_modules = ["analysis_program", "quality", "method_execution", "numeric", "category", "temporal", "predictive", "confidence_boundary"]
        if fusion_mode == "procurement_sales_management":
            body_modules = ["analysis_program", "quality", "method_execution", "numeric", "category", "temporal", "market", "growth", "predictive", "confidence_boundary"]
    elif family == "procurement_sales_review":
        body_modules = ["analysis_program", "quality", "method_execution", "numeric", "category", "temporal", "market", "growth", "predictive", "confidence_boundary"]
    elif family == "sales_review":
        body_modules = ["analysis_program", "quality", "numeric", "category", "temporal", "market", "growth", "predictive", "confidence_boundary"]
    elif family == "consumer_research":
        body_modules = ["analysis_program", "quality", "semantic", "category", "segmentation", "method_execution", "confidence_boundary"]
    elif family == "brand_listening":
        body_modules = ["analysis_program", "semantic", "semantic", "temporal", "category", "confidence_boundary"]
    elif family == "experiment_review":
        body_modules = ["analysis_program", "quality", "method_execution", "experimentation", "predictive", "confidence_boundary"]
    elif family == "performance_benchmark":
        body_modules = ["analysis_program", "quality", "numeric", "temporal", "method_execution", "confidence_boundary"]

    core_outcomes = []
    if family in {"sales_review", "procurement_sales_review"} or (family == "management_accounting_review" and fusion_mode == "procurement_sales_management"):
        derived_sales_metrics = [
            item["metric"]
            for item in derived_metrics
            if str(item.get("metric") or "").strip() in {"销售额", "GMV", "Revenue"}
        ]
        core_outcomes.extend(derived_sales_metrics[:2])
        for role in ["revenue", "conversion", "price", "spend"]:
            if role in role_summary:
                core_outcomes.extend(item["column"] for item in role_summary[role][:2])
    else:
        for role in ["conversion", "revenue", "interaction", "reach", "spend"]:
            if role in role_summary:
                core_outcomes.extend(item["column"] for item in role_summary[role][:2])
    core_outcomes = _dedupe_preserve_order(core_outcomes)
    efficiency_metrics = [item["metric"] for item in derived_metrics]
    for metric in _existing_efficiency_metrics(frame):
        if metric not in efficiency_metrics:
            efficiency_metrics.append(metric)
    slices = []
    slice_roles = ["media", "channel", "device", "placement", "brand", "region", "audience", "experiment_group", "entity_name", "organization_type", "governance"]
    if family == "sales_review":
        slice_roles = ["category", "product", "sku", "spu", "brand", "region", "channel", "audience"]
    elif family == "procurement_sales_review":
        slice_roles = ["entity_name", "organization_type", "governance", "category", "product", "sku", "spu", "brand", "region", "channel"]
    elif family == "management_accounting_review" and fusion_mode == "procurement_sales_management":
        slice_roles = ["entity_name", "organization_type", "governance", "category", "product", "sku", "spu", "brand", "region", "channel"]
    for role in slice_roles:
        if role in role_summary:
            slices.extend(item["column"] for item in role_summary[role][:2])
    slices = _dedupe_preserve_order(slices)

    if task_model["primary_family"] == "performance_benchmark":
        can_analyze = [
            "导入完整性、字段识别稳定性、统计模块执行稳定性",
            "结构均衡性、分布偏态、指标冗余和大样本下的章节生成完整性",
        ]
        cannot_analyze = [
            "真实市场格局、真实投放策略优先级、真实品牌竞争判断",
        ]
    else:
        can_analyze = [
            "规模、效率、结构、时间波动和关键切片差异",
            "可稳健构造的派生指标与可执行动作建议",
        ]
        cannot_analyze = [
            "字段语义不稳、口径缺失或证据不足的强结论",
        ]
    if family == "procurement_sales_review" or fusion_mode == "procurement_sales_management":
        can_analyze.insert(0, "采购投入、责任主体、商品结构、订单承接、客户覆盖与库存/退货风险之间的联动关系")
        cannot_analyze.append("缺少采购成本、库存时间序列或供应商到SKU映射时的完整采销闭环归因")

    outcome_confidences = [
        item["confidence"]
        for role in ["conversion", "revenue", "interaction", "reach", "spend"]
        for item in role_summary.get(role, [])[:1]
    ]
    slice_confidences = [
        item["confidence"]
        for role in ["media", "channel", "device", "placement", "brand", "region", "audience", "experiment_group", "entity_name", "organization_type", "governance"]
        for item in role_summary.get(role, [])[:1]
    ]
    if outcome_confidences:
        outcome_rank = round(sum(_confidence_rank(value) for value in outcome_confidences) / len(outcome_confidences))
    else:
        outcome_rank = 0
    if slices and slice_confidences:
        slice_rank = round(sum(_confidence_rank(value) for value in slice_confidences) / len(slice_confidences))
    else:
        slice_rank = 0
    base_rank = _confidence_rank(primary_object["confidence"])
    combined_rank = min(base_rank, max(outcome_rank, 1) if core_outcomes else base_rank, max(slice_rank, 1) if slices else base_rank)
    if family == "procurement_sales_review" and primary_object["object_type"] == "sales_transaction_panel" and core_outcomes and len(slices) >= 3:
        combined_rank = max(combined_rank, 1)
    confidence = {0: "low", 1: "medium", 2: "high"}[max(0, min(2, combined_rank))]
    return {
        "observation_unit": primary_object["observation_unit"],
        "business_object": primary_object["object_type"],
        "core_outcomes": core_outcomes[:4],
        "efficiency_metrics": efficiency_metrics[:4],
        "explanatory_slices": slices[:5],
        "can_analyze": can_analyze,
        "cannot_analyze": cannot_analyze,
        "confidence": confidence,
        "body_modules": body_modules,
        "appendix_modules": appendix_modules,
        "preferred_methods": primary_object["preferred_methods"],
        "fusion_mode": fusion_mode,
    }


def _expert_recall(task_model: dict[str, Any], object_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family = str(task_model.get("primary_family") or "mixed_business_review")
    experts = list(EXPERT_RULES.get(family, []))
    if not experts:
        object_type = object_candidates[0]["object_type"] if object_candidates else "generic_business_table"
        experts = [
            {
                "expert": "通用市场分析负责人",
                "focus": f"围绕 `{object_type}` 先定义观察单位、结果变量、切片和证据边界",
                "priority_questions": ["当前数据最可能服务什么判断", "哪些结论可以稳健输出"],
                "evidence_preference": ["字段语义", "结果变量", "切片结构"],
                "decision_outputs": ["初步判断", "后续补数清单"],
                "guardrails": ["不把猜测写成事实"],
            }
        ]
    return [_soulize_expert(family, item) for item in experts[:3]]


def _promote_family_consistent_candidates(task_model: dict[str, Any], object_candidates: list[dict[str, Any]], request: SmartReportRequest, dataset_name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    joined = " ".join(
        [
            dataset_name,
            request.user_requirement,
            request.problem_to_solve,
            request.target_audience,
            request.core_purpose,
            request.expected_result,
            request.key_constraints,
            request.business_background_name,
            request.business_background_text,
        ]
    )
    normalized = _normalize_text(joined)
    family = str(task_model.get("primary_family") or "mixed_business_review")
    finance_tokens = ["财务", "会计", "预算", "偏差", "利润", "现金流", "资产", "负债", "应收", "应付", "存货"]
    media_tokens = ["投放", "媒体", "曝光", "点击", "cpm", "cpc", "cpa", "campaign", "媒介"]
    ops_tokens = ["运营", "增长", "留存", "转化", "活跃"]
    procurement_tokens = ["procurement", "contract", "supplier", "vendor", "purchase", "payment", "spend", "waiver", "card", "transaction", "invoice", "commitment", "pipeline", "合同", "采购", "供应商", "支付", "支出", "采购卡", "waivers"]
    finance_hits = sum(token in normalized for token in finance_tokens)
    media_hits = sum(token in normalized for token in media_tokens)
    ops_hits = sum(token in normalized for token in ops_tokens)
    procurement_hits = sum(token in normalized for token in procurement_tokens)

    def _promote_family(family_name: str, object_type: str) -> None:
        nonlocal family, task_model, object_candidates
        match = next((item for item in object_candidates if item.get("object_type") == object_type), None)
        if not match:
            return
        if family != family_name:
            task_model["primary_family"] = family_name
            task_model["family_candidates"] = [
                {
                    "family": family_name,
                    "score": round(float(match.get("score", 0)), 2),
                    "confidence": match.get("confidence", "medium"),
                },
                *task_model.get("family_candidates", [])[:3],
            ]
        object_candidates = [match, *[item for item in object_candidates if item is not match]]
        family = family_name

    if "基金会" in normalized and any(item.get("object_type") == "nonprofit_project_portfolio" for item in object_candidates):
        _promote_family("foundation_review", "nonprofit_project_portfolio")
    elif procurement_hits >= 2 and any(item.get("object_type") in {"procurement_spend_register", "management_accounting_statement", "financial_budget_table", "sales_transaction_panel"} for item in object_candidates):
        preferred = next((item["object_type"] for item in object_candidates if item.get("object_type") in {"procurement_spend_register", "management_accounting_statement", "financial_budget_table", "sales_transaction_panel"}), None)
        if preferred:
            _promote_family("management_accounting_review", preferred)
    elif finance_hits >= 2 and finance_hits > media_hits and any(item.get("object_type") in {"management_accounting_statement", "financial_budget_table"} for item in object_candidates):
        preferred = next((item["object_type"] for item in object_candidates if item.get("object_type") in {"management_accounting_statement", "financial_budget_table"}), None)
        if preferred:
            _promote_family("management_accounting_review", preferred)
    elif ops_hits >= 2 and ops_hits >= media_hits and any(item.get("object_type") in {"internet_operations_log", "content_performance_table", "crm_funnel_event_log"} for item in object_candidates):
        preferred = next((item["object_type"] for item in object_candidates if item.get("object_type") in {"internet_operations_log", "content_performance_table", "crm_funnel_event_log"}), None)
        if preferred:
            _promote_family("internet_ops_review", preferred)
    elif media_hits >= 2 and any(item.get("object_type") == "media_performance_log" for item in object_candidates):
        _promote_family("media_review", "media_performance_log")
    elif any(token in normalized for token in ["销售", "订单", "销量", "sku", "spu"]) and any(item.get("object_type") == "sales_transaction_panel" for item in object_candidates):
        _promote_family("sales_review", "sales_transaction_panel")

    if family == "performance_benchmark" and not any(token in normalized for token in ["压测", "benchmark", "stress", "性能", "load", "latency", "吞吐"]):
        for preferred_family, preferred_object in [
            ("foundation_review", "nonprofit_project_portfolio"),
            ("management_accounting_review", "procurement_spend_register"),
            ("management_accounting_review", "management_accounting_statement"),
            ("internet_ops_review", "internet_operations_log"),
            ("media_review", "media_performance_log"),
            ("sales_review", "sales_transaction_panel"),
        ]:
            if any(item.get("object_type") == preferred_object for item in object_candidates):
                _promote_family(preferred_family, preferred_object)
                break

    preferred_objects_by_family = {
        "foundation_review": ["nonprofit_project_portfolio"],
        "management_accounting_review": ["procurement_spend_register", "management_accounting_statement", "financial_budget_table", "sales_transaction_panel"],
        "internet_ops_review": ["internet_operations_log"],
        "media_review": ["media_performance_log"],
        "sales_review": ["sales_transaction_panel"],
    }
    preferred_object = next(
        (
            object_type
            for object_type in preferred_objects_by_family.get(family, [])
            if any(item.get("object_type") == object_type for item in object_candidates)
        ),
        None,
    )
    if preferred_object:
        _promote_family(family, preferred_object)

    return task_model, object_candidates[:4]


def _self_critique(program: dict[str, Any], semantic_mapping: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("观察单位已定义", bool(program["observation_unit"])),
        ("业务对象已识别", bool(program["business_object"])),
        ("核心结果变量已定义", bool(program["core_outcomes"])),
        ("规模与效率已区分", bool(program["core_outcomes"]) and bool(program["efficiency_metrics"])),
        ("时间或切片已处理", bool(program["explanatory_slices"]) or "time" in semantic_mapping["role_summary"]),
        ("不确定性已标注", True),
        ("正文模块与当前任务相符", bool(program["body_modules"])),
    ]
    return [
        {"check": name, "passed": passed}
        for name, passed in checks
    ]


def _strong_family_signal(frame: pd.DataFrame, family: str) -> bool:
    joined = " ".join(_normalize_text(column) for column in frame.columns.astype(str).tolist())
    if family == "media_review":
        required_groups = [
            ["预算", "budget", "spend", "cost"],
            ["曝光", "impression", "reach"],
            ["点击", "click"],
            ["媒体", "media", "platform"],
            ["终端", "device", "phone", "pc", "ott"],
        ]
        return all(any(token in joined for token in group) for group in required_groups)
    if family == "internet_ops_review":
        required_groups = [
            ["活跃", "active"],
            ["新增", "new"],
            ["留存", "retention"],
            ["转化", "conversion"],
            ["渠道", "channel"],
        ]
        return all(any(token in joined for token in group) for group in required_groups)
    if family == "procurement_sales_review":
        required_groups = [
            ["product", "商品", "sku"],
            ["order", "订单"],
            ["customer", "客户"],
            ["seller", "supplier", "卖家", "供应商"],
            ["review", "评价", "comment", "score"],
        ]
        return all(any(token in joined for token in group) for group in required_groups)
    return False


def build_analysis_program(request: SmartReportRequest, dataset_name: str, sheet_name: str, frame: pd.DataFrame) -> dict[str, Any]:
    requirement_context = _build_requirement_context(request, dataset_name, sheet_name)
    requirement_context["columns"] = frame.columns.astype(str).tolist()[:40]
    requirement_context["sample_rows"] = frame.head(6).where(pd.notnull(frame.head(6)), None).astype(object).to_dict(orient="records")
    requirement_context["column_profiles"] = [
        {
            "column": column,
            **_column_profile(frame, column),
        }
        for column in frame.columns.astype(str).tolist()[:24]
    ]
    completed_inputs = codex_complete_input_fields(requirement_context)
    effective_request = _resolved_request(request, completed_inputs)
    requirement_context = _build_requirement_context(effective_request, dataset_name, sheet_name)
    requirement_context["columns"] = frame.columns.astype(str).tolist()[:40]
    requirement_context["sample_rows"] = frame.head(6).where(pd.notnull(frame.head(6)), None).astype(object).to_dict(orient="records")
    requirement_context["column_profiles"] = [
        {
            "column": column,
            **_column_profile(frame, column),
        }
        for column in frame.columns.astype(str).tolist()[:24]
    ]
    requirement_model = codex_synthesize_requirement(requirement_context)
    task_model = _task_model(effective_request, dataset_name, requirement_model)
    object_candidates = _recognize_objects(frame, dataset_name, task_model["primary_family"], effective_request)
    learned_route = _learned_route_hints(effective_request, dataset_name, frame)
    task_model, object_candidates = _merge_learned_route(task_model, object_candidates, learned_route)
    if object_candidates:
        primary_object = object_candidates[0]["object_type"]
        if task_model["primary_family"] == "mixed_business_review" and primary_object in {"internet_operations_log", "content_performance_table", "crm_funnel_event_log"}:
            task_model["primary_family"] = "internet_ops_review"
            task_model["family_candidates"] = [
                {
                    "family": "internet_ops_review",
                    "score": round(float(object_candidates[0].get("score", 0)), 2),
                    "confidence": object_candidates[0].get("confidence", "medium"),
                },
                *task_model.get("family_candidates", [])[:3],
            ]
        if task_model["primary_family"] == "mixed_business_review" and primary_object == "nonprofit_project_portfolio":
            task_model["primary_family"] = "foundation_review"
            task_model["family_candidates"] = [
                {
                    "family": "foundation_review",
                    "score": round(float(object_candidates[0].get("score", 0)), 2),
                    "confidence": object_candidates[0].get("confidence", "medium"),
                },
                *task_model.get("family_candidates", [])[:3],
            ]
        if task_model["primary_family"] == "mixed_business_review" and primary_object in {"management_accounting_statement", "financial_budget_table"}:
            task_model["primary_family"] = "management_accounting_review"
            task_model["family_candidates"] = [
                {
                    "family": "management_accounting_review",
                    "score": round(float(object_candidates[0].get("score", 0)), 2),
                    "confidence": object_candidates[0].get("confidence", "medium"),
                },
                *task_model.get("family_candidates", [])[:3],
            ]
    semantic_mapping = _semantic_mapping(frame)
    semantic_mapping = _sanitize_semantic_mapping(frame, semantic_mapping)
    ai_hints = codex_classify_business_context(
        _build_ai_classification_context(
            request=request,
            dataset_name=dataset_name,
            frame=frame,
            task_model=task_model,
            object_candidates=object_candidates,
            semantic_mapping=semantic_mapping,
            requirement_model=requirement_model,
        )
    )
    task_model = _merge_ai_task_model(task_model, ai_hints)
    object_candidates = _merge_ai_object_candidates(object_candidates, ai_hints)
    semantic_mapping = _merge_ai_semantic_mapping(semantic_mapping, ai_hints)
    semantic_mapping = _sanitize_semantic_mapping(frame, semantic_mapping)
    task_model, object_candidates = _merge_learned_route(task_model, object_candidates, learned_route)
    task_model, object_candidates = _promote_family_consistent_candidates(task_model, object_candidates, effective_request, dataset_name)
    task_model, object_candidates = _merge_learned_route(task_model, object_candidates, learned_route)
    task_model, object_candidates = _promote_family_consistent_candidates(task_model, object_candidates, effective_request, dataset_name)
    fusion_context = _detect_procurement_sales_fusion(
        task_model=task_model,
        object_candidates=object_candidates,
        request=effective_request,
        dataset_name=dataset_name,
        frame=frame,
    )
    explicit_procurement_text = _normalize_text(
        " ".join(
            [
                effective_request.user_requirement,
                effective_request.problem_to_solve,
                effective_request.core_purpose,
                effective_request.target_audience,
            ]
        )
    )
    explicit_procurement_intent = any(
        token in explicit_procurement_text
        for token in ["采销", "采购", "供应商", "seller", "supplier", "sku", "补货", "履约", "售后"]
    )
    frame_columns_lower = {str(column).lower() for column in frame.columns.astype(str).tolist()}
    has_procurement_sales_field_chain = (
        any(token in frame_columns_lower for token in {"seller", "supplier"})
        and any(token in frame_columns_lower for token in {"sku", "product", "category"})
        and any(token in frame_columns_lower for token in {"reviewscore", "review_score", "rating"})
        and any(token in frame_columns_lower for token in {"deliverydays", "delaydays", "islate", "estimateddeliverydate", "deliveredcustomerdate"})
    )
    if fusion_context.get("procurement_sales_management"):
        if (
            explicit_procurement_intent
            and has_procurement_sales_field_chain
            and task_model.get("primary_family") in {"sales_review", "mixed_business_review", "internet_ops_review", "management_accounting_review"}
        ):
            task_model["primary_family"] = "procurement_sales_review"
            task_model["family_candidates"] = [
                {
                    "family": "procurement_sales_review",
                    "score": round(max(float((task_model.get("family_candidates") or [{}])[0].get("score", 0) or 0), 8.4), 2),
                    "confidence": "high",
                },
                *[item for item in task_model.get("family_candidates", []) if item.get("family") != "procurement_sales_review"][:3],
            ][:4]
        elif not fusion_context.get("prefer_management_accounting"):
            task_model["primary_family"] = "procurement_sales_review"
            task_model["family_candidates"] = [
                {
                    "family": "procurement_sales_review",
                    "score": round(max(float((task_model.get("family_candidates") or [{}])[0].get("score", 0) or 0), 7.8), 2),
                    "confidence": "high" if fusion_context.get("procurement_hits", 0) >= 2 and fusion_context.get("sales_hits", 0) >= 2 else "medium",
                },
                *[item for item in task_model.get("family_candidates", []) if item.get("family") != "procurement_sales_review"][:3],
            ][:4]
        task_model["fusion_mode"] = "procurement_sales_management"
    enriched_frame, derived_metrics = _derived_metrics(frame, semantic_mapping)
    hypotheses = _rank_hypotheses(task_model, object_candidates, semantic_mapping)
    program = _analysis_program(task_model, object_candidates, semantic_mapping, derived_metrics, enriched_frame)
    critique = _self_critique(program, semantic_mapping)
    hard_fail = any(not item["passed"] for item in critique[:5])
    graceful_degradation = program["confidence"] == "low" or hard_fail or (not program["core_outcomes"] and not program["efficiency_metrics"])
    learned_top_family = ((learned_route.get("task_family_candidates") or [{}])[0]).get("family")
    learned_top_confidence = _confidence_value(((learned_route.get("task_family_candidates") or [{}])[0]).get("confidence", "low"))
    if graceful_degradation and learned_top_family == task_model["primary_family"] and learned_top_confidence >= 1:
        graceful_degradation = False
        if program["confidence"] == "low":
            program["confidence"] = "medium"
    if graceful_degradation and _strong_family_signal(frame, task_model["primary_family"]):
        graceful_degradation = False
        if program["confidence"] == "low":
            program["confidence"] = "medium"
    if (
        graceful_degradation
        and task_model["primary_family"] == "procurement_sales_review"
        and object_candidates
        and object_candidates[0]["object_type"] == "sales_transaction_panel"
        and program["core_outcomes"]
        and program["explanatory_slices"]
    ):
        graceful_degradation = False
        if program["confidence"] == "low":
            program["confidence"] = "medium"
    if graceful_degradation and task_model["primary_family"] != "foundation_review":
        program["body_modules"] = ["analysis_program", "quality", "semantic", "confidence_boundary"]
        program["appendix_modules"] = ["method_execution", "numeric", "category", "temporal"]
    return {
        "task_model": task_model,
        "object_candidates": object_candidates,
        "learned_route": learned_route,
        "semantic_mapping": semantic_mapping,
        "completed_inputs": completed_inputs,
        "requirement_model": requirement_model,
        "ai_hints": ai_hints,
        "hypotheses": hypotheses,
        "derived_metrics": derived_metrics,
        "experts": _expert_recall(task_model, object_candidates),
        "program": program,
        "graceful_degradation": graceful_degradation,
        "self_critique": critique,
        "frame": enriched_frame,
        "resolved_request_payload": effective_request.model_dump(),
        "lens": task_model["primary_family"],
        "fusion_context": fusion_context,
        "sheet_name": sheet_name,
        "reasoning_layers": [
            "requirement_completion",
            "business_classification",
            "workflow_blueprint",
            "semantic_analysis",
            "metric_interpretation",
            "method_review",
            "section_drafts",
            "evidence_digest",
            "insight_mining",
            "challenge",
            "business_synthesis",
            "decision_design",
            "final_polish",
            "judge_feedback",
        ],
    }
