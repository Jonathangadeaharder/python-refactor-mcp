"""
LSP Client for JSON-RPC 2.0 communication with Pyright language server.

This module implements an asynchronous LSP client that manages:
- Subprocess lifecycle (spawn, initialize, shutdown)
- JSON-RPC 2.0 message framing (Content-Length headers)
- Request/response correlation (using message IDs)
- File synchronization (didOpen, didChange, didSave notifications)
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
import os

logger = logging.getLogger(__name__)


class LSPClient:
    """
    Asynchronous LSP client for communicating with Pyright language server.

    Architecture:
    - Manages a persistent subprocess running pyright-langserver
    - Implements JSON-RPC 2.0 protocol over stdin/stdout
    - Maintains request/response correlation via message IDs
    - Keeps LSP's internal state synchronized with file system changes
    """

    def __init__(self, workspace_root: str):
        """
        Initialize LSP client.

        Args:
            workspace_root: Absolute path to the Python project root
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_uri = f"file://{self.workspace_root}"

        # Subprocess management
        self.process: Optional[asyncio.subprocess.Process] = None
        self.stdin_writer: Optional[asyncio.StreamWriter] = None
        self.stdout_reader: Optional[asyncio.StreamReader] = None

        # JSON-RPC state
        self.message_id = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}

        # LSP state
        self.initialized = False
        self.server_capabilities: Dict[str, Any] = {}
        self.open_documents: set = set()

        # Background task for reading responses
        self.read_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """
        Start the Pyright language server subprocess and perform initialization handshake.
        """
        logger.info(f"Starting Pyright LSP server for workspace: {self.workspace_root}")

        # Check if pyright-langserver is available
        pyright_path = self._find_pyright()
        if not pyright_path:
            raise RuntimeError(
                "pyright-langserver not found. Install with: npm install -g pyright"
            )

        # Spawn the subprocess
        self.process = await asyncio.create_subprocess_exec(
            pyright_path,
            "--stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.stdin_writer = self.process.stdin
        self.stdout_reader = self.process.stdout

        # Start background task to read responses
        self.read_task = asyncio.create_task(self._read_responses())

        # Perform LSP initialize handshake
        await self._initialize()

        logger.info("Pyright LSP server started and initialized successfully")

    def _find_pyright(self) -> Optional[str]:
        """
        Find pyright-langserver executable.

        Returns:
            Path to pyright-langserver or None if not found
        """
        # Try common locations
        candidates = [
            "pyright-langserver",  # In PATH
            "npx pyright-langserver",  # Via npx
            str(Path.home() / ".npm-global/bin/pyright-langserver"),
            "/usr/local/bin/pyright-langserver",
        ]

        for candidate in candidates:
            try:
                # Check if command exists
                result = os.popen(f"which {candidate.split()[0]}").read().strip()
                if result:
                    return candidate
            except Exception:
                continue

        return None

    async def _initialize(self) -> None:
        """
        Perform LSP initialize handshake.

        This sends the 'initialize' request with client capabilities
        and waits for the server's response with server capabilities.
        """
        init_params = {
            "processId": os.getpid(),
            "rootUri": self.workspace_uri,
            "rootPath": str(self.workspace_root),
            "capabilities": {
                "workspace": {
                    "applyEdit": True,
                    "workspaceEdit": {
                        "documentChanges": True,
                        "resourceOperations": ["create", "rename", "delete"],
                    },
                    "didChangeConfiguration": {"dynamicRegistration": False},
                },
                "textDocument": {
                    "synchronization": {
                        "dynamicRegistration": False,
                        "willSave": False,
                        "willSaveWaitUntil": False,
                        "didSave": True,
                    },
                    "completion": {"dynamicRegistration": False},
                    "hover": {"dynamicRegistration": False},
                    "definition": {"dynamicRegistration": False},
                    "references": {"dynamicRegistration": False},
                    "rename": {"dynamicRegistration": False},
                    "codeAction": {
                        "dynamicRegistration": False,
                        "codeActionLiteralSupport": {
                            "codeActionKind": {
                                "valueSet": [
                                    "quickfix",
                                    "refactor",
                                    "refactor.extract",
                                    "refactor.inline",
                                    "refactor.rewrite",
                                ]
                            }
                        },
                    },
                },
            },
            "initializationOptions": {},
        }

        result = await self.send_request("initialize", init_params)
        self.server_capabilities = result.get("capabilities", {})

        # Send initialized notification
        await self.send_notification("initialized", {})

        self.initialized = True
        logger.info(f"LSP initialized. Server capabilities: {list(self.server_capabilities.keys())}")

    async def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """
        Send a JSON-RPC request and wait for response.

        Args:
            method: LSP method name (e.g., "textDocument/rename")
            params: Method parameters

        Returns:
            The result from the LSP server

        Raises:
            RuntimeError: If server returns an error
        """
        if not self.initialized and method != "initialize":
            raise RuntimeError("LSP client not initialized")

        self.message_id += 1
        request_id = self.message_id

        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        # Create a future to wait for the response
        future = asyncio.Future()
        self.pending_requests[request_id] = future

        # Send the request
        await self._send_message(message)

        # Wait for the response
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            del self.pending_requests[request_id]
            raise RuntimeError(f"LSP request '{method}' timed out after 30 seconds")

    async def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """
        Send a JSON-RPC notification (no response expected).

        Args:
            method: LSP method name (e.g., "textDocument/didChange")
            params: Method parameters
        """
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        await self._send_message(message)

    async def _send_message(self, message: Dict[str, Any]) -> None:
        """
        Send a JSON-RPC message with proper framing.

        JSON-RPC 2.0 over LSP uses Content-Length header framing:
        Content-Length: <bytes>\r\n\r\n<json-content>
        """
        if not self.stdin_writer:
            raise RuntimeError("LSP subprocess not started")

        content = json.dumps(message)
        content_bytes = content.encode("utf-8")

        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
        header_bytes = header.encode("utf-8")

        self.stdin_writer.write(header_bytes + content_bytes)
        await self.stdin_writer.drain()

        logger.debug(f"Sent LSP message: {message.get('method', message.get('id'))}")

    async def _read_responses(self) -> None:
        """
        Background task to continuously read and process responses from LSP server.

        This task runs for the lifetime of the LSP connection and:
        - Reads JSON-RPC messages with Content-Length framing
        - Correlates responses with pending requests
        - Handles server notifications (diagnostics, etc.)
        """
        try:
            while True:
                if not self.stdout_reader:
                    break

                # Read headers
                headers = {}
                while True:
                    line = await self.stdout_reader.readline()
                    if not line:
                        return  # EOF

                    line = line.decode("utf-8").strip()
                    if not line:
                        break  # Empty line marks end of headers

                    if ":" in line:
                        key, value = line.split(":", 1)
                        headers[key.strip()] = value.strip()

                # Read content
                content_length = int(headers.get("Content-Length", 0))
                if content_length == 0:
                    continue

                content_bytes = await self.stdout_reader.readexactly(content_length)
                content = content_bytes.decode("utf-8")
                message = json.loads(content)

                # Process message
                await self._process_message(message)

        except asyncio.CancelledError:
            logger.info("LSP response reader task cancelled")
        except Exception as e:
            logger.error(f"Error reading LSP responses: {e}", exc_info=True)

    async def _process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a received JSON-RPC message.

        Args:
            message: Parsed JSON-RPC message
        """
        if "id" in message:
            # This is a response to a request
            request_id = message["id"]
            future = self.pending_requests.pop(request_id, None)

            if future:
                if "result" in message:
                    future.set_result(message["result"])
                elif "error" in message:
                    error = message["error"]
                    future.set_exception(
                        RuntimeError(f"LSP error: {error.get('message', 'Unknown error')}")
                    )
        elif "method" in message:
            # This is a notification from the server
            method = message["method"]
            params = message.get("params", {})

            # Handle specific notifications
            if method == "textDocument/publishDiagnostics":
                # Server is sending diagnostics - we could log or store these
                uri = params.get("uri", "")
                diagnostics = params.get("diagnostics", [])
                logger.debug(f"Received {len(diagnostics)} diagnostics for {uri}")
            else:
                logger.debug(f"Received notification: {method}")

    async def open_document(self, file_path: str) -> None:
        """
        Notify LSP server that a document is opened.

        This is critical for maintaining LSP state synchronization.

        Args:
            file_path: Absolute path to the file
        """
        file_path = Path(file_path).resolve()
        uri = f"file://{file_path}"

        if uri in self.open_documents:
            return  # Already open

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return

        # Determine language ID
        language_id = "python"

        # Send didOpen notification
        await self.send_notification(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id,
                    "version": 1,
                    "text": text,
                }
            },
        )

        self.open_documents.add(uri)
        logger.debug(f"Opened document: {uri}")

    async def close_document(self, file_path: str) -> None:
        """
        Notify LSP server that a document is closed.

        Args:
            file_path: Absolute path to the file
        """
        file_path = Path(file_path).resolve()
        uri = f"file://{file_path}"

        if uri not in self.open_documents:
            return

        await self.send_notification(
            "textDocument/didClose",
            {"textDocument": {"uri": uri}},
        )

        self.open_documents.remove(uri)
        logger.debug(f"Closed document: {uri}")

    async def did_change_document(self, file_path: str, new_text: str) -> None:
        """
        Notify LSP server that a document's content has changed.

        This is critical after applying edits to keep LSP state in sync.

        Args:
            file_path: Absolute path to the file
            new_text: New content of the file
        """
        file_path = Path(file_path).resolve()
        uri = f"file://{file_path}"

        # Ensure document is open first
        if uri not in self.open_documents:
            await self.open_document(str(file_path))

        await self.send_notification(
            "textDocument/didChange",
            {
                "textDocument": {"uri": uri, "version": 1},
                "contentChanges": [{"text": new_text}],
            },
        )

        logger.debug(f"Notified change for document: {uri}")

    async def shutdown(self) -> None:
        """
        Gracefully shut down the LSP server.
        """
        logger.info("Shutting down Pyright LSP server")

        if self.initialized:
            try:
                await self.send_request("shutdown", {})
                await self.send_notification("exit", {})
            except Exception as e:
                logger.error(f"Error during LSP shutdown: {e}")

        # Cancel read task
        if self.read_task:
            self.read_task.cancel()
            try:
                await self.read_task
            except asyncio.CancelledError:
                pass

        # Close streams
        if self.stdin_writer:
            self.stdin_writer.close()
            await self.stdin_writer.wait_closed()

        # Terminate process
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

        logger.info("Pyright LSP server shut down successfully")
