# Fraud Investigation Workbench

![Application workspace](docs/screenshots/desktop.png)

A financial activity investigation application combining graph evidence, temporal rules, an explainable behavioral model and revision-bound analyst case review.

[Open application](https://Snuthakki21.github.io/fraud-investigation-workbench/) · [Source architecture](docs/ARCHITECTURE.md) · [AI and data contracts](docs/AI_CONTRACTS.md) · [Operating workflow](docs/WORKFLOWS.md) · [Tests](tests) · [Local setup](docs/RUNNING.md)

[![Tests](https://github.com/Snuthakki21/fraud-investigation-workbench/actions/workflows/ci.yml/badge.svg)](https://github.com/Snuthakki21/fraud-investigation-workbench/actions/workflows/ci.yml)

## What the application does

An analyst needs more than an alert score: linked transactions, reasons for priority, a view of false positives, and a traceable case disposition. This application separates evidence-based rules, learned ranking, labeled evaluation and human review so each can be inspected without confusing a high score with proof of wrongdoing.

## Working with the application

### 1. Map activity

Load fictional accounts and timestamped transfers. Inspect connected components, directed three-account cycles, rolling outgoing velocity, sender/recipient counts and pass-through activity.

### 2. Tune review capacity

Compare rule thresholds and their queue sizes, precision, recall and missed seeded entities. Current labels evaluate the rules; they never enter feature computation.

### 3. Train a behavioral model

Choose the training scenario containing 80 separate historical feature snapshots. The model sorts them chronologically into train/validation/test partitions, fits train-only scaling and regularized logistic coefficients, and selects a threshold on validation data.

### 4. Inspect held-out evidence

Inspect the untouched test confusion matrix, precision, recall, F1 and Brier score. Per-entity log-odds contributions explain current model scores. The model artifact exposes feature order, means, scales, coefficients, intercept, threshold and digest.

### 5. Review a case

Open an evidence-linked case, cite its indicators and enter a rationale for a valid state transition. Reviews require the current activity revision. Optional model narratives remain analyst-reviewed hypotheses and cannot change scores or close cases.

## Capabilities

| Area | Implemented behavior |
|---|---|
| Graph and temporal analytics | Connected components, directed triangles, rolling windows, pass-through indicators and exact monetary aggregation. |
| Machine learning | L2 logistic regression, train-only normalization, chronological splits, bounded full-batch optimization and reproducible parameter artifact. |
| ML evaluation | Validation-only threshold selection, held-out confusion metrics, Brier score, label-leakage regression tests and model contribution explanations. |
| Analyst workflow | Evidence-linked queues, explicit state machine, revision checks, duplicate-review rejection, rationale and review audit. |
| Generative AI controls | Provider hypotheses restricted to flagged entities and the same entity’s computed evidence; no autonomous financial or case action. |

## Run locally

Python 3.11 or newer runs the application. The core domain algorithms use the Python standard library. The hosted browser application runs the same code through its bundled WebAssembly Python runtime.

```sh
python3 -m portfolio serve
```

Open the loopback address printed by the server. For a repeatable command-line execution:

```sh
python3 -m portfolio run fraud_investigation_workbench
python3 -m portfolio run fraud_investigation_workbench --input examples/base.json --output reports/result.json
```

The [running guide](docs/RUNNING.md) covers installation, persistent workspace, browser deployment, optional provider configuration and troubleshooting. Browser workspace storage belongs to that browser; the native workspace uses local SQLite. Neither is advertised as a multi-tenant cloud service.

## Domain API

```python
from projects.fraud_investigation_workbench.project import default_input, run

payload = default_input()
result = run(payload)["details"]
assert all(row["priority_score"] <= 100 for row in result["entities"])
assert "case_states" in result
# The browser training scenario includes a separate historical dataset.
from projects.fraud_investigation_workbench.project import META
trained = run(META["demo_inputs"][0]["payload"])["details"]["behavioral_model"]
assert trained["available"]
assert trained["split"]["train"]["last_timestamp"] < trained["split"]["test"]["first_timestamp"]
```

The project entry point is a compatibility adapter. `ProductApplication` in `app/application/product.py` coordinates domain services; it does not duplicate their implementations.

## Input and result contracts

entities contains 2–200 unique account/merchant/treasury ids and no personal traits. transactions contains 1–1,000 unique transfers between known distinct entities, positive amounts with at most two decimal places and offset-aware timestamps. review_threshold is 1–100. Optional ground_truth labels every current entity with a boolean. training_examples contains 40–500 separate historical snapshots with unique ids/timestamps, five documented behavioral features and boolean labels; all must predate the target activity window.

The report includes graph edges/components/cycles, evidence-linked entities, rule evaluation, threshold comparisons, case states and review audit. With historical training data it also includes partition membership/time boundaries, validation threshold curve, held-out test measurements, model artifact and current entity scores with per-feature log-odds contributions. Generated hypotheses are clearly separated from computed indicators.

Invalid shapes and unsupported values fail before a successful execution is stored. The platform envelope adds source/input provenance, execution timing and provider-use disclosure. Rendering limits do not imply unreported success; inspect the full downloadable report for all reported data.

## Architecture and project structure

```text
app/
  application/    Use-case orchestration and report assembly
  domain/         Typed records, policies and substantive domain services
  ai/             Retrieval/model/evaluation components and provider boundaries
  platform/       Versioned scenarios, execution records, reviews, comparisons, SQLite and HTTP
projects/fraud_investigation_workbench/
  project.py      Small compatibility entry point and scenario catalog
  fixtures/      Original fictional example data
web/
  templates/     Product-specific workspace composition
portfolio/       CLI, build, worker package, runtime and transport adapters
tests/           Domain, integration, regression, workspace and browser-unit verification
docs/            Architecture, input/model contracts, workflows and operating guidance
```

The domain flow is:

```text
GraphAnalyzer → ActivityFeatureExtractor → CaseReviewWorkflow + ThresholdEvaluation → TemporalModelTrainer → GroundedCaseNarrator
```

See [architecture decisions](docs/ARCHITECTURE.md) for the reasoning behind the boundaries and the actual module responsibilities. The application is deliberately a modular single-process system within its documented data limits; it does not claim distributed infrastructure that is absent from the source.

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 -m coverage run -m unittest discover -s tests
python3 -m coverage report
python3 -m portfolio build --output dist
node --test tests/*.test.mjs
```

Install the pinned development requirements before the coverage command. Tests include original behavior regressions and the expanded domain cases in [test_product_domain.py](tests/test_product_domain.py). They exercise invalid inputs, adverse policy outcomes and evidence boundaries as well as successful scenarios. Test doubles for a provider verify the contract; they do not establish live provider quality.

The latest machine-generated [validation evidence](docs/VALIDATION.md) and independent review artifacts state what was actually checked. Earlier version reviews describe the source they reviewed; an expansion is not automatically covered by an older review. CI and deployment badges link to the live verification result.

## Operating boundaries

| Boundary | Meaning |
|---|---|
| Decision boundary | No entity is accused, blocked or automatically closed. Rule and model scores support investigation rather than establish fraudulent intent. |
| Model boundary | The learned classifier is trained on original synthetic snapshots. Scores are uncalibrated and its held-out measurements do not establish real-world fraud performance. |
| Leakage boundary | Historical snapshots must precede current activity, scaling/weights use training rows and threshold selection uses validation. The application cannot independently attest that externally supplied features were collected without future information. |
| Graph boundary | Cycle detection enumerates directed triangles, not arbitrary-length paths or rings. Legitimate treasury behavior can trigger both cycles and pass-through rules. |
| Identity boundary | Reviewer names and review events are scenario data, not authenticated identity or an external case-management integration. |

Begin with graph evidence and legitimate business context. Choose thresholds against analyst capacity, then inspect false positives and missed cases. Treat historical labels and sampling policy as a model-governance artifact. Inspect held-out performance and contributions before using the learned ranking in an investigation. Every disposition should record a current revision, evidence and rationale; repeated or stale transitions are rejected.

## Documentation

- [Architecture and decisions](docs/ARCHITECTURE.md)
- [AI and data contracts](docs/AI_CONTRACTS.md)
- [User workflows and failure handling](docs/WORKFLOWS.md)
- [Product requirements and acceptance](docs/PRODUCT.md)
- [Runtime and provider setup](docs/RUNNING.md)
- [Security policy](SECURITY.md)
- [Third-party notices](docs/THIRD_PARTY.md)

## Persistent workspace

The interface includes a versioned scenario library, execution history, exact input/result replay, outcome comparison and evidence reviews. GitHub Pages persists records in this browser; the native server uses SQLite with optimistic revisions, idempotent execution reservations and a verifiable audit chain. Application and workspace data remain independent of every other repository.

See [workspace workflows, installation, container, backup and recovery](docs/WORKSPACE.md), [HTTP API contracts](docs/API.md), [domain Staff Engineer review](docs/STAFF_REVIEW_V2.md), [platform Staff Engineer review](docs/STAFF_PLATFORM_REVIEW.md), and [measured validation](docs/VALIDATION.md).
