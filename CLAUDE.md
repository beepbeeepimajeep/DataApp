## COST GROUND TRUTH

Hard ceiling: $150 total OpenAI spend. Raised from $100 on 2026-05-20 PDT
after $73 morning-sync sunk cost. Any further raise requires explicit
Rain approval and documented reasoning.

**Ground truth, in priority order:**
1. OpenAI dashboard (platform.openai.com/usage) — freshest, real-time
2. Admin API via `scripts/check_spend.py` — authoritative but lags
   dashboard by minutes to hours
3. When 1 and 2 disagree on recent activity: take the higher number

NEVER use the following for cost decisions:
- Local `cost_log.jsonl` — undercounts by ~2.4x due to SDK token reporting issue
- Smoke-sample × item-count projections — smoke samples bias toward easy items;
  use Phase 2's actual per-item rate ($0.197/item) as the planning rate
- Token-count × price math without confirming against dashboard

Before any operation that may spend >$5:
1. Run `check_spend.py` — record baseline
2. Run operation
3. Run `check_spend.py` AND check dashboard — verify actual cost in expected range
4. If actual is >20% above projected: STOP and report

Admin API has UTC-day buckets and reporting lag. PDT "today" may span two
UTC buckets. Don't trust date labels derived from local timezone.

---

## USE EXISTING TOOLS

Before writing collection, audit, or analysis code, check `scripts/` and
`src/` for an existing implementation. Official scripts handle file format,
atomic writes, cost logging, and edge cases that ad-hoc code re-discovers
incorrectly.

Official scripts (canonical):
- Batch results collection: `scripts/batch_collect_gpt55_results.py`
- Manifest population from responses: `scripts/collect_gpt55_responses.py`
- Consensus audit: `scripts/audit_consensus.py`
- Phase 2 results audit: `scripts/audit_phase2_results.py`
- Cost ground truth: `scripts/check_spend.py`

If an existing script doesn't fit, REPORT the gap to Rain before writing
new code. Ad-hoc scripts that diverge from established pipeline format
break downstream tools that depend on that format.

Why this rule: Phase 3 was collected with custom one-off code that wrote
markdown files without the `## Metadata` and `## Reasoning + Response`
wrappers, breaking Ticket 6 trace selector and audit scripts.

---

## VERIFY BEFORE ASSERTING

Confident technical claims about external systems (OpenAI APIs, batch
behavior, rate limits, model timeouts, vendor SLAs) require either:
- A documentation citation or quoted source
- Explicit acknowledgment that the claim is inferred from observation,
  not verified against docs

Phrases like "X is documented to..." or "the API behaves..." without a
link or quote signal a stop-and-check moment. If unsure, say: "I think
X based on observed behavior but haven't verified against docs."

Why this rule: Confidently-stated false claims today included "OpenAI
batch cancellation loses partial data" (wrong per OpenAI's batch FAQ)
and "10-min per-item timeout in batch API" (not documented anywhere).
Both were stated as if authoritative.

---

## CROSS-CHECK COUNTS WITHIN SESSION

When reporting a count that differs from an earlier count in the same
session, RECONCILE explicitly. Example:
- "Earlier said 339 morning-sync clean."
- "Now reporting 488 total clean = 339 morning-sync + 50 Phase 1 + 99 Phase 2."

If the count uses a different audit method than before, name the method
("file-existence count" vs "content-based audit") and prefer the
content-based number.

Counts based on `ls | wc -l` are file-existence, not content-validity.
For "items needing X" or "items that have valid Y," always read content
and check for failure markers (Output tokens: 0, RetryError, timeout,
placeholder text, missing `\boxed{}`).

Why this rule: Today produced both "474 needs retry" and "622 failed
items need reprocessing" within minutes, without reconciliation. The
two used different audit methods. Also: "0 items remaining" was a file
count that missed that 622 files contained morning-sync failures.

---

## KNOWN HISTORICAL FAILURES (LEARN FROM THESE)

Failures are grouped by root cause. Each entry summarizes the pattern,
not every incident.

### Authorization drift
- **2026-05-19 Phase 2 launched between turns.** Operation started without
  explicit "proceed" while Rain was reviewing prior output.
- **Resulting rule:** No operation launches between Rain prompts. Wait
  for explicit "proceed" in the current chat turn.

### Stalled-process misdiagnosis
- **2026-05-19 kill-and-restart of running Phase 2.** A single `ps` check
  showing no output was treated as "stalled," process was killed, logs
  destroyed, restarted with default concurrency causing $15 burn.
- **Resulting rule:** Before concluding "stalled," check PID alive,
  manifest mtime, log mtime, manifest count delta over N minutes. If
  unclear, REPORT — do not kill.

### Inline analysis without commit
- **2026-05-19 smoke analysis script unreproducible.** When Rain
  questioned numbers, the script that generated them couldn't be located.
  Reconstruction produced different counts.
- **Resulting rule:** Every analysis that informs a decision must be a
  committed script with a discoverable git SHA. Inline analysis is
  forbidden for load-bearing reports.

### Cost ground-truth confusion
- **2026-05-19 OpenAI SDK reasoning_tokens undercount.** Local cost log
  showed $22 when actual billing was $77. Root cause: SDK doesn't include
  reasoning_tokens in cost calc despite docs implying it does.
- **2026-05-19 Admin API date-bucket misread.** "$0 today" reported
  when bucket was actually $76, due to UTC/PDT bucket boundary.
- **Resulting rule:** Use dashboard + Admin API only. Never local
  cost_log for decisions. See `## COST GROUND TRUTH`.

### Verification overreach
- **2026-05-19 informal verification claimed certainty.** Reported
  "MATHEMATICALLY IMPOSSIBLE" on item 312 based on a hand-wavy bound.
  Actual verifier returned INCONCLUSIVE.
- **Resulting rule:** VERIFY means code-checked. Hand-wavy bounds are
  not verification.

### Smoke without exercising the fix
- **2026-05-19 $15 default-concurrency burn.** After answers_match()
  recursion fix, Phase 2 relaunched without smoke; 5/7 items crashed on
  the SAME recursion path the fix was supposed to handle (different code
  path in fresh outputs).
- **Resulting rule:** Every scaled operation gets a smoke that exercises
  the fix in production, not just unit tests. See `## TEST BEFORE SCALE`.

### Repo state vs claimed state
- **2026-05-19 GitHub had no source code.** Audit showed only CLAUDE.md
  + README despite weeks of work. Bus factor was 1.
- **Resulting rule:** `git push` is part of "done." See implementation
  arm health rules.

### Silent provider failures
- **2026-05-19 GPT-5.5-xhigh sync run silent failure.** 622/943 items
  returned `output_tokens=0` with no error raised. $73 sunk on items
  that produced nothing. Root cause: 15-worker concurrency saturated
  reasoning rate-limit pool, requests hung server-side past 600s timeout,
  returned empty completions but still billed.
- **Resulting rule:** NEVER re-run `generate_gpt55_full.py`. Use Batch
  API for all xhigh at scale.

### Ad-hoc code diverging from pipeline
- **2026-05-20 Phase 3 collected with custom one-off code.** Files
  written without `## Metadata` and `## Reasoning + Response` wrappers,
  breaking Ticket 6 trace selector and audit detection.
- **Resulting rule:** See `## USE EXISTING TOOLS`.

### Confident-wrong technical claims
- **2026-05-20 "cancel loses partial data" wrong per OpenAI docs.**
- **2026-05-20 "10-min per-item timeout" fabricated.**
- **Resulting rule:** See `## VERIFY BEFORE ASSERTING`.

### Count inconsistency within session
- **2026-05-20 474 vs 622 needs-retry without reconciliation.** Different
  audit methods, no cross-check.
- **2026-05-20 "0 items remaining" from file-existence count missed
  622 files with empty content.**
- **Resulting rule:** See `## CROSS-CHECK COUNTS WITHIN SESSION`.

---

## MEMORY

Surface to Rain: "Worth adding to DataApp CLAUDE.md: [what]" and wait
for approval. Never modify this CLAUDE.md unprompted.

When you encounter a bad assumption during a session, suggest a CLAUDE.md
correction at the end of that session.