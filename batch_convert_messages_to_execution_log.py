#!/usr/bin/env python3
"""
Batch convert messages.json files to execution.log format

Usage:
    python batch_convert_messages_to_execution_log.py <root_directory>
    
Example:
    python batch_convert_messages_to_execution_log.py /path/to/traj/folder
    
This script recursively traverses the specified directory, finds all folders
containing messages.json but no execution.log, and generates execution.log files for them.
"""

import json
import os
import sys
from pathlib import Path


def extract_tool_info_from_message(msg):
    """Extract tool call information from a message"""
    if msg.get("type") == "function_call":
        # Tool call
        name = msg.get("name", "")
        arguments = msg.get("arguments", "")
        return {
            "type": "tool_call",
            "name": name,
            "arguments": arguments
        }
    elif msg.get("type") == "function_call_output":
        # Tool output
        output = msg.get("output", "")
        return {
            "type": "tool_output",
            "output": output
        }
    return None


def parse_tool_call(tool_info):
    """Parse tool call and generate execution log format"""
    if tool_info["type"] == "tool_call":
        name = tool_info["name"]
        arguments = tool_info["arguments"]
        
        # Try to parse JSON arguments, use compact format (no spaces)
        try:
            args_dict = json.loads(arguments)
            args_str = json.dumps(args_dict, ensure_ascii=False, separators=(',', ':'))
        except:
            args_str = arguments
            
        return f"| {name} {args_str}"
    return None


def convert_messages_to_execution_log(messages):
    """Convert messages list to execution log format"""
    lines = []
    
    # First add tool list (if available)
    # This part can be adjusted based on actual needs
    
    # Find the first user message as task description
    task_description = None
    for msg in messages:
        if msg.get("role") == "user" and msg.get("content"):
            task_description = msg["content"]
            break
    
    # Don't add execution log header, start with tool calls directly
    # lines.append("===== Execution Logs =====")
    
    if task_description:
        # Optionally add task description
        # lines.append(task_description)
        pass
    
    # Process all messages
    assistant_text_buffer = []
    
    for i, msg in enumerate(messages):
        role = msg.get("role", "")
        content = msg.get("content", "")
        msg_type = msg.get("type", "")
        
        # Skip the first user message (task description)
        if i == 0 and role == "user":
            continue
            
        # Process assistant text content
        if role == "assistant" and content and msg_type != "function_call":
            # content can be a string or list
            if isinstance(content, list):
                # If it's a list, extract text fields
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        assistant_text_buffer.append(item["text"])
            elif isinstance(content, str):
                assistant_text_buffer.append(content)
        
        # Process tool calls
        if msg_type == "function_call":
            # If there's buffered assistant text, output it first
            if assistant_text_buffer:
                lines.append(" ".join(assistant_text_buffer))
                assistant_text_buffer = []
            
            tool_info = extract_tool_info_from_message(msg)
            if tool_info:
                tool_call_line = parse_tool_call(tool_info)
                if tool_call_line:
                    # Add empty line separator
                    if lines:
                        lines.append("")
                    lines.append(tool_call_line)
        
        # Tool output usually doesn't need to be shown in execution.log
        # If needed, uncomment the following code
        # elif msg_type == "function_call_output":
        #     pass
    
    # Output remaining assistant text
    if assistant_text_buffer:
        lines.append(" ".join(assistant_text_buffer))
    
    return "\n".join(lines)


def process_folder(folder_path, skip_existing=True):
    """Process folder, read messages.json and generate execution.log"""
    folder = Path(folder_path)
    
    messages_file = folder / "messages.json"
    execution_log_file = folder / "execution.log"
    
    # Check if should skip
    if skip_existing and execution_log_file.exists():
        return None, "execution.log already exists, skipping"
    
    if not messages_file.exists():
        return None, "messages.json not found"
    
    # Read messages.json
    try:
        with open(messages_file, 'r', encoding='utf-8') as f:
            messages = json.load(f)
    except Exception as e:
        return False, f"Failed to read messages.json: {e}"
    
    # Convert to execution log format
    try:
        execution_log = convert_messages_to_execution_log(messages)
    except Exception as e:
        return False, f"Conversion failed: {e}"
    
    # Write execution.log
    try:
        with open(execution_log_file, 'w', encoding='utf-8') as f:
            f.write(execution_log)
        return True, f"Successfully generated, {len(execution_log.splitlines())} lines"
    except Exception as e:
        return False, f"Failed to write execution.log: {e}"


def find_and_process_folders(root_dir, skip_existing=True):
    """Recursively find and process all folders containing messages.json"""
    root = Path(root_dir)
    
    if not root.exists():
        print(f"Error: Directory does not exist: {root_dir}")
        return
    
    # Statistics
    total_found = 0
    total_processed = 0
    total_skipped = 0
    total_failed = 0
    
    # Recursively traverse all directories
    for messages_file in root.rglob("messages.json"):
        folder = messages_file.parent
        total_found += 1
        
        # Process folder
        result, message = process_folder(folder, skip_existing)
        
        if result is True:
            total_processed += 1
            print(f"✓ {folder.relative_to(root)}: {message}")
        elif result is False:
            total_failed += 1
            print(f"✗ {folder.relative_to(root)}: {message}")
        else:  # result is None
            total_skipped += 1
            if not skip_existing:  # Only show when not skipping
                print(f"- {folder.relative_to(root)}: {message}")
    
    # Output statistics
    print("\n" + "="*60)
    print(f"Total found: {total_found} folders")
    print(f"Successfully processed: {total_processed}")
    print(f"Skipped: {total_skipped}")
    print(f"Failed: {total_failed}")
    print("="*60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_convert_messages_to_execution_log.py <root_directory> [--force]")
        print("Example: python batch_convert_messages_to_execution_log.py /path/to/traj/folder")
        print("\nOptions:")
        print("  --force    Force overwrite existing execution.log files")
        sys.exit(1)
    
    root_dir = sys.argv[1]
    skip_existing = "--force" not in sys.argv
    
    if not skip_existing:
        print("Note: Will overwrite existing execution.log files\n")
    
    find_and_process_folders(root_dir, skip_existing)


if __name__ == "__main__":
    main()
