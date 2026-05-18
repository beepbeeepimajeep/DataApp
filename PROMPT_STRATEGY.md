# dataApp Prompt Strategy — LOCKED Decisions

**Locked: 2026-05-16, Opus 4.7 session**

## TL;DR

Use **16k max_tokens** with **explicit conciseness instruction** in prompts.
Use **unified base prompt + type-specific suffixes** (MCQ / single / multi).
Light planning step. Mandatory count verification for multi-answer.
**Losing some unboxed traces is acceptable and likely beneficial.**

## Evidence base (peer-reviewed, 2025-2026)

| Paper | Finding | Implication |
|---|---|---|
| LIMO (COLM 2025) | 817 curated samples beat 100K for 32B math | Quality > quantity |
| LiteCoT / DAP (May 2025) | 100K traces avg 720 tokens beat 800K long-CoT | Shorter = better student |
| BRIDGE (2026) | "Verbose CoT is detrimental to small models" | Direct support for 4B concern |
| ShorterBetter (Apr 2025) | 50-80% length reduction, maintained accuracy | Long traces have repetition/over-exploration |
| Retro-Search (Apr 2025) | -31.2% length, +7.7% accuracy | Trace revision improves transfer |
| "Optimal Reasoning Length" (2026) | Thinking models have OPTIMAL intermediate length | Over-thinking hurts |

**Consensus:** For small reasoning-model students (≤7B), concise teacher traces transfer better than verbose ones. This is the dominant finding of the 2025-2026 distillation literature.

## Locked design decisions

### 1. Token budget: 16k max_tokens (NOT 32k)
- Rain's earlier concern about 7.2% unboxed loss at 16k was based on Qwen3-4B inference, not teacher inference
- Frontier teachers at 16k will rarely hit the cap on well-formed math problems
- More importantly: pushing teachers to 32k encourages verbose reasoning that hurts the 4B student
- If ~5-7% of items produce unboxed traces, we drop them. ~875 clean traces ≈ LIMO scale (817). Sufficient for LoRA.

### 2. Unified base prompt + type-specific suffixes
- Single shared system prompt for trace style consistency
- Three suffixes: MCQ, single-answer, multi-answer
- Pipeline simplicity + format precision per type

### 3. Explicit conciseness instruction in system prompt
- "Show essential reasoning. Avoid unnecessary verification loops, restarts, or alternative path exploration."
- Targets the exact failure modes ShorterBetter identified

### 4. Light planning step (NOT elaborate decomposition)
- "First, briefly identify what is being asked. Then solve."
- Plan-and-Solve (Wang 2023) supports planning helps, but BRIDGE/LiteCoT warn against elaborate verbose reasoning
- Compromise: planning structure without verbosity

### 5. Mandatory count verification for multi-answer ONLY
- Targets the known V0 failure mode
- "Before final box: verify you have produced exactly N answers in requested order"
- Don't add this to single/MCQ (avoids token bloat)

### 6. Symbolic form: soft instruction
- "Use exact symbolic form when natural; decimal only when problem specifies"
- Avoids the id=93-class failure (premature numerical evaluation)

### 7. Format: explicit, single box
- All types: end with exactly one \boxed{...}
- Multi-answer: comma-separated inside single box, order matters
- No examples in prompt (avoids style overfit to specific exemplars)

## Concrete prompts

### Shared system prompt
```
You are generating a math solution trace for supervised fine-tuning of a smaller reasoning model.

Your goal: produce a correct, clear, concise solution. Not flashy. Not verbose. Teachable.

Rules:
1. Show essential reasoning steps. Avoid unnecessary verification loops, restarts, or exploration of alternative paths.
2. Use exact symbolic form when natural (fractions, radicals, π). Use decimals only when the problem asks for them.
3. Do not use \boxed{} anywhere except the final answer.
4. End with exactly one \boxed{...} containing the final answer.
5. Briefly identify what is being asked before solving.
```

### Single-answer suffix
```
Problem type: single-answer.

There is exactly one final answer. End with: \boxed{answer}
```

### Multi-answer suffix
```
Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \boxed{...} with comma-separated values

End with: \boxed{value1,value2,value3}
```

### MCQ suffix
```
Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \boxed{Letter}
```

## Sampling parameters

- **max_tokens**: 16384
- **temperature**: 0.6 (low diversity for clean traces; we want quality, not exploration)
- **top_p**: 0.95 (default)

## What success looks like (validation gate)

Run on Document 4's 45-item stratified sample (15 MCQ / 15 single / 15 multi) before full 943.

Success thresholds:
- Format compliance ≥95% per teacher
- Multi-answer count accuracy ≥90% (improved from Document 4's 80% baseline given our explicit verification step)
- 3/3 teacher agreement ≥40%
- Median tokens 3k-8k (NOT 10k-20k as Document 4 suggested — our prompt explicitly targets shorter)
- p95 tokens <14k (well within 16k cap)

If validation passes: proceed to full 943.
If multi-answer count <90%: investigate count verification placement before scaling.
If format compliance <95%: tighten format instruction.

## What we explicitly REJECTED and why

| Approach | Source | Why rejected |
|---|---|---|
| 32k max_tokens, take all traces | Earlier conservative reading | BRIDGE + LiteCoT show this hurts small students |
| Few-shot exemplars in prompt | Document 7 | Risks style overfit; teacher models don't need them for format |
| XML-style format tags | Document 6 | Over-engineered for frontier models |
| Elaborate decomposition / sub-problem enumeration | Document 7 | Plan-and-Solve supports light planning, not verbose enumeration |
| Per-type fully separate prompts | Document 6 | Pipeline complexity without clear win |
| Truncate traces post-hoc | Earlier suggestion | Fragile, adds preprocessing step |

## Key insight (the headline)

**The 7.2% unboxed-at-16k that Rain wanted to eliminate was actually a beneficial filter.** Items that produce long unfocused reasoning are exactly what the distillation literature says you DON'T want in your training data. Letting them drop out preserves quality.

LIMO-scale data (~800 samples) trained a 32B model to SOTA on AIME. We'd be doing LoRA on a 4B with potentially 850-900 clean samples. Sufficient.

## Status

This decision is LOCKED unless contradicted by 45-item validation results. The validation is the gate; the literature is the foundation.