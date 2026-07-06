# apps/agents/src/schemas/state.py

from typing import Any, Dict, List, Optional, TypedDict


class AgentMessage(TypedDict):
    agent: str
    content: str

class ResearchDocument(TypedDict):
    path: str
    content: str


class SectionItem(TypedDict):
    name: str
    path: str
    index: int


class SectionOutput(TypedDict):
    section: str
    path: str
    content: str


class ResearchWorkflowState(TypedDict, total=False):
    # user input
    user_request: str
    project_path: str

    # validated / normalized project info
    normalized_project_path: str

    # top-level project context
    readme_content: str

    # brief discovery + selected supporting context
    brief_tree: List[str]
    selected_brief_files: List[str]
    brief_documents: List[ResearchDocument]

    # section discovery and loop state
    section_queue: List[SectionItem]
    remaining_sections: List[SectionItem]
    current_section: SectionItem
    current_section_content: str

    # section summaries
    current_section_summary_path: str
    section_summaries: List[Dict[str, str]]

    # rolling context from prior generated sections
    rolling_context: str

    # current section working outputs
    current_section_output: str
    current_section_report_path: str

    # accumulated outputs
    section_outputs: List[SectionOutput]
    files_written: List[str]

    # runtime / trace
    agent_messages: List[AgentMessage]

    # final response
    final_message: str

    # error handling
    error: Optional[str]


class ProjectWorkflowState(TypedDict, total=False):
    user_request: str
    project_path: str
    normalized_project_path: str

    tree_summary: List[str]
    key_files: List[str]
    documents: List[Dict[str, str]]

    plan: str
    analysis: str
    review: str

    existing_pieces: List[str]
    missing_pieces: List[str]
    risks: List[str]
    recommended_next_steps: List[str]

    files_written: List[str]
    agent_messages: List[AgentMessage]

    next_agent: str
    final_message: str
    error: Optional[str]