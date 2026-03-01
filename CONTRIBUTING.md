# Contributing

## 开发环境
1. 安装 Python 3.11+。
2. 安装依赖：
```bash
pip install -e .[dev]
```

## 本地开发命令
1. 启动 control-plane：
```bash
./scripts/run_control_plane.sh
```
2. 运行 Mac agent：
```bash
CONTROL_PLANE_URL=http://127.0.0.1:8000 AGENT_NAME=mbp-work ./scripts/run_agent_mac.sh
```
3. 运行 Ubuntu agent：
```bash
CONTROL_PLANE_URL=http://127.0.0.1:8000 AGENT_NAME=ubuntu-dev-1 ./scripts/run_agent_ubuntu.sh
```

## 质量与测试
1. 代码检查：
```bash
ruff check .
```
2. 类型检查：
```bash
mypy src
```
3. 测试：
```bash
pytest --cov=src --cov-report=term --cov-fail-under=80
```

## 提交流程
1. 新分支开发并提交。
2. 提交 PR 到 `main`。
3. CI 全绿后合并。

## 版本发布流程
1. 更新版本信息和变更说明。
2. 创建语义化版本 tag（例如 `v0.1.0`）：
```bash
git tag v0.1.0
git push origin v0.1.0
```
3. `release.yml` 自动执行质量检查、构建发布资产并创建 GitHub Release。
