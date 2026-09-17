# Author engineering review

This is the implementing agent's scoped review of the original synthetic fraud investigation project and its tests. It is not the independent Staff Engineer review and does not claim a production security certification.

## Applied skills and actual evidence

Ponytail ultra: used standard-library graph traversal, rolling windows, integer cents, JSON and unittest. No graph database, orchestration framework, trained-model package or speculative integration was added. The bounded triangle algorithm is marked with a `ponytail:` ceiling comment.

Codex Security: read the Standard skill and desktop/prologue instructions. The parent owns any authoritative scan setup and canonical artifacts; this worker did not start or claim a completed independent native scan.

AgentOps security: reviewed the OWASP checklist and exercised source-backed trust boundaries. No private data, credentials, SQL, dynamic code execution, shell execution or project-defined network calls exist in this project. Optional provider calls pass only validated synthetic cases. Identity, HTTP transport and browser rendering remain shared runtime review scope.

HOL Guard: the initial worker availability checks did not resolve `hol-guard`, `plugin-scanner` or `pipx`. No protection or scanner-approval claim follows from this review. No `.env` files or user harness configuration were accessed or modified.

## Findings and controls

- Monetary values must be finite, positive and cent-exact. Aggregation uses integer cents.
- Entity IDs and transaction endpoints must match the input graph. Extra entity fields, including personal traits, are rejected.
- Seeded labels are used only after detection to calculate the confusion matrix. A test flips every label and proves that entity scores and evidence remain unchanged.
- Outbound transactions preceding the first receipt cannot contribute to the pass-through ratio.
- Review state transitions require a reviewer, rationale, entity-specific evidence and matching activity revision. Tests reject skipped states, stale activity and duplicate events.
- Model summaries must cite the same flagged account's computed evidence. They cannot modify the score or review states. Model failure fails the run without a persisted action.
- Narrative interpretations remain hypotheses. Exact valid evidence IDs do not prove the model's semantic interpretation.
- Demo reviewer identity and returned case state are caller-controlled; authenticated identity and durable audit are required for a real case workflow.

## OWASP review coverage

Secrets: no project secrets. Input validation: exercised through malformed IDs, amounts, timestamps, fields, reviews and model output. SQL/code injection: no execution surface. XSS/CSRF: no project HTML or HTTP handlers; shared runtime remains outside this author review. Authentication: no production identity claim. Authorization: project-specific review/reference checks only. Rate limiting: bounded local workload, no service limiter claim. Sensitive data: synthetic fixture only. Dependencies: standard library only; no interpreter CVE scan performed here.

## Verification

`python -m unittest discover -s tests -p 'test_fraud_investigation_workbench.py' -v` passed all 22 tests in the local run. Coverage.py 7.16.1 measured 219 statements and 106 branches with no missed statements or partial branches for `project.py` at that revision. Counterexample fixtures intentionally retain three false positives and one false negative at the default threshold. There is no claim of a live-provider evaluation or real-world fraud accuracy.
