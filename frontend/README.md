# Asteria Analyst Frontend

This directory contains the Next.js interface for Asteria Analyst: formal analysis, Analysis Lab, method guidance, report revision, and local runtime status.

For the product overview and user-facing workflow, start with the repository [README](../README.md). For local setup, use the root `start-asteria.cmd` launcher or follow [Getting Started](../docs/getting-started.zh-CN.md).

## Development

```powershell
npm ci
npm run dev
```

The frontend normally expects the local backend at `http://127.0.0.1:8000`. The root launcher pairs the frontend with the actual backend port it chooses and is the recommended way to start a complete local environment.

## Required checks

```powershell
npm run lint
npm run verify:method-guide
npm run build
```

Do not add browser-accessible API keys, user-provided code execution, or direct public access to backend storage. The public repository is local-first; multi-user or internet-facing deployment requires a separate security design.
