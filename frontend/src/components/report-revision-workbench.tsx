"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useEffectEvent, useMemo, useRef, useState } from "react";
import { ArrowLeft, FileText, LoaderCircle, Paperclip, Plus, RefreshCw, Search, Send, Square } from "lucide-react";

import { apiRequest, apiUrl, isApiAbortError } from "@/lib/api";
import type {
  ReportAttachment,
  ReportAgentDiffFile,
  ReportAgentEvent,
  ReportAgentFile,
  ReportAgentSession,
  ReportAnnotation,
  ReportCatalogBusinessProfileStat,
  ReportCatalogDetail,
  ReportCatalogItem,
  ReportCatalogResponse,
  ReportCatalogDatasetStat,
  ReportCatalogIndexStatus,
  RuntimeProcessItem,
} from "@/lib/types";

import { CodexTimeline } from "./revision/codex-timeline";
import { ReportPreviewPane } from "./revision/report-preview-pane";
import { ResizableWorkbenchLayout } from "./revision/resizable-workbench-layout";
import { RuntimeActivityRing } from "./revision/runtime-activity-ring";

type Props = {
  backHref?: string;
  onBack?: () => void;
  initialReportId?: string;
  initialSessionId?: string;
  workspaceMode?: "library" | "session";
};

type CodexNativeHealth = {
  available: boolean;
  resolved_path?: string;
  version?: string;
  app_server_available?: boolean;
  error?: string;
  portable_hint?: string;
};

type ResumeProcessResponse = {
  action?: string;
  kind?: string;
  id?: string;
  pipeline_job_id?: string;
  pipeline_type?: string;
  resume_strategy?: string;
  resume_issue_kind?: string;
  repair_rule_id?: string;
  retry_stage_id?: string;
  rollback_stage_id?: string;
  blocking_missing_inputs?: string[];
  result?: {
    session?: ReportAgentSession;
    events?: ReportAgentEvent[];
    missing_required_assets?: string[];
  };
  processes: RuntimeProcessItem[];
};

type OpenReportOptions = {
  forceNewSession?: boolean;
  preserveDetail?: boolean;
  targetSessionId?: string;
};

type LoadReportsOptions = {
  silent?: boolean;
  refreshIndex?: boolean;
};

const TURN_RUNNING_STATUSES = new Set(["queued", "running", "cancelling", "verifying", "auto_repairing"]);
const RUNTIME_ACTIVE_STATUSES = new Set(["queued", "running", "starting", "cancelling"]);
const STALE_RUNTIME_STATUSES = new Set(["stale_queued", "stale_running", "stale_turn", "stale_cancelling"]);
const ACTIONABLE_RUNTIME_STATUSES = new Set(["failed", "blocked", "cancelled", "timed_out", "error"]);
const RECENT_RUNTIME_STATUSES = new Set(["completed", "available", "active"]);
const STARTABLE_RUNTIME_STATUSES = new Set(["not_started"]);
const TURN_TERMINAL_STATUSES = new Set([
  "completed",
  "failed",
  "cancelled",
  "timed_out",
  "failed_scope_miss",
  "failed_partial_application",
  "failed_scope_violation",
  "failed_pdf_render",
]);
const REPORT_CATALOG_TIMEOUT_MS = 45000;
const REPORT_DETAIL_TIMEOUT_MS = 20000;
const OPTIONAL_REQUEST_TIMEOUT_MS = 9000;
const PROCESS_REQUEST_TIMEOUT_MS = 15000;
const REPORT_CATALOG_PAGE_SIZE = 20;
const REPORT_CATALOG_MAX_PAGES = 200;
const REPORT_CATALOG_BACKGROUND_PAGE_LIMIT = 1;
const REPORT_CATALOG_REFRESH_POLL_MS = 4000;
const REPORT_CATALOG_TIMEOUT_RETRY_MS = 2500;
const EVENT_POLL_FALLBACK_MS = 12000;
const SELECTED_PROCESS_POLL_MS = 15000;
const ACTIVE_PROCESS_POLL_MS = 30000;
const ACTIVE_PROCESS_LIMIT = 30;
const SEARCH_DEBOUNCE_MS = 350;
const INTERNAL_SESSION_TITLE_MARKERS = [
  "smoke",
  "retest",
  "confidence-smoke",
  "native-bridge-retest",
  "native composer post smoke",
  "final native startup smoke",
  "cancel regression",
  "revision follow-up",
];

async function swallowOptionalRequest<T>(request: Promise<T>, fallback: T): Promise<T> {
  try {
    return await request;
  } catch {
    return fallback;
  }
}

function turnStatusLabel(status: string | undefined) {
  const labels: Record<string, string> = {
    queued: "已排队",
    running: "运行中",
    cancelling: "停止中",
    verifying: "验收中",
    auto_repairing: "自动纠偏中",
    completed: "已完成",
    failed: "失败",
    failed_scope_miss: "未命中要求",
    failed_partial_application: "部分命中失败",
    failed_scope_violation: "越界修改",
    cancelled: "已取消",
    timed_out: "超时",
    active: "active",
    stale_queued: "排队已停滞",
    stale_running: "运行已停滞",
    stale_turn: "引导已停滞",
    stale_cancelling: "取消已停滞",
  };
  return labels[String(status || "")] || String(status || "");
}

function formatTime(value: string | undefined) {
  if (!value) {
    return "";
  }
  try {
    return new Intl.DateTimeFormat("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function timeValue(value: string | undefined) {
  if (!value) {
    return 0;
  }
  const parsed = new Date(value).getTime();
  return Number.isFinite(parsed) ? parsed : 0;
}

function titleAlreadyContainsReportId(title: string | undefined, reportId: string | undefined) {
  const normalizedTitle = String(title || "").toLowerCase();
  const normalizedId = String(reportId || "").toLowerCase();
  return Boolean(normalizedTitle && normalizedId && normalizedTitle.includes(normalizedId));
}

function isFreshRuntimeTimestamp(value: string | undefined, ttlMs = 20 * 60 * 1000) {
  const timestamp = timeValue(value);
  return timestamp > 0 && Date.now() - timestamp <= ttlMs;
}

type ReportRuntimeSortState = {
  priority: number;
  label: string;
  status: string;
  updatedAt: string;
  processKind?: string;
};

function runtimeStateFromProcess(item: RuntimeProcessItem): ReportRuntimeSortState | null {
  const status = String(item.observed_status || item.status || "");
  if (!item.report_id) {
    return null;
  }
  if (item.is_active && item.kind === "report_agent_turn" && TURN_RUNNING_STATUSES.has(status)) {
    return { priority: 0, label: item.display_status || "引导中", status, updatedAt: item.updated_at || item.started_at || "", processKind: item.kind };
  }
  if (item.is_active && ["pipeline", "report_task", "codex_run_task"].includes(item.kind) && RUNTIME_ACTIVE_STATUSES.has(status)) {
    return { priority: 1, label: item.display_status || "续跑中", status, updatedAt: item.updated_at || item.started_at || "", processKind: item.kind };
  }
  if (item.is_stale && item.can_resume && STALE_RUNTIME_STATUSES.has(status)) {
    return { priority: 2, label: item.display_status || "已停滞，可续跑", status, updatedAt: item.updated_at || item.started_at || "", processKind: item.kind };
  }
  if (item.can_resume && ACTIONABLE_RUNTIME_STATUSES.has(status)) {
    return { priority: 2, label: item.display_status || "可续跑", status, updatedAt: item.updated_at || item.started_at || "", processKind: item.kind };
  }
  if (item.can_resume && STARTABLE_RUNTIME_STATUSES.has(status)) {
    return {
      priority: 2,
      label: item.resume_label || item.display_status || "可启动",
      status,
      updatedAt: item.updated_at || item.started_at || "",
      processKind: item.kind,
    };
  }
  if (RECENT_RUNTIME_STATUSES.has(status)) {
    return { priority: 3, label: "最近完成", status, updatedAt: item.updated_at || item.started_at || "", processKind: item.kind };
  }
  return null;
}

function runtimeStateFromReportSession(item: ReportCatalogItem): ReportRuntimeSortState | null {
  if (isInternalRevisionSession(item.latest_revision_session)) {
    return null;
  }
  const turnStatus = item.latest_revision_session?.current_turn_status || item.latest_revision_session?.current_turn?.status || "";
  if (!TURN_RUNNING_STATUSES.has(turnStatus)) {
    return null;
  }
  const updatedAt = item.latest_revision_session?.updated_at || item.latest_revision_session?.created_at || "";
  if (!isFreshRuntimeTimestamp(updatedAt)) {
    return null;
  }
  return {
    priority: 0,
    label: "引导中",
    status: turnStatus,
    updatedAt,
    processKind: "report_agent_turn",
  };
}

function turnStatusTone(status: string | undefined) {
  if (!status) {
    return "border-white/10 text-[var(--muted)]";
  }
  if (TURN_RUNNING_STATUSES.has(status)) {
    return "border-cyan-300/25 text-cyan-50";
  }
  if (status === "completed") {
    return "border-emerald-300/25 text-emerald-50";
  }
  if (status === "failed" || status === "cancelled" || status === "timed_out" || String(status || "").startsWith("failed_")) {
    return "border-red-300/30 text-red-100";
  }
  return "border-white/10 text-[var(--muted)]";
}

function newestCursor(events: ReportAgentEvent[]) {
  return Math.max(0, ...events.map((event) => Number(event.event_id || 0)));
}

function isInternalRevisionSession(session: ReportAgentSession | null | undefined) {
  const title = String(session?.title || "").trim().toLowerCase();
  if (!title) {
    return true;
  }
  if (INTERNAL_SESSION_TITLE_MARKERS.some((marker) => title.includes(marker))) {
    return true;
  }
  return /^[?？�\s]+$/.test(title);
}

function pickPreferredRevisionSession(detail: ReportCatalogDetail): ReportAgentSession | null {
  const sessions = [
    ...(detail.latest_revision_session ? [detail.latest_revision_session] : []),
    ...(detail.revision_sessions || []),
  ].filter((item) => item && !isInternalRevisionSession(item as ReportAgentSession)) as ReportAgentSession[];
  if (!sessions.length) {
    return null;
  }
  const deduped = Array.from(new Map(sessions.map((item) => [item.session_id, item])).values());
  deduped.sort((left, right) => {
    const leftTurns = left.turns?.length || 0;
    const rightTurns = right.turns?.length || 0;
    const leftRunning = TURN_RUNNING_STATUSES.has(left.current_turn_status || left.current_turn?.status || "");
    const rightRunning = TURN_RUNNING_STATUSES.has(right.current_turn_status || right.current_turn?.status || "");
    const leftPublished = left.published_versions?.length || 0;
    const rightPublished = right.published_versions?.length || 0;
    const leftGuidance = left.guidance_injections?.length || 0;
    const rightGuidance = right.guidance_injections?.length || 0;
    const leftCurrent = left.current_turn?.turn_id || left.current_turn?.user_message ? 1 : 0;
    const rightCurrent = right.current_turn?.turn_id || right.current_turn?.user_message ? 1 : 0;
    const leftUpdated = left.updated_at || left.created_at || "";
    const rightUpdated = right.updated_at || right.created_at || "";
    return (
      Number(rightRunning) - Number(leftRunning) ||
      rightTurns - leftTurns ||
      rightPublished - leftPublished ||
      rightGuidance - leftGuidance ||
      rightCurrent - leftCurrent ||
      rightUpdated.localeCompare(leftUpdated)
    );
  });
  return deduped[0] || null;
}

function buildWorkspaceHref(reportId: string, sessionId: string) {
  const query = new URLSearchParams({
    report_id: reportId,
    session_id: sessionId,
  });
  return `/revision/workspace?${query.toString()}`;
}

function statusMessageForTurnStatus(status: string | undefined) {
  const normalized = String(status || "");
  if (!normalized) {
    return "";
  }
  if (normalized === "completed") {
    return "本轮已完成，PDF 草稿已生成；可以继续提交新的修改意见或发布修订版。";
  }
  if (normalized === "cancelled") {
    return "本轮已停止，可以继续提交新的修改意见。";
  }
  if (normalized === "timed_out") {
    return "本轮处理超时，可以继续补充需求或重新发起。";
  }
  if (normalized === "failed" || normalized.startsWith("failed_")) {
    return "本轮未通过验收或执行失败，可以继续调整需求后再发起。";
  }
  return "";
}

function buildSessionSkeleton(reportId: string, sessionId: string): ReportAgentSession {
  return {
    session_id: sessionId,
    report_id: reportId,
    status: "active",
    session_status: "active",
    current_turn_status: "",
    current_turn: {
      turn_id: "",
      status: "",
      user_message: "",
      started_at: "",
      completed_at: "",
      native_turn_id: "",
      task_id: "",
      run_id: "",
      final_scope_status: "",
    },
    turns: [],
    title: "后续改造",
    mode: "native_app_server",
    codex_thread_id: "",
    active_turn_id: "",
    native_connection_status: "starting",
    native_protocol_error: "",
    guidance_injections: [],
    published_versions: [],
  };
}

export function ReportRevisionWorkbench({
  backHref = "/",
  onBack,
  initialReportId = "",
  initialSessionId = "",
  workspaceMode = "library",
}: Props) {
  const router = useRouter();
  const [reports, setReports] = useState<ReportCatalogItem[]>([]);
  const [totalReportCount, setTotalReportCount] = useState(0);
  const [catalogIndexStatus, setCatalogIndexStatus] = useState<ReportCatalogIndexStatus | null>(null);
  const [datasetStats, setDatasetStats] = useState<ReportCatalogDatasetStat[]>([]);
  const [businessProfileStats, setBusinessProfileStats] = useState<ReportCatalogBusinessProfileStat[]>([]);
  const [selectedReportId, setSelectedReportId] = useState("");
  const [detail, setDetail] = useState<ReportCatalogDetail | null>(null);
  const [session, setSession] = useState<ReportAgentSession | null>(null);
  const [events, setEvents] = useState<ReportAgentEvent[]>([]);
  const [files, setFiles] = useState<ReportAgentFile[]>([]);
  const [diffFiles, setDiffFiles] = useState<ReportAgentDiffFile[]>([]);
  const [annotations, setAnnotations] = useState<ReportAnnotation[]>([]);
  const [attachments, setAttachments] = useState<ReportAttachment[]>([]);
  const [processes, setProcesses] = useState<RuntimeProcessItem[]>([]);
  const [activeProcesses, setActiveProcesses] = useState<RuntimeProcessItem[]>([]);
  const [cursor, setCursor] = useState(0);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("\u6b63\u5728\u8f7d\u5165\u62a5\u544a\u5e93...");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isProcessBusy, setIsProcessBusy] = useState(false);
  const [isUploadingAttachment, setIsUploadingAttachment] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [streamState, setStreamState] = useState<"idle" | "connecting" | "open" | "retrying">("idle");
  const [streamRetryToken, setStreamRetryToken] = useState(0);
  const [codexHealth, setCodexHealth] = useState<CodexNativeHealth | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [selectedBusinessProfile, setSelectedBusinessProfile] = useState("");
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [catalogSortBy, setCatalogSortBy] = useState<"updated_at" | "generated_at">("updated_at");
  const eventSourceRef = useRef<EventSource | null>(null);
  const cursorRef = useRef(0);
  const catalogRefreshTimerRef = useRef<number | null>(null);
  const reportLoadRequestRef = useRef(0);
  const reportLoadAbortRef = useRef<AbortController | null>(null);
  const reportOpenRequestRef = useRef(0);
  const processLoadKeyRef = useRef("");
  const activeProcessLoadRef = useRef(false);
  const terminalRefreshKeyRef = useRef("");
  const workspaceSyncRef = useRef(false);
  const selectedReportIdRef = useRef("");
  const sessionIdRef = useRef("");

  const sessionId = session?.session_id || "";
  const sessionStatus = session?.session_status || session?.status || "";
  const currentTurnStatus = session?.current_turn_status || session?.current_turn?.status || "";
  const currentTurn = session?.current_turn || null;
  const guidanceCount = session?.guidance_injections?.length || 0;
  const isTurnRunning = TURN_RUNNING_STATUSES.has(currentTurnStatus);
  const nativeStatus = session?.native_connection_status || "";
  const currentTurnScopeStatus = String(currentTurn?.final_scope_status || "");
  const verificationExists = Boolean(currentTurn?.revision_verification && Object.keys(currentTurn.revision_verification).length);
  const canPublish =
    Boolean(session?.preview_url || session?.preview_artifact) &&
    !isPublishing &&
    !isTurnRunning &&
    (!verificationExists || currentTurnScopeStatus === "passed");

  function isCurrentReportSession(reportId: string, nextSessionId = "") {
    return selectedReportIdRef.current === reportId && (!nextSessionId || sessionIdRef.current === nextSessionId);
  }

  const revisionQuickPrompts = useMemo(
    () => [
      {
        label: "结构级大改",
        prompt:
          "对整份报告做结构级大改：重排首页、章节顺序、摘要和正文表达，让它更像管理层可读的正式报告。保持所有 deterministic 数字不变，不新增无证据指标，Markdown 和 HTML 同步更新。",
      },
      {
        label: "首页重写",
        prompt:
          "大幅重写首页：改成强结论、关键对象、行动项和检查点前置的管理摘要。保持所有数字不变，不改后续章节的事实口径。",
      },
      {
        label: "图注业务化",
        prompt:
          "把报告里的图题和图注整体改成业务语言，去掉 runtime 命名和技术口吻。不得改变图表数值、对象名称和证据口径。",
      },
    ],
    [],
  );

  const reportRuntimeStateById = useMemo(() => {
    const stateByReport = new Map<string, ReportRuntimeSortState>();
    for (const process of activeProcesses) {
      const reportId = process.report_id || "";
      const nextState = runtimeStateFromProcess(process);
      if (!reportId || !nextState) {
        continue;
      }
      const currentState = stateByReport.get(reportId);
      if (
        !currentState ||
        nextState.priority < currentState.priority ||
        (nextState.priority === currentState.priority && timeValue(nextState.updatedAt) > timeValue(currentState.updatedAt))
      ) {
        stateByReport.set(reportId, nextState);
      }
    }
    for (const report of reports) {
      const fallbackState = runtimeStateFromReportSession(report);
      if (!fallbackState) {
        continue;
      }
      const currentState = stateByReport.get(report.report_id);
      if (
        !currentState ||
        fallbackState.priority < currentState.priority ||
        (fallbackState.priority === currentState.priority && timeValue(fallbackState.updatedAt) > timeValue(currentState.updatedAt))
      ) {
        stateByReport.set(report.report_id, fallbackState);
      }
    }
    return stateByReport;
  }, [activeProcesses, reports]);

  const sortedReports = useMemo(() => {
    return [...reports].sort((left, right) => {
      const leftState = reportRuntimeStateById.get(left.report_id);
      const rightState = reportRuntimeStateById.get(right.report_id);
      const leftPriority = leftState?.priority ?? 4;
      const rightPriority = rightState?.priority ?? 4;
      if (leftPriority !== rightPriority) {
        return leftPriority - rightPriority;
      }
      const leftRuntimeAt = timeValue(leftState?.updatedAt);
      const rightRuntimeAt = timeValue(rightState?.updatedAt);
      if (leftRuntimeAt !== rightRuntimeAt) {
        return rightRuntimeAt - leftRuntimeAt;
      }
      return timeValue(right.generated_at || right.updated_at) - timeValue(left.generated_at || left.updated_at);
    });
  }, [reportRuntimeStateById, reports]);

  const reportCountsLabel = useMemo(() => {
    if (!reports.length && !totalReportCount) {
      return "0 份";
    }
    if (totalReportCount > reports.length) {
      return `${reports.length} / ${totalReportCount} 份`;
    }
    return `${reports.length} 份`;
  }, [reports.length, totalReportCount]);

  async function loadReports(options: LoadReportsOptions = {}) {
    const { silent = false } = options;
    if (catalogRefreshTimerRef.current !== null && typeof window !== "undefined") {
      window.clearTimeout(catalogRefreshTimerRef.current);
      catalogRefreshTimerRef.current = null;
    }
    const requestId = reportLoadRequestRef.current + 1;
    reportLoadRequestRef.current = requestId;
    reportLoadAbortRef.current?.abort();
    const abortController = new AbortController();
    reportLoadAbortRef.current = abortController;
    setIsLoading(true);
    setCatalogError("");
    if (!silent) {
      setStatus("正在载入报告库...");
    }
    try {
      const buildQuery = (offset: number) => {
        const query = new URLSearchParams({
          limit: String(REPORT_CATALOG_PAGE_SIZE),
          offset: String(offset),
          sort_by: catalogSortBy,
        });
        if (searchKeyword.trim()) {
          query.set("q", searchKeyword.trim());
        }
        if (selectedDatasetId) {
          query.set("dataset_id", selectedDatasetId);
        }
        if (selectedBusinessProfile) {
          query.set("business_profile", selectedBusinessProfile);
        }
        if (options.refreshIndex) {
          query.set("refresh_index", "true");
        }
        return query;
      };
      const firstPayload = await apiRequest<ReportCatalogResponse>(`/api/reports?${buildQuery(0).toString()}`, {
        timeoutMs: REPORT_CATALOG_TIMEOUT_MS,
        signal: abortController.signal,
      });
      if (reportLoadRequestRef.current !== requestId) {
        return;
      }
      const totalCount = Number(firstPayload.total_count || 0);
      const loadedReports = [...(firstPayload.reports || [])];
      const applyCatalogState = (payload: ReportCatalogResponse, nextReports: ReportCatalogItem[]) => {
        const indexStatus = payload.index_status || null;
        const indexedCount = Number(indexStatus?.indexed_report_count || 0);
        const knownCount = Number(indexStatus?.known_report_count || 0);
        const needsBackgroundRefresh =
          Boolean(indexStatus?.is_refreshing) ||
          Boolean(indexStatus?.is_partial) ||
          (knownCount > 0 && indexedCount > 0 && indexedCount < knownCount);
        const dedupedReports = Array.from(new Map(nextReports.map((report) => [report.report_id, report])).values());
        setReports(dedupedReports);
        setTotalReportCount(totalCount);
        setCatalogIndexStatus(indexStatus);
        setDatasetStats(payload.stats?.datasets || []);
        setBusinessProfileStats(payload.stats?.business_profiles || []);
        return {
          indexedCount,
          knownCount,
          needsBackgroundRefresh,
          loadedCount: dedupedReports.length,
        };
      };
      const totalPages = Math.min(
        REPORT_CATALOG_MAX_PAGES,
        Math.max(1, Math.ceil(totalCount / Math.max(REPORT_CATALOG_PAGE_SIZE, 1))),
      );
      const { indexedCount, knownCount, needsBackgroundRefresh, loadedCount } = applyCatalogState(firstPayload, loadedReports);
      if (needsBackgroundRefresh && typeof window !== "undefined") {
        catalogRefreshTimerRef.current = window.setTimeout(() => {
          void loadReports({ silent });
        }, REPORT_CATALOG_REFRESH_POLL_MS);
      }
      void loadActiveProcesses();
      if (!silent) {
        setStatus(
          needsBackgroundRefresh
            ? `报告库已快速加载，正在后台补全历史索引（${indexedCount}${knownCount ? ` / ${knownCount}` : ""}）。`
            : loadedCount
              ? "报告库已加载。支持按关键词、业务画像和数据集筛选。"
              : "\u8fd8\u6ca1\u6709\u627e\u5230\u53ef\u7ee7\u7eed\u6539\u9020\u7684\u5386\u53f2\u62a5\u544a\u3002",
        );
      }
      if (totalPages > 1) {
        void (async () => {
          try {
            const pageStop = Math.min(totalPages, 1 + REPORT_CATALOG_BACKGROUND_PAGE_LIMIT);
            for (let page = 1; page < pageStop; page += 1) {
              const nextPayload = await apiRequest<ReportCatalogResponse>(`/api/reports?${buildQuery(page * REPORT_CATALOG_PAGE_SIZE).toString()}`, {
                timeoutMs: REPORT_CATALOG_TIMEOUT_MS,
                signal: abortController.signal,
              });
              if (reportLoadRequestRef.current !== requestId) {
                return;
              }
              const nextReports = nextPayload.reports || [];
              if (!nextReports.length) {
                break;
              }
              loadedReports.push(...nextReports);
              applyCatalogState(nextPayload, loadedReports);
              if (loadedReports.length >= totalCount) {
                break;
              }
            }
          } catch {
            // Keep the first page visible even if background pagination is interrupted.
          }
        })();
      }
    } catch (error) {
      if (reportLoadRequestRef.current !== requestId) {
        return;
      }
      if (isApiAbortError(error)) {
        return;
      }
      const messageText = error instanceof Error ? error.message : String(error || "未知错误");
      setCatalogError(messageText);
      if (!silent) {
        if (messageText.includes("请求超时") && typeof window !== "undefined") {
          setStatus("报告库首次加载较慢，正在自动重试...");
          catalogRefreshTimerRef.current = window.setTimeout(() => {
            void loadReports({ silent: false });
          }, REPORT_CATALOG_TIMEOUT_RETRY_MS);
        } else {
          setStatus(`报告库加载失败：${messageText}`);
        }
      }
    } finally {
      if (reportLoadRequestRef.current === requestId) {
        setIsLoading(false);
      }
      if (reportLoadAbortRef.current === abortController) {
        reportLoadAbortRef.current = null;
      }
    }
  }

  async function refreshDetail(reportId = selectedReportId) {
    if (!reportId) {
      return null;
    }
    const reportDetail = await apiRequest<ReportCatalogDetail>(`/api/reports/${reportId}`, { timeoutMs: REPORT_DETAIL_TIMEOUT_MS });
    if (selectedReportIdRef.current && selectedReportIdRef.current !== reportId) {
      return reportDetail;
    }
    setDetail(reportDetail);
    return reportDetail;
  }

  async function loadSessionArtifacts(nextSession = session, reportId = selectedReportId) {
    if (!nextSession || !reportId) {
      setFiles([]);
      setDiffFiles([]);
      return;
    }
    const requestSessionId = nextSession.session_id;
    const [filePayload, diffPayload] = await Promise.all([
      apiRequest<{ session: ReportAgentSession; files: ReportAgentFile[] }>(
        `/api/report-agent-sessions/${nextSession.session_id}/files?report_id=${encodeURIComponent(reportId)}`,
        { timeoutMs: OPTIONAL_REQUEST_TIMEOUT_MS },
      ),
      apiRequest<{ session: ReportAgentSession; changed_files: ReportAgentDiffFile[] }>(
        `/api/report-agent-sessions/${nextSession.session_id}/diff?report_id=${encodeURIComponent(reportId)}`,
        { timeoutMs: OPTIONAL_REQUEST_TIMEOUT_MS },
      ),
    ]);
    if (!isCurrentReportSession(reportId, requestSessionId)) {
      return;
    }
    setFiles(filePayload.files || []);
    setDiffFiles(diffPayload.changed_files || []);
    sessionIdRef.current = (diffPayload.session || filePayload.session || nextSession).session_id;
    setSession(diffPayload.session || filePayload.session || nextSession);
  }

  async function loadAnnotations(nextSession = session, reportId = selectedReportId) {
    if (!nextSession || !reportId) {
      setAnnotations([]);
      return;
    }
    const requestSessionId = nextSession.session_id;
    const payload = await apiRequest<{ session: ReportAgentSession; annotations: ReportAnnotation[] }>(
      `/api/report-agent-sessions/${nextSession.session_id}/annotations?report_id=${encodeURIComponent(reportId)}`,
      { timeoutMs: OPTIONAL_REQUEST_TIMEOUT_MS },
    );
    if (!isCurrentReportSession(reportId, requestSessionId)) {
      return;
    }
    setAnnotations(payload.annotations || []);
    sessionIdRef.current = (payload.session || nextSession).session_id;
    setSession(payload.session || nextSession);
  }

  async function loadAttachments(nextSession = session, reportId = selectedReportId) {
    if (!nextSession || !reportId) {
      setAttachments([]);
      return;
    }
    const requestSessionId = nextSession.session_id;
    const payload = await apiRequest<{ session: ReportAgentSession; attachments: ReportAttachment[] }>(
      `/api/report-agent-sessions/${nextSession.session_id}/attachments?report_id=${encodeURIComponent(reportId)}`,
      { timeoutMs: OPTIONAL_REQUEST_TIMEOUT_MS },
    );
    if (!isCurrentReportSession(reportId, requestSessionId)) {
      return;
    }
    setAttachments(payload.attachments || []);
    sessionIdRef.current = (payload.session || nextSession).session_id;
    setSession(payload.session || nextSession);
  }

  async function loadProcesses(reportId = selectedReportId, nextSession = session) {
    if (!reportId) {
      setProcesses([]);
      return;
    }
    const requestSessionId = nextSession?.session_id || "";
    const requestKey = `${reportId}:${nextSession?.session_id || ""}`;
    if (processLoadKeyRef.current === requestKey) {
      return;
    }
    processLoadKeyRef.current = requestKey;
    setIsProcessBusy(true);
    try {
      const sessionQuery = nextSession?.session_id ? `&session_id=${encodeURIComponent(nextSession.session_id)}` : "";
      const payload = await apiRequest<{ processes: RuntimeProcessItem[] }>(
        `/api/runtime/processes?report_id=${encodeURIComponent(reportId)}${sessionQuery}`,
        { timeoutMs: PROCESS_REQUEST_TIMEOUT_MS },
      );
      if (!isCurrentReportSession(reportId, requestSessionId)) {
        return;
      }
      setProcesses(payload.processes || []);
    } finally {
      if (processLoadKeyRef.current === requestKey) {
        processLoadKeyRef.current = "";
      }
      setIsProcessBusy(false);
    }
  }

  async function loadProcessesSafely(reportId = selectedReportId, nextSession = session) {
    try {
      await loadProcesses(reportId, nextSession);
      return true;
    } catch {
      setProcesses([]);
      return false;
    }
  }

  async function loadCodexHealth() {
    try {
      const health = await apiRequest<CodexNativeHealth>("/api/runtime/codex-health", {
        timeoutMs: OPTIONAL_REQUEST_TIMEOUT_MS,
      });
      setCodexHealth(health);
    } catch (error) {
      setCodexHealth({
        available: false,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  async function loadActiveProcesses() {
    if (activeProcessLoadRef.current) {
      return;
    }
    activeProcessLoadRef.current = true;
    try {
      const payload = await apiRequest<{ processes: RuntimeProcessItem[] }>(`/api/runtime/processes?scope=active&limit=${ACTIVE_PROCESS_LIMIT}`, {
        timeoutMs: PROCESS_REQUEST_TIMEOUT_MS,
      });
      setActiveProcesses(payload.processes || []);
    } catch {
      setActiveProcesses([]);
    } finally {
      activeProcessLoadRef.current = false;
    }
  }

  async function loadSessionArtifactsSafely(nextSession = session, reportId = selectedReportId) {
    return swallowOptionalRequest(loadSessionArtifacts(nextSession, reportId), undefined);
  }

  async function loadAnnotationsSafely(nextSession = session, reportId = selectedReportId) {
    return swallowOptionalRequest(loadAnnotations(nextSession, reportId), undefined);
  }

  async function loadAttachmentsSafely(nextSession = session, reportId = selectedReportId) {
    return swallowOptionalRequest(loadAttachments(nextSession, reportId), undefined);
  }

  async function refreshDetailSafely(reportId = selectedReportId) {
    return swallowOptionalRequest(refreshDetail(reportId), null);
  }

  function enterReadOnlyReportWorkspace(reportId: string, reportDetail: ReportCatalogDetail, reason: string) {
    sessionIdRef.current = "";
    setSession(null);
    setEvents([]);
    setFiles([]);
    setDiffFiles([]);
    setAnnotations([]);
    setAttachments([]);
    setDetail(reportDetail);
    void loadProcessesSafely(reportId, null);
    setStatus(`报告已打开，可先查看和刷新预览；Codex 会话暂不可用：${reason}`);
  }

  async function loadSessionEvents(nextSession: ReportAgentSession, reportId: string) {
    const payload = await apiRequest<{
      session: ReportAgentSession;
      events: ReportAgentEvent[];
      next_cursor: number;
    }>(
      `/api/report-agent-sessions/${nextSession.session_id}/events?report_id=${encodeURIComponent(reportId)}&cursor=0`,
    );
    const initialEvents = payload.events || [];
    const nextCursor = payload.next_cursor || newestCursor(initialEvents);
    sessionIdRef.current = (payload.session || nextSession).session_id;
    setSession(payload.session || nextSession);
    setEvents(initialEvents.slice(-500));
    setCursor(nextCursor);
    cursorRef.current = nextCursor;
    return payload.session || nextSession;
  }

  async function loadSpecificSession(reportId: string, explicitSessionId: string) {
    const payload = await apiRequest<{ session: ReportAgentSession; events: ReportAgentEvent[] }>(
      `/api/reports/${reportId}/agent-sessions/${explicitSessionId}`,
      { timeoutMs: REPORT_DETAIL_TIMEOUT_MS },
    );
    const initialEvents = payload.events || [];
    const nextCursor = newestCursor(initialEvents);
    sessionIdRef.current = payload.session.session_id;
    setSession(payload.session);
    setEvents(initialEvents.slice(-500));
    setCursor(nextCursor);
    cursorRef.current = nextCursor;
    return payload.session;
  }

  function closeEventStream() {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setStreamState("idle");
  }

  function resetSelectedReportContext(preserveDetail = false) {
    closeEventStream();
    if (!preserveDetail) {
      setDetail(null);
    }
    sessionIdRef.current = "";
    setSession(null);
    setEvents([]);
    setFiles([]);
    setDiffFiles([]);
    setAnnotations([]);
    setAttachments([]);
    setProcesses([]);
    setCursor(0);
    cursorRef.current = 0;
  }

  async function openReport(reportId: string, options: OpenReportOptions = {}) {
    const { forceNewSession = false, preserveDetail = false, targetSessionId = "" } = options;
    const shouldNavigateToWorkspace = workspaceMode === "session" || forceNewSession || Boolean(targetSessionId);
    const shouldReuseLoadedDetail = preserveDetail && detail?.report_id === reportId;
    const latestCatalogSession = sortedReports.find((item) => item.report_id === reportId)?.latest_revision_session || null;
    const canUseCatalogSessionHint = workspaceMode === "session" || Boolean(targetSessionId);
    const catalogSessionHint =
      forceNewSession
        ? null
        : targetSessionId
          ? latestCatalogSession?.session_id === targetSessionId && !isInternalRevisionSession(latestCatalogSession)
            ? latestCatalogSession
            : null
          : canUseCatalogSessionHint && !isInternalRevisionSession(latestCatalogSession)
            ? latestCatalogSession
            : null;
    const requestId = reportOpenRequestRef.current + 1;
    reportOpenRequestRef.current = requestId;
    const isCurrentRequest = () => reportOpenRequestRef.current === requestId;
    resetSelectedReportContext(shouldReuseLoadedDetail);
    selectedReportIdRef.current = reportId;
    setSelectedReportId(reportId);
    setStatus(forceNewSession ? "正在创建新的工作区会话..." : "正在恢复后续改造会话...");
    try {
      const detailPromise =
        shouldReuseLoadedDetail && detail
          ? Promise.resolve(detail)
          : apiRequest<ReportCatalogDetail>(`/api/reports/${reportId}`, { timeoutMs: REPORT_DETAIL_TIMEOUT_MS });
      let activeSession: ReportAgentSession | null = null;
      if (!forceNewSession && targetSessionId) {
        try {
          activeSession = await loadSpecificSession(reportId, targetSessionId);
          if (!isCurrentRequest()) {
            return;
          }
          setStatus("工作区会话已恢复，正在补加载预览和链路状态...");
        } catch {
          if (!isCurrentRequest()) {
            return;
          }
          const placeholder = buildSessionSkeleton(reportId, targetSessionId);
          sessionIdRef.current = placeholder.session_id;
          setSession(placeholder);
          activeSession = placeholder;
          setStatus("工作区已打开，正在后台补拉会话详情和预览...");
        }
      } else if (!forceNewSession && catalogSessionHint) {
        sessionIdRef.current = catalogSessionHint.session_id;
        setSession(catalogSessionHint);
        setStatus("已恢复后续改造会话，正在补加载历史事件和预览...");
        activeSession = catalogSessionHint;
        try {
          activeSession = await loadSessionEvents(catalogSessionHint, reportId);
          if (!isCurrentRequest()) {
            return;
          }
        } catch {
          if (!isCurrentRequest()) {
            return;
          }
          sessionIdRef.current = catalogSessionHint.session_id;
          setSession(catalogSessionHint);
          activeSession = catalogSessionHint;
        }
      }
      const reportDetail = await detailPromise;
      if (!isCurrentRequest()) {
        return;
      }
      if (!shouldReuseLoadedDetail || !detail) {
        setDetail(reportDetail);
      }
      const existingSession =
        forceNewSession
          ? null
          : targetSessionId
            ? (reportDetail.revision_sessions || []).find((item) => item.session_id === targetSessionId) ||
              (reportDetail.latest_revision_session?.session_id === targetSessionId ? reportDetail.latest_revision_session : null)
            : pickPreferredRevisionSession(reportDetail);
      const createSession = async () =>
        apiRequest<{ session: ReportAgentSession; events: ReportAgentEvent[] }>(
          `/api/reports/${reportId}/agent-sessions`,
          {
            method: "POST",
            body: JSON.stringify({ title: "\u540e\u7eed\u6539\u9020" }),
            timeoutMs: REPORT_DETAIL_TIMEOUT_MS,
          },
        );
      if (forceNewSession) {
        let created: { session: ReportAgentSession; events: ReportAgentEvent[] };
        try {
          created = await createSession();
        } catch (error) {
          if (!isCurrentRequest()) {
            return;
          }
          const messageText = error instanceof Error ? error.message : String(error || "未知错误");
          enterReadOnlyReportWorkspace(reportId, reportDetail, messageText);
          return;
        }
        if (!isCurrentRequest()) {
          return;
        }
        const initialEvents = created.events || [];
        const nextCursor = newestCursor(initialEvents);
        sessionIdRef.current = created.session.session_id;
        setSession(created.session);
        setEvents(initialEvents);
        setCursor(nextCursor);
        cursorRef.current = nextCursor;
        activeSession = created.session;
        setStatus("新的工作区会话已创建，现在可以像原生 Codex 一样持续互动。");
        if (shouldNavigateToWorkspace) {
          router.replace(buildWorkspaceHref(reportId, created.session.session_id));
          return;
        }
      } else if (!activeSession && existingSession) {
        try {
          activeSession =
            targetSessionId && existingSession.session_id === targetSessionId
              ? await loadSpecificSession(reportId, targetSessionId)
              : await loadSessionEvents(existingSession, reportId);
          if (!isCurrentRequest()) {
            return;
          }
          setStatus("已恢复后续改造会话，可以继续沿着上一轮结果修改。");
        } catch {
          if (!isCurrentRequest()) {
            return;
          }
          sessionIdRef.current = existingSession.session_id;
          setSession(existingSession);
          activeSession = existingSession;
          setStatus("会话入口已恢复；历史事件暂时不可用，但可以先继续提需求。");
        }
      } else if (!activeSession) {
        let created: { session: ReportAgentSession; events: ReportAgentEvent[] };
        try {
          created = await createSession();
        } catch (error) {
          if (!isCurrentRequest()) {
            return;
          }
          const messageText = error instanceof Error ? error.message : String(error || "未知错误");
          enterReadOnlyReportWorkspace(reportId, reportDetail, messageText);
          return;
        }
        if (!isCurrentRequest()) {
          return;
        }
        const initialEvents = created.events || [];
        const nextCursor = newestCursor(initialEvents);
        sessionIdRef.current = created.session.session_id;
        setSession(created.session);
        setEvents(initialEvents);
        setCursor(nextCursor);
        cursorRef.current = nextCursor;
        activeSession = created.session;
        setStatus("内置 Codex 已就绪，运行中也可以继续发送引导消息。");
        if (shouldNavigateToWorkspace) {
          router.replace(buildWorkspaceHref(reportId, created.session.session_id));
        }
      }
      if (!activeSession) {
        return;
      }
      if (existingSession && activeSession.session_id !== existingSession.session_id) {
        try {
          activeSession =
            targetSessionId && existingSession.session_id === targetSessionId
              ? await loadSpecificSession(reportId, targetSessionId)
              : await loadSessionEvents(existingSession, reportId);
          if (!isCurrentRequest()) {
            return;
          }
        } catch {
          if (!isCurrentRequest()) {
            return;
          }
        }
      }
      if (!forceNewSession && shouldNavigateToWorkspace && activeSession?.session_id) {
        router.replace(buildWorkspaceHref(reportId, activeSession.session_id));
      }
      void (async () => {
        const optionalResults = await Promise.allSettled([
          loadSessionArtifactsSafely(activeSession, reportId),
          loadAnnotationsSafely(activeSession, reportId),
          loadAttachmentsSafely(activeSession, reportId),
          loadProcessesSafely(reportId, activeSession),
        ]);
        if (!isCurrentRequest()) {
          return;
        }
        if (
          optionalResults.some((result) => result.status === "rejected") ||
          optionalResults.some((result) => result.status === "fulfilled" && result.value === false)
        ) {
          setStatus(forceNewSession ? "新工作区已创建；部分批注、附件或运行状态暂时不可用，刷新后会继续补齐。" : "会话已恢复；部分预览、批注或链路状态暂时不可用，刷新后会继续补齐。");
        }
      })();
      if (forceNewSession) {
        void refreshDetail(reportId);
      }
    } catch (error) {
      if (!isCurrentRequest()) {
        return;
      }
      const messageText = error instanceof Error ? error.message : String(error || "未知错误");
      setStatus(`${forceNewSession ? "创建工作区失败" : "打开报告失败"}：${messageText}`);
    }
  }

  async function createFreshSession() {
    const targetReportId = selectedReportId || sortedReports[0]?.report_id || "";
    if (!targetReportId || isCreatingSession) {
      return;
    }
    setIsCreatingSession(true);
    try {
      await openReport(targetReportId, {
        forceNewSession: true,
        preserveDetail: targetReportId === selectedReportId,
      });
    } finally {
      setIsCreatingSession(false);
    }
  }

  async function pollEvents(nextCursor = cursor) {
    if (!session || !selectedReportId) {
      return;
    }
    const requestReportId = selectedReportId;
    const requestSessionId = session.session_id;
    try {
      const payload = await apiRequest<{
        session: ReportAgentSession;
        events: ReportAgentEvent[];
        next_cursor: number;
      }>(
        `/api/report-agent-sessions/${session.session_id}/events?report_id=${encodeURIComponent(
          selectedReportId,
        )}&cursor=${nextCursor}`,
      );
      if (!isCurrentReportSession(requestReportId, requestSessionId)) {
        return;
      }
      const nextSession = payload.session;
      sessionIdRef.current = nextSession.session_id;
      setSession(nextSession);
      const terminalStatus = nextSession?.current_turn_status || "";
      const terminalStatusMessage = statusMessageForTurnStatus(terminalStatus);
      if (terminalStatusMessage) {
        setStatus(terminalStatusMessage);
      }
      if (payload.events?.length) {
        setEvents((current) => {
          const seen = new Set(current.map((event) => event.event_id));
          return [...current, ...payload.events.filter((event) => !seen.has(event.event_id))].slice(-500);
        });
        const next = payload.next_cursor || nextCursor;
        setCursor(next);
        cursorRef.current = Math.max(cursorRef.current, next);
      }
      if (TURN_TERMINAL_STATUSES.has(terminalStatus)) {
        const terminalTurn = nextSession?.current_turn;
        const terminalKey = [
          nextSession?.session_id || session.session_id,
          terminalTurn?.turn_id || nextSession?.active_turn_id || "",
          terminalStatus,
          terminalTurn?.completed_at || nextSession?.updated_at || "",
        ].join(":");
        if (terminalRefreshKeyRef.current !== terminalKey) {
          terminalRefreshKeyRef.current = terminalKey;
          await Promise.all([
            loadSessionArtifactsSafely(nextSession),
            loadAnnotationsSafely(nextSession),
            loadAttachmentsSafely(nextSession),
            refreshDetailSafely(),
            loadProcessesSafely(selectedReportId, nextSession),
          ]);
        }
      } else {
        terminalRefreshKeyRef.current = "";
      }
    } catch {
      setStreamState("retrying");
    }
  }

  const pollEventsForEffect = useEffectEvent(() => {
    if (typeof document !== "undefined" && document.hidden) {
      return;
    }
    void pollEvents(cursorRef.current);
  });

  const refreshProcessesForEffect = useEffectEvent(() => {
    if (typeof document !== "undefined" && document.hidden) {
      return;
    }
    void loadProcessesSafely(selectedReportId, session);
  });

  const refreshActiveProcessesForEffect = useEffectEvent(() => {
    if (typeof document !== "undefined" && document.hidden) {
      return;
    }
    void loadActiveProcesses();
  });

  const openReportForEffect = useEffectEvent((reportId: string) => {
    void openReport(reportId);
  });

  const clearSelectedReportForEffect = useEffectEvent(() => {
    resetSelectedReportContext();
    selectedReportIdRef.current = "";
    setSelectedReportId("");
  });

  const openWorkspaceReportForEffect = useEffectEvent((reportId: string, sessionId?: string) => {
    void openReport(reportId, {
      targetSessionId: sessionId || "",
    });
  });

  const handleStreamEvent = useEffectEvent((rawData: string) => {
    try {
      const parsed = JSON.parse(rawData) as ReportAgentEvent;
      if ((parsed as { type?: string }).type === "session_error") {
        setStreamState("idle");
        return;
      }
      setEvents((current) => {
        if (current.some((item) => item.event_id === parsed.event_id)) {
          return current;
        }
        return [...current, parsed].slice(-500);
      });
      setCursor((current) => Math.max(current, parsed.event_id || 0));
      cursorRef.current = Math.max(cursorRef.current, parsed.event_id || 0);
      if (parsed.preview_url) {
        setSession((current) => (current ? { ...current, preview_url: parsed.preview_url } : current));
      }
      if (
        parsed.kind === "attachment_uploaded" ||
        parsed.kind === "data_profile_created" ||
        parsed.kind === "chart_plan_created" ||
        parsed.kind === "chart_rendered" ||
        parsed.kind === "chart_substituted"
      ) {
        void Promise.all([loadAttachmentsSafely(), loadSessionArtifactsSafely()]);
      }
      const eventStatusMessage =
        parsed.kind === "turn_completed"
          ? statusMessageForTurnStatus("completed")
          : parsed.kind === "turn_cancelled"
            ? statusMessageForTurnStatus("cancelled")
            : parsed.kind === "turn_failed"
              ? statusMessageForTurnStatus(parsed.status || "failed")
              : statusMessageForTurnStatus(parsed.status);
      if (eventStatusMessage) {
        setStatus(eventStatusMessage);
      }
      if (TURN_TERMINAL_STATUSES.has(parsed.status || "") || parsed.kind === "turn_completed" || parsed.kind === "turn_failed" || parsed.kind === "turn_cancelled") {
        void Promise.all([loadSessionArtifactsSafely(), loadAnnotationsSafely(), loadAttachmentsSafely(), refreshDetailSafely(), loadProcessesSafely()]);
      }
    } catch {
      // Polling remains the fallback for malformed or dropped stream chunks.
    }
  });

  async function sendMessageText(text: string): Promise<boolean> {
    if (!selectedReportId || !session || !text.trim()) {
      return false;
    }
    const normalizedText = text.trim();
    setIsSending(true);
    try {
      const payload = await apiRequest<{ session: ReportAgentSession }>(
        `/api/report-agent-sessions/${session.session_id}/messages?report_id=${encodeURIComponent(selectedReportId)}`,
        {
          method: "POST",
          body: JSON.stringify({ message: normalizedText }),
          timeoutMs: REPORT_DETAIL_TIMEOUT_MS,
        },
      );
      setSession(payload.session);
      setStatus(isTurnRunning ? "引导已注入当前原生 Codex turn。" : "Codex 正在执行修改；完成后会自动生成 PDF 草稿。");
      await Promise.all([
        pollEvents(cursorRef.current),
        loadSessionArtifactsSafely(payload.session, selectedReportId),
        loadAnnotationsSafely(payload.session, selectedReportId),
        loadAttachmentsSafely(payload.session, selectedReportId),
        loadProcessesSafely(selectedReportId, payload.session),
      ]);
      return true;
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error || "未知错误");
      setStatus(`提交给 Codex 失败：${messageText}`);
      return false;
    } finally {
      setIsSending(false);
    }
  }

  async function sendMessage() {
    if (!message.trim()) {
      return;
    }
    const text = message.trim();
    setMessage("");
    const ok = await sendMessageText(text);
    if (!ok) {
      setMessage((current) => current || text);
    }
  }

  async function cancelTurn() {
    if (!selectedReportId || !session) {
      return;
    }
    const payload = await apiRequest<{ session: ReportAgentSession }>(
      `/api/report-agent-sessions/${session.session_id}/cancel?report_id=${encodeURIComponent(selectedReportId)}`,
      { method: "POST" },
    );
    setSession(payload.session);
    await Promise.all([
      pollEvents(cursorRef.current),
      loadSessionArtifactsSafely(payload.session, selectedReportId),
      loadProcessesSafely(selectedReportId, payload.session),
    ]);
    setStatus("本轮已请求停止，稳定后可以继续提交新的修改意见。");
  }

  async function publishRevision() {
    if (!selectedReportId || !session) {
      return;
    }
    setIsPublishing(true);
    try {
      const payload = await apiRequest<{ session: ReportAgentSession }>(
        `/api/report-agent-sessions/${session.session_id}/publish?report_id=${encodeURIComponent(selectedReportId)}`,
        {
          method: "POST",
          body: JSON.stringify({ note: "" }),
        },
      );
      setSession(payload.session);
      await Promise.all([
        refreshDetailSafely(),
        pollEvents(cursorRef.current),
        loadSessionArtifactsSafely(payload.session, selectedReportId),
        loadAnnotationsSafely(payload.session, selectedReportId),
        loadAttachmentsSafely(payload.session, selectedReportId),
        loadProcessesSafely(selectedReportId, payload.session),
      ]);
      setStatus("修订版已发布，并注册回该报告下载物。");
    } finally {
      setIsPublishing(false);
    }
  }

  async function createAnnotation(annotation: Omit<ReportAnnotation, "annotation_id" | "created_at" | "updated_at">) {
    if (!selectedReportId || !session) {
      return;
    }
    const payload = await apiRequest<{ session: ReportAgentSession; annotations: ReportAnnotation[] }>(
      `/api/report-agent-sessions/${session.session_id}/annotations?report_id=${encodeURIComponent(selectedReportId)}`,
      {
        method: "POST",
        body: JSON.stringify(annotation),
      },
    );
    setAnnotations(payload.annotations || []);
    setSession(payload.session || session);
    await pollEvents(cursorRef.current);
  }

  async function deleteAnnotation(annotationId: string) {
    if (!selectedReportId || !session) {
      return;
    }
    const payload = await apiRequest<{ session: ReportAgentSession; annotations: ReportAnnotation[] }>(
      `/api/report-agent-sessions/${session.session_id}/annotations/${annotationId}?report_id=${encodeURIComponent(selectedReportId)}`,
      { method: "DELETE" },
    );
    setAnnotations(payload.annotations || []);
    setSession(payload.session || session);
    await pollEvents(cursorRef.current);
  }

  async function uploadAttachments(fileList: FileList | null) {
    if (!selectedReportId || !session || !fileList?.length) {
      return;
    }
    setIsUploadingAttachment(true);
    try {
      let latestSession = session;
      for (const file of Array.from(fileList)) {
        const form = new FormData();
        form.append("file", file);
        const payload = await apiRequest<{ session: ReportAgentSession; attachments: ReportAttachment[] }>(
          `/api/report-agent-sessions/${session.session_id}/attachments?report_id=${encodeURIComponent(selectedReportId)}`,
          {
            method: "POST",
            body: form,
          },
        );
        latestSession = payload.session || latestSession;
        setAttachments(payload.attachments || []);
      }
      setSession(latestSession);
      await Promise.all([pollEvents(cursorRef.current), loadSessionArtifacts(latestSession), loadAttachments(latestSession)]);
      setStatus("补充材料已上传并生成数据画像；发送修改意见时 Codex 会自动读取这些证据。");
    } finally {
      setIsUploadingAttachment(false);
    }
  }

  async function deleteAttachment(attachmentId: string) {
    if (!selectedReportId || !session) {
      return;
    }
    const payload = await apiRequest<{ session: ReportAgentSession; attachments: ReportAttachment[] }>(
      `/api/report-agent-sessions/${session.session_id}/attachments/${attachmentId}?report_id=${encodeURIComponent(selectedReportId)}`,
      { method: "DELETE" },
    );
    setSession(payload.session || session);
    setAttachments(payload.attachments || []);
    await Promise.all([pollEvents(cursorRef.current), loadSessionArtifacts(payload.session || session)]);
  }

  async function cancelProcess(item: RuntimeProcessItem) {
    const targetReportId = item.report_id || selectedReportId;
    if (!targetReportId) {
      return;
    }
    const targetSessionQuery = targetReportId === selectedReportId && sessionId ? `&session_id=${encodeURIComponent(sessionId)}` : "";
    setIsProcessBusy(true);
    try {
      const payload = await apiRequest<{ processes: RuntimeProcessItem[] }>(
        `/api/runtime/processes/${encodeURIComponent(item.kind)}/${encodeURIComponent(item.id)}/cancel?report_id=${encodeURIComponent(
          targetReportId,
        )}${targetSessionQuery}`,
        { method: "POST" },
      );
      if (targetReportId === selectedReportId) {
        setProcesses(payload.processes || []);
      }
      await loadActiveProcesses();
      await pollEvents(cursorRef.current);
    } finally {
      setIsProcessBusy(false);
    }
  }

  async function resumeProcess(item: RuntimeProcessItem) {
    const targetReportId = item.report_id || selectedReportId;
    if (!targetReportId) {
      return;
    }
    const targetSessionQuery = targetReportId === selectedReportId && sessionId ? `&session_id=${encodeURIComponent(sessionId)}` : "";
    setIsProcessBusy(true);
    try {
      const payload = await apiRequest<ResumeProcessResponse>(
        `/api/runtime/processes/${encodeURIComponent(item.kind)}/${encodeURIComponent(item.id)}/resume?report_id=${encodeURIComponent(
          targetReportId,
        )}${targetSessionQuery}`,
        { method: "POST" },
      );
      if (targetReportId === selectedReportId) {
        setProcesses(payload.processes || []);
      }
      if (payload.result?.session) {
        const nextSession = payload.result.session;
        setSession(nextSession);
        if (payload.result.events?.length) {
          setEvents((current) => {
            const seen = new Set(current.map((event) => event.event_id));
            return [...current, ...(payload.result?.events || []).filter((event) => !seen.has(event.event_id))].slice(-500);
          });
          const next = newestCursor(payload.result.events);
          setCursor((current) => Math.max(current, next));
          cursorRef.current = Math.max(cursorRef.current, next);
        }
        await Promise.all([loadSessionArtifacts(nextSession), loadAnnotations(nextSession)]);
      }
      await loadActiveProcesses();
      const blockingItems = [
        ...(Array.isArray(payload.blocking_missing_inputs) ? payload.blocking_missing_inputs : []),
        ...(Array.isArray(payload.result?.missing_required_assets) ? payload.result.missing_required_assets : []),
      ].filter(Boolean);
      const action = String(payload.action || "");
      if (action === "resume_blocked" || action === "start_generic_long_cli_blocked" || action.endsWith("_blocked")) {
        const blockingText = blockingItems.length ? `：${blockingItems.join("、")}` : "";
        setStatus(`${item.label || item.kind} 当前还不能续跑，需要先补齐依赖${blockingText}`);
      } else if (payload.action === "rebuild_workspace_then_restart_pipeline") {
        setStatus(`${item.label || item.kind} 正在重建 workspace 并重跑，进程面板会自动刷新。`);
      } else {
        setStatus(`${item.label || item.kind} 已发起续跑，进程面板会自动刷新。`);
      }
      setTimeout(() => {
        void loadActiveProcesses();
        if (targetReportId === selectedReportId) {
          void loadProcessesSafely(selectedReportId, session);
        }
      }, 1800);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error || "未知错误");
      setStatus(`续跑未执行：${messageText}`);
      await loadActiveProcesses();
      if (targetReportId === selectedReportId) {
        await loadProcessesSafely(selectedReportId, session);
      }
    } finally {
      setIsProcessBusy(false);
    }
  }

  useEffect(() => {
    void loadReports({ silent: workspaceMode === "session" });
    // 初次挂载和筛选变化时刷新目录；自动选中逻辑在后续 effect 中处理。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchKeyword, selectedBusinessProfile, selectedDatasetId, catalogSortBy, workspaceMode]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearchKeyword(searchInput.trim());
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (workspaceMode === "session") {
      return;
    }
    if (!sortedReports.length) {
      if (selectedReportId) {
        clearSelectedReportForEffect();
      }
      return;
    }
    if (!selectedReportId || !sortedReports.some((item) => item.report_id === selectedReportId)) {
      openReportForEffect(sortedReports[0].report_id);
    }
  }, [initialReportId, isLoading, selectedReportId, sortedReports, workspaceMode]);

  useEffect(() => {
    if (workspaceMode !== "session") {
      return;
    }
    if (!initialReportId || workspaceSyncRef.current) {
      return;
    }
    workspaceSyncRef.current = true;
    openWorkspaceReportForEffect(initialReportId, initialSessionId);
  }, [initialReportId, initialSessionId, workspaceMode]);

  useEffect(() => {
    return () => {
      reportLoadAbortRef.current?.abort();
      if (catalogRefreshTimerRef.current !== null && typeof window !== "undefined") {
        window.clearTimeout(catalogRefreshTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    void loadCodexHealth();
    const timer = setInterval(() => {
      void loadCodexHealth();
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    cursorRef.current = cursor;
  }, [cursor]);

  useEffect(() => {
    selectedReportIdRef.current = selectedReportId;
  }, [selectedReportId]);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    eventSourceRef.current?.close();
    if (!sessionId || !selectedReportId) {
      setStreamState("idle");
      return;
    }
    setStreamState("connecting");
    const sourceSessionId = sessionId;
    const sourceReportId = selectedReportId;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let shouldReconnect = true;
    const source = new EventSource(
      apiUrl(
        `/api/report-agent-sessions/${sessionId}/events/stream?report_id=${encodeURIComponent(
          selectedReportId,
        )}&cursor=${cursorRef.current}`,
      ),
    );
    eventSourceRef.current = source;
    source.onopen = () => {
      if (!isCurrentReportSession(sourceReportId, sourceSessionId)) {
        source.close();
        return;
      }
      setStreamState("open");
    };
    source.onmessage = (event) => {
      if (!isCurrentReportSession(sourceReportId, sourceSessionId)) {
        source.close();
        return;
      }
      handleStreamEvent(event.data);
    };
    source.addEventListener("done", () => {
      shouldReconnect = false;
      source.close();
      if (isCurrentReportSession(sourceReportId, sourceSessionId)) {
        setStreamState("idle");
      }
    });
    source.onerror = () => {
      source.close();
      if (!shouldReconnect) {
        return;
      }
      if (!isCurrentReportSession(sourceReportId, sourceSessionId)) {
        return;
      }
      setStreamState("retrying");
      reconnectTimer = setTimeout(() => {
        setStreamRetryToken((current) => current + 1);
      }, 1800);
    };
    return () => {
      shouldReconnect = false;
      source.close();
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
      }
    };
  }, [sessionId, selectedReportId, streamRetryToken]);

  useEffect(() => {
    if (!sessionId || !selectedReportId) {
      return;
    }
    if (streamState === "open") {
      return;
    }
    const timer = setInterval(() => {
      pollEventsForEffect();
    }, EVENT_POLL_FALLBACK_MS);
    return () => clearInterval(timer);
  }, [sessionId, selectedReportId, streamState]);

  useEffect(() => {
    if (!selectedReportId) {
      return;
    }
    const timer = setInterval(() => {
      refreshProcessesForEffect();
    }, SELECTED_PROCESS_POLL_MS);
    return () => clearInterval(timer);
  }, [selectedReportId, sessionId]);

  useEffect(() => {
    const timer = setInterval(() => {
      refreshActiveProcessesForEffect();
    }, ACTIVE_PROCESS_POLL_MS);
    return () => clearInterval(timer);
  }, []);

  const compactProcesses = useMemo(() => {
    const byKey = new Map<string, RuntimeProcessItem>();
    for (const item of [...activeProcesses, ...processes]) {
      const key = `${item.kind}:${item.id}`;
      const existing = byKey.get(key);
      if (!existing || item.report_id === selectedReportId) {
        byKey.set(key, item);
      }
    }
    const priority = (item: RuntimeProcessItem) => {
      const status = String(item.observed_status || item.status || "");
      const selectedRank = item.report_id === selectedReportId ? 0 : 1;
      let stateRank = 7;
      if (item.is_active && item.kind === "report_agent_turn") {
        stateRank = 0;
      } else if (item.is_active) {
        stateRank = 1;
      } else if (item.can_cancel) {
        stateRank = 2;
      } else if (item.is_stale && item.can_resume) {
        stateRank = 3;
      } else if (item.can_resume) {
        stateRank = 4;
      } else if (item.is_stale) {
        stateRank = 5;
      } else if (["failed", "blocked", "cancelled", "timed_out", "error"].includes(status)) {
        stateRank = 6;
      }
      return [selectedRank, stateRank, -timeValue(item.updated_at || item.started_at)] as const;
    };
    return Array.from(byKey.values())
      .filter((item) => {
        const status = String(item.observed_status || item.status || "");
        return (
          (item.is_active && item.kind !== "native_app_server") ||
          item.can_resume ||
          item.can_cancel ||
          item.is_stale ||
          (item.report_id === selectedReportId && ["failed", "blocked", "cancelled", "timed_out", "error"].includes(status))
        );
      })
      .sort((a, b) => {
        const left = priority(a);
        const right = priority(b);
        return left[0] - right[0] || left[1] - right[1] || left[2] - right[2];
      });
  }, [activeProcesses, processes, selectedReportId]);

  const resumableProcesses = useMemo(() => compactProcesses.filter((item) => item.can_resume), [compactProcesses]);
  const selectedReportResumableProcesses = useMemo(
    () => resumableProcesses.filter((item) => (item.report_id || selectedReportId) === selectedReportId),
    [resumableProcesses, selectedReportId],
  );
  const primaryResumeProcess = useMemo(() => {
    if (!selectedReportResumableProcesses.length) {
      return null;
    }
    const rank = (item: RuntimeProcessItem) => {
      const status = String(item.observed_status || item.status || "");
      const isBootstrap = item.kind === "runtime_bootstrap";
      const isSelectedReport = (item.report_id || selectedReportId) === selectedReportId;
      let priority = 5;
      if (item.is_active) {
        priority = 0;
      } else if (item.is_stale && item.can_resume) {
        priority = 1;
      } else if (isBootstrap && item.can_resume) {
        priority = 2;
      } else if (item.can_resume && ACTIONABLE_RUNTIME_STATUSES.has(status)) {
        priority = 3;
      } else if (item.can_resume) {
        priority = 4;
      }
      return [isSelectedReport ? 0 : 1, priority, -timeValue(item.updated_at || item.started_at)] as const;
    };
    return [...selectedReportResumableProcesses].sort((left, right) => {
      const leftRank = rank(left);
      const rightRank = rank(right);
      return leftRank[0] - rightRank[0] || leftRank[1] - rightRank[1] || leftRank[2] - rightRank[2];
    })[0];
  }, [selectedReportId, selectedReportResumableProcesses]);
  const selectedReportMeta = useMemo(
    () => sortedReports.find((item) => item.report_id === selectedReportId) || null,
    [selectedReportId, sortedReports],
  );

  const leftPane = (
    <aside className="revision-left-rail flex h-full min-h-0 flex-col gap-2 overflow-hidden">
      <div className="revision-sidebar-actions">
        <button
          type="button"
          className="revision-sidebar-action disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isCreatingSession || (!selectedReportId && !sortedReports.length)}
          onClick={() => void createFreshSession()}
        >
          {isCreatingSession ? <LoaderCircle size={16} className="animate-spin" /> : <Plus size={16} />}
          {isCreatingSession ? "创建中" : "新工作区"}
        </button>
        <form
          className="revision-sidebar-action muted !h-auto !cursor-default !items-center gap-2 px-3 py-2"
          onSubmit={(event) => {
            event.preventDefault();
            setSearchKeyword(searchInput.trim());
          }}
        >
          <Search size={15} />
          <input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="搜索报告 / 数据集 / 画像"
            className="min-w-0 flex-1 bg-transparent text-sm text-[var(--text-strong)] outline-none placeholder:text-[var(--muted)]"
          />
        </form>
      </div>
      <div className="soft-panel revision-library-panel min-h-[220px] shrink-0 overflow-hidden p-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">报告线程</p>
            <h3 className="mt-1 text-base font-semibold text-[var(--text-strong)]">已产出报告</h3>
          </div>
          <span className="surface-chip">{reportCountsLabel}</span>
        </div>
        <div className="mt-3 grid grid-cols-1 gap-2">
          <div className="flex gap-2">
            <button
              type="button"
              className={`surface-chip !px-3 !py-1.5 ${!searchKeyword && !selectedBusinessProfile && !selectedDatasetId ? "border-cyan-300/25 text-cyan-50" : ""}`}
              onClick={() => {
                setSearchInput("");
                setSearchKeyword("");
                setSelectedBusinessProfile("");
                setSelectedDatasetId("");
              }}
            >
              全部
            </button>
            <button
              type="button"
              className="surface-chip !px-3 !py-1.5"
              onClick={() => void loadReports({ refreshIndex: true })}
            >
              刷新索引
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={selectedBusinessProfile}
              onChange={(event) => setSelectedBusinessProfile(event.target.value)}
              className="rounded-[12px] border border-white/10 bg-white/5 px-3 py-2 text-xs text-[var(--text-strong)] outline-none"
            >
              <option value="">全部画像</option>
              {businessProfileStats.map((item) => (
                <option key={item.business_profile} value={item.business_profile}>
                  {item.business_profile} ({item.count})
                </option>
              ))}
            </select>
            <select
              value={selectedDatasetId}
              onChange={(event) => setSelectedDatasetId(event.target.value)}
              className="rounded-[12px] border border-white/10 bg-white/5 px-3 py-2 text-xs text-[var(--text-strong)] outline-none"
            >
              <option value="">全部数据集</option>
              {datasetStats.map((item) => (
                <option key={item.dataset_id} value={item.dataset_id}>
                  {(item.dataset_name || item.dataset_id).slice(0, 18)} ({item.count})
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center justify-between gap-2 text-[11px] text-[var(--muted)]">
            <span>
              {catalogIndexStatus?.indexed_report_count || totalReportCount || 0}
              {catalogIndexStatus?.known_report_count ? ` / ${catalogIndexStatus.known_report_count}` : ""}
              份已索引
            </span>
            <select
              value={catalogSortBy}
              onChange={(event) => setCatalogSortBy(event.target.value as "updated_at" | "generated_at")}
              className="rounded-[10px] border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-[var(--text-strong)] outline-none"
            >
              <option value="updated_at">按更新时间</option>
              <option value="generated_at">按生成时间</option>
            </select>
          </div>
        </div>
        {selectedReportId ? (
          <div className="mt-3 rounded-[18px] border border-cyan-300/18 bg-cyan-500/10 p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-[0.18em] text-cyan-100/80">
                  {workspaceMode === "session" ? "当前工作区" : "当前报告"}
                </p>
                <p className="mt-1 truncate text-sm font-semibold text-cyan-50">
                  {selectedReportMeta?.title || detail?.title || selectedReportId}
                </p>
                <p className="mt-1 truncate font-mono text-[11px] text-cyan-100/70">{selectedReportId}</p>
              </div>
              <span className="surface-chip border-cyan-300/20 !px-2 !py-1 text-cyan-50">
                {selectedReportResumableProcesses.length ? `${selectedReportResumableProcesses.length} 条链路` : "仅查看"}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {primaryResumeProcess ? (
                <button
                  type="button"
                  className="surface-chip inline-flex items-center gap-2 border-cyan-300/20 !px-3 !py-2 text-cyan-50 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isProcessBusy}
                  onClick={() => void resumeProcess(primaryResumeProcess)}
                >
                  {isProcessBusy ? <LoaderCircle size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                  {primaryResumeProcess.resume_label ||
                    (primaryResumeProcess.kind === "runtime_bootstrap" ? "启动 CLI 长报告链" : "续跑")}
                </button>
              ) : null}
              <button
                type="button"
                className="surface-chip !px-3 !py-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!selectedReportId || isProcessBusy}
                onClick={() => void loadProcesses(selectedReportId, session)}
              >
                刷新链路状态
              </button>
            </div>
            <p className="mt-2 text-xs leading-5 text-cyan-100/70">
              {primaryResumeProcess
                ? primaryResumeProcess.kind === "runtime_bootstrap"
                  ? "这会基于当前历史报告目录里的原始数据和现有报告资产，启动可续跑的 CLI 长报告链。"
                  : "这会从当前报告最近一次可恢复的 runtime / pipeline 节点继续往下跑。"
                : "当前这份报告还没有可直接续跑的链路；如果后端识别到可补建资产，这里会直接出现续跑键。 "}
            </p>
          </div>
        ) : null}
        <div className="revision-thread-list mt-3 h-[calc(100%-170px)] space-y-1 overflow-auto pr-1">
          {sortedReports.map((item) => {
            const runtimeState = reportRuntimeStateById.get(item.report_id);
            const inlineResume = resumableProcesses.find((process) => (process.report_id || item.report_id) === item.report_id);
            return (
              <div key={item.report_id} className={`revision-thread-item transition ${selectedReportId === item.report_id ? "is-active" : ""}`}>
                <button type="button" onClick={() => void openReport(item.report_id)} className="w-full text-left">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="revision-thread-title break-words text-sm font-semibold leading-5 text-[var(--text-strong)]">{item.title}</p>
                      {!titleAlreadyContainsReportId(item.title, item.report_id) ? (
                        <p className="mt-1 font-mono text-[11px] text-[var(--muted)]">{item.report_id}</p>
                      ) : null}
                    </div>
                    {runtimeState ? (
                      <span className="revision-thread-status inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-1 text-[11px] text-cyan-50">
                        <RuntimeActivityRing status={runtimeState.status} size="sm" title={runtimeState.label} />
                        {runtimeState.label}
                      </span>
                    ) : (
                      <FileText size={16} className="mt-1 shrink-0 text-[var(--accent-warm)]" />
                    )}
                  </div>
                  <p className="mt-2 text-xs text-[var(--muted)]">
                    运行时间 {formatTime(item.generated_at || item.updated_at)} / {item.downloadable_count || 0} 个产物
                  </p>
                  {item.dataset_name || item.business_profile ? (
                    <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-[var(--muted)]">
                      {item.dataset_name ? <span className="surface-chip !px-2 !py-1">{item.dataset_name}</span> : null}
                      {item.business_profile ? <span className="surface-chip !px-2 !py-1">{item.business_profile}</span> : null}
                    </div>
                  ) : null}
                </button>
                {inlineResume ? (
                  <div className="mt-2 flex items-center justify-end">
                    <button
                      type="button"
                      className="surface-chip inline-flex items-center gap-1.5 !px-2 !py-1 text-[11px] text-cyan-50 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={isProcessBusy}
                      onClick={() => void resumeProcess(inlineResume)}
                    >
                      {isProcessBusy ? <LoaderCircle size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                      {inlineResume.kind === "runtime_bootstrap" ? "续跑链路" : "续跑"}
                    </button>
                  </div>
                ) : null}
              </div>
            );
          })}
          {catalogError ? (
            <div className="rounded-[16px] border border-red-300/20 bg-red-500/10 px-4 py-4 text-sm leading-6 text-red-100">
              <p>报告库加载失败：{catalogError}</p>
              <button type="button" className="surface-chip mt-3 !px-3 !py-1.5" onClick={() => void loadReports()}>
                重新加载
              </button>
            </div>
          ) : !reports.length ? (
            <p className="rounded-[16px] border border-white/10 bg-white/5 px-4 py-5 text-sm leading-7 text-[var(--muted)]">
              {isLoading ? "正在加载报告库..." : "暂无可改造报告。"}
            </p>
          ) : null}
        </div>
        {session ? (
          <div className="mt-4 rounded-[18px] border border-white/10 bg-black/14 p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">Turn 历史</p>
              <span className="surface-chip !px-2 !py-1">{session.turns?.length || 0} 轮</span>
            </div>
            <div className="max-h-[210px] space-y-2 overflow-auto pr-1">
              {session.turns?.length ? (
                session.turns
                  .slice()
                  .reverse()
                  .slice(0, 6)
                  .map((turn, index) => (
                    <article
                      key={turn.turn_id || `${turn.started_at || "turn"}-${index}`}
                      className="rounded-[14px] border border-white/10 bg-white/5 px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="truncate font-mono text-[11px] text-[var(--muted)]">
                          {turn.turn_id || `turn-${(session.turns?.length || 0) - index}`}
                        </span>
                        <span className={`surface-chip !px-2 !py-1 ${turnStatusTone(turn.status)}`}>{turnStatusLabel(turn.status)}</span>
                      </div>
                      {turn.user_message ? (
                        <p className="mt-2 break-words text-xs leading-5 text-[var(--text)]">{turn.user_message}</p>
                      ) : null}
                      <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-[var(--muted)]">
                        {turn.started_at ? <span>开始 {formatTime(turn.started_at)}</span> : null}
                        {turn.completed_at ? <span>完成 {formatTime(turn.completed_at)}</span> : null}
                        {turn.changed_files?.length ? <span>{turn.changed_files.length} 个文件变更</span> : null}
                      </div>
                    </article>
                  ))
              ) : (
                <p className="rounded-[14px] border border-white/10 bg-white/5 px-3 py-3 text-xs leading-5 text-[var(--muted)]">
                  还没有执行过 turn。发送第一条修改意见后，这里会保留每一轮的状态和文件变更。
                </p>
              )}
            </div>
          </div>
        ) : null}
        {resumableProcesses.length ? (
          <div className="mt-4 rounded-[18px] border border-orange-300/20 bg-orange-500/10 p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-orange-100/80">续跑入口</p>
                <p className="mt-1 text-sm font-semibold text-orange-50">当前可续跑 / 可启动链路</p>
              </div>
              <span className="surface-chip border-orange-300/20 !px-2 !py-1 text-orange-50">{resumableProcesses.length} 项</span>
            </div>
            <div className="mt-3 space-y-2">
              {resumableProcesses.slice(0, 4).map((item) => (
                <div key={`${item.kind}:${item.id}`} className="rounded-[14px] border border-orange-300/15 bg-black/18 px-3 py-2">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-[var(--text-strong)]">{item.label || item.kind}</p>
                      <p className="mt-1 truncate text-[11px] text-[var(--muted)]">{item.display_status || item.observed_status || item.status}</p>
                    </div>
                    <button
                      type="button"
                      className="surface-chip inline-flex items-center gap-2 !px-2 !py-1 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={isProcessBusy}
                      onClick={() => void resumeProcess(item)}
                    >
                      {isProcessBusy ? <LoaderCircle size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                      {item.resume_label || "续跑"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="soft-panel revision-composer-panel min-h-0 flex-1 overflow-auto p-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Codex Turn</p>
            <h3 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">修改意见</h3>
          </div>
          {isTurnRunning ? (
            <span className="surface-chip inline-flex items-center gap-2">
              <LoaderCircle size={14} className="animate-spin" />
              {turnStatusLabel(currentTurnStatus || "running")}
            </span>
          ) : (
            <span className="surface-chip">{turnStatusLabel(currentTurnStatus || sessionStatus || "active")}</span>
          )}
        </div>
        <div className="mt-4 rounded-[18px] border border-white/10 bg-black/14 p-3 text-xs leading-6 text-[var(--muted)]">
          当前会话保持 active；运行中继续输入会作为原生 Codex 引导注入当前 turn，不会排队成下一轮。
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {revisionQuickPrompts.map((item) => (
            <button
              key={item.label}
              type="button"
              className="surface-chip !px-3 !py-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!session || isSending}
              onClick={() => setMessage(item.prompt)}
            >
              {item.label}
            </button>
          ))}
        </div>
        {session ? (
          <div className="mt-3 rounded-[18px] border border-white/10 bg-white/5 p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">当前 Turn</p>
              <span className={`surface-chip !px-2 !py-1 ${turnStatusTone(currentTurnStatus || "active")}`}>
                {turnStatusLabel(currentTurnStatus || "active")}
              </span>
            </div>
            <div className="mt-3 grid gap-2 text-[11px] leading-5 text-[var(--muted)]">
              <div className="flex items-center justify-between gap-3">
                <span>turn_id</span>
                <span className="truncate font-mono text-[var(--text)]">{currentTurn?.turn_id || session.active_turn_id || "待启动"}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>native_turn</span>
                <span className="truncate font-mono text-[var(--text)]">{currentTurn?.native_turn_id || "未绑定"}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>task / run</span>
                <span className="truncate font-mono text-[var(--text)]">
                  {currentTurn?.task_id || session.current_task_id || "无"} / {currentTurn?.run_id || session.current_run_id || "无"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>guidance</span>
                <span className="font-mono text-[var(--text)]">{guidanceCount} 次注入</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>scope</span>
                <span className="truncate font-mono text-[var(--text)]">{currentTurnScopeStatus || "旧会话"}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>attempts</span>
                <span className="font-mono text-[var(--text)]">{currentTurn?.attempt_count || 1}</span>
              </div>
            </div>
            {verificationExists ? (
              <div className="mt-3 rounded-[14px] border border-white/10 bg-black/18 px-3 py-2 text-[11px] leading-5 text-[var(--muted)]">
                <div>验收通过：{String((currentTurn?.revision_verification as Record<string, unknown> | undefined)?.passed ?? false)}</div>
                <div>
                  已改动：{Array.isArray((currentTurn?.revision_verification as Record<string, unknown> | undefined)?.changed_targets) ? (((currentTurn?.revision_verification as Record<string, unknown>).changed_targets as string[]).join(", ") || "无") : "无"}
                </div>
                <div>
                  越界项：{Array.isArray((currentTurn?.revision_verification as Record<string, unknown> | undefined)?.forbidden_target_violations) ? (((currentTurn?.revision_verification as Record<string, unknown>).forbidden_target_violations as string[]).join(", ") || "无") : "无"}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
        <div className="mt-3 rounded-[18px] border border-white/10 bg-black/14 p-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">补充材料</p>
              <p className="mt-1 text-sm font-semibold text-[var(--text-strong)]">上传数据 / 文档让 Codex 深挖</p>
            </div>
            <label className="surface-chip cursor-pointer !px-3 !py-2 text-xs">
              {isUploadingAttachment ? "上传中..." : "上传"}
              <input
                type="file"
                className="hidden"
                multiple
                disabled={!session || isUploadingAttachment}
                accept=".csv,.tsv,.xlsx,.xls,.md,.txt,.pdf,.json"
                onChange={(event) => {
                  void uploadAttachments(event.currentTarget.files);
                  event.currentTarget.value = "";
                }}
              />
            </label>
          </div>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
            附件会作为补充证据进入原生 Codex；图表数值由后端确定性渲染，不会静默覆盖原报告数字。
          </p>
          {attachments.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {attachments.map((item) => (
                <span
                  key={item.attachment_id}
                  className="inline-flex max-w-full items-center gap-2 rounded-full border border-white/10 bg-white/7 px-3 py-1.5 text-[11px] text-[var(--text)]"
                  title={item.name}
                >
                  <span className="truncate">{item.name}</span>
                  {item.profile?.row_count ? <span className="text-[var(--muted)]">{item.profile.row_count} 行</span> : null}
                  <button
                    type="button"
                    className="text-[var(--muted)] hover:text-red-200"
                    onClick={() => void deleteAttachment(item.attachment_id)}
                    aria-label={`删除 ${item.name}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : null}
          <button
            type="button"
            className="surface-chip mt-3 !px-3 !py-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!session || isSending}
            onClick={() =>
              setMessage(
                "读取已上传补充材料、原报告派生指标和已有图表底层数据，选择最合适的指标做气泡图或象限图；如果字段不足，就生成最接近的替代图，并把业务解释加到报告中。",
              )
            }
          >
            用补充证据补气泡/象限图
          </button>
        </div>
        <textarea
          className="field-input mt-4 min-h-[150px] resize-y"
          placeholder={
            isTurnRunning
              ? "运行中继续输入引导，例如：先停一下，把首页改成三条行动项，不要动数字。"
              : "例如：改标题但保持数字不变；把首页改成更强的管理摘要；把图题全部业务化。"
          }
          value={message}
          disabled={!session || isSending}
          onChange={(event) => setMessage(event.target.value)}
        />
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            className="primary-button inline-flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!session || !message.trim() || isSending}
            onClick={() => void sendMessage()}
          >
            {isSending ? <LoaderCircle size={16} className="animate-spin" /> : <Send size={16} />}
            {isTurnRunning ? "发送引导" : "提交给 Codex"}
          </button>
          {isTurnRunning ? (
            <button type="button" className="surface-chip inline-flex items-center gap-2" onClick={() => void cancelTurn()}>
              <Square size={14} />
              停止本轮
            </button>
          ) : (
            <button
              type="button"
              className="surface-chip inline-flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!session}
              onClick={() =>
                setMessage(
                  (current) =>
                    current ||
                    "继续基于上一轮结果做更大范围的结构和表达优化：可以重排章节、重写摘要和正文，但保持所有 deterministic 数字不变，不新增无证据指标。",
                )
              }
            >
              继续修改
            </button>
          )}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs leading-6 text-[var(--muted)]">
          <span>{status}</span>
          {session ? <span className="surface-chip">原生 Codex：{nativeStatus || "idle"}</span> : null}
          {session?.revision_agent_contract_version ? <span className="surface-chip">contract：{session.revision_agent_contract_version}</span> : null}
          {codexHealth ? (
            <span className={`surface-chip ${codexHealth.available && codexHealth.app_server_available ? "" : "border-red-300/30 text-red-100"}`}>
              {codexHealth.available && codexHealth.app_server_available ? "Codex app-server 可用" : "Codex app-server 不可用"}
            </span>
          ) : null}
          {session?.native_protocol_error ? <span className="text-red-200">{session.native_protocol_error}</span> : null}
          {codexHealth?.error ? <span className="text-red-200">{codexHealth.error}</span> : null}
        </div>
      </div>
    </aside>
  );

  const nativeComposer = (
    <div className="revision-native-composer shrink-0">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        {revisionQuickPrompts.map((item) => (
          <button
            key={item.label}
            type="button"
            className="surface-chip !min-h-0 !px-3 !py-1.5 text-xs disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!session || isSending}
            onClick={() => setMessage(item.prompt)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="revision-composer-box">
        <textarea
          className="revision-composer-textarea"
          placeholder={
            isTurnRunning
              ? "运行中继续输入引导，例如：先停一下，把首页改成三条行动项，不要动数字。"
              : "向 Codex 描述你要怎么改这份报告..."
          }
          value={message}
          disabled={!session || isSending}
          onChange={(event) => setMessage(event.target.value)}
        />
        <div className="revision-composer-footer">
          <label className="revision-icon-action cursor-pointer" title="上传文件">
            {isUploadingAttachment ? <LoaderCircle size={16} className="animate-spin" /> : <Paperclip size={16} />}
            <input
              type="file"
              className="hidden"
            multiple
            disabled={!session || isUploadingAttachment}
            accept=".csv,.tsv,.xlsx,.xls,.md,.txt,.pdf,.json"
            onChange={(event) => {
              void uploadAttachments(event.currentTarget.files);
                event.currentTarget.value = "";
              }}
            />
          </label>
          <span className="min-w-0 flex-1 truncate text-xs text-[var(--muted)]">{status}</span>
          {isTurnRunning ? (
            <button type="button" className="revision-icon-action" onClick={() => void cancelTurn()} title="停止本轮">
              <Square size={15} />
            </button>
          ) : (
            <button
              type="button"
              className="revision-continue-action disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!session}
              onClick={() =>
                setMessage(
                  (current) =>
                    current ||
                    "继续基于上一轮结果做更大范围的结构和表达优化：可以重排章节、重写摘要和正文，但保持所有 deterministic 数字不变，不新增无证据指标。",
                )
              }
            >
              继续
            </button>
          )}
          <button
            type="button"
            className="revision-send-action disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!session || !message.trim() || isSending}
            onClick={() => void sendMessage()}
            title={isTurnRunning ? "发送引导" : "提交给 Codex"}
          >
            {isSending ? <LoaderCircle size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  );

  const compactProcessStrip = compactProcesses.length ? (
    <div className="revision-process-strip" aria-label="运行状态列表">
      <div className="revision-process-strip-header">
        <span>运行状态</span>
        <span>共 {compactProcesses.length} 项</span>
      </div>
      <div className="revision-process-scroll">
        {compactProcesses.map((item) => {
          const status = String(item.observed_status || item.status || "");
          return (
            <div key={`${item.kind}:${item.id}`} className="revision-process-pill">
              <RuntimeActivityRing status={status} size="sm" title={item.display_status || status || item.kind} />
              <span className="min-w-0 flex-1 break-words">{item.label || item.kind}</span>
              <span className="shrink-0 text-[11px] text-[var(--muted)]">{item.display_status || status}</span>
              {typeof item.progress_percent === "number" ? <span className="text-[var(--muted)]">{Math.round(item.progress_percent)}%</span> : null}
              {item.can_resume ? (
                <button type="button" className="revision-process-action" disabled={isProcessBusy} onClick={() => void resumeProcess(item)}>
                  续跑
                </button>
              ) : null}
              {item.can_cancel ? (
                <button type="button" className="revision-process-action" disabled={isProcessBusy} onClick={() => void cancelProcess(item)}>
                  停止
                </button>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  ) : null;

  const centerPane = (
    <div className="revision-thread-column flex h-full min-h-0 flex-col gap-2 overflow-hidden">
      {compactProcessStrip}
      <CodexTimeline events={events} status={status} streamState={streamState} />
      {nativeComposer}
    </div>
  );

  const rightPane = (
    <ReportPreviewPane
      detail={detail}
      session={session}
      files={files}
      diffFiles={diffFiles}
      annotations={annotations}
      canPublish={canPublish}
      isPublishing={isPublishing}
      onPublish={() => void publishRevision()}
      onCreateAnnotation={(annotation) => void createAnnotation(annotation)}
      onDeleteAnnotation={(annotationId) => void deleteAnnotation(annotationId)}
      onUseAnnotationsAsGuidance={(text) => void sendMessageText(text)}
    />
  );

  return (
    <section className="revision-workbench flex min-h-dvh w-full flex-col overflow-auto p-0 text-white lg:h-dvh lg:overflow-hidden">
      <div className="revision-topbar flex shrink-0 flex-wrap items-center justify-between gap-3 px-3">
        <div className="flex min-w-0 items-center gap-3">
          <Link
            href={backHref}
            className="surface-chip relative z-10 inline-flex shrink-0 cursor-pointer items-center gap-2"
            onClick={(event) => {
              event.preventDefault();
              if (onBack) {
                onBack();
                return;
              }
              router.push(backHref);
            }}
          >
            <ArrowLeft size={15} />
            返回
          </Link>
          <div className="min-w-0">
            <h2 className="truncate text-[15px] font-semibold tracking-[-0.02em] text-[var(--text-strong)]">后续改造</h2>
            <p className="hidden text-[11px] text-[var(--muted)] md:block">
              {workspaceMode === "session" ? "独立工作区 · Codex 会话 · 工具调用" : "Codex 会话 · 工具调用 · 报告预览"}
            </p>
          </div>
        </div>
        <button type="button" className="surface-chip inline-flex items-center gap-2" onClick={() => void loadReports()}>
          <RefreshCw size={15} className={isLoading ? "animate-spin" : ""} />
          刷新报告库
        </button>
      </div>

      <ResizableWorkbenchLayout left={leftPane} center={centerPane} right={rightPane} />
    </section>
  );
}
