# 需求文档：

## 简介

 hn-agent是一个基于 LangGraph 的 AI 超级 Agent 系统后端，提供沙箱代码执行、持久化记忆、子 Agent 委派、MCP 协议集成、多 IM 平台桥接等能力。本项目采用 Harness（可发布框架包）+ App（应用层）双层架构，技术栈为 Python 3.10 / LangGraph v1.0+ / LangChain v1.0+ / FastAPI / text-embedding-3-small / Chroma。

## 术语表

- **Harness_Layer**: 核心框架层，可独立发布的 Python 包，包含 Agent、沙箱、工具、模型等核心模块
- **App_Layer**: 应用层，包含 Gateway API 和 IM 渠道桥接，依赖 Harness_Layer，不可被 Harness_Layer 导入
- **Lead_Agent**: 主 Agent，基于 LangGraph 构建的核心推理引擎，负责接收用户消息并协调工具调用和子 Agent 委派
- **Middleware_Chain**: 中间件链，14 个有序中间件组成的处理管道，在 Agent 推理前后执行预处理和后处理
- **Thread_State**: 线程状态，Agent 运行时的状态 Schema，包含消息、artifacts、图片等数据的自定义 reducer
- **Sandbox_System**: 沙箱系统，提供隔离的代码执行环境，支持 Local 和 Docker 两种 Provider
- **Tool_System**: 工具系统，统一的工具注册与加载机制，支持 sandbox、built-in、MCP、community 四类工具
- **Subagent_System**: 子 Agent 系统，支持异步任务委派和双线程池并发执行
- **Memory_System**: 记忆系统，LLM 驱动的持久化上下文记忆，包含防抖队列、原子文件 I/O、向量化长期记忆存储和语义检索
- **Vector_Store**: 向量数据库（ChromaDB），用于存储和检索向量化的记忆数据，支持语义相似度搜索
- **Embedding_Model**: 嵌入模型（text-embedding-3-small），将文本内容转换为高维向量表示的模型，用于记忆的向量化编码
- **MCP_Client**: MCP 集成客户端，支持多服务器连接、懒加载缓存和 OAuth 认证
- **Skill_System**: 技能系统，支持技能发现、加载、解析和安装，使用 YAML frontmatter 元数据
- **Guardrail_System**: 护栏系统，工具调用前的授权检查机制，支持可插拔 Provider 协议
- **Config_System**: 配置系统，支持 YAML/JSON 配置加载、环境变量解析和版本管理
- **Reflection_System**: 反射系统，通过字符串路径动态加载模块、解析类和变量
- **Model_Factory**: 模型工厂，多 LLM 提供商的统一创建入口，支持 thinking/vision 能力
- **Checkpoint_System**: 检查点系统，基于 SQLite 的 Agent 状态持久化
- **Embedded_Client**: 嵌入式客户端，无需 HTTP 的进程内 Agent 访问接口
- **Gateway_API**: FastAPI REST 服务，包含 10 个路由模块
- **Channel_Bridge**: IM 渠道桥接，支持飞书/Slack/Telegram 消息桥接
- **Community_Tools**: 社区工具，Tavily/Jina/Firecrawl/DuckDuckGo 等外部工具集成
- **Agent_Factory**: Agent 工厂，负责 Agent 创建和特性管理
- **SSE**: Server-Sent Events，服务端推送事件流，用于流式响应
- **MessageBus**: 异步消息总线，IM 渠道内部的消息分发机制
- **Provider**: 提供者模式，可插拔的实现接口

## 需求

### 需求 1：配置系统

**用户故事：** 作为开发者，我希望系统提供统一的配置加载机制，以便通过 YAML/JSON 文件和环境变量灵活管理应用配置。

#### 验收标准

1. WHEN 应用启动时，THE Config_System SHALL 从指定路径加载 YAML 和 JSON 格式的配置文件，并将配置解析为类型化的 Python 对象
2. WHEN 环境变量与配置文件中的同名配置项同时存在时，THE Config_System SHALL 优先使用环境变量的值覆盖配置文件中的值
3. THE Config_System SHALL 为以下模块提供独立的配置模型：app、model、sandbox、tool、memory、extensions、guardrails
4. WHEN 配置文件中包含无法识别的配置项时，THE Config_System SHALL 记录警告日志并忽略该配置项
5. IF 必需的配置项缺失，THEN THE Config_System SHALL 抛出包含缺失项名称的 ConfigurationError 异常
6. THE Config_System SHALL 支持配置版本管理，在配置结构变更时提供向后兼容的迁移路径

### 需求 2：反射系统

**用户故事：** 作为开发者，我希望系统能通过字符串路径动态加载模块和类，以便实现可插拔的组件架构。

#### 验收标准

1. WHEN 提供一个合法的 Python 模块路径字符串时，THE Reflection_System SHALL 动态导入该模块并返回对应的模块对象
2. WHEN 提供一个合法的类路径字符串（格式为 "module.path:ClassName"）时，THE Reflection_System SHALL 解析并返回对应的类对象
3. WHEN 提供一个合法的变量路径字符串时，THE Reflection_System SHALL 解析并返回对应的变量值
4. IF 提供的模块路径不存在，THEN THE Reflection_System SHALL 抛出包含路径信息的 ModuleNotFoundError 异常
5. IF 提供的类或变量在模块中不存在，THEN THE Reflection_System SHALL 抛出包含名称信息的 AttributeError 异常

### 需求 3：模型工厂

**用户故事：** 作为开发者，我希望通过统一接口创建不同 LLM 提供商的模型实例，以便在不修改业务代码的情况下切换模型。

#### 验收标准

1. THE Model_Factory SHALL 提供统一的 create_model 函数，接受模型名称和配置参数，返回 LangChain BaseChatModel 实例
2. THE Model_Factory SHALL 支持以下 LLM 提供商：OpenAI、Anthropic (Claude)、DeepSeek、Google、MiniMax、Qwen
3. WHEN 创建模型实例时，THE Model_Factory SHALL 从 Config_System 加载对应提供商的 API 凭证
4. WHERE 模型支持 thinking 能力，THE Model_Factory SHALL 在创建时启用 thinking 模式的配置
5. WHERE 模型支持 vision 能力，THE Model_Factory SHALL 在创建时启用图片输入的配置
6. IF 指定的模型提供商不受支持，THEN THE Model_Factory SHALL 抛出包含提供商名称的 UnsupportedProviderError 异常
7. IF API 凭证缺失或无效，THEN THE Model_Factory SHALL 抛出包含提供商名称的 CredentialError 异常
8. THE Model_Factory SHALL 为每个提供商提供独立的 Provider 适配器，封装提供商特有的参数处理逻辑

### 需求 4：Lead Agent 核心

**用户故事：** 作为开发者，我希望系统提供基于 LangGraph 的主 Agent 引擎，以便处理用户消息并协调工具调用和推理。

#### 验收标准

1. THE Lead_Agent SHALL 基于 LangGraph v1.0+ 的 create_agent 构建，支持消息输入和流式输出
2. WHEN 接收到用户消息时，THE Lead_Agent SHALL 通过 LLM 推理生成响应，并在需要时调用已注册的工具
3. THE Lead_Agent SHALL 在创建时通过 Agent_Factory 组装中间件链、工具集和模型实例
4. THE Lead_Agent SHALL 根据 Agent 配置动态选择 LLM 模型
5. THE Lead_Agent SHALL 基于 Agent 配置和已加载的技能生成系统提示词
6. WHEN 工具调用返回结果时，THE Lead_Agent SHALL 将结果注入上下文并继续 LLM 推理，直到生成最终响应
7. THE Lead_Agent SHALL 通过 SSE 流式返回推理过程中的中间状态和最终响应

### 需求 5：中间件链

**用户故事：** 作为开发者，我希望 Agent 的处理流程支持可扩展的中间件机制，以便在推理前后注入横切关注点。

#### 验收标准

1. THE Middleware_Chain SHALL 按固定顺序执行以下 14 个中间件：ThreadData、Uploads、Sandbox、DanglingToolCall、Guardrail、Summarization、TodoList、Title、Memory、ViewImage、SubagentLimit、Clarification、LoopDetection、TokenUsage
2. WHEN Agent 开始处理消息时，THE Middleware_Chain SHALL 按顺序执行每个中间件的预处理逻辑
3. WHEN Agent 完成推理后，THE Middleware_Chain SHALL 按逆序执行每个中间件的后处理逻辑
4. THE ThreadData_Middleware SHALL 在预处理阶段加载线程关联的数据到 Agent 状态中
5. THE Uploads_Middleware SHALL 在预处理阶段将上传文件的内容注入到消息上下文中
6. THE Sandbox_Middleware SHALL 管理沙箱实例的生命周期，在预处理阶段创建沙箱，在后处理阶段清理资源
7. THE DanglingToolCall_Middleware SHALL 检测并处理未完成的工具调用，防止 Agent 状态不一致
8. THE Guardrail_Middleware SHALL 在工具调用执行前进行授权检查
9. THE Summarization_Middleware SHALL 在对话超过配置的长度阈值时，对历史消息进行摘要压缩
10. THE TodoList_Middleware SHALL 维护 Agent 的任务列表状态
11. THE Title_Middleware SHALL 在后处理阶段为新对话线程自动生成标题
12. THE Memory_Middleware SHALL 在后处理阶段将对话内容提交到记忆更新队列
13. THE ViewImage_Middleware SHALL 处理 Agent 生成的图片，将图片数据注入到线程状态中
14. THE SubagentLimit_Middleware SHALL 限制子 Agent 的并发数量，防止资源耗尽
15. THE Clarification_Middleware SHALL 检测 Agent 是否需要向用户请求澄清信息
16. THE LoopDetection_Middleware SHALL 检测 Agent 推理是否进入循环，并在检测到循环时终止推理
17. THE TokenUsage_Middleware SHALL 在后处理阶段统计并记录本次推理的 Token 使用量

### 需求 6：线程状态

**用户故事：** 作为开发者，我希望 Agent 运行时拥有结构化的状态管理，以便在推理过程中维护消息、artifacts 和图片等数据。

#### 验收标准

1. THE Thread_State SHALL 定义 Agent 运行时的状态 Schema，包含 messages、artifacts、images、title 等字段
2. THE Thread_State SHALL 为 artifacts 字段提供自定义 reducer，支持 artifact 的增量追加和更新
3. THE Thread_State SHALL 为 images 字段提供自定义 reducer，支持图片数据的追加
4. WHEN 多个中间件同时修改 Thread_State 时，THE Thread_State SHALL 通过 reducer 机制保证状态合并的一致性
5. THE Thread_State SHALL 支持序列化为 JSON 格式，以便持久化存储和网络传输

### 需求 7：沙箱系统

**用户故事：** 作为开发者，我希望系统提供隔离的代码执行环境，以便安全地运行用户提交的代码。

#### 验收标准

1. THE Sandbox_System SHALL 定义统一的沙箱抽象接口（SandboxProvider），包含 execute、read_file、write_file、list_files 方法
2. THE Sandbox_System SHALL 提供 LocalProvider 实现，在本地文件系统的隔离目录中执行代码
3. THE Sandbox_System SHALL 提供基于 Docker 的 AioProvider 实现，在容器中执行代码
4. WHEN 执行代码时，THE Sandbox_System SHALL 将虚拟路径翻译为沙箱内的实际路径，防止路径逃逸
5. THE Sandbox_System SHALL 提供以下沙箱工具：bash 命令执行、ls 目录列表、read 文件读取、write 文件写入、str_replace 文本替换
6. WHEN 代码执行超过配置的超时时间时，THE Sandbox_System SHALL 终止执行并返回超时错误
7. IF 代码执行过程中发生异常，THEN THE Sandbox_System SHALL 捕获异常并返回包含错误详情的结构化结果
8. THE Sandbox_Middleware SHALL 在 Agent 处理开始时创建沙箱实例，在处理结束后清理沙箱资源

### 需求 8：工具系统

**用户故事：** 作为开发者，我希望系统提供统一的工具注册和加载机制，以便 Agent 能够调用多种类型的工具。

#### 验收标准

1. THE Tool_System SHALL 支持四类工具的注册和加载：sandbox 工具、built-in 工具、MCP 工具、community 工具
2. THE Tool_System SHALL 提供统一的工具加载器，根据 Agent 配置动态加载所需的工具集
3. THE Tool_System SHALL 提供以下内置工具：clarification（澄清请求）、present_file（文件展示）、view_image（图片查看）、task（子 Agent 委派）、invoke_acp_agent（ACP Agent 调用）、setup_agent（Agent 设置）、tool_search（工具搜索）
4. WHEN Agent 配置中指定了 MCP 服务器时，THE Tool_System SHALL 从 MCP_Client 加载对应的 MCP 工具
5. WHEN Agent 配置中指定了社区工具时，THE Tool_System SHALL 加载对应的 Community_Tools
6. THE Tool_System SHALL 为每个工具提供名称、描述和参数 Schema 的元数据定义

### 需求 9：子 Agent 系统

**用户故事：** 作为开发者，我希望主 Agent 能够将任务委派给专门的子 Agent 异步执行，以便并行处理复杂任务。

#### 验收标准

1. THE Subagent_System SHALL 提供 Agent 注册表（Registry），支持注册和查找子 Agent 定义
2. THE Subagent_System SHALL 提供后台执行引擎（Executor），支持异步提交和执行子 Agent 任务
3. THE Subagent_System SHALL 使用双线程池实现并发执行，分离 I/O 密集型和 CPU 密集型任务
4. THE Subagent_System SHALL 提供以下内置子 Agent：general_purpose（通用 Agent）和 bash_agent（Bash 专家）
5. WHEN 子 Agent 任务执行完成时，THE Subagent_System SHALL 通过 SSE 事件通知主 Agent
6. WHEN 子 Agent 执行过程中发生错误时，THE Subagent_System SHALL 捕获错误并将错误信息返回给主 Agent
### 需求 10：记忆系统

**用户故事：** 作为开发者，我希望系统能够通过向量化技术持久化存储对话中的关键上下文信息，并支持跨会话的长期记忆管理和语义检索，以便 Agent 在后续对话中精准利用历史记忆。

#### 验收标准

1. THE Memory_System SHALL 使用 LLM 从对话内容中提取关键信息并更新记忆存储
2. THE Memory_System SHALL 提供防抖队列（Debounce Queue），合并短时间内的多次记忆更新请求为一次 LLM 调用
3. THE Memory_System SHALL 提供原子文件 I/O 的存储层，确保记忆数据的写入不会因进程中断而损坏
4. THE Memory_System SHALL 提供记忆提示词模板，将已存储的记忆注入到 Agent 的系统提示词中
5. WHEN 对话结束后，THE Memory_Middleware SHALL 将对话内容提交到记忆更新队列
6. WHEN 记忆更新队列触发处理时，THE Memory_System SHALL 调用 LLM 分析对话内容并生成记忆更新
7. IF 记忆存储文件写入失败，THEN THE Memory_System SHALL 记录错误日志并保留上一次的有效记忆数据
8. THE Memory_System SHALL 提供跨会话的长期记忆（Long-term Memory）存储，将结构化的记忆数据持久化到独立的存储后端，支持跨线程和跨会话的记忆共享与检索
9. THE Memory_System SHALL 使用 Embedding_Model 将对话内容和提取的记忆片段转换为向量表示
10. THE Memory_System SHALL 使用 Vector_Store（如ChromaDB）存储向量化的记忆数据，支持基于语义相似度的记忆检索
11. WHEN Agent 接收到用户消息时，THE Memory_System SHALL 通过 Vector_Store 执行语义相似度搜索，检索与当前对话上下文最相关的历史记忆，并注入到 Agent 的上下文中
12. THE Memory_System SHALL 为 Vector_Store 提供可插拔的 Provider 接口，支持在不同向量数据库实现之间切换
13. IF Vector_Store 连接失败或查询超时，THEN THE Memory_Syst

### 需求 11：MCP 集成

**用户故事：** 作为开发者，我希望系统能够连接多个 MCP 服务器并加载其提供的工具，以便扩展 Agent 的能力。

#### 验收标准

1. THE MCP_Client SHALL 支持连接以下传输协议的 MCP 服务器：stdio、SSE、HTTP
2. THE MCP_Client SHALL 实现懒加载缓存机制，在首次请求时连接 MCP 服务器并缓存工具列表
3. THE MCP_Client SHALL 支持 OAuth 认证流程，用于连接需要授权的 MCP 服务器
4. WHEN 连接 MCP 服务器时，THE MCP_Client SHALL 获取服务器提供的工具列表并转换为 LangChain Tool 格式
5. IF MCP 服务器连接失败，THEN THE MCP_Client SHALL 记录错误日志并在配置的重试间隔后重新尝试连接
6. WHEN MCP 工具被调用时，THE MCP_Client SHALL 将调用请求转发到对应的 MCP 服务器并返回执行结果

### 需求 12：技能系统

**用户故事：** 作为开发者，我希望系统支持技能的发现、加载和管理，以便通过技能文件扩展 Agent 的行为。

#### 验收标准

1. THE Skill_System SHALL 从指定目录发现并加载 SKILL.md 格式的技能文件
2. THE Skill_System SHALL 解析 SKILL.md 文件中的 YAML frontmatter 元数据，提取技能名称、描述、依赖工具等信息
3. THE Skill_System SHALL 验证技能文件的格式和必需字段的完整性
4. THE Skill_System SHALL 支持技能安装功能，将外部技能包安装到本地技能目录
5. WHEN Agent 配置中指定了技能时，THE Skill_System SHALL 加载对应技能的提示词并注入到 Agent 的系统提示词中
6. IF 技能文件格式不合法，THEN THE Skill_System SHALL 返回包含具体错误位置的验证错误信息

### 需求 13：护栏系统

**用户故事：** 作为开发者，我希望系统在工具调用前进行授权检查，以便防止未授权的操作执行。

#### 验收标准

1. THE Guardrail_System SHALL 定义可插拔的 GuardrailProvider 协议接口，包含 check_authorization 方法
2. THE Guardrail_System SHALL 提供内置的 GuardrailProvider 实现，支持基于规则的授权检查
3. WHEN Agent 发起工具调用时，THE Guardrail_Middleware SHALL 在工具执行前调用 GuardrailProvider 进行授权检查
4. IF 授权检查未通过，THEN THE Guardrail_System SHALL 阻止工具执行并向 Agent 返回授权拒绝的原因
5. THE Guardrail_System SHALL 支持通过配置文件定义授权规则


### 需求 14：上传管理

**用户故事：** 作为开发者，我希望系统支持文件上传和格式转换，以便 Agent 能够处理用户上传的各种文档。

#### 验收标准

1. THE Upload_Manager SHALL 接收用户上传的文件并存储到线程关联的目录中
2. THE Upload_Manager SHALL 支持以下文档格式到 Markdown 的转换：PDF、PPT、Excel、Word
3. WHEN 用户上传文档文件时，THE Upload_Manager SHALL 自动将文档转换为 Markdown 格式，以便 Agent 读取
4. THE Upload_Manager SHALL 为每个上传文件生成唯一标识符，并维护文件元数据（文件名、大小、MIME 类型、上传时间）
5. IF 文件格式转换失败，THEN THE Upload_Manager SHALL 记录错误日志并保留原始文件，同时向调用方返回转换失败的原因

### 需求 15：检查点系统

**用户故事：** 作为开发者，我希望 Agent 的运行状态能够持久化存储，以便在进程重启后恢复对话上下文。

#### 验收标准

1. THE Checkpoint_System SHALL 基于 SQLite 实现 Agent 状态的持久化存储
2. THE Checkpoint_System SHALL 提供同步和异步两种 Provider 接口
3. WHEN Agent 完成一轮推理后，THE Checkpoint_System SHALL 将当前 Thread_State 序列化并存储到 SQLite 数据库
4. WHEN Agent 恢复已有线程的对话时，THE Checkpoint_System SHALL 从 SQLite 数据库加载最近的检查点并恢复 Thread_State
5. IF 检查点数据损坏或加载失败，THEN THE Checkpoint_System SHALL 记录错误日志并创建新的空白 Thread_State

### 需求 16：嵌入式客户端

**用户故事：** 作为开发者，我希望能够在同一进程内直接调用 Agent，无需通过 HTTP 请求，以便实现高效的进程内集成。

#### 验收标准

1. THE Embedded_Client SHALL 提供 HnAgentwClient 类，支持在同一进程内直接创建和调用 Lead_Agent
2. THE Embedded_Client SHALL 提供与 Gateway_API 对齐的方法接口，包含 chat、stream、get_thread、list_threads 等方法
3. WHEN 调用 chat 方法时，THE Embedded_Client SHALL 创建 Lead_Agent 实例并同步返回完整响应
4. WHEN 调用 stream 方法时，THE Embedded_Client SHALL 创建 Lead_Agent 实例并通过异步生成器返回流式响应
5. THE Embedded_Client SHALL 复用 Config_System 加载配置，与 Gateway_API 使用相同的配置源

### 需求 17：Gateway API

**用户故事：** 作为开发者，我希望系统提供 RESTful API 服务，以便前端和外部系统通过 HTTP 与 Agent 交互。

#### 验收标准

1. THE Gateway_API SHALL 基于 FastAPI 框架构建，监听配置的端口（默认 8001）
2. THE Gateway_API SHALL 提供以下 10 个路由模块：models、mcp、skills、memory、uploads、threads、artifacts、suggestions、agents、channels
3. WHEN 收到 /api/threads/{thread_id}/chat 请求时，THE Gateway_API SHALL 创建 Lead_Agent 并通过 SSE 流式返回推理结果
4. WHEN 收到 /api/models 请求时，THE Gateway_API SHALL 返回当前配置中可用的模型列表
5. WHEN 收到 /api/mcp 请求时，THE Gateway_API SHALL 返回已配置的 MCP 服务器列表及其工具信息
6. WHEN 收到 /api/skills 请求时，THE Gateway_API SHALL 返回已加载的技能列表
7. WHEN 收到 /api/threads/{thread_id}/uploads 请求时，THE Gateway_API SHALL 处理文件上传并返回上传结果
8. WHEN 收到 /api/threads/{thread_id}/artifacts 请求时，THE Gateway_API SHALL 返回线程关联的 artifacts 列表
9. WHEN 收到 /api/memory 请求时，THE Gateway_API SHALL 返回当前记忆内容或接受记忆更新请求
10. WHEN 收到 /api/agents 请求时，THE Gateway_API SHALL 返回可用的 Agent 配置列表或创建新的 Agent 配置
11. WHEN 收到 /api/threads/{thread_id}/suggestions 请求时，THE Gateway_API SHALL 返回基于对话上下文的建议回复列表
12. THE Gateway_API SHALL 对所有请求进行输入验证，对不合法的请求返回包含错误详情的 4xx 响应

### 需求 18：IM 渠道桥接

**用户故事：** 作为开发者，我希望系统能够桥接多个 IM 平台的消息，以便用户通过飞书、Slack、Telegram 等平台与 Agent 交互。

#### 验收标准

1. THE Channel_Bridge SHALL 定义 Channel 抽象基类，包含 receive_message、send_message、setup_webhook 方法
2. THE Channel_Bridge SHALL 提供以下 IM 平台的实现：飞书（Feishu）、Slack、Telegram
3. THE Channel_Bridge SHALL 提供 ChannelManager 核心调度器，管理多个 Channel 实例的生命周期
4. THE Channel_Bridge SHALL 提供异步 MessageBus，在 Channel 接收消息和 Agent 处理之间进行异步解耦
5. THE Channel_Bridge SHALL 提供 Store 模块，持久化 IM 平台会话 ID 与 Agent 线程 ID 的映射关系
6. WHEN IM 平台发送消息到 webhook 时，THE Channel_Bridge SHALL 通过对应的 Channel 实现解析消息并投递到 MessageBus
7. WHEN MessageBus 收到消息时，THE ChannelManager SHALL 查找或创建对应的 Agent 线程，并调用 Lead_Agent 处理消息
8. WHEN Agent 生成响应后，THE Channel_Bridge SHALL 通过对应的 Channel 实现将响应发送回 IM 平台
9. THE Channel_Bridge SHALL 提供渠道生命周期管理服务（Service），支持渠道的启动、停止和健康检查

### 需求 19：社区工具

**用户故事：** 作为开发者，我希望系统集成常用的外部搜索和内容获取工具，以便 Agent 能够访问互联网信息。

#### 验收标准

1. THE Community_Tools SHALL 提供以下外部工具的集成：Tavily（搜索）、Jina（内容提取）、Firecrawl（网页抓取）、DuckDuckGo（搜索）
2. THE Community_Tools SHALL 为每个外部工具提供统一的 LangChain Tool 接口封装
3. WHEN Agent 调用社区工具时，THE Community_Tools SHALL 将请求转发到对应的外部 API 并返回结构化结果
4. IF 外部 API 调用失败，THEN THE Community_Tools SHALL 返回包含错误类型和错误信息的结构化错误结果
5. THE Community_Tools SHALL 从 Config_System 加载各外部工具的 API 密钥和配置参数

### 需求 20：Agent 工厂

**用户故事：** 作为开发者，我希望系统提供统一的 Agent 创建和特性管理机制，以便灵活配置不同能力的 Agent 实例。

#### 验收标准

1. THE Agent_Factory SHALL 提供 make_lead_agent 函数，根据 Agent 配置创建完整的 Lead_Agent 实例
2. THE Agent_Factory SHALL 在创建 Agent 时组装中间件链、加载工具集、选择模型、生成系统提示词
3. THE Agent_Factory SHALL 提供特性管理模块（Features），支持通过配置启用或禁用 Agent 的特定能力（如沙箱、记忆、子 Agent 等）
4. WHEN 创建 Agent 时指定了特性配置，THE Agent_Factory SHALL 仅加载已启用特性对应的中间件和工具
5. THE Agent_Factory SHALL 支持通过 API 动态创建和管理 Agent 配置

### 需求 21：双层架构隔离

**用户故事：** 作为开发者，我希望框架层和应用层保持严格的依赖隔离，以便 Harness 框架包可以独立发布和复用。

#### 验收标准

1. THE Harness_Layer SHALL 作为独立的 Python 包发布，不依赖 App_Layer 中的任何模块
2. THE App_Layer SHALL 依赖 Harness_Layer，通过导入 Harness_Layer 的公开接口使用核心功能
3. IF App_Layer 中的代码尝试被 Harness_Layer 导入，THEN 构建系统 SHALL 报告依赖违规错误
4. THE Harness_Layer SHALL 将以下模块作为公开接口导出：agents、sandbox、tools、models、mcp、skills、config、guardrails、memory、subagents、reflection、client

### 需求 22：SSE 流式响应

**用户故事：** 作为开发者，我希望 Agent 的推理过程能够通过 SSE 流式返回，以便前端实时展示推理进度。

#### 验收标准

1. WHEN Agent 开始推理时，THE Gateway_API SHALL 建立 SSE 连接并持续推送事件
2. THE SSE 流 SHALL 包含以下事件类型：token（逐 token 输出）、tool_call（工具调用开始）、tool_result（工具调用结果）、subagent_start（子 Agent 启动）、subagent_result（子 Agent 结果）、done（推理完成）
3. WHEN LLM 生成 token 时，THE Lead_Agent SHALL 通过 SSE 流实时推送每个 token
4. WHEN 工具调用开始和完成时，THE Lead_Agent SHALL 通过 SSE 流推送工具调用的状态和结果
5. IF SSE 连接中断，THEN THE Gateway_API SHALL 清理对应的 Agent 资源并终止推理
