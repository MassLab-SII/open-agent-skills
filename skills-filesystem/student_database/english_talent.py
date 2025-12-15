#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
English Talent Selector (Using utils.py)
========================================

筛选满足：
1) recommendation_letter.txt 评级为 S 或 A
2) TOEFL >= 100
输出 qualified_students.txt：
name: xxx
id: xxx
email: xxx
块之间空一行。
"""

import asyncio
import os
import argparse
import re
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


def parse_recommendation(content: str) -> str | None:
    # 查找 S/A
    m = re.search(r"grade\\s*[:：]\\s*([SA])", content, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # 回退：直接找 S 或 A 单独行
    m = re.search(r"\\b([SA])\\b", content)
    if m:
        return m.group(1).upper()
    return None


class EnglishTalentSelector:
    def __init__(self, target_dir: str, output_file: str = "qualified_students.txt"):
        self.target_dir = target_dir
        self.output_file = output_file
        self.results: List[Dict[str, str]] = []

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            basic_files = await fs.search_files("**/basic_info.txt")
            print(f"Found {len(basic_files)} basic_info.txt files")

            for basic_path in basic_files:
                # parse basic info
                basic_content = await fs.read_text_file(basic_path)
                if not basic_content:
                    continue
                info = parse_basic_info(basic_content)
                name = info.get("name")
                sid = info.get("id") or info.get("student_id")
                email = info.get("email")
                toefl = info.get("toefl")

                try:
                    toefl_score = int(toefl) if toefl is not None else -1
                except ValueError:
                    toefl_score = -1

                # recommendation letter
                rec_path = os.path.join(os.path.dirname(basic_path), "recommendation_letter.txt")
                rec_content = await fs.read_text_file(rec_path)
                grade = parse_recommendation(rec_content or "") if rec_content else None

                if name and sid and email and grade in ("S", "A") and toefl_score >= 100:
                    self.results.append({"name": name, "id": sid, "email": email})

            # build output
            lines: List[str] = []
            for stu in self.results:
                lines.append(f"name: {stu['name']}")
                lines.append(f"id: {stu['id']}")
                lines.append(f"email: {stu['email']}")
                lines.append("")

            output_path = os.path.join(self.target_dir, self.output_file)
            await fs.write_file(output_path, "\n".join(lines).strip() + "\n")
            print(f"Created {self.output_file} with {len(self.results)} students.")


async def main():
    parser = argparse.ArgumentParser(
        description="Select English-proficient students (S/A and TOEFL>=100)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python english_talent.py /path/to/student_database"
    )
    parser.add_argument("target_directory", help="Root of student database")
    parser.add_argument("--output", default="qualified_students.txt", help="Output filename")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    selector = EnglishTalentSelector(args.target_directory, args.output)
    try:
        await selector.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

