"""
Universal LLM Client using LiteLLM.
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
    """Universal LLM client with rate limiting, backoff, and fallback."""

    def __init__(self, model: str, max_rpm: int, max_retries: int, retry_base_delay: int, 
                 daily_budget: int, request_delay: float, fallback_models: Optional[List[str]] = None):
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
        if self.daily_budget <= 0: return
        if time.time() - self._daily_reset_time > 86400:
            self._daily_count = 0
            self._daily_reset_time = time.time()
        if self._daily_count >= self.daily_budget:
            raise RuntimeError(f"Daily LLM budget exceeded ({self.daily_budget})")

    def _get_model_pool(self) -> List[str]:
        return [self.model] + self.fallback_models

    def _get_provider_from_model(self, model: str) -> str:
        if model.startswith("gpt"): return "openai"
        if model.startswith("gemini"): return "gemini"
        if "groq" in model: return "groq"
        if "/" in model: return model.split("/")[0]
        return model.lower()

    def _get_api_key_for_model(self, model: str) -> Optional[str]:
        provider = self._get_provider_from_model(model)
        key_map = {
            "openai": config.OPENAI_API_KEY,
            "gemini": config.GEMINI_API_KEY,
            "groq": config.GROQ_API_KEY,
        }
        return key_map.get(provider)

    def generate_content(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 1,
                         response_format: Optional[Type[BaseModel]] = None, model_override: Optional[str] = None) -> str:
        self._check_daily_budget()
        messages = []
        if system_prompt: messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        base_kwargs = {"messages": messages, "temperature": temperature}
        if response_format: 
            base_kwargs["response_model"] = response_format

        model_pool = [model_override] if model_override else self._get_model_pool()
        last_exception = None

        for attempt in range(len(model_pool) + self.max_retries):
            current_model = model_pool[attempt % len(model_pool)]
            try:
                self.rate_limiter.acquire()
                if self.request_delay > 0 and attempt == 0: time.sleep(self.request_delay)

                kwargs = base_kwargs.copy()
                kwargs["model"] = current_model
                api_key = self._get_api_key_for_model(current_model)
                if api_key: kwargs["api_key"] = api_key

                logger.info(f"Using model: {current_model}")
                response = litellm.completion(**kwargs)
                self._daily_count += 1
                content = response.choices[0].message.content
                if content:
                    logger.info(f"LLM request successful using {current_model}")
                    return content.strip()
                logger.warning(f"Empty response from {current_model}")
                return ""
            except Exception as e:
                last_exception = e
                logger.warning(f"LLM error on {current_model}. Error: {e}")
                delay = self.retry_base_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
        
        logger.error(f"All attempts failed. Last error: {last_exception}")
        raise last_exception if last_exception else RuntimeError("LLM generation failed after all retries.")

def _create_primary_client() -> LLMClient:
    """Creates the primary LLM client from config."""
    provider = config.LLM_PROVIDER
    if provider not in config.LLM_CONFIG:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    provider_config = config.LLM_CONFIG[provider]
    
    return LLMClient(
        model=provider_config["model"],
        fallback_models=provider_config.get("fallback_models", []),
        max_rpm=provider_config["max_rpm"],
        max_retries=provider_config["max_retries"],
        retry_base_delay=provider_config["retry_base_delay"],
        daily_budget=provider_config["daily_budget"],
        request_delay=provider_config["request_delay"],
    )

# --- Global Primary Client ---
# This is the single, authoritative client for the application.
primary_client = _create_primary_client()
