"""V8: focused pack hints, multi-page inventory, help cleanup, unique Boss palettes."""
import os, unittest
from unittest.mock import patch
from arcana.game import Game
from arcana.content import BOSSES
from arcana.tui import UI, Renderer, BLUE, FOCUS_BG, BOSS_COLOURS, boss_palette
from play import Controller


def snapshot(ui,g,dim=(160,60)):
    frames=[]
    with patch('shutil.get_terminal_size', return_value=os.terminal_size(dim)):
        with patch.object(Renderer, 'draw', lambda _,c:frames.append(c)):
            ui.draw(g)
    return frames[0]

def line(canvas,i):
    return ''.join(c.text or '' for c in canvas.a[i])

def content(canvas):
    return '\n'.join(line(canvas,i) for i in range(canvas.h))

class V8(unittest.TestCase):
    def new_pack(self):
        g=Game.new_run(seed=13);g.state='pack'
        g.pack={'kind':'Celestial','size':'Mega','options':[
            {'type':'Planet','name':'Pair'},
            {'type':'Planet','name':'Flush'},
            {'type':'Planet','name':'Straight'},
            {'type':'Planet','name':'High Card'},
            {'type':'Planet','name':'Two Pair'}],
            'picks':2,'original_total':5}
        return g

    def test_pack_focus_description_visible_and_not_clobbered(self):
        g=self.new_pack();u=UI()
        for dim in ((122,50),(160,60),(190,75)):
            for index in (0,1,2,3,4):
                u.cursor_pack=index
                c=snapshot(u,g,dim)
                rows=[(i,line(c,i)) for i in range(c.h)]
                expected=f'Lv.{g.levels[g.pack["options"][index]["name"]]+1}'
                _,origin_y,_,_=u.last_layout
                yy=origin_y+6+6+index*4+2
                self.assertIn(expected,rows[yy][1],(dim,index,expected))
                self.assertFalse(any(cell.bg==FOCUS_BG for cell in c.a[yy]))
                self.assertIn('基础筹码',rows[yy][1])
                self.assertTrue(any(q.text=='┄' and q.fg==BLUE for line_ in c.a for q in line_))

    def test_pack_all_types_have_explanations(self):
        g=self.new_pack();g.pack['kind']='Buffoon'
        g.pack['options']=[{'type':'Joker','name':'Joker'},
                           {'type':'Tarot','name':'The Star'},
                           {'type':'Spectral','name':'Black Hole'},
                           {'type':'Card','name':'Card','card':g.deck[0].to_dict()}]
        u=UI()
        for pos,marker in enumerate(('倍率','方块','等级','新扑克牌')):
            u.cursor_pack=pos
            txt=content(snapshot(u,g))
            self.assertIn(marker,txt,(pos,marker))
        
    def test_inventory_available_every_play_stage(self):
        c=Controller();g=Game.new_run(seed=10);g.add_joker('Joker')
        g.consumables.append({'type':'Planet','name':'Pair'})
        c.game=g
        for state in ('blind','play','shop','pack'):
            g.state=state
            c.key('i')
            self.assertEqual(c.ui.overlay,'hand',state)
            shown=content(snapshot(c.ui,g))
            self.assertIn('持有 Joker',shown)
            self.assertIn('消耗牌',shown)
            self.assertNotIn('当前手牌',shown)
            c.key('e')
            self.assertEqual(c.ui.overlay,'detail')
            self.assertEqual(c.ui.detail,{'kind':'joker','index':0})
            self.assertIn('核心效果',content(snapshot(c.ui,g)))
            c.key('e');self.assertEqual(c.ui.overlay,'hand')
            c.key('DOWN');c.key('e')
            self.assertEqual(c.ui.detail,{'kind':'consumable','index':0})
            c.key('e');self.assertEqual(c.ui.overlay,'hand')
            c.key('RIGHT')
            self.assertEqual(c.ui.inventory_page,c.ui.inventory_pages(g)-1)
            self.assertIn('整 套 牌 组',content(snapshot(c.ui,g)))
            c.key('i');self.assertIsNone(c.ui.overlay)

    def test_jokers_paginate_without_footer_overlap(self):
        c=Controller();g=Game.new_run(seed=16)
        g.jokers=[g.make_joker('Joker') for _ in range(30)]
        c.game=g
        for dim in ((122,50),(160,60)):
            c.key('i')
            snap=snapshot(c.ui,g,dim)
            n=c.ui.inventory_pages(g)
            self.assertGreaterEqual(n,3)
            self.assertIn('持有 Joker',content(snap))
            seen=0
            for page in range(n-1):
                c.ui.inventory_page=page
                snap=snapshot(c.ui,g,dim)
                seen+=len([v for v in c.ui.inventory_page_entries(g) if v[0]=='joker'])
                x,y,W,H=c.ui.last_layout
                footer_y=y+H-12
                final_row=y+13+(len(c.ui.inventory_page_entries(g))-1)*3+2
                self.assertLess(final_row,footer_y,(dim,page,final_row,footer_y))
            self.assertEqual(seen,30)
            c.ui.inventory_page=n-1
            self.assertIn('整 套 牌 组',content(snapshot(c.ui,g,dim)))
            c.key('i')

    def test_help_unique_key_entries_no_deprecated_buy_pack(self):
        u=UI();u.overlay='help'
        c=snapshot(u,None)
        s=content(c)
        self.assertIn('操  作  指  南',s)
        for old in ('B 1','O 1','T 1','按数字购买','按数字领取'):
            self.assertNotIn(old,s)
        for current in ('Enter','I','E','H','X','↑ ↓'):
            self.assertIn(current,s)
        # The help dictionary source is keyed by shortcut, repeated entries should be absent.
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/'arcana'/'tui.py').read_text()
        block=source[source.index('actions=[',source.index('def _help(')):source.index(']',source.index('actions=[',source.index('def _help(')))+1]
        self.assertEqual(block.count("('Enter',"),1)
        self.assertEqual(block.count("('E',"),1)

    def test_every_boss_color_matches_source_and_distinct(self):
        self.assertEqual(set(BOSS_COLOURS),set(BOSSES))
        self.assertEqual(BOSS_COLOURS['The Manacle'],(0x57,0x57,0x57))
        self.assertEqual(BOSS_COLOURS['The Wheel'],(0x50,0xbf,0x7c))
        self.assertEqual(BOSS_COLOURS['The Eye'],(0x4b,0x71,0xe4))
        self.assertEqual(len(set(BOSS_COLOURS.values())),len(BOSSES))
        self.assertEqual(len({boss_palette(name)[1] for name in BOSSES}),len(BOSSES))
        for boss in BOSSES:
            outside,bg,bright=boss_palette(boss)
            self.assertTrue(all(b<180 for b in bg))
            self.assertTrue(all(hi>=lo for hi,lo in zip(bright,bg)))

    def test_boss_battle_background_differs_normal_game(self):
        g=Game.new_run(seed=8)
        g.state='blind';g.blind=2;g.boss='The Eye'
        u=UI();a=snapshot(u,g)
        g.boss='The Hook';b=snapshot(u,g)
        self.assertNotEqual(a.bg,b.bg)
        self.assertEqual(a.bg,boss_palette('The Eye')[0])
        self.assertEqual(b.bg,boss_palette('The Hook')[0])
        self.assertIn('本 Ante 的 BOSS 能力预告',content(b))
        g.state='play';g.boss='The Wheel'
        d=snapshot(u,g)
        self.assertEqual(d.bg,boss_palette('The Wheel')[0])

    def test_help_and_inventory_restore_underlying_shop_and_pack(self):
        c=Controller();g=Game.new_run(seed=5);g.state='shop';g.generate_shop();c.game=g
        c.ui.cursor_shop=1
        c.key('i');c.key('RIGHT');c.key('ESC')
        self.assertEqual(c.ui.cursor_shop,1)
        self.assertEqual(c.ui.overlay,None)
        c.key('h');self.assertIn('操  作',content(snapshot(c.ui,g)))
        c.key('ENTER');self.assertIsNone(c.ui.overlay)
        g.state='pack';g.pack=self.new_pack().pack
        c.ui.cursor_pack=2
        c.key('i');c.key('RIGHT');c.key('ENTER')
        self.assertEqual(c.ui.cursor_pack,2)
        self.assertEqual(c.ui.overlay,'hand')
        c.key('i');self.assertIsNone(c.ui.overlay)

if __name__=='__main__':unittest.main()
