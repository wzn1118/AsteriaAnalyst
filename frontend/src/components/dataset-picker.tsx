"use client";

import { ChevronDown, Search } from "lucide-react";
import { useMemo, useState } from "react";

const INITIAL_VISIBLE_DATASET_COUNT = 24;
const DATASET_LOAD_MORE_STEP = 24;

type DatasetLike = {
  dataset_id: string;
  name?: string;
  filename?: string;
  row_count?: number;
  column_count?: number;
};

function formatNumber(value: unknown) {
  if (typeof value !== "number") {
    return value == null ? "0" : String(value);
  }
  return new Intl.NumberFormat("zh-CN").format(value);
}

function datasetLabel(dataset?: DatasetLike) {
  if (!dataset) return "选择已上传数据集";
  return dataset.name || dataset.filename || dataset.dataset_id;
}

export function DatasetPicker<TDataset extends DatasetLike>({
  datasets,
  onChange,
  selectedDataset,
  value,
}: {
  datasets: TDataset[];
  onChange: (datasetId: string) => void;
  selectedDataset?: TDataset;
  value: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const normalizedQuery = query.trim().toLowerCase();
  const visibleLimitKey = `${open ? "open" : "closed"}:${normalizedQuery}:${datasets.length}`;
  const [visibleWindow, setVisibleWindow] = useState({
    key: visibleLimitKey,
    limit: INITIAL_VISIBLE_DATASET_COUNT,
  });
  const visibleLimit =
    visibleWindow.key === visibleLimitKey ? visibleWindow.limit : INITIAL_VISIBLE_DATASET_COUNT;
  const matchingDatasets = useMemo(() => {
    return normalizedQuery
      ? datasets.filter((dataset) =>
          [datasetLabel(dataset), dataset.dataset_id]
            .filter(Boolean)
            .some((item) => String(item).toLowerCase().includes(normalizedQuery)),
        )
      : datasets;
  }, [datasets, normalizedQuery]);
  const visibleDatasets = useMemo(() => {
    return matchingDatasets.slice(0, visibleLimit);
  }, [matchingDatasets, visibleLimit]);

  return (
    <div className="rounded-[20px] border border-white/10 bg-black/18 p-3">
      <button
        className="flex w-full items-center justify-between gap-3 text-left"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold text-[var(--text-strong)]">
            {datasetLabel(selectedDataset)}
          </span>
          <span className="mt-1 block text-xs text-[var(--muted)]">
            {selectedDataset
              ? `${formatNumber(selectedDataset.row_count)} rows / ${formatNumber(selectedDataset.column_count)} columns`
              : `${formatNumber(datasets.length)} saved datasets`}
          </span>
        </span>
        <ChevronDown className="shrink-0 text-[var(--muted)]" size={18} />
      </button>

      {open ? (
        <div className="mt-3 space-y-3">
          <div className="field-input flex items-center gap-2">
            <Search size={16} className="shrink-0 text-[var(--muted)]" />
            <input
              className="min-w-0 flex-1 border-0 bg-transparent p-0 text-sm outline-none"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索数据集名称或 ID"
              value={query}
            />
          </div>
          <div className="max-h-[280px] space-y-2 overflow-auto pr-1">
            {visibleDatasets.length ? (
              visibleDatasets.map((dataset) => {
                const active = dataset.dataset_id === value;
                return (
                  <button
                    className={`w-full rounded-[16px] border px-3 py-2 text-left transition ${
                      active
                        ? "border-[#74d0d9]/55 bg-[#74d0d9]/12 text-[var(--text-strong)]"
                        : "border-white/10 bg-white/5 text-[var(--muted)] hover:bg-white/10"
                    }`}
                    key={dataset.dataset_id}
                    onClick={() => {
                      onChange(dataset.dataset_id);
                      setOpen(false);
                    }}
                    type="button"
                  >
                    <span className="block truncate text-sm font-semibold">{datasetLabel(dataset)}</span>
                    <span className="mt-1 block text-xs opacity-80">
                      {formatNumber(dataset.row_count)} rows / {formatNumber(dataset.column_count)} columns
                    </span>
                  </button>
                );
              })
            ) : (
              <div className="rounded-[16px] border border-dashed border-white/10 px-3 py-6 text-sm text-[var(--muted)]">
                没有匹配的数据集。
              </div>
            )}
          </div>
          {matchingDatasets.length > visibleDatasets.length ? (
            <button
              className="w-full rounded-[16px] border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--text-strong)] transition hover:bg-white/10"
              onClick={() =>
                setVisibleWindow({
                  key: visibleLimitKey,
                  limit: Math.min(visibleLimit + DATASET_LOAD_MORE_STEP, matchingDatasets.length),
                })
              }
              type="button"
            >
              加载更多数据集
            </button>
          ) : null}
          {matchingDatasets.length > visibleDatasets.length || datasets.length > visibleDatasets.length ? (
            <p className="text-xs leading-5 text-[var(--muted)]">
              当前显示 {formatNumber(visibleDatasets.length)} / {formatNumber(matchingDatasets.length)}，继续输入可缩小范围。
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
