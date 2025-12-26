#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Verification Script
==========================

Interactive script to verify each skill one by one.
Run this script and follow the prompts to test each skill.
"""

import os
import subprocess
import sys

# Get the directory where this script is located
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))

# Default test environment path (adjust if needed)
DEFAULT_TEST_ENV = "/Users/zhaoji/project/mcpmark/.mcpmark_backups/test_environments"

def run_command(cmd, description):
    """Run a command and display output."""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"命令: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"[stderr]: {result.stderr}", file=sys.stderr)
    
    print(f"\n退出码: {result.returncode}")
    return result.returncode == 0

def wait_for_user():
    """Wait for user to press Enter to continue."""
    input("\n按 Enter 继续下一个测试，或按 Ctrl+C 退出...")

def test_list_all_files(test_env):
    """Test list_all_files.py"""
    print("\n" + "#"*60)
    print("# Skill 1: list_all_files.py - 列出目录下所有文件")
    print("#"*60)
    
    test_dir = os.path.join(test_env, "folder_structure/complex_structure")
    script = os.path.join(SKILL_DIR, "list_all_files.py")
    
    cmd = f"python {script} {test_dir}"
    run_command(cmd, "列出文件")
    
    cmd = f"python {script} {test_dir} | wc -l"
    run_command(cmd, "统计文件总数")
    
    wait_for_user()

def test_file_statistics(test_env):
    """Test file_statistics.py"""
    print("\n" + "#"*60)
    print("# Skill 2: file_statistics.py - 文件统计")
    print("#"*60)
    
    test_dir = os.path.join(test_env, "folder_structure")
    script = os.path.join(SKILL_DIR, "file_statistics.py")
    
    cmd = f"python {script} {test_dir}"
    run_command(cmd, "统计文件、文件夹数量和总大小")
    
    wait_for_user()

def test_gradebased_score(test_env):
    """Test gradebased_score.py"""
    print("\n" + "#"*60)
    print("# Skill 3: gradebased_score.py - 成绩等级计算")
    print("#"*60)
    
    test_dir = os.path.join(test_env, "student_database")
    script = os.path.join(SKILL_DIR, "gradebased_score.py")
    output_dir = "/tmp/skill_test_output"
    
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = f"python {script} {test_dir} --output-dir {output_dir}"
    run_command(cmd, "计算学生成绩等级")
    
    print("\n--- student_grades.csv (前10行) ---")
    run_command(f"head -10 {output_dir}/student_grades.csv", "查看成绩CSV")
    
    print("\n--- grade_summary.txt ---")
    run_command(f"cat {output_dir}/grade_summary.txt", "查看成绩统计")
    
    wait_for_user()

def test_duplicate_name(test_env):
    """Test duplicate_name.py"""
    print("\n" + "#"*60)
    print("# Skill 4: duplicate_name.py - 重名查找")
    print("#"*60)
    
    test_dir = os.path.join(test_env, "student_database")
    script = os.path.join(SKILL_DIR, "duplicate_name.py")
    output_file = "/tmp/skill_test_output/namesake.txt"
    
    cmd = f"python {script} {test_dir} --output {output_file}"
    run_command(cmd, "查找重名学生")
    
    print("\n--- namesake.txt ---")
    run_command(f"cat {output_file}", "查看重名结果")
    
    wait_for_user()

def test_extract_authors(test_env):
    """Test extract_authors.py"""
    print("\n" + "#"*60)
    print("# Skill 5: extract_authors.py - 提取论文作者")
    print("#"*60)
    
    test_dir = os.path.join(test_env, "papers")
    script = os.path.join(SKILL_DIR, "extract_authors.py")
    
    cmd = f"python {script} {test_dir} | head -40"
    run_command(cmd, "提取HTML论文作者（前40行）")
    
    wait_for_user()

def main():
    print("="*60)
    print("       Skill 验证脚本")
    print("="*60)
    

    test_env = DEFAULT_TEST_ENV
    
    if not os.path.isdir(test_env):
        print(f"错误: 测试环境目录不存在: {test_env}")
        sys.exit(1)
    
    print(f"\n使用测试环境: {test_env}")
    
    # Run tests
    try:
        test_gradebased_score(test_env)
        test_duplicate_name(test_env)
        test_extract_authors(test_env)
        
        print("\n" + "="*60)
        print("       所有测试完成!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n测试中断。")
        sys.exit(0)

if __name__ == '__main__':
    main()
