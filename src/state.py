"""
AgentState schema for Nexus-PM orchestrator.
Defines the immutable state container tracked across all LangGraph nodes.
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


class AgentState(TypedDict):
    """
    Immutable state container for the Nexus-PM orchestrator.
    Each node returns a new dict with updated fields.
    
    State is persisted via SqliteSaver checkpointer to enable:
    - Human-in-the-loop approval interrupts
    - Workflow resumption after approval
    - Cyclic monitoring across multiple days
    """
    
    # ===== Strategy & Planning =====
    meeting_audio_path: Optional[str]
    """Path to .mp3 meeting file for multimodal ingestion"""
    
    strategy_summary: Optional[str]
    """Extracted action items and decisions from meeting audio"""
    
    # ===== Technical Context =====
    github_context: Optional[Dict[str, Any]]
    """Raw GitHub repository structure: file tree, patterns, architecture"""
    
    codebase_insights: Optional[str]
    """RAG-generated technical summary from Vertex AI (1M token context)"""
    
    # ===== Roadmap & Approval =====
    roadmap: Optional[str]
    """Generated ROADMAP.md content with weekly goals and issue breakdown"""
    
    roadmap_version: int
    """Increments on each regeneration (starts at 1)"""
    
    approval_status: str
    """Current approval state: 'pending' | 'approved' | 'rejected'"""
    
    approval_token: Optional[str]
    """Unique token for workflow resumption after interrupt"""
    
    approval_feedback: Optional[str]
    """Lead Dev's change requests if roadmap was rejected"""
    
    # ===== Linear Integration =====
    linear_cycle_id: Optional[str]
    """Created sprint cycle ID in Linear"""
    
    linear_issue_ids: List[str]
    """List of created Linear issue IDs for tracking"""
    
    provisioning_status: str
    """Status of Linear provisioning: 'not_started' | 'in_progress' | 'complete'"""
    
    # ===== Monitoring =====
    monitor_iteration: int
    """Tracks cyclic loop count (increments every 4 hours)"""
    
    last_monitor_time: Optional[datetime]
    """Timestamp of last monitoring check"""
    
    blockers_detected: List[Dict[str, Any]]
    """Issues with no Git activity (potential blockers)"""
    
    # ===== Metadata =====
    workflow_id: str
    """Unique workflow instance ID for checkpointer"""
    
    started_at: datetime
    """Workflow start timestamp"""
    
    last_updated: datetime
    """Last state update timestamp"""


def create_initial_state(
    workflow_id: str,
    meeting_audio_path: Optional[str] = None
) -> AgentState:
    """
    Create initial state for a new workflow instance.
    
    Args:
        workflow_id: Unique identifier for this workflow
        meeting_audio_path: Optional path to meeting audio file
        
    Returns:
        AgentState with default values
    """
    now = datetime.utcnow()
    
    return AgentState(
        # Strategy & Planning
        meeting_audio_path=meeting_audio_path,
        strategy_summary=None,
        
        # Technical Context
        github_context=None,
        codebase_insights=None,
        
        # Roadmap & Approval
        roadmap=None,
        roadmap_version=0,
        approval_status="pending",
        approval_token=None,
        approval_feedback=None,
        
        # Linear Integration
        linear_cycle_id=None,
        linear_issue_ids=[],
        provisioning_status="not_started",
        
        # Monitoring
        monitor_iteration=0,
        last_monitor_time=None,
        blockers_detected=[],
        
        # Metadata
        workflow_id=workflow_id,
        started_at=now,
        last_updated=now
    )


def update_state(
    current_state: AgentState,
    **updates: Any
) -> AgentState:
    """
    Create new state dict with updates (immutable pattern).
    Automatically updates last_updated timestamp.
    
    Args:
        current_state: Current state dict
        **updates: Fields to update
        
    Returns:
        New AgentState dict with updates applied
    """
    new_state = current_state.copy()
    new_state.update(updates)
    new_state["last_updated"] = datetime.utcnow()
    return new_state

# Made with Bob
