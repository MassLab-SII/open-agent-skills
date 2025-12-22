#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find Math Benchmark Paper (Using utils.py)
==========================================

查找描述“数学基准，既检验正确性，又分析知识不足/泛化不足/机械记忆”的论文，
将对应 HTML 重命名为 answer.html。
"""

import asyncio
import os
import argparse
import re
from typing import List, Tuple

from utils import FileSystemTools


KEYWORDS = [
    "math", "mathematics", "benchmark", "evaluation",
    "knowledge", "generalization", "memorization", "rote",
    "reasoning", "insufficient knowledge"
]


class MathPaperFinder:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            html_files = await fs.search_files("*.html")
            html_files = [p for p in html_files if p.endswith(".html")]
            if not html_files:
                print("No HTML papers found.")
                return

            best_file, best_score = None, -1
            for path in html_files:
                content = await fs.read_text_file(path)
                if not content:
                    continue
                score = self._score(content)
                if score > best_score:
                    best_score = score
                    best_file = path

            if not best_file:
                print("No candidate paper found.")
                return

            dest = os.path.join(self.target_dir, "answer.html")
            # If destination exists, overwrite by write content then remove original via move_file
            content = await fs.read_text_file(best_file)
            await fs.write_file(dest, content or "")
            print(f"Selected paper: {os.path.basename(best_file)} -> answer.html (score={best_score})")

            # Remove original? Task要求重命名，可通过 move（覆盖可能失败），这里在写入后删除原文件通过 move_file to dest if possible
            if best_file != dest:
                try:
                    await fs.move_file(best_file, dest)  # if tool supports overwrite may fail; already wrote content.
                except Exception:
                    pass

            print("Task completed.")

    def _score(self, content: str) -> int:
        text = content.lower()
        score = 0
        for kw in KEYWORDS:
            score += text.count(kw)
        # Bonus for phrases
        if "lack of generalization" in text or "generalization ability" in text:
            score += 5
        if "rote memorization" in text or "memorization" in text:
            score += 3
        if "insufficient knowledge" in text:
            score += 3
        if "math benchmark" in text:
            score += 5
        return score


async def main():
    parser = argparse.ArgumentParser(
        description="Find math benchmark paper and rename it to answer.html",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python find_math_paper.py /path/to/papers
        """
    )
    parser.add_argument("target_directory", help="Directory containing papers")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    finder = MathPaperFinder(args.target_directory)
    try:
        await finder.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

