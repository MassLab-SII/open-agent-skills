#!/usr/bin/env python3
"""
Example Usage of FileSystemTools
=================================

This script demonstrates various ways to use the FileSystemTools wrapper.

"""

import asyncio
import os
from utils import FileSystemTools


async def example_basic_operations():
    """Example: Basic file operations"""
    print("=" * 60)
    print("Example 1: Basic File Operations")
    print("=" * 60)
    
    target_dir = "/Users/zhaoji/project/mcpmark/.mcpmark_backups/backup_filesystem_file_property_size_classification_82172/123"
    
    async with FileSystemTools(target_dir) as fs:
        # Create directory
        await fs.create_directory(target_dir)
        print(f"✓ Created directory: {target_dir}")
        
        # Write a file
        await fs.write_file(
            os.path.join(target_dir, "example111.txt"),
            "Hello, World!\nThis is a test file."
        )
        print("✓ Created file: example111.txt")
        
        # Read the file
        content = await fs.read_text_file(os.path.join(target_dir, "example111.txt"))
        print(f"✓ Read file content:\n{content}\n")
        
        # Get file info
        info = await fs.get_file_info(os.path.join(target_dir, "example111.txt"))
        print(f"✓ File info:")
        print(f"  - Size: {info.get('size')} bytes")
        print(f"  - Created: {info.get('created')}")
        print()


async def example_list_and_search():
    """Example: Listing and searching files"""
    print("=" * 60)
    print("Example 2: Listing and Searching Files")
    print("=" * 60)
    
    # Use current directory as example
    target_dir = os.path.dirname(os.path.abspath(__file__))
    
    async with FileSystemTools(target_dir) as fs:
        # List files
        files = await fs.list_files()
        print(f"✓ Found {len(files)} files:")
        for f in files[:5]:  # Show first 5
            print(f"  - {f}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
        print()
        
        # List with directories
        files, dirs = await fs.list_directory(target_dir)
        print(f"✓ Directory contains:")
        print(f"  - {len(files)} files")
        print(f"  - {len(dirs)} directories")
        print()


async def example_batch_operations():
    """Example: Batch operations for efficiency"""
    print("=" * 60)
    print("Example 3: Batch Operations")
    print("=" * 60)
    
    target_dir = os.path.dirname(os.path.abspath(__file__))
    
    async with FileSystemTools(target_dir) as fs:
        # Get all Python files
        files = await fs.list_files()
        py_files = [f for f in files if f.endswith('.py')]
        
        # Get info for all Python files in parallel
        print(f"✓ Getting info for {len(py_files)} Python files...")
        files_info = await fs.get_files_info_batch(py_files)
        
        # Show results
        total_size = sum(info.get('size', 0) for info in files_info.values())
        print(f"✓ Total size of Python files: {total_size:,} bytes")
        


async def example_file_organization():
    """Example: Simple move file operation"""
    print("=" * 60)
    print("Example 4: Move File")
    print("=" * 60)
    
    target_dir = "/Users/zhaoji/project/mcpmark/.mcpmark_backups/backup_filesystem_file_property_size_classification_82172"
    
    async with FileSystemTools(target_dir) as fs:
        # Move a file
        source = os.path.join(target_dir, "example111.txt")
        dest = os.path.join(target_dir, "example111_moved.txt")
        
        success = await fs.move_file(source, dest)
        if success:
            print(f"✓ Moved file from {source} to {dest}")
        else:
            print(f"✗ Failed to move file")
        
        print()



async def example_read_multiple_files():
    """Example: Read multiple files at once"""
    print("=" * 60)
    print("Example 6: Read Multiple Files")
    print("=" * 60)
    
    target_dir = os.path.dirname(os.path.abspath(__file__))
    
    async with FileSystemTools(target_dir) as fs:
        # Get list of Python files
        files = await fs.list_files()
        py_files = [os.path.join(target_dir, f) for f in files if f.endswith('.py')][:3]
        
        if py_files:
            print(f"✓ Reading {len(py_files)} Python files simultaneously...")
            contents = await fs.read_multiple_files(py_files)
            print(f"✓ Read {len(contents)} files")
            print(f"  Raw result keys: {list(contents.keys())}")
        
        print()


async def example_edit_file():
    """Example: Edit file with line-based operations"""
    print("=" * 60)
    print("Example 7: Edit File")
    print("=" * 60)
    
    target_dir = "/Users/zhaoji/project/mcpmark/.mcpmark_backups/backup_filesystem_file_property_size_classification_82172"
    
    async with FileSystemTools(target_dir) as fs:
        # Create a test file
        test_file = os.path.join(target_dir, "edit_test.txt")
        await fs.write_file(test_file, "Line 1\nLine 2\nLine 3\n")
        print(f"✓ Created test file: {test_file}")
        
        # Edit the file
        edits = [
            {"oldText": "Line 2", "newText": "Line 2 - Modified"}
        ]
        success = await fs.edit_file(test_file, edits)
        if success:
            print(f"✓ Edited file successfully")
            content = await fs.read_text_file(test_file)
            print(f"  New content:\n{content}")
        else:
            print(f"✗ Failed to edit file")
        
        print()



async def example_search_files():
    """Example: Search files with patterns"""
    print("=" * 60)
    print("Example 10: Search Files")
    print("=" * 60)
    
    target_dir = os.path.dirname(os.path.abspath(__file__))
    
    async with FileSystemTools(target_dir) as fs:
        # Search for Python files
        py_files = await fs.search_files("*.py", target_dir)
        print(f"✓ Found {len(py_files)} Python files:")
        for f in py_files[:5]:
            print(f"  - {f}")
        if len(py_files) > 5:
            print(f"  ... and {len(py_files) - 5} more")
        
        # Search for markdown files
        md_files = await fs.search_files("*.md", target_dir)
        print(f"✓ Found {len(md_files)} Markdown files:")
        for f in md_files:
            print(f"  - {f}")
        
        print()


async def example_file_metadata():
    """Example: Get file size, creation time, and modification time"""
    print("=" * 60)
    print("Example 11: File Metadata (Size, Ctime, Mtime)")
    print("=" * 60)
    
    target_dir = os.path.dirname(os.path.abspath(__file__))
    
    async with FileSystemTools(target_dir) as fs:
        files = await fs.list_files()
        
        if files:
            test_file = os.path.join(target_dir, files[0])
            
            # Get file size
            size = await fs.get_file_size(test_file)
            print(f"✓ File: {files[0]}")
            print(f"  Size: {size} bytes")
            
            # Get creation time
            ctime = await fs.get_file_ctime(test_file)
            print(f"  Created: {ctime}")
            
            # Get modification time
            mtime = await fs.get_file_mtime(test_file)
            print(f"  Modified: {mtime}")
        
        print()


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("FileSystemTools Usage Examples")
    print("=" * 60 + "\n")
    
    # try:
    #     await example_basic_operations()
    # except Exception as e:
    #     print(f"✗ Example 1 failed: {e}\n")
    
    # try:
    #     await example_list_and_search()
    # except Exception as e:
    #     print(f"✗ Example 2 failed: {e}\n")
    
    # try:
    #     await example_batch_operations()
    # except Exception as e:
    #     print(f"✗ Example 3 failed: {e}\n")
    
    # try:
    #     await example_file_organization()
    # except Exception as e:
    #     print(f"✗ Example 4 failed: {e}\n")
    
    
    # try:
    #     await example_read_multiple_files()
    # except Exception as e:
    #     print(f"✗ Example 6 failed: {e}\n")
    
    # try:
    #     await example_edit_file()
    # except Exception as e:
    #     print(f"✗ Example 7 failed: {e}\n")
    
    
    # try:
    #     await example_search_files()
    # except Exception as e:
    #     print(f"✗ Example 10 failed: {e}\n")
    
    # try:
    #     await example_file_metadata()
    # except Exception as e:
    #     print(f"✗ Example 11 failed: {e}\n")
    
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # import os
    # import debugpy
    # debugpy.listen(("localhost", 5678))
    # print("⏳ 等待调试器附加...")
    # debugpy.wait_for_client()
    # print("🚀 调试器已附加！继续执行...")
    asyncio.run(main())

