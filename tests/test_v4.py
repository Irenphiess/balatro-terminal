"""Regression tests for keyboard UX, fixed booster choices, and boss forecasts."""
import collections,unittest
from unittest.mock import patch
from arcana.cards import Card
from arcana.game import Game
from arcana.poker import analyze
from arcana.content import PACK_CONFIG,BOSSES
from arcana.tui import UI,Renderer
from play import Controller

class V4(unittest.TestCase):
    def test_flush_requires_five_unless_four_fingers(self):
        four=[Card(r,'♥') for r in ['2','5','8','K']]
        off=Card('A','♣')
        self.assertEqual(analyze(four+[off])[0],'High Card')
        self.assertEqual(analyze(four+[off],four_fingers=True)[0],'Flush')
        self.assertEqual(analyze(four+[Card('9','♦')],smeared=True)[0],'Flush')
    def test_five_suit_normal(self):
        self.assertEqual(analyze([Card(r,'♣') for r in ['2','4','6','9','J']])[0],'Flush')
    def test_boss_preselected_until_next_ante(self):
        g=Game.new_run(seed=2)
        boss=g.boss
        self.assertIn(boss,BOSSES)
        g.blind=1;g.choose_blind();self.assertEqual(g.boss,boss)
        g.blind=2;g.choose_blind();self.assertEqual(g.boss,boss)
        g.ante+=1;g.blind=0;g.choose_blind();self.assertEqual(g.boss_roll_ante,g.ante)
    def test_boss_preview_does_not_debuff_small_blind(self):
        g=Game.new_run(seed=3)
        g.boss='The Water';g.start_blind()
        self.assertEqual(g.discards,g.max_discards)
        g=Game.new_run(seed=3)
        g.boss='The Needle';g.start_blind()
        self.assertEqual(g.hands,g.max_hands)
    def test_pack_unique_always(self):
        for kind in PACK_CONFIG:
            for seed in range(120):
                g=Game.new_run(seed=seed)
                g.state='shop';g.money=999
                g.packs=[{'kind':kind,'size':'Mega','cost':8}]
                g.open_pack(0)
                keys=[(x['type'],x['name']) for x in g.pack['options']]
                self.assertEqual(len(keys),len(set(keys)),(kind,seed))
    def test_mega_pack_stable_after_first_pick(self):
        g=Game.new_run(seed=10);g.state='shop';g.money=100
        g.packs=[{'kind':'Celestial','size':'Mega','cost':8}]
        g.open_pack(0)
        before=[o['name'] for o in g.pack['options']]
        self.assertEqual(g.pack['original_total'],5)
        self.assertEqual(g.pack['picks'],2)
        g.select_pack(1)
        self.assertEqual([o['name'] for o in g.pack['options']],before[:1]+before[2:])
        self.assertEqual(g.pack['picks'],1)
        self.assertEqual(g.pack['original_total'],5)
        g.select_pack(0)
        self.assertIsNone(g.pack)
        self.assertEqual(g.state,'shop')
    def test_single_enter_navigation(self):
        c=Controller();c.key('ENTER')
        c.key('s');self.assertEqual(c.ui.deck_index,5)
        c.key('d');self.assertEqual(c.ui.deck_index,6)
        c.key('UP');self.assertEqual(c.ui.stake_index,4)
        c.key('RIGHT');self.assertEqual(c.ui.stake_index,5)
        c.key('ENTER');self.assertEqual(c.game.state,'blind')
        self.assertEqual(c.game.deck_name,'Nebula Deck')
        c.key('ENTER');self.assertEqual(c.game.state,'play')
        c.key('ENTER');c.key('p');self.assertTrue(c.game.last_result)
        c.game.score=c.game.target;c.game.win_blind();self.assertEqual(c.game.state,'shop')
        c.key('n');self.assertEqual(c.game.state,'blind')
    def test_dynamic_layout_content_and_center(self):
        for size in ((122,50),(130,52),(158,60),(182,67)):
            captured=[]
            from os import terminal_size
            with patch('shutil.get_terminal_size',return_value=terminal_size(size)):
                with patch.object(Renderer,'draw',lambda self,c:captured.append(c)):
                    u=UI();u.draw(None);u.stage='select';u.draw(None)
                    g=Game.new_run(seed=44)
                    u.draw(g)
                    g.start_blind();u.draw(g)
                    g.score=g.target;g.win_blind();u.draw(g)
                    g.money=500;g.packs=[{'kind':'Arcana','size':'Mega','cost':8}]
                    g.open_pack(0);u.draw(g)
                    u.overlay='help';u.draw(g)
                    u.overlay='gallery';u.draw(g)
                    u.overlay='levels';u.draw(g)
                    u.overlay='hand';u.draw(g)
            for c in captured:
                self.assertGreater(c.w,110)
                self.assertEqual(len(c.a),c.h)
                self.assertTrue(all(len(row)==c.w for row in c.a))
                flattened=''.join(cell.text for row in c.a for cell in row)
                self.assertIn('B A L A T R O',flattened)
            self.assertIn('选择难度',''.join(cell.text for row in captured[1].a for cell in row))
            self.assertIn('BOSS 能力预告',''.join(cell.text for row in captured[2].a for cell in row))
            self.assertIn('补充包',''.join(cell.text for row in captured[5].a for cell in row))

if __name__=='__main__':unittest.main()
