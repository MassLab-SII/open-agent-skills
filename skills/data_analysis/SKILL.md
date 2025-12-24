---
name: data-analysis
description: Data analysis and reporting tools. Includes music analysis with popularity scoring, file statistics(Count files, folders, and calculate total size), student grade calculation from student database, and duplicate name detection in databases.
---

# Data Analysis Skill

This skill provides data analysis and reporting tools:

1. **Music analysis**: Generate popularity reports from music data
2. **File statistics**: Count files, folders, and calculate total size
3. **Grade-based score**: Calculate student grades from database
4. **Duplicate name finder**: Find duplicate names in student database

## Important Notes

- **Do not use other bash commands**: Do not attempt to use general bash commands or shell operations like cat, ls.
- **Use relative paths**: Use paths relative to the working directory (e.g., `./folder/file.txt` or `folder/file.txt`).

---

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
python music_report.py ./music

# Use a custom output filename
python music_report.py ./music --output my_report.txt

# Use custom weights for the popularity formula
python music_report.py ./music --rating-weight 0.5 --play-count-weight 0.3 --year-weight 0.2
```

---

## 2. File Statistics

Generate file statistics for a directory: total files, folders, and size.

### Features

- Count total files (excluding .DS_Store)
- Count total folders
- Calculate total size in bytes (includes .DS_Store for size only)

### Example

```bash
python file_statistics.py .
```

---

## 3. Grade-Based Score

Calculate student grades from student database and generate output files.

### Features

- Read all basic_info.txt files from student folders
- Extract chinese, math, english scores
- Calculate grades: A(90+), B(80-89), C(70-79), D(60-69), F(<60)
- Generate student_grades.csv and grade_summary.txt

### Example

```bash
python gradebased_score.py ./student_database

# Specify output directory
python gradebased_score.py ./student_database --output-dir ./output
```

### Output Files

1. **student_grades.csv**: student_id, name, chinese_score, chinese_grade, math_score, math_grade, english_score, english_grade
2. **grade_summary.txt**: Total students, A/B/C/D/F counts per subject, pass/fail counts

---

## 4. Duplicate Name Finder

Find duplicate names in student database.

### Features

- Scan all student folders
- Extract names from basic_info.txt
- Identify names that appear more than once
- Generate namesake.txt

### Example

```bash
python duplicate_name.py ./student_database

# Specify output file
python duplicate_name.py ./student_database --output ./namesake.txt
```

### Output Format

```
name: xxx
count: xxx
ids: xxx, xxx, ...

name: yyy
count: yyy
ids: yyy, yyy, ...
```
