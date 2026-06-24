"""
templates.py
============
PromptTemplate — builds structured prompts for zero-shot, one-shot,
and few-shot evaluation.

Design principle: prompts are data, not strings. A PromptTemplate is
a testable, versioned object with explicit fields for shot type,
system message, examples, and user template.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ShotType(Enum):
    ZERO_SHOT = "zero_shot"
    ONE_SHOT  = "one_shot"
    FEW_SHOT  = "few_shot"
    SYSTEM    = "system_only"


@dataclass
class RenderedPrompt:
    """
    The final, ready-to-send prompt after template rendering.
    Carries metadata for evaluation and regression tracking.
    """
    messages:      list[dict]       # OpenAI-compatible message list
    shot_type:     ShotType
    template_name: str
    variables:     dict = field(default_factory=dict)

    @property
    def user_content(self) -> str:
        """Last user message content."""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return ""

    @property
    def system_content(self) -> str:
        for msg in self.messages:
            if msg["role"] == "system":
                return msg["content"]
        return ""

    @property
    def example_count(self) -> int:
        """Number of assistant/user example pairs (excluding final user msg)."""
        pairs = 0
        for i, msg in enumerate(self.messages[:-1]):
            if msg["role"] == "user" and i > 0:
                pairs += 1
        return pairs


class PromptTemplate:
    """
    Builds a prompt from a template specification.

    Usage:
        template = PromptTemplate(
            shot_type     = ShotType.FEW_SHOT,
            system_msg    = "You are a JSON-answering assistant.",
            user_template = "Capital of {country}?",
            examples      = [
                ("Capital of France?",  '{"capital": "Paris"}'),
                ("Capital of Germany?", '{"capital": "Berlin"}'),
            ],
            name = "capital-few-shot-v1",
        )
        prompt = template.render(country="Japan")
    """

    def __init__(self,
                 shot_type:     ShotType       = ShotType.ZERO_SHOT,
                 system_msg:    str            = "",
                 user_template: str            = "{input}",
                 examples:      list[tuple[str, str]] | None = None,
                 name:          str            = "unnamed"):
        self.shot_type     = shot_type
        self.system_msg    = system_msg
        self.user_template = user_template
        self.examples      = examples or []
        self.name          = name

        # Validate shot type vs examples
        if shot_type == ShotType.ONE_SHOT and len(self.examples) != 1:
            raise ValueError(
                "ONE_SHOT requires exactly 1 example, "
                f"got {len(self.examples)}"
            )
        if shot_type == ShotType.FEW_SHOT and len(self.examples) < 2:
            raise ValueError(
                "FEW_SHOT requires at least 2 examples, "
                f"got {len(self.examples)}"
            )

    def render(self, **variables: Any) -> RenderedPrompt:
        """
        Render the template with the given variables.
        Variables are substituted into user_template using str.format().
        """
        try:
            user_content = self.user_template.format(**variables)
        except KeyError as exc:
            raise ValueError(
                f"Template variable {exc} not provided. "
                f"Template: {self.user_template!r}, "
                f"Variables: {variables}"
            ) from exc

        messages: list[dict] = []

        # System message
        if self.system_msg:
            messages.append({"role": "system", "content": self.system_msg})

        # Examples (for one-shot and few-shot)
        for user_ex, assistant_ex in self.examples:
            messages.append({"role": "user",      "content": user_ex})
            messages.append({"role": "assistant",  "content": assistant_ex})

        # Final user message
        messages.append({"role": "user", "content": user_content})

        return RenderedPrompt(
            messages      = messages,
            shot_type     = self.shot_type,
            template_name = self.name,
            variables     = variables,
        )


# ── Pre-built template library ────────────────────────────────

def zero_shot_qa(system_msg: str = "You are a helpful assistant.") -> PromptTemplate:
    return PromptTemplate(
        shot_type     = ShotType.ZERO_SHOT,
        system_msg    = system_msg,
        user_template = "{question}",
        name          = "zero-shot-qa",
    )


def one_shot_qa(example: tuple[str, str],
                system_msg: str = "You are a helpful assistant.") -> PromptTemplate:
    return PromptTemplate(
        shot_type     = ShotType.ONE_SHOT,
        system_msg    = system_msg,
        user_template = "{question}",
        examples      = [example],
        name          = "one-shot-qa",
    )


def few_shot_json(examples: list[tuple[str, str]],
                  system_msg: str = "Answer only with valid JSON.") -> PromptTemplate:
    return PromptTemplate(
        shot_type     = ShotType.FEW_SHOT,
        system_msg    = system_msg,
        user_template = "{question}",
        examples      = examples,
        name          = "few-shot-json",
    )


def classification_prompt(labels: list[str],
                            examples: list[tuple[str, str]] | None = None
                            ) -> PromptTemplate:
    """Prompt for single-label classification tasks."""
    label_str  = ", ".join(f'"{l}"' for l in labels)
    system_msg = (
        f"Classify the input into exactly one of: {label_str}. "
        "Respond with only the label, nothing else."
    )
    shot_type = ShotType.ZERO_SHOT if not examples else (
        ShotType.ONE_SHOT if len(examples) == 1 else ShotType.FEW_SHOT
    )
    return PromptTemplate(
        shot_type     = shot_type,
        system_msg    = system_msg,
        user_template = "{text}",
        examples      = examples or [],
        name          = "classification",
    )
