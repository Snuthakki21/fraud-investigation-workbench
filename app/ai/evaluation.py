def _evaluate(labels, flagged):
    if labels is None:
        return {"available": False, "note": "No labels supplied; precision and recall are not estimated."}
    truth = {entity for entity, positive in labels.items() if positive}
    tp, fp, fn = flagged & truth, flagged - truth, truth - flagged
    tn = set(labels) - flagged - truth
    return {"available": True, "true_positives": len(tp), "false_positives": len(fp), "false_negatives": len(fn), "true_negatives": len(tn), "precision": len(tp) / len(flagged) if flagged else None, "recall": len(tp) / len(truth) if truth else None, "false_positive_entities": sorted(fp), "missed_seeded_entities": sorted(fn), "note": "Evaluation against original synthetic seeded labels. Labels are excluded from feature computation. This is not estimated real-world fraud-detection performance."}


class ThresholdEvaluation:
    def compare(self, labels, features):
        if labels is None:
            return []
        return [{'threshold': threshold, 'queue_size': sum(row['priority_score'] >= threshold for row in features), **_evaluate(labels, {row['entity_id'] for row in features if row['priority_score'] >= threshold})} for threshold in (25, 40, 60, 75, 90)]
