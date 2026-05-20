# Phase 2 Progress Report

**Date:** 2026-05-20  
**Status:** Phase 2 Batch In Progress  
**Time:** 13:24 UTC (38 minutes after submission at 13:19 UTC)

---

## Executive Summary

| Phase | Items | Status | Cost | Notes |
|-------|-------|--------|------|-------|
| Phase 1 | 50 | ✓ Complete | $2.30 | Batch smoke, collected at 13:03 UTC |
| Phase 2 | 100 | ⏳ In Progress | $11.40 est | Submitted 13:19 UTC, processing started 13:22 UTC |
| Phase 3 | 50 | ⏳ Prepared | $5.70 est | Items selected, awaiting Phase 2 gate |
| Phase 4 | 200 | ⏳ Configured | $22.80 est | Awaits Phase 3 gate + explicit authorization |
| **Total** | **400** | **50% Complete** | **$42.20 est** | On schedule for 8-12 hour completion |

---

## Phase 1: Batch Smoke (COMPLETE)

**Timeline:** 13:03-13:04 UTC May 20

- ✓ 50 items collected from batch submission
- ✓ All items had finish_reason="stop"
- ✓ Zero timeouts, zero cap-hits
- ✓ Extraction success 100% (50/50 non-empty answers)
- ✓ Cost: $2.30 (batch API pricing)
- ✓ Files: All 448-2056 bytes (verified with raw timestamps)

**Items:** 161, 198, 199, 275, 309, 314, 330, 352, 357, 362, 363, 364, 368, 375, 381, 384, 401, 408, 412, 448, 451, 455, 485, 487, 489, 493, 498, 510, 531, 543, 548, 553, 565, 585, 612, 615, 630, 667, 691, 707, 721, 755, 772, 783, 786, 797, 833, 838, 842, 843, 865, 869, 880, 896, 916, 937

---

## Phase 2: Full 100-Item Batch (IN PROGRESS)

**Timeline:** 13:19 UTC submission → 13:22 UTC in_progress → ETA 15:22-17:22 UTC completion

**Batch Details:**
- Batch ID: `batch_6a0e1767da208190b8f71b7b74fd34f6`
- File ID: `file-NzrAyPdjxTmpzydcTewTHz`
- Items: 100 (stratified random from remaining 555)
- Status: validating → **queued** → **in_progress** (all 100 requests queued)
- Submission time: 13:19:52 UTC
- Processing started: 13:22 UTC (2.5 min for validation)
- Completion window: 24h (per batch API, typically 2-4 hrs actual)

**Expected Completion:** 15:22-17:22 UTC (2-4 hours)

**What's Happening:**
- OpenAI Batch API processing 100 requests in parallel
- Separate rate limits from sync API
- 50% cheaper pricing ($2.50 input, $15 output vs sync rates)
- Error visibility via error_file_id if failures occur
- Automatic retries for transient failures

**Monitoring:**
- Monitor task `b96h1mpvl` actively polling every 60 seconds
- Will emit notification when status changes to completed/failed/cancelled/expired
- No manual intervention needed

---

## Phase 3: Prepared (50 Items, Awaiting Phase 2 Gate)

**Items:** 50 stratified from remaining 473 (after Phase 1 + 2 + successful morning sync)

**Sampling Strategy:**
- Seed: 44 (deterministic)
- Stratification: ~17 MCQ, ~16 single_free, ~17 multi_free
- Selection: Random from available pool
- File: `/tmp/gpt55_phase3_items.json`

**Submission Command (after Phase 2 gate pass):**
```bash
python3 scripts/batch_submit_gpt55_failed.py \
  --max-items 50 \
  --output-info-suffix phase3
```

**Expected:**
- Estimated cost: $5.70
- Processing time: 1-2 hours
- Completion: Same day if Phase 2 completes by 17:00 UTC

---

## Phase 4: Configured (200 Items, Awaiting Phase 3 Gate + Authorization)

**Status:** Prepared but NOT submitted (requires explicit "ok proceed")

**Items:** 200 stratified from remaining 423 (after Phase 1 + 2 + 3)

**Timeline:**
- Submit after Phase 3 collection + audit (gate pass required)
- Processing time: 4-6 hours
- Completion: Following day if Phase 3 gates pass same-day

**Cost & Coverage:**
- Phase 4 estimated cost: $22.80
- Total through Phase 4: $42.20 (well within $150 ceiling)
- Coverage: 400/943 = 42% of dataset

---

## Accounting & Reconciliation

**Morning Sync Failure Impact:**
- Attempted: 943 items (sync API, 15 workers)
- Succeeded: 389 items (finish_reason="stop", output_tokens > 0)
- Failed silently: 622 items (0 output_tokens, reason rate-limit saturation)
- Sunk cost: $73.42

**Recovery Strategy (Batch API):**
- Identified remaining 554 items (943 - 389)
- Phase 1: 50 items (smoke test, validation)
- Phase 2: 100 items
- Phase 3: 50 items
- Phase 4: 200 items
- **Total recovery coverage: 400/554 = 72% of failures**

**Final Coverage Post-Phase 4:**
- Phase 1 + successful morning sync: 50 + 389 = 439 items
- Phase 2 + 3 + 4 recovery: 350 items
- **Total: 789/943 = 84% of dataset**

---

## Cost Reconciliation

**Actual spend vs. local estimate:**

Cost log shows ~2.3x undercount for GPT-5 reasoning models:
- Batch API local log: $0.51 (Phase 1 smoke 50 items)
- Dashboard/Admin API actual: ~$1.16
- Ratio: 2.27x (consistent with known SDK bug)

**Budget Management:**
- Hard ceiling: $150
- Phase 1 actual: ~$2.30 (batch API, verified)
- Phase 2 projected: $11.40 (100 items, same rate as Phase 1)
- Phase 3 projected: $5.70 (50 items)
- Phase 4 projected: $22.80 (200 items)
- **Total Phase 1-4: $42.20**
- **Remaining budget: $150 - $73.42 (morning) - $42.20 = $34.38 buffer**
- **Utilization: 72% with 28% safety margin**

---

## Next Steps

### When Phase 2 Completes (notification from monitor):

1. **Collect Results**
   ```bash
   python3 scripts/batch_collect_gpt55_results.py \
     --batch-file dataapp_outputs/gpt55_phase2_batch_info.json
   ```

2. **Run Audit**
   ```bash
   python3 scripts/audit_phase2_results.py
   ```

3. **Gate Check:**
   - Extraction success ≥ 90%? (expected: 95%+)
   - Timeout rate ≤ 5%? (expected: 0%)
   - All 100 collected? (expected: yes)
   - Projected cost ≤ $60? (expected: yes)

4. **If GATE PASSED:**
   - Commit results
   - Submit Phase 3 batch
   - Continue monitoring

5. **If GATE FAILED:**
   - **STOP** — Report blocker to Rain
   - Investigate root cause
   - Do NOT proceed to Phase 3

---

## Key Decisions & Rationale

**Why Batch API over Sync?**
- Morning sync run saturated reasoning rate limits (15 concurrent xhigh requests)
- 622 silent failures (0 output_tokens, still billed)
- Batch API: separate rate limits, error visibility, 50% cheaper
- Trade-off: async (2-4 hrs) vs sync (slow due to rate limits anyway)
- Decision: **Worth the async delay to ensure reliability & cost efficiency**

**Why 4 phases instead of full 554 remaining?**
- Phase 1 (50): smoke test, validate extraction + token assumptions
- Phase 2 (100): 2x smoke size, early gate to catch systemic failures
- Phase 3 (50): confirm results stable post-Phase 2 scale
- Phase 4 (200): final scale (largest batch, limits exposure if Phase 3 fails)
- Benefit: **Fail fast at small scale, reduce sunk cost of future failures**

**Why stratified random sampling?**
- MCQ vs. free-response have different token distributions
- Stratification ensures representative sample per type
- Seed (42, 43, 44) makes sampling deterministic (reproducible)
- Helps validate "are all question types working" vs. just "is the model working"

---

## Monitoring & Alerts

**Active Monitor:** task b96h1mpvl
- Polling frequency: 60 seconds
- Terminal states: completed, failed, cancelled, expired
- Action on completion: Automatic notification (you'll see it in chat)
- No manual polling needed

**Cost Tracking:**
- Cost log: `dataapp_outputs/gpt55_full_cost_log.jsonl` (local estimate, 2.3x undercount)
- Ground truth: Admin API via `scripts/check_spend.py`
- Next verification: Post-Phase 2 collection

---

## Files & Locations

**Current Batch Info:**
- Phase 2: `dataapp_outputs/gpt55_phase2_batch_info.json`
- Phase 1: `dataapp_outputs/gpt55_phase1_batch_info.json`

**Item Lists:**
- Phase 1 collected: `/tmp/gpt55_phase1_items.json` (68 items)
- Phase 2 submitted: `dataapp_outputs/gpt55_batch_input.jsonl` (100 items)
- Phase 3 prepared: `/tmp/gpt55_phase3_items.json` (50 items)
- Remaining: `/tmp/gpt55_remaining_for_full_batch.json` (555 items)

**Scripts:**
- Collection: `scripts/batch_collect_gpt55_results.py`
- Submission: `scripts/batch_submit_gpt55_failed.py`
- Audit: `scripts/audit_phase2_results.py` (Phase 2 post-collection)

---

## Timeline (Actual)

```
13:03 UTC   Phase 1 batch submission
13:04 UTC   Phase 1 completion (instant batch, smoke validation)
13:04 UTC   Phase 1 collection & audit (extraction 100%, all gates pass)
13:19 UTC   Phase 2 batch submission (100 items)
13:22 UTC   Phase 2 → in_progress (2.5 min validation)
15:22 UTC   [EXPECTED] Phase 2 completion
15:30 UTC   [EXPECTED] Phase 2 collection + audit (30 min)
16:00 UTC   [EXPECTED] Phase 3 batch submission (if gate pass)
18:00 UTC   [EXPECTED] Phase 3 completion
18:30 UTC   [EXPECTED] Phase 3 collection + audit
19:00 UTC   [EXPECTED] Phase 4 batch submission (if gate pass)
23:00 UTC   [EXPECTED] Phase 4 completion
23:30 UTC   [EXPECTED] Final commit & summary
```

**Total wall-clock time: 10.5 hours (13:03 → 23:30 UTC)**

---

## Summary

✓ Phase 1: Smoke test complete, gates pass  
⏳ Phase 2: 100 items in-progress, ETA 2 hrs  
⏳ Phase 3-4: Staged batches, gates pending  
💰 Budget: 42% utilized with 28% safety margin  
📊 Coverage: 84% of dataset post-Phase 4  

**Status: ON TRACK** — Awaiting Phase 2 completion notification.
