#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shopping Admin Skills Debug/Test Script
=========================================

This script helps you test each skill interactively to verify they work correctly.

Usage:
    python test_skills.py

Prerequisites:
    1. Start browser server first: python browser_server.py
    2. Make sure Magento Admin is accessible at http://localhost:7780/admin
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser_client import BrowserClient, is_server_running


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str, details: str = None):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status}: {message}")
    if details:
        preview = details[:500] + "..." if len(details) > 500 else details
        print(f"   Details: {preview}")


async def test_admin_login():
    """Test admin_login skill."""
    print_header("Testing: admin_login.py")
    
    try:
        from admin_login import admin_login
        result = await admin_login()
        
        # Check if login was successful by looking for Dashboard in snapshot
        if result and ("Dashboard" in result or "dashboard" in result.lower()):
            print_result(True, "Admin login successful", result)
            return True
        else:
            print_result(False, "Login may have failed - Dashboard not found in snapshot", result)
            return False
    except Exception as e:
        print_result(False, f"Exception during login: {e}")
        return False


async def test_read_dashboard():
    """Test read_dashboard skill."""
    print_header("Testing: read_dashboard.py")
    
    try:
        from read_dashboard import dashboard_reader
        result = await dashboard_reader("all")
        
        if result:
            # Look for typical dashboard elements
            has_bestsellers = "bestseller" in result.lower() or "Bestseller" in result
            has_revenue = "revenue" in result.lower() or "Revenue" in result
            
            if has_bestsellers or has_revenue:
                print_result(True, "Dashboard read successful", result)
                return True
            else:
                print_result(False, "Dashboard elements not found", result)
                return False
        else:
            print_result(False, "No result returned")
            return False
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False


async def test_search_products():
    """Test search_products skill."""
    print_header("Testing: search_products.py")
    
    try:
        from search_products import search_products
        result = await search_products("name", "Yoga")
        
        if result:
            print_result(True, "Product search executed", result)
            return True
        else:
            print_result(False, "No result returned")
            return False
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False


async def test_search_customer():
    """Test search_customer skill."""
    print_header("Testing: search_customer.py")
    
    try:
        from search_customer import search_customer
        result = await search_customer("name", "Sarah")
        
        if result:
            print_result(True, "Customer search executed", result)
            return True
        else:
            print_result(False, "No result returned")
            return False
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False


async def test_search_orders():
    """Test search_orders skill."""
    print_header("Testing: search_orders.py")
    
    try:
        from search_orders import search_orders
        result = await search_orders("status", "Pending")
        
        if result:
            print_result(True, "Order search executed", result)
            return True
        else:
            print_result(False, "No result returned")
            return False
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False


async def test_create_customer():
    """Test create_customer skill (interactive - requires confirmation)."""
    print_header("Testing: create_customer.py")
    print("⚠️  This test will CREATE a real customer in the database!")
    print("   Test customer: Test User, test.debug@example.com")
    
    confirm = input("   Do you want to proceed? (y/N): ").strip().lower()
    if confirm != 'y':
        print("   Skipped create_customer test")
        return None
    
    try:
        from create_customer import create_customer
        
        # First navigate to All Customers page
        async with BrowserClient() as browser:
            await browser.click(ref="e17", element="Customers menu")
            await browser.wait_for_time(1)
            await browser.click(ref="e182", element="All Customers link")
            await browser.wait_for_time(2)
        
        # Now create customer
        result = await create_customer(
            first_name="TestDebug",
            last_name="User",
            email=f"test.debug.{int(asyncio.get_event_loop().time())}@example.com",
            group="General"
        )
        
        if result:
            print_result(True, "Customer creation executed", result)
            return True
        else:
            print_result(False, "No result returned")
            return False
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False


async def reset_browser():
    """Reset browser state between tests."""
    print("\n🔄 Resetting browser state...")
    try:
        async with BrowserClient() as browser:
            await browser.navigate("about:blank")
            await browser.wait_for_time(1)
        print("   Reset complete")
    except Exception as e:
        print(f"   Reset warning: {e}")


async def run_all_tests():
    """Run all skill tests."""
    print_header("SHOPPING ADMIN SKILLS TEST SUITE")
    print("\nThis will test each skill sequentially.")
    print("Make sure browser_server.py is running!\n")
    
    if not is_server_running():
        print("❌ ERROR: Browser server is not running!")
        print("   Please start it with: python browser_server.py")
        return
    
    results = {}
    
    # Test 1: Admin Login (required for other tests)
    results['admin_login'] = await test_admin_login()
    if not results['admin_login']:
        print("\n⚠️  Login failed, skipping remaining tests")
        return results
    
    # Test 2: Read Dashboard
    results['read_dashboard'] = await test_read_dashboard()
    await reset_browser()
    
    # Re-login for next tests
    from admin_login import admin_login
    await admin_login()
    
    # Test 3: Search Products
    results['search_products'] = await test_search_products()
    await reset_browser()
    await admin_login()
    
    # Test 4: Search Customer
    results['search_customer'] = await test_search_customer()
    await reset_browser()
    await admin_login()
    
    # Test 5: Search Orders
    results['search_orders'] = await test_search_orders()
    await reset_browser()
    await admin_login()
    
    # Test 6: Create Customer (optional, requires confirmation)
    results['create_customer'] = await test_create_customer()
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for name, result in results.items():
        status = "✅" if result is True else ("❌" if result is False else "⏭️")
        print(f"  {status} {name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    return results


async def run_single_test(test_name: str):
    """Run a single test by name."""
    test_map = {
        'login': test_admin_login,
        'admin_login': test_admin_login,
        'dashboard': test_read_dashboard,
        'read_dashboard': test_read_dashboard,
        'products': test_search_products,
        'search_products': test_search_products,
        'customer': test_search_customer,
        'search_customer': test_search_customer,
        'orders': test_search_orders,
        'search_orders': test_search_orders,
        'create': test_create_customer,
        'create_customer': test_create_customer,
    }
    
    if test_name not in test_map:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {list(test_map.keys())}")
        return
    
    if not is_server_running():
        print("❌ ERROR: Browser server is not running!")
        return
    
    # Login first if not testing login
    if test_name not in ['login', 'admin_login']:
        print("First logging in...")
        await test_admin_login()
    
    await test_map[test_name]()


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║          Shopping Admin Skills - Debug Tool                ║
╠════════════════════════════════════════════════════════════╣
║  Usage:                                                    ║
║    python test_skills.py          - Run all tests          ║
║    python test_skills.py login    - Test login only        ║
║    python test_skills.py dashboard - Test dashboard only   ║
║    python test_skills.py products  - Test product search   ║
║    python test_skills.py customer  - Test customer search  ║
║    python test_skills.py orders    - Test order search     ║
║    python test_skills.py create    - Test create customer  ║
╚════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        asyncio.run(run_single_test(test_name))
    else:
        asyncio.run(run_all_tests())


if __name__ == "__main__":

    import debugpy
    debugpy.listen(("localhost", 5678))
    print("⏳ 等待调试器附加...")
    debugpy.wait_for_client()
    print("🚀 调试器已附加！继续执行...")
    main()
