---
name: votenet-tools
description: VoteNet utility toolkit covering dependency generation, debugging assistance, and dataset category mapping statistics.
---

# VoteNet Toolkit

Contains three scripts:
1. **requirements_writing.py**: Generate/merge VoteNet dependencies into requirements.txt
2. **debugging.py**: Locate potential backbone/PointNet/VoteNet related bug files, output path to answer.txt
3. **dataset_comparison.py**: Map ScanNet categories to SUNRGBD 10 classes and count, output analysis.txt

## 1) requirements_writing.py
- Generates/merges requirements.txt based on common 3D detection dependencies (deduplicated, alphabetically sorted):
  torch, torchvision, numpy, scipy, scikit-learn, matplotlib, pyyaml, tqdm,
  h5py, opencv-python, open3d, trimesh, plyfile, pandas, networkx,
  tensorboard, einops

### Usage
```bash
python requirements_writing.py /path/to/votenet
```

## 2) debugging.py
- Searches for .py files containing votenet/backbone/pointnet keywords, writes priority path to `answer.txt` (path only).
- Used to assist manual bug investigation.

### Usage
```bash
python debugging.py /path/to/votenet
```

## 3) dataset_comparison.py
- Assumes annotation JSON contains `objects` list with `category` field, maps ScanNet categories to SUNRGBD 10 classes and counts.
- Supports simple synonyms (night_stand→nightstand, bookshelf(es), couch→sofa, etc.).
- Outputs `analysis.txt`, each class has two lines (class name, count) separated by blank line.

### Usage
```bash
python dataset_comparison.py /path/to/votenet
```

## General Notes
- Relies on `FileSystemTools` from `utils.py` (async I/O)
- Does not modify source code, except requirements_writing writes dependencies; debugging only writes answer.txt; dataset_comparison only writes analysis.txt

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

