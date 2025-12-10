#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pattern Matching Script (Using utils.py)
=========================================

This script finds all files that contain a substring of N or more characters
that also appears in a reference file.

Usage:
    python pattern_matching.py <target_directory> <reference_file> [--min-length N] [--output filename]

Example:
    python pattern_matching.py /path/to/directory large_file.txt --min-length 30 --output answer.txt
"""

import asyncio
import os
import argparse
from typing import List, Tuple, Optional

from utils import FileSystemTools


class PatternMatcher:
    """Matcher that finds files containing substrings from a reference file"""
    
    def __init__(self, target_dir: str, reference_file: str, min_length: int = 30,
                 output_filename: str = "answer.txt"):
        """
        Initialize the pattern matcher
        
        Args:
            target_dir: Target directory containing files to search
            reference_file: Reference file to extract patterns from
            min_length: Minimum substring length to match (default: 30)
            output_filename: Name of the output file (default: answer.txt)
        """
        self.target_dir = target_dir
        self.reference_file = reference_file
        self.min_length = min_length
        self.output_filename = output_filename
    
    async def find_pattern_matches(self):
        """Main workflow to find pattern matches"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Read reference file
            print(f"Step 1: Reading reference file '{self.reference_file}'...")
            ref_path = os.path.join(self.target_dir, self.reference_file)
            ref_content = await fs.read_text_file(ref_path)
            
            if ref_content is None:
                print(f"Error: Could not read reference file '{self.reference_file}'")
                return
            
            print(f"  Reference file size: {len(ref_content)} characters\n")
            
            # Step 2: List all files to check
            print("Step 2: Listing files to check...")
            all_files = await fs.list_files()
            
            # Filter out the reference file and non-txt files
            files_to_check = [f for f in all_files 
                            if f.endswith('.txt') and f != self.reference_file 
                            and f != self.output_filename]
            
            print(f"Found {len(files_to_check)} files to check\n")
            
            # Step 3: Read all files
            print("Step 3: Reading files...")
            file_contents = await self._read_files(fs, files_to_check)
            print(f"Successfully read {len(file_contents)} files\n")
            
            # Step 4: Find matches
            print(f"Step 4: Finding matches (min length: {self.min_length} characters)...")
            matches = self._find_matches(ref_content, file_contents)
            
            if matches:
                print(f"Found {len(matches)} matching file(s):")
                for filename, position in matches:
                    print(f"  {filename}: position {position}")
            else:
                print("No matches found.")
            print()
            
            # Step 5: Write results
            print("Step 5: Writing results...")
            await self._write_results(fs, matches)
            
            print(f"\nTask completed successfully!")
            print(f"Results saved to '{self.output_filename}'")
    
    async def _read_files(self, fs: FileSystemTools, files: List[str]) -> dict:
        """
        Read contents of all files
        
        Args:
            fs: FileSystemTools instance
            files: List of file names
            
        Returns:
            Dictionary mapping filename to content
        """
        file_contents = {}
        
        for filename in files:
            file_path = os.path.join(self.target_dir, filename)
            content = await fs.read_text_file(file_path)
            if content is not None:
                file_contents[filename] = content
                print(f"  Read: {filename}")
        
        return file_contents
    
    def _find_matches(self, ref_content: str, file_contents: dict) -> List[Tuple[str, int]]:
        """
        Find files that contain substrings from reference content
        
        Args:
            ref_content: Reference file content
            file_contents: Dictionary mapping filename to content
            
        Returns:
            List of (filename, position) tuples for matching files
        """
        matches = []
        
        for filename, content in file_contents.items():
            # Try to find a matching substring
            match_pos = self._find_longest_match(ref_content, content)
            
            if match_pos is not None:
                matches.append((filename, match_pos))
        
        # Sort by filename for consistent output
        matches.sort(key=lambda x: x[0])
        
        return matches
    
    def _find_longest_match(self, ref_content: str, file_content: str) -> Optional[int]:
        """
        Find the position of the longest matching substring in reference content
        
        Args:
            ref_content: Reference file content
            file_content: File content to search for matches
            
        Returns:
            1-indexed position in reference content, or None if no match
        """
        # Try to find substrings of min_length or longer
        best_match_pos = None
        best_match_len = 0
        
        # Iterate through all possible substrings in file_content
        for i in range(len(file_content) - self.min_length + 1):
            # Start with min_length and try to extend
            for length in range(self.min_length, len(file_content) - i + 1):
                substring = file_content[i:i + length]
                
                # Check if this substring exists in reference content
                pos = ref_content.find(substring)
                
                if pos != -1:
                    # Found a match, try to extend it
                    if length > best_match_len:
                        best_match_len = length
                        best_match_pos = pos + 1  # Convert to 1-indexed
                else:
                    # Can't extend further from this starting position
                    break
        
        return best_match_pos if best_match_len >= self.min_length else None
    
    async def _write_results(self, fs: FileSystemTools, matches: List[Tuple[str, int]]):
        """
        Write results to output file
        
        Args:
            fs: FileSystemTools instance
            matches: List of (filename, position) tuples
        """
        # Format: filename,position (one per line)
        lines = [f"{filename},{position}" for filename, position in matches]
        content = '\n'.join(lines)
        
        output_path = os.path.join(self.target_dir, self.output_filename)
        success = await fs.write_file(output_path, content)
        
        if success:
            print(f"  Created: {self.output_filename}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Find files containing substrings from a reference file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find files with 30+ character matches (default)
  python pattern_matching.py /path/to/directory large_file.txt
  
  # Use a custom minimum length
  python pattern_matching.py /path/to/directory large_file.txt --min-length 50
  
  # Use a custom output filename
  python pattern_matching.py /path/to/directory large_file.txt --output results.txt
  
  # The script will:
  # 1. Read the reference file
  # 2. Read all other .txt files in the directory
  # 3. Find files containing substrings (min N characters) from the reference
  # 4. Write results to output file in format: filename,position
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing files to search'
    )
    parser.add_argument(
        'reference_file',
        default='large_file.txt',
        help='Reference file to extract patterns from'
    )
    parser.add_argument(
        '--min-length',
        type=int,
        default=30,
        help='Minimum substring length to match (default: 30)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='answer.txt',
        help='Name of the output file (default: answer.txt)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate min_length
    if args.min_length < 1:
        print(f"Error: Minimum length must be at least 1")
        return
    
    # Create matcher and run
    matcher = PatternMatcher(
        target_dir=args.target_directory,
        reference_file=args.reference_file,
        min_length=args.min_length,
        output_filename=args.output
    )
    
    try:
        await matcher.find_pattern_matches()
    except Exception as e:
        print(f"\nError during pattern matching: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

