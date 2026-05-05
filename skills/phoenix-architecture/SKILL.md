---
name: phoenix-architecture
description: "不死鸟架构（Phoenix Architecture）— 三层模型路由：本地模型/DeepSeek/Claude Code"
version: 2.0.0
author: cwc
tags: [routing, model-selection, cost-optimization, phoenix, deepseek]
---

# 不死鸟架构（Phoenix Architecture）

大脑手脚分离 + 智能路由，实现轻量、稳定、低成本。由我（路由器）根据任务类型自动判断走哪层。

```
用户提问
  ↓ (自动路由)
  简单对话 ──→ [可选] 层1 → phoenix-l1-server（本地 Qwen2.5 7B，长驻 HTTP）
  复杂推理 ──→ 层2 → DeepSeek v4 Flash（主模型，默认兜底所有层）
  编码任务 ──→ 层3 → Claude Code + DeepSeek v4 Flash
```

---

## 层 1：简单对话 → 本地模型（Qwen2.5 7B，长驻进程）

> **当前状态：已关闭** — 本地模型占用 ~4.5GB VRAM，在 16GB 机器上资源紧张时不建议运行。
> 关闭后所有简单对话自动走层 2（DeepSeek v4 Flash）兜底。

**何时启用：** 问候、yes/no 确认、无需推理的事实查询、闲聊。

**启动方式：**
```bash
python3 ~/.hermes/scripts/phoenix-l1-server.py qwen2.5:7b 11999 &
# 然后创建 cronjob 看门狗（参考 references/watchdog-cronjob.md）
```

**调用方式：**
```bash
curl -s --noproxy '*' -X POST http://127.0.0.1:11999/chat -d '{"message":"你好"}'
# 返回: {"reply": "你好！(Qwen)"}
```

**性能：** ~0.6s vs delegate_task 的 ~19s（快了 30 倍），跳过子 agent 初始化开销直接调用 Ollama API。
**坑：** 必须加 `--noproxy '*'`，否则 http_proxy 会把 localhost 请求路由到代理导致超时。

---

## 层 2：复杂推理 → DeepSeek v4 Flash（主模型）

**默认路由层** — 所有不匹配层 1/层 3 的任务自动走这层。

**何时走：** 架构设计、方案分析、多步骤推理、技术调研、代码分析、对比研究。

**如何执行：** 直接用主模型的思考回复用户，无需额外操作。

**配置：**
```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
```

---

## 层 3：编码任务 → Claude Code + DeepSeek v4 Flash

**何时走：** 写代码、重构、修 bug、git 操作、PR review、测试编写。

**如何执行：**
```python
terminal(command="cd /project && claude -p '任务描述' --allowedTools 'Read,Edit,Write,Bash' --max-turns N", timeout=...)
```

注：Claude Code 已配置 `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`，实际走 DeepSeek v4 Flash。

---

## 层 1 上下文限制（重要坑）

Qwen2.5 7B 只有 32K 上下文，但 Hermes Agent 强制要求所有模型 ≥ 64K。delegate_task 到本地模型时会报错：

> Model qwen2.5:7b has a context window of 32,768 tokens, which is below the minimum 64,000 required by Hermes Agent.

**解决办法：** 在 config.yaml 以下位置添加 `context_length: 64000`：

```yaml
model:
  context_length: 64000           # 主模型层

delegation:
  context_length: 64000           # 子 agent 层

auxiliary:
  compression:
    context_length: 64000         # 压缩模型层
```

设为 64000 只是绕过硬性检查，模型实际仍用 32K（简单对话够用）。

---

## 成本对比

| 层 | 模型 | 成本 | 延迟 | 当前状态 |
|----|------|------|------|----------|
| 层 1 | Qwen2.5 7B (本地) | 免费 | ~0.6s | **默认禁用**（需手动启动） |
| 层 2 | DeepSeek v4 Flash | 极低（按量） | ~1-2s | **默认兜底**（层 1 关闭时所有对话走这层） |
| 层 3 | Claude Code + DeepSeek | 极低（按量） | 按任务 | 编码专用 |

> ⚠️ 层 1 关闭后，原本走层 1 的简单对话自动走层 2（DeepSeek v4 Flash），成本仍可忽略（单次对话 < $0.001）。

---

## 如何禁用/重新启用层 1

### 禁用层 1（释放本地模型内存）

```bash
# 1. 杀掉 L1 服务器（如果运行中）
kill $(lsof -t -i :11999) 2>/dev/null

# 2. 移除 cronjob 看门狗
hermes cron remove phoenix-l1 2>/dev/null || true

# 3. 清空 delegation 配置（使所有流量走主模型）
# 在 config.yaml 中将以下字段设为空字符串：
#   delegation.model: ''
#   delegation.provider: ''
#   delegation.base_url: ''
#   delegation.api_key: ''

# 4. 从 Ollama 内存卸载模型
curl -s http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","keep_alive":0}'
```

### 重新启用层 1

```bash
# 1. 启动 L1 服务器
python3 ~/.hermes/scripts/phoenix-l1-server.py qwen2.5:7b 11999 &

# 2. 测试连通性
curl -s --noproxy '*' --max-time 5 -X POST http://127.0.0.1:11999/chat -d '{"message":"ping"}'

# 3. 恢复 cronjob 看门狗（可选）
# 参考 references/watchdog-cronjob.md

# 4. 恢复 config.yaml delegation 配置为 ollama + qwen2.5:7b
# 详见 references/delegation-clear.md
```

---

## Skill 内嵌资源

- `scripts/phoenix-l1-server.py` — 层 1 长驻 HTTP 服务器代码
- `references/watchdog-cronjob.md` — 看门狗 cronjob 配置说明
- `references/delegation-clear.md` — delegation 禁用模式（空字符串清空法）
