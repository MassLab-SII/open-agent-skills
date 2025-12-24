#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert to Uppercase Script (Using utils.py)
=============================================

This script converts text files to uppercase and counts words in each file.

Usage:
    python convert_uppercase.py <target_directory> [--files file1.txt file2.txt ...] [--output-dir dirname]

Example:
    python convert_uppercase.py /path/to/directory --files file_01.txt file_02.txt --output-dir uppercase
"""

import asyncio
import os
import argparse
from typing import List, Dict

from utils import FileSystemTools


class UppercaseConverter:
    """Converter that transforms files to uppercase and counts words"""
    
    def __init__(self, target_dir: str, files: List[str], output_dir: str = "uppercase"):
        """
        Initialize the uppercase converter
        
        Args:
            target_dir: Target directory containing files to convert
            files: List of file names to convert
            output_dir: Name of the output directory (default: uppercase)
        """
        self.target_dir = target_dir
        self.files = files
        self.output_dir = output_dir
    
    async def convert_files(self):
        """Main workflow to convert files to uppercase"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Create output directory
            print(f"Step 1: Creating output directory '{self.output_dir}'...")
            output_path = os.path.join(self.target_dir, self.output_dir)
            success = await fs.create_directory(output_path)
            if success:
                print(f"  Created: {self.output_dir}/\n")
            
            # Step 2: Read all files
            print("Step 2: Reading files...")
            file_contents = await self._read_files(fs)
            print(f"Successfully read {len(file_contents)} files\n")
            
            # Step 3: Convert to uppercase and count words
            print("Step 3: Converting to uppercase and counting words...")
            word_counts = {}
            
            for filename, content in file_contents.items():
                # Convert to uppercase
                uppercase_content = content.upper()
                
                # Count words in original content
                word_count = self._count_words(content)
                word_counts[filename] = word_count
                
                # Write uppercase file
                output_file_path = os.path.join(output_path, filename)
                success = await fs.write_file(output_file_path, uppercase_content)
                
                if success:
                    print(f"  Converted: {filename} ({word_count} words)")
            
            print()
            
            # Step 4: Create answer.txt with word counts
            print("Step 4: Creating answer.txt with word counts...")
            await self._write_answer_file(fs, word_counts, output_path)
            
            print(f"\nTask completed successfully!")
            print(f"Converted {len(file_contents)} files to uppercase in '{self.output_dir}/' directory")
    
    async def _read_files(self, fs: FileSystemTools) -> Dict[str, str]:
        """
        Read contents of all files
        
        Args:
            fs: FileSystemTools instance
            
        Returns:
            Dictionary mapping filename to content
        """
        file_contents = {}
        
        for filename in self.files:
            file_path = os.path.join(self.target_dir, filename)
            content = await fs.read_text_file(file_path)
            
            if content is not None:
                file_contents[filename] = content
                print(f"  Read: {filename}")
        
        return file_contents
    
    def _count_words(self, content: str) -> int:
        """
        Count words in content
        
        Args:
            content: Text content
            
        Returns:
            Number of words
        """
        # Split by whitespace and count non-empty strings
        words = content.split()
        return len(words)
    
    async def _write_answer_file(self, fs: FileSystemTools, word_counts: Dict[str, int], 
                                 output_path: str):
        """
        Write answer.txt with word counts
        
        Args:
            fs: FileSystemTools instance
            word_counts: Dictionary mapping filename to word count
            output_path: Path to output directory
        """
        # Format: filename:word_count (one per line)
        # Sort by filename to ensure consistent order
        sorted_files = sorted(word_counts.keys())
        lines = [f"{filename}:{word_counts[filename]}" for filename in sorted_files]
        content = '\n'.join(lines)
        
        answer_path = os.path.join(output_path, "answer.txt")
        success = await fs.write_file(answer_path, content)
        
        if success:
            print(f"  Created: answer.txt")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert text files to uppercase and count words',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert files file_01.txt through file_10.txt
  python convert_uppercase.py /path/to/directory --files file_01.txt file_02.txt file_03.txt file_04.txt file_05.txt file_06.txt file_07.txt file_08.txt file_09.txt file_10.txt
  
  # Use a custom output directory name
  python convert_uppercase.py /path/to/directory --files file_01.txt file_02.txt --output-dir UPPERCASE
  
  # The script will:
  # 1. Create an output directory
  # 2. Read all specified files
  # 3. Convert each file to uppercase
  # 4. Count words in each original file
  # 5. Save uppercase files to the output directory
  # 6. Create answer.txt with word counts in format: filename:count
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing files to convert'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        required=True,
        help='List of files to convert'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='uppercase',
        help='Name of the output directory (default: uppercase)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate files list
    if not args.files:
        print(f"Error: At least one file must be specified")
        return
    
    # Create converter and run
    converter = UppercaseConverter(
        target_dir=args.target_directory,
        files=args.files,
        output_dir=args.output_dir
    )
    
    try:
        await converter.convert_files()
    except Exception as e:
        print(f"\nError during conversion: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

