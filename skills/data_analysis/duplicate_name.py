#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duplicate Name Finder
=====================

Find duplicate names in student database and generate namesake.txt.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict


def find_duplicate_names(directory: str) -> dict[str, list[str]]: #verified
    """
    Find duplicate names in student database.
    
    Args:
        directory: Path to student database directory
        
    Returns:
        Dictionary mapping names to list of student IDs
    """
    name_to_ids = defaultdict(list)
    
    # List all student folders
    for item in os.listdir(directory):
        student_dir = os.path.join(directory, item)
        if not os.path.isdir(student_dir):
            continue
        
        # Skip hidden directories
        if item.startswith('.'):
            continue
        
        basic_info_path = os.path.join(student_dir, 'basic_info.txt')
        if not os.path.exists(basic_info_path):
            continue
        
        # Read basic_info.txt (CSV format)
        try:
            with open(basic_info_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    student_id = row.get('student_id', '')
                    name = row.get('name', '')
                    if name and student_id:
                        name_to_ids[name].append(student_id)
        except Exception as e:
            print(f"Warning: Could not process {basic_info_path}: {e}", file=sys.stderr)
    
    # Filter to only duplicates (count > 1)
    duplicates = {name: ids for name, ids in name_to_ids.items() if len(ids) > 1}
    
    # Print results for model context
    print(f"Found {len(duplicates)} duplicate name(s):")
    for name in sorted(duplicates.keys()):
        ids = sorted(duplicates[name])
        print(f"  {name}: {', '.join(ids)}")
    
    return duplicates


def main():
    parser = argparse.ArgumentParser(
        description='Find duplicate names in student database.'
    )
    parser.add_argument(
        'directory',
        help='Path to the student database directory'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path (default: namesake.txt in input directory)'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path if relative
    directory = os.path.abspath(args.directory)
    
    # Validate directory exists
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Find duplicates
    duplicates = find_duplicate_names(directory)
    
    if not duplicates:
        print("No duplicate names found.")
        return
    
    # Generate output
    output_path = args.output or os.path.join(directory, 'namesake.txt')
    if args.output:
        output_path = os.path.abspath(args.output)
    
    lines = []
    for name in sorted(duplicates.keys()):
        ids = sorted(duplicates[name])
        lines.append(f"name: {name}")
        lines.append(f"count: {len(ids)}")
        lines.append(f"ids: {', '.join(ids)}")
        lines.append("")  # Empty line between groups
    
    # Remove trailing empty line
    if lines and lines[-1] == "":
        lines.pop()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Created: {output_path}")
    print(f"Found {len(duplicates)} duplicate name(s).")


if __name__ == '__main__':
    main()
