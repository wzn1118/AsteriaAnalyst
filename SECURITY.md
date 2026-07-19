# Security Policy

## Supported use

This repository is intended for local, loopback-only use. It is not a hardened public multi-user service. Do not expose the backend, fallback server, uploaded files, or generated report storage directly to the Internet.

## Reporting a vulnerability

Do not file public issues containing exploit details, credentials, personal data, uploaded datasets, generated reports, or customer information. Contact the repository owner through the private GitHub security-advisory channel or the contact method configured for the repository. Include affected version, impact, reproduction steps, and a safe proof of concept.

## Security boundaries in this release

- HTTP code execution and runtime-control APIs are disabled by default.
- Only explicit public report artifacts may be served; application storage is not mounted as a static web root.
- Report HTML previews are sandboxed and must not be treated as trusted application content.
- API keys belong in local environment variables, never in Git or browser-accessible settings.
