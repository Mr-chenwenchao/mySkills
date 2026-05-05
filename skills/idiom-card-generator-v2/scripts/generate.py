#!/usr/bin/env python3
"""
小红书国风双语成语卡片生成器 V2 — 极致真实宣纸质感版
"""
from google import genai
import os, sys, argparse

# ============================================================
# ★ 配置区 — 可直接修改，也支持命令行覆盖 ★
# ============================================================
IDIOM = "对牛弹琴"
PINYIN = "duì niú tán qín"
ENGLISH_TITLE = "Playing Music to a Cow"
MEANING = "比喻说话不看对象，对不懂道理的人讲道理，对外行人说内行话。也用来讥笑说话的人不看对象。"
EXAMPLE_CN = "他跟我这个完全不懂音乐的人大谈交响乐，简直是对牛弹琴。"
EXAMPLE_EN = "He was talking about symphony orchestras to me, someone who knows nothing about music — it was like playing music to a cow."
ILLUSTRATION = "一位身穿古代长袍的琴师，坐在山间草地上，面前摆着一架古琴。他正在专注地弹奏，十指轻抚琴弦。而他对面坐着一头大黄牛，牛睁着大大的眼睛，呆萌地看着琴师，完全不明白发生了什么。周围是青山绿水的田园风光，有几片竹叶随风飘落。画面有趣又充满古风诗意。"
ENGLISH_MEANING = "To talk about something over someone's head. To cast pearls before swine. To address the wrong audience."
SEAL_TEXT = "若瑜的成语笔记"
# ============================================================

# 命令行参数覆盖配置
parser = argparse.ArgumentParser(description="生成小红书国风成语卡片")
parser.add_argument("--idiom", help="成语")
parser.add_argument("--pinyin", help="拼音")
parser.add_argument("--title-en", help="英文标题")
parser.add_argument("--meaning", help="中文释义")
parser.add_argument("--meaning-en", help="英文释义")
parser.add_argument("--example-cn", help="中文例句")
parser.add_argument("--example-en", help="英文例句")
parser.add_argument("--illustration", help="插画场景描述")
parser.add_argument("--seal", help="品牌印章文字")
args = parser.parse_args()
if args.idiom: IDIOM = args.idiom
if args.pinyin: PINYIN = args.pinyin
if args.title_en: ENGLISH_TITLE = args.title_en
if args.meaning: MEANING = args.meaning
if args.meaning_en: ENGLISH_MEANING = args.meaning_en
if args.example_cn: EXAMPLE_CN = args.example_cn
if args.example_en: EXAMPLE_EN = args.example_en
if args.illustration: ILLUSTRATION = args.illustration
if args.seal: SEAL_TEXT = args.seal

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
OUT = "/tmp/xhs_cards_v2"
os.makedirs(OUT, exist_ok=True)

VISUAL_BASE = """# Visual Style and Ultimate Realistic Material Base (Keep Constant)
[STYLE]: Traditional Chinese ink wash painting meets realistic photo of physical artifacts, with a friendly, modern cartoon character style. High-definition (8k).
[MATERIAL & TEXTURE]: Ultra-realistic photo of antique, hand-made Chinese rice paper (Xuan paper). The surface is characterized by:
  - Visible, raw rice paper fibers and imperfections.
  - A subtle tea-stained or aged ivory color.
  - Raw, irregular, slightly feathered paper edges that look cut and worn.
  - No smooth computer rendering, pure physical texture.
[PAINTING STYLE]: Delicate traditional Chinese brushwork, ink wash (Shuimo) technique, soft watercolor gradients, natural ink bleeding and bleeding edges around illustrations and text, as if hand-painted on the physical paper.
[COLOR PALETTE]: Harmonious ancient tones, dominated by deep ink blacks, muted vermilion, soft moss greens, and ochre, with a clean and focused composition.
[TYPOGRAPHY]:
  - [CHINESE]: Elegant, hand-drawn traditional Chinese brush calligraphy, illegible as computer font, with authentic texture.
  - [ENGLISH]: Classic, hand-drawn English serif calligraphy, clean and complementary to the Chinese brush style.
  - Both use texturised ink that bleeds into the paper fibers.
[LIGHTING]: Natural, soft, directional side-lighting that emphasizes the 3D texture and depth of the paper surface."""


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
print("📸 V2 Card 1: 封面")
print("=" * 45)

prompt_1 = f"""{VISUAL_BASE}

# Image 1 (Cover): Bilingual Idiom Only + Cartoon Illustration
[LAYOUT]: 9:16 vertical composition, clean, focused, and powerful.
[CONTENT]:
  - [CHINESE IDIOM]: "{IDIOM}" in large, bold, hand-drawn calligraphy at the top.
  - [ENGLISH IDIOM/MEANING]: Below the Chinese, "{PINYIN} · Playing Music to a Cow" in a smaller, clean, complementary serif font.
  - [ILLUSTRATION]: A friendly, highly-integrated, traditional Chinese cartoon illustration depicting: {ILLUSTRATION}
  - [DECORATION]: A matching, weathered red seal stamp with the brand name "{SEAL_TEXT}" in ancient seal script. Subtle, natural ink bleeding. This seal must appear on every card in the series.
  - No extra explanation text."""

resp_1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt_1,
    config={"response_modalities": ["Text", "Image"]}
)
img1 = save_image(resp_1, "01_cover.jpg")


# ======== Card 2: Meaning ========
print("\n📸 V2 Card 2: 释义")
print("=" * 45)

prompt_2 = f"""{VISUAL_BASE}

# Image 2 (Inside Page 1): Bilingual Idiom + Bilingual Explanation
[LAYOUT]: 9:16 vertical composition, text-focused, clean sections.
[CONTENT]:
  - [BILINGUAL IDIOM]: "{IDIOM}" in Chinese Calligraphy at the top and "{PINYIN} · Playing Music to a Cow" in English serif below.
  - [EXPLANATION SECTION]:
    - Title: "解释 / Explanation" (with bilingual labels).
    - [CHINESE EXPLANATION]: "{MEANING}"
    - [ENGLISH EXPLANATION]: "To talk about something over someone's head. To cast pearls before swine. To address the wrong audience."
  - [DECORATION]: A smaller illustration motif and a side stamp with "{SEAL_TEXT}" in seal script. Must match the brand seal from Card 1.

[STYLE MATCHING]: The paper texture, calligraphy, ink quality, side-lighting, and seal stamps (especially the "{SEAL_TEXT}" brand seal) must be EXACTLY the same as Card 1. The ink must bleed into paper fibers. 3D side-lighting on paper surface must be visible."""

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
print("\n📸 V2 Card 3: 举例")
print("=" * 45)

prompt_3 = f"""{VISUAL_BASE}

# Image 3 (Inside Page 2): Bilingual Idiom + Bilingual Usage Example
[LAYOUT]: 9:16 vertical composition, example-focused, clear sections.
[CONTENT]:
  - [BILINGUAL IDIOM]: "{IDIOM}" in Chinese Calligraphy at the top and "{PINYIN} · Playing Music to a Cow" in English serif below.
  - [USAGE SECTION]:
    - Title: "使用举例 / Usage Example" (with bilingual labels).
    - [CHINESE EXAMPLE]: "{EXAMPLE_CN}"
    - [ENGLISH EXAMPLE]: "{EXAMPLE_EN}"
  - [DECORATION]: Small, matching painting motifs and a side stamp with "{SEAL_TEXT}" in seal script. Must match the brand seal from Cards 1 and 2.

[STYLE MATCHING]: The paper texture, calligraphy, ink quality, side-lighting, and seal stamps must be IDENTICAL to Cards 1 and 2. The "{SEAL_TEXT}" brand seal should appear consistently. This is card 3 of a 3-card series."""

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
print(f"🎉 V2 全部生成完毕！输出: {OUT}/")
for f in sorted(os.listdir(OUT)):
    sz = os.path.getsize(os.path.join(OUT, f)) // 1024
    print(f"  {f}: {sz}KB")
