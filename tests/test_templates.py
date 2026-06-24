"""test_templates.py — 10 tests for PromptTemplate."""

import pytest
from src.prompts.templates import (
    PromptTemplate, ShotType, RenderedPrompt,
    zero_shot_qa, one_shot_qa, few_shot_json, classification_prompt
)


class TestTemplates:

    def test_zero_shot_renders(self, zero_shot):
        prompt = zero_shot.render(question="What is Python?")
        assert isinstance(prompt, RenderedPrompt)
        assert "What is Python?" in prompt.user_content

    def test_zero_shot_has_system_message(self, zero_shot):
        prompt = zero_shot.render(question="Hello?")
        assert prompt.system_content

    def test_one_shot_includes_example(self, one_shot):
        prompt = one_shot.render(question="What is Paris?")
        roles  = [m["role"] for m in prompt.messages]
        assert "assistant" in roles

    def test_few_shot_example_count(self, few_shot):
        prompt = few_shot.render(question="Capital of Spain?")
        assert prompt.example_count >= 2

    def test_shot_type_preserved(self, few_shot):
        prompt = few_shot.render(question="test")
        assert prompt.shot_type == ShotType.FEW_SHOT

    def test_template_name_preserved(self):
        t = PromptTemplate(
            shot_type     = ShotType.ZERO_SHOT,
            user_template = "{q}",
            name          = "my-template-v1",
        )
        prompt = t.render(q="hello")
        assert prompt.template_name == "my-template-v1"

    def test_missing_variable_raises(self, zero_shot):
        with pytest.raises(ValueError, match="variable"):
            zero_shot.render()   # 'question' not provided

    def test_one_shot_requires_exactly_one_example(self):
        with pytest.raises(ValueError, match="ONE_SHOT"):
            PromptTemplate(
                shot_type = ShotType.ONE_SHOT,
                user_template = "{q}",
                examples  = [("A", "a"), ("B", "b")],  # 2 examples
            )

    def test_few_shot_requires_at_least_two_examples(self):
        with pytest.raises(ValueError, match="FEW_SHOT"):
            PromptTemplate(
                shot_type = ShotType.FEW_SHOT,
                user_template = "{q}",
                examples  = [("A", "a")],  # only 1
            )

    def test_classification_prompt_has_labels_in_system(self):
        tmpl = classification_prompt(
            labels=["positive", "negative"],
        )
        prompt = tmpl.render(text="Great product!")
        assert "positive" in prompt.system_content
        assert "negative" in prompt.system_content
