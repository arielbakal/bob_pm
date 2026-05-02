"""
Generate Roadmap Node - Convert meeting summary to structured roadmap.
Uses Gemini to transform unstructured action items into Linear-ready issues.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from src.state import AgentState, update_state
from src.llm import get_gemini_client

logger = logging.getLogger(__name__)


def generate_roadmap_from_summary(
    strategy_summary: str,
    cycle_name: Optional[str] = None,
    cycle_duration_days: int = 7
) -> str:
    """
    Convert strategy summary to structured roadmap markdown.
    
    Uses Gemini to:
    1. Extract action items from meeting summary
    2. Assign priorities (HIGH/MEDIUM/LOW)
    3. Generate acceptance criteria
    4. Format as roadmap markdown compatible with provision_ops
    
    Args:
        strategy_summary: Extracted summary from meeting audio
        cycle_name: Optional custom cycle name (auto-generated if None)
        cycle_duration_days: Sprint duration in days (default: 7)
        
    Returns:
        Structured roadmap markdown string
        
    Example Output:
        # Sprint 2026-W18 (May 05-11)
        
        ## Goals
        - Launch analytics feature
        - Implement authentication
        
        ## Issues
        
        ### [HIGH] Build analytics dashboard
        **Priority:** High
        
        Description here.
        
        **Acceptance Criteria:**
        - [ ] Criterion 1
        - [ ] Criterion 2
    """
    logger.info("Generating roadmap from strategy summary")
    
    # Calculate cycle dates
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    cycle_end = next_monday + timedelta(days=cycle_duration_days - 1)
    
    if not cycle_name:
        cycle_name = f"Sprint {next_monday.strftime('%Y-W%U')}"
    
    cycle_dates = f"{next_monday.strftime('%b %d')}-{cycle_end.strftime('%d')}"
    
    # Get Gemini client
    gemini_client = get_gemini_client(
        model_name="gemini-2.5-flash",
        temperature=0.3,  # Lower temperature for structured output
        max_output_tokens=4096
    )
    
    # System prompt for roadmap generation
    system_prompt = """You are an expert engineering project manager who converts meeting notes into actionable sprint roadmaps.

Your task is to transform unstructured meeting summaries into well-structured sprint roadmaps with:
- Clear, actionable issue titles
- Appropriate priority levels (HIGH/MEDIUM/LOW)
- Detailed descriptions
- Specific acceptance criteria (3-5 items per issue)

Follow the exact markdown format provided in the example."""
    
    # Task prompt with format specification
    task_prompt = f"""Convert this meeting summary into a sprint roadmap:

MEETING SUMMARY:
{strategy_summary}

Generate a roadmap with this EXACT format:

# {cycle_name} ({cycle_dates})

## Goals
- [Extract 3-5 high-level goals from the summary]

## Issues

### [PRIORITY] Issue Title
**Priority:** High/Medium/Low

[Detailed description of what needs to be done]

**Acceptance Criteria:**
- [ ] Specific, measurable criterion 1
- [ ] Specific, measurable criterion 2
- [ ] Specific, measurable criterion 3

[Repeat for each action item found in the summary]

IMPORTANT RULES:
1. Extract ALL action items from the summary
2. Assign realistic priorities based on urgency and impact
3. Write clear, actionable issue titles (not vague)
4. Include 3-5 specific acceptance criteria per issue
5. Use the EXACT markdown format shown above
6. Priority prefix must be [HIGH], [MEDIUM], or [LOW]
7. Each issue must have a "**Priority:**" line
8. Acceptance criteria must use "- [ ]" checkbox format

Generate the roadmap now:"""
    
    try:
        # Generate roadmap with Gemini
        roadmap = gemini_client.invoke(
            prompt=task_prompt,
            system_prompt=system_prompt
        )
        
        logger.info(f"Generated roadmap: {len(roadmap)} characters")
        logger.debug(f"Roadmap preview: {roadmap[:200]}...")
        
        # Validate roadmap format
        validation = validate_roadmap_format(roadmap)
        if not validation["valid"]:
            logger.warning(f"Roadmap validation issues: {validation['issues']}")
            # Could regenerate here if needed, but we'll proceed with warnings
        
        return roadmap
        
    except Exception as e:
        logger.error(f"Failed to generate roadmap: {e}")
        raise Exception(f"Roadmap generation failed: {e}")


def validate_roadmap_format(roadmap: str) -> dict:
    """
    Validate that generated roadmap matches expected format.
    
    Args:
        roadmap: Generated roadmap markdown
        
    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "issues": List[str],
            "warnings": List[str]
        }
    """
    issues = []
    warnings = []
    
    # Check for required sections
    if "# Sprint" not in roadmap and "# " not in roadmap:
        issues.append("Missing cycle header (# Sprint ...)")
    
    if "## Goals" not in roadmap:
        issues.append("Missing Goals section")
    
    if "## Issues" not in roadmap:
        issues.append("Missing Issues section")
    
    # Check for at least one issue
    if "###" not in roadmap:
        issues.append("No issues found (missing ### headers)")
    
    # Check for priority markers
    priority_count = roadmap.count("[HIGH]") + roadmap.count("[MEDIUM]") + roadmap.count("[LOW]")
    if priority_count == 0:
        issues.append("No priority markers found ([HIGH]/[MEDIUM]/[LOW])")
    
    # Check for acceptance criteria
    if "**Acceptance Criteria:**" not in roadmap:
        warnings.append("No acceptance criteria sections found")
    
    # Check for checkbox format
    if "- [ ]" not in roadmap:
        warnings.append("No checkbox items found (- [ ])")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }


def generate_roadmap(state: AgentState) -> AgentState:
    """
    Node: Generate roadmap from strategy summary WITH GitHub context.
    
    Enhanced to incorporate:
    - Technical constraints from codebase analysis
    - Architectural patterns
    - Existing tech stack
    
    This node:
    1. Takes strategy_summary from state
    2. Optionally incorporates codebase_insights from GitHub analysis
    3. Uses Gemini to convert to structured roadmap
    4. Updates state with roadmap markdown
    
    Args:
        state: Current AgentState with strategy_summary populated
        
    Returns:
        Updated AgentState with roadmap
        
    Raises:
        ValueError: If strategy_summary is not in state
        Exception: If roadmap generation fails
    """
    logger.info("Starting enhanced roadmap generation with GitHub context")
    
    # Validate input
    strategy_summary = state.get("strategy_summary")
    if not strategy_summary:
        raise ValueError(
            "strategy_summary must be provided in state for generate_roadmap node"
        )
    
    # Get GitHub context (optional - may not be available)
    codebase_insights = state.get("codebase_insights", "")
    github_context = state.get("github_context", {})
    
    has_github_context = bool(codebase_insights and codebase_insights != "Codebase analysis unavailable - proceeding without GitHub context")
    
    if has_github_context:
        logger.info(f"Generating roadmap with GitHub context ({len(codebase_insights)} chars)")
    else:
        logger.info("Generating roadmap without GitHub context")
    
    # Build enhanced prompt with GitHub context
    context_section = ""
    if has_github_context:
        context_section = f"""

## Technical Context from Codebase Analysis

{codebase_insights}

**Important:** Ensure all proposed issues align with the existing architecture and tech stack."""
    
    # Get Gemini client
    gemini_client = get_gemini_client(
        model_name="gemini-2.5-flash",
        temperature=0.3,
        max_output_tokens=4096
    )
    
    # Calculate cycle dates
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    cycle_end = next_monday + timedelta(days=6)
    cycle_name = f"Sprint {next_monday.strftime('%Y-W%U')}"
    cycle_dates = f"{next_monday.strftime('%b %d')}-{cycle_end.strftime('%d')}"
    
    # Enhanced system prompt
    system_prompt = """You are an expert engineering project manager who converts meeting notes into actionable sprint roadmaps.

You have access to technical context about the codebase. Use this to:
- Ensure proposed work aligns with existing architecture
- Identify technical dependencies
- Flag potential conflicts with current tech stack
- Suggest implementation approaches that fit the codebase"""
    
    # Enhanced task prompt
    task_prompt = f"""Convert this meeting summary into a technically-informed sprint roadmap:

## MEETING SUMMARY
{strategy_summary}
{context_section}

Generate a roadmap with this EXACT format:

# {cycle_name} ({cycle_dates})

## Goals
- [Extract 3-5 high-level goals aligned with technical constraints]

## Issues

### [PRIORITY] Issue Title
**Priority:** High/Medium/Low

[Description that considers existing architecture and tech stack]

**Technical Notes:**
- [Any architectural considerations]
- [Dependencies on existing components]

**Acceptance Criteria:**
- [ ] Specific, measurable criterion 1
- [ ] Specific, measurable criterion 2
- [ ] Specific, measurable criterion 3

IMPORTANT RULES:
1. Consider technical constraints from codebase analysis
2. Align issues with existing architecture patterns
3. Flag any potential technical conflicts
4. Include technical notes for complex issues
5. Use realistic priorities based on technical complexity
6. Ensure acceptance criteria are technically feasible

Generate the roadmap now:"""
    
    try:
        # Generate enhanced roadmap
        roadmap = gemini_client.invoke(
            prompt=task_prompt,
            system_prompt=system_prompt
        )
        
        logger.info(f"Generated enhanced roadmap: {len(roadmap)} characters")
        
        # Validate format
        validation = validate_roadmap_format(roadmap)
        if not validation["valid"]:
            logger.warning(f"Roadmap validation issues: {validation['issues']}")
        
        # Update state with roadmap
        # Note: approval_status remains "pending" until human approval
        return update_state(
            state,
            roadmap=roadmap,
            roadmap_version=state.get("roadmap_version", 0) + 1
        )
        
    except Exception as e:
        logger.error(f"Enhanced roadmap generation failed: {e}")
        raise Exception(f"Failed to generate roadmap: {e}")


# Made with Bob