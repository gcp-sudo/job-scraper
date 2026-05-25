"""
Universal LLM Client using LiteLLM.
"""

import os
import time
import random
import logging
import threading
import json
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

    def _get_api_key_for_model(self, model: str) -> Optional[str]:
        provider = model.split('/')[0] if '/' in model else None
        if "gpt" in model: provider = "openai"
        elif "gemini" in model: provider = "gemini"
        
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
            # Convert Pydantic model to JSON schema for the 'tools' parameter
            schema = response_format.model_json_schema()
            tool_name = schema.get("title", "structured_output")
            base_kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": f"Extracts data matching the '{tool_name}' schema.",
                        "parameters": schema
                    },
                }
            ]
            base_kwargs["tool_choice"] = {"type": "function", "function": {"name": tool_name}}

        model_pool = [model_override] if model_override else self._get_model_pool()
        last_exception = None

        for model in model_pool:
            for attempt in range(self.max_retries + 1):
                try:
                    self.rate_limiter.acquire()
                    
                    if model == self.model and attempt == 0 and self.request_delay > 0:
                        time.sleep(self.request_delay)

                    kwargs = base_kwargs.copy()
                    kwargs["model"] = model
                    api_key = self._get_api_key_for_model(model)
                    if api_key: kwargs["api_key"] = api_key

                    logger.info(f"Attempt {attempt + 1}/{self.max_retries + 1} with model: {model}")
                    response = litellm.completion(**kwargs)
                    self._daily_count += 1

                    if response_format:
                        if not response.choices[0].message.tool_calls:
                            raise ValueError("Model failed to return the required tool call for structured output.")
                        
                        tool_call = response.choices[0].message.tool_calls[0]
                        content = tool_call.function.arguments
                        
                        json.loads(content)  # Validate JSON
                        logger.info(f"LLM request successful using {model} with structured output.")
                        return content
                    else:
                        content = response.choices[0].message.content
                        if content:
                            logger.info(f"LLM request successful using {model}")
                            return content.strip()
                        else:
                            raise ValueError("Model returned an empty response.")
                
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Error on attempt {attempt + 1} with {model}: {e}")
                    if attempt < self.max_retries:
                        delay = self.retry_base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.info(f"Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All retries failed for model {model}.")
                        break 
        
        logger.error(f"All models in the pool failed. Last error: {last_exception}")
        raise last_exception if last_exception else RuntimeError("LLM generation failed for all models.")


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
primary_client = _create_primary_client()
