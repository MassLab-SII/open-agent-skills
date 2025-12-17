#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Search by Product Name and Price Range
================================================

This skill performs advanced search with product name and price range filters.
Assumes you are already on the Advanced Search page.

Usage:
    python advanced_search_by_name.py <product_name> <price_from> <price_to> <name_ref> <price_from_ref> <price_to_ref> <search_btn_ref>

Example:
    python advanced_search_by_name.py "Ginger" 50.00 100.00 e91 e110 e114 e118

Note:
    For persistent browser sessions, first start: python browser_server.py
"""

import asyncio
import argparse
from browser_client import BrowserClient


async def advanced_search_by_name(
    product_name: str, 
    price_from: str, 
    price_to: str,
    name_ref: str,
    price_from_ref: str,
    price_to_ref: str,
    search_btn_ref: str
):
    """
    Perform advanced search by product name and price range.
    
    Args:
        product_name: Product name to search for
        price_from: Minimum price
        price_to: Maximum price
        name_ref: Element reference for Product Name field
        price_from_ref: Element reference for Price From field
        price_to_ref: Element reference for Price To field
        search_btn_ref: Element reference for Search button
        
    Note:
        This assumes you are already on the Advanced Search page.
        Uses browser_server.py for persistent browser sessions.
    """
    async with BrowserClient() as browser:
        # Fill search form
        print(f"Searching for '{product_name}' with price range ${price_from} - ${price_to}...")
        await browser.fill_form(fields=[
            {"name": "Product Name", "type": "textbox", "ref": name_ref, "value": product_name},
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
    parser = argparse.ArgumentParser(description="Advanced search by product name and price range")
    parser.add_argument("product_name", help="Product name to search for")
    parser.add_argument("price_from", help="Minimum price")
    parser.add_argument("price_to", help="Maximum price")
    parser.add_argument("name_ref", help="Element reference for Product Name field")
    parser.add_argument("price_from_ref", help="Element reference for Price From field")
    parser.add_argument("price_to_ref", help="Element reference for Price To field")
    parser.add_argument("search_btn_ref", help="Element reference for Search button")
    
    args = parser.parse_args()
    
    asyncio.run(advanced_search_by_name(
        args.product_name,
        args.price_from,
        args.price_to,
        args.name_ref,
        args.price_from_ref,
        args.price_to_ref,
        args.search_btn_ref
    ))


if __name__ == "__main__":
    main()

