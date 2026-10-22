# Gen_X Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans. Follow the explicit user scope: Bash/Slurm smoke only; no GPU compute.

**Goal:** Deliver literature survey and technical roadmap PDFs plus reproducible CPU-only Bash/Slurm smoke with a clearly labelled feedback-queue demonstration.

**Architecture:** Configuration-driven route registry, shell launchers, lightweight Python validation/QA, unique run artifacts. Documentation separates literature claims, proposed work and executed checks.

**Tech Stack:** Bash, Python 3 standard library, Slurm, Markdown, Pandoc/XeLaTeX.

**Spec:** docs/design.md

## Global Constraints

- All writes remain inside this repository; no GPU submissions or training.
- Existing results are never overwritten. External models/data are not committed.
- Synthetic fixtures and dry runs must be labelled and cannot be reported as model generation.
- Errors propagate to process exit status and Slurm job state.
- CPU smoke uses shared storage and one CPU with a short walltime.

## Review Focus

- User-controlled paths with spaces must remain intact.
- Invalid route/config fails before creating a successful manifest.
- Duplicate output directories are refused.
- Subprocess/Slurm failures cannot yield success records.
- Feedback scores are illustrative QA, not uncertainty estimates or physical validation.

## Task 1: Bash/Slurm workflow smoke and feedback queue

Own scripts/, configs/, tests/, examples/, runs/ and docs/smoke_results.md.

- [ ] Write meaningful failure tests for route/config validation, output collision, path quoting and failure propagation; record initial failure.
- [ ] Implement route configs, local smoke launcher and Slurm submit launcher with dry-run support.
- [ ] Implement synthetic QA-to-candidate-queue demo with provenance on every sample.
- [ ] Run local smoke and tests; save exact commands and results.
- [ ] Submit CPU-only Slurm smoke if available, monitor completion, and save job metadata/logs.
- [ ] Report executed vs unexecuted stages without claiming scientific success.

## Task 2: Literature and technical route

- [ ] Write docs/literature_survey.md with primary sources, release status, input/output, scale evidence and code availability.
- [ ] Write docs/technical_roadmap.md with model family selection, staged milestones, data contracts, ensemble validation and two feedback loops.
- [ ] Include actual environment observations and smoke outcome after Task 1.
- [ ] Render both documents to PDF and inspect pagination, text extraction and links.

## Task 3: Independent review and repository sync

- [ ] Review scientific claims, execution boundary, quoting/no-overwrite behavior and Slurm correctness.
- [ ] Address material findings and rerun affected checks.
- [ ] Commit only task-owned sources, PDFs and small run evidence; push to user-authorized repository.
- [ ] Verify remote commit and report links plus remaining scientific milestones.
