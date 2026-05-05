#!/usr/bin/env python3
"""
小红书国风双语成语卡片生成器 V1
接受任意成语，生成 3 张 9:16 国风水墨宣纸风格卡片（封面+释义+举例）
包含中英双语，系列风格统一

使用方法：
  1. 修改下方 CONFIG 区的成语变量
  2. python3 generate.py
  3. 图片输出到 /tmp/xhs_cards/
"""
from google import genai
import os, sys

# ============================================================
# ★ 配置区 — 修改这里切换成语内容 ★
# ============================================================
IDIOM = "画龙点睛"          # 成语
PINYIN = "huà lóng diǎn jīng"  # 拼音
MEANING = "比喻在关键的地方用精辟的语句点明要旨，使内容更加生动传神。也比喻在整体中加上关键的细节，使之更加完美。"
EXAMPLE_CN = "他的这篇文章本来很一般，但他最后那段话真是画龙点睛，让整个作品立刻有了灵气。"
EXAMPLE_EN = "His article was ordinary, but his concluding words were the perfect finishing touch that brought the entire piece to life."
ILLUSTRATION = "一个画家在一幅龙的画作上，用笔点在龙的眼睛上，龙立刻变得栩栩如生、灵气动人。画家身穿古代中式服装，周围有墨色气流晕染。"
# ============================================================

KEY = os.environ.get("GOOGLE_API_KEY", "")
if not KEY:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("GOOGLE_API_KEY="):
                    KEY = line.strip().split("=", 1)[1]
                    break
if not KEY:
    print("❌ 需要设置 GOOGLE_API_KEY")
    sys.exit(1)

client = genai.Client(api_key=KEY, http_options={"api_version": "v1beta"})
OUT = "/tmp/xhs_cards"
os.makedirs(OUT, exist_ok=True)

# ======== 视觉基座（三张图完全一致）========
VISUAL_BASE = """# Visual Style and Material Base
[STYLE]: Traditional Chinese ink wash painting, authentic Xuan paper (宣纸) texture, genuine handmade rice paper feel.
[MATERIAL]: Real traditional Chinese Xuan paper, visible long plant fibers texture, raw hand-torn edges, aged tea-stained ivory color, subtle paper grain, slight water stain marks, authentic antique paper appearance.
[PAINTING STYLE]: Traditional Chinese Gongbi (工笔) fine brushwork combined with Xieyi (写意) ink wash, soft watercolor bleeding effects, natural ink diffusion at brushstroke edges, subtle ink wash gradients.
[COLOR PALETTE]: Authentic antique Chinese painting colors — deep ink black, vermilion red (朱砂) seal stamps, indigo blue, malachite green, earthy ochre yellow, all on warm aged paper background.
[TYPOGRAPHY]: Traditional Chinese calligraphy, semi-cursive script (行书), elegant brush-stroke characters, vermilion red seal stamps (印章) as decorative elements.
[TEXTURE]: The paper MUST show visible natural fibers, subtle uneven coloring from age, slight stains, raw deckle edges, authentic handmade paper character.
[BORDER]: Natural deckle edge of handmade paper, subtle shadow indicating paper thickness on a clean background surface."""


def save_image(response, filename):
    if not response.candidates:
        print(f"  ❌ No candidates: {response.text[:150] if response.text else 'empty'}")
        return None
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            path = os.path.join(OUT, filename)
            with open(path, "wb") as f:
                f.write(part.inline_data.data)
            print(f"  ✅ {filename} ({len(part.inline_data.data)//1024}KB)")
            return path
    print(f"  ⚠️ No image: {response.text[:100] if response.text else ''}")
    return None


# ============================================================
# Card 1: 封面 — 成语 + 插图（无解释）
# ============================================================
print("📸 Card 1: 封面")
print("=" * 45)

prompt_1 = f"""{VISUAL_BASE}

# Image 1 (Cover): Idiom + Illustration — NO EXPLANATION TEXT

[LAYOUT]: 9:16 vertical composition on aged Xuan paper. The paper must show visible fiber texture, subtle tea-stained uneven coloring, and raw deckle edges.

[CONTENT]:
  - At the very top in elegant large calligraphy: "{IDIOM}" (semi-cursive script), dark ink black.
  - Just below in smaller elegant brush stroke style: "{PINYIN}" in gray ink.
  - Below that, in fine delicate English calligraphy style: "The Finishing Touch — Chinese Idiom" in subtle gray.
  - A vermilion red seal stamp (朱砂印章) stamped next to the idiom, with the characters "{IDIOM}" in ancient seal script.
  
  - CENTER of the card: A beautiful traditional Chinese painting illustration depicting: {ILLUSTRATION}
  
  - At the very bottom, extremely subtle: a small vermilion seal stamp and handwritten-style "Bilingual Chinese Idiom · 每日成语" in very small subtle brush script.

[NO ADDITIONAL TEXT]: This is the cover image. It should NOT contain any explanation, meaning, or usage text. Just the idiom, pinyin, English title, the painting illustration, and decorative seals."""

resp_1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt_1,
    config={"response_modalities": ["Text", "Image"]}
)
img1 = save_image(resp_1, "01_cover.jpg")


# ============================================================
# Card 2: 释义 — 双语解释
# ============================================================
print("\n📸 Card 2: 释义")
print("=" * 45)

prompt_2 = f"""{VISUAL_BASE}

# Image 2: Idiom Explanation — BILINGUAL

[LAYOUT]: 9:16 vertical composition on aged Xuan paper. IDENTICAL paper texture, color, and feel as Card 1.

[CONTENT]:
  - At top left: a small vermilion seal stamp.
  - [HEADER]: "{IDIOM}" in large calligraphy, with "{PINYIN}" in smaller script below.
  - [ENGLISH HEADER]: "The Finishing Touch" in elegant English calligraphy style below.
  - Below the header, a thin decorative line or divider suggesting hand-brushed ink line.
  - [CHINESE EXPLANATION]: A large brush-style subtitle "释义 / Meaning:" then: "{MEANING}"
  - [ENGLISH EXPLANATION]: Below: "To add the finishing touch that brings a work to life. The final, crucial detail that makes something perfect."
  - [DECORATION]: A small floating ink wash illustration element — a dragon tail or brush tip with ink drops in traditional style.
  - At bottom right: a vermilion seal stamp.

[STYLE MATCHING]: The paper texture, calligraphy style, ink wash quality, seal stamps, and color palette must create the exact same visual series as Card 1."""

if img1:
    u1 = client.files.upload(file=img1)
    resp_2 = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[u1, prompt_2],
        config={"response_modalities": ["Text", "Image"]}
    )
    img2 = save_image(resp_2, "02_meaning.jpg")
else:
    print("  ⏭️ Skip")
    img2 = None


# ============================================================
# Card 3: 举例 — 双语例句
# ============================================================
print("\n📸 Card 3: 举例")
print("=" * 45)

prompt_3 = f"""{VISUAL_BASE}

# Image 3: Usage Examples — BILINGUAL

[LAYOUT]: 9:16 vertical composition on aged Xuan paper. IDENTICAL paper texture, color, and feel as Cards 1 and 2.

[CONTENT]:
  - At top left: a small vermilion seal stamp.
  - [HEADER]: "{IDIOM}" in large calligraphy.
  - [PINYIN]: "{PINYIN}" in smaller script.
  - [SECTION TITLE]: Brush-style subtitle "使用举例 / Usage Examples" in ink black.
  - [EXAMPLE 1]: "{EXAMPLE_CN}" in clear calligraphy-style text.
  - [EXAMPLE 1 EN]: "{EXAMPLE_EN}"
  - [EXAMPLE 2]: "演讲结尾引经据典，画龙点睛。" with English "Using a classic quote to end a speech — the finishing touch."
  - [EXAMPLE 3]: "设计中一个巧妙的细节，起到画龙点睛的效果。" with English "A clever design detail that serves as the finishing touch."
  - [DECORATION]: Small floating ink wash motifs — brush, ink stone, or clouds.
  - [SEAL]: Vermilion seal stamp at bottom right.

[CRITICAL]: The paper texture, calligraphy style, ink wash quality, and overall aesthetic must be EXACTLY the same visual series as Cards 1 and 2."""

if img1 and img2:
    u1 = client.files.upload(file=img1)
    u2 = client.files.upload(file=img2)
    resp_3 = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[u1, u2, prompt_3],
        config={"response_modalities": ["Text", "Image"]}
    )
    save_image(resp_3, "03_usage.jpg")
else:
    print("  ⏭️ Skip - missing reference images")


print(f"\n{'='*45}")
print(f"🎉 全部生成完毕！")
for f in sorted(os.listdir(OUT)):
    sz = os.path.getsize(os.path.join(OUT, f)) // 1024
    print(f"  {f}: {sz}KB")
print(f"目录: {OUT}")
