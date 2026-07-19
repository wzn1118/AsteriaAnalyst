# AsteriaAnalyst Project Rules

These rules apply to all work in this repository.

## AI Mandatory Release Rules

Formal management report release must follow the mandatory AI chain below:

`raw data`
`-> DataProfileService`
`-> AIFieldSemanticMapper`
`-> AIBusinessContextRouter`
`-> AIMetricDerivationPlanner`
`-> DeterministicMetricExecutor`
`-> EvidenceValidator`
`-> ReportBindingLayer`
`-> FormalPDFReleaseGate`
`-> management_report.pdf`

The following rules are mandatory:

- `AIFieldSemanticMapper` must be called before formal report binding.
- `AIBusinessContextRouter` must be called before formal report binding.
- `AIMetricDerivationPlanner` must be called before formal report binding.
- AI/Codex/LLM outputs must persist trace artifacts.
- AI outputs must pass schema validation before downstream use.
- All numeric calculations must be executed by a deterministic executor.
- LLMs must not invent or finalize numeric results.
- PDF renderers must not perform field understanding or business routing.
- [backend/app/services/report_service.py](backend/app/services/report_service.py) must not bypass the AI mandatory chain.
- If AI trace is missing, the system may emit `debug_report` only and must not release formal `management_report.pdf`.
- If final quality score is below `90`, the system must not release formal `management_report.pdf`.

## Release Guardrails

- No formal management report is releasable without AI trace, schema-valid AI outputs, deterministic numeric execution, and release-gate approval.
- Any fallback, bypass, or missing AI mandatory step must be treated as a release blocker.
- Future code changes must preserve the mandatory AI chain and must not shift field understanding into renderer code.

## Testing Commands

Before considering report-generation changes complete, run:

- `python -m pytest`
- Because the frontend contains `package.json`, run `npm run build`
- If a dedicated `typecheck` script is added later, `npm run typecheck` is also acceptable where appropriate

## Definition of Done

- `docs/architecture_ai_mandatory_chain.md` exists and documents the mandatory AI release chain.
- `AGENTS.md` explicitly forbids bypassing the AI mandatory chain for formal management report release.
- Subsequent code changes must continue to obey this architecture and release policy.
