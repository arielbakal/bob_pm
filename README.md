# Nexus-PM Agent

Strategic AI Orchestrator using LangGraph and Gemini AI to manage complex workflows between business vision, Linear backlog, and GitHub activity.

## Overview

Nexus-PM is a LangGraph-based agent that:
- 🎙️ Ingests strategy from meeting audio using Gemini multimodal
- 🔍 Analyzes codebase architecture via GitHub (1M token context)
- 📋 Generates weekly roadmaps with AI-powered issue extraction
- ✅ Implements human-in-the-loop approval gates
- 🎯 Provisions Linear issues and sprint cycles automatically
- 🔄 Monitors GitHub activity to detect blockers

## ✨ What's New

**Latest Updates:**
- ✅ **Gemini API Integration** - Simplified authentication with API key (no service account needed)
- ✅ **End-to-End Workflow** - Complete pipeline from audio to Linear issues
- ✅ **Roadmap Generation** - AI-powered conversion of meeting summaries to structured roadmaps
- ✅ **Audio Processing** - Native multimodal support with Gemini 2.5 Flash
- ✅ **No Warnings** - Clean output with suppressed deprecation warnings

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

✅ **Phase 1 Complete: Core Infrastructure**
- AgentState TypedDict schema
- Gemini API client with retry logic and multimodal support
- `ingest_strategy` node with native audio processing
- Project structure and dependencies

✅ **Phase 2 Complete: Linear Integration**
- Linear GraphQL client with retry logic
- `provision_ops` node for automatic issue/cycle creation
- Roadmap parsing with acceptance criteria extraction
- Batch issue creation support

✅ **Phase 3 Complete: AI Roadmap Generation**
- `generate_roadmap` node for intelligent issue extraction
- Automatic priority assignment (HIGH/MEDIUM/LOW)
- Acceptance criteria generation
- End-to-end workflow: Audio → Summary → Roadmap → Linear

✅ **Phase 4 Complete: GitHub Integration & StateGraph**
- `scan_codebase` node for repository analysis
- GitHub client with file tree extraction
- Enhanced `generate_roadmap` with technical context
- Complete LangGraph StateGraph with all nodes
- Human-in-the-loop approval gate with interrupt
- State persistence via SqliteSaver checkpointer

🎉 **COMPLETE: Full Workflow Operational**
- Audio → GitHub Analysis → Roadmap → **[APPROVAL]** → Linear Issues
- Pause/resume capability for human approval
- Rejection loop for roadmap regeneration
- Complete test suite with approval scenarios

🚧 **Optional Future Enhancements:**
- Implement `monitor_loop` node (cyclic blocker detection)
- MCP tool integration for advanced features
- Bob IDE custom mode configuration

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Linear API Key** (optional - for sprint management)
4. **GitHub Token** (optional - for code analysis)

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
# Edit .env and add your Gemini API key
```

Required in `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Optional (for full workflow):
```bash
LINEAR_API_KEY=your_linear_api_key_here
GITHUB_TOKEN=your_github_token_here
```

## Usage

### Quick Start: Complete Workflow Test

**Test the full LangGraph workflow with human-in-the-loop approval:**

```bash
python examples/test_complete_workflow.py
```

This complete StateGraph workflow will:
1. **Ingest Strategy** - Process meeting audio with Gemini
2. **Scan Codebase** - Analyze GitHub repository structure
3. **Generate Roadmap** - Create sprint roadmap with technical context
4. **Human Gate** - **PAUSE for approval** (simulated in test)
5. **Provision Ops** - Create Linear cycle and issues
6. Display results

**Total time:** ~30 seconds (includes GitHub API calls)

**Alternative: Simplified End-to-End Test (No GitHub/Approval):**

```bash
python examples/test_end_to_end.py
```

This simplified workflow will:
1. Process meeting audio with Gemini
2. Extract strategy summary
3. Generate structured roadmap with AI
4. Create Linear cycle and issues
5. Display results

**Total time:** ~15 seconds

### Test Individual Nodes

**Audio Processing:**
```bash
python examples/test_ingest_strategy.py
```

**Linear Provisioning:**
```bash
python examples/test_provision_ops.py
```

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
│   ├── state.py                 # AgentState TypedDict schema
│   ├── llm.py                   # Gemini API client with retry logic
│   ├── linear_client.py         # Linear GraphQL client
│   ├── github_client.py         # GitHub API client (NEW)
│   ├── graph.py                 # LangGraph StateGraph workflow (NEW)
│   └── nodes/
│       ├── __init__.py
│       ├── ingest_strategy.py   # Meeting audio ingestion node
│       ├── scan_codebase.py     # GitHub repository analysis node (NEW)
│       ├── generate_roadmap.py  # AI roadmap generation node (ENHANCED)
│       └── provision_ops.py     # Linear provisioning node
├── examples/
│   ├── test_ingest_strategy.py     # Audio processing test
│   ├── test_provision_ops.py       # Linear provisioning test
│   ├── test_end_to_end.py          # Simplified workflow test
│   └── test_complete_workflow.py   # Full StateGraph test (NEW)
├── .bob/
│   ├── rules-code/
│   │   └── AGENTS.md         # Code mode rules
│   ├── rules-advanced/
│   │   └── AGENTS.md         # Advanced mode rules
│   ├── rules-ask/
│   │   └── AGENTS.md         # Ask mode rules
│   └── rules-plan/
│       └── AGENTS.md         # Plan mode rules
├── AGENTS.md                    # Main agent guidance
├── blueprint.md                 # Original design blueprint
├── stategraph-plan.md           # Detailed implementation plan
├── IMPLEMENTATION_PLAN.md       # Final implementation plan (NEW)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options. Key variables:

**Required:**
- `GEMINI_API_KEY`: Gemini API key from Google AI Studio

**Optional:**
- `LINEAR_API_KEY`: Linear API key for sprint management
- `GITHUB_TOKEN`: GitHub personal access token
- `MONITOR_INTERVAL_HOURS`: Monitoring loop interval (default: 4)
- `PYTHONWARNINGS`: Set to `ignore::FutureWarning` to suppress warnings

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

Gemini processes meeting audio **directly** - no transcription service needed:

```python
from src.llm import get_gemini_client

gemini_client = get_gemini_client()
strategy = gemini_client.process_audio(
    audio_path="meeting.mp3",
    task_prompt="Extract action items and technical decisions"
)
```

### 2. AI-Powered Roadmap Generation

Convert meeting summaries to structured roadmaps automatically:

```python
from src.nodes import generate_roadmap_from_summary

roadmap = generate_roadmap_from_summary(
    strategy_summary="Build analytics feature...",
    cycle_name="Sprint 2026-W18"
)
# Returns formatted markdown with issues, priorities, and acceptance criteria
```

### 3. 1-Million Token Context

Gemini 2.5 Flash handles entire codebases in a single call:

```python
insights = gemini_client.analyze_codebase(
    codebase_context=full_repo_content,  # Up to 1M tokens
    analysis_prompt="Identify architectural patterns"
)
```

### 4. Linear GraphQL Integration

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

### 5. Roadmap Parsing

Automatic extraction of issues from markdown:

```python
from src.nodes.provision_ops import parse_roadmap

cycle_data, issues_data = parse_roadmap(roadmap_markdown)
# Returns structured data ready for Linear provisioning
```

### 6. Human-in-the-Loop Approval

Workflow pauses for approval using LangGraph interrupts:

```python
workflow = graph.compile(
    checkpointer=SqliteSaver("nexus_pm.db"),
    interrupt_before=["human_gate"]  # Pause here
)
```

### 7. State Persistence

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

## References

- [Blueprint](blueprint.md) - Original design document
- [Implementation Plan](stategraph-plan.md) - Detailed technical plan
- [Quick Start Guide](QUICKSTART.md) - 5-minute setup guide
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Linear API Documentation](https://developers.linear.app/)

## Recent Changes

**v0.4.0 (Current) - Complete LangGraph Implementation**
- ✅ **GitHub Integration** - Repository analysis with file tree extraction
- ✅ **Complete StateGraph** - Full LangGraph workflow with all nodes
- ✅ **Human-in-the-Loop** - Approval gate with interrupt and state persistence
- ✅ **Enhanced Roadmap** - Technical context from GitHub incorporated
- ✅ **Pause/Resume** - SqliteSaver checkpointer for workflow resumption
- ✅ **Rejection Loop** - Roadmap regeneration with feedback
- ✅ **Complete Tests** - Full workflow validation with approval scenarios

**v0.3.0**
- ✅ Complete end-to-end workflow implementation
- ✅ Gemini API integration with simple API key auth
- ✅ AI-powered roadmap generation from meeting summaries
- ✅ Native audio processing with Gemini 2.5 Flash
- ✅ Automatic priority assignment and acceptance criteria
- ✅ Clean output with warning suppression

**v0.2.0**
- ✅ Linear GraphQL integration
- ✅ Automatic issue and cycle provisioning
- ✅ Roadmap parsing with acceptance criteria

**v0.1.0**
- ✅ Initial project structure
- ✅ AgentState schema
- ✅ Audio ingestion node
