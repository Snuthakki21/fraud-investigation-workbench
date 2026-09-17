# User workflows and failure handling

Begin with graph evidence and legitimate business context. Choose thresholds against analyst capacity, then inspect false positives and missed cases. Treat historical labels and sampling policy as a model-governance artifact. Inspect held-out performance and contributions before using the learned ranking in an investigation. Every disposition should record a current revision, evidence and rationale; repeated or stale transitions are rejected.

## Workflow 1: Map activity

Load fictional accounts and timestamped transfers. Inspect connected components, directed three-account cycles, rolling outgoing velocity, sender/recipient counts and pass-through activity.

## Workflow 2: Tune review capacity

Compare rule thresholds and their queue sizes, precision, recall and missed seeded entities. Current labels evaluate the rules; they never enter feature computation.

## Workflow 3: Train a behavioral model

Choose the training scenario containing 80 separate historical feature snapshots. The model sorts them chronologically into train/validation/test partitions, fits train-only scaling and regularized logistic coefficients, and selects a threshold on validation data.

## Workflow 4: Inspect held-out evidence

Inspect the untouched test confusion matrix, precision, recall, F1 and Brier score. Per-entity log-odds contributions explain current model scores. The model artifact exposes feature order, means, scales, coefficients, intercept, threshold and digest.

## Workflow 5: Review a case

Open an evidence-linked case, cite its indicators and enter a rationale for a valid state transition. Reviews require the current activity revision. Optional model narratives remain analyst-reviewed hypotheses and cannot change scores or close cases.

## Saved work and comparison

Create a named scenario, execute the current input and save the resulting record. When exploring a changed policy or dataset, save a new scenario revision and execute it independently. Compare completed executions and inspect changed metrics alongside domain evidence. Review notes belong to the execution under review and should explain why the evidence supports the recorded decision.

## Recovery from errors

- Invalid input: retain the submitted input, read the field-level boundary in AI_CONTRACTS.md and correct the source. Do not make a result appear successful by deleting the failing test or silently changing the policy.
- Insufficient evidence: collect an appropriate source or observation window. Abstention and pending checkpoints are valid outcomes.
- Provider error: inspect the configured endpoint/model and retry explicitly. Computed domain evidence remains authoritative where a report exists; no claim of a successful model call is inferred from a configured provider.
- Stale version or review: load the current revision, inspect changed evidence and submit a new explicit review. Reusing an old approval is not a conflict-resolution strategy.
- Browser storage loss: browser records are local to that profile. Export important results and use native SQLite workspace storage when durable local records are required.

## Change review

Run all unit/integration tests, inspect new and adverse examples in the UI, and compare outputs against their recorded source/input provenance. Update the input/AI contracts when behavior changes. A source-code change requires a current review; an older review remains historical evidence only.
