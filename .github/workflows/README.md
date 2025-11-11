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
