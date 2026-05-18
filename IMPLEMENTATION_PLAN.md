# DataApp v0 — Full Implementation Plan

**Date:** 2026-05-18  
**Status:** Phase 0 fixes implemented. Blockers resolved. Phase 1 ready to execute.

### Resolved Blockers
1. ✅ **Extraction Source Code:** Copy extraction functions only (no Judger import). Self-contained, Windows-compatible.
2. ✅ **Test Fixture:** Rain will provide `tests/fixtures/run09_sample.jsonl` (50 Run 09 samples for validation).
3. ✅ **Phase 2 Budget:** Locked to Option B — real-time API, ~$235 total (Phase 1 ~$22 + Phase 2 ~$215).

---

## Context

DataApp v0 queries 3 frontier LLMs (Sonnet 4.6, GPT-5.4, Kimi K2.6) on 943 math problems and produces `dataset_manifest.jsonl` for SFT training of Qwen3-4B-Thinking via LoRA. Budget: ~$235 (Phase 1 validation $22 + Phase 2 full run $215). This is a one-shot pipeline; failures cost money.

The repo skeleton was committed at init time but several modules contain wrong model names, wrong prompts, mismatched field names, and missing functionality. This plan fixes all of them before any API call is made.

---

## Data Structure (private.jsonl)

943 items. Each item:
```json
{"question": "...", "id": 0}                            // single or multi
{"question": "...", "options": ["A", "B", ...], "id": 1} // MCQ
```

**No gold answers are provided.** Consensus is computed from 3-teacher agreement.

Type distribution (detected by `[ANS]` count and `options` presence):
- `mcq`: 300 items (has `options` field)
- `single`: 305 items (one or zero `[ANS]`, no options)
- `multi`: 338 items (2+ `[ANS]` placeholders)

---

## Required Response Format (LOCKED — from PROMPT_STRATEGY.md)

Each teacher response must end with exactly one `\boxed{...}`. Prompts enforce:

### System Prompt (all types)
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

### Type-Specific Suffixes
- **MCQ**: "Problem type: multiple choice. Solve and identify correct option letter. End with: \boxed{Letter}"
- **Single-answer**: "Problem type: single-answer. Exactly one final answer. End with: \boxed{answer}"
- **Multi-answer**: "Problem type: multi-answer. Verify count + order before final line. End with: \boxed{value1,value2,value3}"

**MCQ items**: Options are formatted as A. / B. / C. ... and appended to user message.  
**Multi-answer items**: Count verification is MANDATORY — do not add to single/MCQ.

---

## Extraction Logic

### Implementation Approach (DECISION: Copy functions, no external import)
Instead of importing `Judger` from competition repo at runtime (won't work on Windows, isolated workspace), we **copy ONLY the extraction functions** from `judger.py` + `utils.py` into `src/extraction.py`. Self-contained, ~200 lines, no external dependency.

Functions copied:
- **From judger.py:** `extract_ans()`, `extract_explicit_ans()`, `extract_boxed_answer()`, `extract_all_boxed()`, `normalize_answer()`, `clean_trailing()`, + constants (`GSM8K_ANS_PREFIX`, etc.)
- **From utils.py:** `last_boxed_only_string()`, `remove_boxed()`, `fix_sqrt()`, `fix_fracs()`, `fix_a_slash_b()`, + constants (`LATEX_CMDS`, `SIMPLE_REPLACE_MAP`)
- **From run_vllm_experiment.py:** `extract_letter()` (MCQ single-letter regex)

Wrapped as `DataAppExtractor` class with public methods:
- `extract(response: str) -> str` — main entry point
- `has_boxed(response: str) -> bool` — check for `\boxed{}`
- `count_boxes(response: str) -> int` — count `\boxed{}` blocks

### Extraction Flow (ported from judger.py)
1. `extract_ans()` calls `extract_explicit_ans()` first
2. `extract_explicit_ans()` checks for keyword anchors ("Therefore", GSM8K prefix, "answer is", etc.)
3. If `\boxed{}` is found in text: calls `extract_boxed_answer()`
4. `extract_boxed_answer()` strips `</think>` tags — only looks at content AFTER last `</think>`
5. Calls `extract_all_boxed()` on the post-think section:
   - Finds last contiguous group of `\boxed{}` blocks
   - If >1 box in that group: joins with ", " (multi-answer)
   - If 1 box: returns its content
6. Fallback: `last_boxed_only_string()` on full text (proper brace matching)
7. Final fallback: last LaTeX formula, then last number (only in non-strict mode)

### Code Snippet: Core Extraction Functions
```python
# In src/extraction.py (ported from competition repo's judger.py + utils.py)

def extract_ans(response: str, strict_extract: bool = True) -> str:
    """Main entry point for answer extraction."""
    # Try explicit keyword anchors first
    ans = extract_explicit_ans(response)
    if ans:
        return ans
    
    # Try boxed answer if explicit fails
    if "\\boxed{" in response:
        ans = extract_boxed_answer(response)
        if ans:
            return ans
    
    # Fallback: last boxed with proper brace matching
    if not strict_extract:
        return last_boxed_only_string(response) or ""
    return ""

def extract_boxed_answer(response: str) -> str:
    """Extract boxed answer, handling thinking tags."""
    # Strip </think> tags — only look at content after last </think>
    if "</think>" in response:
        response = response.split("</think>")[-1]
    
    # Find all boxed expressions
    boxes = extract_all_boxed(response)
    if boxes:
        # If multiple boxes in last group, join with ", " for multi-answer
        return ", ".join(boxes) if len(boxes) > 1 else boxes[0]
    
    return ""

def extract_all_boxed(response: str) -> list[str]:
    """Extract last contiguous group of \\boxed{} blocks."""
    import re
    # Match \boxed{...} with proper nested brace handling
    pattern = r"\\boxed\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
    matches = re.findall(pattern, response)
    return [m.strip() for m in matches[-3:] if m.strip()]  # Last 3 boxes max

class DataAppExtractor:
    """Public API for answer extraction."""
    def __init__(self, strict_extract: bool = True):
        self.strict_extract = strict_extract
    
    def extract(self, response: str) -> str:
        """Extract answer from response. Returns empty string if none found."""
        return extract_ans(response, strict_extract=self.strict_extract)
    
    def has_boxed(self, response: str) -> bool:
        """Check if response contains \\boxed{}."""
        return "\\boxed{" in response
    
    def count_boxes(self, response: str) -> int:
        """Count number of \\boxed{} blocks."""
        import re
        return len(re.findall(r"\\boxed\{", response))
```

### Key Extraction Rules
- `\boxed{\frac{1}{2}}` → returns `\frac{1}{2}` (nested braces handled)
- `\boxed{ A }` → returns `A` (trimmed)
- `\boxed{a} \boxed{b} \boxed{c}` (last group) → returns `a, b, c`
- `\boxed{a,b,c}` (single box, comma-separated) → returns `a,b,c`
- Empty response or no box → returns `""` in strict mode, last number otherwise
- Models with thinking tags: extraction only looks after `</think>`

### has_boxed() and count_boxed()
- `has_boxed()`: checks `"\\boxed{"` in response (simple string check — OK for format compliance)
- `count_boxed()`: calls `extract_all_boxed()` on the response, returns len

---

## Output Structure (per IMPLEMENTATION.md spec)

```
dataapp_outputs/
  item_0000/
    sonnet_response.md        # raw response formatted as markdown + metadata footer
    sonnet_metadata.json      # tokens, timing, model, request_id, error
    gpt5_4_response.md
    gpt5_4_metadata.json
    kimi_response.md
    kimi_metadata.json
    extractions.json          # {sonnet: {extracted_answer, has_boxed, n_boxes}, ...}
  dataset_manifest.jsonl      # one line per completed item (consensus + per-teacher answers)
  cost_log.jsonl              # one line per API call (timestamp, item_id, model, tokens, cost)
```

Teacher keys used throughout: `sonnet`, `gpt5_4`, `kimi` (consistent naming).

### Manifest Entry Schema
```json
{
  "id": 0,
  "question_type": "multi_free",
  "sonnet_answer": "3, 5",
  "gpt5_4_answer": "3, 5",
  "kimi_answer": "3, 5",
  "agreement_type": "3/3",
  "which_agreed": ["sonnet", "gpt5_4", "kimi"],
  "consensus_answer": "3, 5",
  "any_errors": false
}
```

### Consensus Logic
- Count teacher agreements on extracted answers (exclude empty extractions)
- `3/3`: all three agree → consensus = that answer
- `2/3`: two agree → consensus = majority answer
- `1/3` or `0/3`: no majority → consensus = modal answer (or "" if all empty)
- Tie-breaking: lexicographic sort on tied answers

---

## Files to Fix (ordered by criticality)

### 1. `requirements.txt` — ADD tenacity, fix versions
Currently missing `tenacity`. `anthropic==0.28.0` is too old for Sonnet 4.6.
```
anthropic>=0.40.0
openai>=1.50.0
python-dotenv>=1.0.0
pyyaml>=6.0
tenacity>=8.2.0
tqdm>=4.65.0
```
Remove: `requests==2.31.0`, `black==24.1.0` (dev tool, not runtime dep)

### 2. `config.yaml` — FIX model names, URL, paths, add alert thresholds
- `openai.name`: "gpt-5.4-turbo" → **"gpt-5.4"**
- `moonshot.name`: "moonshot-v1" → **"kimi-k2.6"**
- `moonshot.base_url`: "https://api.moonshot.cn/v1" → **"https://api.moonshot.ai/v1"**
- `paths.data_dir`: "data" → **"."** (private.jsonl is at repo root, not in data/)
- Add `cost_alert_thresholds: [25, 50, 75, 100]`
- Add `validation_stratification: {mcq: 15, single_free: 15, multi_free: 15}`
- Add per-model temperature/top_p under each model config
- Remove unsupported sampling params: `top_k`, `min_p`, `repetition_penalty`

### 3. `src/prompts.py` — COMPLETE REWRITE (MOST CRITICAL)
Current prompts are generic and do NOT match PROMPT_STRATEGY.md.  
Replace with:
- `SYSTEM_PROMPT` (locked conciseness-focused system prompt)
- `SINGLE_ANSWER_SUFFIX`, `MULTI_ANSWER_SUFFIX`, `MCQ_SUFFIX`
- `detect_question_type(item: dict) -> str` — "mcq" / "single_free" / "multi_free"
  - MCQ: `isinstance(item.get("options"), list) and len(item["options"]) > 0`
  - Multi: `item["question"].count("[ANS]") > 1`
  - Single: otherwise
- `build_messages(question: str, question_type: str, options: list | None) -> list[dict]`
  - Returns `[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": ...}]`
  - MCQ: appends options as "A. ... B. ..." + MCQ_SUFFIX
  - Multi: appends MULTI_ANSWER_SUFFIX
  - Single: appends SINGLE_ANSWER_SUFFIX

### 4. `src/api_clients.py` — FIX Anthropic system message, fix defaults, align return schema
Critical bug: `AnthropicClient.query()` passes system message inside `messages` list. Anthropic SDK requires system as a **separate parameter**.

Fix pattern:
```python
system = next((m["content"] for m in messages if m["role"] == "system"), "")
user_messages = [m for m in messages if m["role"] != "system"]
resp = self.client.messages.create(
    model=self.model,
    system=system,
    messages=user_messages,
    ...
)
```

Also fix:
- Default model names (align with config)
- Return dict: add `hit_token_cap`, `generation_time_s`, `request_id`, `error` fields
- Replace manual retry loop with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))` from tenacity
- Remove cost calculation from clients (cost is tracked by CostTracker, not clients)
- Add `_error_response()` helper for failed calls

### 5. `src/cost_tracker.py` — ADD file persistence + threshold alerts
Current tracker is in-memory only. If process dies, cost is lost.

Add:
- `__init__(log_path: str, alert_thresholds: list[float])`
- `_load_existing()` — reads existing cost_log.jsonl on init (resume)
- `record(item_id, model, input_tokens, output_tokens)` — write to file, check thresholds
- Threshold alert: print warning to stdout when crossing $25/$50/$75/$100
- Track `alerted` set to avoid double-alerting

Pricing (real-time, for validation phase):
```python
PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},  # per million tokens
    "gpt-5.4":            {"input": 2.50, "output": 15.00},
    "kimi-k2.6":          {"input": 0.60, "output": 2.50},
}
```

### 6. `src/storage.py` — ADD Storage class alongside utilities
Keep existing utility functions (atomic_write_json, append_jsonl, read_jsonl, get_completed_ids).
Add `Storage` class:
```python
class Storage:
    def __init__(self, output_dir: str, manifest_path: str)
    def item_dir(self, item_id: int) -> Path
    def save_response(self, item_id, teacher_key, response_data, prompt)
    def save_extraction(self, item_id, teacher_key, extracted, has_boxed, n_boxes)
    def append_manifest(self, entry: dict)
    def completed_items(self) -> set[int]
```
All writes use `_atomic_write()` (temp → rename pattern). Never plain `open(path, "w")`.

### 7. `src/orchestrator.py` — FIX field names, type detection, output format, teacher keys
- `item.get("problem")` → `item.get("question")` 
- Add `detect_question_type(item)` call at top of `process_item()`
- Use `build_messages(question, question_type, options)` instead of `get_conversation()`
- Teacher keys throughout: `"sonnet"`, `"gpt5_4"`, `"kimi"` (not `"anthropic"`, `"openai"`, `"moonshot"`)
- Use `Storage` class for saving
- Use updated `CostTracker.record()` with persistent logging
- Fix manifest entry schema to match spec above
- `compute_consensus()` returns `{type, which_agreed, answer}` dict

### 8. `src/__init__.py` — Update exports
Add new exports: `Storage`, `detect_question_type`, `build_messages`

### 9. `scripts/run_validation.py` — FIX stratification
Current stratification uses `item.get("type")` (field doesn't exist in private.jsonl).

Fix: use `detect_question_type(item)` to classify each item, then sample 15 of each.
Keep seed=42 for reproducibility.
Output dir: `dataapp_outputs/validation/` (separate from full run outputs).
Use real-time pricing (use_batch=False).

### 10. `scripts/run_full.py` — MINOR fixes
- Fix data loading (updated paths)
- Pass `use_batch=False` for v0 (batch API is post-v0)
- tqdm progress bar already present ✓

### 11. `scripts/analyze_results.py` — FIX metric calculations
- Format compliance: per-teacher (check each teacher's extracted answer ≠ "")
- Multi-answer count accuracy: compare comma-count in extracted vs expected [ANS] count from question
- Token stats: load from per-item metadata.json files
- Gate checks against PROMPT_STRATEGY.md thresholds

### 12. `tests/test_extraction.py` — CREATE
Validate extraction port against Run 09 data from competition repo.

```python
# Load samples from competition repo results
COMP_RESULTS = Path("/home/dvaneetv/private/151B_SP26_Competition/results/")
# Find run09 or run14b jsonl file, load 50 items
# For each: run extractor.extract(item["response"]) and compare to item["extracted_answer"]
# Assert 100% match
```

---

## Testing Plan

### Step 1: Dependency install (after requirements.txt fix)
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

### Step 2: Extraction validation (100% match required)
```bash
python tests/test_extraction.py
```
- Loads 50 samples from `tests/fixtures/run09_sample.jsonl` (provided by Rain)
- Each sample: `{id, response, extracted_answer}` from competition Run 09
- Runs `DataAppExtractor.extract()` on each response
- Compares to `extracted_answer` field  
- **Must be 100% match.** If not, port bug exists — fix before proceeding.

(Rain provides fixture; dataApp has no external dependency on competition repo at runtime)

### Step 3: API client smoke test (1 item each, no data saved)
```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
from src.api_clients import SonnetClient, GPTClient, KimiClient
from src.prompts import build_messages, detect_question_type

item = {'question': 'What is 2+2?', 'id': 9999}
qt = detect_question_type(item)
messages = build_messages(item['question'], qt, None)

# Test each client
for name, cls in [('Sonnet', SonnetClient), ('GPT', GPTClient), ('Kimi', KimiClient)]:
    r = cls().call(messages, temperature=0.6, max_tokens=100)
    print(f'{name}: error={r[\"error\"]}, tokens={r[\"output_tokens\"]}')
"
```
Expected: all 3 return `error=None` with >0 output tokens.

### Step 4: Single item end-to-end test
Process item 0 through the full orchestrator:
- Sends to all 3 APIs
- Extracts answers
- Writes outputs to `dataapp_outputs/item_0000/`
- Appends to manifest

Verify files exist and are valid JSON/markdown.

### Step 5: Phase 1 validation (45 items, ~$10-15)
```bash
python scripts/run_validation.py
```
Thresholds to pass (per PROMPT_STRATEGY.md):
- Format compliance ≥95% per teacher
- Multi-answer count accuracy ≥90%
- 3/3 agreement ≥40%
- Median tokens 3k-8k per teacher
- p95 tokens <14k

```bash
python scripts/analyze_results.py
```
Report full metrics to Rain. **Wait for approval before Phase 2.**

### Step 6: Phase 2 (943 items) — DECISION: Real-time API, ~$235 total
```bash
python scripts/run_full.py
```

**LOCKED DECISION (Rain):** Option B — real-time Phase 2 (~$235 total spend).
- Phase 1 validation: ~$22
- Phase 2 full run: ~$215
- Total: ~$237 (vs $89 locked budget, but prioritizes data quality + faster iteration)

**Condition:** Only proceed to Phase 2 if Phase 1 passes ALL thresholds:
- Format compliance ≥95% per teacher
- Multi-answer count accuracy ≥90%
- 3/3 agreement ≥40%
- Median tokens 3k-8k per teacher
- p95 tokens <14k

If Phase 1 fails any threshold, debug BEFORE burning $215 on Phase 2.

Resume-safe: will skip already-completed items.

---

## Locked Invariants (do not change)

| Parameter | Value |
|-----------|-------|
| Sonnet model | `claude-sonnet-4-6` |
| GPT model | `gpt-5.4` |
| Kimi model | `kimi-k2.6` |
| temperature | `0.6` |
| top_p | `0.95` |
| max_tokens | `16384` |
| Validation sample | 15 MCQ + 15 single + 15 multi |
| Atomic writes | Always (tmp → rename) |
| Resume | Always (skip completed item IDs) |

---

## Files Modified Summary

| File | Change Type |
|------|-------------|
| `requirements.txt` | Targeted fixes |
| `config.yaml` | Targeted fixes |
| `src/prompts.py` | Complete rewrite |
| `src/api_clients.py` | Targeted fixes |
| `src/cost_tracker.py` | Extend with persistence + alerts |
| `src/storage.py` | Add Storage class |
| `src/orchestrator.py` | Targeted fixes |
| `src/__init__.py` | Update exports |
| `scripts/run_validation.py` | Fix stratification |
| `scripts/analyze_results.py` | Fix metric calculations |
| `tests/test_extraction.py` | Create new |

**Not modified:** `src/extraction.py` (already correct), `scripts/run_full.py` (minor only)

---

## What NOT to do

- No async/await (threading only for parallel teacher calls)
- No abstract base classes or factory patterns beyond existing TeacherClient ABC
- No UI of any kind
- No new dependencies beyond what's listed above
- Do not import anything from competition repo at runtime (extraction.py only, via sys.path)
- Do not modify locked prompts
- Do not change sampling hyperparameters
