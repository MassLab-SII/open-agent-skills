#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Folders Script
======================

Create multiple folders under a target directory.

Usage:
    python create_folders.py <target_directory> <folder_names...>

Example:
    python create_folders.py /path/to/directory folder1 folder2 folder3
"""

import asyncio
import os
import argparse

from utils import FileSystemTools


async def create_folders(target_dir: str, folder_names: list):
    """Create multiple folders under the target directory"""
    async with FileSystemTools(target_dir) as fs:
        print(f"Creating {len(folder_names)} folders in {target_dir}...")
        print("-" * 40)
        
        for name in folder_names:
            folder_path = os.path.join(target_dir, name)
            success = await fs.create_directory(folder_path)
            if success:
                print(f"  Created: {name}/")
            else:
                print(f"  Failed: {name}/")
        
        print("-" * 40)
        print(f"Done! Created {len(folder_names)} folders.")


def main():
    parser = argparse.ArgumentParser(
        description='Create multiple folders under a target directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create 3 folders
  python create_folders.py /path/to/directory folder1 folder2 folder3
  
  # Create folders with specific names
  python create_folders.py /path/to/directory experiments learning personal
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory where folders will be created'
    )
    parser.add_argument(
        'folder_names',
        nargs='+',
        help='Names of folders to create'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path if relative
    target_dir = os.path.abspath(args.target_directory)
    
    # Validate directory exists
    if not os.path.isdir(target_dir):
        # print(f"Error: Directory '{target_dir}' does not exist")
        return
    
    asyncio.run(create_folders(target_dir, args.folder_names))


if __name__ == "__main__":
    main()
