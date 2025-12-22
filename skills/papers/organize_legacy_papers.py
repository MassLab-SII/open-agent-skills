#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Organize Legacy Papers (Using utils.py)
=======================================

- 将 2023 及更早的 HTML 论文按年份移动到 organized/<year>/ 保留文件名
- 2024 及之后的论文和 arxiv_2025.bib 原地保留
- 每个年份生成 INDEX.md（表：ArXiv ID | Authors | Local Path）
- organized/SUMMARY.md 汇总年份索引
"""

import asyncio
import os
import argparse
import re
from typing import List, Dict, Tuple

from utils import FileSystemTools


def arxiv_year_from_id(filename: str) -> int | None:
    m = re.match(r"(\\d{2})\\d{2}\\.\\d{5}", filename)
    if not m:
        return None
    yy = int(m.group(1))
    return 2000 + yy


def extract_authors(meta_html: str) -> List[str]:
    authors = re.findall(r'<meta[^>]+name=["\\\']citation_author["\\\'][^>]+content=["\\\']([^"\\\']+)["\\\']', meta_html, flags=re.IGNORECASE)
    return [a.strip() for a in authors if a.strip()]


class LegacyOrganizer:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.year_buckets: Dict[int, List[str]] = {}

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            html_files = await fs.search_files("*.html")
            html_files = [p for p in html_files if p.endswith(".html")]
            print(f"Found {len(html_files)} HTML papers")

            # Bucket by year
            for path in html_files:
                fname = os.path.basename(path)
                year = arxiv_year_from_id(fname)
                if year is None:
                    continue
                if year >= 2024:
                    continue  # keep in place
                self.year_buckets.setdefault(year, []).append(path)

            organized_root = os.path.join(self.target_dir, "organized")
            await fs.create_directory(organized_root)

            # Move papers and build index data
            index_data: Dict[int, List[Tuple[str, List[str]]]] = {}
            for year, files in self.year_buckets.items():
                year_dir = os.path.join(organized_root, str(year))
                await fs.create_directory(year_dir)
                index_rows = []
                for src in files:
                    fname = os.path.basename(src)
                    dst = os.path.join(year_dir, fname)
                    # Move file
                    success = await fs.move_file(src, dst)
                    if success:
                        content = await fs.read_text_file(dst)
                        authors = extract_authors(content or "")[:3]
                        if len(extract_authors(content or "")) > 3:
                            if authors:
                                authors[-1] = authors[-1] + ", et al."
                        author_str = ", ".join(authors)
                        index_rows.append((fname, author_str, fname))
                        rel = os.path.relpath(dst, self.target_dir)
                        print(f"  Moved {os.path.relpath(src, self.target_dir)} -> {rel}")
                # sort by arxiv id
                index_rows.sort(key=lambda x: x[0])
                index_data[year] = index_rows

                # Write INDEX.md
                lines = ["ArXiv ID | Authors | Local Path", "---|---|---"]
                for arxiv_id, authors, local_path in index_rows:
                    lines.append(f"{arxiv_id} | {authors} | {local_path}")
                await fs.write_file(os.path.join(year_dir, "INDEX.md"), "\n".join(lines))

            # Write SUMMARY.md
            summary_lines = ["Year | Paper Count | Index Link", "---|---|---"]
            for year in sorted(index_data.keys()):
                count = len(index_data[year])
                summary_lines.append(f"{year} | {count} | [View Index]({year}/INDEX.md)")
            await fs.write_file(os.path.join(organized_root, "SUMMARY.md"), "\n".join(summary_lines))

            print("Task completed.")


async def main():
    parser = argparse.ArgumentParser(
        description="Organize 2023及更早论文到按年目录，生成索引与汇总",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python organize_legacy_papers.py /path/to/papers
        """
    )
    parser.add_argument("target_directory", help="Papers root directory")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    org = LegacyOrganizer(args.target_directory)
    try:
        await org.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

