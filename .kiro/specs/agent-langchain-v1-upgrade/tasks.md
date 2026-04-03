# Implementation Plan: LangChain v1.0 升级

## Overview

按依赖拓扑排序，自底向上将 hn-agent 的 9 个核心模块从 LangChain v0.3+ / LangGraph v0.4+ 迁移到 LangChain v1.0 / LangGraph v1.0。每个任务对应一个模块的迁移工作，包含代码修改和测试验证。

## Tasks

- [x] 1. 升级依赖版本 (`pyproject.toml`)
  - [x] 1.1 更新 `pyproject.toml` 中所有 LangChain 生态依赖版本约束
    - 将 `langchain>=0.3.0` 改为 `langchain>=1.0.0`
    - 将 `langchain-core>=0.3.0` 改为 `langchain-core>=1.0.0`
    - 将 `langchain-openai>=0.3.0` 改为 `langchain-openai>=1.0.0`
    - 将 `langchain-anthropic>=0.3.0` 改为 `langchain-anthropic>=1.0.0`
    - 将 `langchain-google-genai>=2.0.0` 改为 `langchain-google-genai>=2.1.0`
    - 将 `langchain-community>=0.3.0` 改为 `langchain-community>=1.0.0`
    - 将 `langgraph>=0.4.0` 改为 `langgraph>=1.0.0`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  - [ ]* 1.2 编写单元测试验证 `pyproject.toml` 依赖版本约束正确
    - 解析 `pyproject.toml` 验证每个 LangChain 依赖的版本下限
    - _Requirements: 1.8_

- [x] 2. 迁移模型工厂 Provider (`models/`)
  - [x] 2.1 验证并适配各 Provider 的 v1.0 导入路径和构造函数签名
    - 检查 `models/factory.py` 中 `BaseChatModel` 导入路径
    - 检查 `models/openai_provider.py` 中 `ChatOpenAI` 构造函数参数
    - 检查 `models/anthropic_provider.py` 中 `ChatAnthropic` 构造函数参数
    - 检查 `models/google_provider.py` 中 `ChatGoogleGenerativeAI` 构造函数参数
    - 检查 `models/deepseek_provider.py`、`models/minimax_provider.py`、`models/qwen_provider.py`
    - 更新所有因 v1.0 变更而需要修改的导入路径和参数
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - [ ]* 2.2 编写单元测试验证各 Provider 使用正确的 v1.0 类
    - 验证 `create_model` 对各前缀路由到正确的 Provider
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 3. 迁移线程状态 (`thread_state.py`)
  - [x] 3.1 更新 `thread_state.py` 中的 LangChain/LangGraph 导入路径
    - 验证 `MessagesState` 从 `langgraph.graph` 导入是否仍有效，如有变更则更新
    - 验证 `BaseMessage`, `HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage` 导入路径
    - 验证 `message_to_dict`, `messages_from_dict` 导入路径
    - 确保 `ThreadState` 继承和自定义 reducer 逻辑不受影响
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [ ]* 3.2 编写属性测试验证消息序列化往返一致性
    - **Property 5: 消息序列化往返一致性**
    - 使用 hypothesis 随机生成 HumanMessage/AIMessage/SystemMessage/ToolMessage 列表
    - 验证 `message_to_dict` → `messages_from_dict` 往返后内容等价
    - **Validates: Requirements 5.3**
  - [ ]* 3.3 编写属性测试验证 artifacts_reducer 合并正确性
    - **Property 6: Artifacts Reducer 合并正确性**
    - 使用 hypothesis 随机生成 Artifact 列表（含重复/不重复 ID）
    - 验证替换、追加和 ID 唯一性
    - **Validates: Requirements 5.5**

- [ ] 4. 迁移检查点系统 (`checkpointer/`)
  - [ ] 4.1 更新 `checkpointer/provider.py` 中的导入路径和方法签名
    - 验证 `BaseCheckpointSaver`, `Checkpoint`, `CheckpointMetadata`, `CheckpointTuple`, `ChannelVersions` 导入路径
    - 验证 `SqliteSaver` 导入路径和构造函数
    - 适配 `put`, `put_writes`, `get_tuple`, `list` 方法签名（如有变更）
    - _Requirements: 4.1, 4.2, 4.3, 4.6_
  - [ ] 4.2 更新 `checkpointer/async_provider.py` 中的导入路径和方法签名
    - 验证 `AsyncSqliteSaver` 导入路径和构造函数
    - 适配 `aput`, `aput_writes`, `aget_tuple`, `alist` 方法签名（如有变更）
    - _Requirements: 4.1, 4.2, 4.4, 4.6_
  - [ ]* 4.3 编写属性测试验证检查点损坏容错
    - **Property 4: 检查点损坏容错**
    - 验证损坏数据下 `get_tuple` 返回 None 而非抛出异常
    - **Validates: Requirements 4.5**
  - [ ]* 4.4 编写属性测试验证检查点持久化往返一致性
    - **Property 8: 检查点持久化往返一致性**
    - 验证 `put` → `get_tuple` 往返后数据等价
    - **Validates: Requirements 11.3**

- [ ] 5. Checkpoint - 底层模块迁移验证
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. 迁移 Lead Agent 创建 (`lead_agent/agent.py`)
  - [ ] 6.1 将 `create_react_agent` 迁移到 `create_agent`
    - 将 `from langgraph.prebuilt import create_react_agent` 改为 `from langchain.agents import create_agent`
    - 将 `prompt=system_prompt` 参数改为 `system_prompt=system_prompt`
    - 保持 `create_lead_agent` 函数签名不变
    - 移除所有废弃 API 调用
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 10.1_
  - [ ]* 6.2 编写属性测试验证 Lead Agent 返回类型
    - **Property 1: Lead Agent 返回类型正确性**
    - 使用 Mock BaseChatModel 和随机工具列表验证返回 `CompiledStateGraph`
    - **Validates: Requirements 2.5**

- [ ] 7. 迁移中间件链 (`middlewares/`)
  - [ ] 7.1 检查并更新中间件模块中的 LangChain 类型导入
    - 扫描所有 14 个中间件文件，更新任何 LangChain/LangGraph 导入路径
    - 验证 `Middleware` Protocol 和 `MiddlewareChain` 不受影响
    - _Requirements: 9.1, 9.2, 9.3_
  - [ ]* 7.2 编写属性测试验证中间件执行顺序
    - **Property 7: 中间件执行顺序**
    - 验证 `run_pre` 正序、`run_post` 逆序执行
    - **Validates: Requirements 9.1**

- [ ] 8. 迁移流式响应 (`streaming.py`)
  - [ ] 8.1 更新 `streaming.py` 中的 `astream_events` 调用
    - 移除 `version="v2"` 参数（v1.0 默认即为 v2）
    - 验证 `CompiledStateGraph` 导入路径
    - 验证事件类型名称（`on_chat_model_stream`, `on_tool_start`, `on_tool_end`）是否变更
    - _Requirements: 3.1, 3.2, 10.2_
  - [ ]* 8.2 编写属性测试验证流式事件映射正确性
    - **Property 2: 流式事件映射正确性**
    - 随机生成 LangGraph 事件字典，验证映射结果的 event 和 data 字段
    - **Validates: Requirements 3.3, 3.4, 3.5**
  - [ ]* 8.3 编写属性测试验证流式响应终止事件
    - **Property 3: 流式响应终止事件**
    - 验证 `stream_agent_response` 最后一个事件为 `done` 且包含 `{"finished": true}`
    - **Validates: Requirements 3.6**

- [ ] 9. 迁移 Agent 工厂 (`factory.py`)
  - [ ] 9.1 更新 `factory.py` 中的导入路径和调用方式
    - 验证 `CompiledStateGraph` 从 `langgraph.graph.state` 导入是否仍有效
    - 确保 `create_lead_agent` 和 `create_model` 调用与 v1.0 兼容
    - 更新所有因 v1.0 变更而需要修改的导入语句
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 10.4_
  - [ ]* 9.2 编写单元测试验证 `make_lead_agent` 默认配置不抛异常
    - Mock 模型和工具，验证工厂组装流程正常
    - _Requirements: 11.4_

- [ ] 10. 迁移嵌入式客户端 (`client.py`)
  - [ ] 10.1 更新 `client.py` 中的 LangChain 导入路径
    - 验证 `HumanMessage` 从 `langchain_core.messages` 导入是否仍有效
    - 确保 `stream_agent_response` 和 `make_lead_agent` 调用与 v1.0 兼容
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [ ]* 10.2 编写单元测试验证嵌入式客户端基本流程
    - Mock Agent，验证 `chat` 和 `stream` 方法正常工作
    - _Requirements: 11.1, 11.2_

- [ ] 11. Checkpoint - 全模块迁移验证
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. 清理废弃 API 并最终验证
  - [ ] 12.1 全局扫描并移除所有废弃 LangChain v0.3 API 调用
    - 搜索所有 Python 文件中的 `langgraph.prebuilt.create_react_agent` 引用
    - 搜索 `version="v2"` 等废弃参数用法
    - 搜索 `prompt=` 参数（应已改为 `system_prompt=`）
    - 确保无遗漏的废弃导入路径
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  - [ ] 12.2 更新 `hn_agent/agents/__init__.py` 等公共导出模块
    - 确保所有公共 API 导出正常
    - _Requirements: 6.4_

- [ ] 13. Final checkpoint - 全部测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after bottom-layer and full migration
- Property tests validate universal correctness properties from the design document
- 迁移顺序严格遵循设计文档中的依赖拓扑：pyproject.toml → models → thread_state → checkpointer → lead_agent → middlewares → streaming → factory → client
