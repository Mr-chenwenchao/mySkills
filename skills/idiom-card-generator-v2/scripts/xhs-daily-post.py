#!/usr/bin/env python3
"""
全自动小红书成语发布 — 每日一次
随机选未用过的成语 → 生成三张卡 → 发布
"""
import base64, re, subprocess, json, random, os, sys, requests
import hashlib

SCRIPT = os.path.expanduser("~/.hermes/skills/xiaohongshu/idiom-card-generator-v2/scripts/generate.py")
MCP_URL = "http://127.0.0.1:18060/mcp"
USED_FILE = "/tmp/xhs_used_idioms.json"

# 成语库（排除已用过的）
IDIOMS = {
    "画蛇添足": {
        "pinyin": "huà shé tiān zú",
        "meaning": "比喻做了多余的事，非但无益，反而不合适。也比喻节外生枝，多此一举。",
        "example_cn": "这个方案已经很完整了，再加这些细节就是画蛇添足了。",
        "example_en": "The plan is already complete — adding more details would be like drawing legs on a snake.",
        "illustration": "一位古代书生在纸上画了一条栩栩如生的蛇，蛇身蜿蜒，鳞片清晰。但他觉得不够完美，又在蛇身下面添了四只脚。旁边的朋友摇头叹息。周围有墨色晕染，画面中蛇和脚的风格对比明显，暗示多此一举。"
    },
    "守株待兔": {
        "pinyin": "shǒu zhū dài tù",
        "meaning": "比喻不主动努力，存在侥幸心理，希望得到意外的收获。也讽刺那些死守狭隘经验、不知变通的人。",
        "example_cn": "找工作不能守株待兔，要主动出击才行。",
        "example_en": "You can't just wait by the tree stump for a job — you need to actively pursue opportunities.",
        "illustration": "一个古代农夫靠在一棵大树桩上打瞌睡，旁边放着一只撞死的兔子。农田里长满了杂草。远处有别的农夫在辛勤耕种。阳光斜照，画面幽默中带讽刺。"
    },
    "掩耳盗铃": {
        "pinyin": "yǎn ěr dào líng",
        "meaning": "比喻自己欺骗自己，明明掩盖不住的事情偏要想法子掩盖。",
        "example_cn": "考试作弊还想不被发现，简直是掩耳盗铃。",
        "example_en": "Cheating on an exam and thinking you won't get caught is like covering your ears while stealing a bell.",
        "illustration": "一个古代小偷站在一口大铜钟前，一只手捂着耳朵，另一只手去偷钟。他的眼睛紧闭，脸上带着天真的笑容，以为自己听不到钟声别人也听不到。古色古香的庭院背景，画面幽默。"
    },
    "叶公好龙": {
        "pinyin": "yè gōng hào lóng",
        "meaning": "比喻口头上说爱好某事物，实际上并不是真的爱好，甚至害怕它。",
        "example_cn": "他整天说喜欢冒险，结果连游乐园都不敢去，真是叶公好龙。",
        "example_en": "He talks about loving adventure but is afraid of amusement parks — like Lord Ye professing to love dragons.",
        "illustration": "一位身穿古代官服的叶公，惊恐地躲在桌子底下，浑身发抖。一条威严的真龙从窗口探进头来，龙须飘动，云雾缭绕。墙上挂满了龙的书画和雕刻，桌案上也有龙纹。画面极具戏剧性。"
    },
    "狐假虎威": {
        "pinyin": "hú jiǎ hǔ wēi",
        "meaning": "比喻仗着别人的势力欺压人。也讽刺那些自己没有本事，靠别人的力量来炫耀的人。",
        "example_cn": "他不过是经理的亲戚，就狐假虎威地指挥大家做事。",
        "example_en": "He's just the manager's relative, yet he throws his weight around like a fox borrowing a tiger's might.",
        "illustration": "一只狐狸昂首挺胸走在前面，身后跟着一只巨大的老虎。森林里的小动物们看到老虎都吓得四处逃窜，而狐狸得意洋洋地走在前面。老虎则一脸困惑地跟着狐狸。"
    },
    "井底之蛙": {
        "pinyin": "jǐng dǐ zhī wā",
        "meaning": "比喻见识狭窄、目光短浅的人。",
        "example_cn": "他觉得自己很了不起，其实不过是井底之蛙。",
        "example_en": "He thinks he's amazing, but he's just a frog at the bottom of a well.",
        "illustration": "一只青蛙坐在深深的古井底部，抬头望着井口那一小片圆形的天空，脸上露出满足的笑容。井壁上长着青苔，井口外有白云飘过。青蛙不知道外面的世界有多大，还以为这就是整个天空。"
    }
}

# 读取已使用记录
used_file = "/tmp/xhs_used_idioms.json"
used = []
if os.path.exists(used_file):
    with open(used_file) as f:
        used = json.load(f)
else:
    used = ["画龙点睛", "胸有成竹", "对牛弹琴"]

# 选一个没用过的
available = [k for k in IDIOMS if k not in used]
if not available:
    print("❌ 所有成语都用过了！")
    sys.exit(1)

idiom = random.choice(available)
data = IDIOMS[idiom]
print(f"🎯 选中: {idiom}")

# 1. 修改 generate.py 配置
import re
with open(SCRIPT, "r") as f:
    content = f.read()

replacements = {
    '^IDIOM = .*': f'IDIOM = "{idiom}"',
    '^PINYIN = .*': f'PINYIN = "{data["pinyin"]}"',
    '^MEANING = .*': f'MEANING = "{data["meaning"]}"',
    '^EXAMPLE_CN = .*': f'EXAMPLE_CN = "{data["example_cn"]}"',
    '^EXAMPLE_EN = .*': f'EXAMPLE_EN = "{data["example_en"]}"',
    '^ILLUSTRATION = .*': f'ILLUSTRATION = "{data["illustration"]}"',
}

for pattern, replacement in replacements.items():
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

with open(SCRIPT, "w") as f:
    f.write(content)
print(f"✅ 脚本已更新为: {idiom}")

# 2. 运行生成
result = subprocess.run(["python3", SCRIPT], capture_output=True, text=True, timeout=600)
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
if result.returncode != 0:
    print(f"❌ 生成失败: {result.stderr[:200]}")
    sys.exit(1)

# 3. 发布到小红书
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
            "content": f"【{idiom}】{data['pinyin']} · {data['example_en'].split('.')[0]}\n\n{data['meaning']}\n\n{data['example_en']}\n\n你学会了吗？评论区用「{idiom}」造个句吧👇",
            "images": [
                "/tmp/xhs_cards/01_cover.jpg",
                "/tmp/xhs_cards/02_meaning.jpg",
                "/tmp/xhs_cards/03_usage.jpg"
            ],
            "tags": ["成语", "双语", "学中文", "LearnChinese", idiom]
        }
    }
}, headers={"Mcp-Session-Id": sid})

pub_result = r.json()
print(f"\n📤 发布结果: {'✅ 成功' if 'result' in pub_result else '❌ 失败'}")
print(json.dumps(pub_result, ensure_ascii=False)[:200])

# 4. 记录已用
used.append(idiom)
with open(used_file, "w") as f:
    json.dump(used, f, ensure_ascii=False)
print(f"📝 已记录: {used}")
