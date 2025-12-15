---
name: papers-management
description: Tools for managing arXiv paper collections — organize legacy papers, group frequent authors, and locate specific math benchmarks.
---

# Papers Management Skill

提供三个针对论文集合的实用脚本：
1. **组织旧论文**：按年份整理 2023 及更早的论文并生成索引
2. **作者分组**：识别高频作者并按作者复制论文
3. **查找数学基准论文**：自动定位并重命名 math 基准相关论文

## 1) organize_legacy_papers.py
整理 2023 及更早的 HTML 论文到 `organized/<year>/`，生成索引与汇总。

### 功能
- 按 arXiv ID 年份（前两位）移动 2023 及更早论文
- 2024+ 论文与 `arxiv_2025.bib` 保持原位
- 每年生成 `INDEX.md`（表：ArXiv ID | Authors | Local Path，作者取前 3 个，>3 时末尾加 et al.）
- 生成 `organized/SUMMARY.md` 汇总各年

### 用法
```bash
python organize_legacy_papers.py /path/to/papers
```

## 2) author_folders.py
识别高频作者并复制论文：
- `frequent_authors/`：总论文数 ≥4 的作者
- `2025_authors/`：2025 年论文数 ≥3 的作者
- 作者目录名：小写，空格/逗号替换为下划线
- 复制（不移动）论文，保留原始文件

### 用法
```bash
python author_folders.py /path/to/papers
```

## 3) find_math_paper.py
寻找描述“数学基准，检验正确性并分析知识不足/泛化不足/机械记忆”的论文，并将对应 HTML 重命名为 `answer.html`。

### 用法
```bash
python find_math_paper.py /path/to/papers
```

### 说明
- 通过关键词评分选择最符合描述的论文
- 将选中的论文写为 `answer.html`（若存在同名则覆盖）

## 通用说明
- 所有脚本依赖 `utils.py` 的 `FileSystemTools` 进行文件操作
- 默认异步 I/O
- 不修改论文内容；仅移动/复制或写出新文件

