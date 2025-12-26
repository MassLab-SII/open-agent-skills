#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Forum Skill
===================

Create a new forum/community.

Usage:
    python create_forum.py <name> <title> <description> <sidebar> <name_ref> <title_ref> <desc_ref> <sidebar_ref> <create_btn_ref>

Example:
    python create_forum.py "BudgetEuropeTravel" "Budget Travel Europe" "Community for sharing money-saving tips" "Share your best deals here!" e51 e56 e61 e69 e83
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_client import BrowserClient


async def create_forum(
    name: str,
    title: str,
    description: str,
    sidebar: str,
    name_ref: str,
    title_ref: str,
    desc_ref: str,
    sidebar_ref: str,
    create_btn_ref: str
):
    """
    Create a new forum.
    
    Args:
        name: Forum name (URL slug)
        title: Forum title
        description: Forum description
        sidebar: Sidebar content
        name_ref: Ref for name textbox
        title_ref: Ref for title textbox
        desc_ref: Ref for description textbox
        sidebar_ref: Ref for sidebar textbox
        create_btn_ref: Ref for "Create forum" button
    
    Returns:
        Snapshot of the page after forum creation
    """
    async with BrowserClient() as browser:
        print(f"📝 Entering forum name: {name}")
        await browser.type_text(ref=name_ref, text=name, element="Name textbox")
        
        print(f"📝 Entering forum title: {title}")
        await browser.type_text(ref=title_ref, text=title, element="Title textbox")
        
        print(f"📝 Entering description")
        await browser.type_text(ref=desc_ref, text=description, element="Description textbox")
        
        print(f"📝 Entering sidebar")
        await browser.type_text(ref=sidebar_ref, text=sidebar, element="Sidebar textbox")
        
        print(f"✅ Clicking Create forum")
        await browser.click(ref=create_btn_ref, element="Create forum button")
        
        await browser.wait_for_time(1)
        result = await browser.snapshot()
        print("✅ Forum created!")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Create a new forum")
    parser.add_argument("name", help="Forum name (URL slug)")
    parser.add_argument("title", help="Forum title")
    parser.add_argument("description", help="Forum description")
    parser.add_argument("sidebar", help="Sidebar content")
    parser.add_argument("name_ref", help="Element reference for name textbox")
    parser.add_argument("title_ref", help="Element reference for title textbox")
    parser.add_argument("desc_ref", help="Element reference for description textbox")
    parser.add_argument("sidebar_ref", help="Element reference for sidebar textbox")
    parser.add_argument("create_btn_ref", help="Element reference for Create forum button")
    
    args = parser.parse_args()
    
    print(f"🚀 Create Forum Skill")
    print(f"   Name: {args.name}")
    print(f"   Title: {args.title}")
    print("-" * 40)
    
    result = asyncio.run(create_forum(
        args.name,
        args.title,
        args.description,
        args.sidebar,
        args.name_ref,
        args.title_ref,
        args.desc_ref,
        args.sidebar_ref,
        args.create_btn_ref
    ))
    
    if result:
        print(f"\n📄 Page snapshot:\n{result}")


if __name__ == "__main__":
    main()
