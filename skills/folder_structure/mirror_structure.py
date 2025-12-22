#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mirror Directory Structure Script (Using utils.py)
===================================================

This script mirrors a directory structure without copying file contents.
It creates placeholder files in empty directories and applies custom rules.

Usage:
    python mirror_structure.py <target_directory> <source_dir> [--output-dir dirname] [--max-files N]

Example:
    python mirror_structure.py /path/to/directory complex_structure --output-dir complex_structure_mirror --max-files 2
"""

import asyncio
import os
import argparse
import re
from typing import List, Tuple, Set

from utils import FileSystemTools


class StructureMirror:
    """Mirror that replicates directory structure with custom rules"""
    
    def __init__(self, target_dir: str, source_dir: str, output_dir: str = None, 
                 max_files: int = 2, append_processed: bool = True):
        """
        Initialize the structure mirror
        
        Args:
            target_dir: Base directory containing the source
            source_dir: Source directory name to mirror
            output_dir: Output directory name (default: source_dir + "_mirror")
            max_files: Maximum files allowed in a directory (default: 2)
            append_processed: Whether to append "_processed" to dirs with numbers (default: True)
        """
        self.target_dir = target_dir
        self.source_dir = source_dir
        self.output_dir = output_dir or f"{source_dir}_mirror"
        self.max_files = max_files
        self.append_processed = append_processed
        self.discarded_dirs = []
    
    async def mirror_structure(self):
        """Main workflow to mirror directory structure"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Analyze source structure
            print(f"Step 1: Analyzing source structure '{self.source_dir}'...")
            source_path = os.path.join(self.target_dir, self.source_dir)
            
            # Get the directory tree
            structure = await self._analyze_structure(fs, source_path, "")
            print(f"  Analyzed directory structure\n")
            
            # Step 2: Create mirror root directory
            print(f"Step 2: Creating mirror directory '{self.output_dir}'...")
            output_path = os.path.join(self.target_dir, self.output_dir)
            success = await fs.create_directory(output_path)
            if success:
                print(f"  Created: {self.output_dir}/\n")
            
            # Step 3: Mirror the structure
            print("Step 3: Mirroring directory structure...")
            await self._mirror_directories(fs, structure, output_path)
            
            # Step 4: Create placeholder files
            print("\nStep 4: Creating placeholder files in empty directories...")
            await self._create_placeholders(fs, output_path)
            
            print(f"\nTask completed successfully!")
            print(f"Mirrored structure from '{self.source_dir}/' to '{self.output_dir}/'")
            
            if self.discarded_dirs:
                print(f"\nDiscarded {len(self.discarded_dirs)} directories (>2 files):")
                for dir_path in self.discarded_dirs:
                    print(f"  - {dir_path}")
    
    async def _analyze_structure(self, fs: FileSystemTools, current_path: str, 
                                 rel_path: str) -> dict:
        """
        Recursively analyze directory structure
        
        Args:
            fs: FileSystemTools instance
            current_path: Current absolute path
            rel_path: Relative path from source root
            
        Returns:
            Dictionary representing the directory structure
        """
        files, dirs = await fs.list_directory(current_path)
        
        # Check if this directory should be discarded (>max_files files)
        if len(files) > self.max_files:
            discard_path = os.path.join(self.source_dir, rel_path) if rel_path else self.source_dir
            self.discarded_dirs.append(discard_path)
            return None  # Discard this directory and its subtree
        
        structure = {
            'path': rel_path,
            'dirs': {},
            'has_files': len(files) > 0
        }
        
        # Recursively process subdirectories
        for dir_name in dirs:
            sub_path = os.path.join(current_path, dir_name)
            sub_rel_path = os.path.join(rel_path, dir_name) if rel_path else dir_name
            
            sub_structure = await self._analyze_structure(fs, sub_path, sub_rel_path)
            
            # Only include if not discarded
            if sub_structure is not None:
                structure['dirs'][dir_name] = sub_structure
        
        return structure
    
    def _transform_dirname(self, dirname: str) -> str:
        """
        Transform directory name according to rules
        
        Args:
            dirname: Original directory name
            
        Returns:
            Transformed directory name
        """
        if self.append_processed and re.search(r'\d', dirname):
            # Directory name contains numbers, append "_processed"
            return f"{dirname}_processed"
        return dirname
    
    async def _mirror_directories(self, fs: FileSystemTools, structure: dict, 
                                  parent_path: str):
        """
        Recursively create mirror directories
        
        Args:
            fs: FileSystemTools instance
            structure: Directory structure dictionary
            parent_path: Parent directory path in mirror
        """
        # Create subdirectories
        for dir_name, sub_structure in structure['dirs'].items():
            # Transform directory name
            mirror_name = self._transform_dirname(dir_name)
            mirror_path = os.path.join(parent_path, mirror_name)
            
            # Create directory
            success = await fs.create_directory(mirror_path)
            if success:
                rel_path = sub_structure['path']
                print(f"  Created: {rel_path} → {mirror_name}/")
            
            # Recursively create subdirectories
            await self._mirror_directories(fs, sub_structure, mirror_path)
    
    async def _create_placeholders(self, fs: FileSystemTools, current_path: str):
        """
        Recursively create placeholder files in empty directories
        
        Args:
            fs: FileSystemTools instance
            current_path: Current directory path
        """
        files, dirs = await fs.list_directory(current_path)
        
        # If directory is empty (no files, no subdirs), create placeholder
        if len(files) == 0 and len(dirs) == 0:
            placeholder_path = os.path.join(current_path, "placeholder.txt")
            # Write the absolute path as content
            success = await fs.write_file(placeholder_path, current_path)
            if success:
                rel_path = os.path.relpath(current_path, os.path.join(self.target_dir, self.output_dir))
                print(f"  Created placeholder: {rel_path}/placeholder.txt")
        
        # Recursively process subdirectories
        for dir_name in dirs:
            sub_path = os.path.join(current_path, dir_name)
            await self._create_placeholders(fs, sub_path)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Mirror directory structure without copying file contents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mirror complex_structure to complex_structure_mirror (default)
  python mirror_structure.py /path/to/directory complex_structure
  
  # Use a custom output directory name
  python mirror_structure.py /path/to/directory complex_structure --output-dir my_mirror
  
  # Allow up to 5 files per directory before discarding
  python mirror_structure.py /path/to/directory complex_structure --max-files 5
  
  # Disable appending "_processed" to directories with numbers
  python mirror_structure.py /path/to/directory complex_structure --no-append-processed
  
  # The script will:
  # 1. Analyze the source directory structure
  # 2. Create a mirror directory structure (no file contents)
  # 3. Discard directories with more than N files
  # 4. Append "_processed" to directory names containing numbers
  # 5. Create placeholder.txt in empty directories with their absolute paths
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Base directory containing the source'
    )
    parser.add_argument(
        'source_dir',
        help='Source directory name to mirror'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory name (default: source_dir + "_mirror")'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        default=2,
        help='Maximum files allowed in a directory before discarding (default: 2)'
    )
    parser.add_argument(
        '--no-append-processed',
        action='store_true',
        help='Do not append "_processed" to directories with numbers'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate source directory exists
    source_path = os.path.join(args.target_directory, args.source_dir)
    if not os.path.isdir(source_path):
        print(f"Error: Source directory '{args.source_dir}' does not exist in '{args.target_directory}'")
        return
    
    # Validate max_files
    if args.max_files < 0:
        print(f"Error: max-files must be non-negative")
        return
    
    # Create mirror and run
    mirror = StructureMirror(
        target_dir=args.target_directory,
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        max_files=args.max_files,
        append_processed=not args.no_append_processed
    )
    
    try:
        await mirror.mirror_structure()
    except Exception as e:
        print(f"\nError during structure mirroring: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

