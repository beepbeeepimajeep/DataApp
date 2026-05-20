# DataApp v0 — SFT Training Data Generator

Generate synthetic training data for CSE 151B via 3-teacher consensus from frontier LLMs.

## Quick Start

```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create .env with your API keys
# ANTHROPIC_API_KEY=sk-...
# OPENAI_API_KEY=sk-...
# MOONSHOT_API_KEY=sk-...

# Copy private.jsonl from competition repo to data/
cp ../151B_SP26_Competition/private.jsonl data/

# Run validation (45 items)
python scripts/run_validation.py

# Run full pipeline (943 items) — only after validation passes
python scripts/run_full.py

# Analyze results
python scripts/analyze_results.py
```

## Status (2026-05-20 PDT)

- **Phase 0 (Setup):** ✓ Complete
- **Phase 1 (Validation):** ✓ Complete
- **Phase 2 (Full Run, 3-teacher):** ✓ Complete — 943 items, 0 errors, 65.9% 3/3 agreement
- **Phase 3 (Analysis):** ✓ Manifest at dataapp_outputs/dataset_manifest.jsonl

Active work: Ticket 5/6 (correctness labels + SFT data construction).
GPT-5.5-xhigh batch retry in progress (4th teacher signal).

## Architecture

- `src/prompts.py`: System/user prompts (same for all 3 LLMs)
- `src/api_clients.py`: Anthropic, OpenAI, Moonshot wrappers
- `src/extraction.py`: Answer extraction (via judger.py)
- `src/orchestrator.py`: Parallel execution, resume, voting
- `src/storage.py`: Atomic JSON write/read
- `src/cost_tracker.py`: Token & USD tracking

- `scripts/run_validation.py`: Phase 1 (45-item test)
- `scripts/run_full.py`: Phase 2 (943-item full)
- `scripts/analyze_results.py`: Phase 3 (stats & manifest)

## Output

```
dataapp_outputs/
  item_0/
    anthropic.json
    openai.json
    moonshot.json
    extraction.json       # extracted answers from each LLM
    manifest.json         # consensus & agreement
  ...
  item_942/
    ...
dataset_manifest.jsonl    # one line per item, final consensus
```

## Requirements

See `config.yaml` for model names, hyperparams. All 3 LLMs use:
- temperature=0.6, top_p=0.95
- max_tokens=16384 (Qwen3-Thinking compatible)

## Cost Estimate

- Phase 1 (45 items): ~$0.50 (validation only)
- Phase 2 (943 items): ~$10–15 (Anthropic/OpenAI batch API, Moonshot real-time)

## See Also

- `CLAUDE.md`: Full specification & locked decisions
- Competition repo: `/home/dvaneetv/private/151B_SP26_Competition`
