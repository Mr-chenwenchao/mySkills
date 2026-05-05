#!/usr/bin/env python3
"""
小红书评论自动回复 — 每30分钟
搜索自己的成语笔记 → 获取新评论 → AI回复 → 记录已回
"""
import requests, json, os, sys, random, time

MCP_URL = "http://127.0.0.1:18060/mcp"
REPLIED_FILE = "/tmp/xhs_replied_comments.json"
OUR_NAME = "若瑜的成语笔记"

def mcp_init():
    s = requests.Session()
    s.proxies = {"http": "", "https": ""}
    r = s.post(MCP_URL, json={"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"hermes","version":"1.0"}
    }})
    return s, r.headers.get("Mcp-Session-Id", "")

def mcp_call(s, sid, method, args):
    r = s.post(MCP_URL, json={"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
        "name":method,"arguments":args
    }}, headers={"Mcp-Session-Id":sid})
    return r.json()

# 加载已回复记录
replied = set()
if os.path.exists(REPLIED_FILE):
    with open(REPLIED_FILE) as f:
        replied = set(json.load(f))

print(f"📋 已回复 {len(replied)} 条评论")

# 搜索自己的帖子
s, sid = mcp_init()
resp = mcp_call(s, sid, "search_feeds", {"keyword":"若瑜成语","filters":{}})

our_feeds = []
try:
    text = resp.get("result",{}).get("content",[{}])[0].get("text","")
    data = json.loads(text)
    for feed in data.get("feeds", []):
        nc = feed.get("noteCard", {})
        user = nc.get("user", {})
        if user.get("nickname") == OUR_NAME or user.get("nickName") == OUR_NAME:
            our_feeds.append({
                "id": feed["id"],
                "xsec": feed["xsecToken"],
                "title": nc.get("displayTitle",""),
                "comments": int(nc.get("interactInfo",{}).get("commentCount",0))
            })
except Exception as e:
    print(f"⚠️ 解析出错: {e}")

if not our_feeds:
    print("❌ 没找到自己的帖子")
    sys.exit(0)

print(f"📝 找到 {len(our_feeds)} 篇自己的笔记")

replied_this_round = 0
for feed in our_feeds:
    if feed["comments"] == 0:
        continue
    
    # 获取帖子详情和评论
    detail = mcp_call(s, sid, "get_feed_detail", {
        "feed_id": feed["id"],
        "xsec_token": feed["xsec"],
        "load_all_comments": True,
        "limit": 20
    })
    
    # 解析评论
    try:
        detail_text = detail.get("result",{}).get("content",[{}])[0].get("text","")
        detail_data = json.loads(detail_text)
        comments = detail_data.get("comments", [])
    except:
        comments = []
    
    if not comments:
        continue
    
    for c in comments:
        cid = c.get("id", "")
        if not cid or cid in replied:
            continue
        
        content = c.get("content", "")
        user_name = c.get("user", {}).get("nickname", "用户")
        
        # 根据评论内容选回复
        t = content.lower()
        if any(w in t for w in ["好棒","喜欢","有用","收藏","厉害","不错","nice","great","good","棒","赞","❤","👍","😊"]):
            replies = ["谢谢喜欢～每天一个成语，一起进步💪","感谢支持！觉得有用记得收藏哦📌","能帮到你太开心了😊","一起学成语一起涨知识！✨"]
        elif any(w in t for w in ["什么","意思","怎么","why","what","how","为什么","？","?"]):
            replies = ["好问题！多读几遍例句就能理解啦，加油💪","你可以用这个成语造个句试试看？👇"]
        elif any(w in t for w in ["造句","例句","比如"]):
            replies = ["造得好！👍 看来你完全掌握了这个成语🎉","例句很棒，大家快来学！👏"]
        else:
            replies = ["感谢评论～一起学成语！😊","欢迎常来～每天一个双语成语📚","学会了吗？明天还有新的哦✨"]
        
        reply_text = random.choice(replies)
        
        # 回复
        reply_resp = mcp_call(s, sid, "reply_comment_in_feed", {
            "feed_id": feed["id"],
            "xsec_token": feed["xsec"],
            "comment_id": cid,
            "user_id": c.get("user",{}).get("userId",""),
            "content": reply_text
        })
        
        success = "result" in reply_resp
        print(f"  {user_name}: 「{content[:30]}」→ 「{reply_text}」{'✅' if success else '❌'}")
        
        replied.add(cid)
        replied_this_round += 1

# 保存已回复记录
if replied_this_round > 0:
    with open(REPLIED_FILE, "w") as f:
        json.dump(list(replied), f, ensure_ascii=False)
    print(f"\n✅ 本次回复了 {replied_this_round} 条新评论")
else:
    print(f"\n✅ 无新评论")

# 推送到 GitHub
print(f"⏰ {time.strftime('%H:%M:%S')} 检查完成")
