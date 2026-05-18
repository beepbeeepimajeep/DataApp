"""
API clients for Anthropic, OpenAI, and Moonshot.
Handles retries, token counting, and cost calculation.
"""

import os
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Anthropic Claude API client."""

    def __init__(self, api_key: Optional[str] = None, config: dict = None):
        """
        Initialize Anthropic client.

        Args:
            api_key: API key (defaults to ANTHROPIC_API_KEY env var).
            config: Config dict with model name, temperature, etc.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.config = config or {}
        self.model = self.config.get("name", "claude-sonnet-4-6")
        self.max_tokens = self.config.get("max_tokens", 16384)
        self.temperature = self.config.get("temperature", 0.6)
        self.top_p = self.config.get("top_p", 0.95)

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package required. pip install anthropic")

    def query(
        self, messages: list[dict], max_retries: int = 3, retry_backoff: float = 2.0
    ) -> dict:
        """
        Query Claude API with retries.

        Returns:
            Dict with keys: "response", "input_tokens", "output_tokens", "cost_usd"
        """
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    messages=messages,
                )

                text = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

                # Cost calculation (Claude Sonnet 4.6)
                cost_usd = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

                return {
                    "response": text,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = retry_backoff ** attempt
                    logger.warning(
                        f"Anthropic query failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"Anthropic query failed after {max_retries} attempts: {e}")
                    raise

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate (Claude uses ~1 token per 4 chars)."""
        return len(text) // 4


class OpenAIClient:
    """OpenAI GPT API client."""

    def __init__(self, api_key: Optional[str] = None, config: dict = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: API key (defaults to OPENAI_API_KEY env var).
            config: Config dict with model name, temperature, etc.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.config = config or {}
        self.model = self.config.get("name", "gpt-5.4-turbo")
        self.max_tokens = self.config.get("max_tokens", 16384)
        self.temperature = self.config.get("temperature", 0.6)
        self.top_p = self.config.get("top_p", 0.95)

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required. pip install openai")

    def query(
        self, messages: list[dict], max_retries: int = 3, retry_backoff: float = 2.0
    ) -> dict:
        """
        Query OpenAI API with retries.

        Returns:
            Dict with keys: "response", "input_tokens", "output_tokens", "cost_usd"
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    messages=messages,
                )

                text = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                # Cost calculation (GPT-4 Turbo)
                cost_usd = (input_tokens * 0.01 + output_tokens * 0.03) / 1000

                return {
                    "response": text,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = retry_backoff ** attempt
                    logger.warning(
                        f"OpenAI query failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"OpenAI query failed after {max_retries} attempts: {e}")
                    raise

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate."""
        return len(text) // 4


class MoonshotClient:
    """Moonshot API client (Kimi)."""

    def __init__(self, api_key: Optional[str] = None, config: dict = None):
        """
        Initialize Moonshot client.

        Args:
            api_key: API key (defaults to MOONSHOT_API_KEY env var).
            config: Config dict with model name, temperature, etc.
        """
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        self.config = config or {}
        self.model = self.config.get("name", "moonshot-v1")
        self.max_tokens = self.config.get("max_tokens", 16384)
        self.temperature = self.config.get("temperature", 0.6)
        self.top_p = self.config.get("top_p", 0.95)
        self.base_url = self.config.get("base_url", "https://api.moonshot.cn/v1")

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("openai package required. pip install openai")

    def query(
        self, messages: list[dict], max_retries: int = 3, retry_backoff: float = 2.0
    ) -> dict:
        """
        Query Moonshot API with retries.

        Returns:
            Dict with keys: "response", "input_tokens", "output_tokens", "cost_usd"
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    messages=messages,
                )

                text = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                # Cost calculation (Moonshot)
                cost_usd = (input_tokens + output_tokens) * 0.0008 / 1000

                return {
                    "response": text,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = retry_backoff ** attempt
                    logger.warning(
                        f"Moonshot query failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"Moonshot query failed after {max_retries} attempts: {e}")
                    raise

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate."""
        return len(text) // 4
