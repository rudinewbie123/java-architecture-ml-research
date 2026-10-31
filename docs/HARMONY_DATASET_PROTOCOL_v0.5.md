# HARMONY Dataset v0.5 — Operational Next Step

## Frozen decisions
- Prediction target: classification plus ranked alternatives.
- Priority: dataset-first.
- Execution: GitHub Actions cloud runner.
- Pilot scope: Java 21; five repositories.
- Repository is the architecture-level unit of inference.

## What v0.5 adds
1. Repository-level descriptive feature engineering from existing class AST rows: sums, means, medians, quartiles, standard deviations, Gini dispersion, type-kind counts, observed package counts.
2. An explicit architecture-label verification protocol and evidence register.
3. An expert review template for independent reviewers.
4. A machine-readable report with class-record imbalance and a supervised-learning readiness gate.

## Important restrictions
- Do not train a model on the five-repository pilot.
- Do not use 487 class records as 487 independent architecture samples.
- Do not claim runtime quality from static source metrics.
- RFC/CBO/LCOM remain proxies; WMC is project-specific until validated against an accepted implementation.
- Architecture labels remain UNVERIFIED until independent evidence is recorded.

## Execution
The workflow expects the existing AST artifact committed at `results/ast_metrics/class_ast_metrics.csv`. It generates:
- `results/harmony_v05/repository_features_v05.csv`
- `results/harmony_v05/harmony_v05_audit_report.json`

The script is descriptive and auditable. It does not infer or change labels.
