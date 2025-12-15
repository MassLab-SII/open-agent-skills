#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Organize Projects Script (Using utils.py)
==========================================

This script organizes project files into a structured directory hierarchy
based on file types and content categories.

Usage:
    python organize_projects.py <target_directory> [--output-dir dirname]

Example:
    python organize_projects.py /path/to/directory --output-dir organized_projects
"""

import asyncio
import os
import argparse
from typing import List, Dict

from utils import FileSystemTools


class ProjectOrganizer:
    """Organizer that structures project files into categories"""
    
    def __init__(self, target_dir: str, output_dir: str = "organized_projects"):
        """
        Initialize the project organizer
        
        Args:
            target_dir: Target directory to organize
            output_dir: Output directory name (default: organized_projects)
        """
        self.target_dir = target_dir
        self.output_dir = output_dir
        self.file_mapping = {
            'py_files': [],
            'csv_files': [],
            'md_files': []
        }
    
    async def organize(self):
        """Main workflow to organize projects"""
        async with FileSystemTools(self.target_dir) as fs:
            # Step 1: Create directory structure
            print("Step 1: Creating directory structure...")
            await self._create_directory_structure(fs)
            print()
            
            # Step 2: Scan and categorize files
            print("Step 2: Scanning and categorizing files...")
            await self._scan_files(fs)
            print(f"  Found {len(self.file_mapping['py_files'])} Python files")
            print(f"  Found {len(self.file_mapping['csv_files'])} CSV files")
            print(f"  Found {len(self.file_mapping['md_files'])} Markdown files")
            print()
            
            # Step 3: Move files to appropriate locations
            print("Step 3: Moving files...")
            await self._move_files(fs)
            print()
            
            # Step 4: Generate documentation
            print("Step 4: Generating project structure documentation...")
            await self._generate_documentation(fs)
            
            print(f"\nTask completed successfully!")
            print(f"Projects organized in '{self.output_dir}/' directory")
    
    async def _create_directory_structure(self, fs: FileSystemTools):
        """Create the organized directory structure"""
        base_path = os.path.join(self.target_dir, self.output_dir)
        
        directories = [
            base_path,
            os.path.join(base_path, "experiments"),
            os.path.join(base_path, "experiments", "ml_projects"),
            os.path.join(base_path, "experiments", "data_analysis"),
            os.path.join(base_path, "learning"),
            os.path.join(base_path, "learning", "progress_tracking"),
            os.path.join(base_path, "learning", "resources"),
            os.path.join(base_path, "personal"),
            os.path.join(base_path, "personal", "entertainment"),
            os.path.join(base_path, "personal", "collections")
        ]
        
        for dir_path in directories:
            success = await fs.create_directory(dir_path)
            if success:
                rel_path = os.path.relpath(dir_path, self.target_dir)
                print(f"  Created: {rel_path}/")
    
    async def _scan_files(self, fs: FileSystemTools):
        """Scan directory for files to organize"""
        # Search for Python files
        py_files = await fs.search_files("**/*.py")
        self.file_mapping['py_files'] = [f for f in py_files if self.output_dir not in f]
        
        # Search for CSV files
        csv_files = await fs.search_files("**/*.csv")
        self.file_mapping['csv_files'] = [f for f in csv_files if self.output_dir not in f]
        
        # Search for Markdown files
        md_files = await fs.search_files("**/*.md")
        self.file_mapping['md_files'] = [f for f in md_files if self.output_dir not in f]
    
    async def _move_files(self, fs: FileSystemTools):
        """Move files to their appropriate locations"""
        base_path = os.path.join(self.target_dir, self.output_dir)
        
        # Move Python files to experiments/ml_projects/
        ml_projects_path = os.path.join(base_path, "experiments", "ml_projects")
        for file_path in self.file_mapping['py_files']:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(ml_projects_path, filename)
            success = await fs.move_file(file_path, dest_path)
            if success:
                print(f"  Moved: {filename} → experiments/ml_projects/")
        
        # Move CSV files to experiments/data_analysis/
        data_analysis_path = os.path.join(base_path, "experiments", "data_analysis")
        for file_path in self.file_mapping['csv_files']:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(data_analysis_path, filename)
            success = await fs.move_file(file_path, dest_path)
            if success:
                print(f"  Moved: {filename} → experiments/data_analysis/")
        
        # Categorize and move Markdown files
        await self._categorize_markdown_files(fs, base_path)
    
    async def _categorize_markdown_files(self, fs: FileSystemTools, base_path: str):
        """Categorize and move Markdown files based on content"""
        learning_keywords = ['learning', 'study', 'research', 'experiment', 'analysis', 'README']
        entertainment_keywords = ['game', 'gaming', 'entertainment', 'travel', 'play']
        collection_keywords = ['music', 'collection']
        
        for file_path in self.file_mapping['md_files']:
            filename = os.path.basename(file_path)
            file_lower = filename.lower()
            
            # Read file content to better categorize
            content = await fs.read_text_file(file_path)
            content_lower = content.lower() if content else ""
            
            # Determine category
            if any(keyword in file_lower or keyword in content_lower for keyword in learning_keywords):
                dest_dir = os.path.join(base_path, "learning", "resources")
                category = "learning/resources"
            elif any(keyword in file_lower or keyword in content_lower for keyword in entertainment_keywords):
                dest_dir = os.path.join(base_path, "personal", "entertainment")
                category = "personal/entertainment"
            elif any(keyword in file_lower or keyword in content_lower for keyword in collection_keywords):
                dest_dir = os.path.join(base_path, "personal", "collections")
                category = "personal/collections"
            else:
                # Default to learning resources
                dest_dir = os.path.join(base_path, "learning", "resources")
                category = "learning/resources"
            
            dest_path = os.path.join(dest_dir, filename)
            success = await fs.move_file(file_path, dest_path)
            if success:
                print(f"  Moved: {filename} → {category}/")
    
    async def _generate_documentation(self, fs: FileSystemTools):
        """Generate project structure documentation"""
        base_path = os.path.join(self.target_dir, self.output_dir)
        
        # Count files in each directory
        file_counts = {}
        subdirs = [
            ("experiments/ml_projects", os.path.join(base_path, "experiments", "ml_projects")),
            ("experiments/data_analysis", os.path.join(base_path, "experiments", "data_analysis")),
            ("learning/progress_tracking", os.path.join(base_path, "learning", "progress_tracking")),
            ("learning/resources", os.path.join(base_path, "learning", "resources")),
            ("personal/entertainment", os.path.join(base_path, "personal", "entertainment")),
            ("personal/collections", os.path.join(base_path, "personal", "collections"))
        ]
        
        for name, path in subdirs:
            files, _ = await fs.list_directory(path)
            file_counts[name] = len(files)
        
        # Generate documentation content
        doc_lines = [
            "Project Structure Documentation",
            "",
            f"Base Directory: {self.output_dir}",
            "",
            "1) experiments/",
            f"- ml_projects/ ({file_counts['experiments/ml_projects']} files)",
            "  * Python scripts for ML and utilities",
            f"- data_analysis/ ({file_counts['experiments/data_analysis']} files)",
            "  * CSV datasets and logs",
            "",
            "2) learning/",
            f"- progress_tracking/ ({file_counts['learning/progress_tracking']} files)",
            "  * Placeholder for tracking progress",
            f"- resources/ ({file_counts['learning/resources']} files)",
            "  * Learning-related documentation",
            "",
            "3) personal/",
            f"- entertainment/ ({file_counts['personal/entertainment']} files)",
            "  * Entertainment planning docs",
            f"- collections/ ({file_counts['personal/collections']} files)",
            "  * Music collection documentation",
            "",
            "Summary by directory:",
            f"- experiments/ml_projects: Python scripts for ML and utilities ({file_counts['experiments/ml_projects']} .py files)",
            f"- experiments/data_analysis: CSV datasets and logs ({file_counts['experiments/data_analysis']} .csv files)",
            f"- learning/resources: Learning-related documentation ({file_counts['learning/resources']} .md files)",
            f"- learning/progress_tracking: Placeholder for tracking progress (empty)",
            f"- personal/entertainment: Entertainment planning docs ({file_counts['personal/entertainment']} .md files)",
            f"- personal/collections: Music collection documentation ({file_counts['personal/collections']} .md file)"
        ]
        
        doc_content = '\n'.join(doc_lines)
        doc_path = os.path.join(base_path, "project_structure.md")
        
        success = await fs.write_file(doc_path, doc_content)
        if success:
            print(f"  Created: project_structure.md")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Organize project files into structured directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Organize projects (default output: organized_projects)
  python organize_projects.py /path/to/directory
  
  # Use a custom output directory name
  python organize_projects.py /path/to/directory --output-dir my_projects
  
  # The script will:
  # 1. Create a structured directory hierarchy
  # 2. Move Python files to experiments/ml_projects/
  # 3. Move CSV files to experiments/data_analysis/
  # 4. Categorize and move Markdown files to appropriate locations
  # 5. Generate project_structure.md documentation
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory to organize'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='organized_projects',
        help='Output directory name (default: organized_projects)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Create organizer and run
    organizer = ProjectOrganizer(
        target_dir=args.target_directory,
        output_dir=args.output_dir
    )
    
    try:
        await organizer.organize()
    except Exception as e:
        print(f"\nError during project organization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

