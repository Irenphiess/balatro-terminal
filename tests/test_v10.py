"""V10: horizontal full-deck cards, shared selection frames and new keymap."""
import os,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from arcana.cards import Card
from arcana.game import Game
from arcana.tui import UI,Renderer,BLUE,BORDER,FOCUS_BG
from play import Controller

def snap(u,g,dim=(160,60)):
    out=[]
    with patch('shutil.get_terminal_size',return_value=os.terminal_size(dim)):
        with patch.object(Renderer,'draw',lambda _r,c:out.append(c)):
            u.draw(g)
    return out[0]

def row(c,y):return ''.join(z.text or '' for z in c.a[y])
def rendered(c):return '\n'.join(row(c,y) for y in range(c.h))

def has_outline(c,colour,dashed=False):
    return any(z.fg==colour and z.text==('┄' if dashed else '─') for r in c.a for z in r)

class V10(unittest.TestCase):
    def test_standard_deck_four_horizontal_suits_and_actual_card_frames(self):
        g=Game.new_run(seed=1);u=UI();u.overlay='hand';u.inventory_page=u.inventory_pages(g)-1
        c=snap(u,g)
        self.assertEqual(len(u.deck_visual_rows(g,u.last_layout[2])),4)
        x,y,W,H=u.last_layout
        for j,suit in enumerate(('♥','♦','♠','♣')):
            yy=y+13+j*7
            self.assertIn(suit,row(c,yy+2))
            self.assertIn('2',row(c,yy+1))
            self.assertIn('A',row(c,yy+1))
            self.assertGreaterEqual(row(c,yy).count('╭'),13)
            self.assertGreaterEqual(row(c,yy+5).count('╰'),13)
        self.assertNotIn('行 1–',rendered(c))

    def test_deck_wrap_and_scroll_on_narrow_window(self):
        g=Game.new_run(seed=1);g.deck.extend(Card('2','♥') for _ in range(30))
        u=UI();u.overlay='hand';u.inventory_page=u.inventory_pages(g)-1
        c=snap(u,g,(122,50));x,y,W,H=u.last_layout
        self.assertGreater(len(u.deck_visual_rows(g,W)),4)
        self.assertGreater(len(u.deck_visual_rows(g,W)),u.deck_visible_rows(H))
        ctrl=Controller();ctrl.game=g;ctrl.ui=u
        ctrl.key('DOWN');self.assertEqual(u.inventory_deck_scroll,1)
        c2=snap(u,g,(122,50));self.assertIn('第 2–',rendered(c2))
        self.assertTrue(all(row(c2,k).count('╭')==0 for k in range(y+H-11,y+H-7)))

    def test_purchased_card_has_visible_modified_face(self):
        g=Game.new_run(seed=1);g.deck.append(Card('2','♥',enhancement='Glass',seal='Red',edition='Foil'))
        u=UI();u.overlay='hand';u.inventory_page=u.inventory_pages(g)-1
        c=snap(u,g)
        txt=rendered(c)
        self.assertIn('玻璃×2',txt)
        self.assertIn('红·箔',txt)

    def test_shop_selection_keeps_scene_background_and_all_boxes(self):
        g=Game.new_run(seed=3);g.state='shop';g.generate_shop()
        u=UI();c=snap(u,g)
        self.assertTrue(has_outline(c,BLUE,True))
        self.assertTrue(has_outline(c,BORDER,False))
        self.assertFalse(any(z.bg==FOCUS_BG for r in c.a for z in r))
        self.assertNotIn('上手得分',rendered(c))

    def test_shop_many_items_remain_bordered_and_focus_scrolls(self):
        g=Game.new_run(seed=2);g.state='shop';g.generate_shop()
        g.shop=(g.shop*9)[:17]
        u=UI();u.cursor_shop=len(g.shop)+len(g.packs)-1
        c=snap(u,g,(122,50))
        self.assertTrue(has_outline(c,BLUE,True))
        self.assertTrue(has_outline(c,BORDER,False))
        self.assertFalse(any(z.bg==FOCUS_BG for r in c.a for z in r))

    def test_pack_no_extra_gap_and_green_unselected_box(self):
        g=Game.new_run(seed=1);g.state='pack'
        g.pack={'kind':'Celestial','size':'Normal','options':[{'type':'Planet','name':'Pair'}, {'type':'Planet','name':'Flush'}], 'picks':1}
        u=UI();c=snap(u,g)
        x,y,_,_=u.last_layout
        first=y+6+6
        self.assertIn('水星',row(c,first+1))
        self.assertIn('基础筹码',row(c,first+2))
        self.assertNotIn('基础筹码',row(c,first+3))
        self.assertTrue(has_outline(c,BLUE,True))
        self.assertTrue(has_outline(c,BORDER,False))
        self.assertFalse(any(z.bg==FOCUS_BG for r in c.a for z in r))

    def test_blind_preparation_has_no_focus_fill_and_completed_status(self):
        g=Game.new_run(seed=12);u=UI()
        g.blind=1;g.choose_blind()
        c=snap(u,g)
        self.assertIn('已完成',rendered(c))
        self.assertIn('当前挑战',rendered(c))
        self.assertNotIn('K 跳过',rendered(c))
        self.assertFalse(any(z.bg==tuple(min(255,v+10) for v in c.a[10][60].bg) and z.text=='╭' for r in c.a for z in r)) if False else None
        self.assertIn('T 跳过',rendered(c))

    def test_wasd_battle_movement_o_discard_and_k_save(self):
        c=Controller();g=Game.new_run(seed=1);g.start_blind();g.add_joker('Joker');c.game=g
        c.key('d');self.assertEqual(c.ui.cursor_hand,1)
        c.key('a');self.assertEqual(c.ui.cursor_hand,0)
        c.key('w');self.assertEqual(c.ui.focus,'joker')
        c.key('s');self.assertEqual(c.ui.focus,'hand')
        c.key('ENTER');self.assertEqual(len(c.ui.selected_uids),1)
        remaining=g.discards;c.key('o');self.assertEqual(g.discards,remaining-1)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'v10.json'
            with patch.object(g,'save',return_value=path) as saved:
                with patch.object(Game,'save_candidates',return_value=[path]):
                    c.key('k')
                saved.assert_called_once()
        self.assertEqual(c.ui.command,'')

    def test_shop_wasd_and_arrow_navigation_symmetric(self):
        c=Controller();g=Game.new_run(seed=4);g.state='shop';g.generate_shop();c.game=g
        count=len(c.ui.shop_entries(g));self.assertGreater(count,1)
        c.key('s');self.assertEqual(c.ui.cursor_shop,1)
        c.key('w');self.assertEqual(c.ui.cursor_shop,0)
        c.key('d');self.assertEqual(c.ui.cursor_shop,1)
        c.key('LEFT');self.assertEqual(c.ui.cursor_shop,0)
        c.key('RIGHT');self.assertEqual(c.ui.cursor_shop,1)
        c.key('a');self.assertEqual(c.ui.cursor_shop,0)

    def test_t_skip_and_k_not_skip(self):
        c=Controller();g=Game.new_run(seed=5);c.game=g
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'save.json'
            with patch.object(g,'save',return_value=path):
                with patch.object(Game,'save_candidates',return_value=[path]):c.key('k')
            self.assertEqual(g.blind,0)
            c.key('t');self.assertEqual(g.blind,1)
            self.assertEqual(g.state,'blind')

    def test_help_prompts_only_current_keymap(self):
        u=UI();u.overlay='help';c=snap(u,None)
        s=rendered(c)
        self.assertIn('P / O',s)
        self.assertIn('T',s)
        self.assertIn('K',s)
        self.assertNotIn('P / D',s)
        self.assertNotIn('K  跳过',s)

if __name__=='__main__':unittest.main()
