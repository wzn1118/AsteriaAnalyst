"use client";

import {
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  Database,
  Expand,
  FileText,
  FileUp,
  Filter,
  PackageOpen,
  Layers3,
  LoaderCircle,
  LockKeyhole,
  Maximize2,
  Minimize2,
  Plus,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Sparkles,
  Table2,
  Workflow,
} from "lucide-react";
import Link from "next/link";
import {
  Children,
  isValidElement,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
  useTransition,
} from "react";
import { createPortal } from "react-dom";

import { DatasetPicker } from "@/components/dataset-picker";
import { MethodGuideModal, type MethodGuideTopic } from "@/components/method-guide-modal";
import { apiRequest } from "@/lib/api";
import type {
  AutoAnalysisData,
  AutoReportPartGenerationBlueprint,
  GenericTable,
  SmartReport,
  StatsResult,
} from "@/lib/types";

type DatasetItem = {
  dataset_id: string;
  name?: string;
  filename?: string;
  active_sheet?: string;
  sheets?: Array<{ name: string; rows?: number; columns?: number }>;
  row_count?: number;
  column_count?: number;
  numeric_columns?: string[];
  categorical_columns?: string[];
  datetime_columns?: string[];
  sample_rows?: Record<string, unknown>[];
  column_summaries?: Array<{
    name: string;
    dtype?: string;
    missing_count?: number;
    missing_ratio?: number;
    unique_count?: number;
    sample_values?: unknown[];
    stats?: Record<string, unknown>;
  }>;
};

type DatasetListResponse = {
  datasets: DatasetItem[];
};

type MethodCatalogItem = {
  id: string;
  name: string;
  name_zh: string;
  package_ref?: string;
  path?: string;
  base_method_id?: string;
  bundle_id?: string;
  bundle_title?: string;
  bundle_title_zh?: string;
  bundle_title_en?: string;
  parent_method_id?: string;
  parent_method_title?: string;
  method_concept_label?: string;
  method_output_label?: string;
  submethod_label?: string;
  submethod_title?: string;
  output_variant?: string;
  family: string;
  family_label?: string;
  goal?: string;
  goal_zh?: string;
  status: string;
  source: string;
  allowed_domain?: string;
  excluded_domain?: string;
  output_types: string[];
  stable_output_types?: string[];
  default_output_types?: string[];
  output_labels?: string[];
  required_roles: string[];
  role_labels?: string[];
  runtime_required?: boolean;
  runtime_executor?: string;
  cli_runtime_available?: boolean;
  runtime_block_reason?: string;
  runtime_binding_roles?: string[];
  compatibility_alias_ids?: string[];
  output_modes?: string[];
  granularity_modes?: string[];
  runtime_dimensions?: Record<string, unknown>;
  run_metadata_schema?: Record<string, unknown>;
  artifact_contract?: Record<string, unknown>;
  field_bindings?: MethodFieldBinding;
  selection_mode?: MethodRunSelectionMode | "";
  object_selection?: MethodRunSpec["object_selection"];
  statistical_options?: MethodStatisticalOptions;
  card_description?: string;
  card_tags?: string[];
  card_sections?: Array<{
    kind: string;
    label: string;
    value: string;
    help?: string;
  }>;
  method_card_contract?: string;
  edit_capabilities?: {
    editable_fields?: string[];
    editable_field_labels?: string[];
    selection_modes?: MethodRunSelectionMode[];
    selection_mode_labels?: Array<{
      mode: MethodRunSelectionMode;
      label: string;
      recommended?: boolean;
    }>;
    run_controls?: string[];
    run_control_labels?: string[];
    freedom_score?: number;
  };
  usage_guidance?: Array<{
    title: string;
    detail: string;
  }>;
  report_value_hooks?: string[];
  binding_controls?: string[];
  recommended_selection_mode?: MethodRunSelectionMode;
};

type MethodCatalogResponse = {
  methods: MethodCatalogItem[];
  summary: {
    total_methods: number;
    live_or_catalog_methods: number;
    planned_methods: number;
    learned_methods: number;
    families: string[];
    sources: Record<string, number>;
    statuses: Record<string, number>;
    learned_method_path: string;
  };
  priority_method_ids: string[];
  report_parts: string[];
  method_aliases?: Record<string, string>;
  compact?: boolean;
};

type MethodCardSection = NonNullable<MethodCatalogItem["card_sections"]>[number];
type MethodUsageGuidance = NonNullable<MethodCatalogItem["usage_guidance"]>[number];

type MethodIndexItem = {
  method: MethodCatalogItem;
  family: string;
  familyLabel: string;
  displayTitle: string;
  bundleTitle: string;
  outputLabel: string;
  goalText: string;
  outputLabels: string[];
  roleLabels: string[];
  searchText: string;
};

type MethodQualitySummary = {
  total: number;
  visual: number;
  nonFinancialVisual: number;
  runnable: number;
  blocked: number;
  selected: number;
  selectedRunnable: number;
  saved: number;
  sources: Record<string, number>;
  readyPercent: number;
  visualSlaMet: boolean;
  financeExcluded: boolean;
};

const DEFAULT_REPORT_PARTS = [
  "executive_summary",
  "chapter",
  "visual_gallery",
  "appendix",
  "method_note",
  "field_glossary",
  "action_plan",
  "evidence_index",
];

const REPORT_PART_LABELS: Record<string, string> = {
  executive_summary: "管理摘要",
  chapter: "分析章节",
  visual_gallery: "图组与管理解读",
  appendix: "分析附录",
  method_note: "方法说明",
  field_glossary: "字段解释",
  action_plan: "行动建议",
  evidence_index: "证据索引",
};

const DEFAULT_EXTERNAL_SKILL_SOURCE_URL = "https://github.com/anthropics/knowledge-work-plugins";
const LEGACY_EXTERNAL_SKILL_SOURCE_URL = "https://github.com/anthropics/skills";

type ExternalSkillItem = {
  id: string;
  name: string;
  description?: string;
  license?: string;
  source?: string;
  source_url?: string;
  source_repo?: string;
  source_ref?: string;
  source_path?: string;
  package_path?: string;
  skill_md_path?: string;
  mounted: boolean;
  installed_at?: string;
  updated_at?: string;
  file_count?: number;
  instruction_chars?: number;
  instruction_excerpt?: string;
  package_kind?: string;
  kind?: string;
  plugin_name?: string;
  plugin_version?: string;
  plugin_author?: string;
  skill_count?: number;
  command_count?: number;
  mcp_server_count?: number;
  plugin_skills?: Array<{ id?: string; name?: string; description?: string; path?: string; instruction_chars?: number }>;
  commands?: Array<{ name?: string; description?: string; path?: string; instruction_chars?: number }>;
  mcp_servers?: Array<{ name?: string; type?: string; url?: string; command?: string; oauth?: boolean }>;
};

type ExternalSkillFeatureKind = "command" | "embedded_skill";

type ExternalSkillFeatureSelection = {
  plugin_id: string;
  feature_kind: ExternalSkillFeatureKind;
  feature_id: string;
  name?: string;
  description?: string;
  path?: string;
  selection_source?: string;
};

type ExternalSkillResponse = {
  summary: {
    count: number;
    mounted_count: number;
    plugin_count?: number;
    mounted_plugin_count?: number;
    embedded_skill_count?: number;
    command_count?: number;
    mcp_server_count?: number;
    skill_ids?: string[];
    mounted_skill_ids?: string[];
  };
  skills: ExternalSkillItem[];
  default_source_url?: string;
  storage_dir?: string;
  installed_count?: number;
  source_url?: string;
  source_ref?: string;
  local_path?: string;
};

type LabFeatureTrialResult = {
  trial_id: string;
  created_at?: string;
  dataset?: { dataset_id?: string; name?: string; sheet_name?: string };
  plugin?: { id?: string; name?: string; version?: string; source_repo?: string };
  feature?: { feature_kind?: string; feature_id?: string; name?: string; description?: string; path?: string };
  baseline_profile?: {
    row_count?: number;
    column_count?: number;
    numeric_column_count?: number;
    categorical_column_count?: number;
    datetime_column_count?: number;
    duplicate_row_count?: number;
  };
  enhancement_effect?: {
    readiness_score?: number;
    readiness_reasons?: string[];
    summary?: string;
    top_fields?: Array<{ column?: string; role?: string; dtype?: string; score?: number; missing_rate?: number }>;
    recommended_actions?: string[];
  };
  recommended_lab_run_payload?: Record<string, unknown>;
  artifacts?: { directory?: string; json_url?: string; csv_url?: string; report_url?: string };
};

type LabReportAgentTeamItem = {
  id: string;
  name: string;
  description?: string;
  source?: string;
  source_url?: string;
  source_ref?: string;
  source_path?: string;
  package_path?: string;
  mounted: boolean;
  installed_at?: string;
  updated_at?: string;
  version?: string;
  agent_count?: number;
  agents?: Array<{
    id: string;
    name: string;
    role?: string;
    path?: string;
    chars?: number;
  }>;
  entry_file?: string;
  codex_ready?: boolean;
};

type LabReportAgentTeamResponse = {
  summary: {
    count: number;
    mounted_count: number;
    team_ids?: string[];
    mounted_team_ids?: string[];
  };
  teams: LabReportAgentTeamItem[];
  default_source_url?: string;
  storage_dir?: string;
  installed_count?: number;
  local_path?: string;
};

type RunMode = "auto" | "method" | "batch" | "smart_report";
type MethodFilter = "all" | "visual" | "live" | "catalog" | "planned" | "selected" | "recommended";

const RUN_MODE_LABELS: Record<RunMode, string> = {
  auto: "合并运行",
  method: "单方法",
  batch: "批量独立",
  smart_report: "报告试跑",
};

type WorkspaceResult = {
  mode: RunMode;
  title: string;
  datasetName: string;
  createdAt: string;
  payload: unknown;
};

type MethodRunResult = {
  method_id: string;
  method_run_id: string;
  method_run_label: string;
  method_name: string;
  method_name_zh: string;
  status: string;
  runtime_status?: string;
  local_preparation_status?: string;
  runtime_required?: boolean;
  runtime_executor?: string;
  runtime_job_id?: string;
  runtime_manifest_path?: string;
  runtime_error?: string;
  source: string;
  selection_mode: MethodRunSelectionMode | string;
  smart_merge_group: string;
  payload: unknown;
  ran_at: string;
};

type MethodBundle = {
  id: string;
  family: string;
  title: string;
  concept: string;
  role: string;
  grouped: boolean;
  representative: MethodCatalogItem;
  methods: MethodCatalogItem[];
};

type FieldSelection = {
  target: string;
  features: string[];
  group: string;
  label: string;
  time: string;
  bubble: {
    x: string;
    y: string;
    size: string;
    color: string;
    label: string;
  };
  quadrant: {
    x: string;
    y: string;
    group: string;
    label: string;
  };
};

type DerivedMetricEdit = {
  field: string;
  display_name: string;
  formula: string;
  source_fields: string[];
  recipe_id?: string;
  selected: boolean;
  custom?: boolean;
};

type MethodFieldBinding = {
  field?: string;
  x?: string;
  y?: string;
  target?: string;
  dataset_scope?: string;
  features?: string[];
  group?: string;
  label?: string;
  entity?: string;
  time?: string;
  derived_metric?: string;
  derived_metrics?: string[];
};

type MethodStatisticalOptions = {
  alpha?: number;
  hypothesis?: "two-sided" | "larger" | "smaller";
  test_value?: number;
  population_std?: number;
  components?: number;
  clusters?: number;
  window?: number;
  lag?: number;
  regularization_strength?: number;
  l1_ratio?: number;
  quantile?: number;
  bootstrap_iterations?: number;
  metric_type?: "auto" | "continuous" | "binary";
  success_value?: string;
  group_a?: string;
  group_b?: string;
};

type SmartMethodBindingRole = {
  key: keyof MethodFieldBinding;
  label: string;
  value: string;
  confidence: "high" | "medium" | "fallback";
};

type SmartMethodBindingPlan = {
  binding: MethodFieldBinding;
  roles: SmartMethodBindingRole[];
  reasons: string[];
  missing: string[];
  confidence: number;
};

type MethodFieldBindings = Record<string, MethodFieldBinding>;

type MethodRunSelectionMode = "fields" | "all_rows" | "object";

type MethodRunSpec = {
  run_id: string;
  method_id: string;
  label: string;
  bundle_run_id?: string;
  bundle_title?: string;
  selection_mode: MethodRunSelectionMode;
  field_bindings: MethodFieldBinding;
  object_selection?: {
    object_type?: string;
    merge_mode?: "smart" | "manual";
    object_keys?: string[];
    group_key?: string;
    label_key?: string;
    filter_field?: string;
    filter_values?: string[];
    filter_operator?: "in" | "eq";
    selection_source?: "fields" | "point_pick";
  };
  smart_merge_group?: string;
  statistical_options?: MethodStatisticalOptions;
};

type MethodEditorTarget = {
  methodId: string;
  runId?: string;
};

type MethodRunSpecPatch = Partial<Omit<MethodRunSpec, "field_bindings" | "object_selection" | "smart_merge_group" | "statistical_options">> & {
  field_bindings?: MethodFieldBinding | null;
  object_selection?: MethodRunSpec["object_selection"] | null;
  smart_merge_group?: string | null;
  statistical_options?: MethodStatisticalOptions | null;
};

type SavedMethodCardResponse = {
  status: string;
  method?: MethodCatalogItem;
  learned_method_path?: string;
  method_count?: number;
};

type WorkflowProgressState = {
  active: boolean;
  phase: "idle" | "upload" | "understand" | "clean" | "derive" | "route" | "ready" | "failed";
  percent: number;
  title: string;
  detail: string;
};

const EMPTY_FIELD_SELECTION: FieldSelection = {
  target: "",
  features: [],
  group: "",
  label: "",
  time: "",
  bubble: { x: "", y: "", size: "", color: "", label: "" },
  quadrant: { x: "", y: "", group: "", label: "" },
};

const METHOD_NAME_SEPARATOR = String.fromCharCode(0x30fb);
const METHOD_BUNDLE_SEGMENT_COUNT = 3;
const METHOD_DEFAULT_OUTPUT_PRIORITY = ["chart", "text", "table", "data", "report_section", "image_spec"];
const METHOD_TEXTUAL_DEFAULT_OUTPUTS = ["text", "table", "data"];
const METHOD_VISUAL_DEFAULT_OUTPUTS = ["chart", "text"];
const METHOD_REPORT_DEFAULT_OUTPUTS = ["report_section", "text"];
const METHOD_CHART_OUTPUTS = new Set(["chart", "image_spec"]);
const DEFAULT_SELECTED_METHOD_RUNS = 20;
const MAX_SELECTED_METHOD_RUNS = 24;
const INITIAL_VISIBLE_METHOD_LIMIT = 72;
const METHOD_LOAD_MORE_STEP = 120;
const AUTO_PREPROCESS_MAX_ROWS = 12_000;
const AUTO_PREPROCESS_MAX_CELLS = 250_000;
const CJK_TEXT_PATTERN = /[\u3400-\u9fff]/;

const METHOD_FAMILY_LABELS: Record<string, string> = {
  descriptive: "描述统计",
  association: "关联分析",
  categorical_association: "分类关联",
  comparison: "差异比较",
  distribution_assumption: "分布假设",
  mean_tests: "均值检验",
  nonparametric: "非参数检验",
  regression: "回归建模",
  regression_glm: "广义线性模型",
  machine_learning: "机器学习",
  multivariate: "多变量分析",
  time_series: "时间序列",
  causal: "因果探查",
  causal_panel: "面板因果",
  survival: "生存分析",
  experimentation: "实验分析",
  psychometrics: "心理测量",
  visual: "可视化",
  report_part: "报告部件",
  learned: "已学习方法",
  statistical: "统计方法",
};

const METHOD_OUTPUT_LABELS: Record<string, string> = {
  chart: "图表",
  image_spec: "图片规格",
  report_section: "报告段落",
  text: "文字解读",
  table: "表格",
  data: "结构化数据",
  summary: "摘要",
  diagnostics: "诊断信息",
};

const METHOD_ROLE_LABELS: Record<string, string> = {
  single_field: "单字段",
  field_pair: "字段组合",
  field_set: "字段集合",
  grouped: "分组",
  categorical: "分类字段",
  dimension: "维度",
  group: "分组字段",
  time_window: "时间窗口",
  time: "时间字段",
  entity_level: "实体层级",
  entity: "对象",
  full_dataset: "全表",
  derived_metric: "派生指标",
};

function firstDisplayText(...values: Array<string | null | undefined>) {
  const normalized = values.map((value) => String(value || "").trim()).filter(Boolean);
  return normalized.find((value) => CJK_TEXT_PATTERN.test(value)) || normalized[0] || "";
}

function methodFamilyLabel(method: MethodCatalogItem) {
  return firstDisplayText(method.family_label, METHOD_FAMILY_LABELS[method.family], method.family, "其他");
}

function methodOutputLabels(method: MethodCatalogItem) {
  const labels = method.output_labels?.length
    ? method.output_labels
    : (method.output_types || []).map((item) => METHOD_OUTPUT_LABELS[item] || item);
  return uniqueStrings(labels);
}

function methodRoleLabels(method: MethodCatalogItem) {
  const labels = method.role_labels?.length
    ? method.role_labels
    : (method.required_roles || []).map((item) => METHOD_ROLE_LABELS[item] || item);
  return uniqueStrings(labels);
}

function methodGoalText(method: MethodCatalogItem) {
  const outputs = methodOutputLabels(method).join("、");
  return firstDisplayText(
    method.goal_zh,
    method.goal,
    outputs ? `${methodFamilyLabel(method)}：输出 ${outputs}` : `${methodFamilyLabel(method)} 分析方法`,
  );
}

function buildMethodIndex(method: MethodCatalogItem): MethodIndexItem {
  const familyLabel = methodFamilyLabel(method);
  const displayTitle = methodDisplayTitle(method);
  const bundleTitle = methodBundleTitle(method);
  const outputLabel = methodOutputLabel(method);
  const goalText = methodGoalText(method);
  const outputLabels = methodOutputLabels(method);
  const roleLabels = methodRoleLabels(method);
  const searchText = uniqueStrings([
    method.name,
    method.name_zh,
    displayTitle,
    bundleTitle,
    outputLabel,
    goalText,
    ...outputLabels,
    ...roleLabels,
    method.family,
    familyLabel,
    method.goal,
    method.goal_zh,
    method.status,
    method.source,
    method.method_card_contract,
    ...(method.edit_capabilities?.editable_field_labels || []),
    ...(method.edit_capabilities?.selection_mode_labels || []).map((item) => item.label),
    ...(method.edit_capabilities?.run_control_labels || []),
    ...(method.usage_guidance || []).flatMap((item) => [item.title, item.detail]),
    ...(method.report_value_hooks || []),
  ])
    .join(" ")
    .toLowerCase();
  return {
    method,
    family: method.family,
    familyLabel,
    displayTitle,
    bundleTitle,
    outputLabel,
    goalText,
    outputLabels,
    roleLabels,
    searchText,
  };
}

function formatNumber(value: unknown) {
  if (typeof value !== "number") {
    return value == null ? "0" : String(value);
  }
  return new Intl.NumberFormat("zh-CN").format(value);
}

function formatValue(value: unknown) {
  if (value == null) return "-";
  if (typeof value === "number") return Number.isInteger(value) ? formatNumber(value) : value.toFixed(4);
  if (typeof value === "string" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function stringifySafe(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isSmartReport(value: unknown): value is SmartReport {
  return isRecord(value) && Array.isArray(value.sections);
}

function isStatsResult(value: unknown): value is StatsResult {
  return isRecord(value) && typeof value.title === "string" && "metrics" in value;
}

function autoAnalysisData(payload: StatsResult): AutoAnalysisData {
  return isRecord(payload.data) ? (payload.data as AutoAnalysisData) : {};
}

function stringFromRecord(record: Record<string, unknown> | undefined, key: string) {
  return String(record?.[key] || "").trim();
}

type RuntimeDownloadable = NonNullable<StatsResult["downloadables"]>[number];

type MethodPackageDisplayGroup = {
  key: string;
  primary: RuntimeDownloadable;
  items: RuntimeDownloadable[];
  label: string;
  family: string;
  totalRuns: number;
  collapsedRuns: number;
  packageRefs: string[];
  methodIds: string[];
};

function cleanMethodPackageLabel(value: unknown) {
  return String(value || "")
    .replace(/\.[a-z0-9]+$/i, "")
    .replace(/^\d+[-_\s]+/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function methodPackageDisplayLabel(item: RuntimeDownloadable) {
  return (
    cleanMethodPackageLabel(item.method_name_zh) ||
    cleanMethodPackageLabel(item.method_name) ||
    cleanMethodPackageLabel(item.name) ||
    cleanMethodPackageLabel(item.method_id) ||
    cleanMethodPackageLabel(item.package_ref) ||
    "method package"
  );
}

function methodPackageDisplayKey(item: RuntimeDownloadable) {
  const displayGroup = isRecord(item.display_group) ? item.display_group : {};
  const explicitKey = stringFromRecord(displayGroup, "display_key");
  if (explicitKey) {
    return explicitKey;
  }
  const family = cleanMethodPackageLabel(item.family || "unknown").toLowerCase();
  const label = methodPackageDisplayLabel(item).toLowerCase();
  return `${family || "unknown"}|${label || stringFromRecord(item, "package_ref") || item.path}`;
}

function numberFromRecord(record: Record<string, unknown> | undefined, key: string) {
  const value = Number(record?.[key] || 0);
  return Number.isFinite(value) ? value : 0;
}

function buildMethodPackageDisplayGroups(items: RuntimeDownloadable[]): MethodPackageDisplayGroup[] {
  const grouped = new Map<string, RuntimeDownloadable[]>();
  items.forEach((item) => {
    const key = methodPackageDisplayKey(item);
    grouped.set(key, [...(grouped.get(key) || []), item]);
  });
  return Array.from(grouped.entries()).map(([key, groupItems]) => {
    const primary = groupItems[0];
    const displayGroup = isRecord(primary.display_group) ? primary.display_group : {};
    const family = cleanMethodPackageLabel(primary.family || key.split("|")[0] || "method");
    const label = methodPackageDisplayLabel(primary);
    const packageRefs = Array.from(
      new Set(
        groupItems
          .map((item) => String(item.package_ref || item.path || ""))
          .filter((value) => value.trim()),
      ),
    );
    const methodIds = Array.from(
      new Set(
        groupItems
          .map((item) => String(item.method_id || ""))
          .filter((value) => value.trim()),
      ),
    );
    const totalRuns = Math.max(numberFromRecord(displayGroup, "total_runs"), groupItems.length);
    const collapsedRuns = Math.max(numberFromRecord(displayGroup, "collapsed_run_count"), totalRuns - 1, 0);
    return {
      key,
      primary,
      items: groupItems,
      label,
      family,
      totalRuns,
      collapsedRuns,
      packageRefs,
      methodIds,
    };
  });
}

function methodExecutions(payload: StatsResult): Array<Record<string, unknown>> {
  return (autoAnalysisData(payload).method_card_executions || []).filter(isRecord);
}

function methodRunResultKey(item: Pick<MethodRunResult, "method_id" | "method_run_id">) {
  return item.method_run_id || item.method_id;
}

function methodRunRuntimeStatusLabel(item: Pick<MethodRunResult, "runtime_status" | "status">) {
  if (item.runtime_status === "runtime_handoff_ready") return "runtime handoff ready";
  if (item.runtime_status === "runtime_blocked") return "runtime blocked";
  return item.runtime_status || item.status;
}

function methodRunResultFromRow(
  row: Record<string, unknown>,
  method: MethodCatalogItem | undefined,
  fallbackMethodId: string,
  ranAt: string,
  fallbackPayload?: unknown,
  fallbackLabel?: string,
  index = 0,
): MethodRunResult {
  const methodId = String(row.method_id || fallbackMethodId || method?.id || "").trim();
  const methodRunId = String(row.method_run_id || row.execution_id || "").trim() || `${methodId || "method"}__result_${index + 1}`;
  const selectionMode = String(row.selection_mode || "fields") as MethodRunSelectionMode | string;
  return {
    method_id: methodId,
    method_run_id: methodRunId,
    method_run_label: String(row.method_run_label || row.label || fallbackLabel || "").trim(),
    method_name: method?.name || methodId,
    method_name_zh: method?.name_zh || method?.name || methodId,
    status: String(row.status || "completed"),
    runtime_status: String(row.runtime_status || row.runtime_handoff_status || row.status || ""),
    local_preparation_status: String(row.local_preparation_status || row.preparation_status || row.status || ""),
    runtime_required: row.runtime_required === true || String(row.runtime_required || "").toLowerCase() === "true",
    runtime_executor: String(row.runtime_executor || "").trim(),
    runtime_job_id: String(row.runtime_job_id || "").trim(),
    runtime_manifest_path: String(row.runtime_manifest_path || "").trim(),
    runtime_error: String(row.runtime_error || "").trim(),
    source: method?.source || "lab",
    selection_mode: selectionMode,
    smart_merge_group: String(row.smart_merge_group || "").trim(),
    payload: Object.keys(row).length ? row : fallbackPayload,
    ran_at: ranAt,
  };
}

function materializeMethodRunResults({
  payload,
  methods,
  runSpecs,
}: {
  payload: StatsResult;
  methods: MethodCatalogItem[];
  runSpecs: MethodRunSpec[];
}): MethodRunResult[] {
  const rows = methodExecutions(payload);
  const now = new Date().toISOString();
  const byMethod = new Map(methods.map((method) => [method.id, method]));
  const rowsByRunId = new Map<string, Record<string, unknown>>();
  const rowsByMethodId = new Map<string, Record<string, unknown>[]>();

  for (const row of rows) {
    const methodId = String(row.method_id || "").trim();
    const runId = String(row.method_run_id || row.run_id || "").trim();
    if (runId) {
      rowsByRunId.set(runId, row);
    }
    if (methodId) {
      const list = rowsByMethodId.get(methodId) || [];
      list.push(row);
      rowsByMethodId.set(methodId, list);
    }
  }

  const results: MethodRunResult[] = [];
  const usedRows = new Set<Record<string, unknown>>();
  const specs = runSpecs.length
    ? runSpecs
    : rows.map((row, index) => ({
        run_id: String(row.method_run_id || row.run_id || row.method_id || `method__run_${index + 1}`),
        method_id: String(row.method_id || ""),
        label: String(row.method_run_label || row.label || row.method_id || `Run ${index + 1}`),
        selection_mode: (String(row.selection_mode || "fields") as MethodRunSelectionMode) || "fields",
        field_bindings: {},
        object_selection: undefined,
        smart_merge_group: String(row.smart_merge_group || ""),
      }));

  for (const [index, spec] of specs.entries()) {
    const byRunId = rowsByRunId.get(spec.run_id);
    const candidates = [
      byRunId,
      ...((rowsByMethodId.get(spec.method_id) || []).filter((row) => row !== byRunId)),
    ].filter((row): row is Record<string, unknown> => isRecord(row) && !usedRows.has(row));
    const row = candidates[0];
    if (row) {
      usedRows.add(row);
    }
    const syntheticRow = row || {
      method_id: spec.method_id,
      method_run_id: spec.run_id,
      method_run_label: spec.label,
      selection_mode: spec.selection_mode,
      smart_merge_group: spec.smart_merge_group || "",
      status: "completed",
    };
    results.push(methodRunResultFromRow(syntheticRow, byMethod.get(spec.method_id), spec.method_id, now, row ?? payload, spec.label, index));
  }

  for (const row of rows) {
    if (usedRows.has(row)) continue;
    results.push(methodRunResultFromRow(row, byMethod.get(String(row.method_id || "").trim()), String(row.method_id || ""), now, payload, String(row.method_run_label || row.label || ""), results.length));
  }

  return results;
}

function downloadJsonFile(fileName: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function copyJsonToClipboard(payload: unknown) {
  const text = JSON.stringify(payload, null, 2);
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

function slugFilePart(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 96) || "report-part";
}

function datasetLabel(dataset?: DatasetItem) {
  if (!dataset) return "未选择数据集";
  return dataset.name || dataset.filename || dataset.dataset_id;
}

function datasetSheetName(dataset?: DatasetItem) {
  return dataset?.active_sheet || dataset?.sheets?.[0]?.name || "";
}

function uniqueStrings(values: Array<string | null | undefined>) {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const normalized = String(value || "").trim();
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
}

function clampMethodIds(methodIds: string[], limit = MAX_SELECTED_METHOD_RUNS) {
  return uniqueStrings(methodIds).slice(0, limit);
}

function columnNames(dataset?: DatasetItem) {
  return uniqueStrings([
    ...(dataset?.column_summaries || []).map((summary) => summary.name),
    ...(dataset?.numeric_columns || []),
    ...(dataset?.categorical_columns || []),
    ...(dataset?.datetime_columns || []),
    ...Object.keys(dataset?.sample_rows?.[0] || {}),
  ]);
}

function datasetCellCount(dataset?: DatasetItem) {
  const rows = Number(dataset?.row_count || 0);
  const columns = Number(dataset?.column_count || 0);
  return Math.max(0, rows) * Math.max(0, columns);
}

function shouldAutoPreprocessDataset(dataset?: DatasetItem) {
  const rows = Number(dataset?.row_count || 0);
  const cells = datasetCellCount(dataset);
  if (!rows && !cells) return true;
  return rows <= AUTO_PREPROCESS_MAX_ROWS && cells <= AUTO_PREPROCESS_MAX_CELLS;
}

function largeDatasetReadyStatus(dataset?: DatasetItem) {
  return `Large dataset loaded: ${datasetLabel(dataset)} (${formatNumber(dataset?.row_count)} rows / ${formatNumber(dataset?.column_count)} columns). Auto preprocessing was skipped; click the run button when ready.`;
}

function inferDefaultFieldSelection(dataset?: DatasetItem): FieldSelection {
  const numeric = dataset?.numeric_columns || [];
  const categorical = dataset?.categorical_columns || [];
  const datetimes = dataset?.datetime_columns || [];
  const summaries = dataset?.column_summaries || [];
  const entityCandidate =
    summaries.find((summary) => !numeric.includes(summary.name) && !datetimes.includes(summary.name) && Number(summary.unique_count || 0) > 0)?.name ||
    categorical[0] ||
    "";
  const group = categorical[0] || entityCandidate;
  const target = numeric[0] || "";
  const features = uniqueStrings(numeric.filter((item) => item !== target).slice(0, 4));
  const second = features[0] || target;
  const third = features[1] || target;
  return {
    target,
    features,
    group,
    label: entityCandidate || group,
    time: datetimes[0] || "",
    bubble: { x: target, y: second, size: third, color: group, label: entityCandidate || group },
    quadrant: { x: target, y: second, group, label: entityCandidate || group },
  };
}

function defaultDerivedMetricDrafts(dataset?: DatasetItem): DerivedMetricEdit[] {
  const numeric = (dataset?.numeric_columns || []).slice(0, 6);
  const datetimes = (dataset?.datetime_columns || []).slice(0, 2);
  const drafts: DerivedMetricEdit[] = [];
  if (numeric[0]) {
    drafts.push({
      field: `自定义指标_${numeric[0]}`,
      display_name: `${numeric[0]}指标`,
      formula: `${numeric[0]} (直接取值)`,
      source_fields: [numeric[0]],
      recipe_id: "custom",
      selected: true,
      custom: true,
    });
  }
  for (const column of numeric.slice(0, 3)) {
    drafts.push({
      field: `标准化_${column}`,
      display_name: `${column}标准化`,
      formula: `zscore(${column})`,
      source_fields: [column],
      recipe_id: "zscore",
      selected: true,
      custom: true,
    });
    drafts.push({
      field: `百分位_${column}`,
      display_name: `${column}百分位`,
      formula: `percentile_rank(${column})`,
      source_fields: [column],
      recipe_id: "percentile_rank",
      selected: true,
      custom: true,
    });
  }
  for (let index = 0; index + 1 < numeric.length && index < 3; index += 1) {
    const left = numeric[index];
    const right = numeric[index + 1];
    drafts.push({
      field: `${left}_${right}比值`,
      display_name: `${left}${right}比值`,
      formula: `${left} / ${right}`,
      source_fields: [left, right],
      recipe_id: "ratio",
      selected: true,
      custom: true,
    });
    drafts.push({
      field: `${left}_${right}差值`,
      display_name: `${left}${right}差值`,
      formula: `${left} - ${right}`,
      source_fields: [left, right],
      recipe_id: "difference",
      selected: true,
      custom: true,
    });
    drafts.push({
      field: `${left}_${right}占比`,
      display_name: `${left}占${left}+${right}比重`,
      formula: `${left} / (${left} + ${right})`,
      source_fields: [left, right],
      recipe_id: "share",
      selected: true,
      custom: true,
    });
  }
  for (const column of datetimes) {
    drafts.push({
      field: `月份_${column}`,
      display_name: `${column}月份`,
      formula: `month(${column})`,
      source_fields: [column],
      recipe_id: "calendar_month",
      selected: true,
      custom: true,
    });
    drafts.push({
      field: `星期_${column}`,
      display_name: `${column}星期`,
      formula: `dayofweek(${column})`,
      source_fields: [column],
      recipe_id: "calendar_dayofweek",
      selected: true,
      custom: true,
    });
  }
  return drafts;
}

function selectedDerivedMetricFields(derivedMetricEdits: DerivedMetricEdit[]) {
  return uniqueStrings(derivedMetricEdits.filter((item) => item.selected).map((item) => item.field));
}

function allDerivedMetricFields(derivedMetricEdits: DerivedMetricEdit[]) {
  return uniqueStrings(derivedMetricEdits.map((item) => item.field));
}

function methodBindingOptions(dataset?: DatasetItem, derivedMetricEdits: DerivedMetricEdit[] = []) {
  return uniqueStrings([
    ...(dataset?.numeric_columns || []),
    ...selectedDerivedMetricFields(derivedMetricEdits),
    ...allDerivedMetricFields(derivedMetricEdits),
  ]);
}

function methodSearchText(method: MethodCatalogItem) {
  return [
    method.id,
    method.name,
    method.name_zh,
    method.family,
    method.family_label,
    method.bundle_title,
    method.bundle_title_zh,
    method.bundle_title_en,
    method.parent_method_title,
    method.method_concept_label,
    method.method_output_label,
    method.submethod_label,
    method.submethod_title,
    method.output_variant,
    method.goal,
    method.goal_zh,
    method.card_description,
    ...(method.output_types || []),
    ...(method.output_labels || []),
    ...(method.required_roles || []),
    ...(method.role_labels || []),
    ...(method.card_tags || []),
  ].join(" ").toLowerCase();
}

function columnSummaryFor(dataset: DatasetItem | undefined, column: string) {
  return (dataset?.column_summaries || []).find((summary) => summary.name === column);
}

function columnSemanticText(dataset: DatasetItem | undefined, column: string) {
  const summary = columnSummaryFor(dataset, column);
  return [
    column,
    summary?.dtype,
    ...(summary?.sample_values || []).slice(0, 4).map((value) => String(value || "")),
  ].join(" ").toLowerCase();
}

function rankColumnCandidates(
  candidates: string[],
  dataset: DatasetItem | undefined,
  options: {
    preferred?: string[];
    avoid?: string[];
    include?: RegExp[];
    exclude?: RegExp[];
    lowCardinalityBonus?: boolean;
    highCardinalityBonus?: boolean;
  } = {},
) {
  const preferred = new Set(uniqueStrings(options.preferred || []));
  const avoid = new Set(uniqueStrings(options.avoid || []));
  const ranked = uniqueStrings(candidates)
    .filter((column) => !avoid.has(column))
    .map((column, index) => {
      const text = columnSemanticText(dataset, column);
      const summary = columnSummaryFor(dataset, column);
      let score = Math.max(0, 120 - index);
      if (preferred.has(column)) score += 900;
      for (const pattern of options.include || []) {
        if (pattern.test(text)) score += 80;
      }
      for (const pattern of options.exclude || []) {
        if (pattern.test(text)) score -= 180;
      }
      const uniqueCount = Number(summary?.unique_count || 0);
      if (options.lowCardinalityBonus && uniqueCount > 1 && uniqueCount <= 40) score += 55;
      if (options.highCardinalityBonus && uniqueCount > 20) score += 45;
      const missingRatio = Number(summary?.missing_ratio || 0);
      if (missingRatio > 0) score -= Math.min(70, missingRatio * 100);
      return { column, score };
    })
    .sort((left, right) => right.score - left.score);
  return ranked.map((item) => item.column);
}

function firstRankedColumn(
  candidates: string[],
  dataset: DatasetItem | undefined,
  options: Parameters<typeof rankColumnCandidates>[2] = {},
) {
  return rankColumnCandidates(candidates, dataset, options)[0] || "";
}

function bindingRoleValue(binding: MethodFieldBinding, key: keyof MethodFieldBinding) {
  const value = binding[key];
  if (Array.isArray(value)) return value.filter(Boolean).join(", ");
  return String(value || "");
}

function fieldBindingRoleLabel(key: keyof MethodFieldBinding | string, preferObjectMode = false) {
  return {
    target: preferObjectMode ? "对象要分析的指标" : "结果指标",
    field: "单字段指标",
    x: "横轴 / 对比字段",
    y: "纵轴 / 结果字段",
    features: "解释字段",
    group: preferObjectMode ? "对象分组口径" : "分组口径",
    label: preferObjectMode ? "对象名称列" : "名称/标签列",
    entity: "对象名称列",
    time: "时间口径",
    derived_metric: "派生指标",
    derived_metrics: "派生指标",
    pair: "字段对",
  }[key] || String(key);
}

function availableBindingFields(dataset?: DatasetItem, derivedMetrics: DerivedMetricEdit[] = []) {
  return new Set(
    uniqueStrings([
      ...columnNames(dataset),
      ...selectedDerivedMetricFields(derivedMetrics),
      ...allDerivedMetricFields(derivedMetrics),
    ]),
  );
}

function pruneMethodFieldBinding(binding: MethodFieldBinding, dataset?: DatasetItem, derivedMetrics: DerivedMetricEdit[] = []) {
  const available = availableBindingFields(dataset, derivedMetrics);
  if (!available.size) return cleanMethodFieldBinding(binding);
  const pruned: MethodFieldBinding = {};
  for (const [key, value] of Object.entries(binding) as Array<[keyof MethodFieldBinding, string | string[] | undefined]>) {
    if (key === "dataset_scope") {
      if (value && !Array.isArray(value)) pruned.dataset_scope = value;
      continue;
    }
    if (Array.isArray(value)) {
      const next = value.filter((item) => available.has(item));
      if (next.length) pruned[key] = next as never;
      continue;
    }
    if (value && available.has(value)) {
      pruned[key] = value as never;
    }
  }
  return cleanMethodFieldBinding(pruned);
}

function makeSmartMethodBindingPlan(
  method: MethodCatalogItem,
  fieldSelection: FieldSelection,
  dataset?: DatasetItem,
  derivedMetrics?: DerivedMetricEdit[],
): SmartMethodBindingPlan {
  const allColumns = columnNames(dataset);
  const numeric = uniqueStrings(dataset?.numeric_columns || []);
  const categorical = uniqueStrings(dataset?.categorical_columns || []);
  const datetimes = uniqueStrings(dataset?.datetime_columns || []);
  const summaries = dataset?.column_summaries || [];
  const nonNumeric = allColumns.filter((column) => !numeric.includes(column));
  const derivedCandidates = uniqueStrings([
    ...selectedDerivedMetricFields(derivedMetrics || []),
    ...allDerivedMetricFields(derivedMetrics || []),
  ]);
  const metricCandidates = uniqueStrings([...numeric, ...derivedCandidates]);
  const roles = new Set((method.required_roles || []).map((role) => String(role)));
  const outputType = methodOutputType(method);
  const methodText = methodSearchText(method);
  const preferredTarget = uniqueStrings([fieldSelection.target, fieldSelection.bubble.y, fieldSelection.quadrant.y]);
  const preferredGroup = uniqueStrings([fieldSelection.group, fieldSelection.bubble.color, fieldSelection.quadrant.group]);
  const preferredLabel = uniqueStrings([fieldSelection.label, fieldSelection.bubble.label, fieldSelection.quadrant.label]);
  const preferredTime = uniqueStrings([fieldSelection.time]);
  const target =
    firstRankedColumn(metricCandidates, dataset, {
      preferred: preferredTarget,
      include: [/revenue|sales|amount|price|cost|profit|margin|score|rate|value|total|count|index|收入|销售|金额|价格|成本|利润|得分|评分|分数|数量|总额|指标|占比|比例/],
      exclude: [/id|编号|代码|编码|phone|mobile|tel|身份证/],
    }) ||
    firstRankedColumn(allColumns, dataset, { preferred: preferredTarget });
  const secondaryNumeric = firstRankedColumn(metricCandidates, dataset, {
    preferred: uniqueStrings([...fieldSelection.features, fieldSelection.bubble.x, fieldSelection.quadrant.x]),
    avoid: [target],
    include: [/quantity|volume|rate|score|value|total|count|index|数量|规模|比例|评分|指数|指标/],
    exclude: [/id|编号|代码|编码|phone|mobile|tel|身份证/],
  });
  const featurePool = uniqueStrings([
    ...fieldSelection.features,
    ...rankColumnCandidates(metricCandidates, dataset, {
      avoid: [target],
      include: [/score|rate|value|amount|price|cost|profit|count|index|指标|比例|金额|价格|数量|得分/],
      exclude: [/id|编号|代码|编码|phone|mobile|tel|身份证/],
    }),
    ...allColumns.filter((column) => column !== target),
  ]);
  const group =
    firstRankedColumn(uniqueStrings([...categorical, ...nonNumeric, ...allColumns]), dataset, {
      preferred: preferredGroup,
      include: [/category|type|segment|region|city|province|country|channel|department|team|group|class|level|status|类别|类型|分组|地区|城市|省份|国家|渠道|部门|团队|等级|状态|品类/],
      exclude: [/id|编号|代码|编码|date|time|日期|时间/],
      lowCardinalityBonus: true,
    }) || "";
  const label =
    firstRankedColumn(uniqueStrings([...nonNumeric, ...categorical, ...allColumns]), dataset, {
      preferred: preferredLabel,
      include: [/name|title|label|customer|user|client|company|product|store|brand|姓名|名称|名字|标题|客户|用户|公司|企业|产品|门店|品牌|对象/],
      exclude: [/date|time|日期|时间/],
      highCardinalityBonus: true,
    }) ||
    group;
  const time =
    firstRankedColumn(datetimes.length ? datetimes : allColumns, dataset, {
      preferred: preferredTime,
      include: [/date|time|year|month|week|day|quarter|period|日期|时间|年份|年度|月份|周|季度|期间/],
      exclude: [/id|编号|代码|编码/],
    }) || "";
  const selectedDerived = uniqueStrings(derivedCandidates.length ? derivedCandidates : [target]).slice(
    0,
    method.family === "visual" ? 2 : method.family === "report_part" ? 1 : 4,
  );
  const binding: MethodFieldBinding = {};
  const controlHints = new Set(method.binding_controls || []);
  const pairChartHint = /scatter|bubble|quadrant|correl|association|heatmap|matrix|x-y|xy|散点|气泡|象限|相关|关联|矩阵/.test(methodText);
  const wantsPair =
    controlHints.has("x") ||
    controlHints.has("y") ||
    roles.has("field_pair") ||
    ["association", "comparison", "causal", "categorical_association", "mean_tests", "nonparametric"].includes(method.family) ||
    methodText.includes("compare") ||
    /对比/.test(methodText) ||
    pairChartHint;
  const wantsFieldSet = roles.has("field_set") || ["regression", "machine_learning", "multivariate", "psychometrics"].includes(method.family);
  const pairPriority =
    wantsPair &&
    (!wantsFieldSet ||
      controlHints.has("x") ||
      controlHints.has("y") ||
      ["association", "comparison", "causal", "categorical_association", "mean_tests", "nonparametric"].includes(method.family) ||
      pairChartHint ||
      /compare|对比/.test(methodText));
  const wantsSingle = roles.has("single_field") || method.family === "descriptive" || method.family === "distribution_assumption";
  const wantsTime = roles.has("time_window") || roles.has("time") || method.family === "time_series" || /line|trend|time|date|calendar|timeline|时间|趋势/.test(methodText);
  const wantsGroup = roles.has("grouped") || roles.has("categorical") || roles.has("dimension") || roles.has("group") || /bar|column|stack|pie|donut|box|violin|heatmap|funnel|map|分类|分组|对比/.test(methodText);
  const wantsEntity = roles.has("entity_level") || roles.has("entity") || methodRecommendedSelectionMode(method) === "object" || /object|entity|customer|user|product|rank|对象|客户|用户|产品|排行/.test(methodText);
  const wantsDerived = roles.has("derived_metric") || ["causal", "time_series"].includes(method.family) || /derived|ratio|rate|growth|share|派生|比率|增长|占比/.test(methodText);

  if (method.family === "visual" && /bubble|气泡/.test(methodText)) {
    binding.x = fieldSelection.bubble.x || secondaryNumeric || target;
    binding.y = fieldSelection.bubble.y || target || secondaryNumeric;
    binding.target = binding.y;
    binding.features = uniqueStrings([binding.x, binding.y, fieldSelection.bubble.size, ...featurePool]).filter((column) => column !== binding.target).slice(0, 6);
    binding.group = fieldSelection.bubble.color || group;
    binding.label = fieldSelection.bubble.label || label;
  } else if (method.family === "visual" && /quadrant|象限/.test(methodText)) {
    binding.x = fieldSelection.quadrant.x || secondaryNumeric || target;
    binding.y = fieldSelection.quadrant.y || target || secondaryNumeric;
    binding.target = binding.y;
    binding.features = uniqueStrings([binding.x, binding.y, ...featurePool]).filter((column) => column !== binding.target).slice(0, 6);
    binding.group = fieldSelection.quadrant.group || group;
    binding.label = fieldSelection.quadrant.label || label;
  } else if (wantsTime) {
    binding.time = time;
    binding.target = target;
    binding.features = featurePool.filter((column) => column !== target).slice(0, 5);
    if (wantsGroup) binding.group = group;
  } else if (pairPriority) {
    binding.x = secondaryNumeric || target;
    binding.y = target && target !== binding.x ? target : featurePool.find((column) => column !== binding.x) || target;
    binding.target = binding.y || target;
    binding.features = uniqueStrings([binding.x, binding.y, ...featurePool]).filter((column) => column !== binding.target).slice(0, 6);
  } else if (wantsFieldSet) {
    binding.target = target;
    binding.features = featurePool.filter((column) => column !== target).slice(0, 8);
  } else if (wantsPair) {
    binding.x = secondaryNumeric || target;
    binding.y = target && target !== binding.x ? target : featurePool.find((column) => column !== binding.x) || target;
    binding.target = binding.y || target;
    binding.features = uniqueStrings([binding.x, binding.y, ...featurePool]).filter((column) => column !== binding.target).slice(0, 6);
  } else if (wantsSingle) {
    binding.field = target || group || label;
    binding.target = target || binding.field;
  } else {
    binding.target = target;
    binding.features = featurePool.filter((column) => column !== target).slice(0, 5);
  }

  if (wantsGroup && group) binding.group = binding.group || group;
  if (wantsEntity && label) {
    binding.entity = binding.entity || label;
    binding.label = binding.label || label;
  }
  if (wantsTime && time) binding.time = binding.time || time;
  if (wantsPair && binding.x && binding.y === binding.x) {
    const alternatePairField = uniqueStrings([...featurePool, target, ...selectedDerived]).find((column) => column && column !== binding.x);
    if (alternatePairField) {
      binding.y = alternatePairField;
      binding.target = alternatePairField;
    }
  }
  if (wantsDerived && selectedDerived.length) {
    binding.derived_metrics = selectedDerived;
    binding.derived_metric = selectedDerived[0];
  }
  if (!binding.target && target) binding.target = target;
  if (!binding.features?.length && featurePool.length && !wantsSingle) {
    binding.features = featurePool.filter((column) => column !== binding.target).slice(0, 4);
  }
  if (!binding.group && wantsGroup && categorical.length) binding.group = categorical[0];
  if (!binding.label && wantsEntity && label) binding.label = label;
  if (!binding.entity && wantsEntity && label) binding.entity = label;

  const cleaned = cleanMethodFieldBinding(binding);
  const roleLabels: Array<[keyof MethodFieldBinding, string, boolean]> = [
    ["target", fieldBindingRoleLabel("target", wantsEntity), Boolean(cleaned.target)],
    ["field", fieldBindingRoleLabel("field", wantsEntity), Boolean(cleaned.field)],
    ["x", fieldBindingRoleLabel("x", wantsEntity), Boolean(cleaned.x)],
    ["y", fieldBindingRoleLabel("y", wantsEntity), Boolean(cleaned.y)],
    ["features", fieldBindingRoleLabel("features", wantsEntity), Boolean(cleaned.features?.length)],
    ["group", fieldBindingRoleLabel("group", wantsEntity), Boolean(cleaned.group)],
    ["label", fieldBindingRoleLabel("label", wantsEntity), Boolean(cleaned.label)],
    ["entity", fieldBindingRoleLabel("entity", wantsEntity), Boolean(cleaned.entity)],
    ["time", fieldBindingRoleLabel("time", wantsEntity), Boolean(cleaned.time)],
    ["derived_metrics", fieldBindingRoleLabel("derived_metrics", wantsEntity), Boolean(cleaned.derived_metrics?.length)],
  ];
  const presentRoles = roleLabels
    .filter(([, , present]) => present)
    .map(([key, labelText]) => {
      const value = bindingRoleValue(cleaned, key);
      const confidence: SmartMethodBindingRole["confidence"] =
        preferredTarget.includes(value) || preferredGroup.includes(value) || preferredLabel.includes(value) || preferredTime.includes(value)
          ? "high"
          : value
            ? "medium"
            : "fallback";
      return { key, label: labelText, value, confidence };
    });
  const requiredChecks: Array<[string, boolean]> = [
    ["target", Boolean(cleaned.target || cleaned.field || cleaned.y)],
    ["pair", !wantsPair || Boolean(cleaned.x && cleaned.y && cleaned.x !== cleaned.y)],
    ["features", !wantsFieldSet || Boolean(cleaned.features?.length)],
    ["group", !wantsGroup || Boolean(cleaned.group)],
    ["time", !wantsTime || Boolean(cleaned.time)],
    ["entity", !wantsEntity || Boolean(cleaned.entity || cleaned.label)],
  ];
  const missing = requiredChecks.filter(([, ok]) => !ok).map(([key]) => key);
  const confidence = Math.max(0, Math.min(100, Math.round(((requiredChecks.length - missing.length) / requiredChecks.length) * 100)));
  const reasons = uniqueStrings([
    `${methodFamilyLabel(method)} / ${methodOutputLabel(method)}`,
    methodRoleLabels(method).slice(0, 3).join(", "),
    target ? `${fieldBindingRoleLabel("target", wantsEntity)}:${target}` : "",
    group ? `${fieldBindingRoleLabel("group", wantsEntity)}:${group}` : "",
    time ? `${fieldBindingRoleLabel("time", wantsEntity)}:${time}` : "",
  ]).slice(0, 5);
  return { binding: cleaned, roles: presentRoles, reasons, missing, confidence };
}

function smartMethodBindingSummary(plan: SmartMethodBindingPlan) {
  if (!plan.roles.length) return "还没有匹配到可用字段";
  return plan.roles
    .slice(0, 5)
    .map((role) => `${role.label}: ${role.value}`)
    .join(" · ");
}

function cleanMethodFieldBinding(binding: MethodFieldBinding) {
  const cleaned: MethodFieldBinding = {};
  const derivedMetrics = uniqueStrings([
    ...((Array.isArray(binding.derived_metrics) ? binding.derived_metrics : []) as string[]),
    ...(binding.derived_metric ? [binding.derived_metric] : []),
  ]);
  if (derivedMetrics.length) {
    cleaned.derived_metrics = derivedMetrics;
    cleaned.derived_metric = derivedMetrics[0];
  }
  for (const [key, value] of Object.entries(binding) as Array<[keyof MethodFieldBinding, string | string[] | undefined]>) {
    if (key === "derived_metric" || key === "derived_metrics") continue;
    if (Array.isArray(value)) {
      const next = uniqueStrings(value);
      if (next.length) cleaned[key] = next as never;
      continue;
    }
    if (value) cleaned[key] = value as never;
  }
  return cleaned;
}

function resolveMethodFieldBindings({
  dataset,
  derivedMetricEdits,
  fieldSelection,
  methods,
  manualBindings,
  selectedIds,
}: {
  dataset?: DatasetItem;
  derivedMetricEdits: DerivedMetricEdit[];
  fieldSelection: FieldSelection;
  methods: MethodCatalogItem[];
  manualBindings: MethodFieldBindings;
  selectedIds: string[];
}) {
  const selectedSet = new Set(selectedIds);
  const resolved: MethodFieldBindings = {};
  for (const method of methods) {
    if (!selectedSet.has(method.id)) continue;
    const merged = cleanMethodFieldBinding({
      ...methodDefaultBinding(method, fieldSelection, dataset, derivedMetricEdits),
      ...(method.field_bindings || {}),
      ...(manualBindings[method.id] || {}),
    });
    if (Object.keys(merged).length) {
      resolved[method.id] = merged;
    }
  }
  return resolved;
}

function cleanFieldSelection(selection: FieldSelection) {
  const payload: Record<string, unknown> = {};
  if (selection.target) payload.target = selection.target;
  if (selection.features.length) payload.features = selection.features;
  if (selection.group) payload.group = selection.group;
  if (selection.label) payload.label = selection.label;
  if (selection.time) payload.time = selection.time;
  const bubble = Object.fromEntries(Object.entries(selection.bubble).filter(([, value]) => value));
  const quadrant = Object.fromEntries(Object.entries(selection.quadrant).filter(([, value]) => value));
  if (Object.keys(bubble).length) payload.bubble = bubble;
  if (Object.keys(quadrant).length) payload.quadrant = quadrant;
  return payload;
}

function cleanDerivedMetricEdits(edits: DerivedMetricEdit[]) {
  return edits
    .filter((edit) => edit.selected && edit.field.trim())
    .map((edit) => ({
      field: edit.field.trim(),
      display_name: edit.display_name.trim() || edit.field.trim(),
      display_name_zh: edit.display_name.trim() || edit.field.trim(),
      formula: edit.formula.trim() || edit.field.trim(),
      source_fields: edit.source_fields.filter(Boolean),
      recipe_id: edit.recipe_id || "custom",
      manual_rename: true,
    }));
}

function cleanMethodFieldBindings(bindings: MethodFieldBindings) {
  const payload: MethodFieldBindings = {};
  for (const [methodId, binding] of Object.entries(bindings)) {
    const cleaned = cleanMethodFieldBinding(binding);
    if (Object.keys(cleaned).length) payload[methodId] = cleaned;
  }
  return payload;
}

function cleanMethodStatisticalOptions(options?: MethodStatisticalOptions | null) {
  const cleaned: MethodStatisticalOptions = {};
  if (!options) return cleaned;
  if (typeof options.alpha === "number" && Number.isFinite(options.alpha)) {
    cleaned.alpha = Math.min(0.2, Math.max(0.0001, options.alpha));
  }
  if (options.hypothesis === "two-sided" || options.hypothesis === "larger" || options.hypothesis === "smaller") {
    cleaned.hypothesis = options.hypothesis;
  }
  if (typeof options.test_value === "number" && Number.isFinite(options.test_value)) {
    cleaned.test_value = Math.min(1_000_000_000, Math.max(-1_000_000_000, options.test_value));
  }
  if (typeof options.population_std === "number" && Number.isFinite(options.population_std) && options.population_std > 0) {
    cleaned.population_std = Math.min(1_000_000_000, options.population_std);
  }
  if (typeof options.components === "number" && Number.isFinite(options.components)) {
    cleaned.components = Math.min(12, Math.max(1, Math.round(options.components)));
  }
  if (typeof options.clusters === "number" && Number.isFinite(options.clusters)) {
    cleaned.clusters = Math.min(12, Math.max(2, Math.round(options.clusters)));
  }
  if (typeof options.window === "number" && Number.isFinite(options.window)) {
    cleaned.window = Math.min(90, Math.max(2, Math.round(options.window)));
  }
  if (typeof options.lag === "number" && Number.isFinite(options.lag)) {
    cleaned.lag = Math.min(120, Math.max(1, Math.round(options.lag)));
  }
  if (typeof options.regularization_strength === "number" && Number.isFinite(options.regularization_strength)) {
    cleaned.regularization_strength = Math.min(100, Math.max(0.0001, options.regularization_strength));
  }
  if (typeof options.l1_ratio === "number" && Number.isFinite(options.l1_ratio)) {
    cleaned.l1_ratio = Math.min(1, Math.max(0, options.l1_ratio));
  }
  if (typeof options.quantile === "number" && Number.isFinite(options.quantile)) {
    cleaned.quantile = Math.min(0.95, Math.max(0.05, options.quantile));
  }
  if (typeof options.bootstrap_iterations === "number" && Number.isFinite(options.bootstrap_iterations)) {
    cleaned.bootstrap_iterations = Math.min(10000, Math.max(100, Math.round(options.bootstrap_iterations)));
  }
  if (options.metric_type === "auto" || options.metric_type === "continuous" || options.metric_type === "binary") {
    cleaned.metric_type = options.metric_type;
  }
  if (options.success_value?.trim()) cleaned.success_value = options.success_value.trim();
  if (options.group_a?.trim()) cleaned.group_a = options.group_a.trim();
  if (options.group_b?.trim()) cleaned.group_b = options.group_b.trim();
  return cleaned;
}

function cleanMethodRunSpecs(runSpecs: MethodRunSpec[]) {
  return runSpecs
    .filter((spec) => spec.method_id && spec.run_id)
    .map((spec) => ({
      run_id: spec.run_id,
      method_id: spec.method_id,
      label: spec.label.trim() || spec.method_id,
      bundle_run_id: spec.bundle_run_id?.trim() || "",
      bundle_title: spec.bundle_title?.trim() || "",
      selection_mode: spec.selection_mode,
      field_bindings: cleanMethodFieldBinding(spec.field_bindings),
      object_selection: spec.object_selection
        ? {
            ...spec.object_selection,
            object_keys: uniqueStrings(spec.object_selection.object_keys || []),
            filter_field:
              (spec.object_selection.filter_field || spec.object_selection.label_key || spec.object_selection.group_key || "").trim(),
            filter_values: uniqueStrings(spec.object_selection.filter_values || spec.object_selection.object_keys || []),
            filter_operator: spec.object_selection.filter_operator || "in",
          }
        : undefined,
      smart_merge_group: spec.smart_merge_group?.trim() || "",
      statistical_options: cleanMethodStatisticalOptions(spec.statistical_options),
    }))
    .map((spec) => ({
      ...spec,
      field_bindings: spec.field_bindings,
      ...(spec.object_selection ? { object_selection: spec.object_selection } : {}),
      ...(spec.bundle_run_id ? { bundle_run_id: spec.bundle_run_id } : {}),
      ...(spec.bundle_title ? { bundle_title: spec.bundle_title } : {}),
      ...(spec.smart_merge_group ? { smart_merge_group: spec.smart_merge_group } : {}),
      ...(Object.keys(spec.statistical_options).length ? { statistical_options: spec.statistical_options } : {}),
    }));
}

function methodRunSpecsForMethods(methodRunSpecs: MethodRunSpec[], methodIds: string[]) {
  const wanted = new Set(methodIds);
  return methodRunSpecs.filter((spec) => wanted.has(spec.method_id));
}

function methodIdsFromRunSpecs(runSpecs: MethodRunSpec[]) {
  return uniqueStrings(runSpecs.map((spec) => spec.method_id));
}

function methodIdsFromSetAndRuns(selectedIds: Set<string>, runSpecs: MethodRunSpec[]) {
  const runMethodIds = methodIdsFromRunSpecs(runSpecs);
  return new Set(runMethodIds.length ? runMethodIds : [...selectedIds]);
}

function methodRunCountById(runSpecs: MethodRunSpec[], methodId: string) {
  return runSpecs.filter((spec) => spec.method_id === methodId).length;
}

function methodDefaultBinding(method: MethodCatalogItem, fieldSelection: FieldSelection, dataset?: DatasetItem, derivedMetrics?: DerivedMetricEdit[]) {
  return makeSmartMethodBindingPlan(method, fieldSelection, dataset, derivedMetrics).binding;
}

function methodNameSegments(method: MethodCatalogItem) {
  return String(firstDisplayText(method.name_zh, method.submethod_title, method.name, method.id))
    .split(METHOD_NAME_SEPARATOR)
    .map((segment) => segment.trim())
    .filter(Boolean);
}

function methodProfessionalTitle(method: MethodCatalogItem) {
  return firstDisplayText(method.bundle_title_en, method.bundle_title, method.name, method.id);
}

function methodConceptTitle(method: MethodCatalogItem) {
  if (method.source === "statistical_catalog") {
    return methodProfessionalTitle(method);
  }
  const segments = methodNameSegments(method);
  return firstDisplayText(
    methodProfessionalTitle(method),
    method.method_concept_label,
    method.bundle_title_zh,
    method.parent_method_title,
    CJK_TEXT_PATTERN.test(method.bundle_title || "") ? method.bundle_title : "",
    segments[1],
    segments.slice(1, 2).join(METHOD_NAME_SEPARATOR),
    method.name,
    method.id,
  );
}

function methodBundleTitle(method: MethodCatalogItem) {
  if (method.source === "statistical_catalog") {
    return methodProfessionalTitle(method);
  }
  const segments = methodNameSegments(method);
  const slice = segments.slice(0, Math.min(METHOD_BUNDLE_SEGMENT_COUNT, segments.length));
  return firstDisplayText(
    methodProfessionalTitle(method),
    method.bundle_title_zh,
    method.parent_method_title,
    methodConceptTitle(method),
    CJK_TEXT_PATTERN.test(method.bundle_title || "") ? method.bundle_title : "",
    slice.join(METHOD_NAME_SEPARATOR),
    method.bundle_title,
    method.name_zh,
    method.name,
    method.id,
  );
}

function methodBundleKey(method: MethodCatalogItem) {
  return method.parent_method_id || method.bundle_id || method.base_method_id || method.id || methodBundleTitle(method);
}

function methodOutputType(method: MethodCatalogItem) {
  return String(method.output_variant || method.output_types?.[0] || "").trim();
}

function methodOutputLabel(method: MethodCatalogItem) {
  return firstDisplayText(method.submethod_label, method.method_output_label, methodOutputLabels(method)[0], method.output_types?.[0], "通用结果");
}

function methodDisplayTitle(method: MethodCatalogItem) {
  if (method.source === "statistical_catalog") {
    return methodProfessionalTitle(method);
  }
  return firstDisplayText(methodProfessionalTitle(method), methodBundleTitle(method), method.submethod_title, method.name_zh, method.name, method.id);
}

function methodSubmethodTitle(method: MethodCatalogItem) {
  return firstDisplayText(
    method.submethod_title,
    [methodBundleTitle(method), methodOutputLabel(method)].filter(Boolean).join(METHOD_NAME_SEPARATOR),
    method.name_zh,
    methodDisplayTitle(method),
  );
}

function methodOutputPriority(method: MethodCatalogItem) {
  const outputType = methodOutputType(method);
  const index = METHOD_DEFAULT_OUTPUT_PRIORITY.indexOf(outputType);
  return index === -1 ? METHOD_DEFAULT_OUTPUT_PRIORITY.length : index;
}

function compareBundleMethods(left: MethodCatalogItem, right: MethodCatalogItem) {
  const priorityDelta = methodOutputPriority(left) - methodOutputPriority(right);
  if (priorityDelta !== 0) return priorityDelta;
  const labelDelta = methodOutputLabel(left).localeCompare(methodOutputLabel(right), "zh-CN");
  if (labelDelta !== 0) return labelDelta;
  return String(left.name_zh || left.name || left.id).localeCompare(String(right.name_zh || right.name || right.id), "zh-CN");
}

function buildMethodBundles(methods: MethodCatalogItem[]) {
  const map = new Map<string, MethodCatalogItem[]>();
  for (const method of methods) {
    const key = methodBundleKey(method);
    const list = map.get(key) || [];
    list.push(method);
    map.set(key, list);
  }
  return [...map.entries()]
    .map(([bundleId, bundleMethods]) => {
      const methodsInBundle = [...bundleMethods].sort(compareBundleMethods);
      const representative = methodsInBundle[0];
      const segments = methodNameSegments(representative);
      const family = methodFamilyLabel(representative) || segments[0] || "其他";
      const title = methodBundleTitle(representative);
      return {
        id: `bundle-${bundleId}`,
        family,
        title,
        concept: methodConceptTitle(representative) || segments[1] || title,
        role: segments[2] || methodRoleLabels(representative)[0] || representative.required_roles?.[0] || "默认",
        grouped: methodsInBundle.length > 1,
        representative,
        methods: methodsInBundle,
      };
    })
    .sort((left, right) => {
      const familyDelta = left.family.localeCompare(right.family, "zh-CN");
      if (familyDelta !== 0) return familyDelta;
      return left.title.localeCompare(right.title, "zh-CN");
    });
}

function groupMethodBundles(bundles: MethodBundle[]) {
  const map = new Map<string, MethodBundle[]>();
  for (const bundle of bundles) {
    const family = bundle.family || "其他";
    const list = map.get(family) || [];
    list.push(bundle);
    map.set(family, list);
  }
  return [...map.entries()].sort((left, right) => left[0].localeCompare(right[0], "zh-CN"));
}

function smartDefaultOutputTypes(bundle: MethodBundle) {
  const configured = uniqueStrings(bundle.methods.flatMap((method) => method.default_output_types || []));
  if (configured.length) return configured;
  const family = bundle.representative.family;
  const availableOutputs = new Set(bundle.methods.map((method) => methodOutputType(method)).filter(Boolean));
  const title = `${bundle.title} ${bundle.concept} ${bundle.representative.id}`.toLowerCase();
  if (family === "visual") return METHOD_VISUAL_DEFAULT_OUTPUTS.filter((output) => availableOutputs.has(output));
  if (family === "report_part") return METHOD_REPORT_DEFAULT_OUTPUTS.filter((output) => availableOutputs.has(output));
  if (family === "descriptive" || family === "comparison" || title.includes("variance") || title.includes("mean") || title.includes("median")) {
    return METHOD_TEXTUAL_DEFAULT_OUTPUTS.filter((output) => availableOutputs.has(output));
  }
  if (["association", "categorical_association", "regression", "machine_learning", "multivariate", "time_series"].includes(family)) {
    return ["chart", "text", "table", "data"].filter((output) => availableOutputs.has(output));
  }
  return METHOD_TEXTUAL_DEFAULT_OUTPUTS.filter((output) => availableOutputs.has(output));
}

function bundleDefaultMethods(bundle: MethodBundle, dataset?: DatasetItem) {
  const selected: MethodCatalogItem[] = [];
  const usedOutputs = new Set<string>();
  const defaultOutputs = smartDefaultOutputTypes(bundle);
  const allowedOutputs = defaultOutputs.length ? new Set(defaultOutputs) : null;
  for (const method of bundle.methods) {
    const outputKey = methodOutputType(method) || methodOutputLabel(method) || method.id;
    if (allowedOutputs && !allowedOutputs.has(outputKey)) continue;
    if (dataset && !methodCanRun(method, dataset)) continue;
    if (usedOutputs.has(outputKey)) continue;
    usedOutputs.add(outputKey);
    selected.push(method);
  }
  if (selected.length) return selected;
  return bundle.methods.filter((method) => !dataset || methodCanRun(method, dataset)).slice(0, 1);
}

function bundlePlanningMethods(bundle: MethodBundle) {
  const selected: MethodCatalogItem[] = [];
  const usedOutputs = new Set<string>();
  const defaultOutputs = smartDefaultOutputTypes(bundle);
  const allowedOutputs = defaultOutputs.length ? new Set(defaultOutputs) : null;
  for (const method of bundle.methods) {
    const outputKey = methodOutputType(method) || methodOutputLabel(method) || method.id;
    if (allowedOutputs && !allowedOutputs.has(outputKey)) continue;
    if (usedOutputs.has(outputKey)) continue;
    usedOutputs.add(outputKey);
    selected.push(method);
  }
  return selected.length ? selected : bundle.methods.slice(0, 1);
}

function methodRunBlockReason(method: MethodCatalogItem, dataset?: DatasetItem) {
  if (!dataset) return "请先选择或上传数据集。";
  if (method.runtime_required !== false && method.cli_runtime_available === false) {
    return method.runtime_block_reason || "当前环境缺少该方法需要的 CLI 运行时。";
  }
  if (methodCanRun(method, dataset)) return "";
  const roles = new Set((method.required_roles || []).map((item) => String(item)));
  const outputType = methodOutputType(method);
  if (methodRequiresTemporalField(method) || roles.has("time")) {
      return "选择可用时间字段后即可运行这类方法。";
  }
  if (roles.has("field_pair") || ["association", "comparison", "regression", "machine_learning", "multivariate"].includes(method.family) || METHOD_CHART_OUTPUTS.has(outputType)) {
      return "选择足够的数值字段后即可运行这类方法。";
  }
  if (roles.has("grouped") || roles.has("categorical")) {
      return "选择可用分组字段后即可运行这类方法。";
  }
  return "当前数据结构还不满足这个方法的运行条件。";
}

function blockReasonAction(reason: string) {
  if (reason.includes("选择或上传数据集")) return "先在左侧选择已有数据集，或上传 CSV / Excel 文件。";
  if (reason.includes("时间字段")) return "换一个包含日期、月份、时间戳字段的数据集，或先补充时间字段。";
  if (reason.includes("数值字段")) return "至少需要足够的数值列；可换数据集，或在字段流程里补充可计算指标。";
  if (reason.includes("分组字段")) return "需要分类/分组列；可选择含地区、品类、渠道等字段的数据集。";
  if (reason.includes("CLI")) return "确认本机运行时依赖可用后再执行，当前仍可展开查看方法说明。";
  return "可以先展开明细查看可用子项，或更换更完整的数据集。";
}

function bundleInteractionState(bundle: MethodBundle, dataset?: DatasetItem) {
  const runnableMethods = bundle.methods.filter((method) => methodCanRun(method, dataset));
  const defaults = runnableMethods.length ? runnableMethods : bundlePlanningMethods(bundle);
  const blocked = !defaults.length;
  const representativeReason = methodRunBlockReason(bundle.representative, dataset);
  const reason =
    !runnableMethods.length
      ? representativeReason || "当前数据下没有可直接加入的默认子项，请展开后手动选择。"
      : "";
  return {
    defaults,
    runnableCount: runnableMethods.length,
    blocked: !runnableMethods.length,
    reason,
  };
}

function bundleSelectedCount(bundle: MethodBundle, selectedIds: Set<string>) {
  return bundle.methods.reduce((count, method) => count + (selectedIds.has(method.id) ? 1 : 0), 0);
}

function bundleRunCount(bundle: MethodBundle, runSpecs: MethodRunSpec[], selectedIds: Set<string>) {
  const methodIds = new Set(bundle.methods.map((method) => method.id));
  const explicitRuns = runSpecs.filter((spec) => methodIds.has(spec.method_id)).length;
  return explicitRuns || bundleSelectedCount(bundle, selectedIds);
}

function bundleRunGroups(bundle: MethodBundle, runSpecs: MethodRunSpec[]) {
  const methodIds = new Set(bundle.methods.map((method) => method.id));
  const groups = new Map<string, MethodRunSpec[]>();
  for (const spec of runSpecs) {
    if (!methodIds.has(spec.method_id)) continue;
    const groupId = spec.bundle_run_id || `single:${spec.run_id}`;
    const list = groups.get(groupId) || [];
    list.push(spec);
    groups.set(groupId, list);
  }
  return [...groups.entries()].map(([groupId, runs]) => ({ groupId, runs }));
}

function bundleOutputCount(bundle: MethodBundle) {
  return uniqueStrings(bundle.methods.map((method) => methodOutputType(method))).length;
}

function methodRenderKey(method: MethodCatalogItem, scope: string, index = 0) {
  return `${scope}-${method.id}-${method.source || "source"}-${method.package_ref || method.path || "catalog"}-${index}`;
}

function bundleRenderKey(bundle: MethodBundle, scope: string, index = 0) {
  return `${scope}-${bundle.id}-${bundle.representative.source || "source"}-${bundle.representative.package_ref || bundle.representative.path || "catalog"}-${index}`;
}

function bundleOutputSummary(bundle: MethodBundle) {
  const count = bundleOutputCount(bundle);
  return count >= 6 ? `完整 ${count} 项` : `基础 ${count} 项`;
}

function sliceBundlesByMethodLimit(bundles: MethodBundle[], methodLimit: number) {
  if (!bundles.length) return [];
  const safeLimit = Math.max(methodLimit, 1);
  const visible: MethodBundle[] = [];
  let usedCount = 0;
  for (const bundle of bundles) {
    const nextCount = usedCount + bundle.methods.length;
    if (visible.length && nextCount > safeLimit) break;
    visible.push(bundle);
    usedCount = nextCount;
    if (usedCount >= safeLimit) break;
  }
  return visible;
}

function groupMethods(methods: MethodCatalogItem[]) {
  const map = new Map<string, MethodCatalogItem[]>();
  for (const method of methods) {
    const family = methodFamilyLabel(method);
    const list = map.get(family) || [];
    list.push(method);
    map.set(family, list);
  }
  return [...map.entries()].sort((left, right) => left[0].localeCompare(right[0], "zh-CN"));
}

function familyCountsFromIndex(index: MethodIndexItem[]) {
  const counts = new Map<string, number>();
  for (const item of index) {
    counts.set(item.familyLabel, (counts.get(item.familyLabel) || 0) + 1);
  }
  return [...counts.entries()].sort((left, right) => right[1] - left[1]);
}

function groupMethodBundlesFromIndex(index: MethodIndexItem[]) {
  return groupMethodBundles(buildMethodBundles(index.map(({ method }) => method)));
}

function firstDownloadable(report: SmartReport) {
  return report.main_downloadable || report.downloadables?.find((item) => item.is_main);
}

function methodRequiresTemporalField(method: MethodCatalogItem) {
  if (method.family === "time_series") return true;
  return /(^|_)(line|time|trend|seasonality|lag|forecast|calendar|slope|bump|stream|control|candlestick)(_|$)/.test(
    method.id.toLowerCase(),
  );
}

function methodCanRun(method: MethodCatalogItem, dataset?: DatasetItem) {
  if (method.runtime_required !== false && method.cli_runtime_available === false) return false;
  if (!dataset) return false;
  const hasNumeric = Boolean(dataset.numeric_columns?.length);
  const hasCategorical = Boolean(dataset.categorical_columns?.length);
  const hasTemporal = Boolean(dataset.datetime_columns?.length);
  const roles = new Set((method.required_roles || []).map((item) => String(item)));
  const outputType = methodOutputType(method);
  if (METHOD_CHART_OUTPUTS.has(outputType)) {
    if (method.family === "visual") {
      if (methodRequiresTemporalField(method)) {
        return hasTemporal && hasNumeric;
      }
      if (method.required_roles.includes("field_pair")) return hasNumeric && (dataset.numeric_columns || []).length >= 2;
      if (method.required_roles.includes("grouped") || method.required_roles.includes("categorical")) return hasNumeric && hasCategorical;
      return hasNumeric || hasCategorical;
    }
    if (["association", "comparison", "regression", "machine_learning", "multivariate"].includes(method.family)) {
      return (dataset.numeric_columns || []).length >= 2;
    }
    if (method.family === "time_series") return hasTemporal && hasNumeric;
    if (method.family === "descriptive" || method.family === "distribution_assumption") return hasNumeric;
  }
  if (!roles.size) return hasNumeric || hasCategorical || hasTemporal;
  if (roles.has("field_pair") || roles.has("field_set")) return hasNumeric || hasCategorical;
  if (roles.has("time_window") || roles.has("time")) return hasTemporal;
  if (roles.has("single_field") || roles.has("derived_metric")) return hasNumeric;
  return hasNumeric || hasCategorical || hasTemporal;
}

function selectedMethodNames(methods: MethodCatalogItem[], selectedIds: Set<string>, runSpecs: MethodRunSpec[] = [], limit = 5) {
  const bundles = buildMethodBundles(methods.filter((method) => selectedIds.has(method.id)));
  if (!bundles.length) return "尚未选择方法";
  const names = bundles.slice(0, limit).map((bundle) => {
    const selectedCount = bundleRunCount(bundle, runSpecs, selectedIds);
    return selectedCount > 1 ? `${bundle.title}（${selectedCount} 项）` : bundle.title;
  });
  const remaining = bundles.length - names.length;
  return `${names.join("、")}${remaining > 0 ? ` 等 ${bundles.length} 类` : ""}`;
}

function methodBeginnerText(method: MethodCatalogItem) {
  return [
    method.id,
    method.name,
    method.name_zh,
    method.bundle_title,
    method.bundle_title_zh,
    method.bundle_title_en,
    method.parent_method_title,
    method.method_concept_label,
    method.method_output_label,
    method.submethod_label,
    method.submethod_title,
    method.output_variant,
    method.goal,
    method.goal_zh,
    method.card_description,
    method.method_card_contract,
    method.family,
    method.family_label,
    ...(method.output_types || []),
    ...(method.output_labels || []),
    ...(method.required_roles || []),
    ...(method.role_labels || []),
    ...(method.card_tags || []),
  ].join(" ").toLowerCase();
}

function methodBeginnerProfile(method: MethodCatalogItem) {
  const text = methodBeginnerText(method);
  const family = method.family;
  const roles = new Set(method.required_roles || []);
  const has = (pattern: RegExp) => pattern.test(text);

  if (family === "association" || family === "categorical_association" || has(/correlation|pearson|spearman|kendall|chi[-_\s]?square|chisq|crosstab|fisher|cramer|关联|相关|卡方|列联/)) {
    if (has(/chi[-_\s]?square|chisq|crosstab|fisher|cramer|categorical|分类|列联|卡方/)) {
      return {
        problem: "用来评估两个分类字段的关联程度，例如渠道与转化状态、地区与用户类型的组合结构。",
        when: "当两个字段都是类别或分组，且你关心“不同类别的比例是否明显不同”时使用。",
        how: "选择两个分类字段，先看交叉表里的样本量和占比，再看检验结果。",
        read: "重点看 p 值、各格子的占比差异和效应量；因果结论结合研究设计与额外证据评估。",
        caution: "如果某些格子的样本很少，优先用 Fisher 精确检验或合并过细类别。",
      };
    }
    return {
      problem: "用来判断两个数值字段是否一起变化，比如价格越高销量是否越低、满意度越高复购是否越高。",
      when: "当你有两个数值变量，想先确认它们有没有线性或单调关系时使用。",
      how: "选择一对数值字段；先看散点图和异常值，再看 Pearson、Spearman 或 Kendall 等相关系数。",
      read: "相关系数接近 1 或 -1 代表关系更强，接近 0 代表关系弱；方向正负表示同涨同跌或一升一降。",
      caution: "相关结果用于描述共同变化；因果解释结合研究设计、分组和图形复查。关系弯曲、分组混杂和极端值也应纳入检查。",
    };
  }

  if (family === "comparison" || family === "mean_tests" || family === "nonparametric" || has(/t[-_\s]?test|anova|wilcoxon|mann|whitney|kruskal|差异|均值|中位数|方差分析|非参数|检验/)) {
    if (family === "nonparametric" || has(/wilcoxon|mann|whitney|kruskal|rank|秩|非参数|中位数/)) {
      return {
        problem: "用来比较不同组的数值水平是否真的有差异，尤其适合数据不服从正态或样本偏小的场景。",
        when: "当你要比较两组或多组，但均值检验假设不稳、异常值较多时使用。",
        how: "选择一个数值结果字段和一个分组字段；配对数据要选择配对检验，独立分组要选择独立样本检验。",
        read: "重点看每组中位数、秩次差异、p 值和效果大小；业务价值结合效果大小、业务阈值和使用场景判断。",
        caution: "先确认分组含义、样本量与同一对象的重复测量情况；配对数据使用对应的配对方法。",
      };
    }
    return {
      problem: "用来比较不同组的平均水平是否有差异，比如不同渠道客单价、不同班级成绩、实验组和对照组表现。",
      when: "当一个字段提供数值结果，另一个字段提供分组，并且需要比较组间均值时使用。",
      how: "选择目标数值字段和分组字段；两组常用 t 检验，多组常用 ANOVA，必要时再做事后比较。",
      read: "先看各组均值和置信区间，再看 p 值；如果多组显著，还要看是哪几组之间不同。",
      caution: "检查异常值、样本量、方差是否差不多；如果假设不满足，可改用非参数方法。",
    };
  }

  if (family === "regression" || family === "regression_glm" || has(/regression|linear|logistic|poisson|glm|回归|预测|解释变量|自变量|因变量/)) {
    if (has(/logistic|binary|二分类|分类结果/)) {
      return {
        problem: "用来解释或预测一个二分类结果，比如是否购买、是否流失、是否通过。",
        when: "当目标字段使用是/否、0/1、成功/失败等二分类结果，并且需要评估影响概率的因素时使用。",
        how: "选择二分类目标字段，再选择可能影响它的特征字段；分类特征要确认编码和基准组。",
        read: "重点看方向、显著性、优势比或概率变化；系数为正通常表示发生概率上升。",
        caution: "同时查看准确率、类别平衡、混淆矩阵和业务可解释性。",
      };
    }
    return {
      problem: "用来解释或预测一个数值结果，并估计每个因素对结果的影响方向和大小。",
      when: "当你有一个连续数值目标，同时有多个可能影响它的字段时使用。",
      how: "选择目标字段和特征字段；先排除明显重复、强共线或缺失严重的字段，再运行模型。",
      read: "重点看系数方向、大小、置信区间、p 值和拟合度；系数代表在其他变量不变时的边际变化。",
      caution: "回归是条件解释，不自动证明因果；要检查残差、异常点、多重共线性和样本是否足够。",
    };
  }

  if (family === "machine_learning" || has(/cluster|kmeans|random forest|xgboost|classification|model|聚类|分类模型|机器学习|特征重要/)) {
    if (has(/cluster|kmeans|聚类|分群/)) {
      return {
        problem: "用来把相似样本自动分成几类，帮助发现客群、商品、地区或行为模式。",
        when: "当没有现成标签，但想根据多个特征找自然分组时使用。",
        how: "选择能代表对象特征的数值字段，运行前尽量标准化量纲，并尝试不同聚类数。",
        read: "重点看每一类的样本量、典型特征和可命名性；好聚类应该能说清每类是谁。",
        caution: "聚类结果会随字段选择和量纲变化；请结合业务特征解读分群。",
      };
    }
    return {
      problem: "用来做预测或分类，并判断哪些字段对预测更有帮助。",
      when: "当目标是提升预测准确度，或需要从很多字段中找出重要影响因素时使用。",
      how: "选择目标字段和特征字段，保留训练/验证评估；分类任务要关注类别平衡。",
      read: "看准确率、召回率、误差和特征重要性；模型好不好要以验证集表现为准。",
      caution: "机器学习更强调预测，不天然解释因果；上线前要检查过拟合和数据泄漏。",
    };
  }

  if (family === "multivariate" || has(/pca|principal|factor|dimension|多变量|主成分|因子|降维/)) {
    return {
      problem: "用来把很多相关字段压缩成少数几个综合维度，帮助看整体结构和主要差异来源。",
      when: "当变量很多、彼此相关，直接看单个字段太乱时使用。",
      how: "选择一组数值字段；运行前通常需要标准化，使不同量纲的字段获得均衡权重。",
      read: "重点看解释方差、载荷和样本在主成分上的位置；给每个维度起一个业务能懂的名字。",
      caution: "结合原始字段解释降维结果，并核对保留的细节与维度含义。",
    };
  }

  if (family === "time_series" || has(/time series|forecast|trend|season|rolling|时间序列|趋势|预测|季节|滚动/)) {
    return {
      problem: "用来观察指标随时间怎么变化，识别趋势、周期、拐点和异常时间段。",
      when: "当数据有明确时间字段，并且你关心过去走势或未来短期变化时使用。",
      how: "选择时间字段和数值指标，确认时间粒度一致；缺失日期、重复日期要先处理。",
      read: "综合查看趋势方向、波动幅度、季节性、异常点和预测区间。",
      caution: "时间预测默认未来规律与历史相似；遇到政策、活动或口径变化要单独标注。",
    };
  }

  if (family === "distribution_assumption" || has(/normal|shapiro|kolmogorov|qq|distribution|skew|kurtosis|正态|分布|偏度|峰度/)) {
    return {
      problem: "用来检查字段的分布形态，为后续依赖正态性或稳定分布前提的统计方法提供依据。",
      when: "当你准备做 t 检验、ANOVA、回归，或想知道数据是否偏态、长尾、异常值多时使用。",
      how: "选择一个或多个数值字段，结合直方图、QQ 图和正态性检验一起看。",
      read: "p 值小通常表示偏离正态；同时查看偏度、峰度和图形形状。",
      caution: "大样本下很小的偏离也可能显著；业务上是否影响结论要结合图形和方法稳健性判断。",
    };
  }

  if (family === "descriptive" || has(/describe|summary|profile|missing|outlier|描述|画像|概览|缺失|异常/)) {
    if (has(/missing|缺失/)) {
      return {
        problem: "用来检查数据缺失情况，判断哪些字段或记录会影响后续分析可靠性。",
        when: "分析开始前、建模前、或发现结果异常时都应该先看。",
        how: "查看每个字段缺失数量、缺失比例和缺失是否集中在某些分组或时间段。",
        read: "重点看缺失比例高的字段、关键字段是否缺失，以及缺失是否有明显模式。",
        caution: "先判断缺失是否具有业务含义，再决定填补、保留或剔除。",
      };
    }
    return {
      problem: "用来快速认识数据的基本样子，包括规模、均值、中位数、范围、缺失和异常。",
      when: "任何正式检验、建模或报告前都应该先用它打底。",
      how: "选择核心字段或全表运行；先看分布、缺失、极端值，再决定下一步分析方法。",
      read: "重点看中位数和均值差距、最小最大值、分位数和缺失比例，这些能暴露口径问题。",
      caution: "描述统计呈现当前结构；差异显著性和因果问题使用相应的分析方法评估。",
    };
  }

  if (family === "visual" || has(/chart|plot|hist|box|scatter|heatmap|bar|line|图|可视化|直方|箱线|散点|热力/)) {
    return {
      problem: "用图形把字段关系、分布或趋势变成直观证据，帮助先发现问题再做统计检验。",
      when: "当文字表格太难看出模式，或者你需要向非技术读者解释数据时使用。",
      how: "按图形类型选择数值、分类、时间或分组字段；先保证字段口径正确。",
      read: "重点看趋势、分组差距、离群点、集中区间和形状变化，并把图形发现转成下一步问题。",
      caution: "图形容易受坐标轴、分箱和样本量影响；重要发现最好再配合统计检验。",
    };
  }

  if (family === "causal" || family === "causal_panel" || family === "experimentation" || has(/causal|did|propensity|ab test|experiment|因果|实验|处理组|对照组|倾向得分/)) {
    return {
      problem: "用来评估某个动作、政策、实验或处理是否可能带来结果变化。",
      when: "当你有处理组和对照组，或有明确干预前后时间点，并且想接近因果解释时使用。",
      how: "明确处理变量、结果变量、时间或分组口径；先检查两组在干预前是否可比。",
      read: "结合处理效应大小、置信区间、显著性和稳健性评估结果。",
      caution: "因果方法依赖假设；观察性分组或遗漏变量存在时，结论宜表述为“可能影响”。",
    };
  }

  if (family === "survival" || has(/survival|kaplan|cox|hazard|生存|风险率|留存|流失时间/)) {
    return {
      problem: "用来分析事件发生前能持续多久，比如用户多久流失、设备多久故障、客户多久转化。",
      when: "适用于结果以“到某事件发生所需时间”表示，且部分样本仍处于观察期的情形。",
      how: "选择起止时间、事件是否发生字段和分组或协变量；保留未发生事件的删失信息。",
      read: "重点看生存曲线、风险比和不同组的事件发生速度。",
    caution: "将尚未发生事件的样本按删失处理，保证此类方法的结果完整。",
    };
  }

  if (family === "psychometrics" || has(/alpha|cronbach|reliability|scale|问卷|信度|量表/)) {
    return {
      problem: "用来检查问卷题项或量表是否稳定地测量同一个概念。",
      when: "当多个题目共同代表满意度、态度、能力等潜在概念时使用。",
      how: "选择同一量表下的题项字段，先确认题项方向一致，反向题要先反向计分。",
      read: "重点看信度系数、题项相关和删除某题后的变化。",
      caution: "量表评估结合信度、题目内容和维度结构判断。",
    };
  }

  if (roles.has("time") || roles.has("time_window")) {
    return {
      problem: "用来围绕时间字段整理数据变化，帮助发现趋势、阶段差异或异常窗口。",
      when: "当问题里包含日期、周期、前后对比或持续变化时使用。",
      how: "先选时间字段，再选要观察的指标或分组；确认时间粒度和缺失时间点。",
      read: "重点看方向、波动、拐点和异常时间段，并结合业务事件解释。",
      caution: "时间口径变化会影响结论，跨周期比较前要确认粒度一致。",
    };
  }

  if (roles.has("grouped") || roles.has("group") || roles.has("categorical")) {
    return {
      problem: "用来按类别或分组拆开数据，比较不同人群、渠道、地区或对象的表现。",
      when: "当你想知道“哪一组更高、哪一组更低、差异是否值得追”时使用。",
      how: "选择分组字段和要观察的指标；先看每组样本量，再看差异。",
      read: "重点看组间差距、占比、排序和异常组，并判断差异是否有业务意义。",
      caution: "样本量很小的组容易误导；必要时合并稀疏类别或补充显著性检验。",
    };
  }

  if (roles.has("field_pair")) {
    return {
      problem: "用来同时观察两个字段，判断它们之间是否存在关系、差距或匹配问题。",
      when: "当你的问题天然包含两个变量，比如价格和销量、年龄和收入、预测值和实际值时使用。",
      how: "选择一对字段，先看图形和异常点，再看表格或检验指标。",
      read: "重点看方向、强弱、异常组合和是否存在分组差异。",
      caution: "两个字段共同变化用于描述关联；因果评估还要检查第三个变量造成的混杂。",
    };
  }

  return {
    problem: `用来围绕「${methodGoalText(method) || methodDisplayTitle(method)}」生成可复核的分析证据，把字段、图表和文字解读连起来。`,
    when: `当你的业务问题属于「${methodFamilyLabel(method)}」，但还不确定该看哪些字段时，可以先用这张卡作为起点。`,
    how: "先按卡片提示选择目标字段、特征字段、分组或时间字段；字段不确定时先用智能默认，再根据业务口径微调。",
    read: "重点看输出里的方向、差异、异常、样本量和解释文字；把结果转成一句能行动的问题或结论。",
    caution: "这张卡提供统计证据，不替代业务判断；显著性、相关性和预测表现都需要结合数据质量复查。",
  };
}

function normalizeMethodSections(sections: MethodCatalogItem["card_sections"] = []): MethodCardSection[] {
  return sections
    .map((section) => ({
      kind: String(section.kind || "catalog").trim() || "catalog",
      label: String(section.label || "").trim(),
      value: String(section.value || "").trim(),
      help: section.help ? String(section.help).trim() : undefined,
    }))
    .filter((section) => section.label && section.value);
}

function normalizeUsageGuidance(items: MethodCatalogItem["usage_guidance"] = []): MethodUsageGuidance[] {
  return items
    .map((item) => ({
      title: String(item.title || "").trim(),
      detail: String(item.detail || "").trim(),
    }))
    .filter((item) => item.title && item.detail);
}

function beginnerMethodSections(method: MethodCatalogItem): MethodCardSection[] {
  const profile = methodBeginnerProfile(method);
  const title = methodDisplayTitle(method);
  const subTitle = methodSubmethodTitle(method);
  const family = methodFamilyLabel(method);
  const goal = methodGoalText(method) || title;
  const roles = methodRoleLabels(method).filter(Boolean).join("、") || "智能识别出的可用字段";
  const outputs = methodOutputLabels(method).filter(Boolean).join("、") || methodOutputLabel(method);
  const primaryOutput = methodOutputLabel(method);
  const cardName = subTitle && subTitle !== title ? `「${title} / ${subTitle}」` : `「${title}」`;
  return [
    {
      kind: "beginner_problem",
      label: "解决什么问题",
      value: `这张方法卡 ${cardName} 属于「${family}」，专门回答「${goal}」。${profile.problem} 它的核心输出是「${primaryOutput}」。`,
    },
    {
      kind: "beginner_when",
      label: "什么时候用",
      value: `当问题由 ${cardName} 解释，且数据提供 ${roles} 时使用。${profile.when}`,
    },
    {
      kind: "beginner_how",
      label: "怎么用",
      value: `在 ${cardName} 里优先配置 ${roles}，运行后会产出 ${outputs}。${profile.how}`,
    },
    {
      kind: "beginner_read",
      label: "结果怎么看",
      value: `解读 ${cardName} 时，先看「${primaryOutput}」，再结合 ${outputs} 判断这张卡给出的证据。${profile.read}`,
    },
    {
      kind: "beginner_caution",
      label: "小白避坑",
      value: `${cardName} 的限制是：${profile.caution}`,
    },
  ];
}

function beginnerUsageGuidance(method: MethodCatalogItem): MethodUsageGuidance[] {
  const profile = methodBeginnerProfile(method);
  const title = methodDisplayTitle(method);
  const roles = methodRoleLabels(method).filter(Boolean).join("、") || "目标字段、分组字段或时间字段";
  const outputs = methodOutputLabels(method).filter(Boolean).join("、") || methodOutputLabel(method);
  return [
    { title: "这张卡何时用", detail: `回答「${title}」对应问题时优先使用。${profile.when}` },
    { title: "字段怎么选", detail: `为「${title}」配置 ${roles}；字段不确定时先用智能默认，再按业务口径微调。${profile.how}` },
    { title: "读结果先看", detail: `「${title}」的输出重点是 ${outputs}。${profile.read}` },
  ];
}

function beginnerReportValueHooks(method: MethodCatalogItem) {
  const profile = methodBeginnerProfile(method);
  const title = methodDisplayTitle(method);
  const output = methodOutputLabel(method);
  return [
    `报告里先写清「${title}」这张方法卡回答的问题：${profile.problem}`,
    `解释「${title}」的 ${output} 时同时交代适用条件：${profile.when}`,
    `「${title}」结论后补一句限制：${profile.caution}`,
  ];
}

function mergeBeginnerSections(method: MethodCatalogItem) {
  const existing = normalizeMethodSections(method.card_sections);
  const existingLabels = new Set(existing.map((section) => section.label));
  const fallback = beginnerMethodSections(method).filter((section) => !existingLabels.has(section.label));
  return [...existing, ...fallback].slice(0, 8);
}

function mergeUsageGuidance(method: MethodCatalogItem) {
  const existing = normalizeUsageGuidance(method.usage_guidance);
  const existingTitles = new Set(existing.map((item) => item.title));
  const fallback = beginnerUsageGuidance(method).filter((item) => !existingTitles.has(item.title));
  return [...existing, ...fallback].slice(0, 5);
}

function mergeReportValueHooks(method: MethodCatalogItem) {
  const existing = uniqueStrings(method.report_value_hooks || []);
  return uniqueStrings([...existing, ...beginnerReportValueHooks(method)]).slice(0, 5);
}

function methodDisplayCopy(method: MethodCatalogItem) {
  const family = methodFamilyLabel(method);
  const description = String(method.card_description || methodGoalText(method) || "用于把当前数据转成可执行的分析结论。").trim();
  const descriptionLine = description.endsWith("。") ? description : `${description}。`;
  const roles = methodRoleLabels(method).filter(Boolean).join("、") || "数值、分类或时间字段";
  const outputs = methodOutputLabels(method).filter(Boolean).join("、") || "文字解读、表格、结构化结果";
  const primaryOutput = methodOutputLabels(method)[0] || "分析结果";
  const methodFocus = methodGoalText(method) || methodConceptTitle(method) || methodDisplayTitle(method);
  const source = method.source === "statistical_catalog" ? "统计目录" : method.source === "generated_catalog" ? "生成目录" : method.source;
  const status = method.status === "live" ? "可直接运行" : method.status === "catalog" ? "目录可选" : "规划中";
  const tags = uniqueStrings(method.card_tags || []);
  const outputType = methodOutputType(method);
  const sections = mergeBeginnerSections(method);
  const usageGuidance = mergeUsageGuidance(method);
  const reportValueHooks = mergeReportValueHooks(method);

  let businessLine = `该方法围绕「${methodFocus}」组织 ${primaryOutput}，适合在含有 ${roles} 的数据上使用，重点产出 ${outputs}。`;
  let actionLine = `重点确认这类 ${family} 方法是否适合解释当前数据的变化、差异或机会。`;

  if ((method.required_roles || []).includes("field_pair")) {
    businessLine = `该方法专门看一对字段之间的联动、差距和方向性变化，适合用来解释双变量关系，并输出 ${outputs}。`;
    actionLine = `优先确认一对可比较字段，再用 ${primaryOutput} 解释它们之间的联动、差距或方向性变化。`;
  } else if ((method.required_roles || []).includes("derived_metric")) {
    businessLine = `该方法会把原始字段和派生指标一起纳入分析字段，先确认口径，再产出 ${outputs}。`;
    actionLine = `优先把派生指标并入分析字段，再决定最终比较口径和输出重点。`;
  } else if (methodRecommendedSelectionMode(method) === "object") {
    businessLine = `该方法围绕对象全集展开，适合先指定对象字段和对象值，再比较不同对象之间的结构差异、经营表现或覆盖情况。`;
    actionLine = `优先指定对象字段和对象值全集，再判断不同对象之间的结构差异或表现机会。`;
  } else if ((method.required_roles || []).includes("time") || method.family === "time_series") {
    businessLine = `该方法以时间字段为主线，适合追踪趋势、拐点、节奏变化和时间窗异常，并输出 ${outputs}。`;
    actionLine = `优先确认时间字段和分析口径，再追踪趋势、拐点和可执行时间动作。`;
  } else if ((method.required_roles || []).includes("grouped")) {
    businessLine = `该方法以分组字段为核心，适合观察不同组之间的规模、效率、结构或分布差异，并输出 ${outputs}。`;
    actionLine = `优先确认分组字段，再对比不同组的规模、效率或结构差异。`;
  } else if ((method.required_roles || []).includes("single_field")) {
    businessLine = `该方法围绕单个核心字段展开，适合快速确认字段分布、稳定性和解释空间，再输出 ${outputs}。`;
    actionLine = `优先锁定一个核心字段，再决定是否需要补充特征字段或派生指标。`;
  } else if (outputType === "table") {
    businessLine = `该方法会把当前数据整理成更可读的表格证据，适合用来沉淀口径、对象分层或方法对比。`;
    actionLine = `优先确认要保留的字段口径，再通过表格把证据沉淀成可复核结构。`;
  } else if (outputType === "data") {
    businessLine = `该方法更偏向结构化结果沉淀，适合给后续报告、图表或执行链复用。`;
    actionLine = `优先确认结果要复用到哪里，再决定字段、对象和值的保留粒度。`;
  }

  const sectionSummary = sections
    .slice(0, 2)
    .map((section) => `${section.label}：${section.value}`)
    .join("；");
  if (sectionSummary) {
    businessLine += ` 当前重点：${sectionSummary}。`;
  }

  return {
    family,
    source,
    status,
    descriptionLine,
    businessLine,
    cliLine: `默认附带 CLI 智能解读，会把 ${methodDisplayTitle(method)} 的结果翻成带业务关联的中文说明。${tags.length ? ` 标签：${tags.slice(0, 4).join("、")}。` : ""}`,
    actionLine,
    tags,
    sections,
    usageGuidance,
    reportValueHooks,
  };
}

function methodBundleDisplayCopy(bundle: MethodBundle) {
  const representativeCopy = methodDisplayCopy(bundle.representative);
  const childSummaries = bundle.methods
    .map((method) => {
      const title = methodSubmethodTitle(method) || methodDisplayTitle(method);
      const output = methodOutputLabel(method);
      const roles = methodRoleLabels(method).filter(Boolean).join("、") || "智能字段";
      const goal = methodGoalText(method) || methodDisplayTitle(method);
      return { title, output, roles, goal };
    });
  const childList = childSummaries
    .slice(0, 5)
    .map((item) => `${item.title}产出${item.output}`)
    .join("；");
  const roleList = uniqueStrings(childSummaries.flatMap((item) => item.roles.split("、"))).slice(0, 6).join("、") || "智能字段";
  const outputList = uniqueStrings(childSummaries.map((item) => item.output)).slice(0, 8).join("、") || "多种分析结果";
  const firstGoals = childSummaries.slice(0, 3).map((item) => `「${item.title}」回答“${item.goal}”`).join("；");
  const sections: MethodCardSection[] = [
    {
      kind: "bundle_problem",
      label: "这组卡解决什么",
      value: `「${bundle.title}」是一张统一方法卡，会把 ${bundle.methods.length} 个对应子方法作为一组运行：${childList}${bundle.methods.length > 5 ? " 等" : ""}。`,
    },
    {
      kind: "bundle_when",
      label: "什么时候用",
      value: `当你想围绕「${bundle.title}」一次性拿到 ${outputList}，并希望这些子方法共享同一套字段、对象和数据口径时使用。`,
    },
    {
      kind: "bundle_how",
      label: "怎么用",
      value: `先给这组卡统一配置 ${roleList}；系统会把同一套绑定同步给组内每个子方法，保持分析口径一致。`,
    },
    {
      kind: "bundle_read",
      label: "结果怎么看",
      value: firstGoals ? `逐个读子方法结果：${firstGoals}。最后再比较它们是否指向同一个结论。` : representativeCopy.sections[3]?.value || representativeCopy.actionLine,
    },
    {
      kind: "bundle_caution",
      label: "小白避坑",
      value: `这张统一卡中的每个子方法都有独立解释和输出。展开“子方法明细”可以查看每个子方法对应的使用说明。`,
    },
  ];
  return {
    ...representativeCopy,
    descriptionLine: `「${bundle.title}」包含 ${bundle.methods.length} 个对应子方法，会用同一套字段/对象口径生成 ${outputList}。`,
    businessLine: `这张统一方法卡用于把「${bundle.title}」下的子方法一起执行：${childList}${bundle.methods.length > 5 ? " 等" : ""}。适合需要横向比较多种输出证据的场景。`,
    actionLine: `先统一配置 ${roleList}，再逐个检查子方法输出是否互相支持或互相冲突。`,
    cliLine: `默认附带 CLI 智能解读，会分别解释「${bundle.title}」组内每个子方法的结果，再合并成可读结论。`,
    sections,
    usageGuidance: [
      { title: "这组卡何时用", detail: `需要一次性比较 ${outputList}，且希望所有子方法沿用同一数据口径时使用。` },
      { title: "字段怎么选", detail: `优先配置 ${roleList}；字段会同步给这张统一卡下的每个子方法。` },
      { title: "读结果先看", detail: `先看每个子方法自己的 ${outputList}，再看组内结果是否共同支持同一判断。` },
    ],
    reportValueHooks: [
      `报告里先说明「${bundle.title}」是一组统一方法卡，包含 ${bundle.methods.length} 个子方法。`,
      `逐项解释组内子方法输出：${childList}${bundle.methods.length > 5 ? " 等" : ""}。`,
      `最后合并「${bundle.title}」组内结果，指出一致结论、冲突结论和需要复查的数据口径。`,
    ],
  };
}

function methodBindingControls(method: MethodCatalogItem) {
  const controls = method.binding_controls?.length
    ? method.binding_controls
    : ["target", "features", "group", "label", "time", "derived_metrics"];
  const controlSet = new Set([...controls, "derived_metrics"]);
  const text = methodSearchText(method);
  const roles = new Set((method.required_roles || []).map((role) => String(role)));
  if (roles.has("single_field")) controlSet.add("field");
  if (roles.has("field_pair") || method.family === "association" || method.family === "comparison" || method.family === "causal" || METHOD_CHART_OUTPUTS.has(methodOutputType(method))) {
    controlSet.add("x");
    controlSet.add("y");
  }
  if (roles.has("field_set") || ["regression", "machine_learning", "multivariate", "psychometrics"].includes(method.family)) {
    controlSet.add("target");
    controlSet.add("features");
  }
  if (roles.has("grouped") || roles.has("categorical") || roles.has("dimension") || roles.has("group") || /bar|column|pie|donut|box|violin|heatmap|map|funnel|分类|分组|对比/.test(text)) {
    controlSet.add("group");
  }
  if (roles.has("entity") || roles.has("entity_level") || methodRecommendedSelectionMode(method) === "object") {
    controlSet.add("label");
    controlSet.add("entity");
    controlSet.add("object_selection");
  }
  if (roles.has("time") || roles.has("time_window") || method.family === "time_series" || /line|trend|time|date|时间|趋势/.test(text)) {
    controlSet.add("time");
  }
  if (roles.has("derived_metric") || ["causal", "time_series"].includes(method.family)) {
    controlSet.add("derived_metrics");
  }
  return controlSet;
}

function methodRecommendedSelectionMode(method?: MethodCatalogItem | null): MethodRunSelectionMode {
  const mode = method?.selection_mode || method?.recommended_selection_mode;
  return mode === "object" || mode === "all_rows" || mode === "fields" ? mode : "fields";
}

function currentBindingLabelFallback(binding: MethodFieldBinding, fieldSelection: FieldSelection) {
  return binding.entity || binding.label || fieldSelection.label || fieldSelection.group || "对象";
}

function buildUserGoalForRun(
  baseGoal: string,
  methodCount: number,
  options: { includeCli?: boolean } = {},
) {
  const includeCli = options.includeCli !== false;
  const trimmed = baseGoal.trim();
  const tail = includeCli
    ? "请默认输出 CLI 智能解读，并把结论写成带业务关联、可执行的中文说明。"
    : "请把结论写成带业务关联、可执行的中文说明。";
  const prefix = trimmed ? `${trimmed}\n\n` : "";
  return `${prefix}${tail} 当前选择的方法数：${methodCount}。`;
}

function familyCounts(methods: MethodCatalogItem[]) {
  const counts = new Map<string, number>();
  for (const method of methods) {
    const key = methodFamilyLabel(method);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return [...counts.entries()].sort((left, right) => right[1] - left[1]);
}

function recommendedMethods(methods: MethodCatalogItem[], priorityIds: string[] = [], limit = 12) {
  const prioritySet = new Set(priorityIds);
  const liveVisual = methods.filter((method) => prioritySet.has(method.id));
  const fallback = methods.filter(
    (method) =>
      !prioritySet.has(method.id) &&
      (method.status === "live" ||
        method.family === "visual" ||
        method.source === "statistical_catalog" ||
        method.status === "catalog" ||
        method.status === "planned"),
  );
  const seen = new Set<string>();
  const ordered: MethodCatalogItem[] = [];
  for (const method of [...liveVisual, ...fallback]) {
    const key = methodBundleKey(method);
    if (seen.has(key)) continue;
    seen.add(key);
    ordered.push(method);
    if (ordered.length >= limit) break;
  }
  if (ordered.length < limit) {
    for (const method of methods) {
      const key = methodBundleKey(method);
      if (seen.has(key)) continue;
      seen.add(key);
      ordered.push(method);
      if (ordered.length >= limit) break;
    }
  }
  return ordered;
}

function methodQualitySummary(
  methods: MethodCatalogItem[],
  dataset: DatasetItem | undefined,
  selectedIds: Set<string>,
): MethodQualitySummary {
  let visual = 0;
  let nonFinancialVisual = 0;
  let runnable = 0;
  let selected = 0;
  let selectedRunnable = 0;
  let saved = 0;
  const sources: Record<string, number> = {};

  for (const method of methods) {
    const source = method.source || "unknown";
    sources[source] = (sources[source] || 0) + 1;
    const isVisual = method.family === "visual" || method.output_types?.some((item) => item === "chart" || item === "image_spec");
    const canRun = methodCanRun(method, dataset);
    const isSelected = selectedIds.has(method.id);
    if (isVisual) visual += 1;
    if (method.source === "statistical_visual_catalog" && method.allowed_domain === "non_financial") {
      nonFinancialVisual += 1;
    }
    if (method.source === "learned_methods" || method.source === "lab_method_card_editor") saved += 1;
    if (canRun) runnable += 1;
    if (isSelected) selected += 1;
    if (isSelected && canRun) selectedRunnable += 1;
  }

  const blocked = Math.max(0, methods.length - runnable);
  return {
    total: methods.length,
    visual,
    nonFinancialVisual,
    runnable,
    blocked,
    selected,
    selectedRunnable,
    saved,
    sources,
    readyPercent: methods.length ? Math.round((runnable / methods.length) * 100) : 0,
    visualSlaMet: nonFinancialVisual >= 500,
    financeExcluded: !sources.financial_visual_catalog,
  };
}

function normalizeReportParts(reportParts: string[] | null | undefined) {
  const values = (reportParts?.length ? reportParts : DEFAULT_REPORT_PARTS)
    .map((part) => String(part || "").trim())
    .filter(Boolean);
  const filtered = values.filter((part) => Object.prototype.hasOwnProperty.call(REPORT_PART_LABELS, part));
  return filtered.length ? [...new Set(filtered)] : [...DEFAULT_REPORT_PARTS];
}

function reportPartLabel(reportPartId: string) {
  return REPORT_PART_LABELS[reportPartId] || reportPartId;
}

function reportPartSummary(reportPartIds: string[], limit = 3) {
  const names = reportPartIds.slice(0, limit).map((partId) => reportPartLabel(partId));
  if (!names.length) return "尚未选择报告部件";
  const remaining = reportPartIds.length - names.length;
  return `${names.join("、")}${remaining > 0 ? ` 等 ${formatNumber(reportPartIds.length)} 项` : ""}`;
}

function externalSkillFeatureSelectionKey(selection: Pick<ExternalSkillFeatureSelection, "plugin_id" | "feature_kind" | "feature_id">) {
  return `${selection.plugin_id}::${selection.feature_kind}::${selection.feature_id}`;
}

function cleanExternalSkillFeatureSelections(
  selections: ExternalSkillFeatureSelection[],
  externalSkillIds: string[],
): ExternalSkillFeatureSelection[] {
  const mountedIds = new Set(externalSkillIds);
  const seen = new Set<string>();
  return selections
    .filter((selection) => mountedIds.has(selection.plugin_id) && selection.feature_id)
    .filter((selection) => {
      const key = externalSkillFeatureSelectionKey(selection);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .map((selection) => ({
      plugin_id: selection.plugin_id,
      feature_kind: selection.feature_kind,
      feature_id: selection.feature_id,
      name: selection.name || selection.feature_id,
      description: selection.description || "",
      path: selection.path || "",
      selection_source: selection.selection_source || "analysis_lab_report_flow",
    }));
}

function buildLabRunPayload({
  selectedDatasetId,
  selectedSheetName,
  workspaceBrief,
  selectedIds,
  methodRunSpecs,
  selectedReportParts,
  executionMode,
  smartMergeEnabled,
  maxMethods,
  fieldSelection,
  derivedMetricEdits,
  methodFieldBindings,
  externalSkillIds,
  externalSkillFeatureSelections,
}: {
  selectedDatasetId: string;
  selectedSheetName: string;
  workspaceBrief: string;
  selectedIds: string[];
  methodRunSpecs: MethodRunSpec[];
  selectedReportParts: string[];
  executionMode: "separate" | "smart_merge";
  smartMergeEnabled: boolean;
  maxMethods: number;
  fieldSelection: FieldSelection;
  derivedMetricEdits: DerivedMetricEdit[];
  methodFieldBindings: MethodFieldBindings;
  externalSkillIds: string[];
  externalSkillFeatureSelections: ExternalSkillFeatureSelection[];
}) {
  const reportParts = normalizeReportParts(selectedReportParts);
  const derivedEdits = cleanDerivedMetricEdits(derivedMetricEdits);
  const cleanFeatureSelections = cleanExternalSkillFeatureSelections(externalSkillFeatureSelections, externalSkillIds);
  return {
    dataset_id: selectedDatasetId,
    active_sheet: selectedSheetName || null,
    user_goal: buildUserGoalForRun(workspaceBrief, selectedIds.length, { includeCli: true }),
    report_part: reportParts.join(",") || DEFAULT_REPORT_PARTS.join(","),
    selected_report_parts: reportParts,
    max_methods: Math.max(1, maxMethods),
    // Reuse the existing shared preprocessing chain so irregular tables are cleaned
    // and derived fields are created before any method routing/execution starts.
    max_derived_fields: 96,
    max_chart_points: 60,
    execution_mode: executionMode,
    selected_method_ids: selectedIds,
    method_run_specs: cleanMethodRunSpecs(methodRunSpecs),
    external_skill_ids: externalSkillIds,
    external_skill_feature_selections: cleanFeatureSelections,
    selected_fields: cleanFieldSelection(fieldSelection),
    selected_derived_fields: derivedEdits.map((edit) => edit.field),
    derived_metric_edits: derivedEdits,
    method_field_bindings: cleanMethodFieldBindings(methodFieldBindings),
    cli_interpretation_enabled: true,
    business_interpretation_enabled: true,
    method_independent_output_enabled: true,
    smart_merge_enabled: smartMergeEnabled,
  };
}

export function AnalysisWorkspaceShell() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [methods, setMethods] = useState<MethodCatalogItem[]>([]);
  const [reportParts, setReportParts] = useState<string[]>(DEFAULT_REPORT_PARTS);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [selectedSheet, setSelectedSheet] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetDetail, setDatasetDetail] = useState<DatasetItem | null>(null);
  const [fieldSelection, setFieldSelection] = useState<FieldSelection>(EMPTY_FIELD_SELECTION);
  const [derivedMetricEdits, setDerivedMetricEdits] = useState<DerivedMetricEdit[]>([]);
  const [methodFieldBindings, setMethodFieldBindings] = useState<MethodFieldBindings>({});
  const [methodRunSpecs, setMethodRunSpecs] = useState<MethodRunSpec[]>([]);
  const [activeMethodRunIds, setActiveMethodRunIds] = useState<Record<string, string>>({});
  const [editorTarget, setEditorTarget] = useState<MethodEditorTarget | null>(null);
  const [selectedMethodId, setSelectedMethodId] = useState("");
  const [methodEditorOpen, setMethodEditorOpen] = useState(false);
  const [selectedMethodIds, setSelectedMethodIds] = useState<Set<string>>(() => new Set());
  const [priorityMethodIds, setPriorityMethodIds] = useState<string[]>([]);
  const [selectedReportPartIds, setSelectedReportPartIds] = useState<Set<string>>(
    () => new Set(DEFAULT_REPORT_PARTS),
  );
  const [methodSearch, setMethodSearch] = useState("");
  const [methodFilter, setMethodFilter] = useState<MethodFilter>("all");
  const [activeMethodFamily, setActiveMethodFamily] = useState("");
  const [activeMethodSource, setActiveMethodSource] = useState("");
  const [methodCardSaveBusyId, setMethodCardSaveBusyId] = useState<string | null>(null);
  const [mode, setMode] = useState<RunMode>("auto");
  const [groupedView, setGroupedView] = useState(true);
  const [visibleMethodLimit, setVisibleMethodLimit] = useState(INITIAL_VISIBLE_METHOD_LIMIT);
  const [workspaceBrief, setWorkspaceBrief] = useState("");
  const [status, setStatus] = useState("正在加载方法目录和数据集...");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WorkspaceResult | null>(null);
  const [methodRuns, setMethodRuns] = useState<MethodRunResult[]>([]);
  const [autoSummary, setAutoSummary] = useState<StatsResult | SmartReport | null>(null);
  const [externalSkills, setExternalSkills] = useState<ExternalSkillItem[]>([]);
  const [externalSkillSourceUrl, setExternalSkillSourceUrl] = useState(DEFAULT_EXTERNAL_SKILL_SOURCE_URL);
  const [externalSkillLocalPath, setExternalSkillLocalPath] = useState("");
  const [externalSkillStatus, setExternalSkillStatus] = useState("Anthropic Knowledge Work Plugins repo is ready to install.");
  const [externalSkillError, setExternalSkillError] = useState<string | null>(null);
  const [externalSkillBusyId, setExternalSkillBusyId] = useState<string | null>(null);
  const [externalSkillFeatureSelections, setExternalSkillFeatureSelections] = useState<ExternalSkillFeatureSelection[]>([]);
  const [featureTrialResult, setFeatureTrialResult] = useState<LabFeatureTrialResult | null>(null);
  const [featureTrialBusyId, setFeatureTrialBusyId] = useState<string | null>(null);
  const [reportAgentTeams, setReportAgentTeams] = useState<LabReportAgentTeamItem[]>([]);
  const [reportAgentTeamLocalPath, setReportAgentTeamLocalPath] = useState("");
  const [reportAgentTeamStatus, setReportAgentTeamStatus] = useState("Local report agent teams are ready to import.");
  const [reportAgentTeamError, setReportAgentTeamError] = useState<string | null>(null);
  const [reportAgentTeamBusyId, setReportAgentTeamBusyId] = useState<string | null>(null);
  const [reportAgentTeamTask, setReportAgentTeamTask] = useState<Record<string, unknown> | null>(null);
  const [partRunBusy, setPartRunBusy] = useState<string | null>(null);
  const [canvasExpanded, setCanvasExpanded] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isPending, startTransition] = useTransition();
  const [catalogLoaded, setCatalogLoaded] = useState(false);
  const [workflowProgress, setWorkflowProgress] = useState<WorkflowProgressState>({
    active: false,
    phase: "idle",
    percent: 0,
    title: "",
    detail: "",
  });
  const workflowPulseRef = useRef<number | null>(null);
  const workflowTokenRef = useRef(0);
  const deferredMethodSearch = useDeferredValue(methodSearch);
  const deferredMethodFilter = useDeferredValue(methodFilter);
  const methodIndex = useMemo(() => methods.map(buildMethodIndex), [methods]);

  const selectedDataset = datasetDetail?.dataset_id === selectedDatasetId
    ? datasetDetail
    : datasets.find((dataset) => dataset.dataset_id === selectedDatasetId);
  const selectedSheetName = selectedSheet || datasetSheetName(selectedDataset);
  const isBusy = isUploading || isRunning || isPending || workflowProgress.active;
  const mountedExternalSkillIds = useMemo(
    () => externalSkills.filter((skill) => skill.mounted).map((skill) => skill.id),
    [externalSkills],
  );
  const cleanExternalSkillFeatureSelectionList = useMemo(
    () => cleanExternalSkillFeatureSelections(externalSkillFeatureSelections, mountedExternalSkillIds),
    [externalSkillFeatureSelections, mountedExternalSkillIds],
  );
  const mountedReportAgentTeamIds = useMemo(
    () => reportAgentTeams.filter((team) => team.mounted).map((team) => team.id),
    [reportAgentTeams],
  );
  const externalSkillBusy = externalSkillBusyId !== null;
  const reportAgentTeamBusy = reportAgentTeamBusyId !== null;
  const selectedMethodIdSet = useMemo(
    () => new Set(clampMethodIds([...methodIdsFromSetAndRuns(selectedMethodIds, methodRunSpecs)])),
    [methodRunSpecs, selectedMethodIds],
  );
  const visualMethodCount = useMemo(
    () =>
      methods.filter(
        (method) =>
          method.family === "visual" ||
          method.output_types?.some((item) => item === "chart" || item === "image_spec"),
      ).length,
    [methods],
  );
  const recommendedMethodSlice = useMemo(() => recommendedMethods(methods, priorityMethodIds), [methods, priorityMethodIds]);
  const recommendedMethodIdSet = useMemo(
    () => new Set(recommendedMethodSlice.map((method) => method.id)),
    [recommendedMethodSlice],
  );
  const baseFilteredMethodIndex = useMemo(() => {
    const query = deferredMethodSearch.trim().toLowerCase();
    const byFilter = methodIndex.filter(({ method }) => {
      if (deferredMethodFilter === "visual") {
        return method.family === "visual" || method.output_types?.some((item) => item === "chart" || item === "image_spec");
      }
      if (deferredMethodFilter === "selected") {
        return selectedMethodIdSet.has(method.id);
      }
      if (deferredMethodFilter === "recommended") {
        return recommendedMethodIdSet.has(method.id);
      }
      if (deferredMethodFilter === "all") {
        return true;
      }
      return method.status === deferredMethodFilter;
    });
    if (!query) return byFilter;
    return byFilter.filter(({ searchText }) => searchText.includes(query));
  }, [deferredMethodFilter, deferredMethodSearch, methodIndex, recommendedMethodIdSet, selectedMethodIdSet]);
  const groupedMethodCounts = useMemo(() => familyCountsFromIndex(baseFilteredMethodIndex), [baseFilteredMethodIndex]);
  const filteredMethodIndex = useMemo(() => {
    return baseFilteredMethodIndex.filter((item) => {
      const familyMatches = !activeMethodFamily || item.familyLabel === activeMethodFamily;
      const sourceMatches = !activeMethodSource || item.method.source === activeMethodSource;
      return familyMatches && sourceMatches;
    });
  }, [activeMethodFamily, activeMethodSource, baseFilteredMethodIndex]);
  const methodSourceCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const { method } of baseFilteredMethodIndex) {
      const source = method.source || "unknown";
      counts.set(source, (counts.get(source) || 0) + 1);
    }
    const priority = new Map(
      ["statistical_visual_catalog", "auto_analysis_specs", "statistical_catalog", "financial_visual_catalog", "learned_methods"].map((source, index) => [
        source,
        index,
      ]),
    );
    return [...counts.entries()].sort((left, right) => {
      const leftPriority = priority.get(left[0]) ?? 99;
      const rightPriority = priority.get(right[0]) ?? 99;
      return leftPriority - rightPriority || right[1] - left[1] || left[0].localeCompare(right[0]);
    });
  }, [baseFilteredMethodIndex]);
  const filteredMethods = useMemo(() => filteredMethodIndex.map(({ method }) => method), [filteredMethodIndex]);
  const filteredMethodBundles = useMemo(() => {
    const bundles = groupMethodBundlesFromIndex(filteredMethodIndex).flatMap(([, items]) => items);
    return bundles.sort((left, right) => {
      const familyDelta = left.family.localeCompare(right.family, "zh-CN");
      if (familyDelta !== 0) return familyDelta;
      return left.title.localeCompare(right.title, "zh-CN");
    });
  }, [filteredMethodIndex]);
  const visibleMethods = useMemo(
    () => filteredMethods.slice(0, visibleMethodLimit),
    [filteredMethods, visibleMethodLimit],
  );
  const visibleMethodBundles = useMemo(
    () => sliceBundlesByMethodLimit(filteredMethodBundles, visibleMethodLimit),
    [filteredMethodBundles, visibleMethodLimit],
  );
  const visibleGroupedMethods = useMemo(() => groupMethodBundles(visibleMethodBundles), [visibleMethodBundles]);
  const hiddenMethodCount = Math.max(filteredMethodBundles.length - visibleMethodBundles.length, 0);
  const visibleBundleCount = visibleMethodBundles.length;
  const visibleMethodCount = visibleMethodBundles.reduce((count, bundle) => count + bundle.methods.length, 0);
  const currentMethod = methods.find((method) => method.id === selectedMethodId);
  const methodsById = useMemo(() => new Map(methods.map((method) => [method.id, method])), [methods]);
  const selectedRunSpecs = useMemo(
    () => methodRunSpecs.filter((spec) => selectedMethodIdSet.has(spec.method_id)).slice(0, MAX_SELECTED_METHOD_RUNS),
    [methodRunSpecs, selectedMethodIdSet],
  );
  const cappedMethodRunSpecs = useMemo(
    () => methodRunSpecs.slice(0, MAX_SELECTED_METHOD_RUNS),
    [methodRunSpecs],
  );
  const selectedRunCount = selectedRunSpecs.length || selectedMethodIdSet.size;
  const selectedMethods = useMemo(
    () => methods.filter((method) => selectedMethodIdSet.has(method.id)),
    [methods, selectedMethodIdSet],
  );
  const selectedMethodBundles = useMemo(
    () => buildMethodBundles(selectedMethods),
    [selectedMethods],
  );
  const activeSelectedMethod = useMemo(
    () => currentMethod || selectedMethods[0] || null,
    [currentMethod, selectedMethods],
  );
  const activeEditorTarget = useMemo(() => {
    if (methodEditorOpen && editorTarget?.methodId) {
      return editorTarget;
    }
    if (selectedMethodId) {
      const runId = activeMethodRunIds[selectedMethodId];
      return runId ? { methodId: selectedMethodId, runId } : { methodId: selectedMethodId };
    }
    return null;
  }, [activeMethodRunIds, editorTarget, methodEditorOpen, selectedMethodId]);
  const activeEditorMethod = useMemo(
    () => methods.find((method) => method.id === activeEditorTarget?.methodId) || activeSelectedMethod,
    [activeEditorTarget?.methodId, activeSelectedMethod, methods],
  );
  const availableReportParts = useMemo(
    () => (reportParts.length ? reportParts : DEFAULT_REPORT_PARTS),
    [reportParts],
  );
  const selectedReportParts = useMemo(
    () => availableReportParts.filter((partId) => selectedReportPartIds.has(partId)),
    [availableReportParts, selectedReportPartIds],
  );
  const availableSingleMethods = useMemo(
    () => methods.filter((method) => methodCanRun(method, selectedDataset)),
    [methods, selectedDataset],
  );
  const uploadBlockReason = !selectedFile
    ? "请先选择待分析的数据文件。"
    : isBusy
      ? "当前流程正在运行。完成后即可上传新的数据文件。"
      : "";
  const uploadBlockAction = !selectedFile
    ? "点击上方文件卡片选择 CSV、TSV、DTA 或 Excel 文件后，上传按钮会自动恢复。"
    : "等待当前上传、预处理或分析流程完成后，再继续上传新的数据。";
  const currentMethodBlockReason = currentMethod && selectedDataset
    ? methodRunBlockReason(currentMethod, selectedDataset)
    : "";
  const selectedExecutionBlockReason = useMemo(() => {
    if (!selectedDataset) return "";
    for (const run of selectedRunSpecs) {
      const method = methodsById.get(run.method_id);
      if (!method) continue;
      const reason = methodRunBlockReason(method, selectedDataset);
      if (reason) return `${run.label || methodSubmethodTitle(method)}：${reason}`;
    }
    return "";
  }, [methodsById, selectedDataset, selectedRunSpecs]);
  const analysisBlockReason = isBusy
    ? "当前任务正在运行。完成后即可启动新的分析。"
    : !selectedDatasetId
      ? "请先选择或上传一个数据集。"
      : !selectedDataset
        ? "当前数据集详情还在加载，请稍候。"
        : mode === "method" && !selectedMethodId
          ? "请先选择一个单方法。"
          : mode === "method" && currentMethodBlockReason
            ? currentMethodBlockReason
            : mode === "batch" && !selectedRunCount
              ? "请先勾选至少一个 Lab 方法。"
              : (mode === "batch" || mode === "auto") && selectedExecutionBlockReason
                ? selectedExecutionBlockReason
                : "";
  const analysisBlockAction = isBusy
    ? "等待当前进度结束后，执行按钮会自动恢复。"
    : !selectedDatasetId
      ? "在左侧选择已有数据集，或先上传一个新的表格文件。"
      : !selectedDataset
        ? "数据集详情返回后会自动刷新字段、方法和按钮状态。"
        : mode === "method" && !selectedMethodId
          ? "在右侧方法目录中选择一个可运行方法，或切换到自动/批量模式。"
          : mode === "method" && currentMethodBlockReason
            ? blockReasonAction(currentMethodBlockReason)
            : selectedExecutionBlockReason
              ? "这张方法卡仍可保留在执行篮子里；补齐对应字段、换数据集或修复运行时后即可运行。"
            : "在方法目录中加入一个或多个方法实例后，批量执行会自动恢复。";
  const catalogSummary = useMemo(() => {
    let live = 0;
    let catalog = 0;
    let planned = 0;
    for (const item of methodIndex) {
      if (item.method.status === "live") live += 1;
      else if (item.method.status === "catalog") catalog += 1;
      else if (item.method.status === "planned") planned += 1;
    }
    return { live, catalog, planned, total: methods.length, visual: visualMethodCount };
  }, [methodIndex, methods.length, visualMethodCount]);
  const methodQuality = useMemo(
    () => methodQualitySummary(methods, selectedDataset, selectedMethodIdSet),
    [methods, selectedDataset, selectedMethodIdSet],
  );

  useEffect(() => {
    if (!selectedDataset || !methodRunSpecs.length || !methods.length) return;
    setMethodRunSpecs((current) => {
      let changed = false;
      const next = current.map((spec) => {
        const method = methodsById.get(spec.method_id);
        if (!method) return spec;
        const smartBinding = methodDefaultBinding(method, fieldSelection, selectedDataset, derivedMetricEdits);
        const methodSavedBinding = pruneMethodFieldBinding(method.field_bindings || {}, selectedDataset, derivedMetricEdits);
        const currentBindingForDataset = pruneMethodFieldBinding(spec.field_bindings || {}, selectedDataset, derivedMetricEdits);
        const mergedBinding = cleanMethodFieldBinding({ ...smartBinding, ...methodSavedBinding, ...currentBindingForDataset });
        const hasExisting = Object.keys(currentBindingForDataset).length > 0;
        const hasSmart = Object.keys(smartBinding).length > 0 || Object.keys(methodSavedBinding).length > 0;
        if (!hasSmart || (hasExisting && JSON.stringify(mergedBinding) === JSON.stringify(currentBindingForDataset))) {
          return spec;
        }
        changed = true;
        const nextObjectSelection =
          spec.selection_mode === "object"
            ? {
                ...(spec.object_selection || {}),
                object_type: spec.object_selection?.object_type || method.role_labels?.[0] || currentBindingLabelFallback(mergedBinding, fieldSelection),
                merge_mode: spec.object_selection?.merge_mode || "smart",
                object_keys: uniqueStrings(spec.object_selection?.object_keys || []),
                group_key: spec.object_selection?.group_key || mergedBinding.group || fieldSelection.group || "",
                label_key: spec.object_selection?.label_key || mergedBinding.label || mergedBinding.entity || fieldSelection.label || "",
                filter_field:
                  spec.object_selection?.filter_field ||
                  spec.object_selection?.label_key ||
                  mergedBinding.label ||
                  mergedBinding.entity ||
                  fieldSelection.label ||
                  fieldSelection.group ||
                  "",
                filter_values: uniqueStrings(spec.object_selection?.filter_values || spec.object_selection?.object_keys || []),
                filter_operator: spec.object_selection?.filter_operator || "in",
                selection_source: spec.object_selection?.selection_source || "fields",
              }
            : spec.object_selection;
        return {
          ...spec,
          field_bindings: mergedBinding,
          object_selection: nextObjectSelection,
          smart_merge_group: spec.smart_merge_group || mergedBinding.group || "",
        };
      });
      return changed ? next : current;
    });
  }, [derivedMetricEdits, fieldSelection, methodRunSpecs.length, methods.length, methodsById, selectedDataset]);

  useEffect(() => {
    return () => {
      if (workflowPulseRef.current) {
        window.clearInterval(workflowPulseRef.current);
      }
    };
  }, []);

  function updateWorkflowProgress(patch: Partial<WorkflowProgressState>) {
    setWorkflowProgress((current) => ({
      ...current,
      active: patch.active ?? true,
      ...patch,
      percent: Math.max(0, Math.min(100, patch.percent ?? current.percent)),
    }));
  }

  function startWorkflowPulse(token: number, ceiling: number) {
    if (workflowPulseRef.current) {
      window.clearInterval(workflowPulseRef.current);
    }
    workflowPulseRef.current = window.setInterval(() => {
      if (workflowTokenRef.current !== token) {
        if (workflowPulseRef.current) {
          window.clearInterval(workflowPulseRef.current);
          workflowPulseRef.current = null;
        }
        return;
      }
      setWorkflowProgress((current) => {
        if (!current.active || current.percent >= ceiling) return current;
        return { ...current, percent: Math.min(ceiling, current.percent + 2) };
      });
    }, 900);
  }

  function stopWorkflowPulse() {
    if (workflowPulseRef.current) {
      window.clearInterval(workflowPulseRef.current);
      workflowPulseRef.current = null;
    }
  }

  function hydrateAutoAnalysisState(payload: StatsResult, dataset?: DatasetItem) {
    const data = autoAnalysisData(payload) as AutoAnalysisData & Record<string, unknown>;
    const selected = isRecord(data.selected_fields) ? data.selected_fields : {};
    const derivedOptions = Array.isArray(data.derived_field_options) ? data.derived_field_options : [];
    const nextFieldSelection = inferDefaultFieldSelection(dataset || selectedDataset);
    if (typeof selected.target === "string") nextFieldSelection.target = selected.target;
    if (Array.isArray(selected.features)) nextFieldSelection.features = selected.features.filter((item): item is string => typeof item === "string");
    if (typeof selected.group === "string") nextFieldSelection.group = selected.group;
    if (typeof selected.label === "string") nextFieldSelection.label = selected.label;
    if (typeof selected.time === "string") nextFieldSelection.time = selected.time;
    if (isRecord(selected.bubble)) {
      nextFieldSelection.bubble = {
        ...nextFieldSelection.bubble,
        ...Object.fromEntries(Object.entries(selected.bubble).filter(([, value]) => typeof value === "string")),
      } as FieldSelection["bubble"];
    }
    if (isRecord(selected.quadrant)) {
      nextFieldSelection.quadrant = {
        ...nextFieldSelection.quadrant,
        ...Object.fromEntries(Object.entries(selected.quadrant).filter(([, value]) => typeof value === "string")),
      } as FieldSelection["quadrant"];
    }
    setFieldSelection(nextFieldSelection);
    if (derivedOptions.length) {
      setDerivedMetricEdits(
        derivedOptions
          .filter(isRecord)
          .map((item) => ({
            field: String(item.field || ""),
            display_name: String(item.display_name_zh || item.display_name || item.field || ""),
            formula: String(item.formula || item.field || ""),
            source_fields: Array.isArray(item.source_fields)
              ? item.source_fields.map((field) => String(field || "")).filter(Boolean)
              : [],
            recipe_id: String(item.recipe_id || "custom"),
            selected: item.selected !== false,
            custom: Boolean(item.custom),
          }))
          .filter((item) => item.field)
          .slice(0, 96),
      );
    }
  }

  function resolvedBindingsFor(selectedIds: string[]) {
    return resolveMethodFieldBindings({
      dataset: selectedDataset,
      derivedMetricEdits,
      fieldSelection,
      methods,
      manualBindings: methodFieldBindings,
      selectedIds,
    });
  }

  function applyMethodCatalog(methodPayload: MethodCatalogResponse) {
    const nextMethods = methodPayload.methods || [];
    const nextReportParts = normalizeReportParts(methodPayload.report_parts);
    setMethods(nextMethods);
    setReportParts(nextReportParts);
    setPriorityMethodIds(methodPayload.priority_method_ids || []);
    if (nextReportParts.length) {
      setSelectedReportPartIds((current) => (current.size ? current : new Set(nextReportParts)));
    }
    setCatalogLoaded(true);
    return { nextMethods, nextReportParts };
  }

  async function refreshMethodCatalog() {
    const methodPayload = await apiRequest<MethodCatalogResponse>("/api/lab/methods?compact=true", { timeoutMs: 60000 });
    return applyMethodCatalog(methodPayload);
  }

  async function saveCurrentMethodCard(method: MethodCatalogItem, activeRun?: MethodRunSpec | null) {
    const runKey = activeRun?.run_id || method.id;
    const fieldBindings = cleanMethodFieldBinding({
      ...methodDefaultBinding(method, fieldSelection, selectedDataset, derivedMetricEdits),
      ...(method.field_bindings || {}),
      ...(methodFieldBindings[method.id] || {}),
      ...(activeRun?.field_bindings || {}),
    });
    setMethodCardSaveBusyId(runKey);
    setError(null);
    setStatus(`正在保存方法卡：${methodDisplayTitle(method)}`);
    try {
      const response = await apiRequest<SavedMethodCardResponse>("/api/lab/method-cards", {
        method: "POST",
        body: JSON.stringify({
          base_method_id: method.id,
          name: `${methodDisplayTitle(method)} · 自定义`,
          description: `${methodGoalText(method)}；已保存字段绑定和运行指导，可在 Lab 方法池中复用。`,
          family: method.family || "learned",
          output_types: method.default_output_types?.length ? method.default_output_types : method.output_types,
          required_roles: method.required_roles,
          field_bindings: fieldBindings,
          selection_mode: activeRun?.selection_mode || methodRecommendedSelectionMode(method),
          object_selection: activeRun?.object_selection || {},
          statistical_options: cleanMethodStatisticalOptions({
            ...(method.statistical_options || {}),
            ...(activeRun?.statistical_options || {}),
          }),
          report_value_hooks: method.report_value_hooks || [],
          usage_guidance: method.usage_guidance || [],
          tags: uniqueStrings([...(method.card_tags || []), "Lab保存", "可复用方法卡"]),
          source_method: method,
        }),
        timeoutMs: 60000,
      });
      const savedMethodId = response.method?.id || "";
      await refreshMethodCatalog();
      if (savedMethodId) {
        replaceSelectedMethods([savedMethodId, ...Array.from(selectedMethodIds)]);
        setMethodSearch(savedMethodId);
        setMethodFilter("selected");
        setSelectedMethodId(savedMethodId);
        setEditorTarget({ methodId: savedMethodId });
        setMethodEditorOpen(true);
      }
      setStatus(`方法卡已保存：${response.method?.name || methodDisplayTitle(method)}`);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "保存方法卡失败。");
      setStatus("保存方法卡失败，请稍后重试。");
    } finally {
      setMethodCardSaveBusyId(null);
    }
  }

  async function runDatasetPreprocessing(uploaded: DatasetItem) {
    const token = workflowTokenRef.current + 1;
    workflowTokenRef.current = token;
    updateWorkflowProgress({
      active: true,
      phase: "understand",
      percent: 28,
      title: "正在理解表格结构",
      detail: "读取字段画像、缺失率、类型和可分析角色。",
    });
    startWorkflowPulse(token, 88);
    const selectedIds = clampMethodIds(
      recommendedMethods(methods, priorityMethodIds, MAX_SELECTED_METHOD_RUNS)
        .filter((method) => methodCanRun(method, uploaded))
        .map((method) => method.id),
    );
    const baseSelection = inferDefaultFieldSelection(uploaded);
    const baseDerivedMetrics = defaultDerivedMetricDrafts(uploaded);
    updateWorkflowProgress({
      phase: "clean",
      percent: 42,
      title: "正在清洗并标准化字段",
      detail: "复用 Lab 后端的读取、类型识别和预处理链。",
    });
    const payload = await apiRequest<StatsResult>("/api/lab/run", {
      method: "POST",
      body: JSON.stringify(
        buildLabRunPayload({
          selectedDatasetId: uploaded.dataset_id,
          selectedSheetName: datasetSheetName(uploaded),
          workspaceBrief: workspaceBrief || "上传后自动完成数据理解、数据清洗和派生指标准备。",
          selectedIds,
          methodRunSpecs: selectedIds.map((methodId, index) =>
            newMethodRunSpec(methodId, index, undefined, methods, {
              dataset: uploaded,
              fieldSelection: baseSelection,
              derivedMetricEdits: baseDerivedMetrics,
            }),
          ),
          selectedReportParts: ["field_glossary", "method_note"],
          executionMode: "smart_merge",
          smartMergeEnabled: true,
          maxMethods: Math.max(1, Math.min(selectedIds.length || 1, MAX_SELECTED_METHOD_RUNS)),
          fieldSelection: baseSelection,
          derivedMetricEdits: baseDerivedMetrics,
          methodFieldBindings: resolveMethodFieldBindings({
            dataset: uploaded,
            derivedMetricEdits: baseDerivedMetrics,
            fieldSelection: baseSelection,
            methods,
            manualBindings: {},
            selectedIds,
          }),
          externalSkillIds: mountedExternalSkillIds,
          externalSkillFeatureSelections: cleanExternalSkillFeatureSelectionList,
        }),
      ),
      timeoutMs: 600000,
    });
    if (workflowTokenRef.current !== token) return;
    stopWorkflowPulse();
    updateWorkflowProgress({
      phase: "derive",
      percent: 92,
      title: "已生成派生指标候选",
      detail: "派生池已回填到字段面板，方法卡可各自选择不同指标。",
    });
    setAutoSummary(payload);
    hydrateAutoAnalysisState(payload, uploaded);
    startTransition(() => {
      setResult({
        mode: "auto",
        title: "上传后自动预处理",
        datasetName: datasetLabel(uploaded),
        createdAt: new Date().toISOString(),
        payload,
      });
    });
    updateWorkflowProgress({
      active: false,
      phase: "ready",
      percent: 100,
      title: "表格已完成理解、清洗和派生",
      detail: "现在可以在每个方法卡里独立选择目标、特征和派生指标。",
    });
  }

  useEffect(() => {
    setVisibleMethodLimit(INITIAL_VISIBLE_METHOD_LIMIT);
  }, [activeMethodFamily, activeMethodSource, methodFilter, methodSearch]);

  useEffect(() => {
    if (!activeMethodFamily) return;
    if (!groupedMethodCounts.some(([family]) => family === activeMethodFamily)) {
      setActiveMethodFamily("");
    }
  }, [activeMethodFamily, groupedMethodCounts]);

  async function refreshExternalSkills(options?: { quiet?: boolean }) {
    try {
      const payload = await apiRequest<ExternalSkillResponse>("/api/lab/skills", { timeoutMs: 60000 });
      setExternalSkills(payload.skills || []);
      if (
        payload.default_source_url &&
        (!externalSkillSourceUrl || externalSkillSourceUrl === LEGACY_EXTERNAL_SKILL_SOURCE_URL)
      ) {
        setExternalSkillSourceUrl(payload.default_source_url);
      }
      if (!options?.quiet) {
        setExternalSkillStatus(
          `${formatNumber(payload.summary.mounted_count || 0)} mounted / ${formatNumber(payload.summary.count || 0)} installed external entries. ${formatNumber(payload.summary.plugin_count || 0)} plugins, ${formatNumber(payload.summary.embedded_skill_count || 0)} embedded skills, ${formatNumber(payload.summary.mcp_server_count || 0)} MCP connectors.`,
        );
      }
      setExternalSkillError(null);
    } catch (skillError) {
      if (!options?.quiet) {
        setExternalSkillError(skillError instanceof Error ? skillError.message : "Unable to load external skills.");
      }
    }
  }

  async function installExternalSkills() {
    setExternalSkillBusyId("__install__");
    setExternalSkillError(null);
    setExternalSkillStatus("Downloading and assembling Anthropic Knowledge Work Plugins...");
    try {
      const payload = await apiRequest<ExternalSkillResponse & { installed_count?: number }>("/api/lab/skills/install", {
        method: "POST",
        body: JSON.stringify({
          source_url: externalSkillSourceUrl || DEFAULT_EXTERNAL_SKILL_SOURCE_URL,
          mount: true,
        }),
        timeoutMs: 180000,
      });
      await refreshExternalSkills({ quiet: true });
      setExternalSkillStatus(`Installed ${formatNumber(payload.installed_count || 0)} plugin/skill packages and mounted them for Lab runs.`);
    } catch (skillError) {
      setExternalSkillError(skillError instanceof Error ? skillError.message : "External skill install failed.");
      setExternalSkillStatus("External skill install failed.");
    } finally {
      setExternalSkillBusyId(null);
    }
  }

  async function importLocalExternalSkill() {
    setExternalSkillBusyId("__import_local__");
    setExternalSkillError(null);
    setExternalSkillStatus("Importing local skill package...");
    try {
      const payload = await apiRequest<ExternalSkillResponse>("/api/lab/skills/import-local", {
        method: "POST",
        body: JSON.stringify({
          local_path: externalSkillLocalPath,
          mount: true,
        }),
        timeoutMs: 120000,
      });
      await refreshExternalSkills({ quiet: true });
      setExternalSkillStatus(
        `Imported local skill from ${payload.local_path || externalSkillLocalPath || "local path"} and mounted it for Lab runs.`,
      );
    } catch (skillError) {
      setExternalSkillError(skillError instanceof Error ? skillError.message : "Local skill import failed.");
      setExternalSkillStatus("Local skill import failed.");
    } finally {
      setExternalSkillBusyId(null);
    }
  }

  async function setExternalSkillMounted(skillId: string, mounted: boolean) {
    setExternalSkillBusyId(skillId);
    setExternalSkillError(null);
    try {
      await apiRequest(`/api/lab/skills/${encodeURIComponent(skillId)}/${mounted ? "mount" : "unmount"}`, {
        method: "POST",
        timeoutMs: 60000,
      });
      await refreshExternalSkills({ quiet: true });
      setExternalSkillStatus(`${mounted ? "Mounted" : "Unmounted"} ${skillId}.`);
    } catch (skillError) {
      setExternalSkillError(skillError instanceof Error ? skillError.message : "External skill update failed.");
    } finally {
      setExternalSkillBusyId(null);
    }
  }

  async function deleteExternalSkill(skillId: string) {
    setExternalSkillBusyId(skillId);
    setExternalSkillError(null);
    try {
      await apiRequest(`/api/lab/skills/${encodeURIComponent(skillId)}`, {
        method: "DELETE",
        timeoutMs: 60000,
      });
      await refreshExternalSkills({ quiet: true });
      setExternalSkillStatus(`Deleted ${skillId}.`);
    } catch (skillError) {
      setExternalSkillError(skillError instanceof Error ? skillError.message : "External skill delete failed.");
    } finally {
      setExternalSkillBusyId(null);
    }
  }

  async function runFeatureTrial(skill: ExternalSkillItem, featureKind: "command" | "embedded_skill", featureId: string) {
    if (!selectedDatasetId) {
      setExternalSkillError("Select or upload a dataset before running a feature trial.");
      return;
    }
    const trialKey = `${skill.id}:${featureKind}:${featureId}`;
    setFeatureTrialBusyId(trialKey);
    setExternalSkillError(null);
    setExternalSkillStatus(`Running feature trial: ${featureId}`);
    try {
      const payload = await apiRequest<LabFeatureTrialResult>("/api/lab/feature-trials/run", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          active_sheet: selectedSheetName || null,
          plugin_id: skill.id,
          feature_kind: featureKind,
          feature_id: featureId,
          user_goal: workspaceBrief,
        }),
        timeoutMs: 120000,
      });
      setFeatureTrialResult(payload);
      setExternalSkillStatus(
        `Trial complete: ${payload.feature?.name || featureId} scored ${formatNumber(payload.enhancement_effect?.readiness_score || 0)}/100 readiness.`,
      );
    } catch (trialError) {
      setExternalSkillError(trialError instanceof Error ? trialError.message : "Feature trial failed.");
      setExternalSkillStatus("Feature trial failed.");
    } finally {
      setFeatureTrialBusyId(null);
    }
  }

  function toggleExternalSkillFeatureSelection(selection: ExternalSkillFeatureSelection) {
    setExternalSkillFeatureSelections((current) => {
      const key = externalSkillFeatureSelectionKey(selection);
      const exists = current.some((item) => externalSkillFeatureSelectionKey(item) === key);
      if (exists) {
        return current.filter((item) => externalSkillFeatureSelectionKey(item) !== key);
      }
      return [
        ...current,
        {
          ...selection,
          selection_source: selection.selection_source || "analysis_lab_report_flow",
        },
      ];
    });
  }

  async function refreshReportAgentTeams(options?: { quiet?: boolean }) {
    try {
      const payload = await apiRequest<LabReportAgentTeamResponse>("/api/lab/report-agent-teams", { timeoutMs: 60000 });
      setReportAgentTeams(payload.teams || []);
      if (!options?.quiet) {
        setReportAgentTeamStatus(
          `${formatNumber(payload.summary.mounted_count || 0)} mounted / ${formatNumber(payload.summary.count || 0)} report agent teams.`,
        );
      }
      setReportAgentTeamError(null);
    } catch (teamError) {
      if (!options?.quiet) {
        setReportAgentTeamError(teamError instanceof Error ? teamError.message : "Unable to load report agent teams.");
      }
    }
  }

  async function importLocalReportAgentTeam() {
    setReportAgentTeamBusyId("__import_team__");
    setReportAgentTeamError(null);
    setReportAgentTeamStatus("Importing local report agent team...");
    try {
      const payload = await apiRequest<LabReportAgentTeamResponse>("/api/lab/report-agent-teams/import-local", {
        method: "POST",
        body: JSON.stringify({
          local_path: reportAgentTeamLocalPath,
          mount: true,
        }),
        timeoutMs: 120000,
      });
      await refreshReportAgentTeams({ quiet: true });
      setReportAgentTeamStatus(
        `Imported local report agent team from ${payload.local_path || reportAgentTeamLocalPath || "local path"}.`,
      );
    } catch (teamError) {
      setReportAgentTeamError(teamError instanceof Error ? teamError.message : "Local report agent team import failed.");
      setReportAgentTeamStatus("Local report agent team import failed.");
    } finally {
      setReportAgentTeamBusyId(null);
    }
  }

  async function setReportAgentTeamMounted(teamId: string, mounted: boolean) {
    setReportAgentTeamBusyId(teamId);
    setReportAgentTeamError(null);
    try {
      await apiRequest(`/api/lab/report-agent-teams/${encodeURIComponent(teamId)}/${mounted ? "mount" : "unmount"}`, {
        method: "POST",
        timeoutMs: 60000,
      });
      await refreshReportAgentTeams({ quiet: true });
      setReportAgentTeamStatus(`${mounted ? "Mounted" : "Unmounted"} ${teamId}.`);
    } catch (teamError) {
      setReportAgentTeamError(teamError instanceof Error ? teamError.message : "Report agent team update failed.");
    } finally {
      setReportAgentTeamBusyId(null);
    }
  }

  async function deleteReportAgentTeam(teamId: string) {
    setReportAgentTeamBusyId(teamId);
    setReportAgentTeamError(null);
    try {
      await apiRequest(`/api/lab/report-agent-teams/${encodeURIComponent(teamId)}`, {
        method: "DELETE",
        timeoutMs: 60000,
      });
      await refreshReportAgentTeams({ quiet: true });
      setReportAgentTeamStatus(`Deleted ${teamId}.`);
    } catch (teamError) {
      setReportAgentTeamError(teamError instanceof Error ? teamError.message : "Report agent team delete failed.");
    } finally {
      setReportAgentTeamBusyId(null);
    }
  }

  async function runReportAgentTeam() {
    if (!selectedDatasetId) {
      setReportAgentTeamError("请先选择或上传一个数据集，再启动写报告 agent 团队。");
      return;
    }
    if (!mountedReportAgentTeamIds.length) {
      setReportAgentTeamError("请先至少挂载一个写报告 agent 团队。");
      return;
    }
    setReportAgentTeamBusyId("__run_team__");
    setReportAgentTeamError(null);
    setReportAgentTeamStatus("Starting report agent team with Codex CLI...");
    try {
      const reportId = `lab-agent-team-${selectedDatasetId}-${Date.now()}`;
      const payload = await apiRequest<{
        task?: Record<string, unknown>;
        workspace_path?: string;
        mounted_team_ids?: string[];
      }>("/api/lab/report-agent-teams/run", {
        method: "POST",
        body: JSON.stringify({
          report_id: reportId,
          dataset_id: selectedDatasetId,
          sheet_name: selectedSheetName || "Sheet1",
          user_requirement: workspaceBrief || "请生成一份可交付的管理报告，并协调团队成员分工写作。",
          team_ids: mountedReportAgentTeamIds,
        }),
        timeoutMs: 120000,
      });
      setReportAgentTeamTask(payload.task || null);
      setReportAgentTeamStatus(
        `Started report agent team job for ${formatNumber(mountedReportAgentTeamIds.length)} mounted team(s). Workspace: ${payload.workspace_path || "created by backend"}`,
      );
    } catch (teamError) {
      setReportAgentTeamError(teamError instanceof Error ? teamError.message : "Report agent team run failed.");
      setReportAgentTeamStatus("Report agent team run failed.");
    } finally {
      setReportAgentTeamBusyId(null);
    }
  }

  useEffect(() => {
    if (!selectedDatasetId) {
      setDatasetDetail(null);
      setFieldSelection(EMPTY_FIELD_SELECTION);
      setDerivedMetricEdits([]);
      setMethodFieldBindings({});
      return;
    }
    let alive = true;
    async function loadDatasetDetail() {
      try {
        const payload = await apiRequest<DatasetItem>(`/api/datasets/${selectedDatasetId}?summary=true`, { timeoutMs: 60000 });
        if (!alive) return;
        setDatasetDetail(payload);
        setFieldSelection(inferDefaultFieldSelection(payload));
        setDerivedMetricEdits(defaultDerivedMetricDrafts(payload));
        setMethodFieldBindings({});
        setMethodRunSpecs((current) =>
          current.map((spec) => {
            const method = methodsById.get(spec.method_id);
            if (!method) return spec;
            const nextFieldSelection = inferDefaultFieldSelection(payload);
            const nextDerivedMetrics = defaultDerivedMetricDrafts(payload);
            const nextBinding = cleanMethodFieldBinding({
              ...methodDefaultBinding(method, nextFieldSelection, payload, nextDerivedMetrics),
              ...pruneMethodFieldBinding(spec.field_bindings || {}, payload, nextDerivedMetrics),
            });
            return {
              ...spec,
              field_bindings: nextBinding,
              object_selection:
                spec.selection_mode === "object"
                  ? {
                      ...(spec.object_selection || {}),
                      object_type: spec.object_selection?.object_type || method.role_labels?.[0] || currentBindingLabelFallback(nextBinding, nextFieldSelection),
                      merge_mode: spec.object_selection?.merge_mode || "smart",
                      object_keys: uniqueStrings(spec.object_selection?.object_keys || []),
                      group_key: spec.object_selection?.group_key || nextBinding.group || nextFieldSelection.group || "",
                      label_key: spec.object_selection?.label_key || nextBinding.label || nextBinding.entity || nextFieldSelection.label || "",
                      selection_source: spec.object_selection?.selection_source || "fields",
                    }
                  : spec.object_selection,
              smart_merge_group: spec.smart_merge_group || nextBinding.group || "",
            };
          }),
        );
      } catch (detailError) {
        if (!alive) return;
        setDatasetDetail(null);
        setError(detailError instanceof Error ? detailError.message : "数据集字段详情加载失败，请刷新或检查服务连接。");
      }
    }
    void loadDatasetDetail();
    return () => {
      alive = false;
    };
  }, [selectedDatasetId, selectedSheetName]);

  useEffect(() => {
    let alive = true;

    async function loadInitial() {
      const loadDatasets = async () => {
        try {
          const datasetPayload = await apiRequest<DatasetListResponse>("/api/datasets?compact=true", { timeoutMs: 60000 });
          if (!alive) return;
          const nextDatasets = datasetPayload.datasets || [];
          setDatasets(nextDatasets);
          if (nextDatasets[0]) {
            const firstDataset = nextDatasets[0];
            setSelectedDatasetId(firstDataset.dataset_id);
            setSelectedSheet(datasetSheetName(firstDataset));
          }
        } catch (loadError) {
          if (alive) {
            setError(loadError instanceof Error ? loadError.message : "数据集列表加载失败，请刷新或检查服务连接。");
          }
        }
      };

      void loadDatasets();
      void refreshExternalSkills({ quiet: true });
      void refreshReportAgentTeams({ quiet: true });

      try {
        const methodPayload = await apiRequest<MethodCatalogResponse>("/api/lab/methods?compact=true", { timeoutMs: 60000 });
        if (!alive) return;
        const { nextMethods, nextReportParts } = applyMethodCatalog(methodPayload);
        setSelectedReportPartIds(new Set(nextReportParts));
        const methodAliases = methodPayload.method_aliases || {};
        const priority = methodPayload.priority_method_ids?.length
          ? methodPayload.priority_method_ids
          : nextMethods
              .filter((method) => method.family === "visual" || method.status === "live")
              .slice(0, 12)
              .map((method) => method.id);
        const nextPriority = clampMethodIds(
          priority
            .map((methodId) => methodAliases[methodId] || methodId)
            .filter((methodId) => nextMethods.some((method) => method.id === methodId)),
          DEFAULT_SELECTED_METHOD_RUNS,
        );
        const nextPrioritySet = new Set(nextPriority);
        const fallbackIds = clampMethodIds(nextMethods.map((method) => method.id), DEFAULT_SELECTED_METHOD_RUNS);
        const defaultSelectedIds = nextPrioritySet.size ? nextPriority : fallbackIds;
        setSelectedMethodIds(new Set(defaultSelectedIds));
        setMethodRunSpecs(defaultSelectedIds.map((methodId, index) => newMethodRunSpec(methodId, index, undefined, nextMethods)));
        setActiveMethodRunIds(
          Object.fromEntries(defaultSelectedIds.map((methodId, index) => [methodId, `${methodId}__run_${index + 1}`])),
        );
        const nextSelectedMethodId =
          nextPriority[0] ||
          nextMethods.find((method) => method.status === "live" || method.family === "visual")?.id ||
          nextMethods[0]?.id ||
          "";
        if (nextSelectedMethodId) setSelectedMethodId(nextSelectedMethodId);
        setVisibleMethodLimit(INITIAL_VISIBLE_METHOD_LIMIT);
        setMethodFilter("all");
        setStatus(
          `Lab 方法目录已加载：${formatNumber(nextMethods.length)} 个方法，其中可视化 ${formatNumber(nextMethods.filter((method) => method.family === "visual" || method.output_types?.includes("chart") || method.output_types?.includes("image_spec")).length)} 个。`,
        );
      } catch (loadError) {
        if (alive) {
          setCatalogLoaded(false);
          setError(loadError instanceof Error ? loadError.message : "方法目录加载失败，请刷新或检查服务连接。");
        }
      }
    }

    void loadInitial();
    return () => {
      alive = false;
    };
  }, []);

  async function refreshDatasets(preselectId?: string) {
    const payload = await apiRequest<DatasetListResponse>("/api/datasets?compact=true", {
      timeoutMs: 60000,
    });
    const nextDatasets = payload.datasets || [];
    setDatasets(nextDatasets);
    const nextSelected =
      nextDatasets.find((dataset) => dataset.dataset_id === preselectId) ||
      nextDatasets.find((dataset) => dataset.dataset_id === selectedDatasetId) ||
      nextDatasets[0];
    if (nextSelected) {
      setSelectedDatasetId(nextSelected.dataset_id);
      setSelectedSheet(datasetSheetName(nextSelected));
    }
  }

  async function handleUpload() {
    if (!selectedFile) {
      setError("请先选择一个 CSV、TSV、DTA 或 Excel 文件。");
      return;
    }

    setError(null);
    setIsUploading(true);
    setMethodFieldBindings({});
    setStatus("正在上传表格并启动预处理...");
    const token = workflowTokenRef.current + 1;
    workflowTokenRef.current = token;
    updateWorkflowProgress({
      active: true,
      phase: "upload",
      percent: 8,
      title: "正在上传表格",
      detail: "文件进入数据工作区，随后会自动触发理解、清洗和派生。",
    });
    startWorkflowPulse(token, 25);

    try {
      const form = new FormData();
      form.append("file", selectedFile);
      const uploaded = await apiRequest<DatasetItem>("/api/datasets/upload", {
        method: "POST",
        body: form,
        timeoutMs: 180000,
      });
      if (workflowTokenRef.current !== token) return;
      updateWorkflowProgress({
        phase: "understand",
        percent: 20,
        title: "正在识别字段结构",
        detail: "上传成功，开始读取列类型、缺失率和列摘要。",
      });
      try {
        await refreshDatasets(uploaded.dataset_id);
        if (workflowTokenRef.current !== token) return;
        if (shouldAutoPreprocessDataset(uploaded)) {
          updateWorkflowProgress({
            phase: "clean",
            percent: 36,
            title: "正在清洗和标准化",
            detail: "准备调用 Lab 长链路，自动补充派生指标和方法路由依据。",
          });
          await runDatasetPreprocessing(uploaded);
          setStatus(`${datasetLabel(uploaded)} 已完成自动理解、清洗和派生。`);
        } else {
          setStatus(largeDatasetReadyStatus(uploaded));
          stopWorkflowPulse();
          updateWorkflowProgress({
            active: false,
            phase: "ready",
            percent: 100,
            title: "Large dataset ready",
            detail: "Auto preprocessing was skipped to keep the workspace responsive. Click the run button when you want to start analysis.",
          });
        }
      } catch (postUploadError) {
        if (workflowTokenRef.current !== token) return;
        setError(postUploadError instanceof Error ? postUploadError.message : "预处理失败。");
        setStatus("上传成功，但后续预处理失败，请查看错误信息。");
        stopWorkflowPulse();
        updateWorkflowProgress({
          active: false,
          phase: "failed",
          percent: 0,
          title: "预处理失败",
          detail: "上传已完成，但刷新数据集或理解、清洗、派生阶段出错。",
        });
        return;
      }
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "上传失败。");
      setStatus("上传失败，请检查文件后重试。");
      stopWorkflowPulse();
      updateWorkflowProgress({
        active: false,
        phase: "failed",
        percent: 0,
        title: "预处理失败",
        detail: "请检查文件格式或网络后重试。",
      });
    } finally {
      setIsUploading(false);
      stopWorkflowPulse();
    }
  }

  async function runAutoAnalysis() {
    if (!selectedDatasetId) {
      setError("请先选择或上传一个数据集。");
      return;
    }
    if (selectedExecutionBlockReason) {
      setError(selectedExecutionBlockReason);
      setStatus("已保留方法卡配置；请补齐数据字段或运行时后再执行。");
      return;
    }
    setError(null);
    setIsRunning(true);
    setStatus("正在自动清洗、生成派生指标，并按已选择方法输出总合并解读...");
    try {
      const runSpecs = selectedRunSpecs.length
        ? selectedRunSpecs
        : availableSingleMethods.map((item, index) => newMethodRunSpec(item.id, index));
      const selectedIds = methodIdsFromRunSpecs(runSpecs);
      const resolvedBindings = resolvedBindingsFor(selectedIds);
      const payload = await apiRequest<StatsResult>("/api/lab/run", {
        method: "POST",
        body: JSON.stringify(
          buildLabRunPayload({
            selectedDatasetId,
            selectedSheetName,
            workspaceBrief,
            selectedIds,
            methodRunSpecs: runSpecs,
            selectedReportParts,
            executionMode: "smart_merge",
            smartMergeEnabled: true,
            maxMethods: Math.max(1, runSpecs.length),
            fieldSelection,
            derivedMetricEdits,
            methodFieldBindings: resolvedBindings,
            externalSkillIds: mountedExternalSkillIds,
            externalSkillFeatureSelections: cleanExternalSkillFeatureSelectionList,
          }),
        ),
        timeoutMs: 600000,
      });
      setAutoSummary(payload);
      startTransition(() => {
        setResult({
          mode: "auto",
          title: "自动清洗 + 派生 + 方法路由",
          datasetName: datasetLabel(selectedDataset),
          createdAt: new Date().toISOString(),
          payload,
        });
      });
      setStatus(
        runSpecs.length > 1
          ? `总合并已完成：本次纳入 ${formatNumber(runSpecs.length)} 个方法实例，并保留了独立执行产物。`
          : "单方法执行已完成。",
      );
    } catch (autoError) {
      setError(autoError instanceof Error ? autoError.message : "自动分析失败。");
      setStatus("自动分析失败，请检查数据集或退回单方法执行。");
    } finally {
      setIsRunning(false);
    }
  }

  async function runSmartReport() {
    if (!selectedDatasetId) {
      setError("请先选择或上传一个数据集。");
      return;
    }
    setError(null);
    setIsRunning(true);
    setStatus("正在生成总合并智能解读...");
    try {
      const payload = await apiRequest<SmartReport>(`/api/datasets/${selectedDatasetId}/smart-report`, {
        method: "POST",
        body: JSON.stringify({
          sheet_name: selectedSheetName || null,
          report_style: "deep_dive",
          business_profile: "auto",
          report_part: selectedReportParts.join(",") || "auto",
          selected_report_parts: selectedReportParts,
          user_requirement: buildUserGoalForRun(workspaceBrief, selectedRunCount || methods.length, { includeCli: true }),
          raw_user_requirement: workspaceBrief,
          enable_generic_business_runtime: true,
        }),
        timeoutMs: 600000,
      });
      setAutoSummary(payload);
      startTransition(() => {
        setResult({
          mode: "smart_report",
          title: "总合并智能解读",
          datasetName: datasetLabel(selectedDataset),
          createdAt: new Date().toISOString(),
          payload,
        });
      });
      setStatus("总合并智能解读已完成。");
    } catch (reportError) {
      setError(reportError instanceof Error ? reportError.message : "智能报告失败。");
      setStatus("智能报告失败。");
    } finally {
      setIsRunning(false);
    }
  }

  async function runSingleMethod(method: MethodCatalogItem) {
    if (!selectedDatasetId) {
      setError("请先选择或上传一个数据集。");
      return;
    }
    const runBlockReason = methodRunBlockReason(method, selectedDataset);
    if (runBlockReason) {
      setError(`${methodDisplayTitle(method)}：${runBlockReason}`);
      setStatus("方法卡仍可编辑和保存；当前数据或运行时满足条件后即可执行。");
      return;
    }
    setError(null);
    setIsRunning(true);
    setStatus(`正在先清洗与派生，再独立执行方法：${methodDisplayTitle(method)}`);
    try {
      const selectedIds = [method.id];
      const activeRunId = activeMethodRunIds[method.id];
      const activeRun =
        (activeRunId ? methodRunSpecs.find((spec) => spec.method_id === method.id && spec.run_id === activeRunId) : null) ||
        methodRunSpecs.find((spec) => spec.method_id === method.id) ||
        null;
      const runSpecs = activeRun
        ? [activeRun]
        : [newMethodRunSpec(method.id, 0, { selection_mode: methodRecommendedSelectionMode(method) })];
      const resolvedBindings = resolvedBindingsFor(selectedIds);
      const payload = await apiRequest<StatsResult>("/api/lab/run", {
        method: "POST",
        body: JSON.stringify(
          buildLabRunPayload({
            selectedDatasetId,
            selectedSheetName,
            workspaceBrief,
            selectedIds,
            methodRunSpecs: runSpecs,
            selectedReportParts: normalizeReportParts(selectedReportParts),
            executionMode: "smart_merge",
            smartMergeEnabled: true,
            maxMethods: 1,
            fieldSelection,
            derivedMetricEdits,
            methodFieldBindings: resolvedBindings,
            externalSkillIds: mountedExternalSkillIds,
            externalSkillFeatureSelections: cleanExternalSkillFeatureSelectionList,
          }),
        ),
        timeoutMs: 240000,
      });
      const nextRuns = materializeMethodRunResults({
        payload,
        methods,
        runSpecs,
      });
      const nextRunIds = new Set(runSpecs.map((spec) => spec.run_id));
      setMethodRuns((current) => [...nextRuns, ...current.filter((item) => !nextRunIds.has(item.method_run_id))]);
      startTransition(() => {
        setResult({
          mode: "method",
          title: methodDisplayTitle(method),
          datasetName: datasetLabel(selectedDataset),
          createdAt: new Date().toISOString(),
          payload,
        });
      });
      setStatus(`方法执行完成：${methodDisplayTitle(method)}`);
    } catch (methodError) {
      setError(methodError instanceof Error ? methodError.message : "方法执行失败。");
      setStatus("方法执行失败。");
    } finally {
      setIsRunning(false);
    }
  }

  async function runSelectedMethods() {
    if (!selectedDatasetId) {
      setError("请先选择或上传一个数据集。");
      return;
    }
    const batchRunSpecs = selectedRunSpecs;
    const selectedIds = methodIdsFromRunSpecs(batchRunSpecs);
    if (!batchRunSpecs.length) {
      setError("请先勾选至少一个 Lab 方法。");
      return;
    }
    if (selectedExecutionBlockReason) {
      setError(selectedExecutionBlockReason);
      setStatus("已保留方法卡配置；请补齐数据字段或运行时后再执行。");
      return;
    }
    const resolvedBindings = resolvedBindingsFor(selectedIds);
    setError(null);
    setIsRunning(true);
    setStatus(`正在先清洗与派生，再批量执行 ${formatNumber(batchRunSpecs.length)} 个已选方法实例，并生成各自独立结果再做智能合并...`);
    try {
      const payload = await apiRequest<StatsResult>("/api/lab/run", {
        method: "POST",
        body: JSON.stringify(
          buildLabRunPayload({
            selectedDatasetId,
            selectedSheetName,
            workspaceBrief,
            selectedIds,
            methodRunSpecs: batchRunSpecs,
            selectedReportParts,
            executionMode: batchRunSpecs.length > 1 ? "smart_merge" : "separate",
            smartMergeEnabled: true,
            maxMethods: Math.max(batchRunSpecs.length, 1),
            fieldSelection,
            derivedMetricEdits,
            methodFieldBindings: resolvedBindings,
            externalSkillIds: mountedExternalSkillIds,
            externalSkillFeatureSelections: cleanExternalSkillFeatureSelectionList,
          }),
        ),
        timeoutMs: 600000,
      });
      const nextRuns = materializeMethodRunResults({
        payload,
        methods,
        runSpecs: batchRunSpecs,
      });
      const batchRunIds = new Set(batchRunSpecs.map((spec) => spec.run_id));
      setMethodRuns((current) => [
        ...nextRuns,
        ...current.filter((item) => !batchRunIds.has(item.method_run_id)),
      ]);
      setAutoSummary(payload);
      startTransition(() => {
        setResult({
          mode: "batch",
          title: `批量独立执行 ${batchRunSpecs.length} 个方法实例`,
          datasetName: datasetLabel(selectedDataset),
          createdAt: new Date().toISOString(),
          payload,
        });
      });
      setStatus(
        batchRunSpecs.length > 1
          ? `批量执行完成：${formatNumber(nextRuns.length)} 个方法返回独立执行资产，并保留智能合并。`
          : `单方法执行完成：${formatNumber(nextRuns.length)} 个方法返回执行资产。`,
      );
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "批量方法执行失败。");
      setStatus("批量方法执行失败。");
    } finally {
      setIsRunning(false);
    }
  }

  async function rerunBlueprintPart(
    analysisResult: StatsResult,
    workspaceResult: WorkspaceResult,
    blueprint: AutoReportPartGenerationBlueprint,
  ) {
    const datasetId = String((analysisResult.data as { dataset_id?: string } | undefined)?.dataset_id || "").trim();
    if (!datasetId) {
      setError("Rerun is missing the source dataset id.");
      return;
    }
    const rawSheetName = (analysisResult.data as { sheet_name?: string } | undefined)?.sheet_name;
    const activeSheet = typeof rawSheetName === "string" && rawSheetName.trim() ? rawSheetName.trim() : null;
    const selectedIds = blueprintMethodIds(blueprint);
    const blueprintLabel = blueprint.report_part_title || blueprint.report_part_id;
    const maxMethods = selectedIds.length || 24;
    const resolvedBindings = resolvedBindingsFor(selectedIds);
    setError(null);
    setIsRunning(true);
    setPartRunBusy(blueprint.report_part_id);
    setStatus(`Rerunning blueprint part: ${blueprintLabel}`);
    try {
      const payload = await apiRequest<StatsResult>("/api/lab/run", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: datasetId,
          active_sheet: activeSheet,
          user_goal: workspaceBrief || workspaceResult.title || blueprintLabel,
          report_part: blueprint.report_part_id,
          max_methods: maxMethods,
          max_derived_fields: 64,
          max_chart_points: 180,
          execution_mode: "smart_merge",
          selected_method_ids: selectedIds,
          method_run_specs: cleanMethodRunSpecs(selectedIds.map((methodId, index) => newMethodRunSpec(methodId, index))),
          selected_fields: cleanFieldSelection(fieldSelection),
          selected_derived_fields: cleanDerivedMetricEdits(derivedMetricEdits).map((edit) => edit.field),
          derived_metric_edits: cleanDerivedMetricEdits(derivedMetricEdits),
          method_field_bindings: resolvedBindings,
          external_skill_ids: mountedExternalSkillIds,
          external_skill_feature_selections: cleanExternalSkillFeatureSelectionList,
          cli_interpretation_enabled: true,
          business_interpretation_enabled: true,
          method_independent_output_enabled: true,
          smart_merge_enabled: true,
        }),
        timeoutMs: 600000,
      });
      setAutoSummary(payload);
      startTransition(() => {
        setResult({
          mode: "auto",
          title: `${blueprintLabel} rerun`,
          datasetName: workspaceResult.datasetName,
          createdAt: new Date().toISOString(),
          payload,
        });
      });
      setStatus(`Reran ${blueprintLabel} with ${formatNumber(maxMethods)} methods.`);
    } catch (rerunError) {
      setError(rerunError instanceof Error ? rerunError.message : "Report part rerun failed.");
      setStatus(`Blueprint rerun failed: ${blueprintLabel}`);
    } finally {
      setPartRunBusy(null);
      setIsRunning(false);
    }
  }

  function selectMethod(methodId: string) {
    setSelectedMethodId(methodId);
    if (methodId) {
      const activeRunId = activeMethodRunIds[methodId];
      setEditorTarget(activeRunId ? { methodId, runId: activeRunId } : { methodId });
    }
  }

  function replaceSelectedMethods(methodIds: string[]) {
    const normalizedIds = clampMethodIds(methodIds);
    const next = new Set(normalizedIds);
    setSelectedMethodIds(next);
    const nextSelectedMethodId = normalizedIds.find(Boolean) || "";
    if (nextSelectedMethodId) {
      setSelectedMethodId(nextSelectedMethodId);
    }
    let nextActiveMethodRunIds: Record<string, string> | null = null;
    setMethodRunSpecs((current) => {
      const expectedCounts = new Map<string, number>();
      for (const methodId of normalizedIds) {
        expectedCounts.set(methodId, (expectedCounts.get(methodId) || 0) + 1);
      }
      const preservedCounts = new Map<string, number>();
      const preserved: MethodRunSpec[] = [];
      for (const spec of current) {
        const expectedCount = expectedCounts.get(spec.method_id) || 0;
        const preservedCount = preservedCounts.get(spec.method_id) || 0;
        if (!expectedCount || preservedCount >= expectedCount || preserved.length >= MAX_SELECTED_METHOD_RUNS) continue;
        preserved.push(spec);
        preservedCounts.set(spec.method_id, preservedCount + 1);
      }
      const counts = new Map<string, number>();
      const missing: MethodRunSpec[] = [];
      for (const methodId of normalizedIds) {
        const existingCount = counts.get(methodId) || 0;
        const existingRuns = preserved.filter((spec) => spec.method_id === methodId);
        if (!existingRuns[existingCount]) {
          missing.push(newMethodRunSpec(methodId, existingCount));
        }
        counts.set(methodId, existingCount + 1);
      }
      const reconciled = (missing.length ? [...preserved, ...missing] : preserved).slice(0, MAX_SELECTED_METHOD_RUNS);
      const nextActive: Record<string, string> = {};
      for (const spec of reconciled) {
        if (!next.has(spec.method_id) || nextActive[spec.method_id]) continue;
        const preferredActiveRunId = activeMethodRunIds[spec.method_id];
        const preferredRun = preferredActiveRunId
          ? reconciled.find((item) => item.method_id === spec.method_id && item.run_id === preferredActiveRunId)
          : null;
        nextActive[spec.method_id] = preferredRun?.run_id || spec.run_id;
      }
      nextActiveMethodRunIds = nextActive;
      return reconciled;
    });
    if (nextActiveMethodRunIds) {
      setActiveMethodRunIds(nextActiveMethodRunIds);
    }
  }

  function newMethodRunSpec(
    methodId: string,
    index: number,
    overrides?: Partial<MethodRunSpec>,
    methodSource: MethodCatalogItem[] = methods,
    bindingContext?: {
      dataset?: DatasetItem;
      fieldSelection?: FieldSelection;
      derivedMetricEdits?: DerivedMetricEdit[];
    },
  ): MethodRunSpec {
    const method = methodSource.find((item) => item.id === methodId);
    const bindingFieldSelection = bindingContext?.fieldSelection || fieldSelection;
    const bindingDataset = bindingContext?.dataset || selectedDataset;
    const bindingDerivedMetrics = bindingContext?.derivedMetricEdits || derivedMetricEdits;
    const smartBindings = method
      ? methodDefaultBinding(method, bindingFieldSelection, bindingDataset, bindingDerivedMetrics)
      : {};
    const existingBindings = cleanMethodFieldBinding({
      ...smartBindings,
      ...(method?.field_bindings || {}),
      ...pruneMethodFieldBinding(methodFieldBindings[methodId] || {}, bindingDataset, bindingDerivedMetrics),
    });
    const label = overrides?.label?.trim() || `${methodSubmethodTitle(method || ({} as MethodCatalogItem))} #${index + 1}`;
    const selectionMode = overrides?.selection_mode || methodRecommendedSelectionMode(method);
    const nextFieldBindings = overrides?.field_bindings
      ? cleanMethodFieldBinding({ ...existingBindings, ...overrides.field_bindings })
      : existingBindings;
    return {
      run_id: overrides?.run_id || `${methodId}__run_${index + 1}`,
      method_id: methodId,
      label,
      bundle_run_id: overrides?.bundle_run_id,
      bundle_title: overrides?.bundle_title,
      selection_mode: selectionMode,
      field_bindings: nextFieldBindings,
      statistical_options: cleanMethodStatisticalOptions({
        ...(method?.statistical_options || {}),
        ...(overrides?.statistical_options || {}),
      }),
      object_selection:
        overrides?.object_selection ||
        method?.object_selection ||
        (selectionMode === "object"
          ? {
              object_type: method?.role_labels?.[0] || currentBindingLabelFallback(nextFieldBindings, bindingFieldSelection),
              merge_mode: "smart",
              object_keys: [],
              group_key: nextFieldBindings.group || bindingFieldSelection.group || "",
              label_key: nextFieldBindings.label || nextFieldBindings.entity || bindingFieldSelection.label || "",
              filter_field: nextFieldBindings.label || nextFieldBindings.entity || bindingFieldSelection.label || bindingFieldSelection.group || "",
              filter_values: [],
              filter_operator: "in",
              selection_source: "fields",
            }
          : undefined),
      smart_merge_group: overrides?.smart_merge_group || nextFieldBindings.group || "",
    };
  }

  function buildBundleRunGroupSpecs(bundle: MethodBundle, baseRuns: MethodRunSpec[], contextDataset = selectedDataset) {
    const defaults = bundleInteractionState(bundle, contextDataset).defaults;
    if (!defaults.length) return { runs: [] as MethodRunSpec[], requiredSlots: 0 };
    const groupIndex = bundleRunGroups(bundle, baseRuns).length + 1;
    const bundleRunId = `${bundle.id.replace(/^bundle-/, "bundle")}__group_${Date.now()}_${groupIndex}`;
    const methodCounts = new Map<string, number>();
    for (const run of baseRuns) {
      methodCounts.set(run.method_id, (methodCounts.get(run.method_id) || 0) + 1);
    }
    const sharedBinding = cleanMethodFieldBinding({
      ...methodDefaultBinding(bundle.representative, fieldSelection, contextDataset, derivedMetricEdits),
      ...(methodFieldBindings[bundle.representative.id] || {}),
    });
    return {
      requiredSlots: defaults.length,
      runs: defaults.map((method) => {
        const nextIndex = methodCounts.get(method.id) || 0;
        methodCounts.set(method.id, nextIndex + 1);
        return newMethodRunSpec(
          method.id,
          nextIndex,
          {
            bundle_run_id: bundleRunId,
            bundle_title: bundle.title,
            field_bindings: sharedBinding,
            label: `${bundle.title} · ${methodOutputLabel(method)} #${groupIndex}`,
          },
          methods,
          { dataset: contextDataset, fieldSelection, derivedMetricEdits },
        );
      }),
    };
  }

  function commitAddedMethodRuns(nextRuns: MethodRunSpec[], appendedRuns: MethodRunSpec[]) {
    if (!appendedRuns.length) {
      setError(`当前已达到 ${MAX_SELECTED_METHOD_RUNS} 个子项上限。请移除已选子方法后再添加。`);
      return;
    }
    setError(null);
    setMethodRunSpecs(nextRuns.slice(0, MAX_SELECTED_METHOD_RUNS));
    setSelectedMethodIds(new Set(clampMethodIds(methodIdsFromRunSpecs(nextRuns))));
    const focusRun = appendedRuns[0];
    setSelectedMethodId(focusRun.method_id);
    setActiveMethodRunIds((active) => ({
      ...active,
      ...Object.fromEntries(appendedRuns.map((run) => [run.method_id, run.run_id])),
    }));
    setEditorTarget({ methodId: focusRun.method_id, runId: focusRun.run_id });
    setMethodEditorOpen(true);
  }

  function addMethodBundleRunGroup(bundle: MethodBundle, options?: { replaceExisting?: boolean }) {
    const baseRuns = options?.replaceExisting
      ? methodRunSpecs.filter((spec) => !bundle.methods.some((method) => method.id === spec.method_id))
      : methodRunSpecs;
    const { runs, requiredSlots } = buildBundleRunGroupSpecs(bundle, baseRuns);
    if (!runs.length) {
      selectMethod(bundle.representative.id);
      return;
    }
    if (MAX_SELECTED_METHOD_RUNS - baseRuns.length < requiredSlots) {
      setError(`这组方法需要 ${requiredSlots} 个子方法槽位。当前上限为 ${MAX_SELECTED_METHOD_RUNS} 个，请移除已选子方法后再添加。`);
      return;
    }
    commitAddedMethodRuns([...baseRuns, ...runs], runs);
  }

  function addMethodBundleRunGroups(bundles: MethodBundle[]) {
    let workingRuns = [...methodRunSpecs];
    const appendedRuns: MethodRunSpec[] = [];
    for (const bundle of bundles) {
      const { runs, requiredSlots } = buildBundleRunGroupSpecs(bundle, workingRuns);
      if (!runs.length) continue;
      if (MAX_SELECTED_METHOD_RUNS - workingRuns.length < requiredSlots) break;
      workingRuns = [...workingRuns, ...runs].slice(0, MAX_SELECTED_METHOD_RUNS);
      appendedRuns.push(...runs);
    }
    commitAddedMethodRuns(workingRuns, appendedRuns);
  }

  function appendMethodRun(methodId: string, overrides?: Partial<MethodRunSpec>) {
    selectMethod(methodId);
    const nextRunId = overrides?.run_id || `${methodId}__run_${Date.now()}_${methodRunCountById(methodRunSpecs, methodId) + 1}`;
    setEditorTarget({ methodId, runId: nextRunId });
    setMethodEditorOpen(true);
    if (methodRunCountById(methodRunSpecs, methodId) >= MAX_SELECTED_METHOD_RUNS) {
      setError(`当前已达到此方法的 ${MAX_SELECTED_METHOD_RUNS} 个运行实例上限。请移除一个已选实例后再追加。`);
      return;
    }
    if (methodRunSpecs.length >= MAX_SELECTED_METHOD_RUNS) {
        setError(`当前已达到 ${MAX_SELECTED_METHOD_RUNS} 个子项上限。请移除一个已选子项后再追加。`);
      return;
    }
    setMethodRunSpecs((current) => {
      if (current.length >= MAX_SELECTED_METHOD_RUNS) {
      setError(`当前已达到 ${MAX_SELECTED_METHOD_RUNS} 个子项上限。请移除一个已选子项后再追加。`);
        return current.slice(0, MAX_SELECTED_METHOD_RUNS);
      }
      setError(null);
      const sameMethodCount = current.filter((spec) => spec.method_id === methodId).length;
      const nextRun = newMethodRunSpec(methodId, sameMethodCount, {
        ...overrides,
        run_id: nextRunId,
      });
      setActiveMethodRunIds((active) => ({
        ...active,
        [methodId]: nextRun.run_id,
      }));
      return [...current, nextRun].slice(0, MAX_SELECTED_METHOD_RUNS);
    });
    setSelectedMethodIds((current) => {
      const next = new Set(current);
      next.add(methodId);
      return new Set(clampMethodIds([...next]));
    });
  }

  function replaceMethodRuns(methodId: string, nextRuns: MethodRunSpec[]) {
    setMethodRunSpecs((current) => {
      const preserved = current.filter((spec) => spec.method_id !== methodId);
      return [...preserved, ...nextRuns].slice(0, MAX_SELECTED_METHOD_RUNS);
    });
  }

  function updateRunGroup(run: MethodRunSpec | null | undefined, patch: MethodRunSpecPatch) {
    if (!run?.bundle_run_id) {
      updateMethodRunSpec(run?.method_id || "", run?.run_id || "", patch);
      return;
    }
    setMethodRunSpecs((current) =>
      current
        .map((spec) => {
          if (spec.bundle_run_id !== run.bundle_run_id) return spec;
          const nextFieldBindings =
            patch.field_bindings === null
              ? spec.field_bindings
              : patch.field_bindings
                ? cleanMethodFieldBinding(patch.field_bindings)
                : spec.field_bindings;
          const nextObjectSelection =
            patch.object_selection === null
              ? undefined
              : patch.object_selection
                ? { ...patch.object_selection }
                : spec.object_selection;
          return {
            ...spec,
            ...patch,
            method_id: spec.method_id,
            run_id: spec.run_id,
            label: spec.label,
            bundle_run_id: spec.bundle_run_id,
            bundle_title: spec.bundle_title,
            field_bindings: nextFieldBindings,
            object_selection: nextObjectSelection,
            smart_merge_group:
              patch.smart_merge_group === null
                ? ""
                : patch.smart_merge_group !== undefined
                  ? patch.smart_merge_group
                  : spec.smart_merge_group,
            statistical_options:
              patch.statistical_options === null
                ? undefined
                : patch.statistical_options !== undefined
                  ? patch.statistical_options
                  : spec.statistical_options,
          } satisfies MethodRunSpec;
        })
        .slice(0, MAX_SELECTED_METHOD_RUNS),
    );
  }

  function removeMethodRun(runId: string) {
    setMethodRunSpecs((current) => {
      const removed = current.find((spec) => spec.run_id === runId);
      const nextRuns = current.filter((spec) => spec.run_id !== runId).slice(0, MAX_SELECTED_METHOD_RUNS);
      if (removed) {
        setSelectedMethodIds(new Set(clampMethodIds(methodIdsFromRunSpecs(nextRuns))));
        setActiveMethodRunIds((active) => {
          const nextActive = { ...active };
          const fallback = nextRuns.find((spec) => spec.method_id === removed.method_id);
          if (fallback) {
            nextActive[removed.method_id] = fallback.run_id;
          } else {
            delete nextActive[removed.method_id];
          }
          return nextActive;
        });
        if (selectedMethodId === removed.method_id && !nextRuns.some((spec) => spec.method_id === removed.method_id)) {
          const nextFocus = nextRuns[0];
          setSelectedMethodId(nextFocus?.method_id || "");
          setEditorTarget(nextFocus ? { methodId: nextFocus.method_id, runId: nextFocus.run_id } : null);
        }
      }
      return nextRuns;
    });
  }

  function removeMethodRunGroup(groupId: string) {
    setMethodRunSpecs((current) => {
      const nextRuns = current.filter((spec) => (spec.bundle_run_id || `single:${spec.run_id}`) !== groupId).slice(0, MAX_SELECTED_METHOD_RUNS);
      setSelectedMethodIds(new Set(clampMethodIds(methodIdsFromRunSpecs(nextRuns))));
      setActiveMethodRunIds((active) => {
        const nextActive: Record<string, string> = {};
        for (const spec of nextRuns) {
          if (!nextActive[spec.method_id]) nextActive[spec.method_id] = active[spec.method_id] || spec.run_id;
        }
        return nextActive;
      });
      const nextFocus = nextRuns[0];
      setSelectedMethodId(nextFocus?.method_id || "");
      setEditorTarget(nextFocus ? { methodId: nextFocus.method_id, runId: nextFocus.run_id } : null);
      return nextRuns;
    });
  }

  function syncMethodRunBinding(methodId: string, patch: Partial<MethodFieldBinding>) {
    setMethodFieldBindings((current) => ({
      ...current,
      [methodId]: {
        ...(current[methodId] || {}),
        ...patch,
      },
    }));
  }

  function updateMethodRunSpec(methodId: string, runId: string, patch: MethodRunSpecPatch) {
    setMethodRunSpecs((current) =>
      current.map((spec) => {
        if (spec.method_id !== methodId || spec.run_id !== runId) {
          return spec;
        }
        const nextFieldBindings =
          patch.field_bindings === null
            ? spec.field_bindings
            : patch.field_bindings
              ? cleanMethodFieldBinding(patch.field_bindings)
              : spec.field_bindings;
        const nextObjectSelection =
          patch.object_selection === null
            ? undefined
            : patch.object_selection
              ? { ...patch.object_selection }
              : spec.object_selection;
        const nextStatisticalOptions =
          patch.statistical_options === null
            ? undefined
            : patch.statistical_options
              ? cleanMethodStatisticalOptions({ ...(spec.statistical_options || {}), ...patch.statistical_options })
              : spec.statistical_options;
        return {
          ...spec,
          ...patch,
          field_bindings: nextFieldBindings,
          object_selection: nextObjectSelection,
          statistical_options: nextStatisticalOptions,
          smart_merge_group:
            patch.smart_merge_group === null
              ? ""
              : patch.smart_merge_group !== undefined
                ? patch.smart_merge_group
                : spec.smart_merge_group,
        };
      }).slice(0, MAX_SELECTED_METHOD_RUNS),
    );
  }

  function toggleMethod(methodId: string) {
    const currentlySelected = selectedMethodIdSet.has(methodId);
    setSelectedMethodIds((current) => {
      const next = new Set(current);
      if (currentlySelected) {
        next.delete(methodId);
        setMethodRunSpecs((runs) => runs.filter((spec) => spec.method_id !== methodId));
        setActiveMethodRunIds((active) => {
          const nextActive = { ...active };
          delete nextActive[methodId];
          return nextActive;
        });
      } else {
        if (methodRunSpecs.length >= MAX_SELECTED_METHOD_RUNS || selectedMethodIdSet.size >= MAX_SELECTED_METHOD_RUNS) {
          setError(`当前已达到 ${MAX_SELECTED_METHOD_RUNS} 个方法上限。请移除一个已选方法后再加入新的方法。`);
          setSelectedMethodId(methodId);
          return next;
        }
        setError(null);
        next.add(methodId);
        setMethodRunSpecs((runs) => {
          if (runs.some((spec) => spec.method_id === methodId)) return runs;
          const nextRun = newMethodRunSpec(methodId, 0);
          setActiveMethodRunIds((active) => ({
            ...active,
            [methodId]: nextRun.run_id,
          }));
          return [...runs, nextRun].slice(0, MAX_SELECTED_METHOD_RUNS);
        });
        const activeRunId = activeMethodRunIds[methodId];
        const existingRun = activeRunId
          ? methodRunSpecs.find((spec) => spec.method_id === methodId && spec.run_id === activeRunId)
          : methodRunSpecs.find((spec) => spec.method_id === methodId);
        if (existingRun) {
          setActiveMethodRunIds((active) => ({
            ...active,
            [methodId]: existingRun.run_id,
          }));
        }
      }
      return next;
    });
    setSelectedMethodId(methodId);
    setMethodEditorOpen(true);
  }

  function selectFilteredMethods() {
    let workingRuns = [...methodRunSpecs];
    const appendedRuns: MethodRunSpec[] = [];
    for (const bundle of visibleMethodBundles) {
      const { runs, requiredSlots } = buildBundleRunGroupSpecs(bundle, workingRuns, selectedDataset);
      if (!runs.length) continue;
      if (MAX_SELECTED_METHOD_RUNS - workingRuns.length < requiredSlots) break;
      workingRuns = [...workingRuns, ...runs].slice(0, MAX_SELECTED_METHOD_RUNS);
      appendedRuns.push(...runs);
    }
    if (!appendedRuns.length) {
      setError(`当前已达到 ${MAX_SELECTED_METHOD_RUNS} 个子项上限。请移除已选子方法后再添加。`);
      return;
    }
    setError(null);
    setMethodRunSpecs(workingRuns);
    setSelectedMethodIds(new Set(clampMethodIds(methodIdsFromRunSpecs(workingRuns))));
    const focusRun = appendedRuns[0];
    setSelectedMethodId(focusRun.method_id);
    setActiveMethodRunIds((active) => ({
      ...active,
      ...Object.fromEntries(appendedRuns.map((run) => [run.method_id, run.run_id])),
    }));
    setEditorTarget({ methodId: focusRun.method_id, runId: focusRun.run_id });
    setMethodEditorOpen(true);
  }

  function clearFilteredMethods() {
    const visibleMethodIds = new Set(visibleMethodBundles.flatMap((bundle) => bundle.methods.map((method) => method.id)));
    const nextRuns = methodRunSpecs.filter((spec) => !visibleMethodIds.has(spec.method_id));
    setMethodRunSpecs(nextRuns);
    setSelectedMethodIds(new Set(clampMethodIds(methodIdsFromRunSpecs(nextRuns))));
    const nextFocus = nextRuns[0];
    setSelectedMethodId(nextFocus?.method_id || "");
    setEditorTarget(nextFocus ? { methodId: nextFocus.method_id, runId: nextFocus.run_id } : null);
    setActiveMethodRunIds(Object.fromEntries(nextRuns.map((run) => [run.method_id, run.run_id])));
  }

  function loadMoreMethods() {
    setVisibleMethodLimit((current) => Math.min(current + METHOD_LOAD_MORE_STEP, filteredMethods.length));
  }

  function handleDatasetChange(datasetId: string) {
    const nextDataset = datasets.find((dataset) => dataset.dataset_id === datasetId);
    setSelectedDatasetId(datasetId);
    setSelectedSheet(datasetSheetName(nextDataset));
    setMethodFieldBindings({});
    if (nextDataset && shouldAutoPreprocessDataset(nextDataset)) {
      void runDatasetPreprocessing(nextDataset).catch((preprocessError) => {
        setError(preprocessError instanceof Error ? preprocessError.message : "数据集预处理失败。");
        setStatus("数据集切换后预处理失败。");
      });
    } else if (nextDataset) {
      setStatus(largeDatasetReadyStatus(nextDataset));
    }
  }

  function selectAllReportParts() {
    setSelectedReportPartIds(new Set(availableReportParts));
  }

  function toggleReportPart(reportPartId: string) {
    setSelectedReportPartIds((current) => {
      const next = new Set(current);
      if (next.has(reportPartId)) {
        next.delete(reportPartId);
        return next.size ? next : new Set(availableReportParts);
      }
      next.add(reportPartId);
      return next;
    });
  }

  return (
    <section className="lab-workbench relative min-h-dvh overflow-hidden bg-[#050806] text-white xl:h-full">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_11%_7%,rgba(255,156,97,0.20),transparent_22%),radial-gradient(circle_at_83%_10%,rgba(116,208,217,0.18),transparent_26%),linear-gradient(135deg,rgba(255,255,255,0.055),transparent_38%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-30 lab-grid-field" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[linear-gradient(180deg,rgba(255,255,255,0.08),transparent)]" />

      <div className="relative flex h-full flex-col gap-3 p-3 sm:p-4">
        <header className="lab-topbar flex flex-wrap items-center justify-between gap-4 rounded-[28px] border border-white/10 bg-black/30 px-4 py-3 shadow-2xl backdrop-blur-2xl">
          <div className="flex min-w-[280px] flex-1 items-center gap-3">
            <Link
              className="lab-icon-button"
              href="/"
              aria-label="返回首页"
            >
              <ArrowLeft size={18} />
            </Link>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] uppercase tracking-[0.28em] text-[var(--muted)]">Asteria Lab / MethodOps Command Center</p>
              <h1 className="text-balance break-words text-2xl font-semibold leading-tight tracking-[-0.04em] text-[var(--text-strong)] sm:text-3xl">
                企业级数据分析方法工作台
              </h1>
              <p className="mt-1 max-w-3xl text-xs leading-5 text-[var(--muted)]">
                非金融统计可视化、字段绑定、CLI 解读和报告交付在同一张运行指挥台里闭环。
              </p>
            </div>
          </div>

          <div className="flex min-w-[280px] flex-wrap items-center justify-end gap-2">
            <span
              className={`lab-sla-pill ${catalogLoaded && methodQuality.visualSlaMet && methodQuality.financeExcluded ? "lab-sla-pill-ok" : ""}`}
              title="默认 Lab catalog 必须满足至少 500 张非金融统计/数据分析可视化方法卡，且不暴露金融交易/投机方法卡。"
            >
              <Workflow size={14} />
              {catalogLoaded
                ? `${formatNumber(methodQuality.nonFinancialVisual)} non-financial visuals`
                : "加载方法目录..."}
            </span>
            <span className="lab-sla-pill">
              <CheckCircle2 size={14} />
              {catalogLoaded ? `${methodQuality.readyPercent}% runnable now` : "可用性检测中"}
            </span>
            <Link
              className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-[var(--text-strong)] transition hover:bg-white/10"
              href="/analysis"
            >
              正式分析
            </Link>
            <a
              className="rounded-full border border-[#74d0d9]/24 bg-[#74d0d9]/10 px-4 py-2 text-sm text-[var(--text-strong)] transition hover:bg-[#74d0d9]/16"
              href="#lab-method-workspace"
            >
              方法工作台
            </a>
            <button
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-[var(--text-strong)] transition hover:bg-white/10"
              onClick={() => setCanvasExpanded((value) => !value)}
              title={canvasExpanded ? "显示左侧控制区" : "隐藏左侧控制区，专注查看画布"}
              type="button"
            >
              {canvasExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
              {canvasExpanded ? "显示控制区" : "隐藏控制区"}
            </button>
          </div>
        </header>

        <LabStatusRail
          dataset={selectedDataset}
          methodCount={methods.length}
          methodQuality={methodQuality}
          mode={mode}
          selectedRunCount={selectedRunCount}
          selectedSheetName={selectedSheetName}
          visualMethodCount={visualMethodCount}
        />

        <div
          className={`grid min-h-0 flex-1 grid-cols-1 transition-[grid-template-columns] duration-300 xl:grid-cols-[400px_minmax(0,1fr)] ${
            canvasExpanded ? "gap-0 xl:grid-cols-[0px_minmax(0,1fr)]" : "gap-4"
          }`}
        >
          <aside
            className={`min-h-0 overflow-hidden transition-opacity duration-300 ${
              canvasExpanded ? "pointer-events-none opacity-0" : "opacity-100"
            }`}
          >
            <div className="flex h-full min-h-0 flex-col gap-4 overflow-y-auto rounded-[32px] border border-white/10 bg-[#0d1213]/88 p-4 shadow-2xl backdrop-blur-2xl">
              <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
                <div className="mb-4 flex items-start gap-3">
                  <div className="rounded-2xl border border-white/10 bg-[#ff9c61]/15 p-3 text-[#ffd28f]">
                    <FileUp size={20} />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Lab 数据入口</p>
                    <h2 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">上传数据或选择已有数据</h2>
                  </div>
                </div>

                <label className="relative flex min-h-[180px] cursor-pointer flex-col justify-between overflow-hidden rounded-[26px] border border-dashed border-white/16 bg-black/25 p-5 transition hover:border-[#ff9c61]/60 hover:bg-[#ff9c61]/8">
                  <input
                    accept=".xlsx,.xls,.csv,.tsv,.dta"
                    className="hidden"
                    onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                    type="file"
                  />
                  <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white/8 text-[#ffd28f]">
                    <FileUp size={22} />
                  </span>
                  <span>
                    <span className="block text-lg font-semibold text-[var(--text-strong)]">
                      {selectedFile?.name || "选择待分析的数据文件"}
                    </span>
                    <span className="mt-2 block text-sm leading-6 text-[var(--muted)]">
                      CSV, TSV, DTA, XLS, and XLSX files can drive every method below.
                    </span>
                  </span>
                </label>

                <button
                  className="primary-button mt-4 w-full"
                  disabled={isBusy || !selectedFile}
                  onClick={handleUpload}
                  title={uploadBlockReason || undefined}
                  type="button"
                >
                  {isUploading && selectedFile ? <LoaderCircle className="mr-2 animate-spin" size={16} /> : null}
                  上传数据
                </button>
                {uploadBlockReason ? (
                  <BlockedReasonPanel action={uploadBlockAction} reason={uploadBlockReason} />
                ) : null}
                <WorkflowProgressCard progress={workflowProgress} />
              </section>

              <ExternalSkillMountPanel
                busy={externalSkillBusy}
                error={externalSkillError}
                mountedSkillIds={mountedExternalSkillIds}
                onDeleteSkill={deleteExternalSkill}
                onImportLocal={importLocalExternalSkill}
                onInstall={installExternalSkills}
                onRefresh={refreshExternalSkills}
                onRunFeatureTrial={runFeatureTrial}
                onSetMounted={setExternalSkillMounted}
                onToggleReportFeature={toggleExternalSkillFeatureSelection}
                reportFeatureSelections={cleanExternalSkillFeatureSelectionList}
                localPath={externalSkillLocalPath}
                setLocalPath={setExternalSkillLocalPath}
                setSourceUrl={setExternalSkillSourceUrl}
                skills={externalSkills}
                sourceUrl={externalSkillSourceUrl}
                status={externalSkillStatus}
                trialBusyId={featureTrialBusyId}
                trialResult={featureTrialResult}
              />

              <ReportAgentTeamPanel
                busy={reportAgentTeamBusy}
                error={reportAgentTeamError}
                localPath={reportAgentTeamLocalPath}
                mountedTeamIds={mountedReportAgentTeamIds}
                onDeleteTeam={deleteReportAgentTeam}
                onImportLocal={importLocalReportAgentTeam}
                onRefresh={refreshReportAgentTeams}
                onRunTeam={runReportAgentTeam}
                onSetMounted={setReportAgentTeamMounted}
                runTask={reportAgentTeamTask}
                setLocalPath={setReportAgentTeamLocalPath}
                status={reportAgentTeamStatus}
                teams={reportAgentTeams}
              />

              <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">数据集</p>
                    <h2 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">当前工作区</h2>
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-[var(--muted)]">
                    {datasets.length} saved
                  </span>
                </div>

                <div className="space-y-3">
                  <label className="block space-y-2">
                    <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">数据集</span>
                    <DatasetPicker
                      datasets={datasets}
                      onChange={handleDatasetChange}
                      selectedDataset={selectedDataset}
                      value={selectedDatasetId}
                    />
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">工作表</span>
                    <ThemedSelect
                      className="field-input"
                      onChange={(event) => setSelectedSheet(event.target.value)}
                      value={selectedSheetName}
                    >
                      {(selectedDataset?.sheets || []).map((sheet) => (
                        <option key={sheet.name} value={sheet.name}>
                          {sheet.name}
                        </option>
                      ))}
                      {!selectedDataset?.sheets?.length ? <option value="">Default sheet</option> : null}
                    </ThemedSelect>
                  </label>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  {datasets.length ? (
                    <>
                      <MetricCard label="Rows" value={formatNumber(selectedDataset?.row_count)} />
                      <MetricCard label="Columns" value={formatNumber(selectedDataset?.column_count)} />
                      <MetricCard label="Numeric" value={formatNumber(selectedDataset?.numeric_columns?.length)} />
                      <MetricCard label="Category" value={formatNumber(selectedDataset?.categorical_columns?.length)} />
                    </>
                  ) : (
                    <>
                      <LoadingMetricCard label="Rows" />
                      <LoadingMetricCard label="Columns" />
                      <LoadingMetricCard label="Numeric" />
                      <LoadingMetricCard label="Category" />
                    </>
                  )}
                </div>
              </section>

              <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Lab 执行模式</p>
                <div className="mt-3 grid gap-2">
                  <button
                    className={`rounded-[20px] border p-3 text-left transition ${
                      mode === "auto"
                        ? "border-[#ff9c61]/50 bg-[#ff9c61]/12 text-[var(--text-strong)]"
                        : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                    }`}
                    onClick={() => setMode("auto")}
                    type="button"
                  >
                    <span className="block text-sm font-semibold">总合并已选方法</span>
                    <span className="mt-1 block text-xs leading-5 opacity-80">先清洗、派生，再生成各自 method-card 产物并做智能合并。</span>
                  </button>
                  <button
                    className={`rounded-[20px] border p-3 text-left transition ${
                      mode === "method"
                        ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                        : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                    }`}
                    onClick={() => setMode("method")}
                    type="button"
                  >
                    <span className="block text-sm font-semibold">单方法独立执行</span>
                    <span className="mt-1 block text-xs leading-5 opacity-80">选一个方法，也先清洗和派生，再独立执行并保留单项结果。</span>
                  </button>
                  <button
                    className={`rounded-[20px] border p-3 text-left transition ${
                      mode === "batch"
                        ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                        : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                    }`}
                    onClick={() => setMode("batch")}
                    type="button"
                  >
                    <span className="block text-sm font-semibold">批量独立执行</span>
                    <span className="mt-1 block text-xs leading-5 opacity-80">对勾选方法先统一清洗和派生，再分别生成结果，并保留合并解读。</span>
                  </button>
                  <button
                    className={`rounded-[20px] border p-3 text-left transition ${
                      mode === "smart_report"
                        ? "border-[#9c6bff]/55 bg-[#9c6bff]/12 text-[var(--text-strong)]"
                        : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                    }`}
                    onClick={() => setMode("smart_report")}
                    type="button"
                  >
                    <span className="block text-sm font-semibold">正式报告试跑</span>
                    <span className="mt-1 block text-xs leading-5 opacity-80">仍可从 Lab 跳到正式报告生成链路做对照。</span>
                  </button>
                </div>
              </section>

              <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">已选方法</p>
                <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                  {selectedMethodNames(methods, selectedMethodIdSet, selectedRunSpecs)}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedRunSpecs.length
                    ? selectedRunSpecs.slice(0, 24).map((run) => {
                        const method = methodsById.get(run.method_id);
                        const active = selectedMethodId === run.method_id && activeMethodRunIds[run.method_id] === run.run_id;
                        return (
                          <button
                            className={`rounded-full border px-3 py-2 text-xs transition ${
                              active
                                ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                                : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                            }`}
                            key={run.run_id}
                            onClick={() => {
                              selectMethod(run.method_id);
                              setActiveMethodRunIds((current) => ({ ...current, [run.method_id]: run.run_id }));
                              setMethodEditorOpen(true);
                            }}
                            type="button"
                          >
                            {run.label || (method ? methodSubmethodTitle(method) : run.method_id)} · CLI解读
                          </button>
                        );
                      })
                    : selectedMethodBundles.slice(0, 10).map((bundle, index) => {
                        const active = bundle.methods.some((method) => method.id === selectedMethodId);
                        const count = bundleRunCount(bundle, methodRunSpecs, selectedMethodIds);
                        const copy = methodBundleDisplayCopy(bundle);
                        return (
                          <button
                            className={`rounded-full border px-3 py-2 text-xs transition ${
                              active
                                ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                                : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                            }`}
                            key={bundleRenderKey(bundle, "selected-summary", index)}
                            onClick={() => selectMethod(bundle.representative.id)}
                            title={copy.cliLine}
                            type="button"
                          >
                            {count > 1 ? `${bundle.title} · ${count} 项` : bundle.title} · CLI解读
                          </button>
                        );
                      })}
                  {selectedRunSpecs.length > 24 ? (
                    <span className="rounded-full border border-white/10 bg-black/18 px-3 py-2 text-xs text-[var(--muted)]">
                      还有 {formatNumber(selectedRunSpecs.length - 24)} 个实例
                    </span>
                  ) : null}
                </div>
              </section>

              <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Report Parts</p>
                    <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                      {`${formatNumber(selectedReportParts.length)} / ${formatNumber(availableReportParts.length)} selected · ${reportPartSummary(selectedReportParts)}`}
                    </p>
                  </div>
                  <button className="surface-chip" onClick={selectAllReportParts} type="button">
                    All
                  </button>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {availableReportParts.map((reportPartId) => {
                    const active = selectedReportPartIds.has(reportPartId);
                    return (
                      <button
                        aria-pressed={active}
                        className={`rounded-full border px-3 py-2 text-xs transition ${
                          active
                            ? "border-[#9c6bff]/55 bg-[#9c6bff]/14 text-[var(--text-strong)]"
                            : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                        }`}
                        key={reportPartId}
                        onClick={() => toggleReportPart(reportPartId)}
                        type="button"
                      >
                        {reportPartLabel(reportPartId)}
                      </button>
                    );
                  })}
                </div>
              </section>

              {mode === "method" && currentMethod ? (
                <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">当前单方法</p>
                  <h3 className="mt-2 text-base font-semibold text-[var(--text-strong)]">
                    {methodDisplayTitle(currentMethod)}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{methodGoalText(currentMethod)}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {methodOutputLabels(currentMethod).map((label) => (
                      <span className="surface-chip" key={label}>{label}</span>
                    ))}
                    {methodRoleLabels(currentMethod).slice(0, 3).map((label) => (
                      <span className="surface-chip" key={label}>{label}</span>
                    ))}
                  </div>
                </section>
              ) : null}

              <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">执行说明</p>
                <textarea
                  className="field-input mt-3 min-h-[132px] resize-y"
                  onChange={(event) => setWorkspaceBrief(event.target.value)}
                  placeholder="告诉系统这次执行想回答什么业务问题。"
                  value={workspaceBrief}
                />
                {error ? (
                  <div className="mt-3 rounded-[18px] border border-red-300/20 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
                    {error}
                  </div>
                ) : null}
                <RunGuidanceCard
                  analysisBlockAction={analysisBlockAction}
                  analysisBlockReason={analysisBlockReason}
                  currentMethodName={currentMethod ? methodDisplayTitle(currentMethod) : ""}
                  isBusy={isBusy}
                  mode={mode}
                  selectedDataset={selectedDataset}
                  selectedRunCount={selectedRunCount}
                  selectedSheetName={selectedSheetName}
                  status={status}
                />
                <button
                  className="primary-button mt-4 w-full"
                  disabled={Boolean(analysisBlockReason)}
                  onClick={() => {
                    if (mode === "smart_report") {
                      void runSmartReport();
                      return;
                    }
                    if (mode === "batch") {
                      void runSelectedMethods();
                      return;
                    }
                    if (mode === "auto") {
                      void runAutoAnalysis();
                      return;
                    }
                    if (currentMethod) {
                      void runSingleMethod(currentMethod);
                    }
                  }}
                  title={analysisBlockReason || undefined}
                  type="button"
                >
                  {isBusy ? <LoaderCircle className="mr-2 animate-spin" size={16} /> : <Sparkles className="mr-2" size={16} />}
                  {mode === "batch" ? "批量执行已选方法" : mode === "auto" ? "合并运行已选方法" : "执行当前路径"}
                </button>
                {analysisBlockReason ? (
                  <BlockedReasonPanel action={analysisBlockAction} reason={analysisBlockReason} />
                ) : null}
                {mode === "method" && currentMethod ? (
                  <button
                    className="surface-chip mt-3 w-full justify-center"
                    disabled={isBusy}
                    onClick={() => void runSingleMethod(currentMethod)}
                    type="button"
                  >
                    单独执行：{methodDisplayTitle(currentMethod)}
                  </button>
                ) : null}
                <p className="mt-3 text-xs leading-5 text-[var(--muted)]">{status}</p>
              </section>
            </div>
          </aside>

          <main className="min-h-0 overflow-hidden rounded-[32px] border border-white/10 bg-[#080d0e]/92 shadow-2xl backdrop-blur-2xl">
            <div className="flex h-full min-h-0 flex-col">
              <div className="min-h-0 flex-1 overflow-auto">
                <div className={`mx-auto grid w-full max-w-[1800px] gap-5 p-5 ${canvasExpanded ? "min-h-[2200px]" : "min-h-[1600px]"}`}>
                  <LabFieldWorkflowPanel
                    dataset={selectedDataset}
                    derivedMetricEdits={derivedMetricEdits}
                    fieldSelection={fieldSelection}
                    onAddDerivedMetric={() => {
                      const numeric = selectedDataset?.numeric_columns || [];
                      setDerivedMetricEdits((current) => [
                        ...current,
                        {
                          field: `自定义指标_${current.length + 1}`,
                          display_name: `自定义指标${current.length + 1}`,
                          formula: numeric[0] ? `${numeric[0]} (直接取值)` : "请填写计算方式",
                          source_fields: numeric[0] ? [numeric[0]] : [],
                          recipe_id: "custom",
                          selected: true,
                          custom: true,
                        },
                      ]);
                    }}
                    onReset={() => {
                      setFieldSelection(inferDefaultFieldSelection(selectedDataset));
                      setDerivedMetricEdits(defaultDerivedMetricDrafts(selectedDataset));
                      setMethodFieldBindings({});
                    }}
                    setDerivedMetricEdits={setDerivedMetricEdits}
                    setFieldSelection={setFieldSelection}
                  />
                  <MethodWorkspacePanel
                    catalogLoaded={catalogLoaded}
                    clearFilteredMethods={clearFilteredMethods}
                    dataset={selectedDataset}
                    derivedMetricEdits={derivedMetricEdits}
                    fieldSelection={fieldSelection}
                    filteredMethodBundles={filteredMethodBundles}
                    filteredMethods={filteredMethods}
                    groupedMethodCounts={groupedMethodCounts}
                    groupedView={groupedView}
                    activeMethodFamily={activeMethodFamily}
                    activeMethodSource={activeMethodSource}
                    methodFilter={methodFilter}
                    methodFieldBindings={methodFieldBindings}
                    methodSearch={methodSearch}
                    methods={methods}
                    setMethodFieldBindings={setMethodFieldBindings}
                    setActiveMethodFamily={setActiveMethodFamily}
                    setActiveMethodSource={setActiveMethodSource}
                    recommendedMethodSlice={recommendedMethodSlice}
                    replaceSelectedMethods={replaceSelectedMethods}
                    addMethodBundleRunGroup={addMethodBundleRunGroup}
                    addMethodBundleRunGroups={addMethodBundleRunGroups}
                    appendMethodRun={appendMethodRun}
                    removeMethodRunGroup={removeMethodRunGroup}
                    methodCardSaveBusyId={methodCardSaveBusyId}
                    methodSourceCounts={methodSourceCounts}
                    replaceMethodRuns={replaceMethodRuns}
                    removeMethodRun={removeMethodRun}
                    updateMethodRunSpec={updateMethodRunSpec}
                    updateRunGroup={updateRunGroup}
                    runSingleMethod={(method) => runSingleMethod(method)}
                    saveCurrentMethodCard={saveCurrentMethodCard}
                    selectFilteredMethods={selectFilteredMethods}
                    selectMethod={selectMethod}
                    selectedMethodId={selectedMethodId}
                    selectedMethodBundles={selectedMethodBundles}
                    selectedMethodIds={selectedMethodIdSet}
                    selectedRunCount={selectedRunCount}
                    selectedRunSpecs={selectedRunSpecs}
                    methodRunSpecs={cappedMethodRunSpecs}
                    activeMethodRunIds={activeMethodRunIds}
                    activeSelectedMethod={activeSelectedMethod}
                    activeEditorMethod={activeEditorMethod}
                    selectedMethods={selectedMethods}
                    syncMethodRunBinding={syncMethodRunBinding}
                    setActiveMethodRunIds={setActiveMethodRunIds}
                    setEditorTarget={setEditorTarget}
                    setGroupedView={setGroupedView}
                    setMethodFilter={setMethodFilter}
                    setMethodSearch={setMethodSearch}
                    toggleMethod={toggleMethod}
                    hiddenMethodCount={hiddenMethodCount}
                    loadMoreMethods={loadMoreMethods}
                    visibleBundleCount={visibleBundleCount}
                    visibleGroupedMethods={visibleGroupedMethods}
                    visibleMethodCount={visibleMethodCount}
                    visibleMethods={visibleMethods}
                    visualMethodCount={visualMethodCount}
                    methodQuality={methodQuality}
                    methodEditorOpen={methodEditorOpen}
                    setMethodEditorOpen={setMethodEditorOpen}
                  />
                  <ResultCanvas
                    addMethodBundleRunGroup={addMethodBundleRunGroup}
                    appendMethodRun={appendMethodRun}
                    autoSummary={autoSummary}
                    canvasExpanded={canvasExpanded}
                    dataset={selectedDataset}
                    isBusy={isBusy}
                    methodCatalogSummary={catalogSummary}
                    methodRuns={methodRuns}
                    methods={methods}
                    onRerunBlueprintPart={rerunBlueprintPart}
                    onOpenMethodEditor={(methodId, runId) => {
                      const existingRun = runId
                        ? cappedMethodRunSpecs.find((spec) => spec.method_id === methodId && spec.run_id === runId)
                        : cappedMethodRunSpecs.find((spec) => spec.method_id === methodId);
                      setSelectedMethodId(methodId);
                      setEditorTarget(existingRun ? { methodId, runId: existingRun.run_id } : { methodId });
                      setMethodEditorOpen(true);
                    }}
                    partRunBusy={partRunBusy}
                    result={result}
                    selectedMethodIds={selectedMethodIdSet}
                    selectedRunSpecs={selectedRunSpecs}
                    selectMethod={selectMethod}
                    selectedSheetName={selectedSheetName}
                  />
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </section>
  );
}

function buildBlueprintTaskPayload(blueprint: AutoReportPartGenerationBlueprint) {
  const handoff = blueprint.runtime_handoff || {};
  return {
    report_part_id: blueprint.report_part_id,
    report_part_title: blueprint.report_part_title,
    readiness: blueprint.readiness,
    narrative_seed: blueprint.narrative_seed,
    bullet_seeds: blueprint.bullet_seeds || [],
    table_titles: blueprint.table_titles || [],
    chart_refs: blueprint.chart_refs || [],
    pre_method_preprocessing_status: blueprint.pre_method_preprocessing_status,
    required_asset_kinds: blueprint.required_asset_kinds || [],
    missing_asset_kinds: blueprint.missing_asset_kinds || [],
    input_contract: blueprint.input_contract || {},
    runtime_handoff: handoff,
    method_evidence_count: blueprint.method_evidence_count || 0,
    semantic_route_field_count: blueprint.semantic_route_field_count || 0,
    management_use: blueprint.management_use || "",
  };
}

function blueprintMethodIds(blueprint: AutoReportPartGenerationBlueprint) {
  const ids = (blueprint.method_evidence || [])
    .map((item) => String(item.method_id || "").trim())
    .filter(Boolean);
  return [...new Set(ids)];
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-white/10 bg-black/20 p-3">
      <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-[var(--text-strong)]">{value}</p>
    </div>
  );
}

function LoadingMetricCard({ label }: { label: string }) {
  return (
    <div className="rounded-[18px] border border-white/10 bg-black/20 p-3">
      <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-[var(--muted)]">...</p>
    </div>
  );
}

function ExternalSkillMountPanel({
  busy,
  error,
  localPath,
  mountedSkillIds,
  onDeleteSkill,
  onImportLocal,
  onInstall,
  onRefresh,
  onRunFeatureTrial,
  onSetMounted,
  onToggleReportFeature,
  reportFeatureSelections,
  setLocalPath,
  setSourceUrl,
  skills,
  sourceUrl,
  status,
  trialBusyId,
  trialResult,
}: {
  busy: boolean;
  error: string | null;
  localPath: string;
  mountedSkillIds: string[];
  onDeleteSkill: (skillId: string) => Promise<void>;
  onImportLocal: () => Promise<void>;
  onInstall: () => Promise<void>;
  onRefresh: () => Promise<void>;
  onRunFeatureTrial: (skill: ExternalSkillItem, featureKind: "command" | "embedded_skill", featureId: string) => Promise<void>;
  onSetMounted: (skillId: string, mounted: boolean) => Promise<void>;
  onToggleReportFeature: (selection: ExternalSkillFeatureSelection) => void;
  reportFeatureSelections: ExternalSkillFeatureSelection[];
  setLocalPath: Dispatch<SetStateAction<string>>;
  setSourceUrl: Dispatch<SetStateAction<string>>;
  skills: ExternalSkillItem[];
  sourceUrl: string;
  status: string;
  trialBusyId: string | null;
  trialResult: LabFeatureTrialResult | null;
}) {
  const reportFeatureSelectionKeys = new Set(reportFeatureSelections.map((selection) => externalSkillFeatureSelectionKey(selection)));
  const [libraryExpanded, setLibraryExpanded] = useState(false);
  const mountedSkills = skills.filter((skill) => skill.mounted);
  const collapsedSkills = (mountedSkills.length ? mountedSkills : skills).slice(0, 3);
  const visibleSkills = libraryExpanded ? skills : collapsedSkills;
  const hiddenSkillCount = Math.max(skills.length - visibleSkills.length, 0);
  return (
    <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1 basis-[240px]">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">External Skills</p>
          <h2 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">挂载到 Lab 的外部 skill</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
            下载、装配、挂载、取消挂载和删除都会同步到 run payload，运行时会读取对应的 SKILL.md。
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-[var(--muted)]">
          {formatNumber(skills.length)} installed
        </span>
      </div>
      <p className="mb-4 rounded-[18px] border border-[#8fdcc2]/20 bg-[#8fdcc2]/10 px-3 py-2 text-xs leading-5 text-[#c7f5df]">
        {formatNumber(reportFeatureSelections.length)} selected feature(s) will shape the next Lab report method rationale,
        evidence interpretation, recommended actions, and review plan.
      </p>
      <div className="mb-4 grid gap-2 sm:grid-cols-3">
        <MetricCard label="Installed" value={formatNumber(skills.length)} />
        <MetricCard label="Mounted" value={formatNumber(mountedSkills.length)} />
        <MetricCard label="Report Features" value={formatNumber(reportFeatureSelections.length)} />
      </div>

      <label className="block space-y-2">
        <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">GitHub repo</span>
        <input
          className="field-input"
          onChange={(event) => setSourceUrl(event.target.value)}
          placeholder={DEFAULT_EXTERNAL_SKILL_SOURCE_URL}
          value={sourceUrl}
        />
      </label>

      <label className="mt-3 block space-y-2">
        <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Local skill path</span>
        <input
          className="field-input"
          onChange={(event) => setLocalPath(event.target.value)}
          placeholder="C:\\path\\to\\my-local-skill"
          value={localPath}
        />
      </label>

      <div className="mt-3 flex flex-wrap gap-2">
        <button className="surface-chip" disabled={busy} onClick={() => void onInstall()} type="button">
          <PackageOpen size={14} className="mr-1" />
          下载并装配
        </button>
        <button className="surface-chip" disabled={busy || !localPath.trim()} onClick={() => void onImportLocal()} type="button">
          <PackageOpen size={14} className="mr-1" />
          导入本地 skill
        </button>
        <button className="surface-chip" disabled={busy} onClick={() => void onRefresh()} type="button">
          刷新
        </button>
        <span className="rounded-full border border-white/10 bg-black/18 px-3 py-2 text-xs text-[var(--muted)]">
          Payload ids: {mountedSkillIds.length}
        </span>
      </div>

      <div className="mt-3 rounded-[18px] border border-white/10 bg-black/18 px-4 py-3 text-xs leading-6 text-[var(--muted)]">
        {status}
      </div>
      {error ? (
        <div className="mt-3 rounded-[18px] border border-red-300/20 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
          {error}
        </div>
      ) : null}
      {trialResult ? (
        <div className="mt-3 rounded-[20px] border border-[#ffd28f]/25 bg-[#ffd28f]/10 px-4 py-3 text-xs leading-6 text-[var(--muted)]">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.22em] text-[#ffd28f]">Feature trial result</p>
              <p className="mt-1 text-sm font-semibold text-[var(--text-strong)]">
                {trialResult.plugin?.name || "Plugin"} / {trialResult.feature?.name || trialResult.feature?.feature_id}
              </p>
            </div>
            <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-[var(--text-strong)]">
              {formatNumber(trialResult.enhancement_effect?.readiness_score || 0)}/100 readiness
            </span>
          </div>
          <p className="mt-2">
            Baseline: {formatNumber(trialResult.baseline_profile?.row_count || 0)} rows,{" "}
            {formatNumber(trialResult.baseline_profile?.column_count || 0)} columns. Enhanced trial ranked fields and produced a single-run Lab payload.
          </p>
          {trialResult.enhancement_effect?.recommended_actions?.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-4">
              {trialResult.enhancement_effect.recommended_actions.slice(0, 3).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2">
            {trialResult.artifacts?.report_url ? (
              <a className="surface-chip" href={trialResult.artifacts.report_url} rel="noreferrer" target="_blank">
                Open report
              </a>
            ) : null}
            {trialResult.artifacts?.csv_url ? (
              <a className="surface-chip" href={trialResult.artifacts.csv_url} rel="noreferrer" target="_blank">
                Field scores CSV
              </a>
            ) : null}
            {trialResult.artifacts?.json_url ? (
              <a className="surface-chip" href={trialResult.artifacts.json_url} rel="noreferrer" target="_blank">
                Trial JSON
              </a>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-[20px] border border-white/10 bg-black/18 p-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">Plugin library</p>
          <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
            默认展示已挂载插件和前 3 个候选插件，保持方法卡主流程清晰。
          </p>
        </div>
        <button className="surface-chip" onClick={() => setLibraryExpanded((value) => !value)} type="button">
          {libraryExpanded ? "收起插件库" : `展开插件库 ${formatNumber(skills.length)}`}
        </button>
      </div>

      <div className="mt-3 grid gap-3">
        {skills.length ? (
          visibleSkills.map((skill) => (
            <article
              className={`max-w-full overflow-hidden rounded-[22px] border p-4 transition ${
                skill.mounted ? "border-[#74d0d9]/55 bg-[#74d0d9]/10" : "border-white/10 bg-black/18"
              }`}
              key={skill.id}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1 basis-[220px]">
                  <h3 className="break-words text-sm font-semibold text-[var(--text-strong)]">{skill.name}</h3>
                  <p className="mt-1 break-words text-xs leading-5 text-[var(--muted)]">
                    {skill.description || skill.source_path || skill.skill_md_path}
                  </p>
                  <p className="mt-2 break-words text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">
                    {skill.source_repo || skill.source_url || "GitHub skill"} · {formatNumber(skill.instruction_chars || 0)} chars
                  </p>
                  {skill.package_kind === "claude_plugin" ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">
                        {formatNumber(skill.skill_count || 0)} embedded skills
                      </span>
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">
                        {formatNumber(skill.command_count || 0)} commands
                      </span>
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">
                        {formatNumber(skill.mcp_server_count || 0)} MCP servers
                      </span>
                      {skill.plugin_version ? (
                        <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">
                          v{skill.plugin_version}
                        </span>
                      ) : null}
                    </div>
                  ) : null}
                  {skill.package_kind === "claude_plugin" && skill.mcp_servers?.length ? (
                    <p className="mt-2 break-words text-[11px] leading-5 text-[var(--muted)]">
                      MCP: {skill.mcp_servers.slice(0, 5).map((server) => server.name).filter(Boolean).join(", ")}
                      {skill.mcp_servers.length > 5 ? "..." : ""}
                    </p>
                  ) : null}
                  {skill.package_kind === "claude_plugin" && skill.commands?.length ? (
                    <p className="mt-2 break-words text-[11px] leading-5 text-[var(--muted)]">
                      Commands: {skill.commands.slice(0, 5).map((command) => command.name).filter(Boolean).join(", ")}
                      {skill.commands.length > 5 ? "..." : ""}
                    </p>
                  ) : null}
                  {skill.package_kind === "claude_plugin" ? (
                    <div className="mt-3 rounded-[16px] border border-white/10 bg-black/15 p-3">
                      <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">
                        Choose features for the main Lab report flow
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {(skill.commands || []).slice(0, 4).map((command) => {
                          const featureId = command.name || "";
                          const trialKey = `${skill.id}:command:${featureId}`;
                          const selection: ExternalSkillFeatureSelection = {
                            plugin_id: skill.id,
                            feature_kind: "command",
                            feature_id: featureId,
                            name: featureId,
                            description: command.description || "",
                            path: command.path || "",
                            selection_source: "analysis_lab_report_flow",
                          };
                          const selectedForReport = reportFeatureSelectionKeys.has(externalSkillFeatureSelectionKey(selection));
                          return featureId ? (
                            <span className="flex min-w-0 flex-wrap items-center gap-1" key={trialKey}>
                              <button
                                className={`surface-chip max-w-full whitespace-normal break-words ${selectedForReport ? "border-[#8fdcc2]/50 bg-[#8fdcc2]/15 text-[#d8ffee]" : ""}`}
                                disabled={busy || !skill.mounted}
                                onClick={() => onToggleReportFeature(selection)}
                                title={command.description || undefined}
                                type="button"
                              >
                                {selectedForReport ? "Used in report" : "Use in report"}: {featureId}
                              </button>
                              <button
                                className="surface-chip opacity-80"
                                disabled={busy || trialBusyId === trialKey}
                                onClick={() => void onRunFeatureTrial(skill, "command", featureId)}
                                title="Run a one-off feature trial for this dataset."
                                type="button"
                              >
                                {trialBusyId === trialKey ? <LoaderCircle className="mr-1 animate-spin" size={13} /> : null}
                                Trial
                              </button>
                            </span>
                          ) : null;
                        })}
                        {(skill.plugin_skills || []).slice(0, 4).map((pluginSkill) => {
                          const featureId = pluginSkill.id || pluginSkill.path || "";
                          const label = pluginSkill.name || featureId;
                          const trialKey = `${skill.id}:embedded_skill:${featureId}`;
                          const selection: ExternalSkillFeatureSelection = {
                            plugin_id: skill.id,
                            feature_kind: "embedded_skill",
                            feature_id: featureId,
                            name: label,
                            description: pluginSkill.description || "",
                            path: pluginSkill.path || "",
                            selection_source: "analysis_lab_report_flow",
                          };
                          const selectedForReport = reportFeatureSelectionKeys.has(externalSkillFeatureSelectionKey(selection));
                          return featureId ? (
                            <span className="flex min-w-0 flex-wrap items-center gap-1" key={trialKey}>
                              <button
                                className={`surface-chip max-w-full whitespace-normal break-words ${selectedForReport ? "border-[#8fdcc2]/50 bg-[#8fdcc2]/15 text-[#d8ffee]" : ""}`}
                                disabled={busy || !skill.mounted}
                                onClick={() => onToggleReportFeature(selection)}
                                title={pluginSkill.description || undefined}
                                type="button"
                              >
                                {selectedForReport ? "Used in report" : "Use in report"}: {label}
                              </button>
                              <button
                                className="surface-chip opacity-80"
                                disabled={busy || trialBusyId === trialKey}
                                onClick={() => void onRunFeatureTrial(skill, "embedded_skill", featureId)}
                                title="Run a one-off feature trial for this dataset."
                                type="button"
                              >
                                {trialBusyId === trialKey ? <LoaderCircle className="mr-1 animate-spin" size={13} /> : null}
                                Trial
                              </button>
                            </span>
                          ) : null;
                        })}
                      </div>
                    </div>
                  ) : null}
                  {skill.source === "local" && skill.source_path ? (
                    <p className="mt-2 break-words text-[11px] leading-5 text-[var(--muted)]">local: {skill.source_path}</p>
                  ) : null}
                </div>
                <span className="surface-chip max-w-full whitespace-normal break-words">
                  {skill.package_kind === "claude_plugin" ? "Claude plugin" : skill.mounted ? "Mounted" : "Installed"}
                </span>
              </div>

              <div className="mt-3 flex max-w-full flex-wrap gap-2">
                <button
                  className="surface-chip"
                  disabled={busy}
                  onClick={() => void onSetMounted(skill.id, !skill.mounted)}
                  type="button"
                >
                  {skill.mounted ? "取消挂载" : "挂载"}
                </button>
                <button
                  className="surface-chip"
                  disabled={busy}
                  onClick={() => void onDeleteSkill(skill.id)}
                  type="button"
                >
                  删除
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-[20px] border border-dashed border-white/10 bg-black/18 px-4 py-6 text-sm leading-7 text-[var(--muted)]">
            暂无外部 skill。先从 Anthropic GitHub 仓库下载一批，再把需要的条目挂到 Lab run。
          </div>
        )}
      </div>
      {!libraryExpanded && hiddenSkillCount > 0 ? (
        <p className="mt-3 rounded-[16px] border border-white/10 bg-white/5 px-3 py-2 text-xs leading-5 text-[var(--muted)]">
          已收起 {formatNumber(hiddenSkillCount)} 个插件；需要调整挂载、试跑或删除时再展开。
        </p>
      ) : null}
    </section>
  );
}

function ReportAgentTeamPanel({
  busy,
  error,
  localPath,
  mountedTeamIds,
  onDeleteTeam,
  onImportLocal,
  onRefresh,
  onRunTeam,
  onSetMounted,
  runTask,
  setLocalPath,
  status,
  teams,
}: {
  busy: boolean;
  error: string | null;
  localPath: string;
  mountedTeamIds: string[];
  onDeleteTeam: (teamId: string) => Promise<void>;
  onImportLocal: () => Promise<void>;
  onRefresh: (options?: { quiet?: boolean }) => Promise<void>;
  onRunTeam: () => Promise<void>;
  onSetMounted: (teamId: string, mounted: boolean) => Promise<void>;
  runTask: Record<string, unknown> | null;
  setLocalPath: Dispatch<SetStateAction<string>>;
  status: string;
  teams: LabReportAgentTeamItem[];
}) {
  const taskId = String(runTask?.job_id || runTask?.task_id || "");
  const taskStatus = String(runTask?.status || "");
  const [teamsExpanded, setTeamsExpanded] = useState(false);
  const mountedTeams = teams.filter((team) => team.mounted);
  const visibleTeams = teamsExpanded ? teams : (mountedTeams.length ? mountedTeams : teams).slice(0, 3);
  const hiddenTeamCount = Math.max(teams.length - visibleTeams.length, 0);
  return (
    <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Report Agent Teams</p>
          <h2 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">Lab 写报告 agent 团队</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
            导入本地 agent 团队、挂载到 Lab run，并直接用 Codex CLI 启动多 agent 报告写作任务。
          </p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-[var(--muted)]">
          {formatNumber(teams.length)} teams
        </span>
      </div>
      <div className="mb-4 grid gap-2 sm:grid-cols-3">
        <MetricCard label="Teams" value={formatNumber(teams.length)} />
        <MetricCard label="Mounted" value={formatNumber(mountedTeams.length)} />
        <MetricCard label="Task" value={taskStatus || (taskId ? "created" : "idle")} />
      </div>

      <label className="block space-y-2">
        <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Local team path</span>
        <input
          className="field-input"
          onChange={(event) => setLocalPath(event.target.value)}
          placeholder="C:\\path\\to\\agent-team"
          value={localPath}
        />
      </label>

      <div className="mt-3 flex flex-wrap gap-2">
        <button className="surface-chip" disabled={busy || !localPath.trim()} onClick={() => void onImportLocal()} type="button">
          <PackageOpen size={14} className="mr-1" />
          导入本地团队
        </button>
        <button className="surface-chip" disabled={busy} onClick={() => void onRefresh()} type="button">
          刷新
        </button>
        <button className="surface-chip" disabled={busy || !mountedTeamIds.length} onClick={() => void onRunTeam()} type="button">
          <Sparkles size={14} className="mr-1" />
          用 Codex CLI 运行
        </button>
        <span className="rounded-full border border-white/10 bg-black/18 px-3 py-2 text-xs text-[var(--muted)]">
          Mounted teams: {mountedTeamIds.length}
        </span>
      </div>

      <div className="mt-3 rounded-[18px] border border-white/10 bg-black/18 px-4 py-3 text-xs leading-6 text-[var(--muted)]">
        {status}
        {taskId ? <div className="mt-2 break-words">task: {taskId}{taskStatus ? ` · ${taskStatus}` : ""}</div> : null}
      </div>
      {error ? (
        <div className="mt-3 rounded-[18px] border border-red-300/20 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-100">
          {error}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-[20px] border border-white/10 bg-black/18 p-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">Agent team library</p>
          <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
            默认优先显示已挂载团队，减少对方法卡工作台的干扰。
          </p>
        </div>
        <button className="surface-chip" onClick={() => setTeamsExpanded((value) => !value)} type="button">
          {teamsExpanded ? "收起团队库" : `展开团队库 ${formatNumber(teams.length)}`}
        </button>
      </div>

      <div className="mt-3 grid gap-3">
        {teams.length ? (
          visibleTeams.map((team) => (
            <article
              className={`rounded-[22px] border p-4 transition ${
                team.mounted ? "border-[#74d0d9]/55 bg-[#74d0d9]/10" : "border-white/10 bg-black/18"
              }`}
              key={team.id}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="truncate text-sm font-semibold text-[var(--text-strong)]">{team.name}</h3>
                  <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                    {team.description || team.source_path || team.package_path}
                  </p>
                  <p className="mt-2 text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">
                    {team.source || "local"} · {formatNumber(team.agent_count || 0)} agents
                  </p>
                  {team.source_path ? (
                    <p className="mt-2 break-words text-[11px] leading-5 text-[var(--muted)]">local: {team.source_path}</p>
                  ) : null}
                </div>
                <span className="surface-chip">{team.mounted ? "Mounted" : "Installed"}</span>
              </div>
              {team.agents?.length ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {team.agents.slice(0, 8).map((agent) => (
                    <span className="surface-chip" key={`${team.id}-${agent.id}`}>
                      {agent.name}
                    </span>
                  ))}
                </div>
              ) : null}
              <div className="mt-3 flex flex-wrap gap-2">
                <button className="surface-chip" disabled={busy} onClick={() => void onSetMounted(team.id, !team.mounted)} type="button">
                  {team.mounted ? "取消挂载" : "挂载"}
                </button>
                <button className="surface-chip" disabled={busy} onClick={() => void onDeleteTeam(team.id)} type="button">
                  删除
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-[20px] border border-dashed border-white/10 bg-black/18 px-4 py-6 text-sm leading-7 text-[var(--muted)]">
            暂无写报告 agent 团队。导入一个本地团队目录后，就可以挂载到 Lab 并直接交给 Codex CLI 执行。
          </div>
        )}
      </div>
      {!teamsExpanded && hiddenTeamCount > 0 ? (
        <p className="mt-3 rounded-[16px] border border-white/10 bg-white/5 px-3 py-2 text-xs leading-5 text-[var(--muted)]">
          已收起 {formatNumber(hiddenTeamCount)} 个团队；需要重新挂载或删除时再展开。
        </p>
      ) : null}
    </section>
  );
}

function UnavailableBadge({ reason }: { reason: string }) {
  return (
    <span className="lab-unavailable-badge" title={reason}>
      <LockKeyhole size={12} />
      执行待满足
    </span>
  );
}

function BlockedReasonPanel({
  action,
  reason,
}: {
  action?: string;
  reason: string;
}) {
  return (
    <div className="lab-blocked-panel" role="note">
      <CircleAlert className="mt-0.5 shrink-0 text-amber-200" size={16} />
      <div className="min-w-0">
        <p className="font-medium text-amber-50">{reason}</p>
        <p className="mt-1 text-amber-100/80">{action || blockReasonAction(reason)}</p>
      </div>
    </div>
  );
}

function LabStatusRail({
  dataset,
  methodCount,
  methodQuality,
  mode,
  selectedRunCount,
  selectedSheetName,
  visualMethodCount,
}: {
  dataset?: DatasetItem;
  methodCount: number;
  methodQuality: MethodQualitySummary;
  mode: RunMode;
  selectedRunCount: number;
  selectedSheetName: string;
  visualMethodCount: number;
}) {
  const items = [
    {
      icon: Database,
      label: "数据集",
      value: datasetLabel(dataset),
    },
    {
      icon: Table2,
      label: "工作表",
      value: selectedSheetName || "Default sheet",
    },
    {
      icon: SlidersHorizontal,
      label: "运行模式",
      value: RUN_MODE_LABELS[mode],
    },
    {
      icon: Layers3,
      label: "已选运行",
      value: formatNumber(selectedRunCount),
    },
    {
      icon: Workflow,
      label: "方法池",
      value: `${formatNumber(methodCount)} / ${formatNumber(visualMethodCount)} visual`,
    },
    {
      icon: CheckCircle2,
      label: "可运行",
      value: `${formatNumber(methodQuality.runnable)} ready`,
    },
  ];

  return (
    <section className="lab-command-strip" aria-label="Lab command context">
      {items.map(({ icon: Icon, label, value }) => (
        <div className="lab-command-item" key={label}>
          <span className="lab-command-icon">
            <Icon size={15} />
          </span>
          <span className="min-w-0">
            <span className="lab-command-label">{label}</span>
            <span className="lab-command-value">{value}</span>
          </span>
        </div>
      ))}
    </section>
  );
}

function WorkflowProgressCard({ progress }: { progress: WorkflowProgressState }) {
  const visible = progress.active || progress.phase === "ready" || progress.phase === "failed";
  if (!visible) return null;
  const stages = [
    { id: "upload", label: "上传" },
    { id: "understand", label: "理解" },
    { id: "clean", label: "清洗" },
    { id: "derive", label: "派生" },
    { id: "ready", label: "可用" },
  ];
  const activeIndex = Math.max(0, stages.findIndex((stage) => stage.id === progress.phase));
  return (
    <div className="mt-4 rounded-[22px] border border-white/10 bg-black/22 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--muted)]">预处理进度</p>
          <h3 className="mt-1 text-sm font-semibold text-[var(--text-strong)]">{progress.title || "等待上传表格"}</h3>
        </div>
        <span className="surface-chip">{formatNumber(Math.round(progress.percent))}%</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/8">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            progress.phase === "failed" ? "bg-red-300" : "bg-gradient-to-r from-[#ff9c61] via-[#ffd28f] to-[#74d0d9]"
          }`}
          style={{ width: `${Math.max(4, progress.percent)}%` }}
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {stages.map((stage, index) => {
          const done = progress.phase === "ready" || index < activeIndex;
          const active = stage.id === progress.phase;
          return (
            <span
              className={`rounded-full border px-2.5 py-1 text-[10px] ${
                done || active
                  ? "border-[#74d0d9]/35 bg-[#74d0d9]/10 text-[var(--text-strong)]"
                  : "border-white/10 bg-white/5 text-[var(--muted)]"
              }`}
              key={stage.id}
            >
              {stage.label}
            </span>
          );
        })}
      </div>
      <p className="mt-3 text-xs leading-5 text-[var(--muted)]">{progress.detail}</p>
    </div>
  );
}

function RunGuidanceCard({
  analysisBlockAction,
  analysisBlockReason,
  currentMethodName,
  isBusy,
  mode,
  selectedDataset,
  selectedRunCount,
  selectedSheetName,
  status,
}: {
  analysisBlockAction: string;
  analysisBlockReason: string;
  currentMethodName: string;
  isBusy: boolean;
  mode: RunMode;
  selectedDataset?: DatasetItem;
  selectedRunCount: number;
  selectedSheetName: string;
  status: string;
}) {
  const hasDataset = Boolean(selectedDataset);
  const isReady = Boolean(!analysisBlockReason && hasDataset);
  const methodDetail = mode === "method"
    ? currentMethodName
      ? `当前方法：${currentMethodName}`
      : "在右侧方法目录中选一个方法，或切换到合并/批量模式。"
    : selectedRunCount
      ? `已加入 ${formatNumber(selectedRunCount)} 个方法运行。`
      : "可直接使用推荐路径，也可以先在右侧方法目录加入方法。";
  const steps = [
    {
      done: hasDataset,
      label: "准备数据",
      text: hasDataset
        ? `${datasetLabel(selectedDataset)} · ${selectedSheetName || "Default sheet"}`
        : "上传表格，或从已保存数据集中选择一个数据集。",
    },
    {
      done: true,
      label: "选择路径",
      text: `当前路径：${RUN_MODE_LABELS[mode]}`,
    },
    {
      done: mode === "method" ? Boolean(currentMethodName) : Boolean(selectedRunCount) || mode === "auto" || mode === "smart_report",
      label: "配置方法",
      text: methodDetail,
    },
    {
      done: isReady,
      label: "开始执行",
      text: isReady
        ? "点击下方主按钮运行；完成后在右侧画布查看图表、表格和下载产物。"
        : analysisBlockAction || "按上面的步骤补齐条件后，执行按钮会自动恢复。",
    },
  ];

  return (
    <div className="run-guidance-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--muted)]">Run guide</p>
          <h3 className="mt-1 text-sm font-semibold text-[var(--text-strong)]">运行指导</h3>
        </div>
        <span className={`surface-chip ${isReady ? "border-[#74d0d9]/40 bg-[#74d0d9]/10 text-[var(--text-strong)]" : ""}`}>
          {isBusy ? "运行中" : isReady ? "可执行" : "待补齐"}
        </span>
      </div>
      <div className="mt-3 grid gap-2">
        {steps.map((step, index) => (
          <div className={`run-guidance-step ${step.done ? "is-done" : ""}`} key={step.label}>
            <span className="run-guidance-index">
              {step.done ? <CheckCircle2 size={13} /> : index + 1}
            </span>
            <span className="min-w-0">
              <span className="block text-xs font-semibold text-[var(--text-strong)]">{step.label}</span>
              <span className="mt-1 block text-[11px] leading-5 text-[var(--muted)]">{step.text}</span>
            </span>
          </div>
        ))}
      </div>
      {analysisBlockReason ? (
        <div className="run-guidance-warning">
          <CircleAlert className="mt-0.5 shrink-0" size={14} />
          <span>{analysisBlockReason}</span>
        </div>
      ) : (
        <p className="mt-3 text-[11px] leading-5 text-[var(--muted)]">{status}</p>
      )}
    </div>
  );
}

type ThemedSelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

function themedSelectLabel(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(themedSelectLabel).join("");
  return "";
}

function ThemedSelect({
  ariaLabel,
  children,
  className = "",
  compact = false,
  emptyMessage = "暂无可选项",
  onChange,
  options,
  placeholder = "请选择",
  value,
}: {
  ariaLabel?: string;
  children?: ReactNode;
  className?: string;
  compact?: boolean;
  emptyMessage?: string;
  onChange: (event: { target: { value: string } }) => void;
  options?: ThemedSelectOption[];
  placeholder?: string;
  value: string;
}) {
  const [open, setOpen] = useState(false);
  const [menuRect, setMenuRect] = useState({ left: 0, maxHeight: 280, top: 0, width: 0 });
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const selectOptions =
    options ||
    Children.toArray(children).flatMap((child) => {
      if (!isValidElement(child)) return [];
      const props = child.props as { children?: ReactNode; disabled?: boolean; value?: unknown };
      return [
        {
          disabled: Boolean(props.disabled),
          label: themedSelectLabel(props.children) || String(props.value ?? ""),
          value: String(props.value ?? ""),
        },
      ];
    });
  const isCompact = compact || className.includes("theme-select-compact");
  const selectedOption = selectOptions.find((option) => option.value === value);

  useEffect(() => {
    if (!open) return;

    function syncMenuRect() {
      const button = buttonRef.current;
      if (!button || typeof window === "undefined") return;
      const rect = button.getBoundingClientRect();
      const viewportPadding = 14;
      const spaceBelow = window.innerHeight - rect.bottom - viewportPadding;
      const spaceAbove = rect.top - viewportPadding;
      const dropUp = spaceBelow < 180 && spaceAbove > spaceBelow;
      const maxHeight = Math.max(156, Math.min(320, Math.max(spaceBelow, spaceAbove) - 8));
      const left = Math.max(viewportPadding, Math.min(rect.left, window.innerWidth - rect.width - viewportPadding));
      setMenuRect({
        left,
        maxHeight,
        top: dropUp ? Math.max(viewportPadding, rect.top - maxHeight - 8) : rect.bottom + 8,
        width: rect.width,
      });
    }

    syncMenuRect();
    window.addEventListener("resize", syncMenuRect);
    window.addEventListener("scroll", syncMenuRect, true);
    return () => {
      window.removeEventListener("resize", syncMenuRect);
      window.removeEventListener("scroll", syncMenuRect, true);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (buttonRef.current?.contains(target) || menuRef.current?.contains(target)) return;
      setOpen(false);
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setOpen(false);
      buttonRef.current?.focus();
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  function choose(nextValue: string) {
    onChange({ target: { value: nextValue } });
    setOpen(false);
    requestAnimationFrame(() => buttonRef.current?.focus());
  }

  const menu =
    open && typeof document !== "undefined"
      ? createPortal(
          <div
            className={`theme-select-menu ${isCompact ? "theme-select-menu-compact" : ""}`}
            ref={menuRef}
            role="listbox"
            style={{
              left: menuRect.left,
              maxHeight: menuRect.maxHeight,
              top: menuRect.top,
              width: menuRect.width,
            }}
          >
            {selectOptions.length ? (
              selectOptions.map((option, index) => {
                const selected = option.value === value;
                return (
                  <button
                    aria-selected={selected}
                    className={`theme-select-option ${selected ? "is-selected" : ""}`}
                    disabled={option.disabled}
                    key={`${option.value || "empty"}-${index}`}
                    onClick={() => choose(option.value)}
                    role="option"
                    type="button"
                  >
                    <span className="min-w-0 truncate">{option.label}</span>
                    {selected ? <CheckCircle2 className="theme-select-option-check" size={14} /> : null}
                  </button>
                );
              })
            ) : (
              <div className="theme-select-empty">{emptyMessage}</div>
            )}
          </div>,
          document.body,
        )
      : null;

  return (
    <div className="theme-select-root">
      <button
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={ariaLabel}
        className={`theme-select-trigger ${isCompact ? "theme-select-trigger-compact" : ""}`}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            setOpen(true);
          }
        }}
        ref={buttonRef}
        type="button"
      >
        <span className={`theme-select-value ${selectedOption ? "" : "theme-select-placeholder"}`}>
          {selectedOption?.label || placeholder}
        </span>
        <ChevronDown className={`theme-select-chevron ${open ? "is-open" : ""}`} size={15} />
      </button>
      {menu}
    </div>
  );
}

function FieldSelect({
  help,
  label,
  onChange,
  options,
  value,
}: {
  help?: ReactNode;
  label: string;
  onChange: (value: string) => void;
  options: string[];
  value: string;
}) {
  return (
    <label className="block space-y-2">
      <span className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{label}</span>
      {help ? <span className="block text-[11px] leading-5 text-[var(--muted)]">{help}</span> : null}
      <ThemedSelect className="field-input" onChange={(event) => onChange(event.target.value)} value={value}>
        <option value="">自动选择</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </ThemedSelect>
    </label>
  );
}

function SearchableFieldSelect({
  help,
  label,
  onChange,
  options,
  value,
}: {
  help?: ReactNode;
  label: string;
  onChange: (value: string) => void;
  options: string[];
  value: string;
}) {
  const [query, setQuery] = useState("");
  const normalizedOptions = useMemo(() => uniqueStrings(options), [options]);
  const normalizedQuery = query.trim().toLowerCase();
  const filteredOptions = normalizedQuery
    ? normalizedOptions.filter((option) => option.toLowerCase().includes(normalizedQuery))
    : normalizedOptions;
  const visibleOptions = useMemo(() => {
    const limited = filteredOptions.slice(0, 120);
    if (value && normalizedOptions.includes(value) && !limited.includes(value)) {
      return [value, ...limited.filter((option) => option !== value)];
    }
    return limited;
  }, [filteredOptions, normalizedOptions, value]);

  function commit(nextValue: string) {
    setQuery("");
    onChange(nextValue);
  }

  return (
    <label className="block space-y-2">
      <span className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{label}</span>
      {help ? <span className="block text-[11px] leading-5 text-[var(--muted)]">{help}</span> : null}
      <input
        className="field-input"
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            if (visibleOptions[0]) commit(visibleOptions[0]);
          }
          if (event.key === "Escape") {
            setQuery(value);
          }
        }}
        placeholder={`${value ? `当前：${value} · ` : ""}搜索字段 · 共 ${formatNumber(normalizedOptions.length)} 项`}
        value={query}
      />
      <ThemedSelect className="field-input" onChange={(event) => commit(event.target.value)} value={value}>
        <option value="">自动选择</option>
        {visibleOptions.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </ThemedSelect>
    </label>
  );
}

function FieldChipPicker({
  help,
  label,
  options,
  selectedValues,
  onToggle,
  tone = "cool",
  emptyMessage,
  searchPlaceholder,
}: {
  help?: ReactNode;
  label: string;
  options: string[];
  selectedValues: string[];
  onToggle: (value: string) => void;
  tone?: "cool" | "warm";
  emptyMessage?: string;
  searchPlaceholder?: string;
}) {
  const [query, setQuery] = useState("");
  const normalizedOptions = useMemo(() => uniqueStrings(options), [options]);
  const selectedSet = useMemo(() => new Set(uniqueStrings(selectedValues)), [selectedValues]);
  const normalizedQuery = query.trim().toLowerCase();
  const filteredOptions = normalizedQuery
    ? normalizedOptions.filter((option) => option.toLowerCase().includes(normalizedQuery))
    : normalizedOptions;
  const selectedFirst = filteredOptions.filter((option) => selectedSet.has(option));
  const remaining = filteredOptions.filter((option) => !selectedSet.has(option)).slice(0, 120);
  const visibleOptions = uniqueStrings([...selectedFirst, ...remaining]);
  const selectedOptions = normalizedOptions.filter((option) => selectedSet.has(option));
  const hiddenCount = Math.max(filteredOptions.length - visibleOptions.length, 0);
  const selectedChipClass = tone === "warm"
    ? "border-[#ff9c61]/55 bg-[#ff9c61]/14 text-[var(--text-strong)]"
    : "border-[#74d0d9]/55 bg-[#74d0d9]/14 text-[var(--text-strong)]";
  const inactiveChipClass = tone === "warm"
    ? "border-white/10 bg-white/5 text-[var(--muted)] hover:bg-white/10"
    : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/10";

  return (
    <div className="mt-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{label}</p>
          {help ? <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">{help}</p> : null}
        </div>
        <span className="surface-chip">{selectedOptions.length ? `已选 ${selectedOptions.length}` : emptyMessage || "自动建议"}</span>
      </div>
      <input
        className="field-input mt-2"
        onChange={(event) => setQuery(event.target.value)}
        placeholder={searchPlaceholder || `搜索字段 · 共 ${formatNumber(normalizedOptions.length)} 项`}
        value={query}
      />
      <div className="mt-2 flex max-h-[140px] flex-wrap gap-2 overflow-auto rounded-[16px] border border-white/10 bg-black/18 p-2">
        {visibleOptions.length ? visibleOptions.map((option) => {
          const active = selectedSet.has(option);
          return (
            <button
              aria-pressed={active}
              className={`rounded-full border px-2.5 py-1 text-[11px] transition ${active ? selectedChipClass : inactiveChipClass}`}
              key={option}
              onClick={() => onToggle(option)}
              type="button"
            >
              {option}
            </button>
          );
        }) : (
          <span className="text-xs text-[var(--muted)]">{emptyMessage || "没有匹配的字段"}</span>
        )}
      </div>
      {hiddenCount > 0 ? (
        <p className="mt-2 text-[11px] leading-5 text-[var(--muted)]">
          还有 {formatNumber(hiddenCount)} 个字段，继续搜索可以缩小范围。
        </p>
      ) : null}
    </div>
  );
}

function LabFieldWorkflowPanel({
  dataset,
  derivedMetricEdits,
  fieldSelection,
  onAddDerivedMetric,
  onReset,
  setDerivedMetricEdits,
  setFieldSelection,
}: {
  dataset?: DatasetItem;
  derivedMetricEdits: DerivedMetricEdit[];
  fieldSelection: FieldSelection;
  onAddDerivedMetric: () => void;
  onReset: () => void;
  setDerivedMetricEdits: Dispatch<SetStateAction<DerivedMetricEdit[]>>;
  setFieldSelection: Dispatch<SetStateAction<FieldSelection>>;
}) {
  const allColumns = columnNames(dataset);
  const numericColumns = dataset?.numeric_columns || [];
  const targetColumns = uniqueStrings([...allColumns, ...allDerivedMetricFields(derivedMetricEdits)]);
  const categoryColumns = uniqueStrings([...(dataset?.categorical_columns || []), ...(dataset?.column_summaries || []).map((item) => item.name)]);
  const timeColumns = dataset?.datetime_columns || [];
  const selectedDerivedCount = derivedMetricEdits.filter((item) => item.selected).length;

  function updateField<K extends keyof FieldSelection>(key: K, value: FieldSelection[K]) {
    setFieldSelection((current) => ({ ...current, [key]: value }));
  }

  function updateNestedField<T extends "bubble" | "quadrant">(group: T, key: keyof FieldSelection[T], value: string) {
    setFieldSelection((current) => ({
      ...current,
      [group]: { ...current[group], [key]: value },
    }));
  }

  function toggleFeature(column: string) {
    setFieldSelection((current) => {
      const features = current.features.includes(column)
        ? current.features.filter((item) => item !== column)
        : uniqueStrings([...current.features, column]).slice(0, 8);
      return { ...current, features };
    });
  }

  function updateDerivedMetric(index: number, patch: Partial<DerivedMetricEdit>) {
    setDerivedMetricEdits((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)),
    );
  }

  return (
    <section className="rounded-[32px] border border-white/10 bg-[#0d1213]/88 p-5 shadow-2xl backdrop-blur-2xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">上传表格 → 识别数据 → 清洗数据 → 派生指标 → 方法选数据</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">Lab 字段流程</h2>
          <p className="mt-2 max-w-4xl text-sm leading-7 text-[var(--muted)]">
            字段画像来自当前数据集详情；清洗沿用后端读取后的标准化表；派生指标支持中文名、计算方式和手动重命名；每个方法卡旁边可以再覆盖自己的字段绑定。
          </p>
        </div>
        <button className="surface-chip" onClick={onReset} type="button">
          恢复自动推荐
        </button>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1.1fr]">
        <div className="grid gap-4">
          <div className="grid gap-3 sm:grid-cols-4">
            <MetricCard label="字段" value={formatNumber(allColumns.length)} />
            <MetricCard label="数值" value={formatNumber(numericColumns.length)} />
            <MetricCard label="分组" value={formatNumber(dataset?.categorical_columns?.length)} />
            <MetricCard label="派生" value={formatNumber(selectedDerivedCount)} />
          </div>

          <div className="rounded-[24px] border border-white/10 bg-black/18 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">字段绑定</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <SearchableFieldSelect label="目标字段" onChange={(value) => updateField("target", value)} options={targetColumns} value={fieldSelection.target} />
              <SearchableFieldSelect label="分组字段" onChange={(value) => updateField("group", value)} options={allColumns} value={fieldSelection.group} />
              <SearchableFieldSelect label="标签字段" onChange={(value) => updateField("label", value)} options={allColumns} value={fieldSelection.label} />
              <SearchableFieldSelect label="时间字段" onChange={(value) => updateField("time", value)} options={timeColumns.length ? timeColumns : allColumns} value={fieldSelection.time} />
            </div>

            <div className="mt-4">
              <FieldChipPicker
                emptyMessage="当前表没有可识别数值字段。"
                label="特征字段"
                onToggle={toggleFeature}
                options={numericColumns}
                selectedValues={fieldSelection.features}
                searchPlaceholder="搜索特征字段"
              />
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <SearchableFieldSelect label="气泡 X" onChange={(value) => updateNestedField("bubble", "x", value)} options={numericColumns} value={fieldSelection.bubble.x} />
              <SearchableFieldSelect label="气泡 Y" onChange={(value) => updateNestedField("bubble", "y", value)} options={numericColumns} value={fieldSelection.bubble.y} />
              <SearchableFieldSelect label="气泡大小" onChange={(value) => updateNestedField("bubble", "size", value)} options={numericColumns} value={fieldSelection.bubble.size} />
              <SearchableFieldSelect label="象限 X" onChange={(value) => updateNestedField("quadrant", "x", value)} options={numericColumns} value={fieldSelection.quadrant.x} />
              <SearchableFieldSelect label="象限 Y" onChange={(value) => updateNestedField("quadrant", "y", value)} options={numericColumns} value={fieldSelection.quadrant.y} />
              <SearchableFieldSelect label="对象字段" onChange={(value) => updateNestedField("quadrant", "label", value)} options={allColumns} value={fieldSelection.quadrant.label} />
            </div>
          </div>

          <div className="rounded-[24px] border border-white/10 bg-black/18 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">字段画像</p>
            <div className="mt-3 max-h-[230px] overflow-auto rounded-[18px] border border-white/10 bg-white/5">
              {(dataset?.column_summaries || []).slice(0, 24).map((summary) => (
                <div className="grid grid-cols-[1fr_auto] gap-3 border-b border-white/8 px-3 py-2 text-xs last:border-b-0" key={summary.name}>
                  <span className="truncate text-[var(--text-strong)]">{summary.name}</span>
                  <span className="text-[var(--muted)]">
                    {summary.dtype || "unknown"} · missing {formatValue(Number(summary.missing_ratio || 0) * 100)}%
                  </span>
                </div>
              ))}
              {!dataset?.column_summaries?.length ? (
                <div className="px-3 py-8 text-center text-sm text-[var(--muted)]">选择或上传数据集后显示字段画像。</div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="rounded-[24px] border border-white/10 bg-black/18 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">派生指标</p>
              <h3 className="mt-1 text-xl font-semibold text-[var(--text-strong)]">中文命名、计算方式、手动重命名</h3>
            </div>
            <button className="surface-chip" onClick={onAddDerivedMetric} type="button">
              新增指标
            </button>
          </div>

          <div className="mt-4 grid max-h-[590px] gap-3 overflow-auto pr-1">
            {derivedMetricEdits.map((edit, index) => (
              <article className="rounded-[20px] border border-white/10 bg-white/5 p-4" key={`${edit.field}-${index}`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-[var(--muted)]">
                    <input
                      checked={edit.selected}
                      onChange={() => updateDerivedMetric(index, { selected: !edit.selected })}
                      type="checkbox"
                    />
                    纳入方法数据
                  </label>
                  <span className="surface-chip">{edit.recipe_id || "custom"}</span>
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <label className="space-y-2">
                    <span className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">中文名</span>
                    <input
                      className="field-input"
                      onChange={(event) => updateDerivedMetric(index, { display_name: event.target.value })}
                      value={edit.display_name}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">字段名</span>
                    <input
                      className="field-input"
                      onChange={(event) => updateDerivedMetric(index, { field: event.target.value })}
                      value={edit.field}
                    />
                  </label>
                </div>
                <label className="mt-3 block space-y-2">
                  <span className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">计算方式</span>
                  <input
                    className="field-input"
                    onChange={(event) => updateDerivedMetric(index, { formula: event.target.value })}
                    value={edit.formula}
                  />
                </label>
                <FieldChipPicker
                  emptyMessage="当前表没有可识别字段。"
                  label="来源字段"
                  onToggle={(column) =>
                    updateDerivedMetric(index, {
                      source_fields: edit.source_fields.includes(column)
                        ? edit.source_fields.filter((item) => item !== column)
                        : uniqueStrings([...edit.source_fields, column]).slice(0, 4),
                    })
                  }
                  options={allColumns}
                  searchPlaceholder="搜索来源字段"
                  selectedValues={edit.source_fields}
                  tone="warm"
                />
              </article>
            ))}
            {!derivedMetricEdits.length ? (
              <div className="rounded-[20px] border border-dashed border-white/10 px-4 py-10 text-center text-sm text-[var(--muted)]">
                当前数据集暂未生成派生指标草稿，可手动新增。
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function MethodWorkspacePanel({
  catalogLoaded,
  dataset,
  derivedMetricEdits,
  fieldSelection,
  methods,
  groupedView,
  setGroupedView,
  methodSearch,
  setMethodSearch,
  methodFilter,
  setMethodFilter,
  methodFieldBindings,
  setMethodFieldBindings,
  filteredMethodBundles,
  groupedMethodCounts,
  filteredMethods,
  selectedMethodId,
  activeMethodFamily,
  activeMethodSource,
  setActiveMethodFamily,
  setActiveMethodSource,
  selectedMethodBundles,
  selectedMethodIds,
  selectedRunCount,
  selectedRunSpecs,
  methodRunSpecs,
  activeMethodRunIds,
  activeSelectedMethod,
  activeEditorMethod,
  recommendedMethodSlice,
  selectedMethods,
  selectMethod,
  toggleMethod,
  selectFilteredMethods,
  clearFilteredMethods,
  replaceSelectedMethods,
  addMethodBundleRunGroup,
  addMethodBundleRunGroups,
  appendMethodRun,
  removeMethodRunGroup,
  methodCardSaveBusyId,
  methodSourceCounts,
  replaceMethodRuns,
  removeMethodRun,
  updateMethodRunSpec,
  updateRunGroup,
  runSingleMethod,
  saveCurrentMethodCard,
  hiddenMethodCount,
  loadMoreMethods,
  visibleBundleCount,
  visibleGroupedMethods,
  visibleMethodCount,
  visibleMethods,
  visualMethodCount,
  methodQuality,
  syncMethodRunBinding,
  setActiveMethodRunIds,
  setEditorTarget,
  methodEditorOpen,
  setMethodEditorOpen,
}: {
  catalogLoaded: boolean;
  dataset?: DatasetItem;
  derivedMetricEdits: DerivedMetricEdit[];
  fieldSelection: FieldSelection;
  methods: MethodCatalogItem[];
  groupedView: boolean;
  setGroupedView: (value: boolean | ((current: boolean) => boolean)) => void;
  methodSearch: string;
  setMethodSearch: (value: string) => void;
  methodFilter: MethodFilter;
  setMethodFilter: (value: MethodFilter) => void;
  methodFieldBindings: MethodFieldBindings;
  setMethodFieldBindings: Dispatch<SetStateAction<MethodFieldBindings>>;
  filteredMethodBundles: MethodBundle[];
  groupedMethodCounts: Array<[string, number]>;
  filteredMethods: MethodCatalogItem[];
  selectedMethodId: string;
  activeMethodFamily: string;
  activeMethodSource: string;
  setActiveMethodFamily: (value: string) => void;
  setActiveMethodSource: (value: string) => void;
  selectedMethodBundles: MethodBundle[];
  selectedMethodIds: Set<string>;
  selectedRunCount: number;
  selectedRunSpecs: MethodRunSpec[];
  methodRunSpecs: MethodRunSpec[];
  activeMethodRunIds: Record<string, string>;
  activeSelectedMethod: MethodCatalogItem | null;
  activeEditorMethod: MethodCatalogItem | null;
  recommendedMethodSlice: MethodCatalogItem[];
  selectedMethods: MethodCatalogItem[];
  selectMethod: (methodId: string) => void;
  toggleMethod: (methodId: string) => void;
  selectFilteredMethods: () => void;
  clearFilteredMethods: () => void;
  replaceSelectedMethods: (methodIds: string[]) => void;
  addMethodBundleRunGroup: (bundle: MethodBundle, options?: { replaceExisting?: boolean }) => void;
  addMethodBundleRunGroups: (bundles: MethodBundle[]) => void;
  appendMethodRun: (methodId: string, overrides?: Partial<MethodRunSpec>) => void;
  removeMethodRunGroup: (groupId: string) => void;
  methodCardSaveBusyId: string | null;
  methodSourceCounts: Array<[string, number]>;
  replaceMethodRuns: (methodId: string, nextRuns: MethodRunSpec[]) => void;
  removeMethodRun: (runId: string) => void;
  updateMethodRunSpec: (methodId: string, runId: string, patch: MethodRunSpecPatch) => void;
  updateRunGroup: (run: MethodRunSpec | null | undefined, patch: MethodRunSpecPatch) => void;
  runSingleMethod: (method: MethodCatalogItem) => Promise<void>;
  saveCurrentMethodCard: (method: MethodCatalogItem, activeRun?: MethodRunSpec | null) => Promise<void>;
  hiddenMethodCount: number;
  loadMoreMethods: () => void;
  visibleBundleCount: number;
  visibleGroupedMethods: Array<[string, MethodBundle[]]>;
  visibleMethodCount: number;
  visibleMethods: MethodCatalogItem[];
  visualMethodCount: number;
  methodQuality: MethodQualitySummary;
  syncMethodRunBinding: (methodId: string, patch: Partial<MethodFieldBinding>) => void;
  setActiveMethodRunIds: Dispatch<SetStateAction<Record<string, string>>>;
  setEditorTarget: Dispatch<SetStateAction<MethodEditorTarget | null>>;
  methodEditorOpen: boolean;
  setMethodEditorOpen: Dispatch<SetStateAction<boolean>>;
}) {
  const recommendedIds = useMemo(() => new Set(recommendedMethodSlice.map((method) => method.id)), [recommendedMethodSlice]);
  const searchActive = Boolean(methodSearch.trim());
  const [expandedBundleIds, setExpandedBundleIds] = useState<Set<string>>(() => new Set());
  const [methodGuideTopic, setMethodGuideTopic] = useState<MethodGuideTopic>("object");
  const [methodGuideOpen, setMethodGuideOpen] = useState(false);
  const methodsById = useMemo(() => new Map(methods.map((method) => [method.id, method])), [methods]);
  const objectCandidateCache = useMemo(() => {
    const cache = new Map<string, string[]>();
    const rows = dataset?.sample_rows || [];
    for (const objectSelectionLabelKey of columnNames(dataset)) {
      cache.set(
        objectSelectionLabelKey,
        uniqueStrings(
          rows
            .map((row) => {
              if (!isRecord(row)) return "";
              const value = row[objectSelectionLabelKey];
              if (value == null) return "";
              if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
                return String(value).trim();
              }
              return "";
            })
            .filter(Boolean),
        ).slice(0, 24),
      );
    }
    return cache;
  }, [dataset]);

  const recommendedBundles = useMemo(
    () => buildMethodBundles(recommendedMethodSlice),
    [recommendedMethodSlice],
  );
  const visibleBundles = useMemo(
    () => (searchActive ? buildMethodBundles(visibleMethods) : visibleGroupedMethods.flatMap(([, bundles]) => bundles)),
    [searchActive, visibleGroupedMethods, visibleMethods],
  );
  const visibleBundleIds = useMemo(() => new Set(visibleBundles.map((bundle) => bundle.id)), [visibleBundles]);
  const effectiveExpandedBundleIds = useMemo(
    () => new Set([...expandedBundleIds].filter((bundleId) => visibleBundleIds.has(bundleId))),
    [expandedBundleIds, visibleBundleIds],
  );
  const selectedReadinessLabel = methodQuality.selected
    ? `${formatNumber(methodQuality.selectedRunnable)} / ${formatNumber(methodQuality.selected)} selected ready`
    : "no selected runs yet";
  const selectedRunGroups = useMemo(() => {
    const groups = new Map<string, MethodRunSpec[]>();
    for (const run of selectedRunSpecs) {
      const groupId = run.bundle_run_id || `single:${run.run_id}`;
      const list = groups.get(groupId) || [];
      list.push(run);
      groups.set(groupId, list);
    }
    return [...groups.entries()].map(([groupId, runs]) => ({ groupId, runs }));
  }, [selectedRunSpecs]);
  const editorPortalTarget = typeof document !== "undefined" ? document.body : null;

  function openMethodGuide(topic: MethodGuideTopic) {
    setMethodGuideTopic(topic);
    setMethodGuideOpen(true);
  }

  function toggleBundleDetails(bundleId: string) {
    setExpandedBundleIds((current) => {
      const next = new Set(current);
      if (next.has(bundleId)) {
        next.delete(bundleId);
      } else {
        next.add(bundleId);
      }
      return next;
    });
  }

  function selectBundleDefaults(bundle: MethodBundle) {
    const bundleIds = new Set(bundle.methods.map((method) => method.id));
    const defaults = bundleInteractionState(bundle, dataset).defaults.map((method) => method.id);
    if (!defaults.length) {
      setExpandedBundleIds((current) => new Set(current).add(bundle.id));
      selectMethod(bundle.representative.id);
      return;
    }
    const preserved = Array.from(selectedMethodIds).filter((methodId) => !bundleIds.has(methodId));
    const nextIds = clampMethodIds([...preserved, ...defaults]);
    replaceSelectedMethods(nextIds);
    const focusId = defaults.find((methodId) => nextIds.includes(methodId)) || nextIds[0] || "";
    if (focusId) {
      selectMethod(focusId);
    } else {
      selectMethod(bundle.representative.id);
    }
  }

  function addBundleRunGroup(bundle: MethodBundle, options?: { replaceExisting?: boolean }) {
    const defaults = bundleInteractionState(bundle, dataset).defaults;
    if (!defaults.length) {
      setExpandedBundleIds((current) => new Set(current).add(bundle.id));
      selectMethod(bundle.representative.id);
      return;
    }
    addMethodBundleRunGroup(bundle, options);
    setExpandedBundleIds((current) => new Set(current).add(bundle.id));
  }

  function appendBundleDefaults(bundle: MethodBundle) {
    addBundleRunGroup(bundle);
  }

  function addBundleRunGroups(bundles: MethodBundle[]) {
    addMethodBundleRunGroups(bundles);
    for (const bundle of bundles) {
      setExpandedBundleIds((current) => new Set(current).add(bundle.id));
    }
  }

  function runsForMethod(methodId: string) {
    return methodRunSpecs.filter((spec) => spec.method_id === methodId);
  }

  function activeRunForMethod(methodId: string) {
    const runs = runsForMethod(methodId);
    const activeRunId = activeMethodRunIds[methodId] || runs[0]?.run_id || "";
    return runs.find((run) => run.run_id === activeRunId) || runs[0] || null;
  }

  function focusMethodRun(methodId: string, runId: string) {
    selectMethod(methodId);
    setActiveMethodRunIds((current) => ({
      ...current,
      [methodId]: runId,
    }));
    setEditorTarget({ methodId, runId });
    setMethodEditorOpen(true);
  }

  function openMethodEditor(methodId: string, runId?: string) {
    if (runId) {
      focusMethodRun(methodId, runId);
      return;
    }
    selectMethod(methodId);
    const methodRuns = runsForMethod(methodId);
    const activeRun = activeMethodRunIds[methodId] || methodRuns[0]?.run_id || "";
    if (activeRun) {
      setActiveMethodRunIds((current) => ({
        ...current,
        [methodId]: activeRun,
      }));
      setEditorTarget({ methodId, runId: activeRun });
      setMethodEditorOpen(true);
      return;
    }
    const method = methodsById.get(methodId);
    const needsObjectSelection = method
      ? methodBindingControls(method).has("object_selection") || methodRecommendedSelectionMode(method) === "object"
      : false;
    if (needsObjectSelection) {
      appendMethodRun(methodId, { selection_mode: "object" });
      return;
    }
    setEditorTarget({ methodId });
    setMethodEditorOpen(true);
  }

  function closeMethodEditor() {
    setMethodEditorOpen(false);
    setEditorTarget(null);
  }

  function focusBundleSelection(bundle: MethodBundle) {
    const run = methodRunSpecs.find((spec) => bundle.methods.some((method) => method.id === spec.method_id));
    if (run) {
      focusMethodRun(run.method_id, run.run_id);
      return;
    }
    const method = bundle.methods.find((item) => selectedMethodIds.has(item.id)) || bundle.representative;
    openMethodEditor(method.id);
  }

  function selectedBundleSummary(bundle: MethodBundle) {
    const count = bundleRunCount(bundle, methodRunSpecs, selectedMethodIds);
    if (!count) return "未勾选";
    if (count === bundle.methods.length) return `已选全部 ${count} 项`;
    return `已选 ${count} / ${bundle.methods.length} 项`;
  }

  function renderMethodCard(method: MethodCatalogItem, scope = "method-card", index = 0) {
    const copy = methodDisplayCopy(method);
    const active = selectedMethodId === method.id;
    const selected = selectedMethodIds.has(method.id);
    const recommended = recommendedIds.has(method.id);
    const methodBlockedReason = methodRunBlockReason(method, dataset);
    const methodBlocked = Boolean(methodBlockedReason);
    const controls = methodBindingControls(method);
    const showTargetControl = controls.has("target") || controls.has("field");
    const showPairControls = controls.has("x") || controls.has("y");
    const showGroupControl = controls.has("group");
    const showLabelControl = controls.has("label") || controls.has("entity") || controls.has("object_selection");
    const showTimeControl = controls.has("time");
    const showFeaturePicker = controls.has("features") || controls.has("x") || controls.has("y");
    const showDerivedPicker = controls.has("derived_metrics");
    const showObjectBlock = controls.has("object_selection") || controls.has("entity") || controls.has("label");
    const preferObjectMode = methodRecommendedSelectionMode(method) === "object";
    const smartPlan = makeSmartMethodBindingPlan(method, fieldSelection, dataset, derivedMetricEdits);
    const defaultBinding = smartPlan.binding;
    const activeRun = activeRunForMethod(method.id);
    const currentBinding = cleanMethodFieldBinding({
      ...defaultBinding,
      ...(method.field_bindings || {}),
      ...(methodFieldBindings[method.id] || {}),
      ...(activeRun?.field_bindings || {}),
    });
    const currentPlan: SmartMethodBindingPlan = {
      ...smartPlan,
      binding: currentBinding,
      roles: uniqueStrings(["x", "y", "target", "field", "features", "group", "label", "entity", "time", "derived_metrics"])
        .map((key) => {
          const typedKey = key as keyof MethodFieldBinding;
          const value = bindingRoleValue(currentBinding, typedKey);
          const inferredRole = smartPlan.roles.find((role) => role.key === typedKey);
          return value
            ? {
                key: typedKey,
                label: inferredRole?.label || key.replace("_", " "),
                value,
                confidence: inferredRole?.confidence || ("medium" as const),
              }
            : null;
        })
        .filter((role): role is SmartMethodBindingRole => Boolean(role)),
    };
    const derivedOptions = methodBindingOptions(dataset, derivedMetricEdits);
    const allFieldOptions = columnNames(dataset);
    const numericOptions = methodBindingOptions(dataset, derivedMetricEdits);
    const targetOptions = uniqueStrings([...allFieldOptions, ...derivedOptions]);
    const groupOptions = uniqueStrings([...(dataset?.categorical_columns || []), ...allFieldOptions]);
    const timeOptions = uniqueStrings([...(dataset?.datetime_columns || []), ...allFieldOptions]);
    const methodRuns = runsForMethod(method.id);
    const methodRunCount = methodRuns.length;
    const methodSaveBusy = methodCardSaveBusyId === method.id || Boolean(activeRun?.run_id && methodCardSaveBusyId === activeRun.run_id);
    const editCapabilities = method.edit_capabilities;
    const freedomScore = Number(editCapabilities?.freedom_score || 0);
    const visibleEditableFields = uniqueStrings(editCapabilities?.editable_field_labels || Array.from(controls)).slice(0, 10);
    const visibleSelectionModes = (editCapabilities?.selection_mode_labels || []).slice(0, 4);
    const visibleRunControls = uniqueStrings(editCapabilities?.run_control_labels || []).slice(0, 6);
    const usageGuidance = copy.usageGuidance.slice(0, 5);
    const reportValueHooks = copy.reportValueHooks.slice(0, 5);
    const selectedDerivedMetrics = uniqueStrings([
      ...(Array.isArray(currentBinding.derived_metrics) ? currentBinding.derived_metrics : []),
      ...(currentBinding.derived_metric ? [currentBinding.derived_metric] : []),
    ]);
    const runCount = methodRunCountById(methodRunSpecs, method.id);
    const currentObjectSelection =
      activeRun?.object_selection ||
      ({
        object_type: currentBinding.entity || currentBinding.label || fieldSelection.label || fieldSelection.group || "对象",
        merge_mode: "smart",
        object_keys: [],
        group_key: currentBinding.group || fieldSelection.group || "",
        label_key: currentBinding.label || currentBinding.entity || fieldSelection.label || "",
        selection_source: "fields",
      } as NonNullable<MethodRunSpec["object_selection"]>);

    const objectSelectionLabelKey = currentObjectSelection.label_key || currentBinding.label || currentBinding.entity || fieldSelection.label || fieldSelection.group || "";
    const objectCandidateValues = objectCandidateCache.get(objectSelectionLabelKey) || [];
    const showObjectEditor = showObjectBlock || activeRun?.selection_mode === "object";
    const objectFieldOptions = uniqueStrings([
      currentBinding.entity || "",
      currentBinding.label || "",
      fieldSelection.label || "",
      fieldSelection.group || "",
      ...allFieldOptions,
    ]);
    const objectSelectionValues = currentObjectSelection.filter_values || currentObjectSelection.object_keys || [];
    const currentStatisticalOptions = cleanMethodStatisticalOptions({
      ...(method.statistical_options || {}),
      ...(activeRun?.statistical_options || {}),
    });
    const showStatisticalOptions = method.source === "statistical_catalog" || Boolean(Object.keys(currentStatisticalOptions).length);

    function updateBinding(patch: Partial<MethodFieldBinding>) {
      const nextBinding = cleanMethodFieldBinding({ ...defaultBinding, ...currentBinding, ...patch });
      if (activeRun) {
        updateRunGroup(activeRun, { field_bindings: nextBinding, selection_mode: "fields" });
      } else {
        syncMethodRunBinding(method.id, nextBinding);
      }
    }
    function resetBinding() {
      if (activeRun) {
        updateRunGroup(activeRun, {
          field_bindings: cleanMethodFieldBinding(defaultBinding),
          selection_mode: "fields",
          object_selection: null,
          smart_merge_group: null,
        });
        return;
      }
      setMethodFieldBindings((current) => {
        const next = { ...current };
        delete next[method.id];
        return next;
      });
    }
    function updateStatisticalOptions(patch: MethodStatisticalOptions) {
      const nextOptions = cleanMethodStatisticalOptions({ ...currentStatisticalOptions, ...patch });
      if (activeRun) {
        updateRunGroup(activeRun, { statistical_options: nextOptions });
      } else {
        appendMethodRun(method.id, { statistical_options: nextOptions });
      }
    }
    function applySmartBindingToActiveRun() {
      const nextBinding = cleanMethodFieldBinding(defaultBinding);
      if (activeRun) {
        updateRunGroup(activeRun, {
          field_bindings: nextBinding,
          selection_mode: preferObjectMode ? "object" : "fields",
          object_selection: preferObjectMode
            ? {
                object_type: method.role_labels?.[0] || currentBindingLabelFallback(nextBinding, fieldSelection),
                merge_mode: "smart",
                object_keys: activeRun.object_selection?.object_keys || [],
                group_key: nextBinding.group || fieldSelection.group || "",
                label_key: nextBinding.label || nextBinding.entity || fieldSelection.label || "",
                selection_source: "fields",
              }
            : null,
          smart_merge_group: nextBinding.group || null,
        });
        return;
      }
      syncMethodRunBinding(method.id, nextBinding);
    }
  function updateCurrentObjectSelection(patch: Partial<NonNullable<MethodRunSpec["object_selection"]>>) {
    if (!activeRun) return;
    const nextObjectSelection = {
      ...currentObjectSelection,
      ...patch,
      selection_source: patch.selection_source || currentObjectSelection.selection_source || "point_pick",
      filter_field:
        (patch.filter_field !== undefined
          ? patch.filter_field
          : currentObjectSelection.filter_field || patch.label_key || patch.group_key || currentObjectSelection.label_key || currentObjectSelection.group_key || "") || "",
      filter_values: uniqueStrings(
        patch.filter_values ||
          patch.object_keys ||
          currentObjectSelection.filter_values ||
          currentObjectSelection.object_keys ||
          [],
      ),
      object_keys: uniqueStrings(patch.object_keys || currentObjectSelection.object_keys || []),
    };
    updateRunGroup(activeRun, {
      selection_mode: "object",
      object_selection: nextObjectSelection,
      smart_merge_group:
        typeof patch.group_key === "string"
          ? patch.group_key
            : activeRun.smart_merge_group || currentObjectSelection.group_key || "",
      });
    }
    function toggleCurrentObjectKey(objectKey: string) {
      if (!activeRun) return;
      const nextKeys = currentObjectSelection.object_keys?.includes(objectKey)
        ? (currentObjectSelection.object_keys || []).filter((item) => item !== objectKey)
        : uniqueStrings([...(currentObjectSelection.object_keys || []), objectKey]).slice(0, 24);
      updateCurrentObjectSelection({ object_keys: nextKeys, filter_values: nextKeys });
    }
    function updateObjectValuesText(value: string) {
      if (!activeRun) return;
      const nextValues = uniqueStrings(
        value
          .split(/[\n,，]/)
          .map((item) => item.trim())
          .filter(Boolean),
      ).slice(0, 24);
      updateCurrentObjectSelection({ object_keys: nextValues, filter_values: nextValues });
    }
    function setMethodRunSelectionMode(run: MethodRunSpec, selectionMode: MethodRunSelectionMode) {
      const nextFieldBindings =
        selectionMode === "all_rows"
          ? cleanMethodFieldBinding({ ...defaultBinding, ...currentBinding, dataset_scope: "all_rows" })
          : cleanMethodFieldBinding({ ...defaultBinding, ...currentBinding });
      updateRunGroup(run,
        {
        selection_mode: selectionMode,
        field_bindings: nextFieldBindings,
        object_selection:
          selectionMode === "object"
            ? {
                ...currentObjectSelection,
                object_type: currentObjectSelection.object_type || currentBinding.entity || currentBinding.label || fieldSelection.label || fieldSelection.group || "对象",
                merge_mode: currentObjectSelection.merge_mode || "smart",
                object_keys: uniqueStrings(currentObjectSelection.object_keys || []),
                group_key: currentObjectSelection.group_key || currentBinding.group || fieldSelection.group || "",
                label_key: currentObjectSelection.label_key || currentBinding.label || currentBinding.entity || fieldSelection.label || "",
                selection_source: currentObjectSelection.selection_source || "point_pick",
              }
            : null,
        smart_merge_group:
          selectionMode === "object"
            ? currentObjectSelection.group_key || currentBinding.group || fieldSelection.group || ""
            : selectionMode === "all_rows"
              ? run.smart_merge_group || currentObjectSelection.group_key || currentBinding.group || fieldSelection.group || ""
              : null,
        },
      );
    }
    function openMethodFromCard() {
      if (methodRuns.length) {
        const targetRun = activeRun || methodRuns[0];
        if (targetRun) {
          focusMethodRun(method.id, targetRun.run_id);
          return;
        }
      }
      openMethodEditor(method.id);
    }

    function renderObjectSelectionPanel() {
      if (!showObjectEditor) return null;
      return (
        <div className="mt-4 rounded-[18px] border border-cyan-200/15 bg-cyan-400/6 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">重点对象筛选</p>
              <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                对象用于锁定分析范围，再查看对应对象的指标和结构。适合聚焦基金会、门店、客户、地区或项目的表现。
              </p>
            </div>
            <span className="surface-chip">
              {objectSelectionValues.length ? `已选 ${formatNumber(objectSelectionValues.length)}` : activeRun ? "待选对象" : "待创建实例"}
            </span>
          </div>
          <button
            className="surface-chip mt-3"
            onClick={(event) => {
              event.stopPropagation();
              openMethodGuide("object");
            }}
            type="button"
          >
            查看对象选择新手教程
          </button>
          {!activeRun ? (
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-[14px] border border-white/10 bg-black/18 p-3 text-xs text-[var(--muted)]">
              <span>当前还没有可编辑的运行实例。点击下面按钮后，就可以直接输入对象字段和值。</span>
              <button className="surface-chip" onClick={() => appendMethodRun(method.id, { selection_mode: "object" })} type="button">
                添加对象实例
              </button>
            </div>
          ) : (
            <>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <SearchableFieldSelect
                  help="选一列用来识别“谁”。例如基金会名称、客户名称、门店名称、SKU。"
                  label="对象所在列"
                  onChange={(value) =>
                    updateCurrentObjectSelection({
                      object_type: value,
                      label_key: value,
                      filter_field: value,
                      selection_source: "fields",
                    })
                  }
                  options={objectFieldOptions}
                  value={currentObjectSelection.object_type || ""}
                />
                <SearchableFieldSelect
                  help="选一列用来拆分对象表现。例如服务领域、地区、年度、渠道。"
                  label="按什么分组比较"
                  onChange={(value) => updateCurrentObjectSelection({ group_key: value })}
                  options={allFieldOptions}
                  value={currentObjectSelection.group_key || ""}
                />
                <SearchableFieldSelect
                  help="通常与对象所在列一致；对象名称与筛选列不同，可在这里调整。"
                  label="对象值来自哪一列"
                  onChange={(value) =>
                    updateCurrentObjectSelection({
                      label_key: value,
                      filter_field: value,
                      selection_source: "fields",
                    })
                  }
                  options={allFieldOptions}
                  value={currentObjectSelection.label_key || ""}
                />
                <FieldSelect
                  help="智能模式会沿用推荐口径；手动模式严格按你输入的对象值筛选。"
                  label="对象匹配方式"
                  onChange={(value) =>
                    updateCurrentObjectSelection({
                      merge_mode: value === "manual" ? "manual" : "smart",
                    })
                  }
                  options={["smart", "manual"]}
                  value={currentObjectSelection.merge_mode || "smart"}
                />
                <label className="space-y-2 md:col-span-2">
                  <span className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">要分析的对象值</span>
                  <span className="block text-[11px] leading-5 text-[var(--muted)]">
                    填具体对象名称，多个值用逗号分隔；也可以从下面样本值按钮直接点选。
                  </span>
                  <input
                    className="field-input"
                    onChange={(event) => updateObjectValuesText(event.target.value)}
                    placeholder="例如：北京某某基金会, 上海某某基金会"
                    value={objectSelectionValues.join(", ")}
                  />
                </label>
              </div>
              <p className="mt-2 text-xs leading-6 text-[var(--muted)]">
                业务含义：对象所在列 = 对象值。比如“基金会名称 = 某某基金会”，就是筛出这家基金会的全部记录。
              </p>
              <p className="mt-2 text-xs leading-6 text-[var(--muted)]">
                当前对象筛选会同步到运行实例；切换到别的运行实例时，这里也会跟着刷新。
              </p>
              <div className="mt-2 rounded-[14px] border border-white/10 bg-black/18 px-3 py-2 text-xs text-[var(--muted)]">
                当前对象筛选：{" "}
                <span className="text-[var(--text-strong)]">
                  {(currentObjectSelection.filter_field || currentObjectSelection.label_key || currentObjectSelection.object_type || "未设置字段")}
                  {" = "}
                  {objectSelectionValues.length ? objectSelectionValues.join("、") : "未设置对象值"}
                </span>
                {" · "}
                {currentObjectSelection.merge_mode === "manual" ? "手动对象全集匹配" : "方法需要对象时默认显式展示"}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  className="surface-chip"
                  onClick={() =>
                    updateCurrentObjectSelection({
                      merge_mode: "smart",
                      object_keys: currentObjectSelection.object_keys || [],
                      filter_values: currentObjectSelection.object_keys || [],
                    })
                  }
                  type="button"
                >
                  智能匹配对象
                </button>
                <button
                  className="surface-chip"
                  onClick={() =>
                    updateCurrentObjectSelection({
                      merge_mode: "manual",
                      filter_values: currentObjectSelection.object_keys || [],
                    })
                  }
                  type="button"
                >
                  严格按输入筛选
                </button>
                <button className="surface-chip" onClick={() => updateCurrentObjectSelection({ object_keys: [], filter_values: [] })} type="button">
                  清空对象
                </button>
              </div>
              <div className="mt-3 flex max-h-[140px] flex-wrap gap-2 overflow-auto rounded-[16px] border border-white/10 bg-black/18 p-2">
                {objectCandidateValues.length ? (
                  objectCandidateValues.map((objectKey) => {
                    const activeObject = currentObjectSelection.object_keys?.includes(objectKey);
                    return (
                      <button
                        aria-pressed={activeObject}
                        className={`rounded-full border px-2.5 py-1 text-[11px] transition ${
                          activeObject
                            ? "border-[#74d0d9]/55 bg-[#74d0d9]/14 text-[var(--text-strong)]"
                            : "border-white/10 bg-white/5 text-[var(--muted)] hover:bg-white/10"
                        }`}
                        key={`${method.id}-object-top-${objectKey}`}
                        onClick={() => toggleCurrentObjectKey(objectKey)}
                        type="button"
                      >
                        {objectKey}
                      </button>
                    );
                  })
                ) : (
                  <span className="text-xs text-[var(--muted)]">先选对象字段，再从当前表格样本值里选择具体对象值。</span>
                )}
              </div>
            </>
          )}
        </div>
      );
    }

    return (
      <article
        className={`lab-method-card rounded-[20px] border p-4 text-left transition ${
          methodBlocked
            ? "border-amber-200/18 bg-[linear-gradient(135deg,rgba(255,190,118,0.08),rgba(0,0,0,0.18))] text-[var(--muted)]"
            : active
            ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
            : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
        }`}
        key={methodRenderKey(method, scope, index)}
        onClick={() => openMethodFromCard()}
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <button className="block min-w-0 flex-1 text-left" onClick={() => openMethodEditor(method.id)} type="button">
            <span className="block text-[10px] uppercase tracking-[0.24em] text-[var(--muted)]">{copy.family}</span>
            <span className="mt-1 block text-sm font-semibold text-[var(--text-strong)]">{methodDisplayTitle(method)}</span>
            <span className="mt-2 block text-xs leading-6 text-[var(--muted)]">{copy.descriptionLine}</span>
          </button>
          <div className="flex flex-col items-end gap-2">
            <button
              className="surface-chip"
              onClick={() => openMethodEditor(method.id)}
              type="button"
            >
              编辑当前方法
            </button>
            <button
              aria-label={`Add another run for ${methodDisplayTitle(method)}`}
              className="lab-icon-button h-9 w-9 text-[var(--text-strong)]"
              onClick={() => appendMethodRun(method.id)}
              title={methodBlocked ? `先加入执行篮；${methodBlockedReason}` : "Add this method again"}
              type="button"
            >
              <Plus size={16} />
            </button>
            <span className="surface-chip">{copy.status}</span>
            {runCount ? <span className="surface-chip">{runCount} run</span> : null}
            {recommended ? <span className="surface-chip border-[#74d0d9]/40 bg-[#74d0d9]/10 text-[var(--text-strong)]">推荐</span> : null}
            {methodBlocked ? <UnavailableBadge reason={methodBlockedReason} /> : null}
          </div>
        </div>
        <p className="mt-3 text-xs leading-6 text-[var(--muted)]">{copy.businessLine}</p>
        <p className="mt-2 text-xs leading-6 text-[var(--muted)]">{copy.cliLine}</p>
        <p className="mt-2 text-[11px] leading-5 text-[var(--muted)]">{copy.actionLine}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {(copy.tags.length ? copy.tags : [...methodOutputLabels(method), ...methodRoleLabels(method)]).slice(0, 10).map((label) => (
            <span className="surface-chip" key={`${method.id}-${label}`}>
              {label}
            </span>
          ))}
        </div>
        {copy.sections.length ? (
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {copy.sections.map((section) => (
              <div className="rounded-[16px] border border-white/10 bg-white/5 p-3" key={`${method.id}-${section.kind}-${section.label}`}>
                <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">{section.label}</p>
                <p className="mt-1 text-xs font-medium text-[var(--text-strong)]">{section.value}</p>
                {section.help ? <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">{section.help}</p> : null}
              </div>
            ))}
          </div>
        ) : null}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] text-[var(--muted)]">
            <input checked={selected} onChange={() => toggleMethod(method.id)} type="checkbox" />
            <span className="text-[11px]">纳入执行 + 合并</span>
          </label>
          <button className="surface-chip" onClick={() => appendMethodRun(method.id)} title={methodBlocked ? `先规划这张卡；${methodBlockedReason}` : undefined} type="button">
            <Plus size={13} />
            <span className="text-[11px]">再加一次运行</span>
          </button>
          <button className={`surface-chip ${methodBlocked ? "cursor-not-allowed opacity-60" : ""}`} disabled={methodBlocked} onClick={() => void runSingleMethod(method)} title={methodBlocked ? methodBlockedReason : undefined} type="button">
            <Sparkles size={13} />
            <span className="text-[11px]">单独执行</span>
          </button>
          <button
            className={`surface-chip ${methodSaveBusy ? "cursor-wait opacity-70" : ""}`}
            disabled={methodSaveBusy}
            onClick={() => void saveCurrentMethodCard(method, activeRun)}
            title="把当前字段绑定、运行模式和使用指导保存为 Lab 可复用方法卡"
            type="button"
          >
            {methodSaveBusy ? <LoaderCircle className="animate-spin" size={13} /> : <PackageOpen size={13} />}
            <span className="text-[11px]">{methodSaveBusy ? "保存中" : "保存为方法卡"}</span>
          </button>
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.22em]">
            {method.status} / {method.source}
          </span>
          {method.source === "statistical_visual_catalog" && method.allowed_domain === "non_financial" ? (
            <span className="rounded-full border border-[#9ec69f]/30 bg-[#9ec69f]/10 px-2 py-1 text-[10px] uppercase tracking-[0.22em] text-[#d8f5d4]">
              non-financial visual
            </span>
          ) : null}
        </div>
        {methodBlocked ? (
          <BlockedReasonPanel reason={methodBlockedReason} />
        ) : null}
        {(visibleEditableFields.length || visibleSelectionModes.length || visibleRunControls.length || usageGuidance.length || reportValueHooks.length) ? (
          <div className="mt-4 rounded-[18px] border border-[#f0d58c]/20 bg-[linear-gradient(135deg,rgba(240,213,140,0.10),rgba(7,17,19,0.58))] p-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] uppercase tracking-[0.22em] text-[#f0d58c]/80">方法卡自由度</p>
                <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                  后端目录已声明这张卡可编辑什么、如何运行、以及怎样进入高价值报告证据链。
                </p>
              </div>
              {freedomScore ? (
                <span className="rounded-full border border-[#f0d58c]/35 bg-[#f0d58c]/12 px-3 py-1 text-[11px] text-[var(--text-strong)]">
                  自由度 {freedomScore}
                </span>
              ) : null}
            </div>
            <div className="mt-3 grid gap-3 lg:grid-cols-3">
              <div className="rounded-[14px] border border-white/10 bg-black/18 p-3">
                <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">可编辑项</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {visibleEditableFields.length ? (
                    visibleEditableFields.map((label) => (
                      <span className="surface-chip" key={`${method.id}-editable-${label}`}>
                        {label}
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px] text-[var(--muted)]">沿用智能默认绑定</span>
                  )}
                </div>
              </div>
              <div className="rounded-[14px] border border-white/10 bg-black/18 p-3">
                <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">运行模式</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {visibleSelectionModes.map((mode) => (
                    <button
                      className={`surface-chip ${mode.recommended ? "border-[#f0d58c]/35 bg-[#f0d58c]/12 text-[var(--text-strong)]" : ""}`}
                      key={`${method.id}-mode-${mode.mode}`}
                      onClick={() => (activeRun ? setMethodRunSelectionMode(activeRun, mode.mode) : appendMethodRun(method.id, { selection_mode: mode.mode }))}
                      type="button"
                    >
                      {mode.label}{mode.recommended ? " · 推荐" : ""}
                    </button>
                  ))}
                </div>
              </div>
              <div className="rounded-[14px] border border-white/10 bg-black/18 p-3">
                <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">可用操作</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {visibleRunControls.length ? (
                    visibleRunControls.map((label) => (
                      <span className="surface-chip" key={`${method.id}-run-control-${label}`}>
                        {label}
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px] text-[var(--muted)]">追加、执行、合并</span>
                  )}
                </div>
              </div>
            </div>
            {usageGuidance.length ? (
              <div className="mt-3 grid gap-2 md:grid-cols-3">
                {usageGuidance.map((item) => (
                  <div className="rounded-[14px] border border-white/10 bg-white/5 p-3" key={`${method.id}-usage-${item.title}`}>
                    <p className="text-[11px] font-medium text-[var(--text-strong)]">{item.title}</p>
                    <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">{item.detail}</p>
                  </div>
                ))}
              </div>
            ) : null}
            {reportValueHooks.length ? (
              <div className="mt-3 rounded-[14px] border border-[#74d0d9]/20 bg-[#74d0d9]/7 p-3">
                <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">高价值报告钩子</p>
                <div className="mt-2 grid gap-1">
                  {reportValueHooks.map((hook) => (
                    <p className="text-[11px] leading-5 text-[var(--muted)]" key={`${method.id}-report-hook-${hook}`}>
                      {hook}
                    </p>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
        {renderObjectSelectionPanel()}
        {showStatisticalOptions ? (
          <div className="mt-4 rounded-[18px] border border-[#74d0d9]/20 bg-[linear-gradient(135deg,rgba(116,208,217,0.10),rgba(0,0,0,0.22))] p-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] uppercase tracking-[0.22em] text-[#74d0d9]/80">统计运行参数</p>
                <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                  这些选项会随运行实例和保存方法卡一起进入后端统计引擎，适合调显著性、假设方向、聚类数和实验指标口径。
                </p>
              </div>
              <span className="surface-chip">{activeRun ? "写入当前实例" : "编辑会先创建实例"}</span>
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                显著性 alpha
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={0.2}
                  min={0.0001}
                  onChange={(event) => updateStatisticalOptions({ alpha: Number(event.target.value) })}
                  step={0.01}
                  type="number"
                  value={currentStatisticalOptions.alpha ?? 0.05}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                假设方向
                <ThemedSelect
                  className="theme-select theme-select-compact"
                  onChange={(event) => updateStatisticalOptions({ hypothesis: event.target.value as MethodStatisticalOptions["hypothesis"] })}
                  value={currentStatisticalOptions.hypothesis || "two-sided"}
                >
                  <option value="two-sided">双侧检验</option>
                  <option value="larger">A 更大 / 正向</option>
                  <option value="smaller">A 更小 / 反向</option>
                </ThemedSelect>
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                指标类型
                <ThemedSelect
                  className="theme-select theme-select-compact"
                  onChange={(event) => updateStatisticalOptions({ metric_type: event.target.value as MethodStatisticalOptions["metric_type"] })}
                  value={currentStatisticalOptions.metric_type || "auto"}
                >
                  <option value="auto">自动识别</option>
                  <option value="continuous">连续指标</option>
                  <option value="binary">二元成功率</option>
                </ThemedSelect>
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                PCA 维度
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={12}
                  min={1}
                  onChange={(event) => updateStatisticalOptions({ components: Number(event.target.value) })}
                  step={1}
                  type="number"
                  value={currentStatisticalOptions.components ?? 2}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                聚类数 K
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={12}
                  min={2}
                  onChange={(event) => updateStatisticalOptions({ clusters: Number(event.target.value) })}
                  step={1}
                  type="number"
                  value={currentStatisticalOptions.clusters ?? 3}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                Time window
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={90}
                  min={2}
                  onChange={(event) => updateStatisticalOptions({ window: Number(event.target.value) })}
                  step={1}
                  type="number"
                  value={currentStatisticalOptions.window ?? 3}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                Lag count
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={120}
                  min={1}
                  onChange={(event) => updateStatisticalOptions({ lag: Number(event.target.value) })}
                  step={1}
                  type="number"
                  value={currentStatisticalOptions.lag ?? 12}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                Regularization
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={100}
                  min={0.0001}
                  onChange={(event) => updateStatisticalOptions({ regularization_strength: Number(event.target.value) })}
                  step={0.1}
                  type="number"
                  value={currentStatisticalOptions.regularization_strength ?? 1}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                L1 ratio
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={1}
                  min={0}
                  onChange={(event) => updateStatisticalOptions({ l1_ratio: Number(event.target.value) })}
                  step={0.05}
                  type="number"
                  value={currentStatisticalOptions.l1_ratio ?? 0.5}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                Quantile
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={0.95}
                  min={0.05}
                  onChange={(event) => updateStatisticalOptions({ quantile: Number(event.target.value) })}
                  step={0.05}
                  type="number"
                  value={currentStatisticalOptions.quantile ?? 0.5}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                Bootstrap iterations
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  max={10000}
                  min={100}
                  onChange={(event) => updateStatisticalOptions({ bootstrap_iterations: Number(event.target.value) })}
                  step={100}
                  type="number"
                  value={currentStatisticalOptions.bootstrap_iterations ?? 1000}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                成功值 / 转化值
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  onChange={(event) => updateStatisticalOptions({ success_value: event.target.value })}
                  placeholder="例如 yes / 1 / paid"
                  type="text"
                  value={currentStatisticalOptions.success_value || ""}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                检验值 / 理论均值
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  onChange={(event) => updateStatisticalOptions({ test_value: Number(event.target.value) })}
                  step={0.01}
                  type="number"
                  value={currentStatisticalOptions.test_value ?? 0}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                总体标准差
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  min={0}
                  onChange={(event) => updateStatisticalOptions({ population_std: Number(event.target.value) || undefined })}
                  placeholder="可选，Z 检验优先使用"
                  step={0.01}
                  type="number"
                  value={currentStatisticalOptions.population_std ?? ""}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                A 组 / 对照组
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  onChange={(event) => updateStatisticalOptions({ group_a: event.target.value })}
                  placeholder="例如 control / baseline"
                  type="text"
                  value={currentStatisticalOptions.group_a || ""}
                />
              </label>
              <label className="grid gap-1 text-[11px] text-[var(--muted)]">
                B 组 / 实验组
                <input
                  className="rounded-[12px] border border-white/10 bg-black/24 px-3 py-2 text-xs text-[var(--text-strong)] outline-none focus:border-[#74d0d9]/45"
                  onChange={(event) => updateStatisticalOptions({ group_b: event.target.value })}
                  placeholder="例如 treatment / new"
                  type="text"
                  value={currentStatisticalOptions.group_b || ""}
                />
              </label>
            </div>
          </div>
        ) : null}
        <div className="mt-4 rounded-[18px] border border-white/10 bg-black/18 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">字段角色绑定</p>
              <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                在这里为当前方法指定结果列、解释因素列、分组列和对象标记列。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className={`surface-chip ${currentPlan.missing.length ? "border-amber-300/35 bg-amber-300/10" : "border-[#74d0d9]/40 bg-[#74d0d9]/10"}`}>
                智能字段建议 {currentPlan.confidence}%
              </span>
              <button className="surface-chip" onClick={applySmartBindingToActiveRun} type="button">
                重新智能匹配
              </button>
              <button className="surface-chip" onClick={resetBinding} type="button">
                回到默认
              </button>
              <button
                className="surface-chip"
                onClick={(event) => {
                  event.stopPropagation();
                  openMethodGuide("fields");
                }}
                type="button"
              >
                查看字段绑定新手教程
              </button>
            </div>
          </div>
          <div className="mt-3 rounded-[16px] border border-[#74d0d9]/18 bg-[#74d0d9]/7 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="surface-chip border-[#74d0d9]/35 bg-[#74d0d9]/10">AI 建议口径</span>
              {activeRun?.bundle_run_id ? <span className="surface-chip border-[#f0d58c]/35 bg-[#f0d58c]/12">同组子方法共享字段</span> : null}
              <span className="text-xs leading-5 text-[var(--muted)]">{smartMethodBindingSummary(currentPlan)}</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {currentPlan.roles.slice(0, 10).map((role) => (
                <span
                  className={`rounded-full border px-2.5 py-1 text-[11px] ${
                    role.confidence === "high"
                      ? "border-[#74d0d9]/45 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                      : role.confidence === "medium"
                        ? "border-white/12 bg-white/6 text-[var(--muted)]"
                        : "border-amber-300/35 bg-amber-300/10 text-[var(--muted)]"
                  }`}
                  key={`${method.id}-smart-role-${role.key}`}
                >
                  {role.label}: {role.value}
                </span>
              ))}
              {currentPlan.missing.map((missingRole) => (
                <span className="rounded-full border border-amber-300/35 bg-amber-300/10 px-2.5 py-1 text-[11px] text-[var(--muted)]" key={`${method.id}-missing-${missingRole}`}>
                  缺少：{fieldBindingRoleLabel(missingRole, preferObjectMode)}
                </span>
              ))}
            </div>
            <p className="mt-2 text-[11px] leading-5 text-[var(--muted)]">
              {activeRun?.bundle_run_id
                ? "这组统一方法会共用同一套字段、对象和统计参数；如果要换另一套字段或对象，请回到统一方法卡点击“再次加入整组”。"
                : currentPlan.reasons.join(" · ") || "系统会综合方法角色、输出类型、字段画像和全局字段偏好生成默认口径。"}
            </p>
          </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {showTargetControl ? (
              <SearchableFieldSelect
                help={preferObjectMode ? "对象模式下要衡量的业务结果，例如项目收入、项目支出、评分。" : "方法要解释或统计的核心结果列，例如收入、支出、得分、数量。"}
                label={preferObjectMode ? "对象要分析的指标" : controls.has("field") ? "单字段指标" : "结果指标"}
                onChange={(value) => updateBinding({ target: value, field: controls.has("field") ? value || undefined : currentBinding.field })}
                options={targetOptions}
                value={currentBinding.target || currentBinding.field || ""}
              />
            ) : null}
            {showPairControls ? (
              <SearchableFieldSelect
                help="用于字段对、散点图、相关或对比方法的第一列；图表里通常是横轴。"
                label="横轴 / 对比字段"
                onChange={(value) => updateBinding({ x: value })}
                options={numericOptions.length ? numericOptions : allFieldOptions}
                value={currentBinding.x || ""}
              />
            ) : null}
            {showPairControls ? (
              <SearchableFieldSelect
                help="用于字段对、散点图、相关或对比方法的第二列；图表里通常是纵轴，也会作为结果指标。"
                label="纵轴 / 结果字段"
                onChange={(value) => updateBinding({ y: value, target: value || currentBinding.target })}
                options={numericOptions.length ? numericOptions : allFieldOptions}
                value={currentBinding.y || ""}
              />
            ) : null}
            {showGroupControl ? (
              <SearchableFieldSelect
                help="用来把结果拆开比较，例如服务领域、地区、渠道、年度、客户类型。"
                label={preferObjectMode ? "对象分组口径" : "分组口径"}
                onChange={(value) => updateBinding({ group: value })}
                options={groupOptions}
                value={currentBinding.group || ""}
              />
            ) : null}
            {showLabelControl ? (
              <SearchableFieldSelect
                help="用来在图表、对象筛选和报告里显示“是谁”，例如基金会名称、项目名称、客户名称。"
                label={preferObjectMode ? "对象名称列" : "名称/标签列"}
                onChange={(value) => updateBinding({ label: value, entity: value })}
                options={allFieldOptions}
                value={currentBinding.label || currentBinding.entity || ""}
              />
            ) : null}
            {showTimeControl ? (
              <SearchableFieldSelect
                help="用于趋势、时间窗口、滞后或年度/月度对比，例如年度、日期、月份。"
                label="时间口径"
                onChange={(value) => updateBinding({ time: value })}
                options={timeOptions}
                value={currentBinding.time || ""}
              />
            ) : null}
          </div>
          <div className="mt-3 rounded-[16px] border border-white/10 bg-white/5 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">运行实例</p>
                <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">
                  一个实例就是同一方法的一种独立跑法，可用不同字段、对象或全数据口径分别运行。
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  className="surface-chip"
                  onClick={(event) => {
                    event.stopPropagation();
                    openMethodGuide("runs");
                  }}
                  type="button"
                >
                  查看运行实例教程
                </button>
                <button className="surface-chip" onClick={() => appendMethodRun(method.id)} type="button">
                  追加一种跑法
                </button>
              </div>
            </div>
            <div className="mt-3 grid gap-2">
              {methodRuns.map((run, runIndex) => {
                const isActiveRun = activeRun?.run_id === run.run_id;
                return (
                  <div
                    className={`rounded-[14px] border p-3 ${isActiveRun ? "border-[#74d0d9]/55 bg-[#74d0d9]/10" : "border-white/10 bg-black/18"}`}
                    key={run.run_id}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <button className="text-left" onClick={() => focusMethodRun(method.id, run.run_id)} type="button">
                        <span className="block text-xs font-medium text-[var(--text-strong)]">{run.label || `实例 ${runIndex + 1}`}</span>
                        <span className="mt-1 block text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">
                          {run.selection_mode === "all_rows" ? "全数据口径" : run.selection_mode === "object" ? "重点对象口径" : "字段绑定口径"}
                        </span>
                      </button>
                      <div className="flex flex-wrap gap-2">
                        <button className="surface-chip" onClick={() => setMethodRunSelectionMode(run, "fields")} type="button">
                          字段绑定
                        </button>
                        <button className="surface-chip" onClick={() => setMethodRunSelectionMode(run, "all_rows")} type="button">
                          全数据口径
                        </button>
                        <button className="surface-chip" onClick={() => setMethodRunSelectionMode(run, "object")} type="button">
                          重点对象
                        </button>
                        <button className="surface-chip border-red-300/25 bg-red-500/8 text-red-100" onClick={() => removeMethodRun(run.run_id)} type="button">
                          删除这个跑法
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
              {!methodRuns.length ? <p className="text-xs text-[var(--muted)]">当前方法还没有运行实例，先点“再加一次运行”。</p> : null}
            </div>
          </div>
          {showFeaturePicker ? (
            <FieldChipPicker
              help={
                <span>
                  这些列会作为解释变量、建模输入或辅助证据。
                  <button
                    className="ml-2 underline decoration-dotted underline-offset-4"
                    onClick={(event) => {
                      event.stopPropagation();
                      openMethodGuide("features");
                    }}
                    type="button"
                  >
                    查看新手教程
                  </button>
                </span>
              }
              label="解释/建模输入字段"
              onToggle={(column) =>
                updateBinding({
                  features: (currentBinding.features || []).includes(column)
                    ? (currentBinding.features || []).filter((item) => item !== column)
                    : uniqueStrings([...(currentBinding.features || []), column]).slice(0, 6),
                })
              }
              options={columnNames(dataset)}
              selectedValues={currentBinding.features || []}
              searchPlaceholder="搜索解释字段 · 例如支出、年度、规模、比例"
            />
          ) : null}
          {showDerivedPicker ? (
            <FieldChipPicker
              emptyMessage="自动建议"
              help="派生指标是系统按原始字段算出的新口径，例如标准化、百分位、差值、占比。"
              label="可选派生指标"
              onToggle={(field) => {
                const activeMetric = selectedDerivedMetrics.includes(field);
                const next = activeMetric
                  ? selectedDerivedMetrics.filter((item) => item !== field)
                  : uniqueStrings([...selectedDerivedMetrics, field]).slice(0, 6);
                updateBinding({
                  derived_metrics: next,
                  derived_metric: next[0] || "",
                });
              }}
              options={derivedOptions}
              selectedValues={selectedDerivedMetrics}
              searchPlaceholder="搜索派生指标 · 例如标准化、百分位、占比"
              tone="warm"
            />
          ) : null}
        </div>
      </article>
    );
  }

  function renderBundleCard(bundle: MethodBundle, scope = "bundle-card", index = 0) {
    const active = bundle.methods.some((method) => method.id === selectedMethodId);
    const recommended = bundle.methods.some((method) => recommendedIds.has(method.id));
    const expanded = effectiveExpandedBundleIds.has(bundle.id);
    const interaction = bundleInteractionState(bundle, dataset);
    const defaults = interaction.defaults;
    const blocked = interaction.blocked;
    const blockReason = interaction.reason;
    const copy = methodBundleDisplayCopy(bundle);
    const outputLabels = uniqueStrings(bundle.methods.map((method) => methodOutputLabel(method)));
    const outputSummary = bundleOutputSummary(bundle);
    const roleLabels = uniqueStrings(bundle.methods.flatMap((method) => methodRoleLabels(method)));
    function openBundleEditor() {
      const run = methodRunSpecs.find((spec) => bundle.methods.some((method) => method.id === spec.method_id));
      if (run) {
        focusMethodRun(run.method_id, run.run_id);
        return;
      }
      const focusMethod = defaults[0] || bundle.methods[0] || bundle.representative;
      openMethodEditor(focusMethod.id);
    }
    return (
      <article
        className={`rounded-[22px] border p-4 text-left transition ${
          blocked
            ? "border-amber-200/18 bg-[linear-gradient(135deg,rgba(255,190,118,0.08),rgba(0,0,0,0.2))] text-[var(--muted)]"
            : active
            ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
            : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
        }`}
        key={bundleRenderKey(bundle, scope, index)}
        onClick={() => openBundleEditor()}
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <button
            className="block min-w-0 flex-1 text-left"
            onClick={(event) => {
              event.stopPropagation();
              if (bundleRunGroups(bundle, methodRunSpecs).length) {
                focusBundleSelection(bundle);
              } else {
                addBundleRunGroup(bundle);
              }
            }}
            type="button"
          >
            <span className="block text-[10px] uppercase tracking-[0.24em] text-[var(--muted)]">{bundle.family}</span>
            <span className="mt-1 block text-base font-semibold text-[var(--text-strong)]">{bundle.title}</span>
            <span className="mt-2 inline-flex rounded-full border border-white/10 bg-black/18 px-2 py-1 text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{outputSummary}</span>
            <span className="mt-2 block text-xs leading-6 text-[var(--muted)]">
              默认带 {defaults.map((method) => methodOutputLabel(method)).join("、")}，并继续复用现有的清洗与派生指标逻辑。
            </span>
          </button>
          <div className="flex flex-col items-end gap-2">
            <button
              aria-label={`Add default runs for ${bundle.title}`}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#74d0d9]/45 bg-[#74d0d9]/12 text-lg font-semibold text-[var(--text-strong)] transition hover:bg-[#74d0d9]/20"
              onClick={(event) => {
                event.stopPropagation();
                appendBundleDefaults(bundle);
              }}
              title={blocked ? `先加入执行篮；${blockReason}` : "再次加入整组子方法，使用同一套字段/对象形成新运行组"}
              type="button"
            >
              +
            </button>
            <span className="surface-chip">{selectedBundleSummary(bundle)}</span>
            {recommended ? (
              <span className="surface-chip border-[#74d0d9]/40 bg-[#74d0d9]/10 text-[var(--text-strong)]">推荐</span>
            ) : null}
            {blocked ? <UnavailableBadge reason={blockReason} /> : null}
          </div>
        </div>
        <p className="mt-3 text-xs leading-6 text-[var(--muted)]">{copy.descriptionLine}</p>
        <p className="mt-2 text-xs leading-6 text-[var(--muted)]">{copy.cliLine}</p>
        <div className="mt-3 rounded-[16px] border border-[#f0d58c]/20 bg-[#f0d58c]/8 p-3 text-xs leading-6 text-[var(--muted)]">
          <span className="font-semibold text-[var(--text-strong)]">统一方法规则：</span>
          选择后默认加入全部可运行子方法；组内字段、对象和数据口径共享。需要另一套对象/字段/数据时，点“再次加入整组”生成新组。
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {copy.sections.slice(0, 4).map((section) => (
            <div className="rounded-[16px] border border-white/10 bg-white/5 p-3" key={`${bundle.id}-beginner-${section.kind}-${section.label}`}>
              <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">{section.label}</p>
              <p className="mt-1 text-[11px] leading-5 text-[var(--text-strong)]">{section.value}</p>
              {section.help ? <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">{section.help}</p> : null}
            </div>
          ))}
        </div>
        <p className="mt-2 text-[11px] leading-5 text-[var(--muted)]">
          这类方法会先看清洗后的表格和派生字段，再决定输出哪些图表、规格或报告段落。
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {roleLabels.slice(0, 4).map((label) => (
            <span className="surface-chip" key={`${bundle.id}-${label}-role`}>
              {label}
            </span>
          ))}
          {outputLabels.slice(0, 6).map((label) => (
            <span className="surface-chip" key={`${bundle.id}-${label}-output`}>
              {label}
            </span>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            className="surface-chip"
            onClick={(event) => {
              event.stopPropagation();
              if (bundleRunGroups(bundle, methodRunSpecs).length) {
                focusBundleSelection(bundle);
              } else {
                addBundleRunGroup(bundle);
              }
            }}
            type="button"
          >
            加入整组子方法
          </button>
          <button
            className="rounded-full border border-[#f0d58c]/45 bg-[#f0d58c]/14 px-4 py-2 text-xs font-semibold text-[var(--text-strong)] shadow-[0_0_24px_rgba(240,213,140,0.10)] transition hover:bg-[#f0d58c]/20"
            onClick={(event) => {
              event.stopPropagation();
              appendBundleDefaults(bundle);
            }}
            title={blocked ? `先保留这组方法；${blockReason}` : "需要另一套字段、对象或数据口径时，用这里再次加入整组。"}
            type="button"
          >
            再次加入整组
          </button>
          <button
            className="surface-chip"
            onClick={(event) => {
              event.stopPropagation();
              toggleBundleDetails(bundle.id);
            }}
            type="button"
          >
            {expanded ? "收起详细信息" : "详细信息"}
          </button>
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.22em]">
            {bundle.methods.length} child methods
          </span>
        </div>
        {blocked ? (
          <BlockedReasonPanel action="仍可加入执行篮、展开明细和配置字段；数据满足条件后即可运行。" reason={blockReason} />
        ) : null}
        {expanded ? (
          <div className="mt-4 rounded-[20px] border border-white/10 bg-black/20 p-3">
            <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">子方法明细</p>
            <div className="mt-3 grid gap-2">
              {bundle.methods.map((method, methodIndex) => {
                const childActive = selectedMethodId === method.id;
                const childSelected = selectedMethodIds.has(method.id);
                const childCopy = methodDisplayCopy(method);
                return (
                  <div
                    className={`rounded-[16px] border px-3 py-3 transition ${
                      childActive
                        ? "border-[#74d0d9]/55 bg-[#74d0d9]/10"
                        : "border-white/10 bg-white/5"
                    }`}
                    key={methodRenderKey(method, bundle.id, methodIndex)}
                  >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                      <button
                        className="min-w-0 flex-1 text-left"
                        onClick={(event) => {
                          event.stopPropagation();
                          openMethodEditor(method.id);
                        }}
                        type="button"
                      >
                        <span className="block text-sm font-medium text-[var(--text-strong)]">{methodSubmethodTitle(method)}</span>
                        <span className="mt-1 block text-xs leading-5 text-[var(--muted)]">
                          {methodRoleLabels(method).join("、") || "默认角色"} · {methodGoalText(method).trim()}
                        </span>
                        <span className="mt-2 block text-[11px] leading-5 text-[var(--muted)]">
                          <span className="text-[var(--text-strong)]">{childCopy.sections[1]?.label || "什么时候用"}：</span>
                          {childCopy.sections[1]?.value || childCopy.descriptionLine}
                        </span>
                        <span className="mt-1 block text-[11px] leading-5 text-[var(--muted)]">
                          <span className="text-[var(--text-strong)]">{childCopy.sections[2]?.label || "怎么用"}：</span>
                          {childCopy.sections[2]?.value || childCopy.actionLine}
                        </span>
                      </button>
                      <button
                        className="surface-chip"
                        onClick={(event) => {
                          event.stopPropagation();
                          openMethodEditor(method.id);
                        }}
                        type="button"
                      >
                        编辑
                      </button>
                      <button
                        aria-label={`Add another run for ${methodSubmethodTitle(method)}`}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[#74d0d9]/45 bg-[#74d0d9]/12 text-base font-semibold text-[var(--text-strong)] transition hover:bg-[#74d0d9]/20"
                        onClick={(event) => {
                          event.stopPropagation();
                          appendMethodRun(method.id);
                        }}
                        title="单独追加这个子方法；整组再次加入请用上面的醒目按钮"
                        type="button"
                      >
                        +
                      </button>
                      <button
                        className="surface-chip"
                        onClick={(event) => {
                          event.stopPropagation();
                          const firstRun = runsForMethod(method.id)[0];
                          if (childSelected && firstRun) {
                            removeMethodRun(firstRun.run_id);
                          } else {
                            toggleMethod(method.id);
                          }
                        }}
                        type="button"
                      >
                        {childSelected ? "删除子方法" : "加入单子方法"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : null}
      </article>
    );
  }

  return (
    <section id="lab-method-workspace" className="lab-method-command scroll-mt-4 rounded-[32px] border border-white/10 bg-[#0d1213]/88 p-4 shadow-2xl backdrop-blur-2xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">MethodOps SLA</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">
            方法卡可用性、选择、执行和报告证据链
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--muted)]">
            目录默认排除金融交易/投机导向卡片；每张方法卡带可编辑绑定、CLI 智能解读和报告价值钩子，适合批量跑完再合并成 TO B 交付。
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-[var(--muted)]">
          <span className={`surface-chip ${methodQuality.visualSlaMet ? "border-[#9ec69f]/40 bg-[#9ec69f]/10 text-[var(--text-strong)]" : "border-amber-300/35 bg-amber-400/10"}`}>
            非金融可视化 {formatNumber(methodQuality.nonFinancialVisual)}
          </span>
          <span className={`surface-chip ${methodQuality.financeExcluded ? "border-[#9ec69f]/40 bg-[#9ec69f]/10 text-[var(--text-strong)]" : "border-red-300/35 bg-red-500/10 text-red-100"}`}>
            金融卡 {methodQuality.sources.financial_visual_catalog || 0}
          </span>
          <span className="surface-chip">当前可运行 {formatNumber(methodQuality.runnable)}</span>
          <span className="surface-chip">{selectedReadinessLabel}</span>
        </div>
      </div>

      <div className="lab-quality-grid mt-4">
        <div className="lab-quality-card lab-quality-card-hero">
          <p className="lab-command-label">Catalog SLA</p>
          <div className="mt-3 flex items-end justify-between gap-3">
            <span className="text-4xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">
              {formatNumber(methodQuality.nonFinancialVisual)}
            </span>
            <span className="rounded-full border border-[#9ec69f]/30 bg-[#9ec69f]/12 px-3 py-1 text-xs text-[#d8f5d4]">
              target 500+
            </span>
          </div>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
            覆盖通用统计图、EDA、诊断、因果、时间序列、空间、文本、网络、医学/教育/运营等非金融场景。
          </p>
        </div>
        <div className="lab-quality-card">
          <p className="lab-command-label">Ready On Dataset</p>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">{methodQuality.readyPercent}%</p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
            <div className="h-full rounded-full bg-[linear-gradient(90deg,var(--lab-cyan),var(--lab-green))]" style={{ width: `${methodQuality.readyPercent}%` }} />
          </div>
          <p className="mt-2 text-xs text-[var(--muted)]">{formatNumber(methodQuality.runnable)} ready · {formatNumber(methodQuality.blocked)} waiting for fields</p>
        </div>
        <div className="lab-quality-card">
          <p className="lab-command-label">Execution Basket</p>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">{formatNumber(selectedRunCount)}</p>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
            {methodQuality.selected
              ? `${formatNumber(methodQuality.selectedRunnable)} selected methods are runnable on the current dataset.`
              : "Add recommended bundles or search the full catalog to build a run basket."}
          </p>
        </div>
        <div className="lab-quality-card">
          <p className="lab-command-label">Governance</p>
          <p className="mt-3 text-sm font-semibold text-[var(--text-strong)]">
            {methodQuality.financeExcluded ? "Finance visual catalog excluded" : "Finance visual catalog still visible"}
          </p>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
            Default Lab catalog sources: {Object.keys(methodQuality.sources).slice(0, 4).join(" / ") || "loading"}.
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[340px_minmax(0,1fr)]">
        <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">推荐方法</p>
              <h3 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">
                {formatNumber(recommendedMethodSlice.length)} 个推荐项
              </h3>
            </div>
            <button className="surface-chip" onClick={() => setMethodFilter("recommended")} type="button">
              筛到推荐
            </button>
          </div>

          <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
            这里优先放能直接上手、对当前数据更容易出结论的方法。点一下就能加入批量执行。
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {(recommendedBundles.length ? recommendedBundles.slice(0, 12) : []).map((bundle, index) => {
              const selected = bundle.methods.some((method) => selectedMethodIds.has(method.id));
              const interaction = bundleInteractionState(bundle, dataset);
              const blocked = interaction.blocked;
              const copy = methodBundleDisplayCopy(bundle);
              return (
                <button
                    className={`rounded-[20px] border p-4 text-left text-sm transition ${
                    selected
                      ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                      : blocked
                        ? "border-amber-200/20 bg-amber-400/8 text-amber-100/80 hover:bg-amber-400/12"
                        : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                  }`}
                  key={bundleRenderKey(bundle, "recommended-bundle", index)}
                  onClick={() => (selected ? focusBundleSelection(bundle) : addBundleRunGroup(bundle))}
                  title={blocked && !selected ? `先规划这组方法；${interaction.reason}` : copy.cliLine}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-[var(--text-strong)]">{bundle.title}</p>
                      <p className="mt-2 break-words text-xs leading-6 text-[var(--muted)]">
                        {copy.descriptionLine}
                      </p>
                      <p className="mt-2 line-clamp-3 text-[11px] leading-5 text-[var(--muted)]">
                        <span className="text-[var(--text-strong)]">{copy.sections[1]?.label || "什么时候用"}：</span>
                        {copy.sections[1]?.value || copy.actionLine}
                      </p>
                    </div>
                    {blocked && !selected ? <LockKeyhole className="shrink-0" size={13} /> : null}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="surface-chip">{bundle.methods.length} 个子方法</span>
                    {selected ? <span className="surface-chip border-[#74d0d9]/40 bg-[#74d0d9]/10 text-[var(--text-strong)]">已加入</span> : null}
                    {blocked && !selected ? <span className="surface-chip border-amber-300/35 bg-amber-300/10">可先规划</span> : null}
                  </div>
                </button>
              );
            })}
            {!recommendedBundles.length
              ? recommendedMethodSlice.slice(0, 12).map((method, index) => {
                  const selected = selectedMethodIds.has(method.id);
                  const blockedReason = methodRunBlockReason(method, dataset);
                  const blocked = Boolean(blockedReason);
                  const copy = methodDisplayCopy(method);
                  return (
                    <button
                      className={`rounded-[20px] border p-4 text-left text-sm transition ${
                        selected
                          ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                          : blocked
                            ? "border-amber-200/20 bg-amber-400/8 text-amber-100/80 hover:bg-amber-400/12"
                            : "border-white/10 bg-black/18 text-[var(--muted)] hover:bg-white/6"
                      }`}
                      key={methodRenderKey(method, "recommended-method", index)}
                      onClick={() => (selected ? openMethodEditor(method.id) : toggleMethod(method.id))}
                      title={blocked && !selected ? `先规划这张方法卡；${blockedReason}` : copy.cliLine}
                      type="button"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-[var(--text-strong)]">{methodDisplayTitle(method)}</p>
                          <p className="mt-2 break-words text-xs leading-6 text-[var(--muted)]">
                            {copy.descriptionLine}
                          </p>
                          <p className="mt-2 line-clamp-3 text-[11px] leading-5 text-[var(--muted)]">
                            <span className="text-[var(--text-strong)]">{copy.sections[1]?.label || "什么时候用"}：</span>
                            {copy.sections[1]?.value || copy.actionLine}
                          </p>
                        </div>
                        {blocked && !selected ? <LockKeyhole className="shrink-0" size={13} /> : null}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <span className="surface-chip">{method.family}</span>
                        {selected ? <span className="surface-chip border-[#74d0d9]/40 bg-[#74d0d9]/10 text-[var(--text-strong)]">已加入</span> : null}
                        {blocked && !selected ? <span className="surface-chip border-amber-300/35 bg-amber-300/10">可先规划</span> : null}
                      </div>
                    </button>
                  );
                })
              : null}
          </div>

          <div className="mt-4 rounded-[22px] border border-white/10 bg-black/18 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">当前已选</p>
              <span className="surface-chip">全部带 CLI 解读</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedRunGroups.length ? (
                selectedRunGroups.slice(0, MAX_SELECTED_METHOD_RUNS).map(({ groupId, runs }) => {
                  const run = runs[0];
                  const method = methodsById.get(run.method_id);
                  const active = runs.some((item) => selectedMethodId === item.method_id && activeMethodRunIds[item.method_id] === item.run_id);
                  const groupLabel = run.bundle_title || (method ? methodBundleTitle(method) : run.method_id);
                  const sourceBundle = visibleBundles.find((bundle) => bundle.title === groupLabel || bundle.methods.some((item) => item.id === run.method_id));
                  return (
                    <div
                      className={`flex flex-wrap items-center gap-2 rounded-[18px] border px-3 py-2 text-xs transition ${
                        active
                          ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                          : "border-white/10 bg-white/5 text-[var(--muted)]"
                      }`}
                      key={groupId}
                    >
                      <button
                        className="text-left"
                        onClick={() => openMethodEditor(run.method_id, run.run_id)}
                        title="点击切换到这组已选方法；组内子方法共享同一字段、对象和数据口径。"
                        type="button"
                      >
                        {groupLabel} · {runs.length > 1 ? `${runs.length} 子方法共享字段` : "单子方法"} · CLI解读
                      </button>
                      {sourceBundle ? (
                        <button className="surface-chip border-[#f0d58c]/35 bg-[#f0d58c]/12" onClick={() => addBundleRunGroup(sourceBundle)} type="button">
                          再来一组
                        </button>
                      ) : null}
                      <button className="surface-chip border-red-300/25 bg-red-500/8 text-red-100" onClick={() => removeMethodRunGroup(groupId)} type="button">
                        删除整组
                      </button>
                    </div>
                  );
                })
              ) : (
                (selectedMethodBundles.length ? selectedMethodBundles : recommendedBundles)
                  .slice(0, MAX_SELECTED_METHOD_RUNS)
                  .map((bundle, index) => {
                    const active = bundle.methods.some((method) => method.id === selectedMethodId);
                    const count = bundleRunCount(bundle, methodRunSpecs, selectedMethodIds);
                    const copy = methodBundleDisplayCopy(bundle);
                    return (
                      <button
                        className={`rounded-full border px-3 py-2 text-xs transition ${
                          active
                            ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                            : "border-white/10 bg-white/5 text-[var(--muted)] hover:bg-white/10"
                        }`}
                        key={bundleRenderKey(bundle, "selected-run-empty", index)}
                        onClick={() => focusBundleSelection(bundle)}
                        title={copy.cliLine}
                        type="button"
                      >
                        {count > 1 ? `${bundle.title} · ${count} 项` : bundle.title} · CLI解读
                      </button>
                    );
                  })
              )}
              {!selectedRunSpecs.length ? (
                <span className="rounded-full border border-white/10 bg-black/18 px-3 py-2 text-xs text-[var(--muted)]">
                  默认方法已加载，点“编辑当前方法”可进入配置，点“+”可追加运行实例。
                </span>
              ) : null}
            </div>
          </div>

          {catalogLoaded && methodSourceCounts.length ? (
            <div className="mt-3 rounded-[20px] border border-white/10 bg-black/18 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">Source groups</p>
                {activeMethodSource ? (
                  <button className="surface-chip" onClick={() => setActiveMethodSource("")} type="button">
                    Clear source
                  </button>
                ) : null}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {methodSourceCounts.slice(0, 8).map(([source, count]) => (
                  <button
                    aria-pressed={activeMethodSource === source}
                    className={`surface-chip ${
                      activeMethodSource === source ? "border-[#f0d58c]/55 bg-[#f0d58c]/12 text-[var(--text-strong)]" : ""
                    }`}
                    key={source}
                    onClick={() => setActiveMethodSource(activeMethodSource === source ? "" : source)}
                    title={`Filter source ${source}`}
                    type="button"
                  >
                    {source} {count}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {activeSelectedMethod ? (
            <button
              className="mt-4 w-full rounded-[22px] border border-[#74d0d9]/25 bg-[#74d0d9]/10 px-4 py-3 text-left text-sm text-[var(--text-strong)] transition hover:bg-[#74d0d9]/16"
              onClick={() => openMethodEditor(activeSelectedMethod.id)}
              type="button"
            >
              编辑当前方法：{methodDisplayTitle(activeSelectedMethod)}
            </button>
          ) : null}

          <div className="mt-4 grid gap-2">
            <button className="surface-chip justify-center" onClick={selectFilteredMethods} type="button">
              勾选当前展示
            </button>
            <button className="surface-chip justify-center" onClick={clearFilteredMethods} type="button">
              清空当前展示
            </button>
            <button
              className="surface-chip justify-center"
              onClick={() => {
                setMethodFilter("recommended");
                if (recommendedBundles.length) {
                  addBundleRunGroups(recommendedBundles.slice(0, 4));
                  return;
                }
                replaceSelectedMethods(recommendedMethodSlice.slice(0, DEFAULT_SELECTED_METHOD_RUNS).map((method) => method.id));
              }}
              type="button"
            >
              一键加入推荐
            </button>
          </div>

          <div className="mt-4 rounded-[22px] border border-white/10 bg-black/18 p-3">
            <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">默认能力</p>
            <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
              所有方法运行都会默认携带 CLI 智能解读，并绑定业务关联说明。执行前仍会复用现有的数据清洗和派生指标逻辑；多方法批量时，会先独立出各自结果，再做智能合并。
            </p>
          </div>

          {editorPortalTarget && methodEditorOpen
            ? createPortal(
                <div
                  aria-modal="true"
                  className="fixed inset-0 z-[1200] flex items-start justify-center overflow-y-auto bg-black/72 px-3 py-6 backdrop-blur-md"
                  onClick={() => closeMethodEditor()}
                  role="dialog"
                >
                  <div
                    className="w-full max-w-6xl rounded-[28px] border border-[#74d0d9]/40 bg-[#071113] p-4 shadow-[0_34px_120px_rgba(0,0,0,0.55)]"
                    onClick={(event) => event.stopPropagation()}
                  >
                    <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.24em] text-cyan-100/75">Selected method editor</p>
                        <h3 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">
                          {activeEditorMethod ? methodDisplayTitle(activeEditorMethod) : selectedMethodId || "Method editor is opening"}
                        </h3>
                        <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                          {activeEditorMethod
                            ? "Edit fields, variables, object picks, run mode, and add the same method again here."
                            : "The edit request was received, but the method catalog has not produced a concrete method yet."}
                        </p>
                      </div>
                      <button className="surface-chip" onClick={() => closeMethodEditor()} type="button">
                        Hide editor
                      </button>
                    </div>
                    {selectedRunSpecs.length > 1 ? (
                      <div className="mb-3 rounded-[18px] border border-white/10 bg-black/18 p-3">
                        <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">已选方法快速切换</p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {selectedRunSpecs.slice(0, MAX_SELECTED_METHOD_RUNS).map((run) => {
                            const method = methodsById.get(run.method_id);
                            const active = selectedMethodId === run.method_id && activeMethodRunIds[run.method_id] === run.run_id;
                            return (
                              <button
                                className={`rounded-full border px-3 py-2 text-xs transition ${
                                  active
                                    ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                                    : "border-white/10 bg-white/5 text-[var(--muted)] hover:bg-white/10"
                                }`}
                                key={`editor-switch-${run.run_id}`}
                                onClick={() => openMethodEditor(run.method_id, run.run_id)}
                                type="button"
                              >
                                {run.label || (method ? methodSubmethodTitle(method) : run.method_id)}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    ) : null}
                    {activeEditorMethod ? (
                      renderMethodCard(activeEditorMethod, "editor-card")
                    ) : (
                      <div className="rounded-[22px] border border-cyan-200/20 bg-cyan-400/8 p-4 text-sm leading-7 text-[var(--muted)]">
                        <p className="font-semibold text-[var(--text-strong)]">The editor layer is open.</p>
                        <p className="mt-2">
                          Wait for the method catalog to finish loading, then click a concrete method card or selected run. This panel remains available while the catalog loads.
                        </p>
                      </div>
                    )}
                  </div>
                </div>,
                editorPortalTarget,
              )
            : null}
          {editorPortalTarget && methodGuideOpen
            ? createPortal(
                <MethodGuideModal
                  onClose={() => setMethodGuideOpen(false)}
                  onTopicChange={setMethodGuideTopic}
                  topic={methodGuideTopic}
                />,
                editorPortalTarget,
              )
            : null}
        </section>

        <section className="rounded-[28px] border border-white/10 bg-white/5 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">完整方法池</p>
              <h3 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">
                {catalogLoaded ? `${formatNumber(filteredMethodBundles.length)} 个可见方法类` : "正在加载方法目录..."}
              </h3>
              <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                前三段相同的方法明细会先合并为一类，再由详细信息展开具体子项。
              </p>
            </div>
            <button className="surface-chip inline-flex items-center gap-2" onClick={() => setGroupedView((value) => !value)} type="button">
              <ChevronDown size={14} />
              {groupedView ? "按家族分组" : "按方法类平铺"}
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {[
              ["all", catalogLoaded ? `全部 ${formatNumber(methods.length)}` : "全部 ..."],
              ["selected", catalogLoaded ? `已选 ${formatNumber(selectedRunCount)}` : "已选 ..."],
              ["visual", catalogLoaded ? `可视化 ${formatNumber(visualMethodCount)}` : "可视化 ..."],
              ["recommended", catalogLoaded ? `推荐 ${formatNumber(recommendedMethodSlice.length)}` : "推荐 ..."],
            ].map(([value, label]) => (
              <button
                className={`surface-chip justify-center ${
                  methodFilter === value ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]" : ""
                }`}
                key={value}
                onClick={() => setMethodFilter(value as MethodFilter)}
                type="button"
              >
                <Filter size={12} />
                {label}
              </button>
            ))}
          </div>

          <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Catalog" value={catalogLoaded ? formatNumber(methodQuality.total) : "..."} />
            <MetricCard label="Non-fin visual" value={catalogLoaded ? formatNumber(methodQuality.nonFinancialVisual) : "..."} />
            <MetricCard label="Runnable" value={catalogLoaded ? `${formatNumber(methodQuality.runnable)} / ${formatNumber(methodQuality.readyPercent)}%` : "..."} />
            <MetricCard label="Selected" value={catalogLoaded ? formatNumber(selectedRunCount) : "..."} />
          </div>

          <label className="mt-3 block space-y-2">
            <span className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">搜索方法</span>
            <div className="field-input flex items-center gap-2">
              <Search size={16} className="text-[var(--muted)]" />
              <input
                className="min-w-0 flex-1 border-0 bg-transparent p-0 text-[15px] outline-none"
                onChange={(event) => setMethodSearch(event.target.value)}
                placeholder="搜方法名、家族、目标、来源"
                value={methodSearch}
              />
            </div>
          </label>

          {catalogLoaded && groupedMethodCounts.length ? (
            <div className="mt-4 rounded-[20px] border border-white/10 bg-black/18 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">家族分布</p>
                {activeMethodFamily ? (
                  <button className="surface-chip" onClick={() => setActiveMethodFamily("")} type="button">
                    清除家族筛选
                  </button>
                ) : null}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {groupedMethodCounts.slice(0, 12).map(([family, count]) => (
                  <button
                    aria-pressed={activeMethodFamily === family}
                    className={`surface-chip ${
                      activeMethodFamily === family ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]" : ""
                    }`}
                    key={family}
                    onClick={() => setActiveMethodFamily(activeMethodFamily === family ? "" : family)}
                    title={`筛选 ${family} 方法卡`}
                    type="button"
                  >
                    {family} {count}
                  </button>
                ))}
              </div>
              {activeMethodFamily ? (
                <p className="mt-3 text-xs leading-5 text-[var(--muted)]">
                  当前展示「{activeMethodFamily}」方法卡；再次点击该卡片可恢复全部方法。
                </p>
              ) : null}
            </div>
          ) : null}

          {activeSelectedMethod ? (
            <div className="mt-4">
              <p className="mb-2 text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Selected method config</p>
            {activeEditorMethod ? renderMethodCard(activeEditorMethod, "inline-active-editor") : null}
            </div>
          ) : null}

          <div className="mt-4">
            {!catalogLoaded ? (
              <div className="rounded-[18px] border border-dashed border-white/10 bg-black/18 px-4 py-8 text-sm text-[var(--muted)]">
                正在从后端加载方法目录，请稍候。
              </div>
            ) : null}
            {groupedView && !searchActive
              ? visibleGroupedMethods.map(([family, familyMethods]) => (
                  <div className="mb-4" key={family}>
                    <p className="mb-2 text-xs uppercase tracking-[0.24em] text-[var(--muted)]">{family}</p>
                    <div className="grid gap-3">{familyMethods.map((bundle, index) => renderBundleCard(bundle, `group-${family}`, index))}</div>
                  </div>
                ))
              : (
                <div className="grid gap-3">{visibleBundles.map((bundle, index) => renderBundleCard(bundle, "visible-bundle", index))}</div>
              )}
          </div>

          {hiddenMethodCount > 0 ? (
            <div className="mt-4 rounded-[22px] border border-white/10 bg-black/18 p-3 text-sm text-[var(--muted)]">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p>还有 {formatNumber(hiddenMethodCount)} 个方法类未展示，继续加载可把它们放进当前列表。</p>
                <button className="surface-chip" onClick={loadMoreMethods} type="button">
                  加载更多
                </button>
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </section>
  );
}

function ResultCanvas({
  addMethodBundleRunGroup,
  appendMethodRun,
  canvasExpanded,
  dataset,
  isBusy,
  onRerunBlueprintPart,
  partRunBusy,
  result,
  selectedSheetName,
  methodRuns,
  autoSummary,
  methods,
  methodCatalogSummary,
  onOpenMethodEditor,
  selectedMethodIds,
  selectedRunSpecs,
  selectMethod,
}: {
  addMethodBundleRunGroup: (bundle: MethodBundle, options?: { replaceExisting?: boolean }) => void;
  appendMethodRun: (methodId: string, overrides?: Partial<MethodRunSpec>) => void;
  canvasExpanded: boolean;
  dataset?: DatasetItem;
  isBusy: boolean;
  onRerunBlueprintPart: (analysisResult: StatsResult, workspaceResult: WorkspaceResult, blueprint: AutoReportPartGenerationBlueprint) => Promise<void>;
  partRunBusy: string | null;
  result: WorkspaceResult | null;
  selectedSheetName: string;
  methodRuns: MethodRunResult[];
  autoSummary: StatsResult | SmartReport | null;
  methods: MethodCatalogItem[];
  methodCatalogSummary: { live: number; catalog: number; planned: number; total: number; visual: number };
  onOpenMethodEditor: (methodId: string, runId?: string) => void;
  selectedMethodIds: Set<string>;
  selectedRunSpecs: MethodRunSpec[];
  selectMethod: (methodId: string) => void;
}) {
  const [expandedOverviewBundleIds, setExpandedOverviewBundleIds] = useState<Set<string>>(() => new Set());
  const overviewBundles = useMemo(() => buildMethodBundles(methods).slice(0, 60), [methods]);
  const selectedMethodsById = useMemo(() => new Map(methods.map((method) => [method.id, method])), [methods]);

  function toggleOverviewBundle(bundleId: string) {
    setExpandedOverviewBundleIds((current) => {
      const next = new Set(current);
      if (next.has(bundleId)) {
        next.delete(bundleId);
      } else {
        next.add(bundleId);
      }
      return next;
    });
  }

  function appendOverviewBundleDefaults(bundle: MethodBundle) {
    const defaults = bundleDefaultMethods(bundle, dataset);
    if (!defaults.length) {
      setExpandedOverviewBundleIds((current) => new Set(current).add(bundle.id));
      selectMethod(bundle.representative.id);
      return;
    }
    addMethodBundleRunGroup(bundle);
    setExpandedOverviewBundleIds((current) => new Set(current).add(bundle.id));
    selectMethod(defaults[0]?.id || bundle.representative.id);
  }

  return (
    <main className="min-h-0 overflow-hidden rounded-[32px] border border-white/10 bg-[#080d0e]/92 shadow-2xl backdrop-blur-2xl">
      <div className="flex h-full min-h-0 flex-col">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">Result canvas</p>
            <h2 className="mt-1 text-2xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">
              {result?.title || "自动清洗、派生和方法总合并结果"}
            </h2>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-[var(--muted)]">
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2">{datasetLabel(dataset)}</span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2">{selectedSheetName || "Default sheet"}</span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2">{canvasExpanded ? "专注画布" : "控制区可见"}</span>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto">
          <div className={`mx-auto grid w-full max-w-[1800px] gap-5 p-5 ${canvasExpanded ? "min-h-[2200px]" : "min-h-[1600px]"}`}>
            {!result ? (
              <EmptyCanvas
                appendMethodRun={appendMethodRun}
                dataset={dataset}
                methods={methods}
                onOpenMethodEditor={onOpenMethodEditor}
                selectedRunSpecs={selectedRunSpecs}
              />
            ) : (
              <ResultContent
                isBusy={isBusy}
                onRerunBlueprintPart={onRerunBlueprintPart}
                partRunBusy={partRunBusy}
                result={result}
              />
            )}

            <section className="grid gap-5 xl:grid-cols-2">
              {selectedRunSpecs.length ? (
                <div className="rounded-[32px] border border-[#74d0d9]/22 bg-[#74d0d9]/8 p-6 xl:col-span-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-cyan-100/75">Selected methods remain editable</p>
                      <h3 className="mt-1 text-xl font-semibold text-[var(--text-strong)]">
                        {formatNumber(selectedRunSpecs.length)} configured run instances
                      </h3>
                      <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
                        Click any selected method below to reopen the editor for fields, variables, object picks, run mode, and duplicate runs.
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {selectedRunSpecs.slice(0, 24).map((run) => {
                      const method = selectedMethodsById.get(run.method_id);
                      return (
                        <button
                          className="surface-chip border-[#74d0d9]/35 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                          key={`canvas-selected-${run.run_id}`}
                          onClick={() => onOpenMethodEditor(run.method_id, run.run_id)}
                          type="button"
                        >
                          {run.label || (method ? methodSubmethodTitle(method) : run.method_id)}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              <div className="rounded-[32px] border border-white/10 bg-white/5 p-6">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">单项结果</p>
                <div className="mt-4 grid gap-3">
                  {methodRuns.length ? (
                    methodRuns.map((item) => (
                      <div className="rounded-[18px] border border-white/10 bg-black/18 p-4" key={methodRunResultKey(item)}>
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{item.method_run_id || item.method_id}</p>
                            <h4 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">{item.method_run_label || item.method_name_zh || item.method_name}</h4>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <span className="surface-chip">CLI解读</span>
                            <span className="surface-chip">{item.selection_mode}</span>
                            {item.smart_merge_group ? <span className="surface-chip">{item.smart_merge_group}</span> : null}
                            <span className="surface-chip">{item.status}</span>
                            {item.runtime_status ? <span className="surface-chip">{methodRunRuntimeStatusLabel(item)}</span> : null}
                            {item.runtime_executor ? <span className="surface-chip">{item.runtime_executor}</span> : null}
                          </div>
                        </div>
                        <pre className="mt-3 max-h-[220px] overflow-auto rounded-[16px] bg-black/30 p-3 text-xs leading-6">{stringifySafe(item.payload)}</pre>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-[var(--muted)]">完成后，这里会逐个列出每个方法的单独结果。</p>
                  )}
                </div>
              </div>

              <div className="rounded-[32px] border border-white/10 bg-white/5 p-6">
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">总合并解读</p>
                <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
                  这里会把自动清洗、派生指标、各方法单项结果合并成总解读。当前先展示自动结果和方法总览，后续可以再把每个方法的结论压成一份总总结。
                </p>
                {autoSummary ? (
                  <pre className="mt-4 max-h-[360px] overflow-auto rounded-[18px] border border-white/10 bg-black/30 p-4 text-xs leading-6">
                    {stringifySafe(autoSummary)}
                  </pre>
                ) : null}
              </div>
            </section>

            <section className="rounded-[32px] border border-white/10 bg-white/5 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">方法总览</p>
                  <h3 className="mt-1 text-xl font-semibold text-[var(--text-strong)]">
                    {methodCatalogSummary.total} methods · visual {methodCatalogSummary.visual} · live {methodCatalogSummary.live} · catalog {methodCatalogSummary.catalog} · planned {methodCatalogSummary.planned}
                  </h3>
                </div>
              </div>
              <div className="mt-4 grid gap-4 xl:grid-cols-2">
                {overviewBundles.map((bundle, index) => {
                  const selected = bundle.methods.some((method) => selectedMethodIds.has(method.id));
                  const expanded = expandedOverviewBundleIds.has(bundle.id);
                  const interaction = bundleInteractionState(bundle, dataset);
                  const defaults = interaction.defaults;
                  const blocked = interaction.blocked;
                  const blockReason = interaction.reason;
                  const copy = methodBundleDisplayCopy(bundle);
                  return (
                    <div
                      className={`rounded-[18px] border p-4 transition ${
                        selected
                          ? "border-[#74d0d9]/55 bg-[#74d0d9]/10"
                          : blocked
                            ? "border-amber-200/18 bg-[linear-gradient(135deg,rgba(255,190,118,0.08),rgba(0,0,0,0.16))]"
                          : "border-white/10 bg-black/18 hover:border-white/20 hover:bg-white/6"
                      }`}
                      key={bundleRenderKey(bundle, "overview-bundle", index)}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{bundle.family}</p>
                          <h4 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">{bundle.title}</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <span className="surface-chip">{bundle.methods.length} child methods</span>
                          {selected ? <span className="surface-chip border-[#74d0d9]/40 bg-[#74d0d9]/10 text-[var(--text-strong)]">已加入</span> : null}
                          {blocked ? <UnavailableBadge reason={blockReason} /> : null}
                        </div>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{copy.descriptionLine}</p>
                      <div className="mt-3 grid gap-2 md:grid-cols-2">
                        {copy.sections.slice(0, 4).map((section) => (
                          <div className="rounded-[16px] border border-white/10 bg-white/5 p-3" key={`${bundle.id}-overview-beginner-${section.kind}-${section.label}`}>
                            <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--muted)]">{section.label}</p>
                            <p className="mt-1 text-[11px] leading-5 text-[var(--text-strong)]">{section.value}</p>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {uniqueStrings(bundle.methods.map((method) => methodOutputLabel(method))).slice(0, 5).map((label) => (
                          <span className="surface-chip" key={`${bundle.id}-overview-output-${label}`}>{label}</span>
                        ))}
                        {uniqueStrings(bundle.methods.flatMap((method) => methodRoleLabels(method))).slice(0, 3).map((label) => (
                          <span className="surface-chip" key={`${bundle.id}-overview-role-${label}`}>{label}</span>
                        ))}
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button className="surface-chip" onClick={() => appendOverviewBundleDefaults(bundle)} title={blocked ? `先规划这组方法；${blockReason}` : undefined} type="button">
                          {selected ? "再次加入默认运行" : "加入默认方法"}
                        </button>
                        <button className="surface-chip" onClick={() => selectMethod(defaults[0]?.id || bundle.representative.id)} type="button">
                          配置方法
                        </button>
                        <button className="surface-chip" onClick={() => toggleOverviewBundle(bundle.id)} type="button">
                          {expanded ? "收起明细" : "展开明细"}
                        </button>
                      </div>
                      {blocked ? (
                        <BlockedReasonPanel action="可以先加入、配置或展开明细；数据字段满足后即可执行。" reason={blockReason} />
                      ) : null}
                      {expanded ? (
                        <div className="mt-4 rounded-[20px] border border-white/10 bg-black/20 p-3">
                          <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">子方法明细</p>
                          <div className="mt-3 grid gap-2">
                            {bundle.methods.map((method, methodIndex) => {
                              const methodSelected = selectedMethodIds.has(method.id);
                              const methodCopy = methodDisplayCopy(method);
                              const methodBlockReason = methodRunBlockReason(method, dataset);
                              return (
                                <div
                                  className={`flex flex-wrap items-start justify-between gap-3 rounded-[16px] border px-3 py-3 transition ${
                                    methodSelected ? "border-[#74d0d9]/55 bg-[#74d0d9]/10" : "border-white/10 bg-white/5"
                                  }`}
                                  key={methodRenderKey(method, `${bundle.id}-overview-child`, methodIndex)}
                                >
                                  <div className="min-w-0">
                                    <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{method.id}</p>
                                    <p className="mt-1 text-sm font-semibold text-[var(--text-strong)]">{method.name_zh || method.name}</p>
                                    <p className="mt-1 text-xs leading-6 text-[var(--muted)]">{methodCopy.descriptionLine}</p>
                                    <p className="mt-2 text-[11px] leading-5 text-[var(--muted)]">
                                      <span className="text-[var(--text-strong)]">{methodCopy.sections[1]?.label || "什么时候用"}：</span>
                                      {methodCopy.sections[1]?.value || methodCopy.actionLine}
                                    </p>
                                    <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">
                                      <span className="text-[var(--text-strong)]">{methodCopy.sections[2]?.label || "怎么用"}：</span>
                                      {methodCopy.sections[2]?.value || methodCopy.actionLine}
                                    </p>
                                  </div>
                                  <div className="flex flex-wrap gap-2">
                                    <button className="surface-chip" onClick={() => onOpenMethodEditor(method.id)} type="button">
                                      配置
                                    </button>
                                    <button className="surface-chip" onClick={() => appendMethodRun(method.id)} title={methodBlockReason ? `先加入执行篮；${methodBlockReason}` : undefined} type="button">
                                      加入运行
                                    </button>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}

function EmptyCanvas({
  appendMethodRun,
  dataset,
  methods,
  onOpenMethodEditor,
  selectedRunSpecs,
}: {
  appendMethodRun: (methodId: string, overrides?: Partial<MethodRunSpec>) => void;
  dataset?: DatasetItem;
  methods: MethodCatalogItem[];
  onOpenMethodEditor: (methodId: string, runId?: string) => void;
  selectedRunSpecs: MethodRunSpec[];
}) {
  const methodsById = useMemo(() => new Map(methods.map((method) => [method.id, method])), [methods]);
  const quickMethods = useMemo(() => recommendedMethods(methods).slice(0, 6), [methods]);
  return (
    <>
      <section className="relative overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(135deg,rgba(255,156,97,0.12),rgba(116,208,217,0.08)_45%,rgba(0,0,0,0.2))] p-8">
        <div className="absolute right-10 top-8 h-56 w-56 rounded-full bg-[#74d0d9]/12 blur-3xl" />
        <div className="relative max-w-4xl">
          <p className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/20 px-3 py-2 text-xs uppercase tracking-[0.24em] text-[var(--muted)]">
            <BrainCircuit size={14} />
            Waiting for a run
          </p>
          <h3 className="mt-6 text-5xl font-semibold tracking-[-0.06em] text-[var(--text-strong)] md:text-7xl">
            自动清洗、派生指标、单方法结果和总合并解读都在这里展开。
          </h3>
          <p className="mt-6 max-w-3xl text-lg leading-9 text-[var(--muted)]">
            这个页面现在直接读取后端统计目录。你可以先自动清洗读取数据，再看系统派生的指标，然后挑任意一个方法单独执行，最后把所有单项结果合并成总解读。
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            {selectedRunSpecs.length ? (
              selectedRunSpecs.slice(0, 8).map((run) => {
                const method = methodsById.get(run.method_id);
                return (
                  <button
                    className="surface-chip border-[#74d0d9]/35 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                    key={`empty-selected-${run.run_id}`}
                    onClick={() => onOpenMethodEditor(run.method_id, run.run_id)}
                    type="button"
                  >
                    Edit {run.label || (method ? methodSubmethodTitle(method) : run.method_id)}
                  </button>
                );
              })
            ) : (
              quickMethods.map((method) => (
                <button
                  className="surface-chip border-[#74d0d9]/25 bg-[#74d0d9]/10 text-[var(--text-strong)]"
                  key={`empty-quick-${method.id}`}
                  onClick={() => appendMethodRun(method.id)}
                  type="button"
                >
                  Add {methodSubmethodTitle(method)}
                </button>
              ))
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-3">
        <CanvasPlaceholder title="Dataset footprint" value={datasetLabel(dataset)} />
        <CanvasPlaceholder title="Rows" value={dataset ? formatNumber(dataset?.row_count) : "..."} />
        <CanvasPlaceholder title="Columns" value={dataset ? formatNumber(dataset?.column_count) : "..."} />
      </section>

      <section className="rounded-[30px] border border-[#74d0d9]/18 bg-[#74d0d9]/7 p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-100/75">Canvas actions</p>
        <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">
          This area provides controls for the selected method and run.
        </h3>
        <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
          Use the chips above to reopen selected-method editing or add a recommended method before running. Result details will replace this area after execution.
        </p>
      </section>
    </>
  );
}

function CanvasPlaceholder({ title, value }: { title: string; value: string }) {
  return (
    <article className="rounded-[30px] border border-white/10 bg-white/5 p-6">
      <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">{title}</p>
      <p className="mt-5 text-3xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">{value}</p>
    </article>
  );
}

function ResultContent({
  result,
  isBusy,
  onRerunBlueprintPart,
  partRunBusy,
}: {
  result: WorkspaceResult;
  isBusy: boolean;
  onRerunBlueprintPart: (analysisResult: StatsResult, workspaceResult: WorkspaceResult, blueprint: AutoReportPartGenerationBlueprint) => Promise<void>;
  partRunBusy: string | null;
}) {
  const payload = result.payload;
  if (isSmartReport(payload)) return <SmartReportCanvas report={payload} result={result} />;
  if (isStatsResult(payload)) {
    return (
      <StatsResultCanvas
        isBusy={isBusy}
        onRerunBlueprintPart={onRerunBlueprintPart}
        partRunBusy={partRunBusy}
        result={payload}
        workspaceResult={result}
      />
    );
  }
  return <GenericResultCanvas result={result} />;
}

function SmartReportCanvas({ report, result }: { report: SmartReport; result: WorkspaceResult }) {
  const mainDownloadable = firstDownloadable(report);
  return (
    <>
      <section className="rounded-[34px] border border-white/10 bg-[linear-gradient(135deg,rgba(255,156,97,0.14),rgba(255,255,255,0.04))] p-7">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">Smart report</p>
            <h3 className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">{report.title || result.title}</h3>
            <p className="mt-3 text-sm text-[var(--muted)]">{result.datasetName} · {new Date(result.createdAt).toLocaleString()}</p>
          </div>
          {mainDownloadable?.path ? (
            <a className="primary-button" href={mainDownloadable.path} rel="noreferrer" target="_blank">
              <FileText className="mr-2" size={16} />
              Open main artifact
            </a>
          ) : null}
        </div>
      </section>
      <RawPayload payload={report} />
    </>
  );
}

function StatsResultCanvas({
  result,
  workspaceResult,
  isBusy,
  onRerunBlueprintPart,
  partRunBusy,
}: {
  result: StatsResult;
  workspaceResult: WorkspaceResult;
  isBusy: boolean;
  onRerunBlueprintPart: (analysisResult: StatsResult, workspaceResult: WorkspaceResult, blueprint: AutoReportPartGenerationBlueprint) => Promise<void>;
  partRunBusy: string | null;
}) {
  const analysisData = autoAnalysisData(result);
  const blueprints = analysisData.report_part_generation_blueprints || [];
  const preMethodAudit = Array.isArray(analysisData.pre_method_routing_audit)
    ? analysisData.pre_method_routing_audit.filter(isRecord)
    : [];
  return (
    <>
      <section className="rounded-[34px] border border-white/10 bg-[linear-gradient(135deg,rgba(116,208,217,0.14),rgba(255,255,255,0.04))] p-7">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">{result.analysis_type}</p>
            <h3 className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">{result.title || workspaceResult.title}</h3>
            <p className="mt-4 max-w-4xl text-base leading-8 text-[var(--muted)]">{result.narrative}</p>
          </div>
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-100">
            <CheckCircle2 size={16} />
            Completed
          </span>
        </div>
      </section>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Object.entries(result.metrics || {}).map(([label, value]) => (
          <article className="rounded-[28px] border border-white/10 bg-white/5 p-5" key={label}>
            <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{label}</p>
            <p className="mt-4 break-words text-3xl font-semibold text-[var(--text-strong)]">{formatValue(value)}</p>
          </article>
        ))}
      </section>
      {preMethodAudit.length ? (
        <section className="rounded-[32px] border border-white/10 bg-white/5 p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">方法前置审计</p>
              <h3 className="mt-1 text-xl font-semibold text-[var(--text-strong)]">先清洗、先派生、再路由方法</h3>
              <p className="mt-2 text-sm leading-7 text-[var(--muted)]">
                这层审计由后端实际返回。它会先完成字段理解、派生字段、关系图谱和语义路由，再进入方法执行。
              </p>
            </div>
            <span className="surface-chip">7 stages</span>
          </div>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {preMethodAudit.slice(0, 7).map((stage, index) => (
              <article className="rounded-[20px] border border-white/10 bg-black/18 p-4" key={`${String(stage.stage || index)}-${index}`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">
                      {formatNumber(stage.sequence ?? index + 1)} / {String(stage.stage || "stage")}
                    </p>
                    <h4 className="mt-1 text-base font-semibold text-[var(--text-strong)]">
                      {String(stage.output || stage.input || "pre-method step")}
                    </h4>
                  </div>
                  <span className="surface-chip">{String(stage.gate_status || "ready")}</span>
                </div>
                <p className="mt-3 text-xs leading-6 text-[var(--muted)]">
                  <span className="text-[var(--text-strong)]">input:</span> {String(stage.input || "-")} ·{" "}
                  <span className="text-[var(--text-strong)]">output:</span> {String(stage.output || "-")}
                </p>
                <p className="mt-2 text-xs leading-6 text-[var(--muted)]">
                  <span className="text-[var(--text-strong)]">pre-method:</span>{" "}
                  {String(stage.completed_before_method_routing ? "yes" : "no")} ·{" "}
                  <span className="text-[var(--text-strong)]">rows:</span> {formatNumber(stage.record_count)}
                </p>
                <p className="mt-2 text-xs leading-6 text-[var(--muted)]">{String(stage.management_use || "")}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
      <ReportPartBlueprintPanel
        blueprints={blueprints}
        isBusy={isBusy}
        onRerunBlueprintPart={(blueprint) => onRerunBlueprintPart(result, workspaceResult, blueprint)}
        partRunBusy={partRunBusy}
        result={result}
      />
      <RuntimePackageDownloadPanel result={result} />
      {(result.tables || []).length ? (
        <section className="grid gap-5">
          {result.tables.map((table) => (
            <div className="rounded-[32px] border border-white/10 bg-white/5 p-6" key={table.title || table.columns.join("-")}>
              <DataTable table={table} />
            </div>
          ))}
        </section>
      ) : null}
      <RawPayload payload={result} />
    </>
  );
}

function ReportPartBlueprintPanel({
  blueprints,
  isBusy,
  onRerunBlueprintPart,
  partRunBusy,
  result,
}: {
  blueprints: AutoReportPartGenerationBlueprint[];
  isBusy: boolean;
  onRerunBlueprintPart: (blueprint: AutoReportPartGenerationBlueprint) => Promise<void>;
  partRunBusy: string | null;
  result: StatsResult;
}) {
  if (!blueprints.length) {
    return null;
  }
  const readyCount = blueprints.filter((item) => item.readiness === "ready").length;
  const partialCount = blueprints.filter((item) => item.readiness === "partial").length;
  const blockedCount = blueprints.filter((item) => item.readiness === "blocked").length;

  return (
    <section className="rounded-[32px] border border-cyan-200/15 bg-[linear-gradient(135deg,rgba(116,208,217,0.13),rgba(255,255,255,0.045))] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Report part generation blueprints</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">
            {blueprints.length} report parts routed to Codex/exec runtime
          </h3>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-[var(--muted)]">
            Each blueprint describes one report part, its required assets, available evidence and runtime handoff.
            It describes a report part and its handoff requirements.
          </p>
        </div>
        <button
          className="surface-chip"
          onClick={() =>
            downloadJsonFile(
              `${slugFilePart(result.title || "analysis-lab")}-report-part-blueprints.json`,
              blueprints,
            )
          }
          type="button"
        >
          Download all blueprints
        </button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <MetricCard label="ready" value={formatNumber(readyCount)} />
        <MetricCard label="partial" value={formatNumber(partialCount)} />
        <MetricCard label="blocked" value={formatNumber(blockedCount)} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {blueprints.map((blueprint) => {
          const handoff = blueprint.runtime_handoff || {};
          const inputContract = blueprint.input_contract || {};
          const narrativeSeed = String(blueprint.narrative_seed || inputContract.narrative_seed || "").trim();
          const bulletSeeds = (
            blueprint.bullet_seeds ||
            (Array.isArray(inputContract.bullet_seeds) ? inputContract.bullet_seeds : [])
          )
            .map((item) => String(item || "").trim())
            .filter(Boolean);
          const tableTitles = (
            blueprint.table_titles ||
            (Array.isArray(inputContract.table_titles) ? inputContract.table_titles : [])
          )
            .map((item) => String(item || "").trim())
            .filter(Boolean);
          const chartRefs = (
            blueprint.chart_refs ||
            (Array.isArray(inputContract.chart_refs) ? inputContract.chart_refs : [])
          )
            .map((item) => String(item || "").trim())
            .filter(Boolean);
          const availableCount = Object.values(blueprint.available_asset_refs || {}).reduce(
            (total, refs) => total + (Array.isArray(refs) ? refs.length : 0),
            0,
          );
          const missing = blueprint.missing_asset_kinds || [];
          return (
            <article
              className="rounded-[24px] border border-white/10 bg-black/22 p-5"
              key={blueprint.report_part_id}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">
                    {blueprint.report_part_id}
                  </p>
                  <h4 className="mt-1 text-xl font-semibold text-[var(--text-strong)]">
                    {blueprint.report_part_title || blueprint.report_part_id}
                  </h4>
                </div>
                <span
                  className={`rounded-full border px-3 py-1.5 text-xs ${
                    blueprint.readiness === "ready"
                      ? "border-emerald-300/25 bg-emerald-400/10 text-emerald-100"
                      : blueprint.readiness === "blocked"
                        ? "border-red-300/25 bg-red-400/10 text-red-100"
                        : "border-amber-300/25 bg-amber-400/10 text-amber-100"
                  }`}
                >
                  {blueprint.readiness}
                </span>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <MetricCard label="assets" value={formatNumber(availableCount)} />
                <MetricCard label="tables" value={formatNumber(blueprint.table_count || tableTitles.length)} />
                <MetricCard label="charts" value={formatNumber(blueprint.chart_count || chartRefs.length)} />
              </div>

              {narrativeSeed || bulletSeeds.length ? (
                <div className="mt-4 rounded-[18px] border border-cyan-200/15 bg-cyan-400/6 p-4">
                  {narrativeSeed ? (
                    <p className="text-sm leading-7 text-[var(--text-strong)]">{narrativeSeed}</p>
                  ) : null}
                  {bulletSeeds.length ? (
                    <ul className="mt-3 grid gap-2 text-xs leading-6 text-[var(--muted)]">
                      {bulletSeeds.slice(0, 4).map((bullet, index) => (
                        <li key={`${blueprint.report_part_id}-bullet-${index}`}>• {bullet}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ) : null}

              <div className="mt-4 rounded-[18px] border border-white/10 bg-white/5 p-4 text-sm leading-7 text-[var(--muted)]">
                <p>
                  <span className="text-[var(--text-strong)]">Part task:</span>{" "}
                  {handoff.task || `generate_report_part:${blueprint.report_part_id}`}
                </p>
                <p>
                  <span className="text-[var(--text-strong)]">Pre-method gate:</span>{" "}
                  {blueprint.pre_method_preprocessing_status || "not reported"}
                </p>
                <p>
                  <span className="text-[var(--text-strong)]">Required outputs:</span>{" "}
                  {(handoff.required_outputs || blueprint.required_asset_kinds || []).join(", ") || "-"}
                </p>
                <p>
                  <span className="text-[var(--text-strong)]">Missing:</span>{" "}
                  {missing.length ? missing.join(", ") : "none"}
                </p>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {(blueprint.required_asset_kinds || []).map((kind) => (
                  <span className="surface-chip" key={kind}>
                    {kind}
                  </span>
                ))}
              </div>
              {tableTitles.length || chartRefs.length ? (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {tableTitles.length ? (
                    <div className="rounded-[18px] border border-white/10 bg-black/18 p-3">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">Tables in this part</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {tableTitles.slice(0, 6).map((title) => (
                          <span className="surface-chip" key={`${blueprint.report_part_id}-table-${title}`}>
                            {title}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {chartRefs.length ? (
                    <div className="rounded-[18px] border border-white/10 bg-black/18 p-3">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">Charts in this part</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {chartRefs.slice(0, 6).map((ref) => (
                          <span className="surface-chip" key={`${blueprint.report_part_id}-chart-${ref}`}>
                            {ref}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}

              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  className="surface-chip"
                  onClick={() =>
                    downloadJsonFile(
                      `${slugFilePart(blueprint.report_part_id)}-generation-blueprint.json`,
                      blueprint,
                    )
                  }
                  type="button"
                >
                  Download report-part JSON
                </button>
                {blueprint.method_evidence?.length ? (
                  <button
                    className="surface-chip"
                    onClick={() =>
                      downloadJsonFile(
                        `${slugFilePart(blueprint.report_part_id)}-method-evidence.json`,
                        blueprint.method_evidence,
                      )
                    }
                    type="button"
                  >
                    Download part evidence
                  </button>
                ) : null}
                <button
                  className="surface-chip"
                  onClick={() =>
                    void copyJsonToClipboard(buildBlueprintTaskPayload(blueprint))
                  }
                  type="button"
                >
                  Copy part payload
                </button>
                <button className="surface-chip" onClick={() => void onRerunBlueprintPart(blueprint)} disabled={isBusy || partRunBusy === blueprint.report_part_id} type="button">
                  {partRunBusy === blueprint.report_part_id ? "Rerunning..." : "Rerun part"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function RuntimePackageDownloadPanel({ result }: { result: StatsResult }) {
  const analysisData = autoAnalysisData(result);
  const downloadables = result.downloadables || [];
  const runtimeDownloads = downloadables.filter((item) =>
    [
      "runtime_package_manifest",
      "report_part_bundle",
      "method_execution_package_index",
      "single_method_json",
      "lab_report_html",
      "lab_report_markdown",
      "lab_report_revision_seed",
      "external_skill_context",
    ].includes(String(item.download_kind || "")),
  );
  const methodDownloads = analysisData.method_downloads || [];
  const manifest = runtimeDownloads.find((item) => item.download_kind === "runtime_package_manifest");
  const bundle = runtimeDownloads.find((item) => item.download_kind === "report_part_bundle");
  const index = runtimeDownloads.find((item) => item.download_kind === "method_execution_package_index");
  const methodPackageDownloads = runtimeDownloads.filter((item) => item.download_kind === "single_method_json");
  const methodPackageDisplayGroups = buildMethodPackageDisplayGroups(methodPackageDownloads);
  const manifestDisplayPolicy = isRecord(manifest?.method_display_policy) ? manifest.method_display_policy : {};
  const indexDisplayPolicy = isRecord(index?.method_display_policy) ? index.method_display_policy : {};
  const labReport = isRecord(analysisData.lab_report) ? analysisData.lab_report : {};
  const labReportHtml = runtimeDownloads.find((item) => item.download_kind === "lab_report_html");
  const labReportMarkdown = runtimeDownloads.find((item) => item.download_kind === "lab_report_markdown");
  const labReportSeed = runtimeDownloads.find((item) => item.download_kind === "lab_report_revision_seed");
  const externalSkillContextDownload = runtimeDownloads.find((item) => item.download_kind === "external_skill_context");
  const labReportHtmlPath = stringFromRecord(labReport, "html_path") || labReportHtml?.path || "";
  const labReportMarkdownPath = stringFromRecord(labReport, "markdown_path") || labReportMarkdown?.path || "";
  const labReportSeedPath = stringFromRecord(labReport, "seed_path") || labReportSeed?.path || "";
  const labReportId = stringFromRecord(labReport, "report_id") || labReportHtml?.report_id || "";
  const labReportTitle = stringFromRecord(labReport, "title") || result.title;
  const labReportStatus = stringFromRecord(labReport, "runtime_status") || (labReportHtmlPath ? "completed" : "pending");
  const labReportQualityStatus = stringFromRecord(labReport, "quality_status") || "failed";
  const labReportQualitySummary = stringFromRecord(labReport, "quality_summary") || "";
  const labReportQualityChecks = Array.isArray(labReport.quality_checks) ? labReport.quality_checks : [];
  const labReportPassedChecks =
    Number(labReport.passed_check_count || 0) ||
    labReportQualityChecks.filter((item) => isRecord(item) && String(item.status || "") === "passed").length;
  const labReportFailedChecks =
    Number(labReport.failed_check_count || 0) ||
    labReportQualityChecks.filter((item) => isRecord(item) && String(item.status || "") === "failed").length;
  const labReportEvidenceCoverage = isRecord(labReport.evidence_coverage) ? labReport.evidence_coverage : {};
  const labReportError = stringFromRecord(labReport, "error") || stringFromRecord(labReport, "catalog_error");
  const labReportLibrary = isRecord(labReport.report_library) ? labReport.report_library : undefined;
  const labReportCatalogStatus = stringFromRecord(labReport, "catalog_status") || stringFromRecord(labReportLibrary, "catalog_status");
  const revisionWorkspaceHref = stringFromRecord(labReport, "revision_workspace_href") || (labReportId ? `/revision/workspace?report_id=${encodeURIComponent(labReportId)}` : "");
  const revisionAvailable = Boolean(revisionWorkspaceHref && labReport.revision_available !== false);
  const smartMerge = analysisData.smart_merge_download || {};
  const smartMergeStatus = String(smartMerge.runtime_status || "");
  const smartMergeTaskId = String(smartMerge.codex_task_id || "");
  const smartMergeRunId = String(smartMerge.codex_run_id || "");
  const smartMergeInputPath = String(smartMerge.input_path || "");
  const smartMergeBriefPath = String(smartMerge.brief_path || "");
  const smartMergeOutputPath = String(smartMerge.expected_output_path || "");
  const smartMergeReportPath = String(smartMerge.report_path || "");
  const smartMergeError = String(smartMerge.error || "");
  const smartMergeSkipReason = String(smartMerge.skip_reason || "");
  const smartMergeMethodCount = Number(smartMerge.method_count || 0);
  const externalSkillContext = isRecord(analysisData.external_skill_context) ? analysisData.external_skill_context : {};
  const externalSkillIds = Array.isArray(analysisData.external_skill_ids)
    ? analysisData.external_skill_ids.map(String).filter(Boolean)
    : Array.isArray(externalSkillContext.skill_ids)
      ? externalSkillContext.skill_ids.map(String).filter(Boolean)
      : Array.isArray(externalSkillContextDownload?.external_skill_ids)
        ? externalSkillContextDownload.external_skill_ids.map(String).filter(Boolean)
        : [];
  const externalSkillCount =
    Number(externalSkillContext.count || 0) ||
    Number(externalSkillContextDownload?.external_skill_count || 0) ||
    externalSkillIds.length;
  const externalSkillApplicationRequired = Boolean(
    externalSkillContext.enabled ||
      smartMerge.external_skill_application_required ||
      smartMerge.external_skill_applications_required ||
      externalSkillCount > 0,
  );
  const externalSkillApplicationStatus = String(smartMerge.external_skill_application_status || "");
  const showExternalSkillRuntime = Boolean(
    externalSkillCount || externalSkillIds.length || externalSkillContextDownload || externalSkillApplicationRequired,
  );
  const showSmartMergeRuntime = Boolean(
    smartMergeStatus ||
      smartMergeTaskId ||
      smartMergeInputPath ||
      smartMergeBriefPath ||
      smartMergeOutputPath ||
      smartMergeReportPath ||
      smartMergeMethodCount > 1,
  );
  const packageCount =
    Number(manifest?.method_package_count || 0) ||
    Number(index?.method_package_count || 0) ||
    analysisData.method_execution_packages?.length ||
    methodPackageDownloads.length ||
    0;
  const displayPackageCount =
    Number(manifest?.method_display_package_count || 0) ||
    Number(index?.method_display_package_count || 0) ||
    Number(manifestDisplayPolicy.display_method_package_count || 0) ||
    Number(indexDisplayPolicy.display_method_package_count || 0) ||
    methodPackageDisplayGroups.length ||
    packageCount;
  const collapsedMethodRunCount =
    Number(manifestDisplayPolicy.collapsed_duplicate_run_count || 0) ||
    Number(indexDisplayPolicy.collapsed_duplicate_run_count || 0) ||
    Math.max(0, packageCount - displayPackageCount);
  const labReportMethodCount = Number(labReport.method_package_count || packageCount || 0);
  const labReportPartCount = Number(labReport.report_part_count || result.report_parts?.length || 0);
  const labReportChartCount = Number(labReport.chart_count || result.charts?.length || (result.chart ? 1 : 0));
  const labReportMethodCoverage = `${formatNumber(Number(labReportEvidenceCoverage.method_run_covered || 0))}/${formatNumber(Number(labReportEvidenceCoverage.method_run_total || 0))}`;
  const labReportPartCoverage = `${formatNumber(Number(labReportEvidenceCoverage.report_part_covered || 0))}/${formatNumber(Number(labReportEvidenceCoverage.report_part_total || 0))}`;
  const labReportTableRefCount = Number(labReportEvidenceCoverage.table_ref_count || 0);
  const labReportChartRefCount = Number(labReportEvidenceCoverage.chart_ref_count || 0);
  const labReportEvidenceRefCount = Number(labReportEvidenceCoverage.evidence_ref_count || 0);
  const runtimeHandoffCount =
    Number(manifest?.runtime_handoff_count || 0) ||
    methodDownloads.reduce((total, item) => total + Number(item.runtime_handoff_count || 0), 0);
  const dispatchPlanCount = Number(manifest?.dispatch_plan_count || index?.dispatch_plan_count || packageCount || 0);
  const reportPartDispatchCount = Number(manifest?.report_part_dispatch_count || index?.report_part_dispatch_count || 0);
  const runtimeDispatchCount = Number(manifest?.runtime_dispatch_count || index?.runtime_dispatch_count || dispatchPlanCount || 0);
  const preMethodStatus = manifest?.pre_method_preprocessing_status || index?.pre_method_preprocessing_status || "derived_fields_completed_before_method_routing";
  if (!runtimeDownloads.length && !methodDownloads.length && !packageCount && !labReportHtmlPath && labReportStatus !== "failed") {
    return null;
  }

  return (
    <section className="rounded-[32px] border border-amber-200/15 bg-[linear-gradient(135deg,rgba(255,190,118,0.13),rgba(255,255,255,0.045))] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Runtime package downloads</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">
            {formatNumber(displayPackageCount || methodPackageDisplayGroups.length || packageCount)} method cards shown for Codex/exec
          </h3>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-[var(--muted)]">
            Reader-facing cards collapse repeated same-name method runs, while the raw JSON package index still preserves
            every execution with field semantics, method bindings, evidence refs and runtime handoff tasks.
          </p>
          <p className="mt-2 text-xs leading-6 text-[var(--muted)]">
            Raw packages: {formatNumber(packageCount || methodPackageDownloads.length)} · collapsed duplicate runs:{" "}
            {formatNumber(collapsedMethodRunCount)} · Manifest status: {preMethodStatus} · dispatch plan entries: {formatNumber(runtimeDispatchCount || dispatchPlanCount)}
            {reportPartDispatchCount ? ` · report-part dispatch: ${formatNumber(reportPartDispatchCount)}` : ""}
          </p>
        </div>
        <button
          className="surface-chip"
          onClick={() => downloadJsonFile(`${slugFilePart(result.title || "analysis-lab")}-method-downloads.json`, methodDownloads)}
          type="button"
        >
          Download method manifest
        </button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <MetricCard label="display cards" value={formatNumber(displayPackageCount)} />
        <MetricCard label="raw packages" value={formatNumber(packageCount)} />
        <MetricCard label="download links" value={formatNumber(runtimeDownloads.length)} />
        <MetricCard label="handoffs" value={formatNumber(runtimeHandoffCount)} />
        {reportPartDispatchCount ? <MetricCard label="report dispatch" value={formatNumber(reportPartDispatchCount)} /> : null}
      </div>

      {showExternalSkillRuntime ? (
        <div className="mt-5 rounded-[22px] border border-sky-200/15 bg-sky-400/8 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.22em] text-sky-100/70">External skill runtime</p>
              <h4 className="mt-1 text-xl font-semibold text-[var(--text-strong)]">
                {formatNumber(externalSkillCount)} mounted skill{externalSkillCount === 1 ? "" : "s"} carried into this Lab run
              </h4>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--muted)]">
                The runtime export now includes the mounted skill instructions and requires smart merge outputs to record how each skill was applied.
              </p>
            </div>
            <span className="surface-chip">
              application: {externalSkillApplicationRequired ? (externalSkillApplicationStatus || "required") : "not required"}
            </span>
          </div>
          {externalSkillIds.length ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {externalSkillIds.slice(0, 12).map((skillId) => (
                <span className="surface-chip" key={skillId}>{skillId}</span>
              ))}
              {externalSkillIds.length > 12 ? <span className="surface-chip">+{formatNumber(externalSkillIds.length - 12)} more</span> : null}
            </div>
          ) : null}
          <div className="mt-4 grid gap-2 text-xs leading-6 text-[var(--muted)] md:grid-cols-2">
            <p className="break-words">context file: {externalSkillContextDownload?.name || "external_skill_context.json"}</p>
            <p className="break-words">smart merge field: external_skill_applications</p>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {externalSkillContextDownload?.path ? (
              <a className="surface-chip" href={externalSkillContextDownload.path} rel="noreferrer" target="_blank">
                Open skill context
              </a>
            ) : null}
            {smartMergeBriefPath ? (
              <a className="surface-chip" href={smartMergeBriefPath} rel="noreferrer" target="_blank">
                Open merge brief
              </a>
            ) : null}
          </div>
        </div>
      ) : null}

      {labReportHtmlPath || labReportStatus === "failed" ? (
        <div className="mt-5 overflow-hidden rounded-[28px] border border-cyan-200/18 bg-[radial-gradient(circle_at_16%_8%,rgba(103,232,249,0.18),transparent_26%),linear-gradient(135deg,rgba(8,47,73,0.52),rgba(10,10,10,0.26))] shadow-[0_28px_90px_rgba(0,0,0,0.28)]">
          <div className="grid gap-0 xl:grid-cols-[minmax(0,0.92fr)_minmax(440px,1.35fr)]">
            <div className="relative p-5 sm:p-6">
              <div className="pointer-events-none absolute inset-0 opacity-35 [background-image:linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:34px_34px]" />
              <div className="relative">
                <p className="text-[10px] uppercase tracking-[0.24em] text-cyan-100/75">Management report</p>
                <h4 className="mt-2 text-2xl font-semibold tracking-[-0.045em] text-[var(--text-strong)]">{labReportTitle}</h4>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-cyan-50/72">
                  This deterministic management report is the formal delivery entry for Analysis Lab. Smart merge can enhance it,
                  but it cannot replace the report quality gate.
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className={`surface-chip ${labReportQualityStatus === "failed" ? "border-red-300/35 bg-red-400/10 text-red-100" : "border-emerald-300/35 bg-emerald-400/10 text-emerald-100"}`}>
                    quality: {labReportQualityStatus}
                  </span>
                  <span className="surface-chip">checks: {formatNumber(labReportPassedChecks)} passed / {formatNumber(labReportFailedChecks)} failed</span>
                  <span className="surface-chip">catalog: {labReportCatalogStatus || (revisionAvailable ? "registered" : "preview")}</span>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <MetricCard label="parts" value={formatNumber(labReportPartCount)} />
                  <MetricCard label="methods" value={formatNumber(labReportMethodCount)} />
                  <MetricCard label="charts" value={formatNumber(labReportChartCount)} />
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <MetricCard label="method coverage" value={labReportMethodCoverage} />
                  <MetricCard label="part coverage" value={labReportPartCoverage} />
                  <MetricCard label="table refs" value={formatNumber(labReportTableRefCount)} />
                  <MetricCard label="chart refs" value={formatNumber(labReportChartRefCount)} />
                  <MetricCard label="evidence refs" value={formatNumber(labReportEvidenceRefCount)} />
                  <MetricCard label="runtime" value={labReportStatus} />
                </div>
                <p className="mt-4 break-words rounded-2xl border border-white/10 bg-black/22 px-4 py-3 font-mono text-xs leading-5 text-cyan-50/70">
                  {labReportId || "report id pending"}
                </p>
                {labReportQualitySummary ? (
                  <p className={`mt-4 rounded-2xl border px-4 py-3 text-xs leading-6 ${
                    labReportQualityStatus === "failed"
                      ? "border-red-300/25 bg-red-400/10 text-red-100"
                      : "border-emerald-300/20 bg-emerald-400/10 text-emerald-100"
                  }`}>
                    {labReportQualitySummary}
                  </p>
                ) : null}
                <div className="mt-4 flex flex-wrap gap-2">
                  {labReportHtmlPath ? (
                    <a className="surface-chip" href={labReportHtmlPath} rel="noreferrer" target="_blank">
                      Open management report HTML
                    </a>
                  ) : null}
                  {labReportMarkdownPath ? (
                    <a className="surface-chip" href={labReportMarkdownPath} rel="noreferrer" target="_blank">
                      Open management report Markdown
                    </a>
                  ) : null}
                  {labReportSeedPath ? (
                    <a className="surface-chip" href={labReportSeedPath} rel="noreferrer" target="_blank">
                      Open revision seed
                    </a>
                  ) : null}
                  {revisionWorkspaceHref ? (
                    <a className="surface-chip border-cyan-200/35 bg-cyan-300/16 text-cyan-50" href={revisionWorkspaceHref} rel="noreferrer" target="_blank">
                      Open revision workspace
                    </a>
                  ) : null}
                </div>
                {labReportQualityChecks.length ? (
                  <div className="mt-4 rounded-[20px] border border-white/10 bg-black/18 p-4">
                    <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">Quality checks</p>
                    <div className="mt-3 grid gap-2">
                      {labReportQualityChecks.slice(0, 8).map((item, index) => {
                        const check = isRecord(item) ? item : {};
                        const status = String(check.status || "unknown");
                        return (
                          <div
                            className={`rounded-[16px] border px-3 py-3 text-xs leading-6 ${
                              status === "failed"
                                ? "border-red-300/20 bg-red-400/8 text-red-100"
                                : "border-emerald-300/20 bg-emerald-400/8 text-emerald-100"
                            }`}
                            key={`${String(check.id || index)}-${index}`}
                          >
                            <p className="font-semibold text-[var(--text-strong)]">{String(check.label || check.id || `check-${index + 1}`)}</p>
                            <p className="mt-1">status: {status}</p>
                            <p className="mt-1 text-[var(--muted)]">{String(check.detail || "-")}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
                {labReportError ? (
                  <p className="mt-4 rounded-2xl border border-amber-200/20 bg-amber-400/10 px-4 py-3 text-xs leading-6 text-amber-50/88">
                    Lab report handoff warning: {labReportError}
                  </p>
                ) : null}
                {labReportQualityStatus === "failed" ? (
                  <p className="mt-4 rounded-2xl border border-red-300/25 bg-red-400/10 px-4 py-3 text-xs leading-6 text-red-100">
                    This report was generated, but it failed the deterministic quality gate and should not be treated as a final delivery.
                  </p>
                ) : null}
              </div>
            </div>
            <div className="min-h-[420px] border-t border-white/10 bg-[#f8f1e7] xl:border-l xl:border-t-0">
              {labReportHtmlPath ? (
                <iframe
                  className="h-[620px] w-full bg-[#f8f1e7]"
                  loading="lazy"
                  sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox"
                  src={labReportHtmlPath}
                  title="Analysis Lab report preview"
                />
              ) : (
                <div className="flex h-full min-h-[420px] items-center justify-center p-8 text-center text-slate-700">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Preview unavailable</p>
                    <p className="mt-3 max-w-md text-sm leading-7">
                      The deterministic management report was generated without a usable HTML preview. Review the warning state and rerun before treating it as a final delivery.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {showSmartMergeRuntime ? (
        <div className="mt-5 rounded-[22px] border border-emerald-200/15 bg-emerald-400/8 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.22em] text-emerald-100/70">Smart merge enhancement</p>
              <h4 className="mt-1 text-xl font-semibold text-[var(--text-strong)]">
                {smartMergeTaskId ? "Smart merge task submitted to Codex CLI" : "Smart merge enhancement pipeline"}
              </h4>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                Smart merge is an enhancement layer only. It can enrich the deterministic management report, but it cannot replace the formal report entry or its quality gate.
              </p>
            </div>
            <span className="surface-chip">status: {smartMergeStatus || "unknown"}</span>
          </div>
          <div className="mt-4 grid gap-2 text-xs leading-6 text-[var(--muted)] md:grid-cols-2">
            <p className="break-words">task id: {smartMergeTaskId || "-"}</p>
            <p className="break-words">run id: {smartMergeRunId || "-"}</p>
            <p className="break-words">methods: {formatNumber(smartMergeMethodCount)}</p>
            <p className="break-words">expected output: {smartMergeOutputPath || "-"}</p>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {smartMergeInputPath ? (
              <a className="surface-chip" href={smartMergeInputPath} rel="noreferrer" target="_blank">
                Open smart merge input
              </a>
            ) : null}
            {smartMergeBriefPath ? (
              <a className="surface-chip" href={smartMergeBriefPath} rel="noreferrer" target="_blank">
                Open smart merge brief
              </a>
            ) : null}
            {smartMergeOutputPath ? (
              <a className="surface-chip" href={smartMergeOutputPath} rel="noreferrer" target="_blank">
                Open expected result
              </a>
            ) : null}
            {smartMergeReportPath ? (
              <a className="surface-chip" href={smartMergeReportPath} rel="noreferrer" target="_blank">
                Open smart merge report
              </a>
            ) : null}
          </div>
          {smartMergeError || smartMergeSkipReason ? (
            <p className="mt-3 rounded-2xl border border-amber-200/15 bg-amber-400/8 px-4 py-3 text-xs leading-6 text-amber-50/85">
              {smartMergeError || smartMergeSkipReason}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 xl:grid-cols-2">
        {[manifest, bundle, index, externalSkillContextDownload, labReportHtml, labReportMarkdown, labReportSeed].filter(Boolean).map((item) => (
          <a
            className="rounded-[18px] border border-white/10 bg-black/22 p-4 transition-colors hover:border-white/20 hover:bg-white/8"
            href={item?.path || "#"}
            key={item?.name}
            rel="noreferrer"
            target="_blank"
          >
            <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{item?.download_kind}</p>
            <h4 className="mt-1 break-words text-lg font-semibold text-[var(--text-strong)]">{item?.name}</h4>
            <p className="mt-2 text-xs leading-6 text-[var(--muted)]">{item?.purpose || item?.path}</p>
          </a>
        ))}
      </div>

      {methodPackageDisplayGroups.length ? (
        <div className="mt-5 grid gap-3 xl:grid-cols-3">
          {methodPackageDisplayGroups.slice(0, 24).map((group) => (
            <a
              className="rounded-[18px] border border-white/10 bg-black/22 p-4 transition-colors hover:border-white/20 hover:bg-white/8"
              href={group.primary.path}
              key={`${group.key}-${group.primary.package_ref || group.primary.path}`}
              rel="noreferrer"
              target="_blank"
            >
              <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">
                {group.family || group.primary.method_id || "method package"}
              </p>
              <h4 className="mt-1 break-words text-sm font-semibold text-[var(--text-strong)]">{group.label}</h4>
              <div className="mt-3 space-y-1 text-xs leading-5 text-[var(--muted)]">
                <p>runs represented: {formatNumber(group.totalRuns)}</p>
                <p>collapsed duplicates: {formatNumber(group.collapsedRuns)}</p>
                <p>handoffs: {formatNumber(group.items.reduce((total, item) => total + Number(item.runtime_handoff_count || 0), 0))}</p>
                <p className="break-words">package_ref: {group.packageRefs[0] || group.primary.package_ref || "-"}</p>
                {group.packageRefs.length > 1 ? <p>raw packages preserved: {formatNumber(group.packageRefs.length)}</p> : null}
              </div>
            </a>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function GenericResultCanvas({ result }: { result: WorkspaceResult }) {
  return (
    <>
      <section className="rounded-[34px] border border-white/10 bg-white/5 p-7">
        <p className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">{result.mode}</p>
        <h3 className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">{result.title}</h3>
        <p className="mt-3 text-sm text-[var(--muted)]">{result.datasetName} · {new Date(result.createdAt).toLocaleString()}</p>
      </section>
      <RawPayload payload={result.payload} />
    </>
  );
}

function DataTable({ table }: { table: GenericTable }) {
  if (!table.columns.length || !table.rows.length) {
    return <div className="rounded-[22px] border border-dashed border-white/10 bg-black/18 px-4 py-8 text-sm text-[var(--muted)]">暂无表格。</div>;
  }
  return (
    <div className="overflow-hidden rounded-[22px] border border-white/10 bg-black/18">
      {table.title ? <p className="border-b border-white/10 px-4 py-3 text-sm font-semibold text-[var(--text-strong)]">{table.title}</p> : null}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/6 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            <tr>{table.columns.map((column) => <th className="px-4 py-3 font-medium" key={column}>{column}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-white/8">
            {table.rows.slice(0, 80).map((row, rowIndex) => (
              <tr key={`${rowIndex}-${table.columns[0]}`}>
                {table.columns.map((column) => <td className="max-w-[360px] truncate px-4 py-3 text-[var(--muted)]" key={column}>{formatValue(row[column])}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RawPayload({ payload }: { payload: unknown }) {
  return (
    <section className="rounded-[32px] border border-white/10 bg-[#020404]/70 p-6">
      <p className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Raw payload inspection</p>
      <pre className="mt-4 max-h-[760px] overflow-auto whitespace-pre-wrap rounded-[22px] border border-white/10 bg-black/45 p-4 font-mono text-xs leading-6 text-[#d9e6df]">
        {stringifySafe(payload)}
      </pre>
    </section>
  );
}
