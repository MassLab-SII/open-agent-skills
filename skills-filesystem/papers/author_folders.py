#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author Folders Organizer (Using utils.py)
=========================================

- 频繁作者：出现 >=4 篇论文，复制到 frequent_authors/<author>/
- 2025 多产作者：2025 年发表 >=3 篇，复制到 2025_authors/<author>/
- 保留原始 HTML，不移动，只复制
- 作者文件夹命名：全小写，空格/逗号换成下划线
"""

import asyncio
import os
import argparse
import re
from collections import defaultdict
from typing import List, Dict

from utils import FileSystemTools


def norm_author(name: str) -> str:
    return re.sub(r"[\\s,]+", "_", name.strip().lower())


def arxiv_year_from_id(filename: str) -> int | None:
    """
    arXiv 新式 ID 前两位为年份后两位，如 2401.xxxx -> 2024
    老式可能 1707.xxxx -> 2017
    """
    m = re.match(r"(\\d{2})\\d{2}\\.\\d{5}", filename)
    if not m:
        return None
    yy = int(m.group(1))
    # 粗略映射：17->2017, 25->2025
    return 2000 + yy


class AuthorFolders:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.author_papers: Dict[str, List[str]] = defaultdict(list)
        self.author_papers_2025: Dict[str, List[str]] = defaultdict(list)

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            html_files = await fs.search_files("*.html")
            html_files = [p for p in html_files if p.endswith(".html")]

            print(f"Found {len(html_files)} HTML papers")

            # 解析作者并统计
            for path in html_files:
                content = await fs.read_text_file(path)
                if not content:
                    continue
                authors = self._extract_authors(content)
                if not authors:
                    continue

                year = arxiv_year_from_id(os.path.basename(path)) or 0
                for a in authors:
                    self.author_papers[a].append(path)
                    if year == 2025:
                        self.author_papers_2025[a].append(path)

            # 创建目录
            frequent_dir = os.path.join(self.target_dir, "frequent_authors")
            prolific_dir = os.path.join(self.target_dir, "2025_authors")
            await fs.create_directory(frequent_dir)
            await fs.create_directory(prolific_dir)

            # 复制：频繁作者 >=4
            for author, papers in self.author_papers.items():
                if len(papers) >= 4:
                    await self._copy_group(fs, papers, os.path.join(frequent_dir, norm_author(author)))

            # 复制：2025 多产作者 >=3
            for author, papers in self.author_papers_2025.items():
                if len(papers) >= 3:
                    await self._copy_group(fs, papers, os.path.join(prolific_dir, norm_author(author)))

            print("Task completed.")

    async def _copy_group(self, fs: FileSystemTools, papers: List[str], dest_dir: str):
        await fs.create_directory(dest_dir)
        for src in papers:
            filename = os.path.basename(src)
            dst = os.path.join(dest_dir, filename)
            try:
                content = await fs.read_text_file(src)
                if content is None:
                    continue
                await fs.write_file(dst, content)
                rel = os.path.relpath(src, self.target_dir)
                print(f"  Copied {rel} -> {os.path.relpath(dst, self.target_dir)}")
            except Exception as e:
                print(f"  Warn: copy failed {src}: {e}")

    def _extract_authors(self, content: str) -> List[str]:
        # 从 meta 标签获取
        metas = re.findall(r'<meta[^>]+name=["\\\']citation_author["\\\'][^>]+content=["\\\']([^"\\\']+)["\\\']', content, flags=re.IGNORECASE)
        if metas:
            return [m.strip() for m in metas if m.strip()]

        # 退化：尝试“Authors:”行
        m = re.search(r"Authors?:\\s*(.+)", content)
        if m:
            raw = m.group(1)
            parts = re.split(r"[;,]", raw)
            return [p.strip() for p in parts if p.strip()]
        return []


async def main():
    parser = argparse.ArgumentParser(
        description="Organize papers into author folders (frequent and 2025 prolific)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python author_folders.py /path/to/papers
        """
    )
    parser.add_argument("target_directory", help="Directory containing papers")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    runner = AuthorFolders(args.target_directory)
    try:
        await runner.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

