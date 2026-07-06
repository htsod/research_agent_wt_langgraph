# apps/agents/tests/initial_test.py

from dotenv import load_dotenv

from apps.agents.src.graphs.project_workflow import ProjectWorkflow


def main() -> None:
    load_dotenv()

    workflow = ProjectWorkflow()
    graph = workflow.build()

    result = graph.invoke(
        {
            "project_path": "workspace/projects/fermi_surface",
            "user_request": (
                "Analyze this project directory. Identify what exists, "
                "what is missing, and what I should do next."
            ),
        }
    )

    print("\n=== FINAL MESSAGE ===\n")
    print(result.get("final_message", "No final message returned."))


if __name__ == "__main__":
    main()