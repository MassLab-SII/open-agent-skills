#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Move Multiple Files Tool
=========================

Move multiple files to a target directory in a single operation.

Usage:
    python move_files.py <target_directory> <file1> <file2> ...

Example:
    python move_files.py ./archive file1.txt file2.txt file3.txt
"""

import argparse
import os
import shutil
import sys


def move_files(target_dir: str, files: list[str]) -> tuple[list[str], list[str]]:
    """
    Move multiple files to a target directory.
    
    Args:
        target_dir: Target directory path
        files: List of file paths to move
        
    Returns:
        Tuple of (successfully moved files, failed files)
    """
    success = []
    failed = []
    
    for file_path in files:
        try:
            if not os.path.exists(file_path):
                print(f"  Warning: '{file_path}' does not exist, skipping")
                failed.append(file_path)
                continue
            
            # Get the filename
            filename = os.path.basename(file_path)
            dest_path = os.path.join(target_dir, filename)
            
            # Move the file
            shutil.move(file_path, dest_path)
            print(f"  Moved: {file_path} -> {dest_path}")
            success.append(file_path)
            
        except Exception as e:
            print(f"  Failed: {file_path} ({e})")
            failed.append(file_path)
    
    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description='Move multiple files to a target directory.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Move 3 files to archive folder
    python move_files.py ./archive file1.txt file2.txt file3.txt
    
    # Move files from different directories
    python move_files.py ./backup ./data/log1.txt ./data/log2.txt ./temp/cache.dat
"""
    )
    parser.add_argument(
        'target_directory',
        help='Target directory where files will be moved'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Files to move (one or more file paths)'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    target_dir = os.path.abspath(args.target_directory)
    files = [os.path.abspath(f) for f in args.files]
    
    # Validate target directory exists
    if not os.path.isdir(target_dir):
        print(f"Error: Target directory '{target_dir}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    print(f"Moving {len(files)} file(s) to {target_dir}...")
    print("-" * 40)
    
    success, failed = move_files(target_dir, files)
    
    print("-" * 40)
    print(f"Done! Moved {len(success)} file(s), {len(failed)} failed.")
    
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
