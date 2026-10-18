import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any
import httpx

from backend.core.config import settings

logger = logging.getLogger("CLOUD_LLM")

def get_active_cloud_provider_info() -> Dict[str, Any]:
    """Returns detected cloud API providers and active configuration."""
    providers = []
    if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
        providers.append("gemini")
    if settings.OPENROUTER_API_KEY and not settings.OPENROUTER_API_KEY.startswith("your_"):
        providers.append("openrouter")
    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your_"):
        providers.append("groq")
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"):
        providers.append("openai")
    
    active_provider = settings.CLOUD_API_PROVIDER
    if active_provider == "auto":
        if "openrouter" in providers:
            active_provider = "openrouter"
        elif "groq" in providers:
            active_provider = "groq"
        elif "gemini" in providers:
            active_provider = "gemini"
        elif "openai" in providers:
            active_provider = "openai"
        else:
            active_provider = "gemini"  # default attempt
            
    return {
        "active_provider": active_provider,
        "available_providers": providers,
        "primary_model": settings.PRIMARY_MODEL,
        "openrouter_model": settings.OPENROUTER_MODEL,
        "groq_model": settings.GROQ_MODEL
    }

def call_cloud_llm(
    prompt: str,
    system_prompt: str = "",
    provider: str = "auto",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1500
) -> str:
    """
    Synchronous Universal Cloud LLM caller.
    Supports OpenRouter (Nous-Hermes-3), Groq (Llama-3.3), Gemini, OpenAI.
    Gracefully falls back across available providers.
    """
    provider_info = get_active_cloud_provider_info()
    target_provider = provider if provider != "auto" else provider_info["active_provider"]
    
    # Try OpenRouter
    if (target_provider == "openrouter" or "openrouter" in provider_info["available_providers"]) and settings.OPENROUTER_API_KEY:
        try:
            chosen_model = model or settings.OPENROUTER_MODEL
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://nu.ac.bd",
                "X-Title": "NU-AI-Chatbot"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": chosen_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            with httpx.Client(timeout=25.0) as client:
                res = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip()
                logger.warning(f"OpenRouter returned {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"OpenRouter cloud call failed: {e}")

    # Try Groq
    if (target_provider == "groq" or "groq" in provider_info["available_providers"]) and settings.GROQ_API_KEY:
        try:
            chosen_model = model or settings.GROQ_MODEL
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": chosen_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            with httpx.Client(timeout=25.0) as client:
                res = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip()
                logger.warning(f"Groq returned {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"Groq cloud call failed: {e}")

    # Try Gemini
    if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_prompt if system_prompt else None,
                max_output_tokens=max_tokens
            )
            model_to_use = model or settings.PRIMARY_MODEL
            response = client.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=config
            )
            if response and response.text and response.text.strip():
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini cloud call failed: {e}")

    # Try OpenAI
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"):
        try:
            chosen_model = model or settings.OPENAI_MODEL
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": chosen_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            with httpx.Client(timeout=25.0) as client:
                res = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip()
        except Exception as e:
            logger.warning(f"OpenAI cloud call failed: {e}")

    return ""

async def async_call_cloud_llm(
    prompt: str,
    system_prompt: str = "",
    provider: str = "auto",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1500
) -> str:
    """Asynchronous wrapper for cloud LLM call."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: call_cloud_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    )
