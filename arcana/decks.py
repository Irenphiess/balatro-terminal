"""15 starting decks and 8 cumulative stake difficulties, version 1.0.1o-inspired.
All presets are accessible in this independent sandbox; original unlock gates are not reproduced.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class DeckPreset:
    key: str
    name: str
    desc: str

DECKS = (
 DeckPreset('Red Deck','红色牌组','每轮 +1 次弃牌'),
 DeckPreset('Blue Deck','蓝色牌组','每轮 +1 次出牌'),
 DeckPreset('Yellow Deck','黄色牌组','开局额外 $10'),
 DeckPreset('Green Deck','绿色牌组','剩余出牌 +$2 / 弃牌 +$1，失去利息'),
 DeckPreset('Black Deck','黑色牌组','小丑槽 +1，每轮出牌 -1'),
 DeckPreset('Magic Deck','魔法牌组','开局水晶球优惠券与两张愚者'),
 DeckPreset('Nebula Deck','星云牌组','开局望远镜优惠券，消耗牌槽 -1'),
 DeckPreset('Ghost Deck','幽灵牌组','商店出现幻灵牌，开局拥有妖术'),
 DeckPreset('Abandoned Deck','遗弃牌组','移除 J、Q、K，初始牌组40张'),
 DeckPreset('Checkered Deck','方格牌组','仅含26黑桃与26红心'),
 DeckPreset('Zodiac Deck','黄道牌组','三张商店增强优惠券开局'),
 DeckPreset('Painted Deck','彩绘牌组','手牌上限 +2，小丑槽 -1'),
 DeckPreset('Anaglyph Deck','立体牌组','击败 Boss 后获得双倍跳关标记'),
 DeckPreset('Plasma Deck','等离子牌组','计分平衡筹码与倍率，盲注目标 ×2'),
 DeckPreset('Erratic Deck','错乱牌组','52张随机点数与花色'),
)

STAKES = (
 ('White','白注','标准难度'),
 ('Red','红注','小盲注无奖励'),
 ('Green','绿注','目标分数增长更快'),
 ('Black','黑注','商店小丑可能附带永恒贴纸'),
 ('Blue','蓝注','每轮弃牌 -1'),
 ('Purple','紫注','目标分数增长进一步加速'),
 ('Orange','橙注','小丑可能附带易腐贴纸'),
 ('Gold','金注','小丑可能附带租赁贴纸'),
)
CURVES = (
 (300,800,2000,5000,11000,20000,35000,50000),
 (300,900,2600,8000,20000,36000,60000,100000),
 (300,1000,3200,9000,25000,60000,110000,200000),
)

def stake_index(name):
    for i,(key,_,_) in enumerate(STAKES):
        if key==name:return i
    return 0

def curve(name):
    i=stake_index(name)
    return CURVES[2 if i>=5 else 1 if i>=2 else 0]

MIN_BOSS_ANTE = {
 'The Wall':2,'The Ox':6,'The Arm':2,'The Fish':2,'The Water':2,
 'The Eye':3,'The Mouth':2,'The Plant':4,'The Serpent':5,
 'The Needle':2,'The Tooth':3,'The Flint':2,'The House':2,
 'The Wheel':2,'The Mark':2,
}
