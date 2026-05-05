---
name: idiom-card-generator-v2
description: "小红书国风双语成语卡片生成器 V2 — 8K极致真实宣纸质感 + 品牌印章「若瑜的成语笔记」"
version: 2.1.0
author: cwc
tags: [xiaohongshu, image-generation, gemini, bilingual, xuan-paper, brand-seal]
---

# 成语卡片生成器 V2（极致宣纸版 + 品牌印章）

## 核心特性

- **8K 真实宣纸纹理** — 可见纸纤维、茶渍老色、毛边质感
- **侧光立体感** — 自然侧光突出纸面三维纹理
- **墨水渗入纤维** — 笔触边缘自然晕染
- **中英双语** — 每张卡均含中英文
- **品牌印章** — 三张卡片统一显示「若瑜的成语笔记」朱砂印章

## 生成流程（图生图保持风格一致）

```
Card 1（封面）—— 成语书法 + 国风插图 + 印章（无解释）
     │ 图片传给 Card 2 作为视觉上下文
Card 2（释义）—— 中英双语解释 + 延续纸纹风格 + 印章
     │ 两张图一起传给 Card 3
Card 3（举例）—— 中英双语句子 + 完全一致的宣纸质感 + 印章
```

## 使用方法

### 修改成语内容

编辑脚本顶部的配置区：

```bash
nano ~/.hermes/skills/xiaohongshu/idiom-card-generator-v2/scripts/generate.py
```

需要修改 6 个变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `IDIOM` | 成语 | 对牛弹琴 |
| `PINYIN` | 拼音 | duì niú tán qín |
| `MEANING` | 中文释义 | 比喻说话不看对象... |
| `EXAMPLE_CN` | 中文例句 | 他跟我大谈交响乐... |
| `EXAMPLE_EN` | 英文例句 | He was talking about... |
| `ILLUSTRATION` | 插图场景描述 | 琴师在草地上弹琴... |

### 品牌印章

印章文字在 `SEAL_TEXT` 变量中设置，默认是「若瑜的成语笔记」。三张卡片右下角自动显示。

### 运行

```bash
python3 ~/.hermes/skills/xiaohongshu/idiom-card-generator-v2/scripts/generate.py
```

输出目录：`/tmp/xhs_cards_v2/`

### 发布到小红书

通过 xiaohongshu-mcp 的 `publish_content` 工具自动发布。

## 内嵌资源

- `scripts/generate.py` — V2 完整生成脚本（含品牌印章配置）
