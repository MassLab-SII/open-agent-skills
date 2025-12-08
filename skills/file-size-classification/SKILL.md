---
name: file-size-classification
description: This skill classifies and organizes files into categorized subdirectories based on their file sizes. Use this when you need to organize files by size thresholds, separate large files from small ones, or create size-based file management structures.
---

# File Size Classification Skill

This skill classifies files into different subdirectories based on their file sizes, enabling size-threshold-based file organization and management.

## Example

```bash
# Using default thresholds (300 and 700 bytes)
python classify_files_by_size.py /path/to/directory

# Custom thresholds
python classify_files_by_size.py /path/to/directory --small 1024 --large 10240

# Custom category names
python classify_files_by_size.py /path/to/directory --small-category tiny --medium-category normal --large-category huge
```
