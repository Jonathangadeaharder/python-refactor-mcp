"""
Unit tests for LSP client.

Tests the JSON-RPC client that communicates with Pyright language server.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from python_refactor_mcp.lsp_client import LSPClient


class TestLSPClient:
    """Test suite for LSPClient."""

    def test_initialization(self, tmp_path):
        """Test LSPClient initialization."""
        client = LSPClient(str(tmp_path))

        assert client.workspace_root == tmp_path.resolve()
        assert client.workspace_uri == f"file://{tmp_path.resolve()}"
        assert client.process is None
        assert client.initialized is False
        assert client.message_id == 0
        assert len(client.pending_requests) == 0

    def test_workspace_uri_normalization(self, tmp_path):
        """Test that workspace paths are normalized correctly."""
        # Create a subdirectory
        subdir = tmp_path / "test_project"
        subdir.mkdir()

        client = LSPClient(str(subdir))

        assert client.workspace_root == subdir.resolve()
        assert str(client.workspace_root).endswith("test_project")

    @pytest.mark.asyncio
    async def test_start_without_pyright_fails(self, tmp_path):
        """Test that starting without pyright-langserver raises error."""
        client = LSPClient(str(tmp_path))

        with patch.object(client, "_find_pyright", return_value=None):
            with pytest.raises(RuntimeError, match="pyright-langserver not found"):
                await client.start()

    def test_uri_to_path_conversion(self, tmp_path):
        """Test URI to path conversion."""
        client = LSPClient(str(tmp_path))

        test_file = tmp_path / "test.py"
        uri = f"file://{test_file}"

        path = client._uri_to_path(uri)
        assert path == test_file.resolve()

    def test_path_to_uri_conversion(self, tmp_path):
        """Test path to URI conversion."""
        client = LSPClient(str(tmp_path))

        test_file = tmp_path / "test.py"
        uri = client._path_to_uri(str(test_file))

        assert uri.startswith("file://")
        assert str(test_file.resolve()) in uri

    def test_next_message_id_increments(self, tmp_path):
        """Test that message IDs increment correctly."""
        client = LSPClient(str(tmp_path))

        id1 = client._next_message_id()
        id2 = client._next_message_id()
        id3 = client._next_message_id()

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    @pytest.mark.asyncio
    async def test_stop_without_start(self, tmp_path):
        """Test that stopping unstarted client doesn't crash."""
        client = LSPClient(str(tmp_path))

        # Should not raise
        await client.stop()

    def test_open_documents_tracking(self, tmp_path):
        """Test that open documents are tracked correctly."""
        client = LSPClient(str(tmp_path))

        assert len(client.open_documents) == 0

        # Simulate opening documents
        client.open_documents.add("file:///test1.py")
        client.open_documents.add("file:///test2.py")

        assert len(client.open_documents) == 2
        assert "file:///test1.py" in client.open_documents
        assert "file:///test2.py" in client.open_documents
