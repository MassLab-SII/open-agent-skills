#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Search - Type and Submit
================================

This skill performs a simple search by typing the search term and pressing Enter.

Usage:
    python simple_search.py <search_term> <search_input_ref>

Example:
    python simple_search.py "gingerbread" e35

Note:
    For persistent browser sessions, first start: python browser_server.py
"""

import asyncio
import argparse
from browser_client import BrowserClient


async def simple_search(search_term: str, search_ref: str):
    """
    Perform a simple search by typing the term and pressing Enter.
    
    Args:
        search_term: The text to search for
        search_ref: Element reference for the search input field
        
    Note:
        This assumes a search input is visible on the current page.
        Uses browser_server.py for persistent browser sessions.
    """
    async with BrowserClient() as browser:
        # Type search term
        print(f"Searching for '{search_term}'...")
        await browser.type_text(ref=search_ref, text=search_term, element="Search input")
        
        # Press Enter to submit
        print("Submitting search...")
        await browser.press_key("Enter")
        
        # Take snapshot to see results
        print("Getting search results...")
        snapshot = await browser.snapshot()
        
        print("✓ Search completed successfully!")
        return snapshot


def main():
    parser = argparse.ArgumentParser(description="Simple search - type and submit with Enter")
    parser.add_argument("search_term", help="Text to search for")
    parser.add_argument("search_ref", help="Element reference for search input field")
    
    args = parser.parse_args()
    
    result = asyncio.run(simple_search(args.search_term, args.search_ref))
    if result:
        print(result)


if __name__ == "__main__":
    main()
