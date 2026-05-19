"""
API clients for GPT-5.4 (TritonAI primary + OpenAI fallback), GPT-OSS-120B (TritonAI free),
and Claude Sonnet 4.6 (Anthropic). All clients share the same response format.
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
    def call(
        self, messages: list[dict], temperature: float, max_tokens: int, **kwargs
    ) -> dict:
        """
        Query GPT-5.4 directly via OpenAI API.

        Returns:
            Dict with: response, input_tokens, output_tokens, hit_token_cap,
            generation_time_s, model, request_id, error, route
        """
        start = time.time()

        try:
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
                "generation_time_s": time.time() - start,
                "model": self.model,
                "request_id": resp.id,
                "error": None,
                "route": "openai",
            }
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start, "openai")


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
    def call(
        self, messages: list[dict], temperature: float, max_tokens: int, **kwargs
    ) -> dict:
        """
        Call GPT-OSS-120B on TritonAI free tier.

        Returns:
            Dict with: response, input_tokens, output_tokens, hit_token_cap,
            generation_time_s, model, request_id, error, route
        """
        start = time.time()
        try:
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
                "generation_time_s": time.time() - start,
                "model": self.model,
                "request_id": resp.id,
                "error": None,
                "route": "tritonai",
            }
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start, "tritonai")


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
            generation_time_s, model, request_id, error, route,
            reasoning_tokens (if available)
        """
        start = time.time()

        try:
            # GPT-5.5 with reasoning_effort requires temperature=1 (default)
            # Ignore the passed temperature parameter for this model
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
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start, "openai")


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
    def call(
        self, messages: list[dict], temperature: float, max_tokens: int, **kwargs
    ) -> dict:
        """
        Query Claude Sonnet 4.6 API with automatic retries.

        Returns:
            Dict with: response, input_tokens, output_tokens, hit_token_cap,
            generation_time_s, model, request_id, error, route
        """
        start = time.time()

        # Anthropic requires system message as separate parameter
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]

        try:
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
                "generation_time_s": time.time() - start,
                "model": self.model,
                "request_id": resp.id,
                "error": None,
                "route": "anthropic",
            }
        except Exception as e:
            return _error_response(str(e), self.model, time.time() - start, "anthropic")
