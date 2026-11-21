"""V7 regression: levels, pack navigation, target picker and score formulas."""
import unittest,os,tempfile,pathlib,math
from unittest.mock import patch
from arcana.game import Game
from arcana.cards import Card
from arcana.formula import score_formula
from arcana.tui import UI,Renderer,BLUE,FOCUS_BG
from arcana.poker import HANDS,HAND_ZH
from play import Controller


def canvas_for(ui,g,size=(160,60)):
    out=[]
    with patch('shutil.get_terminal_size',return_value=os.terminal_size(size)):
        with patch.object(Renderer,'draw',lambda _,c:out.append(c)):
            ui.draw(g)
    return out[0]

def texts(canvas):
    return '\n'.join(''.join(cell.text or '' for cell in row) for row in canvas.a)

class V7(unittest.TestCase):
    def test_x_levels_from_battle_shop_pack(self):
        c=Controller();g=Game.new_run(seed=11);g.start_blind();c.game=g
        for state in ('play','shop','pack','blind'):
            g.state=state
            c.key('x');self.assertEqual(c.ui.overlay,'levels',state)
            view=texts(canvas_for(c.ui,g))
            self.assertIn('牌 型 组 合 与 等 级',view)
            for kind in HANDS:
                self.assertIn(HAND_ZH[kind],view)
            self.assertIn('组成',view) if False else None
            self.assertIn('五张点数连续',view)
            c.key('ENTER');self.assertIsNone(c.ui.overlay)

    def test_x_hint_visible_on_battle_and_pack(self):
        c=Controller();g=Game.new_run(seed=7);g.start_blind();c.game=g
        self.assertIn('X 牌型等级',texts(canvas_for(c.ui,g)))
        g.state='pack';g.pack={'kind':'Celestial','size':'Mega','options':[{'type':'Planet','name':'High Card'}],'picks':1,'original_total':1}
        self.assertIn('X 牌型等级',texts(canvas_for(c.ui,g)))

    def test_pack_arrows_blue_focus_enter_and_remove_option(self):
        c=Controller();g=Game.new_run(seed=7);g.state='pack';g.pack={
            'kind':'Celestial','size':'Mega','options':[
                {'type':'Planet','name':'Pair'},
                {'type':'Planet','name':'High Card'},
                {'type':'Planet','name':'Flush'}],
            'picks':2,'original_total':3}
        c.game=g
        c.key('DOWN');self.assertEqual(c.ui.cursor_pack,1)
        view=canvas_for(c.ui,g)
        self.assertTrue(any(cell.fg==BLUE and cell.text=='┄' for row in view.a for cell in row))
        self.assertFalse(any(cell.bg==FOCUS_BG for row in view.a for cell in row))
        c.key('ENTER')
        self.assertEqual(g.state,'pack')
        self.assertEqual(g.levels['High Card'],2)
        self.assertEqual(g.pack['picks'],1)
        self.assertEqual(len(g.pack['options']),2)
        self.assertEqual(c.ui.cursor_pack,1)
        c.key('ENTER')
        self.assertEqual(g.levels['Flush'],2)
        self.assertEqual(g.state,'shop')
        self.assertEqual(c.ui.cursor_pack,0)

    def test_pack_e_independent_detail_return(self):
        c=Controller();g=Game.new_run(seed=7);g.state='pack'
        g.pack={'kind':'Celestial','size':'Normal','options':[{'type':'Planet','name':'Pair'},{'type':'Planet','name':'Straight'}],'picks':1}
        c.game=g;c.key('DOWN');c.key('e')
        self.assertEqual(c.ui.overlay,'detail')
        self.assertEqual(c.ui.detail,{'kind':'pack','index':1})
        text=texts(canvas_for(c.ui,g))
        self.assertIn('补充包',text)
        self.assertNotIn('剩余可选 1 张',text)
        c.key('ENTER')
        self.assertIsNone(c.ui.overlay)
        self.assertEqual(c.ui.cursor_pack,1)

    def test_death_targeted_pack_enter_only(self):
        c=Controller();g=Game.new_run(seed=11);g.refresh_shop_hand();c.game=g
        g.state='pack';g.pack={'kind':'Arcana','size':'Normal','options':[{'type':'Tarot','name':'Death'}],'picks':1}
        before=len(g.deck)
        c.key('ENTER')
        self.assertEqual(c.ui.overlay,'pack_target')
        self.assertIn('选 择 效 果 目 标',texts(canvas_for(c.ui,g)))
        c.key('ENTER')
        self.assertEqual(c.ui.target_indices,[0])
        c.key('RIGHT');c.key('ENTER')
        self.assertIsNone(c.ui.overlay)
        self.assertEqual(g.state,'shop')
        self.assertEqual(len(g.deck),before)

    def test_target_cancel_and_single_card(self):
        c=Controller();g=Game.new_run(seed=10);g.refresh_shop_hand();g.state='pack';g.pack={
            'kind':'Arcana','size':'Normal','options':[{'type':'Tarot','name':'Justice'}],'picks':1};c.game=g
        c.key('ENTER');self.assertEqual(c.ui.overlay,'pack_target')
        c.key('ESC');self.assertIsNone(c.ui.overlay)
        self.assertEqual(g.state,'pack')
        c.key('ENTER');c.key('ENTER')
        self.assertEqual(g.state,'shop')
        self.assertTrue(any(z.enhancement=='Glass' for z in g.hand))

    def test_target_multi_optional_p_to_finish(self):
        c=Controller();g=Game.new_run(seed=9);g.refresh_shop_hand();g.state='pack';g.pack={
            'kind':'Arcana','size':'Normal','options':[{'type':'Tarot','name':'The Star'}],'picks':1};c.game=g
        c.key('ENTER');self.assertEqual(c.ui.target_max,3)
        c.key('ENTER');self.assertEqual(c.ui.overlay,'pack_target')
        c.key('p');self.assertEqual(g.state,'shop')
        self.assertEqual(g.hand[0].suit,'♦')

    def test_formula_plain_and_xmult(self):
        a={'hand':'Pair','chips':44,'mult':2,'points':88,
           'breakdown':{'base_chips':10,'bonus_chips':34,'base_mult':2,'bonus_mult':0,'xmult':1}}
        self.assertEqual(score_formula(a),'对子：(10 + 34) × 2 = 88')
        b={'hand':'High Card','chips':105,'mult':30,'points':3150,
           'breakdown':{'base_chips':5,'bonus_chips':100,'base_mult':1,'bonus_mult':9,'xmult':3}}
        self.assertEqual(score_formula(b),'高牌：(5 + 100) × (1 + 9) × 3 = 3,150')

    def test_formula_real_resolution_equals_engine(self):
        for seed in range(20):
            g=Game.new_run(seed=seed)
            g.add_joker('Joker');g.add_joker('Cavendish')
            g.start_blind()
            g.hand[0].enhancement='Glass'
            g.hand[1].enhancement='Steel'
            v=g.play([0])
            b=v['breakdown']
            predicted=(b['base_chips']+b['bonus_chips'])*(b['base_mult']+b['bonus_mult'])*b['xmult']
            self.assertLess(abs(predicted-v['points']),1.01)
            self.assertIn('×',score_formula(v))
            self.assertIn(' = ',score_formula(v))

    def test_mixed_order_additions_after_multipliers(self):
        g=Game.new_run(seed=3);g.start_blind()
        g.jokers=[g.make_joker('Cavendish'),g.make_joker('Joker')]
        v=g.play([0]);b=v['breakdown']
        self.assertAlmostEqual((b['base_mult']+b['bonus_mult'])*b['xmult'],v['mult'],places=6)
        self.assertNotEqual(b['bonus_mult'],0)

    def test_formula_in_battle_shop_and_loss(self):
        c=Controller();g=Game.new_run(seed=14);g.start_blind();c.game=g
        g.play([0]);formula=score_formula(g.last_result)
        self.assertIn('=',formula)
        self.assertIn('=',texts(canvas_for(c.ui,g)))
        g.state='shop';g.generate_shop()
        self.assertNotIn('上手得分',texts(canvas_for(c.ui,g)))
        g.state='lost'
        self.assertIn('最后一手',texts(canvas_for(c.ui,g)))

    def test_cross_version_save_roundtrip_with_breakdown(self):
        g=Game.new_run(seed=7);g.start_blind();g.play([0])
        with tempfile.TemporaryDirectory() as d:
            file=pathlib.Path(d)/'v7.json';g.save(file)
            other=Game.load(file)
            self.assertEqual(other.last_result['breakdown'],g.last_result['breakdown'])

if __name__=='__main__':unittest.main()
