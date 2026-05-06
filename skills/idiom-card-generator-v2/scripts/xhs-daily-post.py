#!/usr/bin/env python3
"""
每日成语卡片生成 — 保存到本地文件夹，供人工发布
每天 06:00 自动跑，输出到 ~/Documents/project/小红书作品集/YYYYMMDD/成语名/
包含 3 张 1242x1660 图片 + content.md（作品文案）
"""
import os, sys, json, random, time, subprocess, shutil

SCRIPT = os.path.expanduser("~/.hermes/skills/xiaohongshu/idiom-card-generator-v2/scripts/generate.py")
OUT_BASE = os.path.expanduser("~/Documents/project/小红书作品集")
USED_FILE = "/tmp/xhs_used_idioms.json"

# 成语库（100个，同上）
IDIOMS = {
    "画蛇添足": {"pinyin":"huà shé tiān zú","meaning":"比喻做了多余的事，非但无益，反而不合适。","example_cn":"这个方案已经很完整了，再加细节就是画蛇添足了。","example_en":"Adding more details to a complete plan is like drawing legs on a snake.","illustration":"一位古代书生在纸上画了一条栩栩如生的蛇，但觉得不够完美，又在蛇身下面添了四只脚，破坏了整体美感。"},
    "对牛弹琴": {"pinyin":"duì niú tán qín","meaning":"比喻说话不看对象，对不懂道理的人讲道理。","example_cn":"他跟我大谈交响乐，简直是对牛弹琴。","example_en":"Talking about symphonies to someone who knows nothing about music.","illustration":"一位琴师在山间草地上弹古琴，对面坐着一头大黄牛呆萌地看着他。"},
    "胸有成竹": {"pinyin":"xiōng yǒu chéng zhú","meaning":"比喻做事前已有完整的筹划和把握。","example_cn":"他准备了整整一个月，答辩时胸有成竹。","example_en":"He prepared for a month and walked in with complete confidence.","illustration":"文人画家闭目凝神，胸中已有完整竹子形象，毛笔悬停在纸上。"},
    "画龙点睛": {"pinyin":"huà lóng diǎn jīng","meaning":"比喻在关键处用精辟语句点明要旨，使内容更加生动。","example_cn":"文章结尾引用古诗，简直是画龙点睛之笔。","example_en":"Quoting a poem at the end was the perfect finishing touch.","illustration":"画家在墙上画龙，最后用笔尖轻轻点上眼睛，龙瞬间活了起来。"},
    "掩耳盗铃": {"pinyin":"yǎn ěr dào líng","meaning":"比喻自己欺骗自己，明明掩盖不住的事情偏要掩盖。","example_cn":"考试作弊还想不被发现，简直是掩耳盗铃。","example_en":"Cheating and thinking you won't get caught — covering your ears while stealing a bell.","illustration":"小偷捂着耳朵去偷钟，以为听不到钟声别人也听不到。"},
    "叶公好龙": {"pinyin":"yè gōng hào lóng","meaning":"比喻口头上说爱好某事物，实际上并不是真的爱好。","example_cn":"他整天说喜欢冒险，结果连游乐园都不敢去。","example_en":"He talks about loving adventure but is afraid of amusement parks.","illustration":"叶公躲在桌子下发抖，真龙从窗口探进头来，龙须飘动。"},
    "守株待兔": {"pinyin":"shǒu zhū dài tù","meaning":"比喻不主动努力，存在侥幸心理。","example_cn":"找工作不能守株待兔，要主动出击。","example_en":"You can't just wait for opportunities — you need to pursue them.","illustration":"农夫靠在大树桩上打瞌睡，旁边放着一只撞死的兔子。"},
    "狐假虎威": {"pinyin":"hú jiǎ hǔ wēi","meaning":"比喻仗着别人的势力欺压人。","example_cn":"他不过是经理亲戚，就狐假虎威地指挥大家。","example_en":"He's just the manager's relative yet throws his weight around.","illustration":"狐狸昂首挺胸走在前面，身后跟着一只巨大的老虎。"},
    "井底之蛙": {"pinyin":"jǐng dǐ zhī wā","meaning":"比喻见识狭窄、目光短浅的人。","example_cn":"他觉得自己很了不起，不过是井底之蛙。","example_en":"He thinks he's amazing but he's just a frog in a well.","illustration":"青蛙坐在古井底部，抬头望着井口那一小片圆形的天空。"},
    "鹤立鸡群": {"pinyin":"hè lì jī qún","meaning":"比喻一个人的仪表或才能在人群中显得很突出。","example_cn":"她在所有候选人中鹤立鸡群。","example_en":"She stood out among all candidates like a crane among chickens.","illustration":"一只优雅的白鹤站在鸡群中间，长颈高抬，气质超群。"},
    "亡羊补牢": {"pinyin":"wáng yáng bǔ láo","meaning":"比喻出了问题后想办法补救，防止继续受损失。","example_cn":"虽然项目出了点问题，现在亡羊补牢还来得及。","example_en":"It's not too late to fix the problem — better late than never.","illustration":"农夫正在修补破损的羊圈，旁边有被找回来的羊。"},
    "塞翁失马": {"pinyin":"sài wēng shī mǎ","meaning":"比喻坏事在一定条件下可变为好事。","example_cn":"丢了工作却找到更好的机会，真是塞翁失马。","example_en":"Losing the job led to a better opportunity — a blessing in disguise.","illustration":"老翁站在边塞篱笆旁看着白马跑向远方，表情平静。"},
    "愚公移山": {"pinyin":"yú gōng yí shān","meaning":"比喻坚持不懈地改造自然，坚定不移地奋斗。","example_cn":"创业就像愚公移山，需要日积月累。","example_en":"Starting a business is like moving mountains — persistent effort.","illustration":"白发老者带领全家用镐头和竹筐挖山运石，人人面带坚毅。"},
    "孟母三迁": {"pinyin":"mèng mǔ sān qiān","meaning":"形容家长为了教育子女选择良好的学习环境。","example_cn":"为了孩子教育搬了三次家，真是孟母三迁。","example_en":"Moving three times for education — like Mencius's mother.","illustration":"母亲牵着孩子三次搬家，从墓地旁到市集旁再到学堂旁。"},
    "班门弄斧": {"pinyin":"bān mén nòng fǔ","meaning":"比喻在行家面前卖弄本领，不自量力。","example_cn":"我在老师面前谈书法，班门弄斧了。","example_en":"Talking about calligraphy in front of the master.","illustration":"年轻人在白发老木匠面前炫耀木工活，老木匠微笑摇头。"},
    "纸上谈兵": {"pinyin":"zhǐ shàng tán bīng","meaning":"比喻只凭书本知识空发议论，不能解决实际问题。","example_cn":"他理论一套套但没有实操过，纯属纸上谈兵。","example_en":"All theories but zero practical experience — all talk.","illustration":"年轻将领对着地图夸夸其谈，帐外士兵正在艰苦训练。"},
    "入木三分": {"pinyin":"rù mù sān fēn","meaning":"比喻分析问题非常深刻透彻。","example_cn":"他的评论入木三分，指出了问题本质。","example_en":"His analysis was penetrating — right to the heart of the issue.","illustration":"王羲之在木板上写字，墨迹渗入木板三分深。"},
    "一箭双雕": {"pinyin":"yī jiàn shuāng diāo","meaning":"比喻做一件事达到两个目的，一举两得。","example_cn":"出差既能谈业务又能旅游，一箭双雕。","example_en":"A business trip combining work and sightseeing — killing two birds with one stone.","illustration":"将军拉满弓，一支箭飞向天空，两只大雕应声而落。"},
    "百发百中": {"pinyin":"bǎi fā bǎi zhòng","meaning":"比喻做事有充分把握，绝不落空。","example_cn":"他每次预测都百发百中。","example_en":"His predictions hit the mark every single time.","illustration":"一位神射手拉弓射箭，箭箭正中靶心，围观的人鼓掌叫好。"},
    "半途而废": {"pinyin":"bàn tú ér fèi","meaning":"比喻做事中途停止，不能坚持到底。","example_cn":"学一门语言不能半途而废。","example_en":"Learning a language — you can't give up halfway.","illustration":"一个书生走到山路中间突然转身往回走，山顶的风景若隐若现。"},
    "杯弓蛇影": {"pinyin":"bēi gōng shé yǐng","meaning":"比喻疑神疑鬼，自己吓自己。","example_cn":"他听到一点声音就紧张，简直是杯弓蛇影。","example_en":"Getting spooked by nothing — seeing a snake in a cup reflection.","illustration":"一人端起酒杯，看到杯中弓的倒影以为是蛇，吓得脸色发白。"},
    "沧海桑田": {"pinyin":"cāng hǎi sāng tián","meaning":"比喻世事变化很大。","example_cn":"几十年后再回故乡，已是沧海桑田。","example_en":"Returning decades later — everything had changed like sea to mulberry fields.","illustration":"同一片土地上，一半是海浪翻涌，一半是桑树成林，中间站着一位老者。"},
    "守口如瓶": {"pinyin":"shǒu kǒu rú píng","meaning":"形容说话谨慎，严守秘密。","example_cn":"他守口如瓶，一个字都不说。","example_en":"He kept his mouth shut tight — not a single word escaped.","illustration":"一个人嘴上挂着一把锁，表情坚定神秘。"},
}

# 随机延时 0-60 分钟
delay = random.randint(0, 60)
print(f"⏳ 随机延时 {delay} 分钟...")
time.sleep(delay * 60)

# 读已用记录
used = []
if os.path.exists(USED_FILE):
    with open(USED_FILE) as f:
        used = json.load(f)
else:
    used = ["画蛇添足", "对牛弹琴", "掩耳盗铃"]

available = [k for k in IDIOMS if k not in used]
if not available:
    available = list(IDIOMS.keys())
    used = []

idiom = random.choice(available)
data = IDIOMS[idiom]
print(f"🎯 选中: {idiom}")

# 生成图片
cmd = ["python3", SCRIPT,
    "--idiom", idiom,
    "--pinyin", data["pinyin"],
    "--meaning", data["meaning"],
    "--meaning-en", data["example_en"].split(".")[0] + ".",
    "--example-cn", data["example_cn"],
    "--example-en", data["example_en"],
    "--title-en", idiom[:4],
    "--illustration", data["illustration"],
    "--seal", "若瑜成语"
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
print(result.stdout[-500:])
if result.returncode != 0:
    print(f"❌ 生成失败: {result.stderr[:200]}")
    sys.exit(1)

# 创建输出目录
today = time.strftime("%Y%m%d")
out_dir = os.path.join(OUT_BASE, today, idiom)
os.makedirs(out_dir, exist_ok=True)

# 复制图片
src_dir = "/tmp/xhs_cards_v2"
for fname in ["01_cover.jpg", "02_meaning.jpg", "03_usage.jpg"]:
    src = os.path.join(src_dir, fname)
    dst = os.path.join(out_dir, fname)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"📄 复制: {fname}")

# 生成作品文案
content_md = f"""# {idiom}（{data['pinyin']}）

## 标题
{idiom} 🐉 每天学成语

## 正文
【{idiom}】{data['pinyin']} · {data['example_en'].split('.')[0]}

{data['meaning']}

例句：{data['example_cn']}
{data['example_en']}

你学会了吗？👇

## 标签
#成语 #双语 #学中文 #LearnChinese #ThinkChinese #传统文化 #知识分享 #{idiom} #若瑜成语

## 图片说明
- 01_cover.jpg — 封面：成语书法 + 国风插图
- 02_meaning.jpg — 释义：中英双语解释
- 03_usage.jpg — 举例：中英双语例句

## 生成时间
{time.strftime('%Y-%m-%d %H:%M:%S')}

## 品牌印章
若瑜成语
"""

md_path = os.path.join(out_dir, "content.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write(content_md)
print(f"📝 文案: content.md")

print(f"\n📂 输出目录: {out_dir}")
print(f"   包含: 01_cover.jpg, 02_meaning.jpg, 03_usage.jpg, content.md")

# 记录已用
used.append(idiom)
with open(USED_FILE, "w") as f:
    json.dump(used, f, ensure_ascii=False)
print(f"📝 已用: {len(used)} 个成语")
