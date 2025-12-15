import os
import re
import json

ROOT_DIR = "/Users/enigma/Documents/ChuangZhi/mcpmark/results/exp_github/gpt-5__github/run-1"
OUTPUT_FILE = "github_tools.json"

def extract_tools():
    unique_tools = {}
    
    # Regex to capture ToolName and Description
    # Example: - ToolName: add_issue_comment             Description: Add a comment ...
    pattern = re.compile(r"-\s+ToolName:\s+(\w+)\s+Description:\s+(.+)")

    print(f"Scanning directory: {ROOT_DIR}")
    
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file == "execution.log":
                file_path = os.path.join(root, file)
                try:
                    # We only need to read the beginning where tools are listed usually
                    # But the log might be huge. The tools are usually printed at the start.
                    # Let's read line by line until we pass the tools section or hit a limit
                    with open(file_path, 'r', errors='ignore') as f:
                        lines_read = 0
                        for line in f:
                            lines_read += 1
                            match = pattern.search(line)
                            if match:
                                name = match.group(1).strip()
                                desc = match.group(2).strip()
                                if name not in unique_tools:
                                    unique_tools[name] = desc
                            
                            # If we see "===== Execution Logs =====", we can probably stop for this file
                            if "===== Execution Logs =====" in line:
                                break
                                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    print(f"Found {len(unique_tools)} unique tools.")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(unique_tools, f, indent=2)
        
    print(f"Saved tools to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_tools()
