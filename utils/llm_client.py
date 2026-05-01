"""
utils/llm_client.py
Unified LLM client — supports multiple providers with automatic fallback.

Priority order:
  1. Google Gemini (GOOGLE_API_KEY)        — free tier generous
  2. OpenRouter  (OPENROUTER_API_KEY)      — free models available
  3. Anthropic   (ANTHROPIC_API_KEY)       — paid
  4. Ollama      (OLLAMA_URL)              — local, fully free
  5. Rule-based  fallback                  — always works, no API needed

All providers use OpenAI-compatible chat completions API where possible.
"""

import os
import json
import requests
from utils.logger import log

# ── API Keys ──────────────────────────────────────────────────────────────────
GOOGLE_API_KEY     = os.getenv("GOOGLE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
OLLAMA_URL         = os.getenv("OLLAMA_URL", "http://localhost:11434")

# ── Model configs ─────────────────────────────────────────────────────────────
# Google Gemini — free tier: 15 RPM, 1M tokens/day
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# OpenRouter — free models rotate; use the free router or specific free model
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")

# Ollama — local open source (requires `ollama run llama3.2` first)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def get_active_provider() -> str:
    """Return the name of the provider that will be used."""
    if GOOGLE_API_KEY:
        return "google"
    if OPENROUTER_API_KEY:
        return "openrouter"
    if ANTHROPIC_API_KEY:
        return "anthropic"
    # Check if Ollama is running
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            return "ollama"
    except Exception:
        pass
    return "rule-based"


def chat(system: str, user: str, max_tokens: int = 512) -> str:
    """
    Send a chat completion request to the best available LLM provider.
    Returns the raw text response.
    Raises Exception if all providers fail.
    """
    provider = get_active_provider()
    log("sys", f"LLM provider: {provider}")

    if provider == "google":
        return _call_gemini(system, user, max_tokens)
    elif provider == "openrouter":
        return _call_openrouter(system, user, max_tokens)
    elif provider == "anthropic":
        return _call_anthropic(system, user, max_tokens)
    elif provider == "ollama":
        return _call_ollama(system, user, max_tokens)
    else:
        raise RuntimeError("No LLM provider available")


def is_available() -> bool:
    """Check if any LLM provider is available."""
    return get_active_provider() != "rule-based"


# ── Google Gemini ─────────────────────────────────────────────────────────────

def _call_gemini(system: str, user: str, max_tokens: int) -> str:
    """Call Google Gemini via the generateContent REST API."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": user}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.3,
        },
    }
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        log("sys", f"Gemini ({GEMINI_MODEL}) responded ✓")
        return text.strip()
    except Exception as e:
        log("sys", f"Gemini failed: {e}", ok=False)
        raise


# ── OpenRouter ────────────────────────────────────────────────────────────────

def _call_openrouter(system: str, user: str, max_tokens: int) -> str:
    """Call OpenRouter API (OpenAI-compatible)."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://agentns.xyz",
        "X-Title": "AGENTNS",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        model_used = data.get("model", OPENROUTER_MODEL)
        log("sys", f"OpenRouter ({model_used}) responded ✓")
        return text.strip()
    except Exception as e:
        log("sys", f"OpenRouter failed: {e}", ok=False)
        raise


# ── Anthropic ─────────────────────────────────────────────────────────────────

def _call_anthropic(system: str, user: str, max_tokens: int) -> str:
    """Call Anthropic Messages API directly."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        text = data["content"][0]["text"]
        log("sys", "Anthropic (Claude Sonnet) responded ✓")
        return text.strip()
    except Exception as e:
        log("sys", f"Anthropic failed: {e}", ok=False)
        raise


# ── Ollama (local) ────────────────────────────────────────────────────────────

def _call_ollama(system: str, user: str, max_tokens: int) -> str:
    """Call local Ollama server (OpenAI-compatible endpoint)."""
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3,
        },
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        text = data["message"]["content"]
        log("sys", f"Ollama ({OLLAMA_MODEL}) responded ✓")
        return text.strip()
    except Exception as e:
        log("sys", f"Ollama failed: {e}", ok=False)
        raise
