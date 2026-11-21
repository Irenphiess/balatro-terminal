"""V15 cross-system rules: spectral transforms, all Boss categories and UI cues."""
import os,re,unittest,random
from collections import Counter
from unittest.mock import patch
from arcana.game import Game
from arcana.cards import Card
from arcana.tui import UI,BLUE,RED,THEMES
from arcana.poker import analyze
from arcana.content import BOSSES

class V15RulesTests(unittest.TestCase):
 def game(self,boss=None,seed=15):
  g=Game.new_run(seed=seed)
  if boss:
   g.blind=2;g.boss=boss;g.boss_disabled=False
  g.start_blind()
  return g
 def test_sigil_round_persistence(self):
  g=self.game();g.consumables=[{'type':'Spectral','name':'Sigil'}]
  original=set(c.uid for c in g.hand)
  g.use(0)
  suits={c.suit for c in g.hand}
  self.assertEqual(len(suits),1)
  self.assertTrue(all(next(c for c in g.deck if c.uid==h.uid).suit==h.suit for h in g.hand))
  self.assertTrue(all(next(c for c in g.draw_pile if c.uid==h.uid).suit==h.suit for h in g.hand if any(c.uid==h.uid for c in g.draw_pile)))
  self.assertEqual(g.consumables,[])
 def test_ouija_rank_and_cost(self):
  g=self.game();before=g.hand_size
  g.consumables=[{'type':'Spectral','name':'Ouija'}]
  g.use(0)
  self.assertEqual(len({c.rank for c in g.hand}),1)
  self.assertEqual(g.hand_size,before-1)
  self.assertTrue(all(next(c for c in g.deck if c.uid==h.uid).rank==h.rank for h in g.hand))
 def test_spectral_pack_applies(self):
  for name,key in [('Sigil','suit'),('Ouija','rank')]:
   with self.subTest(name=name):
    g=self.game(seed=20);g.state='pack';g.pack={'kind':'Spectral','options':[{'type':'Spectral','name':name}],'picks':1}
    g.select_pack(0)
    self.assertEqual(len({getattr(c,key) for c in g.hand}),1)
    self.assertEqual(g.state,'shop')
 def test_sigil_requires_actual_hand(self):
  g=self.game();g.hand=[];g.consumables=[{'type':'Spectral','name':'Sigil'}]
  with self.assertRaises(ValueError):g.use(0)
  self.assertEqual(len(g.consumables),1)
 def test_all_bosses_are_registered(self):
  self.assertEqual(len(BOSSES),28)
 def test_four_suit_bosses(self):
  pairs={'The Head':'♥','The Window':'♦','The Club':'♣','The Goad':'♠'}
  for blind,suit in pairs.items():
   with self.subTest(blind=blind):
    g=self.game(blind)
    self.assertTrue(g.debuff(Card('A',suit)))
    self.assertFalse(g.debuff(Card('A',next(s for s in ('♣','♠','♥','♦') if s!=suit))))
    self.assertTrue(g.debuff(Card('2','♠',enhancement='Wild')))
 def test_smeared_extends_suit_debuff(self):
  g=self.game('The Head');g.add_joker('Smeared Joker')
  self.assertTrue(g.debuff(Card('9','♦')))
  self.assertFalse(g.debuff(Card('9','♣')))
 def test_pareidolia_plant(self):
  g=self.game('The Plant');g.add_joker('Pareidolia')
  self.assertTrue(g.debuff(Card('2','♣')))
 def test_debuffed_wild_loses_every_suit(self):
  g=self.game('The Head');cards=[Card(r,'♣') for r in ('2','3','4','5')]+[Card('9','♠',enhancement='Wild')]
  self.assertEqual(analyze(cards)[0],'Flush')
  self.assertNotEqual(g.classify(cards)[0],'Flush')
 def test_debuffed_heart_still_forms_flush(self):
  g=self.game('The Head');cards=[Card(r,'♥') for r in ('2','4','6','8','10')]
  kind,scored=g.classify(cards)
  self.assertEqual(kind,'Flush')
  self.assertTrue(all(g.debuff(c) for c in scored))
 def test_no_boss_effect_after_disabled(self):
  g=self.game('The Head');g.boss_disabled=True
  self.assertFalse(g.debuff(Card('K','♥')))
 def test_psychic_rejection_consumes_hand_no_score(self):
  g=self.game('The Psychic');before=g.hands
  result=g.play([0,1,2,3])
  self.assertTrue(result['blocked'])
  self.assertEqual(result['points'],0)
  self.assertEqual(g.hands,before-1)
 def test_eye_reject_repeat(self):
  g=self.game('The Eye')
  kind,_=g.classify(g.hand[:1]);g.round_history[kind]=1
  result=g.play([0]);self.assertIn('眼睛',result['blocked'])
  self.assertEqual(result['points'],0)
 def test_mouth_reject_different_hand(self):
  g=self.game('The Mouth');kind,_=g.classify(g.hand[:1]);g.round_history['Flush' if kind!='Flush' else 'Pair']=1
  result=g.play([0]);self.assertIn('嘴巴',result['blocked'])
  self.assertEqual(result['points'],0)
 def test_house_turns_over_after_discard(self):
  g=self.game('The House');self.assertEqual(set(g.hidden_cards),{c.uid for c in g.hand})
  g.discard([0]);self.assertFalse(g.hidden_cards)
 def test_mark_new_face_cards_hidden(self):
  g=self.game('The Mark');self.assertEqual(set(g.hidden_cards),{c.uid for c in g.hand if c.rank in ('J','Q','K')})
  g.discard([0]);self.assertEqual(set(g.hidden_cards),{c.uid for c in g.hand if c.rank in ('J','Q','K')})
 def test_wheel_applies_each_draw(self):
  with patch('arcana.game.prob',return_value=True):
   g=self.game('The Wheel');self.assertEqual(set(g.hidden_cards),{c.uid for c in g.hand})
   g.discard([0]);self.assertEqual(set(g.hidden_cards),{c.uid for c in g.hand})
 def test_fish_preserves_old_backs_but_discard_draws_faceup(self):
  g=self.game('The Fish');self.assertFalse(g.hidden_cards)
  g.play([0]);self.assertTrue(g.hidden_cards)
  hidden=set(g.hidden_cards);before={c.uid for c in g.hand}
  g.discard([next(i for i,c in enumerate(g.hand) if c.uid not in hidden)])
  self.assertTrue(hidden.intersection({c.uid for c in g.hand}).issubset(g.hidden_cards))
  new=set(c.uid for c in g.hand)-before
  self.assertFalse(set(g.hidden_cards)&new)
 def test_crimson_heart_visible_before_play(self):
  g=Game.new_run(seed=6);g.add_joker('Joker');g.add_joker('Greedy Joker')
  g.blind=2;g.boss='Crimson Heart';g.start_blind()
  previous=[j for j in g.jokers if j.get('debuff_round')]
  self.assertEqual(len(previous),1)
  g.discard([0]);self.assertEqual(previous,[j for j in g.jokers if j.get('debuff_round')])
  g.play([0]);self.assertEqual(len([j for j in g.jokers if j.get('debuff_round')]),1)
  self.assertNotEqual(previous,[j for j in g.jokers if j.get('debuff_round')])

class V15VisualTests(unittest.TestCase):
 def capture(self,ui,g):
  from arcana import tui
  captured=[]
  with patch('arcana.tui.shutil.get_terminal_size',return_value=os.terminal_size((165,65))):
   ui.renderer.draw=lambda c:captured.append(c)
   ui.draw(g)
  return captured[-1]
 def test_no_filled_deck_or_stake_selection(self):
  u=UI();u.stage='select'
  cv=self.capture(u,None);bg=THEMES['title'][1]
  # All cells inside selection frame use scene background, not lighter highlight.
  self.assertFalse(any(cell.bg not in (bg,THEMES['title'][0]) for row in cv.a for cell in row))
 def test_debuff_draws_red_cross(self):
  g=Game.new_run(seed=14);g.blind=2;g.boss='The Head';g.start_blind()
  g.hand=[Card('8','♥'),Card('9','♣')];g.hidden_cards=[g.hand[0].uid]
  u=UI();cv=self.capture(u,g)
  self.assertTrue(any(cell.text=='╳' and cell.fg==RED for row in cv.a for cell in row))
 def test_blocked_hand_strikethrough_red(self):
  g=Game.new_run(seed=14);g.blind=2;g.boss='The Psychic';g.start_blind()
  u=UI();u.selected_uids=[g.hand[0].uid]
  cv=self.capture(u,g)
  self.assertTrue(any('\u0336' in cell.text and cell.fg==RED for row in cv.a for cell in row))
 def test_hand_size_on_sidebar(self):
  g=Game.new_run(seed=14);g.start_blind();u=UI();cv=self.capture(u,g)
  lines=[''.join(cell.text for cell in row) for row in cv.a]
  self.assertTrue(any('手牌数量' in line and '8' in line for line in lines))
 def test_english_pages_do_not_leak_chinese(self):
  u=UI(language='en');g=Game.new_run(seed=14)
  screens=[]
  for state in ('blind','play','shop','pack'):
   u.overlay=None
   if state=='play':g.start_blind()
   elif state=='shop':g.state='shop';g.generate_shop();g.refresh_shop_hand()
   elif state=='pack':g.open_pack(0)
   screens.append(self.capture(u,g))
  for overlay in ('hand','levels','help','gallery','effects'):
   u.overlay=overlay;screens.append(self.capture(u,g))
  for cv in screens:
   text=''.join(cell.text for row in cv.a for cell in row)
   self.assertIsNone(re.search(r'[\u3400-\u9fff]',text),text[:100])

if __name__=='__main__':unittest.main()
