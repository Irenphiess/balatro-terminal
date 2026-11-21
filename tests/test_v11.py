"""V11: WASD and arrow keys are interchangeable in every navigable screen
except the explicit deck/stake selection screen; separator fill is scene-local.
"""
import os
import unittest
from unittest.mock import patch

from arcana.game import Game
from arcana.cards import Card
from arcana.tui import UI, Canvas, Renderer, BORDER
from play import Controller


def snapshot(ui, game, size=(160, 60)):
    result=[]
    with patch('shutil.get_terminal_size', return_value=os.terminal_size(size)):
        with patch.object(Renderer, 'draw', lambda _self, canvas: result.append(canvas)):
            ui.draw(game)
    return result[0]


def make_pack():
    c=Controller()
    g=Game.new_run(seed=11)
    g.state='pack'
    g.pack={'kind':'Celestial','size':'Mega','picks':2, 'original_total':3,
            'options':[{'type':'Planet','name':n} for n in ('Pair','Flush','Straight')]}
    c.game=g
    return c


class V11(unittest.TestCase):
    def test_pack_ws_matches_up_down_with_wraparound(self):
        for letter,arrow in [('w','UP'),('W','UP'),('s','DOWN'),('S','DOWN')]:
            a=make_pack();b=make_pack()
            a.ui.cursor_pack=b.ui.cursor_pack=1
            a.key(letter);b.key(arrow)
            self.assertEqual(a.ui.cursor_pack,b.ui.cursor_pack)
            self.assertEqual(a.ui.command,'')
        a=make_pack();a.key('w');self.assertEqual(a.ui.cursor_pack,2)
        a.key('s');self.assertEqual(a.ui.cursor_pack,0)
        a.key('s');a.key('ENTER')
        self.assertEqual(a.game.levels['Flush'],2)
        self.assertEqual(a.game.pack['picks'],1)

    def test_pack_target_ad_matches_left_right(self):
        def prepare():
            c=Controller();g=Game.new_run(seed=22);g.refresh_shop_hand()
            g.state='pack';g.pack={'kind':'Arcana','size':'Normal','picks':1,
                                   'options':[{'type':'Tarot','name':'Death'}]}
            c.game=g;c.key('ENTER')
            self.assertEqual(c.ui.overlay,'pack_target')
            return c
        for letter,arrow in [('a','LEFT'),('A','LEFT'),('d','RIGHT'),('D','RIGHT')]:
            a=prepare();b=prepare()
            a.ui.target_cursor=b.ui.target_cursor=3
            a.key(letter);b.key(arrow)
            self.assertEqual(a.ui.target_cursor,b.ui.target_cursor)
            self.assertEqual(a.ui.command,'')
        a=prepare();a.key('d');a.key('ENTER')
        self.assertEqual(a.ui.target_indices,[1])
        a.key('d');a.key('ENTER')
        self.assertIsNone(a.ui.overlay)
        self.assertEqual(a.game.state,'shop')

    def test_shop_wasd_matches_arrows_in_all_four_directions(self):
        def prepare():
            c=Controller();g=Game.new_run(seed=30);g.state='shop';g.generate_shop();c.game=g
            c.ui.cursor_shop=1
            return c
        for letter,arrow in [('w','UP'),('W','UP'),('s','DOWN'),('S','DOWN'),
                             ('a','LEFT'),('A','LEFT'),('d','RIGHT'),('D','RIGHT')]:
            a=prepare();b=prepare()
            a.key(letter);b.key(arrow)
            self.assertEqual(a.ui.cursor_shop,b.ui.cursor_shop)
            self.assertEqual(a.ui.command,'')

    def test_play_wasd_matches_arrows_and_never_discards_or_saves(self):
        def prepare():
            c=Controller();g=Game.new_run(seed=41);g.add_joker('Joker');g.start_blind();c.game=g
            c.ui.cursor_hand=2;c.ui.focus='hand'
            return c
        for letter,arrow in [('w','UP'),('s','DOWN'),('a','LEFT'),('d','RIGHT')]:
            a=prepare();b=prepare()
            a.key(letter);b.key(arrow)
            self.assertEqual((a.ui.focus,a.ui.cursor_hand,a.ui.cursor_joker,a.game.discards),
                             (b.ui.focus,b.ui.cursor_hand,b.ui.cursor_joker,b.game.discards))
            self.assertEqual(a.ui.command,'')

    def test_gallery_effects_help_inventory_navigation_equivalence(self):
        for overlay,key_pairs in [
            ('gallery',[('a','LEFT'),('d','RIGHT')]),
            ('effects',[('a','LEFT'),('d','RIGHT'),('w','UP'),('s','DOWN')]),
            ('help',[('a','LEFT'),('d','RIGHT')]),
            ('hand',[('a','LEFT'),('d','RIGHT'),('w','UP'),('s','DOWN')]),
        ]:
            def prepare():
                c=Controller();g=Game.new_run(seed=6);g.add_joker('Joker');
                g.consumables.append({'type':'Planet','name':'Pair'})
                c.game=g;c.ui.overlay=overlay
                c.ui.page=1;c.ui.effects_group=2;c.ui.effects_page=1
                c.ui.help_page=1;c.ui.inventory_cursor=1;c.ui.inventory_page=0
                return c
            for letter,arrow in key_pairs:
                with self.subTest(overlay=overlay,letter=letter):
                    a=prepare();b=prepare()
                    a.key(letter);b.key(arrow)
                    ua,ub=a.ui,b.ui
                    self.assertEqual((ua.page,ua.effects_group,ua.effects_page,ua.help_page,
                                      ua.inventory_page,ua.inventory_cursor,ua.inventory_deck_scroll),
                                     (ub.page,ub.effects_group,ub.effects_page,ub.help_page,
                                      ub.inventory_page,ub.inventory_cursor,ub.inventory_deck_scroll))
                    self.assertEqual(ua.command,'')

    def test_inventory_deck_scroll_ws_matches_up_down(self):
        def prepare():
            c=Controller();g=Game.new_run(seed=17)
            g.deck.extend(Card('2','♥') for _ in range(70))
            c.game=g;c.ui.overlay='hand';c.ui.inventory_page=c.ui.inventory_pages(g)-1
            snapshot(c.ui,g,(122,50))
            return c
        for letter,arrow in [('w','UP'),('s','DOWN')]:
            a=prepare();b=prepare()
            a.ui.inventory_deck_scroll=b.ui.inventory_deck_scroll=2
            a.key(letter);b.key(arrow)
            self.assertEqual(a.ui.inventory_deck_scroll,b.ui.inventory_deck_scroll)
            self.assertEqual(a.ui.command,'')

    def test_initial_deck_stake_screen_keeps_separate_controls(self):
        c=Controller()
        c.key('ENTER')
        self.assertEqual(c.ui.stage,'select')
        c.key('d');self.assertEqual(c.ui.deck_index,1)
        self.assertEqual(c.ui.stake_index,0)
        c.key('RIGHT');self.assertEqual(c.ui.deck_index,1)
        self.assertEqual(c.ui.stake_index,1)
        c.key('s');self.assertEqual(c.ui.deck_index,6)
        c.key('DOWN');self.assertEqual(c.ui.stake_index,5)

    def test_selection_screen_exception_does_not_leak_into_overlays(self):
        c=Controller();c.key('ENTER')
        c.key('g');self.assertEqual(c.ui.overlay,'gallery')
        c.key('d');self.assertEqual(c.ui.page,1)
        c.key('a');self.assertEqual(c.ui.page,0)
        self.assertEqual(c.ui.stake_index,0)
        c.key('g');c.key('f')
        c.key('d');self.assertEqual(c.ui.effects_group,1)
        c.key('a');self.assertEqual(c.ui.effects_group,0)
        c.key('f');c.key('h')
        c.key('d');self.assertEqual(c.ui.deck_index,0)

    def test_numbered_text_entry_is_retired_and_wasd_stays_navigation(self):
        c=make_pack()
        before=c.ui.cursor_pack
        c.key('w');self.assertNotEqual(c.ui.cursor_pack,before)
        c.key('1');self.assertEqual(c.ui.command,'')
        c.key('s');self.assertEqual(c.ui.cursor_pack,before)

    def test_separators_use_underlying_inner_background(self):
        outer=(1,2,3);inside=(21,43,65)
        c=Canvas(32,12,outer)
        c.rect(2,2,28,9,inside)
        c.hline(4,5,23,BORDER)
        self.assertEqual([(z.text,z.bg) for z in c.a[5][4:27]], [('─',inside)]*23)
        # A page's top, bottom, and section separators should match the page
        # background rather than the darker outer margin.
        g=Game.new_run(seed=9);g.state='shop';g.generate_shop()
        ui=UI();screen=snapshot(ui,g)
        x,y,W,H=ui.last_layout
        bg=screen.a[y+5][x+5].bg
        self.assertNotEqual(bg,screen.bg)
        for row in (y+4,y+H-7):
            self.assertEqual(screen.a[row][x+8].text,'─')
            self.assertEqual(screen.a[row][x+8].bg,bg)
        # Main shop section separators also share this exact background.
        rx=x+(36 if W>=137 else 34)+8
        for pos in range(rx,rx+15):
            z=screen.a[y+6][pos]
            if z.text=='─':self.assertEqual(z.bg,bg)

    def test_detail_separators_are_shop_style_solid_and_without_fill(self):
        g=Game.new_run(seed=12);g.state='shop';g.generate_shop()
        ui=UI();ui.overlay='detail';ui.detail={'kind':'shop','index':0}
        screen=snapshot(ui,g)
        x,y,W,H=ui.last_layout
        bg=screen.a[y+5][x+5].bg
        sep=[z for yy in range(y+14,y+H-15) for z in screen.a[yy]
             if z.text=='─' and z.fg==BORDER]
        self.assertTrue(sep,'expect detail body horizontal separators')
        self.assertTrue(all(z.bg==bg for z in sep))
        self.assertFalse(any(z.text=='·' and z.fg==BORDER for row in screen.a for z in row))


if __name__=='__main__':unittest.main()
