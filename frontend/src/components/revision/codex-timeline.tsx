"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Bot, CheckCircle2, ChevronDown, MessageSquareText, TerminalSquare, XCircle } from "lucide-react";

import type { ReportAgentEvent } from "@/lib/types";

type TimelineItem =
  | { kind: "event"; id: string; event: ReportAgentEvent }
  | { kind: "thinking"; id: string; events: ReportAgentEvent[] }
  | { kind: "tool"; id: string; call?: ReportAgentEvent; result?: ReportAgentEvent };

function formatTime(value: string | undefined) {
  if (!value) return "";
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

function eventLabel(kind: string) {
  const labels: Record<string, string> = {
    user_message: "用户",
    assistant_message: "Codex",
    tool_call: "工具调用",
    tool_result: "工具结果",
    file_changed: "文件变更",
    artifact_created: "产物生成",
    preview_updated: "预览更新",
    blocked_change: "阻断修改",
    runtime_stage: "运行阶段",
    turn_started: "开始执行",
    turn_completed: "执行完成",
    turn_failed: "执行失败",
    turn_cancelled: "已停止",
    verification_failed: "验收失败",
    verification_passed: "验收通过",
    auto_repair_started: "自动纠偏",
    user_guidance: "用户引导",
    thinking: "思考中",
    native_status: "原生状态",
    native_error: "原生错误",
    codex_thread_started: "Codex 会话",
    session_created: "会话创建",
    attachment_uploaded: "附件上传",
    data_profile_created: "数据画像",
    chart_plan_created: "补图计划",
    chart_rendered: "图表生成",
    chart_substituted: "替代图生成",
  };
  return labels[kind] || kind;
}

function eventTone(kind: string, isError?: boolean) {
  if (isError || kind.includes("failed") || kind === "blocked_change" || kind === "native_error") {
    return "border-red-300/30 bg-red-500/10 text-red-100";
  }
  if (kind === "tool_call" || kind === "tool_result" || kind === "runtime_stage") {
    return "border-cyan-300/20 bg-cyan-500/8 text-cyan-50";
  }
  if (
    kind === "artifact_created" ||
    kind === "preview_updated" ||
    kind === "turn_completed" ||
    kind === "verification_passed" ||
    kind === "attachment_uploaded" ||
    kind === "data_profile_created" ||
    kind === "chart_plan_created" ||
    kind === "chart_rendered" ||
    kind === "chart_substituted"
  ) {
    return "border-emerald-300/20 bg-emerald-500/8 text-emerald-50";
  }
  if (kind === "auto_repair_started") {
    return "border-amber-300/25 bg-amber-500/10 text-amber-50";
  }
  if (kind === "user_message" || kind === "user_guidance") {
    return "border-orange-300/20 bg-orange-500/10 text-orange-50";
  }
  if (kind === "thinking") {
    return "border-white/10 bg-white/4 text-[var(--muted)]";
  }
  return "border-white/10 bg-white/5 text-[var(--text)]";
}

function eventIcon(event: ReportAgentEvent) {
  const displayKind = event.display_kind || event.kind;
  if (displayKind === "tool_call" || displayKind === "tool_result" || event.kind === "runtime_stage") {
    return <TerminalSquare size={14} />;
  }
  if (displayKind === "error" || event.is_error) {
    return <XCircle size={14} />;
  }
  if (event.kind === "assistant_message" || event.role === "assistant") {
    return <Bot size={14} />;
  }
  if (event.kind === "user_message" || event.role === "user") {
    return <MessageSquareText size={14} />;
  }
  return <CheckCircle2 size={14} />;
}

function eventBody(event: ReportAgentEvent) {
  if (event.path === "annotations.json") {
    return event.kind === "file_changed" ? "报告批注已更新。" : "报告批注已保存。";
  }
  return event.output_preview || event.text || event.command || event.tool_name || event.stage_id || "事件已记录。";
}

function buildTimelineItems(events: ReportAgentEvent[]) {
  const items: TimelineItem[] = [];
  const toolById = new Map<string, Extract<TimelineItem, { kind: "tool" }>>();
  let thinkingBucket: ReportAgentEvent[] = [];
  let thinkingIndex = 0;

  function flushThinking() {
    if (!thinkingBucket.length) return;
    items.push({
      kind: "thinking",
      id: `thinking-${thinkingIndex}-${thinkingBucket[0]?.event_id || 0}`,
      events: thinkingBucket,
    });
    thinkingIndex += 1;
    thinkingBucket = [];
  }

  for (const event of events) {
    if (event.kind === "thinking") {
      thinkingBucket.push(event);
      continue;
    }
    flushThinking();
    const displayKind = event.display_kind || event.kind;
    if ((displayKind === "tool_call" || displayKind === "tool_result") && event.tool_call_id) {
      const existing = toolById.get(event.tool_call_id) || { kind: "tool" as const, id: `tool-${event.tool_call_id}` };
      if (displayKind === "tool_call") existing.call = event;
      else existing.result = event;
      if (!toolById.has(event.tool_call_id)) {
        toolById.set(event.tool_call_id, existing);
        items.push(existing);
      }
      continue;
    }
    items.push({ kind: "event", id: `event-${event.event_id}`, event });
  }
  flushThinking();
  return items;
}

function EventCard({ event }: { event: ReportAgentEvent }) {
  return (
    <article className={`rounded-[18px] border px-3.5 py-3 ${eventTone(event.kind, event.is_error)}`}>
      <div className="mb-2 flex items-center justify-between gap-2 text-[11px] uppercase tracking-[0.16em] opacity-80">
        <span className="inline-flex items-center gap-1.5">
          {eventIcon(event)}
          {eventLabel(event.kind)}
        </span>
        <span>{formatTime(event.timestamp)}</span>
      </div>
      <p className="whitespace-pre-wrap break-words text-sm leading-6">{eventBody(event)}</p>
    </article>
  );
}

function ToolCard({ call, result }: { call?: ReportAgentEvent; result?: ReportAgentEvent }) {
  const event = result || call;
  if (!event) return null;
  return (
    <article className="rounded-[18px] border border-white/10 bg-white/5 px-3.5 py-3 text-[var(--text-strong)]">
      <div className="mb-2 flex items-center justify-between gap-2 text-[11px] uppercase tracking-[0.16em] opacity-80">
        <span className="inline-flex items-center gap-1.5">
          <TerminalSquare size={14} />
          工具调用
        </span>
        <span>{formatTime(event.timestamp)}</span>
      </div>
      <div className="rounded-[12px] border border-white/10 bg-black/20 px-3 py-2">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
          <span className="font-semibold text-[var(--text-strong)]">{event.tool_name || call?.tool_name || "tool"}</span>
          {result?.status ? <span className="surface-chip !px-2 !py-1">{result.status}</span> : null}
          {typeof result?.exit_code === "number" ? <span>exit {result.exit_code}</span> : null}
          {typeof result?.duration_ms === "number" ? <span>{Math.round(result.duration_ms)}ms</span> : null}
        </div>
        {call?.command ? (
          <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap rounded-[10px] bg-black/25 p-2 text-xs leading-5 text-[var(--text-strong)]">
            {call.command}
          </pre>
        ) : null}
      </div>
      {result ? <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6">{eventBody(result)}</p> : null}
    </article>
  );
}

function ThinkingCard({ events }: { events: ReportAgentEvent[] }) {
  const [open, setOpen] = useState(false);
  const latest = events[events.length - 1];
  return (
    <article className={`rounded-[18px] border px-3.5 py-3 ${eventTone("thinking")}`}>
      <button
        type="button"
        className="flex w-full items-center justify-between gap-2 text-left text-[11px] uppercase tracking-[0.16em]"
        onClick={() => setOpen((current) => !current)}
      >
        <span className="inline-flex items-center gap-1.5">
          <Bot size={14} />
          思考中 / {events.length} 条
        </span>
        <span className="inline-flex items-center gap-2">
          {formatTime(latest?.timestamp)}
          <ChevronDown size={14} className={open ? "rotate-180 transition" : "transition"} />
        </span>
      </button>
      <p className="mt-2 text-sm leading-6">{eventBody(latest)}</p>
      {open ? (
        <div className="mt-3 space-y-2">
          {events.map((event) => (
            <p key={event.event_id} className="rounded-[12px] bg-black/20 px-3 py-2 text-xs leading-5">
              {eventBody(event)}
            </p>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export function CodexTimeline({
  events,
  status,
  streamState,
}: {
  events: ReportAgentEvent[];
  status: string;
  streamState: "idle" | "connecting" | "open" | "retrying";
}) {
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const [isPinnedToBottom, setIsPinnedToBottom] = useState(true);
  const items = useMemo(() => buildTimelineItems(events), [events]);
  const stats = useMemo(() => {
    const toolCallIds = new Set<string>();
    let fileChanges = 0;
    let artifacts = 0;
    let errors = 0;
    let charts = 0;
    for (const event of events) {
      const displayKind = event.display_kind || event.kind;
      if (displayKind === "tool_call") toolCallIds.add(event.tool_call_id || String(event.event_id));
      if (event.kind === "file_changed") fileChanges += 1;
      if (event.kind === "artifact_created") artifacts += 1;
      if (event.kind === "chart_rendered" || event.kind === "chart_substituted") charts += 1;
      if (event.is_error || event.kind === "blocked_change" || event.kind === "native_error" || event.kind.includes("failed")) errors += 1;
    }
    return { tools: toolCallIds.size, fileChanges, artifacts, charts, errors };
  }, [events]);

  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller || !isPinnedToBottom) return;
    scroller.scrollTop = scroller.scrollHeight;
  }, [items, isPinnedToBottom]);

  function handleScroll() {
    const scroller = scrollerRef.current;
    if (!scroller) return;
    const distanceToBottom = scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight;
    setIsPinnedToBottom(distanceToBottom < 80);
  }

  return (
    <section className="soft-panel flex min-h-0 flex-1 flex-col overflow-hidden p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Codex Timeline</p>
          <h3 className="mt-1 text-lg font-semibold text-[var(--text-strong)]">工具调用与执行流</h3>
        </div>
        <div className="flex flex-wrap justify-end gap-2 text-xs">
          <span className="surface-chip">流式 {streamState}</span>
          <span className="surface-chip">{events.length} 条事件</span>
        </div>
      </div>
      <div className="mb-3 flex flex-wrap gap-2 text-xs">
        <span className="surface-chip">Tools {stats.tools}</span>
        <span className="surface-chip">Files {stats.fileChanges}</span>
        <span className="surface-chip">Artifacts {stats.artifacts}</span>
        <span className="surface-chip">Charts {stats.charts}</span>
        <span className={`surface-chip ${stats.errors ? "border-red-300/30 text-red-100" : ""}`}>Errors {stats.errors}</span>
      </div>
      <div ref={scrollerRef} className="min-h-0 flex-1 space-y-3 overflow-auto rounded-[20px] border border-white/10 bg-black/12 p-3" onScroll={handleScroll}>
        {items.length ? (
          items.map((item) => {
            if (item.kind === "thinking") return <ThinkingCard key={item.id} events={item.events} />;
            if (item.kind === "tool") return <ToolCard key={item.id} call={item.call} result={item.result} />;
            return <EventCard key={item.id} event={item.event} />;
          })
        ) : (
          <p className="rounded-[18px] border border-white/10 bg-white/5 px-4 py-5 text-sm leading-7 text-[var(--muted)]">
            {status || "等待 Codex 事件。"}
          </p>
        )}
      </div>
      {!isPinnedToBottom ? (
        <button
          type="button"
          className="surface-chip mt-3 self-end !px-3 !py-2 text-xs"
          onClick={() => {
            const scroller = scrollerRef.current;
            if (scroller) scroller.scrollTop = scroller.scrollHeight;
            setIsPinnedToBottom(true);
          }}
        >
          回到底部
        </button>
      ) : null}
    </section>
  );
}
