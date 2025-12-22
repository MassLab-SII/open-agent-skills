#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Individual Comments Analysis Script (Using utils.py)
=====================================================

This script analyzes individual comments made by different parties on specific
clauses across multiple document versions.

Usage:
    python individual_comments.py <target_directory> [--versions v5 v6 v7 v8] [--output filename]

Example:
    python individual_comments.py /path/to/directory --versions v5 v6 v7 v8 --output individual_comment.csv
"""

import asyncio
import os
import argparse
import re
from typing import List, Dict
from collections import defaultdict

from utils import FileSystemTools


class IndividualCommentsAnalyzer:
    """Analyzer that counts individual comments on specific clauses"""
    
    def __init__(self, target_dir: str, versions: List[str], 
                 clauses: List[str], people: List[str],
                 output_filename: str = "individual_comment.csv"):
        """
        Initialize the individual comments analyzer
        
        Args:
            target_dir: Target directory containing legal files
            versions: List of versions to analyze
            clauses: List of clauses to track
            people: List of people to track
            output_filename: Name of the output CSV file
        """
        self.target_dir = target_dir
        self.versions = versions
        self.clauses = clauses
        self.people = people
        self.output_filename = output_filename
        # Structure: {person: {clause: count}}
        self.comment_counts = {person: {clause: 0 for clause in clauses} for person in people}
    
    async def analyze_comments(self):
        """Main workflow to analyze individual comments"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Find legal_files directory
            print("Step 1: Locating legal files...")
            legal_dir = os.path.join(self.target_dir, "legal_files")
            
            # Step 2: Read and analyze specified versions
            print(f"Step 2: Analyzing versions {', '.join(self.versions)}...")
            for version in self.versions:
                await self._analyze_version(fs, legal_dir, version)
            
            print(f"  Analyzed {len(self.versions)} versions\n")
            
            # Step 3: Generate CSV report
            print("Step 3: Generating CSV report...")
            csv_content = self._generate_csv()
            
            # Step 4: Write CSV file
            print("Step 4: Writing CSV file...")
            output_path = os.path.join(self.target_dir, self.output_filename)
            success = await fs.write_file(output_path, csv_content)
            
            if success:
                print(f"  Created: {self.output_filename}")
                print(f"\nTask completed successfully!")
                print(f"Individual comments analysis saved to '{self.output_filename}'")
    
    async def _analyze_version(self, fs: FileSystemTools, legal_dir: str, version: str):
        """
        Analyze a specific version for individual comments
        
        Args:
            fs: FileSystemTools instance
            legal_dir: Path to legal files directory
            version: Version to analyze
        """
        filename = f"Preferred_Stock_Purchase_Agreement_{version}.txt"
        file_path = os.path.join(legal_dir, filename)
        
        content = await fs.read_text_file(file_path)
        if content:
            print(f"  Analyzing: {filename}")
            self._extract_individual_comments(content)
    
    def _extract_individual_comments(self, content: str):
        """
        Extract individual comments from document content
        
        Args:
            content: Document content
        """
        # Pattern to find comments: [name:content]
        comment_pattern = r'\[([^:]+):[^\]]+\]'
        
        # Split content into lines
        lines = content.split('\n')
        current_clause = None
        
        for line in lines:
            # Check if this line starts a new clause
            clause_match = re.match(r'^(\d+\.\d+)', line.strip())
            if clause_match:
                current_clause = clause_match.group(1)
            
            # If we're in a clause we're tracking, count comments
            if current_clause and current_clause in self.clauses:
                comments = re.findall(comment_pattern, line)
                for commenter in comments:
                    commenter = commenter.strip()
                    # Check if this is one of the people we're tracking
                    if commenter in self.people:
                        self.comment_counts[commenter][current_clause] += 1
    
    def _generate_csv(self) -> str:
        """Generate CSV content"""
        lines = []
        
        # Header row: Name, clause1, clause2, ...
        header = ['Name'] + self.clauses
        lines.append(','.join(header))
        
        # Data rows: person, count1, count2, ...
        for person in self.people:
            row = [person]
            for clause in self.clauses:
                count = self.comment_counts[person][clause]
                row.append(str(count))
            lines.append(','.join(row))
        
        return '\n'.join(lines)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze individual comments on specific clauses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze versions v5-v8 with default clauses and people
  python individual_comments.py /path/to/directory
  
  # Analyze custom versions
  python individual_comments.py /path/to/directory --versions v5 v6 v7
  
  # Use a custom output filename
  python individual_comments.py /path/to/directory --output my_comments.csv
  
  # The script will:
  # 1. Read specified versions from legal_files/
  # 2. Extract comments for specific clauses
  # 3. Count comments by each person
  # 4. Generate CSV with person x clause matrix
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing legal files'
    )
    parser.add_argument(
        '--versions',
        nargs='+',
        default=['v5', 'v6', 'v7', 'v8'],
        help='Versions to analyze (default: v5 v6 v7 v8)'
    )
    parser.add_argument(
        '--clauses',
        nargs='+',
        default=['1.1', '1.3', '4.6', '4.16', '6.8', '6.16'],
        help='Clauses to track (default: 1.1 1.3 4.6 4.16 6.8 6.16)'
    )
    parser.add_argument(
        '--people',
        nargs='+',
        default=['Bill Harvey', 'Michelle Jackson', 'David Russel', 'Tony Taylor'],
        help='People to track (default: Bill Harvey, Michelle Jackson, David Russel, Tony Taylor)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='individual_comment.csv',
        help='Name of the output CSV file (default: individual_comment.csv)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create analyzer and run
    analyzer = IndividualCommentsAnalyzer(
        target_dir=args.target_directory,
        versions=args.versions,
        clauses=args.clauses,
        people=args.people,
        output_filename=args.output
    )
    
    try:
        await analyzer.analyze_comments()
    except Exception as e:
        print(f"\nError during individual comments analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

