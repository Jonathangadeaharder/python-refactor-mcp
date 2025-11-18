# Python Refactor MCP Package

This package implements the MCP-LSP bridge server for semantically-aware Python refactoring.

## Modules

### Core Components

- `__main__.py` - Entry point for the MCP server
- `mcp_server.py` - MCP server implementation and tool definitions
- `lsp_client.py` - LSP JSON-RPC client for communicating with Pyright
- `workspace_edit.py` - WorkspaceEdit application logic

## Architecture

The package follows a layered architecture:

1. **MCP Layer** (`mcp_server.py`) - Exposes tools to AI agents via MCP protocol
2. **LSP Bridge** (`lsp_client.py`) - Manages communication with Pyright LSP server
3. **Workspace Management** (`workspace_edit.py`) - Handles safe file modifications

## Usage

Run the server with:
```bash
python -m python_refactor_mcp /path/to/workspace
```

See the main [README.md](../../README.md) for full documentation and configuration.
