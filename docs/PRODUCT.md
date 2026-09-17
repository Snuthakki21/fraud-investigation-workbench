# Product requirements: Fraud Investigation Workbench

## Purpose

An analyst needs more than an alert score: linked transactions, reasons for priority, a view of false positives, and a traceable case disposition. This application separates evidence-based rules, learned ranking, labeled evaluation and human review so each can be inspected without confusing a high score with proof of wrongdoing.

## Functional acceptance

| Requirement | Observable behavior |
|---|---|
| Graph and temporal analytics | Connected components, directed triangles, rolling windows, pass-through indicators and exact monetary aggregation. |
| Machine learning | L2 logistic regression, train-only normalization, chronological splits, bounded full-batch optimization and reproducible parameter artifact. |
| ML evaluation | Validation-only threshold selection, held-out confusion metrics, Brier score, label-leakage regression tests and model contribution explanations. |
| Analyst workflow | Evidence-linked queues, explicit state machine, revision checks, duplicate-review rejection, rationale and review audit. |
| Generative AI controls | Provider hypotheses restricted to flagged entities and the same entity’s computed evidence; no autonomous financial or case action. |

## End-to-end acceptance

1. The supplied successful and adverse scenarios execute through the local API, CLI and browser worker using the same Python domain code.
2. Each new domain capability appears in the product-specific UI and in the downloadable report.
3. Input mutation is avoided; the same deterministic input produces the same domain result before platform timing/provenance metadata.
4. Provider calls are optional and explicit; unsupported generated evidence is rejected.
5. Saved scenarios and completed executions can be inspected independently, compared and reviewed without changing prior evidence.
6. The test suite covers policy rejection and malformed data as well as the happy path. A separate automated Staff Engineer reviewer checks the expansion before publication.

## Explicit operating boundaries

entities contains 2–200 unique account/merchant/treasury ids and no personal traits. transactions contains 1–1,000 unique transfers between known distinct entities, positive amounts with at most two decimal places and offset-aware timestamps. review_threshold is 1–100. Optional ground_truth labels every current entity with a boolean. training_examples contains 40–500 separate historical snapshots with unique ids/timestamps, five documented behavioral features and boolean labels; all must predate the target activity window.

The application accepts original fictional fixtures and bounded operator-supplied data. It does not promise production authentication, real account/infrastructure action, regulatory certification or model quality outside a measured dataset. Domain-specific limitations are documented in the README and AI_CONTRACTS.md.
