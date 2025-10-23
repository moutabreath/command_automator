"""
Commands Automator package.
"""

# Expose key components for easier access
from .commands_automator_api import CommandsAutomatorApi
from .llm.mcp_servers.job_applicant_mcp import MCPRunner
from .utils.logger_config import setup_logging

# Import submodules last to avoid circular dependencies
from . import ui
from . import llm
from . import services

__version__ = "0.1.0"

__all__ = [
    "ui",
    "llm",
    "services",
    "config",
    "CommandsAutomatorApi",
    "MCPRunner",
    "setup_logging",
]
