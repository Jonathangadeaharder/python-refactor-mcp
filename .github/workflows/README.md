# GitHub Actions Workflows

## Test and Log Results Workflow

**File**: `test-and-log.yml`

### Purpose

This workflow automatically runs the integration test suite on every push and embeds the test execution log directly into the commit itself via force-amend.

### How It Works

1. **Trigger**: Runs on push to `claude/**`, `main`, or `develop` branches
2. **Setup**: Installs Node.js, Python, Pyright, and all dependencies
3. **Test Execution**: Runs `python tests/test_integration.py`
4. **Log Capture**: Captures all output (stdout + stderr) to `test_execution.log`
5. **Commit Amendment**: Adds the log file and amends the pushed commit
6. **Force Push**: Force-pushes the amended commit back to the branch

### Log File Format

The `test_execution.log` file contains:

```
=================================================================================
MCP-LSP Bridge - Integration Test Execution
=================================================================================

Execution Time: 2025-11-11 12:34:56 UTC
Branch: claude/feature-branch
Commit: abc123...
Triggered by: push

=================================================================================
Test Output:
=================================================================================

[Full test execution output with colors and formatting]

=================================================================================
Test Summary:
=================================================================================
Status: ✅ PASSED (or ❌ FAILED)
Exit Code: 0

=================================================================================
System Information:
=================================================================================

Python Version: 3.11.x
Pyright Version: 1.1.407
Node.js Version: 20.x.x
Runner OS: Linux
```

### Benefits

1. **Embedded Proof**: Test results are permanently attached to the commit
2. **No Artifact Downloads**: No need to download workflow artifacts
3. **Quick Review**: Simply `git pull` and check `test_execution.log`
4. **Historical Record**: Test results preserved in Git history
5. **Offline Access**: View test results without GitHub UI

### Usage

#### Viewing Test Results

After pushing a commit:

```bash
# Pull the amended commit
git pull --rebase

# View the test log
cat test_execution.log

# Or with syntax highlighting
less test_execution.log
```

#### In GitHub UI

1. Push your commit
2. Wait for GitHub Action to complete (~2-3 minutes)
3. Pull the branch to see the updated commit with log
4. The log file will be visible in the file tree

#### Understanding Workflow Status

- **✅ Green Check**: Tests passed, log shows success
- **❌ Red X**: Tests failed, log shows errors and stack traces
- **🟡 Yellow**: Workflow error (setup issue, not test failure)

### Workflow Behavior

#### On Test Success
- Log file is created with ✅ status
- Commit is amended with the log
- Force-pushed back to branch
- Workflow shows green ✅

#### On Test Failure
- Log file is created with ❌ status and error details
- Commit is still amended (you can see what failed)
- Force-pushed back to branch
- Workflow shows red ❌

#### Important Notes

1. **Force Push**: This workflow uses `--force-with-lease` to safely update the commit
2. **Local Changes**: If you have local commits, you'll need `git pull --rebase` after the workflow runs
3. **Branch Protection**: This workflow requires write permissions to force-push
4. **Concurrent Pushes**: If multiple commits are pushed rapidly, some may conflict

### Configuration

#### Trigger Branches

To modify which branches trigger this workflow, edit:

```yaml
on:
  push:
    branches:
      - 'claude/**'    # All Claude branches
      - 'main'         # Main branch
      - 'develop'      # Development branch
      - 'feature/**'   # Add more patterns as needed
```

#### Skip Workflow

To skip the workflow for a specific commit:

```bash
git commit -m "Your commit message [skip ci]"
```

### Security Considerations

- Workflow uses `${{ secrets.GITHUB_TOKEN }}` (automatically provided)
- No sensitive data is logged
- Test execution is sandboxed in GitHub's runners
- Force push is protected by `--force-with-lease`

### Troubleshooting

#### Workflow Fails to Push

**Symptom**: Workflow succeeds but force-push fails

**Solution**: Check branch protection rules - ensure GitHub Actions has write permissions

#### Log File Not Appearing

**Symptom**: Workflow succeeds but no log file in commit

**Solution**:
1. Check workflow logs for "No changes to commit"
2. Ensure `git add test_execution.log` is working
3. Verify file is actually created

#### Tests Pass Locally But Fail in CI

**Symptom**: `python tests/test_integration.py` works locally but fails in workflow

**Solution**:
1. Check Python/Node.js version differences
2. Verify all dependencies are installed
3. Look for environment-specific issues (paths, permissions)
4. Check the full log in `test_execution.log`

### Example Log Output

A successful test run produces:

```
=================================================================================
MCP-LSP Bridge - Integration Test Execution
=================================================================================

Execution Time: 2025-11-11 10:15:32 UTC
Branch: claude/mcp-lsp-bridge-python-refactor-011CV1t4sPKxu2wtcgd8FXV1
Commit: bc3779d1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7
Triggered by: push

=================================================================================
Test Output:
=================================================================================

[SETUP] Starting MCP server and LSP client...
✓ Server started successfully

================================================================================
TEST 1: Navigation Tools
================================================================================
✓ Found 4 reference(s)
✓ Retrieved hover info
✓ All navigation tool tests completed!

... [additional test output] ...

Tests passed: 4/4
✓ All tests passed!

=================================================================================
Test Summary:
=================================================================================
Status: ✅ PASSED
Exit Code: 0
```

### Integration with Development Workflow

This workflow seamlessly integrates with your development process:

```bash
# Make changes
vim src/python_refactor_mcp/mcp_server.py

# Commit
git commit -m "Add new MCP tool for code formatting"

# Push (triggers workflow)
git push

# Wait ~2 minutes for GitHub Action

# Pull amended commit with test results
git pull --rebase

# Review test results
cat test_execution.log

# Continue development
```

### Disabling the Workflow

To temporarily disable:

1. **Option 1**: Rename the workflow file
   ```bash
   mv .github/workflows/test-and-log.yml .github/workflows/test-and-log.yml.disabled
   ```

2. **Option 2**: Comment out the trigger
   ```yaml
   # on:
   #   push:
   #     branches:
   #       - 'claude/**'
   ```

3. **Option 3**: Delete the workflow file
   ```bash
   rm .github/workflows/test-and-log.yml
   ```

### Future Enhancements

Possible improvements to consider:

- [ ] Add test coverage metrics to log
- [ ] Generate HTML test report alongside log
- [ ] Send notification on test failure
- [ ] Cache dependencies to speed up workflow
- [ ] Run tests in parallel for faster execution
- [ ] Add performance benchmarking to log

---

## Repomix Codebase Bundle Workflow

**File**: `repomix.yml`

### Purpose

This workflow automatically generates a bundled snapshot of the entire codebase using [Repomix](https://github.com/yamadashy/repomix) and publishes it as a GitHub Actions artifact. This is useful for:

- Sharing the complete codebase context with AI assistants
- Creating portable codebase snapshots for documentation
- Archiving the project state at specific commits
- Providing full context for code review or analysis

### How It Works

1. **Trigger**: Runs on push to `claude/**`, `main`, or `develop` branches, or manual trigger
2. **Setup**: Installs Node.js and Repomix
3. **Bundle Generation**: Runs `repomix` to create a single-file codebase bundle
4. **Artifact Upload**: Uploads the bundle as a GitHub Actions artifact (retained for 30 days)
5. **Summary**: Generates a workflow summary with bundle statistics

### Configuration

**File**: `repomix.config.json` (project root)

```json
{
  "output": {
    "filePath": "repomix-output.txt",
    "style": "plain",
    "headerText": "Python Refactor MCP - Codebase Bundle"
  },
  "include": [
    "**/*.py",
    "**/*.md",
    "**/*.yml",
    "**/*.toml",
    "**/*.json"
  ],
  "ignore": {
    "useGitignore": true,
    "customPatterns": [
      "**/__pycache__/**",
      "**/node_modules/**",
      "**/.venv/**",
      "**/dist/**"
    ]
  }
}
```

### Output Format

The generated `repomix-output.txt` contains:

```
Python Refactor MCP - Codebase Bundle

================================================================================
Project Structure
================================================================================
[Directory tree with file counts]

================================================================================
File Summary
================================================================================
[Statistics: total files, total lines, language breakdown]

================================================================================
Source Files
================================================================================

File: src/python_refactor_mcp/__init__.py
Language: Python
Lines: 42

[File contents with line numbers]

... [all other files]
```

### Usage

#### Downloading Artifacts

1. Navigate to the **Actions** tab in GitHub
2. Click on the **Repomix Codebase Bundle** workflow
3. Select the workflow run for your branch/commit
4. Scroll to **Artifacts** section at the bottom
5. Download `repomix-codebase-[branch]-[commit].zip`

#### Manual Trigger

To generate a bundle on-demand:

1. Go to **Actions** → **Repomix Codebase Bundle**
2. Click **Run workflow**
3. Select branch
4. Click **Run workflow**

#### Using with AI Assistants

```bash
# Download and extract the artifact
unzip repomix-codebase-main-abc123.zip

# Share with Claude or other AI
cat repomix-output.txt | pbcopy  # macOS
cat repomix-output.txt | xclip   # Linux

# Or open in editor
code repomix-output.txt
```

### Artifact Details

- **Name Format**: `repomix-codebase-{branch}-{commit-sha}`
- **Retention**: 30 days (configurable in workflow)
- **Compression**: Maximum (level 9)
- **Includes**: Config file alongside bundle

### Benefits

1. **Full Context**: Single file contains entire codebase
2. **AI-Optimized**: Formatted for LLM consumption
3. **Portable**: Easy to share and archive
4. **Searchable**: Plain text format for easy grepping
5. **Versioned**: Tied to specific commits via artifact name

### Customizing the Bundle

#### Include Additional File Types

Edit `repomix.config.json`:

```json
{
  "include": [
    "**/*.py",
    "**/*.md",
    "**/*.sh",     // Add shell scripts
    "**/*.env.example"  // Add example configs
  ]
}
```

#### Exclude Sensitive Files

```json
{
  "ignore": {
    "customPatterns": [
      "**/*.env",           // Exclude env files
      "**/secrets/**",      // Exclude secrets directory
      "**/*_private.py"     // Exclude private files
    ]
  }
}
```

#### Change Output Format

```json
{
  "output": {
    "style": "plain",  // Options: "markdown", "xml", "plain"
    "removeComments": true,  // Strip code comments
    "showLineNumbers": false  // Hide line numbers
  }
}
```

### Integration with Claude Code

When working with Claude Code, the repomix bundle provides full project context:

```bash
# Generate bundle locally
npx repomix

# Share with Claude
claude < repomix-output.txt "Analyze this codebase and suggest improvements"
```

### Workflow Behavior

#### On Successful Run
- Bundle generated in ~10-30 seconds
- Artifact uploaded automatically
- Summary shows bundle size and line count
- Workflow shows green ✅

#### On Failure
- Check if repomix is installed correctly
- Verify config file syntax
- Review included/excluded patterns
- Check workflow logs for details

### Security Considerations

- ✅ Respects `.gitignore` by default
- ✅ Security check enabled (no secrets leaked)
- ✅ Excludes common sensitive patterns
- ⚠️ Review bundle before sharing externally
- ⚠️ Artifacts are visible to repo collaborators

### Troubleshooting

#### Bundle Too Large

**Symptom**: Artifact exceeds GitHub's 2GB limit

**Solution**:
1. Add more exclusion patterns in config
2. Remove large binary files
3. Exclude test fixtures or data files
4. Use `removeComments: true` to reduce size

#### Missing Files in Bundle

**Symptom**: Expected files don't appear in output

**Solution**:
1. Check `include` patterns in config
2. Verify files aren't in `.gitignore`
3. Check `customPatterns` in ignore section
4. Run `repomix --verbose` locally to debug

#### Workflow Not Triggering

**Symptom**: Push doesn't trigger workflow

**Solution**:
1. Verify branch matches trigger pattern
2. Check workflow file syntax with YAML linter
3. Ensure workflows are enabled in repo settings
4. Try manual trigger to test

### Comparison with Git Archive

| Feature | Repomix Bundle | Git Archive |
|---------|----------------|-------------|
| Format | Single text file | Compressed archive |
| AI-Friendly | ✅ Yes | ❌ No |
| Human-Readable | ✅ Yes | ⚠️ Requires extraction |
| File Structure | ✅ Included | ✅ Preserved |
| Line Numbers | ✅ Optional | ❌ No |
| Syntax Info | ✅ Yes | ❌ No |
| Size | Larger (text) | Smaller (binary) |
| Searchable | ✅ Grep-friendly | ⚠️ After extraction |

### Example Workflow Summary

After a successful run, GitHub shows:

```
📦 Repomix Codebase Bundle Generated

Branch: `main`
Commit: `abc123def456`
Timestamp: 2025-11-15 10:30:45 UTC

Bundle Size: 256K
Line Count: 8,432

✅ The repomix bundle has been uploaded as a workflow artifact.

Download the artifact from the Artifacts section at the top of this workflow run.
```

### Use Cases

1. **AI Code Review**: Share entire codebase with Claude for comprehensive review
2. **Documentation**: Generate snapshots for documentation purposes
3. **Onboarding**: Provide new developers with searchable codebase overview
4. **Archival**: Preserve project state at key milestones
5. **Analysis**: Feed to static analysis tools or AI models
6. **Migration**: Assist in porting code to new frameworks

### Performance

- **Small Projects** (<100 files): ~5-10 seconds
- **Medium Projects** (100-1000 files): ~10-30 seconds
- **Large Projects** (1000+ files): ~30-60 seconds

Bundle size typically ranges from 100KB to several MB depending on codebase size and configuration.

### Best Practices

1. **Review Exclusions**: Regularly audit what's being excluded
2. **Monitor Size**: Keep bundles under 10MB for optimal AI processing
3. **Version Control**: Keep config file in version control
4. **Documentation**: Document custom patterns and why they're excluded
5. **Security**: Never include secrets, API keys, or sensitive data
6. **Retention**: Adjust retention days based on your needs (default: 30)

### Future Enhancements

Possible improvements to consider:

- [ ] Add diff-only bundles (changes since last commit)
- [ ] Generate bundle on PR creation
- [ ] Include git metadata in bundle header
- [ ] Support multiple output formats (JSON, XML)
- [ ] Add bundle quality metrics (complexity, duplication)
- [ ] Auto-tag releases with bundle artifacts
