#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find and Organize Duplicate Files Script (Using utils.py)
==========================================================

This script identifies files with duplicate content in a directory and moves them
to a 'duplicates' subdirectory, leaving only unique files in the original location.

Usage:
    python find_duplicates.py <target_directory>

Example:
    python find_duplicates.py /path/to/directory
"""

import asyncio
import os
import argparse
import hashlib
from typing import List, Dict, Set
from collections import defaultdict

from utils import FileSystemTools


class DuplicateFileFinder:
    """Finder that identifies and organizes files with duplicate content"""
    
    def __init__(self, target_dir: str, duplicates_dir_name: str = "duplicates"):
        """
        Initialize the duplicate finder
        
        Args:
            target_dir: Target directory to scan for duplicates
            duplicates_dir_name: Name of the directory to store duplicates (default: "duplicates")
        """
        self.target_dir = target_dir
        self.duplicates_dir_name = duplicates_dir_name
    
    async def find_and_organize_duplicates(self):
        """Main workflow to find and organize duplicate files"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: List all files in the directory
            print("Step 1: Listing files...")
            files = await fs.list_files()
            print(f"Found {len(files)} files\n")
            
            if not files:
                print("No files to process.")
                return
            
            # Step 2: Read all file contents
            print("Step 2: Reading file contents...")
            file_contents = await self._read_all_files(fs, files)
            print(f"Successfully read {len(file_contents)} files\n")
            
            # Step 3: Identify duplicate groups
            print("Step 3: Identifying duplicate files...")
            duplicate_groups = self._identify_duplicates(file_contents)
            
            if not duplicate_groups:
                print("No duplicate files found.")
                return
            
            print(f"Found {len(duplicate_groups)} groups of duplicates:")
            for i, group in enumerate(duplicate_groups, 1):
                print(f"  Group {i}: {', '.join(group)}")
            print()
            
            # Step 4: Create duplicates directory
            print("Step 4: Creating 'duplicates' directory...")
            duplicates_path = os.path.join(self.target_dir, self.duplicates_dir_name)
            success = await fs.create_directory(duplicates_path)
            if success:
                print(f"  Created: {self.duplicates_dir_name}/\n")
            
            # Step 5: Move duplicate files
            print("Step 5: Moving duplicate files...")
            await self._move_duplicates(fs, duplicate_groups)
            
            print("\nTask completed successfully!")
            print(f"All duplicate files have been moved to '{self.duplicates_dir_name}/' directory")
    
    async def _read_all_files(self, fs: FileSystemTools, files: List[str]) -> Dict[str, str]:
        """
        Read contents of all files
        
        Args:
            fs: FileSystemTools instance
            files: List of file names
            
        Returns:
            Dictionary mapping filename to content
        """
        file_contents = {}
        
        # Read files individually for more reliable content extraction
        print("  Reading files individually for accurate content comparison...")
        for filename in files:
            file_path = os.path.join(self.target_dir, filename)
            content = await fs.read_text_file(file_path)
            if content is not None:
                file_contents[filename] = content
                print(f"  Read: {filename} ({len(content)} bytes)")
        
        return file_contents
    
    def _identify_duplicates(self, file_contents: Dict[str, str]) -> List[List[str]]:
        """
        Identify groups of files with identical content
        
        Args:
            file_contents: Dictionary mapping filename to content
            
        Returns:
            List of duplicate groups (each group is a list of filenames)
        """
        # Group files by content hash
        content_to_files = defaultdict(list)
        
        for filename, content in file_contents.items():
            # Calculate hash of content
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            content_to_files[content_hash].append(filename)
        
        # Extract groups with more than one file (duplicates)
        duplicate_groups = []
        for files in content_to_files.values():
            if len(files) > 1:
                duplicate_groups.append(sorted(files))
        
        return duplicate_groups
    
    async def _move_duplicates(self, fs: FileSystemTools, duplicate_groups: List[List[str]]):
        """
        Move all duplicate files to the duplicates directory
        
        Args:
            fs: FileSystemTools instance
            duplicate_groups: List of duplicate groups
        """
        duplicates_path = os.path.join(self.target_dir, self.duplicates_dir_name)
        
        # Flatten all duplicate files
        all_duplicates = []
        for group in duplicate_groups:
            all_duplicates.extend(group)
        
        # Move each duplicate file
        for filename in all_duplicates:
            source_path = os.path.join(self.target_dir, filename)
            dest_path = os.path.join(duplicates_path, filename)
            
            success = await fs.move_file(source_path, dest_path)
            if success:
                print(f"  Moved {filename} → {self.duplicates_dir_name}/")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Find and organize duplicate files in a directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find and organize duplicate files (default directory name: 'duplicates')
  python find_duplicates.py /path/to/directory
  
  # Use a custom directory name for duplicates
  python find_duplicates.py /path/to/directory --duplicates-dir backup_duplicates
  
  # The script will:
  # 1. Scan all files in the directory
  # 2. Identify files with identical content
  # 3. Create a directory for duplicates
  # 4. Move all duplicate files to that directory
  # 5. Leave unique files in the original location
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing files to scan for duplicates'
    )
    parser.add_argument(
        '--duplicates-dir',
        type=str,
        default='duplicates',
        help='Name of the directory to store duplicate files (default: duplicates)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create finder and run
    finder = DuplicateFileFinder(
        target_dir=args.target_directory,
        duplicates_dir_name=args.duplicates_dir
    )
    
    try:
        await finder.find_and_organize_duplicates()
    except Exception as e:
        print(f"\nError during duplicate detection: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

