"""
Ingest Strategy Node - Multimodal meeting ingestion via Gemini API.
Extracts action items and technical decisions from audio recordings.
"""

import logging
from typing import Dict, Any
from src.state import AgentState, update_state
from src.llm import get_gemini_client

logger = logging.getLogger(__name__)


def ingest_strategy(state: AgentState) -> AgentState:
    """
    Node 1: Multimodal ingestion of meeting audio/PDFs via Gemini API.
    
    This node:
    1. Reads meeting audio file from state['meeting_audio_path']
    2. Passes audio DIRECTLY to Gemini (no preprocessing)
    3. Extracts action items, technical decisions, and strategic goals
    4. Updates state with strategy_summary
    
    Args:
        state: Current AgentState with meeting_audio_path populated
        
    Returns:
        Updated AgentState with strategy_summary
        
    Raises:
        ValueError: If meeting_audio_path is not provided
        Exception: If Gemini API processing fails after retries
    """
    logger.info("Starting strategy ingestion from meeting audio")
    
    # Validate input
    audio_path = state.get("meeting_audio_path")
    if not audio_path:
        raise ValueError(
            "meeting_audio_path must be provided in state for ingest_strategy node"
        )
    
    logger.info(f"Processing audio file: {audio_path}")
    
    # Get Gemini client (singleton with retry logic)
    gemini_client = get_gemini_client(
        model_name="gemini-2.5-flash",
        max_output_tokens=8192,  # High limit for detailed extraction
        temperature=0.3  # Lower temperature for factual extraction
    )
    
    # System prompt for strategic extraction
    system_prompt = """You are an AI assistant helping engineering teams extract actionable insights from planning meetings.

Your task is to analyze meeting audio and extract:
1. **Action Items**: Specific tasks or deliverables mentioned
2. **Technical Decisions**: Architecture choices, technology selections, design patterns
3. **Strategic Goals**: High-level objectives for the upcoming sprint/week
4. **Blockers/Concerns**: Any risks or dependencies mentioned

Format your response as structured markdown with clear sections."""
    
    # Task prompt for audio processing
    task_prompt = """Analyze this engineering planning meeting and extract:

## Action Items
List all specific tasks, deliverables, or commitments made during the meeting.
Include who is responsible if mentioned.

## Technical Decisions
Document any architectural choices, technology selections, or design patterns discussed.

## Strategic Goals
Identify the high-level objectives for the upcoming sprint or project phase.

## Blockers & Concerns
Note any risks, dependencies, or concerns raised by the team.

## Key Takeaways
Summarize the 3-5 most important points from the meeting.

Be concise but comprehensive. Focus on actionable information."""
    
    try:
        # Process audio with Gemini multimodal
        # This uses native audio processing - no transcription service needed
        strategy_summary = gemini_client.process_audio(
            audio_path=audio_path,
            task_prompt=task_prompt,
            system_prompt=system_prompt
        )
        
        logger.info("Successfully extracted strategy summary from audio")
        logger.debug(f"Summary length: {len(strategy_summary)} characters")
        
        # Update state with extracted summary
        return update_state(
            state,
            strategy_summary=strategy_summary
        )
        
    except FileNotFoundError:
        logger.error(f"Audio file not found: {audio_path}")
        raise ValueError(f"Audio file not found: {audio_path}")
        
    except Exception as e:
        logger.error(f"Failed to process audio after retries: {e}")
        raise Exception(f"Gemini API audio processing failed: {e}")


def ingest_strategy_with_mcp(state: AgentState) -> AgentState:
    """
    Alternative implementation using MCP vertex_audio_processor tool.
    Provides speaker diarization for multi-speaker meetings.
    
    Args:
        state: Current AgentState with meeting_audio_path populated
        
    Returns:
        Updated AgentState with strategy_summary including speaker attribution
        
    Note:
        This requires the vertex_audio_processor MCP tool to be configured
        in .bob/custom_modes.yaml under the nexus-pm mode.
    """
    logger.info("Starting strategy ingestion with MCP speaker diarization")
    
    audio_path = state.get("meeting_audio_path")
    if not audio_path:
        raise ValueError("meeting_audio_path required for ingest_strategy_with_mcp")
    
    # TODO: Implement MCP tool call when MCP integration is ready
    # This would use the vertex_audio_processor tool for speaker diarization
    # Format:
    # {
    #     "audio_path": audio_path,
    #     "task": "extract_action_items",
    #     "enable_diarization": True
    # }
    
    # For now, fall back to standard implementation
    logger.warning("MCP tool not yet implemented, using standard audio processing")
    return ingest_strategy(state)


def validate_strategy_summary(summary: str) -> Dict[str, Any]:
    """
    Validate that extracted strategy summary contains required sections.
    
    Args:
        summary: Extracted strategy summary text
        
    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "missing_sections": List[str],
            "warnings": List[str]
        }
    """
    required_sections = [
        "Action Items",
        "Technical Decisions",
        "Strategic Goals"
    ]
    
    missing_sections = []
    warnings = []
    
    for section in required_sections:
        if section.lower() not in summary.lower():
            missing_sections.append(section)
    
    # Check for minimum content length
    if len(summary) < 100:
        warnings.append("Strategy summary is very short (< 100 chars)")
    
    # Check for empty sections
    if "None" in summary or "N/A" in summary:
        warnings.append("Some sections may be empty or not applicable")
    
    return {
        "valid": len(missing_sections) == 0,
        "missing_sections": missing_sections,
        "warnings": warnings
    }

# Made with Bob
