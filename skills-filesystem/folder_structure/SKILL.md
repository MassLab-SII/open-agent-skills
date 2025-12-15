---
name: folder-structure-operations
description: This skill provides tools for analyzing and manipulating directory structures. It can analyze directory statistics, mirror directory hierarchies, apply transformation rules, and create placeholder files. Use this when you need to work with folder structures.
---

# Folder Structure Operations Skill

This skill provides tools for directory structure operations:

1. **Structure analysis**: Generate detailed statistical reports about directory structures
2. **Structure mirroring**: Replicate directory hierarchies with custom rules

## 1. Structure Analysis

Recursively analyzes a directory structure and generates a detailed statistical report including file counts, folder counts, total size, depth analysis, and file type classification.

### Features

- Counts total files and folders (excluding .DS_Store from counts)
- Calculates total size of all files (including .DS_Store)
- Identifies the deepest folder path and its depth level
- Classifies files by extension type
- Generates a formatted report file

### Example

```bash
# Analyze directory structure (default output: structure_analysis.txt)
python analyze_structure.py /path/to/directory

# Use a custom output filename
python analyze_structure.py /path/to/directory --output my_analysis.txt
```


## 2. Structure Mirroring

Mirrors a directory structure without copying file contents. Creates placeholder files in empty directories and applies custom transformation rules.

### Features

- Replicates entire directory hierarchies
- Does not copy file contents, only creates directories
- Discards directories containing more than N files
- Appends "_processed" to directory names containing numbers
- Creates placeholder.txt files in empty directories with their absolute paths
- Handles nested directories of any depth

### Example

```bash
# Mirror complex_structure to complex_structure_mirror (default settings)
python mirror_structure.py /path/to/directory complex_structure

# Use a custom output directory name
python mirror_structure.py /path/to/directory complex_structure --output-dir my_mirror

# Allow up to 5 files per directory before discarding
python mirror_structure.py /path/to/directory complex_structure --max-files 5

# Disable appending "_processed" to directories with numbers
python mirror_structure.py /path/to/directory complex_structure --no-append-processed
```

