"""V6 regression suite: Boss history, navigation, theme, music and saves."""
import os,io,wave,hashlib,tempfile,pathlib,collections,unittest
from unittest.mock import patch
from arcana.game import Game
from arcana.content import BOSSES
from arcana.music import Music,TRACKS
from arcana.tui import UI,Renderer,BLUE,FOCUS_BG
from play import Controller

class V6(unittest.TestCase):
 def test_boss_randomized_across_seeds(self):
  counts=collections.Counter(Game.new_run(seed=seed).boss for seed in range(400))
  self.assertGreaterEqual(len(counts),7)
  self.assertGreater(min(counts.values()),20)
  self.assertLess(max(counts.values()),85)
  self.assertIn('The Manacle',counts)

 def test_boss_stable_within_ante_different_on_next(self):
  for seed in range(30):
   g=Game.new_run(seed=seed);boss=g.boss
   for blind in (1,2):
    g.state='shop';g.next_blind()
    self.assertEqual(g.blind,blind)
    self.assertEqual(g.boss,boss)
   g.state='shop';g.next_blind()
   self.assertEqual(g.ante,2)
   self.assertNotEqual(g.boss,boss)
   self.assertEqual(g.boss_roll_ante,2)
   self.assertEqual(g.boss_history[-1]['ante'],2)

 def test_boss_lookahead_distribution_is_not_manacle_only(self):
  g=Game.new_run(seed=31);past=[]
  for ante in range(1,16):
   g.ante=ante;g.blind=0;g.choose_blind();past.append(g.boss)
  self.assertGreater(len(set(past)),10)
  self.assertTrue(all(b in BOSSES for b in past))

 def test_splash_and_game_setup_separated(self):
  c=Controller()
  self.assertEqual(c.ui.stage,'splash');self.assertIsNone(c.game)
  c.key('ENTER');self.assertEqual(c.ui.stage,'select');self.assertIsNone(c.game)
  c.key('s');self.assertEqual(c.ui.deck_index,5)
  c.key('ESC');self.assertEqual(c.ui.stage,'splash')
  c.key('ENTER');c.key('ENTER');self.assertIsNotNone(c.game)
  self.assertEqual(c.game.deck_name,'Magic Deck')

 def test_shop_arrow_e_enter_card(self):
  c=Controller();g=Game.new_run(seed=42);g.state='shop';g.money=1000;g.generate_shop();c.game=g
  self.assertGreater(len(g.shop),0)
  name=g.shop[0]['name']
  c.key('e')
  self.assertEqual(c.ui.overlay,'detail');self.assertEqual(c.ui.detail,{'kind':'shop','index':0})
  c.key('ENTER');self.assertIsNone(c.ui.overlay)
  c.key('ENTER');self.assertFalse(any(i['name']==name for i in g.shop))
  self.assertEqual(c.ui.cursor_shop,0)
  c.key('n');self.assertEqual(g.state,'blind')

 def test_shop_navigation_pack_and_voucher(self):
  c=Controller();g=Game.new_run(seed=23);g.state='shop';g.money=500;g.generate_shop();c.game=g
  for _ in range(len(g.shop)):c.key('DOWN')
  self.assertEqual(c.shop_current(),('pack',0))
  c.key('e');self.assertEqual(c.ui.detail['kind'],'pack_info')
  got=[]
  with patch('shutil.get_terminal_size',return_value=os.terminal_size((160,60))):
   with patch.object(Renderer,'draw',lambda self,canvas:got.append(canvas)):
    c.ui.draw(g)
  flattened=''.join(v.text for row in got[0].a for v in row)
  self.assertIn('补充包',flattened)
  c.key('ENTER');c.key('ENTER')
  self.assertEqual(g.state,'pack')
  g.skip_pack()
  c.ui.cursor_shop=len(c.ui.shop_entries(g))-1
  self.assertEqual(c.shop_current(),('voucher',0))
  c.key('e');self.assertEqual(c.ui.detail['kind'],'voucher')
  c.key('ENTER');c.key('ENTER')
  self.assertIsNone(g.shop_voucher)

 def test_shop_up_arrow_wraps(self):
  c=Controller();g=Game.new_run(seed=10);g.state='shop';g.generate_shop();c.game=g
  c.key('UP');self.assertEqual(c.ui.cursor_shop,len(c.ui.shop_entries(g))-1)
  c.key('DOWN');self.assertEqual(c.ui.cursor_shop,0)

 def test_play_e_numeric_removed_and_joker_enter_remains(self):
  c=Controller();c.game=Game.new_run(seed=1);g=c.game;g.start_blind();g.add_joker('Joker')
  with self.assertRaises(ValueError):c.execute('e 1')
  c.key('UP');c.key('ENTER');self.assertEqual(c.ui.detail['kind'],'joker')
  c.key('ENTER');self.assertIsNone(c.ui.overlay)

 def test_blue_dashed_card_and_blue_selected_number(self):
  c=Controller();g=Game.new_run(seed=1);g.start_blind();c.game=g
  c.key('ENTER')
  with patch('shutil.get_terminal_size',return_value=os.terminal_size((160,60))):
   captured=[]
   with patch.object(Renderer,'draw',lambda self,canvas:captured.append(canvas)):
    c.ui.draw(g)
  cells=[v for row in captured[0].a for v in row]
  self.assertTrue(any(v.text=='┄' and v.fg==BLUE for v in cells))
  self.assertTrue(any('✓' in v.text and v.fg==BLUE for v in cells))

 def test_blue_joker_focus_and_shop_focus(self):
  c=Controller();g=Game.new_run(seed=1);g.add_joker('Joker');g.start_blind();c.game=g
  c.key('UP');got=[]
  with patch('shutil.get_terminal_size',return_value=os.terminal_size((160,60))):
   with patch.object(Renderer,'draw',lambda self,canvas:got.append(canvas)):
    c.ui.draw(g)
  self.assertTrue(any(v.bg==FOCUS_BG and v.fg==BLUE for row in got[-1].a for v in row))
  g.state='shop';g.generate_shop();c.ui.focus='hand';got=[]
  with patch('shutil.get_terminal_size',return_value=os.terminal_size((160,60))):
   with patch.object(Renderer,'draw',lambda self,canvas:got.append(canvas)):
    c.ui.draw(g)
  self.assertTrue(any(v.text=='┄' and v.fg==BLUE for row in got[-1].a for v in row))

 def test_layout_small_and_large_no_shop_footer_collision(self):
  g=Game.new_run(seed=11);g.state='shop';g.generate_shop()
  for size in ((122,50),(140,54),(160,60),(190,75)):
   got=[]
   with patch('shutil.get_terminal_size',return_value=os.terminal_size(size)):
    with patch.object(Renderer,'draw',lambda self,canvas:got.append(canvas)):
     u=UI();u.stage='splash';u.draw(None);u.stage='select';u.draw(None);u.draw(g)
   self.assertEqual(len(got),3)
   canvas=got[-1]
   full=''.join(v.text for row in canvas.a for v in row)
   self.assertIn('商  店',full)
   self.assertIn('Enter 买入',full)
   self.assertTrue(all(len(row)==canvas.w for row in canvas.a))
   intro=''.join(v.text for row in got[0].a for v in row)
   self.assertIn('按  E N T E R',intro)

 def test_scene_selection_from_stage(self):
  c=Controller()
  self.assertEqual(c.music_scene(),'title')
  g=Game.new_run(seed=1);c.game=g
  self.assertEqual(c.music_scene(),'play')
  g.blind=2;self.assertEqual(c.music_scene(),'boss')
  g.state='shop';self.assertEqual(c.music_scene(),'shop')
  g.state='pack';g.pack={'kind':'Arcana'};self.assertEqual(c.music_scene(),'arcana')
  g.pack={'kind':'Celestial'};self.assertEqual(c.music_scene(),'celestial')
  g.pack={'kind':'Buffoon'};self.assertEqual(c.music_scene(),'play')

 def test_all_scene_tracks_use_user_supplied_mp3(self):
  unique=set()
  for key,p in TRACKS.items():
   self.assertTrue(p.is_file(),key)
   with p.open('rb') as f:
    self.assertTrue(f.read(3) in (b'ID3',b'\xff\xfb\x90'),key)
   unique.add(hashlib.sha256(p.read_bytes()).hexdigest())
  self.assertEqual(len(unique),5)
  self.assertEqual(TRACKS['title'],TRACKS['play'])
  m=Music(enabled=False);m.set_scene('boss');self.assertEqual(m.scene,'boss')

 def test_v5_save_migration_including_boss_history(self):
  with tempfile.TemporaryDirectory() as d:
   old=pathlib.Path(d)/'old.json';g=Game.new_run(seed=31);g.start_blind();g.save(old)
   copy=Game.load(old)
   self.assertEqual(copy.state,'play')
   self.assertEqual(copy.boss,g.boss)
   self.assertEqual(copy.boss_history,g.boss_history)

if __name__=='__main__':unittest.main()
