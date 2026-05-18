"""
Cost tracking for API calls (tokens and USD).
"""

from typing import Optional
import json


class CostTracker:
    """Track tokens and cost across API calls."""

    def __init__(self):
        """Initialize cost tracker."""
        self.calls = []  # List of (vendor, input_tokens, output_tokens, cost_usd)

    def add_call(
        self,
        vendor: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        """
        Log an API call.

        Args:
            vendor: "anthropic", "openai", or "moonshot"
            input_tokens: Input token count.
            output_tokens: Output token count.
            cost_usd: Cost in USD.
        """
        self.calls.append(
            {
                "vendor": vendor,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
            }
        )

    def total_cost(self) -> float:
        """Return total cost in USD."""
        return sum(c["cost_usd"] for c in self.calls)

    def total_input_tokens(self) -> int:
        """Return total input tokens."""
        return sum(c["input_tokens"] for c in self.calls)

    def total_output_tokens(self) -> int:
        """Return total output tokens."""
        return sum(c["output_tokens"] for c in self.calls)

    def cost_by_vendor(self) -> dict[str, float]:
        """Return cost breakdown by vendor."""
        breakdown = {}
        for call in self.calls:
            vendor = call["vendor"]
            breakdown[vendor] = breakdown.get(vendor, 0) + call["cost_usd"]
        return breakdown

    def summary(self) -> dict:
        """Return cost summary."""
        return {
            "total_cost_usd": self.total_cost(),
            "total_input_tokens": self.total_input_tokens(),
            "total_output_tokens": self.total_output_tokens(),
            "cost_by_vendor": self.cost_by_vendor(),
            "num_calls": len(self.calls),
        }

    def __str__(self) -> str:
        """Pretty print summary."""
        s = self.summary()
        return (
            f"Cost: ${s['total_cost_usd']:.2f} | "
            f"Tokens: {s['total_input_tokens']} in, "
            f"{s['total_output_tokens']} out | "
            f"Calls: {s['num_calls']}"
        )
