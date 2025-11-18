"""
Unit tests for workspace edit manager.

Tests the safe application of LSP WorkspaceEdit objects to the file system.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from python_refactor_mcp.workspace_edit import WorkspaceEditManager


class TestWorkspaceEditManager:
    """Test suite for WorkspaceEditManager."""

    def test_initialization(self):
        """Test WorkspaceEditManager initialization."""
        manager = WorkspaceEditManager()
        assert manager is not None

    def test_uri_to_path_conversion(self):
        """Test URI to path conversion."""
        manager = WorkspaceEditManager()

        # Test file URI
        uri = "file:///home/user/test.py"
        path = manager._uri_to_path(uri)

        assert isinstance(path, Path)
        assert str(path).endswith("test.py")

    def test_uri_to_path_invalid_scheme(self):
        """Test that non-file URIs are rejected."""
        manager = WorkspaceEditManager()

        with pytest.raises(ValueError, match="Only file:// URIs are supported"):
            manager._uri_to_path("http://example.com/test.py")

    def test_apply_single_edit_single_line(self):
        """Test applying a single edit to a single line."""
        manager = WorkspaceEditManager()

        lines = ["hello world\n"]
        result = manager._apply_single_edit(lines, 0, 0, 0, 5, "hi")

        assert result == ["hi world\n"]

    def test_apply_single_edit_multi_line(self):
        """Test applying an edit across multiple lines."""
        manager = WorkspaceEditManager()

        lines = ["line one\n", "line two\n", "line three\n"]
        # Replace "one\nline two\n" with "1\n2\n"
        result = manager._apply_single_edit(lines, 0, 5, 1, 8, "1\n2")

        assert result[0] == "line 1\n"
        assert result[1] == "2 three\n"

    def test_apply_single_edit_empty_file(self):
        """Test applying edit to empty file."""
        manager = WorkspaceEditManager()

        lines = []
        result = manager._apply_single_edit(lines, 0, 0, 0, 0, "new content")

        assert len(result) > 0
        assert "new content" in result[0]

    @pytest.mark.asyncio
    async def test_apply_workspace_edit_invalid_structure(self):
        """Test that invalid WorkspaceEdit structure raises error."""
        manager = WorkspaceEditManager()
        mock_lsp = AsyncMock()

        # Empty workspace edit (no 'changes' or 'documentChanges')
        invalid_edit = {}

        with pytest.raises(ValueError, match="Invalid WorkspaceEdit"):
            await manager.apply_workspace_edit(invalid_edit, mock_lsp)

    @pytest.mark.asyncio
    async def test_apply_workspace_edit_with_changes(self, tmp_path):
        """Test applying workspace edit with 'changes' format."""
        manager = WorkspaceEditManager()
        mock_lsp = AsyncMock()

        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("hello world")

        # Create workspace edit
        workspace_edit = {
            "changes": {
                f"file://{test_file}": [
                    {
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": 5},
                        },
                        "newText": "hi",
                    }
                ]
            }
        }

        modified = await manager.apply_workspace_edit(workspace_edit, mock_lsp)

        assert len(modified) == 1
        assert str(test_file) in modified[0]

        # Verify file was modified
        content = test_file.read_text()
        assert content == "hi world"

    @pytest.mark.asyncio
    async def test_apply_workspace_edit_with_document_changes(self, tmp_path):
        """Test applying workspace edit with 'documentChanges' format."""
        manager = WorkspaceEditManager()
        mock_lsp = AsyncMock()

        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("original")

        # Create workspace edit
        workspace_edit = {
            "documentChanges": [
                {
                    "textDocument": {"uri": f"file://{test_file}"},
                    "edits": [
                        {
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": 8},
                            },
                            "newText": "modified",
                        }
                    ],
                }
            ]
        }

        modified = await manager.apply_workspace_edit(workspace_edit, mock_lsp)

        assert len(modified) == 1

        # Verify file was modified
        content = test_file.read_text()
        assert content == "modified"

    @pytest.mark.asyncio
    async def test_apply_text_edits_nonexistent_file(self):
        """Test that applying edits to nonexistent file raises error."""
        manager = WorkspaceEditManager()
        mock_lsp = AsyncMock()

        fake_path = Path("/nonexistent/file.py")
        edits = []

        with pytest.raises(IOError, match="File does not exist"):
            await manager._apply_text_edits(fake_path, edits, mock_lsp)

    @pytest.mark.asyncio
    async def test_lsp_notification_after_edit(self, tmp_path):
        """Test that LSP is notified after file edits."""
        manager = WorkspaceEditManager()
        mock_lsp = AsyncMock()

        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("hello")

        # Apply edit
        edits = [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 5},
                },
                "newText": "hi",
            }
        ]

        await manager._apply_text_edits(test_file, edits, mock_lsp)

        # Verify LSP was notified
        mock_lsp.did_change_document.assert_called_once()
        call_args = mock_lsp.did_change_document.call_args
        assert str(test_file) in call_args[0][0]
        assert "hi" in call_args[0][1]
