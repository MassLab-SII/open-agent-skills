#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Wiki Skill
==================

Create a new wiki page for a forum.

Usage:
    python create_wiki.py <url_path> <title> <body> <url_ref> <title_ref> <body_ref> <save_btn_ref>

Example:
    python create_wiki.py "europe-travel-guide" "Complete Budget Travel Guide" "Wiki content here" e51 e56 e62 e69
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_client import BrowserClient


async def create_wiki(
    url_path: str,
    title: str,
    body: str,
    url_ref: str,
    title_ref: str,
    body_ref: str,
    save_btn_ref: str
):
    """
    Create a new wiki page.
    
    Args:
        url_path: Wiki page URL path
        title: Wiki page title
        body: Wiki page content
        url_ref: Ref for URL textbox
        title_ref: Ref for title textbox
        body_ref: Ref for body textbox
        save_btn_ref: Ref for "Save" button
    
    Returns:
        Snapshot of the page after wiki creation
    """
    async with BrowserClient() as browser:
        print(f"🔗 Entering URL path: {url_path}")
        await browser.type_text(ref=url_ref, text=url_path, element="URL textbox")
        
        print(f"📄 Entering title: {title}")
        await browser.type_text(ref=title_ref, text=title, element="Title textbox")
        
        print(f"📝 Entering body content")
        await browser.type_text(ref=body_ref, text=body, element="Body textbox")
        
        print(f"✅ Clicking Save")
        await browser.click(ref=save_btn_ref, element="Save button")
        
        await browser.wait_for_time(1)
        result = await browser.snapshot()
        print("✅ Wiki page created!")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Create a new wiki page")
    parser.add_argument("url_path", help="Wiki page URL path")
    parser.add_argument("title", help="Wiki page title")
    parser.add_argument("body", help="Wiki page content")
    parser.add_argument("url_ref", help="Element reference for URL textbox")
    parser.add_argument("title_ref", help="Element reference for title textbox")
    parser.add_argument("body_ref", help="Element reference for body textbox")
    parser.add_argument("save_btn_ref", help="Element reference for Save button")
    
    args = parser.parse_args()
    
    print(f"🚀 Create Wiki Skill")
    print(f"   Path: {args.url_path}")
    print(f"   Title: {args.title}")
    print("-" * 40)
    
    result = asyncio.run(create_wiki(
        args.url_path,
        args.title,
        args.body,
        args.url_ref,
        args.title_ref,
        args.body_ref,
        args.save_btn_ref
    ))
    
    if result:
        print(f"\n📄 Page snapshot:\n{result}")


if __name__ == "__main__":
    main()
