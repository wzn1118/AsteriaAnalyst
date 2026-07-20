"use client";

import { useEffect, useRef, useState } from "react";

export type MethodGuideTopic = "object" | "fields" | "runs" | "features";

type MethodGuideAccent = "cool" | "warm";

type MethodGuideSpec = {
  accent?: MethodGuideAccent;
  artifact: string;
  checkpoint: string;
  demo: Array<{
    label: string;
    value: string;
  }>;
  example: string;
  summary: string;
  steps: string[];
  title: string;
  why: string;
};

const METHOD_GUIDE_ORDER: MethodGuideTopic[] = ["object", "fields", "runs", "features"];

const TOPIC_LABELS: Record<MethodGuideTopic, string> = {
  object: "锁定对象",
  fields: "绑定字段",
  runs: "追加跑法",
  features: "解释输入",
};

const CONSTELLATION_POSITIONS = [
  "left-1/2 top-2 -translate-x-1/2",
  "right-2 top-1/2 -translate-y-1/2",
  "bottom-2 left-1/2 -translate-x-1/2",
  "left-2 top-1/2 -translate-y-1/2",
];

const GUIDE_METRICS = [
  { label: "章节", value: "4", detail: "对象、字段、实例、解释输入" },
  { label: "动作", value: "12", detail: "每章 3 步照着做" },
  { label: "样例", value: "4", detail: "每章一套可复制配置" },
];

const GUIDE_OUTCOMES = [
  {
    label: "配置闭环",
    title: "方法知道该看谁、看什么、怎么解释",
    detail: "对象筛选、字段绑定、实例口径和解释输入共同形成完整配置闭环。",
  },
  {
    label: "样例可复制",
    title: "每章都有一套能直接照填的业务样例",
    detail: "新手可先跑通 A 基金会/B 基金会样例，再替换成自己的数据。",
  },
  {
    label: "证据能交付",
    title: "最终产物可以进入报告、图表和附录",
    detail: "教程将第一次配置沉淀为可复用、可审计、可解释的分析证据。",
  },
];

export const METHOD_GUIDES: Record<MethodGuideTopic, MethodGuideSpec> = {
  object: {
    accent: "cool",
    title: "重点对象筛选",
    summary: "先锁定“分析谁”，再分析它的指标和结构。",
    why: "对象指某一列里的具体值。对象级方法先明确关注的一个或一组对象，再按该范围生成统计。",
    steps: [
      "选对象所在列：例如基金会名称、客户名称、门店名称、SKU。",
      "选要分析的对象值：可以点样本值，也可以手动输入多个名称。",
      "选分组口径：例如服务领域、地区、年度，用来比较对象内部结构。",
    ],
    example: "对象列选“基金会名称”，对象值填“某某基金会”，分析指标选“项目收入”，系统就只筛这家基金会的记录，再按服务领域或年度做画像。",
    artifact: "得到聚焦目标对象的分析实例，后续图表和报告围绕该对象展开。",
    checkpoint: "能说清楚“我正在分析谁”，并且对象列、对象值、分组口径三项都已填好。",
    demo: [
      { label: "对象列", value: "基金会名称" },
      { label: "对象值", value: "A 基金会、B 基金会" },
      { label: "分组口径", value: "服务领域 / 年度" },
    ],
  },
  fields: {
    accent: "warm",
    title: "字段角色绑定",
    summary: "通过字段角色绑定明确每一列的业务用途。",
    why: "同一个字段在不同方法里可以扮演不同角色。绑定清楚后，后端统计引擎、图表和报告解释才会使用同一套业务口径。",
    steps: [
      "先看问题要解释什么：收入、支出、得分、数量通常放到结果指标。",
      "再选影响或辅助解释结果的列：支出、年度、规模、比例通常放到解释字段。",
      "如果要比较类别，就补充分组口径；如果要点名对象，就补充名称列。",
    ],
    example: "做基金会画像时，结果指标选“项目收入”，解释字段可选“项目支出、年度”，分组口径选“服务领域”，对象名称列选“基金会名称”。",
    artifact: "得到一组可执行字段绑定，让方法知道结果、解释、分组和对象分别来自哪一列。",
    checkpoint: "结果指标已填写；解释字段具备业务含义；分组字段和对象字段分工清晰。",
    demo: [
      { label: "结果指标", value: "项目收入" },
      { label: "解释字段", value: "项目支出、年度" },
      { label: "分组字段", value: "服务领域" },
    ],
  },
  runs: {
    accent: "cool",
    title: "运行实例",
    summary: "同一个方法可以保存多种独立跑法。",
    why: "更换对象或字段时可追加实例。每个实例保留自己的字段绑定和对象筛选，报告生成时作为独立证据进入合并。",
    steps: [
      "字段绑定口径：只按当前字段角色运行，适合普通统计或图表。",
      "全数据口径：不锁定某个对象，适合总体概览、数据审计、附录证据。",
      "重点对象口径：先筛某个对象值，再分析它自己的表现和结构。",
    ],
    example: "同一个“画像文字解读”方法，可以跑一次“基金会名称 = A 基金会”，再跑一次“基金会名称 = B 基金会”，最后比较两家的服务领域和收入结构。",
    artifact: "得到多个独立执行实例，报告可以将它们作为独立证据一起引用。",
    checkpoint: "每个实例都有独立名称、字段绑定和筛选条件，切换时各实例配置保持独立。",
    demo: [
      { label: "实例 01", value: "全数据总体画像" },
      { label: "实例 02", value: "A 基金会重点对象" },
      { label: "实例 03", value: "B 基金会对比对象" },
    ],
  },
  features: {
    accent: "warm",
    title: "解释/建模输入字段",
    summary: "这些字段用于解释结果，可作为特征、解释变量或辅助证据。",
    why: "建模、关联、对比类方法需要一些辅助字段来解释结果指标。这里选择的字段会作为特征、解释变量或辅助证据进入方法执行。",
    steps: [
      "优先选和结果有关的业务字段，例如支出、年度、规模、比例。",
      "将纯 ID、统一信用代码和长文本简介保留为标识或说明字段，另选业务变量作为建模输入。",
      "如果系统已生成标准化、百分位、占比等派生指标，可按业务口径补充选择。",
    ],
    example: "结果指标是“项目收入”时，解释字段可以选“项目支出、年度、服务领域”，派生指标可以选“标准化_项目收入、百分位_项目收入”。",
    artifact: "得到一组可解释输入，模型和报告都会围绕这些字段解释“为什么是这个结果”。",
    checkpoint: "解释字段能帮助回答业务问题，派生指标有清晰口径，长文本和纯编号没有误选。",
    demo: [
      { label: "业务输入", value: "项目支出、年度、服务领域" },
      { label: "派生指标", value: "标准化_项目收入" },
      { label: "避开字段", value: "统一信用代码、长简介" },
    ],
  },
};

function accentClasses(accent: MethodGuideAccent = "cool") {
  if (accent === "warm") {
    return {
      active: "border-[#f7c873]/70 bg-[#f7c873]/14 shadow-[0_20px_54px_rgba(247,200,115,0.16)]",
      badge: "border-[#f7c873]/45 bg-[#f7c873]/14 text-[#ffe6ae]",
      glow: "from-[#f7c873]/36 via-[#ff9c61]/22 to-transparent",
      line: "from-[#f7c873] via-[#ff9c61] to-[#74d0d9]",
      panel: "border-[#f7c873]/26 bg-[linear-gradient(135deg,rgba(247,200,115,0.14),rgba(7,17,19,0.76)_42%,rgba(255,156,97,0.09))]",
      text: "text-[#ffe6ae]",
    };
  }

  return {
    active: "border-[#74d0d9]/70 bg-[#74d0d9]/14 shadow-[0_20px_54px_rgba(116,208,217,0.15)]",
    badge: "border-[#74d0d9]/45 bg-[#74d0d9]/14 text-[#c8fbff]",
    glow: "from-[#74d0d9]/34 via-[#9ec69f]/20 to-transparent",
    line: "from-[#74d0d9] via-[#9ec69f] to-[#f7c873]",
    panel: "border-[#74d0d9]/28 bg-[linear-gradient(135deg,rgba(116,208,217,0.15),rgba(7,17,19,0.78)_42%,rgba(158,198,159,0.09))]",
    text: "text-[#c8fbff]",
  };
}

function MethodGuideCard({
  accent = "cool",
  artifact,
  checkpoint,
  demo,
  example,
  steps,
  summary,
  title,
  why,
}: MethodGuideSpec) {
  const visual = accentClasses(accent);

  return (
    <article className={`guide-glass guide-reveal relative overflow-hidden rounded-[32px] border p-4 md:p-5 ${visual.panel}`}>
      <div className={`guide-beam bg-gradient-to-r ${visual.glow}`} />
      <div className="relative grid gap-5 xl:grid-cols-[1.08fr_0.92fr]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.22em] ${visual.badge}`}>
              新手教程任务卡
            </span>
            <span className="surface-chip py-1.5 text-[11px]">可复用使用引导</span>
          </div>
          <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-[-0.05em] text-[var(--text-strong)] md:text-5xl">
            {title}
          </h2>
          <p className={`mt-3 text-base font-medium leading-7 ${visual.text}`}>{summary}</p>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--muted)]">{why}</p>

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            <div className="rounded-[22px] border border-white/10 bg-black/22 p-4">
              <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--muted)]">最终交付</p>
              <p className="mt-2 text-sm leading-6 text-[var(--text-strong)]">{artifact}</p>
            </div>
            <div className="rounded-[22px] border border-white/10 bg-white/6 p-4">
              <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--muted)]">最终检查</p>
              <p className="mt-2 text-sm leading-6 text-[var(--text-strong)]">{checkpoint}</p>
            </div>
          </div>
        </div>

        <aside className="guide-radar relative min-h-[360px] overflow-hidden rounded-[28px] border border-white/12 bg-black/28 p-4">
          <div className="guide-scanline" />
          <div className="relative z-10 flex h-full flex-col justify-between gap-5">
            <div>
              <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--muted)]">样例剧场</p>
              <h3 className="mt-2 text-xl font-semibold text-[var(--text-strong)]">照着填一次，就能跑起来</h3>
            </div>
            <div className="space-y-2">
              {demo.map((item, index) => (
                <div
                  className="rounded-[18px] border border-white/10 bg-white/7 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                  key={`${item.label}-${item.value}`}
                  style={{ animationDelay: `${index * 90}ms` }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{item.label}</span>
                    <span className={`rounded-full bg-white/8 px-2 py-0.5 text-[10px] ${visual.text}`}>Demo {index + 1}</span>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-[var(--text-strong)]">{item.value}</p>
                </div>
              ))}
            </div>
            <p className="rounded-[20px] border border-white/10 bg-black/24 p-4 text-sm leading-7 text-[var(--muted)]">
              <span className={`font-semibold ${visual.text}`}>样例：</span>
              {example}
            </p>
          </div>
        </aside>
      </div>

      <div className="relative mt-5 grid gap-3 lg:grid-cols-3">
        {steps.map((step, index) => (
          <div className="guide-step-card rounded-[22px] border border-white/10 bg-black/18 p-4" key={`${title}-${step}`}>
            <div className={`h-1 rounded-full bg-gradient-to-r ${visual.line}`} />
            <div className="mt-4 flex items-start gap-3">
              <span className="inline-flex h-9 w-9 flex-none items-center justify-center rounded-full border border-white/12 bg-white/8 text-sm font-semibold text-[var(--text-strong)]">
                {index + 1}
              </span>
              <p className="text-sm leading-7 text-[var(--text-strong)]">{step}</p>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function GuideConstellation({
  onTopicChange,
  topic,
}: {
  onTopicChange: (topic: MethodGuideTopic) => void;
  topic: MethodGuideTopic;
}) {
  const activeGuide = METHOD_GUIDES[topic];
  const activeIndex = METHOD_GUIDE_ORDER.indexOf(topic);
  const visual = accentClasses(activeGuide.accent);

  return (
    <aside className="guide-command-deck guide-glass relative min-h-[430px] overflow-hidden rounded-[34px] border border-white/10 bg-black/24 p-5">
      <div className="guide-comet" />
      <div className="relative z-10 flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--muted)]">Star map onboarding</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">星图导航</h2>
        </div>
        <span className={`rounded-full border px-3 py-1 text-[11px] ${visual.badge}`}>Stage {activeIndex + 1}</span>
      </div>

      <div className="guide-constellation relative z-10 mx-auto mt-6 h-[260px] max-w-[360px]">
        <div className="guide-orbit guide-orbit-outer" />
        <div className="guide-orbit guide-orbit-inner" />
        <div className={`absolute left-1/2 top-1/2 z-10 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full border bg-gradient-to-br p-3 text-center shadow-[0_24px_70px_rgba(0,0,0,0.38)] ${visual.badge}`}>
          <div className="flex h-full flex-col items-center justify-center rounded-full border border-white/12 bg-black/24">
            <span className="text-[10px] uppercase tracking-[0.22em] opacity-80">Now</span>
            <span className="mt-1 text-sm font-semibold leading-5">{TOPIC_LABELS[topic]}</span>
          </div>
        </div>
        {METHOD_GUIDE_ORDER.map((guideTopic, index) => {
          const guide = METHOD_GUIDES[guideTopic];
          const active = guideTopic === topic;
          const topicVisual = accentClasses(guide.accent);

          return (
            <button
              aria-label={`切换到${guide.title}`}
              aria-pressed={active}
              className={`absolute z-20 w-24 rounded-[20px] border p-2.5 text-left text-xs transition duration-200 ${CONSTELLATION_POSITIONS[index]} ${
                active ? topicVisual.active : "border-white/10 bg-[#071113]/88 text-[var(--muted)] hover:border-white/24 hover:bg-white/10"
              }`}
              key={guideTopic}
              onClick={() => onTopicChange(guideTopic)}
              type="button"
            >
              <span className="block text-[10px] uppercase tracking-[0.18em] opacity-75">0{index + 1}</span>
              <span className="mt-1 block font-semibold text-[var(--text-strong)]">{TOPIC_LABELS[guideTopic]}</span>
            </button>
          );
        })}
      </div>

      <div className="relative z-10 mt-5 grid grid-cols-3 gap-2">
        {GUIDE_METRICS.map((item) => (
          <div className="guide-metric-tile rounded-[18px] border border-white/10 bg-white/6 p-3" key={item.label}>
            <p className="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">{item.label}</p>
            <p className="mt-1 text-2xl font-semibold text-[var(--text-strong)]">{item.value}</p>
            <p className="mt-1 text-[11px] leading-4 text-[var(--muted)]">{item.detail}</p>
          </div>
        ))}
      </div>
    </aside>
  );
}

function GuideLaunchStrip({
  onTopicChange,
  topic,
}: {
  onTopicChange: (topic: MethodGuideTopic) => void;
  topic: MethodGuideTopic;
}) {
  const activeGuide = METHOD_GUIDES[topic];
  const activeIndex = METHOD_GUIDE_ORDER.indexOf(topic);
  const visual = accentClasses(activeGuide.accent);

  return (
    <section className="guide-launch-strip guide-glass guide-reveal mt-5 overflow-hidden rounded-[30px] border border-white/10 bg-black/20 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--muted)]">Launch route</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-[-0.05em] text-[var(--text-strong)]">发射轨道：第一次配置就按这条线走</h2>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs ${visual.badge}`}>完成感 {Math.round(((activeIndex + 1) / METHOD_GUIDE_ORDER.length) * 100)}%</span>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-4">
        {METHOD_GUIDE_ORDER.map((guideTopic, index) => {
          const guide = METHOD_GUIDES[guideTopic];
          const active = guideTopic === topic;
          const complete = index < activeIndex;
          const topicVisual = accentClasses(guide.accent);

          return (
            <button
              aria-pressed={active}
              className={`guide-route-node rounded-[22px] border p-3 text-left transition ${
                active
                  ? topicVisual.active
                  : complete
                    ? "border-[#9ec69f]/35 bg-[#9ec69f]/10 text-[var(--text-strong)]"
                    : "border-white/10 bg-white/5 text-[var(--muted)] hover:border-white/22"
              }`}
              key={guideTopic}
              onClick={() => onTopicChange(guideTopic)}
              type="button"
            >
              <span className="flex items-center justify-between gap-3">
                <span className="text-[10px] uppercase tracking-[0.22em]">{complete ? "Done" : active ? "Now" : "Next"}</span>
                <span className="rounded-full border border-white/12 bg-black/20 px-2 py-0.5 text-[10px]">0{index + 1}</span>
              </span>
              <span className="mt-3 block text-sm font-semibold text-[var(--text-strong)]">{guide.title}</span>
              <span className="mt-1 block text-xs leading-5 opacity-85">{guide.artifact}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function GuideOutcomeWall() {
  return (
    <section className="guide-outcome-wall guide-glass guide-reveal mt-5 overflow-hidden rounded-[34px] border border-white/10 bg-black/22 p-5 md:p-6">
      <div className="relative z-10 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--muted)]">Final unlock</p>
          <h2 className="mt-2 max-w-3xl text-3xl font-semibold leading-tight tracking-[-0.06em] text-[var(--text-strong)] md:text-5xl">
            跑完这套教程，新手已经能交付可复用、可审计、可解释的分析证据。
          </h2>
        </div>
        <span className="rounded-full border border-[#9ec69f]/36 bg-[#9ec69f]/10 px-4 py-2 text-xs uppercase tracking-[0.2em] text-[#d9ffd8]">
          Ready to ship
        </span>
      </div>

      <div className="relative z-10 mt-5 grid gap-3 lg:grid-cols-3">
        {GUIDE_OUTCOMES.map((item, index) => (
          <article className="guide-outcome-card rounded-[26px] border border-white/10 bg-white/6 p-4" key={item.label}>
            <div className="flex items-center justify-between gap-3">
              <span className="rounded-full border border-white/12 bg-black/24 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">
                0{index + 1}
              </span>
              <span className="text-[10px] uppercase tracking-[0.22em] text-[#c8fbff]">{item.label}</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold leading-6 text-[var(--text-strong)]">{item.title}</h3>
            <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{item.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function MethodGuideCenter({
  onTopicChange,
  topic,
}: {
  onTopicChange: (topic: MethodGuideTopic) => void;
  topic: MethodGuideTopic;
}) {
  const activeGuide = METHOD_GUIDES[topic];
  const activeIndex = METHOD_GUIDE_ORDER.indexOf(topic);

  return (
    <div className="grid gap-5 xl:grid-cols-[310px_1fr]">
      <nav className="guide-glass guide-reveal rounded-[30px] border border-white/10 bg-black/20 p-4">
        <p className="text-[10px] uppercase tracking-[0.28em] text-[var(--muted)]">Mission map</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[var(--text-strong)]">四步完成第一次方法配置</h2>
        <p className="mt-2 text-xs leading-6 text-[var(--muted)]">
          这套教程可以独立打开，也可以从方法编辑器内按章节呼出。每章都保留“目标、步骤、样例、检查点”。
        </p>

        <div className="relative mt-5 space-y-3">
          <div className="absolute bottom-8 left-[17px] top-8 w-px bg-gradient-to-b from-[#74d0d9]/60 via-[#f7c873]/40 to-transparent" />
          {METHOD_GUIDE_ORDER.map((guideTopic, index) => {
            const guide = METHOD_GUIDES[guideTopic];
            const active = guideTopic === topic;
            const visual = accentClasses(guide.accent);
            return (
              <button
                aria-pressed={active}
                className={`guide-topic-card relative w-full rounded-[22px] border p-3 text-left transition duration-200 ${
                  active ? visual.active : "border-white/10 bg-white/5 text-[var(--muted)] hover:border-white/22 hover:bg-white/8"
                }`}
                key={guideTopic}
                onClick={() => onTopicChange(guideTopic)}
                type="button"
              >
                <div className="relative z-10 flex gap-3">
                  <span className={`inline-flex h-9 w-9 flex-none items-center justify-center rounded-full border text-sm font-semibold ${active ? visual.badge : "border-white/12 bg-black/20 text-[var(--text-strong)]"}`}>
                    {index + 1}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-xs uppercase tracking-[0.18em] opacity-75">{TOPIC_LABELS[guideTopic]}</span>
                    <span className="mt-1 block text-sm font-semibold text-[var(--text-strong)]">{guide.title}</span>
                    <span className="mt-1 block text-xs leading-5 opacity-85">{guide.summary}</span>
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-5 rounded-[22px] border border-[#9ec69f]/24 bg-[#9ec69f]/8 p-4">
          <p className="text-[10px] uppercase tracking-[0.24em] text-[#d9ffd8]">复用提示</p>
          <p className="mt-2 text-xs leading-6 text-[var(--muted)]">
            复用到别的方法页时，可沿用 summary、steps、example、checkpoint 四段数据结构，再替换每章 demo。
          </p>
          <p className="mt-3 text-xs text-[var(--text-strong)]">当前进度：{activeIndex + 1} / {METHOD_GUIDE_ORDER.length}</p>
        </div>
      </nav>

      <MethodGuideCard {...activeGuide} />
    </div>
  );
}

function MethodGuideExperience({
  compact = false,
  onClose,
  onTopicChange,
  titleId,
  topic,
}: {
  compact?: boolean;
  onClose?: () => void;
  onTopicChange: (topic: MethodGuideTopic) => void;
  titleId?: string;
  topic: MethodGuideTopic;
}) {
  const activeGuide = METHOD_GUIDES[topic];
  const activeIndex = METHOD_GUIDE_ORDER.indexOf(topic);

  return (
    <section className={`guide-stage relative overflow-hidden text-white ${compact ? "rounded-[34px]" : "min-h-dvh px-4 py-8 md:px-6"}`}>
      <div className="pointer-events-none absolute inset-0 opacity-80">
        <div className="absolute left-[5%] top-[8%] h-56 w-56 rounded-full bg-[#74d0d9]/16 blur-3xl" />
        <div className="absolute right-[8%] top-[12%] h-64 w-64 rounded-full bg-[#f7c873]/14 blur-3xl" />
        <div className="absolute bottom-[3%] left-[34%] h-72 w-72 rounded-full bg-[#9ec69f]/10 blur-3xl" />
      </div>

      <div className={`relative mx-auto w-full ${compact ? "max-w-7xl p-4 md:p-5" : "max-w-7xl"}`}>
        <header className="guide-glass guide-reveal relative overflow-hidden rounded-[34px] border border-white/10 bg-black/22 p-5 md:p-7">
          <div className="guide-beam bg-gradient-to-r from-[#74d0d9]/30 via-[#f7c873]/22 to-transparent" />
          <div className="relative grid gap-6 lg:grid-cols-[minmax(0,1.18fr)_360px] lg:items-end">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-[#74d0d9]/38 bg-[#74d0d9]/12 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-[#c8fbff]">
                  Reusable method guide
                </span>
                <span className="surface-chip py-1.5 text-[11px]">新手教程</span>
                <span className="surface-chip py-1.5 text-[11px]">含样例</span>
              </div>
              <h1
                className="mt-5 max-w-4xl text-4xl font-semibold leading-[0.95] tracking-[-0.07em] text-[var(--text-strong)] md:text-7xl"
                id={titleId}
              >
                方法编辑器新手教程
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-8 text-[var(--muted)]">
                这是一个可复用的教程控制台：从对象、字段、实例到解释输入，带你把第一次方法配置跑成可交付证据。
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                <span className="surface-chip">4 个章节</span>
                <span className="surface-chip">当前：{activeGuide.title}</span>
                <span className="surface-chip">进度 {activeIndex + 1} / {METHOD_GUIDE_ORDER.length}</span>
                {onClose ? (
                  <button className="surface-chip cursor-pointer border-[#f7c873]/35 bg-[#f7c873]/10 text-[#ffe6ae]" onClick={onClose} type="button">
                    关闭教程
                  </button>
                ) : null}
              </div>
            </div>

            <GuideConstellation onTopicChange={onTopicChange} topic={topic} />
          </div>
        </header>

        <GuideLaunchStrip onTopicChange={onTopicChange} topic={topic} />

        <div className="mt-5">
          <MethodGuideCenter onTopicChange={onTopicChange} topic={topic} />
        </div>

        <GuideOutcomeWall />
      </div>
    </section>
  );
}

export function MethodGuideStandalone({ initialTopic = "object" }: { initialTopic?: MethodGuideTopic }) {
  const [topic, setTopic] = useState<MethodGuideTopic>(initialTopic);

  return <MethodGuideExperience onTopicChange={setTopic} topic={topic} />;
}

export function MethodGuideModal({
  onClose,
  onTopicChange,
  topic,
}: {
  onClose: () => void;
  onTopicChange: (topic: MethodGuideTopic) => void;
  topic: MethodGuideTopic;
}) {
  const modalRef = useRef<HTMLDivElement>(null);
  const titleId = "method-guide-modal-title";

  useEffect(() => {
    modalRef.current?.focus();
  }, []);

  return (
    <div
      aria-labelledby={titleId}
      aria-modal="true"
      className="fixed inset-0 z-[1320] flex items-start justify-center overflow-y-auto bg-[#030605]/86 px-3 py-5 backdrop-blur-xl"
      onKeyDown={(event) => {
        if (event.key === "Escape") onClose();
      }}
      onClick={onClose}
      ref={modalRef}
      role="dialog"
      tabIndex={-1}
    >
      <div className="w-full max-w-7xl" onClick={(event) => event.stopPropagation()}>
        <MethodGuideExperience compact onClose={onClose} onTopicChange={onTopicChange} titleId={titleId} topic={topic} />
      </div>
    </div>
  );
}
