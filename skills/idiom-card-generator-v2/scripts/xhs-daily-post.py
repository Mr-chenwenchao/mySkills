#!/usr/bin/env python3
"""
全自动小红书成语发布 — 每日一次（防检测版）
随机选未用过的成语 → 生成三张卡 → 发布
定时触发后在 0-60 分钟随机延时，避免固定时间被检测为脚本
"""
import base64, re, subprocess, json, random, os, sys, requests, time

SCRIPT = os.path.expanduser("~/.hermes/skills/xiaohongshu/idiom-card-generator-v2/scripts/generate.py")
MCP_URL = "http://127.0.0.1:18060/mcp"
USED_FILE = "/tmp/xhs_used_idioms.json"

# 成语库（30个，用完前有人提醒补充）
IDIOMS = {
    "画蛇添足": {
        "pinyin": "huà shé tiān zú",
        "meaning": "比喻做了多余的事，非但无益，反而不合适。也比喻节外生枝，多此一举。",
        "example_cn": "这个方案已经很完整了，再加这些细节就是画蛇添足了。",
        "example_en": "The plan is already complete — adding more details would be gilding the lily.",
        "illustration": "一位古代书生在纸上画了一条栩栩如生的蛇，但觉得不够完美，又在蛇身下面添了四只脚，破坏了整体美感。朋友摇头叹息。"
    },
    "对牛弹琴": {
        "pinyin": "duì niú tán qín",
        "meaning": "比喻说话不看对象，对不懂道理的人讲道理，对外行人说内行话。",
        "example_cn": "他跟我这个完全不懂音乐的人大谈交响乐，简直是对牛弹琴。",
        "example_en": "Talking about symphonies to someone who knows nothing about music — like playing music to a cow.",
        "illustration": "一位琴师在山间草地上弹古琴，对面坐着一头大黄牛，呆萌地看着琴师。青山绿水，竹叶飘落。"
    },
    "胸有成竹": {
        "pinyin": "xiōng yǒu chéng zhú",
        "meaning": "比喻在做事之前已经拿定主意，心中已有完整的筹划和把握。",
        "example_cn": "他准备了整整一个月，上台答辩时胸有成竹。",
        "example_en": "He prepared for a month and walked into the defense with complete confidence.",
        "illustration": "一位文人画家坐在书案前，并不看面前的竹子，闭目凝神，胸中早已有了完整的竹子形象。"
    },
    "画龙点睛": {
        "pinyin": "huà lóng diǎn jīng",
        "meaning": "比喻在关键的地方用精辟的语句点明要旨，使内容更加生动传神。",
        "example_cn": "文章结尾引用一句古诗，简直是画龙点睛之笔。",
        "example_en": "Quoting a classic poem at the end was the perfect finishing touch.",
        "illustration": "一位画家在墙上画了一条栩栩如生的龙，最后用笔尖轻轻点上龙的眼睛。"
    },
    "掩耳盗铃": {
        "pinyin": "yǎn ěr dào líng",
        "meaning": "比喻自己欺骗自己，明明掩盖不住的事情偏要想法子掩盖。",
        "example_cn": "考试作弊还想不被发现，简直是掩耳盗铃。",
        "example_en": "Cheating and thinking you won't get caught — like covering your ears while stealing a bell.",
        "illustration": "一个小偷站在大铜钟前，捂着耳朵去偷钟，以为听不到钟声别人也听不到。"
    },
    "叶公好龙": {
        "pinyin": "yè gōng hào lóng",
        "meaning": "比喻口头上说爱好某事物，实际上并不是真的爱好，甚至害怕它。",
        "example_cn": "他整天说喜欢冒险，结果连游乐园都不敢去，真是叶公好龙。",
        "example_en": "He talks about loving adventure but is afraid of amusement parks — like Lord Ye professing to love dragons.",
        "illustration": "叶公躲在桌子底下发抖，一条真龙从窗口探进头来，龙须飘动，云雾缭绕。"
    },
    "守株待兔": {
        "pinyin": "shǒu zhū dài tù",
        "meaning": "比喻不主动努力，存在侥幸心理，希望得到意外的收获。",
        "example_cn": "找工作不能守株待兔，要主动出击才行。",
        "example_en": "You can't just wait by the tree stump for a job — you need to actively pursue opportunities.",
        "illustration": "一个农夫靠在大树桩上打瞌睡，旁边放着一只撞死的兔子，农田里长满了杂草。"
    },
    "狐假虎威": {
        "pinyin": "hú jiǎ hǔ wēi",
        "meaning": "比喻仗着别人的势力欺压人。讽刺自己没有本事、靠别人炫耀的人。",
        "example_cn": "他不过是经理的亲戚，就狐假虎威地指挥大家做事。",
        "example_en": "He's just the manager's relative, yet throws his weight around like a fox borrowing a tiger's might.",
        "illustration": "一只狐狸昂首挺胸走在前面，身后跟着一只巨大的老虎，森林里的小动物们吓得四处逃窜。"
    },
    "井底之蛙": {
        "pinyin": "jǐng dǐ zhī wā",
        "meaning": "比喻见识狭窄、目光短浅的人。",
        "example_cn": "他觉得自己很了不起，其实不过是井底之蛙。",
        "example_en": "He thinks he's amazing, but he's just a frog at the bottom of a well.",
        "illustration": "一只青蛙坐在古井底部，抬头望着井口那一小片圆形的天空，脸上露出满足的笑容。"
    },
    "鹤立鸡群": {
        "pinyin": "hè lì jī qún",
        "meaning": "比喻一个人的仪表或才能在周围一群人里显得很突出。",
        "example_cn": "她在所有候选人中鹤立鸡群，面试官一眼就看中了她。",
        "example_en": "She stood out among all the candidates like a crane among chickens.",
        "illustration": "一群鸡在院子里啄食，一只优雅的白鹤站在它们中间，长颈高抬，气质超群。"
    },
    "亡羊补牢": {
        "pinyin": "wáng yáng bǔ láo",
        "meaning": "比喻出了问题以后想办法补救，防止继续受损失。",
        "example_cn": "虽然项目出了点问题，但现在亡羊补牢还来得及。",
        "example_en": "It's not too late to fix the problem — better late than never.",
        "illustration": "一个农夫正在修补破损的羊圈，旁边有一只跑丢的羊正在被找回来的路上。夕阳西下。"
    },
    "塞翁失马": {
        "pinyin": "sài wēng shī mǎ",
        "meaning": "比喻坏事在一定条件下可变为好事。福祸相依。",
        "example_cn": "虽然丢了工作，但后来找到了更好的机会，真是塞翁失马。",
        "example_en": "Losing the job led to a better opportunity — a blessing in disguise.",
        "illustration": "一位老翁站在边塞的篱笆旁，看着一匹白马跑向远方，表情平静。远处有群山和夕阳。"
    },
    "愚公移山": {
        "pinyin": "yú gōng yí shān",
        "meaning": "比喻坚持不懈地改造自然和坚定不移地进行斗争。",
        "example_cn": "创业就像愚公移山，需要日积月累的努力。",
        "example_en": "Starting a business is like the foolish old man moving mountains — persistent effort over time.",
        "illustration": "一位白发老者带领全家老小，用镐头和竹筐挖山运石。汗水洒落，但人人面带坚毅。"
    },
    "孟母三迁": {
        "pinyin": "mèng mǔ sān qiān",
        "meaning": "形容家长为了教育子女，选择良好的学习环境。",
        "example_cn": "为了孩子的教育，他们搬了三次家，真是孟母三迁。",
        "example_en": "They moved three times for their child's education — like Mencius's mother choosing the right environment.",
        "illustration": "一位古代母亲牵着孩子的手，三次搬家从墓地旁到市集旁再到学堂旁。最后孩子在学堂窗边认真读书。"
    },
    "班门弄斧": {
        "pinyin": "bān mén nòng fǔ",
        "meaning": "比喻在行家面前卖弄本领，不自量力。",
        "example_cn": "我在老师面前谈书法，简直是班门弄斧。",
        "example_en": "Talking about calligraphy in front of the master — like showing off斧 skills at Lu Ban's door.",
        "illustration": "一个年轻人在一位白发苍苍的老木匠面前炫耀自己的木工活，老木匠微笑着摇头。"
    },
    "纸上谈兵": {
        "pinyin": "zhǐ shàng tán bīng",
        "meaning": "比喻只凭书本知识空发议论，不能解决实际问题。",
        "example_cn": "他理论一套一套的，但从来没有实际操作过，纯属纸上谈兵。",
        "example_en": "He has all the theories but zero practical experience — all talk and no action.",
        "illustration": "一位年轻将领在营帐中对着地图夸夸其谈，而帐外真正的士兵正在艰苦训练。"
    },
    "入木三分": {
        "pinyin": "rù mù sān fēn",
        "meaning": "比喻分析问题或描写事物非常深刻、透彻。",
        "example_cn": "他这篇评论入木三分，一针见血地指出了问题的本质。",
        "example_en": "His analysis was penetrating — he cut right to the heart of the issue.",
        "illustration": "王羲之在木板上写字，墨迹渗入木板三分深。旁边的人惊叹不已。"
    },
    "一箭双雕": {
        "pinyin": "yī jiàn shuāng diāo",
        "meaning": "比喻做一件事达到两个目的。一举两得。",
        "example_cn": "这次出差既能谈业务又能旅游，真是一箭双雕。",
        "example_en": "The business trip combines work and sightseeing — killing two birds with one stone.",
        "illustration": "一位将军拉满弓，一支箭飞向天空，两只大雕应声而落。草原广阔，气势恢宏。"
    }
}

# 随机延时（0-60分钟），避免固定时间被检测
delay_minutes = random.randint(0, 60)
print(f"⏳ 随机延时 {delay_minutes} 分钟...")
time.sleep(delay_minutes * 60)

# 读取已使用记录
used = []
if os.path.exists(USED_FILE):
    with open(USED_FILE) as f:
        used = json.load(f)
else:
    used = ["画蛇添足"]  # 初始只有已发布的

available = [k for k in IDIOMS if k not in used]
if not available:
    print("❌ 所有成语用完了，循环重置！")
    available = list(IDIOMS.keys())
    used = []

idiom = random.choice(available)
data = IDIOMS[idiom]
print(f"🎯 选中: {idiom}")

# 写入 generate.py 配置
with open(SCRIPT, "r") as f:
    content = f.read()

# 用 argument 方式调用脚本，不直接改文件
cmd = [
    "python3", SCRIPT,
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

# 发布到小红书
s = requests.Session()
s.proxies = {"http": "", "https": ""}
r = s.post(MCP_URL, json={"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"hermes","version":"1.0"}
}})
sid = r.headers.get("Mcp-Session-Id", "")

r = s.post(MCP_URL, json={
    "jsonrpc":"2.0","id":2,"method":"tools/call","params":{
        "name":"publish_content","arguments":{
            "title": f"{idiom} 🐉 每天学成语",
            "content": f"【{idiom}】{data['pinyin']} · {data['example_en'].split('.')[0]}\n\n{data['meaning']}\n\n{data['example_en']}\n\n你学会了吗？👇",
            "images": [
                "/tmp/xhs_cards_v2/01_cover.jpg",
                "/tmp/xhs_cards_v2/02_meaning.jpg",
                "/tmp/xhs_cards_v2/03_usage.jpg"
            ],
            "tags": ["成语", "双语", "学中文", idiom, "若瑜成语"]
        }
    }
}, headers={"Mcp-Session-Id": sid})

pub = r.json()
st = pub.get("result",{}).get("content",[{}])[0].get("text","")
print(f"\n📤 {'✅ 发布成功' if '成功' in st else '❌ 失败'}")
print(st[:150])

# 记录
used.append(idiom)
with open(USED_FILE, "w") as f:
    json.dump(used, f, ensure_ascii=False)
print(f"📝 已使用: {used}")
