#!/usr/bin/env python3
"""
Check actual OpenAI spend via Admin API.

Ground truth for cost reconciliation. Run before/after any billing-relevant operation.

Usage:
  python3 scripts/check_spend.py                    # Last 24h
  python3 scripts/check_spend.py --hours 12         # Last 12h
  python3 scripts/check_spend.py --start-date 2026-05-19
"""

import os
import sys
import requests
import time
import argparse
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_admin_key():
    """Load admin key from .env"""
    key = os.environ.get('OPENAI_ADMIN_KEY')
    if not key:
        print("ERROR: OPENAI_ADMIN_KEY not in environment")
        sys.exit(1)
    return key

def fetch_costs(admin_key, start_time, end_time=None):
    """Fetch costs grouped by line_item"""
    if end_time is None:
        end_time = int(time.time())

    resp = requests.get(
        "https://api.openai.com/v1/organization/costs",
        headers={"Authorization": f"Bearer {admin_key}"},
        params={
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": "1d",
            "limit": 100,
            "group_by": "line_item"
        }
    )

    if resp.status_code != 200:
        print(f"ERROR: Costs API returned {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    return resp.json()

def parse_costs(costs_data):
    """Extract model costs from API response"""
    model_costs = {}

    for bucket in costs_data.get('data', []):
        for result in bucket.get('results', []):
            line_item = result.get('line_item', '')
            amount = float(result.get('amount', {}).get('value', 0))
            quantity = result.get('quantity', 0)

            # Parse line_item: "gpt-5.5-2026-04-23, output"
            parts = line_item.split(', ')
            if len(parts) < 2:
                continue

            model_date = parts[0]
            cost_type = parts[1]  # "input", "output", "cached input"

            if model_date not in model_costs:
                model_costs[model_date] = {
                    'input': {'cost': 0, 'qty': 0},
                    'output': {'cost': 0, 'qty': 0},
                    'cached_input': {'cost': 0, 'qty': 0}
                }

            if cost_type == 'input':
                model_costs[model_date]['input']['cost'] += amount
                model_costs[model_date]['input']['qty'] += quantity
            elif cost_type == 'output':
                model_costs[model_date]['output']['cost'] += amount
                model_costs[model_date]['output']['qty'] += quantity
            elif cost_type == 'cached input':
                model_costs[model_date]['cached_input']['cost'] += amount
                model_costs[model_date]['cached_input']['qty'] += quantity

    return model_costs

def extract_model_name(model_date_str):
    """Extract model name from 'gpt-5.5-2026-04-23' format"""
    parts = model_date_str.split('-')
    # Handle both 'gpt-5.5' and 'gpt-5.4'
    if parts[0] == 'gpt':
        return f"{parts[0]}-{parts[1]}.{parts[2]}"
    return model_date_str

def main():
    parser = argparse.ArgumentParser(description="Check OpenAI spend via Admin API")
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default 24)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD), overrides --hours')
    args = parser.parse_args()

    admin_key = get_admin_key()

    if args.start_date:
        try:
            dt = datetime.strptime(args.start_date, '%Y-%m-%d')
            start_time = int(dt.timestamp())
        except ValueError:
            print(f"ERROR: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        start_time = int(time.time()) - (args.hours * 3600)

    end_time = int(time.time())

    # Fetch costs
    costs_data = fetch_costs(admin_key, start_time, end_time)
    model_costs = parse_costs(costs_data)

    # Display results
    print("\n" + "="*70)
    print("OPENAI SPEND REPORT (Admin API Ground Truth)")
    print("="*70)

    start_dt = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    end_dt = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nPeriod: {start_dt} to {end_dt}")

    total_cost = 0

    print("\nBY MODEL:\n")
    for model_date_str in sorted(model_costs.keys()):
        model_name = extract_model_name(model_date_str)
        costs = model_costs[model_date_str]

        input_cost = costs['input']['cost']
        output_cost = costs['output']['cost']
        cached_cost = costs['cached_input']['cost']
        model_total = input_cost + output_cost + cached_cost

        input_qty = costs['input']['qty']
        output_qty = costs['output']['qty']
        cached_qty = costs['cached_input']['qty']

        print(f"  {model_name}:")
        print(f"    Input:  ${input_cost:.4f} ({input_qty:,} tokens)")
        if output_qty > 0:
            print(f"    Output: ${output_cost:.4f} ({output_qty:,} tokens)")
        if cached_qty > 0:
            print(f"    Cached: ${cached_cost:.4f} ({cached_qty:,} tokens)")
        print(f"    Subtotal: ${model_total:.4f}")
        print()

        total_cost += model_total

    print("="*70)
    print(f"TOTAL: ${total_cost:.4f}")
    print("="*70 + "\n")

    return 0

if __name__ == '__main__':
    sys.exit(main())
