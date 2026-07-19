"use client";

type Props = {
  status?: string;
  size?: "sm" | "md";
  title?: string;
};

function tone(status: string) {
  if (["failed", "error", "timed_out", "blocked"].includes(status)) {
    return "border-red-200 border-r-transparent shadow-[0_0_14px_rgba(248,113,113,0.18)]";
  }
  if (status.startsWith("stale_")) {
    return "border-zinc-300 border-l-transparent shadow-[0_0_14px_rgba(244,244,245,0.12)]";
  }
  if (["completed", "available", "active"].includes(status)) {
    return "border-emerald-200 shadow-[0_0_12px_rgba(134,239,172,0.14)]";
  }
  if (["queued", "starting"].includes(status)) {
    return "border-zinc-200 border-t-transparent shadow-[0_0_14px_rgba(244,244,245,0.14)]";
  }
  if (["running", "cancelling", "verifying", "auto_repairing"].includes(status)) {
    return "border-zinc-100 border-b-transparent shadow-[0_0_16px_rgba(244,244,245,0.16)]";
  }
  return "border-white/30";
}

function shouldSpin(status: string) {
  return ["running", "cancelling", "verifying", "auto_repairing"].includes(status);
}

function shouldPulse(status: string) {
  return ["queued", "starting"].includes(status);
}

export function RuntimeActivityRing({ status, size = "md", title }: Props) {
  const safeStatus = String(status || "idle");
  const boxSize = size === "sm" ? "h-4 w-4" : "h-5 w-5";
  const dotSize = size === "sm" ? "h-1.5 w-1.5" : "h-2 w-2";
  return (
    <span
      className={`relative inline-flex shrink-0 items-center justify-center ${boxSize}`}
      title={title || safeStatus}
      aria-label={title || safeStatus}
    >
      <span
        className={`${boxSize} rounded-full border-2 ${tone(safeStatus)} ${
          shouldSpin(safeStatus) ? "motion-safe:animate-spin" : ""
        }`}
      />
      <span
        className={`absolute rounded-full bg-current text-zinc-100 ${dotSize} ${
          shouldPulse(safeStatus) ? "motion-safe:animate-pulse" : ""
        } ${safeStatus === "completed" || safeStatus === "available" || safeStatus === "active" ? "text-emerald-200" : ""} ${
          ["failed", "error", "timed_out", "blocked"].includes(safeStatus) ? "text-red-200" : ""
        }`}
      />
    </span>
  );
}
