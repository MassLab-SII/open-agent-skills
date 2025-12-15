#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fill Shipping Information at Checkout
======================================

This skill fills in the complete shipping information form during checkout.
Assumes you are already on the checkout page.

Usage:
    python fill_shipping_info.py <email> <first_name> <last_name> <street> <country> <state> <city> <zipcode> <phone> <email_ref> <fname_ref> <lname_ref> <street_ref> <country_ref> <state_ref> <city_ref> <zip_ref> <phone_ref>

Example:
    python fill_shipping_info.py test.buyer@example.com Alice Johnson "456 Oak Avenue" "United States" California "San Francisco" 94102 415-555-0123 e33 e46 e51 e65 e75 e80 e85 e90 e95
"""

import asyncio
import argparse
from utils import BrowserTools


async def fill_shipping_info(
    email: str,
    first_name: str,
    last_name: str,
    street: str,
    country: str,
    state: str,
    city: str,
    zipcode: str,
    phone: str,
    email_ref: str,
    fname_ref: str,
    lname_ref: str,
    street_ref: str,
    country_ref: str,
    state_ref: str,
    city_ref: str,
    zip_ref: str,
    phone_ref: str
):
    """
    Fill shipping information form at checkout.
    
    Args:
        email: Email address
        first_name: First name
        last_name: Last name
        street: Street address
        country: Country name
        state: State/Province name
        city: City name
        zipcode: Zip/Postal code
        phone: Phone number
        email_ref: Element reference for Email field
        fname_ref: Element reference for First Name field
        lname_ref: Element reference for Last Name field
        street_ref: Element reference for Street Address field
        country_ref: Element reference for Country dropdown
        state_ref: Element reference for State dropdown
        city_ref: Element reference for City field
        zip_ref: Element reference for Zip/Postal Code field
        phone_ref: Element reference for Phone field
        
    Note:
        This assumes you are already on the checkout page after clicking "Proceed to Checkout".
    """
    async with BrowserTools() as browser:
        print("Filling shipping information...")
        
        # Fill email
        print(f"  Email: {email}")
        await browser.type_text(ref=email_ref, text=email, element="Email Address*")
        
        # Fill name
        print(f"  Name: {first_name} {last_name}")
        await browser.type_text(ref=fname_ref, text=first_name, element="First Name*")
        await browser.type_text(ref=lname_ref, text=last_name, element="Last Name*")
        
        # Fill address
        print(f"  Address: {street}, {city}, {state} {zipcode}")
        await browser.type_text(ref=street_ref, text=street, element="Street Address: Line 1")
        
        # Select country
        print(f"  Country: {country}")
        await browser.select_option(ref=country_ref, element_desc="Country*", value=country)
        
        # Select state
        print(f"  State: {state}")
        await browser.select_option(ref=state_ref, element_desc="State/Province*", value=state)
        
        # Fill city
        await browser.type_text(ref=city_ref, text=city, element="City*")
        
        # Fill zipcode
        await browser.type_text(ref=zip_ref, text=zipcode, element="Zip/Postal Code*")
        
        # Fill phone
        print(f"  Phone: {phone}")
        await browser.type_text(ref=phone_ref, text=phone, element="Phone Number*")
        
        print("✓ Shipping information filled successfully!")


def main():
    parser = argparse.ArgumentParser(description="Fill shipping information at checkout")
    parser.add_argument("email", help="Email address")
    parser.add_argument("first_name", help="First name")
    parser.add_argument("last_name", help="Last name")
    parser.add_argument("street", help="Street address")
    parser.add_argument("country", help="Country name")
    parser.add_argument("state", help="State/Province name")
    parser.add_argument("city", help="City name")
    parser.add_argument("zipcode", help="Zip/Postal code")
    parser.add_argument("phone", help="Phone number")
    parser.add_argument("email_ref", help="Element reference for Email field")
    parser.add_argument("fname_ref", help="Element reference for First Name field")
    parser.add_argument("lname_ref", help="Element reference for Last Name field")
    parser.add_argument("street_ref", help="Element reference for Street Address field")
    parser.add_argument("country_ref", help="Element reference for Country dropdown")
    parser.add_argument("state_ref", help="Element reference for State dropdown")
    parser.add_argument("city_ref", help="Element reference for City field")
    parser.add_argument("zip_ref", help="Element reference for Zip/Postal Code field")
    parser.add_argument("phone_ref", help="Element reference for Phone field")
    
    args = parser.parse_args()
    
    asyncio.run(fill_shipping_info(
        args.email,
        args.first_name,
        args.last_name,
        args.street,
        args.country,
        args.state,
        args.city,
        args.zipcode,
        args.phone,
        args.email_ref,
        args.fname_ref,
        args.lname_ref,
        args.street_ref,
        args.country_ref,
        args.state_ref,
        args.city_ref,
        args.zip_ref,
        args.phone_ref
    ))


if __name__ == "__main__":
    main()

