#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Operations Runner
=========================

This script runs GitHub operation code snippets without requiring full Python boilerplate.
Designed for quick, atomic GitHub operations using the GitHubTools wrapper.

Usage:
    # Run a single operation
    python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'path', 'content', 'message', 'main')"

Examples:
    # Create/update a file
    python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'README.md', '# Hello', 'Add readme', 'main')"
    
    # Push multiple files in one commit
    python run_github_ops.py -c "await github.push_files('owner', 'repo', 'main', [{'path': 'a.txt', 'content': 'A'}, {'path': 'b.txt', 'content': 'B'}], 'Add files')"
    
    # Get file contents (to check SHA for updates)
    python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'README.md')"
"""

import asyncio
import argparse
import sys

from utils import GitHubTools


async def run_operations(code: str):
    """
    Run GitHub operations code.
    
    Args:
        code: Python code containing GitHub operations (await github.xxx calls)
    """
    async with GitHubTools(timeout=300) as github:
        exec_globals = {"github": github, "asyncio": asyncio}
        
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


def main():
    parser = argparse.ArgumentParser(
        description="Run GitHub operation code snippets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Create/update a single file
    python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'file.txt', 'content', 'message', 'main')"
    
    # Push multiple files in one commit
    python run_github_ops.py -c "await github.push_files('owner', 'repo', 'main', [{'path': 'a.txt', 'content': 'A'}], 'Add files')"
    
    # Get file contents
    python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'README.md')"
"""
    )
    parser.add_argument("file", nargs="?", help="File containing GitHub operations")
    parser.add_argument("-c", "--code", help="GitHub operations code string")
    
    args = parser.parse_args()
    
    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        parser.print_help()
        sys.exit(1)
    
    print("Running GitHub operations...")
    print("-" * 40)
    asyncio.run(run_operations(code))
    print("-" * 40)
    print("Done!")


if __name__ == "__main__":
    main()
