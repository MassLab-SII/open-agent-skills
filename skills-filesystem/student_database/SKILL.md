---
name: student-database-tools
description: 工具集用于学生库的重复名检测、英语人才筛选、成绩计算。
---

# Student Database Tools

三项常用操作：
1. **重复名检测**：输出 namesake.txt
2. **英语人才筛选**：基于推荐等级与 TOEFL 生成 qualified_students.txt
3. **成绩计算**：生成 student_grades.csv 与 grade_summary.txt

## 1) duplicate_name.py
扫描全部 basic_info.txt，找出同名学生及其 ID。

### 输出
```
name: xxx
count: n
ids: id1, id2, ...

(空一行分隔)
```

### 用法
```bash
python duplicate_name.py /path/to/student_database
```

## 2) english_talent.py
筛选满足：
1) recommendation_letter.txt 评级为 S 或 A  
2) TOEFL >= 100  

### 输出
qualified_students.txt
```
name: xxx
id: xxx
email: xxx

...
```

### 用法
```bash
python english_talent.py /path/to/student_database
```

## 3) gradebased_score.py
按分数映射 A(90+), B(80-89), C(70-79), D(60-69), F(<60)。

### 输出
- student_grades.csv:  
  `student_id,name,chinese_score,chinese_grade,math_score,math_grade,english_score,english_grade`
- grade_summary.txt: 每科 A/B/C/D/F 统计与通过(A/B/C)/不通过(D/F)人数，总人数。

### 用法
```bash
python gradebased_score.py /path/to/student_database
```

## 通用说明
- 依赖 `utils.py` 的 `FileSystemTools` 进行文件操作（异步）
- 仅读取/写入或移动新文件，不修改原有内容
- 关键字段：basic_info.txt 中的 name/id/email/chinese/math/english/toefl；recommendation_letter.txt 的等级

