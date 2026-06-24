"""conftest.py — shared fixtures for prompt engineering test lab."""

import pytest
from src.prompts.templates         import (
    PromptTemplate, ShotType,
    zero_shot_qa, one_shot_qa, few_shot_json, classification_prompt
)
from src.prompts.injection_cases   import (
    ALL_INJECTION_CASES, MALICIOUS_CASES, SAFE_CASES
)
from src.runner.prompt_runner      import MockLlm, PromptRunner
from src.evaluators.format_validator   import FormatValidator
from src.evaluators.consistency_scorer import ConsistencyScorer
from src.evaluators.injection_detector import InjectionDetector
from src.evaluators.quality_scorer     import QualityScorer


# ── LLM + runner ─────────────────────────────────────────────

@pytest.fixture
def mock_llm():
    return MockLlm(seed=42, latency_ms=1.0)

@pytest.fixture
def runner(mock_llm):
    return PromptRunner(mock_llm, model_name="mock-llm")


# ── Templates ─────────────────────────────────────────────────

@pytest.fixture
def zero_shot():
    return zero_shot_qa()

@pytest.fixture
def one_shot():
    return one_shot_qa(
        example=("What is the capital of France?", "Paris."),
    )

@pytest.fixture
def few_shot():
    return few_shot_json(examples=[
        ("Capital of France?",  '{"capital": "Paris"}'),
        ("Capital of Germany?", '{"capital": "Berlin"}'),
        ("Capital of Japan?",   '{"capital": "Tokyo"}'),
    ])

@pytest.fixture
def classify():
    return classification_prompt(
        labels=["positive", "negative", "neutral"],
        examples=[
            ("I love this product!", "positive"),
            ("Terrible experience.", "negative"),
        ],
    )


# ── Evaluators ────────────────────────────────────────────────

@pytest.fixture
def fmt():
    return FormatValidator()

@pytest.fixture
def consistency():
    return ConsistencyScorer(min_jaccard=0.7)

@pytest.fixture
def detector():
    return InjectionDetector()

@pytest.fixture
def quality():
    return QualityScorer()


# ── Rendered prompts ──────────────────────────────────────────

@pytest.fixture
def zero_rendered(zero_shot):
    return zero_shot.render(question="What is Python?")

@pytest.fixture
def few_rendered(few_shot):
    return few_shot.render(question="Capital of Spain?")
