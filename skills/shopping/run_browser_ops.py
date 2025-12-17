#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Operations Runner
==========================

This script runs browser operation code snippets without requiring full Python boilerplate.

**Persistent Browser Mode (Recommended):**
    First start the browser server in a separate terminal:
        python browser_server.py
    
    Then run commands (browser stays alive between calls):
        python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')"
        python run_browser_ops.py -c "await browser.snapshot()"

**Standalone Mode (browser closes after each call):**
        python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')" --standalone

Example operations.txt:
    await browser.navigate("http://localhost:7770")
    await browser.click(ref="e31", element="Advanced Search link")
    await browser.snapshot()
"""

import asyncio
import argparse
import json
import os
import sys

# Server configuration (must match browser_server.py)
SOCKET_PATH = "/tmp/browser_server.sock"


def is_server_running() -> bool:
    """Check if browser server is running."""
    return os.path.exists(SOCKET_PATH)


async def send_to_server(code: str) -> str:
    """Send command to browser server via Unix socket."""
    try:
        reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)
        
        # Send request
        request = json.dumps({"command": code})
        writer.write(request.encode())
        await writer.drain()
        writer.write_eof()
        
        # Read response
        data = await reader.read()
        response = json.loads(data.decode())
        
        writer.close()
        await writer.wait_closed()
        
        if response.get("success"):
            return response.get("result", "OK")
        else:
            raise Exception(response.get("error", "Unknown error"))
            
    except ConnectionRefusedError:
        raise Exception("Browser server not running. Start it with: python browser_server.py")
    except FileNotFoundError:
        raise Exception("Browser server not running. Start it with: python browser_server.py")


async def run_standalone(code: str):
    """Run browser operations in standalone mode (browser closes after execution)."""
    from utils import BrowserTools
    
    async with BrowserTools(timeout=300) as browser:
        exec_globals = {"browser": browser, "asyncio": asyncio}
        
        lines = [line.strip() for line in code.strip().split('\n') 
                 if line.strip() and not line.strip().startswith('#')]
        
        for line in lines:
            if line.startswith('await '):
                expr = line[6:]
                result = await eval(expr, exec_globals)
                if result:
                    print(f"Result: {result}")
            elif line.startswith('result = await '):
                expr = line[15:]
                exec_globals['result'] = await eval(expr, exec_globals)
                print(f"Stored result")
            elif '=' in line and 'await' in line:
                var_name, expr = line.split('=', 1)
                var_name = var_name.strip()
                expr = expr.strip()
                if expr.startswith('await '):
                    expr = expr[6:]
                exec_globals[var_name] = await eval(expr, exec_globals)
                print(f"Stored {var_name}")
            else:
                exec(line, exec_globals)


async def run_operations(code: str, standalone: bool = False):
    """
    Run browser operations code.
    
    Args:
        code: Python code containing browser operations (await browser.xxx calls)
        standalone: If True, run in standalone mode (browser closes after execution)
                   If False, connect to browser server (browser stays alive)
    """
    if standalone:
        await run_standalone(code)
    else:
        # Try to connect to server
        if not is_server_running():
            print("⚠️  Browser server not running!")
            print("   Starting in standalone mode (browser will close after execution)")
            print("   For persistent browser, run: python browser_server.py")
            print()
            await run_standalone(code)
        else:
            result = await send_to_server(code)
            if result and result != "OK":
                print(f"Result: {result}")


def main():
    parser = argparse.ArgumentParser(
        description="Run browser operation code snippets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # First, start the browser server (keeps browser alive):
    python browser_server.py &
    
    # Then run commands (browser persists between calls):
    python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')"
    python run_browser_ops.py -c "await browser.snapshot()"
    
    # Run in standalone mode (browser closes after each call):
    python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')" --standalone
    
    # Stop the browser server:
    python browser_server.py --stop
"""
    )
    parser.add_argument("file", nargs="?", help="File containing browser operations")
    parser.add_argument("-c", "--code", help="Browser operations code string")
    parser.add_argument("--standalone", action="store_true",
                        help="Run in standalone mode (browser closes after execution)")
    
    args = parser.parse_args()
    
    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        parser.print_help()
        sys.exit(1)
    
    print("Running browser operations...")
    print("-" * 40)
    asyncio.run(run_operations(code, standalone=args.standalone))
    print("-" * 40)
    print("Done!")


if __name__ == "__main__":
    main()
