#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Arrangement Script (Using utils.py)
========================================

This script organizes a desktop into categorized folders:
- work/     : work, research, project related files
- life/     : personal life related files
- archives/ : archived or dated/backup/tax files
- temp/     : temporary or draft files
- others/   : anything that doesn't fit above

Usage:
    python file_arrangement.py <target_directory>
"""

import asyncio
import os
import argparse
from typing import List

from utils import FileSystemTools


class FileArranger:
    """Organize files into categorized folders."""

    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.categories = {
            "work": [
                "work", "project", "projects", "client", "timesheet",
                "budget_tracker", "calculations", "experiment", "analysis"
            ],
            "life": [
                "life", "contact", "book", "emergency", "budget.csv",
                "important_dates", "fitness", "price_comparisons", "bookmark"
            ],
            "archives": [
                "archive", "archives", "backup", "tax", "correspondence",
                "2022", "2023", "2021", "old"
            ],
            "temp": [
                "temp", "draft", "tmp", "test_data"
            ]
        }

    async def arrange(self):
        async with FileSystemTools(self.target_dir) as fs:
            print("Step 1: Creating target folders...")
            for folder in ["work", "life", "archives", "temp", "others"]:
                await fs.create_directory(os.path.join(self.target_dir, folder))

            print("Step 2: Scanning files...")
            paths = await fs.search_files("**/*")
            # Keep only files (heuristic: exclude trailing '/')
            files = [p for p in paths if not p.endswith("/")]

            # Skip files already in target categories to avoid re-moving
            category_roots = tuple(
                os.path.join(self.target_dir, c) + os.sep for c in ["work", "life", "archives", "temp", "others"]
            )
            files = [f for f in files if not f.startswith(category_roots)]

            print(f"  Found {len(files)} files to classify")

            for file_path in files:
                dest_folder = self._classify(file_path)
                dest_path = os.path.join(self.target_dir, dest_folder, os.path.basename(file_path))
                success = await fs.move_file(file_path, dest_path)
                if success:
                    rel_src = os.path.relpath(file_path, self.target_dir)
                    print(f"  Moved {rel_src} -> {dest_folder}/")

            print("\nTask completed! Files organized.")

    def _classify(self, path: str) -> str:
        """Return destination folder name based on path heuristics."""
        lower_path = path.lower()

        # Archives first
        if any(key in lower_path for key in self.categories["archives"]):
            return "archives"
        # Temp
        if any(key in lower_path for key in self.categories["temp"]):
            return "temp"
        # Work
        if any(key in lower_path for key in self.categories["work"]):
            return "work"
        # Life
        if any(key in lower_path for key in self.categories["life"]):
            return "life"
        # Default
        return "others"


async def main():
    parser = argparse.ArgumentParser(
        description="Organize desktop files into categorized folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python file_arrangement.py /path/to/desktop_template
        """
    )
    parser.add_argument("target_directory", help="Desktop root directory")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    arranger = FileArranger(target_dir=args.target_directory)
    try:
        await arranger.arrange()
    except Exception as e:
        print(f"\nError during file arrangement: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

