"use client";

import { useEffect, useState } from "react";

type Props = {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
};

const STORAGE_KEY = "asteria.revisionWorkbench.columns.v7";
const MIN_LEFT = 300;
const MAX_LEFT = 460;
const MIN_CENTER = 420;
const MAX_CENTER = 720;
const DEFAULT_LEFT = 340;
const DEFAULT_CENTER = 520;

function clamp(value: number, min: number, max: number) {
  if (!Number.isFinite(value)) {
    return min;
  }
  return Math.min(max, Math.max(min, value));
}

function loadColumns() {
  if (typeof window === "undefined") {
    return { left: DEFAULT_LEFT, center: DEFAULT_CENTER };
  }
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}") as { left?: number; center?: number };
    return {
      left: clamp(Number(parsed.left || DEFAULT_LEFT), MIN_LEFT, MAX_LEFT),
      center: clamp(Number(parsed.center || DEFAULT_CENTER), MIN_CENTER, MAX_CENTER),
    };
  } catch {
    return { left: DEFAULT_LEFT, center: DEFAULT_CENTER };
  }
}

export function ResizableWorkbenchLayout({ left, center, right }: Props) {
  const [columns, setColumns] = useState({ left: DEFAULT_LEFT, center: DEFAULT_CENTER });
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [centerCollapsed, setCenterCollapsed] = useState(false);
  const [isNarrow, setIsNarrow] = useState(false);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setColumns(loadColumns());
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(columns));
  }, [columns]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const query = window.matchMedia("(max-width: 1023px)");
    const update = () => setIsNarrow(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  function startDrag(handle: "left" | "center", event: React.PointerEvent<HTMLDivElement>) {
    const startX = event.clientX;
    const startColumns = columns;
    event.currentTarget.setPointerCapture(event.pointerId);
    const onMove = (moveEvent: PointerEvent) => {
      const delta = moveEvent.clientX - startX;
      setColumns((current) => {
        if (handle === "left") {
          return { ...current, left: clamp(startColumns.left + delta, MIN_LEFT, MAX_LEFT) };
        }
        return { ...current, center: clamp(startColumns.center + delta, MIN_CENTER, MAX_CENTER) };
      });
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  const leftWidth = leftCollapsed ? 48 : columns.left;
  const centerWidth = centerCollapsed ? 48 : columns.center;
  const gridTemplateColumns = isNarrow
    ? "minmax(0, 1fr)"
    : `${leftWidth}px 10px ${centerWidth}px 10px minmax(0, 1fr)`;

  if (isNarrow) {
    return (
      <div className="revision-layout grid min-h-0 flex-1 grid-cols-1 gap-3 overflow-auto p-3">
        <div className="min-w-0">{left}</div>
        <div className="min-w-0">{center}</div>
        <div className="min-w-0">{right}</div>
      </div>
    );
  }

  return (
    <div
      className="revision-layout grid min-h-0 flex-1 gap-0"
      style={{
        gridTemplateColumns,
      }}
    >
      <div className="min-h-0 min-w-0 overflow-hidden">
        {leftCollapsed ? (
          <button
            type="button"
            className="surface-chip h-full w-full justify-center [writing-mode:vertical-rl]"
            onClick={() => setLeftCollapsed(false)}
          >
            展开报告与输入
          </button>
        ) : (
          left
        )}
      </div>
      <div
        className="group flex cursor-col-resize items-center justify-center"
        role="separator"
        onPointerDown={(event) => startDrag("left", event)}
        onDoubleClick={() => setLeftCollapsed((value) => !value)}
        title="拖拽调整左栏宽度，双击折叠或展开"
      >
        <div className="revision-splitter h-full w-px rounded-full bg-white/10 transition group-hover:bg-[var(--accent-warm)]/70" />
      </div>
      <div className="min-h-0 min-w-0 overflow-hidden">
        {centerCollapsed ? (
          <button
            type="button"
            className="surface-chip h-full w-full justify-center [writing-mode:vertical-rl]"
            onClick={() => setCenterCollapsed(false)}
          >
            展开 Timeline
          </button>
        ) : (
          center
        )}
      </div>
      <div
        className="group flex cursor-col-resize items-center justify-center"
        role="separator"
        onPointerDown={(event) => startDrag("center", event)}
        onDoubleClick={() => setCenterCollapsed((value) => !value)}
        title="拖拽调整 Timeline 宽度，双击折叠或展开"
      >
        <div className="revision-splitter h-full w-px rounded-full bg-white/10 transition group-hover:bg-[var(--accent-warm)]/70" />
      </div>
      <div className="min-h-0 min-w-0 overflow-hidden">{right}</div>
    </div>
  );
}
