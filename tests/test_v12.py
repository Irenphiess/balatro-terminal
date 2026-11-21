"""V12 UI-first gameplay and inventory coverage."""
import os, unittest
from unittest.mock import patch
from arcana.game import Game
from arcana.cards import Card
from arcana.tui import UI, Renderer, HAND_ZH
from play import Controller


def screen(u,g,size=(160,60)):
    frames=[]
    with patch('shutil.get_terminal_size',return_value=os.terminal_size(size)):
        with patch.object(Renderer,'draw',lambda _r,c:frames.append(c)):
            u.draw(g)
    return frames[-1]

def text(c):return '\n'.join(''.join(z.text or '' for z in r) for r in c.a)

class V12(unittest.TestCase):
    def test_live_selected_hand_type_and_level(self):
        c=Controller();g=Game.new_run(seed=10);g.start_blind();c.game=g
        g.hand=[Card('9','♥'),Card('9','♦'),Card('5','♣'),Card('4','♠'),Card('2','♣')]
        g.levels['Pair']=3
        c.key('ENTER');c.key('d');c.key('ENTER')
        shown=text(screen(c.ui,g))
        self.assertIn('当前选中牌型：对子  Lv.3',shown)
        c.key('ENTER')
        self.assertIn('高牌',text(screen(c.ui,g)))

    def test_title_selected_deck_formation(self):
        u=UI();u.stage='select'
        u.deck_index=0;self.assertIn('♥13 ♦13 ♠13 ♣13',text(screen(u,None)))
        u.deck_index=8;self.assertIn('40 张',text(screen(u,None)))
        u.deck_index=9;self.assertIn('♥26 ♠26',text(screen(u,None)))

    def test_owned_shop_jokers_and_consumables_are_first_and_unlimited(self):
        c=Controller();g=Game.new_run(seed=31);g.state='shop';g.generate_shop()
        g.jokers=[g.make_joker('Joker') for _ in range(18)]
        g.consumables=[{'type':'Planet','name':'Pair'},{'type':'Tarot','name':'The Hermit'}]
        c.game=g
        entries=c.ui.shop_entries(g)
        self.assertEqual(entries[:18],[('owned_joker',i) for i in range(18)])
        self.assertEqual(entries[18:20],[('owned_consumable',0),('owned_consumable',1)])
        c.ui.cursor_shop=19
        for dim in ((122,50),(160,60)):
            self.assertIn('隐者',text(screen(c.ui,g,dim)))
        before=g.money
        with patch.object(c,'stash'):
            c.key('ENTER')
        self.assertEqual(len(g.consumables),1)
        self.assertGreaterEqual(g.money,before)

    def test_shop_enter_sells_joker_at_any_index(self):
        c=Controller();g=Game.new_run(seed=21);g.state='shop';g.generate_shop()
        g.jokers=[g.make_joker('Joker') for _ in range(12)];c.game=g
        c.ui.cursor_shop=10
        with patch.object(c,'stash'):
            c.key('ENTER')
        self.assertEqual(len(g.jokers),11)
        self.assertEqual(c.ui.shop_entries(g)[10],('owned_joker',10))

    def test_inventory_joker_enter_no_change_no_exit(self):
        c=Controller();g=Game.new_run(seed=15);g.add_joker('Joker');c.game=g
        c.key('i');before=g.jokers.copy()
        c.key('ENTER')
        self.assertEqual(c.ui.overlay,'hand')
        self.assertEqual(g.jokers,before)
        c.key('i');self.assertIsNone(c.ui.overlay)

    def test_inventory_planet_enter_upgrade_and_remain(self):
        c=Controller();g=Game.new_run(seed=20);g.consumables=[{'type':'Planet','name':'Pair'}];c.game=g
        with patch.object(c,'stash'):
            c.key('i');c.key('ENTER')
        self.assertEqual(g.levels['Pair'],2)
        self.assertEqual(g.consumables,[])
        self.assertEqual(c.ui.overlay,'hand')

    def test_inventory_targeted_tarot_after_enter_selects_targets(self):
        c=Controller();g=Game.new_run(seed=5);g.refresh_shop_hand()
        g.consumables=[{'type':'Tarot','name':'Death'}];c.game=g
        with patch.object(c,'stash'):
            c.key('i');c.key('ENTER')
            self.assertEqual(c.ui.overlay,'use_target')
            self.assertIn('选 择 生 效 目 标',text(screen(c.ui,g)))
            c.key('ENTER');c.key('d');c.key('ENTER')
        self.assertIsNone(c.ui.pending_use_index)
        self.assertEqual(c.ui.overlay,'hand')
        self.assertEqual(len(g.consumables),0)

    def test_inventory_target_cancel_keeps_consumable(self):
        c=Controller();g=Game.new_run(seed=5);g.refresh_shop_hand()
        g.consumables=[{'type':'Tarot','name':'The Star'}];c.game=g
        c.key('i');c.key('ENTER');self.assertEqual(c.ui.overlay,'use_target')
        c.key('ESC');self.assertEqual(c.ui.overlay,'hand')
        self.assertEqual(len(g.consumables),1)

    def test_shop_consumable_use_requires_target_screen(self):
        c=Controller();g=Game.new_run(seed=8);g.state='shop';g.generate_shop();g.refresh_shop_hand()
        g.consumables=[{'type':'Tarot','name':'Justice'}];c.game=g
        with patch.object(c,'stash'):
            c.key('ENTER');self.assertEqual(c.ui.overlay,'use_target')
            c.key('ENTER')
        self.assertIsNone(c.ui.overlay)
        self.assertEqual(len(g.consumables),0)

    def test_joker_reorder_ui_instead_of_numbered_command(self):
        c=Controller();g=Game.new_run(seed=9)
        g.add_joker('Joker');g.add_joker('Cavendish');c.game=g
        with patch.object(c,'stash'):
            c.key('i');c.key('s');c.key('m')
            self.assertTrue(c.ui.inventory_reorder)
            c.key('w');self.assertEqual(g.jokers[0]['name'],'Cavendish')
            c.key('m')
        self.assertFalse(c.ui.inventory_reorder)
        self.assertEqual(c.ui.overlay,'hand')
        self.assertIn('卡文迪什',text(screen(c.ui,g)))

    def test_removed_numbered_input_with_and_without_spaces(self):
        c=Controller();g=Game.new_run(seed=7);g.start_blind();c.game=g
        for op in ('p1','p 1','o2','o 2','u1','u 1','j1','j 1','b1','b 1','m1','m 1 2'):
            with self.subTest(op=op):
                with self.assertRaises(ValueError):c.execute(op)
        self.assertEqual(g.state,'play')
        self.assertIsNone(g.last_result)

    def test_gallery_ui_focus_e_details_and_e_return(self):
        c=Controller();c.key('g');c.key('s');c.key('e')
        self.assertEqual(c.ui.overlay,'detail')
        self.assertEqual(c.ui.detail,{'kind':'gallery','index':1})
        c.key('e');self.assertEqual(c.ui.overlay,'gallery')
        self.assertEqual(c.ui.gallery_cursor,1)
        self.assertIn('➤',text(screen(c.ui,None)))

    def test_effect_gallery_selection_auto_pagination(self):
        c=Controller();c.key('f')
        for _ in range(9):c.key('s')
        self.assertEqual(c.ui.effects_page,1)
        self.assertEqual(c.ui.effects_cursor,9)
        c.key('e')
        self.assertEqual(c.ui.detail['index'],9)
        c.key('e');self.assertEqual(c.ui.overlay,'effects')
        c.key('d');self.assertEqual(c.ui.effects_cursor,0)

    def test_no_numbered_hints_anywhere(self):
        g=Game.new_run(seed=10);g.state='shop';g.generate_shop()
        c=Controller();c.game=g
        with patch('shutil.get_terminal_size',return_value=os.terminal_size((160,60))):
            for overlay in (None,'help','hand'):
                c.ui.overlay=overlay
                view=text(screen(c.ui,g))
                for phrase in ('J编号','U 编号','M 两编号','B1','O1','T1'):
                    self.assertNotIn(phrase,view)

if __name__=='__main__':unittest.main()
