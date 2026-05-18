"""
Cost tracking with file persistence and threshold alerts.
Logs each API call to cost_log.jsonl and alerts at predefined thresholds.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

# Pricing per million tokens (real-time, not batch)
# GPT-5.4 pricing is same for both TritonAI and OpenAI routes
PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "gpt-5.4": {"input": 2.50, "output": 15.00},
    "api-gpt-oss-120b": {"input": 0.0, "output": 0.0},  # free tier on TritonAI
}


class CostTracker:
    """Track API costs with file logging and threshold alerts."""

    def __init__(self, log_path: str, alert_thresholds: list[float]):
        """
        Initialize cost tracker.

        Args:
            log_path: Path to write cost_log.jsonl
            alert_thresholds: List of USD thresholds to alert at (e.g., [25, 50, 75, 100])
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.alert_thresholds = sorted(alert_thresholds)
        self.total_cost = 0.0
        self.alerted = set()

        self._load_existing()

    def _load_existing(self) -> None:
        """Load cost from existing log file (for resume)."""
        if self.log_path.exists():
            try:
                with open(self.log_path) as f:
                    for line in f:
                        entry = json.loads(line)
                        self.total_cost += entry.get("cost_usd", 0)
                        # Mark thresholds we've already alerted for
                        for t in self.alert_thresholds:
                            if self.total_cost >= t:
                                self.alerted.add(t)
            except Exception as e:
                print(f"Warning: could not load existing cost log: {e}")

    def record(self, item_id: str, model: str, input_tokens: int, output_tokens: int, route: str = None) -> float:
        """
        Record an API call and return its cost.

        Args:
            item_id: Item ID for tracking
            model: Model name (must be in PRICING dict)
            input_tokens: Input token count
            output_tokens: Output token count
            route: Optional route info ("tritonai" or "openai-fallback") for debugging

        Returns:
            Cost in USD for this call
        """
        if model not in PRICING:
            print(f"WARNING: Unknown model {model}, skipping cost")
            return 0.0

        p = PRICING[model]
        cost = (input_tokens * p["input"] / 1_000_000) + (
            output_tokens * p["output"] / 1_000_000
        )
        self.total_cost += cost

        # Write to log
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "item_id": item_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "running_total_usd": self.total_cost,
        }
        if route:
            entry["route"] = route
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Check thresholds
        for t in self.alert_thresholds:
            if self.total_cost >= t and t not in self.alerted:
                print(f"\n*** COST ALERT: total spend has crossed ${t} (currently ${self.total_cost:.2f}) ***\n")
                self.alerted.add(t)

        return cost

    def total_cost_usd(self) -> float:
        """Return total cost in USD."""
        return self.total_cost

    def summary(self) -> dict:
        """Return cost summary."""
        return {
            "total_cost_usd": self.total_cost,
        }
