#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Operations Runner
==========================

This script runs browser operation code snippets without requiring full Python boilerplate.

Usage:
    # Method 1: Pass operations file
    python run_browser_ops.py operations.txt
    
    # Method 2: Pass operations directly as string
    python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')"

Example operations.txt:
    await browser.navigate("http://localhost:7770")
    await browser.click(ref="e31", element="Advanced Search link")
    await browser.snapshot()
"""

import asyncio
import argparse
import sys
from utils import BrowserTools


async def run_operations(code: str):
    """
    Run browser operations code.
    
    Args:
        code: Python code containing browser operations (await browser.xxx calls)
    """
    async with BrowserTools() as browser:
        # Execute the code with browser in scope
        exec_globals = {"browser": browser, "asyncio": asyncio}
        
        # Actually, we need to use await directly, let's do it differently
        # Create a coroutine that executes each line
        lines = [line.strip() for line in code.strip().split('\n') if line.strip() and not line.strip().startswith('#')]
        
        for line in lines:
            if line.startswith('await '):
                # Execute await expression
                expr = line[6:]  # Remove 'await '
                result = await eval(expr, exec_globals)
                if result:
                    print(f"Result: {result[:500]}..." if len(str(result)) > 500 else f"Result: {result}")
            elif line.startswith('result = await '):
                # Store result
                expr = line[15:]  # Remove 'result = await '
                exec_globals['result'] = await eval(expr, exec_globals)
                print(f"Stored result")
            elif '=' in line and 'await' in line:
                # Variable assignment with await
                var_name, expr = line.split('=', 1)
                var_name = var_name.strip()
                expr = expr.strip()
                if expr.startswith('await '):
                    expr = expr[6:]
                exec_globals[var_name] = await eval(expr, exec_globals)
                print(f"Stored {var_name}")
            else:
                # Regular Python statement
                exec(line, exec_globals)


def main():
    parser = argparse.ArgumentParser(
        description="Run browser operation code snippets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run from file
    python run_browser_ops.py ops.txt
    
    # Run inline code
    python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')"
    
    # Run multiple inline operations
    python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')
await browser.snapshot()"
"""
    )
    parser.add_argument("file", nargs="?", help="File containing browser operations")
    parser.add_argument("-c", "--code", help="Browser operations code string")
    
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
    asyncio.run(run_operations(code))
    print("-" * 40)
    print("Done!")


if __name__ == "__main__":
    main()

