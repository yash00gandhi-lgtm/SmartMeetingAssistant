"""
llm_provider.py
---------------
Factory that returns either an OpenRouter or Groq chat model
based on LLM_PROVIDER in .env.
"""

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from config import (
    LLM_PROVIDER,
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL,
    GROQ_API_KEY, GROQ_MODEL,
)


def get_llm(temperature: float = 0.2):
    """Return a configured chat LLM. Lower temp = more factual."""
    if LLM_PROVIDER == "groq":
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=temperature,
        )
    # default: OpenRouter (OpenAI-compatible)
    return ChatOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        model=OPENROUTER_MODEL,
        temperature=temperature,
    )
