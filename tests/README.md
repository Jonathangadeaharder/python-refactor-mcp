# Tests

This directory contains the test suite for the Python Refactor MCP server.

## Test Structure

- `test_integration.py` - End-to-end integration tests
- `test_lsp_client.py` - Unit tests for LSP client
- `test_mcp_server.py` - Unit tests for MCP server
- `test_workspace_edit.py` - Unit tests for workspace edit functionality
- `example_project/` - Test fixtures and example Python project

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_integration.py
```

## Test Coverage

See [TEST_COVERAGE.md](../TEST_COVERAGE.md) for detailed test coverage information.

## CI/CD

Tests run automatically on every push via GitHub Actions. See `.github/workflows/test-and-log.yml` for the test workflow configuration.
