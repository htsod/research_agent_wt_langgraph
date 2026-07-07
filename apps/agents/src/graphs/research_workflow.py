# apps/agents/src/graphs/research_workflow.py

from langgraph.graph import END, START, StateGraph

from apps.agents.src.registry.agent_registry import AgentRegistry
from apps.agents.src.schemas.state import ResearchWorkflowState
from apps.agents.src.toolkits.research import ResearchToolkit


class ResearchWorkflow:
    def __init__(self, project_path: str):
        self.registry = AgentRegistry()
        self.toolkit = ResearchToolkit()
        self.planner = self.registry.build_planner()
        self.researcher = self.registry.build_researcher(project_path=project_path)
        self.reviewer = self.registry.build_reviewer()

    def validate_project(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        try:
            project_root = self.toolkit.resolve_project_path(state["project_path"])
            return {
                "normalized_project_path": str(project_root),
                "agent_messages": [],
                "files_written": [],
                "section_outputs": [],
                "section_summaries": [],
                "rolling_context": "",
                "error": None,
            }
        except Exception as exc:
            return {
                "error": str(exc),
                "final_message": f"Project validation failed: {exc}",
            }


    def load_readme(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        if state.get("error"):
            return {}
        readme = self.toolkit.load_readme_raw(state["normalized_project_path"])
        return {"readme_content": readme}


    def load_sections(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        if state.get("error"):
            return {}
        sections = self.toolkit.discover_section_files_raw(state["normalized_project_path"])
        print("DISCOVERED SECTIONS:", sections)
        return {
            "section_queue": sections,
            "remaining_sections": sections,
        }

    def route_next_section(self, state: ResearchWorkflowState) -> str:
        print("DEBUG route_next_section")
        if state.get("error"):
            return "finalize"

        remaining = state.get("remaining_sections", [])
        if not remaining:
            return "compile_final_report"
        return "prepare_next_section"

    def prepare_next_section(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        print("DEBUG prepare_next_section")
        remaining = state.get("remaining_sections", [])
        if not remaining:
            return {}

        current = remaining[0]
        updated_remaining = remaining[1:]

        return {
            "current_section": current,
            "remaining_sections": updated_remaining,
        }

    def read_section_context(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        print("DEBUG read_section_context")
        if state.get("error"):
            return {}

        section = state["current_section"]
        project_path = state["normalized_project_path"]

        try:
            section_content = self.toolkit.read_text_raw(project_path, section["path"])
        except Exception:
            section_content = ""

        return {"current_section_content": section_content}

    def research_section(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        print("DEBUG research_section")
        if state.get("error"):
            return {}

        section = state["current_section"]
        section_name = section["name"]
        user_request = state.get("user_request", "")[:800]
        readme = state.get("readme_content", "")[:1200]
        rolling = state.get("rolling_context", "")[:1000]
        section_text = state.get("current_section_content", "")[:4500]

        prompt = f"""
User request:
{user_request}

README summary / project goal:
{readme}

Previous section summaries:
{rolling}

Current section:
{section_name}

Current section file path:
{section["path"]}

Existing section content:
{section_text}

Task:
Review and improve this section.

Return concise markdown with these headings:
# {section_name}
## Section Purpose
## Problems Found
## Corrections and Suggestions
## Improved Draft
Keep the improved draft under 600 words.
## Notes for Next Section
Keep the whole response under 2000 words.
""".strip()

        output = self.researcher.invoke(prompt)

        return {
                "current_section_output": output,
                "agent_messages": [],  # avoid carrying huge history
            }

    def review_section(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        if state.get("error"):
            return {}

        section = state["current_section"]

        prompt = f"""
Review this section analysis and rewrite.

Section:
{section["name"]}

Draft review output:
{state.get("current_section_output", "")}

Check for:
- clarity
- grounding in README
- useful corrections
- strong improved draft
- useful transition to next section

Return concise review notes only.
""".strip()

        review = self.reviewer.invoke(prompt)

        combined = (
            state.get("current_section_output", "")
            + "\n\n---\n\n## Reviewer Notes\n"
            + review
        )

        return {
            "current_section_output": combined,
            "agent_messages": state.get("agent_messages", [])
            + [{"agent": self.reviewer.name, "content": review}],
        }

    def write_section_report(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        print("DEBUG write_section_report")
        if state.get("error"):
            return {}

        section = state["current_section"]
        project_path = state["normalized_project_path"]

        path = self.toolkit.write_section_review_raw(
            project_path=project_path,
            section_index=section["index"],
            section_name=section["name"],
            content=state.get("current_section_output", ""),
        )

        outputs = state.get("section_outputs", []) + [
            {
                "section": section["name"],
                "path": path,
                "content": state.get("current_section_output", ""),
            }
        ]

        files_written = state.get("files_written", []) + [path]

        return {
            "current_section_report_path": path,
            "section_outputs": outputs,
            "files_written": files_written,
        }

    def update_rolling_context(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        print("DEBUG update_rolling_context")
        outputs = state.get("section_outputs", [])
        recent = outputs[-2:]  # keep only recent sections to control context size

        rolling_context = "\n\n".join(
            f"SECTION: {item['section']}\n---\n{item['content'][:2500]}"
            for item in recent
        )

        return {"rolling_context": rolling_context}

    def compile_final_report(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        print("DEBUG compile_final_report")
        if state.get("error"):
            return {}

        outputs = state.get("section_outputs", [])

        content = "# Compiled Research Review\n\n"
        content += "## Sections Processed\n\n"
        for item in outputs:
            content += f"- {item['section']}: `{item['path']}`\n"

        content += "\n## Combined Notes\n\n"
        for item in outputs:
            content += f"---\n\n# {item['section']}\n\n{item['content']}\n\n"

        path = self.toolkit.write_compiled_review_raw(
            state["normalized_project_path"],
            content,
        )

        return {
            "files_written": state.get("files_written", []) + [path],
        }

    def finalize(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        print("DEBUG finalize")
        if state.get("error"):
            return {"final_message": state.get("final_message", state["error"])}

        files = "\n".join(f"- {f}" for f in state.get("files_written", []))

        return {
            "final_message": f"""Section-by-section research workflow completed.

Files written:
{files}
"""
        }

    def build(self):
        graph = StateGraph(ResearchWorkflowState)

        graph.add_node("validate_project", self.validate_project)
        graph.add_node("load_readme", self.load_readme)
        # graph.add_node("scan_brief_tree", self.scan_brief_tree)
        # graph.add_node("select_brief_files", self.select_brief_files)
        graph.add_node("load_sections", self.load_sections)
        graph.add_node("prepare_next_section", self.prepare_next_section)
        graph.add_node("read_section_context", self.read_section_context)
        graph.add_node("research_section", self.research_section)
        graph.add_node("review_section", self.review_section)
        graph.add_node("write_section_report", self.write_section_report)
        graph.add_node("update_rolling_context", self.update_rolling_context)
        graph.add_node("compile_final_report", self.compile_final_report)
        graph.add_node("finalize", self.finalize)

        graph.add_edge(START, "validate_project")
        graph.add_edge("validate_project", "load_readme")
        # graph.add_edge("load_readme", "scan_brief_tree")
        # graph.add_edge("scan_brief_tree", "select_brief_files")
        # graph.add_edge("select_brief_files", "load_sections")
        graph.add_edge("load_readme", "load_sections")

        graph.add_conditional_edges(
            "load_sections",
            self.route_next_section,
            {
                "prepare_next_section": "prepare_next_section",
                "compile_final_report": "compile_final_report",
                "finalize": "finalize",
            },
        )

        graph.add_edge("prepare_next_section", "read_section_context")
        graph.add_edge("read_section_context", "research_section")
        graph.add_edge("research_section", "review_section")
        graph.add_edge("review_section", "write_section_report")
        graph.add_edge("write_section_report", "update_rolling_context")

        graph.add_conditional_edges(
            "update_rolling_context",
            self.route_next_section,
            {
                "prepare_next_section": "prepare_next_section",
                "compile_final_report": "compile_final_report",
                "finalize": "finalize",
            },
        )

        graph.add_edge("compile_final_report", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile()