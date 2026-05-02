# Nexus-PM Agent

Strategic AI Orchestrator using LangGraph and Vertex AI to manage complex workflows between business vision, Linear backlog, and GitHub activity.

## Overview

Nexus-PM is a LangGraph-based agent that:
- 🎙️ Ingests strategy from meeting audio using Vertex AI multimodal
- 🔍 Analyzes codebase architecture via GitHub (1M token context)
- 📋 Generates weekly roadmaps with technical acceptance criteria
- ✅ Implements human-in-the-loop approval gates
- 🎯 Provisions Linear issues and sprint cycles automatically
- 🔄 Monitors GitHub activity to detect blockers

## Architecture

```
┌─────────────────┐
│ Meeting Audio   │
│   (.mp3)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│ ingest_strategy │────▶│ scan_codebase│
│  (Vertex AI)    │     │   (GitHub)   │
└─────────────────┘     └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │generate_     │
                        │  roadmap     │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ human_gate   │◀── INTERRUPT
                        │  (Approval)  │
                        └──────┬───────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              [Approved]            [Rejected]
                    │                     │
                    ▼                     │
            ┌──────────────┐              │
            │provision_ops │              │
            │   (Linear)   │              │
            └──────┬───────┘              │
                   │                      │
                   ▼                      │
            ┌──────────────┐              │
            │monitor_loop  │              │
            │  (Cyclic)    │◀─────────────┘
            └──────────────┘
```

## Current Implementation Status

✅ **Phase 1 Complete:**
- AgentState TypedDict schema
- Vertex AI LLM client with retry logic
- `ingest_strategy` node with multimodal audio processing
- Project structure and dependencies

✅ **Phase 2 Complete:**
- Linear GraphQL client with retry logic
- `provision_ops` node for automatic issue/cycle creation
- Roadmap parsing with acceptance criteria extraction
- Batch issue creation support

🚧 **Next Steps:**
- Implement `scan_codebase` node (GitHub analysis)
- Implement `generate_roadmap` node (AI roadmap generation)
- Configure human-in-the-loop interrupt
- Implement `monitor_loop` node (cyclic blocker detection)
- Full LangGraph workflow integration

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Google Cloud Project** with Vertex AI API enabled
3. **Service Account** with Vertex AI permissions
4. **Linear API Key** (for sprint management)
5. **GitHub Token** (for code analysis)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd nexus-pm
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure credentials:**
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

5. **Set up Google Cloud credentials:**
```bash
# Download service account key from GCP Console
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
export GOOGLE_CLOUD_PROJECT=your-project-id
```

## Usage

### Test Ingest Strategy Node

```bash
python examples/test_ingest_strategy.py
```

This will:
1. Load a meeting audio file
2. Process it with Vertex AI multimodal
3. Extract action items and strategic goals
4. Display the extracted strategy summary

### Test Linear Provisioning Node

```bash
python examples/test_provision_ops.py
```

This will:
1. Create a sample approved roadmap
2. Parse roadmap into cycle and issue data
3. Create sprint cycle in Linear
4. Create issues with acceptance criteria
5. Display created Linear IDs

### Python API

**Ingest Strategy:**
```python
from src.state import create_initial_state
from src.nodes import ingest_strategy

# Create initial state
state = create_initial_state(
    workflow_id="weekly-planning-2024-w03",
    meeting_audio_path="meetings/planning.mp3"
)

# Execute ingest_strategy node
updated_state = ingest_strategy(state)

# Access extracted strategy
print(updated_state["strategy_summary"])
```

**Provision Linear Operations:**
```python
from src.state import create_initial_state, update_state
from src.nodes import provision_ops

# Create state with approved roadmap
state = create_initial_state(workflow_id="sprint-2024-w03")
state = update_state(
    state,
    roadmap="# Sprint 2024-W03...",  # Your roadmap markdown
    approval_status="approved"
)

# Execute provision_ops node
updated_state = provision_ops(state)

# Access created Linear IDs
print(f"Cycle: {updated_state['linear_cycle_id']}")
print(f"Issues: {updated_state['linear_issue_ids']}")
```

## Project Structure

```
nexus-pm/
├── src/
│   ├── __init__.py
│   ├── state.py              # AgentState TypedDict schema
│   ├── llm.py                # Vertex AI client with retry logic
│   ├── linear_client.py      # Linear GraphQL client
│   └── nodes/
│       ├── __init__.py
│       ├── ingest_strategy.py  # Meeting audio ingestion node
│       └── provision_ops.py    # Linear provisioning node
├── examples/
│   ├── test_ingest_strategy.py  # Ingest strategy example
│   └── test_provision_ops.py    # Linear provisioning example
├── .bob/
│   ├── rules-code/
│   │   └── AGENTS.md         # Code mode rules
│   ├── rules-advanced/
│   │   └── AGENTS.md         # Advanced mode rules
│   ├── rules-ask/
│   │   └── AGENTS.md         # Ask mode rules
│   └── rules-plan/
│       └── AGENTS.md         # Plan mode rules
├── AGENTS.md                 # Main agent guidance
├── blueprint.md              # Original design blueprint
├── stategraph-plan.md        # Detailed implementation plan
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options. Key variables:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account key
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `LINEAR_API_KEY`: Linear API key for sprint management
- `GITHUB_TOKEN`: GitHub personal access token
- `MONITOR_INTERVAL_HOURS`: Monitoring loop interval (default: 4)

### Bob Mode Configuration

To use with Bob IDE, configure `.bob/custom_modes.yaml`:

```yaml
modes:
  - slug: nexus-pm
    name: "Nexus PM"
    tools:
      - mcp
      - terminal
    mcp_tools:
      - linear_graphql_executor
      - github_diff_analyzer
      - vertex_audio_processor
```

## Key Features

### 1. Multimodal Audio Processing

Vertex AI processes meeting audio **directly** - no transcription service needed:

```python
vertex_client = get_vertex_client()
strategy = vertex_client.process_audio(
    audio_path="meeting.mp3",
    task_prompt="Extract action items and technical decisions"
)
```

### 2. 1-Million Token Context

Gemini 1.5 Pro handles entire codebases in a single call:

```python
insights = vertex_client.analyze_codebase(
    codebase_context=full_repo_content,  # Up to 1M tokens
    analysis_prompt="Identify architectural patterns"
)
```

### 3. Linear GraphQL Integration

Direct GraphQL operations with automatic retry:

```python
from src.linear_client import get_linear_client

linear = get_linear_client()

# Create sprint cycle
cycle = linear.create_cycle(
    name="Sprint 2024-W03",
    starts_at=datetime(2024, 1, 15),
    ends_at=datetime(2024, 1, 22),
    team_id="team_id"
)

# Batch create issues
issues = linear.batch_create_issues(
    issues=[
        {"title": "Implement auth", "description": "...", "priority": 2},
        {"title": "Refactor DB", "description": "...", "priority": 3}
    ],
    team_id="team_id",
    cycle_id=cycle["id"]
)
```

### 4. Roadmap Parsing

Automatic extraction of issues from markdown:

```python
from src.nodes.provision_ops import parse_roadmap

cycle_data, issues_data = parse_roadmap(roadmap_markdown)
# Returns structured data ready for Linear provisioning
```

### 5. Human-in-the-Loop Approval

Workflow pauses for approval using LangGraph interrupts:

```python
workflow = graph.compile(
    checkpointer=SqliteSaver("nexus_pm.db"),
    interrupt_before=["human_gate"]  # Pause here
)
```

### 6. State Persistence

SqliteSaver enables pause/resume across sessions:

```python
# Workflow pauses at human_gate
# Later, resume with approval:
workflow.stream(
    {"approval_status": "approved"},
    config={"configurable": {"thread_id": workflow_id}}
)
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black src/ examples/
ruff check src/ examples/
```

### Type Checking

```bash
mypy src/
```

## Troubleshooting

### "GOOGLE_APPLICATION_CREDENTIALS not set"

Set the environment variable to your service account key:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### "Import langchain_google_vertexai could not be resolved"

Install dependencies:
```bash
pip install -r requirements.txt
```

### "Audio file not found"

Ensure the audio file path in your code matches an actual file:
```python
meeting_audio_path="examples/sample_meeting.mp3"  # Must exist
```

## Contributing

1. Follow the implementation plan in `stategraph-plan.md`
2. Read agent guidance in `AGENTS.md` and `.bob/rules-*/AGENTS.md`
3. Maintain immutable state pattern (never mutate, always return new dict)
4. Use retry logic for all external API calls
5. Add tests for new nodes

## License

[Your License Here]

## References

- [Blueprint](blueprint.md) - Original design document
- [Implementation Plan](stategraph-plan.md) - Detailed technical plan
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)