#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Search by Description and Price Range
===============================================

This skill performs advanced search with description and price range filters.
Assumes you are already on the Advanced Search page.

Usage:
    python advanced_search_by_description.py <description> <price_from> <price_to> <desc_ref> <price_from_ref> <price_to_ref> <search_btn_ref>

Example:
    python advanced_search_by_description.py "vitamin" 0.00 99.99 e99 e110 e114 e118
"""

import asyncio
import argparse
from utils import BrowserTools


async def advanced_search_by_description(
    description: str, 
    price_from: str, 
    price_to: str,
    desc_ref: str,
    price_from_ref: str,
    price_to_ref: str,
    search_btn_ref: str
):
    """
    Perform advanced search by description and price range.
    
    Args:
        description: Description keyword to search for
        price_from: Minimum price
        price_to: Maximum price
        desc_ref: Element reference for Description field
        price_from_ref: Element reference for Price From field
        price_to_ref: Element reference for Price To field
        search_btn_ref: Element reference for Search button
        
    Note:
        This assumes you are already on the Advanced Search page.
    """
    async with BrowserTools() as browser:
        # Fill search form with description field
        print(f"Searching for description containing '{description}' with price range ${price_from} - ${price_to}...")
        await browser.fill_form(fields=[
            {"name": "Description", "type": "textbox", "ref": desc_ref, "value": description},
            {"name": "Price From", "type": "textbox", "ref": price_from_ref, "value": price_from},
            {"name": "Price To", "type": "textbox", "ref": price_to_ref, "value": price_to}
        ])
        
        # Click Search button
        print("Submitting search...")
        result = await browser.click(ref=search_btn_ref, element="Search button")
        
        # Take snapshot to see results
        print("Getting search results...")
        snapshot = await browser.snapshot()
        
        print("✓ Advanced search completed successfully!")
        return snapshot


def main():
    parser = argparse.ArgumentParser(description="Advanced search by description and price range")
    parser.add_argument("description", help="Description keyword to search for")
    parser.add_argument("price_from", help="Minimum price")
    parser.add_argument("price_to", help="Maximum price")
    parser.add_argument("desc_ref", help="Element reference for Description field")
    parser.add_argument("price_from_ref", help="Element reference for Price From field")
    parser.add_argument("price_to_ref", help="Element reference for Price To field")
    parser.add_argument("search_btn_ref", help="Element reference for Search button")
    
    args = parser.parse_args()
    
    asyncio.run(advanced_search_by_description(
        args.description,
        args.price_from,
        args.price_to,
        args.desc_ref,
        args.price_from_ref,
        args.price_to_ref,
        args.search_btn_ref
    ))


if __name__ == "__main__":
    main()

