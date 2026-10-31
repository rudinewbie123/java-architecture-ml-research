# Java Architecture ML Research

Reproducible pilot for Java 21 software-architecture mining and evaluation.

## Frozen protocol
- Primary language: Java
- Strict toolchain: JDK 21
- Scope: static source analysis + controlled runtime benchmarking
- Repository observations are pinned to immutable commit SHAs.
- Failed builds and missing measurements remain explicit; no synthetic values are substituted.

## One-time upload to the empty GitHub repository
1. Open https://github.com/rudinewbie123/java-architecture-ml-research
2. Choose **Add file → Upload files**.
3. Extract this ZIP and upload its contents, including the hidden `.github` directory.
4. Commit to `main`.
5. Open **Actions** and run **Java 21 repository build + static extraction** using `workflow_dispatch`.

The connected GitHub integration currently rejects write API calls with HTTP 403. These files are prepared for one-time upload by the repository owner. No repository files have been committed by this assistant.

## Workflow
The workflow clones each pinned source repository, sets up JDK 21 and Maven, runs Maven `verify`, extracts static screening metrics, and uploads CSV/logs as an Actions artifact.

## Scientific limitations
- Import density is a screening proxy, not CK CBO.
- Static counts require AST/dependency-graph validation for final coupling metrics.
- Runtime benchmarking is separate. Barista is used only for benchmark applications it supports; arbitrary repositories require equivalent application-specific workloads.
