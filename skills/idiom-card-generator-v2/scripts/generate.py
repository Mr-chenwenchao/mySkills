#!/usr/bin/env python3
"""
小红书成语卡片 V2 — 防AI检测版
保持图生图视觉连续（Card 1→2→3），但每张卡纸纹/墨色微随机化，
后处理仅加肉眼几乎不可见的细微差异。
"""
import base64, argparse, os, sys, random, json
from google import genai
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument("--idiom", default="叶公好龙")
parser.add_argument("--pinyin", default="yè gōng hào lóng")
parser.add_argument("--meaning", default="比喻口头上说爱好某事物，实际上并不是真的爱好，甚至害怕它。")
parser.add_argument("--meaning-en", default="To profess love for something but actually be afraid of it.")
parser.add_argument("--example-cn", default="他整天说喜欢冒险，结果连游乐园都不敢去，真是叶公好龙。")
parser.add_argument("--example-en", default="He talks about loving adventure but is afraid of amusement parks.")
parser.add_argument("--title-en", default="Professing Love for Dragons")
parser.add_argument("--illustration", default="一位身穿古代官服的叶公躲在桌子底下发抖，一条真龙从窗口探进头来。墙上挂满龙的书画。")
parser.add_argument("--seal", default="若瑜的成语笔记")
parser.add_argument("--out", default="/tmp/xhs_cards_v2")
args = parser.parse_args()

IDIOM, PINYIN = args.idiom, args.pinyin
MEANING, EN_MEANING = args.meaning, args.meaning_en
EXAMPLE_CN, EXAMPLE_EN = args.example_cn, args.example_en
EN_TITLE = args.title_en
ILLUSTRATION = args.illustration
SEAL_TEXT = args.seal

KEY = os.environ.get("GOOGLE_API_KEY", "")
if not KEY:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("GOOGLE_API_KEY="):
                    KEY = line.strip().split("=", 1)[1]; break
if not KEY: print("❌ 需要 GOOGLE_API_KEY"); sys.exit(1)

client = genai.Client(api_key=KEY, http_options={"api_version": "v1beta"})
OUT = args.out
os.makedirs(OUT, exist_ok=True)
TW, TH = 1242, 1660

# ======== 视觉基座（不变的核心风格）========
VISUAL_CORE = """# Visual Style: Traditional Chinese ink wash on authentic Xuan paper
[MATERIAL]: Ultra-realistic antique Xuan paper, {paper} color, {texture}
[STYLE]: Traditional Chinese brushwork with ink wash technique
[COLORS]: Deep ink blacks, muted vermilion, soft moss greens, ochre
[TYPOGRAPHY]: Chinese brush calligraphy + English serif calligraphy, hand-drawn feel
[INK]: Natural ink bleeding effect, {bleed} intensity
[SEAL]: A weathered vermilion seal stamp "{SEAL_TEXT}" in seal script, consistently sized, placed at bottom area of the card
[LIGHTING]: Soft natural side lighting"""

# 极细微随机参数（肉眼几乎不可见的变化）
PAPER_VARS = [
    ("aged ivory", "visible rice paper fibers"),
    ("warm cream", "subtle fiber bundles"),
    ("light ochre", "slight pulp texture"),
    ("pale beige", "natural paper grain"),
    ("cream ivory", "fine bamboo fiber traces"),
]
INK_VARS = ["natural", "gentle", "subtle"]


def save_and_upload(response, filename):
    """Save image and return (path, base64_data) for inline use in next request"""
    if not response.candidates:
        print(f"  ❌ No candidates")
        return None, None
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            path = os.path.join(OUT, filename)
            with open(path, "wb") as f:
                f.write(part.inline_data.data)
            b64 = base64.b64encode(part.inline_data.data).decode()
            print(f"  ✅ {filename} ({len(part.inline_data.data)//1024}KB)")
            return path, b64
    print(f"  ⚠️ No image")
    return None, None


def subtle_noise(img_path):
    """极细微的后处理：肉眼几乎不可见"""
    img = Image.open(img_path).convert("RGB")
    if img.size != (TW, TH):
        img = img.resize((TW, TH), Image.LANCZOS)
    
    pixels = img.load()
    
    # 1. 极少量噪点（0.1%，比之前少10倍）
    noise_count = int(TW * TH * random.uniform(0.0008, 0.002))
    for _ in range(noise_count):
        x, y = random.randint(0, TW-1), random.randint(0, TH-1)
        r, g, b = pixels[x, y]
        noise = random.randint(-12, 12)
        pixels[x, y] = (max(0, min(255, r+noise)), max(0, min(255, g+noise)), max(0, min(255, b+noise)))
    
    # 2. 极细微色温（1%，肉眼几乎看不出）
    shift = random.uniform(-0.01, 0.01)
    if abs(shift) > 0.005:
        for x in range(TW):
            for y in range(TH):
                r, g, b = pixels[x, y]
                if shift > 0:
                    pixels[x, y] = (min(255, r+2), g, max(0, b-1))
                else:
                    pixels[x, y] = (max(0, r-2), g, min(255, b+1))
    
    # 3. 极轻微亮度抖动（0.5%）
    brightness = random.uniform(0.995, 1.005)
    if abs(brightness - 1.0) > 0.003:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)
        pixels = img.load()
    
    # 4. 灰尘点减少到 1-3 个，颜色更浅
    dust_count = random.randint(1, 3)
    draw = ImageDraw.Draw(img)
    for _ in range(dust_count):
        x, y = random.randint(100, TW-100), random.randint(100, TH-100)
        sz = random.randint(1, 3)
        shade = random.randint(80, 120)
        draw.ellipse([x, y, x+sz, y+sz], fill=(shade, shade-5, shade-10))
    
    img.save(img_path, quality=92)
    new_sz = os.path.getsize(img_path) // 1024
    print(f"  ✨ {img_path.split('/')[-1]} 后处理 ({new_sz}KB)")
    return img_path


# ======== Card 1: 封面（独立生成）========
p = random.choice(PAPER_VARS)
ink = random.choice(INK_VARS)
paper_desc = VISUAL_CORE.format(paper=p[0], texture=p[1], bleed=ink, SEAL_TEXT=SEAL_TEXT)

print(f"🎯 {IDIOM} | 纸:{p[0]} 墨:{ink}")
print("=" * 45)
print("\n📸 01_cover.jpg")

prompt_1 = f"""{paper_desc}

Image 1 (Cover): "{IDIOM}" in large bold calligraphy at top.
Below: "{PINYIN} · {EN_TITLE}" in English serif.
Center: Traditional Chinese cartoon illustration — {ILLUSTRATION}
A weathered red seal stamp with "{SEAL_TEXT}" in seal script, consistent size.
NO explanation text. 3:4 vertical (1242x1660 pixels)."""

resp_1 = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt_1,
    config={"response_modalities": ["Text", "Image"]}
)
img1, img1_b64 = save_and_upload(resp_1, "01_cover.jpg")


# ======== Card 2: 释义（以 Card 1 为参考，但微调纸纹）========
p2 = random.choice(PAPER_VARS)
ink2 = random.choice(INK_VARS)
paper_desc2 = VISUAL_CORE.format(paper=p2[0], texture=p2[1], bleed=ink2, SEAL_TEXT=SEAL_TEXT)

print(f"\n📸 02_meaning.jpg (纸:{p2[0]} 墨:{ink2})")

prompt_2 = f"""{paper_desc2}

Image 2: Based on the EXACT SAME visual style as Image 1. Same paper texture feel, same seal size/style, same lighting. Only paper characteristics may differ slightly.

"{IDIOM}" in calligraphy at top. "{PINYIN} · {EN_TITLE}" in English below.
Title: "解释 / Explanation"
Chinese: "{MEANING}"
English: "{EN_MEANING}"
Small floating ink wash motif. Seal stamp "{SEAL_TEXT}" in seal script.
3:4 vertical (1242x1660)."""

if img1:
    resp_2 = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[
            {"inline_data": {"mime_type": "image/jpeg", "data": img1_b64}},
            prompt_2
        ],
        config={"response_modalities": ["Text", "Image"]}
    )
    img2, img2_b64 = save_and_upload(resp_2, "02_meaning.jpg")


# ======== Card 3: 举例（以 Card 1+2 为参考，微调纸纹）========
p3 = random.choice(PAPER_VARS)
ink3 = random.choice(INK_VARS)
paper_desc3 = VISUAL_CORE.format(paper=p3[0], texture=p3[1], bleed=ink3, SEAL_TEXT=SEAL_TEXT)

print(f"\n📸 03_usage.jpg (纸:{p3[0]} 墨:{ink3})")

prompt_3 = f"""{paper_desc3}

Image 3: EXACT same visual series as Images 1 and 2. Same paper feel, same seal size/style.

"{IDIOM}" in calligraphy. "{PINYIN} · {EN_TITLE}" in English below.
Title: "使用举例 / Usage Example"
Chinese: "{EXAMPLE_CN}"
English: "{EXAMPLE_EN}"
Small floating ink wash decorative element. Seal "{SEAL_TEXT}" in seal script.
3:4 vertical (1242x1660)."""

if img1 and img2:
    resp_3 = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[
            {"inline_data": {"mime_type": "image/jpeg", "data": img1_b64}},
            {"inline_data": {"mime_type": "image/jpeg", "data": img2_b64}},
            prompt_3
        ],
        config={"response_modalities": ["Text", "Image"]}
    )
    img3, img3_b64 = save_and_upload(resp_3, "03_usage.jpg")


# ======== 后处理 ========
print(f"\n🎨 细微后处理...")
for f in sorted(os.listdir(OUT)):
    if f.endswith('.jpg'):
        subtle_noise(os.path.join(OUT, f))

print(f"\n{'='*45}")
print(f"🎉 完成！{OUT}/")
for f in sorted(os.listdir(OUT)):
    if f.endswith('.jpg'):
        img = Image.open(os.path.join(OUT, f))
        sz = os.path.getsize(os.path.join(OUT, f)) // 1024
        print(f"  {f}: {img.size[0]}x{img.size[1]} {sz}KB")
