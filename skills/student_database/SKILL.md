---
name: student-database-tools
description: Toolkit for student database duplicate name detection, English talent screening, and grade calculation.
---

# Student Database Tools

Three common operations:
1. **Duplicate Name Detection**: Outputs namesake.txt
2. **English Talent Screening**: Generates qualified_students.txt based on recommendation level and TOEFL
3. **Grade Calculation**: Generates student_grades.csv and grade_summary.txt

## 1) duplicate_name.py
Scans all basic_info.txt files to find students with the same name and their IDs.

### Output
```
name: xxx
count: n
ids: id1, id2, ...

(blank line separator)
```

### Usage
```bash
python duplicate_name.py /path/to/student_database
```

## 2) english_talent.py
Filters students meeting:
1) recommendation_letter.txt rating is S or A  
2) TOEFL >= 100  

### Output
qualified_students.txt
```
name: xxx
id: xxx
email: xxx

...
```

### Usage
```bash
python english_talent.py /path/to/student_database
```

## 3) gradebased_score.py
Maps scores to grades: A(90+), B(80-89), C(70-79), D(60-69), F(<60).

### Output
- student_grades.csv:  
  `student_id,name,chinese_score,chinese_grade,math_score,math_grade,english_score,english_grade`
- grade_summary.txt: A/B/C/D/F statistics per subject, pass(A/B/C)/fail(D/F) counts, total count.

### Usage
```bash
python gradebased_score.py /path/to/student_database
```

## General Notes
- Relies on `FileSystemTools` from `utils.py` for file operations (async)
- Only reads/writes or moves new files, does not modify original content
- Key fields: name/id/email/chinese/math/english/toefl in basic_info.txt; rating in recommendation_letter.txt

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

