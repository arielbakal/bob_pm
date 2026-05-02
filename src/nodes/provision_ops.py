"""
Provision Ops Node - Automatic Linear issue and cycle creation.
Parses approved roadmap and provisions sprint operations.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.state import AgentState, update_state
from src.linear_client import get_linear_client

logger = logging.getLogger(__name__)


def provision_ops(state: AgentState) -> AgentState:
    """
    Node 5: Automatic creation of Linear issues and cycles from approved roadmap.
    
    This node:
    1. Validates that roadmap is approved
    2. Parses roadmap into structured issue data
    3. Creates sprint cycle in Linear
    4. Creates issues with acceptance criteria
    5. Links issues to cycle
    6. Updates state with Linear IDs
    
    Args:
        state: Current AgentState with approved roadmap
        
    Returns:
        Updated AgentState with linear_cycle_id and linear_issue_ids
        
    Raises:
        ValueError: If roadmap not approved or missing
        Exception: If Linear provisioning fails
    """
    logger.info("Starting Linear provisioning from approved roadmap")
    
    # Validate approval status
    if state.get("approval_status") != "approved":
        raise ValueError(
            f"Cannot provision ops - roadmap not approved. "
            f"Status: {state.get('approval_status')}"
        )
    
    # Validate roadmap exists
    roadmap = state.get("roadmap")
    if not roadmap:
        raise ValueError("Cannot provision ops - roadmap is empty")
    
    logger.info("Roadmap approved, beginning provisioning")
    
    # Update provisioning status
    state = update_state(state, provisioning_status="in_progress")
    
    try:
        # Get Linear client
        linear_client = get_linear_client()
        
        # Get team ID (required for cycle and issue creation)
        team_id = linear_client.get_team_id()
        logger.info(f"Using Linear team ID: {team_id}")
        
        # Parse roadmap into structured data
        cycle_data, issues_data = parse_roadmap(roadmap)
        logger.info(f"Parsed roadmap: 1 cycle, {len(issues_data)} issues")
        
        # Create sprint cycle
        cycle = linear_client.create_cycle(
            name=cycle_data["name"],
            starts_at=cycle_data["starts_at"],
            ends_at=cycle_data["ends_at"],
            team_id=team_id,
            description=cycle_data.get("description")
        )
        cycle_id = cycle["id"]
        logger.info(f"Created cycle: {cycle['name']} ({cycle_id})")
        
        # Batch create issues
        created_issues = linear_client.batch_create_issues(
            issues=issues_data,
            team_id=team_id,
            cycle_id=cycle_id
        )
        
        issue_ids = [issue["id"] for issue in created_issues]
        logger.info(f"Created {len(issue_ids)} issues in Linear")
        
        # Log issue identifiers for reference
        for issue in created_issues:
            logger.info(f"  - {issue['identifier']}: {issue['title']}")
        
        # Update state with Linear IDs
        return update_state(
            state,
            linear_cycle_id=cycle_id,
            linear_issue_ids=issue_ids,
            provisioning_status="complete"
        )
        
    except Exception as e:
        logger.error(f"Linear provisioning failed: {e}")
        # Update state to reflect failure
        state = update_state(state, provisioning_status="failed")
        raise Exception(f"Failed to provision Linear operations: {e}")


def parse_roadmap(roadmap: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Parse roadmap markdown into structured cycle and issue data.
    
    Expected roadmap format:
    ```markdown
    # Sprint 2024-W03 (Jan 15-22)
    
    ## Goals
    - Implement authentication system
    - Refactor database layer
    
    ## Issues
    
    ### [HIGH] Implement OAuth2 authentication
    **Priority:** High
    **Acceptance Criteria:**
    - [ ] Google OAuth integration
    - [ ] Token refresh mechanism
    - [ ] Session management
    
    ### [MEDIUM] Refactor database queries
    **Priority:** Medium
    **Acceptance Criteria:**
    - [ ] Extract query builder
    - [ ] Add connection pooling
    ```
    
    Args:
        roadmap: Roadmap markdown text
        
    Returns:
        Tuple of (cycle_data, issues_data)
        - cycle_data: Dict with name, starts_at, ends_at, description
        - issues_data: List of dicts with title, description, priority
    """
    logger.info("Parsing roadmap into structured data")
    
    # Extract cycle information from header
    cycle_match = re.search(
        r'#\s+(.+?)\s+\((.+?)\)',
        roadmap,
        re.MULTILINE
    )
    
    if not cycle_match:
        # Default to current week
        cycle_name = f"Sprint {datetime.now().strftime('%Y-W%U')}"
        starts_at = datetime.now()
        ends_at = starts_at + timedelta(days=7)
    else:
        cycle_name = cycle_match.group(1).strip()
        date_range = cycle_match.group(2).strip()
        
        # Parse date range (e.g., "Jan 15-22")
        starts_at, ends_at = parse_date_range(date_range)
    
    # Extract goals as cycle description
    goals_match = re.search(
        r'##\s+Goals\s*\n(.*?)(?=\n##|\Z)',
        roadmap,
        re.DOTALL
    )
    
    description = None
    if goals_match:
        goals_text = goals_match.group(1).strip()
        description = f"Sprint Goals:\n{goals_text}"
    
    cycle_data = {
        "name": cycle_name,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "description": description
    }
    
    # Extract issues
    issues_data = []
    
    # Find all issue sections (### headers)
    issue_pattern = r'###\s+(?:\[(\w+)\]\s+)?(.+?)\n(.*?)(?=\n###|\Z)'
    issue_matches = re.finditer(issue_pattern, roadmap, re.DOTALL)
    
    for match in issue_matches:
        priority_label = match.group(1)  # HIGH, MEDIUM, LOW
        title = match.group(2).strip()
        body = match.group(3).strip()
        
        # Map priority label to Linear priority (1-4)
        priority_map = {
            "URGENT": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4
        }
        priority = priority_map.get(priority_label, 3)  # Default to Medium
        
        # Extract acceptance criteria
        acceptance_criteria = extract_acceptance_criteria(body)
        
        # Build issue description
        description_parts = []
        
        # Add original body (may contain context)
        if body:
            description_parts.append(body)
        
        # Format acceptance criteria as checklist
        if acceptance_criteria:
            description_parts.append("\n## Acceptance Criteria\n")
            for criterion in acceptance_criteria:
                description_parts.append(f"- [ ] {criterion}")
        
        description = "\n".join(description_parts)
        
        issues_data.append({
            "title": title,
            "description": description,
            "priority": priority
        })
    
    logger.info(f"Parsed cycle: {cycle_data['name']}")
    logger.info(f"Parsed {len(issues_data)} issues")
    
    return cycle_data, issues_data


def parse_date_range(date_range: str) -> tuple[datetime, datetime]:
    """
    Parse date range string into start and end datetimes.
    
    Supports formats:
    - "Jan 15-22" (same month)
    - "Jan 15 - Feb 5" (different months)
    - "2024-01-15 to 2024-01-22" (ISO format)
    
    Args:
        date_range: Date range string
        
    Returns:
        Tuple of (starts_at, ends_at)
    """
    # Try ISO format first
    iso_match = re.match(r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})', date_range)
    if iso_match:
        starts_at = datetime.fromisoformat(iso_match.group(1))
        ends_at = datetime.fromisoformat(iso_match.group(2))
        return starts_at, ends_at
    
    # Try "Jan 15-22" format
    month_day_match = re.match(r'(\w+)\s+(\d+)-(\d+)', date_range)
    if month_day_match:
        month_name = month_day_match.group(1)
        start_day = int(month_day_match.group(2))
        end_day = int(month_day_match.group(3))
        
        # Get current year
        year = datetime.now().year
        
        # Parse month name
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "may": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        month = month_map.get(month_name.lower()[:3], 1)
        
        starts_at = datetime(year, month, start_day)
        ends_at = datetime(year, month, end_day)
        
        return starts_at, ends_at
    
    # Default to current week
    logger.warning(f"Could not parse date range: {date_range}, using current week")
    starts_at = datetime.now()
    ends_at = starts_at + timedelta(days=7)
    return starts_at, ends_at


def extract_acceptance_criteria(text: str) -> List[str]:
    """
    Extract acceptance criteria from issue body text.
    
    Looks for:
    - Lines starting with "- [ ]" or "- [x]"
    - Lines under "Acceptance Criteria:" header
    
    Args:
        text: Issue body text
        
    Returns:
        List of acceptance criteria strings
    """
    criteria = []
    
    # Look for explicit "Acceptance Criteria" section
    ac_match = re.search(
        r'(?:Acceptance Criteria|AC):\s*\n(.*?)(?=\n##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    
    if ac_match:
        ac_text = ac_match.group(1)
        # Extract checklist items
        checklist_items = re.findall(r'-\s+\[[ x]\]\s+(.+)', ac_text)
        criteria.extend(checklist_items)
    
    # Also look for standalone checklist items
    if not criteria:
        checklist_items = re.findall(r'-\s+\[[ x]\]\s+(.+)', text)
        criteria.extend(checklist_items)
    
    return criteria


def validate_provisioning(state: AgentState) -> Dict[str, Any]:
    """
    Validate that provisioning completed successfully.
    
    Args:
        state: AgentState after provisioning
        
    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "cycle_created": bool,
            "issues_created": int,
            "warnings": List[str]
        }
    """
    warnings = []
    
    cycle_created = bool(state.get("linear_cycle_id"))
    issues_created = len(state.get("linear_issue_ids", []))
    
    if not cycle_created:
        warnings.append("No cycle was created")
    
    if issues_created == 0:
        warnings.append("No issues were created")
    
    if state.get("provisioning_status") != "complete":
        warnings.append(f"Provisioning status: {state.get('provisioning_status')}")
    
    return {
        "valid": cycle_created and issues_created > 0,
        "cycle_created": cycle_created,
        "issues_created": issues_created,
        "warnings": warnings
    }

# Made with Bob
