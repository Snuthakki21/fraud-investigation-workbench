"""Coordinate graph evidence, case handling, learned ranking and constrained narrative assistance."""
import hashlib
import json
from app.domain.policies import _validate
from app.domain.entities import ActivityRevision
from app.domain.graph import GraphAnalyzer
from app.domain.features import ActivityFeatureExtractor
from app.domain.cases import CaseReviewWorkflow
from app.ai.evaluation import _evaluate, ThresholdEvaluation
from app.ai.model import TemporalModelTrainer
from app.ai.narrative import GroundedCaseNarrator

class ProductApplication:
    def run(self, payload, context=None):
        entity_ids, transactions, threshold, reviews, labels = _validate(payload)
        revision = hashlib.sha256(json.dumps({'entities': payload['entities'], 'transactions': payload['transactions'], 'review_threshold': threshold}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:16]
        identity = ActivityRevision(revision, threshold)
        graph = GraphAnalyzer.build(entity_ids, transactions)
        cycles, components, edges = graph.cycles, graph.components, graph.edges
        features, evidence_map = ActivityFeatureExtractor.extract(entity_ids, graph, threshold)
        flagged = {row['entity_id'] for row in features if row['review_required']}
        evaluation = _evaluate(labels, flagged)
        threshold_comparison = ThresholdEvaluation().compare(labels, features)
        states, audit, feature_by_id = CaseReviewWorkflow.apply(features, flagged, reviews, identity.value)
        behavioral_model = TemporalModelTrainer().train_and_score(payload.get('training_examples'), features, min(tx['time'] for tx in transactions))
        model_summaries, model_used = GroundedCaseNarrator.summarize(flagged, features, states, feature_by_id, context)
        evidence = [f"G1: {len(entity_ids)} synthetic entities and {len(transactions)} transactions form {len(components)} connected components and {len(cycles)} directed triangle(s).", f"G2: {len(flagged)} accounts meet the configured priority threshold of {threshold}/100. A priority score is a heuristic, not a probability of fraud."]
        evidence += [f"{key}: {value}" for key, value in list(evidence_map.items())[:30]]
        if evaluation["available"]:
            evidence.append(f"E1: Synthetic label evaluation: TP={evaluation['true_positives']}, FP={evaluation['false_positives']}, FN={evaluation['false_negatives']}, TN={evaluation['true_negatives']}. Labels are excluded from detection.")
        metrics = [{"label": "Cases requiring review", "value": len(flagged), "unit": "cases"}, {"label": "Directed activity cycles", "value": len(cycles), "unit": "cycles"}]
        for key in ("precision", "recall"):
            if evaluation.get(key) is not None:
                metrics.append({"label": f"Synthetic {key}", "value": round(evaluation[key] * 100, 2), "unit": "%"})
        summary = f"Prioritize {len(flagged)} synthetic accounts for analyst review based on linked activity, transfer velocity and pass-through patterns. No account is accused, blocked or automatically closed; {len(audit)} explicit human review event(s) were applied in this local simulation."
        return {"summary": summary, "metrics": metrics, "evidence": evidence, "next_actions": ["Review the cited transactions and legitimate business context before drawing a conclusion.", "Inspect false positives and missed seeded cases; compare thresholds against analyst capacity.", "Record a human rationale and evidence references for every case-state change."], "details": {"activity_revision": revision, "review_threshold": threshold, "entities": features, "edges": [{"from": e["from"], "to": e["to"], "transaction_count": e["transaction_count"], "total_amount": e["total_cents"] / 100} for _, e in sorted(edges.items())], "components": components, "cycles": [{"id": f"cycle-{i}", "entities": list(cycle) + [cycle[0]]} for i, cycle in enumerate(cycles, 1)], "evaluation": evaluation, "case_states": states, "review_audit": audit, "model_used": model_used, "model_summaries": model_summaries, "behavioral_model": behavioral_model, "threshold_comparison": threshold_comparison, "limits": "Rule-based graph indicators plus an optional separately trained synthetic behavioral classifier. No protected traits are accepted. Case reviews and reviewer identity are caller-supplied simulations; no account or external case system is modified."}}
