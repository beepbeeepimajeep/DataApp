# Repo Housekeeping — Post-Pipeline Cleanup

**Status:** PENDING. Execute AFTER Ticket 7 (final report) delivered.

## DO NOT EXECUTE WHILE PIPELINE IS RUNNING

These cleanups touch tracked files (some actively written by the 
running pipeline). `git mv` on a file mid-write would corrupt state.

Wait until:
- Phase 2 (`run_full.py`) has exited
- GPT-5.5 xhigh (`generate_gpt55_full.py`) has exited
- Tickets 5, 6, 7 complete
- SFT v3 dataset handed off

## Phase A — Archive Phase 1 documentation

13 Phase 1 .md files clutter the repo root. They're tracked on 
origin/main. Archive to docs/phase1_archive/.

    mkdir -p docs/phase1_archive
    git mv GPT55_SANITY_CHECK.md docs/phase1_archive/
    git mv IMPLEMENTATION_3_AGENTS.md docs/phase1_archive/
    git mv IMPLEMENTATION_PLAN.md docs/phase1_archive/
    git mv IMPLEMTATION.md docs/phase1_archive/IMPLEMENTATION.md
    git mv PHASE1_COMPLETE_ALL_TEACHERS.md docs/phase1_archive/
    git mv PHASE1_COMPLETE_NORMALIZED.md docs/phase1_archive/
    git mv PHASE1_DISAGREEMENT_ANALYSIS.md docs/phase1_archive/
    git mv PHASE1_FINAL_REPORT.md docs/phase1_archive/
    git mv PHASE1_NORMALIZATION_RESULTS.md docs/phase1_archive/
    git mv PROMPT_STRATEGY.md docs/phase1_archive/
    git mv SONNET_PHASE1_COMPLETE.md docs/phase1_archive/
    git mv TODAY_SUMMARY.md docs/phase1_archive/
    git commit -m "Archive Phase 1 docs to docs/phase1_archive/"
    git push

DO NOT MOVE: CLAUDE.md, README.md, HOUSEKEEPING.md (this file).

## Phase B — Clean up root log files

Phase 1 .log files in root (untracked, just on disk). Move to logs/.

    mkdir -p logs
    mv phase1_*.log logs/ 2>/dev/null || true

No commit needed.

## Phase C — PAT security rotation (RAIN ACTION REQUIRED)

The GitHub PAT is currently embedded in the git remote URL. Security 
risk. Rain must:

1. Revoke current PAT in GitHub Settings → Developer settings → 
   Personal access tokens
2. Generate new PAT or set up SSH key (SSH preferred)
3. Update local remote:

    # Option 1: SSH (preferred)
    git remote set-url origin git@github.com:beepbeeepimajeep/DataApp.git
    
    # Option 2: HTTPS with credential helper
    git remote set-url origin https://github.com/beepbeeepimajeep/DataApp.git
    git config credential.helper store

Verify after:
    git remote -v   # should not contain "ghp_"

## Phase D — gpt55_full/ directory persistence

Already correctly gitignored via `dataapp_outputs/*_response.md`. 
943 response files live only on pod filesystem. Decision deferred:
- Tar + upload to external backup, OR
- Accept as ephemeral (cost_log + manifest are tracked)

DECISION: Rain post-Ticket-7.

## Execution Order

When pipeline fully done:
1. Confirm no pipeline processes: 
   `ps aux | grep -E "run_full|generate_gpt55" | grep -v grep`
2. Phase A (commit + push)
3. Phase B (no commit)
4. Surface Phase C status to Rain
5. Surface Phase D decision to Rain

After all phases done, delete this file.
