"""
Nexus-PM Agent - LangGraph + Vertex AI orchestrator for project management.
"""

__version__ = "0.1.0"

from src.state import AgentState, create_initial_state, update_state
from src.llm import VertexAIClient, get_vertex_client
from src.linear_client import LinearClient, get_linear_client

__all__ = [
    "AgentState",
    "create_initial_state",
    "update_state",
    "VertexAIClient",
    "get_vertex_client",
    "LinearClient",
    "get_linear_client",
]

# Made with Bob
