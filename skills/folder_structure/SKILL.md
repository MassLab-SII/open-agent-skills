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

