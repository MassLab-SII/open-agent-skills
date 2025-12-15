#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dispute Review Script (Using utils.py)
=======================================

This script analyzes legal document versions to identify disputed clauses
and count comments on each clause.

Usage:
    python dispute_review.py <target_directory> [--versions v5 v6 v7] [--output filename]

Example:
    python dispute_review.py /path/to/directory --versions v5 v6 v7 --output dispute_review.txt
"""

import asyncio
import os
import argparse
import re
from typing import List, Dict
from collections import defaultdict

from utils import FileSystemTools


class DisputeReviewer:
    """Reviewer that analyzes disputed clauses in legal documents"""
    
    def __init__(self, target_dir: str, versions: List[str], output_filename: str = "dispute_review.txt"):
        """
        Initialize the dispute reviewer
        
        Args:
            target_dir: Target directory containing legal files
            versions: List of versions to analyze (e.g., ['v5', 'v6', 'v7'])
            output_filename: Name of the output file (default: dispute_review.txt)
        """
        self.target_dir = target_dir
        self.versions = versions
        self.output_filename = output_filename
        self.clause_comments = defaultdict(int)
    
    async def review_disputes(self):
        """Main workflow to review disputes"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Find legal_files directory
            print("Step 1: Locating legal files...")
            legal_dir = os.path.join(self.target_dir, "legal_files")
            
            # Step 2: Read specified versions
            print(f"Step 2: Reading versions {', '.join(self.versions)}...")
            for version in self.versions:
                await self._analyze_version(fs, legal_dir, version)
            
            print(f"  Found {len(self.clause_comments)} disputed clauses\n")
            
            # Step 3: Generate report
            print("Step 3: Generating dispute review report...")
            report = self._generate_report()
            
            # Step 4: Write report
            print("Step 4: Writing report...")
            output_path = os.path.join(self.target_dir, self.output_filename)
            success = await fs.write_file(output_path, report)
            
            if success:
                print(f"  Created: {self.output_filename}")
                print(f"\nTask completed successfully!")
                print(f"Dispute review saved to '{self.output_filename}'")
    
    async def _analyze_version(self, fs: FileSystemTools, legal_dir: str, version: str):
        """
        Analyze a specific version for comments
        
        Args:
            fs: FileSystemTools instance
            legal_dir: Path to legal files directory
            version: Version to analyze (e.g., 'v5')
        """
        filename = f"Preferred_Stock_Purchase_Agreement_{version}.txt"
        file_path = os.path.join(legal_dir, filename)
        
        content = await fs.read_text_file(file_path)
        if content:
            print(f"  Analyzing: {filename}")
            self._extract_comments(content)
    
    def _extract_comments(self, content: str):
        """
        Extract comments from document content
        
        Args:
            content: Document content
        """
        # Pattern to find comments: [name:content]
        comment_pattern = r'\[([^:]+):[^\]]+\]'
        
        # Split content into lines
        lines = content.split('\n')
        current_clause = None
        
        for line in lines:
            # Check if this line starts a new clause (e.g., "1.1", "4.6")
            clause_match = re.match(r'^(\d+\.\d+)', line.strip())
            if clause_match:
                current_clause = clause_match.group(1)
            
            # Find all comments in this line
            if current_clause:
                comments = re.findall(comment_pattern, line)
                for commenter in comments:
                    commenter = commenter.strip()
                    # Skip "All parties" comments as they don't count toward clause dispute count
                    if commenter.lower() != "all parties":
                        self.clause_comments[current_clause] += 1
    
    def _generate_report(self) -> str:
        """Generate the dispute review report"""
        lines = []
        
        # Sort clauses numerically
        sorted_clauses = sorted(self.clause_comments.keys(), 
                              key=lambda x: tuple(map(int, x.split('.'))))
        
        for clause in sorted_clauses:
            count = self.clause_comments[clause]
            lines.append(f"{clause}:{count}")
        
        return '\n'.join(lines)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze disputed clauses in legal document versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze versions v5, v6, v7 (default)
  python dispute_review.py /path/to/directory
  
  # Analyze custom versions
  python dispute_review.py /path/to/directory --versions v3 v4 v5
  
  # Use a custom output filename
  python dispute_review.py /path/to/directory --output my_review.txt
  
  # The script will:
  # 1. Read specified versions from legal_files/
  # 2. Extract comments in format [name:content]
  # 3. Count comments per clause (excluding "All parties")
  # 4. Generate report with format: clause_number:comment_count
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing legal files'
    )
    parser.add_argument(
        '--versions',
        nargs='+',
        default=['v5', 'v6', 'v7'],
        help='Versions to analyze (default: v5 v6 v7)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='dispute_review.txt',
        help='Name of the output file (default: dispute_review.txt)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create reviewer and run
    reviewer = DisputeReviewer(
        target_dir=args.target_directory,
        versions=args.versions,
        output_filename=args.output
    )
    
    try:
        await reviewer.review_disputes()
    except Exception as e:
        print(f"\nError during dispute review: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

