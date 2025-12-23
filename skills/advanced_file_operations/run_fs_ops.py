#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File System Operations Runner
==============================

This script runs filesystem operation code snippets.

Usage:
    python run_fs_ops.py -c "await fs.read_text_file('/path/to/file.txt')"
    python run_fs_ops.py -c "await fs.list_files('/path/to/directory')"

"""

import asyncio
import argparse
import sys

from utils import FileSystemTools


async def run_operations(code: str, base_directory: str):
    """
    Run filesystem operations code.
    
    Args:
        code: Python code containing filesystem operations (await fs.xxx calls)
        base_directory: Base directory for file operations (allowed directory)
    """
    async with FileSystemTools(base_directory) as fs:
        exec_globals = {"fs": fs, "asyncio": asyncio}
        
        lines = [line.strip() for line in code.strip().split('\n') 
                 if line.strip() and not line.strip().startswith('#')]
        
        for line in lines:
            if line.startswith('await '):
                expr = line[6:]
                result = await eval(expr, exec_globals)
                if result is not None:
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
        description="Run filesystem operation code snippets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Read a file
    python run_fs_ops.py /path/to/base -c "await fs.read_text_file('/path/to/file.txt')"
    
    # List directory
    python run_fs_ops.py /path/to/base -c "await fs.list_files('/path/to/directory')"
    
    # Write a file
    python run_fs_ops.py /path/to/base -c "await fs.write_file('/path/to/new.txt', 'hello')"
    
    # Get file info
    python run_fs_ops.py /path/to/base -c "await fs.get_file_info('/path/to/file.txt')"
    
    # Search files
    python run_fs_ops.py /path/to/base -c "await fs.search_files('*.py')"
"""
    )
    parser.add_argument("base_directory", help="Base directory for file operations (allowed directory)")
    parser.add_argument("-c", "--code", help="Filesystem operations code string")
    parser.add_argument("-f", "--file", help="File containing filesystem operations")
    
    args = parser.parse_args()
    
    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        parser.print_help()
        sys.exit(1)
    
    print("Running filesystem operations...")
    print("-" * 40)
    asyncio.run(run_operations(code, args.base_directory))
    print("-" * 40)
    print("Done!")


if __name__ == "__main__":
    main()
