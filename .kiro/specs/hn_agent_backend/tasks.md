# 实现计划：hn-agent 后端系统

## 概述

按依赖顺序实现 hn-agent 后端系统的全部模块。基础设施模块优先，逐步构建至 Agent 核心和应用层。每个任务构建在前序任务之上，确保无孤立代码。

## 任务

- [x] 1. 项目脚手架与基础结构
  - [x] 1.1 初始化项目结构和依赖配置
    - 创建 `hn_agent/` 和 `app/` 目录结构
    - 配置 `pyproject.toml` 依赖：langchain, langgraph, fastapi, chromadb, hypothesis, pydantic, pyyaml 等
    - 创建 `hn_agent/__init__.py` 导出公开接口（agents, sandbox, tools, models, mcp, skills, config, guardrails, memory, subagents, reflection, client）
    - 创建异常层次结构 `hn_agent/exceptions.py`（HarnessError, ConfigurationError, UnsupportedProviderError, CredentialError, SandboxError, SandboxTimeoutError, PathEscapeError, SkillValidationError, AuthorizationDeniedError, MCPConnectionError, VectorStoreError）
    - 创建 `tests/unit/`, `tests/properties/`, `tests/integration/` 目录
    - _需求: 21.1, 21.4_

  - [ ]* 1.2 编写属性测试：Harness 层不导入 App 层
    - **Property 47: Harness 层不导入 App 层**
    - **验证: 需求 21.1, 21.3**

  - [ ]* 1.3 编写属性测试：Harness 层公开接口完整性
    - **Property 48: Harness 层公开接口完整性**
    - **验证: 需求 21.4**

- [x] 2. 配置系统
  - [x] 2.1 实现配置模型和加载器
    - 创建 `hn_agent/config/models.py`：基于 Pydantic BaseModel 定义 AppConfig, AppSettings, ModelSettings, ProviderConfig, SandboxSettings, ToolSettings, MemorySettings, VectorStoreSettings, ExtensionsSettings, GuardrailSettings
    - 创建 `hn_agent/config/loader.py`：ConfigLoader 类，支持 YAML/JSON 加载、环境变量覆盖（HN_AGENT_ 前缀）、未知配置项警告忽略、必需项缺失抛出 ConfigurationError
    - 创建 `hn_agent/config/__init__.py` 导出公开接口
    - _需求: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 2.2 编写属性测试：配置加载往返一致性
    - **Property 1: 配置加载往返一致性**
    - **验证: 需求 1.1**

  - [ ]* 2.3 编写属性测试：环境变量覆盖优先级
    - **Property 2: 环境变量覆盖优先级**
    - **验证: 需求 1.2**

  - [ ]* 2.4 编写属性测试：未知配置项被忽略
    - **Property 3: 未知配置项被忽略**
    - **验证: 需求 1.4**

  - [ ]* 2.5 编写属性测试：必需配置项缺失抛出异常
    - **Property 4: 必需配置项缺失抛出异常**
    - **验证: 需求 1.5**

- [x] 3. 反射系统
  - [x] 3.1 实现反射解析器
    - 创建 `hn_agent/reflection/resolvers.py`：resolve_module, resolve_class（"module.path:ClassName" 格式）, resolve_variable 函数
    - 创建 `hn_agent/reflection/__init__.py` 导出公开接口
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_


  - [ ]* 3.2 编写属性测试：反射系统路径解析正确性
    - **Property 5: 反射系统路径解析正确性**
    - **验证: 需求 2.2, 2.3**

  - [ ]* 3.3 编写属性测试：反射系统无效路径错误处理
    - **Property 6: 反射系统无效路径错误处理**
    - **验证: 需求 2.4, 2.5**

- [x] 4. 模型工厂
  - [x] 4.1 实现模型工厂和 Provider 适配器
    - 创建 `hn_agent/models/base_provider.py`：ModelProvider Protocol 接口
    - 创建 `hn_agent/models/factory.py`：create_model 函数，根据模型名称前缀路由到对应 Provider
    - 创建 Provider 适配器：`openai_provider.py`, `anthropic_provider.py`, `deepseek_provider.py`, `google_provider.py`, `minimax_provider.py`, `qwen_provider.py`
    - 创建 `hn_agent/models/credential_loader.py`：从 Config_System 加载 API 凭证
    - 创建 `hn_agent/models/__init__.py` 导出公开接口
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [ ]* 4.2 编写属性测试：模型工厂对所有支持的提供商返回 BaseChatModel
    - **Property 7: 模型工厂对所有支持的提供商返回 BaseChatModel**
    - **验证: 需求 3.1**

  - [ ]* 4.3 编写属性测试：不支持的提供商抛出 UnsupportedProviderError
    - **Property 8: 不支持的提供商抛出 UnsupportedProviderError**
    - **验证: 需求 3.6**

  - [ ]* 4.4 编写属性测试：API 凭证缺失抛出 CredentialError
    - **Property 9: API 凭证缺失抛出 CredentialError**
    - **验证: 需求 3.7**

- [x] 5. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 6. 线程状态
  - [x] 6.1 实现线程状态 Schema 和 Reducer
    - 创建 `hn_agent/agents/thread_state.py`：ThreadState 类（继承 MessagesState），包含 messages, artifacts, images, title, thread_data 字段
    - 实现 artifacts_reducer（增量追加 + 按 ID 更新）和 images reducer
    - 实现 Artifact, ImageData 数据模型
    - 实现 ThreadState 的 JSON 序列化/反序列化
    - _需求: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 6.2 编写属性测试：ThreadState Reducer 一致性
    - **Property 18: ThreadState Reducer 一致性**
    - **验证: 需求 6.2, 6.3, 6.4**

  - [ ]* 6.3 编写属性测试：ThreadState JSON 序列化往返
    - **Property 19: ThreadState JSON 序列化往返**
    - **验证: 需求 6.5**

- [x] 7. 沙箱系统
  - [x] 7.1 实现沙箱抽象接口和 LocalProvider
    - 创建 `hn_agent/sandbox/provider.py`：SandboxProvider Protocol（execute, read_file, write_file, list_files）
    - 创建 `hn_agent/sandbox/path_translator.py`：translate_path 函数，防止路径逃逸（处理 ../, 绝对路径, 符号链接）
    - 创建 `hn_agent/sandbox/local/provider.py`：LocalProvider 实现
    - 创建 `hn_agent/sandbox/docker/provider.py`：DockerAioProvider 实现
    - 创建 `hn_agent/sandbox/tools.py`：bash, ls, read, write, str_replace 沙箱工具
    - 创建 `hn_agent/sandbox/middleware.py`：沙箱生命周期管理（创建/清理）
    - 创建 `hn_agent/sandbox/exceptions.py` 和 `hn_agent/sandbox/__init__.py`
    - _需求: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

  - [ ]* 7.2 编写属性测试：虚拟路径翻译防逃逸
    - **Property 20: 虚拟路径翻译防逃逸**
    - **验证: 需求 7.4**

  - [ ]* 7.3 编写属性测试：沙箱执行超时终止
    - **Property 21: 沙箱执行超时终止**
    - **验证: 需求 7.6**

  - [ ]* 7.4 编写属性测试：沙箱异常捕获结构化返回
    - **Property 22: 沙箱异常捕获结构化返回**
    - **验证: 需求 7.7**

- [x] 8. 护栏系统
  - [x] 8.1 实现护栏 Provider 和规则引擎
    - 创建 `hn_agent/guardrails/provider.py`：GuardrailProvider Protocol, AuthorizationResult, GuardrailContext 数据模型
    - 创建 `hn_agent/guardrails/builtin.py`：RuleBasedGuardrailProvider 实现，基于配置规则的授权检查
    - 创建 `hn_agent/guardrails/__init__.py`
    - _需求: 13.1, 13.2, 13.4, 13.5_

  - [ ]* 8.2 编写属性测试：护栏规则授权检查
    - **Property 37: 护栏规则授权检查**
    - **验证: 需求 13.2, 13.4**

- [x] 9. 上传管理
  - [x] 9.1 实现上传管理器和文档格式转换
    - 创建 `hn_agent/uploads/manager.py`：UploadManager 类（save, convert_to_markdown, get_metadata）
    - 实现 FileMetadata 数据模型（file_id, filename, size, mime_type, upload_time, markdown_path）
    - 实现 PDF/PPT/Excel/Word → Markdown 转换逻辑
    - 创建 `hn_agent/uploads/__init__.py`
    - _需求: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ]* 9.2 编写属性测试：上传文件元数据完整性
    - **Property 38: 上传文件元数据完整性**
    - **验证: 需求 14.1, 14.4**

- [x] 10. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 11. 记忆系统
  - [x] 11.1 实现短期记忆（更新器、防抖队列、原子存储）
    - 创建 `hn_agent/memory/updater.py`：MemoryUpdater 类，使用 LLM 从对话中提取关键信息
    - 创建 `hn_agent/memory/queue.py`：DebounceQueue 类，合并短时间内的多次记忆更新请求
    - 创建 `hn_agent/memory/storage.py`：MemoryStorage 类，原子文件 I/O（写入临时文件后 os.rename）
    - 创建 `hn_agent/memory/prompt.py`：build_memory_prompt 函数
    - _需求: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 11.2 实现长期记忆（向量化存储与语义检索）
    - 创建 `hn_agent/memory/embedding.py`：EmbeddingClient 类（text-embedding-3-small）
    - 创建 `hn_agent/memory/vector
    _store.py`：VectorStoreProvider Protocol 和 ChromaVectorStore 实现
    - 实现 MemoryChunk 数据模型（id, content, user_id, thread_id, embedding, created_at, metadata）
    - 将向量检索结果集成到 build_memory_prompt
    - 创建 `hn_agent/memory/__init__.py`
    - _需求: 10.8, 10.9, 10.10, 10.11, 10.12, 10.13_

  - [ ]* 11.3 编写属性测试：防抖队列合并请求
    - **Property 27: 防抖队列合并请求**
    - **验证: 需求 10.2**

  - [ ]* 11.4 编写属性测试：记忆存储原子往返
    - **Property 28: 记忆存储原子往返**
    - **验证: 需求 10.3**

  - [ ]* 11.5 编写属性测试：记忆提示词包含记忆内容
    - **Property 29: 记忆提示词包含记忆内容**
    - **验证: 需求 10.4**

  - [ ]* 11.6 编写属性测试：向量化记忆存储与检索往返
    - **Property 30: 向量化记忆存储与检索往返**
    - **验证: 需求 10.8, 10.10, 10.11**

  - [ ]* 11.7 编写属性测试：Embedding 向量维度一致性
    - **Property 31: Embedding 向量维度一致性**
    - **验证: 需求 10.9**

- [x] 12. MCP 集成
  - [x] 12.1 实现 MCP 客户端、缓存和 OAuth
    - 创建 `hn_agent/mcp/client.py`：MCPClient 类（connect, list_tools, call_tool），支持 stdio/SSE/HTTP 传输协议
    - 创建 `hn_agent/mcp/cache.py`：MCPToolCache 类，懒加载缓存机制
    - 创建 `hn_agent/mcp/oauth.py`：MCPOAuthHandler 类
    - 创建 `hn_agent/mcp/tools.py`：MCP 工具到 LangChain Tool 的转换适配
    - 创建 `hn_agent/mcp/__init__.py`
    - _需求: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [ ]* 12.2 编写属性测试：MCP 工具缓存懒加载
    - **Property 32: MCP 工具缓存懒加载**
    - **验证: 需求 11.2**

  - [ ]* 12.3 编写属性测试：MCP 工具转换为 LangChain Tool
    - **Property 33: MCP 工具转换为 LangChain Tool**
    - **验证: 需求 11.4**

- [x] 13. 技能系统
  - [x] 13.1 实现技能加载、解析和安装
    - 创建 `hn_agent/skills/types.py`：Skill 数据模型
    - 创建 `hn_agent/skills/parser.py`：SkillParser 类，解析 SKILL.md 的 YAML frontmatter
    - 创建 `hn_agent/skills/loader.py`：SkillLoader 类（discover, load）
    - 创建 `hn_agent/skills/installer.py`：SkillInstaller 类
    - 创建 `hn_agent/skills/validation.py`：技能文件格式验证
    - 创建 `hn_agent/skills/__init__.py`
    - _需求: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 13.2 编写属性测试：技能文件发现完整性
    - **Property 34: 技能文件发现完整性**
    - **验证: 需求 12.1**

  - [ ]* 13.3 编写属性测试：SKILL.md YAML frontmatter 解析
    - **Property 35: SKILL.md YAML frontmatter 解析**
    - **验证: 需求 12.2**

  - [ ]* 13.4 编写属性测试：技能文件验证
    - **Property 36: 技能文件验证**
    - **验证: 需求 12.3, 12.6**

- [x] 14. 检查点系统
  - [x] 14.1 实现 SQLite 检查点 Provider
    - 创建 `hn_agent/agents/checkpointer/provider.py`：SQLiteCheckpointer（同步 put/get）
    - 创建 `hn_agent/agents/checkpointer/async_provider.py`：AsyncSQLiteCheckpointer（异步 aput/aget）
    - 创建 `hn_agent/agents/checkpointer/__init__.py`
    - _需求: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ]* 14.2 编写属性测试：检查点存储往返
    - **Property 39: 检查点存储往返**
    - **验证: 需求 15.3, 15.4**

- [x] 15. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 16. 社区工具
  - [x] 16.1 实现社区工具集成
    - 创建 `hn_agent/community/tavily/` ：Tavily 搜索工具的 LangChain Tool 封装
    - 创建 `hn_agent/community/jina/`：Jina 内容提取工具封装
    - 创建 `hn_agent/community/firecrawl/`：Firecrawl 网页抓取工具封装
    - 创建 `hn_agent/community/duckduckgo/`：DuckDuckGo 搜索工具封装
    - 每个工具从 Config_System 加载 API 密钥，提供统一 BaseTool 接口
    - 创建 `hn_agent/community/__init__.py`
    - _需求: 19.1, 19.2, 19.3, 19.4, 19.5_

  - [ ]* 16.2 编写属性测试：社区工具接口一致性
    - **Property 44: 社区工具接口一致性**
    - **验证: 需求 19.2**

  - [ ]* 16.3 编写属性测试：社区工具错误结构化返回
    - **Property 45: 社区工具错误结构化返回**
    - **验证: 需求 19.4**

- [x] 17. 工具系统
  - [x] 17.1 实现工具加载器和内置工具
    - 创建 `hn_agent/tools/loader.py`：ToolLoader 类（load_tools, _load_sandbox_tools, _load_builtin_tools, _load_mcp_tools, _load_community_tools）
    - 创建内置工具：`hn_agent/tools/builtins/clarification_tool.py`, `present_file_tool.py`, `view_image_tool.py`, `task_tool.py`, `invoke_acp_agent_tool.py`, `setup_agent_tool.py`, `tool_search.py`
    - 每个工具提供 name, description, 参数 Schema 元数据
    - 创建 `hn_agent/tools/__init__.py`
    - _需求: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 17.2 编写属性测试：工具加载器按配置加载
    - **Property 23: 工具加载器按配置加载**
    - **验证: 需求 8.2**

  - [ ]* 17.3 编写属性测试：所有工具具备完整元数据
    - **Property 24: 所有工具具备完整元数据**
    - **验证: 需求 8.6**

- [x] 18. 子 Agent 系统
  - [x] 18.1 实现子 Agent 注册表、执行器和内置子 Agent
    - 创建 `hn_agent/subagents/config.py`：SubagentDefinition, SubagentTask, SubagentResult 数据模型
    - 创建 `hn_agent/subagents/registry.py`：SubagentRegistry 类（register, get）
    - 创建 `hn_agent/subagents/executor.py`：SubagentExecutor 类，双线程池（I/O + CPU），异步提交和执行
    - 创建 `hn_agent/subagents/builtins/general_purpose.py` 和 `bash_agent.py`
    - 创建 `hn_agent/subagents/__init__.py`
    - _需求: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 18.2 编写属性测试：子 Agent 注册表往返
    - **Property 25: 子 Agent 注册表往返**
    - **验证: 需求 9.1**

  - [ ]* 18.3 编写属性测试：子 Agent 错误捕获
    - **Property 26: 子 Agent 错误捕获**
    - **验证: 需求 9.6**

- [x] 19. 中间件链
  - [x] 19.1 实现中间件基类和链管理器
    - 创建 `hn_agent/agents/middlewares/base.py`：Middleware Protocol（pre_process, post_process）
    - 创建 `hn_agent/agents/middlewares/chain.py`：MiddlewareChain 类（run_pre 正序, run_post 逆序）
    - _需求: 5.1, 5.2, 5.3_

  - [x] 19.2 实现 14 个中间件
    - 创建 `hn_agent/agents/middlewares/thread_data.py`：加载线程关联数据
    - 创建 `hn_agent/agents/middlewares/uploads.py`：注入上传文件内容
    - 创建 `hn_agent/agents/middlewares/sandbox.py`：沙箱生命周期管理
    - 创建 `hn_agent/agents/middlewares/dangling_tool_call.py`：检测未完成工具调用
    - 创建 `hn_agent/agents/middlewares/guardrail.py`：工具调用授权检查
    - 创建 `hn_agent/agents/middlewares/summarization.py`：历史消息摘要压缩
    - 创建 `hn_agent/agents/middlewares/todolist.py`：任务列表状态维护
    - 创建 `hn_agent/agents/middlewares/title.py`：自动生成对话标题
    - 创建 `hn_agent/agents/middlewares/memory.py`：记忆上下文注入 + 记忆更新队列提交
    - 创建 `hn_agent/agents/middlewares/view_image.py`：图片数据注入
    - 创建 `hn_agent/agents/middlewares/subagent_limit.py`：子 Agent 并发限制
    - 创建 `hn_agent/agents/middlewares/clarification.py`：澄清需求检测
    - 创建 `hn_agent/agents/middlewares/loop_detection.py`：推理循环检测
    - 创建 `hn_agent/agents/middlewares/token_usage.py`：Token 用量统计
    - 创建 `hn_agent/agents/middlewares/__init__.py`
    - _需求: 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14, 5.15, 5.16, 5.17_

  - [ ]* 19.3 编写属性测试：中间件执行顺序不变性
    - **Property 11: 中间件执行顺序不变性**
    - **验证: 需求 5.2, 5.3**

  - [ ]* 19.4 编写属性测试：沙箱中间件生命周期往返
    - **Property 12: 沙箱中间件生命周期往返**
    - **验证: 需求 5.6, 7.8**

  - [ ]* 19.5 编写属性测试：悬挂工具调用检测
    - **Property 13: 悬挂工具调用检测**
    - **验证: 需求 5.7**

  - [ ]* 19.6 编写属性测试：摘要压缩阈值触发
    - **Property 14: 摘要压缩阈值触发**
    - **验证: 需求 5.9**

  - [ ]* 19.7 编写属性测试：子 Agent 并发限制
    - **Property 15: 子 Agent 并发限制**
    - **验证: 需求 5.14**

  - [ ]* 19.8 编写属性测试：循环检测终止
    - **Property 16: 循环检测终止**
    - **验证: 需求 5.16**

  - [ ]* 19.9 编写属性测试：Token 用量统计准确性
    - **Property 17: Token 用量统计准确性**
    - **验证: 需求 5.17**

- [x] 20. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 21. Lead Agent 核心
  - [x] 21.1 实现 Lead Agent 和系统提示词生成
    - 创建 `hn_agent/agents/lead_agent/agent.py`：create_lead_agent 函数，基于 LangGraph create_react_agent 构建 Agent 图
    - 创建 `hn_agent/agents/lead_agent/prompt.py`：build_system_prompt 函数，根据 Agent 配置、技能列表和记忆上下文生成系统提示词
    - 创建 `hn_agent/agents/lead_agent/__init__.py`
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 21.2 编写属性测试：系统提示词包含所有技能内容
    - **Property 10: 系统提示词包含所有技能内容**
    - **验证: 需求 4.5, 12.5**

- [x] 22. Agent 工厂与特性管理
  - [x] 22.1 实现 Agent 工厂和特性管理
    - 创建 `hn_agent/agents/features.py`：Features 数据类（sandbox_enabled, memory_enabled, subagent_enabled, guardrail_enabled, mcp_enabled），from_config 类方法
    - 创建 `hn_agent/agents/factory.py`：make_lead_agent 异步函数，组装中间件链 + 加载工具 + 选择模型 + 生成提示词 + 创建 LangGraph Agent
    - 实现 AgentConfig 数据模型
    - _需求: 20.1, 20.2, 20.3, 20.4, 20.5_

  - [ ]* 22.2 编写属性测试：特性配置控制加载
    - **Property 46: 特性配置控制加载**
    - **验证: 需求 20.3, 20.4**

- [x] 23. SSE 流式响应
  - [x] 23.1 实现 SSE 事件模型和流式生成器
    - 创建 SSEEvent 数据模型（event: token|tool_call|tool_result|subagent_start|subagent_result|done, data: dict）
    - 实现 stream_agent_response 异步生成器，将 LangGraph 流式输出转换为 SSE 事件流
    - 集成到 Lead Agent 的推理流程中
    - _需求: 22.1, 22.2, 22.3, 22.4, 22.5_

  - [ ]* 23.2 编写属性测试：SSE 事件类型合法性
    - **Property 49: SSE 事件类型合法性**
    - **验证: 需求 22.2**

- [x] 24. 嵌入式客户端
  - [x] 24.1 实现 HarnessClient
    - 创建 `hn_agent/client.py`：HarnessClient 类
    - 实现 chat（同步返回完整响应）、stream（异步生成器流式响应）、get_thread、list_threads 方法
    - 复用 Config_System 加载配置，内部调用 make_lead_agent 创建 Agent
    - _需求: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ]* 24.2 编写属性测试：嵌入式客户端接口对齐
    - **Property 40: 嵌入式客户端接口对齐**
    - **验证: 需求 16.2**

- [x] 25. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 26. Gateway API
  - [x] 26.1 实现 FastAPI 应用入口和配置
    - 创建 `app/gateway/app.py`：FastAPI 应用入口，CORS 配置，路由注册
    - 创建 `app/gateway/config.py`：Gat
    eway 配置（端口、CORS 等）
    - 创建 `app/gateway/path_utils.py`：路径工具函数
    - _需求: 17.1_

  - [x] 26.2 实现 10 个 API 路由模块
    - 创建 `app/gateway/routers/models.py`：GET /api/models
    - 创建 `app/gateway/routers/mcp.py`：GET /api/mcp
    - 创建 `app/gateway/routers/skills.py`：GET /api/skills
    - 创建 `app/gateway/routers/memory.py`：GET/PUT /api/memory
    - 创建 `app/gateway/routers/uploads.py`：POST /api/threads/{id}/uploads
    - 创建 `app/gateway/routers/threads.py`：GET/POST /api/threads, POST /api/threads/{id}/chat (SSE)
    - 创建 `app/gateway/routers/artifacts.py`：GET /api/threads/{id}/artifacts
    - 创建 `app/gateway/routers/suggestions.py`：GET /api/threads/{id}/suggestions
    - 创建 `app/gateway/routers/agents.py`：GET/POST /api/agents
    - 创建 `app/gateway/routers/channels.py`：GET/POST /api/channels
    - 所有路由进行输入验证，不合法请求返回 4xx 错误响应
    - _需求: 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 17.10, 17.11, 17.12_

  - [ ]* 26.3 编写属性测试：API 输入验证
    - **Property 41: API 输入验证**
    - **验证: 需求 17.12**

- [x] 27. IM 渠道桥接
  - [x] 27.1 实现渠道抽象基类和核心调度
    - 创建 `app/channels/base.py`：Channel 抽象基类（receive_message, send_message, setup_webhook）
    - 创建 `app/channels/manager.py`：ChannelManager 核心调度器
    - 创建 `app/channels/message_bus.py`：异步 MessageBus（publish, subscribe）
    - 创建 `app/channels/store.py`：ChannelStore（IM 会话 ID ↔ Agent 线程 ID 映射持久化）
    - 创建 `app/channels/service.py`：渠道生命周期管理（启动、停止、健康检查）
    - _需求: 18.1, 18.3, 18.4, 18.5, 18.6, 18.7, 18.9_

  - [x] 27.2 实现 IM 平台 Channel
    - 创建 `app/channels/feishu.py`：FeishuChannel 实现
    - 创建 `app/channels/slack.py`：SlackChannel 实现
    - 创建 `app/channels/telegram.py`：TelegramChannel 实现
    - 每个 Channel 实现消息解析、响应发送和 Webhook 设置
    - _需求: 18.2, 18.6, 18.8_

  - [ ]* 27.3 编写属性测试：MessageBus 消息投递
    - **Property 42: MessageBus 消息投递**
    - **验证: 需求 18.4**

  - [ ]* 27.4 编写属性测试：渠道会话映射往返
    - **Property 43: 渠道会话映射往返**
    - **验证: 需求 18.5**

- [x] 28. 最终检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。
  - 验证双层架构隔离：hn_agent/ 不导入 app/ 中的任何模块
  - 验证所有 22 个需求的验收标准均被任务覆盖

## 备注

- 标记 `*` 的任务为可选任务，可跳过以加速 MVP 开发
- 每个任务引用了具体的需求编号，确保可追溯性
- 检查点任务确保增量验证
- 属性测试验证 49 个正确性属性的通用正确性
- 单元测试验证具体示例和边界情况
