#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ScanNet -> SUN RGB-D Category Mapping & Counts (Using utils.py)
==============================================================

读取 ScanNet 标注，按 category 字段映射到 SUNRGBD 10 类，统计每类数量。
输出 analysis.txt：
<sun_category>
<count>
(空行分隔)
"""

import asyncio
import os
import argparse
import json
from collections import defaultdict
from typing import Dict, List

from utils import FileSystemTools

# 约定的 10 类（可根据数据调整），示例：
SUN10 = [
    "bed",
    "bookshelf",
    "chair",
    "desk",
    "dresser",
    "nightstand",
    "sofa",
    "table",
    "toilet",
    "tv",
]

# 简单同义词映射（可扩展）
ALIASES = {
    "night_stand": "nightstand",
    "night stand": "nightstand",
    "bookshelves": "bookshelf",
    "couch": "sofa",
}


class DatasetComparator:
    def __init__(self, target_dir: str, output_file: str = "analysis.txt"):
        self.target_dir = target_dir
        self.output_file = output_file
        self.counts = defaultdict(int)

    def normalize(self, cat: str) -> str:
        cat = cat.strip().lower().replace(" ", "_")
        if cat in ALIASES:
            cat = ALIASES[cat]
        return cat

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            # 搜索可能的标注文件，假设为 .json
            json_files = await fs.search_files("**/*.json")
            for path in json_files:
                content = await fs.read_text_file(path)
                if not content:
                    continue
                try:
                    data = json.loads(content)
                except Exception:
                    continue
                self._process_json(data)

            # 写出
            lines: List[str] = []
            for cat in SUN10:
                cnt = self.counts.get(cat, 0)
                lines.append(cat)
                lines.append(str(cnt))
                lines.append("")

            await fs.write_file(os.path.join(self.target_dir, self.output_file), "\n".join(lines).strip() + "\n")
            print(f"Wrote {self.output_file}")

    def _process_json(self, data):
        """
        假设 JSON 中有 objects 列表，每个对象含 category 字段。
        """
        objs = []
        if isinstance(data, dict):
            if "objects" in data and isinstance(data["objects"], list):
                objs = data["objects"]
        elif isinstance(data, list):
            objs = data

        for obj in objs:
            if not isinstance(obj, dict):
                continue
            cat = obj.get("category")
            if not cat:
                continue
            norm = self.normalize(str(cat))
            if norm in SUN10:
                self.counts[norm] += 1


async def main():
    parser = argparse.ArgumentParser(
        description="Map ScanNet categories to SUNRGBD 10 categories and count",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python dataset_comparison.py /path/to/votenet"
    )
    parser.add_argument("target_directory", help="Root directory containing annotations")
    parser.add_argument("--output", default="analysis.txt", help="Output filename")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    comp = DatasetComparator(args.target_directory, args.output)
    try:
        await comp.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

