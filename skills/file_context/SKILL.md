---
name: file_context
description: This skill analyzes and organizes files based on their content. It provides tools for duplicate detection, file merging, file splitting, pattern matching, and text transformation. Use this when you need to work with file content rather than just file metadata.
---

# File Content Analysis Skill

This skill provides comprehensive content-based file analysis and manipulation:

1. **Duplicate detection**: Find and organize files with identical content
2. **File merging**: Combine multiple small files into one
3. **File splitting**: Split large files into smaller equal-sized parts
4. **Pattern matching**: Find files containing specific substrings
5. **Text transformation**: Convert files to uppercase and count words

## 1. Duplicate File Detection

Scans all files in a directory, identifies files with duplicate content, and moves them to a separate subdirectory.

### Example

```bash
# Find and organize duplicate files (default directory name: 'duplicates')
python find_duplicates.py /path/to/directory

# Use a custom directory name for duplicates
python find_duplicates.py /path/to/directory --duplicates-dir my_duplicates
```

## 2. File Merging

Identifies the N smallest .txt files, sorts them alphabetically, and merges their content into a single file with proper formatting.

### Example

```bash
# Merge the 10 smallest .txt files (default)
python merge_files.py /path/to/directory

# Merge the 5 smallest files
python merge_files.py /path/to/directory --count 5

# Use a custom output filename
python merge_files.py /path/to/directory --output merged_content.txt
```

## 3. File Splitting

Splits a large text file into multiple smaller files with equal character counts.

### Example

```bash
# Split large_file.txt into 10 equal parts (default)
python split_file.py /path/to/directory large_file.txt

# Split into 5 parts
python split_file.py /path/to/directory large_file.txt --parts 5

# Use a custom output directory name
python split_file.py /path/to/directory large_file.txt --output-dir spilt
```

## 4. Pattern Matching

Finds all files that contain a substring of N or more characters that also appears in a reference file.

### Example

```bash
# Find files with 30+ character matches (default)
python pattern_matching.py /path/to/directory large_file.txt

# Use a custom minimum length
python pattern_matching.py /path/to/directory large_file.txt --min-length 50

# Use a custom output filename
python pattern_matching.py /path/to/directory large_file.txt --output results.txt
```

## 5. Text Transformation (Uppercase Conversion)

Converts text files to uppercase and counts words in each file.

### Example

```bash
# Convert specific files to uppercase
python convert_uppercase.py /path/to/directory --files file_01.txt file_02.txt file_03.txt

# Use a custom output directory name
python convert_uppercase.py /path/to/directory --files file_01.txt file_02.txt --output-dir UPPERCASE
```


