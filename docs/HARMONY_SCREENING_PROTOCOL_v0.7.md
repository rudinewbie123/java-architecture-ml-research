# HARMONY — v0.7 screening protocol

## Primary labels
- `monolith`
- `modular_monolith`
- `microservices`
- `serverless`
- `hybrid`

## Java 21 gate
A candidate is eligible for the strict dataset only when its pinned build configuration and/or CI explicitly targets Java 21. A README-only mention is insufficient when the build file contradicts it.

## Architecture evidence
- Monolith: one production deployable unit, without enforced internal module boundaries.
- Modular monolith: one production deployable unit, explicit module boundaries and shared release lifecycle.
- Microservices: at least two independently deployable service units, runtime communication, and meaningful service/data ownership boundaries.
- Serverless: production-targeted function/event-driven managed compute, with function handlers and deployment definitions.
- Hybrid: multiple distinct deployment styles coexist in the intended production system and are integrated. Local dev/test adapters do not establish hybrid.

## Status values
`DISCOVERED` → `SCREENED_CANDIDATE` → `BUILD_CHECKED` → `EXPERT_REVIEWED` → `ADJUDICATED` → `FROZEN`.
A candidate must not be used as a supervised ground-truth sample before `ADJUDICATED`.

## Reproducibility
Pin repository commit SHA, preserve evidence links, record exact build command/JDK distribution, logs, and timestamps. No synthetic build or runtime metrics.
