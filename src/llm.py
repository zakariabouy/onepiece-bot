# src/llm.py — LLM clients
#
# Two clients for different use cases:
#   llm_chat()         → Groq (llama-3.1-8b-instant) — fast, for chat
#   llm_chat_quality() → Cerebras (llama-3.1-70b)    — better reasoning, for theory/NLI
#                        Falls back to Groq if no Cerebras key is set.

from typing import List, Dict
from groq import Groq
from .config import (
    get_api_key,
    get_cerebras_api_key,
    GROQ_MODEL,
    CEREBRAS_MODEL,
    CEREBRAS_BASE_URL,
)

_groq_client = None
_cerebras_client = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = get_api_key()
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set! Get free key at: https://console.groq.com/keys"
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def _get_cerebras_client():
    """Returns an OpenAI-compatible client pointed at Cerebras, or None."""
    global _cerebras_client
    if _cerebras_client is None:
        api_key = get_cerebras_api_key()
        if not api_key:
            return None
        from openai import OpenAI
        _cerebras_client = OpenAI(api_key=api_key, base_url=CEREBRAS_BASE_URL)
    return _cerebras_client


# ---------- Fast LLM (Groq — for chat) ----------

def llm_chat(
    messages: List[Dict], temperature: float = 0.5, timeout: float = 30.0
) -> str:
    """Send messages to Groq (fast model) and return the assistant reply."""
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip() or "(no reply)"
    except Exception as e:
        return f"(LLM error: {e})"


# ---------- Quality LLM (Cerebras — for theory/NLI) ----------

def llm_chat_quality(
    messages: List[Dict], temperature: float = 0.3, timeout: float = 60.0
) -> str:
    """
    Send messages to Cerebras (70B model) for higher-quality reasoning.
    Falls back to Groq if Cerebras is not configured.
    """
    cerebras = _get_cerebras_client()
    if cerebras is None:
        # Fallback: use Groq with its best available model
        return llm_chat(messages, temperature=temperature, timeout=timeout)

    try:
        response = cerebras.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip() or "(no reply)"
    except Exception as e:
        # Fallback to Groq on Cerebras error
        print(f"Cerebras error, falling back to Groq: {e}")
        return llm_chat(messages, temperature=temperature, timeout=timeout)
