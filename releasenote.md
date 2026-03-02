# Release Notes

## v0.1.1 (2026-03-02)

### Summary
新增“会话可见与会话控制”能力：飞书/iMessage 可发送 `list` 查看所有设备 session（Markdown 输出），并可用 `@session:<id>` 指定会话继续下发控制。

### Added
1. Session 查询接口
- `GET /api/sessions/list`
- `GET /api/sessions/markdown`

2. 命令桥接能力（统一协议）
- 新增 `connectors/command_bridge.py`
- 支持命令：
  - `list`
  - `@codex @agent:<name> @proj:<alias> <task>`
  - `@codex @agent:<name> @session:<session_id> @proj:<alias> <task>`

3. Connector 扩展
- iMessage BlueBubbles webhook 支持 `list` 与 `@session`。
- 新增 Feishu webhook bridge，支持 `list` 与 `@session`。
- `list` 与任务受理信息支持“主动回推”到对应通道（不只是 webhook 返回）。

4. 数据模型与存储
- `TaskEnvelope` 新增可选字段 `session_id`。
- `tasks` 表新增 `session_id`（兼容已有库自动迁移）。
- 新增 session 汇总查询与 Markdown 渲染。

5. Agent 行为
- 执行任务时若任务包含 `session_id`，事件上报复用该 thread/session。

6. 任务结果主动通知
- control-plane 新增通知扇出（Notification Fanout）。
- `started|tool_error|completed` 事件会根据任务 `source`（`feishu|imessage`）主动回推到配置通道。

### Test Results
本地执行结果：
1. `ruff check .` -> Passed
2. `mypy src` -> Passed
3. `pytest -q` -> Passed (`25 passed`)

## v0.1.0 (2026-03-01)

### Summary
本版本完成了 Codex Bridge V1 的可运行代码基线：
- Python + FastAPI 控制面
- Mac / Ubuntu agent runner
- 本地 mock connectors（Feishu / iMessage）
- 结构化记忆索引（SQLite）+ 本地 OSS 抽象
- 一键安装脚本与 GitHub Actions CI/Release 工作流

### Added
1. `common` 基础层
- 新增统一类型：`TaskEnvelope`、`AgentDescriptor`、`RunEvent`、`MemoryRecord`、`Citation`
- 新增统一时间工具（UTC + ISO8601）与配置加载

2. `control-plane` API 与服务闭环
- 新增任务入口：`POST /api/tasks/ingest`（显式 `target_agent`，幂等键 `source + source_message_id`）
- 新增 agent 生命周期接口：
  - `POST /api/agents/register`
  - `POST /api/agents/heartbeat`
  - `POST /api/agents/pull-task`
- 新增事件上报：`POST /api/events/run`
- 新增记忆接口：
  - `GET /api/memory/index`
  - `POST /api/memory/index`
  - `GET /api/memory/content`
- 新增 bootstrap 一次性注册码兑换 `agent_token` 流程
- 新增显式路由策略：未指定设备或离线设备直接拒绝

3. `memory-sync` V1 本地实现
- 新增 `MemoryIndexService` 规则：
  - 缺失 `oss_uri` 拒绝入库
  - 缺失 citation 拒绝复用
  - TTL 过期判定 `stale`
  - 版本变更判定 `superseded`
- 新增 `LocalOSSStore`：支持 `oss://` URI 与本地路径映射

4. Agents 与 connectors
- 新增 `agent_mac` runner（heartbeat + pull + completed 事件上报）
- 新增 `agent_ubuntu` runner（mock codex 执行 + 事件上报）
- 新增 `mock_feishu` / `mock_imessage` 入站 connector

5. DevOps 与可发布能力
- 新增 `pyproject.toml`（依赖、ruff/mypy/pytest 配置）
- 新增 `install.sh` 与 `scripts/` 运行脚本
- 新增 CI 工作流：`.github/workflows/ci.yml`
- 新增 release 工作流：`.github/workflows/release.yml`（tag `v*.*.*` 触发）
- 新增 `CONTRIBUTING.md`

6. 文档
- 更新 `README.md`：实现状态矩阵、部署图与实现入口
- 更新 `QUICKSTART.md`：本地最小运行命令
- 新增独立 Mermaid 文件：`architecture.mmd`

### Test Results
本地执行结果：
1. `ruff check .` -> Passed
2. `mypy src` -> Passed
3. `pytest --cov=src --cov-report=term --cov-fail-under=80` -> Passed
- `16 passed`
- Coverage `84.94%`（阈值 80%）

### Known Issues
1. 测试过程中存在 `sqlite3` `ResourceWarning: unclosed database` 警告，不影响当前功能但建议在后续版本补充连接生命周期管理（例如显式 close 或连接池策略）。
