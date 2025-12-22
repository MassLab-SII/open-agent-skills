#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restore Zero123 dependencies in requirements.txt (Using utils.py)
=================================================================

查找 threestudio 项目中的 requirements.txt，将 Zero123 相关依赖补全到文件末尾。
已存在的行不重复添加，保持一行一个依赖。
"""

import asyncio
import os
import argparse

from utils import FileSystemTools

# 依据 Zero123/扩散/指导常用依赖整理的一组基础依赖
ZERO123_DEPS = [
    "einops",
    "k-diffusion",
    "transformers",
    "diffusers",
    "omegaconf",
    "pytorch-lightning",
    "open-clip-torch",
    "trimesh",
    "imageio[ffmpeg]",
]


class RequirementsRestorer:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            # 定位 requirements.txt
            candidates = await fs.search_files("**/requirements.txt")
            if not candidates:
                print("requirements.txt not found.")
                return
            req_path = candidates[0]
            print(f"Found requirements.txt: {req_path}")

            content = await fs.read_text_file(req_path) or ""
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            existing = set(lines)

            added = []
            for dep in ZERO123_DEPS:
                if dep not in existing:
                    lines.append(dep)
                    added.append(dep)

            # 保持原有顺序，新增依赖追加在末尾
            new_content = "\n".join(lines) + "\n"
            await fs.write_file(req_path, new_content)

            print(f"Added {len(added)} deps: {', '.join(added) if added else 'none'}")
            print("Task completed.")


async def main():
    parser = argparse.ArgumentParser(
        description="Restore Zero123 dependencies into requirements.txt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python requirements_completion.py /path/to/threestudio"
    )
    parser.add_argument("target_directory", help="Threestudio project root")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    runner = RequirementsRestorer(args.target_directory)
    try:
        await runner.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

