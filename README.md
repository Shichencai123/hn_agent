# hn_agent
Harness Agent — 基于 LangGraph 的 AI 超级 Agent 框架
=======
# HN-Agent (Harness Agent)

基于 LangGraph 的 AI 超级 Agent 系统后端，提供沙箱代码执行、持久化记忆（含向量化长期记忆与语义检索）、子 Agent 委派、MCP 协议集成、多 IM 平台桥接等能力。

## 架构概览

项目采用 **Harness（可发布框架包）+ App（应用层）** 双层架构：

- **Harness 层** (`hn_agent/`) — 核心框架包，可独立发布为 Python 包，包含 Agent 引擎、沙箱、工具、模型工厂等全部核心模块
- **App 层** (`app/`) — 应用层，包含 Gateway API 和 IM 渠道桥接，依赖 Harness 层但不可被反向导入

```
hn-agent/
├── hn_agent/                  # Harness 层 — 核心框架包
│   ├── agents/                # Agent 核心
│   │   ├── lead_agent/        #   主 Agent (LangGraph)
│   │   ├── middlewares/       #   14 个有序中间件
│   │   ├── checkpointer/     #   SQLite 检查点
│   │   ├── factory.py         #   Agent 工厂
│   │   ├── features.py        #   特性管理
│   │   ├── streaming.py       #   SSE 流式响应
│   │   └── thread_state.py    #   线程状态 Schema
│   ├── config/                # 配置系统 (YAML/JSON + 环境变量)
│   ├── models/                # 模型工厂 (6 个 LLM Provider)
│   ├── sandbox/               # 沙箱系统 (Local + Docker)
│   ├── tools/                 # 工具系统 (7 个内置工具)
│   ├── subagents/             # 子 Agent 系统 (双线程池)
│   ├── memory/                # 记忆系统 (LLM + RAG + ChromaDB)
│   ├── mcp/                   # MCP 集成 (stdio/SSE/HTTP)
│   ├── skills/                # 技能系统 (SKILL.md 解析)
│   ├── guardrails/            # 护栏系统 (规则引擎)
│   ├── community/             # 社区工具 (Tavily/Jina/Firecrawl/DuckDuckGo)
│   ├── uploads/               # 上传管理
│   ├── reflection/            # 反射系统 (动态模块加载)
│   ├── client.py              # 嵌入式客户端
│   └── exceptions.py          # 异常层次结构
│
├── app/                       # App 层 — 应用层
│   ├── gateway/               # Gateway API (FastAPI + 10 个路由)
│   │   ├── app.py             #   FastAPI 应用入口
│   │   ├── config.py          #   Gateway 配置
│   │   └── routers/           #   10 个 API 路由模块
│   └── channels/              # IM 渠道桥接
│       ├── base.py            #   Channel 抽象基类
│       ├── manager.py         #   核心调度器
│       ├── message_bus.py     #   异步消息总线
│       ├── store.py           #   会话映射持久化
│       ├── feishu.py          #   飞书实现
│       ├── slack.py           #   Slack 实现
│       └── telegram.py        #   Telegram 实现
│
└── tests/                     # 测试套件 (700+ 单元测试)
    ├── unit/                  #   24 个测试文件
    ├── properties/            #   属性测试 (预留)
    └── integration/           #   集成测试 (预留)
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| Agent 框架 | LangGraph v0.4+ / LangChain v0.3+ |
| Web 框架 | FastAPI |
| 向量数据库 | ChromaDB |
| 嵌入模型 | text-embedding-3-small (OpenAI) |
| 检查点存储 | SQLite |
| 配置格式 | YAML / JSON |
| 测试框架 | pytest / Hypothesis |

## 快速开始

### 安装依赖

```bash
pip install -e ".[dev]"
```

### 配置

创建 `config/config.yaml`：

```yaml
app:
  name: hn-agent
  port: 8001
  debug: false

model:
  default_model: gpt-4o
  providers:
    openai:
      api_key: sk-your-openai-key
    anthropic:
      api_key: sk-ant-your-key

memory:
  enabled: true
  debounce_seconds: 5.0
  storage_dir: ./data/memory
  vector_store:
    provider: chromadb
    collection_name: hn_agent_memories
    embedding_model: text-embedding-3-small
    persist_directory: ./data/chromadb

sandbox:
  provider: local
  timeout: 30
```

环境变量覆盖（`HN_AGENT_` 前缀，双下划线分隔嵌套）：

```bash
export HN_AGENT_MODEL__PROVIDERS__OPENAI__API_KEY=sk-xxx
export HN_AGENT_APP__DEBUG=true
```

### 启动 Gateway API

```bash
uvicorn app.gateway.app:create_app --factory --host 0.0.0.0 --port 8001
```

### 嵌入式调用

```python
from hn_agent.client import HarnessClient

client = HarnessClient(config_path="config/config.yaml")

# 同步调用
response = await client.chat("thread-1", "帮我写一个 Python 排序算法")
print(response.content)

# 流式调用
async for event in client.stream("thread-1", "解释一下快速排序"):
    if event.event == "token":
        print(event.data["content"], end="")
```

### 运行测试

```bash
# 全部测试
pytest

# 指定模块
pytest tests/unit/test_config.py
pytest tests/unit/test_memory.py

# 带覆盖率
pytest --cov=hn_agent --cov=app
```

## 核心模块

### 模型工厂

支持 6 个 LLM 提供商，通过模型名称前缀自动路由：

| 前缀 | 提供商 | 示例 |
|------|--------|------|
| `gpt-` / `o1-` / `o3-` / `o4-` | OpenAI | gpt-4o, o3-mini |
| `claude-` | Anthropic | claude-3-opus-20240229 |
| `deepseek-` | DeepSeek | deepseek-chat |
| `gemini-` | Google | gemini-1.5-pro |
| `minimax-` | MiniMax | minimax-abab6.5 |
| `qwen-` | Qwen | qwen-turbo |

```python
from hn_agent.models import create_model

model = create_model("gpt-4o", config=model_settings)
```

### 记忆系统

双层记忆架构：短期记忆（原子文件 I/O）+ 长期记忆（ChromaDB 向量化存储）。

```
对话消息 → LLM 提取关键信息 → Embedding 向量化 → ChromaDB 存储
                                                        ↓
新对话开始 → 用户消息 Embedding → 向量相似度检索 → 注入 System Prompt
```

- **MemoryUpdater** — LLM 驱动的记忆提取
- **DebounceQueue** — 防抖合并高频更新
- **MemoryStorage** — 原子文件 I/O（写入临时文件 → os.rename）
- **ChromaVectorStore** — 向量化长期记忆存储与语义检索
- **EmbeddingClient** — text-embedding-3-small 封装

### 中间件链

14 个有序中间件，预处理正序执行，后处理逆序执行：

| # | 中间件 | 预处理 | 后处理 |
|---|--------|--------|--------|
| 1 | ThreadData | 加载线程数据 | — |
| 2 | Uploads | 注入上传文件 | — |
| 3 | Sandbox | 创建沙箱 | 清理沙箱 |
| 4 | DanglingToolCall | 检测未完成调用 | — |
| 5 | Guardrail | 授权检查 | — |
| 6 | Summarization | 历史摘要压缩 | — |
| 7 | TodoList | 任务列表维护 | — |
| 8 | Title | — | 生成对话标题 |
| 9 | Memory | 注入记忆上下文 | 提交记忆更新 |
| 10 | ViewImage | — | 处理图片 |
| 11 | SubagentLimit | 限制并发 | — |
| 12 | Clarification | 检测澄清需求 | — |
| 13 | LoopDetection | 检测推理循环 | — |
| 14 | TokenUsage | — | 统计 Token |

### Gateway API

10 个 RESTful 路由模块：

| 路由 | 路径 | 方法 |
|------|------|------|
| models | `/api/models` | GET |
| mcp | `/api/mcp` | GET |
| skills | `/api/skills` | GET |
| memory | `/api/memory` | GET, PUT |
| uploads | `/api/threads/{id}/uploads` | POST |
| threads | `/api/threads`, `/api/threads/{id}/chat` | GET, POST |
| artifacts | `/api/threads/{id}/artifacts` | GET |
| suggestions | `/api/threads/{id}/suggestions` | GET |
| agents | `/api/agents` | GET, POST |
| channels | `/api/channels` | GET, POST |

### IM 渠道桥接

支持飞书、Slack、Telegram 三个 IM 平台的消息桥接：

```
IM 平台消息 → Channel 实现 → MessageBus → ChannelManager
  → Agent 处理 → 响应 → Channel 回复平台
```

## 数据存储

| 存储类型 | 技术 | 用途 | 位置 |
|---------|------|------|------|
| 检查点 | SQLite | Agent 状态持久化 | `./data/checkpoints.db` |
| 短期记忆 | 原子文件 I/O | 用户级记忆文本 | `./data/memory/{user_id}.md` |
| 长期记忆 | ChromaDB | 向量化记忆与语义检索 | `./data/chromadb/` |
| 上传文件 | 文件系统 | 用户上传文档 | `./data/uploads/{thread_id}/` |
| 渠道映射 | JSON 文件 | IM 会话 → Agent 线程 | `./data/channels/store.json` |
| 配置 | YAML/JSON | 应用配置 | `./config/` |

## 开发

### 代码规范

```bash
ruff check .
ruff format .
```

### 项目结构约束

- `hn_agent/` → `app/` ❌ (Harness 层禁止导入 App 层)
- `app/` → `hn_agent/` ✅ (App 层可导入 Harness 层)

