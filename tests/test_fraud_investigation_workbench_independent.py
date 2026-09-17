"""Independent checks of temporal boundaries, label isolation and model authority."""
from copy import deepcopy
import unittest
from projects.fraud_investigation_workbench.project import default_input,run

class FraudIndependentTests(unittest.TestCase):
    def window(self,last):
        return {'entities':[{'id':'A','kind':'account'},{'id':'B','kind':'merchant'}],'transactions':[{'id':'T'+str(i),'from':'A','to':'B','amount':1,'timestamp':time} for i,time in enumerate(['2026-09-01T00:00:00Z','2026-09-01T00:20:00+00:00','2026-09-01T01:40:00+01:00',last])],'review_threshold':1}

    def test_rolling_window_inclusive_boundary_and_timezone(self):
        result=run(self.window('2026-09-01T01:00:00Z'))['details']
        entity=next(e for e in result['entities'] if e['entity_id']=='A')
        self.assertEqual(entity['max_outgoing_per_hour'],4)
        result=run(self.window('2026-09-01T01:00:01Z'))['details']
        entity=next(e for e in result['entities'] if e['entity_id']=='A')
        self.assertEqual(entity['max_outgoing_per_hour'],3)

    def test_labels_do_not_change_scores_revision_or_case_states(self):
        payload=default_input();original=run(payload)['details'];payload['ground_truth']={key:not value for key,value in payload['ground_truth'].items()};changed=run(payload)['details']
        self.assertEqual(original['entities'],changed['entities'])
        self.assertEqual(original['activity_revision'],changed['activity_revision'])
        self.assertEqual(original['case_states'],changed['case_states'])

    def test_model_cannot_borrow_another_entity_evidence(self):
        payload=default_input();cases=[e for e in run(payload)['details']['entities'] if e['review_required']]
        first,second=cases[0],cases[1]
        class Model:
            def generate_json(self,**kwargs):return {'summaries':[{'entity_id':first['entity_id'],'hypothesis':'Review only.','evidence_ids':[second['indicators'][0]['id']]}]}
        with self.assertRaises(ValueError):run(payload,Model())

    def test_terminal_case_cannot_be_reopened(self):
        payload=default_input();result=run(payload)['details'];entity=next(e for e in result['entities'] if e['review_required']);base={'entity_id':entity['entity_id'],'reviewer':'Synthetic reviewer','rationale':'Reviewed original source evidence.','evidence_ids':[entity['indicators'][0]['id']],'expected_revision':result['activity_revision']}
        payload['case_reviews']=[{**base,'review_id':'R1','from_state':'new','to_state':'triaged'},{**base,'review_id':'R2','from_state':'triaged','to_state':'closed_no_issue'},{**base,'review_id':'R3','from_state':'closed_no_issue','to_state':'investigating'}]
        with self.assertRaises(ValueError):run(payload)

    def test_additional_personal_trait_is_rejected(self):
        payload=default_input();payload['entities'][0]['nationality']='invented'
        with self.assertRaises(ValueError):run(payload)
