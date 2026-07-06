# apps/agents/src/toolkits/project_analysis.py

from pathlib import Path
from typing import Any, Callable, List

from langchain.tools import tool

from apps.agents.src.config.settings import settings
from apps.agents.src.toolkits.filesystem import FilesystemToolkit


class ProjectAnalysisToolkit(FilesystemToolkit):
    """Specialized toolkit for analyzing project structure."""

    def select_key_files_raw(self, project_path: str) -> List[str]:
        project_root = self.resolve_project_path(project_path)

        candidates: List[Path] = []

        brief_dir = project_root / "brief"
        if brief_dir.exists() and brief_dir.is_dir():
            for ext in ("*.md", "*.txt"):
                candidates.extend(sorted(brief_dir.glob(ext)))

        for name in ["README.md", "README.txt", "readme.md", "readme.txt"]:
            p = project_root / name
            if p.exists() and p.is_file():
                candidates.append(p)

        docs_dir = project_root / "docs"
        if docs_dir.exists() and docs_dir.is_dir():
            for ext in ("*.md", "*.txt"):
                candidates.extend(sorted(docs_dir.glob(ext)))

        unique: List[Path] = []
        seen = set()

        for p in candidates:
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                unique.append(p)

        return [
            str(p.relative_to(project_root))
            for p in unique[: settings.max_key_files]
        ]

    def write_assessment_raw(
        self,
        project_path: str,
        content: str,
    ) -> str:
        return self.write_text_raw(
            project_path=project_path,
            rel_path="reports/initial_assessment.md",
            content=content,
        )

    def write_next_steps_raw(
        self,
        project_path: str,
        content: str,
    ) -> str:
        return self.write_text_raw(
            project_path=project_path,
            rel_path="artifacts/next_steps.md",
            content=content,
        )

    def tools(self) -> List[Callable[..., Any]]:
        base_tools = super().tools()
        toolkit = self

        @tool
        def select_project_key_files(project_path: str) -> str:
            """Select key project files such as brief files, README, and docs."""
            files = toolkit.select_key_files_raw(project_path)
            return "\n".join(files)

        @tool
        def write_initial_assessment(project_path: str, content: str) -> str:
            """Write the initial project assessment report."""
            return toolkit.write_assessment_raw(project_path, content)

        @tool
        def write_project_next_steps(project_path: str, content: str) -> str:
            """Write the project's next steps artifact."""
            return toolkit.write_next_steps_raw(project_path, content)

        return base_tools + [
            select_project_key_files,
            write_initial_assessment,
            write_project_next_steps,
        ]