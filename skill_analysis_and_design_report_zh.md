# GitHub 技能设计分析与验证报告

## 1. 概述 (Overview)
本报告总结了对 `github_detective`（GitHub 侦探）和 `github_content_editor`（GitHub 内容编辑器）这两个技能的验证结果。验证过程基于 GitHub 交互任务（具体为 `missing-semester` and `build_your_own_x` benchmarks）的真实成功执行轨迹。

**目标：** 验证当前的技能设计是否有效解决了在原生 MCP 工具使用中观察到的挑战和低效问题。

## 2. 执行日志中的关键发现 (Key Findings)

通过分析成功的任务日志（在这些任务中 Agent 使用了原生的 MCP 工具），我们发现了两个关键痛点：

### 2.1. "暴力"搜索的低效性 (Inefficiency of "Brute Force" Search)
*   **观察 (Observation):** 在 `missing-semester__find_legacy_name` 任务中，模型不得不手动逐个检查 **超过 20 次** 提交，以寻找特定的变更（一个旧名称/域名）。
*   **机制 (Mechanism):** Agent 在一个循环中反复调用 `get_commit`，一次检查一条提交信息。
*   **影响 (Impact):** 极大地浪费了步骤（Steps）和 Token；造成高延迟；存在耗尽上下文窗口（Context Window）的风险。

### 2.2. 原生 Git 操作的脆弱性 (Brittleness of Raw Git Operations)
*   **观察 (Observation):** 在 `build_your_own_x` 任务中，模型经常遇到 `failed to resolve git reference`（无法解析 Git 引用）的错误。
*   **机制 (Mechanism):** 模型试图直接使用原始的 Commit SHA 作为引用（Ref）来进行 `get_file_contents` 读取或文件创建操作。虽然这在 Git 中通常是合法的，但底层的 MCP Server 或特定的仓库状态对此处理不一致，导致崩溃或 API 错误。
*   **影响 (Impact):** 导致任务失败或被迫进入重试循环；自动化过程缺乏鲁棒性。

## 3. 技能设计解决方案 (Skill Design Solutions)

我们需要设计的技能正是为了直接填补这些已识别的空白。

### 3.1. GitHub 侦探技能 (`github_detective`)

该技能旨在将复杂的信息检索工作从 LLM 的上下文中卸载到服务器端脚本上。

#### **`find_commit.py`** (搜索引擎)
*   **解决问题:** "暴力"搜索的低效性。
*   **核心能力:** 实现了 `--query` 参数，支持正则表达式搜索。
*   **收益:** Agent 无需进行 20 多次往返交互，只需发出 **一条指令**：
    ```bash
    python find_commit.py owner repo --query "domain|legacy|rename" --author "AuthorName"
    ```
    脚本会高效地过滤历史记录，并仅返回相关的提交。

#### **`blame_analysis.py`** (深度追踪)
*   **解决问题:** 追踪特定代码行或功能（如 "RAG support"）是 *何时* 引入的困难。
*   **核心能力:** 递归地追踪 `git blame` 历史（配合新修复的 `--max-depth` 参数）以找到起源提交。
*   **收益:** 自动化了 "检查旧版本 -> 检查 blame -> 重复" 这一认知负担。

### 3.2. GitHub 内容编辑器技能 (`github_content_editor`)

该技能侧重于对仓库进行安全、标准化的修改。

#### **`doc_gen.py`** (安全写入器)
*   **解决问题:** "Git 引用" 的脆弱性和缺乏标准化。
*   **核心能力:** 封装了创建特定文件类型（`answer`, `changelog`, `generic`）的最佳实践工作流。
    *   **`answer` 命令:** 专为提交答案的任务设计。它自动处理底层的 Git 管道操作（`create_tree` -> `create_commit`）。
    *   **错误处理:** 内部管理 SHA 引用和更新，防止在覆盖或更新文件时出现 "ref not found" 错误。
*   **收益:** Agent 只需声明意图：
    ```bash
    python doc_gen.py answer owner repo --content "The Answer"
    ```
    该技能保证生成一个有效的 Git 提交，而无需 Agent 手动管理复杂的树哈希（Tree Hash）。

## 4. 对比总结 (Comparison Summary)

| 特性           | 原生 MCP 工具方案         | 基于技能 (Skill) 的方案    |
| :------------- | :------------------------ | :------------------------- |
| **搜索策略**   | 线性循环 (O(N) 步骤)      | 单次查询 (O(1) 步骤)       |
| **提交分析**   | 手动 `get_commit` 检查    | 自动化正则过滤             |
| **历史追踪**   | 手动递归 blame 检查       | `blame_analysis.py` 自动化 |
| **文件创建**   | 原生 API (易出现引用错误) | `doc_gen.py` (安全封装)    |
| **Token 使用** | 极高 (记录每次提交)       | 低 (仅记录相关结果)        |

## 5. 结论 (Conclusion)

`github_detective` 和 `github_content_editor` 的设计是 **准确且高效的**。它们将高摩擦、多步骤的监控任务转化为单步、健壮的函数调用。

**建议:**
确保 System Prompts（系统提示词）明确引导模型：在寻找历史变更时，**优先使用** 带有 `--query` 的 `find_commit.py` 进行 "先过滤"，而不是列出所有提交。
