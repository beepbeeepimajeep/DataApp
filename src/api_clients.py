"""
API clients for GPT-5.4 (OpenAI direct), GPT-OSS-120B (TritonAI free tier),
Claude Sonnet 4.6 (Anthropic), and GPT-5.5 xhigh (OpenAI direct).
All clients share the same response format.
"""

import os
import time
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def _error_response(error: str, model: str, elapsed: float, route: str = None) -> dict:
    """Create error response dict."""
    resp = {
        "response": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "hit_token_cap": False,
        "finish_reason": None,
        "generation_time_s": elapsed,
        "model": model,
        "request_id": None,
        "error": error,
    }
    if route:
        resp["route"] = route
    return resp


class GPT54Client:
    """GPT-5.4: OpenAI API directly."""

    def __init__(self, tritonai_model: str = "gpt-5.4", openai_model: str = "gpt-5.4"):
        self.model = openai_model  # For logging

        try:
            from openai import OpenAI

            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        except ImportError:
            raise ImportError("openai package required. pip install openai")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def _call_impl(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> dict:
        """Internal implementation that raises on failure (for tenacity retry)."""
        start = time.time()
        resp = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )
        return {
            "response": resp.choices[0].message.content or "",
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
            "hit_token_cap": resp.choices[0].finish_reason == "length",
            "finish_reason": resp.choices[0].finish_reason,
            "generation_time_s": time.time() - start,
            "model": self.model,
            "request_id": resp.id,
            "error": None,
            "route": "openai",
        }

    def call(
        self, messages: list[dict], temperature: float, max_tokens: int, **kwargs
    ) -> dict:
        """
        Query GPT-5.4 directly via OpenAI API.

        Returns:
            Dict with: response, input_tokens, output_tokens, hit_token_cap,
            finish_reason, generation_time_s, model, request_id, error, route
        """
        try:
            return self._call_impl(messages, temperature, max_tokens)
        except Exception as e:
            return _error_response(str(e), self.model, time.time(), "openai")


class GPTOSSClient:
    """GPT-OSS-120B: TritonAI free tier only. No fallback — skip item if TritonAI down."""

    def __init__(self, model: str = "gpt-oss-120b"):
        self.model = model

        try:
            from openai import OpenAI

            self.client = OpenAI(
                base_url="https://tritonai-api.ucsd.edu/v1",
                api_key=os.environ.get("TRITON_API_KEY", ""),
            )
        except ImportError:
            raise ImportError("openai package required. pip install openai")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def _call_impl(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> dict:
        """Internal implementation that raises on failure (for tenacity retry)."""
        start = time.time()
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {
            "response": resp.choices[0].message.content or "",
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
            "hit_token_cap": resp.choices[0].finish_reason == "length",
            "finish_reason": resp.choices[0].finish_reason,
            "generation_time_s": time.time() - start,
            "model": self.model,
            "request_id": resp.id,
            "error": None,
            "route": "tritonai",
        }

    def call(
        self, messages: list[dict], temperature: float, max_tokens: int, **kwargs
    ) -> dict:
        """
        Call GPT-OSS-120B on TritonAI free tier.

        Returns:
            Dict with: response, input_tokens, output_tokens, hit_token_cap,
            finish_reason, generation_time_s, model, request_id, error, route
        """
        try:
            return self._call_impl(messages, temperature, max_tokens)
        except Exception as e:
            return _error_response(str(e), self.model, time.time(), "tritonai")


class GPT55Client:
    """GPT-5.5 (xhigh reasoning): OpenAI API directly."""

    def __init__(self, model: str = "gpt-5.5"):
        self.model = model

        try:
            from openai import OpenAI

            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        except ImportError:
            raise ImportError("openai package required. pip install openai")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def _call_impl(
        self, messages: list[dict], reasoning_effort: str, max_tokens: int
    ) -> dict:
        """Internal implementation that raises on failure (for tenacity retry)."""
        start = time.time()
        resp = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1.0,  # Required for reasoning_effort
            max_completion_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )

        result = {
            "response": resp.choices[0].message.content or "",
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
            "hit_token_cap": resp.choices[0].finish_reason == "length",
            "finish_reason": resp.choices[0].finish_reason,
            "generation_time_s": time.time() - start,
            "model": self.model,
            "request_id": resp.id,
            "error": None,
            "route": "openai",
        }

        # Add reasoning tokens if available (GPT-5.5 extended thinking)
        if hasattr(resp.usage, "completion_tokens_details") and resp.usage.completion_tokens_details:
            result["reasoning_tokens"] = getattr(
                resp.usage.completion_tokens_details, "reasoning_tokens", 0
            )

        return result

    def call(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        reasoning_effort: str = "xhigh",
        **kwargs
    ) -> dict:
        """
        Query GPT-5.5 via OpenAI API with extended thinking (reasoning_effort).

        Returns:
            Dict with: response, input_tokens, output_tokens, hit_token_cap,
            finish_reason, generation_time_s, model, request_id, error, route,
            reasoning_tokens (if available)
        """
        try:
            return self._call_impl(messages, reasoning_effort, max_tokens)
        except Exception as e:
            return _error_response(str(e), self.model, time.time(), "openai")


class SonnetClient:
    """Claude Sonnet 4.6 via Anthropic API."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        try:
            from anthropic import Anthropic

            self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        except ImportError:
            raise ImportError("anthropic package required. pip install anthropic")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
    def _call_impl(
        self, system: str, user_messages: list[dict], temperature: float, max_tokens: int
    ) -> dict:
        """Internal implementation that raises on failure (for tenacity retry)."""
        start = time.time()
        resp = self.client.messages.create(
            model=self.model,
            system=system,
            messages=user_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "response": resp.content[0].text if resp.content else "",
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "hit_token_cap": resp.stop_reason == "max_tokens",
            "finish_reason": resp.stop_reason,
            "generation_time_s": time.time() - start,
            "model": self.model,
            "request_id": resp.id,
            "error": None,
            "route": "anthropic",
        }

    def call(
        self, messages: list[dict], temperature: float, max_tokens: int, **kwargs
    ) -> dict:
        """
        Query Claude Sonnet 4.6 API with automatic retries.

        Returns:
            Dict with: response, input_tokens, output_tokens, hit_token_cap,
            finish_reason, generation_time_s, model, request_id, error, route
        """
        # Anthropic requires system message as separate parameter
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]

        try:
            return self._call_impl(system, user_messages, temperature, max_tokens)
        except Exception as e:
            return _error_response(str(e), self.model, time.time(), "anthropic")
