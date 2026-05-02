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
            raise ValueError(
                "GITHUB_TOKEN not set. Get one from https://github.com/settings/tokens"
            )
        
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
            raise ValueError("Repository not set. Provide repo_name in constructor or set GITHUB_REPO env var")
        
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
        key_patterns = ["src", "lib", "app", "tests", "test", "docs", "api", "components", "examples"]
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


# Singleton instance for reuse across nodes
_github_client: Optional[GitHubClient] = None


def get_github_client(token: Optional[str] = None, repo_name: Optional[str] = None) -> GitHubClient:
    """
    Get or create singleton GitHub client.
    
    Args:
        token: GitHub personal access token (defaults to env var)
        repo_name: Repository name (defaults to env var)
        
    Returns:
        GitHubClient instance
    """
    global _github_client
    
    if _github_client is None:
        _github_client = GitHubClient(token=token, repo_name=repo_name)
    
    return _github_client

# Made with Bob