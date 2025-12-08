#!/usr/bin/env python3
"""
File Size Classification Script
================================

This script classifies files in a directory into subdirectories based on their file sizes.
It uses the MCP filesystem server to perform file operations.

Usage:
    python classify_files_by_size.py <target_directory> [--small <bytes>] [--large <bytes>] 
                                      [--small-category <name>] [--medium-category <name>] [--large-category <name>]

Example:
    python classify_files_by_size.py /path/to/directory --small 300 --large 700
    python classify_files_by_size.py /path/to/directory --small 1024 --large 10240 --small-category tiny --medium-category normal --large-category huge
"""

import asyncio
import json
import os
import argparse
from pathlib import Path
from contextlib import AsyncExitStack
from typing import List, Dict, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPStdioServer:
    """Lightweight MCP Stdio Server wrapper"""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 120):
        self.params = StdioServerParameters(
            command=command, 
            args=args, 
            env={**os.environ, **(env or {})}
        )
        self.timeout = timeout
        self._stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None

    async def __aenter__(self):
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(self.params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call the specified MCP tool"""
        result = await asyncio.wait_for(
            self.session.call_tool(name, arguments), 
            timeout=self.timeout
        )
        return result.model_dump()


class FileSizeClassifier:
    """Classifier that organizes files by size thresholds"""
    
    def __init__(self, target_dir: str, small_threshold: int = 300, large_threshold: int = 700,
                 small_category: str = 'small_files', medium_category: str = 'medium_files', 
                 large_category: str = 'large_files'):
        """
        Initialize the classifier
        
        Args:
            target_dir: Target directory to classify files in
            small_threshold: Maximum size (bytes) for small files (exclusive)
            large_threshold: Minimum size (bytes) for large files (exclusive)
            small_category: Name for small files category directory (default: 'small_files')
            medium_category: Name for medium files category directory (default: 'medium_files')
            large_category: Name for large files category directory (default: 'large_files')
        """
        self.target_dir = target_dir
        self.small_threshold = small_threshold
        self.large_threshold = large_threshold
        self.small_category = small_category
        self.medium_category = medium_category
        self.large_category = large_category
        self.mcp_server = None
        
        # Category definitions
        self.categories = {
            small_category: lambda size: size < small_threshold,
            medium_category: lambda size: small_threshold <= size <= large_threshold,
            large_category: lambda size: size > large_threshold
        }
    
    async def classify_files(self):
        """Main classification workflow"""
        # Initialize MCP server
        self.mcp_server = MCPStdioServer(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", self.target_dir]
        )
        
        async with self.mcp_server:
            
            # Step 1: List all files in the directory
            print("Step 1: Listing files...")
            files = await self._list_files()
            print(f"Found {len(files)} files\n")
            
            if not files:
                print("No files to classify.")
                return
            
            # Step 2: Get file size information
            print("Step 2: Getting file size information...")
            file_sizes = await self._get_file_sizes(files)
            print(f"Retrieved size info for {len(file_sizes)} files\n")
            
            # Step 3: Create category directories
            print("Step 3: Creating category directories...")
            await self._create_category_directories()
            print("Category directories created\n")
            
            # Step 4: Classify and move files
            print("Step 4: Classifying and moving files...")
            classification_results = await self._move_files_to_categories(file_sizes)
            
            # Print summary
            # self._print_summary(classification_results)
    
    async def _list_files(self) -> List[str]:
        """List all files in the target directory"""
        try:
            result = await asyncio.wait_for(
                self.mcp_server.call_tool(
                    "list_directory",
                    {"path": self.target_dir}
                ),
                timeout=10
            )
            
            # Extract file names from structuredContent
            structured_content = result.get('structuredContent', {})
            content_text = structured_content.get('content', '')
            
            if not content_text:
                print("  No content found in directory listing")
                return []
            
            # Parse the content to extract file names
            files = []
            for line in content_text.split('\n'):
                line = line.strip()
                if line.startswith('[FILE]'):
                    # Extract filename after '[FILE] '
                    filename = line[7:].strip()  # Skip '[FILE] ' prefix
                    if filename:
                        files.append(filename)
            
            return files
            
        except Exception as e:
            print(f"  Error listing files: {e}")
            return []
    
    async def _get_file_sizes(self, files: List[str]) -> Dict[str, int]:
        """Get size information for all files"""
        file_sizes = {}
        
        # Create tasks for parallel execution
        tasks = []
        for filename in files:
            file_path = os.path.join(self.target_dir, filename)
            tasks.append(self._get_single_file_info(file_path, filename))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, tuple):
                filename, size = result
                if size is not None:
                    file_sizes[filename] = size
                    print(f"  {filename}: {size:,} bytes")
        
        return file_sizes
    
    async def _get_single_file_info(self, file_path: str, filename: str) -> Tuple[str, int]:
        """Get size information for a single file"""
        try:
            result = await asyncio.wait_for(
                self.mcp_server.call_tool(
                    "get_file_info",
                    {"path": file_path}
                ),
                timeout=10
            )
            
            # Extract size from content array
            content = result.get('content', [])
            if content and len(content) > 0:
                text = content[0].get('text', '')
                
                # Parse the text to find size
                for line in text.split('\n'):
                    line = line.strip()
                    if line.startswith('size:'):
                        # Extract size value after 'size: '
                        size_str = line[5:].strip()  # Skip 'size:' prefix
                        size = int(size_str)
                        return (filename, size)
                    
        except Exception as e:
            print(f"  Error getting info for {filename}: {e}")
        
        return (filename, None)
    
    async def _create_category_directories(self):
        """Create subdirectories for each category"""
        for category_name in self.categories.keys():
            category_path = os.path.join(self.target_dir, category_name)
            try:
                result = await self.mcp_server.call_tool(
                    "create_directory",
                    {"path": category_path}
                )
                print(f"  Created: {category_name}/")
            except Exception as e:
                print(f"  Error creating {category_name}: {e}")
    
    async def _move_files_to_categories(self, file_sizes: Dict[str, int]) -> Dict[str, List[Tuple[str, int]]]:
        """Move files to their appropriate category directories"""
        classification_results = {category: [] for category in self.categories.keys()}
        
        for filename, size in file_sizes.items():
            # Determine category
            category = self._determine_category(size)
            
            # Move file
            source_path = os.path.join(self.target_dir, filename)
            dest_path = os.path.join(self.target_dir, category, filename)
            
            try:
                result = await asyncio.wait_for(
                    self.mcp_server.call_tool(
                        "move_file",
                        {"source": source_path, "destination": dest_path}
                    ),
                    timeout=10
                )
                classification_results[category].append((filename, size))
                print(f"  Moved {filename} → {category}/")
            except Exception as e:
                # File might already be moved, check if it exists in destination
                print(f"  Note: {filename} - {e}")
                classification_results[category].append((filename, size))
        
        return classification_results
    
    def _determine_category(self, size: int) -> str:
        """Determine which category a file belongs to based on its size"""
        for category_name, condition in self.categories.items():
            if condition(size):
                return category_name
        return self.large_category  # Default fallback
    



async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Classify files in a directory by size',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default thresholds (300 and 700 bytes)
  python classify_files_by_size.py /path/to/directory
  
  # Custom thresholds
  python classify_files_by_size.py /path/to/directory --small 1024 --large 10240
  
  # For document management (1KB and 100KB)
  python classify_files_by_size.py /path/to/docs --small 1024 --large 102400
  
  # Custom category names
  python classify_files_by_size.py /path/to/directory --small-category tiny --medium-category normal --large-category huge
        """
    )
    
    parser.add_argument(
        'target_directory',
        help='Directory containing files to classify'
    )
    parser.add_argument(
        '--small',
        type=int,
        default=300,
        help='Maximum size for small files in bytes (default: 300)'
    )
    parser.add_argument(
        '--large',
        type=int,
        default=700,
        help='Minimum size for large files in bytes (default: 700)'
    )
    parser.add_argument(
        '--small-category',
        type=str,
        default='small_files',
        help='Name for small files category directory (default: small_files)'
    )
    parser.add_argument(
        '--medium-category',
        type=str,
        default='medium_files',
        help='Name for medium files category directory (default: medium_files)'
    )
    parser.add_argument(
        '--large-category',
        type=str,
        default='large_files',
        help='Name for large files category directory (default: large_files)'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.target_directory):
        print(f"Error: Directory '{args.target_directory}' does not exist")
        return
    
    # Validate thresholds
    if args.small >= args.large:
        print(f"Error: Small threshold ({args.small}) must be less than large threshold ({args.large})")
        return
    
    # Create classifier and run
    classifier = FileSizeClassifier(
        target_dir=args.target_directory,
        small_threshold=args.small,
        large_threshold=args.large,
        small_category=args.small_category,
        medium_category=args.medium_category,
        large_category=args.large_category
    )
    
    try:
        await classifier.classify_files()
    except Exception as e:
        print(f"\nError during classification: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

