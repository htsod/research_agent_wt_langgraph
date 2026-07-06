# apps/agents/src/registry/agent_registry.py

from apps.agents.src.agents.analyst import AnalystAgent
from apps.agents.src.agents.planner import PlannerAgent
from apps.agents.src.agents.reviewer import ReviewerAgent
from apps.agents.src.agents.researcher import ResearchAgent
from apps.agents.src.toolkits.filesystem import FilesystemToolkit
from apps.agents.src.toolkits.project_analysis import ProjectAnalysisToolkit
from apps.agents.src.toolkits.research import ResearchToolkit


class AgentRegistry:
    """Creates agents with shared or specialized tools."""

    def __init__(self):
        self.filesystem_toolkit = FilesystemToolkit()
        self.project_analysis_toolkit = ProjectAnalysisToolkit()
        self.research_toolkit = ResearchToolkit()

    def build_planner(self) -> PlannerAgent:
        # Planner does not need write tools in first version.
        return PlannerAgent(
            tools=[],
            temperature=0.2,
        )

    def build_analyst(self) -> AnalystAgent:
        # Analyst gets project analysis tools.
        return AnalystAgent(
            tools=self.project_analysis_toolkit.tools(),
            temperature=0.2,
        )

    def build_reviewer(self) -> ReviewerAgent:
        # Reviewer only needs read/list tools.
        return ReviewerAgent(
            tools=self.filesystem_toolkit.tools(),
            temperature=0.1,
        )
    
    def build_researcher(self, project_path: str) -> ResearchAgent:
        return ResearchAgent(
            tools=self.research_toolkit.tools(project_path=project_path),
            temperature=0.2,
        )