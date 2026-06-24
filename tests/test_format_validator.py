"""test_format_validator.py — 12 tests for FormatValidator."""

import pytest
from src.evaluators.format_validator import FormatValidator


class TestFormatValidator:

    def test_valid_json_passes(self, fmt):
        result = fmt.validate_json('{"name": "Alice", "score": 95}')
        assert result.passed
        assert result.score == 1.0

    def test_invalid_json_fails(self, fmt):
        result = fmt.validate_json("This is plain text, not JSON.")
        assert not result.passed
        assert result.score == 0.0

    def test_json_keys_all_present_passes(self, fmt):
        result = fmt.validate_json_keys(
            '{"name": "Alice", "score": 95}',
            required_keys=["name", "score"]
        )
        assert result.passed
        assert result.score == 1.0

    def test_json_keys_missing_key_fails(self, fmt):
        result = fmt.validate_json_keys(
            '{"name": "Alice"}',
            required_keys=["name", "score"]
        )
        assert not result.passed
        assert "score" in result.details["missing"]

    def test_list_with_items_passes(self, fmt):
        result = fmt.validate_list(
            "1. Python\n2. JavaScript\n3. Java", min_items=3
        )
        assert result.passed

    def test_list_too_few_items_fails(self, fmt):
        result = fmt.validate_list("Only one item.", min_items=3)
        assert not result.passed

    def test_length_within_bounds_passes(self, fmt):
        result = fmt.validate_length("Hello world", min_chars=5, max_chars=100)
        assert result.passed

    def test_length_too_short_fails(self, fmt):
        result = fmt.validate_length("Hi", min_chars=10, max_chars=100)
        assert not result.passed

    def test_length_too_long_fails(self, fmt):
        result = fmt.validate_length("a" * 200, min_chars=0, max_chars=50)
        assert not result.passed

    def test_keyword_all_present_passes(self, fmt):
        result = fmt.validate_keyword(
            "Python is a great programming language.",
            keywords=["python", "programming", "language"]
        )
        assert result.passed
        assert result.score == 1.0

    def test_keyword_missing_fails(self, fmt):
        result = fmt.validate_keyword("Java is verbose.", keywords=["python"])
        assert not result.passed

    def test_no_markdown_clean_text_passes(self, fmt):
        result = fmt.validate_no_markdown("The capital of France is Paris.")
        assert result.passed
