#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate requirements.txt for VoteNet (Using utils.py)
======================================================

基于常见 VoteNet/3D 检测依赖生成 requirements.txt，覆盖点云处理、
深度学习、可视化与网格处理等核心库。若已有 requirements.txt，将合并去重。
"""

import asyncio
import os
import argparse

from utils import FileSystemTools

# 常见依赖列表（版本留空，便于环境适配）
BASE_REQUIREMENTS = [
    "torch",
    "torchvision",
    "numpy",
    "scipy",
    "scikit-learn",
    "matplotlib",
    "pyyaml",
    "tqdm",
    "h5py",
    "opencv-python",
    "open3d",
    "trimesh",
    "plyfile",
    "pandas",
    "networkx",
    "tensorboard",
    # 可能用到的可视化/日志
    "einops",
]


class RequirementsWriter:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            req_path = os.path.join(self.target_dir, "requirements.txt")

            existing = set()
            try:
                content = await fs.read_text_file(req_path)
                if content:
                    existing = set(
                        ln.strip() for ln in content.splitlines() if ln.strip()
                    )
            except Exception:
                pass

            final = list(existing)
            for dep in BASE_REQUIREMENTS:
                if dep not in existing:
                    final.append(dep)

            final = sorted(final)
            new_content = "\n".join(final) + "\n"
            await fs.write_file(req_path, new_content)
            print(f"Wrote requirements.txt with {len(final)} entries.")


async def main():
    parser = argparse.ArgumentParser(
        description="Generate VoteNet requirements.txt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python requirements_writing.py /path/to/votenet"
    )
    parser.add_argument("target_directory", help="VoteNet project root")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    writer = RequirementsWriter(args.target_directory)
    try:
        await writer.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

