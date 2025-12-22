#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duplicate Name Detector (Using utils.py)
========================================

扫描全部学生 basic_info.txt，找出同名学生，输出 namesake.txt：
name: xxx
count: n
ids: id1, id2, ...

块之间空一行。
"""

import asyncio
import os
import argparse
import re
from collections import defaultdict
from typing import Dict, List

from utils import FileSystemTools


def parse_basic_info(content: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for line in content.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        data[key.strip().lower()] = val.strip()
    return data


class DuplicateNameFinder:
    def __init__(self, target_dir: str, output_file: str = "namesake.txt"):
        self.target_dir = target_dir
        self.output_file = output_file

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            basic_files = await fs.search_files("**/basic_info.txt")
            print(f"Found {len(basic_files)} basic_info.txt files")

            name_to_ids: Dict[str, List[str]] = defaultdict(list)

            for path in basic_files:
                content = await fs.read_text_file(path)
                if not content:
                    continue
                info = parse_basic_info(content)
                name = info.get("name")
                sid = info.get("id") or info.get("student_id")
                if name and sid:
                    name_to_ids[name].append(sid)

            # Build output
            lines: List[str] = []
            for name, ids in sorted(name_to_ids.items()):
                if len(ids) <= 1:
                    continue
                lines.append(f"name: {name}")
                lines.append(f"count: {len(ids)}")
                lines.append(f"ids: {', '.join(ids)}")
                lines.append("")  # blank line

            output_path = os.path.join(self.target_dir, self.output_file)
            await fs.write_file(output_path, "\n".join(lines).strip() + "\n")
            print(f"Created {self.output_file}")


async def main():
    parser = argparse.ArgumentParser(
        description="Identify duplicate student names and list their IDs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python duplicate_name.py /path/to/student_database"
    )
    parser.add_argument("target_directory", help="Root of student database")
    parser.add_argument("--output", default="namesake.txt", help="Output filename")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    runner = DuplicateNameFinder(args.target_directory, args.output)
    try:
        await runner.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

