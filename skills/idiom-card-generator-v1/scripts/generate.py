#!/usr/bin/env python3
"""
小红书国风双语成语卡片生成器 V1 — 传统国风水墨宣纸版
"""
from google import genai
import os, sys

# ============================================================
# ★ 配置区 ★
# ============================================================
IDIOM = "胸有成竹"
PINYIN = "xiōng yǒu chéng zhú"
MEANING = "比喻在做事之前已经拿定主意，心中已有完整的筹划和把握。形容做事有充分的准备和信心。"
EXAMPLE_CN = "他准备了整整一个月，上台答辩时胸有成竹，对每个问题都对答如流。"
EXAMPLE_EN = "He had prepared for a full month. When presenting his defense, he was completely confident and answered every question flawlessly."
ILLUSTRATION = "一位古代文人画家坐在书案前，案上铺开一张空白宣纸。他面前放着一盆挺拔的翠竹，但他并不看竹子，而是闭目凝神，胸中早已有了完整的竹子形象。"
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
OUT = "/tmp/xhs_cards_v1"
os.makedirs(OUT, exist_ok=True)

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


# ======== Card 1: Cover ========
print("📸 V1 Card 1: 封面")
print("=" * 45)

prompt_1 = f"""{VISUAL_BASE}

# Image 1 (Cover): Idiom + Illustration — NO EXPLANATION TEXT
[LAYOUT]: 9:16 vertical composition on aged Xuan paper. The paper must show visible fiber texture, subtle tea-stained uneven coloring, and raw deckle edges.
[CONTENT]:
  - At the very top in elegant large calligraphy: "{IDIOM}" (semi-cursive script), dark ink black.
  - Just below in smaller elegant brush stroke style: "{PINYIN}" in gray ink.
  - Below that, in fine delicate English calligraphy style: "Having a Well-Thought-Out Plan — Chinese Idiom" in subtle gray.
  - A vermilion red seal stamp (朱砂印章) stamped next to the idiom.
  - CENTER: A beautiful traditional Chinese painting illustration depicting: {ILLUSTRATION}
  - At the very bottom: a small vermilion seal stamp with "Bilingual Chinese Idiom · 每日成语" in brush script.
[NO ADDITIONAL TEXT]: Just the idiom, pinyin, English title, the painting, and decorative seals."""

resp_1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt_1,
    config={"response_modalities": ["Text", "Image"]}
)
img1 = save_image(resp_1, "01_cover.jpg")


# ======== Card 2: Meaning ========
print("\n📸 V1 Card 2: 释义")
print("=" * 45)

prompt_2 = f"""{VISUAL_BASE}

# Image 2: Idiom Explanation — BILINGUAL
[LAYOUT]: 9:16 vertical composition on aged Xuan paper. IDENTICAL paper texture, color, and feel as Card 1.
[CONTENT]:
  - [HEADER]: "{IDIOM}" in large calligraphy, with "{PINYIN}" in smaller script below.
  - [ENGLISH HEADER]: "Having a Well-Thought-Out Plan" in elegant English calligraphy below.
  - Below the header, a thin decorative hand-brushed ink divider line.
  - [CHINESE EXPLANATION]: "释义 / Meaning:" subtitle then "{MEANING}"
  - [ENGLISH EXPLANATION]: "To have a well-thought-out plan before taking action. To be fully prepared and confident."
  - [DECORATION]: A floating ink wash illustration element — bamboo leaves in traditional style.
  - At bottom right: a vermilion seal stamp.
[STYLE MATCHING]: The paper texture, calligraphy, ink quality, seal stamps, and color palette must be the exact same visual series as Card 1."""

if img1:
    u1 = client.files.upload(file=img1)
    resp_2 = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[u1, prompt_2],
        config={"response_modalities": ["Text", "Image"]}
    )
    img2 = save_image(resp_2, "02_meaning.jpg")
else:
    img2 = None


# ======== Card 3: Usage ========
print("\n📸 V1 Card 3: 举例")
print("=" * 45)

prompt_3 = f"""{VISUAL_BASE}

# Image 3: Usage Examples — BILINGUAL
[LAYOUT]: 9:16 vertical composition on aged Xuan paper. IDENTICAL paper texture, color, and feel as Cards 1 and 2.
[CONTENT]:
  - [HEADER]: "{IDIOM}" in large calligraphy. "{PINYIN}" in smaller script.
  - [SECTION TITLE]: "使用举例 / Usage Examples" in brush-style ink black.
  - [EXAMPLE 1]: "{EXAMPLE_CN}" in calligraphy-style text.
  - [EXAMPLE 1 EN]: "{EXAMPLE_EN}"
  - [EXAMPLE 2]: "他考前复习了三遍，走进考场时胸有成竹。" with "He reviewed three times and walked into the exam with complete confidence."
  - [DECORATION]: Small floating ink wash motifs — brush and ink stone.
  - [SEAL]: Vermilion seal stamp at bottom right.
[CRITICAL]: The paper texture, calligraphy, ink wash quality, and overall aesthetic must be the same visual series as Cards 1 and 2."""

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
    print("  ⏭️ Skip")

print(f"\n{'='*45}")
print(f"🎉 V1 全部生成完毕！输出: {OUT}/")
for f in sorted(os.listdir(OUT)):
    sz = os.path.getsize(os.path.join(OUT, f)) // 1024
    print(f"  {f}: {sz}KB")
