# Nexus-PM Agent - Final Implementation Plan

## Executive Summary

This plan completes the Nexus-PM Agent by implementing the remaining LangGraph components: GitHub codebase scanning, enhanced roadmap generation with technical context, and the complete StateGraph with human-in-the-loop approval.

## Current Status

### ✅ Completed Components

1. **Core Infrastructure**
   - [`src/state.py`](src/state.py) - AgentState TypedDict with all required fields
   - [`src/llm.py`](src/llm.py) - Gemini API client with audio processing
   - [`src/linear_client.py`](src/linear_client.py) - Linear GraphQL client

2. **Implemented Nodes**
   - [`src/nodes/ingest_strategy.py`](src/nodes/ingest_strategy.py) - Audio processing with Gemini
   - [`src/nodes/generate_roadmap.py`](src/nodes/generate_roadmap.py) - Roadmap generation from summaries
   - [`src/nodes/provision_ops.py`](src/nodes/provision_ops.py) - Linear issue provisioning

3. **Testing**
   - [`examples/test_end_to_end.py`](examples/test_end_to_end.py) - Complete workflow validation

### 🔨 Remaining Work

1. **GitHub Integration** - Codebase scanning and analysis
2. **Enhanced Roadmap** - Incorporate GitHub context into planning
3. **StateGraph** - Complete LangGraph workflow with interrupts
4. **Human Gate** - Approval checkpoint implementation
5. **Testing** - Full StateGraph workflow validation

---

## Implementation Tasks

### Task 1: GitHub Client for Codebase Scanning

**File:** `src/github_client.py`

**Purpose:** Analyze GitHub repository structure and extract technical context

**Implementation:**

```python
"""
GitHub client for repository analysis and commit tracking.
Provides codebase structure, file tree, and activity monitoring.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from github import Github, Repository
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    GitHub API client for codebase analysis.
    
    Features:
    - Repository structure analysis
    - File tree extraction
    - Commit activity tracking
    - Branch monitoring
    """
    
    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
            repo_name: Repository name in format "owner/repo" (defaults to GITHUB_REPO env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo_name = repo_name or os.getenv("GITHUB_REPO")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN not set")
        
        self.client = Github(self.token)
        self.repo: Optional[Repository.Repository] = None
        
        if self.repo_name:
            self.repo = self.client.get_repo(self.repo_name)
            logger.info(f"Connected to repository: {self.repo_name}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_repository_structure(self) -> Dict[str, Any]:
        """
        Get complete repository structure including file tree and metadata.
        
        Returns:
            Dict with:
            - file_tree: Nested dict of directories and files
            - languages: Programming languages used
            - total_files: Total file count
            - key_directories: Important directories identified
        """
        if not self.repo:
            raise ValueError("Repository not set")
        
        logger.info(f"Analyzing repository structure: {self.repo_name}")
        
        # Get file tree
        contents = self.repo.get_contents("")
        file_tree = self._build_file_tree(contents)
        
        # Get languages
        languages = self.repo.get_languages()
        
        # Identify key directories
        key_dirs = self._identify_key_directories(file_tree)
        
        return {
            "repo_name": self.repo_name,
            "file_tree": file_tree,
            "languages": languages,
            "total_files": self._count_files(file_tree),
            "key_directories": key_dirs,
            "default_branch": self.repo.default_branch
        }
    
    def _build_file_tree(self, contents, max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
        """Recursively build file tree (limited depth to avoid API rate limits)."""
        tree = {}
        
        if current_depth >= max_depth:
            return tree
        
        for content in contents:
            if content.type == "dir":
                try:
                    subcontents = self.repo.get_contents(content.path)
                    tree[content.name] = self._build_file_tree(subcontents, max_depth, current_depth + 1)
                except Exception as e:
                    logger.warning(f"Could not access directory {content.path}: {e}")
                    tree[content.name] = {}
            else:
                tree[content.name] = {
                    "type": "file",
                    "size": content.size,
                    "path": content.path
                }
        
        return tree
    
    def _count_files(self, tree: Dict[str, Any]) -> int:
        """Count total files in tree."""
        count = 0
        for value in tree.values():
            if isinstance(value, dict):
                if value.get("type") == "file":
                    count += 1
                else:
                    count += self._count_files(value)
        return count
    
    def _identify_key_directories(self, tree: Dict[str, Any]) -> List[str]:
        """Identify important directories (src, tests, docs, etc.)."""
        key_patterns = ["src", "lib", "app", "tests", "test", "docs", "api", "components"]
        key_dirs = []
        
        for dir_name in tree.keys():
            if any(pattern in dir_name.lower() for pattern in key_patterns):
                key_dirs.append(dir_name)
        
        return key_dirs
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_recent_commits(self, branch: Optional[str] = None, since_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent commits on a branch.
        
        Args:
            branch: Branch name (defaults to default branch)
            since_hours: Look back this many hours
            
        Returns:
            List of commit data
        """
        if not self.repo:
            raise ValueError("Repository not set")
        
        branch = branch or self.repo.default_branch
        since = datetime.now() - timedelta(hours=since_hours)
        
        commits = self.repo.get_commits(sha=branch, since=since)
        
        return [
            {
                "sha": commit.sha[:7],
                "message": commit.commit.message,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat(),
                "files_changed": len(commit.files) if commit.files else 0
            }
            for commit in commits
        ]


def get_github_client(token: Optional[str] = None, repo_name: Optional[str] = None) -> GitHubClient:
    """Get or create singleton GitHub client."""
    return GitHubClient(token=token, repo_name=repo_name)
```

**Dependencies:** Already in [`requirements.txt`](requirements.txt:27) - `PyGithub>=2.3.0`

**Environment Variables:**
- `GITHUB_TOKEN` - Personal access token
- `GITHUB_REPO` - Repository name (e.g., "owner/repo")

---

### Task 2: Scan Codebase Node

**File:** `src/nodes/scan_codebase.py`

**Purpose:** Analyze GitHub repository and generate technical insights with Gemini

**Implementation:**

```python
"""
Scan Codebase Node - GitHub repository analysis with Gemini insights.
Extracts technical context for roadmap generation.
"""

import logging
from typing import Dict, Any
from src.state import AgentState, update_state
from src.github_client import get_github_client
from src.llm import get_gemini_client

logger = logging.getLogger(__name__)


def scan_codebase(state: AgentState) -> AgentState:
    """
    Node 2: Analyze GitHub repository structure and generate technical insights.
    
    This node:
    1. Fetches repository structure from GitHub
    2. Analyzes file tree, languages, and key directories
    3. Uses Gemini to generate architectural insights
    4. Updates state with github_context and codebase_insights
    
    Args:
        state: Current AgentState
        
    Returns:
        Updated AgentState with github_context and codebase_insights
    """
    logger.info("Starting codebase scan")
    
    try:
        # Get GitHub client
        github_client = get_github_client()
        
        # Fetch repository structure
        repo_structure = github_client.get_repository_structure()
        logger.info(f"Fetched structure for {repo_structure['repo_name']}")
        logger.info(f"Languages: {list(repo_structure['languages'].keys())}")
        logger.info(f"Total files: {repo_structure['total_files']}")
        
        # Get Gemini client for analysis
        gemini_client = get_gemini_client(
            model_name="gemini-2.5-flash",
            temperature=0.3,
            max_output_tokens=4096
        )
        
        # Build analysis prompt
        analysis_prompt = f"""Analyze this codebase structure and provide technical insights:

Repository: {repo_structure['repo_name']}
Languages: {', '.join(repo_structure['languages'].keys())}
Total Files: {repo_structure['total_files']}
Key Directories: {', '.join(repo_structure['key_directories'])}

File Structure:
{_format_file_tree(repo_structure['file_tree'])}

Provide:
1. **Architecture Pattern**: Identify the architectural style (monorepo, microservices, MVC, etc.)
2. **Tech Stack**: Main frameworks and libraries used
3. **Key Components**: Important modules or services
4. **Technical Constraints**: Limitations or dependencies to consider
5. **Recommendations**: Suggestions for new feature development

Be concise and focus on actionable insights for sprint planning."""

        system_prompt = """You are a senior software architect analyzing a codebase.
Provide concise, actionable insights that will help with sprint planning and feature development."""

        # Generate insights with Gemini
        codebase_insights = gemini_client.invoke(
            prompt=analysis_prompt,
            system_prompt=system_prompt
        )
        
        logger.info("Generated codebase insights")
        logger.debug(f"Insights length: {len(codebase_insights)} characters")
        
        # Update state
        return update_state(
            state,
            github_context=repo_structure,
            codebase_insights=codebase_insights
        )
        
    except Exception as e:
        logger.error(f"Codebase scan failed: {e}")
        # Continue with empty context rather than failing
        return update_state(
            state,
            github_context={"error": str(e)},
            codebase_insights="Codebase analysis unavailable"
        )


def _format_file_tree(tree: Dict[str, Any], indent: int = 0, max_depth: int = 2) -> str:
    """Format file tree as readable text (limited depth)."""
    if indent >= max_depth:
        return ""
    
    lines = []
    for name, value in tree.items():
        prefix = "  " * indent
        if isinstance(value, dict) and value.get("type") == "file":
            lines.append(f"{prefix}- {name}")
        elif isinstance(value, dict):
            lines.append(f"{prefix}📁 {name}/")
            lines.append(_format_file_tree(value, indent + 1, max_depth))
    
    return "\n".join(lines)
```

---

### Task 3: Enhanced Roadmap Generation

**File:** Update [`src/nodes/generate_roadmap.py`](src/nodes/generate_roadmap.py)

**Changes:** Modify [`generate_roadmap()`](src/nodes/generate_roadmap.py:199) to incorporate GitHub context

**Implementation:**

```python
def generate_roadmap(state: AgentState) -> AgentState:
    """
    Node: Generate roadmap from strategy summary WITH GitHub context.
    
    Enhanced to incorporate:
    - Technical constraints from codebase analysis
    - Architectural patterns
    - Existing tech stack
    """
    logger.info("Starting enhanced roadmap generation with GitHub context")
    
    # Validate inputs
    strategy_summary = state.get("strategy_summary")
    if not strategy_summary:
        raise ValueError("strategy_summary required for generate_roadmap")
    
    # Get GitHub context (optional - may not be available)
    codebase_insights = state.get("codebase_insights", "")
    github_context = state.get("github_context", {})
    
    # Build enhanced prompt
    context_section = ""
    if codebase_insights:
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
        
        # Update state
        return update_state(
            state,
            roadmap=roadmap,
            roadmap_version=state.get("roadmap_version", 0) + 1
        )
        
    except Exception as e:
        logger.error(f"Enhanced roadmap generation failed: {e}")
        raise Exception(f"Failed to generate roadmap: {e}")
```

---

### Task 4: Complete StateGraph Implementation

**File:** `src/graph.py`

**Purpose:** Assemble all nodes into LangGraph StateGraph with human-in-the-loop

**Implementation:**

```python
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
```

---

### Task 5: Complete Workflow Test

**File:** `examples/test_complete_workflow.py`

**Purpose:** Test full StateGraph with interrupt and resumption

**Implementation:**

```python
"""
Complete workflow test with human-in-the-loop approval.
Tests the full LangGraph StateGraph from audio to Linear issues.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import create_initial_state
from src.graph import create_workflow, run_workflow, resume_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_complete_workflow():
    """
    Test complete workflow with interrupt and approval.
    
    Workflow:
    1. Process meeting audio
    2. Scan codebase
    3. Generate roadmap
    4. INTERRUPT for approval
    5. Resume with approval
    6. Provision Linear issues
    """
    logger.info("=" * 60)
    logger.info("COMPLETE WORKFLOW TEST")
    logger.info("=" * 60)
    
    # Create workflow
    workflow = create_workflow(checkpointer_path="test_workflow.db")
    
    # Create initial state
    workflow_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    initial_state = create_initial_state(
        workflow_id=workflow_id,
        meeting_audio_path="examples/sample_meeting.mp3"
    )
    
    logger.info(f"Workflow ID: {workflow_id}")
    
    # Phase 1: Run until interrupt
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: Running workflow until human gate")
    logger.info("=" * 60)
    
    state_at_interrupt = run_workflow(workflow, initial_state, workflow_id)
    
    # Display roadmap for approval
    logger.info("\n" + "=" * 60)
    logger.info("ROADMAP FOR APPROVAL")
    logger.info("=" * 60)
    print(state_at_interrupt.get("roadmap", "No roadmap generated"))
    
    # Simulate human approval
    logger.info("\n" + "=" * 60)
    logger.info("SIMULATING HUMAN APPROVAL")
    logger.info("=" * 60)
    
    approval_status = "approved"  # Change to "rejected" to test regeneration
    approval_feedback = None
    
    logger.info(f"Approval status: {approval_status}")
    
    # Phase 2: Resume with approval
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Resuming workflow with approval")
    logger.info("=" * 60)
    
    final_state = resume_workflow(
        workflow,
        workflow_id,
        approval_status,
        approval_feedback
    )
    
    # Display results
    logger.info("\n" + "=" * 60)
    logger.info("WORKFLOW COMPLETE")
    logger.info("=" * 60)
    
    logger.info(f"Cycle ID: {final_state.get('linear_cycle_id')}")
    logger.info(f"Issues created: {len(final_state.get('linear_issue_ids', []))}")
    logger.info(f"Provisioning status: {final_state.get('provisioning_status')}")
    
    return final_state


if __name__ == "__main__":
    try:
        final_state = test_complete_workflow()
        logger.info("\n✅ Complete workflow test PASSED")
    except Exception as e:
        logger.error(f"\n❌ Complete workflow test FAILED: {e}", exc_info=True)
        sys.exit(1)
```

---

## Testing Strategy

### Unit Tests

1. **GitHub Client** - Test repository structure fetching
2. **Scan Codebase Node** - Test with mock GitHub data
3. **Enhanced Roadmap** - Test with and without GitHub context
4. **StateGraph** - Test node connections and routing

### Integration Tests

1. **Interrupt Mechanism** - Verify workflow pauses at human_gate
2. **State Persistence** - Verify SQLite checkpointer works
3. **Approval Routing** - Test both approved and rejected paths
4. **Regeneration Loop** - Test roadmap regeneration with feedback

### End-to-End Test

Run [`examples/test_complete_workflow.py`](examples/test_complete_workflow.py) with:
- Real meeting audio
- Real GitHub repository
- Real Linear workspace
- Manual approval step

---

## Environment Setup

### Required Environment Variables

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Linear
LINEAR_API_KEY=your_linear_api_key

# GitHub
GITHUB_TOKEN=your_github_token
GITHUB_REPO=owner/repo

# Optional
PYTHONWARNINGS=ignore::FutureWarning
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import langgraph; import github; print('✅ All dependencies installed')"
```

---

## Execution Timeline

### Phase 1: GitHub Integration (2-3 hours)
- [ ] Implement [`src/github_client.py`](src/github_client.py)
- [ ] Test with real repository
- [ ] Verify API rate limits

### Phase 2: Scan Codebase Node (1-2 hours)
- [ ] Implement [`src/nodes/scan_codebase.py`](src/nodes/scan_codebase.py)
- [ ] Test with GitHub client
- [ ] Validate Gemini insights

### Phase 3: Enhanced Roadmap (1 hour)
- [ ] Update [`generate_roadmap()`](src/nodes/generate_roadmap.py:199)
- [ ] Test with GitHub context
- [ ] Validate output format

### Phase 4: StateGraph (2-3 hours)
- [ ] Implement [`src/graph.py`](src/graph.py)
- [ ] Configure interrupt points
- [ ] Test state persistence

### Phase 5: Complete Testing (2-3 hours)
- [ ] Create [`examples/test_complete_workflow.py`](examples/test_complete_workflow.py)
- [ ] Run end-to-end test
- [ ] Validate all components

### Phase 6: Documentation (1 hour)
- [ ] Update [`README.md`](README.md)
- [ ] Create workflow diagrams
- [ ] Document approval process

**Total Estimated Time: 9-13 hours**

---

## Success Criteria

✅ **Complete Workflow**
- Audio → Summary → GitHub Analysis → Roadmap → Approval → Linear Issues

✅ **Human-in-the-Loop**
- Workflow pauses at human_gate
- State persists during approval
- Resumes correctly after approval

✅ **GitHub Integration**
- Repository structure analyzed
- Technical insights generated
- Context incorporated into roadmap

✅ **Error Handling**
- Graceful failures at each node
- Retry logic for API calls
- Informative error messages

✅ **Testing**
- All nodes tested individually
- Complete workflow tested end-to-end
- Approval/rejection paths validated

---

## Next Steps After Completion

### Optional Enhancements

1. **Monitor Loop** - Cyclic blocker detection (from [`stategraph-plan.md`](stategraph-plan.md:259))
2. **MCP Tools** - Custom tools for Linear/GitHub/Vertex AI
3. **Bob Mode** - Custom mode configuration in `.bob/custom_modes.yaml`
4. **Notifications** - Slack/email alerts for blockers
5. **Analytics** - Track sprint velocity and completion rates

### Production Deployment

1. **Environment** - Set up production credentials
2. **Monitoring** - Add logging and metrics
3. **Scheduling** - Automate weekly workflow runs
4. **Documentation** - User guide for Lead Devs

---

## Conclusion

This plan completes the Nexus-PM Agent by implementing the remaining 5 core components. The implementation is straightforward since all infrastructure is already in place. Each task builds on existing patterns and can be completed independently.

**Key Advantages:**
- ✅ All dependencies already installed
- ✅ State schema already defined
- ✅ Node patterns already established
- ✅ Testing framework already created
- ✅ Clear success criteria defined

**Estimated completion: 9-13 hours of focused development**