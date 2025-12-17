#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Server - Background Process for Persistent Browser Sessions
====================================================================

This server keeps the MCP Playwright browser alive and accepts commands via Unix socket.
Run this in the background, then use browser_client.py or run_browser_ops.py to send commands.

Usage:
    # Start server (foreground)
    python browser_server.py
    
    # Start server (background)
    python browser_server.py &
    
    # Stop server
    python browser_server.py --stop
"""

import asyncio
import json
import os
import signal
import sys
from pathlib import Path

# Server configuration
SOCKET_PATH = "/tmp/browser_server.sock"
PID_FILE = "/tmp/browser_server.pid"

# Import BrowserTools from utils
sys.path.insert(0, str(Path(__file__).parent))
from utils import BrowserTools, print_result


class BrowserServer:
    """
    Background server that keeps MCP browser session alive.
    Accepts commands via Unix socket and executes them on the persistent browser.
    """
    
    def __init__(self, socket_path: str = SOCKET_PATH):
        self.socket_path = socket_path
        self.browser: BrowserTools = None
        self.server = None
        self.running = False
    
    async def start(self):
        """Start the browser server."""
        # Clean up old socket if exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        # Write PID file
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        print(f"🚀 Starting Browser Server (PID: {os.getpid()})")
        print(f"   Socket: {self.socket_path}")
        
        # Start MCP browser
        print("   Initializing browser...")
        self.browser = BrowserTools(timeout=300)
        await self.browser.__aenter__()
        print("   ✓ Browser ready!")
        
        # Start Unix socket server
        self.server = await asyncio.start_unix_server(
            self.handle_client, 
            path=self.socket_path
        )
        self.running = True
        
        print(f"   ✓ Server listening on {self.socket_path}")
        print("   Use run_browser_ops.py to send commands")
        print("-" * 50)
        
        # Keep server running
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming client connection."""
        try:
            # Read command
            data = await reader.read(65536)  # 64KB max
            if not data:
                return
            
            request = json.loads(data.decode())
            command = request.get("command", "")
            
            print(f"📥 Received: {command[:100]}...")
            
            # Execute command
            result = await self.execute_command(command)
            
            # Send response
            response = json.dumps({"success": True, "result": result})
            writer.write(response.encode())
            await writer.drain()
            
        except Exception as e:
            error_response = json.dumps({"success": False, "error": str(e)})
            writer.write(error_response.encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def execute_command(self, code: str) -> str:
        """Execute browser command code."""
        exec_globals = {"browser": self.browser, "asyncio": asyncio}
        results = []
        
        lines = [line.strip() for line in code.strip().split('\n') 
                 if line.strip() and not line.strip().startswith('#')]
        
        for line in lines:
            if line.startswith('await '):
                expr = line[6:]
                result = await eval(expr, exec_globals)
                if result:
                    results.append(str(result))
            elif '=' in line and 'await' in line:
                var_name, expr = line.split('=', 1)
                var_name = var_name.strip()
                expr = expr.strip()
                if expr.startswith('await '):
                    expr = expr[6:]
                exec_globals[var_name] = await eval(expr, exec_globals)
                results.append(f"Stored {var_name}")
            else:
                exec(line, exec_globals)
        
        return '\n'.join(results) if results else "OK"
    
    async def stop(self):
        """Stop the browser server."""
        print("\n🛑 Stopping Browser Server...")
        self.running = False
        
        if self.browser:
            await self.browser.__aexit__(None, None, None)
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Clean up
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
        
        print("   ✓ Server stopped")


def stop_server():
    """Stop the running server by PID."""
    if not os.path.exists(PID_FILE):
        print("No server running (PID file not found)")
        return
    
    with open(PID_FILE, 'r') as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to server (PID: {pid})")
        
        # Clean up socket
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
            
    except ProcessLookupError:
        print(f"Server process {pid} not found, cleaning up...")
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)


def is_server_running() -> bool:
    """Check if server is running."""
    return os.path.exists(SOCKET_PATH)


async def main():
    server = BrowserServer()
    
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        asyncio.create_task(server.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await server.start()
    except asyncio.CancelledError:
        await server.stop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stop":
        stop_server()
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        if is_server_running():
            print("Browser server is running")
        else:
            print("Browser server is not running")
    else:
        asyncio.run(main())
