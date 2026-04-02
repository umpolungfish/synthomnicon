"""
Aider Code Agent — Git-native AI pair programming for code operations.

This agent wraps aider's Coder class to provide Git-aware code operations:
- Automatic commits with descriptive messages
- Multi-file editing coordination
- Test/lint integration
- Repo map for context-aware changes

Example:
    from agents import AiderCodeAgent
    
    config = {
        "model": "claude-sonnet-4-5-20250929",
        "auto_commits": True,
        "show_diffs": True,
    }
    agent = AiderCodeAgent(config)
    result = await agent.run("Add a hello world function")
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from framework import BaseAgent

logger = logging.getLogger(__name__)


class AiderCodeAgent(BaseAgent):
    """
    Aider Code Agent — Git-native AI pair programming.
    
    Wraps aider's Coder class for Git-aware code operations:
    - Automatic commits with descriptive messages
    - Multi-file editing coordination
    - Test/lint integration
    - Repo map for context-aware changes
    
    Example:
        config = {
            "model": "claude-sonnet-4-5-20250929",
            "auto_commits": True,
            "show_diffs": True,
            "fnames": ["myfile.py"],  # Files to edit
        }
        agent = AiderCodeAgent(config)
        result = await agent.run("Refactor the main function")
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Aider Code Agent.
        
        Args:
            config: Agent configuration with:
                - model: Model name (default: claude-sonnet-4-5-20250929)
                - auto_commits: Auto-commit changes (default: True)
                - show_diffs: Show diffs before committing (default: True)
                - use_git: Use Git for version control (default: True)
                - auto_lint: Auto-lint after changes (default: True)
                - auto_test: Auto-test after changes (default: False)
                - test_cmd: Test command to run (optional)
                - fnames: List of files to edit (optional)
                - auto_accept: Auto-accept changes without confirmation (default: False)
        """
        super().__init__(
            agent_id="aider_code_agent",
            name="Aider Code Agent",
            description="Git-native AI pair programming with automatic commits and multi-file editing",
            capabilities=[
                "git_native_operations",
                "multi_file_editing",
                "automatic_commits",
                "test_integration",
                "lint_integration",
                "repo_context_awareness",
            ],
            config=config,
        )
        
        self.coder = None
        self._aider_available = self._check_aider_available()
        
        if self._aider_available:
            self._init_coder()
        else:
            logger.warning(
                "aider-chat not installed. AiderCodeAgent features will be limited. "
                "Install with: pip install aider-chat"
            )
    
    def _check_aider_available(self) -> bool:
        """Check if aider is available."""
        try:
            from aider.coders import Coder  # noqa: F401
            return True
        except ImportError:
            return False
    
    def _init_coder(self):
        """Initialize aider's Coder with repo context."""
        from aider.coders import Coder
        from aider.models import Model
        from aider.io import InputOutput
        
        # Get config
        model_name = self.config.get("model", "claude-sonnet-4-5-20250929")
        main_model = Model(model_name)
        
        # Create I/O handler
        io = InputOutput(
            pretty=self.config.get("pretty", True),
            yes=self.config.get("auto_accept", False),
        )
        
        # Get files to edit
        fnames = self.config.get("fnames", [])
        
        # Create Coder instance
        try:
            self.coder = Coder.create(
                main_model=main_model,
                io=io,
                fnames=fnames,
                auto_commits=self.config.get("auto_commits", True),
                dirty_commits=self.config.get("dirty_commits", True),
                show_diffs=self.config.get("show_diffs", True),
                use_git=self.config.get("use_git", True),
                auto_lint=self.config.get("auto_lint", True),
                auto_test=self.config.get("auto_test", False),
                test_cmd=self.config.get("test_cmd"),
                dry_run=self.config.get("dry_run", False),
                verbose=self.config.get("verbose", False),
            )
            logger.info(f"AiderCodeAgent initialized with model {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Aider Coder: {e}")
            self.coder = None
    
    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute code operation with Git tracking.
        
        Args:
            task: Natural language description of code operation
            context: Optional context with:
                - files: Additional files to include
                - instructions: Specific instructions
                
        Returns:
            Dict with:
            - status: success/error
            - commits: List of commit hashes
            - files_modified: List of modified files
            - diff: Unified diff of changes
            - findings: Summary of changes
        """
        if not self._aider_available or not self.coder:
            return {
                "status": "error",
                "error": "aider-chat not installed. Install with: pip install aider-chat",
            }
        
        try:
            # Run aider's main loop with task
            # Note: This is synchronous, run in thread pool
            loop = asyncio.get_event_loop()
            
            with ThreadPoolExecutor() as executor:
                # Run coder in thread
                await loop.run_in_executor(
                    executor,
                    self._run_coder_task,
                    task
                )
            
            # Collect results
            commits = list(getattr(self.coder, 'aider_commit_hashes', set()))
            files_modified = list(getattr(self.coder, 'aider_edited_files', set()))
            
            return {
                "status": "success",
                "commits": commits,
                "files_modified": files_modified,
                "findings": f"Code changes completed: {len(commits)} commits, {len(files_modified)} files modified",
                "metadata": {
                    "total_cost": getattr(self.coder, 'total_cost', 0.0),
                    "tokens_sent": getattr(self.coder, 'total_tokens_sent', 0),
                    "tokens_received": getattr(self.coder, 'total_tokens_received', 0),
                }
            }
            
        except Exception as e:
            logger.error(f"Error during Aider code operation: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    def _run_coder_task(self, task: str):
        """Run aider coder task (synchronous)."""
        if self.coder:
            self.coder.run(task)
    
    def get_repo_info(self) -> Dict[str, Any]:
        """Get information about the current Git repository."""
        if not self.coder or not self.coder.repo:
            return {
                "available": False,
                "note": "No Git repository found or Git disabled",
            }
        
        repo = self.coder.repo
        return {
            "available": True,
            "root": str(repo.root),
            "branch": repo.get_branch_name() if hasattr(repo, 'get_branch_name') else "unknown",
            "clean": repo.is_dirty() if hasattr(repo, 'is_dirty') else None,
        }
    
    def add_files(self, fnames: List[str]) -> Dict[str, Any]:
        """
        Add files to the coder's working set.
        
        Args:
            fnames: List of file paths to add
            
        Returns:
            Dict with status and added files
        """
        if not self.coder:
            return {"status": "error", "error": "Coder not initialized"}
        
        try:
            added = []
            for fname in fnames:
                path = Path(fname).resolve()
                if path not in self.coder.abs_fnames:
                    self.coder.abs_fnames.add(path)
                    added.append(str(path))
            
            return {
                "status": "success",
                "added": added,
                "total_files": len(self.coder.abs_fnames),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_files(self) -> List[str]:
        """Get list of files in the working set."""
        if not self.coder:
            return []
        return [str(f) for f in getattr(self.coder, 'abs_fnames', set())]
