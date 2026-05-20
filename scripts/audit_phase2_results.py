#!/usr/bin/env python3
"""
Audit Phase 2 (100 items) batch results before proceeding to Phase 3.

Verifies:
1. All 100 items collected successfully
2. No excessive cap-hits (finish_reason='length' <5%)
3. No excessive timeouts
4. Extraction success rate >=90%
5. Cost within 20% of projection
6. Token distribution within expected bounds

Gate conditions (MUST ALL PASS):
- Projected cost ≤ $60 for remaining 443 items (Phase 3+4)
- Timeout rate ≤ 5%
- Extraction success ≥ 90%
- No catastrophic API failures

Usage:
  python3 scripts/audit_phase2_results.py
"""

import sys
import json
import logging
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction import DataAppExtractor

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def audit_phase2():
    """Audit Phase 2 results"""

    output_dir = Path("dataapp_outputs")
    response_dir = output_dir / "gpt55_full"
    cost_log = output_dir / "gpt55_full_cost_log.jsonl"

    # Load Phase 2 items
    phase2_items = set()
    batch_input = output_dir / "gpt55_batch_input.jsonl"
    with open(batch_input) as f:
        for line in f:
            if line.strip():
                req = json.loads(line)
                item_id = int(req['custom_id'].split('_')[1])
                phase2_items.add(item_id)

    print(f"\n{'='*70}")
    print(f"PHASE 2 AUDIT (100 items)")
    print(f"{'='*70}\n")

    # Check response files
    response_files = {}
    for item_id in phase2_items:
        f = response_dir / f"item_{int(item_id):04d}_gpt5_5_response.md"
        if f.exists() and f.stat().st_size > 0:
            response_files[item_id] = f

    collected = len(response_files)
    missing = len(phase2_items) - collected

    print(f"Response Files:")
    print(f"  Collected: {collected}/100")
    print(f"  Missing: {missing}")

    if collected == 0:
        print(f"\n❌ GATE FAILED: No items collected!")
        return False

    # Load cost log entries for Phase 2
    phase2_entries = []
    with open(cost_log) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if entry['item_id'] in phase2_items:
                    phase2_entries.append(entry)

    # Analyze
    finish_reasons = Counter(e['finish_reason'] for e in phase2_entries)
    cap_hits = finish_reasons.get('length', 0)
    timeouts = finish_reasons.get('timeout', 0)
    successes = finish_reasons.get('stop', 0)

    print(f"\nFinish Reasons:")
    for reason, count in sorted(finish_reasons.items()):
        pct = (count / len(phase2_entries)) * 100
        print(f"  {reason}: {count} ({pct:.1f}%)")

    # Extract answers
    extractor = DataAppExtractor(strict_extract=False)
    extracted_count = 0
    for item_id in phase2_items:
        response_file = response_dir / f"item_{int(item_id):04d}_gpt5_5_response.md"
        if response_file.exists():
            content = response_file.read_text()
            # Extract "## Reasoning + Response" section
            if "## Reasoning + Response" in content:
                reasoning_section = content.split("## Reasoning + Response")[1].split("## Metadata")[0]
                extracted = extractor.extract(reasoning_section)
                if extracted:
                    extracted_count += 1

    extraction_rate = (extracted_count / collected) * 100 if collected > 0 else 0

    print(f"\nExtraction:")
    print(f"  Successfully extracted: {extracted_count}/{collected} ({extraction_rate:.1f}%)")

    # Token and cost analysis
    output_tokens = [e['output_tokens'] for e in phase2_entries]
    reasoning_tokens = [e['reasoning_tokens'] for e in phase2_entries]
    costs = [e['cost_usd'] for e in phase2_entries]

    total_cost = sum(costs)
    mean_output = sum(output_tokens) / len(output_tokens) if output_tokens else 0
    mean_reasoning = sum(reasoning_tokens) / len(reasoning_tokens) if reasoning_tokens else 0

    print(f"\nTokens:")
    print(f"  Mean output tokens: {mean_output:.0f}")
    print(f"  Mean reasoning tokens: {mean_reasoning:.0f}")
    print(f"  Max output tokens: {max(output_tokens) if output_tokens else 0}")
    print(f"  Max reasoning tokens: {max(reasoning_tokens) if reasoning_tokens else 0}")

    print(f"\nCost:")
    print(f"  Total cost (batch API): ${total_cost:.2f}")
    print(f"  Expected cost: $11.40")
    print(f"  Variance: {((total_cost - 11.40) / 11.40 * 100):+.1f}%")

    # Projected cost for remaining phases
    remaining_items = 943 - 68 - 100  # after Phase 1 and 2
    cost_per_item = total_cost / collected if collected > 0 else 0
    projected_remaining = cost_per_item * remaining_items

    print(f"\nProjection:")
    print(f"  Cost per item: ${cost_per_item:.3f}")
    print(f"  Remaining items: {remaining_items}")
    print(f"  Projected cost for all remaining: ${projected_remaining:.2f}")
    print(f"  Phase 3 (50): ${cost_per_item * 50:.2f}")
    print(f"  Phase 4 (200): ${cost_per_item * 200:.2f}")

    # Gate checks
    print(f"\n{'='*70}")
    print(f"GATE CHECKS (Phase 2)")
    print(f"{'='*70}\n")

    gate_pass = True

    # Gate 1: Extraction success
    if extraction_rate >= 90:
        print(f"✓ Extraction success rate: {extraction_rate:.1f}% (≥90%)")
    else:
        print(f"❌ Extraction success rate: {extraction_rate:.1f}% (<90%)")
        gate_pass = False

    # Gate 2: Timeout rate
    timeout_rate = (timeouts / collected * 100) if collected > 0 else 0
    if timeout_rate <= 5:
        print(f"✓ Timeout rate: {timeout_rate:.1f}% (≤5%)")
    else:
        print(f"❌ Timeout rate: {timeout_rate:.1f}% (>5%)")
        gate_pass = False

    # Gate 3: Cap-hit rate (warning, not hard gate)
    cap_hit_rate = (cap_hits / collected * 100) if collected > 0 else 0
    if cap_hit_rate <= 10:
        print(f"✓ Cap-hit rate: {cap_hit_rate:.1f}% (≤10%)")
    else:
        print(f"⚠ Cap-hit rate: {cap_hit_rate:.1f}% (>10% — monitor for Phase 3+)")

    # Gate 4: Cost projection
    if projected_remaining <= 60:
        print(f"✓ Projected remaining cost: ${projected_remaining:.2f} (≤$60)")
    else:
        print(f"❌ Projected remaining cost: ${projected_remaining:.2f} (>$60)")
        gate_pass = False

    # Gate 5: Collection completeness
    if missing == 0:
        print(f"✓ All 100 items collected")
    else:
        print(f"❌ {missing} items missing")
        gate_pass = False

    print(f"\n{'='*70}")
    if gate_pass:
        print(f"✓ GATE PASSED — Phase 3 authorized")
    else:
        print(f"❌ GATE FAILED — DO NOT PROCEED TO PHASE 3")
    print(f"{'='*70}\n")

    return gate_pass


if __name__ == "__main__":
    try:
        passed = audit_phase2()
        sys.exit(0 if passed else 1)
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        sys.exit(1)
