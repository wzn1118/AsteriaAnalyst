import { SmartReportStudioClient } from "./smart-report-studio-client";

export default function AnalysisPage() {
  return (
    <main className="page-shell min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="glass-panel rounded-[2rem] p-6">
          <p className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">Formal Analysis</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">
            正式分析与报告交付
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--muted)]">
            这里保留正式报告生成链路。需要试验 2k+ 统计与可视化方法时，进入独立的 Lab。
          </p>
          <a className="surface-chip mt-4" href="/lab">
            打开 Lab 方法实验台
          </a>
        </section>
        <SmartReportStudioClient />
      </div>
    </main>
  );
}
