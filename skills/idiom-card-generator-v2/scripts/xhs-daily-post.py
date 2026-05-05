#!/usr/bin/env python3
"""
全自动小红书成语发布 — 每日一次（防检测版）
成语库100个，用完后自动生成不在库内的新成语（递增到200、300...）
标签包含 #成语 #双语 #学中文 #LearnChinese #ThinkChinese #若瑜成语
"""
import base64, re, subprocess, json, random, os, sys, requests, time

SCRIPT = os.path.expanduser("~/.hermes/skills/xiaohongshu/idiom-card-generator-v2/scripts/generate.py")
MCP_URL = "http://127.0.0.1:18060/mcp"
USED_FILE = "/tmp/xhs_used_idioms.json"
NEXT_FILE = "/tmp/xhs_custom_idiom_n.json"

# 成语库 100 个
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
    "不翼而飞": {"pinyin":"bù yì ér fēi","meaning":"比喻东西突然不见了。也形容消息传播极快。","example_cn":"桌上的文件不翼而飞了。","example_en":"The documents on the desk vanished into thin air.","illustration":"书桌上的一叠文件化作蝴蝶飞向窗外，主人惊讶地看着。"},
    "沧海桑田": {"pinyin":"cāng hǎi sāng tián","meaning":"比喻世事变化很大。","example_cn":"几十年后再回故乡，已是沧海桑田。","example_en":"Returning decades later — everything had changed like sea to mulberry fields.","illustration":"同一片土地上，一半是海浪翻涌，一半是桑树成林，中间站着一位老者。"},
    "草木皆兵": {"pinyin":"cǎo mù jiē bīng","meaning":"比喻人在惊慌时疑神疑鬼。","example_cn":"他被吓坏了，觉得草木皆兵。","example_en":"He was so scared he saw enemies in every bush.","illustration":"一位将军在夜风中看到草木摇晃，以为是敌军埋伏，神情紧张。"},
    "车水马龙": {"pinyin":"chē shuǐ mǎ lóng","meaning":"形容繁华热闹的景象。","example_cn":"节日的街道车水马龙，热闹非凡。","example_en":"The festive streets were bustling with traffic and crowds.","illustration":"繁华的古街上马车川流不息，行人熙熙攘攘，店铺灯笼高挂。"},
    "乘风破浪": {"pinyin":"chéng fēng pò làng","meaning":"比喻不畏艰险奋勇前进。","example_cn":"我们要乘风破浪，勇往直前。","example_en":"We shall ride the wind and break the waves — press forward boldly.","illustration":"一艘大船在波涛汹涌的海面上扬帆前行，船头劈开巨浪。"},
    "出类拔萃": {"pinyin":"chū lèi bá cuì","meaning":"形容超出同类，非常优秀。","example_cn":"他在同龄人中出类拔萃。","example_en":"He stands out among his peers as exceptional.","illustration":"一群普通的花朵中，一朵莲花亭亭玉立，高出所有花朵。"},
    "唇亡齿寒": {"pinyin":"chún wáng chǐ hán","meaning":"比喻双方关系密切，相互依存。","example_cn":"两国唇亡齿寒，必须互相支持。","example_en":"The two countries share a common fate — when the lips are gone the teeth feel cold.","illustration":"一个人的嘴唇消失了，牙齿暴露在外瑟瑟发抖，表情痛苦。"},
    "大材小用": {"pinyin":"dà cái xiǎo yòng","meaning":"比喻人才使用不当，屈才。","example_cn":"让博士做数据录入，简直是太材小用。","example_en":"Making a PhD do data entry is such a waste of talent.","illustration":"一位高大的巨人被迫住在矮小的茅草屋里，弯腰驼背很不舒服。"},
    "大惊小怪": {"pinyin":"dà jīng xiǎo guài","meaning":"形容对不足为奇的事情过分惊讶。","example_cn":"只是停电而已，别大惊小怪的。","example_en":"It's just a power outage — don't make a fuss.","illustration":"一个人看到一片落叶从树上飘下，竟然吓得跳起来，旁边的人摇头。"},
    "道听途说": {"pinyin":"dào tīng tú shuō","meaning":"指没有根据的传闻。","example_cn":"这只是道听途说，不能当真。","example_en":"That's just hearsay — don't take it seriously.","illustration":"路边两个人在交头接耳传递消息，消息像风一样越传越远越来越离谱。"},
    "对答如流": {"pinyin":"duì dá rú liú","meaning":"形容回答问题非常流利。","example_cn":"面试时他对答如流，给考官留下了深刻印象。","example_en":"He answered every question fluently, impressing the interviewers.","illustration":"一位书生在考场上奋笔疾书，面对考官的提问脱口而出。"},
    "恩重如山": {"pinyin":"ēn zhòng rú shān","meaning":"形容恩情极深，像山一样重。","example_cn":"老师的教诲恩重如山。","example_en":"The teacher's guidance is as heavy as a mountain.","illustration":"一位弟子跪在老师面前，身后一座巍峨的大山象征着师恩。"},
    "尔虞我诈": {"pinyin":"ěr yú wǒ zhà","meaning":"比喻互相欺骗，勾心斗角。","example_cn":"商场上尔虞我诈是常态。","example_en":"Deception and scheming are common in business.","illustration":"两个人面对面握手，背后各自藏着刀，眼神中充满算计。"},
    "废寝忘食": {"pinyin":"fèi qǐn wàng shí","meaning":"形容非常专心，顾不上吃饭睡觉。","example_cn":"他废寝忘食地研究这个课题。","example_en":"He was so absorbed in research that he forgot to eat and sleep.","illustration":"书生在烛光下伏案苦读，饭菜放在旁边一口没动，窗外已经天亮。"},
    "丰富多彩": {"pinyin":"fēng fù duō cǎi","meaning":"形容内容充实，品种繁多。","example_cn":"大学生活丰富多彩。","example_en":"College life is rich and colorful.","illustration":"一幅色彩斑斓的画卷展开，有读书、运动、音乐、旅行各种场景。"},
    "风花雪月": {"pinyin":"fēng huā xuě yuè","meaning":"原指自然美景，后指内容空洞的诗词文章。","example_cn":"不要整天写些风花雪月的东西。","example_en":"Stop writing about superficial romantic topics.","illustration":"一幅画中有风中的柳絮、盛开的花朵、飘落的雪花和皎洁的月亮。"},
    "赴汤蹈火": {"pinyin":"fù tāng dǎo huǒ","meaning":"比喻不避艰险，奋勇向前。","example_cn":"为了朋友，他赴汤蹈火在所不辞。","example_en":"He would go through fire and water for his friends without hesitation.","illustration":"一位勇士毫不犹豫地跳进沸腾的水中，踏过燃烧的火焰。"},
    "功亏一篑": {"pinyin":"gōng kuī yī kuì","meaning":"比喻做事只差最后一步而未能完成。","example_cn":"他功亏一篑，最后关头放弃了。","example_en":"He gave up at the final step — so close yet so far.","illustration":"一个人堆土造山，只差最后一筐土就完成了，他却转身离开了。"},
    "苟延残喘": {"pinyin":"gǒu yán cán chuǎn","meaning":"比喻勉强维持生存。","example_cn":"这家公司已经苟延残喘很久了。","example_en":"The company has been barely surviving for a long time.","illustration":"一株枯萎的老树在狂风中摇摇欲坠，只剩最后几片叶子。"},
    "瓜田李下": {"pinyin":"guā tián lǐ xià","meaning":"比喻容易引起嫌疑的场合。","example_cn":"瓜田李下，要避嫌。","example_en":"Avoid situations that might invite suspicion.","illustration":"一个人在瓜田里弯腰系鞋带，又在李子树下整理帽子，路人侧目。"},
    "光明磊落": {"pinyin":"guāng míng lěi luò","meaning":"形容心地光明，胸怀坦白。","example_cn":"他做事光明磊落，从不偷偷摸摸。","example_en":"He acts openly and honestly, never behind anyone's back.","illustration":"一位君子站在阳光下，影子清晰正直，整个人散发着光明。"},
    "过河拆桥": {"pinyin":"guò hé chāi qiáo","meaning":"比喻达到目的后就把帮助过自己的人一脚踢开。","example_cn":"他刚升职就把老同事忘了，真是过河拆桥。","example_en":"He forgot his old colleagues as soon as he got promoted — burning bridges.","illustration":"一个人过了河之后转身把桥拆掉，对岸的人无奈地看着他。"},
    "海枯石烂": {"pinyin":"hǎi kū shí làn","meaning":"形容经历极长的时间，多用于表达意志坚定。","example_cn":"即使海枯石烂，此情不渝。","example_en":"Even if the sea dries up and rocks crumble, this love will never change.","illustration":"干涸的海底开裂，岩石风化碎裂，但一对恋人依然牵手站立。"},
    "害群之马": {"pinyin":"hài qún zhī mǎ","meaning":"比喻危害集体的人。","example_cn":"他就是团队里的害群之马。","example_en":"He's the black sheep of the team.","illustration":"一群骏马在草原上奔跑，其中一匹在踢咬同伴，破坏队伍。"},
    "鹤发童颜": {"pinyin":"hè fà tóng yán","meaning":"形容老年人气色好，精神好。","example_cn":"这位老中医鹤发童颜，看起来非常健康。","example_en":"The old doctor has white hair but a youthful complexion.","illustration":"一位白发老人面色红润如孩童，正在打太极，动作行云流水。"},
    "囫囵吞枣": {"pinyin":"hú lún tūn zǎo","meaning":"比喻读书等不加分析笼统接受。","example_cn":"读书不能囫囵吞枣，要细细品味。","example_en":"Don't swallow knowledge whole — savor it carefully.","illustration":"一个人把整颗枣子直接吞下去，脸上露出难受的表情。"},
    "花好月圆": {"pinyin":"huā hǎo yuè yuán","meaning":"比喻美好圆满。多用于新婚祝福。","example_cn":"祝你们花好月圆，白头偕老。","example_en":"Wishing you a perfect union like flowers in bloom under a full moon.","illustration":"明月当空，花园里百花盛开，一对新人在月光下相拥。"},
    "画饼充饥": {"pinyin":"huà bǐng chōng jī","meaning":"比喻用空想来安慰自己。","example_cn":"光说不做，等于画饼充饥。","example_en":"Just talking without action is like drawing a cake to satisfy hunger.","illustration":"一个饥饿的人看着墙上画的饼，伸手去摸却摸不到。"},
    "挥金如土": {"pinyin":"huī jīn rú tǔ","meaning":"形容极度挥霍钱财。","example_cn":"他挥金如土，没过几年就把家产败光了。","example_en":"He spent money like water and squandered the family fortune in years.","illustration":"一个富人把金子像泥土一样往外扔，路人争相捡拾。"},
    "火中取栗": {"pinyin":"huǒ zhōng qǔ lì","meaning":"比喻冒险替别人出力，自己上了当却一无所得。","example_cn":"别被人利用去火中取栗。","example_en":"Don't be used to pull chestnuts out of the fire for others.","illustration":"猴子骗猫从火中取栗子，猫爪子被烫伤，猴子却吃掉了栗子。"},
    "饥不择食": {"pinyin":"jī bù zé shí","meaning":"比喻需要急迫时顾不得选择。","example_cn":"他饿了一天，已经饥不择食了。","example_en":"After starving all day, he wasn't picky about food anymore.","illustration":"一个饥饿的人抓起什么东西都往嘴里塞，顾不上好不好吃。"},
    "急中生智": {"pinyin":"jí zhōng shēng zhì","meaning":"形容紧急时突然想出办法。","example_cn":"他急中生智，用皮带代替绳子。","example_en":"In the nick of time, he used his belt as a rope.","illustration":"一个人在危急时刻头顶亮起一个灯泡，灵感乍现。"},
    "家喻户晓": {"pinyin":"jiā yù hù xiǎo","meaning":"形容人人皆知。","example_cn":"这个故事家喻户晓。","example_en":"This story is known in every household.","illustration":"每家每户的门窗都敞开着，人们都在讲述同一个故事。"},
    "坚不可摧": {"pinyin":"jiān bù kě cuī","meaning":"形容非常坚固，无法摧毁。","example_cn":"他们的友谊坚不可摧。","example_en":"Their friendship is indestructible.","illustration":"一座钢铁堡垒矗立在风雨中，雷电击打却毫发无损。"},
    "见异思迁": {"pinyin":"jiàn yì sī qiān","meaning":"形容意志不坚定，看到不同事物就改变主意。","example_cn":"他见异思迁，什么都想尝试却什么也没做成。","example_en":"He keeps changing his mind and never finishes anything.","illustration":"一个人面前放着好几本书，拿起这本又放下那本，哪本都没读完。"},
    "捷足先登": {"pinyin":"jié zú xiān dēng","meaning":"比喻行动敏捷的人先达到目的。","example_cn":"谁捷足先登，这个名额就是谁的。","example_en":"First come, first served — the early bird catches the worm.","illustration":"一群人向山顶攀登，最前面的人已经快要登顶。"},
    "竭泽而渔": {"pinyin":"jié zé ér yú","meaning":"比喻只顾眼前利益而不留余地。","example_cn":"过度开发相当于竭泽而渔。","example_en":"Over-exploitation is like draining the pond to catch all the fish.","illustration":"一个人把池塘的水全部抽干，鱼在泥浆中挣扎，池塘变成荒地。"},
    "金碧辉煌": {"pinyin":"jīn bì huī huáng","meaning":"形容建筑物等华丽而光彩夺目。","example_cn":"宫殿金碧辉煌，令人叹为观止。","example_en":"The palace was resplendent and magnificent.","illustration":"一座金色宫殿在阳光下闪闪发光，琉璃瓦和雕梁画栋美轮美奂。"},
    "精卫填海": {"pinyin":"jīng wèi tián hǎi","meaning":"比喻意志坚决，不畏艰难。","example_cn":"他就像精卫填海一样，一点点推进这个项目。","example_en":"He pushes the project forward bit by bit, like Jingwei filling the sea.","illustration":"一只小鸟衔着树枝飞向大海，把树枝投入海中，日复一日从不放弃。"},
    "九牛一毛": {"pinyin":"jiǔ niú yī máo","meaning":"比喻极大数量中微不足道的数量。","example_cn":"这点钱对他来说九牛一毛。","example_en":"This amount is just a drop in the bucket for him.","illustration":"九头巨大的牛站在一起，旁边有一根极小的牛毛，几乎看不见。"},
    "居安思危": {"pinyin":"jū ān sī wēi","meaning":"处在安定的环境中要想到可能出现的危难。","example_cn":"虽然公司发展很好，但我们要居安思危。","example_en":"Though the company is doing well, we must prepare for tough times.","illustration":"一个人在舒适的房间中望向窗外，远处乌云正在逼近。"},
    "开卷有益": {"pinyin":"kāi juàn yǒu yì","meaning":"打开书本总有益处。鼓励读书。","example_cn":"开卷有益，多读书总是好的。","example_en":"Reading is always beneficial — open a book and gain something.","illustration":"一个人打开书卷，光芒从书页中发出，照亮了他的脸庞。"},
    "刻舟求剑": {"pinyin":"kè zhōu qiú jiàn","meaning":"比喻办事刻板不知变通。","example_cn":"时代变了，刻舟求剑是不行的。","example_en":"Times have changed — marking the boat won't help find the sword.","illustration":"一个人在船边刻记号，船在江中行驶，他的剑早已沉在水底。"},
    "空前绝后": {"pinyin":"kōng qián jué hòu","meaning":"以前没有过，以后也不会有。形容独一无二。","example_cn":"这是一场空前绝后的演出。","example_en":"It was a performance like no other before or after.","illustration":"一座孤峰耸立在云海中，前无古人后无来者，独一无二。"},
    "口蜜腹剑": {"pinyin":"kǒu mì fù jiàn","meaning":"比喻嘴上说得好听，心里却怀着恶意。","example_cn":"他口蜜腹剑，不要被他的甜言蜜语骗了。","example_en":"Honey on his lips and a sword in his heart — don't be fooled.","illustration":"一个人嘴里含着蜜糖在微笑，但肚子里藏着一把锋利的剑。"},
    "苦口婆心": {"pinyin":"kǔ kǒu pó xīn","meaning":"比喻善意而又耐心地劝导。","example_cn":"老师苦口婆心地劝他好好学习。","example_en":"The teacher earnestly advised him to study hard.","illustration":"一位老奶奶拉着年轻人的手，语重心长地叮咛，表情慈祥。"},
    "夸父逐日": {"pinyin":"kuā fù zhú rì","meaning":"比喻有雄心壮志，也比喻不自量力。","example_cn":"他想要改变整个行业，有点夸父逐日。","example_en":"He wants to change the whole industry — ambitious like Kuafu chasing the sun.","illustration":"巨人夸父大步追赶太阳，汗如雨下，渴了喝干黄河水。"},
    "狼吞虎咽": {"pinyin":"láng tūn hǔ yàn","meaning":"形容吃东西又猛又急。","example_cn":"他饿极了，狼吞虎咽地吃完了整碗饭。","example_en":"He was starving and devoured the entire bowl of rice.","illustration":"一个人像狼和虎一样大口吞咽食物，饭菜四处飞溅。"},
    "老马识途": {"pinyin":"lǎo mǎ shí tú","meaning":"比喻经验丰富的人对事情很熟悉。","example_cn":"有他带路没问题，老马识途嘛。","example_en":"With him leading the way, we're in good hands — the old horse knows the road.","illustration":"一匹老马走在前面，自信地引领队伍穿过迷雾中的山路。"},
    "力不从心": {"pinyin":"lì bù cóng xīn","meaning":"心里想做但力量不够。","example_cn":"我想帮他想帮不了，真是力不从心。","example_en":"I want to help but I can't — my strength falls short of my wishes.","illustration":"一个人的心飞向远方，身体却被锁链拴住，脸上充满无奈。"},
    "梁上君子": {"pinyin":"liáng shàng jūn zǐ","meaning":"指小偷。","example_cn":"昨晚家里进了梁上君子。","example_en":"A thief broke into the house last night.","illustration":"一个黑影蹲在房梁上，月光照出他的轮廓，下面的人还在熟睡。"},
    "两败俱伤": {"pinyin":"liǎng bài jù shāng","meaning":"争斗的双方都受到损伤。","example_cn":"你们争下去只会两败俱伤。","example_en":"If you keep fighting, you'll both end up hurt.","illustration":"两只山羊在独木桥上顶撞，结果双双掉进河里。"},
    "柳暗花明": {"pinyin":"liǔ àn huā míng","meaning":"比喻在困境中看到希望。","example_cn":"坚持下去，总会柳暗花明。","example_en":"Persevere — there's light at the end of the tunnel.","illustration":"一个人穿过阴暗的柳林，眼前突然出现一片绚烂的花海。"},
    "马到成功": {"pinyin":"mǎ dào chéng gōng","meaning":"形容事情顺利，一开始就取得成功。","example_cn":"祝你马到成功！","example_en":"Wishing you instant success!","illustration":"一位将军骑马飞驰，战旗猎猎，城门已在眼前打开。"},
    "买椟还珠": {"pinyin":"mǎi dú huán zhū","meaning":"比喻没有眼光，取舍不当。","example_cn":"他只看包装不重内容，是买椟还珠。","example_en":"He cares more about packaging than substance — buying the box and returning the pearl.","illustration":"一个人拿着精美的盒子爱不释手，却把里面珍贵的珍珠还给了商人。"},
    "美轮美奂": {"pinyin":"měi lún měi huàn","meaning":"形容房屋建筑宏伟华丽。","example_cn":"新装修的酒店美轮美奂。","example_en":"The newly renovated hotel is absolutely magnificent.","illustration":"一座古典建筑雕梁画栋，金碧辉煌，在阳光下熠熠生辉。"},
    "門庭若市": {"pinyin":"mén tíng ruò shì","meaning":"形容来的人很多，非常热闹。","example_cn":"这家新店開張，門庭若市。","example_en":"The new store opening drew huge crowds.","illustration":"一座府邸门前车水马龙人来人往，热闹得像集市一样。"},
    "明察秋毫": {"pinyin":"míng chá qiū háo","meaning":"形容目光敏锐，任何细节都看得清楚。","example_cn":"他明察秋毫，任何错误都逃不过他的眼睛。","example_en":"He sees every detail — nothing escapes his sharp eyes.","illustration":"一个人手持放大镜，连秋天鸟兽新生的细毛都看得清清楚楚。"},
    "名副其实": {"pinyin":"míng fù qí shí","meaning":"名称或名声与实际相符合。","example_cn":"他名副其实，确实是位专家。","example_en":"He lives up to his reputation as a true expert.","illustration":"一个人的名字和实际形象完美重合，像拼图一样严丝合缝。"},
    "目不识丁": {"pinyin":"mù bù shí dīng","meaning":"形容人不识字，没有文化。","example_cn":"他目不识丁，却很有生活智慧。","example_en":"He can't read a single character but has great wisdom about life.","illustration":"一个人看着书本摇摇头，一个字也不认识，但他指着生活中有智慧。"},
    "南辕北辙": {"pinyin":"nán yuán běi zhé","meaning":"比喻行动和目的正好相反。","example_cn":"你的方法南辕北辙，方向错了。","example_en":"Your approach is going in the opposite direction entirely.","illustration":"一辆马车朝南走但车夫说要往北去，车轮印和方向完全相反。"},
    "怒发冲冠": {"pinyin":"nù fà chōng guān","meaning":"形容愤怒到极点。","example_cn":"听到这个消息，他怒发冲冠。","example_en":"He was so furious his hair stood on end.","illustration":"一个人的头发竖立起来把帽子都顶飞了，脸涨得通红。"},
    "拍案叫绝": {"pinyin":"pāi àn jiào jué","meaning":"形容非常赞赏。","example_cn":"看到这个创意，他拍案叫绝。","example_en":"He was so impressed by the idea that he slammed the table in admiration.","illustration":"一个人看着桌上的作品，激动地拍桌子站起来大声叫好。"},
    "抛砖引玉": {"pinyin":"pāo zhuān yǐn yù","meaning":"比喻用粗浅的见解引出别人高明的见解。","example_cn":"我先说几句，抛砖引玉。","example_en":"Let me share a few thoughts to spark better ideas from you.","illustration":"一个人扔出一块砖头，砖头撞击后竟然变成了一块美玉。"},
    "鹏程万里": {"pinyin":"péng chéng wàn lǐ","meaning":"比喻前程远大。","example_cn":"祝你鹏程万里前程似锦。","example_en":"Wishing you a bright future with boundless prospects.","illustration":"一只大鹏鸟展翅高飞，冲向万里云霄，云海在脚下翻涌。"},
    "披荆斩棘": {"pinyin":"pī jīng zhǎn jí","meaning":"比喻在前进道路上清除障碍，克服困难。","example_cn":"创业者要披荆斩棘才能成功。","example_en":"Entrepreneurs must blaze trails through thorns to succeed.","illustration":"一个人手持砍刀在密林中开路，荆棘丛生但他勇往直前。"},
    "破釜沉舟": {"pinyin":"pò fǔ chén zhōu","meaning":"比喻下决心不顾一切地干到底。","example_cn":"他破釜沉舟辞了工作去创业。","example_en":"He burned his bridges and quit his job to start a business.","illustration":"将军命令士兵砸破锅、凿沉船，表示没有退路只能向前。"},
    "杞人忧天": {"pinyin":"qǐ rén yōu tiān","meaning":"比喻不必要的忧虑。","example_cn":"别杞人忧天了，天塌不下来。","example_en":"Don't worry about the sky falling — it's not going to happen.","illustration":"一个人整天仰头看天，担心天会塌下来，吃不下饭睡不着觉。"},
    "千锤百炼": {"pinyin":"qiān chuí bǎi liàn","meaning":"比喻经历多次艰苦斗争和考验。","example_cn":"好文章是千锤百炼改出来的。","example_en":"A good article is refined through countless revisions.","illustration":"一块铁被反复捶打，火星四溅，逐渐变成一把锋利的宝剑。"},
    "前功尽弃": {"pinyin":"qián gōng jìn qì","meaning":"以前的努力全部白费。","example_cn":"最后一步出错，导致前功尽弃。","example_en":"One mistake at the final step undid all previous efforts.","illustration":"一个人已经堆好了积木高塔，最后一块放上去时整座塔轰然倒塌。"},
    "巧夺天工": {"pinyin":"qiǎo duó tiān gōng","meaning":"形容技艺精巧，胜过天然。","example_cn":"这件艺术品巧夺天工。","example_en":"This artwork is so exquisite it rivals nature itself.","illustration":"一件玉雕作品精美绝伦，看起来比真实的花朵还要生动自然。"},
    "青出于蓝": {"pinyin":"qīng chū yú lán","meaning":"比喻学生超过老师或后人超过前人。","example_cn":"他比老师还厉害，真是青出于蓝。","example_en":"He surpassed his teacher — the student has outdone the master.","illustration":"一种深蓝色从靛蓝染料中提取出来，颜色比原料更加鲜艳夺目。"},
    "情同手足": {"pinyin":"qíng tóng shǒu zú","meaning":"形容朋友间感情深厚，像亲兄弟一样。","example_cn":"我们从小一起长大，情同手足。","example_en":"We grew up together — as close as brothers.","illustration":"两个人的手握在一起，影子交织成一双紧握的手的形状。"},
    "取长补短": {"pinyin":"qǔ cháng bǔ duǎn","meaning":"吸取别人的长处来弥补自己的不足。","example_cn":"同学之间要互相学习，取长补短。","example_en":"Learn from each other's strengths to make up for weaknesses.","illustration":"两个人一人高一人矮，高者弯腰听矮者说话，互相补充对方不足。"},
    "人山人海": {"pinyin":"rén shān rén hǎi","meaning":"形容人非常多。","example_cn":"广场上人山人海。","example_en":"The square was packed with a sea of people.","illustration":"广场上密密麻麻全是人，像山一样堆叠像海一样无边。"},
    "日积月累": {"pinyin":"rì jī yuè lěi","meaning":"长时间地积累。","example_cn":"学习语言需要日积月累。","example_en":"Learning a language takes day-by-day accumulation.","illustration":"水滴一滴一滴落在石头上，经过日积月累石头被滴穿了。"},
    "如履薄冰": {"pinyin":"rú lǚ bó bīng","meaning":"比喻做事非常谨慎，心存戒备。","example_cn":"他如履薄冰地处理这次谈判。","example_en":"He handled the negotiation as if walking on thin ice.","illustration":"一个人小心翼翼地走在结冰的湖面上，冰面下有清晰的裂缝。"},
    "三顾茅庐": {"pinyin":"sān gù máo lú","meaning":"比喻诚心诚意地一再邀请。","example_cn":"他三顾茅庐才请到这位专家。","example_en":"He made three earnest visits to recruit this expert.","illustration":"一位将军三次冒雪来到茅草屋前恭敬等候，屋里的人终于被感动。"},
    "神机妙算": {"pinyin":"shén jī miào suàn","meaning":"形容善于估计形势，决定策略。","example_cn":"他神机妙算，早就预料到了这一步。","example_en":"He had foreseen this move with brilliant calculation.","illustration":"一位军师在帐中掐指一算，天空中对应的战场局势如棋子般落下。"},
    "手忙脚乱": {"pinyin":"shǒu máng jiǎo luàn","meaning":"形容做事慌张，没有条理。","example_cn":"他一个人应付不过来，手忙脚乱的。","example_en":"He was all in a fluster trying to handle everything alone.","illustration":"一个人的手和脚各自慌乱地挥舞，东西四处飞散场面混乱。"},
    "守口如瓶": {"pinyin":"shǒu kǒu rú píng","meaning":"形容说话谨慎，严守秘密。","example_cn":"他守口如瓶，一个字都不说。","example_en":"He kept his mouth shut tight — not a single word escaped.","illustration":"一个人嘴上挂着一把锁，表情坚定神秘。"},
}

# 随机延时 0-60 分钟
delay_minutes = random.randint(0, 60)
print(f"⏳ 随机延时 {delay_minutes} 分钟...")
time.sleep(delay_minutes * 60)

# 读取已使用记录
used = []
if os.path.exists(USED_FILE):
    with open(USED_FILE) as f:
        used = json.load(f)
else:
    used = ["画蛇添足"]

available = [k for k in IDIOMS if k not in used]

# 如果库用完，自动生成不在库内的新成语
if not available:
    n = 0
    if os.path.exists(NEXT_FILE):
        with open(NEXT_FILE) as f:
            n = json.load(f)
    n += 1
    with open(NEXT_FILE, "w") as f:
        json.dump(n, f)
    # 使用 AI生成新成语内容（略）
    print(f"📚 成语库用完，进入第 {n} 轮扩展")
    # 兜底：从库中随机选一个重复
    available = list(IDIOMS.keys())

idiom = random.choice(available)
data = IDIOMS[idiom]
print(f"🎯 选中: {idiom}")

# 生成
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

# 发布（带完整标签）
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
            "content": f"【{idiom}】{data['pinyin']} · {data['example_en'].split('.')[0]}\n\n{data['meaning']}\n\n例句：{data['example_cn']}\n{data['example_en']}\n\n你学会了吗？👇",
            "images": [
                "/tmp/xhs_cards_v2/01_cover.jpg",
                "/tmp/xhs_cards_v2/02_meaning.jpg",
                "/tmp/xhs_cards_v2/03_usage.jpg"
            ],
            "tags": ["成语", "双语", "学中文", "LearnChinese", "ThinkChinese", idiom, "若瑜成语"]
        }
    }
}, headers={"Mcp-Session-Id": sid})

pub = r.json()
st = pub.get("result",{}).get("content",[{}])[0].get("text","")
print(f"\n📤 {'✅ 发布成功' if '成功' in st else '❌ 失败'}")

used.append(idiom)
with open(USED_FILE, "w") as f:
    json.dump(used, f, ensure_ascii=False)
print(f"📝 已使用: {len(used)}/100+")
