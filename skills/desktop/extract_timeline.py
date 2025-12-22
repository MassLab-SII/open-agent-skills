#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Timeline Script (Using utils.py)
=========================================

This script extracts timeline information from files and generates a chronologically
sorted timeline report.

Usage:
    python extract_timeline.py <target_directory> [--year YYYY] [--output filename]

Example:
    python extract_timeline.py /path/to/directory --year 2024 --output timeline.txt
"""

import asyncio
import os
import argparse
import re
from typing import List, Tuple, Set
from datetime import datetime

from utils import FileSystemTools


class TimelineExtractor:
    """Extractor that generates chronological timelines from file contents"""
    
    def __init__(self, target_dir: str, year: int = 2024, output_filename: str = "timeline.txt"):
        """
        Initialize the timeline extractor
        
        Args:
            target_dir: Target directory to scan
            year: Year to extract timeline for (default: 2024)
            output_filename: Name of the output file (default: timeline.txt)
        """
        self.target_dir = target_dir
        self.year = year
        self.output_filename = output_filename
        self.timeline_entries = []
    
    async def extract_timeline(self):
        """Main workflow to extract timeline"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Scan all files
            print(f"Step 1: Scanning files for {self.year} timeline...")
            await self._scan_files(fs, self.target_dir, "")
            print(f"  Found {len(self.timeline_entries)} timeline entries\n")
            
            # Step 2: Sort by date
            print("Step 2: Sorting entries chronologically...")
            self.timeline_entries.sort(key=lambda x: x[1])
            
            # Step 3: Generate timeline file
            print("Step 3: Generating timeline file...")
            timeline_content = self._generate_timeline_content()
            
            # Step 4: Write timeline file
            print("Step 4: Writing timeline file...")
            output_path = os.path.join(self.target_dir, self.output_filename)
            success = await fs.write_file(output_path, timeline_content)
            
            if success:
                print(f"  Created: {self.output_filename}")
                print(f"\nTask completed successfully!")
                print(f"Timeline saved to '{self.output_filename}'")
    
    async def _scan_files(self, fs: FileSystemTools, current_path: str, rel_path: str):
        """
        Recursively scan files for timeline information
        
        Args:
            fs: FileSystemTools instance
            current_path: Current absolute path
            rel_path: Relative path from target directory
        """
        try:
            files, dirs = await fs.list_directory(current_path)
            
            # Process files
            for filename in files:
                if filename == '.DS_Store':
                    continue
                
                file_path = os.path.join(current_path, filename)
                file_rel_path = os.path.join(rel_path, filename) if rel_path else filename
                
                # Read file content
                content = await fs.read_text_file(file_path)
                if content:
                    self._extract_dates_from_content(content, file_rel_path)
            
            # Recursively process subdirectories
            for dir_name in dirs:
                sub_path = os.path.join(current_path, dir_name)
                sub_rel_path = os.path.join(rel_path, dir_name) if rel_path else dir_name
                await self._scan_files(fs, sub_path, sub_rel_path)
                
        except Exception as e:
            print(f"  Warning: Could not scan {rel_path}: {e}")
    
    def _extract_dates_from_content(self, content: str, file_path: str):
        """
        Extract dates from file content
        
        Args:
            content: File content
            file_path: Relative file path
        """
        # Track dates already found in this file to avoid duplicates
        found_dates = set()
        
        # Pattern 1: YYYY-MM-DD format
        pattern1 = rf'{self.year}-(\d{{2}})-(\d{{2}})'
        matches1 = re.finditer(pattern1, content)
        for match in matches1:
            month = int(match.group(1))
            day = int(match.group(2))
            date_str = f"{self.year}-{month:02d}-{day:02d}"
            
            if date_str not in found_dates:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    self.timeline_entries.append((file_path, date_obj, date_str))
                    found_dates.add(date_str)
                except ValueError:
                    pass
        
        # Pattern 2: Month name format (e.g., "January 2024", "Feb 2024")
        month_names = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        for month_name, month_num in month_names.items():
            # Pattern: "Month YYYY" or "Month, YYYY"
            pattern = rf'\b{month_name}[,\s]+{self.year}\b'
            if re.search(pattern, content, re.IGNORECASE):
                date_str = f"{self.year}-{month_num:02d}-01"
                if date_str not in found_dates:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    self.timeline_entries.append((file_path, date_obj, date_str))
                    found_dates.add(date_str)
        
        # Pattern 3: MM/DD/YYYY format
        pattern3 = rf'(\d{{1,2}})/(\d{{1,2}})/({self.year})'
        matches3 = re.finditer(pattern3, content)
        for match in matches3:
            month = int(match.group(1))
            day = int(match.group(2))
            date_str = f"{self.year}-{month:02d}-{day:02d}"
            
            if date_str not in found_dates and 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    self.timeline_entries.append((file_path, date_obj, date_str))
                    found_dates.add(date_str)
                except ValueError:
                    pass
    
    def _generate_timeline_content(self) -> str:
        """Generate timeline file content"""
        lines = []
        
        for file_path, date_obj, date_str in self.timeline_entries:
            lines.append(f"{file_path}:{date_str}")
        
        return '\n'.join(lines)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Extract timeline information from files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract 2024 timeline (default)
  python extract_timeline.py /path/to/directory
  
  # Extract timeline for a specific year
  python extract_timeline.py /path/to/directory --year 2023
  
  # Use a custom output filename
  python extract_timeline.py /path/to/directory --output my_timeline.txt
  
  # The script will:
  # 1. Scan all files recursively
  # 2. Extract date information for the specified year
  # 3. Sort entries chronologically
  # 4. Generate timeline.txt with format: file_path:YYYY-MM-DD
  
  # Rules:
  # - If only month is shown, use the 1st day of that month
  # - If only year is shown, skip it
  # - If multiple tasks on same date in same file, count only once
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory to scan for timeline information'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2024,
        help='Year to extract timeline for (default: 2024)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='timeline.txt',
        help='Name of the output file (default: timeline.txt)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate year
    if args.year < 1900 or args.year > 2100:
        print(f"Error: Year must be between 1900 and 2100")
        return
    
    # Create extractor and run
    extractor = TimelineExtractor(
        target_dir=args.target_directory,
        year=args.year,
        output_filename=args.output
    )
    
    try:
        await extractor.extract_timeline()
    except Exception as e:
        print(f"\nError during timeline extraction: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

