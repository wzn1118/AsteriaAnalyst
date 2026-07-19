#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const https = require("node:https");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { URL } = require("node:url");

const LOOPBACK_HOST = "127.0.0.1";
const requestedHost = arg("--host", LOOPBACK_HOST);
if (requestedHost !== LOOPBACK_HOST) {
  throw new Error(`fallback-server.cjs only listens on ${LOOPBACK_HOST}; received --host ${requestedHost}.`);
}
const host = LOOPBACK_HOST;
const port = Number(arg("--port", "3000"));
const backendBase = new URL(arg("--backend", "http://127.0.0.1:8000"));
const backendProxyTimeoutMs = Number(arg("--backend-timeout-ms", "900000"));
const skillInstallationEnabled = process.env.ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER === "1";
const repoRoot = path.resolve(__dirname, "..");
const staticRoot = path.join(repoRoot, "backend", "frontend_dist");
const labWorkspaceFile = path.join(__dirname, "lab-workspace.html");
const codexHome = resolveCodexHome();
const codexSkillsDir = path.join(codexHome, "skills");
const systemSkillsDir = path.join(codexSkillsDir, ".system");
const labSkillStatePath = path.join(codexHome, "lab-external-skills-state.json");
const skillInstallerScript = path.join(
  systemSkillsDir,
  "skill-installer",
  "scripts",
  "install-skill-from-github.py",
);

function arg(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

function resolveCodexHome() {
  const driveHome = path.join(path.parse(repoRoot).root || "", "CodexHome");
  const candidates = [process.env.CODEX_HOME, driveHome, path.join(os.homedir(), ".codex")].filter(Boolean);
  return candidates.find((candidate) => fs.existsSync(path.join(candidate, "skills"))) || candidates[0];
}

function send(res, statusCode, body, contentType = "text/plain; charset=utf-8") {
  const payload = Buffer.from(body, "utf8");
  res.writeHead(statusCode, {
    "Content-Type": contentType,
    "Content-Length": payload.length,
    "Cache-Control": "no-store",
  });
  res.end(payload);
}

function sendJson(res, statusCode, payload) {
  send(res, statusCode, JSON.stringify(payload), "application/json; charset=utf-8");
}

function sendSkillInstallationDisabled(res) {
  sendJson(res, 403, {
    code: "SKILL_INSTALLATION_DISABLED",
    detail: "Skill installation is disabled. Set ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1 for local development only.",
  });
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > 5 * 1024 * 1024) {
        reject(new Error("Request body is too large."));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      try {
        const raw = Buffer.concat(chunks).toString("utf8");
        resolve(raw ? JSON.parse(raw) : {});
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

function cleanMetaValue(value) {
  return String(value || "").trim().replace(/^['"]|['"]$/g, "");
}

function parseSkillMetadata(markdown, fallbackName) {
  const meta = { name: fallbackName, description: "" };
  const frontmatter = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!frontmatter) {
    const heading = markdown.match(/^#\s+(.+)$/m);
    if (heading) meta.description = cleanMetaValue(heading[1]);
    return meta;
  }
  frontmatter[1].split(/\r?\n/).forEach((line) => {
    const nameMatch = line.match(/^\s*name:\s*(.+)$/);
    const descriptionMatch = line.match(/^\s*description:\s*(.+)$/);
    const shortDescriptionMatch = line.match(/^\s*short-description:\s*(.+)$/);
    if (nameMatch) meta.name = cleanMetaValue(nameMatch[1]);
    if (descriptionMatch) meta.description = cleanMetaValue(descriptionMatch[1]);
    if (!meta.description && shortDescriptionMatch) meta.description = cleanMetaValue(shortDescriptionMatch[1]);
  });
  return meta;
}

function readSkillFromDir(dir, source) {
  const skillPath = path.join(dir, "SKILL.md");
  if (!fs.existsSync(skillPath)) return null;
  try {
    const markdown = fs.readFileSync(skillPath, "utf8");
    const meta = parseSkillMetadata(markdown.slice(0, 16000), path.basename(dir));
    return {
      name: meta.name || path.basename(dir),
      description: meta.description || "Local Codex skill",
      source,
      installed: true,
      local_path: dir,
    };
  } catch {
    return null;
  }
}

function listSkillRoot(root, source) {
  if (!root || !fs.existsSync(root)) return [];
  return fs
    .readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name !== ".system" && !entry.name.startsWith("__"))
    .map((entry) => readSkillFromDir(path.join(root, entry.name), source))
    .filter(Boolean);
}

function listLocalSkills() {
  return [...listSkillRoot(codexSkillsDir, "installed"), ...listSkillRoot(systemSkillsDir, "system")].sort((a, b) =>
    a.name.localeCompare(b.name),
  );
}

function readLabSkillState() {
  try {
    const raw = fs.readFileSync(labSkillStatePath, "utf8");
    const payload = JSON.parse(raw);
    if (Array.isArray(payload.mounted_skill_ids)) {
      return new Set(payload.mounted_skill_ids.map((item) => String(item)));
    }
  } catch {}
  return null;
}

function writeLabSkillState(mountedIds) {
  try {
    fs.mkdirSync(path.dirname(labSkillStatePath), { recursive: true });
    fs.writeFileSync(
      labSkillStatePath,
      JSON.stringify({ mounted_skill_ids: Array.from(mountedIds), updated_at: new Date().toISOString() }, null, 2),
      "utf8",
    );
  } catch {}
}

function listLabExternalSkills() {
  const mountedIds = readLabSkillState();
  const skills = listSkillRoot(codexSkillsDir, "installed").map((skill) => {
    const skillPath = skill.local_path || path.join(codexSkillsDir, skill.name);
    const stat = fs.existsSync(skillPath) ? fs.statSync(skillPath) : null;
    const mounted = mountedIds ? mountedIds.has(skill.name) : true;
    return {
      id: skill.name,
      name: skill.name,
      description: skill.description || "",
      source: skill.source || "installed",
      source_url: "",
      source_repo: "",
      source_ref: "",
      source_path: "",
      package_path: skillPath,
      skill_md_path: path.join(skillPath, "SKILL.md"),
      mounted,
      installed_at: stat ? stat.birthtime.toISOString() : "",
      updated_at: stat ? stat.mtime.toISOString() : "",
      file_count: fs.existsSync(skillPath) ? fs.readdirSync(skillPath).length : 0,
      instruction_chars: 0,
      instruction_excerpt: "",
    };
  });
  return skills.sort((a, b) => a.name.localeCompare(b.name));
}

function importLocalLabSkill(localPath, mount = true) {
  const cleanPath = String(localPath || "").trim();
  if (!cleanPath) {
    throw new Error("Local skill path is required.");
  }
  const resolved = path.resolve(cleanPath);
  const skill = readSkillFromDir(resolved, "local");
  if (!skill) {
    throw new Error(`Local skill directory must contain SKILL.md: ${resolved}`);
  }
  const mountedIds = readLabSkillState() || new Set(listLabExternalSkills().map((item) => item.id));
  if (mount) {
    mountedIds.add(skill.name);
  }
  writeLabSkillState(mountedIds);
  return {
    ...buildLabSkillResponse(),
    installed_count: 1,
    local_path: resolved,
  };
}

function deleteLocalLabSkill(skillId) {
  const mountedIds = readLabSkillState() || new Set();
  mountedIds.delete(String(skillId || "").trim());
  writeLabSkillState(mountedIds);
  return buildLabSkillResponse();
}

function buildLabSkillResponse() {
  const skills = listLabExternalSkills();
  return {
    summary: {
      count: skills.length,
      mounted_count: skills.filter((skill) => skill.mounted).length,
      skill_ids: skills.map((skill) => skill.id),
      mounted_skill_ids: skills.filter((skill) => skill.mounted).map((skill) => skill.id),
    },
    skills,
    default_source_url: "https://github.com/anthropics/skills",
    storage_dir: codexSkillsDir,
  };
}

function githubJson(url, redirects = 0) {
  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      {
        headers: {
          Accept: "application/vnd.github+json",
          "User-Agent": "asteria-lab-skill-browser",
        },
      },
      (response) => {
        if ([301, 302, 307, 308].includes(response.statusCode || 0) && response.headers.location && redirects < 3) {
          response.resume();
          resolve(githubJson(new URL(response.headers.location, url).toString(), redirects + 1));
          return;
        }
        const chunks = [];
        response.on("data", (chunk) => chunks.push(chunk));
        response.on("end", () => {
          const text = Buffer.concat(chunks).toString("utf8");
          if ((response.statusCode || 500) >= 400) {
            reject(new Error(text || `GitHub request failed with ${response.statusCode}`));
            return;
          }
          try {
            resolve(JSON.parse(text));
          } catch (error) {
            reject(error);
          }
        });
      },
    );
    req.setTimeout(15000, () => req.destroy(new Error("GitHub request timed out.")));
    req.on("error", reject);
  });
}

async function searchOnlineSkills(query) {
  const installedNames = new Set(listLocalSkills().map((skill) => String(skill.name).toLowerCase()));
  const groups = [
    { path: "skills/.curated", label: "curated" },
    { path: "skills/.experimental", label: "experimental" },
  ];
  const term = String(query || "").trim().toLowerCase();
  const results = [];
  for (const group of groups) {
    const entries = await githubJson(`https://api.github.com/repos/openai/skills/contents/${group.path}?ref=main`);
    for (const entry of Array.isArray(entries) ? entries : []) {
      if (entry.type !== "dir") continue;
      const searchable = `${entry.name} ${group.label}`.toLowerCase();
      if (term && !searchable.includes(term)) continue;
      results.push({
        name: entry.name,
        description: `OpenAI ${group.label} skill from openai/skills.`,
        source: `online:${group.label}`,
        installed: installedNames.has(String(entry.name).toLowerCase()),
        repo: "openai/skills",
        ref: "main",
        path: `${group.path}/${entry.name}`,
        url: entry.html_url,
      });
    }
  }
  return results.sort((a, b) => a.name.localeCompare(b.name));
}

function runProcess(command, args, timeoutMs = 240000) {
  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    const child = spawn(command, args, { cwd: repoRoot, env: process.env, windowsHide: true });
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill();
    }, timeoutMs);
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      resolve({ ok: false, code: null, stdout, stderr: stderr || error.message, timedOut });
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ ok: code === 0 && !timedOut, code, stdout, stderr, timedOut });
    });
  });
}

async function installSkillItems(items) {
  if (!fs.existsSync(skillInstallerScript)) {
    throw new Error(`Skill installer not found: ${skillInstallerScript}`);
  }
  const python = process.env.PYTHON || "python";
  const requests = (Array.isArray(items) ? items : []).slice(0, 12);
  const results = [];
  for (const item of requests) {
    const args = [skillInstallerScript];
    if (item.url) {
      args.push("--url", String(item.url));
    } else {
      const skillPath = item.path || (item.name ? `skills/.curated/${item.name}` : "");
      if (!skillPath) {
        results.push({ ok: false, item, stderr: "Missing skill path or URL." });
        continue;
      }
      args.push("--repo", String(item.repo || "openai/skills"));
      if (item.ref) args.push("--ref", String(item.ref));
      args.push("--path", String(skillPath));
    }
    const result = await runProcess(python, args);
    results.push({ ...result, item });
  }
  return results;
}

async function handleSkillsApi(req, res, url) {
  try {
    if (req.method === "GET" && url.pathname === "/api/skills") {
      sendJson(res, 200, {
        skills: listLocalSkills(),
        codex_home: codexHome,
        installer_available: fs.existsSync(skillInstallerScript),
      });
      return;
    }
    if (req.method === "GET" && url.pathname === "/api/skills/search") {
      const results = await searchOnlineSkills(url.searchParams.get("q") || "");
      sendJson(res, 200, { results });
      return;
    }
    if (req.method === "POST" && (url.pathname === "/api/skills/install" || url.pathname === "/api/skills/import")) {
      if (!skillInstallationEnabled) {
        sendSkillInstallationDisabled(res);
        return;
      }
      const body = await readJsonBody(req);
      const items = body.items || (body.item ? [body.item] : []);
      const results = await installSkillItems(items);
      const ok = results.length > 0 && results.every((result) => result.ok);
      sendJson(res, ok ? 200 : 207, { ok, results, skills: listLocalSkills() });
      return;
    }
    sendJson(res, 405, { detail: "Unsupported skills API request." });
  } catch (error) {
    sendJson(res, 500, { detail: error.message || String(error) });
  }
}

async function handleLabSkillsApi(req, res, url) {
  try {
    if (req.method === "GET" && url.pathname === "/api/lab/skills") {
      sendJson(res, 200, buildLabSkillResponse());
      return;
    }

    if (req.method === "POST" && url.pathname === "/api/lab/skills/install") {
      if (!skillInstallationEnabled) {
        sendSkillInstallationDisabled(res);
        return;
      }
      const body = await readJsonBody(req);
      const sourceUrl = String(body.source_url || "").trim();
      let installedCount = 0;
      if (sourceUrl && /github\.com\/.+\/(tree|blob)\//i.test(sourceUrl)) {
        const results = await installSkillItems([{ url: sourceUrl }]);
        installedCount = results.filter((item) => item.ok).length;
      }
      const response = buildLabSkillResponse();
      sendJson(res, 200, { ...response, installed_count: installedCount });
      return;
    }

    if (req.method === "POST" && url.pathname === "/api/lab/skills/import-local") {
      const body = await readJsonBody(req);
      sendJson(res, 200, importLocalLabSkill(body.local_path, body.mount !== false));
      return;
    }

    const mountMatch = url.pathname.match(/^\/api\/lab\/skills\/([^/]+)\/(mount|unmount)$/);
    if (req.method === "POST" && mountMatch) {
      const skillId = decodeURIComponent(mountMatch[1]);
      const action = mountMatch[2];
      const mountedIds = readLabSkillState() || new Set(listLabExternalSkills().map((skill) => skill.id));
      if (action === "mount") mountedIds.add(skillId);
      if (action === "unmount") mountedIds.delete(skillId);
      writeLabSkillState(mountedIds);
      sendJson(res, 200, buildLabSkillResponse());
      return;
    }

    const deleteMatch = url.pathname.match(/^\/api\/lab\/skills\/([^/]+)$/);
    if (req.method === "DELETE" && deleteMatch) {
      sendJson(res, 200, deleteLocalLabSkill(decodeURIComponent(deleteMatch[1])));
      return;
    }

    sendJson(res, 405, { detail: "Unsupported lab skills request." });
  } catch (error) {
    sendJson(res, 500, { detail: error.message || String(error) });
  }
}

function contentTypeFor(filePath) {
  switch (path.extname(filePath).toLowerCase()) {
    case ".html":
      return "text/html; charset=utf-8";
    case ".css":
      return "text/css; charset=utf-8";
    case ".js":
    case ".mjs":
      return "application/javascript; charset=utf-8";
    case ".json":
      return "application/json; charset=utf-8";
    case ".txt":
      return "text/plain; charset=utf-8";
    case ".svg":
      return "image/svg+xml";
    case ".ico":
      return "image/x-icon";
    case ".png":
      return "image/png";
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".webp":
      return "image/webp";
    case ".gif":
      return "image/gif";
    case ".pdf":
      return "application/pdf";
    case ".woff":
      return "font/woff";
    case ".woff2":
      return "font/woff2";
    default:
      return "application/octet-stream";
  }
}

function safeStaticPath(relativePath) {
  const target = path.resolve(staticRoot, relativePath.replace(/^\/+/, ""));
  const root = path.resolve(staticRoot);
  return target.startsWith(root) ? target : null;
}

function resolveStaticFilePath(relativePath) {
  const directPath = safeStaticPath(relativePath);
  if (directPath && fs.existsSync(directPath) && fs.statSync(directPath).isFile()) {
    return directPath;
  }

  const baseName = path.basename(relativePath);
  const pageMatch = baseName.match(/^(__next\.[^.]+(?:\.[^.]+)?)\.__PAGE__\.txt$/);
  if (pageMatch) {
    const dirName = pageMatch[1].replace(/\./g, path.sep);
    const nestedCandidates = [
      path.join(path.dirname(relativePath), dirName, "__PAGE__.txt"),
      path.join(path.dirname(relativePath), `${pageMatch[1]}.txt`),
      path.join(path.dirname(relativePath), pageMatch[1], pageMatch[1].endsWith(".txt") ? "__PAGE__.txt" : `${pageMatch[1]}.txt`),
    ];
    for (const candidate of nestedCandidates) {
      const nestedPath = safeStaticPath(candidate);
      if (nestedPath && fs.existsSync(nestedPath) && fs.statSync(nestedPath).isFile()) {
        return nestedPath;
      }
    }
  }

  return null;
}

function readStaticFile(relativePath) {
  const filePath = resolveStaticFilePath(relativePath);
  if (!filePath) {
    return null;
  }
  return fs.readFileSync(filePath, "utf8");
}

function sendStaticFile(res, relativePath, transformHtml) {
  const filePath = resolveStaticFilePath(relativePath);
  if (!filePath) {
    send(res, 404, "Not found");
    return;
  }

  if (typeof transformHtml === "function" && filePath.toLowerCase().endsWith(".html")) {
    const html = fs.readFileSync(filePath, "utf8");
    send(res, 200, transformHtml(html), "text/html; charset=utf-8");
    return;
  }

  res.writeHead(200, {
    "Content-Type": contentTypeFor(filePath),
    "Cache-Control": filePath.includes(`${path.sep}_next${path.sep}`) ? "public, max-age=600" : "no-store",
  });
  fs.createReadStream(filePath).pipe(res);
}

function proxyApi(req, res) {
  const target = new URL(req.url, backendBase);
  if (target.pathname === "/api/datasets" && target.searchParams.get("compact") !== "true") {
    target.searchParams.set("compact", "true");
  }
  const client = target.protocol === "https:" ? https : http;
  const headers = { ...req.headers, host: target.host };
  delete headers.connection;
  delete headers["proxy-connection"];
  delete headers["content-length"];

  const proxyReq = client.request(
    {
      protocol: target.protocol,
      hostname: target.hostname,
      port: target.port || (target.protocol === "https:" ? 443 : 80),
      method: req.method,
      path: `${target.pathname}${target.search}`,
      headers,
      agent: false,
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
      proxyRes.pipe(res);
    },
  );

  proxyReq.setTimeout(backendProxyTimeoutMs, () => {
    proxyReq.destroy(new Error("backend proxy timed out"));
  });

  req.on("aborted", () => {
    proxyReq.destroy();
  });

  proxyReq.on("error", (error) => {
    if (!res.headersSent) {
      send(res, 502, JSON.stringify({ detail: `后端代理失败：${error.message}` }), "application/json; charset=utf-8");
      return;
    }
    try {
      res.destroy();
    } catch {}
  });
  if (req.method === "POST" && target.pathname === "/api/lab/run") {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      const rawBody = Buffer.concat(chunks).toString("utf8");
      let body = rawBody;
      try {
        const payload = JSON.parse(rawBody || "{}");
        payload.max_methods = Math.max(1, Math.min(Number(payload.max_methods || 5), 12));
        payload.max_derived_fields = Math.max(1, Math.min(Number(payload.max_derived_fields || 16), 16));
        payload.max_chart_points = Math.max(20, Math.min(Number(payload.max_chart_points || 60), 60));
        if (Array.isArray(payload.selected_method_ids)) {
          payload.selected_method_ids = payload.selected_method_ids.slice(0, 12);
        }
        if (Array.isArray(payload.selected_report_parts)) {
          payload.selected_report_parts = payload.selected_report_parts.slice(0, 3);
          payload.report_part = payload.selected_report_parts.join(",") || payload.report_part;
        }
        body = JSON.stringify(payload);
      } catch {}
      proxyReq.end(body);
    });
    return;
  }

  req.pipe(proxyReq);
}

function injectHome(html) {
  return html;
}

/*
function analysisPageHtml() {
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Asteria 单个执行工作台</title>
  <style>
    :root{color-scheme:dark;--bg:#050806;--panel:rgba(13,18,19,.92);--line:rgba(255,255,255,.12);--soft:rgba(255,255,255,.05);--text:#f5eedf;--muted:#aab5c1;--warm:#ff9c61;--cool:#74d0d9;--purple:#9c6bff;--shadow:0 24px 70px rgba(0,0,0,.38)}
    *{box-sizing:border-box}
    body{margin:0;min-height:100vh;color:var(--text);font-family:"Aptos","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:radial-gradient(circle at 12% 12%,rgba(255,156,97,.22),transparent 24%),radial-gradient(circle at 84% 10%,rgba(116,208,217,.18),transparent 26%),linear-gradient(180deg,#040708,#0a1014 52%,#050806)}
    .shell{min-height:100vh;padding:14px}
    .frame{display:flex;flex-direction:column;gap:14px;min-height:calc(100vh - 28px)}
    .topbar,.panel,.canvas{border:1px solid var(--line);border-radius:28px;background:var(--panel);box-shadow:var(--shadow);backdrop-filter:blur(20px)}
    .topbar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding:14px 18px}
    .topbar h1{margin:3px 0 0;font-size:28px;line-height:1;letter-spacing:-.04em}
    .kicker{font-size:11px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted)}
    .top-actions{display:flex;flex-wrap:wrap;gap:10px}
    .chip,.button{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:42px;padding:0 16px;border-radius:999px;border:1px solid var(--line);text-decoration:none;color:var(--text);background:rgba(255,255,255,.06);font-size:13px;font-weight:600}
    .button-primary{background:linear-gradient(135deg,var(--warm),var(--cool));color:#081018;border:0;font-weight:800;cursor:pointer}
    .button-primary:disabled{opacity:.55;filter:grayscale(.7);cursor:not-allowed}
    .layout{display:grid;grid-template-columns:420px minmax(0,1fr);gap:14px;min-height:0;flex:1}
    @media (max-width:1080px){.layout{grid-template-columns:1fr}}
    .panel{min-height:0;overflow:auto;padding:18px;display:flex;flex-direction:column;gap:14px}
    .panel-section{border:1px solid var(--line);border-radius:28px;background:var(--soft);padding:16px}
    .field{display:grid;gap:8px}
    .field span{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}
    input,select,textarea{width:100%;border:1px solid var(--line);border-radius:18px;background:rgba(0,0,0,.22);color:var(--text);padding:13px 14px;font:inherit;outline:none}
    textarea{min-height:110px;resize:vertical}
    .grid{display:grid;gap:12px}
    .grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}
    @media (max-width:760px){.grid-2{grid-template-columns:1fr}}
    .dropzone{display:flex;flex-direction:column;justify-content:space-between;gap:16px;min-height:180px;padding:18px;border-radius:26px;border:1px dashed rgba(255,255,255,.18);background:rgba(0,0,0,.22)}
    .metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
    .metric{border:1px solid var(--line);border-radius:18px;background:rgba(0,0,0,.18);padding:12px}
    .metric .label{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}
    .metric .value{margin-top:10px;font-size:28px;font-weight:700}
    .mode-card{padding:14px;border-radius:20px;border:1px solid var(--line);background:rgba(0,0,0,.18);cursor:pointer}
    .mode-card.active{border-color:rgba(255,156,97,.55);background:rgba(255,156,97,.12)}
    .mode-card h4{margin:0;font-size:14px}
    .mode-card p{margin:8px 0 0;font-size:12px;line-height:1.6;color:var(--muted)}
    .method-card{border:1px solid var(--line);border-radius:20px;background:rgba(0,0,0,.18);padding:14px}
    .method-card.active{border-color:rgba(116,208,217,.55);background:rgba(116,208,217,.10)}
    .method-card__head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
    .method-card__title{margin:0;font-size:14px;font-weight:700}
    .method-card__desc{margin:8px 0 0;font-size:12px;line-height:1.6;color:var(--muted)}
    .method-card__meta{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.18em}
    .method-card__actions{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px}
    .method-editor-modal{position:fixed;inset:0;z-index:1200;display:none;align-items:flex-start;justify-content:center;overflow:auto;background:rgba(0,0,0,.76);padding:28px 14px;backdrop-filter:blur(14px)}
    .method-editor-modal.open{display:flex}
    .method-editor-panel{width:min(1120px,100%);border:1px solid rgba(116,208,217,.42);border-radius:28px;background:#071113;padding:18px;box-shadow:0 34px 120px rgba(0,0,0,.55)}
    .method-editor-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:14px}
    .method-editor-title{margin:4px 0 0;font-size:24px;font-weight:800;letter-spacing:-.04em;color:var(--text)}
    .method-editor-copy{margin:8px 0 0;color:var(--muted);line-height:1.7;font-size:13px}
    .method-editor-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    @media (max-width:900px){.method-editor-grid{grid-template-columns:1fr}}
    .checkbox{display:inline-flex;align-items:center;gap:8px}
    .canvas{display:flex;flex-direction:column;min-height:0;overflow:hidden}
    .canvas-head{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding:18px 22px;border-bottom:1px solid var(--line)}
    .canvas-head h2{margin:4px 0 0;font-size:28px;letter-spacing:-.04em}
    .canvas-body{min-height:0;overflow:auto;padding:18px;display:grid;gap:14px}
    .hero-card{overflow:hidden;border-radius:34px;padding:26px;border:1px solid var(--line);background:linear-gradient(135deg,rgba(255,156,97,.14),rgba(116,208,217,.08),rgba(255,255,255,.03))}
    .hero-card h3{margin:18px 0 0;font-size:clamp(34px,4vw,64px);line-height:.95;letter-spacing:-.06em}
    .muted{color:var(--muted)}
    .card{border:1px solid var(--line);border-radius:26px;background:var(--soft);padding:18px}
    .card h4{margin:0;font-size:22px}
    .pill-row{display:flex;flex-wrap:wrap;gap:10px}
    .pill{display:inline-flex;align-items:center;gap:8px;padding:9px 12px;border-radius:999px;border:1px solid var(--line);background:rgba(0,0,0,.18);font-size:12px;color:var(--muted)}
    table{width:100%;border-collapse:collapse;font-size:14px}
    th,td{padding:12px 14px;border-bottom:1px solid rgba(255,255,255,.08);text-align:left;vertical-align:top}
    th{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);background:rgba(255,255,255,.03)}
    pre{margin:0;white-space:pre-wrap;word-break:break-word;max-height:460px;overflow:auto}
    .status{padding:13px 15px;border-radius:18px;border:1px solid rgba(116,208,217,.22);background:rgba(116,208,217,.08);color:#dbfbff}
    .status.error{border-color:rgba(255,120,120,.36);background:rgba(255,120,120,.1);color:#ffdcdc}
  </style>
</head>
<body>
  <div class="shell">
    <div class="frame">
      <header class="topbar">
        <div>
          <div class="kicker">Single Run Module</div>
          <h1>自动清洗、派生指标、单方法执行和总合并解读</h1>
        </div>
        <div class="top-actions">
          <a class="chip" href="/">返回首页</a>
          <a class="chip" href="/revision">后续改造</a>
          <a class="chip" href="/revision/workspace">工作区</a>
        </div>
      </header>
      <div class="layout">
        <aside class="panel">
          <section class="panel-section">
            <h2 class="section-title">上传或选择数据</h2>
            <p class="section-copy">这里是独立方法总览页：先清洗数据，再看系统派生的指标，然后按目录逐个运行单方法，最后生成总合并智能解读。</p>
            <label class="dropzone">
              <input id="datasetFile" type="file" class="hidden" accept=".xlsx,.xls,.csv,.tsv,.dta" />
              <div>
                <div class="kicker">Core Workspace</div>
                <div id="datasetFileName" style="margin-top:12px;font-size:20px;font-weight:700">选择待分析的数据文件</div>
                <p class="section-copy">支持 CSV / TSV / DTA / XLS / XLSX。</p>
              </div>
              <button class="button button-primary" id="uploadBtn" type="button">上传进工作台</button>
            </label>
          </section>

          <section class="panel-section">
            <div class="grid">
              <label class="field"><span>数据集</span><select id="datasetSelect"></select></label>
              <label class="field"><span>工作表</span><select id="sheetSelect"></select></label>
            </div>
            <div class="metrics" style="margin-top:12px">
              <div class="metric"><div class="label">Rows</div><div class="value" id="rowsMetric">0</div></div>
              <div class="metric"><div class="label">Columns</div><div class="value" id="columnsMetric">0</div></div>
              <div class="metric"><div class="label">Numeric</div><div class="value" id="numericMetric">0</div></div>
              <div class="metric"><div class="label">Category</div><div class="value" id="categoryMetric">0</div></div>
            </div>
          </section>

          <section class="panel-section">
            <div class="kicker">Auto cleaning</div>
            <div class="grid" style="margin-top:12px">
              <button class="mode-card active" data-mode="auto" type="button">
                <h4>自动清洗与派生</h4>
                <p>自动读取数据、生成派生指标并输出路由结果。</p>
              </button>
              <button class="mode-card" data-mode="method" type="button">
                <h4>单方法执行</h4>
                <p>选中某个方法后，可单独执行并保留单项结果。</p>
              </button>
              <button class="mode-card" data-mode="merge" type="button">
                <h4>总合并解读</h4>
                <p>把自动清洗结果和勾选方法合并成一份智能解读。</p>
              </button>
            </div>
          </section>

          <section class="panel-section">
            <div class="mb-3 flex items-center justify-between gap-3">
              <p class="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">方法目录</p>
              <button class="surface-chip inline-flex items-center gap-2" id="toggleGroupBtn" type="button">
                <ChevronDown size={14} />
                <span id="groupLabel">按家族分组</span>
              </button>
            </div>
            <label class="block space-y-2">
              <span class="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">搜索方法</span>
              <div class="field-input flex items-center gap-2">
                <Search size={16} class="text-[var(--muted)]" />
                <input id="methodSearch" class="min-w-0 flex-1 border-0 bg-transparent p-0 text-[15px] outline-none" placeholder="输入方法名、家族、目标、来源" />
              </div>
            </label>
            <div class="mt-3 max-h-[360px] overflow-auto pr-1" id="methodList"></div>
          </section>

          <section class="panel-section">
            <p class="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">方法参数</p>
            <div class="mt-3 space-y-3" id="methodParams">
              <input id="targetColumn" class="field-input" placeholder="目标字段（可选）" />
              <input id="featureColumns" class="field-input" placeholder="特征字段，逗号分隔" />
              <input id="groupColumn" class="field-input" placeholder="分组字段（可选）" />
            </div>
          </section>

          <section class="panel-section">
            <p class="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">执行说明</p>
            <textarea id="workspaceBrief" class="field-input mt-3 min-h-[132px] resize-y" placeholder="告诉系统这次执行想回答什么业务问题。"></textarea>
            <div class="pill-row" style="margin-top:12px">
              <button class="button button-primary" id="runCurrentBtn" type="button">执行当前路径</button>
              <button class="button" id="runAutoBtn" type="button">自动清洗与派生</button>
              <button class="button" id="runMergedBtn" type="button">总合并解读</button>
            </div>
            <div class="status" id="statusBox" style="margin-top:14px">正在加载方法目录和数据集...</div>
          </section>
        </aside>

        <main class="canvas">
          <div class="canvas-head">
            <div>
              <div class="kicker">Result canvas</div>
              <h2 id="canvasTitle">自动清洗、派生和方法总合并结果</h2>
            </div>
            <div class="pill-row">
              <span class="pill" id="canvasDataset">未选择数据集</span>
              <span class="pill" id="canvasSheet">默认工作表</span>
            </div>
          </div>
          <div class="canvas-body" id="resultBox">
            <section class="hero-card">
              <div class="kicker">Waiting For A Run</div>
              <h3>先跑自动清洗，再逐个跑单方法，最后生成总合并解读。</h3>
              <p class="muted" style="margin-top:18px;max-width:920px;line-height:1.9">
                这个页面直接读取后端统计目录。你可以先看系统自动清洗出的派生指标，再单独执行某一个方法，最后把勾选的方法一起合并成一份总解读。
              </p>
            </section>

            <section class="grid grid-2">
              <div class="card"><h4>自动清洗</h4><p class="muted">先读取数据，完成清洗与字段理解。</p></div>
              <div class="card"><h4>派生指标</h4><p class="muted">系统会输出衍生字段和路由计划。</p></div>
              <div class="card"><h4>单方法执行</h4><p class="muted">每个方法都能单独出结果。</p></div>
              <div class="card"><h4>总合并解读</h4><p class="muted">最后把单项与自动结果汇总成一份解读。</p></div>
            </section>
          </div>
        </main>
      </div>
    </div>
  </div>
  <div id="methodEditorModal" class="method-editor-modal" role="dialog" aria-modal="true" aria-labelledby="methodEditorTitle">
    <div class="method-editor-panel">
      <div class="method-editor-head">
        <div>
          <div class="kicker">Selected method editor</div>
          <h2 id="methodEditorTitle" class="method-editor-title">Method editor</h2>
          <p id="methodEditorCopy" class="method-editor-copy">Edit fields, variables, run mode, and object picks here.</p>
        </div>
        <button class="button" id="closeMethodEditorBtn" type="button">关闭编辑浮层</button>
      </div>
      <div id="methodEditorBody"></div>
    </div>
  </div>
  <script>
    const state = {
      datasets: [],
      methods: [],
      checked: new Set(),
      selectedDatasetId: "",
      selectedSheet: "",
      selectedMethodId: "",
      selectedFile: null,
      groupedView: true,
      mode: "auto",
      methodSearch: "",
      workspaceBrief: "",
      targetColumn: "",
      featureColumns: "",
      groupColumn: "",
      autoSummary: null,
      mergedSummary: null,
      runs: [],
    };

    const $ = (id) => document.getElementById(id);

    function setStatus(message, isError) {
      const box = $("statusBox");
      box.textContent = message;
      box.className = isError ? "status error" : "status";
    }

    function datasetLabel(dataset) {
      if (!dataset) return "未选择数据集";
      return dataset.name || dataset.filename || dataset.dataset_id;
    }

    function fmt(value) {
      if (value == null) return "-";
      if (typeof value === "number") return Number.isInteger(value) ? new Intl.NumberFormat("zh-CN").format(value) : value.toFixed(4);
      if (typeof value === "string" || typeof value === "boolean") return String(value);
      try { return JSON.stringify(value); } catch { return String(value); }
    }

    async function api(path, options) {
      const response = await fetch(path, Object.assign({ cache: "no-store" }, options || {}));
      const text = await response.text();
      let payload = null;
      try { payload = text ? JSON.parse(text) : null; } catch { payload = text; }
      if (!response.ok) {
        const detail = payload && (payload.detail || payload.message) ? (payload.detail || payload.message) : response.statusText;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      return payload;
    }

    function fillDatasets() {
      const select = $("datasetSelect");
      select.innerHTML = '<option value="">选择数据集</option>';
      state.datasets.forEach((item) => {
        const option = document.createElement("option");
        option.value = item.dataset_id;
        option.textContent = datasetLabel(item);
        select.appendChild(option);
      });
      if (state.selectedDatasetId) select.value = state.selectedDatasetId;
    }

    function fillSheets() {
      const select = $("sheetSelect");
      select.innerHTML = "";
      const current = state.datasets.find((item) => item.dataset_id === state.selectedDatasetId);
      const sheets = current && current.sheets ? current.sheets : [];
      if (!sheets.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "默认工作表";
        select.appendChild(option);
      } else {
        sheets.forEach((sheet) => {
          const option = document.createElement("option");
          option.value = sheet.name;
          option.textContent = sheet.name;
          select.appendChild(option);
        });
      }
      if (current && current.active_sheet) {
        select.value = current.active_sheet;
      }
    }

    function syncMetrics() {
      const current = state.datasets.find((item) => item.dataset_id === state.selectedDatasetId);
      $("rowsMetric").textContent = fmt(current && current.row_count || 0);
      $("columnsMetric").textContent = fmt(current && current.column_count || 0);
      $("numericMetric").textContent = fmt(current && current.numeric_columns ? current.numeric_columns.length : 0);
      $("categoryMetric").textContent = fmt(current && current.categorical_columns ? current.categorical_columns.length : 0);
      $("canvasDataset").textContent = datasetLabel(current);
      $("canvasSheet").textContent = $("sheetSelect").value || (current && current.active_sheet) || "默认工作表";
    }

    function groupMethods(methods) {
      const map = new Map();
      methods.forEach((method) => {
        const key = method.family_label || method.family || "其他";
        const list = map.get(key) || [];
        list.push(method);
        map.set(key, list);
      });
      return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0], "zh-CN"));
    }

    function filteredMethods() {
      const query = state.methodSearch.trim().toLowerCase();
      if (!query) return state.methods;
      return state.methods.filter((method) => {
        return [
          method.name,
          method.name_zh,
          method.family,
          method.family_label,
          method.goal,
          method.goal_zh,
          method.status,
          method.source,
        ]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(query));
      });
    }

    function methodCanRun(method) {
      const current = state.datasets.find((item) => item.dataset_id === state.selectedDatasetId);
      if (!current) return false;
      return Boolean(current.numeric_columns?.length || current.categorical_columns?.length || current.datetime_columns?.length);
    }

    function selectedMethod() {
      return state.methods.find((item) => item.id === state.selectedMethodId) || state.methods[0] || null;
    }

    function openMethodEditor(methodId) {
      if (methodId) state.selectedMethodId = methodId;
      const method = selectedMethod();
      const modal = $("methodEditorModal");
      const title = $("methodEditorTitle");
      const copy = $("methodEditorCopy");
      const body = $("methodEditorBody");
      title.textContent = method ? (method.name_zh || method.name || method.id) : "Method editor is opening";
      copy.textContent = method
        ? "点击已收到。这里现在是独立编辑浮层，不再静默停留在列表里。"
        : "点击已收到，但方法目录还没有返回具体方法。请稍等目录加载完成。";
      if (method) {
        body.innerHTML = `
          <div class="method-editor-grid">
            <label class="field"><span>目标字段</span><input id="editorTargetColumn" value="${fmt(state.targetColumn)}" placeholder="可选" /></label>
            <label class="field"><span>特征字段</span><input id="editorFeatureColumns" value="${fmt(state.featureColumns)}" placeholder="逗号分隔" /></label>
            <label class="field"><span>分组字段</span><input id="editorGroupColumn" value="${fmt(state.groupColumn)}" placeholder="可选" /></label>
          </div>
          <div class="card" style="margin-top:14px">
            <div class="method-card__head">
              <div>
                <div class="kicker">${fmt(method.family_label || method.family || "method")}</div>
                <h3 class="method-card__title">${fmt(method.name_zh || method.name)}</h3>
              </div>
              <span class="surface-chip">${fmt(method.status || "catalog")}</span>
            </div>
            <p class="method-card__desc">${fmt(method.goal_zh || method.goal || "当前方法可在这里配置后执行。")}</p>
            <div class="method-card__meta">
              <span>${fmt(method.source || "catalog")}</span>
              <span>${fmt((method.output_labels || []).join(" · "))}</span>
              <span>${fmt((method.role_labels || []).join(" · "))}</span>
            </div>
            <div class="method-card__actions">
              <button type="button" class="button button-primary" id="editorRunMethodBtn">执行这个方法</button>
              <button type="button" class="button" id="editorSelectMethodBtn">保持选中</button>
            </div>
          </div>
        `;
        $("editorTargetColumn").addEventListener("input", (event) => state.targetColumn = event.target.value);
        $("editorFeatureColumns").addEventListener("input", (event) => state.featureColumns = event.target.value);
        $("editorGroupColumn").addEventListener("input", (event) => state.groupColumn = event.target.value);
        $("editorSelectMethodBtn").addEventListener("click", () => {
          state.checked.add(method.id);
          renderControls();
        });
        $("editorRunMethodBtn").addEventListener("click", async () => {
          try {
            await runSingleMethod(method);
          } catch (error) {
            setStatus(error.message || "执行失败。", true);
          }
        });
      } else {
        body.innerHTML = '<div class="card"><p class="method-editor-copy">编辑浮层已打开。目录加载完成后，再点击具体方法即可编辑。</p></div>';
      }
      modal.classList.add("open");
      renderControls();
    }

    function closeMethodEditor() {
      $("methodEditorModal").classList.remove("open");
    }

    function renderMethodList() {
      const container = $("methodList");
      const methods = filteredMethods();
      const cards = [];
      const renderCard = (method) => {
        const active = state.selectedMethodId === method.id;
        const checked = state.checked.has(method.id);
        const disabled = !methodCanRun(method);
        return `
          <div class="method-card ${active ? "active" : ""}">
            <div class="method-card__head">
              <div>
                <p class="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">${fmt(method.family_label || method.family || "其他")}</p>
                <h4 class="method-card__title">${fmt(method.name_zh || method.name)}</h4>
              </div>
              <span class="surface-chip">${fmt(method.status || "catalog")}</span>
            </div>
            <p class="method-card__desc">${fmt(method.goal_zh || method.goal || "")}</p>
            <div class="method-card__meta">
              <span>${fmt(method.source || "catalog")}</span>
              <span>${fmt((method.output_labels || []).join(" · "))}</span>
              <span>${fmt((method.role_labels || []).join(" · "))}</span>
            </div>
            <div class="method-card__actions">
              <label class="checkbox">
                <input data-toggle-method="${method.id}" type="checkbox" ${checked ? "checked" : ""} />
                纳入总合并
              </label>
              <button type="button" class="surface-chip" data-select-method="${method.id}">选择</button>
              <button type="button" class="surface-chip" data-edit-method="${method.id}">编辑</button>
              <button type="button" class="surface-chip" data-run-method="${method.id}" ${disabled ? "disabled" : ""}>单独执行</button>
            </div>
          </div>
        `;
      };
      if (state.groupedView) {
        groupMethods(methods).forEach(([family, familyMethods]) => {
          cards.push(`<div class="mb-4"><p class="mb-2 text-xs uppercase tracking-[0.24em] text-[var(--muted)]">${fmt(family)}</p><div class="grid gap-2">${familyMethods.map(renderCard).join("")}</div></div>`);
        });
      } else {
        cards.push(`<div class="grid gap-2">${methods.map(renderCard).join("")}</div>`);
      }
      container.innerHTML = cards.join("") || '<p class="rounded-[16px] border border-white/10 bg-white/5 px-4 py-5 text-sm leading-7 text-[var(--muted)]">没有匹配的方法。</p>';
      container.querySelectorAll("[data-run-method]").forEach((node) => {
        node.addEventListener("click", () => {
          const method = state.methods.find((item) => item.id === node.getAttribute("data-run-method"));
          if (method) runSingleMethod(method);
        });
      });
      container.querySelectorAll("[data-select-method]").forEach((node) => {
        node.addEventListener("click", () => {
          const id = node.getAttribute("data-select-method") || "";
          state.selectedMethodId = id;
          state.mode = "method";
          openMethodEditor(id);
        });
      });
      container.querySelectorAll("[data-edit-method]").forEach((node) => {
        node.addEventListener("click", () => {
          const id = node.getAttribute("data-edit-method") || "";
          state.selectedMethodId = id;
          state.mode = "method";
          openMethodEditor(id);
        });
      });
      container.querySelectorAll("[data-toggle-method]").forEach((node) => {
        node.addEventListener("change", () => {
          const id = node.getAttribute("data-toggle-method");
          if (!id) return;
          if (node.checked) state.checked.add(id);
          else state.checked.delete(id);
          renderCanvas();
        });
      });
    }

    function renderControls() {
      $("groupLabel").textContent = state.groupedView ? "按家族分组" : "平铺";
      $("targetColumn").value = state.targetColumn;
      $("featureColumns").value = state.featureColumns;
      $("groupColumn").value = state.groupColumn;
      $("workspaceBrief").value = state.workspaceBrief;
      $("methodSearch").value = state.methodSearch;
      fillDatasets();
      fillSheets();
      syncMetrics();
      renderMethodList();
      renderCanvasHeader();
    }

    function renderCanvasHeader() {
      $("canvasTitle").textContent = state.mode === "method"
        ? "单项结果 + 总合并解读"
        : state.mode === "merge"
        ? "总合并解读"
        : "自动清洗、派生和方法总合并结果";
    }

    function buildMethodPayload(method) {
      return {
        dataset_id: state.selectedDatasetId,
        active_sheet: state.selectedSheet || null,
        analysis_type: method.id,
        target: state.targetColumn.trim() || null,
        features: splitColumns(state.featureColumns),
        group_column: state.groupColumn.trim() || null,
        clusters: 3,
        components: 2,
        metric_type: "auto",
        alpha: 0.05,
        hypothesis: "two-sided",
        user_goal: state.workspaceBrief,
      };
    }

    function renderAutoSummary() {
      const payload = state.autoSummary;
      if (!payload) {
        return `
          <section class="card">
            <p class="text-sm text-[var(--muted)]">先点击“自动清洗与派生”，这里会显示自动读数、派生指标和方法路由总览。</p>
          </section>
        `;
      }
      const metrics = payload.metrics || {};
      const cards = Object.entries(metrics).map(([label, value]) => `
        <article class="card">
          <p class="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">${fmt(label)}</p>
          <p class="mt-4 break-words text-3xl font-semibold text-[var(--text-strong)]">${fmt(value)}</p>
        </article>
      `).join("");
      const derived = payload.data && payload.data.derived_fields ? payload.data.derived_fields : [];
      const derivedChips = Array.isArray(derived)
        ? derived.slice(0, 24).map((item) => `<span class="pill">${fmt(item.field || item.name || item.metric_id || item)}</span>`).join("")
        : "";
      const routePlan = payload.data && payload.data.field_semantic_route_plan ? payload.data.field_semantic_route_plan : null;
      const routeRows = routePlan && Array.isArray(routePlan.rows)
        ? routePlan.rows.slice(0, 12).map((row) => `<tr>${Object.keys(row).slice(0, 6).map((key) => `<td>${fmt(row[key])}</td>`).join("")}</tr>`).join("")
        : "";
      return `
        <section class="card">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">自动清洗与派生</p>
              <h3 class="mt-2 text-2xl font-semibold text-[var(--text-strong)]">${fmt(payload.title || "自动清洗结果")}</h3>
            </div>
            <span class="surface-chip">方法 ${fmt(metrics.routed_method_count || 0)}</span>
          </div>
          <p class="mt-4 text-sm leading-7 text-[var(--muted)]">${fmt(payload.narrative || "")}</p>
          <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">${cards}</div>
          <div class="mt-5 flex flex-wrap gap-2">${derivedChips || '<span class="text-sm text-[var(--muted)]">暂无派生字段。</span>'}</div>
          ${routePlan ? `
            <div class="mt-5 overflow-hidden rounded-[22px] border border-white/10">
              <p class="border-b border-white/10 px-4 py-3 text-sm font-semibold text-[var(--text-strong)]">方法路由</p>
              <div class="overflow-x-auto">
                <table class="min-w-full text-left text-sm">
                  <thead class="bg-white/6 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
                    <tr><th class="px-4 py-3">field</th><th class="px-4 py-3">role</th><th class="px-4 py-3">source</th><th class="px-4 py-3">derived</th></tr>
                  </thead>
                  <tbody class="divide-y divide-white/8">${routeRows}</tbody>
                </table>
              </div>
            </div>` : ""}
          <pre class="mt-5 rounded-[22px] border border-white/10 bg-black/40 p-4 text-xs leading-6">${stringifySafe(payload.data || payload)}</pre>
        </section>
      `;
    }

    function renderMergedSummary() {
      const payload = state.mergedSummary;
      if (!payload) {
        return '<section class="card"><p class="text-sm text-[var(--muted)]">还没有生成总合并解读。先运行自动清洗，再点击“总合并解读”。</p></section>';
      }
      return `
        <section class="card">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">总合并智能解读</p>
              <h3 class="mt-2 text-2xl font-semibold text-[var(--text-strong)]">${fmt(payload.title || "总合并解读")}</h3>
            </div>
            <span class="surface-chip">执行方法 ${state.checked.size || state.methods.length}</span>
          </div>
          <p class="mt-4 text-sm leading-7 text-[var(--muted)]">${fmt(payload.executive_summary ? payload.executive_summary.join("；") : payload.narrative || "")}</p>
          <div class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            ${(payload.key_metrics || []).slice(0, 8).map((item) => `
              <article class="card">
                <p class="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">${fmt(item.label)}</p>
                <p class="mt-3 text-3xl font-semibold text-[var(--text-strong)]">${fmt(item.value)}</p>
                <p class="mt-2 text-sm leading-6 text-[var(--muted)]">${fmt(item.detail)}</p>
              </article>
            `).join("")}
          </div>
          ${(payload.downloadables || []).length ? `
            <div class="mt-5 flex flex-wrap gap-2">
              ${(payload.downloadables || []).slice(0, 10).map((item) => `<a class="button" href="${item.path}" target="_blank" rel="noreferrer">${fmt(item.name)}</a>`).join("")}
            </div>` : ""}
          <pre class="mt-5 rounded-[22px] border border-white/10 bg-black/40 p-4 text-xs leading-6">${stringifySafe(payload)}</pre>
        </section>
      `;
    }

    function renderMethodRuns() {
      const cards = state.runs.slice(0, 12).map((item) => `
        <div class="rounded-[18px] border border-white/10 bg-black/18 p-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">${fmt(item.method_id)}</p>
              <h4 class="mt-1 text-lg font-semibold text-[var(--text-strong)]">${fmt(item.method_name_zh || item.method_name)}</h4>
            </div>
            <span class="surface-chip">${fmt(item.status)}</span>
          </div>
          <pre class="mt-3 max-h-[220px] overflow-auto rounded-[16px] bg-black/30 p-3 text-xs leading-6">${stringifySafe(item.payload)}</pre>
        </div>
      `).join("");
      return `
        <section class="card">
          <p class="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">单项结果</p>
          <div class="mt-4 grid gap-3">${cards || '<p class="text-sm text-[var(--muted)]">完成后，这里会逐个列出每个方法的单独结果。</p>'}</div>
        </section>
      `;
    }

    function renderMethodsOverview() {
      const cards = state.methods.slice(0, 80).map((method) => `
        <div class="rounded-[18px] border border-white/10 bg-black/18 p-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-[10px] uppercase tracking-[0.22em] text-[var(--muted)]">${fmt(method.family_label || method.family || "其他")}</p>
              <h4 class="mt-1 text-lg font-semibold text-[var(--text-strong)]">${fmt(method.name_zh || method.name)}</h4>
            </div>
            <span class="surface-chip">${fmt(method.status)}</span>
          </div>
          <p class="mt-3 text-sm leading-7 text-[var(--muted)]">${fmt(method.goal_zh || method.goal)}</p>
        </div>
      `).join("");
      return `
        <section class="card">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">方法总览</p>
              <h3 class="mt-1 text-xl font-semibold text-[var(--text-strong)]">${state.methods.length} methods · live ${state.methods.filter((m) => m.status === "live").length} · catalog ${state.methods.filter((m) => m.status === "catalog").length} · planned ${state.methods.filter((m) => m.status === "planned").length}</h3>
            </div>
          </div>
          <div class="mt-4 grid gap-4 xl:grid-cols-2">${cards}</div>
        </section>
      `;
    }

    function renderCanvas() {
      const pieces = [renderAutoSummary(), renderMethodRuns(), renderMergedSummary(), renderMethodsOverview()];
      $("resultBox").innerHTML = pieces.join("");
    }

    async function loadInitial() {
      try {
        const [datasetPayload, methodPayload] = await Promise.all([
          api("/api/datasets?compact=false"),
          api("/api/analysis/auto/methods"),
        ]);
        state.datasets = datasetPayload.datasets || [];
        state.methods = methodPayload.methods || [];
        state.selectedMethodId = state.methods[0] ? state.methods[0].id : "";
        if (state.datasets[0]) {
          state.selectedDatasetId = state.datasets[0].dataset_id;
          state.selectedSheet = state.datasets[0].active_sheet || state.datasets[0].sheets?.[0]?.name || "";
        }
        state.methods.filter((method) => method.status === "live" || method.status === "catalog").forEach((method) => state.checked.add(method.id));
        setStatus("方法目录已加载。可先自动清洗，再挑任一方法单独执行。");
        renderControls();
        renderCanvas();
      } catch (error) {
        setStatus(error.message || "加载失败。", true);
      }
    }

    async function refreshDatasets(preselectId) {
      const payload = await api("/api/datasets?compact=false");
      const nextDatasets = payload.datasets || [];
      state.datasets = nextDatasets;
      state.selectedDatasetId = nextDatasets.find((dataset) => dataset.dataset_id === preselectId)?.dataset_id || state.selectedDatasetId || nextDatasets[0]?.dataset_id || "";
      state.selectedSheet = (nextDatasets.find((dataset) => dataset.dataset_id === state.selectedDatasetId) || nextDatasets[0])?.active_sheet || (nextDatasets.find((dataset) => dataset.dataset_id === state.selectedDatasetId) || nextDatasets[0])?.sheets?.[0]?.name || "";
      fillDatasets();
      fillSheets();
      syncMetrics();
    }

    async function uploadDataset() {
      if (!state.selectedFile) throw new Error("请先选择数据文件。");
      const form = new FormData();
      form.append("file", state.selectedFile);
      const uploaded = await api("/api/datasets/upload", { method: "POST", body: form });
      await refreshDatasets(uploaded.dataset_id);
      setStatus("数据已进入工作台：" + datasetLabel(uploaded));
    }

    async function runAuto() {
      if (!state.selectedDatasetId) throw new Error("请先选择或上传一个数据集。");
      setStatus("正在自动清洗、生成派生指标和方法路由...");
      const selectedMethodIds = Array.from(state.checked.size ? state.checked : new Set(state.methods.map((method) => method.id)));
      const payload = await api("/api/analysis/auto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: state.selectedDatasetId,
          active_sheet: state.selectedSheet || null,
          user_goal: state.workspaceBrief,
          report_part: "analysis_lab_workspace",
          max_methods: 24,
          max_derived_fields: 64,
          max_chart_points: 180,
          execution_mode: "smart_merge",
          selected_method_ids: selectedMethodIds,
        }),
      });
      state.autoSummary = payload;
      renderCanvas();
      setStatus("自动清洗与派生已完成。");
    }

    async function runMerged() {
      if (!state.selectedDatasetId) throw new Error("请先选择或上传一个数据集。");
      setStatus("正在生成总合并智能解读...");
      const payload = await api(`/api/datasets/${encodeURIComponent(state.selectedDatasetId)}/smart-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sheet_name: state.selectedSheet || null,
          report_style: "deep_dive",
          business_profile: "auto",
          user_requirement: state.workspaceBrief,
          raw_user_requirement: state.workspaceBrief,
          enable_generic_business_runtime: true,
        }),
      });
      state.mergedSummary = payload;
      renderCanvas();
      setStatus("总合并智能解读已完成。");
    }

    async function runSingleMethod(method) {
      if (!state.selectedDatasetId) throw new Error("请先选择或上传一个数据集。");
      state.selectedMethodId = method.id;
      renderControls();
      setStatus("正在独立执行方法：" + (method.name_zh || method.name));
      const payload = await api("/api/statistics/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildMethodPayload(method)),
      });
      state.runs = [
        {
          method_id: method.id,
          method_name: method.name,
          method_name_zh: method.name_zh,
          status: "completed",
          source: method.source,
          payload,
          ran_at: new Date().toISOString(),
        },
        ...state.runs.filter((item) => item.method_id !== method.id),
      ];
      renderCanvas();
      setStatus("方法执行完成：" + (method.name_zh || method.name));
    }

    $("datasetFile").addEventListener("change", (event) => {
      const file = event.target.files && event.target.files[0];
      state.selectedFile = file || null;
      $("datasetFileName").textContent = file ? file.name : "选择待分析的数据文件";
    });
    $("datasetSelect").addEventListener("change", (event) => {
      state.selectedDatasetId = event.target.value;
      const current = state.datasets.find((item) => item.dataset_id === state.selectedDatasetId);
      state.selectedSheet = current?.active_sheet || current?.sheets?.[0]?.name || "";
      fillSheets();
      syncMetrics();
      renderControls();
      renderCanvas();
    });
    $("sheetSelect").addEventListener("change", (event) => {
      state.selectedSheet = event.target.value;
      syncMetrics();
    });
    $("methodSearch").addEventListener("input", (event) => {
      state.methodSearch = event.target.value;
      renderMethodList();
    });
    $("toggleGroupBtn").addEventListener("click", () => {
      state.groupedView = !state.groupedView;
      renderControls();
    });
    $("targetColumn").addEventListener("input", (event) => state.targetColumn = event.target.value);
    $("featureColumns").addEventListener("input", (event) => state.featureColumns = event.target.value);
    $("groupColumn").addEventListener("input", (event) => state.groupColumn = event.target.value);
    $("workspaceBrief").addEventListener("input", (event) => state.workspaceBrief = event.target.value);
    $("closeMethodEditorBtn").addEventListener("click", closeMethodEditor);
    $("methodEditorModal").addEventListener("click", (event) => {
      if (event.target === $("methodEditorModal")) closeMethodEditor();
    });

    $("runCurrentBtn").addEventListener("click", async () => {
      try {
        if (state.mode === "method") {
          const method = state.methods.find((item) => item.id === state.selectedMethodId);
          if (!method) throw new Error("请先选择一个方法。");
          await runSingleMethod(method);
        } else if (state.mode === "merge") {
          await runMerged();
        } else {
          await runAuto();
        }
      } catch (error) {
        setStatus(error.message || "执行失败。", true);
      }
    });
    $("runAutoBtn").addEventListener("click", async () => {
      try {
        await runAuto();
      } catch (error) {
        setStatus(error.message || "自动清洗失败。", true);
      }
    });
    $("runMergedBtn").addEventListener("click", async () => {
      try {
        await runMerged();
      } catch (error) {
        setStatus(error.message || "总合并失败。", true);
      }
    });

    loadInitial().catch((error) => setStatus(error.message || "初始化失败。", true));
  </script>
</body>
</html>`;
}

*/

function labFallbackPageHtml() {
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Asteria Lab 方法实验台</title>
  <style>
    :root{color-scheme:dark;--bg:#050806;--panel:rgba(10,17,19,.92);--line:rgba(255,255,255,.14);--soft:rgba(255,255,255,.06);--text:#f6efe2;--muted:#aab5c1;--warm:#ff9c61;--cool:#74d0d9;--danger:#ff7f7f}
    *{box-sizing:border-box}
    body{margin:0;min-height:100vh;background:radial-gradient(circle at 14% 8%,rgba(255,156,97,.22),transparent 28%),radial-gradient(circle at 86% 10%,rgba(116,208,217,.20),transparent 30%),linear-gradient(180deg,#040708,#091114 58%,#050806);color:var(--text);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
    .shell{width:min(1180px,calc(100vw - 28px));margin:0 auto;padding:24px 0 44px}
    .hero,.panel,.method-card,.editor-panel{border:1px solid var(--line);border-radius:28px;background:var(--panel);box-shadow:0 28px 90px rgba(0,0,0,.42);backdrop-filter:blur(18px)}
    .hero{padding:26px;display:flex;gap:18px;align-items:flex-end;justify-content:space-between;flex-wrap:wrap}
    .kicker{font-size:11px;letter-spacing:.26em;text-transform:uppercase;color:var(--muted)}
    h1{margin:8px 0 0;font-size:clamp(34px,6vw,68px);line-height:.92;letter-spacing:-.06em}
    p{color:var(--muted);line-height:1.75}
    .actions{display:flex;flex-wrap:wrap;gap:10px}
    .button,.chip{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:0 14px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.07);color:var(--text);font-weight:700;text-decoration:none;cursor:pointer;transition:transform .16s ease,border-color .16s ease,background .16s ease,box-shadow .16s ease}
    .button:hover,.chip:hover{border-color:rgba(116,208,217,.54);background:rgba(116,208,217,.12);box-shadow:0 12px 32px rgba(0,0,0,.26)}
    .button:active,.chip:active{transform:translateY(1px) scale(.98)}
    .button-primary,.chip-primary{border:0;color:#081018;background:linear-gradient(135deg,var(--warm),var(--cool))}
    .layout{display:grid;grid-template-columns:340px minmax(0,1fr);gap:16px;margin-top:16px}
    @media (max-width:900px){.layout{grid-template-columns:1fr}}
    .panel{padding:18px}
    .field{display:grid;gap:8px;margin-top:12px}
    .field span{font-size:12px;color:var(--muted)}
    input,textarea,select{width:100%;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.07);color:var(--text);padding:12px 13px;font:inherit;outline:none;transition:border-color .16s ease,box-shadow .16s ease,background .16s ease}
    input:focus,textarea:focus,select:focus{border-color:rgba(116,208,217,.74);background:rgba(116,208,217,.09);box-shadow:0 0 0 4px rgba(116,208,217,.12)}
    select option{background:#081114;color:var(--text)}
    textarea{min-height:96px;resize:vertical}
    .method-grid{display:grid;gap:12px}
    .method-card{padding:16px;cursor:pointer;position:relative;overflow:hidden;transition:transform .18s ease,border-color .18s ease,background .18s ease,box-shadow .18s ease}
    .method-card::after{content:"";position:absolute;inset:auto 14px 0;height:3px;border-radius:999px;background:linear-gradient(90deg,var(--warm),var(--cool));opacity:0;transform:scaleX(.35);transform-origin:left;transition:opacity .18s ease,transform .18s ease}
    .method-card:hover{transform:translateY(-2px);border-color:rgba(116,208,217,.46);background:rgba(13,24,27,.94)}
    .method-card:active{transform:translateY(0) scale(.995)}
    .method-card:focus-visible{outline:0;border-color:rgba(255,156,97,.72);box-shadow:0 0 0 4px rgba(255,156,97,.15),0 28px 90px rgba(0,0,0,.42)}
    .method-card.active{border-color:rgba(116,208,217,.78);background:linear-gradient(135deg,rgba(116,208,217,.16),rgba(255,156,97,.08)),var(--panel)}
    .method-card.active::after{opacity:1;transform:scaleX(1)}
    .method-card.queued{border-color:rgba(255,156,97,.46)}
    .method-card.queued .queue-mark{color:#081018;background:linear-gradient(135deg,var(--warm),#ffd48d);border:0}
    .method-card.bump{animation:method-bump .22s ease}
    @keyframes method-bump{0%{transform:scale(.995)}55%{transform:scale(1.012)}100%{transform:scale(1)}}
    .method-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
    .method-title{margin:5px 0 0;font-size:18px}
    .method-desc{margin:10px 0 0;font-size:13px}
    .method-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
    .filter-rail{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) auto auto;gap:10px;margin:14px 0}
    @media (max-width:860px){.filter-rail{grid-template-columns:1fr 1fr}.filter-rail .button{width:100%}}
    .status{margin-top:14px;padding:12px 14px;border-radius:18px;background:rgba(255,255,255,.07);color:var(--muted)}
    .status.error{color:#ffd6d6;background:rgba(255,127,127,.12);border:1px solid rgba(255,127,127,.28)}
    .queue-panel{margin-top:14px;padding:14px;border:1px solid rgba(255,156,97,.24);border-radius:22px;background:linear-gradient(135deg,rgba(255,156,97,.10),rgba(116,208,217,.06))}
    .queue-list{display:grid;gap:8px;margin-top:12px;max-height:260px;overflow:auto}
    .queue-item{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;padding:10px 10px;border:1px solid rgba(255,255,255,.12);border-radius:16px;background:rgba(0,0,0,.18)}
    .queue-item strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px}
    .queue-item span{display:block;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-size:11px}
    .empty-note{color:var(--muted);font-size:13px;line-height:1.6}
    .data-panel{margin-top:0;border-color:rgba(116,208,217,.30);background:linear-gradient(135deg,rgba(116,208,217,.12),rgba(255,156,97,.06))}
    .dropzone{display:grid;gap:10px;margin-top:12px;padding:16px;border:1px dashed rgba(116,208,217,.48);border-radius:22px;background:rgba(116,208,217,.07);cursor:pointer;transition:border-color .16s ease,background .16s ease,transform .16s ease}
    .dropzone:hover{border-color:rgba(255,156,97,.72);background:rgba(255,156,97,.08);transform:translateY(-1px)}
    .hidden-input{position:absolute;inline-size:1px;block-size:1px;opacity:0;pointer-events:none}
    .file-name{font-size:18px;font-weight:800;color:var(--text)}
    .metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}
    .metric{padding:10px 12px;border:1px solid rgba(255,255,255,.12);border-radius:16px;background:rgba(0,0,0,.18)}
    .metric .label{color:var(--muted);font-size:10px;letter-spacing:.16em;text-transform:uppercase}
    .metric .value{margin-top:3px;font-size:18px;font-weight:800}
    .operation-dock{position:fixed;left:50%;bottom:18px;z-index:15;width:min(880px,calc(100vw - 28px));display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 16px;border:1px solid rgba(116,208,217,.38);border-radius:24px;background:rgba(6,12,14,.90);box-shadow:0 28px 90px rgba(0,0,0,.54);backdrop-filter:blur(20px);transform:translate(-50%,120%);opacity:0;pointer-events:none;transition:transform .22s ease,opacity .22s ease}
    .operation-dock.show{transform:translate(-50%,0);opacity:1;pointer-events:auto}
    .dock-copy{min-width:0}
    .dock-copy strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:15px}
    .dock-copy span{display:block;margin-top:3px;color:var(--muted);font-size:12px}
    .dock-actions{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}
    .shortcut{margin-left:8px;padding:2px 7px;border-radius:999px;background:rgba(0,0,0,.25);font-size:11px;color:rgba(246,239,226,.78)}
    .operation-toast{position:fixed;right:20px;bottom:104px;z-index:26;max-width:min(360px,calc(100vw - 40px));padding:12px 14px;border:1px solid rgba(255,255,255,.16);border-radius:18px;background:rgba(6,12,14,.92);color:var(--text);box-shadow:0 18px 60px rgba(0,0,0,.42);opacity:0;transform:translateY(12px);pointer-events:none;transition:opacity .18s ease,transform .18s ease}
    .operation-toast.show{opacity:1;transform:translateY(0)}
    .editor{position:fixed;inset:0;z-index:20;display:none;align-items:flex-start;justify-content:center;overflow:auto;background:rgba(0,0,0,.76);padding:30px 14px}
    .editor.open{display:flex}
    .editor-panel{width:min(980px,100%);padding:20px}
    .editor.open .editor-panel{animation:panel-in .2s ease both}
    @keyframes panel-in{from{opacity:0;transform:translateY(12px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)}}
    .editor-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:14px}
    .editor-title{margin:5px 0 0;font-size:30px;letter-spacing:-.04em}
    .editor-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    @media (max-width:760px){.editor-grid{grid-template-columns:1fr}}
    code{color:#dce6e4}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div>
        <div class="kicker">Lab Surface</div>
        <h1>Lab 方法实验台</h1>
        <p>选择或编辑任一方法会打开独立浮层，不再静默停留在列表里。</p>
      </div>
      <div class="actions">
        <a class="button" href="/">返回首页</a>
        <a class="button" href="/analysis">正式分析</a>
        <button class="button button-primary" id="refreshMethodsBtn" type="button">刷新方法目录</button>
      </div>
    </section>
    <div class="layout">
      <aside class="panel">
        <section class="queue-panel data-panel">
          <div class="kicker">Data Workspace</div>
          <label class="dropzone">
            <input id="datasetFile" class="hidden-input" type="file" accept=".xlsx,.xls,.csv,.tsv,.dta" />
            <span class="file-name" id="datasetFileName">选择待分析的数据文件</span>
            <span class="empty-note">支持 CSV / TSV / DTA / XLS / XLSX。先上传或选择数据集，再运行方法。</span>
          </label>
          <div class="actions" style="margin-top:12px">
            <button class="button button-primary" id="uploadBtn" type="button">上传进工作台</button>
            <button class="button" id="refreshDatasetsBtn" type="button">刷新数据集</button>
          </div>
          <label class="field"><span>数据集</span><select id="datasetSelect"><option value="">正在加载数据集...</option></select></label>
          <label class="field"><span>工作表</span><select id="sheetSelect"><option value="">默认工作表</option></select></label>
          <div class="metric-grid">
            <div class="metric"><div class="label">Rows</div><div class="value" id="rowsMetric">0</div></div>
            <div class="metric"><div class="label">Columns</div><div class="value" id="columnsMetric">0</div></div>
            <div class="metric"><div class="label">Numeric</div><div class="value" id="numericMetric">0</div></div>
            <div class="metric"><div class="label">Category</div><div class="value" id="categoryMetric">0</div></div>
          </div>
        </section>
        <div class="kicker">Run Context</div>
        <label class="field"><span>目标字段</span><input id="targetColumn" placeholder="可选，例如 revenue" /></label>
        <label class="field"><span>特征字段</span><input id="featureColumns" placeholder="逗号分隔，例如 channel,cost" /></label>
        <label class="field"><span>分组字段</span><input id="groupColumn" placeholder="可选，例如 city" /></label>
        <label class="field"><span>执行说明</span><textarea id="workspaceBrief" placeholder="这次希望回答什么业务问题？"></textarea></label>
        <div id="status" class="status">正在加载方法目录...</div>
        <section class="queue-panel">
          <div class="method-head">
            <div>
              <div class="kicker">Work Queue</div>
              <p id="queueSummary">候选队列为空</p>
            </div>
          </div>
          <div class="actions">
            <button class="button" id="copyQueueBtn" type="button">复制队列 ID</button>
            <button class="button" id="clearQueueBtn" type="button">清空队列</button>
          </div>
          <div id="queueList" class="queue-list"><p class="empty-note">把常用方法加入候选队列，后续可以只看候选或复制 ID。</p></div>
        </section>
      </aside>
      <main class="panel">
        <div class="method-head">
          <div>
            <div class="kicker">Method Catalog</div>
            <p id="methodCount">等待目录加载</p>
          </div>
          <label class="field" style="margin:0;min-width:240px"><span>搜索</span><input id="methodSearch" placeholder="输入方法名、家族或目标" /></label>
        </div>
        <div class="filter-rail">
          <label class="field" style="margin:0"><span>家族过滤</span><select id="familyFilter"><option value="">全部家族</option></select></label>
          <label class="field" style="margin:0"><span>视图范围</span><select id="scopeFilter"><option value="all">全部方法</option><option value="queued">只看候选队列</option></select></label>
          <button class="button" id="queueVisibleBtn" type="button">把当前可见加入队列</button>
          <button class="button" id="clearFiltersBtn" type="button">清空筛选</button>
        </div>
        <div id="methodList" class="method-grid"></div>
        <div class="actions" style="margin-top:14px">
          <button class="button" id="loadMoreMethodsBtn" type="button" hidden>加载更多方法</button>
        </div>
      </main>
    </div>
  </div>
  <div id="operationDock" class="operation-dock" aria-live="polite">
    <div class="dock-copy">
      <strong id="dockTitle">还没有选择方法</strong>
      <span id="dockMeta">点击任意卡片选中；双击或 Enter 打开编辑。</span>
    </div>
    <div class="dock-actions">
      <button class="button button-primary" id="dockEditBtn" type="button">编辑 <span class="shortcut">Enter</span></button>
      <button class="button" id="dockRunBtn" type="button">执行 <span class="shortcut">Ctrl+Enter</span></button>
    </div>
  </div>
  <div id="operationToast" class="operation-toast" role="status" aria-live="polite"></div>
  <div id="methodEditorModal" class="editor" role="dialog" aria-modal="true" aria-labelledby="methodEditorTitle">
    <section class="editor-panel">
      <div class="editor-head">
        <div>
          <div class="kicker">Selected Method Editor</div>
          <h2 id="methodEditorTitle" class="editor-title">方法编辑</h2>
          <p id="methodEditorCopy">配置字段、变量、运行模式和对象选择。</p>
        </div>
        <button class="button" id="closeMethodEditorBtn" type="button">关闭编辑浮层</button>
      </div>
      <div id="methodEditorBody"></div>
    </section>
  </div>
  <script>
    const fallbackMethods = [
      { id: "descriptive_statistics", name_zh: "描述统计", family_label: "基础统计", goal_zh: "查看字段分布、缺失和基础描述。" },
      { id: "correlation_analysis", name_zh: "相关性分析", family_label: "关系探索", goal_zh: "探索变量之间的线性关系。" },
      { id: "group_comparison", name_zh: "分组对比", family_label: "差异检验", goal_zh: "比较不同分组的关键指标差异。" }
    ];
    const PAGE_SIZE = 80;
    const state = {
      methods: [],
      selectedMethodId: "",
      search: "",
      familyFilter: "",
      scopeFilter: "all",
      visibleLimit: PAGE_SIZE,
      queued: new Set(),
      toastTimer: null
    };
    const $ = (id) => document.getElementById(id);
    function escapeHtml(value) {
      return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
      });
    }
    function methodName(method) {
      return method.name_zh || method.name || method.label || method.id || "method";
    }
    function methodFamily(method) {
      return method.family_label || method.family || method.category || method.source || "catalog";
    }
    function methodGoal(method) {
      return method.goal_zh || method.goal || method.description || method.summary || "";
    }
    function normalizeMethods(payload) {
      const raw = Array.isArray(payload) ? payload
        : Array.isArray(payload.methods) ? payload.methods
        : Array.isArray(payload.items) ? payload.items
        : Array.isArray(payload.catalog) ? payload.catalog
        : [];
      return raw.map(function (item, index) {
        return Object.assign({}, item, {
          id: String(item.id || item.method_id || item.analysis_type || "method_" + index)
        });
      }).filter(function (item) { return item.id; });
    }
    function setStatus(message, isError) {
      $("status").textContent = message;
      $("status").classList.toggle("error", Boolean(isError));
    }
    function showToast(message) {
      const toast = $("operationToast");
      toast.textContent = message;
      toast.classList.add("show");
      window.clearTimeout(state.toastTimer);
      state.toastTimer = window.setTimeout(function () {
        toast.classList.remove("show");
      }, 1800);
    }
    function filteredMethods() {
      const term = state.search.trim().toLowerCase();
      return state.methods.filter(function (method) {
        if (state.familyFilter && methodFamily(method) !== state.familyFilter) return false;
        if (state.scopeFilter === "queued" && !state.queued.has(method.id)) return false;
        if (!term) return true;
        return [method.id, methodName(method), methodFamily(method), methodGoal(method)].join(" ").toLowerCase().includes(term);
      });
    }
    function visibleMethods() {
      return filteredMethods().slice(0, state.visibleLimit);
    }
    function renderFamilyFilter() {
      const select = $("familyFilter");
      const families = Array.from(new Set(state.methods.map(methodFamily).filter(Boolean))).sort();
      const current = state.familyFilter;
      select.innerHTML = '<option value="">全部家族</option>' + families.map(function (family) {
        return '<option value="' + escapeHtml(family) + '">' + escapeHtml(family) + '</option>';
      }).join("");
      select.value = families.includes(current) ? current : "";
      state.familyFilter = select.value;
    }
    function renderQueue() {
      const queuedMethods = state.methods.filter(function (method) { return state.queued.has(method.id); });
      $("queueSummary").textContent = queuedMethods.length ? queuedMethods.length + " 个候选方法" : "候选队列为空";
      $("queueList").innerHTML = queuedMethods.slice(0, 12).map(function (method) {
        return '<div class="queue-item"><div><strong>' + escapeHtml(methodName(method)) + '</strong><span>' + escapeHtml(method.id) + '</span></div><button class="chip" type="button" data-remove-queue="' + escapeHtml(method.id) + '">移出</button></div>';
      }).join("") || '<p class="empty-note">把常用方法加入候选队列，后续可以只看候选或复制 ID。</p>';
      document.querySelectorAll("[data-remove-queue]").forEach(function (button) {
        button.addEventListener("click", function () {
          toggleQueue(button.getAttribute("data-remove-queue"), false);
        });
      });
    }
    function renderMethods() {
      const allMethods = filteredMethods();
      const methods = allMethods.slice(0, state.visibleLimit);
      const loadMoreButton = $("loadMoreMethodsBtn");
      $("methodCount").textContent = methods.length + " / " + allMethods.length + " 个方法可见";
      loadMoreButton.hidden = methods.length >= allMethods.length;
      loadMoreButton.textContent = "加载更多方法（还有 " + Math.max(0, allMethods.length - methods.length) + " 个）";
      $("methodList").innerHTML = methods.map(function (method) {
        const active = state.selectedMethodId === method.id;
        const queued = state.queued.has(method.id);
        return '<article class="method-card ' + (active ? "active " : "") + (queued ? "queued" : "") + '" tabindex="0" data-method-card="' + escapeHtml(method.id) + '" aria-selected="' + (active ? "true" : "false") + '">' +
          '<div class="method-head"><div><div class="kicker">' + escapeHtml(methodFamily(method)) + '</div>' +
          '<h3 class="method-title">' + escapeHtml(methodName(method)) + '</h3></div>' +
          '<span class="chip">' + escapeHtml(method.source || "catalog") + '</span></div>' +
          '<p class="method-desc">' + escapeHtml(methodGoal(method)) + '</p>' +
          '<div class="method-meta">' +
          '<button class="chip chip-primary" type="button" data-open-method="' + escapeHtml(method.id) + '">选择 / 编辑</button>' +
          '<button class="chip" type="button" data-edit-method="' + escapeHtml(method.id) + '">编辑</button>' +
          '<button class="chip queue-mark" type="button" data-toggle-queue="' + escapeHtml(method.id) + '">' + (queued ? "移出候选" : "加入候选") + '</button>' +
          '<button class="chip" type="button" data-copy-method="' + escapeHtml(method.id) + '">复制 ID</button>' +
          '</div></article>';
      }).join("") || '<p class="status">没有匹配的方法。</p>';
      document.querySelectorAll("[data-open-method],[data-edit-method]").forEach(function (button) {
        button.addEventListener("click", function (event) {
          event.stopPropagation();
          openMethodEditor(button.getAttribute("data-open-method") || button.getAttribute("data-edit-method"));
        });
      });
      document.querySelectorAll("[data-method-card]").forEach(function (card) {
        const methodId = card.getAttribute("data-method-card");
        card.addEventListener("click", function () {
          selectMethod(methodId, true);
        });
        card.addEventListener("dblclick", function () {
          openMethodEditor(methodId);
        });
        card.addEventListener("keydown", function (event) {
          if (event.key === "Enter") {
            event.preventDefault();
            openMethodEditor(methodId);
          }
        });
      });
      document.querySelectorAll("[data-toggle-queue]").forEach(function (button) {
        button.addEventListener("click", function (event) {
          event.stopPropagation();
          toggleQueue(button.getAttribute("data-toggle-queue"));
        });
      });
      document.querySelectorAll("[data-copy-method]").forEach(function (button) {
        button.addEventListener("click", function (event) {
          event.stopPropagation();
          copyText(button.getAttribute("data-copy-method") || "");
        });
      });
      renderQueue();
      renderOperationDock();
    }
    function toggleQueue(methodId, nextValue) {
      if (!methodId) return;
      const shouldQueue = typeof nextValue === "boolean" ? nextValue : !state.queued.has(methodId);
      if (shouldQueue) state.queued.add(methodId);
      else state.queued.delete(methodId);
      renderMethods();
      showToast(shouldQueue ? "已加入候选队列" : "已移出候选队列");
    }
    async function copyText(text) {
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        showToast("已复制到剪贴板");
      } catch (error) {
        showToast("复制失败，请手动复制");
      }
    }
    function renderOperationDock() {
      const method = state.selectedMethodId
        ? state.methods.find(function (item) { return item.id === state.selectedMethodId; })
        : null;
      const dock = $("operationDock");
      if (!method) {
        dock.classList.remove("show");
        return;
      }
      $("dockTitle").textContent = methodName(method);
      $("dockMeta").textContent = methodFamily(method) + " · " + (method.id || "method");
      dock.classList.add("show");
    }
    function selectMethod(methodId, announce) {
      if (!methodId || state.selectedMethodId === methodId) {
        if (announce && methodId) showToast("已选中当前方法");
        return;
      }
      state.selectedMethodId = methodId;
      renderMethods();
      const card = document.querySelector('[data-method-card="' + CSS.escape(methodId) + '"]');
      if (card) {
        card.classList.add("bump");
        card.scrollIntoView({ block: "nearest", behavior: "smooth" });
        window.setTimeout(function () { card.classList.remove("bump"); }, 240);
      }
      if (announce) showToast("已选中：" + methodName(selectedMethod()));
    }
    function selectedMethod() {
      return state.methods.find(function (method) { return method.id === state.selectedMethodId; }) || state.methods[0] || null;
    }
    function ensureSelection() {
      if (!state.selectedMethodId && state.methods[0]) {
        selectMethod(state.methods[0].id, true);
      }
      return selectedMethod();
    }
    function visibleMethodIds() {
      return filteredMethods().slice(0, state.visibleLimit).map(function (method) { return method.id; });
    }
    function moveSelection(delta) {
      const ids = visibleMethodIds();
      if (!ids.length) return;
      const currentIndex = Math.max(0, ids.indexOf(state.selectedMethodId));
      const nextIndex = Math.min(ids.length - 1, Math.max(0, currentIndex + delta));
      selectMethod(ids[nextIndex], true);
      const card = document.querySelector('[data-method-card="' + CSS.escape(ids[nextIndex]) + '"]');
      if (card) card.focus({ preventScroll: true });
    }
    function openMethodEditor(methodId) {
      if (methodId) selectMethod(methodId, false);
      const method = selectedMethod();
      if (!method) {
        setStatus("方法目录还没有加载完成。", true);
        return;
      }
      $("methodEditorTitle").textContent = methodName(method);
      $("methodEditorCopy").textContent = "点击已收到。这里现在是独立编辑浮层，可以调整运行字段后再执行。";
      $("methodEditorBody").innerHTML =
        '<div class="editor-grid">' +
        '<label class="field"><span>目标字段</span><input id="editorTargetColumn" value="' + escapeHtml($("targetColumn").value) + '" /></label>' +
        '<label class="field"><span>特征字段</span><input id="editorFeatureColumns" value="' + escapeHtml($("featureColumns").value) + '" /></label>' +
        '<label class="field"><span>分组字段</span><input id="editorGroupColumn" value="' + escapeHtml($("groupColumn").value) + '" /></label>' +
        '</div>' +
        '<label class="field"><span>执行说明</span><textarea id="editorWorkspaceBrief">' + escapeHtml($("workspaceBrief").value) + '</textarea></label>' +
        '<div class="status"><strong>' + escapeHtml(methodFamily(method)) + '</strong><br />' + escapeHtml(methodGoal(method) || method.id) + '<br /><code>' + escapeHtml(method.id) + '</code></div>' +
        '<div class="actions" style="margin-top:14px"><button class="button button-primary" id="editorApplyBtn" type="button">保存配置</button><button class="button" id="editorRunBtn" type="button">执行这个方法</button></div>';
      $("editorApplyBtn").addEventListener("click", syncEditorFields);
      $("editorRunBtn").addEventListener("click", function () {
        syncEditorFields();
        runMethod(method);
      });
      $("methodEditorModal").classList.add("open");
      showToast("编辑面板已打开");
      renderMethods();
    }
    function syncEditorFields() {
      $("targetColumn").value = $("editorTargetColumn").value;
      $("featureColumns").value = $("editorFeatureColumns").value;
      $("groupColumn").value = $("editorGroupColumn").value;
      $("workspaceBrief").value = $("editorWorkspaceBrief").value;
      setStatus("已保存当前方法配置。", false);
      showToast("配置已保存");
    }
    function closeMethodEditor() {
      $("methodEditorModal").classList.remove("open");
      showToast("编辑面板已关闭");
    }
    function splitColumns(value) {
      return value.split(",").map(function (part) { return part.trim(); }).filter(Boolean);
    }
    async function runMethod(method) {
      setStatus("正在提交 " + methodName(method) + "...", false);
      const response = await fetch("/api/lab/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis_type: method.id,
          method_id: method.id,
          target: $("targetColumn").value.trim() || null,
          features: splitColumns($("featureColumns").value),
          group: $("groupColumn").value.trim() || null,
          user_goal: $("workspaceBrief").value.trim()
        })
      });
      if (!response.ok) throw new Error("执行接口返回 " + response.status);
      setStatus("方法已提交，接口返回成功。", false);
      showToast("方法已提交");
    }
    async function loadMethods() {
      setStatus("正在加载方法目录...", false);
      try {
        const response = await fetch("/api/lab/methods");
        if (!response.ok) throw new Error("目录接口返回 " + response.status);
        const payload = await response.json();
        state.methods = normalizeMethods(payload);
        state.visibleLimit = PAGE_SIZE;
        if (!state.methods.length) throw new Error("目录为空");
        setStatus("方法目录已加载。", false);
      } catch (error) {
        state.methods = fallbackMethods;
        state.visibleLimit = PAGE_SIZE;
        setStatus("方法目录暂不可用，已显示本地兜底方法；点击仍会打开编辑浮层。", true);
      }
      renderMethods();
    }
    $("methodSearch").addEventListener("input", function (event) {
      state.search = event.target.value;
      state.visibleLimit = PAGE_SIZE;
      renderMethods();
    });
    $("loadMoreMethodsBtn").addEventListener("click", function () {
      state.visibleLimit += PAGE_SIZE;
      renderMethods();
      showToast("已追加一批方法");
    });
    $("refreshMethodsBtn").addEventListener("click", loadMethods);
    $("dockEditBtn").addEventListener("click", function () {
      const method = ensureSelection();
      if (method) openMethodEditor(method.id);
    });
    $("dockRunBtn").addEventListener("click", function () {
      const method = ensureSelection();
      if (method) runMethod(method).catch(function (error) {
        setStatus(error.message || "执行失败。", true);
        showToast("执行失败");
      });
    });
    $("closeMethodEditorBtn").addEventListener("click", closeMethodEditor);
    $("methodEditorModal").addEventListener("click", function (event) {
      if (event.target === $("methodEditorModal")) closeMethodEditor();
    });
    document.addEventListener("keydown", function (event) {
      const tagName = document.activeElement && document.activeElement.tagName;
      const isTyping = tagName === "INPUT" || tagName === "TEXTAREA";
      const modalOpen = $("methodEditorModal").classList.contains("open");
      if (event.key === "Escape" && modalOpen) {
        event.preventDefault();
        closeMethodEditor();
        return;
      }
      if (isTyping) return;
      if (event.key === "/") {
        event.preventDefault();
        $("methodSearch").focus();
        showToast("已聚焦搜索");
        return;
      }
      if (event.key === "j" || event.key === "ArrowDown") {
        event.preventDefault();
        moveSelection(1);
        return;
      }
      if (event.key === "k" || event.key === "ArrowUp") {
        event.preventDefault();
        moveSelection(-1);
        return;
      }
      if (event.key === "Enter" && event.ctrlKey) {
        const method = ensureSelection();
        if (method) {
          event.preventDefault();
          runMethod(method).catch(function (error) {
            setStatus(error.message || "执行失败。", true);
            showToast("执行失败");
          });
        }
        return;
      }
      if (event.key === "Enter") {
        const method = ensureSelection();
        if (method) {
          event.preventDefault();
          openMethodEditor(method.id);
        }
      }
    });
    loadMethods();
  </script>
</body>
</html>`;
}

function completeLabWorkspaceHtml() {
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Asteria Lab 数据理解工作台</title>
  <style>
    :root{color-scheme:dark;--bg:#050806;--panel:rgba(9,16,18,.92);--line:rgba(255,255,255,.14);--soft:rgba(255,255,255,.06);--text:#f6efe2;--muted:#aab5c1;--warm:#ff9c61;--cool:#74d0d9;--green:#9ee6a8;--danger:#ff8a8a}
    *{box-sizing:border-box}
    body{margin:0;min-height:100vh;background:radial-gradient(circle at 12% 8%,rgba(255,156,97,.22),transparent 28%),radial-gradient(circle at 88% 12%,rgba(116,208,217,.20),transparent 30%),linear-gradient(180deg,#040708,#091114 58%,#050806);color:var(--text);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
    .shell{width:min(1440px,calc(100vw - 28px));margin:0 auto;padding:22px 0 44px}
    .hero,.panel,.card,.modal-panel{border:1px solid var(--line);border-radius:28px;background:var(--panel);box-shadow:0 28px 90px rgba(0,0,0,.42);backdrop-filter:blur(18px)}
    .hero{padding:24px;display:flex;gap:18px;align-items:flex-end;justify-content:space-between;flex-wrap:wrap}
    .kicker{font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:var(--muted)}
    h1{margin:8px 0 0;font-size:clamp(34px,6vw,64px);line-height:.92;letter-spacing:-.06em}
    h2,h3,p{margin-top:0}
    p{color:var(--muted);line-height:1.7}
    .layout{display:grid;grid-template-columns:340px minmax(0,1fr) 360px;gap:14px;margin-top:14px;align-items:start}
    @media (max-width:1180px){.layout{grid-template-columns:1fr}.sticky{position:static!important}}
    .panel{padding:18px}
    .sticky{position:sticky;top:14px}
    .section{padding:14px;border:1px solid rgba(255,255,255,.10);border-radius:22px;background:rgba(255,255,255,.045);margin-top:12px}
    .field{display:grid;gap:8px;margin-top:12px}
    .field span{font-size:12px;color:var(--muted)}
    input,textarea,select{width:100%;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.07);color:var(--text);padding:11px 12px;font:inherit;outline:none}
    textarea{min-height:94px;resize:vertical}
    select option{background:#081114;color:var(--text)}
    input:focus,textarea:focus,select:focus{border-color:rgba(116,208,217,.74);box-shadow:0 0 0 4px rgba(116,208,217,.12)}
    .button,.chip{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:38px;padding:0 13px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.07);color:var(--text);font-weight:750;text-decoration:none;cursor:pointer;transition:transform .16s ease,border-color .16s ease,background .16s ease,box-shadow .16s ease}
    .button:hover,.chip:hover{border-color:rgba(116,208,217,.55);background:rgba(116,208,217,.12)}
    .button:active,.chip:active{transform:translateY(1px) scale(.98)}
    .button-primary,.chip-primary{border:0;color:#081018;background:linear-gradient(135deg,var(--warm),var(--cool))}
    .actions{display:flex;flex-wrap:wrap;gap:9px}
    .dropzone{display:grid;gap:8px;padding:15px;border:1px dashed rgba(116,208,217,.50);border-radius:22px;background:rgba(116,208,217,.07);cursor:pointer}
    .hidden-input{position:absolute;inline-size:1px;block-size:1px;opacity:0;pointer-events:none}
    .file-name{font-size:18px;font-weight:850}
    .metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}
    .metric{padding:10px;border:1px solid rgba(255,255,255,.12);border-radius:16px;background:rgba(0,0,0,.18)}
    .metric .label{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
    .metric .value{margin-top:3px;font-size:18px;font-weight:850}
    .status{margin-top:12px;padding:11px 13px;border-radius:18px;background:rgba(255,255,255,.07);color:var(--muted)}
    .status.error{color:#ffd6d6;border:1px solid rgba(255,138,138,.34);background:rgba(255,138,138,.12)}
    .status.good{color:#d8ffdf;border:1px solid rgba(158,230,168,.28);background:rgba(158,230,168,.10)}
    .role-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
    @media (max-width:760px){.role-grid{grid-template-columns:1fr}}
    .role-box{padding:12px;border:1px solid rgba(255,255,255,.12);border-radius:18px;background:rgba(0,0,0,.15)}
    .role-box strong{display:block;margin-bottom:8px}
    .tag-list{display:flex;flex-wrap:wrap;gap:7px;min-height:30px}
    .tag{display:inline-flex;align-items:center;gap:6px;max-width:100%;padding:6px 9px;border-radius:999px;background:rgba(116,208,217,.13);border:1px solid rgba(116,208,217,.28);font-size:12px}
    .tag button{border:0;background:transparent;color:var(--text);cursor:pointer}
    .filters{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr) minmax(0,1fr);gap:9px;margin:12px 0}
    @media (max-width:760px){.filters{grid-template-columns:1fr}}
    .field-grid{display:grid;gap:10px;max-height:760px;overflow:auto;padding-right:3px}
    .field-card{padding:13px;border:1px solid rgba(255,255,255,.12);border-radius:20px;background:rgba(255,255,255,.045)}
    .field-card.assigned{border-color:rgba(116,208,217,.45);background:rgba(116,208,217,.08)}
    .field-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
    .field-title{font-weight:850;word-break:break-word}
    .field-meta{display:flex;flex-wrap:wrap;gap:7px;margin-top:8px;color:var(--muted);font-size:12px}
    .sample{margin-top:8px;color:#dbe6e3;font-size:12px;line-height:1.55}
    .method-grid{display:grid;gap:10px;max-height:420px;overflow:auto;padding-right:3px}
    .method-card{padding:13px;border:1px solid rgba(255,255,255,.12);border-radius:20px;background:rgba(255,255,255,.045);cursor:pointer}
    .method-card.active{border-color:rgba(116,208,217,.70);background:rgba(116,208,217,.11)}
    .insight-list{display:grid;gap:9px;margin-top:10px}
    .insight{padding:10px 11px;border:1px solid rgba(255,255,255,.12);border-radius:16px;background:rgba(0,0,0,.16);color:var(--muted);line-height:1.55}
    .insight strong{color:var(--text)}
    .business-pill{display:inline-flex;margin:5px 6px 0 0;padding:6px 9px;border-radius:999px;background:rgba(255,156,97,.12);border:1px solid rgba(255,156,97,.26);font-size:12px}
    .modal{position:fixed;inset:0;z-index:30;display:none;align-items:flex-start;justify-content:center;overflow:auto;background:rgba(0,0,0,.76);padding:30px 14px}
    .modal.open{display:flex}
    .modal-panel{width:min(980px,100%);padding:20px;animation:panel-in .2s ease both}
    @keyframes panel-in{from{opacity:0;transform:translateY(12px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)}}
    .toast{position:fixed;right:20px;bottom:22px;z-index:40;max-width:min(380px,calc(100vw - 40px));padding:12px 14px;border:1px solid rgba(255,255,255,.16);border-radius:18px;background:rgba(6,12,14,.94);opacity:0;transform:translateY(12px);pointer-events:none;transition:opacity .18s ease,transform .18s ease}
    .toast.show{opacity:1;transform:translateY(0)}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div>
        <div class="kicker">Asteria Lab</div>
        <h1>数据理解工作台</h1>
        <p>先理解数据和业务背景，再浏览字段、清洗、选择目标/特征/分组字段，最后运行分析方法。字段不会被默认塞进任何角色。</p>
      </div>
      <div class="actions">
        <a class="button" href="/">返回首页</a>
        <a class="button" href="/analysis">正式分析</a>
        <button class="button button-primary" id="smartUnderstandBtn" type="button">智能理解数据</button>
      </div>
    </section>
    <div class="layout">
      <aside class="panel sticky">
        <div class="kicker">Step 1 · 数据进入</div>
        <label class="dropzone">
          <input id="datasetFile" class="hidden-input" type="file" accept=".xlsx,.xls,.csv,.tsv,.dta" />
          <span class="file-name" id="datasetFileName">选择待分析的数据文件</span>
          <span class="status">支持 CSV / TSV / DTA / XLS / XLSX。上传后会自动读取字段、类型、缺失和样例。</span>
        </label>
        <div class="actions" style="margin-top:12px">
          <button class="button button-primary" id="uploadBtn" type="button">上传数据</button>
          <button class="button" id="refreshDatasetsBtn" type="button">刷新数据集</button>
        </div>
        <label class="field"><span>选择已有数据集</span><select id="datasetSelect"><option value="">正在加载数据集...</option></select></label>
        <label class="field"><span>选择工作表</span><select id="sheetSelect"><option value="">默认工作表</option></select></label>
        <div class="metric-grid">
          <div class="metric"><div class="label">Rows</div><div class="value" id="rowsMetric">0</div></div>
          <div class="metric"><div class="label">Columns</div><div class="value" id="columnsMetric">0</div></div>
          <div class="metric"><div class="label">Numeric</div><div class="value" id="numericMetric">0</div></div>
          <div class="metric"><div class="label">Missing</div><div class="value" id="missingMetric">0</div></div>
        </div>
        <div id="status" class="status">准备加载数据集。</div>
        <section class="section">
          <div class="kicker">Step 2 · 业务背景判断</div>
          <label class="field"><span>业务背景/分析目的</span><textarea id="businessGoal" placeholder="例如：这是电商订单数据，希望分析 GMV、转化、渠道、复购或异常。"></textarea></label>
          <div id="businessBox" class="insight-list"></div>
        </section>
      </aside>
      <main class="panel">
        <div class="kicker">Step 3 · 字段浏览与角色选择</div>
        <p>先浏览字段，再显式选择目标字段、特征字段、分组字段。未选择的字段保持“未分配”，不会自动变成三类之一。</p>
        <section class="section">
          <div class="role-grid">
            <div class="role-box"><strong>目标字段</strong><div id="targetRole" class="tag-list"><span class="status">未选择</span></div></div>
            <div class="role-box"><strong>特征字段</strong><div id="featureRole" class="tag-list"><span class="status">未选择</span></div></div>
            <div class="role-box"><strong>分组字段</strong><div id="groupRole" class="tag-list"><span class="status">未选择</span></div></div>
          </div>
          <div class="actions" style="margin-top:12px">
            <button class="button" id="applySuggestionsBtn" type="button">应用智能字段建议</button>
            <button class="button" id="clearRolesBtn" type="button">清空字段选择</button>
          </div>
        </section>
        <div class="filters">
          <label class="field"><span>搜索字段</span><input id="fieldSearch" placeholder="字段名 / 类型 / 样例" /></label>
          <label class="field"><span>字段类型</span><select id="fieldTypeFilter"><option value="">全部字段</option><option value="numeric">数值字段</option><option value="categorical">分类字段</option><option value="datetime">时间字段</option><option value="missing">有缺失字段</option><option value="unassigned">未分配字段</option></select></label>
          <label class="field"><span>方法搜索</span><input id="methodSearch" placeholder="搜索分析方法" /></label>
        </div>
        <div id="fieldList" class="field-grid"><p class="status">请选择或上传数据集后浏览字段。</p></div>
      </main>
      <aside class="panel sticky">
        <section>
          <div class="kicker">Step 4 · 智能理解与清洗</div>
          <div class="actions">
            <button class="button button-primary" id="smartCleanBtn" type="button">运行清洗/派生</button>
            <button class="button" id="refreshMethodsBtn" type="button">刷新方法</button>
          </div>
          <div id="understandingBox" class="insight-list"></div>
          <div id="cleaningBox" class="insight-list"></div>
        </section>
        <section class="section">
          <div class="kicker">Step 5 · 选择方法执行</div>
          <p id="methodCount">等待方法目录加载</p>
          <div id="methodList" class="method-grid"></div>
          <div class="actions" style="margin-top:12px">
            <button class="button" id="loadMoreMethodsBtn" type="button" hidden>加载更多方法</button>
          </div>
        </section>
      </aside>
    </div>
  </div>
  <div id="methodModal" class="modal" role="dialog" aria-modal="true">
    <section class="modal-panel">
      <div style="display:flex;justify-content:space-between;gap:14px;align-items:flex-start">
        <div>
          <div class="kicker">Method Run</div>
          <h2 id="modalTitle">方法配置</h2>
          <p id="modalCopy">运行前会携带当前数据集、sheet、业务背景和你显式选择的字段角色。</p>
        </div>
        <button class="button" id="closeModalBtn" type="button">关闭</button>
      </div>
      <div id="modalBody"></div>
    </section>
  </div>
  <div id="toast" class="toast" role="status" aria-live="polite"></div>
  <script>
    const PAGE_SIZE = 60;
    const state = {
      datasets: [],
      dataset: null,
      selectedDatasetId: "",
      selectedSheet: "",
      selectedFile: null,
      methods: [],
      selectedMethodId: "",
      methodLimit: PAGE_SIZE,
      target: "",
      features: new Set(),
      group: "",
      fieldSearch: "",
      fieldTypeFilter: "",
      methodSearch: "",
      suggestions: { target: "", features: [], group: "" },
      toastTimer: null
    };
    const $ = (id) => document.getElementById(id);
    function escapeHtml(value) {
      return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
      });
    }
    function api(url, options) {
      return fetch(url, options).then(function (response) {
        if (!response.ok) {
          return response.text().then(function (text) { throw new Error(text || ("HTTP " + response.status)); });
        }
        return response.json();
      });
    }
    function toast(message) {
      $("toast").textContent = message;
      $("toast").classList.add("show");
      window.clearTimeout(state.toastTimer);
      state.toastTimer = window.setTimeout(function () { $("toast").classList.remove("show"); }, 2000);
    }
    function setStatus(message, isError) {
      $("status").textContent = message;
      $("status").classList.toggle("error", Boolean(isError));
      $("status").classList.toggle("good", !isError && Boolean(message));
    }
    function datasetLabel(dataset) {
      if (!dataset) return "未选择数据集";
      return dataset.name || dataset.filename || dataset.dataset_id;
    }
    function columns() {
      return (state.dataset && Array.isArray(state.dataset.column_summaries)) ? state.dataset.column_summaries : [];
    }
    function columnNames(kind) {
      if (!state.dataset) return [];
      if (kind === "numeric") return state.dataset.numeric_columns || [];
      if (kind === "categorical") return state.dataset.categorical_columns || [];
      if (kind === "datetime") return state.dataset.datetime_columns || [];
      return columns().map(function (item) { return item.name; }).filter(Boolean);
    }
    function fieldKind(name, summary) {
      if (columnNames("numeric").includes(name)) return "numeric";
      if (columnNames("datetime").includes(name)) return "datetime";
      if (columnNames("categorical").includes(name)) return "categorical";
      const dtype = String(summary && summary.dtype || "").toLowerCase();
      if (dtype.includes("int") || dtype.includes("float") || dtype.includes("number")) return "numeric";
      if (dtype.includes("date") || dtype.includes("time")) return "datetime";
      return "text";
    }
    function roleOf(name) {
      if (state.target === name) return "target";
      if (state.group === name) return "group";
      if (state.features.has(name)) return "feature";
      return "";
    }
    function setRole(name, role) {
      if (!name) return;
      if (state.target === name) state.target = "";
      if (state.group === name) state.group = "";
      state.features.delete(name);
      if (role === "target") state.target = name;
      if (role === "group") state.group = name;
      if (role === "feature") state.features.add(name);
      renderRoles();
      renderFields();
      toast(role ? "已设置字段角色" : "已取消字段角色");
    }
    function removeFeature(name) {
      state.features.delete(name);
      renderRoles();
      renderFields();
    }
    function renderRoles() {
      $("targetRole").innerHTML = state.target ? '<span class="tag">' + escapeHtml(state.target) + '<button type="button" data-clear-role="target">×</button></span>' : '<span class="status">未选择</span>';
      $("groupRole").innerHTML = state.group ? '<span class="tag">' + escapeHtml(state.group) + '<button type="button" data-clear-role="group">×</button></span>' : '<span class="status">未选择</span>';
      const features = Array.from(state.features);
      $("featureRole").innerHTML = features.length ? features.map(function (name) {
        return '<span class="tag">' + escapeHtml(name) + '<button type="button" data-remove-feature="' + escapeHtml(name) + '">×</button></span>';
      }).join("") : '<span class="status">未选择</span>';
      document.querySelectorAll("[data-clear-role]").forEach(function (button) {
        button.addEventListener("click", function () {
          if (button.getAttribute("data-clear-role") === "target") state.target = "";
          if (button.getAttribute("data-clear-role") === "group") state.group = "";
          renderRoles();
          renderFields();
        });
      });
      document.querySelectorAll("[data-remove-feature]").forEach(function (button) {
        button.addEventListener("click", function () { removeFeature(button.getAttribute("data-remove-feature")); });
      });
    }
    function inferSuggestions() {
      const all = columns();
      const numeric = columnNames("numeric");
      const categorical = columnNames("categorical");
      const lowerScore = function (name) {
        const text = String(name || "").toLowerCase();
        let score = 0;
        ["销售","金额","收入","gmv","revenue","sales","profit","利润","成本","cost","数量","count","price","价格","score"].forEach(function (token) {
          if (text.includes(token)) score += 3;
        });
        ["id","编号","name","名称","日期","date","time"].forEach(function (token) {
          if (text.includes(token)) score -= 2;
        });
        return score;
      };
      const target = numeric.slice().sort(function (a, b) { return lowerScore(b) - lowerScore(a); })[0] || "";
      const group = categorical.find(function (name) { return /渠道|地区|城市|品类|类别|部门|门店|客户|用户|group|category|channel|city|region/i.test(name); }) || categorical[0] || "";
      const features = all.map(function (item) { return item.name; }).filter(function (name) {
        return name && name !== target && name !== group;
      }).slice(0, 8);
      state.suggestions = { target: target, features: features, group: group };
    }
    function inferBusiness() {
      const text = [datasetLabel(state.dataset), $("businessGoal").value, columnNames().join(" ")].join(" ").toLowerCase();
      const profiles = [
        ["电商/商品运营", ["gmv","订单","商品","sku","转化","复购","客单","品类","ecommerce","order","product"]],
        ["采购销售/供应链", ["采购","供应商","库存","入库","出库","成本","销售","supplier","inventory","procurement"]],
        ["互联网运营", ["用户","活跃","留存","渠道","点击","曝光","转化","uv","pv","retention","click"]],
        ["媒体投放", ["投放","广告","曝光","点击","ctr","cpc","campaign","media","ad"]]
      ];
      let best = ["通用业务数据", 0, []];
      profiles.forEach(function (profile) {
        const hits = profile[1].filter(function (token) { return text.includes(token); });
        if (hits.length > best[1]) best = [profile[0], hits.length, hits];
      });
      return { label: best[0], confidence: Math.min(0.95, 0.35 + best[1] * 0.12), evidence: best[2] };
    }
    function renderUnderstanding() {
      if (!state.dataset) {
        $("understandingBox").innerHTML = '<div class="insight">请选择或上传数据集后再进行智能理解。</div>';
        $("cleaningBox").innerHTML = "";
        $("businessBox").innerHTML = "";
        return;
      }
      inferSuggestions();
      const missing = Number(state.dataset.missing_cells || 0);
      const rowCount = Number(state.dataset.row_count || 0);
      const colCount = Number(state.dataset.column_count || 0);
      const missingRatio = rowCount && colCount ? missing / (rowCount * colCount) : 0;
      const highMissing = columns().filter(function (item) { return Number(item.missing_ratio || 0) >= 0.2; });
      const business = inferBusiness();
      $("understandingBox").innerHTML =
        '<div class="insight"><strong>数据结构：</strong>' + rowCount + ' 行，' + colCount + ' 列；数值字段 ' + columnNames("numeric").length + ' 个，分类字段 ' + columnNames("categorical").length + ' 个，时间字段 ' + columnNames("datetime").length + ' 个。</div>' +
        '<div class="insight"><strong>智能字段建议：</strong>目标字段建议为 ' + escapeHtml(state.suggestions.target || "暂无") + '；分组字段建议为 ' + escapeHtml(state.suggestions.group || "暂无") + '；特征字段建议 ' + state.suggestions.features.length + ' 个。建议不会自动应用，除非你点击“应用智能字段建议”。</div>';
      $("cleaningBox").innerHTML =
        '<div class="insight"><strong>清洗判断：</strong>缺失单元格 ' + missing + '，约 ' + Math.round(missingRatio * 10000) / 100 + '%。</div>' +
        '<div class="insight"><strong>清洗建议：</strong>' + (highMissing.length ? '优先检查高缺失字段：' + highMissing.slice(0, 6).map(function (item) { return escapeHtml(item.name); }).join("、") : '缺失比例未发现明显异常；可继续检查字段类型和异常值。') + '</div>';
      $("businessBox").innerHTML =
        '<div class="insight"><strong>业务背景判断：</strong>' + escapeHtml(business.label) + '，置信度 ' + Math.round(business.confidence * 100) + '%。</div>' +
        '<div>' + (business.evidence.length ? business.evidence.map(function (item) { return '<span class="business-pill">' + escapeHtml(item) + '</span>'; }).join("") : '<span class="business-pill">证据不足，请补充业务背景</span>') + '</div>';
    }
    function renderMetrics() {
      const dataset = state.dataset;
      $("rowsMetric").textContent = dataset ? String(dataset.row_count || 0) : "0";
      $("columnsMetric").textContent = dataset ? String(dataset.column_count || 0) : "0";
      $("numericMetric").textContent = dataset ? String((dataset.numeric_columns || []).length) : "0";
      $("missingMetric").textContent = dataset ? String(dataset.missing_cells || 0) : "0";
    }
    function renderDatasetSelect() {
      $("datasetSelect").innerHTML = '<option value="">选择数据集</option>' + state.datasets.map(function (dataset) {
        return '<option value="' + escapeHtml(dataset.dataset_id) + '">' + escapeHtml(datasetLabel(dataset)) + '</option>';
      }).join("");
      $("datasetSelect").value = state.selectedDatasetId || "";
    }
    function renderSheetSelect() {
      const sheets = state.dataset && Array.isArray(state.dataset.sheets) ? state.dataset.sheets : [];
      $("sheetSelect").innerHTML = sheets.length ? sheets.map(function (sheet) {
        return '<option value="' + escapeHtml(sheet.name) + '">' + escapeHtml(sheet.name) + '</option>';
      }).join("") : '<option value="">默认工作表</option>';
      $("sheetSelect").value = state.selectedSheet || (sheets[0] && sheets[0].name) || "";
    }
    function renderFields() {
      const term = state.fieldSearch.trim().toLowerCase();
      let items = columns().filter(function (summary) {
        const name = summary.name || "";
        const kind = fieldKind(name, summary);
        if (state.fieldTypeFilter === "numeric" && kind !== "numeric") return false;
        if (state.fieldTypeFilter === "categorical" && kind !== "categorical") return false;
        if (state.fieldTypeFilter === "datetime" && kind !== "datetime") return false;
        if (state.fieldTypeFilter === "missing" && Number(summary.missing_count || 0) <= 0) return false;
        if (state.fieldTypeFilter === "unassigned" && roleOf(name)) return false;
        if (!term) return true;
        return [name, summary.dtype, (summary.sample_values || []).join(" ")].join(" ").toLowerCase().includes(term);
      });
      $("fieldList").innerHTML = items.map(function (summary) {
        const name = summary.name || "";
        const kind = fieldKind(name, summary);
        const role = roleOf(name);
        const samples = (summary.sample_values || []).slice(0, 4).map(escapeHtml).join("，");
        return '<article class="field-card ' + (role ? "assigned" : "") + '">' +
          '<div class="field-head"><div><div class="field-title">' + escapeHtml(name) + '</div><div class="field-meta"><span>' + escapeHtml(kind) + '</span><span>' + escapeHtml(summary.dtype || "") + '</span><span>缺失 ' + Number(summary.missing_count || 0) + '</span><span>唯一 ' + Number(summary.unique_count || 0) + '</span>' + (role ? '<span>已设为 ' + escapeHtml(role) + '</span>' : '<span>未分配</span>') + '</div></div></div>' +
          '<div class="sample">样例：' + (samples || "暂无") + '</div>' +
          '<div class="actions" style="margin-top:10px">' +
          '<button class="chip chip-primary" type="button" data-role-target="' + escapeHtml(name) + '">设为目标</button>' +
          '<button class="chip" type="button" data-role-feature="' + escapeHtml(name) + '">加入特征</button>' +
          '<button class="chip" type="button" data-role-group="' + escapeHtml(name) + '">设为分组</button>' +
          '<button class="chip" type="button" data-role-clear="' + escapeHtml(name) + '">取消角色</button>' +
          '</div></article>';
      }).join("") || '<p class="status">没有匹配字段。</p>';
      document.querySelectorAll("[data-role-target]").forEach(function (button) { button.addEventListener("click", function () { setRole(button.getAttribute("data-role-target"), "target"); }); });
      document.querySelectorAll("[data-role-feature]").forEach(function (button) { button.addEventListener("click", function () { setRole(button.getAttribute("data-role-feature"), "feature"); }); });
      document.querySelectorAll("[data-role-group]").forEach(function (button) { button.addEventListener("click", function () { setRole(button.getAttribute("data-role-group"), "group"); }); });
      document.querySelectorAll("[data-role-clear]").forEach(function (button) { button.addEventListener("click", function () { setRole(button.getAttribute("data-role-clear"), ""); }); });
    }
    function renderAllData() {
      renderDatasetSelect();
      renderSheetSelect();
      renderMetrics();
      renderRoles();
      renderUnderstanding();
      renderFields();
    }
    async function loadDatasets(preselectId) {
      setStatus("正在加载数据集...", false);
      const payload = await api("/api/datasets");
      state.datasets = payload.datasets || [];
      const selected = preselectId || state.selectedDatasetId || (state.datasets[0] && state.datasets[0].dataset_id) || "";
      if (selected) await loadDatasetDetail(selected);
      else {
        state.dataset = null;
        state.selectedDatasetId = "";
        renderAllData();
        setStatus("还没有数据集，请上传数据。", true);
      }
    }
    async function loadDatasetDetail(datasetId) {
      if (!datasetId) return;
      setStatus("正在读取数据结构...", false);
      const detail = await api("/api/datasets/" + encodeURIComponent(datasetId));
      state.dataset = detail;
      state.selectedDatasetId = detail.dataset_id || datasetId;
      state.selectedSheet = detail.active_sheet || ((detail.sheets || [])[0] && (detail.sheets || [])[0].name) || "";
      state.target = "";
      state.features = new Set();
      state.group = "";
      renderAllData();
      setStatus("数据已读取：" + datasetLabel(detail), false);
    }
    async function uploadDataset() {
      if (!state.selectedFile) throw new Error("请先选择数据文件。");
      const form = new FormData();
      form.append("file", state.selectedFile);
      setStatus("正在上传并解析数据...", false);
      const uploaded = await api("/api/datasets/upload", { method: "POST", body: form });
      await loadDatasets(uploaded.dataset_id);
      toast("数据已进入工作台");
    }
    async function activateSheet(sheetName) {
      if (!state.selectedDatasetId || !sheetName) return;
      await api("/api/datasets/" + encodeURIComponent(state.selectedDatasetId) + "/sheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sheet_name: sheetName })
      });
      await loadDatasetDetail(state.selectedDatasetId);
      toast("工作表已切换");
    }
    function filteredMethods() {
      const term = state.methodSearch.trim().toLowerCase();
      const methods = state.methods || [];
      if (!term) return methods;
      return methods.filter(function (method) {
        return [method.id, method.name, method.name_zh, method.family, method.family_label, method.goal, method.goal_zh].join(" ").toLowerCase().includes(term);
      });
    }
    function methodName(method) {
      return method.name_zh || method.name || method.id || "method";
    }
    function renderMethods() {
      const all = filteredMethods();
      const visible = all.slice(0, state.methodLimit);
      $("methodCount").textContent = visible.length + " / " + all.length + " 个方法可见";
      $("loadMoreMethodsBtn").hidden = visible.length >= all.length;
      $("methodList").innerHTML = visible.map(function (method) {
        const active = state.selectedMethodId === method.id;
        return '<article class="method-card ' + (active ? "active" : "") + '" data-method-id="' + escapeHtml(method.id) + '"><strong>' + escapeHtml(methodName(method)) + '</strong><p>' + escapeHtml(method.goal_zh || method.goal || method.family_label || method.family || "") + '</p><div class="actions"><button class="chip chip-primary" type="button" data-open-method="' + escapeHtml(method.id) + '">配置/运行</button></div></article>';
      }).join("") || '<p class="status">没有匹配的方法。</p>';
      document.querySelectorAll("[data-open-method]").forEach(function (button) {
        button.addEventListener("click", function () {
          openMethodModal(button.getAttribute("data-open-method"));
        });
      });
      document.querySelectorAll("[data-method-id]").forEach(function (card) {
        card.addEventListener("dblclick", function () { openMethodModal(card.getAttribute("data-method-id")); });
      });
    }
    async function loadMethods() {
      const payload = await api("/api/lab/methods");
      state.methods = Array.isArray(payload.methods) ? payload.methods : [];
      state.methodLimit = PAGE_SIZE;
      renderMethods();
    }
    function selectedFieldsPayload() {
      return {
        target: state.target || null,
        features: Array.from(state.features),
        group: state.group || null,
        unassigned_count: Math.max(0, columns().length - (state.target ? 1 : 0) - state.features.size - (state.group ? 1 : 0))
      };
    }
    function requireDataset() {
      if (!state.selectedDatasetId) throw new Error("请先上传或选择数据集。");
    }
    function openMethodModal(methodId) {
      const method = state.methods.find(function (item) { return item.id === methodId; });
      if (!method) return;
      state.selectedMethodId = method.id;
      $("modalTitle").textContent = methodName(method);
      $("modalBody").innerHTML =
        '<div class="section"><div class="kicker">当前运行上下文</div>' +
        '<p>数据集：' + escapeHtml(datasetLabel(state.dataset)) + '</p>' +
        '<p>Sheet：' + escapeHtml(state.selectedSheet || "默认工作表") + '</p>' +
        '<p>目标字段：' + escapeHtml(state.target || "未选择") + '</p>' +
        '<p>特征字段：' + escapeHtml(Array.from(state.features).join("，") || "未选择") + '</p>' +
        '<p>分组字段：' + escapeHtml(state.group || "未选择") + '</p>' +
        '<div class="actions"><button class="button button-primary" id="runMethodBtn" type="button">运行这个方法</button></div></div>';
      $("runMethodBtn").addEventListener("click", function () {
        runMethod(method).catch(function (error) {
          setStatus(error.message || "方法执行失败。", true);
          toast("方法执行失败");
        });
      });
      $("methodModal").classList.add("open");
      renderMethods();
    }
    async function runMethod(method) {
      requireDataset();
      setStatus("正在运行方法：" + methodName(method), false);
      const payload = await api("/api/lab/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: state.selectedDatasetId,
          active_sheet: state.selectedSheet || null,
          user_goal: $("businessGoal").value,
          report_part: "analysis_lab_workspace",
          selected_method_ids: [method.id],
          selected_fields: selectedFieldsPayload(),
          execution_mode: "smart_merge",
          business_interpretation_enabled: true,
          max_methods: 1,
          max_derived_fields: 64,
          max_chart_points: 180
        })
      });
      setStatus("方法已完成：" + methodName(method), false);
      $("modalBody").insertAdjacentHTML("beforeend", '<div class="status good">接口返回成功。已基于当前数据集、业务背景和字段选择执行。</div>');
      toast("方法已完成");
      return payload;
    }
    async function runSmartClean() {
      requireDataset();
      setStatus("正在运行智能清洗、派生和数据理解...", false);
      const payload = await api("/api/analysis/auto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: state.selectedDatasetId,
          active_sheet: state.selectedSheet || null,
          user_goal: $("businessGoal").value,
          report_part: "analysis_lab_workspace",
          selected_fields: selectedFieldsPayload(),
          execution_mode: "smart_merge",
          business_interpretation_enabled: true,
          max_methods: 12,
          max_derived_fields: 64,
          max_chart_points: 180
        })
      });
      $("cleaningBox").insertAdjacentHTML("beforeend", '<div class="insight"><strong>清洗/派生已运行：</strong>后端返回成功，已按当前数据集和字段角色执行。</div>');
      setStatus("智能清洗/派生已完成。", false);
      toast("智能清洗已完成");
      return payload;
    }
    $("datasetFile").addEventListener("change", function (event) {
      const file = event.target.files && event.target.files[0];
      state.selectedFile = file || null;
      $("datasetFileName").textContent = file ? file.name : "选择待分析的数据文件";
    });
    $("uploadBtn").addEventListener("click", function () {
      uploadDataset().catch(function (error) { setStatus(error.message || "上传失败。", true); });
    });
    $("refreshDatasetsBtn").addEventListener("click", function () {
      loadDatasets().catch(function (error) { setStatus(error.message || "刷新数据集失败。", true); });
    });
    $("datasetSelect").addEventListener("change", function (event) {
      loadDatasetDetail(event.target.value).catch(function (error) { setStatus(error.message || "读取数据失败。", true); });
    });
    $("sheetSelect").addEventListener("change", function (event) {
      activateSheet(event.target.value).catch(function (error) { setStatus(error.message || "切换工作表失败。", true); });
    });
    $("businessGoal").addEventListener("input", renderUnderstanding);
    $("smartUnderstandBtn").addEventListener("click", function () { renderUnderstanding(); toast("已完成智能理解"); });
    $("smartCleanBtn").addEventListener("click", function () {
      runSmartClean().catch(function (error) { setStatus(error.message || "智能清洗失败。", true); });
    });
    $("applySuggestionsBtn").addEventListener("click", function () {
      inferSuggestions();
      if (state.suggestions.target) state.target = state.suggestions.target;
      state.group = state.suggestions.group || "";
      state.features = new Set(state.suggestions.features || []);
      renderRoles();
      renderFields();
      toast("已应用智能字段建议");
    });
    $("clearRolesBtn").addEventListener("click", function () {
      state.target = "";
      state.group = "";
      state.features = new Set();
      renderRoles();
      renderFields();
      toast("字段角色已清空");
    });
    $("fieldSearch").addEventListener("input", function (event) { state.fieldSearch = event.target.value; renderFields(); });
    $("fieldTypeFilter").addEventListener("change", function (event) { state.fieldTypeFilter = event.target.value; renderFields(); });
    $("methodSearch").addEventListener("input", function (event) { state.methodSearch = event.target.value; state.methodLimit = PAGE_SIZE; renderMethods(); });
    $("loadMoreMethodsBtn").addEventListener("click", function () { state.methodLimit += PAGE_SIZE; renderMethods(); });
    $("refreshMethodsBtn").addEventListener("click", function () { loadMethods().catch(function (error) { setStatus(error.message || "方法目录加载失败。", true); }); });
    $("closeModalBtn").addEventListener("click", function () { $("methodModal").classList.remove("open"); });
    $("methodModal").addEventListener("click", function (event) { if (event.target === $("methodModal")) $("methodModal").classList.remove("open"); });
    Promise.all([
      loadDatasets().catch(function (error) { setStatus(error.message || "数据集加载失败。", true); }),
      loadMethods().catch(function (error) { setStatus(error.message || "方法目录加载失败。", true); })
    ]);
  </script>
</body>
</html>`;
}

function fallbackPageHtml(kind) {
  if (kind === "lab") {
    if (fs.existsSync(labWorkspaceFile)) {
      return fs.readFileSync(labWorkspaceFile, "utf8");
    }
    return labFallbackPageHtml();
  }
  const isLab = kind === "lab";
  const title = isLab ? "Asteria Lab 方法实验台" : "Asteria 正式分析";
  const headline = isLab ? "Lab 方法实验台" : "正式分析与报告交付";
  const copy = isLab
    ? "Lab 和正式分析已经分开。这里用于选择 2k+ 统计、可视化与报告部件方法，并通过后端 Lab API 执行。"
    : "这里保留正式分析与报告生成链路。需要试验全量方法目录时，请进入 Lab。";
  const primaryHref = isLab ? "/api/lab/methods" : "/lab";
  const primaryLabel = isLab ? "检查 Lab 方法目录 API" : "打开 Lab 方法实验台";
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${title}</title>
  <style>
    :root{color-scheme:dark}
    body{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 16% 10%,rgba(255,156,97,.20),transparent 26%),radial-gradient(circle at 84% 14%,rgba(116,208,217,.18),transparent 28%),#050806;color:#f6efe2;font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
    main{width:min(920px,calc(100vw - 32px));border:1px solid rgba(255,255,255,.12);border-radius:32px;background:rgba(9,14,16,.86);box-shadow:0 28px 80px rgba(0,0,0,.42);padding:34px}
    .kicker{font-size:12px;letter-spacing:.28em;text-transform:uppercase;color:#aab5c1}
    h1{margin:12px 0 0;font-size:clamp(36px,7vw,72px);line-height:.95;letter-spacing:-.06em}
    p{max-width:720px;margin:18px 0 0;color:#aab5c1;font-size:16px;line-height:1.8}
    .actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}
    a{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 18px;border-radius:999px;border:1px solid rgba(255,255,255,.14);color:#f6efe2;text-decoration:none;font-weight:700}
    a.primary{border:0;color:#081018;background:linear-gradient(135deg,#ff9c61,#74d0d9)}
    code{display:block;margin-top:22px;padding:14px 16px;border-radius:18px;background:rgba(255,255,255,.06);color:#dce6e4;overflow:auto}
  </style>
</head>
<body>
  <main>
    <div class="kicker">${isLab ? "Lab Surface" : "Formal Surface"}</div>
    <h1>${headline}</h1>
    <p>${copy}</p>
    <div class="actions">
      <a class="primary" href="${primaryHref}">${primaryLabel}</a>
      <a href="/">返回首页</a>
      <a href="/analysis">正式分析</a>
      <a href="/revision">后续改造</a>
    </div>
    <code>${isLab ? "/api/lab/methods + /api/lab/run" : "/api/datasets/{dataset_id}/smart-report-jobs"}</code>
  </main>
</body>
</html>`;
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${host}:${port}`);

  if (url.pathname === "/health") {
    send(
      res,
      200,
      JSON.stringify({ ok: true, mode: "recovery-proxy", staticRootExists: fs.existsSync(staticRoot) }),
      "application/json; charset=utf-8",
    );
    return;
  }

  if (url.pathname === "/api/skills" || url.pathname === "/api/skills/search" || url.pathname === "/api/skills/install" || url.pathname === "/api/skills/import") {
    handleSkillsApi(req, res, url);
    return;
  }

  if (url.pathname.startsWith("/api/")) {
    proxyApi(req, res);
    return;
  }

  if (url.pathname === "/" || url.pathname === "/index.html") {
    sendStaticFile(res, "index.html", injectHome);
    return;
  }

  if (url.pathname === "/revision" || url.pathname === "/revision/") {
    sendStaticFile(res, "revision.html");
    return;
  }

  if (url.pathname === "/revision/workspace" || url.pathname === "/revision/workspace/") {
    sendStaticFile(res, path.join("revision", "workspace.html"));
    return;
  }

  if (url.pathname === "/lab" || url.pathname === "/lab/") {
    const labHtml = readStaticFile("lab.html");
    send(res, 200, labHtml || fallbackPageHtml("lab"), "text/html; charset=utf-8");
    return;
  }

  if (url.pathname === "/analysis" || url.pathname === "/analysis/") {
    const analysisHtml = readStaticFile("analysis.html") || readStaticFile(path.join("analysis", "index.html"));
    send(res, 200, analysisHtml || fallbackPageHtml("analysis"), "text/html; charset=utf-8");
    return;
  }

  sendStaticFile(res, url.pathname.replace(/^\/+/, ""));
});

server.listen(port, host, () => {
  console.log(`Asteria recovery frontend ready at http://${host}:${port}/ via ${backendBase.href}`);
});
