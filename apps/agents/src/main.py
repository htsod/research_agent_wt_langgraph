# apps/agents/src/main.py

from dotenv import load_dotenv

from apps.agents.src.graphs.research_workflow import ResearchWorkflow




def main() -> None:
    load_dotenv()

    workflow = ResearchWorkflow(project_path="workspace/projects/fermi_surface")
    graph = workflow.build()

    result = graph.invoke(
        {
            "project_path": "workspace/projects/fermi_surface",
            "user_request": (
                "Review the paper section by section. Use README.md for the main goal, "
                "use files reports/sections as supporting context, and write section-specific review in reports/summaries. After reviewing all sections, write a final summary report in reports/final_summary.md that synthesizes the section reviews and provides an overall assessment of the paper. Make sure to save all section reviews and the final summary report in the appropriate paths under the reports folder."
                "reports into the reports folder."
            ),
        }
    )

    print("\n=== FINAL MESSAGE ===\n")
    print(result.get("final_message", "No final message returned."))


if __name__ == "__main__":
    main()