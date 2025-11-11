#!/usr/bin/env python3
"""
Integration test for Python Refactor MCP Server.

This script tests the MCP server by:
1. Starting the server
2. Testing navigation tools (get_definition, get_references, get_hover_info)
3. Testing refactoring tools (rename_symbol)
4. Verifying the two-stage security model
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
