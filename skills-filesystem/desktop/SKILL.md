---
name: desktop-file-management
description: This skill provides tools for managing and analyzing desktop files. It includes music analysis reports, project organization, and timeline extraction. Use this when you need to organize scattered files, analyze data, or extract temporal information.
---

# Desktop File Management Skill

This skill provides tools for desktop file management and analysis:

1. **Music analysis**: Generate popularity reports from music data
2. **Project organization**: Structure project files into organized hierarchies
3. **Timeline extraction**: Extract and organize temporal information from files

## 1. Music Analysis Report

Analyzes music data from multiple artists, calculates popularity scores using a weighted formula, and generates a detailed analysis report.

### Features

- Reads song data from multiple artist directories
- Supports CSV and TXT file formats
- Calculates popularity scores using:
  - `popularity_score = (rating × 0.4) + (play_count_normalized × 0.4) + (year_factor × 0.2)`
- Sorts songs by popularity (descending)
- Generates a 25-line report with top songs

### Example

```bash
# Generate music analysis report (default output: music_analysis_report.txt)
python music_report.py /path/to/directory

# Use a custom output filename
python music_report.py /path/to/directory --output my_report.txt
```

### Report Format

- Lines 1-20: All songs with scores (`songname:score`)
- Lines 21-25: Top 5 song names only

## 2. Project Organization

Organizes scattered project files into a structured directory hierarchy based on file types and content categories.

### Features

- Creates organized directory structure with 3 main categories
- Moves Python files to `experiments/ml_projects/`
- Moves CSV files to `experiments/data_analysis/`
- Categorizes Markdown files by content:
  - Learning-related → `learning/resources/`
  - Entertainment-related → `personal/entertainment/`
  - Collection-related → `personal/collections/`
- Generates project structure documentation

### Example

```bash
# Organize projects (default output: organized_projects)
python organize_projects.py /path/to/directory

# Use a custom output directory name
python organize_projects.py /path/to/directory --output-dir my_projects
```

### Directory Structure

```
organized_projects/
├── experiments/
│   ├── ml_projects/        # Python scripts
│   └── data_analysis/      # CSV files
├── learning/
│   ├── progress_tracking/  # Placeholder
│   └── resources/          # Learning docs
└── personal/
    ├── entertainment/      # Entertainment docs
    └── collections/        # Collection docs
```

## 3. Timeline Extraction

Extracts timeline information from files and generates a chronologically sorted timeline report.

### Features

- Recursively scans all files
- Extracts dates in multiple formats:
  - YYYY-MM-DD
  - Month YYYY (uses 1st day)
  - MM/DD/YYYY
- Filters by specific year
- Removes duplicate dates per file
- Sorts chronologically
- Generates timeline.txt report

### Example

```bash
# Extract 2024 timeline (default)
python extract_timeline.py /path/to/directory

# Extract timeline for a specific year
python extract_timeline.py /path/to/directory --year 2023

# Use a custom output filename
python extract_timeline.py /path/to/directory --output my_timeline.txt
```

### Output Format

Each line: `file_path:YYYY-MM-DD`

### Rules

- If only month is shown, use the 1st day of that month
- If only year is shown, skip it
- If multiple tasks on same date in same file, count only once
- Sort by chronological order

