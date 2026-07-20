"use client";

import {
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  FileText,
  FileUp,
  LoaderCircle,
  MessageSquareText,
  Paperclip,
  Plus,
  Save,
  RefreshCw,
  Send,
  Sparkles,
  Trash2,
  GripVertical,
} from "lucide-react";
import Link from "next/link";
import { type PointerEvent, type ReactNode, useEffect, useMemo, useRef, useState, useTransition } from "react";

import { DatasetPicker } from "@/components/dataset-picker";
import { apiRequest } from "@/lib/api";
import type {
  AnalysisType,
  BusinessBackgroundAsset,
  DatasetSummary,
  GenericTable,
  HistoricalReportTemplate,
  SmartReport,
  SmartReportJob,
  StatsResult,
} from "@/lib/types";

type DatasetListResponse = {
  datasets: DatasetSummary[];
};

type HistoricalTemplatesResponse = {
  templates: HistoricalReportTemplate[];
};

type BusinessBackgroundsResponse = {
  contexts: BusinessBackgroundAsset[];
};

type MultiTableMode = "single" | "merge" | "separate" | "combined";
type ReportStyle = "executive" | "deep_dive";

const REPORT_STYLES: Array<{ value: ReportStyle; label: string }> = [
  { value: "deep_dive", label: "深度版" },
  { value: "executive", label: "高管摘要版" },
];

const MULTI_TABLE_MODES: Array<{ value: MultiTableMode; label: string }> = [
  { value: "single", label: "单表分析" },
  { value: "merge", label: "合并分析" },
  { value: "separate", label: "分别生成" },
  { value: "combined", label: "组合分析" },
];

const STAT_METHODS: Array<{ value: AnalysisType; label: string }> = [
  { value: "correlation", label: "相关矩阵" },
  { value: "ols", label: "OLS 回归" },
  { value: "random_forest", label: "随机森林" },
  { value: "kmeans", label: "K-means 聚类" },
  { value: "pca", label: "PCA 降维" },
  { value: "normality", label: "正态性检验" },
];

type StylePresetOption = {
  description: string;
  label: string;
  value: string;
};

const STYLE_PRESETS: StylePresetOption[] = [
  { value: "chinese_finance_editorial", label: "中文财经内参", description: "管理层经营复盘、策略判断、质量评测和投研式深度报告。" },
  { value: "navy_white_premium", label: "深蓝白高级商务", description: "正式经营报告、管理层汇报。" },
  { value: "black_white_editorial", label: "黑白编辑部", description: "投资 memo、审计报告、正式长文。" },
  { value: "swiss_grid_consulting", label: "瑞士网格咨询风", description: "高密度、秩序感、咨询公司风格。" },
  { value: "boardroom_briefing", label: "董事会简报风", description: "结论先行、决策条、关键证据模块。" },
  { value: "strategy_matrix", label: "战略矩阵风", description: "象限、优先级、组合管理。" },
  { value: "financial_times_longform", label: "金融时报长文风", description: "长文分析、表格、脚注、克制高级。" },
  { value: "burgundy_premium_proposal", label: "酒红高端提案", description: "品牌、电商、高客单、投资人材料。" },
  { value: "green_growth_war_room", label: "绿色增长作战室", description: "增长、留存、效率改善。" },
  { value: "orange_gold_retail_command", label: "橙金零售指挥台", description: "零售、电商、商品、采销。" },
  { value: "graphite_finance_audit", label: "石墨财务审计", description: "财务、预算、风控、合规。" },
  { value: "cobalt_saas_ops_console", label: "钴蓝 SaaS 运营台", description: "互联网运营、漏斗、AARRR。" },
  { value: "minimalist_white_paper", label: "极简白皮书", description: "研究型报告、方法型说明。" },
  { value: "data_lab_monograph", label: "数据实验室专著", description: "统计、模型、R 工作流、严肃分析。" },
  { value: "executive_one_page_expanded", label: "高管一页纸扩展版", description: "结论先行、重点动作、少而重。" },
  { value: "analyst_atlas", label: "分析师图谱", description: "大量证据、附录、索引型报告。" },
  { value: "premium_magazine_report", label: "高级杂志式报告", description: "对外展示、商业故事、强视觉。" },
  { value: "enterprise_control_tower", label: "企业控制塔", description: "KPI、预警、动作闭环。" },
  { value: "category_management_manual", label: "类目管理手册", description: "电商类目、SKU、店铺、商品池。" },
  { value: "supply_chain_war_room", label: "供应链战情室", description: "履约、库存、路线、异常处理。" },
  { value: "procurement_reconciliation_review", label: "采购彩账复核", description: "供应商、用途、付款窗口、明细审计。" },
  { value: "internet_growth_console", label: "互联网增长控制台", description: "渠道、漏斗、留存、用户分层。" },
  { value: "media_buying_postmortem", label: "媒体投放复盘", description: "预算、ROI、素材、渠道效率。" },
  { value: "risk_committee_materials", label: "风险委员会材料", description: "异常、合规、边界、复核路径。" },
  { value: "fund_ic_memo", label: "基金 IC 备忘录", description: "投资判断、商业化、风险收益。" },
  { value: "founder_strategy_notes", label: "创始人战略笔记", description: "产品路线、商业路径、组织动作。" },
  { value: "art_school_editorial_blueprint", label: "艺术学院编辑蓝图", description: "高审美、深蓝白、留白、编辑感。" },
  { value: "gallery_whitespace", label: "画廊留白风", description: "少图高质、对象突出、版面安静。" },
  { value: "dense_table_compendium", label: "密集表格汇编", description: "完整版、审计长版、大量明细表。" },
  { value: "premium_visual_atlas", label: "高级图册型报告", description: "多图、多解释卡、视觉证据强。" },
  { value: "split_column_dossier", label: "左右分栏档案风", description: "证据与判断并列，适合复核。" },
  { value: "monochrome_accent_research", label: "单色强调研究报告", description: "克制、专业、少量强调色。" },
  { value: "warm_consumer_insight", label: "暖色消费者洞察", description: "消费、品牌、渠道、用户画像。" },
  { value: "cool_precision_operations", label: "冷色精密运营", description: "效率、监控、自动化、严谨控制。" },
  { value: "frontline_action_manual", label: "一线行动手册", description: "任务卡、负责人、检查点、30/60/90。" },
  { value: "thick_appendix_binder", label: "厚附录装订册", description: "统计表、源数据、方法和证据全部保留。" },
  { value: "dark_cover_white_body", label: "深色封面白色正文", description: "高级交付 PDF，封面强、正文清爽。" },
];

type PalettePresetOption = {
  colors: string[];
  id: string;
  label: string;
  source?: "custom" | "system";
};

type SavedPalettePreset = PalettePresetOption & {
  createdAt: number;
};

const MAX_PALETTE_COLORS = 12;
const CUSTOM_PALETTE_STORAGE_KEY = "smart-report-studio.custom-chart-palettes.v1";

const PALETTE_PRESETS: PalettePresetOption[] = [
  { id: "cn_editorial_ink", label: "中文内参墨色", colors: ["#17191c", "#214a4f", "#8f2f31", "#b08a57", "#5f737b", "#7b6d61"] },
  { id: "navy_gold_boardroom", label: "深蓝金商务", colors: ["#052b5f", "#0f4c81", "#f2c14e", "#2a9d8f", "#c2410c", "#94a3b8"] },
  { id: "ink_blue_slate", label: "墨蓝石板", colors: ["#111827", "#1d4ed8", "#38bdf8", "#0f766e", "#be123c", "#64748b"] },
  { id: "black_white_editorial", label: "黑白编辑部", colors: ["#111827", "#374151", "#6b7280", "#9ca3af", "#d1d5db"] },
  { id: "emerald_teal_growth", label: "祖母绿增长", colors: ["#064e3b", "#0f766e", "#14b8a6", "#5eead4", "#84cc16", "#64748b"] },
  { id: "amber_copper_retail", label: "琥珀零售", colors: ["#7c2d12", "#b45309", "#f59e0b", "#facc15", "#15803d", "#78716c"] },
  { id: "burgundy_luxury", label: "酒红奢华", colors: ["#4c0519", "#9f1239", "#d4af37", "#f8e7a2", "#166534", "#64748b"] },
  { id: "cobalt_cyan_saas", label: "钴蓝青 SaaS", colors: ["#1e3a8a", "#2563eb", "#06b6d4", "#10b981", "#f97316", "#64748b"] },
  { id: "graphite_mint_finance", label: "石墨薄荷", colors: ["#1f2937", "#475569", "#2dd4bf", "#059669", "#e11d48", "#94a3b8"] },
  { id: "terracotta_sand_consumer", label: "陶土沙消费者", colors: ["#7c2d12", "#c65d3b", "#f4d35e", "#2a9d8f", "#bc4749", "#9a8c7a"] },
  { id: "indigo_rose_media", label: "靛蓝玫瑰媒体", colors: ["#312e81", "#4f46e5", "#f472b6", "#22c55e", "#fb7185", "#64748b"] },
  { id: "forest_lime_ops", label: "森林青柠运营", colors: ["#14532d", "#166534", "#84cc16", "#22c55e", "#ea580c", "#64748b"] },
  { id: "steel_violet_product", label: "钢蓝紫产品", colors: ["#334155", "#7c3aed", "#a78bfa", "#14b8a6", "#f43f5e", "#94a3b8"] },
  { id: "navy_white_premium", label: "深蓝白高级", colors: ["#0f2a44", "#1f6f8b", "#d8a24a", "#1f7a5b", "#b4532a", "#64748b"] },
];

function asText(value: unknown) {
  if (value == null) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function formatValue(value: unknown) {
  if (value == null || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? new Intl.NumberFormat("zh-CN").format(value) : value.toFixed(4);
  }
  return asText(value);
}

function datasetLabel(dataset?: DatasetSummary) {
  if (!dataset) {
    return "选择已上传数据集";
  }
  return dataset.name || dataset.filename || dataset.dataset_id;
}

function loadingCount(value: unknown) {
  return value == null ? "..." : formatValue(value);
}

function delay(ms: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function mergeDatasetSummary(
  current: DatasetSummary | undefined,
  detail: DatasetSummary,
): DatasetSummary {
  return {
    ...(current || detail),
    ...detail,
    sheets: detail.sheets?.length ? detail.sheets : current?.sheets || [],
    numeric_columns: detail.numeric_columns?.length ? detail.numeric_columns : current?.numeric_columns || [],
    categorical_columns: detail.categorical_columns?.length ? detail.categorical_columns : current?.categorical_columns || [],
    datetime_columns: detail.datetime_columns?.length ? detail.datetime_columns : current?.datetime_columns || [],
    column_summaries: detail.column_summaries?.length ? detail.column_summaries : current?.column_summaries || [],
    sample_rows: detail.sample_rows?.length ? detail.sample_rows : current?.sample_rows || [],
    chart_bundle:
      detail.chart_bundle && Object.keys(detail.chart_bundle).length
        ? detail.chart_bundle
        : current?.chart_bundle || {},
  };
}

export function SmartReportStudio() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [templates, setTemplates] = useState<HistoricalReportTemplate[]>([]);
  const [contexts, setContexts] = useState<BusinessBackgroundAsset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [selectedSheets, setSelectedSheets] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [reportStyle, setReportStyle] = useState<ReportStyle>("deep_dive");
  const [multiTableMode, setMultiTableMode] = useState<MultiTableMode>("single");

  const [userRequirement, setUserRequirement] = useState("");
  const [problemToSolve, setProblemToSolve] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [corePurpose, setCorePurpose] = useState("");
  const [expectedResult, setExpectedResult] = useState("");
  const [keyConstraints, setKeyConstraints] = useState("");

  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [historicalName, setHistoricalName] = useState("");
  const [historicalText, setHistoricalText] = useState("");
  const [selectedContextId, setSelectedContextId] = useState("");
  const [businessBackgroundName, setBusinessBackgroundName] = useState("");
  const [businessBackgroundText, setBusinessBackgroundText] = useState("");

  const [useRWorkflow, setUseRWorkflow] = useState(true);
  const [industryResearchEnabled, setIndustryResearchEnabled] = useState(true);
  const [enablePremiumPipeline, setEnablePremiumPipeline] = useState(true);
  const [generateFullTableVersion, setGenerateFullTableVersion] = useState(false);
  const [enableGenericBusinessRuntime, setEnableGenericBusinessRuntime] = useState(true);
  const [premiumTarget, setPremiumTarget] = useState("analyst_appendix");
  const [stylePreset, setStylePreset] = useState("chinese_finance_editorial");
  const [palettePreset, setPalettePreset] = useState("cn_editorial_ink");
  const [paletteColors, setPaletteColors] = useState(PALETTE_PRESETS[0].colors);
  const [visualStyleText, setVisualStyleText] = useState("");
  const [requiredDetailDimensions, setRequiredDetailDimensions] = useState("");

  const [statMethod, setStatMethod] = useState<AnalysisType>("correlation");
  const [targetColumn, setTargetColumn] = useState("");
  const [groupColumn, setGroupColumn] = useState("");
  const [featureColumns, setFeatureColumns] = useState<string[]>([]);
  const [statsResult, setStatsResult] = useState<StatsResult | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);

  const [status, setStatus] = useState("上传一个数据集，系统会自动搭建分析流程。");
  const [error, setError] = useState<string | null>(null);
  const [reportJob, setReportJob] = useState<SmartReportJob | null>(null);
  const [report, setReport] = useState<SmartReport | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isStatsRunning, startStatsTransition] = useTransition();
  const isMounted = useRef(true);

  const selectedDataset = datasets.find((dataset) => dataset.dataset_id === selectedDatasetId);
  const sheetOptions = selectedDataset?.sheets || [];
  const activeSheet = selectedSheets[0] || selectedDataset?.active_sheet || sheetOptions[0]?.name || "";
  const numericColumns = selectedDataset?.numeric_columns || [];
  const categoricalColumns = selectedDataset?.categorical_columns || [];
  const allColumns = useMemo(
    () => (selectedDataset?.column_summaries || []).map((column) => column.name),
    [selectedDataset],
  );
  useEffect(() => {
    isMounted.current = true;
    void loadInitialResources();
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedDatasetId) {
      return;
    }
    void hydrateSelectedDataset(selectedDatasetId);
  }, [selectedDatasetId]);

  async function loadInitialResources() {
    try {
      setError(null);
      const [datasetPayload, templatePayload, contextPayload] = await Promise.all([
        apiRequest<DatasetListResponse>("/api/datasets?compact=true"),
        apiRequest<HistoricalTemplatesResponse>("/api/historical-reports"),
        apiRequest<BusinessBackgroundsResponse>("/api/business-backgrounds"),
      ]);
      if (!isMounted.current) {
        return;
      }
      const nextDatasets = datasetPayload.datasets || [];
      setDatasets(nextDatasets);
      setTemplates(templatePayload.templates || []);
      setContexts(contextPayload.contexts || []);
      if (!selectedDatasetId && nextDatasets[0]) {
        selectDataset(nextDatasets[0].dataset_id, nextDatasets);
      }
      setStatus("资源已加载。可以直接上传数据、填写业务背景，或选择历史报告做仿写。");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "初始化资源失败。");
      setStatus("初始化资源失败，请确认后端服务已启动。");
    }
  }

  function selectDataset(datasetId: string, source = datasets) {
    const nextDataset = source.find((dataset) => dataset.dataset_id === datasetId);
    setSelectedDatasetId(datasetId);
    const firstSheet = nextDataset?.active_sheet || nextDataset?.sheets?.[0]?.name || "";
    setSelectedSheets(firstSheet ? [firstSheet] : []);
    setFeatureColumns([]);
    setTargetColumn("");
    setGroupColumn("");
  }

  function toggleSheet(sheetName: string) {
    setSelectedSheets((current) => {
      if (multiTableMode === "single") {
        return [sheetName];
      }
      return current.includes(sheetName)
        ? current.filter((item) => item !== sheetName)
        : [...current, sheetName];
    });
  }

  function toggleFeatureColumn(column: string) {
    setFeatureColumns((current) =>
      current.includes(column)
        ? current.filter((item) => item !== column)
        : [...current, column].slice(-8),
    );
  }

  async function refreshDatasets(preselectId?: string) {
    const payload = await apiRequest<DatasetListResponse>("/api/datasets?compact=true");
    const nextDatasets = payload.datasets || [];
    setDatasets(nextDatasets);
    const nextSelected =
      nextDatasets.find((dataset) => dataset.dataset_id === preselectId) ||
      nextDatasets.find((dataset) => dataset.dataset_id === selectedDatasetId) ||
      nextDatasets[0];
    if (nextSelected) {
      selectDataset(nextSelected.dataset_id, nextDatasets);
    }
  }

  async function hydrateSelectedDataset(datasetId: string) {
    try {
      const detail = await apiRequest<DatasetSummary>(`/api/datasets/${datasetId}?summary=true`, {
        timeoutMs: 30000,
      });
      if (!isMounted.current) {
        return;
      }
      setDatasets((current) =>
        current.map((dataset) =>
          dataset.dataset_id === datasetId ? mergeDatasetSummary(dataset, detail) : dataset,
        ),
      );
    } catch {
      // Keep the compact list usable even if the detail request fails.
    }
  }

  async function refreshTemplates(preselectId?: string) {
    const payload = await apiRequest<HistoricalTemplatesResponse>("/api/historical-reports");
    const nextTemplates = payload.templates || [];
    setTemplates(nextTemplates);
    if (preselectId) {
      setSelectedTemplateId(preselectId);
    }
  }

  async function refreshContexts(preselectId?: string) {
    const payload = await apiRequest<BusinessBackgroundsResponse>("/api/business-backgrounds");
    const nextContexts = payload.contexts || [];
    setContexts(nextContexts);
    if (preselectId) {
      setSelectedContextId(preselectId);
    }
  }

  async function handleUploadDataset() {
    if (!selectedFile) {
      setError("请先选择一个 Excel、CSV、TSV 或 Stata 数据文件。");
      return;
    }
    try {
      setIsUploading(true);
      setError(null);
      setStatus("正在上传数据集并生成首批预览...");
      const form = new FormData();
      form.append("file", selectedFile);
      const uploaded = await apiRequest<DatasetSummary>("/api/datasets/upload", {
        method: "POST",
        body: form,
        timeoutMs: 180000,
      });
      await refreshDatasets(uploaded.dataset_id);
      setStatus(`数据集 ${uploaded.name || uploaded.filename} 已就绪，现在可以生成报告。`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "上传失败。");
      setStatus("上传失败，请检查文件格式。");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleHistoricalUpload(file: File) {
    try {
      setError(null);
      setStatus(`正在上传历史模板 ${file.name} 并提取正文...`);
      const form = new FormData();
      form.append("file", file);
      const uploaded = await apiRequest<HistoricalReportTemplate>("/api/historical-reports/upload", {
        method: "POST",
        body: form,
        timeoutMs: 180000,
      });
      await refreshTemplates(uploaded.template_id);
      setHistoricalName(uploaded.name || uploaded.filename);
      setHistoricalText(uploaded.extracted_text || "");
      setStatus(`历史模板 ${uploaded.filename} 已就绪，可用于报告仿写。`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "历史模板上传失败。");
    }
  }

  async function handleBusinessBackgroundUpload(file: File) {
    try {
      setError(null);
      setStatus(`正在上传业务背景 ${file.name} 并提取上下文...`);
      const form = new FormData();
      form.append("file", file);
      const uploaded = await apiRequest<BusinessBackgroundAsset>("/api/business-backgrounds/upload", {
        method: "POST",
        body: form,
        timeoutMs: 180000,
      });
      await refreshContexts(uploaded.context_id);
      setBusinessBackgroundName(uploaded.name || uploaded.filename);
      setBusinessBackgroundText(uploaded.extracted_text || "");
      setStatus(`业务背景 ${uploaded.filename} 已就绪，系统会将其作为独立业务上下文使用。`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "业务背景上传失败。");
    }
  }

  async function handleTemplateSelect(templateId: string) {
    setSelectedTemplateId(templateId);
    if (!templateId) {
      return;
    }
    try {
      const loaded = await apiRequest<HistoricalReportTemplate>(`/api/historical-reports/${templateId}`, {
        timeoutMs: 30000,
      });
      setHistoricalName(loaded.name || loaded.filename);
      setHistoricalText(loaded.extracted_text || loaded.preview || "");
      setStatus(`已载入历史模板 ${loaded.filename}，现在可以直接生成仿写报告。`);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "历史模板载入失败。");
    }
  }

  async function handleContextSelect(contextId: string) {
    setSelectedContextId(contextId);
    if (!contextId) {
      return;
    }
    try {
      const loaded = await apiRequest<BusinessBackgroundAsset>(`/api/business-backgrounds/${contextId}`, {
        timeoutMs: 30000,
      });
      setBusinessBackgroundName(loaded.name || loaded.filename);
      setBusinessBackgroundText(loaded.extracted_text || loaded.preview || "");
      setStatus(`已载入业务背景 ${loaded.filename}，系统会将其作为独立业务上下文使用。`);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "业务背景载入失败。");
    }
  }

  async function handleGenerateReport() {
    if (!selectedDataset) {
      setError("请先选择一个已上传的数据集。");
      return;
    }
    const sheets = selectedSheets.length ? selectedSheets : activeSheet ? [activeSheet] : [];
    if (!sheets.length) {
      setError("请先选择至少一个工作表。");
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);
      setReportJob(null);
      setReport(null);
      setStatus("正在创建报告任务...");
      const payload = {
        sheet_name: sheets[0],
        selected_sheets: sheets,
        multi_table_mode: multiTableMode,
        report_style: reportStyle,
        report_language: "zh-CN",
        user_requirement: userRequirement,
        problem_to_solve: problemToSolve,
        target_audience: targetAudience,
        core_purpose: corePurpose,
        expected_result: expectedResult,
        key_constraints: keyConstraints,
        historical_report_template_id: selectedTemplateId,
        historical_report_text: historicalText,
        historical_report_name: historicalName,
        business_background_text: businessBackgroundText,
        business_background_name: businessBackgroundName,
        use_r_workflow: useRWorkflow,
        industry_research_standalone_enabled: industryResearchEnabled,
        enable_premium_pipeline: enablePremiumPipeline,
        generate_full_table_version: generateFullTableVersion,
        enable_generic_business_runtime: enableGenericBusinessRuntime,
        premium_target: premiumTarget,
        premium_style_preset: stylePreset,
        chart_palette_preset: palettePreset,
        chart_palette_colors: paletteColors,
        visual_style_text: visualStyleText,
        required_detail_dimensions_text: requiredDetailDimensions,
      };
      const created = await apiRequest<SmartReportJob>(`/api/datasets/${selectedDataset.dataset_id}/smart-report-jobs`, {
        method: "POST",
        body: JSON.stringify(payload),
        timeoutMs: 60000,
      });
      setReportJob(created);
      setStatus(`${created.current_stage_title || "报告任务已创建"} / ${created.progress_percent || 0}%`);
      await pollReportJob(created.job_id);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "报告生成失败。");
      setStatus("报告生成失败，请查看错误信息。");
    } finally {
      setIsGenerating(false);
    }
  }

  async function pollReportJob(jobId: string) {
    for (let attempt = 0; attempt < 360; attempt += 1) {
      if (!isMounted.current) {
        return;
      }
      const next = await apiRequest<SmartReportJob>(`/api/report-jobs/${jobId}`, {
        timeoutMs: 20000,
      });
      setReportJob(next);
      setStatus(`${next.current_stage_title || next.status} / ${next.progress_percent || 0}%`);
      if (next.status === "completed") {
        setReport(next.result || null);
        setStatus("报告已生成。下方会展示结构化结论、历史风格改写和导出物。");
        return;
      }
      if (next.status === "failed") {
        throw new Error(next.error || "报告任务失败。");
      }
      await delay(2500);
    }
    throw new Error("报告任务仍在运行，轮询已超时。");
  }

  function handleRunStats() {
    if (!selectedDataset) {
      setStatsError("请先选择一个数据集。");
      return;
    }
    setStatsError(null);
    setStatsResult(null);
    startStatsTransition(() => {
      void (async () => {
        try {
          const result = await apiRequest<StatsResult>("/api/statistics/run", {
            method: "POST",
            body: JSON.stringify({
              dataset_id: selectedDataset.dataset_id,
              active_sheet: activeSheet,
              analysis_type: statMethod,
              target: targetColumn || null,
              features: featureColumns,
              group_column: groupColumn || null,
            }),
            timeoutMs: 120000,
          });
          setStatsResult(result);
          setStatus(`统计分析已完成：${result.title}`);
        } catch (runError) {
          setStatsError(runError instanceof Error ? runError.message : "统计分析失败。");
        }
      })();
    });
  }

  return (
    <section className="elevated-panel p-6 md:p-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="section-header">
          <div className="section-badge bg-[rgba(103,78,44,0.34)]">
            <BrainCircuit size={18} />
          </div>
          <div>
            <p className="section-kicker">智能报告工作台</p>
            <h2 className="section-title">上传数据，直接生成一份像样的深度分析报告</h2>
          </div>
        </div>
        <Link className="surface-chip relative z-10 inline-flex cursor-pointer items-center gap-2" href="/revision">
          <MessageSquareText size={15} />
          后续改造
        </Link>
      </div>

      <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--muted)]">
        当前版本会自动做数据质量审计、结构理解、相关与预测信号扫描，并把结果组织成可审阅、可导出的报告工作流。
      </p>

      <div className="mt-6 grid gap-6 2xl:grid-cols-[minmax(560px,0.96fr)_minmax(0,1.04fr)]">
        <div className="space-y-5">
          <div className="runtime-status-card rounded-[24px] p-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/6 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-[var(--muted)]">
              <Sparkles size={14} />
              报告流程
            </div>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)]">{status}</p>
            {error ? (
              <div className="mt-3 rounded-[16px] border border-red-300/20 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                {error}
              </div>
            ) : null}
          </div>

          <AccordionPanel
            defaultOpen={false}
            description="低频调试信息默认收起；需要时可以刷新当前数据、历史模板和业务背景。"
            eyebrow="Runtime Ledger"
            title="运行记忆与链路学习"
          >
            <div className="flex flex-wrap gap-3">
              <button className="surface-chip" onClick={() => void loadInitialResources()} type="button">
                <RefreshCw size={14} />
                刷新资源
              </button>
              <StatusPill label="数据集" value={`${datasets.length} 个`} />
              <StatusPill label="历史模板" value={`${templates.length} 个`} />
              <StatusPill label="业务背景" value={`${contexts.length} 个`} />
            </div>
          </AccordionPanel>

          <AccordionPanel
            defaultOpen
            description="先选数据、表和报告风格；低频上下文配置位于下方折叠区。"
            eyebrow="Data Source"
            title="数据入口与工作表"
          >
            <label className="upload-box min-h-[96px] bg-white/[0.035] p-4">
              <input
                accept=".xlsx,.xls,.csv,.tsv,.dta"
                className="hidden"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                type="file"
              />
              <FileUp size={22} />
              <div>
                <p className="text-sm font-semibold text-[var(--text-strong)]">
                  {selectedFile?.name || "选择待分析的数据文件"}
                </p>
                <p className="mt-1 text-sm text-[var(--muted)]">支持 `.xlsx` / `.csv` / `.tsv` / `.dta`</p>
              </div>
            </label>

            <div className="grid gap-4 xl:grid-cols-2">
              <Field label="数据集">
                <DatasetPicker
                  datasets={datasets}
                  onChange={(value) => selectDataset(value)}
                  selectedDataset={selectedDataset}
                  value={selectedDatasetId}
                />
              </Field>
              <Field label="报告风格">
                <SelectInput
                  onChange={(value) => setReportStyle(value as ReportStyle)}
                  options={REPORT_STYLES}
                  value={reportStyle}
                />
              </Field>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <Field label="多表分析模式">
                <SelectInput
                  onChange={(value) => {
                    const nextMode = value as MultiTableMode;
                    setMultiTableMode(nextMode);
                    if (nextMode === "single" && selectedSheets.length > 1) {
                      setSelectedSheets([selectedSheets[0]]);
                    }
                  }}
                  options={MULTI_TABLE_MODES}
                  value={multiTableMode}
                />
              </Field>
              <div className="block space-y-2">
                <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">工作表选择</span>
                <div className="min-h-[54px] rounded-[18px] border border-white/10 bg-white/4 p-3">
                  {sheetOptions.length ? (
                    <div className="flex flex-wrap gap-2">
                      {sheetOptions.map((sheet) => {
                        const selected = selectedSheets.includes(sheet.name);
                        return (
                          <button
                            className={`surface-chip ${
                              selected ? "border-[rgba(255,163,92,0.55)] bg-[rgba(255,163,92,0.16)] text-[var(--text-strong)]" : ""
                            }`}
                            key={sheet.name}
                            onClick={() => toggleSheet(sheet.name)}
                            type="button"
                          >
                            {sheet.name} ({sheet.rows})
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-[var(--muted)]">当前数据集暂未提供可选工作表。导入包含工作表的数据后即可选择。</p>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-1">
              <button className="primary-button" disabled={!selectedFile || isUploading} onClick={handleUploadDataset} type="button">
                {isUploading ? <LoaderCircle className="mr-2 animate-spin" size={16} /> : null}
                上传数据
              </button>
              <button
                className="primary-button"
                disabled={!selectedDataset || isGenerating}
                onClick={handleGenerateReport}
                type="button"
              >
                {isGenerating ? <LoaderCircle className="mr-2 animate-spin" size={16} /> : <Send className="mr-2" size={16} />}
                {isGenerating ? `生成中 ${reportJob?.progress_percent ?? 0}%` : "生成智能报告"}
              </button>
            </div>
            <p className="text-sm leading-7 text-[var(--muted)]">上传成功后，系统会自动选中新数据集，你可以直接开始生成报告。</p>
          </AccordionPanel>

          <AccordionPanel
            defaultOpen
            description="Run governed statistics before report generation. Arbitrary code execution is disabled in the public release."
            eyebrow="分析实验室"
            title="统计分析"
          >
            <div className="grid gap-5 xl:grid-cols-2">
              <div className="rounded-[20px] border border-white/10 bg-black/10 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">快速统计</p>
                    <h4 className="mt-2 text-lg font-semibold text-[var(--text-strong)]">快速统计分析</h4>
                  </div>
                  <span className="surface-chip">{activeSheet || "未选择工作表"}</span>
                </div>

                <div className="mt-4 grid gap-4">
                  <Field label="分析类型">
                    <SelectInput
                      onChange={(value) => setStatMethod(value as AnalysisType)}
                      options={STAT_METHODS}
                      value={statMethod}
                    />
                  </Field>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Field label="目标字段">
                      <SelectInput
                        onChange={setTargetColumn}
                        options={allColumns.map((column) => ({ label: column, value: column }))}
                        placeholder="选择目标字段"
                        value={targetColumn}
                      />
                    </Field>
                    <Field label="分组字段">
                      <SelectInput
                        onChange={setGroupColumn}
                        options={categoricalColumns.map((column) => ({ label: column, value: column }))}
                        placeholder="可选：分组字段"
                        value={groupColumn}
                      />
                    </Field>
                  </div>
                  <Field label="特征字段">
                    <div className="min-h-[54px] rounded-[18px] border border-white/10 bg-white/4 p-3">
                      {numericColumns.length ? (
                        <div className="flex flex-wrap gap-2">
                          {numericColumns.map((column) => {
                            const selected = featureColumns.includes(column);
                            return (
                              <button
                                className={`surface-chip ${
                                  selected ? "border-[rgba(116,208,217,0.55)] bg-[rgba(116,208,217,0.16)] text-[var(--text-strong)]" : ""
                                }`}
                                key={column}
                                onClick={() => toggleFeatureColumn(column)}
                                type="button"
                              >
                                {column}
                              </button>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-sm text-[var(--muted)]">当前数据集中没有可用数值字段。</p>
                      )}
                    </div>
                  </Field>
                  <button className="primary-button" disabled={!selectedDataset || isStatsRunning} onClick={handleRunStats} type="button">
                    {isStatsRunning ? <LoaderCircle className="mr-2 animate-spin" size={16} /> : null}
                    运行统计分析
                  </button>
                  {statsError ? <ErrorBox>{statsError}</ErrorBox> : null}
                  {statsResult ? <StatsResultCard result={statsResult} /> : null}
                </div>
              </div>

              <div className="rounded-[20px] border border-white/10 bg-black/10 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Code Execution</p>
                    <h4 className="mt-2 text-lg font-semibold text-[var(--text-strong)]">Server-managed execution</h4>
                  </div>
                  <span className="surface-chip">Disabled in release</span>
                </div>
                <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
                  This public build does not expose arbitrary Python or R execution. Use the governed statistics workflow or formal report generation instead.
                </p>
              </div>
            </div>
          </AccordionPanel>

          <AccordionPanel
            defaultOpen
            description="这些字段会直接进入生成请求，帮助报告从“数据总结”变成“业务判断”。"
            eyebrow="报告简报"
            title="报告需求与业务目标"
          >
            <Field label="你想让报告回答什么问题">
              <textarea
                className="field-input min-h-[120px] resize-y"
                onChange={(event) => setUserRequirement(event.target.value)}
                placeholder="例如：解释销售下滑原因，判断哪些渠道/区域值得加预算，并给出下一季度动作优先级。"
                value={userRequirement}
              />
            </Field>
            <div className="grid gap-4 xl:grid-cols-2">
              <Field label="要解决的问题">
                <input
                  className="field-input"
                  onChange={(event) => setProblemToSolve(event.target.value)}
                  placeholder="例如：预算投放效率下降、区域增长分化"
                  value={problemToSolve}
                />
              </Field>
              <Field label="目标读者">
                <input
                  className="field-input"
                  onChange={(event) => setTargetAudience(event.target.value)}
                  placeholder="例如：管理层、市场负责人、渠道团队"
                  value={targetAudience}
                />
              </Field>
              <Field label="核心用途">
                <input
                  className="field-input"
                  onChange={(event) => setCorePurpose(event.target.value)}
                  placeholder="例如：经营复盘、预算决策、策略汇报"
                  value={corePurpose}
                />
              </Field>
              <Field label="期望结果">
                <input
                  className="field-input"
                  onChange={(event) => setExpectedResult(event.target.value)}
                  placeholder="例如：能直接放进月度经营会"
                  value={expectedResult}
                />
              </Field>
            </div>
            <Field label="关键约束">
              <textarea
                className="field-input min-h-[110px] resize-y"
                onChange={(event) => setKeyConstraints(event.target.value)}
                placeholder="例如：以已提供数据为依据；保留关键明细；使用中文；图表对应管理动作。"
                value={keyConstraints}
              />
            </Field>
          </AccordionPanel>

          <AccordionPanel
            defaultOpen
            description="历史报告模仿材料和业务背景属于增强上下文；这里恢复为首页可见输入区。"
            eyebrow="Context Assets"
            title="历史报告模仿与业务背景"
          >
            <div className="grid gap-4 xl:grid-cols-2">
              <Field label="历史文档名称">
                <input
                  className="field-input"
                  onChange={(event) => setHistoricalName(event.target.value)}
                  placeholder="例如：2025Q4 华东市场经营复盘"
                  type="text"
                  value={historicalName}
                />
              </Field>
              <label className="upload-box bg-white/[0.035] p-4">
                <input
                  accept=".md,.txt,.html,.htm,.pdf,.docx"
                  className="hidden"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      void handleHistoricalUpload(file);
                    }
                  }}
                  type="file"
                />
                <Paperclip size={22} />
                <div>
                  <p className="text-sm font-semibold text-[var(--text-strong)]">上传历史报告</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">支持 `.md` / `.txt` / `.html` / `.pdf` / `.docx`</p>
                  {historicalName ? <p className="mt-2 text-sm text-[var(--text-strong)]">当前历史文档：{historicalName}</p> : null}
                </div>
              </label>
            </div>
            <Field label="已上传历史报告">
              <SelectInput
                onChange={(value) => void handleTemplateSelect(value)}
                options={templates.map((template) => ({
                  label: `${template.name || template.filename} (${template.word_count || 0} words)`,
                  value: template.template_id,
                }))}
                placeholder="选择已上传的历史文档"
                value={selectedTemplateId}
              />
            </Field>
            <Field label="历史报告正文或模板文本">
              <textarea
                className="field-input min-h-[150px] resize-y"
                onChange={(event) => setHistoricalText(event.target.value)}
                placeholder="把历史报告正文贴进来，Codex 会学习它的结构和汇报风格，再按新数据重写一版。"
                value={historicalText}
              />
            </Field>

            <div className="grid gap-4 xl:grid-cols-2">
              <Field label="业务背景名称">
                <input
                  className="field-input"
                  onChange={(event) => setBusinessBackgroundName(event.target.value)}
                  placeholder="例如：品牌策略、渠道背景、经营约束、目标受众"
                  type="text"
                  value={businessBackgroundName}
                />
              </Field>
              <label className="upload-box bg-white/[0.035] p-4">
                <input
                  accept=".md,.txt,.html,.htm,.pdf,.docx,.xlsx,.csv,.tsv"
                  className="hidden"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      void handleBusinessBackgroundUpload(file);
                    }
                  }}
                  type="file"
                />
                <FileText size={22} />
                <div>
                  <p className="text-sm font-semibold text-[var(--text-strong)]">上传业务背景</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">支持 `.pdf` / `.docx` / `.xlsx` / `.csv`</p>
                  {businessBackgroundName ? (
                    <p className="mt-2 text-sm text-[var(--text-strong)]">当前业务背景：{businessBackgroundName}</p>
                  ) : null}
                </div>
              </label>
            </div>
            <Field label="已上传业务背景">
              <SelectInput
                onChange={(value) => void handleContextSelect(value)}
                options={contexts.map((context) => ({
                  label: `${context.name || context.filename} (${context.source_type || "context"})`,
                  value: context.context_id,
                }))}
                placeholder="选择已上传的业务背景"
                value={selectedContextId}
              />
            </Field>
            <Field label="业务背景正文或摘要">
              <textarea
                className="field-input min-h-[140px] resize-y"
                onChange={(event) => setBusinessBackgroundText(event.target.value)}
                placeholder="可以粘贴业务背景、策略说明、渠道规则或研究目标。"
                value={businessBackgroundText}
              />
            </Field>
          </AccordionPanel>

          <AccordionPanel
            defaultOpen={false}
            description="高级生成链路和版式偏好，默认沿用旧版中文工作台参数。"
            eyebrow="Delivery Design"
            title="高阶经营 PDF 与版式偏好"
          >
            <div className="grid gap-3 md:grid-cols-3">
              <div className="soft-panel rounded-[22px] p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">入口</p>
                <p className="mt-2 text-sm leading-7 text-[var(--muted)]">单个执行入口已经恢复在首页按钮和 `/analysis` 独立工作台里。</p>
                <Link className="surface-chip mt-3 inline-flex" href="/analysis">
                  打开单个执行
                </Link>
              </div>
              <div className="soft-panel rounded-[22px] p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">预设</p>
                <p className="mt-2 text-sm leading-7 text-[var(--muted)]">报告风格预设仍然可选，保留中文财经内参、董事会简报等完整选项。</p>
              </div>
              <div className="soft-panel rounded-[22px] p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">色卡</p>
                <p className="mt-2 text-sm leading-7 text-[var(--muted)]">图表色盘仍然可点选，恢复到原先的成组色板交互。</p>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <ToggleField
                checked={useRWorkflow}
                description="让后端尝试生成独立 R 工作流和可复核统计产物。"
                onChange={setUseRWorkflow}
                title="启用 R 工作流"
              />
              <ToggleField
                checked={industryResearchEnabled}
                description="生成行业研究型补充材料。"
                onChange={setIndustryResearchEnabled}
                title="启用行业研究"
              />
              <ToggleField
                checked={enablePremiumPipeline}
                description="启动更完整的高级 PDF / 长报告工程链。"
                onChange={setEnablePremiumPipeline}
                title="启用高级交付链"
              />
              <ToggleField
                checked={enableGenericBusinessRuntime}
                description="启用通用业务运行时，让报告更贴近经营诊断。"
                onChange={setEnableGenericBusinessRuntime}
                title="启用通用业务 runtime"
              />
              <ToggleField
                checked={generateFullTableVersion}
                description="需要完整明细表时打开，生成会更重。"
                onChange={setGenerateFullTableVersion}
                title="生成完整表格版"
              />
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <Field label="交付目标">
                <input className="field-input" onChange={(event) => setPremiumTarget(event.target.value)} value={premiumTarget} />
              </Field>
              <Field label="报告风格预设">
                <PresetSelectInput
                  onChange={setStylePreset}
                  options={STYLE_PRESETS}
                  value={stylePreset}
                />
              </Field>
            </div>

            <PaletteEditor
              colors={paletteColors}
              onColorsChange={setPaletteColors}
              onPresetChange={setPalettePreset}
              presetId={palettePreset}
              presets={PALETTE_PRESETS}
            />

            <Field label="视觉风格说明">
              <textarea
                className="field-input min-h-[100px] resize-y"
                onChange={(event) => setVisualStyleText(event.target.value)}
                placeholder="例如：中文财经内参风，结论先行，图表旁要有业务解释，正文保持克制高级。"
                value={visualStyleText}
              />
            </Field>
            <Field label="必须展开的明细类目">
              <textarea
                className="field-input min-h-[100px] resize-y"
                onChange={(event) => setRequiredDetailDimensions(event.target.value)}
                placeholder="例如：媒体、终端、品牌、省份、点位、SKU、类目、区域。"
                value={requiredDetailDimensions}
              />
            </Field>
          </AccordionPanel>
        </div>

        <ReportPanel job={reportJob} report={report} selectedDataset={selectedDataset} />
      </div>
    </section>
  );
}

function ReportPanel({
  job,
  report,
  selectedDataset,
}: {
  job: SmartReportJob | null;
  report: SmartReport | null;
  selectedDataset?: DatasetSummary;
}) {
  if (!report) {
    return (
      <div className="space-y-4">
        {job ? <JobProgressCard job={job} /> : null}
        <div className="soft-panel rounded-[28px] p-6">
          <p className="text-sm leading-7 text-[var(--muted)]">
            报告区还没有内容。先上传一份数据，再点击“生成智能报告”，这里会按章节展开结构化结论、历史风格改写和导出物。
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <MiniMetric label="当前数据" value={datasetLabel(selectedDataset)} />
            <MiniMetric label="行数" value={loadingCount(selectedDataset?.row_count)} />
            <MiniMetric label="字段数" value={loadingCount(selectedDataset?.column_count)} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {job ? <JobProgressCard job={job} /> : null}
      <div className="soft-panel rounded-[28px] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">报告产物</p>
            <h3 className="mt-2 text-2xl font-semibold text-[var(--text-strong)]">{report.title}</h3>
            <p className="mt-2 text-sm text-[var(--muted)]">
              {report.dataset_name} / {report.sheet_name} / {new Date(report.generated_at).toLocaleString("zh-CN")}
            </p>
          </div>
          {report.main_downloadable?.path ? (
            <a className="primary-button" href={report.main_downloadable.path} rel="noreferrer" target="_blank">
              <FileText className="mr-2" size={16} />
              打开主文件
            </a>
          ) : null}
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(report.key_metrics || []).map((metric) => (
            <MiniMetric detail={metric.detail} key={metric.label} label={metric.label} value={formatValue(metric.value)} />
          ))}
        </div>

        <div className="mt-5 space-y-2">
          {(report.executive_summary || []).map((item) => (
            <div className="rounded-[18px] border border-white/8 bg-white/4 px-4 py-3 text-sm leading-7 text-[var(--muted)]" key={item}>
              {item}
            </div>
          ))}
        </div>
      </div>

      {report.codex_layer ? (
        <div className="soft-panel rounded-[28px] p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Codex 推理层</p>
              <h3 className="mt-2 text-xl font-semibold text-[var(--text-strong)]">{report.codex_layer.board_title}</h3>
            </div>
            <span className="surface-chip">
              {report.codex_layer.provider_label || "OpenAI Codex API"} / {report.codex_layer.model || "gpt-5.4"}
            </span>
          </div>
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <ListCard items={report.codex_layer.executive_summary_rewrite} title="管理层摘要改写" />
            <ListCard items={report.codex_layer.strategic_recommendations} title="行动建议" />
            <ListCard items={report.codex_layer.risk_flags} title="风险提示" />
            <ListCard items={report.codex_layer.next_questions} title="下一步问题" />
          </div>
        </div>
      ) : null}

      {report.historical_report_adaptation ? (
        <div className="soft-panel rounded-[28px] p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">历史风格改写</p>
              <h3 className="mt-2 text-xl font-semibold text-[var(--text-strong)]">
                {report.historical_report_adaptation.title}
              </h3>
            </div>
            <span className="surface-chip">
              {report.historical_report_adaptation.provider_label || "OpenAI Codex API"} /{" "}
              {report.historical_report_adaptation.model || "gpt-5.4"}
            </span>
          </div>
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <ListCard items={report.historical_report_adaptation.template_signals} title="模板信号" />
            <ListCard items={report.historical_report_adaptation.adaptation_notes} title="改写说明" />
          </div>
          {report.historical_style_cli_final_output ? (
            <div className="mt-5 grid grid-cols-1 gap-3 rounded-[18px] border border-white/8 bg-white/4 p-4 text-sm text-[var(--muted)] sm:grid-cols-2 xl:grid-cols-3">
              <MiniMetric label="报告家族" value={report.historical_style_cli_final_output.historical_report_family || "未知"} />
              <MiniMetric label="计划页数" value={formatValue(report.historical_style_cli_final_output.planned_page_count)} />
              <MiniMetric label="渲染页数" value={formatValue(report.historical_style_cli_final_output.rendered_page_count)} />
              <MiniMetric label="图表资产" value={formatValue(report.historical_style_cli_final_output.chart_asset_count)} />
              <MiniMetric label="表格资产" value={formatValue(report.historical_style_cli_final_output.table_asset_count)} />
              {report.historical_style_cli_final_output.main_artifact_url ? (
                <a
                  className="rounded-xl bg-black/10 p-3 text-sm font-semibold text-[var(--accent)] underline-offset-4 hover:underline"
                  href={report.historical_style_cli_final_output.main_artifact_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  打开仿写 PDF
                </a>
              ) : null}
            </div>
          ) : null}
          <div className="mt-5 rounded-[18px] border border-white/8 bg-white/4 px-4 py-4">
            <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">仿写预览</p>
            <pre className="mt-3 max-h-[520px] overflow-auto whitespace-pre-wrap text-sm leading-7 text-[var(--text-strong)]">
              {report.historical_report_adaptation.adapted_report_markdown}
            </pre>
          </div>
        </div>
      ) : null}

      {(report.downloadables || []).length ? (
        <div className="soft-panel rounded-[28px] p-5">
          <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">导出物</p>
          <div className="mt-4 grid gap-3 xl:grid-cols-2">
            {report.downloadables.map((item) => (
              <a
                className="rounded-[16px] border border-white/8 bg-white/4 px-4 py-3 transition-colors hover:border-white/20 hover:bg-white/8"
                href={item.path}
                key={`${item.name}-${item.path}`}
                rel="noreferrer"
                target="_blank"
              >
                <p className="break-words text-sm font-semibold text-[var(--text-strong)]">
                  {item.name} {item.is_main ? "（主文件）" : ""}
                </p>
                <p className="mt-2 text-sm leading-7 text-[var(--muted)]">{item.purpose}</p>
              </a>
            ))}
          </div>
        </div>
      ) : null}

      {(report.sections || []).map((section) => (
        <article className="soft-panel rounded-[28px] p-5" key={section.id}>
          <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">报告章节</p>
          <h3 className="mt-2 text-xl font-semibold text-[var(--text-strong)]">{section.title}</h3>
          <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{section.summary}</p>
          <div className="mt-4 space-y-2">
            {(section.bullets || []).map((bullet) => (
              <div className="rounded-[16px] border border-white/8 bg-white/4 px-4 py-3 text-sm leading-7 text-[var(--muted)]" key={bullet}>
                {bullet}
              </div>
            ))}
          </div>
          {(section.tables || []).length ? (
            <div className="mt-5 space-y-4">
              {section.tables.map((table) => (
                <DataTable key={table.title || table.columns.join("-")} table={table} />
              ))}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function JobProgressCard({ job }: { job: SmartReportJob }) {
  const stageEvents = job.stage_events || [];

  return (
    <div className="soft-panel rounded-[28px] p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">报告任务</p>
          <h3 className="mt-2 text-lg font-semibold text-[var(--text-strong)]">{job.current_stage_title || job.status}</h3>
          <p className="mt-2 text-sm leading-7 text-[var(--muted)]">{job.current_stage_detail || "等待任务状态更新。"}</p>
        </div>
        <span className="surface-chip">
          {job.status} / {job.progress_percent || 0}%
        </span>
      </div>
      <div className="mt-4 h-3 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,#ff9c61,#74d0d9)] transition-all duration-500"
          style={{ width: `${Math.max(2, Math.min(100, job.progress_percent || 0))}%` }}
        />
      </div>
      {stageEvents.length ? (
        <div className="mt-4 max-h-[260px] space-y-2 overflow-auto pr-1">
          {stageEvents.slice(-8).reverse().map((event) => (
            <div className="rounded-[14px] border border-white/8 bg-white/4 px-3 py-2 text-xs leading-5 text-[var(--muted)]" key={`${event.stage_id}-${event.timestamp}`}>
              <span className="font-semibold text-[var(--text-strong)]">{event.title}</span>
              <span> / {event.detail}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function StatsResultCard({ result }: { result: StatsResult }) {
  return (
    <div className="rounded-[18px] border border-white/10 bg-white/5 p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-strong)]">
        <CheckCircle2 size={16} />
        {result.title}
      </div>
      <p className="mt-2 text-sm leading-7 text-[var(--muted)]">{result.narrative}</p>
      <div className="mt-3 grid gap-2">
        {Object.entries(result.metrics || {}).slice(0, 6).map(([label, value]) => (
          <div className="flex items-center justify-between gap-3 rounded-[12px] bg-black/15 px-3 py-2 text-xs" key={label}>
            <span className="text-[var(--muted)]">{label}</span>
            <span className="text-[var(--text-strong)]">{formatValue(value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DataTable({ table }: { table: GenericTable }) {
  if (!table.columns.length || !table.rows.length) {
    return (
      <div className="rounded-[18px] border border-dashed border-white/10 px-4 py-6 text-sm text-[var(--muted)]">
        当前章节还没有可展示的表格内容。
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-[18px] border border-white/10">
      {table.title ? <p className="border-b border-white/10 px-4 py-3 text-sm font-semibold text-[var(--text-strong)]">{table.title}</p> : null}
      <table className="data-grid min-w-full">
        <thead>
          <tr>
            {table.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.slice(0, 40).map((row, rowIndex) => (
            <tr key={`${rowIndex}-${table.columns[0]}`}>
              {table.columns.map((column) => (
                <td key={column}>{formatValue(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AccordionPanel({
  children,
  defaultOpen = false,
  description,
  eyebrow,
  title,
}: {
  children: ReactNode;
  defaultOpen?: boolean;
  description?: string;
  eyebrow: string;
  title: string;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/[0.035] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] md:p-5">
      <button className="flex w-full items-start justify-between gap-4 text-left" onClick={() => setOpen((value) => !value)} type="button">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">{eyebrow}</p>
          <h3 className="mt-2 text-lg font-semibold text-[var(--text-strong)]">{title}</h3>
          {description ? <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--muted)]">{description}</p> : null}
        </div>
        <span className="mt-1 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-lg text-[var(--text-strong)] transition">
          {open ? "-" : "+"}
        </span>
      </button>
      {open ? <div className="mt-5 space-y-5">{children}</div> : null}
    </section>
  );
}

function Field({ children, label }: { children: ReactNode; label: string }) {
  return (
    <label className="block space-y-2">
      <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">{label}</span>
      {children}
    </label>
  );
}

function SelectInput({
  onChange,
  options,
  placeholder,
  value,
}: {
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  placeholder?: string;
  value: string;
}) {
  return (
    <div className="relative">
      <select className="field-input appearance-none pr-10" onChange={(event) => onChange(event.target.value)} value={value}>
        {placeholder ? <option value="">{placeholder}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--muted)]" size={18} />
    </div>
  );
}

function PresetSelectInput({
  onChange,
  options,
  value,
}: {
  onChange: (value: string) => void;
  options: StylePresetOption[];
  value: string;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selected = options.find((option) => option.value === value) || options[0];

  useEffect(() => {
    if (!open) {
      return;
    }
    const handlePointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        aria-expanded={open}
        aria-haspopup="listbox"
        className="field-input flex min-h-[4.1rem] items-start justify-between gap-4 text-left"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold text-[var(--text-strong)]">{selected?.label || "选择报告风格"}</span>
          <span className="mt-1 block text-xs leading-5 text-[var(--muted)]">{selected?.description || "选择一个与报告气质匹配的风格预设。"}</span>
        </span>
        <ChevronDown className={`mt-1 shrink-0 text-[var(--muted)] transition-transform duration-200 ${open ? "rotate-180" : ""}`} size={18} />
      </button>
      {open ? (
        <div className="absolute z-30 mt-2 max-h-[22rem] w-full overflow-y-auto rounded-[1.25rem] border border-white/10 bg-[#101722]/96 p-2 shadow-2xl shadow-black/40 backdrop-blur-xl">
          <div className="space-y-1">
            {options.map((option) => {
              const active = option.value === value;
              return (
                <button
                  aria-selected={active}
                  className={`w-full rounded-xl px-3 py-2.5 text-left transition ${
                    active
                      ? "bg-amber-300/12 text-[var(--text-strong)] ring-1 ring-amber-300/35"
                      : "text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text-strong)]"
                  }`}
                  key={option.value}
                  onClick={() => {
                    onChange(option.value);
                    setOpen(false);
                  }}
                  role="option"
                  type="button"
                >
                  <span className="block text-sm font-semibold">{option.label}</span>
                  <span className="mt-1 block text-xs leading-5 opacity-80">{option.description}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function normalizePaletteColor(value: string) {
  const text = String(value || "").trim();
  if (!text) {
    return "";
  }
  if (/^#[0-9a-fA-F]{3}$/.test(text)) {
    return `#${text
      .slice(1)
      .split("")
      .map((char) => `${char}${char}`)
      .join("")
      .toLowerCase()}`;
  }
  if (/^#[0-9a-fA-F]{6}$/.test(text)) {
    return text.toLowerCase();
  }
  return "";
}

function sanitizePaletteColors(values: string[]) {
  const colors: string[] = [];
  for (const value of values) {
    const normalized = normalizePaletteColor(value);
    if (!normalized || colors.includes(normalized)) {
      continue;
    }
    colors.push(normalized);
    if (colors.length >= MAX_PALETTE_COLORS) {
      break;
    }
  }
  return colors.length ? colors : PALETTE_PRESETS[0].colors.slice();
}

function reorderPaletteColors(values: string[], fromIndex: number, toIndex: number) {
  if (fromIndex === toIndex) {
    return values;
  }
  if (fromIndex < 0 || toIndex < 0 || fromIndex >= values.length || toIndex >= values.length) {
    return values;
  }
  const next = values.slice();
  const [moving] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moving);
  return next;
}

function nextPaletteColor(currentColors: string[], activePreset: PalettePresetOption) {
  const used = new Set(currentColors.map((color) => normalizePaletteColor(color)).filter(Boolean));
  const candidates = [...activePreset.colors, ...PALETTE_PRESETS.flatMap((preset) => preset.colors)];
  return candidates.find((color) => !used.has(normalizePaletteColor(color))) || "#2563eb";
}

type RgbColor = {
  b: number;
  g: number;
  r: number;
};

type HsvColor = {
  h: number;
  s: number;
  v: number;
};

function clampNumber(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function hsvToRgb(hue: number, saturation: number, value: number): RgbColor {
  const h = (((hue % 360) + 360) % 360) / 60;
  const s = clampNumber(saturation, 0, 1);
  const v = clampNumber(value, 0, 1);
  const c = v * s;
  const x = c * (1 - Math.abs((h % 2) - 1));
  const m = v - c;
  let r = 0;
  let g = 0;
  let b = 0;

  if (h < 1) {
    r = c;
    g = x;
  } else if (h < 2) {
    r = x;
    g = c;
  } else if (h < 3) {
    g = c;
    b = x;
  } else if (h < 4) {
    g = x;
    b = c;
  } else if (h < 5) {
    r = x;
    b = c;
  } else {
    r = c;
    b = x;
  }

  return {
    b: Math.round((b + m) * 255),
    g: Math.round((g + m) * 255),
    r: Math.round((r + m) * 255),
  };
}

function rgbToHex({ b, g, r }: RgbColor) {
  return `#${[r, g, b]
    .map((channel) => clampNumber(Math.round(channel), 0, 255).toString(16).padStart(2, "0"))
    .join("")}`;
}

function hexToRgb(value: string): RgbColor | null {
  const normalized = normalizePaletteColor(value);
  if (!normalized) {
    return null;
  }
  return {
    b: Number.parseInt(normalized.slice(5, 7), 16),
    g: Number.parseInt(normalized.slice(3, 5), 16),
    r: Number.parseInt(normalized.slice(1, 3), 16),
  };
}

function rgbToHsv({ b, g, r }: RgbColor): HsvColor {
  const red = clampNumber(r, 0, 255) / 255;
  const green = clampNumber(g, 0, 255) / 255;
  const blue = clampNumber(b, 0, 255) / 255;
  const max = Math.max(red, green, blue);
  const min = Math.min(red, green, blue);
  const delta = max - min;
  let h = 0;

  if (delta !== 0) {
    if (max === red) {
      h = 60 * (((green - blue) / delta) % 6);
    } else if (max === green) {
      h = 60 * ((blue - red) / delta + 2);
    } else {
      h = 60 * ((red - green) / delta + 4);
    }
  }

  return {
    h: (h + 360) % 360,
    s: max === 0 ? 0 : delta / max,
    v: max,
  };
}

function hsvFromHex(value: string): HsvColor {
  const rgb = hexToRgb(value);
  return rgb ? rgbToHsv(rgb) : { h: 215, s: 0.72, v: 0.9 };
}

function colorWheelPosition(hsv: HsvColor) {
  const radians = (hsv.h * Math.PI) / 180;
  return {
    left: `${50 + Math.cos(radians) * hsv.s * 50}%`,
    top: `${50 + Math.sin(radians) * hsv.s * 50}%`,
  };
}

function ColorWheelPicker({
  onChange,
  selectedIndex,
  value,
}: {
  onChange: (color: string) => void;
  selectedIndex: number;
  value: string;
}) {
  const wheelRef = useRef<HTMLDivElement | null>(null);
  const normalizedValue = normalizePaletteColor(value) || "#2563eb";
  const hsv = hsvFromHex(normalizedValue);
  const markerPosition = colorWheelPosition(hsv);
  const vividColor = rgbToHex(hsvToRgb(hsv.h, hsv.s, 1));

  function updateFromWheel(event: PointerEvent<HTMLDivElement>) {
    const rect = wheelRef.current?.getBoundingClientRect();
    if (!rect) {
      return;
    }
    const radius = Math.min(rect.width, rect.height) / 2;
    const dx = event.clientX - rect.left - rect.width / 2;
    const dy = event.clientY - rect.top - rect.height / 2;
    const distance = Math.min(Math.hypot(dx, dy), radius);
    const hue = ((Math.atan2(dy, dx) * 180) / Math.PI + 360) % 360;
    const saturation = clampNumber(distance / radius, 0, 1);
    const nextBrightness = hsv.v < 0.18 ? 0.9 : hsv.v;
    onChange(rgbToHex(hsvToRgb(hue, saturation, nextBrightness)));
  }

  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--text-strong)]">连续色盘</p>
          <p className="mt-1 text-xs leading-5 text-[var(--muted)]">在圆盘中点击或拖动，替换当前色位。</p>
        </div>
        <div className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">色位 {selectedIndex + 1}</div>
      </div>

      <div className="mt-5 flex justify-center">
        <div
          aria-label={`调整第 ${selectedIndex + 1} 个颜色`}
          className="relative aspect-square w-full max-w-[14rem] cursor-crosshair touch-none rounded-full border border-white/20 shadow-[0_18px_60px_rgba(0,0,0,0.35),inset_0_0_28px_rgba(0,0,0,0.22)]"
          onPointerDown={(event) => {
            event.currentTarget.setPointerCapture(event.pointerId);
            updateFromWheel(event);
          }}
          onPointerMove={(event) => {
            if (event.buttons !== 1 && event.pointerType !== "touch") {
              return;
            }
            updateFromWheel(event);
          }}
          ref={wheelRef}
          style={{
            background:
              "radial-gradient(circle, #ffffff 0%, rgba(255,255,255,0.88) 10%, rgba(255,255,255,0) 58%), conic-gradient(from 90deg, #ef4444, #f97316, #facc15, #22c55e, #14b8a6, #06b6d4, #2563eb, #7c3aed, #e11d48, #ef4444)",
          }}
        >
          <span
            className="pointer-events-none absolute h-6 w-6 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white shadow-[0_8px_24px_rgba(0,0,0,0.45),0_0_0_1px_rgba(0,0,0,0.25)]"
            style={{ ...markerPosition, backgroundColor: normalizedValue }}
          />
        </div>
      </div>

      <label className="mt-5 block text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]" htmlFor="palette-brightness">
        明暗
      </label>
      <input
        className="mt-2 h-2 w-full cursor-pointer appearance-none rounded-full"
        id="palette-brightness"
        max={100}
        min={8}
        onChange={(event) => {
          const nextBrightness = Number(event.target.value) / 100;
          onChange(rgbToHex(hsvToRgb(hsv.h, hsv.s, nextBrightness)));
        }}
        style={{ background: `linear-gradient(90deg, #050607, ${vividColor})` }}
        type="range"
        value={Math.round(hsv.v * 100)}
      />

      <div className="mt-4 flex items-center gap-3">
        <span className="h-12 w-12 rounded-2xl border border-white/15 shadow-inner" style={{ backgroundColor: normalizedValue }} />
        <input
          aria-label={`选择第 ${selectedIndex + 1} 个颜色`}
          className="h-12 w-16 cursor-pointer rounded-xl border border-white/10 bg-transparent p-1"
          onChange={(event) => onChange(event.target.value)}
          type="color"
          value={normalizedValue}
        />
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">当前颜色</p>
          <p className="mt-1 font-mono text-sm font-semibold text-[var(--text-strong)]">{normalizedValue}</p>
        </div>
      </div>
    </div>
  );
}

function loadSavedPalettePresets(): SavedPalettePreset[] {
  if (typeof window === "undefined") {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(CUSTOM_PALETTE_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }
    const saved = parsed
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }
        const candidate = item as Partial<SavedPalettePreset>;
        if (candidate.source !== "custom" || typeof candidate.id !== "string" || typeof candidate.label !== "string") {
          return null;
        }
        return {
          colors: sanitizePaletteColors(Array.isArray(candidate.colors) ? candidate.colors.map((value) => String(value)) : []),
          createdAt: Number(candidate.createdAt) || Date.now(),
          id: candidate.id,
          label: candidate.label,
          source: "custom" as const,
        };
      })
      .filter((item): item is NonNullable<typeof item> => item !== null);
    return saved.map((item) => ({ ...item, source: "custom" }));
  } catch {
    return [];
  }
}

function savePalettePresets(presets: SavedPalettePreset[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(CUSTOM_PALETTE_STORAGE_KEY, JSON.stringify(presets));
}

function makePalettePresetId(label: string) {
  const base = label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `custom-${base || "palette"}-${Date.now().toString(36)}`;
}

function PaletteEditor({
  colors,
  onColorsChange,
  onPresetChange,
  presetId,
  presets,
}: {
  colors: string[];
  onColorsChange: (colors: string[]) => void;
  onPresetChange: (presetId: string) => void;
  presetId: string;
  presets: PalettePresetOption[];
}) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [selectedColorIndex, setSelectedColorIndex] = useState(0);
  const [customPresets, setCustomPresets] = useState<SavedPalettePreset[]>(() => loadSavedPalettePresets());
  const [newPresetName, setNewPresetName] = useState("");
  const activePreset = presets.find((preset) => preset.id === presetId) || presets[0];
  const paletteColors = sanitizePaletteColors(colors);
  const canAddColor = paletteColors.length < MAX_PALETTE_COLORS;
  const allPresets = [...presets, ...customPresets];
  const activeColorIndex = Math.min(selectedColorIndex, Math.max(paletteColors.length - 1, 0));
  const activeColorValue = paletteColors[activeColorIndex] || "#2563eb";

  function commitColors(nextColors: string[]) {
    onColorsChange(sanitizePaletteColors(nextColors));
  }

  function updateSelectedColor(color: string) {
    if (!paletteColors.length) {
      return;
    }
    const next = paletteColors.slice();
    next[Math.min(selectedColorIndex, next.length - 1)] = color;
    commitColors(next);
  }

  function applyPreset(preset: PalettePresetOption) {
    onPresetChange(preset.id);
    onColorsChange(sanitizePaletteColors(preset.colors));
    setSelectedColorIndex(0);
    setNewPresetName(preset.label);
  }

  function updateCustomPresets(nextPresets: SavedPalettePreset[]) {
    setCustomPresets(nextPresets);
    savePalettePresets(nextPresets);
  }

  function saveCurrentAsPreset() {
    const label = newPresetName.trim() || "未命名色谱";
    const cleanedColors = sanitizePaletteColors(paletteColors);
    const nextPreset: SavedPalettePreset = {
      colors: cleanedColors,
      createdAt: Date.now(),
      id: makePalettePresetId(label),
      label,
      source: "custom",
    };
    updateCustomPresets([nextPreset, ...customPresets.filter((preset) => preset.label !== label)]);
    onPresetChange(nextPreset.id);
  }

  function deleteCustomPreset(id: string) {
    updateCustomPresets(customPresets.filter((preset) => preset.id !== id));
    if (presetId === id) {
      onPresetChange(activePreset.id);
    }
  }

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/[0.035] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] md:p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">图表色谱</p>
          <h3 className="mt-2 text-lg font-semibold text-[var(--text-strong)]">可拖动、可补色、可保存的图表配色</h3>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--muted)]">
            先选一个预设，再用色盘给当前色位换色；也可以添加、删除、拖动排序，并保存成自己的颜色预设。
          </p>
        </div>
        <button
          className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--text-strong)] transition hover:border-amber-300/40 hover:bg-amber-300/10"
          onClick={() => applyPreset(activePreset)}
          type="button"
        >
          恢复预设
        </button>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {presets.map((preset) => {
          const selected = preset.id === presetId;
          return (
            <button
              className={`rounded-2xl border p-3 text-left transition ${
                selected
                  ? "border-amber-300/70 bg-amber-300/10 shadow-[0_0_0_1px_rgba(252,211,77,0.18)]"
                  : "border-white/10 bg-white/[0.03] hover:border-white/25 hover:bg-white/[0.06]"
              }`}
              key={preset.id}
              onClick={() => applyPreset(preset)}
              type="button"
            >
              <div className="flex gap-1">
                {preset.colors.slice(0, MAX_PALETTE_COLORS).map((color) => (
                  <span
                    className="h-5 flex-1 rounded-full border border-white/15"
                    key={`${preset.id}-${color}`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <div className="mt-2 font-semibold text-slate-100">{preset.label}</div>
              <div className="mt-1 text-xs leading-5 text-[var(--muted)]">{preset.colors.length} 色预设</div>
            </button>
            );
          })}
        {customPresets.map((preset) => {
          const selected = preset.id === presetId;
          return (
            <button
              className={`rounded-2xl border p-3 text-left transition ${
                selected
                  ? "border-amber-300/70 bg-amber-300/10 shadow-[0_0_0_1px_rgba(252,211,77,0.18)]"
                  : "border-white/10 bg-white/[0.03] hover:border-white/25 hover:bg-white/[0.06]"
              }`}
              key={preset.id}
              onClick={() => applyPreset(preset)}
              type="button"
            >
              <div className="flex gap-1">
                {preset.colors.slice(0, MAX_PALETTE_COLORS).map((color) => (
                  <span
                    className="h-5 flex-1 rounded-full border border-white/15"
                    key={`${preset.id}-${color}`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <div className="mt-2 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate font-semibold text-slate-100">{preset.label}</div>
                  <div className="mt-1 text-xs leading-5 text-[var(--muted)]">{preset.colors.length} 色自定义预设</div>
                </div>
                <button
                  className="rounded-lg border border-white/10 bg-white/[0.04] p-2 text-[var(--muted)] transition hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200"
                  onClick={(event) => {
                    event.stopPropagation();
                    deleteCustomPreset(preset.id);
                  }}
                  type="button"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-5 rounded-[24px] border border-white/10 bg-black/10 p-4">
        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-[var(--text-strong)]">当前色序</p>
                <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                  拖动左侧把手调整顺序，点色块就能选中当前色位。
                </p>
              </div>
              <button
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-semibold text-[var(--text-strong)] transition hover:border-amber-300/40 hover:bg-amber-300/10 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!canAddColor}
                onClick={() => commitColors([...paletteColors, nextPaletteColor(paletteColors, activePreset)])}
                type="button"
              >
                <Plus size={16} />
                添加颜色
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {paletteColors.map((color, index) => {
                const isDragging = dragIndex === index;
                const isSelected = index === activeColorIndex;
                return (
                  <div
                    className={`flex items-center gap-3 rounded-2xl border px-3 py-3 transition ${
                      isDragging
                        ? "border-amber-300/70 bg-amber-300/10"
                        : isSelected
                          ? "border-sky-300/70 bg-sky-300/10"
                          : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.06]"
                    }`}
                    draggable
                    key={`${index}-${color}`}
                    onDragEnd={() => setDragIndex(null)}
                    onDragOver={(event) => {
                      event.preventDefault();
                    }}
                    onDragStart={(event) => {
                      setDragIndex(index);
                      event.dataTransfer.effectAllowed = "move";
                      event.dataTransfer.setData("text/plain", String(index));
                    }}
                    onDrop={(event) => {
                      event.preventDefault();
                      const nextIndex = index;
                      const fromIndex = dragIndex ?? Number(event.dataTransfer.getData("text/plain"));
                      if (Number.isNaN(fromIndex)) {
                        return;
                      }
                      commitColors(reorderPaletteColors(paletteColors, fromIndex, nextIndex));
                      setDragIndex(null);
                    }}
                    role="listitem"
                  >
                    <button
                      aria-label={`拖动第 ${index + 1} 个颜色`}
                      className="cursor-grab rounded-xl border border-white/10 bg-white/[0.04] p-2 text-[var(--muted)] active:cursor-grabbing"
                      type="button"
                    >
                      <GripVertical size={16} />
                    </button>
                    <button
                      aria-label={`选中第 ${index + 1} 个颜色`}
                      className="h-11 w-11 shrink-0 rounded-xl border border-white/10"
                      onClick={() => setSelectedColorIndex(index)}
                      style={{ backgroundColor: color }}
                      type="button"
                    />
                    <input
                      aria-label={`第 ${index + 1} 个颜色`}
                      className="h-11 w-14 shrink-0 cursor-pointer rounded-xl border border-white/10 bg-transparent p-1"
                      onChange={(event) => {
                        const next = paletteColors.slice();
                        next[index] = event.target.value;
                        commitColors(next);
                      }}
                      type="color"
                      value={color}
                    />
                    <button
                      className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-left text-xs font-mono text-[var(--text-strong)] transition hover:border-sky-300/40 hover:bg-sky-300/10"
                      onClick={() => setSelectedColorIndex(index)}
                      type="button"
                    >
                      {color}
                    </button>
                    <button
                      className="rounded-xl border border-white/10 bg-white/[0.04] p-2 text-[var(--muted)] transition hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200 disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={paletteColors.length <= 1}
                      onClick={() => {
                        if (paletteColors.length <= 1) {
                          return;
                        }
                        const next = paletteColors.filter((_, colorIndex) => colorIndex !== index);
                        commitColors(next);
                        setSelectedColorIndex((current) => Math.min(current, Math.max(next.length - 1, 0)));
                      }}
                      type="button"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-4">
            <ColorWheelPicker onChange={updateSelectedColor} selectedIndex={activeColorIndex} value={activeColorValue} />

            <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm font-semibold text-[var(--text-strong)]">保存为预设</p>
              <p className="mt-1 text-xs leading-5 text-[var(--muted)]">命名后会存在浏览器本地，下次还能继续选。</p>
              <div className="mt-4 flex gap-2">
                <input
                  className="field-input min-w-0 flex-1"
                  onChange={(event) => setNewPresetName(event.target.value)}
                  placeholder="给这个色盘起个名字"
                  value={newPresetName}
                />
                <button
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm font-semibold text-[var(--text-strong)] transition hover:border-emerald-300/40 hover:bg-emerald-300/10"
                  onClick={saveCurrentAsPreset}
                  type="button"
                >
                  <Save size={16} />
                  保存
                </button>
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm font-semibold text-[var(--text-strong)]">全部预设</p>
              <div className="mt-3 max-h-[18rem] space-y-2 overflow-y-auto pr-1">
                {allPresets.map((preset) => {
                  const selected = preset.id === presetId;
                  return (
                    <button
                      className={`w-full rounded-2xl border p-3 text-left transition ${
                        selected
                          ? "border-amber-300/70 bg-amber-300/10 shadow-[0_0_0_1px_rgba(252,211,77,0.18)]"
                          : "border-white/10 bg-black/10 hover:border-white/25 hover:bg-white/[0.06]"
                      }`}
                      key={preset.id}
                      onClick={() => applyPreset(preset)}
                      type="button"
                    >
                      <div className="flex gap-1">
                        {preset.colors.slice(0, MAX_PALETTE_COLORS).map((color) => (
                          <span
                            className="h-4 flex-1 rounded-full border border-white/15"
                            key={`${preset.id}-${color}`}
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                      <div className="mt-2 flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-slate-100">{preset.label}</div>
                          <div className="mt-1 text-xs leading-5 text-[var(--muted)]">
                            {preset.source === "custom" ? "自定义预设" : "系统预设"}
                          </div>
                        </div>
                        {preset.source === "custom" ? (
                          <button
                            className="rounded-lg border border-white/10 bg-white/[0.04] p-2 text-[var(--muted)] transition hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200"
                            onClick={(event) => {
                              event.stopPropagation();
                              deleteCustomPreset(preset.id);
                            }}
                            type="button"
                          >
                            <Trash2 size={14} />
                          </button>
                        ) : null}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ToggleField({
  checked,
  description,
  onChange,
  title,
}: {
  checked: boolean;
  description: string;
  onChange: (value: boolean) => void;
  title: string;
}) {
  return (
    <label className="flex items-start gap-3 rounded-[18px] border border-white/8 bg-white/4 px-4 py-3 text-sm text-[var(--text-strong)] transition-colors duration-200 hover:border-white/14 hover:bg-white/6">
      <input
        checked={checked}
        className="mt-1 h-4 w-4 shrink-0"
        onChange={(event) => onChange(event.target.checked)}
        style={{ accentColor: "var(--accent-warm)" }}
        type="checkbox"
      />
      <span>
        <span className="block font-semibold">{title}</span>
        <span className="mt-1 block text-xs leading-6 text-[var(--muted)]">{description}</span>
      </span>
    </label>
  );
}

function MiniMetric({ detail, label, value }: { detail?: string; label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-xl bg-black/10 p-3">
      <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">{label}</p>
      <p className="mt-2 break-words text-sm font-semibold leading-5 text-[var(--text-strong)]">{value}</p>
      {detail ? <p className="mt-2 text-xs leading-5 text-[var(--muted)]">{detail}</p> : null}
    </div>
  );
}

function ListCard({ items, title }: { items?: string[]; title: string }) {
  const filtered = (items || []).map(asText).filter(Boolean);
  if (!filtered.length) {
    return null;
  }
  return (
    <div className="table-card rounded-[18px] p-4">
      <p className="mb-3 text-sm font-semibold text-[var(--text-strong)]">{title}</p>
      <div className="space-y-2">
        {filtered.map((item) => (
          <div className="break-words rounded-[16px] border border-white/8 bg-white/4 px-4 py-3 text-sm leading-7 text-[var(--muted)]" key={item}>
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusPill({ label, value }: { label: string; value: string }) {
  return (
    <span className="surface-chip">
      {label}: {value}
    </span>
  );
}

function ErrorBox({ children }: { children: ReactNode }) {
  return (
    <div className="mt-3 rounded-[16px] border border-red-300/20 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
      {children}
    </div>
  );
}
