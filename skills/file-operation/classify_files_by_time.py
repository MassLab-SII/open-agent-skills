#!/usr/bin/env python3
"""
File Time Classification Script (Using tool.py)
================================================

This script classifies files in a directory into subdirectories based on their creation time.
It uses the FileSystemTools wrapper for cleaner code.

Usage:
    python classify_files_by_time.py <target_directory>

Example:
    python classify_files_by_time.py /path/to/directory
"""

import asyncio
import os
import argparse
from typing import List, Dict, Optional
from datetime import datetime

from utils import FileSystemTools


class FileTimeClassifier:
    """Classifier that organizes files by creation time (MM/DD structure)"""
    
    def __init__(self, target_dir: str):
        """
        Initialize the classifier
        
        Args:
            target_dir: Target directory to classify files in
        """
        self.target_dir = target_dir
    
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
            
            # Step 2: Get file creation time information
            print("Step 2: Getting file creation time information...")
            file_times = await self._get_file_times(fs, files)
            print(f"Retrieved time info for {len(file_times)} files\n")
            
            # Step 3: Group files by creation date
            print("Step 3: Grouping files by creation date...")
            grouped_files = self._group_by_date(file_times)
            print(f"Grouped into {len(grouped_files)} date directories\n")
            
            # Step 4: Create date directories and move files
            print("Step 4: Creating directories and moving files...")
            await self._organize_files(fs, grouped_files, file_times)
            
            # Step 5: Create metadata_analyse.txt files
            print("\nStep 5: Creating metadata_analyse.txt files...")
            await self._create_metadata_files(fs, grouped_files, file_times)
            
            print("\nTask completed successfully!")
    
    async def _get_file_times(self, fs: FileSystemTools, files: List[str]) -> Dict[str, Dict]:
        """Get creation time information for all files"""
        file_times = {}
        
        # Get file info in batch
        files_info = await fs.get_files_info_batch(files)
        
        for filename, info in files_info.items():
            if 'created' not in info:
                continue
            
            created_value = info['created']
            dt = None
            
            # Handle both datetime objects and string formats
            if isinstance(created_value, datetime):
                dt = created_value
            elif isinstance(created_value, str):
                # Parse the string format: "Wed Aug 06 2025 12:31:58 GMT+0800 (China Standard Time)"
                dt = self._parse_datetime_string(created_value)
            
            if dt:
                file_times[filename] = {
                    'timestamp': dt.timestamp(),
                    'datetime': dt,
                    'month': f"{dt.month:02d}",
                    'day': f"{dt.day:02d}"
                }
                print(f"  {filename}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return file_times
    
    def _parse_datetime_string(self, date_str: str) -> Optional[datetime]:
        """
        Parse datetime string in format: "Wed Aug 06 2025 12:31:58 GMT+0800 (China Standard Time)"
        
        Args:
            date_str: Datetime string to parse
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Remove timezone info in parentheses
            if '(' in date_str:
                date_str = date_str.split('(')[0].strip()
            
            # Remove GMT offset (e.g., "GMT+0800")
            if 'GMT' in date_str:
                parts = date_str.split('GMT')
                date_str = parts[0].strip()
            
            # Parse the remaining format: "Wed Aug 06 2025 12:31:58"
            dt = datetime.strptime(date_str, '%a %b %d %Y %H:%M:%S')
            return dt
        except Exception as e:
            print(f"  Warning: Failed to parse datetime '{date_str}': {e}")
            return None
    
    def _group_by_date(self, file_times: Dict[str, Dict]) -> Dict[str, List[str]]:
        """Group files by their creation date (MM/DD)"""
        grouped = {}
        
        for filename, time_info in file_times.items():
            month = time_info['month']
            day = time_info['day']
            date_key = f"{month}/{day}"
            
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(filename)
        
        return grouped
    
    async def _organize_files(self, fs: FileSystemTools, grouped_files: Dict[str, List[str]], 
                             file_times: Dict[str, Dict]):
        """Create date directories and move files"""
        for date_path, filenames in grouped_files.items():
            # Create directory structure (MM/DD)
            full_path = os.path.join(self.target_dir, date_path)
            
            success = await fs.create_directory(full_path)
            if success:
                print(f"  Created directory: {date_path}/")
            
            # Move files to the directory
            for filename in filenames:
                source_path = os.path.join(self.target_dir, filename)
                dest_path = os.path.join(full_path, filename)
                
                success = await fs.move_file(source_path, dest_path)
                if success:
                    print(f"  Moved {filename} → {date_path}/")
    
    async def _create_metadata_files(self, fs: FileSystemTools, grouped_files: Dict[str, List[str]], 
                                     file_times: Dict[str, Dict]):
        """Create metadata_analyse.txt in each date directory"""
        for date_path, filenames in grouped_files.items():
            # Sort files by creation time
            sorted_files = sorted(filenames, key=lambda f: file_times[f]['timestamp'])
            
            # Get first and last file info
            first_file = sorted_files[0]
            last_file = sorted_files[-1]
            
            first_dt = file_times[first_file]['datetime']
            last_dt = file_times[last_file]['datetime']
            
            # Format datetime strings (matching the execution.log format)
            first_time_str = self._format_datetime(first_dt)
            last_time_str = self._format_datetime(last_dt)
            
            # Create metadata content (two lines as specified)
            metadata_content = f"{first_file} {first_time_str}\n{last_file} {last_time_str}"
            
            # Write metadata file
            metadata_path = os.path.join(self.target_dir, date_path, "metadata_analyse.txt")
            
            success = await fs.write_file(metadata_path, metadata_content)
            if success:
                print(f"  Created metadata_analyse.txt in {date_path}/")
    
    def _format_datetime(self, dt: datetime) -> str:
        """
        Format datetime in the specified format.
        Example: "Wed Jul 09 2025 23:40:02 GMT+0800 (China Standard Time)"
        """
        weekday = dt.strftime('%a')
        month = dt.strftime('%b')
        day = dt.strftime('%d')
        year = dt.strftime('%Y')
        time = dt.strftime('%H:%M:%S')
        
        # Get timezone offset
        tz_offset = dt.strftime('%z')
        if tz_offset:
            # Format as GMT+0800
            tz_str = f"GMT{tz_offset[:3]}{tz_offset[3:]}"
        else:
            tz_str = "GMT+0800"
        
        return f"{weekday} {month} {day} {year} {time} {tz_str} (China Standard Time)"


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Classify files in a directory by creation time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify files by creation time into MM/DD structure
  python classify_files_by_time.py /path/to/directory
  
  # The script will:
  # 1. Read creation time (ctime) for all files
  # 2. Create MM/DD directory structure
  # 3. Move files to corresponding directories
  # 4. Create metadata_analyse.txt with earliest and latest file info
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing files to classify'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create classifier and run
    classifier = FileTimeClassifier(target_dir=args.target_directory)
    
    try:
        await classifier.classify_files()
    except Exception as e:
        print(f"\nError during classification: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # import os
    # import debugpy
    # debugpy.listen(("localhost", 5678))
    # print("⏳ 等待调试器附加...")
    # debugpy.wait_for_client()
    # print("🚀 调试器已附加！继续执行...")
    asyncio.run(main())
