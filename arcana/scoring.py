"""Independent ordered scorer: played cards -> held cards -> Joker row -> vouchers."""
from .cards import RANKS
from .content import LOOKUP

def effective(g,idx,seen=None):
    seen=set() if seen is None else seen
    if idx<0 or idx>=len(g.jokers) or idx in seen:return None
    seen.add(idx)
    n=g.jokers[idx]['name']
    if n=='Blueprint':return effective(g,idx+1,seen)
    if n=='Brainstorm':return effective(g,0,seen)
    return n

def all_effects(g):
    for i,j in enumerate(g.jokers):
        if not j.get('debuff') and not j.get('debuff_round'):
            n=effective(g,i)
            if n:yield i,n

def count(g,n):return sum(name==n for _,name in all_effects(g))

def is_face(g,c):return c.rank in ('J','Q','K') or g.has('Pareidolia')

def prob(g,n):return g.rng.random()<min(1,1/n*(2 if g.has('Oops! All 6s') else 1))

def add_state(g,name,amount,default=0):
    g.joker_state[name]=g.joker_state.get(name,default)+amount

def times(g, mult, factor):
    """Multiply Mult, recording the factor for the transparent score breakdown."""
    g._score_x *= factor
    return mult * factor


def score_hand(g,kind,cards,scored):
    """Returns (chips,mult,score) and applies triggered card effects to Game."""
    chips,mult,chip_inc,mult_inc=g.hands_data[kind]
    chips+=chip_inc*(g.levels[kind]-1);mult+=mult_inc*(g.levels[kind]-1)
    if g.boss_active('The Flint'):chips=max(1,chips//2);mult=max(1,mult//2)
    # The Flint debuff modifies the base before any card or Joker bonuses.
    base_chips, base_mult = chips, mult
    g._score_x = 1.0
    if g.has('Splash'):scored=cards
    # Stone cards contribute their +50 chips regardless of the detected poker hand.
    scored=list(scored)
    for c in cards:
        if c.enhancement=='Stone' and not any(x.uid==c.uid for x in scored):scored.append(c)
    if g.has('Space Joker') and prob(g,4):g.levels[kind]+=1;g.note('太空小丑：牌型等级+1')
    if g.has('DNA') and g.round_history.total()==1 and len(cards)==1:
        new=cards[0].clone();g.deck.append(new);g.draw_pile.insert(0,new.clone());g.added_cards+=1;g.note('DNA：复制一张牌')
    if g.has('Sixth Sense') and g.round_history.total()==1 and len(cards)==1 and cards[0].rank=='6':
        g.remove_deck_card(cards[0]);g.add_consumable('Spectral');g.note('第六感：将6转化为幻灵牌')
    if g.has('Square Joker') and len(cards)==4:add_state(g,'Square Joker',4)
    if g.has('Runner') and 'Straight' in kind:add_state(g,'Runner',15)
    if g.has('Spare Trousers') and 'Two Pair' in kind:add_state(g,'Spare Trousers',2)
    if g.has('Green Joker'):add_state(g,'Green Joker',1)
    if g.has('Ride the Bus'):
        if any(is_face(g,c) and not g.debuff(c) for c in scored):g.joker_state['Ride the Bus']=0
        else:add_state(g,'Ride the Bus',1)
    if g.has('Obelisk'):
        prevmax=max((v for k,v in g.history.items() if k!=kind),default=0)
        if g.history[kind]>prevmax:g.joker_state['Obelisk']=1.0
        else:add_state(g,'Obelisk',.2,1.0)
    if g.has('Vagabond') and g.money<=4:g.add_consumable('Tarot')
    if g.has('Séance') and 'Straight Flush' in kind:g.add_consumable('Spectral')
    if g.has('Superposition') and 'Straight' in kind and any(c.rank=='A' for c in cards):g.add_consumable('Tarot')
    if g.has('To Do List') and kind==g.joker_state.get('todo','Pair'):g.money+=4
    if g.has('Midas Mask'):
        for c in scored:
            if not g.debuff(c) and is_face(g,c):c.enhancement='Gold';g.commit_card(c)
    if g.has('Vampire'):
        for c in scored:
            if not g.debuff(c) and c.enhancement and c.enhancement!='Stone':c.enhancement='';add_state(g,'Vampire',.1,1.0);g.commit_card(c)
    first_face=False
    for card_idx,c in enumerate(scored):
        if g.debuff(c):continue
        face=is_face(g,c)
        triggers=1+(c.seal=='Red')
        for _,n in all_effects(g):
            if n=='Hanging Chad' and card_idx==0:triggers+=2
            if n=='Dusk' and g.hands==0:triggers+=1
            if n=='Hack' and c.rank in ('2','3','4','5'):triggers+=1
            if n=='Sock and Buskin' and face:triggers+=1
            if n=='Seltzer' and g.joker_state.get('Seltzer',10)>0:triggers+=1
        for _ in range(triggers):
            if c.enhancement!='Stone':chips+=c.chips()+c.bonus
            if c.enhancement=='Bonus':chips+=30
            if c.enhancement=='Stone':chips+=50
            if c.enhancement=='Mult':mult+=4
            if c.enhancement=='Glass':mult = times(g, mult, 2)
            if c.edition=='Foil':chips+=50
            if c.edition=='Holographic':mult+=10
            if c.edition=='Polychrome':mult = times(g, mult, 1.5)
            if c.seal=='Gold':g.money+=3
            for i,n in all_effects(g):
                if n=='Greedy Joker' and c.suit=='♦' or n=='Lusty Joker' and c.suit=='♥' or n=='Wrathful Joker' and c.suit=='♠' or n=='Gluttonous Joker' and c.suit=='♣':mult+=3
                elif n=='Even Steven' and c.rank in ('2','4','6','8','10'):mult+=4
                elif n=='Odd Todd' and c.rank in ('A','3','5','7','9'):chips+=31
                elif n=='Fibonacci' and c.rank in ('A','2','3','5','8'):mult+=8
                elif n=='Scholar' and c.rank=='A':chips+=20;mult+=4
                elif n=='Scary Face' and face:chips+=30
                elif n=='Smiley Face' and face:mult+=5
                elif n=='Arrowhead' and c.suit=='♠':chips+=50
                elif n=='Onyx Agate' and c.suit=='♣':mult+=7
                elif n=='Bloodstone' and c.suit=='♥' and prob(g,2):mult = times(g, mult, 1.5)
                elif n=='Rough Gem' and c.suit=='♦':g.money+=1
                elif n=='Walkie Talkie' and c.rank in ('10','4'):chips+=10;mult+=4
                elif n=='Triboulet' and c.rank in ('K','Q'):mult = times(g, mult, 2)
                elif n=='Ancient Joker' and c.suit==g.joker_state.get('ancient_suit','♥'):mult = times(g, mult, 1.5)
                elif n=='Photograph' and face and not first_face:mult = times(g, mult, 2)
                elif n=='The Idol' and (c.rank,c.suit)==tuple(g.joker_state.get('idol',('A','♥'))):mult = times(g, mult, 2)
                elif n=='Wee Joker' and c.rank=='2':add_state(g,'Wee Joker',8)
                elif n=='Business Card' and face and prob(g,2):g.money+=2
                elif n=='8 Ball' and c.rank=='8' and prob(g,4):g.add_consumable('Tarot')
                elif n=='Golden Ticket' and c.enhancement=='Gold':g.money+=4
                elif n=='Hiker':c.bonus+=5;g.commit_card(c)
            if c.enhancement=='Lucky':
                if prob(g,5):mult+=20;add_state(g,'Lucky Cat',.25,1.0)
                if prob(g,15):g.money+=20
        if face:first_face=True
        if c.enhancement=='Glass' and prob(g,4):g.remove_deck_card(c);g.destroyed_glass+=1;add_state(g,'Glass Joker',.75,1.0)
    held=[c for c in g.hand if c.uid not in {x.uid for x in cards}]
    for c in held:
        if g.debuff(c):continue
        repeats=1+(c.seal=='Red')+count(g,'Mime')
        for _ in range(repeats):
            if c.enhancement=='Steel':mult = times(g, mult, 1.5)
            for _,n in all_effects(g):
                if n=='Baron' and c.rank=='K':mult = times(g, mult, 1.5)
                elif n=='Shoot the Moon' and c.rank=='Q':mult+=13
                elif n=='Reserved Parking' and is_face(g,c) and prob(g,2):g.money+=1
            if c.enhancement=='Gold':pass   # Gold pays out at round end
    # Independent Joker resolution, left-to-right; editions applied per physical Joker.
    for idx,j in enumerate(g.jokers):
        if j.get('debuff') or j.get('debuff_round'):continue
        n=effective(g,idx)
        if not n:continue
        if j.get('edition')=='Foil':chips+=50
        if j.get('edition')=='Holographic':mult+=10
        chips,mult=_independent(g,n,kind,cards,scored,held,chips,mult)
        if LOOKUP.get(j['name']) and LOOKUP[j['name']].rarity=='Uncommon':
            mult = times(g, mult, 1.5**count(g,'Baseball Card'))
        if j.get('edition')=='Polychrome':mult = times(g, mult, 1.5)
    if 'Observatory' in g.vouchers:
        mult = times(g, mult, 1.5**sum(c['type']=='Planet' and c['name']==kind for c in g.consumables))
    if g.deck_name=='Plasma Deck':
        # Plasma balances the fully resolved chips and Mult after all modifiers.
        balance_base=(base_chips+base_mult)/2
        chips=mult=(chips+mult)/2
        g._score_breakdown={
            'base_chips':balance_base, 'bonus_chips':chips-balance_base,
            'base_mult':balance_base, 'bonus_mult':mult-balance_base,
            'xmult':1.0, 'special':'等离子牌组：结算结束后，筹码和倍率取均值',
        }
    else:
        factor=g._score_x
        g._score_breakdown={
            'base_chips':base_chips,'bonus_chips':chips-base_chips,
            # Later +Mult effects are normalized to the combined XMult factor,
            # so the displayed product faithfully matches the resolved Mult.
            'base_mult':base_mult,'bonus_mult':mult/factor-base_mult if factor else 0,
            'xmult':factor,
        }
    result=int(max(0,chips)*max(0,mult))
    if g.has('Ice Cream'):g.joker_state['Ice Cream']=max(0,g.joker_state.get('Ice Cream',100)-5)
    if g.has('Seltzer'):
        v=g.joker_state.get('Seltzer',10)-1;g.joker_state['Seltzer']=v
        if v<=0:g.remove_joker_by_name('Seltzer')
    return chips,mult,result

def _independent(g,n,k,cards,scored,held,chips,mult):
    has=lambda phrase:phrase in k or phrase in g.composites(k)
    mcond={'Jolly Joker':('Pair',8),'Zany Joker':('Three of a Kind',12),'Mad Joker':('Two Pair',10),'Crazy Joker':('Straight',12),'Droll Joker':('Flush',10)}
    ccond={'Sly Joker':('Pair',50),'Wily Joker':('Three of a Kind',100),'Clever Joker':('Two Pair',80),'Devious Joker':('Straight',100),'Crafty Joker':('Flush',80)}
    if n in mcond and has(mcond[n][0]):mult+=mcond[n][1]
    if n in ccond and has(ccond[n][0]):chips+=ccond[n][1]
    if n=='Joker':mult+=4
    elif n=='Half Joker' and len(cards)<=3:mult+=20
    elif n=='Banner':chips+=30*g.discards
    elif n=='Mystic Summit' and g.discards==0:mult+=15
    elif n=='Abstract Joker':mult+=3*len(g.jokers)
    elif n=='Misprint':mult+=g.rng.randint(0,23)
    elif n=='Raised Fist' and held:mult+=2*min(c.chips() for c in held)
    elif n=='Supernova':mult+=g.history[k]
    elif n in ('Ride the Bus','Green Joker','Spare Trousers','Flash Card','Ceremonial Dagger'):
        mult+=g.joker_state.get(n,0)
    elif n=='Swashbuckler':mult+=sum(j.get('sell',2) for j in g.jokers if j['name']!=n)
    elif n=='Fortune Teller':mult+=g.tarot_uses
    elif n=='Square Joker':chips+=g.joker_state.get(n,0)
    elif n=='Runner':chips+=g.joker_state.get(n,0)
    elif n=='Ice Cream':chips+=g.joker_state.get(n,100)
    elif n=='Blue Joker':chips+=2*len(g.draw_pile)
    elif n=='Wee Joker':chips+=g.joker_state.get(n,0)
    elif n=='Castle':chips+=g.joker_state.get(n,0)
    elif n=='Bull':chips+=2*max(0,g.money)
    elif n=='Stone Joker':chips+=25*sum(c.enhancement=='Stone' for c in g.deck)
    elif n=='Erosion':mult+=4*max(0,52-len(g.deck))
    elif n=='Bootstraps':mult+=2*max(0,g.money//5)
    elif n=='Popcorn':mult+=g.joker_state.get(n,20)
    elif n=='Red Card':mult+=g.joker_state.get(n,0)
    elif n=='Gros Michel':mult+=15
    elif n=='Photograph':pass # On-scored only
    elif n=='Card Sharp' and g.round_history[k]>1:mult = times(g, mult, 3)
    elif n=='Blackboard' and all(c.suit in ('♠','♣') for c in held):mult = times(g, mult, 3)
    elif n=='Cavendish':mult = times(g, mult, 3)
    elif n=='Ramen':mult = times(g, mult, g.joker_state.get(n,2))
    elif n=='Steel Joker':mult = times(g, mult, 1+.2*sum(c.enhancement=='Steel' for c in g.deck))
    elif n=='Glass Joker':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Constellation':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Hologram':mult = times(g, mult, 1+.25*g.added_cards)
    elif n=='Vampire':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Lucky Cat':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Obelisk':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Madness':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Campfire':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Canio':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Yorick':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Hit the Road':mult = times(g, mult, g.joker_state.get(n,1))
    elif n=='Throwback':mult = times(g, mult, 1+.25*g.skip_count)
    elif n=='Joker Stencil':mult = times(g, mult, max(1,g.joker_slots-len([j for j in g.jokers if j.get('edition')!='Negative'])+1))
    elif n=='Acrobat' and g.hands==0:mult = times(g, mult, 3)
    elif n=='Loyalty Card' and g.history.total()%6==0:mult = times(g, mult, 4)
    elif n=='Flower Pot' and len({c.suit for c in scored})==4:mult = times(g, mult, 3)
    elif n=='Seeing Double' and '♣' in {c.suit for c in scored} and len({c.suit for c in scored})>=2:mult = times(g, mult, 2)
    elif n=="Driver's License" and sum(bool(c.enhancement) for c in g.deck)>=16:mult = times(g, mult, 3)
    elif n in ('The Duo','The Trio','The Family','The Order','The Tribe'):
        need,factor={'The Duo':('Pair',2),'The Trio':('Three of a Kind',3),'The Family':('Four of a Kind',4),'The Order':('Straight',3),'The Tribe':('Flush',2)}[n]
        if has(need):mult = times(g, mult, factor)
    elif n=='Stuntman':chips+=250
    return chips,mult
