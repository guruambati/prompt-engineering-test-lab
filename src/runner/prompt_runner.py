"""
prompt_runner.py
================
PromptRunner — executes rendered prompts against an LLM backend.
MockLlm      — deterministic mock backend for testing (no API key needed).

MockLlm response logic:
  - Detects injection patterns → returns refusal
  - Detects JSON requests → returns JSON
  - Detects classification → returns label
  - Otherwise → returns general helpful response
"""

from __future__ import annotations

import re
import time
import random
from dataclasses import dataclass, field
from typing import Protocol

from src.prompts.templates import RenderedPrompt


# ── Result ─────────────────────────────────────────────────────

@dataclass
class PromptResult:
    prompt:      RenderedPrompt
    output:      str
    latency_ms:  float
    model:       str = "mock-llm"
    run_id:      int = 0

    @property
    def output_stripped(self) -> str:
        return self.output.strip()


# ── LLM Protocol ──────────────────────────────────────────────

class LlmBackend(Protocol):
    def complete(self, messages: list[dict]) -> str:
        ...


# ── Mock LLM ──────────────────────────────────────────────────

_INJECTION_SIGNALS = [
    "ignore", "disregard", "forget", "new instruction",
    "system:", "dan ", "evil", "jailbreak", "roleplay",
    "no restriction", "unrestricted", "pretend you are",
    "hypothetical", "admin note", "end of system",
    "[inst]", "```\nnew system",
]

_JSON_SIGNALS  = ["json", "return json", "output json", "{"]
_LIST_SIGNALS  = ["list", "enumerate", "give me 3", "give me 5"]
_CLASS_SIGNALS = ["classify", "category", "label", "sentiment"]

_SAFE_RESPONSES = [
    "Python is a high-level programming language created by Guido van Rossum.",
    "The capital of France is Paris.",
    "A REST API uses HTTP methods to allow systems to communicate.",
    "Cloud computing provides on-demand computing resources over the internet.",
    "Machine learning enables systems to learn patterns from data.",
    "Docker containers package code and dependencies for consistent deployment.",
    "Kubernetes orchestrates containerised workloads at scale.",
    "SQL databases use structured tables; NoSQL supports flexible schemas.",
]

_REFUSAL = "I cannot assist with that request."


class MockLlm:
    """
    Deterministic mock LLM — no network calls, no API key.

    Detects injection patterns in user input and returns refusal.
    Otherwise returns context-appropriate mock responses.
    """

    def __init__(self, seed: int | None = None,
                 latency_ms: float = 5.0,
                 fail_rate: float = 0.0):
        """
        Args:
            seed:       random seed for determinism
            latency_ms: simulated response latency
            fail_rate:  fraction of calls that raise RuntimeError (0.0–1.0)
        """
        self._rng       = random.Random(seed)
        self._latency   = latency_ms
        self._fail_rate = fail_rate

    def complete(self, messages: list[dict]) -> str:
        time.sleep(self._latency / 1000)

        if self._fail_rate > 0 and self._rng.random() < self._fail_rate:
            raise RuntimeError("MockLlm: simulated transient failure")

        # Collect all message content
        all_text   = " ".join(m.get("content", "") for m in messages).lower()
        user_texts = [m.get("content", "") for m in messages if m["role"] == "user"]
        last_user  = user_texts[-1].lower() if user_texts else ""

        # Injection detection
        if self._is_injection(last_user):
            return _REFUSAL

        # System prompt instruction following
        system_content = next(
            (m.get("content", "") for m in messages if m["role"] == "system"), ""
        ).lower()

        # JSON output
        if any(sig in system_content for sig in _JSON_SIGNALS) or \
           any(sig in last_user     for sig in _JSON_SIGNALS):
            return '{"answer": "mock response", "confidence": 0.95}'

        # List output
        if any(sig in last_user for sig in _LIST_SIGNALS):
            return "1. Python\n2. JavaScript\n3. Java\n4. TypeScript\n5. Go"

        # Classification
        if any(sig in last_user for sig in _CLASS_SIGNALS):
            return self._rng.choice(["positive", "negative", "neutral"])

        # Generic response
        return self._rng.choice(_SAFE_RESPONSES)

    @staticmethod
    def _is_injection(text: str) -> bool:
        return any(sig in text for sig in _INJECTION_SIGNALS)


# ── Runner ────────────────────────────────────────────────────

class PromptRunner:
    """
    Executes RenderedPrompt objects against an LLM backend.
    Records latency and run metadata.
    """

    def __init__(self, llm: LlmBackend, model_name: str = "mock-llm"):
        self._llm   = llm
        self._model = model_name

    def run(self, prompt: RenderedPrompt, run_id: int = 0) -> PromptResult:
        """Execute one rendered prompt and return a PromptResult."""
        t0     = time.perf_counter()
        output = self._llm.complete(prompt.messages)
        ms     = (time.perf_counter() - t0) * 1000

        return PromptResult(
            prompt     = prompt,
            output     = output,
            latency_ms = round(ms, 3),
            model      = self._model,
            run_id     = run_id,
        )

    def run_n(self, prompt: RenderedPrompt, n: int = 5) -> list[PromptResult]:
        """Run the same prompt n times for consistency measurement."""
        return [self.run(prompt, run_id=i) for i in range(n)]

    def run_batch(self, prompts: list[RenderedPrompt]) -> list[PromptResult]:
        """Run a list of different prompts."""
        return [self.run(p) for p in prompts]
