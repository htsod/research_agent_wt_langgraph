# apps/agents/src/models/client_factory.py

from langchain_openai import ChatOpenAI

from apps.agents.src.config.settings import settings


def get_llm(
    *,
    model: str | None = None,
    temperature: float | None = None,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or settings.llm_model,
        base_url=settings.llm_base_url,
        api_key="not-needed",
        temperature=settings.llm_temperature if temperature is None else temperature,
    )