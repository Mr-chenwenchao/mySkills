---
name: idiom-card-generator-v1
description: "小红书国风双语成语卡片生成器 — 接受任意成语，自动生成3张9:16国风水墨宣纸风格卡片（封面+释义+举例），中英双语，系列风格统一"
version: 1.0.0
author: cwc
tags: [xiaohongshu, image-generation, gemini, bilingual, content-creation]
---

# 成语卡片生成器 V1（小红书国风系列）

基于 Gemini 3.1 Flash Image 的图生图能力，自动生成国风宣纸水墨风格的三联成语卡片，适配小红书 9:16 竖屏发布。

## 效果预览

生成 3 张 9:16 卡片：
- **Card 1（封面）** — 成语书法 + 国风卡通插图 + 印章装饰，无解释文字
- **Card 2（释义）** — 中英双语释义 + 书法排版
- **Card 3（举例）** — 中英双语例句 + 使用场景

视觉风格：宣纸纹理、水墨技法、工笔+写意、朱砂印章、书法字体。

## 前置条件

### 环境

- Python 3.9+
- `google-genai` 包：`pip3 install google-genai`
- Gemini API Key（配置 `GOOGLE_API_KEY` 在 `~/.hermes/.env`）

### 模型

使用 `gemini-3.1-flash-image-preview`，支持图文输入 + 图片输出。

## 使用方法

### 方式一：直接调用脚本

```bash
# 先修改脚本顶部的成语变量，然后运行
python3 ~/.hermes/skills/xiaohongshu/idiom-card-generator-v1/scripts/generate.py
```

生成的图片在 `/tmp/xhs_cards_v6/`。

### 方式二：在对话中触发

告诉我一个成语，我自动执行生成全流程。

## 核心原理

### 图生图保持风格一致

关键技巧：三张图不是独立生成，而是**前一张图作为"视觉上下文"传给下一张**。

```
Card 1 ── 纯文本 prompt 生成
     ↓ (图片传给 Card 2 作为视觉参考)
Card 2 ── 文本 prompt + Card 1 图片
     ↓ (两张图片传给 Card 3)
Card 3 ── 文本 prompt + Card 1 + Card 2 图片
```

### 提示词结构

每张图的 prompt 由两部分组成：

1. **视觉基座（VISUAL_BASE，三张完全相同）** — 定义宣纸纹理、水墨技法、配色、字体
2. **每张定制（仅布局和内容不同）** — 封面/释义/举例各自的文本和插图

这种结构确保三张图的纸纹、墨色、印章风格完全一致，系列感强烈。

### 可替换变量

每张图只需修改脚本顶部的以下变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `IDIOM` | 成语 | 画龙点睛 |
| `PINYIN` | 拼音 | huà lóng diǎn jīng |
| `MEANING` | 中文释义 | 比喻在关键的地方... |
| `EXAMPLE_CN` | 中文例句 | 他的这篇文章... |
| `EXAMPLE_EN` | 英文例句 | His article was... |
| `ILLUSTRATION` | 插图场景描述 | 一个画家在一幅龙的画作上... |

### 发布到小红书

生成后在对话中告知 agent，通过 xiaohongshu-mcp 的 `publish_content` 工具自动发布。

## 内嵌资源

- `scripts/generate.py` — 完整生成脚本，修改顶部配置区的成语变量即可切换内容
