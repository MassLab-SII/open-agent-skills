#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List All Files Tool
====================

Recursively list all files under a given directory path.
"""

import argparse
import os
import sys


def list_all_files(directory: str, include_hidden: bool = False) -> list[str]: #verified
    """
    Recursively list all files under the given directory.
    
    Args:
        directory: Path to the directory to scan
        include_hidden: If True, include hidden files (like .DS_Store)
        
    Returns:
        List of file paths relative to the input directory
    """
    all_files = []
    
    for root, dirs, files in os.walk(directory):
        # Get relative path from the input directory
        rel_root = os.path.relpath(root, directory)
        
        for filename in files:
            # Skip hidden files if not included
            if not include_hidden and filename.startswith('.'):
                continue
            
            # Build relative path
            if rel_root == '.':
                rel_path = filename
            else:
                rel_path = os.path.join(rel_root, filename)
            
            all_files.append(rel_path)
    
    # Sort for consistent output
    all_files.sort()
    
    # Print results for model context
    print(f"Found {len(all_files)} files:")
    for f in all_files:
        print(f)
    
    return all_files


def main():
    parser = argparse.ArgumentParser(
        description='Recursively list all files under a given directory.'
    )
    parser.add_argument(
        'directory',
        help='Path to the directory to scan'
    )
    parser.add_argument(
        '--include-hidden',
        action='store_true',
        help='Include hidden files (like .DS_Store)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # List all files (function already prints results)
    files = list_all_files(args.directory, args.include_hidden)


if __name__ == '__main__':
    main()
