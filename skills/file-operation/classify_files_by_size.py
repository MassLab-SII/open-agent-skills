#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Size Classification Script (Using tool.py)
================================================

This script classifies files in a directory into subdirectories based on their file sizes.
It uses the FileSystemTools wrapper for cleaner code.

Usage:
    python classify_files_by_size_v2.py <target_directory> [--small <bytes>] [--large <bytes>] 
                                        [--small-category <name>] [--medium-category <name>] [--large-category <name>]

Example:
    python classify_files_by_size_v2.py /path/to/directory --small 300 --large 700
"""

import asyncio
import os
import argparse
from typing import List, Dict

from utils import FileSystemTools


class FileSizeClassifier:
    """Classifier that organizes files by size thresholds"""
    
    def __init__(self, target_dir: str, small_threshold: int = 300, large_threshold: int = 700,
                 small_category: str = 'small_files', medium_category: str = 'medium_files', 
                 large_category: str = 'large_files'):
        """
        Initialize the classifier
        
        Args:
            target_dir: Target directory to classify files in
            small_threshold: Maximum size (bytes) for small files (exclusive)
            large_threshold: Minimum size (bytes) for large files (exclusive)
            small_category: Name for small files category directory
            medium_category: Name for medium files category directory
            large_category: Name for large files category directory
        """
        self.target_dir = target_dir
        self.small_threshold = small_threshold
        self.large_threshold = large_threshold
        self.small_category = small_category
        self.medium_category = medium_category
        self.large_category = large_category
        
        # Category definitions
        self.categories = {
            small_category: lambda size: size < small_threshold,
            medium_category: lambda size: small_threshold <= size <= large_threshold,
            large_category: lambda size: size > large_threshold
        }
    
    async def classify_files(self):
        """Main classification workflow"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: List all files in the directory
            print("Step 1: Listing files...")
            files = await fs.list_files()
            print(f"Found {len(files)} files\n")
            
            if not files:
                print("No files to classify.")
                return
            
            # Step 2: Get file size information
            print("Step 2: Getting file size information...")
            file_sizes = await fs.get_files_info_batch(files)
            
            # Extract just the sizes
            file_size_map = {}
            for filename, info in file_sizes.items():
                if 'size' in info:
                    size = info['size']
                    file_size_map[filename] = size
                    print(f"  {filename}: {size:,} bytes")
            
            print(f"Retrieved size info for {len(file_size_map)} files\n")
            
            # Step 3: Create category directories
            print("Step 3: Creating category directories...")
            for category_name in self.categories.keys():
                category_path = os.path.join(self.target_dir, category_name)
                success = await fs.create_directory(category_path)
                if success:
                    print(f"  Created: {category_name}/")
            print()
            
            # Step 4: Classify and move files
            print("Step 4: Classifying and moving files...")
            for filename, size in file_size_map.items():
                category = self._determine_category(size)
                
                source_path = os.path.join(self.target_dir, filename)
                dest_path = os.path.join(self.target_dir, category, filename)
                
                success = await fs.move_file(source_path, dest_path)
                if success:
                    print(f"  Moved {filename} → {category}/")
            
            print("\nTask completed successfully!")
    
    def _determine_category(self, size: int) -> str:
        """Determine which category a file belongs to based on its size"""
        for category_name, condition in self.categories.items():
            if condition(size):
                return category_name
        return self.large_category  # Default fallback


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Classify files in a directory by size',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default thresholds (300 and 700 bytes)
  python classify_files_by_size_v2.py /path/to/directory
  
  # Custom thresholds
  python classify_files_by_size_v2.py /path/to/directory --small 1024 --large 10240
  
  # Custom category names
  python classify_files_by_size_v2.py /path/to/directory --small-category tiny --medium-category normal --large-category huge
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing files to classify'
    )
    parser.add_argument(
        '--small',
        type=int,
        default=300,
        help='Maximum size for small files in bytes (default: 300)'
    )
    parser.add_argument(
        '--large',
        type=int,
        default=700,
        help='Minimum size for large files in bytes (default: 700)'
    )
    parser.add_argument(
        '--small-category',
        type=str,
        default='small_files',
        help='Name for small files category directory (default: small_files)'
    )
    parser.add_argument(
        '--medium-category',
        type=str,
        default='medium_files',
        help='Name for medium files category directory (default: medium_files)'
    )
    parser.add_argument(
        '--large-category',
        type=str,
        default='large_files',
        help='Name for large files category directory (default: large_files)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate thresholds
    if args.small >= args.large:
        print(f"Error: Small threshold ({args.small}) must be less than large threshold ({args.large})")
        return
    
    # Create classifier and run
    classifier = FileSizeClassifier(
        target_dir=args.target_directory,
        small_threshold=args.small,
        large_threshold=args.large,
        small_category=args.small_category,
        medium_category=args.medium_category,
        large_category=args.large_category
    )
    
    try:
        await classifier.classify_files()
    except Exception as e:
        print(f"\nError during classification: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

