# Requirements Document

## Introduction

本需求文档描述将 hn-agent 项目的 Agent 模块从 LangChain v0.3+ / LangGraph v0.4+ 升级到 LangChain v1.0 / LangGraph v1.0 的重构工作。升级范围涵盖依赖版本、Agent 创建 API、流式响应、检查点系统和线程状态等核心模块，参考 LangChain 官方 Quickstart 文档完成迁移（https://docs.langchain.com/oss/python/langchain/quickstart）。
## Glossary

- **Lead_Agent**: 基于 LangGraph 构建的主 Agent 引擎，负责接收用户消息、调用工具、生成回复。
- **Agent_Factory**: Agent 工厂模块（`factory.py`），负责组装模型、工具、技能、检查点并创建 Lead_Agent 实例。
- **Streaming_Module**: SSE 流式响应模块（`streaming.py`），将 LangGraph 流式输出转换为 SSE 事件流。
- **Thread_State**: 线程状态 Schema（`thread_state.py`），定义 Agent 运行时的状态结构，继承 `MessagesState`。
- **Checkpointer**: 检查点 Provider（`checkpointer/`），基于 SQLite 的 Agent 状态持久化模块，包含同步和异步两种实现。
- **Middleware_Chain**: 中间件链管理器，按固定顺序执行 14 个中间件的 pre_process 和 post_process。
- **Embedded_Client**: 嵌入式客户端（`client.py`），提供进程内直接调用 Lead_Agent 的接口。
- **Dependency_Manifest**: 项目依赖声明文件（`pyproject.toml`），定义所有 Python 包依赖及版本约束。
- **Model_Factory**: 模型工厂（`models/factory.py`），根据模型名称前缀路由到对应 Provider 创建 `BaseChatModel`。
- **LangChain_v1**: LangChain 1.0 版本，包含 API 变更、废弃接口移除和新的 Agent 构建模式。
- **LangGraph_v1.0**: 与 LangChain v1.0 兼容的 LangGraph 版本，`create_react_agent` API 可能有签名变更。

## Requirements

### Requirement 1: 升级依赖版本

**User Story:** As a developer, I want to upgrade all LangChain ecosystem dependencies to v1.0 compatible versions, so that the project uses the latest stable API and receives ongoing support.

#### Acceptance Criteria

1. THE Dependency_Manifest SHALL declare `langchain>=1.0.0` as the langchain dependency version constraint.
2. THE Dependency_Manifest SHALL declare `langchain-core>=1.0.0` as the langchain-core dependency version constraint.
3. THE Dependency_Manifest SHALL declare `langchain-openai>=1.0.0` as the langchain-openai dependency version constraint.
4. THE Dependency_Manifest SHALL declare `langchain-anthropic>=1.0.0` as the langchain-anthropic dependency version constraint.
5. THE Dependency_Manifest SHALL declare `langchain-google-genai>=2.1.0` as the langchain-google-genai dependency version constraint compatible with LangChain v1.0.
6. THE Dependency_Manifest SHALL declare `langchain-community>=1.0.0` as the langchain-community dependency version constraint.
7. THE Dependency_Manifest SHALL declare `langgraph>=1.0.0` as the langgraph dependency version constraint compatible with LangChain v1.0.
8. WHEN all dependencies are upgraded, THE Dependency_Manifest SHALL allow successful resolution of all package versions without conflicts.

### Requirement 2: 迁移 Lead Agent 创建 API

**User Story:** As a developer, I want to migrate the Lead Agent creation to use LangChain v1.0 compatible `create_react_agent` API, so that the agent construction follows the latest recommended patterns.

#### Acceptance Criteria

1. THE Lead_Agent SHALL be created using the LangChain v1.0 `create_agent` function from `langchain.agents`.
2. WHEN `create_agent` is invoked, THE Lead_Agent SHALL pass the model, tools, and system_prompt parameters using the v1.0 API signature.
3. THE Lead_Agent SHALL accept a `BaseChatModel` instance (or string model identifier), a list of `BaseTool` instances, a system prompt string, and an optional checkpointer as creation parameters.
4. THE Lead_Agent SHALL use the `system_prompt` parameter name (replacing the deprecated `prompt` parameter from `create_react_agent`).
5. THE Lead_Agent SHALL return a `CompiledStateGraph` instance after creation.
6. IF `create_react_agent` raises an exception due to invalid parameters, THEN THE Lead_Agent SHALL propagate the exception with a descriptive log message.

### Requirement 3: 迁移流式响应模块

**User Story:** As a developer, I want to migrate the streaming module to use LangChain v1.0 compatible streaming API, so that SSE event streaming continues to work correctly after the upgrade.

#### Acceptance Criteria

1. THE Streaming_Module SHALL use the LangChain v1.0 compatible `astream_events` method to obtain streaming output from the Agent.
2. WHEN `astream_events` API signature changes in v1.0 (e.g., `version` parameter removal or default change), THE Streaming_Module SHALL adapt the invocation accordingly.
3. THE Streaming_Module SHALL map `on_chat_model_stream` events to SSE `token` events containing the content string.
4. THE Streaming_Module SHALL map `on_tool_start` events to SSE `tool_call` events containing the tool name and input.
5. THE Streaming_Module SHALL map `on_tool_end` events to SSE `tool_result` events containing the tool name and output.
6. WHEN the Agent streaming completes without error, THE Streaming_Module SHALL yield a final SSE `done` event with `{"finished": true}`.
7. IF an exception occurs during streaming, THEN THE Streaming_Module SHALL yield an SSE `done` event containing the error message and `{"finished": true}`.

### Requirement 4: 迁移检查点系统

**User Story:** As a developer, I want to migrate the checkpointer module to use LangChain v1.0 / LangGraph v0.5 compatible checkpoint API, so that agent state persistence continues to function correctly.

#### Acceptance Criteria

1. THE Checkpointer SHALL implement the `BaseCheckpointSaver` interface as defined in the LangChain v1.0 compatible `langgraph.checkpoint.base` module.
2. WHEN `BaseCheckpointSaver` method signatures change in the new version (e.g., `put`, `get_tuple`, `list`, `put_writes`), THE Checkpointer SHALL adapt its method signatures to match.
3. THE Checkpointer SHALL delegate to `SqliteSaver` from `langgraph.checkpoint.sqlite` for the synchronous provider.
4. THE Checkpointer SHALL delegate to `AsyncSqliteSaver` from `langgraph.checkpoint.sqlite.aio` for the asynchronous provider.
5. IF checkpoint data is corrupted or deserialization fails, THEN THE Checkpointer SHALL log the error and return None instead of raising an exception.
6. WHEN the `Checkpoint`, `CheckpointMetadata`, or `ChannelVersions` types change in the new version, THE Checkpointer SHALL use the updated type definitions.

### Requirement 5: 迁移线程状态 Schema

**User Story:** As a developer, I want to migrate the ThreadState schema to use LangChain v1.0 compatible MessagesState and message types, so that the agent runtime state remains correctly structured.

#### Acceptance Criteria

1. THE Thread_State SHALL inherit from `MessagesState` as provided by the LangChain v1.0 compatible `langgraph.graph` module.
2. THE Thread_State SHALL use `BaseMessage`, `HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage` from `langchain_core.messages` as provided in LangChain v1.0.
3. THE Thread_State SHALL use `message_to_dict` and `messages_from_dict` from `langchain_core.messages` for JSON serialization and deserialization.
4. WHEN any message type or serialization function is relocated or renamed in LangChain v1.0, THE Thread_State SHALL update the import paths accordingly.
5. THE Thread_State SHALL preserve the custom `artifacts_reducer` and `images` reducer behavior after migration.

### Requirement 6: 迁移 Agent 工厂模块

**User Story:** As a developer, I want to migrate the Agent Factory to use LangChain v1.0 compatible APIs throughout the assembly pipeline, so that agent creation works end-to-end with the upgraded dependencies.

#### Acceptance Criteria

1. THE Agent_Factory SHALL use the LangChain v1.0 compatible `create_model` function from Model_Factory to create `BaseChatModel` instances.
2. THE Agent_Factory SHALL pass the created model, tools, system prompt, and checkpointer to the LangChain v1.0 compatible `create_lead_agent` function.
3. THE Agent_Factory SHALL return a `CompiledStateGraph` instance from `langgraph.graph.state` as the created agent.
4. WHEN any import path for LangGraph or LangChain types changes in v1.0, THE Agent_Factory SHALL update the import statements accordingly.

### Requirement 7: 迁移嵌入式客户端

**User Story:** As a developer, I want to migrate the Embedded Client to work with the LangChain v1.0 upgraded agent module, so that in-process agent access continues to function correctly.

#### Acceptance Criteria

1. THE Embedded_Client SHALL use `HumanMessage` from `langchain_core.messages` as provided in LangChain v1.0 to construct input messages.
2. THE Embedded_Client SHALL invoke the LangChain v1.0 compatible `stream_agent_response` function for streaming responses.
3. THE Embedded_Client SHALL create agent instances through the LangChain v1.0 compatible `make_lead_agent` factory function.
4. WHEN the `CompiledStateGraph` interface changes in the new version, THE Embedded_Client SHALL adapt its agent invocation accordingly.

### Requirement 8: 迁移模型工厂 Provider

**User Story:** As a developer, I want to migrate all model provider implementations to use LangChain v1.0 compatible provider packages, so that model creation works with the upgraded dependencies.

#### Acceptance Criteria

1. THE Model_Factory SHALL use `BaseChatModel` from `langchain_core.language_models` as provided in LangChain v1.0.
2. THE Model_Factory SHALL use `ChatOpenAI` from `langchain_openai` v1.0 for OpenAI model creation.
3. THE Model_Factory SHALL use `ChatAnthropic` from `langchain_anthropic` v1.0 for Anthropic model creation.
4. THE Model_Factory SHALL use `ChatGoogleGenerativeAI` from `langchain_google_genai` for Google model creation compatible with LangChain v1.0.
5. WHEN any provider class constructor signature changes in v1.0, THE Model_Factory SHALL adapt the parameter passing accordingly.

### Requirement 9: 保持中间件链兼容性

**User Story:** As a developer, I want the middleware chain to remain fully functional after the LangChain v1.0 upgrade, so that all 14 middlewares continue to execute correctly.

#### Acceptance Criteria

1. THE Middleware_Chain SHALL execute all 14 middlewares in the defined order during pre_process (forward order) and post_process (reverse order).
2. WHEN any middleware imports LangChain types (e.g., message types, tool types), THE Middleware_Chain SHALL ensure those imports are updated to LangChain v1.0 compatible paths.
3. THE Middleware_Chain SHALL preserve the `Middleware` protocol interface (`pre_process` and `post_process` methods) without changes.

### Requirement 10: 移除废弃 API 调用

**User Story:** As a developer, I want to remove all deprecated LangChain v0.3 API calls, so that the codebase is clean and does not trigger deprecation warnings under v1.0.

#### Acceptance Criteria

1. THE Lead_Agent SHALL use no deprecated `langchain` or `langgraph` API calls as defined by LangChain v1.0 deprecation notices.
2. THE Streaming_Module SHALL use no deprecated `astream_events` parameters (e.g., the `version` parameter if it is removed in v1.0).
3. THE Checkpointer SHALL use no deprecated `langgraph.checkpoint` API calls.
4. WHEN a deprecated API is identified during migration, THE Agent_Factory SHALL replace the deprecated call with the recommended v1.0 alternative.

### Requirement 11: 验证升级后的端到端功能

**User Story:** As a developer, I want to verify that the entire agent pipeline works end-to-end after the upgrade, so that I have confidence the migration is complete and correct.

#### Acceptance Criteria

1. WHEN a user message is sent through the Embedded_Client, THE Lead_Agent SHALL process the message and return a response.
2. WHEN a user message is sent through the Streaming_Module, THE Lead_Agent SHALL produce a stream of SSE events including at least one `token` event and a final `done` event.
3. WHEN the Lead_Agent is created with a Checkpointer, THE Checkpointer SHALL successfully persist and restore agent state across invocations.
4. THE Agent_Factory SHALL successfully create a Lead_Agent instance with the default configuration without raising exceptions.
