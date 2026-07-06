# apps/agents/src/main.py

from dotenv import load_dotenv

from apps.agents.src.graphs.research_workflow import ResearchWorkflow


def main() -> None:
    load_dotenv()

    workflow = ResearchWorkflow()
    graph = workflow.build()

    result = graph.invoke(
        {
            "project_path": "workspace/projects/demo_project",
            "user_request": (
                "Read the project files, research relevant external information, "
                "and write a research summary report for this project."
            ),
        }
    )

    print("\n=== FINAL MESSAGE ===\n")
    print(result.get("final_message", "No final message returned."))


if __name__ == "__main__":
    main()