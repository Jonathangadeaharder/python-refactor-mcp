"""
Unit tests for MCP server.

Tests the MCP server implementation and tool registration.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from python_refactor_mcp.mcp_server import PythonRefactorMCPServer


class TestPythonRefactorMCPServer:
    """Test suite for PythonRefactorMCPServer."""

    def test_initialization(self, tmp_path):
        """Test MCP server initialization."""
        server = PythonRefactorMCPServer(str(tmp_path))

        assert server.workspace_root == tmp_path.resolve()
        assert server.lsp_client is None
        assert server.workspace_edit_manager is None
        assert server.mcp_server is not None

    def test_workspace_path_resolution(self, tmp_path):
        """Test that workspace paths are resolved correctly."""
        subdir = tmp_path / "project"
        subdir.mkdir()

        server = PythonRefactorMCPServer(str(subdir))

        assert server.workspace_root == subdir.resolve()
        assert server.workspace_root.exists()
        assert server.workspace_root.is_dir()

    def test_server_name(self, tmp_path):
        """Test that MCP server has correct name."""
        server = PythonRefactorMCPServer(str(tmp_path))

        # The server name should be "python-refactor-mcp"
        assert server.mcp_server.name == "python-refactor-mcp"

    @pytest.mark.asyncio
    async def test_startup_initializes_components(self, tmp_path):
        """Test that startup initializes LSP client and workspace manager."""
        server = PythonRefactorMCPServer(str(tmp_path))

        # Mock the LSP client start method
        with patch("python_refactor_mcp.mcp_server.LSPClient") as mock_lsp:
            mock_lsp_instance = AsyncMock()
            mock_lsp.return_value = mock_lsp_instance

            await server.startup()

            assert server.lsp_client is not None
            assert server.workspace_edit_manager is not None

    @pytest.mark.asyncio
    async def test_shutdown_stops_lsp_client(self, tmp_path):
        """Test that shutdown stops the LSP client."""
        server = PythonRefactorMCPServer(str(tmp_path))

        # Create a mock LSP client
        server.lsp_client = AsyncMock()

        await server.shutdown()

        # Verify stop was called
        server.lsp_client.stop.assert_called_once()

    def test_file_path_validation(self, tmp_path):
        """Test file path validation logic."""
        server = PythonRefactorMCPServer(str(tmp_path))

        # Create test files
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("# test")

        # Valid file should work
        validated = server._validate_file_path(str(valid_file))
        assert validated == valid_file.resolve()

    def test_position_validation(self, tmp_path):
        """Test position (line/column) validation."""
        server = PythonRefactorMCPServer(str(tmp_path))

        # Valid positions
        assert server._validate_position(0, 0) == (0, 0)
        assert server._validate_position(10, 5) == (10, 5)

        # Invalid positions should raise
        with pytest.raises(ValueError):
            server._validate_position(-1, 0)

        with pytest.raises(ValueError):
            server._validate_position(0, -1)
