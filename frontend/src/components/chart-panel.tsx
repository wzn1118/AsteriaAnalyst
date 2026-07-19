"use client";

import dynamic from "next/dynamic";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function ChartPanel({
  option,
  title,
  caption,
  height = 320,
}: {
  option: object | null;
  title: string;
  caption?: string;
  height?: number;
}) {
  return (
    <section className="glass-panel flex h-full flex-col gap-4 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">
            Live chart
          </p>
          <h3 className="mt-2 text-lg font-semibold text-white">{title}</h3>
        </div>
        {caption ? (
          <span className="rounded-full border border-white/12 bg-white/6 px-3 py-1 text-xs text-[var(--muted)]">
            {caption}
          </span>
        ) : null}
      </div>

      {option ? (
        <ReactECharts
          option={option}
          style={{ height, width: "100%" }}
          notMerge
          lazyUpdate
        />
      ) : (
        <div className="flex h-full min-h-[220px] items-center justify-center rounded-[24px] border border-dashed border-white/12 bg-black/10 text-sm text-[var(--muted)]">
          Upload a dataset to unlock this chart.
        </div>
      )}
    </section>
  );
}
