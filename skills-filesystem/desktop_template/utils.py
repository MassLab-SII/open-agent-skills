#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Filesystem Tools Wrapper
=============================

This module provides a high-level wrapper around MCP filesystem server tools.
It simplifies common file operations and makes them reusable across different skills.

"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Optional, Tuple
from datetime import datetime

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


class FileSystemTools:
    """
    High-level wrapper for MCP filesystem tools.
    
    This class provides convenient methods for common file operations using the
    MCP filesystem server.
    """
    
    def __init__(self, base_directory: str, timeout: int = 120):
        """
        Initialize the filesystem tools.
        
        Args:
            base_directory: Base directory for file operations (allowed directory)
            timeout: Timeout for MCP operations in seconds
        """
        self.base_directory = base_directory
        self.timeout = timeout
        self.mcp_server = MCPStdioServer(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", base_directory],
            timeout=timeout
        )
    
    async def __aenter__(self):
        """Enter async context manager"""
        await self.mcp_server.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context manager"""
        await self.mcp_server.__aexit__(exc_type, exc, tb)
    
    # ==================== File Reading Tools ====================
    
    async def read_text_file(self, path: str, head: Optional[int] = None, tail: Optional[int] = None) -> Optional[str]: #verified
        """
        Read the complete contents of a text file.
        
        Args:
            path: Path to the file (relative to base_directory or absolute)
            head: Read only the first N lines
            tail: Read only the last N lines
            
        Returns:
            File contents as string, or None if error
        """
        try:
            args = {"path": path}
            if head is not None:
                args["head"] = head
            if tail is not None:
                args["tail"] = tail
                
            result = await self.mcp_server.call_tool("read_text_file", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
        except Exception as e:
            print(f"Error reading file {path}: {e}")
        return None
    
    async def read_multiple_files(self, paths: List[str]) -> Dict[str, str]: #verified
        """
        Read multiple files simultaneously.
        
        Args:
            paths: List of file paths to read
            
        Returns:
            Dictionary mapping file paths to their contents
        """
        try:
            result = await self.mcp_server.call_tool(
                "read_multiple_files",
                {"paths": paths}
            )
            
            files_content = {}
            content = result.get('content', [])
            if content and len(content) > 0:
                text = content[0].get('text', '')
                # Parse the output to extract file contents
                # This is a simplified parser - adjust based on actual output format
                files_content = {"raw": text}
            
            return files_content
        except Exception as e:
            print(f"Error reading multiple files: {e}")
            return {}
    
    # ==================== File Writing Tools ====================
    
    async def write_file(self, path: str, content: str) -> bool: #verified
        """
        Create a new file or overwrite an existing file.
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.mcp_server.call_tool(
                "write_file",
                {"path": path, "content": content}
            )
            return True
        except Exception as e:
            print(f"Error writing file {path}: {e}")
            return False
    
    async def edit_file(self, path: str, edits: List[Dict]) -> bool: #verified
        """
        Make line-based edits to a text file.
        
        Args:
            path: Path to the file
            edits: List of edit operations
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.mcp_server.call_tool(
                "edit_file",
                {"path": path, "edits": edits}
            )
            return True
        except Exception as e:
            print(f"Error editing file {path}: {e}")
            return False
    
    # ==================== Directory Tools ====================
    
    async def create_directory(self, path: str) -> bool: #verified
        """
        Create a new directory or ensure it exists.
        Supports recursive creation of nested directories (like mkdir -p).
        
        Args:
            path: Path to the directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # MCP's create_directory doesn't support recursive creation
            # We need to create parent directories first
            
            # Normalize the path
            path = os.path.normpath(path)
            
            # Get all parent directories that need to be created
            parts = []
            current = path
            while current and current != self.base_directory:
                parts.append(current)
                parent = os.path.dirname(current)
                if parent == current:  # Reached root
                    break
                current = parent
            
            # Reverse to create from parent to child
            parts.reverse()
            
            # Create each directory in sequence
            for dir_path in parts:
                try:
                    await self.mcp_server.call_tool(
                        "create_directory",
                        {"path": dir_path}
                    )
                except Exception as e:
                    # Ignore errors if directory already exists
                    error_msg = str(e).lower()
                    if 'exist' not in error_msg:
                        # Only print if it's not an "already exists" error
                        pass
            
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False
    
    async def list_directory(self, path: str) -> Tuple[List[str], List[str]]: #verified
        """
        List all files and directories in a path.
        
        Args:
            path: Path to the directory
            
        Returns:
            Tuple of (files, directories) lists
        """
        try:
            result = await self.mcp_server.call_tool(
                "list_directory",
                {"path": path}
            )
            
            structured_content = result.get('structuredContent', {})
            content_text = structured_content.get('content', '')
            
            files = []
            directories = []
            
            for line in content_text.split('\n'):
                line = line.strip()
                if line.startswith('[FILE]'):
                    filename = line[7:].strip()
                    if filename:
                        files.append(filename)
                elif line.startswith('[DIR]'):
                    dirname = line[6:].strip()
                    if dirname:
                        directories.append(dirname)
            
            return files, directories
            
        except Exception as e:
            print(f"Error listing directory {path}: {e}")
            return [], []
    
    async def list_files(self, path: Optional[str] = None, exclude_hidden: bool = True) -> List[str]:  #verified
        """
        List only files in a directory (convenience method).
        
        Args:
            path: Path to the directory (defaults to base_directory)
            exclude_hidden: Exclude hidden files like .DS_Store
            
        Returns:
            List of file names
        """
        if path is None:
            path = self.base_directory
        
        files, _ = await self.list_directory(path)
        
        if exclude_hidden:
            files = [f for f in files if not f.startswith('.')]
        
        return files
    
    # ==================== File Operations ====================
    
    async def move_file(self, source: str, destination: str) -> bool: #verified
        """
        Move or rename a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.mcp_server.call_tool(
                "move_file",
                {"source": source, "destination": destination}
            )
            return True
        except Exception as e:
            print(f"Error moving {source} to {destination}: {e}")
            return False
    
    async def search_files(self, pattern: str, base_path: Optional[str] = None) -> List[str]: #verified
        """
        Search for files matching a pattern.
        
        Args:
            pattern: Glob pattern (e.g., '*.txt', '**/*.py')
            base_path: Base path for search (defaults to base_directory)
            
        Returns:
            List of matching file paths
        """
        try:
            args = {"pattern": pattern}
            if base_path:
                args["path"] = base_path
                
            result = await self.mcp_server.call_tool("search_files", args)
            
            content = result.get('content', [])
            if content and len(content) > 0:
                text = content[0].get('text', '')
                # Parse file paths from the result
                return [line.strip() for line in text.split('\n') if line.strip()]
                
        except Exception as e:
            print(f"Error searching files with pattern {pattern}: {e}")
            return []
    
    # ==================== File Information ====================
    
    async def get_file_info(self, path: str) -> Optional[Dict]: #verified
        """
        Get detailed metadata about a file or directory.
        
        Args:
            path: Path to the file or directory
            
        Returns:
            Dictionary with file metadata (size, created, modified, etc.)
        """
        try:
            result = await self.mcp_server.call_tool(
                "get_file_info",
                {"path": path}
            )
            
            content = result.get('content', [])
            if content and len(content) > 0:
                text = content[0].get('text', '')
                
                # Parse the text to extract metadata
                info = {}
                for line in text.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert specific fields
                        if key == 'size':
                            info['size'] = int(value)
                        elif key in ['created', 'modified', 'accessed']:
                            # Parse ISO format timestamp
                            try:
                                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                info[key] = dt
                                info[f'{key}_timestamp'] = dt.timestamp()
                            except:
                                info[key] = value
                        else:
                            info[key] = value
                
                return info
                
        except Exception as e:
            print(f"Error getting file info for {path}: {e}")
            return None
    
    async def get_file_size(self, path: str) -> Optional[int]: #verified
        """
        Get file size in bytes (convenience method).
        
        Args:
            path: Path to the file
            
        Returns:
            File size in bytes, or None if error
        """
        info = await self.get_file_info(path)
        return info.get('size') if info else None
    
    async def get_file_ctime(self, path: str) -> Optional[datetime]: #verified
        """
        Get file creation time (convenience method).
        
        Args:
            path: Path to the file
            
        Returns:
            Creation time as datetime, or None if error
        """
        info = await self.get_file_info(path)
        return info.get('created') if info else None
    
    async def get_file_mtime(self, path: str) -> Optional[datetime]: #verified
        """
        Get file modification time (convenience method).
        
        Args:
            path: Path to the file
            
        Returns:
            Modification time as datetime, or None if error
        """
        info = await self.get_file_info(path)
        return info.get('modified') if info else None
    
    # ==================== Batch Operations ====================
    
    async def get_files_info_batch(self, filenames: List[str], base_path: Optional[str] = None) -> Dict[str, Dict]: #verified
        """
        Get file information for multiple files in parallel.
        
        Args:
            filenames: List of file names
            base_path: Base path for files (defaults to base_directory)
            
        Returns:
            Dictionary mapping filenames to their info
        """
        if base_path is None:
            base_path = self.base_directory
        
        tasks = []
        for filename in filenames:
            file_path = os.path.join(base_path, filename)
            tasks.append(self._get_file_info_with_name(file_path, filename))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        files_info = {}
        for result in results:
            if isinstance(result, tuple):
                filename, info = result
                if info is not None:
                    files_info[filename] = info
        
        return files_info
    
    async def _get_file_info_with_name(self, path: str, filename: str) -> Tuple[str, Optional[Dict]]: #verified
        """Helper method for batch operations"""
        info = await self.get_file_info(path)
        return (filename, info)
    

