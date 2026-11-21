import random, json, pathlib, math
from collections import Counter
from .cards import Card,deck,draw,RANKS,SUITS
from .poker import analyze,HANDS,PLANETS
from .content import JOKERS,LOOKUP,TAROTS,SPECTRALS,BOSSES
SAVE=pathlib.Path.home()/'.terminal_arcana_save.json'
BASE_TARGETS=[300,800,2000,5000,11000,20000,35000,50000,110000,560000,7200000]
class Game:
 def __init__(self,seed=None):
  self.rng=random.Random(seed);self.seed=seed;self.ante=1;self.blind=0;self.money=4;self.score=0;self.target=0
  self.deck=deck();self.rng.shuffle(self.deck);self.draw_pile=[];self.hand=[];self.discard_pile=[]
  self.jokers=[];self.joker_state={};self.levels={k:1 for k in HANDS};self.history=Counter();self.round_history=Counter()
  self.hands=4;self.discards=3;self.max_hands=4;self.max_discards=3;self.hand_size=8;self.joker_slots=5
  self.state='blind';self.shop=[];self.consumables=[];self.consumable_slots=2;self.boss='';self.log=[];self.round=0;self.vouchers=set();self.skip_count=0
  self.last_result=None;self.won=False;self.planet_uses=0;self.tarot_uses=0;self.added_cards=0;self.destroyed_glass=0
  self.choose_blind()
 def note(self,s):self.log.append(str(s));self.log=self.log[-8:]
 def names(self):return [j['name'] for j in self.jokers]
 def has(self,n):return n in self.names()
 def choose_blind(self):
  self.state='blind';self.score=0;self.round_history=Counter();self.last_result=None
  self.boss=self.rng.choice(list(BOSSES)) if self.blind==2 else ''
  base=BASE_TARGETS[min(self.ante-1,len(BASE_TARGETS)-1)]*(2**max(0,self.ante-11))
  self.target=int(base*[1,1.5,2][self.blind]);
  if self.boss=='The Wall':self.target*=4
  if self.boss=='Violet Vessel':self.target*=6
  self.note(f'Ante {self.ante} · {self.blind_name()} · target {self.target:,}')
 def blind_name(self):return ('Small Blind','Big Blind','Boss Blind')[self.blind]
 def start_blind(self):
  if self.state!='blind':return False
  self.state='play';self.round+=1;self.hands=self.max_hands;self.discards=self.max_discards
  self.hands+=3 if self.has('Burglar') else 0
  self.discards+=1 if self.has('Drunkard') else 0
  self.discards+=3 if self.has('Merry Andy') else 0
  if self.has('Burglar') or self.boss=='The Water':self.discards=0
  if self.has('Troubadour'):self.hands-=1
  if self.boss=='The Needle':self.hands=1
  self.draw_pile=[Card.from_dict(c.to_dict()) for c in self.deck];self.rng.shuffle(self.draw_pile)
  self.hand=[];self.discard_pile=[];self.fill_hand();self.note('Blind started. Choose up to 5 cards.')
  return True
 def fill_hand(self,n=None):
  size=max(1,self.hand_size-(self.has('Merry Andy'))-(self.boss=='The Manacle'))
  need=max(0,size-len(self.hand)) if n is None else min(n,max(0,size-len(self.hand)))
  self.hand+=draw(self.draw_pile,need,self.rng)
 def selected(self,indices):
  ids=sorted(set(indices));
  if not ids or len(ids)>5 or any(i<0 or i>=len(self.hand) for i in ids):raise ValueError('Select 1–5 valid card numbers.')
  return ids,[self.hand[i] for i in ids]
 def discard(self,indices):
  if self.state!='play':raise ValueError('Not playing.')
  if self.discards<=0:raise ValueError('No discards left.')
  ids,cards=self.selected(indices)
  if self.has('Trading Card') and self.discards==self.max_discards and len(cards)==1:
   self.remove_deck_card(cards[0]);self.money+=3;self.note('Trading Card: destroyed a card, +$3')
  for i in reversed(ids):self.discard_pile.append(self.hand.pop(i))
  self.discards-=1
  if self.has('Green Joker'):self.joker_state['Green Joker']=max(0,self.joker_state.get('Green Joker',0)-1)
  if self.has('Ramen'):self.joker_state['Ramen']=max(1,self.joker_state.get('Ramen',2)-.01)
  self.fill_hand(3 if self.boss=='The Serpent' else None)
 def remove_deck_card(self,c):
  for i,x in enumerate(self.deck):
   if x.rank==c.rank and x.suit==c.suit:self.deck.pop(i);return
 def play(self,indices):
  if self.state!='play':raise ValueError('Not playing.')
  ids,cards=self.selected(indices)
  if self.boss=='The Psychic' and len(cards)!=5:raise ValueError('Psychic: play exactly 5 cards.')
  kind,scored=analyze(cards,self.has('Shortcut'),self.has('Four Fingers'),self.has('Smeared Joker'))
  if self.boss=='The Eye' and self.round_history[kind]:raise ValueError('Eye: cannot repeat hand type.')
  if self.boss=='The Mouth' and self.round_history and kind not in self.round_history:raise ValueError('Mouth: must repeat first hand type.')
  chips,mult,ci,mi=HANDS[kind];level=self.levels[kind];chips+=ci*(level-1);mult+=mi*(level-1)
  if self.boss=='The Flint':chips=max(1,chips//2);mult=max(1,mult//2)
  self.hands-=1;self.history[kind]+=1;self.round_history[kind]+=1
  if self.has('Splash'):scored=cards
  if self.boss=='The Tooth':self.money-=len(cards)
  if self.boss=='The Ox' and self.history[kind]==max(self.history.values()):self.money=0
  if self.has('DNA') and self.round_history.total()==1 and len(cards)==1:
   self.deck.append(Card.from_dict(cards[0].to_dict()));self.added_cards+=1;self.note('DNA duplicated one card.')
  if self.has('Square Joker') and len(cards)==4:self.joker_state['Square Joker']=self.joker_state.get('Square Joker',0)+4
  if self.has('Runner') and 'Straight' in kind:self.joker_state['Runner']=self.joker_state.get('Runner',0)+15
  if self.has('Green Joker'):self.joker_state['Green Joker']=self.joker_state.get('Green Joker',0)+1
  if self.has('Ride the Bus'):
   if any(c.rank in ('J','Q','K') for c in scored):self.joker_state['Ride the Bus']=0
   else:self.joker_state['Ride the Bus']=self.joker_state.get('Ride the Bus',0)+1
  for c in scored:
   if self.debuff(c):continue
   repeat=3 if (self.has('Hanging Chad') and c is scored[0]) else 1
   if c.seal=='Red':repeat+=1
   for _ in range(repeat):
    chips+=c.chips()+c.bonus
    if c.enhancement=='Bonus':chips+=30
    if c.enhancement=='Mult':mult+=4
    if c.enhancement=='Glass':mult*=2
    if c.edition=='Foil':chips+=50
    if c.edition=='Holographic':mult+=10
    if c.edition=='Polychrome':mult*=1.5
    for name in self.names():
     if name=='Greedy Joker' and c.suit=='♦' or name=='Lusty Joker' and c.suit=='♥' or name=='Wrathful Joker' and c.suit=='♠' or name=='Gluttonous Joker' and c.suit=='♣':mult+=3
     if name=='Even Steven' and c.rank in ('2','4','6','8','10'):mult+=4
     if name=='Odd Todd' and c.rank in ('A','3','5','7','9'):chips+=31
     if name=='Fibonacci' and c.rank in ('A','2','3','5','8'):mult+=8
     if name=='Scholar' and c.rank=='A':chips+=20;mult+=4
     if name=='Scary Face' and c.rank in ('J','Q','K'):chips+=30
     if name=='Smiley Face' and c.rank in ('J','Q','K'):mult+=5
     if name=='Arrowhead' and c.suit=='♠':chips+=50
     if name=='Onyx Agate' and c.suit=='♣':mult+=7
     if name=='Bloodstone' and c.suit=='♥' and self.rng.random()<.5:mult*=1.5
     if name=='Rough Gem' and c.suit=='♦':self.money+=1
   if c.enhancement=='Lucky' and self.rng.random()<.2:mult+=20
   if c.enhancement=='Lucky' and self.rng.random()<1/15:self.money+=20
   if c.enhancement=='Glass' and self.rng.random()<.25:self.remove_deck_card(c);self.destroyed_glass+=1
  for c in self.hand:
   if c not in cards and c.enhancement=='Steel':mult*=1.5
  for j in self.jokers:
   name=j['name'];chips,mult=self.joker_effect(name,kind,cards,scored,chips,mult)
   if j.get('edition')=='Foil':chips+=50
   if j.get('edition')=='Holographic':mult+=10
   if j.get('edition')=='Polychrome':mult*=1.5
  result=int(max(0,chips)*max(0,mult));self.score+=result
  self.last_result={'hand':kind,'chips':round(chips,2),'mult':round(mult,2),'points':result}
  self.note(f'{kind}: {chips:.0f} × {mult:.2f} = {result:,}')
  if self.boss=='The Arm':self.levels[kind]=max(1,self.levels[kind]-1)
  for i in reversed(ids):self.discard_pile.append(self.hand.pop(i))
  if self.boss=='The Hook' and self.hand:
   for i in sorted(self.rng.sample(range(len(self.hand)),min(2,len(self.hand))),reverse=True):self.discard_pile.append(self.hand.pop(i))
  if self.score>=self.target:self.win_blind()
  elif self.hands<=0:
   if self.has('Mr. Bones') and self.score>=self.target*.25:
    self.sell_joker(self.names().index('Mr. Bones'));self.win_blind()
   else:self.state='lost';self.note('Game over.')
  else:self.fill_hand(3 if self.boss=='The Serpent' else None)
  return self.last_result
 def debuff(self,c):
  if self.boss=='The Club' and c.suit=='♣' or self.boss=='The Goad' and c.suit=='♠' or self.boss=='The Window' and c.suit=='♦' or self.boss=='The Head' and c.suit=='♥':return True
  if self.boss=='The Plant' and c.rank in ('J','Q','K'):return True
  return False
 def joker_effect(self,n,k,cards,scored,chips,mult):
  cond={'Jolly Joker':'Pair','Zany Joker':'Three of a Kind','Mad Joker':'Two Pair','Crazy Joker':'Straight','Droll Joker':'Flush','Sly Joker':'Pair','Wily Joker':'Three of a Kind','Clever Joker':'Two Pair','Devious Joker':'Straight','Crafty Joker':'Flush'}
  vals={'Jolly Joker':8,'Zany Joker':12,'Mad Joker':10,'Crazy Joker':12,'Droll Joker':10}
  cvals={'Sly Joker':50,'Wily Joker':100,'Clever Joker':80,'Devious Joker':100,'Crafty Joker':80}
  if n=='Joker':mult+=4
  if n in cond and cond[n] in k:mult+=vals.get(n,0);chips+=cvals.get(n,0)
  if n=='Half Joker' and len(cards)<=3:mult+=20
  if n=='Banner':chips+=30*self.discards
  if n=='Mystic Summit' and self.discards==0:mult+=15
  if n=='Abstract Joker':mult+=3*len(self.jokers)
  if n=='Misprint':mult+=self.rng.randint(0,23)
  if n=='Raised Fist' and len(self.hand)>len(cards):mult+=2*min(c.chips() for c in self.hand if c not in cards)
  if n=='Supernova':mult+=self.history[k]
  if n in ('Ride the Bus','Green Joker','Swashbuckler','Fortune Teller'):mult+= {'Ride the Bus':self.joker_state.get(n,0),'Green Joker':self.joker_state.get(n,0),'Swashbuckler':sum(j.get('sell',2) for j in self.jokers if j['name']!=n),'Fortune Teller':self.tarot_uses}[n]
  if n in ('Square Joker','Runner','Ice Cream','Bull','Stone Joker','Erosion'):
   chips+= {'Square Joker':self.joker_state.get(n,0),'Runner':self.joker_state.get(n,0),'Ice Cream':self.joker_state.get(n,100),'Bull':2*max(0,self.money),'Stone Joker':25*sum(c.enhancement=='Stone' for c in self.deck),'Erosion':4*max(0,52-len(self.deck))}[n]
  if n=='Ice Cream':self.joker_state[n]=max(0,self.joker_state.get(n,100)-5)
  if n=='Popcorn':mult+=self.joker_state.get(n,20)
  if n=='Bootstraps':mult+=2*max(0,self.money//5)
  if n=='Photograph' and any(c.rank in ('J','Q','K') for c in scored):mult*=2
  if n=='Card Sharp' and self.round_history[k]>1:mult*=3
  if n in ('The Duo','The Trio','The Family','The Order','The Tribe'):
   needed={'The Duo':'Pair','The Trio':'Three of a Kind','The Family':'Four of a Kind','The Order':'Straight','The Tribe':'Flush'}[n]
   if needed in k:mult*= {'The Duo':2,'The Trio':3,'The Family':4,'The Order':3,'The Tribe':2}[n]
  if n=='Cavendish':mult*=3
  if n=='Ramen':mult*=self.joker_state.get(n,2)
  if n=='Blackboard' and all(c.suit in ('♠','♣') for c in self.hand if c not in cards):mult*=3
  if n=='Baseball Card':mult*=1.5**sum(LOOKUP.get(j['name'],LOOKUP['Joker']).rarity=='Uncommon' for j in self.jokers if j['name']!=n)
  if n=='Constellation':mult*=self.joker_state.get(n,1)
  if n=='Hologram':mult*=1+.25*self.added_cards
  if n=='Steel Joker':mult*=1.2**sum(c.enhancement=='Steel' for c in self.deck)
  if n=='Glass Joker':mult*=1.5**self.destroyed_glass
  if n=='Flower Pot' and len({c.suit for c in scored})==4:mult*=3
  if n=='Seeing Double' and '♣' in {c.suit for c in scored} and len({c.suit for c in scored})>=2:mult*=2
  if n=='Acrobat' and self.hands==0:mult*=3
  if n=='Joker Stencil':mult*=max(1,self.joker_slots-len(self.jokers)+1)
  if n=='Loyalty Card' and sum(self.history.values())%6==0:mult*=4
  if n=='Throwback':mult*=1+.25*self.skip_count
  return chips,mult
 def win_blind(self):
  reward=[3,4,5][self.blind];self.money+=reward+max(0,self.hands)+min(5,max(0,self.money)//5)
  for n in self.names():
   if n=='Golden Joker':self.money+=4
   if n=='Cloud 9':self.money+=sum(c.rank=='9' for c in self.deck)
   if n=='To the Moon':self.money+=max(0,self.money//5)
   if n=='Delayed Gratification':self.money+=2*self.discards
   if n=='Popcorn':self.joker_state[n]=max(0,self.joker_state.get(n,20)-4)
   if n=='Egg':
    for j in self.jokers:
     if j['name']==n:j['sell']=j.get('sell',2)+3
  self.state='shop';self.generate_shop();self.note(f'Blind cleared! Earned ${reward} plus bonuses.')
 def generate_shop(self):
  self.shop=[]
  for _ in range(2):
   j=self.rng.choice(JOKERS);self.shop.append({'type':'Joker','name':j.name,'cost':j.cost})
  for _ in range(2):
   t=self.rng.choice(['Planet','Tarot','Spectral']);name=self.rng.choice(list(HANDS) if t=='Planet' else TAROTS if t=='Tarot' else SPECTRALS)
   self.shop.append({'type':t,'name':name,'cost':3 if t!='Spectral' else 4})
 def reroll(self):
  if self.state!='shop':raise ValueError('Not in shop.')
  price=5+self.joker_state.get('rerolls',0)
  if self.money<price:raise ValueError(f'Need ${price}.')
  self.money-=price;self.joker_state['rerolls']=self.joker_state.get('rerolls',0)+1;self.generate_shop()
 def buy(self,index):
  if self.state!='shop':raise ValueError('Not in shop.')
  if not 0<=index<len(self.shop):raise ValueError('Invalid item.')
  item=self.shop[index]
  if self.money<item['cost'] and not(self.has('Credit Card') and self.money-item['cost']>=-20):raise ValueError('Not enough money.')
  if item['type']=='Joker' and len(self.jokers)>=self.joker_slots:raise ValueError('Joker slots full.')
  if item['type']!='Joker' and len(self.consumables)>=self.consumable_slots:raise ValueError('Consumable slots full.')
  self.money-=item['cost']
  if item['type']=='Joker':self.jokers.append({'name':item['name'],'sell':max(1,item['cost']//2)})
  else:self.consumables.append({'type':item['type'],'name':item['name']})
  self.shop.pop(index);self.note('Bought '+item['name'])
 def sell_joker(self,index):
  if not 0<=index<len(self.jokers):raise ValueError('Invalid Joker.')
  j=self.jokers.pop(index);self.money+=j.get('sell',2);self.note('Sold '+j['name'])
 def use(self,index,targets=None):
  if not 0<=index<len(self.consumables):raise ValueError('Invalid consumable.')
  item=self.consumables[index];name=item['name'];typ=item['type'];targets=targets or []
  if typ=='Planet':self.levels[name]+=1;self.planet_uses+=1
  elif typ=='Tarot':
   self.tarot_uses+=1
   if name=='The Hermit':self.money+=min(20,max(0,self.money))
   elif name=='Temperance':self.money+=min(50,sum(j.get('sell',2) for j in self.jokers))
   elif name=='The High Priestess':self.add_consumable('Planet')
   elif name=='The Emperor':self.add_consumable('Tarot')
   elif name=='Judgement':
    if len(self.jokers)<self.joker_slots:self.jokers.append({'name':self.rng.choice(JOKERS).name,'sell':2})
   elif name=='Strength':
    for i in targets[:2]:self.hand[i].rank=RANKS[(RANKS.index(self.hand[i].rank)+1)%13]
   elif name=='The Hanged Man':
    for i in sorted(set(targets[:2]),reverse=True):self.remove_deck_card(self.hand[i]);self.hand.pop(i)
   elif name=='Death' and len(targets)>=2:self.hand[targets[0]].rank=self.hand[targets[1]].rank;self.hand[targets[0]].suit=self.hand[targets[1]].suit
   elif name in ('The Star','The Moon','The Sun','The World'):
    suit={'The Star':'♦','The Moon':'♣','The Sun':'♥','The World':'♠'}[name]
    for i in targets[:3]:self.hand[i].suit=suit
   elif name in ('The Magician','The Empress','The Hierophant','The Lovers','The Chariot','Justice','The Devil','The Tower'):
    enh={'The Magician':'Lucky','The Empress':'Mult','The Hierophant':'Bonus','The Lovers':'Wild','The Chariot':'Steel','Justice':'Glass','The Devil':'Gold','The Tower':'Stone'}[name]
    for i in targets[:2]:self.hand[i].enhancement=enh
   elif name=='The Wheel of Fortune' and self.jokers and self.rng.random()<.25:self.rng.choice(self.jokers)['edition']='Polychrome'
   elif name=='The Fool':self.add_consumable('Tarot')
  elif typ=='Spectral':
   if name=='Wraith' and len(self.jokers)<self.joker_slots:self.jokers.append({'name':self.rng.choice([j for j in JOKERS if j.rarity=='Rare']).name,'sell':4});self.money=0
   elif name=='Immolate':
    for i in sorted(self.rng.sample(range(len(self.hand)),min(5,len(self.hand))),reverse=True):self.remove_deck_card(self.hand[i]);self.hand.pop(i)
    self.money+=20
   elif name=='Cryptid' and targets:
    for _ in range(2):self.deck.append(Card.from_dict(self.hand[targets[0]].to_dict()));self.added_cards+=1
   elif name=='Ankh' and self.jokers:
    j=self.rng.choice(self.jokers);self.jokers=[j.copy(),j.copy()][:self.joker_slots]
   elif name=='Hex' and self.jokers:
    j=self.rng.choice(self.jokers);self.jokers=[j];j['edition']='Polychrome'
   elif name in ('Deja Vu','Trance','Medium','Talisman'):
    for i in targets[:1]:self.hand[i].seal={'Deja Vu':'Red','Trance':'Blue','Medium':'Purple','Talisman':'Gold'}[name]
   elif name=='Aura':
    for i in targets[:1]:self.hand[i].edition=self.rng.choice(['Foil','Holographic','Polychrome'])
   elif name=='Sigil':
    suit=self.rng.choice(SUITS)
    for c in self.hand:c.suit=suit
   elif name=='Ouija':
    rank=self.rng.choice(RANKS)
    for c in self.hand:c.rank=rank
    self.hand_size=max(1,self.hand_size-1)
  self.consumables.pop(index);self.note('Used '+name)
 def add_consumable(self,typ):
  if len(self.consumables)<self.consumable_slots:self.consumables.append({'type':typ,'name':self.rng.choice(list(HANDS) if typ=='Planet' else TAROTS)})
 def next_blind(self):
  if self.state not in ('shop','blind'):raise ValueError('Cannot advance.')
  if self.state=='blind':self.skip_count+=1
  self.blind+=1
  if self.blind==3:self.blind=0;self.ante+=1
  if self.ante>=9 and not self.won:self.won=True;self.note('Ante 8 cleared! Victory! Endless mode unlocked.')
  self.choose_blind()
 def save(self,path=SAVE):
  data={k:v for k,v in vars(self).items() if k not in ('rng','deck','draw_pile','hand','discard_pile','history','round_history')}
  data['deck']=[c.to_dict() for c in self.deck];data['draw_pile']=[c.to_dict() for c in self.draw_pile];data['hand']=[c.to_dict() for c in self.hand];data['discard_pile']=[c.to_dict() for c in self.discard_pile]
  data['history']=dict(self.history);data['round_history']=dict(self.round_history);data['vouchers']=list(self.vouchers)
  data['rng_state']=repr(self.rng.getstate())
  path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
 @classmethod
 def load(cls,path=SAVE):
  import ast
  d=json.loads(pathlib.Path(path).read_text(encoding='utf8'));obj=cls(d.get('seed'))
  for k,v in d.items():
   if k in ('deck','draw_pile','hand','discard_pile'):setattr(obj,k,[Card.from_dict(c) for c in v])
   elif k in ('history','round_history'):setattr(obj,k,Counter(v))
   elif k=='vouchers':obj.vouchers=set(v)
   elif k=='rng_state':obj.rng.setstate(ast.literal_eval(v))
   else:setattr(obj,k,v)
  return obj
