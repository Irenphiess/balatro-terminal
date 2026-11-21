"""V5 regression: navigation, shop weight, explanations, migration and redraw."""
import collections,unittest,tempfile,os,pathlib
from unittest.mock import patch
from arcana.game import Game
from arcana.cards import Card
from arcana.explain import EFFECT_GROUPS,card_description,joker_description,item_description
from arcana.tui import UI,Renderer
from play import Controller

class V5(unittest.TestCase):
 def test_sort_ascending_each_suit(self):
  g=Game.new_run(seed=1)
  g.hand=[Card('K','♠'),Card('2','♠'),Card('A','♥'),Card('3','♥'),Card('10','♦'),Card('4','♣')]
  g.sort_hand()
  self.assertEqual([(c.rank,c.suit) for c in g.hand],[('3','♥'),('A','♥'),('10','♦'),('2','♠'),('K','♠'),('4','♣')])
 def test_shop_weights_base_and_voucher(self):
  g=Game.new_run(seed=1)
  self.assertEqual(g.shop_weights(),{'Joker':20.0,'Tarot':4.0,'Planet':4.0})
  g.vouchers.add('Planet Merchant')
  self.assertEqual(g.shop_weights()['Planet'],9.6)
  g.vouchers.add('Magic Trick')
  self.assertEqual(g.shop_weights()['Card'],4.0)
  g.vouchers.add('Tarot Tycoon')
  self.assertEqual(g.shop_weights()['Tarot'],32.0)
 def test_shop_distribution(self):
  g=Game.new_run(seed=44)
  ct=collections.Counter(g.shop_item()['type'] for _ in range(5000))
  self.assertGreater(ct['Joker'],3300)
  self.assertLess(abs(ct['Planet']-ct['Tarot']),160)
 def test_shop_rejects_duplicates(self):
  for seed in range(100):
   g=Game.new_run(seed=seed);g.generate_shop()
   names=[(x['type'],x['name']) for x in g.shop]
   self.assertEqual(len(names),len(set(names)))
 def test_hand_focus_select_move_and_discard(self):
  c=Controller();c.key('ENTER');c.key('ENTER');c.key('ENTER')
  self.assertEqual(c.game.state,'play')
  current=c.game.hand[0].uid
  c.key('ENTER');self.assertIn(current,c.ui.selected_uids)
  c.key('RIGHT');self.assertEqual(c.ui.cursor_hand,1)
  c.key('ENTER');self.assertEqual(len(c.ui.selected_uids),2)
  c.key('LEFT');c.key('ENTER');self.assertNotIn(current,c.ui.selected_uids)
  c.key('o')
  self.assertEqual(c.game.discards,c.game.max_discards-1)
  self.assertFalse(c.ui.selected_uids)
 def test_joker_focus_opens_detail_without_overlay_collision(self):
  c=Controller();c.game=Game.new_run(seed=1);c.game.add_joker('Blueprint');c.game.start_blind()
  c.key('UP');self.assertEqual(c.ui.focus,'joker')
  c.key('ENTER');self.assertEqual(c.ui.overlay,'detail');self.assertEqual(c.ui.detail['kind'],'joker')
  canvas=[]
  with patch('shutil.get_terminal_size',return_value=os.terminal_size((160,60))):
   with patch.object(Renderer,'draw',lambda self,c:canvas.append(c)):
    c.ui.draw(c.game)
  screen=''.join(z.text for row in canvas[0].a for z in row)
  self.assertIn('小丑牌',screen)
  self.assertNotIn('已选择 0 / 5 张',screen)
  c.key('ENTER');self.assertIsNone(c.ui.overlay)
 def test_explain_commands(self):
  c=Controller();c.game=Game.new_run(seed=1);c.game.add_joker('Mime');c.game.start_blind()
  with self.assertRaises(ValueError):c.execute('e 1')
  c.key('UP');c.key('ENTER');self.assertEqual(c.ui.detail['kind'],'joker');c.key('ENTER')
  c.game.state='shop';c.game.generate_shop();c.ui.focus='hand'
  c.execute('e');self.assertEqual(c.ui.detail['kind'],'joker');c.key('e')
  c.execute('f');self.assertEqual(c.ui.overlay,'effects')
  c.execute('e e 1') if False else None
 def test_explanation_library(self):
  self.assertEqual(len(EFFECT_GROUPS),7)
  for n in ('Blueprint','Brainstorm','Baron','Mime'):
   self.assertGreaterEqual(len(joker_description(n)),4)
  self.assertTrue(any('1/4' in x for x in card_description(Card('K','♥',enhancement='Glass'))))
  self.assertTrue(any('升级' in x for x in item_description({'type':'Planet','name':'Pair'})))
 def test_atomic_save_and_read_anywhere(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'save.json';g=Game.new_run(seed=11);g.start_blind();g.save(p)
   self.assertTrue(p.is_file());self.assertFalse((p.parent/(p.name+'.tmp')).exists())
   copy=Game.load(p);self.assertEqual(copy.state,'play')
   with patch('arcana.game.SAVE',p):
    c=Controller();c.key('l');self.assertEqual(c.game.state,'play')
    self.assertEqual(c.game.deck_name,g.deck_name)
 def test_render_every_view(self):
  for size in ((122,50),(160,60),(184,70)):
   got=[]
   with patch('shutil.get_terminal_size',return_value=os.terminal_size(size)):
    with patch.object(Renderer,'draw',lambda self,c:got.append(c)):
     u=UI();u.draw(None)
     g=Game.new_run(seed=7);g.add_joker('Joker');g.add_joker('Mime');g.start_blind()
     u.selected_uids=[g.hand[0].uid,g.hand[1].uid]
     u.draw(g);u.focus='joker';u.cursor_joker=1;u.draw(g)
     for d in ({'kind':'joker','index':1},{'kind':'hand','index':0},{'kind':'effect','index':0,'group':0}):
      u.detail=d;u.overlay='detail';u.draw(g)
     u.overlay='effects';u.draw(g)
     u.overlay='help';u.draw(g)
     g.state='shop';g.generate_shop();u.overlay=None;u.draw(g)
     u.detail={'kind':'shop','index':0};u.overlay='detail';u.draw(g)
   for canvas in got:self.assertTrue(all(len(row)==canvas.w for row in canvas.a))
   self.assertGreaterEqual(len(got),8)
 def test_autosave_after_real_move(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'save.json'
   # Game.save defaults to its own declared path; patching the controller's stash path.
   with patch.object(Controller,'stash',lambda self:self.game.save(p) if self.game and self.game.state!='lost' else None):
    c=Controller();c.key('ENTER');c.key('ENTER');self.assertEqual(Game.load(p).state,'blind')
    c.key('ENTER');self.assertEqual(Game.load(p).state,'play')
    c.key('ENTER');c.key('p');self.assertTrue(p.exists())
 def test_music_unavailable_safe(self):
  from arcana.music import Music
  m=Music();m.available=False;m.enabled=False
  self.assertFalse(m.toggle())

if __name__=='__main__':unittest.main()
