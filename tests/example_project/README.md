# Example Project

This is a test fixture used by the integration tests.

## Purpose

This example Python project provides test cases for:
- Symbol navigation (definitions, references)
- Type information retrieval
- Rename operations
- Cross-file refactoring

## Structure

- `main.py` - Main module with function calls
- `utils.py` - Utility functions that are referenced from main
- `__init__.py` - Package initialization

## Usage

This project is used by `test_integration.py` to verify that the MCP-LSP bridge correctly:
1. Initializes the Pyright LSP server
2. Performs semantic analysis
3. Executes refactoring operations
4. Maintains type safety

Do not modify these files without updating the corresponding test assertions.
