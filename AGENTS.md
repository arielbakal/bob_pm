# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project: Nexus-PM Agent (LangGraph + Vertex AI)

Strategic AI orchestrator using LangGraph for managing workflows between business vision, Linear backlog, and GitHub activity.

## Critical Architecture Patterns

**LangGraph State Management:**
- Use `interrupt_before` on human_gate node - workflow MUST pause for approval before provisioning
- State persists via SqliteSaver checkpointer - agent "sleeps" during human approval
- AgentState TypedDict tracks: roadmap, GitHub context, Linear IDs, approval tokens
- Cyclic edges on monitor_loop trigger every 4 hours for blocker detection

**Vertex AI Integration:**
- Gemini 1.5 Pro handles 1-million-token codebase contexts
- Audio files (.mp3) passed DIRECTLY to Vertex AI for transcription (no preprocessing)
- Use native multimodal capabilities for meeting ingestion

**Human-in-the-Loop Pattern:**
- Workflow interrupts after generate_roadmap node
- Requires explicit "Approved" input from Lead Dev in Bob IDE
- Changes trigger re-generation, not continuation

## Required Credentials

```
GOOGLE_APPLICATION_CREDENTIALS  # Vertex AI (reasoning, audio, RAG)
LINEAR_API_KEY                  # Sprint management via GraphQL
GITHUB_TOKEN                    # Code analysis and PR tracking
```

## Custom MCP Tools

- `linear_graphql_executor` - Complex mutations/queries on Linear workspace
- `github_diff_analyzer` - Compares code against roadmap goals for progress %
- `vertex_audio_processor` - Speaker diarization for engineering meetings

## Node Execution Order

1. ingest_strategy → Multimodal meeting ingestion
2. scan_codebase → GitHub tree analysis + RAG
3. generate_roadmap → Draft weekly goals
4. **human_gate** → INTERRUPT for approval
5. provision_ops → Create Linear issues/cycles
6. monitor_loop → Cyclic GitHub vs Linear comparison

## Bob Mode Configuration

Define in `.bob/custom_modes.yaml` with:
- Mode slug: `nexus-pm`
- Required tools: `mcp`, `terminal`
- Access to all three MCP tools listed above