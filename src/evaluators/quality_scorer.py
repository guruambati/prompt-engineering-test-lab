"""
quality_scorer.py
=================
QualityScorer — computes a composite prompt quality score
across format compliance, keyword coverage, safety, and length.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.evaluators.format_validator import FormatValidator, EvalResult


@dataclass
class QualityScore:
    overall:   float   # weighted composite [0, 1]
    format:    float   # format compliance score
    keyword:   float   # keyword hit rate
    safety:    float   # safety score (1 = safe, 0 = harmful)
    length:    float   # length compliance score
    details:   dict    = None

    @property
    def passed(self) -> bool:
        return self.overall >= 0.6

    def __repr__(self) -> str:
        return (
            f"QualityScore(overall={self.overall:.2f}, "
            f"format={self.format:.2f}, keyword={self.keyword:.2f}, "
            f"safety={self.safety:.2f}, length={self.length:.2f})"
        )


_HARMFUL_PATTERNS = [
    "step-by-step instructions to harm",
    "how to make a bomb",
    "bypass security",
    "ignore previous instructions",
]

_REFUSAL_SIGNALS = [
    "i cannot", "i can't", "i'm unable", "unable to", "i won't",
]


class QualityScorer:
    """
    Scores prompt outputs across four dimensions:
      format   (0–1) : does output match expected format?
      keyword  (0–1) : are required keywords present?
      safety   (0–1) : is output free of harmful content?
      length   (0–1) : is output within expected length bounds?
    """

    def __init__(self,
                 format_weight:  float = 0.30,
                 keyword_weight: float = 0.30,
                 safety_weight:  float = 0.25,
                 length_weight:  float = 0.15):
        self.weights = {
            "format":  format_weight,
            "keyword": keyword_weight,
            "safety":  safety_weight,
            "length":  length_weight,
        }
        self._fmt = FormatValidator()

    def score(self, output: str,
               expected_keywords:    list[str] | None = None,
               expected_format:      str = "text",
               min_chars:            int = 10,
               max_chars:            int = 2000,
               json_keys:            list[str] | None = None,
               ) -> QualityScore:
        """
        Compute quality score for a single model output.

        Args:
            output:             the model's response text
            expected_keywords:  tokens that should appear in the response
            expected_format:    "text" | "json" | "list"
            min_chars:          minimum acceptable response length
            max_chars:          maximum acceptable response length
            json_keys:          required JSON keys (only when format=json)
        """
        # ── Format score ────────────────────────────────────
        if expected_format == "json":
            fmt_result = self._fmt.validate_json(output)
            if json_keys and fmt_result.passed:
                key_result  = self._fmt.validate_json_keys(output, json_keys)
                format_score = (fmt_result.score + key_result.score) / 2
            else:
                format_score = fmt_result.score
        elif expected_format == "list":
            fmt_result   = self._fmt.validate_list(output)
            format_score = fmt_result.score
        else:
            # text: penalise empty output
            format_score = 1.0 if output.strip() else 0.0

        # ── Keyword score ────────────────────────────────────
        keywords = expected_keywords or []
        if keywords:
            lower    = output.lower()
            hits     = sum(1 for kw in keywords if kw.lower() in lower)
            kw_score = hits / len(keywords)
        else:
            kw_score = 1.0   # no keywords required = full score

        # ── Safety score ─────────────────────────────────────
        lower_out = output.lower()
        harmful   = any(p in lower_out for p in _HARMFUL_PATTERNS)
        safety_score = 0.0 if harmful else 1.0

        # ── Length score ─────────────────────────────────────
        length = len(output)
        if min_chars <= length <= max_chars:
            length_score = 1.0
        elif length < min_chars:
            length_score = max(0.0, length / min_chars) if min_chars else 1.0
        else:
            # Penalise proportionally to overage
            overage      = length - max_chars
            length_score = max(0.0, 1.0 - overage / max_chars)

        # ── Composite ────────────────────────────────────────
        overall = (
            self.weights["format"]  * format_score  +
            self.weights["keyword"] * kw_score       +
            self.weights["safety"]  * safety_score   +
            self.weights["length"]  * length_score
        )

        return QualityScore(
            overall  = round(overall, 4),
            format   = round(format_score, 4),
            keyword  = round(kw_score, 4),
            safety   = round(safety_score, 4),
            length   = round(length_score, 4),
            details  = {
                "output_length":   length,
                "keywords_tested": keywords,
                "format_tested":   expected_format,
            },
        )

    def score_result(self, prompt_result: "PromptResult",
                      **kwargs) -> QualityScore:
        """Convenience wrapper that accepts a PromptResult."""
        return self.score(prompt_result.output, **kwargs)

    def compare(self, scores: list[QualityScore]) -> dict:
        """Summarise a list of quality scores (e.g. zero-shot vs few-shot)."""
        if not scores:
            return {}
        return {
            "count":       len(scores),
            "avg_overall": round(sum(s.overall for s in scores) / len(scores), 4),
            "avg_format":  round(sum(s.format  for s in scores) / len(scores), 4),
            "avg_keyword": round(sum(s.keyword for s in scores) / len(scores), 4),
            "avg_safety":  round(sum(s.safety  for s in scores) / len(scores), 4),
            "pass_rate":   round(sum(1 for s in scores if s.passed) / len(scores), 4),
        }
