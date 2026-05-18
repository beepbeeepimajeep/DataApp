# DataApp v0: 3-Teacher Agent Implementation Plan

**Status:** Pre-implementation  
**Date:** 2026-05-18  
**Budget:** TritonAI $20 + OpenAI $15 + Anthropic $19 ≈ $54 total

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DataApp Orchestrator                  │
│                    (run_item() loop)                     │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ GPT54Client  │ │ GPTOSSClient │ │SonnetClient  │
    │              │ │              │ │              │
    │TritonAI pri→ │ │TritonAI free │ │ Anthropic    │
    │OpenAI fallb  │ │ (no fallback) │ │ (no fallback)│
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
    ┌──────▼────────────────▼────────────────▼──────┐
    │          CostTracker (unified logging)        │
    │     (TritonAI $, OpenAI $, Anthropic $)      │
    └─────────────────────────────────────────────┘
```

---

## Implementation Plan (7 files modified)

### 1. `.env` — API Keys (ALREADY DONE ✓)
```
TRITONAI_API_KEY=<Rain provides>
OPENAI_API_KEY=<Rain provides>
ANTHROPIC_API_KEY=<Rain provides>
```

---

### 2. `config.yaml` — Update Model Config

**BEFORE:**
```yaml
models:
  sonnet: ...
  gpt5_4: ...
  kimi: ...
```

**AFTER:**
```yaml
models:
  gpt5_4:
    provider: tritonai-primary
    tritonai_base_url: https://tritonai-api.ucsd.edu/v1
    tritonai_model: gpt-5.4  # CONFIRM exact ID with Rain
    openai_fallback_model: gpt-5.4
    temperature: 0.6
    max_tokens: 16384
    top_p: 0.95
    fallback_trigger: 402  # Credit exhaustion
    
  gpt_oss:
    provider: tritonai-free
    tritonai_base_url: https://tritonai-api.ucsd.edu/v1
    tritonai_model: gpt-oss-120b  # CONFIRM exact ID with Rain
    temperature: 0.6
    max_tokens: 16384
    top_p: 0.95
    no_fallback: true  # Skip item if TritonAI down
    
  sonnet:
    provider: anthropic
    model: claude-sonnet-4-6
    temperature: 0.6
    max_tokens: 16384
    top_p: 0.95
    batch_api_phase2: true  # Use Anthropic Batch for Phase 2
```

---

### 3. `src/api_clients.py` — Implement 3 Clients

#### Client 1: GPT54Client (TritonAI primary + OpenAI fallback)

```python
class GPT54Client:
    """GPT-5.4: TritonAI primary, OpenAI fallback on 402 credit exhaustion."""
    
    def __init__(self, tritonai_model="gpt-5.4", openai_model="gpt-5.4"):
        self.tritonai_model = tritonai_model
        self.openai_model = openai_model
        self.tritonai_client = OpenAI(
            base_url="https://tritonai-api.ucsd.edu/v1",
            api_key=os.environ["TRITONAI_API_KEY"]
        )
        self.openai_client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"]
        )
        self.model = tritonai_model  # For logging
        self.route_used = "tritonai"  # Track which route
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def call(self, messages: list[dict], temperature: float, max_tokens: int) -> dict:
        """Try TritonAI first. On 402, fallback to OpenAI."""
        start = time.time()
        
        # Try TritonAI
        try:
            resp = self.tritonai_client.chat.completions.create(
                model=self.tritonai_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            self.route_used = "tritonai"
            return {
                "response": resp.choices[0].message.content or "",
                "input_tokens": resp.usage.prompt_tokens,
                "output_tokens": resp.usage.completion_tokens,
                "hit_token_cap": resp.choices[0].finish_reason == "length",
                "generation_time_s": time.time() - start,
                "model": self.tritonai_model,
                "request_id": resp.id,
                "error": None,
                "route": "tritonai",
            }
        
        except Exception as e:
            # Check if 402 (credit exhaustion)
            if "402" in str(e) or "credit" in str(e).lower():
                logger.warning(f"TritonAI 402 credit exhaustion, falling back to OpenAI")
                # Fall back to OpenAI
                try:
                    resp = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=messages,
                        temperature=temperature,
                        max_completion_tokens=max_tokens,
                    )
                    self.route_used = "openai"
                    return {
                        "response": resp.choices[0].message.content or "",
                        "input_tokens": resp.usage.prompt_tokens,
                        "output_tokens": resp.usage.completion_tokens,
                        "hit_token_cap": resp.choices[0].finish_reason == "length",
                        "generation_time_s": time.time() - start,
                        "model": self.openai_model,
                        "request_id": resp.id,
                        "error": None,
                        "route": "openai-fallback",
                    }
                except Exception as e2:
                    return _error_response(str(e2), self.openai_model, time.time() - start)
            else:
                return _error_response(str(e), self.tritonai_model, time.time() - start)
```

#### Client 2: GPTOSSClient (TritonAI free, no fallback)

```python
class GPTOSSClient:
    """GPT-OSS-120B: TritonAI free tier only. Skip item if TritonAI down."""
    
    def __init__(self, model="gpt-oss-120b"):
        self.model = model
        self.client = OpenAI(
            base_url="https://tritonai-api.ucsd.edu/v1",
            api_key=os.environ["TRITONAI_API_KEY"]
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def call(self, messages: list[dict], temperature: float, max_tokens: int) -> dict:
        """Call GPT-OSS-120B on TritonAI free tier."""
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
                "route": "tritonai",
            }
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start)
```

#### Client 3: SonnetClient (unchanged, already exists ✓)

---

### 4. `src/orchestrator.py` — Update Teacher Initialization

**BEFORE:**
```python
self.sonnet = SonnetClient(model="claude-sonnet-4-6")
self.gpt5_4 = GPTClient(model="gpt-5.4")
self.kimi = KimiClient(model="moonshotai/Kimi-K2.6")
self.clients = {"sonnet": self.sonnet, "gpt5_4": self.gpt5_4, "kimi": self.kimi}
```

**AFTER:**
```python
from src.api_clients import SonnetClient, GPT54Client, GPTOSSClient

# Initialize new 3-teacher lineup
self.gpt5_4 = GPT54Client(
    tritonai_model=config["models"]["gpt5_4"]["tritonai_model"],
    openai_model=config["models"]["gpt5_4"]["openai_fallback_model"]
)
self.gpt_oss = GPTOSSClient(
    model=config["models"]["gpt_oss"]["tritonai_model"]
)
self.sonnet = SonnetClient(model="claude-sonnet-4-6")

# Update teacher list
self.clients = {"gpt5_4": self.gpt5_4, "gpt_oss": self.gpt_oss, "sonnet": self.sonnet}
self.teacher_keys = ["gpt5_4", "gpt_oss", "sonnet"]
```

**Update run_item() futures:**
```python
futures = {
    executor.submit(self.gpt5_4.call, messages, 0.6, max_tokens): "gpt5_4",
    executor.submit(self.gpt_oss.call, messages, 0.6, max_tokens): "gpt_oss",
    executor.submit(self.sonnet.call, messages, 0.6, max_tokens): "sonnet",
}
```

**Update consensus loop:**
```python
for teacher in ["gpt5_4", "gpt_oss", "sonnet"]:  # Was ["sonnet", "gpt5_4", "kimi"]
    r = results[teacher]
    ...
```

**Update manifest entry:**
```python
manifest_entry = {
    "id": item_id,
    "question_type": question_type,
    "gpt5_4_answer": extractions.get("gpt5_4", ""),
    "gpt_oss_answer": extractions.get("gpt_oss", ""),  # Was kimi_answer
    "sonnet_answer": extractions.get("sonnet", ""),
    "agreement_type": consensus["type"],
    "which_agreed": consensus["which_agreed"],
    "consensus_answer": consensus["answer"],
    "any_errors": any(results[t].get("error") for t in ["gpt5_4", "gpt_oss", "sonnet"]),
    "reasoning_present": {
        "gpt5_4": has_reasoning(results["gpt5_4"].get("response", "")),
        "gpt_oss": has_reasoning(results["gpt_oss"].get("response", "")),
        "sonnet": has_reasoning(results["sonnet"].get("response", "")),
    },
    "gpt5_4_metadata": {...},
    "gpt_oss_metadata": {...},  # Was kimi_metadata
    "sonnet_metadata": {...},
    "route_gpt5_4": results["gpt5_4"].get("route", "tritonai"),  # Track TritonAI vs OpenAI
    "any_hit_cap": any(results[t].get("hit_token_cap", False) for t in [...]),
}
```

---

### 5. `src/cost_tracker.py` — Update Pricing

**BEFORE:**
```python
PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "gpt-5.4": {"input": 2.50, "output": 15.00},
    "kimi-k2.6": {"input": 0.60, "output": 2.50},
}
```

**AFTER:**
```python
PRICING = {
    # TritonAI pricing (per 1M tokens)
    "gpt-5.4-tritonai": {"input": 2.50, "output": 10.00},  # Estimate, Rain confirms
    "gpt-5.4-openai": {"input": 2.50, "output": 15.00},   # OpenAI fallback
    "gpt-oss-120b": {"input": 0.00, "output": 0.00},      # Free tier ($15/mo)
    
    # Anthropic
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
}
```

**Update record() to track route:**
```python
def record(self, item_id, model, input_tokens, output_tokens, route=None):
    """
    Args:
        route: "tritonai", "openai-fallback", or None (default)
    """
    # Determine pricing based on model + route
    if model == "gpt-5.4" and route == "openai-fallback":
        pricing = PRICING["gpt-5.4-openai"]
    elif model == "gpt-5.4":
        pricing = PRICING["gpt-5.4-tritonai"]
    else:
        pricing = PRICING.get(model, {"input": 0, "output": 0})
    
    cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "item_id": item_id,
        "model": model,
        "route": route,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
    }
    
    append_jsonl(entry, self.log_path)
    self.total_cost += cost
    
    # Alert thresholds
    for threshold in self.alert_thresholds:
        if threshold not in self.alerted and self.total_cost >= threshold:
            logger.warning(f"⚠️ Cost reached ${threshold:.0f}")
            self.alerted.add(threshold)
```

---

### 6. `src/storage.py` — Update Manifest Fields (Minor)

No changes to Storage class itself. Just update field names in orchestrator:
- `kimi_answer` → `gpt_oss_answer`
- `kimi_metadata` → `gpt_oss_metadata`
- Add `route_gpt5_4` tracking for fallback detection

---

### 7. `scripts/run_validation.py` — Update Validation Script

**Update teacher keys:**
```python
# OLD: ["sonnet", "gpt5_4", "kimi"]
# NEW:
TEACHERS = ["gpt5_4", "gpt_oss", "sonnet"]
```

**Update agreement checks:**
```python
manifest_entry = {
    ...
    "gpt5_4_answer": ...,
    "gpt_oss_answer": ...,  # Was kimi_answer
    "sonnet_answer": ...,
}

# In checks:
for teacher in TEACHERS:
    answer = entry[f"{teacher}_answer"]
```

**Update reasoning checks:**
```python
reasoning_present = entry.get("reasoning_present", {})
# Now has keys: gpt5_4, gpt_oss, sonnet
```

---

## Data Flow: Single Item Processing

```
Item 0:
  question = "What is 2+2?"
  type = "mcq"
  max_tokens = 2048

┌─ Parallel queries ─────────────────────┐
│                                        │
├─ GPT54Client.call()                   │
│   ├─ Try TritonAI (https://tritonai-api...)
│   │   ├─ Success → return (route=tritonai)
│   │   └─ 402 error → Fallback to OpenAI
│   │       └─ return (route=openai-fallback)
│   └─ Other error → return error_response
│
├─ GPTOSSClient.call()                  │
│   ├─ Try TritonAI (same endpoint)
│   │   └─ Success/error → return (no fallback)
│
├─ SonnetClient.call()                  │
│   └─ Try Anthropic API
│       └─ Success/error → return
│
└─ Wait for all 3 ────────────────────┘

Extract answers (3 per item):
  gpt5_4_answer = "4"
  gpt_oss_answer = "4"
  sonnet_answer = "4"

Compute consensus: 3/3 agreement → consensus="4"

Track costs:
  gpt5_4: 200 input + 150 output → $X (via TritonAI or OpenAI)
  gpt_oss: 200 input + 140 output → $0 (free tier)
  sonnet: 195 input + 120 output → $Y (Anthropic)

Manifest entry:
{
  "id": 0,
  "gpt5_4_answer": "4",
  "gpt_oss_answer": "4",
  "sonnet_answer": "4",
  "agreement_type": "3/3",
  "consensus_answer": "4",
  "route_gpt5_4": "tritonai",
  ...
}
```

---

## Testing Sequence

### Phase 0a: API Connectivity (before Phase 1)
```bash
python3 << 'EOF'
from src.api_clients import GPT54Client, GPTOSSClient, SonnetClient

# Test each client once
clients = [
    ("gpt5_4", GPT54Client()),
    ("gpt_oss", GPTOSSClient()),
    ("sonnet", SonnetClient()),
]

for name, client in clients:
    r = client.call([{"role": "user", "content": "hi"}], 0.6, 100)
    print(f"{name}: {r['route'] if 'route' in r else 'OK'}")
EOF
```

### Phase 0b: Single Item End-to-End
```bash
python3 << 'EOF'
from src.orchestrator import DataAppOrchestrator
import yaml

config = yaml.safe_load(open('config.yaml'))
orch = DataAppOrchestrator(config)
manifest = orch.run_item({"id": 0, "question": "2+2?", "options": ["3", "4", "5"]})
print(manifest)
EOF
```

### Phase 1: Full Validation (45 items)
```bash
python scripts/run_validation.py
# Check: all gates pass, cost ~$15 (mostly OpenAI fallback once TritonAI credits exhausted)
```

### Phase 2: Full Run (943 items)
```bash
python scripts/run_full.py
# Check: resume capability (skip already-done items)
```

---

## Rollout Steps (In Order)

1. **Update config.yaml** — Lock in model IDs (confirm with Rain)
2. **Implement api_clients.py** — GPT54Client + GPTOSSClient
3. **Update orchestrator.py** — Swap teacher lineup
4. **Update cost_tracker.py** — New pricing + route tracking
5. **Test connectivity** — Phase 0a
6. **Test single item** — Phase 0b
7. **Run Phase 1 validation** — 45 items
8. **Report metrics** — Format compliance, agreement rate, cost breakdown
9. **Await Rain approval** — Before Phase 2
10. **Run Phase 2 full** — 943 items (use Anthropic batch API for Sonnet)

---

## Known Unknowns (Confirm with Rain)

- [ ] Exact model ID for GPT-5.4 on TritonAI (gpt-5.4? gpt-54?)
- [ ] Exact model ID for GPT-OSS-120B (gpt-oss-120b? oss-120b?)
- [ ] TritonAI pricing (estimated $2.50/$10, confirm actual)
- [ ] Error code for credit exhaustion (402? specific message?)
- [ ] Anthropic batch API details (format, timing, integration)

---

## Budget Tracking

| Phase | Teacher | Cost | Notes |
|-------|---------|------|-------|
| 1 | GPT-5.4 (TritonAI) | ~$5 | 45 items × $0.11/item avg |
| 1 | GPT-OSS | $0 | Free tier |
| 1 | Sonnet | ~$1 | 45 items × $0.02/item avg |
| **1 Total** | | **~$6** | Well under $50 budget |
| 2 | GPT-5.4 (TritonAI→OpenAI) | ~$20 | TritonAI exhausted ~item 540, fallback thereafter |
| 2 | GPT-OSS | $0 | Free tier (entire run) |
| 2 | Sonnet (batch) | ~$10 | 50% off with batch API |
| **2 Total** | | **~$30** | |
| **Grand Total** | | **~$36** | Under $54 budget ✓ |

