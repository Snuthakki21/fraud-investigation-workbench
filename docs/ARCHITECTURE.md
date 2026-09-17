# Architecture: Fraud Investigation Workbench

## Execution boundary

`ProductApplication.run(payload, context=None)` is the application use case. It validates requests, coordinates independently testable domain and AI components, and returns the established report envelope. The compatibility adapter in `projects/fraud_investigation_workbench/project.py` preserves imports used by existing consumers and tests; the algorithms live in the modules below.

| Module | Responsibility |
|---|---|
| app/domain/policies.py | Entity, amount, timestamp, review and label boundaries. |
| app/domain/entities.py | TransactionGraph and immutable activity revision. |
| app/domain/graph.py | Component discovery, aggregated edges and directed triangles. |
| app/domain/features.py | Rolling velocity, fan-in/fan-out, pass-through and explainable rule scores. |
| app/domain/cases.py | Revision-bound analyst state transitions and evidence checks. |
| app/ai/model.py | Historical snapshot validation, temporal splits, logistic training and scored explanations. |
| app/ai/evaluation.py | Rule confusion metrics and threshold capacity comparisons. |
| app/ai/narrative.py | Evidence-grounded optional model hypotheses. |
| app/application/product.py | Graph, case, model and report use-case coordination. |

The shared platform is outside the domain layer: it owns scenario versions, execution persistence, generic review audit and comparisons. Domain case/approval state remains explicit input/output of the relevant domain services. Optional provider access is injected through the context boundary, keeping deterministic unit tests and local execution independent of a network service.

## Decisions

### ADR-001: Keep learned ranking separate from case authority

The classifier supplements investigation with a scored explanation. Rule flags own the review queue and CaseReviewWorkflow owns transitions. A model cannot open/close a case by changing a probability.

### ADR-002: Use explicit chronological partitions

Historical records are sorted by unique offset-aware timestamp and split 60/20/20. A unique timestamp cannot straddle a partition; historical records must precede the current activity window.

### ADR-003: Prevent evaluation contamination

Means, scales and coefficients use training data only. Validation data chooses an operating threshold. Held-out labels change only test metrics. Current ground_truth never enters model training or graph features.

### ADR-004: Make model parameters inspectable

A bounded five-feature logistic model permits exact log-odds contributions and a serializable digest. It is more auditable here than an unmeasured complex model; no neural-network capability is claimed.

### ADR-005: Measure errors before calling a score useful

Threshold comparisons expose queue capacity, false positives and missed seeded accounts. A calibrated production operating point requires representative reviewed outcomes and a documented sampling process.

## Failure and consistency model

Input validation failures do not produce a success report. A provider failure is not silently treated as model success. The application performs no production data or infrastructure write. The shared workspace records the source/input associated with a completed execution and uses optimistic scenario versions so conflicting updates can be detected instead of silently overwriting a saved revision.

Tests call domain services directly for mathematical and policy boundaries and execute ProductApplication through the retained public adapter for integration coverage. Browser execution packages the same application modules rather than maintaining a second JavaScript implementation of the domain algorithms.
