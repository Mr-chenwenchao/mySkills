# Phoenix 看门狗 Cronjob

Phoenix L1 服务器（端口 11999）通过 Hermes cronjob 系统实现自动保活，每 5 分钟检查一次。

## 从 Hermes 创建

```bash
hermes cron create every 5m
# 提示输入 prompt，填入：
# Check if phoenix-l1-server is running on port 11999. If not, start it with:
#   python3 ~/.hermes/skills/routing/phoenix-architecture/scripts/phoenix-l1-server.py
# Use curl -s --noproxy '*' http://127.0.0.1:11999/chat -d '{"message":"ping"}'
# to test connectivity. If curl times out or returns error, restart the server.
# Delivery: local (execute on this machine)
```

## 手动保活命令

```bash
# 检查端口
lsof -i :11999 2>/dev/null || ss -tlnp | grep 11999

# 重启
python3 ~/.hermes/skills/routing/phoenix-architecture/scripts/phoenix-l1-server.py qwen2.5:7b 11999 &

# 测试
curl -s --noproxy '*' --max-time 5 -X POST http://127.0.0.1:11999/chat -d '{"message":"ping"}'
```

## 已知坑

1. **代理拦截：** 所有 localhost curl 必须加 `--noproxy '*'`，否则 http_proxy 环境变量会把请求路由到 7897 代理导致超时。
2. **端口冲突：** 如果进程 crash 但端口未释放，lsof 能检测到但 curl 会失败。看门狗应 kill 旧进程再启动新进程。
3. **Ollama 必须运行：** L1 服务器依赖 localhost:11434 上的 Ollama 服务。如果 Ollama 挂了，看门狗重启 L1 也没用。
