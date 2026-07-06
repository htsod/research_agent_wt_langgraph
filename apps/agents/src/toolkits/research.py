# apps/agents/src/toolkits/research.py

from pathlib import Path
from typing import Any, Callable, List
from urllib.parse import quote_plus

import httpx
from langchain.tools import tool
from apps.agents.src.toolkits.filesystem import FilesystemToolkit


class ResearchToolkit(FilesystemToolkit):
    """Toolkit for section-by-section research workflows.

    Responsibilities:
    - Load global project context from README
    - Inspect and select supporting files from /brief
    - Discover section files like Abstract.md, Introduction.md, etc.
    - Read section content and selected context files
    - Perform lightweight web search
    - Write section-specific reports and compiled reports
    """

    def load_readme_raw(self, project_path: str) -> str:
        """Load README content if present."""
        candidates = ["README.md", "README.txt", "readme.md", "readme.txt"]

        for name in candidates:
            try:
                path = self.resolve_file_path(project_path, name)
                if path.exists() and path.is_file():
                    return self.read_text_raw(project_path, name)
            except Exception:
                continue

        return ""


    def discover_section_files_raw(self, project_path: str) -> List[dict]:
        """Discover section markdown files under reports/sections first."""
        project_root = self.resolve_project_path(project_path)

        preferred_dir = project_root / "reports" 
        fallback_dirs = [
            project_root / "drafts",
            project_root,
        ]

        candidates: List[Path] = []

        if preferred_dir.exists() and preferred_dir.is_dir():
            candidates.extend(sorted(preferred_dir.glob("*.md")))

        for d in fallback_dirs:
            if d.exists() and d.is_dir():
                candidates.extend(sorted(d.glob("*.md")))

        if not candidates:
            return []

        preferred_order = {
            "readme": 0,
            "abstract": 1,
            "introduction": 2,
            "background": 3,
            "relatedwork": 4,
            "methods": 5,
            "methodology": 6,
            "experiments": 7,
            "results": 8,
            "discussion": 9,
            "conclusion": 10,
        }

        unique: List[Path] = []
        seen = set()
        for p in candidates:
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                unique.append(p)

        def sort_key(p: Path):
            stem = p.stem.lower().replace("_", "").replace("-", "")
            return (preferred_order.get(stem, 999), p.name.lower())

        unique = sorted(unique, key=sort_key)

        found: List[dict] = []
        for idx, p in enumerate(unique, start=1):
            found.append(
                {
                    "name": p.stem,
                    "path": str(p.relative_to(project_root)),
                    "index": idx,
                }
            )

        return found

    def read_section_content_raw(self, project_path: str, rel_path: str) -> str:
        """Read one section file."""
        return self.read_text_raw(project_path, rel_path)

    def search_web_raw(self, query: str, max_results: int = 5) -> str:
        """Lightweight HTML-based DuckDuckGo search.

        For production, replace with Tavily, SerpAPI, Brave Search, etc.
        """
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            html = resp.text

        lines = []
        for line in html.splitlines():
            if "result__a" in line or "result__snippet" in line:
                cleaned = (
                    line.replace("<a", "\n<a")
                    .replace("</a>", "</a>\n")
                    .replace("<", " <")
                    .replace(">", "> ")
                )
                lines.append(cleaned.strip())

        joined = "\n".join(lines[: max_results * 3]).strip()
        if not joined:
            return "No search results extracted."
        return joined[:8000]

    def write_research_report_raw(self, project_path: str, content: str) -> str:
        """Write a generic research summary report."""
        return self.write_text_raw(
            project_path=project_path,
            rel_path="summaries/research_summary.md",
            content=content,
        )

    def write_section_review_raw(
        self,
        project_path: str,
        section_index: int,
        section_name: str,
        content: str,
    ) -> str:
        """Write one section review report."""
        safe_name = section_name.replace(" ", "_")
        # rel_path = f"summaries/{section_index:02d}_{safe_name}_review.md"
        rel_path = f"summaries/{safe_name}_review.md"
        return self.write_text_raw(
            project_path=project_path,
            rel_path=rel_path,
            content=content,
        )

    def write_compiled_review_raw(self, project_path: str, content: str) -> str:
        """Write the compiled multi-section review report."""
        return self.write_text_raw(
            project_path=project_path,
            rel_path="summaries/compiled_research_review.md",
            content=content,
        )

    def tools(self, project_path: str) -> List[Callable[..., Any]]:
        """Expose LangChain-compatible tools."""
        toolkit = self
        # project_path = "{project_path}"  # Placeholder to be filled by agent context

    
        @tool
        def load_project_readme(project_path=project_path) -> str:
            """Load README.md or similar root readme file for the project."""
            return toolkit.load_readme_raw(project_path)

        # @tool
        # def list_brief_tree(project_path: str) -> str:
        #     """List the tree under the project's brief folder."""
        #     return "\n".join(toolkit.list_brief_tree_raw(project_path))

        # @tool
        # def select_brief_files(project_path: str) -> str:
        #     """Select a limited set of brief files for contextual reading."""
        #     return "\n".join(toolkit.select_brief_files_raw(project_path))

        @tool
        def discover_section_files(project_path=project_path) -> str:
            """Discover section markdown files such as Abstract.md and Introduction.md."""
            sections = toolkit.discover_section_files_raw(project_path)
            return "\n".join(
                f"{item['index']}. {item['name']} -> {item['path']}" for item in sections
            )

        @tool
        def read_section_file(rel_path: str, project_path=project_path) -> str:
            """Read a single section file from the project."""
            return toolkit.read_section_content_raw(project_path, rel_path)

        # @tool
        # def read_selected_project_files(project_path: str, rel_paths: str) -> str:
        #     """Read multiple project files. Pass newline-separated relative file paths."""
        #     paths = [p.strip() for p in rel_paths.splitlines() if p.strip()]
        #     return toolkit.read_selected_files_raw(project_path, paths)

        @tool
        def search_web(query: str) -> str:
            """Search the web for public information related to the query."""
            return toolkit.search_web_raw(query)

        @tool
        def write_research_report(content: str, project_path=project_path) -> str:
            """Write a generic research summary report into the project's summaries folder."""
            return toolkit.write_research_report_raw(project_path, content)

        @tool
        def write_section_review(
            project_path: str,
            section_index: int,
            section_name: str,
            content: str,
        ) -> str:
            """Write a section-specific review report into summaries/section_reviews."""
            return toolkit.write_section_review_raw(
                project_path=project_path,
                section_index=section_index,
                section_name=section_name,
                content=content,
            )

        @tool
        def write_compiled_review(content: str, project_path=project_path) -> str:
            """Write the compiled research review report."""
            return toolkit.write_compiled_review_raw(project_path, content)

        return [
            load_project_readme,
            discover_section_files,
            read_section_file,
            search_web,
            write_research_report,
            write_section_review,
            write_compiled_review,
        ]