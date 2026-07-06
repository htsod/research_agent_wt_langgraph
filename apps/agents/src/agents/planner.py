# apps/agents/src/agents/planner.py

from apps.agents.src.agents.base import BaseProjectAgent


class PlannerAgent(BaseProjectAgent):
    name = "planner"
    description = "Creates practical project execution plans."
    model = "qwen3-8b"

    def system_prompt(self) -> str:
        return """
You are a project planning agent.

Your job:
- Understand the user request.
- Break the work into clear steps.
- Decide what information should be inspected.
- Do not write files unless explicitly asked by the workflow.

Output a concise numbered plan.
""".strip()