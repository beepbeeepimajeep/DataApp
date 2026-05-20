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

## OPTIMIZATION OBJECTIVE

We are optimizing for grader score on Kaggle (the competition metric).
Mathematical correctness is correlated with but not identical to that objective.

The grader enforces specific format requirements, numeric precision, LaTeX
conventions, and answer ordering. An answer may be mathematically sound but
score zero if it does not match the grader's expected format.

This distinction matters:
- When choosing between "correct math, wrong format" and "close enough, right format"
- When deciding if a teacher's answer is "wrong" (grader perspective, not math)
- When tuning consensus or acceptance thresholds
- When debugging apparent disagreements between teachers

---

## AUTHORIZATION GATES

claude_dataApp NEVER autonomously launches operations that:
- Process more than 5 items
- Make API calls outside a smoke test
- Resume a paused pipeline
- Restart a killed process

Every scaled operation requires Rain's EXPLICIT "proceed" in chat. 
"Skip-and-continue" or "ready to proceed" pattern is FORBIDDEN — 
claude_dataApp reports, then STOPS, then waits for authorization 
before the next billable operation.

### EXPLICIT AUTHORIZATION PROTOCOL (non-negotiable)

1. **Forward-authorizations are NOT valid for scaled operations.**
   - Example of INVALID: "After you finish X, go ahead and do Y"
   - You must STOP after X and wait for a NEW explicit authorization.

2. **Valid authorization format:**
   - User types: "ok proceed" OR "proceed" OR explicit approval
   - In the CURRENT chat turn (not a previous message)
   - After all setup, planning, dry-runs, and verification steps complete
   - BEFORE any API calls that process >5 items or cost >$5

3. **Prohibited patterns (NEVER do these):**
   - Treating "ready to proceed?" as authorization to proceed
   - Executing forward instructions ("go do X when Y is done")
   - Inferring permission from context or prior messages
   - Any execution between user messages without new explicit "proceed"
   - Skipping confirmation just because an earlier message said "ok"

4. **When uncertain:** STOP, report completion of prior steps, wait 
   for new explicit authorization in the NEXT user message.

---

If claude_dataApp finds a process running unexpectedly, the response 
is: "I see process X running, status Y, what should I do?" — never 
"I'll restart it cleanly."

If a long-running process appears stalled, claude_dataApp checks 
manifest timestamps, log activity, and PID liveness BEFORE concluding 
"stalled." A process can be active and producing output while not 
logging visibly for minutes at a time.

KILL ONLY ON AUTHORIZATION. Even apparently-stuck processes get 
reported, not killed. Lost forensic data is irrecoverable.

---

## COST DISCIPLINE

### Budget ceilings (2026-05-20 PDT update)

Hard ceiling: $150 total OpenAI spend for the project.
(Previously $100; raised 2026-05-20 PDT after morning sync run on
2026-05-19 produced $73 in unexpected sunk cost. See HISTORICAL
FAILURES "GPT-5.5-xhigh sync run silent failure".)

Reasoning for $150:
- $79 already spent (Phase 2 + GPT-5.5-xhigh morning sync)
- $47 projected for GPT-5.5-xhigh batch retry (4th teacher unblocks
  Ticket 5 HIGH labels)
- $24 buffer for unexpected costs (retry items, Ticket 5 verification)
- Account credit balance is $130; OpenAI deposit covers $150
  ceiling with $20 margin if last $20 deposit/match is honored.

Authorization to raise this ceiling further requires explicit Rain
approval AND documented reasoning. Do NOT raise silently.

Local cost_log.jsonl is ESTIMATES, NOT TRUTH. The OpenAI Python SDK 
undercounts billed tokens by ~2.4x for GPT-5.4 and GPT-5.5 (likely 
all GPT-5 family). Local cost is for relative comparison and 
debugging only.

**Cost ground truth (reconciled):**
- Primary: Admin API via scripts/check_spend.py (most reliable)
- Secondary: OpenAI dashboard / platform.openai.com/usage (real-time)
- When they disagree on very recent activity (within last few hours):
  Admin API can lag the dashboard by minutes to hours per OpenAI docs
  ("data may be delayed"). In conflicts, **take the HIGHER number**
  as more accurate for very recent spend.
- **NEVER apply multipliers to either source.** Multipliers are for 
  correcting SDK undercounts only; both Admin API and dashboard 
  report actual billing.

Before any operation that may spend >$5:
1. Run check_spend.py — record baseline
2. Run operation
3. Run check_spend.py — verify actual cost in expected range
4. If actual is >20% above projected: STOP and report

Admin API has reporting & bucket quirks:
- Buckets are UTC-day boundaries, not local
- If "today" in PDT spans two UTC days, expect 2 buckets to inspect
- Reporting lag: minutes to hours behind actual transactions per OpenAI
- For real-time spend during active operations, cross-check dashboard

Budget framing rules:
- "Available" = credit balance shown on dashboard (already net of spent)
- Do NOT subtract today's spend from credit balance — it's already deducted
- "Monthly cap" is a separate ceiling, not the budget

---

## TEST BEFORE SCALE

Any operation processing >5 items requires a smoke first that:
- Exercises the actual code path (not just the API endpoint)
- Targets a known failure-mode input where one exists
- Verifies output quality, not just "no crash"

Smoke checklist:
- 1-item smoke first (under $0.50 cost)
- 5-item smoke second (mix of question types / known-hard items)
- ONLY then full scale

Smoke pass criteria:
- No crashes
- Actual cost within 30% of projection
- Output content is sensible (not just non-empty)
- Recursion/error fallback paths fire when expected on known-bad inputs
- Agreement/consensus values match what a human inspection would say

"Smoke didn't crash" is NOT pass. Smoke must demonstrate the failure-mode 
fix actually works in production, not just in isolated unit tests.

Default concurrency is FORBIDDEN. Every scaled operation specifies 
--workers N explicitly. If --workers flag doesn't exist, build it before 
running.

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
- Launch any operation processing >5 items without explicit "proceed" from Rain in chat
- Kill or restart a running process without first reporting its state
- Restart a stalled process without authorization
- Conclude a process is "stalled" without checking manifest timestamps and PID liveness
- Trust local cost_log as actual spend (it's 2.4x undercount on GPT-5)
- Subtract today's spend from credit balance when computing remaining budget (credit balance is already net)
- Use default concurrency on any scaled API operation
- Mark items as low-agreement without verifying answers_match handled the comparison correctly (numerical tolerance, interval formats)
- Run a smoke without verifying it exercised the failure-mode it was meant to test

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
- Launching any operation processing >5 items
- Resuming a paused pipeline
- Restarting a killed process
- Re-running an operation that previously failed
- Spending decisions based on local cost_log alone
- Any operation projected to cost >$5

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

**Process status reporting:**
- When checking a running process, report: PID alive (Y/N), manifest count, manifest mtime, log mtime — not just "ps showed nothing"
- After every billing operation: report check_spend.py result, not just the local cost_log estimate
- When a smoke "passes", report what was actually exercised — not just "no errors"

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

**2026-05-19: $15 burn from default concurrency Phase 2 launch.**

After fixing the answers_match() recursion bug, Phase 2 was relaunched 
without smoke test and with default concurrency. 5 of 7 items crashed 
on the same recursion path the fix was supposed to handle (because 
fresh API outputs hit a different code path). Cost: ~$15 actual, $6.28 
logged.

Lesson: Every scaled operation gets a smoke that EXERCISES THE FIX, not 
just verifies "process starts and runs."

**2026-05-19: Unauthorized Phase 2 launch between turns.**

While Rain was reviewing smoke output, claude_dataApp launched Phase 2 
without authorization. Logs show activity at 13:37 between an authorized 
smoke and the next Rain prompt. When questioned, claude_dataApp didn't 
recognize its own running process and tried to "restart fresh."

Lesson: NO operation launches between Rain prompts. Wait for explicit 
"proceed."

**2026-05-19: Kill-and-restart of running Phase 2.**

claude_dataApp interpreted a Phase 2 process as "stalled after 2-3 items" 
based on a single `ps` check showing no output. The process was actually 
running but between log writes. claude_dataApp killed it and tried to 
restart with `rm logs/phase2_full.log` (destroying forensic data) and 
default concurrency (no --workers flag).

Lesson: Stalled ≠ slow logging. Before killing, check: PID alive, 
manifest mtime, log file mtime, manifest count vs N minutes ago. If 
unclear, REPORT to Rain, don't act.

**2026-05-19: OpenAI SDK reasoning_tokens undercount discovered.**

Cost log undercounted actual billing by 2.4-2.5x for both GPT-5.4 and 
GPT-5.5 (likely a Chat Completions API field-extraction issue with 
completion_tokens_details.reasoning_tokens). Spent today reached $77 
when local log said $22.

Lesson: Local cost_log is for relative comparison only. Admin API via 
check_spend.py is the only source of truth for spend decisions.

**2026-05-19: Date bucket misinterpretation in Admin API.**

Costs API was queried with rolling 24h windows. Today's spend ($76) 
appeared in the May 19-20 UTC bucket but claude_dataApp reported it 
as "$0 today" because it labeled buckets by start_time and the 
earlier query window cut off before today's UTC midnight.

Lesson: When querying Costs API, query a wider window (7 days minimum) 
and inspect raw bucket timestamps in UTC. Don't trust date labels 
derived from local timezone.

**2026-05-19: False-disagreement labeling on coordinate-pair answers.**

Smoke item 74 had three teacher answers all expressing the same 
interval `(12.30, 25.10)`, `(12.3, 25.1)`, `[12.306, 25.094]` — 
semantically equivalent. consensus_normalizer.answers_match marked 
them as 1/3 disagreement. Root cause: answers_match doesn't decompose 
parenthesized coordinate pairs for element-wise numerical comparison. 
Treats "(12.30, 25.10)" as opaque string.

Lesson: When agreement_type comes out lower than expected, INSPECT the 
raw teacher answers and verify the comparison logic handled them. 
Silent false-disagreement contaminates training data. Add coordinate-pair 
handling to answers_match in Ticket 5 prep.

**2026-05-19: GPT-5.5-xhigh sync run silent failure (morning).**

`scripts/generate_gpt55_full.py` was launched with 15-worker concurrency 
and 600s per-request timeout on 943 items. Result: 321 succeeded, 622 
failed silently (0 output_tokens, no error raised). Cost: $73.42 sunk.

Root cause: reasoning rate-limit pool saturation under 15 concurrent 
xhigh requests causes requests to hang server-side past the 600s client 
timeout, return empty completions (output_tokens=0), but still get 
billed at the model's standard rate. The dead-item "\\boxed{answer}" 
string was a script markdown stub in format_gpt55_response_md(), NOT 
the model copying the prompt (later confirmed by smoke batch after 
prompts.py angle-bracket fix).

Decision: Use OpenAI Batch API instead. Benefits: 50% off pricing, 
separate rate limits, proper failure visibility via error_file_id, 
automatic retries. Downside: async (up to 24h), but acceptable for 
backfill use case.

Lesson: NEVER re-run generate_gpt55_full.py. Use batch API for all 
GPT-5.5-xhigh at scale.

---

## MEMORY

Surface to Rain: "Worth adding to DataApp CLAUDE.md: [what]" and wait 
for approval. Never modify this CLAUDE.md unprompted.