#!/usr/bin/env python3
"""
Collect results from completed GPT-5.5 xhigh batch job.

Polls batch status, downloads results when complete, parses and saves
responses to dataapp_outputs/gpt55_full/ and updates cost log.

Usage:
  python3 scripts/batch_collect_gpt55_results.py <batch_id>
  python3 scripts/batch_collect_gpt55_results.py --batch-file /path/to/batch_info.json
"""

import sys
import json
import time
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml
from openai import OpenAI
from src.extraction import DataAppExtractor
from src.storage import append_jsonl, _atomic_write

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config():
    """Load config.yaml"""
    config_file = Path(__file__).parent.parent / "config.yaml"
    with open(config_file) as f:
        return yaml.safe_load(f)


def format_gpt55_response_md(response_data, prompt):
    """Format response as markdown"""
    finish_reason = response_data.get("finish_reason", "unknown")
    reasoning_tokens = response_data.get("reasoning_tokens", 0)
    error_note = f"\n\n**ERROR:** {response_data.get('error')}" if response_data.get("error") else ""

    return f"""# GPT-5.5 xhigh Response

## Prompt
```
{prompt}
```

## Reasoning + Response
{response_data.get('response', '')}

## Metadata
- Model: {response_data.get('model', 'gpt-5.5')}
- Input tokens: {response_data.get('input_tokens', 0)}
- Output tokens: {response_data.get('output_tokens', 0)}
- Reasoning tokens: {reasoning_tokens}
- Hit token cap: {response_data.get('hit_token_cap', False)}
- Finish reason: {finish_reason}
- Generation time: {response_data.get('generation_time_s', 0):.2f}s
- Request ID: {response_data.get('request_id', 'N/A')}{error_note}
- Via batch: True
"""


def poll_batch_status(client, batch_id, poll_interval=300):
    """Poll batch status until complete or failed"""
    logger.info(f"Polling batch {batch_id}...")

    while True:
        batch = client.batches.retrieve(batch_id)
        logger.info(f"Status: {batch.status}")

        if batch.status in ['completed', 'failed', 'expired']:
            return batch

        logger.info(f"Waiting {poll_interval}s before next poll...")
        time.sleep(poll_interval)


def process_batch_results(client, batch, output_dir):
    """Download and process batch results"""
    config = load_config()
    output_file_id = batch.output_file_id

    if not output_file_id:
        logger.warning("No output file in batch response")
        return 0, 0, 0.0

    logger.info(f"Downloading results from {output_file_id}...")

    # Download output file
    output_content = client.files.content(output_file_id).text
    lines = output_content.strip().split('\n')

    logger.info(f"Downloaded {len(lines)} result lines")

    response_dir = output_dir / "gpt55_full"
    response_dir.mkdir(exist_ok=True)

    cost_log_path = output_dir / "gpt55_full_cost_log.jsonl"

    collected = 0
    errors = 0
    total_cost = 0.0

    extractor = DataAppExtractor(strict_extract=False)

    for line in lines:
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            logger.warning(f"Skipping malformed line: {line[:100]}")
            errors += 1
            continue

        custom_id = result.get('custom_id', '')
        if not custom_id.startswith('item_'):
            logger.warning(f"Unknown custom_id: {custom_id}")
            errors += 1
            continue

        try:
            item_id = int(custom_id.split('_')[1])
        except (IndexError, ValueError):
            logger.warning(f"Could not parse item_id from {custom_id}")
            errors += 1
            continue

        # Check for error in result
        if 'error' in result:
            logger.warning(f"Item {item_id}: {result['error']}")
            errors += 1
            continue

        # Extract response
        response_body = result.get('response', {}).get('body', {})

        if response_body.get('error'):
            logger.warning(f"Item {item_id}: API error: {response_body['error']}")
            errors += 1
            continue

        # Parse response
        try:
            choice = response_body['choices'][0]
            content = choice['message']['content']
            finish_reason = choice['finish_reason']
            usage = response_body['usage']

            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            reasoning_tokens = 0

            # Extract reasoning tokens if available
            if 'completion_tokens_details' in usage:
                details = usage['completion_tokens_details']
                reasoning_tokens = details.get('reasoning_tokens', 0)

            request_id = response_body.get('id', '')

        except (KeyError, IndexError) as e:
            logger.warning(f"Item {item_id}: Failed to parse response: {e}")
            errors += 1
            continue

        # Calculate cost (with 2.5x multiplier)
        SDK_REASONING_MULTIPLIER = 2.5
        input_cost = (input_tokens / 1_000_000) * 5
        sdk_output_cost = ((output_tokens + reasoning_tokens) / 1_000_000) * 30
        estimated_output_cost = sdk_output_cost * SDK_REASONING_MULTIPLIER
        cost_usd = input_cost + estimated_output_cost

        # Save response file
        response_path = response_dir / f"item_{int(item_id):04d}_gpt5_5_response.md"
        response_data = {
            'response': content,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'reasoning_tokens': reasoning_tokens,
            'hit_token_cap': finish_reason == 'length',
            'finish_reason': finish_reason,
            'generation_time_s': 0,  # Not available in batch
            'model': 'gpt-5.5',
            'request_id': request_id,
            'error': None,
        }

        md_content = format_gpt55_response_md(response_data, "")
        _atomic_write(response_path, md_content)

        # Extract answer
        extracted = ""
        if content:
            extracted = extractor.extract(content)

        # Log cost
        cost_entry = {
            'item_id': item_id,
            'model': 'gpt-5.5',
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'reasoning_tokens': reasoning_tokens,
            'cost_usd': cost_usd,
            'wall_time_s': 0,  # Not available in batch
            'finish_reason': finish_reason,
            'error': None,
            'via_batch': True,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        append_jsonl(cost_entry, cost_log_path)

        collected += 1
        total_cost += cost_usd

        logger.info(f"Item {item_id}: finish={finish_reason}, tokens={output_tokens}, cost=${cost_usd:.4f}")

    return collected, errors, total_cost


def main():
    parser = argparse.ArgumentParser(description="Collect GPT-5.5 batch results")
    parser.add_argument('batch_id', nargs='?', help='Batch ID')
    parser.add_argument('--batch-file', type=str, help='Batch info JSON file')
    args = parser.parse_args()

    if args.batch_file:
        with open(args.batch_file) as f:
            batch_info = json.load(f)
        batch_id = batch_info['batch_id']
        logger.info(f"Loaded batch_id from {args.batch_file}: {batch_id}")
    elif args.batch_id:
        batch_id = args.batch_id
    else:
        logger.error("Must provide batch_id or --batch-file")
        return 1

    logger.info(f"=== GPT-5.5 xhigh Batch Collect ===")

    config = load_config()
    output_dir = Path(config["paths"]["output_dir"])

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    # Poll for completion
    batch = poll_batch_status(client, batch_id, poll_interval=300)

    logger.info(f"Batch final status: {batch.status}")

    if batch.status != 'completed':
        logger.error(f"Batch did not complete: {batch.status}")
        return 1

    # Process results
    collected, errors, total_cost = process_batch_results(client, batch, output_dir)

    print("\n" + "="*70)
    print("BATCH COLLECTION COMPLETE")
    print("="*70)
    print(f"Items collected: {collected}")
    print(f"Items errored: {errors}")
    print(f"Total estimated cost: ${total_cost:.2f}")
    print("="*70 + "\n")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    import os
    sys.exit(main())
