"""LLM factory. Provider is swappable via .env (any OpenAI-compatible endpoint)."""
import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.getenv("LLM_BASE_URL") or None,
        api_key=os.getenv("LLM_API_KEY", "missing-key"),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0,
        timeout=float(os.getenv("LLM_TIMEOUT", "30")),
        max_retries=1,
    )
