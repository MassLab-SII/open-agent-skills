---
name: desktop-file-management
description: This skill provides tools for managing and analyzing desktop files. It includes music analysis reports, folder creation, and timeline extraction. Use this when you need to organize scattered files, analyze data, or extract temporal information.
---

# Desktop File Management Skill

This skill provides tools for desktop file management and analysis:

1. **Music analysis**: Generate popularity reports from music data
2. **Folder creation**: Create multiple folders under a target directory
3. **Timeline extraction**: Extract and organize temporal information from files

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

## 3. Timeline Extraction

Extracts timeline information from files and generates a chronologically sorted timeline report.

### Features

- Recursively scans all files
- Extracts dates in multiple formats:
  - YYYY-MM-DD
  - Month YYYY (uses 1st day)
  - MM/DD/YYYY
- Filters by specific year
- Removes duplicate dates per file
- Sorts chronologically
- Generates timeline.txt report

### Example

```bash
# Extract 2024 timeline (default)
python extract_timeline.py /path/to/directory

# Extract timeline for a specific year
python extract_timeline.py /path/to/directory --year 2023

# Use a custom output filename
python extract_timeline.py /path/to/directory --output my_timeline.txt
```

### Output Format

Each line: `file_path:YYYY-MM-DD`

### Rules

- If only month is shown, use the 1st day of that month
- If only year is shown, skip it
- If multiple tasks on same date in same file, count only once
- Sort by chronological order

---

## II. Basic Tools (FileSystemTools)

Below are the basic tool functions from `utils.py`. These are atomic operations for flexible combination.

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

