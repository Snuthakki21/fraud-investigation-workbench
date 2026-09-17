"""Regularized logistic regression with chronological train/validation/test separation."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import statistics

FEATURES = ('velocity', 'fan_in', 'fan_out', 'pass_through', 'cycle_count')
BOUNDS = {'velocity': 1000, 'fan_in': 200, 'fan_out': 200, 'pass_through': 100, 'cycle_count': 20000}

def sigmoid(value):
    if value >= 0:
        return 1 / (1 + math.exp(-min(value, 700)))
    e = math.exp(max(value, -700))
    return e / (1 + e)

@dataclass(frozen=True)
class TrainingObservation:
    id: str
    observed_at: datetime
    values: tuple[float, ...]
    label: int

@dataclass(frozen=True)
class LogisticModel:
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float

    def standardized(self, values):
        return tuple((value - mean) / scale for value, mean, scale in zip(values, self.means, self.scales))

    def predict(self, values):
        contributions = tuple(weight * value for weight, value in zip(self.weights, self.standardized(values)))
        return sigmoid(self.intercept + sum(contributions)), contributions

class TemporalModelTrainer:
    def _parse(self, records):
        if not isinstance(records, list) or not 40 <= len(records) <= 500:
            raise ValueError('training_examples must contain 40–500 historical feature snapshots.')
        observations, ids, stamps = [], set(), set()
        for record in records:
            if not isinstance(record, dict) or set(record) != {'id', 'observed_at', 'features', 'label'} or not isinstance(record['id'], str) or not 1 <= len(record['id']) <= 64 or record['id'] in ids or type(record['label']) is not bool:
                raise ValueError('Training snapshots require unique bounded ids, features, timestamps and boolean labels.')
            try:
                stamp = datetime.fromisoformat(record['observed_at'].replace('Z', '+00:00'))
                if stamp.tzinfo is None:
                    raise ValueError()
                stamp = stamp.astimezone(timezone.utc)
            except (AttributeError, TypeError, ValueError, OverflowError):
                raise ValueError('Training timestamps need an explicit UTC offset.') from None
            if stamp in stamps:
                raise ValueError('Training snapshot timestamps must be unique to prevent temporal split overlap.')
            features = record['features']
            if not isinstance(features, dict) or set(features) != set(FEATURES):
                raise ValueError('Training snapshots must contain exactly the documented behavioral features.')
            for name, value in features.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= BOUNDS[name] or not math.isfinite(value):
                    raise ValueError(f'Training feature {name} is outside its supported range.')
            observations.append(TrainingObservation(record['id'], stamp, tuple(float(features[name]) for name in FEATURES), int(record['label'])))
            ids.add(record['id']); stamps.add(stamp)
        return sorted(observations, key=lambda item: item.observed_at)

    def _fit(self, rows):
        if len({row.label for row in rows}) < 2:
            raise ValueError('The training partition must contain both label classes.')
        means = tuple(statistics.mean(row.values[i] for row in rows) for i in range(len(FEATURES)))
        scales = tuple(max(statistics.pstdev(row.values[i] for row in rows), 1e-8) for i in range(len(FEATURES)))
        x = [tuple((value - mean) / scale for value, mean, scale in zip(row.values, means, scales)) for row in rows]
        weights, intercept = [0.0] * len(FEATURES), 0.0
        # Full-batch gradients and fixed schedule give repeatable, bounded training.
        for _ in range(400):
            errors = [sigmoid(intercept + sum(w * v for w, v in zip(weights, values))) - row.label for values, row in zip(x, rows)]
            intercept -= .08 * sum(errors) / len(rows)
            for i in range(len(weights)):
                gradient = sum(error * values[i] for error, values in zip(errors, x)) / len(rows) + .02 * weights[i]
                weights[i] -= .08 * gradient
        return LogisticModel(means, scales, tuple(weights), intercept)

    def _metrics(self, rows, model, threshold):
        probabilities = [model.predict(row.values)[0] for row in rows]
        tp = sum(p >= threshold and row.label == 1 for p, row in zip(probabilities, rows))
        fp = sum(p >= threshold and row.label == 0 for p, row in zip(probabilities, rows))
        fn = sum(p < threshold and row.label == 1 for p, row in zip(probabilities, rows))
        tn = len(rows) - tp - fp - fn
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        return {'threshold': threshold, 'samples': len(rows), 'true_positives': tp, 'false_positives': fp, 'false_negatives': fn, 'true_negatives': tn, 'precision': precision, 'recall': recall, 'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0, 'brier_score': sum((p - row.label)**2 for p, row in zip(probabilities, rows)) / len(rows)}

    def train_and_score(self, records, entities, activity_start=None):
        if records is None:
            return {'available': False, 'note': 'Supply separate historical training_examples to train and evaluate the behavioral classifier. Rule-based case handling remains available.'}
        observations = self._parse(records)
        if activity_start is not None and observations[-1].observed_at >= activity_start:
            raise ValueError('Historical training snapshots must precede the target activity window.')
        train_end, validation_end = int(len(observations) * .6), int(len(observations) * .8)
        training, validation, test = observations[:train_end], observations[train_end:validation_end], observations[validation_end:]
        model = self._fit(training)
        curve = [self._metrics(validation, model, threshold) for threshold in (.2, .3, .4, .5, .6, .7, .8)]
        selected = max(curve, key=lambda row: (row['f1'], row['precision'], row['threshold']))['threshold']
        test_metrics = self._metrics(test, model, selected)
        scores = []
        for entity in entities:
            values = (entity['max_outgoing_per_hour'], entity['distinct_senders'], entity['distinct_recipients'], min(entity['pass_through_ratio'] or 0, 100), sum(len(indicator.get('cycle_ids', [])) for indicator in entity['indicators']))
            probability, contributions = model.predict(values)
            scores.append({'entity_id': entity['entity_id'], 'model_score': round(probability, 6), 'above_model_threshold': probability >= selected, 'contributions': {name: round(value, 6) for name, value in zip(FEATURES, contributions)}, 'intercept': model.intercept})
        artifact = {'feature_order': FEATURES, 'means': model.means, 'scales': model.scales, 'weights': model.weights, 'intercept': model.intercept, 'threshold': selected}
        artifact['sha256'] = hashlib.sha256(json.dumps(artifact, sort_keys=True).encode()).hexdigest()
        split = {name: {'samples': len(rows), 'ids': [row.id for row in rows], 'first_timestamp': rows[0].observed_at.isoformat(), 'last_timestamp': rows[-1].observed_at.isoformat(), 'positives': sum(row.label for row in rows)} for name, rows in [('train', training), ('validation', validation), ('test', test)]}
        return {'available': True, 'algorithm': 'L2-regularized logistic regression', 'split': split, 'artifact': artifact, 'validation_threshold_curve': curve, 'held_out_test': test_metrics, 'entity_scores': sorted(scores, key=lambda row: (-row['model_score'], row['entity_id'])), 'note': 'Scaling and coefficients use training rows only. Threshold selection uses validation only. Test labels affect only held-out metrics. Model scores rank synthetic activity; they are uncalibrated and never modify rule-based review states, declare fraud or trigger account actions.'}
