const fs = require("fs");
const Module = require("module");
const path = require("path");
const ts = require("typescript");

const root = path.resolve(__dirname, "..");
const guideFile = path.join(root, "src/components/method-guide-modal.tsx");
const outputFile = path.join(root, "public/method-guide-preview.html");

function compileCommonJs(file) {
  const source = fs.readFileSync(file, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      jsx: ts.JsxEmit.ReactJSX,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
    fileName: file,
    reportDiagnostics: true,
  });

  if (output.diagnostics?.length) {
    throw new Error(
      output.diagnostics
        .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n")}`)
        .join("\n"),
    );
  }

  const mod = new Module(file, module);
  mod.filename = `${file}.js`;
  mod.paths = Module._nodeModulePaths(root);
  mod._compile(output.outputText, mod.filename);
  return mod.exports;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const { METHOD_GUIDES } = compileCommonJs(guideFile);
const order = ["object", "fields", "runs", "features"];
const labels = {
  object: "锁定对象",
  fields: "绑定字段",
  runs: "追加跑法",
  features: "解释输入",
};

function renderGuide(topic, index) {
  const guide = METHOD_GUIDES[topic];
  const accent = guide.accent === "warm" ? "warm" : "cool";

  return `
    <article class="mission-card ${accent}" id="topic-${topic}">
      <div class="mission-copy">
        <p class="eyebrow">Stage 0${index + 1} / ${escapeHtml(labels[topic])}</p>
        <h2>${escapeHtml(guide.title)}</h2>
        <p class="summary">${escapeHtml(guide.summary)}</p>
        <p class="why">${escapeHtml(guide.why)}</p>
        <div class="result-grid">
          <div>
            <span>最终交付</span>
            <p>${escapeHtml(guide.artifact)}</p>
          </div>
          <div>
            <span>最终检查</span>
            <p>${escapeHtml(guide.checkpoint)}</p>
          </div>
        </div>
      </div>
      <div class="sample-deck">
        <p class="eyebrow">样例剧场</p>
        ${guide.demo
          .map(
            (item, demoIndex) => `
              <div class="sample-row">
                <span>${escapeHtml(item.label)} · Demo ${demoIndex + 1}</span>
                <strong>${escapeHtml(item.value)}</strong>
              </div>
            `,
          )
          .join("")}
        <p class="example"><b>样例：</b>${escapeHtml(guide.example)}</p>
      </div>
      <div class="steps">
        ${guide.steps
          .map(
            (step, stepIndex) => `
              <div class="step">
                <span>0${stepIndex + 1}</span>
                <p>${escapeHtml(step)}</p>
              </div>
            `,
          )
          .join("")}
      </div>
    </article>
  `;
}

const html = `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>方法编辑器新手教程 · 静态视觉预览</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #030605;
        --panel: rgba(255, 255, 255, 0.065);
        --line: rgba(255, 255, 255, 0.12);
        --text: #f6f0e6;
        --muted: #a9b6ba;
        --cool: #74d0d9;
        --warm: #f7c873;
        --sage: #9ec69f;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        min-height: 100vh;
        color: var(--text);
        font-family: "Aptos Display", "Microsoft YaHei", "PingFang SC", sans-serif;
        background:
          radial-gradient(circle at 16% 8%, rgba(116, 208, 217, 0.24), transparent 30%),
          radial-gradient(circle at 86% 12%, rgba(247, 200, 115, 0.18), transparent 32%),
          radial-gradient(circle at 50% 100%, rgba(158, 198, 159, 0.16), transparent 38%),
          linear-gradient(135deg, #030605 0%, #081314 44%, #0d0b07 100%);
        overflow-x: hidden;
      }

      body::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background-image:
          linear-gradient(rgba(255, 255, 255, 0.045) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255, 255, 255, 0.045) 1px, transparent 1px);
        background-size: 96px 96px;
        mask-image: radial-gradient(circle at 48% 18%, black 0%, transparent 72%);
        opacity: 0.3;
      }

      main {
        position: relative;
        width: min(1280px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 36px 0 52px;
      }

      .glass {
        position: relative;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 34px;
        background: rgba(0, 0, 0, 0.24);
        box-shadow: 0 32px 120px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(22px);
      }

      .hero {
        display: grid;
        gap: 28px;
        grid-template-columns: minmax(0, 1.1fr) minmax(340px, 0.9fr);
        padding: 30px;
      }

      .badge, .metric, .route-node, .sample-row, .step, .outcome-card {
        border: 1px solid var(--line);
        background: var(--panel);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07);
      }

      .badge {
        display: inline-flex;
        border-radius: 999px;
        padding: 8px 12px;
        color: #c8fbff;
        font-size: 11px;
        letter-spacing: 0.22em;
        text-transform: uppercase;
      }

      h1 {
        margin: 24px 0 0;
        max-width: 860px;
        font-size: clamp(48px, 7vw, 94px);
        line-height: 0.92;
        letter-spacing: -0.08em;
      }

      .lead {
        max-width: 760px;
        color: var(--muted);
        font-size: 18px;
        line-height: 1.9;
      }

      .constellation {
        min-height: 430px;
        padding: 24px;
      }

      .orbit {
        position: relative;
        height: 270px;
        margin-top: 22px;
      }

      .orbit::before, .orbit::after {
        content: "";
        position: absolute;
        left: 50%;
        top: 50%;
        border-radius: 999px;
        transform: translate(-50%, -50%);
      }

      .orbit::before {
        width: 242px;
        height: 242px;
        border: 1px solid rgba(116, 208, 217, 0.26);
        box-shadow: 0 0 46px rgba(116, 208, 217, 0.12);
      }

      .orbit::after {
        width: 148px;
        height: 148px;
        border: 1px dashed rgba(247, 200, 115, 0.28);
      }

      .core {
        position: absolute;
        left: 50%;
        top: 50%;
        display: grid;
        width: 128px;
        height: 128px;
        place-items: center;
        border-radius: 999px;
        border: 1px solid rgba(116, 208, 217, 0.5);
        background: linear-gradient(135deg, rgba(116, 208, 217, 0.22), rgba(247, 200, 115, 0.16));
        transform: translate(-50%, -50%);
        text-align: center;
      }

      .star {
        position: absolute;
        width: 106px;
        border-radius: 20px;
        padding: 12px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: rgba(7, 17, 19, 0.86);
      }

      .star:nth-child(2) { left: 50%; top: 0; transform: translateX(-50%); }
      .star:nth-child(3) { right: 0; top: 50%; transform: translateY(-50%); }
      .star:nth-child(4) { left: 50%; bottom: 0; transform: translateX(-50%); }
      .star:nth-child(5) { left: 0; top: 50%; transform: translateY(-50%); }

      .metric-grid, .launch-route, .outcomes {
        display: grid;
        gap: 14px;
      }

      .metric-grid {
        grid-template-columns: repeat(3, 1fr);
        margin-top: 18px;
      }

      .metric {
        border-radius: 18px;
        padding: 14px;
      }

      .metric strong {
        display: block;
        margin-top: 4px;
        font-size: 30px;
      }

      .launch {
        margin-top: 20px;
        padding: 22px;
      }

      .launch-route {
        grid-template-columns: repeat(4, 1fr);
        margin-top: 18px;
      }

      .route-node, .outcome-card {
        border-radius: 24px;
        padding: 16px;
      }

      .route-node:nth-child(1), .mission-card.cool {
        border-color: rgba(116, 208, 217, 0.3);
      }

      .route-node:nth-child(2), .mission-card.warm {
        border-color: rgba(247, 200, 115, 0.28);
      }

      .mission-card {
        position: relative;
        display: grid;
        gap: 20px;
        grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
        margin-top: 20px;
        padding: 22px;
        border: 1px solid var(--line);
        border-radius: 34px;
        background: rgba(0, 0, 0, 0.22);
        box-shadow: 0 24px 90px rgba(0, 0, 0, 0.32);
      }

      .mission-card h2 {
        margin: 10px 0 0;
        font-size: clamp(34px, 4vw, 58px);
        line-height: 1;
        letter-spacing: -0.06em;
      }

      .eyebrow {
        margin: 0;
        color: var(--muted);
        font-size: 11px;
        letter-spacing: 0.28em;
        text-transform: uppercase;
      }

      .summary {
        color: #c8fbff;
        font-size: 17px;
        line-height: 1.8;
      }

      .warm .summary { color: #ffe6ae; }

      .why, .example, .outcome-card p, .route-node p, .metric p {
        color: var(--muted);
        line-height: 1.75;
      }

      .result-grid {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(2, 1fr);
        margin-top: 18px;
      }

      .result-grid div {
        border-radius: 22px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.055);
        padding: 16px;
      }

      .result-grid span, .sample-row span, .step span {
        color: var(--muted);
        font-size: 11px;
        letter-spacing: 0.2em;
        text-transform: uppercase;
      }

      .sample-deck {
        min-height: 360px;
        border-radius: 28px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background:
          radial-gradient(circle at center, rgba(116, 208, 217, 0.12), transparent 42%),
          rgba(0, 0, 0, 0.28);
        padding: 18px;
      }

      .sample-row {
        margin-top: 10px;
        border-radius: 18px;
        padding: 12px;
      }

      .sample-row strong {
        display: block;
        margin-top: 6px;
      }

      .example {
        border-radius: 20px;
        border: 1px solid var(--line);
        background: rgba(0, 0, 0, 0.24);
        padding: 14px;
      }

      .steps {
        display: grid;
        grid-column: 1 / -1;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
      }

      .step {
        border-radius: 22px;
        padding: 16px;
      }

      .outcome-wall {
        margin-top: 20px;
        padding: 24px;
      }

      .outcomes {
        grid-template-columns: repeat(3, 1fr);
        margin-top: 18px;
      }

      .outcome-card h3 {
        margin: 12px 0 0;
      }

      @media (max-width: 900px) {
        .hero, .mission-card, .launch-route, .outcomes {
          grid-template-columns: 1fr;
        }

        .steps, .metric-grid, .result-grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero glass">
        <div>
          <span class="badge">Reusable method guide · static preview</span>
          <h1>方法编辑器新手教程</h1>
          <p class="lead">这是从 METHOD_GUIDES 数据生成的静态视觉预览。即使 Next 路由预览卡住，也能独立验收星图导航、发射轨道、样例剧场和最终交付墙。</p>
        </div>
        <aside class="constellation glass">
          <p class="eyebrow">Star map onboarding</p>
          <h2>星图导航</h2>
          <div class="orbit">
            <div class="core"><strong>Now</strong><br />锁定对象</div>
            ${order.map((topic, index) => `<div class="star"><span>0${index + 1}</span><br /><strong>${escapeHtml(labels[topic])}</strong></div>`).join("")}
          </div>
          <div class="metric-grid">
            <div class="metric"><span>章节</span><strong>4</strong><p>对象、字段、实例、解释输入</p></div>
            <div class="metric"><span>动作</span><strong>12</strong><p>每章 3 步照着做</p></div>
            <div class="metric"><span>样例</span><strong>4</strong><p>每章一套可复制配置</p></div>
          </div>
        </aside>
      </section>

      <section class="launch glass">
        <p class="eyebrow">Launch route</p>
        <h2>发射轨道：第一次配置就按这条线走</h2>
        <div class="launch-route">
          ${order
            .map((topic, index) => {
              const guide = METHOD_GUIDES[topic];
              return `<div class="route-node"><span>0${index + 1}</span><h3>${escapeHtml(guide.title)}</h3><p>${escapeHtml(guide.artifact)}</p></div>`;
            })
            .join("")}
        </div>
      </section>

      ${order.map(renderGuide).join("")}

      <section class="outcome-wall glass">
        <p class="eyebrow">Final unlock</p>
        <h2>跑完这套教程，新手已经能交付可复用、可审计、可解释的分析证据。</h2>
        <div class="outcomes">
          <article class="outcome-card"><span>配置闭环</span><h3>方法知道该看谁、看什么、怎么解释</h3><p>对象筛选、字段绑定、实例口径和解释输入共同形成完整配置闭环。</p></article>
          <article class="outcome-card"><span>样例可复制</span><h3>每章都有一套能直接照填的业务样例</h3><p>新手不用从空白开始，先跑通样例，再替换成自己的数据。</p></article>
          <article class="outcome-card"><span>证据能交付</span><h3>最终产物可以进入报告、图表和附录</h3><p>教程将第一次配置沉淀为可复用、可审计、可解释的分析证据。</p></article>
        </div>
      </section>
    </main>
  </body>
</html>`;

fs.mkdirSync(path.dirname(outputFile), { recursive: true });
const normalizedHtml = html.replace(/[ \t]+(?=\r?\n|$)/g, "");
fs.writeFileSync(outputFile, normalizedHtml, "utf8");
console.log(`Rendered method guide preview: ${outputFile}`);
