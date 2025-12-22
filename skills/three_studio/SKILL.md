---
name: threestudio-tools
description: Utility toolkit for ThreeStudio codebase covering dependency fixing, file locating, and output structure analysis.
---

# ThreeStudio Toolkit

Contains three scripts:
1. **requirements_completion.py**: Complete Zero123 related dependencies in requirements.txt
2. **code_locating.py**: Locate Zero123 guidance implementation file, output path to answer.txt
3. **output_analysis.py**: Analyze guidance_out structure in zero123.py, write to answer.txt

## 1) requirements_completion.py
- Searches for requirements.txt in the project
- Appends Zero123 common dependencies (einops, k-diffusion, transformers, diffusers, omegaconf, pytorch-lightning, open-clip-torch, trimesh, imageio[ffmpeg]) to the file, avoiding duplicates

### Usage
```bash
python requirements_completion.py /path/to/threestudio
```

## 2) code_locating.py
- Searches for .py files containing "zero123" with "guidance" in the path
- Prioritizes `threestudio/models/guidance/zero123*.py`
- Writes relative path to `answer.txt` in project root

### Usage
```bash
python code_locating.py /path/to/threestudio
```

## 3) output_analysis.py
- Reads `threestudio/systems/zero123.py` (or searches for zero123.py)
- Locates guidance_out assignment line, extracts keys if dict; otherwise outputs snippet
- Writes to `answer.txt` (contains structure or snippet, and file relative path)

### Usage
```bash
python output_analysis.py /path/to/threestudio
```

## General Notes
- Relies on `FileSystemTools` from `utils.py` (async I/O)
- Does not modify source code content, except requirements_completion writes dependencies
- Output files are written to project root (answer.txt or modified requirements.txt)

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

