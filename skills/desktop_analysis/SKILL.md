---
name: desktop-analysis
description: Desktop analysis and reporting tools. Includes music analysis with popularity scoring and file statistics (count files, folders, and calculate total size).
---

# Desktop Analysis Skill

This skill provides data analysis and reporting tools:

1. **Music analysis**: Generate popularity reports from music data
2. **File statistics**: Count files, folders, and calculate total size
3. **List all files**: Recursively list all files under a directory

## Important Notes

- **Do not use other bash commands**: Do not attempt to use general bash commands or shell operations like cat, ls.
- **Use relative paths**: Use paths relative to the working directory (e.g., `./folder/file.txt` or `folder/file.txt`).

---

## I. Skills

### 1. Music Analysis Report

Analyzes music data from multiple artists, calculates popularity scores using a weighted formula, and generates a detailed analysis report.

#### Features

- Reads song data from multiple artist directories
- Supports CSV and TXT file formats
- Calculates popularity scores using configurable weights:
  - `popularity_score = (rating × W1) + (play_count_normalized × W2) + (year_factor × W3)`
  - Default weights: W1=0.4, W2=0.4, W3=0.2
- Sorts songs by popularity

#### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--output` | `music_analysis_report.txt` | Output report filename |
| `--rating-weight` | `0.4` | Weight for rating score |
| `--play-count-weight` | `0.4` | Weight for normalized play count |
| `--year-weight` | `0.2` | Weight for year factor |

#### Example

```bash
# Generate music analysis report with default weights (0.4, 0.4, 0.2)
python music_report.py ./music

# Use a custom output filename
python music_report.py ./music --output my_report.txt

# Use custom weights for the popularity formula
python music_report.py ./music --rating-weight 0.5 --play-count-weight 0.3 --year-weight 0.2
```

---

### 2. File Statistics

Generate file statistics for a directory: total files, folders, and size.

#### Features

- Count total files (excluding .DS_Store)
- Count total folders
- Calculate total size in bytes (includes .DS_Store for size only)

#### Example

```bash
python file_statistics.py .
```

---

### 3. List All Files

Recursively list all files under a given directory path. Useful for quickly understanding project directory structure.

#### Features

- Recursively traverse all subdirectories
- Option to exclude hidden files (like .DS_Store)
- Output one file path per line, including both path and filename (relative to input directory)

#### Example

```bash
# List all files (excluding hidden)
python list_all_files.py .

# Include hidden files
python list_all_files.py ./data --include-hidden
```

---

## II. Basic Tools (FileSystemTools)

Below are the basic tool functions. These are atomic operations for flexible combination.

**Prefer Skills over Basic Tools**: When a task matches one of the Skills above, use the corresponding Skill instead of Basic Tools. Skills are more efficient because they can perform batch operations in a single call.

**Prefer List All Files over list_directory/list_files**: When you need to list files in a directory, prefer using the `list_all_files.py` skill instead of `list_directory` or `list_files` basic tools. The skill provides recursive listing with better output formatting.

**Note**: Code should be written without line breaks.

### How to Run

```bash
# Standard format
python run_fs_ops.py -c "await fs.read_text_file('./file.txt')"
```

---

### File Reading Tools

#### `read_text_file(path, head=None, tail=None)`
**Use Cases**:
- Read complete file contents
- Read first N lines (head) or last N lines (tail)

**Example**:
```bash
python run_fs_ops.py -c "await fs.read_text_file('./data/file.txt')"
```

---

#### `read_multiple_files(paths)`
**Use Cases**:
- Read multiple files simultaneously

**Example**:
```bash
python run_fs_ops.py -c "await fs.read_multiple_files(['./a.txt', './b.txt'])"
```

---

### File Writing Tools

#### `write_file(path, content)`
**Use Cases**:
- Create new files with **short, simple content only**
- Overwrite existing files

**⚠️ Warning**: Do NOT include triple backticks (` ``` `) in the content, as this will break command parsing.

**Example**:
```bash
python run_fs_ops.py -c "await fs.write_file('./new.txt', 'Hello World')"
```

---

#### `edit_file(path, edits)`
**Use Cases**:
- Make line-based edits to existing files

**Example**:
```bash
python run_fs_ops.py -c "await fs.edit_file('./file.txt', [{'oldText': 'foo', 'newText': 'bar'}])"
```

---

### Directory Tools

#### `create_directory(path)`
**Use Cases**:
- Create new directories (supports recursive creation)

**Example**:
```bash
python run_fs_ops.py -c "await fs.create_directory('./new/nested/dir')"
```

---

#### `list_directory(path)`
**Use Cases**:
- List all files and directories in a path

**Example**:
```bash
python run_fs_ops.py -c "await fs.list_directory('.')"
```

---

#### `list_files(path=None, exclude_hidden=True)`
**Use Cases**:
- List only files in a directory

**Example**:
```bash
python run_fs_ops.py -c "await fs.list_files('./data')"
```

---

### File Operations

#### `move_file(source, destination)`
**Use Cases**:
- Move or rename files/directories

**Example**:
```bash
python run_fs_ops.py -c "await fs.move_file('./old.txt', './new.txt')"
```

---

#### `search_files(pattern, base_path=None)`
**Use Cases**:
- Search for files matching a glob pattern

**Example**:
```bash
python run_fs_ops.py -c "await fs.search_files('*.txt')"
```

---

### File Information

#### `get_file_info(path)`
**Use Cases**:
- Get detailed metadata (size, created, modified, etc.)

**Example**:
```bash
python run_fs_ops.py -c "await fs.get_file_info('./file.txt')"
```

---

#### `get_file_size(path)`
**Use Cases**:
- Get file size in bytes

**Example**:
```bash
python run_fs_ops.py -c "await fs.get_file_size('./file.txt')"
```

---

#### `get_file_ctime(path)` / `get_file_mtime(path)`
**Use Cases**:
- Get file creation/modification time

**Example**:
```bash
python run_fs_ops.py -c "await fs.get_file_mtime('./file.txt')"
```

---

#### `get_files_info_batch(filenames, base_path=None)`
**Use Cases**:
- Get file information for multiple files in parallel

**Example**:
```bash
python run_fs_ops.py -c "await fs.get_files_info_batch(['a.txt', 'b.txt'], './data')"
```
