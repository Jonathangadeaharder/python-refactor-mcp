# Python Refactor MCP: Semantically-Aware AI Refactoring

An MCP-LSP Bridge that enables AI agents to perform safe, type-aware Python refactoring operations via Pyright.

## Overview

This MCP server acts as a bridge between AI agents (like Claude) and the Pyright language server, providing semantically-aware code intelligence and refactoring capabilities. Unlike simple text manipulation tools, this server uses Pyright's full type system and project-wide semantic analysis to ensure refactorings are safe and correct.

### Key Features

- **Semantically-Aware**: Uses Pyright's type checker for accurate, scope-aware refactoring
- **Safe by Design**: Two-stage approval process prevents unauthorized file modifications
- **Project-Wide Analysis**: Understands cross-file dependencies and references
- **Stateful Architecture**: Maintains persistent LSP connection for fast responses
- **AI-Friendly API**: Clean MCP tools designed for LLM consumption

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   AI Assistant  │  MCP    │  MCP-LSP Bridge  │   LSP   │  Pyright Server │
│  (Claude, etc.) ├────────►│  (This Server)   ├────────►│   (The "Brain") │
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      │ File I/O
                                      ▼
                                ┌──────────┐
                                │ Workspace│
                                │  Files   │
                                └──────────┘
```

### Design Principles

1. **MCP for Intent**: AI agents use MCP to express what they want to do
2. **LSP for Execution**: Pyright computes how to do it safely
3. **Human for Approval**: User reviews and approves all file modifications
4. **Stateful for Performance**: Persistent LSP connection with in-memory caching

## Installation

### Prerequisites

1. **Python 3.10+**: Required for the MCP server
2. **Node.js & npm**: Required for Pyright language server
3. **Pyright**: Install globally with npm

```bash
# Install Pyright language server
npm install -g pyright

# Verify installation
pyright-langserver --version
```

### Install the MCP Server

```bash
# Clone the repository
git clone <repository-url>
cd python-refactor-mcp

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Usage

### Running the Server

The server requires a workspace root (the Python project directory):

```bash
# Run with uv
uv run python-refactor-mcp /path/to/your/python/project

# Or with python
python -m python_refactor_mcp /path/to/your/python/project
```

### Configuring with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "python-refactor": {
      "command": "uv",
      "args": [
        "run",
        "python-refactor-mcp",
        "/absolute/path/to/your/python/project"
      ]
    }
  }
}
```

### Configuring with Other MCP Clients

The server uses stdio transport and is compatible with any MCP client that supports stdio, including:

- Claude Desktop
- Cursor IDE
- Custom agents built with MCP SDK

## Available Tools

### Navigation Tools

#### `get_definition`
Find where a symbol (variable, function, class) is defined.

**Parameters:**
- `file_path`: Absolute path to Python file
- `line`: Line number (0-based)
- `column`: Column number (0-based)

**Example:**
```python
# Find definition of 'calculate_total' at line 42, column 10
result = get_definition(
    file_path="/project/sales.py",
    line=42,
    column=10
)
# Returns: {"definition": {"uri": "file:///project/utils.py", "range": {...}}}
```

#### `get_references`
Find all usages of a symbol across the entire project.

**Parameters:**
- `file_path`: Absolute path to Python file
- `line`: Line number (0-based)
- `column`: Column number (0-based)
- `include_declaration`: Include the symbol's declaration (default: true)

**Example:**
```python
# Find all references to 'user_id'
result = get_references(
    file_path="/project/models.py",
    line=15,
    column=8
)
# Returns: {"references": [{"uri": "...", "range": {...}}, ...]}
```

#### `get_hover_info`
Get type information, documentation, and signatures for a symbol.

**Parameters:**
- `file_path`: Absolute path to Python file
- `line`: Line number (0-based)
- `column`: Column number (0-based)

**Example:**
```python
# Get type info for a function
result = get_hover_info(
    file_path="/project/api.py",
    line=20,
    column=5
)
# Returns: {"hover": {"contents": "def process_data(items: List[str]) -> Dict[str, int]", ...}}
```

### Refactoring Tools

#### `rename_symbol`
**SAFE**: Rename a symbol across the entire project with semantic awareness.

**Security Model**: This tool generates a WorkspaceEdit PLAN but does NOT apply it. The user must review and approve the changes via `apply_workspace_edit`.

**Parameters:**
- `file_path`: Absolute path to Python file containing the symbol
- `line`: Line number where symbol is located (0-based)
- `column`: Column number where symbol starts (0-based)
- `new_name`: New name for the symbol

**Example:**
```python
# Generate rename plan for 'old_name' -> 'new_name'
plan = rename_symbol(
    file_path="/project/models.py",
    line=10,
    column=4,
    new_name="new_name"
)
# Returns: {
#   "workspace_edit": {"changes": {...}},
#   "message": "WorkspaceEdit plan generated. Review and apply."
# }

# After user approval:
apply_workspace_edit(workspace_edit=plan["workspace_edit"])
```

#### `get_code_actions`
Get available refactoring actions for a selected code range.

**Parameters:**
- `file_path`: Absolute path to Python file
- `start_line`: Start line of selection (0-based)
- `start_column`: Start column of selection (0-based)
- `end_line`: End line of selection (0-based)
- `end_column`: End column of selection (0-based)
- `only_kind`: Filter to specific action kind (optional)
  - `"refactor"`: All refactorings
  - `"refactor.extract"`: Extract operations
  - `"refactor.inline"`: Inline operations
  - `"quickfix"`: Quick fixes

**Example:**
```python
# Get all available refactorings for selected code
actions = get_code_actions(
    file_path="/project/utils.py",
    start_line=30,
    start_column=0,
    end_line=35,
    end_column=20,
    only_kind="refactor"
)
# Returns: {"code_actions": [{"title": "Extract function", ...}, ...]}
```

### Security-Critical Tools

#### `apply_workspace_edit`
**SECURITY CRITICAL**: Apply a WorkspaceEdit plan to the file system.

This tool modifies files on disk. It should ONLY be called after:
1. A WorkspaceEdit was generated by a tool like `rename_symbol`
2. The user has explicitly reviewed and approved the changes

**Parameters:**
- `workspace_edit`: The WorkspaceEdit object to apply

**Example:**
```python
# Step 1: Generate plan (does NOT modify files)
plan = rename_symbol(...)

# Step 2: User reviews the plan in UI

# Step 3: User approves, client calls apply
result = apply_workspace_edit(workspace_edit=plan["workspace_edit"])
# Returns: {
#   "success": true,
#   "modified_files": ["/project/file1.py", "/project/file2.py"],
#   "message": "Successfully applied changes to 2 file(s)"
# }
```

### Diagnostic Tools

#### `get_diagnostics`
Get type errors, warnings, and other diagnostics for a file.

**Parameters:**
- `file_path`: Absolute path to Python file

**Example:**
```python
result = get_diagnostics(file_path="/project/app.py")
# Note: Diagnostics are sent asynchronously by LSP server
```

## Security Model

The server implements a two-stage commit process for all file modifications:

### Stage 1: Plan Generation
Tools like `rename_symbol` compute a WorkspaceEdit "plan" but DO NOT modify files. The plan is returned to the MCP client for user review.

### Stage 2: User Approval & Execution
The MCP client UI displays the plan to the user. After explicit approval, the client calls `apply_workspace_edit` to execute the changes.

This ensures:
- No AI hallucination can corrupt files
- User maintains full control
- All changes are auditable before execution

## Development

### Project Structure

```
python-refactor-mcp/
├── .github/workflows/       # GitHub Actions
│   ├── test-and-log.yml    # Auto-test on push
│   └── README.md           # Workflow documentation
├── src/python_refactor_mcp/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Entry point
│   ├── lsp_client.py        # LSP JSON-RPC client
│   ├── mcp_server.py        # MCP server & tools
│   └── workspace_edit.py    # WorkspaceEdit application
├── tests/                   # Test suite
│   ├── test_integration.py  # Integration tests
│   └── example_project/     # Test fixtures
├── test_execution.log       # Latest test results (auto-generated)
├── pyproject.toml          # Project metadata
└── README.md               # This file
```

### Continuous Integration

This repository includes a GitHub Action that automatically:
1. Runs the integration test suite on every push
2. Captures test output to `test_execution.log`
3. Force-amends the log file to the commit
4. Pushes the updated commit back to the branch

**After pushing a commit:**
```bash
# Wait for GitHub Action to complete (~2-3 minutes)

# Pull the amended commit with test results
git pull --rebase

# View test results
cat test_execution.log
```

See [`.github/workflows/README.md`](.github/workflows/README.md) for full documentation.

### Project Structure Validation

This project uses [structurelint](https://github.com/Jonathangadeaharder/structurelint) to enforce clean project organization and architectural integrity with evidence-based quality metrics.

**What structurelint enforces:**

*Phase 0 - Filesystem Linting:*
- Directory depth limits (max 5 levels)
- File count restrictions (20 per directory, 15 in src/)
- Subdirectory limits (max 10)
- Python naming conventions (snake_case)
- README.md requirements for documentation
- Disallowed patterns (temp files, build artifacts)

*Phase 1 - Architectural Layer Enforcement:*
- Layer boundary validation
- Prevents circular dependencies
- Enforces clean architecture patterns

*Phase 2 - Dead Code Detection:*
- Orphaned file detection (disabled - Python import analysis pending)
- Unused export detection (disabled - Python export analysis pending)

*Phase 3 - Test Validation:*
- Every source file requires corresponding test
- Tests mirror source directory structure (`tests/src/python_refactor_mcp/`)
- Separate test directory pattern enforced
- Test location validation

*Evidence-Based Complexity Metrics:*
- **Cognitive Complexity (CoC)**: Measures code comprehension difficulty
  - Research shows r=0.54 correlation with comprehension time
  - Current threshold: 40 (target: 15 for new code)
  - Penalizes nesting and control flow complexity
- **Halstead Effort**: Captures data/operator complexity
  - Research shows rs=0.901 correlation with cognitive load
  - Threshold: 100,000 for Python
  - Complements CoC by detecting different complexity patterns

*Linter Configuration Enforcement:*
- Validates Python linter configuration exists
- Accepts config files (pyproject.toml) OR GitHub workflow
- Ensures black, ruff, mypy are configured

**Configuration Philosophy:**
The `.structurelint.yml` implements research-backed quality gates that prevent technical debt accumulation. The configuration balances pragmatism (accommodating existing code) with best practices (guiding future development).

**Running structurelint:**
```bash
# Check project structure
structurelint

# Initialize config (if starting fresh)
structurelint --init

# Output as JSON for CI/CD
structurelint --format json
```

**CI/CD Integration:**
Structurelint runs automatically on every push via GitHub Actions (see `.github/workflows/structurelint.yml`). It's also included in the pre-commit hooks.

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Check project structure
structurelint
```

### Pre-commit Hooks

This project uses pre-commit hooks to maintain code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

The hooks include:
- **black**: Code formatting
- **ruff**: Python linting
- **structurelint**: Project structure and architecture validation
- Standard file checks (trailing whitespace, YAML/JSON validation, etc.)

## Troubleshooting

### "pyright-langserver not found"

**Solution**: Install Pyright globally:
```bash
npm install -g pyright
```

Verify with:
```bash
which pyright-langserver
```

### "LSP request timed out"

**Causes**:
- Very large codebase
- Pyright performing initial indexing
- Complex type inference

**Solutions**:
- Wait for initial indexing to complete
- Check Pyright logs in stderr
- Ensure sufficient system resources

### Server not responding

**Debug Steps**:
1. Check server logs (stderr output)
2. Verify workspace root path is correct
3. Ensure Python files are syntactically valid
4. Restart the MCP client

## Architecture Details

### Why Not LibCST or ast?

While LibCST provides lossless parsing and ast provides fast AST manipulation, neither provides project-wide semantic analysis. Safe refactoring requires:

- Cross-file dependency graphs
- Type inference and checking
- Scope resolution
- Symbol definition tracking

Implementing these from scratch would be a multi-year engineering effort. By using Pyright via LSP, we leverage a production-grade semantic engine for free.

### Why Pyright vs. Jedi vs. Mypy?

**Pyright** (Recommended):
- ✅ Designed for interactive use (JIT evaluation)
- ✅ Stateful in-memory caching
- ✅ Type-aware semantic analysis
- ✅ Fast and scalable

**Jedi**:
- ❌ Performance issues on large codebases
- ❌ Known to hang on complex imports
- ✅ Pure Python implementation

**Mypy**:
- ❌ Batch-oriented architecture
- ❌ No error recovery
- ❌ Not designed for interactive queries
- ✅ Excellent for CI/CD

### Performance Characteristics

- **Initial Startup**: 1-3 seconds (LSP initialization)
- **First Query**: 1-5 seconds (project indexing)
- **Subsequent Queries**: 50-200ms (cached)
- **Memory Usage**: ~100-500MB (depends on project size)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license here]

## References

1. [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
2. [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
3. [Pyright Documentation](https://github.com/microsoft/pyright)
4. [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## Citation

If you use this in research or publications, please cite:

```
[Add citation information]
```
