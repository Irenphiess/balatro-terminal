import io,sys,unittest,tempfile,pathlib
from contextlib import redirect_stdout
from arcana.decks import DECKS,STAKES,curve
from arcana.game import Game
from arcana.cards import Card
from arcana.tui import Canvas,UI,Renderer,SUIT,THEMES
from arcana.poker import HANDS
from play import Controller

class V3(unittest.TestCase):
 def test_all_decks_and_stakes_create(self):
  for d in DECKS:
   for s in STAKES:
    g=Game.new_run(d.key,s[0],seed=2)
    self.assertEqual(g.deck_name,d.key)
    self.assertEqual(g.stake,s[0]);self.assertGreater(g.target,0)
    g.start_blind();self.assertEqual(g.state,'play')
 def test_decks(self):
  x=lambda key:Game.new_run(key,seed=1)
  self.assertEqual(x('Red Deck').max_discards,4)
  self.assertEqual(x('Blue Deck').max_hands,5)
  self.assertEqual(x('Yellow Deck').money,14)
  self.assertEqual(x('Black Deck').joker_slots,6)
  self.assertEqual(x('Black Deck').max_hands,3)
  self.assertEqual(x('Abandoned Deck').deck.__len__(),40)
  self.assertEqual({c.suit for c in x('Checkered Deck').deck},{'♥','♠'})
  self.assertEqual(len(x('Erratic Deck').deck),52)
  self.assertEqual(x('Painted Deck').hand_size,10)
  self.assertEqual(x('Nebula Deck').consumable_slots,1)
  self.assertEqual(len(x('Magic Deck').consumables),2)
 def test_stakes(self):
  self.assertEqual(curve('White')[7],50_000)
  self.assertEqual(curve('Green')[7],100_000)
  self.assertEqual(curve('Purple')[7],200_000)
  self.assertEqual(Game.new_run('Red Deck','Red',1).max_discards,4)
  self.assertEqual(Game.new_run('Red Deck','Blue',1).max_discards,3)
  g=Game.new_run('Red Deck','Gold',1)
  d=[g.sticker_fields({'type':'Joker','name':'Joker','cost':4}) for _ in range(1000)]
  self.assertTrue(any('rental' in a for a in d))
  self.assertTrue(any('perishable' in a for a in d))
  self.assertTrue(any('eternal' in a for a in d))
  self.assertFalse(any('eternal' in a and 'perishable' in a for a in d))
 def test_sort(self):
  g=Game.new_run(seed=2)
  g.hand=[Card('2','♣'),Card('3','♥'),Card('A','♥'),Card('K','♠'),Card('10','♦')]
  g.sort_hand()
  self.assertEqual([(c.rank,c.suit) for c in g.hand],[('3','♥'),('A','♥'),('10','♦'),('K','♠'),('2','♣')])
 def test_glass_scoring_and_stone(self):
  g=Game.new_run(seed=4);g.start_blind()
  g.hand=[Card('5','♣',enhancement='Stone'),Card('3','♠')]
  from arcana.scoring import score_hand
  kind='High Card'
  chips,mult,res=score_hand(g,kind,g.hand[:],g.hand[1:])
  self.assertGreaterEqual(chips,55)
  g=Game.new_run(seed=4);g.start_blind()
  a=Card('A','♥',enhancement='Glass')
  g.hand=[a]
  chips,mult,res=score_hand(g,'High Card',[a],[a])
  self.assertGreaterEqual(mult,2)
 def test_boss_effects(self):
  g=Game.new_run(seed=1);g.blind=2;g.boss='The Water';g.recompute_target();g.start_blind()
  self.assertEqual(g.discards,0)
  g=Game.new_run(seed=1);g.blind=2;g.boss='Cerulean Bell';g.recompute_target();g.start_blind()
  self.assertTrue(g.locked_card)
  notlocked=[i for i,c in enumerate(g.hand) if c.uid!=g.locked_card][:2]
  with self.assertRaises(ValueError):g.play(notlocked)
  g=Game.new_run(seed=1);g.blind=2;g.boss='The Pillar';g.recompute_target();g.start_blind()
  c=g.hand[0];g.played_ante=[c.uid]
  self.assertTrue(g.debuff(c))
 def test_shop_stake_red_reward(self):
  g=Game.new_run(stake='Red',seed=8);g.start_blind();g.hands=0;g.score=g.target
  g.win_blind();self.assertEqual(g.state,'shop')
 def test_screen_changes_and_colored_cards(self):
  ui=UI();g=Game.new_run(seed=1)
  ui._new_screen(g)
  s,data=ui._new_screen(g)
  self.assertTrue(data)
  self.assertTrue(all(s.a[0][x].bg==THEMES['blind'][0] for x in range(s.w)))
  # Renderer caches previous rows and updates only changed content.
  canvas=Canvas(25,6,(12,15,19));out=io.StringIO()
  r=Renderer()
  with redirect_stdout(out):r.draw(canvas)
  out.truncate(0);out.seek(0)
  with redirect_stdout(out):r.draw(canvas)
  self.assertEqual(out.getvalue(),'')
  canvas.put(2,2,'牌',SUIT['♥'])
  with redirect_stdout(out):r.draw(canvas)
  self.assertIn('[3;1H',out.getvalue())
 def test_controller_paths(self):
  c=Controller();c.execute('enter');c.execute('enter');self.assertEqual(c.game.state,'blind')
  c.execute('start');self.assertEqual(c.game.state,'play')
  c.key('ENTER');c.execute('p');self.assertEqual(len(c.game.hand)>0,True)
  c.game.score=c.game.target;c.game.win_blind();self.assertEqual(c.game.state,'shop')
  c.game.money=500;c.game.open_pack(0);self.assertEqual(c.game.state,'pack')
  c.execute('z');self.assertEqual(c.game.state,'shop')
  c.execute('n');self.assertEqual(c.game.state,'blind')

if __name__=='__main__':unittest.main()
