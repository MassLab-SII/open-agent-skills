#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Customer Skill
======================

Create a new customer in Magento Admin.

Usage:
    python create_customer.py <first_name> <last_name> <email> <group> <group_ref> <fname_ref> <lname_ref> <email_ref> <save_btn_ref>

Example:
    python create_customer.py "Isabella" "Romano" "isabella.romano@premium.eu" "Premium Europe" e92 e112 e124 e136 e61

Prerequisites:
    - Must be logged into Admin panel
    - Must be on the All Customers page (Customers > All Customers)
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_client import BrowserClient


async def create_customer( #verified
    first_name: str,
    last_name: str,
    email: str,
    group: str,
    group_ref: str,
    fname_ref: str,
    lname_ref: str,
    email_ref: str,
    save_btn_ref: str
):
    """
    Create a new customer in Magento Admin.
    
    Args:
        first_name: Customer first name
        last_name: Customer last name
        email: Customer email address
        group: Customer group (e.g., "General", "Wholesale", "Premium Europe")
        group_ref: Ref for Group select dropdown
        fname_ref: Ref for First Name textbox
        lname_ref: Ref for Last Name textbox
        email_ref: Ref for Email textbox
        save_btn_ref: Ref for Save Customer button
    
    Returns:
        Snapshot of the page after creation
    """
    async with BrowserClient() as browser:
        print(f"👥 Selecting group: {group}")
        await browser.select_option(ref=group_ref, element_desc="Group select", value=group)
        
        print(f"📝 Entering first name: {first_name}")
        await browser.type_text(ref=fname_ref, text=first_name, element="First Name textbox")
        
        print(f"📝 Entering last name: {last_name}")
        await browser.type_text(ref=lname_ref, text=last_name, element="Last Name textbox")
        
        print(f"📧 Entering email: {email}")
        await browser.type_text(ref=email_ref, text=email, element="Email textbox")
        
        print(f"💾 Saving customer")
        await browser.click(ref=save_btn_ref, element="Save Customer button")
        
        await browser.wait_for_time(1)
        result = await browser.snapshot()
        print("✅ Customer created!")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Create a new customer in Magento Admin")
    parser.add_argument("first_name", help="Customer first name")
    parser.add_argument("last_name", help="Customer last name")
    parser.add_argument("email", help="Customer email address")
    parser.add_argument("group", help="Customer group (e.g., General, Wholesale)")
    parser.add_argument("group_ref", help="Element reference for Group select dropdown")
    parser.add_argument("fname_ref", help="Element reference for First Name textbox")
    parser.add_argument("lname_ref", help="Element reference for Last Name textbox")
    parser.add_argument("email_ref", help="Element reference for Email textbox")
    parser.add_argument("save_btn_ref", help="Element reference for Save Customer button")
    
    args = parser.parse_args()
    
    print(f"🚀 Create Customer Skill")
    print(f"   Name: {args.first_name} {args.last_name}")
    print(f"   Email: {args.email}")
    print(f"   Group: {args.group}")
    print("-" * 40)
    
    result = asyncio.run(create_customer(
        args.first_name,
        args.last_name,
        args.email,
        args.group,
        args.group_ref,
        args.fname_ref,
        args.lname_ref,
        args.email_ref,
        args.save_btn_ref
    ))
    
    if result:
        print(f"\n📄 Page snapshot:\n{result}")


if __name__ == "__main__":
    main()
