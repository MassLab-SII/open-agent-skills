---
name: github_content_editor
description: This skill enables direct file manipulation within GitHub repositories. It allows you to generate documentation (like ANSWER.md) and edit code files, handling the creating, updating, and pushing of files to the remote repository. Use this when you need to submit answers or apply fixes.
---

# GitHub Content Editor Skill

This skill allows for direct file manipulation within GitHub repositories:

1. **Document generation**: Create or update documentation files (ANSWER.md, CHANGELOG.md, etc.)
2. **File editing**: General-purpose file modification with search and replace

## 1. Document Generation

Create or update documentation files in the repository, including answer submission, changelog, and contributors list.

**Use when**: You need to submit answers, create documentation, or generate changelog/contributors from commit history.

### Example

```bash
# Submit an answer (creates/updates ANSWER.md)
python doc_gen.py answer owner repo --content "048cd3b..." --message "Submit answer"

# Specify a branch (if not default)
python doc_gen.py answer owner repo --content "answer text" --message "Submit" --branch "master"

# Create a generic document
python doc_gen.py create owner repo --path "docs/API.md" --content "# API Reference" --message "Add API docs"

# Generate a changelog from commit history
python doc_gen.py changelog owner repo --since "2024-01-01"

# Generate a contributors list
python doc_gen.py contributors owner repo --output "CONTRIBUTORS.md"
```

## 2. File Editing

Edit files, apply pattern-based fixes, or perform mass search-and-replace across multiple files.

**Use when**: You need to update configuration, fix bugs, rename variables, or update URLs across multiple files.

### Example

```bash
# Edit/Overwrite a file
python file_editor.py edit owner repo --path "src/config.py" --content "DEBUG = False" --message "Disable debug"

# Apply a specific fix (search and replace in a single file)
python file_editor.py apply_fix owner repo --path "src/bug.py" --pattern "if x = y:" --replacement "if x == y:" --message "Fix syntax"

# Mass edit (search and replace across multiple files)
python file_editor.py file_edit owner repo --query "http://old.com" --replacement "https://new.com" --message "Update URLs"
```
