function normalizeBaseUrl(value: string | undefined | null) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function inferRuntimeApiBaseUrl() {
  const sameOriginApi = String(process.env.NEXT_PUBLIC_API_SAME_ORIGIN || "").trim().toLowerCase();
  if ((sameOriginApi === "1" || sameOriginApi === "true") && typeof window !== "undefined") {
    return window.location.origin;
  }
  const configured = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);
  if (configured) {
    return configured;
  }
  if (typeof window !== "undefined") {
    const { origin, hostname, port, protocol } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      if (port === "8000") {
        return origin;
      }
      return `${protocol}//${hostname}:8000`;
    }
  }
  return "";
}

export const API_BASE_URL = inferRuntimeApiBaseUrl();

export function apiUrl(path: string) {
  const rawPath = String(path || "").trim();
  if (/^[a-z][a-z\d+.-]*:/i.test(rawPath) || rawPath.startsWith("//")) {
    throw new Error("API paths must be relative.");
  }
  const base = inferRuntimeApiBaseUrl();
  if (rawPath.startsWith("/api/")) {
    return base ? `${base}${rawPath}` : rawPath;
  }
  const normalizedPath = rawPath.startsWith("/") ? rawPath : `/${rawPath}`;
  return base ? `${base}${normalizedPath}` : normalizedPath;
}

export function resolveArtifactUrl(value: string | undefined | null): string | null {
  const rawValue = String(value || "").trim();
  if (!rawValue) {
    return null;
  }

  const configuredBase = inferRuntimeApiBaseUrl();
  const browserOrigin = typeof window !== "undefined" ? window.location.origin : "";
  const backendBase = configuredBase || browserOrigin;
  if (!backendBase) {
    return rawValue.startsWith("/api/") ? rawValue : null;
  }

  try {
    const backend = new URL(backendBase);
    const artifact = new URL(rawValue, backend.origin);
    const isTrustedArtifactPath = artifact.pathname.startsWith("/api/") || artifact.pathname.startsWith("/storage/");
    if (artifact.origin !== backend.origin || !isTrustedArtifactPath) {
      return null;
    }
    return artifact.href;
  } catch {
    return null;
  }
}

function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (typeof detail === "number" || typeof detail === "boolean") {
    return String(detail);
  }
  if (detail && typeof detail === "object") {
    const payload = detail as { message?: unknown; detail?: unknown };
    const nestedMessage = formatErrorDetail(payload.message);
    if (nestedMessage) {
      return nestedMessage;
    }
    const nestedDetail = formatErrorDetail(payload.detail);
    if (nestedDetail) {
      return nestedDetail;
    }
    try {
      return JSON.stringify(detail);
    } catch {
      return String(detail);
    }
  }
  return "";
}

type ApiRequestInit = RequestInit & { timeoutMs?: number };

export class ApiAbortError extends Error {
  constructor(message = "请求已取消。") {
    super(message);
    this.name = "ApiAbortError";
  }
}

export class ApiTimeoutError extends Error {
  constructor(message = "请求超时，请稍后刷新重试。") {
    super(message);
    this.name = "ApiTimeoutError";
  }
}

export function isApiAbortError(error: unknown): error is ApiAbortError {
  return error instanceof ApiAbortError;
}

export async function apiRequest<T>(
  path: string,
  init?: ApiRequestInit,
): Promise<T> {
  const { timeoutMs, ...requestInit } = (init || {}) as RequestInit & { timeoutMs?: number };
  const controller = new AbortController();
  const externalSignal = requestInit.signal;
  let didTimeout = false;
  const abortRequest = () => controller.abort();
  if (externalSignal?.aborted) {
    controller.abort();
  } else {
    externalSignal?.addEventListener("abort", abortRequest, { once: true });
  }
  const timeout =
    timeoutMs && timeoutMs > 0
      ? setTimeout(() => {
          didTimeout = true;
          controller.abort();
        }, timeoutMs)
      : null;

  try {
    const shouldSetJsonContentType =
      requestInit?.body != null &&
      !(requestInit.body instanceof FormData) &&
      !(requestInit.headers && new Headers(requestInit.headers).has("Content-Type"));
    const response = await fetch(apiUrl(path), {
      ...requestInit,
      headers: {
        ...(shouldSetJsonContentType ? { "Content-Type": "application/json" } : {}),
        ...(requestInit?.headers ?? {}),
      },
      cache: "no-store",
      signal: controller.signal,
    });

    const rawText = await response.text();
    let parsedJson: unknown = null;
    if (rawText) {
      try {
        parsedJson = JSON.parse(rawText);
      } catch {
        parsedJson = null;
      }
    }

    if (!response.ok) {
      let detail = response.statusText;
      if (parsedJson && typeof parsedJson === "object") {
        const payload = parsedJson as { detail?: unknown; message?: unknown };
        detail = formatErrorDetail(payload.detail ?? payload.message) || detail;
      } else if (rawText) {
        detail = rawText;
      }
      throw new Error(detail || "Request failed");
    }

    if (!rawText) {
      return null as T;
    }

    if (parsedJson !== null) {
      return parsedJson as T;
    }

    try {
      return JSON.parse(rawText) as T;
    } catch {
      return rawText as T;
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      if (didTimeout) {
        throw new ApiTimeoutError();
      }
      throw new ApiAbortError();
    }
    throw error;
  } finally {
    externalSignal?.removeEventListener("abort", abortRequest);
    if (timeout !== null) {
      clearTimeout(timeout);
    }
  }
}
