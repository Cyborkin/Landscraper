"""LLM factory for Landscraper agent nodes.

Each node role maps to the least expensive Anthropic model capable of the task:
- Haiku 4.5: structured extraction, classification, summarization
- Sonnet 4.6: analytical reasoning, strategy generation
"""

from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from landscraper.config import settings

ROLE_MODELS = {
    "source_discovery": "claude-haiku-4-5-20251001",
    "enrichment": "claude-haiku-4-5-20251001",
    "consensus": "claude-haiku-4-5-20251001",
    "strategy": "claude-sonnet-4-6",
    "summary": "claude-haiku-4-5-20251001",
}


@lru_cache(maxsize=8)
def get_llm(role: str, temperature: float = 0.0) -> ChatAnthropic:
    """Get an LLM instance for the given node role."""
    model = ROLE_MODELS.get(role, "claude-haiku-4-5-20251001")
    return ChatAnthropic(
        model=model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=1024,
    )
