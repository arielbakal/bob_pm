# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Advanced Mode - Implementation with MCP/Browser

**LangGraph Node Implementation:**
- Each node function MUST return updated AgentState dict
- Use `interrupt_before=["human_gate"]` in graph compilation
- SqliteSaver checkpointer required for state persistence between interrupts
- Cyclic edges defined with `add_edge(source, target)` for monitor_loop

**Vertex AI API Calls:**
- Use `ChatVertexAI(model_name="gemini-1.5-pro")` for reasoning
- Pass audio files directly as multimodal content - no preprocessing
- Set `max_output_tokens` high for codebase analysis (1M token context)
- Use streaming for long-running operations

**MCP Tool Integration:**
- Tools must be registered in `.bob/custom_modes.yaml` under nexus-pm mode
- `linear_graphql_executor` requires LINEAR_API_KEY in environment
- `github_diff_analyzer` needs GITHUB_TOKEN with repo scope
- `vertex_audio_processor` uses GOOGLE_APPLICATION_CREDENTIALS

**State Management:**
- AgentState TypedDict must include: roadmap, github_context, linear_ids, approval_token
- Never mutate state directly - always return new dict
- Checkpoint after each node execution for resumability

**Error Handling:**
- Wrap Vertex AI calls in retry logic (API rate limits)
- Linear GraphQL errors should not halt workflow - log and continue
- GitHub API failures should cache last known state

## MCP and Browser Tools Available

This mode has full access to MCP servers and browser automation for enhanced capabilities.