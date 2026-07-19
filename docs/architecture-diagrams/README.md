# Architecture Diagram Sources

These files are the cleaned redesign sources prepared after auditing the Asteria project:

- `01-business-view.svg`
- `02-technical-architecture.svg`
- `03-endpoint-inventory.svg`

They are designed to solve the failures of the earlier Figma drafts:

- business explanation is separated from technical explanation
- the technical page shows only the structural backbone, not every endpoint
- the full endpoint list is moved into its own appendix page
- card sizes, gutters, and page margins are fixed on a strict grid to avoid overflow and visible misalignment

## Intended Figma mapping

- Page 1: `01 Business View`
- Page 2: `02 Technical Architecture`
- Page 3: `03 Endpoint Inventory`
- Current premium frame: `05 Business Flow Premium v1 - Low Color` (`52:2`)

## Evidence basis

The wording and grouping are grounded in:

- `backend/app/main.py`
- `backend/app/models.py`
- `frontend/src/app/*`
- `frontend/src/components/*`
- `backend/app/services/*`
- `docs/workflow-optimization.md`

## Published visual assets

The tracked PNG and SVG files in this directory are the public visual assets. A generated PDF may be created locally for review, but it is intentionally not linked here because `output/pdf/` is excluded from the public repository.

The low-color premium business flow is the default business-facing view; the previous no-cross business flow remains a comparison baseline.
