# apps/agents/src/toolkits/filesystem.py

from pathlib import Path
from typing import Any, Callable, List

from langchain.tools import tool

from apps.agents.src.config.settings import settings
from apps.agents.src.toolkits.base import BaseToolkit


class FilesystemToolkit(BaseToolkit):
    """General safe filesystem toolkit for project workspaces."""

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = (workspace_root or settings.workspace_root).resolve()

    # def resolve_project_path(self, project_path: str) -> Path:
    #     path = Path(project_path)

    #     if not path.is_absolute():
    #         path = (Path.cwd() / path).resolve()
    #     else:
    #         path = path.resolve()

    #     if path != self.workspace_root and self.workspace_root not in path.parents:
    #         raise ValueError(f"Project path escapes workspace root: {path}")

    #     if not path.exists():
    #         raise FileNotFoundError(f"Project path does not exist: {path}")

    #     if not path.is_dir():
    #         raise NotADirectoryError(f"Project path is not a directory: {path}")

    #     return path

    def resolve_project_path(self, project_path: str) -> Path:
        if project_path == "/workspace":
            project_path = "workspace"

        path = Path(project_path)
        print("DEBUG workspace_root =", self.workspace_root)
        print("DEBUG incoming path =", path)

        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()

        if path != self.workspace_root and self.workspace_root not in path.parents:
            raise ValueError(f"Project path escapes workspace root: {path}")

        if not path.exists():
            raise FileNotFoundError(f"Project path does not exist: {path}")

        if not path.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {path}")

        return path

    def resolve_file_path(self, project_path: str, rel_path: str) -> Path:
        project_root = self.resolve_project_path(project_path)
        file_path = (project_root / rel_path).resolve()

        if file_path != project_root and project_root not in file_path.parents:
            raise ValueError(f"File path escapes project root: {file_path}")

        return file_path

    def list_tree_raw(
        self,
        project_path: str,
        max_depth: int | None = None,
        max_entries: int | None = None,
    ) -> List[str]:
        project_root = self.resolve_project_path(project_path)
        max_depth = max_depth or settings.max_tree_depth
        max_entries = max_entries or settings.max_tree_entries

        entries: List[str] = []

        for item in sorted(project_root.rglob("*")):
            rel = item.relative_to(project_root)
            depth = len(rel.parts)

            if depth > max_depth:
                continue

            display = str(rel)
            if item.is_dir():
                display += "/"

            entries.append(display)

            if len(entries) >= max_entries:
                entries.append("... truncated ...")
                break

        return entries

    def read_text_raw(self, project_path: str, rel_path: str) -> str:
        path = self.resolve_file_path(project_path, rel_path)

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"Path is not a file: {path}")

        text = path.read_text(encoding="utf-8", errors="ignore")

        if len(text) > settings.max_file_chars:
            return text[: settings.max_file_chars] + "\n\n[TRUNCATED]"

        return text

    def write_text_raw(self, project_path: str, rel_path: str, content: str) -> str:
        path = self.resolve_file_path(project_path, rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def tools(self) -> List[Callable[..., Any]]:
        toolkit = self

        @tool
        def list_project_tree(project_path: str) -> str:
            """List the project directory tree inside the workspace."""
            return "\n".join(toolkit.list_tree_raw(project_path))

        @tool
        def read_project_file(project_path: str, rel_path: str) -> str:
            """Read a UTF-8 text file from a project folder."""
            return toolkit.read_text_raw(project_path, rel_path)

        @tool
        def write_project_file(project_path: str, rel_path: str, content: str) -> str:
            """Write a UTF-8 text file inside a project folder."""
            return toolkit.write_text_raw(project_path, rel_path, content)

        return [list_project_tree, read_project_file, write_project_file]