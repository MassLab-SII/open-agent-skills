#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solution Tracing Script (Using utils.py)
=========================================

This script traces the origin of final solutions in legal documents by analyzing
comments across versions to identify who first proposed ideas.

Usage:
    python solution_tracing.py <target_directory> [--versions v5 v6 v7 v8 v9] [--output filename]

Example:
    python solution_tracing.py /path/to/directory --versions v5 v6 v7 v8 v9 --output tracing.csv
"""

import asyncio
import os
import argparse
import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from utils import FileSystemTools


class SolutionTracer:
    """Tracer that identifies originators of final solutions"""
    
    def __init__(self, target_dir: str, versions: List[str], 
                 clauses: List[str], output_filename: str = "tracing.csv"):
        """
        Initialize the solution tracer
        
        Args:
            target_dir: Target directory containing legal files
            versions: List of versions to analyze
            clauses: List of clauses to track
            output_filename: Name of the output CSV file
        """
        self.target_dir = target_dir
        self.versions = versions
        self.clauses = clauses
        self.output_filename = output_filename
        # Structure: {clause: [(version, person, comment_text), ...]}
        self.clause_history = {clause: [] for clause in clauses}
        # Final results: {clause: (version_number, person)}
        self.solution_origins = {}
    
    async def trace_solutions(self):
        """Main workflow to trace solution origins"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Find legal_files directory
            print("Step 1: Locating legal files...")
            legal_dir = os.path.join(self.target_dir, "legal_files")
            
            # Step 2: Read all versions and collect comment history
            print(f"Step 2: Analyzing versions {', '.join(self.versions)}...")
            for version in self.versions:
                await self._analyze_version(fs, legal_dir, version)
            
            print(f"  Collected comment history for {len(self.clauses)} clauses\n")
            
            # Step 3: Identify solution origins
            print("Step 3: Identifying solution origins...")
            self._identify_solution_origins()
            
            # Step 4: Generate CSV report
            print("Step 4: Generating CSV report...")
            csv_content = self._generate_csv()
            
            # Step 5: Write CSV file
            print("Step 5: Writing CSV file...")
            output_path = os.path.join(self.target_dir, self.output_filename)
            success = await fs.write_file(output_path, csv_content)
            
            if success:
                print(f"  Created: {self.output_filename}")
                print(f"\nTask completed successfully!")
                print(f"Solution tracing saved to '{self.output_filename}'")
    
    async def _analyze_version(self, fs: FileSystemTools, legal_dir: str, version: str):
        """
        Analyze a specific version for comments
        
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
            self._extract_comments_with_context(content, version)
    
    def _extract_comments_with_context(self, content: str, version: str):
        """
        Extract comments with full context
        
        Args:
            content: Document content
            version: Version being analyzed
        """
        # Pattern to find comments: [name:content]
        comment_pattern = r'\[([^:]+):([^\]]+)\]'
        
        # Split content into lines
        lines = content.split('\n')
        current_clause = None
        
        for line in lines:
            # Check if this line starts a new clause
            clause_match = re.match(r'^(\d+\.\d+)', line.strip())
            if clause_match:
                current_clause = clause_match.group(1)
            
            # If we're in a clause we're tracking, collect comments
            if current_clause and current_clause in self.clauses:
                comments = re.findall(comment_pattern, line)
                for commenter, comment_text in comments:
                    commenter = commenter.strip()
                    comment_text = comment_text.strip()
                    # Skip "All parties" comments
                    if commenter.lower() != "all parties":
                        self.clause_history[current_clause].append(
                            (version, commenter, comment_text)
                        )
    
    def _identify_solution_origins(self):
        """
        Identify who first proposed the solution for each clause
        
        This is a simplified heuristic that identifies the first person
        to comment on each clause as the solution originator.
        """
        for clause in self.clauses:
            history = self.clause_history[clause]
            
            if history:
                # Sort by version to get chronological order
                history.sort(key=lambda x: self._version_to_number(x[0]))
                
                # The first comment is considered the solution originator
                first_version, first_person, _ = history[0]
                version_number = self._version_to_number(first_version)
                
                self.solution_origins[clause] = (version_number, first_person)
                print(f"  {clause}: v{version_number} by {first_person}")
            else:
                # No comments found, use placeholder
                self.solution_origins[clause] = (0, "Unknown")
    
    def _version_to_number(self, version: str) -> int:
        """Convert version string (e.g., 'v5') to number (e.g., 5)"""
        return int(version.replace('v', ''))
    
    def _generate_csv(self) -> str:
        """Generate CSV content"""
        lines = []
        
        # Header row: empty, clause1, clause2, ...
        header = [''] + self.clauses
        lines.append(','.join(header))
        
        # Version number row
        version_row = ['version_number']
        for clause in self.clauses:
            version_num, _ = self.solution_origins.get(clause, (0, "Unknown"))
            version_row.append(str(version_num))
        lines.append(','.join(version_row))
        
        # Name row
        name_row = ['name']
        for clause in self.clauses:
            _, person = self.solution_origins.get(clause, (0, "Unknown"))
            name_row.append(person)
        lines.append(','.join(name_row))
        
        return '\n'.join(lines)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Trace the origin of final solutions in legal documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trace solutions in versions v5-v9 with default clauses
  python solution_tracing.py /path/to/directory
  
  # Trace solutions in custom versions
  python solution_tracing.py /path/to/directory --versions v5 v6 v7
  
  # Use a custom output filename
  python solution_tracing.py /path/to/directory --output my_tracing.csv
  
  # The script will:
  # 1. Read specified versions from legal_files/
  # 2. Collect comment history for each clause
  # 3. Identify who first proposed the solution
  # 4. Generate CSV with version numbers and originators
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing legal files'
    )
    parser.add_argument(
        '--versions',
        nargs='+',
        default=['v5', 'v6', 'v7', 'v8', 'v9'],
        help='Versions to analyze (default: v5 v6 v7 v8 v9)'
    )
    parser.add_argument(
        '--clauses',
        nargs='+',
        default=['4.6', '4.16', '6.8', '6.16'],
        help='Clauses to track (default: 4.6 4.16 6.8 6.16)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='tracing.csv',
        help='Name of the output CSV file (default: tracing.csv)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create tracer and run
    tracer = SolutionTracer(
        target_dir=args.target_directory,
        versions=args.versions,
        clauses=args.clauses,
        output_filename=args.output
    )
    
    try:
        await tracer.trace_solutions()
    except Exception as e:
        print(f"\nError during solution tracing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

