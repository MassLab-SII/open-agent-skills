#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Generator Script
=======================

Generate CI/CD related configuration files for GitHub repositories.
Supports ESLint config, Issue templates, PR templates, and more.

Usage:
    python config_generator.py <command> <owner> <repo> [options]

Commands:
    eslint          Create ESLint configuration
    issue-templates Create Issue templates (bug, feature, maintenance)
    pr-template     Create Pull Request template

Examples:
    # Create ESLint configuration
    python config_generator.py eslint owner repo --extends "eslint:recommended" --rules "semi,quotes"
    
    # Create Issue templates
    python config_generator.py issue-templates owner repo --types "bug,feature,maintenance"
    
    # Create PR template
    python config_generator.py pr-template owner repo
"""

import asyncio
import argparse
import json
import sys
from typing import List, Optional

from utils import (
    GitHubTools,
    extract_sha_from_result,
    check_api_success,
)


class ConfigGenerator:
    """Generate CI/CD configuration files"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Config Generator.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def create_eslint_config(
        self,
        extends: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
        branch: str = "main"
    ) -> bool:
        """
        Create ESLint configuration file.

        Args:
            extends: List of ESLint configs to extend
            rules: List of rules to enable
            branch: Target branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Creating ESLint configuration for {self.owner}/{self.repo}")
            
            config_content = self._generate_eslint_config(extends, rules)
            
            # Check if file exists
            existing = await gh.get_file_contents(
                owner=self.owner,
                repo=self.repo,
                path=".eslintrc.json",
                ref=branch
            )
            sha = self._extract_sha(existing)
            
            result = await gh.create_or_update_file(
                owner=self.owner,
                repo=self.repo,
                path=".eslintrc.json",
                content=config_content,
                message="Add ESLint configuration",
                branch=branch,
                sha=sha
            )
            
            success = self._check_success(result)
            
            if success:
                print("✓ ESLint configuration created at .eslintrc.json")
            else:
                print(f"✗ Failed to create ESLint config: {result}")
            
            return success

    async def create_issue_templates(
        self,
        types: Optional[List[str]] = None,
        branch: str = "main"
    ) -> bool:
        """
        Create Issue templates. Will update existing templates if they exist.

        Args:
            types: List of template types (bug, feature, maintenance)
            branch: Target branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            if types is None:
                types = ["bug", "feature"]
            
            print(f"Creating Issue templates: {types}")
            
            files = []
            
            if "bug" in types:
                files.append({
                    "path": ".github/ISSUE_TEMPLATE/bug_report.md",
                    "content": self._generate_bug_template()
                })
            
            if "feature" in types:
                files.append({
                    "path": ".github/ISSUE_TEMPLATE/feature_request.md",
                    "content": self._generate_feature_template()
                })
            
            if "maintenance" in types:
                files.append({
                    "path": ".github/ISSUE_TEMPLATE/maintenance_report.md",
                    "content": self._generate_maintenance_template()
                })
            
            # push_files handles both create and update automatically
            # It will overwrite existing files, which is the expected behavior for templates
            result = await gh.push_files(
                owner=self.owner,
                repo=self.repo,
                branch=branch,
                files=files,
                message="Add/Update Issue templates"
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Created/Updated {len(files)} Issue templates")
                for f in files:
                    print(f"  - {f['path']}")
            else:
                print(f"✗ Failed to create Issue templates: {result}")
            
            return success

    async def create_pr_template(self, branch: str = "main") -> bool:
        """
        Create Pull Request template.

        Args:
            branch: Target branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Creating PR template for {self.owner}/{self.repo}")
            
            template_content = self._generate_pr_template()
            
            # Check if file exists
            existing = await gh.get_file_contents(
                owner=self.owner,
                repo=self.repo,
                path=".github/PULL_REQUEST_TEMPLATE.md",
                ref=branch
            )
            sha = self._extract_sha(existing)
            
            result = await gh.create_or_update_file(
                owner=self.owner,
                repo=self.repo,
                path=".github/PULL_REQUEST_TEMPLATE.md",
                content=template_content,
                message="Add Pull Request template",
                branch=branch,
                sha=sha
            )
            
            success = self._check_success(result)
            
            if success:
                print("✓ PR template created at .github/PULL_REQUEST_TEMPLATE.md")
            else:
                print(f"✗ Failed to create PR template: {result}")
            
            return success

    def _generate_eslint_config(self, extends: Optional[List[str]] = None, rules: Optional[List[str]] = None) -> str:
        """Generate ESLint configuration JSON"""
        extends = extends or ["eslint:recommended"]
        
        config = {
            "env": {
                "browser": True,
                "es2021": True,
                "node": True
            },
            "extends": extends,
            "parserOptions": {
                "ecmaVersion": 12,
                "sourceType": "module"
            },
            "rules": {
                "no-unused-vars": "error",
                "no-console": "warn"
            },
            "ignorePatterns": ["node_modules/", "dist/", "build/"]
        }
        
        if rules:
            for rule in rules:
                if rule == "semi":
                    config["rules"]["semi"] = ["error", "always"]
                elif rule == "quotes":
                    config["rules"]["quotes"] = ["error", "single"]
                elif rule == "indent":
                    config["rules"]["indent"] = ["error", 2]
                elif rule == "no-var":
                    config["rules"]["no-var"] = "error"
                elif rule == "prefer-const":
                    config["rules"]["prefer-const"] = "error"
        
        return json.dumps(config, indent=2)

    def _generate_bug_template(self) -> str:
        """Generate bug report template"""
        return '''---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
What actually happened.

## Screenshots
If applicable, add screenshots to help explain your problem.

## Environment
- OS: [e.g. macOS, Windows, Linux]
- Browser: [e.g. Chrome, Safari]
- Version: [e.g. 1.0.0]

## Additional Context
Add any other context about the problem here.
'''

    def _generate_feature_template(self) -> str:
        """Generate feature request template"""
        return '''---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Problem Statement
A clear and concise description of what the problem is.

## Proposed Solution
A clear and concise description of what you want to happen.

## Alternatives Considered
A clear and concise description of any alternative solutions or features you've considered.

## Additional Context
Add any other context or screenshots about the feature request here.

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3
'''

    def _generate_maintenance_template(self) -> str:
        """Generate maintenance report template"""
        return '''---
name: Maintenance Report
about: Report maintenance tasks or technical debt
title: '[MAINTENANCE] '
labels: maintenance
assignees: ''
---

## Maintenance Type
- [ ] Dependency Update
- [ ] Code Refactoring
- [ ] Documentation Update
- [ ] Performance Optimization
- [ ] Security Patch
- [ ] Other

## Description
A clear and concise description of the maintenance task.

## Affected Areas
List the files, modules, or components affected.

## Priority
- [ ] Critical (blocking other work)
- [ ] High (should be done soon)
- [ ] Medium (can wait for next sprint)
- [ ] Low (nice to have)

## Additional Context
Add any other context about the maintenance task here.
'''

    def _generate_pr_template(self) -> str:
        """Generate PR template"""
        return '''## Summary
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Fixes #(issue number)

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
Describe the tests that you ran to verify your changes.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
'''

    def _extract_sha(self, result) -> Optional[str]:
        """Extract SHA from result"""
        return extract_sha_from_result(result)

    def _check_success(self, result) -> bool:
        """Check if operation was successful"""
        return check_api_success(result)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate CI/CD configuration files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create ESLint configuration
  python config_generator.py eslint owner repo --extends "eslint:recommended" --rules "semi,quotes"
  
  # Create Issue templates
  python config_generator.py issue-templates owner repo --types "bug,feature,maintenance"
  
  # Create PR template
  python config_generator.py pr-template owner repo
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: eslint
    eslint_parser = subparsers.add_parser("eslint", help="Create ESLint configuration")
    eslint_parser.add_argument("owner", help="Repository owner")
    eslint_parser.add_argument("repo", help="Repository name")
    eslint_parser.add_argument("--extends", help="Comma-separated configs to extend (default: eslint:recommended)")
    eslint_parser.add_argument("--rules", help="Comma-separated rules to enable (semi,quotes,indent,no-var,prefer-const)")
    eslint_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: issue-templates
    issue_parser = subparsers.add_parser("issue-templates", help="Create Issue templates")
    issue_parser.add_argument("owner", help="Repository owner")
    issue_parser.add_argument("repo", help="Repository name")
    issue_parser.add_argument("--types", default="bug,feature", 
                             help="Comma-separated template types: bug,feature,maintenance")
    issue_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: pr-template
    pr_parser = subparsers.add_parser("pr-template", help="Create PR template")
    pr_parser.add_argument("owner", help="Repository owner")
    pr_parser.add_argument("repo", help="Repository name")
    pr_parser.add_argument("--branch", default="main", help="Target branch")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    generator = ConfigGenerator(args.owner, args.repo)
    
    try:
        if args.command == "eslint":
            extends = [e.strip() for e in args.extends.split(",")] if args.extends else None
            rules = [r.strip() for r in args.rules.split(",")] if args.rules else None
            success = await generator.create_eslint_config(
                extends=extends,
                rules=rules,
                branch=args.branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "issue-templates":
            types = [t.strip() for t in args.types.split(",")]
            success = await generator.create_issue_templates(
                types=types,
                branch=args.branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "pr-template":
            success = await generator.create_pr_template(branch=args.branch)
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
