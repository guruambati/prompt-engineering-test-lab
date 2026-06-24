"""
format_validator.py
===================
FormatValidator — checks that prompt outputs conform to expected formats.

Validators:
  validate_json()        : output is parseable JSON
  validate_json_keys()   : JSON contains required keys
  validate_list()        : output is a numbered or bulleted list
  validate_length()      : output length within [min, max]
  validate_keyword()     : output contains required keywords
  validate_single_word() : output is exactly one word (for classification)
  validate_no_markdown() : output contains no raw markdown syntax
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class EvalResult:
    check_name: str
    passed:     bool
    score:      float          # 0.0–1.0
    message:    str
    details:    dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.passed

    def __repr__(self) -> str:
        return (f"EvalResult({self.check_name}, "
                f"passed={self.passed}, score={self.score:.2f})")


class FormatValidator:

    def validate_json(self, output: str) -> EvalResult:
        """Output must be valid parseable JSON."""
        try:
            parsed = json.loads(output.strip())
            return EvalResult(
                check_name = "format_json",
                passed     = True,
                score      = 1.0,
                message    = "Output is valid JSON",
                details    = {"keys": list(parsed.keys())
                              if isinstance(parsed, dict) else []},
            )
        except json.JSONDecodeError as exc:
            return EvalResult(
                check_name = "format_json",
                passed     = False,
                score      = 0.0,
                message    = f"Invalid JSON: {exc}",
                details    = {"raw_output": output[:100]},
            )

    def validate_json_keys(self, output: str,
                            required_keys: list[str]) -> EvalResult:
        """JSON output contains all required keys."""
        try:
            parsed  = json.loads(output.strip())
        except json.JSONDecodeError:
            return EvalResult("format_json_keys", False, 0.0,
                              "Output is not valid JSON")

        missing = [k for k in required_keys if k not in parsed]
        score   = 1.0 - len(missing) / len(required_keys) if required_keys else 1.0
        passed  = len(missing) == 0

        return EvalResult(
            check_name = "format_json_keys",
            passed     = passed,
            score      = round(score, 4),
            message    = "All required keys present" if passed
                         else f"Missing keys: {missing}",
            details    = {"required": required_keys, "missing": missing},
        )

    def validate_list(self, output: str,
                       min_items: int = 2) -> EvalResult:
        """Output is a list with at least min_items items."""
        lines = [
            l.strip() for l in output.split("\n")
            if re.match(r'^(\d+[\.\)]\s|[-•*]\s|\-\s)', l.strip())
        ]
        # Fallback: count non-empty lines if no list markers found
        if not lines:
            lines = [l for l in output.split("\n") if l.strip()]

        passed = len(lines) >= min_items
        return EvalResult(
            check_name = "format_list",
            passed     = passed,
            score      = min(len(lines) / max(min_items, 1), 1.0),
            message    = f"List has {len(lines)} item(s) (min {min_items})",
            details    = {"item_count": len(lines), "min_items": min_items},
        )

    def validate_length(self, output: str,
                         min_chars: int = 0,
                         max_chars: int = 10000) -> EvalResult:
        """Output length is within [min_chars, max_chars]."""
        length = len(output)
        passed = min_chars <= length <= max_chars
        score  = 1.0 if passed else 0.0

        return EvalResult(
            check_name = "format_length",
            passed     = passed,
            score      = score,
            message    = (
                f"Length {length} in [{min_chars}, {max_chars}]"
                if passed else
                f"Length {length} outside [{min_chars}, {max_chars}]"
            ),
            details    = {"length": length, "min": min_chars, "max": max_chars},
        )

    def validate_keyword(self, output: str,
                          keywords: list[str],
                          case_sensitive: bool = False) -> EvalResult:
        """Output contains all required keywords."""
        haystack = output if case_sensitive else output.lower()
        needles  = keywords if case_sensitive else [k.lower() for k in keywords]
        missing  = [k for k in needles if k not in haystack]
        score    = 1.0 - len(missing) / len(keywords) if keywords else 1.0
        passed   = len(missing) == 0

        return EvalResult(
            check_name = "format_keyword",
            passed     = passed,
            score      = round(score, 4),
            message    = "All keywords found" if passed
                         else f"Missing keywords: {missing}",
            details    = {"missing": missing},
        )

    def validate_single_word(self, output: str,
                              allowed: set[str] | None = None) -> EvalResult:
        """Output is a single word (optionally from an allowed set)."""
        word   = output.strip().lower()
        words  = word.split()
        is_one = len(words) == 1

        in_set = True
        if allowed and is_one:
            in_set = word in {a.lower() for a in allowed}

        passed = is_one and in_set
        return EvalResult(
            check_name = "format_single_word",
            passed     = passed,
            score      = 1.0 if passed else 0.0,
            message    = (
                f"Single word '{word}' in allowed set" if passed else
                f"{'Multiple words' if not is_one else f'Word {word!r} not in allowed set {allowed}'}"
            ),
            details    = {"word": word, "allowed": list(allowed) if allowed else []},
        )

    def validate_no_markdown(self, output: str) -> EvalResult:
        """Output contains no raw markdown syntax."""
        _MD_PATTERNS = [
            r"\*\*.*?\*\*",   # bold
            r"\*.*?\*",       # italic
            r"#{1,6}\s",      # headings
            r"```",           # code blocks
            r"\[.*?\]\(.*?\)",# links
        ]
        found = []
        for pattern in _MD_PATTERNS:
            if re.search(pattern, output):
                found.append(pattern)

        passed = len(found) == 0
        return EvalResult(
            check_name = "format_no_markdown",
            passed     = passed,
            score      = 1.0 if passed else 0.0,
            message    = "No markdown detected" if passed
                         else f"Markdown patterns found: {found}",
            details    = {"patterns_found": found},
        )
