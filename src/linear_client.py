"""
Linear GraphQL client for sprint management and issue provisioning.
Handles cycle creation, issue creation, and status queries.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LinearClient:
    """
    GraphQL client for Linear API operations.
    
    Features:
    - Cycle (sprint) creation and management
    - Issue creation with acceptance criteria
    - Status queries and updates
    - Automatic retry on failures
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None
    ):
        """
        Initialize Linear GraphQL client.
        
        Args:
            api_key: Linear API key (defaults to LINEAR_API_KEY env var)
            workspace_id: Linear workspace ID (defaults to LINEAR_WORKSPACE_ID env var)
        """
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        self.workspace_id = workspace_id or os.getenv("LINEAR_WORKSPACE_ID")
        
        if not self.api_key:
            raise ValueError(
                "LINEAR_API_KEY not set. Get one from https://linear.app/settings/api"
            )
        
        # Configure GraphQL transport
        transport = RequestsHTTPTransport(
            url="https://api.linear.app/graphql",
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            },
            verify=True,
            retries=3
        )
        
        # Create GraphQL client
        self.client = Client(
            transport=transport,
            fetch_schema_from_transport=True
        )
        
        logger.info("Linear GraphQL client initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query with automatic retry.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query result as dict
            
        Raises:
            Exception: After 3 failed retry attempts
        """
        try:
            result = self.client.execute(
                gql(query),
                variable_values=variables
            )
            return result
        except Exception as e:
            logger.error(f"GraphQL query failed: {e}")
            raise
    
    def create_cycle(
        self,
        name: str,
        starts_at: datetime,
        ends_at: datetime,
        team_id: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new sprint cycle in Linear.
        
        Args:
            name: Cycle name (e.g., "Sprint 2024-W03")
            starts_at: Cycle start date
            ends_at: Cycle end date
            team_id: Linear team ID
            description: Optional cycle description
            
        Returns:
            Created cycle data with ID
        """
        mutation = """
        mutation CreateCycle($input: CycleCreateInput!) {
            cycleCreate(input: $input) {
                success
                cycle {
                    id
                    name
                    number
                    startsAt
                    endsAt
                    description
                }
            }
        }
        """
        
        variables = {
            "input": {
                "name": name,
                "startsAt": starts_at.isoformat(),
                "endsAt": ends_at.isoformat(),
                "teamId": team_id
            }
        }
        
        if description:
            # Linear has a 255 character limit for cycle descriptions
            variables["input"]["description"] = description[:255]
        
        logger.info(f"Creating cycle: {name}")
        result = self.execute_query(mutation, variables)
        
        if result["cycleCreate"]["success"]:
            cycle = result["cycleCreate"]["cycle"]
            logger.info(f"Cycle created: {cycle['id']} - {cycle['name']}")
            return cycle
        else:
            raise Exception("Failed to create cycle")
    
    def create_issue(
        self,
        title: str,
        description: str,
        team_id: str,
        cycle_id: Optional[str] = None,
        priority: int = 3,
        labels: Optional[List[str]] = None,
        assignee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue in Linear.
        
        Args:
            title: Issue title
            description: Issue description with acceptance criteria
            team_id: Linear team ID
            cycle_id: Optional cycle to assign issue to
            priority: Priority (1=Urgent, 2=High, 3=Medium, 4=Low)
            labels: Optional list of label IDs
            assignee_id: Optional assignee user ID
            
        Returns:
            Created issue data with ID
        """
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    priority
                    url
                    state {
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            "input": {
                "title": title,
                "description": description,
                "teamId": team_id,
                "priority": priority
            }
        }
        
        if cycle_id:
            variables["input"]["cycleId"] = cycle_id
        
        if labels:
            variables["input"]["labelIds"] = labels
        
        if assignee_id:
            variables["input"]["assigneeId"] = assignee_id
        
        logger.info(f"Creating issue: {title}")
        result = self.execute_query(mutation, variables)
        
        if result["issueCreate"]["success"]:
            issue = result["issueCreate"]["issue"]
            logger.info(f"Issue created: {issue['identifier']} - {issue['title']}")
            return issue
        else:
            raise Exception(f"Failed to create issue: {title}")
    
    def batch_create_issues(
        self,
        issues: List[Dict[str, Any]],
        team_id: str,
        cycle_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create multiple issues in batch.
        
        Args:
            issues: List of issue dicts with title, description, priority
            team_id: Linear team ID
            cycle_id: Optional cycle to assign all issues to
            
        Returns:
            List of created issue data
        """
        created_issues = []
        
        for issue_data in issues:
            try:
                issue = self.create_issue(
                    title=issue_data["title"],
                    description=issue_data["description"],
                    team_id=team_id,
                    cycle_id=cycle_id,
                    priority=issue_data.get("priority", 3),
                    labels=issue_data.get("labels"),
                    assignee_id=issue_data.get("assignee_id")
                )
                created_issues.append(issue)
            except Exception as e:
                logger.error(f"Failed to create issue '{issue_data['title']}': {e}")
                # Continue with other issues instead of failing entire batch
                continue
        
        logger.info(f"Batch created {len(created_issues)}/{len(issues)} issues")
        return created_issues
    
    def get_issues_by_cycle(
        self,
        cycle_id: str,
        state_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query issues in a specific cycle.
        
        Args:
            cycle_id: Linear cycle ID
            state_filter: Optional state name filter (e.g., "In Progress")
            
        Returns:
            List of issue data
        """
        query = """
        query GetIssuesByCycle($cycleId: String!, $stateFilter: String) {
            issues(
                filter: {
                    cycle: { id: { eq: $cycleId } }
                    state: { name: { eq: $stateFilter } }
                }
            ) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    url
                    state {
                        name
                    }
                    assignee {
                        name
                    }
                    branchName
                }
            }
        }
        """
        
        variables = {
            "cycleId": cycle_id,
            "stateFilter": state_filter
        }
        
        result = self.execute_query(query, variables)
        return result["issues"]["nodes"]
    
    def get_team_id(self, team_name: Optional[str] = None) -> str:
        """
        Get team ID by name or return first team.
        
        Args:
            team_name: Optional team name to search for
            
        Returns:
            Team ID
        """
        query = """
        query GetTeams {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        
        result = self.execute_query(query)
        teams = result["teams"]["nodes"]
        
        if not teams:
            raise Exception("No teams found in Linear workspace")
        
        if team_name:
            for team in teams:
                if team["name"].lower() == team_name.lower():
                    return team["id"]
            raise Exception(f"Team '{team_name}' not found")
        
        # Return first team if no name specified
        return teams[0]["id"]
    
    def update_issue_state(
        self,
        issue_id: str,
        state_id: str
    ) -> Dict[str, Any]:
        """
        Update issue state (e.g., move to "In Progress").
        
        Args:
            issue_id: Linear issue ID
            state_id: Target state ID
            
        Returns:
            Updated issue data
        """
        mutation = """
        mutation UpdateIssue($id: String!, $stateId: String!) {
            issueUpdate(
                id: $id
                input: { stateId: $stateId }
            ) {
                success
                issue {
                    id
                    identifier
                    state {
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            "id": issue_id,
            "stateId": state_id
        }
        
        result = self.execute_query(mutation, variables)
        
        if result["issueUpdate"]["success"]:
            return result["issueUpdate"]["issue"]
        else:
            raise Exception(f"Failed to update issue {issue_id}")


# Singleton instance for reuse across nodes
_linear_client: Optional[LinearClient] = None


def get_linear_client(
    api_key: Optional[str] = None,
    workspace_id: Optional[str] = None
) -> LinearClient:
    """
    Get or create singleton Linear client.
    
    Args:
        api_key: Linear API key (defaults to env var)
        workspace_id: Linear workspace ID (defaults to env var)
        
    Returns:
        LinearClient instance
    """
    global _linear_client
    
    if _linear_client is None:
        _linear_client = LinearClient(
            api_key=api_key,
            workspace_id=workspace_id
        )
    
    return _linear_client

# Made with Bob
