#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zero123 guidance_out analyzer (Using utils.py)
=============================================

读取 threestudio/systems/zero123.py，分析 line 137 附近的 guidance_out，
推断其结构（若是 dict 列出 key；否则输出片段）。将结果写入 answer.txt。
"""

import asyncio
import os
import argparse
import re
from typing import List

from utils import FileSystemTools


class GuidanceOutAnalyzer:
    def __init__(self, target_dir: str, output_file: str = "answer.txt"):
        self.target_dir = target_dir
        self.output_file = output_file

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            target_path = None
            # 优先标准路径
            cand = os.path.join(self.target_dir, "threestudio", "systems", "zero123.py")
            if await self._exists(fs, cand):
                target_path = cand
            else:
                # 搜索 zero123.py
                files = await fs.search_files("**/zero123.py")
                if files:
                    target_path = files[0]

            if not target_path:
                print("zero123.py not found.")
                return

            content = await fs.read_text_file(target_path)
            if not content:
                print("zero123.py empty.")
                return

            lines = content.splitlines()
            idx = self._find_guidance_out_line(lines)
            snippet = self._extract_snippet(lines, idx)
            keys = self._extract_keys(snippet)

            out_lines: List[str] = []
            rel = os.path.relpath(target_path, self.target_dir).replace("\\", "/")
            if keys:
                out_lines.append(f"guidance_out: dict with keys {', '.join(keys)}")
            else:
                out_lines.append("guidance_out snippet:")
                out_lines.extend(snippet)
            out_lines.append(f"path: {rel}")

            await fs.write_file(os.path.join(self.target_dir, self.output_file), "\n".join(out_lines) + "\n")
            print(f"Wrote analysis to {self.output_file}")

    async def _exists(self, fs: FileSystemTools, path: str) -> bool:
        try:
            await fs.get_file_info(path)
            return True
        except Exception:
            return False

    def _find_guidance_out_line(self, lines: List[str]) -> int:
        for i, ln in enumerate(lines):
            if "guidance_out" in ln and "=" in ln:
                return i
        return -1

    def _extract_snippet(self, lines: List[str], idx: int) -> List[str]:
        if idx == -1:
            return lines[:10] if len(lines) > 10 else lines
        start = max(0, idx - 5)
        end = min(len(lines), idx + 15)
        return [lines[i].strip() for i in range(start, end)]

    def _extract_keys(self, snippet: List[str]) -> List[str]:
        text = "\n".join(snippet)
        # 如果是字典字面量
        if "{" in text and "}" in text:
            keys = re.findall(r"[\"']([^\"']+)[\"']\\s*:", text)
            return list(dict.fromkeys(keys))  # 去重保持顺序
        return []


async def main():
    parser = argparse.ArgumentParser(
        description="Analyze guidance_out structure in zero123.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python output_analysis.py /path/to/threestudio"
    )
    parser.add_argument("target_directory", help="Threestudio project root")
    parser.add_argument("--output", default="answer.txt", help="Output filename")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    analyzer = GuidanceOutAnalyzer(args.target_directory, args.output)
    try:
        await analyzer.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

