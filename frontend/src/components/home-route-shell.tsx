"use client";

import { BrainCircuit, ShieldCheck, Sparkles } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import type { ReactNode } from "react";

const RuntimeSettingsPanel = dynamic(
  () => import("@/components/runtime-settings-panel").then((module) => module.RuntimeSettingsPanel),
  {
    ssr: false,
    loading: () => <LoadingPanel label="正在加载运行设置..." />,
  },
);

const SmartReportStudio = dynamic(
  () => import("@/components/smart-report-studio").then((module) => module.SmartReportStudio),
  {
    ssr: false,
    loading: () => <LoadingPanel label="正在加载分析入口..." />,
  },
);

const AnalysisWorkspaceLink = dynamic(
  async () => {
    const Link = (await import("next/link")).default;
    return function AnalysisWorkspaceLink() {
      return (
        <Link className="surface-chip relative z-10 inline-flex cursor-pointer items-center gap-2" href="/lab">
          <BrainCircuit size={15} />
          Lab 方法实验台
        </Link>
      );
    };
  },
  { ssr: false, loading: () => null },
);

export function HomeRouteShell() {
  return <HomePageBody />;
}

export function HomePageBody() {
  return (
    <main className="page-shell min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="hero-shell">
          <div className="hero-copy">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/6 px-4 py-2 text-xs uppercase tracking-[0.28em] text-[var(--muted)]">
              <Sparkles size={14} />
              Asteria 智能分析
            </div>

            <div className="space-y-4">
              <h1 className="display-title max-w-5xl text-5xl leading-[0.92] tracking-[-0.06em] md:text-7xl">
                放数据，
                <br />
                直接进入分析与交付。
              </h1>
              <p className="max-w-3xl text-base leading-8 text-[var(--muted)] md:text-lg">
                当前首页提供上传数据、填写需求、生成报告和查看结果四个入口。
                页面围绕这些操作组织，便于直接开始分析工作。
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link className="surface-chip relative z-10 inline-flex cursor-pointer items-center gap-2" href="/analysis">
                <BrainCircuit size={14} />
                正式分析
              </Link>
              <SurfaceChip icon={<ShieldCheck size={14} />} text="先配置再生成" />
              <AnalysisWorkspaceLink />
            </div>
          </div>

          <aside className="signal-board">
            <div className="signal-orb signal-orb-left" />
            <div className="signal-orb signal-orb-right" />
            <div className="signal-panel">
              <p className="text-xs uppercase tracking-[0.26em] text-[var(--muted)]">当前焦点</p>
              <h2 className="mt-2 text-2xl font-semibold text-[var(--text-strong)]">
                一个更像工作台的首页
              </h2>
              <div className="mt-5 space-y-3">
                <div className="signal-strip">
                  <span className="pulse-dot" />
                  先上传或选择数据集
                </div>
                <div className="signal-strip">
                  <span className="pulse-dot" />
                  再填写需求与背景
                </div>
                <div className="signal-strip">
                  <span className="pulse-dot" />
                  最后直接生成报告
                </div>
              </div>
            </div>
          </aside>
        </section>

        <SmartReportStudio />

        <RuntimeSettingsPanel />
      </div>
    </main>
  );
}

function SurfaceChip({ icon, text }: { icon: ReactNode; text: string }) {
  return (
    <span className="surface-chip">
      {icon}
      {text}
    </span>
  );
}

function LoadingPanel({ label }: { label: string }) {
  return <div className="glass-panel rounded-[1.6rem] p-5 text-sm text-[var(--muted)]">{label}</div>;
}
