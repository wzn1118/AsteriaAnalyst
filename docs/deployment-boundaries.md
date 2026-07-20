# Deployment and Public-Use Boundaries

> 中文说明：[安全与部署说明](security-deployment.zh-CN.md)

This repository can be public without becoming a public data service. Asteria Analyst is designed for local, loopback-only, single-user use unless a separate deployment and security design is implemented.

## What "Public" Means Here

Public repository scope includes:

- source code, tests, examples, and launch scripts;
- public architecture and user documentation;
- a Windows portable package when the owner uploads it as a GitHub Release.

Public repository scope does not include:

- customer datasets, uploaded workbooks, generated reports, screenshots, or revision sessions;
- API keys, tokens, passwords, private endpoints, or local environment files;
- private portfolio material, historical delivery artifacts, or unlicensed third-party material;
- a hosted multi-user service.

The repository's `.gitignore` is intentionally structured to keep local data, reports, runtime state, logs, and credentials out of version control. It is still the operator's responsibility to inspect files before committing or uploading a Release asset.

## Local-Only Default

The provided launchers bind the backend and frontend to `127.0.0.1`. This is deliberate:

- it limits normal access to the local machine;
- it avoids treating uploaded data and generated reports as public web content;
- it keeps local API keys and runtime settings outside a shared service boundary.

Do not make the application internet-accessible by only changing a bind address, opening a firewall port, using port forwarding, or placing it behind a reverse proxy. Those actions create a materially different deployment that needs its own design and review.

## AI Provider Data Boundary

Basic CSV/Excel analysis can run locally without an external model provider. When a user explicitly enables AI-assisted reporting or revision, the application can send relevant field context, report context, or workbook/PDF content to the OpenAI-compatible provider configured in that user's local environment.

Before enabling those features, the operator must decide:

1. Whether the provider is authorized to receive the specific data category.
2. Whether personal, customer, financial, health, contract, or regulated fields need to be removed, masked, aggregated, or sampled.
3. Whether provider retention, region, audit, and access policies satisfy organizational requirements.
4. Whether the user understands that an API key only authorizes a provider call; it does not make the data safe to transmit.

Never state that data "never leaves the machine" when AI-assisted provider calls are enabled.

## Secrets and Sensitive Files

Keep secrets in local environment files such as `.env`. Do not place them in:

- source code;
- frontend settings or browser storage;
- Git commits, GitHub Issues, pull requests, release notes, or screenshots;
- exported report bundles, manifests, notebooks, or log files.

The included `.env.example` is a template only. Do not turn it into a real configuration file and commit it.

## If You Need a Shared or Internet-Facing Service

A production multi-user deployment requires a separate threat model and implementation plan. At minimum, it should include:

| Area | Required design work |
| --- | --- |
| Identity | Authenticated users, session management, and account lifecycle |
| Authorization | Per-user or per-tenant access control for data, reports, revisions, and downloads |
| Data isolation | Tenant-aware storage paths, encrypted storage, retention/deletion policy, and backup controls |
| Upload handling | File type/size limits, malware scanning strategy, content validation, and private object storage |
| Browser/API security | CSRF protections, strict CORS, secure headers, rate limits, request validation, and audit logging |
| Secrets | Managed secret storage, rotation, least privilege, and no browser exposure |
| AI providers | Data processing agreements, routing controls, data minimization, provider logging policy, and consent |
| Runtime execution | Sandboxed workloads, resource limits, tenancy isolation, monitoring, and incident response |

The default release disables HTTP code execution and privileged runtime-control APIs. Do not re-enable them for shared users without an explicit security review.

## Release Asset Hygiene

Before publishing a GitHub Release:

1. Check that the source package and portable ZIP contain no `.env`, API keys, uploaded data, reports, logs, caches, local runtime state, or portfolio files.
2. Run the documented smoke checks on a clean machine or clean working directory.
3. Ensure the startup instructions match the actual filenames and supported platform.
4. Publish a version number, release notes, known limitations, and a checksum when appropriate.
5. Do not claim that a Release exists until the GitHub Release asset has actually been uploaded.

## Reporting Security Issues

Do not place exploit instructions, real datasets, credentials, personal data, or customer reports in a public issue. Use the private reporting channel described in [SECURITY.md](../SECURITY.md), and include a minimal reproduction, affected version, impact, and a safe proof of concept.

## Legal Reuse Boundary

Making the repository visible is separate from granting reuse rights. Until the owner adds a formal `LICENSE` file, the repository should be treated as view-and-evaluate only: do not copy, modify, or redistribute it without written permission.
