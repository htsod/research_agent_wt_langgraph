# apps/agents/src/agents/reviewer.py

from apps.agents.src.agents.base import BaseProjectAgent


class ReviewerAgent(BaseProjectAgent):
    name = "reviewer"
    description = "Reviews project reports for clarity, completeness, and usefulness."
    model = "qwen3-8b"
    
    def system_prompt(self) -> str:
        return """
You are a project review agent.

Your job:
- Review the proposed assessment.
- Check whether it is clear, grounded, and actionable.
- Identify weak assumptions.
- Suggest improvements.

Do not rewrite everything unless necessary.
Return a concise review.
""".strip()