# Interview Notes — Prompt Engineering Test Lab

## What I Built

A systematic testing framework for prompt engineering. Four layers:
PromptTemplate manages zero-shot, one-shot, few-shot, and system prompts as
versioned, testable objects. FormatValidator checks that outputs match their
expected format contract. ConsistencyScorer measures output stability across
multiple runs of the same prompt. InjectionDetector classifies whether a model
output indicates successful injection resistance or compliance with an injected
instruction. QualityScorer computes a composite score across all dimensions.

All tests run against a MockLlm — no API key, fully deterministic, fast CI.

## How I Would Explain It in an Interview

> "Prompts are code. They have bugs, they have regressions, and they need tests.
> But most teams treat prompts as configuration — they change them informally,
> without any systematic evaluation of whether the change improved or degraded
> output quality.
>
> I built a framework that brings software engineering discipline to prompt
> management. A PromptTemplate is a typed, versioned object — not a raw string.
> You render it with variables, run it through an evaluator, and get a quality
> score.
>
> The FormatValidator catches the most common production bug: a prompt that was
> supposed to return JSON starts returning prose after the model is updated.
>
> The ConsistencyScorer catches fragile prompts — ones where the same input
> produces wildly different outputs across runs. A low consistency score tells
> you the prompt has too much ambiguity.
>
> The InjectionDetector is the security layer. For every prompt that processes
> user input, I run it against a catalogue of 16 injection and jailbreak
> attempts and verify the model resisted."

## Key Design Decisions Worth Discussing

**Why is PromptTemplate a class instead of a string?**
A string can't be tested, versioned, or validated. A class has a shot_type field,
a name field, an examples list, and a render() method that raises ValueError when
a variable is missing. This catches prompt bugs at render time, not at model
inference time.

**Why separate format, consistency, injection, and quality into different modules?**
Different teams own different concerns. The safety team owns the injection tests.
The product team owns format compliance. Keeping them separate means you can run
just injection tests in a security review without running the full quality suite.

**Why MockLlm simulates injection resistance?**
It would be circular to test injection detection against a model that might actually
comply with injections. The MockLlm returns predictable refusals for injection inputs
and predictable topic responses for normal inputs, making the tests deterministic
and fast without needing real model calls.

**Why Jaccard similarity for consistency instead of exact match?**
LLMs rarely produce identical outputs across runs even for the same prompt. Exact
match would always fail. Jaccard over token sets measures semantic consistency —
"Paris is France's capital" and "The capital of France is Paris" are different
strings but very similar by Jaccard.

## What I Would Add Next

1. **Promptfoo integration** — export PromptTemplate objects as promptfoo YAML
   config and run the suite through the promptfoo CLI for provider comparison
2. **A/B shot comparison** — automatically run zero-shot, one-shot, and few-shot
   variants of the same prompt and produce a side-by-side quality score table
3. **LLM-as-judge evaluation** — use a judge LLM to score open-ended outputs that
   aren't amenable to keyword or format checking
4. **Prompt version diffing** — when a prompt is updated, automatically run the
   previous and new versions through the suite and flag any quality regressions
5. **Injection pattern updates** — plug in jailbreak databases like JailbreakBench
   to keep the injection case catalogue current with emerging attack patterns
