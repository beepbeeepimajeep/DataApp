Append, never overwrite. Atomic writes (temp + rename). Resume by skipping 
completed item IDs.

When adding a new teacher mid-pipeline:
- APPEND new fields to existing manifest entries
- Do not modify existing fields or consensus_answer
- New teacher outputs go in NEW subdirectory

---

## PHASES

**Phase 0 (Setup):**
- Verify API credentials
- Copy private.jsonl to data/
- Port extraction from competition repo
- Test extraction against Run 09 data (100% match required)
- Git init + initial commit + push

**Phase 1 (Validation, n=45):**
- 15 MCQ, 15 single-free, 15 multi-free
- Real-time API
- Thresholds (gates, not goals):
  - Per-teacher format compliance: ≥95%
  - Multi-answer count accuracy: ≥90%
  - Median tokens: 3k–8k
  - 3/3 agreement: ≥40% (sanity floor, NOT a quality measure)
- Threshold failure: report to Rain, debug, re-run, do not proceed.

**Phase 2 (Full Run, n=943):**
- All 943 items
- Batch API where supported, real-time for TritonAI
- Resume capability
- Cap-hit canary: monitor finish_reason on first ~50 items. If cap-hit 
  rate >5%, halt and alert Rain.

**Phase 3 (Analysis & Handoff):**
- Generate dataset_manifest.jsonl
- Compute stats: agreement distribution, cost breakdown, no-box rate
- If no-box rate >5%: investigate
- Deliver to Rain for SFT v3 integration
- Do NOT recommend SFT data construction strategy. Report stats.

---

## CODE RULES

- Type hints on function signatures
- Black formatting, 88-char lines
- No silent failures. Every exception logged with (item_id, model, error)
- Config-driven (paths, models, hyperparams in config.yaml)
- Modular but flat. No deep class hierarchies.
- Resume by skipping completed item IDs
- Atomic writes (temp + rename)
- Per-call cost tracking to cost_log.jsonl

---

## ANTI-PATTERNS

**Process:**
- Recommend pipeline/lineup decisions from incomplete data
- Frame "consensus rate up" as a quality win without correctness data
- Conclude "model X is wrong" from informal reasoning instead of code-checked verification
- Overwrite or modify existing manifest entries when adding a teacher
- Skip prose-restatement when asked to verify a math claim
- Treat INCONCLUSIVE as "verified wrong"
- Run analysis inline without committing the script

**Code:**
- Rewrite extraction logic when judger.py has it working
- Use regex for nested-brace extraction
- Hardcode paths, model names, API endpoints
- Plain json.dump without atomic rename
- Run full 943 without Phase 1 validation
- Change extraction mid-run
- Build any UI
- Add deps outside requirements.txt without asking
- Use async/await outside batch API

---

## ASK RAIN BEFORE

- Deviating from locked sampling params or prompts
- Test runs >$10
- Adding any dependency
- Changing output structure
- Adding/removing a teacher
- Drawing conclusions that contradict frontier-model priors

## DO NOT ASK RAIN ABOUT

- Code style (Black + type hints)
- Standard library choices among allowed deps
- Retry logic on transient API errors
- Logging errors, skipping individual failed items with documentation
- Writing helper functions

---

## COMMUNICATION FORMAT

- Concise. 1-2 sentences per fact. State fact, then implication.
- Surface blockers immediately.
- Lead with what you measured, not what you concluded.
- For verification: PROSE RESTATEMENT first, then verifier result, then 
  confidence level.

**Confidence taxonomy:**
- HIGH: sympy returned clean match, OR brute-force validated on multiple 
  small cases, OR direct equivalence via math_verify
- MEDIUM: verifier ran but used numerical approximation or limited 
  small-case validation
- LOW: verifier ran but problem interpretation or implementation is uncertain
- INCONCLUSIVE: verifier could not produce a definitive answer

Only HIGH is decision-quality. MEDIUM is evidence. LOW/INCONCLUSIVE are 
not actionable.

**Progress milestones to report:**
1. Setup complete, all teachers verified, repo committed and pushed
2. Phase 1 complete — full metrics + threshold gates + commit SHA
3. Phase 2 progress at 250 / 500 / 750 / complete (each milestone committed)
4. Final manifest ready

---

## KNOWN HISTORICAL FAILURES (LEARN FROM THESE)

**2026-05-19: Smoke test analysis script could not be located.**

After Rain pushed back on a Phase 2 lineup recommendation, claude_dataApp 
could not produce the script that generated the original smoke report 
numbers (4/4=18, 3/4=13, 2/4=5, 1/4=9). Reconstruction produced different 
numbers (4/4=19, 3/4=13, 2/4=7, 1/4=6). Root cause: the original analysis 
was run inline without saving the script, OR the script existed locally 
but was never committed.

Lesson: every analysis that informs a decision must be a committed script 
with a discoverable git SHA. Inline analysis is forbidden for load-bearing 
reports.

**2026-05-19: Smoke test extraction confusion.**

A regex-based boxed extractor was suspected of failing on nested braces 
like \boxed{7,\frac{7}{8}}. Investigation revealed the production 
extraction was correct, but the agreement counter was using a different 
comparison method than expected. The smoke report drove a wrong 
recommendation regardless.

Lesson: SANITY-CHECK PARSED OUTPUTS BY HAND before running analysis on 
extraction results. The fix existed in judger.py:extract_all_boxed and 
was correctly ported; the bug was downstream in agreement counting.

**2026-05-19: Verification overreach.**

When asked to verify GPT-5.5's item 312 answer (171), reported 
"MATHEMATICALLY IMPOSSIBLE" based on an informal "n ≤ 25 because 25 
primes < 100" intuition. The verifier itself returned INCONCLUSIVE.

Lesson: VERIFY means code-checked. Hand-wavy bounds are not verification.

**2026-05-19: GitHub repo missing source code.**

Audit of github.com/beepbeeepimajeep/DataApp showed only CLAUDE.md, 
README.md, empty config.yaml, and requirements.txt. No source code, no 
scripts, no manifest had ever been committed. Bus factor was 1: pod 
cycle = total loss.

Lesson: git push is part of "done" — not optional. See Implementation 
Arm Health rules above.

---

## MEMORY

Surface to Rain: "Worth adding to DataApp CLAUDE.md: [what]" and wait 
for approval. Never modify this CLAUDE.md unprompted.