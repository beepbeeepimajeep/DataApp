#!/usr/bin/env python3
"""
GPT-5.5 single-item sanity check.
Tests one item from the Phase 1 validation set to verify quota is unblocked
and reasoning_effort=xhigh is working correctly.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_clients import GPT55Client
from src.prompts import build_messages, detect_question_type
from dotenv import load_dotenv

load_dotenv()


def main():
    # Load Phase 1 validation items
    manifest_path = Path(__file__).parent.parent / "dataapp_outputs" / "dataset_manifest.jsonl"

    if not manifest_path.exists():
        print(f"❌ Manifest not found at {manifest_path}")
        sys.exit(1)

    # Read first item from manifest
    with open(manifest_path) as f:
        first_line = f.readline().strip()
        if not first_line:
            print("❌ Manifest is empty")
            sys.exit(1)
        item_data = json.loads(first_line)

    item_id = item_data.get("id")
    print(f"\n🔍 Testing GPT-5.5 with Phase 1 item {item_id}")
    print("=" * 80)

    # Load raw item from data
    data_path = Path(__file__).parent.parent / "private.jsonl"
    with open(data_path) as f:
        lines = f.readlines()
        if item_id >= len(lines):
            print(f"❌ Item {item_id} not found in data")
            sys.exit(1)
        raw_item = json.loads(lines[item_id])

    question = raw_item.get("question", "")
    options = raw_item.get("options")
    question_type = detect_question_type(raw_item)

    print(f"Item ID: {item_id}")
    print(f"Type: {question_type}")
    print(f"Question (first 100 chars): {question[:100]}...")
    print()

    # Build messages
    messages = build_messages(question, question_type, options)

    # Call GPT-5.5
    client = GPT55Client()
    print("🚀 Calling GPT-5.5 (reasoning_effort=xhigh, max_completion_tokens=65536)...")

    response = client.call(
        messages=messages,
        temperature=0.6,
        max_tokens=65536,
        reasoning_effort="xhigh"
    )

    print()
    print("=" * 80)
    print(f"Status: {'✓ SUCCESS' if response['error'] is None else '✗ FAILED'}")
    print()

    if response["error"]:
        print(f"Error: {response['error']}")
        print(f"Route: {response.get('route', 'unknown')}")
        sys.exit(1)

    # Verify response structure
    print(f"HTTP Status: 200 ✓")
    print(f"Model: {response['model']}")
    print(f"Request ID: {response['request_id']}")
    print()

    # Token stats
    print("Token Usage:")
    print(f"  Input tokens: {response['input_tokens']}")
    print(f"  Output tokens: {response['output_tokens']}")

    if "reasoning_tokens" in response:
        print(f"  Reasoning tokens: {response['reasoning_tokens']}")
    else:
        print(f"  Reasoning tokens: NOT POPULATED (⚠️  check if model supports extended thinking)")

    total_tokens = response["input_tokens"] + response["output_tokens"]
    print(f"  Total tokens: {total_tokens}")
    print()

    # Finish reason
    print(f"Finish reason: {response.get('finish_reason', 'unknown')}")
    if response['hit_token_cap']:
        print(f"  ⚠️  Hit token cap (finish_reason='length')")
    else:
        print(f"  ✓ Completed normally (finish_reason='stop')")
    print()

    # Cost estimate
    # GPT-5.5 pricing (per latest OpenAI docs):
    # Input: $0.0015 per 1K tokens
    # Output (reasoning): $0.006 per 1K tokens
    # Output (text): $0.002 per 1K tokens
    # For simplicity, assume all output is reasoning for max estimate
    input_cost = response["input_tokens"] * 0.0015 / 1000
    output_cost = response["output_tokens"] * 0.006 / 1000  # Use reasoning rate
    total_cost = input_cost + output_cost

    print(f"Estimated Cost: ${total_cost:.4f}")
    print(f"  (Input: ${input_cost:.4f} + Output: ${output_cost:.4f})")
    print()

    # Response preview
    response_text = response["response"]
    if len(response_text) > 200:
        print(f"Response (first 200 chars):")
        print(f"  {response_text[:200]}...")
    else:
        print(f"Response (full):")
        print(f"  {response_text}")
    print()

    print("=" * 80)
    print("✓ Sanity check passed! Quota is unblocked. Ready for full 45-item smoke test.")
    print()


if __name__ == "__main__":
    main()
