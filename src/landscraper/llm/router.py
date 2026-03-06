"""LLM routing: local models for cost-sensitive tasks, cloud for complex reasoning."""

from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_core.language_models import BaseChatModel

from landscraper.config import settings

# Task types that should use cloud models
CLOUD_TASKS = frozenset({
    "consensus_arbitration",
    "novel_source_evaluation",
    "lead_narrative",
    "strategy_analysis",
    "complex_extraction",
})


def get_llm(task_type: str = "default", temperature: float = 0.0) -> BaseChatModel:
    """Route to the appropriate LLM based on task type.

    Args:
        task_type: The type of task. Cloud tasks get Claude, everything else gets local.
        temperature: LLM temperature setting.

    Returns:
        A LangChain chat model instance.
    """
    if task_type in CLOUD_TASKS and settings.anthropic_api_key:
        return ChatAnthropic(
            model=settings.default_cloud_model,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=4096,
        )

    return ChatOllama(
        model=settings.default_local_model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
    )
