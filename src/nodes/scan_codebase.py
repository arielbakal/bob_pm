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
            codebase_insights="Codebase analysis unavailable - proceeding without GitHub context"
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
            subtree = _format_file_tree(value, indent + 1, max_depth)
            if subtree:
                lines.append(subtree)
    
    return "\n".join(lines)

# Made with Bob