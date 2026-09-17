"""Compatibility entry point; behavior lives in the product's application and domain layers."""
from copy import deepcopy
import json
from pathlib import Path
from app.application.product import ProductApplication
from app.domain.policies import _validate, _valid_id
from app.domain.graph import _components, _triangles
from app.domain.features import _velocity
from app.domain.cases import TRANSITIONS
from app.ai.evaluation import _evaluate

def default_input():
    return json.loads((Path(__file__).parent / "fixtures" / "synthetic_activity.json").read_text())

def run(payload, context=None):
    return ProductApplication().run(payload, context)

_base = default_input()
_strict = deepcopy(_base)
_strict["review_threshold"] = 75
_unlabeled = deepcopy(_base)
_unlabeled.pop("ground_truth")
META = {"id": "fraud_investigation_workbench", "title": "Fraud Investigation Workbench", "category": "Financial crime investigation", "buyer": "Head of Fraud / Financial Crime Technology Director", "question": "Can analysts trace linked activity and understand both alerts and false positives?", "promise": "Turn synthetic transaction graphs into explainable, evidence-linked review priorities with measured limitations.", "description": "Directed cycles, rolling transfer velocity and pass-through indicators identify review candidates. Synthetic labels measure precision and recall; human review transitions keep final case handling accountable.", "principal": "Graph algorithms, temporal windows, exact monetary arithmetic, label-leakage prevention and constrained evidence-grounded AI summaries.", "director": "Analyst capacity, false-positive tradeoffs, case-review accountability and responsible model adoption.", "patterns": ["Graph analytics", "Temporal anomaly indicators", "Human case review", "Precision/recall evaluation", "Evidence-grounded model hypotheses"], "architecture": ["Original synthetic entities and transactions", "Validate amounts, identities and UTC timestamps", "Compute components, directed cycles and rolling velocity", "Score evidence-based review priorities", "Measure seeded-label precision and recall", "Apply explicit human review transitions", "Optional validated model hypotheses"], "risks": ["Legitimate treasury activity can form cycles", "Indicators do not establish fraudulent intent", "Synthetic labels do not predict real-world accuracy"], "limits": ["No protected personal traits or automated account action", "Directed triangles only, not arbitrary cycle enumeration", "Heuristic scoring, not a trained or calibrated classifier", "Reviewer identity is simulated"], "demo_inputs": [{"label": "Seeded graph patterns with false positives", "payload": _base}, {"label": "Higher threshold tradeoff", "payload": _strict}, {"label": "Unlabeled analyst workflow", "payload": _unlabeled}], "flagship": False, "order": 13}

_training = deepcopy(_base)
_training['training_examples'] = json.loads((Path(__file__).parent / 'fixtures' / 'training_snapshots.json').read_text())
META['demo_inputs'].insert(0, {'label': 'Train, validate and investigate', 'payload': _training})
META['patterns'] += ['Chronological model evaluation', 'Explainable logistic regression', 'Threshold calibration']
META['limits'] = [item for item in META['limits'] if 'not a trained' not in item] + ['Behavioral model is synthetic and uncalibrated; no production accuracy claim']
