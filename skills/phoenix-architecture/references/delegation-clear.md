# Delegation 禁用模式：空字符串清空法

当需要临时关闭 delegation（子 agent 不派发到本地/特定模型）时，
最干净的方式是把 delegation 字段设为空字符串，而不是删除配置段。

## 为什么用空字符串而不是删除配置段

- 保留完整的 YAML 结构，重新启用时只需恢复字段值
- 不会触发 Hermes 配置文件加载器的格式校验问题
- 改 4 个字段即可，无需改动 YAML 层级结构

## 配置示例

```yaml
delegation:
  model: ''
  provider: ''
  base_url: ''
  api_key: ''
  context_length: 64000     # 保留，不影响
```

## 恢复启用

```yaml
delegation:
  model: qwen2.5:7b
  provider: ollama
  base_url: http://127.0.0.1:11434
  api_key: ''
  context_length: 64000
```

## 验证配置

```bash
# 查看当前 delegation 配置
grep -A5 "^delegation:" ~/.hermes/config.yaml

# 确认子 agent 走的模型
# 正常对话即可，如果 delegation 为空，子 agent 会继承主模型
```

## 完整禁用步骤

参见 SKILL.md 的"如何禁用/重新启用层 1"章节。
