#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Statistics Tool
====================

Generate file statistics for a directory: total files, folders, and size.
Statistics exclude .DS_Store files from count but include them in size calculation.
"""

import argparse
import os
import sys


def get_file_statistics(directory: str) -> tuple[int, int, int]: #verified
    """
    Calculate file statistics for a directory.
    
    Args:
        directory: Path to the directory to analyze
        
    Returns:
        Tuple of (total_files, total_folders, total_size)
        - total_files: Number of files (excluding .DS_Store)
        - total_folders: Number of folders
        - total_size: Total size in bytes (including .DS_Store)
    """
    total_files = 0
    total_folders = 0
    total_size = 0
    
    for root, dirs, files in os.walk(directory):
        # Count folders (excluding the root directory itself)
        total_folders += len(dirs)
        
        for filename in files:
            filepath = os.path.join(root, filename)
            
            # Get file size (including .DS_Store)
            try:
                file_size = os.path.getsize(filepath)
                total_size += file_size
            except OSError:
                pass
            
            # Count files (excluding .DS_Store)
            if filename != '.DS_Store':
                total_files += 1
    
    # Print results for model context
    print(f"total number of files: {total_files}")
    print(f"total number of folders: {total_folders}")
    print(f"total size of all files: {total_size}")
    
    return total_files, total_folders, total_size


def main():
    parser = argparse.ArgumentParser(
        description='Generate file statistics for a directory.'
    )
    parser.add_argument(
        'directory',
        help='Path to the directory to analyze'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path if relative
    directory = os.path.abspath(args.directory)
    
    # Validate directory exists
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Get statistics (function already prints results)
    total_files, total_folders, total_size = get_file_statistics(directory)


if __name__ == '__main__':
    main()
