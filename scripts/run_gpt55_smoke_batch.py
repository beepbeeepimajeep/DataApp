#!/usr/bin/env python3
"""
GPT-5.5 (xhigh reasoning) smoke test on Phase 1 validation set (45 items).
Uses Batch API for cost efficiency and faster turnaround.
"""

import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prompts import build_messages, detect_question_type
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def main():
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    # Load validation items from manifest
    manifest_path = Path(__file__).parent.parent / "dataapp_outputs" / "dataset_manifest.jsonl"
    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        sys.exit(1)

    items_to_test = []
    with open(manifest_path) as f:
        for line in f:
            if line.strip():
                items_to_test.append(json.loads(line.strip()))
                if len(items_to_test) >= 45:  # 45 items total
                    break

    print(f"📋 Loaded {len(items_to_test)} items for batch test")

    # Load raw data
    data_path = Path(__file__).parent.parent / "private.jsonl"
    raw_items = {}
    with open(data_path) as f:
        for i, line in enumerate(f):
            raw_items[i] = json.loads(line.strip())

    # Build batch request file
    batch_requests = []
    for item_data in items_to_test:
        item_id = item_data["id"]
        raw_item = raw_items.get(item_id, {})

        question = raw_item.get("question", "")
        options = raw_item.get("options")
        question_type = detect_question_type(raw_item)

        messages = build_messages(question, question_type, options)

        # Convert to OpenAI API format
        batch_requests.append({
            "custom_id": f"item_{item_id:04d}",
            "params": {
                "model": "gpt-5.5",
                "messages": messages,
                "temperature": 1.0,  # Required for reasoning
                "max_completion_tokens": 65536,
                "reasoning_effort": "xhigh",
            }
        })

    print(f"📤 Created {len(batch_requests)} batch requests")

    # Write batch file
    batch_file_path = Path(__file__).parent.parent / "dataapp_outputs" / "gpt55_smoke_batch_requests.jsonl"
    batch_file_path.parent.mkdir(exist_ok=True)

    with open(batch_file_path, "w") as f:
        for req in batch_requests:
            f.write(json.dumps({
                "custom_id": req["custom_id"],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": req["params"]
            }) + "\n")

    print(f"✓ Batch file written: {batch_file_path}")

    # Upload batch file
    print("\n📡 Uploading batch file to OpenAI...")
    with open(batch_file_path, "rb") as f:
        batch_file = client.files.create(
            file=f,
            purpose="batch"
        )

    print(f"✓ File uploaded: {batch_file.id}")

    # Submit batch
    print("\n🚀 Submitting batch job...")
    batch = client.beta.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        timeout_hours=24,
    )

    print(f"✓ Batch submitted: {batch.id}")
    print(f"  Status: {batch.status}")
    print(f"  Created: {batch.created_at}")

    # Save batch info
    batch_info_path = Path(__file__).parent.parent / "dataapp_outputs" / "gpt55_smoke_batch_info.json"
    with open(batch_info_path, "w") as f:
        json.dump({
            "batch_id": batch.id,
            "file_id": batch_file.id,
            "items_count": len(batch_requests),
            "submitted_at": datetime.now().isoformat(),
            "status": batch.status,
            "request_counts": {
                "total": batch.request_counts.total if hasattr(batch, "request_counts") else len(batch_requests),
                "completed": batch.request_counts.completed if hasattr(batch, "request_counts") else 0,
                "failed": batch.request_counts.failed if hasattr(batch, "request_counts") else 0,
            }
        }, f, indent=2)

    print(f"\n✓ Batch info saved: {batch_info_path}")

    # Start polling for completion
    print("\n⏳ Polling for batch completion...")
    poll_count = 0
    max_polls = 120  # ~2 hours max with 60s interval
    poll_interval = 60

    while poll_count < max_polls:
        poll_count += 1
        batch = client.beta.batches.retrieve(batch.id)

        print(f"  [{poll_count}] Status: {batch.status} | Completed: {batch.request_counts.completed}/{batch.request_counts.total}")

        if batch.status == "completed":
            print(f"\n✓ Batch completed!")
            break
        elif batch.status == "failed":
            print(f"\n❌ Batch failed!")
            print(f"  Failed requests: {batch.request_counts.failed}")
            sys.exit(1)
        elif batch.status == "expired":
            print(f"\n❌ Batch expired!")
            sys.exit(1)

        if poll_count < max_polls:
            time.sleep(poll_interval)

    if poll_count >= max_polls:
        print(f"\n⚠️  Polling timeout after {max_polls} attempts")
        print(f"  Current status: {batch.status}")
        print(f"  Check batch status later with: batch_id={batch.id}")
        sys.exit(1)

    # Download results
    print("\n📥 Downloading batch results...")
    output_file = client.beta.files.content(batch.output_file_id)
    output_path = Path(__file__).parent.parent / "dataapp_outputs" / "gpt55_smoke_batch_results.jsonl"

    with open(output_path, "wb") as f:
        f.write(output_file.read())

    print(f"✓ Results saved: {output_path}")

    # Parse and analyze results
    print("\n📊 Analyzing results...")
    results = []
    errors = []
    total_tokens = 0
    reasoning_tokens = 0
    total_cost = 0

    with open(output_path) as f:
        for line in f:
            result = json.loads(line.strip())
            custom_id = result.get("custom_id", "")
            item_id = int(custom_id.split("_")[1]) if "_" in custom_id else None

            if "error" in result:
                errors.append({
                    "item_id": item_id,
                    "error": result["error"].get("message", "Unknown error")
                })
                print(f"  ❌ Item {item_id}: {result['error'].get('message', 'Unknown error')}")
            elif "result" in result and "message" in result["result"]:
                resp = result["result"]
                message = resp["message"]

                # Calculate tokens and cost
                usage = result.get("usage", {})
                inp = usage.get("prompt_tokens", 0)
                out = usage.get("completion_tokens", 0)
                reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)

                total_tokens += inp + out
                reasoning_tokens += reasoning

                # Cost: input $0.0015/1K, output reasoning $0.006/1K, output text $0.002/1K
                # Assume all output is reasoning for max estimate
                inp_cost = inp * 0.0015 / 1000
                out_cost = out * 0.006 / 1000
                item_cost = inp_cost + out_cost
                total_cost += item_cost

                results.append({
                    "item_id": item_id,
                    "tokens": inp + out,
                    "reasoning_tokens": reasoning,
                    "cost": item_cost,
                })
                print(f"  ✓ Item {item_id}: {inp + out} tokens (reasoning: {reasoning}), cost: ${item_cost:.4f}")
            else:
                errors.append({
                    "item_id": item_id,
                    "error": "Unexpected response format"
                })
                print(f"  ❌ Item {item_id}: Unexpected response format")

    print("\n" + "=" * 80)
    print(f"Results Summary:")
    print(f"  ✓ Successful: {len(results)}/45")
    print(f"  ❌ Failed: {len(errors)}/45")
    print(f"  Total tokens used: {total_tokens:,}")
    print(f"  Reasoning tokens: {reasoning_tokens:,} ({100*reasoning_tokens/total_tokens:.1f}% of output)")
    print(f"  Total estimated cost: ${total_cost:.2f}")
    print(f"  Cost per successful item: ${total_cost/len(results):.4f}" if results else "  Cost per item: N/A")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors:
            print(f"  - Item {err['item_id']}: {err['error']}")

    # Save summary
    summary_path = Path(__file__).parent.parent / "dataapp_outputs" / "gpt55_smoke_batch_summary.json"
    with open(summary_path, "w") as f:
        json.dump({
            "batch_id": batch.id,
            "total_items": 45,
            "successful": len(results),
            "failed": len(errors),
            "total_tokens": total_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_cost": total_cost,
            "cost_per_item": total_cost / len(results) if results else 0,
            "completed_at": datetime.now().isoformat(),
        }, f, indent=2)

    print(f"\n✓ Summary saved: {summary_path}")
    print("=" * 80)

    # Exit status
    if len(errors) > 0:
        print(f"\n⚠️  {len(errors)} items failed. Check errors above.")
        sys.exit(1 if len(results) == 0 else 0)  # Exit 1 only if ALL failed


if __name__ == "__main__":
    main()
