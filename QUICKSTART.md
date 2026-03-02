# Quickstart: 一键部署多端 Codex Bridge

本指南目标：在 30-60 分钟内跑通最小可用链路。

## 0. 你将得到什么
1. 可以随时随地控制你的 codex
2. 你多台电脑的 codex 记忆可以共享

## 1. 前置条件
1. 至少 1 台 Mac（安装 Codex App）和 1 台 Ubuntu（可运行 Docker）
2. 准备一台“控制面主机（control-plane host）”，用于长期运行 `control-plane`：
- 生产环境：推荐 ECS/云主机（7x24 在线、固定公网地址）。
- 开发/测试：可用任意一台常在线电脑（Mac/Linux）临时运行。
- 不建议：经常休眠/关机的个人笔记本（会导致 agent 断连、消息中断）。
3. 已准备以下接入信息：
- 飞书机器人配置（应用凭据、事件订阅）
- iMessage 通道（BlueBubbles）
- Notion 工作区（用于索引，建议独立 Teamspace：`Codex Memory`）
- OSS Bucket（用于原文/证据片段）
4. 每台机器可访问 `control-plane`

Notion 隔离最小配置：
1. 在 Notion 新建 Teamspace：`Codex Memory`
2. 新建数据库：
- `Memory Index`（机器写）
- `Human Docs`（人工写）
3. 给 bot 账号最小权限：仅可写 `Codex Memory`，不可写个人空间
4. 机器写入统一标签：`source=agent`、`visibility=system`、`owner=codex-bot`

## 2. 启动 control-plane
在“控制面主机”执行：

```bash
./install.sh --role control-plane
```

预期结果：
1. 初始化数据库完成
2. API/worker/connectors 启动
3. 能生成一次性 `bootstrap_code`

控制面主机选型建议：
1. 你要长期稳定使用：选 ECS/云主机（推荐）。
2. 你只是本地联调：任意常在线电脑即可。
3. 若使用内网电脑，需确保所有 agent 与消息 connector 能访问该主机地址。

## 本地最小运行命令
以下命令用于本地快速跑通（单机模拟）：

```bash
pip install -e .[dev]
```

终端 A（control-plane）：
```bash
./scripts/run_control_plane.sh
```

终端 B（注册并运行一个 Ubuntu agent）：
```bash
bootstrap_code=$(curl -sS -X POST http://127.0.0.1:8000/api/bootstrap/new | python -c 'import sys,json; print(json.load(sys.stdin)["bootstrap_code"])')
./scripts/install.sh --role agent-ubuntu --agent-name ubuntu-dev-1 --bootstrap-code "$bootstrap_code"
source .runtime/ubuntu-dev-1.env
./scripts/run_agent_ubuntu.sh
```

终端 C（模拟飞书下发）：
```bash
curl -sS -X POST http://127.0.0.1:8000/api/tasks/ingest \
  -H 'content-type: application/json' \
  -d '{"task_id":"quickstart-task-1","source":"feishu","source_message_id":"quickstart-msg-1","requester_id":"u1","target_agent":"ubuntu-dev-1","project_alias":"demo","instruction":"run quickstart","priority":1,"created_at":"2026-03-01T00:00:00+00:00"}'
```

## 3. 注册 Mac agent
在 Mac 上执行（示例）：

```bash
./install.sh --role agent-mac --agent-name mbp-work --bootstrap-code xxx
```

预期结果：
1. Agent 成功注册到 control-plane
2. 创建常驻服务
3. 上报心跳为在线

## 4. 注册 Ubuntu agent（容器）
在 Ubuntu 上执行（示例）：

```bash
./install.sh --role agent-ubuntu --agent-name ubuntu-dev-1 --bootstrap-code xxx
```

容器运行时确保挂载：
1. `/workspace`
2. `/var/lib/codex-agent`
3. `/root/.codex`（或等效凭据路径）

预期结果：
1. `codex-agent-runner` 容器启动
2. Agent 成功注册并持续上报心跳

## 5. 下发第一条任务（必须指定设备）
入站命令格式：

```text
@codex @agent:<name> @proj:<alias> <task>
```

示例：

```text
@codex @agent:ubuntu-dev-1 @proj:backend 修复支付重试
```

注意：
1. 不支持 `@agent:auto`
2. 未指定 `@agent` 或设备离线会直接失败
3. 复用会话时可指定：`@session:<session_id>`

查看 session 列表：
```text
list
```
系统会返回 Markdown 表格，按设备展示 session 与最后输出。

按 session 继续控制示例：
```text
@codex @agent:mbp-work @session:sess-123 @proj:backend 继续处理上次失败用例
```

## 6. 验证运行里程碑
一次成功任务应看到：
1. `started`
2. （可选）`tool_error` + 重试
3. `completed`

并满足去重规则：
1. 同一 `source + source_message_id` 只执行一次

## 7. 验证共享记忆（Notion 索引 + OSS 内容）
验证写入：
1. Notion 中出现 `MemoryRecord` 索引（含 `source_doc_id`、`summary`、`citations`、`status`）
2. OSS 中存在对应 `oss_uri` 对象（原文或证据片段）
3. 新记录应写入 `Codex Memory` Teamspace，不出现在个人文档默认视图

验证读取：
1. agent 先查 Notion 索引，仅取 `status=fresh`
2. 再按 `oss_uri` 拉取内容
3. 按 citation 回跳到页码/片段

## 8. 常见故障排查
1. 任务拒绝执行
- 检查是否缺少 `@agent:<name>` 或目标设备离线

2. Mac 无法抽取本地会话
- 检查 `~/.codex/state_5.sqlite` 与 `~/.codex/sessions/*.jsonl` 可读

3. Ubuntu 容器执行失败
- 检查 Docker 状态与 `/root/.codex` 挂载

4. 记忆无法复用
- 检查索引是否 `stale/superseded`
- 检查 `source_version` 是否变化并触发重抽取

## 9. 这台 MacBook 接 iMessage（BlueBubbles）
目标：让 iMessage 指令直接进入本项目 `control-plane`。

1. 启动 control-plane（若未启动）
```bash
./scripts/run_control_plane.sh
```

2. 在同一台 MacBook 启动 iMessage connector
```bash
CONTROL_PLANE_URL=http://127.0.0.1:8000 \
IMESSAGE_ALLOWED_SENDERS=\"+8613800000000\" \
IMESSAGE_STATUS_RECIPIENT=\"+8613800000000\" \
./scripts/run_imessage_connector.sh
```

3. 在 BlueBubbles 服务端把 webhook 指向：
```text
http://<这台MacBookIP>:8090/webhooks/bluebubbles
```

4. 从 iMessage 发送命令（必须显式设备名）
```text
@codex @agent:mbp-work @proj:backend 修复支付重试
```

5. 预期
- connector 返回 `accepted`
- `control-plane` 中出现对应任务
- 指定 agent 拉取并执行
- 若配置 `IMESSAGE_OUTBOUND_PUSH_URL`，`list` 与任务受理会主动回推到 iMessage 通道

## 10. 这台 MacBook 接飞书（Webhook）
目标：让飞书消息和 iMessage 一样支持 `list` / `@session`。

1. 启动 Feishu connector
```bash
CONTROL_PLANE_URL=http://127.0.0.1:8000 \
FEISHU_ALLOWED_USERS="ou_xxx,ou_yyy" \
FEISHU_STATUS_RECIPIENT="ou_xxx" \
./scripts/run_feishu_connector.sh
```

2. 在飞书事件订阅配置 webhook：
```text
http://<这台MacBookIP>:8091/webhooks/feishu
```

3. 在飞书里发送：
```text
list
```
或
```text
@codex @agent:mbp-work @session:sess-123 @proj:backend 继续处理
```

4. 预期
- 返回 Markdown session 列表或任务受理信息
- 指令写入 control-plane 并由指定 agent 执行
- 若配置 `FEISHU_OUTBOUND_PUSH_URL`，`list` 与任务受理会主动回推到飞书通道

## 11. 任务结果主动回推（control-plane 扇出）
在 control-plane 环境增加：
```bash
export CODEX_BRIDGE_FEISHU_PUSH_URL=http://<host>:<port>/push/feishu
export CODEX_BRIDGE_IMESSAGE_PUSH_URL=http://<host>:<port>/push/imessage
```
效果：
1. `POST /api/events/run` 的 `started|tool_error|completed` 事件会自动回推到原任务来源通道。
2. 回推消息为 Markdown，包含 task_id、agent、session、event_type、summary。
3. control-plane 启动成功会自动回推一条 `System Status`。
4. connector 启动成功会回推 `started`；若连不上 control-plane，会回推 `control_plane_unreachable`。

## 12. 最小验收清单
1. 三角色安装命令都可执行
2. 可向指定设备成功下发任务
3. 飞书/iMessage 至少一条通道可收发
4. `RunEvent` 三阶段可观测
5. Notion 有索引、OSS 有内容且可回溯

---
进一步细节见 [README.md](/Users/ckt1010/project/codex-agent/README.md)。
