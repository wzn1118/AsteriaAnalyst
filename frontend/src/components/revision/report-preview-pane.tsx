"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Brush,
  CheckCircle2,
  Eraser,
  FileCode2,
  GitCompare,
  Highlighter,
  LoaderCircle,
  Maximize2,
  MessageSquareText,
  MousePointer2,
  Play,
  RectangleHorizontal,
  RefreshCw,
  Trash2,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

import { resolveArtifactUrl } from "@/lib/api";
import type {
  ReportAgentDiffFile,
  ReportAgentFile,
  ReportAgentSession,
  ReportAnnotation,
  ReportCatalogDetail,
  ReportDownloadable,
} from "@/lib/types";

import { AnnotationLayer, type AnnotationTool } from "./annotation-layer";

type PreviewCandidate = {
  id: string;
  name: string;
  url: string;
  type: "html" | "pdf";
  source: "revision" | "original" | "workspace";
};

type Props = {
  detail: ReportCatalogDetail | null;
  session: ReportAgentSession | null;
  files: ReportAgentFile[];
  diffFiles: ReportAgentDiffFile[];
  annotations: ReportAnnotation[];
  canPublish: boolean;
  isPublishing: boolean;
  onPublish: () => void;
  onCreateAnnotation: (annotation: Omit<ReportAnnotation, "annotation_id" | "created_at" | "updated_at">) => void;
  onDeleteAnnotation: (annotationId: string) => void;
  onUseAnnotationsAsGuidance: (message: string) => void;
};

const HEIGHT_KEY = "asteria.revisionPreview.height.v2";
type PdfFitMode = "fit-page" | "fit-width" | "custom";
type PdfViewportLike = { width: number; height: number };
type PdfPageLike = {
  getViewport: (options: { scale: number }) => PdfViewportLike;
  render: (context: unknown) => { promise: Promise<unknown> };
};
type PdfDocumentLike = {
  numPages: number;
  getPage: (pageNumber: number) => Promise<PdfPageLike>;
};
type PdfLoadingTaskLike = {
  promise: Promise<PdfDocumentLike>;
  destroy?: () => void;
};

function fileTypeFromName(name: string): "html" | "pdf" | "" {
  const lower = String(name || "").toLowerCase();
  if (lower.endsWith(".html") || lower.endsWith(".htm")) {
    return "html";
  }
  if (lower.endsWith(".pdf")) {
    return "pdf";
  }
  return "";
}

function candidateFromDownloadable(item: ReportDownloadable, source: PreviewCandidate["source"]): PreviewCandidate | null {
  const type = item.type === "html" || item.type === "pdf" ? item.type : fileTypeFromName(item.name || item.path);
  const url = resolveArtifactUrl(item.path);
  if ((type !== "html" && type !== "pdf") || !url) {
    return null;
  }
  return {
    id: `${source}:${item.path}`,
    name: item.name || item.purpose || item.path,
    url,
    type,
    source,
  };
}

function normalizeArtifactPath(value: string | undefined) {
  const rawValue = String(value || "").trim();
  if (!rawValue) {
    return "";
  }
  try {
    return new URL(rawValue.replace(/\\/g, "/"), "http://asteria.local").pathname.replace(/\/+$/, "").toLowerCase();
  } catch {
    return rawValue.split(/[?#]/)[0].replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
  }
}

function artifactFileName(value: string | undefined) {
  const normalized = normalizeArtifactPath(value);
  return normalized.split("/").filter(Boolean).pop() || "";
}

function clampUnit(value: number) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function isSameReportArtifact(annotation: ReportAnnotation, selected: PreviewCandidate) {
  if (annotation.artifact_type !== selected.type) {
    return false;
  }
  if (annotation.artifact_url === selected.url || annotation.artifact_id === selected.id) {
    return true;
  }
  const annotationPath = normalizeArtifactPath(annotation.artifact_url);
  const selectedPath = normalizeArtifactPath(selected.url);
  if (annotationPath && annotationPath === selectedPath) {
    return true;
  }
  const annotationName = String(annotation.artifact_name || "").trim();
  if (annotationName && annotationName === selected.name) {
    return true;
  }
  const annotationFile = artifactFileName(annotation.artifact_url || annotation.artifact_name);
  const selectedFile = artifactFileName(selected.url || selected.name);
  return Boolean(annotationFile && selectedFile && annotationFile === selectedFile);
}

function annotationCoordinateSpace(annotation: ReportAnnotation, selected: PreviewCandidate) {
  if (annotation.coordinate_space) {
    return annotation.coordinate_space;
  }
  return selected.type === "pdf" ? "pdf_page_normalized_v3" : "html_viewport_legacy";
}

function projectAnnotationForPreview(
  annotation: ReportAnnotation,
  selected: PreviewCandidate,
  htmlPreviewHeight: number,
  previewHeight: number,
) {
  if (selected.type !== "html") {
    return annotation;
  }
  const coordinateSpace = annotationCoordinateSpace(annotation, selected);
  if (coordinateSpace !== "html_viewport_legacy") {
    return annotation;
  }
  const documentHeight = Math.max(1, Number(annotation.document_height || htmlPreviewHeight || previewHeight || 1));
  const viewportHeight = Math.max(1, Number(annotation.viewport_height || previewHeight || 1));
  const scrollOffset = Math.max(0, Number(annotation.scroll_offset || 0));
  return {
    ...annotation,
    coordinate_space: "html_document",
    points: (annotation.points || []).map((point) => ({
      x: clampUnit(Number(point.x || 0)),
      y: clampUnit((clampUnit(Number(point.y || 0)) * viewportHeight + scrollOffset) / documentHeight),
    })),
  };
}

function loadPreviewHeight() {
  if (typeof window === "undefined") {
    return 760;
  }
  const preferred = Math.max(520, window.innerHeight - 285);
  const value = Number(window.localStorage.getItem(HEIGHT_KEY) || preferred || 760);
  return Math.min(Math.max(520, window.innerHeight - 180), Math.max(420, value));
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

export function ReportPreviewPane({
  detail,
  session,
  files,
  diffFiles,
  annotations,
  canPublish,
  isPublishing,
  onPublish,
  onCreateAnnotation,
  onDeleteAnnotation,
  onUseAnnotationsAsGuidance,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const previewScrollRef = useRef<HTMLDivElement | null>(null);
  const lastPreviewScrollRef = useRef({ id: "", left: 0, top: 0 });
  const [selectedId, setSelectedId] = useState("");
  const [previewNonce, setPreviewNonce] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [pdfFitMode, setPdfFitMode] = useState<PdfFitMode>("fit-page");
  const [pdfPage, setPdfPage] = useState(1);
  const [pdfPageCount, setPdfPageCount] = useState(1);
  const [pdfPageBox, setPdfPageBox] = useState({ width: 0, height: 0, renderScale: 1, pdfScale: 1, baseWidth: 0, baseHeight: 0 });
  const [pdfError, setPdfError] = useState("");
  const [previewSize, setPreviewSize] = useState({ width: 0, height: 0 });
  const [htmlSource, setHtmlSource] = useState("");
  const [htmlError, setHtmlError] = useState("");
  const [htmlLoading, setHtmlLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [previewHeight, setPreviewHeight] = useState(760);
  const [tool, setTool] = useState<AnnotationTool>("select");
  const [color, setColor] = useState("#f97316");
  const [strokeWidth, setStrokeWidth] = useState(3);
  const [sidePanel, setSidePanel] = useState<"artifacts" | "diff" | "annotations" | "published">("artifacts");

  useEffect(() => {
    setPreviewHeight(loadPreviewHeight());
  }, []);

  const candidates = useMemo(() => {
    const result: PreviewCandidate[] = [];
    if (session?.preview_artifact) {
      const item = candidateFromDownloadable(session.preview_artifact, "revision");
      if (item) {
        result.push(item);
      }
    }
    if (session?.preview_url) {
      const type = fileTypeFromName(session.preview_url) || "html";
      const url = resolveArtifactUrl(session.preview_url);
      if (url) {
        result.push({
          id: `revision:${session.preview_url}`,
          name: "最新修订预览",
          url,
          type,
          source: "revision",
        });
      }
    }
    for (const item of detail?.downloadables || []) {
      const candidate = candidateFromDownloadable(item, "original");
      if (candidate) {
        result.push(candidate);
      }
    }
    for (const file of files) {
      const type = file.type === "html" || file.type === "pdf" ? file.type : fileTypeFromName(file.name);
      const url = resolveArtifactUrl(file.url);
      if ((type === "html" || type === "pdf") && url) {
        result.push({
          id: `workspace:${file.url}`,
          name: file.name,
          url,
          type,
          source: "workspace",
        });
      }
    }
    const deduped = new Map<string, PreviewCandidate>();
    for (const item of result) {
      const dedupeKey = `${item.type}:${normalizeArtifactPath(item.url) || item.id}`;
      if (!deduped.has(dedupeKey)) {
        deduped.set(dedupeKey, item);
      }
    }
    return [...deduped.values()].sort((left, right) => {
      const sourceWeight = { revision: 0, original: 1, workspace: 2 };
      const typeWeight = { html: 0, pdf: 1 };
      return sourceWeight[left.source] - sourceWeight[right.source] || typeWeight[left.type] - typeWeight[right.type];
    });
  }, [detail, files, session]);

  const selected = useMemo(() => {
    return candidates.find((item) => item.id === selectedId) || candidates[0] || null;
  }, [candidates, selectedId]);
  const selectedKey = selected?.id || "";
  const selectedType = selected?.type || "";
  const selectedUrl = selected?.url || "";
  const selectedArtifactUrl = resolveArtifactUrl(selectedUrl);
  const htmlPreviewHeight = Math.max(620, previewHeight);

  const selectedAnnotations = useMemo(() => {
    if (!selected) {
      return [];
    }
    return annotations.filter((annotation) => {
      if (!isSameReportArtifact(annotation, selected)) {
        return false;
      }
      if (selected.type === "pdf") {
        return Number(annotation.page_number || 1) === Number(pdfPage || 1);
      }
      return true;
    });
  }, [annotations, pdfPage, selected]);

  const layerAnnotations = useMemo(() => {
    if (!selected) {
      return [];
    }
    return selectedAnnotations.map((annotation) =>
      projectAnnotationForPreview(annotation, selected, htmlPreviewHeight, previewHeight),
    );
  }, [htmlPreviewHeight, previewHeight, selected, selectedAnnotations]);

  useEffect(() => {
    if (!selectedId && candidates[0]) {
      setSelectedId(candidates[0].id);
      return;
    }
    if (selectedId && candidates.length > 0 && !candidates.some((item) => item.id === selectedId)) {
      setSelectedId(candidates[0].id);
    }
  }, [candidates, selectedId]);

  useEffect(() => {
    const element = previewScrollRef.current;
    if (!element || !selectedKey) {
      return;
    }
    lastPreviewScrollRef.current = { id: selectedKey, left: 0, top: 0 };
    element.scrollTo({ left: 0, top: 0 });
  }, [selectedKey]);

  useEffect(() => {
    window.localStorage.setItem(HEIGHT_KEY, String(previewHeight));
  }, [previewHeight]);

  useEffect(() => {
    if (!selectedArtifactUrl || selectedType !== "html") {
      setHtmlSource("");
      setHtmlError("");
      setHtmlLoading(false);
      return;
    }
    const artifactUrl = selectedArtifactUrl;
    let cancelled = false;
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 12000);
    setHtmlError("");
    setHtmlLoading(true);
    setHtmlSource("");

    async function loadHtmlPreview() {
      try {
        const response = await fetch(artifactUrl, { cache: "no-store", signal: controller.signal });
        if (!response.ok) {
          throw new Error(`HTML 预览加载失败：${response.status}`);
        }
        const rawHtml = await response.text();
        const absoluteUrl = new URL(artifactUrl);
        const baseHref = new URL(".", absoluteUrl).href;
        const baseTag = `<base href="${baseHref}" />`;
        const withBase = /<head[^>]*>/i.test(rawHtml)
          ? rawHtml.replace(/<head([^>]*)>/i, `<head$1>${baseTag}`)
          : `<!doctype html><html><head>${baseTag}</head><body>${rawHtml}</body></html>`;
        if (!cancelled) {
          setHtmlSource(withBase);
        }
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error && error.name === "AbortError"
            ? "HTML 预览加载超时，请刷新或用新窗口打开。"
            : error instanceof Error
              ? error.message
              : String(error);
          setHtmlError(message);
        }
      } finally {
        window.clearTimeout(timeoutId);
        if (!cancelled) {
          setHtmlLoading(false);
        }
      }
    }

    void loadHtmlPreview();
    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [previewNonce, selectedArtifactUrl, selectedKey, selectedType]);

  useEffect(() => {
    const element = previewScrollRef.current;
    if (!element) {
      return;
    }
    const syncSize = () => {
      setPreviewSize({
        width: Math.max(0, element.clientWidth || 0),
        height: Math.max(0, element.clientHeight || 0),
      });
    };
    syncSize();
    const observer = new ResizeObserver(syncSize);
    observer.observe(element);
    window.addEventListener("resize", syncSize);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", syncSize);
    };
  }, [selectedKey, previewHeight]);

  useEffect(() => {
    if (!selectedArtifactUrl || selectedType !== "pdf") {
      setPdfLoading(false);
      return;
    }
    let cancelled = false;
    let loadingTask: PdfLoadingTaskLike | null = null;
    async function renderPdf() {
      setPdfError("");
      setPdfLoading(true);
      const canvas = canvasRef.current;
      if (!canvas || !selectedArtifactUrl) {
        setPdfLoading(false);
        return;
      }
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.mjs", import.meta.url).toString();
        loadingTask = pdfjs.getDocument(selectedArtifactUrl) as PdfLoadingTaskLike;
        const pdf = await loadingTask.promise;
        if (cancelled) {
          return;
        }
        setPdfPageCount(pdf.numPages);
        const safePage = Math.min(Math.max(1, pdfPage), pdf.numPages);
        if (safePage !== pdfPage) {
          setPdfPage(safePage);
          return;
        }
        const page = await pdf.getPage(safePage);
        const baseViewport = page.getViewport({ scale: 1 });
        const availableWidth = Math.max(260, (previewSize.width || previewScrollRef.current?.clientWidth || 900) - 72);
        const availableHeight = Math.max(260, (previewSize.height || previewScrollRef.current?.clientHeight || previewHeight) - 104);
        const fitWidthScale = availableWidth / Math.max(1, baseViewport.width);
        const fitPageScale = Math.min(fitWidthScale, availableHeight / Math.max(1, baseViewport.height));
        const effectiveScale =
          pdfFitMode === "fit-width"
            ? fitWidthScale
            : pdfFitMode === "fit-page"
              ? fitPageScale
              : zoom;
        const safeScale = Math.min(3, Math.max(0.2, effectiveScale || 1));
        const viewport = page.getViewport({ scale: safeScale });
        const context = canvas.getContext("2d");
        if (!context) {
          return;
        }
        const outputScale = typeof window === "undefined" ? 1 : window.devicePixelRatio || 1;
        const cssWidth = Math.ceil(viewport.width);
        const cssHeight = Math.ceil(viewport.height);
        canvas.width = Math.ceil(viewport.width * outputScale);
        canvas.height = Math.ceil(viewport.height * outputScale);
        canvas.style.width = `${cssWidth}px`;
        canvas.style.height = `${cssHeight}px`;
        setPdfPageBox({
          width: cssWidth,
          height: cssHeight,
          renderScale: outputScale,
          pdfScale: safeScale,
          baseWidth: Math.ceil(baseViewport.width),
          baseHeight: Math.ceil(baseViewport.height),
        });
        const transform = outputScale !== 1 ? ([outputScale, 0, 0, outputScale, 0, 0] as [number, number, number, number, number, number]) : undefined;
        const renderContext = {
          canvas,
          canvasContext: context,
          viewport,
          transform,
        };
        await page.render(renderContext).promise;
      } catch (error) {
        if (!cancelled) {
          setPdfError(error instanceof Error ? error.message : String(error));
        }
      } finally {
        if (!cancelled) {
          setPdfLoading(false);
        }
      }
    }
    void renderPdf();
    return () => {
      cancelled = true;
      loadingTask?.destroy?.();
    };
  }, [pdfFitMode, pdfPage, previewHeight, previewNonce, previewSize.height, previewSize.width, selectedArtifactUrl, selectedKey, selectedType, zoom]);

  function rememberPreviewScroll(element: HTMLDivElement | null) {
    if (!element || !selectedKey) {
      return;
    }
    lastPreviewScrollRef.current = {
      id: selectedKey,
      left: element.scrollLeft,
      top: element.scrollTop,
    };
  }

  function restorePreviewScrollForSelection() {
    const element = previewScrollRef.current;
    const saved = lastPreviewScrollRef.current;
    if (!element || !selectedKey || saved.id !== selectedKey) {
      return;
    }
    window.requestAnimationFrame(() => {
      element.scrollTo({ left: saved.left, top: saved.top });
    });
  }

  function startHeightDrag(event: React.PointerEvent<HTMLDivElement>) {
    const startY = event.clientY;
    const startHeight = previewHeight;
    event.currentTarget.setPointerCapture(event.pointerId);
    const onMove = (moveEvent: PointerEvent) => {
      setPreviewHeight(Math.min(1500, Math.max(620, startHeight + moveEvent.clientY - startY)));
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  function handleCreateAnnotation(annotation: Omit<ReportAnnotation, "annotation_id" | "created_at" | "updated_at">) {
    const rect = previewScrollRef.current?.getBoundingClientRect();
    const canvasRect = canvasRef.current?.getBoundingClientRect();
    const pdfPageWidth = pdfPageBox.width || canvasRect?.width || 0;
    const pdfPageHeight = pdfPageBox.height || canvasRect?.height || 0;
    const documentWidth = selected?.type === "html" ? rect?.width || 0 : pdfPageWidth;
    const documentHeight = selected?.type === "html" ? htmlPreviewHeight : pdfPageHeight;
    onCreateAnnotation({
      ...annotation,
      artifact_id: selected?.id || "",
      artifact_name: selected?.name || selected?.url || "",
      artifact_source: selected?.source || "",
      coordinate_version: selected?.type === "pdf" ? 3 : 2,
      coordinate_space: selected?.type === "pdf" ? "pdf_page_normalized_v3" : "html_document",
      scroll_offset: selected?.type === "html" ? previewScrollRef.current?.scrollTop || 0 : 0,
      viewport_width: selected?.type === "pdf" ? pdfPageWidth : rect?.width || 0,
      viewport_height: selected?.type === "pdf" ? pdfPageHeight : rect?.height || 0,
      document_width: documentWidth,
      document_height: documentHeight,
      page_width: selected?.type === "pdf" ? pdfPageWidth : undefined,
      page_height: selected?.type === "pdf" ? pdfPageHeight : undefined,
      render_scale: selected?.type === "pdf" ? pdfPageBox.pdfScale : undefined,
      preview_zoom: selected?.type === "pdf" ? pdfPageBox.pdfScale : zoom,
    });
    setSidePanel("annotations");
  }

  function sendVisibleAnnotationsToCodex() {
    if (!selected || !selectedAnnotations.length) {
      return;
    }
    const scope = selected.type === "pdf" ? `PDF 第 ${pdfPage} 页` : "HTML 当前报告";
    const lines = selectedAnnotations.map((annotation, index) => {
      const label = annotation.shape === "highlight" ? "高亮" : annotation.shape === "pen" ? "画笔" : "矩形框";
      const note = annotation.note?.trim() || "未填写说明，请结合标注位置判断需要修改的地方。";
      const location = selected.type === "pdf" ? `第 ${annotation.page_number || pdfPage} 页` : `scroll=${Math.round(annotation.scroll_offset || 0)}`;
      const coordinateSpace = annotationCoordinateSpace(annotation, selected);
      const size =
        selected.type === "pdf"
          ? `页面尺寸 ${Math.round(annotation.page_width || annotation.document_width || pdfPageBox.width || 0)}×${Math.round(
              annotation.page_height || annotation.document_height || pdfPageBox.height || 0,
            )}；PDF 缩放 ${Math.round(Number(annotation.preview_zoom || pdfPageBox.pdfScale || zoom) * 100)}%`
          : `文档高度 ${Math.round(annotation.document_height || htmlPreviewHeight || 0)}；滚动 ${Math.round(annotation.scroll_offset || 0)}`;
      return `${index + 1}. ${label}: ${note}；${location}；坐标空间 ${coordinateSpace}；${size}；normalized_points=${JSON.stringify(annotation.points || [])}`;
    });
    onUseAnnotationsAsGuidance([
      `请按我在${scope}上的批注修改报告。`,
      "要求：不要改 deterministic 数字，不要发明新指标；只调整文字、结构、图注、标题或排版。",
      `当前预览文件：${selected.name}`,
      "批注清单：",
      ...lines,
    ].join("\n"));
  }

  const annotationEnabled = Boolean(selected) && tool !== "select";
  const lockPdfAnnotationScroll = annotationEnabled && selected?.type === "pdf";
  const sidePanelTabs = [
    { key: "artifacts" as const, label: "生成结果", Icon: FileCode2 },
    { key: "diff" as const, label: "文件变更", Icon: GitCompare },
    { key: "annotations" as const, label: "批注", Icon: MessageSquareText },
    { key: "published" as const, label: "发布版本", Icon: CheckCircle2 },
  ];
  const annotationTools = [
    { key: "select" as const, label: "浏览", Icon: MousePointer2 },
    { key: "pen" as const, label: "画笔", Icon: Brush },
    { key: "rectangle" as const, label: "矩形", Icon: RectangleHorizontal },
    { key: "highlight" as const, label: "高亮", Icon: Highlighter },
    { key: "eraser" as const, label: "橡皮", Icon: Eraser },
  ];

  return (
    <section className="soft-panel revision-preview-panel flex h-full min-h-0 flex-col overflow-hidden p-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">实时预览</p>
          <h3 className="mt-1 truncate text-lg font-semibold text-[var(--text-strong)]">
            {detail?.content_title || detail?.title || "报告预览"}
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="surface-chip inline-flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!canPublish}
            onClick={onPublish}
          >
            {isPublishing ? <LoaderCircle size={15} className="animate-spin" /> : <Play size={15} />}
            生成修订版
          </button>
          {selectedArtifactUrl ? (
            <a className="surface-chip inline-flex items-center gap-2" href={selectedArtifactUrl} target="_blank" rel="noreferrer">
              <Maximize2 size={14} />
              新窗口打开
            </a>
          ) : null}
        </div>
      </div>

      <div className="mb-2 flex min-w-0 flex-wrap items-center gap-2">
        <select
          data-testid="revision-preview-select"
          className="field-input min-w-0 max-w-full flex-[1_1_220px] !py-2 text-sm"
          value={selected?.id || ""}
          onChange={(event) => {
            setSelectedId(event.target.value);
            setPdfPage(1);
            setPdfFitMode("fit-page");
          }}
        >
          {candidates.length ? (
            candidates.map((item) => (
              <option key={item.id} value={item.id}>
                {item.type.toUpperCase()} / {item.name}
              </option>
            ))
          ) : (
            <option value="">暂无可预览 HTML/PDF</option>
          )}
        </select>
        <button type="button" className="surface-chip inline-flex items-center gap-2" onClick={() => setPreviewNonce((value) => value + 1)}>
          <RefreshCw size={14} />
          刷新
        </button>
        {selected?.type === "pdf" ? (
          <>
            <button
              type="button"
              className={`surface-chip ${pdfFitMode === "fit-page" ? "is-selected" : ""}`}
              onClick={() => setPdfFitMode("fit-page")}
            >
              整页
            </button>
            <button
              type="button"
              className={`surface-chip ${pdfFitMode === "fit-width" ? "is-selected" : ""}`}
              onClick={() => setPdfFitMode("fit-width")}
            >
              适宽
            </button>
          </>
        ) : null}
        <button
          type="button"
          className="surface-chip inline-flex items-center gap-2"
          onClick={() => {
            setPdfFitMode("custom");
            setZoom((value) => Math.max(0.3, value - 0.1));
          }}
        >
          <ZoomOut size={14} />
        </button>
        <span className="surface-chip">{Math.round((selected?.type === "pdf" ? pdfPageBox.pdfScale || zoom : zoom) * 100)}%</span>
        <button
          type="button"
          className="surface-chip inline-flex items-center gap-2"
          onClick={() => {
            setPdfFitMode("custom");
            setZoom((value) => Math.min(3, value + 0.1));
          }}
        >
          <ZoomIn size={14} />
        </button>
      </div>

      <div className="mb-2 flex min-w-0 flex-wrap items-center gap-2 rounded-[18px] border border-white/10 bg-black/14 p-2 [scrollbar-width:thin]">
        {annotationTools.map(({ key, label, Icon }) => (
          <button
            key={key}
            type="button"
            className={`surface-chip inline-flex shrink-0 items-center gap-2 whitespace-nowrap !px-3 !py-1.5 ${tool === key ? "is-selected" : ""}`}
            onClick={() => setTool(key)}
          >
            <Icon size={13} />
            {label}
          </button>
        ))}
        <input className="shrink-0" aria-label="批注颜色" type="color" value={color} onChange={(event) => setColor(event.target.value)} />
        <input className="min-w-[96px] flex-1" aria-label="批注粗细" type="range" min={1} max={12} value={strokeWidth} onChange={(event) => setStrokeWidth(Number(event.target.value))} />
        <span className="min-w-[180px] flex-1 break-words text-xs leading-5 text-[var(--muted)]">
          PDF 批注按页坐标保存；选择批注工具时会锁定页面拖动，避免框选漂移。
        </span>
      </div>

      <div
        ref={previewScrollRef}
        data-testid="revision-preview-scroll"
        className={`relative min-h-0 flex-1 rounded-[22px] border border-white/10 bg-white ${
          lockPdfAnnotationScroll ? "overflow-hidden overscroll-none" : "overflow-auto"
        }`}
        style={{ flexBasis: previewHeight }}
        onScroll={(event) => rememberPreviewScroll(event.currentTarget)}
      >
        {selected?.type === "html" ? (
          <div className="relative" style={{ height: Math.max(previewHeight, htmlPreviewHeight * zoom) }}>
            <div className="relative" style={{ height: htmlPreviewHeight, transform: `scale(${zoom})`, transformOrigin: "top left", width: `${100 / zoom}%` }}>
              {htmlError ? (
                <div className="flex min-h-[420px] items-center justify-center bg-white px-8 text-center text-sm text-red-700">{htmlError}</div>
              ) : (
                <iframe
                  key={`${selectedKey}:${previewNonce}`}
                  title="报告 HTML 预览"
                  srcDoc={htmlSource || "<!doctype html><html><body style='font-family: sans-serif; padding: 32px;'>正在加载报告预览...</body></html>"}
                  sandbox=""
                  className="w-full border-0 bg-white"
                  scrolling="auto"
                  style={{ height: htmlPreviewHeight, pointerEvents: annotationEnabled ? "none" : "auto" }}
                  onLoad={() => restorePreviewScrollForSelection()}
                />
              )}
              {htmlLoading && !htmlError ? (
                <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-full bg-white/95 px-3 py-1.5 text-xs font-semibold text-neutral-700 shadow">
                  正在加载 HTML 预览...
                </div>
              ) : null}
              <AnnotationLayer
                annotations={layerAnnotations}
                artifactUrl={selectedArtifactUrl || ""}
                artifactType="html"
                enabled={annotationEnabled}
                tool={tool}
                color={color}
                strokeWidth={strokeWidth}
                onCreate={handleCreateAnnotation}
                onDelete={onDeleteAnnotation}
              />
            </div>
          </div>
        ) : selected?.type === "pdf" ? (
          <div className="flex min-h-full flex-col items-center bg-neutral-200 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-center gap-2 text-sm text-neutral-800">
              <button type="button" className="rounded-full border border-neutral-300 bg-white px-3 py-1" onClick={() => setPdfPage((value) => Math.max(1, value - 1))}>上一页</button>
              <span>
                第 {pdfPage} / {pdfPageCount} 页 · {pdfFitMode === "fit-page" ? "整页显示" : pdfFitMode === "fit-width" ? "适应宽度" : "自定义缩放"}
              </span>
              <button type="button" className="rounded-full border border-neutral-300 bg-white px-3 py-1" onClick={() => setPdfPage((value) => Math.min(pdfPageCount, value + 1))}>下一页</button>
            </div>
            <div
              className="relative inline-block shrink-0 bg-white shadow-2xl"
              style={pdfPageBox.width && pdfPageBox.height ? { width: pdfPageBox.width, height: pdfPageBox.height } : undefined}
            >
              <canvas ref={canvasRef} className="block" />
              <AnnotationLayer
                annotations={layerAnnotations}
                artifactUrl={selectedArtifactUrl || ""}
                artifactType="pdf"
                pageNumber={pdfPage}
                contentWidth={pdfPageBox.width || undefined}
                contentHeight={pdfPageBox.height || undefined}
                enabled={annotationEnabled}
                tool={tool}
                color={color}
                strokeWidth={strokeWidth}
                onCreate={handleCreateAnnotation}
                onDelete={onDeleteAnnotation}
              />
              {pdfLoading ? (
                <div className="pointer-events-none absolute left-4 top-4 rounded-full bg-white/95 px-3 py-1.5 text-xs font-semibold text-neutral-700 shadow">
                  正在加载 PDF 页面...
                </div>
              ) : null}
            </div>
            {pdfError ? <p className="mt-3 max-w-xl rounded-[12px] bg-red-50 px-3 py-2 text-sm text-red-700">{pdfError}</p> : null}
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-neutral-500">选择一份 HTML 或 PDF 后在这里预览。</div>
        )}
      </div>
      <div className="mt-2 h-2 cursor-row-resize rounded-full bg-white/8 transition hover:bg-[var(--accent-warm)]/60" role="separator" onPointerDown={startHeightDrag} />

      <div className="mt-3 shrink-0 rounded-[22px] border border-white/10 bg-black/14 p-3">
        <div className="flex flex-wrap gap-2">
          {sidePanelTabs.map(({ key, label, Icon }) => (
            <button
              key={key}
              type="button"
              className={`surface-chip inline-flex items-center gap-2 ${sidePanel === key ? "is-selected" : ""}`}
              onClick={() => setSidePanel(key)}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
          <span className="surface-chip">当前 {selectedAnnotations.length} 条 / 全部 {annotations.length} 条批注</span>
          {selectedAnnotations.length ? (
            <button type="button" className="surface-chip inline-flex items-center gap-2" onClick={sendVisibleAnnotationsToCodex}>
              <MessageSquareText size={14} />
              发送当前批注给 Codex
            </button>
          ) : null}
        </div>

        <div className="mt-3 max-h-[110px] overflow-auto pr-1">
          {sidePanel === "artifacts" ? (
            files.length ? (
              <div className="space-y-2">
                {files.map((file) => {
                  const artifactUrl = resolveArtifactUrl(file.url);
                  return (
                    <a
                      key={file.relative_path}
                      href={artifactUrl || undefined}
                      target={artifactUrl ? "_blank" : undefined}
                      rel="noreferrer"
                      aria-disabled={!artifactUrl}
                      className={`flex items-center justify-between gap-3 rounded-[14px] border border-white/10 bg-white/5 px-3 py-2 text-sm ${artifactUrl ? "hover:bg-white/8" : "cursor-not-allowed opacity-50"}`}
                    >
                      <span className="min-w-0">
                        <span className="block truncate font-semibold text-[var(--text-strong)]">{file.name}</span>
                        <span className="block truncate font-mono text-[11px] text-[var(--muted)]">{file.relative_path}</span>
                      </span>
                      <span className="surface-chip !px-2 !py-1">{file.type}</span>
                    </a>
                  );
                })}
              </div>
            ) : <p className="text-sm leading-7 text-[var(--muted)]">暂无会话产物。完成一轮修改后会显示 Markdown、HTML、PDF 和调试文件。</p>
          ) : null}

          {sidePanel === "diff" ? (
            diffFiles.length ? (
              <div className="space-y-2">
                {diffFiles.map((file) => (
                  <div key={`${file.kind}:${file.relative_path || file.working_path || file.source_path}`} className="rounded-[14px] border border-white/10 bg-white/5 px-3 py-2">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold text-[var(--text-strong)]">{file.kind}</span>
                      <span className="text-xs text-[var(--muted)]">+{file.additions} / -{file.deletions}</span>
                    </div>
                    {file.diff_preview ? <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap rounded-[10px] bg-black/25 p-2 text-[11px] leading-5 text-cyan-50">{file.diff_preview}</pre> : <p className="mt-2 text-xs text-[var(--muted)]">暂无文本差异。</p>}
                  </div>
                ))}
              </div>
            ) : <p className="text-sm leading-7 text-[var(--muted)]">暂无文件变更。完成一轮修改后这里会显示 diff 摘要。</p>
          ) : null}

          {sidePanel === "annotations" ? (
            !selected ? <p className="text-sm leading-7 text-[var(--muted)]">先在上方选择一份 HTML 或 PDF，再用画笔、矩形或高亮做批注。</p> : selectedAnnotations.length ? (
              <div className="space-y-2">
                {selectedAnnotations.map((annotation, index) => (
                  <div key={annotation.annotation_id} className="rounded-[14px] border border-white/10 bg-white/5 px-3 py-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 text-sm">
                        <p className="font-semibold text-[var(--text-strong)]">批注 {index + 1} / {annotation.shape === "highlight" ? "高亮" : annotation.shape === "pen" ? "画笔" : "矩形框"}</p>
                        <p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-[var(--muted)]">{annotation.note?.trim() || "未填写说明。"}</p>
                        <p className="mt-1 font-mono text-[11px] text-[var(--muted)]">{selected.type === "pdf" ? `page=${annotation.page_number || 1}` : `scroll=${Math.round(annotation.scroll_offset || 0)}`}</p>
                      </div>
                      <button type="button" className="surface-chip inline-flex items-center gap-2 !px-2 !py-1" onClick={() => onDeleteAnnotation(annotation.annotation_id)}>
                        <Trash2 size={13} />
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm leading-7 text-[var(--muted)]">选择画笔、矩形或高亮后，在右侧 HTML/PDF 上拖拽即可创建批注；保存时可以写一句修改意见。</p>
          ) : null}

          {sidePanel === "published" ? (
            session?.published_versions?.length ? (
              <div className="space-y-2">
                {session.published_versions.map((version, index) => {
                  const record = version as { version?: number; published_at?: string; artifacts?: Array<{ name?: string; path?: string; type?: string }> };
                  return (
                    <div key={`${record.version || index}`} className="rounded-[14px] border border-white/10 bg-white/5 px-3 py-2">
                      <div className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-semibold text-[var(--text-strong)]">v{record.version || index + 1}</span>
                        <span className="text-xs text-[var(--muted)]">{formatTime(record.published_at)}</span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {(record.artifacts || []).map((artifact) => {
                          const artifactUrl = resolveArtifactUrl(artifact.path);
                          return (
                            <a
                              key={`${artifact.name}:${artifact.path}`}
                              className={`surface-chip !px-2 !py-1 ${artifactUrl ? "" : "cursor-not-allowed opacity-50"}`}
                              href={artifactUrl || undefined}
                              target={artifactUrl ? "_blank" : undefined}
                              rel="noreferrer"
                              aria-disabled={!artifactUrl}
                            >
                              {artifact.type || "file"}
                            </a>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : <p className="text-sm leading-7 text-[var(--muted)]">还没有发布修订版。点击“生成修订版”后会出现在这里。</p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
