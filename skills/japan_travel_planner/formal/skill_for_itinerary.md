# Daily Itinerary Overview Skills

两个通用、可复用的Notion skills，用于创建和填充旅行行程概览页面。

## 概述

这两个skills配合使用，可以快速创建一个结构化的旅行行程概览页面，自动从Notion数据库查询活动数据、按日期分组、并填充到页面中。

### 核心特性

- **模块化设计**: 两个独立的skills，各自承担清晰的职责
- **通用性强**: 不限于Japan Travel Planner，可用于任何相似场景
- **LLM友好**: 支持LLM动态提供文本参数（如emoji前缀）
- **鲁棒性**: 完整的错误处理和日志输出

---

## Skill 1: CreateChildPageByName

**文件**: `skills/japan_travel_planner/formal/create_child_page_by_name.py`

### 功能

在指定的父页面下创建一个新的子页面。

### MCP调用

| 顺序 | API | 用途 |
|------|-----|------|
| 1 | API-post-search | 搜索父页面 |
| 2 | API-post-pages | 创建子页面 |

### 参数

```
python3 create_child_page_by_name.py <parent_page_name> <child_page_title>
```

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| parent_page_name | string | ✓ | 父页面的名称 |
| child_page_title | string | ✓ | 要创建的子页面标题 |

### 示例

```bash
python3 create_child_page_by_name.py "Japan Travel Planner" "📅 Daily Itinerary Overview"
```

### 输出

```json
{
  "success": true,
  "page_id": "2d45d1cf-e7c4-8103-a2e5-c56f9913d1a2",
  "parent_id": "2d45d1cf-e7c4-80e1-b480-c87ddb21d4ec",
  "title": "📅 Daily Itinerary Overview"
}
```

### 应用场景

- 创建旅行概览页面
- 创建项目子任务页面
- 创建部门或团队的总结页面
- 任何需要在现有页面下创建新页面的场景

---

## Skill 2: QueryGroupAndPopulate

**文件**: `skills/japan_travel_planner/formal/query_group_and_populate.py`

### 功能

从Notion数据库查询项目，按指定属性分组，并将其格式化为blocks填充到页面中。

### MCP调用

| 顺序 | API | 用途 |
|------|-----|------|
| 1 | API-post-search | 搜索数据库 |
| 2 | API-post-database-query | 查询数据库所有项 |
| 3 | API-patch-block-children | 添加blocks到页面 |

### 参数

```
python3 query_group_and_populate.py <page_id> <database_name> <grouping_property> <page_title> [options]
```

#### 位置参数

| 参数 | 说明 |
|------|------|
| page_id | 要填充的页面ID |
| database_name | 数据库名称 |
| grouping_property | 按此属性分组（如 "Day"、"Category"、"Location"） |
| page_title | 页面标题（会作为heading_1添加） |

#### 选项参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --item-property | "Name" | 项目名称属性字段名 |
| --location-property | 无 | 附加信息属性字段名（如城市、位置） |
| --status-property | 无 | checkbox属性字段名（用于追踪完成状态） |
| --groups-order | 无 | 分组显示顺序（影响页面展示顺序和统计范围） |
| --group-prefixes | 无 | 分组名称前缀（格式：group_name prefix group_name prefix ...） |
| --json | 无 | 以JSON格式输出结果 |

### 示例

#### 基础用法

```bash
python3 query_group_and_populate.py \
  "2d45d1cf-e7c4-8103-a2e5-c56f9913d1a2" \
  "Travel Itinerary" \
  "Day" \
  "📅 Daily Itinerary Overview"
```

#### 完整用法（推荐）

```bash
python3 query_group_and_populate.py \
  "2d45d1cf-e7c4-8103-a2e5-c56f9913d1a2" \
  "Travel Itinerary" \
  "Day" \
  "📅 Daily Itinerary Overview" \
  --item-property "Name" \
  --location-property "Group" \
  --status-property "Visited" \
  --groups-order "Day 1" "Day 2" "Day 3" \
  --group-prefixes "Day 1" "🌅" "Day 2" "🌆" "Day 3" "🌃"
```

#### JSON输出

```bash
python3 query_group_and_populate.py \
  "2d45d1cf-e7c4-8103-a2e5-c56f9913d1a2" \
  "Travel Itinerary" \
  "Day" \
  "Daily Itinerary Overview" \
  --json
```

### 输出

#### 文本格式输出

```
======================================================================
Query, Group and Populate Page Skill
======================================================================

📍 Step 1: Searching for database: Travel Itinerary
------------------------------------------------------------
✓ Found database
  ID: 2d45d1cf-e7c4-81be-a7f0-000b45...
  Name: Travel Itinerary

📍 Step 2: Querying database for items
------------------------------------------------------------
✓ Retrieved 73 items

📍 Step 3: Organizing items by 'Day'
------------------------------------------------------------
✓ Organized into 8 groups
  Completed items: 22/73
  - Day 1: 9 items
  - Day 2: 9 items
  - Day 3: 11 items
  ...

📍 Step 4: Building page blocks
------------------------------------------------------------
✓ Built 35 blocks

📍 Step 5: Adding blocks to page
------------------------------------------------------------
✓ Added 35 blocks to page

======================================================================
RESULT SUMMARY
======================================================================
✅ Success
   Database ID: 2d45d1cf-e7c4-81be-a7f0-000b453c00a7
   Total Items: 73
   Completed: 22
   Blocks Added: 35
   Groups Processed:
     - Day 1: 9 items
     - Day 2: 9 items
     - Day 3: 11 items
     - Day 4: 8 items
     - Day 5: 5 items
     - Day 6: 11 items
     - Day 7: 6 items
     - Day 8: 5 items
```

#### JSON格式输出

```json
{
  "success": true,
  "database_id": "2d45d1cf-e7c4-81be-a7f0-000b453c00a7",
  "total_items": 73,
  "completed_items": 22,
  "blocks_added": 35,
  "groups_processed": {
    "Day 1": 9,
    "Day 2": 9,
    "Day 3": 11,
    "Day 4": 8,
    "Day 5": 5,
    "Day 6": 11,
    "Day 7": 6,
    "Day 8": 5
  },
  "errors": []
}
```

### 生成的页面结构

当成功执行后，页面会自动创建以下结构：

```
📅 Daily Itinerary Overview (heading_1)
📊 Trip Summary (heading_2)
Total activities visited (from Day 1 to Day 3): 8 (paragraph)
🌅 Day 1 (heading_2)
  ☐ Umeda Sky Building - Osaka (to_do)
  ☐ Riceball Gori-chan Namba - Osaka (to_do)
  ☑ Unagi Kushiyaki Idumo - Osaka (to_do)
  ...
🌆 Day 2 (heading_2)
  ☐ CAFE ANNON カフェアンノン なんば - Osaka (to_do)
  ☑ Studio Ghibli Store - Osaka (to_do)
  ...
🌃 Day 3 (heading_2)
  ...
```

### 智能特性

#### 1. 分组范围智能计算

当指定 `--groups-order` 时，完成统计只计算这些指定分组的项目：

```bash
# 只显示 Day 1-3，且统计数只算这三天的完成项
--groups-order "Day 1" "Day 2" "Day 3"
```

这确保了summary中的统计数字与页面显示内容对应。

#### 2. 前缀文本由LLM控制

`--group-prefixes` 参数允许LLM动态提供分组标签：

```bash
# 使用emoji前缀
--group-prefixes "Day 1" "🌅" "Day 2" "🌆" "Day 3" "🌃"

# 或使用文本前缀
--group-prefixes "Day 1" "Morning:" "Day 2" "Afternoon:" "Day 3" "Evening:"

# 或混合使用
--group-prefixes "Day 1" "📍 Morning" "Day 2" "🍽️ Afternoon"
```

#### 3. 灵活的属性映射

支持多种Notion属性类型的自动提取：

- **title**: 从富文本或标题字段提取项目名称
- **select**: 从单选字段提取分类信息
- **checkbox**: 自动追踪完成状态
- **rich_text**: 从富文本字段提取附加信息

#### 4. 自动格式化

项目显示格式为：`{item_name} - {location_property}`

例如：
```
Osaka Castle - Osaka
Studio Ghibli Store - Osaka
Namba Yasaka Shrine - Osaka
```

### 应用场景

- **旅行规划**: 创建行程概览，按天组织活动
- **项目管理**: 创建项目总结，按阶段组织任务
- **事件组织**: 创建活动日程，按时间或地点分组
- **教学课程**: 创建课程大纲，按周或模块分组
- **数据聚合**: 任何需要汇总和展示分类数据的场景

---

## 使用工作流

### 场景 1: 创建旅行行程概览

```bash
# Step 1: 创建页面
python3 create_child_page_by_name.py \
  "Japan Travel Planner" \
  "📅 Daily Itinerary Overview"

# Step 2: 填充内容（使用上一步返回的page_id）
python3 query_group_and_populate.py \
  "2d45d1cf-e7c4-8103-a2e5-c56f9913d1a2" \
  "Travel Itinerary" \
  "Day" \
  "📅 Daily Itinerary Overview" \
  --item-property "Name" \
  --location-property "Group" \
  --status-property "Visited" \
  --groups-order "Day 1" "Day 2" "Day 3" \
  --group-prefixes "Day 1" "🌅" "Day 2" "🌆" "Day 3" "🌃"
```

### 场景 2: 创建项目总结页面

```bash
# Step 1: 创建页面
python3 create_child_page_by_name.py \
  "2025 Q1 Projects" \
  "📊 Project Summary"

# Step 2: 填充内容
python3 query_group_and_populate.py \
  "page-id-from-step1" \
  "Project Tasks" \
  "Status" \
  "📊 Project Summary" \
  --item-property "Task Name" \
  --location-property "Owner" \
  --status-property "Completed" \
  --groups-order "In Progress" "Completed" \
  --group-prefixes "In Progress" "🔄" "Completed" "✅"
```

### 场景 3: 创建课程大纲

```bash
# Step 1: 创建页面
python3 create_child_page_by_name.py \
  "Python Course" \
  "📚 Course Outline"

# Step 2: 填充内容
python3 query_group_and_populate.py \
  "page-id-from-step1" \
  "Course Modules" \
  "Week" \
  "📚 Course Outline" \
  --item-property "Topic" \
  --location-property "Module" \
  --status-property "Published" \
  --groups-order "Week 1" "Week 2" "Week 3" "Week 4" \
  --group-prefixes "Week 1" "📖" "Week 2" "📖" "Week 3" "📖" "Week 4" "📖"
```

---

## 技术细节

### 数据库对象类型处理

Skill 2 自动处理两种Notion API返回的数据库对象类型：
- `data_source`: 数据库的搜索结果格式
- `database`: 另一种数据库格式

代码会自动识别并使用其中任何一种。

### 属性提取逻辑

对于每个项目，skill会扫描所有属性并根据字段名和类型提取信息：

```python
if property_type == "title" and prop_type == "title":
    # 从标题字段提取名称
    
elif property_type == "text" and prop_type == "rich_text":
    # 从富文本提取信息
    
elif property_type == "select" and prop_type == "select":
    # 从单选提取信息
    
elif property_type == "checkbox" and prop_type == "checkbox":
    # 提取完成状态
```

### 块的生成顺序

1. **heading_1**: 页面标题
2. **heading_2**: "📊 Trip Summary"
3. **paragraph**: 统计摘要
4. **heading_2** × N: 每个分组的标题
5. **to_do** × M: 每个分组下的项目（checkbox状态与数据库同步）

---

## 错误处理

两个skills都包含完整的错误处理：

```
❌ 数据库未找到
❌ 页面未找到
❌ API调用失败
❌ 属性提取失败
```

所有错误都会被捕获、记录并包含在返回结果中。

---

## 依赖

```
python >= 3.8
notion-client >= 2.0
aiohttp >= 3.8
python-dotenv >= 0.19
```

---

## 环境配置

需要设置 `EVAL_NOTION_API_KEY` 环境变量：

```bash
export EVAL_NOTION_API_KEY="ntn_xxxxxxxxxxxxx"
```

或在执行时传入：

```bash
EVAL_NOTION_API_KEY="ntn_xxxxxxxxxxxxx" python3 skill.py ...
```

---

## 总结

这两个skills展示了如何通过**模块化设计**和**参数化配置**来创建通用、可复用的Notion自动化工具。它们不仅解决了特定任务（Daily Itinerary Overview），也为LLM提供了灵活的接口来适应各种相似的场景。
