# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Plan Mode - Architectural Constraints

**LangGraph State Architecture:**
- AgentState TypedDict is the single source of truth across all nodes
- State must be immutable - nodes return new dicts, never mutate
- SqliteSaver checkpointer enables pause/resume across sessions
- Interrupt points must be declared at graph compilation, not runtime

**Workflow Design Constraints:**
- Human-in-the-loop gate MUST occur after roadmap generation, before provisioning
- Monitor loop uses cyclic edges - requires careful design to avoid infinite loops
- Node execution order is deterministic based on edge definitions
- Conditional edges require explicit routing functions

**Integration Architecture:**
- Vertex AI is the reasoning engine - all LLM calls go through it
- Linear is the operational system of record - GitHub is read-only for analysis
- MCP tools are the only interface to external services (no direct API calls)
- Audio processing happens in Vertex AI native multimodal, not separate service

**Scalability Considerations:**
- 1M token context window allows full codebase analysis in single call
- Cyclic monitoring every 4 hours prevents API rate limit issues
- State persistence enables long-running workflows across days/weeks
- GraphQL batching required for Linear operations at scale

**Critical Design Decisions:**
- Interrupt-based approval chosen over webhook callbacks (simpler state management)
- Direct audio to Vertex AI chosen over transcription service (fewer dependencies)
- Cyclic monitoring chosen over event-driven (more predictable, easier debugging)
- TypedDict state chosen over class-based (better LangGraph integration)

**Hidden Coupling:**
- Roadmap format must match Linear issue schema for provisioning
- GitHub analysis output must align with Linear status values
- Approval token format affects state resumption logic
- MCP tool schemas must match LangGraph tool calling conventions