"""
OpenClaw Lite Cost Tracker

Tracks API costs for OpenAI and Claude.
"""

from datetime import datetime, timezone
from typing import Any


# Pricing per 1M tokens (as of 2024)
PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
}


class CostTracker:
    """Tracks API usage costs."""

    def __init__(self, monthly_budget_usd: float = 50.0):
        self.monthly_budget = monthly_budget_usd
        self._current_month = self._get_month()

        # Monthly counters
        self._monthly_costs = {"openai": 0.0, "claude": 0.0}
        self._monthly_tokens = {"openai": {"input": 0, "output": 0}, "claude": {"input": 0, "output": 0}}

        # Total counters
        self._total_requests = 0

    @staticmethod
    def _get_month() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m")

    def _check_month_rollover(self) -> None:
        current = self._get_month()
        if current != self._current_month:
            self._current_month = current
            self._monthly_costs = {"openai": 0.0, "claude": 0.0}
            self._monthly_tokens = {"openai": {"input": 0, "output": 0}, "claude": {"input": 0, "output": 0}}

    def track(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> dict[str, Any]:
        """Track usage and calculate cost."""
        self._check_month_rollover()

        # Get pricing
        pricing = PRICING.get(model, {"input": 1.0, "output": 1.0})
        cost = (input_tokens / 1_000_000) * pricing["input"] + \
               (output_tokens / 1_000_000) * pricing["output"]

        # Update counters
        self._monthly_costs[provider] += cost
        self._monthly_tokens[provider]["input"] += input_tokens
        self._monthly_tokens[provider]["output"] += output_tokens
        self._total_requests += 1

        total_cost = self._monthly_costs["openai"] + self._monthly_costs["claude"]

        return {
            "cost_usd": round(cost, 6),
            "monthly_total_usd": round(total_cost, 4),
            "budget_remaining_usd": round(self.monthly_budget - total_cost, 4),
            "budget_utilization_pct": round(total_cost / self.monthly_budget * 100, 2),
        }

    def is_budget_exceeded(self) -> bool:
        self._check_month_rollover()
        total = self._monthly_costs["openai"] + self._monthly_costs["claude"]
        return total >= self.monthly_budget

    def get_stats(self) -> dict[str, Any]:
        self._check_month_rollover()
        total_cost = self._monthly_costs["openai"] + self._monthly_costs["claude"]

        return {
            "month": self._current_month,
            "monthly_budget_usd": self.monthly_budget,
            "total_cost_usd": round(total_cost, 4),
            "budget_remaining_usd": round(self.monthly_budget - total_cost, 4),
            "budget_utilization_pct": round(total_cost / self.monthly_budget * 100, 2),
            "by_provider": {
                "openai": {
                    "cost_usd": round(self._monthly_costs["openai"], 4),
                    "input_tokens": self._monthly_tokens["openai"]["input"],
                    "output_tokens": self._monthly_tokens["openai"]["output"],
                },
                "claude": {
                    "cost_usd": round(self._monthly_costs["claude"], 4),
                    "input_tokens": self._monthly_tokens["claude"]["input"],
                    "output_tokens": self._monthly_tokens["claude"]["output"],
                },
            },
            "total_requests": self._total_requests,
        }
