"""
LangGraph StateGraph for Nexus-PM orchestrator.
Defines workflow with human-in-the-loop approval checkpoint.
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.state import AgentState
from src.nodes.ingest_strategy import ingest_strategy
from src.nodes.scan_codebase import scan_codebase
from src.nodes.generate_roadmap import generate_roadmap
from src.nodes.provision_ops import provision_ops

logger = logging.getLogger(__name__)


def human_gate(state: AgentState) -> AgentState:
    """
    Human approval checkpoint - workflow interrupts here.
    
    This node doesn't execute logic - it's a marker for interrupt_before.
    External process (Bob IDE) will:
    1. Display roadmap to Lead Dev
    2. Collect approval/rejection + feedback
    3. Resume workflow with updated state
    """
    logger.info("Human gate checkpoint - waiting for approval")
    return state


def route_approval(state: AgentState) -> Literal["provision_ops", "generate_roadmap"]:
    """
    Route based on approval status after human_gate.
    
    Returns:
        "provision_ops" if approved
        "generate_roadmap" if rejected (regenerate with feedback)
    """
    approval_status = state.get("approval_status", "pending")
    
    if approval_status == "approved":
        logger.info("Roadmap approved - proceeding to provisioning")
        return "provision_ops"
    elif approval_status == "rejected":
        logger.info("Roadmap rejected - regenerating with feedback")
        return "generate_roadmap"
    else:
        # Default to regeneration if status unclear
        logger.warning(f"Unclear approval status: {approval_status}, defaulting to regeneration")
        return "generate_roadmap"


def create_workflow(checkpointer_path: str = "nexus_pm.db") -> StateGraph:
    """
    Create complete LangGraph workflow with all nodes and edges.
    
    Workflow:
    1. ingest_strategy → Process meeting audio
    2. scan_codebase → Analyze GitHub repository
    3. generate_roadmap → Create sprint roadmap
    4. human_gate → INTERRUPT for approval
    5. route_approval → Conditional routing
       - If approved → provision_ops
       - If rejected → generate_roadmap (loop)
    6. provision_ops → Create Linear issues
    
    Args:
        checkpointer_path: Path to SQLite database for state persistence
        
    Returns:
        Compiled StateGraph workflow
    """
    logger.info("Creating Nexus-PM StateGraph workflow")
    
    # Initialize graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("ingest_strategy", ingest_strategy)
    workflow.add_node("scan_codebase", scan_codebase)
    workflow.add_node("generate_roadmap", generate_roadmap)
    workflow.add_node("human_gate", human_gate)
    workflow.add_node("provision_ops", provision_ops)
    
    # Add edges (sequential flow)
    workflow.add_edge("ingest_strategy", "scan_codebase")
    workflow.add_edge("scan_codebase", "generate_roadmap")
    workflow.add_edge("generate_roadmap", "human_gate")
    
    # Add conditional edge after human_gate
    workflow.add_conditional_edges(
        "human_gate",
        route_approval,
        {
            "approved": "provision_ops",
            "rejected": "generate_roadmap"
        }
    )
    
    # Add final edge
    workflow.add_edge("provision_ops", END)
    
    # Set entry point
    workflow.set_entry_point("ingest_strategy")
    
    # Initialize checkpointer for state persistence
    checkpointer = SqliteSaver.from_conn_string(checkpointer_path)
    
    # Compile with interrupt before human_gate
    compiled_workflow = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_gate"]  # Pause here for approval
    )
    
    logger.info("StateGraph compiled with human-in-the-loop interrupt")
    
    return compiled_workflow


def run_workflow(
    workflow: StateGraph,
    initial_state: AgentState,
    workflow_id: str
) -> AgentState:
    """
    Run workflow until interrupt or completion.
    
    Args:
        workflow: Compiled StateGraph
        initial_state: Starting state
        workflow_id: Unique workflow instance ID
        
    Returns:
        Final state after execution
    """
    config = {"configurable": {"thread_id": workflow_id}}
    
    logger.info(f"Starting workflow execution: {workflow_id}")
    
    # Run until interrupt
    for event in workflow.stream(initial_state, config):
        logger.info(f"Event: {list(event.keys())}")
    
    # Get current state
    final_state = workflow.get_state(config)
    
    logger.info(f"Workflow paused at: {final_state.next}")
    
    return final_state.values


def resume_workflow(
    workflow: StateGraph,
    workflow_id: str,
    approval_status: str,
    approval_feedback: str = None
) -> AgentState:
    """
    Resume workflow after human approval.
    
    Args:
        workflow: Compiled StateGraph
        workflow_id: Workflow instance ID
        approval_status: "approved" or "rejected"
        approval_feedback: Optional feedback if rejected
        
    Returns:
        Final state after completion
    """
    config = {"configurable": {"thread_id": workflow_id}}
    
    logger.info(f"Resuming workflow {workflow_id} with status: {approval_status}")
    
    # Update state with approval
    updated_state = {
        "approval_status": approval_status,
        "approval_feedback": approval_feedback
    }
    
    # Resume from checkpoint
    for event in workflow.stream(updated_state, config):
        logger.info(f"Event: {list(event.keys())}")
    
    # Get final state
    final_state = workflow.get_state(config)
    
    logger.info("Workflow completed")
    
    return final_state.values

# Made with Bob