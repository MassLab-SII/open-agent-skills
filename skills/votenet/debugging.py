#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VoteNet Debugging Helper (Using utils.py)
=========================================

辅助定位并记录 VoteNet backbone 的 bug 文件路径。
实际修复需人工根据项目情况完成；此脚本只搜索可疑文件并写入 answer.txt。
"""

import asyncio
import os
import argparse

from utils import FileSystemTools


class DebugLocator:
    def __init__(self, target_dir: str, output_file: str = "answer.txt"):
        self.target_dir = target_dir
        self.output_file = output_file

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            py_files = await fs.search_files("**/*.py")
            candidates = []
            for path in py_files:
                lower = path.lower()
                if "backbone" in lower or "pointnet" in lower or "votenet" in lower:
                    candidates.append(path)

            if not candidates:
                print("No backbone-related files found.")
                return

            # 简单优先级：含 votenet 或 backbone 关键词的深层路径
            candidates.sort(key=lambda p: (0 if "votenet" in p.lower() else 1, len(p)))
            chosen = candidates[0]
            rel = os.path.relpath(chosen, self.target_dir).replace("\\", "/")

            await fs.write_file(os.path.join(self.target_dir, self.output_file), rel + "\n")
            print(f"Recorded potential bug file: {rel}")


async def main():
    parser = argparse.ArgumentParser(
        description="Locate potential VoteNet backbone bug file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python debugging.py /path/to/votenet"
    )
    parser.add_argument("target_directory", help="VoteNet project root")
    parser.add_argument("--output", default="answer.txt", help="Output filename")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    locator = DebugLocator(args.target_directory, args.output)
    try:
        await locator.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

