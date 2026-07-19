# AI Mandatory Chain Architecture

## Purpose

This document defines the mandatory AI/Codex/LLM chain that must run before AsteriaAnalyst releases a formal management report.

The goal is to ensure that:

- field meaning is understood before report writing
- business routing is decided before report writing
- metric planning is established before numeric execution
- numeric results are produced deterministically
- renderer layers only render bound report content and do not reinterpret data

## Formal Release Chain

The formal report chain must be:

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

## Mandatory Responsibilities

### 1. DataProfileService

- Profiles raw uploaded data.
- Produces structural understanding such as field inventory, data types, missingness, object candidates, and sheet-level overview.
- Does not finalize business meaning by itself.

### 2. AIFieldSemanticMapper

- Interprets field semantics using AI/Codex/LLM.
- Produces structured semantic mapping and trace artifacts.
- Must run before routing and metric planning.

### 3. AIBusinessContextRouter

- Uses semantic understanding to determine business profile and report chain.
- Must not be skipped for formal release.
- Must emit structured routing output and trace.

### 4. AIMetricDerivationPlanner

- Plans which metrics are direct, derived, proxy, hypothesis, or unsupported.
- Must not directly fabricate final numeric values.
- Must emit structured planning output and trace.

### 5. DeterministicMetricExecutor

- Performs actual numeric calculation.
- All final numeric values used in formal reports must come from deterministic execution.
- LLMs must not invent numeric results.

### 6. EvidenceValidator

- Checks calculation inputs, evidence binding, and schema validity.
- Rejects malformed or unsupported AI output before formal report release.

### 7. ReportBindingLayer

- Binds validated AI interpretation plus deterministic metrics into report-ready structures.
- Ensures renderers consume already-understood fields and validated evidence.

### 8. FormalPDFReleaseGate

- Blocks formal release if any mandatory AI link is missing, invalid, or below quality threshold.
- The release gate is the final authority before `management_report.pdf` becomes releasable.

## Mandatory Rules

- `AIFieldSemanticMapper` must be called.
- `AIBusinessContextRouter` must be called.
- `AIMetricDerivationPlanner` must be called.
- AI output must be saved with trace artifacts.
- AI output must pass schema validation before downstream use.
- Numeric calculation must be done by `DeterministicMetricExecutor`.
- LLMs must not fabricate numeric facts.
- PDF renderers must not do field understanding, business routing, or metric interpretation planning.
- [report_service.py](../backend/app/services/report_service.py) must not bypass this AI mandatory chain for formal release.
- If AI trace is missing, only `debug_report` may be produced; formal `management_report.pdf` is forbidden.
- If the final score is below `90`, formal `management_report.pdf` is forbidden.

## Forbidden Shortcuts

- No direct `raw data -> renderer -> management_report.pdf`
- No renderer-side field interpretation
- No release based only on deterministic metrics without mandatory AI routing/semantic/planning steps
- No release based only on AI text without deterministic metric execution
- No silent fallback that still exposes formal `management_report.pdf`

## Trace Requirements

Mandatory AI stages must leave persistent trace outputs that can be audited later. At minimum:

- semantic mapping trace
- business routing trace
- metric derivation planning trace
- schema validation result
- downstream usage or binding record

If these traces are absent, formal release must be blocked.

## Renderer Boundary

Renderer responsibilities are limited to:

- consuming validated report-bound structures
- laying out HTML/PDF output
- preserving report content faithfully

Renderers must not:

- infer field roles
- reinterpret business profile
- invent metrics
- repair missing semantic understanding

## Release Policy

Formal `management_report.pdf` is allowed only when all of the following are true:

- mandatory AI chain steps completed
- AI trace exists
- schema validation passed
- deterministic numeric execution completed
- evidence validation passed
- formal release gate passed
- final score `>= 90`

If any condition fails:

- formal `management_report.pdf` must not be released
- `debug_report` may still be generated for diagnosis

## Definition of Done

- This document exists and defines the mandatory AI release chain.
- Root [AGENTS.md](../AGENTS.md) explicitly prohibits bypassing the chain.
- Future code and architecture changes must preserve this release policy.
