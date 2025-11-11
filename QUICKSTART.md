# Quick Start Guide

Get started with Python Refactor MCP in 5 minutes.

## 1. Install Prerequisites

### Install Pyright Language Server

```bash
npm install -g pyright
```

Verify installation:
```bash
pyright-langserver --version
```

### Install Python Dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## 2. Test the Server

Run the server on the example project:

```bash
uv run python-refactor-mcp ./tests/example_project
```

You should see:
```
INFO - Starting Python Refactor MCP Server for workspace: /path/to/tests/example_project
INFO - Starting Pyright LSP server for workspace: /path/to/tests/example_project
INFO - LSP initialized. Server capabilities: [...]
INFO - Python Refactor MCP Server started successfully
```

## 3. Configure Claude Desktop

1. Locate your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the server configuration:

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

3. Restart Claude Desktop

4. Verify the server is connected (look for the MCP icon in Claude)

## 4. Try It Out

Ask Claude to help you refactor code:

### Example 1: Find Definition
```
Claude, use the get_definition tool to find where the calculate_total
function is defined in /path/to/project/main.py at line 42, column 10.
```

### Example 2: Safe Rename
```
Claude, I want to rename the variable 'user_id' to 'account_id' in
/path/to/project/models.py at line 15, column 8. Please use the
rename_symbol tool to generate a refactoring plan, then show me what
files will be changed before applying it.
```

### Example 3: Find All References
```
Claude, find all places where the DataProcessor class is used in my
project. Check /path/to/project/main.py at line 25, column 6.
```

## 5. Understanding the Two-Stage Process

**IMPORTANT**: File modifications require two steps:

1. **Generate Plan**: Tools like `rename_symbol` create a WorkspaceEdit plan
2. **Review & Apply**: You review the plan, then Claude calls `apply_workspace_edit`

This ensures you always see what will change before any files are modified.

## Common Use Cases

### Refactoring a Function Name

```python
# Original code
def calc_sum(numbers):
    return sum(numbers)

# You want: calculate_total
```

Ask Claude:
```
Rename the function 'calc_sum' to 'calculate_total' at line 10, column 4
in /project/utils.py. Show me what will change.
```

Claude will:
1. Call `rename_symbol` to generate the plan
2. Show you all files that will be modified
3. Ask for your approval
4. Call `apply_workspace_edit` after you approve

### Finding Impact of Changes

Before making changes, understand the impact:

```
Before I refactor this function, show me all places where it's used.
Use get_references on 'process_data' in /project/main.py at line 15.
```

### Getting Type Information

```
What is the type signature of the function at line 20, column 5
in /project/api.py? Use get_hover_info.
```

## Troubleshooting

### Server Won't Start

**Check Pyright Installation:**
```bash
which pyright-langserver
# Should output: /usr/local/bin/pyright-langserver or similar
```

**Check Python Version:**
```bash
python --version
# Should be 3.10 or higher
```

### "LSP request timed out"

First queries can be slow while Pyright indexes your project. Wait 5-10 seconds and try again.

### Changes Not Applied

Verify you completed both steps:
1. Generated the plan with `rename_symbol`
2. Called `apply_workspace_edit` with the plan

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Explore the [example project](tests/example_project/)
- Check the [architectural blueprint](docs/architecture.md) to understand the design

## Getting Help

- Check the [README](README.md) for detailed documentation
- Review server logs (stderr output) for error messages
- Verify your workspace path is correct and contains Python files
