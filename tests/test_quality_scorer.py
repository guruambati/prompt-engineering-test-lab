"""test_quality_scorer.py — 10 tests for QualityScorer."""

import pytest
from src.evaluators.quality_scorer import QualityScorer, QualityScore


class TestQualityScorer:

    def test_perfect_text_response_scores_high(self, quality):
        score = quality.score(
            "Python is a high-level programming language created by Guido.",
            expected_keywords=["python", "programming", "language"],
            expected_format="text",
            min_chars=10,
        )
        assert score.overall >= 0.7
        assert score.passed

    def test_valid_json_format_scores_high(self, quality):
        score = quality.score(
            '{"answer": "mock response", "confidence": 0.95}',
            expected_format="json",
            json_keys=["answer", "confidence"],
        )
        assert score.format >= 0.8

    def test_invalid_json_format_scores_zero(self, quality):
        score = quality.score(
            "This is plain text, not JSON.",
            expected_format="json",
        )
        assert score.format == 0.0

    def test_missing_keywords_reduces_score(self, quality):
        score_with = quality.score(
            "Python is a programming language.",
            expected_keywords=["python", "programming"],
        )
        score_without = quality.score(
            "Java is a compiled language.",
            expected_keywords=["python", "programming"],
        )
        assert score_with.keyword > score_without.keyword

    def test_empty_output_scores_zero_format(self, quality):
        score = quality.score("", expected_format="text")
        assert score.format == 0.0

    def test_safety_score_one_for_safe_output(self, quality):
        score = quality.score("Paris is the capital of France.")
        assert score.safety == 1.0

    def test_length_score_one_within_bounds(self, quality):
        score = quality.score(
            "A response of reasonable length here.",
            min_chars=10,
            max_chars=500,
        )
        assert score.length == 1.0

    def test_length_score_penalised_for_short(self, quality):
        score = quality.score("Hi", min_chars=100, max_chars=500)
        assert score.length < 1.0

    def test_overall_score_in_range(self, quality):
        score = quality.score("any response")
        assert 0.0 <= score.overall <= 1.0

    def test_compare_returns_summary(self, quality):
        scores = [
            quality.score("Python is a programming language.", expected_keywords=["python"]),
            quality.score("Java is compiled.", expected_keywords=["python"]),
        ]
        summary = quality.compare(scores)
        assert "avg_overall" in summary
        assert "pass_rate"   in summary
        assert summary["count"] == 2
