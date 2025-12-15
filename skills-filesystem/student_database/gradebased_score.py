#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grade-based Score Calculator (Using utils.py)
=============================================

读取全部 basic_info.txt，提取语数英分数，按简单等级映射：
 A 90+, B 80-89, C 70-79, D 60-69, F <60

输出：
- student_grades.csv: student_id,name,chinese_score,chinese_grade,math_score,math_grade,english_score,english_grade
- grade_summary.txt: 每科 A/B/C/D/F 数，及每科通过(A/B/C)/不通过(D/F)人数，总人数
"""

import asyncio
import os
import argparse
from typing import Dict, List

from utils import FileSystemTools


GRADE_SCALE = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
    (0, "F"),
]


def grade(score: int) -> str:
    for thresh, g in GRADE_SCALE:
        if score >= thresh:
            return g
    return "F"


def parse_basic_info(content: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for line in content.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        data[key.strip().lower()] = val.strip()
    return data


class GradeCalculator:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.records: List[Dict[str, str]] = []
        self.summary = {
            "chinese": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "math": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "english": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
        }

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            basic_files = await fs.search_files("**/basic_info.txt")
            print(f"Found {len(basic_files)} basic_info.txt files")

            for path in basic_files:
                content = await fs.read_text_file(path)
                if not content:
                    continue
                info = parse_basic_info(content)
                sid = info.get("id") or info.get("student_id")
                name = info.get("name")
                try:
                    chi = int(info.get("chinese", -1))
                    math = int(info.get("math", -1))
                    eng = int(info.get("english", -1))
                except ValueError:
                    continue
                if sid is None or name is None:
                    continue

                g_chi = grade(chi)
                g_math = grade(math)
                g_eng = grade(eng)

                self.records.append({
                    "student_id": sid,
                    "name": name,
                    "chinese_score": chi,
                    "chinese_grade": g_chi,
                    "math_score": math,
                    "math_grade": g_math,
                    "english_score": eng,
                    "english_grade": g_eng,
                })

                self.summary["chinese"][g_chi] += 1
                self.summary["math"][g_math] += 1
                self.summary["english"][g_eng] += 1

            await self._write_csv(fs)
            await self._write_summary(fs)
            print("Task completed.")

    async def _write_csv(self, fs: FileSystemTools):
        headers = [
            "student_id", "name",
            "chinese_score", "chinese_grade",
            "math_score", "math_grade",
            "english_score", "english_grade",
        ]
        lines = [",".join(headers)]
        for r in self.records:
            row = [str(r[h]) for h in headers]
            lines.append(",".join(row))
        await fs.write_file(os.path.join(self.target_dir, "student_grades.csv"), "\n".join(lines))

    async def _write_summary(self, fs: FileSystemTools):
        total = len(self.records)
        def pass_fail(subj):
            passes = self.summary[subj]["A"] + self.summary[subj]["B"] + self.summary[subj]["C"]
            fails = self.summary[subj]["D"] + self.summary[subj]["F"]
            return passes, fails

        lines: List[str] = []
        lines.append(f"total students: {total}")
        for subj in ["chinese", "math", "english"]:
            counts = self.summary[subj]
            lines.append(f"{subj} A:{counts['A']} B:{counts['B']} C:{counts['C']} D:{counts['D']} F:{counts['F']}")
            p, f = pass_fail(subj)
            lines.append(f"{subj} pass:{p} fail:{f}")
        await fs.write_file(os.path.join(self.target_dir, "grade_summary.txt"), "\n".join(lines))


async def main():
    parser = argparse.ArgumentParser(
        description="Compute grades and summaries for student database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python gradebased_score.py /path/to/student_database"
    )
    parser.add_argument("target_directory", help="Root of student database")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    calc = GradeCalculator(args.target_directory)
    try:
        await calc.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

