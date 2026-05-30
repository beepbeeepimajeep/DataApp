# DataApp SCRATCH

## 2026-05-30 — Opus 4.7 client + smoke (claude_dataApp)

**Work-unit:** Port SonnetClient → OpusClient, 5-item smoke before production.
**Outcome:** PASS. Ready to wire production 1000-call work-unit.

### Config journey (3 re-locks; all driven by live 400s, evidence recorded)
- CONFIG A `thinking={type:enabled,budget_tokens}` + temp 1.0 → 400
  ("use thinking.type.adaptive + output_config.effort").
- Adaptive thinking accepted but `thinking_tokens=0` even on hard item 0041
  → thinking does not engage via this shape. Handed to strategy.
- Amended lock `temp=0.6, no thinking` → 400 ("temperature is deprecated for
  this model"). Verified rule: with no thinking, temperature must be OMITTED.
- **Final (Option 1, Rain-confirmed):** model=claude-opus-4-7, no thinking,
  no temperature, max_tokens=32768, streaming=True. Verified 200.

### Smoke results
- Phases 0/3/4/5 all pass. A1–A10 met. Cost ≈ $0.82 (Anthropic, < $1).
- Diamond 0041 → 2112 (beats all 4 teachers, cold, 12 out_tok).
- Diamond 0285 → 735 (corroborates audit fix; not Wolfram 147 / Kimi 387).
- 0019 → E using 12,745 out_tok (~12K embedded reasoning in plain output).
- 0451 numerically correct (max diff 4.8e-5) but agree=False on exact-string
  comparator due to RAW full-precision (A7). Production: use gold_equiv
  (free_multi) tolerance. Did NOT add tolerance helper (spec discipline).

### Trace-track finding
SFT reasoning track is NOT dead: reasoning happens in regular output tokens
(not thinking blocks). Production should store full response per item; the
response field IS the trace. Curation pass needed (0019 shows self-correction
churn + multiple intermediate boxed answers; RAW last-boxed correctly takes E).

### Deliverables
- `src/api_clients.py` — OpusClient (streaming, Option 1 config)
- `scripts/smoke_opus.py` — standalone 5-item smoke
- `scripts/probe_opus_matrix.py` — API recon (reproducible)
- `.gitignore` — ignores `dataapp_outputs/smoke_tests/`
- Report: `dataapp_outputs/smoke_tests/opus_smoke_test_report.md` (gitignored)
- Raw: `phase3_raw.json`, `phase4_raw.json` (gitignored)

### Cost caveat
Anthropic spend is OUTSIDE the OpenAI $150 ceiling; no check_spend.py for it.
$300 worst-case 1000-call figure is a DERIVED token×price estimate, to be
validated against the Anthropic dashboard during the run — not ground truth.

### Next
Strategy drafts the production 1000-call work-unit. Commit SHA: fdfbc1c (smoke).

---

## 2026-05-30 — Opus 4.7 production pass, 535 items (claude_dataApp)

**Outcome:** COMPLETE. 535/535 items, 0 errors, 0 remaining empties/cap-hits.

### Run
- Config: claude-opus-4-7, no thinking, no temperature, max_tokens=32768,
  streaming, max_workers=10. Target built by scripts/build_opus_target.py
  (316 anchor ∪ 219 contested = 535; A∩B=0; reconciled).
- Initial run: 535 done, 0 errors, ~23 min wall. 13 items hit the 32K output
  cap (finish_reason=max_tokens) with NO \boxed — genuinely hard items where
  Opus reasoned past 32K mid-exploration (cap-hits ≡ empties exactly).
- A8 ("zero cap-hits") initially FAILED. Fix (authorized "rerun with fixes"):
  scripts/rerun_caphits.py — constrained continuation (feed truncated trace +
  "commit to final answer as \boxed", max_tokens=2048 so it can't re-cap).
  All 13 produced boxed answers; tagged caphit_forced=True; original 32K trace
  preserved in response_truncated (SFT data intact). Post-fix: 0 cap-hits,
  0 empties. A8 now satisfied.
- 32K is the model max output; cannot raise — continuation is the only fix.

### Cost / scale
- Total Anthropic spend: **$33.01** (initial $30.85 + continuation $2.16).
  Continuation cost was ~$0.166/item, NOT trivial — the 32K truncated trace
  is re-sent as input each call (~33K input tokens). Under $50 cap / ~$40 credit.
- 1.20M output tokens captured (SFT trace payload).
- Smoke had projected ~$37; actual $33 — projection was close, slightly high.
  (Anthropic spend is OUTSIDE OpenAI $150 ceiling; no check_spend.py.)

### Diamonds (production == smoke)
0041=2112, 0285=735, 0017=C, 0019=E — all MATCH smoke. A8-diamond OK.

### Deliverables (dataapp_outputs/opus/, gitignored)
- items.jsonl (535 rows; response_full = SFT trace; caphit_forced flag)
- opus_results.csv (535), anchor_v2_candidates.csv (316),
  opus_5th_teacher.csv (219)
- target_535.json, caphit_ids.json, progress.json, run.log

### Anchor_v2 corroboration (via 151B gold_equiv)
corroborate **209** / contradict **78** / inconclusive **29** (=316).
78 contradictions warrant strategy review (Opus disagreeing with anchor —
could be anchor errors OR Opus errors; the 13 caphit_forced items are
lower-confidence and flagged in the CSV).

### Scripts committed
build_opus_target.py, run_opus_production.py, rerun_caphits.py, aggregate_opus.py

### For strategy
Outputs ready for transfer to 151B (vscode work-unit), anchor_v2 build, and
5th-teacher slot integration. Recommend reviewing the 78 contradictions and
treating caphit_forced=True items as lower-confidence.
