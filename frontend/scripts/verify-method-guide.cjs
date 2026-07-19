const fs = require("fs");
const Module = require("module");
const path = require("path");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const ts = require("typescript");

const root = path.resolve(__dirname, "..");
const guideFile = path.join(root, "src/components/method-guide-modal.tsx");
const pageFile = path.join(root, "src/app/lab/method-guide/page.tsx");

function compileCommonJs(file, extraRequire = {}, sourceOverride) {
  const source = sourceOverride ?? fs.readFileSync(file, "utf8");
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
    const rendered = output.diagnostics
      .map((diagnostic) => `${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n")}`)
      .join("\n");
    throw new Error(rendered);
  }

  const mod = new Module(file, module);
  mod.filename = `${file}.js`;
  mod.paths = Module._nodeModulePaths(root);
  const originalRequire = mod.require.bind(mod);
  mod.require = (id) => extraRequire[id] || originalRequire(id);
  mod._compile(output.outputText, mod.filename);
  return mod.exports;
}

function assert(name, ok) {
  console.log(`${ok ? "PASS" : "FAIL"} ${name}`);
  if (!ok) process.exitCode = 1;
}

const guideSource = fs.readFileSync(guideFile, "utf8");
const shellSource = fs.readFileSync(path.join(root, "src/components/analysis-workspace-shell.tsx"), "utf8");

const guideExports = compileCommonJs(guideFile);
const {
  METHOD_GUIDES,
  MethodGuideCenter,
  MethodGuideModal,
  MethodGuideStandalone,
} = guideExports;

assert("exports reusable guide data", Boolean(METHOD_GUIDES));
assert("exports reusable center", Boolean(MethodGuideCenter));
assert("exports modal", Boolean(MethodGuideModal));
assert("exports standalone page component", Boolean(MethodGuideStandalone));

for (const topic of ["object", "fields", "runs", "features"]) {
  const guide = METHOD_GUIDES?.[topic];
  assert(`${topic} has title`, Boolean(guide?.title));
  assert(`${topic} has summary`, Boolean(guide?.summary));
  assert(`${topic} has why`, Boolean(guide?.why));
  assert(`${topic} has three steps`, Array.isArray(guide?.steps) && guide.steps.length === 3);
  assert(`${topic} has example`, Boolean(guide?.example));
  assert(`${topic} has artifact`, Boolean(guide?.artifact));
  assert(`${topic} has checkpoint`, Boolean(guide?.checkpoint));
  assert(`${topic} has demo triplet`, Array.isArray(guide?.demo) && guide.demo.length === 3);
  assert(`${topic} shell entry wired`, shellSource.includes(`openMethodGuide("${topic}")`));

  const modalHtml = ReactDOMServer.renderToStaticMarkup(
    React.createElement(MethodGuideModal, {
      onClose: () => {},
      onTopicChange: () => {},
      topic,
    }),
  );
  assert(`${topic} modal renders guide title`, modalHtml.includes(guide.title));
  assert(`${topic} modal renders dialog role`, modalHtml.includes('role="dialog"'));
  assert(`${topic} modal renders example`, modalHtml.includes("样例："));
  assert(`${topic} modal renders star map shell`, modalHtml.includes("Star map onboarding"));
  assert(`${topic} modal renders checkpoint`, modalHtml.includes("最终检查"));
}

const standaloneHtml = ReactDOMServer.renderToStaticMarkup(React.createElement(MethodGuideStandalone));
assert("standalone renders tutorial title", standaloneHtml.includes("方法编辑器新手教程"));
assert("standalone renders reusable label", standaloneHtml.includes("可复用使用引导"));
assert("standalone renders examples", standaloneHtml.includes("样例："));
assert("standalone renders guide stage", standaloneHtml.includes("guide-stage"));
assert("standalone renders example theater", standaloneHtml.includes("样例剧场"));
assert("standalone renders delivery artifact", standaloneHtml.includes("最终交付"));
assert("standalone renders star map", standaloneHtml.includes("星图导航"));
assert("standalone renders launch route", standaloneHtml.includes("发射轨道"));
assert("standalone renders completion meter", standaloneHtml.includes("完成感"));
assert("standalone renders final unlock", standaloneHtml.includes("跑完这套教程"));
assert("standalone renders shippable outcome", standaloneHtml.includes("已经能交付"));

const pageSource = fs.readFileSync(pageFile, "utf8").replace("@/components/method-guide-modal", "__guide__");
const pageExports = compileCommonJs(pageFile, {
  "__guide__": guideExports,
}, pageSource);
const pageHtml = ReactDOMServer.renderToStaticMarkup(React.createElement(pageExports.default));
assert("route page renders standalone guide", pageHtml.includes("方法编辑器新手教程") && pageHtml.includes("可复用使用引导"));

assert("shell imports guide module", shellSource.includes('from "@/components/method-guide-modal"'));
assert("shell no longer owns guide data", !shellSource.includes("const METHOD_GUIDES"));
assert("guide source contains independent tutorial copy", guideSource.includes("可复用的教程控制台"));
assert("guide source contains premium visual hooks", [
  "guide-stage",
  "guide-glass",
  "guide-radar",
  "guide-scanline",
  "guide-step-card",
  "guide-command-deck",
  "guide-constellation",
  "guide-launch-strip",
  "guide-route-node",
  "guide-outcome-wall",
  "guide-outcome-card",
].every((token) => guideSource.includes(token)));

const cssSource = fs.readFileSync(path.join(root, "src/app/globals.css"), "utf8");
assert("global css contains star map motion", [
  "guide-comet",
  "guide-orbit-spin-centered",
  "guide-shimmer",
  "guide-launch-strip",
  "guide-outcome-wall",
].every((token) => cssSource.includes(token)));

require(path.join(__dirname, "render-method-guide-preview.cjs"));

const previewFile = path.join(root, "public/method-guide-preview.html");
const previewHtml = fs.readFileSync(previewFile, "utf8");
assert("static preview file generated", fs.existsSync(previewFile));
assert("static preview renders star map", previewHtml.includes("星图导航") && previewHtml.includes("Star map onboarding"));
assert("static preview renders launch route", previewHtml.includes("发射轨道") && previewHtml.includes("Launch route"));
assert("static preview renders example theater", previewHtml.includes("样例剧场") && previewHtml.includes("样例："));
assert("static preview renders final unlock", previewHtml.includes("跑完这套教程") && previewHtml.includes("已经能交付"));
