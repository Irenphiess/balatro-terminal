"""Hand-authored game data, for the standalone Balatro terminal adaptation."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Joker:
    name: str
    zh: str
    desc: str
    rarity: str = 'Common'
    cost: int = 4
    status: str = 'active'  # 'active' or 'partial'

# 150 original Joker names, in collection order. Gameplay is an independent implementation.
_NAMES = '''
Joker|Greedy Joker|Lusty Joker|Wrathful Joker|Gluttonous Joker|Jolly Joker|Zany Joker|Mad Joker|Crazy Joker|Droll Joker
Sly Joker|Wily Joker|Clever Joker|Devious Joker|Crafty Joker|Half Joker|Joker Stencil|Four Fingers|Mime|Credit Card
Ceremonial Dagger|Banner|Mystic Summit|Marble Joker|Loyalty Card|8 Ball|Misprint|Dusk|Raised Fist|Chaos the Clown
Fibonacci|Steel Joker|Scary Face|Abstract Joker|Delayed Gratification|Hack|Pareidolia|Gros Michel|Even Steven|Odd Todd
Scholar|Business Card|Supernova|Ride the Bus|Space Joker|Egg|Burglar|Blackboard|Runner|Ice Cream
DNA|Splash|Blue Joker|Sixth Sense|Constellation|Hiker|Faceless Joker|Green Joker|Superposition|To Do List
Cavendish|Card Sharp|Red Card|Madness|Square Joker|Séance|Riff-Raff|Vampire|Shortcut|Hologram
Vagabond|Baron|Cloud 9|Rocket|Obelisk|Midas Mask|Luchador|Photograph|Gift Card|Turtle Bean
Erosion|Reserved Parking|Mail-In Rebate|To the Moon|Hallucination|Fortune Teller|Juggler|Drunkard|Stone Joker|Golden Joker
Lucky Cat|Baseball Card|Bull|Diet Cola|Trading Card|Flash Card|Popcorn|Spare Trousers|Ancient Joker|Ramen
Walkie Talkie|Seltzer|Castle|Smiley Face|Campfire|Golden Ticket|Mr. Bones|Acrobat|Sock and Buskin|Swashbuckler
Troubadour|Certificate|Smeared Joker|Throwback|Hanging Chad|Rough Gem|Bloodstone|Arrowhead|Onyx Agate|Glass Joker
Showman|Flower Pot|Blueprint|Wee Joker|Merry Andy|Oops! All 6s|The Idol|Seeing Double|Matador|Hit the Road
The Duo|The Trio|The Family|The Order|The Tribe|Stuntman|Invisible Joker|Brainstorm|Satellite|Shoot the Moon
Driver's License|Cartomancer|Astronomer|Burnt Joker|Bootstraps|Canio|Triboulet|Yorick|Chicot|Perkeo
'''
NAMES=[x.strip() for line in _NAMES.strip().splitlines() for x in line.strip().split('|')]
assert len(NAMES)==150 and len(set(NAMES))==150, (len(NAMES),len(set(NAMES)))
# Chinese display names in same order as NAMES.
_ZH='''
小丑|贪婪小丑|欲望小丑|愤怒小丑|暴食小丑|欢快小丑|怪诞小丑|狂躁小丑|疯狂小丑|滑稽小丑
狡猾小丑|精明小丑|机灵小丑|诡计小丑|巧手小丑|半张小丑|模板小丑|四指|默剧演员|信用卡
仪式匕首|旗帜|神秘山峰|大理石小丑|忠诚卡|八号球|印刷失误|黄昏|举拳|混沌小丑
斐波那契|钢铁小丑|恐怖面孔|抽象小丑|延迟满足|黑客|脸盲症|大香蕉|偶数史蒂文|奇数托德
学者|商业名片|超新星|乘车|太空小丑|鸡蛋|窃贼|黑板|长跑者|冰淇淋
脱氧核糖核酸|飞溅|蓝色小丑|第六感|星座|登山客|无面小丑|绿色小丑|叠加态|待办事项
卡文迪什|出千高手|红牌|疯狂|方形小丑|降灵会|乌合之众|吸血鬼|捷径|全息影像
流浪汉|男爵|九重云|火箭|方尖碑|迈达斯面具|摔角手|照片|礼品卡|龟豆
侵蚀|停车位|邮寄返现|奔月|幻觉|算命先生|杂耍演员|醉汉|石头小丑|黄金小丑
幸运猫|棒球卡|公牛|无糖可乐|交易卡|闪卡|爆米花|备用裤子|远古小丑|拉面
对讲机|苏打水|城堡|笑脸|篝火|黄金票|骸骨先生|杂技演员|袜子与长靴|侠盗
吟游诗人|证书|涂抹小丑|往事|悬挂的乍得|粗糙宝石|血石|箭头|缟玛瑙|玻璃小丑
表演者|花盆|蓝图|小小丑|快乐安迪|全是六|偶像|双重视觉|斗牛士|上路
二重奏|三重奏|家族|秩序|部族|特技演员|隐形小丑|头脑风暴|卫星|射向月亮
驾照|塔罗师|天文学家|烧焦的小丑|靴带|卡尼奥|特里布莱|约里克|奇科|佩克奥
'''
ZHNAMES=[x.strip() for line in _ZH.strip().splitlines() for x in line.strip().split('|')]
assert len(ZHNAMES)==150
RARITIES={
 'Rare': 'DNA|Vagabond|Baron|Obelisk|Baseball Card|Ancient Joker|Campfire|Blueprint|Wee Joker|Hit the Road|The Duo|The Trio|The Family|The Order|The Tribe|Stuntman|Invisible Joker|Brainstorm|Driver\'s License|Burnt Joker',
 'Legendary':'Canio|Triboulet|Yorick|Chicot|Perkeo',
 'Uncommon':'Joker Stencil|Four Fingers|Mime|Splash|Ceremonial Dagger|Marble Joker|Loyalty Card|Dusk|Fibonacci|Steel Joker|Hack|Pareidolia|Space Joker|Burglar|Blackboard|Sixth Sense|Constellation|Hiker|Card Sharp|Madness|Séance|Vampire|Shortcut|Hologram|Cloud 9|Rocket|Midas Mask|Luchador|Gift Card|Turtle Bean|Erosion|To the Moon|Stone Joker|Lucky Cat|Bull|Diet Cola|Trading Card|Flash Card|Spare Trousers|Ramen|Seltzer|Castle|Mr. Bones|Acrobat|Sock and Buskin|Troubadour|Certificate|Smeared Joker|Throwback|Rough Gem|Bloodstone|Arrowhead|Onyx Agate|Glass Joker|Flower Pot|Merry Andy|Oops! All 6s|The Idol|Seeing Double|Matador|Satellite|Cartomancer|Astronomer|Bootstraps'
}
RARITY={name:rarity for rarity,names in RARITIES.items() for name in names.split('|')}
assert len([n for n in NAMES if RARITY.get(n)=='Rare'])==20
assert len([n for n in NAMES if RARITY.get(n)=='Legendary'])==5
assert len([n for n in NAMES if RARITY.get(n)=='Uncommon'])==64, len([n for n in NAMES if RARITY.get(n)=='Uncommon'])

# English descriptions for compact reference; Chinese name and UI are fully localized.
DESC={
 'Joker':'+4 倍率','Greedy Joker':'计分方块每张 +3 倍率','Lusty Joker':'计分红心每张 +3 倍率','Wrathful Joker':'计分黑桃每张 +3 倍率','Gluttonous Joker':'计分梅花每张 +3 倍率',
 'Jolly Joker':'包含对子 +8 倍率','Zany Joker':'包含三条 +12 倍率','Mad Joker':'包含两对 +10 倍率','Crazy Joker':'包含顺子 +12 倍率','Droll Joker':'包含同花 +10 倍率',
 'Sly Joker':'对子 +50 筹码','Wily Joker':'三条 +100 筹码','Clever Joker':'两对 +80 筹码','Devious Joker':'顺子 +100 筹码','Crafty Joker':'同花 +80 筹码',
 'Half Joker':'出牌≤3张，倍率+20','Joker Stencil':'空余小丑栏提供倍率乘算','Four Fingers':'4张即可形成顺子或同花','Mime':'手持牌效果重复触发','Credit Card':'允许透支至 -$20',
 'Ceremonial Dagger':'开始盲注吞噬右侧小丑','Banner':'每剩一次弃牌 +30 筹码','Mystic Summit':'无弃牌时 +15 倍率','Marble Joker':'开局向牌组加入石头牌','Loyalty Card':'每六次出牌 x4 倍率',
 '8 Ball':'计分8有机会生成塔罗','Misprint':'随机 +0~23 倍率','Dusk':'最后一手重复计分','Raised Fist':'最低手持牌点数 x2 倍率','Chaos the Clown':'每商店首次刷新免费',
 'Fibonacci':'A、2、3、5、8 计分时+8倍率','Steel Joker':'钢铁牌越多倍率越高','Scary Face':'计分人头牌+30筹码','Abstract Joker':'每张小丑 +3 倍率','Delayed Gratification':'未弃牌则回合末获得金钱',
 'Hack':'计分2~5重复触发','Pareidolia':'所有点数视为人头牌','Gros Michel':'倍率+15；有概率损坏','Even Steven':'计分偶数牌+4倍率','Odd Todd':'计分奇数牌+31筹码',
 'Scholar':'计分A +20筹码/+4倍率','Business Card':'计分人头牌有概率获$2','Supernova':'倍率随牌型使用次数增长','Ride the Bus':'不计分人头牌即可持续增长','Space Joker':'概率提升牌型等级',
 'Egg':'每回合增加售价','Burglar':'+3出牌，弃牌归零','Blackboard':'手持牌全黑色时倍率x3','Runner':'打顺子增加长期筹码','Ice Cream':'高筹码逐次衰减',
 'DNA':'首手单牌复制入牌组','Splash':'所有打出的牌都计分','Blue Joker':'剩余抽牌堆每张+2筹码','Sixth Sense':'首手单6可转化为幻灵牌','Constellation':'用星球牌累积倍率',
 'Hiker':'计分牌永久增加筹码','Faceless Joker':'弃掉3张人头牌获$5','Green Joker':'出牌+1倍率，弃牌-1','Superposition':'含A的顺子生成塔罗','To Do List':'打特定牌型得$4',
 'Cavendish':'倍率x3，极小概率消失','Card Sharp':'本回合重复牌型 x3','Red Card':'跳过补充包获得永久倍率','Madness':'选择盲注增加倍率并吞噬小丑','Square Joker':'4张出牌累加筹码',
 'Séance':'同花顺生成幻灵牌','Riff-Raff':'开始盲注生成两张普通小丑','Vampire':'剥离强化换取倍率','Shortcut':'允许间隔1的顺子','Hologram':'加牌可提升倍率',
 'Vagabond':'低资金出牌生成塔罗','Baron':'手持K触发 x1.5 倍率','Cloud 9':'回合末依牌组9数量获得金钱','Rocket':'回合末金钱，Boss后增长','Obelisk':'回避最多使用牌型累积倍率',
 'Midas Mask':'计分人头牌变黄金牌','Luchador':'出售可禁用本轮Boss','Photograph':'第一张人头计分牌 x2','Gift Card':'每回合增加卡牌售价','Turtle Bean':'增加手牌上限但逐轮衰减',
 'Erosion':'牌组小于52时 +4倍率/缺张','Reserved Parking':'手持人头牌可能获$1','Mail-In Rebate':'弃特定点数获得$5','To the Moon':'额外利息','Hallucination':'开包概率生成塔罗',
 'Fortune Teller':'塔罗使用次数越多倍率越高','Juggler':'手牌数+1','Drunkard':'弃牌次数+1','Stone Joker':'石头牌越多筹码越高','Golden Joker':'回合末获得$4',
 'Lucky Cat':'幸运牌触发增加倍率','Baseball Card':'每张非普通小丑倍率x1.5','Bull':'每$1 增加2筹码','Diet Cola':'出售获得双倍跳关标记','Trading Card':'首弃单牌销毁并获$3',
 'Flash Card':'每次商店刷新 +2 倍率','Popcorn':'倍率+20，每轮-4','Spare Trousers':'打两对永久增长倍率','Ancient Joker':'特定花色计分时倍率x1.5','Ramen':'倍率x2，弃牌逐渐减少',
 'Walkie Talkie':'10与4计分加筹码与倍率','Seltzer':'接下来10次出牌重复触发','Castle':'弃指定花色增加筹码','Smiley Face':'人头牌计分+5倍率','Campfire':'出售卡片积累倍率',
 'Golden Ticket':'黄金牌计分获$4','Mr. Bones':'得分达25%可免死一次','Acrobat':'最后一手倍率x3','Sock and Buskin':'人头牌计分重复触发','Swashbuckler':'其他小丑售价转倍率',
 'Troubadour':'手牌+2、出牌-1','Certificate':'开始回合新增带封印牌','Smeared Joker':'红色花色视为同种，黑色同理','Throwback':'跳过盲注提升倍率','Hanging Chad':'第一张计分牌重复两次',
 'Rough Gem':'方块计分获$1','Bloodstone':'红心计分概率x1.5','Arrowhead':'黑桃计分+50筹码','Onyx Agate':'梅花计分+7倍率','Glass Joker':'碎裂玻璃牌增加倍率',
 'Showman':'商店允许重复小丑','Flower Pot':'四花色齐全倍率x3','Blueprint':'复制右侧小丑效果','Wee Joker':'计分2增加永久筹码','Merry Andy':'弃牌+3，手牌-1',
 'Oops! All 6s':'翻倍多数随机概率','The Idol':'随机花色和点数计分 x2','Seeing Double':'梅花+其他花色倍率x2','Matador':'触发Boss限制时获$8','Hit the Road':'弃J永久提高本轮倍率',
 'The Duo':'包含对子倍率x2','The Trio':'包含三条倍率x3','The Family':'包含四条倍率x4','The Order':'包含顺子倍率x3','The Tribe':'包含同花倍率x2',
 'Stuntman':'+250筹码、手牌-2','Invisible Joker':'经过两回合后出售可复制小丑','Brainstorm':'复制最左侧小丑','Satellite':'按使用过的星球种类发钱','Shoot the Moon':'手持Q每张+13倍率',
 "Driver's License":'强化牌≥16张时倍率x3','Cartomancer':'每次选盲注生成塔罗','Astronomer':'星球牌和天体包免费','Burnt Joker':'每回合首次弃牌升级牌型','Bootstraps':'每$5获得+2倍率',
 'Canio':'销毁人头牌增加倍率','Triboulet':'计分K/Q倍率x2','Yorick':'每弃23张牌永久提升倍率','Chicot':'禁用Boss能力','Perkeo':'离店复制一张负片消耗牌'
}

# Most play-affecting names have handlers, including passives and timed actions.
PARTIAL={'The Idol','To Do List','Superposition','Obelisk','Diet Cola','Matador','Showman','Riff-Raff','Red Card','Perkeo','Certificate','Ectoplasm'}
JOKERS=[Joker(n,ZHNAMES[i],DESC.get(n,'特殊小丑能力'),RARITY.get(n,'Common'),(20 if RARITY.get(n)=='Legendary' else 10 if n in ('Blueprint','Brainstorm') else 8 if RARITY.get(n)=='Rare' else 6 if RARITY.get(n)=='Uncommon' else 4), 'partial' if n in PARTIAL else 'active') for i,n in enumerate(NAMES)]
LOOKUP={j.name:j for j in JOKERS}

def zh(name):return LOOKUP[name].zh if name in LOOKUP else name

TAROTS=('The Fool','The Magician','The High Priestess','The Empress','The Emperor','The Hierophant','The Lovers','The Chariot','Justice','The Hermit','The Wheel of Fortune','Strength','The Hanged Man','Death','Temperance','The Devil','The Tower','The Star','The Moon','The Sun','Judgement','The World')
TAROT_ZH=dict(zip(TAROTS,'愚者|魔术师|女祭司|皇后|皇帝|教皇|恋人|战车|正义|隐者|命运之轮|力量|倒吊人|死神|节制|恶魔|高塔|星星|月亮|太阳|审判|世界'.split('|')))
SPECTRALS=('Familiar','Grim','Incantation','Talisman','Aura','Wraith','Sigil','Ouija','Ectoplasm','Immolate','Ankh','Deja Vu','Hex','Trance','Medium','Cryptid','The Soul','Black Hole')
SPECTRAL_ZH=dict(zip(SPECTRALS,'使魔|死神使者|咒语|护符|光环|幽灵|符印|通灵板|灵质|焚祭|安卡|似曾相识|妖术|恍惚|灵媒|隐秘|灵魂|黑洞'.split('|')))
BOSSES={'The Hook':'每次出牌后随机丢弃2张手牌','The Ox':'打出指定牌型时金钱清零','The House':'起始手牌背面朝上','The Wall':'目标翻倍','The Wheel':'部分手牌背面朝上','The Arm':'每次出牌降低该牌型等级','The Club':'梅花牌失效','The Fish':'新抽到的手牌背面朝上','The Psychic':'每手必须出满5张','The Goad':'黑桃牌失效','The Water':'无法弃牌','The Window':'方块牌失效','The Manacle':'手牌数-1','The Eye':'每回合不能重复牌型','The Mouth':'全回合只能使用一种牌型','The Plant':'人头牌失效','The Serpent':'出牌或弃牌后只补3张牌','The Pillar':'已经出过的牌失效','The Needle':'只有一次出牌','The Head':'红心牌失效','The Tooth':'每出一张牌扣$1','The Flint':'基础筹码与倍率减半','The Mark':'人头牌隐藏','Violet Vessel':'目标6倍','Crimson Heart':'每手随机一张小丑失效','Amber Acorn':'开局乱序小丑','Verdant Leaf':'出售一张小丑前所有牌失效','Cerulean Bell':'每手强制选择一张牌'}
BOSS_ZH=dict(zip(BOSSES,'钩子|公牛|房屋|高墙|车轮|手臂|梅花|鱼儿|灵媒|荆棘|水域|窗户|镣铐|眼睛|嘴巴|植物|巨蛇|石柱|针尖|红心|利齿|燧石|面具|紫色容器|猩红之心|琥珀橡实|翠绿叶片|蔚蓝铃铛'.split('|')))
VOUCHER_PAIRS=[
 ('Overstock','Overstock Plus','增加商店商品栏位'),('Clearance Sale','Liquidation','商店折扣'),('Hone','Glow Up','提高特殊版本概率'),('Reroll Surplus','Reroll Glut','减少刷新费用'),('Crystal Ball','Omen Globe','增加消耗牌槽 / 奥秘包混入幻灵'),('Telescope','Observatory','天体包优先最常用牌型 / 手持星球增倍率'),('Grabber','Nacho Tong','增加每轮出牌次数'),('Wasteful','Recyclomancy','增加弃牌次数'),('Tarot Merchant','Tarot Tycoon','提高塔罗出现率'),('Planet Merchant','Planet Tycoon','提高星球出现率'),('Seed Money','Money Tree','提高利息上限'),('Blank','Antimatter','提升小丑槽位'),('Magic Trick','Illusion','商店可出售普通扑克牌'),('Hieroglyph','Petroglyph','降低 Ante 和每轮操作次数'),("Director's Cut",'Retcon','允许重掷 Boss'),('Paint Brush','Palette','提升手牌上限')]
VOUCHERS={n:{'tier':i,'pair':a if i else b,'desc':d,'zh':(f'{d}·高级' if i else d)} for a,b,d in VOUCHER_PAIRS for i,n in enumerate((a,b))}
PACK_KINDS={'Arcana':'奥秘包','Celestial':'天体包','Spectral':'幻灵包','Standard':'标准包','Buffoon':'小丑包'}
PACK_CONFIG={'Arcana':(3,5),'Celestial':(3,5),'Spectral':(2,4),'Standard':(3,5),'Buffoon':(2,4)}
PACK_SIZES={'Normal':(4,1),'Jumbo':(6,1),'Mega':(8,2)}
