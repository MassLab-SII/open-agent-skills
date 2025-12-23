#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Operations Runner
=========================

This script runs GitHub operation code snippets without requiring full Python boilerplate.
Designed for quick, atomic GitHub operations using the GitHubTools wrapper.

Usage:
    # Run a single operation
    python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'title', body='desc', method='create')"

Examples:
    # Create an issue
    python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'Bug Report', body='Description', method='create')"
    
    # Close an issue
    python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'title', issue_number=42, state='closed', method='update')"
    
    # Create a PR
    python run_github_ops.py -c "await github.create_pull_request('owner', 'repo', 'Add feature', 'feature-branch', 'main')"
    
    # Merge a PR
    python run_github_ops.py -c "await github.merge_pull_request('owner', 'repo', 42, merge_method='squash')"
    
    # Add comment to issue/PR
    python run_github_ops.py -c "await github.add_issue_comment('owner', 'repo', 42, 'LGTM!')"
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
    # Create an issue
    python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'Bug', body='desc', method='create')"
    
    # Add comment
    python run_github_ops.py -c "await github.add_issue_comment('owner', 'repo', 42, 'Thanks!')"
    
    # Create PR
    python run_github_ops.py -c "await github.create_pull_request('owner', 'repo', 'Title', 'head', 'base')"
    
    # Merge PR
    python run_github_ops.py -c "await github.merge_pull_request('owner', 'repo', 42, merge_method='squash')"
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
