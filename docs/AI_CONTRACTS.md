# AI and data contracts

## Input boundary

entities contains 2–200 unique account/merchant/treasury ids and no personal traits. transactions contains 1–1,000 unique transfers between known distinct entities, positive amounts with at most two decimal places and offset-aware timestamps. review_threshold is 1–100. Optional ground_truth labels every current entity with a boolean. training_examples contains 40–500 separate historical snapshots with unique ids/timestamps, five documented behavioral features and boolean labels; all must predate the target activity window.

## Algorithm and provider boundary

The learned classifier uses only velocity, fan_in, fan_out, pass_through and cycle_count from separate historical snapshots. It has 400 deterministic full-batch gradient steps, learning rate 0.08 and L2 coefficient 0.02. Optional generative assistance receives flagged entity indicators and current case states and must cite only evidence belonging to the same entity. Neither model changes deterministic rule scores or human case outcomes.

## Result semantics

The report includes graph edges/components/cycles, evidence-linked entities, rule evaluation, threshold comparisons, case states and review audit. With historical training data it also includes partition membership/time boundaries, validation threshold curve, held-out test measurements, model artifact and current entity scores with per-feature log-odds contributions. Generated hypotheses are clearly separated from computed indicators.

## Evaluation discipline

Use the supplied original fictional fixtures to verify execution and repeatability. Preserve the data and source revision alongside every result. Measure adverse cases separately from successful cases, and do not interpret synthetic fixture performance as evidence about an unseen operational population. Provider test doubles exercise response schemas and rejection paths; live provider output needs its own dataset, review and quality evaluation.

Changing input data must produce a new execution rather than retroactively changing an old result. Model parameters, evidence citations and statistical decisions remain inspectable in the returned details. The application reports its limits rather than introducing unsupported neural, autonomous or compliance claims.

## Operational limits

| Boundary | Contract |
|---|---|
| Decision boundary | No entity is accused, blocked or automatically closed. Rule and model scores support investigation rather than establish fraudulent intent. |
| Model boundary | The learned classifier is trained on original synthetic snapshots. Scores are uncalibrated and its held-out measurements do not establish real-world fraud performance. |
| Leakage boundary | Historical snapshots must precede current activity, scaling/weights use training rows and threshold selection uses validation. The application cannot independently attest that externally supplied features were collected without future information. |
| Graph boundary | Cycle detection enumerates directed triangles, not arbitrary-length paths or rings. Legitimate treasury behavior can trigger both cycles and pass-through rules. |
| Identity boundary | Reviewer names and review events are scenario data, not authenticated identity or an external case-management integration. |
