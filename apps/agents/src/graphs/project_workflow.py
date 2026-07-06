# apps/agents/src/graphs/project_workflow.py

from pathlib import Path
from typing import Literal

from langgraph.graph import END, START, StateGraph

from apps.agents.src.registry.agent_registry import AgentRegistry
from apps.agents.src.schemas.state import ProjectWorkflowState
from apps.agents.src.toolkits.project_analysis import ProjectAnalysisToolkit


class ProjectWorkflow:
    """Multi-agent project workflow."""

    def __init__(self):
        self.registry = AgentRegistry()
        self.analysis_toolkit = ProjectAnalysisToolkit()

        self.planner = self.registry.build_planner()
        self.analyst = self.registry.build_analyst()
        self.reviewer = self.registry.build_reviewer()

    def validate_project(self, state: ProjectWorkflowState) -> ProjectWorkflowState:
        try:
            project_root = self.analysis_toolkit.resolve_project_path(state["project_path"])
            return {
                "normalized_project_path": str(project_root),
                "agent_messages": [],
                "files_written": [],
                "error": None,
            }
        except Exception as exc:
            return {
                "error": str(exc),
                "final_message": f"Project validation failed: {exc}",
            }

    def planning_node(self, state: ProjectWorkflowState) -> ProjectWorkflowState:
        if state.get("error"):
            return {}

        prompt = f"""
User request:
{state["user_request"]}

Project path:
{state["normalized_project_path"]}

Create a short project analysis plan.
""".strip()

        plan = self.planner.invoke(prompt)

        return {
            "plan": plan,
            "agent_messages": state.get("agent_messages", [])
            + [{"agent": self.planner.name, "content": plan}],
        }

    def discovery_node(self, state: ProjectWorkflowState) -> ProjectWorkflowState:
        if state.get("error"):
            return {}

        project_path = state["normalized_project_path"]

        tree_summary = self.analysis_toolkit.list_tree_raw(project_path)
        key_files = self.analysis_toolkit.select_key_files_raw(project_path)

        documents = []
        for rel_path in key_files:
            try:
                content = self.analysis_toolkit.read_text_raw(project_path, rel_path)
                documents.append({"path": rel_path, "content": content})
            except Exception as exc:
                documents.append(
                    {
                        "path": rel_path,
                        "content": f"[ERROR READING FILE: {exc}]",
                    }
                )

        return {
            "tree_summary": tree_summary,
            "key_files": key_files,
            "documents": documents,
        }

    def analyst_node(self, state: ProjectWorkflowState) -> ProjectWorkflowState:
        if state.get("error"):
            return {}

        tree_text = "\n".join(f"- {x}" for x in state.get("tree_summary", []))
        docs_text = "\n\n".join(
            f"FILE: {doc['path']}\n---\n{doc['content']}"
            for doc in state.get("documents", [])
        )

        prompt = f"""
User request:
{state["user_request"]}

Planner's plan:
{state.get("plan", "")}

Project path:
{state["normalized_project_path"]}

Directory tree:
{tree_text}

Documents reviewed:
{docs_text}

Now produce a project assessment with:
1. Summary
2. Existing pieces
3. Missing pieces
4. Risks / unknowns
5. Recommended next steps
""".strip()

        analysis = self.analyst.invoke(prompt)

        return {
            "analysis": analysis,
            "agent_messages": state.get("agent_messages", [])
            + [{"agent": self.analyst.name, "content": analysis}],
        }

    def reviewer_node(self, state: ProjectWorkflowState) -> ProjectWorkflowState:
        if state.get("error"):
            return {}

        prompt = f"""
Review this project analysis.

User request:
{state["user_request"]}

Analysis:
{state.get("analysis", "")}

Check for:
- clarity
- groundedness
- missing obvious sections
- practical usefulness

Return a concise review.
""".strip()

        review = self.reviewer.invoke(prompt)

        return {
            "review": review,
            "agent_messages": state.get("agent_messages", [])
            + [{"agent": self.reviewer.name, "content": review}],
        }

    def write_outputs_node(self, state: ProjectWorkflowState) -> ProjectWorkflowState:
        if state.get("error"):
            return {}

        project_path = state["normalized_project_path"]

        report = f"""# Initial Assessment

## User Request

{state["user_request"]}

## Plan

{state.get("plan", "")}

## Analysis

{state.get("analysis", "")}

## Review

{state.get("review", "")}

## Files Reviewed

{chr(10).join(f"- {f}" for f in state.get("key_files", [])) or "- None"}
"""

        report_path = self.analysis_toolkit.write_assessment_raw(
            project_path=project_path,
            content=report,
        )

        next_steps = f"""# Next Steps

This file was generated from the project analysis workflow.

## Source

See `reports/initial_assessment.md`.

## Recommended Action

Use the assessment report to decide the next implementation, research, or documentation workflow.
"""

        next_steps_path = self.analysis_toolkit.write_next_steps_raw(
            project_path=project_path,
            content=next_steps,
        )

        return {
            "files_written": state.get("files_written", [])
            + [report_path, next_steps_path],
        }

    def finalize_node(self, state: ProjectWorkflowState) -> ProjectWorkflowState:
        if state.get("error"):
            return {"final_message": state.get("final_message", state["error"])}

        files = "\n".join(f"- {f}" for f in state.get("files_written", []))

        return {
            "final_message": f"""Project workflow completed.

Files written:
{files}

Summary:
{state.get("analysis", "")[:1000]}
"""
        }

    def should_continue_after_validation(
        self,
        state: ProjectWorkflowState,
    ) -> Literal["planning", "finalize"]:
        if state.get("error"):
            return "finalize"
        return "planning"

    def build(self):
        graph = StateGraph(ProjectWorkflowState)

        graph.add_node("validate", self.validate_project)
        graph.add_node("planning", self.planning_node)
        graph.add_node("discovery", self.discovery_node)
        graph.add_node("analyst", self.analyst_node)
        graph.add_node("reviewer", self.reviewer_node)
        graph.add_node("write_outputs", self.write_outputs_node)
        graph.add_node("finalize", self.finalize_node)

        graph.add_edge(START, "validate")

        graph.add_conditional_edges(
            "validate",
            self.should_continue_after_validation,
            {
                "planning": "planning",
                "finalize": "finalize",
            },
        )

        graph.add_edge("planning", "discovery")
        graph.add_edge("discovery", "analyst")
        graph.add_edge("analyst", "reviewer")
        graph.add_edge("reviewer", "write_outputs")
        graph.add_edge("write_outputs", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile()