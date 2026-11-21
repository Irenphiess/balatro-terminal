import unittest,tempfile,pathlib,random
from arcana.game import Game
from arcana.cards import Card
from arcana.poker import analyze,HANDS
from arcana.content import JOKERS,VOUCHERS,PACK_CONFIG,PACK_SIZES,RARITY
from arcana.ui import content,card_art,ESC,wid

class TestTerminalArcana(unittest.TestCase):
 def test_catalog(self):
  self.assertEqual(len(JOKERS),150)
  self.assertEqual(len(set(j.name for j in JOKERS)),150)
  self.assertEqual(len(VOUCHERS),32)
  self.assertEqual(len(PACK_CONFIG)*len(PACK_SIZES),15)
  self.assertEqual(sum(j.rarity=='Rare' for j in JOKERS),20)
 def test_cards_and_colours(self):
  for suit in '♥♦♠♣':
   lines=card_art(Card('10',suit),1)
   self.assertEqual(len(lines),6)
   self.assertTrue(all(wid(x)==11 for x in lines))
   self.assertIn(suit,''.join(lines))
 def test_scoring(self):
  cs=[Card(r,'♥') for r in ('10','J','Q','K','A')]
  self.assertEqual(analyze(cs)[0],'Straight Flush')
  self.assertEqual(analyze([Card('2','♥'),Card('2','♠'),Card('3','♦')])[0],'Pair')
  self.assertEqual(analyze([Card(r,'♠') for r in ('2','4','6','8','10')])[0],'Flush')
 def test_game_play_and_shop(self):
  g=Game(19)
  self.assertEqual(g.target,300)
  self.assertTrue(g.start_blind());self.assertEqual(len(g.hand),8)
  points=g.play([0,1,2])
  self.assertGreaterEqual(points['points'],1)
  g.score=g.target-1
  g.play([0,1,2]);self.assertEqual(g.state,'shop')
  self.assertEqual(len(g.packs),2)
  self.assertIsNotNone(g.shop_voucher)
  g.money=100
  g.buy_voucher();self.assertEqual(len(g.vouchers),1)
  g.open_pack(0);self.assertEqual(g.state,'pack')
  self.assertTrue(g.pack['options'])
  g.skip_pack();self.assertEqual(g.state,'shop')
  g.next_blind();self.assertEqual(g.blind,1)
 def test_endless(self):
  g=Game(42)
  targets=[]
  for ante in (8,9,10,11,12,13):
   g.ante=ante;g.blind=0;g.choose_blind();targets.append(g.target)
  self.assertEqual(targets,[50000,110000,560000,7200000,300000000,47000000000])
 def test_joker_copy_scoring(self):
  g=Game(2)
  g.jokers=[g.make_joker('Blueprint'),g.make_joker('Joker')]
  g.start_blind();v=g.play([0])
  self.assertGreater(v['mult'],8) # both Joker and Blueprint additive
 def test_save_load(self):
  g=Game(5);g.start_blind();g.jokers=[g.make_joker('Joker')]
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t)/'save.json';g.save(p);other=Game.load(p)
   self.assertEqual(other.ante,1);self.assertEqual(other.state,'play')
   self.assertEqual(other.jokers[0]['name'],'Joker')
   self.assertEqual(other.deck[0].uid,g.deck[0].uid)
 def test_every_pack_family(self):
  for typ in PACK_CONFIG:
   g=Game(5);g.state='shop';g.money=999
   g.packs=[{'kind':typ,'size':'Mega','cost':8}]
   g.open_pack(0)
   self.assertEqual(g.state,'pack')
   self.assertEqual(g.pack['kind'],typ)
   if typ=='Standard':
    before=len(g.deck);g.select_pack(0);self.assertEqual(len(g.deck),before+1)
   if typ=='Celestial':
    chosen=g.pack['options'][0]['name'];level=g.levels[chosen]
    g.select_pack(0);self.assertEqual(g.levels[chosen],level+1)
   g.skip_pack()
 def test_many_random_hands(self):
  for seed in range(100):
   g=Game(seed)
   g.start_blind()
   for _ in range(4):
    if g.state!='play':break
    g.play(list(range(min(5,len(g.hand)))))
   self.assertIn(g.state,('lost','shop'))
 def test_zh_centered_output(self):
  g=Game(7)
  lines=content(g)
  self.assertTrue(any('小 丑 区' in x for x in lines))

if __name__=='__main__':unittest.main()
