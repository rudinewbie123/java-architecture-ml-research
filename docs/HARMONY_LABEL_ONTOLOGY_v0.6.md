# HARMONY Architecture Label Ontology — v0.6 proposal

## Primary architecture labels
- `monolith`: one deployable application without explicitly enforced modular boundaries.
- `modular_monolith`: one deployable application with explicit internal module boundaries.
- `microservices`: multiple independently deployable services with runtime communication.
- `serverless`: production workload materially deployed on managed function/event-driven compute.
- `hybrid`: two or more materially distinct production deployment styles coexist in one integrated target system.

## Secondary attributes (not primary labels)
- `local_development_runtime` (e.g. Spring Boot local adapter)
- `shared_domain_core` (true/false)
- `event_driven_integration` (true/false)
- `containerized_infrastructure` (true/false)
- `deployment_platform` (Kubernetes, AWS Lambda, VM, etc.)

A local Spring Boot runtime used for development/parity testing does not make a Lambda production architecture hybrid. Hybrid requires evidence that multiple styles are concurrently part of the target production system.

This ontology is a proposal for expert review. Do not overwrite existing labels until the research team freezes the ontology and adjudicates candidates.
