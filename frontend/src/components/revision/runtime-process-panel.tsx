"use client";

import { LoaderCircle, Play, RefreshCw, Square } from "lucide-react";

import type { RuntimeProcessItem } from "@/lib/types";

import { RuntimeActivityRing } from "./runtime-activity-ring";

type Props = {
  processes: RuntimeProcessItem[];
  isBusy?: boolean;
  onRefresh: () => void;
  onCancel: (item: RuntimeProcessItem) => void;
  onResume: (item: RuntimeProcessItem) => void;
  title?: string;
  eyebrow?: string;
  emptyText?: string;
  maxHeightClassName?: string;
  onOpenReport?: (reportId: string) => void;
};

function kindLabel(kind: string) {
  const labels: Record<string, string> = {
    report_task: "报告任务",
    pipeline: "CLI 分析链",
    codex_run_task: "Codex Run",
    report_agent_turn: "后续改造 Turn",
    native_app_server: "原生 app-server",
    runtime_bootstrap: "可启动链路",
  };
  return labels[kind] || kind;
}

function statusLabel(status: string | undefined) {
  const safeStatus = String(status || "");
  const labels: Record<string, string> = {
    not_started: "未启动",
    queued: "排队中",
    starting: "启动中",
    running: "运行中",
    active: "在线",
    online: "在线",
    idle: "空闲",
    available: "可用",
    completed: "已完成",
    failed: "失败",
    error: "错误",
    cancelled: "已取消",
    cancelling: "取消中",
    timed_out: "超时",
    blocked: "已阻断",
    verifying: "验收中",
    auto_repairing: "自动纠偏中",
    stale_queued: "排队已停滞",
    stale_running: "运行已停滞",
    stale_turn: "引导已停滞",
    stale_cancelling: "取消已停滞",
  };
  if (labels[safeStatus]) {
    return labels[safeStatus];
  }
  if (safeStatus.endsWith("_completed")) {
    return "已完成";
  }
  if (safeStatus.startsWith("failed_") || safeStatus === "verification_failed") {
    return "失败";
  }
  if (safeStatus.startsWith("blocked_")) {
    return "已阻断";
  }
  return safeStatus || "未知";
}

function visibleStatus(item: RuntimeProcessItem) {
  return String(item.observed_status || item.status || "");
}

function visibleStatusLabel(item: RuntimeProcessItem) {
  return item.display_status || statusLabel(visibleStatus(item));
}

function statusTone(status: string | undefined) {
  const safeStatus = String(status || "");
  if (["failed", "error", "timed_out", "blocked"].includes(safeStatus) || safeStatus.startsWith("failed_")) {
    return "border-red-300/30 text-red-100";
  }
  if (safeStatus.startsWith("stale_")) {
    return "border-orange-300/35 text-orange-100";
  }
  if (["running", "queued", "cancelling", "starting", "verifying", "auto_repairing"].includes(safeStatus)) {
    return "border-cyan-300/25 text-cyan-50";
  }
  if (["completed", "available", "active", "online"].includes(safeStatus) || safeStatus.endsWith("_completed")) {
    return "border-emerald-300/25 text-emerald-50";
  }
  return "border-white/10 text-[var(--muted)]";
}

function resumeLabel(item: RuntimeProcessItem) {
  if (item.resume_label) {
    return item.resume_label;
  }
  const strategy = String(item.meta?.resume_strategy || "");
  const labels: Record<string, string> = {
    stale_codex_session_fresh_retry: "清理旧 Codex 会话并续跑",
    deterministic_repair_then_continue: "补齐缺失依赖并续跑",
    regenerate_workspace_contracts_then_continue: "重建合同并续跑",
    rebuild_workspace_then_restart_pipeline: "重建 workspace 并重跑",
    rollback_upstream_stage: "回滚上游阶段并续跑",
    blocked_missing_inputs: "检查缺失依赖",
  };
  if (labels[strategy]) {
    return labels[strategy];
  }
  if (item.is_stale) {
    return "续跑停滞阶段";
  }
  if (item.kind === "pipeline") {
    return "重试当前阶段";
  }
  if (item.kind === "runtime_bootstrap") {
    return "启动 CLI 长报告链";
  }
  return "续跑";
}

function retrofitModeLabel(value: unknown) {
  const mode = String(value || "");
  if (mode === "full_retrofit") {
    return "完整补建";
  }
  if (mode === "degraded_report_retrofit") {
    return "降级补建";
  }
  if (mode === "evidence_limited_retrofit") {
    return "证据有限补建";
  }
  return "";
}

function stringListMeta(value: unknown, limit = 4) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .slice(0, limit);
}

function minutesAgo(value: RuntimeProcessItem) {
  if (typeof value.age_seconds !== "number") {
    return "";
  }
  return `${Math.max(0, Math.round(value.age_seconds / 60))} 分钟`;
}

function formatDateTime(value: string | undefined) {
  if (!value) {
    return "";
  }
  try {
    return new Date(value).toLocaleString("zh-CN");
  } catch {
    return value;
  }
}

export function RuntimeProcessPanel({
  processes,
  isBusy,
  onRefresh,
  onCancel,
  onResume,
  title = "运行进程与续跑",
  eyebrow = "Runtime Processes",
  emptyText = "选择报告后，这里会显示 report task、CLI pipeline、Codex turn 和原生 app-server 状态。",
  maxHeightClassName = "max-h-[28dvh]",
  onOpenReport,
}: Props) {
  return (
    <section className="soft-panel min-h-0 overflow-hidden p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">{eyebrow}</p>
          <h3 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">{title}</h3>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="surface-chip !px-2 !py-1 text-[11px]">共 {processes.length} 项</span>
          <button type="button" className="surface-chip inline-flex items-center gap-2" onClick={onRefresh}>
            <RefreshCw size={14} className={isBusy ? "animate-spin" : ""} />
            刷新
          </button>
        </div>
      </div>

      <div className={`mt-4 space-y-2 overflow-auto pr-1 ${maxHeightClassName}`}>
        {processes.length ? (
          processes.map((item) => {
            const status = visibleStatus(item);
            const showResumeMeta = Boolean(
              item.can_resume ||
                item.is_stale ||
                ["failed", "blocked", "cancelled", "timed_out", "error"].includes(status),
            );
            const missingInputs = stringListMeta(item.meta?.blocking_missing_inputs);
            const availableAssets = stringListMeta(item.meta?.available_source_assets, 3);
            return (
              <article
                key={`${item.kind}:${item.id}`}
                className={`rounded-[16px] border border-white/10 bg-black/14 p-3 ${
                  onOpenReport && item.report_id ? "cursor-pointer transition hover:border-white/20 hover:bg-white/6" : ""
                }`}
                onClick={() => {
                  if (onOpenReport && item.report_id) {
                    onOpenReport(item.report_id);
                  }
                }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 gap-3">
                    <RuntimeActivityRing status={status} title={`${visibleStatusLabel(item)} / ${item.label || kindLabel(item.kind)}`} />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-[var(--text-strong)]">{item.label || kindLabel(item.kind)}</p>
                      <p className="mt-1 truncate font-mono text-[11px] text-[var(--muted)]">{item.id}</p>
                      {item.scope === "active" && item.report_id ? (
                        <p className="mt-1 truncate text-[11px] text-[var(--muted)]">{item.linked_report_title || item.report_id}</p>
                      ) : null}
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-2">
                    <span className={`surface-chip !px-2 !py-1 ${statusTone(status)}`}>{visibleStatusLabel(item)}</span>
                    {onOpenReport && item.report_id ? (
                      <button
                        type="button"
                        className="text-[11px] text-cyan-100 hover:text-white"
                        onClick={(event) => {
                          event.stopPropagation();
                          onOpenReport(item.report_id || "");
                        }}
                      >
                        打开报告
                      </button>
                    ) : null}
                  </div>
                </div>

                {typeof item.progress_percent === "number" ? (
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-[var(--accent-warm)]"
                      style={{ width: `${Math.max(0, Math.min(100, item.progress_percent))}%` }}
                    />
                  </div>
                ) : null}

                <div className="mt-2 text-xs leading-5 text-[var(--muted)]">
                  {item.stage_title || item.stage_id ? (
                    <p>
                      阶段：{item.stage_title || item.stage_id}
                      {item.progress_percent != null ? ` / ${Math.round(item.progress_percent)}%` : ""}
                    </p>
                  ) : null}
                  {item.error ? <p className="text-red-200">错误：{item.error}</p> : null}
                  {item.disabled_reason ? <p>不可续跑：{item.disabled_reason}</p> : null}
                  {showResumeMeta && item.meta?.resume_strategy ? <p>续跑策略：{String(item.meta.resume_strategy)}</p> : null}
                  {showResumeMeta && item.meta?.resume_issue_kind ? <p>问题类型：{String(item.meta.resume_issue_kind)}</p> : null}
                  {item.meta?.retrofit_mode ? <p>补建模式：{retrofitModeLabel(item.meta.retrofit_mode) || String(item.meta.retrofit_mode)}</p> : null}
                  {item.meta?.evidence_limited ? <p>结果类型：证据有限诊断版</p> : null}
                  {item.meta?.stale_reason ? <p>状态核对：{String(item.meta.stale_reason)}</p> : null}
                  {item.meta?.reconciliation_reason ? <p>核对依据：{String(item.meta.reconciliation_reason)}</p> : null}
                  {showResumeMeta && item.meta?.stale_session_id ? <p className="truncate font-mono">stale_session={String(item.meta.stale_session_id)}</p> : null}
                  {showResumeMeta && item.meta?.repair_rule_id ? <p className="font-mono">repair_rule={String(item.meta.repair_rule_id)}</p> : null}
                  {showResumeMeta && item.meta?.retry_stage_id ? <p className="font-mono">retry_stage={String(item.meta.retry_stage_id)}</p> : null}
                  {showResumeMeta && item.meta?.rollback_stage_id ? <p className="font-mono">rollback_stage={String(item.meta.rollback_stage_id)}</p> : null}
                  {showResumeMeta && item.meta?.last_repair_log_path ? <p className="truncate font-mono">repair_log={String(item.meta.last_repair_log_path)}</p> : null}
                  {showResumeMeta && item.meta?.contract_batch_manifest_path ? (
                    <p className="truncate font-mono">contract_batch={String(item.meta.contract_batch_manifest_path)}</p>
                  ) : null}
                  {showResumeMeta && item.meta?.workspace_rebuild_path ? <p className="truncate font-mono">rebuild={String(item.meta.workspace_rebuild_path)}</p> : null}
                  {missingInputs.length ? <p>缺失依赖：{missingInputs.join("、")}</p> : null}
                  {item.kind === "runtime_bootstrap" && availableAssets.length ? <p>可用资产：{availableAssets.join("、")}</p> : null}
                  {item.last_event ? <p>最新事件：{item.last_event}</p> : null}
                  {minutesAgo(item) ? <p>更新距今：{minutesAgo(item)}</p> : null}
                  {item.updated_at ? <p>更新：{formatDateTime(item.updated_at)}</p> : null}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {item.can_resume ? (
                    <button
                      type="button"
                      className="surface-chip inline-flex items-center gap-2 !px-2 !py-1"
                      disabled={isBusy}
                      onClick={(event) => {
                        event.stopPropagation();
                        onResume(item);
                      }}
                    >
                      {isBusy ? <LoaderCircle size={13} className="animate-spin" /> : <Play size={13} />}
                      {resumeLabel(item)}
                    </button>
                  ) : null}
                  {item.can_cancel ? (
                    <button
                      type="button"
                      className="surface-chip inline-flex items-center gap-2 !px-2 !py-1"
                      disabled={isBusy}
                      onClick={(event) => {
                        event.stopPropagation();
                        onCancel(item);
                      }}
                    >
                      <Square size={13} />
                      取消
                    </button>
                  ) : null}
                </div>
              </article>
            );
          })
        ) : (
          <p className="rounded-[16px] border border-white/10 bg-white/5 px-4 py-5 text-sm leading-7 text-[var(--muted)]">
            {emptyText}
          </p>
        )}
      </div>
    </section>
  );
}
