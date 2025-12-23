#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Split File Script (Using utils.py)
===================================

This script splits a large text file into multiple smaller files with equal
character counts.

Usage:
    python split_file.py <target_directory> <input_file> [--parts N] [--output-dir dirname]

Example:
    python split_file.py /path/to/directory large_file.txt --parts 10 --output-dir split
"""

import asyncio
import os
import argparse
from typing import List

from utils import FileSystemTools


class FileSplitter:
    """Splitter that divides a large file into smaller equal-sized files"""
    
    def __init__(self, target_dir: str, input_filename: str, num_parts: int = 10, 
                 output_dir: str = "split"):
        """
        Initialize the file splitter
        
        Args:
            target_dir: Target directory containing the file to split
            input_filename: Name of the input file to split
            num_parts: Number of parts to split into (default: 10)
            output_dir: Name of the output directory for split files (default: split)
        """
        self.target_dir = target_dir
        self.input_filename = input_filename
        self.num_parts = num_parts
        self.output_dir = output_dir
    
    async def split_file(self):
        """Main workflow to split file"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Create output directory
            print(f"Step 1: Creating output directory '{self.output_dir}'...")
            output_path = os.path.join(self.target_dir, self.output_dir)
            success = await fs.create_directory(output_path)
            if success:
                print(f"  Created: {self.output_dir}/\n")
            
            # Step 2: Read the input file
            print(f"Step 2: Reading input file '{self.input_filename}'...")
            input_path = os.path.join(self.target_dir, self.input_filename)
            content = await fs.read_text_file(input_path)
            
            if content is None:
                print(f"Error: Could not read file '{self.input_filename}'")
                return
            
            total_chars = len(content)
            print(f"  File size: {total_chars} characters\n")
            
            # Step 3: Calculate split size
            chars_per_part = total_chars // self.num_parts
            print(f"Step 3: Splitting into {self.num_parts} parts...")
            print(f"  Characters per part: {chars_per_part}\n")
            
            # Step 4: Split and write files
            print("Step 4: Creating split files...")
            await self._split_and_write(fs, content, chars_per_part, output_path)
            
            print(f"\nTask completed successfully!")
            print(f"Split '{self.input_filename}' into {self.num_parts} files in '{self.output_dir}/' directory")
    
    async def _split_and_write(self, fs: FileSystemTools, content: str, 
                               chars_per_part: int, output_path: str):
        """
        Split content and write to files
        
        Args:
            fs: FileSystemTools instance
            content: Content to split
            chars_per_part: Number of characters per part
            output_path: Path to output directory
        """
        total_chars = len(content)
        
        for i in range(self.num_parts):
            # Calculate start and end positions
            start_pos = i * chars_per_part
            
            # For the last part, include all remaining characters
            if i == self.num_parts - 1:
                end_pos = total_chars
            else:
                end_pos = start_pos + chars_per_part
            
            # Extract part content
            part_content = content[start_pos:end_pos]
            
            # Generate filename with zero-padded number
            filename = f"split_{i+1:02d}.txt"
            file_path = os.path.join(output_path, filename)
            
            # Write the file
            success = await fs.write_file(file_path, part_content)
            if success:
                print(f"  Created: {filename} ({len(part_content)} characters)")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Split a large text file into multiple smaller files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Split large_file.txt into 10 equal parts (default)
  python split_file.py /path/to/directory large_file.txt
  
  # Split into 5 parts
  python split_file.py /path/to/directory large_file.txt --parts 5
  
  # Use a custom output directory name
  python split_file.py /path/to/directory large_file.txt --output-dir chunks
  
  # The script will:
  # 1. Create an output directory
  # 2. Read the input file
  # 3. Calculate equal character counts per part
  # 4. Split the content into N files
  # 5. Save files as split_01.txt, split_02.txt, etc.
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing the file to split'
    )
    parser.add_argument(
        'input_file',
        help='Name of the file to split'
    )
    parser.add_argument(
        '--parts',
        type=int,
        default=10,
        help='Number of parts to split into (default: 10)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='split',
        help='Name of the output directory (default: split)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate parts
    if args.parts < 1:
        print(f"Error: Parts must be at least 1")
        return
    
    # Create splitter and run
    splitter = FileSplitter(
        target_dir=args.target_directory,
        input_filename=args.input_file,
        num_parts=args.parts,
        output_dir=args.output_dir
    )
    
    try:
        await splitter.split_file()
    except Exception as e:
        print(f"\nError during file splitting: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

