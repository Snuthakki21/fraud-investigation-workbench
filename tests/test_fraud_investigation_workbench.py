from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
from projects.fraud_investigation_workbench.project import default_input, run


def find_entity(result, entity_id):
    return next(x for x in result["details"]["entities"] if x["entity_id"] == entity_id)


def review_event(result, entity="HUB", from_state="new", to_state="triaged", index=1):
    return {"review_id": f"REVIEW-{index}", "entity_id": entity, "from_state": from_state, "to_state": to_state, "reviewer": "Synthetic analyst", "rationale": "Inspect activity against legitimate business context.", "evidence_ids": [find_entity(result, entity)["indicators"][0]["id"]], "expected_revision": result["details"]["activity_revision"]}


class FraudInvestigationTests(unittest.TestCase):
    def test_seeded_indicators_and_measured_false_positives(self):
        result = run(default_input())
        evaluation = result["details"]["evaluation"]
        self.assertEqual(evaluation["true_positives"], 4)
        self.assertEqual(evaluation["false_positives"], 3)
        self.assertEqual(evaluation["false_negatives"], 1)
        self.assertAlmostEqual(evaluation["precision"], 4 / 7)
        self.assertAlmostEqual(evaluation["recall"], .8)
        self.assertEqual(result["details"]["case_states"]["HUB"], "new")
        self.assertEqual(len(result["details"]["cycles"]), 2)

    def test_higher_threshold_changes_precision_recall_tradeoff(self):
        data = default_input()
        data["review_threshold"] = 75
        result = run(data)["details"]
        self.assertEqual(set(result["case_states"]), {"HUB"})
        self.assertEqual(result["evaluation"]["precision"], 1)
        self.assertEqual(result["evaluation"]["recall"], .2)

    def test_labels_do_not_leak_into_detection(self):
        data = default_input()
        before = run(data)
        data["ground_truth"] = {key: not value for key, value in data["ground_truth"].items()}
        after = run(data)
        self.assertEqual(before["details"]["entities"], after["details"]["entities"])
        self.assertNotEqual(before["details"]["evaluation"], after["details"]["evaluation"])

    def test_unlabeled_data_has_no_invented_metrics(self):
        data = default_input()
        data.pop("ground_truth")
        result = run(data)
        self.assertFalse(result["details"]["evaluation"]["available"])
        self.assertFalse(any("precision" in metric["label"] for metric in result["metrics"]))

    def test_no_predictions_produces_undefined_precision(self):
        data = default_input()
        data["review_threshold"] = 100
        result = run(data)["details"]
        self.assertEqual(result["case_states"], {})
        self.assertIsNone(result["evaluation"]["precision"])
        self.assertEqual(result["evaluation"]["recall"], 0)

    def test_no_positive_labels_produces_undefined_recall(self):
        data = default_input()
        data["ground_truth"] = {key: False for key in data["ground_truth"]}
        self.assertIsNone(run(data)["details"]["evaluation"]["recall"])

    def test_breaking_graph_edge_removes_ring_cycle(self):
        data = default_input()
        data["transactions"] = [x for x in data["transactions"] if not (x["from"] == "RING-C" and x["to"] == "RING-A")]
        result = run(data)
        self.assertEqual(len(result["details"]["cycles"]), 1)
        self.assertFalse(find_entity(result, "RING-A")["review_required"])

    def test_velocity_is_a_rolling_hour_not_total_count(self):
        data = default_input()
        stamp = datetime(2026, 9, 1, tzinfo=timezone.utc)
        for i, tx in enumerate(data["transactions"]):
            tx["timestamp"] = (stamp + timedelta(hours=i * 2)).isoformat()
        result = run(data)
        self.assertEqual(find_entity(result, "RING-A")["max_outgoing_per_hour"], 1)
        self.assertFalse(find_entity(result, "RING-A")["review_required"])

    def test_outgoing_before_receipts_is_not_pass_through(self):
        data = default_input()
        for tx in data["transactions"]:
            if tx["from"] == "HUB":
                tx["timestamp"] = "2026-08-30T00:00:00Z"
        result = run(data)
        self.assertFalse(any(x["id"].endswith(":pass-through") for x in find_entity(result, "HUB")["indicators"]))

    def test_human_review_valid_transitions_and_rationale(self):
        data = default_input()
        result = run(data)
        data["case_reviews"] = [review_event(result), review_event(result, from_state="triaged", to_state="investigating", index=2), review_event(result, from_state="investigating", to_state="escalated", index=3)]
        after = run(data)["details"]
        self.assertEqual(after["case_states"]["HUB"], "escalated")
        self.assertEqual(len(after["review_audit"]), 3)

    def test_human_can_close_no_issue_only_after_triage(self):
        data = default_input()
        result = run(data)
        data["case_reviews"] = [review_event(result, entity="CLEAR-A"), review_event(result, entity="CLEAR-A", from_state="triaged", to_state="closed_no_issue", index=2)]
        self.assertEqual(run(data)["details"]["case_states"]["CLEAR-A"], "closed_no_issue")

    def test_invalid_review_cannot_skip_triage(self):
        data = default_input()
        data["case_reviews"] = [review_event(run(data), to_state="closed_no_issue")]
        with self.assertRaises(ValueError):
            run(data)

    def test_review_rejects_stale_evidence_revision(self):
        data = default_input()
        data["case_reviews"] = [review_event(run(data))]
        data["transactions"][0]["amount"] += 1
        with self.assertRaises(ValueError):
            run(data)

    def test_review_rejects_other_entity_evidence(self):
        data = default_input()
        event = review_event(run(data))
        event["evidence_ids"] = ["RING-A:cycle"]
        data["case_reviews"] = [event]
        with self.assertRaises(ValueError):
            run(data)

    def test_duplicate_review_event_rejected(self):
        data = default_input()
        event = review_event(run(data))
        data["case_reviews"] = [event, deepcopy(event)]
        with self.assertRaises(ValueError):
            run(data)

    def test_model_can_only_summarize_flagged_entity_evidence(self):
        class Context:
            def generate_json(self, **kwargs):
                case = kwargs["data"]["cases"][0]
                return {"summaries": [{"entity_id": case["entity_id"], "hypothesis": "Check whether activity has a legitimate operational explanation.", "evidence_ids": [case["indicators"][0]["id"]]}]}
        result = run(default_input(), Context())
        self.assertTrue(result["details"]["model_used"])
        self.assertEqual(set(result["details"]["case_states"].values()), {"new"})

    def test_model_rejects_fabricated_or_cross_entity_evidence(self):
        for entity, evidence in (("SINGLE", "SINGLE:fake"), ("HUB", "RING-A:cycle")):
            class Context:
                def generate_json(self, **kwargs):
                    return {"summaries": [{"entity_id": entity, "hypothesis": "Review this case", "evidence_ids": [evidence]}]}
            with self.assertRaises(ValueError):
                run(default_input(), Context())

    def test_model_failure_does_not_turn_into_case_action(self):
        class Context:
            def generate_json(self, **kwargs):
                raise ValueError("Provider unavailable")
        data = default_input()
        with self.assertRaises(ValueError):
            run(data, Context())
        self.assertEqual(data["case_reviews"], [])

    def test_invalid_input_boundaries(self):
        mutations = [
            lambda d: d.update(entities=[]),
            lambda d: d["entities"][0].update(age=30),
            lambda d: d["entities"].append(dict(d["entities"][0])),
            lambda d: d.update(transactions=[]),
            lambda d: d["transactions"][0].update(note="unsupported"),
            lambda d: d["transactions"][1].update(id=d["transactions"][0]["id"]),
            lambda d: d["transactions"][0].update(to="UNKNOWN"),
            lambda d: d["transactions"][0].update(to=d["transactions"][0]["from"]),
            lambda d: d["transactions"][0].update(amount=float("nan")),
            lambda d: d["transactions"][0].update(amount=10**400),
            lambda d: d["transactions"][0].update(amount=-1),
            lambda d: d["transactions"][0].update(amount=.001),
            lambda d: d["transactions"][0].update(timestamp="2026-09-01T09:00:00"),
            lambda d: d.update(review_threshold=True),
            lambda d: d.update(case_reviews={}),
            lambda d: d.update(ground_truth={"UNKNOWN": True}),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)):
                data = default_input()
                mutate(data)
                with self.assertRaises(ValueError):
                    run(data)
        with self.assertRaises(ValueError):
            run([])


    def test_human_review_requires_nonempty_rationale(self):
        data = default_input()
        event = review_event(run(data))
        event["rationale"] = ""
        data["case_reviews"] = [event]
        with self.assertRaises(ValueError):
            run(data)

    def test_local_context_none_has_no_model_claim(self):
        class Context:
            def generate_json(self, **kwargs):
                return None
        self.assertFalse(run(default_input(), Context())["details"]["model_used"])

    def test_model_summary_shape_is_checked(self):
        class Context:
            def generate_json(self, **kwargs):
                return {"summaries": "not-an-array"}
        with self.assertRaises(ValueError):
            run(default_input(), Context())


if __name__ == "__main__":
    unittest.main()
