# Contributing

## Development setup

- Use Python 3.11 or later and Node.js 20 or later.
- Keep `.env` and all uploaded datasets, reports, logs, runtime state, and credentials out of Git.
- Use `backend/requirements-dev.txt` for local development and test dependencies.

## Required checks

Run these checks before opening a pull request:

```powershell
cd backend
python -m pytest

cd ..\frontend
npm ci
npm run lint
npm run verify:method-guide
npm run build
```

## Report-release rules

Formal management reports must preserve the mandatory chain documented in `docs/architecture_ai_mandatory_chain.md`. AI outputs require schema-valid trace artifacts, numeric results must be produced by deterministic execution, and quality below 90 must block formal release.

## Scope

Do not add production endpoints that execute user-provided code, expose runtime credentials, or serve the entire backend storage directory. Public or multi-user deployment requires a separate security design and review.
