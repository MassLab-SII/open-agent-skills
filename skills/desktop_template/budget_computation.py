#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Budget Computation Script (Using utils.py)
==========================================

This script scans the desktop template, extracts personal life expenses,
and produces a summary file `total_budget.txt`.

Rules implemented:
- Only personal/life expenses are included (exclude work/project-related paths).
- Each numeric value found in a personal file is treated as an expense entry.
- Output format: one line per entry `file_path;price` (relative path, 2 decimals),
  last line is the total sum (2 decimals).
"""

import asyncio
import os
import argparse
import re
from typing import List, Tuple

from utils import FileSystemTools


class BudgetComputer:
    """Compute personal budget from desktop template files."""

    def __init__(self, target_dir: str, output_filename: str = "total_budget.txt"):
        self.target_dir = target_dir
        self.output_filename = output_filename
        self.entries: List[Tuple[str, float]] = []

        # Heuristics for personal vs work
        self.exclude_keywords = [
            "work", "projects", "project", "client", "timesheet",
            "budget_tracker", "experiment", "analysis", "ml"
        ]
        self.include_keywords = [
            "life", "downloads", "documents/budget", "documents/personal",
            "archives", "important_dates", "price_comparisons",
            "fitness", "expenses", "tax"
        ]

    async def compute(self):
        async with FileSystemTools(self.target_dir) as fs:
            print("Step 1: Scanning files...")
            paths = await fs.search_files("**/*")
            files = [p for p in paths if not p.endswith("/")]
            print(f"  Found {len(files)} paths")

            # Process each file
            for file_path in files:
                if not self._is_personal(file_path):
                    continue

                rel_path = os.path.relpath(file_path, self.target_dir)
                content = await fs.read_text_file(file_path)
                if not content:
                    continue

                nums = self._extract_numbers(content)
                if not nums:
                    continue

                for num in nums:
                    self.entries.append((rel_path, num))

            print(f"  Collected {len(self.entries)} expense entries\n")

            # Step 2: Write output
            print("Step 2: Writing total_budget.txt...")
            total = sum(price for _, price in self.entries)
            lines = [f"{path};{price:.2f}" for path, price in self.entries]
            lines.append(f"{total:.2f}")
            output_path = os.path.join(self.target_dir, self.output_filename)
            success = await fs.write_file(output_path, "\n".join(lines))

            if success:
                print(f"  Created: {self.output_filename}")
                print(f"  Total: {total:.2f}")
                print("\nTask completed successfully!")

    def _is_personal(self, path: str) -> bool:
        """Heuristic to decide if a file is personal (not work/project)."""
        lower = path.lower()
        if any(key in lower for key in self.exclude_keywords):
            return False
        if any(key in lower for key in self.include_keywords):
            return True
        # Default: if under Downloads, Archives, Documents (non-work), Life
        return True

    def _extract_numbers(self, content: str) -> List[float]:
        """Extract positive numeric values from content."""
        nums = []
        for match in re.findall(r"-?\\d+(?:\\.\\d+)?", content):
            try:
                val = float(match)
                if val > 0:
                    nums.append(val)
            except ValueError:
                continue
        return nums


async def main():
    parser = argparse.ArgumentParser(
        description="Compute personal budget from desktop template files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python budget_computation.py /path/to/desktop_template
  python budget_computation.py /path/to/desktop_template --output my_budget.txt
        """
    )
    parser.add_argument("target_directory", help="Desktop root directory")
    parser.add_argument("--output", type=str, default="total_budget.txt",
                        help="Output filename (default: total_budget.txt)")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    computer = BudgetComputer(target_dir=args.target_directory,
                              output_filename=args.output)
    try:
        await computer.compute()
    except Exception as e:
        print(f"\nError during budget computation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

