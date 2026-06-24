"""
consistency_scorer.py
=====================
ConsistencyScorer — measures how consistent a prompt's outputs are
across multiple runs.

A well-engineered prompt should produce semantically consistent outputs
every time it's run. High variance indicates the prompt is fragile.

Metrics:
  exact_match_rate()    : fraction of runs producing identical output
  jaccard_agreement()   : average pairwise Jaccard similarity
  length_variance()     : coefficient of variation of output lengths
"""

from __future__ import annotations

import re
import math
import statistics
from dataclasses import dataclass

from src.evaluators.format_validator import EvalResult


def _tokens(text: str) -> set[str]:
    return set(re.findall(r'\b[a-z0-9]+\b', text.lower()))


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class ConsistencyReport:
    exact_match_rate:  float   # fraction identical to first output
    avg_jaccard:       float   # average pairwise similarity
    length_cv:         float   # coefficient of variation of lengths
    n_runs:            int
    outputs:           list[str]

    @property
    def overall_score(self) -> float:
        """Composite consistency score in [0, 1]."""
        cv_score = max(0.0, 1.0 - self.length_cv)
        return round(
            0.4 * self.exact_match_rate +
            0.4 * self.avg_jaccard +
            0.2 * cv_score,
            4
        )

    @property
    def is_consistent(self) -> bool:
        return self.overall_score >= 0.7


class ConsistencyScorer:

    def __init__(self, min_jaccard: float = 0.7):
        self.min_jaccard = min_jaccard

    def score(self, outputs: list[str]) -> ConsistencyReport:
        """
        Compute consistency metrics across a list of outputs from
        repeated runs of the same prompt.
        """
        if not outputs:
            return ConsistencyReport(0.0, 0.0, 0.0, 0, [])

        if len(outputs) == 1:
            return ConsistencyReport(1.0, 1.0, 0.0, 1, outputs)

        # Exact match rate (vs first output)
        reference      = outputs[0]
        exact_matches  = sum(1 for o in outputs if o.strip() == reference.strip())
        exact_rate     = exact_matches / len(outputs)

        # Pairwise Jaccard
        pairs   = []
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                pairs.append(_jaccard(outputs[i], outputs[j]))
        avg_jac = sum(pairs) / len(pairs) if pairs else 1.0

        # Length coefficient of variation
        lengths = [len(o) for o in outputs]
        mean_l  = sum(lengths) / len(lengths)
        std_l   = math.sqrt(
            sum((l - mean_l) ** 2 for l in lengths) / len(lengths)
        )
        cv      = std_l / mean_l if mean_l > 0 else 0.0

        return ConsistencyReport(
            exact_match_rate = round(exact_rate, 4),
            avg_jaccard      = round(avg_jac, 4),
            length_cv        = round(cv, 4),
            n_runs           = len(outputs),
            outputs          = outputs,
        )

    def to_eval_result(self, report: ConsistencyReport) -> EvalResult:
        passed = report.overall_score >= self.min_jaccard
        return EvalResult(
            check_name = "consistency",
            passed     = passed,
            score      = report.overall_score,
            message    = (
                f"Consistency score {report.overall_score:.3f} "
                f"({'≥' if passed else '<'} threshold {self.min_jaccard})"
            ),
            details    = {
                "exact_match_rate": report.exact_match_rate,
                "avg_jaccard":      report.avg_jaccard,
                "length_cv":        report.length_cv,
                "n_runs":           report.n_runs,
            },
        )
