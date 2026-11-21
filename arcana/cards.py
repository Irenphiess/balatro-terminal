from dataclasses import dataclass,field
import random,uuid
SUITS=('♠','♥','♣','♦')
RANKS=('2','3','4','5','6','7','8','9','10','J','Q','K','A')
@dataclass
class Card:
    rank:str
    suit:str
    enhancement:str=''
    edition:str=''
    seal:str=''
    bonus:int=0
    uid:str=field(default_factory=lambda:uuid.uuid4().hex[:14])
    def chips(self):
        return 11 if self.rank=='A' else min(10,int(self.rank)) if self.rank.isdigit() else 10
    def label(self):return f'{self.rank}{self.suit}'+(f'[{self.enhancement}]' if self.enhancement else '')
    def to_dict(self):return vars(self).copy()
    @classmethod
    def from_dict(cls,d):return cls(**d)
    def clone(self):
        d=self.to_dict();d.pop('uid',None);return Card(**d)
def deck():return [Card(r,s) for s in SUITS for r in RANKS]
def draw(cards,n,rng=random):
    return [cards.pop(rng.randrange(len(cards))) for _ in range(min(n,len(cards)))]
