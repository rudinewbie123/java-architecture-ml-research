# HARMONY Architecture Label Verification Protocol v0.5

## Purpose
Independently verify repository-level architectural labels before supervised learning. The repository is the unit of analysis. Labels must describe the architecture implemented at the pinned commit, not merely the repository's marketing description or framework choice.

## Evidence hierarchy
1. Primary evidence: deployment manifests, service definitions, infrastructure-as-code, build modules, runtime entrypoints, API/service contracts, database ownership/configuration.
2. Supporting evidence: architecture decision records, official repository documentation, diagrams maintained with source.
3. Secondary evidence: maintainer statements or peer-reviewed case descriptions.
4. Insufficient alone: repository name, README keyword, directory naming, framework dependency, or a single Docker Compose file.

Record stable URLs or commit-pinned file links, evidence type, reviewer identifier, review date, and rationale in `data/architecture_label_evidence_v05.csv`.

## Operational decision rules

### Monolithic
A single deployable application/runtime unit is the primary production unit. Internal packages/modules do not independently deploy. A monolith may still use layered architecture.

### Modular monolith
One primary deployable application/runtime unit with explicit internal modules or bounded contexts. Modules share one release/deployment lifecycle; module boundaries are visible in code/build structure and preferably enforced by architecture tests or module contracts.

### Microservices
Multiple independently deployable services with runtime communication across service boundaries. Evidence should establish at least two separately deployable service units and their communication mechanism. Multiple folders, Maven modules, containers, or processes alone are insufficient if they are not independently deployable services.

### Serverless
A material part of the application is deployed as function/event-driven managed compute (e.g., Lambda or equivalent), with deployment configuration and function entrypoints. A local Spring Boot application or a SAM template alone is not sufficient unless the serverless functions are actually part of the target architecture.

### Hybrid
Use only when two or more architectural/deployment styles are materially combined in the same system and the integration is evidenced. Record the constituent styles explicitly. Do not use `serverless_hybrid` as a synonym for a serverless-oriented repository without evidence of a hybrid deployment.

## Reviewer dimensions
Each reviewer independently assesses:
- deployment unit count and independence;
- inter-unit communication;
- data ownership and persistence boundaries;
- release/deployment independence;
- module/service boundary evidence;
- serverless/function execution evidence, where applicable.

Use `CONFIRMED`, `REFUTED`, or `UNCERTAIN` per dimension. Reviewers must not see each other's initial decisions before submitting.

## Adjudication
- Two reviewers agree: accept provisional label, subject to evidence completeness.
- Reviewers disagree: third reviewer adjudicates; retain original ratings.
- Any `UNCERTAIN` on a defining criterion: label remains `UNVERIFIED`.
- Record Cohen's kappa (or an appropriate multi-rater agreement statistic) only after independent ratings are available. Do not calculate agreement from a single reviewer or pre-filled labels.

## Exclusion
Exclude or mark `UNCLASSIFIABLE` when source snapshot lacks sufficient architecture/deployment evidence, repository is a tutorial/sample without a coherent target system, or the pinned commit does not represent the documented system.

## Publication safeguards
- Freeze labels before model training.
- Split train/validation/test by repository, never by class.
- Do not infer labels from predictor variables that encode the same architectural declaration.
- Keep label evidence and reviewer notes in the audit trail.
- Report unresolved labels and excluded candidates transparently.
