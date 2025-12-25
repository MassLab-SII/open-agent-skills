#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Login Skill
==================

Login to the Magento Admin panel with provided credentials.

Usage:
    python admin_login.py <admin_url> <username> <password> <username_ref> <password_ref> <signin_ref>

Example:
    python admin_login.py http://localhost:7780/admin admin admin1234 e15 e20 e23
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_client import BrowserClient


async def admin_login( #verified
    admin_url: str,
    username: str,
    password: str,
    username_ref: str,
    password_ref: str,
    signin_ref: str
):
    """
    Login to Magento Admin panel.
    
    Args:
        admin_url: Admin panel URL
        username: Admin username
        password: Admin password
        username_ref: Ref for username textbox
        password_ref: Ref for password textbox
        signin_ref: Ref for Sign in button
    
    Returns:
        Snapshot of the page after login
    """
    async with BrowserClient() as browser:
        print(f"📍 Navigating to {admin_url}")
        await browser.navigate(admin_url)
        await browser.wait_for_time(1)
        
        print(f"👤 Entering username: {username}")
        await browser.type_text(ref=username_ref, text=username, element="Username textbox")
        
        print(f"🔑 Entering password")
        await browser.type_text(ref=password_ref, text=password, element="Password textbox")
        
        print(f"🔓 Clicking Sign in")
        await browser.click(ref=signin_ref, element="Sign in button")
        
        await browser.wait_for_time(1)
        result = await browser.snapshot()
        print("✅ Login complete!")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Login to Magento Admin panel")
    parser.add_argument("admin_url", help="Admin panel URL (e.g., http://localhost:7780/admin)")
    parser.add_argument("username", help="Admin username")
    parser.add_argument("password", help="Admin password")
    parser.add_argument("username_ref", help="Element reference for username textbox")
    parser.add_argument("password_ref", help="Element reference for password textbox")
    parser.add_argument("signin_ref", help="Element reference for Sign in button")
    
    args = parser.parse_args()
    
    print(f"🚀 Admin Login Skill")
    print(f"   URL: {args.admin_url}")
    print(f"   User: {args.username}")
    print("-" * 40)
    
    result = asyncio.run(admin_login(
        args.admin_url,
        args.username,
        args.password,
        args.username_ref,
        args.password_ref,
        args.signin_ref
    ))
    
    if result:
        print(f"\n📄 Page snapshot:\n{result}")


if __name__ == "__main__":
    main()
