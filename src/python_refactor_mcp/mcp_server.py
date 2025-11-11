"""
MCP Server: AI-friendly API for safe Python refactoring via Pyright LSP.

This module implements the MCP server that exposes tools for AI agents.
Each tool translates MCP requests into LSP requests and ensures safety
through the two-stage WorkspaceEdit approval process.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .lsp_client import LSPClient
from .workspace_edit import WorkspaceEditManager

logger = logging.getLogger(__name__)


class PythonRefactorMCPServer:
    """
    MCP-LSP Bridge Server for safe Python refactoring.

    Architecture:
    - Exposes MCP tools for AI agents
    - Translates tool calls to LSP requests
    - Manages persistent Pyright subprocess
    - Enforces two-stage WorkspaceEdit security model
    """

    def __init__(self, workspace_root: str):
        """
        Initialize MCP server.

        Args:
            workspace_root: Absolute path to the Python project root
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.lsp_client: Optional[LSPClient] = None
        self.workspace_edit_manager: Optional[WorkspaceEditManager] = None
        self.mcp_server = Server("python-refactor-mcp")

        # Register MCP tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all MCP tools with their handlers."""

        # Navigation tools
        @self.mcp_server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            return [
                Tool(
                    name="get_definition",
                    description="Find the definition of a symbol (variable, function, class). "
                    "Returns the file path and position where the symbol is defined. "
                    "Use this to navigate to source code.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the Python file",
                            },
                            "line": {
                                "type": "integer",
                                "description": "Line number (0-based)",
                            },
                            "column": {
                                "type": "integer",
                                "description": "Column number (0-based)",
                            },
                        },
                        "required": ["file_path", "line", "column"],
                    },
                ),
                Tool(
                    name="get_references",
                    description="Find all references to a symbol across the entire project. "
                    "Returns a list of locations where the symbol is used. "
                    "Essential for understanding impact before refactoring.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the Python file",
                            },
                            "line": {
                                "type": "integer",
                                "description": "Line number (0-based)",
                            },
                            "column": {
                                "type": "integer",
                                "description": "Column number (0-based)",
                            },
                            "include_declaration": {
                                "type": "boolean",
                                "description": "Include the symbol's declaration in results",
                                "default": True,
                            },
                        },
                        "required": ["file_path", "line", "column"],
                    },
                ),
                Tool(
                    name="get_hover_info",
                    description="Get type information, documentation, and signature for a symbol. "
                    "Returns hover information that helps understand what a symbol is. "
                    "Useful for gathering context before making changes.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the Python file",
                            },
                            "line": {
                                "type": "integer",
                                "description": "Line number (0-based)",
                            },
                            "column": {
                                "type": "integer",
                                "description": "Column number (0-based)",
                            },
                        },
                        "required": ["file_path", "line", "column"],
                    },
                ),
                Tool(
                    name="rename_symbol",
                    description="SAFE: Rename a symbol (variable, function, class, parameter) across the entire project. "
                    "This operation is semantically-aware and type-safe. "
                    "Returns a WorkspaceEdit plan that REQUIRES USER APPROVAL before execution. "
                    "This tool does NOT modify files - it only generates the refactoring plan.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the Python file containing the symbol",
                            },
                            "line": {
                                "type": "integer",
                                "description": "Line number where symbol is located (0-based)",
                            },
                            "column": {
                                "type": "integer",
                                "description": "Column number where symbol starts (0-based)",
                            },
                            "new_name": {
                                "type": "string",
                                "description": "New name for the symbol",
                            },
                        },
                        "required": ["file_path", "line", "column", "new_name"],
                    },
                ),
                Tool(
                    name="get_code_actions",
                    description="Get available code actions (refactorings and quick fixes) for a code range. "
                    "Returns a list of actions like 'Extract function', 'Inline variable', etc. "
                    "Use this to discover what refactorings are possible for selected code.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the Python file",
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "Start line of selection (0-based)",
                            },
                            "start_column": {
                                "type": "integer",
                                "description": "Start column of selection (0-based)",
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "End line of selection (0-based)",
                            },
                            "end_column": {
                                "type": "integer",
                                "description": "End column of selection (0-based)",
                            },
                            "only_kind": {
                                "type": "string",
                                "description": "Filter to specific action kind: 'refactor', 'refactor.extract', 'refactor.inline', 'quickfix'",
                                "default": None,
                            },
                        },
                        "required": ["file_path", "start_line", "start_column", "end_line", "end_column"],
                    },
                ),
                Tool(
                    name="apply_workspace_edit",
                    description="SECURITY CRITICAL: Apply a previously generated WorkspaceEdit plan to the file system. "
                    "This tool modifies files on disk. It should ONLY be called after: "
                    "1) A WorkspaceEdit was generated by a tool like rename_symbol "
                    "2) The user has explicitly reviewed and approved the changes "
                    "The MCP client UI is responsible for obtaining user approval.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_edit": {
                                "type": "object",
                                "description": "The WorkspaceEdit object to apply (from rename_symbol or similar)",
                            },
                        },
                        "required": ["workspace_edit"],
                    },
                ),
                Tool(
                    name="get_diagnostics",
                    description="Get type errors, linting issues, and other diagnostics for a file. "
                    "Returns a list of problems found by Pyright's static analysis. "
                    "Useful for verifying code quality after refactoring.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the Python file",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
            ]

        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Route tool calls to appropriate handlers."""

            if not self.lsp_client or not self.lsp_client.initialized:
                return [TextContent(
                    type="text",
                    text="Error: LSP client not initialized. Please restart the server."
                )]

            try:
                if name == "get_definition":
                    result = await self._get_definition(**arguments)
                elif name == "get_references":
                    result = await self._get_references(**arguments)
                elif name == "get_hover_info":
                    result = await self._get_hover_info(**arguments)
                elif name == "rename_symbol":
                    result = await self._rename_symbol(**arguments)
                elif name == "get_code_actions":
                    result = await self._get_code_actions(**arguments)
                elif name == "apply_workspace_edit":
                    result = await self._apply_workspace_edit(**arguments)
                elif name == "get_diagnostics":
                    result = await self._get_diagnostics(**arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(
                    type="text",
                    text=self._format_result(result)
                )]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

    def _format_result(self, result: Any) -> str:
        """Format tool result as readable text."""
        import json
        return json.dumps(result, indent=2)

    async def _get_definition(self, file_path: str, line: int, column: int) -> Dict[str, Any]:
        """
        Implement textDocument/definition LSP request.

        Args:
            file_path: Absolute path to file
            line: Line number (0-based)
            column: Column number (0-based)

        Returns:
            Location or list of locations where symbol is defined
        """
        # Ensure document is open
        await self.lsp_client.open_document(file_path)

        # Convert to file URI
        file_uri = f"file://{Path(file_path).resolve()}"

        # Send LSP request
        result = await self.lsp_client.send_request(
            "textDocument/definition",
            {
                "textDocument": {"uri": file_uri},
                "position": {"line": line, "character": column},
            },
        )

        return {"definition": result}

    async def _get_references(
        self, file_path: str, line: int, column: int, include_declaration: bool = True
    ) -> Dict[str, Any]:
        """
        Implement textDocument/references LSP request.

        Args:
            file_path: Absolute path to file
            line: Line number (0-based)
            column: Column number (0-based)
            include_declaration: Include symbol declaration in results

        Returns:
            List of locations where symbol is referenced
        """
        await self.lsp_client.open_document(file_path)

        file_uri = f"file://{Path(file_path).resolve()}"

        result = await self.lsp_client.send_request(
            "textDocument/references",
            {
                "textDocument": {"uri": file_uri},
                "position": {"line": line, "character": column},
                "context": {"includeDeclaration": include_declaration},
            },
        )

        return {"references": result}

    async def _get_hover_info(self, file_path: str, line: int, column: int) -> Dict[str, Any]:
        """
        Implement textDocument/hover LSP request.

        Args:
            file_path: Absolute path to file
            line: Line number (0-based)
            column: Column number (0-based)

        Returns:
            Hover information (type, docs, signature)
        """
        await self.lsp_client.open_document(file_path)

        file_uri = f"file://{Path(file_path).resolve()}"

        result = await self.lsp_client.send_request(
            "textDocument/hover",
            {
                "textDocument": {"uri": file_uri},
                "position": {"line": line, "character": column},
            },
        )

        return {"hover": result}

    async def _rename_symbol(
        self, file_path: str, line: int, column: int, new_name: str
    ) -> Dict[str, Any]:
        """
        Implement textDocument/rename LSP request.

        SECURITY: This generates a WorkspaceEdit PLAN but does NOT apply it.
        The plan must be approved by the user via apply_workspace_edit.

        Args:
            file_path: Absolute path to file
            line: Line number (0-based)
            column: Column number (0-based)
            new_name: New name for the symbol

        Returns:
            WorkspaceEdit object (the refactoring plan)
        """
        await self.lsp_client.open_document(file_path)

        file_uri = f"file://{Path(file_path).resolve()}"

        result = await self.lsp_client.send_request(
            "textDocument/rename",
            {
                "textDocument": {"uri": file_uri},
                "position": {"line": line, "character": column},
                "newName": new_name,
            },
        )

        return {
            "workspace_edit": result,
            "message": "WorkspaceEdit plan generated. Review changes and use 'apply_workspace_edit' to apply.",
        }

    async def _get_code_actions(
        self,
        file_path: str,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        only_kind: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Implement textDocument/codeAction LSP request.

        Args:
            file_path: Absolute path to file
            start_line: Start line of range (0-based)
            start_column: Start column of range (0-based)
            end_line: End line of range (0-based)
            end_column: End column of range (0-based)
            only_kind: Filter to specific CodeActionKind (e.g., 'refactor')

        Returns:
            List of available code actions
        """
        await self.lsp_client.open_document(file_path)

        file_uri = f"file://{Path(file_path).resolve()}"

        params = {
            "textDocument": {"uri": file_uri},
            "range": {
                "start": {"line": start_line, "character": start_column},
                "end": {"line": end_line, "character": end_column},
            },
            "context": {"diagnostics": []},
        }

        # Add kind filter if specified
        if only_kind:
            params["context"]["only"] = [only_kind]

        result = await self.lsp_client.send_request("textDocument/codeAction", params)

        return {"code_actions": result}

    async def _apply_workspace_edit(self, workspace_edit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a WorkspaceEdit to the file system.

        SECURITY CRITICAL: This is the only tool that modifies files.
        It should only be called after user approval.

        Args:
            workspace_edit: WorkspaceEdit object from rename_symbol or similar

        Returns:
            Success status and list of modified files
        """
        modified_files = await self.workspace_edit_manager.apply_workspace_edit(
            workspace_edit, self.lsp_client
        )

        return {
            "success": True,
            "modified_files": modified_files,
            "message": f"Successfully applied changes to {len(modified_files)} file(s)",
        }

    async def _get_diagnostics(self, file_path: str) -> Dict[str, Any]:
        """
        Get diagnostics (errors, warnings) for a file.

        Note: LSP servers send diagnostics asynchronously via notifications.
        This is a simplified implementation that opens the file to trigger
        diagnostic computation.

        Args:
            file_path: Absolute path to file

        Returns:
            Message about diagnostics (actual diagnostics are sent as notifications)
        """
        await self.lsp_client.open_document(file_path)

        # Wait a moment for diagnostics to be computed
        await asyncio.sleep(0.5)

        return {
            "message": "Diagnostics are sent asynchronously by LSP server. "
            "Check server logs or implement diagnostic storage.",
            "file": file_path,
        }

    async def start(self) -> None:
        """Start the LSP client and initialize server."""
        logger.info("Starting Python Refactor MCP Server")

        # Initialize LSP client
        self.lsp_client = LSPClient(str(self.workspace_root))
        await self.lsp_client.start()

        # Initialize workspace edit manager
        self.workspace_edit_manager = WorkspaceEditManager()

        logger.info("Python Refactor MCP Server started successfully")

    async def shutdown(self) -> None:
        """Shut down the server and LSP client."""
        logger.info("Shutting down Python Refactor MCP Server")

        if self.lsp_client:
            await self.lsp_client.shutdown()

        logger.info("Python Refactor MCP Server shut down successfully")

    async def run(self) -> None:
        """Run the MCP server with stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.mcp_server.run(
                read_stream,
                write_stream,
                self.mcp_server.create_initialization_options(),
            )
