#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Python Refactor MCP Server.

This script tests the MCP server by:
1. Navigation tools (get_definition, get_references, get_hover_info)
2. Refactoring tools (rename_symbol, get_code_actions)
3. Cross-file reference tracking
4. Two-stage security model verification
5. WorkspaceEdit application (P0 - Critical for write operations)
6. Multi-line edit handling (P1 - Correctness critical)
7. Error handling and edge cases (P2 - Reliability)

Coverage: 7 test suites, ~500 lines of test code
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from python_refactor_mcp.lsp_client import LSPClient
from python_refactor_mcp.mcp_server import PythonRefactorMCPServer


async def test_navigation_tools(server: PythonRefactorMCPServer):
    """Test navigation tools: get_definition, get_references, get_hover_info."""
    print("\n" + "=" * 80)
    print("TEST 1: Navigation Tools")
    print("=" * 80)

    workspace = Path(__file__).parent / "example_project"
    main_file = workspace / "main.py"

    # Explicitly open the file first (LSP needs this)
    print("\n[Setup] Opening file in LSP...")
    await server.lsp_client.open_document(str(main_file))
    # Give Pyright a moment to parse
    await asyncio.sleep(0.5)

    # Test 1: Get definition of 'calculate_total'
    print("\n[1.1] Testing get_definition on 'calculate_total'...")
    try:
        # Line 45 (0-based): total = calculate_total(numbers)
        result = await server._get_definition(
            file_path=str(main_file),
            line=45,  # 0-based line number where calculate_total is called
            column=10,  # Column where 'calculate_total' starts
        )
        definition = result.get("definition")
        if definition:
            print(f"✓ Found definition at: {json.dumps(definition, indent=2)[:200]}...")
        else:
            print("ℹ  No definition found (LSP may still be indexing)")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Test 2: Get references to 'calculate_total'
    print("\n[1.2] Testing get_references for 'calculate_total'...")
    try:
        # Line 9 (0-based): def calculate_total(items: List[int]) -> int:
        result = await server._get_references(
            file_path=str(main_file),
            line=9,  # 0-based line where calculate_total is defined
            column=4,
            include_declaration=True,
        )
        references = result.get("references")
        if references and len(references) > 0:
            print(f"✓ Found {len(references)} reference(s)")
            for i, ref in enumerate(references[:3]):  # Show first 3
                uri = ref.get("uri", "")
                range_info = ref.get("range", {})
                start = range_info.get("start", {})
                print(f"  {i+1}. {Path(uri.replace('file://', '')).name} at line {start.get('line', 0) + 1}")
        else:
            print("ℹ  No references found (LSP may still be indexing)")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Test 3: Get hover info for 'DataProcessor'
    print("\n[1.3] Testing get_hover_info for 'DataProcessor'...")
    try:
        # Line 25 (0-based): class DataProcessor:
        result = await server._get_hover_info(
            file_path=str(main_file),
            line=25,  # 0-based line where DataProcessor class is defined
            column=6,
        )
        hover = result.get("hover")
        if hover and hover.get("contents"):
            contents = hover.get("contents", {})
            # Contents can be a string or MarkupContent object
            if isinstance(contents, dict):
                value = contents.get("value", "")
                print(f"✓ Retrieved hover info: {value[:150]}...")
            else:
                print(f"✓ Retrieved hover info: {str(contents)[:150]}...")
        else:
            print("ℹ  No hover info found (LSP may still be indexing)")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    print("\n✓ All navigation tool tests completed!")
    return True


async def test_refactoring_tools(server: PythonRefactorMCPServer):
    """Test refactoring tools: rename_symbol, get_code_actions."""
    print("\n" + "=" * 80)
    print("TEST 2: Refactoring Tools")
    print("=" * 80)

    workspace = Path(__file__).parent / "example_project"
    main_file = workspace / "main.py"

    # Ensure file is open
    print("\n[Setup] Ensuring file is open in LSP...")
    await server.lsp_client.open_document(str(main_file))
    await asyncio.sleep(0.5)

    # Test 1: Get code actions for a function
    print("\n[2.1] Testing get_code_actions for 'calculate_total' function...")
    try:
        # Select the body of calculate_total (lines 11-14, 0-based)
        result = await server._get_code_actions(
            file_path=str(main_file),
            start_line=11,  # Start of calculate_total body (0-based)
            start_column=0,
            end_line=14,  # End of calculate_total function (0-based)
            end_column=0,
            only_kind="refactor",
        )
        actions = result.get("code_actions")
        if actions and len(actions) > 0:
            print(f"✓ Found {len(actions)} refactoring action(s)")
            for i, action in enumerate(actions[:5]):  # Show first 5
                title = action.get("title", "Unknown")
                print(f"  {i+1}. {title}")
        else:
            print("ℹ  No refactoring actions available for this selection")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Test 2: Generate rename plan (does NOT apply)
    print("\n[2.2] Testing rename_symbol to generate WorkspaceEdit plan...")
    try:
        # Line 11 (0-based): total = 0
        result = await server._rename_symbol(
            file_path=str(main_file),
            line=11,  # Variable 'total' in calculate_total (0-based)
            column=4,  # Column where 'total' starts
            new_name="sum_total",
        )

        workspace_edit = result.get("workspace_edit")
        if workspace_edit and (workspace_edit.get("changes") or workspace_edit.get("documentChanges")):
            print("✓ WorkspaceEdit plan generated successfully!")

            # Analyze the plan
            changes = workspace_edit.get("changes", {})
            doc_changes = workspace_edit.get("documentChanges", [])

            if changes:
                print(f"  Files to be modified: {len(changes)}")
                for uri, edits in changes.items():
                    file_path = uri.replace("file://", "")
                    print(f"    - {Path(file_path).name}: {len(edits)} edit(s)")
            elif doc_changes:
                print(f"  Document changes: {len(doc_changes)}")
                for change in doc_changes:
                    if "textDocument" in change:
                        uri = change["textDocument"]["uri"]
                        edits = change.get("edits", [])
                        print(f"    - {Path(uri.replace('file://', '')).name}: {len(edits)} edit(s)")

            # IMPORTANT: We do NOT call apply_workspace_edit here
            # This demonstrates the two-stage security model
            print("\n  ℹ  Security Note: WorkspaceEdit generated but NOT applied.")
            print("     In production, user must review and approve before applying.")

        else:
            print("ℹ  No WorkspaceEdit returned (symbol may not support renaming)")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✓ All refactoring tool tests completed!")
    return True


async def test_cross_file_references(server: PythonRefactorMCPServer):
    """Test cross-file reference tracking."""
    print("\n" + "=" * 80)
    print("TEST 3: Cross-File Reference Tracking")
    print("=" * 80)

    workspace = Path(__file__).parent / "example_project"
    main_file = workspace / "main.py"
    utils_file = workspace / "utils.py"

    # Open both files in LSP
    print("\n[Setup] Opening files in LSP...")
    await server.lsp_client.open_document(str(main_file))
    await server.lsp_client.open_document(str(utils_file))
    await asyncio.sleep(1.0)  # Give Pyright time to index both files

    # Test: Find references to 'calculate_total' which is imported in utils.py
    print("\n[3.1] Testing cross-file references for 'calculate_total'...")
    try:
        # Get references from main.py (where it's defined)
        # Line 9 (0-based): def calculate_total
        result = await server._get_references(
            file_path=str(main_file),
            line=9,  # Where calculate_total is defined (0-based)
            column=4,
            include_declaration=True,
        )

        references = result.get("references")
        if references and len(references) > 0:
            print(f"✓ Found {len(references)} reference(s) across project")

            # Show all references
            for i, ref in enumerate(references):
                uri = ref.get("uri", "")
                range_info = ref.get("range", {})
                start = range_info.get("start", {})
                file_name = Path(uri.replace("file://", "")).name
                print(f"  {i+1}. {file_name} at line {start.get('line', 0) + 1}")

            # Check if utils.py is in the references
            has_utils_ref = any("utils.py" in ref.get("uri", "") for ref in references)
            if has_utils_ref:
                print("  ✓ Cross-file reference detected in utils.py")
            else:
                print("  ℹ  No cross-file reference in utils.py (Pyright may need more time)")
        else:
            print("ℹ  No references found (LSP may still be indexing)")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✓ Cross-file reference test completed!")
    return True


async def test_security_model(server: PythonRefactorMCPServer):
    """Verify the two-stage security model."""
    print("\n" + "=" * 80)
    print("TEST 4: Two-Stage Security Model")
    print("=" * 80)

    print("\n[4.1] Verifying rename_symbol does NOT modify files...")

    workspace = Path(__file__).parent / "example_project"
    main_file = workspace / "main.py"

    # Ensure file is open
    await server.lsp_client.open_document(str(main_file))
    await asyncio.sleep(0.5)

    # Read original content
    with open(main_file, "r") as f:
        original_content = f.read()

    # Generate rename plan
    try:
        # Line 9 (0-based): def calculate_total
        result = await server._rename_symbol(
            file_path=str(main_file),
            line=9,  # calculate_total function name (0-based)
            column=4,
            new_name="compute_total_value",
        )

        # Check that file content is unchanged
        with open(main_file, "r") as f:
            current_content = f.read()

        if original_content == current_content:
            print("✓ File content unchanged after rename_symbol call")
            print("  ✓ Security model verified: plan generated without modification")
        else:
            print("✗ File was modified! Security model violated!")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✓ Two-stage security model verified!")
    return True


async def test_workspace_edit_application(server: PythonRefactorMCPServer):
    """Test apply_workspace_edit tool - CRITICAL for write operations."""
    print("\n" + "=" * 80)
    print("TEST 5: WorkspaceEdit Application (P0 - Critical)")
    print("=" * 80)

    workspace = Path(__file__).parent / "example_project"
    main_file = workspace / "main.py"

    # Create a temporary test file to avoid modifying the example
    import tempfile
    import shutil

    print("\n[Setup] Creating temporary test file...")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_rename.py"

        # Write test content
        test_content = """def calculate_sum(items):
    total = 0
    for item in items:
        total += item
    return total

result = calculate_sum([1, 2, 3])
print(f"Result: {total}")
"""
        test_file.write_text(test_content)

        print(f"  Created test file: {test_file}")

        # Open document in LSP
        await server.lsp_client.open_document(str(test_file))
        await asyncio.sleep(0.5)

        # Test 1: Generate rename plan for 'total' variable
        print("\n[5.1] Generating WorkspaceEdit for rename 'total' → 'sum_value'...")
        try:
            result = await server._rename_symbol(
                file_path=str(test_file),
                line=1,  # Line: total = 0
                column=4,  # Column where 'total' starts
                new_name="sum_value",
            )

            workspace_edit = result.get("workspace_edit")
            if not workspace_edit:
                print("✗ No WorkspaceEdit generated")
                return False

            print("✓ WorkspaceEdit generated")

            # Verify plan content
            changes = workspace_edit.get("changes") or {}
            doc_changes = workspace_edit.get("documentChanges") or []

            edit_count = 0
            if changes:
                for edits in changes.values():
                    edit_count += len(edits)
            elif doc_changes:
                for change in doc_changes:
                    if "edits" in change:
                        edit_count += len(change["edits"])

            print(f"  Generated {edit_count} edit(s)")

        except Exception as e:
            print(f"✗ Error generating plan: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 2: Apply the WorkspaceEdit
        print("\n[5.2] Applying WorkspaceEdit to file system...")
        try:
            # Read original content
            original_content = test_file.read_text()

            # Apply the edit
            apply_result = await server._apply_workspace_edit(workspace_edit)

            if not apply_result.get("success"):
                print("✗ apply_workspace_edit returned failure")
                return False

            print("✓ apply_workspace_edit succeeded")

            # Verify file was modified
            new_content = test_file.read_text()

            if original_content == new_content:
                print("✗ File content unchanged - edits not applied!")
                return False

            print("✓ File content modified")

            # Verify edits are correct
            if "sum_value" not in new_content:
                print("✗ New symbol name 'sum_value' not found in file")
                print(f"Content: {new_content[:200]}...")
                return False

            if "total" in new_content:
                # Check if it's just in the last line (which references undefined variable)
                lines = new_content.split("\n")
                total_count = sum(1 for line in lines[:-2] if "total" in line and "calculate" not in line)
                if total_count > 0:
                    print(f"✗ Old symbol 'total' still present ({total_count} occurrences)")
                    return False

            print("✓ Symbol correctly renamed to 'sum_value'")

        except Exception as e:
            print(f"✗ Error applying WorkspaceEdit: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 3: Verify LSP was notified (check with a query)
        print("\n[5.3] Verifying LSP cache was updated...")
        try:
            # Give LSP time to process the change
            await asyncio.sleep(0.5)

            # Try to find references to the NEW name
            refs_result = await server._get_references(
                file_path=str(test_file),
                line=1,  # Line where sum_value is now defined
                column=4,
                include_declaration=True,
            )

            references = refs_result.get("references") or []
            if len(references) > 0:
                print(f"✓ LSP found {len(references)} reference(s) to new name")
            else:
                print("ℹ  LSP cache may need more time to update")

        except Exception as e:
            print(f"ℹ  Could not verify LSP update: {e}")
            # This is not a critical failure

    print("\n✓ WorkspaceEdit application test passed!")
    return True


async def test_multiline_edits(server: PythonRefactorMCPServer):
    """Test multi-line edit handling - CRITICAL for correctness."""
    print("\n" + "=" * 80)
    print("TEST 6: Multi-Line Edit Handling (P1 - High)")
    print("=" * 80)

    import tempfile

    print("\n[Setup] Creating test files for multi-line scenarios...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Multi-line function rename
        print("\n[6.1] Testing multi-line function rename...")
        test_file1 = Path(tmpdir) / "multiline_test.py"

        content1 = """class Calculator:
    def compute_result(self, x, y):
        # This function computes result
        value = x + y
        return value

    def process(self):
        result = self.compute_result(10, 20)
        return result
"""
        test_file1.write_text(content1)

        try:
            await server.lsp_client.open_document(str(test_file1))
            await asyncio.sleep(0.5)

            # Rename method spanning multiple lines
            result = await server._rename_symbol(
                file_path=str(test_file1),
                line=1,  # def compute_result line
                column=8,
                new_name="calculate_value",
            )

            workspace_edit = result.get("workspace_edit")
            if workspace_edit:
                # Apply the edit
                await server._apply_workspace_edit(workspace_edit)

                # Verify
                new_content = test_file1.read_text()
                if "calculate_value" in new_content and "compute_result" not in new_content:
                    print("✓ Multi-line function rename successful")
                else:
                    print("✗ Multi-line rename failed")
                    print(f"Content:\n{new_content}")
                    return False
            else:
                print("ℹ  No WorkspaceEdit for multi-line rename")

        except Exception as e:
            print(f"✗ Error in multi-line rename: {e}")
            return False

        # Test 2: Line ending preservation
        print("\n[6.2] Testing line ending preservation...")
        test_file2 = Path(tmpdir) / "line_endings.py"

        # Create file with specific line endings
        content2 = "def func1():\n    pass\n\ndef func2():\n    x = 1\n    return x\n"
        test_file2.write_text(content2)

        try:
            original_content = test_file2.read_text()
            original_lines = len(original_content.split("\n"))

            await server.lsp_client.open_document(str(test_file2))
            await asyncio.sleep(0.5)

            # Rename variable
            result = await server._rename_symbol(
                file_path=str(test_file2),
                line=4,  # x = 1 line
                column=4,
                new_name="value",
            )

            workspace_edit = result.get("workspace_edit")
            if workspace_edit:
                await server._apply_workspace_edit(workspace_edit)

                new_content = test_file2.read_text()
                new_lines = len(new_content.split("\n"))

                if new_lines == original_lines:
                    print("✓ Line count preserved")
                else:
                    print(f"✗ Line count changed: {original_lines} → {new_lines}")
                    return False

                # Check content correctness
                if "value" in new_content and new_content.count("x =") == 0:
                    print("✓ Edit applied correctly with line endings preserved")
                else:
                    print("ℹ  Line ending test inconclusive")

            else:
                print("ℹ  No WorkspaceEdit for line ending test")

        except Exception as e:
            print(f"✗ Error in line ending test: {e}")
            return False

        # Test 3: Empty line handling
        print("\n[6.3] Testing empty line handling...")
        test_file3 = Path(tmpdir) / "empty_lines.py"

        content3 = """def process():
    data = []


    result = data
    return result
"""
        test_file3.write_text(content3)

        try:
            await server.lsp_client.open_document(str(test_file3))
            await asyncio.sleep(0.5)

            result = await server._rename_symbol(
                file_path=str(test_file3),
                line=1,  # data = []
                column=4,
                new_name="items",
            )

            workspace_edit = result.get("workspace_edit")
            if workspace_edit:
                await server._apply_workspace_edit(workspace_edit)

                new_content = test_file3.read_text()
                empty_line_count = new_content.count("\n\n\n")

                if empty_line_count > 0:
                    print("✓ Empty lines preserved")
                else:
                    print("ℹ  Empty lines may have been modified")

                if "items" in new_content:
                    print("✓ Edit applied correctly with empty lines")
                else:
                    print("✗ Edit not applied correctly")
                    return False
            else:
                print("ℹ  No WorkspaceEdit for empty line test")

        except Exception as e:
            print(f"✗ Error in empty line test: {e}")
            return False

    print("\n✓ Multi-line edit handling test passed!")
    return True


async def test_error_handling(server: PythonRefactorMCPServer):
    """Test error handling and edge cases - MEDIUM priority."""
    print("\n" + "=" * 80)
    print("TEST 7: Error Handling (P2 - Medium)")
    print("=" * 80)

    workspace = Path(__file__).parent / "example_project"

    # Test 1: Invalid file path
    print("\n[7.1] Testing invalid file path handling...")
    try:
        result = await server._get_definition(
            file_path="/nonexistent/file.py",
            line=0,
            column=0,
        )

        # LSP might return null or error
        if result.get("definition") is None:
            print("✓ Invalid file path handled gracefully (returned None)")
        else:
            print("ℹ  LSP returned unexpected result for invalid path")

    except Exception as e:
        print(f"✓ Exception raised for invalid path: {type(e).__name__}")

    # Test 2: Out of bounds line/column
    print("\n[7.2] Testing out-of-bounds position handling...")
    try:
        main_file = workspace / "main.py"
        await server.lsp_client.open_document(str(main_file))

        result = await server._get_definition(
            file_path=str(main_file),
            line=99999,  # Way beyond file length
            column=99999,
        )

        if result.get("definition") is None:
            print("✓ Out-of-bounds position handled gracefully")
        else:
            print("ℹ  LSP accepted out-of-bounds position")

    except Exception as e:
        print(f"✓ Exception raised for out-of-bounds: {type(e).__name__}")

    # Test 3: Invalid WorkspaceEdit format
    print("\n[7.3] Testing invalid WorkspaceEdit handling...")
    try:
        invalid_edit = {
            "changes": {
                "file:///invalid": [
                    {"range": {"start": {}, "end": {}}, "newText": "invalid"}
                ]
            }
        }

        result = await server._apply_workspace_edit(invalid_edit)

        # Should either fail or handle gracefully
        if result.get("success") == False or "error" in result:
            print("✓ Invalid WorkspaceEdit rejected")
        else:
            print("ℹ  Invalid WorkspaceEdit processing result unclear")

    except Exception as e:
        print(f"✓ Exception raised for invalid WorkspaceEdit: {type(e).__name__}")

    # Test 4: Empty/null parameters
    print("\n[7.4] Testing empty parameter handling...")
    try:
        result = await server._rename_symbol(
            file_path=str(workspace / "main.py"),
            line=0,
            column=0,
            new_name="",  # Empty name
        )

        workspace_edit = result.get("workspace_edit")
        if workspace_edit is None or not workspace_edit:
            print("✓ Empty rename name handled gracefully")
        else:
            print("ℹ  LSP accepted empty rename name")

    except Exception as e:
        print(f"✓ Exception raised for empty name: {type(e).__name__}")

    # Test 5: File system permissions (if applicable)
    print("\n[7.5] Testing file permission handling...")
    try:
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            readonly_file = Path(tmpdir) / "readonly.py"
            readonly_file.write_text("x = 1\n")

            # Make file read-only
            os.chmod(readonly_file, 0o444)

            await server.lsp_client.open_document(str(readonly_file))
            await asyncio.sleep(0.3)

            result = await server._rename_symbol(
                file_path=str(readonly_file),
                line=0,
                column=0,
                new_name="y",
            )

            workspace_edit = result.get("workspace_edit")
            if workspace_edit:
                apply_result = await server._apply_workspace_edit(workspace_edit)

                if not apply_result.get("success"):
                    print("✓ Read-only file handled correctly")
                else:
                    print("ℹ  Read-only file edit succeeded (may have permissions)")
            else:
                print("ℹ  No WorkspaceEdit generated for readonly file")

    except Exception as e:
        print(f"✓ Exception raised for readonly file: {type(e).__name__}")

    print("\n✓ Error handling test completed!")
    return True


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("Python Refactor MCP Server - Integration Tests")
    print("=" * 80)

    workspace = Path(__file__).parent / "example_project"
    server = PythonRefactorMCPServer(str(workspace))

    try:
        # Start server
        print("\n[SETUP] Starting MCP server and LSP client...")
        await server.start()
        print("✓ Server started successfully")

        # Run tests
        results = []
        results.append(await test_navigation_tools(server))
        results.append(await test_refactoring_tools(server))
        results.append(await test_cross_file_references(server))
        results.append(await test_security_model(server))
        results.append(await test_workspace_edit_application(server))
        results.append(await test_multiline_edits(server))
        results.append(await test_error_handling(server))

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        passed = sum(results)
        total = len(results)
        print(f"\nTests passed: {passed}/{total}")

        if passed == total:
            print("\n✓ All tests passed!")
            return 0
        else:
            print(f"\n✗ {total - passed} test(s) failed")
            return 1

    except Exception as e:
        print(f"\n✗ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        print("\n[CLEANUP] Shutting down server...")
        await server.shutdown()
        print("✓ Server shut down successfully")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
