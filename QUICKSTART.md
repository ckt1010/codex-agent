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

## 9. 最小验收清单
1. 三角色安装命令都可执行
2. 可向指定设备成功下发任务
3. 飞书/iMessage 至少一条通道可收发
4. `RunEvent` 三阶段可观测
5. Notion 有索引、OSS 有内容且可回溯

---
进一步细节见 [README.md](/Users/ckt1010/project/codex-agent/README.md)。
