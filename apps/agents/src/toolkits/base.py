# apps/agents/src/toolkits/base.py

from abc import ABC, abstractmethod
from typing import Any, Callable, List


class BaseToolkit(ABC):
    """Base class for tool groups.

    A toolkit owns related capabilities, shared configuration,
    and safety constraints.
    """

    @abstractmethod
    def tools(self) -> List[Callable[..., Any]]:
        """Return LangChain-compatible tools."""
        raise NotImplementedError