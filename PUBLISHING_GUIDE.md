# Publishing Guide

Complete guide to publishing the MCP-LSP Bridge to PyPI and the MCP Registry.

---

## 📦 Publishing to PyPI

### Prerequisites

1. **PyPI Account**: Create account at https://pypi.org
2. **API Token**: Generate at https://pypi.org/manage/account/token/
3. **Twine**: Install with `pip install twine`

### Step 1: Verify Package Build

The package is already built in `dist/`:

```bash
ls -lh dist/
# python_refactor_mcp-1.0.0-py3-none-any.whl (19K)
# python_refactor_mcp-1.0.0.tar.gz (41K)
```

### Step 2: Test Upload (TestPyPI)

**Optional but recommended** - test on TestPyPI first:

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ python-refactor-mcp
```

### Step 3: Production Upload

```bash
# Upload to PyPI
python -m twine upload dist/*

# Enter credentials:
# Username: __token__
# Password: <your-pypi-api-token>
```

### Step 4: Verify Installation

```bash
# Install from PyPI
pip install python-refactor-mcp

# Verify it works
python -m python_refactor_mcp --help
```

### Package URLs After Publishing

- **PyPI Page**: https://pypi.org/project/python-refactor-mcp/
- **Install Command**: `pip install python-refactor-mcp`

---

## 🌐 Publishing to MCP Registry

The MCP Registry is the official directory for MCP servers, making them discoverable in Claude Desktop.

### What You Need

1. **GitHub Repository**: Already have (https://github.com/Jonathangadeaharder/python-refactor-mcp)
2. **Published Package**: After PyPI publication
3. **MCP Registry PR**: Submit to https://github.com/modelcontextprotocol/servers

### Step 1: Fork MCP Servers Repository

```bash
# Fork on GitHub: https://github.com/modelcontextprotocol/servers
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/servers.git
cd servers
```

### Step 2: Add Server Entry

Create `src/python-refactor-mcp/README.md`:

```markdown
# python-refactor-mcp

MCP-LSP Bridge for semantically-aware Python refactoring using Pyright.

## Features

- Navigate Python code with semantic accuracy
- Find all references to symbols across projects
- Generate safe rename operations using type analysis
- Apply refactorings with user approval (two-stage security)

## Installation

### Via pip

```bash
pip install python-refactor-mcp
npm install -g pyright  # Required dependency
```

### Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "python-refactor": {
      "command": "python",
      "args": [
        "-m",
        "python_refactor_mcp",
        "/path/to/your/python/project"
      ]
    }
  }
}
```

## Tools

- `get_definition` - Navigate to symbol definitions
- `get_references` - Find all symbol references
- `get_hover_info` - Get type information
- `rename_symbol` - Generate safe rename plans
- `get_code_actions` - Get available refactorings
- `apply_workspace_edit` - Apply approved edits
- `get_diagnostics` - Collect type errors

## Links

- Repository: https://github.com/Jonathangadeaharder/python-refactor-mcp
- PyPI: https://pypi.org/project/python-refactor-mcp/
- Issues: https://github.com/Jonathangadeaharder/python-refactor-mcp/issues
```

### Step 3: Update Registry Index

Add entry to `src/index.json`:

```json
{
  "python-refactor-mcp": {
    "name": "python-refactor-mcp",
    "description": "MCP-LSP Bridge for semantically-aware Python refactoring using Pyright",
    "repository": "https://github.com/Jonathangadeaharder/python-refactor-mcp",
    "package": "python-refactor-mcp",
    "type": "pip",
    "tags": ["python", "refactoring", "lsp", "pyright", "type-checking", "code-analysis"],
    "author": "Python Refactor MCP Contributors",
    "license": "MIT"
  }
}
```

### Step 4: Submit Pull Request

```bash
git checkout -b add-python-refactor-mcp
git add src/python-refactor-mcp/README.md src/index.json
git commit -m "Add python-refactor-mcp server"
git push origin add-python-refactor-mcp
```

Create PR with title: **"Add python-refactor-mcp: MCP-LSP Bridge for Python Refactoring"**

### PR Description Template

```markdown
## New MCP Server: python-refactor-mcp

MCP-LSP Bridge that enables AI agents to perform semantically-aware Python refactoring using Pyright's type system.

### Details

- **Repository**: https://github.com/Jonathangadeaharder/python-refactor-mcp
- **PyPI**: https://pypi.org/project/python-refactor-mcp/
- **License**: MIT
- **Version**: 1.0.0
- **Status**: Production-ready (100% test pass rate)

### Features

- 7 MCP tools for navigation and refactoring
- Two-stage security model (plan → approve → execute)
- Persistent Pyright LSP connection
- 86% test coverage

### Installation

```bash
pip install python-refactor-mcp
npm install -g pyright
```

### Testing

Fully tested with comprehensive integration test suite (7/7 tests passing).

### Checklist

- [x] Repository is public
- [x] README with clear documentation
- [x] MIT License
- [x] Published to PyPI
- [x] Installation instructions
- [x] Configuration example
- [x] Test coverage
```

---

## 🚀 Post-Publication Tasks

### 1. Update Repository

Add PyPI badge to README:

```markdown
[![PyPI version](https://badge.fury.io/py/python-refactor-mcp.svg)](https://pypi.org/project/python-refactor-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

### 2. Create GitHub Release

1. Go to: https://github.com/Jonathangadeaharder/python-refactor-mcp/releases/new
2. Tag: `v1.0.0`
3. Title: "Release v1.0.0: Production-Ready MCP-LSP Bridge"
4. Description: Use contents of `RELEASE_NOTES_v1.0.0.md`
5. Attach built packages:
   - `python_refactor_mcp-1.0.0-py3-none-any.whl`
   - `python_refactor_mcp-1.0.0.tar.gz`

### 3. Announce

Consider announcing on:
- Reddit: r/Python, r/ClaudeAI
- Hacker News
- Twitter/X
- LinkedIn
- Discord communities (Python, AI)

### 4. Documentation Site (Optional)

Consider creating docs site with:
- MkDocs or Sphinx
- Host on GitHub Pages
- Include API reference, examples, tutorials

---

## 📊 Monitoring

### PyPI Statistics

Track download statistics at:
- https://pypistats.org/packages/python-refactor-mcp

### GitHub Insights

Monitor:
- Stars and forks
- Issues and PRs
- Traffic and clones

### User Feedback

Watch for:
- GitHub issues
- PyPI comments
- MCP Registry discussions
- Community feedback

---

## 🔄 Future Releases

### Version Numbering

Follow Semantic Versioning:
- **Major (2.0.0)**: Breaking changes
- **Minor (1.1.0)**: New features, backward compatible
- **Patch (1.0.1)**: Bug fixes

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Build: `python -m build`
4. Test: Run integration tests
5. Commit and tag: `git tag v1.X.Y`
6. Push: `git push && git push --tags`
7. Publish: `twine upload dist/*`
8. Create GitHub release

---

## ✅ Pre-Publication Checklist

Current status:

- [x] Package built successfully
- [x] Version updated to 1.0.0
- [x] CHANGELOG created
- [x] LICENSE included (MIT)
- [x] README comprehensive
- [x] All tests passing (7/7)
- [x] PyPI metadata complete
- [x] Git tag created (v1.0.0)
- [ ] Uploaded to PyPI
- [ ] GitHub release created
- [ ] MCP Registry PR submitted

---

## 🛟 Troubleshooting

### Twine Upload Fails

```bash
# Check credentials
python -m twine check dist/*

# Use API token (not password)
# Username: __token__
# Password: pypi-...
```

### Package Import Fails

```bash
# Verify package structure
python -m build --check

# Test locally
pip install -e .
python -c "import python_refactor_mcp; print('OK')"
```

### MCP Registry PR Rejected

Common issues:
- Missing documentation
- No installation instructions
- Unclear server purpose
- No testing evidence

**Solution**: Refer to existing servers in the registry for examples.

---

## 📧 Support

Questions about publishing?
- PyPI Help: https://pypi.org/help/
- MCP Registry: https://github.com/modelcontextprotocol/servers/discussions
- Project Issues: https://github.com/Jonathangadeaharder/python-refactor-mcp/issues

---

**Ready to publish!** 🚀
