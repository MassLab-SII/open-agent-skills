#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Post Skill
==================

Create a new post/submission in a forum.

Usage:
    python create_post.py <title> <body> <title_ref> <body_ref> <create_btn_ref>

Example:
    python create_post.py "My Post Title" "Post body content here" e58 e63 e82
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_client import BrowserClient


async def create_post(
    title: str,
    body: str,
    title_ref: str,
    body_ref: str,
    create_btn_ref: str
):
    """
    Create a new post in the forum.
    
    Args:
        title: Post title
        body: Post body text
        title_ref: Ref for title textbox
        body_ref: Ref for body textbox
        create_btn_ref: Ref for "Create submission" button
    
    Returns:
        Snapshot of the page after posting
    """
    async with BrowserClient() as browser:
        print(f"📄 Entering title: {title}")
        await browser.type_text(ref=title_ref, text=title, element="Title textbox")
        
        print(f"📝 Entering body")
        await browser.type_text(ref=body_ref, text=body, element="Body textbox")
        
        print(f"✅ Clicking Create submission")
        await browser.click(ref=create_btn_ref, element="Create submission button")
        
        await browser.wait_for_time(1)
        result = await browser.snapshot()
        print("✅ Post created!")
        
        return result


def main():
    # Manually parse arguments to support bodies starting with "-"
    if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        parser = argparse.ArgumentParser(description="Create a new post in the forum")
        parser.add_argument("title", help="Post title")
        parser.add_argument("body", help="Post body text")
        parser.add_argument("title_ref", help="Element reference for title textbox")
        parser.add_argument("body_ref", help="Element reference for body textbox")
        parser.add_argument("create_btn_ref", help="Element reference for Create submission button")
        parser.print_help()
        return

    if len(sys.argv) != 6:
        print("Usage: python create_post.py <title> <body> <title_ref> <body_ref> <create_btn_ref>")
        print("For help: python create_post.py --help")
        sys.exit(1)

    title = sys.argv[1]
    body = sys.argv[2]
    title_ref = sys.argv[3]
    body_ref = sys.argv[4]
    create_btn_ref = sys.argv[5]

    # Support reading body from stdin for multi-line content
    if body == "-":
        body = sys.stdin.read().strip()
    else:
        # Convert \n escape sequences to actual newlines
        body = body.replace("\\n", "\n")
    
    print(f"🚀 Create Post Skill")
    print(f"   Title: {title}")
    print("-" * 40)
    
    result = asyncio.run(create_post(
        title,
        body,
        title_ref,
        body_ref,
        create_btn_ref
    ))
    
    if result:
        print(f"\n📄 Page snapshot:\n{result}")


if __name__ == "__main__":
    main()
