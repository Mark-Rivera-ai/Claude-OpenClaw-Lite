"""
OpenClaw Lite Query Router

Routes queries between OpenAI (simple) and Claude (complex).
"""

import logging
import re
from typing import Any

from .providers import OpenAIProvider, ClaudeProvider, ProviderResponse
from .cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """Simple complexity scoring for query routing."""

    COMPLEX_PATTERNS = [
        r"\banalyze\b", r"\bevaluate\b", r"\bstep[- ]by[- ]step\b",
        r"\bexplain\s+in\s+detail\b", r"\bcompare\b", r"\bcontrast\b",
        r"\bwhy\b", r"\bhow\s+does\b", r"\bimplement\b", r"\bdebug\b",
        r"```", r"\bcode\b", r"\bfunction\b", r"\bclass\b", r"\balgorithm\b",
    ]

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.COMPLEX_PATTERNS]

    def score(self, messages: list[dict[str, Any]]) -> float:
        """Score message complexity from 0.0 to 1.0."""
        text = " ".join(m.get("content", "") for m in messages)

        # Word count factor (longer = more complex)
        words = len(text.split())
        length_score = min(words / 200, 1.0) * 0.4

        # Pattern matching factor
        matches = sum(1 for p in self._patterns if p.search(text))
        pattern_score = min(matches / 5, 1.0) * 0.6

        return length_score + pattern_score

    def is_complex(self, messages: list[dict[str, Any]]) -> bool:
        return self.score(messages) >= self.threshold


class QueryRouter:
    """Routes queries to appropriate provider based on complexity."""

    def __init__(
        self,
        openai_provider: OpenAIProvider,
        claude_provider: ClaudeProvider,
        cost_tracker: CostTracker,
        complexity_threshold: float = 0.5,
    ):
        self.openai = openai_provider
        self.claude = claude_provider
        self.cost_tracker = cost_tracker
        self.analyzer = ComplexityAnalyzer(threshold=complexity_threshold)

        # Stats
        self.openai_count = 0
        self.claude_count = 0

    async def route(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        """Route query to appropriate provider."""

        is_complex = self.analyzer.is_complex(messages)

        # Determine primary and fallback providers
        if is_complex and self.claude.is_available():
            primary = self.claude
            fallback = self.openai if self.openai.is_available() else None
        elif self.openai.is_available():
            primary = self.openai
            fallback = self.claude if self.claude.is_available() else None
        elif self.claude.is_available():
            primary = self.claude
            fallback = None
        else:
            raise RuntimeError("No API providers available")

        # Generate response, falling back on provider errors
        try:
            response = await primary.generate(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if primary == self.claude:
                self.claude_count += 1
            else:
                self.openai_count += 1
        except Exception as e:
            if fallback is None:
                raise
            logger.warning(f"{primary.__class__.__name__} failed ({e}), falling back to {fallback.__class__.__name__}")
            response = await fallback.generate(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if fallback == self.claude:
                self.claude_count += 1
            else:
                self.openai_count += 1

        # Track costs
        self.cost_tracker.track(
            provider=response.provider,
            model=response.model,
            input_tokens=response.usage["prompt_tokens"],
            output_tokens=response.usage["completion_tokens"],
        )

        return response

    def get_stats(self) -> dict[str, Any]:
        """Get routing statistics."""
        total = self.openai_count + self.claude_count
        return {
            "total_requests": total,
            "openai_requests": self.openai_count,
            "claude_requests": self.claude_count,
            "openai_percentage": round(self.openai_count / total * 100, 2) if total else 0,
            "claude_percentage": round(self.claude_count / total * 100, 2) if total else 0,
            "cost": self.cost_tracker.get_stats(),
        }
