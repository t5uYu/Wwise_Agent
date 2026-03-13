# Wwise Agent

基于 AI 的 Audiokinetic Wwise 智能助手，支持自主多轮工具调用、联网搜索、WAAPI 批量操作、Plan 模式规划复杂任务、大脑启发式长期记忆系统，配备现代深色 UI 与双语支持。另提供标准 MCP Server，支持 Claude Desktop / Cursor 等外部 AI 客户端直接调用 Wwise 工具。

基于 **OpenAI Function Calling** 协议，Agent 可以查询项目结构、搜索对象、创建/修改/移动/删除 Wwise 对象、批量操作、Event 管理、RTPC 绑定、Effect 管理、Bus 路由、联网搜索、查询本地文档、创建结构化执行计划、从历史交互中持续学习 —— 全部在自主循环中迭代完成。

## 核心特性

### Agent 循环

AI 以自主 **Agent 循环** 运行：接收用户请求 → 规划步骤 → 调用工具 → 检查结果 → 继续调用 → 直到任务完成。提供三种模式：

- **Agent 模式** — 完整权限，AI 可以使用全部 30 个工具，创建、修改、移动、删除对象，设置属性，批量操作，管理 Event/Bus/RTPC/Effect。
- **Ask 模式** — 只读模式，AI 只能查询项目结构、检查属性、搜索对象和提供分析。所有修改类工具被模式守卫拦截。
- **Plan 模式** — AI 进入规划阶段：只读调研当前项目，通过 `ask_question` 澄清需求，然后生成带 DAG 流程图的结构化执行计划。用户审核确认后方可执行。

```
用户请求 → AI 规划 → 调用工具 → 检查结果 → 调用更多工具 → … → 最终回复
```

- **多轮工具调用** — AI 自主决定调用哪些工具、以什么顺序执行
- **Todo 任务系统** — 复杂任务自动拆分为子任务，实时跟踪状态
- **流式输出** — 实时显示思考过程和回复内容
- **深度思考** — 原生支持推理模型（DeepSeek-R1、GLM-4.7、Claude `<think>` 标签）
- **随时中断** — 可在任意时刻停止正在运行的 Agent 循环
- **智能上下文管理** — 按轮次裁剪对话，永不截断用户/助手消息，仅压缩工具结果
- **长期记忆** — 大脑启发式三层记忆系统（事件记忆、抽象知识、策略记忆），基于奖励驱动的学习与自动反思
- **确认模式** — 修改操作前内联预览确认卡片，安全可控
- **Wwise 路径可点击** — AI 回复中的 `\Actor-Mixer Hierarchy\...\MySound` 路径自动变为链接，点击即可在 Wwise 中定位到对应对象

### 支持的 AI 提供商

| 提供商 | 模型 | 说明 |
|--------|------|------|
| **DeepSeek** | `deepseek-chat`、`deepseek-reasoner` (R1) | 性价比高，响应快，支持 Function Calling 和推理 |
| **智谱 GLM** | `glm-4.7` | 国内访问稳定，原生推理与工具调用 |
| **OpenAI** | `gpt-5.2`、`gpt-5.3-codex` | 能力强大，完整 Function Calling 与 Vision 支持 |
| **Ollama**（本地） | `qwen2.5:14b`、任意本地模型 | 隐私优先，自动检测可用模型 |
| **Duojie**（中转） | `claude-sonnet-4-5`、`claude-opus-4-5-kiro`、`claude-opus-4-6-normal`、`claude-opus-4-6-kiro`、`claude-haiku-4-5`、`gemini-3-pro-image-preview`、`glm-4.7`、`glm-5`、`kimi-k2.5`、`MiniMax-M2.5`、`qwen3.5-plus`、`gpt-5.3-codex` | 通过中转接口访问 Claude、Gemini、GLM、Kimi、MiniMax、Qwen 模型 |
| **WLAI** | `gpt-4o`、`claude-sonnet-4-6`、`claude-opus-4-6`、`deepseek-chat`、`gemini-2.0-flash` 等 | 多模型中转 |

### 图片/多模态输入

- **多模态消息** — 为支持视觉的模型附加图片（PNG/JPG/GIF/WebP）
- **粘贴与拖拽** — `Ctrl+V` 从剪贴板粘贴图片，或直接拖拽图片文件到输入框
- **文件选择器** — 点击「+」→ Attach Image 从磁盘选择图片
- **图片预览** — 发送前在输入框上方显示缩略图，支持单独移除；点击缩略图可放大查看

### 深色 UI

- 深邃蓝黑主题（`#0a0a12` 色调），现代暗色风格
- 思考过程、工具调用、执行结果均可折叠/展开
- **可点击 Wwise 路径** — 回复中的 `\Events\Default Work Unit\Play_BGM` 等路径自动变为绿色链接，点击即可在 Wwise 中定位
- **AuroraBar 流光条** — AI 生成时左侧银白流动渐变光带
- **Token 分析** — 实时显示 Token 用量、推理 Token、Cache 命中率和按模型计费的费用估算（点击查看详细分析面板）
- 多会话标签页 — 同时运行多个独立对话
- AI 回复一键复制
- `Enter` 发送消息，`Shift+Enter` 换行
- **字号缩放** — 溢出菜单 → Font 滑块控制，70%~150%
- **双语 UI** — 通过溢出菜单切换中文/英文界面，所有 UI 元素和系统提示词动态重译
- **WwisePreviewInline** — 确认模式下的内联操作预览卡片（显示工具名称和参数，Accept/Cancel）
- **批量操作栏** — Undo All / Keep All 按钮

## 可用工具（30 个）

### 查询工具（9 个）

| 工具 | 说明 |
|------|------|
| `get_project_hierarchy` | 获取 Wwise 项目顶层结构概览（各 Hierarchy 子节点数量、Wwise 版本） |
| `get_object_properties` | 获取对象属性详情（支持分页，设置属性前必须先调用确认属性名） |
| `search_objects` | 按关键词模糊搜索 Wwise 对象（支持按类型过滤） |
| `get_bus_topology` | 获取 Master-Mixer Hierarchy 中所有 Bus 的拓扑结构 |
| `get_event_actions` | 获取 Event 下所有 Action 的详情（类型、Target 引用） |
| `get_soundbank_info` | 获取 SoundBank 信息（列表或指定 Bank 详情） |
| `get_rtpc_list` | 获取所有 Game Parameter（RTPC）列表 |
| `get_selected_objects` | 获取 Wwise Authoring 中当前选中的对象（无需知道路径） |
| `get_effect_chain` | 获取对象或 Bus 的 Effect 插件链（最多 4 个插槽） |

### 操作工具（10 个）

| 工具 | 说明 |
|------|------|
| `create_object` | 创建 Wwise 对象（Sound、ActorMixer、BlendContainer、RandomSequenceContainer、SwitchContainer、Folder 等） |
| `set_property` | 设置对象的一个或多个属性（Volume、Pitch、LPF、HPF、Positioning、Streaming 等） |
| `create_event` | 创建 Event + Action 并设置 Target 引用（Play/Stop/Pause/Resume/Break/Mute/UnMute） |
| `assign_bus` | 将对象路由到指定 Bus（设置 OverrideOutput + OutputBus 引用） |
| `delete_object` | 删除对象（默认检查是否被 Action 引用，force 模式跳过检查） |
| `move_object` | 移动对象到新父节点 |
| `preview_event` | 通过 Wwise Transport API 试听 Event（play/stop/pause/resume） |
| `set_rtpc_binding` | 将 Game Parameter 绑定到对象属性，设置驱动曲线控制点 |
| `add_effect` | 为对象或 Bus 添加 Effect 插件（RoomVerb、Delay、Compressor、PeakLimiter、ParametricEQ 等 16 种） |
| `remove_effect` | 清空对象上的所有 Effect 插槽 |

### 批量操作工具（4 个）

| 工具 | 说明 |
|------|------|
| `batch_create` | 批量创建对象 — flat 模式（同一父节点下批量创建同级对象）/ tree 模式（一次性创建嵌套层级结构），全部操作包裹在 Undo Group 中可一键撤销 |
| `batch_set_property` | 批量设置属性 — 统一设置（targets + properties）/ 独立设置（items 数组）/ 按类型过滤自动设置（type_filter），支持 Streaming、Volume、Positioning 等所有属性 |
| `batch_delete` | 批量删除对象 — 路径列表或按类型+名称过滤，dry_run 试运行预览，引用保护（被 Event 引用的自动跳过） |
| `batch_move` | 批量移动对象 — 统一目标模式（全部移到同一父节点）/ 独立映射模式（items 数组） |

### 验证工具（2 个）

| 工具 | 说明 |
|------|------|
| `verify_structure` | 结构完整性验证 — 检查孤儿 Event、Action 无 Target、Sound 无 Bus、音量/Pitch 范围异常 |
| `verify_event_completeness` | Event 完整性验证 — 检查 Action Target、音频文件存在性、SoundBank 包含状态 |

### 兜底工具（1 个）

| 工具 | 说明 |
|------|------|
| `execute_waapi` | 直接执行原始 WAAPI 调用（受黑名单保护，project.open/close/save 等危险操作被拦截） |

### Skill 元工具（2 个）

| 工具 | 说明 |
|------|------|
| `list_skills` | 列出所有可用的 Wwise Skill 元数据 |
| `run_skill` | 执行指定的 Wwise Skill |

### 联网与文档（2 个）

| 工具 | 说明 |
|------|------|
| `web_search` | 联网搜索（Brave/DuckDuckGo 自动降级，带缓存） |
| `fetch_webpage` | 获取网页正文内容（分页、编码自适应） |

### 文档检索（内置）

| 工具 | 说明 |
|------|------|
| `search_local_doc` | 搜索本地 Wwise 文档索引（WAAPI 函数签名、对象类型属性、知识库文章） |

### 任务管理（2 个）

| 工具 | 说明 |
|------|------|
| `add_todo` | 添加任务到 Todo 列表 |
| `update_todo` | 更新任务状态（pending / in_progress / done / error） |

## Skill 系统

Skill 是预定义的 Wwise 工具函数，通过 WAAPI 与 Wwise Authoring 交互。每个 Skill 文件放在 `skills/` 目录下，包含 `SKILL_INFO` 元数据和 `run()` 入口函数，启动时自动扫描注册。

| Skill | 说明 |
|-------|------|
| `get_project_hierarchy` | 项目顶层结构概览 |
| `get_object_properties` | 对象属性详情（分页） |
| `search_objects` | 模糊搜索对象 |
| `get_bus_topology` | Bus 拓扑结构 |
| `get_event_actions` | Event Action 详情 |
| `get_soundbank_info` | SoundBank 信息 |
| `get_rtpc_list` | RTPC 列表 |
| `get_selected_objects` | 当前选中对象 |
| `get_effect_chain` | Effect 插件链 |
| `create_object` | 创建对象 |
| `create_event` | 创建 Event + Action |
| `set_property` | 设置属性 |
| `assign_bus` | Bus 路由 |
| `delete_object` | 删除对象（引用检查） |
| `move_object` | 移动对象 |
| `preview_event` | 试听 Event |
| `set_rtpc_binding` | RTPC 绑定 |
| `add_effect` | 添加 Effect |
| `remove_effect` | 移除 Effect |
| `execute_waapi` | 原始 WAAPI 调用 |
| `verify_structure` | 结构完整性验证 |
| `verify_event_completeness` | Event 完整性验证 |
| `batch_create` | 批量创建对象 |
| `batch_set_property` | 批量设置属性 |
| `batch_delete` | 批量删除对象 |
| `batch_move` | 批量移动对象 |

## 项目结构

```
Wwise_Agent/
├── launcher.py                      # 启动入口
├── pyproject.toml                   # 项目配置
├── VERSION                          # 语义版本文件（0.1.0）
├── README.md                        # 项目文档
├── lib/                             # 内置依赖库
├── config/                          # 运行时配置
│   └── wwise_ai.ini                # API Key 及设置
├── cache/                           # 运行时缓存
│   ├── conversations/              # 对话历史
│   ├── memory/                     # 记忆数据库（agent_memory.db、growth_profile.json）
│   ├── plans/                      # Plan 模式数据文件（plan_{session_id}.json）
│   ├── doc_index/                  # 文档索引缓存
│   └── workspace/                  # 工作区状态（workspace.json）
├── shared/                          # 共享工具
│   └── common_utils.py             # 路径与配置工具
├── trainData/                       # 导出的训练数据（JSONL）
│
├── wwise_agent/                     # GUI 客户端 + AI Agent 逻辑
│   ├── main.py                     # 模块入口与窗口管理
│   ├── core/
│   │   ├── main_window.py          # 主窗口（工作区保存/恢复）
│   │   ├── agent_runner.py         # AgentRunnerMixin — Agent 循环辅助、确认模式、工具调度
│   │   └── session_manager.py      # SessionManagerMixin — 多会话创建/切换/关闭
│   ├── ui/
│   │   ├── ai_tab.py              # AI Agent 标签页（Mixin 宿主、Agent 循环、上下文管理、流式 UI）
│   │   ├── cursor_widgets.py      # UI 组件（主题、对话块、Todo、Token 分析、Plan 查看器）
│   │   ├── header.py              # HeaderMixin — 顶部设置栏（提供商、模型、功能开关）
│   │   ├── input_area.py          # InputAreaMixin — 输入区域、模式切换、确认模式 UI
│   │   ├── chat_view.py           # ChatViewMixin — 对话显示、滚动控制、Toast 消息
│   │   ├── i18n.py                # 国际化 — 中英双语支持（800+ 条翻译）
│   │   ├── theme_engine.py        # QSS 模板渲染与字号缩放引擎
│   │   ├── font_settings_dialog.py # 字号缩放滑块对话框
│   │   └── style_template.qss    # 集中式 QSS 主题样式表
│   ├── skills/                     # Wwise 工具函数（26 个 Skill + helpers）
│   │   ├── __init__.py            # Skill 注册表 & 动态加载器
│   │   ├── _waapi_helpers.py      # WAAPI 连接 & 通用工具（内部模块）
│   │   ├── get_project_hierarchy.py
│   │   ├── get_object_properties.py
│   │   ├── search_objects.py
│   │   ├── get_bus_topology.py
│   │   ├── get_event_actions.py
│   │   ├── get_soundbank_info.py
│   │   ├── get_rtpc_list.py
│   │   ├── get_selected_objects.py
│   │   ├── get_effect_chain.py
│   │   ├── create_object.py
│   │   ├── create_event.py
│   │   ├── set_property.py
│   │   ├── assign_bus.py
│   │   ├── delete_object.py
│   │   ├── move_object.py
│   │   ├── preview_event.py
│   │   ├── set_rtpc_binding.py
│   │   ├── add_effect.py
│   │   ├── remove_effect.py
│   │   ├── execute_waapi.py
│   │   ├── verify_structure.py
│   │   ├── verify_event_completeness.py
│   │   ├── batch_create.py
│   │   ├── batch_set_property.py
│   │   ├── batch_delete.py
│   │   └── batch_move.py
│   └── utils/
│       ├── ai_client.py           # AI API 客户端（流式传输、Function Calling、联网搜索、30 个工具定义）
│       ├── wwise_backend.py       # Wwise 工具执行器（基于 Skills 系统的分发层）
│       ├── doc_rag.py             # 本地文档索引（WAAPI 函数、对象类型、知识库 O(1) 查找）
│       ├── token_optimizer.py     # Token 预算与压缩策略（tiktoken 精准计数）
│       ├── ultra_optimizer.py     # 系统提示词与工具定义优化器
│       ├── training_data_exporter.py # 对话导出为训练数据 JSONL
│       ├── updater.py             # 自动更新器（GitHub Releases、ETag 缓存）
│       ├── plan_manager.py        # Plan 模式数据模型与持久化
│       ├── memory_store.py        # 三层记忆存储（事件/抽象/策略）SQLite + numpy embedding
│       ├── embedding.py           # 本地文本 Embedding（sentence-transformers / 回退方案）
│       ├── reward_engine.py       # 奖励评分与记忆重要度更新
│       ├── reflection.py          # 规则反思 + LLM 深度反思模块
│       └── growth_tracker.py      # 成长追踪与个性特征形成
│
└── wwise_mcp/                      # WAAPI 通信层 + MCP Server
    ├── __init__.py
    ├── server.py                   # MCP Server 入口（stdio 传输）
    ├── config/
    │   └── settings.py            # WAAPI 连接配置
    ├── core/
    │   ├── adapter.py             # WAAPI 封装层（WwiseAdapter）
    │   ├── connection.py          # WebSocket 连接管理
    │   └── exceptions.py          # 异常体系（6 种分类异常）
    ├── prompts/
    │   └── system_prompt.py       # System Prompt + 动态上下文
    ├── rag/
    │   └── context.py             # RAG 上下文收集
    └── tools/                      # 22 个 MCP 工具函数
        ├── __init__.py            # 工具注册中心
        ├── query.py               # 9 个查询工具
        ├── action.py              # 10 个操作工具
        ├── verify.py              # 2 个验证工具
        └── fallback.py            # 1 个兜底工具
```

## 快速开始

### 环境要求

- **Python >= 3.10**
- **PySide6 或 PySide2**（Qt GUI）
- **Wwise Authoring Tool**（需开启 WAAPI，默认端口 8080）
- **Windows / macOS**

### 安装依赖

```bash
pip install waapi-client requests
# 可选：精准 token 计数
pip install tiktoken
# Qt（二选一）
pip install PySide6
# 或
pip install PySide2
```

### 配置 API Key

**方式一：配置文件**

在 `config/wwise_ai.ini` 中填写你的 AI 服务 API Key：

```ini
ollama_api_key:your_key_here
deepseek_api_key:your_key_here
glm_api_key:your_key_here
openai_api_key:your_key_here
duojie_api_key:your_key_here
wlai_api_key:your_key_here
```

**方式二：工具内设置**

点击右上角 `···` → API Key，在弹窗中输入。

### 启动 Wwise

确保 Wwise Authoring Tool 已打开项目，且 WAAPI 已启用（User Preferences → General → Enable WAAPI，默认 `ws://127.0.0.1:8080/waapi`）。

### 启动 Agent

```bash
python launcher.py
```

### 使用 MCP Server（可选）

Wwise Agent 同时提供标准 MCP Server，可被 Claude Desktop、Cursor 等外部 AI 客户端调用。

#### 配置 Claude Desktop

在 Claude Desktop 配置文件（`claude_desktop_config.json`）中添加：

```json
{
  "mcpServers": {
    "wwise": {
      "command": "python",
      "args": ["-m", "wwise_mcp.server"],
      "cwd": "你的项目路径/Wwise_Agent"
    }
  }
}
```

#### 配置 Cursor

在 Cursor 的 MCP 设置中添加相同配置。启动后，外部 AI 客户端即可使用全部 22 个 Wwise MCP 工具。

## 架构

### Agent 循环流程

```
┌───────────────────────────────────────────────────────┐
│  用户发送消息                                           │
│  ↓                                                     │
│  系统提示词 + 对话历史 + RAG 文档 + 长期记忆            │
│  ↓                                                     │
│  AI 模型（流式）→ 思考过程 + tool_calls                  │
│  ↓                                                     │
│  工具执行器（WwiseToolExecutor）分发每个工具调用：       │
│    - Wwise Skill → 后台线程 WAAPI 调用                  │
│    - 联网 / 文档 → 后台线程（非阻塞）                   │
│  ↓                                                     │
│  工具结果 → 以 tool 消息反馈给 AI                        │
│  ↓                                                     │
│  AI 继续（可能调用更多工具或生成最终回复）                │
│  ↓                                                     │
│  循环直到 AI 完成或达到最大迭代次数                      │
└───────────────────────────────────────────────────────┘
```

### Mixin 架构

`AITab` 是核心组件，由五个聚焦的 Mixin 组合而成：

| Mixin | 模块 | 职责 |
|-------|------|------|
| `HeaderMixin` | `ui/header.py` | 顶部设置栏 — 提供商/模型选择器、Web/Think 开关、Key 状态 |
| `InputAreaMixin` | `ui/input_area.py` | 输入区域、发送/停止按钮、模式切换（Agent/Ask/Plan）、确认模式 |
| `ChatViewMixin` | `ui/chat_view.py` | 对话显示、消息插入、滚动控制、Toast 通知 |
| `AgentRunnerMixin` | `core/agent_runner.py` | Agent 循环辅助、自动标题生成、确认模式拦截、工具分类 |
| `SessionManagerMixin` | `core/session_manager.py` | 多会话创建/切换/关闭、会话标签栏、状态保存/恢复 |

### Plan 模式

Plan 模式使 AI 能够通过结构化的三阶段工作流处理复杂任务：

1. **深度调研** — 使用只读查询工具调查当前 Wwise 项目
2. **需求澄清** — 发现歧义时通过 `ask_question` 与用户交互确认
3. **结构化规划** — 生成工程级执行计划，包含阶段划分、步骤、依赖关系、风险评估

计划以交互式 `PlanViewer` 卡片显示，附带 DAG 流程图。用户可以查看每个步骤的详情、批准/拒绝计划，并监控执行进度。计划数据持久化到 `cache/plans/plan_{session_id}.json`。

### 大脑启发式长期记忆系统

五个模块组成的系统，使 Agent 能够持续学习和改进：

| 模块 | 说明 |
|------|------|
| `memory_store.py` | 三层 SQLite 存储 — **事件记忆**（具体任务经历）、**抽象知识**（反思生成的经验规则）、**策略记忆**（解决问题的套路，带优先级） |
| `embedding.py` | 本地文本向量化，使用 `sentence-transformers/all-MiniLM-L6-v2`（384维），回退方案为字符 n-gram + numpy 余弦相似度 |
| `reward_engine.py` | 类多巴胺奖励评分 — 成功度（0.4）、效率（0.25）、新颖度（0.15）、错误惩罚（0.2）；驱动记忆重要度的强化/衰减 |
| `reflection.py` | 混合反思 — 每次任务后零成本规则提取 + 每 5 个任务 LLM 深度反思生成抽象规则和策略更新 |
| `growth_tracker.py` | 滚动窗口指标（错误率、成功率趋势）+ 个性特征形成（效率偏好、风险容忍度、回复详细度、主动性） |

查询时自动激活记忆：通过余弦相似度检索相关的事件记忆、抽象规则和策略记忆，压缩注入到系统提示词中（最多 500 字符）。

### WAAPI 连接

- **WebSocket 通信** — 基于官方 `waapi-client` 库，连接 `ws://127.0.0.1:8080/waapi`
- **全局连接池** — 单例模式复用连接，避免频繁握手
- **安全黑名单** — `execute_waapi` 兜底工具受黑名单保护（project.open/close/save、remote.connect/disconnect）
- **Undo Group** — 批量操作工具自动包裹 `beginGroup/endGroup`，支持一键撤销
- **异常体系** — 6 种分类异常（ConnectionError、APIError、NotFound、InvalidProperty、Forbidden、Timeout），每种附带建议

### 上下文管理

- **原生工具消息链**：`assistant(tool_calls)` → `tool(result)` 消息直接传递给模型
- **严格的 user/assistant 交替**：确保跨提供商的 API 兼容性
- **按轮次裁剪**：对话按用户消息分割为轮次；超出 Token 预算时，先压缩旧轮次的工具结果，再整轮删除
- **永不截断 user/assistant**：仅压缩或移除 `tool` 结果内容
- **自动 RAG 注入**：根据用户查询自动检索相关的 WAAPI 函数签名和对象类型文档

### Token 计数与费用估算

- **tiktoken 集成** — 可用时使用 tiktoken 精准计数，否则使用启发式估算
- **多模态 Token 估算** — 图片按约 765 Token 估算
- **按模型计费** — 根据各提供商定价估算费用
- **推理 Token 追踪** — 单独统计推理/思考 Token
- **Token 分析面板** — 每次请求的详细分解：输入、输出、推理、缓存、延迟和费用

### 本地文档索引

`doc_rag.py` 模块提供轻量级 dict 索引：

- **WAAPI 函数索引** — URI → 签名 + 描述
- **Wwise 对象类型索引** — 类型 → 属性 + 描述
- **知识库分段检索** — `Doc/*.txt` 知识库文章

相关文档会根据用户的查询自动注入到系统提示词中。

## 使用示例

**查询项目结构：**
```
用户：帮我看看项目里有什么
Agent：[get_project_hierarchy]
项目包含 Actor-Mixer Hierarchy（15 个对象）、Events（8 个）、Master-Mixer Hierarchy（3 条 Bus）...
```

**创建完整音效系统：**
```
用户：创建一个脚步声系统：RandomContainer 下放 3 个 Sound，再创建播放 Event。
Agent：[add_todo: 规划 3 个步骤]
       [batch_create: tree 模式创建 RandomContainer + 3 个子 Sound]
       [create_event: Play_Footsteps → RandomContainer]
       [verify_event_completeness: 验证完整性]
完成。创建了 Footsteps（RandomSequenceContainer）+ 3 个子 Sound + Play_Footsteps Event。
```

**批量属性设置：**
```
用户：把项目里所有 Sound 的 Streaming 都打开。
Agent：[batch_set_property: type_filter="Sound", properties={"IsStreamingEnabled": true}]
已为 23 个 Sound 对象开启 Streaming，可通过 Ctrl+Z 一键撤销。
```

**联网搜索文档：**
```
用户：Wwise 2024 的 Blend Container 有什么新 API？
Agent：[web_search: "Wwise 2024 Blend Container WAAPI new API"]
       [fetch_webpage: https://www.audiokinetic.com/...]
根据官方文档，Wwise 2024.1 新增了 Blend Track 管理 API...
```

**Plan 模式重组项目：**
```
用户：帮我重组整个项目的 Bus 结构。
Agent：[Plan 模式]
       [get_bus_topology: 调研当前结构]
       [get_project_hierarchy: 了解对象分布]
       [create_plan: 生成 3 阶段重组计划]
       → 展示 PlanViewer 卡片，等待用户确认
用户：确认执行
Agent：[按计划逐步执行 Bus 创建、路由调整、验证]
```

## 常见问题

### WAAPI 连接问题
- 确认 Wwise Authoring Tool 已打开并加载了项目
- 确认 WAAPI 已启用：User Preferences → General → Enable Wwise Authoring API
- 默认端口 8080，如有冲突请修改 `_waapi_helpers.py` 中的 `WAAPI_URL`

### Agent 不调用工具
- 确认所选提供商支持 Function Calling
- DeepSeek、GLM-4.7、OpenAI、Duojie（Claude）均支持工具调用
- Ollama 需要支持工具调用的模型（如 `qwen2.5`），不支持时自动降级为 JSON Mode

### 批量操作失败
- 确认目标路径存在（先用 `search_objects` 或 `get_project_hierarchy` 查询）
- `batch_delete` 默认检查引用，如需强制删除传 `force=true`
- 所有批量操作支持 Undo Group，可在 Wwise 中 Ctrl+Z 一键撤销

### UI 卡顿
- Wwise 工具在后台线程运行，不应阻塞 UI
- 如遇卡顿，请检查 WAAPI 连接是否正常

### 更新
- 点击溢出菜单中的 **Update** 按钮检查新版本
- 启动时静默检查 GitHub Releases，有新版本时高亮 Update 按钮
- 更新时保留 `config/`、`cache/`、`trainData/` 目录

## 作者

tsuyu
KazamaSuichiku(翠竹,meshy,指导老师)

## 许可证

MIT
