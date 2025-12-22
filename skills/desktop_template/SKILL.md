---
name: desktop-template-utilities
description: Tools for organizing desktop templates, computing personal budgets, and consolidating contact information.
---

# Desktop Template Utilities

本技能集提供三个工具，用于桌面模板的整理、预算计算和联系人整合：

1. **文件整理**：按类别归档桌面文件
2. **预算计算**：提取个人生活支出并汇总
3. **联系人整合**：汇总联系人信息并回答指定问题

## 1) 文件整理（file_arrangement.py）

按规则将文件移动到统一的分类目录：
- work/：工作、研究、项目相关
- life/：个人生活相关
- archives/：归档、历史、备份、税务等
- temp/：临时/草稿
- others/：无法归类的文件

### 用法
```bash
python file_arrangement.py /path/to/desktop_template
```

### 特性
- 自动创建分类目录
- 依据文件路径和关键词进行分类
- 不修改文件名，仅移动位置

## 2) 预算计算（budget_computation.py）

扫描桌面模板，提取个人生活支出，生成 `total_budget.txt`：
- 每行：`file_path;price`（相对路径，保留两位小数）
- 最后一行：总和（两位小数）

### 用法
```bash
python budget_computation.py /path/to/desktop_template
python budget_computation.py /path/to/desktop_template --output my_budget.txt
```

### 特性
- 排除工作/项目相关路径
- 解析文件中的数值作为支出条目
- 汇总总支出

## 3) 联系人整合（contact_information.py）

扫描所有文件，提取联系人信息并生成 `contact_info.csv`，同时回答：
> Charlie Davis 的职业/工作是什么？

输出：
- `contact_info.csv`：列包含 Name, Email, Phone 以及检测到的其他字段
- `answer.txt`：上述问题的回答（若无法确定则为 Unknown）

### 用法
```bash
python contact_information.py /path/to/desktop_template
```

### 特性
- 支持 CSV/文本的联系人信息提取
- 动态并集所有字段，自动生成表头
- 生成回答文件 answer.txt

## 通用说明
- 所有脚本依赖 `utils.py` 中的 `FileSystemTools` 进行文件操作
- 默认使用异步 I/O
- 不会修改文件内容，只会读取或移动/写入新文件


