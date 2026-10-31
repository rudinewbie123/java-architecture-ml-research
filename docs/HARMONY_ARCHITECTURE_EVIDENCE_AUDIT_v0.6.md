# HARMONY v0.6 — Preliminary Architecture Evidence Audit

**Scope:** five Java repositories at the immutable commit SHAs in the pilot manifest.  
**Status:** documentary/structural screening completed; all labels remain `UNVERIFIED` pending independent expert review.

## Method
Inspected pinned repository trees and selected primary artifacts: README architecture descriptions, Maven/Gradle build files, Docker Compose files, service-specific Dockerfiles/POMs, CI/CD configuration, and AWS SAM deployment templates. Repository self-description is treated as supporting evidence, not sufficient proof.

## Candidate findings

### JAVA-P013 — Ecommerce Modular Monolith
**Preliminary assessment:** supports `modular_monolith`, pending review. The README describes a single deployable artifact, Spring Modulith, and `catalogquery` / `accountsquery` modules. The root POM targets Java 21. Compose provisions PostgreSQL and observability infrastructure rather than separately deployed business services.
**Remaining checks:** inspect actual package boundaries and Modulith tests; confirm one production business deployment.
Evidence: [README](https://github.com/diegolopes98/ecommerce-modular-monolith/blob/76c3bfd38e3ac6e3d7a811697dd24a3f7afba9e5/README.md) · [POM](https://github.com/diegolopes98/ecommerce-modular-monolith/blob/76c3bfd38e3ac6e3d7a811697dd24a3f7afba9e5/pom.xml) · [Compose](https://github.com/diegolopes98/ecommerce-modular-monolith/blob/76c3bfd38e3ac6e3d7a811697dd24a3f7afba9e5/compose.yml)

### JAVA-P014 — Sample Spring Modulith
**Preliminary assessment:** supports `modular_monolith`, pending review. README identifies four logical modules: department, employee, gateway, organization. The root Maven project targets Java 21 and includes Spring Modulith core/JPA/test dependencies. The documented run command starts one Spring Boot application; Compose provisions Zipkin only.
**Remaining checks:** inspect package declarations and Modulith verification tests; logical modules alone do not prove enforced boundaries.
Evidence: [README](https://github.com/piomin/sample-spring-modulith/blob/4d64aa4d321c4a2446bdfb7cc3cb378a38d48dd7/README.md) · [POM](https://github.com/piomin/sample-spring-modulith/blob/4d64aa4d321c4a2446bdfb7cc3cb378a38d48dd7/pom.xml) · [Compose](https://github.com/piomin/sample-spring-modulith/blob/4d64aa4d321c4a2446bdfb7cc3cb378a38d48dd7/docker-compose.yml)

### JAVA-P012 — Spring Modular Monolith
**Preliminary assessment:** supports `modular_monolith`, pending review. README identifies six modules: Common, Catalog, Orders, Inventory, Notifications, Webapp; documents event-driven module communication and schema isolation. Gradle targets Java 21 and includes Spring Modulith. Compose runs one application container plus PostgreSQL, RabbitMQ, and Zipkin. RabbitMQ does not by itself imply microservices.
**Remaining checks:** inspect package boundaries, module tests, and shared release/deployment lifecycle.
Evidence: [README](https://github.com/odrotbohm/spring-modular-monolith/blob/6d23a62890d82e93031b8aae9eb9b815bbe9b5a4/README.md) · [Gradle](https://github.com/odrotbohm/spring-modular-monolith/blob/6d23a62890d82e93031b8aae9eb9b815bbe9b5a4/build.gradle) · [Compose](https://github.com/odrotbohm/spring-modular-monolith/blob/6d23a62890d82e93031b8aae9eb9b815bbe9b5a4/compose.yml)

### JAVA-P005 — Ecommerce Microservices
**Preliminary assessment:** strongly supports `microservices`, pending independent review. README describes 13 backend services. Pinned tree contains service-specific Maven POMs, Dockerfiles, application configs, CI/CD workflows, and Kubernetes/ArgoCD files. Compose defines separately named service containers and configuration.
**Remaining checks:** confirm independent build/release/deployment, runtime communication, and data ownership. Multiple containers alone are insufficient.
Evidence: [README](https://github.com/hoangtien2k3/ecommerce-microservices/blob/2d687821f8246f426e536641cd0503cb15465275/README.md) · [Compose](https://github.com/hoangtien2k3/ecommerce-microservices/blob/2d687821f8246f426e536641cd0503cb15465275/docker-compose.yml) · [CI](https://github.com/hoangtien2k3/ecommerce-microservices/blob/2d687821f8246f426e536641cd0503cb15465275/.github/workflows/ci.yml)

### JAVA-P009 — Serverless Fintech Backend
**Preliminary assessment:** current `serverless_hybrid` label requires re-examination. SAM template declares one Java 21 Lambda behind API Gateway, with DynamoDB tables and EventBridge permissions. README and architecture guide describe `wallet-lambda` as the AWS deployment entrypoint, `wallet-core` as shared business logic, and `serverless-wallet-app` as Spring Boot for local development/parity testing. Both HTTP paths call the same `WalletFacade`.
**Interpretation:** evidence currently supports serverless production architecture plus a local Spring adapter, not necessarily a hybrid production deployment. If Spring Boot is not concurrently deployed as a production component, `hybrid` is not justified. Keep original label for traceability; do not relabel until reviewers decide.
Evidence: [README](https://github.com/mrahbari/serverless-fintech-style-backend-system/blob/080001c400a3b908381c2b6eb7009b1121b1c314/README.md) · [How it works](https://github.com/mrahbari/serverless-fintech-style-backend-system/blob/080001c400a3b908381c2b6eb7009b1121b1c314/docs/README-HOW-IT-WORKS.md) · [SAM template](https://github.com/mrahbari/serverless-fintech-style-backend-system/blob/080001c400a3b908381c2b6eb7009b1121b1c314/template.yaml)

## Cross-case conclusions
1. Three modular-monolith candidates have coherent evidence of one application deployment with internal modules.
2. JAVA-P005 has stronger deployment-level evidence for microservices than a README keyword alone, but service independence and data boundaries still require expert confirmation.
3. JAVA-P009 exposes a taxonomy issue: `serverless` and `hybrid` must be distinct. A local Spring adapter is a secondary runtime attribute, not automatically a second production architecture.
4. All labels remain `UNVERIFIED`. This audit is not expert judgment and does not authorize supervised training.

## Next actions
- Two reviewers independently complete `data/expert_label_review_v06.csv`.
- Reviewers record evidence and rationale without seeing each other's initial decisions.
- A third reviewer adjudicates disagreements.
- Freeze the label ontology before dataset expansion.
- Split training/validation/test by repository, never by class.
- Expand the repository sample before claims about model generalization.

## Reproducibility
All evidence links point to immutable commit snapshots in the pilot manifest. Re-run the audit if a source commit changes.
