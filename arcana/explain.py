"""Chinese explanations, keyed to the current game data and scoring order."""
from __future__ import annotations
from .content import LOOKUP,TAROT_ZH,SPECTRAL_ZH,VOUCHERS,PACK_KINDS,TAROTS,SPECTRALS,JOKERS
from .poker import HANDS,HAND_ZH,PLANET_ZH
from .tui import ENH,ED,SEAL,RU  # constants only; UI imports this lazily

ENH_DETAIL={
 'Bonus':('额外筹码','打出并参与计分时，增加 30 筹码。','相加型筹码加成，不会直接乘倍率。'),
 'Mult':('额外倍率','打出并参与计分时，增加 4 倍率。','在后续乘算型 Joker 生效前累积通常更有价值。'),
 'Wild':('万能花色','判定同花时可以充当任意花色。','不会改变显示花色；与某些按花色加成的小丑存在差异。'),
 'Glass':('玻璃牌','打出并参与计分时，当前倍率 ×2；计分后有 1/4 概率碎裂。','碎裂后会永久从牌组移除；重触发可能造成更多乘算。'),
 'Steel':('钢铁牌','留在手中、未被打出时，当前倍率 ×1.5。','打出钢铁牌不会触发它的钢铁倍率。'),
 'Gold':('黄金牌','本轮结束时，留在手里的黄金牌会产生金币。','黄金牌的收益来自持有，不是直接增加出牌分数。'),
 'Lucky':('幸运牌','计分时有 1/5 概率 +20 倍率、1/15 概率获得 $20。','两个概率独立；每次重复触发也可能再次掷骰。'),
 'Stone':('石头牌','参与计分时 +50 筹码，不具有正常点数或花色。','在计分引擎中，即使不参与牌型组合也会贡献石头筹码。'),
}
ED_DETAIL={'Foil':'计分时增加 50 筹码。','Holographic':'计分时增加 10 倍率。','Polychrome':'计分时使当前倍率 ×1.5。','Negative':'小丑牌的负片版本不消耗常规小丑槽位。'}
SEAL_DETAIL={'Red':'该牌的计分或手持效果额外触发一次。','Gold':'打出并计分时给予金币。','Blue':'通常于回合结束时产生与牌型相关的星球牌。','Purple':'弃置时通常产生塔罗牌。'}
TAROT_DETAIL={
 'The Fool':'复制本局上一次使用的塔罗或星球牌（不能复制愚者本身）。',
 'The Magician':'选择最多两张手牌，将它们强化为幸运牌。',
 'The High Priestess':'尝试生成最多两张随机星球牌，受消耗牌容量限制。',
 'The Empress':'选择最多两张手牌，赋予额外倍率强化。',
 'The Emperor':'尝试生成最多两张随机塔罗牌，受消耗牌容量限制。',
 'The Hierophant':'选择最多两张手牌，赋予额外筹码强化。',
 'The Lovers':'选择一张手牌，变为万能花色牌。',
 'The Chariot':'选择一张手牌，变为钢铁牌。',
 'Justice':'选择一张手牌，变为玻璃牌。',
 'The Hermit':'获得与当前金币数量相同的金币，最多额外 $20。',
 'The Wheel of Fortune':'有 1/4 概率为随机一张 Joker 添加特殊版本。',
 'Strength':'选择最多两张手牌，将点数提升一级（A 循环至 2）。',
 'The Hanged Man':'选择最多两张手牌并从牌组中永久移除。',
 'Death':'选两张手牌，使第一张复制第二张的属性。',
 'Temperance':'获得相当于当前 Joker 售价总和的金币，上限 $50。',
 'The Devil':'选择一张手牌，变为黄金牌。',
 'The Tower':'选择一张手牌，变为石头牌。',
 'The Star':'选择最多三张手牌，改为方块花色。',
 'The Moon':'选择最多三张手牌，改为梅花花色。',
 'The Sun':'选择最多三张手牌，改为红心花色。',
 'Judgement':'尝试创建一张随机 Joker，需要空余槽位。',
 'The World':'选择最多三张手牌，改为黑桃花色。',
}
SPECTRAL_DETAIL={
 'Familiar':'破坏一张随机手牌，往牌组中加入三张强化人头牌。',
 'Grim':'破坏一张随机手牌，往牌组中加入两张强化 A。',
 'Incantation':'破坏一张随机手牌，往牌组中加入四张强化数字牌。',
 'Talisman':'指定一张手牌，增加金色封印。',
 'Aura':'指定一张手牌，给予随机特殊版本。',
 'Wraith':'获得一张随机稀有 Joker，并把当前金币归零。',
 'Sigil':'将手牌中的所有牌变为同一个随机花色。',
 'Ouija':'将手牌中所有牌变为同一个随机点数，手牌上限 -1。',
 'Ectoplasm':'随机一张 Joker 变为负片版本，手牌上限 -1。',
 'Immolate':'销毁至多五张随机手牌并获得 $20。',
 'Ankh':'复制一张随机 Joker，移除其它 Joker。',
 'Deja Vu':'给一张手牌增加红色封印。',
 'Hex':'随机一张 Joker 获得多彩版本，移除其它 Joker。',
 'Trance':'给一张手牌增加蓝色封印。',
 'Medium':'给一张手牌增加紫色封印。',
 'Cryptid':'指定一张手牌，将其复制两张加入牌组。',
 'The Soul':'生成一张传说 Joker，需要空余槽位。',
 'Black Hole':'所有牌型等级 +1。',
}
SPECIAL_JOKER={
 'Blueprint':'结算时复制右手边紧邻 Joker 的可复制能力；将其放在强力 Joker 左侧。注意相邻 Joker 更换或重排会改变结果。',
 'Brainstorm':'结算时复制最左边 Joker 的可复制能力；它本身并不要求与目标相邻。',
 'Four Fingers':'顺子和同花改为四张即可满足；但不同复合牌型仍取决于参与判定的牌张。',
 'Mime':'手里未出牌的持有触发再执行一次，与钢铁牌、男爵、红印等可以叠加。',
 'Baron':'留在手里的每张 K 都会提供 ×1.5 倍率；配合钢铁牌与 Mime 可重复触发。',
 'Hanging Chad':'第一张实际计分牌额外触发两次，包括该牌本身强化和适用的计分型 Joker。',
 'Showman':'持有时允许商店/补充包出现本来受去重规则限制的重复卡牌。',
 'Smeared Joker':'红心与方块视为同一颜色、黑桃与梅花视为另一颜色进行同花判定。',
 'Chicot':'禁用 Boss 的负面能力；同时不会删除或更换 Boss 本身。',
 'Joker Stencil':'空余常规 Joker 槽越多，提供的乘算倍率越高；占用槽位会降低收益。',
 'DNA':'每轮第一手只打出一张牌时，可以复制它加入整个牌组。',
 'Constellation':'每使用一张星球牌都增加累积乘算倍率，适合频繁升级牌型。',
 'Riff-Raff':'进入 Blind 时尽可能增加两张普通 Joker；需要预留小丑槽位。',
 'Credit Card':'允许余额最低至 -$20；要承担负债带来的利息和购买机会成本。',
 'Luchador':'出售后可以禁用当前 Boss 的能力；一旦卖出便失去此 Joker。',
 'Astronomer':'星球牌及天体补充包价格归零；靠牌型等级提升提高基础分。',
 'Perkeo':'离开商店时复制一张消耗牌，生成负片版本。',
 'Obelisk':'继续打出不是最常用的牌型来累积倍率；重复最常用牌型会重置积累。',
 'Glass Joker':'每当玻璃牌碎裂时，永久增加它的乘算倍率。',
 'Steel Joker':'按整副牌组中的钢铁牌张数提供乘算倍率，不只看当前手牌。',
 'The Idol':'随回合变化的指定点数与花色组合，符合的计分牌提供额外乘算倍率。',
 'Burnt Joker':'每轮首次弃牌时升级对应牌型；应谨慎规划首次弃牌。',
 'Trading Card':'每轮首次弃牌且只弃一张时，销毁它并获得 $3，可精简牌组。',
 'Cartomancer':'进入新 Blind 时生成塔罗牌，消耗牌槽位满时可能无法新增。',
 'Hologram':'向整副牌组添加扑克牌后，累积提升乘算倍率。',
 'Midas Mask':'计分的人头牌永久变为黄金牌，为后续收益积累基础。',
 'Madness':'选择普通盲注时积累乘算倍率，并可能摧毁另一张非永恒 Joker。',
 'Ramen':'初始倍率 ×2，但弃牌会逐渐削弱，适合少弃牌的打法。',
 'Bloodstone':'计分红心时掷概率判定，成功可产生 ×1.5 倍率；重触发有收益。',
 'Hiker':'被计分的牌永久增加额外筹码，重复利用成长很快。',
 'Cavendish':'提供 ×3 倍率，但每回合有极低概率消失。',
 'Gros Michel':'提供固定加倍率，但每回合有一定概率消失，之后有机会出现卡文迪什。',
 'Seltzer':'接下来若干手的计分牌获得额外重复触发，效果耗尽后消失。',
 'Photograph':'每手第一张计分的人头牌额外 ×2 倍率，牌序会影响效果。',
 'Ceremonial Dagger':'进入 Blind 时牺牲右侧 Joker，把其售价的两倍转化为永久加倍率。',
}
TRIGGER_MARKERS=(('回合末','回合结束'),('每轮','整轮累计/轮末'),('弃','弃牌时'),('出牌','打出牌时'),('计分','计分阶段'),('手持','手牌保留阶段'),('持有','手牌保留阶段'),('商店','商店阶段'),('购买','购物阶段'),('小丑','小丑结算阶段'))

def joker_description(name,game=None,joker=None):
 j=LOOKUP.get(name)
 if not j:return ['未知小丑牌：'+str(name)]
 trigger='小丑结算阶段'
 for word,stage in TRIGGER_MARKERS:
  if word in j.desc:trigger=stage;break
 lines=[f'类别：Joker · {RU.get(j.rarity,j.rarity)} · 基础售价 ${j.cost}',
        '核心效果：'+j.desc,
        '触发时机：'+trigger,
        '玩法说明：'+SPECIAL_JOKER.get(name,'它的效果在满足描述条件时生效。需结合出牌、已有 Joker 以及牌型等级安排触发次序。')]
 if j.status=='partial':lines.append('实现提示：这张小丑涉及特殊交互；当前版本的少数边界行为仍可能简化。')
 if joker:
  flags=[s for key,s in (('eternal','永恒：无法出售'),('rental','租赁：轮末扣费'),('debuff','已失效：暂不触发')) if joker.get(key)]
  if joker.get('perishable') is not None:flags.append('易腐：剩余 '+str(joker['perishable'])+' 轮')
  if joker.get('edition'):flags.append('版本：'+str(joker['edition']))
  if flags:lines.append('当前状态：'+'；'.join(flags))
  lines.append('当前出售价值：$'+str(joker.get('sell',0)))
 if game:
  values=game.joker_state
  if name in values:lines.append('本局累计值：'+str(values[name]))
  if name=='Constellation':lines.append('本局使用星球牌数：'+str(game.planet_uses))
  if name=='Fortune Teller':lines.append('本局使用塔罗牌数：'+str(game.tarot_uses))
  if name in ('Steel Joker','Glass Joker'):
   kind='Steel' if name=='Steel Joker' else 'Glass'
   lines.append('整副牌组 '+kind+' 数量：'+str(sum(c.enhancement==kind for c in game.deck)))
 return lines

def card_description(card):
 lines=[f'牌面：{card.rank}{card.suit}  ·  普通点数筹码：{card.chips()}  ·  额外筹码：{card.bonus}',
        '花色判定：'+{'♥':'红心（红）','♦':'方块（橙）','♠':'黑桃（黑）','♣':'梅花（绿）'}.get(card.suit,card.suit),
        '普通牌可以用于组成高牌、对子、顺子、同花、葫芦等牌型。']
 if card.enhancement in ENH_DETAIL:
  a,b,c=ENH_DETAIL[card.enhancement];lines+=['强化：'+a,'结算：'+b,'提示：'+c]
 else:lines.append('强化：无')
 if card.edition:lines.append('特殊版本：'+ED.get(card.edition,card.edition)+' · '+ED_DETAIL.get(card.edition,''))
 if card.seal:lines.append('封印：'+SEAL.get(card.seal,card.seal)+' · '+SEAL_DETAIL.get(card.seal,''))
 if not card.edition and not card.seal:lines.append('版本/封印：无')
 return lines

def item_description(item,game=None):
 kind=item.get('type');name=item.get('name','')
 if kind=='Joker':return joker_description(name,game,item)
 if kind=='Planet':
  v=HANDS.get(name)
  if v:
   lv=(game.levels.get(name,1) if game else 1)
   lines=[f'星球牌：{PLANET_ZH.get(name,name)} · 对应牌型：{HAND_ZH.get(name,name)}',
          f'当前牌型等级：Lv.{lv}，使用后变成 Lv.{lv+1}',
          f'每升级一级：基础筹码 +{v[2]}，基础倍率 +{v[3]}。',
          '牌型升级是永久的（持续到本局结束），不要求本回合立即打出该牌型。']
   return lines
 if kind=='Tarot':return ['塔罗牌：'+TAROT_ZH.get(name,name),
                          '详细效果：'+TAROT_DETAIL.get(name,'此塔罗具有特殊牌组效果。'),
                          '使用时机：通常在商店、补充包或持有消耗牌时使用。',
                          '注意：指定目标时，要按当前手牌编号输入，目标通常会永久影响整副牌组。']
 if kind=='Spectral':return ['幻灵牌：'+SPECTRAL_ZH.get(name,name),
                              '详细效果：'+SPECTRAL_DETAIL.get(name,'此幻灵牌具有特殊稀有能力。'),
                              '注意：这类卡牌往往同时带来强大收益与代价，部分需要指定手牌。']
 if kind=='Card' and 'card' in item:
  from .cards import Card
  return card_description(Card.from_dict(item['card']))
 return ['暂无解释：'+str(item)]

def voucher_description(name):
 if name not in VOUCHERS:return ['未知优惠券：'+str(name)]
 v=VOUCHERS[name]
 return ['优惠券：'+v['desc'],
         '优惠券在购买后立即生效并持续到本局结束。',
         '如果存在对应高级优惠券，通常需先购买基础版本。',
         '商店卡牌、补充包和某些回合数限制可能随优惠券改变。']

EFFECT_GROUPS=[
 ('塔罗牌',[{'type':'Tarot','name':n} for n in TAROTS]),
 ('星球牌',[{'type':'Planet','name':n} for n in HANDS]),
 ('幻灵牌',[{'type':'Spectral','name':n} for n in SPECTRALS]),
 ('卡牌强化',[{'type':'Enhancement','name':n} for n in ENH_DETAIL]),
 ('特殊版本',[{'type':'Edition','name':n} for n in ED_DETAIL]),
 ('四色封印',[{'type':'Seal','name':n} for n in SEAL_DETAIL]),
 ('优惠券',[{'type':'Voucher','name':n} for n in VOUCHERS]),
]

def explain_effect(group,index,game=None):
 item=EFFECT_GROUPS[group][1][index];typ=item['type'];n=item['name']
 if typ in ('Tarot','Planet','Spectral'):return item_description(item,game)
 if typ=='Enhancement':return ['强化牌：'+ENH_DETAIL[n][0],ENH_DETAIL[n][1],ENH_DETAIL[n][2]]
 if typ=='Edition':return ['特殊版本：'+ED.get(n,n),ED_DETAIL[n]]
 if typ=='Seal':return ['特殊封印：'+SEAL.get(n,n),SEAL_DETAIL[n]]
 if typ=='Voucher':return voucher_description(n)
 return []
