#!/bin/bash
#
# Release Verification Script for python-refactor-mcp v1.0.0
#
# This script verifies that the package is ready for publication
#

set -e

echo "=================================================="
echo "🔍 Python Refactor MCP - Release Verification"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Helper function
check() {
    local test_name="$1"
    local command="$2"

    echo -n "Checking: $test_name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        FAILURES=$((FAILURES + 1))
    fi
}

# 1. Python environment
echo "📦 Python Environment"
echo "--------------------"
check "Python 3.10+" "python3 --version | grep -E 'Python 3\.(1[0-9]|[2-9][0-9])'"
check "pip installed" "pip --version"
check "build module" "python -c 'import build'"

# Twine is optional - only needed for publishing
if python -c 'import twine' 2>/dev/null; then
    echo -e "Checking: twine installed... ${GREEN}✓${NC} (ready for PyPI upload)"
else
    echo -e "Checking: twine installed... ${YELLOW}⚠${NC} (install for PyPI: pip install twine)"
fi

echo ""

# 2. Node.js environment (for Pyright)
echo "📦 Node.js Environment"
echo "---------------------"
check "Node.js installed" "node --version"
check "npm installed" "npm --version"
check "Pyright installed" "pyright --version"

echo ""

# 3. Package files
echo "📄 Package Files"
echo "----------------"
check "pyproject.toml exists" "test -f pyproject.toml"
check "README.md exists" "test -f README.md"
check "LICENSE exists" "test -f LICENSE"
check "CHANGELOG.md exists" "test -f CHANGELOG.md"
check "src/ directory" "test -d src/python_refactor_mcp"
check "tests/ directory" "test -d tests"

echo ""

# 4. Version consistency
echo "🔢 Version Consistency"
echo "---------------------"
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
INIT_VERSION=$(grep '^__version__ = ' src/python_refactor_mcp/__init__.py | cut -d'"' -f2)

echo "  pyproject.toml: $PYPROJECT_VERSION"
echo "  __init__.py:    $INIT_VERSION"

if [ "$PYPROJECT_VERSION" = "$INIT_VERSION" ]; then
    echo -e "  ${GREEN}✓ Versions match${NC}"
else
    echo -e "  ${RED}✗ Version mismatch!${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# 5. Build artifacts
echo "🏗️  Build Artifacts"
echo "------------------"
check "dist/ directory" "test -d dist"
check "wheel package" "test -f dist/python_refactor_mcp-${PYPROJECT_VERSION}-py3-none-any.whl"
check "source tarball" "test -f dist/python_refactor_mcp-${PYPROJECT_VERSION}.tar.gz"

echo ""

# 6. Git status
echo "🔀 Git Status"
echo "-------------"
BRANCH=$(git branch --show-current)
echo "  Current branch: $BRANCH"

if git diff-index --quiet HEAD --; then
    echo -e "  ${GREEN}✓ Working tree clean${NC}"
else
    echo -e "  ${YELLOW}⚠ Uncommitted changes${NC}"
fi

if git tag -l | grep -q "^v${PYPROJECT_VERSION}$"; then
    echo -e "  ${GREEN}✓ Git tag v${PYPROJECT_VERSION} exists${NC}"
else
    echo -e "  ${YELLOW}⚠ Git tag v${PYPROJECT_VERSION} not found${NC}"
fi

echo ""

# 7. Integration tests
echo "🧪 Integration Tests"
echo "-------------------"
echo "  Running tests..."
if python tests/test_integration.py > /tmp/test_output.log 2>&1; then
    TEST_COUNT=$(grep -o "Tests passed: [0-9]*/[0-9]*" /tmp/test_output.log | tail -1)
    echo -e "  ${GREEN}✓ $TEST_COUNT${NC}"
else
    echo -e "  ${RED}✗ Tests failed${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# 8. Package installation test
echo "📥 Package Installation"
echo "----------------------"
echo "  Installing package..."
if pip install dist/python_refactor_mcp-${PYPROJECT_VERSION}-py3-none-any.whl --force-reinstall --no-deps --quiet 2>&1; then
    echo -e "  ${GREEN}✓ Package installs successfully${NC}"

    # Test import
    if python -c "import python_refactor_mcp; assert python_refactor_mcp.__version__ == '$PYPROJECT_VERSION'" 2>&1; then
        echo -e "  ${GREEN}✓ Package imports correctly${NC}"
    else
        echo -e "  ${RED}✗ Package import failed${NC}"
        FAILURES=$((FAILURES + 1))
    fi

    # Test CLI
    if python -m python_refactor_mcp --version 2>&1 | grep -q "$PYPROJECT_VERSION"; then
        echo -e "  ${GREEN}✓ CLI --version works${NC}"
    else
        echo -e "  ${RED}✗ CLI --version failed${NC}"
        FAILURES=$((FAILURES + 1))
    fi

    if python -m python_refactor_mcp --help > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ CLI --help works${NC}"
    else
        echo -e "  ${RED}✗ CLI --help failed${NC}"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "  ${RED}✗ Package installation failed${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# 9. Documentation
echo "📚 Documentation"
echo "---------------"
check "README complete" "test $(wc -l < README.md) -gt 50"
check "QUICKSTART exists" "test -f QUICKSTART.md"
check "TEST_COVERAGE exists" "test -f TEST_COVERAGE.md"
check "CI_CD_SETUP exists" "test -f CI_CD_SETUP.md"
check "RELEASE_NOTES exists" "test -f RELEASE_NOTES_v${PYPROJECT_VERSION}.md"
check "PUBLISHING_GUIDE exists" "test -f PUBLISHING_GUIDE.md"

echo ""

# 10. PyPI metadata
echo "🏷️  PyPI Metadata"
echo "----------------"
check "Package name" "grep -q 'name = \"python-refactor-mcp\"' pyproject.toml"
check "License specified" "grep -q 'license = { text = \"MIT\" }' pyproject.toml"
check "Authors listed" "grep -q 'authors =' pyproject.toml"
check "Keywords present" "grep -q 'keywords =' pyproject.toml"
check "Classifiers present" "grep -q 'classifiers =' pyproject.toml"
check "URLs present" "grep -q '\[project.urls\]' pyproject.toml"

echo ""

# Final summary
echo "=================================================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - READY FOR RELEASE!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review PUBLISHING_GUIDE.md"
    echo "  2. Upload to PyPI: twine upload dist/*"
    echo "  3. Create GitHub release"
    echo "  4. Submit to MCP Registry"
    exit 0
else
    echo -e "${RED}❌ $FAILURES CHECK(S) FAILED${NC}"
    echo ""
    echo "Please fix the issues above before releasing."
    exit 1
fi
