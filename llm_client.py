"""
Universal LLM Client using LiteLLM.

Provides a unified interface for 400+ LLMs with built-in rate limiting,
exponential backoff, and daily budget tracking.

Supports intelligent fallback across multiple LLM providers:
1. Gemini (primary)
2. OpenAI (fallback)
3. Groq (secondary fallback)

Usage:
    from llm_client import primary_client

    response = primary_client.generate_content(
        prompt="Hello!",
        system_prompt="You are a helpful assistant.",
        temperature=0.2,
        response_format=MyPydanticModel
    )
"""

import os
import time
import random
import logging
import threading
from typing import Optional, Type, List

import litellm
from pydantic import BaseModel

import config

logger = logging.getLogger(__name__)

# Suppress LiteLLM verbose logs unless enabled
litellm.suppress_debug_info = True

if os.environ.get("LLM_DEBUG", "").lower() == "true":
    litellm.set_verbose = True


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, max_rpm: int):
        self.max_rpm = max_rpm
        self.tokens = max_rpm
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self):
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill

                refill = elapsed * (self.max_rpm / 60.0)

                self.tokens = min(self.max_rpm, self.tokens + refill)

                self.last_refill = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

            time.sleep(0.5)


class LLMClient:
    """
    Universal LLM client with:
    - Rate limiting
    - Exponential backoff
    - Daily budget tracking
    - Multi-provider fallback
    """

    def __init__(
        self,
        model: str,
        max_rpm: int = 10,
        max_retries: int = 3,
        retry_base_delay: int = 10,
        daily_budget: int = 0,
        request_delay: float = 0,
        fallback_models: Optional[List[str]] = None,
    ):
        self.model = model
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.daily_budget = daily_budget
        self.request_delay = request_delay

        self.rate_limiter = RateLimiter(max_rpm)

        self.fallback_models = fallback_models or []

        self._daily_count = 0
        self._daily_reset_time = time.time()

    def _check_daily_budget(self):
        """Reset and validate daily budget."""

        if self.daily_budget <= 0:
            return

        if time.time() - self._daily_reset_time > 86400:
            self._daily_count = 0
            self._daily_reset_time = time.time()

        if self._daily_count >= self.daily_budget:
            raise RuntimeError(
                f"Daily LLM budget exceeded ({self.daily_budget})"
            )

    def _get_model_pool(self) -> List[str]:
        """Return primary + fallback model pool."""
        return [self.model] + self.fallback_models

    def _get_provider_from_model(self, model: str) -> str:
        """
        Detect provider from model name.
        """

        if model.startswith("gpt"):
            return "openai"

        if model.startswith("gemini"):
            return "gemini"

        if "groq" in model:
            return "groq"

        if model.startswith("claude"):
            return "anthropic"

        if "/" in model:
            return model.split("/")[0]

        return model.lower()

    def _get_api_key_for_model(self, model: str) -> Optional[str]:
        """
        Return correct API key for the given model provider.
        """

        provider = self._get_provider_from_model(model)

        # Directly use the config attributes for keys
        key_map = {
            "openai": config.OPENAI_API_KEY,
            "gemini": config.GEMINI_API_KEY,
            "groq": config.GROQ_API_KEY,
        }

        return key_map.get(provider)

    def generate_content(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1,
        response_format: Optional[Type[BaseModel]] = None,
        model_override: Optional[str] = None,
    ) -> str:
        """
        Generate content using intelligent fallback.
        """

        self._check_daily_budget()

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        base_kwargs = {
            "messages": messages,
            "temperature": temperature,
        }

        if response_format is not None:
            # Forcing JSON mode with Pydantic models
            base_kwargs["response_model"] = response_format
            base_kwargs["response_format"] = {"type": "json_object"}


        model_pool = (
            [model_override]
            if model_override
            else self._get_model_pool()
        )

        pool_index = 0

        max_attempts = len(model_pool) + self.max_retries

        last_exception = None

        for attempt in range(max_attempts):

            current_model = model_pool[
                pool_index % len(model_pool)
            ]

            try:
                self.rate_limiter.acquire()

                if self.request_delay > 0 and attempt == 0:
                    time.sleep(self.request_delay)

                kwargs = base_kwargs.copy()

                kwargs["model"] = current_model

                # IMPORTANT:
                # Dynamically choose correct API key
                api_key = self._get_api_key_for_model(
                    current_model
                )

                if api_key:
                    kwargs["api_key"] = api_key

                logger.info(
                    f"Using model: {current_model}"
                )

                if api_key:
                    logger.info(
                        f"API key prefix: {api_key[:6]}..."
                    )

                response = litellm.completion(**kwargs)

                self._daily_count += 1

                content = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                if content:
                    logger.info(
                        f"LLM request successful using {current_model}"
                    )

                    return content.strip()

                logger.warning(
                    f"Empty response from {current_model}"
                )

                return ""

            except Exception as e:

                last_exception = e

                error_str = str(e).lower()

                is_rate_limit = any(
                    keyword in error_str
                    for keyword in [
                        "429",
                        "rate_limit",
                        "rate limit",
                        "resource_exhausted",
                        "quota",
                        "too many requests",
                        "retry",
                    ]
                )

                if attempt < max_attempts - 1:

                    next_model_index = (
                        pool_index + 1
                    ) % len(model_pool)

                    next_model = model_pool[
                        next_model_index
                    ]

                    if is_rate_limit:

                        delay = random.uniform(1, 4)

                        logger.warning(
                            f"Rate limit on {current_model}. "
                            f"Falling back to {next_model}. "
                            f"Retrying in {delay:.1f}s. "
                            f"Error: {e}"
                        )

                    else:

                        delay = (
                            self.retry_base_delay
                            * (2 ** attempt)
                            + random.uniform(0, 5)
                        )

                        logger.warning(
                            f"LLM error on {current_model}. "
                            f"Falling back to {next_model}. "
                            f"Retrying in {delay:.1f}s. "
                            f"Error: {e}"
                        )

                    pool_index = next_model_index

                    time.sleep(delay)

                    continue

        failed_model = model_pool[
            pool_index % len(model_pool)
        ]

        logger.error(
            f"All attempts exhausted across models: "
            f"{model_pool}. "
            f"Last failed model: {failed_model}. "
            f"Last error: {last_exception}"
        )

        raise last_exception


def _create_client(
    model: str,
    fallback_models: Optional[List[str]] = None,
) -> LLMClient:
    """
    Create configured LLM client.
    """

    return LLMClient(
        model=model,
        max_rpm=config.LLM_MAX_RPM,
        max_retries=config.LLM_MAX_RETRIES,
        retry_base_delay=config.LLM_RETRY_BASE_DELAY,
        daily_budget=config.LLM_DAILY_REQUEST_BUDGET,
        request_delay=config.LLM_REQUEST_DELAY_SECONDS,
        fallback_models=fallback_models
        or config.LLM_FALLBACK_MODELS,
    )


# Global primary client

primary_client = _create_client(
    model=config.LLM_MODEL,
    fallback_models=config.LLM_FALLBACK_MODELS,
)
