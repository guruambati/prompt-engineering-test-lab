# Resume Bullets — Prompt Engineering Test Lab

## Option A — AI QA Engineer / Prompt Testing focus

- Built a systematic prompt engineering testing framework (Python, pytest) covering
  zero-shot / one-shot / few-shot template management, output format validation,
  multi-run consistency scoring (Jaccard), injection resistance testing with a 16-case
  catalogue, and composite quality scoring; all tests run against a deterministic
  MockLlm with no API key

## Option B — GenAI QA Engineer / LLM Security focus

- Implemented an InjectionDetector that classifies model outputs as "resisted" or
  "pwned" using refusal and compliance signal matching; built a 16-case injection
  catalogue across direct, role-play, indirect, and delimiter attack categories for
  systematic prompt security regression testing

## Option C — AI SDET / Prompt Quality Engineering focus

- Designed a ConsistencyScorer measuring output stability across N prompt runs via
  exact match rate, pairwise Jaccard similarity, and length coefficient of variation;
  combined with FormatValidator and QualityScorer into a CI-integrated prompt quality
  gate with GitHub Actions

## Notes on Usage

- Strongest talking point: "Prompts are code — they have bugs and regressions and
  they need tests. Most teams change prompts informally without any systematic
  evaluation. I treat prompts as versioned objects with typed fields and render()
  methods so bugs are caught at render time, not at inference time."
- For security-focused interviews: "I catalogue injection attacks by category —
  direct injection, role-play jailbreaks, indirect injection via document content,
  and delimiter escape attempts. Each category has different detection heuristics."
