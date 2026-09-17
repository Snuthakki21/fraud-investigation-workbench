from copy import deepcopy
from app.domain.policies import _valid_id

TRANSITIONS = {"new": {"triaged"}, "triaged": {"investigating", "closed_no_issue"}, "investigating": {"escalated", "closed_no_issue"}, "escalated": set(), "closed_no_issue": set()}



class CaseReviewWorkflow:
    @staticmethod
    def apply(features, flagged, reviews, revision):
        feature_by_id = {x["entity_id"]: x for x in features}
        states = {entity: "new" for entity in sorted(flagged)}
        audit, review_ids = [], set()
        for review in reviews:
            required = {"review_id", "entity_id", "from_state", "to_state", "reviewer", "rationale", "evidence_ids", "expected_revision"}
            if not isinstance(review, dict) or set(review) != required or not _valid_id(review.get("review_id")) or review["review_id"] in review_ids:
                raise ValueError("Each human review must have the required fields and a unique review_id.")
            entity = review["entity_id"]
            if not isinstance(entity, str) or entity not in flagged or review["expected_revision"] != revision:
                raise ValueError("Human review must reference a flagged entity and the current activity revision.")
            if review["from_state"] != states[entity] or not isinstance(review["to_state"], str) or review["to_state"] not in TRANSITIONS[states[entity]]:
                raise ValueError("Case review has an invalid or stale state transition.")
            if any(not isinstance(review.get(key), str) or not 3 <= len(review[key].strip()) <= 500 for key in ("reviewer", "rationale")):
                raise ValueError("Human review requires a reviewer and an explanatory rationale.")
            ids = review["evidence_ids"]
            allowed = {x["id"] for x in feature_by_id[entity]["indicators"]}
            if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or x not in allowed for x in ids):
                raise ValueError("Human review must cite the entity's computed evidence.")
            states[entity] = review["to_state"]
            review_ids.add(review["review_id"])
            audit.append(deepcopy(review))
        return states, audit, feature_by_id
