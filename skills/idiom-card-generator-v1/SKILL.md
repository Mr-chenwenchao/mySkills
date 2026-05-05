---
name: idiom-card-generator-v1
description: "小红书国风双语成语卡片生成器 — 接受任意成语，自动生成3张9:16国风水墨宣纸风格卡片（封面+释义+举例），中英双语，系列风格统一"
version: 2.0.0
author: cwc
tags: [xiaohongshu, image-generation, gemini, bilingual, content-creation, xuan-paper]
---

# 成语卡片生成器 V1（传统国风版）

基于 Gemini 3.1 Flash Image 的**图生图**能力，自动生成传统国风宣纸水墨风格的三联成语卡片，适配小红书 9:16 竖屏发布。

视觉核心：**传统宣纸质感** — 植物纤维纹路、茶渍老色、工笔+写意水墨、半行书书法。

**V2 是当前首选版本**（8K 极致宣纸质感版），仅在需要传统水墨风格时使用 V1。

## 效果预览

生成 3 张 9:16 卡片，中英双语：

| 卡片 | 内容 | 特点 |
|------|------|------|
| **Card 1（封面）** | 双语成语标题 + 国风插画 + 印章装饰 | **无解释文字**，只有标题和画面 |
| **Card 2（释义）** | 双语成语 + 中英释义 | 标题"解释 / Explanation" |
| **Card 3（举例）** | 双语成语 + 中英例句 | 标题"使用举例 / Usage Example" |

## 前置条件

### 环境

- Python 3.9+
- `google-genai` 包（**注意：不是旧版 `google.generativeai`**）：`pip3 install google-genai`
- Gemini API Key（配置 `GOOGLE_API_KEY` 在 `~/.hermes/.env`）

### 模型

`gemini-3.1-flash-image-preview` — 支持图文输入 + 图片输出。

## 使用方法

### 方式一：直接调用脚本

```bash
# 1. 修改脚本顶部 CONFIG 区的成语变量
# 2. 运行
python3 ~/.hermes/skills/xiaohongshu/idiom-card-generator-v1/scripts/generate.py
# 3. 图片输出到 /tmp/xhs_cards/
```

### 方式二：在对话中触发

直接说「生成 XXX 的卡片」，Agent 自动执行全流程。

## 核心原理

### 图生图保持风格一致（关键技巧）

三张图不是独立生成，而是**前一张图作为"视觉上下文"传给下一张**：

```
Card 1 ── 纯文本 prompt 生成
     ↓ (client.files.upload → 传给 Card 2)
Card 2 ── 文本 prompt + Card 1 图片（Gemini 看到 Card 1 的风格）
     ↓ (两张图一起上传 → 传给 Card 3)
Card 3 ── 文本 prompt + Card 1 + Card 2 图片（保持系列一致性）
```

SDK 关键代码：
```python
from google import genai
client = genai.Client(api_key=KEY, http_options={"api_version": "v1beta"})

# Card 1 → 纯文本
resp_1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt_1,
    config={"response_modalities": ["Text", "Image"]}
)

# Card 2 → 上传 Card 1 的图片作为视觉参考
u1 = client.files.upload(file=img1)
resp_2 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[u1, prompt_2],  # 图片 + 文本
    config={"response_modalities": ["Text", "Image"]}
)

# Card 3 → 上传前两张
u1 = client.files.upload(file=img1)
u2 = client.files.upload(file=img2)
resp_3 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[u1, u2, prompt_3],
    config={"response_modalities": ["Text", "Image"]}
)
```

### 提示词结构

每张图的 prompt 由两部分组成：

1. **视觉基座（VISUAL_BASE，三张完全相同）** — 定义所有材质和风格参数
2. **每张定制（仅布局和内容不同）** — 封面/释义/举例各自的文本和插图

### 视觉基座（完整提示词模板）

详见 `references/prompts-v2.md`。核心要素：

```
[STYLE]: Traditional Chinese ink wash meets realistic photo of physical artifacts, 8K
[MATERIAL & TEXTURE]: Ultra-realistic antique Xuan paper — visible fibers, tea-stained ivory,
  raw feathered edges, no smooth rendering, pure physical texture
[PAINTING STYLE]: Delicate brushwork, Shuimo technique, ink bleeding on paper fibers
[TYPOGRAPHY]:
  - [CHINESE]: Hand-drawn brush calligraphy, not computer font
  - [ENGLISH]: Classic hand-drawn serif calligraphy
  - Both: textured ink that bleeds into paper fibers
[LIGHTING]: Soft directional side-lighting emphasizing 3D paper depth
```

### 可替换变量

脚本顶部 CONFIG 区：

| 变量 | 说明 | 示例 |
|------|------|------|
| `IDIOM` | 成语（中文） | 画龙点睛 |
| `PINYIN` | 拼音 | huà lóng diǎn jīng |
| `MEANING` | 中文释义 | 比喻在关键的地方... |
| `EXAMPLE_CN` | 中文例句 | 他的这篇文章... |
| `EXAMPLE_EN` | 英文例句 | His article was... |
| `ILLUSTRATION` | 插图场景描述（英文提示词风格） | 一位古代文人画家... |

## 已知陷阱

### 1. Gemini 图片免费额度为 0
图片生成不计入免费额度，必须绑定 billing。当前使用 Key `AIzaSyDQ8cT2Tfov-0vZ-V_IwNHOLx_fuSvXrjU` 已启用付费。

### 2. 不能用旧版 SDK
旧版 `google.generativeai`（gRPC 版）已被标记废弃，且在国内网络下走 gRPC 无法正确路由代理，**必须使用新版 `google-genai` SDK（HTTP 版）**。

### 3. 图片尺寸
Gemini 生成的图片约 896×1200（3:4 比例），接近 9:16 的 960×1280 标准，可直接使用。

### 4. 英文翻译适配
英文句子中的中文成语在生成时需要适配为英文意译（如 "the finishing touch" 对应 "画龙点睛"），而非直译。

## 发布到小红书

通过 xiaohongshu-mcp（localhost:18060/mcp）的 `publish_content` 工具发布。

## 内嵌资源

- `scripts/generate.py` — 完整生成脚本，修改顶部配置区的成语变量即可切换内容
- `references/prompts-v2.md` — 提示词2模板（极致宣纸质感版），包含完整的视觉基座和每张图布局模板
