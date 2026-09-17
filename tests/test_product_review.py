"""Independent Staff Engineer review: temporal ML, labels, evidence and case authority."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib
import json
import unittest
from app.ai.model import TemporalModelTrainer,FEATURES
from projects.fraud_investigation_workbench.project import META,default_input,run

class IndependentFraudProductReview(unittest.TestCase):
    def trained(self):return deepcopy(next(row['payload'] for row in META['demo_inputs'] if 'training_examples' in row['payload']))

    def test_model_artifact_digest_is_recomputable(self):
        model=run(self.trained())['details']['behavioral_model'];artifact=dict(model['artifact']);digest=artifact.pop('sha256')
        self.assertEqual(digest,hashlib.sha256(json.dumps(artifact,sort_keys=True).encode()).hexdigest())
        self.assertEqual(tuple(artifact['feature_order']),FEATURES)

    def test_timezone_equivalent_training_instants_are_not_distinct(self):
        p=self.trained();instant=datetime.fromisoformat(p['training_examples'][0]['observed_at'].replace('Z','+00:00'))
        equivalent=instant.astimezone(timezone(timedelta(hours=1))).isoformat()
        p['training_examples'][1]['observed_at']=equivalent
        with self.assertRaisesRegex(ValueError,'unique'):run(p)

    def test_snapshot_at_exact_activity_start_is_future_leakage(self):
        p=self.trained();p['training_examples'][-1]['observed_at']=min(row['timestamp'] for row in p['transactions'])
        with self.assertRaisesRegex(ValueError,'precede'):run(p)

    def test_validation_labels_cannot_change_fitted_coefficients(self):
        p=self.trained();before=run(p)['details']['behavioral_model'];ordered=sorted(p['training_examples'],key=lambda row:row['observed_at']);n=len(ordered)
        for row in ordered[int(n*.6):int(n*.8)]:row['label']=not row['label']
        after=run(p)['details']['behavioral_model']
        for key in ['means','scales','weights','intercept']:
            self.assertEqual(before['artifact'][key],after['artifact'][key])
        self.assertNotEqual(before['validation_threshold_curve'],after['validation_threshold_curve'])

    def test_current_ground_truth_does_not_leak_to_narrative_context(self):
        p=self.trained()
        class Context:
            def generate_json(self,**kw):self.request=kw;return {'summaries':[]}
        context=Context();run(p,context)
        self.assertEqual(set(context.request['data']),{'cases','case_states'})
        self.assertNotIn('ground_truth',str(context.request));self.assertNotIn('training_examples',str(context.request))
        self.assertTrue(all(row['review_required'] for row in context.request['data']['cases']))

    def test_generative_narrative_cannot_cite_other_entities_evidence(self):
        p=default_input()
        class Context:
            def generate_json(self,**kw):
                first,second=kw['data']['cases'][:2]
                return {'summaries':[{'entity_id':first['entity_id'],'hypothesis':'Needs review','evidence_ids':[second['indicators'][0]['id']]}]}
        with self.assertRaisesRegex(ValueError,'same entity'):run(p,Context())

    def test_model_does_not_change_simulated_case_revision_or_states(self):
        p=self.trained();trained=run(p)['details'];p.pop('training_examples');plain=run(p)['details']
        self.assertEqual(trained['activity_revision'],plain['activity_revision'])
        self.assertEqual(trained['case_states'],plain['case_states'])
        self.assertEqual(trained['entities'],plain['entities'])

    def test_invalid_training_is_rejected_before_optional_narrative(self):
        p=self.trained();p['training_examples'][0]['features']['velocity']=float('inf')
        class Context:
            def generate_json(self,**kw):raise AssertionError('Malformed training reached provider')
        with self.assertRaises(ValueError):run(p,Context())

if __name__=='__main__':unittest.main()
