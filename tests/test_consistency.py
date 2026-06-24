"""test_consistency.py — 10 tests for ConsistencyScorer."""

import pytest
from src.evaluators.consistency_scorer import ConsistencyScorer, ConsistencyReport


class TestConsistency:

    def test_identical_outputs_score_one(self, consistency):
        outputs = ["Paris is the capital of France."] * 5
        report  = consistency.score(outputs)
        assert report.exact_match_rate == 1.0
        assert report.avg_jaccard      == 1.0

    def test_completely_different_outputs_low_score(self, consistency):
        outputs = [
            "Python is a programming language.",
            "The weather in Tokyo is sunny.",
            "Kubernetes orchestrates containers.",
        ]
        report = consistency.score(outputs)
        assert report.avg_jaccard < 0.5

    def test_single_output_perfect_score(self, consistency):
        report = consistency.score(["Only one output."])
        assert report.exact_match_rate == 1.0
        assert report.n_runs           == 1

    def test_empty_outputs_returns_zeros(self, consistency):
        report = consistency.score([])
        assert report.exact_match_rate == 0.0
        assert report.n_runs           == 0

    def test_n_runs_reflects_input(self, consistency):
        outputs = ["response"] * 7
        report  = consistency.score(outputs)
        assert report.n_runs == 7

    def test_overall_score_in_range(self, consistency):
        outputs = ["A response here.", "A similar response.", "Another answer."]
        report  = consistency.score(outputs)
        assert 0.0 <= report.overall_score <= 1.0

    def test_is_consistent_true_for_identical(self, consistency):
        outputs = ["Same text."] * 5
        report  = consistency.score(outputs)
        assert report.is_consistent

    def test_eval_result_passed_for_high_consistency(self, consistency):
        outputs  = ["The capital of France is Paris."] * 5
        report   = consistency.score(outputs)
        eval_res = consistency.to_eval_result(report)
        assert eval_res.passed
        assert eval_res.score >= 0.7

    def test_eval_result_failed_for_low_consistency(self):
        scorer  = ConsistencyScorer(min_jaccard=0.99)
        outputs = ["cats", "dogs", "birds", "fish", "snakes"]
        report  = scorer.score(outputs)
        eval_res = scorer.to_eval_result(report)
        assert not eval_res.passed

    def test_length_cv_zero_for_uniform_outputs(self, consistency):
        outputs = ["abc"] * 5
        report  = consistency.score(outputs)
        assert report.length_cv == 0.0
