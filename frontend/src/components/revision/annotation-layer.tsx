"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import type { ReportAnnotation } from "@/lib/types";

type AnnotationTool = "select" | "pen" | "rectangle" | "highlight" | "eraser";

type Props = {
  annotations: ReportAnnotation[];
  artifactUrl: string;
  artifactType: "html" | "pdf";
  pageNumber?: number | null;
  contentWidth?: number;
  contentHeight?: number;
  enabled: boolean;
  tool: AnnotationTool;
  color: string;
  strokeWidth: number;
  onCreate: (annotation: Omit<ReportAnnotation, "annotation_id" | "created_at" | "updated_at">) => void;
  onDelete: (annotationId: string) => void;
};

function clamp(value: number) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function pointsToPath(points: Array<{ x: number; y: number }>, width: number, height: number) {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x * width} ${point.y * height}`)
    .join(" ");
}

function rectFromPoints(points: Array<{ x: number; y: number }>, width: number, height: number) {
  const [start, end] = points;
  const x1 = Math.min(start?.x ?? 0, end?.x ?? 0) * width;
  const y1 = Math.min(start?.y ?? 0, end?.y ?? 0) * height;
  const x2 = Math.max(start?.x ?? 0, end?.x ?? 0) * width;
  const y2 = Math.max(start?.y ?? 0, end?.y ?? 0) * height;
  return { x: x1, y: y1, width: Math.max(1, x2 - x1), height: Math.max(1, y2 - y1) };
}

function isTinyDraft(tool: AnnotationTool, points: Array<{ x: number; y: number }>) {
  if (tool === "pen") {
    return points.length < 3;
  }
  const [start, end] = points;
  if (!start || !end) {
    return true;
  }
  return Math.abs(start.x - end.x) < 0.006 && Math.abs(start.y - end.y) < 0.006;
}

export function AnnotationLayer({
  annotations,
  artifactUrl,
  artifactType,
  pageNumber,
  contentWidth,
  contentHeight,
  enabled,
  tool,
  color,
  strokeWidth,
  onCreate,
  onDelete,
}: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const draftRef = useRef<Array<{ x: number; y: number }>>([]);
  const activePointerIdRef = useRef<number | null>(null);
  const [draft, setDraft] = useState<Array<{ x: number; y: number }>>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [box, setBox] = useState({ width: Math.max(1, contentWidth || 1), height: Math.max(1, contentHeight || 1) });

  const visibleAnnotations = useMemo(
    () =>
      annotations.filter(
        (annotation) =>
          annotation.artifact_type === artifactType &&
          (artifactType !== "pdf" || Number(annotation.page_number || 1) === Number(pageNumber || 1)),
      ),
    [annotations, artifactType, pageNumber],
  );

  useEffect(() => {
    const element = rootRef.current;
    if (!element) {
      return;
    }

    const syncSize = () => {
      const rect = element.getBoundingClientRect();
      setBox({
        width: Math.max(1, contentWidth || element.offsetWidth || rect.width || 1),
        height: Math.max(1, contentHeight || element.offsetHeight || rect.height || 1),
      });
    };

    syncSize();
    const observer = new ResizeObserver(syncSize);
    observer.observe(element);
    return () => observer.disconnect();
  }, [contentHeight, contentWidth]);

  function setDraftPoints(points: Array<{ x: number; y: number }>) {
    draftRef.current = points;
    setDraft(points);
  }

  function clientPoint(clientX: number, clientY: number) {
    const rect = rootRef.current?.getBoundingClientRect();
    if (!rect) {
      return { x: 0, y: 0 };
    }
    return {
      x: clamp((clientX - rect.left) / Math.max(1, rect.width)),
      y: clamp((clientY - rect.top) / Math.max(1, rect.height)),
    };
  }

  function startDrawing(event: React.PointerEvent<HTMLDivElement>) {
    if (!enabled || tool === "select" || tool === "eraser") {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    activePointerIdRef.current = event.pointerId;
    setDraftPoints([clientPoint(event.clientX, event.clientY)]);
    setIsDrawing(true);
  }

  function updateDrawing(event: React.PointerEvent<HTMLDivElement>) {
    if (!isDrawing || !enabled || tool === "select" || tool === "eraser" || activePointerIdRef.current !== event.pointerId) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    const point = clientPoint(event.clientX, event.clientY);
    const current = draftRef.current;
    setDraftPoints(tool === "pen" ? [...current, point].slice(-400) : [current[0] || point, point]);
  }

  function completeDrawing() {
    const current = draftRef.current;
    const points = current.length === 1 ? [current[0], current[0]] : current;
    setDraftPoints([]);
    setIsDrawing(false);
    if (points.length < 2 || isTinyDraft(tool, points)) {
      return;
    }
    const note = window.prompt("给这条批注写一句修改意见，可以留空；取消则不保存。", "");
    if (note === null) {
      return;
    }
    onCreate({
      artifact_url: artifactUrl,
      artifact_type: artifactType,
      page_number: artifactType === "pdf" ? Number(pageNumber || 1) : null,
      target_kind: artifactType === "pdf" ? "page" : "html",
      points,
      shape: tool === "highlight" ? "highlight" : tool === "pen" ? "pen" : "rectangle",
      color,
      stroke_width: strokeWidth,
      note,
    });
  }

  function finishDrawing(event: React.PointerEvent<HTMLDivElement>) {
    if (!isDrawing || activePointerIdRef.current !== event.pointerId) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    try {
      event.currentTarget.releasePointerCapture(event.pointerId);
    } catch {
      // Pointer capture release is best effort.
    }
    activePointerIdRef.current = null;
    completeDrawing();
  }

  return (
    <div
      ref={rootRef}
      className={`absolute inset-0 z-20 ${enabled ? "pointer-events-auto cursor-crosshair" : "pointer-events-none"}`}
      style={{ touchAction: enabled ? "none" : "auto" }}
      onPointerDown={startDrawing}
      onPointerMove={updateDrawing}
      onPointerUp={finishDrawing}
      onPointerCancel={finishDrawing}
    >
      <svg className="h-full w-full" viewBox={`0 0 ${box.width} ${box.height}`} preserveAspectRatio="none">
        {visibleAnnotations.map((annotation) => {
          if (annotation.shape === "pen") {
            return (
              <path
                key={annotation.annotation_id}
                d={pointsToPath(annotation.points || [], box.width, box.height)}
                fill="none"
                stroke={annotation.color}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={annotation.stroke_width}
                className={tool === "eraser" ? "pointer-events-auto cursor-not-allowed" : "pointer-events-none"}
                onPointerDown={(event) => {
                  if (tool === "eraser") {
                    event.stopPropagation();
                    onDelete(annotation.annotation_id);
                  }
                }}
              />
            );
          }
          const rect = rectFromPoints(annotation.points || [], box.width, box.height);
          return (
            <rect
              key={annotation.annotation_id}
              {...rect}
              fill={annotation.shape === "highlight" ? annotation.color : "transparent"}
              fillOpacity={annotation.shape === "highlight" ? 0.2 : 0}
              stroke={annotation.color}
              strokeWidth={annotation.stroke_width}
              rx={8}
              className={tool === "eraser" ? "pointer-events-auto cursor-not-allowed" : "pointer-events-none"}
              onPointerDown={(event) => {
                if (tool === "eraser") {
                  event.stopPropagation();
                  onDelete(annotation.annotation_id);
                }
              }}
            />
          );
        })}
        {draft.length ? (
          tool === "pen" ? (
            <path
              d={pointsToPath(draft, box.width, box.height)}
              fill="none"
              stroke={color}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={strokeWidth}
            />
          ) : (
            <rect
              {...rectFromPoints(draft.length === 1 ? [draft[0], draft[0]] : draft, box.width, box.height)}
              fill={tool === "highlight" ? color : "transparent"}
              fillOpacity={tool === "highlight" ? 0.18 : 0}
              stroke={color}
              strokeDasharray="6 5"
              strokeWidth={strokeWidth}
              rx={8}
            />
          )
        ) : null}
      </svg>
    </div>
  );
}

export type { AnnotationTool };
