#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge Smallest Files Script (Using utils.py)
=============================================

This script identifies the N smallest .txt files in a directory, sorts them
alphabetically, and merges their content into a single file with proper formatting.

Usage:
    python merge_files.py <target_directory> [--count N] [--output filename]

Example:
    python merge_files.py /path/to/directory --count 10 --output merged_content.txt
"""

import asyncio
import os
import argparse
from typing import List, Tuple

from utils import FileSystemTools


class FileMerger:
    """Merger that combines the smallest files into one"""
    
    def __init__(self, target_dir: str, file_count: int = 10, output_filename: str = "merged_content.txt"):
        """
        Initialize the file merger
        
        Args:
            target_dir: Target directory containing files to merge
            file_count: Number of smallest files to merge (default: 10)
            output_filename: Name of the output merged file (default: merged_content.txt)
        """
        self.target_dir = target_dir
        self.file_count = file_count
        self.output_filename = output_filename
    
    async def merge_smallest_files(self):
        """Main workflow to merge smallest files"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: List all .txt files
            print("Step 1: Listing .txt files...")
            all_files = await fs.list_files()
            txt_files = [f for f in all_files if f.endswith('.txt')]
            print(f"Found {len(txt_files)} .txt files\n")
            
            if not txt_files:
                print("No .txt files found.")
                return
            
            # Step 2: Get file sizes
            print("Step 2: Getting file sizes...")
            file_sizes = await self._get_file_sizes(fs, txt_files)
            print(f"Retrieved size info for {len(file_sizes)} files\n")
            
            # Step 3: Identify smallest N files
            print(f"Step 3: Identifying {self.file_count} smallest files...")
            smallest_files = self._get_smallest_files(file_sizes)
            
            print(f"Smallest {len(smallest_files)} files:")
            for filename, size in smallest_files:
                print(f"  {filename}: {size} bytes")
            print()
            
            # Step 4: Sort alphabetically
            print("Step 4: Sorting files alphabetically...")
            sorted_files = sorted([f[0] for f in smallest_files])
            print(f"Sorted order: {', '.join(sorted_files)}\n")
            
            # Step 5: Read and merge content
            print("Step 5: Reading and merging content...")
            merged_content = await self._merge_files_content(fs, sorted_files)
            
            # Step 6: Write merged file
            print("Step 6: Writing merged file...")
            output_path = os.path.join(self.target_dir, self.output_filename)
            success = await fs.write_file(output_path, merged_content)
            
            if success:
                print(f"  Created: {self.output_filename}")
                print(f"\nTask completed successfully!")
                print(f"Merged {len(sorted_files)} files into {self.output_filename}")
    
    async def _get_file_sizes(self, fs: FileSystemTools, files: List[str]) -> List[Tuple[str, int]]:
        """
        Get file sizes for all files
        
        Args:
            fs: FileSystemTools instance
            files: List of file names
            
        Returns:
            List of (filename, size) tuples
        """
        file_sizes = []
        files_info = await fs.get_files_info_batch(files)
        
        for filename, info in files_info.items():
            if 'size' in info:
                size = info['size']
                file_sizes.append((filename, size))
                print(f"  {filename}: {size} bytes")
        
        return file_sizes
    
    def _get_smallest_files(self, file_sizes: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """
        Get the N smallest files
        
        Args:
            file_sizes: List of (filename, size) tuples
            
        Returns:
            List of N smallest (filename, size) tuples
        """
        # Sort by size (ascending) and take first N
        sorted_by_size = sorted(file_sizes, key=lambda x: x[1])
        return sorted_by_size[:self.file_count]
    
    async def _merge_files_content(self, fs: FileSystemTools, files: List[str]) -> str:
        """
        Read and merge content from files with headers
        
        Args:
            fs: FileSystemTools instance
            files: List of file names (already sorted)
            
        Returns:
            Merged content string
        """
        merged_parts = []
        
        for filename in files:
            file_path = os.path.join(self.target_dir, filename)
            content = await fs.read_text_file(file_path)
            
            if content is not None:
                # Add file header and content
                merged_parts.append(f"File: {filename}")
                merged_parts.append(content)
                merged_parts.append("")  # Blank line between files
                print(f"  Read: {filename}")
        
        # Join all parts, removing the last blank line
        return '\n'.join(merged_parts).rstrip() + '\n'


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Merge the smallest N .txt files in a directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge the 10 smallest .txt files (default)
  python merge_files.py /path/to/directory
  
  # Merge the 5 smallest .txt files
  python merge_files.py /path/to/directory --count 5
  
  # Use a custom output filename
  python merge_files.py /path/to/directory --output combined.txt
  
  # The script will:
  # 1. Find all .txt files in the directory
  # 2. Identify the N smallest files by size
  # 3. Sort them alphabetically
  # 4. Merge their content with file headers
  # 5. Save to the output file
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing files to merge'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of smallest files to merge (default: 10)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='merged_content.txt',
        help='Name of the output merged file (default: merged_content.txt)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate count
    if args.count < 1:
        print(f"Error: Count must be at least 1")
        return
    
    # Create merger and run
    merger = FileMerger(
        target_dir=args.target_directory,
        file_count=args.count,
        output_filename=args.output
    )
    
    try:
        await merger.merge_smallest_files()
    except Exception as e:
        print(f"\nError during file merging: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

