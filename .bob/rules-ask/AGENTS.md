# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Ask Mode - Documentation Context

**Project Architecture Understanding:**
- This is a LangGraph StateGraph orchestrator, not a traditional web app
- "Nodes" are workflow phases, not UI components
- "Edges" define execution flow, including cyclic patterns for monitoring
- State persists across interrupts via SqliteSaver checkpointer

**Workflow Execution Model:**
- Human-in-the-loop approval happens at human_gate node
- Workflow pauses (interrupts) and resumes after approval
- Monitor loop runs cyclically every 4 hours (not event-driven)
- Each node returns updated AgentState dict

**Integration Points:**
- Vertex AI handles multimodal input (audio, text) and 1M token contexts
- Linear GraphQL API manages sprint operations (not REST)
- GitHub API provides code analysis, not version control operations
- Three custom MCP tools bridge these services

**Key Terminology:**
- "Roadmap" = weekly goals generated from strategy meetings
- "Provisioning" = creating Linear issues/cycles from approved roadmap
- "Blocker detection" = comparing GitHub activity vs Linear status
- "Codebase archaeology" = recursive GitHub tree analysis for context

**Non-Standard Patterns:**
- Audio files go directly to Vertex AI (no transcription service)
- State includes approval tokens, not just data
- Cyclic edges for monitoring (unusual in typical workflows)
- Interrupt-based approval (not callback-based)