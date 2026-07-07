# Research Agent with LangGraph

This project is a local multi-agent workflow for research and document writing using LangGraph, LangChain, and a local LLM backend.

## Overview

The goal of this project is to build a scalable agentic workflow that can work on files inside a project directory. The system is designed so that different agents can perform different roles, such as planning, research, reviewing, and writing, while sharing a common workspace and selected tools.

The current workflow focuses on section-by-section research writing. It reads the project `README.md` for the overall goal, uses files in the `brief/` folder as supporting context, and processes section files such as `Abstract.md` and `Introduction.md` one at a time. For each section, the workflow generates a review or improved draft and writes outputs into the project reports folder.

## Features

* Local LLM inference through `llama.cpp`
* LangGraph-based workflow orchestration
* LangChain-based agent and tool integration
* Modular toolkit and agent architecture
* Shared workspace for project files
* Section-by-section research workflow
* Rolling context between sections
* Generated outputs written into project report folders

## Project Structure

```text
apps/agents/src/
├─ agents/        # agent role definitions
├─ config/        # settings and environment config
├─ graphs/        # LangGraph workflows
├─ models/        # model client factory
├─ registry/      # agent and toolkit registry
├─ schemas/       # shared state schemas
└─ toolkits/      # reusable tools and tool groups

workspace/projects/
└─ <project_name>/
   ├─ README.md
   ├─ brief/
   ├─ reports/
   └─ ...
```

## Current Workflow

The main research workflow currently does the following:

1. Validate the project path
2. Read the project `README.md`
3. Inspect the `brief/` folder for supporting files
4. Discover section files
5. Process each section one at a time
6. Generate section output and review notes
7. Write reports and compiled outputs

## Requirements

* Python 3.11+
* LangChain
* LangGraph
* `llama.cpp` server running locally
* Environment variables configured in `.env`

## Example `.env`

```env
LLM_BASE_URL=http://127.0.0.1:8080/v1
LLM_MODEL=local-model
LLM_TEMPERATURE=0.2
```

## Installation

Create and activate a virtual environment, then install dependencies:

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


## Running the Project

From the project root:

```bash
PYTHONPATH=. python -m apps.agents.src.main
```

## Status

This project is under active development. The architecture is being refactored toward a more scalable multi-agent design with specialized toolkits, explicit workflow control, and section-aware research pipelines.

## Future Work

* More robust section discovery
* Better context control for long documents
* Explicit summary generation between sections
* Specialized agents for different paper sections
* Improved web research integration
* Support for supervisor-style multi-agent routing

## License

Add your preferred license here.
