---
name: advanced-file-management
description: Advanced file management and analysis tools. Includes directory statistics, student database processing (grades, duplicate names, TOEFL/recommendation filtering), HTML author extraction, music analysis reports, and batch folder creation. Also provides basic FileSystemTools for atomic file operations (read, write, edit, move, search).
---

# Advanced File Management Skill

This skill provides tools for desktop file management and analysis:

1. **Music analysis**: Generate popularity reports from music data
2. **Folder creation**: Create multiple folders under a target directory
3. **List all files**: Recursively list all files under a directory
4. **File statistics**: Count files, folders, and calculate total size
5. **Grade-based score**: Calculate student grades from database
6. **Duplicate name finder**: Find duplicate names in student database
7. **Extract authors**: Extract authors from HTML papers
8. **Filter by recommendation**: Find students by recommendation grade
9. **Filter by TOEFL**: Find students by TOEFL score threshold

## Important Notes

- **Do not use other bash commands**: Do not attempt to use general bash commands or shell operations like cat, ls.


## 1. Music Analysis Report

Analyzes music data from multiple artists, calculates popularity scores using a weighted formula, and generates a detailed analysis report.

### Features

- Reads song data from multiple artist directories
- Supports CSV and TXT file formats
- Calculates popularity scores using configurable weights:
  - `popularity_score = (rating × W1) + (play_count_normalized × W2) + (year_factor × W3)`
  - Default weights: W1=0.4, W2=0.4, W3=0.2
- Sorts songs by popularity

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--output` | `music_analysis_report.txt` | Output report filename |
| `--rating-weight` | `0.4` | Weight for rating score |
| `--play-count-weight` | `0.4` | Weight for normalized play count |
| `--year-weight` | `0.2` | Weight for year factor |

### Example

```bash
# Generate music analysis report with default weights (0.4, 0.4, 0.2)
python music_report.py /path/to/directory

# Use a custom output filename
python music_report.py /path/to/directory --output my_report.txt

# Use custom weights for the popularity formula
python music_report.py /path/to/directory --rating-weight 0.5 --play-count-weight 0.3 --year-weight 0.2
```


## 2. Create Folders

Creates multiple folders under a target directory.

### Features

- Creates multiple folders with specified names
- Supports any number of folder names as arguments

### Example

```bash
# Create 3 folders
python create_folders.py /path/to/directory folder1 folder2 folder3

# Create folders with specific names
python create_folders.py /path/to/directory experiments learning personal
```

## 3. List All Files

Recursively list all files under a given directory path. Useful for quickly understanding project directory structure.

### Features

- Recursively traverse all subdirectories
- Option to exclude hidden files (like .DS_Store)
- Output one file path per line, including both path and filename (relative to input directory)

### Example

```bash
# List all files (excluding hidden)
python list_all_files.py /path/to/directory

# Include hidden files
python list_all_files.py /path/to/directory --include-hidden
```

---

## 4. File Statistics

Generate file statistics for a directory: total files, folders, and size.

### Features

- Count total files (excluding .DS_Store)
- Count total folders
- Calculate total size in bytes (includes .DS_Store for size only)

### Example

```bash
python file_statistics.py /path/to/directory
```

---

## 5. Grade-Based Score

Calculate student grades from student database and generate output files.

### Features

- Read all basic_info.txt files from student folders
- Extract chinese, math, english scores
- Calculate grades: A(90+), B(80-89), C(70-79), D(60-69), F(<60)
- Generate student_grades.csv and grade_summary.txt

### Example

```bash
python gradebased_score.py /path/to/student_database

# Specify output directory
python gradebased_score.py /path/to/student_database --output-dir /path/to/output
```

### Output Files

1. **student_grades.csv**: student_id, name, chinese_score, chinese_grade, math_score, math_grade, english_score, english_grade
2. **grade_summary.txt**: Total students, A/B/C/D/F counts per subject, pass/fail counts

---

## 6. Duplicate Name Finder

Find duplicate names in student database.

### Features

- Scan all student folders
- Extract names from basic_info.txt
- Identify names that appear more than once
- Generate namesake.txt

### Example

```bash
python duplicate_name.py /path/to/student_database

# Specify output file
python duplicate_name.py /path/to/student_database --output /path/to/namesake.txt
```

### Output Format

```
name: xxx
count: xxx
ids: xxx, xxx, ...

name: yyy
count: yyy
ids: yyy, yyy, ...
```

---

## 7. Extract Authors

Extract authors from all HTML papers in a directory using `<meta name="citation_author">` tags.

### Features

- Automatically scan all HTML files in directory
- Extract author names from citation_author meta tags
- Support multiple authors per paper
- Returns list of dicts with filename and authors

### Example

```bash
# Extract and print authors from all HTML files
python extract_authors.py /path/to/papers

# Save to file
python extract_authors.py /path/to/papers --output authors.txt
```

---

## 8. Filter by Recommendation Grade

Find students with specified grade(s) from recommendation_letter.txt files.

### Features

- Filter by single grade (S, A, B, C, D, F) or multiple grades (e.g., SA for S or A)
- Returns list of matching student folder names

### Example

```bash
# Filter students with grade S
python filter_by_recommendation.py /path/to/student_database S

# Filter students with grade A
python filter_by_recommendation.py /path/to/student_database A

# Filter students with grade S OR A
python filter_by_recommendation.py /path/to/student_database SA
```

---

## 9. Filter by TOEFL Score

Find students with TOEFL score >= a specified threshold.

### Features

- Reads TOEFL score from basic_info.txt in each student folder
- Filter by minimum score threshold
- Returns list of matching student folder names

### Example

```bash
# Find students with TOEFL >= 100
python filter_by_toefl.py /path/to/student_database 100

# Find students with TOEFL >= 90
python filter_by_toefl.py /path/to/student_database 90
```

---

## II. Basic Tools (FileSystemTools)

Below are the basic tool functions. These are atomic operations for flexible combination.

**Important**: The first argument `/path/to/base` is the **base directory** (allowed directory). This is a security sandbox - all file operations are restricted to this directory and its subdirectories. Files outside this boundary cannot be accessed.

**Note**: Code should be written without line breaks.

### How to Run

```bash
# Standard format
python run_fs_ops.py /path/to/base -c "await fs.read_text_file('/path/to/file.txt')"
```

---

### File Reading Tools

#### `read_text_file(path, head=None, tail=None)`
**Use Cases**:
- Read complete file contents
- Read first N lines (head) or last N lines (tail)

**Example**:
```bash
# Read entire file
python run_fs_ops.py /path/to/base -c "await fs.read_text_file('/path/to/file.txt')"

# Read first 10 lines
python run_fs_ops.py /path/to/base -c "await fs.read_text_file('/path/to/file.txt', head=10)"
```

---

#### `read_multiple_files(paths)`
**Use Cases**:
- Read multiple files simultaneously
- Batch file reading operations

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.read_multiple_files(['/path/a.txt', '/path/b.txt'])"
```

---

### File Writing Tools

#### `write_file(path, content)`
**Use Cases**:
- Create new files
- Overwrite existing files

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.write_file('/path/to/new.txt', 'Hello World')"
```

---

#### `edit_file(path, edits)`
**Use Cases**:
- Make line-based edits to existing files
- Partial file modifications

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.edit_file('/path/to/file.txt', [{'oldText': 'foo', 'newText': 'bar'}])"
```

---

### Directory Tools

#### `create_directory(path)`
**Use Cases**:
- Create new directories
- Supports recursive creation (like mkdir -p)

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.create_directory('/path/to/new/nested/dir')"
```

---

#### `list_directory(path)`
**Use Cases**:
- List all files and directories in a path
- Returns tuple of (files, directories)

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.list_directory('/path/to/directory')"
```

---

#### `list_files(path=None, exclude_hidden=True)`
**Use Cases**:
- List only files in a directory
- Optionally exclude hidden files like .DS_Store

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.list_files('/path/to/directory')"
```

---

### File Operations

#### `move_file(source, destination)`
**Use Cases**:
- Move files or directories
- Rename files or directories

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.move_file('/path/old.txt', '/path/new.txt')"
```

---

#### `search_files(pattern, base_path=None)`
**Use Cases**:
- Search for files matching a glob pattern
- Examples: '*.txt', '**/*.py'

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.search_files('*.txt')"
python run_fs_ops.py /path/to/base -c "await fs.search_files('**/*.py', '/path/to/search')"
```

---

### File Information

#### `get_file_info(path)`
**Use Cases**:
- Get detailed metadata (size, created, modified, etc.)

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_file_info('/path/to/file.txt')"
```

---

#### `get_file_size(path)`
**Use Cases**:
- Get file size in bytes

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_file_size('/path/to/file.txt')"
```

---

#### `get_file_ctime(path)` / `get_file_mtime(path)`
**Use Cases**:
- Get file creation/modification time

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_file_mtime('/path/to/file.txt')"
```

---

#### `get_files_info_batch(filenames, base_path=None)`
**Use Cases**:
- Get file information for multiple files in parallel

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_files_info_batch(['a.txt', 'b.txt'], '/path/to/files')"
```

