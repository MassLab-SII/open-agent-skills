#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Locate Zero123 guidance implementation (Using utils.py)
======================================================

在 threestudio 代码库中定位 Zero123 指导实现文件，输出 answer.txt 仅包含相对路径。
策略：
- 搜索包含 “zero123” 且文件路径含 “guidance” 或文件名含 zero123 的 python 文件
- 优先匹配 threestudio/models/guidance/zero123*.py
"""

import asyncio
import os
import argparse

from utils import FileSystemTools


class Zero123Locator:
    def __init__(self, target_dir: str, output_file: str = "answer.txt"):
        self.target_dir = target_dir
        self.output_file = output_file

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            py_files = await fs.search_files("**/*.py")
            candidates = []
            for path in py_files:
                lower = path.lower()
                if "zero123" in lower and ("guidance" in lower or "zero123" in os.path.basename(lower)):
                    candidates.append(path)

            if not candidates:
                print("No candidates found.")
                return

            # 优先 models/guidance/zero123*.py
            def score(p: str):
                s = 0
                if "models" in p and "guidance" in p:
                    s += 10
                if os.path.basename(p).startswith("zero123"):
                    s += 5
                if "systems" in p:
                    s += 2
                return -s  # lower is better for sorting

            candidates.sort(key=score)
            chosen = candidates[0]
            rel = os.path.relpath(chosen, self.target_dir).replace("\\", "/")

            await fs.write_file(os.path.join(self.target_dir, self.output_file), rel + "\n")
            print(f"Located guidance file: {rel}")
            print(f"Written to {self.output_file}")


async def main():
    parser = argparse.ArgumentParser(
        description="Locate Zero123 guidance implementation file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python code_locating.py /path/to/threestudio"
    )
    parser.add_argument("target_directory", help="Threestudio project root")
    parser.add_argument("--output", default="answer.txt", help="Output filename")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    locator = Zero123Locator(args.target_directory, args.output)
    try:
        await locator.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

