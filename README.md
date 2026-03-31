# CLI Agent

一个基于终端的 AI 助手，支持工具调用、长期记忆、Skills 系统和网络搜索。兼容任何 OpenAI API 格式的模型（vLLM、Ollama、OpenAI 等）。

## 功能特性

- **多工具并行调用** — 文件读写、Shell 命令、Python 执行、网络搜索、截图
- **长期记忆** — 跨会话持久化记忆，自动注入 system prompt
- **Skills 系统** — 通过 Markdown 文件定义可复用的任务流程，支持动态加载
- **上下文管理** — 滑动窗口 + Token 预算双重保护，防止打爆模型上下文
- **中文输入友好** — 使用 prompt_toolkit，正确处理 CJK 宽字符的删除和编辑

## 目录结构

```
cli-agent/
├── agent.py          # 核心 Agent 循环（多轮对话 + 并行工具调用）
├── main.py           # CLI 入口
├── config.py         # 配置项
├── memory.py         # 长期记忆管理
├── history.py        # 对话历史（滑动窗口 + Token 预算裁剪）
├── skills.py         # Skills 管理器
├── tools.md          # 工具说明文档（注入 system prompt）
├── requirements.txt
├── tools/
│   ├── __init__.py       # 工具注册表 & dispatcher
│   ├── filesystem.py     # 文件读写搜索
│   ├── shell.py          # Shell 命令执行
│   ├── python_exec.py    # Python 沙箱执行
│   ├── web.py            # 网络搜索 & 网页抓取
│   ├── screenshot.py     # 截图（macOS）
│   ├── memory_tools.py   # 记忆工具
│   └── skill_tools.py    # Skills 工具
├── skills/               # Skills 文件目录
│   └── web_research/
│       └── SKILL.md
├── memory/               # 运行时记忆存储（自动生成）
│   ├── memory.md         # 长期记忆
│   └── YYYY-MM-DD/       # 每日会话存档
└── ui/
    └── display.py        # 终端 UI（Rich）
```

## 快速开始

### 1. 环境要求

- Python 3.9+
- 可访问的 OpenAI 兼容 API（vLLM、Ollama、OpenAI 等）

### 2. 安装依赖

```bash
git clone <repo_url>
cd cli-agent
pip install -r requirements.txt
```

### 3. 配置模型

编辑 `config.py`，修改 API 地址和模型名：

```python
@dataclass
class AgentConfig:
    base_url: str = "http://your-server:8001/v1"  # API 地址
    model: str = "your-model-name"                 # 模型名称
    max_tokens: int = 4096                         # 单次最大输出 token
    max_context_tokens: int = 262144               # 模型上下文窗口大小
```

**常见配置示例：**

```python
# vLLM 本地部署
base_url = "http://localhost:8000/v1"
model = "Qwen/Qwen3-7B"

# Ollama
base_url = "http://localhost:11434/v1"
model = "qwen3:8b"

# OpenAI
base_url = "https://api.openai.com/v1"
model = "gpt-4o"
# 需同时设置环境变量或在代码中传入真实 api_key
```

### 4. 启动

```bash
python3 main.py
```

## 内置命令

| 命令 | 说明 |
|------|------|
| `/skills` | 列出所有可用 Skills |
| `/screenshot <prompt>` | 截图并提问（macOS） |
| `/clear` | 清空对话历史（自动保存当前会话） |
| `/help` | 显示帮助 |
| `/quit` | 退出（自动保存会话） |

## 可用工具

Agent 自动选择工具，无需手动调用：

| 工具 | 说明 |
|------|------|
| `read_file` / `write_file` / `search_files` | 文件操作 |
| `execute_shell` | 执行 Shell 命令（30s 超时）|
| `execute_python` | 执行 Python 代码（15s 沙箱）|
| `web_search` | DuckDuckGo 搜索 |
| `scrape_webpage` | 抓取网页正文 |
| `capture_screenshot` | 截图（macOS）|
| `read_memory` / `update_memory` / `append_memory` | 长期记忆读写 |
| `list_skills` / `load_skill` / `create_skill` / `update_skill` | Skills 管理 |

## Skills 系统

Skills 是存放在 `skills/<name>/SKILL.md` 的 Markdown 文件，描述特定任务的工作流程。Agent 会在 system prompt 中看到可用 Skills 列表，并在合适时主动加载。

**SKILL.md 格式：**

```markdown
---
description: 一句话描述（显示在列表中）
---

# Skill 名称

## 何时使用
...

## 工作流
...
```

**创建新 Skill（让 Agent 自动创建）：**

```
You> 帮我创建一个 code_review skill，专门做代码审查
```

**或手动创建：**

```bash
mkdir -p skills/my_skill
cat > skills/my_skill/SKILL.md << 'EOF'
---
description: 我的自定义 Skill
---
# My Skill
...
EOF
```

## 长期记忆

Agent 可以通过工具主动存储跨会话的重要信息：

```
You> 记住我叫张三，偏好简洁回答
# Agent 会自动调用 append_memory 保存
```

记忆存储在 `memory/memory.md`，每次启动自动加载到 system prompt。

## 上下文管理

- **滑动窗口**：默认保留最近 40 条消息（`max_history_messages`）
- **Token 预算**：每次调用前估算总 token，超出时从最旧的消息开始裁剪
- **工具结果截断**：单条工具返回超过 8000 字符时自动截断（`max_tool_result_chars`）

所有参数均可在 `config.py` 中调整。

## 依赖说明

| 包 | 用途 |
|----|------|
| `openai` | API 客户端（兼容 vLLM/Ollama） |
| `rich` | 终端 UI 渲染 |
| `prompt_toolkit` | 终端输入（支持中文 CJK 字符正确编辑）|
| `ddgs` | DuckDuckGo 搜索 |
| `beautifulsoup4` | 网页正文提取 |
| `requests` | HTTP 请求 |
| `Pillow` | 截图压缩（可选）|

## 常见问题

**Q: Agent 没有响应 / 一直转圈**

检查 API 服务是否正常：
```bash
curl http://your-server:8001/v1/models
```

**Q: `web_search` 返回错误**

```bash
pip install ddgs  # 安装新版包
```

**Q: 截图功能不可用**

`capture_screenshot` 仅支持 macOS，依赖系统 `screencapture` 命令。

**Q: 中文输入删不掉字符**

确保已安装 `prompt_toolkit`：
```bash
pip install prompt_toolkit
```

## License

MIT
