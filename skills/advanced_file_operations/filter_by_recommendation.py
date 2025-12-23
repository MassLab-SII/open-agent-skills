#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filter Students by Recommendation Grade
========================================

Find students with specified grade (S or A) from recommendation_letter.txt files.
Supports two patterns:
- Pattern 1: "overall performance as X grade level"
- Pattern 2: "overall academic performance as X grade level"
"""

import argparse
import os
import re
import sys


def extract_grade_from_recommendation(filepath: str) -> str | None:
    """
    Extract grade from recommendation_letter.txt.
    
    Args:
        filepath: Path to recommendation_letter.txt
        
    Returns:
        Grade letter (A, B, C, S, etc.) or None if not found
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try both patterns
        # Pattern 1: overall performance as X grade level
        # Pattern 2: overall academic performance as X grade level
        patterns = [
            r"overall performance as ([A-Z]) grade level",
            r"overall academic performance as ([A-Z]) grade level"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    except Exception:
        return None


def find_students_by_grade(directory: str, target_grades: str | list[str]) -> list[str]:
    """
    Find all student folders with specified grade(s).
    
    Args:
        directory: Path to student database directory
        target_grades: Target grade(s) to filter. Can be:
            - A single grade string (e.g., 'S', 'A')
            - Multiple grades as string (e.g., 'SA' for S or A)
            - A list of grades (e.g., ['S', 'A'])
        
    Returns:
        List of folder names that match the grade(s)
    """
    # Normalize target_grades to a set
    if isinstance(target_grades, str):
        grades_set = set(target_grades.upper())
    else:
        grades_set = set(g.upper() for g in target_grades)
    
    matching_folders = []
    
    for item in os.listdir(directory):
        student_dir = os.path.join(directory, item)
        if not os.path.isdir(student_dir):
            continue
        
        # Skip hidden directories
        if item.startswith('.'):
            continue
        
        recommendation_path = os.path.join(student_dir, 'recommendation_letter.txt')
        if not os.path.exists(recommendation_path):
            continue
        
        grade = extract_grade_from_recommendation(recommendation_path)
        if grade in grades_set:
            matching_folders.append(item)
    
    result = sorted(matching_folders)
    
    # Print results for model context
    grades_str = ','.join(sorted(grades_set))
    print(f"Found {len(result)} students with grade(s) {grades_str}:")
    for folder in result:
        print(folder)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Find students with specified grade(s) from recommendation letters.'
    )
    parser.add_argument(
        'directory',
        help='Path to the student database directory'
    )
    parser.add_argument(
        'grades',
        help='Target grade(s) to filter (e.g., S, A, SA for both S and A)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Validate grades
    target_grades = args.grades.upper()
    valid_grades = {'S', 'A', 'B', 'C', 'D', 'F'}
    for g in target_grades:
        if g not in valid_grades:
            print(f"Error: Invalid grade '{g}'. Must be S, A, B, C, D, or F", file=sys.stderr)
            sys.exit(1)
    
    # Find matching students (function already prints results)
    matching_folders = find_students_by_grade(args.directory, target_grades)


if __name__ == '__main__':
    main()
