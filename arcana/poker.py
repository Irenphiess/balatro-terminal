"""Poker evaluator; hand detection is deterministic and independent of UI."""
from collections import Counter
from .cards import RANKS
HANDS={
 'High Card':(5,1,10,1),'Pair':(10,2,15,1),'Two Pair':(20,2,20,1),
 'Three of a Kind':(30,3,20,2),'Straight':(30,4,30,3),'Flush':(35,4,15,2),
 'Full House':(40,4,25,2),'Four of a Kind':(60,7,30,3),
 'Straight Flush':(100,8,40,4),'Five of a Kind':(120,12,35,3),
 'Flush House':(140,14,40,4),'Flush Five':(160,16,50,3)}
PLANETS={'High Card':'Pluto','Pair':'Mercury','Two Pair':'Uranus','Three of a Kind':'Venus','Straight':'Saturn','Flush':'Jupiter','Full House':'Earth','Four of a Kind':'Mars','Straight Flush':'Neptune','Five of a Kind':'Planet X','Flush House':'Ceres','Flush Five':'Eris'}
HAND_ZH=dict(zip(HANDS,'高牌|对子|两对|三条|顺子|同花|葫芦|四条|同花顺|五条|同花葫芦|同花五条'.split('|')))
PLANET_ZH=dict(zip(HANDS,'冥王星|水星|天王星|金星|土星|木星|地球|火星|海王星|X行星|谷神星|阋神星'.split('|')))
def _straight(values,need,shortcut):
    vals=sorted(set(values));vals=[1]+vals if 14 in vals else vals
    for combo in __import__('itertools').combinations(vals,need):
        diffs=[b-a for a,b in zip(combo,combo[1:])]
        if diffs and all(1<=d<=(2 if shortcut else 1) for d in diffs):
            return set(combo)
    return set()
def analyze(cards,shortcut=False,four_fingers=False,smeared=False):
    if not cards: return 'High Card',[]
    ranks=Counter(c.rank for c in cards if c.enhancement!='Stone')
    suits=Counter(('red' if c.suit in ('♥','♦') else 'black') if smeared else c.suit for c in cards if c.enhancement!='Stone')
    need=4 if four_fingers else 5
    wild=[c for c in cards if c.enhancement=='Wild']
    normal=[c for c in cards if c.enhancement!='Wild']
    flush_suits=[s for s in ('♠','♥','♣','♦') if sum(c.suit==s or c.enhancement=='Wild' or (smeared and ((s in '♥♦' and c.suit in '♥♦') or (s in '♠♣' and c.suit in '♠♣'))) for c in cards)>=need]
    flush=bool(flush_suits)
    def straight_cards(seq):
        vals=[RANKS.index(c.rank)+2 for c in seq if c.enhancement!='Stone']
        return _straight(vals,need,shortcut)
    st=straight_cards(cards)
    straight=bool(st)
    groups=sorted(ranks.values(),reverse=True)
    if not groups:groups=[0]
    if flush and groups[0]>=5:kind='Flush Five'
    elif flush and groups[0]>=3 and len(groups)>1 and groups[1]>=2:kind='Flush House'
    elif groups[0]>=5:kind='Five of a Kind'
    elif flush and straight and (four_fingers or any(straight_cards([c for c in cards if c.suit==s or c.enhancement=='Wild' or (smeared and ((s in '♥♦' and c.suit in '♥♦') or (s in '♠♣' and c.suit in '♠♣')))]) for s in flush_suits)):kind='Straight Flush'
    elif groups[0]>=4:kind='Four of a Kind'
    elif groups[0]>=3 and len(groups)>1 and groups[1]>=2:kind='Full House'
    elif flush:kind='Flush'
    elif straight:kind='Straight'
    elif groups[0]>=3:kind='Three of a Kind'
    elif sum(x>=2 for x in groups)>=2:kind='Two Pair'
    elif groups[0]>=2:kind='Pair'
    else:kind='High Card'
    if kind in ('Straight','Straight Flush'):
        if kind=='Straight Flush':
            for s in flush_suits:
                seq=[c for c in cards if c.suit==s or c.enhancement=='Wild'];ss=straight_cards(seq)
                if ss:return kind,[c for c in seq if RANKS.index(c.rank)+2 in ss or (c.rank=='A' and 1 in ss)][:5]
            if four_fingers:return kind,list(cards)[:5]
        return kind,[c for c in cards if RANKS.index(c.rank)+2 in st or (c.rank=='A' and 1 in st)][:5]
    if kind=='Flush':return kind,[c for c in cards if c.suit==flush_suits[0] or c.enhancement=='Wild'][:5]
    if kind=='High Card':return kind,[max(cards,key=lambda c:RANKS.index(c.rank))]
    if kind in ('Full House','Flush House','Two Pair'):
        order=sorted((r for r,n in ranks.items() if n>=2),key=lambda r:(ranks[r],RANKS.index(r)),reverse=True)
        return kind,[c for c in cards if c.rank in order[:2]][:5]
    target=max(ranks,key=lambda r:(ranks[r],RANKS.index(r))) if ranks else cards[0].rank
    return kind,[c for c in cards if c.rank==target][:5]
