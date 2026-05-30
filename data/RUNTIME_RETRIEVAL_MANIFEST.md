# Runtime Retrieval Manifest
**Date:** 2026-05-30  
**Agent:** claude_vscode (DSMLP)  
**Repo:** DataApp  

Full filesystem vs git audit. Goal: nothing important on DSMLP runtime missing from repo.

---

## Summary

| Category | Count | Size | Action |
|----------|-------|------|--------|
| A LIGHT DATA | 1 file | 490 KB | **SKIPPED** (gitignored intentionally — see below) |
| B RAW OUTPUTS | 3,772 files | ~1.1 MB | **EXTRACTED** → 2 compact CSVs pushed |
| C SCRIPTS/DOCS | 0 files | — | Nothing to push |
| D MODELS | 0 files | — | Nothing to push |
| E SECRETS | 1 file | 0.6 KB | **FLAGGED** — never push |
| F JUNK/SKIP | 3,586 files | ~99 MB | Skipped (venv, pytest cache) |

**Total untracked:** 7,360 files, ~101 MB  

---

## Category A — LIGHT DATA

| File | Size | Action | Reason |
|------|------|--------|--------|
| `./private.jsonl` | 490 KB | **SKIPPED** | Explicitly gitignored (`private.jsonl` in .gitignore). Contains 943 competition questions (id + question text). Intentionally excluded from version control — this is the private test set. Do NOT push. |

---

## Category B — RAW OUTPUTS

Per-item dirs: `dataapp_outputs/item_XXXX/` (943 dirs × 4 files each = 3,772 files).

Files per item:
- `extractions.json` — pre-extracted s/g/o answers + has_boxed + n_boxes (943 files)
- `sonnet_metadata.json` — model, tokens, timing, error for sonnet teacher (943 files)
- `gpt5_4_metadata.json` — model, tokens, timing, error for gpt4 teacher (943 files)
- `gpt_oss_metadata.json` — model, tokens, timing, error for oss teacher (943 files)

**Action: extracted to compact CSVs, pushed those.**

### Extracted outputs (pushed):

| Output CSV | Rows | Notes |
|-----------|------|-------|
| `data/extractions_compact.csv` | 943 | Per-item s/g/o extracted answers (id UNPADDED). Sourced from extractions.json. Item 498 sonnet has partial reasoning text (token-cap, no boxed — stored verbatim from original pipeline). |
| `data/teacher_metadata_summary.csv` | 2,829 | Per-item per-teacher: model, input_tokens, output_tokens, hit_token_cap, error, generation_time_s, timestamp. Confirms: 171 gpt4 errors (RateLimitError, items 267-449), 3 sonnet token_cap hits, 5 oss token_cap hits. |

### Raw dir manifest (NOT pushed — files exist on DSMLP runtime only):

```
dataapp_outputs/item_0000/ .. item_0942/
  ├── extractions.json        (per-item, 943 files)
  ├── sonnet_metadata.json    (per-item, 943 files)
  ├── gpt5_4_metadata.json    (per-item, 943 files)
  └── gpt_oss_metadata.json   (per-item, 943 files)
Total: 3,772 files, ~1.1 MB
```

Raw response .md files (already tracked in git):
- `dataapp_outputs/item_XXXX/sonnet_response.md` — tracked
- `dataapp_outputs/item_XXXX/gpt5_4_response.md` — tracked
- `dataapp_outputs/item_XXXX/gpt_oss_response.md` — tracked
- `dataapp_outputs/gpt55_full/item_XXXX_gpt5_5_response.md` — tracked

---

## Category C — SCRIPTS/DOCS

No untracked scripts or docs found outside of venv.

---

## Category D — MODELS

No model files found outside of venv (no .safetensors, .bin, .pt, etc.).

---

## Category E — SECRETS ⚠️

| File | Size | Action |
|------|------|--------|
| `./.env` | 602 bytes | **NEVER PUSH** — contains ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENAI_ADMIN_KEY, TRITON_API_KEY. Already gitignored. No action needed beyond confirming it stays excluded. |

**Verification:** `.env` is listed in `.gitignore` — confirmed safe as long as no `git add -f .env` is ever run.

---

## Category F — JUNK/SKIP

| Subcategory | Count | Size |
|-------------|-------|------|
| `./venv/` (Python virtualenv) | ~3,400 files | ~99 MB |
| `./.pytest_cache/` | ~6 files | ~0.1 MB |

No action. `.gitignore` already excludes `venv/`.

---

## What Was Pushed (this session)

| File | Category | Size |
|------|----------|------|
| `data/extractions_compact.csv` | B-extracted | 40 KB |
| `data/teacher_metadata_summary.csv` | B-extracted | 227 KB |
| `data/RUNTIME_RETRIEVAL_MANIFEST.md` | this file | — |

**Total new data pushed:** ~270 KB

---

## Key Findings

1. **No missing scripts/docs** — all pipeline scripts already tracked.
2. **No models on runtime** — no .safetensors/.pt files to flag.
3. **Secrets safe** — `.env` is gitignored and was never staged.
4. **`private.jsonl` is intentionally excluded** — competition question set, stays gitignored.
5. **Per-item metadata now preserved** — `teacher_metadata_summary.csv` captures 171 gpt4 RateLimitErrors (items 267-449) and token-cap events for sonnet/oss.
6. **`extractions.json` values now in CSV** — `extractions_compact.csv` has s/g/o per item (unpadded ids).
