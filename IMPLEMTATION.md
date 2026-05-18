# dataApp v0 — Full Implementation Doc

**Implementation agent: claude_vscode** (operating in the dataApp repo, separate from the competition repo).

---

## ⚠️ NB NB NB — SIMPLICITY MANDATE (READ FIRST, OBEY ALWAYS)

This is a **one-shot, time-constrained data collection pipeline**. Read this section before every implementation decision.

1. **Keep it simple.** Always err on the conservative, boring, well-trodden path. No clever abstractions. No premature optimization. No "this would be more elegant if..." rewrites.

2. **No UI.** No web dashboards, no progress visualizations, no streamlit/gradio/anything. CLI scripts only. Logs to stdout + files. That's it.

3. **No heavy debugging budget.** If a design choice looks like it'll take >30min to debug if it goes wrong, pick a simpler design. We don't have time for clever-but-fragile.

4. **Standard libraries only.** Use the libraries in `requirements.txt`. Don't add new ones unless absolutely necessary, and ask Rain before adding any.

5. **Boring data structures.** Plain dicts, lists, JSON. No custom classes unless they earn their keep. No pydantic schemas unless they prevent a real bug.

6. **No async complexity unless required.** Use plain threading or sequential calls. Async is only justified for the batch API path (Phase 2 v1+), not for Phase 1.

7. **Atomic writes for output files. Period.** This is the one piece of complexity that's non-negotiable because corruption costs money.

8. **When in doubt: do the dumbest thing that could work, and ship it.**

---

## Project Goal

Query 3 frontier LLMs (Sonnet 4.6, GPT-5.4, Kimi K2.6) on 943 math problems. Save reasoning traces. Output is SFT training data for Qwen3-4B-Thinking.

**Budget: ~$89.** Use Batch API for Anthropic + OpenAI (50% off). Kimi uses standard API.

## Directory Structure

```
dataapp/
├── PROJECT_BRIEF.md
├── DATAAPP_V0_DESIGN_SPEC.md
├── DATAAPP_PROMPT_STRATEGY_LOCKED.md
├── IMPLEMENTATION.md (this file)
├── private.jsonl                # Rain provides
├── .env                          # gitignored
├── .gitignore
├── config.yaml
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── extraction.py            # ported from competition repo
│   ├── prompts.py               # locked prompts
│   ├── api_clients.py           # 3 API wrappers
│   ├── cost_tracker.py
│   ├── storage.py               # atomic writes, resume
│   └── orchestrator.py          # main loop
├── scripts/
│   ├── run_validation.py        # 45-item phase
│   ├── run_full_batch.py        # 943-item phase, batch API
│   └── analyze_results.py
├── tests/
│   └── test_extraction.py       # extractor audit on Run 09 data
└── dataapp_outputs/             # gitignored
    ├── item_001/
    ├── item_002/
    ...
    └── dataset_manifest.jsonl
```

## Dependencies (requirements.txt)

Minimal. Don't add anything else without Rain's approval.

```
anthropic>=0.40.0
openai>=1.50.0
python-dotenv>=1.0.0
pyyaml>=6.0
tenacity>=8.2.0
```

(No pydantic. No requests beyond what the SDKs use. No fastapi/streamlit/anything UI.)

## .env (Rain creates locally, NEVER commit)

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
MOONSHOT_API_KEY=sk-...
```

## .gitignore

```
.env
dataapp_outputs/
*.pyc
__pycache__/
.pytest_cache/
private.jsonl
```

## config.yaml

```yaml
# Model configuration
models:
  sonnet:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.6
    max_tokens: 16384
    top_p: 0.95
  gpt5_4:
    provider: openai
    model: gpt-5.4
    temperature: 0.6
    max_tokens: 16384
    top_p: 0.95
  kimi:
    provider: moonshot
    model: kimi-k2.6
    temperature: 0.6
    max_tokens: 16384
    top_p: 0.95
    base_url: https://api.moonshot.ai/v1

# Data paths
input_file: private.jsonl
output_dir: dataapp_outputs
manifest_file: dataapp_outputs/dataset_manifest.jsonl
cost_log: dataapp_outputs/cost_log.jsonl

# Execution
retry_max_attempts: 3
retry_initial_wait_seconds: 2
retry_backoff_multiplier: 2

# Cost alerts (USD)
cost_alert_thresholds: [25, 50, 75, 100]

# Phase 1 validation
validation_sample_size: 45
validation_stratification:
  mcq: 15
  single_free: 15
  multi_free: 15
```

## Module 1: `src/extraction.py`

**Port from competition repo.** Copy these functions verbatim:

### From `judger.py` (competition repo):
- `extract_ans()`
- `extract_explicit_ans()`
- `extract_boxed_answer()`
- `extract_all_boxed()`
- `normalize_answer()`
- `clean_trailing()`
- Any helpers these call

### From `utils.py` (competition repo):
- `last_boxed_only_string()`
- `remove_boxed()`
- `fix_sqrt()`
- `fix_fracs()`
- `fix_a_slash_b()`
- `LATEX_CMDS`, `SIMPLE_REPLACE_MAP`, etc. (constants needed by helpers)

### From `run_vllm_experiment.py` (competition repo):
- `extract_letter()` — for MCQ

### Public API for dataApp:

```python
class Extractor:
    """Wraps competition repo's extraction logic. Kaggle-aligned."""
    
    def __init__(self):
        # Initialize underlying judger
        self._judger = _create_judger()  # internal factory
    
    def extract(self, response: str, is_mcq: bool) -> str:
        """Extract answer from a model response.
        
        For MCQ: returns single letter (A/B/C/D/E) or "".
        For free-form: returns normalized answer string or "".
        Multi-answer free-form: returns comma-space-joined string ("a, b, c").
        
        Returns "" if no answer extractable.
        """
        if is_mcq:
            return extract_letter(response)
        return self._judger.extract_ans(response) or ""
    
    def has_boxed(self, response: str) -> bool:
        """True if a closed \\boxed{} appears after the last </think>."""
        # Port from run_vllm_experiment.py
        ...
    
    def count_boxes(self, response: str) -> int:
        """Count top-level \\boxed{} occurrences."""
        # Port count_top_level_boxes from run_vllm_sc.py
        ...
```

### Edge cases the extractor must handle (test these):
1. No `\boxed{}` at all → return ""
2. Multiple `\boxed{}` blocks → return last contiguous group, comma-joined
3. Nested braces inside box (e.g., `\boxed{\frac{1}{2}}`) → return inner content correctly
4. `</think>` tag present → strip before extracting
5. Box with whitespace (`\boxed{ A }`) → return "A" trimmed
6. Empty box (`\boxed{}`) → return "" (or whatever judger does, match it)
7. Per-slot multi-answer (`\boxed{a} \boxed{b} \boxed{c}`) → return "a, b, c"

### Validation test (tests/test_extraction.py)

Run on 50 samples from `results/run14b_sc8_v1_private943_tok32k_pp1.jsonl` (Rain provides). For each sample:
1. Run our extractor on the `response` field
2. Compare to the existing `extracted_answer` field
3. They should match 100%

If less than 100%, there's a port bug. Fix before proceeding.

## Module 2: `src/prompts.py`

```python
"""Locked prompts from DATAAPP_PROMPT_STRATEGY_LOCKED.md."""

SYSTEM_PROMPT = """You are generating a math solution trace for supervised fine-tuning of a smaller reasoning model.

Your goal: produce a correct, clear, concise solution. Not flashy. Not verbose. Teachable.

Rules:
1. Show essential reasoning steps. Avoid unnecessary verification loops, restarts, or exploration of alternative paths.
2. Use exact symbolic form when natural (fractions, radicals, π). Use decimals only when the problem asks for them.
3. Do not use \\boxed{} anywhere except the final answer.
4. End with exactly one \\boxed{...} containing the final answer.
5. Briefly identify what is being asked before solving."""

SINGLE_ANSWER_SUFFIX = """Problem type: single-answer.

There is exactly one final answer. End with: \\boxed{answer}"""

MULTI_ANSWER_SUFFIX = """Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \\boxed{...} with comma-separated values

End with: \\boxed{value1,value2,value3}"""

MCQ_SUFFIX = """Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \\boxed{Letter}"""


def build_messages(question: str, question_type: str, options: list = None) -> list[dict]:
    """Build the messages array for an API call.
    
    Args:
        question: Question text from private.jsonl
        question_type: One of "mcq", "single_free", "multi_free"
        options: List of options for MCQ items (or None)
    
    Returns:
        List of {"role": "system"|"user", "content": str} dicts
    """
    if question_type == "mcq":
        suffix = MCQ_SUFFIX
        if options:
            labels = [chr(65 + i) for i in range(len(options))]
            opts_text = "\n".join(f"{lbl}. {opt.strip()}" for lbl, opt in zip(labels, options))
            user_content = f"{question}\n\nOptions:\n{opts_text}\n\n{suffix}"
        else:
            user_content = f"{question}\n\n{suffix}"
    elif question_type == "multi_free":
        user_content = f"{question}\n\n{MULTI_ANSWER_SUFFIX}"
    else:  # single_free
        user_content = f"{question}\n\n{SINGLE_ANSWER_SUFFIX}"
    
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]


def detect_question_type(item: dict) -> str:
    """Determine question type from item structure.
    
    MCQ: has 'options' field as a non-empty list
    Multi-free: question text contains multiple [ANS] placeholders OR
                gold answer is a list with len > 1
    Single-free: otherwise
    """
    if isinstance(item.get("options"), list) and item["options"]:
        return "mcq"
    
    # Check question text for [ANS] placeholders
    question = item.get("question", "")
    ans_count = question.count("[ANS]")
    if ans_count > 1:
        return "multi_free"
    
    # Check gold answer (if present) for multi-value
    gold = item.get("answer") or item.get("gold")
    if isinstance(gold, list) and len(gold) > 1:
        return "multi_free"
    
    return "single_free"
```

## Module 3: `src/api_clients.py`

```python
"""API clients for the 3 teachers.

Each client has the same interface:
    client.call(messages: list[dict], **sampling_params) -> dict

Returns a dict with:
    {
        "response": str,        # raw model output
        "input_tokens": int,
        "output_tokens": int,
        "hit_token_cap": bool,
        "generation_time_s": float,
        "model": str,
        "request_id": str | None,
        "error": str | None,    # if call failed
    }
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional

import anthropic
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential


class TeacherClient(ABC):
    """Abstract base for teacher API clients."""
    
    @abstractmethod
    def call(self, messages: list[dict], temperature: float, max_tokens: int, **kwargs) -> dict:
        pass


class SonnetClient(TeacherClient):
    """Claude Sonnet 4.6 via Anthropic API."""
    
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def call(self, messages: list[dict], temperature: float, max_tokens: int, **kwargs) -> dict:
        start = time.time()
        
        # Anthropic separates system from messages
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]
        
        try:
            resp = self.client.messages.create(
                model=self.model,
                system=system,
                messages=user_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "response": resp.content[0].text if resp.content else "",
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
                "hit_token_cap": resp.stop_reason == "max_tokens",
                "generation_time_s": time.time() - start,
                "model": self.model,
                "request_id": resp.id,
                "error": None,
            }
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start)


class GPTClient(TeacherClient):
    """GPT-5.4 via OpenAI API."""
    
    def __init__(self, model: str = "gpt-5.4"):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def call(self, messages: list[dict], temperature: float, max_tokens: int, **kwargs) -> dict:
        start = time.time()
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "response": resp.choices[0].message.content or "",
                "input_tokens": resp.usage.prompt_tokens,
                "output_tokens": resp.usage.completion_tokens,
                "hit_token_cap": resp.choices[0].finish_reason == "length",
                "generation_time_s": time.time() - start,
                "model": self.model,
                "request_id": resp.id,
                "error": None,
            }
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start)


class KimiClient(TeacherClient):
    """Kimi K2.6 via Moonshot API (OpenAI-compatible interface)."""
    
    def __init__(self, model: str = "kimi-k2.6"):
        self.client = OpenAI(
            api_key=os.environ["MOONSHOT_API_KEY"],
            base_url="https://api.moonshot.ai/v1",
        )
        self.model = model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def call(self, messages: list[dict], temperature: float, max_tokens: int, **kwargs) -> dict:
        start = time.time()
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "response": resp.choices[0].message.content or "",
                "input_tokens": resp.usage.prompt_tokens,
                "output_tokens": resp.usage.completion_tokens,
                "hit_token_cap": resp.choices[0].finish_reason == "length",
                "generation_time_s": time.time() - start,
                "model": self.model,
                "request_id": resp.id,
                "error": None,
            }
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start)


def _error_response(error: str, model: str, elapsed: float) -> dict:
    return {
        "response": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "hit_token_cap": False,
        "generation_time_s": elapsed,
        "model": model,
        "request_id": None,
        "error": error,
    }
```

## Module 4: `src/cost_tracker.py`

```python
"""Track API costs and alert at thresholds."""

import json
from pathlib import Path
from datetime import datetime, timezone

# Pricing per million tokens (May 2026, batch API where applicable)
PRICING = {
    "claude-sonnet-4-6": {"input": 1.50, "output": 7.50, "batch": True},
    "gpt-5.4": {"input": 1.25, "output": 7.50, "batch": True},
    "kimi-k2.6": {"input": 0.60, "output": 2.50, "batch": False},
}

# Real-time pricing (for validation phase)
PRICING_REALTIME = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "gpt-5.4": {"input": 2.50, "output": 15.00},
    "kimi-k2.6": {"input": 0.60, "output": 2.50},
}


class CostTracker:
    def __init__(self, log_path: str, alert_thresholds: list[float]):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.alert_thresholds = sorted(alert_thresholds)
        self.total_cost = 0.0
        self.alerted = set()
        self._load_existing()
    
    def _load_existing(self):
        """Resume cost tracking from prior runs."""
        if self.log_path.exists():
            with open(self.log_path) as f:
                for line in f:
                    entry = json.loads(line)
                    self.total_cost += entry["cost_usd"]
                    for t in self.alert_thresholds:
                        if self.total_cost >= t:
                            self.alerted.add(t)
    
    def record(self, item_id: str, model: str, input_tokens: int, output_tokens: int, use_batch: bool = True) -> float:
        """Record a single API call and return its cost."""
        pricing = PRICING if use_batch else PRICING_REALTIME
        if model not in pricing:
            print(f"WARNING: Unknown model {model}, skipping cost")
            return 0.0
        
        p = pricing[model]
        cost = (input_tokens * p["input"] / 1_000_000) + (output_tokens * p["output"] / 1_000_000)
        self.total_cost += cost
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "item_id": item_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "running_total_usd": self.total_cost,
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Alert check
        for t in self.alert_thresholds:
            if self.total_cost >= t and t not in self.alerted:
                print(f"\n*** COST ALERT: total spend has crossed ${t} (currently ${self.total_cost:.2f}) ***\n")
                self.alerted.add(t)
        
        return cost
```

## Module 5: `src/storage.py`

```python
"""File I/O with atomic writes and resume support."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone


class Storage:
    def __init__(self, output_dir: str, manifest_path: str):
        self.output_dir = Path(output_dir)
        self.manifest_path = Path(manifest_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    def item_dir(self, item_id: str | int) -> Path:
        """Get directory for a specific item."""
        d = self.output_dir / f"item_{int(item_id):04d}"
        d.mkdir(exist_ok=True)
        return d
    
    def save_response(self, item_id: str | int, teacher_key: str, response_data: dict, prompt: str):
        """Save a teacher's response atomically.
        
        Writes to:
            item_XXX/{teacher_key}_response.md
            item_XXX/{teacher_key}_metadata.json
        """
        d = self.item_dir(item_id)
        
        # Save markdown response
        md_path = d / f"{teacher_key}_response.md"
        md_content = self._format_response_md(response_data, prompt, teacher_key)
        _atomic_write(md_path, md_content)
        
        # Save metadata JSON
        meta_path = d / f"{teacher_key}_metadata.json"
        meta = {
            "teacher": teacher_key,
            "model": response_data["model"],
            "input_tokens": response_data["input_tokens"],
            "output_tokens": response_data["output_tokens"],
            "hit_token_cap": response_data["hit_token_cap"],
            "generation_time_s": response_data["generation_time_s"],
            "request_id": response_data["request_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": response_data["error"],
        }
        _atomic_write(meta_path, json.dumps(meta, indent=2))
    
    def save_extraction(self, item_id: str | int, teacher_key: str, extracted: str, has_boxed: bool, n_boxes: int):
        """Append extraction result to per-item extraction file."""
        d = self.item_dir(item_id)
        ext_path = d / "extractions.json"
        
        existing = {}
        if ext_path.exists():
            with open(ext_path) as f:
                existing = json.load(f)
        
        existing[teacher_key] = {
            "extracted_answer": extracted,
            "has_boxed": has_boxed,
            "n_boxes": n_boxes,
        }
        _atomic_write(ext_path, json.dumps(existing, indent=2))
    
    def append_manifest(self, manifest_entry: dict):
        """Append a manifest entry. NOT atomic per-call but rare enough not to matter."""
        with open(self.manifest_path, "a") as f:
            f.write(json.dumps(manifest_entry) + "\n")
    
    def completed_items(self) -> set[int]:
        """Return set of item_ids that already have complete output (all 3 teachers).
        
        Used for resume: skip items already done.
        An item is "complete" if all 3 teacher response files exist AND the
        manifest has an entry for it.
        """
        if not self.manifest_path.exists():
            return set()
        
        completed = set()
        with open(self.manifest_path) as f:
            for line in f:
                entry = json.loads(line)
                completed.add(int(entry["id"]))
        return completed
    
    def _format_response_md(self, response_data: dict, prompt: str, teacher_key: str) -> str:
        return f"""# {teacher_key} Response

## Prompt
```
{prompt}
```

## Reasoning + Response
{response_data['response']}

## Metadata
- Model: {response_data['model']}
- Input tokens: {response_data['input_tokens']}
- Output tokens: {response_data['output_tokens']}
- Hit token cap: {response_data['hit_token_cap']}
- Generation time: {response_data['generation_time_s']:.2f}s
- Request ID: {response_data['request_id']}
- Error: {response_data['error'] or 'none'}
"""


def _atomic_write(path: Path, content: str):
    """Write to a temp file then rename. Prevents corruption mid-write."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp, path)
```

## Module 6: `src/orchestrator.py`

```python
"""Main orchestration: load items, dispatch to 3 teachers, compute consensus."""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from collections import Counter

from .api_clients import SonnetClient, GPTClient, KimiClient
from .extraction import Extractor
from .prompts import build_messages, detect_question_type
from .storage import Storage
from .cost_tracker import CostTracker


TEACHERS = ["sonnet", "gpt5_4", "kimi"]


def run_item(item: dict, clients: dict, extractor: Extractor, storage: Storage, cost_tracker: CostTracker, use_batch: bool = False) -> dict:
    """Run one item through all 3 teachers (parallel) and compute consensus.
    
    Returns a manifest entry dict.
    """
    item_id = item["id"]
    question_type = detect_question_type(item)
    is_mcq = question_type == "mcq"
    
    options = item.get("options")
    messages = build_messages(item["question"], question_type, options)
    
    # Use the user message as the "prompt" for logging
    prompt_for_log = messages[-1]["content"]
    
    # Parallel API calls to 3 teachers
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_teacher = {
            executor.submit(
                clients[t].call,
                messages=messages,
                temperature=0.6,
                max_tokens=16384,
            ): t for t in TEACHERS
        }
        for fut in as_completed(future_to_teacher):
            t = future_to_teacher[fut]
            results[t] = fut.result()
    
    # Save responses + metadata, track cost, extract answers
    extractions = {}
    for t in TEACHERS:
        r = results[t]
        storage.save_response(item_id, t, r, prompt_for_log)
        cost_tracker.record(item_id, r["model"], r["input_tokens"], r["output_tokens"], use_batch=use_batch)
        
        extracted = extractor.extract(r["response"], is_mcq)
        has_boxed = extractor.has_boxed(r["response"])
        n_boxes = extractor.count_boxes(r["response"])
        extractions[t] = extracted
        storage.save_extraction(item_id, t, extracted, has_boxed, n_boxes)
    
    # Compute consensus
    consensus = compute_consensus(extractions)
    
    # Build manifest entry
    manifest = {
        "id": item_id,
        "question_type": question_type,
        "gold": item.get("answer") or item.get("gold"),
        "sonnet_answer": extractions["sonnet"],
        "gpt5_4_answer": extractions["gpt5_4"],
        "kimi_answer": extractions["kimi"],
        "agreement_type": consensus["type"],
        "which_agreed": consensus["which_agreed"],
        "consensus_answer": consensus["answer"],
        "any_errors": any(results[t]["error"] for t in TEACHERS),
    }
    storage.append_manifest(manifest)
    return manifest


def compute_consensus(extractions: dict) -> dict:
    """Compute agreement type from 3 teacher extractions.
    
    Returns:
        {
            "type": "3/3" | "2/3" | "1/3" | "0/3",
            "which_agreed": list of teacher keys that share modal answer,
            "answer": modal answer string (or "" if all unique/empty),
        }
    """
    # Exclude empty extractions from agreement (treat as missing)
    valid = {t: a for t, a in extractions.items() if a}
    
    if not valid:
        return {"type": "0/3", "which_agreed": [], "answer": ""}
    
    counts = Counter(valid.values())
    most_common_ans, most_count = counts.most_common(1)[0]
    
    which_agreed = [t for t, a in valid.items() if a == most_common_ans]
    
    if most_count == 3:
        type_str = "3/3"
    elif most_count == 2:
        type_str = "2/3"
    else:
        type_str = "1/3"
    
    return {
        "type": type_str,
        "which_agreed": which_agreed,
        "answer": most_common_ans,
    }


def load_items(jsonl_path: str) -> list[dict]:
    """Load all items from private.jsonl."""
    items = []
    with open(jsonl_path) as f:
        for line in f:
            items.append(json.loads(line))
    return items


def run_orchestrator(input_file: str, storage: Storage, cost_tracker: CostTracker, item_filter: callable = None, use_batch: bool = False):
    """Main loop. Resume-safe.
    
    Args:
        input_file: path to private.jsonl
        storage: Storage instance
        cost_tracker: CostTracker instance
        item_filter: optional callable(item) -> bool to select items
        use_batch: whether to use batch API pricing for cost tracking
    """
    clients = {
        "sonnet": SonnetClient(),
        "gpt5_4": GPTClient(),
        "kimi": KimiClient(),
    }
    extractor = Extractor()
    
    items = load_items(input_file)
    if item_filter:
        items = [i for i in items if item_filter(i)]
    
    completed = storage.completed_items()
    pending = [i for i in items if int(i["id"]) not in completed]
    
    print(f"Total items: {len(items)}")
    print(f"Already done: {len(completed)}")
    print(f"Pending: {len(pending)}")
    print(f"Current cost: ${cost_tracker.total_cost:.2f}")
    
    for i, item in enumerate(pending, 1):
        print(f"\n[{i}/{len(pending)}] item_id={item['id']}...")
        try:
            manifest = run_item(item, clients, extractor, storage, cost_tracker, use_batch=use_batch)
            print(f"  → {manifest['agreement_type']} (consensus: {manifest['consensus_answer'][:50]})")
            print(f"  → running cost: ${cost_tracker.total_cost:.2f}")
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            # Don't crash on individual item failures
            continue
```

## Module 7: `scripts/run_validation.py`

```python
"""Phase 1: 45-item stratified validation run (real-time API, ~$10-15)."""

import random
import yaml
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.storage import Storage
from src.cost_tracker import CostTracker
from src.orchestrator import run_orchestrator
from src.prompts import detect_question_type


def select_validation_sample(items: list[dict], counts: dict, seed: int = 42) -> list[dict]:
    """Stratified random sample.
    
    Args:
        items: All items from private.jsonl
        counts: {"mcq": 15, "single_free": 15, "multi_free": 15}
        seed: For reproducibility
    
    Returns:
        Selected items.
    """
    rng = random.Random(seed)
    
    by_type = {"mcq": [], "single_free": [], "multi_free": []}
    for item in items:
        t = detect_question_type(item)
        by_type[t].append(item)
    
    selected = []
    for t, n in counts.items():
        pool = by_type[t]
        if len(pool) < n:
            print(f"WARNING: requested {n} {t} items but only {len(pool)} available")
            selected.extend(pool)
        else:
            selected.extend(rng.sample(pool, n))
    
    return selected


def main():
    config = yaml.safe_load(open("config.yaml"))
    
    # Override output dir to keep validation separate
    output_dir = "dataapp_outputs/validation"
    manifest = "dataapp_outputs/validation/manifest.jsonl"
    
    storage = Storage(output_dir, manifest)
    cost_tracker = CostTracker("dataapp_outputs/validation/cost_log.jsonl", config["cost_alert_thresholds"])
    
    # Load all items, then filter to validation sample
    with open(config["input_file"]) as f:
        all_items = [json.loads(line) for line in f]
    
    sample = select_validation_sample(all_items, config["validation_stratification"])
    sample_ids = {int(i["id"]) for i in sample}
    
    print(f"Validation sample: {len(sample)} items")
    print(f"IDs: {sorted(sample_ids)}")
    
    # Use real-time API pricing for validation phase
    run_orchestrator(
        input_file=config["input_file"],
        storage=storage,
        cost_tracker=cost_tracker,
        item_filter=lambda item: int(item["id"]) in sample_ids,
        use_batch=False,
    )
    
    print(f"\nValidation complete. Total cost: ${cost_tracker.total_cost:.2f}")
    print(f"Results: {output_dir}")
    print("\nRun analyze_results.py to compute metrics.")


if __name__ == "__main__":
    main()
```

## Module 8: `scripts/analyze_results.py`

```python
"""Compute validation metrics from manifest.jsonl."""

import json
import yaml
from pathlib import Path
from collections import Counter
import sys


def analyze(manifest_path: str, output_dir: str):
    """Compute and print Phase 1 validation metrics."""
    
    entries = []
    with open(manifest_path) as f:
        for line in f:
            entries.append(json.loads(line))
    
    total = len(entries)
    print(f"=== Validation Metrics ({total} items) ===\n")
    
    # Agreement breakdown
    agreement_counts = Counter(e["agreement_type"] for e in entries)
    print("Agreement:")
    for t in ["3/3", "2/3", "1/3", "0/3"]:
        n = agreement_counts[t]
        print(f"  {t}: {n}/{total} ({100*n/total:.1f}%)")
    
    # Format compliance per teacher (load from per-item metadata)
    print("\nFormat compliance (extracted ≠ ''):")
    teachers = ["sonnet", "gpt5_4", "kimi"]
    for t in teachers:
        n_valid = sum(1 for e in entries if e[f"{t}_answer"])
        print(f"  {t}: {n_valid}/{total} ({100*n_valid/total:.1f}%)")
    
    # Multi-answer count compliance
    multi_entries = [e for e in entries if e["question_type"] == "multi_free"]
    print(f"\nMulti-answer items: {len(multi_entries)}")
    # NOTE: Count accuracy needs the gold answer's expected count.
    # For each multi item, count commas in extracted answer + 1, compare to expected.
    
    # Token usage stats (load from per-item metadata)
    output_dir_p = Path(output_dir)
    token_stats = {t: [] for t in teachers}
    cap_hits = {t: 0 for t in teachers}
    for e in entries:
        item_dir = output_dir_p / f"item_{int(e['id']):04d}"
        for t in teachers:
            meta_path = item_dir / f"{t}_metadata.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                token_stats[t].append(meta["output_tokens"])
                if meta["hit_token_cap"]:
                    cap_hits[t] += 1
    
    print("\nOutput token stats:")
    for t in teachers:
        vals = sorted(token_stats[t])
        if not vals:
            continue
        median = vals[len(vals)//2]
        p95 = vals[int(len(vals)*0.95)] if len(vals) >= 20 else vals[-1]
        print(f"  {t}: median={median} p95={p95} cap_hits={cap_hits[t]}/{len(vals)}")
    
    # Decision gates
    print("\n=== Decision Gates (per DATAAPP_PROMPT_STRATEGY_LOCKED.md) ===")
    
    # Format ≥95%
    for t in teachers:
        n_valid = sum(1 for e in entries if e[f"{t}_answer"])
        passed = n_valid / total >= 0.95
        print(f"  {t} format ≥95%: {'✓' if passed else '✗'} ({100*n_valid/total:.1f}%)")
    
    # 3/3 agreement ≥40%
    n_full = agreement_counts["3/3"]
    passed = n_full / total >= 0.40
    print(f"  3/3 agreement ≥40%: {'✓' if passed else '✗'} ({100*n_full/total:.1f}%)")
    
    # Median tokens 3k-8k
    for t in teachers:
        vals = sorted(token_stats[t])
        if vals:
            median = vals[len(vals)//2]
            passed = 3000 <= median <= 8000
            print(f"  {t} median tokens 3k-8k: {'✓' if passed else '✗'} ({median})")


def main():
    config = yaml.safe_load(open("config.yaml"))
    analyze("dataapp_outputs/validation/manifest.jsonl", "dataapp_outputs/validation")


if __name__ == "__main__":
    main()
```

## Module 9: `scripts/run_full_batch.py`

**For Phase 2 (943-item run via Batch API).** Note: Anthropic and OpenAI batch APIs are async — you submit a batch, wait up to 24h, then retrieve results. Implementation is more complex than real-time.

For v0 simplicity, build Phase 2 using the same real-time orchestrator as validation, but ALL 943 items. Batch API is an optimization that can be added after v0 works.

```python
"""Phase 2: Full 943-item run.

For v0: uses real-time API (same as validation). Cost is ~$160 at real-time pricing.
TODO: implement batch API path to halve cost to ~$80.
"""

import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.storage import Storage
from src.cost_tracker import CostTracker
from src.orchestrator import run_orchestrator


def main():
    config = yaml.safe_load(open("config.yaml"))
    
    storage = Storage(config["output_dir"], config["manifest_file"])
    cost_tracker = CostTracker(config["cost_log"], config["cost_alert_thresholds"])
    
    print(f"Starting full run. Current cost: ${cost_tracker.total_cost:.2f}")
    print("Press Ctrl+C to stop; resume picks up where it left off.")
    
    run_orchestrator(
        input_file=config["input_file"],
        storage=storage,
        cost_tracker=cost_tracker,
        item_filter=None,  # all items
        use_batch=False,   # real-time for v0
    )
    
    print(f"\nFull run complete. Total cost: ${cost_tracker.total_cost:.2f}")


if __name__ == "__main__":
    main()
```

## Build Order

1. **Setup**: directory structure, `.env`, `.gitignore`, `requirements.txt`, `config.yaml`
2. **Port extraction** (`src/extraction.py`) — copy from competition repo
3. **Test extraction** (`tests/test_extraction.py`) on Run 09 data — must match 100%
4. **Build prompts** (`src/prompts.py`)
5. **Build API clients** (`src/api_clients.py`) — test each with a "hello" call
6. **Build cost tracker, storage** (`src/cost_tracker.py`, `src/storage.py`)
7. **Build orchestrator** (`src/orchestrator.py`)
8. **Build validation script** (`scripts/run_validation.py`)
9. **Build analysis script** (`scripts/analyze_results.py`)
10. **Run Phase 1 validation** (45 items, ~$10-15)
11. **Show Rain the metrics**
12. **If Rain approves**: run `scripts/run_full_batch.py` for Phase 2

## Critical Don'ts

- DO NOT commit `.env`
- DO NOT cross into competition repo (`/home/dvaneetv/private/151B_SP26_Competition/`)
- DO NOT skip atomic writes (corruption mid-run = lost data = lost money)
- DO NOT modify the locked prompt strategy
- DO NOT change `max_tokens=16384` or `temperature=0.6`
- DO NOT add features beyond v0 MVP
- **DO NOT build any UI** — no web app, no dashboard, no progress visualization. CLI + logs only.
- **DO NOT add dependencies** beyond requirements.txt without asking Rain
- **DO NOT introduce async/await** unless explicitly required (batch API is the only justified case, and that's v1+)
- **DO NOT write abstract base classes, factory patterns, or framework-style code.** Plain functions and simple classes only.

## When to Ask Rain

- Before Phase 2 (full run) — wait for explicit approval after Phase 1 metrics
- If extraction port doesn't match competition repo 100% on test data
- If cost crosses $50 unexpectedly
- If any API returns >10% errors

## Status Reports

After each milestone, report:
- What you built
- What you tested
- What's not tested yet
- Next step

Be concise. No long preambles.