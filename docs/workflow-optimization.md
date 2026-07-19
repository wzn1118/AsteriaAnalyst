# Workflow Optimization For Complex Data Sources

## Why the naive workflow fails

Most data-analysis products assume a simple path:

1. upload one file
2. preview a few rows
3. choose a chart or model
4. run analysis

That breaks down quickly in real work, because complex sources usually include:

- multiple sheets or tables with latent relationships
- ambiguous primary keys
- mixed semantic roles such as facts, dimensions, logs, and lookup tables
- inconsistent types and dirty category labels
- temporal data mixed with entity-level snapshots
- analysis goals that should branch into different routes

If the agent skips structural reasoning, it produces fast but unreliable output.

## Optimized workflow

The optimized workflow for Asteria Analyst is:

1. Source fingerprinting
   Determine the number of sheets, row/column counts, numeric vs categorical vs datetime structure, and likely table role.
2. Quality gate
   Measure missingness, duplicates, mixed-type columns, and high-cardinality dimensions before any inference.
3. Relationship modeling
   For multi-sheet inputs, scan shared column names and overlapping value domains to infer join paths and one-to-many vs many-to-many risk.
4. Workflow mode classification
   Route the dataset into a primary mode such as `multi_source_relational_analysis`, `temporal_analytical_modeling`, `entity_level_inference`, or `general_exploratory_analysis`.
5. Analysis track recommendation
   Suggest the right family of analyses: driver analysis, segmentation, trend analysis, or exploratory modeling.
6. Code-assisted execution
   Only after the plan is stable should the agent open Python or SQL execution for custom work.

## What the backend now computes

For each sheet:

- sheet role guess
- candidate keys
- high-cardinality columns
- mixed-type columns
- overall missing ratio
- duplicate row ratio

Across sheets:

- candidate relationship pairs
- overlap ratios for likely join fields
- one-to-one / one-to-many / many-to-many hints

Across the full dataset:

- complexity score
- quality score
- prioritized recommended sequence
- suggested analysis tracks

## Why this matters

This changes the agent from “analysis UI with some models” into “analysis system that thinks before it runs.” That is the right direction if the goal is eventually to support:

- enterprise BI workflows
- messy research datasets
- survey + behavioral + transactional combined analysis
- causality / experimentation workflows
- agentic notebook generation and autonomous reporting

## Next engineering steps

1. Push the workflow blueprint into the frontend so the user sees route recommendations before running statistics.
2. Add semantic type refinement for currency, percentages, IDs, geographic fields, and treatment / outcome candidates.
3. Add explicit multi-table join planning with join previews and row-loss estimates.
4. Add optional LLM reasoning on top of the deterministic workflow blueprint.
5. Add artifact memory so the agent can compare multiple datasets, not just one upload at a time.
