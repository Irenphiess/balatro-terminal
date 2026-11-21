"""V13: soundtrack, multilingual menu, voucher lifecycle, title and navigation."""
import os
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arcana.game import Game
from arcana.content import VOUCHERS,VOUCHER_PAIRS
from arcana.i18n import LANGUAGES,CONFIG_PATH,tr,localize,set_active,load_language
from arcana.music import Music,TRACKS
from arcana.tui import UI,Renderer,BLUE,BORDER
from play import Controller


def draw_snapshot(u,g=None,size=(160,60)):
    result=[]
    with patch('shutil.get_terminal_size',return_value=os.terminal_size(size)):
        with patch.object(Renderer,'draw',lambda _,canvas:result.append(canvas)):
            u.draw(g)
    return result[0]


def canvas_text(screen):
    return ''.join(c.text for row in screen.a for c in row)

class V13(unittest.TestCase):
    def test_bought_voucher_disappears_and_stays_gone_until_boss(self):
        g=Game.new_run(seed=12);g.state='shop';g.money=10000;g.generate_shop()
        offered=g.shop_voucher;self.assertIsNotNone(offered)
        g.buy_voucher();self.assertIn(offered,g.vouchers)
        self.assertIsNone(g.shop_voucher)
        g.generate_shop();self.assertIsNone(g.shop_voucher)
        g.blind=1;g.generate_shop();self.assertIsNone(g.shop_voucher)
        g.blind=2;g.generate_shop()
        self.assertIsNotNone(g.shop_voucher)
        self.assertNotEqual(g.shop_voucher,offered)
        self.assertNotIn(g.shop_voucher,g.vouchers)

    def test_unbought_voucher_stays_the_same_within_ante(self):
        g=Game.new_run(seed=4);g.state='shop';g.generate_shop();first=g.shop_voucher
        for i in range(5):
            g.generate_shop()
            self.assertEqual(g.shop_voucher,first)
        g.blind=1;g.generate_shop();self.assertEqual(g.shop_voucher,first)

    def test_voucher_upgrades_require_base_and_all_redeemed_is_empty(self):
        g=Game.new_run(seed=16)
        base,upgrade,_=VOUCHER_PAIRS[0]
        g.vouchers=set(VOUCHERS)-{base,upgrade}
        for _ in range(10):self.assertEqual(g._eligible_voucher(),base)
        g.vouchers.add(base)
        self.assertEqual(g._eligible_voucher(),upgrade)
        g.vouchers.add(upgrade)
        self.assertIsNone(g._eligible_voucher())
        g.state='shop';g.generate_shop();self.assertIsNone(g.shop_voucher)
        self.assertFalse(any(typ=='voucher' for typ,_ in UI().shop_entries(g)))

    def test_user_supplied_five_original_tracks_scene_mapping(self):
        self.assertEqual(len({p for p in TRACKS.values()}),5)
        for p in set(TRACKS.values()):
            self.assertTrue(p.is_file())
            self.assertGreater(p.stat().st_size,3_000_000)
            self.assertEqual(p.read_bytes()[:3],b'ID3')
        c=Controller();g=Game.new_run(seed=20);c.game=g
        c.game.state='pack'
        for kind,expected in [('Arcana','arcana'),('Spectral','arcana'),('Celestial','celestial'),('Standard','play'),('Buffoon','play')]:
            g.pack={'kind':kind};self.assertEqual(c.music_scene(),expected)

    def test_language_selection_persists_uses_the_same_dashed_focus(self):
        with tempfile.TemporaryDirectory() as td:
            with patch('arcana.i18n.CONFIG_PATH',Path(td)/'lang.json'):
                c=Controller();c.key('v')
                self.assertEqual(c.ui.overlay,'language')
                before=c.ui.language_cursor
                c.key('s');self.assertEqual(c.ui.language_cursor,before+1)
                c.key('UP');self.assertEqual(c.ui.language_cursor,before)
                c.key('DOWN');c.key('ENTER')
                self.assertEqual(c.ui.language,'zh_TW')
                self.assertIsNone(c.ui.overlay)
                self.assertEqual(json.loads((Path(td)/'lang.json').read_text())['language'],'zh_TW')
                self.assertEqual(UI(language=load_language()).language,'zh_TW')
                c.key('v');snapshot=draw_snapshot(c.ui)
                self.assertIn('LANGUAGE',canvas_text(snapshot))
                self.assertTrue(any(cell.fg==BLUE and cell.text=='┄' for row in snapshot.a for cell in row))
                self.assertTrue(any(cell.fg==BORDER and cell.text=='─' for row in snapshot.a for cell in row))
                c.key('ESC');self.assertIsNone(c.ui.overlay)

    def test_language_returns_to_existing_screen(self):
        c=Controller();c.ui.overlay='hand';g=Game.new_run(seed=8);c.game=g
        c.key('v');self.assertEqual(c.ui.overlay,'language')
        c.key('ESC');self.assertEqual(c.ui.overlay,'hand')
        c.key('v');c.key('ENTER');self.assertEqual(c.ui.overlay,'hand')

    def test_18_language_labels_and_draw_safe_at_supported_terminal_sizes(self):
        self.assertGreaterEqual(len(LANGUAGES),18)
        for locale,name in LANGUAGES:
            with self.subTest(locale=locale):
                self.assertTrue(tr('language',locale))
                self.assertNotEqual(tr('language',locale),'language')
                u=UI();u.language=locale;u.overlay='language'
                for size in ((122,50),(160,60)):
                    canvas=draw_snapshot(u,None,size)
                    self.assertEqual(len(canvas.a),canvas.h)
                    self.assertTrue(all(len(row)==canvas.w for row in canvas.a))
                    self.assertIn('LANGUAGE',canvas_text(canvas))

    def test_title_only_balatro_and_boss_boilerplate_removed(self):
        u=UI();u.language='zh_CN'
        for mode in ('splash','select'):
            u.stage=mode
            t=canvas_text(draw_snapshot(u))
            self.assertIn('B A L A T R O',t)
            self.assertNotIn('T E R M I N A L',t)
            self.assertNotIn('A R C A N A  ·  T E R M I N A L',t)
        g=Game.new_run(seed=77);t=canvas_text(draw_snapshot(u,g))
        self.assertNotIn('同一 Ante 共用',t)

    def test_v_key_does_not_clash_with_deck_stake_or_game_navigation(self):
        c=Controller();c.ui.stage='select'
        di,si=c.ui.deck_index,c.ui.stake_index
        c.key('v');self.assertEqual(c.ui.overlay,'language')
        c.key('ESC');self.assertEqual((c.ui.deck_index,c.ui.stake_index),(di,si))
        c.key('w');self.assertNotEqual(c.ui.deck_index,di)
        c.key('RIGHT');self.assertNotEqual(c.ui.stake_index,si)

    def test_no_new_voucher_after_reroll_in_the_same_shop(self):
        g=Game.new_run(seed=47);g.money=500;g.state='shop';g.generate_shop()
        name=g.shop_voucher
        g.reroll();self.assertEqual(g.shop_voucher,name)
        g.buy_voucher();g.reroll();self.assertIsNone(g.shop_voucher)

if __name__=='__main__':unittest.main()
