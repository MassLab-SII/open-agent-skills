---
name: student-database
description: Student database processing tools. Includes grade calculation, duplicate name detection, recommendation letter filtering, and TOEFL score filtering.
---

# Student Database Skill

This skill provides tools for processing student database:

1. **Grade calculation**: Calculate student grades from scores
2. **Duplicate name finder**: Find duplicate names in database
3. **Filter by recommendation**: Find students by recommendation grade
4. **Filter by TOEFL**: Find students by TOEFL score threshold

## Important Notes

- **Do not use other bash commands**: Do not attempt to use general bash commands or shell operations like cat, ls.
- **Use relative paths**: Use paths relative to the working directory (e.g., `./student_database`).

---

## I. Skills

### 1. Grade-Based Score

Calculate student grades from student database and generate output files.

#### Features

- Read all basic_info.txt files from student folders
- Extract chinese, math, english scores
- Calculate grades: A(90+), B(80-89), C(70-79), D(60-69), F(<60)
- Generate student_grades.csv and grade_summary.txt

#### Example

```bash
python gradebased_score.py ./student_database

# Specify output directory
python gradebased_score.py ./student_database --output-dir ./output
```

#### Output Files

1. **student_grades.csv**: student_id, name, chinese_score, chinese_grade, math_score, math_grade, english_score, english_grade
2. **grade_summary.txt**: Total students, A/B/C/D/F counts per subject, pass/fail counts

---

### 2. Duplicate Name Finder

Find duplicate names in student database.

#### Features

- Scan all student folders
- Extract names from basic_info.txt
- Identify names that appear more than once
- Generate namesake.txt

#### Example

```bash
python duplicate_name.py ./student_database

# Specify output file
python duplicate_name.py ./student_database --output ./namesake.txt
```

#### Output Format

```
name: xxx
count: xxx
ids: xxx, xxx, ...

name: yyy
count: yyy
ids: yyy, yyy, ...
```

---

### 3. Filter by Recommendation Grade

Find students with specified grade(s) from recommendation_letter.txt files.

#### Features

- Filter by single grade (S, A, B, C, D, F) or multiple grades (e.g., SA for S or A)
- Returns list of matching student folder names

#### Example

```bash
# Filter students with grade S
python filter_by_recommendation.py ./student_database S

# Filter students with grade A
python filter_by_recommendation.py ./student_database A

# Filter students with grade S OR A
python filter_by_recommendation.py ./student_database SA
```

---

### 4. Filter by TOEFL Score

Find students with TOEFL score >= a specified threshold.

#### Features

- Reads TOEFL score from basic_info.txt in each student folder
- Filter by minimum score threshold
- Returns list of matching student folder names

#### Example

```bash
# Find students with TOEFL >= 100
python filter_by_toefl.py ./student_database 100

# Find students with TOEFL >= 90
python filter_by_toefl.py ./student_database 90
```

---

## II. Basic Tools (FileSystemTools)

Below are the basic tool functions. These are atomic operations for flexible combination.

**Prefer Skills over Basic Tools**: When a task matches one of the Skills above, use the corresponding Skill instead of Basic Tools. Skills are more efficient because they can perform batch operations in a single call.

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
