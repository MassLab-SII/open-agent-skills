#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow Builder Script
=======================

Build and deploy GitHub Actions workflows for CI/CD automation.
Supports creating various workflow types: CI, linting, issue automation, PR automation, and deployment.

Usage:
    python workflow_builder.py <command> <owner> <repo> [options]

Commands:
    ci-basic        Create basic CI workflow
    lint            Create linting workflow
    issue-auto      Create issue automation workflow
    pr-auto         Create PR automation workflow
    scheduled       Create scheduled workflow
    deployment      Create deployment status workflow

Examples:
    # Create basic CI workflow
    python workflow_builder.py ci-basic owner repo --trigger "push,pull_request" --branch main --node-version 18
    
    # Create linting workflow
    python workflow_builder.py lint owner repo --trigger "push,pull_request" --branch main
    
    # Create issue automation workflow
    python workflow_builder.py issue-auto owner repo
    
    # Create PR automation workflow
    python workflow_builder.py pr-auto owner repo
    
    # Create scheduled workflow
    python workflow_builder.py scheduled owner repo --cron "0 2 * * *" --script "npm run health-check"
    
    # Create deployment workflow
    python workflow_builder.py deployment owner repo
"""

import asyncio
import argparse
import sys
from typing import List, Optional

from utils import (
    GitHubTools,
    extract_sha_from_result,
    extract_pr_number,
    check_api_success,
    check_merge_success,
)


class WorkflowBuilder:
    """Build and deploy GitHub Actions workflows"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Workflow Builder.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def create_ci_basic_workflow(
        self,
        triggers: List[str],
        branch: str = "main",
        node_version: str = "18"
    ) -> bool:
        """
        Create a basic CI workflow.

        Args:
            triggers: List of trigger events (push, pull_request)
            branch: Target branch
            node_version: Node.js version

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            # Generate unique branch name using timestamp + random suffix to avoid conflicts
            import time
            import random
            timestamp = int(time.time())
            random_suffix = random.randint(1000, 9999)
            branch_name = f"ci/add-basic-workflow-{timestamp}-{random_suffix}"
            
            print(f"Step 1: Creating branch '{branch_name}'")
            branch_result = await gh.create_branch(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                from_branch=branch
            )
            if not self._check_success(branch_result):
                print(f"✗ Failed to create branch: {branch_result}")
                return False
            
            print(f"Step 2: Generating workflow content")
            workflow_content = self._generate_ci_basic_workflow(triggers, branch, node_version)
            
            print(f"Step 3: Pushing workflow file")
            files = [{"path": ".github/workflows/ci.yml", "content": workflow_content}]
            push_result = await gh.push_files(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                files=files,
                message="Add basic CI workflow"
            )
            if not self._check_success(push_result):
                print(f"✗ Failed to push workflow file: {push_result}")
                return False
            
            print(f"Step 4: Creating pull request")
            pr_result = await gh.create_pull_request(
                owner=self.owner,
                repo=self.repo,
                title="Add basic CI checks",
                head=branch_name,
                base=branch,
                body="## Summary\nAdds basic CI workflow for automated linting and testing."
            )
            
            pr_number = self._extract_pr_number(pr_result)
            if not pr_number:
                print(f"✗ Failed to create PR: {pr_result}")
                return False
            
            print(f"Step 5: Merging pull request #{pr_number}")
            merge_result = await gh.merge_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                merge_method="squash"
            )
            if not self._check_merge_success(merge_result):
                print(f"✗ Failed to merge PR: {merge_result}")
                return False
            
            print(f"✓ Successfully created basic CI workflow")
            return True

    async def create_lint_workflow(
        self,
        triggers: List[str],
        branch: str = "main"
    ) -> bool:
        """
        Create a linting CI workflow.

        Args:
            triggers: List of trigger events
            branch: Target branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            # Generate unique branch name using timestamp + random suffix to avoid conflicts
            import time
            import random
            timestamp = int(time.time())
            random_suffix = random.randint(1000, 9999)
            branch_name = f"ci/add-eslint-workflow-{timestamp}-{random_suffix}"
            
            print(f"Step 1: Creating branch '{branch_name}'")
            branch_result = await gh.create_branch(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                from_branch=branch
            )
            if not self._check_success(branch_result):
                print(f"✗ Failed to create branch: {branch_result}")
                return False
            
            print(f"Step 2: Generating workflow and config files")
            workflow_content = self._generate_lint_workflow(triggers, branch)
            eslint_config = self._generate_eslint_config()
            
            print(f"Step 3: Pushing files")
            # Only push workflow and config, not example files that might conflict
            files = [
                {"path": ".github/workflows/lint.yml", "content": workflow_content},
                {"path": ".eslintrc.json", "content": eslint_config},
            ]
            push_result = await gh.push_files(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                files=files,
                message="Add ESLint workflow for code quality enforcement"
            )
            if not self._check_success(push_result):
                print(f"✗ Failed to push files: {push_result}")
                return False
            
            print(f"Step 4: Creating pull request")
            pr_result = await gh.create_pull_request(
                owner=self.owner,
                repo=self.repo,
                title="Add ESLint workflow for code quality enforcement",
                head=branch_name,
                base=branch,
                body="## Summary\nAdds ESLint workflow and configuration.\n\n## Changes\n- Added .github/workflows/lint.yml\n- Added .eslintrc.json"
            )
            
            pr_number = self._extract_pr_number(pr_result)
            if not pr_number:
                print(f"✗ Failed to create PR: {pr_result}")
                return False
            print(f"Created PR #{pr_number}")
            
            print(f"Step 5: Merging pull request #{pr_number}")
            merge_result = await gh.merge_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                merge_method="squash"
            )
            if not self._check_merge_success(merge_result):
                print(f"✗ Failed to merge PR: {merge_result}")
                return False
            
            print(f"✓ Successfully created linting workflow")
            return True

    async def create_scheduled_workflow(
        self,
        cron: str,
        script: str,
        workflow_name: str = "Nightly Health Check",
        branch: str = "main"
    ) -> bool:
        """
        Create a scheduled workflow.

        Args:
            cron: Cron schedule expression
            script: Script command to run
            workflow_name: Workflow name
            branch: Target branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            # Generate unique branch name using timestamp + random suffix to avoid conflicts
            import time
            import random
            timestamp = int(time.time())
            random_suffix = random.randint(1000, 9999)
            branch_name = f"ci/add-scheduled-workflow-{timestamp}-{random_suffix}"
            
            print(f"Step 1: Creating branch '{branch_name}'")
            branch_result = await gh.create_branch(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                from_branch=branch
            )
            if not self._check_success(branch_result):
                print(f"✗ Failed to create branch: {branch_result}")
                return False
            
            print(f"Step 2: Generating workflow content")
            workflow_content = self._generate_scheduled_workflow(cron, script, workflow_name)
            
            print(f"Step 3: Pushing workflow file")
            files = [{"path": ".github/workflows/scheduled.yml", "content": workflow_content}]
            push_result = await gh.push_files(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                files=files,
                message=f"Add {workflow_name.lower()}"
            )
            if not self._check_success(push_result):
                print(f"✗ Failed to push workflow file: {push_result}")
                return False
            
            print(f"Step 4: Creating and merging pull request")
            pr_result = await gh.create_pull_request(
                owner=self.owner,
                repo=self.repo,
                title=f"Add {workflow_name.lower()}",
                head=branch_name,
                base=branch,
                body=f"## Summary\nAdds scheduled workflow: {workflow_name}"
            )
            
            pr_number = self._extract_pr_number(pr_result)
            if not pr_number:
                print(f"✗ Failed to create PR: {pr_result}")
                return False
            
            merge_result = await gh.merge_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                merge_method="squash"
            )
            if not self._check_merge_success(merge_result):
                print(f"✗ Failed to merge PR: {merge_result}")
                return False
            
            print(f"✓ Successfully created scheduled workflow")
            return True

    def _generate_ci_basic_workflow(self, triggers: List[str], branch: str, node_version: str) -> str:
        """Generate basic CI workflow YAML"""
        trigger_lines = []
        for trigger in triggers:
            if trigger == "push":
                trigger_lines.append(f"  push:\n    branches: [{branch}]")
            elif trigger == "pull_request":
                trigger_lines.append(f"  pull_request:\n    branches: [{branch}]")
        
        triggers_yaml = "\n".join(trigger_lines)
        
        return f'''name: Basic CI Checks

on:
{triggers_yaml}

jobs:
  quality-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '{node_version}'
      - run: npm ci
      - run: npm run lint
      - run: npm test
'''

    def _generate_lint_workflow(self, triggers: List[str], branch: str) -> str:
        """Generate linting workflow YAML"""
        trigger_lines = []
        for trigger in triggers:
            if trigger == "push":
                trigger_lines.append(f"  push:\n    branches: [{branch}]")
            elif trigger == "pull_request":
                trigger_lines.append(f"  pull_request:\n    branches: [{branch}]")
        
        triggers_yaml = "\n".join(trigger_lines)
        
        return f'''name: Code Linting

on:
{triggers_yaml}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: npm install -g eslint
      - run: eslint src/**/*.js
'''

    def _generate_scheduled_workflow(self, cron: str, script: str, name: str) -> str:
        """Generate scheduled workflow YAML"""
        return f'''name: {name}

on:
  workflow_dispatch:
  schedule:
    - cron: '{cron}'

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: {script}
'''

    def _generate_eslint_config(self) -> str:
        """Generate ESLint configuration"""
        return '''{
  "env": {
    "browser": true,
    "es2021": true,
    "node": true
  },
  "extends": [
    "eslint:recommended"
  ],
  "parserOptions": {
    "ecmaVersion": 12,
    "sourceType": "module"
  },
  "rules": {
    "no-unused-vars": "error",
    "no-console": "warn",
    "semi": ["error", "always"],
    "quotes": ["error", "single"]
  },
  "ignorePatterns": ["node_modules/", "dist/", "build/"]
}
'''

    def _generate_example_file_with_errors(self) -> str:
        """Generate example file with linting errors"""
        return '''// Example file with intentional linting errors
const unusedVariable = "test"
console.log("Hello World")
const message = "test"
'''

    def _generate_example_file_fixed(self) -> str:
        """Generate example file with errors fixed"""
        return '''// Example file with linting errors fixed
const message = 'test';
console.log(message);
'''

    def _extract_pr_number(self, result) -> int:
        """Extract PR number from result, handling MCP response format"""
        return extract_pr_number(result)

    def _extract_sha(self, result) -> str:
        """Extract SHA from get_file_contents result."""
        return extract_sha_from_result(result)

    def _check_success(self, result) -> bool:
        """Check if operation was successful, handling MCP response format"""
        return check_api_success(result)

    def _check_merge_success(self, result) -> bool:
        """Check if merge was successful, handling MCP response format"""
        return check_merge_success(result)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Build and deploy GitHub Actions workflows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create basic CI workflow
  python workflow_builder.py ci-basic owner repo --trigger "push,pull_request" --branch main
  
  # Create linting workflow
  python workflow_builder.py lint owner repo --trigger "push,pull_request" --branch main
  
  # Create scheduled workflow
  python workflow_builder.py scheduled owner repo --cron "0 2 * * *" --script "npm run health-check"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: ci-basic
    ci_parser = subparsers.add_parser("ci-basic", help="Create basic CI workflow")
    ci_parser.add_argument("owner", help="Repository owner")
    ci_parser.add_argument("repo", help="Repository name")
    ci_parser.add_argument("--trigger", required=True, help="Comma-separated triggers (push,pull_request)")
    ci_parser.add_argument("--branch", default="main", help="Target branch")
    ci_parser.add_argument("--node-version", default="18", help="Node.js version")
    
    # Command: lint
    lint_parser = subparsers.add_parser("lint", help="Create linting workflow")
    lint_parser.add_argument("owner", help="Repository owner")
    lint_parser.add_argument("repo", help="Repository name")
    lint_parser.add_argument("--trigger", required=True, help="Comma-separated triggers")
    lint_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: scheduled
    sched_parser = subparsers.add_parser("scheduled", help="Create scheduled workflow")
    sched_parser.add_argument("owner", help="Repository owner")
    sched_parser.add_argument("repo", help="Repository name")
    sched_parser.add_argument("--cron", required=True, help="Cron schedule")
    sched_parser.add_argument("--script", required=True, help="Script to run")
    sched_parser.add_argument("--name", default="Nightly Health Check", help="Workflow name")
    sched_parser.add_argument("--branch", default="main", help="Target branch")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    builder = WorkflowBuilder(args.owner, args.repo)
    
    try:
        if args.command == "ci-basic":
            triggers = [t.strip() for t in args.trigger.split(",")]
            success = await builder.create_ci_basic_workflow(
                triggers=triggers,
                branch=args.branch,
                node_version=args.node_version
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "lint":
            triggers = [t.strip() for t in args.trigger.split(",")]
            success = await builder.create_lint_workflow(
                triggers=triggers,
                branch=args.branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "scheduled":
            success = await builder.create_scheduled_workflow(
                cron=args.cron,
                script=args.script,
                workflow_name=args.name,
                branch=args.branch
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
