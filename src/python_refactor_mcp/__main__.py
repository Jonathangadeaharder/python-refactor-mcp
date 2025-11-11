"""
Entry point for the Python Refactor MCP server.

Usage:
    python -m python_refactor_mcp <workspace_root>

    or with uv:
    uv run python-refactor-mcp <workspace_root>
"""

import asyncio
import logging
import sys
from pathlib import Path

from .mcp_server import PythonRefactorMCPServer


def setup_logging() -> None:
    """Configure logging for the server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Log to stderr so it doesn't interfere with MCP stdio transport
            logging.StreamHandler(sys.stderr)
        ],
    )


async def main() -> None:
    """Main entry point for the MCP server."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python -m python_refactor_mcp <workspace_root>")
        sys.exit(1)

    workspace_root = sys.argv[1]

    # Validate workspace root
    workspace_path = Path(workspace_root).resolve()
    if not workspace_path.exists():
        logger.error(f"Workspace root does not exist: {workspace_root}")
        sys.exit(1)

    if not workspace_path.is_dir():
        logger.error(f"Workspace root is not a directory: {workspace_root}")
        sys.exit(1)

    logger.info(f"Starting Python Refactor MCP Server for workspace: {workspace_path}")

    # Create and start server
    server = PythonRefactorMCPServer(str(workspace_path))

    try:
        # Start LSP client
        await server.start()

        # Run MCP server (blocks until shutdown)
        await server.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean shutdown
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
