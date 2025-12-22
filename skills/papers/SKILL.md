---
name: papers-management
description: Tools for managing arXiv paper collections — organize legacy papers, group frequent authors, and locate specific math benchmarks.
---

# Papers Management Skill

Provides three utility scripts for paper collections:
1. **Organize Legacy Papers**: Organize papers from 2023 and earlier by year and generate indices.
2. **Author Grouping**: Identify frequent authors and copy papers by author.
3. **Find Math Benchmark Papers**: Automatically locate and rename math benchmark-related papers.

## 1) organize_legacy_papers.py
Organizes HTML papers from 2023 and earlier into `organized/<year>/`, generating indices and summaries.

### Features
- Moves papers from 2023 and earlier based on arXiv ID year (first two digits).
- Keeps 2024+ papers and `arxiv_2025.bib` in place.
- Generates `INDEX.md` for each year (Table: ArXiv ID | Authors | Local Path; takes first 3 authors, appends "et al." if >3).
- Generates `organized/SUMMARY.md` summarizing all years.

### Usage
```bash
python organize_legacy_papers.py /path/to/papers
```

## 2) author_folders.py
Identifies frequent authors and copies papers:
- `frequent_authors/`: Authors with total papers ≥4.
- `2025_authors/`: Authors with 2025 papers ≥3.
- Author directory names: lowercase, spaces/commas replaced with underscores.
- Copies (does not move) papers, preserving original files.

### Usage
```bash
python author_folders.py /path/to/papers
```

## 3) find_math_paper.py
Finds papers describing "math benchmarks, checking correctness and analyzing knowledge gaps/under-generalization/rote memorization", and renames the corresponding HTML to `answer.html`.

### Usage
```bash
python find_math_paper.py /path/to/papers
```

### Notes
- Selects the paper best matching the description via keyword scoring.
- Writes the selected paper as `answer.html` (overwrites if exists).

## General Notes
- All scripts rely on `FileSystemTools` from `utils.py` for file operations.
- Default asynchronous I/O.
- Does not modify paper content; only moves/copies or writes new files.

---

## II. Basic Tools (FileSystemTools)

Below are the basic tool functions from `utils.py`. These are atomic operations for flexible combination.

### How to Run

```bash
python run_fs_ops.py /path/to/base -c "await fs.read_text_file('/path/to/file.txt')"
```

---

### File Reading Tools

#### `read_text_file(path, head=None, tail=None)`
Read complete file contents, or first/last N lines.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.read_text_file('/path/to/file.txt')"
```

#### `read_multiple_files(paths)`
Read multiple files simultaneously.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.read_multiple_files(['/path/a.txt', '/path/b.txt'])"
```

---

### File Writing Tools

#### `write_file(path, content)`
Create new file or overwrite existing file.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.write_file('/path/to/new.txt', 'content')"
```

#### `edit_file(path, edits)`
Make line-based edits to existing files.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.edit_file('/path/to/file.txt', [{'oldText': 'foo', 'newText': 'bar'}])"
```

---

### Directory Tools

#### `create_directory(path)`
Create new directories (supports recursive creation).

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.create_directory('/path/to/new/dir')"
```

#### `list_directory(path)`
List all files and directories, returns (files, directories).

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.list_directory('/path/to/directory')"
```

#### `list_files(path=None, exclude_hidden=True)`
List only files, optionally exclude hidden files.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.list_files('/path/to/directory')"
```

---

### File Operations

#### `move_file(source, destination)`
Move or rename files/directories.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.move_file('/path/old.txt', '/path/new.txt')"
```

#### `search_files(pattern, base_path=None)`
Search for files matching glob pattern (e.g., '*.txt', '**/*.py').

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.search_files('*.txt')"
```

---

### File Information

#### `get_file_info(path)`
Get detailed metadata (size, created, modified, etc.).

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_file_info('/path/to/file.txt')"
```

#### `get_file_size(path)`
Get file size in bytes.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_file_size('/path/to/file.txt')"
```

#### `get_file_ctime(path)` / `get_file_mtime(path)`
Get file creation/modification time.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_file_mtime('/path/to/file.txt')"
```

#### `get_files_info_batch(filenames, base_path=None)`
Get file info for multiple files in parallel.

**Example**:
```bash
python run_fs_ops.py /path/to/base -c "await fs.get_files_info_batch(['a.txt', 'b.txt'])"
```

