# HARMONY v0.7 — Java 21 Dataset Expansion and Screening

## Scope and status

This release carries forward the five pinned pilot repositories and adds nine repository candidates screened against the strict Java 21 rule. The candidate pool now contains 14 repositories. This is an intake/screening pool, not a final labelled dataset.

**Important:** no Maven/Gradle build was executed in this stage. `build_verification=NOT_RUN`; all new candidates have `expert_label_status=UNVERIFIED`. Repository README claims are not treated as ground truth.

## Added candidates

### Modular monolith
- **JAVA-P015 — alitaghavizad/tixly-modular-monolith**, commit `92efd7e6f0087be1892b656d106db064dac0dadd`. Java 21 in POM; README describes Spring Modulith, public module APIs, domain events, ArchUnit and module-boundary verification tests. Candidate label: `modular_monolith`.
  - [README](https://github.com/alitaghavizad/tixly-modular-monolith/blob/92efd7e6f0087be1892b656d106db064dac0dadd/README.md)
  - [POM](https://github.com/alitaghavizad/tixly-modular-monolith/blob/92efd7e6f0087be1892b656d106db064dac0dadd/pom.xml)
- **JAVA-P016 — q86865511/ERPSystem**, commit `33b5df13594bcb456ba8a3d20e0bc455ac79aa75`. Java 21 in POM; README refers to an ADR defining an enforced modular monolith. Candidate label: `modular_monolith`. Inspect ADR and source boundaries before acceptance.
  - [README](https://github.com/q86865511/ERPSystem/blob/33b5df13594bcb456ba8a3d20e0bc455ac79aa75/README.md)
  - [POM](https://github.com/q86865511/ERPSystem/blob/33b5df13594bcb456ba8a3d20e0bc455ac79aa75/pom.xml)
  - [ADR 0001](https://github.com/q86865511/ERPSystem/blob/33b5df13594bcb456ba8a3d20e0bc455ac79aa75/docs/adr/0001-modular-monolith.md)
- **JAVA-P017 — abdalrahmanehab/spring-commerce**, commit `77763a9b63a00a7dea3378f0c6f1ac0d822b771a`. Java 21 in POM; README describes package-by-feature modular monolith. Candidate label: `modular_monolith`.
  - [README](https://github.com/abdalrahmanehab/spring-commerce/blob/77763a9b63a00a7dea3378f0c6f1ac0d822b771a/README.md)
  - [POM](https://github.com/abdalrahmanehab/spring-commerce/blob/77763a9b63a00a7dea3378f0c6f1ac0d822b771a/pom.xml)
- **JAVA-P018 — MiguelCorre/minibank**, commit `bdc2bfd2889b2976934567dda122968fe531c55d`. Java 21 in POM; README describes account, transfer, ledger, auth and common packages with one-way dependencies. Candidate label: `modular_monolith`.
  - [README](https://github.com/MiguelCorre/minibank/blob/bdc2bfd2889b2976934567dda122968fe531c55d/README.md)
  - [POM](https://github.com/MiguelCorre/minibank/blob/bdc2bfd2889b2976934567dda122968fe531c55d/pom.xml)

### Microservices
- **JAVA-P019 — SaiUpadhyayula/spring-boot-3-microservices-course**, commit `9cc3cc7c37ab25315d8d92bd58dae19fdfff3b65`. Java 21; separate API gateway, product, order, inventory and notification modules; Kubernetes application manifests. Candidate label: `microservices`.
  - [README](https://github.com/SaiUpadhyayula/spring-boot-3-microservices-course/blob/9cc3cc7c37ab25315d8d92bd58dae19fdfff3b65/README.md)
  - [POM](https://github.com/SaiUpadhyayula/spring-boot-3-microservices-course/blob/9cc3cc7c37ab25315d8d92bd58dae19fdfff3b65/pom.xml)
- **JAVA-P021 — blanho/fintech-platform-microservices**, commit `735487004e378a8b7072e9f1ab07701ccd08f9b6`. Java 21; multiple domain services; README documents Kafka, gRPC and database-per-service; deployment manifests are present. Candidate label: `microservices`.
  - [README](https://github.com/blanho/fintech-platform-microservices/blob/735487004e378a8b7072e9f1ab07701ccd08f9b6/README.md)
  - [Parent POM](https://github.com/blanho/fintech-platform-microservices/blob/735487004e378a8b7072e9f1ab07701ccd08f9b6/src/pom.xml)
  - [Docker Compose](https://github.com/blanho/fintech-platform-microservices/blob/735487004e378a8b7072e9f1ab07701ccd08f9b6/deploy/docker-compose.yml)
- **JAVA-P022 — varadharajaan/freightflow**, commit `425e982f7a2f403110114e31c942ffc13a36708a`. Java 21; separate service POMs and Dockerfiles; README documents Kafka, Kubernetes, Istio, Saga, CQRS/event sourcing and per-service database. Candidate label: `microservices`.
  - [README](https://github.com/varadharajaan/freightflow/blob/425e982f7a2f403110114e31c942ffc13a36708a/README.md)
  - [Parent POM](https://github.com/varadharajaan/freightflow/blob/425e982f7a2f403110114e31c942ffc13a36708a/pom.xml)
  - [Kubernetes deployment](https://github.com/varadharajaan/freightflow/tree/425e982f7a2f403110114e31c942ffc13a36708a/infrastructure/kubernetes)
- **JAVA-P023 — amitha-jestin/payment-gateway-k8s-demo**, commit `2bd3b8ada71b99c842aa2a417317e7b320f8e38b`. Java 21; user, order and payment services; service-specific Dockerfiles and Kubernetes deployments. Candidate label: `microservices`.
  - [README](https://github.com/amitha-jestin/payment-gateway-k8s-demo/blob/2bd3b8ada71b99c842aa2a417e7b320f8e38b/README.md)
  - [Parent POM](https://github.com/amitha-jestin/payment-gateway-k8s-demo/blob/2bd3b8ada71b99c842aa2a417e7b320f8e38b/pom.xml)
  - [Kubernetes manifests](https://github.com/amitha-jestin/payment-gateway-k8s-demo/tree/2bd3b8ada71b99c842aa2a417e7b320f8e38b/k8s)

### Serverless
- **JAVA-P020 — dominikcebula/aws-samples-lambda-serverless-framework-java21**, commit `0d2f106c77fdf356b2d3befb9c62f5322c57db1d`. Maven compiler source/target/release set to 21; Serverless Framework declares AWS `runtime: java21` and an HTTP API function. Candidate label: `serverless`.
  - [README](https://github.com/dominikcebula/aws-samples-lambda-serverless-framework-java21/blob/0d2f106c77fdf356b2d3befb9c62f5322c57db1d/README.md)
  - [POM](https://github.com/dominikcebula/aws-samples-lambda-serverless-framework-java21/blob/0d2f106c77fdf356b2d3befb9c62f5322c57db1d/pom.xml)
  - [serverless.yml](https://github.com/dominikcebula/aws-samples-lambda-serverless-framework-java21/blob/0d2f106c77fdf356b2d3befb9c62f5322c57db1d/serverless.yml)

## Current pool composition

| Candidate label | Count | Notes |
|---|---:|---|
| Modular monolith | 7 | 3 original + 4 new |
| Microservices | 5 | 1 original + 4 new |
| Serverless / serverless label under review | 2 | JAVA-P009 requires relabel adjudication; JAVA-P020 is a new pure serverless candidate |
| **Total** | **14** | All unverified |

The monolith-only class is not yet represented. Do not force a class-balanced sample by admitting non-Java-21 repositories.

## Exclusion / side-pool decisions

- Spring PetClinic Modulith (pinned commit `58c3310e36c7d827959df6af4d64bdeb8d81f1ea`): Java 17.
- xsreality/spring-modulith-with-ddd (pinned commit `bbbabe06d3af9ddd78c5699ca7b4dab36792ee8c`): Java 23.
- victorrentea/spring-modulith (pinned commit `d48fca8cf9782ab0d870da2946df0ad8c23bc295`): Java 17.
- teamlead/spring-microservices-kubernetes-demo (pinned commit `437c2fcdf85fb4b7e8d669ffc64d472b0e5b9484`): Java 17.
- ShopSphere (pinned commit `635db8b131d886cbee3e1c78f1e4dd4cc3546def`): Java 17.
- mzubal/spring-boot-monolith (pinned commit `67bb4d54a17ef93ab99e62a4347c24cd3a8b3bff`): Java 8.
- smit-lakhani-13/flight-ops-services (pinned commit `6db2673e0b9621aa840f039c962be5f69d1e1a78`): Java 21 and hybrid design elements, but its README states the EKS/SAM deployment artifacts were written and linted, never deployed. Keep in a design-intent side pool, not as an implemented-runtime positive label.

## Protocol for next stage

1. Download source at exact commit SHA, never default branch.
2. Run JDK 21 Maven/Gradle verification in isolated CI.
3. Record build outcome, test outcome, source LOC, module/service count, deployment artifacts, and missing evidence. Failed build is a recorded result, not an exclusion by default.
4. Inspect module/service boundaries and independently deployable units. A Maven module is not automatically a microservice.
5. Two independent reviewers assess every candidate. `CONFIRMED`, `REFUTED`, `UNCERTAIN` are recorded per defining criterion.
6. Adjudicate disagreement and freeze labels before training.
7. Preserve repository-level train/validation/test separation to avoid leakage.

## Research caution

The current pool is strongly enriched for modular monolith and microservices because public Java 21 sample repositories are easier to discover in those categories. It is not representative of the population of Java systems. Report this as a convenience/curated sample unless a systematic sampling frame is established. Do not claim generalization from 14 repositories.
