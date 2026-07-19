---
name: analysis-delivery-workflow
description: Use when uploaded business data and a rough analysis ask must be converted into a clearer requirement, a coarse data understanding pass, an automatically chosen deliverable format, and a downloadable final report with minimal user decision burden.
---

# Analysis Delivery Workflow

## Overview

Use this skill when the user gives data files plus a rough request and expects the system to decide how to analyze and package the result. The goal is not to dump every possible analysis, but to move from vague input to a professional, downloadable deliverable.

## Workflow

### 1. Restate the Requirement Before Deep Analysis

Before running heavy analysis, rewrite the user request into a clearer problem statement:

- what problem the user really wants solved
- who the audience is
- what the output is meant to achieve
- what hard constraints exist
- which parts of the request are clear vs still ambiguous

If critical details are missing, ask at most a few high-value confirmation questions. If the request is already good enough, state:

- your understanding
- your default assumptions
- what you will do next

### 2. Build a Coarse Understanding of the Data

Do not jump straight into deep statistics. First identify:

- which files, tables, pages, or content blocks exist
- the rough theme of the data
- row counts, time range, variable types, and completeness
- obvious missingness, duplication, outliers, OCR/encoding issues, or format problems
- which parts are most useful for the stated goal

This layer should help choose the right analytical path, not just document metadata.

### 3. Choose the Output Format Automatically

The system should choose a main output format based on:

- the user goal
- the audience
- the structure of the data
- whether charts, narrative, tables, or slide-style packaging matter most

Return:

- 1 main output format
- at most 2 backup options

Always explain:

- why the chosen format fits best
- what problem it is best at solving
- whether a second supporting format should also be produced

### 4. Generate Interpreted Results

Results should not be raw tables only. They should include:

- structure
- emphasis
- conclusions
- explanations
- readable visual summaries when useful

Prefer judgments over exhaustive option lists. The system should help the user decide.

### 5. Make the Deliverable Downloadable

Every run should end with downloadable output. Good default bundles include:

- HTML or Markdown main report
- Excel attachment for structured result tables
- optional PDF, Word, PPT, or chart pack when the use case clearly needs them

Always tell the user:

- which files were created
- what each file is for
- which file is the primary one to download or share

## Output Contract

Every execution should return these sections in this order:

1. 需求重述
2. 需求确认问题或默认假设
3. 数据初步理解
4. 选定的输出方式及理由
5. 结果生成计划
6. 可下载交付物列表

If information is insufficient, stop after the confirmation layer and make the gaps explicit. If the request is clear enough, continue automatically.

## Project Notes

- This skill fits the Asteria Analyst product direction: reduce user decision cost and actively choose the right reporting path.
- Prefer a main HTML report when narrative + charts + structured sections all matter.
- Prefer an Excel companion file when analysts are likely to continue slicing the output.
- When the data looks like logs or social exports, treat ID columns as identifiers, not business metrics.

## References

- For output packaging heuristics, read `references/output-selection.md`.
- For section naming and report ordering, follow `references/report-structure.md`.
