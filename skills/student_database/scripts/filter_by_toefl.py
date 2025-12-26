#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filter Students by TOEFL Score
==============================

Find students with TOEFL score greater than or equal to a threshold.
Reads from basic_info.txt files in student folders.
"""

import argparse
import os
import sys


def extract_toefl_score(filepath: str) -> int | None:
    """
    Extract TOEFL score from basic_info.txt.
    
    The file format is CSV with header:
    student_id,name,address,phone,email,toefl,chinese,math,english,...
    
    Args:
        filepath: Path to basic_info.txt
        
    Returns:
        TOEFL score as integer, or None if not found
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None
        
        # Parse header to find toefl column index
        header = lines[0].strip().split(',')
        try:
            toefl_idx = header.index('toefl')
        except ValueError:
            return None
        
        # Parse data line - handle commas in address by counting from end
        # toefl is at index 5 from start, or -8 from end (13 columns total)
        data_line = lines[1].strip()
        parts = data_line.split(',')
        
        # Count from end: mother_profession=-1, mother_name=-2, father_profession=-3, 
        # father_name=-4, english=-5, math=-6, chinese=-7, toefl=-8
        toefl_score = int(parts[-8])
        return toefl_score
        
    except Exception:
        return None


def find_students_by_toefl(directory: str, min_score: int) -> list[str]:
    """
    Find all student folders with TOEFL score >= min_score.
    
    Args:
        directory: Path to student database directory
        min_score: Minimum TOEFL score threshold
        
    Returns:
        List of folder names that match the criteria
    """
    matching_folders = []
    
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
        
        toefl_score = extract_toefl_score(basic_info_path)
        if toefl_score is not None and toefl_score >= min_score:
            matching_folders.append(item)
    
    result = sorted(matching_folders)
    
    # Print results for model context
    print(f"Found {len(result)} students with TOEFL >= {min_score}:")
    for folder in result:
        print(folder)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Find students with TOEFL score >= threshold.'
    )
    parser.add_argument(
        'directory',
        help='Path to the student database directory'
    )
    parser.add_argument(
        'min_score',
        type=int,
        help='Minimum TOEFL score threshold (e.g., 100)'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path if relative
    directory = os.path.abspath(args.directory)
    
    # Validate directory exists
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Validate score
    if args.min_score < 0 or args.min_score > 120:
        print(f"Error: Invalid TOEFL score '{args.min_score}'. Must be between 0 and 120", file=sys.stderr)
        sys.exit(1)
    
    # Find matching students (function already prints results)
    matching_folders = find_students_by_toefl(directory, args.min_score)


if __name__ == '__main__':
    main()
