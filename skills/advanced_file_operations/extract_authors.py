#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Authors Tool
=====================

Extract authors from HTML papers using <meta name="citation_author"> tags.
"""

import argparse
import os
import re
import sys


def _extract_authors_from_file(filepath: str) -> list[str]:
    """
    Extract author names from citation_author meta tags in a single HTML file.
    
    Args:
        filepath: Path to HTML file
        
    Returns:
        List of author names
    """
    authors = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all citation_author meta tags
        # Pattern: <meta name="citation_author" content="..."/>
        pattern = r'<meta\s+name=["\']citation_author["\']\s+content=["\']([^"\']+)["\'][^>]*/?\\s*>'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        # Clean up author names (decode HTML entities)
        for author in matches:
            # Decode common HTML entities
            author = author.replace('&#39;', "'")
            author = author.replace('&quot;', '"')
            author = author.replace('&amp;', '&')
            author = author.replace('&lt;', '<')
            author = author.replace('&gt;', '>')
            authors.append(author)
            
    except Exception as e:
        print(f"Warning: Could not process {filepath}: {e}", file=sys.stderr)
    
    return authors


def extract_authors_from_html(directory: str) -> list[dict]:
    """
    Extract authors from all HTML files in a directory.
    
    Args:
        directory: Path to the directory containing HTML papers
        
    Returns:
        List of dicts with 'filename' and 'authors' keys
    """
    results = []
    
    for filename in sorted(os.listdir(directory)):
        if not filename.lower().endswith('.html'):
            continue
        
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
        
        authors = _extract_authors_from_file(filepath)
        if authors:
            results.append({
                'filename': filename,
                'authors': authors
            })
    
    # Print results for model context
    total_authors = sum(len(r['authors']) for r in results)
    print(f"Scanned {len(results)} HTML files, extracted {total_authors} authors total:")
    for result in results:
        print(f"  {result['filename']}: {len(result['authors'])} authors")
        for author in result['authors']:
            print(f"    - {author}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Extract authors from HTML papers.'
    )
    parser.add_argument(
        'directory',
        help='Path to the directory containing HTML papers'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path (default: print to stdout)'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path if relative
    directory = os.path.abspath(args.directory)
    
    # Validate directory exists
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Extract authors (function already prints results)
    results = extract_authors_from_html(directory)
    
    # Generate output file if requested
    if args.output:
        output_lines = []
        for result in results:
            output_lines.append(f"File: {result['filename']}")
            output_lines.append(f"Authors ({len(result['authors'])}):")
            for author in result['authors']:
                output_lines.append(f"  - {author}")
            output_lines.append("")
        
        output_text = '\n'.join(output_lines)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"\nCreated: {args.output}")


if __name__ == '__main__':
    main()
