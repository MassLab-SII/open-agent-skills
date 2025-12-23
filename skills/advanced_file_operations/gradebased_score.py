#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grade-Based Score Calculator
=============================

Calculate student grades from student database basic_info.txt files.
Generates student_grades.csv and grade_summary.txt.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict


def _calculate_grade(score: float) -> str:
    """
    Calculate grade based on score.
    
    A: 90+
    B: 80-89
    C: 70-79
    D: 60-69
    F: <60
    """
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def _is_passing(grade: str) -> bool:
    """Check if grade is passing (A, B, or C)."""
    return grade in ['A', 'B', 'C']


def _read_student_data(directory: str) -> list[dict]:
    """
    Read all student basic_info.txt files and extract scores.
    
    Args:
        directory: Path to student database directory
        
    Returns:
        List of student data dictionaries
    """
    students = []
    
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
        
        # Read basic_info.txt 
        # Note: The address field may contain commas, so we need to parse carefully
        # Format: student_id,name,address,phone,email,toefl,chinese,math,english,father_name,father_profession,mother_name,mother_profession
        # We parse from the end since the last fields are stable
        try:
            with open(basic_info_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                continue
            
            # Parse header
            header = lines[0].strip().split(',')
            
            # Find column indices
            try:
                id_idx = header.index('student_id')
                name_idx = header.index('name')
            except ValueError:
                continue
            
            # Parse data line - handle commas in address by counting from the end
            data_line = lines[1].strip()
            parts = data_line.split(',')
            
            # Count from end: mother_profession=-1, mother_name=-2, father_profession=-3, 
            # father_name=-4, english=-5, math=-6, chinese=-7
            student_id = parts[id_idx]
            name = parts[name_idx]
            chinese_score = float(parts[-7])
            math_score = float(parts[-6])
            english_score = float(parts[-5])
            
            student = {
                'student_id': student_id,
                'name': name,
                'chinese_score': chinese_score,
                'math_score': math_score,
                'english_score': english_score
            }
            
            # Calculate grades
            student['chinese_grade'] = _calculate_grade(student['chinese_score'])
            student['math_grade'] = _calculate_grade(student['math_score'])
            student['english_grade'] = _calculate_grade(student['english_score'])
            
            students.append(student)
        except Exception as e:
            print(f"Warning: Could not process {basic_info_path}: {e}", file=sys.stderr)
    
    return students


def _generate_summary_text(students: list[dict]) -> str:
    """
    Generate grade summary statistics text.
    
    Args:
        students: List of student data dictionaries
        
    Returns:
        Summary text
    """
    # Count grades per subject
    subjects = ['chinese', 'math', 'english']
    grade_counts = {subj: defaultdict(int) for subj in subjects}
    pass_counts = {subj: {'pass': 0, 'fail': 0} for subj in subjects}
    
    for student in students:
        for subj in subjects:
            grade = student[f'{subj}_grade']
            grade_counts[subj][grade] += 1
            
            if _is_passing(grade):
                pass_counts[subj]['pass'] += 1
            else:
                pass_counts[subj]['fail'] += 1
    
    # Build summary text
    lines = []
    lines.append(f"Total students processed: {len(students)}")
    lines.append("")
    
    for subj in subjects:
        lines.append(f"{subj.capitalize()} grades:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            lines.append(f"  {grade}: {grade_counts[subj][grade]}")
        lines.append(f"  Pass (A/B/C): {pass_counts[subj]['pass']}")
        lines.append(f"  Fail (D/F): {pass_counts[subj]['fail']}")
        lines.append("")
    
    return '\n'.join(lines)


def calculate_student_grades(directory: str, output_dir: str = None) -> tuple[list[dict], str]:
    """
    Calculate student grades and generate output files.
    
    Args:
        directory: Path to the student database directory
        output_dir: Output directory for generated files (default: same as input directory)
        
    Returns:
        Tuple of (students list, summary text)
    """
    output_dir = output_dir or directory
    
    # Read student data
    students = _read_student_data(directory)
    
    if not students:
        print("No student data found.", file=sys.stderr)
        return [], ""
    
    # Sort by student_id
    students.sort(key=lambda x: x['student_id'])
    
    # Generate student_grades.csv
    csv_path = os.path.join(output_dir, 'student_grades.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'student_id', 'name', 
            'chinese_score', 'chinese_grade',
            'math_score', 'math_grade',
            'english_score', 'english_grade'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(students)
    
    # Generate summary
    summary_text = _generate_summary_text(students)
    
    # Generate grade_summary.txt
    summary_path = os.path.join(output_dir, 'grade_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)
    
    # Print results for model context
    print(f"Processed {len(students)} students from {directory}")
    print(f"Created: {csv_path}")
    print(f"Created: {summary_path}")
    print("\nGrade Summary:")
    print(summary_text)
    
    return students, summary_text


def main():
    parser = argparse.ArgumentParser(
        description='Calculate student grades from basic_info.txt files.'
    )
    parser.add_argument(
        'directory',
        help='Path to the student database directory'
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help='Output directory for generated files (default: same as input directory)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Calculate grades (function handles everything)
    calculate_student_grades(args.directory, args.output_dir)


if __name__ == '__main__':
    main()
