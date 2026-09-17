# Operating model: Fraud Investigation Workbench

## Decision and ownership

Can analysts trace linked activity and understand both alerts and false positives?

The **Financial crime operations lead** owns the business decision. The **Investigation platform engineer** owns reproducibility, validation and operational failure handling. An independent reviewer challenges the assumptions and evidence before wider adoption.

## Acceptance gate

Inspect entity indicators and transaction/cycle evidence, including false positives and misses, before recording a simulated review.

Pause the business decision when: Evidence is insufficient, a state transition is stale, or a generated hypothesis uses another entity’s evidence.

The repository's unit and independent-review tests are an engineering gate. They do not replace the domain owner's acceptance of assumptions and inputs.

## Working cycle

1. Select an original example or load a reviewed input file. Record its purpose and owner.
2. Run the application; retain both the input and exported JSON result.
3. Inspect evidence and exceptions before accepting the summary. Optional model prose remains a draft.
4. Record the execution review and rationale in the workspace. Reviewer labels remain operator-supplied data rather than authenticated identity.
5. Re-run when inputs, assumptions, rules or source code change. Compare source/input fingerprints and explain changed outcomes.

## Measures that matter

Analyst queue load, precision/recall on independently labeled samples, false positives and case-review age.

The included fixtures demonstrate calculations. They are not estimates of production value, organizational savings, regulatory compliance or population-level performance.

## Before organizational adoption

Authenticated analysts, durable cases, investigated ground truth, legal review and evidence-retention controls.

The included server is a loopback development tool for a single trusted operator. Public GitHub Pages executes local algorithms inside the visitor's browser; it exposes no model credentials. Do not publish confidential input files or point the development server at an unauthenticated public proxy.

## Failure and recovery

Validation failures do not produce an accepted replacement report. Preserve the failing synthetic input, reproduce it with the CLI, and compare against the relevant regression test. A browser cancellation stops the browser worker; an already-started local-server or provider request may finish. There is no automatic retry that could hide duplicated work or spend.

A release should retain the previous commit and its known-good input/report pair. Roll back by running that reviewed revision; reassess any intervening schema or rule changes before reusing old results.
