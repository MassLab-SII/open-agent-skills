#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze Directory Structure Script (Using utils.py)
====================================================

This script recursively analyzes a directory structure and generates a detailed
statistical report including file counts, folder counts, total size, depth analysis,
and file type classification.

Usage:
    python analyze_structure.py <target_directory> [--output filename]

Example:
    python analyze_structure.py /path/to/directory --output structure_analysis.txt
"""

import asyncio
import os
import argparse
from typing import Dict, Tuple, List
from collections import defaultdict

from utils import FileSystemTools


class StructureAnalyzer:
    """Analyzer that generates detailed directory structure statistics"""
    
    def __init__(self, target_dir: str, output_filename: str = "structure_analysis.txt"):
        """
        Initialize the structure analyzer
        
        Args:
            target_dir: Target directory to analyze
            output_filename: Name of the output report file (default: structure_analysis.txt)
        """
        self.target_dir = target_dir
        self.output_filename = output_filename
        
        # Statistics
        self.total_files = 0
        self.total_folders = 0
        self.total_size = 0
        self.deepest_path = ""
        self.max_depth = 0
        self.file_types = defaultdict(int)
    
    async def analyze_structure(self):
        """Main workflow to analyze directory structure"""
        async with FileSystemTools(self.target_dir) as fs:
            print("Step 1: Analyzing directory structure...")
            
            # Recursively analyze the structure
            await self._analyze_recursive(fs, self.target_dir, "", 0)
            
            print(f"  Total files: {self.total_files}")
            print(f"  Total folders: {self.total_folders}")
            print(f"  Total size: {self.total_size} bytes")
            print(f"  Max depth: {self.max_depth}")
            print(f"  Deepest path: {self.deepest_path}")
            print()
            
            # Step 2: Generate report
            print("Step 2: Generating report...")
            report = self._generate_report()
            
            # Step 3: Write report to file
            print("Step 3: Writing report to file...")
            output_path = os.path.join(self.target_dir, self.output_filename)
            success = await fs.write_file(output_path, report)
            
            if success:
                print(f"  Created: {self.output_filename}")
                print(f"\nTask completed successfully!")
                print(f"Analysis report saved to '{self.output_filename}'")
    
    async def _analyze_recursive(self, fs: FileSystemTools, current_path: str, 
                                 rel_path: str, depth: int):
        """
        Recursively analyze directory structure
        
        Args:
            fs: FileSystemTools instance
            current_path: Current absolute path
            rel_path: Relative path from target directory
            depth: Current depth level
        """
        try:
            files, dirs = await fs.list_directory(current_path)
            
            # Filter out .DS_Store from file count (but include in size calculation)
            visible_files = [f for f in files if f != '.DS_Store']
            
            # Count files (excluding .DS_Store)
            self.total_files += len(visible_files)
            
            # Count folders
            self.total_folders += len(dirs)
            
            # Get file sizes and types for all files (including .DS_Store for size)
            for filename in files:
                file_path = os.path.join(current_path, filename)
                file_info = await fs.get_file_info(file_path)
                
                if file_info and 'size' in file_info:
                    self.total_size += file_info['size']
                
                # Only count file types for visible files (excluding .DS_Store)
                if filename != '.DS_Store':
                    # Get file extension
                    if '.' in filename:
                        ext = filename.rsplit('.', 1)[1].lower()
                        self.file_types[ext] += 1
                    else:
                        self.file_types['(no extension)'] += 1
            
            # Update deepest path if this directory has subdirectories or files
            if depth > self.max_depth:
                self.max_depth = depth
                self.deepest_path = rel_path if rel_path else "."
            
            # Recursively process subdirectories
            for dir_name in dirs:
                sub_path = os.path.join(current_path, dir_name)
                sub_rel_path = os.path.join(rel_path, dir_name) if rel_path else dir_name
                
                await self._analyze_recursive(fs, sub_path, sub_rel_path, depth + 1)
                
        except Exception as e:
            print(f"  Warning: Could not analyze {rel_path}: {e}")
    
    def _generate_report(self) -> str:
        """
        Generate the analysis report
        
        Returns:
            Report content as string
        """
        lines = []
        
        # Section 1: File Statistics
        lines.append(f"total number of files: {self.total_files}")
        lines.append(f"total number of folders: {self.total_folders}")
        lines.append(f"total size of all files: {self.total_size}")
        lines.append("")
        
        # Section 2: Depth Analysis
        lines.append(f"depth: {self.max_depth}")
        lines.append(self.deepest_path)
        lines.append("")
        
        # Section 3: File Type Classification
        # Sort by extension name for consistent output
        sorted_types = sorted(self.file_types.items())
        for ext, count in sorted_types:
            lines.append(f"{ext}: {count}")
        
        return '\n'.join(lines)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze directory structure and generate statistical report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze directory structure (default output: structure_analysis.txt)
  python analyze_structure.py /path/to/directory
  
  # Use a custom output filename
  python analyze_structure.py /path/to/directory --output my_analysis.txt
  
  # The script will generate a report with:
  # 1. File Statistics: total files, folders, and size
  # 2. Depth Analysis: deepest path and its depth level
  # 3. File Type Classification: count of files by extension
  
  # Note: .DS_Store files are excluded from file counts and type classification,
  #       but included in total size calculation
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory to analyze'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='structure_analysis.txt',
        help='Name of the output report file (default: structure_analysis.txt)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create analyzer and run
    analyzer = StructureAnalyzer(
        target_dir=args.target_directory,
        output_filename=args.output
    )
    
    try:
        await analyzer.analyze_structure()
    except Exception as e:
        print(f"\nError during structure analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

