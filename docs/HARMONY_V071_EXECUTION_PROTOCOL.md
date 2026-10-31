# HARMONY v0.7.1 — Build Verification and Static Feature Extraction

## Objective
Run reproducible Java 21 build checks and source/configuration-level feature extraction for each repository in `data/java21_candidate_manifest_v07.csv`.

## Execution architecture
- GitHub Actions hosted Ubuntu runners; the user's Mac is not used for heavy computation.
- Dynamic matrix is generated from the committed manifest.
- At most four candidate repositories run concurrently by default.
- Each candidate is checked out at the exact 40-character commit SHA.
- JDK 21 (Temurin) is used for every candidate.
- Maven and Gradle builds are attempted where descriptors exist.
- Static extraction runs even if a build fails, provided the pinned source checkout succeeds.
- Per-candidate artifacts are merged into one consolidated artifact.

## Files
- `.github/workflows/harmony-v071-build-static.yml`
- `scripts/harmony_v071/prepare_matrix.py`
- `scripts/harmony_v071/run_candidate.py`
- `scripts/harmony_v071/aggregate_results.py`
- `scripts/harmony_v071/requirements.txt`

## Build interpretation
`BUILD_PASS` means the detected build command completed with exit code zero. `PARTIAL_BUILD_PASS` means at least one of multiple independent build roots passed. `BUILD_FAILED`, `NO_BUILD_DESCRIPTOR`, `CLONE_FAILED`, and `PINNED_SHA_FAILED` are retained as outcomes and must not be silently removed from the candidate log.

The pipeline runs Maven `clean verify` and Gradle `clean build`; tests are not intentionally skipped. A build failure may be caused by repository defects, external dependency availability, environment assumptions, or test instability. Inspect logs before making eligibility decisions.

## Static feature groups
1. Java source size: Java file count, physical/nonblank LOC.
2. AST structure: class/interface/enum/record declarations, methods/constructors, fields, annotations, imports, parse-error files.
3. Package import graph: package nodes, cross-package import edges, density, mean/max fan-in and fan-out.
4. Deployment/configuration inventory: POMs, Gradle files, Dockerfiles, Compose files, Kubernetes/Helm manifests, SAM/Serverless manifests, Terraform files.
5. Technology markers: REST annotations, Kafka, gRPC, Spring Modulith, AWS Lambda patterns.

These are static proxies. They are not runtime performance measures, service-call graphs, or canonical CK metrics. In particular, `package_dependency_density` is based on Java package imports and must not be reported as CK CBO.

## Reproducibility controls
- Commit SHA must match the manifest.
- The workflow records JDK version, build commands, exit codes, durations, logs, and UTC timestamps.
- All candidate outcomes are retained, including failures.
- Candidate labels are copied as provisional metadata only; they are not changed by this workflow.
- Do not run supervised training until independent expert review and adjudication are complete.

## Expected consolidated artifact
`harmony-v071-consolidated-<run_id>`:
- `build_results_v071.csv`
- `repository_features_v071.csv`
- `class_ast_metrics_v071.csv`
- `harmony_v071_summary.json`

## Manual execution
In GitHub: Actions → HARMONY v0.7.1 - Java 21 Build Verification and Static Feature Extraction → Run workflow. Default concurrency is four. Use two if dependency services or rate limits cause instability.
