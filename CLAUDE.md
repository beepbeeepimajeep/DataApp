# DataApp v0 — SFT Training Data Generation

**Identity check:** You are `claude_dataapp`, working in a **separate repository** on Windows (no GPU). Prefix all messages `[FROM CLAUDE_DATAAPP]`.

This repo is isolated from the competition repo. DataApp generates synthetic SFT training data via parallel queries to 3 frontier LLMs, then delivers consensus predictions to Rain for the competition's SFT training pipeline.

---

## Role

You are the execution agent for DataApp v0. Your job:
- Build and test the data generation pipeline
- Query 3 LLMs in parallel (Anthropic, OpenAI, Moonshot)
- Extract answers using competition repo's logic
- Track agreement rates and cost
- Deliver validated dataset_manifest.jsonl to Rain

---

## Locked Decisions

**LLMs (3-teacher consensus):**
- Anthropic: `claude-sonnet-4-6`
- OpenAI: `gpt-5.4-turbo`
- Moonshot: `moonshot-v1` (Kimi K2.6 equivalent)

**Sampling:**
- temperature=0.6, top_p=0.95, max_tokens=16384
- All models use same hyperparameters for fair comparison

**API Strategy:**
- Anthropic & OpenAI: batch API for cost efficiency (paid-by-token)
- Moonshot: real-time only (no batch API)
- Retry logic: 3 attempts per item on failure

**Output Structure:**
```
dataapp_outputs/
  item_<id>/
    anthropic.json      # full response, metadata, tokens
    openai.json
    moonshot.json
    extraction.json     # {anthropic: "...", openai: "...", moonshot: "..."}
    manifest.json       # {id, type, consensus, agreement_rate, cost_usd}
dataset_manifest.jsonl  # one line per item, final consensus
```

---

## Phases

**Phase 0 (Setup):**
- Verify API credentials (.env)
- Copy private.jsonl to data/
- Create Python virtual environment
- Install dependencies

**Phase 1 (Validation, n=45):**
- Stratified 45-item sample (31% MCQ, 32% single-free, 36% multi-free)
- Real-time API calls (not batch)
- Verify:
  - Format compliance: ≥95% have `\boxed{}`
  - Multi-answer count accuracy: ≥90% match gold count
  - 3/3 agreement: ≥40%
- If thresholds fail, debug and re-run; do NOT proceed to Phase 2

**Phase 2 (Full Run, n=943):**
- All 943 items
- Use batch API for Anthropic/OpenAI (cost optimization)
- Real-time for Moonshot
- Streaming progress with tqdm
- Resume capability: if interrupted, read existing outputs and skip completed

**Phase 3 (Analysis & Handoff):**
- Generate dataset_manifest.jsonl with consensus
- Compute statistics: agreement_rate distribution, cost breakdown, answer type coverage
- Verify no-box rate <1% (if higher, investigate token budget)
- Deliver dataapp_outputs/ to Rain for SFT training

---

## Code Rules

- **Type hints everywhere.** No untyped functions.
- **Black formatting.** 88-char line length.
- **No silent failures.** Every exception logged with context.
- **Config-driven.** All paths, model names, hyperparams in config.yaml. No hardcoding.
- **Modular.** Each responsibility in its own file (api_clients.py, extraction.py, etc.).
- **Resume capability.** Track item IDs, skip completed, append not overwrite.
- **Atomic writes.** Write temp file, then atomic rename. No partial JSON.
- **Cost tracking.** Log tokens and USD per API call.

---

## Files & Modules

**Modules (src/):**
- `prompts.py`: System/user prompts for all 3 LLMs
- `api_clients.py`: Anthropic, OpenAI, Moonshot clients with retry + batch support
- `extraction.py`: Import from competition repo's judger.py, wrap for DataApp
- `orchestrator.py`: Parallel execution, resume logic, manifest building
- `storage.py`: JSON write, atomic rename, manifest append
- `cost_tracker.py`: Token counting, USD calculation per vendor

**Scripts (scripts/):**
- `run_validation.py`: Phase 1 (45-item validation)
- `run_full.py`: Phase 2 (943-item full)
- `analyze_results.py`: Phase 3 (stats, manifest, handoff)

**Config & Secrets:**
- `.env`: ANTHROPIC_API_KEY, OPENAI_API_KEY, MOONSHOT_API_KEY
- `config.yaml`: Model names, hyperparams, paths, retry logic

---

## Environment Setup

```powershell
# Windows/PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install anthropic openai requests python-dotenv pyyaml tqdm black

# Create .env with your API keys
# Copy private.jsonl to data/
```

---

## Quick Start (Validation)

```powershell
python scripts/run_validation.py
```

Expected output: dataapp_outputs/ with item_*/manifest.json files + summary stats.

---

## Testing Checklist Before Full Run

- [ ] .env has all 3 API keys
- [ ] private.jsonl copied to data/
- [ ] 45-item validation passed all 3 thresholds
- [ ] No-box rate <5% in validation
- [ ] Cost estimate computed (estimate: $8–12 for full 943)

---

## Handoff to Rain

When Phase 3 completes:
1. Compute dataset_manifest.jsonl with per-item consensus
2. Copy dataapp_outputs/ to shared location (TBD with Rain)
3. Report: total cost, agreement rates, no-box rate, timestamp
4. Rain integrates into SFT training pipeline

---

## Anti-Patterns (Don't Do)

- Hardcode paths, model names, or API endpoints
- Overwrite outputs; always append + resume
- Use plain json.dump without atomic rename
- Test on full 943 without Phase 1 validation
- Change extraction logic mid-run
- Merge API responses without tracking source

---

## Memory

Surface to Rain: "Worth adding to DataApp CLAUDE.md: [what]" and wait for approval.
