"""
Python Refactor MCP: Semantically-aware MCP server for safe Python refactoring.

This package implements an MCP-LSP bridge that connects AI agents to Pyright
for type-safe, semantically-aware Python refactoring operations.
"""

__version__ = "1.0.0"

from .lsp_client import LSPClient
from .mcp_server import PythonRefactorMCPServer
from .workspace_edit import WorkspaceEditManager

__all__ = ["LSPClient", "PythonRefactorMCPServer", "WorkspaceEditManager"]
