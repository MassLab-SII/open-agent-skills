---
name: file-classification
description: This skill classifies and organizes files into categorized subdirectories based on their file sizes or creation times. Use this when you need to organize files by size thresholds, separate large files from small ones, or organize files by their dates.
---

# File Classification Skill

This skill provides two types of file classification:
1. **Size-based classification**: Organize files by size thresholds
2. **Time-based classification**: Organize files by creation time (MM/DD structure)

## File Size Classification

Classifies files into different subdirectories based on their file sizes.

### Example

```bash
# Using default thresholds (300 and 700 bytes)
python classify_files_by_size.py /path/to/directory

# Custom thresholds
python classify_files_by_size.py /path/to/directory --small 1024 --large 10240

# Custom category names
python classify_files_by_size.py /path/to/directory --small-category tiny --medium-category normal --large-category huge
```

## File Time Classification

Classifies files into MM/DD directory structure based on their creation time, and creates metadata_analyse.txt files containing the earliest and latest file information in each directory.

### Example

```bash
# Classify files by creation time
python classify_files_by_time.py /path/to/directory
```
