"""Stateful game engine. Independent data/scorer/UI for easy iteration."""
import math,random,copy,pathlib,os,json
from collections import Counter
from ._base import Game as BaseGame, SAVE as OLD_SAVE
SAVE=pathlib.Path.home()/'.terminal_arcana_v10_save.json'
from .cards import Card,draw,RANKS,SUITS
from .poker import HANDS,HAND_ZH,analyze
from .content import JOKERS,LOOKUP,TAROTS,SPECTRALS,BOSSES,VOUCHERS,VOUCHER_PAIRS,PACK_CONFIG,PACK_SIZES
from .scoring import score_hand,prob,add_state
from .formula import score_formula
from .decks import DECKS, STAKES, curve, stake_index, MIN_BOSS_ANTE

SCALING=[300,800,2000,5000,11000,20000,35000,50000]
FINAL_BOSSES=('Violet Vessel','Crimson Heart','Amber Acorn','Verdant Leaf','Cerulean Bell')

class Game(BaseGame):
 def __init__(self,seed=None):
  self.used_bosses={};self.boss_roll_ante=None;self.boss_history=[];self.boss_disabled=False;self.pack=None;self.packs=[];self.shop_voucher=None
  self.deck_name='Red Deck';self.stake='White';self.last_tarot=None;self.last_consumable=None
  self.planet_types=[];self.free_reroll=False;self.boss_rerolls=0;self.pack_count=0
  self.played_ante=[];self.hidden_cards=[];self.locked_card=None;self.boss_ox_kind=None;self.double_tags=0
  self.voucher_period=None;self.voucher_current=None
  self.hand_was_played=False;self.last_rejected_hand=None
  super().__init__(seed)
  self.hands_data=HANDS
  self.max_hands=4;self.max_discards=3
  self.note('欢迎游玩！请选择开始盲注。')
 @classmethod
 def new_run(cls,deck_name='Red Deck',stake='White',seed=None):
  if deck_name not in {d.key for d in DECKS}:raise ValueError('未知牌组')
  if stake not in {s[0] for s in STAKES}:raise ValueError('未知难度')
  g=cls(seed);g.deck_name=deck_name;g.stake=stake
  if deck_name=='Red Deck':g.max_discards+=1
  elif deck_name=='Blue Deck':g.max_hands+=1
  elif deck_name=='Yellow Deck':g.money+=10
  elif deck_name=='Black Deck':g.joker_slots+=1;g.max_hands-=1
  elif deck_name=='Magic Deck':
   g.vouchers.add('Crystal Ball');g.consumable_slots+=1
   g.consumables.extend([{'type':'Tarot','name':'The Fool'} for _ in range(2)])
  elif deck_name=='Nebula Deck':
   g.vouchers.add('Telescope');g.consumable_slots-=1
  elif deck_name=='Ghost Deck':g.consumables.append({'type':'Spectral','name':'Hex'})
  elif deck_name=='Abandoned Deck':g.deck=[c for c in g.deck if c.rank not in ('J','Q','K')]
  elif deck_name=='Checkered Deck':
   for c in g.deck:
    if c.suit=='♣':c.suit='♠'
    if c.suit=='♦':c.suit='♥'
  elif deck_name=='Zodiac Deck':
   g.vouchers.update(('Tarot Merchant','Planet Merchant','Overstock'))
  elif deck_name=='Painted Deck':g.hand_size+=2;g.joker_slots-=1
  elif deck_name=='Erratic Deck':
   for c in g.deck:c.rank=g.rng.choice(RANKS);c.suit=g.rng.choice(SUITS)
  if stake_index(stake)>=4:g.max_discards=max(0,g.max_discards-1)
  g.recompute_target();g.note(f'已选：{deck_name} · {stake}')
  return g
 def sort_hand(self):
  order={'♥':0,'♦':1,'♠':2,'♣':3}
  rank={r:i for i,r in enumerate(RANKS)}
  self.hand.sort(key=lambda c:(order.get(c.suit,9),rank.get(c.rank,0),c.uid))
 def boss_active(self,name):return self.blind==2 and self.boss==name and not self.boss_disabled and not self.has('Chicot')
 def base_target(self):
  if self.ante<=0:return 100
  bases=curve(self.stake)
  if self.ante<=8:return bases[self.ante-1]
  c=self.ante-8
  # Two significant figures, integer arithmetic; large numbers remain arbitrary-precision.
  logvalue=math.log10(bases[-1])+c*math.log10(1.6+(.75*c)**(1+.2*c)) if c<=90 else 12000
  power=int(math.floor(logvalue));first=max(10,min(99,int(10**(logvalue-power+1)+1e-9)))
  return first*10**max(0,power-1)
 def recompute_target(self):
  factor=(1,1.5,2)[self.blind]
  if self.boss_active('The Wall'):factor=4
  if self.boss_active('Violet Vessel'):factor=6
  if self.boss_active('The Needle'):factor=1
  self.target=int(self.base_target()*factor*(2 if self.deck_name=='Plasma Deck' else 1))
 def choose_blind(self):
  self.state='blind';self.score=0;self.round_history=Counter();self.last_result=None
  self.boss_disabled=False
  if self.blind==0:self.played_ante=[]
  # The upcoming Boss is rolled once at the beginning of each Ante,
  # so its restriction is visible on both preceding Blind-select screens.
  if self.boss_roll_ante!=self.ante or not self.boss:
   pool=list(FINAL_BOSSES) if self.ante%8==0 else [n for n in BOSSES if n not in FINAL_BOSSES and max(1,self.ante)>=MIN_BOSS_ANTE.get(n,1)]
   low=min(self.used_bosses.get(n,0) for n in pool)
   pool=[n for n in pool if self.used_bosses.get(n,0)==low]
   self.boss=self.rng.choice(pool)
   self.used_bosses[self.boss]=self.used_bosses.get(self.boss,0)+1
   self.boss_roll_ante=self.ante
   self.boss_history.append({'ante':self.ante,'boss':self.boss})
  self.recompute_target()
  self.note(f'底注 {self.ante} · {self.blind_name()} · 目标 {self.target:,}')
 def blind_name(self):return ('小盲注','大盲注','Boss 盲注')[self.blind]
 def note(self,msg):
  if not hasattr(self,'log'):self.log=[]
  self.log.append(str(msg));self.log=self.log[-10:]
 def composites(self,kind):
  return {'Full House':('Pair','Three of a Kind','Two Pair'),'Four of a Kind':('Pair','Three of a Kind'),'Five of a Kind':('Pair','Three of a Kind','Four of a Kind'),'Flush House':('Flush','Full House','Pair','Three of a Kind'),'Flush Five':('Flush','Five of a Kind','Four of a Kind','Pair'),'Straight Flush':('Straight','Flush'),'Two Pair':('Pair',)}.get(kind,())
 def valid_slots(self):
  return len([j for j in self.jokers if j.get('edition')!='Negative'])<self.joker_slots
 def random_joker(self,rarity=None,exclude_owned=True):
  if rarity is None:rarity=self.rng.choices(['Common','Uncommon','Rare'],[70,25,5])[0]
  options=[j for j in JOKERS if j.rarity==rarity and (j.name!='Cavendish' or self.joker_state.get('Gros Michel_died')) and (not exclude_owned or j.name not in self.names() or self.has('Showman'))]
  return self.rng.choice(options or [j for j in JOKERS if j.rarity==rarity])
 def make_joker(self,name,edition=''):
  info=LOOKUP[name]
  return {'name':name,'sell':max(1,info.cost//2),'edition':edition}
 def sticker_fields(self,j):
  sticker=self.rng.random()
  if stake_index(self.stake)>=3 and sticker<.30:j['eternal']=True
  elif stake_index(self.stake)>=6 and sticker<.60:j['perishable']=5
  if stake_index(self.stake)>=7 and self.rng.random()<.30:j['rental']=True;j['cost']=1
  return j
 def make_joker_from_item(self,item):
  j=self.make_joker(item['name'],item.get('edition',''))
  for field in ('eternal','perishable','rental'):
   if field in item:j[field]=item[field]
  return j
 def choose_edition(self):
  boost=4 if 'Glow Up' in self.vouchers else 2 if 'Hone' in self.vouchers else 1
  roll=self.rng.random()
  if roll<.003*boost:return 'Negative'
  if roll<.02*boost:return 'Polychrome'
  if roll<.04*boost:return 'Holographic'
  if roll<.06*boost:return 'Foil'
  return ''
 def remove_joker_by_name(self,name):
  for idx,j in enumerate(self.jokers):
   if j['name']==name:self.jokers.pop(idx);return True
  return False
 def add_joker(self,name,edition='',free=False):
  if not self.valid_slots() and edition!='Negative':return False
  self.jokers.append(self.make_joker(name,edition));return True
 def commit_card(self,c):
  for own in self.deck:
   if own.uid==c.uid:
    for field in ('rank','suit','enhancement','edition','seal','bonus'):setattr(own,field,getattr(c,field))
  for own in self.draw_pile:
   if own.uid==c.uid:
    for field in ('rank','suit','enhancement','edition','seal','bonus'):setattr(own,field,getattr(c,field))
 def remove_deck_card(self,c):
  for i,x in enumerate(self.deck):
   if x.uid==c.uid:
    self.deck.pop(i)
    self.draw_pile=[x for x in self.draw_pile if x.uid!=c.uid]
    if c.rank in ('J','Q','K'):add_state(self,'Canio',1,1.0)
    return
 def fill_hand(self,n=None):
  cap=max(1,self.hand_size+(self.has('Juggler'))+(2 if self.has('Troubadour') else 0)-self.has('Merry Andy')-(2 if self.has('Stuntman') else 0)-self.boss_active('The Manacle')+max(0,self.joker_state.get('Turtle Bean',0)))
  want=max(0,cap-len(self.hand)) if n is None else min(n,max(0,cap-len(self.hand)))
  self.hand+=draw(self.draw_pile,want,self.rng)
  self.sort_hand()
 def draw_after_action(self):
  if self.boss_active('The Serpent'):
   # Balatro's Serpent draws exactly three new cards after an action,
   # even when doing so exceeds the usual hand-size limit.
   self.hand+=draw(self.draw_pile,3,self.rng)
   self.sort_hand()
  else:
   self.fill_hand()
 def start_blind(self):
  if self.state!='blind':raise ValueError('请先选择未开始的盲注')
  if self.has('Cartomancer'):self.add_consumable('Tarot')
  self.joker_state['Hit the Road']=1.0
  self.joker_state['mail_rank']=self.rng.choice(RANKS)
  self.joker_state['castle_suit']=self.rng.choice(SUITS)
  if self.has('Marble Joker'):
   c=self.rng.choice(self.deck).clone();c.enhancement='Stone';self.deck.append(c);self.added_cards+=1
  if self.has('Riff-Raff'):
   for _ in range(2):
    if self.valid_slots():self.jokers.append(self.make_joker(self.random_joker('Common').name))
  if self.has('Ceremonial Dagger'):
   for idx,j in enumerate(list(self.jokers)):
    if j['name']=='Ceremonial Dagger' and idx+1<len(self.jokers):
     other=self.jokers.pop(idx+1);add_state(self,'Ceremonial Dagger',2*other['sell']);self.note('仪式匕首献祭右侧小丑');break
  if self.has('Madness') and self.blind<2:
   add_state(self,'Madness',.5,1.0)
   options=[j for j in self.jokers if j['name']!='Madness' and not j.get('eternal')]
   if options:self.jokers.remove(self.rng.choice(options))
  if self.has('Turtle Bean') and 'Turtle Bean' not in self.joker_state:self.joker_state['Turtle Bean']=5
  if self.has('Certificate'):
   c=self.rng.choice(self.deck).clone();c.seal=self.rng.choice(['Red','Gold','Blue','Purple']);self.deck.append(c);self.added_cards+=1
  if self.boss_active('Amber Acorn'):self.rng.shuffle(self.jokers)
  for joker in self.jokers:joker.pop('debuff_round',None)
  if self.boss_active('Crimson Heart') and self.jokers:
   self.rng.choice(self.jokers)['debuff_round']=True
  # Base game's legacy Blind setup directly checks self.boss without checking
  # blind index; suppress the preview boss for Small / Big Blind setup only.
  preview_boss=self.boss
  if self.blind!=2:self.boss=''
  try:super().start_blind()
  finally:self.boss=preview_boss
  if not self.boss_active('The Needle') and self.hands==1 and self.boss=='The Needle':self.hands=self.max_hands
  if self.boss_active('The Water'):self.discards=0
  self.note('盲注已开始：Enter 选择手牌，P 出牌，O 弃牌。')
  self.hidden_cards=[];self.locked_card=None;self.hand_was_played=False;self.last_rejected_hand=None
  self._hide_new_draws(self.hand,initial=True)
  if self.boss_active('The Ox'):
   self.boss_ox_kind=max(self.history,key=self.history.get) if self.history else 'High Card'
  if self.boss_active('Cerulean Bell') and self.hand:
   self.locked_card=self.rng.choice(self.hand).uid
  return True
 def effective_hand_size(self):
  """The visible per-round capacity, including relevant Joker/Boss modifiers."""
  return max(1,self.hand_size+int(self.has('Juggler'))+
             (2 if self.has('Troubadour') else 0)-int(self.has('Merry Andy'))-
             (2 if self.has('Stuntman') else 0)-int(self.boss_active('The Manacle'))+
             max(0,self.joker_state.get('Turtle Bean',0)))
 def _hide_new_draws(self,cards,initial=False):
  """Keep existing face-down cards face-down; apply each Boss on each new draw."""
  if not cards:return
  was=set(self.hidden_cards)
  if self.boss_active('The House') and initial:was.update(c.uid for c in cards)
  if self.boss_active('The Wheel'):
   was.update(c.uid for c in cards if prob(self,7))
  if self.boss_active('The Mark'):
   was.update(c.uid for c in cards if c.rank in ('J','Q','K'))
  # The Fish only conceals draws made after PLAY, not after DISCARD.
  # Its caller marks the immediate played-hand redraw separately.
  self.hidden_cards=[c.uid for c in self.hand if c.uid in was]
 def _after_draw(self,previous,action):
  """Update hidden status after either play or discard without revealing old backs."""
  if self.boss_active('The House'):
   self.hidden_cards=[]  # The opening hand is revealed after the first action.
  self.hidden_cards=[uid for uid in self.hidden_cards if uid in {c.uid for c in self.hand}]
  newly_drawn=[c for c in self.hand if c.uid not in previous]
  self._hide_new_draws(newly_drawn)
  if action=='play' and self.boss_active('The Fish'):
   self.hidden_cards=list(dict.fromkeys(self.hidden_cards+[c.uid for c in newly_drawn]))
 def classify(self,cards):
  """Identify poker hands after disabled Wilds lose their all-suits property."""
  work=[]
  for c in cards:
   if c.enhancement=='Wild' and self.debuff(c):
    neutral=copy.copy(c);neutral.enhancement='';work.append(neutral)
   else:work.append(c)
  kind,scored=analyze(work,self.has('Shortcut'),self.has('Four Fingers'),self.has('Smeared Joker'))
  # Always return genuine cards so edition, seal and enhancement mutations persist.
  original={c.uid:c for c in cards}
  return kind,[original.get(c.uid,c) for c in scored]
 def blocked_hand_reason(self,kind,count):
  if self.boss_active('The Psychic') and count!=5:return '心灵感应：必须打出恰好 5 张牌'
  if self.boss_active('The Eye') and self.round_history[kind]:return '眼睛：本轮不能重复相同牌型'
  if self.boss_active('The Mouth') and self.round_history and kind not in self.round_history:
   return '嘴巴：本轮只能使用首次打出的牌型'
  if self.boss_active('Cerulean Bell') and self.locked_card:
   # This is a selection constraint rather than a hand-type scoring restriction.
   return None
  return None
 def discard(self,indices):
  if self.state!='play':raise ValueError('必须在对局中弃牌')
  ids,cards=self.selected(indices)
  if not self.discards:raise ValueError('弃牌次数已用完')
  if self.has('Burnt Joker') and self.discards==self.max_discards:
   kind,_=analyze(cards,self.has('Shortcut'),self.has('Four Fingers'),self.has('Smeared Joker'))
   self.levels[kind]+=1;self.note('烧焦小丑：升级了 '+kind)
  if self.has('Faceless Joker') and sum(c.rank in ('J','Q','K') for c in cards)>=3:self.money+=5
  if self.has('Mail-In Rebate'):self.money+=5*sum(c.rank==self.joker_state.get('mail_rank','A') for c in cards)
  for c in cards:
   if c.seal=='Purple':self.add_consumable('Tarot')
  if self.has('Castle'):add_state(self,'Castle',3*sum(c.suit==self.joker_state.get('castle_suit','♥') for c in cards))
  if self.has('Hit the Road'):add_state(self,'Hit the Road',.5*sum(c.rank=='J' for c in cards),1.0)
  if self.has('Yorick'):
   add_state(self,'Yorick_counter',len(cards))
   while self.joker_state['Yorick_counter']>=23:self.joker_state['Yorick_counter']-=23;add_state(self,'Yorick',1,1.0)
  if self.has('Trading Card') and self.discards==self.max_discards and len(cards)==1:
   self.remove_deck_card(cards[0]);self.money+=3
  for i in reversed(ids):self.discard_pile.append(self.hand.pop(i))
  self.discards-=1
  if self.has('Green Joker'):self.joker_state['Green Joker']=max(0,self.joker_state.get('Green Joker',0)-1)
  if self.has('Ramen'):add_state(self,'Ramen',-.01*len(cards),2)
  previous={c.uid for c in self.hand}
  self.draw_after_action()
  self._after_draw(previous,'discard')
  return cards
 def debuff(self,c):
  if self.boss_disabled or self.has('Chicot'):return False
  if self.boss_active('Verdant Leaf'):return True
  # Every Wild is affected by each suit boss. Smeared Joker extends a suit
  # debuff to both members of its colour pair.
  affected={'The Club':'♣','The Goad':'♠','The Window':'♦','The Head':'♥'}
  for blind,suit in affected.items():
   if self.boss_active(blind):
    if c.enhancement=='Wild':return True
    if c.suit==suit:return True
    if self.has('Smeared Joker') and (c.suit in ('♥','♦'))==(suit in ('♥','♦')):return True
  if self.boss_active('The Plant') and (c.rank in ('J','Q','K') or self.has('Pareidolia')):return True
  if self.boss_active('The Pillar') and c.uid in self.played_ante:return True
  return False
 def play(self,indices):
  if self.state!='play':raise ValueError('请先开始盲注')
  ids,cards=self.selected(indices)
  if self.boss_active('Cerulean Bell') and self.locked_card and self.locked_card not in [c.uid for c in cards]:
   raise ValueError('蔚蓝铃铛：必须包含被锁定的手牌')
  kind,scored=self.classify(cards)
  rejection=self.blocked_hand_reason(kind,len(cards))
  self.last_rejected_hand={'hand':kind,'reason':rejection} if rejection else None
  self.hands-=1;self.history[kind]+=1;self.round_history[kind]+=1
  if self.boss_active('The Tooth'):self.money-=len(cards)
  if self.has('Matador') and self.blind==2 and not self.has('Chicot') and any(self.boss_active(n) for n in ('The Tooth','The Ox','The Flint','The Psychic','The Needle','The Eye','The Mouth','The Club','The Head','The Goad','The Window','The Plant')):
   self.money+=8
  if self.boss_active('The Ox') and kind==self.boss_ox_kind:self.money=0
  if self.boss_active('The Arm'):self.levels[kind]=max(1,self.levels[kind]-1)
  # Crimson Heart's debuffed Joker was selected BEFORE the hand and is
  # visible to the player. It changes only after the hand, not after discards.
  if self.boss_active('Crimson Heart') and self.jokers and not any(j.get('debuff_round') for j in self.jokers):
   self.rng.choice(self.jokers)['debuff_round']=True
  if rejection:
   chips=mult=result=0
   self._score_breakdown={'base_chips':0,'bonus_chips':0,'base_mult':0,'bonus_mult':0,'xmult':1}
   self.note('无法计分：'+rejection)
  else:
   chips,mult,result=score_hand(self,kind,cards,scored)
  self.score+=result
  self.last_result={'hand':kind,'chips':round(chips,2),'mult':round(mult,3),'points':result,
                    'breakdown':self._score_breakdown,'blocked':rejection}
  if not rejection:self.note(score_formula(self.last_result))
  self.played_ante.extend(c.uid for c in cards)
  previously_disabled=[j for j in self.jokers if j.get('debuff_round')]
  for j in self.jokers:j.pop('debuff_round',None)
  if self.boss_active('Crimson Heart') and self.jokers:
   eligible=[j for j in self.jokers if all(id(j)!=id(prev) for prev in previously_disabled)] or self.jokers
   self.rng.choice(eligible)['debuff_round']=True
  for i in reversed(ids):self.discard_pile.append(self.hand.pop(i))
  if self.boss_active('The Hook') and self.hand:
   for i in sorted(self.rng.sample(range(len(self.hand)),min(2,len(self.hand))),reverse=True):self.discard_pile.append(self.hand.pop(i))
  if self.score>=self.target:self.win_blind()
  elif self.hands<=0 or (not self.hand and not self.draw_pile):
   if self.has('Mr. Bones') and self.score>=self.target*.25:
    self.remove_joker_by_name('Mr. Bones');self.win_blind()
   else:self.state='lost';self.note('游戏结束：本轮未达到目标分数。')
  else:
   previous={c.uid for c in self.hand}
   self.hand_was_played=True
   self.draw_after_action()
   self._after_draw(previous,'play')
   if self.boss_active('Cerulean Bell') and self.hand:self.locked_card=self.rng.choice(self.hand).uid
  return self.last_result
 def win_blind(self):
  for joker in self.jokers:joker.pop('debuff_round',None)
  # Apply on-end-of-round events before creating next shop.
  for c in self.hand:
   if c.enhancement=='Gold' and not self.debuff(c):self.money+=3
   if c.seal=='Blue' and not self.debuff(c) and self.last_result and len(self.consumables)<self.consumable_slots:
    self.consumables.append({'type':'Planet','name':self.last_result['hand']})
  for j in list(self.jokers):
   n=j['name']
   if n=='Golden Joker':self.money+=4
   elif n=='Cloud 9':self.money+=sum(c.rank=='9' for c in self.deck)
   elif n=='Rocket':self.money+=self.joker_state.get('Rocket',1)
   elif n=='Delayed Gratification' and self.discards==self.max_discards:self.money+=2*self.discards
   elif n=='Satellite':self.money+=len(set(self.planet_types))
   elif n=='Gift Card':
    for item in self.jokers:item['sell']=item.get('sell',2)+1
   elif n=='Egg':j['sell']=j.get('sell',2)+3
   elif n=='Popcorn':add_state(self,'Popcorn',-4,20)
   elif n=='Gros Michel' and prob(self,6):self.jokers.remove(j);self.joker_state['Gros Michel_died']=True
   elif n=='Cavendish' and prob(self,1000):self.jokers.remove(j)
   elif n=='Invisible Joker':add_state(self,'Invisible Joker_rounds',1)
   elif n=='Turtle Bean':
    self.joker_state['Turtle Bean']=max(0,self.joker_state.get('Turtle Bean',5)-1)
    if self.joker_state['Turtle Bean']==0:self.jokers.remove(j)
   elif n=='Ancient Joker':self.joker_state['ancient_suit']=self.rng.choice(SUITS)
  self.joker_state['todo']=self.rng.choice(list(HANDS))
  self.joker_state['idol']=(self.rng.choice(RANKS),self.rng.choice(SUITS))
  if self.blind==2:
   if self.has('Rocket'):add_state(self,'Rocket',2,1)
   if self.has('Campfire'):self.joker_state['Campfire']=1
  for j in self.jokers:
   if j.get('perishable') is not None:
    j['perishable']=max(0,j['perishable']-1)
    if j['perishable']==0:j['debuff']=True
   if j.get('rental'):self.money-=3
  interest=0 if self.deck_name=='Green Deck' else max(0,self.money)//5
  cap=20 if 'Money Tree' in self.vouchers else 10 if 'Seed Money' in self.vouchers else 5
  if self.has('To the Moon'):interest+=max(0,self.money)//5
  reward=[3,4,8 if self.ante%8==0 else 5][self.blind]
  if stake_index(self.stake)>=1 and self.blind==0:reward=0
  if self.deck_name=='Green Deck':reward+=2*max(0,self.hands)+max(0,self.discards)
  self.money+=reward+(0 if self.deck_name=='Green Deck' else max(0,self.hands))+min(cap,interest)
  self.state='shop';self.generate_shop();self.refresh_shop_hand()
  self.note(f'盲注完成！获得回合奖金 ${reward} 及剩余手牌/利息奖励。')
 def refresh_shop_hand(self):
  self.hand=[Card.from_dict(c.to_dict()) for c in self.rng.sample(self.deck,min(len(self.deck),max(1,self.hand_size)))]
  self.sort_hand()
 def _eligible_voucher(self):
  pool=[]
  for base,upgrade,_ in VOUCHER_PAIRS:
   if base not in self.vouchers:pool.append(base)
   elif upgrade not in self.vouchers:pool.append(upgrade)
  return self.rng.choice(pool) if pool else None
 def shop_discount(self):return .5 if 'Liquidation' in self.vouchers else .75 if 'Clearance Sale' in self.vouchers else 1
 def apply_cost(self,raw):return max(0,math.ceil(raw*self.shop_discount()))
 def shop_weights(self):
  # 原始权重 Joker / Tarot / Planet 为 20 / 4 / 4。
  # 商人/大亨优惠券改变权重而非覆盖概率。
  wt={'Joker':20.0,'Tarot':4.0,'Planet':4.0}
  if 'Tarot Tycoon' in self.vouchers:wt['Tarot']=32.0
  elif 'Tarot Merchant' in self.vouchers:wt['Tarot']=9.6
  if 'Planet Tycoon' in self.vouchers:wt['Planet']=32.0
  elif 'Planet Merchant' in self.vouchers:wt['Planet']=9.6
  if self.deck_name=='Ghost Deck':wt['Spectral']=2.0
  if 'Magic Trick' in self.vouchers:wt['Card']=4.0
  return wt
 def shop_item(self):
  weights=self.shop_weights()
  kind=self.rng.choices(list(weights),weights=list(weights.values()))[0]
  if kind=='Joker':
   j=self.random_joker();ed=self.choose_edition()
   price=self.apply_cost(j.cost+({'Foil':2,'Holographic':3,'Polychrome':5,'Negative':5}.get(ed,0)))
   return self.sticker_fields({'type':kind,'name':j.name,'edition':ed,'cost':price})
  if kind=='Card':
   card=self.rng.choice(self.deck).clone()
   if 'Illusion' in self.vouchers:
    card.enhancement=self.rng.choice(['','Bonus','Mult','Steel','Glass','Lucky','Gold'])
    card.edition=self.choose_edition()
   return {'type':'Card','name':card.label(),'card':card.to_dict(),'cost':self.apply_cost(3)}
  if kind=='Spectral':name=self.rng.choice(SPECTRALS[:16]);base=4
  else:name=self.rng.choice(list(HANDS) if kind=='Planet' else TAROTS);base=3
  price=0 if kind=='Planet' and self.has('Astronomer') else self.apply_cost(base)
  return {'type':kind,'name':name,'cost':price}
 def roll_shop_cards(self,n):
  results=[];seen=set()
  for _ in range(n):
   for _attempt in range(120):
    item=self.shop_item();key=(item['type'],item['name'])
    if self.has('Showman') or key not in seen:
     results.append(item);seen.add(key);break
   else:results.append(self.shop_item())
  return results
 def generate_shop(self):
  self.joker_state['rerolls']=0;self.free_reroll=self.has('Chaos the Clown')
  slots=2+int('Overstock' in self.vouchers)+int('Overstock Plus' in self.vouchers)
  self.shop=self.roll_shop_cards(slots)
  self.packs=[]
  for _ in range(2):
   kind=self.rng.choices(list(PACK_CONFIG),weights=[32,32,5,24,7])[0]
   size=self.rng.choices(['Normal','Jumbo','Mega'],weights=[65,27,8])[0]
   price=self.apply_cost(PACK_SIZES[size][0])
   if kind=='Celestial' and self.has('Astronomer'):price=0
   self.packs.append({'kind':kind,'size':size,'cost':price})
  # A voucher remains on offer until bought. It restocks only after the Boss
  # has been defeated, and redeemed vouchers are never drawn again.
  period=self.ante+int(self.blind==2)
  if self.voucher_period!=period:
   self.voucher_period=period
   self.voucher_current=self._eligible_voucher()
  if self.voucher_current in self.vouchers:self.voucher_current=None
  self.shop_voucher=self.voucher_current
 def reroll(self):
  if self.state!='shop':raise ValueError('只能在商店刷新')
  price=max(1,5+self.joker_state.get('rerolls',0)-2*('Reroll Surplus' in self.vouchers)-2*('Reroll Glut' in self.vouchers))
  if self.free_reroll:price=0;self.free_reroll=False
  if self.money<price:raise ValueError(f'刷新需要 ${price}')
  self.money-=price;self.joker_state['rerolls']=self.joker_state.get('rerolls',0)+1
  self.shop=self.roll_shop_cards(len(self.shop));add_state(self,'Flash Card',2)
 def buy(self,index):
  if self.state!='shop':raise ValueError('目前不在商店')
  if not 0<=index<len(self.shop):raise ValueError('商品编号无效')
  item=self.shop[index];price=item['cost']
  if self.money-price<(-20 if self.has('Credit Card') else 0):raise ValueError('金币不足')
  if item['type']=='Joker' and not self.valid_slots() and item.get('edition')!='Negative':raise ValueError('小丑栏已满')
  if item['type'] in ('Tarot','Planet','Spectral') and len(self.consumables)>=self.consumable_slots:raise ValueError('消耗牌栏已满')
  self.money-=price
  if item['type']=='Joker':self.jokers.append(self.make_joker_from_item(item))
  elif item['type']=='Card':
   c=Card.from_dict(item['card']);self.deck.append(c);self.added_cards+=1
  else:self.consumables.append({'type':item['type'],'name':item['name']})
  self.note('购买成功：'+(LOOKUP[item['name']].zh if item['type']=='Joker' else item['name']));self.shop.pop(index)
 def buy_voucher(self):
  if self.state!='shop':raise ValueError('只能在商店购买优惠券')
  if not self.shop_voucher:raise ValueError('本店没有优惠券')
  price=self.apply_cost(10)
  if self.money-price<(-20 if self.has('Credit Card') else 0):raise ValueError('金币不足')
  name=self.shop_voucher
  if name in self.vouchers:raise ValueError('已经拥有该券')
  self.money-=price;self.vouchers.add(name);self.shop_voucher=None;self.voucher_current=None
  if name in ('Grabber','Nacho Tong'):self.max_hands+=1
  if name in ('Wasteful','Recyclomancy'):self.max_discards+=1
  if name=='Crystal Ball':self.consumable_slots+=1
  if name=='Antimatter':self.joker_slots+=1
  if name in ('Paint Brush','Palette'):self.hand_size+=1
  if name=='Hieroglyph':self.ante=max(0,self.ante-1);self.max_hands=max(1,self.max_hands-1)
  if name=='Petroglyph':self.ante=max(0,self.ante-1);self.max_discards=max(0,self.max_discards-1)
  if name in ('Hieroglyph','Petroglyph'):self.recompute_target()
  self.note('优惠券已激活：'+name)
 def open_pack(self,index):
  if self.state!='shop':raise ValueError('只有商店能打开补充包')
  if not 0<=index<len(self.packs):raise ValueError('补充包编号无效')
  p=self.packs[index]
  if self.money-p['cost']<(-20 if self.has('Credit Card') else 0):raise ValueError('金币不足')
  self.money-=p['cost'];self.packs.pop(index)
  kind,size=p['kind'],p['size'];shown=PACK_CONFIG[kind][0 if size=='Normal' else 1];picks=PACK_SIZES[size][1]
  options=[]
  seen=set()
  # Options are a fixed set sampled once. Never replenish a choice after picking.
  for i in range(shown):
   for attempt in range(500):
    if kind=='Arcana':
     if self.rng.random()<.003:name='The Soul';typ='Spectral'
     elif 'Omen Globe' in self.vouchers and self.rng.random()<.2:name=self.rng.choice(SPECTRALS[:16]);typ='Spectral'
     else:name=self.rng.choice(TAROTS);typ='Tarot'
     item={'type':typ,'name':name}
    elif kind=='Celestial':
     top=max(HANDS,key=lambda n:self.history.get(n,0)) if self.history else 'Pair'
     name=top if i==0 and 'Telescope' in self.vouchers else self.rng.choice(list(HANDS))
     item={'type':'Planet','name':name}
    elif kind=='Spectral':
     name='The Soul' if self.rng.random()<.003 else 'Black Hole' if self.rng.random()<.003 else self.rng.choice(SPECTRALS[:16])
     item={'type':'Spectral','name':name}
    elif kind=='Standard':
     c=self.rng.choice(self.deck).clone()
     if self.rng.random()<.35:c.enhancement=self.rng.choice(['Bonus','Mult','Wild','Glass','Steel','Gold','Lucky','Stone'])
     if self.rng.random()<.2:c.seal=self.rng.choice(['Red','Purple','Blue','Gold'])
     c.edition=self.choose_edition()
     item={'type':'Card','name':c.label(),'card':c.to_dict()}
    else:
     # Exclude names already rolled within this single pack.
     pool=[j for j in JOKERS if j.rarity!='Legendary' and j.name not in seen]
     j=self.rng.choice(pool)
     item=self.sticker_fields({'type':'Joker','name':j.name,'edition':self.choose_edition()})
    unique_key=(item['type'],item['name'])
    if unique_key not in seen:
     options.append(item);seen.add(unique_key);break
   else:
    raise RuntimeError('补充包生成失败：可用卡牌不足')
  self.pack={'kind':kind,'size':size,'options':options,'picks':picks,'original_total':len(options)}
  if kind in ('Arcana','Spectral'):self.refresh_shop_hand()
  self.state='pack';self.pack_count+=1
  if self.has('Hallucination') and prob(self,2):self.add_consumable('Tarot')
  self.note('补充包已打开：选择编号，Z 放弃剩余项目')
 def select_pack(self,index,targets=None):
  if self.state!='pack' or not self.pack:raise ValueError('当前没有补充包')
  opts=self.pack['options'];targets=targets or []
  if not 0<=index<len(opts):raise ValueError('补充包卡牌编号无效')
  item=opts[index];typ=item['type'];name=item['name']
  if typ=='Joker':
   if not self.valid_slots() and item.get('edition')!='Negative':raise ValueError('小丑栏已满')
   self.jokers.append(self.make_joker_from_item(item))
  elif typ=='Card':
   self.deck.append(Card.from_dict(item['card']));self.added_cards+=1
  else:
   self.consumables.append({'type':typ,'name':name})
   try:self.use(len(self.consumables)-1,targets)
   except Exception:
    if self.consumables and self.consumables[-1]['name']==name:self.consumables.pop()
    raise
  self.pack['picks']-=1;opts.pop(index);self.note('从补充包选择了：'+name)
  if self.pack['picks']<=0 or not opts:self.pack=None;self.state='shop'
 def skip_pack(self):
  if self.state!='pack':raise ValueError('当前没有补充包')
  if self.has('Red Card'):add_state(self,'Red Card',3)
  self.pack=None;self.state='shop';self.note('跳过了补充包')
 def add_consumable(self,typ):
  if len(self.consumables)>=self.consumable_slots:return False
  name=self.rng.choice(list(HANDS) if typ=='Planet' else TAROTS if typ=='Tarot' else SPECTRALS[:16])
  self.consumables.append({'type':typ,'name':name});return True
 def use(self,index,targets=None):
  if not 0<=index<len(self.consumables):raise ValueError('消耗牌编号无效')
  item=self.consumables[index];typ=item['type'];name=item['name'];targets=targets or []
  if typ=='Planet':
   self.levels[name]+=1;self.planet_uses+=1;self.planet_types.append(name)
   if self.has('Constellation'):add_state(self,'Constellation',.1,1.0)
   self.consumables.pop(index);self.last_consumable=('Planet',name);self.note('升级牌型：'+name);return
  if typ=='Tarot':
   if name=='The Fool':
    if not self.last_consumable or self.last_consumable[0]=='Tarot' and self.last_consumable[1]=='The Fool':raise ValueError('尚无可复制的消耗牌')
    self.consumables.pop(index)
    if len(self.consumables)<self.consumable_slots:self.consumables.append({'type':self.last_consumable[0],'name':self.last_consumable[1]})
    return
   if name in ('The Hanged Man','Death','Strength','The Magician','The Empress','The Hierophant','The Lovers','The Chariot','Justice','The Devil','The Tower','The Star','The Moon','The Sun','The World') and not targets:
    raise ValueError('此塔罗需要指定手牌编号，例如：使用 1 2 3')
   if any(t<0 or t>=len(self.hand) for t in targets):raise ValueError('目标手牌编号无效')
   if name=='The High Priestess':
    self.consumables.pop(index)
    for _ in range(2):self.add_consumable('Planet')
    self.tarot_uses+=1;self.last_tarot=name;self.last_consumable=('Tarot',name)
    return
   if name=='The Emperor':
    self.consumables.pop(index)
    for _ in range(2):self.add_consumable('Tarot')
    self.tarot_uses+=1;self.last_tarot=name;self.last_consumable=('Tarot',name)
    return
   if name=='Judgement':
    self.consumables.pop(index)
    if self.valid_slots():self.add_joker(self.random_joker().name)
    self.tarot_uses+=1;self.last_tarot=name;self.last_consumable=('Tarot',name)
    return
   if name=='Death' and len(targets)>=2:
    source=self.hand[targets[1]];target=self.hand[targets[0]]
    for attribute in ('rank','suit','enhancement','edition','seal','bonus'):
     setattr(target,attribute,getattr(source,attribute))
    self.commit_card(target);self.consumables.pop(index);self.tarot_uses+=1;self.last_consumable=('Tarot',name)
    return
   if name=='The Wheel of Fortune':
    if self.jokers and prob(self,4):self.rng.choice(self.jokers)['edition']=self.rng.choice(['Foil','Holographic','Polychrome'])
   else:
    super().use(index,targets)
    if name=='The Hermit':pass
   if name=='The Wheel of Fortune':self.consumables.pop(index)
   for c in self.hand:self.commit_card(c)
   self.tarot_uses+=int(name=='The Wheel of Fortune')
   self.last_tarot=name;self.last_consumable=('Tarot',name)
   return
  if typ=='Spectral':
   # All Spectral consumables share the same permanent card / Joker objects.
   # Validate before consumption so impossible effects do not waste the item.
   if name in ('Familiar','Grim','Incantation','Immolate','Sigil','Ouija') and len(self.hand)<2:
    raise ValueError('此幻灵牌要求当前至少有 2 张手牌')
   if name in ('Aura','Talisman','Deja Vu','Trance','Medium','Cryptid'):
    if len(targets)!=1 or targets[0]<0 or targets[0]>=len(self.hand):
     raise ValueError('请在界面选中恰好 1 张目标手牌')
   if name=='Black Hole':
    for kind in self.levels:self.levels[kind]+=1
   elif name=='The Soul':
    if not self.valid_slots():raise ValueError('小丑栏已满，不能使用灵魂')
    opts=[j.name for j in JOKERS if j.rarity=='Legendary' and j.name not in self.names()]
    if not opts:opts=[j.name for j in JOKERS if j.rarity=='Legendary']
    if not self.add_joker(self.rng.choice(opts)):raise ValueError('小丑栏已满')
   elif name=='Wraith':
    if not self.valid_slots():raise ValueError('小丑栏已满，不能使用幽灵')
    self.add_joker(self.random_joker('Rare').name);self.money=0
   elif name in ('Familiar','Grim','Incantation'):
    destroyed=self.rng.choice(self.hand)
    self.remove_deck_card(destroyed);self.hand.remove(destroyed)
    qty={'Familiar':3,'Grim':2,'Incantation':4}[name]
    ranks=('J','Q','K') if name=='Familiar' else ('A',) if name=='Grim' else ('2','3','4','5','6','7','8','9','10')
    for _ in range(qty):
     card=Card(self.rng.choice(ranks),self.rng.choice(SUITS),
               enhancement=self.rng.choice(('Bonus','Mult','Wild','Glass','Steel','Gold','Lucky')))
     self.deck.append(card)
     self.hand.append(Card.from_dict(card.to_dict()))
     self.added_cards+=1
    self.hidden_cards=[uid for uid in self.hidden_cards if any(c.uid==uid for c in self.hand)]
    self.sort_hand()
   elif name in ('Sigil','Ouija'):
    if name=='Sigil':
     suit=self.rng.choice(SUITS)
     for card in self.hand:card.suit=suit;self.commit_card(card)
     self.note('符印：全部 '+str(len(self.hand))+' 张手牌变成 '+suit)
    else:
     rank=self.rng.choice(RANKS)
     for card in self.hand:card.rank=rank;self.commit_card(card)
     self.hand_size=max(1,self.hand_size-1)
     self.note('通灵板：全部 '+str(len(self.hand))+' 张手牌变成 '+rank+'，手牌容量 -1')
    self.sort_hand()
   elif name=='Ectoplasm':
    eligible=[j for j in self.jokers if not j.get('edition')]
    if not eligible:raise ValueError('没有无特殊版本的 Joker 可以添加负片')
    self.rng.choice(eligible)['edition']='Negative'
    count=self.joker_state.get('Ectoplasm_used',0)+1
    self.joker_state['Ectoplasm_used']=count
    self.hand_size=max(1,self.hand_size-count)
   elif name=='Immolate':
    destroyed=self.rng.sample(self.hand,min(5,len(self.hand)))
    ids={c.uid for c in destroyed}
    for card in destroyed:self.remove_deck_card(card)
    self.hand=[c for c in self.hand if c.uid not in ids]
    self.hidden_cards=[uid for uid in self.hidden_cards if uid not in ids]
    self.money+=20
   elif name=='Ankh':
    if not self.jokers:raise ValueError('没有可复制的小丑牌')
    if not self.valid_slots():raise ValueError('需要空余 Joker 栏位才能复制')
    survivor=self.rng.choice(self.jokers)
    survivor_id=id(survivor)
    clone=survivor.copy()
    if clone.get('edition')=='Negative':clone['edition']=''
    self.jokers=[j for j in self.jokers if id(j)==survivor_id or j.get('eternal')]
    self.jokers.append(clone)
   elif name=='Hex':
    eligible=[j for j in self.jokers if not j.get('edition')]
    if not eligible:raise ValueError('没有无特殊版本的 Joker 可以获得多彩效果')
    survivor=self.rng.choice(eligible)
    survivor_id=id(survivor)
    survivor['edition']='Polychrome'
    self.jokers=[j for j in self.jokers if id(j)==survivor_id or j.get('eternal')]
   elif name=='Cryptid':
    original=self.hand[targets[0]]
    for _ in range(2):
     clone=original.clone()
     self.deck.append(clone)
     self.hand.append(Card.from_dict(clone.to_dict()))
     self.added_cards+=1
    self.sort_hand()
   elif name in ('Aura','Talisman','Deja Vu','Trance','Medium'):
    card=self.hand[targets[0]]
    if name=='Aura':
     if card.edition:raise ValueError('目标已经有特殊版本，不能使用光环')
     card.edition=self.rng.choices(('Foil','Holographic','Polychrome'),weights=(50,35,15))[0]
    else:
     card.seal={'Talisman':'Gold','Deja Vu':'Red','Trance':'Blue','Medium':'Purple'}[name]
    self.commit_card(card)
   else:
    raise ValueError('此幻灵牌暂不可使用')
   self.consumables.pop(index)
   self.last_consumable=('Spectral',name)
   return
 def sell_joker(self,index):
  if not 0<=index<len(self.jokers):raise ValueError('小丑编号无效')
  j=self.jokers[index]
  if j.get('eternal'):raise ValueError('永恒小丑不可出售')
  name=j['name']
  super().sell_joker(index)
  if name=='Luchador' and self.blind==2:self.boss_disabled=True;self.recompute_target()
  if self.boss_active('Verdant Leaf') or self.boss=='Verdant Leaf' and self.state=='play':self.boss_disabled=True;self.note('翠绿叶片：出售小丑后 Boss 失效')
  if name=='Invisible Joker' and self.joker_state.get('Invisible Joker_rounds',0)>=2 and self.jokers:
   other=self.rng.choice(self.jokers)
   if self.valid_slots():self.jokers.append(other.copy())
  if name=='Diet Cola':self.skip_count+=2
  if self.has('Campfire'):add_state(self,'Campfire',.25,1.0)
 def next_blind(self):
  if self.state!='shop':raise ValueError('请先完成对局并进入商店')
  if self.has('Perkeo') and self.consumables:
   item=copy.deepcopy(self.rng.choice(self.consumables));item['negative']=True;self.consumables.append(item)
  self.blind+=1
  if self.blind==3:
   self.blind=0;self.ante+=1;self.boss_rerolls=0
   if self.deck_name=='Anaglyph Deck':self.double_tags+=1
   if self.ante>=9 and not self.won:self.won=True;self.note('第8底注完成！无尽模式开始。')
  self.choose_blind()
 def skip_blind(self):
  if self.state!='blind' or self.blind==2:raise ValueError('只能跳过尚未开始的小盲注/大盲注')
  self.skip_count+=1
  # Simplified, playable tag reward; double tags duplicate the next reward.
  repeat=min(8,1+self.double_tags);self.double_tags=0
  tag=self.rng.choice(('现金奖励','小丑赠礼','免费刷新'))
  for _ in range(repeat):
   if tag=='现金奖励':self.money+=6
   elif tag=='小丑赠礼' and self.valid_slots():self.add_joker(self.random_joker('Common').name)
   elif tag=='免费刷新':self.free_reroll=True
  self.blind+=1;self.choose_blind()
  self.note(f'跳过盲注 · {tag} ×{repeat}（Tag 奖励为简化实现）')
 def reroll_boss(self):
  if self.state!='blind':raise ValueError('只能在盲注准备页重掷下一位 Boss')
  if not any(v in self.vouchers for v in ("Director's Cut",'Retcon')):raise ValueError('尚未购买 Boss 重掷优惠券')
  if "Director's Cut" in self.vouchers and self.boss_rerolls>=1 and 'Retcon' not in self.vouchers:raise ValueError('每底注只能重掷一次')
  if self.money<10:raise ValueError('重掷需要 $10')
  self.money-=10;old=self.boss
  options=[n for n in (FINAL_BOSSES if self.ante%8==0 else tuple(n for n in BOSSES if n not in FINAL_BOSSES)) if n!=old and (self.ante%8==0 or self.ante>=MIN_BOSS_ANTE.get(n,1))]
  self.boss=self.rng.choice(options);self.boss_rerolls+=1;self.recompute_target();self.note('下一个 Boss 已更换')
  self.boss_history.append({'ante':self.ante,'boss':self.boss,'reroll':True})
 def save(self,path=SAVE):
  """Atomic save prevents a crash/quit from leaving a broken JSON file."""
  path=pathlib.Path(path).expanduser()
  path.parent.mkdir(parents=True,exist_ok=True)
  temp=path.with_name(path.name+'.tmp')
  try:
   super().save(temp)
   os.replace(temp,path)
  finally:
   if temp.exists():temp.unlink()
  return path
 @classmethod
 def save_candidates(cls):
  return [SAVE] if SAVE.exists() else []
 @classmethod
 def load(cls,path=None):
  candidates=[pathlib.Path(path).expanduser()] if path is not None else cls.save_candidates()
  error=None
  for candidate in candidates:
   try:
    game=super().load(candidate)
    # Restore fields added since earlier versions, regardless of explicit path.
    with candidate.open(encoding='utf8') as fp:
     saved_fields=json.load(fp)
    template=cls(game.seed)
    for name,value in vars(template).items():
     if not hasattr(game,name):setattr(game,name,value)
    # Preserve the voucher shown in a pre-V13 shop; do not reroll it while
    # loading a save, and do not resurrect a voucher already purchased.
    if 'voucher_period' not in saved_fields and game.state=='shop':
     game.voucher_period=game.ante+int(game.blind==2)
     game.voucher_current=(game.shop_voucher if game.shop_voucher not in game.vouchers else None)
     game.shop_voucher=game.voucher_current
    # Older saves might have previewed a Boss without identifying the Ante.
    if getattr(game,'boss_roll_ante',None) is None and game.boss:
     game.boss_roll_ante=game.ante
    if 'boss_history' not in saved_fields or (not game.boss_history and game.boss):
     game.boss_history=[{'ante':game.boss_roll_ante or game.ante,'boss':game.boss}] if game.boss else []
    game.sort_hand()
    return game
   except (ValueError,TypeError,KeyError,AttributeError,OSError,json.JSONDecodeError) as exc:
    error=exc
  if error:raise ValueError('找到存档，但格式无效：'+str(error))
  raise FileNotFoundError('尚未找到当前版本的存档。请先创建游戏。')
