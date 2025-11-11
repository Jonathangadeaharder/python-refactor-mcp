"""
WorkspaceEdit Manager: Safe application of LSP WorkspaceEdit objects.

This module implements the critical security boundary for file modifications.
It applies WorkspaceEdit objects to the file system and maintains LSP synchronization.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WorkspaceEditManager:
    """
    Manages safe application of WorkspaceEdit objects to the file system.

    Security Model:
    - Only modifies files after explicit user approval
    - Validates all file paths before writing
    - Maintains LSP state synchronization after changes
    - Provides detailed logging of all modifications
    """

    def __init__(self):
        """Initialize WorkspaceEdit manager."""
        pass

    async def apply_workspace_edit(
        self, workspace_edit: Dict[str, Any], lsp_client: Any
    ) -> List[str]:
        """
        Apply a WorkspaceEdit to the file system.

        This method:
        1. Parses the WorkspaceEdit structure
        2. Applies text edits to each affected file
        3. Notifies LSP server of changes via didChange
        4. Returns list of modified files

        Args:
            workspace_edit: LSP WorkspaceEdit object
            lsp_client: LSP client for synchronization

        Returns:
            List of modified file paths

        Raises:
            ValueError: If WorkspaceEdit structure is invalid
            IOError: If file operations fail
        """
        modified_files = []

        # WorkspaceEdit can have two formats:
        # 1. "changes": { "file:///path": [TextEdit, ...] }
        # 2. "documentChanges": [TextDocumentEdit, ...]

        if "changes" in workspace_edit:
            # Format 1: Simple changes map
            changes = workspace_edit["changes"]

            for uri, text_edits in changes.items():
                file_path = self._uri_to_path(uri)
                await self._apply_text_edits(file_path, text_edits, lsp_client)
                modified_files.append(str(file_path))

        elif "documentChanges" in workspace_edit:
            # Format 2: Document changes array
            document_changes = workspace_edit["documentChanges"]

            for change in document_changes:
                if "textDocument" in change:
                    # This is a TextDocumentEdit
                    uri = change["textDocument"]["uri"]
                    file_path = self._uri_to_path(uri)
                    text_edits = change.get("edits", [])
                    await self._apply_text_edits(file_path, text_edits, lsp_client)
                    modified_files.append(str(file_path))
                elif "kind" in change:
                    # This is a ResourceOperation (create, rename, delete)
                    # For now, we'll log and skip these
                    logger.warning(
                        f"Skipping resource operation: {change.get('kind')}. "
                        "File creation/deletion/rename not yet implemented."
                    )

        else:
            raise ValueError("Invalid WorkspaceEdit: missing 'changes' or 'documentChanges'")

        logger.info(f"Applied WorkspaceEdit to {len(modified_files)} file(s)")
        return modified_files

    async def _apply_text_edits(
        self, file_path: Path, text_edits: List[Dict[str, Any]], lsp_client: Any
    ) -> None:
        """
        Apply a list of TextEdit objects to a single file.

        TextEdit format:
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 5}
            },
            "newText": "hello"
        }

        Args:
            file_path: Path to file to modify
            text_edits: List of TextEdit objects
            lsp_client: LSP client for synchronization
        """
        # Validate file exists
        if not file_path.exists():
            raise IOError(f"File does not exist: {file_path}")

        # Read current content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into lines for editing
        lines = content.splitlines(keepends=True)

        # Sort edits by position (reverse order to avoid offset issues)
        # When applying edits, we go from end to start so earlier edits
        # don't invalidate later positions
        sorted_edits = sorted(
            text_edits,
            key=lambda e: (
                e["range"]["start"]["line"],
                e["range"]["start"]["character"],
            ),
            reverse=True,
        )

        # Apply each edit
        for edit in sorted_edits:
            range_obj = edit["range"]
            new_text = edit["newText"]

            start_line = range_obj["start"]["line"]
            start_char = range_obj["start"]["character"]
            end_line = range_obj["end"]["line"]
            end_char = range_obj["end"]["character"]

            # Apply the edit
            lines = self._apply_single_edit(
                lines, start_line, start_char, end_line, end_char, new_text
            )

        # Join lines back into content
        new_content = "".join(lines)

        # Write modified content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"Applied {len(text_edits)} edit(s) to {file_path}")

        # Notify LSP server of the change
        await lsp_client.did_change_document(str(file_path), new_content)

    def _apply_single_edit(
        self,
        lines: List[str],
        start_line: int,
        start_char: int,
        end_line: int,
        end_char: int,
        new_text: str,
    ) -> List[str]:
        """
        Apply a single TextEdit to a list of lines.

        Args:
            lines: List of lines (with line endings)
            start_line: Start line (0-based)
            start_char: Start character (0-based)
            end_line: End line (0-based)
            end_char: End character (0-based)
            new_text: Replacement text

        Returns:
            Modified list of lines
        """
        # Handle edge case: empty file
        if not lines:
            lines = [""]

        # Ensure we have enough lines
        while len(lines) <= max(start_line, end_line):
            lines.append("\n")

        # Extract the affected portion
        if start_line == end_line:
            # Single line edit
            line = lines[start_line]
            # Remove line ending temporarily
            line_ending = ""
            if line.endswith("\r\n"):
                line_ending = "\r\n"
                line = line[:-2]
            elif line.endswith("\n"):
                line_ending = "\n"
                line = line[:-1]

            # Apply edit
            before = line[:start_char]
            after = line[end_char:]
            new_line = before + new_text + after

            # Handle if new_text contains newlines
            if "\n" in new_line:
                # Split into multiple lines
                new_lines = new_line.split("\n")
                # Add line endings
                new_lines_with_endings = [l + line_ending for l in new_lines[:-1]]
                new_lines_with_endings.append(new_lines[-1] + line_ending)
                # Replace the single line with multiple lines
                lines = lines[:start_line] + new_lines_with_endings + lines[start_line + 1 :]
            else:
                # Single line replacement
                lines[start_line] = new_line + line_ending

        else:
            # Multi-line edit
            # Get content before edit
            start_line_content = lines[start_line]
            start_line_ending = ""
            if start_line_content.endswith("\r\n"):
                start_line_ending = "\r\n"
                start_line_content = start_line_content[:-2]
            elif start_line_content.endswith("\n"):
                start_line_ending = "\n"
                start_line_content = start_line_content[:-1]
            before = start_line_content[:start_char]

            # Get content after edit
            end_line_content = lines[end_line]
            end_line_ending = ""
            if end_line_content.endswith("\r\n"):
                end_line_ending = "\r\n"
                end_line_content = end_line_content[:-2]
            elif end_line_content.endswith("\n"):
                end_line_ending = "\n"
                end_line_content = end_line_content[:-1]
            after = end_line_content[end_char:]

            # Create new content
            new_content = before + new_text + after

            # Handle newlines in new content
            if "\n" in new_content:
                new_lines = new_content.split("\n")
                new_lines_with_endings = [l + start_line_ending for l in new_lines[:-1]]
                new_lines_with_endings.append(new_lines[-1] + end_line_ending)
                # Replace affected lines
                lines = lines[:start_line] + new_lines_with_endings + lines[end_line + 1 :]
            else:
                # Single line result
                lines = (
                    lines[:start_line]
                    + [new_content + start_line_ending]
                    + lines[end_line + 1 :]
                )

        return lines

    def _uri_to_path(self, uri: str) -> Path:
        """
        Convert file:// URI to Path object.

        Args:
            uri: File URI (e.g., "file:///path/to/file.py")

        Returns:
            Path object

        Raises:
            ValueError: If URI is not a file:// URI
        """
        parsed = urlparse(uri)

        if parsed.scheme != "file":
            raise ValueError(f"Only file:// URIs are supported, got: {uri}")

        # Handle Windows paths
        path = parsed.path
        if path.startswith("/") and len(path) > 2 and path[2] == ":":
            # Windows path like "/C:/Users/..."
            path = path[1:]

        return Path(path).resolve()
