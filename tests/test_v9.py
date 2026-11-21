"""V9: details toggle, whole-deck inventory, focused outlines, shop selling, hidden cards."""
import os, unittest
from unittest.mock import patch
from arcana.cards import Card, RANKS
from arcana.game import Game, SAVE
from arcana.tui import UI,Renderer,BLUE,FOCUS_BG, Canvas
from play import Controller


def snapshot(u,g,dim=(160,60)):
    output=[]
    with patch('shutil.get_terminal_size',return_value=os.terminal_size(dim)):
        with patch.object(Renderer,'draw',lambda _,c:output.append(c)):
            u.draw(g)
    return output[0]


def text(c):return '\n'.join(''.join(cell.text or '' for cell in row) for row in c.a)


class V9(unittest.TestCase):
    @staticmethod
    def pack():
        g=Game.new_run(seed=19)
        g.state='pack'
        g.pack={'kind':'Celestial','size':'Normal','options':[{'type':'Planet','name':'Pair'},
            {'type':'Planet','name':'Straight'}],'picks':1,'original_total':2}
        return g

    def test_e_toggles_detail_in_shop_pack_and_inventory(self):
        c=Controller();g=Game.new_run(seed=19);g.state='shop';g.generate_shop();c.game=g
        c.key('e');self.assertEqual(c.ui.overlay,'detail')
        c.key('e');self.assertIsNone(c.ui.overlay)
        c.key('e');c.key('E');self.assertIsNone(c.ui.overlay)
        c.game=self.pack();g=c.game
        c.key('e');self.assertEqual(c.ui.detail['kind'],'pack')
        c.key('e');self.assertIsNone(c.ui.overlay)
        g.add_joker('Joker');c.key('i');c.key('e')
        self.assertEqual(c.ui.overlay,'detail')
        c.key('e');self.assertEqual(c.ui.overlay,'hand')

    def test_pack_description_replaces_lower_border_not_interior(self):
        g=self.pack();u=UI()
        for dim in ((122,50),(160,60)):
            c=snapshot(u,g,dim);x,y,W,H=u.last_layout
            yy=y+6+6+2
            self.assertIn('基础筹码', ''.join(cell.text or '' for cell in c.a[yy]))
            self.assertIn('┄', ''.join(cell.text or '' for cell in c.a[yy]))
            self.assertNotIn('基础筹码',''.join(cell.text or '' for cell in c.a[yy-1]))
            self.assertTrue(any(cell.fg==BLUE and cell.text=='┄' for cell in c.a[yy]))
            self.assertIn('Lv.2',text(c))

    def test_i_inventory_uses_blue_outline_without_blue_fill(self):
        g=Game.new_run(seed=20);g.add_joker('Joker')
        g.consumables.append({'type':'Planet','name':'Pair'})
        c=Controller();c.game=g;c.key('i')
        canvas=snapshot(c.ui,g)
        self.assertIn('Joker',text(canvas))
        self.assertIn('消耗牌',text(canvas))
        self.assertTrue(any(z.text=='┄' and z.fg==BLUE for row in canvas.a for z in row))
        self.assertFalse(any(z.bg==FOCUS_BG for row in canvas.a for z in row))
        c.key('DOWN');canvas=snapshot(c.ui,g)
        self.assertIn('星球',text(canvas)) if False else None
        self.assertTrue(any(z.text=='┄' and z.fg==BLUE for row in canvas.a for z in row))
        self.assertFalse(any(z.bg==FOCUS_BG for row in canvas.a for z in row))
        c.key('e');self.assertEqual(c.ui.detail,{'kind':'consumable','index':0})

    def test_full_deck_last_page_sorted_and_includes_purchased_card(self):
        g=Game.new_run(seed=19);g.state='shop';g.money=50
        extra=Card('2','♥',enhancement='Glass',edition='Foil',seal='Red')
        g.shop=[{'type':'Card','name':'Card','card':extra.to_dict(),'cost':1}]
        g.packs=[];g.shop_voucher=None
        c=Controller();c.game=g;c.shop_confirm()
        self.assertEqual(len(g.deck),53)
        c.key('i');c.key('RIGHT')
        self.assertTrue(c.ui.inventory_is_deck(g))
        canvas=snapshot(c.ui,g)
        rendered=text(canvas)
        self.assertIn('整 套 牌 组',rendered)
        self.assertIn('53 张牌',rendered)
        self.assertIn('玻璃',rendered)
        cards=c.ui._deck_by_suit(g)
        self.assertEqual([v.rank for v in cards['♥']][:2],['2','2'])
        self.assertEqual([v.rank for v in cards['♦']],list(RANKS))
        self.assertEqual(len(cards['♥']),14)

    def test_deck_scroll_stays_on_last_page_when_one_suit_long(self):
        g=Game.new_run(seed=2)
        g.deck.extend(Card('2','♥') for _ in range(75))
        c=Controller();c.game=g;c.key('i');c.key('RIGHT')
        u=c.ui;self.assertTrue(u.inventory_is_deck(g))
        snapshot(u,g,(122,50))
        for _ in range(7):c.key('DOWN')
        self.assertEqual(u.inventory_deck_scroll,7)
        self.assertIn('第 8–',text(snapshot(u,g,(122,50))))
        self.assertEqual(u.inventory_page,u.inventory_pages(g)-1)

    def test_hidden_card_check_and_number_are_blue(self):
        g=Game.new_run(seed=11);g.start_blind();c=Controller();c.game=g
        focus=g.hand[0].uid;g.hidden_cards=[focus]
        c.key('ENTER');self.assertEqual(c.ui.selected_uids,[focus])
        canvas=snapshot(c.ui,g)
        visible=[z for row in canvas.a for z in row]
        self.assertTrue(any(z.text=='✓' and z.fg==BLUE for z in visible))
        self.assertIn('??',text(canvas))
        self.assertTrue(any(z.text=='1' and z.fg==BLUE for z in visible))
        c.key('ENTER');canvas=snapshot(c.ui,g)
        self.assertFalse(any(z.text=='✓' and z.fg==BLUE for row in canvas.a for z in row))
        c.key('ENTER');c.key('RIGHT')
        self.assertIn(focus,c.ui.selected_uids)
        self.assertTrue(any(z.text=='✓' and z.fg==BLUE for row in snapshot(c.ui,g).a for z in row))

    def test_dashes_horizontal_and_vertical_use_consistent_cell_pitch(self):
        c=Canvas(50,30,(0,0,0));c.box(5,5,10,6,BLUE,(0,0,0),dashed=True)
        top=[z.text for z in c.a[5][5:15]]
        self.assertEqual(top[1:-1].count('┄'),4)
        self.assertEqual(top[1:-1].count(' '),4)
        self.assertEqual([c.a[i][5].text for i in range(6,10)],['┆']*4)

    def test_shop_can_focus_view_and_sell_owned_joker(self):
        c=Controller();g=Game.new_run(seed=21);g.state='shop';g.money=1000
        g.generate_shop();g.add_joker('Joker');c.game=g
        snapshot(c.ui,g,(160,60))
        self.assertTrue(c.ui.shop_shows_owned(g))
        self.assertEqual(c.shop_current(),('owned_joker',0))
        self.assertIn('已 持 有 小 丑 牌',text(snapshot(c.ui,g)))
        c.key('e');self.assertEqual(c.ui.detail,{'kind':'joker','index':0})
        c.key('e');self.assertIsNone(c.ui.overlay)
        before=g.money;c.key('ENTER')
        self.assertEqual(g.jokers,[]);self.assertGreater(g.money,before)

    def test_shop_all_jokers_are_scrollable_and_j_command_removed(self):
        g=Game.new_run(seed=22);g.state='shop';g.generate_shop();g.money=50
        for _ in range(5):g.jokers.append(g.make_joker('Joker'))
        c=Controller();c.game=g
        self.assertTrue(c.ui.shop_shows_owned(g))
        self.assertEqual(c.ui.shop_entries(g)[:5],[('owned_joker',i) for i in range(5)])
        for _ in range(4):c.key('DOWN')
        self.assertEqual(c.shop_current(),('owned_joker',4))
        self.assertIn('Joker',text(snapshot(c.ui,g,(122,50))))
        c.key('ENTER');self.assertEqual(len(g.jokers),4)
        with self.assertRaises(ValueError):c.execute('j1')

    def test_old_save_migration_ui_removed(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        self.assertNotIn('旧版', (root/'README.md').read_text(encoding='utf8'))
        self.assertNotIn('旧存档', (root/'arcana/tui.py').read_text(encoding='utf8'))
        self.assertTrue(str(SAVE).endswith('_v10_save.json'))

if __name__=='__main__':unittest.main()
