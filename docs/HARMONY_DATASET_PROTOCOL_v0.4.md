# HARMONY Dataset Protocol v0.4

## Frozen decisions
- Output task: joint architecture classification and ranked alternatives.
- Immediate priority: dataset quality and provenance before model fitting.
- Language scope: Java; source snapshots pinned by commit SHA; JDK 21 toolchain.
- Compute: GitHub Actions hosted cloud runner.
- Architecture-level unit of inference: repository, not class.

## Current pilot cohort
The five candidate repositories in `data/java21_strict_manifest.csv` are a feasibility cohort. Their labels are screening labels until independently verified. The class-level AST table is nested within repository and must not be treated as 487 independent architecture samples.

## Feature status
`data/feature_dictionary.csv` records operational definitions and limitations. `rfc_source_proxy`, `cbo_local_type_proxy`, and `lcom1_name_based_proxy` are explicitly proxies. Do not rename them as standard CK metrics. `wmc_ast` is also a project-specific AST operationalization and requires validation against a reference implementation.

## Label verification
`data/architecture_label_evidence.csv` is an evidence register. A label can be marked VERIFIED only after a reviewer records a stable evidence URL, evidence type, reviewer identifier, and rationale. The present five labels are UNVERIFIED and therefore the supervised-learning gate remains closed.

## Validation workflow
The `HARMONY dataset quality gate` workflow:
1. Checks out the research repository.
2. Configures JDK 21 and Python 3.12.
3. Runs AST extraction against exact manifest SHAs.
4. Checks schema, candidate coverage, commit provenance, duplicate class identities, numeric validity, and label consistency.
5. Emits repository-level aggregates and a JSON quality report.
6. Uploads evidence as a GitHub Actions artifact.

A structural pass does not establish construct validity, label validity, sampling adequacy, or external validity.

## Next dataset work
- Independently verify architecture labels using repository documentation, module boundaries, deployment manifests, and expert review.
- Add repositories using a pre-registered inclusion/exclusion protocol and class-balanced sampling.
- Add semantic symbol resolution before treating CBO/RFC/LCOM as standard metrics.
- Keep repositories grouped during train/validation/test splitting to prevent leakage.
- Keep runtime performance features separate from static features until equivalent workloads and execution conditions are validated.
- Do not train the final HARMONY model on the five-repository pilot.
