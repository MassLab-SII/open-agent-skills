---
name: legal-document-analysis
description: This skill provides tools for analyzing legal documents across multiple versions. It can track disputed clauses, count individual comments, and trace solution origins. Use this when you need to analyze comment patterns, identify contributors, or understand the evolution of legal agreements.
---

# Legal Document Analysis Skill

This skill provides tools for analyzing legal document revisions:

1. **Dispute review**: Identify and count comments on disputed clauses
2. **Individual comments**: Track comment counts by person and clause
3. **Solution tracing**: Identify who first proposed final solutions

## 1. Dispute Review

Analyzes legal document versions to identify disputed clauses and count the total number of comments on each clause.

### Features

- Reads multiple document versions
- Extracts comments in format `[name:content]`
- Counts comments per clause
- Excludes "All parties" joint comments
- Generates dispute review report

### Example

```bash
# Analyze versions v5, v6, v7 (default)
python dispute_review.py /path/to/directory

# Analyze custom versions
python dispute_review.py /path/to/directory --versions v3 v4 v5

# Use a custom output filename
python dispute_review.py /path/to/directory --output my_review.txt
```

### Output Format

```
clause_number:comment_count
1.1:3
1.3:3
4.6:6
4.16:5
6.8:4
```

## 2. Individual Comments Analysis

Counts comments made by specific individuals on designated clauses across multiple versions.

### Features

- Tracks comments by specific people
- Focuses on designated clauses
- Generates person × clause matrix
- Outputs CSV format
- Excludes "All parties" comments

### Example

```bash
# Analyze versions v5-v8 with default settings
python individual_comments.py /path/to/directory

# Analyze custom versions
python individual_comments.py /path/to/directory --versions v5 v6 v7

# Specify custom clauses and people
python individual_comments.py /path/to/directory --clauses 1.1 1.3 4.6 --people "Bill Harvey" "Tony Taylor"

# Use a custom output filename
python individual_comments.py /path/to/directory --output my_comments.csv
```

### Output Format (CSV)

```csv
Name,1.1,1.3,4.6,4.16,6.8,6.16
Bill Harvey,0,2,3,1,1,1
Michelle Jackson,0,1,2,1,1,1
David Russel,2,1,1,2,1,1
Tony Taylor,2,0,1,2,1,1
```

## 3. Solution Tracing

Traces the origin of final solutions by identifying who first proposed ideas that led to the final agreed solutions.

### Features

- Analyzes comment history across versions
- Identifies solution originators
- Tracks version where solution was first proposed
- Generates CSV with version numbers and names
- Focuses on key clauses

### Example

```bash
# Trace solutions in versions v5-v9 (default)
python solution_tracing.py /path/to/directory

# Trace solutions in custom versions
python solution_tracing.py /path/to/directory --versions v5 v6 v7

# Specify custom clauses
python solution_tracing.py /path/to/directory --clauses 4.6 4.16 6.8

# Use a custom output filename
python solution_tracing.py /path/to/directory --output my_tracing.csv
```

### Output Format (CSV)

```csv
,4.6,4.16,6.8,6.16
version_number,5,6,7,8
name,Tony Taylor,Michelle Jackson,Michelle Jackson,Tony Taylor
```

## Common Features

- **Comment Format**: All scripts recognize comments in format `[name:content]`
- **Special Handling**: "All parties" comments are handled specially (counted as one comment but not attributed to individuals)
- **Version Naming**: Expects files named `Preferred_Stock_Purchase_Agreement_vX.txt`
- **Clause Format**: Clauses are identified by format `X.X` (e.g., 1.1, 4.6)

## Use Cases

- Track negotiation progress in legal agreements
- Identify most disputed clauses
- Analyze individual contribution patterns
- Trace the evolution of solutions
- Generate reports for stakeholders
- Audit comment history

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

