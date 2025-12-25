#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sign Up Skill
==============

Create a new account on the Postmill/Reddit-like forum.

Usage:
    python sign_up.py <username> <password> <username_ref> <password_ref> <password_repeat_ref> <submit_ref>

Example:
    python sign_up.py "AIDataAnalyst2025" "SecurePass123!" e35 e43 e44 e54
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_client import BrowserClient


async def sign_up( 
    username: str,
    password: str,
    username_ref: str,
    password_ref: str,
    password_repeat_ref: str,
    submit_ref: str
):
    """
    Create a new account on the forum.
    
    Args:
        username: Desired username
        password: Desired password
        username_ref: Ref for username textbox
        password_ref: Ref for password textbox
        password_repeat_ref: Ref for password repeat textbox
        submit_ref: Ref for submit button
    
    Returns:
        Snapshot of the page after registration
    """
    async with BrowserClient() as browser:
        
        print(f"👤 Entering username: {username}")
        await browser.type_text(ref=username_ref, text=username, element="Username field")
        
        print(f"🔑 Entering password")
        await browser.type_text(ref=password_ref, text=password, element="Password field")
        
        print(f"🔑 Confirming password")
        await browser.type_text(ref=password_repeat_ref, text=password, element="Password repeat field")
        
        print(f"✅ Clicking Sign up button")
        await browser.click(ref=submit_ref, element="Sign up button")
        
        await browser.wait_for_time(1)
        result = await browser.snapshot()
        print("✅ Registration complete!")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Create a new account on the forum")
    parser.add_argument("username", help="Desired username")
    parser.add_argument("password", help="Desired password")
    parser.add_argument("username_ref", help="Element reference for username textbox")
    parser.add_argument("password_ref", help="Element reference for password textbox")
    parser.add_argument("password_repeat_ref", help="Element reference for password repeat textbox")
    parser.add_argument("submit_ref", help="Element reference for Sign up button")
    
    args = parser.parse_args()
    
    print(f"🚀 Sign Up Skill")
    print(f"   Username: {args.username}")
    print("-" * 40)
    
    result = asyncio.run(sign_up(
        args.username,
        args.password,
        args.username_ref,
        args.password_ref,
        args.password_repeat_ref,
        args.submit_ref
    ))
    
    if result:
        print(f"\n📄 Page snapshot:\n{result}")


if __name__ == "__main__":
    main()
