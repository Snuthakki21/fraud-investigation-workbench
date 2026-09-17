"""Leakage, reproducibility and explanation tests for the behavioral model."""
from copy import deepcopy
from datetime import datetime, timezone
import math
import unittest
from app.ai.model import TemporalModelTrainer, sigmoid, FEATURES
from app.application.product import ProductApplication
from projects.fraud_investigation_workbench.project import META,default_input,run

class BehavioralModelTests(unittest.TestCase):
    def scenario(self):return deepcopy(META['demo_inputs'][0]['payload'])

    def test_chronological_partitions_are_disjoint_and_ordered(self):
        result=run(self.scenario())['details']['behavioral_model'];split=result['split']
        self.assertEqual([split[name]['samples'] for name in ['train','validation','test']],[48,16,16])
        self.assertLess(split['train']['last_timestamp'],split['validation']['first_timestamp']);self.assertLess(split['validation']['last_timestamp'],split['test']['first_timestamp'])
        self.assertFalse(set(split['train']['ids']) & set(split['test']['ids']))
        self.assertEqual(len(set(sum([s['ids'] for s in split.values()],[]))),80)

    def test_held_out_labels_do_not_change_model_or_selected_threshold(self):
        data=self.scenario();before=run(data)['details']['behavioral_model']
        for row in data['training_examples'][64:]:row['label']=not row['label']
        after=run(data)['details']['behavioral_model']
        self.assertEqual(before['artifact'],after['artifact']);self.assertEqual(before['entity_scores'],after['entity_scores']);self.assertNotEqual(before['held_out_test'],after['held_out_test'])

    def test_held_out_features_do_not_change_training_scaler(self):
        data=self.scenario();before=run(data)['details']['behavioral_model']['artifact']
        for row in data['training_examples'][64:]:row['features']['velocity']=1000
        after=run(data)['details']['behavioral_model']['artifact']
        self.assertEqual(before,after)

    def test_current_labels_never_enter_classifier_or_case_scores(self):
        data=self.scenario();before=run(data)['details']
        data['ground_truth']={key:not value for key,value in data['ground_truth'].items()};after=run(data)['details']
        self.assertEqual(before['behavioral_model'],after['behavioral_model']);self.assertEqual(before['entities'],after['entities'])

    def test_train_only_means_match_raw_training_partition(self):
        data=self.scenario();model=run(data)['details']['behavioral_model']['artifact']
        expected=sum(row['features']['velocity'] for row in data['training_examples'][:48])/48
        self.assertAlmostEqual(model['means'][0],expected)

    def test_feature_contributions_reconstruct_scores(self):
        model=run(self.scenario())['details']['behavioral_model']
        for score in model['entity_scores']:
            reconstructed=sigmoid(score['intercept']+sum(score['contributions'].values()))
            self.assertAlmostEqual(reconstructed,score['model_score'],places=5)

    def test_model_scores_never_change_rule_case_state_machine(self):
        data=self.scenario();with_model=run(data)['details'];data.pop('training_examples');without=run(data)['details']
        self.assertEqual(with_model['case_states'],without['case_states']);self.assertEqual(with_model['entities'],without['entities'])
        self.assertFalse(without['behavioral_model']['available'])

    def test_test_confusion_matrix_and_brier_score_are_consistent(self):
        metric=run(self.scenario())['details']['behavioral_model']['held_out_test']
        self.assertEqual(sum(metric[k] for k in ['true_positives','false_positives','false_negatives','true_negatives']),metric['samples'])
        self.assertTrue(0<=metric['brier_score']<=1)

    def test_threshold_is_selected_only_from_validation_curve(self):
        result=run(self.scenario())['details']['behavioral_model']
        best=max(result['validation_threshold_curve'],key=lambda row:(row['f1'],row['precision'],row['threshold']))
        self.assertEqual(result['artifact']['threshold'],best['threshold'])

    def test_row_order_does_not_change_temporal_split_or_model(self):
        data=self.scenario();before=run(data)['details']['behavioral_model'];data['training_examples'].reverse()
        self.assertEqual(before,run(data)['details']['behavioral_model'])

    def test_no_silent_future_feature_leakage(self):
        data=self.scenario();data['training_examples'][-1]['observed_at']='2027-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'precede'):run(data)

    def test_identical_timestamps_cannot_cross_split_boundary(self):
        data=self.scenario();data['training_examples'][49]['observed_at']=data['training_examples'][47]['observed_at']
        with self.assertRaisesRegex(ValueError,'unique'):run(data)

    def test_single_class_training_is_rejected(self):
        data=self.scenario()
        for row in data['training_examples'][:48]:row['label']=True
        with self.assertRaisesRegex(ValueError,'both label classes'):run(data)

    def test_constant_features_produce_finite_repeatable_parameters(self):
        data=self.scenario()
        for row in data['training_examples']:
            row['features']={name:0 for name in FEATURES}
        artifact=run(data)['details']['behavioral_model']['artifact']
        self.assertTrue(all(math.isfinite(v) for v in artifact['weights']));self.assertTrue(all(v==1e-8 for v in artifact['scales']))

    def test_bad_training_shapes_and_values_are_rejected(self):
        edits=[lambda d:d.update(training_examples=[]),lambda d:d['training_examples'][0].update(label=1),lambda d:d['training_examples'][0].update(observed_at='2026-01-01'),lambda d:d['training_examples'][0].update(observed_at='invalid'),lambda d:d['training_examples'][0]['features'].update(velocity=float('nan')),lambda d:d['training_examples'][0]['features'].update(velocity=True),lambda d:d['training_examples'][0]['features'].update(velocity=1001),lambda d:d['training_examples'][0]['features'].update(protected_trait=0),lambda d:d['training_examples'][0].update(id=d['training_examples'][1]['id'])]
        for mutate in edits:
            data=self.scenario();mutate(data)
            with self.assertRaises(ValueError):run(data)

    def test_stable_sigmoid_for_extreme_log_odds(self):
        self.assertEqual(sigmoid(1000),1.0);self.assertLess(sigmoid(-1000),1e-100)

    def test_rule_threshold_tradeoff_queue_is_monotonic(self):
        result=run(default_input())['details']['threshold_comparison'];sizes=[row['queue_size'] for row in result]
        self.assertEqual(sizes,sorted(sizes,reverse=True))
        data=default_input();data.pop('ground_truth');self.assertEqual(run(data)['details']['threshold_comparison'],[])

    def test_application_is_repeatable_and_preserves_input(self):
        data=self.scenario();before=deepcopy(data);app=ProductApplication()
        self.assertEqual(app.run(data),app.run(data));self.assertEqual(data,before)

if __name__=='__main__':unittest.main()
