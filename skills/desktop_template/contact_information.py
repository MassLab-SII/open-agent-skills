#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contact Information Aggregator (Using utils.py)
===============================================

This script scans all files, extracts contact information, and consolidates it
into a CSV table. It also answers a reasoning question about a specific person.

Outputs:
- contact_info.csv
- answer.txt (answer to: What is Charlie Davis's job/profession?)
"""

import asyncio
import os
import argparse
import csv
import re
from typing import List, Dict, Set

from utils import FileSystemTools


class ContactAggregator:
    """Aggregate contact information from mixed files."""

    def __init__(self, target_dir: str,
                 output_csv: str = "contact_info.csv",
                 answer_file: str = "answer.txt"):
        self.target_dir = target_dir
        self.output_csv = output_csv
        self.answer_file = answer_file
        self.contacts: List[Dict[str, str]] = []
        self.all_fields: Set[str] = set(["Name", "Email", "Phone"])

    async def run(self):
        async with FileSystemTools(self.target_dir) as fs:
            print("Step 1: Scanning files...")
            paths = await fs.search_files("**/*")
            files = [p for p in paths if not p.endswith("/")]
            print(f"  Found {len(files)} files")

            # Extract contacts
            for file_path in files:
                content = await fs.read_text_file(file_path)
                if not content:
                    continue

                rel_path = os.path.relpath(file_path, self.target_dir)
                if rel_path.lower().endswith(".csv"):
                    self._parse_csv(content, rel_path)
                else:
                    self._parse_text(content, rel_path)

            # Step 2: Write CSV
            print("Step 2: Writing contact_info.csv...")
            csv_content = self._build_csv()
            await fs.write_file(os.path.join(self.target_dir, self.output_csv), csv_content)

            # Step 3: Answer reasoning question
            print("Step 3: Writing answer.txt...")
            answer = self._answer_question()
            await fs.write_file(os.path.join(self.target_dir, self.answer_file), answer)

            print("\nTask completed successfully!")
            print(f"Contacts saved to {self.output_csv}")
            print(f"Answer saved to {self.answer_file}")

    def _parse_csv(self, content: str, rel_path: str):
        """Parse CSV content and append contacts."""
        try:
            reader = csv.DictReader(content.splitlines())
            for row in reader:
                contact = {}
                # Normalize keys (strip spaces)
                for k, v in row.items():
                    key = k.strip() if k else ""
                    if not key:
                        continue
                    value = v.strip() if isinstance(v, str) else ""
                    if value == "":
                        continue
                    contact[key] = value
                if contact:
                    # Ensure Name/Email/Phone keys exist (even empty)
                    contact.setdefault("Name", contact.get("name", ""))
                    contact.setdefault("Email", contact.get("email", ""))
                    contact.setdefault("Phone", contact.get("phone", ""))
                    self.contacts.append(contact)
                    self.all_fields.update(contact.keys())
        except Exception:
            return

    def _parse_text(self, content: str, rel_path: str):
        """Parse plain text heuristically for contact info."""
        # Heuristic patterns
        email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"
        phone_pattern = r"(?:\\+?\\d[\\d\\-\\s]{6,}\\d)"

        emails = re.findall(email_pattern, content)
        phones = re.findall(phone_pattern, content)

        if emails or phones:
            contact = {
                "Name": os.path.basename(rel_path),
                "Email": emails[0] if emails else "",
                "Phone": phones[0] if phones else ""
            }
            self.contacts.append(contact)
            self.all_fields.update(contact.keys())

    def _build_csv(self) -> str:
        """Construct CSV string from collected contacts."""
        # Order fields: Name, Email, Phone, others alphabetically
        other_fields = sorted(f for f in self.all_fields if f not in ["Name", "Email", "Phone"])
        headers = ["Name", "Email", "Phone"] + other_fields

        rows = []
        rows.append(",".join(headers))
        for contact in self.contacts:
            row = []
            for h in headers:
                row.append(contact.get(h, ""))
            rows.append(",".join(row))

        return "\n".join(rows)

    def _answer_question(self) -> str:
        """Answer: What is Charlie Davis's job/profession?"""
        for contact in self.contacts:
            name = contact.get("Name", "").strip()
            if name.lower() == "charlie davis":
                # Try to infer from Status/Industry/Category
                for key in ["Status", "Industry", "Category", "Profession", "Job"]:
                    val = contact.get(key, "").strip()
                    if val:
                        return val
                # If nothing found, return Unknown
                return "Unknown"
        return "Unknown"


async def main():
    parser = argparse.ArgumentParser(
        description="Aggregate contact information into a CSV table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python contact_information.py /path/to/desktop_template
        """
    )
    parser.add_argument("target_directory", help="Desktop root directory")
    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return

    agg = ContactAggregator(target_dir=args.target_directory)
    try:
        await agg.run()
    except Exception as e:
        print(f"\nError during contact aggregation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

