# apps/agents/src/agents/base.py

from abc import ABC, abstractmethod
from typing import Any, Callable, List

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage

from apps.agents.src.models.client_factory import get_llm


class BaseProjectAgent(ABC):
    """Base class for project agents."""

    name: str = "base_agent"
    description: str = "Base project agent."

    def __init__(
        self,
        *,
        tools: List[Callable[..., Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ):
        self.tools = tools or []
        self.llm = get_llm(model=model, temperature=temperature)
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt(),
        )

    @abstractmethod
    def system_prompt(self) -> str:
        raise NotImplementedError

    def invoke(self, message: str) -> str:
        result = self.agent.invoke(
            {
                "messages": [
                    HumanMessage(content=message),
                ]
            }
        )

        messages = result.get("messages", [])
        if not messages:
            return str(result)

        last = messages[-1]
        return getattr(last, "content", str(last))