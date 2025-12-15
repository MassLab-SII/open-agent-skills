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

