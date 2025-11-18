# Unit Tests for Python Refactor MCP

This directory contains unit tests for the `python_refactor_mcp` package, mirroring the source structure.

## Test Files

- `test_lsp_client.py` - Tests for LSP client (JSON-RPC communication)
- `test_mcp_server.py` - Tests for MCP server (tool registration and handling)
- `test_workspace_edit.py` - Tests for workspace edit manager (file modifications)
- `test___main__.py` - Tests for entry point

## Running

```bash
# Run all unit tests
pytest tests/src/

# Run specific module tests
pytest tests/src/python_refactor_mcp/test_lsp_client.py
```

See the main [tests README](../../README.md) for more information.
