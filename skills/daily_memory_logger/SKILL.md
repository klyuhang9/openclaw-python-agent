---
description: 自动记录每天对话内容到 memory/日期文件夹 下的 Markdown 文件
---

# Daily Memory Logger - 每日对话自动记录

## 🎯 核心功能

本技能负责在每次对话中自动记录内容到对应的日期文件夹中，确保对话历史完整保存。

**关键特性**：每天第一次对话时，自动检查并整理昨天的对话记录。

---

## 📁 文件结构

```
memory/
├── memory.md                    # 主记忆文件（精华记忆）
├── 2026-03-31/
│   └── session_1.md             # 3月31日第1次对话记录
├── 2026-04-01/
│   ├── session_1.md             # 4月1日第1次对话记录
│   └── session_2.md             # 4月1日第2次对话记录（如有）
└── ...
```

---

## 🔄 自动记录流程

### 1️⃣ 每天第一次对话时 — 检查昨天记录

```python
import datetime

today = datetime.datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# 检查昨天的文件夹是否存在
yesterday_folder = f"memory/{yesterday}"

if os.path.exists(yesterday_folder):
    # 检查是否有 session 文件
    sessions = [f for f in os.listdir(yesterday_folder) if f.startswith("session_") and f.endswith(".md")]
    if sessions:
        print(f"✅ 昨天的对话记录已存在：{len(sessions)} 个 session")
    else:
        print(f"⚠️ 昨天的文件夹存在但没有 session 文件")
else:
    print(f"ℹ️ 昨天没有对话记录（可能是周末或节假日）")
```

### 2️⃣ 检查/创建今天日期文件夹

```bash
# 获取今天日期
date +%Y-%m-%d  # 输出：2026-04-01

# 检查文件夹是否存在
ls memory/2026-04-01/ 2>/dev/null || mkdir -p memory/2026-04-01/
```

### 3️⃣ 确定 Session 编号

检查当天已有几个 session 文件：

```bash
# 数一下当天有几个 session 文件
ls memory/2026-04-01/session_*.md 2>/dev/null | wc -l
# 如果是 0，则创建 session_1.md；如果是 1，则创建 session_2.md
```

### 4️⃣ 记录对话内容

在对话进行中或结束时，将内容追加到当前 session 文件：

```markdown
# Session X — 2026-04-01 HH:MM:SS

## **User**

[用户的问题/指令]

## **Assistant**

[助手的回复]
```

---

## 📝 记录规则

| 场景 | 操作 |
|------|------|
| **新的一天第一次对话** | 1. 检查昨天记录 2. 创建今天文件夹 + session_1.md |
| **同一天新对话** | 创建新的 session_X.md 文件 |
| **同一 session 内** | 追加内容到当前 session 文件 |
| **重要信息** | 同时更新到 `memory.md` |

---

## 🛠️ 实现方式

### 方式 A：每次回复后自动追加（推荐）

在每次回复用户后，自动调用 `write_file` 或 `append_file` 将对话内容写入当天的 session 文件。

**示例代码逻辑**：

```python
import datetime
import os

def record_conversation(user_input, assistant_output):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    folder = f"memory/{today}"
    
    # 创建文件夹
    os.makedirs(folder, exist_ok=True)
    
    # 确定 session 编号
    existing = [f for f in os.listdir(folder) if f.startswith("session_") and f.endswith(".md")]
    session_num = len(existing) + 1
    
    # 写入文件
    filename = f"{folder}/session_{session_num}.md"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# Session {session_num} — {timestamp}

## **User**

{user_input}

## **Assistant**

{assistant_output}
"""
    
    with open(filename, "a", encoding="utf-8") as f:
        f.write(content)
```

### 方式 B：对话结束时批量写入

在检测到对话结束（如用户长时间无响应、或明确说"结束"）时，一次性写入整个对话。

---

## ⚠️ 注意事项

1. **文件编码**：始终使用 `utf-8` 编码
2. **追加模式**：同一 session 内使用追加模式 (`mode="a"`)
3. **时间戳**：每次记录都要包含准确的时间戳
4. **精华提取**：重要的、跨会话的信息要同步到 `memory.md`
5. **昨天记录检查**：每天第一次对话时自动检查昨天的记录状态

---

## 📋 与 memory.md 的同步规则

| 内容类型 | 存储位置 |
|---------|---------|
| 日常对话详情 | `memory/日期/session_X.md` |
| 用户偏好/习惯 | `memory.md` |
| 重要事实/信息 | `memory.md` |
| 技能/配置变更 | `memory.md` |
| 每日精华摘要 | `memory/日期/summary.md`（可选） |

**示例**：
- 用户说"记住我喜欢喝美式咖啡" → 写入 `memory.md`
- 用户问"今天天气怎么样" → 只写入当天 session 文件

---

## 🎯 激活后的行为

加载本技能后，我会：

1. ✅ **每天第一次对话时** — 自动检查昨天的记录状态并报告
2. ✅ 每次对话前检查并创建当天日期文件夹
3. ✅ 自动记录每轮对话到 session 文件
4. ✅ 识别重要信息并同步到 `memory.md`
5. ✅ 在对话结束时确认记录完成

---

## 🔧 手动命令

你也可以手动触发记录：

```
"记录今天的对话"
"把刚才的内容记到 memory"
"同步精华到 memory.md"
"检查昨天的记录"
```

---

## 📊 状态检查

```bash
# 查看今天的记录
ls -la memory/2026-04-01/

# 查看今天的对话内容
cat memory/2026-04-01/session_1.md

# 查看所有日期文件夹
ls -la memory/

# 检查昨天的记录
ls -la memory/2026-03-31/
```

---

## 📋 每日检查模板

每天第一次对话时，我会输出类似这样的报告：

```markdown
## 📅 每日记忆检查 — 2026-04-01

### 昨天记录状态 (2026-03-31)
- 📁 文件夹：✅ 存在
- 📝 Session 文件：✅ 1 个 (session_1.md)
- 📊 精华同步：✅ 已同步到 memory.md

### 今天记录状态 (2026-04-01)
- 📁 文件夹：✅ 已创建
- 📝 Session 文件：🆕 session_1.md (新建)
- 🔄 自动记录：✅ 已激活
```
