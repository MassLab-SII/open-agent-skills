---
name: desktop-template-utilities
description: Tools for organizing desktop templates, computing personal budgets, and consolidating contact information.
---

# Desktop Template Utilities

This skill set provides three tools for desktop template organization, budget calculation, and contact consolidation:

1. **File Arrangement**: Archive desktop files by category
2. **Budget Computation**: Extract personal living expenses and summarize
3. **Contact Information**: Consolidate contact info and answer specific questions

## 1) File Arrangement (file_arrangement.py)

Moves files to unified categorized directories according to rules:
- work/: Work, research, project related
- life/: Personal life related
- archives/: Archive, history, backup, tax related
- temp/: Temporary/drafts
- others/: Files that cannot be categorized

### Usage
```bash
python file_arrangement.py /path/to/desktop_template
```

### Features
- Automatically creates categorized directories
- Classifies based on file path and keywords
- Does not modify filenames, only moves location

## 2) Budget Computation (budget_computation.py)

Scans desktop template, extracts personal living expenses, generates `total_budget.txt`:
- Each line: `file_path;price` (relative path, two decimal places)
- Last line: Total sum (two decimal places)

### Usage
```bash
python budget_computation.py /path/to/desktop_template
python budget_computation.py /path/to/desktop_template --output my_budget.txt
```

### Features
- Excludes work/project related paths
- Parses numeric values in files as expense entries
- Summarizes total expenses

## 3) Contact Information (contact_information.py)

Scans all files, extracts contact information and generates `contact_info.csv`, also answers:
> What is Charlie Davis's occupation/job?

Output:
- `contact_info.csv`: Columns include Name, Email, Phone and other detected fields
- `answer.txt`: Answer to the above question (Unknown if cannot determine)

### Usage
```bash
python contact_information.py /path/to/desktop_template
```

### Features
- Supports CSV/text contact information extraction
- Dynamically unions all fields, automatically generates header
- Generates answer file answer.txt

## General Notes
- All scripts rely on `FileSystemTools` from `utils.py` for file operations
- Default uses async I/O
- Does not modify file content, only reads or moves/writes new files

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
python run_fs_ops.py /path/to/base -c "await fs.read_text_file('/path/to/file.txt', head=10)"
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
python run_fs_ops.py /path/to/base -c "await fs.write_file('/path/to/new.txt', 'Hello World')"
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
python run_fs_ops.py /path/to/base -c "await fs.get_files_info_batch(['a.txt', 'b.txt'], '/path/to/files')"
```

